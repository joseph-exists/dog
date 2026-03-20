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
