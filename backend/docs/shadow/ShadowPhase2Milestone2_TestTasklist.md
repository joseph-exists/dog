# Shadow — Milestone 2 Test Tasklist (Delegation Checklist)

This file lists the test cases needed to fully satisfy Milestone 2’s reliability goals (per `backend/docs/shadow/ShadowPhase2Milestone2_TechnicalSpec.md`) and to resolve the `[~]` items in `backend/docs/shadow/ShadowPhase2Milestone2_ImplementationGuide.md`.

## Notes for implementers

- Several existing service tests rely on `pytest_asyncio`, but the current environment may not have it installed. Confirm test dependencies in your target environment before execution.
- New Shadow context injection happens when `build_room_context(..., context_store=...)` is called. Some existing tests may need to stub Shadow injection to keep their scope narrow.

## A) ShadowReadService tests (`backend/app/tests/services/`)

Target: `backend/app/services/shadow_read_service.py`

- [x] `test_shadow_read_service_get_snapshot_by_version_returns_db_snapshot`
  - Setup: create `ShadowRepo` + multiple `ShadowVersion`s for the same `(entity_type, entity_id)`.
  - Assert: `get_snapshot_by_version(..., version_number=n)` returns that version’s `snapshot_json`, `version_number=n`.

- [x] `test_shadow_read_service_get_snapshot_by_commit_partial_match`
  - Setup: create `ShadowVersion(commit_sha="abc123...")`.
  - Assert: `get_snapshot_by_commit(commit_sha="abc123")` resolves the same version.

- [x] `test_shadow_read_service_forgejo_failure_falls_back_to_db`
  - Approach A (recommended): monkeypatch `ShadowReadService._read_json_file_from_forgejo` to raise `ShadowReadError`.
  - Assert: result uses `source="db"`, `is_stale=True`, and returns DB `snapshot_json`.

- [x] `test_shadow_read_service_missing_shadow_repo_raises_typed_error`
  - Assert: calling read with no `ShadowRepo` raises `ShadowRepoNotFound`.

- [x] `test_shadow_read_service_missing_shadow_version_raises_typed_error`
  - Setup: create `ShadowRepo` but no versions.
  - Assert: raises `ShadowVersionNotFound`.

Suggested fixture additions (sync):
- [ ] `shadow_owner_user(db) -> User` (creates a user for FK use)
- [ ] `create_shadow_repo(db, *, entity_type, entity_id, owner_id) -> ShadowRepo`
- [ ] `create_shadow_version(db, *, shadow_repo_id, version_number, commit_sha, snapshot_json, created_by_id) -> ShadowVersion`

## B) ShadowSummaryService tests (`backend/app/tests/services/`)

Targets:
- `backend/app/services/shadow_summaries.py`
- `backend/app/services/shadow_summary_service.py`

- [x] `test_summarize_user_llm_provider_redacts_keys` (already added in `backend/app/tests/services/test_shadow_summaries.py`)

- [x] `test_summarize_room_contains_active_bindings_shape`
  - Input: a room snapshot shaped like `build_room_snapshot` output.
  - Assert: summary includes `participants[*].participant_id/type/role/active` and `active_bindings[*].participant_id/type/persona_id/model_name/user_llm_provider_id`.

- [x] `test_shadow_summary_service_returns_summary_dispatch_result`
  - Setup: create `ShadowRepo` + `ShadowVersion` for an entity type and snapshot_json that the summarizer can parse.
  - Assert: `get_latest_summary` returns a `summary` field (not raw snapshot) and preserves `commit_sha/version_number/is_stale`.

- [ ] `test_shadow_summary_service_cache_key_stability` (optional)
  - If you want to validate caching logic without Redis:
    - monkeypatch `_get_cached_summary` / `_set_cached_summary` to track calls.
  - Assert: for the same `(repo_id, commit_sha)`, the cache key is stable.

Suggested fixture additions:
- [ ] `room_shadow_snapshot_json(room) -> dict` helper to generate test snapshot JSON
- [ ] `provider_shadow_snapshot_json(user_llm_provider) -> dict` helper that intentionally includes `api_key_encrypted` to ensure redaction

## C) ShadowContextLoader tests (`backend/app/tests/services/`)

Target: `backend/app/services/shadow_context_loader.py`

- [x] `test_shadow_context_loader_emits_missing_item_when_room_shadow_missing`
  - Setup: create a room in DB but do not create `ShadowRepo/ShadowVersion` for it.
  - Call: `build_shadow_context_items(room_id=..., agent_slug=None, ...)`.
  - Assert: returned items include `context_type="shadow.room.summary"` with payload containing `missing_shadow_snapshot=True`.

- [x] `test_shadow_context_loader_emits_missing_item_when_story_shadow_missing`
  - Setup: room with `story_id`, but story has no shadow repo/version.
  - Assert: includes `context_type="shadow.story.summary"` missing payload.

- [x] `test_shadow_context_loader_agent_scoped_items_use_binding_row`
  - Setup:
    - `AgentConfig(slug=...)`
    - room participant binding row for `(room_id, 'agent', participant_id=<slug>)`
    - shadow repo/version for agent (and optionally persona/provider)
  - Assert: includes `shadow.agent.summary`, plus `shadow.persona.summary` and `shadow.runtime.summary` when IDs exist.

- [x] `test_shadow_context_loader_runtime_provider_missing_is_embedded`
  - Setup: binding has `user_llm_provider_id` but provider has no shadow repo/version.
  - Assert: `shadow.runtime.summary` payload includes `user_llm_provider_missing` with `missing_shadow_snapshot=True`.

Suggested fixture additions (async + sync mix):
- [ ] `async_room_with_agent_binding(async_session) -> (Room, AgentConfig, RoomParticipantBinding)`
- [ ] `seed_shadow_for_entity(db, entity_type, entity_id, snapshot_json)` helper using sync `Session(engine)`

## D) Context provider + A2A integration tests (`backend/app/tests/services/`)

Targets:
- `backend/app/services/context_provider.py`
- `backend/app/services/agent_tools.py`

- [x] `test_build_room_context_logs_warning_on_shadow_loader_failure` (optional)
  - Monkeypatch `build_shadow_context_items` to raise.
  - Assert (caplog): warning log contains room_id and agent_slug.

- [x] `test_build_room_context_includes_shadow_items_when_context_store_provided`
  - Use `InMemoryContextStore`.
  - Setup minimal ShadowRepo/ShadowVersion data for room (and story if present).
  - Call `build_room_context(..., context_store=store, agent_slug=...)`.
  - Assert: `context.extra_contexts` contains at least one item with `source="shadow"`.

- [x] `test_a2a_tool_call_passes_agent_slug_to_build_room_context`
  - Monkeypatch `build_room_context` to capture kwargs, or monkeypatch `ContextItemStore.list` to ensure agent_slug scoping is honored.
  - Assert: `agent_slug` argument is provided in `_run_agent_for_tool_call`.

Important maintenance task (existing tests):
- [ ] Update existing `backend/app/tests/services/test_context_provider_extra_contexts.py` to stub Shadow injection
  - Reason: `build_room_context` now auto-adds Shadow items when a `context_store` is supplied.
  - Options:
    - monkeypatch `build_shadow_context_items` to return `[]` for those unit tests, OR
    - update expectations to include Shadow items (less ideal for unit scope).

## E) Documentation verification (non-test, but required deliverable)

- [IN PROGRESS] Update `backend/docs/shadow/ShadowPhase2Milestone2_ImplementationGuide.md`:
  - mark items `[~]` → `[x]` once tests above exist
  - mark optional caching tests if you decide to ship them

