# TinyFoot-Minimog Integration Technical Specification

**Version:** 0.X  
**Document Type:** Implementation-Ready System Specification  
**Status:** REJECTED
**Last Updated:** December 11, 2025  
**Approvers:** [Pending]

***

## 0. Document Structure and Cross-Reference Guide

This specification defines the integration of Minimog's multi-user, multi-agent conversational system into TinyFoot's story creation platform. It is designed as an **interdependent system** where each section builds upon and validates previous sections.

**Rationale:** Minimog's core value is enabling collaborative story development where:
- Multiple authors can work together in shared spaces
- Multiple AI agents can participate as room members
- All participants see all messages in real-time
- Agents are first-class participants, not external services

### Cross-Reference Notation

- **AP#** - Architectural Pattern (e.g., AP1, AP2)
- **AC#.#** - Assumption/Constraint (e.g., AC1.1, AC2.3)
- **D#** - Domain Object (e.g., D1, D2)
- **E#** - Event (when using event sourcing)
- **P#** - Projection/Read Model (when using CQRS)
- **S#** - Service (e.g., S1, S2)
- **R#.#** - Requirement (e.g., R1.1, R3.2)
- **C#.#** - Contract (e.g., C1.1, C2.3)
- **DG#.#** - Design Guardrail (e.g., DG1.1, DG2.5)

### Section Dependencies

```
Architectural Patterns (AP1-AP5)
    ↓
Assumptions & Constraints (AC1.1-AC5.3)
    ↓
Domain Model (D1-D4, E1-E6, P1-P6)
    ↓
Services (S1-S5)
    ↓
Requirements (R1.1-R5.3)
    ↓
Contracts (C1.1-C3.3)
    ↓
Design Guardrails (DG1.1-DG5.3)
```

### Phased Implementation Approach

This specification supports a **steel thread** implementation approach across 5 phases:

**Phase 0:** Infrastructure (Redis, connection pooling)  
**Phase 1:** Event Sourcing + Room Management (rooms, participants, events)  
**Phase 2:** Multi-User Multi-Agent Integration (agents as room participants)  
**Phase 3:** Frontend Multi-User UI (room list, participant management)  
**Phase 4:** Real-Time Streaming (WebSocket, token streaming)  
**Phase 5:** Advanced Multi-Agent (agent handoffs, tool tracking)

Each phase delivers end-to-end working value and can be deployed independently.

### Completeness Validation Checklist

Before finalizing this specification, verify:

- [x] Every Domain Object (D#) is owned by exactly one Service (S#)
- [x] Every Service (S#) declares dependencies on other Services
- [x] Every Requirement (R#) explicitly references Domain Objects and Services
- [x] Every Constraint (AC#) has corresponding Design Guardrails (DG#)
- [x] Every Contract (C#) maps to at least one Requirement (R#)
- [x] All technology choices have corresponding Assumptions/Constraints
- [x] No circular service dependencies exist
- [x] Multi-user concurrency scenarios reference ordering and authorization
- [x] Data storage patterns consistent across all Domain Objects

***

## 1. Architectural Patterns

**Purpose:** Define foundational architectural decisions that constrain all subsequent design choices.

### AP1. Event Sourcing as System of Record

**Pattern Type:** Event Sourcing + Append-Only Log

**Description:** All state changes in the conversational system are recorded as immutable events in a single event log table. This event log is the only authoritative source of truth. All queryable tables are materialized projections derived from events.

**Implications:**
- **Constraint:** All business logic must emit events; no direct state mutation outside event writes
- **Impact on consistency:** Strong consistency within single room via ordered event log
- **Impact on services:** Services emit events and update projections transactionally
- **Audit capability:** Complete audit trail with no additional logging infrastructure
- **Replay capability:** System state can be rebuilt from event log

**Contradicts:** Traditional CRUD patterns, direct table mutations

**Justification:** Event sourcing provides:
1. Complete conversation history for AI context building
2. Ability to replay conversations for debugging and analysis
3. Natural fit for multi-user scenarios where ordering matters
4. Foundation for future features (conversation analytics, time travel)

***

### AP2. Multi-User Rooms with Heterogeneous Participants

**Pattern Type:** Multi-Party Collaborative Spaces

**Description:** The fundamental unit of interaction is a Room, which contains multiple participants of different types (human users and AI agents). All participants have equal standing in the event log - messages from users and agents are both first-class events. Rooms manage membership explicitly through a participants relation.

**Implications:**
- **Constraint:** Authorization is room-scoped, not session-scoped
- **Impact on data model:** Requires explicit participant tracking table
- **Impact on agents:** Agents are room members, not external services
- **Impact on UI:** Must show all participants and attribute messages correctly

**Contradicts:** Single-user session models, agent-as-service patterns

**Justification:** 
1. Core to value proposition of collaborative story development
2. Enables multiple authors to work together on stories
3. Allows multiple specialized agents in same conversation
4. Provides foundation for future social features

***

### AP3. CQRS with Transactional Projections

**Pattern Type:** Command Query Responsibility Segregation

**Description:** Write path (commands) appends events to the event log. Read path (queries) uses optimized projection tables. Critically, projections are updated in the **same database transaction** as event writes to ensure strong consistency.

**Implications:**
- **Constraint:** All reads use projections; never parse event log for business queries
- **Impact on performance:** Read-optimized indexes on projections; write path has transaction overhead
- **Impact on deployment:** Projection tables must migrate alongside event schema changes
- **Consistency model:** Read-after-write consistency (not eventual consistency)

**Contradicts:** Eventual consistency patterns, separate write/read databases

**Justification:**
1. Provides fast read access for UI and agent context building
2. Transactional updates avoid the complexity of eventual consistency
3. Allows optimization of different query patterns
4. Maintains strong consistency guarantees users expect

***

### AP4. Real-Time Streaming via WebSocket

**Pattern Type:** Bidirectional Streaming Protocol

**Description:** Real-time updates delivered via WebSocket connections using a publish-subscribe pattern. Events written to PostgreSQL trigger publications to Redis pub/sub channels, which fan out to connected WebSocket clients. Supports streaming agent responses token-by-token.

**Implications:**
- **Constraint:** WebSocket required for real-time features; REST as fallback
- **Impact on infrastructure:** Requires Redis for ephemeral message bus
- **Impact on scaling:** Must support multiple worker processes via Redis coordination
- **Impact on UI:** Client must handle reconnection and message replay

**Contradicts:** Polling-based approaches, server-side rendering

**Justification:**
1. Enables collaborative real-time experience
2. Supports streaming agent responses for better UX
3. Scales via Redis pub/sub to multiple workers
4. Standard WebSocket protocol with clean reconnection semantics

***

### AP5. Stateless Multi-Worker Architecture

**Pattern Type:** Shared-Nothing Horizontal Scaling

**Description:** Multiple FastAPI worker processes run concurrently, coordinating via PostgreSQL (for sequence generation) and Redis (for ephemeral event streaming). No in-process state is shared between workers; all session state is reconstructed from PostgreSQL on each request or reconnection.

**Implications:**
- **Constraint:** All session state must be in PostgreSQL or reconstructible
- **Impact on deployment:** Requires load balancing across workers
- **Impact on concurrency:** Sequence generation requires coordination mechanism
- **Impact on testing:** Must test multi-worker scenarios explicitly

**Contradicts:** Single-process in-memory caching, sticky sessions

**Justification:**
1. Enables horizontal scaling for multiple concurrent users
2. Provides high availability (worker failures don't lose data)
3. Simplifies deployment (workers are identical)
4. Standard cloud-native architecture pattern

***

## 2. Assumptions and Constraints

### 2.1 Technology Stack

**Relates to:** AP1, AP2, AP3, AP4, AP5

| Component | Technology Choice | Version Constraint | Justification | Risk Reference |
|:----------|:------------------|:-------------------|:--------------|:---------------|
| Primary Database | PostgreSQL | >=15.0 | Event log durability, JSONB support, excellent transaction support | AC3.1 |
| Application Runtime | Python + FastAPI | Python 3.11+, FastAPI 0.104+ | Async-native, existing TinyFoot stack, PydanticAI compatibility | AC2.3 |
| Agent Framework | PydanticAI | >=0.0.9 | Native streaming, tool injection, type safety, Pydantic integration | AC2.4 |
| Cache/Pub-Sub | Redis | >=7.0 | Multi-worker coordination, ephemeral streaming | AC2.2 |
| Container Runtime | Docker + Compose | Docker 24+ | Existing TinyFoot deployment, reproducible environments | AC2.1 |

**Validation Questions:**

- **Are these compatible?** YES - All are async-compatible and work together in existing TinyFoot stack
- **Do these support patterns?** YES - PostgreSQL supports event sourcing (AP1), Redis enables multi-worker (AP5), FastAPI supports WebSocket (AP4)
- **Operational expertise?** Requires PostgreSQL administration, Redis operations, Docker orchestration - all already present in TinyFoot

***

### 2.2 Deployment Constraints

**Relates to:** AP5

**AC2.1 Docker Compose Deployment**
- **Statement:** Development and initial production deployment uses Docker Compose with services: `postgres`, `redis`, `fastapi` (4 workers), load balancer
- **Impacts:** S1-S5 (all services run in FastAPI workers)
- **Validation:** `docker-compose up` brings up full stack with health checks passing

**AC2.2 Multi-Worker Coordination**
- **Statement:** 4+ FastAPI workers run concurrently; Redis required for ephemeral streaming; PostgreSQL provides sequence coordination to prevent collisions
- **Impacts:** S4 (agent execution), S5 (streaming gateway), E1-E6 (sequence generation)
- **Validation:** Load test with 4 workers verifies no duplicate sequences, no lost messages

**AC2.3 Async-First Concurrency**
- **Statement:** All I/O operations (PostgreSQL, Redis, HTTP, LLM calls) must use async/await; blocking calls wrapped in thread pool executors
- **Impacts:** All services
- **Validation:** Static analysis prohibits blocking operations; performance tests verify responsiveness

**AC2.4 PydanticAI Agent Runtime**
- **Statement:** PydanticAI's native streaming capabilities used for agent execution; agents receive dependency-injected context including room details and story data
- **Impacts:** S4 (agent runner), agent implementations
- **Validation:** Agent tests verify context injection; streaming tests verify token delivery

***

### 2.3 Concurrency and Consistency Constraints

**Relates to:** AP1, AP3, AP5

**AC3.1 Event Ordering Guarantee**
- **Statement:** Events within a single room are strictly ordered by monotonically increasing sequence numbers; events across different rooms are unordered
- **Chosen Strategy:** PostgreSQL sequence generation with per-room coordination
- **Impacts:** E1 (room_events), all event emission
- **Validation:** Concurrent writes to same room never produce duplicate sequences

**AC3.2 Projection Update Semantics**
- **Statement:** Projection tables are updated in the **same PostgreSQL transaction** as event log writes for strong read-after-write consistency
- **Chosen Strategy:** Single transaction wrapping both event insert and projection update
- **Impacts:** S2, S3, S4 (all event-emitting services)
- **Validation:** Test queries projection immediately after event write; data must be visible

**AC3.3 Room-Based Authorization**
- **Statement:** Users can only read/write in rooms where they are active participants; agents can only act in rooms where they are members
- **Impacts:** All room operations (S2, S3, S4, S5)
- **Validation:** Tests verify non-participants receive 403 errors

***

### 2.4 Performance and Scale Assumptions

**Relates to:** AP5

| Metric | Assumed Load | Design Ceiling | Degradation Behavior |
|:-------|:-------------|:---------------|:---------------------|
| Concurrent Users | 50 | 200 | Queue requests, return 503 after timeout |
| Messages/Second (per room) | 5 | 20 | Backpressure via client-side rate limiting |
| Room Event Read Latency (p95) | <100ms | <500ms | Serve from projection cache |
| Event Log Growth | 10K events/day | 10M events | Partition room_events table by time |
| Context Building Latency | <500ms | <2s | Limit message history to last 20 messages |

**AC4.1 Connection Pool Sizing**
- **Statement:** Each FastAPI worker maintains up to 10 PostgreSQL connections (4 workers = 40 total); PostgreSQL max_connections must be ≥50
- **Impacts:** Database configuration
- **Validation:** Monitor connection usage under load

**AC4.2 Message History Limits**
- **Statement:** Agent context limited to last 20 messages plus story outline; total context <6000 words to fit in LLM windows
- **Impacts:** S3 (context provider), agent implementations
- **Validation:** Token counting tests verify limits respected

***

### 2.5 Security and Authorization Constraints

**Relates to:** AP2, AP4

**AC5.1 JWT-Based Authentication**
- **Statement:** All requests include JWT in Authorization header; FastAPI dependency validates and extracts user_id; WebSocket connections validate JWT during handshake
- **Impacts:** S1 (identity service), all API contracts
- **Validation:** Requests without JWT return 401; expired JWT returns 401

**AC5.2 Room-Level Authorization**
- **Statement:** Authorization check required before any room operation: "Is user X an active participant in room Y?"
- **Enforcement:** Application-level checks before operations (not database row-level security)
- **Impacts:** S2, S3, S4, S5
- **Validation:** Tests verify non-participants cannot access room resources

**AC5.3 Agent Authorization**
- **Statement:** Agents can only be invoked in rooms where they are registered participants; agent responses attributed to agent's participant_id
- **Impacts:** S4 (agent runner), P3 (room_participants)
- **Validation:** Tests verify agents cannot respond in rooms where not registered

***

## 3. Domain Model

**Purpose:** Define authoritative data structures representing system state.

### Domain Object Hierarchy

```
Rooms (D1) ──┬── Created by User
             ├── Has many Participants (D2)
             │   ├── User Participants
             │   └── Agent Participants
             ├── Contains Events (E1-E6)
             └── Materializes to Projections (P1-P6)

Users (D3) ──── Participates in Rooms
              └── Owns Stories (D4)

Stories (D4) ── Provides context for Room conversations
```

***

### D1. Room

**Owner Service:** S2 (Room Management)  
**Pattern Context:** AP2 (Multi-User Rooms)  
**Related Constraints:** AC3.3, AC5.2

**Purpose:** Represents a collaborative space where multiple users and agents can converse about story development.

**Conceptual Fields:**

| Field Concept | Type Concept | Nullable | Pattern Rationale | Constraint Reference |
|:--------------|:-------------|:---------|:------------------|:---------------------|
| room_id | Unique identifier | No | AP2 - Primary key for room entity | - |
| title | Short text | Yes | AP2 - Human-readable room name | - |
| created_by | User reference | No | AP2 - Room creator (becomes owner) | AC5.2 |
| is_group | Boolean | No | AP2 - Distinguishes 1:1 vs multi-user | - |
| room_type | Category | Yes | AP2 - 'story_discussion', 'general', etc. | - |
| story_id | Story reference | Yes | Integration - Optional story context | - |
| created_at | Timestamp | No | AP1 - Audit trail | - |
| last_activity | Timestamp | No | AP3 - Query optimization for room lists | - |

**Relationships:**
- **Used By:** D2 (RoomParticipant) as foreign key
- **References:** D3 (User) for created_by, D4 (Story) for story_id

**Lifecycle:**
- **Created by:** S2.create_room() operation
- **Modified by:** S2.update_room() for metadata changes
- **Deleted/Archived:** Soft delete possible; hard delete requires cascade to participants and events

**Uniqueness Constraints:**
- None required (titles can duplicate)

**Indexes Required:**
- created_by + last_activity (supports "my rooms" query from R2.1)
- story_id where not null (supports "rooms for this story" query)

***

### D2. RoomParticipant

**Owner Service:** S2 (Room Management)  
**Pattern Context:** AP2 (Multi-User Rooms)  
**Related Constraints:** AC3.3, AC5.2, AC5.3

**Purpose:** Explicitly tracks which users and agents are members of which rooms, enabling room-based authorization.

**🔍 CRITICAL ARCHITECTURAL DECISION:** This entity is the **foundation of multi-user architecture**. Unlike single-user sessions, rooms require explicit participant tracking to support:
- Multiple human users in same room
- Multiple AI agents in same room
- Room-based authorization
- Participant management (invite, remove, leave)

**Conceptual Fields:**

| Field Concept | Type Concept | Nullable | Pattern Rationale | Constraint Reference |
|:--------------|:-------------|:---------|:------------------|:---------------------|
| room_id | Room reference | No | AP2 - Part of composite key | - |
| participant_id | Identifier | No | AP2 - Part of composite key (user OR agent) | AC5.3 |
| participant_type | Enum | No | AP2 - Distinguishes 'user' vs 'agent' | AC5.3 |
| role | Enum | No | AP2 - 'owner', 'member', 'agent' | AC5.2 |
| is_active | Boolean | No | AP2 - Soft delete for participants | - |
| joined_at | Timestamp | No | AP1 - Audit trail | - |
| left_at | Timestamp | Yes | AP1 - Audit trail for departures | - |

**Relationships:**
- **References:** D1 (Room), D3 (User) when participant_type='user'

**Lifecycle:**
- **Created by:** S2.add_participant() when user joins or agent added
- **Modified by:** S2.update_participant() for role changes; S2.remove_participant() sets is_active=false
- **Deleted/Archived:** Soft delete via is_active; maintains historical record

**Uniqueness Constraints:**
- (room_id, participant_id, participant_type) must be unique

**Indexes Required:**
- (participant_id, participant_type, is_active) where is_active=true (supports "which rooms is user in?" query from R2.1)
- (room_id, is_active) where is_active=true (supports "who's in this room?" query)

**🔍 ARCHITECTURAL NOTE:** Agent participants use stable UUIDs generated from agent names (e.g., UUID5 namespace). This allows agents to be referenced consistently across rooms.

***

### D3. User

**Owner Service:** S1 (Identity & Authorization)  
**Pattern Context:** AP2 (Multi-User Rooms)  
**Related Constraints:** AC5.1

**Purpose:** Represents authenticated users who can participate in rooms and create stories.

**Conceptual Fields:**

| Field Concept | Type Concept | Nullable | Pattern Rationale | Constraint Reference |
|:--------------|:-------------|:---------|:------------------|:---------------------|
| user_id | Unique identifier | No | Existing TinyFoot pattern | - |
| external_id | External identity | No | AC5.1 - From JWT 'sub' claim | AC5.1 |
| email | Email address | No | Existing TinyFoot pattern | - |
| display_name | Short text | No | AP2 - Shown in participant lists | - |
| avatar_url | URL | Yes | AP2 - Visual identification | - |

**Relationships:**
- **Used By:** D1 (Room) for created_by, D2 (RoomParticipant)

**Lifecycle:**
- **Created by:** S1 on first JWT validation (upsert pattern)
- **Modified by:** S1 via admin API (future feature)
- **Deleted/Archived:** Soft delete via is_active flag

***

### D4. Story

**Owner Service:** Existing TinyFoot story service  
**Pattern Context:** Integration with existing TinyFoot domain  
**Related Constraints:** AC4.2

**Purpose:** Provides contextual information for room conversations. Existing TinyFoot domain object.

**Relevant Fields for Integration:**
- story_id - Referenced by D1 (Room)
- title, description - Included in agent context
- nodes - Story structure provided to agents (limited to prevent context overflow)

**🔍 INTEGRATION NOTE:** This spec does not modify Story domain object. Integration is read-only: rooms reference stories for context, but room conversations don't modify stories directly.

***

### Event Sourcing Domain Objects

### E1. room_events (Event Log)

**Owner Service:** S3 (Event Emitter)  
**Pattern Context:** AP1 (Event Sourcing)  
**Related Constraints:** AC3.1, AC3.2

**Purpose:** Immutable, append-only log of every state change in the conversational system. This is the source of truth.

**Conceptual Structure:**

| Field Concept | Type Concept | Nullable | Pattern Rationale | Constraint Reference |
|:--------------|:-------------|:---------|:------------------|:---------------------|
| event_id | Monotonic integer | No | AP1 - Global ordering | - |
| room_id | Room reference | No | AP1 - Partition key | AC3.1 |
| room_sequence | Per-room integer | No | AP1 - Room-specific ordering | AC3.1 |
| event_type | Event type string | No | AP1 - Polymorphic events | - |
| payload | Structured data | No | AP1 - Event-specific data | - |
| created_at | Timestamp | No | AP1 - Audit trail | - |

**Uniqueness Constraints:**
- event_id is globally unique (auto-increment)
- (room_id, room_sequence) must be unique per AC3.1

**Indexes Required:**
- (room_id, room_sequence) for event replay (R3.3)
- (event_type, created_at) for analytics queries

**Immutability Enforcement:**
- Database trigger prevents UPDATE/DELETE operations (DG1.1)
- Application code has no mutation logic

***

### E2. room.created Event

**Owner Service:** S2 (Room Management)  
**Related Projections:** P1 (rooms)

**Purpose:** Records room creation.

**Payload Concepts:**
- room_id
- title
- created_by
- is_group
- room_type
- story_id (optional)

**Ordering:** First event in room's sequence

***

### E3. participant.joined Event

**Owner Service:** S2 (Room Management)  
**Related Projections:** P3 (room_participants)

**Purpose:** Records user or agent joining room.

**Payload Concepts:**
- room_id
- participant_id
- participant_type ('user' or 'agent')
- role ('owner', 'member', 'agent')
- invited_by (optional)

***

### E4. participant.left Event

**Owner Service:** S2 (Room Management)  
**Related Projections:** P3 (room_participants)

**Purpose:** Records user or agent leaving room.

**Payload Concepts:**
- room_id
- participant_id
- participant_type

***

### E5. message.user Event

**Owner Service:** S3 (Event Emitter), triggered by S5 (UI Gateway)  
**Related Projections:** P4 (messages)

**Purpose:** Records user sending message.

**Payload Concepts:**
- sender_id (user's participant_id)
- content (message text)
- metadata (optional structured data)

**Ordering:** Follows AC3.1 strict room ordering

***

### E6. message.agent Event

**Owner Service:** S4 (Agent Runner)  
**Related Projections:** P4 (messages)

**Purpose:** Records agent response completion.

**Payload Concepts:**
- agent_id (agent's participant_id)
- agent_name (e.g., 'story_advisor')
- content (response text)
- model (LLM model used)
- metadata (optional tool execution references)

**Ordering:** Follows AC3.1 strict room ordering

***

### CQRS Projections

### P1. rooms Projection

**Source Events:** E2 (room.created)  
**Owner Service:** S2 (Room Management)  
**Update Semantics:** Transactional with event write (AC3.2)

**Purpose:** Fast queryable room metadata for listing and display.

**Conceptual Fields:** Match D1 (Room) domain object

**Projection Logic:** On room.created event, insert row with event payload data

**Rebuild Strategy:** Replay all room.created events ordered by event_id

***

### P2. room_participants Projection

**Source Events:** E3 (participant.joined), E4 (participant.left)  
**Owner Service:** S2 (Room Management)  
**Update Semantics:** Transactional with event write (AC3.2)

**Purpose:** Authorization queries - "Is user X in room Y?"

**Conceptual Fields:** Match D2 (RoomParticipant) domain object

**Projection Logic:**
- On participant.joined: Insert or reactivate participant record
- On participant.left: Set is_active=false, record left_at timestamp

**Rebuild Strategy:** 
1. Replay all participant.joined events (insert records)
2. Replay all participant.left events (mark inactive)
3. Chronological order critical

***

### P3. messages Projection

**Source Events:** E5 (message.user), E6 (message.agent)  
**Owner Service:** S3 (Event Emitter)  
**Update Semantics:** Transactional with event write (AC3.2)

**Purpose:** Fast chronological message retrieval for chat UI and agent context.

**Conceptual Fields:**

| Field Concept | Type Concept | Purpose |
|:--------------|:-------------|:--------|
| message_id | Unique identifier | Message identity |
| room_id | Room reference | Partition key |
| sender_id | Participant reference | Message attribution |
| sender_type | Enum ('user'/'agent') | Distinguish user vs agent messages |
| agent_name | String (nullable) | Agent identifier if sender_type='agent' |
| content | Text | Message content |
| metadata | Structured data | Extensible (e.g., tool references) |
| created_at | Timestamp | Display ordering |

**Projection Logic:**
- On message.user: Insert message with sender_type='user'
- On message.agent: Insert message with sender_type='agent', populate agent_name

**Rebuild Strategy:** Replay all message.user and message.agent events chronologically

**Indexes Required:**
- (room_id, created_at DESC) for message list queries (R3.1)
- sender_id for "messages by user" queries

***

## 4. Services and Boundaries

**Purpose:** Define computational boundaries and ownership of domain objects.

### Service Dependency Graph

```
        ┌────────────────────────────────────────────┐
        │  S5: UI Gateway (WebSocket + REST)        │
        └────────────┬───────────────────────────────┘
                     │
        ┌────────────┴────────────┬───────────────┐
        │                         │               │
        ▼                         ▼               ▼
  ┌──────────────┐      ┌─────────────────┐   ┌──────────────┐
  │ S2: Room     │◄─────│ S4: Agent       │   │ S3: Event    │
  │ Management   │      │ Runner          │   │ Emitter      │
  └──────┬───────┘      └────────┬────────┘   └──────┬───────┘
         │                       │                    │
         │                       │                    │
         ▼                       ▼                    ▼
  ┌────────────────────────────────────────────────────┐
  │ S1: Identity & Authorization                       │
  └────────────────────────────────────────────────────┘
```

**Validation:** No circular dependencies ✓

***

### S1. Identity & Authorization Service

**Pattern Context:** AP2 (Multi-User), AP5 (Stateless)  
**Related Constraints:** AC5.1, AC5.2, AC5.3

**Responsibilities:**
- Validate JWT tokens and extract user_id from claims
- Upsert user records on first authentication
- Provide authorization check: "Is user X an active participant in room Y?"
- Provide authorization check: "Is agent A registered in room Y?"

**Owns Domain Objects:**
- D3 (User) - Create on first auth, manage lifecycle

**Depends On Services:**
- None (leaf service)

**Provides Contracts To:**
- S2, S3, S4, S5 - C1.1 (Authorization Check)
- External API - C2.1 (User Profile)

**State Management:**
- Users stored in PostgreSQL users table
- No caching (queries fast with indexes)

**Concurrency Model:**
- Stateless; safe for multi-worker (AC2.2)
- User upsert uses ON CONFLICT for idempotency

**Authorization Model:**
- **This IS the authorization service**
- Enforces AC5.2 via check_room_access(user_id, room_id) helper
- Enforces AC5.3 via check_agent_access(agent_id, room_id) helper

***

### S2. Room Management Service

**Pattern Context:** AP1 (Event Sourcing), AP2 (Multi-User), AP3 (CQRS)  
**Related Constraints:** AC3.2, AC3.3, AC5.2

**Responsibilities:**
- Create rooms and emit room.created events
- Add/remove participants (users and agents) with corresponding events
- List rooms for a user (query P1, P2)
- Manage room metadata (title, type, story context)

**Owns Domain Objects:**
- D1 (Room) - Full lifecycle management
- D2 (RoomParticipant) - Participant membership
- P1 (rooms projection) - Maintain consistency
- P2 (room_participants projection) - Maintain consistency
- E2, E3, E4 (room/participant events) - Emit these event types

**Depends On Services:**
- S1 - User identity validation, authorization checks
- S3 - Event emission mechanism

**Provides Contracts To:**
- S4, S5 - C1.2 (Room Existence Check)
- External API - C2.2 (Room Management REST API)

**State Management:**
- Writes events to E1 via S3
- Updates projections P1, P2 in same transaction (AC3.2)

**Concurrency Model:**
- Room creation idempotent (client-provided room_id or generate)
- Participant add/remove uses event log ordering to resolve conflicts

**Authorization Model:**
- Only room owner can add/remove participants (checked via P2.role)
- Users can leave any room they're in
- Agents added by room owners or system


***

### S3. Event Emitter & History Service

**Pattern Context:** AP1 (Event Sourcing), AP3 (CQRS)  
**Related Constraints:** AC3.1, AC3.2, AC3.3

**Responsibilities:**
- Provide emit_event() helper for all services to write to event log
- Coordinate event sequence generation per room (AC3.1)
- Update projections transactionally with event writes (AC3.2)
- Publish events to Redis for real-time delivery (AP4)
- Retrieve ordered message history for rooms (query P3)
- Build AI-agent-compatible context from message history

**Owns Domain Objects:**
- E1 (room_events) - Coordinate writes (shared ownership pattern)
- P3 (messages projection) - Maintain consistency
- E5, E6 (message events) - Coordinate emission

**Depends On Services:**
- S1 - Authorization checks before returning history
- S2 - Room existence validation

**Provides Contracts To:**
- S4 - C1.3 (Context Provider for agents)
- S5 - C3.1 (Message History for UI)
- S2, S4 - C1.4 (Event Emission Helper)

**State Management:**
- Writes to E1, maintains P3 projection
- Publishes to Redis after successful transaction
- No caching (PostgreSQL query with index <10ms)

**Concurrency Model:**
- Event writes acquire per-room sequence coordination (AC3.1)
- Reads are lock-free from P3 projection
- Sequence generation via PostgreSQL mechanisms (SEQUENCE per room - creates more objects, but much simpler and can be refactored later)

**Authorization Model:**
- Calls S1.check_room_access() before returning messages

***

### S4. Agent Runner Service

**Pattern Context:** AP2 (Multi-User), AP1 (Event Sourcing)  
**Related Constraints:** AC2.3, AC2.4, AC4.2, AC5.3

**Responsibilities:**
- Initialize PydanticAI agents with dependency-injected room context - ensure explicit deps_type and RunContext[T] typing
```python
@dataclass
class AgentDeps:
    room_id: UUID
    room_context: RoomContext  # from C1.3
    event_emitter: EventEmitter  # from C1.4

agent = Agent('openai:gpt-4', deps_type=AgentDeps)

@agent.tool
async def analyze_story(ctx: RunContext[AgentDeps]) -> str:
    messages = ctx.deps.room_context.messagehistory
    ...
```
- Execute agent.run() with streaming enabled (Phase 4)
- Coordinate tool execution during agent runs
- Emit message.agent events after response generation
- Manage agent context building (story + message history)
- Register agents as room participants when added to rooms

**Owns Domain Objects:**
- E6 (message.agent events) - Emit after agent responses
- Agent implementations (code artifacts, not data)

**Depends On Services:**
- S1 - Authorization (agents can only act in their rooms)
- S2 - Room participant registration for agents
- S3 - Message history for context building, event emission

**Provides Contracts To:**
- S5 - C1.5 (Agent Invocation)
- External - C2.3 (Agent Management API for adding agents to rooms)

**State Management:**
- Stateless - all context from S3 on each invocation
- Agents are code (PydanticAI Agent instances) not data
- Agent-to-room mapping via D2 (RoomParticipant)

**Concurrency Model:**
- Each agent run is an async task (can run multiple per worker)
- Thread-safe via stateless design
- Context built fresh per invocation from projections

**Authorization Model:**
- Inherits from S5 (room access already checked)
- Verifies agent is room participant before responding (AC5.3)

**🔍 ARCHITECTURAL SHIFT:** Unlike original plan where agents were external, agents are now room participants. Agent responses attributed to agent participant_id in D2, enabling proper multi-user message attribution.

***

### S5. UI Gateway (WebSocket + REST Server)

**Pattern Context:** AP4 (Real-Time Streaming), AP5 (Multi-Worker)  
**Related Constraints:** AC2.2, AC3.3, AC5.1

**Responsibilities:**
- Terminate WebSocket connections for real-time updates
- Authenticate connections via JWT (AC5.1)
- Subscribe to Redis room channels for event broadcasting
- Forward user messages to S3 → S4 pipeline
- Provide REST endpoints for room management and message history
- Handle reconnection with event replay from last sequence

**Owns Domain Objects:**
- None (routing layer only)

**Depends On Services:**
- S1 - JWT validation, authorization
- S2 - Room existence/membership checks, room CRUD
- S3 - Message history for replay, event emission
- S4 - Agent invocation

**Provides Contracts To:**
- External WebSocket clients - C3.1 (WebSocket Protocol)
- External HTTP clients - C2.2 (Room Management), C2.4 (Message History)

**State Management:**
- Stateless - no in-process session state
- Reconnection state rebuilt from E1 via client-provided last_sequence

**Concurrency Model:**
- Multiple workers handle different WebSocket connections
- Redis pub/sub ensures all workers receive room events
- No worker affinity required (any worker can handle any connection)

**Authorization Model:**
- Validates JWT on WebSocket handshake and HTTP requests
- Checks room membership before allowing subscription (via S1)

***

## 5. Requirements with Explicit Cross-References

### R1. Multi-User Room Foundation

#### R1.1 User Identity Management

**Description:** System must authenticate users via JWT and maintain user profiles.

**Domain Impact:** D3 (User)  
**Service Owner:** S1 (primary)  
**Constraint Reference:** AC5.1  
**Pattern Justification:** AP2 (multi-user requires identity), AP5 (stateless JWT)

**Contracts Required:**
- C1.1 (JWT Validation)
- C2.1 (User Profile API)

**Acceptance Criteria:**
- [ ] Valid JWT extracts 'sub' claim to external_id
- [ ] User record created/updated on first authentication
- [ ] Invalid JWT returns 401
- [ ] Expired JWT returns 401
- [ ] User profile includes display_name, email for participant display

**Edge Cases:**
- User changes email in auth provider → Update on next login
- JWT missing required claims → Reject with 400

***

#### R1.2 Multi-User Room Creation

**Description:** Users must create rooms that can contain multiple participants (users and agents).

**Domain Impact:** D1 (Room), D2 (RoomParticipant)  
**Service Owner:** S2 (primary), S1 (auth)  
**Constraint Reference:** AC3.2, AC3.3  
**Pattern Justification:** AP2 (multi-user rooms core feature)

**Contracts Required:**
- C2.2 (POST /rooms)

**Acceptance Criteria:**
- [ ] Room creator automatically added as owner participant
- [ ] room.created and participant.joined events emitted transactionally
- [ ] Room visible in creator's room list immediately (AC3.3)
- [ ] Can specify optional story context for room
- [ ] Room type can be set (e.g., 'story_discussion')

**Edge Cases:**
- Empty title → Use default "Untitled Room"
- Story_id reference invalid → Create room without story context

**🔍 CHANGE FROM PLAN:** Original plan had "chat sessions" owned by single user. This requirement reflects multi-user rooms architecture.

***

#### R1.3 Room Membership & Authorization

**Description:** System must track room participants (users and agents) and enforce room-based access control.

**Domain Impact:** D2 (RoomParticipant)  
**Service Owner:** S2 (membership), S1 (authorization)  
**Constraint Reference:** AC3.3, AC5.2, AC5.3  
**Pattern Justification:** AP2 (explicit participant tracking)

**Contracts Required:**
- C1.1 (check_room_access)
- C2.2 (POST /rooms/{room_id}/participants)

**Acceptance Criteria:**
- [ ] Only room owners can add user participants
- [ ] Room owners can add agents to rooms
- [ ] Users can leave rooms voluntarily
- [ ] Inactive participants cannot read/write messages
- [ ] Authorization checked before every room operation
- [ ] Agents must be room participants to respond

**Edge Cases:**
- User removed while connected → WebSocket closed with 403
- Last participant leaves → Room remains (orphaned until garbage collection)
- Agent added to room → participant.joined event with participant_type='agent'

**🔍 CRITICAL FEATURE:** This requirement enables the core multi-user capability. Without explicit participant tracking, cannot support multiple users or agents.

***

### R2. Message Lifecycle & History

#### R2.1 User Message Persistence

**Description:** Users send messages that are persisted as immutable events visible to all room participants.

**Domain Impact:** E1 (room_events), E5 (message.user), P3 (messages)  
**Service Owner:** S5 (ingestion), S3 (persistence)  
**Constraint Reference:** AC3.1, AC3.2  
**Pattern Justification:** AP1 (event sourcing), AP2 (multi-party visibility)

**Contracts Required:**
- C3.1 (WebSocket message.send) or C2.4 (POST message via REST)

**Acceptance Criteria:**
- [ ] Message assigned monotonic room_sequence
- [ ] message.user event written to E1
- [ ] Projection P3 updated in same transaction
- [ ] All room participants receive real-time notification via Redis

**Edge Cases:**
- Empty message → Rejected with 400
- Message >10KB → Truncated with warning
- User not in room → Rejected with 403

***

#### R2.2 Message History Retrieval

**Description:** Clients retrieve paginated message history showing all participant messages (users and agents).

**Domain Impact:** P3 (messages)  
**Service Owner:** S3 (primary), S1 (auth)  
**Constraint Reference:** AC3.3, AC4.1, AC4.2  
**Pattern Justification:** AP3 (CQRS for fast reads)

**Contracts Required:**
- C2.4 (GET /rooms/{room_id}/messages)

**Acceptance Criteria:**
- [ ] Messages returned in chronological order
- [ ] Includes both user and agent messages
- [ ] Message attribution shows sender (user or agent name)
- [ ] Pagination via cursor (before message_id)
- [ ] Default limit 50, max 100 messages
- [ ] Agent context loading limited to last 20 messages (AC4.2)

**Edge Cases:**
- No messages → Empty array
- Invalid cursor → 400 error

***

#### R2.3 Event Immutability

**Description:** Events must be immutable once written (append-only).

**Domain Impact:** E1 (room_events)  
**Service Owner:** S3 (enforcer)  
**Constraint Reference:** AC3.1  
**Pattern Justification:** AP1 (event sourcing)

**Contracts Required:**
- None (architectural constraint)

**Acceptance Criteria:**
- [ ] No UPDATE operations on room_events table
- [ ] No DELETE operations on room_events table
- [ ] Application code has no mutation logic
- [ ] Database constraint/trigger prevents mutations

**Edge Cases:**
- Moderation needed → Emit new event (e.g., message.hidden), don't mutate original

***

### R3. Agent Execution & Multi-Agent Coordination

#### R3.1 Agent Invocation with Room Context

**Description:** Agents execute with full room context (participants, story, message history) and respond as room participants.

**Domain Impact:** E6 (message.agent), P3 (messages), D2 (RoomParticipant)  
**Service Owner:** S4 (primary), S3 (context), S2 (participant check)  
**Constraint Reference:** AC2.3, AC2.4, AC4.2, AC5.3  
**Pattern Justification:** AP2 (agents as participants)

**Contracts Required:**
- C1.5 (run_agent)
- C1.3 (get_messages for context)

**Acceptance Criteria:**
- [ ] Agent receives room context including all participants
- [ ] Agent receives last 20 messages as context (AC4.2)
- [ ] Agent receives story outline if room has story context
- [ ] Agent verified as room participant before responding (AC5.3)
- [ ] Agent response includes agent_id as sender
- [ ] message.agent event written after response generation
- [ ] Agent context includes typed RunContext with room_id, participants, and message history

**Edge Cases:**
- Agent timeout (60s) → Emit system.error event, return partial
- Agent not in room → Rejected with 403
- Story context unavailable → Agent still responds without story context

**🔍 ARCHITECTURAL CHANGE:** Agents now room participants with participant_id, not external services. Response attribution via participant system.

***

#### R3.2 Multiple Agents per Room

**Description:** Rooms can contain multiple agent participants simultaneously, each responding based on their specialization.

**Domain Impact:** D2 (RoomParticipant), E6 (message.agent)  
**Service Owner:** S2 (agent registration), S4 (execution)  
**Constraint Reference:** AC5.3  
**Pattern Justification:** AP2 (multi-agent collaboration)

**Contracts Required:**
- C2.3 (POST /rooms/{room_id}/agents)

**Acceptance Criteria:**
- [ ] Multiple agents can be registered in single room
- [ ] Each agent has distinct participant_id
- [ ] Agent responses attributed to correct agent
- [ ] UI shows which agent responded

**Edge Cases:**
- Same agent type added twice → Use same participant_id, update metadata
- No agents in room → Valid state, users can converse

**🔍 FUTURE FEATURE:** Agent handoffs (one agent transferring to another) deferred to Phase 5. Initially, agents respond independently based on message content.

***

#### R3.3 Event Replay for State Recovery

**Description:** System state can be recovered by replaying events from event log.

**Domain Impact:** E1 (room_events), P1-P3 (all projections)  
**Service Owner:** S3 (replay mechanism)  
**Constraint Reference:** AC3.1, AC3.2  
**Pattern Justification:** AP1 (event sourcing), AP3 (projections derivable)

**Contracts Required:**
- Internal service contract (not external API)

**Acceptance Criteria:**
- [ ] Truncated projection can be rebuilt from events
- [ ] Events replayed in room_sequence order produce correct projection state
- [ ] Replay process is idempotent
- [ ] Missing events cause replay to fail loudly

**Edge Cases:**
- Partial replay (some events missing) → Error, require complete event log
- Concurrent replay and new writes → Use separate transaction for replay

***

### R4. Real-Time Multi-User Behavior

#### R4.1 Concurrent Multi-User Writes

**Description:** Multiple users send messages concurrently in same room without conflicts or lost messages.

**Domain Impact:** E1 (room_events), P3 (messages)  
**Service Owner:** S5 (ingestion), S3 (ordering)  
**Constraint Reference:** AC3.1, AC2.2  
**Pattern Justification:** AP5 (multi-worker), AP1 (event ordering)

**Contracts Required:**
- C1.1 (Authorization before write)
- C3.1 (WebSocket concurrent connections)

**Acceptance Criteria:**
- [ ] Sequence generation prevents collisions
- [ ] All messages receive unique room_sequence
- [ ] Sequence gaps allowed (e.g., 1, 2, 5, 7 is valid)
- [ ] Clients handle non-consecutive sequences

**Edge Cases:**
- 100 concurrent writes to same room → Serialized by coordination, max 1s latency
- Worker failure mid-write → Transaction rollback, no partial events

***

#### R4.2 Real-Time Event Broadcast

**Description:** All room participants receive real-time updates for new messages and room events.

**Domain Impact:** E1 (all event types)  
**Service Owner:** S5 (broadcast), S3 (emission to Redis)  
**Constraint Reference:** AC2.2, AC4.1  
**Pattern Justification:** AP4 (WebSocket streaming), AP5 (Redis pub/sub)

**Contracts Required:**
- C3.1 (WebSocket events)

**Acceptance Criteria:**
- [ ] Event written to E1 triggers Redis publish
- [ ] All workers subscribed to room receive event
- [ ] Workers forward to connected WebSocket clients
- [ ] Event includes sequence number for deduplication
- [ ] Both user and agent messages broadcast to all participants

**Edge Cases:**
- Client temporarily disconnected → Reconnects, replays from last_sequence
- Redis unavailable → Events still written to PostgreSQL, clients catch up on reconnect

***

#### R4.3 Reconnection & Replay

**Description:** Clients reconnect after disconnect and replay missed events seamlessly.

**Domain Impact:** E1 (room_events)  
**Service Owner:** S5 (replay), S3 (event query)  
**Constraint Reference:** AC3.3  
**Pattern Justification:** AP1 (event log), AP4 (WebSocket reconnection)

**Contracts Required:**
- C3.1 (WebSocket session with last_sequence)

**Acceptance Criteria:**
- [ ] Client sends last_sequence on reconnection
- [ ] Server replays events with room_sequence > last_sequence
- [ ] Replay completed before subscribing to live events
- [ ] No duplicate events received (client deduplicates by sequence)

**Edge Cases:**
- last_sequence in future → Return empty replay
- Replay >1000 events → Paginate replay in chunks

***

### R5. Story Integration

#### R5.1 Story Context for Agent Responses

**Description:** When room has story context, agents receive story outline and can reference specific story elements.

**Domain Impact:** D1 (Room.story_id), D4 (Story), S4 (context building)  
**Service Owner:** S4 (agent context), S3 (context building)  
**Constraint Reference:** AC4.2  
**Pattern Justification:** Integration with existing TinyFoot domain

**Contracts Required:**
- C1.3 (Context Provider with story data)

**Acceptance Criteria:**
- [ ] Room can reference story via story_id
- [ ] Agent context includes story title, description
- [ ] Agent context includes story outline (limited to prevent overflow)
- [ ] Agents can reference specific story nodes in responses
- [ ] Story context remains read-only (agents don't modify stories)

**Edge Cases:**
- Story deleted while room exists → Room continues, agents respond without story context
- Story too large → Include only title, description, first 10 nodes

**🔍 INTEGRATION BOUNDARY:** This requirement defines read-only integration with existing TinyFoot story domain. Future enhancement: agents could suggest story edits, but this spec keeps integration simple.

***

## 6. Contracts (APIs and Interfaces)

### C1. Service-to-Service Internal APIs

#### C1.1 Authorization Check

**Provided By:** S1 (Identity & Authorization)  
**Consumed By:** S2, S3, S4, S5  
**Implements Requirements:** R1.3, R4.1  
**Pattern Context:** AP5 (stateless)

**Functional Signature:** `check_room_access(user_id, room_id) → boolean`

**Input Concepts:**
- user_id: User identifier
- room_id: Room identifier

**Output:** Boolean (true if user is active participant)

**Authorization:** N/A (this IS the authorization check)

**Error Responses:**
- Database error → Raises exception (caller handles)

**Consistency Guarantees:**
- Read-after-write (AC3.3) - sees participant adds immediately

**Idempotency:** Yes (pure query)

**🔍 ALSO NEEDED:** `check_agent_access(agent_id, room_id)` for AC5.3

***

#### C1.2 Room Existence Check

**Provided By:** S2 (Room Management)  
**Consumed By:** S3, S4, S5  
**Implements Requirements:** R1.2

**Functional Signature:** `room_exists(room_id) → boolean`

**Input:** Room identifier  
**Output:** Boolean

***

#### C1.3 Context Provider

**Provided By:** S3 (Event Emitter & History)  
**Consumed By:** S4 (Agent Runner)  
**Implements Requirements:** R2.2, R3.1, R5.1

**Functional Signature:** `build_room_context(room_id, agent_name) → RoomContext`

**Input Concepts:**
- room_id: Room identifier
- agent_name: Agent requesting context (for personalization)

**Output Concepts:**
- room_id, room_title
- story_data (if room has story context)
- participants list (all room members)
- message_history (last 20 messages, chronological)

**Authorization:** Caller (S4) responsible for verifying agent is room participant

**Performance:** <500ms target, <2s ceiling (AC4.1)

**Context Limits:**
- Maximum 20 messages (AC4.2)
- Story outline truncated if large
- Total context <6000 words for LLM compatibility

***

#### C1.4 Event Emission Helper

**Provided By:** S3 (Event Emitter & History)  
**Consumed By:** S2, S4, S5  
**Implements Requirements:** R2.1, R2.3, R3.1

**Functional Signature:** `emit_event(room_id, event_type, payload) → sequence_number`

**Input Concepts:**
- room_id: Target room
- event_type: Event type string
- payload: Event-specific data structure

**Output:** room_sequence number assigned

**Side Effects:**
- Writes event to E1 (room_events)
- Updates corresponding projection (P1, P2, or P3) in same transaction
- Publishes event to Redis for real-time delivery

**Error Handling:**
- Sequence generation collision → Retry with backoff
- Projection update failure → Full transaction rollback

**Consistency:** Transactional (AC3.2) - event and projection update atomic

***

#### C1.5 Agent Invocation

**Provided By:** S4 (Agent Runner)  
**Consumed By:** S5 (UI Gateway)  
**Implements Requirements:** R3.1

**Functional Signature:** `run_agent(room_id, user_message, user_id, agent_name) → response`

**Input Concepts:**
- room_id: Room context
- user_message: User's message content
- user_id: User who sent message
- agent_name: Which agent to invoke
- deps_type and RunContext[T] for dependency injection

**Output:** Agent response text

**Side Effects:**
- Writes message.user event to E1 (via S3)
- Writes message.agent event to E1 after completion
- Updates P3 (messages projection)

**Error Handling:**
- Agent timeout → Raises TimeoutError
- Agent not in room → Raises AuthorizationError
- Agent execution error → Returns error message to user

**Performance:** Target <3s for simple responses, <10s for complex

**🔍 PHASE 4 EXTENSION:** Streaming version returns async iterator of text chunks

***

### C2. External HTTP/REST APIs

#### C2.1 User Profile API

**Provided By:** S1 (Identity & Authorization)  
**Consumed By:** External clients  
**Implements Requirements:** R1.1

**Endpoint:** `GET /api/v1/users/me`

**Authentication:** JWT in Authorization header (AC5.1)

**Response Concepts:**
- user_id, email, display_name, avatar_url
- created_at timestamp

**Error Responses:**
- 401 Unauthorized - Invalid/expired JWT
- 500 Internal Server Error - Database error

***

#### C2.2 Room Management API

**Provided By:** S2 (Room Management)  
**Consumed By:** External clients  
**Implements Requirements:** R1.2, R1.3

**Create Room:**
```
POST /api/v1/rooms
Authorization: Bearer <jwt>

Request Concepts:
- title, room_type (optional)
- story_id (optional)
- initial_agents (optional) - list of agent names

Response Concepts:
- room_id, title, created_by, created_at
- participant_count

Status Codes:
- 201 Created
- 400 Bad Request (invalid story_id)
- 401 Unauthorized
```

**List User Rooms:**
```
GET /api/v1/rooms
Authorization: Bearer <jwt>

Response Concepts:
- Array of room summaries (id, title, last_activity, unread_count)
- Total count

Status Codes:
- 200 OK
- 401 Unauthorized
```

**Add Participant:**
```
POST /api/v1/rooms/{room_id}/participants
Authorization: Bearer <jwt>

Request Concepts:
- participant_type ('user' or 'agent')
- user_id (if type='user')
- agent_name (if type='agent')
- role (optional, defaults to 'member')

Status Codes:
- 200 OK
- 403 Forbidden (not room owner)
- 404 Not Found (room doesn't exist)
```

***

#### C2.3 Agent Management API

**Provided By:** S4 (Agent Runner), S2 (Room Management)  
**Consumed By:** External clients  
**Implements Requirements:** R3.2

**Add Agent to Room:**
```
POST /api/v1/rooms/{room_id}/agents
Authorization: Bearer <jwt>

Request Concepts:
- agent_name (e.g., 'story_advisor')

Response Concepts:
- participant_id (agent's UUID)
- agent_name
- display_name

Status Codes:
- 201 Created
- 403 Forbidden (not room owner)
- 404 Not Found (agent not registered)
```

**List Available Agents:**
```
GET /api/v1/agents

Response Concepts:
- Array of agent metadata (name, display_name, description)

Status Codes:
- 200 OK
```

***

#### C2.4 Message History API

**Provided By:** S3 (Event Emitter & History)  
**Consumed By:** External clients  
**Implements Requirements:** R2.2

**Endpoint:** `GET /api/v1/rooms/{room_id}/messages`

**Authentication:** JWT required

**Query Parameters:**
- before (optional) - message_id for pagination
- limit (optional, default 50, max 100)

**Response Concepts:**
- Array of messages (message_id, sender_id, sender_type, content, created_at)
- has_more boolean
- next_cursor (for pagination)

**Authorization:** User must be room participant (AC3.3)

**Error Responses:**
- 403 Forbidden - User not in room
- 404 Not Found - Room doesn't exist

***

### C3. Real-Time/Streaming Protocols

#### C3.1 WebSocket Room Event Stream

**Provided By:** S5 (UI Gateway)  
**Consumed By:** WebSocket clients  
**Implements Requirements:** R2.1, R4.2, R4.3  
**Pattern Context:** AP4 (Real-Time Streaming)

**Protocol:** WebSocket

**Connection:** `ws://api.domain/ws/rooms/{room_id}`

**Handshake (Client → Server):**
```json
{
  "type": "session.create",
  "auth": {"token": "jwt_token"},
  "room_id": "uuid",
  "last_sequence": 0
}
```

**Handshake Response (Server → Client):**
```json
{
  "type": "session.created",
  "session_id": "uuid",
  "room": {
    "room_id": "uuid",
    "title": "string",
    "participants": [...]
  }
}
```

**Event Types (Server → Client):**

| Event Type | When Sent | Payload Concepts |
|:-----------|:----------|:-----------------|
| message.user | User sent message | sender_id, content, sequence |
| message.agent | Agent completed response | agent_id, agent_name, content, sequence |
| message.delta | Agent streaming (ephemeral) | content chunk |
| participant.joined | User/agent joined | participant_id, participant_type, role, sequence |
| participant.left | User/agent left | participant_id, participant_type, sequence |

**Ordering Guarantee:** All events include `sequence` (room_sequence from E1)

**Reconnection Semantics:**
1. Client sends last_sequence in handshake
2. Server replays events where room_sequence > last_sequence
3. Server subscribes to Redis for live events
4. Client receives replay THEN live events

**Backpressure Handling:**
- Ephemeral message.delta events may be dropped if client slow
- Persistent events (message.agent) never dropped - replayed on reconnect

**Error Codes:**
- 401 - Invalid JWT
- 403 - User not in room
- 4000 - Invalid message format
- 4001 - Room not found

**🔍 STILL REVIEWING** AG-UI protocol compatibility. 

***

## 7. Design Guardrails

### DG1. Data Consistency and Concurrency

**Enforces:** AP1, AP3, AC3.1, AC3.2

#### DG1.1 Event Immutability

**Rule Type:** Mandatory

**Statement:** No code may perform UPDATE or DELETE operations on room_events table. All state changes must append new events.

**Rationale:** Violating this breaks event sourcing pattern (AP1), corrupts audit trail, and makes replay impossible (R3.3).

**Validation Method:**
- Database trigger rejects mutations
- Code review checklist
- Integration test attempts UPDATE, expects error

**Applies To:**
- Services: All (S1-S5)
- Domain Objects: E1 (room_events)
- Requirements: R2.3

**Conceptual Example (Correct):**
```
To "delete" a message:
1. Emit new event: message.hidden
2. Projection shows message as hidden
3. Original message.user event remains
```

**Conceptual Anti-Pattern (Incorrect):**
```
DO NOT: UPDATE room_events SET payload = ...
DO NOT: DELETE FROM room_events WHERE ...
```

***

#### DG1.2 Transactional Projection Updates

**Rule Type:** Mandatory

**Statement:** Projection updates (P1-P3) MUST occur in the same database transaction as the event write (E1).

**Rationale:** Ensures read-after-write consistency (AC3.3). Prevents projections from diverging from event log.

**Validation Method:**
- Code review - all emit_event() calls include projection update in same transaction
- Integration test: Write event, query projection immediately, expect new data

**Applies To:**
- Services: S2, S3, S4
- Domain Objects: E1, P1-P3
- Requirements: R1.2, R2.1, R3.1

**Conceptual Pattern:**
```
Transaction Start
  ├─ Write event to E1
  ├─ Update projection P1/P2/P3
  └─ Commit (both succeed or both fail)
Publish to Redis (outside transaction)
```

***

#### DG1.3 Sequence Uniqueness Enforcement

**Rule Type:** Mandatory

**Statement:** room_sequence generation must use database coordination to prevent duplicate sequences in multi-worker environments.

**Rationale:** Prevents sequence collisions when multiple workers write to same room concurrently (AC3.1, AP5).

**Validation Method:**
- Load test: 4 workers, 100 concurrent writes to same room, verify no duplicates
- Code review: sequence generation uses coordination mechanism

**Applies To:**
- Services: S3 (emit_event helper)
- Domain Objects: E1
- Requirements: R4.1

**🔍 ARCHITECTURAL DECISION:** Specific coordination mechanism: SEQUENCE per room


***

#### DG1.4 Sparse Sequence Handling

**Rule Type:** Mandatory (Client-Side)

**Statement:** Client code must NOT assume room_sequence values are consecutive. Gaps (1, 2, 5, 7) are valid.

**Rationale:** Coordination mechanisms may create gaps. Transaction rollbacks create gaps (AC3.1).

**Validation Method:**
- Client integration test with synthetic gaps
- UI review: No "missing message" warnings for non-consecutive sequences

**Applies To:**
- Requirements: R4.1, R4.3
- Contracts: C3.1

***

### DG2. Performance and Scalability

**Enforces:** AP5, AC2.3, AC4.1, AC4.2

#### DG2.1 Async-First I/O

**Rule Type:** Mandatory

**Statement:** All I/O operations (database, Redis, HTTP, LLM calls) MUST use async/await. Blocking calls MUST be wrapped in thread pool executors.

**Rationale:** Prevents blocking event loop in multi-worker deployment (AP5). Python GIL requires async for concurrency.

**Validation Method:**
- Static analysis: Ban blocking libraries
- Code review: Check for await on all I/O
- Performance test: Measure worker responsiveness under load

**Applies To:**
- All services (S1-S5)
- Constraints: AC2.3

***

#### DG2.2 Connection Pool Limits

**Rule Type:** Mandatory

**Statement:** Each FastAPI worker maintains at most 10 PostgreSQL connections. Total connections across all workers must not exceed max_connections - 10.

**Rationale:** Prevents connection exhaustion (AC4.1).

**Validation Method:**
- Configuration validation on startup
- Monitoring: Alert if connections >80% of max

**Applies To:**
- All services
- Constraints: AC4.1

***

#### DG2.3 Context Size Limits

**Rule Type:** Mandatory

**Statement:** Agent context must not exceed limits: 20 messages, story outline <2000 words, total <6000 words.

**Rationale:** Prevents LLM context window overflow (AC4.2). Controls cost.

**Validation Method:**
- Unit tests verify truncation
- Token counting in context builder
- Integration tests with large conversations

**Applies To:**
- Services: S3 (context builder), S4 (agent runner)
- Requirements: R3.1, R5.1

***

### DG3. Security and Authorization

**Enforces:** AC5.1, AC5.2, AC5.3

#### DG3.1 Authorization Before Every Room Operation

**Rule Type:** Mandatory

**Statement:** All operations that read or write room data MUST call check_room_access(user_id, room_id) before executing.

**Rationale:** Enforces room-level authorization (AC5.2). Prevents unauthorized access.

**Validation Method:**
- Security test: Non-participant attempts access, expect 403
- Code review: Check for authorization call in all room operations

**Applies To:**
- Services: S2, S3, S4, S5
- Requirements: R1.3, R4.1
- Contracts: All C2.x, C3.x

***

#### DG3.2 JWT Validation on Every Request

**Rule Type:** Mandatory

**Statement:** All HTTP endpoints (except health checks) MUST validate JWT. WebSocket connections validate on handshake.

**Rationale:** Enforces authentication (AC5.1). Stateless workers have no session memory.

**Validation Method:**
- Security test: Request without JWT returns 401
- Security test: Expired JWT returns 401

**Applies To:**
- Services: S1 (provides), All others (consume)
- Contracts: All C2.x, C3.x

***

#### DG3.3 Agent Participant Verification

**Rule Type:** Mandatory

**Statement:** Before agent responds, verify agent is active participant in room via check_agent_access(agent_id, room_id).

**Rationale:** Enforces AC5.3. Prevents agents from responding in unauthorized rooms.

**Validation Method:**
- Integration test: Attempt agent response in room without registration
- Code review: Check in agent runner before execution

**Applies To:**
- Services: S4
- Requirements: R3.1

***

### DG4. Error Handling and Resilience

**Enforces:** AP2, R3.1, R2.1

#### DG4.1 Agent Timeout Handling

**Rule Type:** Mandatory

**Statement:** All agent executions must have 60-second timeout. On timeout, log error and return friendly message to user.

**Rationale:** Prevents hung agents from blocking workers. Users get feedback.

**Validation Method:**
- Integration test: Mock slow LLM, verify timeout triggers
- Load test: Verify worker remains responsive after timeout

**Applies To:**
- Services: S4 (Agent Runner)
- Requirements: R3.1

***

#### DG4.2 Transaction Rollback Safety

**Rule Type:** Mandatory

**Statement:** If projection update fails within transaction, entire transaction (including event write) MUST rollback. Never commit partial state.

**Rationale:** Maintains consistency between event log and projections (AC3.2). Prevents orphan events.

**Validation Method:**
- Integration test: Mock projection update failure, verify event not in E1
- Code review: No try/except around projection updates without re-raising

**Applies To:**
- Services: S2, S3, S4
- Domain: E1, P1-P3

***

#### DG4.3 Redis PubSub Message Loss Mitigation

**Rule Type:** Mandatory

**Statement:** Clients MUST use sequence-based replay on reconnection (C3.1 lastsequence)

**Rationale:** Maintains consistency between event log and projections (AC3.2). Prevents orphan events.

**Validation Method:**
- Integration test: explicitly test worker failure scenarios with message replay verification
- Code review: No try/except around projection updates without re-raising

**Applies To:**
- Services: S2, S3, S4
- Domain: E1, P1-P3

***

### DG5. Testing and Validation

**Enforces:** All Requirements

#### DG5.1 Event Log Replay Testing

**Rule Type:** Mandatory

**Statement:** All projection updates MUST be testable by replaying events from E1. Test suite must include replay scenarios.

**Rationale:** Validates projections can be rebuilt from events (AP1). Critical for disaster recovery.

**Validation Method:**
- Integration test: Truncate projection, replay events, verify match

**Applies To:**
- Services: S2, S3, S4
- Domain: P1-P3

***

#### DG5.2 Multi-Worker Concurrency Testing

**Rule Type:** Mandatory

**Statement:** Load tests MUST run with 4+ workers and simulate concurrent writes to same room. Verify no duplicate sequences, no lost events.

**Validation Method:**
- Load test: 4 workers, 100 concurrent requests to same room, check sequence uniqueness
- Verify all 100 events in E1 with unique room_sequence

**Applies To:**
- Services: All
- Requirements: R4.1

***

#### DG5.3 Multi-User Scenario Testing

**Rule Type:** Mandatory

**Statement:** Integration tests must verify multi-user and multi-agent scenarios: multiple users in room, multiple agents responding, participant management.

**Validation Method:**
- Test: Create room, add 3 users + 2 agents, send messages from each, verify all see all messages
- Test: Remove participant, verify they cannot access room

**Applies To:**
- Requirements: R1.2, R1.3, R3.2, R4.2

***

## 8. Validation and Approval

### Cross-Reference Validation Matrix

| Section | References To | Referenced By | Orphan Check | Completeness Check |
|:--------|:-------------|:--------------|:-------------|:-------------------|
| AP (Patterns) | None | AC, D, S, R, DG | N/A | ✅ 5 patterns defined |
| AC (Constraints) | AP1-AP5 | D, S, R, DG | ✅ All AC referenced | ✅ All AP have constraints |
| D/E/P (Domain) | AP1-AP3, AC | S, R | ✅ All referenced | ✅ All have owner service |
| S (Services) | AP, AC, D, other S | R, C | ✅ S1-S5 all referenced | ✅ All D owned |
| R (Requirements) | AP, AC, D, S | C, DG | ✅ R1-R5 all referenced | ✅ All have acceptance criteria |
| C (Contracts) | D, S, R | DG | ✅ C1-C3 all referenced | ✅ All R have implementing C |
| DG (Guardrails) | AP, AC, R, C | None | ✅ All enforcing something | ✅ Critical AC have DG |

### Contradiction Checklist

- [x] **Technology Stack Consistency:** All domain objects use PostgreSQL (AC2.1)
- [x] **Service Ownership:** Each domain object owned by exactly one service
- [x] **Dependency Acyclicity:** No circular dependencies (see service graph §4)
- [x] **Authorization Completeness:** All multi-user requirements (R1.3, R4.x) have authorization (DG3.1, DG3.3)
- [x] **Concurrency Strategy:** AC3.1 enforced by DG1.3 (sequence coordination)
- [x] **Error Handling:** All contracts define error responses
- [x] **Projection Consistency:** All projections specify transactional update (AC3.2, DG1.2)
- [x] **Event Sourcing:** AP1 enforced by DG1.1 (immutability) and DG5.1 (replay testing)
- [x] **Multi-Worker Coordination:** AC2.2 + DG1.3 + DG5.2
- [ ] **Undefined References:** Some areas marked "NEEDS CONSIDERATION" - see below

### Areas Requiring Further Consideration 

**🔍 PENDING DECISIONS:**


1. **AG-UI Protocol Compatibility (C3.1): in review pending research spike**
   - Current spec uses simplified JSON WebSocket protocol
   - Should evaluate AG-UI standard for ecosystem compatibility
   - Impact: WebSocket message formats in Phase 4

2. **Analytics Extension (AC2.1): deferred**
   - Future plans to integrate duckdb_pg as needed: decision and planning deferred

4. **Agent Handoff Mechanism (R3.2):**
   - Multi-agent handoffs deferred to Phase 5
   - Initial implementation: agents respond independently
   - Impact: Agent coordination patterns

5. **Room Garbage Collection: deferred** 
   - No spec for orphaned room cleanup
   - Should define retention policy
   - Impact: Database growth over time: deferred

### Approval Sign-Off

| Role | Name | Date | Concerns |
|:-----|:-----|:-----|:---------|
| Principal Architect | | | Advisory locks vs alternatives |
| Lead Engineer | | | AG-UI protocol evaluation |
| Security Lead | | | Review AC5.x, DG3.x |
| Operations Lead | | | Room retention policy |

***

## 9. Change Log

| Version | Date | Author | Changes | Sections Affected |
|:--------|:-----|:-------|:--------|:------------------|
| 1.0 | Dec 11, 2025 | Integration Team | Initial creation incorporating multi-user rooms architecture | All |

***

## 10. Implementation Roadmap

### Phased Implementation Strategy

This specification supports incremental delivery across 5 phases, each delivering end-to-end value:

**Phase 0: Infrastructure (2-3 days)**
- Add Redis to docker-compose
- Verify pgvector extension
- Update health checks
- Configuration management

**Phase 1: Event Sourcing + Room Management (4-5 days)**
- Implement D1, D2, E1-E4, P1-P2 domain objects
- Implement S2 (Room Management), S3 (Event Emitter) services
- Implement C2.2 (Room Management API)
- Database migration with event immutability enforcement
- Tests: DG5.1 (event replay), DG1.1 (immutability)

**Phase 2: Multi-User Multi-Agent Integration (5-6 days)**
- Implement agent participant registration
- Implement S4 (Agent Runner) service
- Implement first agent (StoryAdvisor)
- Implement E5, E6, P3 domain objects
- Implement C1.3 (Context Provider), C1.5 (Agent Invocation)
- Implement C2.3 (Agent Management API)
- Tests: DG5.3 (multi-user scenarios), DG3.3 (agent authorization)

**Phase 3: Frontend Multi-User UI (4-5 days)**
- Room list component
- Room creation modal
- Participant list sidebar
- Message attribution UI
- Chat interface integrated into story editor
- OpenAPI client regeneration

**Phase 4: Real-Time Streaming (5-6 days)**
- WebSocket endpoint (C3.1)
- Redis pub/sub integration
- Streaming agent responses
- Reconnection with replay
- Tests: DG5.2 (multi-worker concurrency)

**Phase 5: Advanced Multi-Agent (Optional, 6-8 days)**
- Agent handoff mechanism
- Tool execution tracking
- Multi-agent coordination

### Steel Thread Definition

> **"Multiple authors join a shared room, invite the StoryAdvisor agent, and collaborate on story development. All participants see each message in real-time. The agent's responses are contextually aware of the entire conversation and referenced story."**

This steel thread proves:
- ✅ Multi-user rooms (not single-user sessions)
- ✅ Agent as room participant
- ✅ Room-level authorization
- ✅ Multi-party event broadcasting
- ✅ Participant management
- ✅ Story context integration

***

## Appendix A: Quick Reference Guide

### Finding What You Need

- **"What data do I need?"** → Section 3 (Domain Model)
- **"Who owns this data?"** → Section 4 (Services) + Domain Object's "Owner Service"
- **"What can the system do?"** → Section 5 (Requirements)
- **"How do I call this?"** → Section 6 (Contracts)
- **"What am I not allowed to do?"** → Section 7 (Design Guardrails)
- **"Why was this decided?"** → Section 1 (Patterns) + Section 2 (Constraints)

### Key Architectural Diagrams

#### Multi-User Message Flow

```
User A sends message in Room X
         ↓
S5: UI Gateway validates authorization
         ↓
S3: emit_event(room_id, "message.user", {...})
         ↓
    Transaction Start
         ├─ Write to E1 (room_events)
         ├─ Update P3 (messages projection)
         └─ Commit
         ↓
    Publish to Redis channel "room:X"
         ↓
    All Workers subscribed to room:X receive event
         ↓
    Workers forward via WebSocket to:
         ├─ User A (sees own message)
         ├─ User B (sees User A's message)
         ├─ User C (sees User A's message)
         ├─ Agent 1 (sees message, may respond)
         └─ Agent 2 (sees message, may respond)
         ↓
    Agent 1 decides to respond
         ↓
    S4: run_agent(room_id, message, "story_advisor")
         ↓
    S3: build_room_context() → Story + X messages
         ↓
    PydanticAI executes agent with context
         ↓
    S3: emit_event(room_id, "message.agent", {...})
         ↓
    Broadcast agent response to all participants
```

#### Room Authorization Flow

```
User attempts operation on Room Y
         ↓
S1: check_room_access(user_id, room_id)
         ↓
Query P2: room_participants
         WHERE room_id = Y
         AND participant_id = user_id
         AND participant_type = 'user'
         AND is_active = true
         ↓
    Found? → Authorized ✓
         ↓
    Not found? → 403 Forbidden ✗
```

#### Agent as Participant Pattern

```
Room Created
    ├─ User A added as 'owner'
    │   participant_type='user'
    │   role='owner'
    │
    ├─ User B invited as 'member'
    │   participant_type='user'
    │   role='member'
    │
    └─ StoryAdvisor added as 'agent'
        participant_type='agent'
        role='agent'
        participant_id=UUID5("story_advisor")

All participants:
    ├─ See all messages
    ├─ Can send messages
    └─ Attributed by participant_id
```

### Critical Design Principles

1. **Rooms, Not Sessions:** Multi-user collaborative spaces, not single-user sessions
2. **Events Are Immutable:** Append-only log, never mutate
3. **Projections Are Transactional:** Updated atomically with events
4. **Agents Are Participants:** Not external services, but room members
5. **Authorization Is Room-Scoped:** Check participant membership before every operation

***

**END OF TECHNICAL SPECIFICATION**

***

**Document Status:** Ready for review with areas marked for consideration

**Next Steps:**
1. Review and approve specification with stakeholders
2. Final Review of Open 
3. Begin Phase 0 implementation
4. Establish monitoring and observability
5. Create detailed implementation tickets per phase

**Questions or clarifications?** Reference section numbers and cross-references throughout this specification.