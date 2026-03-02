from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.config import settings


def test_enqueue_tesser_script_route(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    async def _fake_enqueue_tesser(**kwargs):
        assert kwargs["script_name"] == "examples.animation.operations.hybrid_control_systems"
        return {
            "request_id": "job-123",
            "job_id": "job-123",
            "status": "queued",
            "runtime_profile": "export",
            "resolved_capabilities": ["render.gif"],
            "queued_at": "2026-03-02T00:00:00Z",
            "worker_id": "tesser-worker-1",
        }

    monkeypatch.setattr("app.api.routes.tesser.enqueue_tesser", _fake_enqueue_tesser)

    response = client.post(
        f"{settings.API_V1_STR}/tesser/scripts/examples.animation.operations.hybrid_control_systems/enqueue",
        headers=superuser_token_headers,
        json={"script_input": {"format": "gif"}, "room_id": "room-1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job-123"
    assert data["status"] == "queued"
    assert data["runtime_profile"] == "export"


def test_get_tesser_job_status_route(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    async def _fake_get_tesser_job_status(**kwargs):
        assert kwargs["job_id"] == "job-123"
        return {
            "request_id": "status-req-1",
            "job_id": "job-123",
            "status": "completed",
            "script_name": "examples.animation.operations.hybrid_control_systems",
            "runtime_profile": "export",
            "resolved_capabilities": ["render.gif"],
            "queued_at": "2026-03-02T00:00:00Z",
            "completed_at": "2026-03-02T00:00:05Z",
            "render": {"format": "external", "runtime_profile": "export"},
            "worker_id": "tesser-worker-export",
        }

    monkeypatch.setattr("app.api.routes.tesser.get_tesser_job_status", _fake_get_tesser_job_status)

    response = client.get(
        f"{settings.API_V1_STR}/tesser/jobs/job-123",
        headers=superuser_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == "job-123"
    assert data["status"] == "completed"
    assert data["worker_id"] == "tesser-worker-export"


def test_get_tesser_job_status_route_404(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    monkeypatch,
) -> None:
    async def _fake_get_tesser_job_status(**kwargs):
        return {
            "request_id": "status-req-2",
            "job_id": kwargs["job_id"],
            "status": "not_found",
            "error": "Unknown tesser job 'missing-job'",
        }

    monkeypatch.setattr("app.api.routes.tesser.get_tesser_job_status", _fake_get_tesser_job_status)

    response = client.get(
        f"{settings.API_V1_STR}/tesser/jobs/missing-job",
        headers=superuser_token_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown tesser job 'missing-job'"
