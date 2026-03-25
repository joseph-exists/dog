# Room Workspace Current Connection Roadmap

## Recommendation

The next Track 4 slice should make the room's current workspace connection a
backend-recognized fact, while tightening descriptor scope enough that room and
workspace trust is easier to reason about.

This is the right next move because the room now has a real descriptor-backed
workflow, but the current connection still lives only in frontend state.

## Why This Slice

The present implementation is useful, but it still has two soft spots:

- reloading the room loses the selected connection
- token and endpoint scope are still described mostly by convention

That means the next step should not be a broad transport abstraction. It should
be a narrow backend convenience layer that makes the current room/workspace
connection durable and legible.

## Scope

This pass should implement:

- a backend current-connection convenience surface
- room-scoped persistence of selected workspace and purpose
- backend projection of the current descriptor-backed connection
- explicit endpoint scope metadata for room/workspace descriptors
- frontend hydration from backend truth instead of local-only cache

This pass should not yet implement:

- generalized descriptor proxying
- multi-workspace attachment per room
- long-lived bearer credentials
- a new room/workspace join table

## Design Intent

The system should answer this question clearly:

- what workspace connection is this room currently using, and what exactly was granted?

The answer should be:

1. room selects a workspace and purpose
2. backend validates and issues a descriptor
3. backend stores a narrow current-connection record for the room
4. room hydrates from that backend record
5. endpoint descriptors carry explicit scope and expiry semantics

## Proposed Implementation Sequence

### Step 1: Backend Current Connection Projection

Add backend models and service helpers for a current room/workspace connection.

Recommendation:

- persist this via room context items, not a new room table field
- treat it as a narrow convenience record, not a general attachment model

First-pass route surface:

- `GET /api/v1/rooms/{room_id}/workspace-connections/current`
- `PUT /api/v1/rooms/{room_id}/workspace-connections/current`
- `DELETE /api/v1/rooms/{room_id}/workspace-connections/current`

The current record should store only:

- `workspace_id`
- `purpose`
- enough candidate summary to keep room UX legible

The route should project the latest descriptor-backed state on read rather than
blindly trusting stale payload.

Status:

- implemented
- the backend now persists current room/workspace connection intent via a room
  context item and re-projects live descriptor state on read

### Step 2: Descriptor Scope Tightening

Add explicit scope metadata to issued endpoints.

Recommendation:

- scope should bind to:
  - `room_id`
  - `workspace_id`
  - `purpose`
  - `endpoint_id`
- keep expiry short
- keep first-pass auth simple and descriptive even if transport remains direct

This should make token semantics clearer before any proxying discussion.

Status:

- implemented for the current descriptor contract
- endpoint descriptors now carry explicit scope fields for:
  - `room_id`
  - `workspace_id`
  - `purpose`
  - `endpoint_id`

### Step 3: Frontend Hydration And Mutation Alignment

Update room connection hooks and panels to use backend current-connection truth.

Expected result:

- room reload preserves current connection
- room UX can read current connection without first revisiting the inspector
- current connection changes invalidate and refresh cleanly

Status:

- implemented
- room connection hooks now hydrate current connection state from backend truth
- room-side UX writes current connection through backend routes instead of
  frontend-only cache updates

### Step 4: UX And Trust Review

After this slice lands:

- review whether direct endpoint issuance remains acceptable
- decide whether some service kinds want proxying
- decide whether room-side tools need a backend "consume descriptor" helper

## Definition Of Done

This slice should count as successful when:

- the room can persist a current workspace connection across reloads
- backend routes expose the current connection cleanly
- descriptors carry explicit scope metadata
- the frontend hydrates current connection state from backend truth
- the trust story is clearer without introducing a broad transport rewrite
