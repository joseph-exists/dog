# Prompt Builder RFC (Phase 1)
> **Status:** Active implementation snapshot (Phase M1 in progress)  
> **Date:** 2026-02-24  
> **Scope:** Prompt Builder domain-first design that later feeds a shared Builder Platform extraction.

## Linked Follow-up
1. Phase M1 contract skeleton + mapping spec:
- `docs/plans/2026-02-24-prompt-builder-m1-contract-and-mapping.md`

## Current Implementation Status (2026-02-24)
### Completed
1. M1 schema foundation is implemented:
- `frontend/src/components/Prompt/builder/promptBuilderSchema.ts`
- includes defaults, field specs, normalization helpers, and semantic validator stubs.
2. Mapping/hydration adapter layer is implemented:
- `frontend/src/components/Prompt/builder/promptBuilderAdapters.ts`
- includes `mapUserAgentConfigToPromptDraft(...)`, `hydratePromptDraftProviderAndModel(...)`, `buildPromptValidationContext(...)`.
3. Capability registry foundation is implemented:
- `frontend/src/components/Prompt/builder/promptBuilderCapabilityRegistry.ts`
- includes descriptor model, normalization hooks, and capability-level semantic validators.
4. Bootstrap route is implemented for day-one editing:
- `frontend/src/routes/_layout/prompt-builder.tsx`
- top-level editor + data-backed provider/model controls + semantic validation panel.
5. Baseline test coverage is implemented:
- `frontend/tests-unit/prompt-builder-schema.spec.ts`
- `frontend/tests-unit/prompt-builder-adapters.spec.ts`
- `frontend/tests-unit/prompt-builder-capability-registry.spec.ts`
- `frontend/tests-unit/prompt-top-level-editor.spec.tsx`

### Partially Complete
1. Bootstrap editor route scope:
- completed: top-level provider/model/input/params sections, semantic validation panel, raw JSON fallback editor, sticky action bar, and `PromptConfigsService` persistence wiring (working-copy + commit endpoints).
- remaining: version history UX depth (compare/restore) and expanded failure-state ergonomics.
2. Version/history flow:
- contract direction is defined; commit/list flows are wired, with compare/restore UX still pending.
3. Backend integration test depth:
- owner access + version commit + working-copy `409` conflict paths are covered.
- broader endpoint matrix (reset/validate negative cases, cross-user list filters) still pending.

### Next Priorities
1. Finish bootstrap UX parity:
- polish raw JSON fallback and sticky action bar UX in `/prompt-builder` (deep links, pending states, and API-bound action wiring).
2. Wire persistence + version APIs:
- continue hardening PromptConfig save/load/commit/reset flows (richer version UX, restore compare workflows, and reset-path hardening tests).
3. Add provider/model-aware advanced parameter controls:
- keep descriptor-driven controls and preserve forward-compat pass-through behavior.

## Implementation References (Current)
1. Prompt builder user reference card:
- `frontend/src/components/Prompt/prompt-docs/prompt-builder-user-expectations-reference-card.md`
2. Prompt-config backend route coverage:
- `backend/app/tests/api/routes/test_prompt_configs.py`

### Concurrency Buckets (Immediate Execution Plan)
1. Bucket A: route-level UX completion (frontend-only, low dependency)
- owner scope: `frontend/src/routes/_layout/prompt-builder.tsx` + local UI helpers
- tasks: finalize JSON fallback ergonomics, dirty-state polish, save/commit pending states, field-to-error deep links.
- dependency: none (can run now).

2. Bucket B: persistence/version integration (frontend + backend contract dependency)
- owner scope: prompt config endpoints, DTO finalization, save/load/commit/reset route wiring.
- tasks: replace local save/commit placeholders with API-backed actions and optimistic/react-query invalidation.
- dependency: endpoint + DTO naming decision.

3. Bucket C: capability depth (frontend schema/registry, parallelizable with B)
- owner scope: `promptBuilderSchema.ts`, `promptBuilderCapabilityRegistry.ts`, provider/model metadata adapters.
- tasks: provider-specific param controls, capability-level compatibility guards, richer semantic issue taxonomy.
- dependency: partial provider/model metadata clarity (can start with stubs now).

4. Suggested sequencing for minimal churn:
- step 1: complete Bucket A polish and test coverage first.
- step 2: execute Bucket B and C concurrently once endpoint names are fixed.
- step 3: perform one stabilization pass across A/B/C with full save/commit UX and regression tests.

## 1. Why This RFC
Prompt Builder is intentionally broader than "prompt text editing." It must support:
1. minimal authoring (`question` or base prompt only)
2. provider/model selection
3. model-specific parameter tuning
4. version/history workflows
5. reusable kits/templates

This RFC proposes Prompt Builder as the second builder type (after Demo Builder) to validate cross-domain patterns before finalizing the shared Builder Platform.

## 2. Decision: Domain-First, Then Platform
We will not build the full Builder Platform first.  
We will implement Prompt Builder with the same architectural pattern as Demo Builder, then extract only proven common primitives.

Rationale:
1. reduces premature abstraction risk
2. captures text/version-centric requirements that Demo Builder does not prioritize
3. improves odds of shared abstractions that serve both UX-heavy and text/config-heavy builders

## 3. Product Goals
1. Let builder users author prompts from minimal to advanced.
2. Keep provider/model parameter tuning guided and safe.
3. Make versioning/history first-class (draft, commit, compare, rollback).
4. Preserve contract correctness when switching providers/models.
5. Produce reusable prompt kits for downstream flows (Agent/Environment/Experiment builders).

## 4. Non-Goals (Phase 1)
1. Full multi-agent orchestration builder.
2. Full experiment matrix runner.
3. Universal plugin marketplace.
4. Backend contract redesign beyond required Prompt Builder API surface.

## 5. Contract Model (Canonical vs Builder Schema)
### 5.1 Canonical persisted contract (backend-owned)
Define a stable persisted object (name illustrative):
1. `PromptConfig_Input`
2. `provider` (enum/string id)
3. `model` (string id)
4. `input` payload (minimal prompt/messages/system instructions as supported by model family)
5. `parameters` (provider/model-specific config)
6. `metadata` (tags, ownership, notes, template/setup state)

### 5.2 Builder wrapper schema (frontend-owned)
Define `promptBuilderSchema.ts`:
1. active capabilities
2. defaults and constructors
3. field specs (labels/help/control metadata)
4. semantic validators
5. patch normalizers
6. template constructors

Persisted contract shape does not change for builder UX features.

## 6. Capability + Type Design
Use discriminated unions for provider/model parameter sets.

### 6.1 Core discriminators
1. `provider`
2. `model_family` (optional but useful for shared controls)
3. `model`

### 6.2 Parameter union model
1. Common parameter subset:
- `temperature`
- `max_output_tokens`
- `top_p`
- `stop`
- `seed` (if supported)

2. Provider/model-specific extension:
- reasoning controls
- response format controls (json/schema/tool-call settings)
- safety/policy toggles
- modality settings

3. Unknown/forward-compat bucket:
- allow pass-through map for unsupported-yet-valid fields (advanced mode)

### 6.3 Capability examples (builder-facing)
1. `basePrompt`
2. `systemInstructions`
3. `messageTemplate`
4. `providerSelection`
5. `modelSelection`
6. `samplingControls`
7. `structuredOutputControls`
8. `toolCallControls`
9. `safetyPolicyControls`
10. `versionMetadata`

## 7. Versioning + History Requirements
Version/history is first-class for Prompt Builder.

### 7.1 Required behaviors
1. Draft vs committed version states.
2. Immutable committed snapshots.
3. Diff/compare between versions.
4. Restore/branch-from behavior.
5. Change reason/comment metadata.

### 7.2 Suggested minimal model
1. `prompt_config` (logical object id)
2. `prompt_config_version` (immutable snapshots)
3. `working_copy` (draft state)
4. optional `parent_version_id` for branching lineage

### 7.3 Builder UX expectations
1. visible "dirty draft" state
2. commit action with summary
3. compare current draft to selected prior version
4. quick rollback to prior committed snapshot

## 8. Validation Model
Two-level validation:
1. structural validation (schema/type)
2. semantic validation (cross-field/domain constraints)

### 8.1 Example semantic rules
1. provider/model must be compatible.
2. disallow unsupported parameters for chosen model.
3. enforce required base input presence.
4. enforce parameter ranges and cross-field constraints.
5. warning-level issues for risky settings (for example extreme token/sampling combos).

### 8.2 Save gating
1. block save on error-level semantic issues
2. allow warnings with explicit visibility

## 9. Template + Setup Workflow
Reuse Demo pattern:
1. template constructors (minimal/chat/structured-output/tool-enabled/etc.)
2. post-apply checklist for unresolved assumptions
3. persisted checklist state in metadata
4. deep links to unresolved controls

Prompt-specific setup examples:
1. provider credentials availability
2. model access entitlement
3. required schema for structured output
4. required tool bindings for tool-enabled templates

## 10. Editor Composition Pattern
Use the same decomposition pattern as Demo Builder:
1. top-level editor
2. capability editor sections
3. validation panel
4. raw JSON editor fallback
5. sticky save/version bar

Keep fields descriptor-driven, not hardcoded by capability type.

## 11. Compatibility + Registry Rules
Implement `promptBuilderCapabilityRegistry.ts` with:
1. deterministic core + pack composition
2. conflict policies (`keep_existing`, `replace_existing`, `error`)
3. requirement compatibility checks
4. safety analyzer checks

Use env-gated pack activation for local/experimental capabilities.

## 12. Extraction Plan To Builder Platform
After Prompt Builder v1 lands, extract common primitives used by both Demo + Prompt:
1. schema core primitives
2. capability registry core
3. setup checklist primitives
4. validation model + issue rendering primitives
5. pack composition + compatibility analyzer primitives

Do not extract domain-specific capabilities, validators, or templates into platform core.

## 13. Milestones
### M1: Prompt Builder RFC alignment + contract skeleton
1. finalize canonical `PromptConfig` contract direction with backend
2. define capability catalog and semantic rules

### M2: Prompt Builder schema + registry foundation
1. implement `promptBuilderSchema.ts`
2. implement `promptBuilderCapabilityRegistry.ts`
3. implement first template set + checklist workflow

### M3: Version/history MVP
1. draft/commit model
2. version list + compare view
3. rollback/branch-from path

### M4: Shared platform extraction pass
1. compare Demo + Prompt primitives
2. extract proven shared core modules
3. migrate both builders to shared core

## 14. Risks + Mitigations
1. Risk: provider/model churn creates brittle schema.
- Mitigation: discriminated union + forward-compat pass-through bucket.

2. Risk: overfitting to one provider.
- Mitigation: enforce provider-agnostic capability layer with provider-specific extensions.

3. Risk: versioning added late creates UX/data debt.
- Mitigation: include version model in M1/M2 boundary decisions.

4. Risk: premature platform extraction.
- Mitigation: extract only after Prompt + Demo parity review.

## 15. Open Questions
1. Should version commits be auto-generated on save or explicit user action?
2. Should model/provider capabilities be loaded statically, from API metadata, or hybrid?
3. What is the minimum compare UX needed in MVP (field diff vs full JSON diff)?
4. How should org policy constraints be injected (read-only constraints vs soft warnings)?
