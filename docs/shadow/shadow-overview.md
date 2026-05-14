# Shadow System Overview

Shadow is the internal provenance system for versioned application state. It turns important domain objects into JSON snapshots, stores version metadata in Postgres, and commits the snapshots into local git repositories. The system is intentionally backend-owned: product flows ask Shadow to record or read state, but end users do not manage shadow repos directly.

Forgejo has been refactored out of the Shadow runtime. Current Shadow writes target local git first, under `SHADOW_REPOS_PATH`, and may optionally sync to a remote Gittin/Gogs repository when `SHADOW_REPO_URL_TEMPLATE` and `SHADOW_GOGS_*` settings are configured. Some database columns and attempt fields still use `forgejo_*` names for backward compatibility; those names are legacy schema labels, not an active Forgejo dependency.

## Core Flow

1. A route or service builds a deterministic snapshot with `backend/app/services/shadow_exporters.py`.
2. `ShadowService.enqueue_entity_version(...)` or `enqueue_entity_version_with_owner(...)` ensures a `ShadowRepo`, allocates a per-repo `version_number`, creates a pending `ShadowVersion`, and queues a `ShadowOutboxJob`.
3. `backend/app/services/shadow_outbox_worker.py` claims queued jobs, commits `{entity_type}.json` into the local git repo at `{SHADOW_REPOS_PATH}/{entity_type}/{entity_id}/`, optionally pushes through `SHADOW_REPO_URL_TEMPLATE`, and finalizes the `ShadowVersion` with the commit SHA.
4. `backend/app/services/shadow_read_service.py` reads committed snapshots from git by commit SHA. If the git snapshot is missing, or the version is still pending/error, it falls back to `ShadowVersion.snapshot_json` and marks the result stale.

Room snapshots have one extra behavior: when a room version is committed, the worker also writes `room_events.redis.json`, a replay-oriented export of persisted `RoomEvent` rows. That keeps room state and room event history available in the same shadow repo without coupling the read path to Redis.

## What Gets Versioned

Shadow currently supports snapshots for the core runtime entities used by rooms and agents:

- `room`: room metadata, participants, and active participant bindings.
- `story`: story metadata, nodes, choices, requirements, and state variables.
- `agent`: agent configuration and agent-persona links.
- `persona`: persona metadata plus linked traits and qualities.
- `llm_model`: model metadata used by runtime selection.
- `user_access_provider`: provider gateway configuration with secret-safe indicators only.
- `quality` and `trait`: reusable persona/story building blocks.

Snapshots are intentionally JSON-first. The DB copy is the durable request-path record; the git copy provides a browsable, diffable, commit-addressable history once the worker finishes.

## Runtime Pieces

The main service boundary is `ShadowService`. It is responsible for idempotent repo lookup/creation, version counter allocation, pending version creation, and durable outbox enqueue. Remote provisioning is best-effort through `shadow_gogs_service`; if Gogs/Gittin is not configured or temporarily unavailable, Shadow keeps operating in local-only mode.

The outbox worker is the only component that turns pending versions into git commits. It handles retry/backoff, records `ShadowOutboxAttempt` rows, marks jobs `committed`, `retryable_error`, or `dead`, and exposes repair modes for missing jobs or missing commits. The worker writes through `shadow_git.py`, which owns local repo initialization, file commits, reads, and optional remote push/pull.

Reads flow through `ShadowReadService` and `shadow_summary_service`. The read service returns full snapshots with provenance metadata (`source="git"` or `source="db"`, `is_stale`), while the summary service turns large snapshots into prompt-friendly shapes. `shadow_context_loader.py` injects those summaries into the context pipeline as `ContextItem`s with `source="shadow"` for rooms, stories, agents, personas, models, and provider gateways.

## Configuration

Core settings live in `backend/app/core/config.py`:

```python
SHADOW_ENABLED = True
SHADOW_REPOS_PATH = "/tmp/shadows"
SHADOW_REPO_URL_TEMPLATE = None
SHADOW_REPO_DEFAULT_BRANCH = "main"
SHADOW_GOGS_BASE_URL = None
SHADOW_GOGS_TOKEN = None
SHADOW_GOGS_ORG = "shadow"
SHADOW_GOGS_TIMEOUT_SECONDS = 10.0
```

Worker-only settings are environment variables read by `shadow_outbox_worker.py`:

```bash
SHADOW_OUTBOX_POLL_INTERVAL_SECONDS=5
SHADOW_OUTBOX_BATCH_SIZE=10
SHADOW_OUTBOX_LOCK_TTL_SECONDS=60
SHADOW_OUTBOX_MAX_ATTEMPTS=25
SHADOW_OUTBOX_WORKER_ID=<hostname:pid>
SHADOW_OUTBOX_LOG_LEVEL=INFO
SHADOW_OUTBOX_MODE=worker
```

## Related Docs

- [Shadow Outbox Worker](ShadowOutboxWorker.md)
- [Shadow Read Path and Context Provider](ShadowPhase2Milestone2_TechnicalSpec.md)
- [Shadow Implementation Guide](ShadowPhase2Milestone2_ImplementationGuide.md)
- [Shadow Outbox and Repair](ShadowPhase3Milestone3.md)
- [Shadow Models](shadow-models.py.md)
