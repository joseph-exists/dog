# Demos

Status: `partial but substantial`
Primary routes:
- `/demos`
- `/demo-builder`
- `/demo/$slug`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/demo-builder.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/demo.$slug.tsx`
- `/home/josep/dog/frontend/src/components/Demo/DemoLibraryPage.tsx`
- `/home/josep/dog/frontend/src/components/Demo/rendererRegistry.tsx`
- `/home/josep/dog/frontend/src/components/Demo/builder/demoBuilderSchema.ts`
- `/home/josep/dog/frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`
- `/home/josep/dog/frontend/src/components/Demo/demo-docs/demo-builder-workflow.md`
- `/home/josep/dog/docs/affordances/demo-builder.yaml`

Related backend/services:
- `DemosService`
- `DemoService`
- `RoomService`
- `RoomRuntimeService`
- `AgentsService`
- `StoriesService`
- `PersonasService`

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

`Demo` should be treated primarily as an authored assemblage system, not just a
library of launchable pages. The most meaningful implemented surface is
`demo-builder`, where a user composes a demo out of:

- top-level runtime and presentation policy
- panel assemblages
- block assemblages
- guided capability-specific controls
- semantic validation
- preview/runtime handoff

The individual `/demo/$slug` page is the resolved presentation/runtime target
for that authored composition. It matters, but it is downstream from the
builder.

Primary user intents:
- create or select a demo configuration
- assemble a demo from panels and blocks
- bind story, persona, runtime, theme, and interaction behavior
- validate and preview the composition
- save and launch the resulting “show your work” runtime

Key integrations:
- `Room`
- `Story`
- `Agents`
- themes
- canvas/tesser rendering

## Surface Model

| Surface | Role | Status | Notes |
| --- | --- | --- | --- |
| Demo Library | discovery and management | `verified` | browse, inspect, launch, edit, delete |
| Demo Builder | primary authoring surface | `verified` | composition, panels, blocks, preview, validation, save |
| Demo Runtime Page | resolved live demo surface | `verified` | loads resolved session for slug and renders composition into room-backed runtime |
| Legacy/simple DemoPage component | older split-pane surface | `verified but secondary` | exists, but current route is centered on `ResolvedDemoRoute` |

## Verifiable Authored Object Model

The builder is grounded in a canonical composition contract and an explicit
frontend authoring layer.

Verified in code:
- `EditableComposition` is the builder authoring model over
  `DemoPageCompositionBase_Input`
- active authoring panel kinds are:
  `storyRuntime`, `chat`, `content`, `gitView`, `participantPanel`, `canvas`,
  `a2ui`, `storyEditor`, `storyPlayer`, `debug`
- active authoring block types are:
  `context`, `content`, `story`, `storyMetadata`, `agentRoster`,
  `orchestratorState`, `toolCapability`, `contributionFeed`, `gitView`,
  `fileExplorer`
- composition-level policy fields include:
  `layout_mode`, `runtime_policy`, `persona_policy`, `chat_mode`,
  `fixed_user_persona_id`, `page_theme_id`, `cards_theme_id`,
  `presentation_json`, `metadata_json`

This means the builder is not a generic markdown/page editor. It is already a
schema-constrained composition system for runtime-aware demo assemblies.

## Builder Surfaces And Affordances

### 1. Composition Editor

Implemented by `DemoTopLevelEditor`.

Verified affordances:
- edit layout mode
- edit runtime policy
- edit persona policy
- edit chat mode
- attach fixed persona
- attach page/card themes
- edit composition-level `presentation_json`
- edit composition-level `metadata_json`
- associate a story via `metadata_json.story_id`
- quick-select themes and open story picker from the builder shell

Meaning:
- users define global runtime posture before tuning individual panels and blocks
- story coupling is a first-class builder concern rather than a hidden runtime concern

### 2. Panel Editor

Implemented by `DemoPanelEditor`.

Verified affordances:
- add panel by active panel capability kind
- block panel creation when capability requirements are unmet
- edit panel primitives:
  `kind`, `id`, `title`, `order`, `default_size`, `min_size`, `max_size`,
  `prominence`, `viewport_mode`, `theme_id`, `presentation_json`, `options`
- clone existing panel
- remove panel
- configure interaction receiver options on eligible panels
- use guided presentation fields where a capability exposes them

Meaning:
- panels are authored functional surfaces, not just layout containers
- the builder already understands capability gating and panel-specific semantics

### 3. Block Editor

Implemented by `DemoBlockEditor`.

Verified affordances:
- add block by active block capability type
- block block creation when requirements are unmet
- edit block primitives:
  `type`, `id`, `title`, `order`, `region`, `visibility`, `theme_id`,
  `presentation_json`, `config_json`
- clone existing block
- remove block
- configure `gitView` metadata/config helpers
- configure click-to-chat interaction payloads for eligible block types
- target a chat panel as an interaction receiver
- use guided presentation fields where a capability exposes them

Meaning:
- blocks are both presentation objects and behavioral interfaces
- demo-builder already supports authored interaction contracts, not only static content placement

### 4. Composition Tree

Implemented by `DemoCompositionTree`.

Verified affordances:
- inspect root panel and block nodes
- detect nested panel/block nodes inside composition JSON
- focus matching editor nodes from the tree
- add child panels or blocks to detected nodes

Meaning:
- the builder is aware of nested composition structures, not just flat lists
- composition JSON can represent richer assemblages than a single-level layout

### 5. Template Setup Checklist

Implemented by `DemoTemplateSetupChecklist`.

Verified affordances:
- load a template-backed composition
- inspect unresolved template assumptions
- jump directly to missing story/persona dependencies
- confirm runtime/persona/chat assumptions
- dismiss and resume checklist flow

Meaning:
- builder templates are not just starter JSON; they carry setup workflow and dependency resolution prompts

### 6. Semantic Validation

Implemented by `DemoValidationPanel` plus builder/schema validators.

Verified affordances:
- run builder-side semantic validation
- surface warnings vs errors
- report composition paths for issues
- run capability-specific validators for panels and blocks

Current focus of validation:
- story/runtime dependencies
- composition constraints
- capability requirement mismatches

### 7. Raw JSON Editor

Implemented by `DemoRawJsonEditor`.

Verified affordances:
- edit raw composition JSON directly
- reset raw editor from current in-memory state
- apply raw JSON back into the guided editor

Meaning:
- there is a deliberate escape hatch for power users and copy/paste workflows
- the guided builder and raw composition editing are both supported paths

### 8. Preview

Implemented by `DemoBuilderPreview`.

Verified affordances:
- preview composition using the same runtime renderer registry used by demo runtime
- resolve preview against a saved demo slug when available
- reflect selected themes
- preview panel and block capability behavior through adapter hooks
- render canvas panels through async tesser/canvas jobs when a saved config and preview room exist
- block some live preview actions when the demo is unsaved or preview room context is unavailable

Meaning:
- preview is not a dead mock; it is partially runtime-coupled
- preview fidelity is real but still bounded by saved-config/runtime availability

### 9. Save / Persistence

Implemented by `DemoSaveBar` and the `demo-builder` route shell.

Verified affordances:
- show dirty vs saved state
- persist current composition
- gate save button on saveability and active save state

## Runtime / Published Demo Surface

The `/demo/$slug` route resolves a live demo session and renders it as a
room-backed runtime, not as a static page.

Verified affordances in `ResolvedDemoRoute` and `rendererRegistry`:
- resolve a session from slug
- derive room, composition, runtime policy, and metadata from the resolved demo
- render authored panels through runtime registry dispatch
- render authored blocks through runtime registry dispatch
- support runtime-aware panel kinds including:
  `storyRuntime`, `chat`, `content`, `gitView`, `participantPanel`, `canvas`,
  `a2ui`, `storyEditor`, `storyPlayer`, `debug`
- support runtime-aware blocks including:
  `storyMetadata`, `agentRoster`, `orchestratorState`, `toolCapability`,
  `contributionFeed`, `gitView`, `fileExplorer`
- add and remove room participants and agents from the demo runtime
- start room runtime where applicable
- customize panel layout/collapse state client-side
- send messages through room stream / websocket
- manage repo-context file inclusion for debug-oriented surfaces
- request canvas/tesser render jobs

Meaning:
- a demo page is a resolved orchestration of room runtime, panels, blocks, and
  attached services
- the authored demo is a runtime assembly target, not just a presentational page

## Library And Management Surface

Implemented by `DemoLibraryPage`.

Verified affordances:
- browse all visible demos
- filter by scope, status, and ownership
- search by title, slug, description
- inspect demo details in a dialog
- open demo runtime via `/demo/$slug`
- open demo builder for owned demos
- delete owned demos

This surface is useful, but it is not the center of the Demo product model.
It is a discovery and management shell around authored demo configurations.

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Browse visible demos | `verified` | implemented in library page |
| Inspect metadata for a demo before launch | `verified` | detail dialog implemented |
| Launch a resolved demo runtime | `verified` | `/demo/$slug` route resolves session |
| Open an owned demo in builder | `verified` | explicit library affordance |
| Create or select a demo config in builder | `verified-ish` | builder route supports config-centered editing flow |
| Define top-level runtime/layout/persona policy | `verified` | composition editor implemented |
| Attach a story to a demo composition | `verified` | builder story association flow exists |
| Assemble demo panels from active capability kinds | `verified` | panel editor + capability gating |
| Assemble demo blocks from active capability types | `verified` | block editor + capability gating |
| Configure presentation and theme tokens | `verified` | guided + JSON editing paths exist |
| Configure block-to-chat interaction behavior | `verified` | click prompt dispatch tooling implemented |
| Validate composition semantics before save | `verified` | validation panel implemented |
| Preview composition before launch | `verified-ish` | implemented, but some fidelity depends on saved runtime context |
| Render canvas/tesser output into demo panels | `verified-ish` | implemented with saved-config/runtime requirements |
| Add agents to demo-backed room runtime | `verified-ish` | implemented in resolved runtime route |

## Walkthrough Candidates

- Create a demo composition from a template and resolve setup dependencies
- Build a story-coupled demo with `storyRuntime`, `chat`, and `storyMetadata`
- Build a multi-panel demo with agent roster, orchestrator state, and tool capability blocks
- Configure click-to-chat interaction on a content block and bind it to a chat receiver
- Save a builder composition and open the resolved `/demo/$slug` runtime
- Compare builder preview versus resolved live demo runtime

## Open Questions And Gaps

- builder docs and code strongly suggest pack-based extensibility, but the user-facing management of capability packs is not yet a visible product surface
- preview fidelity is intentionally incomplete for some runtime-coupled behavior
- the legacy/simple `DemoPage` component still exists, but current product meaning is concentrated in `ResolvedDemoRoute`
- the next missing normalization step is a dedicated `Demo Builder -> Demo Runtime` journey doc and executable walkthrough set
