#!/usr/bin/env python3
"""Topology-morph animation stress test for Tesserax."""

import argparse
import random
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Polyline, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, Parallel, Scene, Sequence
from tesserax.color import hls


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def palette(n: int) -> list:
    if n <= 1:
        return [Colors.DodgerBlue]
    return [hls(i / n, 0.52, 0.70) for i in range(n)]


def ring_points(n: int, cx: float, cy: float, r: float) -> list[Point]:
    pts = []
    for i in range(n):
        ang = (2 * 3.141592653589793 * i / n) - 3.141592653589793 / 2
        pts.append(Point(cx + r * __import__("math").cos(ang), cy + r * __import__("math").sin(ang)))
    return pts


def star_points(n: int, cx: float, cy: float, r_outer: float, r_inner: float) -> list[Point]:
    pts = []
    for i in range(n):
        ang = (2 * 3.141592653589793 * i / n) - 3.141592653589793 / 2
        radius = r_outer if i % 2 == 0 else r_inner
        pts.append(Point(cx + radius * __import__("math").cos(ang), cy + radius * __import__("math").sin(ang)))
    return pts


def tree_points(n: int, cx: float, top: float, width: float, level_gap: float) -> list[Point]:
    pts = []
    max_levels = 1
    while (2**max_levels - 1) < n:
        max_levels += 1
    for i in range(n):
        level = 0
        while (2 ** (level + 1) - 1) <= i:
            level += 1
        idx_in_level = i - (2**level - 1)
        slots = 2**level
        x = cx if slots == 1 else (cx - width / 2) + idx_in_level * (width / (slots - 1))
        y = top + level * level_gap
        pts.append(Point(x, y))
    return pts


def cluster_points(n: int, cx: float, cy: float, spread: float, rng: random.Random) -> list[Point]:
    centers = [
        Point(cx - spread, cy - spread * 0.7),
        Point(cx + spread, cy - spread * 0.7),
        Point(cx - spread, cy + spread * 0.8),
        Point(cx + spread, cy + spread * 0.8),
    ]
    pts = []
    for i in range(n):
        c = centers[i % len(centers)]
        dx = rng.uniform(-spread * 0.32, spread * 0.32)
        dy = rng.uniform(-spread * 0.25, spread * 0.25)
        pts.append(Point(c.x + dx, c.y + dy))
    return pts


def undirected(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated topology morph stress test.")
    p.add_argument("--nodes", type=int, default=18, help="Node count for all topologies.")
    p.add_argument("--duration", type=float, default=12.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument(
        "--edge-pulse-cycles",
        type=float,
        default=2.5,
        help="Repeated pulse cycles for active edges.",
    )
    p.add_argument("--lag", type=float, default=0.03, help="Delayed node-pulse lag.")
    p.add_argument("--seed", type=int, default=31, help="Random seed.")
    p.add_argument("--width", type=int, default=1808, help="Canvas width.")
    p.add_argument("--height", type=int, default=1040, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="topology_morph.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    n = max(6, args.nodes)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)

    canvas = Canvas(width=args.width, height=args.height)
    canvas.add(
        Rect(
            w=args.width,
            h=args.height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(args.width / 2, args.height / 2))
    )

    title = Text("Topology Morph Animation Stress Test", size=24, fill=Colors.DarkBlue)
    title.move_to(Point(args.width / 2, 42))
    canvas.add(title)
    canvas.add(
        Text(
            f"nodes={n} topologies=star->ring->tree->cluster",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 70))
    )

    cx, cy = args.width / 2, args.height / 2 + 20
    star = star_points(n, cx, cy, r_outer=min(args.width, args.height) * 0.33, r_inner=min(args.width, args.height) * 0.16)
    ring = ring_points(n, cx, cy, r=min(args.width, args.height) * 0.30)
    tree = tree_points(n, cx, top=180, width=args.width * 0.72, level_gap=120)
    cluster = cluster_points(n, cx, cy, spread=min(args.width, args.height) * 0.22, rng=rng)

    # Edges for each topology.
    edges_star = {undirected(0, i) for i in range(1, n)}
    edges_ring = {undirected(i, (i + 1) % n) for i in range(n)}
    edges_tree = set()
    for i in range(n):
        l, r = 2 * i + 1, 2 * i + 2
        if l < n:
            edges_tree.add(undirected(i, l))
        if r < n:
            edges_tree.add(undirected(i, r))
    edges_cluster = set()
    groups = {g: [i for i in range(n) if i % 4 == g] for g in range(4)}
    for grp in groups.values():
        for i in range(len(grp) - 1):
            edges_cluster.add(undirected(grp[i], grp[i + 1]))
        if len(grp) > 2:
            edges_cluster.add(undirected(grp[0], grp[-1]))

    all_edges = sorted(edges_star | edges_ring | edges_tree | edges_cluster)

    # Nodes.
    node_shapes = []
    colors = palette(n)
    for i in range(n):
        c = Circle(r=12, fill=colors[i], stroke=Colors.DarkBlue.transparent(0.65), width=1.0)
        c.move_to(star[i])
        canvas.add(c)
        canvas.add(Text(str(i), size=8, fill=Colors.Black, font="monospace").move_to(star[i]))
        node_shapes.append(c)

    # Dynamic edges from callables.
    edge_shapes = {}
    for a, b in all_edges:
        edge = Arrow(
            p1=lambda ia=a: node_shapes[ia].anchor("center"),
            p2=lambda ib=b: node_shapes[ib].anchor("center"),
            stroke=Colors.Gray.transparent(0.40),
            width=0.25,
            marker_end=None,
        )
        canvas.add(edge)
        edge_shapes[(a, b)] = edge

    # Morph overlay polyline (same point count in each topology) to exercise Morphed.
    hull = Polyline(points=star, closed=True, smoothness=0.42, stroke=Colors.DarkBlue.transparent(0.33), width=2.2)
    canvas.add(hull)

    # Node keyframes across topologies.
    phase = [0.0, 0.34, 0.67, 1.0]
    node_anims = []
    for i, node in enumerate(node_shapes):
        node_anims.append(
            node.animate.keyframes(
                tx={
                    phase[0]: star[i].x,
                    phase[1]: ring[i].x,
                    phase[2]: tree[i].x,
                    phase[3]: cluster[i].x,
                },
                ty={
                    phase[0]: star[i].y,
                    phase[1]: ring[i].y,
                    phase[2]: tree[i].y,
                    phase[3]: cluster[i].y,
                },
            )
        )

    # Edge widths indicate active topology.
    edge_anims = []
    for e in all_edges:
        edge = edge_shapes[e]
        w_star = 1.9 if e in edges_star else 0.20
        w_ring = 1.9 if e in edges_ring else 0.20
        w_tree = 1.9 if e in edges_tree else 0.20
        w_cluster = 1.9 if e in edges_cluster else 0.20
        edge_anims.append(
            edge.animate.keyframes(
                width={
                    phase[0]: w_star,
                    phase[1]: w_ring,
                    phase[2]: w_tree,
                    phase[3]: w_cluster,
                }
            ).repeating(args.edge_pulse_cycles)
        )

    # Node pulse wave.
    pulse = []
    for node in node_shapes:
        pulse.append(
            node.animate.keyframes(
                sx={0.0: 1.0, 0.5: 1.16, 1.0: 1.0},
                sy={0.0: 1.0, 0.5: 1.16, 1.0: 1.0},
                width={0.0: 1.0, 0.5: 2.2, 1.0: 1.0},
            ).repeating(2.5)
        )

    # Sequence of explicit polyline morph steps.
    hull_morph = Sequence(
        hull.animate.morph(Polyline(points=ring, closed=True)).weight(0.34),
        hull.animate.morph(Polyline(points=tree, closed=True)).weight(0.33),
        hull.animate.morph(Polyline(points=cluster, closed=True)).weight(0.33),
    )

    combined = Parallel(
        *node_anims,
        *edge_anims,
        hull_morph,
        Delayed(*pulse, lag_ratio=args.lag),
    )

    scene = Scene(canvas, fps=fps, background="white")
    scene.play(combined, duration=duration)

    result = render_scene(
        scene,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            timing=TimingSpec(fps=fps, duration=duration, seed=args.seed),
        ),
    )
    out = result.output_path
    print(f"✅ Saved: {out}")
    print(f"   nodes={n}, edges={len(all_edges)}, frames={int(duration * fps)}")


if __name__ == "__main__":
    main()
