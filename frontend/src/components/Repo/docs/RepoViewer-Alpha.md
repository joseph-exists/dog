Reuse the stack in [ContentRenderer.tsx](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/ContentRenderer.tsx), [registry.ts](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/registry.ts), and [pluginRegistry.ts](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/pluginRegistry.ts) is already generic and plugin-aware. 

Plan: build a `RepoContent` layer that wraps it, supplies repo-specific metadata/context, and registers repo-oriented renderers only where needed. Cloning now would fork code highlighting, MDX/markdown behavior, and plugin lifecycle for no gain.

The main constraint is panel configuration. `PanelLayoutDialog` and the panel service are still room-centric: [PanelLayoutDialog.tsx](/home/josep/dog/frontend/src/components/Page/Dialogs/PanelLayoutDialog.tsx), [panelService.ts](/home/josep/dog/frontend/src/services/panelService.ts), and [useRoomPanels.ts](/home/josep/dog/frontend/src/hooks/useRoomPanels.ts) only persist real layouts for `room`, with `story`/`demo` mostly defaulted and no `repo` support. 

Plan:

1. Reuse `ContentRenderer` and `CodeHighlight` as shared infra.
   Add `frontend/src/components/Repo/content/` with:
   - a `RepoContentRenderer` wrapper
   - repo plugin registration/bootstrap
   - repo render helpers that normalize file/blob/readme payloads into existing `Content` shapes
   - initial rule: use existing formats (`code`, `markdown`, `text`, `json`, `image`) before inventing new ones
   - extend existing formats immediately as necessary to support operations.

2. Extend renderer behavior through metadata, not format explosion.

   
`ContentFormat` is backend-generated in [types.ts](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/types.ts). Until the backend exposes more content formats, repo-specific needs like filename, diff mode, binary/large-file state, and path breadcrumbs should live in `metadata.options` or a repo wrapper type. 

`CodeHighlight` in [CodeHighlight.tsx](/home/josep/dog/frontend/src/components/Page/primitives/ContentRenderer/components/CodeHighlight.tsx) can then be enhanced for:

   - filename/header chrome
   - copy/download affordances
   - large-file guardrails
   - diff line styling if we later support diff payloads

3. Generalize `BlockContainer` instead of replacing it.
   [BlockContainer.tsx](/home/josep/dog/frontend/src/components/Page/primitives/BlockContainer.tsx) is too simple for repo browsing. 
   

   It needs a second-generation API for:
   - loading, empty, and error states
   - toolbar slots for path controls, view toggles, actions
   - optional sticky header
   - density variants
   - height policies for browser-style blocks
   - status chrome for async/importing states
   
   I would evolve this primitive rather than fork it, because repo blocks and page blocks both need the same container semantics.

4. Separate repo panels from repo blocks.
   Panels should be workspace-level views:
   - `repoExplorer`
   - `fileViewer`
   - `repoOverview`
   - `repoImportStatus`
   - `repoSearch`
   - `repoActivity`
   Blocks should be embeddable summaries inside those panels:
   - README block
   - source/provenance block
   - import status block
   - repo metadata block
   - file stats block
   - recent files block
   - failure diagnostics block

   Use panels for navigation and mode switching; use blocks for composable information surfaces.

5. Add a repo panel registry, but do not wire full persistence until backend supports it.

   The existing panel registry in [panelTypes.ts](/home/josep/dog/frontend/src/components/Page/registry/panelTypes.ts) should be generalized to include `repo` context and repo panel kinds. The route can consume static/default `PanelConfig` immediately, but user-customizable PanelLayout should wait until there is a generic `usePanels(entityType, entityId)` flow and backend support for repo layouts. Otherwise we build controls the user cannot actually save.

Phase the repo viewer by backend reality.
   Current repo backend supports list/detail/import status. Rich browser features like tree/blob/readme/history/search need more endpoints. So:

   - Phase 1: overview/status/provenance panels and blocks on current API
   - Phase 2: file tree + blob viewer using shared content renderer
   - Phase 3: saved panel layouts and richer engagement views

My recommendation is to implement the infra in this order:

1. `RepoContentRenderer` wrapper + repo content adapters
2. `BlockContainer` generalization for richer block chrome
3. repo panel registry/default `PanelConfig`
4. overview/import-status panels on current API
5. browser/file-view panels once repo content endpoints exist
6. generalized panel persistence for `repo`

If you want, I can take the next step by drafting the concrete `RepoContentRenderer` and repo panel/block type definitions in code.