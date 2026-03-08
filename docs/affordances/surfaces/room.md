# Room

Status: `partial but substantial`
Primary routes:
- `/rooms`
- `/r/$roomId`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/rooms.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- `/home/josep/dog/frontend/src/hooks/useRoomPanels.ts`
- `/home/josep/dog/frontend/src/hooks/useRoomRepoContext.ts`
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
- `/home/josep/dog/frontend/src/services/roomService.ts`
- `/home/josep/dog/frontend/src/components/Room/Dialogs/RoomPromptSettingsDialog.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/ParticipantPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/RoomDebugPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/A2UIPanel.tsx`

Related backend/services:
- `RoomsService`
- `RoomRuntimeService`
- room participant APIs
- room context item APIs
- room agent settings APIs
- room stream / event orchestration

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

`Room` is the primary collaborative runtime surface in the product. It is not
just a chat shell. It combines:

- live messaging and streaming agent responses
- shared story runtime
- participant and agent management
- room-scoped context curation
- room-scoped prompt binding controls
- AG-UI action surfaces
- repo-aware co-working panels
- per-room and per-user panel layout resolution

Primary user intents:
- enter a live collaboration room
- talk with users and agents around shared context
- run and inspect shared story runtime
- curate what agents can see
- tune prompt bindings for the room and for specific agents
- customize the room panel assemblage

Key integrations:
- `Agents`
- `Story`
- `Repos`
- `Demo`
- room context and agent settings backend contracts

## Surface Model

| Surface | Role | Status | Notes |
| --- | --- | --- | --- |
| Room List | discovery and entry | `verified-ish` | browse and open accessible rooms |
| Unified Room Route | primary runtime shell | `verified` | route resolves room, messages, participants, panels |
| Chat Panel | message and trigger surface | `verified` | user messages, AG-UI actions, context toggles |
| Story Runtime Panel | shared authored workflow runtime | `verified-ish` | shared node, choices, state, rewind/reset |
| Participant Panel | user/agent roster and management | `verified-ish` | add, remove, activate, deactivate |
| Debug Panel | agent/context inspection | `verified-ish` | active agents, visible messages, repo context files |
| A2UI Panel | grouped agent UI component surface | `verified-ish` | action buttons re-invoke originating agent |
| Prompt Settings Dialog | room/agent prompt binding control | `verified-ish` | prompt config attach/pin/clear, inline overlay inspection |
| Repo Panels | context-fed co-working surfaces | `partial` | explorer/viewer + shared repo events + room context attach |

## What Room Means After The New Context Audit

The updated backend review changes how Room should be documented.

Room is now verifiably a place where:
- shared `storyRuntime` can exist as authoritative room state
- active agents in that same room can be triggered by user messages
- backend agent context includes story runtime, active-for-context messages, and extra room contexts
- room owners can attach or remove supplemental room context items
- room owners can bind room-level and per-agent prompt configs

That makes Room the product surface where `Story`, `Agents`, and `Context`
actually converge in operation.

## Verifiable Runtime Object Model

Room frontend visibly manages and consumes:
- room metadata
- room messages, including `active_for_context`
- participants, including both users and agents
- room panel config resolution
- shared `storyRuntime`
- room context items
- room agent settings

Evidence in current code:
- room aggregation hook loads room, participants, messages, and participant mutations:
  `/home/josep/dog/frontend/src/hooks/useRoom.ts`
- room runtime hook exposes start/advance/rewind/reset:
  `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
- room service exposes room context item CRUD and AG-UI action calls:
  `/home/josep/dog/frontend/src/services/roomService.ts`

## Core Affordance Areas

### 1. Chat As The Primary Trigger Surface

Verified affordances:
- send room messages
- stream agent responses over room websocket
- edit, pin, unpin, delete, and context-toggle messages
- dispatch AG-UI actions back to the originating agent
- add multiple agents from chat-side controls

Meaning:
- chat is not only conversation UI
- it is the main trigger path for agent execution and context shaping

### 2. Shared Story Runtime Inside The Room

Verified affordances:
- start shared runtime
- inspect current node
- inspect available choices
- inspect path taken
- inspect current story state
- advance, rewind, and reset shared runtime

Meaning:
- room can host authoritative shared workflow state
- room participants can reason about the same current story step

### 3. Participant And Agent Management

Verified affordances:
- add agents to the room
- remove agents from the room
- activate/deactivate agents already present
- remove non-owner human participants
- inspect coordinator and participation mode badges

Meaning:
- room is the runtime assembly point for multi-agent collaboration, not merely a place agents happen to talk

### 4. Agent-Visible Context Curation

Verified affordances:
- toggle whether individual messages are active for context
- inspect which messages are visible to agents in debug
- attach repo files as room context items
- remove repo file context items
- observe room-context query invalidation when room context events arrive

Important distinction:
- frontend clearly supports room context item management for repo-file style payloads
- frontend does not yet expose a general-purpose room-context authoring UI for arbitrary note/upload/system items

Meaning:
- room already has a real context-governance layer
- the current UI is narrow, but the backend contract is broader than the current surface

### 5. Prompt Binding And Agent Policy

Verified affordances:
- open prompt settings from room shell when user is owner
- inspect room-default prompt binding
- inspect per-agent overrides
- attach a `PromptConfig`
- choose latest vs pinned version policy
- clear room-default or per-agent override
- inspect inline overlay payload if present

What is not visibly surfaced:
- direct tool-policy editing for the room or per-agent override

Meaning:
- room already has a prompt-governance surface
- tool-governance appears present in backend models but underexposed in current frontend

### 6. AG-UI / A2UI

Verified affordances:
- agent-emitted UI components are grouped by agent in `A2UI`
- action buttons send `sendUIAction`
- backend re-invokes the originating agent rather than broadcasting to all agents

Meaning:
- room supports structured agent interaction beyond plain text chat

### 7. Debug And Inspection

Verified affordances:
- show internal agent-to-agent messages
- inspect approximate API payload for agent message context
- inspect active agents in the room
- inspect recent messages
- inspect context-visible message subset
- inspect repo files currently attached as room context

Current limit:
- debug does not show the exact backend prompt serialization for story runtime plus extra contexts

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Browse rooms you can access | `verified-ish` | room list page exists |
| Create a room | `partial` | dialog exists on room list and story flows |
| Open room runtime | `verified` | unified room route exists |
| Chat in a room | `verified` | primary interaction surface |
| Add/remove participants | `verified-ish` | hooks and panels exist |
| Add and manage agents in a room | `verified-ish` | quick-add, toggles, removals, party-picker paths exist |
| Start and operate shared story runtime | `verified-ish` | start, advance, rewind, reset are implemented |
| Compare shared story runtime with agent replies | `verified-ish` | room is the main comparison surface |
| Toggle messages into or out of agent context | `verified` | `active_for_context` controls are visible |
| Inspect what messages agents can currently see | `verified-ish` | debug panel exposes context subset |
| Attach repo files as room context | `verified-ish` | owner-only repo context flow exists |
| Remove repo files from room context | `verified-ish` | debug and repo context flow support removal |
| Use AG-UI / A2UI actions | `verified-ish` | action buttons re-invoke originating agent |
| Bind room-default prompt config | `verified-ish` | owner settings dialog exists |
| Bind per-agent prompt config override | `verified-ish` | owner settings dialog exists |
| Edit room tool policy directly | `not surfaced in current frontend` | backend model suggests capability, UI not visible |
| Trigger agents automatically on story runtime transition | `not verified` | current verified trigger is user message path |
| Let agents directly advance shared story runtime | `not verified` | no agent-side mutation path found |

## Room-Specific Use Cases Added By The New Story/Agent Understanding

### Use Case: Observe Story-Aware Agent Replies In Shared Runtime

Status: `verified-ish`

User goal:
- keep shared story runtime visible while sending a message that causes agents
  to react to the current node and choices

Why it matters:
- this is the primary currently-supported `Room + Story + Agents` convergence path

### Use Case: Curate Agent Context Before Triggering A Reply

Status: `verified-ish`

User goal:
- choose which prior messages remain active for context, then send a new message
  and observe how the agent reply changes

Why it matters:
- this gives users operational control over the prompt context without exposing the raw backend prompt directly

### Use Case: Add Repo File Context To Support Story/Agent Work

Status: `partial but real`

User goal:
- attach a repo file to room context so agents can reason over it alongside
  room messages and story runtime

Why it matters:
- this is the clearest current bridge from room collaboration into richer multi-source agent context

### Use Case: Apply Room-Wide Or Per-Agent Prompt Binding

Status: `verified-ish`

User goal:
- adjust prompt behavior at room scope or for a specific agent while keeping the
  same room runtime and participants

Why it matters:
- this is the current visible control point for agent policy in rooms

## Bridge Opportunities

These are small bridges that could unlock broader feature sets without a full redesign.

### 1. Show Story Runtime In Debug Prompt Preview

Current state:
- debug shows active-for-context messages
- backend prompt also includes story runtime and extra contexts

Bridge:
- add a debug subsection that renders the exact `story_runtime` and `extra_contexts`
  payload segment passed to agents

Result:
- makes hidden backend wiring visible
- reduces ambiguity in story-aware agent walkthroughs

### 2. Add General Room Context Composer

Current state:
- backend supports general room context items
- frontend mainly exposes repo-file attachment as the room-context UX

Bridge:
- add a lightweight room-context editor for `note.*`, `upload.*`, or `system.*`
  items in debug or settings

Result:
- unlocks richer human-curated context without changing core backend contracts

### 3. Expose Tool Policy Alongside Prompt Binding

Current state:
- room agent settings models include tool policy
- prompt settings dialog currently surfaces prompt config controls only

Bridge:
- add a read-only tool-policy inspector first, then editable controls

Result:
- closes the gap between backend capability and visible room governance

### 4. Runtime-Triggered Agent Mode

Current state:
- verified trigger path is user message -> agent run
- no verified runtime-transition trigger

Bridge:
- add an optional room policy that emits an agent invocation when runtime
  starts/advances/rewinds/resets

Result:
- would satisfy the broader workflow-orchestrator use case without changing room’s existing conceptual model

### 5. Agent-Proposed Runtime Choice Flow

Current state:
- agents can comment on current runtime
- agents do not visibly mutate runtime

Bridge:
- first add agent recommendation UI for next choice
- later add owner-approved runtime-advance actions if desired

Result:
- creates a safe path from advisory agents to agent-assisted workflow progression

## Walkthrough Candidates

- Open a story-backed room, add agents, and compare their replies to the shared story step
- Toggle messages into and out of agent context, then compare agent replies
- Attach repo file context and inspect it in debug while agents respond
- Bind a room-default prompt config and then override one agent
- Use AG-UI actions from an agent message and observe the follow-up reply

## Open Questions And Gaps

- room walkthroughs should branch cleanly between owner/member/viewer experiences
- current frontend does not expose a general-purpose room-context editor even though the backend contract exists
- current frontend does not expose tool-policy editing even though room agent settings models suggest broader governance support
- debug still hides the exact story-runtime and extra-context payload that agents receive
- broader workflow cases such as auto-triggered orchestrators or agent-driven runtime mutations still need explicit backend contracts
