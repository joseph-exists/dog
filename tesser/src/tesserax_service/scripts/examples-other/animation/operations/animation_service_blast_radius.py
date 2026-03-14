#!/usr/bin/env python3
"""Force-directed service blast-radius animation scaffold for Tesserax.

This script is intentionally designed as a scaffold:
- scenario/policy/report-json pattern aligned with recent examples
- inline comments on model assumptions and key transforms
- in-canvas notation/legend panel for visual interpretation
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


PHASES = ["OBSERVE", "DETECT", "CONTAIN", "RECOVER", "POST"]


@dataclass
class NodeSpec:
    role: str
    criticality: float
    base_load: float


@dataclass
class ScenarioPreset:
    attack_start_ratio: float
    attack_duration_ratio: float
    stress_nodes: tuple[str, ...]
    attack_intensity: float
    propagation_rate: float
    traffic_spike: float


@dataclass
class PolicyPreset:
    detect_threshold: float
    triage_delay: float
    containment_gain: float
    recovery_gain: float


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


NODE_SPECS = {
    "EDGE": NodeSpec("gateway", 0.60, 0.48),
    "API": NodeSpec("service", 0.82, 0.58),
    "AUTH": NodeSpec("service", 0.95, 0.52),
    "CACHE": NodeSpec("service", 0.62, 0.46),
    "QUEUE": NodeSpec("service", 0.74, 0.50),
    "WORKER": NodeSpec("service", 0.86, 0.58),
    "DB": NodeSpec("datastore", 1.00, 0.62),
    "SEARCH": NodeSpec("service", 0.64, 0.44),
    "NOTIFY": NodeSpec("service", 0.52, 0.40),
}

EDGES = [
    ("EDGE", "API"),
    ("API", "AUTH"),
    ("API", "CACHE"),
    ("API", "QUEUE"),
    ("AUTH", "DB"),
    ("CACHE", "DB"),
    ("QUEUE", "WORKER"),
    ("WORKER", "DB"),
    ("WORKER", "SEARCH"),
    ("SEARCH", "DB"),
    ("QUEUE", "NOTIFY"),
    ("NOTIFY", "API"),
]

SCENARIOS = {
    "auth_outage": ScenarioPreset(0.22, 0.34, ("AUTH", "API"), 1.65, 0.95, 0.32),
    "queue_saturation": ScenarioPreset(0.24, 0.40, ("QUEUE", "WORKER"), 1.82, 1.10, 0.26),
    "db_lockstorm": ScenarioPreset(0.28, 0.32, ("DB", "AUTH", "WORKER"), 1.72, 0.88, 0.18),
    "cache_poison": ScenarioPreset(0.20, 0.36, ("CACHE", "API"), 1.55, 0.80, 0.24),
}

POLICIES = {
    "reactive": PolicyPreset(0.34, 1.20, 0.62, 0.24),
    "balanced": PolicyPreset(0.28, 0.90, 0.84, 0.36),
    "proactive": PolicyPreset(0.22, 0.55, 1.06, 0.50),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated force-directed service blast-radius scaffold.")
    p.add_argument("--duration", type=float, default=12.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--seed", type=int, default=181)

    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="auth_outage")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="balanced")

    p.add_argument("--attack-start-ratio", type=float, default=None)
    p.add_argument("--attack-duration-ratio", type=float, default=None)
    p.add_argument("--attack-intensity", type=float, default=None)
    p.add_argument("--propagation-rate", type=float, default=None)
    p.add_argument("--traffic-spike", type=float, default=None)

    p.add_argument("--packet-rate", type=float, default=2.5)
    p.add_argument("--packets-max", type=int, default=640)

    p.add_argument("--camera-mode", choices=["fixed", "track", "hybrid"], default="hybrid")
    p.add_argument("--world-width", type=int, default=2600)
    p.add_argument("--world-height", type=int, default=1600)
    p.add_argument("--camera-width", type=float, default=980)
    p.add_argument("--camera-height", type=float, default=620)

    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="service_blast_radius.gif")
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

    attack_start_ratio = float(choose(args.attack_start_ratio, scenario.attack_start_ratio))
    attack_duration_ratio = float(choose(args.attack_duration_ratio, scenario.attack_duration_ratio))
    attack_intensity = float(choose(args.attack_intensity, scenario.attack_intensity))
    propagation_rate = float(choose(args.propagation_rate, scenario.propagation_rate))
    traffic_spike = float(choose(args.traffic_spike, scenario.traffic_spike))

    attack_start = clamp(attack_start_ratio, 0.0, 0.95) * duration
    attack_end = clamp(attack_start_ratio + attack_duration_ratio, 0.02, 0.98) * duration
    attack_end = max(attack_end, attack_start + 0.2)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0)
        .move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(Text("Service Blast Radius", size=34, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 76)))
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} attack=[{attack_start:.2f}s,{attack_end:.2f}s]",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 106))
    )

    # Build a force-directed topology. We compute layout once, then animate state over fixed positions.
    node_shapes: dict[str, Circle] = {}
    with ForceLayout(iterations=220, diameter=620) as network:
        for name, spec in NODE_SPECS.items():
            if spec.role == "gateway":
                fill = Colors.LightYellow
            elif spec.role == "datastore":
                fill = Colors.MistyRose
            else:
                fill = Colors.LightCyan
            node_shapes[name] = Circle(r=26, fill=fill, stroke=Colors.DarkBlue.transparent(0.72), width=1.3)

        for u, v in EDGES:
            network.connect(node_shapes[u], node_shapes[v])
        network.do_layout()

    # Position network in world space.
    for s in node_shapes.values():
        s.transform.tx += args.world_width * 0.47
        s.transform.ty += args.world_height * 0.50
    canvas.add(network)

    # Edge visuals are separate so we can animate width independently from the layout group.
    edge_shapes: dict[tuple[str, str], Arrow] = {}
    for u, v in EDGES:
        edge = Arrow(
            p1=node_shapes[u].anchor("center"),
            p2=node_shapes[v].anchor("center"),
            stroke=Colors.Gray.transparent(0.34),
            width=1.3,
            marker_end=None,
        )
        edge_shapes[(u, v)] = edge
        canvas.add(edge)

    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for n, shape in node_shapes.items():
        center = shape.anchor("center")
        halo = Circle(r=34, fill=Colors.Transparent, stroke=Colors.Crimson.transparent(0.70), width=0.7).move_to(center)
        bar = Rect(w=11, h=44, fill=Colors.SeaGreen.transparent(0.58), stroke=Colors.DarkGray.transparent(0.42), width=0.8).move_to(Point(center.x + 64, center.y))
        node_halos[n] = halo
        node_bars[n] = bar
        canvas.add(halo, bar)
        canvas.add(Text(n, size=9, fill=Colors.Black).move_to(center))

    # Phase panel + legend keep semantics inside the SVG/GIF itself.
    panel_x = 300
    panel_y = 390
    row_h = 38
    canvas.add(Rect(w=310, h=row_h * len(PHASES) + 36, fill=Colors.White.transparent(0.90), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(panel_x, panel_y)))
    canvas.add(Text("Incident Phase", size=14, fill=Colors.Black).move_to(Point(panel_x, panel_y - 110)))

    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=11, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 98, y)))
    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(Point(panel_x - 120, phase_rows["OBSERVE"]))
    canvas.add(phase_indicator)

    legend = Rect(w=470, h=250, fill=Colors.White.transparent(0.93), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(args.world_width - 300, 300))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 300, 190)))
    lx = args.world_width - 510
    ly = 230
    canvas.add(Circle(r=6, fill=Colors.MediumBlue, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Blue packet: normal traffic", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))
    ly += 20
    canvas.add(Circle(r=6, fill=Colors.DarkOrange, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Orange packet: degraded path", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))
    ly += 20
    canvas.add(Circle(r=6, fill=Colors.Crimson, stroke=Colors.Black.transparent(0.2), width=0.6).move_to(Point(lx, ly)))
    canvas.add(Text("Red packet: incident pressure", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))
    ly += 24
    canvas.add(Circle(r=8, fill=Colors.Transparent, stroke=Colors.Crimson, width=2.0).move_to(Point(lx, ly)))
    canvas.add(Text("Halo width ~ risk_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))
    ly += 22
    canvas.add(Rect(w=10, h=24, fill=Colors.SeaGreen, stroke=Colors.DarkGray, width=1.0).move_to(Point(lx, ly)))
    canvas.add(Text("Bar scale ~ queue_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))
    ly += 22
    canvas.add(Arrow(p1=Point(lx - 8, ly), p2=Point(lx + 8, ly), stroke=Colors.Gray, width=2.0, marker_end=None))
    canvas.add(Text("Edge width ~ call volume", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx + 22, ly)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    # Simulation state.
    phase = "OBSERVE"
    phase_entry = 0.0
    transitions = 0
    detect_time: float | None = None
    recover_time: float | None = None

    load = {n: NODE_SPECS[n].base_load for n in NODE_SPECS}
    risk = {n: 0.03 for n in NODE_SPECS}
    queue = {n: 0.04 for n in NODE_SPECS}
    edge_volume = {(u, v): 0.18 for (u, v) in EDGES}

    incoming: dict[str, list[str]] = {n: [] for n in NODE_SPECS}
    outgoing: dict[str, list[str]] = {n: [] for n in NODE_SPECS}
    for u, v in EDGES:
        incoming[v].append(u)
        outgoing[u].append(v)

    packets: list[Packet] = []
    peak_impact = 0.0
    peak_radius = 0
    total_expected = 0.0
    total_processed = 0.0

    tracks: dict[str, dict[float, float]] = {"phase_ty": {}, "cam_tx": {}, "cam_ty": {}}
    for n in NODE_SPECS:
        tracks[f"halo_w_{n}"] = {}
        tracks[f"bar_sy_{n}"] = {}
    for u, v in EDGES:
        tracks[f"edge_w_{u}_{v}"] = {}

    def set_phase(t: float, new_phase: str, reason: str) -> None:
        nonlocal phase, phase_entry, transitions, detect_time, recover_time
        if new_phase == phase:
            return
        phase = new_phase
        phase_entry = t
        transitions += 1
        if new_phase == "DETECT" and detect_time is None:
            detect_time = t
        if new_phase == "RECOVER" and recover_time is None:
            recover_time = t

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        in_incident = attack_start <= t <= attack_end

        # Attack injection on scenario focus nodes.
        if in_incident:
            for n in scenario.stress_nodes:
                risk[n] += attack_intensity * 0.22 * dt
                queue[n] += scenario.traffic_spike * 0.45 * dt

        # Propagate pressure through directed calls.
        delta = {n: 0.0 for n in NODE_SPECS}
        for u, v in EDGES:
            prop = propagation_rate * 0.25 * risk[u] * (1.0 - risk[v]) * dt
            delta[v] += prop
        for n in NODE_SPECS:
            risk[n] += delta[n]

        global_impact = sum(risk[n] * NODE_SPECS[n].criticality for n in NODE_SPECS) / sum(
            NODE_SPECS[n].criticality for n in NODE_SPECS
        )

        if phase == "OBSERVE" and global_impact >= policy.detect_threshold:
            set_phase(t, "DETECT", "impact_threshold")
        elif phase == "DETECT" and (t - phase_entry) >= policy.triage_delay:
            set_phase(t, "CONTAIN", "triage_complete")
        elif phase == "CONTAIN" and (not in_incident) and global_impact <= policy.detect_threshold * 0.82:
            set_phase(t, "RECOVER", "impact_reduced")
        elif phase == "RECOVER" and global_impact <= policy.detect_threshold * 0.55:
            set_phase(t, "POST", "stable")

        # Policy action dampens risk/queue over time.
        if phase in {"CONTAIN", "RECOVER", "POST"}:
            for n in NODE_SPECS:
                risk[n] -= policy.containment_gain * 0.28 * dt
                queue[n] -= policy.containment_gain * 0.20 * dt
        if phase in {"RECOVER", "POST"}:
            for n in NODE_SPECS:
                risk[n] -= policy.recovery_gain * 0.22 * dt
                queue[n] -= policy.recovery_gain * 0.18 * dt

        # Update base load and edge volumes from risk/queue state.
        for n, spec in NODE_SPECS.items():
            parent_pressure = sum(edge_volume[(u, n)] for u in incoming[n]) / max(1, len(incoming[n]))
            load_target = spec.base_load + 0.45 * parent_pressure + (scenario.traffic_spike if in_incident else 0.0) * 0.2
            load[n] += clamp(load_target - load[n], -0.8 * dt, 0.8 * dt)
            backlog = max(0.0, load[n] - (0.9 if spec.role != "datastore" else 0.82))
            queue[n] += backlog * dt
            risk[n] += 0.06 * backlog * dt

            # Small deterministic oscillation to avoid perfectly static segments.
            risk[n] += 0.016 * math.sin(0.8 * t + 0.21 * (len(n) % 7)) * dt

            queue[n] = clamp(queue[n], 0.0, 2.0)
            risk[n] = clamp(risk[n], 0.0, 1.0)

        for u, v in EDGES:
            edge_volume[(u, v)] = clamp(load[u] * (1.0 - 0.5 * risk[u]), 0.0, 1.8)

        expected = load["API"] + load["PUBLISH"] if "PUBLISH" in load else load["API"]
        processed = expected * (1.0 - global_impact * 0.6)
        total_expected += expected * dt
        total_processed += max(0.0, processed) * dt

        blast_radius = sum(1 for n in NODE_SPECS if risk[n] >= 0.40)
        peak_radius = max(peak_radius, blast_radius)
        peak_impact = max(peak_impact, global_impact)

        # Packet creation from edge volume and local risk.
        if len(packets) < packets_max:
            for u, v in EDGES:
                rate = packet_rate * clamp(edge_volume[(u, v)], 0.0, 1.5)
                if rng.random() < rate * dt and len(packets) < packets_max:
                    st = clamp(t + rng.uniform(-0.05, 0.05), 0.0, duration)
                    et = clamp(st + rng.uniform(0.45, 0.90), st + 0.02, duration)
                    local_risk = (risk[u] + risk[v]) / 2.0
                    if local_risk > 0.68:
                        color = Colors.Crimson
                    elif local_risk > 0.34:
                        color = Colors.DarkOrange
                    else:
                        color = Colors.MediumBlue
                    packets.append(Packet(node_shapes[u].anchor("center"), node_shapes[v].anchor("center"), st, et, color))

        tracks["phase_ty"][k] = phase_rows[phase]

        hotspot = max(NODE_SPECS.keys(), key=lambda n: (risk[n] + 0.6 * queue[n]) * NODE_SPECS[n].criticality)
        for n in NODE_SPECS:
            stress = clamp(risk[n] + 0.6 * queue[n], 0.0, 1.0)
            tracks[f"halo_w_{n}"][k] = 0.8 + 4.0 * stress
            tracks[f"bar_sy_{n}"][k] = 0.30 + 1.20 * clamp(queue[n], 0.0, 1.6) / 1.6
        for u, v in EDGES:
            tracks[f"edge_w_{u}_{v}"][k] = 1.0 + 2.4 * clamp(edge_volume[(u, v)], 0.0, 1.6) / 1.6

        center = Point(args.world_width / 2, args.world_height / 2)
        hot = node_shapes[hotspot].anchor("center")
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.72 + center * 0.28
        else:
            if phase in {"OBSERVE", "DETECT"}:
                cam = node_shapes["API"].anchor("center") * 0.62 + node_shapes["AUTH"].anchor("center") * 0.38
            elif phase == "CONTAIN":
                cam = hot * 0.66 + node_shapes["DB"].anchor("center") * 0.34
            else:
                cam = hot * 0.42 + center * 0.58
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

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
    mttd = max(0.0, (detect_time if detect_time is not None else duration) - attack_start)
    mttr = max(0.0, (recover_time if recover_time is not None else duration) - attack_start)

    print(f"✅ Saved: {out}")
    print(
        f"   scenario={args.scenario} policy={args.policy} phase={phase} packets={len(packets)} transitions={transitions}"
    )
    print(
        f"   service_level={service_level:.3f} peak_impact={peak_impact:.3f} blast_radius={peak_radius} "
        f"mttd={mttd:.2f}s mttr={mttr:.2f}s"
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
            "attack": {
                "start_s": attack_start,
                "end_s": attack_end,
                "attack_intensity": attack_intensity,
                "propagation_rate": propagation_rate,
                "traffic_spike": traffic_spike,
                "stressed_nodes": list(scenario.stress_nodes),
            },
            "metrics": {
                "service_level": service_level,
                "peak_impact": peak_impact,
                "blast_radius": peak_radius,
                "mttd": mttd,
                "mttr": mttr,
                "transitions": transitions,
                "visible_packets": len(packets),
                "final_phase": phase,
            },
        }
        report_path = Path(args.report_json)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={report_path}")


if __name__ == "__main__":
    main()
