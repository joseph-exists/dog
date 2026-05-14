# Shadow Outbox and Repair

This document records the current async write architecture. It was originally a milestone plan for moving Shadow writes out of the request path; that migration is now implemented around local git plus optional Gogs/Gittin remote sync.

## Current Invariants

- Request-path code creates DB records and enqueues outbox jobs.
- The outbox worker is responsible for git commits.
- `ShadowVersion.snapshot_json` is the durable fallback copy.
- `ShadowVersion.commit_sha` starts as `pending` and is finalized after a successful commit.
- `ShadowVersion.status` tracks `pending`, `committed`, or error states.
- One `ShadowOutboxJob` exists per `ShadowVersion`.
- `ShadowRepoVersionCounter` allocates monotonically increasing version numbers per repo.

## Write Lifecycle

1. The application mutates domain state.
2. A snapshot exporter builds the Shadow JSON.
3. `ShadowService` ensures the `ShadowRepo`, allocates a version number, writes a pending `ShadowVersion`, and enqueues a `ShadowOutboxJob`.
4. The worker claims the job, commits the snapshot into local git, optionally pushes to the configured remote, and records the commit SHA.
5. On success, the job and version are marked committed.
6. On retryable failure, the job is rescheduled with backoff.
7. On fatal or exhausted failure, the job is marked dead and the DB snapshot remains available for fallback reads.

## Repair Surface

The worker supports two one-shot repair modes:

- `repair_missing_jobs`: finds pending/error versions without jobs and creates jobs for them.
- `repair_missing_commits`: finds committed versions whose git commit cannot be read and re-enqueues them.

These modes are intended for operational recovery after worker outages, manual git cleanup, or old data migrations.

## Legacy Schema Names

The attempt table still has `forgejo_repo` and `forgejo_commit_sha` fields. Current code writes the local repo path and git commit SHA there. Treat those as legacy column names until a migration renames them.

`ShadowRepo.forgejo_repo_name` and `ShadowRepo.forgejo_repo_id` are also legacy field names. The repo name remains useful; the repo id is now populated from Gogs/Gittin remote provisioning when configured.

## Failure Modes

| Failure | Current behavior | Recovery |
| --- | --- | --- |
| Worker down | Jobs remain queued | Restart worker |
| Local git commit fails | Job becomes retryable or dead | Inspect attempt error, repair underlying filesystem/git issue |
| Remote push fails | Commit helper raises; job retries | Fix remote/Gogs/Gittin config or run local-only |
| Git snapshot missing | Reads fall back to DB with `is_stale=True` | Run `repair_missing_commits` |
| Missing job for pending version | Version remains pending | Run `repair_missing_jobs` |

## Related Code

- `backend/app/services/shadow_service.py`
- `backend/app/services/shadow_outbox_worker.py`
- `backend/app/services/shadow_git.py`
- `backend/app/services/shadow_read_service.py`
