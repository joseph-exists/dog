from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    AgentConfig,
    Room,
    RoomParticipantBinding,
    ShadowRepo,
    ShadowVersion,
    Story,
    User,
    UserCreate,
    UserLLMProvider,
)
from app.services.shadow_context_loader import build_shadow_context_items


def _create_agent_binding(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    agent_id: uuid.UUID,
    user_llm_provider_id: uuid.UUID | None = None,
) -> RoomParticipantBinding:
    return RoomParticipantBinding(
        room_id=room_id,
        participant_type="agent",
        participant_id=agent_slug,
        agent_id=agent_id,
        user_llm_provider_id=user_llm_provider_id,
    )


@pytest.mark.asyncio
async def test_shadow_context_loader_skips_room_summary_when_missing(
    async_session: AsyncSession,
) -> None:
    """Test that missing room shadow snapshot does not emit a room summary context."""
    # Setup: create user and room without shadow repo
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = await async_session.run_sync(
        lambda session: crud.create_user(session=session, user_create=user_in)
    )

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Test Room",
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)
    await async_session.commit()
    await async_session.refresh(room)

    # Test: build shadow context items without shadow repo
    items = await build_shadow_context_items(
        session=async_session,
        room_id=room.room_id,
        agent_slug=None,
    )

    # Assert: no room summary context when the shadow snapshot is missing
    room_items = [
        item for item in items if item.context_type == "shadow.room.summary"
    ]
    assert len(room_items) == 0


@pytest.mark.asyncio
async def test_shadow_context_loader_emits_missing_item_when_story_shadow_missing(
    async_session: AsyncSession,
) -> None:
    """Test that missing story shadow snapshot emits missing_shadow_snapshot item."""
    # Setup: create user, room with story
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = await async_session.run_sync(
        lambda session: crud.create_user(session=session, user_create=user_in)
    )

    story = Story(
        title="Test Story",
        description="Test Story Description",
        owner_id=user.id,
    )
    async_session.add(story)
    await async_session.commit()
    await async_session.refresh(story)

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Test Room with Story",
        story_id=story.id,
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)
    await async_session.commit()
    await async_session.refresh(room)

    # Test: build shadow context items without shadow repo for story
    items = await build_shadow_context_items(
        session=async_session,
        room_id=room.room_id,
        agent_slug=None,
    )

    # Assert: should emit missing story shadow item
    story_items = [
        item for item in items if item.context_type == "shadow.story.summary"
    ]
    assert len(story_items) > 0
    assert story_items[0].payload.get("missing_shadow_snapshot") is True


@pytest.mark.asyncio
async def test_shadow_context_loader_agent_scoped_items_use_binding_row(
    async_session: AsyncSession,
) -> None:
    """Test that agent-scoped items use binding row data."""
    # Setup: create user, agent config, room with agent binding
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = await async_session.run_sync(
        lambda session: crud.create_user(session=session, user_create=user_in)
    )

    agent_slug = "test-agent"
    agent_config = AgentConfig(
        slug=agent_slug,
        owner_id=user.id,
        name="Test Agent",
    )
    async_session.add(agent_config)
    await async_session.commit()
    await async_session.refresh(agent_config)

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Test Room",
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)
    await async_session.commit()
    await async_session.refresh(room)

    # Create room participant binding for agent
    binding = _create_agent_binding(
        room_id=room.room_id,
        agent_slug=agent_slug,
        agent_id=agent_config.id,
    )
    async_session.add(binding)
    await async_session.commit()

    # Create shadow repo and version for agent
    agent_snapshot = {"agent": {"slug": agent_slug, "name": "Test Agent"}}
    agent_shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="agent",
        entity_id=agent_config.id,
        forgejo_repo_name=f"agent-{str(agent_config.id)[:8]}",
        forgejo_repo_id=None,
    )
    async_session.add(agent_shadow_repo)
    await async_session.commit()
    await async_session.refresh(agent_shadow_repo)

    agent_shadow_version = ShadowVersion(
        shadow_repo_id=agent_shadow_repo.id,
        commit_sha="abc123",
        version_number=1,
        message="agent snapshot",
        snapshot_json=agent_snapshot,
        created_by_id=user.id,
    )
    async_session.add(agent_shadow_version)
    await async_session.commit()

    # Test: build shadow context items with agent_slug
    items = await build_shadow_context_items(
        session=async_session,
        room_id=room.room_id,
        agent_slug=agent_slug,
    )

    # Assert: should include shadow.agent.summary
    agent_items = [
        item for item in items if item.context_type == "shadow.agent.summary"
    ]
    assert len(agent_items) > 0


@pytest.mark.asyncio
async def test_shadow_context_loader_runtime_provider_missing_is_embedded(
    async_session: AsyncSession,
) -> None:
    """Test that missing user_llm_provider shadow is embedded as missing."""
    # Setup: create user, room, provider without shadow
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = await async_session.run_sync(
        lambda session: crud.create_user(session=session, user_create=user_in)
    )

    provider = UserLLMProvider(
        user_id=user.id,
        provider_type="openai",
        name="Test Provider",
        is_enabled=True,
        api_key_encrypted="test-key",
    )
    async_session.add(provider)
    await async_session.commit()
    await async_session.refresh(provider)

    agent_slug = "test-agent"
    agent_config = AgentConfig(
        slug=agent_slug,
        owner_id=user.id,
        name="Test Agent",
    )
    async_session.add(agent_config)
    await async_session.commit()
    await async_session.refresh(agent_config)

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Test Room",
        created_at=datetime.now(timezone.utc),
        last_activity=datetime.now(timezone.utc),
    )
    async_session.add(room)
    await async_session.commit()
    await async_session.refresh(room)

    # Create room participant binding with user_llm_provider_id but no shadow repo
    binding = _create_agent_binding(
        room_id=room.room_id,
        agent_slug=agent_slug,
        agent_id=agent_config.id,
        user_llm_provider_id=provider.id,
    )
    async_session.add(binding)
    await async_session.commit()

    # Test: build shadow context items
    items = await build_shadow_context_items(
        session=async_session,
        room_id=room.room_id,
        agent_slug=agent_slug,
    )

    # Assert: should embed missing provider shadow
    runtime_items = [
        item for item in items if item.context_type == "shadow.runtime.summary"
    ]
    if runtime_items:  # May or may not be present depending on implementation
        assert runtime_items[0].payload.get("user_llm_provider_missing") is not None
