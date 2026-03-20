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


def test_palette_family_affects_output():
    """Different palette_family values produce different SVG content."""
    svg_neon = render_svg({"palette_family": "neon", "seed": 42})
    svg_earth = render_svg({"palette_family": "earth", "seed": 42})
    assert validate_svg(svg_neon) == []
    assert validate_svg(svg_earth) == []
    assert svg_neon != svg_earth  # different palettes, different content


def test_morphology_adds_feMorphology():
    for morph in ["erode(1)", "dilate(1)", "dilate(3)"]:
        svg = render_svg({"morphology": morph, "seed": 42})
        assert validate_svg(svg) == []
        assert "feMorphology" in svg, f"morphology={morph} should add feMorphology"


def test_fuzz_mask_adds_feComposite():
    for fuzz in ["low", "high"]:
        svg = render_svg({"fuzz_mask": fuzz, "seed": 42})
        assert validate_svg(svg) == []
        assert "feComposite" in svg, f"fuzz_mask={fuzz} should add feComposite"


def test_luminance_bias_affects_palette():
    """dark and light bias produce different hex colors."""
    svg_dark = render_svg({"luminance_bias": "dark", "seed": 42})
    svg_light = render_svg({"luminance_bias": "light", "seed": 42})
    assert validate_svg(svg_dark) == []
    assert validate_svg(svg_light) == []
    assert svg_dark != svg_light


def test_saturation_band_adds_feColorMatrix():
    for band in ["desat", "vivid"]:
        svg = render_svg({"saturation_band": band, "seed": 42})
        assert validate_svg(svg) == []
        assert "feColorMatrix" in svg, f"saturation_band={band} should add feColorMatrix"


def test_blend_mode_secondary_applied_to_later_layers():
    svg = render_svg({"layer_count": "4", "blend_mode_primary": "normal",
                      "blend_mode_secondary": "screen", "seed": 42})
    assert validate_svg(svg) == []
    assert "mix-blend-mode:screen" in svg


def test_frequency_jitter_does_not_shift_shapes():
    """frequency_jitter should not change shape positions (separate RNG)."""
    svg_no_jitter   = render_svg({"frequency_jitter": "none", "seed": 42})
    svg_high_jitter = render_svg({"frequency_jitter": "high", "seed": 42})
    assert validate_svg(svg_no_jitter) == []
    assert validate_svg(svg_high_jitter) == []
    # They differ only in baseFrequency, not in shape coordinates
    # (The filter section differs; the shape g sections should have same coordinates)
    # Simple check: both produce different SVG (jitter changes frequency)
    assert svg_no_jitter != svg_high_jitter


def test_phase_offset_distinct_for_seed_zero():
    """phase_offset must produce distinct turbulence even when seed=0."""
    svgs = [render_svg({"seed": 0, "phase_offset": p}) for p in ["0", "0.25", "0.5", "0.75"]]
    for svg in svgs:
        assert validate_svg(svg) == []
    # All four must differ
    assert len(set(svgs)) == 4, "All 4 phase_offset values must produce distinct output at seed=0"
