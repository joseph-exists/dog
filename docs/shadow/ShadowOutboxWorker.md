# Shadow Outbox Worker

The Shadow outbox worker drains `shadow_outbox_jobs` and turns pending `ShadowVersion` rows into git commits. It writes to local repositories under `SHADOW_REPOS_PATH` and optionally pushes to a remote Gittin/Gogs repository when `SHADOW_REPO_URL_TEMPLATE` is configured.

Forgejo is not part of the current worker runtime. A few attempt fields still use legacy `forgejo_*` names in the schema; the worker now stores the local repo path and git commit SHA in those fields until a migration renames them.

## Run

```bash
python -m app.services.shadow_outbox_worker
```

## Normal Mode

In `worker` mode, the process:

1. Claims queued or retryable jobs whose `run_after` has elapsed.
2. Loads the associated `ShadowRepo` and `ShadowVersion`.
3. Ensures the local git repo exists at `{SHADOW_REPOS_PATH}/{entity_type}/{entity_id}/`.
4. Commits `{entity_type}.json` with the snapshot stored on the version row.
5. For `room` entities, also commits `room_events.redis.json` from persisted `RoomEvent` rows.
6. Finalizes the version with `status="committed"` and the git commit SHA.
7. Records a `ShadowOutboxAttempt` for success or failure.

Failures are classified as retryable or fatal. Retryable failures use exponential backoff with jitter and eventually become `dead` after `SHADOW_OUTBOX_MAX_ATTEMPTS`.

## Repair Modes

Set `SHADOW_OUTBOX_MODE` to run one repair pass instead of the polling loop:

- `repair_missing_jobs`: enqueue missing outbox jobs for pending/error versions.
- `repair_missing_commits`: enqueue jobs for committed versions whose git commit cannot be found.

```bash
SHADOW_OUTBOX_MODE=repair_missing_jobs python -m app.services.shadow_outbox_worker
SHADOW_OUTBOX_MODE=repair_missing_commits python -m app.services.shadow_outbox_worker
```

## Environment Variables

All variables are optional; defaults are shown.

- `SHADOW_OUTBOX_POLL_INTERVAL_SECONDS` (default: `5`): how often the worker polls when no jobs are available.
- `SHADOW_OUTBOX_BATCH_SIZE` (default: `10`): number of jobs claimed per poll cycle.
- `SHADOW_OUTBOX_LOCK_TTL_SECONDS` (default: `60`): timeout for reclaiming stale job locks.
- `SHADOW_OUTBOX_MAX_ATTEMPTS` (default: `25`): max attempts before a job is marked `dead`.
- `SHADOW_OUTBOX_WORKER_ID` (default: `<hostname>:<pid>`): identifier stored in `shadow_outbox_jobs.locked_by`.
- `SHADOW_OUTBOX_LOG_LEVEL` (default: `INFO`): logging level for the worker process.
- `SHADOW_OUTBOX_MODE` (default: `worker`): worker loop or one of the repair modes above.

These knobs intentionally live outside `Settings` so the worker can stay small and avoid depending on web-server defaults.

## Related Code

- `backend/app/services/shadow_outbox_worker.py`
- `backend/app/services/shadow_git.py`
- `backend/app/services/shadow_service.py`
- `backend/app/services/shadow_read_service.py`
