# Walkthrough: Configure Click-To-Chat Interaction From Block To Panel

Status: `ready-ish`
Persona: `demo author`
Goal: make a content-oriented block act as a functional interaction source that dispatches to chat

## Preconditions

- you can edit a demo in `/demo-builder`
- the composition includes or can include a `chat` panel

## Steps

1. Open `/demo-builder` with a selected demo config.
2. Add a `chat` panel if one is not already present.
3. In the panel editor, enable interaction receiver settings for that chat panel.
4. Add an eligible block such as `content`, `context`, or `gitView`.
5. In the block editor, configure the interaction contract under `config_json`.
6. Set the dispatch target to the intended chat panel.
7. Use preview to test the click-to-input flow if available for the authored content.
8. Save the composition.
9. Open `/demo/$slug` and verify the interaction in resolved runtime.

## Expected Result

- clicking eligible block content opens the configured interaction flow
- the message is dispatched to the intended chat receiver
- the runtime demonstrates that the block is a functional interface, not just display content

## Verify In Code

- interaction helper text and config support in `/home/josep/dog/frontend/src/components/Demo/builder/DemoBlockEditor.tsx`
- receiver options in `/home/josep/dog/frontend/src/components/Demo/builder/DemoPanelEditor.tsx`
- interaction handling references in `/home/josep/dog/frontend/src/components/Demo/demo-docs/demo-builder-workflow.md`

## Common Failure Modes

- no chat panel is configured as a receiver
- dispatch target does not match a real panel id
- authored content does not expose selectable/clickable source elements
