# Event-Sourcing Control Flow & Call Hierarchies

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Write Path (Event Emission)](#write-path-event-emission)
3. [Read Path (Event Replay)](#read-path-event-replay)
4. [Real-time Delivery (WebSocket + Redis)](#real-time-delivery)
5. [Call Hierarchy Diagrams](#call-hierarchy-diagrams)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           CLIENT REQUEST                                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  WRITE PATH (event_emitter.py)                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ emit_event()                                                     │   │
│  │   ├── _get_next_room_sequence()  [Advisory Lock + MAX query]    │   │
│  │   ├── Create RoomEvent                                           │   │
│  │   ├── _update_projections()  [Dispatch to handler]              │   │
│  │   ├── session.flush()  [Read-after-write consistency]           │   │
│  │   └── _publish_to_redis()  → realtime_publisher                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
┌──────────────────────────────┐   ┌──────────────────────────────────────┐
│  POSTGRES                    │   │  REDIS PUB/SUB                       │
│  ├── room_events (log)       │   │  Channel: room:{room_id}             │
│  └── projections (Room,      │   └──────────────────────────────────────┘
│      RoomMessage,            │                   │
│      RoomParticipant)        │                   ▼
└──────────────────────────────┘   ┌──────────────────────────────────────┐
         │                         │  websocket_manager.py                 │
         │                         │  ConnectionManager._listen_to_room()  │
         ▼                         │       └── send_to_room()              │
┌──────────────────────────────┐   └──────────────────────────────────────┘
│  READ PATH (event_replay.py) │                   │
│  ├── replay_events_since()   │                   ▼
│  └── get_latest_sequence()   │   ┌──────────────────────────────────────┐
└──────────────────────────────┘   │  WEBSOCKET CLIENTS                   │
                                   └──────────────────────────────────────┘
```

---

## Write Path (Event Emission)

**Entry Point:** `backend/app/services/event_emitter.py`

### emit_event() - Main Write Function

```
emit_event(session, room_id, event_type, payload, enrichment_metadata)
│
├── 1. _get_next_room_sequence(session, room_id)
│       ├── pg_advisory_xact_lock(hash(room_id))  # Transaction-scoped lock
│       └── SELECT MAX(room_sequence) FROM room_events WHERE room_id = ?
│           └── Returns: max + 1 (or 1 if first event)
│
├── 2. Create RoomEvent(event_id, room_id, room_sequence, event_type, payload, ...)
│       └── session.add(event)
│
├── 3. _update_projections(session, event)
│       ├── Dispatch to handler based on event_type
│       │   ├── "room.created"           → _handle_room_created()
│       │   ├── "room.updated"           → _handle_room_updated()
│       │   ├── "participant.joined"     → _handle_participant_joined()
│       │   ├── "participant.left"       → _handle_participant_left()
│       │   ├── "participant.role_changed" → _handle_participant_role_changed()
│       │   ├── "room_message.user"      → _handle_room_message_user()
│       │   ├── "room_message.agent"     → _handle_room_message_agent()
│       │   ├── "message.edited"         → _handle_message_edited()
│       │   ├── "message.pinned"         → _handle_message_pinned()
│       │   ├── "message.unpinned"       → _handle_message_unpinned()
│       │   ├── "message.context_toggled" → _handle_message_context_toggled()
│       │   └── "message.deleted"        → _handle_message_deleted()
│       │
│       └── _update_room_last_activity(session, room_id, timestamp)
│
├── 4. session.flush()  # Ensures read-after-write consistency
│
├── 5. _publish_to_redis(room_id, event)
│       └── realtime_publisher.publish_event_to_redis(
│               channel=f"room:{room_id}",
│               event_type, sequence, payload, created_at
│           )
│
└── Returns: RoomEvent
```

### Projection Handler Details

Each handler updates the corresponding projection table:

| Handler | Projection Table | Operation |
|---------|------------------|-----------|
| `_handle_room_created` | `Room` | INSERT |
| `_handle_room_updated` | `Room` | UPDATE fields |
| `_handle_participant_joined` | `RoomParticipant` | INSERT or reactivate |
| `_handle_participant_left` | `RoomParticipant` | UPDATE (soft delete) |
| `_handle_participant_role_changed` | `RoomParticipant` | UPDATE role |
| `_handle_room_message_user` | `RoomMessage` | INSERT |
| `_handle_room_message_agent` | `RoomMessage` | INSERT |
| `_handle_message_edited` | `RoomMessage` | UPDATE content |
| `_handle_message_pinned` | `RoomMessage` | UPDATE is_pinned=True |
| `_handle_message_unpinned` | `RoomMessage` | UPDATE is_pinned=False |
| `_handle_message_context_toggled` | `RoomMessage` | UPDATE active_for_context |
| `_handle_message_deleted` | `RoomMessage` | DELETE (from projection only) |

### Token Streaming (Ephemeral)

```
publish_agent_token(room_id, agent_name, token)
│
└── realtime_publisher.publish_ephemeral_message(
        channel=f"room:{room_id}",
        message_type="message.delta",
        payload={agent_name, content: token}
    )
```

**Note:** Token streaming is NOT persisted. Final message saved via `room_message.agent` event.

---

## Read Path (Event Replay)

**Entry Point:** `backend/app/services/event_replay.py`

### replay_events_since()

```
replay_events_since(session, room_id, after_sequence, limit=1000)
│
├── SELECT * FROM room_events
│   WHERE room_id = ? AND room_sequence > after_sequence
│   ORDER BY room_sequence ASC
│   LIMIT 1000
│
└── Returns: List[{type, sequence, event_type, payload, created_at}]
```

### get_latest_sequence()

```
get_latest_sequence(session, room_id)
│
├── SELECT room_sequence FROM room_events
│   WHERE room_id = ?
│   ORDER BY room_sequence DESC
│   LIMIT 1
│
└── Returns: int (latest sequence, or 0 if no events)
```

---

## Real-time Delivery

**Entry Point:** `backend/app/services/websocket_manager.py`

### Connection Lifecycle

```
ConnectionManager (singleton per worker)
│
├── connect(websocket, room_id)
│   ├── websocket.accept()
│   ├── Add to room_connections[room_id]
│   ├── Track in websocket_rooms[websocket] = room_id
│   └── IF first connection to room:
│       └── _subscribe_to_room(room_id)
│           ├── redis.pubsub()
│           ├── pubsub.subscribe(f"room:{room_id}")
│           └── asyncio.create_task(_listen_to_room(room_id, pubsub))
│
├── disconnect(websocket)
│   ├── Remove from room_connections[room_id]
│   ├── Remove from websocket_rooms
│   └── IF last connection in room:
│       └── _unsubscribe_from_room(room_id)
│           ├── pubsub.unsubscribe()
│           └── pubsub.close()
│
└── send_to_room(room_id, message)
    └── FOR websocket IN room_connections[room_id]:
        └── websocket.send_text(json.dumps(message))
```

### Redis Listener (Background Task)

```
_listen_to_room(room_id, pubsub)  # Runs as asyncio task
│
└── LOOP: async for message in pubsub.listen()
    │
    ├── IF message["type"] == "message":
    │   ├── data = json.loads(message["data"])
    │   └── await send_to_room(room_id, data)
    │
    ├── IF message["type"] == "subscribe":
    │   └── Log subscription confirmation
    │
    └── IF room_id not in room_subscriptions:
        └── BREAK (room unsubscribed)
```

---

## Call Hierarchy Diagrams

### Complete Write Flow

```
Route Handler (e.g., POST /rooms/{room_id}/messages)
└── emit_event(session, room_id, "room_message.user", payload)
    ├── _get_next_room_sequence(session, room_id)
    │   └── [Postgres: Advisory Lock + MAX query]
    ├── session.add(RoomEvent)
    ├── _update_projections(session, event)
    │   ├── _handle_room_message_user(session, event)
    │   │   └── session.add(RoomMessage)
    │   └── _update_room_last_activity(session, room_id, timestamp)
    │       └── [Postgres: UPDATE Room.last_activity]
    ├── session.flush()
    └── _publish_to_redis(room_id, event)
        └── publish_event_to_redis(channel, event_type, sequence, payload, created_at)
            └── redis.publish(channel, json.dumps(message))
```

### Complete Read/Reconnect Flow

```
WebSocket Route (GET /ws/rooms/{room_id})
├── connection_manager.connect(websocket, room_id)
│   └── _subscribe_to_room(room_id)
│       └── asyncio.create_task(_listen_to_room)
│
├── Client sends: {"type": "replay", "after_sequence": N}
│   └── replay_events_since(session, room_id, after_sequence=N)
│       └── [Postgres: SELECT events > N]
│
└── Background: _listen_to_room() forwards Redis messages to client
```

### Multi-Worker Fan-out

```
Worker 1                          Worker 2                          Worker 3
    │                                 │                                 │
    │  emit_event()                   │                                 │
    │      │                          │                                 │
    │      ├── [Postgres Write]       │                                 │
    │      │                          │                                 │
    │      └── redis.publish()────────┼─────────────────────────────────┤
    │               │                 │                                 │
    │               ▼                 ▼                                 ▼
    │         [Redis Channel: room:XYZ]                                 │
    │               │                 │                                 │
    │               ▼                 ▼                                 ▼
    │    _listen_to_room()    _listen_to_room()              _listen_to_room()
    │         │                      │                              │
    │         ▼                      ▼                              ▼
    │    send_to_room()        send_to_room()                send_to_room()
    │         │                      │                              │
    │         ▼                      ▼                              ▼
    │    [WS Clients]          [WS Clients]                  [WS Clients]
```

---

## File Locations

| Service | Path |
|---------|------|
| Event Emitter | `backend/app/services/event_emitter.py` |
| Event Replay | `backend/app/services/event_replay.py` |
| Realtime Publisher | `backend/app/services/realtime_publisher.py` |
| WebSocket Manager | `backend/app/services/websocket_manager.py` |
| Redis Client | `backend/app/core/redis.py` |
| Models | `backend/app/models.py` |
