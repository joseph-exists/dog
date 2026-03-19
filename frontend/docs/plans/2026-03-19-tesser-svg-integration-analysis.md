# Tesser SVG Integration Analysis

**Date**: 2026-03-19
**Status**: Review Artifact
**Source Prompt**: analysis of `frontend/docs/plans/2026-03-18-tesser-svg-integration-design.md` against current frontend/backend surface area

## Context

This note responds to the open questions in `2026-03-18-tesser-svg-integration-design.md` after reviewing:

- `AGENT.md`
- `frontend/src/components/Stories/StoryEditor/NodeEditor/SVG_STUDIO_REFERENCE.md`
- `frontend/src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx`
- `frontend/src/components/Svg/*`
- `frontend/src/components/Room/panels/CanvasPanel.tsx`
- `frontend/src/services/demoService.ts`
- `frontend/src/hooks/useSvgs.ts`
- `frontend/src/services/svgService.ts`
- `backend/app/api/routes/tesser.py`
- `backend/app/api/routes/svgs.py`
- `backend/app/models.py`
- `tesser/docs/history/completed-api_migration_backlog.md`

## Short Answer

The current proposal is directionally right, but too greenfield relative to the codebase.

The main mismatch is that it treats Tesser Studio as a new self-contained frontend subsystem with a recursive schema form engine, while the existing product surface is already split into:

- a lightweight SVG library shell for browse/create/edit operations
- a much richer SVG composition studio inside `NodeEditorForm`
- an already-working Tesser script selection and help flow in demos/rooms

My view is that the right foundation is not "build a new generic schema app under `components/Svg/TesserStudio/*` first." It is:

1. Reuse the existing `SvgShell` panel model.
2. Reuse existing `svgs` query/mutation patterns.
3. Reuse existing Tesser service contracts from `demoService.ts`.
4. Extract only the minimum shared Tesser execution primitives needed by Svg, Demos, Rooms, and later Projects.
5. Treat schema-driven forms as progressive enhancement, not MVP core architecture.

## Surface Area Assessment

## What the code already gives us

- `SvgShell.tsx` is a thin host for pluggable panels. Adding a Tesser panel fits cleanly.
- `SvgsGalleryPanel.tsx` and `SvgOperationsPanel.tsx` already define the SVG library UX language: `PanelContainer`, `Alert`, `Tabs`, `Button`, `Input`, `Label`, query-backed mutations, and local draft state.
- `useSvgs.ts` and `svgService.ts` already centralize library queries and writes.
- `NodeEditorForm.tsx` already contains the highest-value SVG authoring affordances in the repo:
  - layered composition
  - library import
  - apply planning
  - non-destructive MDX merge modes
  - explicit conversion between `svg` and `mdx`
- `CanvasPanel.tsx` and `demoService.ts` already expose a Tesser interaction model:
  - list scripts
  - show help
  - pass `script_input`
  - render async / poll status
- `backend/app/api/routes/tesser.py` already has the core Tesser routes needed for a frontend integration.
- `backend/app/api/routes/svgs.py` and the SVG models already support provenance-friendly metadata on persisted assets.

## What the code does not give us yet

- There is no shared frontend Tesser hook layer. Tesser access is still demo-oriented.
- There is no `/svgs/from-tesser-job` route today.
- There is no existing generic JSON-schema form system in the frontend.
- There is no persisted "work in flight" model for SVG generation or SVG studio drafts.
- There is no shared abstraction tying Tesser output to multiple destinations:
  - save to library
  - apply to node body
  - attach to room/demo/project state

## Question-by-Question Perspective

### 1. Does this architecture align with our frontend composition and enable the suite of interdependent functionality and affordances which are our top-level concerns?

Partially.

It aligns at the `SvgShell` level because a new panel is a natural fit. It does not align well at the capability level because the proposal places the deepest new investment in a brand new schema-form subsystem, while the deepest existing SVG affordances already live in `NodeEditorForm.tsx`.

That matters because the top-level concerns are not only "submit script input and save an SVG." They also include:

- composition
- importing existing assets
- applying outputs into content
- preserving non-destructive authoring paths
- moving work between authoring surfaces

The current plan covers script execution and asset creation, but it does not yet connect to the strongest existing affordance set.

### 2. Does this plan take into consideration the variability of tesser script affordances, including depth of parameterization?

In intent, yes. In implementation assumptions, not enough.

The schema-driven approach assumes the scripts can be expressed usefully through a generic recursive JSON-schema form builder. That will work for simple and medium scripts, but the migration backlog shows the system now has a broad script surface with 28 migrated render scripts. That increases variance, not decreases it.

The likely reality is:

- some scripts will be well served by generated controls
- some will need raw JSON escape hatches
- some will want script-specific curated UIs or presets
- some animation or multi-output scripts may not map cleanly to "single SVG asset create" semantics

So the plan is correct to care about schema depth, but too optimistic that schema rendering alone is the product abstraction.

### 3. Does this plan enable later enabling through various other interfaces, including but not limited to Rooms, Demos, Projects?

Not by itself.

It would create another Tesser-specific implementation inside `components/Svg`, while demos already have a separate path in `CanvasPanel.tsx` and `demoService.ts`. If built as proposed, later reuse would probably mean copying logic outward instead of sharing it.

The more extensible move is to first introduce shared frontend Tesser primitives:

- `useTesserScripts`
- `useTesserScriptHelp`
- `useEnqueueTesserScript`
- `useTesserJobStatus`
- `useSaveSvgFromTesserResult` or equivalent asset-save mutation

Then each host surface can compose those primitives differently:

- Svg Library: generate and save to asset library
- Node Editor: generate and apply to node body or import as layer
- Demos/Rooms: generate and render in place
- Projects: persist generated outputs into project artifacts

### 4. Does this plan create an extensible foundation for increasing the variance of scripts tesser has available?

Only if the form system is explicitly tiered.

A durable foundation would have three input modes:

1. `PresetForm`
2. `SchemaForm`
3. `RawJsonEditor`

Without that, script variance will push the generic form system into a brittle edge-case collector. The existing `CanvasPanel` already proves the raw JSON fallback is useful and cheap.

The migration backlog is relevant here: since the render API migration is complete, the bottleneck is no longer script contract stabilization. The bottleneck is frontend affordance strategy for a widening script catalog.

### 5. Does this plan use existing SVG types, primitives and methods when appropriate?

Only partially.

It reuses the backend SVG asset model conceptually, but it misses important existing frontend SVG behavior:

- existing library query/mutation hooks
- existing asset editor and gallery flow
- existing import behaviors in `NodeEditorForm`
- existing `svg` versus `mdx` apply planning semantics

If Tesser output lands in the library, the next natural step is often "use this inside node content." The architecture should account for that as a first-class path, because that is already where the most developed SVG handling logic exists.

### 6. Does this plan use our existing UI primitives when appropriate?

Mostly yes at a high level, but the document should be more explicit.

The current SVG surfaces already rely on:

- `PanelContainer`
- `Alert`
- `Tabs`
- `Dialog`
- `Button`
- `Input`
- `Label`
- `Textarea`
- `Badge`
- shared query/mutation toast behavior

The proposed file tree implies a new UI subtree, but not how strongly it will conform to those existing patterns. It should.

### 7. Does this plan enable sharing of work in flight as well as work completed?

Completed work: yes, if saved as SVG assets.

Work in flight: no, not really.

The jobs list provides observability for in-flight execution, but not shareable draft state. The current proposal does not define any persisted object for:

- unsaved script input
- partially configured presets
- queued job records tied to a reusable artifact
- draft compositions combining generated SVG plus later layer edits

If sharing in-flight work matters, the MVP should at least preserve enough metadata in the saved asset or related job record to support rehydration. Otherwise only finished SVG markup is truly shareable.

## Recommended Architecture Shift

## Recommendation

Keep the "Tesser Studio panel in `SvgShell`" idea, but reduce the initial scope and center it on shared execution primitives plus asset/library interoperability.

### MVP shape

- Add a new `Tesser Studio` panel to `SvgShell`.
- Start with:
  - script selector
  - script description/help
  - preset chooser when available
  - raw JSON editor for `script_input`
  - optional lightweight generated controls for only the simplest schema cases
  - enqueue + poll
  - save result to SVG library
- Reuse `useSvgs` invalidation so gallery updates immediately.

### Shared primitives to extract first

- frontend Tesser hooks/services should move out of demo-specific ownership
- the save-to-library path should be usable by Svg, NodeEditor, Demos, and Rooms
- the payload shape should preserve provenance in `metadata_json`

Suggested metadata baseline:

- `source: "tesser"`
- `script_name`
- `script_input`
- `job_id`
- `request_id`
- `runtime_profile`
- `resolved_capabilities`
- `status`
- `created_from_surface` such as `svg-library`, `node-editor`, `demo-canvas`

### Why not make recursive schema forms the core of MVP

- There is no existing schema form framework in this frontend.
- It is the highest-risk implementation area in the proposal.
- It is not required to prove the core product loop:
  - choose script
  - provide input
  - enqueue
  - inspect job
  - save result
  - reuse result elsewhere

That loop should land first.

## Relationship To SVG Studio In NodeEditor

The new Tesser Studio should not ignore `NodeEditorForm.tsx`; it should be designed to connect to it later.

The strongest follow-on move after library save is:

- generate in Tesser Studio
- save as SVG asset
- import that asset into SVG Studio as a layer
- or apply the generated markup directly to node content using existing apply-plan semantics

That path is already closer to the repo's richest SVG authoring story than the standalone library surface.

So I would treat the library panel as one host, not the final center of gravity.

## Implementation Order I Would Recommend

1. Extract shared frontend Tesser service/hooks from the existing demo-oriented flow.
2. Add a minimal `Tesser Studio` panel to `SvgShell` using existing UI primitives.
3. Support script selection, help text, raw JSON `script_input`, enqueue, polling, and save-to-library.
4. Add provenance-rich `metadata_json`.
5. Reuse the saved asset immediately in gallery and operations flows.
6. Add NodeEditor import/apply integration path.
7. Add selective schema-derived controls and script-specific curated forms after real script usage patterns are known.

## Concrete Risks In The Current Plan

- Building a recursive schema form system before validating which scripts deserve bespoke UX.
- Creating a new Tesser frontend island instead of shared hooks usable by Svg, Demos, Rooms, and Projects.
- Saving only final SVG assets without a draft/job rehydration model, which weakens "share work in flight."
- Treating failed assets as empty-markup placeholders when the current SVG model requires valid non-empty `<svg>` markup.

That last point needs explicit attention: the proposed failure case uses `svg_markup=""`, but the backend validator in `SvgAssetBase` rejects empty markup and requires a valid `<svg>` root.

## Bottom Line

My answer to the design doc is:

- `Yes` on adding Tesser into the SVG library surface.
- `No` on making a full schema-form architecture the primary MVP investment.
- `Yes` on designing for later Rooms/Demos/Projects reuse, but only if Tesser interaction is extracted into shared primitives first.
- `Yes` on preserving SVG assets as the durable completed-work artifact.
- `No` on the current plan fully covering work-in-flight sharing.

If we want the implementation to match the current codebase, the steel thread should be:

`shared tesser hooks -> SvgShell panel -> save asset -> reuse asset in NodeEditor/Demos/Rooms`

rather than:

`new schema-form subsystem -> new isolated Tesser Studio app inside Svg`
