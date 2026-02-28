from __future__ import annotations

import uuid

import httpx

from app import crud
from app.models import UserCreate
from app.services.user_repo_service import user_repo_service


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
