# Shadow Outbox Worker

This worker drains `shadow_outbox_jobs` and performs Forgejo IO for Shadow writes.

## Run

```
python -m app.services.shadow_outbox_worker
```

## Environment variables

All variables are optional; defaults are shown.

- `SHADOW_OUTBOX_POLL_INTERVAL_SECONDS` (default: `5`)
  - How often the worker polls when no jobs are available.
- `SHADOW_OUTBOX_BATCH_SIZE` (default: `10`)
  - Number of jobs claimed per poll cycle.
- `SHADOW_OUTBOX_LOCK_TTL_SECONDS` (default: `60`)
  - Lease timeout for job and repo locks; stale locks are re-claimed.
- `SHADOW_OUTBOX_MAX_ATTEMPTS` (default: `25`)
  - Max attempts before a job is marked `dead`.
- `SHADOW_OUTBOX_WORKER_ID` (default: `<hostname>:<pid>`)
  - Identifier stored in `shadow_outbox_jobs.locked_by` and repo lease rows.
- `SHADOW_OUTBOX_LOG_LEVEL` (default: `INFO`)
  - Logging level for the worker process.
- `SHADOW_OUTBOX_MODE` (default: `worker`)
  - `worker` runs the polling loop.
  - `repair_missing_jobs` enqueues missing outbox jobs for pending/error versions.
  - `repair_missing_commits` enqueues jobs for committed versions missing in Forgejo.

## Wiring the polling knobs

In Docker or Compose, set the environment variables on the worker container:

```
environment:
  - SHADOW_OUTBOX_POLL_INTERVAL_SECONDS=5
  - SHADOW_OUTBOX_BATCH_SIZE=10
  - SHADOW_OUTBOX_LOCK_TTL_SECONDS=60
  - SHADOW_OUTBOX_LOG_LEVEL=INFO
```

In local runs, export them in the shell:

```
export SHADOW_OUTBOX_POLL_INTERVAL_SECONDS=5
export SHADOW_OUTBOX_BATCH_SIZE=10
export SHADOW_OUTBOX_LOCK_TTL_SECONDS=60
export SHADOW_OUTBOX_MAX_ATTEMPTS=25
export SHADOW_OUTBOX_LOG_LEVEL=INFO
python -m app.services.shadow_outbox_worker
```

Repair runs:

```
export SHADOW_OUTBOX_MODE=repair_missing_jobs
python -m app.services.shadow_outbox_worker
```

```
export SHADOW_OUTBOX_MODE=repair_missing_commits
python -m app.services.shadow_outbox_worker
```

These knobs intentionally live outside `Settings` so the worker can stay minimal
and avoid loading web server defaults.
