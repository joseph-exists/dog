# User Repo Viewer Backend Handoff Checklist

## Purpose

This checklist covers the backend work required to activate the current repo viewer frontend for platform-managed user repos.

Current frontend status:

- repo detail route is registry-backed
- `repoExplorer` and `fileViewer` panels already exist
- both panels support multiple instances with per-panel `config_json`
- both panels are still capability-gated in the frontend route, but backend user-repo tree/blob/readme reads are now wired and available

The goal of this checklist is to move those panels from placeholder state into real tree/blob rendering without requiring another frontend architecture pass.

## Product Constraints

- Treat platform-managed user repos as the product object.
- Do not require direct frontend knowledge of Gogs internals.
- Do not require frontend inference of raw Git semantics the backend does not guarantee.
- Upstream source metadata may be retained as import/audit record, but the viewer should operate on the platform repo state.


## UPDATES

  - The checklist says “support user_repo as a valid entity type for repo tree/view reads,” :use the pattern: repo-ID-native routes like /user-repos/{id}/tree and /user-repos/{id}/file  
  
  -  user_repo_service.py gives ownership and provisioning context, note that shared/collaborative access is a first-class requirement of v1.
  
  - Error semantics will be revised after v1 prior to launch based on feedback.
  
  - README resolution is required for v1, and the pattern will be extended rapidly with LICENSE and others.

## Current Status

Backend shipped:

- `GET /user-repos/{id}` now returns `default_branch` and a `capabilities` envelope.
- `GET /user-repos/{id}/tree` is implemented.
- `GET /user-repos/{id}/file` is implemented.
- `GET /user-repos/{id}/readme` is implemented.
- user-repo reads are backend-authorized and Gogs remains opaque to the client.
- read responses are branch-aware in shape and accept optional `ref`.
- v1 shared access is implemented as:
  - owner access
  - superuser access
  - non-owner access when `is_private == false`
- preview flags are present on file/readme payloads:
  - `is_binary`
  - `is_truncated`
  - `truncation_reason`
  - `is_unsupported_preview`
- targeted backend route tests pass.

Remaining work before the frontend benefits from this:

- [ ] update [frontend/src/routes/_layout/repo.$repoId.tsx](/home/josep/dog/frontend/src/routes/_layout/repo.$repoId.tsx) to use `repo.capabilities` instead of hardcoded capability flags
- [ ] wire `repoExplorer` and `fileViewer` panels to the regenerated client endpoints
- [ ] decide final launch error semantics and error-code stability

## Checklist

### 1. Enable user-repo tree reads

- [x] Support repo reads through repo-ID-native user-repo routes.
- [x] Support entity lookup by platform repo ID.
- [x] Owner-user-ID lookup is not supported for viewer reads.
- [x] Owner-user-ID lookup is rejected by omission; routes are repo-ID-native only.
- [x] Authorization is enforced through platform repo rules, not forge assumptions.

> **[Review Comment]:** The existing `shadow_repo_view_service.py` provides a proven pattern here. It uses `authorize_shadow_repo_read()` with `current_user_id` + `is_superuser` checks, returning opaque 404 on denial. A parallel `user_repo_view_service.py` following this pattern is the cleanest path. The key difference: user repos live under `dog/` org in Gogs and use `gogs_repo_name` for path resolution rather than the `{entity_type}/{entity_id}` structure shadow repos use.

Frontend dependency:

- `repoExplorer` panel config already supports:
  - `entity_type`
  - `entity_id_source`
  - `initial_path`
  - `selection_key`

### 2. Define the user-repo tree response contract

- [x] Return the current requested path.
- [x] Return an effective `ref` or revision label for the tree view.
- [x] Return tree entries with:
  - `entry_type`
  - `path`
  - `name`
  - optional `size_bytes` for files
- [x] Return enough top-level summary metadata for explorer header chrome.
- [x] Include latest commit summary data for badge/header support.

> **[Review Comment]:** The existing `ShadowRepoViewResponse`, `ShadowRepoTreeEntry`, and `ShadowRepoCommitSummary` models in `models.py` (lines 5229-5260) already define this contract for shadow repos. Consider reusing these DTOs directly with a `UserRepoViewResponse` alias, or creating parallel `UserRepo*` models if the response shape must diverge (e.g., user repos may expose branch names while shadow repos intentionally hide them).

Behavior checklist:

- [x] Root path listing works.
- [x] Nested directory listing works.
- [x] Nonexistent path returns a backend error.
- [x] Requesting tree view for a file path returns a backend error.
- [x] Unauthorized repo access is denied at the backend.

> **[Branch-Awareness Note]:** Even in v1 single-branch mode, accept `ref` as an optional query parameter. If omitted, default to `main`. This makes the endpoint branch-ready without requiring frontend changes when branching is enabled. Example: `GET /user-repos/{id}/tree?path=src&ref=main`

### 3. Enable user-repo blob/file reads

- [x] Support blob/file reads via repo-ID-native user-repo routes.
- [x] Support blob lookup by platform repo ID.
- [x] Blob authorization follows platform repo access rules.

> **[Review Comment]:** The shadow repo file endpoint uses `git show {ref}:{path}` via subprocess, which naturally handles path validation (git rejects traversal attempts). For user repos, never read from the local clone in `volumes/shadows` - always call the Gogs API. While local reads are faster and avoid network latency, Gogs API reads are authoritative, secure, and will rapidly become the only source of truth. Local-first with the same `git show` pattern will not work once we segment our user-repo GOGS away from our internal shadow-repo GOGS.

Frontend dependency:

- `fileViewer` panel config already supports:
  - `entity_type`
  - `entity_id_source`
  - `path_mode`
  - `fixed_path`
  - `selection_key`
  - display controls such as path badge and copy button

### 4. Define the user-repo blob/file response contract

- [x] Return `path`.
- [x] Return textual content when the file is renderable as text.
- [x] Return `content_type` or mime type.
- [x] Return effective `ref` or revision identifier.
- [x] Return `size_bytes`.

Strongly preferred flags:

- [x] Explicit binary-file signal.
- [x] Explicit truncated / too-large signal.
- [x] Explicit unsupported-preview signal.
- [x] Encoding metadata when relevant.

Reason:

- Without these flags, the frontend must infer too much about previewability and payload safety.

> **[Review Comment]:** Current `ShadowRepoFileContent` model returns `content`, `encoding`, `size_bytes`, and `content_type` but lacks the binary/truncated/unsupported flags. This is a gap in the shadow repo implementation too. Extend the base model with: `is_binary: bool = False`, `is_truncated: bool = False`, `truncation_reason: str | None = None`. The service layer can detect binary via `\x00` in first 8KB, and enforce a max preview size (e.g., 1MB) with truncation signaling as a config tuneable.

### 5. Expose route-level capability availability

The repo detail route currently hardcodes viewer capabilities as unavailable.

- [x] Expose `hasFileTree` availability for the current repo/user.
- [x] Expose `hasBlobContent` availability for the current repo/user.
- [x] Expose `hasCommitHistory` availability when history endpoints exist.
- [x] Expose `hasSearch` availability when search endpoints exist.
- [x] Expose `hasBranches` availability when branch listing is supported.
- [x] Expose a unified capability envelope on `UserRepoPublic`.

> **[Branch-Awareness Note]:** Include `hasBranches: false` in v1 capabilities. When branching is enabled, flip to `true`. Frontend can use this to conditionally render branch selector UI. Also include `default_branch: "main"` in the capability envelope so frontend always knows which branch to request.

Acceptable delivery shapes:

- repo detail metadata
- dedicated repo capabilities endpoint
- shared entity capability envelope

> **[Review Comment]:** The cleanest path is extending `UserRepoPublic` response model with a `capabilities` field. This avoids extra API calls and keeps capability discovery atomic with repo fetch. Example shape: `capabilities: { has_file_tree: bool, has_blob_content: bool, has_commit_history: bool }`. These can be derived from `import_status == "ready"` plus feature flags. This mirrors how the demo system exposes `runtimeHasRuntime` and `runtimePolicy` as capability signals.

Frontend dependency:

- the route needs capability values to decide whether to render:
  - real panel
  - capability placeholder
  - degraded partial UI

### 6. Define product-facing read semantics

Because the platform may sever upstream branch/ref history after intake, the backend must define what the viewer is reading.

- [x] Define whether tree/blob reads are from:
  - working tree snapshot
  - default branch state
  - retained repo ref state
  - synthetic platform snapshot
- [x] Define what `ref` means in tree/blob responses.
- [x] Define whether `ref` is stable, synthetic, internal, or user-facing.
- [x] Define whether commit summary data is meaningful, optional, or intentionally absent.
- [x] Define when history panels should be considered valid for user repos.

> **[Review Comment]:** Recommend: user repos read from `main` branch HEAD (matching `SHADOW_REPO_DEFAULT_BRANCH` pattern). The `ref` returned should be the literal branch name `"main"`, not a commit SHA—this keeps it user-facing and stable. Commit history *is* meaningful for user repos (unlike shadow repos which are system-generated), so history panels should be valid once `import_status == "ready"`. The key difference from shadow repos: user repo commits represent real upstream history, not synthetic snapshots.

Frontend dependency:

- the frontend will not invent Git semantics for:
  - path browsing
  - file viewing
  - commit badge display
  - history availability

### 7. Provide README resolution strategy

If the frontend is expected to render a first-class `repoReadme` block:

- [x] Expose a canonical README resolution endpoint.
- [ ] expose tree metadata that identifies README candidates, or
- [ ] guarantee enough tree/blob semantics that frontend README resolution is deterministic

Constraint:

- the frontend should not encode forge-specific README heuristics unless backend contract explicitly delegates that responsibility.

> **[Review Comment]:** Recommend a dedicated `GET /user-repos/{id}/readme` endpoint that returns the resolved README content or 404. Backend handles the resolution logic: check for `README.md`, `README`, `readme.md`, `Readme.md` in priority order at root. This keeps heuristics server-side and allows future enhancement (e.g., subdirectory READMEs, format detection) without frontend changes. Response shape can match `ShadowRepoFileContent` with an added `resolved_from_path` field.

### 8. Define error semantics usable by the viewer

- [x] Tree endpoint errors distinguish operationally between:
  - not found
  - unauthorized
  - invalid path kind
  - backend unavailable
  - branch not found (v2, but reserve error code now)
- [x] Blob endpoint errors distinguish operationally between:
  - file missing
  - unauthorized
  - binary/unsupported preview
  - payload too large
  - backend unavailable
  - branch not found (v2, but reserve error code now)
- [ ] Error responses are launch-stable enough for frontend loading/empty/error states.

> **[Branch-Awareness Note]:** Reserve `BRANCH_NOT_FOUND` as an error code now, even if v1 only supports `main`. In v1, if someone passes `ref=develop` and the endpoint accepts `ref`, return this error rather than a generic 404. This provides a clear upgrade path and avoids confusing "path not found" with "branch not found".

> **[Review Comment]:** Current shadow repo routes use opaque 404 for both "not found" and "unauthorized" (security best practice). For user repos, consider the same pattern but with structured error codes in the response body for non-security-sensitive cases. Example: `{ "detail": "Path not found", "error_code": "PATH_NOT_FOUND" }` vs `{ "detail": "File too large for preview", "error_code": "FILE_TOO_LARGE", "size_bytes": 52428800 }`. The `error_code` field gives frontend stable keys for i18n and conditional UI without parsing message strings.

### 9. Confirm multi-instance viewer compatibility

The frontend already supports multiple concurrent explorer/viewer instances.

- [x] Ensure tree/blob endpoints are safe to call concurrently for the same repo.
- [x] Ensure no backend assumption requires a single global selected path per repo.
- [x] Ensure fixed-path and selection-driven file viewers both work against the same repo.
- [x] Ensure multiple explorer panels can request different paths without backend-side session coupling.

> **[Review Comment]:** The current `shadow_repo_view_service.py` is fully stateless—each request opens a fresh git subprocess with no shared state. This pattern is inherently multi-instance safe. For user repos, maintain this statelessness: no caching of "current path" in session, no locks on repo access. The test added in `test_shadow_repos.py` for concurrent access should be replicated for user repos. Note: git itself handles concurrent reads safely via lockfiles.

### 10. Future-facing but not blocking

These are not required to activate the current viewer, but backend decisions here will affect the next frontend phase.

- [ ] Search/indexing contract for `repoSearch`
- [ ] Commit/change history contract for `repoHistory`
- [ ] Operational activity/event contract for `repoActivity`
- [ ] Entity-backed panel layout persistence for repo layouts

> **[Review Comment]:** For `repoHistory`, the existing `_list_recent_commits()` helper in `shadow_repo_view_service.py` provides a working pattern using `git log --pretty=format`.  For `repoActivity`, the platform's existing event sourcing system (`event_emitter.py`, `RoomEvent`) should be cloned to provide a `RepoEvent` type to track views, clones, and panel interactions. 

### 11. Branch support (high-potential v2 feature)

Branching is a likely first-class feature for user repos. The v1 implementation should avoid decisions that make branch support harder to add.

#### 11.1 Branch listing

- [ ] Define a branch list endpoint: `GET /user-repos/{id}/branches`
- [ ] Return branch metadata including:
  - `name` (branch name)
  - `is_default` (boolean)
  - `commit_sha` (HEAD of branch)
  - `commit_message` (latest commit summary)
  - `committed_at` (timestamp)
- [ ] Define sort order (alphabetical, last-updated, default-first)
- [ ] Consider pagination for repos with many branches

#### 11.2 Branch-aware tree/blob reads

- [x] Accept `ref` as optional query parameter on tree/blob endpoints
- [x] If `ref` is omitted, use the repo's default branch
- [x] Validate that `ref` exists as a branch before reading
- [x] Return the resolved `ref` (branch name) in all responses
- [ ] Do not expose raw commit SHAs as user-selectable refs (keep refs as branch names)

#### 11.3 Default branch metadata

- [x] Include `default_branch` in `UserRepoPublic` response model
- [x] Include `default_branch` in repo summary/capabilities response
- [ ] Ensure default branch is set during import (currently assumes `main`)

#### 11.4 Branch-specific errors

- [x] Add error case: branch not found (`BRANCH_NOT_FOUND`)
- [ ] Distinguish from path not found within a valid branch
- [ ] Consider whether nonexistent branch should return 404 or 400

#### 11.5 Frontend panel config extensibility

- [ ] Ensure `repoExplorer` config shape can accept optional `branch` or `ref` field
- [ ] Ensure `fileViewer` config shape can accept optional `branch` or `ref` field
- [ ] Define whether branch selection is per-panel or shared across panels

#### 11.6 v1 decisions that enable v2 branching

These v1 implementation choices will make branch support easier:

- [ ] Always return `ref` (branch name) in tree/blob responses, even if hardcoded to `main`
- [ ] Structure git commands to accept ref as parameter: `git show {ref}:{path}`, `git ls-tree {ref}`
- [ ] Include `default_branch` in repo metadata from day one
- [ ] Use `git branch --list` or `git for-each-ref` patterns for future branch listing
- [ ] Avoid hardcoding `main` in service layer—pass branch as parameter even if caller always passes `main`

> **[Review Comment]:** The key insight is that v1 can be single-branch while still being *branch-aware* in its implementation. By parameterizing `ref` throughout the service layer and always returning it in responses, adding branch listing and switching later becomes additive rather than requiring refactoring. The `git for-each-ref --sort=-committerdate refs/heads/` command provides branch listing with commit metadata in a single call.

## Minimum Handoff Required To Unblock Frontend

The smallest backend delivery that activates the existing viewer is:

1. support `user_repo` tree reads
2. support `user_repo` blob/file reads
3. expose route-level `hasFileTree` and `hasBlobContent`
4. define the meaning of `ref` in responses
5. verify those responses against a real imported user repo

### Branch-Readiness Additions (Recommended for v1)

These additions are small in v1 but prevent refactoring when branching is added:

6. accept optional `ref` query parameter on tree/blob endpoints (default to `main`)
7. include `default_branch` in repo metadata response
8. include `hasBranches: false` in capabilities
9. return `BRANCH_NOT_FOUND` error for invalid `ref` values
10. parameterize branch in service layer (don't hardcode `main` in implementation)

Once those are in place, the frontend can immediately validate:

- explorer panel rendering
- file viewer rendering
- shared-selection explorer/viewer pairs
- fixed-path viewer instances
- multiple concurrent panel instances

## Suggested Validation Cases

- [ ] Imported repo with small text files
- [ ] Imported repo with nested directories
- [ ] Imported repo with no README at root
- [ ] Imported repo with binary assets
- [ ] Imported repo with a large file that should not be fully previewed
- [ ] Unauthorized access attempt
- [ ] Missing path request
- [ ] Multiple simultaneous tree/blob requests for one repo

### Branch-Readiness Validation (v1 prep for v2)

- [ ] Tree/blob request with `ref=main` explicitly returns same result as omitting `ref`
- [ ] Tree/blob request with `ref=nonexistent` returns `BRANCH_NOT_FOUND` error
- [ ] Repo metadata includes `default_branch` field
- [ ] Capabilities include `hasBranches: false`
- [ ] Service layer accepts branch parameter (even if hardcoded to `main` by caller)
