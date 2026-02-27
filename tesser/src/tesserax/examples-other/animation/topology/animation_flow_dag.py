#!/usr/bin/env python3
"""Animated DAG flow stress test for Tesserax animation primitives."""

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, KeyframeAnimation, Parallel, Scene


@dataclass
class Node:
    idx: int
    layer: int
    shape: Circle
    pos: Point


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def split_counts(total: int, buckets: int) -> list[int]:
    base = total // buckets
    rem = total % buckets
    out = [base] * buckets
    for i in range(rem):
        out[i] += 1
    return out


def build_dag(
    canvas: Canvas,
    nodes: int,
    layers: int,
    max_out: int,
    width: int,
    height: int,
    rng: random.Random,
) -> tuple[list[Node], dict[int, list[int]], list[int], list[int]]:
    layer_counts = split_counts(nodes, layers)
    node_list: list[Node] = []
    by_layer: list[list[int]] = []
    radius = 16
    x_margin = 120
    y_margin = 120
    x_step = (width - 2 * x_margin) / max(1, layers - 1)

    idx = 0
    for li, count in enumerate(layer_counts):
        x = x_margin + li * x_step
        y_step = 0.0 if count <= 1 else (height - 2 * y_margin) / (count - 1)
        ids: list[int] = []
        for ni in range(count):
            y = height / 2 if count == 1 else y_margin + ni * y_step
            c = Circle(
                r=radius,
                fill=Colors.LightCyan if li not in (0, layers - 1) else Colors.LightYellow,
                stroke=Colors.DarkBlue.transparent(0.65),
                width=1.2,
            )
            c.move_to(Point(x, y))
            canvas.add(c)
            canvas.add(
                Text(str(idx), size=9, fill=Colors.Black, font="monospace").move_to(
                    Point(x, y)
                )
            )
            node_list.append(Node(idx=idx, layer=li, shape=c, pos=Point(x, y)))
            ids.append(idx)
            idx += 1
        by_layer.append(ids)

    edges: dict[int, list[int]] = {n.idx: [] for n in node_list}
    for li in range(layers - 1):
        this_layer = by_layer[li]
        next_layer = by_layer[li + 1]
        for nid in this_layer:
            out_degree = rng.randint(1, max(1, min(max_out, len(next_layer))))
            for dst in rng.sample(next_layer, k=out_degree):
                if dst not in edges[nid]:
                    edges[nid].append(dst)

    # Ensure each non-input node has at least one predecessor.
    incoming = {n.idx: 0 for n in node_list}
    for src, outs in edges.items():
        for dst in outs:
            incoming[dst] += 1
    for li in range(1, layers):
        prev_layer = by_layer[li - 1]
        for nid in by_layer[li]:
            if incoming[nid] == 0:
                src = rng.choice(prev_layer)
                edges[src].append(nid)
                incoming[nid] += 1

    # Draw edges.
    for src, outs in edges.items():
        p1 = node_list[src].shape.anchor("right")
        for dst in outs:
            p2 = node_list[dst].shape.anchor("left")
            curve = clamp((p2.y - p1.y) / 320.0, -0.24, 0.24)
            canvas.add(
                Arrow(
                    p1=p1,
                    p2=p2,
                    curvature=curve,
                    stroke=Colors.Gray.transparent(0.35),
                    width=1.0,
                    marker_end=None,
                )
            )

    sources = by_layer[0]
    sinks = by_layer[-1]
    return node_list, edges, sources, sinks


def random_path(
    edges: dict[int, list[int]],
    sources: list[int],
    sinks: list[int],
    rng: random.Random,
) -> list[int]:
    cur = rng.choice(sources)
    path = [cur]
    for _ in range(24):
        if cur in sinks or not edges[cur]:
            break
        cur = rng.choice(edges[cur])
        path.append(cur)
    return path


def shortest_hops_to_sink(
    edges: dict[int, list[int]], sinks: set[int]
) -> dict[int, int]:
    dist: dict[int, int] = {}

    def solve(nid: int) -> int:
        if nid in dist:
            return dist[nid]
        if nid in sinks:
            dist[nid] = 0
            return 0
        outs = edges.get(nid, [])
        if not outs:
            dist[nid] = 10**6
            return dist[nid]
        dist[nid] = 1 + min(solve(dst) for dst in outs)
        return dist[nid]

    for nid in edges:
        solve(nid)
    return dist


def weighted_pick(candidates: list[int], weights: list[float], rng: random.Random) -> int:
    total = sum(weights)
    if total <= 0:
        return rng.choice(candidates)

    cut = rng.uniform(0, total)
    acc = 0.0
    for candidate, weight in zip(candidates, weights):
        acc += weight
        if acc >= cut:
            return candidate
    return candidates[-1]


def routed_path(
    mode: str,
    edges: dict[int, list[int]],
    sources: list[int],
    sinks: list[int],
    node_list: list[Node],
    dist_map: dict[int, int],
    rng: random.Random,
    bias_strength: float,
    y_penalty: float,
) -> list[int]:
    cur = rng.choice(sources)
    path = [cur]
    sink_set = set(sinks)
    max_steps = len(node_list) + 2

    for _ in range(max_steps):
        outs = edges.get(cur, [])
        if cur in sink_set or not outs:
            break

        if mode == "random":
            nxt = rng.choice(outs)
        elif mode == "shortest":
            best = min(dist_map.get(dst, 10**6) for dst in outs)
            tied = [dst for dst in outs if dist_map.get(dst, 10**6) == best]
            nxt = rng.choice(tied)
        else:  # biased
            cy = node_list[cur].pos.y
            weights = []
            for dst in outs:
                d = dist_map.get(dst, 10**6)
                dy = abs(node_list[dst].pos.y - cy)
                score = bias_strength * d + y_penalty * dy
                weights.append(math.exp(-score))
            nxt = weighted_pick(outs, weights, rng)

        path.append(nxt)
        cur = nxt

    return path


def packet_keyframes(
    packet: Circle,
    points: list[Point],
    duration: float,
    start: float,
    travel: float,
) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(t_abs: float, p: Point) -> None:
        t = clamp(t_abs / duration, 0.0, 1.0)
        tx[t] = p.x
        ty[t] = p.y

    p0 = points[0]
    stamp(0.0, p0)
    stamp(start, p0)
    eps = duration * 0.01
    show_t = clamp((start + eps) / duration, 0.0, 1.0)
    hide_t = clamp((start + travel + eps) / duration, 0.0, 1.0)

    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[show_t] = 1.0
    sy[show_t] = 1.0

    seg = travel / max(1, len(points) - 1)
    t_abs = start
    for p in points[1:]:
        t_abs += seg
        stamp(t_abs, p)

    sx[hide_t] = 0.0
    sy[hide_t] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0
    stamp(duration, points[-1])

    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated DAG flow stress test.")
    p.add_argument("--nodes", type=int, default=42, help="Number of DAG nodes.")
    p.add_argument("--layers", type=int, default=6, help="Number of DAG layers.")
    p.add_argument("--packets", type=int, default=140, help="Number of moving packets.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument("--max-out", type=int, default=3, help="Max outgoing edges per node.")
    p.add_argument(
        "--routing",
        choices=["random", "shortest", "biased"],
        default="random",
        help="Packet path selection strategy.",
    )
    p.add_argument(
        "--bias-strength",
        type=float,
        default=1.2,
        help="Biased-routing weight for shortest-distance preference.",
    )
    p.add_argument(
        "--y-penalty",
        type=float,
        default=0.010,
        help="Biased-routing penalty for large vertical jumps.",
    )
    p.add_argument(
        "--lag",
        type=float,
        default=0.035,
        help="Node pulse lag ratio for Delayed animation.",
    )
    p.add_argument(
        "--pulse-cycles",
        type=float,
        default=3.0,
        help="How many pulse cycles each node repeats over total duration.",
    )
    p.add_argument("--seed", type=int, default=7, help="Random seed.")
    p.add_argument("--width", type=int, default=1600, help="Canvas width.")
    p.add_argument("--height", type=int, default=950, help="Canvas height.")
    p.add_argument(
        "--format",
        choices=["gif", "mp4"],
        default="gif",
        help="Output format.",
    )
    p.add_argument(
        "--output",
        type=str,
        default="flow_dag.gif",
        help="Output path. Extension is adjusted to match --format.",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)
    nodes = max(6, args.nodes)
    layers = max(2, min(args.layers, nodes))
    packets = max(1, args.packets)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)
    max_out = max(1, args.max_out)

    canvas = Canvas(width=args.width, height=args.height)
    canvas.add(
        Rect(
            w=args.width,
            h=args.height,
            fill=Colors.White,
            stroke=Colors.LightGray.transparent(0.25),
            width=0.0,
        ).move_to(Point(args.width / 2, args.height / 2))
    )
    canvas.add(
        Text("DAG Flow Animation Stress Test", size=24, fill=Colors.DarkBlue).move_to(
            Point(args.width / 2, 42)
        )
    )
    canvas.add(
        Text(
            f"nodes={nodes} layers={layers} packets={packets} "
            f"max_out={max_out} routing={args.routing}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 70))
    )

    node_list, edges, sources, sinks = build_dag(
        canvas=canvas,
        nodes=nodes,
        layers=layers,
        max_out=max_out,
        width=args.width,
        height=args.height,
        rng=rng,
    )

    dist_map = shortest_hops_to_sink(edges, set(sinks))
    packet_anims = []
    packet_palette = [Colors.Crimson, Colors.DarkOrange, Colors.MediumBlue, Colors.SeaGreen]
    for i in range(packets):
        path_ids = routed_path(
            mode=args.routing,
            edges=edges,
            sources=sources,
            sinks=sinks,
            node_list=node_list,
            dist_map=dist_map,
            rng=rng,
            bias_strength=args.bias_strength,
            y_penalty=args.y_penalty,
        )
        path_pts = [node_list[nid].pos for nid in path_ids]
        packet = Circle(
            r=4.0 + (i % 3),
            fill=packet_palette[i % len(packet_palette)].transparent(0.85),
            stroke=Colors.Black.transparent(0.2),
            width=0.6,
        )
        packet.move_to(path_pts[0])
        canvas.add(packet)

        jitter = (i % 7) * 0.035
        start = rng.uniform(0.0, duration * 0.68) + jitter
        travel = rng.uniform(duration * 0.14, duration * 0.35)
        travel = min(travel, duration - start)
        packet_anims.append(
            packet_keyframes(packet, path_pts, duration=duration, start=start, travel=travel)
        )

    node_pulses = []
    for n in node_list:
        node_pulses.append(
            n.shape.animate.keyframes(
                width={0.0: 1.2, 0.5: 3.0, 1.0: 1.2},
                sx={0.0: 1.0, 0.5: 1.18, 1.0: 1.0},
                sy={0.0: 1.0, 0.5: 1.18, 1.0: 1.0},
            ).repeating(args.pulse_cycles)
        )

    combined = Parallel(*packet_anims, Delayed(*node_pulses, lag_ratio=args.lag))

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
        f"   nodes={nodes}, layers={layers}, packets={packets}, "
        f"routing={args.routing}, frames={int(duration*fps)}"
    )


if __name__ == "__main__":
    main()
