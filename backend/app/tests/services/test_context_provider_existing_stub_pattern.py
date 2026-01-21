"""
Test suite for verifying that existing context_provider tests properly handle
Shadow context injection. These tests validate that build_room_context behavior
works correctly when shadow context loading is in the system.
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import Room, User, UserCreate
from app.services.context_provider import build_room_context
from app.services.context_store import InMemoryContextStore


@pytest.mark.asyncio
async def test_build_room_context_shadow_injection_stub(
    async_session: AsyncSession,
) -> None:
    """
    Verify that existing unit tests can stub shadow injection.
    
    This test demonstrates the pattern for existing tests that need to
    keep their narrow scope by stubbing Shadow context loading.
    """
    # Setup: create user and room
    user_in = UserCreate(email=f"test-{uuid.uuid4()}@example.com", password="password123")
    from app import crud

    user: User = await async_session.run_sync(
        lambda session: crud.create_user(session=session, user_create=user_in)
    )

    room = Room(
        room_id=uuid.uuid4(),
        creator_id=user.id,
        title="Test Room",
    )
    async_session.add(room)
    await async_session.commit()
    await async_session.refresh(room)

    # Stub shadow injection to return empty list (keeps unit test scope narrow)
    with patch(
        "app.services.context_provider.build_shadow_context_items",
        new_callable=AsyncMock,
        return_value=[],
    ):
        context_store = InMemoryContextStore()
        context = await build_room_context(
            session=async_session,
            room_id=room.room_id,
            context_store=context_store,
            agent_slug=None,
        )

        # Assert: context is built without shadow items
        assert context is not None
        # Shadow items should not be added since we stubbed it to return empty list
        shadow_items = [
            item for item in (context.extra_contexts or [])
            if item.get("source") == "shadow"
        ]
        assert len(shadow_items) == 0
