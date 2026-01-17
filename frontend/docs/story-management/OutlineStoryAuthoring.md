**Tinyfoot Story Authoring Implementation Guide**

Below is a synthesized, engineer-facing implementation guide that combines the **mental models and use cases** from Story-Authoring-Guide.md with the **accurate, implementation-ready component architecture and patterns** from StoryAuthoringGuideV2.md and the Story-Author-Reference-Guide.md, aligned to Tinyfoot frontend practices.[1][2][3][4][5]

## What you’re building
The Story Authoring UI is the author-facing product that lets authors create, edit, and publish branching CYOA stories (nodes + choices) with conditional logic and safe versioning. The backend is ready for implementation (APIs implemented), and the intended MVP scope is “My Stories” + Story Editor + Publish/Unpublish, with future enhancements like timeline navigation UI and richer visualization.[2][3]

A critical mental model: the story system operates in three contexts (namespaces)—**Authoring** (mutable drafts), Discovery (catalog), and Playing (per-player progression)—and this guide focuses on Authoring only.[3]

## Mental models and domain rules
Treat a story like a versioned template (similar to a repo): **currentversion** is the editable working draft, while **publishedversion** is what players see and is effectively immutable once published. Nodes are version-scoped via **storyversion**, so fetching/editing must always be filtered to the story’s currentversion while authoring.[1][2][3]

Story lifecycle states (derived from fields) drive UI badges and available actions.[2][1]

| State | ispublished | publishedversion | Meaning |
|---|---:|---:|---|
| Draft | false | null | New story, never published.[2][1] |
| Published | true | set | Visible in catalog; players lock to publishedversion at start.[2][3] |
| Unpublished | false | set | Hidden from catalog; existing players continue on locked version.[2][3] |
| Editing | (either) | set | currentversion > publishedversion indicates unpublished changes / editing a new version.[2][1] |

State logic mental model: player (and test) state is a JSON dictionary that grows via choice **setsstate** (shallow merge), and choice visibility uses **requiresstate** with AND semantics (all conditions must match). Keys are freeform (no enforced schema), so UX should make author intent clear (e.g., JSON preview + typed key/value editor for booleans/strings/numbers).[3][1][2]

## Frontend architecture and team patterns
Use the Tinyfoot standard stack: React + TypeScript (Vite), TanStack Query for server state, TanStack Router for routing, ShadCN for components and TailwindCSS for styling, React Hook Form for forms, and the OpenAPI-generated SDK client for API calls. Authentication uses JWT stored in localStorage, with consistent auth handling and role-based UI (e.g., delete story may be superuser-only per API behavior), so routes should be protected appropriately.[4][1][2]

**Feature-first layout (Stories feature) and file placement** should follow the guides’ directory structure so the authoring UI fits existing conventions.[5][1][2]
- `src/components/Stories/StoryList/` → `StoryList.tsx`, `StoryCard.tsx`, `CreateStoryModal.tsx`.[1][2]
- `src/components/Stories/StoryEditor/` → `StoryEditor.tsx`, `NodeTree/*`, `NodeEditor/*`, `PropertiesPanel/*`.[2][1]
- `src/components/Stories/shared/` → `StateConditionEditor.tsx`, `storyValidation.ts` utilities.[1][2]
- `src/hooks/stories/` → `useStories`, `useStoryEditor`, `useStoryNodes`, `useNodeChoices`, `usePublishWorkflow`.[2][1]

**TanStack Query conventions (keys + invalidation)** are mandatory for consistency and cache correctness.[5][2]
- Key patterns (examples): lists like `['stories']`, story detail `['stories', storyId]`, nodes list `['stories', storyId, 'nodes']`, node choices `['nodes', nodeId, 'choices']`.[2]
- Mutation pattern: call SDK service → success toast (useCustomToast) → invalidate relevant query keys → handle errors via `handleError` → reset/close modal as needed.[5][2]

**Form conventions**: React Hook Form with `mode: 'onBlur'`, explicit `defaultValues`, standard Field components, disable submit when invalid, and show loading during submit.[5][2]

## Authoring use cases (end-to-end)
These use cases define what the UI must do and which services/queries/mutations it should use.[3][2]

- **Use case: List author’s stories (My Stories)**
  - Query: `StoriesService.readStories` with query key `['stories']` and handle loading/empty states.[2]
  - UI: StoryCard shows derived badge based on lifecycle fields (Draft/Published/Unpublished/Editing) and shows version numbers (current vs published).[3][2]
  - Actions: Edit navigation, Publish/Unpublish toggles visibility, Delete is conditional (superuser-only per API behavior described in specs).[2]

- **Use case: Create a story**
  - Mutation: `StoriesService.createStory` with title required (and description optional), then invalidate `['stories']` and navigate to editor (optional but recommended for UX).[1][2]
  - Rule: Do not send currentversion from the client (it is set automatically), so form types should match the SDK create type.[3][2]

- **Use case: Edit a story (Story Editor shell)**
  - Layout: three panels—NodeTree (left), NodeEditor (center), PropertiesPanel (right)—with selectedNodeId in local component state.[3][2]
  - Data: load story via `StoriesService.readStory`, then load nodes for the story’s **currentversion** (filter storyid + storyversion).[2]

- **Use case: Create/update nodes and choices**
  - Nodes: `StorynodesService.createStorynode` / `updateStorynode` / `deleteStorynode`, scoped to storyversion; enforce “only one start node per version” via UI validation (warn/block as appropriate).[2]
  - Choices: edit choice properties (text, tonodeid, order, requiresstate, setsstate) via `NodeChoicesService.updateNodeChoice`, and create choices from a node via `StorynodesService.createNodeChoiceFromNode` where applicable.[2]
  - Editor UX: use a reusable StateConditionEditor for requiresstate/setsstate with validation and JSON preview mode.[2]

- **Use case: Publish / Unpublish**
  - Publish triggers pre-publish validation (start/end/reachability/choice validity) and then calls `StoriesService.publishStory`; Unpublish calls `StoriesService.unpublishStory` and keeps publishedversion intact.[1][3][2]
  - UX: publish modal should surface validation summary and allow cancel; post-publish should toast success and refresh list/story state via invalidation.[3][2]

- **Use case: Create new version (edit without affecting players)**
  - Flow: `StoriesService.createNewStoryVersion` increments currentversion, copies published nodes/choices to the new version, and leaves publishedversion unchanged so existing players remain on old version.[3][2]
  - UX: clearly indicate “editing vN draft while vM is published” and warn that changes won’t affect existing players.[3]

## Validation, testing, and rollout plan
Validation is both UX (field-level) and structural (graph-level), and the publish workflow is the enforcement point. Pre-publish checks include: exactly one start node for currentversion, at least one end node, reachability from start via graph traversal, choice destinations valid and within the same version, and orphan detection (often warn vs hard-block depending on rule).[1][3][2]

Testing strategy should match Tinyfoot practices: unit test critical components and hooks, component test the creation/editing flows, and integration test publish/version isolation workflows. Implementation should follow the phased checklist (StoryList MVP → Editor shell → Node/Choice management → Publish workflow → polish like autosave/shortcuts/drag-drop), ensuring each phase ends with a stable, shippable slice.[5][1][2]


## Overview and Purpose

Authors create branching CYOA stories via a three-panel editor supporting node/choice management, state conditions, versioning, and publishing with validation. The UI uses React/TypeScript, TanStack Query/Router, ShadCN,TailwindCSS, React Hook Form, and auto-generated SDKs per the tech stack. Stories enable conditional choices (requiresstate AND logic) and state tracking (setsstate shallow merge), with safe edits via currentversion (editable draft) vs publishedversion (immutable).

## Domain Concepts

Stories track states: Draft (ispublished false, publishedversion null), Published (true, set), Unpublished (false, set), Editing (currentversion > publishedversion). Nodes belong to storyversion; exactly one isstartnode per version, multiple isendnode; choices link fromnodeid to tonodeid with order, requiresstate/setsstate JSON. Publishing copies currentversion to publishedversion; new versions copy published nodes/choices for isolation.

## Use Case Breakdowns

- **List Stories**: Fetch via StoriesService.readStories; display in grid with StoryCard badges (e.g., "Published v1", "Draft v2"), actions (Edit, Publish/Unpublish, Delete superuser).[^2][^3]
- **Create Story**: POST StoriesService.createStory (title req max100, desc opt max500); invalidate ['stories'], navigate to editor.[^1][^2]
- **Edit Node/Choices**: Load nodes for currentversion (filter storyid/storyversion); update via StorynodesService; choices via NodeChoicesService.[^3][^2]
- **Publish**: Validate (1 start, ≥1 end, reachable nodes, valid targets); PUT StoriesService.publishStory; show toast, update badges.[^1][^2]
- **New Version**: POST StoriesService.createNewStoryVersion; copies published to new currentversion.


## Architecture and Tech Stack

Organize in src/components/Stories: StoryList (list/cards/modal), StoryEditor (NodeTree left, NodeEditor center, PropertiesPanel right), shared (StateConditionEditor, storyValidation.ts), hooks/stories (useStories, useStoryEditor, etc.). Use SDK clients; query keys like ['stories', storyId, 'nodes']; mutations invalidate relevant keys post-success. Routes: /stories (list), /stories/:storyId/edit.

## Component Specifications

| Component | Location | Key Props/Data | Mutations/Actions |
| :-- | :-- | :-- | :-- |
| StoryList | src/components/Stories/StoryList/ | useStories() ['stories'] | Create (modal), navigate edit, toggle publish [^2] |
| StoryCard | src/components/Stories/StoryList/ | story: StoryPublic | Badges by state, edit/delete [^1][^3] |
| NodeTree | src/components/Stories/StoryEditor/ | storyId, version, selectedNodeId | Select node, onSelect callback [^2] |
| NodeEditor | src/components/Stories/StoryEditor/ | nodeId, storyId/version | Update node/choice CRUD, CreateNodeModal [^1][^2] |
| StateConditionEditor | src/components/Stories/shared/ | value, onChange | Add/remove key-values (bool/str/num), JSON preview [^2] |
| PublishModal | src/components/Stories/PublishWorkflow/ | storyId | Pre-validate, publish/unpublish [^1] |

Forms use React Hook Form (mode: 'onBlur', defaultValues, Field wrapper, disable !isValid).[^5][^4]

## Implementation Patterns

Mutations: `useMutation({ mutationFn: data => service.method(data), onSuccess: () => { toast.success(); queryClient.invalidateQueries({ queryKey: [...] }); }, onError: handleError })`. Custom hooks extract logic (e.g., useStoryNodes for CRUD/filtering by version); local state for selectedNodeId/modals. Errors: form errors.field?.message, useCustomToast/handleError for API. Responsive Component layouts [^5][^2]

**Phased Checklist**:

- Phase 1: StoryList MVP (list/create/publish toggle).[^1]
- Phase 2: Editor layout + tree/editor/panel.[^1]
- Phase 3: Node/choice modals + hooks.[^1]
- Phase 4: Publish workflow + validation.[^1]
- Phase 5: Autosave, shortcuts.[^1]


## Validation and Testing

**Pre-publish**: 1 startnode, ≥1 endnode, all reachable (graph traversal), choices to same-version nodes, no orphans (warn). **Forms**: Title/content lengths, valid JSON states. Tests: Unit (hooks like useStories, components like StoryCard badges), component (NodeEditor forms), integration (create-publish-version flows).[^2][^5][^1]

## Reference Appendix

**Key Types** (from SDK): StoryPublic (id, title, ispublished, versions), StoryNodePublic (storyversion, isstartnode), NodeChoicePublic (requiresstate/setsstate). **Services**: StoriesService (CRUD/publish/new-version), StorynodesService (nodes/choices-from-node), NodeChoicesService. Follow FrontendRULES.md for patterns, ComponentDevelopmentWalkthrough.md for decisions.[^5][^2]


[^1]: Story-Author-Reference-Guide.md

[^2]:StoryAuthoringGuideV2.md

[^3]:Story-Authoring-Guide.md

[^4]: Frontend-Tech-Spec.MD

[^5]: FrontendRULES.md

[^6]: ComponentDevelopmentWalkthrough.md


