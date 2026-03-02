from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import RenderResult
from .registry import ScriptSpec


def build_render_payload(result: RenderResult, spec: ScriptSpec) -> dict[str, Any]:
    render_payload: dict[str, Any] = {
        "format": "external",
        "artifacts": [artifact.to_dict() for artifact in result.artifacts],
        "manifest_path": result.manifest_path,
        "runtime_profile": result.runtime_profile,
        "resolved_capabilities": result.resolved_capabilities,
    }
    svg_artifact = next(
        (artifact for artifact in result.artifacts if artifact.media_type == "image/svg+xml"),
        None,
    )
    if svg_artifact is not None:
        svg_path = Path(svg_artifact.path)
        if svg_path.exists():
            render_payload["format"] = "svg"
            render_payload["svg"] = svg_path.read_text(encoding="utf-8")
    if spec.kind in {"runner", "utility"}:
        render_payload["format"] = render_payload.get("format", "external")
    return render_payload


def build_render_response(
    *,
    request_id: str | None,
    room_id: str | None,
    script_name: str,
    worker_id: str,
    completed_at: str,
    render: dict[str, Any],
    received_at: str | None = None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "room_id": room_id,
        "worker_id": worker_id,
        "script_name": script_name,
        "status": "ok",
        "type": "tesser.script.response",
        "render": render,
        "received_at": received_at,
        "completed_at": completed_at,
    }


def build_render_error_response(
    *,
    request_id: str | None,
    room_id: str | None,
    script_name: str | None,
    worker_id: str,
    completed_at: str,
    error: str,
    received_at: str | None = None,
) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "room_id": room_id,
        "worker_id": worker_id,
        "script_name": script_name,
        "status": "error",
        "type": "tesser.script.response",
        "error": error,
        "received_at": received_at,
        "completed_at": completed_at,
    }


def build_enqueue_response(
    *,
    request_id: str,
    script_name: str,
    worker_id: str,
    queued_at: str,
    runtime_profile: str,
    resolved_capabilities: list[str],
    room_id: str | None = None,
    status: str = "queued",
    render: dict[str, Any] | None = None,
    error: str | None = None,
    completed_at: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "request_id": request_id,
        "job_id": request_id,
        "room_id": room_id,
        "worker_id": worker_id,
        "script_name": script_name,
        "status": status,
        "type": "tesser.script.enqueue.response",
        "runtime_profile": runtime_profile,
        "resolved_capabilities": resolved_capabilities,
        "queued_at": queued_at,
    }
    if render is not None:
        payload["render"] = render
    if error is not None:
        payload["error"] = error
    if completed_at is not None:
        payload["completed_at"] = completed_at
    return payload


def build_job_status_response(
    *,
    request_id: str,
    job_id: str,
    worker_id: str,
    status: str,
    script_name: str | None = None,
    room_id: str | None = None,
    runtime_profile: str | None = None,
    resolved_capabilities: list[str] | None = None,
    queued_at: str | None = None,
    completed_at: str | None = None,
    render: dict[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "request_id": request_id,
        "job_id": job_id,
        "worker_id": worker_id,
        "status": status,
        "type": "tesser.script.status.response",
    }
    if script_name is not None:
        payload["script_name"] = script_name
    if room_id is not None:
        payload["room_id"] = room_id
    if runtime_profile is not None:
        payload["runtime_profile"] = runtime_profile
    if resolved_capabilities is not None:
        payload["resolved_capabilities"] = resolved_capabilities
    if queued_at is not None:
        payload["queued_at"] = queued_at
    if completed_at is not None:
        payload["completed_at"] = completed_at
    if render is not None:
        payload["render"] = render
    if error is not None:
        payload["error"] = error
    return payload
