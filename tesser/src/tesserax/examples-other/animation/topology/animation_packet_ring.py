#!/usr/bin/env python3
"""Packet-ring animation stress test for Tesserax."""

import argparse
import math
import random
from collections import deque
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, Parallel, Scene
from tesserax.color import hls


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def ring_palette(count: int) -> list:
    if count <= 1:
        return [Colors.DodgerBlue]
    return [hls(i / count, 0.52, 0.72) for i in range(count)]


def build_graph(nodes: int, chords: int, rng: random.Random) -> tuple[list[list[int]], set[tuple[int, int]]]:
    adj = [[] for _ in range(nodes)]
    ring_edges: set[tuple[int, int]] = set()

    for i in range(nodes):
        cw = (i + 1) % nodes
        ccw = (i - 1) % nodes
        adj[i].extend([cw, ccw])
        ring_edges.add((i, cw))
        ring_edges.add((i, ccw))

    chord_edges: set[tuple[int, int]] = set()
    attempts = 0
    target_pairs = max(0, chords)
    while len(chord_edges) < target_pairs * 2 and attempts < target_pairs * 30 + 200:
        attempts += 1
        a = rng.randrange(nodes)
        b = rng.randrange(nodes)
        if a == b:
            continue
        # avoid near-neighbor edges (already ring-like)
        gap = min((a - b) % nodes, (b - a) % nodes)
        if gap <= 1:
            continue
        if (a, b) in ring_edges or (a, b) in chord_edges:
            continue
        chord_edges.add((a, b))
        chord_edges.add((b, a))
        adj[a].append(b)
        adj[b].append(a)

    return adj, chord_edges


def bfs_dists_to_target(target: int, rev_adj: list[list[int]]) -> list[int]:
    inf = 10**9
    dist = [inf] * len(rev_adj)
    dist[target] = 0
    q = deque([target])
    while q:
        cur = q.popleft()
        for prev in rev_adj[cur]:
            if dist[prev] == inf:
                dist[prev] = dist[cur] + 1
                q.append(prev)
    return dist


def select_next_node(
    mode: str,
    current: int,
    target: int,
    nodes: int,
    adj: list[list[int]],
    dists: list[int],
    chord_edges: set[tuple[int, int]],
    rng: random.Random,
    bias_strength: float,
    chord_boost: float,
) -> int:
    neighbors = adj[current]
    if not neighbors:
        return current

    if mode == "clockwise":
        return (current + 1) % nodes

    if mode == "random":
        return rng.choice(neighbors)

    # shortest or biased
    best_dist = min(dists[n] for n in neighbors)
    if mode == "shortest":
        best_neighbors = [n for n in neighbors if dists[n] == best_dist]
        return rng.choice(best_neighbors)

    # biased: weighted preference for short path + optional chord usage bonus
    weights = []
    for nxt in neighbors:
        base = math.exp(-bias_strength * max(0, dists[nxt]))
        if (current, nxt) in chord_edges:
            base *= (1.0 + chord_boost)
        weights.append(base)

    total = sum(weights)
    if total <= 0:
        return rng.choice(neighbors)
    cut = rng.uniform(0, total)
    acc = 0.0
    for nxt, w in zip(neighbors, weights):
        acc += w
        if acc >= cut:
            return nxt
    return neighbors[-1]


def build_packet_animation(
    packet: Circle,
    path_nodes: list[int],
    positions: list[Point],
    duration: float,
    start: float,
    hop_time: float,
) -> object:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(abs_t: float, p: Point) -> None:
        t = clamp(abs_t / duration, 0.0, 1.0)
        tx[t] = p.x
        ty[t] = p.y

    p0 = positions[path_nodes[0]]
    stamp(0.0, p0)
    stamp(start, p0)
    eps = max(0.01, duration * 0.01)
    show_t = clamp((start + eps) / duration, 0.0, 1.0)
    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[show_t] = 1.0
    sy[show_t] = 1.0

    t_abs = start
    for prev, nxt in zip(path_nodes, path_nodes[1:]):
        p_prev = positions[prev]
        p_next = positions[nxt]
        # Add midpoint to emulate curvy movement visually.
        mx = (p_prev.x + p_next.x) / 2
        my = (p_prev.y + p_next.y) / 2
        t_abs += hop_time * 0.5
        stamp(t_abs, Point(mx, my))
        t_abs += hop_time * 0.5
        stamp(t_abs, p_next)

    hide_t = clamp((t_abs + eps) / duration, 0.0, 1.0)
    sx[hide_t] = 0.0
    sy[hide_t] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0
    stamp(duration, positions[path_nodes[-1]])

    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated packet-ring stress test.")
    p.add_argument("--nodes", type=int, default=28, help="Number of ring nodes.")
    p.add_argument("--chords", type=int, default=20, help="Undirected chord pairs.")
    p.add_argument("--packets", type=int, default=280, help="Number of animated packets.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument(
        "--routing",
        choices=["random", "clockwise", "shortest", "biased"],
        default="random",
        help="Packet routing mode.",
    )
    p.add_argument("--hop-time", type=float, default=0.35, help="Seconds per hop.")
    p.add_argument(
        "--retarget-prob",
        type=float,
        default=0.22,
        help="Chance of choosing a new destination target after each hop.",
    )
    p.add_argument(
        "--bias-strength",
        type=float,
        default=0.9,
        help="Distance weighting for biased routing.",
    )
    p.add_argument(
        "--chord-boost",
        type=float,
        default=0.6,
        help="Extra preference for chord edges in biased routing.",
    )
    p.add_argument("--pulse-cycles", type=float, default=3.0, help="Node pulse cycle count.")
    p.add_argument("--lag", type=float, default=0.03, help="Node pulse lag ratio.")
    p.add_argument("--seed", type=int, default=17, help="Random seed.")
    p.add_argument("--width", type=int, default=1700, help="Canvas width.")
    p.add_argument("--height", type=int, default=1000, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="packet_ring.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    nodes = max(6, args.nodes)
    chords = max(0, args.chords)
    packets = max(1, args.packets)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)
    hop_time = max(0.05, args.hop_time)
    retarget_prob = clamp(args.retarget_prob, 0.0, 1.0)
    bias_strength = max(0.01, args.bias_strength)
    chord_boost = max(0.0, args.chord_boost)

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
    canvas.add(
        Text("Packet Ring Animation Stress Test", size=24, fill=Colors.DarkBlue).move_to(
            Point(args.width / 2, 42)
        )
    )
    canvas.add(
        Text(
            f"nodes={nodes} chords={chords} packets={packets} routing={args.routing}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 70))
    )

    cx, cy = args.width / 2, args.height / 2 + 12
    radius = min(args.width, args.height) * 0.34
    positions = []
    for i in range(nodes):
        a = 2 * math.pi * i / nodes - math.pi / 2
        positions.append(Point(cx + radius * math.cos(a), cy + radius * math.sin(a)))

    adj, chord_edges = build_graph(nodes, chords, rng)
    rev_adj = [[] for _ in range(nodes)]
    for src, outs in enumerate(adj):
        for dst in outs:
            rev_adj[dst].append(src)

    # Draw edges first (under nodes).
    for src, outs in enumerate(adj):
        p1 = positions[src]
        for dst in outs:
            p2 = positions[dst]
            is_ring = (src - dst) % nodes in (1, nodes - 1)
            stroke = Colors.Gray.transparent(0.22 if is_ring else 0.16)
            width = 1.1 if is_ring else 0.9
            if is_ring:
                # gentle arc around ring
                direction = 1 if (dst - src) % nodes == 1 else -1
                curve = 0.12 * direction
            else:
                # small random arc for cross-links
                curve = 0.08 if src < dst else -0.08
            canvas.add(
                Arrow(
                    p1=p1,
                    p2=p2,
                    curvature=curve,
                    stroke=stroke,
                    width=width,
                    marker_end=None,
                )
            )

    # Nodes and labels.
    node_colors = ring_palette(nodes)
    node_shapes = []
    for i, p in enumerate(positions):
        n = Circle(r=13, fill=node_colors[i], stroke=Colors.DarkBlue.transparent(0.60), width=1.0)
        n.move_to(p)
        canvas.add(n)
        canvas.add(Text(str(i), size=8, fill=Colors.Black, font="monospace").move_to(p))
        node_shapes.append(n)

    # Packets.
    packet_palette = [Colors.Crimson, Colors.DarkOrange, Colors.MediumBlue, Colors.SeaGreen]
    packet_anims = []
    max_hops = max(2, int(duration / hop_time))
    dist_cache: dict[int, list[int]] = {}
    for i in range(packets):
        cur = rng.randrange(nodes)
        target = rng.randrange(nodes)
        route = [cur]
        for _ in range(max_hops):
            if cur == target or rng.random() < retarget_prob:
                target = rng.randrange(nodes)
            if target not in dist_cache:
                dist_cache[target] = bfs_dists_to_target(target, rev_adj)
            nxt = select_next_node(
                mode=args.routing,
                current=cur,
                target=target,
                nodes=nodes,
                adj=adj,
                dists=dist_cache[target],
                chord_edges=chord_edges,
                rng=rng,
                bias_strength=bias_strength,
                chord_boost=chord_boost,
            )
            route.append(nxt)
            cur = nxt

        packet = Circle(
            r=3.2 + (i % 3) * 0.7,
            fill=packet_palette[i % len(packet_palette)].transparent(0.9),
            stroke=Colors.Black.transparent(0.18),
            width=0.4,
        )
        packet.move_to(positions[route[0]])
        canvas.add(packet)

        start = rng.uniform(0.0, duration * 0.55) + (i % 11) * 0.01
        travel_budget = max(0.2, duration - start - 0.02)
        effective_hops = max(1, len(route) - 1)
        packet_hop_time = min(hop_time, travel_budget / effective_hops)
        packet_anims.append(
            build_packet_animation(
                packet=packet,
                path_nodes=route,
                positions=positions,
                duration=duration,
                start=start,
                hop_time=packet_hop_time,
            )
        )

    # Node pulse waves.
    node_pulses = []
    for n in node_shapes:
        node_pulses.append(
            n.animate.keyframes(
                sx={0.0: 1.0, 0.5: 1.20, 1.0: 1.0},
                sy={0.0: 1.0, 0.5: 1.20, 1.0: 1.0},
                width={0.0: 1.0, 0.5: 2.4, 1.0: 1.0},
            ).repeating(args.pulse_cycles)
        )

    combined = Parallel(
        *packet_anims,
        Delayed(*node_pulses, lag_ratio=args.lag),
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
    print(
        f"   nodes={nodes}, chords={chords}, packets={packets}, routing={args.routing}, "
        f"frames={int(duration * fps)}"
    )


if __name__ == "__main__":
    main()
