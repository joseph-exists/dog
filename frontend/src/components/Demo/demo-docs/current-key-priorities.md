# Demo Builder Milestone Handoff
> **Status:** Canonical handoff for next engineers
> **Last Revised:** 2026-02-26

## Milestone Outcome
Demo Builder is now beyond baseline guided authoring. It includes nested composition affordances (tree + add-child + path-aware focus), clone-from-source workflows, interaction dispatch configuration, and checklist-guided setup. Next work should tighten nested authoring UX and runtime diagnostics, not rebuild core architecture.

## Source-Of-Truth Doc Map
1. `frontend/src/components/Demo/demo-docs/current-key-priorities.md`
- Canonical status, priorities, and handoff decisions.
2. `frontend/src/components/Demo/demo-docs/demo-builder-workflow.md`
- Architecture, schema, capability, and workflow model.
3. `frontend/src/components/Demo/demo-docs/active-demo-integration-snapshot.md`
- Runtime/backend integration checkpoint and contract reality.
4. `frontend/src/components/Demo/demo-docs/active-implementation-history.md`
- Chronological implementation log.

## Implemented Foundation
1. Reusable editor decomposition:
- `DemoTopLevelEditor`
- `DemoTemplateSetupChecklist`
- `DemoPanelEditor`
- `DemoBlockEditor`
- `DemoCompositionTree`
- `DemoValidationPanel`
- `DemoRawJsonEditor`
- `DemoSaveBar`

2. Canonical builder schema + validation:
- active panel/block kinds, defaults, templates (A/B/C/D/E/F/G)
- semantic validation model + issue paths
- template setup persistence (`metadata_json.template_setup`)
- interaction handler schema helpers (`click_prompt_dispatch.v1`)

3. Capability registry and safety model:
- deterministic pack composition + env activation
- compatibility/safety analyzers
- normalization + semantic validator hooks

4. High-value UX slices now shipped:
- collapsible setup/checklist/editor sections
- panel/block cards are collapsible with richer labels (kind/title/status context)
- clone existing panel/block from demo config or template
- composition tree with nested node detection
- add child panel/block directly from tree
- path-aware tree focus into editor (best-path matching + auto-expand)

5. Interaction routing vertical slice (runtime + builder):
- block interaction contract UI + starter action
- chat receiver registration UI
- enforcement toggle for registered receiver routing

## What Is Stable Enough To Reuse
1. Two-layer model:
- persisted contract remains `DemoPageCompositionBase_Input`
- builder schema remains authoring/view-model layer

2. Registry separation:
- runtime registry remains renderer-facing
- builder registry remains authoring/validation-facing

3. Contract-safe extension pattern:
- prefer descriptor/registry additions over payload-shape changes

## Remaining Work (Priority Order)
1. P1: Nested authoring ergonomics (highest impact)
- add explicit child-slot editing (`slot`) and visibility controls in guided UI
- add cycle/depth guardrails and clearer nested constraints
- add dedicated nested-child management on panel/block cards (not tree-only)

2. P1: Tree-to-editor fidelity completion
- add more `data-builder-path` anchors for deeper advanced JSON controls
- improve fallback targeting when no exact nested field control exists

3. P1: Descriptor completeness
- continue removing editor-specific branches by promoting behavior into capability descriptors

4. P1: Diagnostics + preview confidence
- capability-aware inline diagnostics for nested/interactions/theme constraints
- expand preview parity where guided controls still diverge from runtime behavior

5. P2: Creator-flow contract enhancements
- decide scope/timing for publish/clone-at-contract level and per-user override lifecycle APIs

## Risks To Track
1. Nested JSON capability is ahead of guided UX, which can cause user confusion.
2. Interaction routing can appear broken without explicit receiver registration + acceptance settings.
3. Theme/cascade convergence is still in progress and can create preview/runtime mismatch.

## Definition Of Done For This Milestone
1. Engineers can identify canonical docs in under 2 minutes.
2. Engineers can extend capabilities without persisted-contract churn.
3. QA/UX can create, clone, nest, focus, and save demos without raw JSON for common paths.
4. Remaining work is focused on nested UX hardening and diagnostics rather than architecture rework.
