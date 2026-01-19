Context Provider: Multi-Source Context Extension

Goal
Extend backend/app/services/context_provider.py to aggregate multiple context sources:
- room seed data
- backend hotloads
- frontend uploads
- per-agent scoping (optional)

Design Summary
- Introduce a ContextItem concept stored in DB eventually; initially backed by a pluggable store.
- Add extra_contexts to RoomContext for normalized context payloads.
- Merge extra contexts deterministically and surface them in agent prompts.

Context Item Shape (normalized)
- id: str
- room_id: uuid.UUID
- agent_slug: str | None  # None = room-wide, else scoped to agent
- context_type: str       # e.g., room_seed, hotload, upload
- payload: dict[str, Any]
- source: str             # seed | backend | frontend
- created_at: datetime
- expires_at: datetime | None

Aggregation Rules
- RoomContext should include room-wide items plus agent-specific items when agent_slug is provided.
- Order by source priority (seed → backend → frontend), then created_at.
- Normalize into RoomContext.extra_contexts: list[dict[str, Any]] with {context_type, payload, source}.

API Changes (initial)
- build_room_context(
    *, room_id: uuid.UUID, session: AsyncSession, message_limit: int = 20,
    agent_slug: str | None = None,
    context_store: ContextItemStore | None = None
  ) -> RoomContext
- RoomContext gains extra_contexts: list[dict[str, Any]]

Context Store Interface (initial)
- async def add(item: ContextItem) -> None
- async def list(room_id: uuid.UUID, agent_slug: str | None = None) -> list[ContextItem]

Implementation Tasks
1) Models + Types
   - Add ContextItem dataclass (services layer) with the fields above.
   - Extend RoomContext with extra_contexts: list[dict[str, Any]].
   - Update any dependent typing references.

2) Context Store Abstraction
   - Create backend/app/services/context_store.py with ContextItemStore protocol.
   - Implement InMemoryContextStore for now (simple dict keyed by room_id).

3) Context Provider Aggregation
   - Update build_room_context signature to accept agent_slug and context_store.
   - Load extra contexts from context_store if provided.
   - Apply ordering rules and attach to RoomContext.extra_contexts.

4) Prompt Integration
   - Update backend/app/services/agent_prompt.py to append extra_contexts
     in a structured block (e.g., "Additional context:").
   - Ensure formatting is stable and deterministic.

5) API Surface for Ingestion
   - Add a simple service helper for adding contexts:
     - add_context_item(room_id, agent_slug, context_type, payload, source, expires_at=None)
   - This can live in context_store.py or a small service wrapper.

6) Tests (minimum)
   - Add tests for RoomContext.extra_contexts inclusion + ordering.
   - Add tests for agent_slug scoping (room-wide + agent-specific).
   - Add tests for prompt formatting in agent_prompt.py (extra contexts appear in output).
   - Add tests for InMemoryContextStore add/list behavior.

Suggested Test Files
- backend/app/tests/services/test_context_provider_extra_contexts.py
- backend/app/tests/services/test_context_store.py
- backend/app/tests/services/test_agent_prompt_extra_contexts.py

Notes / Future Work
- Replace InMemoryContextStore with DB-backed ContextItem model and table.
- Add versioning or snapshots once data persistence is required.
- Add expiration cleanup task for expires_at when present.
