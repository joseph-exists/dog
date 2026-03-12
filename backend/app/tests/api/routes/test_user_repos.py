"""Tests for user repository API endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.core.config import settings
from app.models import (
    ShadowRepoCommitSummary,
    ShadowRepoTreeEntry,
    User,
    UserCreate,
    UserRepoCommitResponse,
    UserRepo,
    UserRepoFileContent,
    UserRepoImportStatus,
    UserRepoOutboxJob,
    UserRepoReadmeContent,
    UserRepoViewResponse,
)
from app.services.user_repo_service import (
    UserRepoWriteConflict,
    UserRepoWriteNotReady,
    UserRepoWriteValidationError,
    user_repo_service,
)
from app.services.user_repo_view_service import (
    UserRepoBranchNotFound,
    user_repo_view_service,
)
from app.tests.utils.user import user_authentication_headers


def _create_user_with_headers(
    *,
    client: TestClient,
    db: Session,
) -> tuple[User, dict[str, str]]:
    email = f"user-repo-api-{uuid.uuid4()}@example.com"
    password = "password123"
    user_in = UserCreate(email=email, password=password)
    user = crud.create_user(session=db, user_create=user_in)
    return user, user_authentication_headers(
        client=client,
        email=email,
        password=password,
    )


def _create_user_repo(
    *,
    db: Session,
    owner: User,
    import_status: UserRepoImportStatus = UserRepoImportStatus.READY,
    is_private: bool = False,
) -> UserRepo:
    repo = UserRepo(
        owner_user_id=owner.id,
        slug=f"repo-{uuid.uuid4().hex[:8]}",
        display_name="Viewer Repo",
        description="Repo for viewer tests",
        source_repo_url="https://github.com/example/viewer-repo.git",
        source_branch=settings.USER_REPO_DEFAULT_BRANCH,
        import_status=import_status,
        import_error=None,
        imported_at=datetime.now(timezone.utc),
        gogs_repo_name=f"viewer-{uuid.uuid4().hex[:8]}",
        gogs_repo_id=123,
        gogs_full_name="dog/viewer",
        gogs_html_url="https://gogs.example/dog/viewer",
        is_private=is_private,
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


def test_create_user_repo_returns_accepted_with_importing_status(
    client: TestClient,
    db: Session,
) -> None:
    """
    POST /user-repos/ should return 202 Accepted with import_status=importing.

    The actual provisioning happens asynchronously via the outbox worker.
    """
    _, headers = _create_user_with_headers(client=client, db=db)

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
    _, headers = _create_user_with_headers(client=client, db=db)

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
    _, headers = _create_user_with_headers(client=client, db=db)

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
    _, headers = _create_user_with_headers(client=client, db=db)

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
    _, headers = _create_user_with_headers(client=client, db=db)

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
    owner, headers = _create_user_with_headers(client=client, db=db)

    repo = _create_user_repo(db=db, owner=owner)

    # Get the repo
    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == str(repo.id)
    assert payload["default_branch"] == settings.USER_REPO_DEFAULT_BRANCH
    assert payload["capabilities"]["has_file_tree"] is True
    assert payload["capabilities"]["has_blob_content"] is True
    assert payload["capabilities"]["has_commit_history"] is True
    assert payload["capabilities"]["has_branches"] is False


def test_get_user_repo_returns_404_for_nonexistent(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/{id} should return 404 for nonexistent repo."""
    _, headers = _create_user_with_headers(client=client, db=db)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{uuid.uuid4()}",
        headers=headers,
    )

    assert response.status_code == 404


def test_get_user_repo_returns_404_for_other_users_private_repo(
    client: TestClient,
    db: Session,
) -> None:
    """GET /user-repos/{id} should return opaque 404 for another user's private repo."""
    # User 1 creates a repo
    owner, _headers1 = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner, is_private=True)

    # User 2 tries to access it
    _, headers2 = _create_user_with_headers(client=client, db=db)
    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}",
        headers=headers2,
    )

    assert response.status_code == 404


def test_get_user_repo_allows_non_owner_to_read_shared_repo(
    client: TestClient,
    db: Session,
) -> None:
    owner, _ = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner, is_private=False)
    _, other_headers = _create_user_with_headers(client=client, db=db)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}",
        headers=other_headers,
    )

    assert response.status_code == 200
    assert response.json()["id"] == str(repo.id)


def test_get_user_repo_tree_returns_repo_projection(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    def _fake_get_repo_view(*, session, repo_id, path="", ref=None, commit_limit=10):
        assert repo_id == repo.id
        assert path == "src"
        assert ref is None
        assert commit_limit == 5
        return UserRepoViewResponse(
            summary={
                "repo_id": repo.id,
                "slug": repo.slug,
                "display_name": repo.display_name,
                "repo_available": True,
                "default_branch": settings.USER_REPO_DEFAULT_BRANCH,
                "latest_commit_sha": "abc12345",
                "latest_commit_message": "Initial import",
                "latest_commit_authored_at": datetime.now(timezone.utc),
            },
            commits=[
                ShadowRepoCommitSummary(
                    sha="abc12345",
                    short_sha="abc12345",
                    message="Initial import",
                    author_name="repo-owner",
                )
            ],
            tree=[
                ShadowRepoTreeEntry(
                    path="src/index.ts",
                    name="index.ts",
                    entry_type="file",
                    size_bytes=42,
                )
            ],
            tree_root_path="src",
            ref=settings.USER_REPO_DEFAULT_BRANCH,
        )

    monkeypatch.setattr(user_repo_view_service, "get_repo_view", _fake_get_repo_view)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/tree",
        params={"path": "src", "commit_limit": 5},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["repo_id"] == str(repo.id)
    assert payload["tree_root_path"] == "src"
    assert payload["tree"][0]["path"] == "src/index.ts"


def test_get_user_repo_tree_allows_zero_commit_limit(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    def _fake_get_repo_view(*, session, repo_id, path="", ref=None, commit_limit=10):
        assert repo_id == repo.id
        assert path == ""
        assert ref is None
        assert commit_limit == 0
        return UserRepoViewResponse(
            summary={
                "repo_id": repo.id,
                "slug": repo.slug,
                "display_name": repo.display_name,
                "repo_available": True,
                "default_branch": settings.USER_REPO_DEFAULT_BRANCH,
            },
            commits=[],
            tree=[],
            tree_root_path="",
            ref=settings.USER_REPO_DEFAULT_BRANCH,
        )

    monkeypatch.setattr(user_repo_view_service, "get_repo_view", _fake_get_repo_view)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/tree",
        params={"commit_limit": 0},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["commits"] == []


def test_get_user_repo_file_returns_preview_flags(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    def _fake_get_file_content(*, session, repo_id, path, ref=None):
        assert repo_id == repo.id
        assert path == "README.md"
        return UserRepoFileContent(
            path="README.md",
            ref=settings.USER_REPO_DEFAULT_BRANCH,
            content="# Hello\n",
            encoding="utf-8",
            size_bytes=8,
            content_type="text/markdown",
            is_binary=False,
            is_truncated=False,
            truncation_reason=None,
            is_unsupported_preview=False,
        )

    monkeypatch.setattr(
        user_repo_view_service,
        "get_file_content",
        _fake_get_file_content,
    )

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/file",
        params={"path": "README.md"},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "README.md"
    assert payload["is_binary"] is False
    assert payload["is_truncated"] is False


def test_get_user_repo_readme_returns_resolved_content(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    def _fake_get_readme(*, session, repo_id, ref=None):
        assert repo_id == repo.id
        return UserRepoReadmeContent(
            path="README.md",
            ref=settings.USER_REPO_DEFAULT_BRANCH,
            content="# Repo\n",
            encoding="utf-8",
            size_bytes=7,
            content_type="text/markdown",
            is_binary=False,
            is_truncated=False,
            truncation_reason=None,
            is_unsupported_preview=False,
            resolved_from_path="README.md",
        )

    monkeypatch.setattr(user_repo_view_service, "get_readme", _fake_get_readme)

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/readme",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resolved_from_path"] == "README.md"
    assert payload["content"] == "# Repo\n"


def test_get_user_repo_tree_rejects_unsupported_branch(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    monkeypatch.setattr(
        user_repo_view_service,
        "get_repo_view",
        lambda **kwargs: (_ for _ in ()).throw(UserRepoBranchNotFound("Branch not found")),
    )

    response = client.get(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/tree",
        params={"ref": "develop"},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error_code"] == "BRANCH_NOT_FOUND"


def test_commit_user_repo_changes_returns_commit_summary(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    def _fake_commit_user_repo_changes(
        *,
        session,
        repo_id,
        actor_user_id,
        branch,
        mutations,
        commit_message,
        expected_head_sha,
        is_superuser=False,
    ):
        assert repo_id == repo.id
        assert actor_user_id == owner.id
        assert branch == "main"
        assert expected_head_sha == "abc123"
        assert commit_message == "Update README"
        assert len(mutations) == 1
        assert mutations[0].path == "README.md"
        return UserRepoCommitResponse(
            repo_id=repo.id,
            branch="main",
            previous_head_sha="abc123",
            new_head_sha="def456",
            commit_message=commit_message,
            committed_at=datetime.now(timezone.utc),
            changed_paths=["README.md"],
        )

    monkeypatch.setattr(
        user_repo_service,
        "commit_user_repo_changes",
        _fake_commit_user_repo_changes,
    )

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/commits",
        headers=headers,
        json={
            "branch": "main",
            "mutations": [
                {
                    "path": "README.md",
                    "operation": "upsert",
                    "content": "# Hello\n",
                }
            ],
            "commit_message": "Update README",
            "expected_head_sha": "abc123",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["repo_id"] == str(repo.id)
    assert payload["previous_head_sha"] == "abc123"
    assert payload["new_head_sha"] == "def456"
    assert payload["changed_paths"] == ["README.md"]


def test_commit_user_repo_changes_returns_409_for_stale_head(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    monkeypatch.setattr(
        user_repo_service,
        "commit_user_repo_changes",
        lambda **kwargs: (_ for _ in ()).throw(
            UserRepoWriteConflict("Repo head no longer matches expected_head_sha")
        ),
    )

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/commits",
        headers=headers,
        json={
            "branch": "main",
            "mutations": [
                {
                    "path": "README.md",
                    "operation": "upsert",
                    "content": "# Hello\n",
                }
            ],
            "commit_message": "Update README",
            "expected_head_sha": "abc123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "HEAD_CONFLICT"


def test_commit_user_repo_changes_returns_409_for_not_ready_repo(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(
        db=db,
        owner=owner,
        import_status=UserRepoImportStatus.IMPORTING,
    )

    monkeypatch.setattr(
        user_repo_service,
        "commit_user_repo_changes",
        lambda **kwargs: (_ for _ in ()).throw(
            UserRepoWriteNotReady("User repo is not ready for writes")
        ),
    )

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/commits",
        headers=headers,
        json={
            "branch": "main",
            "mutations": [
                {
                    "path": "README.md",
                    "operation": "upsert",
                    "content": "# Hello\n",
                }
            ],
            "commit_message": "Update README",
            "expected_head_sha": "abc123",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["error_code"] == "REPO_NOT_READY"


def test_commit_user_repo_changes_returns_422_for_invalid_request(
    client: TestClient,
    db: Session,
    monkeypatch,
) -> None:
    owner, headers = _create_user_with_headers(client=client, db=db)
    repo = _create_user_repo(db=db, owner=owner)

    monkeypatch.setattr(
        user_repo_service,
        "commit_user_repo_changes",
        lambda **kwargs: (_ for _ in ()).throw(
            UserRepoWriteValidationError("Invalid repo path: ../README.md")
        ),
    )

    response = client.post(
        f"{settings.API_V1_STR}/user-repos/{repo.id}/commits",
        headers=headers,
        json={
            "branch": "main",
            "mutations": [
                {
                    "path": "../README.md",
                    "operation": "upsert",
                    "content": "# Hello\n",
                }
            ],
            "commit_message": "Update README",
            "expected_head_sha": "abc123",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["error_code"] == "INVALID_WRITE_REQUEST"
