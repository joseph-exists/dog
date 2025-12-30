"""
Event Emitter Service: Single write-path for room state changes.

This module implements the Phase 1 event-sourcing pattern with transactional
projections. It is the ONLY supported mechanism for room-related writes.

CRITICAL INVARIANTS:
- Events are immutable (append-only, never UPDATE/DELETE)
- Event ordering is per-room via monotonically increasing room_sequence
- Projections are updated transactionally with event writes
- Projections are fully rebuildable by replaying events in sequence order
- All writes must go through emit_event() to maintain consistency

Phase 4 Preparation:
- Redis pub/sub fan-out will be added to emit_event()
- WebSocket clients will receive events in real-time
- Sequence-based replay will handle reconnections

Architecture Compliance:
- Async-first I/O for multi-worker responsiveness (per MasterImplementationPlan.md)
- Transactional projection updates for read-after-write consistency
- Database-level sequence generation for concurrent write safety
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func

from app.core.redis import get_redis

from app.models import (
    RoomMessage,
    Room,
    RoomEvent,
    RoomParticipant,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Event Emission (Write Path)
# ============================================================================


async def emit_event(
    session: AsyncSession,
    room_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
    enrichment_metadata: dict[str, Any] | None = None,
) -> RoomEvent:
    """
    Emit a room event and update projections transactionally.

    This is the single write-path for all room state changes. It ensures:
    1. Event is appended to immutable room_events log
    2. room_sequence is monotonically increasing per room
    3. Projections are updated in the same transaction
    4. Strong read-after-write consistency is maintained

    TRANSACTION REQUIREMENTS:
    This function expects to be called within an active transaction. The
    transaction is managed by the route handler using AsyncSessionTransactionDep.
    This ensures atomic operations across multiple events and projections.

    Args:
        session: Async database session with active transaction
        room_id: UUID of the room
        event_type: Event type (e.g., "room.created", "room_message.user")
        payload: Event-specific data as dict
        enrichment_metadata: Optional metadata for trace IDs, performance metrics, etc.

    Returns:
        The created RoomEvent

    Raises:
        ValueError: If event_type is not supported
        sqlalchemy.exc.IntegrityError: If sequence constraint is violated

    Example:
        # Route handler manages transaction
        @router.post("/{room_id}/messages")
        async def send_message(
            session: AsyncSessionTransactionDep,  # Transaction starts here
            ...
        ):
            # emit_event uses route-level transaction
            event = await emit_event(
                session,
                room_id,
                "room_message.user",
                {
                    "sender_id": str(user_id),
                    "content": "Hello world",
                },
            )
            # Transaction commits automatically on return
            return event

    Event Types (Phase 1):
        - room.created: New room created
        - room.updated: Room metadata changed
        - participant.joined: User or agent joined
        - participant.left: User or agent left (soft delete)
        - participant.role_changed: Participant role updated
        - room_message.user: User sent message
        - room_message.agent: Agent sent message
    
    Phase 4 Enhancement: Publishes event to Redis after transaction flush
    for real-time delivery to WebSocket clients.
    
    Future: see Phase2-addendum.md for usage post Phase 4.

    """
    # Generate next sequence number for this room
    next_sequence = await _get_next_room_sequence(session, room_id)

    # Create immutable event
    event = RoomEvent(
        event_id=uuid.uuid4(),
        room_id=room_id,
        room_sequence=next_sequence,
        event_type=event_type,
        payload=payload,
        enrichment_metadata=enrichment_metadata,
        created_at=datetime.utcnow(),
    )

    session.add(event)

    # Update projections based on event type
    await _update_projections(session, event)

    # Flush to make projection changes visible to subsequent queries in this transaction
    # This is required for read-after-write consistency within the same request
    await session.flush()

    await _publish_to_redis(room_id, event)

    return event

async def _publish_to_redis(room_id: uuid.UUID, event: RoomEvent) -> None:
    """
    Publish event to Redis pub/sub for real-time delivery.

    This enables multi-worker fanout - all workers subscribed to the room
    channel will receive the event and forward to their connected WebSocket clients.

    Channel naming: room:{room_id}

    Message format (AG-UI compatible):
    {
        "type": "event",
        "sequence": room_sequence,
        "event_type": event_type,
        "payload": {...},
        "created_at": ISO timestamp
    }

    Failure handling:
    - If Redis unavailable, logs error but does NOT fail transaction
    - Event is still persisted in Postgres (clients will catch up via replay)
    - This ensures graceful degradation
    """
    try:
        redis = await get_redis()

        message = {
            "type": "event",
            "sequence": event.room_sequence,
            "event_type": event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }

        channel = f"room:{room_id}"
        await redis.publish(channel, json.dumps(message))

    except Exception as e:
        # Don't fail transaction if Redis publish fails
        # Clients will catch up via replay on reconnect
        logger.warning(f"Failed to publish event to Redis: {e}")

## Agent Token Streaming Support

async def publish_agent_token(
    room_id: uuid.UUID,
    agent_name: str,
    token: str,
) -> None:
    """
    Publish a single token from agent streaming.

    This is an EPHEMERAL message (not persisted to Postgres).
    Used for real-time token-by-token streaming during agent responses.

    Final complete message is still persisted via room_message.agent event.

    Message format (AG-UI compatible):
    {
        "type": "message.delta",
        "agent_name": str,
        "content": str (single token)
    }
    """
    try:
        redis = await get_redis()

        message = {
            "type": "message.delta",
            "agent_name": agent_name,
            "content": token,
        }

        channel = f"room:{room_id}"
        await redis.publish(channel, json.dumps(message))

    except Exception as e:
        # Gracefully ignore - full message will be delivered via event
        logger.debug(f"Failed to publish token to Redis: {e}")


# ============================================================================
# Sequence Generation
# ============================================================================


async def _get_next_room_sequence(
    session: AsyncSession,
    room_id: uuid.UUID,
) -> int:
    """
    Generate the next monotonic sequence number for a room.

    Uses MAX(room_sequence) + 1 to ensure sequences are monotonically
    increasing. This is safe under concurrent writes because the
    (room_id, room_sequence) unique constraint will catch conflicts
    and the transaction will be retried by the caller.

    Note: Sequences may have gaps (not consecutive) which is acceptable
    for event sourcing. Clients must not assume consecutive sequences.

    Args:
        session: Async database session
        room_id: UUID of the room

    Returns:
        Next sequence number (1 for first event, MAX + 1 for subsequent)

    Uses Postgres advisory lock to prevent race conditions in multi-worker
    environments. The lock is automatically released at transaction end.

    Lock key is hash of room_id to ensure per-room locking granularity.
    """
    
    # Advisory lock for this room (transaction-scoped)
    lock_key = hash(room_id) % (2**31)  # Postgres bigint range
    await session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": lock_key}
    )
    result = await session.execute(
        select(func.max(RoomEvent.room_sequence)).where(
            RoomEvent.room_id == room_id
        )
    )
    max_sequence = result.scalar()

    # First event in room starts at sequence 1
    return 1 if max_sequence is None else max_sequence + 1


# ============================================================================
# Projection Updates
# ============================================================================


async def _update_projections(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Update projection tables based on event type.

    This function is called within the same transaction as the event write,
    ensuring projections are always consistent with the event log.

    Projections can be fully rebuilt by replaying all events in sequence order
    and calling this function for each event.

    Args:
        session: Async database session
        event: The event to process
    """
    handlers = {
        "room.created": _handle_room_created,
        "room.updated": _handle_room_updated,
        "participant.joined": _handle_participant_joined,
        "participant.left": _handle_participant_left,
        "participant.role_changed": _handle_participant_role_changed,
        "room_message.user": _handle_room_message_user,
        "room_message.agent": _handle_room_message_agent,
    }

    handler = handlers.get(event.event_type)
    if handler is None:
        raise ValueError(f"Unsupported event type: {event.event_type}")

    await handler(session, event)

    # Update room.last_activity for all event types
    await _update_room_last_activity(session, event.room_id, event.created_at)


# ============================================================================
# Room Event Handlers
# ============================================================================


async def _handle_room_created(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle room.created event.

    Payload:
        - creator_id: UUID (required)
        - title: str (optional)
        - story_id: UUID (optional)
    """
    payload = event.payload

    room = Room(
        room_id=event.room_id,
        creator_id=uuid.UUID(payload["creator_id"]),
        title=payload.get("title"),
        story_id=uuid.UUID(payload["story_id"]) if payload.get("story_id") else None,
        created_at=event.created_at,
        last_activity=event.created_at,
    )

    session.add(room)


async def _handle_room_updated(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle room.updated event.

    Payload:
        - updated_fields: dict with fields to update (e.g., {"title": "New Title"})
    """
    result = await session.execute(
        select(Room).where(Room.room_id == event.room_id)
    )
    room = result.scalar_one()

    updated_fields = event.payload.get("updated_fields", {})
    for field, value in updated_fields.items():
        if hasattr(room, field):
            setattr(room, field, value)

    session.add(room)


async def _update_room_last_activity(
    session: AsyncSession,
    room_id: uuid.UUID,
    timestamp: datetime,
) -> None:
    """Update room.last_activity timestamp."""
    result = await session.execute(
        select(Room).where(Room.room_id == room_id)
    )
    room = result.scalar_one_or_none()

    if room:
        room.last_activity = timestamp
        session.add(room)


# ============================================================================
# Participant Event Handlers
# ============================================================================


async def _handle_participant_joined(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle participant.joined event.

    Supports both initial join and re-join (reactivation).

    Payload:
        - participant_id: str (UUID string for users, agent name for agents)
        - participant_type: "user" | "agent" (required)
        - role: "owner" | "member" (required)
    """
    payload = event.payload

    # Check if participant previously existed (re-join scenario)
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == event.room_id,
            RoomParticipant.participant_id == payload["participant_id"],
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Reactivate existing participant
        existing.active = True
        existing.joined_at = event.created_at
        existing.left_at = None
        existing.role = payload["role"]
        session.add(existing)
    else:
        # Create new participant
        participant = RoomParticipant(
            id=uuid.uuid4(),
            room_id=event.room_id,
            participant_id=payload["participant_id"],
            participant_type=payload["participant_type"],
            role=payload["role"],
            joined_at=event.created_at,
            active=True,
        )
        session.add(participant)


async def _handle_participant_left(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle participant.left event (soft delete).

    Payload:
        - participant_id: str (UUID string for users, agent name for agents)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == event.room_id,
            RoomParticipant.participant_id == payload["participant_id"],
        )
    )
    participant = result.scalar_one()

    participant.active = False
    participant.left_at = event.created_at

    session.add(participant)


async def _handle_participant_role_changed(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle participant.role_changed event.

    Payload:
        - participant_id: str (UUID string for users, agent name for agents)
        - new_role: "owner" | "member" (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == event.room_id,
            RoomParticipant.participant_id == payload["participant_id"],
        )
    )
    participant = result.scalar_one()

    participant.role = payload["new_role"]

    session.add(participant)


# ============================================================================
# Message Event Handlers
# ============================================================================


async def _handle_room_message_user(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle room_message.user event.

    Payload:
        - sender_id: UUID string (required)
        - content: str (required)
    """
    payload = event.payload

    room_message = RoomMessage(
        message_id=uuid.uuid4(),
        room_id=event.room_id,
        sender_type="user",
        sender_id=uuid.UUID(payload["sender_id"]),
        agent_name=None,
        content=payload["content"],
        created_at=event.created_at,
    )

    session.add(room_message)


async def _handle_room_message_agent(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle room_message.agent event.

    Payload:
        - agent_name: str (required)
        - content: str (required)
    """
    payload = event.payload

    room_message = RoomMessage(
        message_id=uuid.uuid4(),
        room_id=event.room_id,
        sender_type="agent",
        sender_id=None,
        agent_name=payload["agent_name"],
        content=payload["content"],
        created_at=event.created_at,
    )

    session.add(room_message)


# ============================================================================
# Event Replay (For Testing & Recovery)
# ============================================================================


async def replay_events_for_room(
    session: AsyncSession,
    room_id: uuid.UUID,
) -> None:
    """
    Rebuild projections for a room by replaying all events.

    This is primarily used for:
    1. Testing projection correctness
    2. Recovering from projection corruption
    3. Migrating to new projection schemas

    WARNING: This deletes and rebuilds ALL projections for the room.
    Should only be used in controlled scenarios.

    Args:
        session: Async database session (must be within a transaction)
        room_id: UUID of the room to replay
    """
    # Delete existing projections for this room
    await session.execute(
        select(RoomMessage).where(RoomMessage.room_id == room_id)
    )
    await session.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    )
    await session.execute(
        select(Room).where(Room.room_id == room_id)
    )

    # Replay all events in sequence order
    result = await session.execute(
        select(RoomEvent)
        .where(RoomEvent.room_id == room_id)
        .order_by(RoomEvent.room_sequence)
    )
    events = result.scalars().all()

    for event in events:
        await _update_projections(session, event)
