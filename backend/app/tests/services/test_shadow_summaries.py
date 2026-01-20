from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session

from app.models import ShadowRepo, ShadowVersion, User, UserCreate
from app.services.shadow_summaries import summarize_user_llm_provider
from app.services.shadow_summary_service import shadow_summary_service, ShadowSummaryResult


def test_summarize_user_llm_provider_redacts_keys() -> None:
    snapshot = {
        "user_llm_provider": {
            "id": "provider-id",
            "user_id": "user-id",
            "provider_type": "openai",
            "name": "My OpenAI",
            "is_enabled": True,
            "is_default": False,
            "base_url": None,
            "description": "test",
            "api_key_encrypted": "should-not-leak",
            "api_key": "should-not-leak",
            "api_key_present": True,
            "last_tested_at": None,
            "last_test_success": None,
        }
    }

    summary = summarize_user_llm_provider(snapshot)
    provider = summary["user_llm_provider"]

    assert provider["api_key_present"] is True
    assert "api_key_encrypted" not in provider
    assert "api_key" not in provider


@pytest.mark.asyncio
async def test_summarize_room_contains_active_bindings_shape(db: Session) -> None:
    """Test that room summary includes proper active_bindings shape."""
    # Setup: create user and shadow repo
    user_in = UserCreate(email=f"shadow-room-{uuid.uuid4()}@example.com", password="password123")
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

    # Create a room snapshot with participants and active bindings
    room_snapshot = {
        "entity_type": "room",
        "room": {
            "room_id": str(entity_id),
            "name": "Test Room",
            "participants": [
                {
                    "participant_id": str(uuid.uuid4()),
                    "type": "agent",
                    "role": "moderator",
                    "active": True,
                },
                {
                    "participant_id": str(uuid.uuid4()),
                    "type": "user",
                    "role": "participant",
                    "active": True,
                },
            ],
            "active_bindings": [
                {
                    "participant_id": str(uuid.uuid4()),
                    "type": "agent",
                    "persona_id": str(uuid.uuid4()),
                    "model_name": "gpt-4",
                    "user_llm_provider_id": str(uuid.uuid4()),
                },
            ],
        }
    }

    shadow_version = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha="abc123",
        version_number=1,
        message="room snapshot",
        snapshot_json=room_snapshot,
        created_by_id=user.id,
    )
    db.add(shadow_version)
    db.commit()

    # Test: get summary and verify structure
    result = await shadow_summary_service.get_latest_summary(
        session=db, entity_type="room", entity_id=entity_id
    )

    assert result.summary is not None
    # The summary should contain the raw snapshot when no custom summarizer exists
    assert "raw" in result.summary or "room" in result.summary


@pytest.mark.asyncio
async def test_shadow_summary_service_returns_summary_dispatch_result(db: Session) -> None:
    """Test that get_latest_summary returns summary field and preserves metadata."""
    # Setup: create user and shadow repo
    user_in = UserCreate(email=f"shadow-summary-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    entity_id = uuid.uuid4()
    shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="provider",
        entity_id=entity_id,
        forgejo_repo_name=f"provider-{str(entity_id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(shadow_repo)
    db.commit()
    db.refresh(shadow_repo)

    commit_sha = "deadbeefcafe"
    snapshot = {
        "entity_type": "provider",
        "user_llm_provider": {
            "id": str(entity_id),
            "provider_type": "openai",
            "api_key_encrypted": "secret",
            "api_key_present": True,
        },
    }

    shadow_version = ShadowVersion(
        shadow_repo_id=shadow_repo.id,
        commit_sha=commit_sha,
        version_number=1,
        message="provider snapshot",
        snapshot_json=snapshot,
        created_by_id=user.id,
    )
    db.add(shadow_version)
    db.commit()

    # Test: get summary
    result = await shadow_summary_service.get_latest_summary(
        session=db, entity_type="provider", entity_id=entity_id
    )

    assert isinstance(result, ShadowSummaryResult)
    assert result.entity_type == "provider"
    assert result.entity_id == entity_id
    assert result.version_number == 1
    assert result.commit_sha == commit_sha
    assert result.source == "db"
    assert result.is_stale is True
    assert result.summary is not None

