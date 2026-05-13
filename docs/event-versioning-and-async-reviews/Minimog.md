# Multi-User Multi-AI Chatroom System - Technical Specification

**Version:** 0.8
**Document Type:** REFERENCE
**Status:** Final Review Prior to Implementation
**Last Updated:** December 11, 2025
**Tech Stack:** PydanticAI, FastAPI, AG-UI, Postgres, Redis, Docker

***

## 0. Document Structure and Cross-Reference Guide

This specification is designed as an **interdependent system** where each section builds upon and validates previous sections. All cross-references use explicit notation to enable automated validation.

### Cross-Reference Notation

- **AP\#** - Architectural Pattern
- **AC\#.\#** - Assumption/Constraint
- **E\#** - Event Type
- **P\#** - Projection (Read Model)
- **S\#** - Service
- **R\#.\#** - Requirement
- **C\#.\#** - Contract
- **DG\#.\#** - Design Guardrail

***

## 1. Architectural Patterns

### AP1. Event Sourcing as System of Record

**Pattern Type:** Event Sourcing + Append-Only Log

**Description:** All state changes are recorded as immutable events in a single `room_events` table in Postgres. This is the only authoritative source of truth. All queryable tables are projections derived from events.

**Implications:**

- **Constraint:** "If it's not in the log, it didn't happen" - no business logic may mutate state outside event writes
- **Impact on consistency:** Strong consistency within single room via ordered event log; projections updated transactionally
- **Impact on services:** Services emit events, not mutate entities; replay capability is inherent
- **Audit:** Complete audit trail with no additional logging infrastructure

**Contradicts:** Traditional CRUD patterns, direct table mutations

***

### AP2. PydanticAI-Native Agent Runtime

**Pattern Type:** Agent-as-Runtime (vs External Orchestration)

**Description:** PydanticAI's `agent.run()` loop is the execution engine. Tools are dependency-injected functions that emit events as side effects during execution. The framework handles multi-turn reasoning, retries, and error correction natively.

**Implications:**

- **Constraint:** No manual step orchestration - agent decides tool invocation order
- **Impact on concurrency:** Each agent run is an async task; tools must be async-safe
- **Impact on observability:** Tool execution events are logged to `room_events` for step tracking
- **Multi-agent handoff:** Implemented as a special tool that triggers a new agent invocation

**Contradicts:** Step-by-step orchestration, synchronous blocking tool execution

***

### AP3. CQRS with Transactional Projections

**Pattern Type:** Command Query Responsibility Segregation

**Description:** Write path (commands) appends to `room_events`. Read path (queries) uses optimized projection tables (`messages`, `steps`, `room_participants`). Projections are updated in the **same transaction** as event writes for strong consistency.

**Implications:**

- **Constraint:** All reads must use projections, never parse event log for business queries
- **Impact on performance:** Read-optimized indexes on projections, write path has transaction overhead
- **Impact on deployment:** Projection tables must be created/migrated alongside event schema changes

**Contradicts:** Eventual consistency patterns, separate write/read databases

***

### AP4. AG-UI Protocol for Real-Time Interaction

**Pattern Type:** Standardized Streaming Protocol

**Description:** AG-UI JSON-RPC protocol defines the client-server contract for room sessions, message streaming, and tool interactions. PydanticAI tool schemas are mapped to AG-UI tool definitions.

**Implications:**

- **Constraint:** WebSocket required for bidirectional streaming; REST as fallback for room management
- **Impact on UI:** Clients can be auto-generated from AG-UI schemas
- **Impact on tool design:** All PydanticAI tools must have JSON-serializable schemas

**Contradicts:** Custom WebSocket protocols, GraphQL subscriptions

***

### AP5. Horizontal Scalability via Stateless Workers

**Pattern Type:** Shared-Nothing Multi-Worker

**Description:** Multiple FastAPI worker processes coordinate via Postgres (for sequence generation) and Redis (for ephemeral event streaming). No in-process state shared between workers.

**Implications:**

- **Constraint:** All session state reconstructed from Postgres on reconnection
- **Impact on deployment:** Requires Redis for pub/sub, Postgres connection pooling per worker
- **Impact on testing:** Must test worker failover scenarios

**Contradicts:** Single-process in-memory caching, sticky sessions

***

## 2. Assumptions and Constraints

### 2.1 Technology Stack

**Relates to:** AP1, AP2, AP3, AP4, AP5


| Component | Technology Choice | Version Constraint | Justification | Risk Reference |
| :-- | :-- | :-- | :-- | :-- |
| Primary Database | PostgreSQL | >=15.0 | Event log durability, JSONB, advisory locks for sequences | AC3.1 |
| Analytical Engine | pg_duckdb extension | >=0.0.1 | In-process analytics without ETL, property graph queries | AC4.2 |
| Cache/Pub-Sub | Redis | >=7.0 | Multi-worker ephemeral streaming coordination | AC2.2 |
| Application Runtime | Python + FastAPI | Python 3.11+, FastAPI 0.104+ | PydanticAI compatibility, async-native | AC2.3 |
| Agent Framework | PydanticAI | >=0.0.9 | Native streaming, tool injection, type safety | AC2.4 |
| WebSocket Protocol | AG-UI | Latest spec | Standardized multi-agent interaction | AC5.1 |
| Container Runtime | Docker + Compose | Docker 24+ | Reproducible dev/prod environments | AC2.1 |

**Validation Questions:**

- **Are these compatible?** YES - all are async-compatible, Python-native or protocol-agnostic
- **Do they support AP1-AP5?** YES - Postgres supports event sourcing, Redis enables multi-worker, AG-UI maps to PydanticAI
- **Operational expertise?** Postgres admin, Redis ops, Docker orchestration

***

### 2.2 Deployment Constraints

**Relates to:** AP5

**AC2.1 Docker Compose Deployment**

- **Statement:** Day 1 deployment uses Docker Compose with services: `postgres`, `redis`, `fastapi` (replicas: 4), `traefik` (load balancer)
- **Impacts:** S1-S5 (all services run in FastAPI workers), deployment scripts
- **Validation:** `docker-compose up` brings up full stack

**AC2.2 Multi-Worker Coordination**

- **Statement:** 4+ FastAPI workers run concurrently; Redis is required for ephemeral streaming; Postgres advisory locks prevent sequence collisions
- **Impacts:** S4 (agent execution), S5 (UI Gateway), E1-E5 (sequence generation)
- **Validation:** Load test with 4 workers, verify no duplicate `room_sequence` values

**AC2.3 Async-First Concurrency**

- **Statement:** All I/O (Postgres, Redis, HTTP, agent calls) must be async/await; blocking calls wrapped in `asyncio.to_thread()`
- **Impacts:** All services, DG2.1
- **Validation:** No `time.sleep()`, `requests.get()`, or sync DB drivers in codebase

***

### 2.3 Concurrency and Consistency Constraints

**Relates to:** AP1, AP3, AP5

**AC3.1 Event Ordering Guarantee**

- **Statement:** Events within a single room are strictly ordered by `room_sequence` (monotonic, sparse); events across rooms are unordered
- **Impacts:** E1-E5, P1-P5, R3.1, R3.2
- **Chosen Strategy:** Postgres `SELECT nextval()` with advisory locks during multi-worker contention
- **Validation:** Concurrent message sends to same room never produce duplicate sequences

**AC3.2 Projection Update Semantics**

- **Statement:** Projection tables (P1-P5) are updated in the **same transaction** as event log writes for strong consistency
- **Impacts:** S3, S4, DG1.2
- **Validation:** Query projection immediately after event write, verify data is visible

**AC3.3 Read-After-Write Consistency**

- **Statement:** Clients reading from projections immediately after writes see their own writes (within same Postgres transaction)
- **Impacts:** C2.2, C3.1, R3.3
- **Validation:** POST message → GET messages returns the new message

***

### 2.4 Performance and Scale Assumptions

**Relates to:** AP5


| Metric | Assumed Load | Design Ceiling | Degradation Behavior |
| :-- | :-- | :-- | :-- |
| Concurrent Users | 500 | 2,000 | Queue requests, return 503 after timeout |
| Writes/Second (per room) | 10 | 50 | Backpressure via Redis slow consumer detection |
| Read Latency (p95) | <100ms | <500ms | Serve stale data from projection cache |
| Event Log Growth | 10K events/day | 10M events | Partition `room_events` by month after 1M rows |
| Analytics Query Timeout | 5s | 30s | Cancel long-running pg_duckdb queries |

**AC4.1 Connection Pool Sizing**

- **Statement:** Each FastAPI worker maintains 10 Postgres connections (4 workers = 40 total)
- **Impacts:** Postgres `max_connections` must be >=50
- **Validation:** Monitor connection usage under load

**AC4.2 Analytics Isolation**

- **Statement:** pg_duckdb queries run in separate connection pool with `statement_timeout=5s` to prevent blocking writes
- **Impacts:** S4 analytics tools, DG2.3
- **Validation:** Long query does not block message writes

***

### 2.5 Security and Authorization Constraints

**Relates to:** AP4

**AC5.1 JWT-Based Authentication**

- **Statement:** All requests include JWT in `Authorization: Bearer <token>` header; FastAPI dependency validates and extracts `user_id`
- **Impacts:** S1, all API contracts C1-C3
- **Enforcement Point:** FastAPI middleware before route handlers
- **Validation:** Request without JWT returns 401; expired JWT returns 401

**AC5.2 Room-Level Authorization**

- **Statement:** Users can only read/write messages in rooms where they are active participants (`room_participants.is_active=true`)
- **Impacts:** S2, S3, S5, R1.3, DG3.1
- **Enforcement Point:** Before any room operation, query `room_participants`
- **Validation:** User not in room receives 403 on message send

**AC5.3 No Row-Level Security (Yet)**

- **Statement:** Authorization is enforced in application code, not Postgres RLS, for simplicity
- **Impacts:** All services must check authorization; no defense if service is compromised
- **Future:** Consider RLS for defense-in-depth

***

## 3. Domain Model

### 3.1 Events (Canonical Log)

#### E1. room_events (Event Log Table)

**Owner Service:** All services write events; S3 provides helper functions
**Pattern Context:** AP1 (Event Sourcing)
**Related Constraints:** AC3.1, AC3.2

**Purpose:** Immutable, append-only log of every state change in the system. This is the source of truth.



```sql
room_events:
    event_id        -- Global monotonic ordering
    room_id         -- Partition key
    room_sequence  -- Per-room monotonic sequence (sparse gaps allowed)
    event_type     -- 'message.user', 'message.assistant', 'step.start', etc.
    payload          -- Event-specific data

                             Table "public.room_events"
       Column        |            Type             | Collation | Nullable | Default
---------------------+-----------------------------+-----------+----------+---------
 event_type          | character varying(50)       |           | not null |
 payload             | json                        |           | not null |
 event_id            | uuid                        |           | not null |
 room_id             | uuid                        |           | not null |
 room_sequence       | integer                     |           | not null |
 created_at          | timestamp without time zone |           | not null |
 enrichment_metadata | json                        |           |          |
Indexes:
    "room_events_pkey" PRIMARY KEY, btree (event_id)
    "ix_room_events_created_at" btree (created_at)
    "ix_room_events_room_id" btree (room_id)
Foreign-key constraints:
    "room_events_room_id_fkey" FOREIGN KEY (room_id) REFERENCES rooms(room_id)
```


**Event Types:**

## TODO: EVALUATION AGAINST IMPLEMENTATION AND DESIGN REQUIRED

| Event Type | Payload Schema | Trigger | Projections Updated |
| :-- | :-- | :-- | :-- |
| `room.created` | `{room_id, title, created_by, is_group}` | User creates room | P2 (rooms) |
| `participant.joined` | `{room_id, user_id, role, invited_by}` | User joins room | P3 (room_participants) |
| `participant.left` | `{room_id, user_id}` | User leaves room | P3 (room_participants) |
| `message.user` | `{message_id, sender_id, content, metadata}` | User sends message | P4 (messages) |
| `message.assistant` | `{message_id, agent_id, content, button_options}` | Agent completes turn | P4 (messages) |
| `step.start` | `{step_id, message_id, agent_id, tool_name, input}` | Tool execution begins | P5 (steps) |
| `step.end` | `{step_id, output, duration_ms, status}` | Tool execution finishes | P5 (steps) |
| `agent.handoff` | `{from_agent_id, to_agent_id, message_id, context}` | Agent transfers conversation | P6 (agent_handoffs) |
| `system.error` | `{error_type, message_id, stack_trace}` | Unrecoverable error | None (logging only) |

**Lifecycle:**

- **Created by:** Any service via `emit_event(room_id, event_type, payload)` helper (S3)
- **Modified by:** NEVER (immutable)
- **Deleted by:** 
## TODO: define delete/purge mechanism

**Sequence Generation (AC3.1):**

## TODO: Extract actual sequence generation pattern from implementation and update this design

```python
# In multi-worker environment
async def next_room_sequence(room_id: UUID) -> int:
    async with db.transaction():
        # Advisory lock prevents collisions
        await db.execute("SELECT pg_advisory_xact_lock($1)", hash(room_id))
        result = await db.fetchval(
            "SELECT COALESCE(MAX(room_sequence), 0) + 1 FROM room_events WHERE room_id = $1",
            room_id
        )
        return result
```


***

### 3.2 Projections (Read Models)

#### P1. users

**Owner Service:** S1 (Identity \& Auth)
**Pattern Context:** AP3 (CQRS)
**Update Semantics:** Synchronous (no events for user CRUD - external system)

**Purpose:** User identity and profile information

**Schema:**

```

                            Table "public.user"
     Column      |          Type          | Collation | Nullable | Default
-----------------+------------------------+-----------+----------+---------
 email           | character varying(255) |           | not null |
 is_active       | boolean                |           | not null |
 is_superuser    | boolean                |           | not null |
 full_name       | character varying(255) |           |          |
 hashed_password | character varying      |           | not null |
 id              | uuid                   |           | not null |
Indexes:
    "user_pkey" PRIMARY KEY, btree (id)
    "ix_user_email" UNIQUE, btree (email)
```

**Lifecycle:**

- **Created by:** S1 on first JWT validation (upsert pattern)
- **Modified by:** S1 via admin API
- **Deleted/Archived:** Soft delete via `is_active=false`

***

#### P2. rooms

**Source Events:** E1 (`room.created`)
**Owner Service:** S2 (Room Management)
**Update Semantics:** Transactional with event write (AC3.2)

**Purpose:** Queryable room metadata for listing and display

**Schema:**

```sql
                             Table "public.rooms"
    Column     |            Type             | Collation | Nullable | Default
---------------+-----------------------------+-----------+----------+---------
 title         | character varying(255)      |           |          |
 story_id      | uuid                        |           |          |
 room_id       | uuid                        |           | not null |
 creator_id    | uuid                        |           | not null |
 created_at    | timestamp without time zone |           | not null |
 last_activity | timestamp without time zone |           | not null |
Indexes:
    "rooms_pkey" PRIMARY KEY, btree (room_id)
Foreign-key constraints:
    "rooms_creator_id_fkey" FOREIGN KEY (creator_id) REFERENCES "user"(id)
    "rooms_story_id_fkey" FOREIGN KEY (story_id) REFERENCES story(id)
Referenced by:
    TABLE "room_events" CONSTRAINT "room_events_room_id_fkey" FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    TABLE "room_messages" CONSTRAINT "room_messages_room_id_fkey" FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    TABLE "room_participants" CONSTRAINT "room_participants_room_id_fkey" FOREIGN KEY (room_id) REFERENCES rooms(room_id)
```
#### NOTE: may need enrichment_metadata JSON object at some point
#### NOTE: may need CREATE INDEX idx_rooms_last_activity ON rooms (last_activity DESC) and idx_rooms_created_by ... 
#### NOTE: do we need the is_group column?  need to understand what is_group is for (what was that about??)

**Projection Logic:**

```python
async def on_room_created_event(event: Event):
    await db.execute("""
        INSERT INTO rooms (room_id, title, created_by, is_group, created_at)
        VALUES ($1, $2, $3, $4, $5)
    """, event.payload['room_id'], event.payload['title'], 
         event.payload['created_by'], event.payload['is_group'], event.created_at)
```


***

#### P3. room_participants

**Source Events:** E1 (`participant.joined`, `participant.left`)
**Owner Service:** S2 (Room Management)
**Update Semantics:** Transactional with event write

**Purpose:** Authorization queries - "Is user X in room Y?"

**Schema: PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**

```sql
CREATE TABLE room_participants (
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    role VARCHAR(20) NOT NULL DEFAULT 'member',   -- 'owner' | 'member' | 'guest'
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    
    PRIMARY KEY (room_id, user_id)
);

CREATE INDEX idx_participants_user_rooms ON room_participants (user_id, is_active) 
    WHERE is_active = true;
```

**Projection Logic: PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**

```python
async def on_participant_joined(event: Event):
    await db.execute("""
        INSERT INTO room_participants (room_id, user_id, role, joined_at)
        VALUES ($1, $2, $3, $4)
        ON CONFLICT (room_id, user_id) DO UPDATE SET is_active=true, left_at=NULL
    """, event.payload['room_id'], event.payload['user_id'], 
         event.payload['role'], event.created_at)

async def on_participant_left(event: Event):
    await db.execute("""
        UPDATE room_participants SET is_active=false, left_at=$3
        WHERE room_id=$1 AND user_id=$2
    """, event.payload['room_id'], event.payload['user_id'], event.created_at)
```


***

#### P4. messages

**Source Events:** E1 (`message.user`, `message.assistant`)
**Owner Service:** S3 (Chat History)
**Update Semantics:** Transactional with event write

**Purpose:** Fast chronological message retrieval for chat UI

**Schema:PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**


```sql
CREATE TABLE messages (
    message_id BIGINT PRIMARY KEY,                -- From event payload
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    sender_id UUID REFERENCES users(user_id),      -- NULL for assistant messages
    agent_id VARCHAR(50),                          -- e.g., 'customer_support_agent'
    content TEXT NOT NULL,
    button_options JSONB,                          -- [{label, value, style}] for AG-UI
    metadata JSONB DEFAULT '{}',                   -- Extensible (eval scores, etc.)
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_room_time ON messages (room_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages (sender_id);
```

**Button Options Schema (AG-UI compatible):**

```json
[
  {"label": "Yes, proceed", "value": "confirm_action", "style": "primary"},
  {"label": "Cancel", "value": "cancel_action", "style": "secondary"}
]
```


***

#### P5. steps

**Source Events:** E1 (`step.start`, `step.end`)
**Owner Service:** S4 (Agent Runner)
**Update Semantics:** Two-phase - insert on `step.start`, update on `step.end`

**Purpose:** Track tool execution for observability and analytics

**Schema: PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**

```sql
CREATE TABLE steps (
    step_id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    message_id BIGINT NOT NULL REFERENCES messages(message_id),
    agent_id VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,                   -- 'running' | 'completed' | 'failed'
    input JSONB NOT NULL,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER
);

CREATE INDEX idx_steps_message ON steps (message_id);
CREATE INDEX idx_steps_room_time ON steps (room_id, started_at DESC);
CREATE INDEX idx_steps_status ON steps (status) WHERE status = 'running';
```

**Projection Logic:**

```python
async def on_step_start(event: Event):
    await db.execute("""
        INSERT INTO steps (step_id, room_id, message_id, agent_id, tool_name, 
                          status, input, started_at)
        VALUES ($1, $2, $3, $4, $5, 'running', $6, $7)
    """, event.payload['step_id'], event.room_id, event.payload['message_id'],
         event.payload['agent_id'], event.payload['tool_name'], 
         event.payload['input'], event.created_at)

async def on_step_end(event: Event):
    await db.execute("""
        UPDATE steps SET status=$2, output=$3, finished_at=$4, duration_ms=$5
        WHERE step_id=$1
    """, event.payload['step_id'], event.payload['status'], 
         event.payload['output'], event.created_at, event.payload['duration_ms'])
```


***

#### P6. agent_handoffs

**Source Events:** E1 (`agent.handoff`)
**Owner Service:** S4 (Agent Runner)
**Update Semantics:** Transactional with event write

**Purpose:** Track multi-agent conversations for analytics

**Schema: PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**


```sql
CREATE TABLE agent_handoffs (
    handoff_id UUID PRIMARY KEY,
    from_agent_id VARCHAR(50) NOT NULL,
    to_agent_id VARCHAR(50) NOT NULL,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    message_id BIGINT NOT NULL REFERENCES messages(message_id),
    context JSONB NOT NULL,                        -- Handoff reason, user intent, etc.
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_handoffs_room ON agent_handoffs (room_id, created_at DESC);
```


***

## 4. Services and Boundaries

### Service Dependency Graph

```
        ┌─────────────────────────────────────────┐
        │  S5: UI Gateway (AG-UI WebSocket)      │
        └──────────────┬──────────────────────────┘
                       │
        ┌──────────────┴───────────────┬──────────────────┐
        │                              │                  │
        ▼                              ▼                  ▼
  ┌──────────┐              ┌────────────────┐    ┌─────────────┐
  │ S2: Room │◄─────────────│ S4: Agent      │    │ S3: Chat    │
  │ Mgmt     │              │ Runner         │    │ History     │
  └────┬─────┘              └───────┬────────┘    └──────┬──────┘
       │                            │                     │
       │                    ┌───────┴─────────────────────┘
       │                    │
       ▼                    ▼
  ┌────────────────────────────────┐
  │ S1: Identity & Authorization   │
  └────────────────────────────────┘
```

**Validation:** No circular dependencies ✓

***

### S1. Identity \& Authorization Service

**Pattern Context:** AP4 (JWT), AP5 (Stateless)
**Related Constraints:** AC5.1, AC5.2

**Responsibilities:**

- Validate JWT tokens and extract `user_id` from claims
- Upsert user records on first authentication
- Provide authorization check: "Is user X an active participant in room Y?"

**Owns Domain Objects:**

- P1 (users) - Create on JWT validation, soft delete

**Depends On Services:**

- None (leaf service)

**Provides Contracts To:**

- S2, S3, S4, S5 - C1.1 (Authorization Check)
- External API - C2.1 (User Profile)

**State Management:**

- Users stored in Postgres `users` table
- No caching (queries are fast with index on `external_id`)

**Concurrency Model:**

- Stateless; safe for multi-worker (AC2.2)
- User upsert uses `ON CONFLICT DO UPDATE` for idempotency

**Authorization Model:**

- This IS the authorization service
- Enforces AC5.2 via `check_room_access(user_id, room_id)` helper

**Implementation: PENDING REVIEW PRIOR TO ADDING TO CODEBASE - NEEDS WORK - NOT APPROVED**

```python
# FastAPI dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = jwt.decode(token, SECRET_KEY, algorithms=["RS256"])
    external_id = payload["sub"]
    
    # Upsert user
    user = await db.fetchrow("""
        INSERT INTO users (user_id, external_id, email, display_name)
        VALUES (gen_random_uuid(), $1, $2, $3)
        ON CONFLICT (external_id) DO UPDATE SET email=EXCLUDED.email
        RETURNING *
    """, external_id, payload["email"], payload.get("name", "User"))
    
    return User(**user)

async def check_room_access(user_id: UUID, room_id: UUID) -> bool:
    exists = await db.fetchval("""
        SELECT 1 FROM room_participants 
        WHERE room_id=$1 AND user_id=$2 AND is_active=true
    """, room_id, user_id)
    return exists is not None
```


***

### S2. Room Management Service

**Pattern Context:** AP1 (Event Sourcing), AP3 (CQRS)
**Related Constraints:** AC3.2, AC5.2

**Responsibilities:**

- Create rooms and emit `room.created` events
- Add/remove participants and emit `participant.joined/left` events
- List rooms for a user (query P2, P3)

**Owns Domain Objects:**

- P2 (rooms) - Manage lifecycle
- P3 (room_participants) - Manage membership

**Depends On Services:**

- S1 - User identity validation, authorization checks

**Provides Contracts To:**

- S3, S4, S5 - C1.2 (Room Existence Check)
- External API - C2.2 (Room Management REST API)

**State Management:**

- Writes events to E1 (`room_events`)
- Projections P2, P3 updated in same transaction (AC3.2)

**Concurrency Model:**

- Room creation is idempotent (use client-provided `room_id` or generate)
- Participant add/remove uses event log ordering to resolve conflicts

**Authorization Model:**

- Only room owner can add/remove participants (checked via P3.role)
- User can leave any room they're in

**Implementation:**

```python
async def create_room(title: str, created_by: UUID, is_group: bool = False) -> UUID:
    room_id = uuid4()
    
    async with db.transaction():
        # Emit room.created event
        await emit_event(room_id, "room.created", {
            "room_id": str(room_id),
            "title": title,
            "created_by": str(created_by),
            "is_group": is_group
        })
        
        # Update projection
        await db.execute("""
            INSERT INTO rooms (room_id, title, created_by, is_group)
            VALUES ($1, $2, $3, $4)
        """, room_id, title, created_by, is_group)
        
        # Creator auto-joins as owner
        await add_participant(room_id, created_by, role="owner")
    
    return room_id
```


***

### S3. Chat History Service

**Pattern Context:** AP1 (Event Sourcing), AP3 (CQRS)
**Related Constraints:** AC3.2, AC3.3

**Responsibilities:**

- Provide `emit_event()` helper for all services to write to event log
- Retrieve ordered message history for a room (query P4)
- Build PydanticAI-compatible context from message history

**Owns Domain Objects:**

- P4 (messages) - Projection maintenance
- E1 (room_events) - Shared ownership (provides write helper)

**Depends On Services:**

- S1 - Authorization checks before returning history
- S2 - Room existence validation

**Provides Contracts To:**

- S4 - C1.3 (Context Provider for agents)
- S5 - C3.2 (Message History for UI)

**State Management:**

- Writes to E1, maintains P4 projection
- No caching (Postgres query with index is <10ms)

**Concurrency Model:**

- Event writes acquire per-room sequence lock (AC3.1)
- Reads are lock-free from P4 projection

**Authorization Model:**

- Calls S1.check_room_access() before returning messages

**Implementation:**

```python
async def emit_event(room_id: UUID, event_type: str, payload: dict) -> int:
    """Core event emission - used by all services"""
    async with db.transaction():
        # Generate sequence
        room_seq = await next_room_sequence(room_id)
        
        # Write event
        event_id = await db.fetchval("""
            INSERT INTO room_events (room_id, room_sequence, event_type, payload)
            VALUES ($1, $2, $3, $4)
            RETURNING event_id
        """, room_id, room_seq, event_type, json.dumps(payload))
        
        # Update projection (event-specific logic)
        await update_projection(event_type, payload)
        
        # Publish to Redis for real-time streaming
        await redis.publish(f"room:{room_id}", json.dumps({
            "event_id": event_id,
            "room_sequence": room_seq,
            "event_type": event_type,
            "payload": payload
        }))
        
        return room_seq

async def get_messages(room_id: UUID, limit: int = 50, before: int = None) -> list[Message]:
    """Retrieve message history for context or UI"""
    query = """
        SELECT * FROM messages 
        WHERE room_id = $1
        AND ($2::bigint IS NULL OR message_id < $2)
        ORDER BY created_at DESC
        LIMIT $3
    """
    rows = await db.fetch(query, room_id, before, limit)
    return [Message(**row) for row in reversed(rows)]  # Chronological order
```


***

### S4. Agent Runner Service

**Pattern Context:** AP2 (PydanticAI-Native), AP1 (Event Sourcing)
**Related Constraints:** AC2.3, AC4.2

**Responsibilities:**

- Initialize PydanticAI agents with dependency-injected tools
- Execute `agent.run()` with streaming enabled
- Emit `step.start`/`step.end` events from tool execution
- Handle multi-agent handoffs via special `transfer_to_agent` tool
- Execute analytics queries (with timeout)

**Owns Domain Objects:**

- P5 (steps) - Projection maintenance
- P6 (agent_handoffs) - Projection maintenance

**Depends On Services:**

- S1 - User authorization
- S3 - Message history for context building

**Provides Contracts To:**

- S5 - C1.4 (Agent Invocation)

**State Management:**

- Stateless - all context from S3 on each invocation
- Tools emit events to E1 as side effects

**Concurrency Model:**

- Each agent run is an async task (can run multiple per worker)
- Tools are async functions (AC2.3)
- pg_duckdb queries wrapped in `asyncio.to_thread()`

**Authorization Model:**

- Inherits from S5 (already checked before invocation)

**Implementation:**

```python
# Define smart tools that emit events
async def run_sql_query(ctx: RunContext[RoomContext], query: str) -> str:
    """Tool: Execute SQL query via pg_duckdb"""
    step_id = uuid4()
    
    # Emit step.start
    await emit_event(ctx.deps.room_id, "step.start", {
        "step_id": str(step_id),
        "message_id": ctx.deps.message_id,
        "agent_id": ctx.deps.agent_id,
        "tool_name": "run_sql_query",
        "input": {"query": query}
    })
    
    try:
        # Execute query in thread pool (AC2.3)
        result = await asyncio.to_thread(execute_duckdb_query, query, timeout=5)
        
        # Emit step.end
        await emit_event(ctx.deps.room_id, "step.end", {
            "step_id": str(step_id),
            "status": "completed",
            "output": result,
            "duration_ms": int((time.time() - start) * 1000)
        })
        
        return json.dumps(result)
    except Exception as e:
        await emit_event(ctx.deps.room_id, "step.end", {
            "step_id": str(step_id),
            "status": "failed",
            "output": None,
            "error_message": str(e)
        })
        raise

# Multi-agent handoff tool
async def transfer_to_agent(ctx: RunContext[RoomContext], 
                            target_agent: str, reason: str) -> str:
    """Tool: Hand off conversation to another agent"""
    handoff_id = uuid4()
    
    await emit_event(ctx.deps.room_id, "agent.handoff", {
        "handoff_id": str(handoff_id),
        "from_agent_id": ctx.deps.agent_id,
        "to_agent_id": target_agent,
        "message_id": ctx.deps.message_id,
        "context": {"reason": reason}
    })
    
    # Return instruction to PydanticAI to terminate current run
    return f"HANDOFF_COMPLETE: {target_agent}"

# Main agent execution
async def run_agent(room_id: UUID, user_message: str, user_id: UUID) -> AsyncIterator[str]:
    """Execute agent with streaming"""
    # Get context from S3
    history = await get_messages(room_id, limit=20)
    
    # Create room context
    ctx = RoomContext(room_id=room_id, message_id=next_message_id(), 
                     agent_id="customer_support")
    
    # Initialize agent with tools
    agent = Agent(
        "openai:gpt-4",
        deps_type=RoomContext,
        tools=[run_sql_query, transfer_to_agent, search_knowledge_base]
    )
    
    # Run with streaming
    async with agent.run_stream(user_message, message_history=history, deps=ctx) as result:
        async for chunk in result.stream_text():
            yield chunk  # Stream to S5 → Redis → Client
        
        # After completion, emit message.assistant event
        final_message = await result.final_message()
        await emit_event(room_id, "message.assistant", {
            "message_id": ctx.message_id,
            "agent_id": ctx.agent_id,
            "content": final_message.content,
            "button_options": extract_buttons(final_message)  # From agent metadata
        })
```


***

### S5. UI Gateway (AG-UI WebSocket Server)

**Pattern Context:** AP4 (AG-UI Protocol), AP5 (Multi-Worker)
**Related Constraints:** AC2.2, AC3.3

**Responsibilities:**

- Terminate AG-UI WebSocket connections
- Authenticate connections via JWT
- Subscribe to Redis room channels for real-time events
- Forward user messages to S3 → S4 pipeline
- Stream agent responses from S4 to client
- Replay missed events from E1 on reconnection

**Owns Domain Objects:**

- None (routing layer only)

**Depends On Services:**

- S1 - JWT validation
- S2 - Room existence/membership checks
- S3 - Message history for replay
- S4 - Agent invocation

**Provides Contracts To:**

- External WebSocket clients - C3.1 (AG-UI Protocol)

**State Management:**

- Stateless - no in-process session state
- Reconnection state rebuilt from E1 via client-provided `last_sequence`

**Concurrency Model:**

- Multiple workers handle different WebSocket connections
- Redis pub/sub ensures all workers receive room events
- No worker affinity required

**Authorization Model:**

- Validates JWT on WebSocket handshake
- Checks room membership before allowing subscription

**Implementation:**

```python
@app.websocket("/ui/session")
async def ag_ui_session(websocket: WebSocket):
    await websocket.accept()
    
    # AG-UI handshake
    handshake = await websocket.receive_json()
    token = handshake["auth"]["token"]
    room_id = UUID(handshake["room_id"])
    last_seq = handshake.get("last_sequence", 0)
    
    # Authenticate
    user = await get_current_user(token)
    if not await check_room_access(user.user_id, room_id):
        await websocket.close(code=403)
        return
    
    # Replay missed events
    missed_events = await db.fetch("""
        SELECT * FROM room_events 
        WHERE room_id=$1 AND room_sequence > $2
        ORDER BY room_sequence
    """, room_id, last_seq)
    
    for event in missed_events:
        await websocket.send_json({
            "type": "event",
            "sequence": event["room_sequence"],
            "event_type": event["event_type"],
            "payload": event["payload"]
        })
    
    # Subscribe to Redis for live events
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"room:{room_id}")
    
    # Bidirectional loop
    async def listen_redis():
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_text(message["data"])
    
    async def listen_client():
        async for data in websocket.iter_json():
            if data["type"] == "message.send":
                # User sent message - emit event + invoke agent
                await emit_event(room_id, "message.user", {
                    "message_id": next_message_id(),
                    "sender_id": str(user.user_id),
                    "content": data["content"]
                })
                
                # Stream agent response
                async for chunk in run_agent(room_id, data["content"], user.user_id):
                    await websocket.send_json({
                        "type": "message.delta",
                        "content": chunk
                    })
    
    await asyncio.gather(listen_redis(), listen_client())
```


***

## 5. Requirements with Explicit Cross-References

### R1. Identity and Multi-User Rooms

#### R1.1 User Identity via JWT

**Description:** System must authenticate users via JWT tokens and maintain user profiles.

**Domain Impact:** P1 (users)
**Service Owner:** S1 (primary)
**Constraint Reference:** AC5.1
**Pattern Justification:** AP4 (stateless auth)

**Contracts Required:**

- C1.1 (JWT Validation)
- C2.1 (User Profile API)

**Acceptance Criteria:**

- [ ] Valid JWT extracts `sub` claim to `external_id`
- [ ] User record created on first authentication
- [ ] Invalid/expired JWT returns 401
- [ ] User profile includes display_name, email, avatar_url

**Edge Cases:**

- User changes email in auth provider → Update on next login
- JWT missing required claims → Reject with 400

**Failure Modes:**

- Auth provider unavailable → Cached public keys allow validation for 1 hour

***

#### R1.2 Multi-User Room Creation

**Description:** Users must be able to create 1:1 and group rooms with titles and metadata.

**Domain Impact:** P2 (rooms), P3 (room_participants)
**Service Owner:** S2 (primary), S1 (auth)
**Constraint Reference:** AC3.2
**Pattern Justification:** AP1 (event sourcing)

**Contracts Required:**

- C2.2 (POST /rooms)

**Acceptance Criteria:**

- [ ] Room creator automatically added as owner (P3.role='owner')
- [ ] `room.created` event emitted to E1
- [ ] Room visible in creator's room list immediately (AC3.3)
- [ ] Group rooms support multiple participants, 1:1 rooms limited to 2

**Edge Cases:**

- Duplicate room titles allowed (differentiated by room_id)
- Empty title defaults to "Untitled Room"

**Failure Modes:**

- Database unavailable → Return 503, client retries

***

#### R1.3 Room Membership \& Authorization

**Description:** System must track room membership and enforce access control.

**Domain Impact:** P3 (room_participants)
**Service Owner:** S2 (membership), S1 (authorization)
**Constraint Reference:** AC5.2
**Pattern Justification:** AP1 (event sourcing)

**Contracts Required:**

- C1.1 (check_room_access)
- C2.2 (POST /rooms/{room_id}/participants)

**Acceptance Criteria:**

- [ ] Only room owners can add participants
- [ ] Participants can leave voluntarily
- [ ] Inactive participants cannot read/write messages
- [ ] Authorization checked before every room operation

**Edge Cases:**

- User removed while connected → WebSocket closed with 403
- Last participant leaves → Room remains (orphaned until garbage collection)

**Failure Modes:**

- Authorization check fails → Deny access (fail-safe)

***

### R2. Message Lifecycle \& Chat History

#### R2.1 User Message Persistence

**Description:** Users must send text messages that are persisted as immutable events.

**Domain Impact:** E1 (room_events), P4 (messages)
**Service Owner:** S5 (ingestion), S3 (persistence)
**Constraint Reference:** AC3.1, AC3.2
**Pattern Justification:** AP1 (event sourcing)

**Contracts Required:**

- C3.1 (AG-UI message.send)

**Acceptance Criteria:**

- [ ] Message assigned monotonic `room_sequence`
- [ ] `message.user` event written to E1
- [ ] Projection P4 updated in same transaction
- [ ] All room participants receive real-time notification via Redis

**Edge Cases:**

- Empty message rejected (400)
- Message >10KB truncated with warning

**Failure Modes:**

- Sequence generation collision → Retry with backoff (advisory lock prevents)

***

#### R2.2 Message History Retrieval

**Description:** Clients must retrieve paginated message history for a room.

**Domain Impact:** P4 (messages)
**Service Owner:** S3 (primary), S1 (auth)
**Constraint Reference:** AC3.3, AC4.1
**Pattern Justification:** AP3 (CQRS)

**Contracts Required:**

- C2.3 (GET /rooms/{room_id}/messages)
- C3.2 (AG-UI session replay)

**Acceptance Criteria:**

- [ ] Messages returned in chronological order
- [ ] Pagination via `before` cursor (message_id)
- [ ] Default limit 50, max 100 messages per request
- [ ] Includes assistant messages with button_options

**Edge Cases:**

- No messages → Empty array
- Cursor invalid → 400 error

**Failure Modes:**

- Query timeout → Return partial results with continuation token

***

#### R2.3 Immutable Event Log

**Description:** Messages and events must be immutable once written (append-only).

**Domain Impact:** E1 (room_events)
**Service Owner:** S3 (enforcer)
**Constraint Reference:** AC3.1
**Pattern Justification:** AP1 (event sourcing)

**Contracts Required:**

- None (architectural constraint)

**Acceptance Criteria:**

- [ ] No UPDATE or DELETE operations on room_events table
- [ ] Application code has no mutation logic
- [ ] Database triggers prevent accidental updates

**Edge Cases:**

- Moderation/deletion → Emit new `message.deleted` event, don't mutate original

**Failure Modes:**

- Accidental mutation attempt → Database constraint violation (IMMUTABLE trigger)

***

### R3. Agent Execution \& Multi-Turn Interaction

#### R3.1 PydanticAI Agent Invocation

**Description:** Each user message must trigger PydanticAI agent with room context.

**Domain Impact:** E1 (message.assistant), P4 (messages), P5 (steps)
**Service Owner:** S4 (primary), S3 (context)
**Constraint Reference:** AC2.3, AC4.2
**Pattern Justification:** AP2 (PydanticAI-native)

**Contracts Required:**

- C1.4 (run_agent)
- C1.3 (get_messages for context)

**Acceptance Criteria:**

- [ ] Agent receives last 20 messages as context
- [ ] Tools are async and emit step.start/step.end events
- [ ] Agent response streamed via Redis to all room participants
- [ ] Final message.assistant event written after stream completes

**Edge Cases:**

- Agent timeout (60s) → Emit system.error event, return partial response
- Tool failure → LLM receives error, can retry (self-healing)

**Failure Modes:**

- LLM API unavailable → Return 503 to user, don't emit message.assistant

***

#### R3.2 Tool Execution Tracking

**Description:** All tool invocations must be tracked as steps with status.

**Domain Impact:** E1 (step.start/end), P5 (steps)
**Service Owner:** S4 (primary)
**Constraint Reference:** AC3.2
**Pattern Justification:** AP2 (tools emit events)

**Contracts Required:**

- C1.5 (Tool interface with event emission)

**Acceptance Criteria:**

- [ ] Each tool execution creates step.start event before execution
- [ ] step.end event includes output, duration, status (completed/failed)
- [ ] Failed tools emit error_message, LLM receives error for retry
- [ ] Steps queryable for analytics via P5

**Edge Cases:**

- Tool crashes without emitting step.end → Timeout watcher emits failed event after 30s
- Zero tools invoked → No step events (valid for simple text responses)

**Failure Modes:**

- Step.end write fails → Step remains in 'running' state (monitoring alert)

***

#### R3.3 Multi-Agent Handoff

**Description:** Agents must be able to transfer conversations to specialized agents.

**Domain Impact:** E1 (agent.handoff), P6 (agent_handoffs)
**Service Owner:** S4 (primary)
**Constraint Reference:** AC2.3
**Pattern Justification:** AP2 (tools enable handoff)

**Contracts Required:**

- C1.6 (transfer_to_agent tool)

**Acceptance Criteria:**

- [ ] Agent can invoke `transfer_to_agent(target_agent, reason)` tool
- [ ] Handoff event emitted with context
- [ ] Next message triggers target agent instead of original
- [ ] Handoff visible in UI (agent_name changes)

**Edge Cases:**

- Transfer to non-existent agent → Return error to LLM, LLM can retry with valid agent
- Transfer back to original agent allowed (ping-pong detection added later)

**Failure Modes:**

- Handoff event write fails → Current agent continues (retry handoff)

***

### R4. Real-Time Multi-User Behavior

#### R4.1 Concurrent Multi-User Writes

**Description:** Multiple users must be able to send messages concurrently in the same room.

**Domain Impact:** E1 (room_events), P4 (messages)
**Service Owner:** S5 (ingestion), S3 (ordering)
**Constraint Reference:** AC3.1, AC2.2
**Pattern Justification:** AP5 (multi-worker)

**Contracts Required:**

- C1.1 (Authorization before write)
- C3.1 (AG-UI concurrent connections)

**Acceptance Criteria:**

- [ ] Sequence generation prevents collisions (advisory locks)
- [ ] All messages receive unique room_sequence
- [ ] Gaps in sequence are allowed (1, 2, 5 is valid)
- [ ] Client handles non-consecutive sequences

**Edge Cases:**

- 100 concurrent writes to same room → Serialized by advisory lock, max 1s latency
- Worker failure mid-write → Transaction rollback, no partial events

**Failure Modes:**

- Lock timeout (5s) → Return 503, client retries

***

#### R4.2 Real-Time Event Broadcast

**Description:** All room participants must receive real-time updates for new messages/steps.

**Domain Impact:** E1 (all event types)
**Service Owner:** S5 (broadcast), S3 (emission to Redis)
**Constraint Reference:** AC2.2
**Pattern Justification:** AP5 (Redis pub/sub)

**Contracts Required:**

- C3.1 (AG-UI WebSocket events)

**Acceptance Criteria:**

- [ ] Event written to E1 triggers Redis publish to room channel
- [ ] All workers subscribed to room receive event
- [ ] Workers forward to connected WebSocket clients
- [ ] Event includes sequence number for deduplication

**Edge Cases:**

- Client temporarily disconnected → Reconnects, replays from last_sequence
- Redis unavailable → Events still written to Postgres, clients reconnect to catch up

**Failure Modes:**

- Worker crash → Remaining workers handle other clients (no data loss)

***

#### R4.3 Reconnection \& Replay

**Description:** Clients must reconnect and replay missed events seamlessly.

**Domain Impact:** E1 (room_events)
**Service Owner:** S5 (replay), S3 (event query)
**Constraint Reference:** AC3.3
**Pattern Justification:** AP1 (event log)

**Contracts Required:**

- C3.1 (AG-UI session with last_sequence)

**Acceptance Criteria:**

- [ ] Client sends last_sequence on reconnection
- [ ] Server replays all events with room_sequence > last_sequence
- [ ] Replay completed before subscribing to live events
- [ ] No duplicate events received (client deduplicates by sequence)

**Edge Cases:**

- last_sequence in future → Return empty replay (client ahead somehow)
- Replay >1000 events → Paginate replay in chunks of 100

**Failure Modes:**

- Replay query slow → Stream results instead of buffering (no timeout)

***

### R5. Analytics \& Extensibility

#### R5.1 SQL Analytics via pg_duckdb

**Description:** Agents must execute SQL queries for analytics via pg_duckdb.

**Domain Impact:** P1-P6 (all projections), E1 (for event analytics)
**Service Owner:** S4 (executor)
**Constraint Reference:** AC4.2
**Pattern Justification:** AP1 (single database)

**Contracts Required:**

- C1.7 (run_sql_query tool)

**Acceptance Criteria:**

- [ ] Agent can invoke `run_sql_query(sql)` tool
- [ ] Query executed with 5s timeout
- [ ] Results returned as JSON to LLM
- [ ] Query logged as step (P5)

**Edge Cases:**

- Query timeout → Return partial results + timeout error to LLM
- Query mutates data (INSERT/UPDATE) → Rejected (read-only connection)

**Failure Modes:**

- pg_duckdb extension failure → Fall back to pure Postgres query (slower)

***

#### R5.2 Button-Based Interactions

**Description:** Agents must be able to present button options in responses.

**Domain Impact:** P4 (messages.button_options)
**Service Owner:** S4 (generation), S5 (rendering)
**Constraint Reference:** AC3.2
**Pattern Justification:** AP4 (AG-UI)

**Contracts Required:**

- C3.1 (AG-UI button rendering)

**Acceptance Criteria:**

- [ ] Agent response metadata includes button definitions
- [ ] Buttons stored in P4.button_options as JSONB array
- [ ] UI renders buttons with label, value, style
- [ ] Button click sends message with clicked value

**Edge Cases:**

- No buttons → button_options = NULL
- >10 buttons → Warn in logs, render all (UX issue)

**Failure Modes:**

- Invalid button schema → Ignore buttons, render text only

***

#### R5.3 Future: Step Progress Streaming

**Description:** (Deferred to v2) Stream step execution progress to UI in real-time.

**Domain Impact:** E1 (new event type: step.progress)
**Service Owner:** S4
**Constraint Reference:** AC2.3
**Pattern Justification:** AP1, AP4

**Acceptance Criteria:**

- [ ] Tools emit step.progress events during long operations
- [ ] Progress includes percentage, status message
- [ ] UI shows progress bar

**Implementation Note:** Start with final results only (R3.2), add progress later.

***

## 6. Contracts (APIs and Interfaces)

### C1. Service-to-Service Internal APIs

#### C1.1 Authorization Check

**Provided By:** S1 (Identity \& Auth)
**Consumed By:** S2, S3, S4, S5
**Implements Requirements:** R1.3, R4.1
**Pattern Context:** AP5 (stateless)

**Function Signature:**

```python
async def check_room_access(user_id: UUID, room_id: UUID) -> bool
```

**Input:** User ID, Room ID
**Output:** Boolean (True if user is active participant)

**Authorization:** N/A (this IS the authorization check)

**Error Responses:**

- Database error → Raises exception (caller handles)

**Consistency Guarantees:** Read-after-write (AC3.3) - sees participant adds immediately

**Idempotency:** Yes (pure query)

***

#### C1.2 Room Existence Check

**Provided By:** S2 (Room Management)
**Consumed By:** S3, S4, S5
**Implements Requirements:** R1.2

**Function Signature:**

```python
async def room_exists(room_id: UUID) -> bool
```


***

#### C1.3 Context Provider

**Provided By:** S3 (Chat History)
**Consumed By:** S4 (Agent Runner)
**Implements Requirements:** R2.2, R3.1

**Function Signature:**

```python
async def get_messages(room_id: UUID, limit: int = 50, before: int = None) -> list[Message]
```

**Input:** Room ID, optional pagination
**Output:** List of Message objects in chronological order

**Authorization:** Caller responsible (S4 already authorized)

**Performance:** <50ms for 50 messages (indexed query)

***

#### C1.4 Agent Invocation

**Provided By:** S4 (Agent Runner)
**Consumed By:** S5 (UI Gateway)
**Implements Requirements:** R3.1

**Function Signature:**

```python
async def run_agent(room_id: UUID, user_message: str, user_id: UUID) -> AsyncIterator[str]
```

**Input:** Room ID, user message text, user ID
**Output:** Async stream of text chunks

**Side Effects:**

- Writes message.user event to E1
- Writes step.start/end events to E1
- Writes message.assistant event to E1 on completion

**Error Handling:**

- LLM timeout → Raises TimeoutError
- Tool failure → LLM receives error, may retry

***

#### C1.5 Tool Interface (Event-Emitting)

**Provided By:** S4 (Agent Runner - tool implementations)
**Consumed By:** PydanticAI agent runtime
**Implements Requirements:** R3.2

**Pattern:**

```python
async def tool_name(ctx: RunContext[RoomContext], arg1: str) -> str:
    # 1. Emit step.start
    # 2. Execute logic
    # 3. Emit step.end
    # 4. Return result to LLM
```

**Contract:**

- All tools must emit step.start before execution
- All tools must emit step.end on success OR failure
- Return type must be JSON-serializable string

***

#### C1.6 Multi-Agent Transfer Tool

**Provided By:** S4 (Agent Runner)
**Consumed By:** PydanticAI agent (as tool)
**Implements Requirements:** R3.3

**Function Signature:**

```python
async def transfer_to_agent(ctx: RunContext[RoomContext], 
                            target_agent: str, reason: str) -> str
```

**Input:** Target agent ID, handoff reason
**Output:** Confirmation string

**Side Effects:**

- Writes agent.handoff event to E1
- Updates P6 projection

**Validation:**

- Target agent must exist in AGENT_REGISTRY
- Reason required (>10 chars)

***

#### C1.7 SQL Query Tool

**Provided By:** S4 (Agent Runner)
**Consumed By:** PydanticAI agent (as tool)
**Implements Requirements:** R5.1

**Function Signature:**

```python
async def run_sql_query(ctx: RunContext[RoomContext], query: str) -> str
```

**Input:** SQL query string
**Output:** JSON-serialized query results

**Constraints:**

- Read-only (enforced via connection role)
- 5 second timeout
- Max 1000 rows returned

**Security:**

- No parameterization required (LLM-generated queries vetted by PydanticAI)
- Dangerous keywords (DROP, DELETE, etc.) rejected

***

### C2. External HTTP/REST APIs

#### C2.1 User Profile API

**Provided By:** S1 (Identity \& Auth)
**Consumed By:** External clients
**Implements Requirements:** R1.1

**Endpoint:** `GET /api/users/me`

**Headers:**

```
Authorization: Bearer <jwt_token>
```

**Response 200:**

```json
{
  "user_id": "uuid",
  "email": "user@example.com",
  "display_name": "Jane Doe",
  "avatar_url": "https://...",
  "created_at": "2025-12-06T12:00:00Z"
}
```

**Error Responses:**

- 401 Unauthorized - Invalid/expired JWT
- 500 Internal Server Error - Database error

***

#### C2.2 Room Management API

**Provided By:** S2 (Room Management)
**Consumed By:** External clients
**Implements Requirements:** R1.2, R1.3

**Create Room:**

```http
POST /api/rooms
Authorization: Bearer <jwt>
Content-Type: application/json

{
  "title": "Customer Support",
  "is_group": false,
  "initial_participants": ["user_id"]  // Optional
}

Response 201:
{
  "room_id": "uuid",
  "title": "Customer Support",
  "created_at": "2025-12-06T12:00:00Z"
}
```

**List Rooms:**

```http
GET /api/rooms
Authorization: Bearer <jwt>

Response 200:
{
  "rooms": [
    {
      "room_id": "uuid",
      "title": "Support",
      "last_activity": "2025-12-06T11:50:00Z",
      "unread_count": 3
    }
  ]
}
```

**Add Participant:**

```http
POST /api/rooms/{room_id}/participants
Authorization: Bearer <jwt>

{
  "user_id": "uuid",
  "role": "member"  // owner | member
}

Response 200:
{
  "success": true
}
```

**Error Responses:**

- 403 Forbidden - Not room owner (for add participant)
- 404 Not Found - Room doesn't exist

***

#### C2.3 Message History API

**Provided By:** S3 (Chat History)
**Consumed By:** External clients
**Implements Requirements:** R2.2

**Endpoint:** `GET /api/rooms/{room_id}/messages`

**Query Parameters:**

- `before` (optional) - Message ID for pagination
- `limit` (optional, default 50, max 100)

**Headers:**

```
Authorization: Bearer <jwt>
```

**Response 200:**

```json
{
  "messages": [
    {
      "message_id": 12345,
      "sender_id": "uuid or null",
      "agent_id": "customer_support",
      "content": "Hello, how can I help?",
      "button_options": [
        {"label": "Track Order", "value": "track_order", "style": "primary"}
      ],
      "created_at": "2025-12-06T11:45:00Z"
    }
  ],
  "has_more": true,
  "next_cursor": 12340
}
```

**Error Responses:**

- 403 Forbidden - User not in room
- 404 Not Found - Room doesn't exist

***

### C3. Real-Time/Streaming Protocols

#### C3.1 AG-UI WebSocket Protocol

**Provided By:** S5 (UI Gateway)
**Consumed By:** AG-UI compatible clients
**Implements Requirements:** R2.1, R4.2, R4.3

**Connection:** `ws://localhost:8000/ui/session`

**Handshake (Client → Server):**

```json
{
  "type": "session.create",
  "auth": {
    "token": "jwt_token"
  },
  "room_id": "uuid",
  "last_sequence": 0  // For replay
}
```

**Handshake Response (Server → Client):**

```json
{
  "type": "session.created",
  "session_id": "uuid",
  "room": {
    "room_id": "uuid",
    "title": "Support",
    "participants": [...]
  }
}
```

**Event Types (Server → Client):**


| Event Type | When Sent | Payload |
| :-- | :-- | :-- |
| `message.user` | User sent message | `{message_id, sender_id, content, sequence}` |
| `message.assistant` | Agent completed turn | `{message_id, agent_id, content, button_options, sequence}` |
| `message.delta` | Agent streaming (ephemeral) | `{content: "chunk"}` |
| `step.start` | Tool execution begins | `{step_id, tool_name, input, sequence}` |
| `step.end` | Tool execution completes | `{step_id, output, status, sequence}` |
| `agent.handoff` | Agent transfer | `{from_agent_id, to_agent_id, sequence}` |
| `participant.joined` | User joins room | `{user_id, role, sequence}` |

**User Actions




**User Actions (Client → Server):**


| Action Type | Payload | Result |
| :-- | :-- | :-- |
| `message.send` | `{content: "text", metadata: {}}` | Emits message.user event, triggers agent |
| `button.click` | `{message_id: int, value: "button_value"}` | Same as message.send with button context |
| `room.subscribe` | `{room_id: "uuid"}` | Switch to different room |
| `room.unsubscribe` | `{}` | Stop receiving events |

**Ordering Guarantee:** All events include `sequence` number (from E1.room_sequence) - clients use this for deduplication and gap detection (AC3.1)

**Reconnection Semantics:**

1. Client sends `last_sequence` in handshake
2. Server replays all events where `room_sequence > last_sequence`
3. Server subscribes to Redis for live events
4. Client receives replay THEN live events (no duplicates if client dedupes by sequence)

**Backpressure Handling:**

- If client WebSocket send buffer fills (slow consumer), server drops ephemeral `message.delta` events
- Persistent events (message.assistant) are never dropped - client will receive via replay

**Error Codes:**

- 401 - Invalid JWT
- 403 - User not in room
- 4000 - Invalid message format
- 4001 - Room not found

***

#### C3.2 Message History Stream (Supplementary)

**Provided By:** S5 (UI Gateway)
**Consumed By:** AG-UI clients
**Implements Requirements:** R4.3

**Purpose:** Initial load of message history via WebSocket (alternative to REST API C2.3)

**Request (Client → Server):**

```json
{
  "type": "history.fetch",
  "limit": 50,
  "before": 12345  // Optional cursor
}
```

**Response (Server → Client):**

```json
{
  "type": "history.batch",
  "messages": [...],
  "has_more": true
}
```

**Performance:** Streams messages incrementally (10 at a time) to avoid blocking WebSocket

***

### C4. Batch/Analytics Interfaces

#### C4.1 Event Export API (Future)

**Provided By:** S3 (Chat History)
**Consumed By:** External analytics tools
**Implements Requirements:** Future analytics integration

**Endpoint:** `GET /api/analytics/events`

**Query Parameters:**

- `room_id` (optional) - Filter to specific room
- `event_type` (optional) - Filter to event types
- `since` (required) - Timestamp for incremental export
- `format` (optional) - `json` | `ndjson` | `parquet`

**Response:** Streaming response with event batches

**Note:** Deferred to v2 - focus on real-time for v1

***

## 7. Design Guardrails

### DG1. Data Consistency and Concurrency

**Enforces:** AP1, AP3, AC3.1, AC3.2

#### DG1.1 Event Immutability

**Rule Type:** Mandatory

**Statement:** No code may UPDATE or DELETE from `room_events` table. All state changes append new events.

**Rationale:** Prevents "split brain" between event log and projections. Violating this breaks audit trail and replay capability (AP1).

**Validation Method:**

- Database trigger rejects mutations
- Code review checklist
- Integration test attempts UPDATE, expects error

**Applies To:**

- Services: All (S1-S5)
- Domain Objects: E1
- Requirements: R2.3

**Example (Correct):**

```python
# To "delete" a message, emit a new event
await emit_event(room_id, "message.deleted", {
    "message_id": 12345,
    "deleted_by": user_id,
    "reason": "user_request"
})
```

**Anti-Pattern (Incorrect):**

```python
# NEVER DO THIS
await db.execute("UPDATE room_events SET payload=... WHERE event_id=...")
await db.execute("DELETE FROM room_events WHERE event_id=...")
```


***

#### DG1.2 Transactional Projection Updates

**Rule Type:** Mandatory

**Statement:** Projection updates (P1-P6) MUST occur in the same database transaction as the event write (E1).

**Rationale:** Ensures read-after-write consistency (AC3.3). Prevents projections from diverging from event log.

**Validation Method:**

- Code review - all `emit_event()` calls include projection update in same `async with db.transaction()` block
- Integration test: Write event, query projection immediately, expect new data

**Applies To:**

- Services: S2, S3, S4
- Domain Objects: E1, P2-P6
- Requirements: R1.2, R2.1, R3.2

**Example (Correct):**

```python
async def emit_event(room_id, event_type, payload):
    async with db.transaction():  # Single transaction
        # 1. Write event
        await db.execute("INSERT INTO room_events ...")
        
        # 2. Update projection
        if event_type == "message.user":
            await db.execute("INSERT INTO messages ...")
        
        # 3. Publish to Redis (outside transaction is OK - ephemeral)
    await redis.publish(...)
```

**Anti-Pattern (Incorrect):**

```python
# Event and projection in separate transactions - WRONG
await db.execute("INSERT INTO room_events ...")
# ... some code ...
await db.execute("INSERT INTO messages ...")  # Could fail, leaving orphan event
```


***

#### DG1.3 Sequence Uniqueness Enforcement

**Rule Type:** Mandatory

**Statement:** `room_sequence` generation must use Postgres advisory locks or `SELECT ... FOR UPDATE` to prevent duplicate sequences in multi-worker environments.

**Rationale:** Prevents sequence collisions when multiple workers write to same room concurrently (AC3.1, AP5).

**Validation Method:**

- Load test: 4 workers, 100 concurrent writes to same room, verify no duplicate sequences
- Code review: `next_room_sequence()` uses advisory lock

**Applies To:**

- Services: S3 (emit_event helper)
- Domain Objects: E1
- Requirements: R4.1

**Example (Correct):**

```python
async def next_room_sequence(room_id: UUID) -> int:
    async with db.transaction():
        # Advisory lock scoped to this room
        await db.execute("SELECT pg_advisory_xact_lock($1)", hash(room_id) % (2**31))
        
        seq = await db.fetchval(
            "SELECT COALESCE(MAX(room_sequence), 0) + 1 FROM room_events WHERE room_id=$1",
            room_id
        )
        return seq
```

**Anti-Pattern (Incorrect):**

```python
# No lock - race condition
seq = await db.fetchval("SELECT MAX(room_sequence) + 1 ...")  # Two workers get same seq
```


***

#### DG1.4 Sparse Sequence Handling

**Rule Type:** Mandatory (Client-Side)

**Statement:** Client code must NOT assume `room_sequence` values are consecutive. Gaps (1, 2, 5, 7) are valid.

**Rationale:** Advisory locks allow gaps to improve concurrency. Transaction rollbacks create gaps (AC3.1).

**Validation Method:**

- Client integration test with synthetic gaps
- UI review: No "missing message" warnings for non-consecutive sequences

**Applies To:**

- Requirements: R4.1, R4.3
- Contracts: C3.1

**Example (Correct):**

```javascript
// Client tracks last_sequence, doesn't validate consecutiveness
let last_sequence = 0;
socket.on('event', (event) => {
  if (event.sequence > last_sequence) {
    processEvent(event);
    last_sequence = event.sequence;  // Jump from 2 to 5 is OK
  }
});
```


#### DG1.5 Idempotent Projection Handlers : UNDER REVIEW

**Rule Type:** 

**Statement:** 

**Rationale:** 

**Validation Method:**

- 

**Applies To:**

- Requirements: 
- Contracts: 

**Example (Correct):**



***

### DG2. Performance and Scalability

**Enforces:** AP5, AC2.3, AC4.1, AC4.2

#### DG2.1 Async-First I/O

**Rule Type:** Mandatory

**Statement:** All I/O operations (database, Redis, HTTP, LLM calls) MUST use async/await. Blocking calls MUST be wrapped in `asyncio.to_thread()` or `ProcessPoolExecutor`.

**Rationale:** Prevents blocking the event loop, which would make multi-worker deployment (AP5) unusable. Python GIL requires async for concurrency.

**Validation Method:**

- Static analysis: Ban `import requests`, `import psycopg2` (sync libraries)
- Code review: Check for `await` on all I/O
- Performance test: Measure worker responsiveness under load

**Applies To:**

- All services (S1-S5)
- Constraints: AC2.3

**Example (Correct):**

```python
# Async database
import asyncpg
conn = await asyncpg.connect(...)
await conn.execute(...)

# Async HTTP
import httpx
async with httpx.AsyncClient() as client:
    await client.get(...)

# Blocking library wrapped
import duckdb
result = await asyncio.to_thread(duckdb.execute, query)
```

**Anti-Pattern (Incorrect):**

```python
import time
time.sleep(5)  # Blocks entire worker - FORBIDDEN

import requests
requests.get("https://...")  # Blocks event loop - FORBIDDEN
```


***

#### DG2.2 Connection Pool Limits

**Rule Type:** Mandatory

**Statement:** Each FastAPI worker maintains at most 10 Postgres connections. Total connections across all workers must not exceed `max_connections - 10` (reserve for admin).

**Rationale:** Prevents connection exhaustion in Postgres (AC4.1).

**Validation Method:**

- Configuration validation on startup
- Monitoring: Alert if connections >80% of max

**Applies To:**

- Services: All
- Constraints: AC4.1

**Configuration:**

```python
# config.py
DATABASE_POOL_MIN_SIZE = 5
DATABASE_POOL_MAX_SIZE = 10

# With 4 workers: 4 * 10 = 40 connections
# Postgres max_connections should be >=50
```


***

#### DG2.3 Analytics Query Timeout

**Rule Type:** Mandatory

**Statement:** All pg_duckdb queries invoked by agents MUST have `statement_timeout=5s`. Queries exceeding timeout return partial results + error to LLM.

**Rationale:** Prevents long-running analytical queries from blocking message writes or consuming excessive resources (AC4.2).

**Validation Method:**

- Code review: All `run_sql_query` calls set timeout
- Integration test: Long query is cancelled at 5s

**Applies To:**

- Services: S4 (Agent Runner)
- Requirements: R5.1
- Contracts: C1.7

**Example (Correct):**

```python
async def run_sql_query(ctx, query: str) -> str:
    async with db.acquire() as conn:
        await conn.execute("SET statement_timeout = '5s'")
        try:
            result = await asyncio.to_thread(execute_duckdb, query)
        except asyncio.TimeoutError:
            return json.dumps({"error": "Query timeout", "partial_results": []})
```


***

#### DG2.4 Redis Pub/Sub Ephemeral-Only

**Rule Type:** Mandatory

**Statement:** Redis pub/sub is used ONLY for ephemeral streaming (`message.delta` tokens). All persistent events MUST be written to Postgres FIRST, then published to Redis.

**Rationale:** Redis pub/sub has no persistence. If a worker crashes, ephemeral deltas are lost (acceptable), but persistent events must survive (AP1).

**Validation Method:**

- Code review: All `emit_event()` writes to Postgres before Redis publish
- Chaos test: Kill worker mid-agent-run, verify client can replay from Postgres

**Applies To:**

- Services: S3, S5
- Constraints: AC2.2
- Requirements: R4.2

**Example (Correct):**

```python
async def emit_event(room_id, event_type, payload):
    async with db.transaction():
        # 1. Persist to Postgres FIRST
        await db.execute("INSERT INTO room_events ...")
    
    # 2. Publish to Redis (outside transaction)
    await redis.publish(f"room:{room_id}", json.dumps({...}))
```


***

### DG3. Security and Authorization

**Enforces:** AC5.1, AC5.2

#### DG3.1 Authorization Before Every Room Operation

**Rule Type:** Mandatory

**Statement:** All endpoints/functions that read or write room data MUST call `check_room_access(user_id, room_id)` before executing.

**Rationale:** Enforces room-level authorization (AC5.2). Prevents users from accessing rooms they're not members of.

**Validation Method:**

- Security test: Attempt to access room as non-member, expect 403
- Code review: Check for authorization call at top of all room operations

**Applies To:**

- Services: S2, S3, S4, S5
- Requirements: R1.3, R4.1
- Contracts: All C2.x, C3.x

**Example (Correct):**

```python
@app.get("/api/rooms/{room_id}/messages")
async def get_messages(room_id: UUID, user: User = Depends(get_current_user)):
    # Authorization check FIRST
    if not await check_room_access(user.user_id, room_id):
        raise HTTPException(403, "Not authorized")
    
    # Then query
    messages = await db.fetch("SELECT * FROM messages WHERE room_id=$1", room_id)
    return messages
```

**Anti-Pattern (Incorrect):**

```python
# Missing authorization check - INSECURE
@app.get("/api/rooms/{room_id}/messages")
async def get_messages(room_id: UUID):
    return await db.fetch("SELECT * FROM messages WHERE room_id=$1", room_id)
```


***

#### DG3.2 JWT Validation on Every Request

**Rule Type:** Mandatory

**Statement:** All HTTP endpoints (except health checks) MUST validate JWT via FastAPI dependency. WebSocket connections validate on handshake.

**Rationale:** Enforces authentication (AC5.1). Stateless workers have no session memory.

**Validation Method:**

- Security test: Request without JWT returns 401
- Security test: Expired JWT returns 401

**Applies To:**

- Services: S1 (provides), All others (consume)
- Contracts: All C2.x, C3.x

**Example (Correct):**

```python
from fastapi.security import HTTPBearer
oauth2_scheme = HTTPBearer()

@app.get("/api/rooms")
async def list_rooms(user: User = Depends(get_current_user)):  # JWT validated here
    ...
```


***

#### DG3.3 SQL Injection Prevention (pg_duckdb)

**Rule Type:** Mandatory

**Statement:** All `run_sql_query` tool calls MUST reject queries containing dangerous keywords: `DROP`, `DELETE`, `UPDATE`, `INSERT`, `CREATE`, `ALTER`, `GRANT`.

**Rationale:** Agents generate SQL from LLM output. Prevent accidental or malicious data mutation (R5.1 specifies read-only).

**Validation Method:**

- Unit test: Pass malicious SQL, expect rejection
- Code review: Keyword blacklist applied before execution

**Applies To:**

- Services: S4 (Agent Runner)
- Contracts: C1.7

**Example (Correct):**

```python
FORBIDDEN_SQL_KEYWORDS = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "GRANT"]

async def run_sql_query(ctx, query: str) -> str:
    # Validate before execution
    query_upper = query.upper()
    if any(keyword in query_upper for keyword in FORBIDDEN_SQL_KEYWORDS):
        raise ValueError("Query contains forbidden keyword - read-only queries only")
    
    # Execute with read-only role
    async with db.acquire() as conn:
        await conn.execute("SET ROLE readonly_user")
        result = await asyncio.to_thread(execute_duckdb, query)
    return json.dumps(result)
```


***

### DG4. Error Handling and Resilience

**Enforces:** AP2, R3.1, R3.2

#### DG4.1 Agent Timeout Handling

**Rule Type:** Mandatory

**Statement:** All `agent.run()` calls MUST have a 60-second timeout. On timeout, emit `system.error` event and return partial response to user.

**Rationale:** Prevents hung agents from blocking workers. Users get feedback instead of indefinite waiting.

**Validation Method:**

- Integration test: Mock slow LLM, verify timeout triggers
- Load test: Verify worker remains responsive after timeout

**Applies To:**

- Services: S4 (Agent Runner)
- Requirements: R3.1

**Example (Correct):**

```python
async def run_agent(room_id, user_message, user_id):
    try:
        async with asyncio.timeout(60):  # 60 second timeout
            async with agent.run_stream(...) as result:
                async for chunk in result.stream_text():
                    yield chunk
    except asyncio.TimeoutError:
        # Emit error event
        await emit_event(room_id, "system.error", {
            "error_type": "agent_timeout",
            "message": "Agent execution exceeded 60 seconds"
        })
        yield "\n\n[Response timed out. Please try rephrasing your question.]"
```


***

#### DG4.2 Tool Failure Self-Healing

**Rule Type:** Mandatory

**Statement:** When a tool execution fails, emit `step.end` with status='failed' and error message. Return error to LLM to allow retry. Do NOT crash the agent run.

**Rationale:** Leverages AP2 (PydanticAI self-healing). LLM can see error and retry with corrected input.

**Validation Method:**

- Integration test: Tool raises exception, verify agent continues
- Check logs for step.end with status=failed

**Applies To:**

- Services: S4 (Agent Runner)
- Requirements: R3.2

**Example (Correct):**

```python
async def run_sql_query(ctx, query: str) -> str:
    step_id = uuid4()
    await emit_event(ctx.room_id, "step.start", {...})
    
    try:
        result = await execute_query(query)
        await emit_event(ctx.room_id, "step.end", {
            "step_id": step_id,
            "status": "completed",
            "output": result
        })
        return json.dumps(result)
    except Exception as e:
        # Emit failure event
        await emit_event(ctx.room_id, "step.end", {
            "step_id": step_id,
            "status": "failed",
            "error_message": str(e)
        })
        # Return error to LLM (allows retry)
        return f"ERROR: {str(e)}"  # LLM sees this and can retry
```


***

#### DG4.3 Database Transaction Rollback Safety

**Rule Type:** Mandatory

**Statement:** If projection update fails within a transaction, the entire transaction (including event write) MUST rollback. Never commit partial state.

**Rationale:** Maintains consistency between event log and projections (AC3.2). Prevents orphan events.

**Validation Method:**

- Integration test: Mock projection update failure, verify event not in E1
- Code review: No `try/except` around projection updates without re-raising

**Applies To:**

- Services: S2, S3, S4
- Domain: E1, P2-P6

**Example (Correct):**

```python
async def emit_event(room_id, event_type, payload):
    async with db.transaction():  # Auto-rollback on exception
        await db.execute("INSERT INTO room_events ...")
        
        # If this fails, entire transaction rolls back
        await db.execute("INSERT INTO messages ...")
        
    # Only publish to Redis if transaction succeeded
    await redis.publish(...)
```

**Anti-Pattern (Incorrect):**

```python
async with db.transaction():
    await db.execute("INSERT INTO room_events ...")
    try:
        await db.execute("INSERT INTO messages ...")
    except Exception:
        pass  # Swallowing error - event written but projection failed - INCONSISTENT
```


***

### DG5. Testing and Validation

**Enforces:** All Requirements

#### DG5.1 Event Log Replay Testing

**Rule Type:** Mandatory

**Statement:** All projection updates MUST be testable by replaying events from E1. Test suite must include replay scenarios.

**Rationale:** Validates that projections can be rebuilt from events (AP1). Critical for disaster recovery.

**Validation Method:**

- Integration test: Truncate projection table, replay events, verify projection matches original

**Applies To:**

- Services: S2, S3, S4
- Domain: P2-P6

**Test Pattern:**

```python
async def test_projection_replay():
    # 1. Create events via normal flow
    await create_room(title="Test")
    await send_message(room_id, "Hello")
    
    # 2. Save projection state
    messages_before = await db.fetch("SELECT * FROM messages")
    
    # 3. Truncate projection
    await db.execute("TRUNCATE messages")
    
    # 4. Replay events
    events = await db.fetch("SELECT * FROM room_events ORDER BY event_id")
    for event in events:
        await update_projection(event.event_type, event.payload)
    
    # 5. Verify match
    messages_after = await db.fetch("SELECT * FROM messages")
    assert messages_before == messages_after
```


***

#### DG5.2 Multi-Worker Concurrency Testing

**Rule Type:** Mandatory

**Statement:** Load tests MUST run with 4+ workers and simulate concurrent writes to the same room. Verify no duplicate sequences, no lost events.

**Validation Method:**

- Load test: 4 workers, 100 concurrent requests to same room, check for sequence uniqueness
- Verify all 100 events in E1 with unique room_sequence

**Applies To:**

- Services: All
- Requirements: R4.1

**Test Command:**

```bash
# docker-compose.yml sets replicas: 4 for fastapi service
docker-compose up --scale fastapi=4
python tests/load_test.py --workers 4 --requests 100 --room-id <uuid>
```


***

#### DG5.3 WebSocket Reconnection Testing

**Rule Type:** Mandatory

**Statement:** Integration tests MUST verify reconnection behavior: client disconnects, new events occur, client reconnects with last_sequence, receives missed events.

**Validation Method:**

- Integration test: Connect, receive sequence 1-5, disconnect, server writes 6-10, reconnect with last_sequence=5, receive 6-10

**Applies To:**

- Services: S5
- Requirements: R4.3

**Test Pattern:**

```python
async def test_websocket_reconnection():
    async with websocket_client() as ws:
        # Receive initial events
        for i in range(5):
            event = await ws.receive_json()
            assert event['sequence'] == i + 1
        last_seq = 5
        await ws.close()
    
    # Simulate events while disconnected
    await send_message(room_id, "Missed message 1")
    await send_message(room_id, "Missed message 2")
    
    # Reconnect with last_sequence
    async with websocket_client(last_sequence=last_seq) as ws:
        event1 = await ws.receive_json()
        assert event1['sequence'] == 6
        event2 = await ws.receive_json()
        assert event2['sequence'] == 7
```


***

## 8. Validation and Approval

### Cross-Reference Validation Matrix

| Section | References To | Referenced By | Orphan Check | Completeness Check |
| :-- | :-- | :-- | :-- | :-- |
| AP (Patterns) | None | AC, E, P, S, R, DG | N/A | ✅ 5 patterns defined |
| AC (Constraints) | AP1-AP5 | D, S, R, DG | ✅ All AC referenced | ✅ All AP have constraints |
| E (Events) | AP1, AC3.1 | S, R, DG | ✅ E1 referenced throughout | ✅ E1 has 9 event types |
| P (Projections) | AP3, AC3.2, E1 | S, R | ✅ P1-P6 all referenced | ✅ All events project somewhere |
| S (Services) | AP1-5, AC, P, E | R, C | ✅ S1-S5 all referenced | ✅ All P owned by service |
| R (Requirements) | AP, AC, P, E, S | C, DG | ✅ R1-R5 all referenced | ✅ All R have acceptance criteria |
| C (Contracts) | P, S, R | DG | ✅ C1-C4 all referenced | ✅ All R have implementing C |
| DG (Guardrails) | AP, AC, R, C | None | ✅ All DG enforcing something | ✅ All AC have enforcing DG |

### Contradiction Checklist

Before implementation, verified no contradictions exist:

- [✅] **Technology Stack Consistency:** All Domain Objects (E1, P1-P6) use Postgres (AC2.1)
- [✅] **Service Ownership:** Each projection owned by exactly one service (S1-S5)
- [✅] **Dependency Acyclicity:** No circular dependencies (see service graph in §4)
- [✅] **Authorization Completeness:** All multi-user Requirements (R4.x) have authorization checks (C1.1, DG3.1)
- [✅] **Concurrency Strategy:** AC3.1 enforced by DG1.3 (advisory locks)
- [✅] **Error Handling:** All Contracts (C1-C4) define error responses
- [✅] **Projection Consistency:** All Projections (P2-P6) specify transactional update (AC3.2, DG1.2)
- [✅] **Event Sourcing:** AP1 enforced by DG1.1 (immutability) and DG5.1 (replay testing)
- [✅] **Multi-Worker Coordination:** AC2.2 (Redis required) + DG1.3 (sequence locks) + DG5.2 (load testing)
- [✅] **Undefined References:** All cross-references validated above


### Approval Sign-Off

| Role | Name | Date | Concerns |
| :-- | :-- | :-- | :-- |
| Principal Architect | [Your Name] | Dec 6, 2025 | None - ready for implementation |
| Lead Engineer |  |  |  |
| Security Lead |  |  | Review AC5.x, DG3.x |
| Operations Lead |  |  | Review deployment (§10) |


***

## 9. Change Log

| Version | Date | Author | Changes | Sections Affected | Validation Re-Run |
| :-- | :-- | :-- | :-- | :-- | :-- |
| 1.0 | Dec 6, 2025 | AI Architect | Initial creation from decisions | All | N/A |


***

## 10. Deployment Configuration

### Docker Compose Stack

**File:** `docker-compose.yml`



### Database Initialization Script

**File:** `init.sql`

```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_duckdb";  -- For analytics

-- Create readonly role for analytics queries
CREATE ROLE readonly_user LOGIN PASSWORD 'readonly_pass';

-- Event log (E1)
CREATE TABLE room_events (
    event_id BIGSERIAL PRIMARY KEY,
    room_id UUID NOT NULL,
    room_sequence BIGINT NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (room_id, room_sequence)
);
CREATE INDEX idx_room_events_replay ON room_events (room_id, room_sequence);
CREATE INDEX idx_room_events_type ON room_events (event_type, created_at);

-- Projections
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true
);
CREATE INDEX idx_users_external_id ON users (external_id);

CREATE TABLE rooms (
    room_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(200),
    created_by UUID NOT NULL REFERENCES users(user_id),
    is_group BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);
CREATE INDEX idx_rooms_created_by ON rooms (created_by);
CREATE INDEX idx_rooms_last_activity ON rooms (last_activity DESC);

CREATE TABLE room_participants (
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    user_id UUID NOT NULL REFERENCES users(user_id),
    role VARCHAR(20) NOT NULL DEFAULT 'member',
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    PRIMARY KEY (room_id, user_id)
);
CREATE INDEX idx_participants_user_rooms ON room_participants (user_id, is_active) 
    WHERE is_active = true;

CREATE TABLE messages (
    message_id BIGSERIAL PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    sender_id UUID REFERENCES users(user_id),
    agent_id VARCHAR(50),
    content TEXT NOT NULL,
    button_options JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_messages_room_time ON messages (room_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages (sender_id);

CREATE TABLE steps (
    step_id UUID PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    message_id BIGINT NOT NULL REFERENCES messages(message_id),
    agent_id VARCHAR(50) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL,
    input JSONB NOT NULL,
    output JSONB,
    error_message TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    duration_ms INTEGER
);
CREATE INDEX idx_steps_message ON steps (message_id);
CREATE INDEX idx_steps_room_time ON steps (room_id, started_at DESC);
CREATE INDEX idx_steps_status ON steps (status) WHERE status = 'running';

CREATE TABLE agent_handoffs (
    handoff_id UUID PRIMARY KEY,
    from_agent_id VARCHAR(50) NOT NULL,
    to_agent_id VARCHAR(50) NOT NULL,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    message_id BIGINT NOT NULL REFERENCES messages(message_id),
    context JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_handoffs_room ON agent_handoffs (room_id, created_at DESC);

-- Grant readonly access to all tables for analytics
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO readonly_user;

-- Prevent mutations on event log (DG1.1)
CREATE OR REPLACE FUNCTION prevent_event_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'room_events table is append-only - UPDATE/DELETE forbidden';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER prevent_event_update
    BEFORE UPDATE OR DELETE ON room_events
    FOR EACH ROW EXECUTE FUNCTION prevent_event_mutation();
```


### Environment Variables

**File:** `.env.example`

```bash
# Database
DB_PASSWORD=your_secure_password_here

# JWT Authentication
JWT_SECRET=your_jwt_secret
JWT_ALGORITHM=RS256
JWT_PUBLIC_KEY_URL=https://your-auth-provider.com/.well-known/jwks.json

# Redis
REDIS_URL=redis://redis:6379

# Application
LOG_LEVEL=INFO
WORKERS_PER_CONTAINER=1  # uvicorn workers (4 containers = 4 total workers)

# PydanticAI / LLM
OPENAI_API_KEY=your_openai_key
```


### Quick Start Commands

```bash
# 1. Copy environment template
cp .env.example .env
# Edit .env with your credentials

# 2. Build and start all services
docker-compose up --build -d

# 3. Check health
curl http://localhost/health

# 4. View logs
docker-compose logs -f fastapi

# 5. Run tests
docker-compose exec fastapi pytest

# 6. Scale workers
docker-compose up -d --scale fastapi=8  # Scale to 8 workers
```


***

## Appendix A: Quick Reference Guide

### Finding What You Need

- **"What data do I need?"** → §3 Domain Model (E1, P1-P6)
- **"Who owns this data?"** → §4 Services + Domain Object's "Owner Service"
- **"What can the system do?"** → §5 Requirements (R1-R5)
- **"How do I call this?"** → §6 Contracts (C1-C4)
- **"What am I not allowed to do?"** → §7 Design Guardrails (DG1-DG5)
- **"Why was this decided?"** → §1 Patterns (AP1-AP5) + §2 Constraints (AC)
- **"How do I deploy?"** → §10 Deployment Configuration


### Reviewing a Requirement

For any requirement R\#, trace:

1. **R\# → E\#/P\#:** What data does it touch?
2. **P\# → S\#:** Who owns that data?
3. **S\# → C\#:** What APIs implement this?
4. **R\# → AC\#:** What constraints apply?
5. **AC\# → DG\#:** What guardrails enforce this?

### Implementing a Service

For any service S\#, verify:

1. All Domain Objects (E\#/P\#) you own are defined in §3
2. All Services (S\#) you depend on are listed in your "Depends On" section
3. All Contracts (C\#) you provide map to Requirements (R\#)
4. All Constraints (AC\#) that affect you have corresponding Guardrails (DG\#) you must follow

### Event Flow Example

User sends message → Agent responds:

```
1. Client: WebSocket message.send → S5
2. S5: Validates auth (S1), checks room access
3. S5: emit_event("message.user") → E1 + P4 (S3)
4. S5: Calls S4.run_agent()
5. S4: Fetches context from S3.get_messages() (P4)
6. S4: Invokes PydanticAI agent.run()
7. Agent: Calls tool run_sql_query
8. Tool: emit_event("step.start") → E1 + P5
9. Tool: Executes query via pg_duckdb
10. Tool: emit_event("step.end") → E1 + P5
11. Tool: Returns result to LLM
12. LLM: Generates response text
13. S4: Streams tokens → S5 → Redis → All clients (ephemeral)
14. S4: emit_event("message.assistant") → E1 + P4 (persistent)
15. S5: Publishes message.assistant to Redis → Clients
```


***

## Appendix B: Agent Configuration

### Registered Agents

**File:** `agents/registry.py`

```python
AGENT_REGISTRY = {
    "customer_support": {
        "model": "openai:gpt-4",
        "system_prompt": "You are a helpful customer support agent...",
        "tools": ["run_sql_query", "search_knowledge_base", "transfer_to_agent"],
        "transfer_targets": ["technical_support", "billing"]
    },
    "technical_support": {
        "model": "openai:gpt-4",
        "system_prompt": "You are a technical support specialist...",
        "tools": ["run_sql_query", "run_diagnostic", "transfer_to_agent"],
        "transfer_targets": ["customer_support", "engineering_escalation"]
    },
    "billing": {
        "model": "openai:gpt-3.5-turbo",
        "system_prompt": "You handle billing inquiries...",
        "tools": ["query_invoices", "process_refund", "transfer_to_agent"],
        "transfer_targets": ["customer_support"]
    }
}
```


### Tool Definitions (AG-UI Compatible)

```python
# Example: SQL query tool with AG-UI schema
from pydantic_ai import Tool

sql_query_tool = Tool(
    name="run_sql_query",
    description="Execute a SQL query against the analytics database",
    parameters={
        "query": {
            "type": "string",
            "description": "The SQL SELECT query to execute"
        }
    },
    ag_ui_metadata={
        "display_name": "Database Query",
        "category": "analytics",
        "requires_confirmation": False
    }
)
```


***

**END OF TECHNICAL SPECIFICATION**

***

**Implementation Status:** ✅ Ready to build

**Next Steps:**

1. Review and approve this specification with engineering board
2. Set up GitHub repository with this spec as `SPEC.md`
3. Initialize Docker environment: `docker-compose up -d`
4. Implement services in order: S1 → S2 → S3 → S4 → S5
5. Write tests following DG5.x as you go
6. Ship v1 🚀

**Questions or clarifications?** Reference the section numbers and cross-references above. Every decision is traceable.

**Let's build this thing.** 🔥

