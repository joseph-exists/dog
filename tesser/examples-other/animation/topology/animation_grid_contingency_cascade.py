#!/usr/bin/env python3
"""Grid contingency cascade animation stress test for Tesserax.

Day-one model features:
- explicit guards: trip / isolate / recover with hysteresis + cooldowns
- bounded dynamics: load/gen rate limits and clamped stress metrics
- scenario presets for deterministic contingency studies
- optional JSON metrics report for A/B runner workflows

potential extension: add a tuned --scenario-profile {demo,realistic,extreme} layer to normalize default severity so baseline runs are less harsh while keeping stress modes available.
"""


from __future__ import annotations

import argparse
import json
import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Camera, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import KeyframeAnimation, Parallel, Scene


PHASES = ["NORMAL", "CONTINGENCY", "CASCADE", "STABILIZE", "RECOVERY"]


@dataclass
class GridNode:
    name: str
    pos: Point
    role: str
    base_gen: float
    base_load: float
    criticality: float


@dataclass
class GridEdge:
    name: str
    src: str
    dst: str
    capacity: float
    kind: str


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


@dataclass
class ScenarioPreset:
    event_start_ratio: float
    event_duration_ratio: float
    fault_line: str
    fault_substation: str
    demand_spike_zone: str
    demand_spike_scale: float
    event_severity: float


@dataclass
class PolicyProfile:
    trip_hi: float
    trip_lo: float
    trip_hold: float
    isolate_hold: float
    edge_cooldown: float
    recover_threshold: float
    recover_hold: float
    load_ramp: float
    gen_ramp: float


SCENARIOS = {
    "line_trip": ScenarioPreset(
        event_start_ratio=0.20,
        event_duration_ratio=0.32,
        fault_line="S1_S2",
        fault_substation="",
        demand_spike_zone="",
        demand_spike_scale=1.0,
        event_severity=1.0,
    ),
    "substation_loss": ScenarioPreset(
        event_start_ratio=0.22,
        event_duration_ratio=0.38,
        fault_line="",
        fault_substation="S2",
        demand_spike_zone="",
        demand_spike_scale=1.0,
        event_severity=1.0,
    ),
    "demand_spike": ScenarioPreset(
        event_start_ratio=0.26,
        event_duration_ratio=0.30,
        fault_line="",
        fault_substation="",
        demand_spike_zone="S3",
        demand_spike_scale=1.7,
        event_severity=0.9,
    ),
    "multi_fault": ScenarioPreset(
        event_start_ratio=0.18,
        event_duration_ratio=0.48,
        fault_line="S2_S4",
        fault_substation="S3",
        demand_spike_zone="S2",
        demand_spike_scale=1.9,
        event_severity=1.2,
    ),
}


POLICIES = {
    "conservative": PolicyProfile(
        trip_hi=0.92,
        trip_lo=0.78,
        trip_hold=0.28,
        isolate_hold=0.26,
        edge_cooldown=1.2,
        recover_threshold=0.70,
        recover_hold=0.50,
        load_ramp=0.75,
        gen_ramp=0.70,
    ),
    "balanced": PolicyProfile(
        trip_hi=1.00,
        trip_lo=0.86,
        trip_hold=0.24,
        isolate_hold=0.22,
        edge_cooldown=1.0,
        recover_threshold=0.78,
        recover_hold=0.40,
        load_ramp=0.92,
        gen_ramp=0.86,
    ),
    "aggressive": PolicyProfile(
        trip_hi=1.08,
        trip_lo=0.92,
        trip_hold=0.20,
        isolate_hold=0.20,
        edge_cooldown=0.75,
        recover_threshold=0.86,
        recover_hold=0.26,
        load_ramp=1.08,
        gen_ramp=1.03,
    ),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def build_grid(width: int, height: int) -> tuple[dict[str, GridNode], list[GridEdge]]:
    cx = width / 2
    nodes = {
        "G1": GridNode("G1", Point(cx - 900, 260), "gen", 1.35, 0.0, 0.6),
        "G2": GridNode("G2", Point(cx + 900, 260), "gen", 1.28, 0.0, 0.6),
        "S1": GridNode("S1", Point(cx - 520, 620), "sub", 0.0, 0.22, 0.8),
        "S2": GridNode("S2", Point(cx - 90, 620), "sub", 0.0, 0.24, 0.9),
        "S3": GridNode("S3", Point(cx + 350, 620), "sub", 0.0, 0.24, 0.9),
        "S4": GridNode("S4", Point(cx + 740, 620), "sub", 0.0, 0.20, 0.8),
        "L1": GridNode("L1", Point(cx - 650, 1050), "load", 0.0, 0.28, 0.8),
        "L2": GridNode("L2", Point(cx - 170, 1090), "load", 0.0, 0.30, 1.0),
        "L3": GridNode("L3", Point(cx + 310, 1090), "load", 0.0, 0.27, 1.0),
        "L4": GridNode("L4", Point(cx + 760, 1040), "load", 0.0, 0.24, 0.8),
    }

    edges = [
        GridEdge("G1_S1", "G1", "S1", 1.18, "trunk"),
        GridEdge("G1_S2", "G1", "S2", 0.94, "trunk"),
        GridEdge("G2_S3", "G2", "S3", 1.10, "trunk"),
        GridEdge("G2_S4", "G2", "S4", 0.90, "trunk"),
        GridEdge("S1_S2", "S1", "S2", 0.76, "tie"),
        GridEdge("S2_S3", "S2", "S3", 0.80, "tie"),
        GridEdge("S3_S4", "S3", "S4", 0.76, "tie"),
        GridEdge("S2_S4", "S2", "S4", 0.62, "tie"),
        GridEdge("S1_L1", "S1", "L1", 0.60, "feed"),
        GridEdge("S2_L2", "S2", "L2", 0.66, "feed"),
        GridEdge("S3_L3", "S3", "L3", 0.66, "feed"),
        GridEdge("S4_L4", "S4", "L4", 0.56, "feed"),
        GridEdge("S2_L3", "S2", "L3", 0.44, "alt"),
        GridEdge("S3_L2", "S3", "L2", 0.44, "alt"),
    ]
    return nodes, edges


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated grid contingency cascade stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--dt", type=float, default=0.03, help="Simulation step size.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=97, help="Random seed.")

    p.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="line_trip",
        help="Contingency preset.",
    )
    p.add_argument(
        "--policy",
        choices=sorted(POLICIES.keys()),
        default="balanced",
        help="Protection/restore policy profile.",
    )

    p.add_argument("--event-start-ratio", type=float, default=None, help="Contingency start ratio.")
    p.add_argument("--event-duration-ratio", type=float, default=None, help="Contingency duration ratio.")
    p.add_argument("--fault-line", type=str, default=None, help="Line to force-trip during event.")
    p.add_argument("--fault-substation", type=str, default=None, help="Substation to force-isolate during event.")
    p.add_argument("--demand-spike-zone", type=str, default=None, help="Substation zone for load spike.")
    p.add_argument("--demand-spike-scale", type=float, default=None, help="Demand multiplier in spike zone.")
    p.add_argument("--event-severity", type=float, default=None, help="Scenario severity scalar.")

    p.add_argument("--packet-rate", type=float, default=2.3, help="Energy packet spawn rate per edge/sec.")
    p.add_argument("--packets-max", type=int, default=640, help="Max rendered packets.")

    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="hybrid",
        help="Camera framing mode.",
    )
    p.add_argument("--world-width", type=int, default=2500, help="World width.")
    p.add_argument("--world-height", type=int, default=1550, help="World height.")
    p.add_argument("--camera-width", type=float, default=980, help="Camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Camera height.")

    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument("--report-json", type=str, default="", help="Optional report output path.")
    p.add_argument(
        "--output",
        type=str,
        default="grid_contingency_cascade.gif",
        help="Output file (extension adjusted to --format).",
    )
    return p.parse_args()


def packet_keyframes(packet: Circle, rec: Packet, duration: float) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(at: float, p: Point) -> None:
        k = clamp(at / duration, 0.0, 1.0)
        tx[k] = p.x
        ty[k] = p.y

    stamp(0.0, rec.src)
    stamp(rec.start, rec.src)
    stamp(rec.end, rec.dst)
    stamp(duration, rec.dst)

    show = clamp((rec.start + 0.01 * duration) / duration, 0.0, 1.0)
    hide = clamp((rec.end + 0.01 * duration) / duration, 0.0, 1.0)
    sx[0.0] = sy[0.0] = 0.0
    sx[show] = sy[show] = 1.0
    sx[hide] = sy[hide] = 0.0
    sx[1.0] = sy[1.0] = 0.0
    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def build_components(nodes: dict[str, GridNode], edges: list[GridEdge], edge_active: dict[str, bool]) -> list[list[str]]:
    adj: dict[str, list[str]] = defaultdict(list)
    for e in edges:
        if edge_active[e.name]:
            adj[e.src].append(e.dst)
            adj[e.dst].append(e.src)

    seen: set[str] = set()
    comps: list[list[str]] = []
    for n in nodes:
        if n in seen:
            continue
        q = deque([n])
        seen.add(n)
        comp: list[str] = []
        while q:
            cur = q.popleft()
            comp.append(cur)
            for nxt in adj[cur]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        comps.append(comp)
    return comps


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    duration = max(1.0, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    packets_max = max(20, args.packets_max)
    packet_rate = max(0.1, args.packet_rate)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]

    event_start_ratio = float(choose(args.event_start_ratio, scenario.event_start_ratio))
    event_duration_ratio = float(choose(args.event_duration_ratio, scenario.event_duration_ratio))
    fault_line = str(choose(args.fault_line, scenario.fault_line))
    fault_substation = str(choose(args.fault_substation, scenario.fault_substation))
    demand_spike_zone = str(choose(args.demand_spike_zone, scenario.demand_spike_zone))
    demand_spike_scale = float(choose(args.demand_spike_scale, scenario.demand_spike_scale))
    event_severity = float(choose(args.event_severity, scenario.event_severity))

    event_start = clamp(event_start_ratio, 0.0, 0.95) * duration
    event_end = clamp(event_start_ratio + event_duration_ratio, 0.02, 0.98) * duration
    event_end = max(event_end, event_start + 0.2)

    nodes, edges = build_grid(args.world_width, args.world_height)
    edge_by_name = {e.name: e for e in edges}

    if fault_line and fault_line not in edge_by_name:
        fault_line = ""
    if fault_substation and fault_substation not in nodes:
        fault_substation = ""
    if demand_spike_zone and demand_spike_zone not in nodes:
        demand_spike_zone = ""

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(
            w=args.world_width,
            h=args.world_height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0.0,
        ).move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(
        Text("Grid Contingency Cascade", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 78)
        )
    )
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} fault_line={fault_line or '-'} fault_sub={fault_substation or '-'}",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 110))
    )

    for y, label in [(260, "Generation"), (620, "Substations"), (1050, "Loads")]:
        canvas.add(
            Arrow(
                p1=Point(140, y),
                p2=Point(args.world_width - 140, y),
                stroke=Colors.LightGray.transparent(0.25),
                width=1.0,
                marker_end=None,
            )
        )
        canvas.add(Text(label, size=12, fill=Colors.DarkGray, anchor="start").move_to(Point(120, y - 24)))

    edge_shapes: dict[str, Arrow] = {}
    for e in edges:
        p1 = nodes[e.src].pos
        p2 = nodes[e.dst].pos
        curve = clamp((p2.x - p1.x) / 2200.0, -0.22, 0.22)
        if e.kind == "trunk":
            stroke = Colors.MediumBlue.transparent(0.34)
        elif e.kind == "feed":
            stroke = Colors.SeaGreen.transparent(0.34)
        elif e.kind == "alt":
            stroke = Colors.DarkOrange.transparent(0.30)
        else:
            stroke = Colors.Gray.transparent(0.28)

        a = Arrow(
            p1=p1,
            p2=p2,
            curvature=curve,
            stroke=stroke,
            width=1.4,
            marker_end=None,
        )
        edge_shapes[e.name] = a
        canvas.add(a)

    node_shapes: dict[str, Circle] = {}
    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for n in nodes.values():
        if n.role == "gen":
            fill = Colors.LightYellow
        elif n.role == "sub":
            fill = Colors.LightCyan
        else:
            fill = Colors.MistyRose

        c = Circle(
            r=30 if n.role != "load" else 26,
            fill=fill,
            stroke=Colors.DarkBlue.transparent(0.70),
            width=1.3,
        ).move_to(n.pos)
        h = Circle(
            r=38 if n.role != "load" else 34,
            fill=Colors.Transparent,
            stroke=Colors.Crimson.transparent(0.70),
            width=0.7,
        ).move_to(n.pos)
        b = Rect(
            w=14,
            h=54,
            fill=Colors.SeaGreen.transparent(0.58),
            stroke=Colors.DarkGray.transparent(0.40),
            width=0.8,
        ).move_to(Point(n.pos.x + 48, n.pos.y))
        node_shapes[n.name] = c
        node_halos[n.name] = h
        node_bars[n.name] = b
        canvas.add(h, c, b)
        canvas.add(Text(n.name, size=10, fill=Colors.Black).move_to(n.pos))

    panel_x = 340
    panel_y = 420
    row_h = 44
    panel = Rect(
        w=350,
        h=row_h * len(PHASES) + 42,
        fill=Colors.White.transparent(0.90),
        stroke=Colors.DarkGray.transparent(0.65),
        width=1.1,
    ).move_to(Point(panel_x, panel_y))
    canvas.add(panel)
    canvas.add(Text("Grid Phase", size=15, fill=Colors.Black).move_to(Point(panel_x, panel_y - 128)))

    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=12, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 112, y)))

    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(
        Point(panel_x - 136, phase_rows["NORMAL"])
    )
    canvas.add(phase_indicator)

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    edge_active = {e.name: True for e in edges}
    edge_trip_timer = {e.name: 0.0 for e in edges}
    edge_recover_timer = {e.name: 0.0 for e in edges}
    edge_cooldown_until = {e.name: -1.0 for e in edges}
    edge_forced = {e.name: False for e in edges}

    node_forced_off = {n: False for n in nodes}
    node_isolate_timer = {n: 0.0 for n in nodes}
    node_isolated = {n: False for n in nodes}

    gen_actual = {n.name: n.base_gen for n in nodes.values()}
    load_actual = {n.name: n.base_load for n in nodes.values()}

    phase = "NORMAL"
    phase_log: list[tuple[float, str, str, str]] = []

    packets: list[Packet] = []
    transitions_trip = 0
    transitions_recover = 0

    total_nominal_load = 0.0
    total_served_load = 0.0
    shed_load = 0.0
    peak_overload = 0.0
    peak_island_count = 1
    last_trip_t = -1.0
    recovery_time = duration
    recovery_recorded = False

    tracks: dict[str, dict[float, float]] = {
        "phase_ty": {},
        "cam_tx": {},
        "cam_ty": {},
    }
    for n in nodes:
        tracks[f"halo_w_{n}"] = {}
        tracks[f"bar_sy_{n}"] = {}
    for e in edges:
        tracks[f"edge_w_{e.name}"] = {}

    def set_phase(t: float, new_phase: str, reason: str) -> None:
        nonlocal phase
        if new_phase != phase:
            phase_log.append((t, phase, new_phase, reason))
            phase = new_phase

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        in_event = event_start <= t <= event_end
        if in_event:
            set_phase(t, "CONTINGENCY", "event_window")

        # Forced contingencies.
        for ename in edge_forced:
            edge_forced[ename] = False
        for n in node_forced_off:
            node_forced_off[n] = False

        if in_event and fault_line:
            edge_forced[fault_line] = True
            edge_active[fault_line] = False
        if in_event and fault_substation:
            node_forced_off[fault_substation] = True

        # Load/gen targets with bounded ramps.
        for n in nodes.values():
            load_target = n.base_load
            if demand_spike_zone and in_event and n.name.startswith("L"):
                parent = "S" + n.name[1:]
                if parent == demand_spike_zone:
                    load_target *= demand_spike_scale
            load_target *= max(0.2, 1.0 + 0.05 * math.sin(0.6 * t + 0.7 * (ord(n.name[-1]) % 5)))
            max_step = policy.load_ramp * dt
            load_actual[n.name] += clamp(load_target - load_actual[n.name], -max_step, max_step)
            load_actual[n.name] = clamp(load_actual[n.name], 0.0, 3.0)

            gen_target = n.base_gen
            if n.role == "gen":
                if in_event:
                    gen_target *= max(0.35, 1.0 - 0.18 * event_severity)
                gen_target *= max(0.7, 1.0 + 0.04 * math.sin(0.45 * t + 0.3 * len(n.name)))
            else:
                gen_target = 0.0
            gstep = policy.gen_ramp * dt
            gen_actual[n.name] += clamp(gen_target - gen_actual[n.name], -gstep, gstep)
            gen_actual[n.name] = clamp(gen_actual[n.name], 0.0, 4.0)

        # Build effective active graph (drop edges touching forced-off substation).
        effective_active = dict(edge_active)
        for e in edges:
            if node_forced_off[e.src] or node_forced_off[e.dst]:
                effective_active[e.name] = False

        components = build_components(nodes, edges, effective_active)
        island_count = len(components)
        peak_island_count = max(peak_island_count, island_count)

        served_by_node = {n: 0.0 for n in nodes}
        shed_now = 0.0

        # Component-level balancing.
        for comp in components:
            comp_gen = sum(gen_actual[n] for n in comp)
            comp_load = sum(load_actual[n] for n in comp if nodes[n].role in {"sub", "load"})
            served_ratio = 1.0 if comp_load <= 1e-9 else clamp(comp_gen / comp_load, 0.0, 1.0)

            has_generator = any(nodes[n].role == "gen" for n in comp)
            for n in comp:
                if nodes[n].role in {"sub", "load"}:
                    demand = load_actual[n]
                    served = demand * served_ratio
                    served_by_node[n] = served
                    shed_now += max(0.0, demand - served)
                if not has_generator and nodes[n].role in {"sub", "load"}:
                    node_isolate_timer[n] += dt
                else:
                    node_isolate_timer[n] = max(0.0, node_isolate_timer[n] - 0.8 * dt)

        # Isolate guard with hold.
        for n in nodes:
            if nodes[n].role in {"sub", "load"} and node_isolate_timer[n] >= policy.isolate_hold:
                node_isolated[n] = True
            elif node_isolate_timer[n] <= 0.01:
                node_isolated[n] = False

        # Edge flow proxy from node imbalance differences.
        node_imbalance = {
            n: gen_actual[n] - (served_by_node[n] if nodes[n].role in {"sub", "load"} else 0.0)
            for n in nodes
        }
        overload = {}

        for e in edges:
            if not effective_active[e.name]:
                overload[e.name] = 0.0
                continue
            coupling = 0.95 if e.kind == "trunk" else 0.74
            flow = coupling * abs(node_imbalance[e.src] - node_imbalance[e.dst])
            ratio = flow / max(1e-6, e.capacity)
            overload[e.name] = ratio
            peak_overload = max(peak_overload, ratio)

        # Trip guard with hysteresis.
        any_trip = False
        for e in edges:
            if edge_forced[e.name]:
                edge_trip_timer[e.name] = 0.0
                edge_recover_timer[e.name] = 0.0
                continue

            if effective_active[e.name] and overload[e.name] > policy.trip_hi:
                edge_trip_timer[e.name] += dt
                if edge_trip_timer[e.name] >= policy.trip_hold:
                    edge_active[e.name] = False
                    edge_cooldown_until[e.name] = t + policy.edge_cooldown
                    edge_trip_timer[e.name] = 0.0
                    edge_recover_timer[e.name] = 0.0
                    transitions_trip += 1
                    any_trip = True
                    last_trip_t = t
            elif overload[e.name] < policy.trip_lo:
                edge_trip_timer[e.name] = max(0.0, edge_trip_timer[e.name] - 1.2 * dt)

        if any_trip:
            set_phase(t, "CASCADE", "line_trip_guard")

        # Recover guard with cooldown + stable hold.
        for e in edges:
            if edge_forced[e.name]:
                continue
            if edge_active[e.name]:
                edge_recover_timer[e.name] = 0.0
                continue
            if t < edge_cooldown_until[e.name]:
                continue

            safe = overload.get(e.name, 0.0) < policy.recover_threshold
            if safe:
                edge_recover_timer[e.name] += dt
                if edge_recover_timer[e.name] >= policy.recover_hold:
                    edge_active[e.name] = True
                    edge_recover_timer[e.name] = 0.0
                    transitions_recover += 1
            else:
                edge_recover_timer[e.name] = 0.0

        # Phase progression.
        if phase == "CONTINGENCY" and any_trip:
            set_phase(t, "CASCADE", "trip_detected")
        if phase in {"CONTINGENCY", "CASCADE"} and not any_trip and t > event_end:
            set_phase(t, "STABILIZE", "post_event")
        if phase == "STABILIZE" and peak_overload < policy.trip_hi + 0.2:
            set_phase(t, "RECOVERY", "stable_flow")

        # Recovery time metric when stable after event.
        if (
            not recovery_recorded
            and t > event_end
            and last_trip_t >= 0.0
            and (t - last_trip_t) > max(policy.recover_hold, 0.35)
            and max(overload.values() or [0.0]) < policy.recover_threshold
            and island_count <= 2
        ):
            recovery_time = t - event_start
            recovery_recorded = True

        # Demand accounting.
        nominal_now = sum(load_actual[n] for n in nodes if nodes[n].role in {"sub", "load"})
        served_now = sum(served_by_node[n] for n in served_by_node)
        total_nominal_load += nominal_now * dt
        total_served_load += served_now * dt
        shed_load += shed_now * dt

        # Packet generation.
        if len(packets) < packets_max:
            for e in edges:
                if not effective_active[e.name]:
                    continue
                base_rate = packet_rate * clamp(0.2 + overload[e.name], 0.2, 2.4)
                if rng.random() < base_rate * dt and len(packets) < packets_max:
                    st = clamp(t + rng.uniform(-0.05, 0.05), 0.0, duration)
                    et = clamp(st + rng.uniform(0.50, 1.00), st + 0.02, duration)
                    if e.kind == "trunk":
                        color = Colors.MediumBlue
                    elif e.kind == "feed":
                        color = Colors.SeaGreen
                    elif e.kind == "alt":
                        color = Colors.DarkOrange
                    else:
                        color = Colors.Gray
                    packets.append(Packet(nodes[e.src].pos, nodes[e.dst].pos, st, et, color))

        # Tracks.
        tracks["phase_ty"][k] = phase_rows[phase]
        hotspot = max(nodes.keys(), key=lambda n: (load_actual[n] - served_by_node.get(n, 0.0)) * nodes[n].criticality)
        for n in nodes:
            if nodes[n].role in {"sub", "load"}:
                shed_ratio = (load_actual[n] - served_by_node.get(n, 0.0)) / max(1e-6, load_actual[n])
            else:
                shed_ratio = 0.0
            if node_isolated[n]:
                shed_ratio = max(shed_ratio, 0.95)
            stress = clamp(shed_ratio, 0.0, 1.0)
            tracks[f"halo_w_{n}"][k] = 0.8 + 4.2 * stress
            util = 0.0 if nodes[n].role == "gen" else clamp(load_actual[n], 0.0, 1.5)
            tracks[f"bar_sy_{n}"][k] = 0.30 + 1.20 * util / 1.5

        for e in edges:
            if not effective_active[e.name]:
                tracks[f"edge_w_{e.name}"][k] = 0.35
            else:
                tracks[f"edge_w_{e.name}"][k] = 1.1 + 2.6 * clamp(overload[e.name], 0.0, 1.4)

        center = Point(args.world_width / 2, args.world_height / 2)
        hot = nodes[hotspot].pos
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.72 + center * 0.28
        else:
            if phase in {"NORMAL", "CONTINGENCY"}:
                cam = nodes["S2"].pos * 0.54 + nodes["S3"].pos * 0.46
            elif phase == "CASCADE":
                cam = hot * 0.64 + nodes["S2"].pos * 0.36
            else:
                cam = hot * 0.44 + center * 0.56
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

    packet_anims = []
    for i, p in enumerate(packets):
        pkt = Circle(
            r=4.0 + (i % 2),
            fill=p.color.transparent(0.86),
            stroke=Colors.Black.transparent(0.18),
            width=0.6,
        ).move_to(p.src)
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, p, duration))

    anims = [
        KeyframeAnimation(phase_indicator, ty=tracks["phase_ty"]),
        KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"]),
    ]

    for n in nodes:
        anims.append(KeyframeAnimation(node_halos[n], width=tracks[f"halo_w_{n}"]))
        anims.append(KeyframeAnimation(node_bars[n], sy=tracks[f"bar_sy_{n}"]))
    for e in edges:
        anims.append(KeyframeAnimation(edge_shapes[e.name], width=tracks[f"edge_w_{e.name}"]))

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(Parallel(*(anims + packet_anims)), duration=duration)

    result = render_scene(
        scene,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
        ),
    )
    out = result.output_path

    service_level = 1.0 if total_nominal_load <= 1e-9 else clamp(total_served_load / total_nominal_load, 0.0, 1.0)
    island_count = peak_island_count

    print(f"✅ Saved: {out}")
    print(
        f"   scenario={args.scenario} policy={args.policy} phase={phase} "
        f"event=[{event_start:.2f}s,{event_end:.2f}s] trips={transitions_trip} recovers={transitions_recover}"
    )
    print(
        f"   service_level={service_level:.3f} peak_overload={peak_overload:.3f} "
        f"island_count={island_count} shed_load={shed_load:.3f} recovery_time={recovery_time:.2f}s"
    )

    if args.report_json:
        report = {
            "scenario": args.scenario,
            "policy": args.policy,
            "seed": args.seed,
            "duration": duration,
            "dt": dt,
            "fps": fps,
            "camera_mode": args.camera_mode,
            "event": {
                "start_s": event_start,
                "end_s": event_end,
                "fault_line": fault_line,
                "fault_substation": fault_substation,
                "demand_spike_zone": demand_spike_zone,
                "demand_spike_scale": demand_spike_scale,
                "event_severity": event_severity,
            },
            "metrics": {
                "service_level": service_level,
                "peak_overload": peak_overload,
                "island_count": island_count,
                "shed_load": shed_load,
                "recovery_time": recovery_time,
                "trips": transitions_trip,
                "recovers": transitions_recover,
                "visible_packets": len(packets),
                "phase_transitions": len(phase_log),
                "final_phase": phase,
            },
        }
        path = Path(args.report_json)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={path}")


if __name__ == "__main__":
    main()
