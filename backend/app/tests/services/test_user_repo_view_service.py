from __future__ import annotations

import uuid

from app.models import UserRepo, UserRepoImportStatus
from app.services.user_repo_view_service import user_repo_view_service


def test_to_public_model_includes_required_slug() -> None:
    user_repo = UserRepo(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        slug="viewer-repo",
        display_name="Viewer Repo",
        description=None,
        source_repo_url="https://github.com/example/viewer-repo.git",
        source_branch="main",
        import_status=UserRepoImportStatus.IMPORTING,
        import_error=None,
        imported_at=None,
        gogs_repo_name="viewer-repo",
        gogs_repo_id=None,
        gogs_full_name=None,
        gogs_html_url=None,
        is_private=False,
    )

    public_model = user_repo_view_service.to_public_model(user_repo=user_repo)

    assert public_model.slug == "viewer-repo"
    assert public_model.default_branch == "main"
    assert public_model.capabilities is not None
    assert public_model.capabilities.default_branch == "main"


def test_repo_api_path_uses_repo_full_name_owner(monkeypatch) -> None:
    user_repo = UserRepo(
        id=uuid.uuid4(),
        owner_user_id=uuid.uuid4(),
        slug="viewer-repo",
        display_name="Viewer Repo",
        description=None,
        source_repo_url=None,
        source_branch="main",
        import_status=UserRepoImportStatus.READY,
        import_error=None,
        imported_at=None,
        gogs_repo_name="viewer-repo",
        gogs_repo_id=123,
        gogs_full_name="dog/viewer-repo",
        gogs_html_url=None,
        is_private=False,
    )

    path = user_repo_view_service._repo_api_path(
        user_repo=user_repo,
        suffix="/contents",
    )

    assert path == "/api/v1/repos/dog/viewer-repo/contents"
