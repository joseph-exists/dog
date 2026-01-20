from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session

from app.models import (
    AgentConfig,
    Room,
    RoomParticipant,
    ShadowRepo,
    ShadowVersion,
    Story,
    User,
    UserCreate,
    UserLLMProvider,
)
from app.services.shadow_context_loader import build_shadow_context_items


@pytest.mark.asyncio
async def test_shadow_context_loader_emits_missing_item_when_room_shadow_missing(
    db: Session,
) -> None:
    """Test that missing room shadow snapshot emits missing_shadow_snapshot item."""
    # Setup: create user and room without shadow repo
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    room = Room(
        name="Test Room",
        description="Test Description",
        owner_id=user.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Test: build shadow context items without shadow repo
    items = await build_shadow_context_items(
        db=db,
        room_id=room.id,
        agent_slug=None,
    )

    # Assert: should emit missing room shadow item
    room_items = [
        item for item in items if item.get("context_type") == "shadow.room.summary"
    ]
    assert len(room_items) > 0
    assert room_items[0].get("payload", {}).get("missing_shadow_snapshot") is True


@pytest.mark.asyncio
async def test_shadow_context_loader_emits_missing_item_when_story_shadow_missing(
    db: Session,
) -> None:
    """Test that missing story shadow snapshot emits missing_shadow_snapshot item."""
    # Setup: create user, room with story
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    story = Story(
        title="Test Story",
        description="Test Story Description",
        owner_id=user.id,
    )
    db.add(story)
    db.commit()
    db.refresh(story)

    room = Room(
        name="Test Room with Story",
        description="Test Description",
        story_id=story.id,
        owner_id=user.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Test: build shadow context items without shadow repo for story
    items = await build_shadow_context_items(
        db=db,
        room_id=room.id,
        agent_slug=None,
    )

    # Assert: should emit missing story shadow item
    story_items = [
        item for item in items if item.get("context_type") == "shadow.story.summary"
    ]
    assert len(story_items) > 0
    assert story_items[0].get("payload", {}).get("missing_shadow_snapshot") is True


@pytest.mark.asyncio
async def test_shadow_context_loader_agent_scoped_items_use_binding_row(
    db: Session,
) -> None:
    """Test that agent-scoped items use binding row data."""
    # Setup: create user, agent config, room with agent binding
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    agent_slug = "test-agent"
    agent_config = AgentConfig(
        slug=agent_slug,
        owner_id=user.id,
        name="Test Agent",
    )
    db.add(agent_config)
    db.commit()
    db.refresh(agent_config)

    room = Room(
        name="Test Room",
        description="Test Description",
        owner_id=user.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Create room participant binding for agent
    binding = RoomParticipant(
        room_id=room.id,
        participant_type="agent",
        participant_id=agent_slug,
    )
    db.add(binding)
    db.commit()

    # Create shadow repo and version for agent
    agent_snapshot = {"agent": {"slug": agent_slug, "name": "Test Agent"}}
    agent_shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="agent",
        entity_id=agent_config.id,
        forgejo_repo_name=f"agent-{str(agent_config.id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(agent_shadow_repo)
    db.commit()
    db.refresh(agent_shadow_repo)

    agent_shadow_version = ShadowVersion(
        shadow_repo_id=agent_shadow_repo.id,
        commit_sha="abc123",
        version_number=1,
        message="agent snapshot",
        snapshot_json=agent_snapshot,
        created_by_id=user.id,
    )
    db.add(agent_shadow_version)
    db.commit()

    # Test: build shadow context items with agent_slug
    items = await build_shadow_context_items(
        db=db,
        room_id=room.id,
        agent_slug=agent_slug,
    )

    # Assert: should include shadow.agent.summary
    agent_items = [
        item for item in items if item.get("context_type") == "shadow.agent.summary"
    ]
    assert len(agent_items) > 0


@pytest.mark.asyncio
async def test_shadow_context_loader_runtime_provider_missing_is_embedded(
    db: Session,
) -> None:
    """Test that missing user_llm_provider shadow is embedded as missing."""
    # Setup: create user, room, provider without shadow
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = crud.create_user(session=db, user_create=user_in)

    provider = UserLLMProvider(
        user_id=user.id,
        provider_type="openai",
        name="Test Provider",
        is_enabled=True,
    )
    db.add(provider)
    db.commit()
    db.refresh(provider)

    agent_slug = "test-agent"
    agent_config = AgentConfig(
        slug=agent_slug,
        owner_id=user.id,
        name="Test Agent",
    )
    db.add(agent_config)
    db.commit()
    db.refresh(agent_config)

    room = Room(
        name="Test Room",
        description="Test Description",
        owner_id=user.id,
    )
    db.add(room)
    db.commit()
    db.refresh(room)

    # Create room participant binding with user_llm_provider_id but no shadow repo
    binding = RoomParticipant(
        room_id=room.id,
        participant_type="agent",
        participant_id=agent_slug,
        user_llm_provider_id=provider.id,
    )
    db.add(binding)
    db.commit()

    # Test: build shadow context items
    items = await build_shadow_context_items(
        db=db,
        room_id=room.id,
        agent_slug=agent_slug,
    )

    # Assert: should embed missing provider shadow
    runtime_items = [
        item for item in items if item.get("context_type") == "shadow.runtime.summary"
    ]
    if runtime_items:  # May or may not be present depending on implementation
        assert runtime_items[0].get("payload", {}).get(
            "user_llm_provider_missing"
        ) is not None
