# Shadow Models

The Shadow models live in `backend/app/models.py`. They describe local-git-backed provenance for application entities, with optional Gogs/Gittin remote metadata.

## ShadowUser

`ShadowUser` maps an application user to a system-managed profile shadow repo. It is backend-owned and invisible to normal product flows. The fields `forgejo_repo_name` and `forgejo_repo_id` are legacy schema names; they now identify the shadow repo name and optional remote repo id.

## ShadowRepo

`ShadowRepo` maps a versioned entity to its shadow repository.

- `entity_type`: internal entity contract such as `room`, `story`, `agent`, or `persona`.
- `entity_id`: the domain object id.
- `owner_id`: the application user who owns the entity.
- `forked_from_id`: optional source repo for clone/fork lineage.
- `forgejo_repo_name`: legacy field name for the shadow repo name.
- `forgejo_repo_id`: legacy field name for the optional Gogs/Gittin remote repo id.

Local repo paths are derived from `SHADOW_REPOS_PATH`, `entity_type`, and `entity_id`, not from the legacy field names.

## ShadowVersion

`ShadowVersion` records one immutable snapshot version for a repo. It stores:

- `version_number`: allocated by `ShadowRepoVersionCounter`.
- `snapshot_json`: the full JSON fallback copy.
- `commit_sha`: `pending` until the worker commits, then the git SHA.
- `status`: pending/committed/error state for the async write.
- `created_by_id`: the actor who caused the version.

The DB snapshot exists even before git commit finalization, which is what makes the read path resilient.

## ShadowOutboxJob

`ShadowOutboxJob` is the durable queue for async Shadow git writes. There is one job per `ShadowVersion`, anchored by the unique `shadow_version_id`. Jobs carry status, lock ownership, retry timing, attempt count, and last error metadata.

## ShadowOutboxAttempt

`ShadowOutboxAttempt` records each worker attempt. The `forgejo_repo` and `forgejo_commit_sha` fields are legacy column names; current attempts store the local repo path and git commit SHA there.

## ShadowRepoVersionCounter

`ShadowRepoVersionCounter` serializes version number allocation per shadow repo so that request-path enqueue can create pending versions without relying on git state.

## ShadowOutboxRepoLease

`ShadowOutboxRepoLease` is a schema-level lease primitive for per-repo serialization. The current worker primarily uses job locks; treat this model as available infrastructure rather than the main runtime path.
