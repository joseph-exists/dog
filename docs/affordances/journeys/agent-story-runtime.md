# Agent -> Story Runtime

Status: `partial, evidence-backed`
Primary persona: `operator / story author / orchestrator designer`
Priority: `P0`

Primary routes:
- `/r/$roomId`

Primary files:
- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/Dialogs/AddParticipantDialog.tsx`
- `/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
- `/home/josep/dog/frontend/src/services/roomRuntimeService.ts`
- `/home/josep/dog/frontend/src/services/roomService.ts`
- `/home/josep/dog/backend/app/services/context_provider.py`
- `/home/josep/dog/backend/app/services/agent_prompt.py`
- `/home/josep/dog/backend/app/services/agent_runner.py`
- `/home/josep/dog/backend/app/api/routes/rooms.py`

Related backend/runtime references:
- `run_agents_for_message`
- `build_room_context`
- room runtime APIs
- room participant APIs

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

This journey documents the overlap between:
- shared room `storyRuntime`
- room-resident agents
- user-visible agent responses in chat/debug surfaces

The central claim is satisfiable:
- agents in a story-backed room can be given live story runtime context
- that context includes current node, node content, path taken, available choices, and story state
- user messages can trigger those agents
- users can observe resulting agent responses in the room

The stronger claim is not yet satisfiable from the current code evidence:
- I did not find proof that agents directly advance, rewind, reset, or otherwise mutate shared `storyRuntime`
- I did not find proof that runtime transitions alone automatically trigger agents without a user message, mention, or UI action

## Evidence Table

| Claim | Status | Evidence |
| --- | --- | --- |
| A room runtime exposes current node, choices, node chain, and story state | `satisfiable` | [roomRuntimeService.ts](/home/josep/dog/frontend/src/services/roomRuntimeService.ts):44, [roomRuntimeService.ts](/home/josep/dog/frontend/src/services/roomRuntimeService.ts):100 |
| Room UI exposes shared story runtime to users | `satisfiable` | [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):143, [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):151, [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):161, [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):165 |
| Agents can be added as room participants | `satisfiable` | [AddParticipantDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/AddParticipantDialog.tsx):55, [AddParticipantDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/AddParticipantDialog.tsx):106, [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts):936 |
| Rooms can simultaneously expose `storyRuntime`, `participantPanel`, `debug`, and `a2ui` | `satisfiable` | [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx):77, [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx):80, [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx):85, [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx):86, [roomPanelService.ts](/home/josep/dog/frontend/src/components/Room/services/roomPanelService.ts):169 |
| User messages trigger active agents in the room | `satisfiable` | [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts):579, [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):365, [test_rooms_with_agents.py](/home/josep/dog/backend/app/tests/api/routes/test_rooms_with_agents.py):13 |
| Agent room context includes story runtime | `satisfiable` | [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):64, [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):93, [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):183, [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):257 |
| Agent prompt text explicitly includes current node, content, path, choices, and story state | `satisfiable` | [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):36, [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):45, [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):54, [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):58, [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):64 |
| Coordinator agents run before regular agents | `satisfiable` | [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):349, [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):355, [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):395 |
| Users can see agent responses in the room | `satisfiable` | [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):237, [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):507 |
| Users can inspect what messages are visible to agents | `satisfiable, limited` | [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):111, [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):122, [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):477 |
| Users can inspect story runtime state in UI | `satisfiable` | [StoryStateCollapsible.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryStateCollapsible.tsx):16, [StoryStateCollapsible.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryStateCollapsible.tsx):38 |
| Agents directly mutate shared story runtime | `not satisfiable from current evidence` | runtime mutations found only in room runtime APIs and `useRoomRuntime`; no agent-side mutation path found in inspected files: [useRoomRuntime.ts](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts):106, [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py):45 |
| Story runtime changes automatically trigger agents | `not satisfiable from current evidence` | runtime events invalidate frontend caches, but no `run_agents_for_message` path is tied to runtime event handlers in inspected code: [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):59, [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):264, [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):379 |
| Frontend shows the exact story-runtime payload sent to agents | `not satisfiable from current evidence` | debug panel previews message context only; story runtime injection happens in backend prompt builder, not visibly serialized in current room UI: [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):122, [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):36 |

## Interpreted Journey

What is verifiably implemented today:

1. A room can host shared `storyRuntime`.
2. The same room can host agents as participants.
3. When a user sends a message, active agents in that room are triggered.
4. Backend agent context building includes room story runtime.
5. Agent prompts explicitly include the current story step and available choices.
6. Coordinator agents run before regular agents.
7. Users can inspect runtime state and compare it to agent responses in room UI.

What that means in practice:
- an orchestrator can read the first step of a workflow if the room has active story runtime
- specialist agents can also receive that same runtime framing
- the user can watch different agent responses to the same story step in chat/debug surfaces

## Core Use Cases

## Use Case: Add Agents To A Story-Backed Room

Status: `satisfiable`
Primary persona: `room owner`
Priority: `P0`

### User Goal

Create a room state where both shared story runtime and agents are present.

### Preconditions

- room has a `story_id`
- room exposes `storyRuntime` and participant-management surfaces

### Evidence

- story runtime panel: [StoryPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx):30
- add-agent dialog: [AddParticipantDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/AddParticipantDialog.tsx):55
- room participant add API: [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts):936

### Outcome

- room contains both shared runtime and active agent participants

## Use Case: Trigger Story-Aware Agent Responses

Status: `satisfiable`
Primary persona: `operator`
Priority: `P0`

### User Goal

Send a message in a story-backed room and receive agent replies informed by the
current story step.

### Preconditions

- room has active story runtime
- at least one active agent is present

### Evidence

- user message triggers agents: [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):365
- story runtime loaded into agent context: [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):183
- prompt includes current node and choices: [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):42

### Outcome

- agent response can reference the current node, path, choices, or story state

## Use Case: Observe Coordinator And Specialist Responses To The Same Story Step

Status: `satisfiable`
Primary persona: `orchestrator designer`
Priority: `P1`

### User Goal

See how a coordinator and other agents respond differently to the same current
story step.

### Preconditions

- coordinator agent is present
- one or more regular agents are also present
- room has active story runtime

### Evidence

- coordinators run first: [agent_runner.py](/home/josep/dog/backend/app/services/agent_runner.py):355
- prompt includes other agents in room: [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):75
- agent messages appear in room stream: [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):237

### Caveat

This is satisfiable as “observe multiple responses to the same story step.”
It is not yet proven as “observe explicit orchestrator-controlled runtime
routing” unless the specific room configuration and agent prompt setup already
implements that behavior.

## Missing Or Hidden Pieces

These are the most important gaps surfaced by this audit.

### 1. No visible frontend inspector for full agent story-runtime payload

Evidence:
- debug panel shows message context payload approximation, not the story-runtime
  prompt segment: [RoomDebugPanel.tsx](/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx):122
- story-runtime injection exists only in backend context/prompt assembly:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py):183,
  [agent_prompt.py](/home/josep/dog/backend/app/services/agent_prompt.py):36

Interpretation:
- this may be wired in backend but hidden in frontend

### 2. No verified direct agent -> shared runtime mutation path

Evidence:
- runtime mutation path found in room runtime APIs and user-facing hook:
  [useRoomRuntime.ts](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts):106
- no inspected agent service or route invoked runtime advance/rewind/reset

Interpretation:
- this may be missing rather than hidden

### 3. No verified auto-trigger on runtime transition alone

Evidence:
- user messages trigger agents: [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py):379
- runtime events only invalidate UI state in frontend:
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts):264

Interpretation:
- if desired behavior is “agents react when workflow advances,” an additional
  backend contract or event-consumer path may still be needed
