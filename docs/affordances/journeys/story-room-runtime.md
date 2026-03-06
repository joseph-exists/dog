# Story -> Room Runtime

Status: `partial`
Primary persona: `story author / room owner`
Priority: `P0`

Primary routes:
- `/story`
- `/stories/$storyId/edit`
- `/rooms`
- `/r/$roomId`

Primary files:
- `/home/josep/dog/frontend/src/components/Story/panels/StoryGridPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/Dialogs/AddRoom.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/SoloStoryPlayerPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/StoryEditorPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/StoryEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryPlayer/StoryPreview.tsx`

Related backend/runtime references:
- `RoomsService`
- `RoomRuntimeService`
- story publish/unpublish endpoints

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

This journey documents how an authored Story becomes shared runtime inside a
Room.

The key distinction is:
- `StoryEditor` authors the graph, state schema, and transitions
- `StoryPreview` and standalone `StoryPlayer` execute the story locally
- room `storyRuntime` executes a shared runtime projection for the room
- room `storyPlayer` is explicitly local-only and does not synchronize with the
  room runtime
- room `storyEditor` is a collaborative/editor-context view into the same story

This is the most important conceptual split to preserve in documentation:
the Story system is upstream authored logic, while Room is the collaborative
runtime container that may host several story-related panels with different
state semantics.

## Journey Summary

| Step | Surface | What happens |
| --- | --- | --- |
| 1 | Story Editor | author defines nodes, choices, and state schema |
| 2 | Story Preview / Story Player | story logic is tested locally |
| 3 | Story Library | published story exposes room-creation affordance |
| 4 | Add Room | room is created with `story_id` attached |
| 5 | Room `storyRuntime` | shared runtime is started and advanced with revisioned mutations |
| 6 | Room `storyEditor` / `storyPlayer` | optional adjacent panels provide authoring or local-only inspection paths |

## Surface Roles In This Journey

| Surface | Runtime semantics |
| --- | --- |
| Story Editor | authoring only; edits graph and state definitions |
| Story Preview | local simulation of authored logic |
| Story Player | standalone local runtime |
| Room `storyRuntime` | shared room-level runtime projection |
| Room `storyPlayer` | local-only panel, explicitly not synced to room runtime |
| Room `storyEditor` | embedded authoring panel for the attached story |

## What Is Frontend-Visible Today

| Capability | Status | Notes |
| --- | --- | --- |
| Create room from published story | `verified-ish` | library cards expose `AddRoom` for published stories |
| Attach story when creating room | `verified-ish` | room creation dialog supports `story_id` |
| Start shared room runtime | `partial` | room runtime panel supports start flow |
| Advance shared room runtime | `verified-ish` | choose next transition through room runtime |
| Rewind/reset shared room runtime | `verified-ish` | runtime controls exist |
| Inspect room story state | `verified-ish` | room runtime panel exposes state collapsible |
| Compare local-only player vs shared runtime | `verified-ish` | local-only notice exists on room `storyPlayer` panel |
| Edit attached story from room | `partial` | room `storyEditor` panel exists |

## Core Use Cases

## Use Case: Publish Story And Create A Room From It

Status: `verified-ish`
Primary persona: `story author`
Priority: `P0`

### User Goal

Take an authored story and instantiate a collaborative room around it.

### Entry Points

- `/story`
- published story cards

### Preconditions

- story exists
- story is published
- user can create rooms

### Primary Affordances

- `Room` button from published story card
- `AddRoom` dialog with `defaultStoryId`

### Main Success Path

1. Publish a story from the editor.
2. Return to the story library.
3. Use the `Room` affordance on the published story card.
4. Create the room with that story attached.
5. Land in `/r/$roomId`.

### Outcomes

- room is created with `story_id` attached
- room can host story-related panels against the attached story

## Use Case: Start Shared Story Runtime In A Room

Status: `partial`
Primary persona: `room owner`
Priority: `P0`

### User Goal

Initialize the room’s shared runtime projection for the attached story.

### Preconditions

- room has a `story_id`
- room panel set includes `storyRuntime`
- user has permission to write runtime changes

### Primary Affordances

- `StoryPanel` start action
- `StoryRuntimeStartDialog`

### Main Success Path

1. Open a room with an attached story.
2. Open the `Story Runtime` panel.
3. If no runtime exists yet, start runtime through the dialog.
4. Confirm runtime projection is created and current node appears.

### Outcomes

- room runtime now has a shared revisioned state
- the room can advance, rewind, and reset the story at room scope

### Caveat

The current runtime write path is owner-gated in the frontend and backend
handling. Non-owners may be able to observe but not mutate.

## Use Case: Advance Shared Runtime Through Choices

Status: `verified-ish`
Primary persona: `room owner`
Priority: `P0`

### User Goal

Progress the attached story for all room viewers through the room runtime.

### Preconditions

- shared runtime is active
- current node has available choices

### Primary Affordances

- `ChoiceList`
- revision-aware room runtime mutations

### Main Success Path

1. Open the room `Story Runtime` panel.
2. Select an available choice.
3. Runtime advances using the expected revision.
4. Updated node, state, and chain appear in the panel.

### Outcomes

- current shared node changes
- story state collapsible updates
- node chain updates

### Error And Conflict States

- `403`: user lacks permission to mutate runtime
- `409`: runtime revision changed elsewhere
- `422`: selected choice is no longer valid

## Use Case: Rewind Or Reset Shared Runtime

Status: `verified-ish`
Primary persona: `room owner`
Priority: `P1`

### User Goal

Back up or fully restart the room’s shared story runtime.

### Primary Affordances

- `RuntimeControls`
- rewind/reset actions backed by `useRoomRuntime`

### Outcomes

- rewind returns to a prior runtime head
- reset restarts the room runtime from the beginning

## Use Case: Compare Shared Runtime To Local-Only Player

Status: `verified-ish`
Primary persona: `operator / designer`
Priority: `P1`

### User Goal

Understand the difference between a room’s shared runtime and a local story
player panel inside the same room.

### Main Distinction

`storyRuntime`:
- shared room state
- revisioned mutations
- can rewind/reset room runtime
- intended collaborative runtime surface

`storyPlayer`:
- local-only state
- does not read from or write to shared room runtime
- shows an explicit runtime notice in room and demo contexts
- useful as a sidecar preview/comparison panel, not as the authoritative room runtime

### Documentation Importance

This distinction should appear prominently in all user walkthroughs, because it
is easy to confuse a local player panel with the authoritative shared runtime.

## Use Case: Edit Attached Story From Inside The Room

Status: `partial`
Primary persona: `author / operator`
Priority: `P1`

### User Goal

Inspect or author the attached story without leaving the room context.

### Primary Affordances

- room `storyEditor` panel

### Current Behavior

- room embeds a simplified story editor panel
- it exposes node tree and node editor against the attached story
- it is an authoring-context surface, not the shared runtime itself

### Caveat

The room editor panel is useful for convergence of authoring and runtime
contexts, but it increases the need to clearly separate authored graph changes
from shared runtime state changes in documentation.

## Runtime State Boundary Map

| Concern | Story Preview | Standalone Story Player | Room `storyRuntime` | Room `storyPlayer` |
| --- | --- | --- | --- | --- |
| Local state only | yes | yes | no | yes |
| Shared among room participants | no | no | yes | no |
| Uses room runtime projection | no | no | yes | no |
| Supports rewind/reset | yes | yes | yes | yes, but local only |
| Intended authoritative room progression | no | no | yes | no |

## Affordance Inventory

| Affordance | User-visible control | Surface | Preconditions | Outcome | Evidence |
| --- | --- | --- | --- | --- | --- |
| Create room from published story | `Room` button | story library card | story published | story-attached room created | `/home/josep/dog/frontend/src/components/Story/panels/StoryGridPanel.tsx` |
| Attach story during room creation | room dialog story select | room create dialog | user creating room | room stores `story_id` | `/home/josep/dog/frontend/src/components/Room/Dialogs/AddRoom.tsx` |
| Start room runtime | `Start Runtime` | room `storyRuntime` panel | attached story + writable room | shared runtime created | `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx` |
| Advance room runtime | choice selection | room `storyRuntime` panel | runtime active | shared node/state advance | `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts` |
| Rewind/reset room runtime | runtime controls | room `storyRuntime` panel | runtime active | shared runtime rewound/reset | `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts` |
| Open local-only player | `storyPlayer` panel | room panel assemblage | attached story | local-only play path | `/home/josep/dog/frontend/src/components/Room/panels/SoloStoryPlayerPanel.tsx` |
| Open embedded editor | `storyEditor` panel | room panel assemblage | attached story | in-room authoring context | `/home/josep/dog/frontend/src/components/Room/panels/StoryEditorPanel.tsx` |

## Recommended Walkthrough Backlog

| Walkthrough | Readiness | Notes |
| --- | --- | --- |
| Publish story and create room from library | `ready-ish` | clearest top-level handoff |
| Start room runtime and progress through a few choices | `ready-ish` | authoritative shared-runtime path |
| Compare shared `storyRuntime` with local-only `storyPlayer` | `ready-ish` | critical conceptual clarification |
| Edit attached story from room while observing runtime separately | `partial` | powerful but needs careful wording |
| Rewind/reset room runtime after branching | `ready-ish` | good for operator walkthroughs |

## Open Questions And Gaps

- whether room runtime start policy should remain owner-only or become more configurable
- whether room story editor changes should have clearer warning language relative to active runtime state
- whether room story runtime should emit more explicit chat/system traces when progression changes
- whether `storyRuntime`, `storyEditor`, and `storyPlayer` should get stronger explanatory labels in panel layout UI
