# Room Workspace Connection Service Reference

## Purpose

This document describes the current capabilities exposed by
[room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py)
so frontend and product teams can reason about likely user workflows without
reading backend code.

It focuses on:

- what the service currently does
- what request and response messages exist today
- how a room stores and reuses a selected workspace connection
- how container-discovered runtime services affect the result
- what room and agent surfaces can consume this state today

## What The Service Actually Owns

The service is the backend trust and projection layer between:

- a room
- a user acting in that room
- a workspace
- the workspace's discovered runtime services

Today it owns four behaviors:

1. list room-aware workspace candidates
2. issue a live room/workspace connection descriptor for a chosen purpose
3. persist one room-level "current connection" convenience record
4. re-hydrate that current connection for room UI and agent context

It does not currently own:

- a websocket protocol of its own
- message streaming between room and workspace
- browser-owned runtime websocket transport
- multi-connection room orchestration beyond the single persisted "current"
  record

## Primary Actors

### Room

The room is the collaboration container. The service checks that the caller has
access to the room, and it stores the room's selected workspace connection as a
room context item.

### Workspace

The workspace is the operational/container-backed resource. The service checks:

- whether the room has an authorized path to it
- whether the workspace lifecycle state is connectable
- whether service discovery reports usable runtime surfaces

### User

The user is the API caller for the public room routes. The service uses the
user to:

- verify room access
- verify workspace visibility
- determine allowed actions and access level
- allow the owner-private fallback when the room creator also owns the
  workspace

### Container / Runtime

The service does not inspect Docker directly. It depends on
[workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py),
which asks kennel for discovered services. In practice, the container/runtime
must publish service descriptors with:

- `id`
- `kind`
- `label`
- `status`
- `protocol`
- optionally `url`

If kennel discovery does not return a routable `url`, the room descriptor can
remain `pending` even when the runtime is otherwise healthy.

For Hermes runtime workspaces, the expected gateway contract is websocket
`ws://<workspace-ip>:4319/` with `kind=agent_runtime`.

## Current Public API Messages

The room routes in
[rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py) expose three
message families.

### 1. Workspace Candidate Listing

Route:

- `GET /api/v1/rooms/{room_id}/workspace-candidates`

Response shape:

```json
{
  "data": [
    {
      "room_id": "uuid",
      "workspace_id": "uuid",
      "workspace_name": "My Workspace",
      "workspace_status": "ready",
      "visibility": "project",
      "project_id": "uuid-or-null",
      "project_summary": {
        "id": "uuid",
        "name": "Project Name"
      },
      "relationship": "shared_project",
      "access_level": "use",
      "match_reason": "Room and workspace share project access.",
      "candidate_rank": 100,
      "service_count": 3,
      "ready_service_count": 2,
      "supports_service_connect": true,
      "supports_agent_runtime_connect": true
    }
  ],
  "count": 1
}
```

What this means:

- `relationship` explains why the workspace is being surfaced
  - `shared_project`
  - `owner_private`
- `access_level` is room-facing posture, not a transport credential
  - `view`
  - `use`
  - `manage`
- `supports_*` values are derived from discovered workspace service kinds

This message is the "what could this room use?" list.

### 2. Live Descriptor Request

Route:

- `POST /api/v1/rooms/{room_id}/workspace-connections`

Request shape:

```json
{
  "workspace_id": "uuid",
  "purpose": "service_connect"
}
```

Current `purpose` values:

- `service_connect`
- `agent_runtime_connect` (backend-routed runtime connectivity for room invoke)

Response shape:

```json
{
  "descriptor_id": "uuid-like-string",
  "room_id": "uuid",
  "workspace_id": "uuid",
  "purpose": "service_connect",
  "status": "available",
  "issued_at": "2026-04-02T12:00:00Z",
  "expires_at": "2026-04-02T12:05:00Z",
  "reason": null,
  "capabilities": [
    "service_connect",
    "agent_runtime_connect"
  ],
  "endpoints": [
    {
      "id": "service-id",
      "kind": "service",
      "label": "Frontend",
      "protocol": "http",
      "url": "http://...",
      "auth_mode": "none",
      "expires_at": null,
      "scope": {
        "room_id": "uuid",
        "workspace_id": "uuid",
        "purpose": "service_connect",
        "endpoint_id": "service-id",
        "descriptor_id": "uuid-like-string"
      }
    }
  ]
}
```

Current descriptor statuses:

- `available`: at least one matching service is `ready` and has a routable URL
- `pending`: authorization passed, but matching runtime surfaces are not yet
  routable or still starting
- `denied`: authorization or runtime matching failed

Current capability values:

- `service_connect`
- `agent_runtime_connect`

Note:

- `terminal_view` exists in the enum contract, but this service does not issue
  terminal endpoints today

### 3. Current Room Connection

Routes:

- `GET /api/v1/rooms/{room_id}/workspace-connections/current`
- `PUT /api/v1/rooms/{room_id}/workspace-connections/current`
- `DELETE /api/v1/rooms/{room_id}/workspace-connections/current`

Set request shape:

```json
{
  "workspace_id": "uuid",
  "purpose": "agent_runtime_connect"
}
```

Get/put response shape:

```json
{
  "connection_id": "uuid-like-string",
  "room_id": "uuid",
  "workspace_id": "uuid",
  "workspace_name": "My Workspace",
  "purpose": "agent_runtime_connect",
  "relationship": "shared_project",
  "access_level": "use",
  "selected_at": "2026-04-02T12:03:00Z",
  "service_count": 3,
  "ready_service_count": 2,
  "state": "active",
  "state_reason": null,
  "descriptor": {
    "descriptor_id": "uuid-like-string",
    "room_id": "uuid",
    "workspace_id": "uuid",
    "purpose": "agent_runtime_connect",
    "status": "available",
    "issued_at": "2026-04-02T12:03:00Z",
    "expires_at": "2026-04-02T12:08:00Z",
    "reason": null,
    "capabilities": [
      "service_connect",
      "agent_runtime_connect"
    ],
    "endpoints": []
  }
}
```

Current persisted connection states:

- `active`
- `unavailable`

Important behavior:

- the room stores only one current connection
- this is a convenience default, not a many-to-many room/workspace model
- the held record expires after 10 minutes unless refreshed or replaced
- the nested descriptor is rebuilt from current backend state whenever the
  current connection is read or consumed

## How Descriptor Outcomes Are Determined

The service evaluates a request in this order.

### 1. Workspace Existence

If the workspace does not exist, the descriptor is `denied`.

### 2. Room To Workspace Authorization Path

The descriptor is allowed when one of these is true:

- room and workspace share a project
- current user owns both the room and the workspace
- caller is superuser
- a previously persisted owner-private connection is being re-hydrated

Otherwise the descriptor is `denied`.

### 3. Workspace Lifecycle Connectability

The descriptor is `denied` when the workspace is:

- `destroying`
- `destroyed`
- `failed`

If lifecycle actions do not include `discover_services`, the descriptor is
`pending`.

### 4. Service Discovery Match

Matching service sets are purpose-specific:

- `service_connect` uses non-`agent_runtime` services
- `agent_runtime_connect` uses `agent_runtime` services

Outcomes:

- no matching services: `denied`
- matching service is `ready` and has `url`: `available` (`ready + url`)
- matching service is `ready` but has no `url`: `pending`
- matching service is `pending` or `unknown`: `pending`

## What The Container Must Expose

The room service becomes useful only when workspace discovery returns the right
runtime service records.

For `service_connect`, the container should expose browser- or API-facing
services such as:

- web app
- jupyter
- custom app/service

For `agent_runtime_connect`, the container should expose agent runtime services
such as Codex or Hermes with `kind = "agent_runtime"`.

For Hermes in the current gateway path, the expected runtime endpoint is:

- protocol `ws`
- port `4319`
- path `/`

The practical rule is:

- `status = "ready"` plus a non-null `url` makes the descriptor immediately
  useful
- `status = "ready"` without `url` tells the room that the runtime exists but
  is not yet connectable from the room surface

This is why frontend/product should treat `pending` as a meaningful state, not
as an error.

## How The Room Uses This Today

### Room UI

The current room UI uses the service in two places:

- [WorkspaceConnectionsPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx)
  - lists candidates
  - requests live descriptors
  - lets the user set or clear the room's current connection
- [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx)
  - reads the current connection
  - shows status, freshness, capabilities, and issued endpoints

This means the room object can currently:

- inspect eligible workspaces
- inspect purpose-specific live connectivity
- persist one chosen workspace as session context
- surface current endpoints back to the operator

### Agent / Runtime Context

The service is also consumed internally by
[context_provider.py](/home/josep/dog/backend/app/services/context_provider.py).
When a current connection exists, the room context builder appends a system
extra-context item with this shape:

```json
{
  "context_type": "system.room.workspace_connection.current",
  "payload": {
    "connection_id": "uuid-like-string",
    "workspace_id": "uuid",
    "workspace_name": "My Workspace",
    "purpose": "service_connect",
    "state": "active",
    "state_reason": null,
    "descriptor_id": "uuid-like-string",
    "status": "available",
    "issued_at": "2026-04-02T12:03:00Z",
    "expires_at": "2026-04-02T12:08:00Z",
    "reason": null,
    "capabilities": [
      "service_connect"
    ],
    "endpoints": [
      {
        "id": "service-id",
        "kind": "service",
        "label": "Frontend",
        "protocol": "http",
        "url": "http://...",
        "auth_mode": "none",
        "expires_at": null,
        "scope": {
          "room_id": "uuid",
          "workspace_id": "uuid",
          "purpose": "service_connect",
          "endpoint_id": "service-id",
          "connection_id": "uuid-like-string",
          "descriptor_id": "uuid-like-string"
        }
      }
    ]
  },
  "source": "system"
}
```

This is the current "message back to the room runtime" shape. It is not a chat
message. It is system context injected into agent execution context.

## Message Taxonomy For Workflow Design

For product and frontend workflow mapping, the useful message types are:

1. candidate list message
   what workspaces the room may choose from

2. descriptor inspection message
   whether a specific workspace/purpose pair is available right now

3. current connection state message
   what workspace the room is currently treating as its session default

4. agent extra-context message
   what workspace connection metadata room agents can currently see

There is not yet a separate backend-defined message type for:

- "connect now" websocket traffic
- room-to-container command invocation
- container-to-room event streaming

Those flows would need additional handler or transport work on top of this
service.

## Practical Workflow Affordances Today

The current implementation supports these user stories well:

- "Show me which workspaces this room can use."
- "Check whether this room can use workspace X as a service surface."
- "Check whether this room can use workspace X's agent runtime."
- "Hold workspace X as the room's current workspace for this session."
- "Show the operator whether that held connection is still fresh, pending, or
  no longer available."
- "Expose the room's selected workspace connection to agent context."

It does not yet fully support:

- multiple simultaneous current workspace selections per room
- direct chat handlers that automatically act on the current connection
- room-specific transport credentials beyond the descriptor metadata
- backend-mediated streaming traffic between room and workspace

## Design Guidance For Frontend And Product

When designing workflows, treat the service as:

- a trust evaluator
- a runtime readiness inspector
- a single-current-selection session helper
- a source of agent-visible workspace context

Do not treat it as:

- a full transport layer
- a generic message bus
- a complete multi-workspace orchestration model

The safest current UX pattern is:

1. pick from candidates
2. inspect a live descriptor for a purpose
3. set current only when the room wants a default workspace context
4. handle `pending` and `unavailable` as first-class states

## Related References

- [room_workspace_connection_service.py](/home/josep/dog/backend/app/services/room_workspace_connection_service.py)
- [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py)
- [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [useRoomWorkspaceConnection.ts](/home/josep/dog/frontend/src/hooks/useRoomWorkspaceConnection.ts)
- [WorkspaceConnectionsPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx)
- [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx)
- [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py)
