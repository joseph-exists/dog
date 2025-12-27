# Transaction Ownership Issue - Proposal for Inline Logic Fix

## Problem Statement

The current implementation has transaction ownership conflicts causing crashes due to nested `AsyncSession.begin()` calls within the same request lifecycle.

### Root Cause Analysis

1. **Session Lifecycle**: `get_async_session()` in `app/core/db.py` yields an `AsyncSession` **without** starting a transaction
2. **CRUD Transaction Management**: Room CRUD functions in `app/crud.py` start transactions with `async with session.begin():`
3. **Nested Transaction Conflict**: The following locations create nested transaction contexts:
   - `crud.py:852` - `create_room()`
   - `crud.py:1019` - `update_room_metadata()`
   - `crud.py:1090` - `add_participant()`
   - `crud.py:1156` - `remove_participant()`
   - `crud.py:1220` - `change_participant_role()`
   - `crud.py:1333` - `send_user_message()`

4. **The Failure Scenario**:
   ```python
   # Route handler receives session from dependency injection (no active transaction)
   session = AsyncSessionDep

   # CRUD function starts transaction
   async with session.begin():  # Transaction T1 starts
       await emit_event(session, ...)
           # emit_event calls projection handlers
           await _update_projections(session, event)
               # Handler queries or updates, expecting to be in T1
               # But if another CRUD function is called (nested), it tries:
               async with session.begin():  # FAILS: T1 already active!
   ```

### Current Problematic Flow

```
Route Handler (no transaction)
  ↓
CRUD Function (starts transaction with session.begin())
  ↓
emit_event (uses session, expects transaction context)
  ↓
_update_projections (uses session in same transaction)
  ↓
Projection Handlers (query/update using session)
  ↓
[POTENTIAL CRASH]: If any handler or nested call tries session.begin() again
```

## Proposed Solution

### Option 1: Route-Level Transaction Management (RECOMMENDED)

Move transaction control to the **route level** using middleware or explicit transaction blocks in each route handler. CRUD functions become transaction-agnostic.

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

Remove all `async with session.begin():` blocks from CRUD functions:

```python
# BEFORE (Line 816-880):
async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    room_id = uuid4()

    async with session.begin():  # ❌ REMOVE THIS
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


# AFTER:
async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting room.created and participant.joined events.

    NOTE: Expects session to have an active transaction (managed by route handler).
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

Apply the same pattern to these functions:
- `update_room_metadata()` (line 1019)
- `add_participant()` (line 1090)
- `remove_participant()` (line 1156)
- `change_participant_role()` (line 1220)
- `send_user_message()` (line 1333)

**Phase 3: Update Route Handlers in `app/api/routes/rooms.py`**

Change dependency from `AsyncSessionDep` to `AsyncSessionTransactionDep`:

```python
# BEFORE:
@router.post("/", response_model=RoomPublic)
async def create_new_room(
    *,
    session: AsyncSessionDep,  # ❌ No transaction management
    current_user: CurrentUser,
    room_in: RoomCreate,
) -> Any:
    room = await create_room(
        creator_id=current_user.id,
        story_id=room_in.story_id,
        title=room_in.title,
        session=session,
    )
    return room


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
    """
    room = await create_room(
        creator_id=current_user.id,
        story_id=room_in.story_id,
        title=room_in.title,
        session=session,
    )
    return room
```

Update all write endpoints (POST, PATCH, DELETE) in `app/api/routes/rooms.py`:
- `create_new_room()` (line 65)
- `update_room()` (line 131)
- `add_room_participant()` (line 158)
- `remove_room_participant()` (line 231)
- `change_room_participant_role()` (line 257)
- `send_message()` (line 290)

**For read-only endpoints**, continue using `AsyncSessionDep` (no transaction needed):
- `list_user_rooms()` (line 91)
- `get_room()` (line 112)
- `list_room_participants()` (line 193)
- `list_messages()` (line 315)

### Option 2: Session State Tracking (ALTERNATIVE)

Add a flag to track whether a transaction is already active and use conditional transaction management.

#### Implementation

```python
# app/crud.py

async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    room_id = uuid4()

    # Check if transaction is already active
    if session.in_transaction():
        # Already in transaction, don't create nested one
        await emit_event(...)
        await emit_event(...)
    else:
        # No active transaction, create one
        async with session.begin():
            await emit_event(...)
            await emit_event(...)

    result = await session.execute(select(Room).where(Room.room_id == room_id))
    room = result.scalar_one()
    return room
```

**Pros**: Flexible, works with both transactional and non-transactional contexts
**Cons**: More complex, requires checking transaction state in every function

### Option 3: Nested Savepoints (NOT RECOMMENDED)

Use `session.begin_nested()` for nested transaction support with savepoints.

**Why Not Recommended**:
- Adds complexity with savepoint management
- Can mask errors by creating implicit subtransactions
- Harder to reason about rollback behavior

## Migration Strategy

### Step 1: Create New Dependency (Non-Breaking)
Add `AsyncSessionTransactionDep` to `deps.py` without removing `AsyncSessionDep`

### Step 2: Update CRUD Functions (Non-Breaking)
Remove `async with session.begin():` blocks from all room CRUD functions

### Step 3: Update Routes (Breaking Change - Requires Testing)
Change write endpoints to use `AsyncSessionTransactionDep`

### Step 4: Test Thoroughly
- Unit tests for each CRUD function
- Integration tests for each route
- Test nested event emission scenarios
- Test error rollback behavior

### Step 5: Update Documentation
Update function docstrings to clarify transaction expectations

## Affected Files

### Must Change
1. `app/core/db.py` - Add transaction-managed session generator (if using Option 1 alternative approach)
2. `app/api/deps.py` - Add `AsyncSessionTransactionDep` dependency
3. `app/crud.py` - Remove `session.begin()` from 6 functions (lines 852, 1019, 1090, 1156, 1220, 1333)
4. `app/api/routes/rooms.py` - Update 6 write endpoints to use `AsyncSessionTransactionDep`

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

## Rollback Plan

If issues arise:
1. Keep `AsyncSessionDep` for all endpoints
2. Restore `async with session.begin():` in CRUD functions
3. Investigate specific nested call patterns causing conflicts
4. Consider refactoring to avoid nested CRUD calls entirely

## Recommendation

**Implement Option 1 (Route-Level Transaction Management)** because:
1. ✅ Clear separation of concerns (routes manage transactions, CRUD performs operations)
2. ✅ Follows FastAPI dependency injection patterns
3. ✅ Easier to test (explicit transaction boundaries)
4. ✅ Prevents nested transaction bugs by design
5. ✅ Matches industry standard patterns (transaction-per-request)

## Code Change Summary

### Files to Modify
| File | Lines to Change | Change Type |
|------|----------------|-------------|
| `app/api/deps.py` | Add new function | Addition |
| `app/crud.py` | 852, 1019, 1090, 1156, 1220, 1333 | Remove `async with session.begin():` blocks |
| `app/api/routes/rooms.py` | 67, 133, 160, 233, 259, 292 | Change `AsyncSessionDep` → `AsyncSessionTransactionDep` |

### Estimated Impact
- **6 CRUD functions** to update
- **6 route handlers** to update
- **1 new dependency** to add
- **0 breaking changes** to existing sync CRUD operations
- **High confidence** in fixing the transaction ownership issue
