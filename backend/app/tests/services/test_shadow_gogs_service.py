from __future__ import annotations

import uuid

import httpx

from app.models import ShadowRepo
from app.services.shadow_gogs_service import (
    ShadowGogsProvisioningError,
    shadow_gogs_service,
)


def _repo(owner_id: uuid.UUID, entity_id: uuid.UUID) -> ShadowRepo:
    return ShadowRepo(
        owner_id=owner_id,
        entity_type="agent",
        entity_id=entity_id,
        forgejo_repo_name=f"agent-{entity_id}",
        forgejo_repo_id=None,
    )


def test_ensure_shadow_repo_remote_noops_without_config(db, monkeypatch) -> None:
    owner_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    repo = _repo(owner_id, entity_id)

    monkeypatch.setattr("app.services.shadow_gogs_service.settings.SHADOW_GOGS_BASE_URL", None)
    monkeypatch.setattr("app.services.shadow_gogs_service.settings.SHADOW_GOGS_TOKEN", None)

    result = shadow_gogs_service.ensure_shadow_repo_remote(session=db, shadow_repo=repo)
    assert result is None


def test_ensure_shadow_repo_remote_returns_existing_repo(db, monkeypatch) -> None:
    owner_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    repo = _repo(owner_id, entity_id)

    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        shadow_gogs_service,
        "_get_repo",
        lambda repo_name: shadow_gogs_service._parse_repo(
            httpx.Response(
                200,
                json={
                    "id": 42,
                    "name": repo_name,
                    "full_name": f"shadow/{repo_name}",
                    "ssh_url": f"ssh://git@gittin:2222/shadow/{repo_name}.git",
                    "html_url": f"http://gittin:3000/shadow/{repo_name}",
                },
            )
        ),
    )

    result = shadow_gogs_service.ensure_shadow_repo_remote(session=db, shadow_repo=repo)
    assert result is not None
    assert result.repo_id == 42
    assert repo.forgejo_repo_id == 42


def test_ensure_shadow_repo_remote_creates_missing_repo(db, monkeypatch) -> None:
    owner_id = uuid.uuid4()
    entity_id = uuid.uuid4()
    repo = _repo(owner_id, entity_id)

    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(shadow_gogs_service, "_get_repo", lambda repo_name: None)
    monkeypatch.setattr(
        shadow_gogs_service,
        "_create_repo",
        lambda repo_name: shadow_gogs_service._parse_repo(
            httpx.Response(
                201,
                json={
                    "id": 99,
                    "name": repo_name,
                    "full_name": f"shadow/{repo_name}",
                    "ssh_url": f"ssh://git@gittin:2222/shadow/{repo_name}.git",
                    "html_url": f"http://gittin:3000/shadow/{repo_name}",
                },
            )
        ),
    )

    result = shadow_gogs_service.ensure_shadow_repo_remote(session=db, shadow_repo=repo)
    assert result is not None
    assert result.repo_id == 99
    assert repo.forgejo_repo_id == 99


def test_create_repo_raises_on_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_TOKEN",
        "test-token",
    )

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, path: str, json: dict[str, object]) -> httpx.Response:
            return httpx.Response(500, text="boom")

    monkeypatch.setattr(shadow_gogs_service, "_client", lambda: FakeClient())

    try:
        shadow_gogs_service._create_repo("agent-test")
    except ShadowGogsProvisioningError as exc:
        assert "POST /api/v1/org/shadow/repos returned 500" in str(exc)
        assert "Response summary: boom" in str(exc)
    else:
        raise AssertionError("Expected ShadowGogsProvisioningError")


def test_create_repo_reports_html_auth_failure(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.shadow_gogs_service.settings.SHADOW_GOGS_TOKEN",
        "test-token",
    )

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, path: str, json: dict[str, object]) -> httpx.Response:
            return httpx.Response(
                404,
                headers={"content-type": "text/html; charset=utf-8"},
                text="<html><title>Page Not Found</title></html>",
            )

    monkeypatch.setattr(shadow_gogs_service, "_client", lambda: FakeClient())

    try:
        shadow_gogs_service._create_repo("agent-test")
    except ShadowGogsProvisioningError as exc:
        assert "POST /api/v1/org/shadow/repos returned 404" in str(exc)
        assert "Response summary: HTML page: Page Not Found" in str(exc)
    else:
        raise AssertionError("Expected ShadowGogsProvisioningError")
