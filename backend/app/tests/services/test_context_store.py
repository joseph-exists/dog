"""Tests for ContextItemStore implementations."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.services.context_store import ContextItem, InMemoryContextStore


@pytest.mark.asyncio
async def test_in_memory_context_store_add_and_list() -> None:
    store = InMemoryContextStore()
    room_id = uuid.uuid4()
    now = datetime.now(tz=timezone.utc)

    item_room = ContextItem(
        id="1",
        room_id=room_id,
        agent_slug=None,
        context_type="room_seed",
        payload={"foo": "bar"},
        source="seed",
        created_at=now,
    )
    item_agent = ContextItem(
        id="2",
        room_id=room_id,
        agent_slug="story-advisor",
        context_type="upload",
        payload={"doc": "text"},
        source="frontend",
        created_at=now + timedelta(seconds=1),
    )

    await store.add(item_room)
    await store.add(item_agent)

    room_only = await store.list(room_id=room_id)
    assert room_only == [item_room]

    scoped = await store.list(room_id=room_id, agent_slug="story-advisor")
    assert scoped == [item_room, item_agent]
