Event Services Walkthrough

Purpose
Provide a clear walkthrough of how event_emitter, event_replay, realtime_publisher, and websocket_manager intersect and the contracts between them. This is the baseline for AG-UI integration work.

Services and Contracts

1) event_emitter.py (Write Path, Source of Truth)
- Role: Single write-path for room state changes. Persists RoomEvent and updates projections in one transaction.
- Contract:
  - Must be called within an active transaction (AsyncSessionTransactionDep).
  - Emits immutable RoomEvent with monotonically increasing room_sequence.
  - Updates projections before flush and Redis publish.
  - Publishes to Redis via realtime_publisher.publish_event_to_redis after flush.
- Output message format (Redis):
  {
    "type": "event",
    "sequence": int,
    "event_type": str,
    "payload": {...},
    "created_at": ISO timestamp
  }
- Failure mode: Redis publish failures are logged but do not fail the transaction.

2) realtime_publisher.py (Redis Adapter)
- Role: Shared Redis pub/sub utility for event emission and ephemeral messages.
- Contract:
  - publish_event_to_redis(channel, event_type, sequence, payload, created_at)
    - Publishes the standardized event format above.
  - publish_ephemeral_message(channel, message_type, payload)
    - For non-persisted events (agent token streaming, typing, presence).
- Failure mode: Redis issues are logged; no exception is raised to caller.

3) websocket_manager.py (Fanout + Subscription)
- Role: Per-worker manager for WebSocket connections and Redis subscriptions.
- Contract:
  - Subscribes to Redis channel `room:{room_id}` on first connection.
  - Forwards Redis messages (JSON) to all WebSockets in that room.
  - Unsubscribes when room has no connections.
- Message handling:
  - Expects JSON messages with `type` and payload.
  - Forwards both persisted events and ephemeral events.

4) event_replay.py (Reconnect Path)
- Role: Catch-up for clients after disconnect based on sequence numbers.
- Contract:
  - replay_events_since(room_id, after_sequence, limit=1000)
    - Returns list of event dicts in the same format as Redis events.
  - get_latest_sequence(room_id)
    - Returns max room_sequence or 0 if none.

End-to-End Flow

Write path (persisted events)
1) Route handler calls emit_event(...) within transaction.
2) emit_event creates RoomEvent + updates projections + flushes.
3) emit_event publishes to Redis via realtime_publisher.
4) websocket_manager listens to Redis and forwards to clients.
5) Client updates UI immediately; event is also persisted for replay.

Reconnect path (missed events)
1) Client reconnects with last known sequence.
2) server calls replay_events_since(...) to fetch missed events.
3) Client rehydrates state from replayed events, then resumes live stream.

Ephemeral path (non-persisted)
1) Server emits token stream or presence via publish_ephemeral_message.
2) websocket_manager forwards ephemeral messages to clients.
3) No persistence; client must treat as best-effort.

Key Contracts to Preserve
- event_emitter is the only write path for room events.
- Redis message format must remain AG-UI compatible.
- room_sequence must be monotonic and per-room for replay to work.
- replayed events must match the real-time event schema exactly.

AG-UI Considerations
- AG-UI expects ordered events and stable schemas.
- Ephemeral events (message.delta) should remain non-persisted.
- Final messages should be persisted as room_message.agent events.
- Client should merge replay + live stream seamlessly.

Known Risk Areas
- Redis outages: live updates may not arrive; replay must be reliable.
- Large replays: replay_events_since uses a hard limit (1000). Clients may need pagination.
- Subscription churn: websocket_manager unsubscribes when last connection drops; reconnecting clients must re-subscribe.

Suggested Debug Checklist
- Verify emit_event called within transaction (check route handler).
- Confirm Redis publish logs and subscriber count > 0.
- Ensure websocket_manager has room subscription active.
- On reconnect, verify replay_events_since returns events with correct sequence.

Divergences: Inline Docs vs Behavior
- event_emitter.py: Docstring says emit_event raises ValueError if event_type not supported, but the code does not validate event_type.
- event_emitter.py: Docstring says Redis publish is after transaction flush; this is true, but still occurs before commit (publish happens within the same transaction scope).
- event_replay.py: Docstring mentions pagination as future enhancement; behavior currently hard-caps results at limit with a warning and no pagination token.
- realtime_publisher.py: Docstring states best-effort delivery; behavior is consistent, but publish_event_to_redis logs subscriber count even if 0, which may be misread as success.
- websocket_manager.py: Docstring implies fanout is stable for reconnects; in practice, reconnects rely on event_replay and do not reuse prior PubSub state.

Reliability and Traffic Capacity Analysis

Assumptions
- Redis is used only for pub/sub fanout (no durable queue).
- Postgres is the source of truth for all persisted events.
- WebSockets are per-worker; no sticky sessions required.

Low Traffic / High Reliability
- Works well: event_emitter persists events, Redis pushes to WS.
- Replay path handles transient disconnects.
- Single worker environments stable.

Moderate Traffic / Typical Reliability
- Redis pub/sub scales across workers, but subscriber count per channel can be large.
- Potential pressure points:
  - Redis publish throughput (fanout to many clients).
  - WebSocket send throughput per worker.
  - Replay bursts after deploys or reconnect storms.
- Mitigations:
  - Increase Redis max connections and use pipelined publishes if needed.
  - Consider backpressure handling in websocket_manager (drop or throttle).
  - Add replay pagination or limit client catch-up windows.

High Traffic / Lower Reliability
- Risks:
  - Redis outages lead to live updates missed; replay becomes critical.
  - Large replay payloads can stress Postgres and clients.
  - Per-room connection fanout can saturate a single worker.
- Mitigations:
  - Partition rooms across workers and monitor per-room fanout size.
  - Add replay pagination and resumable cursors.
  - Implement event compression or snapshotting for large histories.
  - Add circuit breakers to avoid flooding WS when replay lag is large.

Reliability Profiles
- Redis down: System continues to persist events; clients must rely on replay on reconnect.
- Postgres down: Emits fail; no events persist, and system is effectively down.
- Network flaps: replay handles gaps; sequence numbers keep ordering.

Capacity Summary
- The architecture is resilient for low–moderate traffic with occasional disconnects.
- For high-traffic rooms or frequent reconnect storms, the current design needs replay pagination, backpressure, and possibly snapshotting to maintain latency and reliability.
