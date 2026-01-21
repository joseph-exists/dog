# Backend Implementation Guide: Room Runtime, Context Items, Agent Settings

This guide is the implementation companion to:
- `backend/docs/architecture/RoomContext_StoryState_and_ToolExposure.md`

It focuses on turning the **three required backend surfaces** into shippable services while keeping the ontology clear:
- **Canonical room runtime** (shared story run state)
- **Supplemental context items** (itemized attachments/injections)
- **Room agent settings** (prompt/tool policies with enforcement)

Where possible, it reuses existing primitives instead of introducing a new state engine.

---

## Key References (read in this order)

1) Architecture / ontology:
- `backend/docs/architecture/RoomContext_StoryState_and_ToolExposure.md`

2) Story definitions (authoring-time):
- `frontend/docs/story-management/story-state-schema/StoryStateSchema.md`
- `frontend/src/components/Stories/StoryEditor/StoryEditor.tsx`
- `frontend/src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx`
- `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx`
- `frontend/src/components/Stories/shared/StateConditionEditor.tsx`

3) Room/agent context building (agent-time):
- `backend/app/services/context_provider.py` (`build_room_context`)
- `backend/app/services/agent_context.py` (`RoomContextService`)
- `backend/app/services/agent_runner_streaming.py` (context build callsite)

4) Supplemental context plumbing:
- `backend/app/services/context_store.py` (`ContextItem`, `ContextItemStore`, `RedisContextStore`)

5) Progress primitives to reuse (canonical runtime state):
- `backend/app/models.py` (`UserStoryProgress`, `UserNodeChoice`, `ProgressSnapshot`)
- `backend/app/api/routes/user_story_progress.py` (existing progress endpoints/workflows)
- `backend/app/crud.py` (replay/snapshot-related functions)

---

## Ontology “Cheat Sheet” (the confusing parts)

### Canonical vs Derived vs Config

These terms are used consistently throughout the architecture doc. The implementation should preserve this separation.

1) **Canonical runtime state** (Room Runtime API)
- “What is true right now for this room’s shared run”
- Must be **rewindable** and consistent across clients
- Backed by **progress primitives**: `story_state` + head pointer + snapshots + choice history

2) **Derived context** (RoomContext projection / prompt rendering)
- “What we show to the agent/UI”
- Built from canonical state + definitions:
  - current node summary
  - active node-chain window
  - filtered available choices
  - summarized/redacted state

3) **Configuration/policy** (Room Agent Settings API)
- “What is allowed / how agents behave in this room”
- Must be **enforced** at agent instantiation/tool registration time
- Not merely “extra text in the prompt”

4) **Supplemental itemized context** (Context Item API)
- “Additional payloads attached to the room”
- Includes uploads, hotloads, notes, temporary facts, system injections, computed summaries
- Should not be the source of truth for progression or rewind

### Why `extra_contexts` is not the “room state”

`extra_contexts` is intentionally a **bag of items** with ordering rules. It is excellent for “attach and render” but poor as the canonical store for a rewindable story run unless you add heavy “latest-wins + pruning + replay” semantics.

Instead, canonical run state is modeled using the existing “progress system”:
- a mutable **current state block** (`story_state`)
- a head pointer (current node / head choice)
- an append-only choice history
- periodic immutable snapshots to make rewind/replay cheap

---

## Shared Principles (apply to all 3 surfaces)

### 1) Authorization model

Minimum baseline:
- **Read**: active room membership
- **Write**: room policy (owner-only by default, or explicit role grants)

Implementation note:
- Keep auth checks *room-centric* even if the underlying data is stored in progress tables keyed by a progress id.

### 2) Concurrency model

Use optimistic concurrency for UI-driven mutations:
- Include a `revision` (or `updated_at`) on the room-scoped wrapper
- Mutation requests should supply `expected_revision` (or `if-match`)
- Reject on mismatch (409) and force clients to refetch the runtime projection

This prevents “two clients advanced at once” or “rewind while advancing” races.

### 3) Eventing model

Emit events for:
- runtime transitions (start/advance/rewind/reset)
- context item changes (create/delete/replace)
- agent settings changes

Why:
- Room UI needs to update in real time (WS subscribers)
- Agents (and coordinators) may need to react to room changes

Where:
- follow existing room event conventions (`event_emitter` + WS replay/publish)

### 4) Payload constraints and validation

Guardrails should be consistent:
- explicit max size for context item payloads
- allowlisted `context_type` (and schema validation per type where feasible)
- sanitize/limit text fields that end up in prompts

### 5) “Projection first” API shape

For UI simplicity, each surface should prefer returning a **projection** over raw internal tables.
Example: runtime endpoint returns “current node + choices + state summary”, not “here is the entire progress event log”.

---

## Compare/Contrast: The Three Surfaces

| Surface | Owns | Mutability | Primary storage | Must support rewind? | Used by agents? |
|---|---|---:|---|---:|---:|
| Room Runtime API | shared canonical story run | high | Postgres progress primitives + room wrapper | yes | yes (via projection in `build_room_context`) |
| Context Item API | supplemental itemized context | medium | Redis list today (DB later) | no (except “replaceable” items) | yes (via `extra_contexts`) |
| Room Agent Settings API | prompt/tool policy | medium | DB (recommended) or room JSON fields | no | yes (enforced before run) |

Guiding rule:
- If it affects **where the story is** (node/head) or **what the state is**, it belongs in **Room Runtime**.
- If it affects **what agents are allowed to do**, it belongs in **Agent Settings**.
- If it is **extra information**, it belongs in **Context Items**.

---

## Surface 1: Room Runtime API (Shared Room Run)

### Objective

Make a room have exactly one shared run (“party progress”), reusing:
- `UserStoryProgress.story_state`
- `UserNodeChoice`
- `ProgressSnapshot`

And introducing a **room-scoped wrapper** that maps `room_id -> progress_id` for the active run.

### Data Model (required)

New persistent mapping is required somewhere:
- Option A: new table/model `RoomStoryProgress` (recommended)
- Option B: add fields to `Room` (less flexible; harder to support history/multiple runs)

Decision: implement **Option A** with a dedicated `RoomStoryProgress` table/model.

Minimum fields (recommended):
- `id` (UUID)
- `room_id` (unique; 1 active shared run per room)
- `story_id`
- `story_version`
- `active_progress_id` (FK to the underlying progress record that represents the current branch/head)
- `revision` (int, monotonically increasing)
- timestamps: `created_at`, `updated_at`
- (Optional) lifecycle: `started_at`, `ended_at`, `ended_reason`

Branching support (recommended additions):
- `active_branch_id` (UUID) or `branch_number` (int) to make “which branch are we on?” explicit in the UI.
- (Optional) `parent_progress_id` (FK) on a branch table, or stored on the progress record, to preserve ancestry.

### Runtime projection (read model)

The runtime projection is what the room UI and agents consume. It should include:
- story identity: `story_id`, `story_version`
- head: `current_node_id` (or derivable from head choice)
- `story_state` (typed/coerced and optionally summarized/redacted)
- active node-chain window:
  - define policy: ancestors+current, or sliding window, etc.
- available choices at head:
  - derived by evaluating `requires_state` against current `story_state`
- rewind metadata:
  - e.g., checkpoints, depth, or “can_rewind: bool”

### Operations

1) **Start/attach run**
- Preconditions: room has a story + version selected
- Steps:
  - create/attach progress record
  - initialize `story_state` from schema defaults (from `StoryStateVariable` for that story version)
  - set head to start node
  - set `RoomStoryProgress.progress_id`

2) **Advance**
- Inputs: `choice_id` (and `expected_revision`)
- Steps:
  - validate `requires_state`
  - apply `sets_state`
  - append choice to `UserNodeChoice`
  - update head pointer + `story_state`
  - create snapshot periodically
  - increment `revision`

3) **Rewind**
- Inputs: target checkpoint (choice id or node id), `expected_revision`
- Steps:
  - reconstruct the target `story_state` from nearest `ProgressSnapshot` + replay
  - create a **new progress record** representing the rewound state (branch)
  - set the room’s `active_progress_id` to the new progress record
  - increment `revision`

4) **Reset**
- Inputs: `expected_revision`
- Steps:
  - create a **new progress record** initialized to:
    - start node
    - schema default `story_state`
  - set the room’s `active_progress_id` to the new progress record
  - increment `revision`

Branching policy (decision):
- **Rewind and reset always branch** (they do not mutate or truncate the existing choice history).
- The previous progress branch remains available for audit/debugging and optional UI affordances (“return to prior branch”).

### Endpoints (illustrative)

Keep endpoints room-centric:
- `GET /rooms/{room_id}/runtime`
- `PUT /rooms/{room_id}/runtime` (select story/version + start)
- `POST /rooms/{room_id}/runtime/advance`
- `POST /rooms/{room_id}/runtime/rewind`
- `POST /rooms/{room_id}/runtime/reset`

### Integration requirement

`build_room_context(...)` should incorporate the runtime projection (or enough fields to build it) so agents reliably see:
- current node + node-chain context
- current state summary
- available choices (or at least the head choice set)

---

## Surface 2: Context Item API (Supplemental Context)

### Objective

Enable “add/remove/replace additional context while room is active” without mutating canonical run state.

### Storage

Current:
- `RedisContextStore` (`backend/app/services/context_store.py`) storing JSON in a Redis list key:
  - `room:{room_id}:contexts`

Future:
- DB-backed table if persistence/querying is needed.

### Required interface upgrades (for UI management)

The current `ContextItemStore` supports only:
- `add(item)`
- `list(room_id, agent_slug)`

For a UI “context manager”, you will almost certainly need at least one of:
- `delete(room_id, context_id)`
- `replace(room_id, context_id, item)` or `upsert(item)`
- “replace latest by (scope, context_type)” for settings-like items

This isn’t necessarily a DB model change, but it is a store/API change.

### Item taxonomy

To keep ontology clean, reserve `context_type` namespaces:
- `upload.*` for user uploads
- `note.*` for human-authored notes
- `system.*` for UI/system injections
- `shadow.*` for computed summaries (already exists)

### Endpoints (illustrative)

- `GET /rooms/{room_id}/contexts?agent_slug=...`
- `POST /rooms/{room_id}/contexts`
- `DELETE /rooms/{room_id}/contexts/{context_id}`
- optional replace/upsert endpoints if needed

### Integration requirement

`build_room_context(...)` already reads:
- room-wide items + agent-scoped items
- ordered deterministically
and exposes them as `RoomContext.extra_contexts`

That should remain the stable extension mechanism for “other objects” attached to room context.

---

## Surface 3: Room Agent Settings API (Prompt/Tool Policy)

### Objective

Let the room configure:
- agent prompt overrides
- tool allow/deny policies
- optional node-gated rules
with actual enforcement (not prompt-only).

### Storage (recommended)

Persist in a DB-backed model/table so settings:
- survive restarts
- can be audited and diffed
- can be validated with migrations

Minimum conceptual structure:
- `room_id`
- room defaults: prompt/tool policy JSON
- per-agent overrides: (room_id, agent_slug) rows or nested structure
- `revision`/`updated_at`

### Enforcement point (non-negotiable)

Enforcement must happen before the agent is run, e.g.:
- in `get_agent_instance_with_tools(...)` / tool registry path
- and/or in agent runner before building the instance

The prompt text can reflect settings, but settings must not rely on “the model will follow it”.

### Node-gated settings

If tools/prompts can depend on the current node (Use Case THREE), evaluate rules against the **runtime projection** from Surface 1:
- current node id
- story state variables
- story version

### Endpoints (illustrative)

- `GET /rooms/{room_id}/agent-settings` (returns effective config)
- `PUT /rooms/{room_id}/agent-settings` (defaults)
- `PUT /rooms/{room_id}/agents/{agent_slug}/agent-settings` (override)
- `DELETE /rooms/{room_id}/agents/{agent_slug}/agent-settings`

---

## Integration Points (how the system composes)

### 1) Building `RoomContext` for agent runs

At agent run time:
1. Fetch room metadata/messages/participants (existing behavior)
2. Fetch runtime projection for the shared room run (Surface 1) and include it in the context/prompt
3. Fetch `extra_contexts` from `ContextItemStore` (Surface 2)
4. Apply agent settings/tool policy (Surface 3) before instantiating the agent/tools

The important “ontology guarantee”:
- **progression + state** comes from Surface 1
- **supplemental items** come from Surface 2
- **tool/prompt policy** comes from Surface 3

### 2) UI composition

Room UI can be composed into panels that map 1:1 with the surfaces:
- Runtime panel: driven by `/rooms/{room_id}/runtime`
- Context panel: driven by `/rooms/{room_id}/contexts`
- Agent settings panel: driven by `/rooms/{room_id}/agent-settings`

This keeps mental models clean and makes it easier to enforce permissions per surface.

### 3) Shadow integration (optional but valuable)

Shadow already versions:
- room snapshots (participants/bindings) and story snapshots (nodes/choices/schema)

For room runtime:
- optionally version the runtime projection (or the underlying progress state/head) to Shadow on advance/rewind/reset
- this supports audit, summaries, and debugging “how did we get here”

---

## Suggested Implementation Order (minimize risk)

1) Implement the room-scoped wrapper mapping `room_id -> progress_id` + runtime projection endpoint (read-only).
2) Add start/advance/rewind/reset operations with revision-based concurrency and events.
3) Add Context Item API CRUD (and extend `ContextItemStore` for delete/upsert as needed).
4) Add Agent Settings API + enforcement at agent instantiation.
5) Integrate all three into `build_room_context`/agent runner composition.

---

## Implementation Status (living checklist)

This section records what has been implemented so far in the repo.

### Surface 1 (Room Runtime API) — Completed: Read-only projection skeleton

- Model: `RoomStoryProgress`, `RoomRuntimePublic` added in `backend/app/models.py`.
- Migration: `backend/app/alembic/versions/52ace76e75d8_add_room_story_progress.py`.
- CRUD: `get_room_runtime(...)` added in `backend/app/crud.py`.
- Route: `GET /rooms/{room_id}/runtime` implemented in `backend/app/api/routes/room_runtime.py` and wired in `backend/app/api/main.py`.
- Test: `backend/app/tests/api/routes/test_room_runtime.py` added (note: local test environment must include `pytest_asyncio` to run the suite).

### Surface 1 — Completed: Start/attach shared run (branching)

- Model: `RoomRuntimeStartRequest` added in `backend/app/models.py`.
- CRUD: `start_room_runtime(...)` added in `backend/app/crud.py` (owner-only; creates a new `UserStoryProgress` branch and updates `RoomStoryProgress.active_progress_id`).
- Route: `PUT /rooms/{room_id}/runtime` implemented in `backend/app/api/routes/room_runtime.py`.

### Surface 1 — Completed: Advance/Rewind/Reset (branching semantics)

- Models:
  - `RoomRuntimeAdvanceRequest`
  - `RoomRuntimeRewindRequest`
  - `RoomRuntimeResetRequest`
  (all in `backend/app/models.py`)
- CRUD:
  - `advance_room_runtime(...)`
  - `rewind_room_runtime(...)` (clones ancestor chain into a new progress branch)
  - `reset_room_runtime(...)` (branches to a new start state)
  (all in `backend/app/crud.py`)
- Routes:
  - `POST /rooms/{room_id}/runtime/advance`
  - `POST /rooms/{room_id}/runtime/rewind`
  - `POST /rooms/{room_id}/runtime/reset`
  (all in `backend/app/api/routes/room_runtime.py`)

### Surface 1 — Pending

### Surface 1 — Completed: Runtime projection enrichment

- `RoomRuntimePublic` now includes `current_node`, `node_chain`, and `available_choices`.
- Projection construction centralized in `_build_room_runtime_public(...)` inside `backend/app/crud.py`.

### Surface 1 — Completed: Runtime transition events

- Runtime transitions emit room events:
  - `room.runtime.started`
  - `room.runtime.advanced`
  - `room.runtime.rewound`
  - `room.runtime.reset`
  (emitted in `backend/app/crud.py`, handled as no-op projection updates in `backend/app/services/event_emitter.py`)

### Surfaces 2 & 3 — Pending

- Context Item API CRUD + store upgrades (delete/upsert/replace semantics)
- Room Agent Settings storage + API + enforcement at agent instantiation/tool registration

### Surface 2 — Completed: Context Item API (basic CRUD + delete)

- Models:
  - `RoomContextItemCreate`
  - `RoomContextItemPublic`
  - `RoomContextItemsPublic`
  (all in `backend/app/models.py`)
- Store:
  - `ContextItemStore.delete(...)` added
  - `InMemoryContextStore.delete(...)` implemented
  - `RedisContextStore.delete(...)` implemented
  (all in `backend/app/services/context_store.py`)
- CRUD:
  - `list_room_context_items(...)`
  - `add_room_context_item(...)`
  - `delete_room_context_item(...)`
  (all in `backend/app/crud.py`)
- Routes:
  - `GET /rooms/{room_id}/contexts`
  - `POST /rooms/{room_id}/contexts`
  - `DELETE /rooms/{room_id}/contexts/{context_id}`
  (all in `backend/app/api/routes/room_contexts.py`, wired in `backend/app/api/main.py`)

### Surface 2 — Pending

### Surface 2 — Completed: Upsert/replace + payload validation

- Validation:
  - `context_type`/`source` length checks
  - JSON-serializable payload enforcement
  - payload size limit (50KB)
  (in `backend/app/crud.py`)
- Upsert/replace:
  - `PUT /rooms/{room_id}/contexts/{context_id}` (upsert by id)
  - `replace_by_type` query flag to replace existing items with the same `context_type` + `agent_slug`
  - `POST /rooms/{room_id}/contexts?replace_by_type=true` uses upsert path
  (implemented in `backend/app/api/routes/room_contexts.py`, `backend/app/crud.py`)
- Events:
  - `room.context_item.created`
  - `room.context_item.deleted`
  - `room.context_item.upserted`
  (emitted in `backend/app/crud.py`, handled as no-op projection updates in `backend/app/services/event_emitter.py`)

### Surface 2 — Pending

- Allowlisted `context_type` rules beyond length/size validation
