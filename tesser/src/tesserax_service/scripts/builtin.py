from __future__ import annotations

from pathlib import Path

from tesserax_service.registry import register_script
from tesserax_service.scripts.svg_compose import render_svg, validate_svg, INPUT_SCHEMA


def _demo_logo_caps(params: dict[str, object], formats: list[str]) -> set[str]:
    extra: set[str] = set()
    animate = bool(params.get("animate", False))
    if animate and "gif" in formats:
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
    fill = str(params.get("fill", "#0f766e"))

    output_path = output_dir / f"{basename}.svg"
    output_path.write_text(
        (
            "<svg xmlns='http://www.w3.org/2000/svg' width='680' height='220' "
            "viewBox='0 0 680 220'>"
            "<rect width='680' height='220' fill='#f8fafc'/>"
            f"<circle cx='120' cy='110' r='60' fill='{fill}'/>"
            f"<text x='210' y='122' font-size='42' font-family='sans-serif' fill='#0f172a'>{title}</text>"
            "</svg>"
        ),
        encoding="utf-8",
    )
    return [output_path]


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
    """Full creative SVG renderer. 30 tunable knobs. Pass {} for a beautiful default."""
    if "svg" not in formats:
        raise ValueError("svg.compose supports only svg output")
    output_dir.mkdir(parents=True, exist_ok=True)
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
    def _fn(
        params: dict[str, object], output_dir: Path, basename: str, formats: list[str]
    ) -> list[Path]:
        if "svg" not in formats:
            raise ValueError(f"{script_id} supports only svg output")
        output_dir.mkdir(parents=True, exist_ok=True)
        merged = {**defaults, **{k: v for k, v in params.items() if k == "seed"}}
        svg = render_svg(merged)
        errors = validate_svg(svg)
        if errors:
            raise ValueError(f"{script_id} produced invalid SVG: {errors}")
        out = output_dir / f"{basename}.svg"
        out.write_text(svg, encoding="utf-8")
        return [out]

    _fn.__doc__ = f"Preset: {script_id}"
    _fn.__tesser_input_schema__ = _PRESET_SCHEMA  # type: ignore[attr-defined]
    return _fn


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
