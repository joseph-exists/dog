# Walkthrough: Preview, Save, And Open The Resolved Demo Runtime

Status: `ready-ish`
Persona: `demo author`
Goal: compare builder preview with the live saved runtime target

## Preconditions

- a demo config is selected
- the composition has at least one visible panel or block

## Steps

1. Open `/demo-builder`.
2. Select `local` or `global` preview mode.
3. Review the preview pane and any preview diagnostics.
4. If validation reports blocking issues, resolve them first.
5. Click `Save Composition`.
6. Use the builder link `Open Preview: /demo/$slug`.
7. Confirm the resolved runtime loads successfully.
8. Compare the resolved runtime against what you saw in builder preview.

## Expected Result

- preview is useful for composition inspection before save
- saving enables the authoritative slug-backed runtime handoff
- `/demo/$slug` renders the saved composition through the runtime route

## Verify In Code

- preview mode and preview link in `/home/josep/dog/frontend/src/routes/_layout/demo-builder.tsx`
- preview renderer in `/home/josep/dog/frontend/src/components/Demo/builder/DemoBuilderPreview.tsx`
- resolved runtime route in `/home/josep/dog/frontend/src/routes/_layout/demo.$slug.tsx`

## Common Failure Modes

- preview looks correct but runtime-specific behavior is still unavailable before save
- the demo slug or config was not created successfully
- resolved runtime fails because the backing session cannot be loaded
