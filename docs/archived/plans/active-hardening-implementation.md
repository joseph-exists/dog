# Demo Composition v2 Contract Hardening Plan

**Date:** 2026-02-22  
**Status:** Proposed implementation roadmap  
**Primary cross-reference:** `frontend/src/components/Demo/demo-docs/active-demo-integration-snapshot.md`
**Primary Engineering References** `backend/docs/DATA_MODEL_RULES.md` `backend/docs/RULES.md`


##  Overview & Philosophy

### Core Philosophy

- **Delight is the goal** - every interaction should feel satisfying, not just functional - for engineers, for operators, for admins, and for users. including agent users.
- **Progressive disclosure** - simple for casual users, powerful for power users - we learn and grow as we go.
- **Visible inheritance** - users always understand where their layout comes from - and engineers can understand where things go and come from too.  type hints, inline documentation, reference cards - be kind to those who follow you, and pay back the ones you follow.
- **Default to more** - invest in polish, micro-interactions, and thoughtful details.  add quotes from artists, philosophers, mathematicians, poets, gardeners - they are good for us. they help us be better builders by pulling us back to the real context - creating and making and doing and being.  

## Context

The active integration snapshot confirms that demos are now composition-native at route entry, with `ResolveDemoEntryPayload` and config composition CRUD in place. It also identifies remaining deltas in panel coverage, block coverage, and contract consistency across backend/frontend render paths.

This plan hardens the composition contract to support:
1. predictable API behavior via strict typed models
2. stable OpenAPI generation for frontend SDK/types/schemas
3. scalable renderer behavior for demos A/B/C/D
4. stronger engineering guardrails (validation, testability, backward compatibility)

## Intended Outcomes Alignment

This plan directly advances the outcomes listed in `active-demo-integration-snapshot.md`:
1. Keep demo routing composition-native and reduce recomposition drift.
2. Strengthen resolved payload contracts so frontend mapping is deterministic.
3. Support full panel/block composition for demos A/B/C/D.
4. Preserve creator flow (`create config`, `attach/patch composition`, `resolve session`) while increasing schema safety.
5. Improve code quality by reducing ad-hoc fallbacks and implicit behavior.

## In-Flight Legacy Policy

### Top-level policy
1. During this v2 hardening effort, we will not maintain or support legacy demo paths, legacy demos, or legacy demo creation methods.
2. Work that preserves dual-path legacy compatibility during implementation will be rejected.

### Required outcome
1. Existing demos must be reproducible via the new composition contracts at equal or better accuracy, correctness, and presentation quality. We can't cut scope.  Reproducibility of existing demos beyond implementation as defined in this document is not required context.
2. Success is measured by recreation fidelity on v2 contracts, not by continued operability of old paths.

### Explicit non-goals during migration
1. Keeping old route-level demo orchestration behavior alive in parallel.
2. Preserving deprecated payload contracts for in-flight convenience.
3. Building adapter layers whose primary purpose is long-lived legacy support.

## Problem Statement

Current composition models are solid but still mixed in strictness:
1. Panel specs include a generic fallback path (`DemoGenericPanelSpec`) that can hide schema drift.
2. Block specs are partially generic (`config_json`, `content_json`) without a discriminated union by block type.
3. Frontend panel/block renderer coverage is incomplete for some defined kinds.
4. OpenAPI/codegen is available, but contract evolution controls (versioning, compatibility checks, migration policy) are not formalized.

## Architectural Direction

Use a layered contract strategy:
1. **Persisted storage:** JSONB-backed panel/block payloads in SQLModel tables.
2. **API boundary validation:** strict discriminated unions in Pydantic v2 models.
3. **Runtime orchestration:** dependency resolution and DI in service/registry layer, not encoded as persisted executable graphs.
4. **Frontend consumption:** generated OpenAPI SDK/types/schemas as the default source, with renderer registries keyed by explicit `kind`/`type`.

This preserves flexibility while maximizing type safety and maintainability.

## Composition Guardrails (Nesting, Visibility, Stacking, Theming)

### Decision
The v2 contract must remain graph-capable. Flat `panels[]` and `blocks[]` editor views are projections, not the long-term canonical limit.

### Required capabilities
1. Nested composition:
- panels within panel containers
- blocks within block containers
- mixed panel/block container children
2. Visibility semantics:
- `visible`
- `hidden_unmounted` (not rendered)
- `hidden_mounted` (not visible but mounted; state/runtime preserved)
3. Container layout modes:
- `stack`
- `split`
- `tabs`
- `overlay`
4. Theme precedence consistency:
- composition-level page/cards defaults
- node-level overrides
- renderer/content-level overrides

### Non-negotiable contract principle
Do not encode runtime executable behavior in persisted composition nodes. Persist declarative intent; resolve behavior in runtime services/registries.

## Content Contract Alignment (Common/ContentRenderer)

### Decision
Content is a first-class object for both demo panels and demo blocks and must align with the shared `Common/ContentRenderer` contract used by node-driven surfaces.

Implementation timing note:
1. Full renderer wiring can be staged.
2. Contract alignment cannot be deferred; backend/frontend schemas must adopt the canonical content shape in this v2 hardening slice.

### Required alignment rules
1. Use one canonical `Content` schema at API boundary for both panel and block content payloads.
2. Do not split into divergent panel-vs-block content contracts.
3. Keep content payload separate from presentation metadata:
- `content`: renderable data contract
- `presentation_json`: chrome/visual/display overrides
4. Keep runtime orchestration and DI concerns out of persisted `content` payloads.
5. Treat content schema evolution as contract evolution with OpenAPI/codegen checks.

### Anti-patterns to avoid
1. Generic `dict[str, Any]` content payloads with no canonical schema.
2. Making content a fallback variant instead of explicit discriminated variants.
3. Embedding executable/runtime behavior in persisted content objects.
4. Different validation semantics for the same content object in panels vs blocks.

### Validation requirements
1. Contract tests proving the same `Content` payload behaves consistently in:
- panel `kind="content"`
- block `type="content"` and `type="context"` (where applicable)
2. OpenAPI/codegen verification that generated frontend types for content stay synchronized.
3. Backward compatibility tests for previously stored content payloads.

## Pydantic v2 Anti-Degradation Rules

### Purpose
Prevent implementation branches that silently fall back to weaker modeling patterns while appearing to satisfy v2 goals.

### Forbidden implementation patterns
1. Catch-all contract shapes as primary models:
- `dict[str, Any]` or `Any` used as the main shape for panel/block payloads
- non-discriminated unions where discriminator is known (`kind`, `type`)
2. Runtime behavior encoded in persisted models:
- executable DI/runtime wiring fields persisted inside panel/block objects
3. Validation bypass at persistence boundaries:
- writing raw JSON payloads directly to DB without `model_validate` normalization
- patch paths that merge untyped JSON and skip re-validation of full composition
4. OpenAPI-unfriendly model shortcuts:
- aliasing or dynamic field injection that obscures discriminators in generated schema
5. Contract drift between semantically equivalent payloads:
- separate incompatible content contracts for panel content vs block content

### Required implementation patterns
1. Discriminator-first modeling:
- panel unions discriminated by `kind`
- block unions discriminated by `type`
2. Strict boundary validation:
- validate inbound request payloads with Pydantic v2 models
- normalize and validate full composition after patch/merge operations
3. Typed extension strategy:
- use constrained extension objects (for example `extras`) rather than unconstrained `Any` trees
- maintain explicit allow-lists for experimental kinds
4. Persistence discipline:
- persisted JSONB remains storage substrate
- typed models remain source of truth for semantics
5. OpenAPI/codegen discipline:
- discriminator fields must remain explicit and stable
- generated artifacts must round-trip with runtime usage

### PR quality gates (must pass)
1. Contract evidence:
- updated model definitions include discriminators and validators
- no new primary `Any`-typed payload model introduced
2. Schema evidence:
- OpenAPI diff reviewed
- codegen outputs updated and compile cleanly
3. Behavior evidence:
- tests cover valid/invalid payloads per discriminator branch
- tests cover patch/update normalization and rejection of invalid intermediate merges
4. Compatibility evidence:
- migration decision documented (normalize vs reset)
- backward compatibility tests included when normalization path is selected

## Scope

### In scope
1. Discriminated union hardening for panel and block contracts.
2. API/versioning rules for composition contract changes.
3. OpenAPI/codegen stability workflow.
4. Frontend renderer mapping completion checklist.
5. A/B/C/D acceptance test matrix and test harness requirements.
6. Canonical content schema alignment with `Common/ContentRenderer`.
7. Graph-capable composition semantics (nesting, visibility modes, stacked containers, theme precedence).
8. Pydantic v2 anti-degradation guardrails and enforcement gates.

### Out of scope
1. Redesign of product narrative/content for each demo.
2. Non-demo page/room registry unification (tracked separately).
3. Full removal of all legacy docs/artifacts.
4. Maintaining legacy demo runtime/render/creation paths during v2 migration.

## Workstreams

## Workstream 1: Backend Contract Hardening (Pydantic v2 + SQLModel)

### Goals
1. Enforce strict panel/block object shapes by discriminator.
2. Keep persistence format stable while improving validation depth.
3. Make invalid compositions fail early with actionable errors.

### Plan
1. Promote `DemoPanelSpec` to strict discriminated union by `kind`.
2. Define explicit panel option models for all production-supported kinds:
- `chat`
- `storyRuntime`
- `content`
- `participantPanel`
- `canvas`
- `a2ui`
- `storyEditor`
- `storyPlayer`
- `storyPlayerPanel`*
- `debug`
- `strange` *
        * - not currently in models.py. *(line 3805)
3. *CUT*
4. Ensure panel `kind="content"` references canonical `Content` schema, not untyped payloads.
5. Promote `DemoBlockSpec` to discriminated union by `type`.
6. Add typed block models for at least:
- `story`
- `context` *
- `content` *
- `storyMetadata` * 
- `agentRoster`
- `orchestratorState`
- `toolCapability`
- `contributionFeed`
- `gitView` *
- `fileExplorer` *
- `strange` *
     * - not currently represented in models.py (line 3820)
7. Ensure block `type="content"` and `type="context"` reference canonical `Content` schema (or explicit nullable form where applicable).
8. Keep extension points with constrained `extras` objects where needed, rather than unconstrained catch-all objects.
9. Add model validators for:
- duplicate IDs
- invalid dependency references
- invalid region/layout combinations
- `viewport_mode='page'` uniqueness
- policy invariants (`persona_policy` + fixed persona coupling)
10. Add contract-level node semantics for:
- nested node relationships
- visibility mode behavior (`hidden_unmounted` vs `hidden_mounted`)
- container layout modes (`stack`/`split`/`tabs`/`overlay`)
11. Add validation for theme precedence metadata and override compatibility.
12. Enforce anti-degradation rules in implementation review:
- disallow new primary `Any` contract models
- require discriminator-preserving schema changes
- require re-validation after composition patch merges

### Engineering quality value
1. Reduces runtime surprises from malformed payloads.
2. Makes API behavior easier to reason about and test.
3. Produces higher-quality generated frontend contracts.

### Workstream 1 Status (2026-02-22)
1. Slice 1 backend hardening is complete:
- panel union converted to explicit discriminator branches
- block union converted to explicit discriminator branches
- canonical content contract introduced for panel/block content payloads
2. Slice 1.5 complete:
- explicit visibility contract (`visible` / `hidden_unmounted` / `hidden_mounted`) implemented across backend + frontend render behavior
3. Slice 1.6 complete:
- strict unknown-key rejection for panel options implemented
- constrained `extras` extension points allow-listed for selected kinds
4. OpenAPI/client artifacts regenerated and frontend rebuild verified.

### Next Workstream Focus
1. Begin Workstream 3 renderer completion.
2. Implement active renderer coverage for currently scoped kinds.
3. Keep deferred compatibility kinds (`storyPlayerPanel`, `strange`) on fallback paths for now to minimize rework.

### OpenAPI/Client Regeneration Checkpoints (for Workstream 1)
1. Run regeneration after Slice 1.5 (visibility enum/value expansion) and after Slice 1.6 (typed options tightening).
2. Treat generated diffs as required review artifacts:
- `frontend/src/client/schemas.gen.ts`
- `frontend/src/client/types.gen.ts`
- `frontend/src/client/sdk.gen.ts`
3. Block merge when generated client and backend contract are out of sync at these checkpoints.

## Workstream 2: OpenAPI and Codegen Reliability

This is not the concern of Workstream 1.

### Goals
1. Ensure generated client types/services remain stable and accurate.
2. Prevent silent breaking changes in composition contract evolution.

### Plan
1. Introduce explicit contract version policy:
- `schema_version` changes only for semantic contract changes
- additive changes default to minor, breaking changes require migration plan
2. Add OpenAPI diff checks in CI for demo endpoints/models.
3. Add codegen verification step:
- regenerate `frontend/src/client/schemas.gen.ts`
- regenerate `frontend/src/client/types.gen.ts`
- regenerate `frontend/src/client/sdk.gen.ts`
- fail CI if generated files drift unexpectedly
4. Add contract tests for v2 payload lifecycle:
- validate accepted v2 payload fixtures
- verify explicit rejection behavior for non-v2/legacy payload shapes
- confirm route payload contract remains stable after strict validation

### Engineering quality value
1. Prevents frontend/backend contract drift.
2. Makes changes auditable and safer across teams.
3. Improves maintainability of SDK-first development flow.

## Workstream 3: Frontend Renderer Completion
This is not the concern of Workstream 1.

### Goals
1. Ensure all contract-supported panel and block kinds have deterministic renderer behavior.
2. Eliminate unsupported-kind fallbacks for intended A/B/C/D paths.

### Panel mapping checklist
1. [x] `storyRuntime`
2. [x] `chat`
3. [x] `content`
4. [x] `participantPanel`
5. [x] `canvas`
6. [x] `a2ui`
7. [x] `storyEditor`
8. [x] `storyPlayer`
9. [x] `debug`

### Block mapping checklist
1. [x] `context`
2. [x] `content`
3. [x] `story`
4. [x] `storyMetadata` (dedicated component)
5. [x] `agentRoster` (dedicated component)
6. [x] `orchestratorState` (dedicated component)
7. [x] `toolCapability` (dedicated component)
8. [x] `contributionFeed` (dedicated component)
9. [x] `gitView` (dedicated component)
10. [x] `fileExplorer` (dedicated component)
11. [x] Explicit fallback renderer for unknown types with non-fatal diagnostics
12. [x] Reuse existing fallback renderer path where possible.

### Deferred Compatibility Kinds (Not in Current WS3 Scope)
1. Panel `storyPlayerPanel`
2. Panel `strange`
3. Block `strange`

### Plan
1. [x] Add renderer registry modules keyed by panel `kind` and block `type`.
2. [x] Route-level mapping delegates to registry, not long inline `if` chains.
3. [x] Route-level content rendering delegates to a `Common/ContentRenderer` adapter for canonical `Content`.
4. [x] Pass a normalized runtime context object to all renderers.
5. [ ] Add unit tests for renderer selection, fallback behavior, and panel/block content parity.
6. [ ] Add renderer tests for:
- nested node rendering
- hidden mounted/unmounted behavior
- hidden-mounted subscription/listener + side-effect behavior
- stacked container behavior
- theme precedence resolution across composition/node/content layers

### Workstream 3 Status (2026-02-22)
1. Active-scope renderer coverage is implemented end-to-end.
2. Dedicated block renderer components are in place for:
- `storyMetadata`
- `agentRoster`
- `orchestratorState`
- `toolCapability`
- `contributionFeed`
- `gitView`
- `fileExplorer`
3. Registry-based route wiring is complete for active panel and block kinds.
4. Frontend build has been verified after WS3 mapping changes.
5. Remaining WS3 scope is test coverage and acceptance validation, not additional active-kind mapping.

### Engineering quality value
1. Reduces branching complexity in route code.
2. Improves extensibility and testability.
3. Supports future panel/block expansion with lower regression risk.

## Workstream 4: Acceptance Validation for Demos A/B/C/D

### Goals
1. Define clear pass/fail behavior for presentation outcomes.
2. Validate both functional behavior and contract integrity.

### A/B/C/D acceptance matrix
1. **Demo A (chat + participants)**  
Must render `chat` + `participantPanel`, support room-isolated behavior, and maintain authored context block placement.
2. **Demo B (story pause/replay)**  
Must render story runtime/player path plus story metadata/context block with readable state presentation.
3. **Demo C (orchestration surface)**  
Must render multi-panel composition (`storyEditor`, `a2ui`, `chat`, participants/debug as configured) with coherent context blocks.
4. **Demo D (canvas collaboration)**  
Must render `canvas` + participant/contribution context with stable layout and responsive behavior.

### Test layers
1. Backend model validation tests for all panel/block kinds.
2. API integration tests for create/put/patch/resolve flows.
3. Frontend route tests for mapping + fallback behavior.
4. Browser-level QA scripts for A/B/C/D happy paths and key error paths.
5. Content parity tests across node surfaces and demo panel/block surfaces.
6. Composition graph behavior tests for nesting, invisible mounted nodes, stacked containers, and theme cascade.
7. Contract hardening tests for anti-degradation rules (no validation bypass, no discriminator regressions).

### Engineering quality value
1. Moves from “feature seems to work” to reproducible quality gates.
2. Prevents regressions during contract evolution.
3. Ensures demo presentation reliability for stakeholders.

## Dependencies and Sequencing

### Phase 0: Baseline and contract freeze window
1. Confirm active list of panel kinds and block types for this slice.
2. Freeze incompatible changes during migration branch.
3. Declarative: legacy cutover mode for implementation branch:
- no dual-write/dual-read legacy maintenance
- migration effort targets v2-only execution paths

### Phase 1: Backend model hardening
1. Implement discriminated unions and validators.
2. Define v2 reset/reseed path for demo composition data (no legacy normalization requirement).
3. Execute Slice 1.5 with explicit visibility values only (`visible`/`hidden_unmounted`/`hidden_mounted`).
4. Execute Slice 1.6 with strict unknown-key rejection enabled.

### Phase 2: OpenAPI/codegen pipeline hardening
1. Add diff checks and generation checks.
2. Regenerate and adopt updated frontend client artifacts.

### Phase 3: Frontend renderer completion
1. Implement registry-based mappings.
2. Complete panel/block kind coverage for A/B/C/D scope.
3. Add renderer-focused test coverage for selection, fallback behavior, and visibility/runtime semantics.

### Phase 4: Acceptance and release gating
1. Execute A/B/C/D acceptance matrix.
2. Resolve regressions.
3. Update active integration snapshot status.

## Risks and Mitigations

1. **Risk:** Breaking existing stored compositions after stricter validation.  
**Mitigation:** adopt explicit v2 reset strategy with managed recreation playbook:
- no legacy runtime support requirement during in-flight work
- recreate required demos using v2 composition contracts and validate fidelity

2. **Risk:** OpenAPI discriminator shapes generate awkward TS unions.  
**Mitigation:** keep discriminator fields explicit and stable; verify generated output in CI.

3. **Risk:** Frontend mapping churn increases during transition.  
**Mitigation:** migrate directly to v2 mapping paths; avoid long-lived legacy adapters.

4. **Risk:** Scope creep from advanced Demo C/D primitives.  
**Mitigation:** split core contract hardening from optional presentation enrichments.

5. **Risk:** content contract drift between node rendering and demo rendering.  
**Mitigation:** enforce canonical `Content` schema reuse and parity tests across panel/block/node paths.

6. **Risk:** accidental flattening of composition model during refactor.  
**Mitigation:** enforce graph-capability tests and keep flat editor views as projections only.

7. **Risk:** team reintroduces legacy support work in-flight, diluting v2 delivery.  
**Mitigation:** reject PRs that add/retain legacy runtime/render/creation paths unless explicitly approved as temporary migration tooling.

## Deliverables

1. Hardened backend composition models with discriminators and validators.
2. Updated demo endpoints with validated contract lifecycle behavior.
3. Stable generated frontend SDK/types/schemas aligned with OpenAPI.
4. Completed panel/block renderer mapping for scoped kinds. (implemented)
5. A/B/C/D acceptance suite and documented pass/fail outcomes.
6. Updated `active-demo-integration-snapshot.md` reflecting new completion state.
7. Canonical content contract documented and verified across demo and node render paths.
8. Composition graph semantics documented and validated (nesting, visibility modes, stacking, theme precedence).
9. Pydantic v2 anti-degradation gates documented and enforced in PR workflow.
10. Demo recreation pack proving that required existing demos are reproducible on v2 contracts with equal-or-better correctness.

## Definition of Done

1. Composition contract changes are implemented through the v2 hardened schema path.
2. OpenAPI and generated frontend client artifacts are synchronized and CI-enforced.
3. Demo route handles all scoped panel/block kinds through typed mapping paths. (implemented)
4. A/B/C/D acceptance criteria pass in automated and QA validation flows.
5. The active integration snapshot is updated with objective status changes and remaining deltas.
6. Canonical content payload renders consistently across panel/block/node surfaces.
7. Composition graph behaviors (nested, invisible mounted, stacked, themed) pass contract and renderer tests.
8. No forbidden Pydantic fallback patterns are introduced in merged implementation.
9. No legacy demo paths are required for successful operation in the implementation branch.
10. Required legacy demos are recreated and validated through v2 contracts only.

## Suggested File Targets (Implementation Phase)

### Backend
1. `backend/app/models.py`
2. `backend/app/crud_demo.py`
3. `backend/app/api/routes/demos.py`
4. `backend/app/tests/...` (new model and endpoint tests)

### Frontend
1. `frontend/src/routes/_layout/demo.$slug.tsx`
2. `frontend/src/components/Demo/...` (renderer registry modules)
3. `frontend/src/client/schemas.gen.ts`
4. `frontend/src/client/types.gen.ts`
5. `frontend/src/client/sdk.gen.ts`

### Docs
1. `frontend/src/components/Demo/demo-docs/active-demo-integration-snapshot.md`
2. `frontend/src/components/Demo/demo-docs/demo-testing-references/...`
