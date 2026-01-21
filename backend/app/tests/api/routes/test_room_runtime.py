"""Integration tests for room runtime (Surface 1) API."""

from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import select

from app.core.config import settings
from app.models import Room, RoomParticipant, RoomStoryProgress, User


def test_read_room_runtime_returns_projection(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db,
    db_story_with_progress,
) -> None:
    story, progress = db_story_with_progress

    # Create room tied to the story
    superuser = db.exec(select(User).where(User.email == settings.FIRST_SUPERTESTUSER)).first()
    assert superuser is not None

    room = Room(
        room_id=uuid4(),
        creator_id=superuser.id,
        title="Runtime Test Room",
        story_id=story.id,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    db.add(room)
    db.add(
        RoomParticipant(
            room_id=room.room_id,
            participant_id=str(superuser.id),
            participant_type="user",
            role="owner",
            active=True,
        )
    )
    db.commit()
    db.refresh(room)

    # Create room-scoped runtime pointer to the shared progress
    db.add(
        RoomStoryProgress(
            id=uuid4(),
            room_id=room.room_id,
            story_id=story.id,
            story_version=progress.story_version,
            active_progress_id=progress.id,
            revision=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = client.get(
        f"{settings.API_V1_STR}/rooms/{room.room_id}/runtime",
        headers=superuser_token_headers,
    )
    assert response.status_code == 200
    data = response.json()

    assert data["room_id"] == str(room.room_id)
    assert data["story_id"] == str(story.id)
    assert data["story_version"] == progress.story_version
    assert data["active_progress_id"] == str(progress.id)
    assert data["revision"] == 0
    assert data["head_version"] == progress.head_version
