#!/usr/bin/env python3
"""Tufte-style small multiples: dense analytical panels with optional animation."""

import argparse
import math
import random

from tesserax import (
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
from tesserax.animation import Parallel, Scene


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Tufte-inspired small multiples stress test.")
    p.add_argument("--panels", type=int, default=8, help="Number of small-multiple panels.")
    p.add_argument("--points", type=int, default=48, help="Time points per panel.")
    p.add_argument("--columns", type=int, default=4, help="Panel columns.")
    p.add_argument(
        "--series",
        type=int,
        default=3,
        help="Context series per panel (one is highlighted).",
    )
    p.add_argument(
        "--events",
        type=int,
        default=3,
        help="Vertical event markers per panel.",
    )
    p.add_argument("--duration", type=float, default=8.0, help="Animation seconds.")
    p.add_argument("--fps", type=int, default=24, help="Render FPS.")
    p.add_argument(
        "--animate",
        action="store_true",
        help="Enable moving cursor/dot overlays (for gif/mp4).",
    )
    p.add_argument("--seed", type=int, default=97, help="Random seed.")
    p.add_argument("--width", type=int, default=1900, help="Canvas width.")
    p.add_argument("--height", type=int, default=1180, help="Canvas height.")
    p.add_argument("--format", choices=["svg", "gif", "mp4"], default="svg", help="Output format.")
    p.add_argument(
        "--output",
        type=str,
        default="tufte_small_multiples.svg",
        help="Output path (extension adjusted to --format).",
    )
    return p.parse_args()


def scale_series(values: list[float], y_top: float, y_bottom: float) -> list[float]:
    lo = min(values)
    hi = max(values)
    if abs(hi - lo) < 1e-9:
        return [(y_top + y_bottom) / 2] * len(values)
    return [y_bottom - (v - lo) * (y_bottom - y_top) / (hi - lo) for v in values]


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    panels = max(1, args.panels)
    points = max(8, args.points)
    cols = max(1, min(args.columns, panels))
    rows = math.ceil(panels / cols)
    series_count = max(2, args.series)
    events = max(0, min(args.events, points - 2))
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
    canvas.add(
        Text("Tufte Small Multiples", size=32, fill=Colors.DarkBlue).move_to(
            Point(args.width / 2, 54)
        )
    )
    canvas.add(
        Text(
            f"panels={panels} points={points} series={series_count} animate={args.animate}",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 84))
    )

    outer_margin = 78
    top_margin = 130
    col_gap = 24
    row_gap = 24
    panel_w = (args.width - 2 * outer_margin - (cols - 1) * col_gap) / cols
    panel_h = (args.height - top_margin - outer_margin - (rows - 1) * row_gap) / rows

    cursor_anims = []
    dot_anims = []

    for i in range(panels):
        r = i // cols
        c = i % cols
        x0 = outer_margin + c * (panel_w + col_gap)
        y0 = top_margin + r * (panel_h + row_gap)

        # Panel frame.
        panel = Rect(
            w=panel_w,
            h=panel_h,
            fill=Colors.White,
            stroke=Colors.LightGray.transparent(0.75),
            width=1.0,
        ).move_to(Point(x0 + panel_w / 2, y0 + panel_h / 2))
        canvas.add(panel)

        # Plot area and residual strip.
        plot_left = x0 + 18
        plot_right = x0 + panel_w - 18
        plot_top = y0 + 24
        plot_bottom = y0 + panel_h - 52
        residual_top = y0 + panel_h - 46
        residual_bottom = y0 + panel_h - 16
        zero_y = (residual_top + residual_bottom) / 2

        title = Text(f"Panel {i+1}", size=12, fill=Colors.Black, anchor="start")
        title.move_to(Point(x0 + 14, y0 + 12))
        canvas.add(title)

        # Event markers.
        event_xs = sorted(rng.sample(range(2, points - 1), k=events)) if events else []
        for ex in event_xs:
            t = ex / (points - 1)
            x = plot_left + t * (plot_right - plot_left)
            canvas.add(
                Polyline(
                    points=[Point(x, plot_top), Point(x, residual_bottom)],
                    stroke=Colors.LightGray.transparent(0.55),
                    width=0.8,
                )
            )

        # Build series.
        raw_series = []
        phase = rng.uniform(0, 2 * math.pi)
        trend = rng.uniform(-0.20, 0.20)
        for si in range(series_count):
            vals = []
            local_phase = phase + si * 0.8
            for t_idx in range(points):
                t = t_idx / (points - 1)
                v = (
                    1.8 * math.sin(2 * math.pi * (t * rng.uniform(0.8, 1.4)) + local_phase)
                    + 0.9 * math.sin(2 * math.pi * (t * rng.uniform(1.5, 2.4)) + local_phase * 0.7)
                    + trend * t * 4.0
                    + rng.uniform(-0.2, 0.2)
                )
                vals.append(v)
            raw_series.append(vals)

        # Context series.
        for s in raw_series[:-1]:
            ys = scale_series(s, plot_top, plot_bottom)
            pts = [
                Point(plot_left + (k / (points - 1)) * (plot_right - plot_left), ys[k])
                for k in range(points)
            ]
            canvas.add(
                Polyline(
                    points=pts,
                    stroke=Colors.DarkGray.transparent(0.25),
                    width=1.0,
                    smoothness=0.3,
                )
            )

        # Highlight series with direct label.
        main_vals = raw_series[-1]
        main_ys = scale_series(main_vals, plot_top, plot_bottom)
        main_pts = [
            Point(plot_left + (k / (points - 1)) * (plot_right - plot_left), main_ys[k])
            for k in range(points)
        ]
        highlight = Polyline(
            points=main_pts,
            stroke=Colors.DarkBlue.transparent(0.88),
            width=2.0,
            smoothness=0.35,
        )
        canvas.add(highlight)
        canvas.add(
            Text(f"S{i+1}", size=10, fill=Colors.DarkBlue, anchor="start").move_to(
                Point(plot_right + 4, main_pts[-1].y)
            )
        )

        # Residual bars (difference vs local moving average).
        residuals = []
        for k in range(points):
            lo = max(0, k - 2)
            hi = min(points, k + 3)
            avg = sum(main_vals[lo:hi]) / (hi - lo)
            residuals.append(main_vals[k] - avg)
        max_res = max(1e-6, max(abs(v) for v in residuals))
        for k in range(0, points, max(1, points // 24)):
            x = plot_left + (k / (points - 1)) * (plot_right - plot_left)
            h = (residuals[k] / max_res) * ((residual_bottom - residual_top) * 0.45)
            y_mid = zero_y
            canvas.add(
                Polyline(
                    points=[Point(x, y_mid), Point(x, y_mid - h)],
                    stroke=Colors.DarkOrange.transparent(0.58),
                    width=1.2,
                )
            )
        canvas.add(
            Polyline(
                points=[Point(plot_left, zero_y), Point(plot_right, zero_y)],
                stroke=Colors.Gray.transparent(0.45),
                width=0.8,
            )
        )

        # Slope summary (left/right endpoints for all series).
        sx_l = x0 + 12
        sx_r = x0 + panel_w - 12
        sy_top = y0 + panel_h - 70
        sy_bottom = y0 + panel_h - 8
        for si, s in enumerate(raw_series):
            s0 = s[0]
            s1 = s[-1]
            # map two values into summary strip y-range
            lo = min(s0, s1) - 0.01
            hi = max(s0, s1) + 0.01
            yl = sy_bottom - (s0 - lo) * (sy_bottom - sy_top) / (hi - lo)
            yr = sy_bottom - (s1 - lo) * (sy_bottom - sy_top) / (hi - lo)
            col = Colors.DarkBlue.transparent(0.7) if si == series_count - 1 else Colors.Gray.transparent(0.45)
            canvas.add(
                Polyline(
                    points=[Point(sx_l, yl), Point(sx_r, yr)],
                    stroke=col,
                    width=1.0 if si < series_count - 1 else 1.4,
                )
            )

        # Optional animation overlays.
        if args.animate and args.format in ("gif", "mp4"):
            cursor = Rect(
                w=2.0,
                h=plot_bottom - plot_top,
                fill=Colors.DarkBlue.transparent(0.18),
                stroke=Colors.Transparent,
                width=0.0,
            ).move_to(Point(plot_left, (plot_top + plot_bottom) / 2))
            canvas.add(cursor)

            cursor_anims.append(
                cursor.animate.keyframes(
                    tx={0.0: plot_left, 1.0: plot_right}
                )
            )

            dot = Circle(r=4, fill=Colors.DarkBlue, stroke=Colors.White, width=0.7).move_to(main_pts[0])
            canvas.add(dot)
            tx = {k / (points - 1): p.x for k, p in enumerate(main_pts)}
            ty = {k / (points - 1): p.y for k, p in enumerate(main_pts)}
            dot_anims.append(dot.animate.keyframes(tx=tx, ty=ty))

    if args.format == "svg":
        result = render_scene(
            canvas,
            RenderConfig(
                output_path=args.output,
                format="svg",
                fit_padding=16,
                fit_crop=False,
                timing=TimingSpec(seed=args.seed),
            ),
        )
        out = result.output_path
        print(f"✅ Saved: {out}")
        print(f"   panels={panels}, points={points}, format=svg (static)")
        return

    scene = Scene(canvas, fps=fps, background="white")
    combined = Parallel(*cursor_anims, *dot_anims) if cursor_anims or dot_anims else Parallel()
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
        f"   panels={panels}, points={points}, format={args.format}, "
        f"animate={args.animate}, frames={int(duration * fps)}"
    )


if __name__ == "__main__":
    main()
