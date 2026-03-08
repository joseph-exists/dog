# Context Issues Audit

Last reviewed: `2026-03-06`
Scope:
- [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py)
- [context_store.py](/home/josep/dog/backend/app/services/context_store.py)
- [context-provider-extra-contexts.md](/home/josep/dog/backend/app/services/service-docs/context-provider-extra-contexts.md)
- [event_sourcing_realtime_flow.md](/home/josep/dog/backend/app/services/service-docs/event_sourcing_realtime_flow.md)

## Purpose

This document replaces earlier speculative notes with an implementation-backed
audit.

Rule of use:
- treat code and tests as source of truth
- treat service docs as design notes unless they match implementation
- mark claims as `satisfied`, `unsatisfied`, or `doc drift`

## Executive Summary

Several claims that previously looked unsatisfied are already implemented:
- agent context includes live story runtime, not just top-level story metadata
- `active_for_context` filtering is already enforced in `build_room_context`
- room context ingestion APIs already exist and write to the same Redis-backed
  context store the agent context path reads
- room context create/update/delete already emit events, and the frontend
  already invalidates room-context queries on those events

The claims that still remain genuinely unsatisfied are narrower:
- no verified direct `agent -> shared storyRuntime` mutation path
- no verified auto-trigger of agents on story runtime transitions alone
- service docs do not accurately describe current `extra_contexts` merge rules,
  especially `system` and `shadow` ordering and context-type dedupe behavior

## Room Surface Implications

The current backend implementation supports a stronger Room surface than older
docs implied.

Verified implications for Room affordances:
- Room can serve as a story-aware agent runtime because `build_room_context`
  includes shared story runtime.
- Room can serve as a context-governance surface because message
  `active_for_context` flags and room context item APIs are both live.
- Room can support broader agent-governance UX because prompt-binding APIs are
  already adjacent to the same runtime model, even if some tool-policy controls
  are not yet surfaced in frontend.

Implication for frontend documentation:
- document current verified bridges first:
  message context curation, room context items, prompt bindings, story-aware agent replies
- document broader feature goals separately:
  runtime-triggered agents, direct agent runtime mutation, richer tool-policy editing

## Claim Review

### 1. “Only top-level story metadata is passed into room context”

Status: `false`

What implementation does:
- loads `Story` metadata into `story_data`
- loads shared room runtime from `RoomStoryProgress -> UserStoryProgress`
- resolves current node
- resolves currently available choices using current `story_state`
- reconstructs node chain
- includes `story_state`

Evidence:
- `RoomContext.story_runtime` exists:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L93)
- runtime projection is built from room progress:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L183)
- current node, choices, node chain, and state are assembled:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L216)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L223)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L230)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L257)

Conclusion:
- this claim should be removed from planning docs

### 2. “When runtime advances, rewinds, or resets, the new node/state should be loaded into context”

Status: `satisfied, but only on the next context build`

What implementation does:
- `build_room_context` recomputes `story_runtime` from the persisted shared
  progress record every time it runs
- if the underlying room runtime projection has changed, the next agent-context
  build will see the new node, choices, path, and state

Evidence:
- context is rebuilt from `RoomStoryProgress.active_progress_id` on each call:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L191)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L203)
- available choices are re-derived from current `story_state`:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L221)
- runtime APIs exist for start/advance/rewind/reset:
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L27)
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L45)
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L68)
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L94)
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L120)

Important limit:
- I did not find evidence that runtime transitions themselves automatically
  trigger a fresh agent run
- the update is visible on the next invocation of `build_room_context`, not as a
  standalone push into running agent state

### 3. “Agents only see messages marked active_for_context”

Status: `satisfied`

What implementation does:
- filters room messages inside `build_room_context` with
  `RoomMessage.active_for_context == True`

Evidence:
- filter in provider:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L272)
- flag mutation handled in event emitter:
  [event_emitter.py](/home/josep/dog/backend/app/services/event_emitter.py#L1111)

Conclusion:
- the old “thread a filter_active_context flag through the runner” task is stale
- current implementation is already active-only by default

### 4. “UI-managed room contexts are not wired yet”

Status: `false`

What implementation does:
- exposes room-context CRUD routes
- validates room membership/ownership
- writes to `ContextItemStore`
- defaults to `RedisContextStore`
- reads through the same store in `RoomContextService -> build_room_context`

Evidence:
- room-context routes exist:
  [room_contexts.py](/home/josep/dog/backend/app/api/routes/room_contexts.py#L20)
  [room_contexts.py](/home/josep/dog/backend/app/api/routes/room_contexts.py#L41)
  [room_contexts.py](/home/josep/dog/backend/app/api/routes/room_contexts.py#L76)
  [room_contexts.py](/home/josep/dog/backend/app/api/routes/room_contexts.py#L99)
- CRUD writes to `RedisContextStore` by default:
  [crud.py](/home/josep/dog/backend/app/crud.py#L2532)
  [crud.py](/home/josep/dog/backend/app/crud.py#L2592)
  [crud.py](/home/josep/dog/backend/app/crud.py#L2646)
  [crud.py](/home/josep/dog/backend/app/crud.py#L2713)
- `RoomContextService` also defaults to `RedisContextStore`:
  [agent_context.py](/home/josep/dog/backend/app/services/agent_context.py#L11)
- `ContextItemStore` and Redis implementation exist:
  [context_store.py](/home/josep/dog/backend/app/services/context_store.py#L29)
  [context_store.py](/home/josep/dog/backend/app/services/context_store.py#L68)

Conclusion:
- older notes claiming “no API surface for ingestion” are now wrong

### 5. “Room-context invalidation hooks are missing”

Status: `mostly false`

What implementation does:
- emits `room.context_item.created|upserted|deleted`
- frontend invalidates room-context queries on those events
- `build_room_context` reads the store fresh per invocation rather than serving
  a cached prompt object

Evidence:
- events emitted by CRUD:
  [crud.py](/home/josep/dog/backend/app/crud.py#L2623)
  [crud.py](/home/josep/dog/backend/app/crud.py#L2688)
  [crud.py](/home/josep/dog/backend/app/crud.py#L2730)
- event emitter routes them through room runtime event handling:
  [event_emitter.py](/home/josep/dog/backend/app/services/event_emitter.py#L414)
- frontend invalidates room contexts:
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts#L72)
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts#L276)

Limit:
- there is still no separate backend prompt-cache invalidation layer because
  there is no evidence of a cached `RoomContext` object beyond the underlying
  store contents

## Actual Unsatisfied Claims

### 1. Direct `agent -> shared storyRuntime` mutation is not verified

Status: `unsatisfied`

What I found:
- runtime mutation endpoints exist
- frontend `useRoomRuntime` calls those endpoints
- I did not find any agent service, room route, or tool path invoking
  `advance_room_runtime`, `rewind_room_runtime`, or `reset_room_runtime`

Evidence:
- runtime mutation path is user/runtime API focused:
  [useRoomRuntime.ts](/home/josep/dog/frontend/src/hooks/useRoomRuntime.ts#L106)
  [room_runtime.py](/home/josep/dog/backend/app/api/routes/room_runtime.py#L68)
- agent trigger path is message-driven:
  [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py#L365)

Interpretation:
- if the desired product behavior is agent-selected workflow progression, a
  backend contract is still missing or hidden elsewhere

### 2. Runtime transitions do not appear to auto-trigger agents

Status: `unsatisfied`

What I found:
- user messages trigger `run_agents_for_message`
- room runtime events are published to clients and used for UI invalidation
- no inspected backend handler binds runtime transition events to
  `run_agents_for_message`

Evidence:
- agent trigger entry point:
  [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py#L365)
- frontend only invalidates runtime on runtime events:
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts#L59)
  [useRoomStream.ts](/home/josep/dog/frontend/src/hooks/useRoomStream.ts#L264)
- event sourcing doc is generic and does not document an agent trigger path:
  [event_sourcing_realtime_flow.md](/home/josep/dog/backend/app/services/service-docs/event_sourcing_realtime_flow.md#L1)

Interpretation:
- if desired behavior is “advance story node -> orchestrator reacts
  automatically”, that contract is still missing from inspected implementation

### 3. Service docs do not match current `extra_contexts` merge behavior

Status: `doc drift`

What design note says:
- ordering is `seed -> backend -> frontend`
- `extra_contexts` normalization is planned

What implementation actually does:
- prepends `system.*` demo-derived contexts before store-backed contexts
- auto-adds shadow-derived items into the store on every context build when a
  store is provided
- sorts only store items with `source_priority = {seed, backend, frontend}`
- any other source, including `shadow` and `system`, falls to priority `99`
- dedupes by `context_type` with “last write wins”

Evidence:
- service doc claims:
  [context-provider-extra-contexts.md](/home/josep/dog/backend/app/services/service-docs/context-provider-extra-contexts.md#L25)
- implementation:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L358)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L440)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L455)
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L469)

Interpretation:
- the design note is no longer a precise description of behavior

### 4. Store cleanup and overwrite semantics are weak

Status: `partially unsatisfied`

What implementation does:
- Redis store appends with `rpush`
- expired items are filtered on read, not removed
- delete rewrites the entire Redis list
- `build_room_context` auto-adds shadow items on each call when a store is present
- context-provider dedupes at read time by `context_type`

Evidence:
- append-only add:
  [context_store.py](/home/josep/dog/backend/app/services/context_store.py#L75)
- expiry is read-time only:
  [context_store.py](/home/josep/dog/backend/app/services/context_store.py#L94)
- delete rewrites the list:
  [context_store.py](/home/josep/dog/backend/app/services/context_store.py#L114)
- shadow auto-add on every build:
  [context_provider.py](/home/josep/dog/backend/app/services/context_provider.py#L440)

Interpretation:
- behavior works, but it relies on read-time filtering and dedupe rather than a
  cleaner persisted canonical state
- this is not a blocker, but it is a real maintenance risk

## Test Coverage That Supports The Current State

- extra-context ordering:
  [test_context_provider_extra_contexts.py](/home/josep/dog/backend/app/tests/services/test_context_provider_extra_contexts.py#L13)
- agent-specific scoping:
  [test_context_provider_extra_contexts.py](/home/josep/dog/backend/app/tests/services/test_context_provider_extra_contexts.py#L71)
- shadow contexts included:
  [test_context_provider_shadow.py](/home/josep/dog/backend/app/tests/services/test_context_provider_shadow.py#L20)
- prompt includes extra contexts:
  [test_agent_prompt_extra_contexts.py](/home/josep/dog/backend/app/tests/services/test_agent_prompt_extra_contexts.py#L10)
- in-memory store semantics:
  [test_context_store.py](/home/josep/dog/backend/app/tests/services/test_context_store.py#L12)

## Task List

### P0

- Add a backend audit task for “agent-driven story runtime mutation”:
  determine whether this should be a new tool, a room action, or an orchestrator-only contract.
- Add a backend audit task for “runtime transition triggers agent run”:
  decide whether runtime events should invoke `run_agents_for_message` or a new dedicated runtime-trigger pipeline.

### P1

- Update [context-provider-extra-contexts.md](/home/josep/dog/backend/app/services/service-docs/context-provider-extra-contexts.md)
  so it describes current implementation and clearly labels future work.
- Expand source-priority documentation to cover `system` and `shadow` explicitly.
- Decide whether `extra_contexts` dedupe-by-`context_type` is the intended contract.

### P2

- Decide whether Redis list storage is sufficient long term or whether room
  contexts should move to a keyed structure or database persistence model.
- Add cleanup behavior for expired Redis context items if list growth becomes a problem.
