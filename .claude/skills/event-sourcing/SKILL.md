---
name: event-sourcing
description: |
  Event-sourcing and real-time messaging system for room-based chat. Use when working with:
  - Room events (create, update, messages, participants)
  - Real-time WebSocket delivery via Redis pub/sub
  - Event replay for client reconnection
  - Agent token streaming

  Triggers: event_emitter.py, event_replay.py, realtime_publisher.py, websocket_manager.py,
  emit_event, RoomEvent, room events, event sourcing, projections, Redis pub/sub, WebSocket
---

# Event-Sourcing System

## Architecture

Single write path through `emit_event()` with transactional projections:

```
emit_event() → [Postgres: Event + Projections] → [Redis pub/sub] → [WebSocket clients]
```

**Critical Invariants:**
- Events are immutable (append-only)
- All room writes go through `emit_event()`
- Projections update in same transaction as event
- Advisory locks ensure sequence ordering per room

## Quick Reference

### Emit an Event

```python
from app.services.event_emitter import emit_event

event = await emit_event(
    session,                    # AsyncSession with active transaction
    room_id,                    # UUID
    "room_message.user",        # Event type
    {"sender_id": str(user.id), "content": "Hello"},
    enrichment_metadata={"trace_id": "..."}  # Optional
)
```

### Stream Agent Tokens

```python
from app.services.event_emitter import publish_agent_token

await publish_agent_token(room_id, "agent-name", "token")
```

### Replay Events (Reconnection)

```python
from app.services.event_replay import replay_events_since, get_latest_sequence

events = await replay_events_since(
    session=session,
    room_id=room_id,
    after_sequence=last_seen,  # Client's last sequence
    limit=1000
)
latest = await get_latest_sequence(session=session, room_id=room_id)
```

## File Locations

| Service | Path | Purpose |
|---------|------|---------|
| Event Emitter | `backend/app/services/event_emitter.py` | Write path, projections |
| Event Replay | `backend/app/services/event_replay.py` | Reconnection replay |
| Realtime Publisher | `backend/app/services/realtime_publisher.py` | Redis pub/sub |
| WebSocket Manager | `backend/app/services/websocket_manager.py` | Connection management |

## References

- **Control flow & call hierarchies**: See [references/control-flow.md](references/control-flow.md)
- **Event types & payloads**: See [references/event-types.md](references/event-types.md)

## Event Types

| Event Type | Description |
|------------|-------------|
| `room.created` | New room created |
| `room.updated` | Room metadata changed |
| `participant.joined` | User/agent joined |
| `participant.left` | User/agent left (soft delete) |
| `participant.role_changed` | Role updated |
| `room_message.user` | User message |
| `room_message.agent` | Agent message |
| `message.edited` | Content edited |
| `message.pinned` | Message pinned |
| `message.unpinned` | Message unpinned |
| `message.context_toggled` | Context flag toggled |
| `message.deleted` | Message soft-deleted |

## Adding New Event Types

1. Add handler in `event_emitter.py`:
   ```python
   async def _handle_new_event(session: AsyncSession, event: RoomEvent) -> None:
       payload = event.payload
       # Update projection tables
   ```

2. Register in `_update_projections()` handlers dict:
   ```python
   handlers = {
       # ...existing handlers...
       "new.event_type": _handle_new_event,
   }
   ```

3. Document payload in [references/event-types.md](references/event-types.md)

## WebSocket Connection Flow

```python
# Route handler pattern
@router.websocket("/ws/rooms/{room_id}")
async def websocket_room(websocket: WebSocket, room_id: UUID):
    await connection_manager.connect(websocket, room_id)
    try:
        async for message in websocket.iter_json():
            if message["type"] == "replay":
                events = await replay_events_since(...)
                await websocket.send_json({"type": "replay", "events": events})
    finally:
        await connection_manager.disconnect(websocket)
```

## Transaction Requirements

`emit_event()` expects an active transaction (use `AsyncSessionTransactionDep`):

```python
@router.post("/{room_id}/messages")
async def send_message(
    session: AsyncSessionTransactionDep,  # Transaction auto-commits
    room_id: UUID,
    ...
):
    event = await emit_event(session, room_id, "room_message.user", {...})
    return event  # Commit on return
```

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Redis unavailable | Event persisted, warning logged, clients catch up via replay |
| Sequence conflict | IntegrityError raised, caller retries |
| Unknown event type | ValueError raised |
