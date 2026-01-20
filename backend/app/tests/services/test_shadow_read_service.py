from __future__ import annotations

import uuid
from unittest.mock import patch, MagicMock

import pytest
from sqlmodel import Session

from app.models import ShadowRepo, ShadowVersion, User, UserCreate
from app.services.shadow_read_service import (
    shadow_read_service,
    ShadowRepoNotFound,
    ShadowVersionNotFound,
    ShadowReadError,
)


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


def test_shadow_read_service_get_snapshot_by_version_returns_db_snapshot(db: Session) -> None:
    """Test that get_snapshot_by_version returns the correct version's snapshot."""
    # Setup: create user and shadow repo
    user_in = UserCreate(email=f"shadow-version-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",
        entity_id=entity_id,
        forgejo_repo_name=f"room-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    # Create multiple versions
    version_1_snapshot = {"entity_type": "room", "version": 1, "room": {"room_id": str(entity_id)}}
    version_1 = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="commit1111",
        version_number=1,
        message="version 1",
        snapshot_json=version_1_snapshot,
        created_by_id=user.id,
    )
    db.add(version_1)
    db.commit()

    version_2_snapshot = {"entity_type": "room", "version": 2, "room": {"room_id": str(entity_id), "updated": True}}
    version_2 = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="commit2222",
        version_number=2,
        message="version 2",
        snapshot_json=version_2_snapshot,
        created_by_id=user.id,
    )
    db.add(version_2)
    db.commit()

    version_3_snapshot = {"entity_type": "room", "version": 3, "room": {"room_id": str(entity_id), "updated": True, "finalized": True}}
    version_3 = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="commit3333",
        version_number=3,
        message="version 3",
        snapshot_json=version_3_snapshot,
        created_by_id=user.id,
    )
    db.add(version_3)
    db.commit()

    # Test: retrieve specific versions
    result_v1 = shadow_read_service.get_snapshot_by_version(
        session=db, entity_type="room", entity_id=entity_id, version_number=1
    )
    assert result_v1.version_number == 1
    assert result_v1.commit_sha == "commit1111"
    assert result_v1.snapshot_json == version_1_snapshot
    assert result_v1.source == "db"
    assert result_v1.is_stale is True

    result_v2 = shadow_read_service.get_snapshot_by_version(
        session=db, entity_type="room", entity_id=entity_id, version_number=2
    )
    assert result_v2.version_number == 2
    assert result_v2.commit_sha == "commit2222"
    assert result_v2.snapshot_json == version_2_snapshot

    result_v3 = shadow_read_service.get_snapshot_by_version(
        session=db, entity_type="room", entity_id=entity_id, version_number=3
    )
    assert result_v3.version_number == 3
    assert result_v3.commit_sha == "commit3333"
    assert result_v3.snapshot_json == version_3_snapshot


def test_shadow_read_service_get_snapshot_by_commit_partial_match(db: Session) -> None:
    """Test that get_snapshot_by_commit resolves partial commit SHA matches."""
    # Setup: create user and shadow repo
    user_in = UserCreate(email=f"shadow-commit-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="story",
        entity_id=entity_id,
        forgejo_repo_name=f"story-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    # Create a version with a full commit SHA
    full_commit_sha = "abc123def456789abcdef456789"
    snapshot = {"entity_type": "story", "story_id": str(entity_id)}
    shadow_version = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha=full_commit_sha,
        version_number=1,
        message="test commit",
        snapshot_json=snapshot,
        created_by_id=user.id,
    )
    db.add(shadow_version)
    db.commit()

    # Test: retrieve by partial commit SHA
    result = shadow_read_service.get_snapshot_by_commit(
        session=db, entity_type="story", entity_id=entity_id, commit_sha="abc123"
    )
    assert result.commit_sha == full_commit_sha
    assert result.version_number == 1
    assert result.snapshot_json == snapshot


def test_shadow_read_service_forgejo_failure_falls_back_to_db(db: Session) -> None:
    """Test that Forgejo read failures fall back to DB with is_stale=True."""
    # Setup: create user and shadow repo
    user_in = UserCreate(email=f"shadow-forgejo-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",
        entity_id=entity_id,
        forgejo_repo_name=f"room-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    db_snapshot = {"entity_type": "room", "room": {"room_id": str(entity_id), "source": "db"}}
    shadow_version = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="deadbeef",
        version_number=1,
        message="test",
        snapshot_json=db_snapshot,
        created_by_id=user.id,
    )
    db.add(shadow_version)
    db.commit()

    # Monkeypatch _read_json_file_from_forgejo to raise an error
    with patch.object(
        shadow_read_service,
        "_read_json_file_from_forgejo",
        side_effect=ShadowReadError("Forgejo connection failed"),
    ):
        # Also patch _get_service_token to return a token so it attempts Forgejo read
        with patch("app.services.shadow_read_service.shadow_service._get_service_token", return_value="test-token"):
            result = shadow_read_service.get_latest_snapshot(
                session=db, entity_type="room", entity_id=entity_id
            )

    # Assert: falls back to DB
    assert result.source == "db"
    assert result.is_stale is True
    assert result.snapshot_json == db_snapshot


def test_shadow_read_service_latest_committed_wins_over_pending(db: Session) -> None:
    user_in = UserCreate(email=f"shadow-latest-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",
        entity_id=entity_id,
        forgejo_repo_name=f"room-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    committed_snapshot = {"entity_type": "room", "version": 1}
    committed = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="commit1111",
        version_number=1,
        message="committed",
        snapshot_json=committed_snapshot,
        created_by_id=user.id,
        status="committed",
    )
    db.add(committed)
    db.commit()

    pending_snapshot = {"entity_type": "room", "version": 2}
    pending = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="pending",
        version_number=2,
        message="pending",
        snapshot_json=pending_snapshot,
        created_by_id=user.id,
        status="pending",
    )
    db.add(pending)
    db.commit()

    result = shadow_read_service.get_latest_snapshot(
        session=db, entity_type="room", entity_id=entity_id
    )
    assert result.version_number == 1
    assert result.snapshot_json == committed_snapshot


def test_shadow_read_service_latest_pending_when_no_committed(db: Session) -> None:
    user_in = UserCreate(email=f"shadow-pending-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",
        entity_id=entity_id,
        forgejo_repo_name=f"room-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    pending_snapshot = {"entity_type": "room", "version": 1}
    pending = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="pending",
        version_number=1,
        message="pending",
        snapshot_json=pending_snapshot,
        created_by_id=user.id,
        status="pending",
    )
    db.add(pending)
    db.commit()

    result = shadow_read_service.get_latest_snapshot(
        session=db, entity_type="room", entity_id=entity_id
    )
    assert result.version_number == 1
    assert result.snapshot_json == pending_snapshot


def test_shadow_read_service_missing_shadow_repo_raises_typed_error(db: Session) -> None:
    """Test that calling read with no ShadowRepo raises ShadowRepoNotFound."""
    entity_id = uuid.uuid4()

    with pytest.raises(ShadowRepoNotFound):
        shadow_read_service.get_latest_snapshot(
            session=db, entity_type="room", entity_id=entity_id
        )


def test_shadow_read_service_missing_shadow_version_raises_typed_error(db: Session) -> None:
    """Test that missing ShadowVersion raises ShadowVersionNotFound."""
    # Setup: create user and shadow repo with no versions
    user_in = UserCreate(email=f"shadow-noversion-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="persona",
        entity_id=entity_id,
        forgejo_repo_name=f"persona-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    # Try to get latest snapshot when no versions exist
    with pytest.raises(ShadowVersionNotFound):
        shadow_read_service.get_latest_snapshot(
            session=db, entity_type="persona", entity_id=entity_id
        )
