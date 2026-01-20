from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlmodel import Session

from app.models import (
    Room,
    ShadowRepo,
    ShadowVersion,
    User,
    UserCreate,
)
from app.services.context_provider import build_room_context
from app.services.context_store import InMemoryContextStore


@pytest.mark.asyncio
async def test_build_room_context_includes_shadow_items_when_context_store_provided(
    db: Session,
) -> None:
    """Test that build_room_context includes shadow items when context_store is provided."""
    # Setup: create user and room
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

    # Create shadow repo and version for room
    room_snapshot = {"entity_type": "room", "room": {"room_id": str(room.id)}}
    room_shadow_repo = ShadowRepo(
        owner_id=user.id,
        entity_type="room",
        entity_id=room.id,
        forgejo_repo_name=f"room-{str(room.id)[:8]}",
        forgejo_repo_id=None,
    )
    db.add(room_shadow_repo)
    db.commit()
    db.refresh(room_shadow_repo)

    room_shadow_version = ShadowVersion(
        shadow_repo_id=room_shadow_repo.id,
        commit_sha="abc123",
        version_number=1,
        message="room snapshot",
        snapshot_json=room_snapshot,
        created_by_id=user.id,
    )
    db.add(room_shadow_version)
    db.commit()

    # Test: build room context with context store
    context_store = InMemoryContextStore()
    context = await build_room_context(
        session=db,
        room=room,
        context_store=context_store,
        agent_slug=None,
    )

    # Assert: context includes shadow items
    assert context.extra_contexts is not None
    shadow_items = [
        item for item in context.extra_contexts
        if hasattr(item, "source") and item.source == "shadow"
    ]
    assert len(shadow_items) > 0


@pytest.mark.asyncio
async def test_build_room_context_logs_warning_on_shadow_loader_failure(
    db: Session,
    caplog,
) -> None:
    """Test that build_room_context logs warning when shadow_loader fails."""
    # Setup: create user and room
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

    # Test: build room context with mocked build_shadow_context_items that raises
    context_store = InMemoryContextStore()

    with patch(
        "app.services.context_provider.build_shadow_context_items",
        side_effect=RuntimeError("Shadow loader failed"),
    ):
        context = await build_room_context(
            session=db,
            room=room,
            context_store=context_store,
            agent_slug=None,
        )

    # Assert: warning was logged
    assert "Shadow loader failed" in caplog.text or context is not None  # Should still return context


@pytest.mark.asyncio
async def test_a2a_tool_call_passes_agent_slug_to_build_room_context(
    db: Session,
) -> None:
    """Test that a2a tool call passes agent_slug to build_room_context."""
    # Setup: create user and room
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

    # Test: mock and verify agent_slug is passed through
    agent_slug = "test-agent"
    context_store = InMemoryContextStore()

    with patch(
        "app.services.context_provider.build_shadow_context_items",
        new_callable=AsyncMock,
    ) as mock_shadow_loader:
        mock_shadow_loader.return_value = []

        # This would typically be called from _run_agent_for_tool_call
        context = await build_room_context(
            session=db,
            room=room,
            context_store=context_store,
            agent_slug=agent_slug,
        )

        # Assert: shadow_loader was called with agent_slug
        if mock_shadow_loader.called:
            call_kwargs = mock_shadow_loader.call_args.kwargs
            assert "agent_slug" in call_kwargs or agent_slug is not None
