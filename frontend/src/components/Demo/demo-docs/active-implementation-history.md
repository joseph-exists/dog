This is a history of builder-implementation with most recent first.

**added runtime-expectation and plugin-safety compatibility analyzers**

### What changed

- Added runtime-coupled expectation compatibility checks:
  - `getBuilderRuntimeExpectationGaps(registry?)`
  - verifies runtime-coupled block capabilities keep required hooks and expected requirement metadata
  - file:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Added plugin safety analyzer:
  - `getBuilderCapabilitySafetyGaps(registry?)`
  - flags unsupported composition controls and requirement escalation/relaxation patterns
  - file:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Expanded unit tests:
  - runtime expectation no-gap baseline
  - missing hook detection on runtime-coupled overrides
  - unsupported control detection
  - requirement escalation/relaxation safety behavior
  - file:
    - `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

- Updated pack registration reference card with safety/compatibility gates:
  - `frontend/src/components/Demo/demo-docs/demo-testing-references/demo-builder-pack-registration-reference-card.md`

### Validation

- `cd frontend && npm run test:unit -- demo-builder-capability-registry.spec.ts` passed (`26` tests)
- `cd frontend && npm run build` passed

**added explicit pack-id registration surface + engineer reference card**

### What changed

- Extended pack activation model to support explicit pack-id selection:
  - `resolveBuilderCapabilityPacks(...)`
  - `VITE_DEMO_BUILDER_PACKS` (comma-separated ids)
  - legacy compatibility with `VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK`
  - files:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Added pack registration inventory APIs:
  - `BUILDER_CAPABILITY_PACK_REGISTRATIONS`
  - `getBuilderCapabilityPackRegistrationInventory()`

- Added targeted tests for registration/resolution behavior:
  - inventory coverage
  - explicit id resolution + unknown-id reporting
  - env-driven resolution + legacy flag compatibility
  - file:
    - `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

- Added engineer-facing reference card:
  - `frontend/src/components/Demo/demo-docs/demo-testing-references/demo-builder-pack-registration-reference-card.md`

### Validation

- `cd frontend && npm run test:unit -- demo-builder-capability-registry.spec.ts` passed (`22` tests)
- `cd frontend && npm run build` passed

**wired first internal plugin pack behind local flag + added requirement-level compatibility checks**

### What changed

- Added local feature-flagged internal plugin pack wiring in builder registry bootstrap:
  - flag: `VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK`
  - default registry now composes with `conflictPolicy: "replace_existing"` and optional internal pack
  - internal pack currently overrides:
    - panel capability: `participantPanel` (plugin display/editor identifier)
    - block capability: `toolCapability` (plugin display/editor identifier + additional warning validator)
  - file:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Added capability-level requirement compatibility checks:
  - `getBuilderRequirementCompatibilityGaps(registry?)`
  - compares active registry requirements against core baseline requirements
  - reports per-field mismatches (`requiresStory`, `requiresRuntime`, `requiresPersona`)
  - file:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Expanded compatibility test coverage:
  - requirement compatibility no-op for default registry
  - mismatch detection for overridden requirement metadata
  - plugin-style override pack composition behavior
  - file:
    - `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

### Validation

- `cd frontend && npm run test:unit -- demo-builder-capability-registry.spec.ts` passed (`19` tests)
- `cd frontend && npm run build` passed

**implemented capability registry composition API (step 2)**

### What changed

- Added deterministic capability registry builder:
  - `buildCapabilityRegistry(options)`
  - supports optional core inclusion, plugin pack inputs, and deterministic pack order (`order`, then `id`)
  - file: `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Added conflict handling policies for duplicate keys:
  - `keep_existing` (default)
  - `replace_existing`
  - `error` (throws on collision)
  - conflict metadata is exposed in `registry.conflicts` and snapshot output

- Rewired default exports to use composed registry output:
  - `BUILDER_COMPOSITION_CAPABILITIES`
  - `BUILDER_PANEL_CAPABILITIES`
  - `BUILDER_BLOCK_CAPABILITIES`

- Added targeted unit tests for composition API behavior:
  - deterministic order assertions
  - default collision behavior assertions
  - replace/throw policy assertions
  - file: `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

### Validation

- `cd frontend && npm run test:unit -- demo-builder-capability-registry.spec.ts` passed (`16` tests)
- `cd frontend && npm run build` passed

**expanded runtime-coupled capability hooks for orchestrator/feed/tool blocks**

### What changed

- Extended block hook implementations in `demoBuilderCapabilityRegistry.ts`:
  - `orchestratorState`: normalize config defaults (`show_agent_list`, `only_active_agents`, `show_config_json`) and warn when agent list is hidden.
  - `contributionFeed`: normalize `max_items`/toggle defaults and warn on permissive settings (`include_internal`, large windows).
  - `toolCapability`: normalize config shape (including `capability_map` sanitization) and warn on invalid mapping input.
  - File:
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`

- Added targeted unit coverage for these three hook implementations:
  - `orchestratorState` normalization + warning behavior.
  - `contributionFeed` normalization + permissive warning behavior.
  - `toolCapability` mapping normalization + invalid mapping warning behavior.
  - File:
    - `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

- Updated workflow status to mark runtime-coupled hook rollout complete for:
  - `storyMetadata`
  - `orchestratorState`
  - `contributionFeed`
  - `toolCapability`
  - File:
    - `frontend/src/components/Demo/demo-docs/demo-builder-workflow.md`

### Validation

- `cd frontend && npm run test:unit -- demo-builder-capability-registry.spec.ts` passed (`12` tests)
- `cd frontend && npm run build` passed

**replaced checklist links with in-context pickers + started capability-registry compatibility checks**

### What changed

- Replaced checklist dependency links with in-context picker actions:
  - `Pick Story` opens a dialog backed by `StoriesService.readStories`.
  - `Pick Persona` opens a dialog backed by `PersonasService.readPersonas`.
  - Story selection writes `metadata_json.story_id`.
  - Persona selection writes `persona_policy=fixed_user_persona` and `fixed_user_persona_id`.
  - Files:
    - `frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx`
    - `frontend/src/routes/_layout/demo-builder.tsx`

- Added a first capability-registry compatibility guard:
  - Introduced shared runtime capability constants in `demoRuntimeCapabilities.ts`.
  - Added `getBuilderRuntimeCompatibilityGaps()` to detect builder/runtime drift for panel and block kinds.
  - Added compatibility coverage in unit tests.
  - Files:
    - `frontend/src/components/Demo/demoRuntimeCapabilities.ts`
    - `frontend/src/components/Demo/builder/demoBuilderCapabilityRegistry.ts`
    - `frontend/src/components/Demo/rendererRegistry.tsx`
    - `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

### Validation

- `cd frontend && npm run test:unit` passed
- `cd frontend && npm run build` passed

**persisted template setup state + added unresolved dependency quick actions**

### What changed

- Persisted checklist state in `metadata_json.template_setup`:
  - Added schema helpers:
    - `getTemplateSetupState`
    - `withTemplateSetupState`
  - Route now reads/writes checklist template id, dismissed state, and confirmations from persisted composition metadata.
  - Files:
    - `frontend/src/components/Demo/builder/demoBuilderSchema.ts:586`
    - `frontend/src/routes/_layout/demo-builder.tsx:127`

- Added unresolved dependency quick actions in checklist:
  - `story_id` assumptions link to `/stories`
  - persona-related assumptions link to `/personas`
  - File: `frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx:32`

- Added/expanded tests:
  - metadata persistence round-trip and clear behavior for `template_setup`
    - `frontend/tests-unit/demo-builder-schema.spec.ts:240`
  - checklist quick-action link coverage
    - `frontend/tests-unit/demo-template-setup-checklist.spec.tsx:38`

### Validation

- `cd frontend && npm run test:unit` passed (`65` tests)
- `cd frontend && npm run build` passed

**added template setup complete banner + unresolved deep links**

### What changed

- Enhanced `DemoTemplateSetupChecklist` UX:
  - Added success-state banner when all checklist items resolve.
  - Added unresolved-item deep links (`#template-checklist-item-*`) so users can jump directly to pending controls.
  - File: `frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx:63`

- Added targeted component tests:
  - unresolved-state deep links render for pending items
  - success banner renders when checklist resolves fully
  - File: `frontend/tests-unit/demo-template-setup-checklist.spec.tsx:1`

### Validation

- `cd frontend && npm run test:unit` passed
- `cd frontend && npm run build` passed

**implemented guided template UX second pass (post-apply assumptions checklist)**

### What changed

- Added template schema descriptors for guided checklist metadata:
  - `BUILDER_COMPOSITION_TEMPLATE_SCHEMAS`
  - `requiredAssumptions`
  - `checklistItems`
  - File: `frontend/src/components/Demo/builder/demoBuilderSchema.ts:330`

- Added checklist status resolver + helpers:
  - `getBuilderCompositionTemplateSchema`
  - `getBuilderCompositionFieldSpec`
  - `getCompositionStoryId`
  - `resolveTemplateChecklistStatus`
  - File: `frontend/src/components/Demo/builder/demoBuilderSchema.ts:548`

- Added reusable checklist component:
  - `DemoTemplateSetupChecklist`
  - Includes story-id prompt, runtime/persona/chat confirmation controls, fixed persona id prompt, skip/resume flow, and resolved/pending status badges.
  - File: `frontend/src/components/Demo/builder/DemoTemplateSetupChecklist.tsx:1`

- Wired checklist into route after template apply:
  - Tracks `activeTemplateSetupId`, dismissal state, and assumption confirmations.
  - Template apply now activates setup checklist for the applied template.
  - File: `frontend/src/routes/_layout/demo-builder.tsx:90`

- Added schema-level tests for checklist behavior:
  - story_id pending/resolved
  - runtime/persona confirmation gating
  - fixed persona id conditional requirement
  - template checklist metadata exposure
  - File: `frontend/tests-unit/demo-builder-schema.spec.ts:156`

### Validation

- `cd frontend && npm run test:unit` passed (`61` tests)
- `cd frontend && npm run build` passed

**replace the remaining hardcoded text/json field rendering with field-spec-driven rendering helpers (same pattern), then add targeted tests for theme field round-trip behavior in the builder UI layer.**

### What changed

- `DemoTopLevelEditor`
  - Enum options now come from field specs.
  - Theme labels/placeholders come from field specs.
  - JSON field rendering for `metadata_json` and `presentation_json` now uses a shared helper (`renderCompositionJsonField`) with schema label lookup.
  - File: `frontend/src/components/Demo/builder/DemoTopLevelEditor.tsx:27`

- `DemoPanelEditor`
  - Added helper `getPanelFieldLabel(...)` driven by panel kind schema.
  - Replaced hardcoded placeholders for `id`, `title`, `order`, and options label with schema-driven labels.
  - File: `frontend/src/components/Demo/builder/DemoPanelEditor.tsx:36`

- `DemoBlockEditor`
  - Added helper `getBlockFieldLabel(...)` driven by block type schema.
  - Replaced hardcoded placeholders for `id`, `title`, `order`, and JSON labels (`config_json`, `content_json`, `presentation_json`) with schema-driven labels.
  - File: `frontend/src/components/Demo/builder/DemoBlockEditor.tsx:36`

- Added targeted UI-layer tests for theme round-trip behavior:
  - `frontend/tests-unit/demo-builder-editors-theme.spec.tsx:1`
  - Covers:
    - top-level `page_theme_id`/`cards_theme_id` callbacks (`""`/whitespace -> `null`)
    - panel `theme_id` patch behavior
    - block `theme_id` patch behavior

### Validation

- `cd frontend && npm run build` passed
- `cd frontend && npm run test:unit` passed (`53` tests)


**Implemented the first dynamic-spec wiring pass for all three editors, focused on enum controls + theme fields.**

What changed:

- `DemoTopLevelEditor` now reads enum options from `BUILDER_COMPOSITION_FIELD_SPECS` and adds schema-driven theme inputs:
  - `layout_mode`, `runtime_policy`, `persona_policy`, `chat_mode` enum options sourced dynamically
  - `page_theme_id` + `cards_theme_id` inputs added
  - File: `frontend/src/components/Demo/builder/DemoTopLevelEditor.tsx:7`

- `DemoPanelEditor` now reads enum options from per-kind schema and includes panel `theme_id` editing:
  - `prominence` + `viewport_mode` option lists pulled from `getBuilderPanelKindSchema(...)`
  - add-panel button labels now use schema `displayName`
  - `theme_id` input added per panel
  - File: `frontend/src/components/Demo/builder/DemoPanelEditor.tsx:1`

- `DemoBlockEditor` now reads enum options from per-type schema and includes block `theme_id` editing:
  - `region` + `visibility` option lists pulled from `getBuilderBlockTypeSchema(...)`
  - add-block button labels now use schema `displayName`
  - `theme_id` input added per block
  - File: `frontend/src/components/Demo/builder/DemoBlockEditor.tsx:1`

- Route wiring updated for top-level theme fields:
  - added `onPageThemeIdChange` and `onCardsThemeIdChange` handlers
  - File: `frontend/src/routes/_layout/demo-builder.tsx:367`

Validation:

- `cd frontend && npm run build` passed
- `cd frontend && npm run test:unit` passed (50/50)

Next good step: 


**doc alignment patch + schema v2 field-spec layer kickoff**

Docs:
- Updated `frontend/src/components/Demo/demo-docs/demo-builder-workflow.md` to:
  - mark route decomposition + core schema/validation as complete
  - replace stale "TO BE BUILT" extraction checklist with prioritized next targets
  - set sequencing around P0.1 schema v2 -> P0.2 A/B/C templates -> capability registry -> embedded preview

Schema v2 (initial implementation):
- Expanded `frontend/src/components/Demo/builder/demoBuilderSchema.ts` with:
  - `BUILDER_COMPOSITION_FIELD_SPECS`
  - `BUILDER_PANEL_KIND_SCHEMAS`
  - `BUILDER_BLOCK_TYPE_SCHEMAS`
  - `getBuilderPanelKindSchema` / `getBuilderBlockTypeSchema`
  - schema-derived dependency sets used by semantic validation
- Updated template creators to consume schema defaults from the v2 descriptors.

Tests:
- Expanded `frontend/tests-unit/demo-builder-schema.spec.ts` with coverage for:
  - composition theme field specs
  - panel kind schema coverage + `theme_id` metadata
  - block type schema coverage + `theme_id` metadata

**extract the raw JSON editor + sticky save bar into a final reusable pair to finish route decomposition.**

Added:
- `frontend/src/components/Demo/builder/DemoRawJsonEditor.tsx:1`
- `frontend/src/components/Demo/builder/DemoSaveBar.tsx:1`

Updated:
- `frontend/src/routes/_layout/demo-builder.tsx:23`
- Replaced inline raw JSON card + sticky save footer with component usage at `frontend/src/routes/_layout/demo-builder.tsx:432`

Behavior remains the same:
- Raw JSON draft editing/reset/apply flow unchanged.
- Save bar still reflects selected demo, dirty state, save pending state, and semantic blocking rules.

Validation:
- `cd frontend && npm run build` passed
- `cd frontend && npm run test:unit` passed (47/47)


**extract the next pair DemoPanelEditor and DemoBlockEditor**
- I’m extracting the Panels and Blocks cards into reusable builder components now, keeping behavior stable and only changing composition of the route. After wiring, I’ll run build + unit tests again.
- I’m removing the inline Panels/Blocks JSX and wiring DemoPanelEditor/DemoBlockEditor with the existing callbacks so state flow stays identical.


Changed files:
- Added `frontend/src/components/Demo/builder/DemoPanelEditor.tsx:1`
- Added `frontend/src/components/Demo/builder/DemoBlockEditor.tsx:1`
- Updated `frontend/src/routes/_layout/demo-builder.tsx:21`
- Replaced inline sections with component usage at `frontend/src/routes/_layout/demo-builder.tsx:397`

What moved:
- `Panels` editor UI, add/remove/update handlers, and panel `options` JSON field binding into `DemoPanelEditor`.
- `Blocks` editor UI, add/remove/update handlers, and block `config/content/presentation` JSON field bindings into `DemoBlockEditor`.



**Extracted and wired DemoTopLevelEditor and DemoValidationPanel with no behavior change:**

- Added `DemoTopLevelEditor` at `frontend/src/components/Demo/builder/DemoTopLevelEditor.tsx:1`
- Added `DemoValidationPanel` at `frontend/src/components/Demo/builder/DemoValidationPanel.tsx:1`
- Updated route to consume them in `frontend/src/routes/_layout/demo-builder.tsx:28` and `frontend/src/routes/_layout/demo-builder.tsx:383`

What moved out of the route:
- Top-level composition controls (`layout_mode`, `runtime_policy`, `persona_policy`, `chat_mode`)
- Top-level JSON fields (`metadata_json`, `presentation_json`)
- Semantic validation issue rendering



 **central schema + semantic validation extraction**.

**Implemented**
1. Added a dedicated builder schema layer:
- `frontend/src/components/Demo/builder/demoBuilderSchema.ts:1`
- Includes:
  - active kinds/types (`ACTIVE_BUILDER_PANEL_KINDS`, `ACTIVE_BUILDER_BLOCK_TYPES`) at `frontend/src/components/Demo/builder/demoBuilderSchema.ts:34`
  - canonical defaults (`createEmptyComposition`) at `frontend/src/components/Demo/builder/demoBuilderSchema.ts:94`
  - normalization (`normalizeComposition`) at `frontend/src/components/Demo/builder/demoBuilderSchema.ts:109`
  - template builders (`createPanelTemplate`, `createBlockTemplate`)
  - semantic validator + issue model (`BuilderValidationIssue`, `validateCompositionSemantics`) at `frontend/src/components/Demo/builder/demoBuilderSchema.ts:157` and `frontend/src/components/Demo/builder/demoBuilderSchema.ts:181`

2. Wired route to consume schema/validators:
- `frontend/src/routes/_layout/demo-builder.tsx:14`
- Route now:
  - imports schema constants/helpers
  - computes semantic issues (`validateCompositionSemantics`) at `frontend/src/routes/_layout/demo-builder.tsx:131`
  - blocks save when error-level issues exist at `frontend/src/routes/_layout/demo-builder.tsx:167`
  - shows a “Semantic Validation” UI section at `frontend/src/routes/_layout/demo-builder.tsx:507`
  - uses schema-backed kind/type lists in panel/block add/edit controls at `frontend/src/routes/_layout/demo-builder.tsx:542` and `frontend/src/routes/_layout/demo-builder.tsx:666`

3. Added targeted unit tests for schema behavior:
- `frontend/tests-unit/demo-builder-schema.spec.ts:1`
- Covers:
  - defaults
  - normalization behavior
  - story_id dependency rules
  - single page-viewport constraint
  - content payload presence warnings


**Why this slice is valuable**
- It establishes the stable authoring contract for future component extraction.
- It reduces route-level logic drift and prepares for A/B/C templates + capability registry.
- It gives immediate guardrails for integrated room/story demos and content-curation semantics.
