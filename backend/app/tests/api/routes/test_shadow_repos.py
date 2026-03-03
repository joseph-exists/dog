from __future__ import annotations

import subprocess
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import ShadowRepo, User, UserCreate
from app.tests.utils.user import user_authentication_headers


def _create_user(db: Session, *, email: str, password: str) -> User:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(email=email, password=password),
    )
    db.commit()
    db.refresh(user)
    return user


def _init_shadow_repo(
    *,
    base_path: Path,
    entity_type: str,
    entity_id: uuid.UUID,
) -> None:
    repo_path = base_path / entity_type / str(entity_id)
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-b", settings.SHADOW_REPO_DEFAULT_BRANCH],
        cwd=repo_path,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "test-shadow"], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "config", "user.email", "shadow@test.local"],
        cwd=repo_path,
        check=True,
    )

    (repo_path / "README.md").write_text("# Shadow Repo\n", encoding="utf-8")
    notes_dir = repo_path / "notes"
    notes_dir.mkdir(parents=True, exist_ok=True)
    (notes_dir / "hello.txt").write_text("hello from shadow repo\n", encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial shadow state"],
        cwd=repo_path,
        check=True,
    )


def test_shadow_repo_view_returns_repo_projection(
    client: TestClient,
    db: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))

    owner_password = "shadow-owner-pass"
    owner = _create_user(
        db,
        email=f"shadow-owner-{uuid.uuid4()}@example.com",
        password=owner_password,
    )
    headers = user_authentication_headers(
        client=client,
        email=owner.email,
        password=owner_password,
    )

    entity_id = uuid.uuid4()
    db.add(
        ShadowRepo(
            owner_id=owner.id,
            entity_type="agent",
            entity_id=entity_id,
            forgejo_repo_name=f"agent-{entity_id}",
            forgejo_repo_id=None,
        )
    )
    db.commit()

    _init_shadow_repo(base_path=tmp_path, entity_type="agent", entity_id=entity_id)

    response = client.get(
        f"{settings.API_V1_STR}/shadow-repos/agent/{entity_id}/view",
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["entity_type"] == "agent"
    assert payload["summary"]["entity_id"] == str(entity_id)
    assert payload["summary"]["default_branch"] == settings.SHADOW_REPO_DEFAULT_BRANCH
    assert payload["commits"][0]["message"] == "Initial shadow state"
    assert {entry["path"] for entry in payload["tree"]} == {"README.md", "notes"}


def test_shadow_repo_file_returns_file_content(
    client: TestClient,
    db: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))

    owner_password = "shadow-file-pass"
    owner = _create_user(
        db,
        email=f"shadow-file-{uuid.uuid4()}@example.com",
        password=owner_password,
    )
    headers = user_authentication_headers(
        client=client,
        email=owner.email,
        password=owner_password,
    )

    entity_id = uuid.uuid4()
    db.add(
        ShadowRepo(
            owner_id=owner.id,
            entity_type="story",
            entity_id=entity_id,
            forgejo_repo_name=f"story-{entity_id}",
            forgejo_repo_id=None,
        )
    )
    db.commit()

    _init_shadow_repo(base_path=tmp_path, entity_type="story", entity_id=entity_id)

    response = client.get(
        f"{settings.API_V1_STR}/shadow-repos/story/{entity_id}/file",
        params={"path": "notes/hello.txt"},
        headers=headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["path"] == "notes/hello.txt"
    assert payload["content"] == "hello from shadow repo\n"
    assert payload["encoding"] == "utf-8"


def test_shadow_repo_access_denied_is_opaque_404(
    client: TestClient,
    db: Session,
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))

    owner_password = "shadow-owner-hidden"
    owner = _create_user(
        db,
        email=f"shadow-hidden-owner-{uuid.uuid4()}@example.com",
        password=owner_password,
    )
    other_password = "shadow-other-hidden"
    other_user = _create_user(
        db,
        email=f"shadow-hidden-other-{uuid.uuid4()}@example.com",
        password=other_password,
    )
    other_headers = user_authentication_headers(
        client=client,
        email=other_user.email,
        password=other_password,
    )

    entity_id = uuid.uuid4()
    db.add(
        ShadowRepo(
            owner_id=owner.id,
            entity_type="persona",
            entity_id=entity_id,
            forgejo_repo_name=f"persona-{entity_id}",
            forgejo_repo_id=None,
        )
    )
    db.commit()

    _init_shadow_repo(base_path=tmp_path, entity_type="persona", entity_id=entity_id)

    response = client.get(
        f"{settings.API_V1_STR}/shadow-repos/persona/{entity_id}/view",
        headers=other_headers,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Shadow repo not found"
