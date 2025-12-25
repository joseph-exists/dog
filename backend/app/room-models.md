

### COPIED IN FROM MODELS.PY FOR ISOLATED REVIEW AND TESTING ###


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
    room_messages: list["RoomMessage"] = Relationship(
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

    pass


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


class ParticipantAddRequest(SQLModel):
    """
    Request model for adding a participant to a room.
    
    Used by: POST /rooms/{room_id}/participants
    """
    participant_id: str = Field(
        ...,
        max_length=255,
        description="UUID string for users, agent name for agents",
        # examples=["550e8400-e29b-41d4-a716-446655440000", "StoryAdvisor"],
    )
    participant_type: Literal["user", "agent"] = Field(
        ...,
        description="Type of participant (user or agent)",
    )
    role: Literal["owner", "member"] = Field(
        default="member",
        description="Participant role (default: member)",
    )


class ParticipantRoleChangeRequest(SQLModel):
    """
    Request model for changing a participant's role.
    
    Used by: PATCH /rooms/{room_id}/participants/{participant_id}/role
    """
    new_role: Literal["owner", "member"] = Field(
        ...,
        description="New role for the participant",
    )


class MessageResponse(SQLModel):
    """
    Generic success message response.
    
    Used for operations that need to return a simple success message.
    """
    message: str = Field(
        ...,
        description="Success message",
    )

# ============================================================================
# Message Models (Projection)
# ============================================================================


class RoomMessageBase(SQLModel):
    """Shared properties for Message projection."""

    content: str = Field(description="Message text content")
    sender_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )


class RoomMessageCreate(RoomMessageBase):
    """Properties required when creating a message via API."""

    pass
    # sender_id and agent_name will be injected based on sender_type

class RoomMessageSend(SQLModel):
    """Properties required when sending a message via API."""

    content: str = Field(description="Message text content")


class RoomMessageUpdate(SQLModel):
    """
    Messages are immutable once created.

    To "edit" a room_message, emit a new room_message.edited event.
    Update model exists for consistency but should not be used.
    """

    pass


class RoomMessage(RoomMessageBase, table=True):
    """
    Message projection table (derived from RoomEvent log).

    Stores conversation messages for efficient querying. Updated transactionally
    with room_message.user and room_message.agent events.
    """

    __tablename__ = "room_messages"

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
    room: Room = Relationship(back_populates="room_messages")


class RoomMessagePublic(RoomMessageBase):
    """Public message response model for API."""

    message_id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID | None
    agent_name: str | None
    created_at: datetime


class RoomMessagesPublic(SQLModel):
    """Paginated collection of messages."""

    data: list[RoomMessagePublic]
    count: int


# ============================================================================
# RoomEvent Models (System of Record - Append-Only)
# ============================================================================


class RoomEventBase(SQLModel):
    """Shared properties for RoomEvent."""

    event_type: str = Field(
        max_length=50,
        description="Event type (e.g., room.created, room_message.user, participant.joined)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data as JSON",
        sa_type=JSON,  # Will be JSONB in PostgreSQL
    )


class RoomEventCreate(RoomEventBase):
    """Properties required when creating an event."""

    room_id: uuid.UUID
    # room_sequence will be auto-generated


class RoomEvent(RoomEventBase, table=True):
    """
    RoomEvent: Immutable append-only event log (system of record).

    This is the source of truth for all room state changes. Projections
    (Room, RoomParticipant, RoomMessage) are derived from this log.

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
    - room_message.user: User sent message
    - room_message.agent: Agent sent message
    """

    __tablename__ = "room_events"
    __table_args__ = (
        # Unique constraint on (room_id, room_sequence) for ordering
        # TODO - why is this sqlite instead of postgres?
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
# defined after all classes exist. However, for Rooms and RoomMessages, all relationships
# are already defined inline using string-based forward references, which is
# sufficient for SQLModel to resolve them correctly.
#
# If additional complex relationships are needed in future phases, add them here.

