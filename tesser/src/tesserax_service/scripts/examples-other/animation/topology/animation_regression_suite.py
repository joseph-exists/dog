#!/usr/bin/env python3
"""Deterministic animation regression harness for Tesserax.

Pattern alignment:
- scenario/policy/report-json CLI contract
- fixture selection for repeatable stress cases
- frame-level hashing for regression signatures
- optional signature-reference comparison for pass/fail gating
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import (
    Camera,
    Canvas,
    Circle,
    Colors,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    Text,
    TimingSpec,
    render_scene,
)
from tesserax.animation import KeyframeAnimation, Parallel, Scene


@dataclass
class ScenarioPreset:
    event_start_ratio: float
    event_duration_ratio: float
    intensity: float
    burstiness: float


@dataclass
class PolicyPreset:
    damping: float
    jitter: float
    recovery: float


@dataclass
class Packet:
    points: list[Point]
    start: float
    end: float
    color: Colors


SCENARIOS = {
    "baseline": ScenarioPreset(0.24, 0.30, 1.0, 1.0),
    "stress": ScenarioPreset(0.20, 0.42, 1.38, 1.26),
    "recovery": ScenarioPreset(0.30, 0.26, 1.12, 0.92),
}

POLICIES = {
    "strict": PolicyPreset(damping=0.32, jitter=0.08, recovery=0.36),
    "balanced": PolicyPreset(damping=0.22, jitter=0.14, recovery=0.24),
    "throughput": PolicyPreset(damping=0.12, jitter=0.20, recovery=0.16),
}

FIXTURES = ["pipeline", "ring", "mesh"]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deterministic animation regression suite.")
    p.add_argument("--duration", type=float, default=6.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=16)
    p.add_argument("--seed", type=int, default=311)

    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="baseline")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="balanced")
    p.add_argument("--fixture", choices=FIXTURES, default="pipeline")

    p.add_argument("--packet-rate", type=float, default=2.0)
    p.add_argument("--packets-max", type=int, default=520)
    p.add_argument("--packet-speed", type=float, default=320.0)

    p.add_argument("--world-width", type=int, default=1800)
    p.add_argument("--world-height", type=int, default=1100)
    p.add_argument("--camera-width", type=float, default=1000)
    p.add_argument("--camera-height", type=float, default=620)

    p.add_argument("--hash-sample-step", type=int, default=1)
    p.add_argument("--signature-ref", type=str, default="", help="Optional reference signature/report JSON.")
    p.add_argument("--signature-out", type=str, default="", help="Optional path to write computed signature JSON.")

    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--save-media", action="store_true", help="Persist media output. Default is report-only.")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="animation_regression_suite.gif")
    return p.parse_args()


def polyline_length(points: list[Point]) -> float:
    return sum(points[i - 1].distance(points[i]) for i in range(1, len(points)))


def packet_keyframes(packet: Circle, rec: Packet, duration: float) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    distances = [0.0]
    for i in range(1, len(rec.points)):
        distances.append(distances[-1] + rec.points[i - 1].distance(rec.points[i]))
    total = max(1e-6, distances[-1])

    def stamp(at: float, p: Point) -> None:
        k = clamp(at / duration, 0.0, 1.0)
        tx[k] = p.x
        ty[k] = p.y

    stamp(0.0, rec.points[0])
    stamp(rec.start, rec.points[0])
    for i, p in enumerate(rec.points[1:-1], start=1):
        frac = distances[i] / total
        stamp(rec.start + frac * (rec.end - rec.start), p)
    stamp(rec.end, rec.points[-1])
    stamp(duration, rec.points[-1])

    show = clamp((rec.start + 0.01 * duration) / duration, 0.0, 1.0)
    hide = clamp((rec.end + 0.01 * duration) / duration, 0.0, 1.0)
    sx[0.0] = sy[0.0] = 0.0
    sx[show] = sy[show] = 1.0
    sx[hide] = sy[hide] = 0.0
    sx[1.0] = sy[1.0] = 0.0
    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def fixture_spec(fixture: str, w: float, h: float) -> tuple[dict[str, Point], list[tuple[str, str]]]:
    if fixture == "pipeline":
        nodes = {
            "A": Point(0.10 * w, 0.42 * h),
            "B": Point(0.22 * w, 0.30 * h),
            "C": Point(0.22 * w, 0.56 * h),
            "D": Point(0.36 * w, 0.42 * h),
            "E": Point(0.52 * w, 0.30 * h),
            "F": Point(0.52 * w, 0.56 * h),
            "G": Point(0.68 * w, 0.42 * h),
            "H": Point(0.82 * w, 0.42 * h),
        }
        edges = [("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("D", "E"), ("D", "F"), ("E", "G"), ("F", "G"), ("G", "H")]
        return nodes, edges

    if fixture == "ring":
        nodes: dict[str, Point] = {}
        cx, cy = 0.50 * w, 0.44 * h
        radius = min(w, h) * 0.30
        n = 14
        for i in range(n):
            t = 2.0 * math.pi * i / n
            nodes[f"N{i:02d}"] = Point(cx + radius * math.cos(t), cy + radius * math.sin(t))
        edges = []
        for i in range(n):
            edges.append((f"N{i:02d}", f"N{(i+1)%n:02d}"))
        for i in range(0, n, 2):
            edges.append((f"N{i:02d}", f"N{(i+5)%n:02d}"))
        return nodes, edges

    # mesh
    nodes = {}
    cols, rows = 4, 4
    x0, y0 = 0.18 * w, 0.22 * h
    sx, sy = 0.18 * w, 0.16 * h
    for r in range(rows):
        for c in range(cols):
            nodes[f"M{r}{c}"] = Point(x0 + c * sx, y0 + r * sy)
    edges: list[tuple[str, str]] = []
    for r in range(rows):
        for c in range(cols):
            if c + 1 < cols:
                edges.append((f"M{r}{c}", f"M{r}{c+1}"))
            if r + 1 < rows:
                edges.append((f"M{r}{c}", f"M{r+1}{c}"))
    return nodes, edges


def compute_signature(frames: list[bytes], sample_step: int) -> dict:
    step = max(1, sample_step)
    sampled = [frames[i] for i in range(0, len(frames), step)]
    frame_hashes = [hashlib.sha256(b).hexdigest() for b in sampled]
    combined = hashlib.sha256("".join(frame_hashes).encode("utf-8")).hexdigest()

    if frame_hashes:
        first = frame_hashes[0]
        mid = frame_hashes[len(frame_hashes) // 2]
        last = frame_hashes[-1]
    else:
        first = mid = last = ""

    return {
        "frame_count": len(frames),
        "sample_step": step,
        "sampled_count": len(frame_hashes),
        "combined_hash": combined,
        "first_hash": first,
        "mid_hash": mid,
        "last_hash": last,
        "total_frame_bytes": int(sum(len(f) for f in frames)),
    }


def read_signature(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if "signature" in data and isinstance(data["signature"], dict):
            return data["signature"]
        metrics = data.get("metrics")
        if isinstance(metrics, dict):
            sig = metrics.get("signature")
            if isinstance(sig, dict):
                return sig
    return data


def compare_signatures(actual: dict, expected: dict) -> tuple[str, list[str]]:
    checks = ["frame_count", "sample_step", "combined_hash", "first_hash", "mid_hash", "last_hash"]
    mismatches: list[str] = []
    for key in checks:
        if actual.get(key) != expected.get(key):
            mismatches.append(key)
    return ("pass" if not mismatches else "fail"), mismatches


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    duration = max(1.0, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    packet_rate = max(0.1, args.packet_rate)
    packets_max = max(20, args.packets_max)
    packet_speed = max(60.0, args.packet_speed)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]

    event_start = clamp(scenario.event_start_ratio, 0.0, 0.95) * duration
    event_end = clamp(scenario.event_start_ratio + scenario.event_duration_ratio, 0.02, 0.98) * duration
    event_end = max(event_end, event_start + 0.2)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0).move_to(
            Point(args.world_width / 2, args.world_height / 2)
        )
    )
    canvas.add(Text("Animation Regression Suite", size=30, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 70)))
    canvas.add(
        Text(
            f"fixture={args.fixture} scenario={args.scenario} policy={args.policy} seed={args.seed}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 96))
    )

    nodes, edges = fixture_spec(args.fixture, args.world_width, args.world_height)

    edge_shapes: dict[tuple[str, str], Polyline] = {}
    node_shapes: dict[str, Circle] = {}

    for u, v in edges:
        p1 = nodes[u]
        p2 = nodes[v]
        mid = (p1 + p2) / 2
        # Slight deterministic curvature proxy by edge key hash.
        wobble = ((sum(ord(ch) for ch in u + v) % 7) - 3) * 0.008
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        d = math.hypot(dx, dy)
        if d > 1e-6:
            nx, ny = -dy / d, dx / d
            mid = Point(mid.x + wobble * d * nx, mid.y + wobble * d * ny)
        edge = Polyline(
            points=[p1, mid, p2],
            smoothness=0.72,
            closed=False,
            fill=Colors.Transparent,
            stroke=Colors.SlateGray.transparent(0.44),
            width=1.2,
            marker_end="arrow",
        )
        edge_shapes[(u, v)] = edge
        canvas.add(edge)

    for name, p in nodes.items():
        c = Circle(r=13, fill=Colors.AliceBlue, stroke=Colors.DarkBlue.transparent(0.70), width=1.0).move_to(p)
        node_shapes[name] = c
        canvas.add(c)
        canvas.add(Text(name, size=8, fill=Colors.Black).move_to(p))

    legend = Rect(w=510, h=130, fill=Colors.White.transparent(0.93), stroke=Colors.DarkGray.transparent(0.58), width=1.0)
    legend.move_to(Point(args.world_width - 300, args.world_height - 90))
    canvas.add(legend)
    lx = args.world_width - 532
    ly = args.world_height - 134
    canvas.add(Text("Legend and Notation", size=13, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 20
    canvas.add(Text("edge width ~ load_e(t)", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 16
    canvas.add(Text("node scale ~ local pressure", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 16
    canvas.add(Text("frame hashes are sampled and combined into signature", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    outgoing: dict[str, list[tuple[str, str]]] = {n: [] for n in nodes}
    incoming: dict[str, list[tuple[str, str]]] = {n: [] for n in nodes}
    for e in edges:
        outgoing[e[0]].append(e)
        incoming[e[1]].append(e)

    edge_tracks: dict[tuple[str, str], dict[float, float]] = {e: {} for e in edges}
    node_scale_tracks: dict[str, dict[float, float]] = {n: {} for n in nodes}

    base_load = {e: 0.22 + 0.04 * (i % 4) for i, e in enumerate(edges)}
    stressed = set(edges[i] for i in range(min(4, len(edges))))
    packets: list[Packet] = []

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps
        in_event = event_start <= t <= event_end

        load_by_edge: dict[tuple[str, str], float] = {}
        for idx, e in enumerate(edges):
            load = base_load[e]
            load += 0.16 * (0.5 + 0.5 * math.sin(0.9 * t + 0.37 * idx))
            if in_event and e in stressed:
                load += 0.34 * scenario.intensity * scenario.burstiness
            load += policy.jitter * 0.14 * math.sin(1.3 * t + 0.11 * (idx % 9))
            if t > event_end:
                load -= policy.recovery * 0.20
            load -= policy.damping * 0.08
            load = clamp(load, 0.05, 1.8)
            load_by_edge[e] = load
            edge_tracks[e][k] = 0.8 + 2.6 * load / 1.8

            if len(packets) < packets_max and rng.random() < packet_rate * load * dt * 0.22:
                pts = edge_shapes[e].points
                length = polyline_length(pts)
                st = clamp(t + rng.uniform(-0.03, 0.05), 0.0, duration)
                flight = clamp(length / packet_speed, 0.14, 1.1)
                et = clamp(st + flight, st + 0.02, duration)
                if in_event and e in stressed:
                    color = Colors.DarkOrange
                elif load >= 1.0:
                    color = Colors.Crimson
                else:
                    color = Colors.MediumBlue
                packets.append(Packet(points=pts, start=st, end=et, color=color))

        for n in nodes:
            local = 0.0
            deg = len(outgoing[n]) + len(incoming[n])
            if deg:
                local += sum(load_by_edge[e] for e in outgoing[n])
                local += sum(load_by_edge[e] for e in incoming[n])
                local /= deg
            node_scale_tracks[n][k] = 0.88 + 0.34 * clamp(local / 1.5, 0.0, 1.0)

    packet_anims = []
    for i, rec in enumerate(packets):
        pkt = Circle(r=3.4 + (i % 2) * 0.4, fill=rec.color.transparent(0.88), stroke=Colors.Black.transparent(0.15), width=0.45)
        pkt.move_to(rec.points[0])
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration))

    anims = []
    for e in edges:
        anims.append(KeyframeAnimation(edge_shapes[e], width=edge_tracks[e]))
    for n in nodes:
        anims.append(KeyframeAnimation(node_shapes[n], sx=node_scale_tracks[n], sy=node_scale_tracks[n]))

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(Parallel(*(anims + packet_anims)), duration=duration)

    signature = compute_signature(scene._frames, args.hash_sample_step)

    status = "pass"
    mismatches: list[str] = []
    if args.signature_ref:
        ref_path = Path(args.signature_ref)
        if ref_path.exists():
            expected = read_signature(ref_path)
            status, mismatches = compare_signatures(signature, expected)
        else:
            status = "fail"
            mismatches = ["missing_reference"]

    if args.save_media:
        result = render_scene(
            scene,
            RenderConfig(
                output_path=args.output,
                format=args.format,
                timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
            ),
        )
        out = result.output_path
        print(f"✅ Saved media: {out}")
    else:
        out = Path(args.output)
        print("✅ Media save skipped (--save-media not set)")

    if args.signature_out:
        spath = Path(args.signature_out)
        spath.parent.mkdir(parents=True, exist_ok=True)
        spath.write_text(json.dumps(signature, indent=2), encoding="utf-8")
        print(f"   signature_out={spath}")

    report = {
        "scenario": args.scenario,
        "policy": args.policy,
        "fixture": args.fixture,
        "seed": args.seed,
        "duration": duration,
        "dt": dt,
        "fps": fps,
        "event": {
            "start_s": event_start,
            "end_s": event_end,
            "intensity": scenario.intensity,
            "burstiness": scenario.burstiness,
        },
        "metrics": {
            "status": status,
            "mismatch_count": len(mismatches),
            "mismatches": mismatches,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "visible_packets": len(packets),
            "signature": signature,
        },
    }

    print(
        f"   fixture={args.fixture} status={status} packets={len(packets)} "
        f"hash={signature['combined_hash'][:12]} mismatches={len(mismatches)}"
    )

    if args.report_json:
        rpath = Path(args.report_json)
        rpath.parent.mkdir(parents=True, exist_ok=True)
        rpath.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={rpath}")


if __name__ == "__main__":
    main()
