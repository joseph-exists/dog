# Shadow — Milestone 2 Implementation Guide (Atomic Task List)

This guide converts `backend/docs/shadow/ShadowPhase2Milestone2_TechnicalSpec.md` into an ordered list of atomic implementation tasks. Each task is meant to be independently reviewable and testable.

## Guiding principles

- Shadow remains invisible: no end-user UI exposure of repos/SHAs/versions.
- Forgejo reads are best-effort: DB fallback is required and must be explicit (`is_stale=true`).
- All context integration flows through `ContextItemStore` → `RoomContext.extra_contexts`.
- Deterministic mapping: `agent_slug` → `AgentConfig` → `(participant_type='agent', participant_id=<slug>)` binding row.

## Phase 0 — Pre-flight (no behavior changes)

1. **Confirm entity_type strings**
   - Lock (Milestone 2 minimum): `room`, `story`, `agent`, `persona`, `llm_model`, `user_llm_provider`.
   - Reserve now (high-value reusable/reference types):
     - `room_policy` (room-level policy/config artifact)
     - `prompt` (system prompts + reusable templates)
     - `tool` (tool definitions/metadata)
     - `mcp_server` (MCP server configs/manifests; never secrets)
     - `external_doc` (snapshotted external documentation, e.g. `pydantic-ai-v2`)
     - `context_pack` (curated bundles of references to other entities)
     - `reference_index` (graph/index of references to pinned SHAs across entities)
   - Verify `SERVICE_ACCOUNT_MAP` and usernames exist for each (write + read use same tokens). (Owner working on this)
   - For each reserved type, document:
     - ownership model (who “owns” the repo)
     - redaction rules (what must never be stored)
     - snapshot filename convention (still `{entity_type}.json`)

2. [x] **Add spec references to docs**
   - Ensure `backend/shadow-work.md` points to:
     - `backend/docs/shadow/ShadowPhase2Milestone2_TechnicalSpec.md`
     - `backend/docs/shadow/ShadowPhase2Milestone2_ImplementationGuide.md`

## Phase 1 — Shadow read service (core)

3. [x] **Create `ShadowSnapshotResult` envelope type**
   - New dataclass: `entity_type`, `entity_id`, `version_number`, `commit_sha`, `source`, `is_stale`, `snapshot_json`.

4. [x] **Implement `ShadowReadService` skeleton**
   - New module: `backend/app/services/shadow_read_service.py`.
   - Public methods:
     - `get_latest_snapshot(session, entity_type, entity_id)`
     - `get_snapshot_by_version(session, entity_type, entity_id, version_number)`
     - `get_snapshot_by_commit(session, entity_type, entity_id, commit_sha)`

5. [x] **DB resolution: `ShadowRepo` + `ShadowVersion` lookups**
   - Use `ShadowService.get_shadow_repo(...)` / `get_version(...)` patterns or direct `select(...)`.
   - Define behavior when no repo/version exists:
     - return a typed error (preferred) or raise a `ValueError` with a stable message.

6. [x] **Forgejo file read implementation**
   - Read `{entity_type}.json` from Forgejo repo using service token.
   - Required: time-bounded call(s) + error handling.
   - On failure: fall back to DB snapshot_json.

7. [x] **DB fallback path**
   - Load latest/pinned `ShadowVersion.snapshot_json`.
   - Return `source="db"`, `is_stale=True`.

8. [~] **Unit tests for ShadowReadService**
   - New tests:
     - “Forgejo failure falls back to DB”
     - “Pinned version lookup resolves commit SHA”
   - Use mocks/stubs for Forgejo client calls.

## Phase 2 — Redis caching for reads

9. [x] **Define cache key scheme**
   - `shadow:summary:{shadow_repo_id}:{commit_sha}`
   - Decide TTLs:
     - latest: ~2–5 minutes
     - pinned: ~1–24 hours

10. [x] **Implement read-through cache layer**
   - In a summary service (recommended), before summary build:
     - check Redis for `(repo_id, commit_sha)`
   - After successful summary build:
     - store into Redis with TTL.
   - If Redis unavailable: proceed without cache.

11. [ ] **Add tests for caching behavior** (optional if time constrained)
   - Cache hit bypasses Forgejo.
   - Cache miss calls Forgejo then populates cache.

## Phase 3 — Summaries (prompt-friendly transforms)

12. [x] **Create summary functions module**
   - New module: `backend/app/services/shadow_summaries.py`
   - Pure functions:
     - `summarize_room(snapshot_json) -> dict`
     - `summarize_story(snapshot_json) -> dict`
     - `summarize_agent(snapshot_json) -> dict`
     - `summarize_persona(snapshot_json) -> dict`
     - `summarize_llm_model(snapshot_json) -> dict`
     - `summarize_user_llm_provider(snapshot_json) -> dict`

13. [x] **Enforce redaction invariants**
   - Ensure summaries never include secret fields.
   - Explicitly include `api_key_present` only (boolean).

14. [~] **Add summary unit tests**
   - “provider summary never includes api_key / api_key_encrypted”
   - “room summary includes participants + active_bindings shape”

## Phase 4 — Deterministic “what to load” rules (binding-driven)

15. [~] **Implement binding resolution helper**
   - Implemented inside `backend/app/services/shadow_context_loader.py` (no separate module).
   - Inputs: `room_id`, `agent_slug`, `AsyncSession`.
   - Outputs:
     - the active binding row for `(room_id, 'agent', agent_slug)` (or None).

16. [x] **Implement agent_slug → AgentConfig resolution**
   - Query by slug only (no UUID path).
   - If not found: return a stable error (“agent not found”) and skip agent-scoped items.

17. [x] **Define “what to load” algorithm as code**
   - New module: `backend/app/services/shadow_context_loader.py`
   - Public API:
     - `async def build_shadow_context_items(room_id, agent_slug, session) -> list[ContextItem]`
   - Must:
     - load room-wide items (room, story if exists)
     - load agent-scoped items (agent, persona, runtime/provider/model)
     - attach `is_stale` in payload envelopes

## Phase 5 — Feed the existing context pipeline

18. [x] **Write Shadow-derived ContextItems into ContextItemStore**
   - Decide the write point:
     - recommended: on-demand (when building context) with short TTLs.
   - Implement:
     - after building Shadow context items, call `await context_store.add(...)` for each.

19. [x] **Update `build_room_context` usage sites to pass `agent_slug`**
   - Ensure all agent runs pass the agent_slug when available.
   - Mandatory: A2A tool path must pass `agent_slug` (currently it doesn’t).

20. [x] **Update A2A tool call path**
   - In `backend/app/services/agent_tools.py` `_run_agent_for_tool_call`, call:
     - `build_room_context(..., agent_slug=agent_slug, context_store=...)`

21. [ ] **Add integration tests for agent_slug-scoped extra_contexts**
   - Extend `backend/app/tests/services/test_context_provider_extra_contexts.py`:
     - add items with `agent_slug=None` + `agent_slug="storyadvisor"`
     - verify `build_room_context(agent_slug="storyadvisor")` includes both global and agent-scoped items

## Phase 6 — Operational hardening

22. [~] **Add logging + safe error handling**
   - All Forgejo failures must log warnings without tokens.
   - All fallbacks must mark `is_stale=true`.

23. [~] **Add timeouts and limits**
   - Avoid unbounded Forgejo reads and overly large payloads.
   - Consider truncating summaries to safe sizes.

24. [ ] **Document extension recipe**
   - Add a short “How to add a new entity_type” section to the Technical Spec (or keep here).

## Adjustments made during implementation

- Shadow summary caching implemented via `backend/app/services/shadow_summary_service.py` (not directly in `ShadowReadService`).
- A2A tool calls now pass `agent_slug` and use `RedisContextStore` for shadow context integration.
- Agent resolution in `build_room_context` is **slug-first** with legacy UUID fallback.
- Binding resolution lives inside `shadow_context_loader.py` rather than a separate helper module.

## Definition of done (Milestone 2)

- `build_room_context(..., agent_slug=...)` includes Shadow-derived items in `extra_contexts`.
- A2A tool calls include correct agent-scoped Shadow context.
- Forgejo outage triggers DB fallback with `is_stale=true` and agents still run.
- Provider summaries never contain secrets.
