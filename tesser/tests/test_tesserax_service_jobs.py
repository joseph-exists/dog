from __future__ import annotations

import json

from tesserax_service.contracts import RenderArtifact, RenderRequest, RenderResult
from tesserax_service.jobs import enqueue_render_job, get_job_status, write_job_status_snapshot
from tesserax_service.redis_messages import (
    build_render_error_response,
    build_render_payload,
    build_render_response,
)
from tesserax_service.registry import get_script_spec
from tesserax_service import scripts as _scripts  # noqa: F401


def test_enqueue_render_job_routes_core_script(tmp_path) -> None:
    request = RenderRequest(
        script_id="demo.logo",
        params={"title": "Queue me"},
        output_dir=str(tmp_path / "artifacts"),
        formats=["svg"],
        basename="render",
        request_id="req-123",
    )

    queued = enqueue_render_job(request, tmp_path / "jobs")

    assert queued["request_id"] == "req-123"
    assert queued["runtime_profile"] == "core"
    assert queued["resolved_capabilities"] == ["render.svg"]

    job_path = tmp_path / "jobs" / "core" / "req-123.json"
    assert queued["job_path"] == str(job_path)
    payload = json.loads(job_path.read_text(encoding="utf-8"))
    assert payload["script_id"] == "demo.logo"
    assert payload["runtime_profile"] == "core"


def test_enqueue_render_job_routes_export_script(tmp_path) -> None:
    request = RenderRequest(
        script_id="examples.animation.operations.hybrid_control_systems",
        params={},
        output_dir=str(tmp_path / "artifacts"),
        formats=["gif"],
        basename="render",
        request_id="req-export",
    )

    queued = enqueue_render_job(request, tmp_path / "jobs")

    assert queued["request_id"] == "req-export"
    assert queued["runtime_profile"] == "export"
    assert "render.gif" in queued["resolved_capabilities"]


def test_build_render_messages_include_svg_payload(tmp_path) -> None:
    svg_path = tmp_path / "render.svg"
    svg_path.write_text("<svg/>", encoding="utf-8")
    result = RenderResult(
        script_id="demo.logo",
        status="completed",
        request_id="req-1",
        runtime_profile="core",
        resolved_capabilities=["render.svg"],
        artifacts=[
            RenderArtifact(
                path=str(svg_path),
                media_type="image/svg+xml",
                size_bytes=svg_path.stat().st_size,
                sha256="abc",
            )
        ],
        manifest_path=str(tmp_path / "render.manifest.json"),
    )
    spec = get_script_spec("demo.logo")

    render = build_render_payload(result, spec)
    response = build_render_response(
        request_id="req-1",
        room_id="room-1",
        script_name="demo.logo",
        worker_id="worker-core",
        completed_at="2026-03-02T00:00:00Z",
        render=render,
        received_at="2026-03-02T00:00:00Z",
    )
    error = build_render_error_response(
        request_id="req-1",
        room_id="room-1",
        script_name="demo.logo",
        worker_id="worker-core",
        completed_at="2026-03-02T00:00:01Z",
        error="boom",
        received_at="2026-03-02T00:00:00Z",
    )

    assert render["format"] == "svg"
    assert render["svg"] == "<svg/>"
    assert response["status"] == "ok"
    assert response["render"]["svg"] == "<svg/>"
    assert error["status"] == "error"
    assert error["error"] == "boom"


def test_get_job_status_reads_queue_and_archive(tmp_path) -> None:
    request = RenderRequest(
        script_id="demo.logo",
        params={},
        output_dir=str(tmp_path / "artifacts"),
        formats=["svg"],
        basename="render",
        request_id="req-status",
    )
    enqueue_render_job(
        request,
        tmp_path / "jobs",
        extra_fields={
            "job_metadata": {
                "script_name": "demo.logo",
                "room_id": "room-1",
                "queued_at": "2026-03-02T00:00:00Z",
            }
        },
    )

    queued = get_job_status("req-status", tmp_path / "jobs")
    assert queued is not None
    assert queued["status"] == "queued"
    assert queued["runtime_profile"] == "core"

    write_job_status_snapshot(
        tmp_path / "jobs",
        "core",
        "req-status",
        {
            "job_id": "req-status",
            "script_name": "demo.logo",
            "status": "completed",
            "worker_id": "worker-core",
            "runtime_profile": "core",
            "resolved_capabilities": ["render.svg"],
            "queued_at": "2026-03-02T00:00:00Z",
            "completed_at": "2026-03-02T00:00:01Z",
            "render": {"format": "svg", "svg": "<svg/>"},
        },
    )

    completed = get_job_status("req-status", tmp_path / "jobs")
    assert completed is not None
    assert completed["status"] == "completed"
    assert completed["render"]["svg"] == "<svg/>"
