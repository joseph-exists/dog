#!/usr/bin/env python3
"""CI/CD dependency risk animation scaffold for Tesserax.

Pattern alignment:
- scenario/policy/report-json CLI contract
- inline comments around model transitions and risk propagation
- notation and legend rendered inside the scene
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


PHASES = ["NORMAL", "DETECT", "MITIGATE", "RELEASE", "RECOVER", "STABLE"]


@dataclass
class StageSpec:
    layer: int
    role: str
    criticality: float
    base_load: float


@dataclass
class ScenarioPreset:
    event_start_ratio: float
    event_duration_ratio: float
    stress_stages: tuple[str, ...]
    risk_intensity: float
    replay_factor: float
    approval_drag: float


@dataclass
class PolicyPreset:
    detect_threshold: float
    triage_delay: float
    mitigation_gain: float
    recovery_gain: float
    gate_gain: float


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


STAGES = {
    "SRC": StageSpec(0, "source", 0.55, 0.45),
    "BUILD": StageSpec(1, "build", 0.75, 0.58),
    "UNIT": StageSpec(2, "test", 0.82, 0.50),
    "INT": StageSpec(3, "test", 0.88, 0.52),
    "SEC": StageSpec(3, "scan", 0.95, 0.54),
    "PKG": StageSpec(4, "package", 0.74, 0.48),
    "STAGE": StageSpec(5, "deploy", 0.84, 0.52),
    "E2E": StageSpec(6, "test", 0.90, 0.56),
    "PROD": StageSpec(7, "deploy", 1.00, 0.50),
    "OBS": StageSpec(7, "ops", 0.62, 0.36),
}

EDGES = [
    ("SRC", "BUILD"),
    ("BUILD", "UNIT"),
    ("BUILD", "INT"),
    ("BUILD", "SEC"),
    ("UNIT", "PKG"),
    ("INT", "PKG"),
    ("SEC", "PKG"),
    ("PKG", "STAGE"),
    ("STAGE", "E2E"),
    ("E2E", "PROD"),
    ("PROD", "OBS"),
]

SCENARIOS = {
    "flaky_tests": ScenarioPreset(0.22, 0.36, ("UNIT", "INT", "E2E"), 1.72, 1.45, 0.20),
    "vuln_spike": ScenarioPreset(0.26, 0.30, ("SEC", "PKG"), 1.85, 1.25, 0.32),
    "infra_drift": ScenarioPreset(0.24, 0.40, ("STAGE", "E2E", "PROD"), 1.68, 1.28, 0.26),
    "hotfix_rush": ScenarioPreset(0.18, 0.44, ("BUILD", "UNIT", "PROD"), 1.60, 1.62, 0.36),
}

POLICIES = {
    "strict": PolicyPreset(0.24, 0.70, 1.02, 0.54, 1.08),
    "balanced": PolicyPreset(0.30, 0.95, 0.82, 0.38, 0.86),
    "fast_track": PolicyPreset(0.36, 1.25, 0.62, 0.24, 0.54),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated CI/CD dependency risk scaffold.")
    p.add_argument("--duration", type=float, default=12.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--seed", type=int, default=211)

    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="flaky_tests")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="balanced")

    p.add_argument("--event-start-ratio", type=float, default=None)
    p.add_argument("--event-duration-ratio", type=float, default=None)
    p.add_argument("--risk-intensity", type=float, default=None)
    p.add_argument("--replay-factor", type=float, default=None)
    p.add_argument("--approval-drag", type=float, default=None)

    p.add_argument("--packet-rate", type=float, default=2.5)
    p.add_argument("--packets-max", type=int, default=620)

    p.add_argument("--camera-mode", choices=["fixed", "track", "hybrid"], default="hybrid")
    p.add_argument("--world-width", type=int, default=2600)
    p.add_argument("--world-height", type=int, default=1600)
    p.add_argument("--camera-width", type=float, default=980)
    p.add_argument("--camera-height", type=float, default=620)

    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="cicd_dependency_risk.gif")
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
    risk_intensity = float(choose(args.risk_intensity, scenario.risk_intensity))
    replay_factor = float(choose(args.replay_factor, scenario.replay_factor))
    approval_drag = float(choose(args.approval_drag, scenario.approval_drag))

    event_start = clamp(event_start_ratio, 0.0, 0.95) * duration
    event_end = clamp(event_start_ratio + event_duration_ratio, 0.02, 0.98) * duration
    event_end = max(event_end, event_start + 0.2)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0).move_to(Point(args.world_width / 2, args.world_height / 2)))
    canvas.add(Text("CI/CD Dependency Risk", size=34, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 76)))
    canvas.add(Text(f"scenario={args.scenario} policy={args.policy} event=[{event_start:.2f}s,{event_end:.2f}s]", size=13, fill=Colors.Gray).move_to(Point(args.world_width / 2, 106)))

    node_shapes: dict[str, Rect] = {}
    with HierarchicalLayout(orientation="horizontal", rank_sep=120, node_sep=58) as dag:
        for name, spec in STAGES.items():
            if spec.role == "source":
                fill = Colors.LightYellow
            elif spec.role == "deploy":
                fill = Colors.MistyRose
            elif spec.role == "scan":
                fill = Colors.LightGreen
            else:
                fill = Colors.LightCyan
            node_shapes[name] = Rect(w=124, h=46, fill=fill, stroke=Colors.DarkBlue.transparent(0.72), width=1.3)
            if spec.layer == 0:
                dag.root(node_shapes[name])
        for u, v in EDGES:
            dag.connect(node_shapes[u], node_shapes[v])
        dag.do_layout()

    for s in node_shapes.values():
        s.transform.tx += 360
        s.transform.ty += 360
    canvas.add(dag)

    edge_shapes: dict[tuple[str, str], Arrow] = {}
    for u, v in EDGES:
        p1 = node_shapes[u].anchor("right")
        p2 = node_shapes[v].anchor("left")
        curve = clamp((p2.y - p1.y) / 260.0, -0.18, 0.18)
        a = Arrow(p1=p1, p2=p2, curvature=curve, stroke=Colors.Gray.transparent(0.34), width=1.2, marker_end=None)
        edge_shapes[(u, v)] = a
        canvas.add(a)

    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for n, shape in node_shapes.items():
        c = shape.anchor("center")
        halo = Circle(r=34, fill=Colors.Transparent, stroke=Colors.Crimson.transparent(0.70), width=0.7).move_to(c)
        bar = Rect(w=11, h=44, fill=Colors.SeaGreen.transparent(0.58), stroke=Colors.DarkGray.transparent(0.42), width=0.8).move_to(Point(c.x + 66, c.y))
        node_halos[n] = halo
        node_bars[n] = bar
        canvas.add(halo, bar)
        canvas.add(Text(n, size=9, fill=Colors.Black).move_to(c))

    panel_x = 300
    panel_y = 390
    row_h = 36
    canvas.add(Rect(w=310, h=row_h * len(PHASES) + 36, fill=Colors.White.transparent(0.90), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(panel_x, panel_y)))
    canvas.add(Text("Pipeline Phase", size=14, fill=Colors.Black).move_to(Point(panel_x, panel_y - 108)))
    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=11, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 98, y)))
    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(Point(panel_x - 120, phase_rows["NORMAL"]))
    canvas.add(phase_indicator)

    legend = Rect(w=470, h=250, fill=Colors.White.transparent(0.93), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(args.world_width - 300, 300))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 300, 190)))
    lx = args.world_width - 510
    ly = 230
    canvas.add(Text("Halo width ~ risk_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Bar scale ~ queue_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Edge width ~ artifact flow", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Blue=normal  Orange=degraded  Red=high-risk", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 24
    canvas.add(Text("success = delivered / expected", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    phase = "NORMAL"
    phase_entry = 0.0
    transitions = 0
    detect_time: float | None = None
    recover_time: float | None = None

    load = {n: STAGES[n].base_load for n in STAGES}
    risk = {n: 0.03 for n in STAGES}
    queue = {n: 0.04 for n in STAGES}
    edge_flow = {(u, v): 0.18 for (u, v) in EDGES}

    incoming: dict[str, list[str]] = {n: [] for n in STAGES}
    outgoing: dict[str, list[str]] = {n: [] for n in STAGES}
    for u, v in EDGES:
        incoming[v].append(u)
        outgoing[u].append(v)

    packets: list[Packet] = []
    peak_stage_risk = 0.0
    blocked_stage_count = 0
    total_expected = 0.0
    total_delivered = 0.0

    tracks: dict[str, dict[float, float]] = {"phase_ty": {}, "cam_tx": {}, "cam_ty": {}}
    for n in STAGES:
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
        in_event = event_start <= t <= event_end

        # Inject scenario stress into selected stages.
        if in_event:
            for n in scenario.stress_stages:
                risk[n] += risk_intensity * 0.22 * dt
                queue[n] += replay_factor * 0.20 * dt

        # Propagate dependency pressure from upstream to downstream stages.
        delta = {n: 0.0 for n in STAGES}
        for u, v in EDGES:
            prop = 0.30 * risk[u] * (1.0 - risk[v]) * dt
            delta[v] += prop
        for n in STAGES:
            risk[n] += delta[n]

        impact = sum((risk[n] + 0.5 * queue[n]) * STAGES[n].criticality for n in STAGES) / sum(
            STAGES[n].criticality for n in STAGES
        )

        if phase == "NORMAL" and impact >= policy.detect_threshold:
            set_phase(t, "DETECT", "impact_threshold")
        elif phase == "DETECT" and (t - phase_entry) >= policy.triage_delay:
            set_phase(t, "MITIGATE", "triage_complete")
        elif phase == "MITIGATE" and (not in_event) and impact <= policy.detect_threshold * 0.85:
            set_phase(t, "RELEASE", "risk_reduced")
        elif phase == "RELEASE" and impact <= policy.detect_threshold * 0.62:
            set_phase(t, "RECOVER", "release_stable")
        elif phase == "RECOVER" and impact <= policy.detect_threshold * 0.50:
            set_phase(t, "STABLE", "steady")

        # Policy controls: strict gates cut risk faster but increase queue drag.
        if phase in {"MITIGATE", "RELEASE", "RECOVER", "STABLE"}:
            for n in STAGES:
                risk[n] -= policy.mitigation_gain * 0.25 * dt
                queue[n] -= policy.gate_gain * 0.16 * dt
        if phase in {"RECOVER", "STABLE"}:
            for n in STAGES:
                risk[n] -= policy.recovery_gain * 0.22 * dt
                queue[n] -= policy.recovery_gain * 0.14 * dt

        # Stage load update with bounded dynamics.
        for n, spec in STAGES.items():
            parent = sum(edge_flow[(u, n)] for u in incoming[n]) / max(1, len(incoming[n]))
            gate_drag = approval_drag * (1.0 if phase in {"MITIGATE", "RELEASE"} else 0.0)
            target = spec.base_load + 0.45 * parent + gate_drag * 0.12
            load[n] += clamp(target - load[n], -0.85 * dt, 0.85 * dt)

            cap = 0.88 if spec.role not in {"deploy", "scan"} else 0.78
            backlog = max(0.0, load[n] - cap)
            queue[n] += backlog * dt
            risk[n] += 0.06 * backlog * dt
            risk[n] += 0.016 * math.sin(0.8 * t + 0.23 * (len(n) % 7)) * dt

            queue[n] = clamp(queue[n], 0.0, 2.0)
            risk[n] = clamp(risk[n], 0.0, 1.0)

        # Edge flow proxy from stage readiness.
        for u, v in EDGES:
            flow = load[u] * (1.0 - 0.52 * risk[u])
            edge_flow[(u, v)] = clamp(flow, 0.0, 1.8)

        expected = load["PROD"] + load["OBS"]
        delivered = expected * (1.0 - impact * 0.62)
        total_expected += expected * dt
        total_delivered += max(0.0, delivered) * dt

        blocked = sum(1 for n in STAGES if risk[n] >= 0.50 or queue[n] >= 0.80)
        blocked_stage_count = max(blocked_stage_count, blocked)
        peak_stage_risk = max(peak_stage_risk, max(risk.values()))

        # Packet visuals from flow and local stage risk.
        if len(packets) < packets_max:
            for u, v in EDGES:
                rate = packet_rate * clamp(edge_flow[(u, v)], 0.0, 1.5)
                if rng.random() < rate * dt and len(packets) < packets_max:
                    st = clamp(t + rng.uniform(-0.05, 0.05), 0.0, duration)
                    et = clamp(st + rng.uniform(0.45, 0.90), st + 0.02, duration)
                    local = (risk[u] + risk[v]) / 2.0
                    if local > 0.68:
                        color = Colors.Crimson
                    elif local > 0.34:
                        color = Colors.DarkOrange
                    else:
                        color = Colors.MediumBlue
                    packets.append(Packet(node_shapes[u].anchor("right"), node_shapes[v].anchor("left"), st, et, color))

        tracks["phase_ty"][k] = phase_rows[phase]

        hotspot = max(STAGES.keys(), key=lambda n: (risk[n] + 0.6 * queue[n]) * STAGES[n].criticality)
        for n in STAGES:
            stress = clamp(risk[n] + 0.6 * queue[n], 0.0, 1.0)
            tracks[f"halo_w_{n}"][k] = 0.8 + 4.0 * stress
            tracks[f"bar_sy_{n}"][k] = 0.30 + 1.20 * clamp(queue[n], 0.0, 1.6) / 1.6
        for u, v in EDGES:
            tracks[f"edge_w_{u}_{v}"][k] = 1.0 + 2.4 * clamp(edge_flow[(u, v)], 0.0, 1.6) / 1.6

        center = Point(args.world_width / 2, args.world_height / 2)
        hot = node_shapes[hotspot].anchor("center")
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.72 + center * 0.28
        else:
            if phase in {"NORMAL", "DETECT"}:
                cam = node_shapes["BUILD"].anchor("center") * 0.55 + node_shapes["UNIT"].anchor("center") * 0.45
            elif phase in {"MITIGATE", "RELEASE"}:
                cam = hot * 0.64 + node_shapes["SEC"].anchor("center") * 0.36
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
    for n in STAGES:
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

    success_rate = 1.0 if total_expected <= 1e-9 else clamp(total_delivered / total_expected, 0.0, 1.0)
    mttd = max(0.0, (detect_time if detect_time is not None else duration) - event_start)
    mttr = max(0.0, (recover_time if recover_time is not None else duration) - event_start)

    print(f"✅ Saved: {out}")
    print(f"   scenario={args.scenario} policy={args.policy} phase={phase} packets={len(packets)} transitions={transitions}")
    print(
        f"   success_rate={success_rate:.3f} peak_stage_risk={peak_stage_risk:.3f} "
        f"blocked_stage_count={blocked_stage_count} mttd={mttd:.2f}s mttr={mttr:.2f}s"
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
                "risk_intensity": risk_intensity,
                "replay_factor": replay_factor,
                "approval_drag": approval_drag,
                "stress_stages": list(scenario.stress_stages),
            },
            "metrics": {
                "success_rate": success_rate,
                "peak_stage_risk": peak_stage_risk,
                "blocked_stage_count": blocked_stage_count,
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
