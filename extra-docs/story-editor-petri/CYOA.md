This is the recreated MVP technical specification for a CYOA fantasy game with a CPN-modeled state engine and **branching timelines** (reader rewind), with randomized NPC movement, and with abandoned branches hidden from the player. It maps the CPN concepts to an event-sourced, n-tier implementation using Postgres + FastAPI/Pydantic + React/TypeScript + Redis pub/sub + a transactional outbox.[^1][^2][^3]

## Product intent (pyramid top)

Ship an online CYOA where the player (persona - eg Ava) makes choices that fire transitions over a world/character state marking, can rewind to earlier points, and can continue from there to create a new future while the old future becomes invisible.[^4][^1]
The engine must support locations, time, inventory with item state, character state, world state, and at least one multi-character join scene (Ava (persona) meets Bram (AI Agent/NPC)) with NPC movement that is randomized but captured per branch.[^2][^1]

## Domain model (CPN ↔ event sourcing)

### CPN mapping (conceptual)

- **Places** = state buckets; **tokens** carry typed state (“colors”); **marking** = the entire authoritative game state.[^1]
- **Transitions** = discrete state changes (choices/events) that are enabled by **guards** and that consume/produce tokens (update state).[^1]
- **Join scenes** are transitions requiring multiple character tokens (synchronization), and rewinding is implemented by moving the active “head” over the history rather than by reversing transitions.[^4]


### Authoritative state representation

The authoritative state for play is the marking at the current `head_node_id`, derived by snapshot + replay along the active branch.[^5][^4]
World state is represented by a singleton World token; character state is represented by one token per character, including inventory and item state.[^5]

### Minimal token schemas

- `WorldState`: `{clock, world_flags, location_flags}` (singleton)[^5]
- `CharState`: `{char_id, location_id, char_flags, inventory:[ItemState...]}`[^5]
- `ItemState`: `{item_id, kind, state_flags, charges?, owner_char_id}`[^5]


### Minimal transition types (MVP)

- `Choice`, `Travel`, `AcquireItem`, `UseItem`, `AdvanceTime`, `ScheduledEvent`, `JoinScene`.[^1]
Random NPC movement is implemented as part of `ScheduledEvent` (or `Choice` side-effects) but must persist its realized RNG outcome into the event payload for that branch.[^1][^5]


## Timeline semantics (branching + hidden futures)

### Event tree + head pointer

Use event sourcing: every transition firing appends an immutable event that can be replayed to derive state.[^6][^1]
Model history as a **tree** with `parent_id`, and store a per-game **head pointer** indicating the currently active node; the UI shows only the active path from root → head.[^4][^5]

### Rewind behavior (required UX)

- “Jump back” moves head to an ancestor node and makes any previously-created future invisible (not part of the active path).[^4]
- A new choice after jumping back appends a new child event under the current head, creating a new branch; old branches remain stored but are not returned by any MVP query.[^4][^1]
- “Redo” is not recomputation; it is moving head to a chosen child node, but MVP hides abandoned branches so redo is effectively only possible within the current visible path (i.e., redo after undo without forking).[^4]


### Determinism boundary (random NPC - or PydanticAI agent)

Projection/rebuild logic must be deterministic with respect to the event stream; therefore, any randomness that affects state must be captured in event payloads (seed or realized outcome).[^7][^5]

## Architecture (n-tier)

### Frontend (React/TypeScript)

- Renders a state projection: location/scene text, clock, inventory, and enabled choices derived from the server’s head state.[^4]
- Supports timeline navigation controls: “undo” (jump to parent), and “jump to earlier” (select an ancestor from the visible path only).[^4]
- Maintains a local `(head_node_id, head_version)` and discards pushed updates that don’t match monotonic expectations, refetching when out of sync.[^8][^2]


### API layer (FastAPI + Pydantic)

- Command endpoints:
    - `POST /games/{id}/transitions/{tid}:attempt`
    - `POST /games/{id}/undo` (jump to parent)
    - `POST /games/{id}/jump/{node_id}` (must be ancestor of current head)[^8][^1]
- Query endpoints:
    - `GET /games/{id}/state` (always resolves state at head; never returns branch lists)
    - `GET /games/{id}/timeline` (returns only the ancestor chain root→head for rendering breadcrumbs)[^4]
- Real-time:
    - `WS /games/{id}/stream` publishes `HeadMoved` and `GameStateChanged` messages.[^2]


### Service layer (Domain engine façade)  (need more details here)

Responsibilities:

- Load head pointer and reconstruct marking at head (snapshot + replay).[^5][^4]
- Compute enabled transitions (guards) for Ava given marking.[^1]
- Apply a transition and produce:
    - new event (with RNG outcome captured if applicable),
    - new marking (or a snapshot candidate),
    - head move to new node.[^1][^5]
- Enforce invariants:
    - singleton world token,
    - one token per character,
    - item ownership,
    - join atomicity,
    - “jump target is ancestor”.[^8][^1]


### Data access layer (Repositories) ??

- `GameRepo`: head pointer load/update with optimistic concurrency.[^8]
- `EventRepo`: append event, fetch ancestor chain, fetch events from snapshot→head.[^4]
- `SnapshotRepo`: load nearest snapshot at/before node; write periodic snapshots.[^5]


### Persistence (Postgres)

Store:

- `games(game_id, created_at, ...)`
- `heads(game_id, head_node_id, head_version)` (optimistic concurrency gate)[^8]
- `events(game_id, node_id, parent_id, type, payload_json, created_at, ...)` (immutable tree)[^1]
- `snapshots(game_id, node_id, marking_json, created_at, ...)` (optimization)[^5]
- `outbox(id, topic, payload_json, created_at, published_at, ...)` for reliable pub/sub emission.[^3]


### Real-time distribution (Redis pub/sub)  (confirmed viable if backend supports)

Use Redis pub/sub to propagate `GameStateChanged` / `HeadMoved` across horizontally scaled API instances so each can push to its WebSocket clients.[^9][^2]
Redis delivery is not authoritative; clients must refetch from Postgres-derived projections when they detect gaps.[^10][^2]

## Control flow (write + read paths)

### Attempt transition (choice/event) ???

1) API receives command with idempotency key and expected `head_version`.[^8]
2) Service reconstructs marking at current head and validates transition enabledness.[^7][^1]
3) Service computes RNG outcome for NPC movement if needed and embeds it into the event payload.[^7]
4) In one Postgres transaction:
    - append new `events` row with `parent_id = head_node_id`,
    - update `heads` to new node with CAS on `head_version`,
    - optionally write snapshot,
    - insert outbox message.[^3][^8]
5) Outbox publisher emits to Redis; WS pushes update.[^2][^3]

### Undo / jump (rewind)  STILL BEING DESIGNED _ THIS IS FLAWED

1) API receives `undo` or `jump(node_id)` with expected `head_version`.[^8]
2) Service verifies node is ancestor of current head (for jump) and updates `heads` only (no new events).[^8]
3) Insert outbox `HeadMoved` so clients update their view and refetch state for the new head.[^3][^4]

### Read path (state + timeline) STILL BEING DESIGNED _ THIS IS POSSIBLY FLAWED

- `GET /state` resolves marking for current head via snapshot+replay and returns a UI projection plus enabled transitions.[^5][^4]
- `GET /timeline` returns only the ancestor chain; it must not return siblings/children, ensuring abandoned branches remain hidden.[^4]


## Design patterns (explicit)

- **Event Sourcing** for state as an event stream (now a tree) and full history.[^6][^1]
- **Projection / Read Model** to serve fast, purpose-built views of current state and enabled choices.[^7][^4]
- **Snapshotting** to avoid replay-from-origin cost as event history grows.[^5]
- **Repository** for storage boundary and testability.[^4]
- **Command** for transition attempts and head moves, with idempotency + expected-version preconditions.[^8]
- **Transactional Outbox** to avoid dual-write inconsistencies between Postgres commits and Redis/WebSocket notifications.[^3]
- **Pub/Sub (Observer)** for real-time fanout via Redis to WS clients.[^10][^2]

the next decision is whether to materialize a separate “current projection table” in Postgres (incremental projection) versus always computing projection on demand from snapshots+replay (simpler, often enough for MVP).[^5]

<div align="center">⁂</div>

[^1]: https://learn.microsoft.com/en-us/azure/architecture/patterns/event-sourcing

[^2]: https://blog.devops.dev/distributed-real-time-communication-scaling-websockets-with-redis-pub-sub-9a7db4f81cd0

[^3]: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html

[^4]: https://event-driven.io/en/projections_and_read_models_in_event_driven_architecture/

[^5]: https://www.kurrent.io/blog/snapshots-in-event-sourcing

[^6]: https://microservices.io/patterns/data/event-sourcing.html

[^7]: https://docs.eventsourcingdb.io/best-practices/designing-read-models/

[^8]: https://event-driven.io/en/optimistic_concurrency_for_pessimistic_times/

[^9]: https://leapcell.io/blog/scaling-websocket-services-with-redis-pub-sub-in-node-js

[^10]: https://redis.io/docs/latest/develop/pubsub/

[^11]: https://www.kurrent.io/blog/live-projections-for-read-models-with-event-sourcing-and-cqrs

[^12]: https://martendb.io/events/learning.html

[^13]: https://www.reddit.com/r/softwarearchitecture/comments/1mmn3eb/transactional_outbox_pattern_processing_design/

[^14]: https://github.com/omkargade04/Scalable-Websocket-Server

[^15]: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/event-sourcing.html

[^16]: https://chairnerd.seatgeek.com/transactional-outbox-pattern/

[^17]: https://www.geeksforgeeks.org/system-design/event-sourcing-pattern/

[^18]: https://dev.to/msdousti/postgresql-outbox-pattern-revamped-part-1-3lai

[^19]: https://dev.to/hexshift/scaling-websocket-connections-with-redis-pubsub-for-multi-instance-nodejs-applications-3pib

[^20]: https://www.youtube.com/watch?v=bTRjO6JK4Ws

[^21]: https://event-driven.io/en/push_based_outbox_pattern_with_postgres_logical_replication/

[^22]: https://ably.com/blog/scaling-pub-sub-with-websockets-and-redis

[^23]: https://www.npmjs.com/package/pg-transactional-outbox

