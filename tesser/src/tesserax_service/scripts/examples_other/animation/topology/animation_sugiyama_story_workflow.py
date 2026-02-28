#!/usr/bin/env python3
"""Sugiyama workflow story animation for Tesserax.

This example intentionally emphasizes:
1) clear engineering comments around non-trivial logic
2) notation/legend overlays embedded directly in the rendered output
3) the established scenario/policy/report CLI pattern used in other examples
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Camera, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import KeyframeAnimation, Parallel, Scene
from tesserax.layout import HierarchicalLayout


PHASES = ["OBSERVE", "TRIAGE", "MITIGATE", "RECOVER", "POST"]


@dataclass
class WorkflowNodeSpec:
    layer: int
    role: str
    criticality: float
    base_load: float


@dataclass
class WorkflowScenario:
    event_start_ratio: float
    event_duration_ratio: float
    stressed_nodes: tuple[str, ...]
    stress_intensity: float
    replay_factor: float
    branch_bias: float


@dataclass
class WorkflowPolicy:
    detect_threshold: float
    triage_delay: float
    mitigation_gain: float
    recovery_gain: float
    reroute_gain: float


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


NODE_SPECS: dict[str, WorkflowNodeSpec] = {
    "INTAKE": WorkflowNodeSpec(layer=0, role="source", criticality=0.55, base_load=0.48),
    "VALIDATE": WorkflowNodeSpec(layer=1, role="gate", criticality=0.86, base_load=0.58),
    "ENRICH": WorkflowNodeSpec(layer=2, role="compute", criticality=0.70, base_load=0.52),
    "ROUTE_A": WorkflowNodeSpec(layer=3, role="branch", criticality=0.65, base_load=0.46),
    "ROUTE_B": WorkflowNodeSpec(layer=3, role="branch", criticality=0.65, base_load=0.46),
    "HUMAN_REVIEW": WorkflowNodeSpec(layer=4, role="review", criticality=0.95, base_load=0.42),
    "MERGE": WorkflowNodeSpec(layer=5, role="merge", criticality=0.82, base_load=0.50),
    "SCORE": WorkflowNodeSpec(layer=6, role="compute", criticality=0.90, base_load=0.56),
    "PUBLISH": WorkflowNodeSpec(layer=7, role="sink", criticality=1.00, base_load=0.52),
    "ARCHIVE": WorkflowNodeSpec(layer=7, role="sink", criticality=0.50, base_load=0.30),
}

# DAG edges for Sugiyama-style layering. The graph is intentionally acyclic.
EDGES: list[tuple[str, str]] = [
    ("INTAKE", "VALIDATE"),
    ("VALIDATE", "ENRICH"),
    ("ENRICH", "ROUTE_A"),
    ("ENRICH", "ROUTE_B"),
    ("ROUTE_A", "HUMAN_REVIEW"),
    ("ROUTE_B", "HUMAN_REVIEW"),
    ("HUMAN_REVIEW", "MERGE"),
    ("MERGE", "SCORE"),
    ("SCORE", "PUBLISH"),
    ("MERGE", "ARCHIVE"),
]

SCENARIOS = {
    "validation_storm": WorkflowScenario(
        event_start_ratio=0.22,
        event_duration_ratio=0.34,
        stressed_nodes=("VALIDATE", "HUMAN_REVIEW"),
        stress_intensity=1.60,
        replay_factor=1.35,
        branch_bias=0.10,
    ),
    "enrichment_latency": WorkflowScenario(
        event_start_ratio=0.28,
        event_duration_ratio=0.30,
        stressed_nodes=("ENRICH", "SCORE"),
        stress_intensity=1.52,
        replay_factor=1.22,
        branch_bias=0.18,
    ),
    "review_backlog": WorkflowScenario(
        event_start_ratio=0.20,
        event_duration_ratio=0.42,
        stressed_nodes=("HUMAN_REVIEW", "MERGE"),
        stress_intensity=1.78,
        replay_factor=1.60,
        branch_bias=0.35,
    ),
    "downstream_degradation": WorkflowScenario(
        event_start_ratio=0.26,
        event_duration_ratio=0.36,
        stressed_nodes=("SCORE", "PUBLISH"),
        stress_intensity=1.70,
        replay_factor=1.28,
        branch_bias=0.22,
    ),
}

POLICIES = {
    "strict": WorkflowPolicy(
        detect_threshold=0.23,
        triage_delay=0.70,
        mitigation_gain=1.05,
        recovery_gain=0.55,
        reroute_gain=0.25,
    ),
    "balanced": WorkflowPolicy(
        detect_threshold=0.28,
        triage_delay=0.95,
        mitigation_gain=0.86,
        recovery_gain=0.42,
        reroute_gain=0.18,
    ),
    "throughput": WorkflowPolicy(
        detect_threshold=0.34,
        triage_delay=1.20,
        mitigation_gain=0.66,
        recovery_gain=0.30,
        reroute_gain=0.35,
    ),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated Sugiyama workflow story stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--dt", type=float, default=0.03, help="Simulation step size.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=173, help="Random seed.")

    p.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="validation_storm",
        help="Workflow incident scenario preset.",
    )
    p.add_argument(
        "--policy",
        choices=sorted(POLICIES.keys()),
        default="balanced",
        help="Response policy profile.",
    )

    p.add_argument("--event-start-ratio", type=float, default=None, help="Override event start ratio.")
    p.add_argument("--event-duration-ratio", type=float, default=None, help="Override event duration ratio.")
    p.add_argument("--stress-intensity", type=float, default=None, help="Override stress intensity.")
    p.add_argument("--replay-factor", type=float, default=None, help="Override replay multiplier.")
    p.add_argument("--branch-bias", type=float, default=None, help="Override branch skew (toward review-heavy path).")

    p.add_argument("--packet-rate", type=float, default=2.5, help="Packet spawn rate per edge per second.")
    p.add_argument("--packets-max", type=int, default=620, help="Maximum rendered packets.")

    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="hybrid",
        help="Camera framing mode.",
    )
    p.add_argument("--world-width", type=int, default=2600, help="World width.")
    p.add_argument("--world-height", type=int, default=1600, help="World height.")
    p.add_argument("--camera-width", type=float, default=980, help="Camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Camera height.")

    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument("--report-json", type=str, default="", help="Optional report JSON output path.")
    p.add_argument(
        "--output",
        type=str,
        default="sugiyama_story_workflow.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def packet_keyframes(packet: Circle, rec: Packet, duration: float) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    # We stamp absolute time values into normalized keyframe coordinates.
    # This lets packets appear/disappear independently but still share one timeline.
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


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    duration = max(1.0, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    packet_rate = max(0.1, args.packet_rate)
    packets_max = max(20, args.packets_max)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]

    event_start_ratio = float(choose(args.event_start_ratio, scenario.event_start_ratio))
    event_duration_ratio = float(choose(args.event_duration_ratio, scenario.event_duration_ratio))
    stress_intensity = float(choose(args.stress_intensity, scenario.stress_intensity))
    replay_factor = float(choose(args.replay_factor, scenario.replay_factor))
    branch_bias = float(choose(args.branch_bias, scenario.branch_bias))

    event_start = clamp(event_start_ratio, 0.0, 0.95) * duration
    event_end = clamp(event_start_ratio + event_duration_ratio, 0.02, 0.98) * duration
    event_end = max(event_end, event_start + 0.2)

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
        Text("Sugiyama Story Workflow", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 76)
        )
    )
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} event=[{event_start:.2f}s,{event_end:.2f}s]",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 106))
    )

    # Workflow banding improves readability by aligning the story with layer progression.
    for x, label in [(260, "Intake"), (860, "Transformation"), (1460, "Decision"), (2060, "Delivery")]:
        canvas.add(
            Arrow(
                p1=Point(x, 170),
                p2=Point(x, args.world_height - 120),
                stroke=Colors.LightGray.transparent(0.20),
                width=1.0,
                marker_end=None,
            )
        )
        canvas.add(Text(label, size=11, fill=Colors.DarkGray).move_to(Point(x + 70, 150)))

    # Build node shapes first, then run hierarchical layout so edges can use final coordinates.
    node_shapes: dict[str, Rect] = {}
    with HierarchicalLayout(orientation="horizontal", rank_sep=120, node_sep=56) as dag:
        for name, spec in NODE_SPECS.items():
            if spec.role == "source":
                fill = Colors.LightYellow
            elif spec.role in {"sink", "review"}:
                fill = Colors.MistyRose
            else:
                fill = Colors.LightCyan

            node = Rect(
                w=126,
                h=46,
                fill=fill,
                stroke=Colors.DarkBlue.transparent(0.72),
                width=1.3,
            )
            node_shapes[name] = node
            if spec.layer == 0:
                dag.root(node)

        for src, dst in EDGES:
            dag.connect(node_shapes[src], node_shapes[dst])

        # Explicit rerun after all edges are present is important for stable ordering.
        dag.do_layout()

    # Shift the whole DAG into visible world space after layout computes local coordinates.
    for name, shape in node_shapes.items():
        shape.transform.tx += 360
        shape.transform.ty += 360

    # The DAG group owns node rectangles; add the group once to avoid parent conflicts.
    canvas.add(dag)

    # Node overlays: halos convey risk, bars convey queue pressure.
    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for name, shape in node_shapes.items():
        center = shape.anchor("center")
        halo = Circle(
            r=34,
            fill=Colors.Transparent,
            stroke=Colors.Crimson.transparent(0.70),
            width=0.7,
        ).move_to(center)
        bar = Rect(
            w=12,
            h=44,
            fill=Colors.SeaGreen.transparent(0.58),
            stroke=Colors.DarkGray.transparent(0.42),
            width=0.8,
        ).move_to(Point(center.x + 72, center.y))

        node_halos[name] = halo
        node_bars[name] = bar
        canvas.add(halo, bar)
        canvas.add(Text(name, size=9, fill=Colors.Black).move_to(center))

    # Draw edges after positioning so arrows match Sugiyama placement.
    edge_shapes: dict[tuple[str, str], Arrow] = {}
    for src, dst in EDGES:
        p1 = node_shapes[src].anchor("right")
        p2 = node_shapes[dst].anchor("left")
        curve = clamp((p2.y - p1.y) / 280.0, -0.20, 0.20)
        arrow = Arrow(
            p1=p1,
            p2=p2,
            curvature=curve,
            stroke=Colors.Gray.transparent(0.34),
            width=1.3,
            marker_end=None,
        )
        edge_shapes[(src, dst)] = arrow
        canvas.add(arrow)

    # Phase panel for state transitions.
    panel_x = 310
    panel_y = 390
    row_h = 40
    phase_panel = Rect(
        w=330,
        h=row_h * len(PHASES) + 40,
        fill=Colors.White.transparent(0.90),
        stroke=Colors.DarkGray.transparent(0.64),
        width=1.1,
    ).move_to(Point(panel_x, panel_y))
    canvas.add(phase_panel)
    canvas.add(Text("Workflow Phase", size=14, fill=Colors.Black).move_to(Point(panel_x, panel_y - 120)))

    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=11, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 105, y)))

    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(
        Point(panel_x - 128, phase_rows["OBSERVE"])
    )
    canvas.add(phase_indicator)

    # Embedded legend/notation panel (explicitly requested for in-canvas interpretation).
    legend = Rect(
        w=510,
        h=300,
        fill=Colors.White.transparent(0.93),
        stroke=Colors.DarkGray.transparent(0.64),
        width=1.1,
    ).move_to(Point(args.world_width - 330, 330))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 330, 196)))

    lx = args.world_width - 550
    ly = 240
    canvas.add(Rect(w=20, h=12, fill=Colors.LightYellow, stroke=Colors.DarkBlue, width=1.0).move_to(Point(lx, ly)))
    canvas.add(Text("Source node", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 24
    canvas.add(Rect(w=20, h=12, fill=Colors.LightCyan, stroke=Colors.DarkBlue, width=1.0).move_to(Point(lx, ly)))
    canvas.add(Text("Compute/branch node", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 24
    canvas.add(Rect(w=20, h=12, fill=Colors.MistyRose, stroke=Colors.DarkBlue, width=1.0).move_to(Point(lx, ly)))
    canvas.add(Text("Review/sink node", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 28

    canvas.add(Circle(r=8, fill=Colors.Transparent, stroke=Colors.Crimson, width=2.0).move_to(Point(lx, ly)))
    canvas.add(Text("Halo width ~ risk_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 24
    canvas.add(Rect(w=10, h=26, fill=Colors.SeaGreen, stroke=Colors.DarkGray, width=1.0).move_to(Point(lx, ly)))
    canvas.add(Text("Bar scale ~ queue_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 24
    canvas.add(Arrow(p1=Point(lx - 9, ly), p2=Point(lx + 9, ly), stroke=Colors.Gray, width=2.0, marker_end=None))
    canvas.add(Text("Edge width ~ flow_{u->v}", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 24

    canvas.add(Circle(r=5, fill=Colors.MediumBlue, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Blue packet: nominal", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 20
    canvas.add(Circle(r=5, fill=Colors.DarkOrange, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Orange packet: degraded", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))
    ly += 20
    canvas.add(Circle(r=5, fill=Colors.Crimson, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Red packet: incident pressure", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 24, ly)))

    canvas.add(Text("risk_i = clamp(error_i + 0.6*queue_i, 0, 1)", size=10, fill=Colors.DarkGray).move_to(Point(args.world_width - 330, 450)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    phase = "OBSERVE"
    phase_entry = 0.0
    transitions = 0
    detect_time: float | None = None
    recover_time: float | None = None

    load = {n: NODE_SPECS[n].base_load for n in NODE_SPECS}
    queue = {n: 0.06 for n in NODE_SPECS}
    error = {n: 0.03 for n in NODE_SPECS}

    inflow: dict[str, list[str]] = {n: [] for n in NODE_SPECS}
    outflow: dict[str, list[str]] = {n: [] for n in NODE_SPECS}
    for u, v in EDGES:
        inflow[v].append(u)
        outflow[u].append(v)

    edge_flow = {(u, v): 0.15 for (u, v) in EDGES}
    packets: list[Packet] = []

    peak_queue = 0.0
    peak_risk = 0.0
    total_expected = 0.0
    total_processed = 0.0

    tracks: dict[str, dict[float, float]] = {
        "phase_ty": {},
        "cam_tx": {},
        "cam_ty": {},
    }
    for n in NODE_SPECS:
        tracks[f"halo_w_{n}"] = {}
        tracks[f"bar_sy_{n}"] = {}
    for e in EDGES:
        tracks[f"edge_w_{e[0]}_{e[1]}"] = {}

    def set_phase(t: float, new_phase: str, why: str) -> None:
        nonlocal phase, phase_entry, transitions, detect_time, recover_time
        if new_phase == phase:
            return
        phase = new_phase
        phase_entry = t
        transitions += 1
        if new_phase == "TRIAGE" and detect_time is None:
            detect_time = t
        if new_phase == "RECOVER" and recover_time is None:
            recover_time = t

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        in_event = event_start <= t <= event_end

        # Branch logic gives a controllable skew toward the review-heavy path.
        bias = 0.5 + branch_bias * (1.0 if in_event else 0.0)
        bias = clamp(bias, 0.05, 0.95)

        # Phase transition guards.
        global_risk = (
            sum((error[n] + 0.6 * queue[n]) * NODE_SPECS[n].criticality for n in NODE_SPECS)
            / sum(NODE_SPECS[n].criticality for n in NODE_SPECS)
        )
        if phase == "OBSERVE" and global_risk >= policy.detect_threshold:
            set_phase(t, "TRIAGE", "risk_threshold")
        elif phase == "TRIAGE" and (t - phase_entry) >= policy.triage_delay:
            set_phase(t, "MITIGATE", "triage_complete")
        elif phase == "MITIGATE" and t > event_end and global_risk <= policy.detect_threshold * 0.8:
            set_phase(t, "RECOVER", "risk_reduced")
        elif phase == "RECOVER" and global_risk <= policy.detect_threshold * 0.55:
            set_phase(t, "POST", "stable")

        # 1) Compute expected load per node from parents + base profile.
        # This gives a simple dynamic model while keeping behavior interpretable.
        expected = {}
        for n, spec in NODE_SPECS.items():
            incoming = 0.0
            if inflow[n]:
                incoming = sum(edge_flow[(u, n)] for u in inflow[n]) / len(inflow[n])
            expected[n] = 0.45 * spec.base_load + 0.70 * incoming

        # 2) Scenario event injects stress on selected nodes.
        if in_event:
            for n in scenario.stressed_nodes:
                expected[n] *= stress_intensity
                error[n] += 0.23 * dt
                queue[n] += 0.30 * replay_factor * dt

        # 3) Policy actions tune mitigation + recovery behavior.
        if phase in {"MITIGATE", "RECOVER", "POST"}:
            for n in NODE_SPECS:
                error[n] -= policy.mitigation_gain * 0.34 * dt
                queue[n] -= policy.reroute_gain * 0.20 * dt
        if phase in {"RECOVER", "POST"}:
            for n in NODE_SPECS:
                queue[n] -= policy.recovery_gain * 0.26 * dt

        # 4) Update node state with bounded dynamics to avoid unstable oscillation.
        for n in NODE_SPECS:
            load[n] += clamp(expected[n] - load[n], -0.95 * dt, 0.95 * dt)
            load[n] = clamp(load[n], 0.02, 2.2)

            capacity = 0.92 if NODE_SPECS[n].role != "review" else 0.72
            backlog = max(0.0, load[n] - capacity)
            queue[n] += backlog * 0.30 * dt
            queue[n] -= (0.10 + 0.10 * (1.0 - error[n])) * dt

            # Small baseline noise keeps motion perceptible without dominating behavior.
            error[n] += 0.02 * math.sin(0.7 * t + 0.35 * (len(n) % 5)) * dt

            queue[n] = clamp(queue[n], 0.0, 2.0)
            error[n] = clamp(error[n], 0.0, 1.0)

        # 5) Derive edge flows from node throughput, with branch split controls.
        for u, v in EDGES:
            base = clamp(load[u] * (1.0 - 0.45 * error[u]), 0.0, 1.8)
            if (u, v) == ("ENRICH", "ROUTE_A"):
                split = bias
            elif (u, v) == ("ENRICH", "ROUTE_B"):
                split = 1.0 - bias
            else:
                split = 1.0
            edge_flow[(u, v)] = clamp(base * split, 0.0, 2.0)

        # Load accounting for service-level metric.
        expected_out = load["PUBLISH"] + load["ARCHIVE"]
        processed_out = expected_out * (1.0 - 0.55 * (error["PUBLISH"] + error["ARCHIVE"]) / 2.0)
        total_expected += expected_out * dt
        total_processed += max(0.0, processed_out) * dt

        # Spawn visual packets from edge flow level.
        if len(packets) < packets_max:
            for u, v in EDGES:
                rate = packet_rate * clamp(edge_flow[(u, v)], 0.0, 1.6)
                if rng.random() < rate * dt and len(packets) < packets_max:
                    st = clamp(t + rng.uniform(-0.05, 0.05), 0.0, duration)
                    et = clamp(st + rng.uniform(0.45, 0.95), st + 0.02, duration)
                    risk_u = clamp(error[u] + 0.6 * queue[u], 0.0, 1.0)
                    if risk_u > 0.68:
                        color = Colors.Crimson
                    elif risk_u > 0.34:
                        color = Colors.DarkOrange
                    else:
                        color = Colors.MediumBlue
                    packets.append(
                        Packet(
                            src=node_shapes[u].anchor("right"),
                            dst=node_shapes[v].anchor("left"),
                            start=st,
                            end=et,
                            color=color,
                        )
                    )

        # Track visual channels.
        tracks["phase_ty"][k] = phase_rows[phase]

        hotspot = max(NODE_SPECS.keys(), key=lambda n: (error[n] + 0.6 * queue[n]) * NODE_SPECS[n].criticality)
        for n in NODE_SPECS:
            risk = clamp(error[n] + 0.6 * queue[n], 0.0, 1.0)
            peak_risk = max(peak_risk, risk)
            peak_queue = max(peak_queue, queue[n])
            tracks[f"halo_w_{n}"][k] = 0.8 + 4.2 * risk
            tracks[f"bar_sy_{n}"][k] = 0.30 + 1.25 * clamp(queue[n], 0.0, 1.6) / 1.6

        for u, v in EDGES:
            tracks[f"edge_w_{u}_{v}"][k] = 1.0 + 2.5 * clamp(edge_flow[(u, v)], 0.0, 1.6) / 1.6

        hot = node_shapes[hotspot].anchor("center")
        center = Point(args.world_width / 2, args.world_height / 2)
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.74 + center * 0.26
        else:
            if phase in {"OBSERVE", "TRIAGE"}:
                cam = node_shapes["VALIDATE"].anchor("center") * 0.66 + node_shapes["ENRICH"].anchor("center") * 0.34
            elif phase == "MITIGATE":
                cam = hot * 0.62 + node_shapes["HUMAN_REVIEW"].anchor("center") * 0.38
            else:
                cam = hot * 0.42 + center * 0.58
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

    packet_anims = []
    for i, rec in enumerate(packets):
        pkt = Circle(
            r=4.0 + (i % 2),
            fill=rec.color.transparent(0.86),
            stroke=Colors.Black.transparent(0.18),
            width=0.6,
        ).move_to(rec.src)
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration))

    anims = [
        KeyframeAnimation(phase_indicator, ty=tracks["phase_ty"]),
        KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"]),
    ]

    for n in NODE_SPECS:
        anims.append(KeyframeAnimation(node_halos[n], width=tracks[f"halo_w_{n}"]))
        anims.append(KeyframeAnimation(node_bars[n], sy=tracks[f"bar_sy_{n}"]))

    for u, v in EDGES:
        anims.append(KeyframeAnimation(edge_shapes[(u, v)], width=tracks[f"edge_w_{u}_{v}"]))

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

    service_level = 1.0 if total_expected <= 1e-9 else clamp(total_processed / total_expected, 0.0, 1.0)
    mttd = max(0.0, (detect_time if detect_time is not None else duration) - event_start)
    mttr = max(0.0, (recover_time if recover_time is not None else duration) - event_start)

    print(f"✅ Saved: {out}")
    print(
        f"   scenario={args.scenario} policy={args.policy} phase={phase} "
        f"packets={len(packets)} transitions={transitions}"
    )
    print(
        f"   service_level={service_level:.3f} peak_queue={peak_queue:.3f} "
        f"peak_risk={peak_risk:.3f} mttd={mttd:.2f}s mttr={mttr:.2f}s"
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
                "stress_intensity": stress_intensity,
                "replay_factor": replay_factor,
                "branch_bias": branch_bias,
                "stressed_nodes": list(scenario.stressed_nodes),
            },
            "metrics": {
                "service_level": service_level,
                "peak_queue": peak_queue,
                "peak_risk": peak_risk,
                "mttd": mttd,
                "mttr": mttr,
                "transitions": transitions,
                "visible_packets": len(packets),
                "final_phase": phase,
            },
        }
        path = Path(args.report_json)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={path}")


if __name__ == "__main__":
    main()
