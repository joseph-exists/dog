Scope
Implement demo runtime/story/chat integration for `/_layout/demo/$slug` using registry-driven panel composition and entity-aware services.
Do not mirror to `d.$d_Id.tsx` in this slice.

Plan Update (Registry + PanelService Path)

1. Prerequisite alignment (before route refactor)
- Extend `panelService` to support `entityType: "demo"` in `PanelEntityType`.
- Add `demo` branch handling in `getResolvedPanels` and related functions, or explicitly document that demo route uses DemoConfig defaults until backend panel endpoints for demo exist.
- Confirm demo route pattern in entity registry is canonical (`/demo/:slug` vs `d/:slug`) and align `entityTypes.ts` to actual router paths.
- Ensure canonical panel kinds for demo are registry kinds (`chat`, `storyRuntime`, `content`, etc.), not ad-hoc local aliases (`story`, `content-renderer-demo`).

2. Remove local panel JSON normalization from `demo.$slug.tsx`
- Delete local helpers (`toString`, `toNumber`, `toObject`, `normalize*`, `parsePanelSpecs`).
- Replace with one of:
  - `panelService.getResolvedPanels("demo", entityId)` when demo panel resolution is wired; or
  - typed DemoConfig panel payload mapped directly by registry kind, without normalization heuristics.
- Keep route responsible only for data orchestration, not schema repair.

3. Route orchestration in `demo.$slug.tsx`
- Keep `DemoRoute` for `resolve-session` query and loading/error states.
- In `ResolvedDemoRoute`, fetch room metadata by `resolved.demoSession.roomId` (`RoomService.getRoom` or `useRoom`).
- Derive `roomStoryId`, `roomTitle`, and `canWrite` from room + participant state.
- Pass these to panel renderers, especially story runtime panel.

4. Story panel contract update
- Update `DemoStoryPanel` props to include `roomTitle?: string | null` and `canWrite?: boolean`.
- Pass `roomStoryId`, `roomTitle`, and `canWrite` through to `StoryPanel`.
- Keep synthetic auto-respond messaging optional and isolated from runtime state authority.

5. Runtime bootstrap behavior
- In `ResolvedDemoRoute`, inspect runtime via `useRoomRuntime(roomId)`.
- If `roomStoryId` exists and runtime is missing, present explicit start action (or one-shot auto-start if policy allows and required persona inputs exist).
- Guard bootstrap to avoid repeated retries/loops.

6. Chat/runtime cohesion
- Keep shared anchor as `roomId` for both `useRoomMessages` and `useRoomRuntime`.
- Preserve WebSocket invalidation behavior for `room.runtime.*` and room messages.
- Do not encode runtime truth in synthetic chat text.

7. Loading/error UX and verification
- Distinguish: demo resolve failure, room fetch failure, runtime not initialized.
- Keep hook order stable (query wrapper + resolved child component pattern).
- Validate with frontend build and manual flow:
  - resolve demo session
  - room metadata loads
  - story runtime panel sees attached story
  - chat and runtime operate on same room.
