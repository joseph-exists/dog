***

# Minimog Integration Plan (V1) for TinyFoot

## Steel Thread: Multi-User, Multi-Agent Collaborative Story Chat

**Created:** December 11, 2025.[^3]
**Purpose:** Deliver Minimog’s multi-user, multi-agent conversational capabilities inside TinyFoot’s story-creation experience, with strong consistency, persistence, and real-time collaboration.[^5][^1]

***

## Strategic framing

### Vision

Transform TinyFoot into an interactive story creation platform where multiple authors collaborate with AI agents in shared rooms during story development.[^1][^3]

### Strategic value

- Authors get real-time, story-aware assistance while editing and can collaborate with other authors in the same space.[^3][^5][^1]
- The system gains a durable conversation history that can be replayed, audited, and used for improved context building over time.[^1]


### Steel thread definition

Multiple authors join a shared room attached to a story, invite the StoryAdvisor agent, exchange messages, and all participants see updates in real time while the conversation persists across reloads and sessions.[^2][^5][^1]

This proves event sourcing with projections, room-based authorization, agents as first-class room participants, and real-time streaming readiness.[^5][^1]

***

## Architectural framing

### Target architecture (major components)

- Frontend (React) adds a chat/room UI integrated into the Story Editor experience and can later support streaming tokens and interactive UI elements.[^3][^5][^1]
- Backend (FastAPI) provides room management, participant management, message/event write paths, agent execution, and real-time gateways.[^5][^1][^3]
- PostgreSQL is the durable system of record for append-only room events, with transactional projections for fast queries and read-after-write consistency.[^1]
- Redis provides ephemeral pub/sub fan-out for WebSocket streaming and multi-worker coordination.[^3][^1]


### Core architectural patterns

- Event sourcing is the system of record: every state change is an immutable event in a single per-room ordered log.[^1]
- Multi-user rooms are the primary unit of collaboration, and both humans and agents are participants with equal standing in the event log.[^5][^1]
- CQRS is implemented with transactional projections updated in the same database transaction as the event write to guarantee strong read-after-write behavior.[^1]
- WebSocket streaming uses Redis pub/sub to distribute updates to all connected clients and supports streaming agent output.[^3][^1]
- Stateless multi-worker operation is required, with no reliance on in-process shared state for correctness.[^1]


### Technology constraints (baseline)

- PostgreSQL (>= 15), Python 3.11+ with FastAPI, Redis (>= 7), and PydanticAI for agent runtime and streaming.[^1]
- Async-first I/O is mandatory for DB, Redis, HTTP, and LLM calls to preserve multi-worker responsiveness.[^1]
- JWT authentication is used for HTTP and WebSocket handshake authentication, and authorization is enforced per room membership.[^1]

***

## Domain model \& storage

### System of record: room_events (append-only)

All business-relevant writes emit an event to `room_events`, and events are never updated or deleted.[^4][^5][^1]
Events in a room are strictly ordered by a monotonically increasing per-room sequence, and clients must not assume sequences are consecutive.[^1]

**Event types (minimum viable set):**

- `room.created`, `room.updated` for room lifecycle.[^5]
- `participant.joined`, `participant.left`, `participant.role_changed` for membership and authorization.[^5]
- `room_message.user`, `room_message.agent` for conversation content (both are first-class).[^4][^5]
- `tool.start`, `tool.end`, and `agent.handoff` are reserved for advanced agent operations and observability.[^4]


### Projections (transactionally maintained)

Projections are query-optimized tables derived from events and updated in the same transaction as the event insert.[^1]
Recommended projections for V1: `rooms`, `room_participants`, and `room_messages`.[^5][^1]

### Required tables (conceptual schema)

- `rooms` holds room metadata, optional `story_id`, and `last_activity` for ordering in room lists.[^5][^1]
- `room_participants` is the foundation of multi-user operation and contains both user and agent participants with `participant_type`, `role`, and active flags.[^5][^1]
- `room_events` is the immutable event log keyed by `room_id` + `room_sequence`, with indexes supporting replay.[^5][^1]
- `room_messages` is the message projection keyed by room, with sender attribution (`sender_type`, `agent_name`) and optional interactive payload fields (e.g., `button_options`).[^5]

***

## API \& service contracts

### Backend services (logical responsibilities)

- Identity/Auth service validates JWT for HTTP requests and WebSocket handshakes.[^1]
- Room Management handles room creation, listing, participant management, and room-scoped authorization checks.[^5][^1]
- Event Emitter appends immutable events and updates projections transactionally.[^4][^1]
- Context Provider assembles room-aware agent context (story outline + last N messages + participant metadata as needed) with strict size limits.[^4][^1]
- Agent Runner executes PydanticAI agents with dependency-injected context, emits `room_message.agent` events, and optionally streams tokens.[^4][^1]


### REST endpoints (Phase 1–3 baseline)

Room operations:

- `POST /rooms` create a room (optionally with initial agents), and creator becomes owner.[^5]
- `GET /rooms` list rooms where the user is an active participant (ordered by last activity).[^1][^5]
- `GET /rooms/{room_id}` fetch room details only if the user is an active participant.[^5][^1]
- `POST /rooms/{room_id}/participants` add users or agents (owner-only).[^5]
- `GET /rooms/{room_id}/participants` list room participants (participant-only).[^5]

Messaging operations:

- `POST /rooms/{room_id}/room_messages` emits `room_message.user`, runs agent(s) as configured, and persists `message.agent` responses as events.[^4][^1][^5]
- `GET /rooms/{room_id}/room_messages` returns message history from the `room_messages` projection with pagination.[^1][^5]

Agent operations (optional companion API):

- `POST /agents/{agent_name}` executes a registered agent via AG-UI adapter for standardized UI integration.[^4]
- `GET /agents` lists available agents and their metadata from an agent registry.[^4]


### WebSocket (Phase 4)

A room-scoped WebSocket endpoint supports real-time fan-out and token streaming using Redis pub/sub.[^3][^1]
Reconnection must support sequence-based replay to mitigate pub/sub message loss and multi-worker delivery gaps.[^1]

***

## Implementation framing (vertical slices)

Each phase delivers end-to-end value and remains deployable independently.[^3][^1]

### Phase 0: Infrastructure (2–3 days)

**Goal:** Introduce Redis and verify database capabilities without breaking existing TinyFoot features.[^2][^3]
**Deliverables:** Redis in docker-compose, connection singleton, health checks, and pgvector verification.[^2][^3]
**Success criteria:** Existing tests pass, the stack boots cleanly, and the backend can connect to Redis.[^2][^3]

### Phase 1: Event sourcing + room management (4–5 days)

**Goal:** Implement rooms, participants, an append-only room event log, and transactional projections.[^1][^5]
**Deliverables:** `rooms`, `room_participants`, `room_events`, `messages` projections; RoomManager; participant APIs; and event emitter utilities.[^5][^1]
**Success criteria:** Events are immutable, projections update transactionally, and room authorization is enforced on every room operation.[^4][^1][^5]

### Phase 2: Multi-user agent integration (5–6 days)

**Goal:** Make agents first-class room participants and run them with room-aware context.[^1][^5]
**Deliverables:** StoryAdvisor agent with tools, agent registry, context provider, agent runner emitting `room_message.agent`, and support for multiple agents in one room.[^4][^5][^1]
**Success criteria:** Agent responses are visible to all participants, include story-aware context, and are persisted and replayable from events.[^5][^1]

### Phase 3: Frontend multi-user room UI (4–5 days)

**Goal:** Provide a room-centric UI embedded in the Story Editor with participant visibility and sender attribution.[^3][^5]
**Deliverables:** room list, room creation flow, participant list, message list with attribution, invite UI for users/agents, and OpenAPI client regeneration.[^2][^3][^5]
**Success criteria:** UI loads quickly, supports room switching, displays all participants and their messages correctly, and persists history across reloads.[^3][^1]

### Phase 4: Real-time streaming (5–6 days)

**Goal:** Stream events and agent tokens over WebSocket and keep all participants synchronized.[^3][^1]
**Deliverables:** WebSocket endpoint, Redis pub/sub fan-out, streaming agent execution, reconnection + replay behavior, and load testing for concurrency.[^2][^3][^1]
**Success criteria:** Token streaming latency is acceptable, reconnect is correct under worker failures, and clients tolerate non-consecutive sequences.[^1]

### Phase 5: Advanced multi-agent (optional expansion)

**Goal:** Add richer agent collaboration features and deeper observability.[^4][^1]
**Deliverables:** `agent.handoff`, tool execution events, richer agent tool tracking, and more advanced coordination patterns.[^4][^1]
**Success criteria:** Tool usage and handoffs are auditable via events and can be replayed into projections for analytics.[^4][^1]

***

## Quality, security, and validation gates

### Non-negotiable guardrails

- All I/O is async-first, and blocking operations must be isolated to avoid event-loop stalls.[^1]
- Authorization checks are required before every room read/write based on active membership in `room_participants`.[^5][^1]
- Event writes and projection updates must succeed or fail together in the same DB transaction to prevent partial state.[^4][^1]
- Agent context size is capped (message history window + story outline limits) to protect latency and LLM context constraints.[^4][^1]
- WebSocket clients must replay by sequence and must not assume sequences are consecutive (gaps are valid).[^1]


### Testing requirements (minimum)

- Event replay tests prove projections can be rebuilt from `room_events`.[^4][^1]
- Multi-worker concurrency tests validate no duplicate per-room sequences and no lost committed events.[^1]
- Multi-user scenario tests validate multiple humans + multiple agents in one room with correct visibility and authorization enforcement.[^5][^1]

***

## Rollout, risks, and operational plan

### Risk mitigation (high-impact areas)

- WebSocket complexity is deferred until the REST-driven room + agent path is correct and well-tested.[^3][^1]
- Redis unavailability should degrade gracefully (REST polling / non-streaming operation) while preserving correctness through PostgreSQL as the system of record.[^3][^1]
- Database growth is managed via operational practices such as partitioning the event log as volume increases.[^3][^1]


### Definition of done (steel thread)

- Authors can create/join a room from the Story Editor context and invite StoryAdvisor.[^3][^5]
- Messages from users and agents persist across reloads and can be queried via projections.[^5][^1]
- All participants see all messages correctly attributed, and authorization prevents non-participants from reading or writing.[^5][^1]
- Automated tests cover replay, authorization, agent execution, and multi-worker sequence correctness.[^4][^1]

---


[^1]: TechSpecTinyfoot-Minimog.md

[^2]: SteelThreadReference.md

[^3]: IntegrationPlan.md

[^4]: Agent-Event-RULES.md

[^5]: IntegrationAddendum.md

