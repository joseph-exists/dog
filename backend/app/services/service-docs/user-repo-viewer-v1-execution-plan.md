# User Repo Viewer V1 Execution Plan

## Goal

Activate the existing repo viewer frontend for platform-managed user repos by adding backend-only, authorized tree/blob/README reads and route-level capability metadata.

## Scope

V1 implementation order:

1. `user_repo_view_service.py`
2. `GET /user-repos/{id}/tree`
3. `GET /user-repos/{id}/file`
4. capability fields on `UserRepoPublic`
5. `GET /user-repos/{id}/readme`

## Product Semantics

- User repos are the product object.
- The client never sees Gogs URLs, repo host tokens, or forge internals.
- Reads are authorized by platform repo access rules only.
- V1 shared access rule:
  - owner always has access
  - superuser always has access
  - non-owner platform users may read repos where `is_private == false`
- Tree/blob/README reads operate against the repo default branch.
- `ref` is accepted as an optional query parameter for branch-aware forward compatibility.
- In v1, only the default branch is supported. Any other `ref` returns branch-not-found.

## Contract Additions

Add response models for:

- `UserRepoViewerCapabilities`
- `UserRepoSummary`
- `UserRepoViewResponse`
- `UserRepoFileContent`
- `UserRepoReadmeContent`

Extend:

- `UserRepoPublic` with `default_branch` and `capabilities`
- `ShadowRepoFileContent`-style payloads with preview flags:
  - `is_binary`
  - `is_truncated`
  - `truncation_reason`
  - `is_unsupported_preview`

## Service Design

Create `backend/app/services/user_repo_view_service.py`.

Responsibilities:

- resolve repo by platform `repo_id`
- authorize repo access
- fetch repo metadata from Gogs
- fetch tree entries from Gogs contents API
- fetch file blobs from Gogs contents API
- resolve README server-side using deterministic root-path precedence
- normalize Gogs payloads into platform DTOs

Implementation constraints:

- stateless per request
- no local clone reads
- no persisted selection state
- no forge URLs or tokens returned to the client

## Route Additions

Extend `backend/app/api/routes/user_repos.py` with:

- `GET /user-repos/{repo_id}/tree`
- `GET /user-repos/{repo_id}/file`
- `GET /user-repos/{repo_id}/readme`

Also update:

- `GET /user-repos/{repo_id}` to include capability metadata
- `GET /user-repos/` to include capability metadata for listed repos

## Error Policy

Security-sensitive failures:

- repo missing
- repo unauthorized

Return opaque `404`.

V1 non-security failures:

- unsupported branch/ref
- path/file kind mismatch
- file too large / truncated
- unsupported preview
- backend unavailable

May use explicit HTTP status and message bodies without final launch-stable error coding yet.

## Test Plan

Add route tests covering:

- owner can read tree/file/readme
- superuser can read private repos
- non-owner can read non-private repos
- non-owner gets opaque `404` for private repos
- branch-not-found on unsupported `ref`
- file endpoint returns preview flags
- README endpoint resolves canonical root README
- `GET /user-repos/{id}` includes capability metadata

Mock Gogs-facing service calls in route tests rather than requiring live Gogs.

## Notes

- Branch listing/history/search/activity remain v2.
- README resolution should be implemented in a way that can later support LICENSE and similar canonical files.
