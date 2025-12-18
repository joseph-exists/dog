"""
Room API Routes (Phase 1)

This module implements the REST API endpoints for multi-user, multi-agent
collaborative chat rooms following the Phase 1 Plan requirements.

All endpoints use async for I/O operations and enforce room-based authorization
via active membership in RoomParticipant.

Architecture:
- All writes go through event_emitter.emit_event()
- Authorization enforced at CRUD level
- Supports both user and agent participants as first-class entities
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud import (
    add_participant,
    change_participant_role,
    create_room,
    get_room_for_user,
    list_room_messages,
    list_rooms_for_user,
    remove_participant,
    send_user_message,
    update_room_metadata,
)
from app.models import (
    Message,
    RoomMessage,
    RoomMessagePublic,
    RoomMessagesPublic,
    RoomParticipant,
    RoomParticipantPublic,
    RoomParticipantsPublic,
    RoomPublic,
    RoomsPublic,
)

router = APIRouter(prefix="/rooms", tags=["rooms"])


# ============================================================================
# Request/Response Models
# ============================================================================


class RoomCreateRequest(BaseModel):
    """Request model for creating a room."""

    title: str | None = None
    story_id: UUID | None = None


class RoomUpdateRequest(BaseModel):
    """Request model for updating room metadata."""

    title: str | None = None


class ParticipantAddRequest(BaseModel):
    """Request model for adding a participant to a room."""

    participant_id: str
    participant_type: str  # "user" | "agent"
    role: str = "member"  # "owner" | "member"


class ParticipantRoleChangeRequest(BaseModel):
    """Request model for changing a participant's role."""

    new_role: str  # "owner" | "member"


class MessageSendRequest(BaseModel):
    """Request model for sending a message."""

    content: str


# ============================================================================
# Room Endpoints
# ============================================================================


@router.post("/", response_model=RoomPublic)
async def create_new_room(
    *,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    room_in: RoomCreateRequest,
) -> Any:
    """
    Create a new room.

    The current user becomes the room owner. Optionally associate with a story.

    Event flow:
    1. Emits room.created event
    2. Emits participant.joined event for creator (as owner)
    3. Returns room projection
    """
    room = await create_room(
        creator_id=current_user.id,
        story_id=room_in.story_id,
        title=room_in.title,
        session=session,
    )
    return room


@router.get("/", response_model=RoomsPublic)
async def list_user_rooms(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all rooms where the current user is an active participant.

    Returns rooms ordered by last_activity (most recent first).
    """
    rooms = await list_rooms_for_user(
        user_id=current_user.id,
        session=session,
        skip=skip,
        limit=limit,
    )
    return rooms


@router.get("/{room_id}", response_model=RoomPublic)
async def get_room(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get room details by ID.

    Only accessible to active participants.
    """
    room = await get_room_for_user(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    return room


@router.patch("/{room_id}", response_model=RoomPublic)
async def update_room(
    *,
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    room_in: RoomUpdateRequest,
) -> Any:
    """
    Update room metadata (owner-only).

    Emits room.updated event with changed fields.
    """
    room = await update_room_metadata(
        room_id=room_id,
        user_id=current_user.id,
        title=room_in.title,
        session=session,
    )
    return room


# ============================================================================
# Participant Endpoints
# ============================================================================


@router.post("/{room_id}/participants", response_model=RoomParticipantPublic)
async def add_room_participant(
    *,
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    participant_in: ParticipantAddRequest,
) -> Any:
    """
    Add a participant to a room (owner-only).

    Supports adding both users and agents. Operation is idempotent:
    re-adding an inactive participant will reactivate them.

    Event flow:
    1. Verifies current user is room owner
    2. Emits participant.joined event
    3. Returns participant projection

    Args:
        participant_id: UUID string for users, agent name for agents
        participant_type: "user" or "agent"
        role: "owner" or "member" (default: "member")
    """
    participant = await add_participant(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_in.participant_id,
        participant_type=participant_in.participant_type,
        role=participant_in.role,
        session=session,
    )
    return participant


@router.get("/{room_id}/participants", response_model=RoomParticipantsPublic)
async def list_room_participants(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    List all active participants in a room.

    Only accessible to room participants. Returns both users and agents.
    """
    from sqlalchemy import select

    # Check membership first
    from app.for_review_crud import check_room_membership

    if not await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    ):
        raise HTTPException(status_code=403, detail="Access denied")

    # Query active participants
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participants = result.scalars().all()

    return RoomParticipantsPublic(
        data=[RoomParticipantPublic.model_validate(p) for p in participants],
        count=len(participants),
    )


@router.delete("/{room_id}/participants/{participant_id}")
async def remove_room_participant(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Message:
    """
    Remove a participant from a room (owner-only, soft delete).

    Emits participant.left event which sets active=False.
    Historical events are preserved.

    Args:
        participant_id: UUID string for users, agent name for agents
    """
    await remove_participant(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_id,
        session=session,
    )
    return Message(message="Participant removed successfully")


@router.patch("/{room_id}/participants/{participant_id}/role", response_model=RoomParticipantPublic)
async def change_room_participant_role(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    role_in: ParticipantRoleChangeRequest,
) -> Any:
    """
    Change a participant's role (owner-only).

    Emits participant.role_changed event.

    Args:
        participant_id: UUID string for users, agent name for agents
        new_role: "owner" or "member"
    """
    participant = await change_participant_role(
        room_id=room_id,
        user_id=current_user.id,
        participant_id=participant_id,
        new_role=role_in.new_role,
        session=session,
    )
    return participant


# ============================================================================
# Message Endpoints
# ============================================================================


@router.post("/{room_id}/messages", response_model=MessagePublic)
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    message_in: MessageSendRequest,
) -> Any:
    """
    Send a message to a room.

    Emits message.user event. In Phase 2, this will also trigger
    agent execution if agents are configured to respond.

    Only accessible to active participants.
    """
    message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,
    )
    return message


@router.get("/{room_id}/messages", response_model=MessagesPublic)
async def list_messages(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=50, le=100),
    before: datetime | None = Query(default=None),
) -> Any:
    """
    List messages in a room with cursor-based pagination.

    Only accessible to active participants.

    Args:
        limit: Maximum number of messages to return (max 100)
        before: Cursor timestamp - returns messages before this time
    """
    messages = await list_room_messages(
        room_id=room_id,
        user_id=current_user.id,
        limit=limit,
        before=before,
        session=session,
    )
    return messages
