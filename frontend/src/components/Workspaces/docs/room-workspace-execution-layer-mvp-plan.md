# Room Workspace Execution Layer MVP Plan

## Purpose

This document defines the MVP execution layer for room-driven use of a connected
workspace agent runtime.

The MVP centers on one stable room-facing capability:

- a room can invoke its current connected workspace runtime
- users and room agents use the same backend-owned invocation surface
- runtime output returns to the room as normal room-visible state

## MVP Goal

The MVP should make this workflow real:

1. a room selects a current workspace connection for `agent_runtime_connect`
2. a user or room agent asks to use that connected runtime
3. the backend resolves the current connection from backend truth
4. the backend selects a runtime adapter for the resolved runtime and profile
5. the selected adapter executes the invocation through the required transport
6. the result is surfaced back into the room as normal room output

## Product Shape

The MVP introduces one room-native capability:

- "Use connected workspace runtime"

This capability is available from two caller types:

- a user in the room
- a room agent acting through backend orchestration

The room experience should remain consistent:

- calls are explicit and visible
- results return to the room as messages or structured status events
- runtime identity is carried by the selected connection and reflected in the
  returned room output

## Core Design

The execution layer is backend-mediated and adapter-based.

The backend remains the place that:

- resolves the room's current connection
- validates purpose, state, and endpoint viability
- selects the runtime adapter
- records invocation lifecycle
- emits room-visible outcomes

The adapter layer owns:

- runtime-specific transport selection
- runtime/profile-specific request shaping
- runtime/profile-specific response interpretation

This gives the room and frontend one stable invocation surface while allowing
Codex, Claude Code, Hermes, and future profiles to use the execution path they
need.

## Runtime Adapter Shape

The runtime execution seam should be organized around:

- a runtime target resolver
- a runtime adapter registry
- one adapter interface
- per-runtime or per-profile adapter implementations

Suggested adapter shape:

```python
@dataclass(frozen=True)
class RoomWorkspaceRuntimeTarget:
    connection_id: str
    room_id: UUID
    workspace_id: UUID
    workspace_name: str
    descriptor_id: str
    endpoint_id: str
    endpoint_label: str
    protocol: str
    url: str
    scope: dict[str, str]
    runtime_id: str
    runtime_profile: str | None = None


class RoomWorkspaceRuntimeAdapter(Protocol):
    async def invoke(
        self,
        request: RoomWorkspaceRuntimeInvocationRequest,
    ) -> RoomWorkspaceRuntimeInvocationResult:
        ...
```

Suggested registry responsibilities:

- select adapter by `runtime_id`
- allow profile-aware selection when `runtime_profile` is present
- keep route and agent-tool code independent of runtime-specific details

## Runtime Execution Semantics

The shared backend request intent remains:

- room context
- caller identity
- input text

The runtime-facing execution path is adapter-owned.

Each adapter may use:

- a kennel-routed websocket invocation path
- a runtime-local websocket path
- a kennel-managed command execution path
- another narrow runtime transport that the selected runtime profile exposes

The normalized backend result shape remains:

```json
{
  "request_id": "uuid-like-string",
  "connection_id": "string",
  "workspace_id": "uuid",
  "endpoint_id": "string",
  "runtime_label": "Runtime Label",
  "protocol": "ws",
  "success": true,
  "output_text": "string",
  "raw": {}
}
```

## Current Implemented Slices

### 1. Runtime Consumer Helper

Implemented in
[room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py).

Current behavior:

- resolves the current connection
- enforces `purpose == agent_runtime_connect`
- rejects unavailable, expired, pending, or endpointless connections
- returns one selected runtime target for backend consumption

### 2. Initial Runtime Execution Service

Implemented in
[room_workspace_runtime_execution_service.py](/home/josep/dog/backend/app/services/room_workspace_runtime_execution_service.py).

Current behavior:

- executes a websocket-based runtime call for the resolved target
- normalizes JSON and plain-text responses into one backend result model
- exposes explicit failure semantics for:
  - websocket open/connection failures
  - post-open response timeouts
  - generic post-open execution failures

This service is now the starting point for the adapter registry and
runtime-specific implementations.

### 3. Room Route

Implemented in
[rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py).

Current behavior:

- `POST /api/v1/rooms/{room_id}/workspace-runtime/invoke`
- validates room membership
- resolves the current runtime target
- executes the runtime call
- persists normalized output back into the room as `room_message.agent`

### 4. Agent Tool Integration

Implemented in
[agent_tools.py](/home/josep/dog/backend/app/services/agent_tools.py) and the
agent runner stack.

Current behavior:

- room agents can invoke the room's connected workspace runtime through a
  backend-owned tool
- normal room-triggered agent execution enables that tool

### 5. Frontend User Action

Implemented in
[WorkspaceConnectionsPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx)
and [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts).

Current behavior:

- the current room connection can expose a `Send To Runtime` action
- the panel shows loading, success, and error state
- runtime output is also written back into room history by backend

## Implementation Focus

The next implementation slices should:

- add a backend runtime adapter registry
- add kennel-routed execution surfaces required by the first runtime adapters
- project runtime identity and profile metadata needed for adapter selection
- keep the route, agent tool, and frontend invocation surface stable

Current status:

- Slice 1 runtime identity projection is implemented in the backend and kennel
  service metadata path
- runtime targets now carry:
  - `runtime_id`
  - `runtime_profile`
  - `transport_kind`
- Slice 2 backend adapter registry is implemented in
  [room_workspace_runtime_orchestrator.py](/home/josep/dog/backend/app/services/room_workspace_runtime_orchestrator.py)
- the room route and agent tool now invoke connected runtimes through the
  runtime orchestrator and adapter registry
- Slice 3 kennel-routed invoke ingress is implemented for kennel-managed agent
  runtime invocation
- the default runtime adapter path now calls kennel-owned runtime ingress rather
  than dialing the raw runtime URL from the backend container
- Slice 4 Codex runtime adapter is implemented with profile-aware execution for:
  - `codex_app_server`
  - `codex_exec`
- the `codex_app_server` profile now uses the generic JSON-RPC session adapter
  path over kennel-routed websocket transport
- Slice 7 invocation lifecycle recording is implemented with persisted room
  workspace runtime invocation records and room message enrichment references
- Slice 8 frontend invocation status refinement is implemented with structured
  backend invoke error details and panel-visible invocation state, runtime
  identity, and invocation identifiers
- Slice 9 agent runner completion is implemented for the current orchestrated
  backend flow, with focused kennel invoke coverage for the active adapter
  execution paths

## Primary References

- [room-workspace-connection-service-reference.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connection-service-reference.md)
- [room-workspace-execution-layer-sequenced-implementation.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-execution-layer-sequenced-implementation.md)
- [room-workspace-connectivity.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connectivity.md)
