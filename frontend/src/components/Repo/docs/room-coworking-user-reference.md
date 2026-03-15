# Room Repo Co-Working User Reference (Browser Guide)

Audience: UX, Product, Design  
Scope: current implemented behavior (`repoExplorer` + `fileViewer` in Rooms)

## What You Can Validate Today

- Repo panels can be added to a Room via **Panel Layout**.
- `Repo Explorer` and `File Viewer` can be bound to a `user_repo`.
- Selection can be shared across panels (and across users) using `selection_key`.
- Room events are emitted for repo actions (`selection`, `open`, `ref`) and sync to other viewers in the same Room.

## Prerequisites

1. Sign in to the app.
2. Have at least one imported `user_repo`.
3. Have (or create) a Room.

## Step 1: Get a Repo ID

1. Open `/repos`.
2. Open a repository.
3. Copy the repo UUID from the URL `/repo/{repoId}`.

## Step 2: Open a Room

1. Go to `/rooms`.
2. Open an existing room, or create one.
3. Confirm you are on `/r/{roomId}`.

## Step 3: Add Repo Panels

1. In the Room header, open the `...` menu.
2. Click **Panel Layout**.
3. In **Add Panel**, add:
   - `Repo Explorer`
   - `File Viewer`
4. Click **Save**.

## Step 4: Bind Panels to a Repo

1. Re-open **Panel Layout**.
2. In **Repo Panel Bindings**:
   - Set `repo_id` for `Repo Explorer` to the UUID from Step 1.
   - Set `repo_id` for `File Viewer` to the same UUID.
3. For shared local behavior, set both panels to the same `selection_key` (example: `shared.main`).
4. For `File Viewer`, use:
   - `selection` mode (recommended) for shared open-file behavior.
   - `fixed` mode for pinned file view.
   - `readme` mode for README-only.
5. Click **Save**.

## Step 5: Validate Single-User Behavior

1. In `Repo Explorer`, click files in the tree.
2. Confirm `File Viewer` updates when `path_mode=selection` and keys match.
3. Change branch/ref context by navigating repo content and confirm viewer footer updates with `Ref ...`.

## Step 6: Validate Multi-User Co-Working

1. Open the same Room in a second browser window (or second user session).
2. In window A, select/open a file in `Repo Explorer`.
3. In window B, confirm shared panel state updates (for matching `selection_key`).
4. Repeat in reverse direction.

## Step 7: Validate Room + Agent Workflow

1. Keep `Chat` and `Participants` panels in the room.
2. Add at least one agent from `Participants`.
3. Use chat and repo panels in the same session to confirm repo panels do not block normal room/agent interactions.

## Expected Error States (Current UX)

- Missing binding: `No repository binding found for this panel...`
- Repo load failure: `Failed to load bound repository for this panel.`
- Invalid capability envelope: `Repository capability flags are missing or invalid for this panel.`

These are intentional explicit states for operator/developer visibility.

## Current Limitations

UNKNOWN IF TRUE: Room-level repo attachment is not yet a fully explicit/stable typed contract; panel-level `repo_id` is the reliable setup path.
UNKNOWN IF TRUE: Runtime cadence controls for repo events are not yet exposed (current behavior is direct roomstream sync/invalidation).
UNKNOWN IF TRUE: Story-wide import of repo panel kinds is not fully enabled yet (room path is primary for this feature).
- Presence details (who selected what) are not yet represented as dedicated cursor/presence UX.

## Recommended Demo Script (5 Minutes)

1. Open Room with `Chat + Participants + Repo Explorer + File Viewer`.
2. Bind both repo panels to same `repo_id` and `selection_key`.
3. Select files in explorer and show viewer updates.
4. Open same Room in second window and show live shared selection change.
5. Trigger agent chat flow to show repo co-working and agent collaboration can coexist in one Room.
