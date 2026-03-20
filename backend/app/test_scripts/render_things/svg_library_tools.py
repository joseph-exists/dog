"""
SVG Library Planning Utilities

Combinatorics planner, pairwise coverage, family quotas, and metadata builder.
Rendering is handled by tesserax_service.scripts.svg_compose — import from there
for any render/validate needs.
"""

from __future__ import annotations

import hashlib
import math
import random
import sys
from itertools import combinations, product
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Import render engine from Tesser
# ---------------------------------------------------------------------------

_TESSER_SRC = Path(__file__).resolve().parents[4] / "tesser" / "src"
if str(_TESSER_SRC) not in sys.path:
    sys.path.insert(0, str(_TESSER_SRC))

from tesserax_service.scripts.svg_compose import render_svg, validate_svg, _palette_for_params  # noqa: E402

# ---------------------------------------------------------------------------
# Domain definitions (authoritative source for planner)
# ---------------------------------------------------------------------------

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


def build_asset_metadata(row: dict[str, str], svg_markup: str) -> dict[str, Any]:
    """
    Create metadata payload aligned with the reference card.
    """
    colors = _palette_for_params(row)
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
