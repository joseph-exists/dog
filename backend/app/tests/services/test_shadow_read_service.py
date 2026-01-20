from __future__ import annotations

import uuid

import pytest
from sqlmodel import Session

from app.models import ShadowRepo, ShadowVersion, User, UserCreate
from app.services.shadow_read_service import shadow_read_service


def test_shadow_read_service_falls_back_to_db_when_no_token(db: Session) -> None:
    # Create a user to satisfy FK constraints.
    user_in = UserCreate(email=f"shadow-read-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",  # token typically not configured in tests
        entity_id=entity_id,
        forgejo_repo_name=f"room-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    snapshot = {"entity_type": "room", "room": {"room_id": str(entity_id)}}
    shadow_version = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="deadbeef",
        version_number=1,
        message="test",
        snapshot_json=snapshot,
        created_by_id=user.id,
    )
    db.add(shadow_version)
    db.commit()

    result = shadow_read_service.get_latest_snapshot(
        session=db, entity_type="room", entity_id=entity_id
    )
    assert result.source == "db"
    assert result.is_stale is True
    assert result.snapshot_json == snapshot

