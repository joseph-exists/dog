# Shadow Implementation Guide

This guide documents the current implementation shape for Shadow read/context work. It supersedes the old Forgejo milestone checklist.

## Add or Update a Snapshot Exporter

1. Add a deterministic builder in `backend/app/services/shadow_exporters.py`.
2. Use JSON-serializable values only.
3. Never include plaintext or encrypted secrets. Store booleans such as `api_key_present` when the runtime needs to know whether a credential exists.
4. Keep the top-level envelope stable:

```json
{
  "schema_version": 1,
  "entity_type": "agent"
}
```

## Enqueue a Version

Call `ShadowService.enqueue_entity_version(...)` after the domain write has enough data to build a coherent snapshot. For room-scoped writes where the room owner differs from the actor, use `enqueue_entity_version_with_owner(...)`.

The enqueue path should only perform DB work plus best-effort remote provisioning. The durable write is the pending `ShadowVersion` plus one `ShadowOutboxJob`.

## Commit the Version

Run the worker:

```bash
python -m app.services.shadow_outbox_worker
```

The worker writes to local git via `shadow_git.py`, optionally pushes to the configured remote, and finalizes the version. Request handlers should not perform git commits inline.

## Read a Snapshot

Use `shadow_read_service`:

```python
result = shadow_read_service.get_latest_snapshot(
    session=session,
    entity_type="room",
    entity_id=room_id,
)
```

Prefer `result.snapshot_json` over reaching into git directly. Check `result.source` and `result.is_stale` when callers need to distinguish committed git state from DB fallback state.

## Add a Summary

Update `backend/app/services/shadow_summary_service.py` when a new entity type should be available to prompts. Summaries should be deterministic and compact. Include provenance metadata and avoid duplicating large graph payloads unless the agent needs them.

## Add Context Wiring

Update `backend/app/services/shadow_context_loader.py` when a new summary should become room or agent context. Use room state and active `RoomParticipantBinding` rows as the source of truth for "what to load" during chat.

## Test Checklist

- Exporter produces stable JSON for the entity.
- Enqueue creates exactly one pending `ShadowVersion` and one `ShadowOutboxJob` per write.
- Worker commits the expected file into the local repo.
- Read service returns `source="git"` for committed versions.
- Read service falls back to `source="db"` and `is_stale=True` when the git file is unavailable.
- Summary output excludes secrets and remains small enough for prompt use.
