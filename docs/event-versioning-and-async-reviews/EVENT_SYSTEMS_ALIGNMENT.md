# Event Systems Alignment Analysis

**Last Updated:** 2026-01-04
**Status:** 🔍 Analysis Document : COMPLETED IMPLEMENTATION
**Purpose:** Align CYOA story replay with Room chat replay patterns

---

## Executive Summary

The codebase has **a hybrid event-sourced system**.

| Aspect | Room Chat System | CYOA Story System |
|--------|-----------------|-------------------|
| **Events Table** | `RoomEvent` (implemented) | `UserNodeChoice` (implemented) |
| **Ordering** | `room_sequence` (monotonic per room) | `parent_choice_id` (tree structure) |
| **Replay Pattern** | Sequence-based (`replay_events_since`) | Ancestor chain traversal |
| **Real-Time** | ✅ Direct Redis publish in `emit_event()` | ✅ implemented |
| **Projection Updates** | Transactional (inline with event) | Transactional (inline with event) |
| **WebSocket** | ✅ implemented | ✅ implemented |
| **Graceful Degradation** | ✅ Redis failure logged, event persisted | ✅ Redis failure logged, event persisted |

---

## Key Architectural Difference

### Room Chat: **Direct Redis Publish**

```python
# event_emitter.py line 148-154
await session.flush()
await _publish_to_redis(room_id, event)  # Direct publish, graceful failure
```

**Characteristics:**
- Publishes to Redis immediately after DB flush
- Still within transaction scope (commit happens later in route handler)
- Graceful degradation: Redis failure logged but doesn't fail transaction
- Simple: No background workers or outbox tables


---

## Why the Difference?

The Room Chat system was implemented with **pragmatic simplicity**:
- Redis publish happens in-process
- Failure is acceptable (clients can replay from DB)
- Lower latency (no polling delay)

We may eventually move to an Outbox centric **enterprise pattern**:
- More reliable delivery guarantees
- Better for critical story state changes
- Handles Redis downtime gracefully

---

## Unified Approach Implementation

### **Current: Adopted Room Chat Pattern for CYOA (**

**Rationale:**
- Already proven in production (`event_emitter.py`)
- Simpler implementation (no Outbox, no worker)
- Consistent with existing codebase patterns
- Adequate reliability for CYOA use case

**Implementation:**

####  we are using a shared Redis publisher

# implementation : backend/app/services/realtime_publisher.py


#### Room Chat uses Shared Publisher



# backend/app/services/event_emitter.py
# _publish_to_redis function (~lines 158-214) 
# publish_agent_token (~lines 217-253)

####  CYOA Endpoints use real time publisher

# backend/app/api/routes/user_story_progress.py

# make_story_choice, undo_story_choice and jump_story_head use real time publisher(background_tasks.add_task and publish_event_to_redis) 


#### WebSocket System extended to Stories


##### 4A: Generalize ConnectionManager (Minor Changes)

The `ConnectionManager` is generic and uses `room_id` parameter but the implementation works for any UUID-based channel. 

**extending code works because:**
- `room_id` is just a UUID - can be story_id too
- Channel name is `f"room:{room_id}"` - story channel support added
- All other logic is channel-agnostic

##### Story WebSocket Route

```python
# backend/app/api/routes/websocket.py

@router.websocket("/ws/stories/{story_id}")
async def websocket_story_session() 
```

**Key Differences from Room WebSocket:**
1. **Channel:** `story:{story_id}` instead of `room:{room_id}`
2. **Handshake:** Uses `last_head_version` + `user_persona_id` instead of `last_sequence`
3. **Replay:** Sends full `timeline.sync` instead of event-by-event replay
4. **No message sending:** Stories are read-only via WebSocket (mutations via REST API)

##### Future extension design:  Extend ConnectionManager for reusability - required prior to release, after fan-out proof (load testing)

# backend/app/services/websocket_manager has commented out stub of subscribe_to_channel which would make  it reusable for any event stream type.

---

### **POTENTIAL FUTURE STATE Use Outbox Pattern for all systems**

**Pros:**
- More robust delivery guarantees
- Industry standard pattern
- Better for mission-critical events

**Cons:**
- More complex (Outbox table, background worker)
- Higher latency (polling delay)
- Would require refactoring Room Chat system

**Verdict:** Not prior to release of V1.



---

## Key Implementation Notes and Divergence from CYOA main plan

### Notes on Event System and Redis publish


Direct Redis publish is used in Room Chat and CYOA systems.

### Async Context for Sync Routes

Since CYOA routes are **synchronous** (not async), use `asyncio.create_task()` for non-blocking Redis publish:

```python
import asyncio

# In sync route handler
session.commit()

# Don't await - fire and forget
asyncio.create_task(
    publish_event_to_redis(...)
)
```

### Graceful Degradation

Both systems handle Redis failure the same way:
- Event is persisted in Postgres (source of truth)
- Redis publish failure is logged but doesn't fail request
- Clients replay from DB on reconnect

### Channel Naming Convention

| System | Channel Pattern | Example |
|--------|----------------|---------|
| Room Chat | `room:{room_id}` | `room:550e8400-e29b-41d4-a716-446655440000` |
| CYOA Stories | `story:{story_id}` | `story:123e4567-e89b-12d3-a456-426614174000` |

### Event Replay on Reconnect

**Room Chat:**
```python
# Client sends last sequence received
events = await replay_events_since(
    session=session,
    room_id=room_id,
    after_sequence=last_sequence
)
```

**CYOA Stories:**
```python
# Client sends last head_version received
# Compare with current progress.head_version
# If different, return full timeline
timeline = get_timeline(...)
```

---

## Validation Criteria

✅ **Unified when:**
✅ Both systems use `realtime_publisher.py` for Redis publishing
✅ Shared WebSocket endpoint supports both room/* and story/* channels
✅ Graceful degradation behavior is identical

---

## References

See:
- `backend/app/services/event_emitter.py` - Room Chat implementation
- `backend/app/services/event_replay.py` - Room replay logic
- `backend/docs/RULES.md` - Backend conventions
