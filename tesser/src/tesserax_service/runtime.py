from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .contracts import RenderArtifact, RenderRequest, RenderResult
from .jobs import resolve_render_request
from .profiles import preflight_errors
from .registry import get_script
from . import scripts as _scripts  # noqa: F401

_MEDIA_TYPES: dict[str, str] = {
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".gif": "image/gif",
    ".mp4": "video/mp4",
    ".json": "application/json",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 64), b""):
            digest.update(chunk)
    return digest.hexdigest()


def execute_render(request: RenderRequest) -> RenderResult:
    output_dir = Path(request.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _, capabilities, resolved_profile = resolve_render_request(request)

    errors = preflight_errors(resolved_profile, capabilities)
    if errors:
        raise RuntimeError(
            f"Preflight failed for profile '{resolved_profile}': " + "; ".join(errors)
        )

    script = get_script(request.script_id)
    artifact_paths = script(request.params, output_dir, request.basename, request.formats)
    if not artifact_paths:
        raise RuntimeError("Script execution produced no artifacts")

    artifacts: list[RenderArtifact] = []
    for path in artifact_paths:
        extension = path.suffix.lower()
        media_type = _MEDIA_TYPES.get(extension, "application/octet-stream")
        artifacts.append(
            RenderArtifact(
                path=str(path),
                media_type=media_type,
                size_bytes=path.stat().st_size,
                sha256=_sha256(path),
            )
        )

    manifest = {
        "script_id": request.script_id,
        "request_id": request.request_id,
        "runtime_profile": resolved_profile,
        "resolved_capabilities": sorted(capabilities),
        "artifacts": [artifact.to_dict() for artifact in artifacts],
    }
    manifest_path = output_dir / f"{request.basename}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return RenderResult(
        script_id=request.script_id,
        status="completed",
        request_id=request.request_id,
        runtime_profile=resolved_profile,
        resolved_capabilities=sorted(capabilities),
        artifacts=artifacts,
        manifest_path=str(manifest_path),
    )
