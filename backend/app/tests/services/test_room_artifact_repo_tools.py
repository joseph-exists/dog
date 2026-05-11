from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from sqlmodel import Session

from app import crud
from app.core.config import settings
from app.models import Room, RoomParticipant, UserCreate
from app.services.agent_tools import read_repo_file, write_repo_files


def _create_room_with_owner(db: Session) -> tuple[uuid.UUID, uuid.UUID]:
    user = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"room-artifact-{uuid.uuid4()}@example.com",
            password="password123",
        ),
    )
    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Artifact Room",
        story_id=None,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(room)
    db.add(
        RoomParticipant(
            room_id=room.room_id,
            participant_id=str(user.id),
            participant_type="user",
            role="owner",
            active=True,
        )
    )
    db.commit()
    return room.room_id, user.id


def _ctx(*, room_id: uuid.UUID, acting_user_id: uuid.UUID):
    return SimpleNamespace(
        deps=SimpleNamespace(
            room_id=room_id,
            acting_user_id=acting_user_id,
            current_agent_slug="artifact-agent",
        )
    )


@pytest.mark.asyncio
async def test_agent_repo_tools_write_and_read_current_room_repo(
    db: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_ENABLED", True)
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "SHADOW_REPO_URL_TEMPLATE", None)

    room_id, user_id = _create_room_with_owner(db)
    ctx = _ctx(room_id=room_id, acting_user_id=user_id)

    write_result = await write_repo_files(
        ctx,  # type: ignore[arg-type]
        mutations=[
            {
                "path": "README.md",
                "operation": "upsert",
                "content": "# Room Artifact\n",
            }
        ],
        commit_message="Create room readme",
    )

    assert "Committed 1 room artifact file change(s)" in write_result
    assert "README.md" in write_result

    read_result = await read_repo_file(
        ctx,  # type: ignore[arg-type]
        path="README.md",
    )
    payload = json.loads(read_result)

    assert payload["repo_id"] == "room"
    assert payload["repo_kind"] == "room_shadow_repo"
    assert payload["room_id"] == str(room_id)
    assert payload["content"] == "# Room Artifact\n"
    assert payload["write_hint"]["branch"] == settings.SHADOW_REPO_DEFAULT_BRANCH
    assert payload["write_hint"]["expected_head_sha"]


@pytest.mark.asyncio
async def test_agent_repo_tools_reject_reserved_room_paths(
    db: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_ENABLED", True)
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "SHADOW_REPO_URL_TEMPLATE", None)

    room_id, user_id = _create_room_with_owner(db)

    result = await write_repo_files(
        _ctx(room_id=room_id, acting_user_id=user_id),  # type: ignore[arg-type]
        mutations=[
            {
                "path": "room.json",
                "operation": "upsert",
                "content": "{}",
            }
        ],
        commit_message="Try to overwrite system snapshot",
    )

    assert (
        result
        == "Write validation failed: Path is reserved for system use: room.json"
    )


@pytest.mark.asyncio
async def test_agent_repo_tools_reject_nonparticipant_room_repo_write(
    db: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_ENABLED", True)
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "SHADOW_REPO_URL_TEMPLATE", None)

    room_id, _owner_id = _create_room_with_owner(db)
    outsider = crud.create_user(
        session=db,
        user_create=UserCreate(
            email=f"room-artifact-outsider-{uuid.uuid4()}@example.com",
            password="password123",
        ),
    )

    result = await write_repo_files(
        _ctx(room_id=room_id, acting_user_id=outsider.id),  # type: ignore[arg-type]
        mutations=[
            {
                "path": "README.md",
                "operation": "upsert",
                "content": "# Nope\n",
            }
        ],
        commit_message="Unauthorized write",
    )

    assert result == "Write failed: user is not allowed to modify this room repo."


@pytest.mark.asyncio
async def test_agent_repo_tools_room_repo_conflict(
    db: Session,
    tmp_path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "SHADOW_ENABLED", True)
    monkeypatch.setattr(settings, "SHADOW_REPOS_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "SHADOW_REPO_URL_TEMPLATE", None)

    room_id, user_id = _create_room_with_owner(db)
    ctx = _ctx(room_id=room_id, acting_user_id=user_id)

    await write_repo_files(
        ctx,  # type: ignore[arg-type]
        mutations=[
            {
                "path": "README.md",
                "operation": "upsert",
                "content": "# First\n",
            }
        ],
        commit_message="Create room readme",
    )

    result = await write_repo_files(
        ctx,  # type: ignore[arg-type]
        mutations=[
            {
                "path": "README.md",
                "operation": "upsert",
                "content": "# Second\n",
            }
        ],
        commit_message="Update room readme",
        expected_head_sha="0" * 40,
    )

    assert result == (
        "Write conflict: Repo head no longer matches expected_head_sha. "
        "Refresh HEAD and retry."
    )
