Our end goal is enabling users to create and manage platform-owned repositories through our interfaces.

Today, the backend already supports one important slice of that product:

- users can import external repositories
- imported repos are represented as `UserRepo` records owned by a platform user
- imported repos can be viewed through platform-authorized repo viewer endpoints
- imported repos can be attached to other product surfaces such as projects

The next phase is extending that model so users can also create empty repos, update repo metadata and policy through our APIs, and eventually archive or delete repos without exposing direct forge ownership.

## Current Shape: Intentional vs Transitional

Before refactoring, it is important to separate the deliberate architectural choices from the parts that appear to be implementation drift.

### Intentional structure we should preserve

1. Provisioning and viewing are split into separate backend services.

- [`backend/app/services/user_repo_service.py`](/home/josep/dog/backend/app/services/user_repo_service.py) is the lifecycle/provisioning boundary.
- [`backend/app/services/user_repo_view_service.py`](/home/josep/dog/backend/app/services/user_repo_view_service.py) is the read/view boundary.

This split is useful and appears intentional. It gives the rest of the backend a clean distinction between:

- operations that create or synchronize platform-managed repos in Gogs
- operations that authorize and project repo contents into product-facing DTOs

2. The backend, not Gogs, is the system of record for authorization and product semantics.

- User-visible repos live under the platform-managed `dog` org.
- Repo names are backend-generated.
- The client does not receive forge credentials or direct forge ownership.
- Read access is authorized through platform rules, not Gogs assumptions.

This is the right model for future collaboration, ownership mapping, and policy enforcement.

3. The view service is intentionally stateless and `READY`-gated.

- Tree/file/README reads only operate on repos whose `import_status` is `READY`.
- Non-ready repos are treated as unavailable for content reads.
- The service does not persist selection state or rely on local clone state.

That shape is aligned with the viewer docs and should remain intact unless product semantics change.

### Transitional structure we should treat cautiously

1. Creation orchestration currently exists in two paths.

- The API route in [`backend/app/api/routes/user_repos.py`](/home/josep/dog/backend/app/api/routes/user_repos.py) validates import input, derives naming, creates the DB row, and enqueues the async outbox job.
- [`clone_user_repo_from_external_source()` in `backend/app/services/user_repo_service.py`](/home/josep/dog/backend/app/services/user_repo_service.py) performs synchronous create-and-provision behavior.

This is probably a result of the API moving from synchronous provisioning to async outbox-based provisioning while preserving earlier service behavior and tests. We should not break either path casually, but we also should not assume this duplication is a final architectural requirement.

2. The route currently reaches into private helper methods on the provisioning service.

- `_normalize_source_repo_url()`
- `_derive_slug_from_source_url()`
- `_derive_display_name_from_source_url()`

This works, but it is a signal that creation orchestration is not yet fully modeled as a stable service API.

## Current Affordances for the Rest of the Backend

The existing structure is still providing real value to dependent code.

### `user_repo_service.py`

Current affordances:

- normalizes source URLs into a constrained import contract
- derives stable platform naming from upstream repo URLs
- persists backend-owned repo metadata
- exposes an idempotent provisioning primitive via `ensure_user_repo_remote()`
- synchronizes remote metadata back onto `UserRepo`

This is useful because other backend code does not need to know whether a repo already exists remotely. It can ask the service to ensure that the platform repo is present and synchronized.

### `user_repo_view_service.py`

Current affordances:

- resolves repos by platform repo ID
- applies platform authorization rules
- hides forge internals from callers
- converts Gogs responses into platform DTOs
- exposes route-facing capability metadata

This is useful because route handlers and future dependent services can consume a stable product contract without coupling themselves to raw Gogs API behavior.

## Creation Status

At the service-layer lifecycle level, repo creation is now complete enough to support both imported repos and empty repos under the same readiness contract.

Implementation decision:

- `import_status = READY` means the platform-managed repo has been successfully provisioned and synchronized, not only that an upstream import completed
- `imported_at` is retained as the existing field name, but is now treated as the timestamp when the repo became ready for use
- this applies to both imported repos and empty repos created directly by the platform

Implication:

- a successfully provisioned empty repo is now a first-class `UserRepo`
- viewer operations can treat imported and non-imported repos consistently once provisioning succeeds
- dependent services can rely on the same readiness invariant for either creation path

## Immediate Design Focus

We should keep the provisioning/view-service split and use it as the basis for repo management work.

The `READY` transition contract has now been clarified and implemented.

### Completed decision

[`ensure_user_repo_remote()` in `backend/app/services/user_repo_service.py`](/home/josep/dog/backend/app/services/user_repo_service.py) provisions two classes of repos:

- imported repos, where `source_repo_url` is present
- empty repos, where `source_repo_url` is absent

The service now treats successful remote provisioning as the condition for `READY`, regardless of whether the repo came from upstream import or empty creation.

### Why this mattered

If empty repos are meant to be first-class user repos, they should satisfy the same product-level invariants as imported repos once provisioning succeeds:

- the platform repo exists remotely
- Gogs metadata has been synchronized
- the repo is available for viewer operations
- dependent services can treat it as usable

### Result

- remote metadata sync remains the same
- `READY` is now a shared lifecycle state for all usable user repos
- the repo-creation concern at this level of abstraction is complete

### Next task

Review current operational capacity for repo writes: specifically adding, updating, and removing files through backend-controlled commits directly to `main`.

## Follow-on Work

After the `READY` contract is clarified, we can extend the service layer to cover management operations beyond import and view:

- commit file changes directly to the default branch through backend-controlled write APIs
- repo creation without upstream import
- repo metadata updates such as rename, description, and privacy
- reprovision/retry flows
- archive/delete behavior
- ownership and collaboration rules built on internal user/group/project structures

## Write Path Decision

We will implement user-repo writes through backend-controlled git operations, with Gogs used as the remote of record.

Chosen model:

- backend clones or fetches the target repo from Gogs
- backend checks out the target branch, initially `main`
- backend writes or removes files in the worktree
- backend creates a git commit
- backend pushes the commit back to the Gogs remote

MVP transport choice:

- use HTTP Git against the existing `gittin` deployment
- authenticate `git clone` / `git push` with dedicated service-account credentials
- keep the existing REST API token flow for Gogs API calls
- defer SSH service-key transport until a later phase if it is still needed

What this means:

- we are not depending on an undocumented Gogs REST endpoint for file mutations
- Gogs remains the authoritative remote host for user repos
- platform policy, authorization, and mutation semantics remain enforced in our backend service layer

Immediate implications for service design:

- add a write-oriented service boundary alongside current provisioning and view concerns
- define a commit request contract for file upsert/delete operations
- define optimistic concurrency and stale-head behavior
- define author/committer policy for backend-generated commits
- define local clone/worktree lifecycle and cleanup strategy

Near-term design target:

- a backend service API that can apply one or more file mutations and commit them directly to `main`

## Proposed Write Service Contract

The write path should begin with a single service-layer method that owns the full mutation flow for a user repo.

Proposed method:

- `commit_user_repo_changes(...)`

Proposed inputs:

- `session`: database session
- `repo_id`: platform `UserRepo.id`
- `actor_user_id`: platform user performing the change
- `branch`: branch name, initially expected to be `main`
- `mutations`: one or more file mutations to apply in a single commit
- `commit_message`: required commit message
- `expected_head_sha`: required optimistic concurrency guard

Proposed mutation shape:

- `path`: normalized repo-relative path
- `operation`: `upsert` or `delete`
- `content`: required for `upsert`, absent for `delete`
- `encoding`: default `utf-8`

Initial semantics:

1. Resolve and authorize the target `UserRepo`.
2. Require the repo to already be `READY`.
3. Resolve the current HEAD SHA of the requested branch from Gogs.
4. If `expected_head_sha` does not match current HEAD, reject with a concurrency error.
5. Materialize a local clone or worktree for the repo.
6. Fetch and check out the target branch.
7. Apply all requested file mutations.
8. Reject a no-op change set.
9. Create a single commit for the full mutation set.
10. Push back to Gogs.
11. Return the new HEAD SHA and commit summary.

Why one method is the right starting point:

- supports both single-file edits and multi-file commits
- keeps git/Gogs details out of routes and higher-level services
- makes optimistic concurrency explicit
- creates one clear place to enforce path safety, content limits, and commit policy

## Proposed Result Contract

The service should return a small, explicit result object.

Suggested fields:

- `repo_id`
- `branch`
- `previous_head_sha`
- `new_head_sha`
- `commit_message`
- `committed_at`
- `changed_paths`

## Proposed Error Contract

The service should use explicit backend exceptions rather than overloading generic runtime errors.

Suggested error cases:

- repo not found
- repo not writable / unauthorized
- repo not ready
- unsupported branch
- stale head / optimistic concurrency failure
- invalid path
- invalid mutation payload
- empty or no-op commit
- git checkout/fetch/push failure
- remote push conflict

## Deliberate Initial Constraints

To keep the first implementation narrow and reliable:

- branch writes are limited to `main`
- one request produces one commit
- only file upsert and file delete are supported
- directory-level operations are not supported directly
- content writes are text-first; binary support can be added later if needed
- authorization remains platform-owned and is not delegated to Gogs collaborators
