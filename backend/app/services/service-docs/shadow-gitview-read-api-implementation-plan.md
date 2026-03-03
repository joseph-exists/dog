# Shadow GitView Read API Implementation Plan

## Objective

Implement v1 shadow-repo read APIs and wire `GitViewBlock` to consume them through backend-authorized transforms only.

This plan is specifically for `shadow` repos. It does not deprecate, replace, or reduce the importance of `user` repos. `user` repos remain a required parallel feature track for future platform functionality.

## Fixed Product Decisions

- `shadow` repos are the first integration target.
- `user` repos remain intact and out of scope for deprecation or removal.
- The frontend never talks to Gogs directly.
- Gogs credentials are never exposed to the client.
- Gogs is fully opaque to users and agents.
- The backend authorizes requests using platform credentials and entity-level access rules.
- Unauthorized shadow repo access returns opaque `404`.
- All shadowed entity types are in scope for v1 viewing.
- File content is required for v1.
- Branch switching is deferred to v2.

## Current State Assessment

### Infrastructure

- `gittin` is now a real persistent Gogs deployment with stable org-based repo structure.
- The documented taxonomy is:
  - `shadow/*` for backend-managed internal repos
  - `dog/*` for user-associated platform repos
- Shadow repo naming is intended to be immutable and deterministic.

### Backend

- `shadow_gogs_service.py` can look up and create shadow repos in Gogs when configured.
- `shadow_service.py` currently treats remote provisioning as best-effort and continues local shadow enqueue even when Gogs provisioning fails.
- `user_repo_service.py` already provides a separate provisioning path for user-visible repos in the `dog` org.
- `shadow_read_service.py` already exists as a likely anchor point for projection-oriented read logic, but there is not yet a repo-view read contract exposed to the frontend.

### Frontend

- `GitViewBlock.tsx` is currently a static config renderer.
- `DemoGitViewBlockSpec` is currently just `config_json`, with no typed live-data contract.
- There is no backend-driven Git read path wired into the demo runtime yet.

## Architectural Direction

The platform should expose shadow repo state as an authorized application projection, not as a forge client.

The client should request repo view data by application entity identity. The backend should:

1. resolve the shadow repo for the requested entity
2. authorize the caller against platform rules for that entity
3. read repo state from backend-managed storage
4. return normalized Git view DTOs

The client should receive only application-level data such as:

- repo summary
- default branch
- recent commits
- file tree
- file content

The client should never receive:

- Gogs URLs
- Gogs tokens
- Gogs org assumptions
- direct forge credentials

## V1 Scope

### Included

- View shadow repo summary for any supported entity type
- View default branch
- View recent commits
- View file tree
- View file content
- Opaque `404` on unauthorized or unavailable access
- Backend-only authorization and repo data retrieval
- GitViewBlock live mode backed by backend APIs

### Excluded

- Branch switching
- Diffs beyond what is needed for initial summary
- Any write actions
- Any client-visible forge metadata
- Any restructuring or removal of user repo flows

## API Contract Direction

### Resource Identity

The client should address repo state by entity identity:

- `entity_type`
- `entity_id`

This keeps authorization aligned with application objects rather than repo host concepts.

### Proposed DTOs

#### `ShadowRepoSummary`

- `entity_type`
- `entity_id`
- `repo_available`
- `default_branch`
- `latest_commit_sha`
- `latest_commit_message`
- `latest_commit_authored_at`

#### `ShadowRepoCommitSummary`

- `sha`
- `short_sha`
- `message`
- `author_name`
- `authored_at`

#### `ShadowRepoTreeEntry`

- `path`
- `name`
- `entry_type` (`file` or `directory`)
- `size_bytes` optional

#### `ShadowRepoFileContent`

- `path`
- `ref`
- `content`
- `encoding`
- `size_bytes`
- `content_type` optional

#### `ShadowRepoViewResponse`

- `summary`
- `commits`
- `tree`
- `tree_root_path`
- `ref`

### Proposed Endpoints

#### `GET /api/v1/shadow-repos/{entity_type}/{entity_id}/view`

Returns:

- repo summary
- recent commits
- tree for the default path

Query params:

- `path` optional
- `ref` optional, but v1 may ignore anything other than the default branch
- `commit_limit` optional

#### `GET /api/v1/shadow-repos/{entity_type}/{entity_id}/file`

Returns:

- normalized file content for the requested path

Query params:

- `path` required
- `ref` optional, defaulting to the default branch

### Authorization Behavior

- resolve access entirely on the backend
- if caller is not allowed to view the entity’s shadow repo, return `404`
- if repo is absent or unreadable in a way that should not leak existence, return `404`
- reserve `500` for real server faults only

## Backend Design

### Service Layer

Add a dedicated projection-oriented read service for repo views.

Suggested new service:

- `shadow_repo_view_service.py`

Responsibilities:

- resolve `ShadowRepo` by entity identity
- normalize repo reads into API DTOs
- provide:
  - repo summary
  - recent commits
  - file tree
  - file content

Data source priority:

1. backend-managed local shadow git state
2. existing shadow repo metadata as needed
3. remote Gogs data only if necessary for internal coordination, never as the exposed read model

### Authorization

Add a single authorization function or policy helper:

- `can_view_shadow_repo(entity_type, entity_id, actor)`

Requirements:

- support all shadowed entity types in v1
- rely on platform entity visibility/ownership rules
- stay independent of Gogs concepts

### Routing

Add shadow repo read endpoints under a dedicated router, with:

- typed response models
- auth dependency for current actor
- opaque `404` behavior

### Client Generation

After endpoint models and routes are in place:

- regenerate frontend client types
- use generated SDK methods in the GitViewBlock fetch path

## Frontend Design

### Block Contract

Evolve `DemoGitViewBlockSpec` from generic snapshot config to support live backend mode.

V1 should support both:

- legacy snapshot mode for existing demos
- live shadow mode for new or migrated demos

Suggested live config fields:

- `source: "shadow_repo"`
- `entity_type`
- `entity_id`
- `initial_path` optional
- `commit_limit` optional
- `show_file_content` optional

### GitViewBlock Behavior

In live mode, `GitViewBlock` should:

- fetch repo view from backend
- render recent commits
- render tree entries
- fetch file content when a file is selected
- show loading, empty, and not-found states

In v1, it should not expose branch switching controls.

### Demo Runtime Integration

The demo runtime should pass through the block config needed for live mode without exposing any forge details.

Likely touchpoints:

- `rendererRegistry.tsx`
- `GitViewBlock.tsx`
- any demo route runtime helper that resolves block data

## Concrete Task List

### Backend: API Models

1. Add typed shadow repo read DTOs in the backend models/schema layer.
2. Keep DTOs scoped to summary, commits, tree, and file content.
3. Avoid any Gogs-specific fields in public responses.

### Backend: Authorization

1. Define `can_view_shadow_repo(entity_type, entity_id, actor)`.
2. Implement support for all entity types currently shadowed by the platform.
3. Standardize opaque `404` responses for unauthorized access.

### Backend: Read Service

1. Create `shadow_repo_view_service.py`.
2. Add methods:
   - `get_repo_view(...)`
   - `get_tree(...)`
   - `get_file_content(...)`
3. Read from backend-managed git state, not direct client-visible Gogs APIs.
4. Normalize output into DTOs.

### Backend: Routes

1. Add `GET /api/v1/shadow-repos/{entity_type}/{entity_id}/view`.
2. Add `GET /api/v1/shadow-repos/{entity_type}/{entity_id}/file`.
3. Attach current-user auth dependencies.
4. Return opaque `404` where required.

### Backend: Tests

1. Add authorization tests for all entity types.
2. Add view endpoint tests for:
   - successful repo view
   - missing repo
   - unauthorized access returning `404`
   - file content fetch
3. Add service tests for summary, commits, tree, and file reads.
4. Ensure tests do not break or modify user repo provisioning coverage.

### Frontend: Client and Types

1. Regenerate the frontend API client after backend endpoints exist.
2. Introduce typed live-config support for `GitViewBlock`.
3. Preserve legacy snapshot config compatibility during rollout.

### Frontend: GitViewBlock

1. Refactor `GitViewBlock.tsx` to support:
   - legacy snapshot mode
   - live backend mode
2. Add data fetching for repo summary and tree.
3. Add file selection and file content loading.
4. Render loading, empty, and not-found states.
5. Do not add branch switching in v1.

### Frontend: Demo Integration

1. Update the renderer path to pass live block config through cleanly.
2. Validate that demo compositions can opt into live shadow mode without breaking old demos.
3. Add or update unit coverage for `gitView` rendering behavior.

## Recommended Delivery Sequence

1. Define DTOs and endpoint contracts.
2. Implement authorization helper for all entity types.
3. Build the backend read service.
4. Ship read-only shadow repo endpoints.
5. Add backend tests.
6. Regenerate frontend client.
7. Refactor `GitViewBlock` for live mode with legacy fallback.
8. Add frontend tests.
9. Migrate one demo composition to prove the live path end to end.

## Non-Goals and Guardrails

- Do not remove, merge, or weaken `user` repo infrastructure.
- Do not expose Gogs details to the client.
- Do not make shadow repo reads depend on direct forge access from the browser.
- Do not add branch switching until the v1 read path is stable.

## Exit Criteria for V1

V1 is complete when:

1. a logged-in user can open a demo containing a live `GitViewBlock`
2. the block loads shadow repo summary, recent commits, tree, and file content from backend APIs
3. unauthorized callers receive opaque `404`
4. no Gogs credentials or forge URLs are exposed to the client
5. existing `user` repo services and flows remain unchanged
