# Repo x Room Co-Working Implementation Plan (Question-Driven)

## Objective

Enable more than one participant (users & agents) to co-work on repository files inside Room/Story contexts by:

- importing `RepoFileViewerPanel` into room-capable panel composition
- importing `RepoExplorerPanel` into room-capable panel composition
- wiring message/event passing from repo panels to room runtime + room stream
- preserving existing `user_repo` and `shadow_repo` behavior

## Current Baseline (Code-Observed)

- Repo panels are real, reusable components:
  - `repoExplorer`: `/home/josep/dog/frontend/src/components/Repo/panels/RepoExplorerPanel.tsx`
  - `fileViewer`: `/home/josep/dog/frontend/src/components/Repo/panels/RepoFileViewerPanel.tsx`
  - shared renderer entry: `/home/josep/dog/frontend/src/components/Repo/panels/rendererRegistry.tsx`
- Repo route already has multi-instance selection coordination via `selection_key`:
  - `/home/josep/dog/frontend/src/routes/_layout/repo.$repoId.tsx`
- Room route composes panels from backend-configured `kind` values:
  - `/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx`
- Room panel kind typing is still closed to current room/story/canvas types:
  - `/home/josep/dog/frontend/src/components/Page/registry/panelTypes.ts`
  - `/home/josep/dog/frontend/src/services/panelService.ts`
- Room stream currently invalidates known event families (runtime, messages, participants, settings), but not repo-collab events:
  - `/home/josep/dog/frontend/src/hooks/useRoomStream.ts`

## Critical Design Questions

## 1) Context + Identity Questions

- In Room, how is a repo chosen for a repo panel?

NOTE: we will need to identify the first passage - and then ensure future extensibility in that implementation through rigorous inline documentation. The repo panel object should enable the repo to be passed from multiple possible sources - both during creation at during runtime.

- Do we allow per-panel repo binding (`config_json.repo_id`) or room-level repo attachment (single source)?

we enable and allow both types.  a user who owns a room can specify that the room is attached to a specific repo (as with story attachment) and that owner - or a different user - can bring up their own panel with a different view of that same repo, or a different repo altogether.  The panel is the connective tissue (both in UX and binding) between the repo that it connects to and the room object.

- For Story context, should repo binding come from story metadata (`story_id` path preservation concern) or explicit panel config?

Story authors can pass repo bindings with the story, with a node, or otherwise.  We have to assume that panels are indiscriminate with respect to source of repo binding. If the Story being viewed/played has a default repo, the default panel should be able to accept that repo.

- Must Room support both `user_repo` and `shadow_repo`, or is Room repo-coworking `user_repo`-only for v1?

user_repo only for V1.


## 2) Panel Contract Questions

- Should room panel config remain `{ id, kind, prominence }` only, or be extended to support `config_json` like Repo route?

room panel config should be extended to support additional parameters without breaking existing functionality.  we maintain dynamicism by extending the possibility set and affordances of panels, then strictly typing their presentation and rendering.  

- If extended, do we version the room panel payload shape to preserve existing rows safely?
- Should repo panel kinds be first-class room kinds (`repoExplorer`, `fileViewer`) or wrapped inside a generic `content` panel?

repo panel kinds should be first-class room kinds.  All panel kinds in the system should eventually be interoperable - this is a V2 ideal. This is not currently possible in the system, and would be problematic to attempt during iterative design-based engineering loops.

## 3) Selection + Presence Questions

- Is `selection_key` enough for co-working intent, or do we need explicit per-user cursor/selection presence?

NOTE: selection key is enough for this implementation.

- Should selection updates be:
  - local-only (panel state)
  - persisted (room config)
  - streamed as transient room events

Note: yes. there will be different operations which will need to be classified into those buckets.  we need the ability to see how the different operations 'feel' - and which contribute to the developer experience we want to support.

- When two users click different files simultaneously, what is the expected winner model for shared viewer panels?

Note: panel-dependent setting. we need a mechanism to specify 'who wins' and 'who drives' - and which settings a room owner can override. 


## 4) Message Passing Questions (Panel -> Runtime -> Stream)

- Are repo actions represented as:
  - chat messages (`room_message.user`)
  - structured UI actions (`sendUIAction`-style)
  - dedicated repo room events (recommended for clean typing)

NOTE: Dedicated repo room events. we may need to extend some repo actions to include other operational sets, but for now, we can send these to the room itself.  

- Which user actions should emit events in v1?
  - file selected
  - file opened
  - ref changed
  - follow mode toggled

NOTE: Panel-dependent. 


- Should runtime consume repo events directly, or should runtime only react through chat/action messages?

NOTE: runtime needs to consume a 'set' of repo events directly, dependent on the panel, repo, and/or user settings.  Visual updates to one users panel (IE a shared surface) will be required very quickly after this implementation, and we can't build in a way that blocks it.  The repo panels should allow/enable runtime updates based on config tuneables.  the runtime does not need all updates that occur with a shared visualization/edit session on a file - the runtime only needs to consume those updates at specific intervals, either pre-determined or user activated.

## 5) Permission + Safety Questions

- Who can bind/change repo in a room: owner only, or all participants?
enable both settings.

- Who can broadcast shared selection changes?
enable broad, we will limit later (patterns exist, but not required for this implementation.)

- Do private repos in room require participant-level access validation before rendering file content?
No.

- What should UI do on permission mismatch: degrade panel, hide entries, or read-only with explanation?
Read only with terse explanation - only show the error message.  This shouldn't happen.

## 6) Compatibility Questions

- How do we guarantee no regression to existing `story` / `story_id` / shadow-repo behavior while adding room imports?
we run our test passes (note: these do not run within agent containers. request them to be run by human engineers.)

- Should repo panels be disabled in contexts where backend capability flags are absent, reusing current placeholder behavior?

No. the error thrown if the backend capability flag is absent should be explicit and direct, and should enable operator/developer review.


## Dimensionality Matrix (What Must Exist)

| Dimension | Required States | Notes |
|---|---|---|
| Context | `repo`, `room`, `story` | Keep additive; no model replacement assumptions |
| Repo Model | `user_repo`, `shadow_repo` | Preserve both paths explicitly |
| Panel Instance | single, multi-instance | Existing `selection_key` supports this |
| Selection Scope | local, shared-with-room, follow-leader | Needs explicit UX contract |
| Event Type | transient, persisted | Transient for live collaboration; persisted for audit only if needed |
| Event Transport | websocket roomstream, REST fallback | Roomstream first for live state |
| Conflict Model | last-write-wins, role-priority, lock-based | Decide before shared edits/follow mode |
| Permission Model | owner, member, agent | Must define who may mutate shared repo-panel state |

## Implementation Status (As of 2026-03-04)

## Track A: Shared Typed Contracts

Status: `completed`

- `PanelKind` now includes `repoExplorer` + `fileViewer`, with room-available definitions in [panelTypes.ts](/home/josep/dog/frontend/src/components/Page/registry/panelTypes.ts).
- Room panel config now supports additive typed fields (`config_json`, `entity_binding`) in [panelService.ts](/home/josep/dog/frontend/src/services/panelService.ts).
- Room panel hooks preserve and round-trip extended config payloads in [useRoomPanels.ts](/home/josep/dog/frontend/src/hooks/useRoomPanels.ts).

## Track B: Room Route Composition via Existing Repo Components

Status: `completed` (with one binding-source caveat)

- Room route now wires `repoExplorer` + `fileViewer` as first-class panel kinds in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Rendering reuses shared repo panel primitives via [rendererRegistry.tsx](/home/josep/dog/frontend/src/components/Repo/panels/rendererRegistry.tsx) (`renderRepoPanel`), no room-specific fork of panel internals.
- Room-level shared selection map keyed by `selection_key` exists in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Explicit operator-facing error surfaces exist for missing repo binding, failed repo fetch, and invalid capability envelope in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Binding resolution order is implemented (`panel config -> panel binding -> room data -> story data`) in `resolveRepoIdForRoomPanel(...)` in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).

Caveat:
- room-level attachment is only partially realized at the frontend contract level; the fallback resolver supports it, but concrete room-level repo attachment payloads are not yet a guaranteed stable source in current typed room view models.

## Track C: Panel Config Schema and Presentation-as-Data

Status: `mostly completed`

- Repo panel config parsing/defaulting remains centralized and panel-kind specific in [config.ts](/home/josep/dog/frontend/src/components/Repo/panels/config.ts).
- Room panel editor now includes repo panel add/remove + data-entry controls for `repo_id`, `selection_key`, and viewer path mode options in [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx).
- Config updates are normalized through repo config helpers (not ad hoc panel branches), preserving presentation-as-data semantics in [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Room/Dialogs/PanelLayoutDialog.tsx).

Remaining:
- promote binding-source semantics (`panel_config`, `room_attachment`, `story_default`) from implicit resolver behavior to explicit persisted policy fields in panel config/editor UI.

## Track D: Dedicated Repo Event Transport + Roomstream Handling

Status: `implemented for selection/open/ref`

- Dedicated room event emission path exists on frontend via `emitRepoEvent(...)` in [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts).
- Room route emits repo collaboration actions from repo panels:
  - `selection` on selection change
  - `open` on file open
  - `ref` on observed ref changes
  in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Roomstream now recognizes repo event families and invalidates repo panel queries in [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts).
- Roomstream event handling updates shared `selection_key` state for live remote file-selection sync in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Backend route + event mapping for dedicated repo events is in place:
  - `POST /rooms/{room_id}/repo-event` in [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py)
  - event types `room.repo.selection`, `room.repo.opened`, `room.repo.ref_changed` handled in [event_emitter.py](/home/josep/dog/backend/app/services/event_emitter.py)

Remaining:
- runtime-side cadence/tuneable consumption for repo events is not implemented yet; current behavior is stream invalidation + selection synchronization.

## Track E: Story Compatibility and Regression Protection

Status: `in progress / pending hardening`

- Room route already attempts story fallback binding when room has `story_id` in [r.$roomId.tsx](/home/josep/dog/frontend/src/routes/_layout/r.$roomId.tsx).
- Repo panel kinds are still registered for room context only (not full story context import yet) in [panelTypes.ts](/home/josep/dog/frontend/src/components/Page/registry/panelTypes.ts).
- No broad automated regression matrix has been executed here for `story` / `story_id` / `shadow_repo` compatibility.

## Revised Next Phases

1. Formalize binding policy in data contracts.
- Add explicit binding policy fields for source precedence and allowed source set.
- Persist these policy fields through panel layout save/load paths.

2. Finish room-level attachment contract.
- Add stable room-level repo attachment fields to room data contracts and resolve them without shape guessing.
- Keep panel-level `repo_id` override behavior intact.

3. Complete runtime-bridge scope.
- Define which repo event subset runtime consumes.
- Add cadence controls (interval + explicit trigger) at panel/config level.

4. Expand story context import intentionally.
- Add repo panel kinds to story-capable contexts only when story contract supports consistent repo binding.
- Preserve existing shadow-repo/demo behavior as non-regression requirement.

5. Hardening pass.
- Add coverage for config round-trip, multi-instance shared selection, repo event propagation, and explicit error states.
- Run human validation passes outside agent containers:
  - legacy room layouts
  - mixed room layouts (chat/story/repo)
  - two-client shared selection
  - story with/without default repo binding
  - invalid capability and binding states
