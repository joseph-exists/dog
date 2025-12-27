# Transaction Strategy in Async Context - Updated Analysis

## Critical Context from async-strategy-for-emitter.md

The async strategy document establishes these **non-negotiable** requirements:

1. **Async-first I/O is mandatory** (architectural mandate)
2. **Phase 4: Redis pub/sub requires async** (must publish events in real-time)
3. **Phase 2: Agent execution is async** (LLM I/O)
4. **Multi-worker responsiveness** (non-blocking I/O essential)

## How This Changes the Transaction Management Decision

### Phase 4 Requirement: Redis Pub/Sub Integration

The async-strategy document shows this future requirement:

```python
async def emit_event(...):
    async with session.begin():
        # Write to database
        event = await write_to_db(...)

        # Publish to Redis (Phase 4)
        await redis_client.publish(f"room:{room_id}", event)  # ✅ Must be in SAME transaction
```

**Critical insight**: The Redis publish MUST happen within the same transaction as the database write to ensure:
- Events are only published if database write succeeds
- Rollback prevents orphaned Redis events
- Atomicity across database + Redis operations

### Option 1 (Route-Level) with Redis: ✅ WORKS

```python
# Route handler
@router.post("/{room_id}/messages")
async def send_message(
    session: AsyncSessionTransactionDep,  # Transaction started here
    ...
):
    # SINGLE transaction for all operations
    message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,  # Reuses route-level transaction
    )
    return message


# CRUD function
async def send_user_message(session: AsyncSession, ...):
    # Uses route-level transaction (already active)
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room_message.user",
        payload={...},
    )
    return message


# Event emitter (Phase 4)
async def emit_event(session: AsyncSession, ...):
    # Uses route-level transaction (already active)

    # Write to DB
    session.add(event)
    await _update_projections(session, event)

    # Publish to Redis - SAME transaction context
    await redis_client.publish(f"room:{room_id}", event.json())

    # If ANYTHING fails, route-level transaction rolls back EVERYTHING
    # Database writes + Redis publish are atomic
```

**Result**: Clean, single transaction from route → CRUD → emit_event → Redis

### Option 2 (State Tracking) with Redis: ❌ BREAKS

```python
# Route handler
@router.post("/{room_id}/messages")
async def send_message(
    session: AsyncSessionDep,  # No transaction (just bare session)
    ...
):
    message = await send_user_message(...)
    return message


# CRUD function
async def send_user_message(session: AsyncSession, ...):
    if session.in_transaction():
        # Path A: Reuses existing transaction
        await emit_event(session, ...)
    else:
        # Path B: Creates transaction
        async with session.begin():
            await emit_event(session, ...)
        # Transaction COMMITS here - before route returns!


# Event emitter (Phase 4)
async def emit_event(session: AsyncSession, ...):
    # Write to DB
    session.add(event)
    await _update_projections(session, event)

    # Publish to Redis
    await redis_client.publish(f"room:{room_id}", event.json())

    # PROBLEM: If we're in Path B above, transaction already committed
    # But route hasn't returned yet - what if route has more work to do?
```

**Critical flaw**: With Option 2, the CRUD function commits the transaction before the route finishes. This breaks atomicity for multi-step operations.

### Phase 2 Requirement: Agent Integration

The async-strategy document shows this pattern:

```python
async def handle_message(room_id: UUID, user_message: str):
    # 1. Write user message event
    await emit_event(room_id, "message.user", {...})

    # 2. Run agent (async LLM call)
    agent_response = await agent_runner.run(room_id, user_message)

    # 3. Write agent message event
    await emit_event(room_id, "message.agent", {...})
```

**Requirement**: All three operations must be atomic - if agent fails, rollback user message.

#### Option 1 with Agent Integration: ✅ WORKS

```python
@router.post("/{room_id}/messages")
async def send_message_with_agent(
    session: AsyncSessionTransactionDep,  # Single transaction for entire flow
    ...
):
    # 1. Write user message (using shared transaction)
    await emit_event(session, room_id, "message.user", {...})

    # 2. Run agent
    try:
        agent_response = await agent_runner.run(room_id, user_message)
    except AgentError as e:
        # Agent failed - transaction will rollback user message on exception
        raise HTTPException(status_code=500, detail="Agent failed")

    # 3. Write agent message (using shared transaction)
    await emit_event(session, room_id, "message.agent", {...})

    # 4. Publish to Redis (using shared transaction)
    await redis_client.publish(...)

    # If ANYTHING fails, ALL operations rollback atomically
    return message
```

**Result**: True atomicity across user message → agent execution → agent response → Redis publish

#### Option 2 with Agent Integration: ❌ BREAKS

```python
@router.post("/{room_id}/messages")
async def send_message_with_agent(
    session: AsyncSessionDep,  # No transaction
    ...
):
    # 1. Write user message
    await emit_event(session, room_id, "message.user", {...})
    # ⚠️ If emit_event uses Option 2 pattern, it COMMITTED already!

    # 2. Run agent
    try:
        agent_response = await agent_runner.run(room_id, user_message)
    except AgentError as e:
        # 💥 BUG: Agent failed, but user message already committed!
        # Can't rollback - database now has orphaned user message
        raise HTTPException(status_code=500, detail="Agent failed")

    # 3. Write agent message
    await emit_event(session, room_id, "message.agent", {...})
```

**Critical flaw**: Can't rollback user message if agent fails because Option 2 already committed it.

## Pattern from async-strategy Document

The document shows this pattern (lines 97-105):

```python
@router.post("/rooms/{room_id}/messages")
async def send_message(
    room_id: UUID,
    message: MessageCreate,
    session: AsyncSessionDep,  # ⚠️ Incomplete - where does transaction start?
    current_user: CurrentUser,
):
    await emit_event(session, room_id, "message.user", {...})
    return {"status": "ok"}
```

**Problem**: This pattern is incomplete. `emit_event` expects a transaction, but `AsyncSessionDep` doesn't provide one.

**Option 1 completes the pattern**:

```python
@router.post("/rooms/{room_id}/messages")
async def send_message(
    room_id: UUID,
    message: MessageCreate,
    session: AsyncSessionTransactionDep,  # ✅ Transaction provided
    current_user: CurrentUser,
):
    await emit_event(session, room_id, "message.user", {...})
    # Transaction commits here (dependency cleanup)
    return {"status": "ok"}
```

## Comparison Table: Options with Async Context

| Feature | Option 1 (Route-Level) | Option 2 (State Tracking) |
|---------|------------------------|---------------------------|
| **Phase 1 (Current)** |
| Transaction atomicity | ✅ Guaranteed | ⚠️ Depends on code path |
| Code complexity | ✅ Simple | ❌ Complex (if/else everywhere) |
| **Phase 2 (Agent Integration)** |
| Agent + DB atomicity | ✅ Single transaction | ❌ Can't rollback committed events |
| Multi-step operations | ✅ All atomic | ❌ Early commits break atomicity |
| **Phase 4 (Redis Pub/Sub)** |
| DB + Redis atomicity | ✅ Single transaction | ❌ Commits before Redis publish |
| Rollback on Redis failure | ✅ Automatic | ❌ DB already committed |
| **Future Phases** |
| WebSocket streaming | ✅ Clean boundaries | ❌ Unclear transaction lifecycle |
| Event replay | ✅ Consistent state | ⚠️ Potential partial commits |

## Updated Recommendation

The async-strategy document makes **Option 1 absolutely critical** because:

### 1. **Aligns with Async Patterns**
The document shows `async with session.begin():` as the standard pattern. Option 1 uses this at the route level, maintaining consistency.

### 2. **Essential for Phase 4 Redis Integration**
Redis pub/sub MUST be in the same transaction as database writes. Option 2 can't guarantee this because it commits early.

### 3. **Essential for Phase 2 Agent Integration**
Agent execution must be atomic with message creation. Option 2 breaks this by committing before agent runs.

### 4. **Prevents Technical Debt**
The document warns about "forced refactor" costs. Using Option 2 creates transaction-related technical debt that must be refactored before Phase 2 and Phase 4.

### 5. **Matches Architectural Mandate**
"Async-first I/O is mandatory" - Option 1 embraces this with proper async transaction management.

## Concrete Example: Why Option 2 Fails with Redis

```python
# Option 2 Pattern (BROKEN with Redis)
async def send_user_message(session: AsyncSession, ...):
    if session.in_transaction():
        # Path A: Transaction managed elsewhere (WHERE?)
        await emit_event(session, ...)  # Writes DB + publishes Redis
        # Who commits? When?
    else:
        # Path B: We manage transaction
        async with session.begin():
            await emit_event(session, ...)  # Writes DB + publishes Redis
        # Commits HERE - but what if route has more work?


# Scenario: Route wants to do multiple operations
@router.post("/{room_id}/messages")
async def send_message_batch(session: AsyncSessionDep, messages: list):
    for msg in messages:
        await send_user_message(session, msg)
        # 💥 BUG: Each call commits independently!
        # Can't rollback earlier messages if later ones fail
        # Redis already has events for committed messages
```

**With Option 1**:
```python
@router.post("/{room_id}/messages")
async def send_message_batch(
    session: AsyncSessionTransactionDep,  # Single transaction
    messages: list
):
    for msg in messages:
        await send_user_message(session, msg)
        # All use same transaction
    # ALL commit together or ALL rollback together
    # Redis only gets events if ALL succeed
```

## Final Verdict

Given the async-strategy requirements, **Option 2 is not viable** for this architecture.

**Option 1 is the ONLY choice** that supports:
- ✅ Current Phase 1 transaction safety
- ✅ Phase 2 agent integration with atomicity
- ✅ Phase 4 Redis pub/sub with transactional guarantees
- ✅ Future WebSocket streaming requirements
- ✅ Architectural mandate for async-first I/O

The async context doesn't just strengthen Option 1's case - it makes Option 2 **architecturally incompatible** with future requirements.
