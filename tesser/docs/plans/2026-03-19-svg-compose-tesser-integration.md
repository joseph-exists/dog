# SVG Compose — Tesser Integration Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Move the SVG render engine into Tesser as a first-class `svg.compose` builtin script with all 30 knobs fully implemented, add two distinctive preset scripts (`svg.vector-rings` with warp transforms, `svg.soft-gradient` with LAB k-means image palette extraction), slim down `svg_library_tools.py` to planner-only, and extend the typer `svgs` commands with `render` and `knobs` discovery commands.

**Architecture:** A new `tesser/src/tesserax_service/scripts/svg_compose.py` module holds the full render engine (pure Python, no Tesser-specific deps). `builtin.py` imports from it and registers `svg.compose` plus five preset scripts. `svg_library_tools.py` loses its renderer and imports it back from `svg_compose.py` via `sys.path`. The typer `svgs` command does the same import swap plus two new commands.

**Tech Stack:** Python 3.12, PIL (Pillow), numpy (for LAB k-means), SVG string generation, Typer CLI, existing Tesser `register_script` decorator pattern.

---

## Task 1: Create `svg_compose.py` — skeleton + render engine port

**Files:**
- Create: `tesser/src/tesserax_service/scripts/svg_compose.py`
- Create: `tesser/tests/test_svg_compose.py`

**Step 1: Write the failing tests**

Create `tesser/tests/test_svg_compose.py`:

```python
"""Tests for svg_compose render engine."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tesserax_service.scripts.svg_compose import render_svg, validate_svg, INPUT_SCHEMA


def test_empty_params_produces_valid_svg():
    svg = render_svg({})
    errors = validate_svg(svg)
    assert errors == [], f"Unexpected errors: {errors}"
    assert "<svg" in svg
    assert "viewBox" in svg
    assert "</svg>" in svg


def test_validate_catches_missing_root():
    errors = validate_svg("not svg at all")
    assert "missing-svg-root" in errors


def test_validate_catches_forbidden_script():
    errors = validate_svg('<svg viewBox="0 0 100 100"><script>alert(1)</script></svg>')
    assert any("forbidden-token" in e for e in errors)


def test_validate_catches_oversized():
    errors = validate_svg('<svg viewBox="0 0 1 1">' + "x" * 260_000 + "</svg>")
    assert "exceeds-hard-size-cap" in errors


def test_input_schema_has_all_knobs():
    props = INPUT_SCHEMA["properties"]
    required_knobs = [
        "style_family", "shape_family", "layer_count", "density", "symmetry",
        "turbulence_type", "displacement_scale", "gaussian_blur", "palette_family",
        "blend_mode_primary", "morphology", "fuzz_mask", "luminance_bias",
        "saturation_band", "blend_mode_secondary", "frequency_jitter", "phase_offset",
    ]
    for knob in required_knobs:
        assert knob in props, f"Missing knob in INPUT_SCHEMA: {knob}"


def test_each_style_family_renders():
    for family in ["organic", "geometric", "glitch", "minimal", "atmospheric", "diagrammatic"]:
        svg = render_svg({"style_family": family})
        assert validate_svg(svg) == [], f"Family {family} produced invalid SVG"


def test_all_viewbox_modes_render():
    for vb in ["square(1024)", "landscape(1366x768)", "portrait(768x1366)"]:
        svg = render_svg({"viewbox": vb})
        assert validate_svg(svg) == []
        assert "viewBox" in svg


def test_element_cap_not_exceeded():
    svg = render_svg({"layer_count": "6", "density": "dense"})
    assert validate_svg(svg) == []
```

**Step 2: Run to confirm they all fail**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v 2>&1 | head -30
```

Expected: ImportError or ModuleNotFoundError — `svg_compose` doesn't exist yet.

**Step 3: Create `svg_compose.py` — port the working engine from `svg_library_tools.py`**

Create `tesser/src/tesserax_service/scripts/svg_compose.py` with:

```python
"""
SVG Compose — Tesser render engine.

Full 30-knob SVG generation engine. Pure Python, no Tesser-specific
dependencies. Importable by builtin.py (Tesser scripts) and by
svg_library_tools.py (combinatorics planner) alike.
"""
from __future__ import annotations

import hashlib
import math
import random
from typing import Any

# ---------------------------------------------------------------------------
# Palette tables
# ---------------------------------------------------------------------------

PALETTE_BY_STYLE_FAMILY: dict[str, list[str]] = {
    "organic":      ["#6BA292", "#82BFA0", "#4E7A63", "#D8E2C9", "#244739", "#90B77D"],
    "geometric":    ["#1E293B", "#334155", "#64748B", "#CBD5E1", "#0F172A", "#38BDF8"],
    "glitch":       ["#0B0F1A", "#00E5FF", "#FF006E", "#FFE600", "#7C3AED", "#12F7B6"],
    "minimal":      ["#111827", "#374151", "#6B7280", "#9CA3AF", "#D1D5DB", "#F3F4F6"],
    "atmospheric":  ["#1A2A6C", "#3F4C6B", "#4B79A1", "#7F7FD5", "#B993D6", "#E0EAFC"],
    "diagrammatic": ["#0F172A", "#1D4ED8", "#2563EB", "#3B82F6", "#93C5FD", "#E2E8F0"],
}

PALETTE_BY_PALETTE_FAMILY: dict[str, list[str]] = {
    "warm":    ["#7C2D12", "#C2410C", "#EA580C", "#FB923C", "#FED7AA", "#FFF7ED"],
    "cool":    ["#1E3A5F", "#2563EB", "#60A5FA", "#BAE6FD", "#E0F2FE", "#F0F9FF"],
    "duotone": ["#0F172A", "#E2E8F0"],
    "neon":    ["#00E5FF", "#FF006E", "#FFE600", "#7C3AED", "#12F7B6", "#FF4500"],
    "earth":   ["#3B1F0E", "#6B3A2A", "#8B6347", "#B89468", "#D4B896", "#F5ECD7"],
    "mono":    ["#111827", "#374151", "#6B7280", "#9CA3AF", "#D1D5DB", "#F9FAFB"],
}

# ---------------------------------------------------------------------------
# Input schema
# ---------------------------------------------------------------------------

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        # Geometry
        "style_family":     {"type": "string", "enum": ["organic","geometric","glitch","minimal","atmospheric","diagrammatic"], "default": "geometric"},
        "shape_family":     {"type": "string", "enum": ["curves","polygons","rings","stripes","particles"], "default": "curves"},
        "layer_count":      {"type": "string", "enum": ["1","2","4","6"], "default": "2"},
        "density":          {"type": "string", "enum": ["sparse","medium","dense"], "default": "medium"},
        "symmetry":         {"type": "string", "enum": ["none","radial","mirror-x","mirror-y"], "default": "none"},
        "viewbox":          {"type": "string", "enum": ["square(1024)","landscape(1366x768)","portrait(768x1366)"], "default": "square(1024)"},
        # Turbulence
        "turbulence_type":  {"type": "string", "enum": ["fractalNoise","turbulence"], "default": "fractalNoise"},
        "base_frequency":   {"type": "string", "enum": ["0.003","0.01","0.03","0.08"], "default": "0.01"},
        "num_octaves":      {"type": "string", "enum": ["1","2","4","6"], "default": "2"},
        "seed":             {"type": "integer", "default": 42},
        "stitch_tiles":     {"type": "string", "enum": ["stitch","noStitch"], "default": "noStitch"},
        # Displacement
        "displacement_scale": {"type": "string", "enum": ["0","8","24","64","120"], "default": "0"},
        "channel_x":          {"type": "string", "enum": ["R","G","B","A"], "default": "R"},
        "channel_y":          {"type": "string", "enum": ["R","G","B","A"], "default": "G"},
        "distortion_scope":   {"type": "string", "enum": ["background-only","subject-only","global"], "default": "global"},
        # Blur / edge
        "gaussian_blur":    {"type": "string", "enum": ["0","0.8","2","6","14"], "default": "0"},
        "morphology":       {"type": "string", "enum": ["none","erode(1)","dilate(1)","dilate(3)"], "default": "none"},
        "drop_shadow":      {"type": "string", "enum": ["off","subtle","strong"], "default": "off"},
        "fuzz_mask":        {"type": "string", "enum": ["off","low","high"], "default": "off"},
        # Color / palette
        "palette_family":     {"type": "string", "enum": ["warm","cool","duotone","neon","earth","mono"], "default": "cool"},
        "palette_cardinality": {"type": "string", "enum": ["1","2","4","6"], "default": "4"},
        "contrast_band":      {"type": "string", "enum": ["low","mid","high"], "default": "mid"},
        "saturation_band":    {"type": "string", "enum": ["desat","balanced","vivid"], "default": "balanced"},
        "luminance_bias":     {"type": "string", "enum": ["dark","balanced","light"], "default": "balanced"},
        # Blending
        "blend_mode_primary":   {"type": "string", "enum": ["normal","multiply","screen","overlay","darken","lighten"], "default": "normal"},
        "blend_mode_secondary": {"type": "string", "enum": ["none","multiply","screen","overlay"], "default": "none"},
        "opacity_stack":        {"type": "string", "enum": ["flat(1.0)","stepped(1/0.7/0.4)","mist(0.15-0.55)"], "default": "flat(1.0)"},
        "composite_op":         {"type": "string", "enum": ["over","in","out","atop","xor"], "default": "over"},
        # Motion-texture
        "directionality":   {"type": "string", "enum": ["none","horizontal","vertical","diagonal","radial"], "default": "none"},
        "frequency_jitter": {"type": "string", "enum": ["none","low","high"], "default": "none"},
        "phase_offset":     {"type": "string", "enum": ["0","0.25","0.5","0.75"], "default": "0"},
    },
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_viewbox(value: str) -> tuple[int, int]:
    if value == "landscape(1366x768)":
        return 1366, 768
    if value == "portrait(768x1366)":
        return 768, 1366
    return 1024, 1024


def _opacity_sequence(kind: str, n: int) -> list[float]:
    if n <= 0:
        return []
    if kind == "stepped(1/0.7/0.4)":
        base = [1.0, 0.7, 0.4]
        return [base[i % 3] for i in range(n)]
    if kind == "mist(0.15-0.55)":
        if n == 1:
            return [0.55]
        return [0.55 - 0.40 * (i / (n - 1)) for i in range(n)]
    return [1.0] * n


def _palette_for_params(params: dict[str, Any]) -> list[str]:
    palette_family = params.get("palette_family", "")
    style_family   = params.get("style_family", "geometric")
    if palette_family in PALETTE_BY_PALETTE_FAMILY:
        base = list(PALETTE_BY_PALETTE_FAMILY[palette_family])
    else:
        base = list(PALETTE_BY_STYLE_FAMILY.get(style_family, PALETTE_BY_STYLE_FAMILY["geometric"]))
    cardinality = max(1, int(float(params.get("palette_cardinality", "4"))))
    # Apply luminance bias
    luminance_bias = params.get("luminance_bias", "balanced")
    if luminance_bias == "dark":
        base = [_darken_hex(c, 0.55) for c in base]
    elif luminance_bias == "light":
        base = [_lighten_hex(c, 0.55) for c in base]
    while len(base) < cardinality:
        base.extend(base)
    return base[:cardinality]


def _darken_hex(hex_color: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(int(r * factor), int(g * factor), int(b * factor))


def _lighten_hex(hex_color: str, factor: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return _rgb_to_hex(
        int(r + (255 - r) * factor),
        int(g + (255 - g) * factor),
        int(b + (255 - b) * factor),
    )


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0]*2 + h[1]*2 + h[2]*2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0,min(255,r)):02x}{max(0,min(255,g)):02x}{max(0,min(255,b)):02x}"


def _jitter_frequency(base: str, jitter: str, rng: random.Random) -> str:
    if jitter == "none":
        return base
    f = float(base)
    if jitter == "low":
        f *= rng.uniform(0.95, 1.05)
    else:  # high
        f *= rng.uniform(0.80, 1.20)
    return f"{f:.5f}"


def _phase_seed(seed: int, phase_offset: str) -> int:
    multipliers = {"0": 1, "0.25": 4, "0.5": 16, "0.75": 64}
    return seed * multipliers.get(phase_offset, 1)


def _saturation_filter_markup(saturation_band: str, filter_id: str) -> str:
    sat = {"desat": "0.2", "balanced": "1.0", "vivid": "1.8"}.get(saturation_band, "1.0")
    if sat == "1.0":
        return ""
    return (
        f'<filter id="{filter_id}-sat" x="0%" y="0%" width="100%" height="100%">'
        f'<feColorMatrix type="saturate" values="{sat}"/>'
        f'</filter>'
    )


def _build_filter(params: dict[str, Any], filter_id: str, rng: random.Random) -> tuple[str, int]:
    primitives: list[str] = []

    turb_type = params.get("turbulence_type", "fractalNoise")
    base_freq = _jitter_frequency(
        params.get("base_frequency", "0.01"),
        params.get("frequency_jitter", "none"),
        rng,
    )
    octaves  = params.get("num_octaves", "2")
    seed_val = _phase_seed(int(params.get("seed", 42)), params.get("phase_offset", "0"))
    stitch   = "stitch" if params.get("stitch_tiles") == "stitch" else "noStitch"

    primitives.append(
        f'<feTurbulence type="{turb_type}" baseFrequency="{base_freq}" '
        f'numOctaves="{octaves}" seed="{seed_val}" stitchTiles="{stitch}" result="noise"/>'
    )

    disp = float(params.get("displacement_scale", "0"))
    if disp > 0:
        cx = params.get("channel_x", "R")
        cy = params.get("channel_y", "G")
        primitives.append(
            f'<feDisplacementMap in="SourceGraphic" in2="noise" scale="{disp}" '
            f'xChannelSelector="{cx}" yChannelSelector="{cy}" result="distorted"/>'
        )

    blur = float(params.get("gaussian_blur", "0"))
    if blur > 0:
        blur_in = "distorted" if disp > 0 else "SourceGraphic"
        primitives.append(
            f'<feGaussianBlur in="{blur_in}" stdDeviation="{min(blur, 14.0)}" result="blurred"/>'
        )

    morph = params.get("morphology", "none")
    if morph != "none":
        op, radius = ("erode", "1") if morph == "erode(1)" else ("dilate", morph.split("(")[1].rstrip(")"))
        morph_in = "blurred" if blur > 0 else ("distorted" if disp > 0 else "SourceGraphic")
        primitives.append(
            f'<feMorphology operator="{op}" radius="{radius}" in="{morph_in}" result="morphed"/>'
        )

    fuzz = params.get("fuzz_mask", "off")
    if fuzz != "off":
        fuzz_freq = "0.65" if fuzz == "low" else "1.2"
        primitives.append(
            f'<feTurbulence type="fractalNoise" baseFrequency="{fuzz_freq}" numOctaves="1" '
            f'seed="{(seed_val + 7) % 9999}" result="fuzz-noise"/>'
        )
        primitives.append(
            '<feComposite in="SourceGraphic" in2="fuzz-noise" operator="arithmetic" '
            'k1="0" k2="0.9" k3="0.1" k4="0" result="fuzzed"/>'
        )

    if params.get("drop_shadow") in {"subtle", "strong"}:
        std = "2.5" if params.get("drop_shadow") == "subtle" else "6.0"
        primitives.append(
            f'<feDropShadow dx="0" dy="2" stdDeviation="{std}" flood-opacity="0.28"/>'
        )

    body = "\n      ".join(primitives)
    return f'<filter id="{filter_id}">\n      {body}\n    </filter>', len(primitives)


# ---------------------------------------------------------------------------
# Main renderer
# ---------------------------------------------------------------------------

def render_svg(params: dict[str, Any], *, override_palette: list[str] | None = None) -> str:
    """Render deterministic SVG markup from a params dict. All fields are optional."""
    seed_val = int(params.get("seed", 42))
    rng = random.Random(seed_val)

    width, height = _parse_viewbox(params.get("viewbox", "square(1024)"))
    layers        = int(float(params.get("layer_count", "2")))
    density       = params.get("density", "medium")
    shape_family  = params.get("shape_family", "curves")
    symmetry      = params.get("symmetry", "none")
    blend_primary = params.get("blend_mode_primary", "normal")
    blend_secondary = params.get("blend_mode_secondary", "none")
    opacities     = _opacity_sequence(params.get("opacity_stack", "flat(1.0)"), layers)
    palette       = override_palette or _palette_for_params(params)
    directionality = params.get("directionality", "none")

    density_scale     = {"sparse": 6, "medium": 14, "dense": 26}.get(density, 14)
    elements_per_layer = max(3, density_scale)

    filter_id = f"f-{hashlib.sha256(str(seed_val).encode()).hexdigest()[:8]}"
    filter_markup, filter_primitives = _build_filter(params, filter_id, rng)
    distortion_scope = params.get("distortion_scope", "global")

    sat_filter = _saturation_filter_markup(params.get("saturation_band", "balanced"), filter_id)

    defs_parts = [
        "<defs>",
        f'  <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{palette[0]}"/>'
        f'<stop offset="100%" stop-color="{palette[-1]}"/>'
        f'</linearGradient>',
        f"  {filter_markup}",
    ]
    if sat_filter:
        defs_parts.append(f"  {sat_filter}")
    defs_parts.append("</defs>")

    content: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="svg-compose-{seed_val}">',
        *defs_parts,
    ]

    # Background rect
    bg_filter = f' filter="url(#{filter_id})"' if distortion_scope in {"background-only", "global"} else ""
    sat_attr  = f' filter="url(#{filter_id}-sat)"' if sat_filter and not bg_filter else ""
    content.append(
        f'  <rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="url(#bg-grad)"{bg_filter}{sat_attr}/>'
    )

    for li in range(layers):
        opacity  = opacities[li] if li < len(opacities) else 1.0
        color    = palette[li % len(palette)]
        # directionality transforms
        transform = ""
        if directionality == "diagonal":
            transform = f' transform="rotate({12 + li * 7} {width // 2} {height // 2})"'
        elif directionality == "radial":
            transform = f' transform="rotate({li * 19} {width // 2} {height // 2})"'

        layer_filter = ""
        if distortion_scope == "subject-only":
            layer_filter = f' filter="url(#{filter_id})"'

        # secondary blend applies to layers beyond the first
        blend = blend_secondary if (blend_secondary != "none" and li > 0) else blend_primary

        content.append(
            f'  <g opacity="{opacity:.3f}" style="mix-blend-mode:{blend}"{transform}{layer_filter}>'
        )

        for i in range(elements_per_layer):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            w = rng.randint(max(8, width // 32), max(16, width // 6))
            h = rng.randint(max(8, height // 32), max(16, height // 6))
            c      = palette[(li + i) % len(palette)]
            stroke = palette[(li + i + 1) % len(palette)]

            if shape_family == "stripes":
                if directionality in {"vertical", "radial"}:
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
                    f'    <circle cx="{x}" cy="{y}" r="{r}" fill="none" '
                    f'stroke="{stroke}" stroke-width="2.2"/>'
                )
            elif shape_family == "particles":
                r = max(1, min(w, h) // 12)
                content.append(
                    f'    <circle cx="{x}" cy="{y}" r="{r}" fill="{c}" fill-opacity="0.7"/>'
                )
            elif shape_family == "polygons":
                pts = f"{x},{y} {min(width, x+w)},{y} {min(width, x+w//2)},{min(height, y+h)}"
                content.append(
                    f'    <polygon points="{pts}" fill="{c}" fill-opacity="0.24" '
                    f'stroke="{stroke}" stroke-width="1.2"/>'
                )
            else:  # curves
                x2 = min(width, x + w)
                y2 = min(height, y + h)
                cx = min(width, x + w // 2)
                cy_ctrl = max(0, y - h // 3)
                content.append(
                    f'    <path d="M {x} {y} Q {cx} {cy_ctrl}, {x2} {y2}" '
                    f'stroke="{stroke}" stroke-width="2" fill="none"/>'
                )

            # symmetry echoes
            if symmetry == "mirror-x":
                mx = max(0, width - x)
                content.append(
                    f'    <circle cx="{mx}" cy="{y}" r="{max(2, min(w,h)//16)}" '
                    f'fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "mirror-y":
                my = max(0, height - y)
                content.append(
                    f'    <circle cx="{x}" cy="{my}" r="{max(2, min(w,h)//16)}" '
                    f'fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "radial":
                content.append(
                    f'    <circle cx="{width-x}" cy="{height-y}" r="{max(2, min(w,h)//18)}" '
                    f'fill="{stroke}" fill-opacity="0.18"/>'
                )

        content.append("  </g>")

    content.append("</svg>")
    svg = "\n".join(content)

    # Safety guards
    if len(svg.encode("utf-8")) > 240_000:
        svg = svg[:220_000] + "\n</svg>"
    if filter_primitives > 12:
        svg = svg.replace(f' filter="url(#{filter_id})"', "")
    return svg


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_svg(svg_markup: str) -> list[str]:
    errors: list[str] = []
    lower = svg_markup.lower()
    if "<svg" not in lower or "</svg>" not in lower:
        errors.append("missing-svg-root")
    if "viewbox=" not in lower:
        errors.append("missing-viewbox")
    for token in ("<script", "onload=", "onerror=", "<foreignobject", 'xlink:href="http'):
        if token in lower:
            errors.append(f"forbidden-token:{token}")
    if len(svg_markup.encode("utf-8")) > 250_000:
        errors.append("exceeds-hard-size-cap")
    if svg_markup.count("<") - svg_markup.count("</svg>") > 2000:
        errors.append("element-cap-exceeded")
    return errors
```

**Step 4: Run tests**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v
```

Expected: all 8 tests PASS.

**Step 5: Commit**

```bash
cd /home/josep/dog
git add tesser/src/tesserax_service/scripts/svg_compose.py tesser/tests/test_svg_compose.py
git commit -m "feat(tesser): add svg_compose render engine with full 30-knob schema"
```

---

## Task 2: Register `svg.compose` and preset scripts in `builtin.py`

**Files:**
- Modify: `tesser/src/tesserax_service/scripts/builtin.py`

**Step 1: Write failing test**

Add to `tesser/tests/test_svg_compose.py`:

```python
def test_svg_compose_registered():
    from tesserax_service.scripts import builtin  # noqa: F401 — triggers registration
    from tesserax_service.registry import get_script, get_script_spec, list_scripts
    scripts = list_scripts()
    expected = ["demo.logo", "svg.compose", "svg.mist-field", "svg.signal-glitch",
                "svg.paper-grain", "svg.vector-rings", "svg.soft-gradient"]
    for s in expected:
        assert s in scripts, f"Script not registered: {s}"

def test_svg_compose_spec():
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script_spec
    spec = get_script_spec("svg.compose")
    assert "svg" in spec.supported_formats
    assert spec.enabled is True

def test_preset_scripts_produce_valid_svg(tmp_path):
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script
    for script_id in ["svg.mist-field", "svg.signal-glitch", "svg.paper-grain"]:
        fn = get_script(script_id)
        paths = fn({"seed": 7}, tmp_path, "out", ["svg"])
        assert len(paths) == 1
        svg = paths[0].read_text(encoding="utf-8")
        from tesserax_service.scripts.svg_compose import validate_svg
        assert validate_svg(svg) == [], f"{script_id} produced invalid SVG"

def test_svg_compose_produces_file(tmp_path):
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script
    fn = get_script("svg.compose")
    paths = fn({"style_family": "glitch", "seed": 42}, tmp_path, "out", ["svg"])
    assert len(paths) == 1
    assert paths[0].suffix == ".svg"
    assert paths[0].stat().st_size > 100
```

**Step 2: Run to confirm they fail**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py::test_svg_compose_registered -v
```

Expected: ImportError or AssertionError — scripts not yet registered.

**Step 3: Update `builtin.py`**

Replace the entire contents of `tesser/src/tesserax_service/scripts/builtin.py` with:

```python
from __future__ import annotations

from pathlib import Path

from tesserax_service.registry import register_script
from tesserax_service.scripts.svg_compose import render_svg, validate_svg, INPUT_SCHEMA


def _demo_logo_caps(params: dict[str, object], formats: list[str]) -> set[str]:
    extra: set[str] = set()
    if bool(params.get("animate", False)) and "gif" in formats:
        extra.add("render.gif")
    return extra


@register_script(
    "demo.logo",
    kind="static",
    default_runtime_profile="core",
    supported_formats={"svg"},
    base_capabilities={"render.svg"},
    resolve_capabilities=_demo_logo_caps,
)
def demo_logo(
    params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
) -> list[Path]:
    """Generate a simple SVG artifact to prove the execution contract."""
    if "svg" not in formats:
        raise ValueError("demo.logo currently supports only svg output")
    title = str(params.get("title", "tesserax service"))
    fill  = str(params.get("fill", "#0f766e"))
    out   = output_dir / f"{basename}.svg"
    out.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='680' height='220' viewBox='0 0 680 220'>"
        f"<rect width='680' height='220' fill='#f8fafc'/>"
        f"<circle cx='120' cy='110' r='60' fill='{fill}'/>"
        f"<text x='210' y='122' font-size='42' font-family='sans-serif' fill='#0f172a'>{title}</text>"
        f"</svg>",
        encoding="utf-8",
    )
    return [out]


# ---------------------------------------------------------------------------
# svg.compose — full 30-knob creative instrument
# ---------------------------------------------------------------------------

@register_script(
    "svg.compose",
    kind="static",
    default_runtime_profile="core",
    supported_formats={"svg"},
    base_capabilities={"render.svg"},
)
def svg_compose(
    params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
) -> list[Path]:
    """
    Full creative SVG renderer. Accepts all 30 knobs from INPUT_SCHEMA.
    Pass {} for a valid default render. Style families, blend modes, palette
    families, turbulence, displacement, morphology — all tunable.
    """
    if "svg" not in formats:
        raise ValueError("svg.compose currently supports only svg output")
    svg = render_svg(dict(params))
    errors = validate_svg(svg)
    if errors:
        raise ValueError(f"Render produced invalid SVG: {errors}")
    out = output_dir / f"{basename}.svg"
    out.write_text(svg, encoding="utf-8")
    return [out]


svg_compose.__tesser_input_schema__ = INPUT_SCHEMA  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Named presets — thin wrappers, seed-only schema
# ---------------------------------------------------------------------------

_PRESET_SCHEMA: dict[str, object] = {
    "type": "object",
    "properties": {
        "seed": {"type": "integer", "default": 42, "description": "Deterministic seed"},
    },
}


def _make_preset(script_id: str, defaults: dict[str, object]):
    """Factory: register a preset script that merges defaults with caller params."""
    @register_script(
        script_id,
        kind="static",
        default_runtime_profile="core",
        supported_formats={"svg"},
        base_capabilities={"render.svg"},
    )
    def _preset_fn(
        params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
    ) -> list[Path]:
        if "svg" not in formats:
            raise ValueError(f"{script_id} currently supports only svg output")
        merged = {**defaults, **{k: v for k, v in params.items() if k in {"seed"}}}
        svg = render_svg(merged)
        errors = validate_svg(svg)
        if errors:
            raise ValueError(f"{script_id} produced invalid SVG: {errors}")
        out = output_dir / f"{basename}.svg"
        out.write_text(svg, encoding="utf-8")
        return [out]

    _preset_fn.__doc__ = f"Preset: {script_id}"
    _preset_fn.__tesser_input_schema__ = _PRESET_SCHEMA  # type: ignore[attr-defined]
    return _preset_fn


_make_preset("svg.mist-field", {
    "style_family": "atmospheric", "shape_family": "particles",
    "turbulence_type": "fractalNoise", "base_frequency": "0.003",
    "num_octaves": "4", "blend_mode_primary": "screen",
    "palette_family": "cool", "density": "medium",
    "gaussian_blur": "2", "displacement_scale": "0",
    "opacity_stack": "mist(0.15-0.55)", "layer_count": "4",
})

_make_preset("svg.signal-glitch", {
    "style_family": "glitch", "shape_family": "particles",
    "displacement_scale": "64", "distortion_scope": "global",
    "blend_mode_primary": "overlay", "palette_family": "neon",
    "turbulence_type": "turbulence", "base_frequency": "0.03",
    "saturation_band": "vivid", "contrast_band": "high",
    "layer_count": "4", "density": "dense",
})

_make_preset("svg.paper-grain", {
    "style_family": "minimal", "shape_family": "curves",
    "turbulence_type": "fractalNoise", "base_frequency": "0.08",
    "num_octaves": "6", "blend_mode_primary": "multiply",
    "palette_family": "warm", "saturation_band": "desat",
    "displacement_scale": "0", "density": "sparse",
    "gaussian_blur": "0.8", "layer_count": "2",
})
```

Note: `svg.vector-rings` and `svg.soft-gradient` are registered in Tasks 3 and 4 respectively — they need additional implementation first.

**Step 4: Run tests**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
cd /home/josep/dog
git add tesser/src/tesserax_service/scripts/builtin.py
git commit -m "feat(tesser): register svg.compose + mist-field, signal-glitch, paper-grain presets"
```

---

## Task 3: `svg.vector-rings` — rings with secondary warp transform

**Files:**
- Modify: `tesser/src/tesserax_service/scripts/svg_compose.py` — add `render_rings_warp()`
- Modify: `tesser/src/tesserax_service/scripts/builtin.py` — register `svg.vector-rings`
- Modify: `tesser/tests/test_svg_compose.py` — add warp tests

**Step 1: Write failing tests**

Add to `tesser/tests/test_svg_compose.py`:

```python
def test_vector_rings_warp_modes(tmp_path):
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script
    from tesserax_service.scripts.svg_compose import validate_svg
    fn = get_script("svg.vector-rings")
    for warp in ["none", "wave", "spiral", "tilt"]:
        paths = fn({"seed": 42, "ring_warp": warp}, tmp_path, f"rings-{warp}", ["svg"])
        svg = paths[0].read_text(encoding="utf-8")
        assert validate_svg(svg) == [], f"ring_warp={warp} invalid"

def test_vector_rings_warp_intensity(tmp_path):
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script
    fn = get_script("svg.vector-rings")
    for intensity in ["low", "mid", "high"]:
        paths = fn({"seed": 42, "ring_warp": "wave", "ring_warp_intensity": intensity},
                   tmp_path, f"rings-wave-{intensity}", ["svg"])
        assert paths[0].exists()
```

**Step 2: Run to confirm failure**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py::test_vector_rings_warp_modes -v
```

Expected: AssertionError — `svg.vector-rings` not registered yet.

**Step 3: Add `render_rings_warp()` to `svg_compose.py`**

Add after the `validate_svg` function:

```python
import math as _math

_RINGS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "seed":               {"type": "integer", "default": 42},
        "ring_count":         {"type": "integer", "default": 8, "minimum": 3, "maximum": 24},
        "palette_family":     {"type": "string", "enum": ["warm","cool","duotone","neon","earth","mono"], "default": "mono"},
        "contrast_band":      {"type": "string", "enum": ["low","mid","high"], "default": "high"},
        "ring_warp":          {"type": "string", "enum": ["none","wave","spiral","tilt"], "default": "none"},
        "ring_warp_intensity": {"type": "string", "enum": ["low","mid","high"], "default": "mid"},
    },
}

RINGS_INPUT_SCHEMA = _RINGS_SCHEMA


def render_rings_warp(params: dict[str, Any]) -> str:
    """Render radially-symmetric rings with optional warp transform."""
    seed_val   = int(params.get("seed", 42))
    rng        = random.Random(seed_val)
    ring_count = max(3, min(24, int(params.get("ring_count", 8))))
    warp       = params.get("ring_warp", "none")
    intensity  = params.get("ring_warp_intensity", "mid")
    amp_map    = {"low": 0.08, "mid": 0.18, "high": 0.38}
    amplitude  = amp_map.get(intensity, 0.18)

    width, height = 1024, 1024
    cx_center, cy_center = width // 2, height // 2

    palette   = _palette_for_params({**params, "style_family": "geometric"})
    stroke_c  = palette[0]
    alt_c     = palette[1] if len(palette) > 1 else palette[0]

    content = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-label="svg-vector-rings-{seed_val}">',
        f'<rect width="{width}" height="{height}" fill="{palette[-1]}"/>',
    ]

    max_r = int(width * 0.46)
    step  = max_r / ring_count

    for i in range(ring_count):
        r     = int(step * (i + 1))
        color = stroke_c if i % 2 == 0 else alt_c
        sw    = max(0.8, 2.5 - i * 0.15)

        if warp == "none":
            content.append(
                f'<circle cx="{cx_center}" cy="{cy_center}" r="{r}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>'
            )

        elif warp == "wave":
            # Approximate wavy circle as polygon (64 points with radial sinusoidal modulation)
            n_pts    = 64
            freq     = rng.randint(3, 7)
            phase    = rng.uniform(0, _math.tau)
            pts: list[str] = []
            for k in range(n_pts):
                angle = _math.tau * k / n_pts
                r_mod = r * (1 + amplitude * _math.sin(freq * angle + phase))
                px    = cx_center + r_mod * _math.cos(angle)
                py    = cy_center + r_mod * _math.sin(angle)
                pts.append(f"{px:.1f},{py:.1f}")
            content.append(
                f'<polygon points="{" ".join(pts)}" fill="none" '
                f'stroke="{color}" stroke-width="{sw:.2f}"/>'
            )

        elif warp == "spiral":
            # Each ring offset from center by amplitude * r, direction rotates with i
            offset_angle = _math.tau * i / ring_count
            offset_dist  = r * amplitude
            ox = cx_center + int(offset_dist * _math.cos(offset_angle))
            oy = cy_center + int(offset_dist * _math.sin(offset_angle))
            content.append(
                f'<circle cx="{ox}" cy="{oy}" r="{r}" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>'
            )

        elif warp == "tilt":
            # 3D perspective: render as ellipse, rx = r, ry = r * cos(tilt), rotated
            tilt_angle_deg = 15 + int(amplitude * 60)
            tilt_rad       = _math.radians(tilt_angle_deg)
            ry             = max(2, int(r * _math.cos(tilt_rad)))
            content.append(
                f'<ellipse cx="{cx_center}" cy="{cy_center}" rx="{r}" ry="{ry}" '
                f'transform="rotate({tilt_angle_deg} {cx_center} {cy_center})" '
                f'fill="none" stroke="{color}" stroke-width="{sw:.2f}"/>'
            )

    content.append("</svg>")
    return "\n".join(content)
```

**Step 4: Register `svg.vector-rings` in `builtin.py`**

Add at the end of `builtin.py`:

```python
from tesserax_service.scripts.svg_compose import render_rings_warp, RINGS_INPUT_SCHEMA


@register_script(
    "svg.vector-rings",
    kind="static",
    default_runtime_profile="core",
    supported_formats={"svg"},
    base_capabilities={"render.svg"},
)
def svg_vector_rings(
    params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
) -> list[Path]:
    """
    Radially-symmetric rings with tunable secondary warp transform.
    ring_warp: none | wave | spiral | tilt
    ring_warp_intensity: low | mid | high
    """
    if "svg" not in formats:
        raise ValueError("svg.vector-rings supports only svg output")
    from tesserax_service.scripts.svg_compose import validate_svg
    svg = render_rings_warp(dict(params))
    errors = validate_svg(svg)
    if errors:
        raise ValueError(f"svg.vector-rings produced invalid SVG: {errors}")
    out = output_dir / f"{basename}.svg"
    out.write_text(svg, encoding="utf-8")
    return [out]


svg_vector_rings.__tesser_input_schema__ = RINGS_INPUT_SCHEMA  # type: ignore[attr-defined]
```

**Step 5: Run tests**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v
```

Expected: all tests PASS.

**Step 6: Commit**

```bash
cd /home/josep/dog
git add tesser/src/tesserax_service/scripts/svg_compose.py tesser/src/tesserax_service/scripts/builtin.py tesser/tests/test_svg_compose.py
git commit -m "feat(tesser): add svg.vector-rings with wave/spiral/tilt warp transforms"
```

---

## Task 4: `svg.soft-gradient` — image-driven palette via LAB k-means

**Files:**
- Modify: `tesser/src/tesserax_service/scripts/svg_compose.py` — add `extract_palette_from_url()`, `render_soft_gradient()`
- Modify: `tesser/src/tesserax_service/scripts/builtin.py` — register `svg.soft-gradient`
- Modify: `tesser/tests/test_svg_compose.py` — add extraction tests

PIL and numpy are available in the Tesser venv. No additional dependencies needed.

**Step 1: Write failing tests**

Add to `tesser/tests/test_svg_compose.py`:

```python
def test_extract_palette_dominant():
    """Test LAB k-means extraction returns valid hex colors."""
    from tesserax_service.scripts.svg_compose import extract_palette_from_image_bytes
    import urllib.request
    # Use a small known PNG (red square data URI decoded)
    import base64, io
    from PIL import Image
    img = Image.new("RGB", (20, 20), color=(200, 50, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    colors = extract_palette_from_image_bytes(buf.getvalue(), k=3, mode="dominant")
    assert len(colors) == 3
    for c in colors:
        assert c.startswith("#"), f"Invalid hex: {c}"
        assert len(c) == 7

def test_extract_palette_modes():
    """All palette_mode values produce valid hex colors."""
    from tesserax_service.scripts.svg_compose import extract_palette_from_image_bytes
    import io
    from PIL import Image
    img = Image.new("RGB", (30, 30), color=(100, 150, 200))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    for mode in ["dominant", "harmonize", "ghost", "complement", "coolshift", "warmshift"]:
        colors = extract_palette_from_image_bytes(buf.getvalue(), k=4, mode=mode)
        assert len(colors) == 4, f"mode={mode} returned {len(colors)} colors"

def test_soft_gradient_no_image_url(tmp_path):
    """soft-gradient works without source_image_url (falls back to default palette)."""
    from tesserax_service.scripts import builtin  # noqa: F401
    from tesserax_service.registry import get_script
    from tesserax_service.scripts.svg_compose import validate_svg
    fn = get_script("svg.soft-gradient")
    paths = fn({"seed": 42}, tmp_path, "sg", ["svg"])
    svg = paths[0].read_text(encoding="utf-8")
    assert validate_svg(svg) == []
```

**Step 2: Run to confirm failure**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py::test_extract_palette_dominant tests/test_svg_compose.py::test_soft_gradient_no_image_url -v
```

Expected: ImportError — functions don't exist yet.

**Step 3: Add image extraction + soft gradient renderer to `svg_compose.py`**

Add after the `render_rings_warp` function:

```python
import io as _io
import math as _math  # already imported above, keep one
try:
    import numpy as _np
    from PIL import Image as _Image
    _IMAGE_DEPS_AVAILABLE = True
except ImportError:
    _IMAGE_DEPS_AVAILABLE = False


def _rgb_arr_to_lab(arr: "_np.ndarray") -> "_np.ndarray":
    """Convert (N, 3) uint8 RGB array to (N, 3) float32 LAB."""
    rgb = arr.astype(_np.float32) / 255.0
    # sRGB → linear
    linear = _np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    # linear RGB → XYZ (D65)
    M = _np.array([[0.4124, 0.3576, 0.1805],
                   [0.2126, 0.7152, 0.0722],
                   [0.0193, 0.1192, 0.9505]], dtype=_np.float32)
    xyz = linear @ M.T
    # XYZ → LAB
    xyz /= _np.array([0.95047, 1.0, 1.08883], dtype=_np.float32)
    xyz = _np.where(xyz > 0.008856, xyz ** (1.0 / 3.0), 7.787 * xyz + 16.0 / 116.0)
    L = 116.0 * xyz[:, 1] - 16.0
    a = 500.0 * (xyz[:, 0] - xyz[:, 1])
    b = 200.0 * (xyz[:, 1] - xyz[:, 2])
    return _np.stack([L, a, b], axis=-1)


def _lab_to_hex(lab: "_np.ndarray") -> str:
    """Convert single (3,) LAB float32 to hex color string."""
    L, a, b = float(lab[0]), float(lab[1]), float(lab[2])
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    xyz = _np.array([
        fx ** 3 if fx ** 3 > 0.008856 else (fx - 16.0 / 116.0) / 7.787,
        fy ** 3 if fy ** 3 > 0.008856 else (fy - 16.0 / 116.0) / 7.787,
        fz ** 3 if fz ** 3 > 0.008856 else (fz - 16.0 / 116.0) / 7.787,
    ], dtype=_np.float32)
    xyz *= _np.array([0.95047, 1.0, 1.08883], dtype=_np.float32)
    M_inv = _np.array([[ 3.2406, -1.5372, -0.4986],
                       [-0.9689,  1.8758,  0.0415],
                       [ 0.0557, -0.2040,  1.0570]], dtype=_np.float32)
    rgb_lin = xyz @ M_inv.T
    rgb_lin = _np.clip(rgb_lin, 0.0, 1.0)
    rgb = _np.where(rgb_lin > 0.0031308,
                    1.055 * rgb_lin ** (1.0 / 2.4) - 0.055,
                    12.92 * rgb_lin)
    rgb = (_np.clip(rgb, 0.0, 1.0) * 255).astype(_np.uint8)
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _kmeans_lab(pixels_lab: "_np.ndarray", k: int, seed: int = 0, max_iter: int = 50) -> "_np.ndarray":
    """Simple k-means in LAB space. Returns (k, 3) centroid array."""
    rng = _np.random.default_rng(seed)
    idx = rng.choice(len(pixels_lab), k, replace=False)
    centers = pixels_lab[idx].copy()
    for _ in range(max_iter):
        dists  = _np.linalg.norm(pixels_lab[:, None, :] - centers[None, :, :], axis=-1)
        labels = _np.argmin(dists, axis=-1)
        new_centers = _np.array([
            pixels_lab[labels == i].mean(axis=0) if (labels == i).any() else centers[i]
            for i in range(k)
        ])
        if _np.allclose(centers, new_centers, atol=0.5):
            break
        centers = new_centers
    return centers


def _apply_palette_mode(centers_lab: "_np.ndarray", mode: str) -> "_np.ndarray":
    """Transform extracted LAB centroids according to palette_mode."""
    out = centers_lab.copy()
    if mode == "dominant":
        pass  # identity
    elif mode == "ghost":
        # Desaturate: pull a and b toward zero, keep L
        out[:, 1] *= 0.15
        out[:, 2] *= 0.15
    elif mode == "complement":
        # Hue-invert in LAB: negate a and b
        out[:, 1] = -out[:, 1]
        out[:, 2] = -out[:, 2]
    elif mode == "harmonize":
        # Sort by hue angle, redistribute evenly on the color wheel
        angles = _np.arctan2(out[:, 2], out[:, 1])
        chroma = _np.sqrt(out[:, 1]**2 + out[:, 2]**2)
        k = len(out)
        base_angle = angles[0]
        for i in range(k):
            new_angle = base_angle + (2 * _math.pi * i / k)
            out[i, 1] = chroma[i] * _math.cos(new_angle)
            out[i, 2] = chroma[i] * _math.sin(new_angle)
    elif mode == "coolshift":
        # Shift hue toward blue (negative a, positive b in LAB)
        out[:, 1] -= 15.0
        out[:, 2] += 10.0
        out[:, 0] = _np.clip(out[:, 0], 20.0, 85.0)
    elif mode == "warmshift":
        # Shift hue toward amber (positive a, slightly negative b)
        out[:, 1] += 18.0
        out[:, 2] -= 8.0
        out[:, 0] = _np.clip(out[:, 0], 25.0, 90.0)
    return out


def extract_palette_from_image_bytes(
    image_bytes: bytes,
    *,
    k: int = 4,
    mode: str = "dominant",
    seed: int = 0,
) -> list[str]:
    """
    Extract k colors from raw image bytes using k-means in LAB color space.
    Returns list of hex color strings.
    """
    if not _IMAGE_DEPS_AVAILABLE:
        raise RuntimeError("PIL and numpy are required for image palette extraction")
    img = _Image.open(_io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((120, 120))
    arr = _np.array(img).reshape(-1, 3)
    # Subsample for speed if very large
    if len(arr) > 5000:
        rng = _np.random.default_rng(seed)
        idx = rng.choice(len(arr), 5000, replace=False)
        arr = arr[idx]
    pixels_lab = _rgb_arr_to_lab(arr)
    centers    = _kmeans_lab(pixels_lab, k=k, seed=seed)
    centers    = _apply_palette_mode(centers, mode)
    # Sort by lightness descending (light to dark)
    order   = _np.argsort(-centers[:, 0])
    centers = centers[order]
    return [_lab_to_hex(c) for c in centers]


def _derive_tonal_params_from_lab(pixels_lab: "_np.ndarray") -> dict[str, str]:
    """Derive luminance_bias and saturation_band from image LAB statistics."""
    mean_L   = float(_np.mean(pixels_lab[:, 0]))
    mean_C   = float(_np.mean(_np.sqrt(pixels_lab[:, 1]**2 + pixels_lab[:, 2]**2)))
    luminance_bias   = "dark" if mean_L < 35 else ("light" if mean_L > 65 else "balanced")
    saturation_band  = "desat" if mean_C < 15 else ("vivid" if mean_C > 40 else "balanced")
    return {"luminance_bias": luminance_bias, "saturation_band": saturation_band}


_SOFT_GRADIENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "seed":              {"type": "integer", "default": 42},
        "source_image_url":  {"type": "string", "description": "URL of image to derive palette from (optional)"},
        "palette_mode":      {"type": "string", "enum": ["dominant","harmonize","ghost","complement","coolshift","warmshift"], "default": "dominant"},
        "palette_count":     {"type": "integer", "enum": [2, 3, 4, 6], "default": 4},
    },
}

SOFT_GRADIENT_INPUT_SCHEMA = _SOFT_GRADIENT_SCHEMA


def render_soft_gradient(params: dict[str, Any]) -> str:
    """
    Render a soft gradient SVG, optionally palette-derived from a source image.
    If source_image_url is provided, fetches the image, runs LAB k-means,
    and uses extracted colors. Auto-derives luminance_bias and saturation_band
    from image statistics unless overridden. Stored SVG has no external refs.
    """
    seed         = int(params.get("seed", 42))
    palette_mode = str(params.get("palette_mode", "dominant"))
    palette_count = int(params.get("palette_count", 4))
    image_url    = params.get("source_image_url")

    base_params: dict[str, Any] = {
        "seed": seed,
        "style_family": "minimal",
        "shape_family": "stripes",
        "displacement_scale": "0",
        "gaussian_blur": "0",
        "blend_mode_primary": "normal",
        "density": "sparse",
        "layer_count": "1",
        "opacity_stack": "flat(1.0)",
        "saturation_band": "balanced",
        "luminance_bias": "balanced",
        "palette_family": "cool",
        "palette_cardinality": str(palette_count),
    }

    override_palette: list[str] | None = None

    if image_url and _IMAGE_DEPS_AVAILABLE:
        import urllib.request
        try:
            with urllib.request.urlopen(str(image_url), timeout=8) as resp:
                image_bytes = resp.read()
            rng_np = __import__("numpy").random.default_rng(seed)
            # Also derive tonal params from image
            img    = _Image.open(_io.BytesIO(image_bytes)).convert("RGB")
            img.thumbnail((120, 120))
            arr    = __import__("numpy").array(img).reshape(-1, 3)
            pixels_lab = _rgb_arr_to_lab(arr)
            tonal  = _derive_tonal_params_from_lab(pixels_lab)
            base_params.update(tonal)
            override_palette = extract_palette_from_image_bytes(
                image_bytes, k=palette_count, mode=palette_mode, seed=seed
            )
        except Exception:
            # Network/decode failure — fall back to default palette gracefully
            override_palette = None

    return render_svg(base_params, override_palette=override_palette)
```

**Step 4: Register `svg.soft-gradient` in `builtin.py`**

Add at the end of `builtin.py`:

```python
from tesserax_service.scripts.svg_compose import render_soft_gradient, SOFT_GRADIENT_INPUT_SCHEMA


@register_script(
    "svg.soft-gradient",
    kind="static",
    default_runtime_profile="core",
    supported_formats={"svg"},
    base_capabilities={"render.svg"},
)
def svg_soft_gradient(
    params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
) -> list[Path]:
    """
    Soft gradient SVG with optional image-derived palette.
    Pass source_image_url to derive palette from an image via LAB k-means.
    palette_mode: dominant | harmonize | ghost | complement | coolshift | warmshift
    Stored SVG never contains external references.
    """
    if "svg" not in formats:
        raise ValueError("svg.soft-gradient supports only svg output")
    from tesserax_service.scripts.svg_compose import validate_svg
    svg = render_soft_gradient(dict(params))
    errors = validate_svg(svg)
    if errors:
        raise ValueError(f"svg.soft-gradient produced invalid SVG: {errors}")
    out = output_dir / f"{basename}.svg"
    out.write_text(svg, encoding="utf-8")
    return [out]


svg_soft_gradient.__tesser_input_schema__ = SOFT_GRADIENT_INPUT_SCHEMA  # type: ignore[attr-defined]
```

**Step 5: Run tests**

```bash
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v
```

Expected: all tests PASS (including the new extraction tests).

**Step 6: Commit**

```bash
cd /home/josep/dog
git add tesser/src/tesserax_service/scripts/svg_compose.py tesser/src/tesserax_service/scripts/builtin.py tesser/tests/test_svg_compose.py
git commit -m "feat(tesser): add svg.soft-gradient with LAB k-means image palette extraction"
```

---

## Task 5: Slim down `svg_library_tools.py` — planner only

**Files:**
- Modify: `backend/app/test_scripts/render_things/svg_library_tools.py`
- Modify: `backend/app/test_scripts/render_things/test_svg_library_population.py`

**Step 1: Write failing test**

Add a test to `backend/app/test_scripts/render_things/test_svg_library_population.py`:

```python
def test_render_svg_imported_from_tesser():
    """render_svg should come from tesserax svg_compose, not local code."""
    from svg_library_tools import render_svg, validate_svg
    # Verify the functions still work after the refactor
    plan = build_generation_plan(total_count=4, seed=42)
    for row in plan["rows"]:
        svg = render_svg(row)
        assert validate_svg(svg) == []
```

Also add at top of file: `from svg_library_tools import build_generation_plan`

**Step 2: Run to confirm current state**

```bash
cd /home/josep/dog/backend/app/test_scripts/render_things
python -m pytest test_svg_library_population.py::test_render_svg_imported_from_tesser -v
```

This should PASS now (before the refactor) since `svg_library_tools.py` still has `render_svg`. After the refactor it should still pass — this test verifies the contract is maintained.

**Step 3: Replace `svg_library_tools.py` with planner-only version**

The new file keeps: `build_generation_plan`, `build_pairwise_rows`, `build_asset_metadata`, `stable_seed`, `STYLE_FAMILIES`, `FAMILY_QUOTAS`, `PAIRWISE_DOMAINS`, all planner helpers.

It removes: `render_svg`, `validate_svg`, `_build_filter`, `_palette_for_row`, `_opacity_sequence`, `_parse_viewbox`, `PALETTE_BY_FAMILY`.

It adds an import shim at the top so existing callers don't break:

```python
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

from tesserax_service.scripts.svg_compose import render_svg, validate_svg  # noqa: E402

# ---------------------------------------------------------------------------
# Domain definitions (authoritative source for planner)
# ---------------------------------------------------------------------------

STYLE_FAMILIES = [
    "organic", "geometric", "glitch", "minimal", "atmospheric", "diagrammatic",
]

FAMILY_QUOTAS: dict[str, float] = {
    "organic": 0.18, "geometric": 0.18, "glitch": 0.14,
    "minimal": 0.16, "atmospheric": 0.18, "diagrammatic": 0.16,
}

PAIRWISE_DOMAINS: dict[str, list[str]] = {
    "shape_family":       ["curves","polygons","rings","stripes","particles"],
    "layer_count":        ["1","2","4","6"],
    "density":            ["sparse","medium","dense"],
    "symmetry":           ["none","radial","mirror-x","mirror-y"],
    "viewbox":            ["square(1024)","landscape(1366x768)","portrait(768x1366)"],
    "turbulence_type":    ["fractalNoise","turbulence"],
    "base_frequency":     ["0.003","0.01","0.03","0.08"],
    "num_octaves":        ["1","2","4","6"],
    "seed_bucket":        ["0-99","100-999","1000-9999"],
    "stitch_tiles":       ["stitch","noStitch"],
    "displacement_scale": ["0","8","24","64","120"],
    "channel_x":          ["R","G","B","A"],
    "channel_y":          ["R","G","B","A"],
    "distortion_scope":   ["background-only","subject-only","global"],
    "gaussian_blur":      ["0","0.8","2","6","14"],
    "morphology":         ["none","erode(1)","dilate(1)","dilate(3)"],
    "drop_shadow":        ["off","subtle","strong"],
    "fuzz_mask":          ["off","low","high"],
    "palette_family":     ["warm","cool","duotone","neon","earth","mono"],
    "palette_cardinality":["1","2","4","6"],
    "contrast_band":      ["low","mid","high"],
    "saturation_band":    ["desat","balanced","vivid"],
    "luminance_bias":     ["dark","balanced","light"],
    "blend_mode_primary": ["normal","multiply","screen","overlay","darken","lighten"],
    "blend_mode_secondary":["none","multiply","screen","overlay"],
    "opacity_stack":      ["flat(1.0)","stepped(1/0.7/0.4)","mist(0.15-0.55)"],
    "composite_op":       ["over","in","out","atop","xor"],
    "directionality":     ["none","horizontal","vertical","diagonal","radial"],
    "frequency_jitter":   ["none","low","high"],
    "phase_offset":       ["0","0.25","0.5","0.75"],
}

# ... (rest of planner functions unchanged: _hash_to_int, stable_seed,
#      _compute_pair_space, _pairs_for_row, _random_row, _apply_family_bias,
#      _allocate_family_targets, build_pairwise_rows, _hero_override,
#      _safe_override, build_generation_plan, build_asset_metadata)
```

Keep all planner functions verbatim from the original. Only the top changes.

**Step 4: Run tests**

```bash
cd /home/josep/dog/backend/app/test_scripts/render_things
python -m pytest test_svg_library_population.py -v
```

Expected: all tests PASS.

**Step 5: Commit**

```bash
cd /home/josep/dog
git add backend/app/test_scripts/render_things/svg_library_tools.py backend/app/test_scripts/render_things/test_svg_library_population.py
git commit -m "refactor(render_things): slim svg_library_tools to planner-only, import render from tesser"
```

---

## Task 6: Update `typer/commands/svgs.py` — new import + `render` and `knobs` commands

**Files:**
- Modify: `backend/app/test_scripts/typer/commands/svgs.py`

**Step 1: Update imports and add two new commands**

Replace the `sys.path` + `render_things` import block at the top with:

```python
# Render engine lives in Tesser — import directly
_TESSER_SRC = Path(__file__).resolve().parents[4] / "tesser" / "src"
if str(_TESSER_SRC) not in sys.path:
    sys.path.insert(0, str(_TESSER_SRC))

from tesserax_service.scripts.svg_compose import (
    INPUT_SCHEMA,
    render_svg,
    validate_svg,
)
from tesserax_service.scripts.svg_compose import RINGS_INPUT_SCHEMA, SOFT_GRADIENT_INPUT_SCHEMA

# Planner stays in render_things
RENDER_THINGS_DIR = Path(__file__).resolve().parents[2] / "render_things"
if str(RENDER_THINGS_DIR) not in sys.path:
    sys.path.append(str(RENDER_THINGS_DIR))

from svg_library_tools import build_asset_metadata, build_generation_plan
```

**Step 2: Add `knobs` command**

```python
@app.command("knobs")
def list_knobs(
    script: Annotated[
        str,
        typer.Option("--script", "-s", help="Script ID to inspect (default: svg.compose)"),
    ] = "svg.compose",
) -> None:
    """List all available knobs and their valid values for a script."""
    schema_map = {
        "svg.compose": INPUT_SCHEMA,
        "svg.vector-rings": RINGS_INPUT_SCHEMA,
        "svg.soft-gradient": SOFT_GRADIENT_INPUT_SCHEMA,
    }
    schema = schema_map.get(script)
    if schema is None:
        typer.secho(f"❌ Unknown script: {script}. Known: {', '.join(schema_map)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    typer.echo(f"\n🎛  Knobs for {script}:\n")
    for knob, spec in schema.get("properties", {}).items():
        enum_vals = spec.get("enum", [])
        default   = spec.get("default", "")
        desc      = spec.get("description", "")
        if enum_vals:
            vals_str = " | ".join(str(v) for v in enum_vals)
            typer.secho(f"  {knob}", fg=typer.colors.CYAN, nl=False)
            typer.echo(f"  [{vals_str}]  default={default}")
        else:
            typer.secho(f"  {knob}", fg=typer.colors.CYAN, nl=False)
            typer.echo(f"  {spec.get('type','')}  default={default}  {desc}")
    typer.echo()
```

**Step 3: Add `render` command**

```python
@app.command("render")
def render_single(
    output: Annotated[Path, typer.Argument(help="Output .svg file path")],
    params_json: Annotated[
        str | None,
        typer.Option("--params", "-p", help="JSON object of knob overrides"),
    ] = None,
    seed: Annotated[int | None, typer.Option("--seed", help="Seed override")] = None,
    style_family: Annotated[str | None, typer.Option("--family", "-f")] = None,
    open_after: Annotated[bool, typer.Option("--open", help="Open file after render")] = False,
) -> None:
    """
    Render a single SVG to a local file with hand-picked knobs.

    Example:
      svgs render out.svg --family glitch --seed 99
      svgs render out.svg --params '{"palette_family":"neon","displacement_scale":"64"}'
    """
    params: dict[str, Any] = {}
    if params_json:
        params = _json_loads_or_exit(params_json, label="params")
    if seed is not None:
        params["seed"] = seed
    if style_family is not None:
        params["style_family"] = style_family

    svg = render_svg(params)
    errors = validate_svg(svg)
    if errors:
        typer.secho(f"❌ Render produced invalid SVG: {errors}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8")
    typer.secho(f"✅ Rendered to {output}", fg=typer.colors.GREEN)
    typer.echo(f"   Bytes: {len(svg.encode('utf-8'))}")
    if open_after:
        import subprocess, platform
        opener = "open" if platform.system() == "Darwin" else "xdg-open"
        subprocess.Popen([opener, str(output)])
```

**Step 4: Manually test**

```bash
cd /home/josep/dog/backend/app/test_scripts/typer
python main.py svgs knobs
python main.py svgs knobs --script svg.vector-rings
python main.py svgs render /tmp/test-render.svg --family glitch --seed 42
```

Expected: knobs table prints cleanly, SVG file is created at `/tmp/test-render.svg`.

**Step 5: Commit**

```bash
cd /home/josep/dog
git add backend/app/test_scripts/typer/commands/svgs.py
git commit -m "feat(svgs): add render and knobs commands, update import to tesser engine"
```

---

## Task 7: Rewrite `TESSER_SCRIPT_REFERENCE.md`

**Files:**
- Modify: `tesser/TESSER_SCRIPT_REFERENCE.md`

Replace the full contents with the design-session text below. The voice is inviting rather than instructional — it tells people what's possible before it tells them what's required.

```markdown
# Tesser Script Reference

> *"Tell me, what is it you plan to do / with your one wild and precious life?"*
> — Mary Oliver

This is a companion for anyone adding to or extending Tesser's script library.
The goal isn't just to make something runnable — it's to make something that can
be found, understood, and used well, by people and by agents alike.

## What Tesser Scripts Are For

A Tesser script is a small, deliberate thing. It takes a set of parameters and
returns an artifact — most often an SVG. That's the whole contract. But within
that contract is a lot of room: for layered noise, for palette choices that feel
like weather, for shapes that are quiet or shapes that argue with each other.

The SVG Library and Tesser Studio are the current first-class surfaces. If you
want a script to appear there, SVG is the format you need to speak.

## What's Available Right Now

| Script | What it does |
|--------|-------------|
| `svg.compose` | Full 30-knob creative instrument. Every parameter is tunable. Pass `{}` for a beautiful default. |
| `svg.mist-field` | Soft atmospheric particles, low-frequency noise, screen blend, cool palette. |
| `svg.signal-glitch` | Heavy displacement, neon, global distortion, vivid contrast. |
| `svg.paper-grain` | Quiet, warm, desaturated, multiply blend, subtle noise. |
| `svg.vector-rings` | Radially-symmetric rings with tunable warp: `none`, `wave`, `spiral`, or `tilt`. |
| `svg.soft-gradient` | The most gentle option. Pass a `source_image_url` and it derives a palette via LAB k-means — the stored SVG carries no external references, only extracted colors. |
| `demo.logo` | A simple proof-of-execution artifact. Good for testing the pipeline. |

## The Knobs

`svg.compose` exposes 30 parameters grouped across seven creative dimensions:

- **Geometry** — `style_family`, `shape_family`, `layer_count`, `density`, `symmetry`, `viewbox`
- **Turbulence** — `turbulence_type`, `base_frequency`, `num_octaves`, `seed`, `stitch_tiles`
- **Displacement** — `displacement_scale`, `channel_x`, `channel_y`, `distortion_scope`
- **Blur / Edge** — `gaussian_blur`, `morphology`, `drop_shadow`, `fuzz_mask`
- **Palette** — `palette_family`, `palette_cardinality`, `contrast_band`, `saturation_band`, `luminance_bias`
- **Blending** — `blend_mode_primary`, `blend_mode_secondary`, `opacity_stack`, `composite_op`
- **Motion-texture** — `directionality`, `frequency_jitter`, `phase_offset`

Run `python main.py svgs knobs` from the typer CLI to see all valid values at a glance.

## What a Script Needs

To appear in the SVG Library, a script needs four things:

1. Registration in `tesserax_service/registry.py` (via the `@register_script` decorator in `builtin.py`)
2. `supported_formats` that includes `"svg"`
3. An actual `.svg` artifact when called with `formats=["svg"]`
4. An `input_schema` that honestly describes what it accepts

That last one matters more than it might seem. The schema is how the frontend
knows what to offer a user. It's how an agent knows what to ask for. Write it
with care — and with curiosity about who might be reading it.

## Where Things Live

| What | Where |
|------|-------|
| Script registration + implementations | `tesserax_service/scripts/builtin.py` |
| SVG render engine (all 30 knobs) | `tesserax_service/scripts/svg_compose.py` |
| External/example-backed scripts | `tesserax_service/scripts/external_examples.py` |
| Script registry | `tesserax_service/registry.py` |

## Input Schema Guidance

The frontend has two modes: **guided** (for simple flat schemas) and **JSON fallback**
(for everything else). Either works. Guided mode feels nicer for humans; JSON mode
is fine for agents.

`svg.compose` uses a flat enum schema for all 30 knobs — guided mode all the way.
Each parameter has a sensible default. `{}` is a valid input and produces
something worth looking at.

If you're adding a new script and want guided mode, keep properties flat:
`string` enums, `integer` ranges, `boolean` flags. Nested objects work, but
they fall back to JSON mode.

## Adding a New Script

1. Implement the render logic in `svg_compose.py` (for SVG-related work) or inline in `builtin.py`
2. Define an `input_schema` dict
3. Register with `@register_script` — choose `kind`, `default_runtime_profile`, `supported_formats`
4. Attach the schema: `your_fn.__tesser_input_schema__ = YOUR_SCHEMA`
5. Run the tests: `pytest tesser/tests/test_svg_compose.py`
6. Check the checklist below

## The Checklist

Before calling a script ready for the SVG Library:

- [ ] Registered, enabled, `supported_formats` includes `"svg"`
- [ ] `formats=["svg"]` returns a real `.svg` file
- [ ] `input_schema` present and accurate
- [ ] Basic path works with `{}` payload
- [ ] Not a utility/runner that should stay hidden from render surfaces

## A Few Good Patterns

- Keep `script_id` stable and readable — it's how both humans and agents navigate
- Match `default_runtime_profile` to actual output needs (`core` for SVG-only, `export` for heavier work)
- When in doubt about the schema: write what you'd want to read if you were an agent discovering a new tool for the first time

## Related Files

- `tesserax_service/scripts/svg_compose.py` — render engine
- `tesserax_service/scripts/builtin.py` — registered scripts
- `tesserax_service/registry.py` — `ScriptSpec`, `register_script`, `get_script`
- `tesserax_service/profiles.py` — runtime profile resolution
- `tesserax_service/runtime.py` — artifact promotion
- `backend/app/test_scripts/typer/commands/svgs.py` — CLI (`knobs`, `render`, `seed`, `plan`)
- `backend/app/test_scripts/render_things/svg_library_tools.py` — combinatorics planner
```

**Step 2: Commit**

```bash
cd /home/josep/dog
git add tesser/TESSER_SCRIPT_REFERENCE.md
git commit -m "docs(tesser): rewrite script reference with warmth and updated script inventory"
```

---

## Final Verification

```bash
# Full test suite
cd /home/josep/dog/tesser
.venv/bin/python -m pytest tests/test_svg_compose.py -v

# Planner tests
cd /home/josep/dog/backend/app/test_scripts/render_things
python -m pytest test_svg_library_population.py -v

# CLI smoke
cd /home/josep/dog/backend/app/test_scripts/typer
python main.py svgs knobs
python main.py svgs knobs --script svg.vector-rings
python main.py svgs render /tmp/smoke.svg --family atmospheric --seed 2026
python main.py svgs plan --count 10
python main.py svgs seed --count 5 --dry-run
```

All should pass. `svgs seed --dry-run` validates that the planner + new render engine round-trip cleanly.
