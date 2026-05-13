# Tesser SVG Integration Implementation Sequence

**Date**: 2026-03-19
**Status**: Proposed
**Related**:

- `frontend/docs/plans/2026-03-19-tesser-svg-integration-analysis.md`
- `frontend/docs/plans/2026-03-19-tesser-svg-integration-mvp-plan.md`

## Purpose

This document turns the MVP plan into an execution sequence with:

- sharper implementation order
- proposed file ownership
- dependency boundaries
- small initial tickets

The aim is to keep the work composable and reviewable while protecting the three MVP proofs:

1. broad parameterized SVG generation from Tesser
2. a frontend foundation that scales with Tesser capacity
3. implementation reuse across surfaces

## Implementation Strategy

Use a thin-vertical-slice sequence:

1. establish shared Tesser access primitives
2. land a minimal SVG-hosted Tesser panel
3. prove job execution and save-to-library
4. layer on simple guided controls
5. validate against diverse scripts

This keeps each step independently useful and avoids blocking on a large form system.

## Ownership Model

## Area A: Shared Tesser frontend primitives

### Responsibility

- Tesser API access
- Tesser types
- Tesser hooks
- polling behavior
- job state normalization

### Proposed file ownership

- `frontend/src/services/tesserService.ts`
- `frontend/src/hooks/useTesser.ts`
- `frontend/src/hooks/useTesserJob.ts`
- optional shared types:
  - `frontend/src/components/Svg/TesserStudio/types.ts`
  - or `frontend/src/services/tesserTypes.ts`

### Rules

- no Svg-specific UI logic here
- no Demo-specific naming here
- all other surfaces should be able to consume this layer directly

## Area B: SVG-hosted Tesser Studio UI

### Responsibility

- render the panel
- orchestrate script selection and input modes
- show job rows and save actions
- consume shared hooks

### Proposed file ownership

- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`
- `frontend/src/components/Svg/panels/index.ts`
- optional support files:
  - `frontend/src/components/Svg/TesserStudio/ScriptSelector.tsx`
  - `frontend/src/components/Svg/TesserStudio/ScriptHelpCard.tsx`
  - `frontend/src/components/Svg/TesserStudio/TesserJobList.tsx`
  - `frontend/src/components/Svg/TesserStudio/TesserInputEditor.tsx`
  - `frontend/src/components/Svg/TesserStudio/schema.ts`

### Rules

- reuse existing UI primitives
- do not own API logic directly
- keep the first iteration simple enough to fit existing SVG panel patterns

## Area C: SVG library persistence and cache sync

### Responsibility

- save completed Tesser output into `/svgs`
- preserve provenance metadata
- invalidate SVG gallery and detail caches

### Proposed file ownership

- `frontend/src/hooks/useSvgs.ts`
- `frontend/src/services/svgService.ts`
- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`

### Rules

- use normal SVG asset creation
- no failed-job asset persistence in MVP

## Area D: SVG shell registration and assembly

### Responsibility

- register the new panel
- control placement/prominence

### Proposed file ownership

- SVG route or page assembly file that builds `SvgShell` panel config
- `frontend/src/components/Svg/index.ts`
- `frontend/src/components/Svg/types.ts` only if panel metadata needs extension

### Rules

- no business logic here
- keep this as composition only

## Phase Sequence

## Phase 0: Payload and route sanity check

### Goal

Confirm the real Tesser job payload contains the data needed to save a completed SVG through existing `/svgs` create.

### Output

- one short technical note or implementation comment
- decision:
  - direct frontend save is viable
  - or backend helper route is required

### File ownership

- no required code ownership yet
- likely inspection in:
  - `frontend/src/services/demoService.ts`
  - `backend/app/api/routes/tesser.py`
  - related backend Tesser service/job models

### Exit criteria

- exact source of completed SVG markup is known
- provenance fields available from enqueue/status are known

### Audit result

- `TesserJobStatusResponse` includes a `render` payload.
- Tesser service payload construction populates `render.svg` when the output format is SVG.
- For MVP, direct frontend save to `/svgs` is viable for successful jobs where:
  - `render.format === "svg"`
  - `render.svg` is a non-empty string
- This means Ticket 6 can target normal `SvgAssetCreatePrivate` creation without requiring a backend helper route in the first pass.

## Phase 1: Extract shared Tesser service layer

### Goal

Create a reusable Tesser API surface independent of the current demo host.

### Main changes

- add `tesserService.ts`
- move or wrap:
  - list scripts
  - get script help
  - enqueue script
  - get job status
- keep `demoService.ts` delegating to the new service where appropriate

### File ownership

- `frontend/src/services/tesserService.ts`
- `frontend/src/services/demoService.ts`

### Exit criteria

- Svg and Demo can both call the same Tesser service layer
- no duplicated request construction for the core Tesser endpoints

## Phase 2: Add shared Tesser hooks

### Goal

Create React-query-based access patterns that match the rest of the frontend.

### Main changes

- add hooks for scripts/help/enqueue/job polling
- normalize query keys
- normalize mutation success/error behavior

### File ownership

- `frontend/src/hooks/useTesser.ts`
- `frontend/src/hooks/useTesserJob.ts`

### Exit criteria

- UI surfaces can consume Tesser state declaratively
- polling behavior is encapsulated instead of hand-rolled per component

## Phase 3: Land minimal Tesser Studio panel

### Goal

Add a panel to the SVG surface that proves the host integration.

### Main changes

- new `TesserStudioPanel`
- script selection
- help/details display
- JSON input editor
- enqueue action
- in-session jobs list

### File ownership

- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`
- `frontend/src/components/Svg/panels/index.ts`
- SVG page assembly file

### Exit criteria

- user can choose a script, provide JSON, enqueue a job, and observe status

## Phase 4: Save completed jobs into the SVG library

### Goal

Close the MVP product loop from generation to persisted asset.

### Main changes

- save action on completed jobs
- map completed job output into `SvgAssetCreatePrivate`
- invalidate SVG list caches

### File ownership

- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`
- `frontend/src/hooks/useSvgs.ts`
- `frontend/src/services/svgService.ts`

### Exit criteria

- a completed Tesser job can become a normal SVG asset
- saved asset appears in the gallery without page reload

## Phase 5: Add simple guided controls

### Goal

Prove parameterized breadth beyond raw JSON while remaining intentionally narrow.

### Main changes

- add schema inspection utilities
- add lightweight guided controls for simple top-level fields
- add explicit fallback messaging when schema complexity exceeds MVP guided support

### File ownership

- `frontend/src/components/Svg/TesserStudio/schema.ts`
- `frontend/src/components/Svg/TesserStudio/TesserInputEditor.tsx`
- `frontend/src/components/Svg/panels/TesserStudioPanel.tsx`

### Exit criteria

- simple scripts can be configured without writing JSON
- complex scripts still run through JSON mode

## Phase 6: Validation pass against representative scripts

### Goal

Prove the MVP against diverse real scripts, not just the happy path.

### Main changes

- validate at least a defined representative set
- patch rough edges only if they improve generality rather than overfitting one script

### File ownership

- likely no new permanent file required
- optional QA note in docs if useful

### Exit criteria

- selected scripts run successfully from the frontend
- no per-script frontend rewrites were required

## Proposed Ticket Breakdown

## Ticket 1: Audit Tesser completed-job payload and decide save path

### Scope

- inspect enqueue/status response fields
- confirm whether completed SVG markup is directly available for `/svgs` create
- document the decision in the MVP plan or implementation notes if needed

### Owner

- shared Tesser/frontend integration area

### Dependencies

- none

### Definition of done

- implementation team knows whether MVP can save directly from frontend

## Ticket 2: Create shared `tesserService.ts`

### Scope

- add service methods for:
  - `listTesserScripts`
  - `getTesserScriptHelp`
  - `enqueueTesserScript`
  - `getTesserJobStatus`
- update `demoService.ts` to delegate instead of owning duplicated Tesser request logic

### Owner

- Area A

### Dependencies

- Ticket 1 only if payload naming needs to be clarified first

### Definition of done

- one shared service layer exists for Tesser API access

## Ticket 3: Add `useTesser` and `useTesserJob` hooks

### Scope

- query keys
- scripts query
- help query or on-demand loader
- enqueue mutation
- job polling query hook

### Owner

- Area A

### Dependencies

- Ticket 2

### Definition of done

- any UI can consume Tesser operations through hooks instead of raw service calls

## Ticket 4: Add minimal `TesserStudioPanel` with JSON-only input

### Scope

- panel shell
- script dropdown
- help/details surface
- JSON textarea
- run button
- in-session jobs list

### Owner

- Area B

### Dependencies

- Ticket 3

### Definition of done

- a user can run at least one Tesser script from the SVG page without touching the demo surface

## Ticket 5: Register `TesserStudioPanel` in the SVG surface

### Scope

- add panel config
- choose panel prominence and placement
- keep layout consistent with existing SVG shell behavior

### Owner

- Area D

### Dependencies

- Ticket 4

### Definition of done

- `Tesser Studio` is visible and accessible in the SVG page

## Ticket 6: Add save-to-library flow for completed jobs

### Scope

- create private SVG asset from completed job
- attach provenance metadata
- refresh gallery cache

### Owner

- Areas B and C

### Dependencies

- Ticket 1
- Ticket 4
- Ticket 5

### Definition of done

- completed jobs can be saved and appear in the SVG gallery

## Ticket 7: Add simple guided input mode

### Scope

- guided controls for simple top-level schema properties
- mode switch between `Guided` and `JSON`
- fallback handling for unsupported schemas

### Owner

- Area B with support from Area A for types/schema helpers

### Dependencies

- Ticket 4

### Definition of done

- the panel supports both approachable guided input and broad JSON fallback

## Ticket 8: Validate representative script set

### Scope

- identify script sample set
- run through the frontend
- capture any generic improvements required

### Owner

- cross-cutting MVP validation

### Dependencies

- Ticket 6
- Ticket 7 ideally, though JSON-only validation can begin earlier

### Definition of done

- MVP breadth is demonstrated against multiple real scripts

## Recommended First Sprint

If we want the fastest path to a meaningful proof, the first sprint should include:

1. Ticket 1
2. Ticket 2
3. Ticket 3
4. Ticket 4
5. Ticket 5

That yields a working frontend Tesser surface in the SVG page before save-to-library and before guided controls.

The second sprint should include:

1. Ticket 6
2. Ticket 7
3. Ticket 8

That closes the MVP product loop and validates breadth.

## Review Boundaries

To keep review quality high, each PR should stay within one ownership area where possible.

### Good PR boundaries

- service extraction only
- hooks only
- panel UI only
- save-to-library only
- guided controls only

### Bad PR boundaries

- service extraction plus full panel plus schema controls in one change
- backend helper route plus frontend refactor plus validation fixes in one change unless the backend route is proven necessary

## Notes For Future Expansion

This sequence intentionally preserves a clean follow-on path to:

- Node Editor integration
- Room/Demo/Project reuse
- richer schema support
- curated per-script editors
- persisted work-in-flight artifacts

None of those should require rethinking the shared Tesser access layer if the early tickets are implemented cleanly.
