# Room Workspace Descriptor Roadmap

## Recommendation

The next Track 4 implementation slice should be:

- move from descriptor inspection to descriptor consumption

In practical terms, that means the platform should stop treating
`POST /api/v1/rooms/{room_id}/workspace-connections` as a diagnostic endpoint
only, and start using it as the real contract for room-to-workspace runtime use.

This is the right next move because Track 3 has now done its job for this phase:

- workspace/project relationship is canonical and real
- workspace visibility is project-aware
- workspace `allowed_actions` are actor-aware
- frontend workspace surfaces now distinguish use from manage

That means richer Track 4 work can now stand on explicit identity, readiness,
and access semantics rather than on relationship projection alone.

## Why This Slice

The current Track 4 slice is useful, but still transitional:

- the backend can issue room/workspace descriptors
- the frontend can inspect them live in the room UI
- readiness and authorization are explicit
- `agent_runtime_connect` can now move from `pending` to `available`

But the descriptor is not yet the operational center of the room/runtime flow.

The main gap is:

- rooms can ask “is this connectable?”
- but the room runtime and room UX do not yet really use that descriptor as the
  durable coordination contract for selecting, exposing, and consuming a workspace

So the next highest-value step is to turn descriptor issuance into an actual
room-side workflow.

## Scope

This pass should implement:

- room-aware eligible workspace selection
- room-side connection intent built on descriptor requests
- descriptor-backed runtime/use state in room UX
- a clean path for room agents or room-side tools to consume the issued endpoints

This pass should not yet implement:

- generalized websocket proxying for every service type
- full bidirectional workspace-to-platform service trust
- arbitrary multi-workspace orchestration per room
- persisted long-lived room/workspace attachments unless they become necessary

## Design Intent

The next Track 4 slice should answer one practical question cleanly:

- how does a room actually choose and use a workspace in a way that is explicit,
  auditable, and understandable to the user?

The answer should be:

1. room identifies eligible workspace candidates
2. room requests a descriptor for a specific purpose
3. backend returns explicit availability and endpoint data
4. room runtime or room-side UI uses only the returned descriptor
5. the current connection state is visible in the room

That is a stronger and more usable milestone than simply adding more descriptor fields.

## Proposed Next Implementation Sequence

### Step 1: Room-Aware Workspace Candidate Surface

Add a room-facing way to identify workspaces that are plausible candidates for the room.

Recommendation:

- keep this lightweight at first
- either:
  - add a dedicated backend route for eligible room workspaces
  - or add a room-filtered frontend query layer built on the existing visible workspace list plus descriptor preflight

Preferred rule:

- candidates should bias toward:
  - shared-project matches
  - owner-private fallback only where allowed

Why this matters:

- the current inspector can choose from visible workspaces
- the next product surface should guide toward room-relevant workspaces instead

Status:

- implemented
- backend now exposes a room-aware candidate route:
  - `GET /api/v1/rooms/{room_id}/workspace-candidates`
- candidates are ranked and explained using:
  - shared-project match
  - owner-private fallback
  - current service/runtime support
  - current use/manage posture
- the room-side workspace panel now uses these candidates instead of the generic visible workspace list

### Step 2: Room-Side Connection State

Introduce a small room-scoped connection model in the frontend.

This does not need to be persisted in the backend yet.

Near-term frontend state should include:

```ts
{
  workspaceId: string | null
  purpose: "service_connect" | "agent_runtime_connect"
  descriptorStatus: "available" | "pending" | "denied" | null
  endpoints: [...]
  reason: string | null
}
```

Why:

- the room needs more than an inspector response
- it needs a stable current “selected workspace connection” concept for the session

Status:

- implemented
- room-scoped current connection state now lives in:
  - [useRoomWorkspaceConnection.ts](/home/josep/dog/frontend/src/hooks/useRoomWorkspaceConnection.ts)
- the room-side workspace panel now:
  - shows the current descriptor-backed connection
  - lets the user set or clear the current connection
  - keeps the current connection refreshed while the selected descriptor remains in view

### Step 3: Descriptor-Backed Runtime Consumption

Use the returned descriptor as the only source of truth for room/workspace runtime access.

Examples:

- a room panel opens a service only from returned endpoint descriptors
- an agent-runtime affordance is enabled only when a descriptor says it is available
- room-side tools stop deriving URLs from workspace service summaries directly

This is the key transition from “debug surface” to “actual trust contract.”

Status:

- implemented for the current room UX slice
- the room runtime panel now consumes the current room-scoped descriptor-backed connection
- runtime/service launch affordances are now sourced from the current descriptor endpoints rather than inferred workspace URLs
- pending or unavailable connections are surfaced in the runtime UX as explicit state instead of being silently ignored

### Step 4: Optional Backend Convenience For Current Room Connection

If the room UX becomes awkward without a backend record, add a narrow backend
convenience surface such as:

- `GET /api/v1/rooms/{room_id}/workspace-connections/current`
- or a lightweight room metadata projection

Recommendation:

- defer this unless the frontend state becomes too fragile
- prefer ephemeral descriptors plus auditability over premature persistence

Status:

- implemented for the current slice through a narrow backend convenience layer
- backend now exposes:
  - `GET /api/v1/rooms/{room_id}/workspace-connections/current`
  - `PUT /api/v1/rooms/{room_id}/workspace-connections/current`
  - `DELETE /api/v1/rooms/{room_id}/workspace-connections/current`
- the current room/workspace connection is persisted through a room-context item
  rather than a new room/workspace attachment table
- frontend room connection state now hydrates from backend truth instead of only
  local query cache

### Step 5: UX And Trust Review

After the room actually uses descriptors:

- revisit whether richer token scope is needed
- revisit whether direct endpoints remain acceptable for all current service kinds
- decide whether the next move is:
  - backend-proxied transport for some surfaces
  - or Track 4 expansion toward workspace-to-platform service trust

## Recommended Backend Focus

For the next Track 4 pass, backend work should focus on:

- keeping descriptor issuance explicit and purpose-scoped
- making room/workspace candidate selection cleaner
- supporting current-room consumption of descriptors

Not on:

- inventing a broad new transport abstraction
- adding many new descriptor fields without a consuming workflow

## Recommended Frontend Focus

For the next Track 4 pass, frontend work should focus on:

- replacing the “Workspace Links” inspector as the main experience with a more
  intentional room-side connection surface
- making descriptor status visible as part of room state
- using descriptors directly for service/runtime affordances

This is the moment where room/workspace connectivity should start feeling like a
real collaboration feature rather than a backend capability probe.

## Definition Of Done

This Track 4 slice should count as successful when:

- a room can identify a sensible workspace candidate
- the room can request and hold a current descriptor-backed connection state
- room UX uses descriptor-issued endpoints rather than inferred workspace URLs
- the current room/workspace connection state is visible and understandable

## Follow-On Recommendation

Once this slice is complete, the next sequencing review should choose between:

- deeper Track 4 transport/trust work
- or a return to Track 3 only if real usage exposes missing management authority

My current bias is:

- this descriptor-consumption slice is the right next move now
- and only after it lands should we decide whether proxying, token hardening, or
  workspace-to-platform trust is the next highest-leverage direction
