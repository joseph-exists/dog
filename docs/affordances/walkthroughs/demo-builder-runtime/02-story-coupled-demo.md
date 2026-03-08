# Walkthrough: Build A Story-Coupled Demo Assembly

Status: `ready-ish`
Persona: `demo author`
Goal: assemble a demo that is explicitly coupled to story runtime and story-aware support surfaces

## Preconditions

- a story exists
- you can edit a demo in `/demo-builder`

## Steps

1. Open `/demo-builder` with a selected demo config.
2. In `Composition`, set the story association via `metadata_json.story_id`.
3. Add a `storyRuntime` panel.
4. Add a `chat` panel.
5. Add a `storyMetadata` block.
6. Optionally add `storyEditor` or `storyPlayer` panels if you need authoring or local-player comparison surfaces.
7. Use the panel and block editors to set titles, order, prominence, and presentation settings.
8. Review `Semantic Validation` to confirm story/runtime requirements are satisfied.
9. Use preview to confirm the intended layout and story-coupled surfaces appear.
10. Save the composition.

## Expected Result

- the composition contains explicit story-coupled runtime surfaces
- validation no longer reports missing-story issues
- the saved demo is ready to open as a resolved runtime

## Verify In Code

- story association in `/home/josep/dog/frontend/src/components/Demo/builder/DemoTopLevelEditor.tsx`
- active panel/block kinds in `/home/josep/dog/frontend/src/components/Demo/builder/demoBuilderSchema.ts`
- runtime rendering in `/home/josep/dog/frontend/src/components/Demo/rendererRegistry.tsx`

## Common Failure Modes

- `metadata_json.story_id` is missing or invalid
- story-coupled panels/blocks are added before prerequisites are met
- users confuse local `storyPlayer` behavior with authoritative `storyRuntime`
