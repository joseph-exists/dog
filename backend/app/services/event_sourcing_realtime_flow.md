```mermaid
%% Event Sourcing + Realtime Flow
%% Focus: emit_event write-path, Redis fanout, and replay read-path.
flowchart TD
  A[emit_event()] --> B["RoomEvent append"]
  A --> C[_update_projections()]
  C --> D[("Projection tables")]
  A --> E[session.flush()]
  A --> F[publish_event_to_redis()]
  F --> G[("Redis pub/sub")]
  G --> H[ConnectionManager._listen_to_room()]
  H --> I[send_to_room()]
  I --> J["WebSocket clients"]

  subgraph "Replay Path"
    K[replay_events_since()] --> L[("RoomEvent query")]
    L --> M["Event list to client"]
  end
```
