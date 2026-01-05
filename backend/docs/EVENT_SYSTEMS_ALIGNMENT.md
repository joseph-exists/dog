# Event Systems Alignment Analysis

**Last Updated:** 2026-01-04
**Status:** 🔍 Analysis Document : COMPLETED IMPLEMENTATION
**Purpose:** Align CYOA story replay with Room chat replay patterns

---

## Executive Summary

The codebase has **two event-sourced systems** with different patterns:

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

### CYOA Phase 4 Legacy Plan: **Transactional Outbox Pattern**

DEPRECATED : WILL NOT MOVE FORWARD

---

## Why the Difference?

The Room Chat system was implemented with **pragmatic simplicity**:
- Redis publish happens in-process
- Failure is acceptable (clients can replay from DB)
- Lower latency (no polling delay)

The CYOA Phase 4 plan used an **enterprise pattern**:
- More reliable delivery guarantees
- Better for critical story state changes
- Handles Redis downtime gracefully

---

## Recommendation: Unified Approach

### **Option 1: Adopt Room Chat Pattern for CYOA (RECOMMENDED)**

**Rationale:**
- Already proven in production (`event_emitter.py`)
- Simpler implementation (no Outbox, no worker)
- Consistent with existing codebase patterns
- Adequate reliability for CYOA use case

**Implementation:**

#### [x] Step 1: Create Shared Redis Publisher

# implementation : backend/app/services/realtime_publisher.py


#### [X] Step 2: Update Room Chat to Use Shared Publisher

COMPLETE.

# backend/app/services/event_emitter.py
# REFACTORED _publish_to_redis function (lines 158-214) 
# REFACTORED publish_agent_token (lines 217-253)

#### [x] Step 3: Add Real-Time to CYOA Endpoints

# backend/app/api/routes/user_story_progress.py

# modified make_story_choice, undo_story_choice and jump_story_head (background_tasks.add_task and publish_event_to_redis)


#### Step 4: Extend Existing WebSocket System for Stories


##### 4A: Generalize ConnectionManager (Minor Changes)

The `ConnectionManager` is generic and uses `room_id` parameter but the implementation works for any UUID-based channel. 

**Current code works because:**
- `room_id` is just a UUID - can be story_id too
- Channel name is `f"room:{room_id}"` - story channel support added
- All other logic is channel-agnostic

##### 4B: Add Story WebSocket Route

```python
# backend/app/api/routes/websocket.py

# new route added:

@router.websocket("/ws/stories/{story_id}")
async def websocket_story_session() 
```

**Key Differences from Room WebSocket:**
1. **Channel:** `story:{story_id}` instead of `room:{room_id}`
2. **Handshake:** Uses `last_head_version` + `user_persona_id` instead of `last_sequence`
3. **Replay:** Sends full `timeline.sync` instead of event-by-event replay
4. **No message sending:** Stories are read-only via WebSocket (mutations via REST API)

##### 4C: Alternative - Extend ConnectionManager (More Reusable) FUTURE STATE, NOT NOW

If you want to make ConnectionManager truly generic for future use cases:

```python
# backend/app/services/websocket_manager.py

# MODIFY _subscribe_to_room to accept custom channel:

async def subscribe_to_channel(
    self,
    channel_id: UUID,
    channel_type: str = "room"  # "room" or "story"
) -> None:
    """
    Subscribe to Redis pub/sub channel.

    Args:
        channel_id: UUID of the resource
        channel_type: Type of channel ("room", "story", etc.)
    """
    channel = f"{channel_type}:{channel_id}"
    # ... rest of implementation same, just use channel variable
```

This makes it reusable for any event stream type.

---

### **Option 2:  POTENTIAL FUTURE STATE Use Outbox Pattern for Both Systems**

**Pros:**
- More robust delivery guarantees
- Industry standard pattern
- Better for mission-critical events

**Cons:**
- More complex (Outbox table, background worker)
- Higher latency (polling delay)
- Would require refactoring Room Chat system

**Verdict:** Not recommended unless reliability requirements change significantly.



---

## Key Implementation Notes and Divergence from CYOA main plan

### No Outbox Table Needed

The Outbox pattern from `CYOA_PHASE4_QUICKREF.md` can be **skipped** entirely:
- ❌ No `Outbox` model
- ❌ No outbox publisher worker
- ❌ No outbox CRUD functions

Instead, use direct Redis publish like Room Chat system.

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

Alternatively, convert routes to async (bigger refactor).

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

## Success Criteria

✅ **Unified when:**
1. Both systems use `realtime_publisher.py` for Redis publishing
2. Shared WebSocket endpoint supports both room/* and story/* channels
3. Graceful degradation behavior is identical
4. No Outbox table or background workers
5. All existing Room Chat functionality preserved
6. CYOA Phase 4 real-time features working

---

## Questions?

See:
- `backend/app/services/event_emitter.py` - Room Chat implementation
- `backend/app/services/event_replay.py` - Room replay logic
- `backend/docs/CYOA_MIGRATION_PLAN.md` - Original CYOA plan
- `backend/docs/RULES.md` - Backend conventions
