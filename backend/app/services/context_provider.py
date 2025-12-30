"""
Context Provider Service: Room-aware context builder for agents.

Provides limited context (20 messages + story outline) to prevent
context window overflow while maintaining conversation relevance.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Room, RoomMessage, RoomParticipant, Story


@dataclass
class RoomContext:
    """
    Context object passed to agents for room-aware responses.

    Attributes:
        room_id: UUID of the current room
        story_id: Optional UUID of associated story
        story_data: Story details (title, description) if available
        recent_messages: Last N messages for conversation context
        participants: List of active participants (users and agents)
        room_metadata: Room title, creator, timestamps
    """

    room_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict[str, Any] | None
    recent_messages: list[dict[str, Any]]
    participants: list[dict[str, Any]]
    room_metadata: dict[str, Any]


async def build_room_context(
    *,
    room_id: uuid.UUID,
    session: AsyncSession,
    message_limit: int = 20,
) -> RoomContext:
    """
    Build context for an agent given a room_id.

    This function:
    1. Loads room metadata (title, story_id, etc.)
    2. Loads associated story data if present
    3. Fetches last N messages for conversation context
    4. Lists active participants

    Args:
        room_id: UUID of the room
        session: Async database session
        message_limit: Max messages to include (default 20)

    Returns:
        RoomContext with all data needed for agent response

    Raises:
        ValueError: If room does not exist
    """
    # Load room
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one_or_none()
    if not room:
        raise ValueError(f"Room {room_id} not found")

    # Load story data if associated
    story_data = None
    if room.story_id:
        story_result = await session.execute(
            select(Story).where(Story.id == room.story_id)
        )
        story = story_result.scalar_one_or_none()
        if story:
            story_data = {
                "id": str(story.id),
                "title": story.title,
                "description": story.description,
                "is_published": story.is_published,
            }

    # Load recent messages (ordered by created_at desc, then reversed)
    messages_result = await session.execute(
        select(RoomMessage)
        .where(RoomMessage.room_id == room_id)
        .order_by(RoomMessage.created_at.desc())
        .limit(message_limit)
    )
    messages = messages_result.scalars().all()

    recent_messages = [
        {
            "message_id": str(msg.message_id),
            "sender_type": msg.sender_type,
            "sender_id": str(msg.sender_id) if msg.sender_id else None,
            "agent_name": msg.agent_name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)  # Chronological order
    ]

    # Load active participants
    participants_result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participants_list = participants_result.scalars().all()

    participants = [
        {
            "participant_id": p.participant_id,
            "participant_type": p.participant_type,
            "role": p.role,
            "joined_at": p.joined_at.isoformat(),
        }
        for p in participants_list
    ]

    room_metadata = {
        "room_id": str(room.room_id),
        "title": room.title,
        "creator_id": str(room.creator_id),
        "created_at": room.created_at.isoformat(),
        "last_activity": room.last_activity.isoformat(),
    }

    return RoomContext(
        room_id=room_id,
        story_id=room.story_id,
        story_data=story_data,
        recent_messages=recent_messages,
        participants=participants,
        room_metadata=room_metadata,
    )
