# Demo Testing Reference Card

Purpose: quick operational reference for QA/testing on the current `/demo/$slug` flow.

## 1) Route + Flow Branching

Entry route:
- `frontend/src/routes/_layout/demo.$slug.tsx`
- URL: `/demo/<slug>`

Primary API branch:
1. `DemoService.resolveSessionForSlug(slug)`
2. Backend `POST /api/v1/demos/{slug}/session`
3. Response contains:
   - `demo_config`
   - `demo_session`
   - `created` (`true` if new session/room created, `false` if reused)

Runtime route branches in UI:
1. `Loading demo...` (resolve pending)
2. `Demo "<slug>" not found.` (resolve 404)
3. `Unable to load demo right now.` (resolve error non-404)
4. `Loading demo room...` (room fetch pending)
5. `Demo room not found.` / room load failure
6. `Loading panels...` (panel config resolve pending)
7. Banner: `No story is attached to this demo room yet.`
8. Banner: `Story attached, but runtime is not started yet...`
9. Fully rendered shell with panels

## 2) Core Parameterization (Current)

Session anchor:
- `demo_session.room_id` is the runtime/chat anchor (per-user isolation)

Theme binding context:
- `contextKey = page:demo:<demo_config.slug>`
- Theme entity context uses:
  - `entityType = demo_session.page_entity_type`
  - `entityId = demo_session.page_entity_id`
  - `ownerId = demo_session.user_id`

Panel composition source:
- `getResolvedPanels("demo", roomId)` from `panelService`
- Current demo defaults (type defaults): `storyRuntime`, `chat`

Panel title resolution:
- `getPanelDisplayName(panel.kind)` from registry

Write permission:
- Derived from room participants:
  - user participant with role `owner` => `canWrite = true`
  - otherwise `false`

## 3) Known Objects (Current Contract)

DemoConfig:
- template-level config (slug/title/description/scope/defaults)
- source for route identity and display metadata

DemoSession:
- per-user runtime session
- includes `room_id`, `page_entity_type`, `page_entity_id`, `auto_respond`
- unique by `(user_id, demo_config_id)` in backend model

Room:
- backing collaborative container for chat + runtime
- may or may not have `story_id` attached

RoomRuntime:
- runtime projection for story execution in room context
- absent runtime is valid state (before start)

PanelConfig (resolved):
- `id`, `kind`, `prominence`
- currently rendered in Demo route for known kinds:
  - `storyRuntime`
  - `chat`
  - `content`

## 4) Composition Rules (What Can Be Composed Today)

Allowed demo panel kinds (effective today):
- `storyRuntime` (StoryPanel via DemoStoryPanel wrapper)
- `chat` (MessageList + MessageInput)
- `content` (ContentRendererDemo wrapper)

Fallback behavior:
- Unknown panel kind renders `Unsupported panel kind: <kind>`

Prominence/layout behavior:
- `primary` and `auxiliary` respected by `DemoLayout`
- optional page-sized rendering when `viewportMode === "page"` at layout level

## 5) Existing Requirements To Create a Demo (Current Path)

Minimum backend requirements:
1. Authenticated user
2. Active/visible `DemoConfig` with target `slug`
3. `POST /demos/{slug}/session` available

Minimum runtime requirements for story demo behavior:
1. Resolved `demo_session.room_id`
2. `Room.story_id` attached (if story panel should run a story)
3. Room runtime started (`PUT /rooms/{room_id}/runtime`) for non-empty runtime state

Common seed path:
- Use seed script to create/reuse demo config/session and attach story to room
- Then initialize runtime with persona/user-persona

## 6) High-Value QA Scenarios

1. Resolve existing session
- Hit `/demo/<slug>` twice as same user
- Verify second load returns reused session branch (`created = false`)

2. Per-user isolation
- Same slug from two users should produce separate `room_id` values

3. Room missing story
- Verify warning banner and story panel start behavior

4. Story attached, runtime missing
- Verify runtime-not-started banner

5. Live runtime updates
- Advance/rewind/reset in story panel and confirm runtime refreshes

6. Chat/runtime coexistence
- Send chat messages and story actions in same room without cross-breakage

7. Panel resolution fallback
- Force unsupported panel kind and verify graceful fallback message

## 7) Known Gaps / Non-Goals In Current Slice

- `demo` panel endpoints are not backend-wired like room panel endpoints; demo currently uses type-default panel resolution path in `panelService`.
- `d.$d_Id.tsx` is out of scope for this slice.
- Distinct runtime bootstrap policy (auto-start vs manual start) is not finalized globally; route currently surfaces state explicitly.
