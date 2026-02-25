# Demo Integration Snapshot
> **Status:** Source of truth for current implementation + remaining delta  
> **Last Revised Date:** 2026-02-24  

> Planning ownership: use `frontend/src/components/Demo/demo-docs/current-key-priorities.md` for milestone sequencing and handoff decisions. This file remains the integration reality checkpoint.


## Purpose
This document is the active integration checkpoint for demos. It distinguishes:
1. what is already implemented and verified in code
2. what remains to reach the desired A/B/C/D demo outcomes

Use this as the planning and execution artifact for the next demo integration slice.

## Desired Outcomes 
1. Demo routing is composition-native and entity-aware.
2. Session resolution returns room/runtime/composition context without frontend recomposition drift.
3. DemoShell can render block + panel compositions with demo-aware theming/presentation.
4. Demo creator flow is contract-first:
- create config
- attach/patch composition
- resolve preview/session
- iterate without route-specific code
5. Demo types A/B/C/D can be expressed as composition presets, not bespoke route logic.

## Verified Current Status

### Backend
1. `POST /demos/{slug}/session` returns `ResolveDemoEntryPayload`.
2. Config composition CRUD is live:
- `GET /demos/configs/{demo_config_id}/composition`
- `PUT /demos/configs/{demo_config_id}/composition`
- `PATCH /demos/configs/{demo_config_id}/composition`
3. Composition resolution precedence is implemented:
- user override record (when enabled)
- config composition
- type defaults fallback
4. Resolve payload includes:
- `composition`
- `composition_source`
- `room` context
- `runtime` context
5. Per-user session isolation via `DemoSession.room_id` remains intact.

### Frontend
1. `demo.$slug` consumes `ResolveDemoEntryPayload` directly via generated SDK types.
2. Route maps panels from `resolved.composition.panels` (composition-first render path).
3. Route maps blocks by region from `resolved.composition.blocks`.
4. Runtime policy is enforced in route (`auto`, `manual`, `owner_only` behavior).
5. Theme bindings and picker controls are wired in DemoShell and inherited through page/cards scopes.
6. Authored content rendering path is active:
- `panel.options.content_json` for `content` panels
- `block.content_json` for `content`/`context` blocks
- invalid payloads are handled with non-fatal fallback cards
- hidden blocks are filtered and block ordering is respected

## Completion Matrix

### Fully Complete for This Slice
1. Session payload contract cutover to `ResolveDemoEntryPayload`.
2. Backend config composition CRUD endpoints.
3. Route-native use of resolved composition data.
4. Top-level block rendering path for all active block kinds:
- `content`
- `context`
- `story`
- `storyMetadata`
- `agentRoster`
- `orchestratorState`
- `toolCapability`
- `contributionFeed`
- `gitView`
- `fileExplorer`
5. Session room isolation + autostart policy guardrails.
6. Content rendering migration from showcase/demo content to authored composition payloads.
7. Registry-based panel/block mapping in demo route with explicit fallback handling for unknown kinds.

### Extended: Complete
1. Panel coverage:
- wired for active scope: `storyRuntime`, `chat`, `content`, `participantPanel`, `canvas`, `a2ui`, `storyEditor`, `debug`, `storyPlayer`
- deferred compatibility kinds remain on fallback path: `storyPlayerPanel`, `strange`
2. DemoShell contract:
- supports block regions and mapped panel configs
- still takes render-ready panel props, not a single composition/view-model contract

### Not Yet Complete
1. User override management endpoints (read/write for per-user composition override lifecycle).

2. Contract-level creator operations for clone/publish flows 



## Pre-existing Delta (Prioritized)

### COMPLETE: Delta 1: Tighten DemoShell Contract
1. Move from ad-hoc prop bundle toward a structured composition input model (`header`, `blocks`, `panels`, `status`).
2. Keep current behavior stable while introducing adapter layer for compatibility.
3. Make route simpler by reducing panel-specific prop drift and repeated context plumbing.

### Delta 2: COMPLETE:  Validate Renderer + Acceptance Behavior
(see demo-testing-references folder for the wonderful implementation)
1. Add renderer tests for registry selection, unknown-kind fallback, and visibility mode behavior.
2. Add QA evidence for A/B/C compositions using current active panel/block mappings.
3. Add targeted checks for runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `contributionFeed`) and agent-coupled blocks (`agentRoster`, `toolCapability`).
NOTE: Demo D delta requirement deferred from this plan.

### Delta 3: Close Creator-Flow Contract Gaps
1. Add user override API surface if per-user composition edits are in scope for this slice.
2. Decide whether clone/publish is required now or deferred; keep core path as:
- create config
- attach composition
- resolve session
- iterate via patch

## Definition of Done (Updated)
1. `POST /demos/{slug}/session` remains the single route-native entry payload consumed by `demo.$slug`.
2. QA can validate at least one composition that includes:
- top context/content block
- `storyRuntime` + `chat` on same isolated room
3. QA can validate full active panel mapping set:
- `storyRuntime`, `chat`, `content`, `participantPanel`, `canvas`, `a2ui`, `storyEditor`, `debug`, `storyPlayer`
4. QA can validate active block mapping set with dedicated renderers:
- `storyMetadata`, `agentRoster`, `orchestratorState`, `toolCapability`, `contributionFeed`, `gitView`, `fileExplorer`
5. DemoShell continues to render composition-driven themes, blocks, and panels without local recomposition.

## Notes
1. (deprecated, moved to legacy)`todo-alpha.md` remains historical context but is no longer the active tracker.
2. (moved to demo-docs/legacy and revised)`demo-scaffolding-v2.md` remains the product/experience target map; this file tracks integration reality against it.
3. (deprecated, integrated)`frontend/src/components/Demo/fix-broken-content.md` is now treated as completed implementation context for authored content rendering and guardrails.
