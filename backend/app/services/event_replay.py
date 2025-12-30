"""
Event Replay Service: Sequence-based event replay for reconnecting clients.

When a client reconnects, they provide the last sequence number they received.
This service queries the event log and returns all events with higher sequences.

This enables:
1. Seamless reconnection after temporary network issues
2. Catching up after client was offline
3. No message loss under normal conditions
"""
from __future__ import annotations

import logging
from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RoomEvent

logger = logging.getLogger(__name__)


async def replay_events_since(
    *,
    session: AsyncSession,
    room_id: UUID,
    after_sequence: int,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """
    Replay events from event log for a room.

    Used for reconnection and catching up on missed events.

    Args:
        session: Async database session
        room_id: UUID of the room
        after_sequence: Last sequence the client received
        limit: Max events to return (default 1000, prevents huge replays)

    Returns:
        List of event dicts in AG-UI format:
        {
            "type": "event",
            "sequence": int,
            "event_type": str,
            "payload": {...},
            "created_at": ISO timestamp
        }

    Notes:
    - Events are ordered by room_sequence (ascending)
    - Large replays (>limit) return first N events + warning
    - Client should handle pagination if needed (future enhancement)
    """
    result = await session.execute(
        select(RoomEvent)
        .where(
            RoomEvent.room_id == room_id,
            RoomEvent.room_sequence > after_sequence,
        )
        .order_by(RoomEvent.room_sequence)
        .limit(limit)
    )
    events = result.scalars().all()

    if len(events) >= limit:
        logger.warning(
            f"Replay limit reached for room {room_id}: "
            f"{len(events)} events after sequence {after_sequence}"
        )

    return [
        {
            "type": "event",
            "sequence": event.room_sequence,
            "event_type": event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


async def get_latest_sequence(
    *,
    session: AsyncSession,
    room_id: UUID,
) -> int:
    """
    Get the latest sequence number for a room.

    Used for clients to know if they're caught up.

    Returns:
        Latest sequence number, or 0 if no events
    """
    result = await session.execute(
        select(RoomEvent.room_sequence)
        .where(RoomEvent.room_id == room_id)
        .order_by(RoomEvent.room_sequence.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    return latest if latest is not None else 0