# Transaction Ownership in Rooms Messaging

## 




### Current Rooms Call Flow

#TODO : create diagram


## Implemented Route-Level Transaction Management

###  Route-Level Transaction Management 

Transaction control is at the **route level** using middleware or explicit transaction blocks in each route handler. CRUD functions become transaction-agnostic.
# TODO: define whether the approach we took below qualifies as middleware? the asyncsessiontransactiondep?

#### Implementation

**Phase 1: Update `app/api/deps.py`**

Add a new dependency that provides a session with an active transaction:

```python
# app/api/deps.py

async def get_async_session_with_transaction() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session generator with automatic transaction management.

    Commits on successful completion, rolls back on exceptions.
    Use for all write operations.
    """
    async with async_session_maker() as session:
        async with session.begin():
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

AsyncSessionTransactionDep = Annotated[AsyncSession, Depends(get_async_session_with_transaction)]
```

**Phase 2: Update CRUD Functions in `app/crud.py`**

CRUD Function Example:

```python
# BEFORE (~Line 816-880):
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

    This operation creates a room with the creator as the owner participant.
    All state changes are recorded as events and projections are updated
    transactionally.

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
                title="Chapter 1 Discussion",
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

same pattern in in these functions:
- `update_room_metadata()` (line 1019)
- `add_participant()` (line 1090)
- `remove_participant()` (line 1156)
- `change_participant_role()` (line 1220)
- `send_user_message()` (line 1333)

**Phase 3: Update Route Handlers in `app/api/routes/rooms.py`**

Change dependency from `AsyncSessionDep` to `AsyncSessionTransactionDep`:

```python

# AFTER:
@router.post("/", response_model=RoomPublic)
async def create_new_room(
    *,
    session: AsyncSessionTransactionDep,  # ✅ Transaction auto-managed
    current_user: CurrentUser,
    room_in: RoomCreate,
) -> Any:
    """
    Create a new room.

    Transaction is automatically managed by dependency injection:
    - Commits on success
    - Rolls back on exception

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
```

**For all write endpoints** use AsyncSessionTransactionDep: (POST, PATCH, DELETE) in `app/api/routes/rooms.py`:
- `create_new_room()` (line 65)
- `update_room()` (line 131)
- `add_room_participant()` (line 158)
- `remove_room_participant()` (line 231)
- `change_room_participant_role()` (line 257)
- `send_message()` (line 290)

**For read-only endpoints** use`AsyncSessionDep` (no transaction needed):
- `list_user_rooms()` (line 91)
- `get_room()` (line 112)
- `list_room_participants()` (line 193)
- `list_messages()` (line 315)


## Implementation Status: Pending Test Coverage and Performance Review

### Step 1 [COMPLETE]: Created New Dependency (Non-Breaking)
Add `AsyncSessionTransactionDep` to `deps.py` without removing `AsyncSessionDep`

### Step 2 [COMPLETE]: Updated CRUD Functions (Non-Breaking)
Remove `async with session.begin():` blocks from all room CRUD functions

### Step 3: [COMPLETE] Updated Routes (Breaking Change)
Change write endpoints to use `AsyncSessionTransactionDep`

### Step 4: Test Thoroughly
- Unit tests for each CRUD function
- Integration tests for each route
- Test nested event emission scenarios
- Test error rollback behavior

### Step 5: Update Documentation
Update function docstrings to clarify transaction expectations

## Files to Review

### Must Change
1. `app/core/db.py` - Added transaction-managed session generator 
2. `app/api/deps.py` - Added `AsyncSessionTransactionDep` dependency
3. `app/crud.py` - Removed `session.begin()` from 6 functions (lines 852, 1019, 1090, 1156, 1220, 1333)
4. `app/api/routes/rooms.py` - Updated 6 write endpoints to use `AsyncSessionTransactionDep`

### Review for Consistency
5. `app/services/event_emitter.py` - Update documentation to clarify transaction expectations

## Testing Checklist

- [ ] Create room - verify transaction commits on success
- [ ] Create room - verify transaction rolls back on error
- [ ] Send message - verify nested event emission works
- [ ] Update room metadata - verify projection updates are transactional
- [ ] Add participant - verify idempotent re-join works
- [ ] Remove participant - verify soft delete commits
- [ ] Change participant role - verify role update commits
- [ ] Concurrent room creation - verify no deadlocks
- [ ] Concurrent message sending - verify sequence ordering
