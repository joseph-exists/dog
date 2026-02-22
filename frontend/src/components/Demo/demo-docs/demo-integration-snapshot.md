# Demo Integration Snapshot
> **Status:** Source of truth for current implementation + forward plan  
> **Date:** 2026-02-21  
> **Supersedes:** `frontend/src/components/Demo/demo-docs/todo-alpha.md`, `backend/app/api/demo_page_mapping_spec.md`

## Purpose
This document unifies:
- product goals from `demo-scaffolding-v2.md`
- backend contract reality
- frontend route/shell reality
- concrete next engineering steps

Use this as the single planning + execution artifact for the next demo integration slice.

## Goals (from scaffolding-v2, normalized)
1. Demos are composition-driven, not route-hardcoded.
2. Each user gets an isolated runtime room per demo config.
3. DemoShell renders blocks + panels from backend composition contracts.
4. Runtime policy and persona policy are data-driven.
5. Theming and presentation cascade through the same page/theme binding model used elsewhere.

## Current State (Implemented)

### Backend
1. `DemoConfig` and `DemoSession` models are restored in `backend/app/models.py`.
2. `POST /demos/{slug}/session` resolves or creates per-user `DemoSession` and room.
3. CRUD and route wiring for demo config/session is active in:
- `backend/app/crud_demo.py`
- `backend/app/api/routes/demos.py`
4. Composition schema models now exist in `backend/app/models.py`:
- `DemoPageComposition*`
- `UserDemoPageCompositionOverride*`
- `ResolveDemoEntryPayload` and related runtime/room context models.

### Frontend
1. `demo.$slug` resolves session via `DemoService.resolveSessionForSlug(slug)`.
2. Demo room anchor is session-based (`demoSession.roomId`), not static config room.
3. Route handles distinct states:
- demo resolve loading/error
- room loading/error
- runtime autostart in-flight/missing/error
4. Demo panels are pulled from panel service (`getResolvedPanels("demo", roomId)`), not legacy local static demo config.
5. DemoShell includes theme picker controls and cascades page/cards theme bindings.

## Derisking Update (Client Exports Confirmed)
1. Generated demo client exports are available and validated in:
- `frontend/src/client/schemas.gen.ts`
- `frontend/src/client/types.gen.ts`
- `frontend/src/client/sdk.gen.ts`
2. This means schema/contract definition work is complete for this slice.
3. Remaining work is integration-only:
- backend route payload wiring
- frontend route/shell consumption
- panel/block composition rendering coverage

## Current Gaps (Blocking Full Compositionality)

### API Contract Gap
1. Route still returns `ResolveDemoSessionResponse` at `POST /demos/{slug}/session`, not `ResolveDemoEntryPayload`.
2. Composition models are defined but not yet served by demos route.
3. No composition CRUD endpoints yet:
- no `/demos/{id}/composition` `GET/PUT/PATCH`
- no user override endpoints.

### Composition Runtime Gap
1. `demo.$slug.tsx` still performs orchestration client-side by separate queries:
- resolve session
- fetch room
- fetch runtime
- fetch panels
2. Blocks are not yet first-class in DemoShell rendering path.
3. DemoShell takes `panels: PanelConfig[]` (render-ready) instead of a typed `DemoPageComposition` input model.

### Panel/Block Capability Gap vs Demo Types A-D
1. `storyRuntime`, `chat`, `content` are integrated in route mapping.
2. `participantPanel`, `a2ui`, `canvas`, `storyEditor`, `debug` are not yet fully wired in the current demo route mapping.
3. Context/story/roster/tool/contribution blocks are modeled but not rendered from composition in current demo shell flow.

## Decisions Locked In
1. Per-user runtime isolation: keep using `DemoSession.room_id` as room anchor.
2. Runtime bootstrap policy default: auto-start demos when room has a story attached.
3. No legacy/backport support: migration can proceed with clean contract cutover.

## Next Engineering Steps (Integration Only, Shortened)
1. Backend integration: return `ResolveDemoEntryPayload` from `POST /demos/{slug}/session`.
2. Backend integration: resolve composition with precedence:
- user override
- demo config composition
- type defaults
3. Backend integration: expose composition CRUD endpoints:
- `GET /demos/{demo_config_id}/composition`
- `PUT /demos/{demo_config_id}/composition`
- `PATCH /demos/{demo_config_id}/composition`
4. Frontend integration: refactor `demo.$slug.tsx` to consume generated typed payloads directly and remove redundant multi-query orchestration where possible.
5. Frontend integration: update `DemoShell` input contract to accept composition-driven blocks/panels/runtime/presentation models.
6. Frontend integration: wire block rendering first (`context`, `content`), then finish panel mapping coverage (`participantPanel`, `a2ui`, `canvas`, `storyEditor`, `debug`).

## Definition of Done for This Slice
1. Demo route renders from resolved backend composition contract, not local recomposition.
2. Top content/context can be authored as block data and appears consistently above runtime panels.
3. Session room isolation and autostart policy still work under the new payload.
4. QA can create and validate one demo with:
- a top constant content block
- a story runtime panel
- a chat panel bound to the same session room.

## Notes for Product + QA
1. Demo creation should be treated as “config + composition + session resolve”, not as “custom route code”.
2. A/B demos are closest to done once composition payload is route-native.
3. C/D demos depend mostly on panel/block wiring depth, not on new core primitives.
