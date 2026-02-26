#!/usr/bin/env python3
"""Graph routing showcase animation for Tesserax.

This example compares multiple visual routing strategies on one DAG-like graph:
- straight
- curved
- orthogonal (obstacle-aware grid tracing)
- bundled (shared corridor heuristic)

Pattern alignment:
- scenario/policy/report-json CLI contract
- inline comments around route construction and metric calculations
- notation + legend rendered inside the output scene
"""

from __future__ import annotations

import argparse
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
    Group,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    Text,
    render_scene,
)
from tesserax.animation import KeyframeAnimation, Parallel, Scene
from tesserax.path import Grid


@dataclass
class ScenarioPreset:
    pulse_start_ratio: float
    pulse_duration_ratio: float
    stressed_edges: tuple[tuple[str, str], ...]
    intensity: float
    burstiness: float


@dataclass
class PolicyPreset:
    jitter_gain: float
    congestion_drag: float
    recovery_gain: float
    reroute_bias: float


@dataclass
class PacketRecord:
    mode: str
    points: list[Point]
    start_s: float
    end_s: float
    color: Colors


@dataclass
class TopologyPreset:
    node_layout: dict[str, tuple[float, float]]
    edges: list[tuple[str, str]]


BASE_NODE_LAYOUT = {
    "A": (0.10, 0.18),
    "B": (0.10, 0.42),
    "C": (0.26, 0.27),
    "D": (0.26, 0.56),
    "E": (0.42, 0.20),
    "F": (0.42, 0.44),
    "G": (0.42, 0.68),
    "H": (0.60, 0.30),
    "I": (0.60, 0.58),
    "J": (0.78, 0.24),
    "K": (0.78, 0.50),
    "L": (0.92, 0.37),
}

BASE_EDGES = [
    ("A", "C"),
    ("A", "D"),
    ("B", "D"),
    ("C", "E"),
    ("C", "F"),
    ("D", "F"),
    ("D", "G"),
    ("E", "H"),
    ("F", "H"),
    ("F", "I"),
    ("G", "I"),
    ("H", "J"),
    ("H", "K"),
    ("I", "K"),
    ("J", "L"),
    ("K", "L"),
]

SCENARIOS = {
    "balanced": ScenarioPreset(0.24, 0.30, (("F", "H"), ("F", "I"), ("I", "K")), 1.00, 1.00),
    "hotspot_h": ScenarioPreset(0.18, 0.44, (("C", "F"), ("D", "F"), ("F", "H")), 1.34, 1.22),
    "cross_region": ScenarioPreset(0.28, 0.36, (("D", "G"), ("G", "I"), ("I", "K")), 1.26, 1.12),
    "downstream_pressure": ScenarioPreset(0.30, 0.34, (("H", "J"), ("H", "K"), ("K", "L")), 1.42, 1.20),
}

POLICIES = {
    "baseline": PolicyPreset(0.16, 0.28, 0.24, 0.00),
    "stability": PolicyPreset(0.10, 0.38, 0.34, 0.24),
    "throughput": PolicyPreset(0.28, 0.18, 0.18, -0.10),
}

TOPOLOGIES = {
    "default": TopologyPreset(
        node_layout=BASE_NODE_LAYOUT,
        edges=BASE_EDGES,
    ),
    "sparse": TopologyPreset(
        node_layout=BASE_NODE_LAYOUT,
        edges=[
            ("A", "C"),
            ("B", "D"),
            ("C", "E"),
            ("C", "F"),
            ("D", "G"),
            ("E", "H"),
            ("F", "I"),
            ("G", "I"),
            ("H", "J"),
            ("I", "K"),
            ("K", "L"),
        ],
    ),
    "dense": TopologyPreset(
        node_layout=BASE_NODE_LAYOUT,
        edges=BASE_EDGES
        + [
            ("A", "E"),
            ("B", "C"),
            ("C", "H"),
            ("D", "H"),
            ("E", "I"),
            ("F", "J"),
            ("G", "K"),
            ("I", "L"),
        ],
    ),
    "clustered": TopologyPreset(
        node_layout={
            "A": (0.09, 0.26),
            "B": (0.12, 0.52),
            "C": (0.29, 0.18),
            "D": (0.31, 0.60),
            "E": (0.44, 0.25),
            "F": (0.45, 0.45),
            "G": (0.43, 0.72),
            "H": (0.64, 0.32),
            "I": (0.63, 0.63),
            "J": (0.80, 0.22),
            "K": (0.80, 0.53),
            "L": (0.93, 0.38),
        },
        edges=[
            ("A", "C"),
            ("A", "D"),
            ("B", "D"),
            ("C", "E"),
            ("D", "F"),
            ("D", "G"),
            ("E", "H"),
            ("F", "H"),
            ("F", "I"),
            ("G", "I"),
            ("H", "J"),
            ("H", "K"),
            ("I", "K"),
            ("J", "L"),
            ("K", "L"),
            ("E", "I"),
        ],
    ),
}

VALID_MODES = ["straight", "curved", "orthogonal", "bundled"]


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def choose(value: float | str | None, fallback: float | str) -> float | str:
    return fallback if value is None else value


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Graph routing strategy comparison showcase.")
    p.add_argument("--duration", type=float, default=11.0)
    p.add_argument("--dt", type=float, default=0.03)
    p.add_argument("--fps", type=int, default=24)
    p.add_argument("--seed", type=int, default=251)

    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="balanced")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="baseline")
    p.add_argument("--mode", choices=["compare", *VALID_MODES], default="compare")
    p.add_argument("--topology", choices=sorted(TOPOLOGIES.keys()), default="default")

    p.add_argument("--pulse-start-ratio", type=float, default=None)
    p.add_argument("--pulse-duration-ratio", type=float, default=None)
    p.add_argument("--intensity", type=float, default=None)
    p.add_argument("--burstiness", type=float, default=None)

    p.add_argument("--packet-rate", type=float, default=2.1)
    p.add_argument("--packets-max", type=int, default=760)
    p.add_argument("--packet-speed", type=float, default=350.0, help="Pixels per second.")

    p.add_argument("--curvature", type=float, default=0.22)
    p.add_argument("--bundle-x-ratio", type=float, default=0.55)
    p.add_argument("--bundle-lane-step", type=float, default=18.0)
    p.add_argument("--turn-penalty", type=float, default=1.4)

    p.add_argument("--camera-mode", choices=["fixed", "track", "hybrid"], default="fixed")
    p.add_argument("--world-width", type=int, default=2800)
    p.add_argument("--world-height", type=int, default=1800)
    p.add_argument("--camera-width", type=float, default=1260)
    p.add_argument("--camera-height", type=float, default=820)

    p.add_argument("--format", choices=["gif", "mp4"], default="gif")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="graph_routing_showcase.gif")
    return p.parse_args()


def seg_intersection(a1: Point, a2: Point, b1: Point, b2: Point) -> bool:
    def ccw(p: Point, q: Point, r: Point) -> float:
        return (q.x - p.x) * (r.y - p.y) - (q.y - p.y) * (r.x - p.x)

    d1 = ccw(a1, a2, b1)
    d2 = ccw(a1, a2, b2)
    d3 = ccw(b1, b2, a1)
    d4 = ccw(b1, b2, a2)
    return (d1 * d2 < 0.0) and (d3 * d4 < 0.0)


def polyline_length(points: list[Point]) -> float:
    return sum(points[i - 1].distance(points[i]) for i in range(1, len(points)))


def route_points(
    mode: str,
    src: Point,
    dst: Point,
    *,
    panel_x: float,
    panel_y: float,
    panel_w: float,
    panel_h: float,
    edge_idx: int,
    obstacle_grid: Grid,
    curvature: float,
    bundle_x_ratio: float,
    bundle_lane_step: float,
    turn_penalty: float,
    bundle_lane_y: float | None = None,
    bundle_trunk_x: float | None = None,
) -> list[Point]:
    if mode == "straight":
        return [src, dst]

    if mode == "curved":
        # Midpoint is shifted by a perpendicular vector to create an arc-like route.
        m = (src + dst) / 2
        dx = dst.x - src.x
        dy = dst.y - src.y
        d = math.hypot(dx, dy)
        if d <= 1e-6:
            return [src, dst]
        nx, ny = -dy / d, dx / d
        amp = curvature * d * (0.65 + 0.35 * math.sin(0.7 * edge_idx))
        mid = Point(m.x + nx * amp, m.y + ny * amp)
        return [src, mid, dst]

    if mode == "orthogonal":
        # Obstacle-aware route through rasterized node boxes.
        points = obstacle_grid.trace(src, dst, turn_penalty=turn_penalty)
        return points if len(points) >= 2 else [src, dst]

    # Bundled heuristic: destination-aware trunk near target reduces global crossings.
    dx = dst.x - src.x
    lane_y = dst.y if bundle_lane_y is None else bundle_lane_y
    trunk_x = (
        panel_x + panel_w * clamp(bundle_x_ratio, 0.28, 0.72)
        if bundle_trunk_x is None
        else bundle_trunk_x
    )
    pre_x = clamp(src.x + 0.24 * dx, src.x + 12.0, dst.x - 22.0)
    near_dst_x = clamp(dst.x - 14.0, src.x + 16.0, dst.x - 2.0)
    pts = [
        src,
        Point(pre_x, src.y),
        Point(trunk_x, lane_y),
        Point(near_dst_x, lane_y),
        Point(near_dst_x, dst.y),
        dst,
    ]
    compact: list[Point] = [pts[0]]
    for p in pts[1:]:
        if p.distance(compact[-1]) > 1e-4:
            compact.append(p)
    return compact


def build_bundle_guides(
    node_shapes: dict[str, Rect],
    edges: list[tuple[str, str]],
    *,
    panel_y: float,
    panel_h: float,
    lane_step: float,
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float]]:
    incoming: dict[str, list[tuple[str, str]]] = {}
    for edge in edges:
        incoming.setdefault(edge[1], []).append(edge)

    lane_map: dict[tuple[str, str], float] = {}
    trunk_map: dict[tuple[str, str], float] = {}
    y_lo = panel_y + 54.0
    y_hi = panel_y + panel_h - 54.0
    for dst, in_edges in incoming.items():
        ordered = sorted(in_edges, key=lambda e: node_shapes[e[0]].anchor("center").y)
        n = len(ordered)
        dst_c = node_shapes[dst].anchor("center")
        for i, edge in enumerate(ordered):
            src = edge[0]
            src_c = node_shapes[src].anchor("center")
            dst_l = node_shapes[dst].anchor("left")
            offset = (i - (n - 1) / 2.0) * lane_step * 0.68
            lane = clamp(dst_c.y + offset, y_lo, y_hi)
            trunk = clamp(src_c.x + 0.72 * (dst_l.x - src_c.x), src_c.x + 26.0, dst_l.x - 18.0)
            lane_map[edge] = lane
            trunk_map[edge] = trunk
    return lane_map, trunk_map


def packet_keyframes(packet: Circle, rec: PacketRecord, duration: float) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    lengths = [0.0]
    for i in range(1, len(rec.points)):
        lengths.append(lengths[-1] + rec.points[i - 1].distance(rec.points[i]))
    total_len = max(1e-6, lengths[-1])

    def stamp(at: float, p: Point) -> None:
        k = clamp(at / duration, 0.0, 1.0)
        tx[k] = p.x
        ty[k] = p.y

    stamp(0.0, rec.points[0])
    stamp(rec.start_s, rec.points[0])
    for i, p in enumerate(rec.points[1:-1], start=1):
        frac = lengths[i] / total_len
        stamp(rec.start_s + frac * (rec.end_s - rec.start_s), p)
    stamp(rec.end_s, rec.points[-1])
    stamp(duration, rec.points[-1])

    show = clamp((rec.start_s + 0.01 * duration) / duration, 0.0, 1.0)
    hide = clamp((rec.end_s + 0.01 * duration) / duration, 0.0, 1.0)
    sx[0.0] = sy[0.0] = 0.0
    sx[show] = sy[show] = 1.0
    sx[hide] = sy[hide] = 0.0
    sx[1.0] = sy[1.0] = 0.0
    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def build_panel(
    canvas: Canvas,
    *,
    mode: str,
    panel_origin: Point,
    panel_size: tuple[float, float],
    curvature: float,
    bundle_x_ratio: float,
    bundle_lane_step: float,
    turn_penalty: float,
    node_layout: dict[str, tuple[float, float]],
    edges: list[tuple[str, str]],
) -> tuple[
    dict[str, Rect],
    dict[tuple[str, str], Polyline],
    dict[tuple[str, str], list[Point]],
    dict[str, Text],
    Rect,
]:
    panel_x, panel_y = panel_origin.x, panel_origin.y
    panel_w, panel_h = panel_size

    panel_frame = Rect(
        w=panel_w,
        h=panel_h,
        fill=Colors.White.transparent(0.95),
        stroke=Colors.DarkGray.transparent(0.55),
        width=1.0,
    ).move_to(Point(panel_x + panel_w / 2, panel_y + panel_h / 2))
    canvas.add(panel_frame)
    canvas.add(Text(mode.upper(), size=14, fill=Colors.DarkBlue).move_to(Point(panel_x + panel_w / 2, panel_y + 20)))

    node_shapes: dict[str, Rect] = {}
    for name, (nx, ny) in node_layout.items():
        cx = panel_x + nx * panel_w
        cy = panel_y + 42 + ny * (panel_h - 82)
        box = Rect(
            w=62,
            h=30,
            fill=Colors.AliceBlue,
            stroke=Colors.SlateGray.transparent(0.76),
            width=1.0,
        ).move_to(Point(cx, cy))
        node_shapes[name] = box
        canvas.add(box)
        canvas.add(Text(name, size=9, fill=Colors.Black).move_to(Point(cx, cy)))

    # Build proxy obstacles for routing so we avoid re-parenting already-mounted shapes.
    obstacles = []
    for shape in node_shapes.values():
        c = shape.anchor("center")
        obstacles.append(
            Rect(
                w=shape.w + 10,
                h=shape.h + 8,
                fill=Colors.Transparent,
                stroke=Colors.Transparent,
                width=0.0,
            ).move_to(c)
        )
    obstacle_group = Group(obstacles)
    grid = Grid(obstacle_group, size=18.0)

    bundle_lane_map: dict[tuple[str, str], float] = {}
    bundle_trunk_map: dict[tuple[str, str], float] = {}
    if mode == "bundled":
        bundle_lane_map, bundle_trunk_map = build_bundle_guides(
            node_shapes,
            edges,
            panel_y=panel_y,
            panel_h=panel_h,
            lane_step=bundle_lane_step,
        )

    route_map: dict[tuple[str, str], list[Point]] = {}
    edge_shapes: dict[tuple[str, str], Polyline] = {}
    for i, (u, v) in enumerate(edges):
        src = node_shapes[u].anchor("right")
        dst = node_shapes[v].anchor("left")
        pts = route_points(
            mode,
            src,
            dst,
            panel_x=panel_x,
            panel_y=panel_y,
            panel_w=panel_w,
            panel_h=panel_h,
            edge_idx=i,
            obstacle_grid=grid,
            curvature=curvature,
            bundle_x_ratio=bundle_x_ratio,
            bundle_lane_step=bundle_lane_step,
            turn_penalty=turn_penalty,
            bundle_lane_y=bundle_lane_map.get((u, v)),
            bundle_trunk_x=bundle_trunk_map.get((u, v)),
        )
        smoothness = 0.82 if mode in {"curved", "bundled"} else 0.0
        edge = Polyline(
            points=pts,
            smoothness=smoothness,
            closed=False,
            fill=Colors.Transparent,
            stroke=Colors.SlateGray.transparent(0.45),
            width=1.2,
            marker_end="arrow",
        )
        route_map[(u, v)] = pts
        edge_shapes[(u, v)] = edge
        canvas.add(edge)

    # Readability labels are animated indirectly by edge width changes and packet activity.
    metric_labels = {
        "score": Text("score=0.000", size=10, fill=Colors.DarkGreen, anchor="start").move_to(Point(panel_x + 16, panel_y + panel_h - 58)),
        "cross": Text("crossings=0", size=9, fill=Colors.Black, anchor="start").move_to(Point(panel_x + 16, panel_y + panel_h - 40)),
        "bends": Text("avg_bends=0.00", size=9, fill=Colors.Black, anchor="start").move_to(Point(panel_x + 16, panel_y + panel_h - 24)),
    }
    canvas.add(*metric_labels.values())

    return node_shapes, edge_shapes, route_map, metric_labels, panel_frame


def route_metrics(route_map: dict[tuple[str, str], list[Point]]) -> tuple[int, float, float, float]:
    segments: list[tuple[Point, Point]] = []
    for pts in route_map.values():
        for i in range(1, len(pts)):
            segments.append((pts[i - 1], pts[i]))

    crossings = 0
    for i in range(len(segments)):
        a1, a2 = segments[i]
        for j in range(i + 1, len(segments)):
            b1, b2 = segments[j]
            # Skip if endpoints are shared.
            if a1.distance(b1) < 1e-4 or a1.distance(b2) < 1e-4 or a2.distance(b1) < 1e-4 or a2.distance(b2) < 1e-4:
                continue
            if seg_intersection(a1, a2, b1, b2):
                crossings += 1

    bends = [max(0, len(pts) - 2) for pts in route_map.values()]
    avg_bends = sum(bends) / max(1, len(bends))
    ink = sum(polyline_length(pts) for pts in route_map.values())

    # Compact readability proxy; higher is better.
    score = 1.0 / (1.0 + 0.48 * crossings + 0.16 * avg_bends + 0.00058 * ink)
    return crossings, avg_bends, ink, score


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    duration = max(1.0, args.duration)
    dt = max(0.005, args.dt)
    fps = max(1, args.fps)
    packet_rate = max(0.1, args.packet_rate)
    packets_max = max(40, args.packets_max)
    packet_speed = max(80.0, args.packet_speed)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]
    topology = TOPOLOGIES[args.topology]
    edges = topology.edges
    edge_set = set(edges)

    pulse_start_ratio = float(choose(args.pulse_start_ratio, scenario.pulse_start_ratio))
    pulse_duration_ratio = float(choose(args.pulse_duration_ratio, scenario.pulse_duration_ratio))
    intensity = float(choose(args.intensity, scenario.intensity))
    burstiness = float(choose(args.burstiness, scenario.burstiness))

    pulse_start = clamp(pulse_start_ratio, 0.0, 0.95) * duration
    pulse_end = clamp(pulse_start_ratio + pulse_duration_ratio, 0.02, 0.98) * duration
    pulse_end = max(pulse_end, pulse_start + 0.2)

    modes = VALID_MODES if args.mode == "compare" else [args.mode]

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0).move_to(
            Point(args.world_width / 2, args.world_height / 2)
        )
    )
    canvas.add(Text("Graph Routing Showcase", size=34, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 74)))
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} topology={args.topology} pulse=[{pulse_start:.2f}s,{pulse_end:.2f}s]",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 102))
    )

    # Panel packing: compare -> 2x2; single -> centered panel.
    panel_layout: list[tuple[str, Point, tuple[float, float]]] = []
    if len(modes) == 1:
        w = args.world_width * 0.78
        h = args.world_height * 0.73
        panel_layout.append((modes[0], Point((args.world_width - w) / 2, 150), (w, h)))
    else:
        gap_x = 48
        gap_y = 44
        w = (args.world_width - 3 * gap_x) / 2
        h = (args.world_height - 210 - gap_y) / 2
        panel_layout = [
            (modes[0], Point(gap_x, 150), (w, h)),
            (modes[1], Point(2 * gap_x + w, 150), (w, h)),
            (modes[2], Point(gap_x, 150 + h + gap_y), (w, h)),
            (modes[3], Point(2 * gap_x + w, 150 + h + gap_y), (w, h)),
        ]

    panel_nodes: dict[str, dict[str, Rect]] = {}
    panel_edges: dict[str, dict[tuple[str, str], Polyline]] = {}
    panel_routes: dict[str, dict[tuple[str, str], list[Point]]] = {}
    panel_labels: dict[str, dict[str, Text]] = {}

    for mode, origin, size in panel_layout:
        n, e, r, labels, _ = build_panel(
            canvas,
            mode=mode,
            panel_origin=origin,
            panel_size=size,
            curvature=max(0.0, args.curvature),
            bundle_x_ratio=args.bundle_x_ratio,
            bundle_lane_step=max(2.0, args.bundle_lane_step),
            turn_penalty=max(0.0, args.turn_penalty),
            node_layout=topology.node_layout,
            edges=edges,
        )
        panel_nodes[mode] = n
        panel_edges[mode] = e
        panel_routes[mode] = r
        panel_labels[mode] = labels

    legend = Rect(
        w=620,
        h=170,
        fill=Colors.White.transparent(0.94),
        stroke=Colors.DarkGray.transparent(0.58),
        width=1.0,
    ).move_to(Point(args.world_width - 390, args.world_height - 114))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 390, args.world_height - 182)))
    lx = args.world_width - 680
    ly = args.world_height - 150
    canvas.add(Text("Edge width ~ instantaneous load_e(t)", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Packets: blue=normal orange=pulse red=congested", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Score combines crossings, bends, and total route length", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Orthogonal uses obstacle grid routing via tesserax.path.Grid", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text(f"topology={args.topology} nodes={len(topology.node_layout)} edges={len(edges)}", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))

    camera = Camera(width=args.camera_width, height=args.camera_height, active=True)
    camera.move_to(Point(args.world_width / 2, args.world_height / 2))
    canvas.add(camera)

    tracks: dict[str, dict[float, float]] = {"cam_tx": {}, "cam_ty": {}}
    edge_tracks: dict[str, dict[tuple[str, str], dict[float, float]]] = {
        mode: {e: {} for e in edges} for mode in modes
    }

    base_load = {e: 0.24 + 0.03 * (i % 5) for i, e in enumerate(edges)}
    spawned_per_mode = {m: 0 for m in modes}
    packets: list[PacketRecord] = []
    stressed_edges = {e for e in scenario.stressed_edges if e in edge_set}

    # Precompute static readability metrics per mode.
    readability: dict[str, dict[str, float]] = {}
    for mode in modes:
        crossings, avg_bends, ink, score = route_metrics(panel_routes[mode])
        readability[mode] = {
            "crossings": float(crossings),
            "avg_bends": avg_bends,
            "ink": ink,
            "score": score,
        }
        panel_labels[mode]["score"].text = f"score={score:.3f}"
        panel_labels[mode]["cross"].text = f"crossings={crossings}"
        panel_labels[mode]["bends"].text = f"avg_bends={avg_bends:.2f}"

    steps = max(2, int(duration / dt))
    for s in range(steps + 1):
        t = min(duration, s * dt)
        k = s / steps
        in_pulse = pulse_start <= t <= pulse_end

        for mode in modes:
            mode_factor = {
                "straight": 1.00,
                "curved": 0.92,
                "orthogonal": 0.86,
                "bundled": 0.94,
            }[mode]

            # Stress model: scenario pulse + policy damping + mode-specific overhead.
            for idx, edge in enumerate(edges):
                load = base_load[edge]
                load += 0.08 * (1.0 + math.sin(0.9 * t + 0.5 * idx))
                if in_pulse and edge in stressed_edges:
                    load += intensity * scenario.burstiness * 0.36
                load += policy.jitter_gain * 0.12 * math.sin(1.4 * t + 0.31 * (idx % 7))
                load -= policy.recovery_gain * 0.08 * (1.0 if (not in_pulse and t > pulse_start) else 0.0)
                load *= mode_factor
                if mode == "bundled":
                    load += policy.reroute_bias * 0.14
                elif mode == "orthogonal":
                    load -= policy.reroute_bias * 0.06
                load = clamp(load - policy.congestion_drag * 0.04, 0.05, 1.65)

                edge_tracks[mode][edge][k] = 0.8 + 2.6 * load / 1.65

                # Spawn packets from edge load; compare mode uses shared packet budget.
                if len(packets) < packets_max and rng.random() < packet_rate * load * dt * 0.20:
                    pts = panel_routes[mode][edge]
                    length = polyline_length(pts)
                    start_s = clamp(t + rng.uniform(-0.04, 0.05), 0.0, duration)
                    flight = clamp(length / packet_speed, 0.18, 1.28)
                    end_s = clamp(start_s + flight, start_s + 0.02, duration)
                    if in_pulse and edge in stressed_edges:
                        color = Colors.DarkOrange
                    elif load >= 1.0:
                        color = Colors.Crimson
                    else:
                        color = Colors.MediumBlue
                    packets.append(PacketRecord(mode=mode, points=pts, start_s=start_s, end_s=end_s, color=color))
                    spawned_per_mode[mode] += 1

        # Camera modes: fixed baseline, track hottest panel, or hybrid blend.
        center = Point(args.world_width / 2, args.world_height / 2)
        if args.camera_mode == "fixed" or len(modes) == 1:
            cam = center
        else:
            hot_mode = max(modes, key=lambda m: readability[m]["score"] * 0.4 + spawned_per_mode[m] * 0.0006)
            hot_node = panel_nodes[hot_mode]["F"].anchor("center")
            if args.camera_mode == "track":
                cam = hot_node * 0.82 + center * 0.18
            else:
                cam = hot_node * (0.52 + 0.25 * math.sin(0.7 * t)) + center * (0.48 - 0.25 * math.sin(0.7 * t))
        tracks["cam_tx"][k] = cam.x
        tracks["cam_ty"][k] = cam.y

    packet_anims = []
    for i, rec in enumerate(packets):
        pkt = Circle(
            r=3.6 + (i % 2) * 0.5,
            fill=rec.color.transparent(0.88),
            stroke=Colors.Black.transparent(0.18),
            width=0.5,
        ).move_to(rec.points[0])
        canvas.add(pkt)
        packet_anims.append(packet_keyframes(pkt, rec, duration))

    anims = [KeyframeAnimation(camera, tx=tracks["cam_tx"], ty=tracks["cam_ty"])]
    for mode in modes:
        for edge in edges:
            anims.append(KeyframeAnimation(panel_edges[mode][edge], width=edge_tracks[mode][edge]))

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(Parallel(*(anims + packet_anims)), duration=duration)

    result = render_scene(scene, RenderConfig(output_path=args.output, format=args.format))

    print(f"✅ Saved: {result.output_path}")
    for mode in modes:
        m = readability[mode]
        print(
            f"   mode={mode} score={m['score']:.3f} crossings={int(m['crossings'])} "
            f"avg_bends={m['avg_bends']:.2f} packets={spawned_per_mode[mode]}"
        )

    if args.report_json:
        report = {
            "scenario": args.scenario,
            "policy": args.policy,
            "topology": args.topology,
            "mode": args.mode,
            "seed": args.seed,
            "duration": duration,
            "dt": dt,
            "fps": fps,
            "camera_mode": args.camera_mode,
            "event": {
                "pulse_start_s": pulse_start,
                "pulse_end_s": pulse_end,
                "intensity": intensity,
                "burstiness": burstiness,
                "stressed_edges": [f"{u}->{v}" for (u, v) in stressed_edges],
            },
            "metrics": {
                "total_visible_packets": len(packets),
                "node_count": len(topology.node_layout),
                "edge_count": len(edges),
                "modes": {
                    mode: {
                        "score": readability[mode]["score"],
                        "crossings": int(readability[mode]["crossings"]),
                        "avg_bends": readability[mode]["avg_bends"],
                        "ink": readability[mode]["ink"],
                        "packets_spawned": spawned_per_mode[mode],
                    }
                    for mode in modes
                },
            },
        }

        if args.mode == "compare":
            best_mode = max(modes, key=lambda m: readability[m]["score"])
            report["metrics"]["best_mode"] = best_mode
            report["metrics"]["best_score"] = readability[best_mode]["score"]
        else:
            sm = modes[0]
            report["metrics"]["score"] = readability[sm]["score"]
            report["metrics"]["crossings"] = int(readability[sm]["crossings"])
            report["metrics"]["avg_bends"] = readability[sm]["avg_bends"]
            report["metrics"]["ink"] = readability[sm]["ink"]
            report["metrics"]["packets_spawned"] = spawned_per_mode[sm]

        path = Path(args.report_json)
        path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={path}")


if __name__ == "__main__":
    main()
