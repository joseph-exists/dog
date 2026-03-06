# Walkthrough 01: Publish Story And Create A Room From It

Status: `ready-ish`
Persona: `story author`

## Goal

Author or open a story, publish it, and create a room directly from the story
library so the story is attached at room creation time.

## Preconditions

- you can open `/stories/$storyId/edit`
- you can open `/story`
- you can create rooms

## Setup

1. Open an existing story in the editor, or create a new one from the library.
2. Ensure the story has at least:
   - one start node
   - one end node
   - at least one choice path from the start node

## Steps

1. In `/stories/$storyId/edit`, review the validation indicator.
2. Click `Publish`.
3. Complete the publish flow.
4. Return to `/story`.
5. Locate the published story card.
6. Click the `Room` affordance on that card.
7. In the create-room dialog, confirm the story is preselected.
8. Create the room.
9. Confirm you land in `/r/$roomId`.

## Expected Results

- the story appears as published in the editor and library
- the room is created with `story_id` attached
- the new room can host story-related panels against that story

## Validation Checklist

- [ ] publish action succeeds
- [ ] story card shows the room-creation affordance only when published
- [ ] room dialog inherits the story association
- [ ] new room opens successfully after creation

## Failure Modes

- publish blocked:
  story graph may be invalid or incomplete
- no `Room` affordance on card:
  story may still be draft
- room creates without story:
  story selection may have been cleared in the dialog

## Evidence

- `/home/josep/dog/frontend/src/components/Story/StoryEditor/StoryEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/panels/StoryGridPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/Dialogs/AddRoom.tsx`
