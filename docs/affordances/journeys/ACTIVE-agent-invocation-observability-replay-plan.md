# Agent Invocation Observability And Replayability Plan

Status: `backend first pass implemented`
Created: `2026-04-25`
Owner: `LLM agent / backend-first implementation`

## Purpose

Close two related gaps:

1. Operators cannot inspect the exact `full_prompt` and structured context sent
   to an agent.
2. Replaying room events does not reconstruct agent invocation inputs after
   prompt/context/runtime code changes.

The target outcome is an auditable agent invocation record that captures the
model-facing input at run time, links it to room events/messages, and can later
be mirrored into Shadow snapshots for longer-term forensic replay.

## Current Constraints

- `build_agent_prompt(...)` returns `full_prompt` in memory.
- `StreamingAgentRunner.run(...)` sends `full_prompt` directly to the model.
- `AgentEventPublisher.emit_message(...)` persists only the final agent
  response as `room_message.agent`.
- `event_replay.py` replays persisted `RoomEvent` payloads only; it does not
  replay prompt construction.
- `shadow_context_loader.py` contributes prompt context but is not durable
  invocation storage.
- `shadow_exporters.py` can be extended for durable snapshots, but Shadow is
  best-effort/outbox-oriented and should not be the only primary audit store.

## Architecture Decision

Use a primary database audit record for immediate, queryable invocation
observability. Then add a Shadow exporter as an optional durability mirror.

Do not store exact prompts directly in normal `room_message.agent` event
payloads. Room events are broadcast and replayed to clients; exact prompt input
may include sensitive context. Instead:

- Store invocation data in a dedicated backend model/table.
- Link invocation records to room id, agent slug, trigger message, resulting
  event/message where possible.
- Expose redacted debug reads to authorized users.
- Mirror redacted/full snapshots to Shadow only if policy allows.

## Proposed Data Model

Add `AgentInvocation` to `backend/app/models.py`.

Suggested fields:

- `id: uuid.UUID`
- `room_id: uuid.UUID`
- `agent_slug: str`
- `trigger_message: str`
- `trigger_source: str`
  - examples: `room_message`, `manual`, `a2a_tool`, `ui_action`, `runtime_event`
- `a2a_depth: int`
- `acting_user_id: uuid.UUID | None`
- `room_context_json: dict[str, Any]`
  - structured `RoomContext` snapshot after dataclass serialization
- `story_runtime_json: dict[str, Any] | None`
  - convenience denormalization for debug UI
- `full_prompt: str | None`
  - nullable for redaction policies
- `full_prompt_redacted: str | None`
- `prompt_sha256: str`
- `prompt_builder_version: str`
  - start with a constant in `agent_prompt.py`
- `model_name: str | None`
- `runtime_prompt_payload: dict[str, Any] | None`
  - from `agent._runtime_prompt_payload` if present
- `runtime_prompt_provenance: dict[str, Any] | None`
  - from `agent._runtime_prompt_provenance` if present
- `request_limit: int | None`
- `response_text: str | None`
- `response_event_id: uuid.UUID | None`
- `response_message_id: uuid.UUID | None`
- `success: bool | None`
- `error: str | None`
- `started_at: datetime`
- `completed_at: datetime | None`

Checklist:
- [x] Add SQLModel table. (use project conventions.)
- [x] Add public/read DTOs with redacted-safe fields.
- [x] Add alembic migration file. (Migration still needs to be applied per environment.)
- [x] Add indexes for `(room_id, started_at)` and `(room_id, agent_slug, started_at)`.

## Slice 1: Serialization Helpers

Goal: Convert the in-memory context/prompt material into stable JSON.

Files:
- `backend/app/services/agent_invocation_audit.py` new
- `backend/app/services/agent_prompt.py`
- `backend/app/tests/services/test_agent_invocation_audit.py` new

Steps:
1. Add `PROMPT_BUILDER_VERSION = "agent_prompt.v1"` in `agent_prompt.py`.
2. Create `serialize_room_context(context: RoomContext) -> dict[str, Any]`.
3. Ensure dataclasses serialize consistently:
   - `story_data`
   - `story_runtime`
   - `recent_messages`
   - `participants`
   - `room_metadata`
   - `active_agents`
   - `extra_contexts`
4. Create `redact_prompt(full_prompt: str) -> str`.
   - Initial implementation can return the full prompt for superuser-only
     reads, but still include the function boundary now.
5. Create `hash_prompt(full_prompt: str) -> str`.

Checklist:
- [x] Unit test serializes `StoryRuntimeContext`.
- [x] Unit test prompt hash is stable.
- [x] Unit test redaction function is deterministic.

## Slice 2: Primary Invocation Persistence

Goal: Persist an invocation record before and after model execution.

Files:
- `backend/app/models.py`
- `backend/app/services/agent_invocation_audit.py`
- `backend/app/services/agent_runner_streaming.py`
- `backend/app/services/agent_tools.py`
- `backend/app/services/agent_events.py`
- tests under `backend/app/tests/services/`

Steps:
1. Add `create_agent_invocation(...)`.
   - Called after `full_prompt` is built and before `agent.run_stream(...)`.
   - Captures context snapshot, story runtime snapshot, full prompt/redaction,
     prompt hash, model metadata, request limit, user id, room id, agent slug,
     trigger source, and A2A depth.
2. Add `complete_agent_invocation(...)`.
   - Called after final response or error.
   - Stores response text, success/error, completed timestamp.
3. Modify `StreamingAgentRunner.run(...)`:
   - create audit record before model call;
   - complete audit record after response emission;
   - complete with error details in exception paths.
4. Modify `AgentEventPublisher.emit_message(...)` to return the emitted
   `RoomEvent` so the invocation can link to `response_event_id`.
5. If `RoomMessage.message_id` linkage is needed immediately, add a lookup by
   event fields after flush or adjust `emit_event`/projection handler to return
   projection ids in metadata. Keep this optional for the first slice.
6. Modify `_run_agent_for_tool_call(...)` in `agent_tools.py`.
   - Capture non-streaming A2A tool invocations with `trigger_source="a2a_tool"`.
   - No room response event is expected for this path.

Checklist:
- [x] Streaming success creates and completes invocation.
- [ ] Streaming model error completes invocation with error.
- [x] A2A tool call creates an invocation without a room message event.
- [x] Existing agent response behavior is unchanged.

## Slice 3: Debug Read API

Goal: Let authorized room users inspect invocation inputs without exposing them
through normal room event replay.

Files:
- `backend/app/api/routes/agent_invocations.py` new
- `backend/app/api/main.py`
- `backend/app/crud.py` or `backend/app/services/agent_invocation_audit.py`
- generated frontend client after OpenAPI refresh

Endpoints:

```text
GET /api/v1/rooms/{room_id}/agent-invocations
GET /api/v1/rooms/{room_id}/agent-invocations/{invocation_id}
```

Authorization:
- active room membership can list redacted summaries;
- room owner or superuser can view full prompt if policy allows;
- default response should be redacted.

Checklist:
- [x] List endpoint returns latest invocations for room.
- [x] Detail endpoint returns structured `story_runtime_json`.
- [x] Detail endpoint returns redacted prompt by default.
- [x] Unauthorized room user receives 403 or opaque 404 per local convention.
- [ ] Superuser/owner full-prompt policy is covered by tests.

## Slice 4: Frontend DebugPanel Integration

Goal: Replace the approximate-only view with an exact backend invocation view,
while preserving the current lightweight preview.

Files:
- `frontend/src/components/Room/panels/DebugPanel.tsx`
- `frontend/src/components/Room/panels/RoomDebugPanel.tsx`
- `frontend/src/services/roomService.ts` or new
  `frontend/src/services/agentInvocationService.ts`
- `frontend/src/hooks/useAgentInvocations.ts` new

Steps:
1. Add a hook to fetch recent invocations for the room.
2. Add a collapsible section: `Agent Invocations`.
3. Show:
   - agent slug/name
   - started/completed timestamps
   - success/error
   - prompt hash
   - trigger source
   - story runtime current node
   - response event id if linked
4. Add a detail drawer/collapsible for:
   - structured `story_runtime_json`
   - structured `room_context_json`
   - redacted/full prompt depending on API response
5. Rename current `API Payload Preview` copy to make its approximation explicit,
   e.g. `Message Context Preview`.

Checklist:
- [x] Debug panel still works without invocation records.
- [x] Existing active-context display remains.
- [x] New exact invocation panel distinguishes exact backend snapshot from
      frontend approximation.
- [x] Prompt copy button copies only what the API returned.

## Slice 5: Event Linkage And Replay Semantics

Goal: Make replay behavior explicit.

Files:
- `backend/app/services/agent_events.py`
- `backend/app/services/event_emitter.py`
- `backend/app/services/event_replay.py`
- `backend/app/services/service-docs/event_sourcing_realtime_flow.md`
- `docs/affordances/journeys/agent-story-room-gap-validation.md`

Steps:
1. Keep `event_replay.py` focused on replaying room events.
2. Add `agent_invocation_id` to `room_message.agent` event
   `enrichment_metadata`, not the broadcast payload.
3. Decide whether `event_replay.py` should include enrichment metadata.
   - Recommended default: no.
   - Debug endpoint should fetch invocation details separately.
4. Document that event replay restores visible room state, while invocation
   replay/debug reads restore model input snapshots.

Checklist:
- [x] Event replay output remains backwards compatible.
- [x] Agent response event can be correlated with invocation server-side.
- [ ] Docs explicitly distinguish client replay from invocation replay.

## Slice 6: Shadow Export Mirror

Goal: Preserve invocation snapshots in the Shadow/versioned snapshot system
without making Shadow the primary runtime audit path.

Files:
- `backend/app/services/shadow_exporters.py`
- `backend/app/services/shadow_service.py` if entity type allowlists exist
- `backend/app/services/shadow_summaries.py`
- `backend/app/services/shadow_context_loader.py` only if summaries should feed
  future prompts
- tests under `backend/app/tests/services/`

Steps:
1. Add `build_agent_invocation_snapshot(...)` to `shadow_exporters.py`.
2. Snapshot from the persisted `AgentInvocation` row, not live reconstruction.
3. Include:
   - invocation ids and room/agent ids
   - structured context snapshot
   - structured story runtime snapshot
   - prompt hash
   - redacted prompt by default
   - full prompt only if allowed by policy
   - response metadata
4. Enqueue a Shadow version after invocation completion.
5. Add a summary transformer in `shadow_summaries.py`, if summaries are useful.
6. Do not automatically feed prior invocation summaries into prompts until a
   separate product decision is made.

Checklist:
- [ ] Shadow snapshot uses persisted invocation, not current room state.
- [ ] Missing Shadow write does not fail agent execution.
- [ ] Shadow summary does not leak full prompt by default.

## Slice 7: Replay/Regression Tests

Goal: Prove that code changes do not destroy historical invocation observability.

Files:
- `backend/app/tests/services/test_agent_invocation_replayability.py` new
- `backend/app/tests/api/routes/test_agent_invocations.py` new
- `frontend` tests if this repo has established panel tests

Test scenarios:
1. Start room runtime, send a message, invoke agent, then mutate room runtime.
   - The stored invocation still shows the old story node/state.
2. Change/pin prompt config after invocation.
   - The stored invocation still shows old prompt provenance/hash.
3. Replay room events after invocation.
   - Visible response returns, but prompt does not appear in event replay.
4. Fetch invocation detail.
   - Exact stored `story_runtime_json` and redacted prompt are available.
5. A2A tool invocation.
   - Tool call input is audited even without room message event.

Checklist:
- [ ] Backend tests pass.
- [ ] Existing room messaging tests pass.
- [ ] Existing agent runner tests pass.

## Implementation Order

1. Serialization helpers.
2. Model/table and audit persistence service.
3. Streaming runner instrumentation.
4. A2A tool instrumentation.
5. Debug read API.
6. Frontend DebugPanel integration.
7. Event linkage docs.
8. Shadow exporter mirror.
9. Replay/regression test suite.

## Non-Goals For First Pass

- Do not attempt deterministic LLM response replay.
- Do not broadcast full prompts over websocket.
- Do not put full prompt data into `RoomEvent.payload`.
- Do not make Shadow the only place invocation inputs are stored.
- Do not auto-trigger agents from runtime transitions as part of this plan.

## Definition Of Done

- An operator can inspect a completed agent invocation and see the exact stored
  prompt/context snapshot used at run time.
- The DebugPanel clearly distinguishes frontend message approximation from
  backend exact invocation snapshot.
- Room event replay remains safe and backwards compatible.
- Invocation snapshots survive later changes to prompt construction, story
  runtime state, room context, and prompt config bindings.
- Shadow can mirror invocation snapshots without being required for immediate
  debugging.
