# Tesser SVG Integration MVP Plan

**Date**: 2026-03-19
**Status**: Proposed
**Related**:

- `frontend/docs/plans/2026-03-18-tesser-svg-integration-design.md`
- `frontend/docs/plans/2026-03-19-tesser-svg-integration-analysis.md`
- `frontend/src/components/Stories/StoryEditor/NodeEditor/SVG_STUDIO_REFERENCE.md`

## Context

We want an MVP that proves three things clearly:

1. The frontend can create a diverse set of parameterized SVGs from the broader Tesser script library.
2. The frontend foundation can absorb increased Tesser script capacity without major rework.
3. The implementation follows our current standards for composability, reuse, and progressive disclosure.

The analysis conclusion is that we should not begin with a large greenfield schema-form system. The current codebase already gives us:

- a pluggable `SvgShell`
- established SVG library query/mutation patterns
- an existing Tesser service contract in the demo surface
- a rich downstream SVG consumer in `NodeEditorForm`

So the MVP should prove breadth of script execution first, while establishing reusable Tesser primitives that other surfaces can consume later.

## MVP Product Goal

Add a `Tesser Studio` panel to the SVG library that lets a user:

- browse available Tesser scripts
- inspect script description/help
- provide parameterized input
- enqueue a render job
- observe job state
- save successful output into the SVG library with provenance metadata

The MVP is successful if it can support a representative cross-section of Tesser scripts without frontend rewrites per script, while leaving room for richer per-script affordances later.

## Success Criteria

## Functional proof

- A user can generate SVGs from multiple Tesser scripts with materially different input shapes.
- The UI supports at least three interaction levels:
  - zero-config or near-zero-config script run
  - simple structured parameter editing
  - raw JSON input for advanced or irregular schemas
- Completed jobs can be saved as SVG assets and appear immediately in the SVG gallery.
- Saved assets include enough provenance metadata to understand how they were produced and to support later rehydration work.

## Architecture proof

- Tesser frontend access is moved into shared hooks/services, not embedded only inside the SVG panel.
- The SVG library panel composes those hooks without introducing a second copy of the Tesser execution flow.
- The save-to-library path is reusable from future surfaces such as Node Editor, Rooms, Demos, and Projects.

## UX proof

- The default path is easy for simple scripts.
- The advanced path is still available for deeper parameterization.
- The MVP uses existing UI primitives and existing SVG library behavior patterns.

## Explicit MVP Boundaries

## In scope

- New `Tesser Studio` panel in the existing `SvgShell`
- Shared frontend Tesser service/hook layer
- Script list + script help loading
- Script input via:
  - defaults/presets when available
  - lightweight form controls for simple schemas
  - raw JSON editor fallback
- Async enqueue + polling
- Save successful Tesser result to SVG library
- Provenance metadata on saved assets
- Gallery refresh on successful save

## Out of scope

- Full recursive schema engine with exhaustive JSON Schema support
- Script-specific custom editors across the whole library
- WebSocket job streaming
- Persisted draft objects for in-flight work
- Node Editor integration in the initial landing
- Room/Demo/Project UI integration in the initial landing
- Backend callback-driven autosave

## Core Design Principles

## 1. Shared Tesser execution, host-specific presentation

The Tesser interaction model should be implemented once, then composed differently by each surface.

That means the SVG library MVP should consume shared primitives such as:

- `useTesserScripts`
- `useTesserScriptHelp`
- `useEnqueueTesserScript`
- `useTesserJobStatus`
- `useSaveTesserSvgToLibrary`

The SVG panel becomes one host of these primitives, not their owner.

## 2. Progressive disclosure for parameterization

The frontend must prove it can support script diversity without hardcoding per-script UIs as the default strategy.

The MVP input model should therefore be tiered:

1. `Defaults`
2. `Simple generated controls`
3. `Raw JSON`

This preserves reach across the broader Tesser library while avoiding premature investment in a full schema engine.

## 3. Use existing SVG library patterns

The MVP should reuse:

- `SvgShell`
- `PanelContainer`
- existing query invalidation via `useSvgs`
- existing toast and mutation handling patterns
- existing SVG asset metadata behavior

## 4. Preserve later composability

The output of Tesser Studio should not be a special-case artifact. It should land as a normal SVG asset with strong metadata, so it can later flow into:

- `NodeEditorForm` layer import
- node body apply flows
- room/demo canvases
- future project asset workflows

## Proposed User Experience

## Tesser Studio panel structure

`TesserStudioPanel`

- Script selector
- Script summary/help area
- Input mode switch
  - Guided
  - JSON
- Simple parameter controls area
- JSON editor area
- Run action row
- Job status list
- Save-to-library action for completed jobs

## Input mode behavior

### Guided mode

Guided mode handles only the simplest cases well:

- top-level object properties
- primitive scalar fields
- flat enums
- basic arrays of primitives only if cheap to support

If a script schema is deeper or irregular, the UI should say so explicitly and route the user to JSON mode rather than pretending to fully support it.

### JSON mode

JSON mode is always available.

This is the capacity-preserving fallback that allows the frontend to support the broader Tesser library without major frontend rework when script diversity increases.

## Save behavior

When a job completes with SVG output, the user can save it into the SVG library.

Saved asset metadata should include at least:

- `source: "tesser"`
- `script_name`
- `script_input`
- `job_id`
- `request_id`
- `runtime_profile`
- `resolved_capabilities`
- `created_from_surface: "svg-library"`
- `saved_at`

Failed jobs should not create invalid SVG assets with empty markup. Failure state belongs in the job UI for MVP.

## API and Data Shape Plan

## Frontend service layer

Create a Tesser-focused frontend service that is no longer demo-route specific in naming, even if it reuses the same API endpoints underneath.

Suggested responsibilities:

- list scripts
- fetch script help
- enqueue script
- get job status

## Save-to-library path

For MVP, prefer reusing existing `POST /svgs` creation over introducing a new backend save endpoint unless a stronger backend reason emerges during implementation.

Reason:

- existing SVG creation already works
- metadata is already supported
- the frontend can save from completed job payload directly
- it keeps the first iteration smaller

If backend job status does not reliably expose the final SVG payload needed for create, then introduce a narrowly scoped backend helper route as a second step, not as the first assumption.

## Asset contract constraints

The SVG asset model requires valid non-empty `<svg>...</svg>` markup.

That means:

- successful jobs can be persisted as assets
- failed jobs should remain job records in the UI for MVP
- any future failed-asset concept must still persist valid SVG markup, not an empty string

## Implementation Phases

## Phase 1: Shared frontend Tesser primitives

### Goal

Extract reusable Tesser API access from the current demo-oriented surface.

### Deliverables

- shared Tesser service module
- hooks for scripts/help/enqueue/job polling
- shared types for script/job UI state where needed

### Likely file touches

- `frontend/src/services/demoService.ts`
- `frontend/src/services/`
- `frontend/src/hooks/`

### Notes

This phase is the key composability move. Without it, the SVG panel would repeat the demo integration instead of establishing reuse.

## Phase 2: Minimal Tesser Studio panel in Svg

### Goal

Land the new SVG-hosted Tesser execution surface using existing shell/panel conventions.

### Deliverables

- new panel component under `frontend/src/components/Svg/`
- script selector
- help/details display
- guided vs JSON input mode
- enqueue action
- local jobs list with polling

### Likely file touches

- `frontend/src/components/Svg/SvgShell.tsx`
- `frontend/src/components/Svg/panels/`
- `frontend/src/components/Svg/types.ts`
- `frontend/src/components/Svg/index.ts`

### Notes

The jobs list should focus on clarity:

- queued
- running
- completed
- failed

It does not need persistence beyond the current page session for MVP.

## Phase 3: Save completed Tesser output into SVG library

### Goal

Turn completed Tesser output into normal SVG assets using the existing library contract.

### Deliverables

- save action for completed job rows
- SVG asset creation payload with provenance metadata
- cache invalidation so the gallery updates immediately

### Likely file touches

- `frontend/src/hooks/useSvgs.ts`
- `frontend/src/services/svgService.ts`
- new Tesser panel files

### Notes

This phase proves the main product loop:

- generate
- inspect
- save
- browse in gallery

## Phase 4: Guided controls for simple schema cases

### Goal

Demonstrate that the frontend can support parameterized generation beyond raw JSON, without overcommitting to full schema recursion.

### Deliverables

- lightweight schema-to-controls mapper for simple top-level cases
- explicit fallback to JSON mode when schema is more complex than the MVP supports

### Supported shapes for MVP

- `type: object`
- primitive `string`, `number`, `integer`, `boolean`
- `enum`
- simple defaults
- plain descriptions

### Explicitly unsupported in MVP guided mode

- deep nesting beyond one level
- complex conditional branches
- polymorphic schemas
- arbitrarily nested arrays/objects
- advanced schema dependencies

### Notes

This is the phase that proves breadth without claiming completeness.

## Phase 5: Validation against diverse Tesser scripts

### Goal

Prove the frontend works against a representative range of Tesser scripts from the broader library.

### Validation target

Select a script set that includes:

- one simple low-parameter script
- one moderately parameterized script
- one script whose schema pushes the UI into JSON mode
- one script with a different visual/output style than the others

### Acceptance result

The MVP is acceptable if all selected scripts can be run from the frontend and at least the successful outputs can be saved as normal SVG assets without per-script frontend rewrites.

## File/Module Plan

## New frontend modules

- Tesser service module outside demo-specific ownership
- Tesser hooks module(s)
- `TesserStudioPanel` and small supporting UI pieces under `frontend/src/components/Svg/`

## Existing modules to update

- `SvgShell.tsx` or the SVG page assembly point to register the panel
- `useSvgs.ts` for invalidation patterns if needed
- `demoService.ts` only to remove duplicated Tesser ownership or delegate to the new shared service

## Backend modules

Prefer no backend changes in the first pass if existing Tesser job status already returns enough completed render data to create SVG assets directly through `/svgs`.

Possible backend follow-up only if necessary:

- small helper route for save-from-job
- better job payload normalization for SVG extraction

## Risks and Mitigations

## Risk: We overbuild schema support too early

Mitigation:

- keep guided mode intentionally narrow
- keep JSON mode always available
- fall back explicitly instead of faking support

## Risk: Tesser logic is duplicated across surfaces

Mitigation:

- extract shared Tesser primitives first
- make Svg consume them rather than reimplementing them

## Risk: MVP only proves one or two narrow scripts

Mitigation:

- define a representative validation set up front
- require successful runs across diverse parameter shapes

## Risk: Failed jobs create invalid SVG assets

Mitigation:

- do not persist failures as SVG assets in MVP
- keep failure handling in the job UI

## Risk: Save flow depends on backend assumptions that are not true

Mitigation:

- validate job status payload shape before implementation
- only add backend helper route if direct save via `/svgs` is not viable

## Acceptance Checklist

- [ ] Shared Tesser service/hooks exist outside demo-specific ownership.
- [ ] SVG library includes a `Tesser Studio` panel.
- [ ] A user can list scripts and inspect help/details.
- [ ] A user can provide input via guided controls for simple schemas.
- [ ] A user can always provide input via raw JSON.
- [ ] A user can enqueue a Tesser job and see status updates.
- [ ] A user can save a completed result to the SVG library.
- [ ] Saved assets include provenance metadata.
- [ ] The MVP is verified against a diverse script set.
- [ ] No major frontend rewrite is required to support the validation set.

## Recommended Next Step After MVP

After this lands and is validated, the next roadmap item should be integration with `NodeEditorForm`, because that is where the repo already has the strongest SVG composition and apply semantics.

That follow-on should aim for:

- import saved Tesser assets as layers
- apply generated SVG into node body through existing apply-plan behavior
- preserve provenance across library and node-authoring surfaces
