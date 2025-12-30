# Route-Level Transaction Management - Implementation Plan

## Overview

This plan implements **Route-Level Transaction Management** for the rooms module, establishing a clear pattern where FastAPI route handlers own transaction lifecycle, and CRUD functions operate within those transactions.

## Architecture Pattern

### Transaction Ownership Model

```
┌─────────────────────────────────────────┐
│ FastAPI Route Handler                   │
│ ┌─────────────────────────────────────┐ │
│ │ [TRANSACTION STARTS]                │ │
│ │                                     │ │
│ │ ┌─────────────────────────────────┐ │ │
│ │ │ CRUD Function                   │ │ │
│ │ │ - No transaction management     │ │ │
│ │ │ - Operates on provided session  │ │ │
│ │ │ ┌─────────────────────────────┐ │ │ │
│ │ │ │ emit_event()                │ │ │ │
│ │ │ │ - Uses session transaction  │ │ │ │
│ │ │ │ ┌─────────────────────────┐ │ │ │ │
│ │ │ │ │ _update_projections()   │ │ │ │ │
│ │ │ │ │ - Uses same transaction │ │ │ │ │
│ │ │ │ └─────────────────────────┘ │ │ │ │
│ │ │ └─────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────┘ │ │
│ │                                     │ │
│ │ [TRANSACTION COMMITS on success]    │ │
│ │ [TRANSACTION ROLLBACKS on error]    │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Key Principles

1. **Single Transaction Per Request**: Each write operation request has exactly one transaction
2. **Route-Level Ownership**: Route handlers control transaction start, commit, and rollback
3. **CRUD Transparency**: CRUD functions are transaction-agnostic, operating on provided sessions
4. **Automatic Cleanup**: Transactions commit on success, rollback on exceptions via dependency injection
5. **Future-Proof**: Supports Phase 2 agent integration and Phase 4 Redis pub/sub without refactoring

## Implementation Steps

### Phase 1: Add Transaction-Managed Session Dependency

**File**: `app/api/deps.py`

**Location**: Add after line 28 (after `AsyncSessionDep` definition)

**Code to Add**:

```python
async def get_async_session_with_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session generator with automatic transaction management.

    Provides a session with an active transaction that:
    - Commits automatically on successful completion
    - Rolls back automatically on exceptions
    - Ensures atomic operations across CRUD functions

    Use this dependency for all write operations (POST, PATCH, DELETE).
    For read-only operations (GET), use AsyncSessionDep instead.

    Example:
        @router.post("/rooms/")
        async def create_room(
            session: AsyncSessionTransactionDep,
            current_user: CurrentUser,
            room_in: RoomCreate,
        ):
            # Transaction active throughout handler
            room = await create_room(session=session, ...)
            # Transaction commits here (on successful return)
            # or rolls back (on exception)
            return room
    """
    async with async_session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                # Transaction automatically rolls back via context manager
                # Re-raise exception for FastAPI error handling
                raise


AsyncSessionTransactionDep = Annotated[
    AsyncSession,
    Depends(get_async_session_with_transaction)
]
```

**Import Required**: Ensure `async_session_maker` is imported:

```python
# Add to imports at top of file
from app.core.db import engine, get_async_session, async_session_maker
```

### Phase 2: Update CRUD Functions

**File**: `app/crud.py`

Remove `async with session.begin():` blocks from all room CRUD functions. These functions should operate within the transaction provided by the route handler.

#### 2.1: Update `create_room()` (Lines 816-880)

**Current Code** (Lines 816-880):
```python
async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting room.created and participant.joined events.
    ...
    """
    room_id = uuid4()

    async with session.begin():  # ← REMOVE THIS LINE
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
        )  # ← REMOVE INDENT FROM ALL ABOVE

    # Fetch and return the created room projection
    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one()
    return room
```

**Updated Code**:
```python
async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting room.created and participant.joined events.

    NOTE: This function expects to be called within an active transaction.
    Use AsyncSessionTransactionDep in route handlers to ensure proper
    transaction management.

    Args:
        creator_id: UUID of the user creating the room
        story_id: Optional UUID of associated story
        title: Optional room title
        session: Async database session with active transaction

    Returns:
        The created Room projection

    Example:
        # In route handler:
        async def create_new_room(session: AsyncSessionTransactionDep, ...):
            room = await create_room(
                creator_id=user.id,
                story_id=story.id,
                title="My Room",
                session=session,  # Transaction managed by route
            )
            return room
    """
    room_id = uuid4()

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
```

#### 2.2: Update `update_room_metadata()` (Lines 976-1030)

**Remove Lines**: 1019 (`async with session.begin():`) and corresponding indent

**Update Docstring**: Add note about transaction expectation

```python
async def update_room_metadata(
    *,
    room_id: UUID,
    user_id: UUID,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Update room metadata via event emission (room.updated).

    NOTE: This function expects to be called within an active transaction.

    Policy: Owner-only operation (enforced in Phase 1).
    Future phases may allow members to update certain fields.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user (must be owner)
        title: New title for the room
        session: Async database session with active transaction

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

    # Emit room.updated event (remove async with session.begin():)
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
```

#### 2.3: Update `add_participant()` (Lines 1038-1110)

**Remove Lines**: 1090 (`async with session.begin():`) and corresponding indent

**Update Docstring**: Add transaction expectation note

```python
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

    NOTE: This function expects to be called within an active transaction.

    This operation is idempotent: re-adding an inactive participant
    will reactivate them via the participant.joined event handler.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        participant_type: "user" or "agent"
        role: "owner" or "member"
        session: Async database session with active transaction

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
    # Remove async with session.begin():
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
```

#### 2.4: Update `remove_participant()` (Lines 1113-1162)

**Remove Lines**: 1156 (`async with session.begin():`) and corresponding indent

**Update Docstring**: Add transaction expectation note

```python
async def remove_participant(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    session: AsyncSession,
) -> None:
    """
    Remove a participant from a room (owner-only, soft delete).

    NOTE: This function expects to be called within an active transaction.

    Emits participant.left event which sets active=False in the projection.
    Historical events are preserved (never deleted).

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        session: Async database session with active transaction

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

    # Emit participant.left event (remove async with session.begin():)
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.left",
        payload={"participant_id": participant_id},
    )
```

#### 2.5: Update `change_participant_role()` (Lines 1165-1239)

**Remove Lines**: 1220 (`async with session.begin():`) and corresponding indent

**Update Docstring**: Add transaction expectation note

```python
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

    NOTE: This function expects to be called within an active transaction.

    Emits participant.role_changed event to update the projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        new_role: "owner" or "member"
        session: Async database session with active transaction

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

    # Emit participant.role_changed event (remove async with session.begin():)
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
```

#### 2.6: Update `send_user_message()` (Lines 1304-1355)

**Remove Lines**: 1333 (`async with session.begin():`) and corresponding indent

**Update Docstring**: Add transaction expectation note

```python
async def send_user_message(
    *,
    room_id: UUID,
    user_id: UUID,
    content: str,
    session: AsyncSession,
) -> RoomMessage:
    """
    Send a user message to a room.

    NOTE: This function expects to be called within an active transaction.

    Emits room_message.user event which creates the message projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user sending the message
        content: Message content
        session: Async database session with active transaction

    Returns:
        Created RoomMessage projection

    Raises:
        HTTPException: 403 if user is not an active participant
    """
    # Check membership
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Emit message.user event (remove async with session.begin():)
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room_message.user",
        payload={
            "sender_id": str(user_id),
            "content": content,
        },
    )

    # Fetch the most recent message for this user
    result = await session.execute(
        select(RoomMessage)
        .where(
            RoomMessage.room_id == room_id,
            RoomMessage.sender_id == user_id,
        )
        .order_by(RoomMessage.created_at.desc())
        .limit(1)
    )
    room_message = result.scalar_one()
    return room_message
```

### Phase 3: Update Route Handlers

**File**: `app/api/routes/rooms.py`

Update write endpoints to use `AsyncSessionTransactionDep` instead of `AsyncSessionDep`.

#### 3.1: Add Import

**Location**: Add to imports at top of file (after line 23)

```python
from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
```

#### 3.2: Update `create_new_room()` (Line 65)

**Change**:
```python
# Before:
async def create_new_room(
    *,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
    room_in: RoomCreate,
) -> Any:

# After:
async def create_new_room(
    *,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
    room_in: RoomCreate,
) -> Any:
    """
    Create a new room.

    The current user becomes the room owner. Optionally associate with a story.

    Transaction is automatically managed:
    - Commits on successful completion
    - Rolls back on any exception

    Event flow:
    1. Emits room.created event
    2. Emits participant.joined event for creator (as owner)
    3. Returns room projection
    """
```

#### 3.3: Update `update_room()` (Line 131)

**Change**:
```python
# Before:
async def update_room(
    *,
    room_id: UUID,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
    room_in: RoomUpdate,
) -> Any:

# After:
async def update_room(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
    room_in: RoomUpdate,
) -> Any:
    """
    Update room metadata (owner-only).

    Transaction automatically managed. Emits room.updated event with changed fields.
    """
```

#### 3.4: Update `add_room_participant()` (Line 158)

**Change**:
```python
# Before:
async def add_room_participant(
    *,
    room_id: UUID,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
    participant_in: ParticipantAddRequest,
) -> Any:

# After:
async def add_room_participant(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
    participant_in: ParticipantAddRequest,
) -> Any:
    """
    Add a participant to a room (owner-only).

    Transaction automatically managed. Supports adding both users and agents.
    Operation is idempotent: re-adding an inactive participant will reactivate them.

    Event flow:
    1. Verifies current user is room owner
    2. Emits participant.joined event
    3. Returns participant projection
    """
```

#### 3.5: Update `remove_room_participant()` (Line 231)

**Change**:
```python
# Before:
async def remove_room_participant(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
) -> MessageResponse:

# After:
async def remove_room_participant(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
) -> MessageResponse:
    """
    Remove a participant from a room (owner-only, soft delete).

    Transaction automatically managed. Emits participant.left event which sets active=False.
    Historical events are preserved.
    """
```

#### 3.6: Update `change_room_participant_role()` (Line 257)

**Change**:
```python
# Before:
async def change_room_participant_role(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
    role_in: ParticipantRoleChangeRequest,
) -> Any:

# After:
async def change_room_participant_role(
    *,
    room_id: UUID,
    participant_id: str,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
    role_in: ParticipantRoleChangeRequest,
) -> Any:
    """
    Change a participant's role (owner-only).

    Transaction automatically managed. Emits participant.role_changed event.
    """
```

#### 3.7: Update `send_message()` (Line 290)

**Change**:
```python
# Before:
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionDep,  # ← Change this
    current_user: CurrentUser,
    message_in: RoomMessageSend,
) -> Any:

# After:
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,  # ← Use transaction-managed session
    current_user: CurrentUser,
    message_in: RoomMessageSend,
) -> Any:
    """
    Send a message to a room.

    Transaction automatically managed. Emits message.user event.
    In Phase 2, this will also trigger agent execution if agents are configured to respond.

    Only accessible to active participants.
    """
```

#### 3.8: Keep Read Endpoints Using `AsyncSessionDep`

The following read-only endpoints should continue using `AsyncSessionDep` (no transaction needed):

- `list_user_rooms()` (line 91)
- `get_room()` (line 112)
- `list_room_participants()` (line 193)
- `list_messages()` (line 315)

### Phase 4: Update Event Emitter Documentation

**File**: `app/services/event_emitter.py`

**Location**: Update docstring for `emit_event()` function (lines 48-96)

**Change**:
```python
async def emit_event(
    session: AsyncSession,
    room_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
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
    """
```

## Testing Strategy

### Unit Tests

Create tests for each CRUD function to verify behavior within transactions.

**File**: `app/tests/test_rooms_crud.py` (create new file)

```python
import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import (
    create_room,
    update_room_metadata,
    add_participant,
    remove_participant,
    change_participant_role,
    send_user_message,
)
from app.models import Room, RoomParticipant, RoomMessage


@pytest.mark.asyncio
async def test_create_room_in_transaction(async_session: AsyncSession):
    """Test create_room within an active transaction."""
    user_id = uuid4()

    async with async_session.begin():
        room = await create_room(
            creator_id=user_id,
            story_id=None,
            title="Test Room",
            session=async_session,
        )

    assert room.room_id is not None
    assert room.creator_id == user_id
    assert room.title == "Test Room"


@pytest.mark.asyncio
async def test_create_room_rollback_on_error(async_session: AsyncSession):
    """Test that transaction rolls back on error."""
    user_id = uuid4()

    with pytest.raises(Exception):
        async with async_session.begin():
            await create_room(
                creator_id=user_id,
                story_id=None,
                title="Test Room",
                session=async_session,
            )
            # Simulate error
            raise Exception("Simulated error")

    # Verify room was not created (rollback worked)
    result = await async_session.execute(
        select(Room).where(Room.creator_id == user_id)
    )
    rooms = result.scalars().all()
    assert len(rooms) == 0


@pytest.mark.asyncio
async def test_send_message_in_transaction(async_session: AsyncSession):
    """Test send_user_message within an active transaction."""
    # Setup: Create room first
    user_id = uuid4()
    async with async_session.begin():
        room = await create_room(
            creator_id=user_id,
            story_id=None,
            title="Test Room",
            session=async_session,
        )

    # Test: Send message
    async with async_session.begin():
        message = await send_user_message(
            room_id=room.room_id,
            user_id=user_id,
            content="Hello, world!",
            session=async_session,
        )

    assert message.content == "Hello, world!"
    assert message.sender_id == user_id


@pytest.mark.asyncio
async def test_multiple_operations_atomic(async_session: AsyncSession):
    """Test multiple operations in same transaction are atomic."""
    user_id = uuid4()
    agent_name = "test-agent"

    async with async_session.begin():
        # Create room
        room = await create_room(
            creator_id=user_id,
            story_id=None,
            title="Test Room",
            session=async_session,
        )

        # Add agent participant
        await add_participant(
            room_id=room.room_id,
            user_id=user_id,
            participant_id=agent_name,
            participant_type="agent",
            role="member",
            session=async_session,
        )

        # Send message
        await send_user_message(
            room_id=room.room_id,
            user_id=user_id,
            content="Hello!",
            session=async_session,
        )

    # Verify all operations committed
    result = await async_session.execute(
        select(RoomParticipant).where(RoomParticipant.room_id == room.room_id)
    )
    participants = result.scalars().all()
    assert len(participants) == 2  # Creator + agent
```

### Integration Tests

Test route handlers to verify transaction management works end-to-end.

**File**: `app/tests/test_rooms_routes.py` (update existing)

```python
@pytest.mark.asyncio
async def test_create_room_commits_transaction(client: AsyncClient, user_token_headers: dict):
    """Test that creating a room commits the transaction."""
    response = await client.post(
        "/api/v1/rooms/",
        headers=user_token_headers,
        json={"title": "Integration Test Room"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Integration Test Room"

    # Verify room persisted (transaction committed)
    room_id = data["room_id"]
    response = await client.get(
        f"/api/v1/rooms/{room_id}",
        headers=user_token_headers,
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_send_message_rollback_on_error(
    client: AsyncClient,
    user_token_headers: dict,
    monkeypatch,
):
    """Test that transaction rolls back on error."""
    # Create room first
    response = await client.post(
        "/api/v1/rooms/",
        headers=user_token_headers,
        json={"title": "Test Room"},
    )
    room_id = response.json()["room_id"]

    # Monkeypatch emit_event to raise error
    async def mock_emit_event_error(*args, **kwargs):
        raise Exception("Simulated error")

    monkeypatch.setattr("app.crud.emit_event", mock_emit_event_error)

    # Send message (should fail)
    response = await client.post(
        f"/api/v1/rooms/{room_id}/messages",
        headers=user_token_headers,
        json={"content": "This should fail"},
    )
    assert response.status_code == 500

    # Verify message was not created (rollback worked)
    response = await client.get(
        f"/api/v1/rooms/{room_id}/messages",
        headers=user_token_headers,
    )
    messages = response.json()["data"]
    assert len(messages) == 0
```

### Test Fixtures

**File**: `app/tests/conftest.py` (add to existing)

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


@pytest.fixture
async def async_session():
    """Provide async session for testing."""
    engine = create_async_engine(
        str(settings.SQLALCHEMY_DATABASE_URI).replace(
            "postgresql://", "postgresql+asyncpg://"
        ),
        echo=False,
    )

    async_session_maker = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()
```

## Verification Checklist

After implementing all changes, verify:

- [ ] `AsyncSessionTransactionDep` defined in `app/api/deps.py`
- [ ] All 6 CRUD functions updated (no `session.begin()` blocks):
  - [ ] `create_room()`
  - [ ] `update_room_metadata()`
  - [ ] `add_participant()`
  - [ ] `remove_participant()`
  - [ ] `change_participant_role()`
  - [ ] `send_user_message()`
- [ ] All 6 write endpoints updated to use `AsyncSessionTransactionDep`:
  - [ ] `POST /rooms/`
  - [ ] `PATCH /rooms/{room_id}`
  - [ ] `POST /rooms/{room_id}/participants`
  - [ ] `DELETE /rooms/{room_id}/participants/{participant_id}`
  - [ ] `PATCH /rooms/{room_id}/participants/{participant_id}/role`
  - [ ] `POST /rooms/{room_id}/messages`
- [ ] Read-only endpoints still use `AsyncSessionDep`
- [ ] `emit_event()` docstring updated
- [ ] Unit tests created and passing
- [ ] Integration tests updated and passing
- [ ] Manual testing completed:
  - [ ] Create room succeeds
  - [ ] Create room rolls back on error
  - [ ] Send message succeeds
  - [ ] Send message rolls back on error
  - [ ] Multiple operations in one request are atomic

## Rollback Plan

If issues are discovered after deployment:

1. **Immediate Rollback**: Revert all changes via git:
   ```bash
   git revert <commit-hash>
   git push origin main
   ```

2. **Partial Rollback**: If only specific endpoints are problematic:
   - Revert those endpoints to use `AsyncSessionDep`
   - Restore `session.begin()` in corresponding CRUD functions
   - Deploy hotfix

3. **Investigation**: If rollback is needed:
   - Capture logs and error traces
   - Identify specific failure scenario
   - Add regression test
   - Fix issue and re-deploy

## Benefits Summary

This implementation provides:

1. **Clear Transaction Boundaries**: Routes own transaction lifecycle
2. **Atomic Operations**: All operations in a request succeed or fail together
3. **Simple CRUD Functions**: No transaction management logic
4. **Better Testability**: Single code path per function
5. **Future-Proof**: Supports Phase 2 agents and Phase 4 Redis without refactoring
6. **Error Handling**: Automatic rollback on exceptions
7. **Maintainability**: Standard pattern enforced by type system

## Timeline Estimate

- **Phase 1** (deps.py): 30 minutes
- **Phase 2** (crud.py): 2 hours (6 functions)
- **Phase 3** (routes/rooms.py): 1 hour (6 endpoints)
- **Phase 4** (event_emitter.py): 15 minutes
- **Testing**: 3 hours (unit + integration)
- **Verification**: 1 hour
- **Documentation**: 30 minutes

**Total**: ~8 hours
