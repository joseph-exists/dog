# Walkthrough 02: Start Shared Room Runtime

Status: `ready-ish`
Persona: `room owner`

## Goal

Initialize the authoritative shared room runtime for an attached story.

## Preconditions

- room exists with `story_id` attached
- room includes the `storyRuntime` panel
- you are the room owner or otherwise have runtime write permission

## Steps

1. Open `/r/$roomId`.
2. Locate the `Story Runtime` panel.
3. If runtime is not initialized, confirm the panel shows the no-runtime state.
4. Click `Start Runtime`.
5. Complete the start dialog.
6. Wait for the runtime projection to load.

## Expected Results

- the no-runtime placeholder is replaced by active runtime UI
- the current node appears in the runtime panel
- story version badge is visible in the panel header
- runtime controls and state collapsibles become available

## Validation Checklist

- [ ] start action is visible to room owner
- [ ] runtime initializes without refresh
- [ ] current node becomes visible
- [ ] runtime controls render after start

## Failure Modes

- start action disabled:
  current user likely lacks runtime write permission
- start dialog opens but runtime does not initialize:
  room may have no valid attached story, or backend start failed
- panel remains in placeholder state:
  runtime projection was not created or was not refetched

## Evidence

- `/home/josep/dog/frontend/src/components/Room/panels/StoryPanel/StoryPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts`
