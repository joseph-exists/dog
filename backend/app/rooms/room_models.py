"""
Room models for multi-user, multi-agent collaborative chat.

This module implements the Phase 1 event-sourcing and projection models:
- Room: Projection of room metadata
- RoomParticipant: Projection of room membership (users and agents)
- Message: Projection of conversation messages
- RoomEvent: Append-only system of record for all room state changes

All models follow the project's standard pattern:
Base → Create → Update → Table → Public → Collection

Relationships use string-based forward references and post-definition binding
to handle circular dependencies per data-model-best-practices.md.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, Relationship, SQLModel


# ============================================================================
# Room Models (Projection)
# ============================================================================


class RoomBase(SQLModel):
    """Shared properties for Room projection."""

    title: str | None = Field(default=None, max_length=255)
    story_id: uuid.UUID | None = Field(default=None, foreign_key="story.id")


class RoomCreate(RoomBase):
    """Properties required when creating a room via API."""

    # creator_id will be injected from current_user, not from API input
    pass


class RoomUpdate(SQLModel):
    """Properties that can be updated via API."""

    title: str | None = Field(default=None, max_length=255)


class Room(RoomBase, table=True):
    """
    Room projection table (derived from RoomEvent log).

    This is a query-optimized view of room state, updated transactionally
    with event writes to ensure read-after-write consistency.
    """

    __tablename__ = "rooms"

    room_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    creator_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_activity: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    # Relationships (using string forward references)
    participants: list["RoomParticipant"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )
    messages: list["Message"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )
    events: list["RoomEvent"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )


class RoomPublic(RoomBase):
    """Public room response model for API."""

    room_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    last_activity: datetime


class RoomsPublic(SQLModel):
    """Paginated collection of rooms."""

    data: list[RoomPublic]
    count: int


# ============================================================================
# RoomParticipant Models (Projection)
# ============================================================================


class RoomParticipantBase(SQLModel):
    """Shared properties for RoomParticipant projection."""

    participant_id: str = Field(
        max_length=255,
        description="UUID string for users, agent name for agents",
    )
    participant_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )
    role: str = Field(
        max_length=20,
        default="member",
        description="Either 'owner' or 'member'",
    )


class RoomParticipantCreate(RoomParticipantBase):
    """Properties required when adding a participant via API."""

    room_id: uuid.UUID


class RoomParticipantUpdate(SQLModel):
    """Properties that can be updated via API."""

    role: str | None = Field(default=None, max_length=20)
    active: bool | None = None


class RoomParticipant(RoomParticipantBase, table=True):
    """
    RoomParticipant projection table (derived from RoomEvent log).

    Tracks both user and agent participants in rooms with their roles
    and active status. Updated transactionally with participant.joined,
    participant.left, and participant.role_changed events.
    """

    __tablename__ = "room_participants"
    __table_args__ = (
        # Unique constraint: one participant entry per room
        {"sqlite_autoincrement": True},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(foreign_key="rooms.room_id", nullable=False, index=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    left_at: datetime | None = Field(default=None)
    active: bool = Field(default=True, nullable=False)

    # Relationships
    room: Room = Relationship(back_populates="participants")


class RoomParticipantPublic(RoomParticipantBase):
    """Public participant response model for API."""

    id: uuid.UUID
    room_id: uuid.UUID
    joined_at: datetime
    left_at: datetime | None
    active: bool


class RoomParticipantsPublic(SQLModel):
    """Paginated collection of room participants."""

    data: list[RoomParticipantPublic]
    count: int


# ============================================================================
# Message Models (Projection)
# ============================================================================


class MessageBase(SQLModel):
    """Shared properties for Message projection."""

    content: str = Field(description="Message text content")
    sender_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )


class MessageCreate(MessageBase):
    """Properties required when creating a message via API."""

    room_id: uuid.UUID
    # sender_id and agent_name will be injected based on sender_type


class MessageUpdate(SQLModel):
    """
    Messages are immutable once created.

    To "edit" a message, emit a new message.edited event.
    Update model exists for consistency but should not be used.
    """

    pass


class Message(MessageBase, table=True):
    """
    Message projection table (derived from RoomEvent log).

    Stores conversation messages for efficient querying. Updated transactionally
    with message.user and message.agent events.
    """

    __tablename__ = "messages"

    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id",
        nullable=False,
        index=True,
    )
    sender_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description="User ID if sender_type='user'",
    )
    agent_name: str | None = Field(
        default=None,
        max_length=255,
        description="Agent name if sender_type='agent'",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    room: Room = Relationship(back_populates="messages")


class MessagePublic(MessageBase):
    """Public message response model for API."""

    message_id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID | None
    agent_name: str | None
    created_at: datetime


class MessagesPublic(SQLModel):
    """Paginated collection of messages."""

    data: list[MessagePublic]
    count: int


# ============================================================================
# RoomEvent Models (System of Record - Append-Only)
# ============================================================================


class RoomEventBase(SQLModel):
    """Shared properties for RoomEvent."""

    event_type: str = Field(
        max_length=50,
        description="Event type (e.g., room.created, message.user, participant.joined)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data as JSON",
        sa_type=None,  # Will be JSONB in PostgreSQL
    )


class RoomEventCreate(RoomEventBase):
    """Properties required when creating an event."""

    room_id: uuid.UUID
    # room_sequence will be auto-generated


class RoomEvent(RoomEventBase, table=True):
    """
    RoomEvent: Immutable append-only event log (system of record).

    This is the source of truth for all room state changes. Projections
    (Room, RoomParticipant, Message) are derived from this log.

    CRITICAL INVARIANTS:
    - Events are NEVER updated or deleted (append-only)
    - room_sequence is monotonically increasing per room
    - (room_id, room_sequence) is unique
    - All projections can be rebuilt by replaying events in sequence order

    Event Types (Phase 1 minimum):
    - room.created: New room created
    - room.updated: Room metadata updated
    - participant.joined: User or agent joined room
    - participant.left: User or agent left room (soft delete)
    - participant.role_changed: Participant role updated
    - message.user: User sent message
    - message.agent: Agent sent message
    """

    __tablename__ = "room_events"
    __table_args__ = (
        # Unique constraint on (room_id, room_sequence) for ordering
        {"sqlite_autoincrement": True},
    )

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id",
        nullable=False,
        index=True,
    )
    room_sequence: int = Field(
        nullable=False,
        description="Monotonically increasing sequence number per room",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )

    # Relationships
    room: Room = Relationship(back_populates="events")


class RoomEventPublic(RoomEventBase):
    """Public event response model for API (for debugging/replay)."""

    event_id: uuid.UUID
    room_id: uuid.UUID
    room_sequence: int
    created_at: datetime


class RoomEventsPublic(SQLModel):
    """Paginated collection of room events."""

    data: list[RoomEventPublic]
    count: int


# ============================================================================
# Post-Definition Relationship Binding
# ============================================================================
#
# Per data-model-best-practices.md, complex circular relationships should be
# defined after all classes exist. However, in this case, all relationships
# are already defined inline using string-based forward references, which is
# sufficient for SQLModel to resolve them correctly.
#
# If additional complex relationships are needed in future phases, add them here.
