GOAL
"Composable, guided DemoBuilder authoring with reusable editor components and schema-driven validation."

PROOF
- Reusable editor components are extracted and wired.
- Builder schema owns active kinds, defaults, field metadata, and semantic validators.
- Unit tests cover normalization, semantic guardrails, field-spec wiring, and theme round-trip behavior.

## Current Status (2026-02-23)

### Completed
1. Route decomposition is complete:
- `DemoTopLevelEditor`
- `DemoValidationPanel`
- `DemoPanelEditor`
- `DemoBlockEditor`
- `DemoRawJsonEditor`
- `DemoSaveBar`

2. Core schema layer is active in `demoBuilderSchema.ts`:
- active panel/block kinds
- canonical defaults + normalization
- schema v2 field-spec descriptors for composition/panel/block fields
- A/B/C template constructors (`composition_a_baseline`, `composition_b_runtime_coupled`, `composition_c_visibility_semantics`)
- semantic validation rules

3. Builder route behavior is production-usable:
- select/create demo
- load/edit/save composition
- raw JSON power mode
- semantic preflight blocking on error-level issues
- template picker + apply-to-editor flow wired from schema templates
- post-apply template setup checklist with skip/resume flow
- unresolved-item deep links + resolved "Template setup complete" banner
- checklist state persisted in `metadata_json.template_setup` across save/reload cycles
- in-context dependency pickers for unresolved assumptions (story/persona dialogs in builder)

4. Test baseline is active:
- `frontend/tests-unit/demo-builder-schema.spec.ts`
- `frontend/tests-unit/demo-builder-editors-theme.spec.tsx`
- `frontend/tests-unit/demo-template-setup-checklist.spec.tsx`
- `frontend/tests-unit/demo-builder-capability-registry.spec.ts`

### Partially Complete
1. Descriptor-driven editor rendering is complete for top-level/panel/block controls (enum/text/id/number/json), but richer specialized controls (`boolean`, advanced structured editors) are still plain inputs/JSON editors.
2. Capability registry foundation is active (composition/panel/block descriptors + add-control wiring + availability predicates + runtime compatibility drift helper), and hook APIs are now wired into panel/block update + validation flows. Runtime-coupled hooks are implemented for `storyMetadata`, `orchestratorState`, `contributionFeed`, and `toolCapability` (config normalization + capability-local warnings). A deterministic registry composition API (`buildCapabilityRegistry`) is now in place with pack ordering (`order`, then `id`) and conflict policies (`keep_existing`, `replace_existing`, `error`), and default builder bootstrap now supports feature-flagged pack activation (`VITE_DEMO_BUILDER_PACKS`, with legacy compatibility for `VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK`). Requirement-level compatibility checks are also active (`getBuilderRequirementCompatibilityGaps`) to catch requirement drift versus core capability expectations.

### Not Started
1. Embedded live preview pane in builder (keeping external preview link).

## Updated Sequencing (Priority)

1. **P1 Capability Registry Layer**
- Add capability descriptor extension points (`editorComponent`, `semanticValidator`, `normalize`, `requires`) while keeping persisted contract unchanged.
- Registry composition/merge rules for core + plugin capability packs are implemented (`buildCapabilityRegistry` + conflict policies + deterministic ordering).
- Keep runtime `rendererRegistry.tsx` separate and expand cross-check tests from kind-level to capability-level requirement compatibility.

2. **P1 Guided Template UX (Third Pass)**
- DEFERRED BY PRODUCT: Add checklist analytics hooks for UX/product validation of drop-off points.
- Add richer story/persona picker affordances (filter facets, recent selections, and creation shortcuts).

## Guided Template UX (Second Pass): Post-Apply Prompt Design

Goal: after a user applies template A/B/C, immediately collect the minimum runtime/story assumptions needed for valid execution, without forcing raw JSON edits.

### Prompt Trigger
1. Trigger immediately after `Apply Template To Editor`.
2. Show a compact "Template Setup Checklist" card at top of builder.
3. Allow "Skip for now" but keep unresolved items visible as warnings.

### Prompt Inputs (Initial Scope)
1. `story_id` (required for templates that include story-dependent panels/blocks).
2. `runtime_policy` confirmation (`auto` / `manual` / `owner_only`) with contextual help.
3. `persona_policy` confirmation with optional `fixed_user_persona_id` when needed.
4. Optional `chat_mode` confirmation for observer/multiplayer flows.

### Template-Specific Checklist
1. Composition A:
- Require `metadata_json.story_id`.
- Confirm runtime/chat defaults are acceptable.
2. Composition B:
- Require `metadata_json.story_id`.
- Confirm runtime-coupled block intent (`storyMetadata`, `orchestratorState`, `contributionFeed`).
3. Composition C:
- Require `metadata_json.story_id`.
- Confirm visibility semantics expectations (`visible`, `hidden_mounted`, `hidden_unmounted`).

### UX/Validation Behavior
1. Checklist items map to semantic validator codes and specific composition paths.
2. "Save" remains blocked only by error-level semantic issues; warnings remain non-blocking but visible.
3. When checklist becomes fully resolved, show "Template setup complete" status.
4. Keep all changes contract-safe by writing only to canonical composition fields.

### Implementation Notes
1. Add template descriptor metadata in schema layer:
- `requiredAssumptions`
- `suggestedDefaults`
- `checklistItems` (id, label, severity, resolver path)
2. Add a small reusable component (proposed: `DemoTemplateSetupChecklist`) near `DemoTopLevelEditor`.
3. Reuse existing `validateCompositionSemantics` output; add thin mapping helper from issue codes to checklist rows.
4. Keep checklist state derived from composition + template id (no duplicate persisted builder state).

### Acceptance Criteria
1. After template apply, users see exactly which assumptions still need input.
2. Users can satisfy checklist items through guided controls (no JSON-only dependency).
3. Checklist resolution and semantic validation stay in sync.
4. Template A/B/C can be brought to "ready to save" using only guided UI controls.
5. Unresolved assumptions expose deep links that jump users directly to the corresponding checklist controls.
6. Completed setups show a clear success-state banner.
7. Checklist progress persists in `metadata_json.template_setup` and restores after reload.

3. **P1 Embedded Preview**
- Add in-builder preview panel powered by current DemoShell runtime path.
- Preserve open-in-new-tab preview link.

4. **P1 Test Matrix Expansion**
- Add tests for template instantiation and semantic expectations per template profile.
- Add editor/raw JSON parity checks for stable round-trip edits.
- Add targeted tests for capability-registry-driven controls and availability predicates in editor add-controls.

## Recommended Next Slice (P1, low churn / high value)

1. **Capability Descriptor vNext (core refactor, no UX breakage)**
- Extend capability types to support optional hooks:
  - `editorComponent`
  - `normalizeCompositionPatch`
  - `semanticValidators`
  - richer `requirements` metadata
- Keep existing built-in behavior as defaults so current editors remain stable.

2. **Registry Composition Layer (core + plugin packs)**
- Implemented:
  - deterministic registry builder (`buildCapabilityRegistry`) for core + optional packs
  - duplicate-key conflict handling with configurable policies
  - deterministic pack ordering (`order`, then `id`)
- Next:
  - externalize plugin pack registration so non-core packs can be injected intentionally per environment/workstream

3. **Capability-Level Compatibility Checks**
- Implemented:
  - requirement metadata drift checks via `getBuilderRequirementCompatibilityGaps(...)`
  - registry-aware runtime kind drift checks (`getBuilderRuntimeCompatibilityGaps(registry?)`)
  - runtime-coupled renderer expectation checks (`getBuilderRuntimeExpectationGaps(registry?)`)
  - plugin safety checks for unsupported controls + requirement escalation/relaxation (`getBuilderCapabilitySafetyGaps(registry?)`)
- Next:
  - route-level preflight integration for pack validation errors/warnings (display in validation panel)
  - plugin capability safety constraints for renderer-specific unsupported patterns

4. **Plugin Spike (single internal example pack)**
- Implemented:
  - internal plugin pack with one panel capability extension (`participantPanel`)
  - internal plugin pack with one block capability extension (`toolCapability`)
  - local flag gate for bootstrap (`VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK`)
  - pack-id activation path (`VITE_DEMO_BUILDER_PACKS`) and registration inventory APIs
- Next:
  - publish connector-facing pack authoring templates/examples beyond internal spike

5. **Then move to Embedded Preview**
- Once registry extension points stabilize, add in-builder preview integration to avoid rework on preview/editor coupling.

## Runtime-Coupled Hook Rollout Status

1. **`storyMetadata`**: complete
- normalize hook for config defaults/sanitization.
- validator warning for debug config visibility.
- unit coverage in capability registry suite.

2. **`orchestratorState`**: complete
- normalize hook for config defaults (`show_agent_list`, `only_active_agents`, `show_config_json`).
- validator warning when orchestration agent list is hidden.
- unit coverage in capability registry suite.

3. **`contributionFeed`**: complete
- normalize hook for `max_items` + visibility toggles.
- validator warnings for permissive settings (`include_internal`, large feed window).
- unit coverage in capability registry suite.

4. **`toolCapability`**: complete
- normalize hook for config shape and capability-map sanitization.
- validator warning for invalid capability mapping normalization.
- unit coverage in capability registry suite.

5. **Cross-capability consistency pass**: next
- Ensure all runtime-coupled hooks emit consistent issue codes/messages/severity.
- Verify save gating remains unchanged (error-level only), with warnings visible in semantic panel.
- Add formatter/i18n pass for warning copy once capability registry composition layer is in place.

## Architecture Reminder

Two-layer model remains the target:
1. Backend/OpenAPI contract remains canonical persisted payload.
2. Builder schema wraps that contract with guided authoring metadata and transforms.

Runtime and authoring registries remain separate concerns:
- `rendererRegistry.tsx`: runtime rendering.
- builder schema/registry: editor behavior + validation.

## Notes
- This file supersedes older "TO BE BUILT" extraction notes for route decomposition.
- Active implementation details are tracked in:
  - `frontend/src/components/Demo/demo-docs/active-implementation-history.md`
