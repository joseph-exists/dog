> Deprecated: moved to `frontend/src/components/Demo/demo-docs/demo-integration-snapshot.md` as the consolidated source of truth.

`DemoPageComposition` can be the creator-facing blueprint plus runtime policy contract.

Use it as the single object that answers: “what does this demo render, and how should it behave?”

## How it fits

`DemoConfig` today is template metadata + defaults.  
`DemoPageComposition` should become the normalized, validated structure for:
1. blocks (top context/content)
2. panels (chat/story/participant/content/etc.)
3. layout (order, prominence, viewport)
4. policies (runtime auto/manual, persona strategy)
5. presentation/theming bindings

Then `resolve-session` can return:
- `demo_config`
- `demo_session`
- `demo_page_composition` (fully resolved)

Frontend stops reconstructing composition locally.

## Demo creator operations (contract-level)

1. **Create demo shell record**
- `createDemoConfig(slug, title, scope, ...)`

2. **Attach composition**
- `setDemoComposition(demoConfigId, composition)`
- Backend validates panel kinds/block types/layout references.

3. **Publish/activate**
- optional `publishDemoConfig` / `setActive` if you want draft vs live.

4. **Preview/resolve**
- creator calls `resolveDemoSessionForSlug(slug)` and gets resolved composition + session room.

5. **Iterate**
- `patchDemoComposition(...)` for partial edits (panel reorder, block content update, policy changes).

6. **Clone**
- `cloneDemoConfig(sourceId, newSlug)` copies composition and metadata for quick variants.

## What creators can change via composition

1. **Panels**
- Add/remove supported kinds (`storyRuntime`, `chat`, `participantPanel`, `content`, etc.)
- Set prominence/order/sizing/viewport mode
- Per-panel options payload (typed union by kind)

2. **Blocks**
- Add static/dynamic context blocks
- Place “constant top content” as a block (solves your product ask cleanly)
- Node-aware blocks later via typed dynamic sources

3. **Policies**
- `runtimePolicy`: `auto | manual | owner_only`
- `personaPolicy`: `first_available | fixed | prompt_on_enter`
- `chatMode`: `participant | observer`

4. **Presentation**
- Theme bindings + optional per-demo overrides (page/cards/headers surfaces)

## Why this enables demo creation better

1. UI, CLI, and seed scripts all write the same contract.
2. Product can define “demo types A/B/C/D” as composition presets.
3. QA can test against one schema instead of route-specific behavior.
4. Frontend becomes renderer-only for composition, not composition author.

## Suggested API surface

1. `POST /demos` create config
2. `PUT /demos/{id}/composition` replace full composition
3. `PATCH /demos/{id}/composition` partial updates
4. `GET /demos/{id}/composition` read draft/live composition
5. `POST /demos/{slug}/session` returns resolved session + resolved composition

If you want, next step is drafting a concrete `DemoPageComposition` schema (with typed `PanelSpec`, `BlockSpec`, `RuntimePolicy`) that aligns with your existing Page registries.


OLDER:

You’re right on the diagnosis. The main gap is not primitives, it’s contracts.

**Current State: A/B Coverage**
1. **Demo A (chat room) is only partially enabled**
- Enabled: room-anchored chat + websocket stream in `frontend/src/routes/_layout/demo.$slug.tsx`.
- Missing: participant-focused composition (no `ParticipantPanel` wiring in demo route panel mapping), observer/participant mode contract, stable context block above chat.

2. **Demo B (story pause/replay) is mostly enabled**
- Enabled: `storyRuntime` panel mapped to `DemoStoryPanel` -> `StoryPanel`, room runtime hooks, auto-start policy.
- Missing: explicit metadata/context block contract and viewer-mode story state contract (not debug-oriented presentation model).

**Core Problem**
- `DemoShell` currently takes pre-rendered panels only, not a full page composition model.
- Page constructs exist (`PageShell`, `usePageEditor`, block registry, panel registry), but demo flow does not consume a shared “page composition contract”.

References:
- `frontend/src/components/Demo/DemoShell.tsx`
- `frontend/src/routes/_layout/demo.$slug.tsx`
- `frontend/src/components/Page/PageShell.tsx`
- `frontend/src/hooks/usePageEditor.ts`

---

## Contract-First Next Step (recommended)

Define these contracts before more feature wiring:

1. **DemoRoute Loader Contract** (outside `DemoShell`)
- Must resolve and pass:
  - `demoConfig`, `demoSession`
  - `roomContext` (`roomId`, `storyId`, `title`, `canWrite`)
  - `runtimeContext` (`hasRuntime`, `isStarting`, `policy`, `status`)
  - `themeContext`
  - `composition` (`panels`, `blocks`, `layout`)
- This becomes the single source of truth for route state branches.

2. **DemoShell Input Contract**
- `DemoShell` should accept structured data, not ad-hoc props:
  - `headerModel`
  - `blocksModel`
  - `panelsModel`
  - `statusModel` (loading/error/banner states)
- Today it has only `demoConfig + panels + theme + autoRespond`; extend to composition-aware input.

3. **Panel Runtime Context Contract**
- Every panel render function should receive the same context object:
  - `{ roomId, storyId, canWrite, autoRespond, runtimeStatus }`
- This removes panel-specific prop drift and lets A/B/C/D compose cleanly.

4. **Block Composition Contract**
- Add explicit block schema for demo pages (top-level context block, story metadata block, etc.).
- Back it with `PageService` entity model (`entityType: "demo"`) so blocks are persisted, not route-hardcoded.

5. **Runtime Policy Contract**
- Move “auto-start all demos” from route logic into policy field (likely demo metadata), e.g.:
  - `runtimePolicy: "auto" | "manual" | "owner_only"`
- Route enforces policy; shell/panels only render state.

---

## Concrete Engineering Steps (next sprint)

1. Create `DemoPageComposition` type in a shared service module.
2. Implement `DemoCompositionService.getComposition(slug)` that aggregates:
- demo resolve
- room context
- runtime status/policy
- panel config
- block layout/content
3. Refactor `demo.$slug` to consume only that service output.
4. Update `DemoShell` props to accept composition contracts (header/blocks/panels/status).
5. Add first block contract (`ContextBlock`) and render it above panel layout.
6. Add `ParticipantPanel` contract path for Demo A using existing Page/Room panel primitives.


