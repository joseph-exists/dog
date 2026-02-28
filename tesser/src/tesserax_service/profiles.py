from __future__ import annotations

import importlib.util
from typing import Any

from .contracts import RenderRequest
from .registry import ScriptSpec

FORMAT_CAPABILITIES: dict[str, set[str]] = {
    "svg": {"render.svg"},
    "gif": {"render.gif"},
    "mp4": {"render.mp4"},
    "png": {"render.png"},
    "pdf": {"render.pdf"},
    "ps": {"render.ps"},
}


def resolve_capabilities(spec: ScriptSpec, request: RenderRequest) -> set[str]:
    caps: set[str] = set(spec.base_capabilities)
    for fmt in request.formats:
        caps.update(FORMAT_CAPABILITIES.get(fmt.lower(), {f"render.{fmt.lower()}"}))
    if spec.resolve_capabilities is not None:
        caps.update(spec.resolve_capabilities(request.params, request.formats))
    return caps


def runtime_profile_for_capabilities(capabilities: set[str], default_profile: str) -> str:
    if any(cap.startswith("render.") and cap not in {"render.svg"} for cap in capabilities):
        return "export"
    return default_profile


def preflight_errors(profile: str, capabilities: set[str]) -> list[str]:
    errors: list[str] = []
    if profile != "export":
        return errors

    if not any(
        cap in capabilities for cap in {"render.gif", "render.mp4", "render.png", "render.pdf", "render.ps"}
    ):
        return errors

    if any(cap in capabilities for cap in {"render.gif", "render.mp4"}):
        if importlib.util.find_spec("imageio") is None:
            errors.append("Missing Python package: imageio")
        if importlib.util.find_spec("imageio_ffmpeg") is None:
            errors.append("Missing Python package: imageio_ffmpeg")

    if any(cap in capabilities for cap in {"render.png", "render.pdf", "render.ps"}):
        if importlib.util.find_spec("cairosvg") is None:
            errors.append("Missing Python package: cairosvg")
        if importlib.util.find_spec("cairocffi") is None:
            errors.append("Missing Python package: cairocffi")

    return errors


def explain_profile(profile: str) -> dict[str, Any]:
    if profile == "core":
        return {"profile": "core", "description": "Core rendering without export extras"}
    if profile == "export":
        return {"profile": "export", "description": "Rendering with animation/raster/vector export extras"}
    return {"profile": profile, "description": "Custom runtime profile"}

