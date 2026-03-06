# Walkthrough 05: Edit Attached Story From Room While Keeping Runtime Semantics Straight

Status: `partial`
Persona: `author / operator`

## Goal

Use the room’s embedded story editor panel to inspect or modify the attached
story while keeping it distinct from the active shared runtime.

## Preconditions

- room includes both `storyEditor` and `storyRuntime`
- room has an attached story
- you can edit that story

## Steps

1. Open `/r/$roomId`.
2. Open the `Story Editor` panel.
3. Inspect the node tree and select a node.
4. Make a small authoring change, such as updating node title or content.
5. Observe that the edit panel reflects the authored change.
6. Compare with the active `Story Runtime` panel.
7. Confirm that shared runtime state is not automatically reinterpreted as an
   authoring edit event.
8. If safe in your environment, refresh or reopen the room and verify that
   authored story data and runtime state remain conceptually separate.

## Expected Results

- the room editor allows authoring-oriented inspection and editing
- the runtime panel continues to represent shared progression state
- authored graph edits are not the same thing as room-runtime progression

## Validation Checklist

- [ ] node tree renders in room editor
- [ ] node editor renders selected node details
- [ ] shared runtime remains a separate panel concern
- [ ] operator can explain which panel is authoritative for shared progression

## Caveat

This walkthrough is intentionally marked `partial` because the UX could still do
more to warn users about the difference between changing the authored story and
changing the current room runtime state.

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/StoryEditorPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
