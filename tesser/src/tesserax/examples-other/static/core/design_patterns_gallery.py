#!/usr/bin/env python3
"""Curated design pattern gallery for integration-facing onboarding.

Recipes in this gallery are intentionally compact and parameterized so teams can
copy/adapt a known blueprint quickly.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Callable

from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Point,
    Rect,
    RenderConfig,
    Text,
    TimingSpec,
    ViewportSpec,
    ParameterSchema,
    ParameterSpec,
    render_batch,
)


RecipeBuilder = Callable[[int, int, random.Random], Canvas]
RECIPE_NAMES = ("state_chart", "timeline", "network")
PRESETS: dict[str, dict[str, object]] = {
    "balanced": {},
    "quickstart": {
        "layout.width": 1100,
        "layout.height": 640,
        "style.recipes": "state_chart,timeline",
        "motion.seed": 71,
    },
    "network_review": {
        "layout.width": 1360,
        "layout.height": 780,
        "style.recipes": "network",
        "motion.seed": 83,
    },
}


def build_gallery_parameter_schema() -> ParameterSchema:
    return ParameterSchema(
        [
            ParameterSpec("layout.width", 1280, stability="stable"),
            ParameterSpec("layout.height", 720, stability="stable"),
            ParameterSpec("style.recipes", "all", stability="stable"),
            ParameterSpec("motion.seed", 71, stability="stable"),
            ParameterSpec("export.format", "svg", allowed=("svg",), stability="stable"),
            ParameterSpec("export.output_prefix", "design_patterns_gallery", stability="stable"),
            ParameterSpec("export.report_dir", "", stability="stable"),
            ParameterSpec("export.summary_report", "", stability="stable"),
        ]
    )


def parse_recipe_list(value: str) -> list[str]:
    raw = [v.strip() for v in value.split(",") if v.strip()]
    if not raw or (len(raw) == 1 and raw[0] == "all"):
        return list(RECIPE_NAMES)
    bad = [v for v in raw if v not in RECIPE_NAMES]
    if bad:
        allowed = ", ".join(RECIPE_NAMES)
        raise ValueError(f"Unsupported recipe(s): {', '.join(bad)}. Allowed: {allowed}")
    seen: set[str] = set()
    out: list[str] = []
    for item in raw:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _base_canvas(width: int, height: int, title: str, subtitle: str) -> Canvas:
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
    canvas.add(Text("Design Patterns Gallery", size=26, fill=Colors.DarkBlue).move_to(Point(width / 2, 52)))
    canvas.add(Text(title, size=18, fill=Colors.Black).move_to(Point(width / 2, 84)))
    canvas.add(Text(subtitle, size=12, fill=Colors.Gray).move_to(Point(width / 2, 108)))
    return canvas


def recipe_state_chart(width: int, height: int, rng: random.Random) -> Canvas:
    del rng
    canvas = _base_canvas(
        width,
        height,
        "Recipe: State Chart",
        "Finite states with guarded transitions and completion path",
    )

    states = {
        "Idle": Point(260, 240),
        "Validate": Point(520, 240),
        "Execute": Point(780, 240),
        "Retry": Point(650, 410),
        "Done": Point(980, 240),
    }

    for name, center in states.items():
        fill = Colors.Honeydew if name in {"Done", "Idle"} else Colors.LightCyan
        if name == "Retry":
            fill = Colors.MistyRose
        canvas.add(Circle(r=52, fill=fill, stroke=Colors.DarkBlue.transparent(0.75), width=1.8).move_to(center))
        canvas.add(Text(name, size=12, fill=Colors.Black).move_to(center))

    def link(a: str, b: str, label: str, dy: float = 0.0) -> None:
        p1 = states[a].d(54, dy)
        p2 = states[b].d(-54, dy)
        canvas.add(Arrow(p1=p1, p2=p2, stroke=Colors.SlateBlue, width=1.5))
        canvas.add(Text(label, size=10, fill=Colors.DarkGray).move_to((p1 + p2) / 2).translated(0, -16))

    link("Idle", "Validate", "event:start")
    link("Validate", "Execute", "guard:valid")
    link("Execute", "Done", "event:success")
    canvas.add(
        Arrow(
            p1=states["Execute"].d(-15, 54),
            p2=states["Retry"].d(20, -54),
            stroke=Colors.Crimson,
            width=1.5,
        )
    )
    canvas.add(Text("event:error", size=10, fill=Colors.DarkGray).move_to(Point(730, 322)))
    canvas.add(
        Arrow(
            p1=states["Retry"].d(-22, -54),
            p2=states["Validate"].d(26, 54),
            stroke=Colors.Crimson,
            width=1.5,
        )
    )
    canvas.add(Text("event:retry", size=10, fill=Colors.DarkGray).move_to(Point(590, 336)))
    return canvas


def recipe_timeline(width: int, height: int, rng: random.Random) -> Canvas:
    del rng
    canvas = _base_canvas(
        width,
        height,
        "Recipe: Timeline",
        "Milestones, phase bands, and event callouts in one compact view",
    )

    y = 310
    x0, x1 = 140, width - 140
    canvas.add(Arrow(p1=Point(x0, y), p2=Point(x1, y), stroke=Colors.DarkGray, width=2.0, marker_end=None))

    phases = [
        ("Discovery", 160, 330, Colors.LightYellow),
        ("Build", 330, 610, Colors.LightCyan),
        ("Verify", 610, 860, Colors.Honeydew),
        ("Launch", 860, 1120, Colors.MistyRose),
    ]
    for name, px0, px1, fill in phases:
        band = Rect(
            w=px1 - px0,
            h=72,
            fill=fill.transparent(0.85),
            stroke=Colors.Gray.transparent(0.45),
            width=0.8,
        ).move_to(Point((px0 + px1) / 2, y + 76))
        canvas.add(band)
        canvas.add(Text(name, size=11, fill=Colors.DarkGray).move_to(Point((px0 + px1) / 2, y + 76)))

    milestones = [
        ("Kickoff", 190, -1),
        ("Spec Freeze", 420, 1),
        ("Beta", 700, -1),
        ("GA", 1030, 1),
    ]
    for label, x, direction in milestones:
        canvas.add(Circle(r=8, fill=Colors.DarkBlue, stroke=Colors.White, width=1.2).move_to(Point(x, y)))
        stem_y = y + direction * 86
        canvas.add(Arrow(p1=Point(x, y), p2=Point(x, stem_y), stroke=Colors.DarkBlue, width=1.0, marker_end=None))
        canvas.add(Text(label, size=11, fill=Colors.Black).move_to(Point(x, stem_y + direction * 18)))
    return canvas


def recipe_network(width: int, height: int, rng: random.Random) -> Canvas:
    canvas = _base_canvas(
        width,
        height,
        "Recipe: Network Diagnostics Panel",
        "Service nodes, risk links, and compact score overlays",
    )

    nodes = {
        "Ingress": Point(220, 230),
        "Auth": Point(430, 180),
        "Catalog": Point(430, 290),
        "Cart": Point(640, 180),
        "Checkout": Point(640, 290),
        "Payments": Point(860, 230),
        "Warehouse": Point(1030, 290),
    }

    for name, p in nodes.items():
        risk = rng.uniform(0.08, 0.72)
        fill = Colors.LightCyan if risk < 0.35 else Colors.MistyRose
        card = Rect(w=126, h=56, fill=fill, stroke=Colors.DarkGray.transparent(0.7), width=1.2).move_to(p)
        canvas.add(card)
        canvas.add(Text(name, size=11, fill=Colors.Black).move_to(p.dy(-10)))
        canvas.add(Text(f"risk={risk:.2f}", size=9, fill=Colors.DarkGray).move_to(p.dy(12)))

    links = [
        ("Ingress", "Auth"),
        ("Ingress", "Catalog"),
        ("Auth", "Cart"),
        ("Catalog", "Cart"),
        ("Catalog", "Checkout"),
        ("Cart", "Payments"),
        ("Checkout", "Payments"),
        ("Payments", "Warehouse"),
    ]
    for a, b in links:
        p1 = nodes[a].d(64, 0)
        p2 = nodes[b].d(-64, 0)
        if p2.x < p1.x:
            p1 = nodes[a].d(0, 28)
            p2 = nodes[b].d(0, -28)
        severity = rng.uniform(0.1, 1.0)
        color = Colors.Crimson.transparent(0.25 + 0.45 * severity)
        canvas.add(Arrow(p1=p1, p2=p2, stroke=color, width=1.0 + severity * 1.6, marker_end=None))

    panel = Rect(
        w=300,
        h=180,
        fill=Colors.White.transparent(0.94),
        stroke=Colors.DarkGray.transparent(0.65),
        width=1.1,
    ).move_to(Point(width - 190, 250))
    canvas.add(panel)
    canvas.add(Text("Diagnostics", size=13, fill=Colors.Black).move_to(Point(width - 190, 182)))
    canvas.add(Text("error_rate=0.037", size=11, fill=Colors.DarkRed).move_to(Point(width - 250, 220)))
    canvas.add(Text("p95_ms=184", size=11, fill=Colors.DarkBlue).move_to(Point(width - 250, 246)))
    canvas.add(Text("queue_depth=43", size=11, fill=Colors.DarkGreen).move_to(Point(width - 250, 272)))
    canvas.add(Text("blast_radius=3", size=11, fill=Colors.DarkGray).move_to(Point(width - 250, 298)))
    return canvas


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Curated design patterns gallery (state chart, timeline, network).")
    p.add_argument(
        "--preset",
        choices=tuple(PRESETS.keys()),
        default="balanced",
        help="Starter profile. Expert flags below override preset values.",
    )
    p.add_argument("--recipes", type=str, default=None, help="Comma list from: state_chart,timeline,network or 'all'.")
    p.add_argument("--seed", type=int, default=None, help="Seed for deterministic recipe details.")
    p.add_argument("--width", type=int, default=None, help="Canvas width.")
    p.add_argument("--height", type=int, default=None, help="Canvas height.")
    p.add_argument("--format", choices=["svg"], default=None, help="Output format.")
    p.add_argument("--output-prefix", type=str, default=None, help="Output file prefix.")
    p.add_argument("--report-dir", type=str, default=None, help="Optional directory for per-recipe render JSON reports.")
    p.add_argument(
        "--summary-report",
        type=str,
        default=None,
        help="Optional aggregate render summary JSON path (populated via report_hook).",
    )
    return p.parse_args()


def _resolve_params(args: argparse.Namespace, schema: ParameterSchema) -> dict[str, object]:
    resolved = {k: spec.default for k, spec in schema.specs.items()}
    preset = PRESETS.get(args.preset, {})
    for key, value in preset.items():
        resolved[str(key)] = value

    overrides = {
        "layout.width": args.width,
        "layout.height": args.height,
        "style.recipes": args.recipes,
        "motion.seed": args.seed,
        "export.format": args.format,
        "export.output_prefix": args.output_prefix,
        "export.report_dir": args.report_dir,
        "export.summary_report": args.summary_report,
    }
    for key, value in overrides.items():
        if value is not None:
            resolved[key] = value
    return schema.validate(resolved)


def main() -> None:
    args = parse_args()
    schema = build_gallery_parameter_schema()
    params = _resolve_params(args, schema)

    recipes = parse_recipe_list(str(params["style.recipes"]))
    rng = random.Random(int(params["motion.seed"]))
    width = max(640, int(params["layout.width"]))
    height = max(400, int(params["layout.height"]))

    builders: dict[str, RecipeBuilder] = {
        "state_chart": recipe_state_chart,
        "timeline": recipe_timeline,
        "network": recipe_network,
    }

    hook_rows: list[dict[str, str]] = []

    batch: list[tuple[Canvas, RenderConfig]] = []
    output_prefix = str(params["export.output_prefix"])
    report_dir = str(params["export.report_dir"])
    for name in recipes:
        canvas = builders[name](width, height, rng)
        report_path = ""
        if report_dir:
            report_path = str(Path(report_dir) / f"{name}.json")

        def make_hook(recipe_name: str):
            def _hook(result) -> None:
                hook_rows.append(
                    {
                        "recipe": recipe_name,
                        "output_path": str(result.output_path),
                        "format": result.format,
                        "config_fingerprint": str(
                            result.metadata.get("config_fingerprint", "")
                        ),
                    }
                )

            return _hook

        batch.append(
            (
                canvas,
                RenderConfig(
                    output_path=f"{output_prefix}_{name}",
                    format=str(params["export.format"]),
                    viewport=ViewportSpec(fit_padding=20, fit_crop=False),
                    timing=TimingSpec(seed=int(params["motion.seed"])),
                    metadata={"recipe": name, "gallery": "design_patterns"},
                    report_json_path=report_path or None,
                    report_hook=make_hook(name),
                ),
            )
        )

    results = render_batch(batch)
    for r in results:
        print(f"✅ Saved: {r.output_path}")
        if r.report_path:
            print(f"   report_json={r.report_path}")

    if params["export.summary_report"]:
        summary_path = Path(str(params["export.summary_report"]))
        if summary_path.suffix.lower() != ".json":
            summary_path = summary_path.with_suffix(".json")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "preset": args.preset,
            "seed": int(params["motion.seed"]),
            "recipes": recipes,
            "results": hook_rows,
            "resolved_params": params,
            "parameter_schema_keys": sorted(schema.specs.keys()),
        }
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"   summary_report={summary_path}")


if __name__ == "__main__":
    main()
