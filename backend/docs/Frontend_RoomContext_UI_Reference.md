# Frontend Reference: Room Context UI Surfaces

This document is a frontend-facing reference for the next UI set, based on:
- `backend/docs/architecture/RoomContext_BackendSurfaces_ImplementationGuide.md`
- `backend/docs/architecture/RoomContext_StoryState_and_ToolExposure.md`

It defines the UI components needed for:
A) Story/Node -> Room integration
B) AG-UI Canvas
C) Prompt + context updates in-room

---

## Goals

- Provide a stable UI contract for the three backend surfaces: Room Runtime, Context Items, Agent Settings.
- Keep the ontology clear: canonical runtime state vs derived context vs configuration.
- Give the frontend team a concrete component breakdown and data expectations.

---

## Ontology Cheat Sheet (do not blur these)

1) Canonical runtime state (Room Runtime API)
- Shared, rewindable story run state for a room.
- Backed by progress primitives; concurrency protected.

2) Derived context (RoomContext projection)
- What the UI and agents render: current node, node chain, available choices, summarized state.
- Built from canonical state + story definitions.

3) Configuration/policy (Room Agent Settings API)
- Prompt/tool policy that must be enforced at agent instantiation.

4) Supplemental itemized context (Context Item API)
- Attachments, notes, uploads, system injects, shadow summaries.
- Not the source of truth for story progression.

---

## Glossary

- Room runtime: the shared, canonical story run for a room (rewindable, concurrency-protected).
- Runtime projection: UI-friendly read model for the room runtime; not the full event log.
- Story state: the current story variable block for a room run (`story_state`).
- Node chain: the in-scope path of nodes shown as context for the current head.
- Available choices: choices filtered by `requires_state` for the current head.
- Revision: monotonic token used for optimistic concurrency on runtime and settings updates.
- Expected revision: client-sent token to prevent concurrent conflicts (409 on mismatch).
- Context item: supplemental itemized payload attached to a room (`ContextItem`).
- Context type: allowlisted namespace for context items (`upload.*`, `note.*`, `system.*`, `shadow.*`).
- Agent slug: stable identifier for an agent configuration in a room.
- Prompt config: JSON rules for prompt prefix/suffix or instructions at room/agent scope.
- Tool policy: JSON rules for tool allow/deny lists and per-tool overrides.
- Rule config: JSON rules gated by runtime state (current node, state vars, story version).
- Replace by type: upsert mode that replaces the latest item matching `context_type` + scope.

---

## UI Surface Map (high level)

The room UI should map to three panels/surfaces:

1) Room Runtime Panel
- Drives the canonical story run.
- Reads from `/rooms/{room_id}/runtime`.
- Writes via advance/rewind/reset operations.

2) Context Items Panel
- Manages supplemental, itemized context.
- Reads/writes via `/rooms/{room_id}/contexts`.

3) Agent Settings Panel
- Manages prompt/tool policy per room and per agent.
- Reads/writes via `/rooms/{room_id}/agent-settings`.

AG-UI Canvas stitches these surfaces into a unified operator experience.

---

## A) Story/Node -> Room Integration

### Purpose
Bridge authoring-time story definitions with a room's live, shared runtime state.

### Required UI Components

1) Story Loader
- Select story + version for a room.
- Start/attach the shared run (PUT `/rooms/{room_id}/runtime`).

2) Runtime Inspector
- Current node summary (title + content excerpt).
- Node chain window (ancestors + current, or a defined sliding window).
- Current story state (summarized/redacted view; not raw debug dump).
- Available choices (filtered by `requires_state`).

3) Runtime Controls
- Advance by choice (POST `/rooms/{room_id}/runtime/advance`).
- Rewind to checkpoint (POST `/rooms/{room_id}/runtime/rewind`).
- Reset to start (POST `/rooms/{room_id}/runtime/reset`).
- Show revision/conflict resolution for concurrent edits.

### Data Contract Expectations

Runtime projection (read model) should include:
- `story_id`, `story_version`
- `current_node` or `current_node_id`
- `node_chain` (in-scope nodes)
- `available_choices` (filtered by state)
- `story_state` (typed, summarized)
- `revision` (optimistic concurrency)
- optional rewind metadata (checkpoint depth, etc.)

### UX Notes
- Treat runtime as a single shared room run ("party progress").
- Rewind/reset branches the run; do not overwrite prior history.
- Use optimistic concurrency (409) to force refetch and avoid dual-advance races.

---

## B) AG-UI Canvas

### Purpose
Provide a unified, live operational surface for runtime, context, and agent controls.

### Suggested Layout

Left rail
- Story loader + runtime inspector
- Node chain view (scrollable)

Center canvas
- Live room activity feed (messages + system/runtime events)
- AG run stream (token stream + final response)

Right rail
- Context Items panel
- Agent Settings panel

### Required Canvas Behaviors

- Live updates via room events:
  - `room.runtime.started`
  - `room.runtime.advanced`
  - `room.runtime.rewound`
  - `room.runtime.reset`
  - `room.context_item.*`
  - `room.agent_settings.*`
- Minimal state duplication: rely on runtime projection + context list endpoints.
- Clear separation of canonical state vs supplemental items.

---

## C) Prompt + Context Updates in Room

### Context Items Panel

Purpose:
- Manage attachments, notes, system injections, and shadow summaries.

Core capabilities:
- List items (GET `/rooms/{room_id}/contexts`)
- Add item (POST `/rooms/{room_id}/contexts`)
- Delete item (DELETE `/rooms/{room_id}/contexts/{context_id}`)
- Replace/upsert item (PUT `/rooms/{room_id}/contexts/{context_id}`)
- Optional replace-by-type behavior (query `replace_by_type=true`)

Item conventions:
- `context_type` must be allowlisted:
  - `upload.*`, `note.*`, `system.*`, `shadow.*`
- Payloads must be JSON-serializable and size-limited (50KB cap).
- Items can be room-wide or agent-scoped.

UX Notes:
- Show source and created_at metadata.
- Highlight "replaceable" items (settings-like content).
- Use ordering: source priority then created_at.

### Agent Settings Panel

Purpose:
- Configure room-level and per-agent prompt/tool policies.

Core capabilities:
- Read effective config (GET `/rooms/{room_id}/agent-settings`)
- Update room defaults (PUT `/rooms/{room_id}/agent-settings`)
- Update per-agent overrides (PUT `/rooms/{room_id}/agents/{agent_slug}/agent-settings`)
- Clear override (DELETE `/rooms/{room_id}/agents/{agent_slug}/agent-settings`)

UI expectations:
- Explicit distinction between room defaults vs per-agent overrides.
- Show last updated + revision.
- Explain that enforcement happens before agent instantiation (not just prompt text).

Node-gated policy (if enabled):
- Allow tools/prompts only when current node/state matches conditions.
- Requires access to runtime projection in the UI.

---

## Endpoint Data Shapes + Workflows (verified from backend models)

Notes:
- Shapes below are derived from `backend/app/models.py` and route response models.
- UUIDs and timestamps are example values; fields shown are required or commonly present.

### Room Runtime Endpoints

Use case: load the current shared run when entering a room.

GET `/rooms/{room_id}/runtime` response:
```json
{
  "room_id": "1c7f2d5a-9d3d-4b7f-9cbe-9d2e5b2f1f10",
  "story_id": "c2c8f0f1-7c0f-4a2e-90c5-6f1ed3b1a2aa",
  "story_version": 3,
  "active_progress_id": "9f2f3a90-6f24-4d7c-92c4-7f7f8ea2e7b9",
  "revision": 12,
  "current_node_id": "b60e56a7-2b5d-44d5-9b78-1d1e3b5b9c2a",
  "head_choice_id": "7c6b0c4f-74df-4c7f-a3b9-12b815a2c009",
  "head_version": 3,
  "story_state": {
    "has_key": true,
    "trust": 2
  },
  "updated_at": "2024-10-08T19:52:32.120Z",
  "current_node": {
    "id": "b60e56a7-2b5d-44d5-9b78-1d1e3b5b9c2a",
    "story_id": "c2c8f0f1-7c0f-4a2e-90c5-6f1ed3b1a2aa",
    "story_version": 3,
    "title": "The Foyer",
    "content": "A locked door blocks the path.",
    "content_format": "text",
    "node_type": null,
    "is_start_node": false,
    "is_end_node": false,
    "created_at": "2024-10-08T19:50:00.000Z",
    "updated_at": "2024-10-08T19:51:10.000Z"
  },
  "node_chain": [
    {
      "id": "a1f1f7b3-44e2-4eaa-b7d3-38a2b6f8241f",
      "story_id": "c2c8f0f1-7c0f-4a2e-90c5-6f1ed3b1a2aa",
      "story_version": 3,
      "title": "Arrival",
      "content": "You step into the hall.",
      "content_format": "text",
      "node_type": null,
      "is_start_node": true,
      "is_end_node": false,
      "created_at": "2024-10-08T19:49:00.000Z",
      "updated_at": "2024-10-08T19:49:20.000Z"
    }
  ],
  "available_choices": [
    {
      "id": "7c6b0c4f-74df-4c7f-a3b9-12b815a2c009",
      "from_node_id": "b60e56a7-2b5d-44d5-9b78-1d1e3b5b9c2a",
      "to_node_id": "3f6d6bb1-2d44-4b6e-9b47-6a24e119fe49",
      "text": "Try the key",
      "order": 0,
      "requires_state": {
        "has_key": true
      },
      "sets_state": {
        "trust": 3
      }
    }
  ]
}
```

Use case: attach/start a story run in a room (Story loader).

PUT `/rooms/{room_id}/runtime` request:
```json
{
  "user_persona_id": "6d92397a-7357-4a02-9c84-c9ef5c1c9e12",
  "story_version": 3,
  "expected_revision": 11
}
```

PUT `/rooms/{room_id}/runtime` response: same shape as GET runtime.

Use case: advance the runtime by selecting a choice.

POST `/rooms/{room_id}/runtime/advance` request:
```json
{
  "choice_id": "7c6b0c4f-74df-4c7f-a3b9-12b815a2c009",
  "expected_revision": 12
}
```

POST `/rooms/{room_id}/runtime/advance` response: same shape as GET runtime.

Use case: rewind the runtime to a prior choice (branching).

POST `/rooms/{room_id}/runtime/rewind` request:
```json
{
  "target_choice_id": "2a9c1d93-b41a-4a54-8d5a-1c5a707d2b4b",
  "expected_revision": 12
}
```

POST `/rooms/{room_id}/runtime/rewind` response: same shape as GET runtime.

Use case: reset the runtime to the start node (branching).

POST `/rooms/{room_id}/runtime/reset` request:
```json
{
  "expected_revision": 12
}
```

POST `/rooms/{room_id}/runtime/reset` response: same shape as GET runtime.

### Context Items Endpoints

Use case: fetch room-wide + agent-scoped context items for display.

GET `/rooms/{room_id}/contexts?agent_slug=planner` response:
```json
{
  "data": [
    {
      "id": "ctx_9a23c7d1",
      "room_id": "1c7f2d5a-9d3d-4b7f-9cbe-9d2e5b2f1f10",
      "agent_slug": null,
      "context_type": "upload.transcript",
      "payload": {
        "title": "Interview Transcript",
        "file_url": "https://example.invalid/transcripts/42"
      },
      "source": "user",
      "created_at": "2024-10-08T19:55:12.000Z",
      "expires_at": null
    }
  ],
  "count": 1
}
```

Use case: attach a new context item (upload, note, or system inject).

POST `/rooms/{room_id}/contexts` request:
```json
{
  "context_type": "note.operator",
  "payload": {
    "text": "Prioritize the main thread; avoid side quests."
  },
  "source": "user",
  "agent_slug": null,
  "expires_at": null
}
```

POST `/rooms/{room_id}/contexts` response:
```json
{
  "id": "ctx_1d5b9134",
  "room_id": "1c7f2d5a-9d3d-4b7f-9cbe-9d2e5b2f1f10",
  "agent_slug": null,
  "context_type": "note.operator",
  "payload": {
    "text": "Prioritize the main thread; avoid side quests."
  },
  "source": "user",
  "created_at": "2024-10-08T19:56:40.000Z",
  "expires_at": null
}
```

Use case: update a replaceable item (e.g., system summary) by id.

PUT `/rooms/{room_id}/contexts/{context_id}` request:
```json
{
  "context_type": "system.summary",
  "payload": {
    "summary": "Current room state and recent actions summarized here."
  },
  "source": "system",
  "agent_slug": null,
  "expires_at": null
}
```

PUT `/rooms/{room_id}/contexts/{context_id}` response: same shape as POST response.

Use case: replace latest item by type (settings-like behavior).

POST `/rooms/{room_id}/contexts?replace_by_type=true` request:
```json
{
  "context_type": "system.summary",
  "payload": {
    "summary": "Updated summary after new events."
  },
  "source": "system",
  "agent_slug": null,
  "expires_at": null
}
```

Use case: delete a context item.

DELETE `/rooms/{room_id}/contexts/{context_id}` response:
```json
{
  "status": "ok"
}
```

### Agent Settings Endpoints

Use case: load effective room defaults and per-agent overrides for the panel.

GET `/rooms/{room_id}/agent-settings` response:
```json
{
  "room_defaults": {
    "id": "e469cd37-40a3-4a5e-9b88-03fd9d36d2e1",
    "room_id": "1c7f2d5a-9d3d-4b7f-9cbe-9d2e5b2f1f10",
    "agent_slug": null,
    "prompt_config": {
      "prefix": "You are the room guide.",
      "suffix": "Always ask one clarifying question."
    },
    "tool_policy": {
      "allow": ["search", "summary"],
      "deny": ["write_file"]
    },
    "rule_config": null,
    "revision": 2,
    "created_at": "2024-10-08T19:40:00.000Z",
    "updated_at": "2024-10-08T19:45:00.000Z"
  },
  "agent_overrides": [
    {
      "id": "dbb8c2c9-8f2b-4f4e-8d1a-9a2b165c2c62",
      "room_id": "1c7f2d5a-9d3d-4b7f-9cbe-9d2e5b2f1f10",
      "agent_slug": "planner",
      "prompt_config": {
        "prefix": "You are the planning specialist."
      },
      "tool_policy": {
        "allow": ["summary"]
      },
      "rule_config": null,
      "revision": 1,
      "created_at": "2024-10-08T19:46:00.000Z",
      "updated_at": "2024-10-08T19:47:00.000Z"
    }
  ]
}
```

Use case: update room defaults (global prompt/tool policy).

PUT `/rooms/{room_id}/agent-settings` request:
```json
{
  "prompt_config": {
    "prefix": "You are the room guide.",
    "suffix": "Keep responses under 200 tokens."
  },
  "tool_policy": {
    "allow": ["search", "summary"],
    "deny": ["write_file"]
  },
  "rule_config": null,
  "expected_revision": 2
}
```

PUT `/rooms/{room_id}/agent-settings` response: same shape as `RoomAgentSettingsPublic`.

Use case: override for a specific agent.

PUT `/rooms/{room_id}/agents/{agent_slug}/agent-settings` request:
```json
{
  "prompt_config": {
    "prefix": "You are the scene director."
  },
  "tool_policy": {
    "allow": ["summary"]
  },
  "rule_config": {
    "only_when": {
      "current_node_id": "b60e56a7-2b5d-44d5-9b78-1d1e3b5b9c2a"
    }
  },
  "expected_revision": 1
}
```

PUT `/rooms/{room_id}/agents/{agent_slug}/agent-settings` response: same shape as `RoomAgentSettingsPublic`.

Use case: remove a per-agent override (fall back to room defaults).

DELETE `/rooms/{room_id}/agents/{agent_slug}/agent-settings` response:
```json
{
  "status": "ok"
}
```

---

## Eventing + Realtime

All three surfaces emit room events for live updates.
The frontend should subscribe to room events and refresh the relevant projection:
- Runtime transitions trigger runtime re-fetch.
- Context item changes trigger context list re-fetch.
- Agent settings changes trigger settings re-fetch.

Do not attempt to derive canonical runtime state from event payloads alone.
Always use the projection endpoints as source-of-truth for UI state.

---

## Open Questions / Frontend TODOs

- Do we want a dedicated "runtime checkpoint picker" UI (depth list vs timeline)?
- How should node-chain window be displayed on small screens?
- Should context items be grouped by `context_type` or by source?
- Do we need an inline policy preview for tools disabled by node-gated rules?

---

## Quick Reference: API Endpoints

Room runtime:
- GET `/rooms/{room_id}/runtime`
- PUT `/rooms/{room_id}/runtime`
- POST `/rooms/{room_id}/runtime/advance`
- POST `/rooms/{room_id}/runtime/rewind`
- POST `/rooms/{room_id}/runtime/reset`

Context items:
- GET `/rooms/{room_id}/contexts`
- POST `/rooms/{room_id}/contexts`
- PUT `/rooms/{room_id}/contexts/{context_id}`
- DELETE `/rooms/{room_id}/contexts/{context_id}`

Agent settings:
- GET `/rooms/{room_id}/agent-settings`
- PUT `/rooms/{room_id}/agent-settings`
- PUT `/rooms/{room_id}/agents/{agent_slug}/agent-settings`
- DELETE `/rooms/{room_id}/agents/{agent_slug}/agent-settings`
