#!/usr/bin/env python3
"""Extended Tufte-style small multiples with data adapters and richer encodings."""

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import Arrow, Canvas, Colors, Point, Polyline, Rect, Text, RenderConfig, render_scene


@dataclass
class Row:
    panel: str
    cohort: str
    time: float
    value: float
    lower: float
    upper: float
    event: str = ""


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Extended Tufte small-multiples with uncertainty and rank overlays."
    )
    p.add_argument("--data-source", choices=["synthetic", "csv", "json"], default="synthetic")
    p.add_argument(
        "--data-path",
        type=str,
        default="",
        help="Path to CSV/JSON data when --data-source is csv/json.",
    )
    p.add_argument("--panels", type=int, default=9, help="Synthetic panel count.")
    p.add_argument("--cohorts", type=int, default=5, help="Synthetic cohort count.")
    p.add_argument("--points", type=int, default=52, help="Synthetic time points.")
    p.add_argument("--columns", type=int, default=3, help="Panel columns.")
    p.add_argument(
        "--highlight-cohort",
        type=str,
        default="",
        help="Optional cohort label to highlight in every panel.",
    )
    p.add_argument("--seed", type=int, default=121, help="Synthetic RNG seed.")
    p.add_argument("--width", type=int, default=2100, help="Canvas width.")
    p.add_argument("--height", type=int, default=1320, help="Canvas height.")
    p.add_argument("--output", type=str, default="tufte_small_multiples_extended.svg")
    return p.parse_args()


def synthetic_rows(
    panels: int,
    cohorts: int,
    points: int,
    rng: random.Random,
) -> list[Row]:
    rows: list[Row] = []
    panel_names = [f"Metric {i+1}" for i in range(panels)]
    cohort_names = [f"C{i+1}" for i in range(cohorts)]
    for pi, pname in enumerate(panel_names):
        panel_phase = rng.uniform(0, math.pi * 2)
        panel_trend = rng.uniform(-0.4, 0.4)
        for ci, cname in enumerate(cohort_names):
            amp = 1.2 + ci * 0.25 + rng.uniform(-0.08, 0.08)
            offset = rng.uniform(-0.35, 0.35) + ci * 0.2
            volatility = 0.18 + 0.04 * (ci % 3)
            for ti in range(points):
                t = ti / (points - 1)
                signal = (
                    amp * math.sin(2 * math.pi * (1.0 + 0.08 * pi) * t + panel_phase + ci * 0.6)
                    + 0.45 * math.sin(2 * math.pi * (2.4 + 0.2 * ci) * t + 0.5 * panel_phase)
                    + panel_trend * (t - 0.5) * 2.2
                    + offset
                    + rng.uniform(-volatility, volatility)
                )
                band = 0.25 + 0.12 * abs(math.sin(2 * math.pi * (t + ci * 0.09)))
                event = ""
                if ti in (int(points * 0.25), int(points * 0.58), int(points * 0.84)) and ci == 0:
                    event = "policy" if ti % 2 == 0 else "shock"
                rows.append(
                    Row(
                        panel=pname,
                        cohort=cname,
                        time=float(ti),
                        value=signal,
                        lower=signal - band,
                        upper=signal + band,
                        event=event,
                    )
                )
    return rows


def _fnum(d: dict, key: str, default: float = 0.0) -> float:
    try:
        return float(d.get(key, default))
    except Exception:
        return default


def load_csv(path: Path) -> list[Row]:
    rows: list[Row] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            panel = str(r.get("panel", "Panel"))
            cohort = str(r.get("cohort", "C1"))
            time = _fnum(r, "time", 0.0)
            value = _fnum(r, "value", 0.0)
            lower = _fnum(r, "lower", value)
            upper = _fnum(r, "upper", value)
            event = str(r.get("event", ""))
            rows.append(Row(panel, cohort, time, value, lower, upper, event))
    return rows


def load_json(path: Path) -> list[Row]:
    rows: list[Row] = []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("JSON must be a list of objects")
    for r in payload:
        if not isinstance(r, dict):
            continue
        panel = str(r.get("panel", "Panel"))
        cohort = str(r.get("cohort", "C1"))
        time = float(r.get("time", 0.0))
        value = float(r.get("value", 0.0))
        lower = float(r.get("lower", value))
        upper = float(r.get("upper", value))
        event = str(r.get("event", ""))
        rows.append(Row(panel, cohort, time, value, lower, upper, event))
    return rows


def rows_from_source(args: argparse.Namespace) -> list[Row]:
    if args.data_source == "synthetic":
        return synthetic_rows(args.panels, args.cohorts, args.points, random.Random(args.seed))
    if not args.data_path:
        raise ValueError("--data-path is required when --data-source is csv/json")
    path = Path(args.data_path)
    if args.data_source == "csv":
        return load_csv(path)
    return load_json(path)


def scale(v: float, lo: float, hi: float, out_lo: float, out_hi: float) -> float:
    if abs(hi - lo) < 1e-9:
        return (out_lo + out_hi) / 2
    t = (v - lo) / (hi - lo)
    return out_lo + t * (out_hi - out_lo)


def main() -> None:
    args = parse_args()
    rows = rows_from_source(args)
    if not rows:
        raise ValueError("No data rows loaded.")

    panels = sorted(set(r.panel for r in rows))
    cohorts = sorted(set(r.cohort for r in rows))
    cols = max(1, min(args.columns, len(panels)))
    rows_n = math.ceil(len(panels) / cols)

    palette = [
        Colors.DodgerBlue,
        Colors.DarkOrange,
        Colors.SeaGreen,
        Colors.MediumVioletRed,
        Colors.SlateBlue,
        Colors.Crimson,
        Colors.Teal,
        Colors.Goldenrod,
    ]
    cohort_color = {c: palette[i % len(palette)] for i, c in enumerate(cohorts)}
    highlight = args.highlight_cohort if args.highlight_cohort in cohorts else cohorts[-1]

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
        Text("Extended Tufte Small Multiples", size=34, fill=Colors.DarkBlue).move_to(
            Point(args.width / 2, 52)
        )
    )
    canvas.add(
        Text(
            f"source={args.data_source} panels={len(panels)} cohorts={len(cohorts)} highlight={highlight}",
            size=13,
            fill=Colors.Gray,
        ).move_to(Point(args.width / 2, 82))
    )

    outer_margin = 72
    top_margin = 132
    col_gap = 28
    row_gap = 24
    panel_w = (args.width - 2 * outer_margin - (cols - 1) * col_gap) / cols
    panel_h = (args.height - top_margin - outer_margin - (rows_n - 1) * row_gap) / rows_n

    # global cohort slope summary on right side (rank-shift overlay companion)
    global_rank_panel_x = args.width - 170
    global_rank_panel_y = 180
    canvas.add(Text("Global Rank Shift", size=12, fill=Colors.Black).move_to(Point(global_rank_panel_x, global_rank_panel_y - 26)))

    panel_to_rows = {p: [r for r in rows if r.panel == p] for p in panels}

    global_start = {c: [] for c in cohorts}
    global_end = {c: [] for c in cohorts}

    for i, pname in enumerate(panels):
        pr = panel_to_rows[pname]
        pcohorts = sorted(set(r.cohort for r in pr))
        ptimes = sorted(set(r.time for r in pr))

        rr = i // cols
        cc = i % cols
        x0 = outer_margin + cc * (panel_w + col_gap)
        y0 = top_margin + rr * (panel_h + row_gap)

        canvas.add(
            Rect(
                w=panel_w,
                h=panel_h,
                fill=Colors.White,
                stroke=Colors.LightGray.transparent(0.72),
                width=1.0,
            ).move_to(Point(x0 + panel_w / 2, y0 + panel_h / 2))
        )
        canvas.add(
            Text(pname, size=12, fill=Colors.Black, anchor="start").move_to(Point(x0 + 12, y0 + 12))
        )

        plot_left = x0 + 20
        plot_right = x0 + panel_w - 20
        plot_top = y0 + 28
        plot_bottom = y0 + panel_h - 68
        rank_top = y0 + panel_h - 58
        rank_bottom = y0 + panel_h - 10

        vals = [r.value for r in pr]
        lowers = [r.lower for r in pr]
        uppers = [r.upper for r in pr]
        lo = min(lowers + vals)
        hi = max(uppers + vals)
        t_lo = min(ptimes)
        t_hi = max(ptimes)

        # per-panel event lines from any cohort event entries
        events = sorted(set(r.time for r in pr if r.event))
        for ev in events:
            ex = scale(ev, t_lo, t_hi, plot_left, plot_right)
            canvas.add(
                Polyline(
                    points=[Point(ex, plot_top), Point(ex, plot_bottom)],
                    stroke=Colors.LightGray.transparent(0.5),
                    width=0.8,
                )
            )

        # draw all cohorts with highlight emphasis + uncertainty band
        cohort_series = {}
        for c in pcohorts:
            cr = sorted([r for r in pr if r.cohort == c], key=lambda x: x.time)
            cohort_series[c] = cr

            xys = [
                Point(
                    scale(r.time, t_lo, t_hi, plot_left, plot_right),
                    scale(r.value, lo, hi, plot_bottom, plot_top),
                )
                for r in cr
            ]

            if c == highlight:
                # confidence/uncertainty band (polygon-like closed path).
                upper_pts = [
                    Point(
                        scale(r.time, t_lo, t_hi, plot_left, plot_right),
                        scale(r.upper, lo, hi, plot_bottom, plot_top),
                    )
                    for r in cr
                ]
                lower_pts = [
                    Point(
                        scale(r.time, t_lo, t_hi, plot_left, plot_right),
                        scale(r.lower, lo, hi, plot_bottom, plot_top),
                    )
                    for r in reversed(cr)
                ]
                band = Polyline(
                    points=upper_pts + lower_pts,
                    closed=True,
                    fill=cohort_color[c].transparent(0.14),
                    stroke=cohort_color[c].transparent(0.12),
                    width=0.5,
                )
                canvas.add(band)

            canvas.add(
                Polyline(
                    points=xys,
                    stroke=cohort_color[c].transparent(0.85 if c == highlight else 0.35),
                    width=2.0 if c == highlight else 1.0,
                    smoothness=0.35,
                )
            )

            if c == highlight:
                canvas.add(
                    Text(c, size=10, fill=cohort_color[c], anchor="start").move_to(
                        Point(plot_right + 4, xys[-1].y)
                    )
                )

        # panel-level callout: largest deviation of highlighted from cohort median
        cvals_by_time = {}
        for r in pr:
            cvals_by_time.setdefault(r.time, []).append(r.value)
        med_by_time = {}
        for t, vals_t in cvals_by_time.items():
            sv = sorted(vals_t)
            med_by_time[t] = sv[len(sv) // 2]

        if highlight in cohort_series:
            best = None
            for r in cohort_series[highlight]:
                dev = abs(r.value - med_by_time.get(r.time, r.value))
                if best is None or dev > best[0]:
                    best = (dev, r)
            if best:
                _, br = best
                bx = scale(br.time, t_lo, t_hi, plot_left, plot_right)
                by = scale(br.value, lo, hi, plot_bottom, plot_top)
                callout_x = clamp(bx + 70, plot_left + 40, plot_right - 10)
                callout_y = clamp(by - 44, plot_top + 16, plot_bottom - 16)
                canvas.add(
                    Arrow(
                        p1=Point(callout_x - 30, callout_y + 8),
                        p2=Point(bx, by),
                        stroke=Colors.DarkGray.transparent(0.8),
                        width=0.9,
                        marker_end=None,
                    )
                )
                canvas.add(
                    Text(
                        f"Δ{best[0]:.2f}",
                        size=9,
                        fill=Colors.Black,
                        anchor="start",
                    ).move_to(Point(callout_x - 28, callout_y))
                )

        # rank-shift overlay (panel local): start rank -> end rank.
        start_rank_vals = []
        end_rank_vals = []
        for c in pcohorts:
            cr = cohort_series[c]
            if cr:
                start_rank_vals.append((c, cr[0].value))
                end_rank_vals.append((c, cr[-1].value))
                global_start[c].append(cr[0].value)
                global_end[c].append(cr[-1].value)

        start_rank = {c: i + 1 for i, (c, _) in enumerate(sorted(start_rank_vals, key=lambda x: x[1], reverse=True))}
        end_rank = {c: i + 1 for i, (c, _) in enumerate(sorted(end_rank_vals, key=lambda x: x[1], reverse=True))}
        max_rank = max(1, len(pcohorts))
        left_rank_x = x0 + 26
        right_rank_x = x0 + panel_w - 26

        for c in pcohorts:
            y_l = scale(start_rank[c], 1, max_rank, rank_top, rank_bottom)
            y_r = scale(end_rank[c], 1, max_rank, rank_top, rank_bottom)
            color = cohort_color[c].transparent(0.9 if c == highlight else 0.4)
            canvas.add(
                Polyline(
                    points=[Point(left_rank_x, y_l), Point(right_rank_x, y_r)],
                    stroke=color,
                    width=1.4 if c == highlight else 1.0,
                )
            )

    # Global rank-shift overlay.
    cohort_global_pairs = []
    for c in cohorts:
        if global_start[c] and global_end[c]:
            cohort_global_pairs.append(
                (c, sum(global_start[c]) / len(global_start[c]), sum(global_end[c]) / len(global_end[c]))
            )
    if cohort_global_pairs:
        s_rank = {c: i + 1 for i, (c, _, _) in enumerate(sorted(cohort_global_pairs, key=lambda x: x[1], reverse=True))}
        e_rank = {c: i + 1 for i, (c, _, _) in enumerate(sorted(cohort_global_pairs, key=lambda x: x[2], reverse=True))}
        max_rank = len(cohort_global_pairs)
        for c, _, _ in cohort_global_pairs:
            y1 = scale(s_rank[c], 1, max_rank, global_rank_panel_y, global_rank_panel_y + 190)
            y2 = scale(e_rank[c], 1, max_rank, global_rank_panel_y, global_rank_panel_y + 190)
            col = cohort_color[c].transparent(0.95 if c == highlight else 0.55)
            canvas.add(
                Polyline(
                    points=[Point(global_rank_panel_x - 40, y1), Point(global_rank_panel_x + 40, y2)],
                    stroke=col,
                    width=1.4 if c == highlight else 1.0,
                )
            )
            if c == highlight:
                canvas.add(Text(c, size=10, fill=cohort_color[c], anchor="start").move_to(Point(global_rank_panel_x + 46, y2)))

    result = render_scene(
        canvas,
        RenderConfig(
            output_path=args.output,
            format="svg",
            fit_padding=14,
            fit_crop=False,
        ),
    )
    out = result.output_path
    print(f"✅ Saved: {out}")
    print(
        f"   panels={len(panels)} cohorts={len(cohorts)} data_source={args.data_source} "
        f"rows={len(rows)} highlight={highlight}"
    )
    if args.data_source in ("csv", "json"):
        print("   expected columns/keys: panel, cohort, time, value, lower, upper, event(optional)")


if __name__ == "__main__":
    main()
