"""Tests for user repository API endpoints."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import UserCreate, UserRepoImportStatus, UserRepoOutboxJob
from app.tests.utils.user import user_authentication_headers


def _create_user_with_headers(*, client: TestClient, db: Session) -> dict[str, str]:
    email = f"user-repo-api-{uuid.uuid4()}@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password)
    crud.create_user(session=db, user_create=user_in)
    return user_authentication_headers(client=client, email=email, password=password)


def test_create_user_repo_returns_accepted_with_importing_status(
    client: TestClient,
    db: Session,
) -> None:
    """
    POST /user-repos/ should return 202 Accepted with import_status=importing.

    The actual provisioning happens asynchronously via the outbox worker.
    """
    headers = _create_user_with_headers(client=client, db=db)

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={
            "source_repo_url": "https://github.com/example/platform-repo.git",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["display_name"] == "platform-repo"
    assert payload["slug"].startswith("platform-repo")
    assert payload["source_repo_url"] == "https://github.com/example/platform-repo.git"
    assert payload["source_branch"] == "main"
    assert payload["import_status"] == UserRepoImportStatus.IMPORTING
    assert payload["import_error"] is None
    # Gogs metadata not set yet (will be set by worker)
    assert payload["gogs_repo_id"] is None


def test_create_user_repo_creates_outbox_job(
    client: TestClient,
    db: Session,
) -> None:
    """
    POST /user-repos/ should create an outbox job for async processing.
    """
    headers = _create_user_with_headers(client=client, db=db)

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={
            "source_repo_url": "https://github.com/example/async-test-repo.git",
        },
    )

    assert response.status_code == 202
    repo_id = uuid.UUID(response.json()["id"])

    # Verify outbox job was created
    job = db.exec(
        select(UserRepoOutboxJob).where(UserRepoOutboxJob.user_repo_id == repo_id)
    ).first()

    assert job is not None
    assert job.status == "queued"
    assert job.attempt_count == 0


def test_create_user_repo_rejects_non_https_urls(
    client: TestClient,
    db: Session,
) -> None:
    """Non-HTTPS URLs should be rejected with 422."""
    headers = _create_user_with_headers(client=client, db=db)

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={
            "source_repo_url": "http://github.com/example/platform-repo.git",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Only https repository URLs are supported"


def test_create_user_repo_with_custom_display_name(
    client: TestClient,
    db: Session,
) -> None:
    """Custom display_name should be preserved."""
    headers = _create_user_with_headers(client=client, db=db)

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={
            "source_repo_url": "https://github.com/example/some-repo.git",
            "display_name": "My Custom Name",
            "description": "A test repository",
        },
    )

    assert response.status_code == 202
    payload = response.json()
    assert payload["display_name"] == "My Custom Name"
    assert payload["description"] == "A test repository"


def test_list_user_repos_returns_only_owned_repos(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/ should only return repos owned by the current user."""
    headers = _create_user_with_headers(client=client, db=db)

    # Create a repo
    client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={"source_repo_url": "https://github.com/example/list-test.git"},
    )

    # List repos
    response = client.get(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert any(r["source_repo_url"] == "https://github.com/example/list-test.git" for r in payload["data"])


def test_get_user_repo_by_id(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/{id} should return the repo details."""
    headers = _create_user_with_headers(client=client, db=db)

    # Create a repo
    create_response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers,
        json={"source_repo_url": "https://github.com/example/get-test.git"},
    )
    repo_id = create_response.json()["id"]

    # Get the repo
    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == repo_id


def test_get_user_repo_returns_404_for_nonexistent(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/{id} should return 404 for nonexistent repo."""
    headers = _create_user_with_headers(client=client, db=db)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{uuid.uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_user_repo_returns_403_for_other_users_repo(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/{id} should return 403 for another user's repo."""
    # User 1 creates a repo
    headers1 = _create_user_with_headers(client=client, db=db)
    create_response = client.post(
        f"{settings.API_V1_STR}/user-repos/",
        headers=headers1,
        json={"source_repo_url": "https://github.com/example/private-test.git"},
    )
    repo_id = create_response.json()["id"]

    # User 2 tries to access it
    headers2 = _create_user_with_headers(client=client, db=db)
    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo_id}",
        headers=headers2,
    )

    assert response.status_code == 403
