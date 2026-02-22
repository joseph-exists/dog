● ---
  Design Section 3: Service Changes

  shadow_service.py changes:

  - Remove: get_api_clients(), get_repo_api(), get_service_token(), all openapi_client imports
  - Remove: ensure_shadow_repo() Forgejo repo creation logic
  - Remove: create_version() Forgejo commit logic (moves to worker via shadow_git)
  - Keep: enqueue_entity_version() unchanged (it's already DB-only)
  - Keep: ensure_shadow_repo_db_only() - still creates ShadowRepo record
  - Add: Helper to compute repo path: get_repo_path(entity_type, entity_id) -> Path

  shadow_outbox_worker.py changes:

  - Remove: _ensure_forgejo_repo(), _commit_snapshot() (Forgejo API calls)
  - Remove: acquire_repo_lease(), release_repo_lease() (no longer needed)
  - Remove: _get_repo_api() and all openapi_client usage
  - Replace with: shadow_git.ensure_repo() and shadow_git.commit_snapshot()
  - Simplify: process_job() becomes straightforward - get snapshot, write to git, update DB

  shadow_read_service.py changes:

  - Remove: _read_json_file_from_forgejo() (HTTP read)
  - Replace with: shadow_git.read_snapshot() (local read)
  - Keep: DB fallback logic (source="db", is_stale=True) for when git read fails
  - Update: source="forgejo" becomes source="git"

  Model changes (ShadowRepo):

  - Remove: forgejo_repo_id field (no longer tracked)
  - Keep: forgejo_repo_name → rename to repo_name or just remove (we compute path from entity_type + entity_id)

  Design Section 4: What Stays Unchanged

  No changes needed:

  - shadow_exporters.py - Builds snapshots, no Forgejo dependency
  - shadow_summaries.py - Pure functions transforming snapshots
  - shadow_summary_service.py - Calls read service, no direct Forgejo dependency
  - shadow_context_loader.py - Calls summary service, no direct Forgejo dependency
  - shadow_tasks.py - Calls enqueue, no direct Forgejo dependency

  Outbox pattern preserved:

  The async job queue pattern stays intact:
  1. enqueue_entity_version() creates ShadowVersion (pending) + ShadowOutboxJob (queued)
  2. Worker polls, claims jobs, commits to git, marks committed
  3. Retry logic, backoff, dead letter handling all remain

  DB models mostly unchanged:

  - ShadowVersion - same (stores commit_sha from git)
  - ShadowOutboxJob - same (queued/processing/committed/dead)
  - ShadowRepoVersionCounter - same (version numbering)
  - ShadowOutboxAttempt - update field names (forgejo_repo → repo_path, forgejo_commit_sha → commit_sha)

  Summary/caching unchanged:

  - Redis caching of summaries stays
  - Cache keys stay the same (shadow_summary:{repo_id}:{commit_sha})