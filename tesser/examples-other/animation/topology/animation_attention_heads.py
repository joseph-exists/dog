#!/usr/bin/env python3
"""Attention-head animation stress test for Tesserax."""

import argparse
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, KeyframeAnimation, Parallel, Scene
from tesserax.color import hls


@dataclass
class AttentionEdge:
    head: int
    src: int
    dst: int
    shape: Arrow
    start: Point
    end: Point
    bend: float


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def head_palette(count: int) -> list:
    if count <= 1:
        return [Colors.DodgerBlue]
    return [hls(i / count, 0.50, 0.78) for i in range(count)]


def packet_keyframes(
    packet: Circle,
    p0: Point,
    p1: Point,
    p2: Point,
    duration: float,
    start: float,
    travel: float,
) -> KeyframeAnimation:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(abs_t: float, p: Point) -> None:
        t = clamp(abs_t / duration, 0.0, 1.0)
        tx[t] = p.x
        ty[t] = p.y

    eps = max(0.01, duration * 0.01)
    stamp(0.0, p0)
    stamp(start, p0)
    stamp(start + travel * 0.5, p1)
    stamp(start + travel, p2)
    stamp(duration, p2)

    show_t = clamp((start + eps) / duration, 0.0, 1.0)
    hide_t = clamp((start + travel + eps) / duration, 0.0, 1.0)
    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[show_t] = 1.0
    sy[show_t] = 1.0
    sx[hide_t] = 0.0
    sy[hide_t] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0

    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated attention-head stress test.")
    p.add_argument("--tokens", type=int, default=24, help="Token count per side.")
    p.add_argument("--heads", type=int, default=8, help="Number of attention heads.")
    p.add_argument("--topk", type=int, default=4, help="Per-query key connections per head.")
    p.add_argument("--packets", type=int, default=320, help="Number of animated packets.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument(
        "--pulse-cycles",
        type=float,
        default=3.0,
        help="Pulse repetitions over total duration.",
    )
    p.add_argument(
        "--lag",
        type=float,
        default=0.045,
        help="Head-indicator lag ratio.",
    )
    p.add_argument(
        "--edge-pulses",
        type=int,
        default=24,
        help="Number of edges with width pulse animation.",
    )
    p.add_argument("--seed", type=int, default=11, help="Random seed.")
    p.add_argument("--width", type=int, default=1800, help="Canvas width.")
    p.add_argument("--height", type=int, default=1000, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="attention_heads.gif",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    tokens = max(4, args.tokens)
    heads = max(1, args.heads)
    topk = max(1, min(args.topk, tokens))
    packets = max(1, args.packets)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)
    edge_pulses = max(0, min(args.edge_pulses, heads * tokens * topk))

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

    title = Text("Attention Heads Animation Stress Test", size=24, fill=Colors.DarkBlue)
    title.move_to(Point(args.width / 2, 42))
    canvas.add(title)
    subtitle = Text(
        f"tokens={tokens} heads={heads} topk={topk} packets={packets}",
        size=12,
        fill=Colors.Gray,
    )
    subtitle.move_to(Point(args.width / 2, 68))
    canvas.add(subtitle)

    # Node layout.
    x_query = 260.0
    x_key = args.width - 260.0
    y_top = 130.0
    y_bottom = args.height - 120.0
    y_step = (y_bottom - y_top) / max(1, tokens - 1)
    q_nodes: list[Circle] = []
    k_nodes: list[Circle] = []

    for i in range(tokens):
        y = y_top + i * y_step
        q = Circle(r=11, fill=Colors.LightBlue, stroke=Colors.DarkBlue.transparent(0.7), width=1.0)
        q.move_to(Point(x_query, y))
        canvas.add(q)
        canvas.add(Text(f"Q{i}", size=8, fill=Colors.Black, font="monospace").move_to(q.anchor("center")))
        q_nodes.append(q)

        k = Circle(r=11, fill=Colors.LightYellow, stroke=Colors.DarkBlue.transparent(0.7), width=1.0)
        k.move_to(Point(x_key, y))
        canvas.add(k)
        canvas.add(Text(f"K{i}", size=8, fill=Colors.Black, font="monospace").move_to(k.anchor("center")))
        k_nodes.append(k)

    canvas.add(Text("Queries", size=12, fill=Colors.Black).move_to(Point(x_query, y_top - 34)))
    canvas.add(Text("Keys / Values", size=12, fill=Colors.Black).move_to(Point(x_key, y_top - 34)))

    # Head legend + indicators.
    palette = head_palette(heads)
    head_badges: list[Circle] = []
    legend_y = args.height - 42
    legend_left = 160.0
    legend_step = min(160.0, (args.width - 320.0) / max(1, heads - 1))
    for h in range(heads):
        x = legend_left + h * legend_step
        dot = Circle(r=8, fill=palette[h], stroke=Colors.Black.transparent(0.25), width=0.8)
        dot.move_to(Point(x, legend_y))
        canvas.add(dot)
        head_badges.append(dot)
        canvas.add(Text(f"head {h+1}", size=9, fill=Colors.Black).move_to(Point(x + 36, legend_y)))

    # Draw attention edges.
    edges: list[AttentionEdge] = []
    for h in range(heads):
        color = palette[h]
        head_offset = (h - (heads - 1) / 2) * 0.018
        for qi in range(tokens):
            for dst in rng.sample(range(tokens), k=topk):
                src = q_nodes[qi]
                tgt = k_nodes[dst]
                p1 = src.anchor("right")
                p2 = tgt.anchor("left")
                relative = (dst - qi) / max(1, tokens - 1)
                bend = clamp(relative * 0.34 + head_offset, -0.42, 0.42)
                edge = Arrow(
                    p1=p1,
                    p2=p2,
                    curvature=bend,
                    stroke=color.transparent(0.17),
                    width=0.9,
                    marker_end=None,
                )
                canvas.add(edge)
                edges.append(
                    AttentionEdge(
                        head=h,
                        src=qi,
                        dst=dst,
                        shape=edge,
                        start=p1,
                        end=p2,
                        bend=bend,
                    )
                )

    # Animated packets.
    packet_anims = []
    for i in range(packets):
        e = rng.choice(edges)
        color = palette[e.head]
        packet = Circle(
            r=3.2 + (i % 2) * 0.8,
            fill=color.transparent(0.90),
            stroke=Colors.Black.transparent(0.20),
            width=0.4,
        )
        packet.move_to(e.start)
        canvas.add(packet)

        mx = (e.start.x + e.end.x) / 2
        my = (e.start.y + e.end.y) / 2 + e.bend * abs(e.end.x - e.start.x) * 0.42
        mid = Point(mx, my)

        start = rng.uniform(0.0, duration * 0.75) + (i % 9) * 0.012
        travel = rng.uniform(duration * 0.08, duration * 0.24)
        travel = min(travel, duration - start)
        packet_anims.append(
            packet_keyframes(
                packet=packet,
                p0=e.start,
                p1=mid,
                p2=e.end,
                duration=duration,
                start=start,
                travel=travel,
            )
        )

    # Edge pulse animations (subset) to stress style transforms.
    edge_anims = []
    for e in rng.sample(edges, k=edge_pulses) if edge_pulses > 0 else []:
        edge_anims.append(
            e.shape.animate.keyframes(width={0.0: 0.9, 0.5: 2.8, 1.0: 0.9}).repeating(
                args.pulse_cycles
            )
        )

    # Head indicator pulses.
    badge_anims = []
    for dot in head_badges:
        badge_anims.append(
            dot.animate.keyframes(
                sx={0.0: 1.0, 0.5: 1.35, 1.0: 1.0},
                sy={0.0: 1.0, 0.5: 1.35, 1.0: 1.0},
                width={0.0: 0.8, 0.5: 2.4, 1.0: 0.8},
            ).repeating(args.pulse_cycles)
        )

    combined = Parallel(
        *packet_anims,
        *edge_anims,
        Delayed(*badge_anims, lag_ratio=args.lag),
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
        f"   tokens={tokens}, heads={heads}, topk={topk}, packets={packets}, "
        f"edges={len(edges)}, frames={int(duration * fps)}"
    )


if __name__ == "__main__":
    main()
