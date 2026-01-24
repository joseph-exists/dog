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


USE CASE ALPHA:
Currently the top level story (without any node objects, their relationships, or the change nodes that define their state changes and requirements) are passed into the room context.  

Needed outcome: within a room that has a story:

The story is loaded (and remains loaded)
- the first node is loaded
- the first set of choices and state requirements for that node is loaded

within the room, an event (could be user or agent driven or some other mechanism) occurs.  that event triggers a state change - one of the choices is made, and the second node - with it's set of choices and state - is loaded into context.  

the users can also 'rewind' nodes (in some cases) and reset the context/state to a prior state.  so if they are at node4 in the tree, and rewind to node2, the state reverts, and node2 is their new context.

USE CASE BETA:
We will (in the near future) allow users to adjust a) the prompts for the agents in a room, and b) the tools that are currently available in the room.  

USE CASE THREE: these two will be linked through a currently not designed interface/mechanic.  It is possible for a story to have tools only be exposed in node 3, for example.




...

Here’s the call path for build_room_context and where it fits in a UI-managed “room context” feature, with concrete file refs you can follow.

Call path (runtime)

REST: user sends message → rooms.py (line 333) → run_agents_for_message(...) → agent_runner.py (line 252) → run_agent_for_room_streaming(...) → agent_runner_streaming.py (line 56) → RoomContextService.build(...) → agent_context.py (line 20) → build_room_context(...) in context_provider.py (line 66).
WebSocket: websocket.py (line 352) → run_agents_for_message(...) → same chain as above.
A2A tool calls also do this path directly in agent_tools.py (line 124) (uses build_room_context with RedisContextStore()).
What build_room_context actually does

Loads room, story, recent messages, participants → context_provider.py (line 66).

If a context_store is passed, it adds Shadow-derived context items every time it runs, then reads the store and exposes items as RoomContext.extra_contexts:

Adds items: context_provider.py (line 194) → build_shadow_context_items(...) in shadow_context_loader.py (line 65).

Reads items: context_provider.py (line 208) → context_store.list(...), filters agent-scoped items, sorts by source and created_at.

That means, today, the only production “context add” is Shadow auto-injection. Any “room context” you want the UI to manage isn’t wired in yet.

Where the store lives

RedisContextStore uses a Redis list at room:{room_id}:contexts → context_store.py (line 103).

It is append-only (rpush) with optional TTL inside the item, but no delete/update/list-by-id APIs.

Why this matters for a UI “room context manager”

To let the UI add/modify context items, you’ll need an explicit API that calls ContextItemStore.add(...) (and likely delete/replace functionality). 

The design note already hints at this: context-provider-extra-contexts.md suggests add_context_item(...) and a thin service wrapper.

Concrete places to extend

Service layer: add a small wrapper or method around ContextItemStore.add(...) (e.g., new function in context_store.py or a new service).

API: create routes for POST /rooms/{room_id}/contexts (and optionally DELETE or PATCH) that validate membership and write to Redis.

If you need deterministic ordering or replace-by-id, you’ll need to decide whether to:

keep Redis list and add removal logic, or
move to a hash/set keyed by ContextItem.id.

