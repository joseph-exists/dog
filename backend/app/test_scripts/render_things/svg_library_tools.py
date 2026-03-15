"""
SVG Library Planning + Rendering Utilities

Implements a practical subset of the combinatorics strategy from
`svg_combinatorics_reference_card.md`:
1. Pairwise planning for core knobs
2. Family quotas
3. Additional hero/safe tiers
4. Deterministic rendering and validation helpers
"""

from __future__ import annotations

import hashlib
import math
import random
from itertools import combinations, product
from typing import Any

STYLE_FAMILIES = [
    "organic",
    "geometric",
    "glitch",
    "minimal",
    "atmospheric",
    "diagrammatic",
]

FAMILY_QUOTAS: dict[str, float] = {
    "organic": 0.18,
    "geometric": 0.18,
    "glitch": 0.14,
    "minimal": 0.16,
    "atmospheric": 0.18,
    "diagrammatic": 0.16,
}

PAIRWISE_DOMAINS: dict[str, list[str]] = {
    "shape_family": ["curves", "polygons", "rings", "stripes", "particles"],
    "layer_count": ["1", "2", "4", "6"],
    "density": ["sparse", "medium", "dense"],
    "symmetry": ["none", "radial", "mirror-x", "mirror-y"],
    "viewbox": ["square(1024)", "landscape(1366x768)", "portrait(768x1366)"],
    "turbulence_type": ["fractalNoise", "turbulence"],
    "base_frequency": ["0.003", "0.01", "0.03", "0.08"],
    "num_octaves": ["1", "2", "4", "6"],
    "seed_bucket": ["0-99", "100-999", "1000-9999"],
    "stitch_tiles": ["stitch", "noStitch"],
    "displacement_scale": ["0", "8", "24", "64", "120"],
    "channel_x": ["R", "G", "B", "A"],
    "channel_y": ["R", "G", "B", "A"],
    "distortion_scope": ["background-only", "subject-only", "global"],
    "gaussian_blur": ["0", "0.8", "2", "6", "14"],
    "morphology": ["none", "erode(1)", "dilate(1)", "dilate(3)"],
    "drop_shadow": ["off", "subtle", "strong"],
    "fuzz_mask": ["off", "low", "high"],
    "palette_family": ["warm", "cool", "duotone", "neon", "earth", "mono"],
    "palette_cardinality": ["1", "2", "4", "6"],
    "contrast_band": ["low", "mid", "high"],
    "saturation_band": ["desat", "balanced", "vivid"],
    "luminance_bias": ["dark", "balanced", "light"],
    "blend_mode_primary": ["normal", "multiply", "screen", "overlay", "darken", "lighten"],
    "blend_mode_secondary": ["none", "multiply", "screen", "overlay"],
    "opacity_stack": ["flat(1.0)", "stepped(1/0.7/0.4)", "mist(0.15-0.55)"],
    "composite_op": ["over", "in", "out", "atop", "xor"],
    "directionality": ["none", "horizontal", "vertical", "diagonal", "radial"],
    "frequency_jitter": ["none", "low", "high"],
    "phase_offset": ["0", "0.25", "0.5", "0.75"],
}

PALETTE_BY_FAMILY: dict[str, list[str]] = {
    "organic": ["#6BA292", "#82BFA0", "#4E7A63", "#D8E2C9", "#244739", "#90B77D"],
    "geometric": ["#1E293B", "#334155", "#64748B", "#CBD5E1", "#0F172A", "#38BDF8"],
    "glitch": ["#0B0F1A", "#00E5FF", "#FF006E", "#FFE600", "#7C3AED", "#12F7B6"],
    "minimal": ["#111827", "#374151", "#6B7280", "#9CA3AF", "#D1D5DB", "#F3F4F6"],
    "atmospheric": ["#1A2A6C", "#3F4C6B", "#4B79A1", "#7F7FD5", "#B993D6", "#E0EAFC"],
    "diagrammatic": ["#0F172A", "#1D4ED8", "#2563EB", "#3B82F6", "#93C5FD", "#E2E8F0"],
}


def _hash_to_int(value: str) -> int:
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:12], 16)


def stable_seed(master_seed: int, scenario_id: str) -> int:
    """Generate deterministic per-scenario seed."""
    return _hash_to_int(f"{master_seed}:{scenario_id}")


def _compute_pair_space(domains: dict[str, list[str]]) -> set[tuple[str, str, str, str]]:
    keys = list(domains.keys())
    required: set[tuple[str, str, str, str]] = set()
    for k1, k2 in combinations(keys, 2):
        for v1, v2 in product(domains[k1], domains[k2]):
            required.add((k1, str(v1), k2, str(v2)))
    return required


def _pairs_for_row(row: dict[str, str], keys: list[str]) -> set[tuple[str, str, str, str]]:
    out: set[tuple[str, str, str, str]] = set()
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            k1, k2 = keys[i], keys[j]
            out.add((k1, str(row[k1]), k2, str(row[k2])))
    return out


def _random_row(rng: random.Random, domains: dict[str, list[str]]) -> dict[str, str]:
    return {k: str(rng.choice(v)) for k, v in domains.items()}


def _apply_family_bias(
    row: dict[str, str],
    family: str,
    rng: random.Random,
) -> dict[str, str]:
    """Inject mild family-specific defaults to keep visual language legible."""
    out = dict(row)
    if family == "organic":
        out["shape_family"] = "curves"
        out["palette_family"] = rng.choice(["earth", "cool"])
        out["symmetry"] = rng.choice(["none", "radial"])
    elif family == "geometric":
        out["shape_family"] = rng.choice(["polygons", "rings", "stripes"])
        out["symmetry"] = rng.choice(["radial", "mirror-x", "mirror-y"])
    elif family == "glitch":
        out["palette_family"] = "neon"
        out["distortion_scope"] = "global"
        out["displacement_scale"] = rng.choice(["24", "64", "120"])
    elif family == "minimal":
        out["density"] = "sparse"
        out["gaussian_blur"] = rng.choice(["0", "0.8"])
        out["palette_family"] = "mono"
    elif family == "atmospheric":
        out["shape_family"] = rng.choice(["curves", "particles"])
        out["base_frequency"] = rng.choice(["0.003", "0.01"])
        out["blend_mode_primary"] = rng.choice(["screen", "overlay"])
    elif family == "diagrammatic":
        out["shape_family"] = rng.choice(["stripes", "rings", "polygons"])
        out["contrast_band"] = "high"
        out["blend_mode_primary"] = rng.choice(["normal", "multiply"])
    out["style_family"] = family
    return out


def _allocate_family_targets(total: int) -> dict[str, int]:
    exact = {k: total * v for k, v in FAMILY_QUOTAS.items()}
    base = {k: int(math.floor(v)) for k, v in exact.items()}
    remainder = total - sum(base.values())
    order = sorted(STYLE_FAMILIES, key=lambda k: exact[k] - base[k], reverse=True)
    for family in order[:remainder]:
        base[family] += 1
    return base


def build_pairwise_rows(
    *,
    count: int,
    seed: int,
    candidate_pool: int = 240,
) -> tuple[list[dict[str, str]], float]:
    """
    Build pairwise-ish rows with greedy random search.

    Returns:
      rows, pairwise_coverage_pct
    """
    rng = random.Random(seed)
    keys = list(PAIRWISE_DOMAINS.keys())
    required = _compute_pair_space(PAIRWISE_DOMAINS)
    uncovered = set(required)
    rows: list[dict[str, str]] = []
    seen: set[tuple[tuple[str, str], ...]] = set()

    family_targets = _allocate_family_targets(count)
    families: list[str] = []
    for family, qty in family_targets.items():
        families.extend([family] * qty)
    rng.shuffle(families)

    for idx in range(count):
        family = families[idx % len(families)] if families else rng.choice(STYLE_FAMILIES)
        best_row: dict[str, str] | None = None
        best_coverage = -1
        for _ in range(candidate_pool):
            trial = _apply_family_bias(_random_row(rng, PAIRWISE_DOMAINS), family, rng)
            token = tuple(sorted(trial.items()))
            if token in seen:
                continue
            trial_pairs = _pairs_for_row(trial, keys)
            coverage = len(trial_pairs.intersection(uncovered))
            if coverage > best_coverage:
                best_row = trial
                best_coverage = coverage
                if coverage >= len(keys):  # good-enough early exit
                    break
        if best_row is None:
            best_row = _apply_family_bias(_random_row(rng, PAIRWISE_DOMAINS), family, rng)
        seen.add(tuple(sorted(best_row.items())))
        rows.append(best_row)
        uncovered -= _pairs_for_row(best_row, keys)

    coverage_pct = 100.0 * (1.0 - (len(uncovered) / max(1, len(required))))
    return rows, coverage_pct


def _hero_override(rng: random.Random, family: str) -> dict[str, str]:
    base: dict[str, str] = {
        "density": "dense",
        "layer_count": "6",
        "displacement_scale": rng.choice(["64", "120"]),
        "gaussian_blur": rng.choice(["6", "14"]),
        "contrast_band": "high",
        "saturation_band": "vivid",
        "palette_cardinality": "6",
        "opacity_stack": "mist(0.15-0.55)",
    }
    if family == "minimal":
        base["density"] = "medium"
        base["gaussian_blur"] = "0.8"
        base["palette_cardinality"] = "2"
    if family == "diagrammatic":
        base["shape_family"] = "stripes"
        base["gaussian_blur"] = "0"
    return base


def _safe_override(rng: random.Random, family: str) -> dict[str, str]:
    return {
        "shape_family": rng.choice(["stripes", "rings", "curves"]),
        "density": "sparse",
        "layer_count": rng.choice(["1", "2"]),
        "displacement_scale": "0",
        "gaussian_blur": rng.choice(["0", "0.8"]),
        "palette_cardinality": rng.choice(["1", "2"]),
        "contrast_band": "mid",
        "opacity_stack": "flat(1.0)",
        "style_family": family,
    }


def build_generation_plan(
    *,
    total_count: int,
    seed: int,
    pairwise_ratio: float = 0.70,
    hero_ratio: float = 0.20,
) -> dict[str, Any]:
    """
    Build a complete generation plan with pairwise/hero/safe tiers.
    """
    if total_count <= 0:
        raise ValueError("total_count must be > 0")

    pairwise_count = max(1, int(total_count * pairwise_ratio))
    hero_count = max(0, int(total_count * hero_ratio))
    safe_count = max(0, total_count - pairwise_count - hero_count)

    rng = random.Random(seed)
    pairwise_rows, coverage = build_pairwise_rows(count=pairwise_count, seed=seed)
    rows: list[dict[str, str]] = []

    for row in pairwise_rows:
        row2 = dict(row)
        row2["generation_tier"] = "pairwise-core"
        rows.append(row2)

    for _ in range(hero_count):
        family = rng.choice(STYLE_FAMILIES)
        row = _apply_family_bias(_random_row(rng, PAIRWISE_DOMAINS), family, rng)
        row.update(_hero_override(rng, family))
        row["generation_tier"] = "hero-extreme"
        rows.append(row)

    for _ in range(safe_count):
        family = rng.choice(["minimal", "diagrammatic", "geometric"])
        row = _apply_family_bias(_random_row(rng, PAIRWISE_DOMAINS), family, rng)
        row.update(_safe_override(rng, family))
        row["generation_tier"] = "safe-utility"
        rows.append(row)

    for i, row in enumerate(rows):
        row["scenario_id"] = f"svg-scenario-{i + 1:06d}"
        row["scenario_seed"] = stable_seed(seed, row["scenario_id"])

    return {
        "meta": {
            "seed": seed,
            "total_count": total_count,
            "pairwise_count": pairwise_count,
            "hero_count": hero_count,
            "safe_count": safe_count,
            "pairwise_coverage_pct": round(coverage, 3),
            "reference": "app/test_scripts/render_things/svg_combinatorics_reference_card.md",
        },
        "rows": rows,
    }


def _parse_viewbox(value: str) -> tuple[int, int]:
    if value == "square(1024)":
        return 1024, 1024
    if value == "landscape(1366x768)":
        return 1366, 768
    if value == "portrait(768x1366)":
        return 768, 1366
    return 1024, 1024


def _palette_for_row(row: dict[str, str]) -> list[str]:
    family = row.get("style_family", "geometric")
    base = list(PALETTE_BY_FAMILY.get(family, PALETTE_BY_FAMILY["geometric"]))
    cardinality = max(1, int(float(row.get("palette_cardinality", "4"))))
    if cardinality <= len(base):
        return base[:cardinality]
    out = list(base)
    while len(out) < cardinality:
        out.extend(base)
    return out[:cardinality]


def _opacity_sequence(kind: str, n: int) -> list[float]:
    if n <= 0:
        return []
    if kind == "flat(1.0)":
        return [1.0 for _ in range(n)]
    if kind == "stepped(1/0.7/0.4)":
        base = [1.0, 0.7, 0.4]
        return [base[i % len(base)] for i in range(n)]
    if kind == "mist(0.15-0.55)":
        if n == 1:
            return [0.55]
        return [0.55 - (0.40 * (i / (n - 1))) for i in range(n)]
    return [1.0 for _ in range(n)]


def _build_filter(row: dict[str, str], filter_id: str) -> tuple[str, int]:
    primitives: list[str] = []
    turb_type = row.get("turbulence_type", "fractalNoise")
    base_frequency = row.get("base_frequency", "0.01")
    octaves = row.get("num_octaves", "2")
    seed_bucket = row.get("seed_bucket", "0-99")
    if seed_bucket == "0-99":
        seed = "37"
    elif seed_bucket == "100-999":
        seed = "421"
    else:
        seed = "1337"
    stitch = "stitch" if row.get("stitch_tiles") == "stitch" else "noStitch"
    primitives.append(
        (
            f'<feTurbulence type="{turb_type}" baseFrequency="{base_frequency}" '
            f'numOctaves="{octaves}" seed="{seed}" stitchTiles="{stitch}" result="noise"/>'
        )
    )
    disp = float(row.get("displacement_scale", "0"))
    if disp > 0:
        cx = row.get("channel_x", "R")
        cy = row.get("channel_y", "G")
        primitives.append(
            (
                f'<feDisplacementMap in="SourceGraphic" in2="noise" scale="{disp}" '
                f'xChannelSelector="{cx}" yChannelSelector="{cy}" result="distorted"/>'
            )
        )
    blur = float(row.get("gaussian_blur", "0"))
    if blur > 0:
        stddev = min(blur, 14.0)
        blur_input = "distorted" if disp > 0 else "SourceGraphic"
        primitives.append(
            f'<feGaussianBlur in="{blur_input}" stdDeviation="{stddev}" result="blurred"/>'
        )
    if row.get("drop_shadow") in {"subtle", "strong"}:
        shadow_std = "2.5" if row.get("drop_shadow") == "subtle" else "6.0"
        primitives.append(
            (
                '<feDropShadow dx="0" dy="2" '
                f'stdDeviation="{shadow_std}" flood-opacity="0.28" />'
            )
        )
    body = "\n      ".join(primitives)
    return f'<filter id="{filter_id}">\n      {body}\n    </filter>', len(primitives)


def render_svg(row: dict[str, str]) -> str:
    """
    Render deterministic SVG markup for one scenario row.
    """
    seed = int(row.get("scenario_seed", 0))
    rng = random.Random(seed)
    width, height = _parse_viewbox(row.get("viewbox", "square(1024)"))
    layers = int(float(row.get("layer_count", "2")))
    density = row.get("density", "medium")
    shape_family = row.get("shape_family", "curves")
    symmetry = row.get("symmetry", "none")
    blend_primary = row.get("blend_mode_primary", "normal")
    opacities = _opacity_sequence(row.get("opacity_stack", "flat(1.0)"), layers)
    palette = _palette_for_row(row)

    density_scale = {"sparse": 6, "medium": 14, "dense": 26}.get(density, 14)
    elements_per_layer = max(3, density_scale)

    filter_id = f"f-{row.get('scenario_id', 'svg')[-8:]}"
    filter_markup, filter_primitives = _build_filter(row, filter_id)
    distortion_scope = row.get("distortion_scope", "global")

    defs = [
        "<defs>",
        (
            f'    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="{palette[0]}"/>'
            f'<stop offset="100%" stop-color="{palette[-1]}"/>'
            "</linearGradient>"
        ),
        f"    {filter_markup}",
        "</defs>",
    ]

    content: list[str] = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{row.get("scenario_id", "svg")}">'
        ),
        *defs,
    ]

    bg_filter = f' filter="url(#{filter_id})"' if distortion_scope in {"background-only", "global"} else ""
    content.append(
        f'  <rect x="0" y="0" width="{width}" height="{height}" fill="url(#bg-grad)"{bg_filter}/>'
    )

    for li in range(layers):
        opacity = opacities[li] if li < len(opacities) else 1.0
        color = palette[li % len(palette)]
        transform = ""
        if row.get("directionality") == "diagonal":
            transform = f' transform="rotate({12 + li * 7} {width // 2} {height // 2})"'
        if row.get("directionality") == "radial":
            transform = f' transform="rotate({li * 19} {width // 2} {height // 2})"'

        layer_filter = ""
        if distortion_scope == "subject-only":
            layer_filter = f' filter="url(#{filter_id})"'

        content.append(
            f'  <g opacity="{opacity:.3f}" style="mix-blend-mode:{blend_primary}"{transform}{layer_filter}>'
        )

        for i in range(elements_per_layer):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            w = rng.randint(max(8, width // 32), max(16, width // 6))
            h = rng.randint(max(8, height // 32), max(16, height // 6))
            c = palette[(li + i) % len(palette)]
            stroke = palette[(li + i + 1) % len(palette)]

            if shape_family == "stripes":
                if row.get("directionality") in {"vertical", "radial"}:
                    content.append(
                        f'    <rect x="{x}" y="0" width="{max(2, w // 8)}" height="{height}" '
                        f'fill="{c}" fill-opacity="0.28"/>'
                    )
                else:
                    content.append(
                        f'    <rect x="0" y="{y}" width="{width}" height="{max(2, h // 9)}" '
                        f'fill="{c}" fill-opacity="0.26"/>'
                    )
            elif shape_family == "rings":
                r = max(6, min(w, h) // 2)
                content.append(
                    f'    <circle cx="{x}" cy="{y}" r="{r}" fill="none" stroke="{stroke}" stroke-width="2.2" />'
                )
            elif shape_family == "particles":
                r = max(1, min(w, h) // 12)
                content.append(
                    f'    <circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity="0.7" />'
                )
            elif shape_family == "polygons":
                points = [
                    f"{x},{y}",
                    f"{min(width, x + w)},{y}",
                    f"{min(width, x + (w // 2))},{min(height, y + h)}",
                ]
                content.append(
                    f'    <polygon points="{" ".join(points)}" fill="{c}" fill-opacity="0.24" '
                    f'stroke="{stroke}" stroke-width="1.2"/>'
                )
            else:  # curves
                x2 = min(width, x + w)
                y2 = min(height, y + h)
                cx = min(width, x + (w // 2))
                cy = max(0, y - (h // 3))
                content.append(
                    f'    <path d="M {x} {y} Q {cx} {cy}, {x2} {y2}" '
                    f'stroke="{stroke}" stroke-width="2" fill="none" />'
                )

            if symmetry == "mirror-x":
                mx = max(0, width - x)
                content.append(
                    f'    <circle cx="{mx}" cy="{y}" r="{max(2, min(w, h) // 16)}" fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "mirror-y":
                my = max(0, height - y)
                content.append(
                    f'    <circle cx="{x}" cy="{my}" r="{max(2, min(w, h) // 16)}" fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "radial":
                rx = width - x
                ry = height - y
                content.append(
                    f'    <circle cx="{rx}" cy="{ry}" r="{max(2, min(w, h) // 18)}" fill="{stroke}" fill-opacity="0.18"/>'
                )

        content.append("  </g>")

    content.append("</svg>")
    svg = "\n".join(content)

    # Keep constraints practical for API payloads.
    if len(svg.encode("utf-8")) > 240_000:
        svg = svg[:220_000] + "\n</svg>"
    if filter_primitives > 12:
        svg = svg.replace(f' filter="url(#{filter_id})"', "")
    return svg


def validate_svg(svg_markup: str) -> list[str]:
    """
    Check compatibility/safety constraints and return validation errors.
    """
    errors: list[str] = []
    lower = svg_markup.lower()
    if "<svg" not in lower or "</svg>" not in lower:
        errors.append("missing-svg-root")
    if "viewbox=" not in lower:
        errors.append("missing-viewbox")
    for token in ("<script", "onload=", "onerror=", "<foreignobject", "xlink:href=\"http"):
        if token in lower:
            errors.append(f"forbidden-token:{token}")
    if len(svg_markup.encode("utf-8")) > 250_000:
        errors.append("exceeds-hard-size-cap")
    element_count = svg_markup.count("<") - svg_markup.count("</svg>")
    if element_count > 2000:
        errors.append("element-cap-exceeded")
    return errors


def build_asset_metadata(row: dict[str, str], svg_markup: str) -> dict[str, Any]:
    """
    Create metadata payload aligned with the reference card.
    """
    colors = _palette_for_row(row)
    has_turbulence = "<feturbulence" in svg_markup.lower()
    has_displacement = "<fedisplacementmap" in svg_markup.lower()
    element_count = max(0, svg_markup.count("<") - svg_markup.count("</svg>"))
    filter_count = svg_markup.lower().count("<fe")
    contrast_lookup = {"low": 0.28, "mid": 0.56, "high": 0.84}
    complexity = min(
        1.0,
        (
            (int(float(row.get("layer_count", "2"))) * 0.10)
            + ({"sparse": 0.12, "medium": 0.26, "dense": 0.42}[row.get("density", "medium")])
            + (0.18 if has_displacement else 0.0)
            + (0.12 if float(row.get("gaussian_blur", "0")) > 2.0 else 0.0)
        ),
    )
    return {
        "asset_id": row.get("scenario_id"),
        "scenario_id": row.get("scenario_id"),
        "seed": row.get("scenario_seed"),
        "family": row.get("style_family"),
        "generation_tier": row.get("generation_tier"),
        "knobs": {k: v for k, v in row.items() if k not in {"scenario_id", "scenario_seed"}},
        "bytes": len(svg_markup.encode("utf-8")),
        "element_count": element_count,
        "filter_count": filter_count,
        "has_turbulence": has_turbulence,
        "has_displacement": has_displacement,
        "dominant_colors": colors,
        "contrast_score": contrast_lookup.get(row.get("contrast_band", "mid"), 0.56),
        "complexity_score": round(complexity, 3),
    }

