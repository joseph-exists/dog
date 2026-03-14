#!/usr/bin/env python3
"""Force-directed supply-chain network stress animation scaffold for Tesserax.

Scaffold intent:
- scenario/policy/report-json compatibility with other examples
- clear inline comments around flow and stress equations
- legend/notation rendered inside output frames
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
from tesserax.layout import ForceLayout


PHASES = ["STEADY", "SHOCK", "REROUTE", "RECOVER", "STABLE"]


@dataclass
class NodeSpec:
    role: str
    base_inventory: float
    target_inventory: float
    demand_rate: float


@dataclass
class EdgeSpec:
    capacity: float
    kind: str


@dataclass
class ScenarioPreset:
    event_start_ratio: float
    event_duration_ratio: float
    disrupted_edges: tuple[tuple[str, str], ...]
    severity: float
    demand_spike_node: str
    demand_spike_scale: float


@dataclass
class PolicyPreset:
    reroute_gain: float
    replenish_gain: float
    recovery_gain: float
    backlog_relief: float


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


NODE_SPECS = {
    "SUP_W": NodeSpec("supplier", 120.0, 150.0, 0.0),
    "SUP_E": NodeSpec("supplier", 120.0, 150.0, 0.0),
    "PLANT": NodeSpec("plant", 52.0, 95.0, 0.0),
    "DC_N": NodeSpec("dc", 34.0, 78.0, 0.0),
    "DC_S": NodeSpec("dc", 34.0, 78.0, 0.0),
    "STORE_A": NodeSpec("store", 18.0, 52.0, 10.6),
    "STORE_B": NodeSpec("store", 18.0, 52.0, 11.2),
    "STORE_C": NodeSpec("store", 18.0, 52.0, 10.0),
}

EDGE_SPECS: dict[tuple[str, str], EdgeSpec] = {
    ("SUP_W", "PLANT"): EdgeSpec(10.0, "primary"),
    ("SUP_E", "PLANT"): EdgeSpec(10.0, "primary"),
    ("SUP_W", "DC_N"): EdgeSpec(4.5, "alt"),
    ("SUP_E", "DC_S"): EdgeSpec(4.5, "alt"),
    ("PLANT", "DC_N"): EdgeSpec(8.5, "primary"),
    ("PLANT", "DC_S"): EdgeSpec(8.5, "primary"),
    ("DC_N", "STORE_A"): EdgeSpec(6.0, "primary"),
    ("DC_N", "STORE_B"): EdgeSpec(5.8, "primary"),
    ("DC_S", "STORE_B"): EdgeSpec(5.8, "primary"),
    ("DC_S", "STORE_C"): EdgeSpec(6.0, "primary"),
    ("DC_N", "STORE_C"): EdgeSpec(3.2, "alt"),
    ("DC_S", "STORE_A"): EdgeSpec(3.2, "alt"),
    ("DC_N", "DC_S"): EdgeSpec(4.0, "balance"),
    ("DC_S", "DC_N"): EdgeSpec(4.0, "balance"),
}

SCENARIOS = {
    "port_delay": ScenarioPreset(0.22, 0.34, (("SUP_W", "PLANT"),), 0.88, "STORE_B", 1.35),
    "lane_disruption": ScenarioPreset(0.25, 0.36, (("PLANT", "DC_N"), ("PLANT", "DC_S")), 0.76, "STORE_A", 1.22),
    "demand_wave": ScenarioPreset(0.20, 0.30, (), 0.0, "STORE_C", 1.85),
    "multi_shock": ScenarioPreset(0.18, 0.46, (("SUP_W", "PLANT"), ("PLANT", "DC_N"), ("DC_N", "STORE_A")), 0.92, "STORE_A", 1.95),
}

POLICIES = {
    "lean": PolicyPreset(0.74, 0.68, 0.24, 0.20),
    "balanced": PolicyPreset(1.00, 1.00, 0.34, 0.30),
    "resilient": PolicyPreset(1.28, 1.24, 0.46, 0.42),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated force-directed supply-chain stress scaffold.")
    p.add_argument("--duration", type=float, default=12.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--seed", type=int, default=193)

    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="port_delay")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="balanced")

    p.add_argument("--event-start-ratio", type=float, default=None)
    p.add_argument("--event-duration-ratio", type=float, default=None)
    p.add_argument("--severity", type=float, default=None)
    p.add_argument("--demand-spike-scale", type=float, default=None)

    p.add_argument("--packet-rate", type=float, default=2.4)
    p.add_argument("--packets-max", type=int, default=640)

    p.add_argument("--camera-mode", choices=["fixed", "track", "hybrid"], default="hybrid")
    p.add_argument("--world-width", type=int, default=2600)
    p.add_argument("--world-height", type=int, default=1600)
    p.add_argument("--camera-width", type=float, default=980)
    p.add_argument("--camera-height", type=float, default=620)

    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="supply_chain_network_stress.gif")
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
    severity = float(choose(args.severity, scenario.severity))
    demand_spike_scale = float(choose(args.demand_spike_scale, scenario.demand_spike_scale))

    event_start = clamp(event_start_ratio, 0.0, 0.95) * duration
    event_end = clamp(event_start_ratio + event_duration_ratio, 0.02, 0.98) * duration
    event_end = max(event_end, event_start + 0.2)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0)
        .move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(Text("Supply Chain Network Stress", size=34, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 76)))
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} event=[{event_start:.2f}s,{event_end:.2f}s]",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 106))
    )

    node_shapes: dict[str, Circle] = {}
    with ForceLayout(iterations=220, diameter=700) as network:
        for n, spec in NODE_SPECS.items():
            if spec.role == "supplier":
                fill = Colors.LightYellow
            elif spec.role == "store":
                fill = Colors.MistyRose
            elif spec.role == "plant":
                fill = Colors.LightGreen
            else:
                fill = Colors.LightCyan
            node_shapes[n] = Circle(r=26, fill=fill, stroke=Colors.DarkBlue.transparent(0.72), width=1.3)
        for u, v in EDGE_SPECS:
            network.connect(node_shapes[u], node_shapes[v])
        network.do_layout()

    for s in node_shapes.values():
        s.transform.tx += args.world_width * 0.48
        s.transform.ty += args.world_height * 0.50
    canvas.add(network)

    edge_shapes: dict[tuple[str, str], Arrow] = {}
    for u, v in EDGE_SPECS:
        spec = EDGE_SPECS[(u, v)]
        if spec.kind == "primary":
            stroke = Colors.MediumBlue.transparent(0.34)
        elif spec.kind == "alt":
            stroke = Colors.DarkOrange.transparent(0.32)
        else:
            stroke = Colors.SeaGreen.transparent(0.34)
        a = Arrow(
            p1=node_shapes[u].anchor("center"),
            p2=node_shapes[v].anchor("center"),
            stroke=stroke,
            width=1.2,
            marker_end=None,
        )
        edge_shapes[(u, v)] = a
        canvas.add(a)

    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for n, shape in node_shapes.items():
        c = shape.anchor("center")
        halo = Circle(r=34, fill=Colors.Transparent, stroke=Colors.Crimson.transparent(0.70), width=0.7).move_to(c)
        bar = Rect(w=11, h=44, fill=Colors.SeaGreen.transparent(0.58), stroke=Colors.DarkGray.transparent(0.42), width=0.8).move_to(Point(c.x + 64, c.y))
        node_halos[n] = halo
        node_bars[n] = bar
        canvas.add(halo, bar)
        canvas.add(Text(n, size=9, fill=Colors.Black).move_to(c))

    panel_x = 300
    panel_y = 390
    row_h = 38
    canvas.add(Rect(w=310, h=row_h * len(PHASES) + 36, fill=Colors.White.transparent(0.90), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(panel_x, panel_y)))
    canvas.add(Text("Network Phase", size=14, fill=Colors.Black).move_to(Point(panel_x, panel_y - 110)))
    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=11, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 98, y)))
    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(Point(panel_x - 120, phase_rows["STEADY"]))
    canvas.add(phase_indicator)

    legend = Rect(w=470, h=250, fill=Colors.White.transparent(0.93), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(args.world_width - 300, 300))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 300, 190)))
    lx = args.world_width - 510
    ly = 230
    canvas.add(Text("Halo width ~ backlog stress", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Bar scale ~ inventory deficit", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Edge width ~ shipment flow", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Blue=primary  Orange=alternate  Green=balance", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 24
    canvas.add(Text("service = fulfilled_demand / requested_demand", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    phase = "STEADY"
    phase_entry = 0.0
    transitions = 0

    inventory = {n: NODE_SPECS[n].base_inventory for n in NODE_SPECS}
    backlog = {n: 0.0 for n in NODE_SPECS if NODE_SPECS[n].role == "store"}
    edge_flow = {(u, v): 0.0 for (u, v) in EDGE_SPECS}

    packets: list[Packet] = []
    total_requested = 0.0
    total_fulfilled = 0.0
    peak_backlog = 0.0
    peak_overload = 0.0
    reroute_flow = 0.0
    total_flow = 0.0

    tracks: dict[str, dict[float, float]] = {"phase_ty": {}, "cam_tx": {}, "cam_ty": {}}
    for n in NODE_SPECS:
        tracks[f"halo_w_{n}"] = {}
        tracks[f"bar_sy_{n}"] = {}
    for u, v in EDGE_SPECS:
        tracks[f"edge_w_{u}_{v}"] = {}

    def set_phase(t: float, new_phase: str, reason: str) -> None:
        nonlocal phase, phase_entry, transitions
        if new_phase == phase:
            return
        phase = new_phase
        phase_entry = t
        transitions += 1

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps
        in_event = event_start <= t <= event_end

        if in_event:
            set_phase(t, "SHOCK", "event_window")

        # Supplier replenishment with policy scaling.
        for n, spec in NODE_SPECS.items():
            if spec.role == "supplier":
                inventory[n] += 5.8 * policy.replenish_gain * dt
                inventory[n] = clamp(inventory[n], 0.0, 380.0)

        # Demand realization at store nodes.
        demand_spike = demand_spike_scale if in_event else 1.0
        for n, spec in NODE_SPECS.items():
            if spec.role != "store":
                continue
            req = spec.demand_rate * dt
            if n == scenario.demand_spike_node:
                req *= demand_spike
            have = inventory[n]
            used = min(have, req)
            inventory[n] -= used
            backlog[n] += req - used
            total_requested += req
            total_fulfilled += used

        # Relief from residual stock.
        for n in backlog:
            relief = min(backlog[n], inventory[n] * policy.backlog_relief * dt)
            backlog[n] -= relief
            inventory[n] -= relief

        # Route capacities under disruption.
        cap_now = {}
        for e, spec in EDGE_SPECS.items():
            cap = spec.capacity
            if in_event and e in scenario.disrupted_edges:
                cap *= max(0.05, 1.0 - severity)
            cap_now[e] = cap * dt

        # Desired deficits for pull-based dispatch.
        deficit = {n: max(0.0, NODE_SPECS[n].target_inventory - inventory[n]) for n in NODE_SPECS}

        # Reset edge flows before dispatch decisions.
        for e in edge_flow:
            edge_flow[e] = 0.0

        # Dispatch helper that updates inventories immediately (scaffold simplification).
        def send(u: str, v: str, qty: float, gain: float = 1.0) -> float:
            e = (u, v)
            if e not in EDGE_SPECS:
                return 0.0
            cap = cap_now[e] * gain
            moved = min(max(0.0, qty), cap, inventory[u])
            if moved <= 1e-9:
                return 0.0
            inventory[u] -= moved
            # Simple in-flight inefficiency proxy keeps stress visible in short runs.
            inventory[v] += moved * 0.90
            edge_flow[e] += moved / max(1e-9, dt)
            return moved

        # Primary replenishment layers.
        send("SUP_W", "PLANT", deficit["PLANT"])
        send("SUP_E", "PLANT", deficit["PLANT"])
        send("PLANT", "DC_N", deficit["DC_N"])
        send("PLANT", "DC_S", deficit["DC_S"])

        send("DC_N", "STORE_A", backlog["STORE_A"] + deficit["STORE_A"])
        send("DC_N", "STORE_B", backlog["STORE_B"] + deficit["STORE_B"])
        send("DC_S", "STORE_B", backlog["STORE_B"] + deficit["STORE_B"])
        send("DC_S", "STORE_C", backlog["STORE_C"] + deficit["STORE_C"])

        # Reroute pass uses alt/balance edges; policy controls aggressiveness.
        reroute_gain = policy.reroute_gain * (1.0 + (0.45 if in_event else 0.0))
        moved_alt = 0.0
        moved_alt += send("SUP_W", "DC_N", deficit["DC_N"], gain=reroute_gain)
        moved_alt += send("SUP_E", "DC_S", deficit["DC_S"], gain=reroute_gain)
        moved_alt += send("DC_N", "STORE_C", backlog["STORE_C"] + deficit["STORE_C"], gain=reroute_gain)
        moved_alt += send("DC_S", "STORE_A", backlog["STORE_A"] + deficit["STORE_A"], gain=reroute_gain)

        # Balance edge smooths uneven DC inventories.
        if inventory["DC_N"] > inventory["DC_S"] + 4.0:
            send("DC_N", "DC_S", (inventory["DC_N"] - inventory["DC_S"]) * 0.22, gain=policy.reroute_gain)
        elif inventory["DC_S"] > inventory["DC_N"] + 4.0:
            send("DC_S", "DC_N", (inventory["DC_S"] - inventory["DC_N"]) * 0.22, gain=policy.reroute_gain)

        # Post-event phase movement.
        total_backlog = sum(backlog.values())
        if phase == "SHOCK" and not in_event:
            set_phase(t, "REROUTE", "event_end")
        if phase == "REROUTE" and total_backlog < 2.0:
            set_phase(t, "RECOVER", "backlog_reduced")
        if phase == "RECOVER" and total_backlog < 0.6:
            set_phase(t, "STABLE", "stabilized")

        # Metrics and visual tracks.
        peak_backlog = max(peak_backlog, total_backlog)
        for e, spec in EDGE_SPECS.items():
            util = edge_flow[e] / max(1e-9, spec.capacity)
            peak_overload = max(peak_overload, util)
            if spec.kind in {"alt", "balance"}:
                reroute_flow += edge_flow[e] * dt
            total_flow += edge_flow[e] * dt

            tracks[f"edge_w_{e[0]}_{e[1]}"][k] = 1.0 + 2.5 * clamp(util, 0.0, 1.8) / 1.8

        for n, spec in NODE_SPECS.items():
            if spec.role == "store":
                stress = clamp(backlog[n] / 8.0, 0.0, 1.0)
            else:
                deficit_ratio = max(0.0, spec.target_inventory - inventory[n]) / max(1e-6, spec.target_inventory)
                stress = clamp(deficit_ratio, 0.0, 1.0)
            tracks[f"halo_w_{n}"][k] = 0.8 + 4.0 * stress

            inventory_deficit = max(0.0, spec.target_inventory - inventory[n]) / max(1.0, spec.target_inventory)
            tracks[f"bar_sy_{n}"][k] = 0.30 + 1.25 * clamp(inventory_deficit, 0.0, 1.0)

        tracks["phase_ty"][k] = phase_rows[phase]

        hotspot = max(NODE_SPECS.keys(), key=lambda n: backlog.get(n, 0.0) + max(0.0, NODE_SPECS[n].target_inventory - inventory[n]))
        center = Point(args.world_width / 2, args.world_height / 2)
        hot = node_shapes[hotspot].anchor("center")
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.72 + center * 0.28
        else:
            if phase in {"STEADY", "SHOCK"}:
                cam = node_shapes["PLANT"].anchor("center") * 0.58 + node_shapes["DC_N"].anchor("center") * 0.42
            elif phase == "REROUTE":
                cam = hot * 0.64 + node_shapes["DC_S"].anchor("center") * 0.36
            else:
                cam = hot * 0.42 + center * 0.58
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

        if len(packets) < packets_max:
            for e, spec in EDGE_SPECS.items():
                rate = packet_rate * clamp(edge_flow[e] / max(0.1, spec.capacity), 0.0, 1.6)
                if rng.random() < rate * dt and len(packets) < packets_max:
                    st = clamp(t + rng.uniform(-0.05, 0.05), 0.0, duration)
                    et = clamp(st + rng.uniform(0.45, 0.95), st + 0.02, duration)
                    if spec.kind == "primary":
                        color = Colors.MediumBlue
                    elif spec.kind == "alt":
                        color = Colors.DarkOrange
                    else:
                        color = Colors.SeaGreen
                    packets.append(Packet(node_shapes[e[0]].anchor("center"), node_shapes[e[1]].anchor("center"), st, et, color))

    packet_anims = []
    for i, rec in enumerate(packets):
        pkt = Circle(r=4.0 + (i % 2), fill=rec.color.transparent(0.86), stroke=Colors.Black.transparent(0.18), width=0.6).move_to(rec.src)
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration))

    anims = [
        KeyframeAnimation(phase_indicator, ty=tracks["phase_ty"]),
        KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"]),
    ]
    for n in NODE_SPECS:
        anims.append(KeyframeAnimation(node_halos[n], width=tracks[f"halo_w_{n}"]))
        anims.append(KeyframeAnimation(node_bars[n], sy=tracks[f"bar_sy_{n}"]))
    for e in EDGE_SPECS:
        anims.append(KeyframeAnimation(edge_shapes[e], width=tracks[f"edge_w_{e[0]}_{e[1]}"]))

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

    service_level = 1.0 if total_requested <= 1e-9 else clamp(total_fulfilled / total_requested, 0.0, 1.0)
    reroute_util = 0.0 if total_flow <= 1e-9 else reroute_flow / total_flow

    print(f"✅ Saved: {out}")
    print(f"   scenario={args.scenario} policy={args.policy} phase={phase} packets={len(packets)} transitions={transitions}")
    print(
        f"   service_level={service_level:.3f} peak_backlog={peak_backlog:.3f} "
        f"peak_route_overload={peak_overload:.3f} reroute_utilization={reroute_util:.3f}"
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
                "severity": severity,
                "disrupted_edges": [[u, v] for (u, v) in scenario.disrupted_edges],
                "demand_spike_node": scenario.demand_spike_node,
                "demand_spike_scale": demand_spike_scale,
            },
            "metrics": {
                "service_level": service_level,
                "peak_backlog": peak_backlog,
                "peak_route_overload": peak_overload,
                "reroute_utilization": reroute_util,
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
