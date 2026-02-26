#!/usr/bin/env python3
"""Incident response playbook animation stress test for Tesserax.

Scenario model:
- service graph with request/control links
- attack injection + compromise propagation
- phase-driven response playbook (detect -> triage -> contain -> eradicate -> recover)
- policy profiles controlling detection and remediation aggressiveness

Outputs animation plus optional JSON metrics report.
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


PHASES = ["DETECT", "TRIAGE", "CONTAIN", "ERADICATE", "RECOVER", "POSTMORTEM"]


@dataclass
class ServiceNode:
    name: str
    pos: Point
    criticality: float
    base_load: float


@dataclass
class Link:
    name: str
    src: str
    dst: str
    transit: float
    kind: str
    propagation_weight: float


@dataclass
class Packet:
    src: Point
    dst: Point
    start: float
    end: float
    color: Colors


@dataclass
class ScenarioPreset:
    attack_target: str
    attack_start_ratio: float
    attack_duration_ratio: float
    attack_intensity: float
    propagation_rate: float
    traffic_spike: float
    alert_noise: float


@dataclass
class PolicyProfile:
    detect_threshold: float
    triage_delay: float
    containment_rate: float
    recovery_rate: float
    investigation_focus: float


SCENARIOS = {
    "credential_stuffing": ScenarioPreset(
        attack_target="AUTH",
        attack_start_ratio=0.22,
        attack_duration_ratio=0.34,
        attack_intensity=1.80,
        propagation_rate=0.78,
        traffic_spike=0.34,
        alert_noise=0.22,
    ),
    "lateral_movement": ScenarioPreset(
        attack_target="WORKER",
        attack_start_ratio=0.25,
        attack_duration_ratio=0.44,
        attack_intensity=1.60,
        propagation_rate=1.04,
        traffic_spike=0.20,
        alert_noise=0.26,
    ),
    "data_exfiltration": ScenarioPreset(
        attack_target="DB",
        attack_start_ratio=0.30,
        attack_duration_ratio=0.30,
        attack_intensity=1.45,
        propagation_rate=0.64,
        traffic_spike=0.16,
        alert_noise=0.18,
    ),
    "ransomware_drill": ScenarioPreset(
        attack_target="QUEUE",
        attack_start_ratio=0.18,
        attack_duration_ratio=0.50,
        attack_intensity=1.95,
        propagation_rate=1.18,
        traffic_spike=0.42,
        alert_noise=0.30,
    ),
}


POLICIES = {
    "manual": PolicyProfile(
        detect_threshold=0.27,
        triage_delay=1.35,
        containment_rate=0.58,
        recovery_rate=0.24,
        investigation_focus=0.70,
    ),
    "assisted": PolicyProfile(
        detect_threshold=0.21,
        triage_delay=0.85,
        containment_rate=0.86,
        recovery_rate=0.36,
        investigation_focus=0.88,
    ),
    "autonomous": PolicyProfile(
        detect_threshold=0.16,
        triage_delay=0.45,
        containment_rate=1.16,
        recovery_rate=0.52,
        investigation_focus=1.08,
    ),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated incident response playbook stress test.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--dt", type=float, default=0.03, help="Simulation step size.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument("--seed", type=int, default=151, help="Random seed.")

    p.add_argument(
        "--scenario",
        choices=sorted(SCENARIOS.keys()),
        default="credential_stuffing",
        help="Scenario preset (overrides can be applied via explicit flags).",
    )
    p.add_argument(
        "--policy",
        choices=sorted(POLICIES.keys()),
        default="assisted",
        help="Response policy profile.",
    )

    p.add_argument("--attack-target", type=str, default=None, help="Override attack target node name.")
    p.add_argument("--attack-start-ratio", type=float, default=None, help="Attack start ratio of duration.")
    p.add_argument("--attack-duration-ratio", type=float, default=None, help="Attack duration ratio of duration.")
    p.add_argument("--attack-intensity", type=float, default=None, help="Attack injection intensity.")
    p.add_argument("--propagation-rate", type=float, default=None, help="Compromise propagation rate.")
    p.add_argument("--traffic-spike", type=float, default=None, help="Traffic amplification during incident.")
    p.add_argument("--alert-noise", type=float, default=None, help="Noise floor for alerts.")

    p.add_argument("--packet-rate", type=float, default=2.6, help="Average packet spawns per second per link.")
    p.add_argument("--packets-max", type=int, default=560, help="Maximum rendered packets.")

    p.add_argument(
        "--camera-mode",
        choices=["fixed", "track", "hybrid"],
        default="hybrid",
        help="Camera framing strategy.",
    )
    p.add_argument("--world-width", type=int, default=2500, help="World width.")
    p.add_argument("--world-height", type=int, default=1600, help="World height.")
    p.add_argument("--camera-width", type=float, default=980, help="Camera width.")
    p.add_argument("--camera-height", type=float, default=620, help="Camera height.")

    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument("--report-json", type=str, default="", help="Optional metrics report JSON path.")
    p.add_argument(
        "--output",
        type=str,
        default="incident_response_playbook.gif",
        help="Output animation path (extension adjusted to --format).",
    )
    return p.parse_args()


def build_graph(width: int, height: int) -> tuple[dict[str, ServiceNode], list[Link]]:
    cx = width / 2
    nodes = {
        "EDGE": ServiceNode("EDGE", Point(cx - 900, 280), 0.45, 0.48),
        "API": ServiceNode("API", Point(cx - 520, 300), 0.72, 0.58),
        "AUTH": ServiceNode("AUTH", Point(cx - 110, 280), 0.92, 0.52),
        "CACHE": ServiceNode("CACHE", Point(cx - 120, 520), 0.58, 0.47),
        "QUEUE": ServiceNode("QUEUE", Point(cx - 520, 640), 0.82, 0.56),
        "WORKER": ServiceNode("WORKER", Point(cx - 60, 820), 0.86, 0.60),
        "DB": ServiceNode("DB", Point(cx + 360, 640), 1.00, 0.62),
        "PAGER": ServiceNode("PAGER", Point(cx - 760, 1040), 0.38, 0.34),
        "SOC": ServiceNode("SOC", Point(cx - 200, 1140), 0.76, 0.42),
    }

    links = [
        Link("EDGE_API", "EDGE", "API", 0.65, "traffic", 0.10),
        Link("API_AUTH", "API", "AUTH", 0.72, "traffic", 0.28),
        Link("API_QUEUE", "API", "QUEUE", 0.76, "traffic", 0.24),
        Link("API_CACHE", "API", "CACHE", 0.66, "traffic", 0.16),
        Link("AUTH_DB", "AUTH", "DB", 0.82, "traffic", 0.42),
        Link("CACHE_DB", "CACHE", "DB", 0.90, "traffic", 0.18),
        Link("QUEUE_WORKER", "QUEUE", "WORKER", 0.74, "traffic", 0.35),
        Link("WORKER_DB", "WORKER", "DB", 0.78, "traffic", 0.48),
        Link("PAGER_SOC", "PAGER", "SOC", 0.90, "control", 0.0),
        Link("SOC_API", "SOC", "API", 0.96, "control", 0.0),
        Link("SOC_AUTH", "SOC", "AUTH", 0.98, "control", 0.0),
        Link("SOC_DB", "SOC", "DB", 1.04, "control", 0.0),
        Link("SOC_WORKER", "SOC", "WORKER", 0.96, "control", 0.0),
        Link("AUTH_API", "AUTH", "API", 0.72, "attack", 0.32),
        Link("WORKER_QUEUE", "WORKER", "QUEUE", 0.78, "attack", 0.30),
        Link("DB_WORKER", "DB", "WORKER", 0.88, "attack", 0.26),
    ]
    return nodes, links


def phase_index(phase: str) -> int:
    return PHASES.index(phase)


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
    packets_max = max(20, args.packets_max)
    packet_rate = max(0.2, args.packet_rate)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]

    attack_target = str(choose(args.attack_target, scenario.attack_target))
    attack_start_ratio = float(choose(args.attack_start_ratio, scenario.attack_start_ratio))
    attack_duration_ratio = float(choose(args.attack_duration_ratio, scenario.attack_duration_ratio))
    attack_intensity = float(choose(args.attack_intensity, scenario.attack_intensity))
    propagation_rate = float(choose(args.propagation_rate, scenario.propagation_rate))
    traffic_spike = float(choose(args.traffic_spike, scenario.traffic_spike))
    alert_noise = float(choose(args.alert_noise, scenario.alert_noise))

    detect_threshold = policy.detect_threshold
    triage_delay = policy.triage_delay
    containment_rate = policy.containment_rate
    recovery_rate = policy.recovery_rate
    investigation_focus = policy.investigation_focus

    attack_start = clamp(attack_start_ratio, 0.0, 0.95) * duration
    attack_end = clamp(attack_start_ratio + attack_duration_ratio, 0.02, 0.98) * duration
    attack_end = max(attack_end, attack_start + 0.2)

    nodes, links = build_graph(args.world_width, args.world_height)
    if attack_target not in nodes:
        attack_target = scenario.attack_target

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
        Text("Incident Response Playbook", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.world_width / 2, 76)
        )
    )
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} attack_target={attack_target}",
            size=14,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 108))
    )

    for y, label in [(270, "Edge/API"), (640, "Services/Data"), (1080, "Response Ops")]:
        canvas.add(
            Arrow(
                p1=Point(140, y),
                p2=Point(args.world_width - 140, y),
                stroke=Colors.LightGray.transparent(0.24),
                width=1.0,
                marker_end=None,
            )
        )
        canvas.add(Text(label, size=12, fill=Colors.DarkGray, anchor="start").move_to(Point(120, y - 24)))

    link_shapes: dict[str, Arrow] = {}
    for link in links:
        p1 = nodes[link.src].pos
        p2 = nodes[link.dst].pos
        curve = clamp((p2.y - p1.y) / 1300.0, -0.24, 0.24)
        if link.kind == "traffic":
            stroke = Colors.MediumBlue.transparent(0.30)
        elif link.kind == "control":
            stroke = Colors.SeaGreen.transparent(0.34)
        else:
            stroke = Colors.Crimson.transparent(0.26)
        arr = Arrow(
            p1=p1,
            p2=p2,
            curvature=curve,
            stroke=stroke,
            width=1.3,
            marker_end=None,
        )
        link_shapes[link.name] = arr
        canvas.add(arr)

    node_shapes: dict[str, Circle] = {}
    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for name, node in nodes.items():
        base = Colors.LightCyan
        if name in {"AUTH", "DB", "WORKER", "QUEUE"}:
            base = Colors.LightYellow
        if name in {"SOC", "PAGER"}:
            base = Colors.MistyRose

        c = Circle(
            r=30 if name not in {"SOC", "PAGER"} else 26,
            fill=base,
            stroke=Colors.DarkBlue.transparent(0.70),
            width=1.3,
        ).move_to(node.pos)
        h = Circle(
            r=38 if name not in {"SOC", "PAGER"} else 34,
            fill=Colors.Transparent,
            stroke=Colors.Crimson.transparent(0.70),
            width=0.7,
        ).move_to(node.pos)
        b = Rect(
            w=14,
            h=52,
            fill=Colors.SeaGreen.transparent(0.56),
            stroke=Colors.DarkGray.transparent(0.40),
            width=0.8,
        ).move_to(Point(node.pos.x + 48, node.pos.y))

        node_shapes[name] = c
        node_halos[name] = h
        node_bars[name] = b
        canvas.add(h, c, b)
        canvas.add(Text(name, size=10, fill=Colors.Black).move_to(node.pos))

    # Phase panel.
    panel_x = 340
    panel_y = 430
    row_h = 44
    panel = Rect(
        w=360,
        h=row_h * len(PHASES) + 42,
        fill=Colors.White.transparent(0.90),
        stroke=Colors.DarkGray.transparent(0.65),
        width=1.1,
    ).move_to(Point(panel_x, panel_y))
    canvas.add(panel)
    canvas.add(Text("Playbook Phase", size=15, fill=Colors.Black).move_to(Point(panel_x, panel_y - 150)))

    phase_rows: dict[str, float] = {}
    top = panel_y - (row_h * (len(PHASES) - 1)) / 2
    for i, ph in enumerate(PHASES):
        y = top + i * row_h
        phase_rows[ph] = y
        canvas.add(Text(ph, size=12, fill=Colors.Black, anchor="start").move_to(Point(panel_x - 120, y)))

    phase_indicator = Circle(r=8, fill=Colors.SeaGreen, stroke=Colors.DarkGreen, width=1.0).move_to(
        Point(panel_x - 144, phase_rows["DETECT"])
    )
    canvas.add(phase_indicator)

    # Live text badges.
    impact_badge = Text("impact=0.00", size=12, fill=Colors.DarkRed).move_to(Point(args.world_width - 260, 120))
    err_badge = Text("error=0.00", size=12, fill=Colors.DarkBlue).move_to(Point(args.world_width - 260, 148))
    canvas.add(impact_badge, err_badge)

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    # Sim state.
    compromised = {name: 0.0 for name in nodes}
    loads = {name: node.base_load for name, node in nodes.items()}
    packets: list[Packet] = []

    phase = "DETECT"
    phase_entry = 0.0
    detect_time: float | None = None
    contain_time: float | None = None
    recover_time: float | None = None
    transition_log: list[tuple[float, str, str, str]] = []

    total_error = 0.0
    peak_impact = 0.0
    breach_time = 0.0

    steps = max(2, int(duration / dt))
    tracks: dict[str, dict[float, float]] = {
        "phase_ty": {},
        "cam_tx": {},
        "cam_ty": {},
        "impact": {},
        "error": {},
    }
    for name in nodes:
        tracks[f"halo_w_{name}"] = {}
        tracks[f"bar_sy_{name}"] = {}
    for link in links:
        tracks[f"edge_w_{link.name}"] = {}

    def set_phase(t: float, new_phase: str, why: str) -> None:
        nonlocal phase, phase_entry, detect_time, contain_time, recover_time
        if new_phase == phase:
            return
        transition_log.append((t, phase, new_phase, why))
        phase = new_phase
        phase_entry = t
        if new_phase == "TRIAGE" and detect_time is None:
            detect_time = t
        if new_phase == "CONTAIN" and contain_time is None:
            contain_time = t
        if new_phase == "RECOVER" and recover_time is None:
            recover_time = t

    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps

        # Attack injection.
        if attack_start <= t <= attack_end:
            wave = 0.82 + 0.18 * math.sin(6.0 * t)
            compromised[attack_target] += attack_intensity * wave * dt

        # Propagation.
        delta = {name: 0.0 for name in nodes}
        for link in links:
            if link.propagation_weight <= 0:
                continue
            src_c = compromised[link.src]
            dst_c = compromised[link.dst]
            prop = propagation_rate * link.propagation_weight * src_c * (1.0 - dst_c) * dt
            delta[link.dst] += prop

        for name in nodes:
            compromised[name] += delta[name]

        # Playbook actions by phase.
        global_impact = sum(compromised[n] * nodes[n].criticality for n in nodes) / sum(
            node.criticality for node in nodes.values()
        )
        if phase == "DETECT" and global_impact >= detect_threshold:
            set_phase(t, "TRIAGE", "impact_threshold")
        elif phase == "TRIAGE" and (t - phase_entry) >= triage_delay:
            set_phase(t, "CONTAIN", "triage_complete")
        elif phase == "CONTAIN" and global_impact <= 0.28:
            set_phase(t, "ERADICATE", "impact_reduced")
        elif phase == "ERADICATE" and global_impact <= 0.16:
            set_phase(t, "RECOVER", "eradication_complete")
        elif phase == "RECOVER" and global_impact <= 0.08 and t >= attack_end + 0.14 * duration:
            set_phase(t, "POSTMORTEM", "stabilized")

        if phase in {"CONTAIN", "ERADICATE", "RECOVER", "POSTMORTEM"}:
            for name in nodes:
                focus = investigation_focus if name in {attack_target, "AUTH", "DB", "WORKER", "API"} else 0.82
                compromised[name] -= containment_rate * focus * dt
        if phase in {"ERADICATE", "RECOVER", "POSTMORTEM"}:
            for name in nodes:
                compromised[name] -= recovery_rate * (0.55 + 0.45 * nodes[name].criticality) * dt

        # Natural drift and clamping.
        for name in nodes:
            compromised[name] += 0.018 * alert_noise * dt
            compromised[name] = clamp(compromised[name], 0.0, 1.0)

        # Load model and derived metrics.
        spike = traffic_spike if attack_start <= t <= attack_end else 0.0
        err = 0.0
        for name, node in nodes.items():
            load = node.base_load * (1.0 + spike) + 0.72 * compromised[name]
            loads[name] = clamp(load, 0.0, 1.8)
            err += clamp(0.62 * compromised[name] + 0.10 * max(0.0, loads[name] - 1.0), 0.0, 1.0) * node.criticality
        err /= sum(node.criticality for node in nodes.values())
        total_error += err * dt

        global_impact = sum(compromised[n] * nodes[n].criticality for n in nodes) / sum(
            node.criticality for node in nodes.values()
        )
        peak_impact = max(peak_impact, global_impact)
        if global_impact > 0.32:
            breach_time += dt

        # packet spawning
        if len(packets) < packets_max:
            for link in links:
                src_load = loads[link.src]
                rate = packet_rate * (1.0 + 0.7 * src_load)
                if link.kind == "control" and phase_index(phase) >= phase_index("TRIAGE"):
                    rate *= 1.45
                if rng.random() < rate * dt and len(packets) < packets_max:
                    jitter = rng.uniform(-0.05, 0.05)
                    st = clamp(t + jitter, 0.0, duration)
                    et = clamp(st + link.transit + rng.uniform(-0.08, 0.08), st + 0.02, duration)
                    if link.kind == "traffic":
                        color = Colors.MediumBlue
                    elif link.kind == "control":
                        color = Colors.SeaGreen
                    else:
                        color = Colors.Crimson
                    packets.append(Packet(nodes[link.src].pos, nodes[link.dst].pos, st, et, color))

        # Record tracks.
        tracks["phase_ty"][k] = phase_rows[phase]
        tracks["impact"][k] = global_impact
        tracks["error"][k] = err
        for name in nodes:
            tracks[f"halo_w_{name}"][k] = 0.8 + 4.2 * compromised[name]
            tracks[f"bar_sy_{name}"][k] = 0.30 + 1.30 * clamp(loads[name], 0.0, 1.3)

        for link in links:
            src_c = compromised[link.src]
            base = 1.2
            if link.kind == "control":
                pulse = 0.8 if phase_index(phase) >= phase_index("TRIAGE") else 0.0
                tracks[f"edge_w_{link.name}"][k] = base + pulse
            else:
                tracks[f"edge_w_{link.name}"][k] = base + 2.4 * src_c

        # Camera cues.
        hotspot = max(nodes.keys(), key=lambda n: compromised[n] * nodes[n].criticality)
        hot = nodes[hotspot].pos
        center = Point(args.world_width / 2, args.world_height / 2)
        if args.camera_mode == "fixed":
            cam = center
        elif args.camera_mode == "track":
            cam = hot * 0.74 + center * 0.26
        else:  # hybrid
            if phase in {"DETECT", "TRIAGE"}:
                cam = nodes[attack_target].pos * 0.70 + nodes["API"].pos * 0.30
            elif phase in {"CONTAIN", "ERADICATE"}:
                cam = hot * 0.62 + nodes["SOC"].pos * 0.38
            else:
                cam = hot * 0.40 + center * 0.60
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

    # Build packet visuals.
    packet_anims = []
    for i, rec in enumerate(packets):
        pkt = Circle(
            r=4.0 + (i % 2),
            fill=rec.color.transparent(0.85),
            stroke=Colors.Black.transparent(0.18),
            width=0.7,
        ).move_to(rec.src)
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration))

    # Animations.
    anims = [
        KeyframeAnimation(phase_indicator, ty=tracks["phase_ty"]),
        KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"]),
        impact_badge.animate.keyframes(size={0.0: 12.0, 0.5: 15.0, 1.0: 12.0}).repeating(2.4),
        err_badge.animate.keyframes(size={0.0: 12.0, 0.5: 14.5, 1.0: 12.0}).repeating(2.1),
    ]

    for name in nodes:
        anims.append(KeyframeAnimation(node_halos[name], width=tracks[f"halo_w_{name}"]))
        anims.append(KeyframeAnimation(node_bars[name], sy=tracks[f"bar_sy_{name}"]))
    for link in links:
        anims.append(KeyframeAnimation(link_shapes[link.name], width=tracks[f"edge_w_{link.name}"]))

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

    mean_error = total_error / max(1e-9, duration)
    service_level = clamp(1.0 - mean_error, 0.0, 1.0)
    mttd = max(0.0, (detect_time if detect_time is not None else duration) - attack_start)
    mttr = (
        max(0.0, recover_time - attack_start)
        if recover_time is not None
        else max(0.0, duration - attack_start)
    )

    print(f"✅ Saved: {out}")
    print(
        f"   scenario={args.scenario} policy={args.policy} phase={phase} "
        f"attack=[{attack_start:.2f}s,{attack_end:.2f}s] packets={len(packets)}"
    )
    print(
        f"   service_level={service_level:.3f} peak_impact={peak_impact:.3f} "
        f"breach_time={breach_time:.2f}s mttd={mttd:.2f}s mttr={mttr:.2f}s"
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
                "target": attack_target,
                "start_s": attack_start,
                "end_s": attack_end,
                "intensity": attack_intensity,
                "propagation_rate": propagation_rate,
                "traffic_spike": traffic_spike,
            },
            "metrics": {
                "service_level": service_level,
                "mean_error": mean_error,
                "peak_impact": peak_impact,
                "breach_time": breach_time,
                "mttd": mttd,
                "mttr": mttr,
                "final_phase": phase,
                "transitions": len(transition_log),
                "visible_packets": len(packets),
            },
        }
        path = Path(args.report_json)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={path}")


if __name__ == "__main__":
    main()
