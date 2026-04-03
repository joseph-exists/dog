# Room Workspace Execution Layer Sequenced Implementation

## Purpose

This artifact defines the atomic sequential work required to deliver the
adapter-based room workspace execution MVP across backend, kennel, db, and
frontend.

Each slice is intended to land independently and leave a usable foundation for
the next slice.

## MVP Delivery Sequence

### Slice 1. Runtime Identity Projection

**Backend**

- extend the resolved runtime target model with:
  - `runtime_id`
  - `runtime_profile`
  - `transport_kind`
- derive runtime identity from discovered workspace service metadata
- carry runtime identity through room current connection refresh and runtime
  target resolution

**DB**

- no schema change required if runtime identity is derived from current
  descriptor state

**Kennel**

- no route change in this slice
- confirm declared service metadata remains stable for:
  - `codex`
  - `claude_code`
  - `hermes`

**Frontend**

- no new UI behavior required

**Acceptance**

- backend can resolve a room runtime target with stable runtime identity fields
- route and agent tool can inspect runtime identity without parsing labels or
  URLs

### Slice 2. Backend Adapter Registry

**Backend**

- add a runtime adapter interface
- add a runtime adapter registry that selects by:
  - `runtime_id`
  - `runtime_profile` when present
- add a room runtime orchestrator service that:
  - resolves the current runtime target
  - selects the adapter
  - executes the invocation
  - returns normalized backend result models

**DB**

- no schema change required

**Kennel**

- no route change in this slice

**Frontend**

- no new UI behavior required

**Acceptance**

- route and agent tool call the orchestrator rather than a transport-specific
  helper
- adapter selection is test-covered for the currently supported runtime ids

### Slice 3. Kennel-Routed Runtime Invoke Endpoint

**Kennel**

- add a narrow management endpoint for agent-runtime invocation scoped to one
  env and one declared runtime service
- endpoint responsibilities:
  - validate management secret
  - resolve the declared runtime service for the env
  - open the runtime transport from kennel
  - send the adapter-supplied payload
  - return the first response frame or command result
  - return explicit failure details for connect, execution, and timeout states

Suggested endpoint family:

- `POST /envs/{name}/agent-runtimes/{service_id}/invoke`

**Backend**

- add a kennel client helper for the new invoke endpoint
- add transport result normalization for kennel-routed responses

**DB**

- no schema change required

**Frontend**

- no new UI behavior required

**Acceptance**

- backend can invoke a connected runtime without dialing the raw env IP from
  the backend container
- kennel returns phase-specific error details to backend

### Slice 4. Codex Adapter

**Backend**

- add a Codex runtime adapter
- support profile-aware execution for:
  - `codex_app_server`
  - `codex_exec`
- choose the request shape and kennel invoke mode required by the selected
  Codex profile
- normalize Codex result payloads into the shared backend result model

**Kennel**

- support the Codex invoke path required by the adapter
- if profile-specific handling is needed, keep it local to the Codex runtime
  execution path

**DB**

- no schema change required

**Frontend**

- update runtime result display copy if Codex-specific metadata is returned in a
  useful normalized field

**Acceptance**

- a room connected to a Codex runtime can complete a request through the room
  invoke route
- the same connection can be used through the room agent tool

### Slice 5. Claude Code Adapter

**Backend**

- add a Claude Code runtime adapter
- support the runtime/profile path required for `claude_code`
- normalize Claude result payloads into the shared backend result model

**Kennel**

- support the Claude Code invoke path required by the adapter

**DB**

- no schema change required

**Frontend**

- no new UI behavior required

**Acceptance**

- a room connected to a Claude Code runtime can complete a request through the
  room invoke route
- the same connection can be used through the room agent tool

### Slice 6. Hermes Adapter

**Backend**

- add a Hermes runtime adapter
- support the Hermes transport and request shape required by the selected
  runtime profile
- normalize Hermes result payloads into the shared backend result model

**Kennel**

- support the Hermes invoke path required by the adapter

**DB**

- no schema change required

**Frontend**

- no new UI behavior required

**Acceptance**

- a room connected to a Hermes runtime can complete a request through the room
  invoke route
- the same connection can be used through the room agent tool

### Slice 7. Invocation Lifecycle Recording

**Backend**

- add a persisted invocation record for room workspace runtime calls
- include:
  - `request_id`
  - `room_id`
  - `workspace_id`
  - `connection_id`
  - `runtime_id`
  - `runtime_profile`
  - caller kind and caller id
  - status
  - error category
  - started_at
  - completed_at
- write invocation records from the room runtime orchestrator

**DB**

- add a migration for the invocation record table
- add indexes for:
  - `room_id`
  - `workspace_id`
  - `request_id`
  - `created_at`

**Kennel**

- no route change required

**Frontend**

- no new UI behavior required in this slice

**Acceptance**

- backend can inspect and audit room runtime invocations by room and request id
- room message enrichment can reference a persisted invocation record

### Slice 8. Frontend Invocation Status Refinement

**Frontend**

- update the room workspace panel to surface:
  - runtime name
  - request state
  - phase-specific error detail
- keep the current single action surface in the workspace connections panel
- add room-history affordances for invocation result messages when enriched
  metadata is present

**Backend**

- ensure the room invoke route returns normalized error detail fields needed by
  the UI
- ensure emitted room messages include invocation metadata that is safe to
  display

**DB**

- no schema change required beyond the invocation record table from Slice 7

**Kennel**

- no route change required

**Acceptance**

- users can distinguish runtime connect failures, execution failures, and
  response timeouts in room UX

### Slice 9. Agent Runner Completion

**Backend**

- route all room-agent runtime calls through the runtime orchestrator
- add adapter-aware tests for:
  - user route invocation
  - room agent tool invocation
  - room message persistence
  - invocation record writes

**Kennel**

- add focused tests for the invoke endpoint behavior used by each adapter

**Frontend**

- validate the panel flow against the stabilized backend response shape

**DB**

- validate invocation record persistence in backend tests

**Acceptance**

- user-driven and agent-driven room runtime execution share one orchestrated
  backend flow
- current supported runtime ids execute through their registered adapters

## Cross-Stack Completion Criteria

The adapter-based MVP is complete when:

- a room can invoke its connected runtime through one stable backend route
- room agents can invoke the same connected runtime through one stable backend
  tool
- backend selects an adapter using runtime identity and profile metadata
- kennel exposes the runtime invoke ingress used by the active adapters
- invocation lifecycle is recorded and room-visible output is emitted
- frontend exposes one stable runtime action with clear invocation state

## Primary References

- [room-workspace-execution-layer-mvp-plan.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-execution-layer-mvp-plan.md)
- [room-workspace-connection-service-reference.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connection-service-reference.md)
