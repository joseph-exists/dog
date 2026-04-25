# Agent / Story / Room Coupling And Redundancy Analysis

Status: `current-code analysis`
Reviewed: `2026-04-25`
Reviewer: `Codex`

## Scope

This analysis describes the current control flow and call hierarchy for the
agent-story-room interconnection, then identifies where the primary interfaces
are tightly coupled and where runtime-shaped redundancy is useful or
unnecessary.

## Current Call Hierarchy

### Shared Story Runtime Read And Write

Frontend:
1. `StoryPanel` calls `useRoomRuntime(roomId)`.
2. `useRoomRuntime` reads and mutates through `RoomRuntimeService`.
3. `RoomRuntimeService` calls generated client endpoints for
   `/rooms/{room_id}/runtime`, `/advance`, `/rewind`, and `/reset`.

Backend:
1. `room_runtime.py` routes call CRUD runtime functions.
2. `start_room_runtime` creates a new `UserStoryProgress` and points
   `RoomStoryProgress.active_progress_id` to it.
3. `advance_room_runtime` mutates the active `UserStoryProgress`, increments
   `RoomStoryProgress.revision`, and emits a runtime event.
4. `rewind_room_runtime` creates a new progress branch, clones the ancestor
   choice chain, and repoints `RoomStoryProgress.active_progress_id`.
5. `reset_room_runtime` creates a fresh start branch through
   `start_room_runtime`.
6. `_build_room_runtime_public` projects canonical state into
   `RoomRuntimePublic`.

Evidence:
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts:83`
- `/home/josep/dog/frontend/src/services/roomRuntimeService.ts:138`
- `/home/josep/dog/backend/app/api/routes/room_runtime.py:27`
- `/home/josep/dog/backend/app/crud.py:2503`
- `/home/josep/dog/backend/app/crud.py:2614`
- `/home/josep/dog/backend/app/crud.py:2755`
- `/home/josep/dog/backend/app/crud.py:2896`
- `/home/josep/dog/backend/app/crud.py:3058`

### User Message To Story-Aware Agent Reply

REST path:
1. `POST /rooms/{room_id}/messages`
2. `send_user_message`
3. `run_agents_for_message`
4. agent selection service chooses coordinators and regular agents
5. `run_agent_for_room_streaming`
6. `StreamingAgentRunner.run`
7. `RoomContextService.build`
8. `build_room_context`
9. room story runtime is loaded from `RoomStoryProgress.active_progress_id`
10. `build_agent_prompt`
11. agent model stream emits room messages
12. A2A mention processing may invoke further agents

WebSocket path:
1. client sends `message.send`
2. websocket route emits `room_message.user`
3. same `run_agents_for_message` path as REST

Evidence:
- `/home/josep/dog/backend/app/api/routes/rooms.py:506`
- `/home/josep/dog/backend/app/api/routes/websocket.py:455`
- `/home/josep/dog/backend/app/services/agent_runner.py:346`
- `/home/josep/dog/backend/app/services/agent_runner_streaming.py:84`
- `/home/josep/dog/backend/app/services/agent_context.py:15`
- `/home/josep/dog/backend/app/services/context_provider.py:186`
- `/home/josep/dog/backend/app/services/agent_prompt.py:36`

### Runtime Event To Frontend Refresh

1. Runtime CRUD emits `room.runtime.*`.
2. WebSocket stream receives the event.
3. `useRoomStream` invalidates `["rooms", roomId, "runtime"]`.
4. `useRoomRuntime` refetches the runtime projection.

Evidence:
- `/home/josep/dog/backend/app/crud.py:2735`
- `/home/josep/dog/backend/app/crud.py:2877`
- `/home/josep/dog/backend/app/crud.py:3039`
- `/home/josep/dog/backend/app/crud.py:3107`
- `/home/josep/dog/frontend/src/hooks/useRoomStream.ts:59`
- `/home/josep/dog/frontend/src/hooks/useRoomStream.ts:264`

## Coupling Assessment

### Room To Story Runtime: Tight, Intentional

The room runtime is tightly coupled to the story progress model:
- `RoomStoryProgress` requires `story_id`, `story_version`, and an
  `active_progress_id`.
- runtime start depends on the room's attached `story_id`.
- runtime writes depend on story nodes, choices, state schema defaults, and
  choice condition evaluation.

This coupling is appropriate because room runtime is the shared execution of an
authored story state machine. The risk is not the coupling itself; it is that
the room runtime reuses `UserStoryProgress`, so a room-level run is represented
through a user/persona-named persistence primitive.

Coupling level: `high but coherent`.

### Agents To Room: Tight, Intentional

Agents are room-resident runtime actors:
- they are selected from room participants;
- their prompt context is room-scoped;
- their output is emitted back into room messages;
- A2A behavior is constrained by agents present in the same room.

This is strong coupling, but it matches the product model. Agents are not
generic story players; they are participants in a room.

Coupling level: `high and product-defining`.

### Agents To Story Runtime: Loose Read Coupling

Agents depend on story runtime only through `RoomContext.story_runtime`, a
text-oriented projection. They do not depend on `RoomRuntimePublic`, generated
frontend models, or direct runtime mutation routes.

This is a good boundary for read-only story awareness:
- the agent runner does not need to know room runtime CRUD details;
- the prompt builder can format the runtime for LLM consumption;
- missing runtime does not prevent basic room-agent behavior.

The downside is duplicated projection logic: `_build_room_runtime_public` and
`build_room_context` both reconstruct current node, node chain, choices, and
state from the same underlying records.

Coupling level: `medium, currently read-only`.

### Frontend StoryPanel To Runtime API: Medium-Tight

`StoryPanel` is coupled to `RoomRuntimeViewModel`, not raw backend models. That
keeps the component cleaner, but the hook/service pair still understands
runtime operations directly: start, advance, rewind, reset, expected revision,
and runtime absence.

Coupling level: `medium-tight and acceptable`.

### Story Local Player To Room Runtime: Intentionally Decoupled

The local StoryPlayer/Preview runtime and room `storyRuntime` are separate
execution contexts. This is not accidental duplication:
- local preview/player supports author-side or solo simulation;
- room runtime is shared, revisioned, evented, and permissioned.

The risk is user/operator confusion when both are mounted in a room-like demo or
page. Documentation already calls this out and should keep doing so.

Coupling level: `low by design`.

## Redundancy Map

### Useful Redundancy

`RoomRuntimePublic` versus `StoryRuntimeContext`:
- `RoomRuntimePublic` is a UI/API projection with model objects, IDs,
  revisions, and choices.
- `StoryRuntimeContext` is a model-prompt projection with titles, content,
  choice text, path, and state.

This split is useful because UI and LLM prompt consumers need different
shapes. The issue is not that two projections exist; the issue is that both
reconstruct the same runtime facts independently.

Local `StoryPlayer` versus shared `storyRuntime`:
- useful separation because local preview should not mutate room state;
- important to keep the local-only label prominent.

### Risky Or Unnecessary Redundancy

Duplicate runtime reconstruction:
- `_build_room_runtime_public` reconstructs current node, available choices,
  and node chain for the UI.
- `build_room_context` reconstructs current node, available choices, node
  chain, and story state again for agents.

This is the main unnecessary redundancy. It creates drift risk if path
reconstruction, choice filtering, or state formatting changes in one path but
not the other.

Room reset event duplication:
- `reset_room_runtime` calls `start_room_runtime`, which emits
  `room.runtime.started`, then `reset_room_runtime` emits `room.runtime.reset`.

This may be intentional if consumers distinguish "new branch started" from
"user requested reset." It is still a coupling footgun because consumers may
double-refresh or interpret reset as two transitions.

Generated client service plus hand-written frontend service:
- generated `RoomRuntimeService` is wrapped by
  `frontend/src/services/roomRuntimeService.ts`.
- this is acceptable as an adapter layer, but it should remain a pure
  transformation layer rather than accumulating runtime policy.

## Primary Interface Tightness

| Interface | Coupling | Assessment |
| --- | --- | --- |
| Room runtime routes to CRUD runtime functions | `tight` | Good service boundary, thin routes. |
| CRUD runtime to story data model | `very tight` | Necessary for state-machine execution. |
| Room runtime to `UserStoryProgress` | `tight/risky naming` | Works, but "user progress" is doing room-run duty. |
| Agent runner to room context | `tight` | Expected; agents are room actors. |
| Agent prompt to story runtime context | `medium` | Good projection boundary. |
| Agent runner to runtime mutation API | `none found` | Agents are readers only today. |
| Runtime event stream to frontend runtime cache | `medium` | Good invalidation contract. |
| Runtime event stream to agent execution | `none found` | No auto-trigger on runtime transition. |
| Local StoryPlayer to room runtime | `low` | Intentional separation. |

## Recommendations

1. Create one backend runtime projection builder that can produce both:
   `RoomRuntimePublic` for UI and `StoryRuntimeContext` for agent prompts.
   Keep consumer-specific formatting separate, but share the data-loading and
   chain/choice reconstruction.

2. Name the room-level runtime primitive more explicitly at the service layer.
   The database can continue using `UserStoryProgress`, but code should expose
   a `RoomRuntimeState` or `SharedStoryRun` service concept so callers do not
   have to reason about room state through a user-progress label.

3. Decide whether reset should emit both `room.runtime.started` and
   `room.runtime.reset`. If both remain, document the semantic difference and
   make frontend consumers idempotent.

4. Keep agent story-runtime coupling read-only unless product intent changes.
   If agents should mutate runtime, add a dedicated tool/contract that uses the
   same revision and permission checks as the existing room runtime routes.

5. Add an operator-facing "agent prompt/context payload" inspector. This would
   close the biggest debugging gap without changing runtime authority.

## Bottom Line

The current architecture has a sane center of gravity: the room owns shared
runtime, story owns authored graph logic, and agents receive room runtime as
context at execution time. The strongest redundancy is duplicated runtime
projection work between UI runtime reads and agent prompt context. The strongest
missing coupling, if desired by product, is an explicit agent-to-runtime
mutation or runtime-event-to-agent-trigger contract.
