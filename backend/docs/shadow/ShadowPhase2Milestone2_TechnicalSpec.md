# Shadow — Milestone 2 Technical Specification (Read-path + Context Provider)

This document specifies the Milestone 2 implementation for Shadow as a first-class, *invisible* context source for agents. It is written to be actionable for implementation and extensible for future entity types.

## Summary

Milestone 2 adds:

1. A **Shadow read service** that can load snapshots from Forgejo for `(entity_type, entity_id)` and also load pinned snapshots by `commit_sha` or `version_number`, with DB fallback.
2. Deterministic **“what to load” rules** driven by `room_participant_bindings` (room-scoped runtime truth).
3. A **context pipeline integration** that emits Shadow-derived context as `ContextItem`s (source=`shadow`) into the existing `extra_contexts` mechanism, including A2A tool calls with correct `agent_slug`.

All Shadow operations remain invisible to end users:

- Users do not authenticate to Forgejo.
- Users do not see Shadow repos, commit SHAs, or versions in UI.
- Shadow reads are best-effort; agent behavior degrades gracefully if Forgejo is unavailable.

## Related implementation context (current code)

- Shadow write service: `backend/app/services/shadow_service.py`
- Snapshot exporters (write side): `backend/app/services/shadow_exporters.py`
- Room runtime truth (Milestone 1.1): `backend/app/models.py` (`RoomParticipantBinding`)
- Room binding write-path (Milestone 1.1): `backend/app/api/routes/room_participant_bindings.py`
- Context pipeline:
  - `backend/app/services/context_provider.py` (`build_room_context`, `extra_contexts`)
  - `backend/app/services/context_store.py` (`ContextItem`, `ContextItemStore`, `RedisContextStore`)
  - `backend/app/services/agent_prompt.py` (renders `extra_contexts` into prompt)
  - `backend/app/services/agent_tools.py` (A2A tool calls)

## Goals and non-goals

### Goals

- **Forgejo-first reads**: latest snapshot comes from Forgejo when possible; fallback to DB `ShadowVersion.snapshot_json` if not.
- **Pinned reads**: can load snapshot at a specific `commit_sha` or `version_number` (via `ShadowVersion` metadata).
- **Deterministic context selection** for both:
  - room-wide context (room/story)
  - agent-scoped context (active persona + runtime model/provider)
- **Invisible transparency**: no user-facing exposure of Shadow mechanics; no UI changes required.
- **Performance**: cache reads by `(repo_name, commit_sha)` to avoid repeated Forgejo calls.

### Non-goals (Milestone 3)

- Async Forgejo IO via outbox/worker for writes (Milestone 3).
- Global “reference index” repo materialization (Milestone 3).
- Full backfill/reconciliation tooling (Milestone 3).

## Entity type contract

Shadow `entity_type` strings are part of an internal contract spanning:

- service account selection (token)
- repo naming (`{entity_type}-{entity_id_short}`)
- snapshot file naming (`{entity_type}.json`)
- context item typing/summary logic

Milestone 2 entity types (minimum viable for context):

- `room`
- `story`
- `agent`
- `persona`
- `llm_model`
- `user_llm_provider`

## ShadowReadService (Forgejo + DB fallback)

### Responsibilities

- Resolve the correct `ShadowRepo` from DB for `(entity_type, entity_id)`.
- Retrieve snapshot JSON:
  - **Preferred**: read `{entity_type}.json` from Forgejo at the latest commit (or at a pinned commit SHA).
  - **Fallback**: use `ShadowVersion.snapshot_json` from DB and mark result as stale.
- Return a normalized response envelope including provenance metadata.

### Proposed interface (Python)

```python
@dataclass(frozen=True)
class ShadowSnapshotResult:
    entity_type: str
    entity_id: uuid.UUID
    version_number: int | None
    commit_sha: str | None
    source: Literal["forgejo", "db"]
    is_stale: bool
    snapshot_json: dict[str, Any]

class ShadowReadService:
    def get_latest_snapshot(self, *, session: Session, entity_type: str, entity_id: uuid.UUID) -> ShadowSnapshotResult: ...
    def get_snapshot_by_version(self, *, session: Session, entity_type: str, entity_id: uuid.UUID, version_number: int) -> ShadowSnapshotResult: ...
    def get_snapshot_by_commit(self, *, session: Session, entity_type: str, entity_id: uuid.UUID, commit_sha: str) -> ShadowSnapshotResult: ...
```

### Forgejo fetch details

- Use the same per-entity-type service tokens as `ShadowService` (Forgejo access remains service-account scoped).
- Read file path: `{entity_type}.json` from the repo for that entity.
- If Forgejo read fails (network, 404, auth, SHA conflict, etc.), fallback to DB:
  - read latest `ShadowVersion` for the entity
  - return `source="db"`, `is_stale=True`

### Caching (Redis)

Cache key: `shadow:snapshot:{shadow_repo_id}:{commit_sha}` (or `{repo_name}:{commit_sha}`)

Value: JSON blob containing:

- `snapshot_json` (or a summarized form; see “Summaries”)
- `commit_sha`
- `version_number`
- `cached_at`

TTL recommendations:

- latest snapshot cache: 1–5 minutes
- pinned commit snapshot cache: 1–24 hours (commit SHA is immutable)

If Redis is unavailable, read-through still works (no hard dependency).

## Summaries (prompt-friendly views)

Milestone 2 introduces a summary layer that turns large snapshots into prompt-friendly, stable shapes.

### Summary format

All summaries should follow a consistent envelope:

```json
{
  "entity_type": "room",
  "entity_id": "…",
  "commit_sha": "…",
  "version_number": 12,
  "is_stale": false,
  "summary": { "…domain-specific fields…" }
}
```

### Recommended summary contents (minimum viable)

- `room`: title, story_id, participants, active bindings (participant_id/type → persona_id/model/provider)
- `story`: title, description, published/current version pointers (do not embed full graph unless needed)
- `agent`: slug, name, system prompt (or safe excerpt), capabilities, agent_personas list (persona IDs + nicknames)
- `persona`: name, description, a short “persona intent” snippet
- `llm_model`: display_name/model_id/provider_type/context_window
- `user_llm_provider`: provider_type/name/base_url/is_default/last_test_* + `api_key_present` (never include keys)

Implementation note:
- Summary functions should be pure and deterministic (same input snapshot → same output).

## Deterministic “what to load” rules (context selection)

### Inputs

- `room_id`
- `agent_slug` (optional; required for agent-scoped loading)
- Current DB projections:
  - `rooms`
  - `room_participants`
  - `room_participant_bindings` (active rows; ended_at IS NULL)

### Core addressing rule (no ambiguity)

For agents, always resolve:

`current_agent_slug` → `AgentConfig` → `(participant_type='agent', participant_id=<slug>)` binding row

This rule requires that agent `participant_id` is standardized to `AgentConfig.slug` (Milestone 1.1 Task 1).

### Load algorithm

1. **Room-wide**
   - Load latest `room` snapshot summary for `room_id`.
   - If room has `story_id`, load latest `story` snapshot summary for that story.
2. **Agent-scoped** (only if `agent_slug` provided)
   - Resolve agent by slug.
   - Find the agent participant’s active binding row for the room.
   - Load:
     - active persona summary (if `persona_id` set)
     - runtime model/provider summary (if `model_name` and/or `user_llm_provider_id` set)
   - Optionally include the `agent` snapshot summary for the agent itself (capabilities, config, persona library).

### ContextItem types

Emit `ContextItem`s using stable `context_type` strings:

- `shadow.room.summary`
- `shadow.story.summary`
- `shadow.agent.summary` (agent-scoped)
- `shadow.persona.summary` (agent-scoped)
- `shadow.runtime.summary` (agent-scoped; derived from binding row + provider snapshot)

## Feeding the existing context pipeline

### Where Shadow context is produced

Introduce a new service (or module) responsible for building `ContextItem`s:

`ShadowContextLoader.build_context_items(room_id, agent_slug)`:

- queries DB for bindings and agent resolution
- calls ShadowReadService for snapshots
- summarizes them
- returns a list of `ContextItem`s

### Where Shadow context is stored/attached

Milestone 2 should use the existing `ContextItemStore` pattern:

- Prefer writing Shadow items to `RedisContextStore` with an expiration (e.g., 1–5 minutes).
- `build_room_context` already loads items from `context_store.list(room_id, agent_slug)` and exposes them as `extra_contexts`.

This keeps Shadow fully invisible and pluggable:

- if store is unavailable, agents still run (just without Shadow context)
- if Forgejo is unavailable, fallback snapshots can still populate context (marked stale)

### A2A tool calls

`backend/app/services/agent_tools.py` must pass `agent_slug` into `build_room_context` for tool calls so agent-scoped items are correct.

Example adjustment (conceptual):

```python
context = await build_room_context(
    room_id=room_id,
    session=session,
    agent_slug=agent_slug,
    context_store=RedisContextStore(),
)
```

## Explicit examples

### Example 1: Building shadow context items (room-wide + agent-scoped)

Given:
- `room_id = 111…`
- `agent_slug = "storyadvisor"`

Expected emitted `ContextItem`s (illustrative):

```python
[
  ContextItem(
    id="shadow:room:111...:latest",
    room_id=room_id,
    agent_slug=None,
    context_type="shadow.room.summary",
    payload={...room summary...},
    source="shadow",
    created_at=now,
    expires_at=now + timedelta(minutes=2),
  ),
  ContextItem(
    id="shadow:story:222...:latest",
    room_id=room_id,
    agent_slug=None,
    context_type="shadow.story.summary",
    payload={...story summary...},
    source="shadow",
    created_at=now,
    expires_at=now + timedelta(minutes=5),
  ),
  ContextItem(
    id="shadow:agent:333...:latest",
    room_id=room_id,
    agent_slug="storyadvisor",
    context_type="shadow.agent.summary",
    payload={...agent summary...},
    source="shadow",
    created_at=now,
    expires_at=now + timedelta(minutes=5),
  ),
  ContextItem(
    id="shadow:persona:444...:latest",
    room_id=room_id,
    agent_slug="storyadvisor",
    context_type="shadow.persona.summary",
    payload={...persona summary...},
    source="shadow",
    created_at=now,
    expires_at=now + timedelta(minutes=5),
  ),
  ContextItem(
    id="shadow:runtime:binding:555...:active",
    room_id=room_id,
    agent_slug="storyadvisor",
    context_type="shadow.runtime.summary",
    payload={
      "model_name": "openai:gpt-4o-mini",
      "user_llm_provider": { "provider_type": "openai", "name": "My OpenAI", "api_key_present": True, ... },
      "binding": { "effective_at": "...", "participant_id": "storyadvisor", ... },
    },
    source="shadow",
    created_at=now,
    expires_at=now + timedelta(minutes=2),
  ),
]
```

### Example 2: Pinned loads (commit SHA)

When a room is “pinned” to a specific ShadowVersion (future UI or admin action), Milestone 2 supports deterministic reads:

- Fetch `ShadowVersion` (DB) by `(entity_type, entity_id, version_number)` to get `commit_sha`.
- Use `get_snapshot_by_commit(...)` to load the exact Forgejo file version.

This enables reproducible “what did the agent know at the time” debugging without exposing any Shadow UI to end users.

### Example 3: Extending to a new entity type

To add `entity_type="room_policy"` in the future:

1. Add a token setting + map entry in `Settings` and `SERVICE_ACCOUNT_MAP`.
2. Add an exporter for write-path snapshots (Milestone 1/3 style).
3. Add read-path summary logic and a new context type `shadow.room_policy.summary`.
4. Update the deterministic load rules to include it.

## Security and “invisible transparency”

- **Never expose** repo names, commit SHAs, or version numbers to end users.
- **Never store secrets** (plaintext or encrypted) in Shadow snapshots (provider snapshots must remain redacted).
- Shadow reads should be:
  - best-effort
  - time-bounded (timeouts)
  - observable (log warnings, include `is_stale` in payload)

## Operational considerations

- Logging:
  - warn on Forgejo failures and fallback usage (without leaking tokens/urls)
  - include `entity_type`, `entity_id`, `shadow_repo_id`, and `commit_sha` (server logs only)
- Metrics (optional):
  - cache hit rate
  - Forgejo latency/error rate
  - fallback rate to DB snapshots

## Milestone 2 “definition of done”

- `build_room_context(..., agent_slug=...)` includes Shadow-derived `extra_contexts` from `ContextItemStore`.
- A2A tool calls include agent-scoped Shadow context (not caller’s).
- Forgejo outage triggers DB fallback with `is_stale=true` and no hard failures.
- Provider snapshots remain redacted.

