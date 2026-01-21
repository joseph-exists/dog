# Room Context, Story State, and Tool Exposure (Architecture)

This document connects three domains that currently live in different parts of the codebase:

1. **Story definition** (authors define nodes/choices/state schema in Story + Node components)
2. **Room runtime** (players and agents interact in Rooms; story/node/state is loaded and evolves here)
3. **Agent execution** (agents consume `RoomContext` and optionally `extra_contexts`, and will eventually be gated by room-specific tool/prompt settings)

The goal is to make the mapping explicit so we can implement UI features for “managing a room’s context” without blurring:
- **canonical state** (what is true right now for this room/story run)
- **derived context** (what we render into prompts / display to users)
- **authoring-time definitions** (what stories/nodes/variables/conditions are allowed to be)

---

## Terminology

**Story definition (authoring-time)**
- Story metadata: title, description, publish/versioning rules
- Nodes: content blocks and transitions
- Choices: edges between nodes with `requires_state` and `sets_state`
- State schema: typed variable definitions used by conditions and mutations

**Room runtime (play-time)**
- Selected story (+ version) for the room session
- Current node, available choices, and current state values
- Active path (“node chain”) and any in-scope content that should remain visible as context
- History needed for “rewind” (choice history + periodic snapshots; see shared room run approach below)

**Room context (agent-time)**
- `RoomContext` built on-demand when an agent is run
- Includes: story metadata + recent messages + participants
- May include: `extra_contexts` (normalized multi-source context items)

---

## Current Implementation Snapshot

### 1) Story state schema (authoring-time)

Primary reference: `frontend/docs/story-management/story-state-schema/StoryStateSchema.md`.

Key points:
- Variables are **versioned per `story_version`**.
- Supported types: `boolean`, `number`, `string`, `enum`.
- Validation is a **soft block** (allow editing; block publish unless forced).

Frontend components (actual current code):
- Story editor shell: `frontend/src/components/Stories/StoryEditor/StoryEditor.tsx`
  - Includes “State Schema” via `StateSchemaSheet`.
- State schema UI:
  - `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaSheet.tsx`
  - `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx`
  - `frontend/src/components/Stories/StoryEditor/StateSchema/StateVariableModal.tsx`
  - Hooks: `frontend/src/hooks/stories/useStateSchema.ts`
- Choice condition + mutation authoring:
  - `frontend/src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx` uses:
    - `requires_state` + `sets_state`
    - `frontend/src/components/Stories/shared/StateConditionEditor.tsx` with optional schema for autocomplete/type coercion

What this means:
- “What variables exist” and “how choices reference/mutate them” is defined and validated in **Story/Node components**.
- The room UI should not re-define schema; it should *consume* it.

#### UI structure (from the legacy reference card, updated to match current components)

High-level layout intent (Story editor):
- Story editor shell (node tree + node editor + properties/actions)
- A state schema panel (“State Schema”) that opens a sheet and provides CRUD for variables
- Choice editor embeds schema-aware editors for:
  - `requires_state` (conditions)
  - `sets_state` (mutations)

Key UX behaviors (implemented in current code):
- Schema CRUD:
  - Table grouped by category
  - Add/edit modal for variables
  - Read-only gating when viewing a published version
- Choice condition/mutation editing:
  - Key suggestions from schema
  - Type-sensitive UI (booleans, enums, etc.)
  - Warnings when referencing undefined keys (supports publish-time validation)

Contract-ish props (current code shape; see referenced files for exact names):
- `StateSchemaSheet`: `storyId`, `version`, `isPublished`, `publishedVersion`
- `StateSchemaEditor`: `storyId`, `version`, `readOnly`
- `ChoiceEditor`: accepts `schema?: StoryStateVariablePublic[]` and passes it to `StateConditionEditor`

### 2) Room context building (agent-time)

Backend context construction:
- `backend/app/services/context_provider.py` (`build_room_context`)
- Wrapper: `backend/app/services/agent_context.py` (`RoomContextService`)

Execution path (high-level):
- REST message → `backend/app/api/routes/rooms.py` → `run_agents_for_message(...)`
- WS message → `backend/app/api/routes/websocket.py` → `run_agents_for_message(...)`
- Both flow into agent runners which call `RoomContextService.build(...)` → `build_room_context(...)`.

### 3) `extra_contexts` and the Context Store

Context store abstraction:
- `backend/app/services/context_store.py`
  - `ContextItem` (normalized room/agent-scoped context payload)
  - `InMemoryContextStore` (tests/dev)
  - `RedisContextStore` (default runtime store)

Aggregation into `RoomContext.extra_contexts`:
- `backend/app/services/context_provider.py`:
  - Loads from `context_store.list(room_id, agent_slug)`
  - Returns room-wide + agent-scoped items
  - Orders by `source` priority then `created_at`

Important caveat (today):
- The only production “writer” currently is **Shadow auto-injection** when a context store is provided:
  - `backend/app/services/context_provider.py` calls `build_shadow_context_items(...)`
  - `backend/app/services/shadow_context_loader.py` emits `ContextItem`s with `source="shadow"`

The UI-driven “room context manager” does not yet exist as an API surface.

---

## Why “Room Context Management” Needs Two Layers

The UI use cases we care about split into two different categories:

### A) Canonical runtime state (must be rewritable)
Example: “we are currently at node 4; rewind to node 2; revert state accordingly”.

This requires:
- a single **authoritative representation** of story progression and state
- support for **replace/rewind** semantics
- concurrency control (revisioning or transactions)

Trying to implement this as “append-only context items” is fragile unless we formalize “latest-wins by `context_type`” + pruning. For a shared run, the better fit is the existing progress pattern: a canonical state block (`story_state`) + head pointer + periodic immutable snapshots + replay between snapshots.

### B) Derived context for agents and UI (can be itemized)
Example: “attach an upload”, “inject a seed snippet”, “show a shadow summary”.

This fits the `ContextItem` model well:
- multiple sources (frontend/backend/seed/shadow)
- typed payloads
- optional TTL
- deterministic ordering

**Recommendation:** model runtime story state separately from `ContextItem`s, then generate context items (or direct prompt blocks) from runtime state.

---

## Proposed Mapping: Story/Node Definitions → Room Runtime → RoomContext

### 1) Story/Node side (definitions)
Owned by: Story editor UI + story APIs.

Inputs:
- Story schema (`StoryStateVariable*`)
- Nodes and choices (including `requires_state` / `sets_state`)

Outputs for runtime to consume:
- A specific story version and its graph (nodes + choices)
- A typed schema used to validate and coerce state

### 2) Room runtime side (canonical state)
Owned by: Rooms service layer, implemented as a **shared room run** using the existing progress primitives.

Instead of a new “room state engine”, represent the room’s canonical story run via:
- `UserStoryProgress.story_state` (the current “block” of state)
- `UserNodeChoice` history (the ordered sequence of choices taken)
- `ProgressSnapshot` (immutable snapshots created periodically for fast replay/rewind)

Add a small room-scoped wrapper (conceptual “RoomStoryProgress”) that selects the single active run for a room:
- `room_id`
- `story_id`
- `story_version`
- `active_progress_id` (points at the underlying progress + choice history + snapshots)
- optional `revision`/`updated_at` (optimistic concurrency for UI-driven edits)

Key operations (API-level intent):
- Load/start story in room:
  - create/attach a progress record, initialize `story_state` from the story’s state schema defaults, set head to start node
- Apply a choice / advance:
  - validate `requires_state` against `story_state`
  - apply `sets_state` to `story_state`
  - append to `UserNodeChoice` history, update head, and create `ProgressSnapshot` periodically
- Rewind:
  - branch to a new progress record at a previous checkpoint (reconstruct state from nearest `ProgressSnapshot` + replay, then set it as the active progress)

### 3) RoomContext side (agent-time projection)
Owned by: context provider + prompt builder.

How it should evolve:
- Extend `build_room_context(...)` to optionally include a **runtime story projection** that reflects the room’s canonical story run:
  - current node summary (title/content excerpt)
  - currently-available choices (text + requirements summary)
  - current state (ideally summarized / redacted, not raw full dict)
  - active path / “node chain” context (the nodes that remain in-scope for the current position, e.g. current node + ancestors or a configured sliding window)
- Keep `extra_contexts` for additional, orthogonal context items:
  - uploads, hotloads, seeds, shadow summaries, etc.

---

## Tool/Prompt Exposure (Room-Specific Configuration)

Use case: “users can adjust prompts per room” and “tools available in a room”.

This is **not just context**; it must be enforced at the point where agents are instantiated and tools are registered.

Where enforcement likely lives:
- Agent instance creation:
  - `get_agent_instance_with_tools(...)` (referenced from agent runner)
- Tool registry:
  - `backend/app/agents/tool_registry.py` (entry point for tools)
- Runner entry:
  - `backend/app/services/agent_runner_streaming.py` (calls instance factory)

Proposed configuration concepts:
- Room-level defaults:
  - tool allowlist/denylist
  - base prompt prefix/suffix override
- Per-agent overrides within a room:
  - additional instructions
  - tool overrides
- Node-gated exposure (Use Case THREE):
  - “tools enabled only when current node is X”
  - implemented as rules evaluated against the canonical runtime state

`ContextItem` can still be used to *display/audit* these settings, but enforcement should not depend on “did the prompt include it”.

---

## Implications for the UI

### Story/Node UI (definition + sorting)
The Story editor remains the place where:
- state schema is defined and organized (categories, descriptions)
- choice requirements/mutations are authored (requires/sets)

Core references:
- `frontend/src/components/Stories/StoryEditor/StoryEditor.tsx`
- `frontend/src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx`
- `frontend/src/components/Stories/StoryEditor/StateSchema/StateSchemaEditor.tsx`
- `frontend/src/components/Stories/shared/StateConditionEditor.tsx`

### Room UI (runtime editing + context management)
Rooms should be the place where:
- the story is loaded into a room session
- the current node/state is viewed and advanced/rewound
- room-specific prompt/tool settings are configured
- supplemental contexts (uploads/hotloads) are managed

This likely becomes two related UI panels:
1. **Room Runtime Panel** (canonical state): current node, choices, state, rewind controls
2. **Room Context Panel** (itemized): uploads/hotloads/seed/shadow + tool/prompt settings (with clear separation between “config” vs “content”)

---

## Required Backend Surfaces (for cohesive design)

1) **Room runtime API** (canonical story state)
- **Purpose:** own the single shared canonical run for a room (“party progress”) and expose safe operations for the room UI.
- **Source of truth:** Postgres progress primitives:
  - `UserStoryProgress.story_state` (canonical state “block”)
  - `UserNodeChoice` (choice history / event log)
  - `ProgressSnapshot` (periodic immutable snapshots)
  - plus a room-scoped wrapper mapping `room_id -> progress_id` (conceptual “RoomStoryProgress”)
- **Core read model:** a “runtime projection” suitable for both UI and agents:
  - story identity: `story_id`, `story_version`
  - head: `current_node_id` (or derived from head choice)
  - state: `story_state` (typed/coerced; optionally summarized/redacted)
  - active node-chain window (in-scope node content)
  - available choices at head (filtered by `requires_state`)
  - rewind capability metadata (e.g., available checkpoints / depth)
- **Write operations (must be atomic):**
  - Load/start story in room (create/attach the shared progress, initialize `story_state` from schema defaults, set head to start)
  - Apply choice / advance:
    - validate `requires_state` against current `story_state`
    - apply `sets_state` to state
    - append a `UserNodeChoice`, update head, and create `ProgressSnapshot` periodically
  - Rewind:
    - move head to a previous checkpoint
    - reconstruct state from nearest `ProgressSnapshot` + replay between snapshots
  - (Optional) reset to start (re-initialize to defaults and clear/branch history per policy)
- **Concurrency requirements:**
  - optimistic concurrency (e.g., `revision`/`updated_at` on the room wrapper) to prevent UI races
  - idempotent “advance” semantics (client supplies choice id + expected head/revision)
- **Auth requirements:**
  - room membership required to read
  - room policy required to mutate (e.g., owner-only vs member)
- **Eventing requirements (recommended):**
  - emit room events on state transitions (advance/rewind/reset) so clients can update in real time
  - optionally version room snapshots to Shadow on mutations for audit/summary
- **Suggested endpoints (illustrative):**
  - `GET /rooms/{room_id}/runtime` (projection)
  - `PUT /rooms/{room_id}/runtime` (attach/start story/version)
  - `POST /rooms/{room_id}/runtime/advance` (apply choice)
  - `POST /rooms/{room_id}/runtime/rewind` (rewind)
  - `POST /rooms/{room_id}/runtime/reset` (reset)

2) **Context item API** (supplemental context)
- **Purpose:** allow the UI (and backend) to attach additional, itemized context to a room without mutating canonical run state.
- **Storage:** `ContextItemStore` (`backend/app/services/context_store.py`) backed by Redis today; DB-backed later.
- **Read semantics:**
  - list room-wide + agent-scoped items (same rule used by `build_room_context`)
  - deterministic ordering for prompt/UI rendering (source priority + created_at)
- **Write semantics (extensibility requirement):**
  - support both:
    - **append-only** items (logs, uploads, evidence) and
    - **replaceable** items (settings-like context) via “upsert by `id`” and/or “replace latest by `context_type` + scope”
  - optional TTL (`expires_at`) for temporary context
- **API surface:**
  - `GET /rooms/{room_id}/contexts` (list; optional `agent_slug`)
  - `POST /rooms/{room_id}/contexts` (create; returns id)
  - `DELETE /rooms/{room_id}/contexts/{context_id}` (remove)
  - (Optional) `PUT /rooms/{room_id}/contexts/{context_id}` (replace)
- **Auth requirements:**
  - room membership required to read
  - room policy required to write (uploads may differ from config-like contexts)
- **Safety requirements:**
  - schema/size limits on payloads (prevent huge prompt injections)
  - explicit `context_type` allowlist or validation per type
  - provenance fields must be set (`source`, `created_at`, optional `created_by`)

3) **Room agent settings API** (prompt/tool config)
- **Purpose:** manage room-specific prompt/tool configuration with real enforcement (not “prompt-only”).
- **Scope:**
  - room-wide defaults (applies to all agents in the room)
  - per-agent overrides (applies to one agent slug)
  - optional node-gated rules (enabled only when runtime head satisfies conditions)
- **Enforcement point (requirement):**
  - must be applied at agent instantiation/tool registration time (e.g., `get_agent_instance_with_tools(...)`), not just appended to the prompt
- **Recommended shape:**
  - prompt overrides: prefix/suffix/instructions blocks, with clear precedence rules
  - tool policy: allowlist/denylist + per-tool config overrides
  - rule system (optional): conditions evaluated against room runtime projection (current node, state vars, story version)
- **API surface (illustrative):**
  - `GET /rooms/{room_id}/agent-settings` (room + per-agent effective config)
  - `PUT /rooms/{room_id}/agent-settings` (update room defaults)
  - `PUT /rooms/{room_id}/agents/{agent_slug}/agent-settings` (override)
  - `DELETE /rooms/{room_id}/agents/{agent_slug}/agent-settings` (clear override)
- **Auth + audit requirements:**
  - owner-only by default (or explicitly granted roles)
  - every change should be auditable (event + optional Shadow version)
  - safe validation of tool exposure (deny dangerous tools by default)

---

## Appendix: Legacy Reference Card

The older “reference card” for state schema editor integration lives at:
- `frontend-legacy/legacy-docs-need-sorting-revision/StateSchemaEditorIntegration.md`

That document is useful as a checklist of UX features (schema drawer/sheet, modal CRUD, schema-aware condition editor), but the cohesive architecture requires the additional mapping in this doc:
- “defined in Story/Node components” ↔ “used/edited in Rooms” ↔ “projected into agent `RoomContext`”.
