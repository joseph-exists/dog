# Option 2: Session State Tracking - Detailed Analysis

## How It Works

Session state tracking uses SQLAlchemy's `session.in_transaction()` method to check whether the session already has an active transaction before attempting to start a new one.

### Implementation Pattern

```python
async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting events.

    Works in both transactional and non-transactional contexts.
    """
    room_id = uuid4()

    # Check if we're already in a transaction
    if session.in_transaction():
        # Already in transaction - just execute operations
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
    else:
        # No active transaction - create one
        async with session.begin():
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
```

### Alternative: Helper Wrapper Pattern

```python
async def with_transaction_if_needed(
    session: AsyncSession,
    operation: Callable,
) -> Any:
    """
    Execute operation within a transaction if one doesn't already exist.
    """
    if session.in_transaction():
        return await operation()
    else:
        async with session.begin():
            return await operation()


async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """Create a new room with automatic transaction management."""

    async def _create():
        room_id = uuid4()
        await emit_event(session, room_id, "room.created", {...})
        await emit_event(session, room_id, "participant.joined", {...})
        result = await session.execute(select(Room).where(Room.room_id == room_id))
        return result.scalar_one()

    return await with_transaction_if_needed(session, _create)
```

## Pros

### 1. **Flexibility in Usage**
Can be called from both transactional and non-transactional contexts:

```python
# Scenario A: Called from route (no transaction)
async def create_new_room(session: AsyncSessionDep, ...):
    room = await create_room(session=session, ...)  # Creates transaction
    return room

# Scenario B: Called from another CRUD function (already in transaction)
async def create_room_with_agents(session: AsyncSession, ...):
    async with session.begin():
        room = await create_room(session=session, ...)  # Reuses transaction
        await add_participant(session=session, ...)      # Reuses transaction
    return room
```

### 2. **Backward Compatibility**
Doesn't break existing code that might be using sessions with or without transactions.

### 3. **Incremental Migration**
Can be implemented function-by-function without requiring coordinated changes across multiple files.

## Cons (Detailed Analysis)

### Con 1: **Code Duplication and Boilerplate**

Every CRUD function must duplicate the transaction-checking logic:

```python
# EVERY function needs this pattern repeated:

async def function_1(..., session: AsyncSession):
    if session.in_transaction():
        # Do work
        await operation_a()
        await operation_b()
    else:
        async with session.begin():
            # DUPLICATE: Same work
            await operation_a()
            await operation_b()

async def function_2(..., session: AsyncSession):
    if session.in_transaction():
        # Do work
        await operation_c()
        await operation_d()
    else:
        async with session.begin():
            # DUPLICATE: Same work
            await operation_c()
            await operation_d()

# Repeated for ALL 6 room CRUD functions + any future functions
```

**Impact**:
- 6 functions × 2 code paths = 12 code blocks to maintain
- Every new CRUD function needs this boilerplate
- Easy to forget in one branch, leading to subtle bugs

**Example Bug**:
```python
async def update_room_metadata(..., session: AsyncSession):
    if session.in_transaction():
        # Validation logic
        if not title:
            raise ValueError("Title required")

        await emit_event(...)
    else:
        async with session.begin():
            # BUG: Forgot to duplicate validation!
            await emit_event(...)
```

### Con 2: **Unclear Transaction Ownership**

It becomes ambiguous WHO is responsible for committing/rolling back:

```python
# Scenario: Nested calls with mixed transaction management

async def complex_room_setup(session: AsyncSession):
    """Who commits this transaction?"""

    # Does THIS function own the transaction?
    if not session.in_transaction():
        async with session.begin():
            room = await create_room(session=session, ...)
            await add_participant(session=session, ...)
            # Commits here
    else:
        # Or does the CALLER own it?
        room = await create_room(session=session, ...)
        await add_participant(session=session, ...)
        # Caller must commit
```

**Problem**: In a deep call stack, it's unclear at what level the transaction is managed:

```
Route Handler (maybe starts transaction?)
  ↓
Service Layer Function (maybe starts transaction?)
  ↓
CRUD Function A (maybe starts transaction?)
  ↓
CRUD Function B (maybe starts transaction?)
  ↓
emit_event (expects transaction to exist)
```

Each function asks "Am I responsible for the transaction?" This mental overhead makes code harder to reason about.

### Con 3: **Testing Complexity**

Every function now has TWO code paths that must be tested:

```python
# Test file must cover BOTH paths:

async def test_create_room_without_transaction():
    """Test when session has NO active transaction."""
    session = AsyncSession(...)
    # Session starts with no transaction
    room = await create_room(session=session, ...)
    # Verify transaction was created and committed
    assert room.room_id is not None


async def test_create_room_with_transaction():
    """Test when session ALREADY has active transaction."""
    session = AsyncSession(...)
    async with session.begin():
        # Session now has active transaction
        room = await create_room(session=session, ...)
        # Verify no nested transaction was created
        assert room.room_id is not None
```

**Impact**:
- 6 functions × 2 test cases each = 12 additional test cases minimum
- Integration tests must verify transaction behavior in nested scenarios
- Harder to reproduce production transaction states in tests

### Con 4: **Hidden Transaction Boundaries**

Transaction boundaries are scattered throughout the codebase rather than centralized:

```python
# Where do transactions start/end? Hard to tell without reading all code:

# File 1: app/api/routes/rooms.py
async def create_new_room(session: AsyncSessionDep, ...):
    room = await create_room(...)  # Maybe starts transaction?
    return room

# File 2: app/crud.py
async def create_room(session: AsyncSession, ...):
    if session.in_transaction():  # Maybe in transaction already?
        ...
    else:
        async with session.begin():  # Or starts one here?
            ...

# File 3: app/services/event_emitter.py
async def emit_event(session: AsyncSession, ...):
    # Assumes transaction exists, but who started it?
    session.add(event)
```

**Problem**: When debugging transaction issues, you must trace through multiple files to understand the transaction lifecycle.

### Con 5: **Incomplete Rollback Control**

Error handling becomes ambiguous:

```python
async def create_room_with_agents(session: AsyncSession, ...):
    if session.in_transaction():
        # In existing transaction
        room = await create_room(session=session, ...)
        await add_participant(session=session, ...)
        # If error occurs here, WHO rolls back?
        # We don't control the transaction, so we can't rollback
        # Must rely on caller to handle it
    else:
        # We control transaction
        async with session.begin():
            room = await create_room(session=session, ...)
            await add_participant(session=session, ...)
            # If error occurs, our context manager rolls back
            # But what if we want to handle it differently?
```

**Scenario where this fails**:
```python
async def batch_create_rooms(session: AsyncSession, room_configs: list):
    """Create multiple rooms, continuing on individual failures."""
    results = []

    for config in room_configs:
        try:
            # Problem: If session already has transaction,
            # we can't rollback just THIS room creation
            room = await create_room(session=session, **config)
            results.append(room)
        except Exception as e:
            # Can't rollback just this one operation
            # Either rolls back ALL or NONE
            results.append({"error": str(e)})

    return results
```

### Con 6: **Performance Overhead**

Every function call incurs the cost of checking transaction state:

```python
async def create_room(...):
    if session.in_transaction():  # DB/state check
        ...
    else:
        ...

async def add_participant(...):
    if session.in_transaction():  # DB/state check
        ...
    else:
        ...

async def send_user_message(...):
    if session.in_transaction():  # DB/state check
        ...
    else:
        ...
```

While `in_transaction()` is typically a cheap operation, in high-throughput scenarios with deep call stacks, these checks add up.

### Con 7: **Subtle SQLAlchemy Behavior**

`session.in_transaction()` has nuances that can cause unexpected behavior:

```python
async with async_session_maker() as session:
    # In SQLAlchemy 1.4+, sessions have an implicit "autobegin" transaction
    print(session.in_transaction())  # Might be True even without begin()!

    # This is because SQLAlchemy auto-begins on first operation
    await session.execute(select(User).limit(1))
    print(session.in_transaction())  # Now definitely True
```

**Problem**: The "transaction state" might not match your expectations:
```python
async def my_crud_function(session: AsyncSession):
    # Expects to start transaction
    if session.in_transaction():  # FALSE (as expected)
        ...
    else:
        async with session.begin():  # Starts explicit transaction
            await some_query()  # First DB operation
            await another_operation()

            # Later in code...
            await nested_crud_function(session)  # Passes session

async def nested_crud_function(session: AsyncSession):
    # Might expect no transaction, but there IS one from caller
    if session.in_transaction():  # TRUE (from parent)
        # Takes this path even though parent didn't explicitly begin()
        ...
```

### Con 8: **Maintenance Burden**

As the codebase grows, every developer must remember the pattern:

```python
# Developer adds new function, forgets pattern:
async def delete_room(session: AsyncSession, room_id: UUID):
    """New function - developer forgets to check transaction state!"""

    # BUG: Always creates new transaction, even if one exists
    async with session.begin():
        await emit_event(...)
        result = await session.execute(...)
        # Crashes if called from within another transaction


# Correct version (easy to forget):
async def delete_room(session: AsyncSession, room_id: UUID):
    """Correct version with state checking."""

    if session.in_transaction():
        await emit_event(...)
        result = await session.execute(...)
    else:
        async with session.begin():
            await emit_event(...)
            result = await session.execute(...)
```

## Comparison: Option 1 vs Option 2

| Aspect | Option 1 (Route-Level) | Option 2 (State Tracking) |
|--------|------------------------|---------------------------|
| Code clarity | ✅ Clear: Routes own transactions | ❌ Unclear: Multiple owners |
| Code duplication | ✅ None | ❌ High (2× code per function) |
| Testing complexity | ✅ Single path per function | ❌ Two paths per function |
| Transaction boundaries | ✅ Explicit at route level | ❌ Implicit in CRUD functions |
| Rollback control | ✅ Clear: Route level only | ❌ Ambiguous: Depends on caller |
| Performance | ✅ No overhead | ⚠️ State check per function |
| Maintainability | ✅ Pattern enforced by types | ❌ Manual pattern enforcement |
| Bug surface area | ✅ Small: One transaction point | ❌ Large: Every CRUD function |

## Real-World Example: Where Option 2 Fails

```python
# Complex scenario: Batch room creation with partial failure handling

async def create_rooms_for_story(
    session: AsyncSession,
    story_id: UUID,
    room_configs: list[dict],
) -> list[Room]:
    """
    Create multiple rooms for a story.

    Requirement: If ONE room fails, roll back ALL room creations.
    """

    # With Option 1 (Route-Level Transaction):
    # -----------------------------------------
    # Route handler starts transaction
    # All operations succeed or fail together
    # Clear rollback semantics

    rooms = []
    for config in room_configs:
        room = await create_room(
            session=session,
            creator_id=config["creator_id"],
            story_id=story_id,
            title=config["title"],
        )
        rooms.append(room)
    # If ANY room fails, route-level transaction rolls back ALL
    return rooms


    # With Option 2 (State Tracking):
    # --------------------------------
    # Unclear: Does THIS function own the transaction?

    if session.in_transaction():
        # In existing transaction - can't control rollback
        rooms = []
        for config in room_configs:
            room = await create_room(session=session, ...)
            rooms.append(room)
        # If error occurs, we don't control rollback
        # Caller's transaction might rollback MORE than we want
        return rooms
    else:
        # We own transaction - can control rollback
        async with session.begin():
            rooms = []
            for config in room_configs:
                room = await create_room(session=session, ...)
                rooms.append(room)
            # If error occurs, our transaction rolls back
            # But what if caller ALSO wants to control rollback?
            return rooms
```

## Recommendation

**Avoid Option 2** because:

1. **Code Duplication**: Every function has duplicate logic in if/else branches
2. **Unclear Ownership**: Transaction boundaries are scattered and implicit
3. **Testing Burden**: Every function needs 2× test coverage
4. **Maintenance Risk**: Easy to forget pattern in new functions
5. **Debugging Difficulty**: Transaction lifecycle is hard to trace
6. **Limited Flexibility**: Can't handle complex rollback scenarios

**Use Option 1** for:
- ✅ Clear, explicit transaction boundaries at route level
- ✅ Single code path per function (easier to test)
- ✅ TypeScript-style dependency injection enforces pattern
- ✅ Standard transaction-per-request pattern
- ✅ Better separation of concerns (routes manage transactions, CRUD performs operations)
