# Walkthrough: Operate A Live Demo Runtime With Layout, Participants, And Runtime-Only Actions

Status: `partial`
Persona: `operator`
Goal: validate the parts of Demo that only fully exist once the saved composition is running live

## Preconditions

- a saved demo exists with a valid slug
- you can open `/demo/$slug`
- the composition includes relevant panels such as `chat`, `participantPanel`, `canvas`, or `storyRuntime`

## Steps

1. Open `/demo/$slug`.
2. Confirm the route resolves a live demo session rather than showing a not-found or load error state.
3. Use chat if the composition exposes a chat panel.
4. If a participant panel is present, add or remove room agents or other participants as permitted.
5. If the composition includes runtime controls, start or use them as appropriate.
6. Open layout customization and adjust panel arrangement.
7. Collapse and expand panels or blocks to confirm client-side view-state persistence.
8. If a canvas panel exists, run a canvas render action and watch for the updated output.

## Expected Result

- the saved demo behaves as a room-backed runtime
- runtime-only controls work beyond what builder preview can fully simulate
- panel layout and collapse state persist for the demo view

## Verify In Code

- resolved runtime flow in `/home/josep/dog/frontend/src/routes/_layout/demo.$slug.tsx`
- layout and collapse persistence in `/home/josep/dog/frontend/src/components/Demo/demoPanelLayoutCustomization.ts`
- runtime shell rendering in `/home/josep/dog/frontend/src/components/Demo/rendererRegistry.tsx`

## Common Failure Modes

- participant or agent changes are blocked by permissions
- canvas rendering fails because worker/runtime dependencies are unavailable
- the composition was authored without the panels needed for the intended runtime checks
