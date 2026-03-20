"""
SVG Compose — Tesser render engine.

Full 30-knob SVG generation engine. Pure Python, no Tesser-specific
dependencies. Importable by builtin.py (Tesser scripts) and by
svg_library_tools.py (combinatorics planner) alike.
"""
from __future__ import annotations

import hashlib
import io as _io
import math
import random
from typing import Any

try:
    import numpy as _np
    from PIL import Image as _Image
    _IMAGE_DEPS_AVAILABLE = True
except ImportError:
    _IMAGE_DEPS_AVAILABLE = False

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
    "duotone": ["#0F172A", "#E2E8F0", "#0F172A", "#E2E8F0", "#0F172A", "#E2E8F0"],
    "neon":    ["#00E5FF", "#FF006E", "#FFE600", "#7C3AED", "#12F7B6", "#FF4500"],
    "earth":   ["#3B1F0E", "#6B3A2A", "#8B6347", "#B89468", "#D4B896", "#F5ECD7"],
    "mono":    ["#111827", "#374151", "#6B7280", "#9CA3AF", "#D1D5DB", "#F9FAFB"],
}

# ---------------------------------------------------------------------------
# Input schema — all 30 knobs
# ---------------------------------------------------------------------------

INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        # Geometry
        "style_family": {
            "type": "string",
            "enum": ["organic", "geometric", "glitch", "minimal", "atmospheric", "diagrammatic"],
            "default": "geometric",
        },
        "shape_family": {
            "type": "string",
            "enum": ["curves", "polygons", "rings", "stripes", "particles"],
            "default": "curves",
        },
        "layer_count": {"type": "string", "enum": ["1", "2", "4", "6"], "default": "2"},
        "density": {"type": "string", "enum": ["sparse", "medium", "dense"], "default": "medium"},
        "symmetry": {
            "type": "string",
            "enum": ["none", "radial", "mirror-x", "mirror-y"],
            "default": "none",
        },
        "viewbox": {
            "type": "string",
            "enum": ["square(1024)", "landscape(1366x768)", "portrait(768x1366)"],
            "default": "square(1024)",
        },
        # Turbulence
        "turbulence_type": {
            "type": "string",
            "enum": ["fractalNoise", "turbulence"],
            "default": "fractalNoise",
        },
        "base_frequency": {
            "type": "string",
            "enum": ["0.003", "0.01", "0.03", "0.08"],
            "default": "0.01",
        },
        "num_octaves": {"type": "string", "enum": ["1", "2", "4", "6"], "default": "2"},
        "seed": {"type": "integer", "default": 42},
        "stitch_tiles": {"type": "string", "enum": ["stitch", "noStitch"], "default": "noStitch"},
        # Displacement
        "displacement_scale": {
            "type": "string",
            "enum": ["0", "8", "24", "64", "120"],
            "default": "0",
        },
        "channel_x": {"type": "string", "enum": ["R", "G", "B", "A"], "default": "R"},
        "channel_y": {"type": "string", "enum": ["R", "G", "B", "A"], "default": "G"},
        "distortion_scope": {
            "type": "string",
            "enum": ["background-only", "subject-only", "global"],
            "default": "global",
        },
        # Blur / edge
        "gaussian_blur": {
            "type": "string",
            "enum": ["0", "0.8", "2", "6", "14"],
            "default": "0",
        },
        "morphology": {
            "type": "string",
            "enum": ["none", "erode(1)", "dilate(1)", "dilate(3)"],
            "default": "none",
        },
        "drop_shadow": {"type": "string", "enum": ["off", "subtle", "strong"], "default": "off"},
        "fuzz_mask": {"type": "string", "enum": ["off", "low", "high"], "default": "off"},
        # Color / palette
        "palette_family": {
            "type": "string",
            "enum": ["warm", "cool", "duotone", "neon", "earth", "mono"],
            "default": "cool",
        },
        "palette_cardinality": {
            "type": "string",
            "enum": ["1", "2", "4", "6"],
            "default": "4",
        },
        "contrast_band": {
            "type": "string",
            "enum": ["low", "mid", "high"],
            "default": "mid",
        },
        "saturation_band": {
            "type": "string",
            "enum": ["desat", "balanced", "vivid"],
            "default": "balanced",
        },
        "luminance_bias": {
            "type": "string",
            "enum": ["dark", "balanced", "light"],
            "default": "balanced",
        },
        # Blending
        "blend_mode_primary": {
            "type": "string",
            "enum": ["normal", "multiply", "screen", "overlay", "darken", "lighten"],
            "default": "normal",
        },
        "blend_mode_secondary": {
            "type": "string",
            "enum": ["none", "multiply", "screen", "overlay"],
            "default": "none",
        },
        "opacity_stack": {
            "type": "string",
            "enum": ["flat(1.0)", "stepped(1/0.7/0.4)", "mist(0.15-0.55)"],
            "default": "flat(1.0)",
        },
        "composite_op": {
            "type": "string",
            "enum": ["over", "in", "out", "atop", "xor"],
            "default": "over",
        },
        # Motion-texture
        "directionality": {
            "type": "string",
            "enum": ["none", "horizontal", "vertical", "diagonal", "radial"],
            "default": "none",
        },
        "frequency_jitter": {
            "type": "string",
            "enum": ["none", "low", "high"],
            "default": "none",
        },
        "phase_offset": {
            "type": "string",
            "enum": ["0", "0.25", "0.5", "0.75"],
            "default": "0",
        },
    },
}

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


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
    style_family = params.get("style_family", "geometric")
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
        base = base + base
    return base[:cardinality]


def _jitter_frequency(base: str, jitter: str, rng: random.Random) -> str:
    if jitter == "none":
        return base
    f = float(base)
    if jitter == "low":
        f *= rng.uniform(0.95, 1.05)
    else:  # high
        f *= rng.uniform(0.80, 1.20)
    return f"{f:.5f}"


_PHASE_CONSTANTS = {"0": 0, "0.25": 1000, "0.5": 5000, "0.75": 25000}


def _phase_seed(seed: int, phase_offset: str) -> int:
    return seed + _PHASE_CONSTANTS.get(phase_offset, 0)


def _saturation_filter_markup(saturation_band: str, filter_id: str) -> str:
    sat = {"desat": "0.2", "balanced": "1.0", "vivid": "1.8"}.get(saturation_band, "1.0")
    if sat == "1.0":
        return ""
    return (
        f'<filter id="{filter_id}-sat" x="0%" y="0%" width="100%" height="100%">'
        f'<feColorMatrix type="saturate" values="{sat}"/>'
        f"</filter>"
    )


def _build_filter(params: dict[str, Any], filter_id: str, seed_val: int) -> tuple[str, int]:
    primitives: list[str] = []

    turb_type = params.get("turbulence_type", "fractalNoise")
    jitter_rng = random.Random(seed_val + 99991)  # isolated from shape rng
    base_freq = _jitter_frequency(
        params.get("base_frequency", "0.01"),
        params.get("frequency_jitter", "none"),
        jitter_rng,
    )
    octaves = params.get("num_octaves", "2")
    seed_val = _phase_seed(int(params.get("seed", 42)), params.get("phase_offset", "0"))
    stitch = "stitch" if params.get("stitch_tiles") == "stitch" else "noStitch"

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
        if morph == "erode(1)":
            op, radius = "erode", "1"
        else:
            op = "dilate"
            radius = morph.split("(")[1].rstrip(")")
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
    layers = int(float(params.get("layer_count", "2")))
    density = params.get("density", "medium")
    shape_family = params.get("shape_family", "curves")
    symmetry = params.get("symmetry", "none")
    blend_primary = params.get("blend_mode_primary", "normal")
    blend_secondary = params.get("blend_mode_secondary", "none")
    opacities = _opacity_sequence(params.get("opacity_stack", "flat(1.0)"), layers)
    palette = override_palette or _palette_for_params(params)
    directionality = params.get("directionality", "none")

    density_scale = {"sparse": 6, "medium": 14, "dense": 26}.get(density, 14)
    elements_per_layer = max(3, density_scale)

    filter_id = f"f-{hashlib.sha256(str(seed_val).encode()).hexdigest()[:8]}"
    filter_markup, filter_primitives = _build_filter(params, filter_id, seed_val)
    distortion_scope = params.get("distortion_scope", "global")

    sat_filter = _saturation_filter_markup(params.get("saturation_band", "balanced"), filter_id)

    defs_parts = [
        "<defs>",
        (
            f'  <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">'
            f'<stop offset="0%" stop-color="{palette[0]}"/>'
            f'<stop offset="100%" stop-color="{palette[-1]}"/>'
            f"</linearGradient>"
        ),
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
    bg_filter = (
        f' filter="url(#{filter_id})"'
        if distortion_scope in {"background-only", "global"}
        else ""
    )
    content.append(
        f'  <rect x="0" y="0" width="{width}" height="{height}" '
        f'fill="url(#bg-grad)"{bg_filter}/>'
    )

    for li in range(layers):
        opacity = opacities[li] if li < len(opacities) else 1.0
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

        sat_layer = f' filter="url(#{filter_id}-sat)"' if sat_filter and not layer_filter else ""
        content.append(
            f'  <g opacity="{opacity:.3f}" style="mix-blend-mode:{blend}"{transform}{layer_filter}{sat_layer}>'
        )

        for i in range(elements_per_layer):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            w = rng.randint(max(8, width // 32), max(16, width // 6))
            h = rng.randint(max(8, height // 32), max(16, height // 6))
            c = palette[(li + i) % len(palette)]
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
                pts = f"{x},{y} {min(width, x + w)},{y} {min(width, x + w // 2)},{min(height, y + h)}"
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
                    f'    <circle cx="{mx}" cy="{y}" r="{max(2, min(w, h) // 16)}" '
                    f'fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "mirror-y":
                my = max(0, height - y)
                content.append(
                    f'    <circle cx="{x}" cy="{my}" r="{max(2, min(w, h) // 16)}" '
                    f'fill="{stroke}" fill-opacity="0.22"/>'
                )
            elif symmetry == "radial":
                content.append(
                    f'    <circle cx="{width - x}" cy="{height - y}" r="{max(2, min(w, h) // 18)}" '
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
# Rings warp renderer
# ---------------------------------------------------------------------------

RINGS_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "seed":                {"type": "integer", "default": 42},
        "ring_count":          {"type": "integer", "default": 8, "minimum": 3, "maximum": 24},
        "palette_family":      {"type": "string", "enum": ["warm", "cool", "duotone", "neon", "earth", "mono"], "default": "mono"},
        "contrast_band":       {"type": "string", "enum": ["low", "mid", "high"], "default": "high"},
        "ring_warp":           {"type": "string", "enum": ["none", "wave", "spiral", "tilt"], "default": "none"},
        "ring_warp_intensity": {"type": "string", "enum": ["low", "mid", "high"], "default": "mid"},
    },
}

_AMPLITUDE_MAP = {"low": 0.08, "mid": 0.18, "high": 0.38}


def render_rings_warp(params: dict[str, Any]) -> str:
    """Render radially-symmetric rings with tunable warp: none | wave | spiral | tilt."""
    seed_val = int(params.get("seed", 42))
    rng = random.Random(seed_val)

    ring_count = max(3, min(24, int(params.get("ring_count", 8))))
    warp = params.get("ring_warp", "none")
    intensity = params.get("ring_warp_intensity", "mid")
    amplitude = _AMPLITUDE_MAP.get(intensity, 0.18)

    cx = 512
    cy = 512
    max_radius = int(1024 * 0.46)

    palette_params = dict(params)
    palette_params.setdefault("style_family", "geometric")
    palette_params.setdefault("palette_cardinality", "4")
    palette = _palette_for_params(palette_params)

    bg_color = palette[-1]
    stroke0 = palette[0]
    stroke1 = palette[1] if len(palette) > 1 else palette[0]

    content: list[str] = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 1024" '
        f'role="img" aria-label="vector-rings-{seed_val}">',
        f'  <rect x="0" y="0" width="1024" height="1024" fill="{bg_color}"/>',
    ]

    for i in range(ring_count):
        # Evenly space radii from innermost to outermost
        r = max(4, int(max_radius * (i + 1) / ring_count))
        stroke_color = stroke0 if i % 2 == 0 else stroke1
        stroke_width = max(0.8, 2.5 - i * 0.15)

        if warp == "none":
            content.append(
                f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )

        elif warp == "wave":
            n_pts = 64
            freq = rng.randint(3, 7)
            phase = rng.uniform(0, math.tau)
            pts_list: list[str] = []
            for k in range(n_pts):
                angle = math.tau * k / n_pts
                r_mod = r * (1 + amplitude * math.sin(freq * angle + phase))
                px = cx + r_mod * math.cos(angle)
                py = cy + r_mod * math.sin(angle)
                pts_list.append(f"{px:.2f},{py:.2f}")
            points_str = " ".join(pts_list)
            content.append(
                f'  <polygon points="{points_str}" fill="none" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )

        elif warp == "spiral":
            offset_angle = math.tau * i / ring_count
            offset_dist = r * amplitude
            ox = cx + int(offset_dist * math.cos(offset_angle))
            oy = cy + int(offset_dist * math.sin(offset_angle))
            content.append(
                f'  <circle cx="{ox}" cy="{oy}" r="{r}" fill="none" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )

        elif warp == "tilt":
            tilt_angle_deg = 15 + int(amplitude * 60)
            tilt_rad = math.radians(tilt_angle_deg)
            ry = max(2, int(r * math.cos(tilt_rad)))
            content.append(
                f'  <ellipse cx="{cx}" cy="{cy}" rx="{r}" ry="{ry}" fill="none" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}" '
                f'transform="rotate({tilt_angle_deg} {cx} {cy})"/>'
            )

        else:
            content.append(
                f'  <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" '
                f'stroke="{stroke_color}" stroke-width="{stroke_width:.2f}"/>'
            )

    content.append("</svg>")
    return "\n".join(content)


# ---------------------------------------------------------------------------
# Image palette extraction (PIL + numpy required)
# ---------------------------------------------------------------------------


def _rgb_arr_to_lab(arr):
    """Convert (N, 3) uint8 RGB array to (N, 3) float32 LAB."""
    rgb = arr.astype(_np.float32) / 255.0
    linear = _np.where(rgb > 0.04045, ((rgb + 0.055) / 1.055) ** 2.4, rgb / 12.92)
    M = _np.array([[0.4124, 0.3576, 0.1805],
                   [0.2126, 0.7152, 0.0722],
                   [0.0193, 0.1192, 0.9505]], dtype=_np.float32)
    xyz = linear @ M.T
    xyz /= _np.array([0.95047, 1.0, 1.08883], dtype=_np.float32)
    xyz = _np.where(xyz > 0.008856, xyz ** (1.0 / 3.0), 7.787 * xyz + 16.0 / 116.0)
    L = 116.0 * xyz[:, 1] - 16.0
    a = 500.0 * (xyz[:, 0] - xyz[:, 1])
    b = 200.0 * (xyz[:, 1] - xyz[:, 2])
    return _np.stack([L, a, b], axis=-1)


def _lab_to_hex(lab):
    """Convert single (3,) LAB float32 to hex string."""
    L, a, b = float(lab[0]), float(lab[1]), float(lab[2])
    fy = (L + 16.0) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0

    def f_inv(t):
        return t**3 if t**3 > 0.008856 else (t - 16.0 / 116.0) / 7.787

    xyz = _np.array([f_inv(fx), f_inv(fy), f_inv(fz)], dtype=_np.float32)
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


def _kmeans_lab(pixels_lab, k, seed=0, max_iter=50):
    """Simple k-means in LAB space. Returns (k, 3) centroid array."""
    rng = _np.random.default_rng(seed)
    idx = rng.choice(len(pixels_lab), k, replace=False)
    centers = pixels_lab[idx].copy()
    for _ in range(max_iter):
        dists = _np.linalg.norm(pixels_lab[:, None, :] - centers[None, :, :], axis=-1)
        labels = _np.argmin(dists, axis=-1)
        new_centers = _np.array([
            pixels_lab[labels == i].mean(axis=0) if (labels == i).any() else centers[i]
            for i in range(k)
        ])
        if _np.allclose(centers, new_centers, atol=0.5):
            break
        centers = new_centers
    return centers


def _apply_palette_mode(centers_lab, mode):
    """Transform extracted LAB centroids per palette_mode."""
    import math as _m
    out = centers_lab.copy()
    if mode == "dominant":
        pass
    elif mode == "ghost":
        out[:, 1] *= 0.15
        out[:, 2] *= 0.15
    elif mode == "complement":
        out[:, 1] = -out[:, 1]
        out[:, 2] = -out[:, 2]
    elif mode == "harmonize":
        angles = _np.arctan2(out[:, 2], out[:, 1])
        chroma = _np.sqrt(out[:, 1]**2 + out[:, 2]**2)
        base_angle = float(angles[0])
        k = len(out)
        for i in range(k):
            new_angle = base_angle + (2 * _m.pi * i / k)
            out[i, 1] = chroma[i] * _m.cos(new_angle)
            out[i, 2] = chroma[i] * _m.sin(new_angle)
    elif mode == "coolshift":
        out[:, 1] -= 15.0
        out[:, 2] += 10.0
        out[:, 0] = _np.clip(out[:, 0], 20.0, 85.0)
    elif mode == "warmshift":
        out[:, 1] += 18.0
        out[:, 2] -= 8.0
        out[:, 0] = _np.clip(out[:, 0], 25.0, 90.0)
    return out


def _derive_tonal_params(pixels_lab):
    """Derive luminance_bias and saturation_band from LAB statistics."""
    mean_L = float(_np.mean(pixels_lab[:, 0]))
    mean_C = float(_np.mean(_np.sqrt(pixels_lab[:, 1]**2 + pixels_lab[:, 2]**2)))
    luminance_bias = "dark" if mean_L < 35 else ("light" if mean_L > 65 else "balanced")
    saturation_band = "desat" if mean_C < 15 else ("vivid" if mean_C > 40 else "balanced")
    return {"luminance_bias": luminance_bias, "saturation_band": saturation_band}


def extract_palette_from_image_bytes(image_bytes, *, k=4, mode="dominant", seed=0):
    """
    Extract k colors from image bytes using k-means in LAB color space.
    Returns list of hex strings. Requires PIL + numpy.
    """
    if not _IMAGE_DEPS_AVAILABLE:
        raise RuntimeError("PIL and numpy required for image palette extraction")
    img = _Image.open(_io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((120, 120))
    arr = _np.array(img).reshape(-1, 3)
    if len(arr) > 5000:
        rng = _np.random.default_rng(seed)
        arr = arr[rng.choice(len(arr), 5000, replace=False)]
    pixels_lab = _rgb_arr_to_lab(arr)
    centers = _kmeans_lab(pixels_lab, k=k, seed=seed)
    centers = _apply_palette_mode(centers, mode)
    order = _np.argsort(-centers[:, 0])  # sort light->dark
    centers = centers[order]
    return [_lab_to_hex(c) for c in centers]


# ---------------------------------------------------------------------------
# Soft gradient renderer
# ---------------------------------------------------------------------------

SOFT_GRADIENT_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "seed":             {"type": "integer", "default": 42},
        "source_image_url": {"type": "string", "description": "URL to derive palette from (optional)"},
        "palette_mode":     {"type": "string",
                             "enum": ["dominant", "harmonize", "ghost", "complement", "coolshift", "warmshift"],
                             "default": "dominant"},
        "palette_count":    {"type": "integer", "enum": [2, 3, 4, 6], "default": 4},
    },
}


def render_soft_gradient(params: dict[str, Any]) -> str:
    """
    Soft gradient SVG. If source_image_url provided, derives palette via LAB k-means.
    Auto-derives luminance_bias and saturation_band from image statistics.
    The stored SVG contains only extracted hex colors — no external refs.
    Falls back gracefully on any network/decode error.
    """
    seed          = int(params.get("seed", 42))
    palette_mode  = str(params.get("palette_mode", "dominant"))
    palette_count = int(params.get("palette_count", 4))
    image_url     = params.get("source_image_url")

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

    override_palette = None

    if image_url and _IMAGE_DEPS_AVAILABLE:
        import urllib.request
        try:
            with urllib.request.urlopen(str(image_url), timeout=8) as resp:
                image_bytes = resp.read()
            img = _Image.open(_io.BytesIO(image_bytes)).convert("RGB")
            img.thumbnail((120, 120))
            arr = _np.array(img).reshape(-1, 3)
            pixels_lab = _rgb_arr_to_lab(arr)
            base_params.update(_derive_tonal_params(pixels_lab))
            override_palette = extract_palette_from_image_bytes(
                image_bytes, k=palette_count, mode=palette_mode, seed=seed
            )
        except Exception:
            override_palette = None  # graceful fallback

    return render_svg(base_params, override_palette=override_palette)


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------


def validate_svg(svg_markup: str) -> list[str]:
    """Check compatibility/safety constraints and return validation errors."""
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
