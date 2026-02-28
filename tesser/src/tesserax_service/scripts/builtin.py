from __future__ import annotations

from pathlib import Path

from tesserax_service.registry import register_script


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
