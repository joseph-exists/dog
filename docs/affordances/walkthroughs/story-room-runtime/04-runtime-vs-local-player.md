# Walkthrough 04: Compare Shared `storyRuntime` With Local-Only `storyPlayer`

Status: `ready-ish`
Persona: `operator / designer`

## Goal

Prove that room `storyRuntime` is the authoritative shared progression surface
while room `storyPlayer` is local-only.

## Preconditions

- room has both `storyRuntime` and `storyPlayer` panels available in its panel set
- room has an attached story
- shared runtime can be started

## Steps

1. Open `/r/$roomId`.
2. Start shared runtime if needed.
3. In `storyRuntime`, note the current node.
4. In `storyPlayer`, start the local player if needed.
5. Advance the local player once.
6. Confirm the shared runtime panel does not change.
7. Advance the shared runtime once.
8. Confirm the local player does not automatically sync to the shared runtime’s node.
9. Read the local-only runtime notice shown in the `storyPlayer` panel.

## Expected Results

- the two panels can diverge
- `storyRuntime` mutations do not automatically reposition the local player
- `storyPlayer` interactions do not mutate shared room runtime
- the runtime notice clearly warns about local-only semantics

## Validation Checklist

- [ ] local player can run independently
- [ ] shared runtime can run independently
- [ ] advancing one does not update the other
- [ ] local-only notice is visible

## Why This Walkthrough Matters

This is the single most important conceptual guardrail in story-room
documentation. Users and operators must not mistake `storyPlayer` for shared
room progression.

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/SoloStoryPlayerPanel.tsx`
- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
