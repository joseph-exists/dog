Reuse the shared content stack in [ContentRenderer.tsx](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx), [registry.ts](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/registry.ts), and [pluginRegistry.ts](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/pluginRegistry.ts). The repo viewer should continue to wrap that stack, not fork it.

The repo product boundary remains:

- once intake has happened, the platform repo is the product object
- upstream source metadata is retained as import record / audit context, not as a live sync relationship
- the frontend should not present an active upstream linkage model
- direct forge semantics should remain backend-owned

## Current State

The following repo-viewer foundations now exist:

1. Shared repo content layer
   - `frontend/src/components/Repo/content/` provides `RepoContentRenderer`, repo content metadata, and adapters that normalize repo blob payloads into shared `ContentRenderer` inputs.
   - `CodeHighlight` is still reused rather than cloned.

2. Repo panel and block registry
   - `frontend/src/components/Repo/registry.ts` defines active repo panel kinds and repo block types with capability requirements.
   - The first concrete blocks are oriented around platform ownership:
     - `repoMetadata`
     - `repoImportSummary`
     - `repoImportRecord`
     - `repoFailureDiagnostics`

3. Registry-backed repo detail layout
   - [repo.$repoId.tsx](/home/josep/dog/frontend/src/routes/_layout/repo.$repoId.tsx) now renders through repo panel definitions instead of a one-off detail layout.
   - `repoOverview` and `repoImportStatus` are real panels.
   - `repoExplorer` and `fileViewer` exist as real panel implementations.
   - the route now reads backend capability data from `repo.capabilities` rather than hardcoding all viewer capabilities off.
   - however, the viewer panels still need to be fully moved onto the user-repo endpoints and payload shapes.

4. Multi-instance-safe panel config
   - `repoExplorer` and `fileViewer` both support per-instance `config_json`.
   - Panel config currently supports:
     - independent `title`
     - `entity_type`
     - `entity_id_source`
     - `initial_path` for explorers
     - `path_mode` / `fixed_path` for file viewers
     - `selection_key` for shared or isolated file selection
     - panel-specific display controls such as size badges and copy affordances
   - `selection_key` is now honored in rendering, which means multiple explorer/viewer instances can cooperate or stay isolated intentionally.

5. Local repo layout editing
   - The repo detail route now includes a minimal repo layout editor dialog.
   - It supports:
     - duplicate panel kinds with unique IDs
     - cloning panel instances
     - editing prominence and size values
     - editing raw `config_json`
     - hiding panels without deleting their draft config
   - Layout customizations are persisted locally for now, not saved through backend entity layout APIs.

6. Shared primitive upgrades already in place
   - [BlockContainer.tsx](/home/josep/dog/frontend/src/components/Page/primitives/BlockContainer.tsx) has already been generalized with richer chrome, toolbar, loading, empty, and error states.
   - That should remain the base container for repo blocks rather than introducing a repo-only fork.

7. Backend viewer contract is now present
   - backend has shipped:
     - `GET /user-repos/{id}/tree`
     - `GET /user-repos/{id}/file`
     - `GET /user-repos/{id}/readme`
     - `default_branch` on repo payloads
     - `capabilities` envelope on repo payloads
     - preview flags on file/readme payloads
   - the remaining work is frontend adoption, not backend architecture definition

## Demo Review Takeaways Still Applicable

The review of demo artifacts remains directionally correct:

1. Use demo patterns as references, not product code.
   - [GitViewBlock.tsx](/home/josep/dog/frontend/src/components/Demo/blocks/GitViewBlock.tsx)
   - [FileExplorerBlock.tsx](/home/josep/dog/frontend/src/components/Demo/blocks/FileExplorerBlock.tsx)
   - [DemoBuilderPreview.tsx](/home/josep/dog/frontend/src/components/Demo/builder/DemoBuilderPreview.tsx)

2. Keep repo visibility backend-owned.
   - tree listings
   - file/blob payloads
   - commit/history metadata
   - search results

3. Keep authoring schema-driven.
   - the repo builder scaffolding should continue following the demo schema/capability model instead of drifting into bespoke forms

4. Treat preview fidelity as important.
   - repo builder preview should render through the actual repo panel/block renderers wherever possible
   - lightweight layout/preset previews should use repo-owned label/color mappings rather than generic room/page panel names

## Revisions To Upcoming Work

What changed after implementation:

1. Multi-instance support is no longer hypothetical.
   - `repoExplorer` and `fileViewer` must be treated as repeatable panel types with instance-local config, not singleton workspace concepts.
   - Future work should assume users may want:
     - two file viewers with different fixed paths
     - multiple explorers scoped to different paths
     - shared-selection explorer/viewer pairs
     - isolated review panes with separate `selection_key` values

2. The next frontend priority is not another generic layout abstraction.
   - The current gap is viewer integration and payload normalization, not panel instance modeling.
   - backend affordances now exist, so the next slice is to activate the actual viewer surfaces.

3. Builder work should proceed in two tracks, not one:
   - panel-layout authoring, which now exists in minimal form and should gain reorder/schema-aware controls
   - block authoring/composition, which still needs to be built for repo surfaces

4. Persistence should stay phased.
   - local storage is acceptable for the current alpha iteration
   - backend entity-typed panel persistence is still a later step
   - do not block repo builder/viewer iteration on generic `usePanels(entityType, entityId)` work

## Updated Implementation Order

1. Finish frontend viewer activation against the shipped user-repo endpoints.
   - update `repoExplorer` and `fileViewer` to use `UserReposService`, not `ShadowReposService`
   - normalize tree/file/readme payloads through the repo content layer
   - expose backend preview flags and branch/default-branch context in the viewer chrome
   - stabilize route-level capability normalization
2. Add first-class README rendering and README-aware default composition.
   - make `repoReadme` a real runtime surface instead of a registry placeholder
   - decide whether README is a block in overview, a dedicated panel, or both
3. Add schema-aware repo panel editing on top of the current layout editor.
   - move beyond raw `config_json` editing for explorer/viewer-specific fields
   - prepare config for branch-aware fields without requiring a later redesign
4. Implement the first additional registry-backed repo blocks inside panels:
   - `repoReadme`
   - `repoFileStats`
   - `repoRecentFiles`
   - `repoCommitSummary` when commit data exists
5. Add repo builder block editing and composition tree visibility.
6. Add repo builder preview routed through real repo panel/block renderers.
7. Generalize persistence from local repo layout storage to backend-backed entity layouts.
8. Add richer repo engagement panels once backend supports them:
   - search
   - history
   - activity

## Backend Handoff

The backend-facing checklist for activating repo viewer reads lives in:

[user-repo-viewer-backend-handoff-checklist.md](/home/josep/dog/backend/app/services/service-docs/user-repo-viewer-backend-handoff-checklist.md)

That checklist now reflects shipped backend scope and remaining adoption work. It covers:

- `user_repo` tree/blob endpoint wiring
- repo-ID-native route patterns
- route-level capability exposure
- README endpoint availability
- product-facing `ref` semantics
- README resolution expectations
- multi-instance explorer/viewer compatibility
- validation cases for real imported repos

## Frontend Constraints The Backend Should Assume

1. The frontend is already prepared to render multiple explorer/viewer instances at once.
   - shared selection depends on `selection_key`
   - isolated instances depend on per-panel `config_json`

2. The frontend prefers platform entity identity over forge identity.
   - repo ID is the safest primary identity
   - forge IDs and URLs should remain secondary metadata

3. The frontend can render tree/blob responses immediately once user-repo capability wiring exists.
   - no further major frontend architecture change is required to start using those endpoints

4. The frontend should not be forced to reverse-engineer Git behavior.
   - if branch/ref/history is intentionally reduced or rewritten, the backend should expose product-facing semantics directly

## Critical Next Slice

The next most critical implementation slice is frontend viewer activation and normalization.

This is primarily concentrated in:

- [RepoLayoutEditorDialog.tsx](/home/josep/dog/frontend/src/components/Repo/Dialogs/RepoLayoutEditorDialog.tsx)
- [RepoContentRenderer.tsx](/home/josep/dog/frontend/src/components/Repo/content/RepoContentRenderer.tsx)
- [registry.ts](/home/josep/dog/frontend/src/components/Repo/registry.ts)
- [repo.$repoId.tsx](/home/josep/dog/frontend/src/routes/_layout/repo.$repoId.tsx)
- [repos.tsx](/home/josep/dog/frontend/src/routes/_layout/repos.tsx)

Why this slice is critical:

1. The route has started consuming backend capabilities, but the panel implementations are still shaped around the earlier shadow-repo assumptions.
2. The new backend payloads include README and preview metadata, but the repo content layer and renderer chrome do not yet treat those fields as first-class.
3. The layout editor can duplicate explorer/viewer panels, but it still edits opaque JSON rather than the actual viewer contract fields the backend now exposes.
4. The registry/default composition has not been revised to take advantage of README/default-branch/capability-backed viewer surfaces.
5. The repo list route should start reflecting viewer readiness more clearly, since repos can now be both import-ready and viewer-capable.

What this slice should accomplish:

1. Make the repo viewer actually use the user-repo backend contract end to end.
2. Make README and preview-state rendering first-class.
3. Make panel defaults and panel editing match the real viewer contract.
4. Leave branch-aware extension points in place without blocking v1 on full branch UI.

## Preview Config Reuse

Repo panel layout previews now use repo-specific preview config from:

- [previewConfig.ts](/home/josep/dog/frontend/src/components/Repo/panels/previewConfig.ts)

This file currently exports:

- `REPO_PANEL_PREVIEW_LABELS`
- `REPO_PANEL_PREVIEW_COLORS`

These mappings are passed into the shared preview primitives:

- [MiniPreview.tsx](/home/josep/dog/frontend/src/components/Page/primitives/MiniPreview.tsx)
- [PresetPicker.tsx](/home/josep/dog/frontend/src/components/Page/primitives/PresetPicker.tsx)
- [InteractivePreview.tsx](/home/josep/dog/frontend/src/components/Page/InteractivePreview.tsx)

When repo blocks and block-layout previews are introduced, engineers should follow the same pattern:

1. Add repo-block preview labels/colors in a repo-owned preview config module rather than hardcoding them in shared Page primitives.
2. Pass those mappings into shared preview components as overrides.
3. Keep shared preview components generic and cross-feature; keep repo naming/color semantics inside `frontend/src/components/Repo/`.

This keeps repo preview language coherent across:

- preset buttons
- lightweight panel-layout dialogs
- future block-layout previews
- future builder preview chrome
