# Agent / Story / Room Gap Validation

Status: `current-code analysis`
Reviewed: `2026-04-25`
Reviewer: `Codex`

## Scope

This analysis validates or refutes the three gaps identified in
`agent-story-runtime.md` against the current control flow for room agents,
shared story runtime, and room-visible runtime surfaces.

The relevant surfaces are:
- `Room`: collaborative container, message trigger surface, participant roster,
  debug UI, shared runtime panel.
- `Story`: authored graph/state machine, local preview/player runtime, room
  handoff source.
- `Agents`: room participants that receive room context at execution time.

## Runtime Ground Truth

The backend has one authoritative shared room-runtime pointer:
- `RoomStoryProgress` is the room-scoped pointer to the active run.
- `UserStoryProgress` is the underlying state machine instance that stores
  current node, story state, head choice, and head version.
- `UserNodeChoice` is the event/history chain used to reconstruct path and
  state.

Evidence:
- `RoomStoryProgressBase` explicitly stores `story_id`, `story_version`,
  `active_progress_id`, and `revision`, while documenting that the underlying
  state lives in `UserStoryProgress`, `UserNodeChoice`, and snapshots:
  `/home/josep/dog/backend/app/models.py:4166`.
- `UserStoryProgress` stores `current_node_id`, `story_state`,
  `head_choice_id`, and `head_version`:
  `/home/josep/dog/backend/app/models.py:1004`.
- The UI-facing `RoomRuntimePublic` is a projection with `current_node`,
  `node_chain`, and `available_choices`:
  `/home/josep/dog/backend/app/models.py:4205`.

## Gap 1: No Visible Frontend Inspector For Full Agent Story-Runtime Payload

Verdict: `validated, with qualification`

The backend does build and inject story runtime into the agent prompt, but the
current frontend does not expose the exact serialized prompt/runtime segment
that the model receives.

Evidence that the payload exists:
- `build_room_context` loads `RoomStoryProgress`, then
  `UserStoryProgress.active_progress_id`, then current node, available choices,
  path, and `story_state`: `/home/josep/dog/backend/app/services/context_provider.py:186`.
- `StoryRuntimeContext` is deliberately a text-oriented agent prompt projection,
  not the full UI model: `/home/josep/dog/backend/app/services/context_provider.py:67`.
- `build_agent_prompt` serializes current node, content, node type, path,
  choices, and story state into the prompt:
  `/home/josep/dog/backend/app/services/agent_prompt.py:36`.

Evidence that the UI has no exact inspector:
- The room stream invalidates messages and runtime caches but does not receive
  or display the constructed prompt: `/home/josep/dog/frontend/src/hooks/useRoomStream.ts:247`.
- Runtime UI uses `RoomRuntimeViewModel`, a transformed API projection, not the
  prompt payload sent to agents:
  `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts:83`.

Qualification:
- This is an observability gap, not a functional gap. Agents can receive the
  story runtime today, but operators cannot compare the exact model-facing
  prompt segment to the visible runtime state from the current frontend.

## Gap 2: No Verified Direct Agent-To-Shared-Runtime Mutation Path

Verdict: `validated`

Current code shows shared runtime mutations only through room runtime routes
and frontend runtime controls. Agent execution reads runtime through context,
but no inspected agent path calls `advance_room_runtime`, `rewind_room_runtime`,
`reset_room_runtime`, or `start_room_runtime`.

Evidence for the writer path:
- Runtime routes expose read, start, advance, rewind, and reset:
  `/home/josep/dog/backend/app/api/routes/room_runtime.py:27`.
- `advance_room_runtime` validates the selected choice, updates
  `UserStoryProgress`, increments `RoomStoryProgress.revision`, and emits
  `room.runtime.advanced`: `/home/josep/dog/backend/app/crud.py:2755`.
- `rewind_room_runtime` creates a new progress branch and repoints
  `RoomStoryProgress.active_progress_id`: `/home/josep/dog/backend/app/crud.py:2896`.
- `reset_room_runtime` delegates to `start_room_runtime` to create a new start
  branch: `/home/josep/dog/backend/app/crud.py:3058`.
- The frontend `useRoomRuntime` hook is the visible caller for start, advance,
  rewind, and reset: `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts:106`.

Evidence for the agent read-only path:
- Agent execution calls context building, then prompt building, then model
  streaming: `/home/josep/dog/backend/app/services/agent_runner_streaming.py:84`.
- The prompt includes the runtime as text, but the runner does not call room
  runtime mutation functions:
  `/home/josep/dog/backend/app/services/agent_prompt.py:40`.

Qualification:
- Agents can indirectly influence runtime if they tell a human which choice to
  take, or if a future tool is wired to the runtime API. The current code does
  not show that direct tool/action path.

## Gap 3: No Verified Auto-Trigger On Runtime Transition Alone

Verdict: `validated`

Runtime transitions emit room runtime events and refresh frontend runtime state,
but they do not trigger `run_agents_for_message`.

Evidence for agent triggers:
- REST message send persists the user message and then calls
  `run_agents_for_message`: `/home/josep/dog/backend/app/api/routes/rooms.py:506`.
- WebSocket message handling does the same for `message.send`:
  `/home/josep/dog/backend/app/api/routes/websocket.py:455`.
- `run_agents_for_message` selects coordinators and regular agents based on a
  `trigger_message`: `/home/josep/dog/backend/app/services/agent_runner.py:346`.

Evidence for runtime transition behavior:
- Runtime mutations emit `room.runtime.started`, `room.runtime.advanced`,
  `room.runtime.rewound`, and `room.runtime.reset`:
  `/home/josep/dog/backend/app/crud.py:2735`,
  `/home/josep/dog/backend/app/crud.py:2877`,
  `/home/josep/dog/backend/app/crud.py:3039`,
  `/home/josep/dog/backend/app/crud.py:3107`.
- Frontend stream handling treats runtime events as cache invalidation only:
  `/home/josep/dog/frontend/src/hooks/useRoomStream.ts:59`,
  `/home/josep/dog/frontend/src/hooks/useRoomStream.ts:264`.

Qualification:
- This is not necessarily a defect. It preserves a clean separation between
  "runtime state changed" and "agent conversation triggered." If product intent
  is that agents should react to workflow movement without a user message, that
  needs a new explicit contract, for example a runtime-event trigger pipeline
  with a synthetic trigger message or a distinct agent event type.

## Consolidated Verdict

All three gaps are validated against current code, with different severity:

| Gap | Verdict | Severity | Why |
| --- | --- | --- | --- |
| Full frontend inspector for agent story-runtime payload | `validated` | `medium` | Functional path works, but debugging fidelity is incomplete. |
| Direct agent-to-runtime mutation path | `validated` | `high if desired behavior` | Agents are story-aware readers, not runtime writers. |
| Runtime-transition auto-trigger | `validated` | `high if desired behavior` | Runtime events refresh UI only; agents run on messages/manual paths. |

## Recommendation

If the intended model is "agents observe and advise while humans operate the
shared story runtime," no runtime mutation work is required. The main missing
piece is an exact prompt/context inspector.

If the intended model is "agents participate in operating the story state
machine," the next design step should not be another frontend control. It should
be a backend contract that answers:
- Which agents are allowed to mutate room runtime?
- Is mutation done through a tool call, AG-UI action, or orchestration event?
- Should runtime transitions trigger all agents, coordinators only, or agents
  subscribed to a specific runtime event type?
- How are optimistic revisions, permissions, and audit messages represented in
  the room stream?
