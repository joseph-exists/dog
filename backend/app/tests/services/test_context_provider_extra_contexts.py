"""Tests for context_provider extra contexts aggregation."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.services.context_provider import build_room_context
from app.services.context_store import ContextItem, InMemoryContextStore


@pytest.mark.asyncio
async def test_build_context_includes_extra_contexts_ordered(
    async_session, test_room
) -> None:
    store = InMemoryContextStore()
    room_id = test_room.room_id
    now = datetime.now(tz=timezone.utc)

    await store.add(
        ContextItem(
            id="1",
            room_id=room_id,
            agent_slug=None,
            context_type="room_seed",
            payload={"seed": 1},
            source="seed",
            created_at=now,
        )
    )
    await store.add(
        ContextItem(
            id="2",
            room_id=room_id,
            agent_slug=None,
            context_type="hotload",
            payload={"hot": 2},
            source="backend",
            created_at=now + timedelta(seconds=1),
        )
    )
    await store.add(
        ContextItem(
            id="3",
            room_id=room_id,
            agent_slug=None,
            context_type="upload",
            payload={"file": 3},
            source="frontend",
            created_at=now + timedelta(seconds=2),
        )
    )

    context = await build_room_context(
        room_id=room_id,
        session=async_session,
        context_store=store,
    )

    assert [item["source"] for item in context.extra_contexts] == [
        "seed",
        "backend",
        "frontend",
    ]


@pytest.mark.asyncio
async def test_build_context_scopes_agent_specific_items(
    async_session, test_room
) -> None:
    store = InMemoryContextStore()
    room_id = test_room.room_id
    now = datetime.now(tz=timezone.utc)

    await store.add(
        ContextItem(
            id="1",
            room_id=room_id,
            agent_slug=None,
            context_type="room_seed",
            payload={"seed": 1},
            source="seed",
            created_at=now,
        )
    )
    await store.add(
        ContextItem(
            id="2",
            room_id=room_id,
            agent_slug="story-advisor",
            context_type="upload",
            payload={"doc": "agent"},
            source="frontend",
            created_at=now + timedelta(seconds=1),
        )
    )

    context = await build_room_context(
        room_id=room_id,
        session=async_session,
        agent_slug="story-advisor",
        context_store=store,
    )

    assert len(context.extra_contexts) == 2
