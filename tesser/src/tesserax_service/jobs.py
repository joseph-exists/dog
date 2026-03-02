from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .contracts import RenderRequest
from .profiles import resolve_capabilities, runtime_profile_for_capabilities
from .registry import ScriptSpec, get_script_spec


def resolve_render_request(
    request: RenderRequest, *, require_enabled: bool = True
) -> tuple[ScriptSpec, set[str], str]:
    spec = get_script_spec(request.script_id)
    if require_enabled and not spec.enabled:
        reason = spec.disabled_reason or "Script disabled"
        raise RuntimeError(f"script_id '{request.script_id}' is disabled: {reason}")

    capabilities = resolve_capabilities(spec, request)
    resolved_profile = runtime_profile_for_capabilities(
        capabilities, default_profile=spec.default_runtime_profile
    )
    if request.runtime_profile is not None and request.runtime_profile != resolved_profile:
        raise RuntimeError(
            f"runtime_profile mismatch: requested='{request.runtime_profile}' "
            f"resolved='{resolved_profile}'"
        )
    return spec, capabilities, resolved_profile


def enqueue_render_job(
    request: RenderRequest,
    jobs_root: str | Path,
    *,
    require_enabled: bool = True,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    spec, capabilities, resolved_profile = resolve_render_request(
        request, require_enabled=require_enabled
    )
    request_id = request.request_id or str(uuid.uuid4())

    jobs_dir = Path(jobs_root) / resolved_profile
    jobs_dir.mkdir(parents=True, exist_ok=True)

    job_payload: dict[str, Any] = {
        "script_id": request.script_id,
        "params": request.params,
        "output_dir": request.output_dir,
        "formats": request.formats,
        "basename": request.basename,
        "request_id": request_id,
        "runtime_profile": resolved_profile,
        "resolved_capabilities": sorted(capabilities),
    }
    if extra_fields:
        job_payload.update(extra_fields)

    job_path = jobs_dir / f"{request_id}.json"
    job_path.write_text(json.dumps(job_payload, indent=2), encoding="utf-8")
    return {
        "job_path": str(job_path),
        "request_id": request_id,
        "runtime_profile": resolved_profile,
        "resolved_capabilities": sorted(capabilities),
        "spec": spec,
    }


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected object payload in {path}")
    return payload


def _job_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    meta = payload.get("job_metadata")
    if isinstance(meta, dict):
        return meta
    return {}


def write_job_status_snapshot(
    jobs_root: str | Path,
    runtime_profile: str,
    job_id: str,
    payload: dict[str, Any],
) -> Path:
    archive_dir = Path(jobs_root) / "archive" / runtime_profile
    archive_dir.mkdir(parents=True, exist_ok=True)
    status_path = archive_dir / f"{job_id}.status.json"
    status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return status_path


def get_job_status(job_id: str, jobs_root: str | Path) -> dict[str, Any] | None:
    root = Path(jobs_root)
    for runtime_profile in ("core", "export"):
        status_path = root / "archive" / runtime_profile / f"{job_id}.status.json"
        if status_path.exists():
            payload = _read_json(status_path)
            payload.setdefault("job_id", job_id)
            payload.setdefault("runtime_profile", runtime_profile)
            return payload

        processing_path = root / runtime_profile / f"{job_id}.processing"
        if processing_path.exists():
            payload = _read_json(processing_path)
            meta = _job_metadata(payload)
            return {
                "job_id": job_id,
                "script_name": str(meta.get("script_name") or payload.get("script_id") or ""),
                "room_id": (
                    str(meta.get("room_id")) if meta.get("room_id") is not None else None
                ),
                "status": "running",
                "runtime_profile": runtime_profile,
                "resolved_capabilities": payload.get("resolved_capabilities", []),
                "queued_at": str(meta.get("queued_at") or _now_iso()),
            }

        queued_path = root / runtime_profile / f"{job_id}.json"
        if queued_path.exists():
            payload = _read_json(queued_path)
            meta = _job_metadata(payload)
            return {
                "job_id": job_id,
                "script_name": str(meta.get("script_name") or payload.get("script_id") or ""),
                "room_id": (
                    str(meta.get("room_id")) if meta.get("room_id") is not None else None
                ),
                "status": "queued",
                "runtime_profile": runtime_profile,
                "resolved_capabilities": payload.get("resolved_capabilities", []),
                "queued_at": str(meta.get("queued_at") or _now_iso()),
            }

    return None
