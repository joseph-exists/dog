"""
Room CRUD Operations (Phase 1 - For Review)

This module contains room-related CRUD operations for Phase 1 implementation.
These operations are designed for review before being added to the centralized
CRUD layer (app/crud.py).

All operations follow Phase 1 requirements:
- Use async for I/O operations
- Enforce room-based authorization via RoomParticipant membership
- Use event_emitter.emit_event() for all writes (no direct projection updates)
- Support both user and agent participants as first-class entities

Authorization Pattern:
- All room reads require active membership
- Owner-only operations verify role == 'owner'
- Uses existing patterns, no bespoke utilities
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.rooms import (
    Message,
    MessagePublic,
    MessagesPublic,
    Room,
    RoomParticipant,
    RoomPublic,
    RoomsPublic,
)
from app.services.event_emitter import emit_event


# ============================================================================
# Authorization Helpers
# ============================================================================


async def check_room_membership(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user_id is an active user participant in room_id.

    This is the foundational authorization check for all room operations.
    Only active participants can read or write to a room.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is an active participant, False otherwise
    """
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()
    return participant is not None


async def check_room_owner(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user_id is an active participant with role == 'owner'.

    Owner-only operations (adding participants, changing roles, etc.)
    must verify ownership before proceeding.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is an active owner, False otherwise
    """
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.role == "owner",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()
    return participant is not None


# ============================================================================
# Room Creation & Management
# ============================================================================


async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting room.created and participant.joined events.

    This operation creates a room with the creator as the owner participant.
    All state changes are recorded as events and projections are updated
    transactionally.

    Args:
        creator_id: UUID of the user creating the room
        story_id: Optional UUID of associated story
        title: Optional room title
        session: Async database session

    Returns:
        The created Room projection

    Example:
        async with session.begin():
            room = await create_room(
                creator_id=user.id,
                story_id=story.id,
                title="Chapter 1 Discussion",
                session=session,
            )
    """
    room_id = UUID(int=0)  # Temporary, will be replaced
    from uuid import uuid4

    room_id = uuid4()

    async with session.begin():
        # Emit room.created event
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room.created",
            payload={
                "creator_id": str(creator_id),
                "story_id": str(story_id) if story_id else None,
                "title": title,
            },
        )

        # Emit participant.joined event for creator (as owner)
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="participant.joined",
            payload={
                "participant_id": str(creator_id),
                "participant_type": "user",
                "role": "owner",
            },
        )

    # Fetch and return the created room projection
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one()
    return room


async def list_rooms_for_user(
    *,
    user_id: UUID,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> RoomsPublic:
    """
    Return rooms where the user is an active participant, ordered by last_activity desc.

    This provides the user's room list for UI display. Only shows rooms where
    the user has active membership.

    Args:
        user_id: UUID of the user
        session: Async database session
        skip: Number of rooms to skip (pagination)
        limit: Maximum number of rooms to return

    Returns:
        RoomsPublic with data and count
    """
    # Query rooms where user is an active participant
    result = await session.execute(
        select(Room)
        .join(RoomParticipant)
        .where(
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
        .order_by(Room.last_activity.desc())
        .offset(skip)
        .limit(limit)
    )
    rooms = result.scalars().all()

    # Get total count
    count_result = await session.execute(
        select(Room)
        .join(RoomParticipant)
        .where(
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    total_count = len(count_result.scalars().all())

    return RoomsPublic(
        data=[RoomPublic.model_validate(room) for room in rooms],
        count=total_count,
    )


async def get_room_for_user(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> Room:
    """
    Fetch a room projection, only if the user is an active participant.

    This enforces authorization at the CRUD level. Non-participants
    cannot access room data.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        Room projection

    Raises:
        HTTPException: 403 if user is not an active participant
        HTTPException: 404 if room does not exist
    """
    # Check membership first
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch room
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


async def update_room_metadata(
    *,
    room_id: UUID,
    user_id: UUID,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Update room metadata via event emission (room.updated).

    Policy: Owner-only operation (enforced in Phase 1).
    Future phases may allow members to update certain fields.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user (must be owner)
        title: New title for the room
        session: Async database session

    Returns:
        Updated Room projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 404 if room does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can update room metadata",
        )

    # Build updated fields payload
    updated_fields = {}
    if title is not None:
        updated_fields["title"] = title

    if not updated_fields:
        # No changes requested, return current room
        return await get_room_for_user(room_id=room_id, user_id=user_id, session=session)

    # Emit room.updated event
    async with session.begin():
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room.updated",
            payload={"updated_fields": updated_fields},
        )

    # Fetch and return updated room
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one()
    return room


# ============================================================================
# Participant Management
# ============================================================================


async def add_participant(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    participant_type: str,
    role: str,
    session: AsyncSession,
) -> RoomParticipant:
    """
    Add a user or agent to a room (owner-only operation).

    This operation is idempotent: re-adding an inactive participant
    will reactivate them via the participant.joined event handler.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        participant_type: "user" or "agent"
        role: "owner" or "member"
        session: Async database session

    Returns:
        RoomParticipant projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 400 if participant_type or role is invalid
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can add participants",
        )

    # Validate participant_type
    if participant_type not in ("user", "agent"):
        raise HTTPException(
            status_code=400,
            detail="participant_type must be 'user' or 'agent'",
        )

    # Validate role
    if role not in ("owner", "member"):
        raise HTTPException(
            status_code=400,
            detail="role must be 'owner' or 'member'",
        )

    # Emit participant.joined event (idempotent via handler)
    async with session.begin():
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="participant.joined",
            payload={
                "participant_id": participant_id,
                "participant_type": participant_type,
                "role": role,
            },
        )

    # Fetch and return participant
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.scalar_one()
    return participant


async def remove_participant(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    session: AsyncSession,
) -> None:
    """
    Remove a participant from a room (owner-only, soft delete).

    Emits participant.left event which sets active=False in the projection.
    Historical events are preserved (never deleted).

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        session: Async database session

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 404 if participant does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can remove participants",
        )

    # Verify participant exists
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Emit participant.left event
    async with session.begin():
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="participant.left",
            payload={"participant_id": participant_id},
        )


async def change_participant_role(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    new_role: str,
    session: AsyncSession,
) -> RoomParticipant:
    """
    Change a participant's role (owner-only operation).

    Emits participant.role_changed event to update the projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        new_role: "owner" or "member"
        session: Async database session

    Returns:
        Updated RoomParticipant projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 400 if new_role is invalid
        HTTPException: 404 if participant does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can change participant roles",
        )

    # Validate new_role
    if new_role not in ("owner", "member"):
        raise HTTPException(
            status_code=400,
            detail="new_role must be 'owner' or 'member'",
        )

    # Verify participant exists
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Emit participant.role_changed event
    async with session.begin():
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="participant.role_changed",
            payload={
                "participant_id": participant_id,
                "new_role": new_role,
            },
        )

    # Fetch and return updated participant
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.scalar_one()
    return participant


# ============================================================================
# Message Operations
# ============================================================================


async def list_room_messages(
    *,
    room_id: UUID,
    user_id: UUID,
    limit: int,
    before: datetime | None,
    session: AsyncSession,
) -> MessagesPublic:
    """
    List messages from the Message projection with pagination constraints.

    Uses cursor-based pagination via 'before' timestamp for efficient
    pagination of large message histories.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user (must be active participant)
        limit: Maximum number of messages to return
        before: Optional timestamp cursor for pagination
        session: Async database session

    Returns:
        MessagesPublic with data and count

    Raises:
        HTTPException: 403 if user is not an active participant
    """
    # Check membership
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Build query with optional cursor
    query = (
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )

    if before:
        query = query.where(Message.created_at < before)

    result = await session.execute(query)
    messages = result.scalars().all()

    # Get total count for this room
    count_result = await session.execute(
        select(Message).where(Message.room_id == room_id)
    )
    total_count = len(count_result.scalars().all())

    return MessagesPublic(
        data=[MessagePublic.model_validate(msg) for msg in messages],
        count=total_count,
    )


async def send_user_message(
    *,
    room_id: UUID,
    user_id: UUID,
    content: str,
    session: AsyncSession,
) -> Message:
    """
    Send a user message to a room.

    Emits message.user event which creates the message projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user sending the message
        content: Message content
        session: Async database session

    Returns:
        Created Message projection

    Raises:
        HTTPException: 403 if user is not an active participant
    """
    # Check membership
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Emit message.user event
    async with session.begin():
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="message.user",
            payload={
                "sender_id": str(user_id),
                "content": content,
            },
        )

    # Fetch the most recent message for this user
    result = await session.execute(
        select(Message)
        .where(
            Message.room_id == room_id,
            Message.sender_id == user_id,
        )
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    message = result.scalar_one()
    return message
