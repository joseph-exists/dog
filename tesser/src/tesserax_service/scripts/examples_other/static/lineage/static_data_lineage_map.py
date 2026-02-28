#!/usr/bin/env python3
"""Static data lineage risk map scaffold for Tesserax.

Pattern alignment:
- scenario/policy/report-json CLI
- deterministic topology + model pass for comparability
- notation and legend embedded inside output SVG
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path

from tesserax import (
    Arrow,
    Canvas,
    Circle,
    Colors,
    Point,
    Rect,
    RenderConfig,
    Text,
    render_scene,
)
from tesserax.layout import ForceLayout


@dataclass
class NodeSpec:
    role: str
    criticality: float
    base_freshness: float


@dataclass
class ScenarioPreset:
    stressed_nodes: tuple[str, ...]
    corruption_injection: float
    freshness_decay: float
    schema_drift: float


@dataclass
class PolicyPreset:
    validation_gain: float
    quarantine_gain: float
    backfill_gain: float


NODE_SPECS = {
    "CRM": NodeSpec("source", 0.70, 0.86),
    "ERP": NodeSpec("source", 0.74, 0.84),
    "WEB": NodeSpec("source", 0.58, 0.88),
    "RAW": NodeSpec("lake", 0.78, 0.82),
    "STAGE": NodeSpec("transform", 0.84, 0.78),
    "DIM": NodeSpec("transform", 0.90, 0.76),
    "FACT": NodeSpec("transform", 0.95, 0.74),
    "MART": NodeSpec("serve", 1.00, 0.72),
    "DASH": NodeSpec("serve", 0.68, 0.76),
    "ML": NodeSpec("serve", 0.72, 0.70),
}

EDGES = [
    ("CRM", "RAW"),
    ("ERP", "RAW"),
    ("WEB", "RAW"),
    ("RAW", "STAGE"),
    ("STAGE", "DIM"),
    ("STAGE", "FACT"),
    ("DIM", "MART"),
    ("FACT", "MART"),
    ("MART", "DASH"),
    ("MART", "ML"),
]

SCENARIOS = {
    "late_arrivals": ScenarioPreset(("RAW", "STAGE"), 0.22, 0.18, 0.08),
    "schema_break": ScenarioPreset(("STAGE", "DIM", "FACT"), 0.35, 0.12, 0.24),
    "source_corruption": ScenarioPreset(("CRM", "ERP"), 0.46, 0.10, 0.18),
    "upstream_outage": ScenarioPreset(("WEB", "RAW", "STAGE"), 0.28, 0.26, 0.10),
}

POLICIES = {
    "strict": PolicyPreset(1.18, 1.10, 0.92),
    "balanced": PolicyPreset(1.00, 1.00, 1.00),
    "fast": PolicyPreset(0.78, 0.72, 0.86),
}


def clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Static data lineage risk map scaffold.")
    p.add_argument("--seed", type=int, default=227)
    p.add_argument("--scenario", choices=sorted(SCENARIOS.keys()), default="late_arrivals")
    p.add_argument("--policy", choices=sorted(POLICIES.keys()), default="balanced")

    p.add_argument("--corruption-injection", type=float, default=None)
    p.add_argument("--freshness-decay", type=float, default=None)
    p.add_argument("--schema-drift", type=float, default=None)

    p.add_argument("--world-width", type=int, default=2200)
    p.add_argument("--world-height", type=int, default=1400)
    p.add_argument("--layout-iterations", type=int, default=220)

    p.add_argument("--format", choices=["svg"], default="svg")
    p.add_argument("--report-json", type=str, default="")
    p.add_argument("--output", type=str, default="data_lineage_map.svg")
    return p.parse_args()


def choose(value: float | None, fallback: float) -> float:
    return fallback if value is None else value


def main() -> None:
    args = parse_args()
    rng = random.Random(args.seed)

    scenario = SCENARIOS[args.scenario]
    policy = POLICIES[args.policy]

    corruption_injection = choose(args.corruption_injection, scenario.corruption_injection)
    freshness_decay = choose(args.freshness_decay, scenario.freshness_decay)
    schema_drift = choose(args.schema_drift, scenario.schema_drift)

    canvas = Canvas(width=args.world_width, height=args.world_height)
    canvas.add(
        Rect(w=args.world_width, h=args.world_height, fill=Colors.White, stroke=Colors.Transparent, width=0.0)
        .move_to(Point(args.world_width / 2, args.world_height / 2))
    )
    canvas.add(Text("Static Data Lineage Map", size=34, fill=Colors.DarkBlue).move_to(Point(args.world_width / 2, 74)))
    canvas.add(
        Text(
            f"scenario={args.scenario} policy={args.policy} corruption={corruption_injection:.2f} drift={schema_drift:.2f}",
            size=12,
            fill=Colors.Gray,
        ).move_to(Point(args.world_width / 2, 102))
    )

    node_shapes: dict[str, Circle] = {}
    with ForceLayout(iterations=max(40, args.layout_iterations), diameter=760) as graph:
        for name, spec in NODE_SPECS.items():
            if spec.role == "source":
                fill = Colors.LightYellow
            elif spec.role in {"serve"}:
                fill = Colors.MistyRose
            elif spec.role in {"transform"}:
                fill = Colors.LightCyan
            else:
                fill = Colors.LightGreen
            node_shapes[name] = Circle(r=28, fill=fill, stroke=Colors.DarkBlue.transparent(0.72), width=1.2)

        for u, v in EDGES:
            graph.connect(node_shapes[u], node_shapes[v])
        graph.do_layout()

    for s in node_shapes.values():
        s.transform.tx += args.world_width * 0.44
        s.transform.ty += args.world_height * 0.52
    canvas.add(graph)

    freshness = {n: NODE_SPECS[n].base_freshness for n in NODE_SPECS}
    corruption = {n: 0.02 for n in NODE_SPECS}
    confidence = {n: 0.96 for n in NODE_SPECS}

    incoming: dict[str, list[str]] = {n: [] for n in NODE_SPECS}
    for u, v in EDGES:
        incoming[v].append(u)

    # Single deterministic inference pass chain to derive static risk scores.
    for _ in range(8):
        for n in NODE_SPECS:
            if n in scenario.stressed_nodes:
                corruption[n] += corruption_injection * 0.08
                freshness[n] -= freshness_decay * 0.06

            if incoming[n]:
                up_cor = sum(corruption[u] for u in incoming[n]) / len(incoming[n])
                up_fresh = sum(freshness[u] for u in incoming[n]) / len(incoming[n])
                corruption[n] += (up_cor + schema_drift * 0.12) * 0.12
                freshness[n] -= (1.0 - up_fresh) * 0.08

            # Policy impact: strict increases confidence by reducing corrupted flow acceptance.
            confidence[n] += policy.validation_gain * 0.012
            corruption[n] -= policy.quarantine_gain * 0.028
            freshness[n] += policy.backfill_gain * 0.014

            jitter = (rng.random() - 0.5) * 0.006
            corruption[n] = clamp(corruption[n] + jitter, 0.0, 1.0)
            freshness[n] = clamp(freshness[n], 0.0, 1.0)
            confidence[n] = clamp(confidence[n] - 0.55 * corruption[n] + 0.12 * freshness[n], 0.0, 1.0)

    edge_shapes: dict[tuple[str, str], Arrow] = {}
    for u, v in EDGES:
        p1 = node_shapes[u].anchor("center")
        p2 = node_shapes[v].anchor("center")
        risk_flow = clamp((corruption[u] + corruption[v]) / 2.0, 0.0, 1.0)
        width = 1.2 + 2.4 * risk_flow
        stroke = Colors.Crimson.transparent(0.30 + 0.40 * risk_flow)
        a = Arrow(p1=p1, p2=p2, stroke=stroke, width=width, marker_end=None)
        edge_shapes[(u, v)] = a
        canvas.add(a)

    node_halos: dict[str, Circle] = {}
    node_bars: dict[str, Rect] = {}
    for n, shape in node_shapes.items():
        c = shape.anchor("center")
        risk = clamp(corruption[n] + (1.0 - confidence[n]), 0.0, 1.0)
        deficit = clamp(1.0 - freshness[n], 0.0, 1.0)
        halo = Circle(r=34, fill=Colors.Transparent, stroke=Colors.Crimson.transparent(0.72), width=0.8 + 3.4 * risk).move_to(c)
        bar = Rect(w=11, h=42, fill=Colors.SeaGreen.transparent(0.60), stroke=Colors.DarkGray.transparent(0.40), width=0.8).move_to(Point(c.x + 66, c.y))
        bar.transform.sy = 0.28 + 1.25 * deficit

        node_halos[n] = halo
        node_bars[n] = bar
        canvas.add(halo, bar)
        canvas.add(Text(n, size=9, fill=Colors.Black).move_to(c))

    legend = Rect(w=520, h=300, fill=Colors.White.transparent(0.94), stroke=Colors.DarkGray.transparent(0.64), width=1.1).move_to(Point(args.world_width - 320, 320))
    canvas.add(legend)
    canvas.add(Text("Legend and Notation", size=14, fill=Colors.Black).move_to(Point(args.world_width - 320, 186)))
    lx = args.world_width - 560
    ly = 226
    canvas.add(Text("Halo width ~ lineage risk_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Bar scale ~ freshness deficit_i", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("Edge width/color ~ corruption flow", size=10, fill=Colors.Black, anchor="start").move_to(Point(lx, ly)))
    ly += 22
    canvas.add(Text("trust_i = clamp(confidence_i - corruption_i, 0, 1)", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))
    ly += 18
    canvas.add(Text("global_trust = mean(trust_i * criticality_i)", size=10, fill=Colors.DarkGray, anchor="start").move_to(Point(lx, ly)))

    trust = {
        n: clamp(confidence[n] - corruption[n], 0.0, 1.0)
        for n in NODE_SPECS
    }
    weighted = [trust[n] * NODE_SPECS[n].criticality for n in NODE_SPECS]
    global_trust = sum(weighted) / sum(NODE_SPECS[n].criticality for n in NODE_SPECS)
    lineage_risk = sum(clamp(corruption[n] + (1.0 - confidence[n]), 0.0, 1.0) * NODE_SPECS[n].criticality for n in NODE_SPECS) / sum(NODE_SPECS[n].criticality for n in NODE_SPECS)
    blast_radius = sum(1 for n in NODE_SPECS if clamp(corruption[n] + (1.0 - confidence[n]), 0.0, 1.0) >= 0.45)
    unresolved_alerts = sum(1 for n in NODE_SPECS if trust[n] < 0.55)

    canvas.add(Text(f"global_trust={global_trust:.3f}", size=12, fill=Colors.DarkBlue).move_to(Point(args.world_width - 320, 444)))
    canvas.add(Text(f"lineage_risk={lineage_risk:.3f}", size=12, fill=Colors.DarkRed).move_to(Point(args.world_width - 320, 468)))
    canvas.add(Text(f"blast_radius={blast_radius}  unresolved_alerts={unresolved_alerts}", size=12, fill=Colors.DarkGray).move_to(Point(args.world_width - 320, 492)))

    result = render_scene(
        canvas,
        RenderConfig(
            output_path=args.output,
            format=args.format,
            fit_padding=26,
            fit_crop=False,
        ),
    )

    print(f"✅ Saved: {result.output_path}")
    print(
        f"   scenario={args.scenario} policy={args.policy} global_trust={global_trust:.3f} "
        f"lineage_risk={lineage_risk:.3f} blast_radius={blast_radius} alerts={unresolved_alerts}"
    )

    if args.report_json:
        report = {
            "scenario": args.scenario,
            "policy": args.policy,
            "seed": args.seed,
            "format": args.format,
            "overrides": {
                "corruption_injection": corruption_injection,
                "freshness_decay": freshness_decay,
                "schema_drift": schema_drift,
                "stressed_nodes": list(scenario.stressed_nodes),
            },
            "metrics": {
                "global_trust": global_trust,
                "lineage_risk": lineage_risk,
                "blast_radius": blast_radius,
                "unresolved_alerts": unresolved_alerts,
            },
        }
        report_path = Path(args.report_json)
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"   report_json={report_path}")


if __name__ == "__main__":
    main()
