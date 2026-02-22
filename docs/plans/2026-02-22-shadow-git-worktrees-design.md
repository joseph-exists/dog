# Shadow Services: Forgejo → Local Git Refactor

**Date:** 2026-02-22
**Status:** Approved
**Driver:** Simplicity - Forgejo is unnecessary overhead

## Context

The shadow versioning system currently uses Forgejo (a git server) via HTTP API to store entity snapshots. This adds:
- External service dependency (Risk #2: Forgejo Outage Cascade - High/High)
- Operational overhead (container, tokens, service accounts)
- Network latency on reads

The system already has DB fallback for reads, making Forgejo redundant complexity.

## Decision

Replace Forgejo HTTP API calls with local git subprocess operations. Keep the outbox worker pattern.

## Design

### Architecture

```
Before:
  enqueue → DB (pending) → worker → Forgejo API → commit SHA → DB (committed)

After:
  enqueue → DB (pending) → worker → local git repo → commit SHA → DB (committed)
```

### Directory Structure

```
$SHADOW_REPOS_PATH/           # env var, default: /data/shadows
  room/
    {room_uuid}/              # git repo (not bare)
      .git/
      room.json
  agent/
    {agent_uuid}/
      .git/
      agent.json
  ...
```

Each entity gets its own git repository at `{base_path}/{entity_type}/{entity_id}/`.

### Configuration

```python
SHADOW_REPOS_PATH: str = "/data/shadows"
```

### New Module: `shadow_git.py`

Thin wrapper around git subprocess calls:

```python
def ensure_repo(repo_path: Path) -> None:
    """Initialize repo if it doesn't exist."""

def commit_snapshot(
    repo_path: Path,
    entity_type: str,
    snapshot_json: dict,
    message: str,
    author: str = "shadow-system"
) -> str:
    """Write snapshot to {entity_type}.json, commit, return SHA."""

def read_snapshot(repo_path: Path, entity_type: str, commit_sha: str) -> dict:
    """Read snapshot at specific commit via git show."""

def get_latest_commit(repo_path: Path) -> str | None:
    """Get HEAD commit SHA, or None if no commits."""
```

### Service Changes

**`shadow_service.py`:**
- Remove: `get_api_clients()`, `get_repo_api()`, `get_service_token()`, `openapi_client` imports
- Remove: `ensure_shadow_repo()` Forgejo logic, `create_version()` Forgejo commits
- Keep: `enqueue_entity_version()` (already DB-only), `ensure_shadow_repo_db_only()`
- Add: `get_repo_path(entity_type, entity_id) -> Path`

**`shadow_outbox_worker.py`:**
- Remove: `_ensure_forgejo_repo()`, `_commit_snapshot()`, lease functions, `openapi_client`
- Replace with: `shadow_git.ensure_repo()`, `shadow_git.commit_snapshot()`
- Simplify: `process_job()` becomes straightforward

**`shadow_read_service.py`:**
- Remove: `_read_json_file_from_forgejo()`
- Replace with: `shadow_git.read_snapshot()`
- Update: `source="forgejo"` → `source="git"`
- Keep: DB fallback logic

**Model changes:**
- `ShadowRepo`: Remove `forgejo_repo_id`, consider removing/renaming `forgejo_repo_name`
- `ShadowOutboxAttempt`: Rename `forgejo_repo` → `repo_path`, `forgejo_commit_sha` → `commit_sha`

### Unchanged

- `shadow_exporters.py` - No Forgejo dependency
- `shadow_summaries.py` - Pure functions
- `shadow_summary_service.py` - Calls read service
- `shadow_context_loader.py` - Calls summary service
- `shadow_tasks.py` - Calls enqueue
- Outbox pattern (enqueue → worker → commit)
- Redis summary caching
- `ShadowVersion`, `ShadowOutboxJob`, `ShadowRepoVersionCounter` models

### Concurrent Access

No worktrees or leases needed. Trust git's own conflict handling:
- Entities are isolated (different repos)
- Git handles concurrent commits gracefully
- Lease complexity was for Forgejo API atomicity, not needed for local git

### Migration

- **Existing data:** Clean slate, no data to preserve
- **Forgejo:** Keep running during validation, remove after confirmed working
- **Rollback:** Revert code, Forgejo still works

## Testing

### Unit Tests (`test_shadow_git.py`)
- `test_ensure_repo_creates_git_dir`
- `test_commit_snapshot_returns_sha`
- `test_read_snapshot_at_commit`
- `test_read_snapshot_invalid_sha_raises`

### Integration Tests (update existing)
- `test_shadow_outbox_worker.py` - Remove Forgejo mocks
- `test_shadow_read_service.py` - Update source checks

### Manual Validation
1. Start stack, Forgejo unused
2. Create/update room → verify git repo at `$SHADOW_REPOS_PATH/room/{id}/`
3. `git log` in repo → verify commit
4. Trigger context load → verify local git read
5. Simulate git failure → verify DB fallback
6. Check logs → no Forgejo API calls
7. Remove Forgejo container

## Future Considerations

- **Prompt/result visualization:** Loose 1:many coupling. Results store explicit `prompt_id` + `prompt_version` references. Query across repos by those references.
- **Production deployment:** Shared volume (EFS/NFS) or revisit architecture for distributed access.
