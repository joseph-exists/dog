# Demo Builder Milestone Handoff
> **Status:** Canonical handoff for next engineers  
> **Last Revised:** 2026-02-24

## Milestone Outcome
The Demo Builder milestone is functionally complete for guided composition authoring and capability-driven editing. The next milestone should build on this foundation rather than reworking it.

## Next Builder RFC
1. Prompt Builder kickoff RFC:
- `docs/plans/2026-02-24-prompt-builder-rfc.md`

## Source-Of-Truth Doc Map
1. `frontend/src/components/Demo/demo-docs/current-key-priorities.md`
- Canonical status, sequencing, and handoff guidance.
2. `frontend/src/components/Demo/demo-docs/demo-builder-workflow.md`
- Architecture and implementation workflow details.
3. `frontend/src/components/Demo/demo-docs/active-demo-integration-snapshot.md`
- Runtime/backend integration checkpoint.
4. `frontend/src/components/Demo/demo-docs/active-implementation-history.md`
- Historical changelog (archive), not planning source-of-truth.

## Implemented Foundation
1. Builder decomposition and reusable editors:
- `DemoTopLevelEditor`
- `DemoValidationPanel`
- `DemoPanelEditor`
- `DemoBlockEditor`
- `DemoRawJsonEditor`
- `DemoSaveBar`

2. Canonical builder schema layer (`demoBuilderSchema.ts`):
- active panel/block kinds and defaults
- template constructors (A/B/C/D/E/F/G)
- semantic validation model and issue codes
- field-spec descriptors powering guided controls

3. Capability registry layer (`demoBuilderCapabilityRegistry.ts`):
- deterministic registry composition API
- pack registration/inventory and env-gated activation
- capability-level normalization and validator hooks
- requirement compatibility/safety analyzers

4. Guided template setup workflow:
- post-apply checklist
- persistent setup state in `metadata_json.template_setup`
- unresolved deep links
- in-context story/persona pickers

5. Theming/presentation progress:
- theme pickers for composition/panel/block surfaces
- guided + JSON fallback editing for presentation fields
- shared presentation resolver wiring
- capability-level runtime-coupled preview effects for key blocks

## What Is Stable Enough To Reuse
1. Two-layer model:
- persisted contract stays `DemoPageCompositionBase_Input`
- builder schema is a view-model/authoring layer

2. Registry separation:
- runtime registry (`rendererRegistry.tsx`) remains renderer-facing
- builder registry remains authoring/validation-facing

3. Extension pattern:
- add/override capability behavior via registry hooks and pack composition
- avoid editing persisted payload shape for builder UX changes

## Remaining Work (Priority Order)
1. P1: Capability descriptor maturity
- finish descriptor-driven controls for edge field types and specialized widgets
- continue moving residual editor conditionals behind capability descriptors

2. P1: Live preview fidelity
- expand capability-level preview adapters so guided presentation fields match runtime rendering more closely
- keep preview toggleable to reduce builder UI clutter

3. P1: Diagnostics overlays
- add capability-aware diagnostics in preview/editor (missing dependency, unsupported presentation key, fallback mode)

4. P1: Theme system convergence
- continue alignment with shared cascade/token system in `src/components/Common/Themes/`
- document precedence and unsupported keys explicitly per capability

## Agent-Builder Reuse Guidance
If the next team is building Agent-Builder, reuse these pieces directly:
1. Schema pattern from `demoBuilderSchema.ts`:
- field specs
- defaults/constructors
- semantic validator surface

2. Registry pattern from `demoBuilderCapabilityRegistry.ts`:
- capability descriptors
- normalization/validation hooks
- pack composition and compatibility gates

3. Editor composition pattern:
- split top-level/panel/block/raw-json/validation components
- keep handlers contract-safe and patch-based

4. Template setup pattern:
- assumption checklist + persisted setup state + deep links + dependency pickers

Likely Agent-Builder-specific replacements:
1. capability catalog and dependency requirements
2. template constructors and guided setup prompts
3. runtime preview adapters for agent-specific surfaces

## Risks To Track
1. Presentation passthrough expectations can exceed what current runtime renderers implement.
2. Pack-level overrides can drift from runtime capability semantics if compatibility checks are bypassed.
3. Theme cascade convergence is ongoing; partial migration can cause UX inconsistency.

## Definition Of Done For This Milestone
1. Next engineer can identify canonical docs in under 2 minutes.
2. Next engineer can extend a capability without changing persisted contract shape.
3. QA/UX can apply templates and complete setup without raw JSON dependency.
4. Handoff clearly identifies the next sequencing for Agent-Builder reuse.
