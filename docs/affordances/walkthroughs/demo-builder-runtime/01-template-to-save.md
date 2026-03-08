# Walkthrough: Create A Demo From A Template And Resolve Setup Requirements

Status: `ready-ish`
Persona: `demo author`
Goal: start from a composition template, satisfy required assumptions, and save a valid demo config

## Preconditions

- you can access `/demo-builder`
- you can create or edit a demo config

## Steps

1. Open `/demo-builder`.
2. If no demo is selected, create a new demo config or select an existing one.
3. In the template selector, choose a composition template.
4. Apply the template to the editor.
5. Review the `Template Setup Checklist`.
6. If the checklist requires a story, use the story picker or set `metadata_json.story_id`.
7. If the checklist requires persona/runtime/chat confirmations, set those values and mark them confirmed.
8. Review `Semantic Validation` for any blocking errors.
9. Click `Save Composition`.

## Expected Result

- the composition saves successfully
- the checklist is fully resolved or reduced to non-blocking items
- builder shows saved rather than unsaved state

## Verify In Code

- template apply/create flow in `/home/josep/dog/frontend/src/routes/_layout/demo-builder.tsx`
- checklist UI in `/home/josep/dog/frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx`
- save affordance in `/home/josep/dog/frontend/src/components/Demo/builder/DemoSaveBar.tsx`

## Common Failure Modes

- template still has unresolved required assumptions
- semantic validation reports an error-level issue
- no demo config is selected as the save target
