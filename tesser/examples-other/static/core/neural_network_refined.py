#!/usr/bin/env python3
"""High-complexity neural network visualizations for Tesserax capability testing."""

import argparse
import math
from dataclasses import dataclass

from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Container,
    Line,
    Path,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    Text,
    render_batch,
)


@dataclass
class LayerSpec:
    name: str
    size: int
    color: object


def pseudo_weight(i: int, j: int, layer_idx: int) -> float:
    """Deterministic pseudo-random value in [-1, 1] for stable rendering."""
    seed = (i + 1) * 12.9898 + (j + 1) * 78.233 + (layer_idx + 1) * 37.719
    return math.sin(seed)


def build_layers(
    canvas: Canvas,
    specs: list[LayerSpec],
    start_x: float = 140.0,
    x_gap: float = 250.0,
    center_y: float = 430.0,
    node_gap: float = 44.0,
    radius: float = 14.0,
) -> tuple[list[list[Circle]], list[float]]:
    layers: list[list[Circle]] = []
    xs: list[float] = []

    for layer_idx, spec in enumerate(specs):
        x = start_x + layer_idx * x_gap
        xs.append(x)
        y0 = center_y - ((spec.size - 1) * node_gap) / 2
        layer_nodes: list[Circle] = []

        layer_h = (spec.size - 1) * node_gap + radius * 2 + 34
        panel = Rect(
            w=radius * 4.8,
            h=layer_h,
            fill=Colors.White,
            stroke=Colors.DarkGray.transparent(0.35),
            width=1.0,
        )
        panel.move_to(Point(x, center_y + 8))
        canvas.add(panel)

        for node_idx in range(spec.size):
            y = y0 + node_idx * node_gap
            node = Circle(
                r=radius,
                fill=spec.color,
                stroke=Colors.DarkBlue.transparent(0.7),
                width=1.2,
            )
            node.move_to(Point(x, y))
            canvas.add(node)
            layer_nodes.append(node)

            if spec.size <= 12:
                t = Text(str(node_idx + 1), size=8, fill=Colors.Black, font="monospace")
                t.move_to(Point(x, y))
                canvas.add(t)

        title = Text(spec.name, size=13, fill=Colors.Black, font="sans-serif")
        title.move_to(Point(x, y0 - 30))
        canvas.add(title)

        layers.append(layer_nodes)

    return layers, xs


def add_dense_connections(
    canvas: Canvas, layers: list[list[Circle]], width_scale: float = 1.0
) -> None:
    for layer_idx in range(len(layers) - 1):
        left = layers[layer_idx]
        right = layers[layer_idx + 1]

        for i, src in enumerate(left):
            src_p = src.anchor("right")
            for j, dst in enumerate(right):
                dst_p = dst.anchor("left")
                w = pseudo_weight(i, j, layer_idx)
                mag = abs(w)
                alpha = 0.10 + 0.28 * mag
                stroke = (
                    Colors.DodgerBlue.transparent(alpha)
                    if w >= 0
                    else Colors.OrangeRed.transparent(alpha)
                )
                bend = ((j / max(1, len(right) - 1)) - 0.5) * 0.22
                edge = Arrow(
                    p1=src_p,
                    p2=dst_p,
                    curvature=bend,
                    stroke=stroke,
                    width=(0.30 + 0.95 * mag) * width_scale,
                    marker_end=None,
                )
                canvas.add(edge)


def add_sparse_connections(
    canvas: Canvas, layers: list[list[Circle]], fanout: int = 4, width_scale: float = 1.0
) -> None:
    for layer_idx in range(len(layers) - 1):
        left = layers[layer_idx]
        right = layers[layer_idx + 1]
        rlen = len(right)
        step = max(1, rlen // fanout)

        for i, src in enumerate(left):
            src_p = src.anchor("right")
            for k in range(fanout):
                j = (i * step + k * (layer_idx + 2)) % rlen
                dst = right[j]
                dst_p = dst.anchor("left")
                w = pseudo_weight(i, j, layer_idx)
                mag = abs(w)
                stroke = (
                    Colors.MediumBlue.transparent(0.18 + 0.35 * mag)
                    if w >= 0
                    else Colors.DarkOrange.transparent(0.18 + 0.35 * mag)
                )
                edge = Arrow(
                    p1=src_p,
                    p2=dst_p,
                    curvature=(k - (fanout - 1) / 2) * 0.10,
                    stroke=stroke,
                    width=(0.9 + 1.4 * mag) * width_scale,
                    marker_end=None,
                )
                canvas.add(edge)


def add_skip_path(
    canvas: Canvas, source: Circle, target: Circle, lift: float, stroke: object, width: float
) -> None:
    p1 = source.anchor("top")
    p2 = target.anchor("top")
    cx1 = p1.x + (p2.x - p1.x) * 0.28
    cx2 = p1.x + (p2.x - p1.x) * 0.72
    yctrl = min(p1.y, p2.y) - lift
    curve = (
        Path(stroke=stroke, fill=Colors.Transparent, width=width, marker_end="arrow")
        .jump_to(p1.x, p1.y - 2)
        .cubic_to(cx1, yctrl, cx2, yctrl, p2.x, p2.y - 2)
    )
    canvas.add(curve)


def add_weight_legend(canvas: Canvas, x: float, y: float) -> None:
    card = Container(
        padding=16,
        corner_radius=10,
        fill=Colors.White.transparent(0.85),
        stroke=Colors.DarkGray.transparent(0.45),
        width=1.0,
    )
    card.move_to(Point(x, y))

    title = Text("Weight Encoding", size=12, fill=Colors.Black)
    title.move_to(Point(0, -25))
    card.add(title)

    pos = Line(
        Point(-58, -2),
        Point(58, -2),
        stroke=Colors.DodgerBlue.transparent(0.55),
        width=2.2,
    )
    neg = Line(
        Point(-58, 16),
        Point(58, 16),
        stroke=Colors.OrangeRed.transparent(0.55),
        width=2.2,
    )
    card.add(pos, neg)
    card.add(Text("positive", size=10, fill=Colors.Black, anchor="start").move_to(Point(-62, -2)))
    card.add(Text("negative", size=10, fill=Colors.Black, anchor="start").move_to(Point(-62, 16)))

    canvas.add(card)


def dense_mlp_demo(scale: float = 1.0) -> Canvas:
    canvas = Canvas(width=1800, height=980)
    specs = [
        LayerSpec("Input", 10, Colors.LightBlue),
        LayerSpec("Hidden A", 20, Colors.LightGreen),
        LayerSpec("Hidden B", 20, Colors.LightGreen),
        LayerSpec("Fusion", 14, Colors.LightYellow),
        LayerSpec("Bottleneck", 8, Colors.LightCoral),
        LayerSpec("Output", 4, Colors.Plum),
    ]
    layers, xs = build_layers(canvas, specs, x_gap=250)
    add_dense_connections(canvas, layers, width_scale=scale)

    # Prediction bars near output nodes for richer composition.
    for i, node in enumerate(layers[-1]):
        score = 0.20 + i * 0.23
        left = node.anchor("right").x + 20
        y = node.anchor("center").y
        bar_bg = Rect(w=110, h=14, fill=Colors.White, stroke=Colors.Gray.transparent(0.6), width=1)
        bar_fg = Rect(w=110 * score, h=14, fill=Colors.SeaGreen.transparent(0.65), stroke=Colors.Transparent, width=0)
        bar_bg.move_to(Point(left + 55, y))
        bar_fg.move_to(Point(left + (110 * score) / 2, y))
        canvas.add(bar_bg, bar_fg)
        canvas.add(Text(f"{score:.2f}", size=10, fill=Colors.Black, anchor="start").move_to(Point(left + 118, y)))

    title = Text("Dense MLP Stress Test (1000+ weighted edges)", size=24, fill=Colors.DarkBlue)
    title.move_to(Point((xs[0] + xs[-1]) / 2, 54))
    canvas.add(title)
    subtitle = Text(
        "Curved all-to-all links, signed edge colors, output score bars",
        size=13,
        fill=Colors.Gray,
    )
    subtitle.move_to(Point((xs[0] + xs[-1]) / 2, 84))
    canvas.add(subtitle)

    add_weight_legend(canvas, x=xs[-1] + 210, y=170)
    canvas.fit(padding=26, crop=False)
    return canvas


def hybrid_residual_demo(fanout: int = 4, scale: float = 1.0) -> Canvas:
    canvas = Canvas(width=1900, height=1020)
    specs = [
        LayerSpec("Embedding", 12, Colors.LightSkyBlue),
        LayerSpec("Attention", 12, Colors.LightCyan),
        LayerSpec("FeedForward", 16, Colors.Honeydew),
        LayerSpec("Compression", 8, Colors.MistyRose),
        LayerSpec("Classifier", 4, Colors.Thistle),
    ]
    layers, xs = build_layers(canvas, specs, x_gap=290, node_gap=40)

    add_sparse_connections(canvas, layers, fanout=fanout, width_scale=scale)

    # Residual/skip routes across blocks.
    add_skip_path(
        canvas,
        source=layers[0][len(layers[0]) // 2],
        target=layers[2][len(layers[2]) // 2],
        lift=170,
        stroke=Colors.MediumVioletRed.transparent(0.55),
        width=2.4,
    )
    add_skip_path(
        canvas,
        source=layers[1][len(layers[1]) // 2],
        target=layers[3][len(layers[3]) // 2],
        lift=190,
        stroke=Colors.SlateBlue.transparent(0.55),
        width=2.2,
    )
    add_skip_path(
        canvas,
        source=layers[2][len(layers[2]) // 2],
        target=layers[4][len(layers[4]) // 2],
        lift=210,
        stroke=Colors.ForestGreen.transparent(0.55),
        width=2.4,
    )

    # Attention-head style ribbons.
    head_colors = [Colors.Red, Colors.DarkOrange, Colors.Goldenrod, Colors.DarkGreen]
    for h, color in enumerate(head_colors):
        src = layers[0][h * 2 + 2]
        dst = layers[1][h * 2 + 3]
        a = Arrow(
            p1=src.anchor("right"),
            p2=dst.anchor("left"),
            curvature=(h - 1.5) * 0.22,
            stroke=color.transparent(0.50),
            width=2.8,
            marker_end=None,
        )
        canvas.add(a)

        tag = Text(f"head {h+1}", size=9, fill=Colors.Black)
        mid_x = (src.anchor("right").x + dst.anchor("left").x) / 2
        mid_y = (src.anchor("right").y + dst.anchor("left").y) / 2 + (h - 1.5) * 28
        tag.move_to(Point(mid_x, mid_y))
        canvas.add(tag)

    # Activation sparkline panel.
    spark = []
    for i in range(60):
        x = i * 7.5
        y = 20 * math.sin(i * 0.33) + 10 * math.sin(i * 0.11 + 1.2)
        spark.append(Point(x, y))
    sparkline = Polyline(
        points=spark,
        smoothness=0.8,
        stroke=Colors.MediumBlue.transparent(0.8),
        width=2.0,
    ).center()
    sparkline.move_to(Point(xs[2], 855))
    canvas.add(sparkline)
    canvas.add(Text("activation trend", size=11, fill=Colors.Gray).move_to(Point(xs[2], 890)))

    # Mini confusion-matrix inset.
    inset_x = xs[-1] + 220
    inset_y = 620
    cell = 24
    matrix = [
        [0.92, 0.05, 0.02, 0.01],
        [0.06, 0.88, 0.04, 0.02],
        [0.03, 0.07, 0.84, 0.06],
        [0.01, 0.03, 0.08, 0.88],
    ]
    for r in range(4):
        for c in range(4):
            v = matrix[r][c]
            shade = Colors.SteelBlue.transparent(0.08 + 0.80 * v)
            sq = Rect(w=cell, h=cell, fill=shade, stroke=Colors.Gray.transparent(0.5), width=0.8)
            sq.move_to(Point(inset_x + c * (cell + 2), inset_y + r * (cell + 2)))
            canvas.add(sq)
            canvas.add(Text(f"{v:.2f}", size=7, fill=Colors.Black, font="monospace").move_to(sq.anchor("center")))
    canvas.add(Text("confusion matrix", size=11, fill=Colors.Black).move_to(Point(inset_x + 1.5 * (cell + 2), inset_y - 22)))

    title = Text("Hybrid Residual Network Test", size=24, fill=Colors.DarkBlue)
    title.move_to(Point((xs[0] + xs[-1]) / 2, 52))
    canvas.add(title)
    subtitle = Text(
        "Sparse routed edges, multi-head ribbons, skip paths, analytic insets",
        size=13,
        fill=Colors.Gray,
    )
    subtitle.move_to(Point((xs[0] + xs[-1]) / 2, 82))
    canvas.add(subtitle)

    canvas.fit(padding=26, crop=False)
    return canvas


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render refined neural network stress-test diagrams."
    )
    parser.add_argument(
        "--mode",
        choices=["dense", "hybrid", "both"],
        default="both",
        help="Which diagram to render.",
    )
    parser.add_argument(
        "--fanout",
        type=int,
        default=4,
        help="Connections per source neuron in hybrid mode.",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Global edge width scaling factor.",
    )
    parser.add_argument(
        "--output-prefix",
        type=str,
        default="neural_network",
        help="Output prefix for rendered artifacts.",
    )
    parser.add_argument(
        "--format",
        choices=["svg", "png", "pdf", "ps"],
        default="svg",
        help="Static output format.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fanout = max(1, args.fanout)
    scale = max(0.1, args.scale)
    batch: list[tuple[Canvas, RenderConfig]] = []

    if args.mode in ("dense", "both"):
        dense = dense_mlp_demo(scale=scale)
        batch.append(
            (
                dense,
                RenderConfig(
                    output_path=f"{args.output_prefix}_dense",
                    format=args.format,
                ),
            )
        )

    if args.mode in ("hybrid", "both"):
        hybrid = hybrid_residual_demo(fanout=fanout, scale=scale)
        batch.append(
            (
                hybrid,
                RenderConfig(
                    output_path=f"{args.output_prefix}_hybrid",
                    format=args.format,
                ),
            )
        )

    results = render_batch(batch)
    for result in results:
        print(f"✅ Saved: {result.output_path}")


if __name__ == "__main__":
    main()
