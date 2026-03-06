# Story

Status: `partial`
Primary routes:
- `/story`
- `/story/$storyId`
- `/stories/$storyId/edit`

Primary files:
- `/home/josep/dog/frontend/src/routes/_layout/story.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/story_.$storyId.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/stories/$storyId/edit.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/StoryEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/NodeEditor/NodeEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/NodeEditor/NodeEditorForm.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/NodeEditor/ChoiceEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryEditor/StateSchema/StateSchemaEditor.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryPlayer/StoryPlayerProvider.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryPlayer/StoryContent.tsx`
- `/home/josep/dog/frontend/src/components/Story/StoryPlayer/StoryPreview.tsx`
- `/home/josep/dog/frontend/src/components/Story/panels/StoryDebugPanel.tsx`
- `/home/josep/dog/frontend/src/hooks/stories/useStoryEditor.ts`
- `/home/josep/dog/frontend/src/hooks/stories/storyValidation.ts`

Related backend/services:
- `StoriesService`
- `StorynodesService`
- story state schema endpoints and choice/node CRUD hooks

Related design/planning references:
- `/home/josep/dog/docs/plans/story-presentation-design.md`
- `/home/josep/dog/docs/plans/story-presentation-design-v2.md`
- `/home/josep/dog/docs/plans/2026-02-12-story-player-panel-refactor.md`

Last reviewed: `2026-03-06`
Reviewer: `Codex`

## Summary

Story should be documented as an authored state machine builder with multiple
surfaces:
- a library surface for discovery and entry
- an editor surface for graph authoring, node editing, conditional transitions,
  and state-schema definition
- a preview surface for author-side runtime testing
- a player surface for standalone consumption
- a room handoff path where a published story becomes shared runtime material

In the current implementation, Story already supports:
- versioned story records
- node-graph authoring
- choice-based transitions
- `requires_state` and `sets_state` behavior on choices
- player runtime state, history, undo, and restart
- content-format-based node presentation and preview
- publish/unpublish workflow and basic validation

Story is therefore both:
- a presentation system, because nodes render authored content in multiple
  formats and are intended to support deeper authored presentation
- a functional interface, because nodes and choices expose runtime state changes
  and gate progression through a stateful graph

## Surface Map

| Surface | Route | Primary role |
| --- | --- | --- |
| Story Library | `/story` | discover, create, inspect, and enter stories |
| Story Editor | `/stories/$storyId/edit` | author node graph, state schema, and publishable runtime |
| Story Preview | inside editor | author-side simulation and debug of runtime behavior |
| Story Player | `/story/$storyId` | standalone user-facing player surface |
| Room Story Runtime | room-linked | shared runtime consumption path for published stories |

## Story As State Machine

### Primary authored objects

| Object | Current role in UX |
| --- | --- |
| `Story` | top-level authored experience, versioned and publishable |
| `StoryNode` | authored state/page unit with content, entry/exit semantics, and node flags |
| `NodeChoice` | directed transition with conditions and state mutations |
| `StoryStateVariable` | explicit schema for state keys, types, defaults, and categories |
| `playerState` | runtime key-value state accumulated during play |
| `history` | runtime navigation memory for undo and debugging |

### What makes a node both presentation and function

A node currently acts as:
- a presentation object through `title`, `content`, and `content_format`, plus
  inline preview and player rendering
- a functional runtime interface because the node's outgoing choices determine
  which state conditions are required and what state mutations happen next

A choice currently acts as:
- a visible UI affordance in the player
- a stateful transition rule through `requires_state` and `sets_state`
- a graph edge connecting authored states

## Role And State Matrix

| Dimension | Values | Notes |
| --- | --- | --- |
| Authoring status | `draft`, `published`, `published with newer draft` | affects publish/unpublish flows and room handoff confidence |
| Node role | `start`, `end`, `normal` | edited in node form; affects runtime semantics |
| Choice state | `unconditional`, `conditional`, `state-mutating`, `both` | determines available runtime transitions |
| Runtime mode | `editor preview`, `standalone player`, `room runtime` | same authored graph, different consumption context |
| Presentation mode | content-format-driven today; richer story/node presentation partially planned | important distinction between implemented and planned behavior |

## Current Story Surface Affordances

| Affordance | User-visible control | Surface | Preconditions | Outcome |
| --- | --- | --- | --- | --- |
| Create story | create modal | library | signed-in user | new story exists |
| Open story editor | link/edit route | library/detail | story accessible | authoring UI opens |
| Clone story | `Clone` button | editor | story loaded | new draft story created |
| Define state schema | `State Schema` sheet | editor | story loaded | runtime state variables are created/edited |
| Add/edit node | node tree + node form | editor | story loaded | node content and role update |
| Mark start/end node | checkboxes | node form | node selected | runtime entry/ending semantics update |
| Add/edit choice | `Add Choice` / edit icon | node editor | non-end node selected | graph transitions change |
| Gate a choice on state | `Requires State` section | choice editor | choice open | conditional availability changes |
| Mutate state on choice | `Sets State` section | choice editor | choice open | runtime state effects change |
| Preview authored runtime | `Preview` button | editor | story loaded | author-side simulation opens |
| Debug runtime state | debug panel / preview debug | player or preview | runtime active | inspect state/history/blocked choices |
| Publish story | `Publish` button | editor | validation passes or warnings accepted | published version advances |
| Unpublish story | `Unpublish` button | editor | story published | published visibility removed |
| Play standalone | player route | library/player | story accessible | standalone story runtime |
| Create room from story | `Room` affordance on published cards | library | story published | room linked to story |

## StoryEditor Mapping

Status: `partial`

The editor is the primary authored state-machine surface.

### What the editor currently enables

- select nodes from a left-hand node tree
- edit node title, content, content format, and start/end semantics
- create, edit, and delete transitions
- define `requires_state` and `sets_state` on each choice
- define explicit state variables in a categorized schema sheet
- preview current authored graph without leaving the editor
- validate and publish the current version
- clone the story into a new authoring branch

### StoryEditor as presentation authoring

Current presentation control is strongest at the node content level:
- content format selection changes how the node is rendered
- HTML content uses a rich text editor
- non-HTML formats use direct text editing
- inline preview renders the node as authored content

This means node presentation is already customizable in practice through:
- content format
- content payload
- live preview

But deeper authored presentation remains only partially realized:
- story-level and node-level theming are discussed in design docs
- the library/player shell already supports page and card themes
- explicit per-node presentation schema appears to still be in design or partial state

### StoryEditor as functional state-machine authoring

This is already strong and concrete:
- start node sets the runtime entry point
- end node defines terminal nodes
- graph edges are authored via choices
- `requires_state` determines if a choice is visible/valid at runtime
- `sets_state` mutates runtime state when a choice is taken
- state schema documents and constrains the intended runtime keys

## StoryPlayer Mapping

Status: `partial`

The standalone player is the runtime consumption surface for the authored story.

### What the player currently enables

- resolve the story and its current nodes/choices
- initialize from the authored start node
- maintain runtime `playerState`
- filter available choices by evaluating `requires_state`
- apply `sets_state` when choices are selected
- keep navigation history for undo
- restart from the start node
- render a dedicated debug panel with state, history, and blocked choices

### StoryPlayer as presentation runtime

The player currently renders nodes as user-facing content objects:
- node title and content are displayed in a card-based player surface
- `ContentRenderer` maps content format to the runtime renderer
- story-level shell theming exists for page/cards
- room or viewer theming/presentation cascade is still a broader design area

### StoryPlayer as functional runtime

The player is an actual local state machine executor:
- authored graph data comes from `useStoryEditor`
- runtime state is held in `StoryPlayerProvider`
- choice conditions are evaluated at runtime
- state mutations are applied at runtime
- dead ends and terminal endings are surfaced distinctly

## StoryPreview Mapping

Status: `verified-ish`

`StoryPreview` is the author-side simulation environment embedded in the editor.
It is the clearest bridge between authoring and runtime because it exposes:
- the same start-node and choice logic as the player
- local runtime state
- undo and restart controls
- a built-in debug panel for state/history/choices

This makes preview the primary affordance for validating authored node logic
before publishing or room handoff.

## Story -> Room Runtime Mapping

Status: `partial`

Story connects directly to room runtime in two important ways:
- published stories expose a room-creation affordance from the library
- room surfaces can host story runtime/editor/player panels tied to the room's story

This means Story is not only standalone content. It is also upstream authored
runtime for collaborative room experiences.

The important documentation distinction is:
- StoryEditor authors the graph and state semantics
- StoryPlayer and StoryPreview execute that graph locally
- Room runtime is the shared, collaborative consumer of the story's authored structure

## Available High-Level Use Cases

| Use case | Status | Notes |
| --- | --- | --- |
| Browse story library | `verified-ish` | grid panel exists |
| Distinguish published stories from drafts | `verified-ish` | split sections in library |
| Create a story | `partial` | modal exists on library page |
| Open standalone player | `verified-ish` | player route exists |
| Open story editor | `verified-ish` | edit route exists |
| Author a node graph | `verified-ish` | node tree + choice editing support graph authoring |
| Mark start and end nodes | `verified-ish` | node form checkboxes exist |
| Define state schema | `verified-ish` | state schema sheet exists |
| Add conditional transitions | `verified-ish` | choice editor supports `requires_state` |
| Add state mutations to transitions | `verified-ish` | choice editor supports `sets_state` |
| Preview and debug authored runtime | `verified-ish` | editor preview supports runtime debug |
| Validate for publish | `partial` | structural validation exists; deeper semantic validation may still be light |
| Publish and unpublish story | `verified-ish` | explicit buttons exist |
| Clone story into a new draft | `verified-ish` | clone flow exists |
| Create room from a published story | `verified-ish` | library affordance exists |
| Deep authored presentation overrides per node | `partial/stub` | content-format authoring exists; fuller story/node presentation model still appears incomplete |

## Walkthrough Candidates

- Create a story, add a start node, and publish a minimal graph
- Define a state variable and use it to gate a choice
- Create a choice that mutates state and changes downstream available paths
- Preview a story and inspect state/history in debug mode
- Publish a story and create a room from it
- Compare standalone player behavior with room-linked story runtime

## Open Questions And Gaps

- the editor route imports `@/components/Stories/StoryEditor/StoryEditor`, while
  most story code lives under `@/components/Story`; this should be verified as
  intentional aliasing rather than drift
- author-level story/node presentation is conceptually important, but much of
  the richer theme-schema work still appears to be in planning rather than fully surfaced in the current node editor
- player route currently sets `canEdit={true}` with a TODO in the route-level code
- publish validation in `useStoryEditor` is lighter than the dedicated graph
  validation utility, so the actual publishing gate should be clarified
- room runtime integration should get its own dedicated journey doc after this top-level mapping
