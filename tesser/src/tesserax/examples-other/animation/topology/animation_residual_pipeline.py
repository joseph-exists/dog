#!/usr/bin/env python3
"""Residual pipeline animation stress test for Tesserax."""

import argparse
import random
from pathlib import Path

from tesserax import Arrow, Canvas, Circle, Colors, Point, Rect, Text, RenderConfig, TimingSpec, render_scene
from tesserax.animation import Delayed, Parallel, Scene, Sequence


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def packet_keyframes(
    packet: Circle,
    waypoints: list[Point],
    start_t: float,
    travel_t: float,
) -> object:
    tx: dict[float, float] = {}
    ty: dict[float, float] = {}
    sx: dict[float, float] = {}
    sy: dict[float, float] = {}

    def stamp(t: float, p: Point) -> None:
        t = clamp(t, 0.0, 1.0)
        tx[t] = p.x
        ty[t] = p.y

    eps = 0.008
    stamp(0.0, waypoints[0])
    stamp(start_t, waypoints[0])
    sx[0.0] = 0.0
    sy[0.0] = 0.0
    sx[clamp(start_t + eps, 0, 1)] = 1.0
    sy[clamp(start_t + eps, 0, 1)] = 1.0

    seg = travel_t / max(1, len(waypoints) - 1)
    t = start_t
    for p in waypoints[1:]:
        t += seg
        stamp(t, p)

    hide_t = clamp(t + eps, 0.0, 1.0)
    sx[hide_t] = 0.0
    sy[hide_t] = 0.0
    sx[1.0] = 0.0
    sy[1.0] = 0.0
    stamp(1.0, waypoints[-1])
    return packet.animate.keyframes(tx=tx, ty=ty, sx=sx, sy=sy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Animated residual-pipeline stress test.")
    p.add_argument("--blocks", type=int, default=7, help="Main pipeline block count.")
    p.add_argument("--branches", type=int, default=2, help="Auxiliary branch count.")
    p.add_argument("--packets", type=int, default=260, help="Animated packet count.")
    p.add_argument("--duration", type=float, default=10.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Capture FPS.")
    p.add_argument("--lag", type=float, default=0.04, help="Delayed pulse lag ratio.")
    p.add_argument(
        "--pulse-cycles",
        type=float,
        default=3.0,
        help="Pulse repeats over animation span.",
    )
    p.add_argument(
        "--edge-pulses",
        type=int,
        default=28,
        help="Number of connector edges to pulse.",
    )
    p.add_argument("--seed", type=int, default=23, help="Random seed.")
    p.add_argument("--width", type=int, default=1800, help="Canvas width.")
    p.add_argument("--height", type=int, default=1000, help="Canvas height.")
    p.add_argument("--format", choices=["gif", "mp4"], default="gif", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="residual_pipeline.gif",
        help="Output file path (extension adjusted to --format).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    blocks = max(4, args.blocks)
    branches = max(1, min(args.branches, max(1, blocks - 3)))
    packets = max(1, args.packets)
    duration = max(0.5, args.duration)
    fps = max(1, args.fps)
    edge_pulses = max(0, args.edge_pulses)

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

    title = Text("Residual Pipeline Animation Stress Test", size=24, fill=Colors.DarkBlue)
    title.move_to(Point(args.width / 2, 44))
    canvas.add(title)
    canvas.add(
        Text(
            f"blocks={blocks} branches={branches} packets={packets}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 70))
    )

    # Main blocks.
    x_left, x_right = 170.0, args.width - 170.0
    y_main = args.height * 0.56
    x_step = (x_right - x_left) / (blocks - 1)
    block_shapes = []
    block_centers = []
    for i in range(blocks):
        x = x_left + i * x_step
        r = Rect(
            w=150,
            h=72,
            fill=Colors.LightCyan if 0 < i < blocks - 1 else Colors.LightYellow,
            stroke=Colors.DarkBlue.transparent(0.7),
            width=1.2,
        )
        r.move_to(Point(x, y_main))
        canvas.add(r)
        canvas.add(Text(f"B{i}", size=13, fill=Colors.Black, font="monospace").move_to(Point(x, y_main)))
        block_shapes.append(r)
        block_centers.append(Point(x, y_main))

    # Main path edges.
    connectors = []
    for i in range(blocks - 1):
        a = block_shapes[i]
        b = block_shapes[i + 1]
        e = Arrow(
            p1=a.anchor("right"),
            p2=b.anchor("left"),
            stroke=Colors.Gray.transparent(0.45),
            width=1.2,
            marker_end=None,
        )
        canvas.add(e)
        connectors.append(e)

    # Branch modules above the mid-pipeline blocks.
    branch_nodes = []
    branch_map = []
    middle_start = 1
    for bi in range(branches):
        src_idx = middle_start + bi
        dst_idx = min(src_idx + 2, blocks - 1)
        bx = (block_centers[src_idx].x + block_centers[dst_idx].x) / 2
        by = y_main - 180 - (bi % 2) * 34
        br = Rect(
            w=128,
            h=56,
            fill=Colors.MistyRose,
            stroke=Colors.MediumVioletRed.transparent(0.7),
            width=1.1,
        )
        br.move_to(Point(bx, by))
        canvas.add(br)
        canvas.add(Text(f"AUX{bi+1}", size=11, fill=Colors.Black).move_to(Point(bx, by)))
        branch_nodes.append(br)
        branch_map.append((src_idx, dst_idx, br))

    for src_idx, dst_idx, br in branch_map:
        in_edge = Arrow(
            p1=block_shapes[src_idx].anchor("top"),
            p2=br.anchor("left"),
            curvature=-0.20,
            stroke=Colors.DarkOrange.transparent(0.48),
            width=1.1,
            marker_end=None,
        )
        out_edge = Arrow(
            p1=br.anchor("right"),
            p2=block_shapes[dst_idx].anchor("top"),
            curvature=0.20,
            stroke=Colors.DarkOrange.transparent(0.48),
            width=1.1,
            marker_end=None,
        )
        canvas.add(in_edge, out_edge)
        connectors.extend([in_edge, out_edge])

    # Residual skip edges.
    for i in range(blocks - 2):
        skip = Arrow(
            p1=block_shapes[i].anchor("bottom"),
            p2=block_shapes[i + 2].anchor("bottom"),
            curvature=0.22,
            stroke=Colors.MediumBlue.transparent(0.35),
            width=1.0,
            marker_end=None,
        )
        canvas.add(skip)
        connectors.append(skip)

    # Packet animations.
    packet_palette = [Colors.Crimson, Colors.SeaGreen, Colors.MediumBlue, Colors.DarkOrange]
    packet_anims = []
    for i in range(packets):
        path_points = [block_shapes[0].anchor("left")]
        mode = rng.random()
        if mode < 0.55:
            # Main path.
            for b in block_shapes:
                path_points.append(b.anchor("center"))
            path_points.append(block_shapes[-1].anchor("right"))
        elif mode < 0.82 and branch_map:
            # Branch route.
            src_idx, dst_idx, br = rng.choice(branch_map)
            for j in range(src_idx + 1):
                path_points.append(block_shapes[j].anchor("center"))
            path_points.append(br.anchor("center"))
            for j in range(dst_idx, blocks):
                path_points.append(block_shapes[j].anchor("center"))
            path_points.append(block_shapes[-1].anchor("right"))
        else:
            # Skip-heavy route.
            j = 0
            while j < blocks:
                path_points.append(block_shapes[j].anchor("center"))
                j += 2
            if path_points[-1] != block_shapes[-1].anchor("center"):
                path_points.append(block_shapes[-1].anchor("center"))
            path_points.append(block_shapes[-1].anchor("right"))

        packet = Circle(
            r=3.6 + (i % 2),
            fill=packet_palette[i % len(packet_palette)].transparent(0.90),
            stroke=Colors.Black.transparent(0.2),
            width=0.4,
        )
        packet.move_to(path_points[0])
        canvas.add(packet)

        start = rng.uniform(0.0, 0.68) + (i % 9) * 0.009
        travel = rng.uniform(0.14, 0.34)
        if start + travel > 0.98:
            travel = 0.98 - start
        packet_anims.append(packet_keyframes(packet, path_points, start, max(0.05, travel)))

    # Edge pulse subset.
    edge_anims = []
    if connectors and edge_pulses > 0:
        for e in rng.sample(connectors, k=min(edge_pulses, len(connectors))):
            edge_anims.append(
                e.animate.keyframes(width={0.0: 1.0, 0.5: 2.9, 1.0: 1.0}).repeating(
                    args.pulse_cycles
                )
            )

    # Block pulses.
    block_pulses = []
    for b in block_shapes + branch_nodes:
        block_pulses.append(
            b.animate.keyframes(
                sx={0.0: 1.0, 0.5: 1.08, 1.0: 1.0},
                sy={0.0: 1.0, 0.5: 1.08, 1.0: 1.0},
                width={0.0: 1.2, 0.5: 3.0, 1.0: 1.2},
            ).repeating(args.pulse_cycles)
        )

    # Use Sequence explicitly: short intro title pulse, then full pipeline activity.
    intro = title.animate.keyframes(
        sx={0.0: 0.9, 0.6: 1.08, 1.0: 1.0},
        sy={0.0: 0.9, 0.6: 1.08, 1.0: 1.0},
    )
    main = Parallel(
        *packet_anims,
        *edge_anims,
        Delayed(*block_pulses, lag_ratio=args.lag),
    )
    combined = Sequence(intro.weight(0.12), main.weight(0.88))

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
        f"   blocks={blocks}, branches={branches}, packets={packets}, "
        f"connectors={len(connectors)}, frames={int(duration * fps)}"
    )


if __name__ == "__main__":
    main()
