from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import uuid

import httpx

from app import crud
from app.models import UserCreate, UserRepoImportStatus
from app.services.user_repo_service import (
    UserRepoCommitResult,
    UserRepoFileMutation,
    UserRepoWriteConflict,
    UserRepoWriteNotReady,
    UserRepoWriteUnauthorized,
    UserRepoWriteUnsupportedBranch,
    UserRepoWriteValidationError,
    UserRepoWriteFailed,
    user_repo_service,
)


def _create_user(db):
    user_in = UserCreate(
        email=f"user-repo-{uuid.uuid4()}@example.com",
        password="password123",
    )
    return crud.create_user(session=db, user_create=user_in)


def test_create_user_repo_db_only_supports_multiple_repos_per_user(db) -> None:
    owner = _create_user(db)

    repo_one = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="First Repo",
        slug="friendly-name",
    )
    repo_two = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Second Repo",
        slug="friendly-name",
    )

    assert repo_one.owner_user_id == owner.id
    assert repo_two.owner_user_id == owner.id
    assert repo_one.gogs_repo_name != repo_two.gogs_repo_name
    assert repo_one.gogs_repo_name.startswith("friendly-name-")
    assert repo_two.gogs_repo_name.startswith("friendly-name-")


def test_ensure_user_repo_remote_updates_remote_metadata(db, monkeypatch) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Launch Plan",
        slug="launch-plan",
    )

    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        user_repo_service,
        "_get_repo",
        lambda repo_name: None,
    )
    monkeypatch.setattr(
        user_repo_service,
        "_create_repo",
        lambda user_repo: user_repo_service._parse_repo(
            httpx.Response(
                201,
                json={
                    "id": 123,
                    "name": user_repo.gogs_repo_name,
                    "full_name": f"dog/{user_repo.gogs_repo_name}",
                    "ssh_url": f"ssh://git@gittin:2222/dog/{user_repo.gogs_repo_name}.git",
                    "html_url": f"http://gittin:3000/dog/{user_repo.gogs_repo_name}",
                },
            )
        ),
    )

    remote = user_repo_service.ensure_user_repo_remote(session=db, user_repo=repo)
    assert remote is not None
    assert repo.gogs_repo_id == 123
    assert repo.gogs_full_name == f"dog/{repo.gogs_repo_name}"
    assert repo.gogs_html_url == f"http://gittin:3000/dog/{repo.gogs_repo_name}"
    assert repo.import_status == UserRepoImportStatus.READY
    assert repo.import_error is None
    assert repo.imported_at is not None


def test_ensure_user_repo_remote_marks_empty_repo_ready(db, monkeypatch) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Blank Repo",
        slug="blank-repo",
    )

    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(
        user_repo_service,
        "_get_repo",
        lambda repo_name: None,
    )
    monkeypatch.setattr(
        user_repo_service,
        "_create_repo",
        lambda user_repo: user_repo_service._parse_repo(
            httpx.Response(
                201,
                json={
                    "id": 789,
                    "name": user_repo.gogs_repo_name,
                    "full_name": f"dog/{user_repo.gogs_repo_name}",
                    "ssh_url": f"ssh://git@gittin:2222/dog/{user_repo.gogs_repo_name}.git",
                    "html_url": f"http://gittin:3000/dog/{user_repo.gogs_repo_name}",
                },
            )
        ),
    )

    remote = user_repo_service.ensure_user_repo_remote(session=db, user_repo=repo)

    assert remote is not None
    assert repo.gogs_repo_id == 789
    assert repo.import_status == UserRepoImportStatus.READY
    assert repo.import_error is None
    assert repo.imported_at is not None


def test_clone_user_repo_from_external_source_derives_contract_and_marks_ready(
    db,
    monkeypatch,
) -> None:
    owner = _create_user(db)

    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_TOKEN",
        "test-token",
    )
    monkeypatch.setattr(user_repo_service, "_get_repo", lambda repo_name: None)
    monkeypatch.setattr(user_repo_service, "_get_org_id", lambda org_name: 7)
    monkeypatch.setattr(
        user_repo_service,
        "_migrate_repo",
        lambda user_repo: user_repo_service._parse_repo(
            httpx.Response(
                201,
                json={
                    "id": 456,
                    "name": user_repo.gogs_repo_name,
                    "full_name": f"dog/{user_repo.gogs_repo_name}",
                    "ssh_url": f"ssh://git@gittin:2222/dog/{user_repo.gogs_repo_name}.git",
                    "html_url": f"http://gittin:3000/dog/{user_repo.gogs_repo_name}",
                },
            )
        ),
    )

    repo = user_repo_service.clone_user_repo_from_external_source(
        session=db,
        owner=owner,
        source_repo_url="https://github.com/example/platform-repo.git",
    )

    assert repo.display_name == "platform-repo"
    assert repo.slug.startswith("platform-repo")
    assert repo.source_repo_url == "https://github.com/example/platform-repo.git"
    assert repo.source_branch == "main"
    assert repo.import_status == UserRepoImportStatus.READY
    assert repo.import_error is None
    assert repo.imported_at is not None
    assert repo.gogs_repo_id == 456


def test_clone_user_repo_from_external_source_rejects_non_https_urls(db) -> None:
    owner = _create_user(db)

    try:
        user_repo_service.clone_user_repo_from_external_source(
            session=db,
            owner=owner,
            source_repo_url="git@github.com:example/platform-repo.git",
        )
    except ValueError as exc:
        assert str(exc) == "Only https repository URLs are supported"
    else:
        raise AssertionError("Expected clone request to reject non-https URL")


def test_get_repo_uses_org_owner_for_lookup(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_BASE_URL",
        "http://gittin:3000",
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GOGS_TOKEN",
        "test-token",
    )
    requested_paths: list[str] = []

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, path):
            requested_paths.append(path)
            return httpx.Response(404)

    monkeypatch.setattr(user_repo_service, "_client", lambda: FakeClient())

    result = user_repo_service._get_repo("viewer-repo")

    assert result is None
    assert requested_paths == ["/api/v1/repos/dog/viewer-repo"]


def test_commit_user_repo_changes_requires_owner_or_superuser(db) -> None:
    owner = _create_user(db)
    other_user = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
    )

    try:
        user_repo_service.commit_user_repo_changes(
            session=db,
            repo_id=repo.id,
            actor_user_id=other_user.id,
            branch="main",
            mutations=[
                UserRepoFileMutation(
                    path="README.md",
                    operation="upsert",
                    content="# Hello\n",
                )
            ],
            commit_message="Update README",
            expected_head_sha="abc123",
        )
    except UserRepoWriteUnauthorized as exc:
        assert str(exc) == "User repo is not writable"
    else:
        raise AssertionError("Expected non-owner write to be rejected")


def test_commit_user_repo_changes_requires_ready_repo(db) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.IMPORTING,
    )

    try:
        user_repo_service.commit_user_repo_changes(
            session=db,
            repo_id=repo.id,
            actor_user_id=owner.id,
            branch="main",
            mutations=[
                UserRepoFileMutation(
                    path="README.md",
                    operation="upsert",
                    content="# Hello\n",
                )
            ],
            commit_message="Update README",
            expected_head_sha="abc123",
        )
    except UserRepoWriteNotReady as exc:
        assert str(exc) == "User repo is not ready for writes"
    else:
        raise AssertionError("Expected write on non-ready repo to be rejected")


def test_commit_user_repo_changes_requires_default_branch(db) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
    )

    try:
        user_repo_service.commit_user_repo_changes(
            session=db,
            repo_id=repo.id,
            actor_user_id=owner.id,
            branch="develop",
            mutations=[
                UserRepoFileMutation(
                    path="README.md",
                    operation="upsert",
                    content="# Hello\n",
                )
            ],
            commit_message="Update README",
            expected_head_sha="abc123",
        )
    except UserRepoWriteUnsupportedBranch as exc:
        assert str(exc) == "Writes are only supported for branch main"
    else:
        raise AssertionError("Expected non-default branch write to be rejected")


def test_commit_user_repo_changes_detects_stale_head(db, monkeypatch) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        user_repo_service,
        "_resolve_repo_head_sha",
        lambda **kwargs: "actual-head-sha",
    )

    try:
        user_repo_service.commit_user_repo_changes(
            session=db,
            repo_id=repo.id,
            actor_user_id=owner.id,
            branch="main",
            mutations=[
                UserRepoFileMutation(
                    path="README.md",
                    operation="upsert",
                    content="# Hello\n",
                )
            ],
            commit_message="Update README",
            expected_head_sha="stale-head-sha",
        )
    except UserRepoWriteConflict as exc:
        assert str(exc) == "Repo head no longer matches expected_head_sha"
    else:
        raise AssertionError("Expected stale head to be rejected")


def test_commit_user_repo_changes_rejects_invalid_mutation_payload(db) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
    )

    try:
        user_repo_service.commit_user_repo_changes(
            session=db,
            repo_id=repo.id,
            actor_user_id=owner.id,
            branch="main",
            mutations=[
                UserRepoFileMutation(
                    path="../README.md",
                    operation="upsert",
                    content="# Hello\n",
                )
            ],
            commit_message="Update README",
            expected_head_sha="abc123",
        )
    except UserRepoWriteValidationError as exc:
        assert str(exc) == "Invalid repo path: ../README.md"
    else:
        raise AssertionError("Expected invalid path to be rejected")


def test_commit_user_repo_changes_returns_commit_result(db, monkeypatch) -> None:
    owner = _create_user(db)
    repo = user_repo_service.create_user_repo_db_only(
        session=db,
        owner=owner,
        display_name="Write Test Repo",
        slug="write-test-repo",
        import_status=UserRepoImportStatus.READY,
        imported_at=datetime.now(timezone.utc),
    )
    monkeypatch.setattr(
        user_repo_service,
        "_resolve_repo_head_sha",
        lambda **kwargs: "abc123",
    )

    def _fake_commit_changes_to_remote(
        *,
        user_repo,
        actor,
        branch,
        mutations,
        commit_message,
        expected_head_sha,
    ):
        assert user_repo.id == repo.id
        assert actor.id == owner.id
        assert branch == "main"
        assert expected_head_sha == "abc123"
        assert mutations == [
            UserRepoFileMutation(
                path="README.md",
                operation="upsert",
                content="# Hello\n",
                encoding="utf-8",
            )
        ]
        return UserRepoCommitResult(
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
        "_commit_changes_to_remote",
        _fake_commit_changes_to_remote,
    )

    result = user_repo_service.commit_user_repo_changes(
        session=db,
        repo_id=repo.id,
        actor_user_id=owner.id,
        branch="main",
        mutations=[
            UserRepoFileMutation(
                path="README.md",
                operation="upsert",
                content="# Hello\n",
            )
        ],
        commit_message="Update README",
        expected_head_sha="abc123",
    )

    assert result.repo_id == repo.id
    assert result.previous_head_sha == "abc123"
    assert result.new_head_sha == "def456"
    assert result.changed_paths == ["README.md"]


def test_build_git_auth_env_requires_http_git_credentials(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GIT_USERNAME",
        None,
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GIT_PASSWORD",
        None,
    )

    try:
        user_repo_service._build_git_auth_env(worktree_dir=tmp_path)
    except UserRepoWriteFailed as exc:
        assert str(exc) == "HTTP git credentials are not configured for user repo writes"
    else:
        raise AssertionError("Expected missing HTTP git credentials to fail")


def test_build_git_auth_env_writes_askpass_script(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GIT_USERNAME",
        "service-user",
    )
    monkeypatch.setattr(
        "app.services.user_repo_service.settings.USER_REPO_GIT_PASSWORD",
        "service-pass",
    )

    env = user_repo_service._build_git_auth_env(worktree_dir=tmp_path)

    assert env["GIT_TERMINAL_PROMPT"] == "0"
    assert "GIT_ASKPASS" in env
    askpass_path = Path(env["GIT_ASKPASS"])
    assert askpass_path.exists()
    script = askpass_path.read_text(encoding="utf-8")
    assert "service-user" in script
    assert "service-pass" in script
