# Demo Builder -> Demo Runtime

Status: `partial`
Primary persona: `demo author / operator`
Priority: `P0`

Primary routes:
- `/demo-builder`
- `/demo/$slug`
- `/demos`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/demo-builder.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/demo.$slug.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoTopLevelEditor.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoPanelEditor.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoBlockEditor.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoValidationPanel.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/DemoBuilderPreview.tsx`
- `/home/josep/dog/frontend/src/components/Demo/rendererRegistry.tsx`
- `/home/josep/dog/frontend/src/components/Demo/DemoLibraryPage.tsx`

Related backend/runtime references:
- `DemosService`
- `DemoService`
- `RoomService`
- `RoomRuntimeService`
- `AgentsService`

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

This journey documents how an authored demo composition becomes a resolved,
room-backed runtime.

The key distinction is:
- `demo-builder` is the authoring surface for composition, capability assembly,
  validation, and preview
- `/demo/$slug` is the resolved runtime target for a saved composition
- builder preview can simulate or partially resolve runtime behavior, but the
  authoritative handoff happens through a saved demo config and resolved slug

This boundary matters for walkthroughs because some actions are available only
after the composition has been saved and resolved into a live demo session.

## Journey Summary

| Step | Surface | What happens |
| --- | --- | --- |
| 1 | Demo Builder | author selects or creates a demo config |
| 2 | Demo Builder | author applies a template or assembles composition manually |
| 3 | Demo Builder | author resolves setup dependencies such as story/persona/runtime assumptions |
| 4 | Demo Builder | author edits panels, blocks, themes, and interaction behavior |
| 5 | Demo Builder | author validates and previews the composition |
| 6 | Demo Builder | author saves the composition |
| 7 | Demo Runtime | `/demo/$slug` resolves session and renders the saved composition against room runtime |
| 8 | Demo Runtime | operator can use live runtime affordances such as chat, participants, agents, layout, and canvas |

## Surface Roles In This Journey

| Surface | Role |
| --- | --- |
| Demo Library | discovery, launch, and management shell |
| Demo Builder | canonical authoring surface |
| Builder Preview | unsaved or saved composition inspection surface |
| Resolved Demo Runtime | authoritative runtime target for a saved slug |

## What Is Frontend-Visible Today

| Capability | Status | Notes |
| --- | --- | --- |
| Create a demo from generated slug/title flow | `verified-ish` | builder route contains create flow and slug generation |
| Apply composition template | `verified` | template selector and apply/create-from-template flows exist |
| Resolve template assumptions | `verified` | checklist supports story/persona/runtime prompts |
| Edit composition policies | `verified` | top-level editor implemented |
| Add active panel and block kinds | `verified` | capability-gated editor flows exist |
| Configure interaction contracts on eligible blocks | `verified` | click prompt dispatch path exists |
| Run semantic validation | `verified` | builder validation panel exists |
| Preview composition locally or globally | `verified-ish` | preview mode selector and preview pane exist |
| Save composition | `verified` | save bar exists |
| Open resolved runtime from builder | `verified` | builder exposes `/demo/$slug` preview link |
| Resolve slug into room-backed runtime | `verified` | demo route resolves session for slug |
| Manage participants/agents in runtime | `verified-ish` | resolved runtime exposes participant and agent controls |
| Persist live layout/collapse customization per demo view | `verified` | runtime stores layout/collapse state client-side |

## Core Use Cases

## Use Case: Create Or Select A Demo Config In Builder

Status: `verified-ish`
Primary persona: `demo author`
Priority: `P0`

### User Goal

Enter the builder with a concrete demo config as the save target.

### Entry Points

- `/demo-builder`

### Preconditions

- user can access demo builder

### Primary Affordances

- demo selector
- slug/title creation flow
- generated slug helper

### Main Success Path

1. Open `/demo-builder`.
2. Select an existing demo config or create a new one.
3. Confirm the builder loads that config as the active composition target.

### Outcomes

- builder is editing a concrete demo config
- save and resolved-runtime handoff become possible

## Use Case: Apply A Template And Resolve Setup Assumptions

Status: `verified`
Primary persona: `demo author`
Priority: `P0`

### User Goal

Start from a composition template and make it valid for the intended runtime
scenario.

### Preconditions

- builder is open

### Primary Affordances

- template selector
- apply template action
- template setup checklist
- story/persona quick actions

### Main Success Path

1. Choose a composition template.
2. Apply it to the builder or create a new demo directly from the template.
3. Review unresolved setup checklist items.
4. Attach required story/persona/runtime settings.
5. Confirm checklist assumptions until the template is save-ready.

### Outcomes

- composition starts from a known authored pattern
- unresolved template dependencies are surfaced before save/runtime handoff

## Use Case: Assemble Runtime-Coupled Panels And Blocks

Status: `verified`
Primary persona: `demo author`
Priority: `P0`

### User Goal

Build the meaningful demo assemblage that will be shown at runtime.

### Primary Affordances

- `DemoTopLevelEditor`
- `DemoPanelEditor`
- `DemoBlockEditor`
- `DemoCompositionTree`

### Main Success Path

1. Configure top-level runtime, persona, chat, and theme policy.
2. Add panels such as `storyRuntime`, `chat`, `participantPanel`, `a2ui`, or `debug`.
3. Add blocks such as `storyMetadata`, `agentRoster`, `orchestratorState`, `toolCapability`, or `content`.
4. Use the composition tree to inspect and focus authored nodes.
5. Adjust IDs, ordering, visibility, and presentation settings until the composition matches the intended demo behavior.

### Outcomes

- authored composition expresses both presentation structure and runtime behavior

## Use Case: Configure Block-To-Chat Interaction Contracts

Status: `verified`
Primary persona: `demo author`
Priority: `P1`

### User Goal

Turn a content-oriented block into a functional interaction surface that sends
user input and selected source context to chat.

### Preconditions

- composition includes an eligible block type such as `content`, `context`, or `gitView`
- composition includes a chat panel that can receive dispatches

### Primary Affordances

- `config_json.interaction` helpers in `DemoBlockEditor`
- interaction receiver options in `DemoPanelEditor`

### Main Success Path

1. Add an eligible block.
2. Configure click prompt dispatch behavior in the block editor.
3. Configure a chat panel as an interaction receiver.
4. Preview the interaction behavior.
5. Save and verify it again in the resolved runtime.

### Outcomes

- demo includes authored functional interfaces, not only passive content

## Use Case: Preview, Save, And Open The Resolved Runtime

Status: `verified-ish`
Primary persona: `demo author`
Priority: `P0`

### User Goal

Validate the composition in builder, persist it, and open the live runtime
version.

### Primary Affordances

- preview mode selector
- local/global preview pane
- semantic validation panel
- save bar
- `Open Preview: /demo/$slug` link

### Main Success Path

1. Review validation warnings/errors.
2. Use preview mode to inspect the composition.
3. Save the composition.
4. Open the resolved `/demo/$slug` preview/runtime link.
5. Confirm the saved runtime matches the intended authored structure.

### Outcomes

- authored composition becomes a launchable, shareable runtime surface

### Caveat

Some preview behaviors are intentionally limited when the demo config is
unsaved or when a preview room has not been resolved yet.

## Use Case: Operate The Live Demo Runtime

Status: `verified-ish`
Primary persona: `operator`
Priority: `P1`

### User Goal

Use the saved demo as a live runtime experience rather than as builder state.

### Primary Affordances

- runtime panel and block rendering
- room messaging
- participant/agent management
- runtime start where applicable
- panel layout customization
- collapse/expand controls
- canvas render actions

### Main Success Path

1. Open `/demo/$slug`.
2. Confirm the runtime resolves successfully.
3. Interact with chat, story/runtime, participants, agents, and support blocks.
4. Adjust panel layout and collapse state as needed.
5. Use runtime-only actions such as participant management or canvas rendering.

### Outcomes

- saved demo is consumed as an operational runtime
- some runtime affordances go beyond what builder preview can simulate

## Open Questions And Gaps

- builder preview is close to runtime but not identical, especially for saved-room and async worker paths
- capability packs are present in architecture but are not yet a user-facing management workflow
- the builder and runtime support rich agent/runtime assemblies, but seeded QA fixtures for repeatable demo walkthroughs are still needed
