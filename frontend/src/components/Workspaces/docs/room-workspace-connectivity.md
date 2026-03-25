# Room And Workspace Connectivity Note

## Purpose

This artifact defines how rooms and workspaces should connect in a way that is operationally useful and security-legible.

The goal is not only to enable websocket connectivity. The goal is to ensure that connectivity is built on explicit:

- workspace identity
- room identity
- workspace readiness
- project and membership access
- backend-issued capability and endpoint descriptors

This note assumes the decisions in:

- [workspace-domain-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md)
- [repo-bootstrap-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md)
- [project-workspace-relationship.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-workspace-relationship.md)

It is also grounded in:

- [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py)
- [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py)
- [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts)
- [roomRuntimeService.ts](/home/josep/dog/frontend/src/services/roomRuntimeService.ts)
- [useWorkspaceTerminal.ts](/home/josep/dog/frontend/src/hooks/useWorkspaceTerminal.ts)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)

## Primary Goal

The near-term system should support this flow:

1. a workspace exists as a first-class platform object
2. that workspace is attached to a project or otherwise accessible
3. a room exists with participants and agents
4. the backend determines whether that room may use that workspace
5. the backend issues explicit connectivity descriptors
6. the room or its agents connect only through those approved descriptors

That is the minimum trust story required for the next milestone.

## Core Decision

Connectivity should be descriptor-based and backend-issued.

Not:

- frontend-synthesized websocket URLs
- room agents guessing service endpoints from workspace metadata
- direct kennel connectivity based only on possession of a workspace id

This means:

- the backend is the authority for whether a room may attach to a workspace
- the backend is the authority for which endpoints are exposed
- the backend is the authority for the scope and lifetime of credentials or tokens

## Trust Model

Connectivity must be authorized across three separate objects:

1. the caller
   user or agent acting in the context of a room

2. the room
   collaboration container with its own membership semantics

3. the workspace
   operational compute/resource surface with its own lifecycle and access semantics

These should not be collapsed into a single yes/no check.

### Recommended Authorization Layers

#### Layer 1: Workspace Eligibility

The workspace must be eligible for attachment:

- it exists
- it is not destroyed
- it is in a state that allows service discovery or runtime use
- it is attached to the appropriate project if project-scoped

Recommended rule:

- room/workspace connectivity requires `allowed_actions` to include a connectivity-oriented capability such as `discover_services`

#### Layer 2: Caller Access To Room

The caller must be an authorized room participant or a backend-recognized room agent.

This is already aligned with current room architecture:

- rooms have participant membership
- room runtime endpoints operate in room-user context

#### Layer 3: Room Access To Workspace

The room itself must be allowed to use the workspace.

Near-term recommended rule:

- if the room and workspace are both attached to the same project, room-to-workspace connectivity is allowed subject to workspace readiness

Fallback near-term rule:

- workspace owner may explicitly connect one of their rooms to one of their private workspaces if no conflicting project semantics exist

Recommendation:

- make shared-project attachment the preferred and most legible path
- allow owner-private connection as a narrow local/dev escape hatch if needed

#### Layer 4: Capability Scope

Even if a room may use a workspace, the backend still decides what kind of connectivity is allowed:

- terminal access
- service access
- agent runtime access
- future direct platform service access

This scope should be explicit and short-lived.

## Connectivity Modes

The system should distinguish several connectivity modes instead of treating all websocket access as equivalent.

### 1. Operator Terminal Access

Used by a human operator viewing a workspace terminal.

Characteristics:

- initiated from workspace detail UI
- backend issues a short-lived terminal URL
- direct browser-to-kennel websocket is acceptable
- already partially implemented today

### 2. Room-To-Workspace Service Access

Used when a room agent or room surface needs to connect to a service hosted inside a workspace.

Characteristics:

- should not reuse terminal semantics
- should be backed by service descriptors, not only a raw URL
- should include purpose-limited credentials or route tokens

### 3. Workspace-To-Platform Service Access

Used when an agent or service running inside the workspace needs to call platform services over websocket or similar runtime channels.

Characteristics:

- should be represented as capability grants
- should not be implied merely by workspace existence
- will likely share conceptual machinery with room-to-workspace trust, but it is a different direction of travel

## Recommended Near-Term Rule Set

For this iteration, the platform should support:

- operator terminal access
- room-to-workspace service connectivity

And defer full generality for:

- arbitrary bidirectional service mesh semantics
- unconstrained direct agent-to-platform websocket reachability

This keeps the trust model understandable while still unlocking the milestone.

## Canonical Relationship Path

The most legible near-term authorization path is:

- room belongs to project
- workspace belongs to project
- caller belongs to room
- project access implies workspace usability
- backend issues room/workspace connectivity descriptor

This is why the previous project/workspace decision matters.

Recommended project-centric rule:

- project association is the canonical way to make a workspace available to rooms beyond the owner-only case

## Descriptor Model

Connectivity should be exposed as explicit descriptors, not inferred from raw workspace state.

### Recommended Room/Workspace Descriptor

```ts
interface RoomWorkspaceConnectionDescriptor {
  room_id: string
  workspace_id: string

  status: "available" | "pending" | "denied"
  reason: string | null

  capabilities: Array<
    | "terminal_view"
    | "service_connect"
    | "agent_runtime_connect"
  >

  endpoints: Array<{
    id: string
    kind: "service" | "terminal" | "agent-runtime"
    label: string
    protocol: "ws" | "wss" | "http" | "https"
    url: string
    auth_mode: "token" | "session" | "none"
    expires_at: string | null
  }>
}
```

Important:

- endpoints should be issued by the backend at request time
- clients should not derive them from `kennel_name`, `service_count`, or host assumptions

## Recommended API Surface

### New Endpoint

Add a dedicated room/workspace connectivity route:

- `POST /api/v1/rooms/{room_id}/workspace-connections`

Request:

```json
{
  "workspace_id": "uuid",
  "purpose": "service_connect"
}
```

Response:

- `RoomWorkspaceConnectionDescriptor`

Implementation update for the current slice:

- this first descriptor route is now implemented on the backend
- it evaluates:
  - caller room membership
  - shared-project or owner-private authorization path
  - workspace lifecycle/connectability
  - purpose-specific discovered services
- the current descriptor behavior is intentionally first-pass:
  - web-service purposes can return backend-issued descriptors based on discovered container-routable URLs
  - `agent_runtime_connect` can now move from `pending` to `available` when the runtime binds its canonical port and kennel discovery sees a real container IP endpoint
  - agent runtimes that are process-healthy but have not published a network endpoint still remain explicitly `pending`
- the room-side frontend now carries a lightweight current connection state built on top of issued descriptors rather than only showing the latest inspection result
- the frontend now exposes this route through the generated client and shared room service layer
- the room view now includes a small `Workspace Links` inspector panel that can:
  - choose from room-aware workspace candidates rather than a generic visible workspace list
  - request a descriptor for `service_connect` or `agent_runtime_connect`
  - poll while the descriptor remains `pending`
  - surface granted capabilities, issued endpoints, and backend reasons directly
- the room runtime surface now consumes the room's current descriptor-backed connection and only offers launch affordances from issued descriptor endpoints
- backend candidate selection now has an explicit surface too:
  - `GET /api/v1/rooms/{room_id}/workspace-candidates`
  - candidates are ranked by shared-project match first, then owner-private fallback
- the backend now also exposes a narrow current-connection convenience surface:
  - `GET /api/v1/rooms/{room_id}/workspace-connections/current`
  - `PUT /api/v1/rooms/{room_id}/workspace-connections/current`
  - `DELETE /api/v1/rooms/{room_id}/workspace-connections/current`
- endpoint descriptors now carry explicit scope metadata for room, workspace,
  purpose, and endpoint id

Why `POST`:

- descriptor issuance is an authorization decision with token generation semantics
- this behaves more like a capability request than a passive read

### Optional Read Endpoint

For UI status only:

- `GET /api/v1/rooms/{room_id}/workspace-connections`

Purpose:

- list known workspace attachment options and their current availability

This can come later if needed.

### Workspace Discovery Endpoint

Complementary to the above, the workspace side should eventually expose:

- `GET /api/v1/workspaces/{workspace_id}/services`

But that route alone should not imply room authorization. It only exposes service discovery for an already authorized caller or as raw operator detail.

## Recommended Backend Authorization Flow

When `POST /rooms/{room_id}/workspace-connections` is called:

1. verify caller has access to the room
2. load workspace and confirm it exists
3. verify workspace lifecycle is compatible with the requested purpose
4. verify the room has a valid authorization path to that workspace
   Near-term:
   - shared project attachment
   - or owner-private exception if explicitly allowed
5. determine capability scope for the requested purpose
6. resolve available service or runtime endpoints
7. mint short-lived credentials or tokens
8. return a descriptor with scoped endpoints

If any of those checks fail, return:

- `status = denied`
- or an HTTP error where appropriate

## Readiness Semantics

Connectivity depends on readiness, but readiness is not identical for every purpose.

### Terminal Readiness

For human terminal viewing:

- terminal token issuance available
- workspace lifecycle `ready`

### Service Connectivity Readiness

For room-to-workspace service access:

- workspace lifecycle `ready`
- bootstrap complete
- requested service startup complete
- at least one declared service endpoint is available

### Agent Runtime Readiness

For room agents interacting with an agent runtime hosted in the workspace:

- workspace lifecycle `ready`
- agent runtime startup profile succeeded
- runtime endpoint discovered and authorized

### Recommendation

Keep these purpose-specific details out of the top-level workspace status enum.

Instead:

- workspace top-level status says whether the resource is operationally ready in general
- service discovery and connection descriptors say whether a specific connectivity purpose is ready

## Endpoint Strategy

There are two plausible strategies:

1. backend-proxied websocket routes
2. direct endpoint descriptors with scoped credentials

### Recommendation For This Iteration

Use direct endpoint descriptors with backend-issued scoped credentials wherever practical.

Why:

- it matches the existing terminal model
- it keeps the backend out of the hot path for streaming
- it is easier to reason about for kennel-hosted services

But:

- direct descriptors must still be backend-issued
- direct access must still be capability-scoped

Proxying can remain an option later for services that need stronger mediation or transport normalization.

## Credential Strategy

Short-lived, purpose-scoped credentials should be preferred.

Recommended properties:

- scoped to:
  - room id
  - workspace id
  - capability
  - endpoint kind
- short expiration
- auditable issuance
- revocable by changing server-side verification or TTL windows

This is better than:

- long-lived generic workspace tokens
- tokens that imply broader authority than the single connection purpose

## Auditability

Every connection descriptor issuance should be loggable with:

- caller id
- room id
- workspace id
- project context if present
- requested purpose
- granted capabilities
- issuance time
- expiration time

This matters because these connections become the operational trust boundary of the platform.

## Frontend Implications

The frontend should not treat workspace connectivity as “another way to fetch a URL.”

Instead:

- request a descriptor for a specific purpose
- render clear availability/denied/pending state
- connect only through the returned endpoint descriptors

Near-term frontend surfaces likely need:

- workspace detail:
  - project association
  - service readiness summary
  - available room connection state

- room UI:
  - select or confirm an eligible workspace
  - request connection
  - surface denied reasons clearly

Current implementation note:

- the room-side portion of that UI now exists as a lightweight live inspector in [WorkspaceConnectionsPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/WorkspaceConnectionsPanel.tsx)
- it is intended as both a practical affordance and a trust/debug surface while the broader room/workspace product flow continues to evolve

## First-Phase Recommendation

The narrowest useful implementation of this note is:

1. add `resource_type = "workspace"` project attachments
2. add workspace service discovery summary to the workspace contract
3. add `POST /rooms/{room_id}/workspace-connections`
4. authorize via:
   - room membership
   - workspace readiness
   - shared project attachment
5. return direct websocket-capable endpoint descriptors with scoped short-lived tokens
6. keep human terminal access separate from room service connectivity, even if both ultimately use websocket transport

That is enough to establish explicit identity, readiness, and access semantics for the next milestone without building a full generalized service mesh.

## Open Questions

- Should owner-private room-to-private-workspace connectivity be supported in the first pass, or should shared project attachment be mandatory?
- Should room/workspace connection descriptors be single-endpoint or allow multiple endpoint capabilities at once?
- Which hosted service types need first-class endpoint kinds immediately:
  - terminal
  - agent runtime
  - app/web service
  - Jupyter
- Do we want descriptor issuance to create a persisted connection record, or stay ephemeral and audit-log only?
- Which services, if any, should be backend-proxied rather than directly exposed?
