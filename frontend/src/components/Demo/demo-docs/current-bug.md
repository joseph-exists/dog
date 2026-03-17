Status: resolved on 2026-03-17

Issue
- Demo creation for `compositionJRepoExplorerDualViewers` and `compositionKParallelRepoClusters` failed with `extra_forbidden` validation errors on panel `options`.
- The failing shapes were repo-aware `gitView` / `fileExplorer` / `fileViewer` panel configs.

Root cause
- The persisted demo contract in `backend/app/models.py` only exposed `options.extras` for `gitView` and `fileExplorer`.
- `fileViewer` was not part of the persisted panel union, and `fileViewer` block was not part of the persisted block union.
- The frontend builder and runtime had already advanced to repo-aware panel authoring, so the generated client validators lagged the actual authoring model.

Fix
- Expanded persisted demo panel option models for:
  - `gitView`
  - `fileExplorer`
  - `fileViewer`
- Added persisted `fileViewer` panel and block support to the demo composition contract.
- Regenerated the frontend OpenAPI client from the updated backend models.
- Removed the temporary frontend persistence guard in the demo builder.
- Restored the repo templates to use first-class `fileExplorer` / `fileViewer` panels instead of the temporary `gitView` workaround.

Files
- `backend/app/models.py`
- `frontend/openapi.json`
- `frontend/src/client/*`
- `frontend/src/routes/_layout/demo-builder.tsx`
- `frontend/src/components/Demo/builder/templates/compositions/compositionJRepoExplorerDualViewers.ts`
- `frontend/src/components/Demo/builder/templates/compositions/compositionKParallelRepoClusters.ts`

Verification
- Regenerate client from current backend source, not a stale running container.
- Run `npm run build` in `frontend`.
- Create demos from templates J and K and confirm they persist without 422 validation errors.
