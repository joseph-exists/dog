#!/usr/bin/env python3
"""Dataset storyboard scaffold.

Phase 1 currently lands Scene A (dataset profile) with render/report contract wiring.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Point,
    Polyline,
    Rect,
    RenderConfig,
    Text,
    TimingSpec,
    ViewportSpec,
    render_batch,
)


@dataclass(frozen=True)
class Row:
    group: str
    category: str
    time: float
    value: float


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_float(value: str | float | int | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def synthetic_rows(
    *,
    seed: int,
    groups: int,
    categories: int,
    points: int,
) -> list[Row]:
    rng = random.Random(seed)
    rows: list[Row] = []
    group_names = [f"G{i+1}" for i in range(max(1, groups))]
    category_names = [f"C{i+1}" for i in range(max(1, categories))]
    n_points = max(6, points)

    for g_idx, group in enumerate(group_names):
        for c_idx, category in enumerate(category_names):
            phase = rng.uniform(0, 2 * math.pi)
            trend = rng.uniform(-0.12, 0.12)
            amp = 0.8 + rng.uniform(0.1, 0.9) + 0.18 * c_idx
            bias = 0.15 * g_idx
            for t_idx in range(n_points):
                t = float(t_idx)
                x = t_idx / (n_points - 1)
                value = (
                    amp * math.sin(2 * math.pi * (x * (1.0 + 0.08 * c_idx)) + phase)
                    + 0.45 * math.sin(2 * math.pi * (2.2 + 0.15 * g_idx) * x + 0.7 * phase)
                    + trend * t_idx
                    + bias
                    + rng.uniform(-0.12, 0.12)
                )
                rows.append(Row(group=group, category=category, time=t, value=value))
    return rows


def load_csv_rows(
    path: Path,
    *,
    group_col: str,
    category_col: str,
    time_col: str,
    value_col: str,
) -> list[Row]:
    rows: list[Row] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {group_col, category_col, time_col, value_col}
        missing = [c for c in required if c not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(
                "Missing required columns in CSV: "
                + ", ".join(sorted(missing))
                + f". Required: {group_col}, {category_col}, {time_col}, {value_col}."
            )
        for i, r in enumerate(reader, start=2):
            group = str(r.get(group_col, "")).strip()
            category = str(r.get(category_col, "")).strip()
            time = parse_float(r.get(time_col))
            value = parse_float(r.get(value_col))
            if not group or not category or time is None or value is None:
                continue
            rows.append(Row(group=group, category=category, time=time, value=value))
            if i > 200_000:
                break
    return rows


def stddev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mu = fmean(values)
    var = sum((v - mu) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(max(0.0, var))


def dataset_profile(rows: list[Row]) -> dict[str, object]:
    if not rows:
        return {
            "row_count": 0,
            "group_count": 0,
            "category_count": 0,
            "time_count": 0,
            "value_min": 0.0,
            "value_max": 0.0,
            "value_mean": 0.0,
            "value_stddev": 0.0,
            "group_counts": {},
            "category_counts": {},
            "time_counts": {},
        }

    groups = sorted({r.group for r in rows})
    categories = sorted({r.category for r in rows})
    times = sorted({r.time for r in rows})
    values = [r.value for r in rows]

    group_counts: dict[str, int] = {g: 0 for g in groups}
    category_counts: dict[str, int] = {c: 0 for c in categories}
    time_counts: dict[float, int] = {t: 0 for t in times}
    for r in rows:
        group_counts[r.group] += 1
        category_counts[r.category] += 1
        time_counts[r.time] += 1

    return {
        "row_count": len(rows),
        "group_count": len(groups),
        "category_count": len(categories),
        "time_count": len(times),
        "value_min": min(values),
        "value_max": max(values),
        "value_mean": fmean(values),
        "value_stddev": stddev(values),
        "group_counts": group_counts,
        "category_counts": category_counts,
        "time_counts": time_counts,
    }


def draw_rank_bars(
    canvas: Canvas,
    *,
    title: str,
    counts: dict[str, int],
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
) -> None:
    canvas.add(Text(title, size=12, fill=Colors.Black, anchor="start").move_to(Point(x + 4, y + 10)))
    if not counts:
        return
    items = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    max_count = max(v for _, v in items) or 1
    row_h = (h - 24) / len(items)
    for idx, (label, count) in enumerate(items):
        yy = y + 22 + idx * row_h
        bar_w = (count / max_count) * (w - 120)
        canvas.add(
            Rect(
                w=max(1.0, bar_w),
                h=max(6.0, row_h - 6),
                fill=fill,
                stroke=Colors.Transparent,
                width=0,
            ).move_to(Point(x + 70 + bar_w / 2, yy + row_h / 2 - 2))
        )
        canvas.add(Text(label, size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + 4, yy + row_h / 2)))
        canvas.add(Text(str(count), size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + w - 36, yy + row_h / 2)))


def build_scene_a_profile(
    rows: list[Row],
    *,
    width: int,
    height: int,
    source_label: str,
) -> tuple[Canvas, dict[str, object]]:
    stats = dataset_profile(rows)
    canvas = Canvas(width=width, height=height)
    canvas.add(
        Rect(
            w=width,
            h=height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(width / 2, height / 2))
    )

    canvas.add(Text("Dataset Storyboard", size=30, fill=Colors.DarkBlue).move_to(Point(width / 2, 52)))
    canvas.add(Text("Scene A: Dataset Profile", size=18, fill=Colors.Black).move_to(Point(width / 2, 82)))
    canvas.add(Text(f"source={source_label}", size=12, fill=Colors.Gray).move_to(Point(width / 2, 106)))

    cards = [
        ("rows", int(stats["row_count"])),
        ("groups", int(stats["group_count"])),
        ("categories", int(stats["category_count"])),
        ("time points", int(stats["time_count"])),
    ]
    card_w = 250
    card_h = 86
    x_start = (width - len(cards) * card_w - (len(cards) - 1) * 18) / 2
    y_cards = 170
    for i, (label, value) in enumerate(cards):
        cx = x_start + i * (card_w + 18) + card_w / 2
        canvas.add(
            Rect(
                w=card_w,
                h=card_h,
                fill=Colors.LightCyan.transparent(0.55),
                stroke=Colors.DarkGray.transparent(0.4),
                width=1.0,
            ).move_to(Point(cx, y_cards))
        )
        canvas.add(Text(label, size=11, fill=Colors.DarkGray).move_to(Point(cx, y_cards - 18)))
        canvas.add(Text(str(value), size=26, fill=Colors.DarkBlue).move_to(Point(cx, y_cards + 8)))

    # Value distribution strip.
    value_min = float(stats["value_min"])
    value_max = float(stats["value_max"])
    value_mean = float(stats["value_mean"])
    value_sd = float(stats["value_stddev"])
    x0, x1 = 130, width - 130
    y = 278
    canvas.add(Arrow(p1=Point(x0, y), p2=Point(x1, y), stroke=Colors.DarkGray, width=1.8, marker_end=None))

    def vx(v: float) -> float:
        if abs(value_max - value_min) < 1e-9:
            return (x0 + x1) / 2
        t = (v - value_min) / (value_max - value_min)
        return x0 + t * (x1 - x0)

    mu_x = vx(value_mean)
    lo_x = vx(value_mean - value_sd)
    hi_x = vx(value_mean + value_sd)
    canvas.add(
        Rect(
            w=max(3.0, hi_x - lo_x),
            h=16,
            fill=Colors.LightGreen.transparent(0.7),
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point((lo_x + hi_x) / 2, y))
    )
    canvas.add(Circle(r=5.5, fill=Colors.DarkBlue, stroke=Colors.White, width=1.2).move_to(Point(mu_x, y)))
    canvas.add(Text("mean", size=10, fill=Colors.DarkBlue).move_to(Point(mu_x, y - 16)))
    canvas.add(Text(f"min={value_min:.3f}", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(x0, y + 18)))
    canvas.add(Text(f"max={value_max:.3f}", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(x1 - 82, y + 18)))
    canvas.add(Text(f"std={value_sd:.3f}", size=10, fill=Colors.DarkGray).move_to(Point((x0 + x1) / 2, y + 18)))

    draw_rank_bars(
        canvas,
        title="Top groups by row count",
        counts=dict(stats["group_counts"]),
        x=120,
        y=340,
        w=520,
        h=250,
        fill=Colors.SlateBlue.transparent(0.65),
    )
    draw_rank_bars(
        canvas,
        title="Top categories by row count",
        counts=dict(stats["category_counts"]),
        x=670,
        y=340,
        w=520,
        h=250,
        fill=Colors.SeaGreen.transparent(0.65),
    )

    # Time coverage mini-strip.
    time_counts = dict(stats["time_counts"])
    if time_counts:
        t_items = sorted(time_counts.items(), key=lambda kv: kv[0])
        tmax = max(v for _, v in t_items) or 1
        tx0, tx1 = 140, width - 140
        ty0 = height - 90
        ty1 = height - 152
        canvas.add(Text("Time coverage", size=11, fill=Colors.Black, anchor="start").move_to(Point(tx0, ty1 - 12)))
        prev = None
        for t, c in t_items:
            u = 0.0 if len(t_items) <= 1 else (t - t_items[0][0]) / (t_items[-1][0] - t_items[0][0] or 1.0)
            x = tx0 + u * (tx1 - tx0)
            yv = ty0 - (c / tmax) * (ty0 - ty1)
            p = Point(x, yv)
            if prev is not None:
                canvas.add(Arrow(p1=prev, p2=p, stroke=Colors.DarkOrange, width=1.2, marker_end=None))
            prev = p
        canvas.add(Arrow(p1=Point(tx0, ty0), p2=Point(tx1, ty0), stroke=Colors.Gray.transparent(0.55), width=0.8, marker_end=None))

    meta = {
        "scene": "scene_a_profile",
        "source": source_label,
        "row_count": int(stats["row_count"]),
        "group_count": int(stats["group_count"]),
        "category_count": int(stats["category_count"]),
        "time_count": int(stats["time_count"]),
    }
    return canvas, meta


def build_scene_b_small_multiples(
    rows: list[Row],
    *,
    width: int,
    height: int,
    source_label: str,
    max_panels: int,
    max_series: int,
) -> tuple[Canvas, dict[str, object]]:
    canvas = Canvas(width=width, height=height)
    canvas.add(
        Rect(
            w=width,
            h=height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(width / 2, height / 2))
    )
    canvas.add(Text("Dataset Storyboard", size=30, fill=Colors.DarkBlue).move_to(Point(width / 2, 52)))
    canvas.add(Text("Scene B: Small Multiples Breakdown", size=18, fill=Colors.Black).move_to(Point(width / 2, 82)))
    canvas.add(Text(f"source={source_label}", size=12, fill=Colors.Gray).move_to(Point(width / 2, 106)))

    groups = sorted({r.group for r in rows})
    categories = sorted({r.category for r in rows})
    times = sorted({r.time for r in rows})
    if not groups or not categories or not times:
        meta = {"scene": "scene_b_small_multiples", "panel_count": 0, "series_count": 0}
        return canvas, meta

    by_group_count: dict[str, int] = {g: 0 for g in groups}
    for r in rows:
        by_group_count[r.group] += 1
    panel_groups = [g for g, _ in sorted(by_group_count.items(), key=lambda kv: (-kv[1], kv[0]))[: max(1, max_panels)]]

    cols = min(3, len(panel_groups))
    rows_n = math.ceil(len(panel_groups) / cols)
    outer = 72
    top = 136
    col_gap = 22
    row_gap = 18
    panel_w = (width - 2 * outer - (cols - 1) * col_gap) / cols
    panel_h = (height - top - outer - (rows_n - 1) * row_gap) / rows_n

    palette = [
        Colors.DodgerBlue,
        Colors.DarkOrange,
        Colors.SeaGreen,
        Colors.MediumVioletRed,
        Colors.SlateBlue,
        Colors.Crimson,
    ]

    # Pre-index for fast aggregate means.
    cell_values: dict[tuple[str, str, float], list[float]] = {}
    for r in rows:
        cell_values.setdefault((r.group, r.category, r.time), []).append(r.value)

    for i, group in enumerate(panel_groups):
        rr = i // cols
        cc = i % cols
        x0 = outer + cc * (panel_w + col_gap)
        y0 = top + rr * (panel_h + row_gap)
        canvas.add(
            Rect(
                w=panel_w,
                h=panel_h,
                fill=Colors.White,
                stroke=Colors.LightGray.transparent(0.72),
                width=1.0,
            ).move_to(Point(x0 + panel_w / 2, y0 + panel_h / 2))
        )
        canvas.add(Text(f"group={group}", size=11, fill=Colors.Black, anchor="start").move_to(Point(x0 + 10, y0 + 12)))

        # Pick most represented categories inside this group.
        cat_counts: dict[str, int] = {c: 0 for c in categories}
        for r in rows:
            if r.group == group:
                cat_counts[r.category] += 1
        panel_cats = [c for c, n in sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0])) if n > 0][: max(1, max_series)]

        plot_left = x0 + 16
        plot_right = x0 + panel_w - 16
        plot_top = y0 + 28
        plot_bottom = y0 + panel_h - 32

        # Gather all values to scale within panel.
        panel_vals: list[float] = []
        series_values: dict[str, list[tuple[float, float]]] = {}
        for c in panel_cats:
            pts: list[tuple[float, float]] = []
            for t in times:
                vals = cell_values.get((group, c, t), [])
                if not vals:
                    continue
                pts.append((t, fmean(vals)))
            if len(pts) < 2:
                continue
            series_values[c] = pts
            panel_vals.extend(v for _, v in pts)

        if panel_vals:
            lo = min(panel_vals)
            hi = max(panel_vals)
            if abs(hi - lo) < 1e-12:
                hi = lo + 1.0

            for s_idx, (cat, pts) in enumerate(series_values.items()):
                col = palette[s_idx % len(palette)]
                poly_pts: list[Point] = []
                for t, v in pts:
                    u = 0.0 if len(times) <= 1 else (t - times[0]) / (times[-1] - times[0] or 1.0)
                    x = plot_left + u * (plot_right - plot_left)
                    y = plot_bottom - (v - lo) * (plot_bottom - plot_top) / (hi - lo)
                    poly_pts.append(Point(x, y))
                canvas.add(
                    Polyline(
                        points=poly_pts,
                        stroke=col.transparent(0.9),
                        width=1.7 if s_idx == 0 else 1.3,
                        smoothness=0.24,
                    )
                )
                end = poly_pts[-1]
                canvas.add(Text(cat, size=8.5, fill=col, anchor="start").move_to(Point(end.x + 4, end.y)))

            canvas.add(
                Arrow(
                    p1=Point(plot_left, plot_bottom),
                    p2=Point(plot_right, plot_bottom),
                    stroke=Colors.Gray.transparent(0.55),
                    width=0.8,
                    marker_end=None,
                )
            )
            canvas.add(
                Arrow(
                    p1=Point(plot_left, plot_bottom),
                    p2=Point(plot_left, plot_top),
                    stroke=Colors.Gray.transparent(0.55),
                    width=0.8,
                    marker_end=None,
                )
            )

    meta = {
        "scene": "scene_b_small_multiples",
        "source": source_label,
        "panel_count": len(panel_groups),
        "series_cap": max(1, max_series),
        "group_count": len(groups),
        "category_count": len(categories),
        "time_count": len(times),
    }
    return canvas, meta


def build_scene_c_callouts(
    rows: list[Row],
    *,
    width: int,
    height: int,
    source_label: str,
    top_n: int,
) -> tuple[Canvas, dict[str, object]]:
    canvas = Canvas(width=width, height=height)
    canvas.add(
        Rect(
            w=width,
            h=height,
            fill=Colors.White,
            stroke=Colors.Transparent,
            width=0,
        ).move_to(Point(width / 2, height / 2))
    )
    canvas.add(Text("Dataset Storyboard", size=30, fill=Colors.DarkBlue).move_to(Point(width / 2, 52)))
    canvas.add(Text("Scene C: Annotated Callouts", size=18, fill=Colors.Black).move_to(Point(width / 2, 82)))
    canvas.add(Text(f"source={source_label}", size=12, fill=Colors.Gray).move_to(Point(width / 2, 106)))

    if not rows:
        meta = {"scene": "scene_c_callouts", "top_deltas": 0, "outliers": 0, "drivers": 0}
        return canvas, meta

    times = sorted({r.time for r in rows})
    t_first = times[0]
    t_last = times[-1]

    # Delta by (group, category): mean(last) - mean(first)
    by_key_first: dict[tuple[str, str], list[float]] = {}
    by_key_last: dict[tuple[str, str], list[float]] = {}
    for r in rows:
        key = (r.group, r.category)
        if r.time == t_first:
            by_key_first.setdefault(key, []).append(r.value)
        if r.time == t_last:
            by_key_last.setdefault(key, []).append(r.value)

    deltas: list[tuple[str, str, float]] = []
    for key in sorted(set(by_key_first) | set(by_key_last)):
        v0 = by_key_first.get(key, [])
        v1 = by_key_last.get(key, [])
        if not v0 and not v1:
            continue
        m0 = fmean(v0) if v0 else 0.0
        m1 = fmean(v1) if v1 else 0.0
        deltas.append((key[0], key[1], m1 - m0))
    n = max(3, top_n)
    top_deltas = sorted(deltas, key=lambda x: -abs(x[2]))[:n]

    # Outliers via z-score over all rows.
    vals = [r.value for r in rows]
    mu = fmean(vals)
    sd = stddev(vals)
    outliers: list[tuple[Row, float]] = []
    if sd > 1e-12:
        for r in rows:
            z = (r.value - mu) / sd
            outliers.append((r, z))
        outliers = sorted(outliers, key=lambda x: -abs(x[1]))[:n]
    else:
        outliers = [(r, 0.0) for r in rows[:n]]

    # Drivers by category: aggregate delta from first->last.
    cat_first: dict[str, list[float]] = {}
    cat_last: dict[str, list[float]] = {}
    for r in rows:
        if r.time == t_first:
            cat_first.setdefault(r.category, []).append(r.value)
        if r.time == t_last:
            cat_last.setdefault(r.category, []).append(r.value)
    drivers: list[tuple[str, float]] = []
    for cat in sorted(set(cat_first) | set(cat_last)):
        a = cat_first.get(cat, [])
        b = cat_last.get(cat, [])
        d = (fmean(b) if b else 0.0) - (fmean(a) if a else 0.0)
        drivers.append((cat, d))
    top_drivers = sorted(drivers, key=lambda x: -abs(x[1]))[:n]

    # Layout columns.
    col_w = (width - 2 * 86 - 2 * 24) / 3
    col_h = height - 190
    y0 = 170

    def card_col(title: str, col_idx: int) -> tuple[float, float]:
        x0 = 86 + col_idx * (col_w + 24)
        canvas.add(
            Rect(
                w=col_w,
                h=col_h,
                fill=Colors.White,
                stroke=Colors.LightGray.transparent(0.72),
                width=1.0,
            ).move_to(Point(x0 + col_w / 2, y0 + col_h / 2))
        )
        canvas.add(Text(title, size=13, fill=Colors.Black, anchor="start").move_to(Point(x0 + 12, y0 + 14)))
        return x0, y0

    # Column 1: top deltas.
    x, y = card_col(f"Top Deltas (t={t_first:.0f} -> t={t_last:.0f})", 0)
    if top_deltas:
        max_abs = max(abs(d) for _, _, d in top_deltas) or 1.0
        row_h = (col_h - 40) / len(top_deltas)
        for i, (g, c, d) in enumerate(top_deltas):
            yy = y + 32 + i * row_h
            bar_w = (abs(d) / max_abs) * (col_w - 162)
            bar_color = Colors.DarkBlue.transparent(0.72) if d >= 0 else Colors.Crimson.transparent(0.72)
            canvas.add(
                Rect(
                    w=max(2.0, bar_w),
                    h=max(8.0, row_h - 8),
                    fill=bar_color,
                    stroke=Colors.Transparent,
                    width=0,
                ).move_to(Point(x + 112 + bar_w / 2, yy + row_h / 2 - 2))
            )
            canvas.add(Text(f"{g}/{c}", size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + 10, yy + row_h / 2)))
            canvas.add(Text(f"{d:+.3f}", size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + col_w - 54, yy + row_h / 2)))

    # Column 2: outliers.
    x, y = card_col("Outliers (global z-score)", 1)
    if outliers:
        row_h = (col_h - 40) / len(outliers)
        for i, (r, z) in enumerate(outliers):
            yy = y + 32 + i * row_h
            c = Colors.Crimson if z > 0 else Colors.SlateBlue
            canvas.add(Circle(r=4.8, fill=c.transparent(0.8), stroke=Colors.White, width=1.0).move_to(Point(x + 18, yy + row_h / 2)))
            canvas.add(
                Text(
                    f"{r.group}/{r.category} t={r.time:.0f} v={r.value:.3f} z={z:+.2f}",
                    size=9,
                    fill=Colors.DarkGray,
                    anchor="start",
                ).move_to(Point(x + 30, yy + row_h / 2))
            )

    # Column 3: drivers.
    x, y = card_col("Drivers (category-level delta)", 2)
    if top_drivers:
        max_abs = max(abs(v) for _, v in top_drivers) or 1.0
        row_h = (col_h - 40) / len(top_drivers)
        for i, (cat, d) in enumerate(top_drivers):
            yy = y + 32 + i * row_h
            bar_w = (abs(d) / max_abs) * (col_w - 150)
            bar_color = Colors.SeaGreen.transparent(0.72) if d >= 0 else Colors.DarkOrange.transparent(0.72)
            canvas.add(
                Rect(
                    w=max(2.0, bar_w),
                    h=max(8.0, row_h - 8),
                    fill=bar_color,
                    stroke=Colors.Transparent,
                    width=0,
                ).move_to(Point(x + 92 + bar_w / 2, yy + row_h / 2 - 2))
            )
            canvas.add(Text(cat, size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + 10, yy + row_h / 2)))
            canvas.add(Text(f"{d:+.3f}", size=9, fill=Colors.DarkGray, anchor="start").move_to(Point(x + col_w - 54, yy + row_h / 2)))

    # Inline notation strip.
    note_y = height - 26
    canvas.add(
        Text(
            "Callout logic: delta = mean(last_time) - mean(first_time); outlier = global z-score; driver = category aggregate delta",
            size=9,
            fill=Colors.Gray,
        ).move_to(Point(width / 2, note_y))
    )

    meta = {
        "scene": "scene_c_callouts",
        "source": source_label,
        "top_deltas": len(top_deltas),
        "outliers": len(outliers),
        "drivers": len(top_drivers),
    }
    return canvas, meta


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Dataset storyboard (Phase 1: Scene A+B+C).")
    p.add_argument("--mode", choices=["csv", "synthetic"], default="synthetic", help="Dataset source mode.")
    p.add_argument("--input-csv", type=str, default="", help="CSV input path for --mode csv.")
    p.add_argument("--group-col", type=str, default="group", help="CSV group column.")
    p.add_argument("--category-col", type=str, default="category", help="CSV category column.")
    p.add_argument("--time-col", type=str, default="time", help="CSV time column.")
    p.add_argument("--value-col", type=str, default="value", help="CSV value column.")
    p.add_argument("--groups", type=int, default=4, help="Synthetic group count.")
    p.add_argument("--categories", type=int, default=5, help="Synthetic category count.")
    p.add_argument("--points", type=int, default=18, help="Synthetic time points.")
    p.add_argument("--scene-b-panels", type=int, default=6, help="Scene B panel cap (groups).")
    p.add_argument("--scene-b-series", type=int, default=4, help="Scene B series cap per panel (categories).")
    p.add_argument("--scene-c-topn", type=int, default=6, help="Scene C callout cap (currently fixed to 6).")
    p.add_argument("--seed", type=int, default=131, help="Deterministic seed.")
    p.add_argument("--width", type=int, default=1360, help="Canvas width.")
    p.add_argument("--height", type=int, default=840, help="Canvas height.")
    p.add_argument("--format", choices=["svg"], default="svg", help="Output format.")
    p.add_argument("--output-prefix", type=str, default="dataset_storyboard", help="Output prefix.")
    p.add_argument("--report-dir", type=str, default="", help="Optional per-scene report directory.")
    p.add_argument("--summary-report", type=str, default="", help="Optional aggregate summary JSON path.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if args.mode == "csv":
        if not args.input_csv:
            raise ValueError("--input-csv is required when --mode csv.")
        rows = load_csv_rows(
            Path(args.input_csv),
            group_col=args.group_col,
            category_col=args.category_col,
            time_col=args.time_col,
            value_col=args.value_col,
        )
        source_label = f"csv:{Path(args.input_csv).name}"
    else:
        rows = synthetic_rows(
            seed=args.seed,
            groups=max(1, args.groups),
            categories=max(1, args.categories),
            points=max(6, args.points),
        )
        source_label = f"synthetic:g{max(1, args.groups)} c{max(1, args.categories)} p{max(6, args.points)}"

    if not rows:
        raise ValueError("No usable rows after ingest/validation.")

    width = max(800, args.width)
    height = max(520, args.height)
    scene_a_canvas, scene_a_meta = build_scene_a_profile(rows, width=width, height=height, source_label=source_label)
    scene_b_canvas, scene_b_meta = build_scene_b_small_multiples(
        rows,
        width=width,
        height=height,
        source_label=source_label,
        max_panels=max(1, args.scene_b_panels),
        max_series=max(1, args.scene_b_series),
    )
    scene_c_canvas, scene_c_meta = build_scene_c_callouts(
        rows,
        width=width,
        height=height,
        source_label=source_label,
        top_n=max(3, args.scene_c_topn),
    )

    hook_rows: list[dict[str, object]] = []

    def report_hook(result) -> None:
        hook_rows.append(
            {
                "output_path": str(result.output_path),
                "scene": result.metadata.get("scene"),
                "config_fingerprint": result.metadata.get("config_fingerprint"),
                "seed": result.metadata.get("seed"),
            }
        )

    batch = [
        (
            scene_a_canvas,
            RenderConfig(
                output_path=f"{args.output_prefix}_scene_a_profile",
                format=args.format,
                viewport=ViewportSpec(fit_padding=16, fit_crop=False),
                timing=TimingSpec(seed=args.seed),
                metadata=scene_a_meta,
                report_json_path=(
                    str(Path(args.report_dir) / "scene_a_profile.json") if args.report_dir else None
                ),
                report_hook=report_hook,
            ),
        ),
        (
            scene_b_canvas,
            RenderConfig(
                output_path=f"{args.output_prefix}_scene_b_small_multiples",
                format=args.format,
                viewport=ViewportSpec(fit_padding=16, fit_crop=False),
                timing=TimingSpec(seed=args.seed),
                metadata=scene_b_meta,
                report_json_path=(
                    str(Path(args.report_dir) / "scene_b_small_multiples.json")
                    if args.report_dir
                    else None
                ),
                report_hook=report_hook,
            ),
        ),
        (
            scene_c_canvas,
            RenderConfig(
                output_path=f"{args.output_prefix}_scene_c_callouts",
                format=args.format,
                viewport=ViewportSpec(fit_padding=16, fit_crop=False),
                timing=TimingSpec(seed=args.seed),
                metadata=scene_c_meta,
                report_json_path=(
                    str(Path(args.report_dir) / "scene_c_callouts.json")
                    if args.report_dir
                    else None
                ),
                report_hook=report_hook,
            ),
        )
    ]

    results = render_batch(batch)
    for r in results:
        print(f"✅ Saved: {r.output_path}")
        if r.report_path:
            print(f"   report_json={r.report_path}")

    if args.summary_report:
        summary_path = Path(args.summary_report)
        if summary_path.suffix.lower() != ".json":
            summary_path = summary_path.with_suffix(".json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"mode": args.mode, "seed": args.seed, "results": hook_rows}
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"   summary_report={summary_path}")


if __name__ == "__main__":
    main()
