# Walkthrough 03: Advance, Rewind, And Reset Shared Runtime

Status: `ready-ish`
Persona: `room owner`

## Goal

Verify that the room’s shared story runtime can move forward, rewind, and fully
reset using the runtime controls.

## Preconditions

- shared room runtime is already active
- current node exposes at least one choice path

## Steps

1. Open the `Story Runtime` panel in `/r/$roomId`.
2. Record the current node title.
3. Select one available choice.
4. Confirm the current node changes.
5. Inspect the node chain and story state collapsibles.
6. Use `Rewind`.
7. Confirm the prior runtime position is restored.
8. Advance again along a branch.
9. Use `Reset`.
10. Confirm runtime returns to the initial path/start state.

## Expected Results

- advancing changes the shared node
- node chain updates to reflect progression
- state collapsible reflects any authored runtime state
- rewind restores an earlier shared runtime head
- reset restarts the room runtime from the beginning

## Validation Checklist

- [ ] advance updates the current node
- [ ] node chain changes as runtime progresses
- [ ] rewind works only when a prior runtime head exists
- [ ] reset returns runtime to initial state

## Conflict And Error Checks

- if a `409` occurs, verify concurrent revision conflict handling
- if a `422` occurs, verify invalid choice handling
- if a `403` occurs, verify mutation permissions are correctly enforced

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
