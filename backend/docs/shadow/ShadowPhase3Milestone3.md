# Shadow — Milestone 3 Technical Specification

Milestone 3 moves Shadow *write-path* Forgejo IO out of the request path by introducing a durable outbox and a background worker. It also defines the reliability/repair surface we need to safely evolve provenance features (e.g., per-user reference indexes) without silently dropping commits.

This spec is written to match the current codebase reality:

- Forgejo writes happen synchronously in `backend/app/services/shadow_service.py` (`ensure_shadow_repo` + `create_version`).
- Some routes call Shadow versioning inline (agent/story); room binding shadowing is currently a FastAPI `BackgroundTasks` function (`backend/app/services/shadow_tasks.py`) but still runs inside the web process and is not durable.

## Goals

1. **No Forgejo IO in the request path** for Shadow writes.
2. **Durable intent**: if a DB mutation commits, the corresponding Shadow write is eventually attempted until it succeeds or is explicitly dead-lettered.
3. **Idempotent retries**: worker retries do not create duplicate versions or reorder versions within an entity repo.
4. **Clear operational state**: every Shadow write has a visible lifecycle (queued → processing → committed, or failed/dead) with diagnostics.
5. **Repair tooling**: we can detect missing repos/commits and replay exports safely.

## Non-goals (Milestone 3)

- End-user UI exposure of Shadow mechanics (repos/SHAs/versions remain invisible).
- A fully-featured distributed queue product (Temporal/Celery/RQ) if a minimal worker loop suffices.
- Global “reference index” materialization beyond the minimum needed to prove the outbox/worker reliability model (that work is specified separately in `backend/shadow-work.md`).

## Existing architecture (baseline)

- DB mapping: `ShadowRepo` and `ShadowVersion` live in `backend/app/models.py`.
- Synchronous Forgejo IO:
  - `ShadowService.ensure_shadow_repo(...)` creates the Forgejo repo via `RepositoryApi.create_current_user_repo(...)`.
  - `ShadowService.create_version(...)` updates/creates `{entity_type}.json` via `repo_get_contents` + `repo_update_file`/`repo_create_file`, then writes a `ShadowVersion` row (even on Forgejo failure).

Key touchpoints (today):

- Inline request-path Shadow writes:
  - `backend/app/api/routes/agent_routes.py` (`create_agent`, `update_agent`)
  - `backend/app/api/routes/stories.py` (`create_story`, `update_story`)
  - `backend/app/api/routes/agent_personas.py` (agent persona changes trigger an agent snapshot write)
- Post-response Shadow write for rooms (still in-process):
  - `backend/app/api/routes/room_participant_bindings.py` → `BackgroundTasks.add_task(shadow_room_version_best_effort)`
  - `backend/app/services/shadow_tasks.py` builds snapshot and calls `shadow_service.create_entity_version_with_owner(...)`

## Proposed architecture

### High-level

Replace “do Forgejo IO now” with:

1. **Write DB domain state**
2. **Enqueue a durable Shadow write intent** (outbox row)
3. **Return HTTP response**
4. **Worker processes outbox**:
   - ensure Forgejo repo exists
   - commit/update `{entity_type}.json`
   - persist commit SHA + attempt diagnostics

### Contract changes (invariants)

- The DB is the durable source of “what snapshot we intended to write”.
- Forgejo is the durable source of the git history and pinned SHAs *after commits succeed*.
- “Latest snapshot” semantics for reads become “latest committed version” (Forgejo-first, DB fallback).

### Latest snapshot semantics (explicit)

When there are pending/uncommitted versions in DB:

- `ShadowReadService.get_latest_snapshot(...)` returns the latest **committed** version only.
- Pending versions remain readable via pinned `version_number`/`commit_sha` lookups and DB fallback, but do not become “latest” until committed.

Edge case (brand-new entity):

- If there are **no committed versions yet**, `get_latest_snapshot(...)` returns the pending DB snapshot, explicitly marked as not committed (e.g., `status="pending"`, `source="db"`, `is_stale=true`).

## Outbox schema (proposed)

### 1) `shadow_outbox_jobs`

One row = one intended Forgejo write for one Shadow version.

**Core columns**

- `id` UUID PK
- `shadow_repo_id` UUID FK → `shadowrepo.id`
- `shadow_version_id` UUID FK → `shadowversion.id` (unique; one job per version)
- `entity_type` string (redundant but convenient for filtering/metrics)
- `entity_id` UUID (redundant but convenient for filtering/metrics)

**Status/locking**

- `status` enum/string:
  - `queued`
  - `processing`
  - `committed`
  - `retryable_error`
  - `dead` (dead-letter; requires manual intervention)
- `attempt_count` int
- `run_after` timestamp (next eligible time; enables backoff)
- `locked_at` timestamp nullable
- `locked_by` string nullable (worker instance id)
- `last_error` string nullable (short human-friendly summary)
- `last_error_at` timestamp nullable

**Metadata**

- `priority` smallint (optional; default 100)
- `created_at`, `updated_at`

**Constraints / indexes**

- Unique: (`shadow_version_id`)
- Index: (`status`, `run_after`)
- Index: (`shadow_repo_id`, `status`)

Rationale:

- Tying a job to a specific `ShadowVersion` gives us a stable idempotency anchor.
- Row-level locking/leases allow multiple worker processes without double-processing.

### 2) `shadow_outbox_attempts` (optional but recommended)

One row per processing attempt; primarily for diagnostics and repair confidence.

- `id` UUID PK
- `outbox_job_id` UUID FK → `shadow_outbox_jobs.id`
- `attempt_number` int (1-based)
- `started_at`, `finished_at`
- `result` enum/string: `success` | `retryable_error` | `fatal_error`
- `error_type` string nullable (e.g., `forgejo_401`, `forgejo_404`, `sha_conflict`, `db_error`)
- `error_message` text nullable
- `forgejo_repo` string nullable (`{owner}/{repo}`)
- `forgejo_commit_sha` string nullable

### 3) `ShadowVersion` changes (minimal, explicit)

We need to reconcile two realities:

- Milestone 2 reads fall back to `ShadowVersion.snapshot_json` when Forgejo is unavailable.
- Milestone 3 makes Forgejo commit asynchronous, so the DB must represent “pending” and “failed” commits cleanly.

Proposed adjustments:

- Keep `snapshot_json` immutable.
- Allow the worker to update *only* commit-related metadata.

Add to `ShadowVersion`:

- `status` enum/string:
  - `pending` (created/enqueued, not yet committed)
  - `committed` (Forgejo commit sha recorded)
  - `error` (last attempt failed; outbox will retry unless dead)
- `committed_at` timestamp nullable
- `last_error` text nullable
- `updated_at` timestamp (default now; updated when status/commit_sha changes)

Commit SHA behavior:

- On enqueue: create `ShadowVersion` with `commit_sha="pending"` and `status="pending"`.
- On commit success: worker updates `ShadowVersion.commit_sha=<real sha>` and `status="committed"`.
- On repeated failures: worker updates `status="error"` and `last_error`, leaving `commit_sha` as `"pending"` (or a stable sentinel like `"error"` if we prefer).

This is a deliberate shift from “versions are immutable” to “snapshot is immutable, commit metadata can be finalized asynchronously”.

## Version numbering / ordering

Decision: allocate `ShadowVersion.version_number` using a **sequence-number allocator**, not “select max + 1”.

Rationale: multiple requests can enqueue versions for the same `shadow_repo_id` concurrently; version numbers must remain unique and strictly increasing per repo.

### Proposed schema: `shadow_repo_version_counters`

- `shadow_repo_id` UUID PK (FK → `shadowrepo.id`)
- `next_version_number` int (starts at 1)
- `updated_at` timestamp

### Allocation algorithm (enqueue-time)

1. `SELECT ... FOR UPDATE` the counter row for `shadow_repo_id` (create if missing).
2. Assign `version_number = next_version_number`.
3. Increment `next_version_number` and commit the transaction.

## ShadowRepo creation policy

Decision: enqueue creates/ensures the **DB** `ShadowRepo` record only (no Forgejo network IO). The worker is the only component that:

- creates/ensures Forgejo repos
- commits `{entity_type}.json` to Forgejo

## Enqueue semantics (write-path behavior)

### When to enqueue

Any code path that currently calls:

- `shadow_service.create_entity_version(...)`
- `shadow_service.create_entity_version_with_owner(...)`

must be changed to enqueue a Shadow write job instead of doing Forgejo IO.

### What to enqueue (payload strategy)

Primary strategy (preferred for provenance): **enqueue the snapshot JSON**.

- Pros: snapshot reflects the exact state at the time we decided to version it.
- Cons: larger DB writes; requires that snapshot is available at enqueue time.

Fallback strategy (allowed only where necessary): **enqueue a “rebuild snapshot” instruction**.

- Pros: works when snapshot building cannot safely run inside the transaction context.
- Cons: risks snapshot drift if the entity changes again before the worker runs.

**Recommendation in this repo (given current patterns):**

- Agent/story/persona/model/provider routes: enqueue with full `snapshot_json` (they already build snapshots synchronously in request handlers).
- Room binding changes: initially keep the existing post-commit snapshot build pattern, but switch it to “enqueue job” instead of “commit to Forgejo” (this preserves current snapshot timing while still eliminating Forgejo IO in the web process).

## Worker (processing model)

### Inputs

Worker polls `shadow_outbox_jobs` for eligible jobs:

- `status in ("queued", "retryable_error")`
- `run_after <= now()`
- not locked, or lock is expired (lease timeout)

### Locking / concurrency

Two requirements:

1. Prevent two workers from processing the same job concurrently.
2. Avoid concurrent writes to the same Forgejo repo that cause file SHA conflicts and version reordering.

Proposed approach:

- Job locking: select jobs `FOR UPDATE SKIP LOCKED` and set `locked_at/locked_by`.
- Per-repo serialization (chosen): acquire a repo-level lease row keyed by `shadow_repo_id` before doing any Forgejo IO.

Proposed schema: `shadow_outbox_repo_leases`

- `shadow_repo_id` UUID PK (FK → `shadowrepo.id`)
- `locked_at` timestamp nullable
- `locked_by` string nullable

Lease rule:

- If `locked_at` is null or older than `LOCK_TTL_SECONDS`, the lease is considered available.
- A worker updates `locked_at/locked_by` to acquire the lease, and clears them when the repo job completes.

This prevents concurrent commits to the same repo and drastically reduces SHA conflict churn.

### Worker state machine (per job)

States and transitions:

- `queued`
  - → `processing` when a worker lease is acquired
- `processing`
  - → `committed` on Forgejo commit success + DB commit_sha finalized
  - → `retryable_error` on retryable failure (Forgejo down, 5xx, SHA conflict, transient DB error)
  - → `dead` on fatal failure (misconfiguration, 401/403 permanent auth failure, invalid repo name contract)
- `retryable_error`
  - → `processing` when `run_after` is reached and a worker lease is acquired
- `dead`
  - terminal until a human/operator intervenes (or a repair job reclassifies it)
- `committed`
  - terminal

### Worker algorithm (per job)

Given `shadow_version_id` (and therefore `entity_type`, `entity_id`, and intended `snapshot_json`):

1. Load `ShadowRepo` and `ShadowVersion`.
2. Acquire per-repo serialization (see above).
3. Ensure Forgejo repo exists:
   - if `ShadowRepo.forgejo_repo_id` is null or Forgejo says repo missing:
     - attempt create repo via service token for `entity_type`
     - update `ShadowRepo.forgejo_repo_id` (best effort)
4. Commit `{entity_type}.json`:
   - read existing file SHA (`repo_get_contents`) to update safely
   - update or create file
   - capture resulting `commit_sha`
5. Finalize DB:
   - update `ShadowVersion.commit_sha`, `ShadowVersion.status="committed"`, `committed_at=now()`
   - set outbox job `status="committed"`, clear lock, record attempt row

Backoff:

- Exponential with jitter, capped (e.g., 1s → 10s → 1m → 5m → 30m).
- After N attempts (e.g., 25) move to `dead` unless error is explicitly retryable forever (operator-configurable).

## Failure modes (and required behavior)

This table is the “don’t drop commits” contract for Milestone 3.

| Failure mode | Example | Expected behavior | Repair path |
|---|---|---|---|
| DB mutation commits, Forgejo down | request succeeds; Forgejo 503 | outbox job remains `retryable_error`; `ShadowVersion.snapshot_json` still exists for DB fallback reads | worker retries; ops monitors retry backlog |
| Enqueue fails after DB mutation | DB committed; outbox insert failed | **must be prevented** for sync routes by doing enqueue in the same DB transaction as the domain write | add transactional outbox insert; add repair scanner to find `ShadowVersion.status=pending` without job |
| Worker crashes mid-processing | process dies after acquiring lock | lock lease expires; another worker can pick it up | lease timeout + idempotent retry |
| Forgejo repo missing | repo deleted manually | worker recreates repo and continues (if allowed) | repair job can re-enqueue all versions for that repo |
| Forgejo auth misconfigured | token revoked; 401/403 | job transitions to `dead` with clear error; alert operator | fix token/env; requeue dead jobs |
| File SHA conflict | two commits racing to same file | worker should serialize per repo; if conflict still happens, refetch SHA and retry | enforce per-repo serialization; retry on conflict |
| Duplicate enqueue | route retries; job inserted twice | unique constraint on `shadow_version_id` prevents two jobs for same version | if duplicates existed historically, dedupe via repair script |
| Commit succeeds, DB finalize fails | Forgejo returns SHA but DB commit fails | job stays retryable; next attempt should detect already-committed file content and converge without creating a new version | attempt table records prior SHA; finalize step is idempotent |
| Snapshot drift (rebuild strategy) | room snapshot rebuilt after later edits | snapshot may not match original intent | avoid rebuild strategy where provenance matters; if unavoidable, record “rebuilt_at” + effective range |

## Repair / reconciliation jobs (required deliverables)

### 1) “Missing job” scanner

Detect ShadowVersions that are not committed and have no outbox job:

- `ShadowVersion.status in ("pending", "error")` and no matching `shadow_outbox_jobs.shadow_version_id`

Action: create an outbox job for each missing entry.

### 2) “Repo/commit missing” reconciler

Detect:

- `ShadowVersion.status="committed"` but Forgejo cannot fetch `{entity_type}.json` at `commit_sha`

Action: enqueue a repair job that replays the snapshot (committing a new version if necessary) and records the incident.

## Observability (minimum)

- Metrics:
  - queued job count by entity_type/status
  - processing latency (created_at → committed_at)
  - retry rate and dead-letter count
- Logs:
  - correlation id: `outbox_job_id`, `shadow_version_id`, `shadow_repo_id`, `entity_type/entity_id`
  - never log tokens or secret fields

## Rollout plan (safe, incremental)

1. Add DB schema (outbox tables + minimal ShadowVersion status fields).
2. Implement enqueue-only API in `ShadowService` (no Forgejo).
3. Update request-path call sites to enqueue (agent/story/agent_personas first).
4. Implement worker and run it in a controlled environment.
5. Switch room binding “background task” to enqueue-only (still post-commit initially).
6. Add repair scanners and validate with deliberate Forgejo outages.

## Acceptance criteria (Milestone 3)

- No route performs Forgejo IO during request handling.
- A committed DB mutation results in a durable outbox job (or is detected and repaired).
- Worker retries are idempotent and do not reorder versions per entity.
- Operators can see and act on stuck/dead jobs.

---

## Implementation checklist (executable task list)

This is the “do the work” checklist, ordered to keep diffs reviewable and to preserve a safe rollout.

### A) Decisions to lock in (before writing code)

Locked decisions:

1. **Per-repo serialization mechanism**: repo lease table keyed by `shadow_repo_id` (Option 1)
2. **Lease timeout**: `60s`
3. **Backoff schedule**: exponential w/ jitter, cap `30m`
4. **Dead-letter threshold**: `25` attempts
5. **Fatal vs retryable classification**:
   - Fatal: Forgejo `401/403`, invalid `entity_type`, invalid repo naming contract
   - Retryable: Forgejo `409`/SHA conflicts, `5xx`, network timeouts, temporary DB errors
6. **Snapshot payload policy**: store full `snapshot_json` per `ShadowVersion` (no rebuild-by-default)
7. **Version numbering**: per-repo sequence counter table (`shadow_repo_version_counters`)
8. **Latest snapshot**: `get_latest_snapshot` returns latest committed only
9. **ShadowRepo policy**: enqueue ensures DB `ShadowRepo` only; worker ensures Forgejo repo
10. **Worker deployment**: separate container/process; keep image minimal and dependencies contained

Record (stable literals used across code/tests/docs):

- `SERIALIZATION_STRATEGY = "repo_lease_table"`
- `LOCK_TTL_SECONDS = 60`
- `BACKOFF = "exponential_with_jitter_cap_30m"`
- `MAX_ATTEMPTS = 25`
- `FATAL_ERROR_RULES = "forgejo_401_403_invalid_contract"`
- `SNAPSHOT_POLICY = "store_snapshot_json_per_version"`
- `VERSION_NUMBERING = "per_repo_sequence_counter_table"`
- `LATEST_SNAPSHOT = "latest_committed_only"`
- `SHADOW_REPO_POLICY = "db_only_in_enqueue; forgejo_only_in_worker"`
- `WORKER_DEPLOYMENT = "separate_container_minimal"`

### B) Schema changes (alembic)

- [x] Add `shadow_outbox_jobs` table (and indexes/unique constraints) to `backend/app/models.py`.
- [x] (Optional) Add `shadow_outbox_attempts` table to `backend/app/models.py`.
- [x] Add `shadow_outbox_repo_leases` table to `backend/app/models.py` (per-repo serialization).
- [x] Add `shadow_repo_version_counters` table to `backend/app/models.py` (per-repo version_number allocator).
- [x] Add `ShadowVersion.status`, `committed_at`, `last_error`, `updated_at` to `backend/app/models.py`.
- [x] Add alembic migration(s) under `backend/app/alembic/versions/` (match existing project conventions).
- [x] Add constraints/indexes in migration:
  - [x] unique `shadow_outbox_jobs.shadow_version_id`
  - [x] unique `shadowversion.shadow_repo_id + shadowversion.version_number` (enforces ordering invariant)
  - [x] indexes for polling: `(status, run_after)` and `(shadow_repo_id, status)`

### C) Enqueue-only write API (no Forgejo IO in web)

Goal: every caller switches from “commit now” to “enqueue intent”.

- [ ] Introduce an enqueue service API (new module or in `ShadowService`), e.g.:
  - `enqueue_entity_version(...)`
  - `enqueue_entity_version_with_owner(...)`
- [ ] Ensure enqueue happens in the same DB transaction as the domain mutation where possible:
  - For sync SQLModel sessions: insert `ShadowVersion(status="pending", commit_sha="pending", snapshot_json=...)` + outbox job row in one transaction.
  - For async routes: either (a) enqueue using the same transaction-bound session, or (b) explicitly document and repair-gap scan (not preferred).
- [ ] Allocate `ShadowVersion.version_number` via `shadow_repo_version_counters` inside the same transaction (no “max+1”).
- [ ] Ensure the old Forgejo-writing methods are no longer called by request handlers:
  - `ShadowService.ensure_shadow_repo(...)`
  - `ShadowService.create_version(...)`

### D) Update all call sites to enqueue

Replace the following with enqueue calls:

- [ ] `backend/app/api/routes/agent_routes.py` (create/update agent)
- [ ] `backend/app/api/routes/stories.py` (create/update story)
- [ ] `backend/app/api/routes/agent_personas.py` (agent persona create/update/delete)

Room bindings:

- [ ] Update `backend/app/services/shadow_tasks.py` so `shadow_room_version_best_effort(...)` enqueues a room shadow job instead of calling Forgejo.
- [ ] Keep `BackgroundTasks` temporarily if needed, but make it enqueue-only (no network IO).

### E) Worker implementation

- [ ] Add a worker entrypoint (module + CLI):
  - Suggested location: `backend/app/services/shadow_outbox_worker.py` (core worker)
  - Suggested runner: `backend/app/scripts/` or an existing CLI pattern in this repo
- [ ] Add a minimal worker container/process:
  - Build a small image that runs only the worker (no web server).
  - Minimize and contain dependencies to what the worker imports (DB client + `openapi_client` + settings).
- [ ] Implement polling:
  - [ ] select eligible jobs (`queued`/`retryable_error`, `run_after <= now`)
  - [ ] acquire job lease (`FOR UPDATE SKIP LOCKED` or equivalent)
  - [ ] enforce per-repo serialization (decision A1)
- [ ] Implement processing steps:
  - [ ] load `ShadowRepo` + `ShadowVersion`
  - [ ] ensure Forgejo repo exists (create if missing)
  - [ ] write `{entity_type}.json` (update/create with file SHA)
  - [ ] finalize `ShadowVersion` (`commit_sha`, `status="committed"`, timestamps)
  - [ ] finalize outbox job (`status="committed"`, unlock)
- [ ] Implement error handling:
  - [ ] classify fatal vs retryable (decision A4)
  - [ ] compute backoff and set `run_after` (decision A3)
  - [ ] record attempt diagnostics (and optional `shadow_outbox_attempts` rows)

### F) Repair/reconciliation jobs

- [ ] Missing job scanner:
  - [ ] query for `ShadowVersion.status in ("pending", "error")` without a matching outbox job
  - [ ] enqueue jobs (idempotent)
- [ ] Repo/commit missing reconciler:
  - [ ] validate `{entity_type}.json` readable at pinned `commit_sha`
  - [ ] enqueue repair write (and record incident details)

### G) Tests (minimum)

Add tests in `backend/app/tests/` matching the existing service test patterns:

- [ ] Enqueue creates `ShadowVersion(status="pending")` + outbox job in one transaction.
- [ ] Worker success path finalizes `ShadowVersion(commit_sha, status="committed")` and marks job committed.
- [ ] Worker retry path updates job to `retryable_error` with increasing `run_after`.
- [ ] Worker fatal path moves job to `dead` and records last_error.
- [ ] Per-repo serialization prevents concurrent writes to the same `shadow_repo_id` (unit-level simulation is fine).
- [ ] Missing job scanner creates jobs for orphan pending versions.

### H) Rollout steps (operator-facing)

- [ ] (If acceptable in the target environment) truncate legacy Shadow tables before migration to avoid back-compat/data-mapping complexity.
- [ ] Deploy schema first (worker disabled).
- [ ] Deploy enqueue-only web changes (still no worker) and verify outbox rows accumulate.
- [ ] Deploy/run worker and verify backlog drains.
- [ ] Simulate Forgejo outage:
  - [ ] confirm jobs retry, no requests block
  - [ ] confirm DB fallback for reads remains functional
- [ ] Add dashboards/alerts for stuck/dead jobs.
