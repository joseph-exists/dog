# Frontend Demo Engineering — Ontology Reference

> Canonical dictionary and concordance for frontend engineers building demos. Every definition includes validation steps to confirm accuracy.

## Document Purpose & Audience

**Purpose:**
This document establishes the shared vocabulary, entity relationships, and architectural patterns that all demo implementation guides reference. It serves as the canonical "dictionary and concordance" for frontend engineers building demos in this codebase.

**Audience:**
Existing frontend engineers familiar with React and TypeScript who need to understand:
- The specific entity model and how data flows through the system
- Which ViewModels exist and what transformations they perform
- Which hooks to use for which operations
- Where to extend the system vs. where to add new constructs

**How to Use This Document:**
- **As a reference** — Look up specific entities, ViewModels, or hooks when building
- **As a map** — Understand relationships between components before diving into code
- **As a glossary** — Use consistent terminology when discussing features with the team
- **As a verification tool** — Each definition includes validation steps to confirm accuracy

**Validation Philosophy:**
Every definition in this document includes a **Verify** block—a concrete step an engineer can take to confirm the statement is accurate in the current codebase. This serves two purposes:
1. **Trust but verify** — Engineers can confirm claims before building on them
2. **Living documentation** — When verification fails, the document needs updating

Verification steps may include: file paths to inspect, grep commands to run, type signatures to check, or runtime behaviors to observe in the browser.

**Relationship to Other Guides:**
This ontology is the foundation. The following guides build upon it:
- Guide A: Context Manipulation Demos
- Guide B: Story Runtime Navigation Demos
- Guide C: Hidden Orchestrator Demos

Each guide assumes familiarity with the ontology and will reference terms defined here without re-explaining them.

---

## Entity Dictionary

### Core Entities

#### Room

The central container for conversations. All messages, participants, and runtime state belong to a room.

| Field | Type | Notes |
|-------|------|-------|
| `room_id` | UUID | Primary key (note: NOT `id`) |
| `title` | string \| null | Display name |
| `story_id` | UUID \| null | Optional linked story for runtime |
| `creator_id` | UUID | Owner reference |

**Relationships:**
- Has many → Messages
- Has many → Participants (users and agents)
- Has one → RoomStoryProgress (if story attached)

**Verify:** Open `frontend/src/services/roomService.ts` and confirm `RoomViewModel` interface matches these fields. Run `grep "room_id" frontend/src/client/types.gen.ts` to see the SDK type.

---

#### Message

A single utterance in a room from a user or agent.

| Field | Type | Notes |
|-------|------|-------|
| `message_id` | UUID | Primary key |
| `room_id` | UUID | Parent room |
| `sender_type` | `"user"` \| `"agent"` \| `"agent_internal"` | Origin type |
| `content` | string | Message body |
| `ui_components` | UIComponent[] \| null | AG-UI payloads |
| `active_for_context` | boolean | Included in agent context window |
| `is_pinned` | boolean | Marked as important |

**Relationships:**
- Belongs to → Room
- May contain → UIComponents (embedded)

**Verify:** Check `MessageViewModel` in `frontend/src/services/roomService.ts`. Confirm `sender_type` includes `"agent_internal"` for A2A messages.

---

#### Participant

A user or agent that has joined a room.

| Field | Type | Notes |
|-------|------|-------|
| `participant_id` | UUID \| string | UUID for users, slug for agents |
| `participant_type` | `"user"` \| `"agent"` | Discriminator |
| `role` | `"owner"` \| `"member"` | Permission level |
| `active` | boolean | Currently in room |

**Relationships:**
- Belongs to → Room
- References → User OR AgentConfig (based on type)

**Verify:** In `frontend/src/services/roomService.ts`, find `ParticipantViewModel` and note the `display_name` derivation logic that looks up user/agent details.

---

#### AgentConfig

Configuration for an AI agent that can participate in rooms.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `slug` | string | URL-safe identifier (used as `participant_id`) |
| `name` | string | Display name |
| `model_name` | string | LLM model identifier |
| `system_prompt` | string | Agent instructions |
| `participation_mode` | `"always"` \| `"mentioned"` \| `"passive"` | When agent responds |
| `provider` | string \| null | LLM provider (e.g., "anthropic", "openai") |

**Key Insight:** `participation_mode: "always"` is required for agents to respond to synthetic messages in demos.

**Verify:** Run `grep "participation_mode" frontend/src/client/types.gen.ts` to see all valid modes.

---

#### Story

A branching narrative structure with nodes and choices.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `title` | string | Display name |
| `current_version` | number | Draft version |
| `published_version` | number \| null | Live version (null if unpublished) |
| `is_published` | boolean | Publication status |

**Relationships:**
- Has many → StoryNodes (per version)
- Has many → NodeChoices (via nodes)
- Has many → StoryStateVariables (per version)

**Verify:** Check `frontend/src/client/types.gen.ts` for `StoryPublic` interface.

---

#### StoryNode

A single location/scene in a story.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `story_id` | UUID | Parent story |
| `story_version` | number | Version this node belongs to |
| `title` | string | Node name (shown in UI) |
| `content` | string | Narrative text |
| `is_start_node` | boolean | Entry point (exactly one per version) |
| `is_end_node` | boolean | Terminal node |

**Relationships:**
- Belongs to → Story
- Has many → NodeChoices (outbound)

**Verify:** In browser devtools, inspect a runtime response and confirm `current_node` contains these fields.

---

#### NodeChoice

A transition between story nodes, optionally with state conditions.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `from_node_id` | UUID | Source node |
| `to_node_id` | UUID | Destination node |
| `text` | string | Choice label shown to user |
| `requires_state` | Record<string, any> \| null | Conditions to show choice |
| `sets_state` | Record<string, any> \| null | State mutations when chosen |

**Key Insight:** Conditional branching uses `requires_state` for visibility and `sets_state` for mutations. Both are JSON objects compared against `story_state`.

**Verify:** In `frontend/src/services/roomRuntimeService.ts`, find `ChoiceViewModel` and trace how `requires_state` is exposed.

---

### Runtime Entities

#### UserStoryProgress

Tracks an individual user's journey through a story. This is the source of truth for "where am I in the story."

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `user_persona_id` | UUID | Links to UserPersona |
| `story_id` | UUID | Which story |
| `story_version` | number | Locked to published version |
| `current_node_id` | UUID | Where the user currently is |
| `story_state` | Record<string, any> | Accumulated state from choices |
| `head_version` | number | Optimistic concurrency (choice count) |

**Key Insight:** `story_state` accumulates via `sets_state` from each choice taken. The `head_version` increments with each advance, enabling one-step rewind.

**Verify:** Make a choice in a demo, then inspect Network tab for the `PUT /rooms/{id}/runtime/advance` response. Confirm `story_state` reflects accumulated values.

---

#### RoomStoryProgress

Links a room to a specific user's story progress, enabling shared story experiences.

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID | Primary key |
| `room_id` | UUID | Parent room (unique constraint) |
| `story_id` | UUID | Which story |
| `story_version` | number | Published version |
| `active_progress_id` | UUID | Points to UserStoryProgress |
| `revision` | number | Optimistic concurrency for room-level ops |

**Key Insight:** The `revision` field is critical—all runtime mutations require `expected_revision` to prevent race conditions. A 409 response means someone else changed the runtime.

**Relationships:**
- Belongs to → Room (one-to-one)
- References → UserStoryProgress (the active progress)

**Verify:** In `frontend/src/hooks/useRoomRuntime.ts`, find where `expected_revision` is passed to mutations.

---

#### RoomRuntimePublic (API Projection)

The backend's combined view of room story state. This is what the API returns—not a stored entity but a projection.

| Field | Type | Notes |
|-------|------|-------|
| `room_id` | UUID | Room reference |
| `story_id` | UUID | Story reference |
| `story_version` | number | Active version |
| `revision` | number | From RoomStoryProgress |
| `head_choice_id` | UUID \| null | Last choice made (enables rewind) |
| `current_node` | StoryNodePublic | Full node data |
| `node_chain` | StoryNodePublic[] | Path taken (breadcrumb) |
| `available_choices` | NodeChoicePublic[] | Valid next choices (filtered by state) |
| `story_state` | Record<string, any> | Current accumulated state |
| `can_rewind` | boolean | Has history to undo |
| `can_reset` | boolean | Not at start node |

**Key Insight:** `available_choices` is pre-filtered by the backend—only choices whose `requires_state` matches `story_state` are returned.

**Verify:** Call `GET /api/v1/rooms/{roomId}/runtime` in browser devtools and inspect the response shape.

---

#### Persona & UserPersona

Lightweight identity layer that connects users to story progress.

| Entity | Purpose |
|--------|---------|
| **Persona** | A named identity (e.g., "The Explorer") |
| **UserPersona** | Links a User to a Persona they can play as |

**Relationships:**
```
User → UserPersona → Persona
         ↓
   UserStoryProgress
```

**Why It Exists:** Allows one user to have multiple story progress records (different personas, different playthroughs).

**Verify:** In a seed script, trace how `user_persona_id` connects to `UserStoryProgress` creation during runtime initialization.

---

## ViewModel Glossary

### Why ViewModels?

ViewModels are the **transformation layer** between raw API types (from `src/client/types.gen.ts`) and what components actually need. They exist because:

1. **API types are transport-optimized** — UUIDs, normalized references, nullable fields
2. **Components need display-optimized data** — Resolved names, computed flags, formatted dates
3. **Caching happens at the ViewModel level** — User/agent lookups are cached to prevent N+1 calls

**The Rule:** Components consume ViewModels, never raw API types. If you see `RoomPublic` or `RoomMessagePublic` in a component, flag it.

```
API Response (RoomMessagePublic)
        ↓
   Service transforms
        ↓
ViewModel (MessageViewModel)  ← Components use this
```

**Verify:** Open any component in `frontend/src/components/Rooms/` and confirm imports reference `*ViewModel` types from services, not `*Public` types from client.

---

### RoomViewModel

**Source:** `RoomPublic` → **Target:** `RoomViewModel`

**Location:** `frontend/src/services/roomService.ts`

| Added/Transformed Field | Source | Notes |
|------------------------|--------|-------|
| `created_at` | string → Date | Parsed for display/sorting |
| `last_activity` | string → Date | Parsed |
| `participant_count` | Enriched | Optional count from list endpoint |
| `unread_count` | Enriched | Optional unread badge |

**Transformation Function:** `transformRoom()`

**Verify:** In `roomService.ts`, find `transformRoom` and confirm it parses date strings to Date objects.

---

### MessageViewModel

**Source:** `RoomMessagePublic` → **Target:** `MessageViewModel`

**Location:** `frontend/src/services/roomService.ts`

This is the richest ViewModel—it resolves sender identity and computes permission flags.

| Added/Transformed Field | Source | Notes |
|------------------------|--------|-------|
| `sender_name` | Looked up | Resolved from user/agent cache |
| `agent_name` | Looked up | Populated if sender is agent |
| `is_own_message` | Computed | `sender_id === currentUserId` |
| `can_edit` | From API | Backend-computed permission |
| `can_delete` | From API | Backend-computed permission |
| `can_pin` | From API | Backend-computed permission |
| `created_at` | string → Date | Parsed |

**Key Insight:** Permission flags (`can_edit`, `can_delete`, `can_pin`) come from the backend—never compute these client-side. The backend considers ownership, roles, and time windows.

**Caching:** Uses `userCache` and `agentCache` Maps to avoid redundant lookups when transforming message lists.

**Transformation Function:** `transformMessage()`

**Verify:** In `roomService.ts`, find `transformMessage` and trace how `sender_name` is resolved via cache lookups.

---

### ParticipantViewModel

**Source:** `RoomParticipantPublic` → **Target:** `ParticipantViewModel`

**Location:** `frontend/src/services/roomService.ts`

| Added/Transformed Field | Source | Notes |
|------------------------|--------|-------|
| `display_name` | Looked up | From user or agent details |
| `avatar_url` | Looked up | Optional, from user profile |
| `joined_at` | string → Date | Parsed |
| `left_at` | string → Date \| null | Parsed if present |

**Key Insight:** `participant_id` is a UUID for users but a **slug** for agents. The transformation logic detects this (UUID format check) and calls the appropriate lookup.

**Transformation Function:** `transformParticipant()`

**Verify:** Add an agent to a room, then inspect `ParticipantViewModel` in React DevTools. Confirm `display_name` shows the agent's name, not its slug.

---

### RoomRuntimeViewModel

**Source:** `RoomRuntimePublic` → **Target:** `RoomRuntimeViewModel`

**Location:** `frontend/src/services/roomRuntimeService.ts`

The runtime ViewModel is the richest transformation—it flattens nested structures and provides derived navigation flags.

| Added/Transformed Field | Source | Notes |
|------------------------|--------|-------|
| `roomId` | `room_id` | Camel-cased |
| `storyId` | `story_id` | Camel-cased |
| `storyVersion` | `story_version` | Camel-cased |
| `revision` | Direct | Optimistic concurrency token |
| `headChoiceId` | `head_choice_id` | Last choice (for one-step rewind) |
| `currentNode` | `current_node` → NodeViewModel | Transformed nested object |
| `nodeChain` | `node_chain` → NodeViewModel[] | Transformed array |
| `availableChoices` | `available_choices` → ChoiceViewModel[] | Transformed array |
| `storyState` | `story_state` | Direct pass-through |
| `hasRuntime` | Computed | `true` (presence indicator) |
| `isAtEndNode` | Computed | `currentNode.isEndNode` |
| `canRewind` | From API | Has undo history |
| `canReset` | From API | Not at start |

**Key Insight:** When the API returns 404/410 for runtime, the hook returns `null`—not an error. Check `hasRuntime` or null-check before accessing fields.

**Transformation Function:** `toViewModel()`

**Verify:** In `frontend/src/services/roomRuntimeService.ts`, find `toViewModel` and trace how `currentNode` is transformed via `toNodeViewModel()`.

---

### NodeViewModel

**Source:** `StoryNodePublic` → **Target:** `NodeViewModel`

**Location:** `frontend/src/services/roomRuntimeService.ts`

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Direct | Node UUID |
| `title` | Direct | Display name |
| `content` | Direct | Narrative text |
| `contentFormat` | `content_format` | `"text"` \| `"html"` \| `"json"` |
| `isStartNode` | `is_start_node` | Entry point flag |
| `isEndNode` | `is_end_node` | Terminal flag |
| `nodeType` | `node_type` | Optional classification tag |

**Key Insight:** `contentFormat` determines rendering strategy. HTML content is sanitized via DOMPurify before rendering. JSON content is parsed for structured display.

**Transformation Function:** `toNodeViewModel()`

**Verify:** Find a story with HTML content nodes. Inspect the rendered output and confirm scripts/unsafe tags are stripped.

---

### ChoiceViewModel

**Source:** `NodeChoicePublic` → **Target:** `ChoiceViewModel`

**Location:** `frontend/src/services/roomRuntimeService.ts`

| Field | Source | Notes |
|-------|--------|-------|
| `id` | Direct | Choice UUID |
| `text` | Direct | Button/link label |
| `toNodeId` | `to_node_id` | Destination node |
| `requiresState` | `requires_state` | Visibility conditions (already filtered by backend) |
| `setsState` | `sets_state` | State mutations on selection |
| `order` | Direct | Display ordering |

**Key Insight:** By the time choices reach the frontend, they're already filtered—`requiresState` has been evaluated server-side. The frontend displays all returned choices without additional filtering.

**Transformation Function:** `toChoiceViewModel()`

**Verify:** Create a story with conditional choices. Confirm that when `story_state` doesn't match `requires_state`, the choice is absent from `availableChoices`—not present but hidden.

---

### ViewModel Summary Table

| ViewModel | Service | Transforms From | Key Additions |
|-----------|---------|-----------------|---------------|
| `RoomViewModel` | roomService | `RoomPublic` | Parsed dates |
| `MessageViewModel` | roomService | `RoomMessagePublic` | Resolved names, permissions, `is_own_message` |
| `ParticipantViewModel` | roomService | `RoomParticipantPublic` | Resolved `display_name`, avatar |
| `RoomRuntimeViewModel` | roomRuntimeService | `RoomRuntimePublic` | Nested transforms, navigation flags |
| `NodeViewModel` | roomRuntimeService | `StoryNodePublic` | Camel-cased, format indicator |
| `ChoiceViewModel` | roomRuntimeService | `NodeChoicePublic` | Camel-cased state fields |

**Verify:** Run `grep "ViewModel" frontend/src/services/*.ts` to confirm all ViewModels are defined in service files, not scattered across components.

---

## Hook Catalog

### Hook Architecture Overview

Hooks are the **state management layer** between services and components. They wrap TanStack Query for caching, loading states, and mutations.

**The Pattern:**
```
Component
    ↓ calls
  Hook (useRoomMessages, useRoomRuntime, etc.)
    ↓ uses
  Service (RoomService.getMessages, etc.)
    ↓ calls
  SDK (sdk.gen.ts auto-generated client)
    ↓
  Backend API
```

**Key Principles:**
- Hooks handle loading/error states—components don't call services directly
- Hooks handle cache invalidation—mutations trigger refetches automatically
- Hooks expose mutation functions with optimistic updates where appropriate

**Verify:** Open any component using room data. Confirm it imports from `@/hooks/`, not from `@/services/` or `@/client/`.

---

### useRoomMessages

**Location:** `frontend/src/hooks/useRoomMessages.ts`

**Purpose:** Fetch, paginate, send, and manage messages in a room.

**Input Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `roomId` | string | Required room UUID |
| `options.includeInternalMessages` | boolean | Show A2A messages (debug) |
| `options.enabled` | boolean | Conditionally enable query |

**Returns — Data:**
| Field | Type | Notes |
|-------|------|-------|
| `messages` | MessageViewModel[] | Transformed, sorted by time |
| `isLoading` | boolean | Initial load |
| `error` | Error \| null | Query error |
| `hasMore` | boolean | More pages available |

**Returns — Pagination:**
| Field | Type | Notes |
|-------|------|-------|
| `loadMore` | () => Promise | Fetch next page |
| `isLoadingMore` | boolean | Pagination in progress |

**Returns — Mutations:**
| Field | Type | Notes |
|-------|------|-------|
| `sendMessage` | (content: string) => Promise | Create message |
| `isSending` | boolean | Send in progress |
| `editMessage` | (messageId, content) => Promise | Update content |
| `isEditing` | boolean | Edit in progress |
| `deleteMessage` | (messageId) => Promise | Soft delete |
| `isDeleting` | boolean | Delete in progress |
| `pinMessage` | (messageId) => Promise | Mark important |
| `unpinMessage` | (messageId) => Promise | Unmark |
| `isPinning` / `isUnpinning` | boolean | Pin ops in progress |
| `toggleContext` | (messageId, active) => Promise | Set `active_for_context` |
| `isTogglingContext` | boolean | Toggle in progress |

**Query Key:** `["rooms", roomId, "messages", variant]` where variant is `"default"` or `"with-internal"`

**When to Use:** Any component that displays or manipulates room messages.

**Verify:** In `frontend/src/hooks/useRoomMessages.ts`, find the `queryKey` definition and confirm the structure matches.

---

### useRoomRuntime

**Location:** `frontend/src/hooks/useRoomRuntime.ts`

**Purpose:** Manage story runtime state—fetch current position, advance, rewind, reset.

**Input Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `roomId` | string | Required room UUID |
| `options.enabled` | boolean | Conditionally enable query |

**Returns — Data:**
| Field | Type | Notes |
|-------|------|-------|
| `runtime` | RoomRuntimeViewModel \| null | Current state (null if no runtime) |
| `isLoading` | boolean | Initial load |
| `error` | ApiError \| null | Query error |
| `refetch` | () => Promise | Manual refresh |

**Returns — Mutations:**
| Field | Type | Notes |
|-------|------|-------|
| `start` | (params) => Promise | Initialize runtime with persona |
| `advance` | (choiceId) => Promise | Make a choice, move forward |
| `rewind` | (targetChoiceId) => Promise | Undo to specific choice |
| `reset` | () => Promise | Return to start node |

**Returns — UI Flags:**
| Field | Type | Notes |
|-------|------|-------|
| `isStarting` | boolean | Start in progress |
| `isAdvancing` | boolean | Advance in progress |
| `isRewinding` | boolean | Rewind in progress |
| `isResetting` | boolean | Reset in progress |
| `pendingChoiceId` | string \| null | Optimistic UI feedback |

**Query Key:** `["rooms", roomId, "runtime"]`

**Error Handling:**
| Status | Behavior |
|--------|----------|
| 404/410 | Returns `null` runtime (no error) |
| 403 | Toast + refetch (permission denied) |
| 409 | Silent refetch (revision conflict) |
| 422 | Toast + refetch (invalid choice) |

**Key Insight:** All mutations pass `expected_revision` from current runtime. On 409 conflict, the hook auto-refetches to get the new revision.

**When to Use:** Any component displaying or controlling story navigation.

**Verify:** Make a choice in two browser tabs simultaneously. Confirm one succeeds and the other refetches without error toast.

---

### useRoomStream

**Location:** `frontend/src/hooks/useRoomStream.ts`

**Purpose:** Real-time WebSocket connection for room events and agent token streaming.

**Input Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `roomId` | string | Required room UUID |
| `options.enabled` | boolean | Conditionally connect |

**Returns:**
| Field | Type | Notes |
|-------|------|-------|
| `isConnected` | boolean | WebSocket connected |
| `sendMessage` | (content) => void | Send via WebSocket |
| `streamingMessage` | { agent_name, content } \| null | Current streaming response |
| `lastSequence` | number | For replay on reconnect |

**WebSocket Events Handled:**
| Event Type | Action |
|------------|--------|
| `room_message.user` | Optimistic add to message cache |
| `room_message.agent` | Invalidate messages query |
| `room_message.agent_internal` | Invalidate if showing internals |
| `message.delta` | Buffer tokens, update `streamingMessage` |
| `participant.*` | Invalidate participants query |
| `room.runtime.*` | Invalidate runtime query |
| `message.edited/pinned/unpinned/deleted` | Invalidate messages query |

**Token Buffering:** Tokens are buffered and flushed to UI every 50ms to prevent render thrashing.

**When to Use:** Any component needing real-time updates. Typically used once at page level, not in child components.

**Verify:** Open Network tab → WS. Send a message and watch for `message.delta` frames during agent response.

---

### useRoom

**Location:** `frontend/src/hooks/useRoom.ts`

**Purpose:** Aggregate hook that combines room metadata, participants, and messages into a single interface. Convenience wrapper for common room page patterns.

**Input Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `roomId` | string | Required room UUID |
| `options.includeInternalMessages` | boolean | Pass to useRoomMessages |
| `options.enabled` | boolean | Conditionally enable all queries |

**Returns — Data:**
| Field | Type | Notes |
|-------|------|-------|
| `room` | RoomViewModel \| undefined | Room metadata |
| `participants` | ParticipantViewModel[] | All participants |
| `messages` | MessageViewModel[] | From useRoomMessages |
| `isLoading` | boolean | Any query loading |
| `error` | Error \| null | First error encountered |

**Returns — Derived State:**
| Field | Type | Notes |
|-------|------|-------|
| `currentUserRole` | `"owner"` \| `"member"` \| null | Current user's role |
| `activeAgents` | ParticipantViewModel[] | Filtered agent participants |
| `activeUsers` | ParticipantViewModel[] | Filtered user participants |

**Returns — Operations:**
Delegates all message operations from `useRoomMessages`: `sendMessage`, `editMessage`, `deleteMessage`, `pinMessage`, `unpinMessage`, `toggleContext`, `loadMore`, plus their loading flags.

**When to Use:** Full room pages that need everything. For partial needs, prefer individual hooks to reduce unnecessary queries.

**Verify:** Compare the return type of `useRoom` with the combined returns of `useRoomMessages` + individual room/participant queries. Confirm it's a superset.

---

### useAgentUI

**Location:** `frontend/src/hooks/useAgentUI.ts`

**Purpose:** Extract and aggregate AG-UI components from all agent messages in a room.

**Input Parameters:**
| Parameter | Type | Notes |
|-----------|------|-------|
| `messages` | MessageViewModel[] | Message array (usually from useRoomMessages) |

**Returns:**
| Field | Type | Notes |
|-------|------|-------|
| `entries` | AgentUIEntry[] | Chronological list of UI components with metadata |
| `byAgent` | Map<string, AgentUIEntry[]> | Grouped by agent name |
| `hasComponents` | boolean | Quick check for any AG-UI content |
| `count` | number | Total component count |

**AgentUIEntry Shape:**
```typescript
interface AgentUIEntry {
  messageId: string
  agentName: string
  component: UIComponent
  createdAt: Date
}
```

**When to Use:** A2UI panels, AG-UI aggregation views, or any component that needs to display all agent-generated UI in one place.

**Key Insight:** This hook doesn't fetch—it transforms. Pass it the messages array from `useRoomMessages`.

**Verify:** In `frontend/src/hooks/useAgentUI.ts`, confirm it filters for messages where `ui_components` is non-null and non-empty.

---

### Hook Selection Guide

| Scenario | Recommended Hook(s) |
|----------|---------------------|
| Full room page with chat | `useRoom` + `useRoomStream` |
| Story-enabled room | Add `useRoomRuntime` |
| Chat-only component | `useRoomMessages` + `useRoomStream` |
| Story panel only | `useRoomRuntime` |
| AG-UI aggregation panel | `useRoomMessages` → `useAgentUI` |
| Real-time connection status | `useRoomStream` (for `isConnected`) |
| Message management (edit/pin/delete) | `useRoomMessages` mutations |

**Verify:** For any new component, check this table before creating a new hook. The hook you need likely exists.

---

### Query Key Reference

All query keys follow a hierarchical pattern for predictable invalidation:

```typescript
["rooms"]                              // All rooms list
["rooms", roomId]                      // Single room metadata
["rooms", roomId, "messages", variant] // Messages (variant: "default" | "with-internal")
["rooms", roomId, "participants"]      // Participants list
["rooms", roomId, "runtime"]           // Story runtime state
["stories"]                            // All stories
["stories", storyId]                   // Single story
["agents"]                             // All agents
["agents", agentId]                    // Single agent
```

**Invalidation Pattern:** Invalidating `["rooms", roomId]` does NOT cascade to messages/participants. Invalidate specific keys or use `queryClient.invalidateQueries({ queryKey: ["rooms", roomId], exact: false })` for subtree invalidation.

**Verify:** In any mutation's `onSuccess`, trace which query keys are invalidated. Confirm they match this hierarchy.

---

## Real-time Event Types

### WebSocket Architecture

The system uses WebSocket for real-time updates. Each room has its own connection, and events flow from backend → frontend to trigger cache invalidations and UI updates.

**Connection URL:** `ws://[api-base]/api/v1/ws/rooms/{roomId}?token={jwt}`

**Reconnection:** On disconnect, the client reconnects with `last_sequence` parameter. The backend replays missed events, preventing message loss.

```
Backend Event Emission
        ↓
   Redis Pub/Sub
        ↓
WebSocket Manager (broadcasts to connected clients)
        ↓
   useRoomStream (receives, dispatches)
        ↓
Query Invalidation OR Optimistic UI Update
```

**Verify:** Disconnect your network briefly, then reconnect. Check that missed messages appear without manual refresh.

---

### WebSocket Message Envelope

All WebSocket messages follow one of these shapes:

```typescript
// Room event (most common)
{
  type: "event"
  sequence: number           // Monotonic, for replay
  event_type: string         // e.g., "room_message.agent"
  payload: Record<string, any>
  created_at: string         // ISO timestamp
}

// Token streaming
{
  type: "message.delta"
  agent_name: string
  content: string            // Incremental token(s)
}

// Session lifecycle
{
  type: "session.created"
  room_id: string
}

// Errors/warnings
{
  type: "error" | "warning"
  message: string
}
```

**Verify:** Open browser DevTools → Network → WS tab. Filter to the room WebSocket and inspect message frames.

---

### Event Type Taxonomy

#### Message Events

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `room_message.user` | User sends message | Full message object | Optimistic add to cache |
| `room_message.agent` | Agent completes response | Full message object | Invalidate messages query |
| `room_message.agent_internal` | A2A message sent | Full message object | Invalidate if `includeInternalMessages` |

**Key Insight:** User messages are added optimistically (instant UI), agent messages invalidate (fetch fresh with full metadata).

**Verify:** Send a message and watch the WebSocket. Confirm `room_message.user` arrives before the REST response completes.

---

#### Streaming Events

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `message.delta` | Agent generates token | `{ agent_name, content }` | Buffer → update `streamingMessage` |

**Buffering Strategy:**
- Tokens accumulate in a buffer
- UI updates every 50ms (throttled)
- When `room_message.agent` arrives, streaming clears and final message displays

**Why Buffer?** Prevents render thrashing. A fast model can emit 100+ tokens/second—updating on every token would freeze the UI.

**Verify:** During agent response, log `streamingMessage` updates. Confirm they batch multiple tokens, not one per frame.

---

#### Message Management Events (Phase 5)

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `message.edited` | Message content updated | `{ message_id, content, edited_at, edited_by }` | Invalidate messages |
| `message.pinned` | Message pinned | `{ message_id, pinned_at, pinned_by }` | Invalidate messages |
| `message.unpinned` | Message unpinned | `{ message_id }` | Invalidate messages |
| `message.context_toggled` | Context flag changed | `{ message_id, active_for_context }` | Invalidate messages |
| `message.deleted` | Message soft deleted | `{ message_id }` | Invalidate messages |

**Key Insight:** All management events invalidate rather than patch. This keeps the cache consistent with server state, especially for permission flags that may change.

**Verify:** Pin a message in one tab. Confirm the other tab updates without manual refresh.

---

#### Participant Events

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `participant.joined` | User/agent joins room | Participant object | Invalidate participants |
| `participant.left` | User/agent leaves room | `{ participant_id }` | Invalidate participants |
| `participant.updated` | Role or status change | Participant object | Invalidate participants |

**Verify:** Add an agent to a room via API. Confirm the participant list updates in real-time.

---

#### Runtime Events

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `room.runtime.started` | Runtime initialized | Runtime state | Invalidate runtime |
| `room.runtime.advanced` | Choice made | `{ choice_id, new_node_id, revision }` | Invalidate runtime |
| `room.runtime.rewound` | Undo performed | `{ target_choice_id, revision }` | Invalidate runtime |
| `room.runtime.reset` | Reset to start | `{ revision }` | Invalidate runtime |

**Key Insight:** Runtime events include the new `revision`. This enables other clients to detect their local revision is stale.

**Verify:** Make a story choice in one tab. Confirm the other tab's story panel updates automatically.

---

### Event Sequence & Replay

**Sequence Numbers:**
- Every `type: "event"` message has a monotonic `sequence` number
- On reconnect, client sends `last_sequence` in handshake
- Server replays all events with `sequence > last_sequence`

**Why This Matters:**
- No lost messages during network hiccups
- Client can be offline briefly and catch up
- Server doesn't need to track per-client state long-term

```typescript
// Reconnection handshake
ws://api/v1/ws/rooms/{roomId}?token={jwt}&last_sequence=42
// Server replays events 43, 44, 45... to present
```

**Verify:** In `useRoomStream`, find where `lastSequence` is tracked and passed on reconnection.

---

### Event Flow Diagram

```
User clicks "Send"
       ↓
useRoomMessages.sendMessage()  ←──── Optimistic cache update
       ↓
POST /rooms/{id}/messages
       ↓
Backend persists + emits event
       ↓
┌──────────────────────────────────────┐
│  room_message.user (WebSocket)       │ → Other clients see message
└──────────────────────────────────────┘
       ↓
Agent runner triggered
       ↓
┌──────────────────────────────────────┐
│  message.delta (streaming)           │ → streamingMessage updates
│  message.delta                       │
│  message.delta                       │
└──────────────────────────────────────┘
       ↓
Agent completes
       ↓
┌──────────────────────────────────────┐
│  room_message.agent (WebSocket)      │ → Invalidate, fetch final message
└──────────────────────────────────────┘
```

**Verify:** Trace a full message send → agent response cycle in the Network tab. Confirm this event sequence.

---

## AG-UI Component Types

### What is AG-UI?

AG-UI (Agent-Generated UI) is the system that allows agents to emit structured UI components in their responses. Instead of plain text, agents can return cards, tables, buttons, code blocks, and more.

**Architecture:**
```
Agent Response (contains ui_components array)
        ↓
MessageViewModel.ui_components
        ↓
AgentUIRenderer (dispatch by type)
        ↓
Primitive Component (UICardBlock, UITableBlock, etc.)
```

**Key Locations:**
| File | Purpose |
|------|---------|
| `frontend/src/components/AgentUI/types.ts` | Type definitions for all components |
| `frontend/src/components/AgentUI/AgentUIRenderer.tsx` | Dispatcher that routes to primitives |
| `frontend/src/components/AgentUI/primitives/` | Individual component implementations |

**Verify:** In `frontend/src/components/AgentUI/types.ts`, find `UIComponentType` and confirm it lists all supported types.

---

### UIComponent Base Shape

All AG-UI components share this envelope:

```typescript
interface UIComponent {
  type: UIComponentType        // Discriminator
  data: Record<string, unknown> // Type-specific payload
  id?: string                  // Optional unique identifier
  fallback_text?: string       // Plain text for non-UI contexts
}

type UIComponentType =
  | "card" | "list" | "table" | "progress"
  | "action_buttons" | "code" | "quote" | "alert"
  | "collapsible" | "tabs" | "divider" | "page_layout_preview"
```

**Verify:** Grep for `UIComponentType` in `frontend/src/components/AgentUI/types.ts` to see the complete union.

---

### Primitive Reference

#### card

**Location:** `frontend/src/components/AgentUI/primitives/UICardBlock.tsx`

**Purpose:** Contained content block with optional title, subtitle, body, and footer.

```typescript
interface UICardData {
  title?: string
  subtitle?: string
  body?: string               // Markdown supported
  footer?: string
  variant?: "default" | "highlight" | "warning" | "success" | "info"
}
```

**Use Cases:** Feature summaries, status displays, highlighted information.

**Verify:** Search codebase for `type: "card"` in test data or agent prompts to see usage examples.

---

#### list

**Location:** `frontend/src/components/AgentUI/primitives/UIListBlock.tsx`

**Purpose:** Bulleted or structured list with optional icons and badges.

```typescript
interface UIListData {
  items: Array<{
    label: string
    description?: string
    icon?: string             // Lucide icon name
    badge?: string            // Small tag/label
  }>
  ordered?: boolean           // Numbered vs bulleted
}
```

**Use Cases:** Feature lists, step sequences, option menus.

**Verify:** In `frontend/src/components/AgentUI/primitives/UIListBlock.tsx`, confirm icon rendering uses Lucide.

---

#### table

**Location:** `frontend/src/components/AgentUI/primitives/UITableBlock.tsx`

**Purpose:** Structured data display with columns and rows.

```typescript
interface UITableData {
  columns: Array<{
    key: string               // Field accessor
    header: string            // Display header
    align?: "left" | "center" | "right"
  }>
  rows: Array<Record<string, unknown>>  // Data rows
}
```

**Use Cases:** Data comparisons, search results, structured outputs.

**Verify:** Render a table component and inspect that column alignment applies correctly.

---

#### progress

**Location:** `frontend/src/components/AgentUI/primitives/UIProgressBlock.tsx`

**Purpose:** One or more progress bars with labels.

```typescript
interface UIProgressData {
  items: Array<{
    label: string
    value: number             // 0-100
    max?: number              // Default 100
    color?: string            // CSS color or Tailwind class
  }>
}
```

**Use Cases:** Task completion, multi-step workflows, capacity indicators.

**Verify:** In `frontend/src/components/AgentUI/primitives/UIProgressBlock.tsx`, confirm value is clamped between 0 and max.

---

#### action_buttons

**Location:** `frontend/src/components/AgentUI/primitives/UIActionButtons.tsx`

**Purpose:** Interactive button group that triggers actions via callback.

```typescript
interface UIActionButtonsData {
  buttons: Array<{
    label: string
    action: string            // Action identifier passed to callback
    variant?: "default" | "primary" | "secondary" | "destructive" | "outline"
    icon?: string             // Lucide icon name
    disabled?: boolean
  }>
  layout?: "horizontal" | "vertical"
}
```

**Action Flow:**
```
User clicks button
       ↓
onAction(action, componentId) callback
       ↓
RoomService.sendUIAction(roomId, action, sourceMessageId, componentId)
       ↓
Backend handles action → may trigger agent response
```

**Use Cases:** Confirmations, navigation choices, workflow triggers.

**Key Insight:** This is the primary way users interact with AG-UI beyond reading. The `action` string is opaque to the frontend—the backend interprets it.

**Verify:** In `frontend/src/components/AgentUI/primitives/UIActionButtons.tsx`, trace the `onAction` prop to understand the callback signature.

---

#### code

**Location:** `frontend/src/components/AgentUI/primitives/UICodeBlock.tsx`

**Purpose:** Syntax-highlighted code display.

```typescript
interface UICodeData {
  code: string
  language?: string           // Highlight.js language identifier
  title?: string              // Optional filename/label
  line_numbers?: boolean      // Show line numbers
}
```

**Use Cases:** Code snippets, configuration examples, API responses.

**Verify:** Render a code block with `language: "typescript"` and confirm syntax highlighting applies.

---

#### quote

**Location:** `frontend/src/components/AgentUI/primitives/UIQuoteBlock.tsx`

**Purpose:** Blockquote with optional attribution.

```typescript
interface UIQuoteData {
  text: string
  attribution?: string        // Source/author
  variant?: "default" | "highlight"
}
```

**Use Cases:** Citations, testimonials, emphasized excerpts.

**Verify:** In `frontend/src/components/AgentUI/primitives/UIQuoteBlock.tsx`, confirm attribution renders below the quote text.

---

#### alert

**Location:** `frontend/src/components/AgentUI/primitives/UIAlertBlock.tsx`

**Purpose:** Attention-grabbing message with semantic variant.

```typescript
interface UIAlertData {
  title?: string
  message: string
  variant: "info" | "success" | "warning" | "error"
}
```

**Use Cases:** Warnings, confirmations, error displays, important notices.

**Verify:** Render each variant and confirm icon and color styling differ appropriately.

---

#### collapsible

**Location:** `frontend/src/components/AgentUI/primitives/UICollapsibleBlock.tsx`

**Purpose:** Expandable section with toggle.

```typescript
interface UICollapsibleData {
  title: string
  content: string             // Markdown supported
  default_open?: boolean
  icon?: string               // Lucide icon name
}
```

**Use Cases:** Details on demand, FAQ items, optional context.

**Verify:** In `frontend/src/components/AgentUI/primitives/UICollapsibleBlock.tsx`, confirm `default_open` controls initial state.

---

#### tabs

**Location:** `frontend/src/components/AgentUI/primitives/UITabsBlock.tsx`

**Purpose:** Tabbed content container.

```typescript
interface UITabsData {
  tabs: Array<{
    label: string
    content: string           // Markdown supported
    icon?: string             // Lucide icon name
  }>
  default_tab?: number        // Index of initially active tab
}
```

**Use Cases:** Multi-view content, alternative options, categorized information.

**Verify:** Render tabs and confirm keyboard navigation (arrow keys) works between tabs.

---

#### divider

**Location:** `frontend/src/components/AgentUI/primitives/UIDividerBlock.tsx`

**Purpose:** Visual separator with optional label.

```typescript
interface UIDividerData {
  label?: string
  variant?: "default" | "subtle" | "strong"
}
```

**Use Cases:** Section breaks, logical grouping.

**Verify:** Render divider with and without label. Confirm label centers on the line.

---

#### page_layout_preview

**Location:** `frontend/src/components/AgentUI/primitives/UIPageLayoutPreview.tsx`

**Purpose:** Preview of a page template or layout structure.

```typescript
interface UIPageLayoutPreviewData {
  entity_type: string
  entity_id: string
  layout_json: Record<string, unknown>
}
```

**Use Cases:** Template previews, layout selection, design proofs.

**Verify:** This is a specialized component—check if it's used in story or page editor contexts.

---

### AG-UI Rendering Pipeline

**Location:** `frontend/src/components/AgentUI/AgentUIRenderer.tsx`

```typescript
interface AgentUIRendererProps {
  component: UIComponent
  onAction?: (action: string, componentId?: string) => void
}
```

**Dispatch Logic:**
```typescript
switch (component.type) {
  case "card": return <UICardBlock data={component.data} />
  case "action_buttons": return <UIActionButtons data={component.data} onAction={onAction} />
  // ... etc
}
```

**Key Insight:** Only `action_buttons` receives the `onAction` callback. Other primitives are display-only.

**Verify:** In `frontend/src/components/AgentUI/AgentUIRenderer.tsx`, confirm the switch statement covers all `UIComponentType` values.

---

### AG-UI Component Summary Table

| Type | Location | Interactive | Markdown Support |
|------|----------|-------------|------------------|
| `card` | primitives/UICardBlock.tsx | No | body field |
| `list` | primitives/UIListBlock.tsx | No | description field |
| `table` | primitives/UITableBlock.tsx | No | No |
| `progress` | primitives/UIProgressBlock.tsx | No | No |
| `action_buttons` | primitives/UIActionButtons.tsx | **Yes** | No |
| `code` | primitives/UICodeBlock.tsx | No (copy button) | No |
| `quote` | primitives/UIQuoteBlock.tsx | No | No |
| `alert` | primitives/UIAlertBlock.tsx | No | No |
| `collapsible` | primitives/UICollapsibleBlock.tsx | Toggle | content field |
| `tabs` | primitives/UITabsBlock.tsx | Tab switch | content field |
| `divider` | primitives/UIDividerBlock.tsx | No | No |
| `page_layout_preview` | primitives/UIPageLayoutPreview.tsx | No | No |

**Verify:** Run `ls frontend/src/components/AgentUI/primitives/` and confirm all files are documented above.

---

## Extension Points

### Overview

This section documents **where to add new things** and **where not to modify**. Following these patterns ensures consistency and prevents architectural violations.

**The Golden Rules:**
1. **Extend in designated locations** — Don't scatter new code randomly
2. **Never modify auto-generated code** — `src/client/` is sacred
3. **Never modify shadcn primitives directly** — Use the CLI for `src/components/ui/`
4. **New hooks require approval** — Justify before creating

---

### Adding a New ViewModel

**When:** You have a new API type that components need to consume.

**Where:** Add to the appropriate service file in `frontend/src/services/`

**Pattern:**
```typescript
// 1. Define the ViewModel interface
export interface NewEntityViewModel {
  id: string
  displayName: string  // Transformed from API's name field
  createdAt: Date      // Parsed from string
  // ... computed/derived fields
}

// 2. Create transformation function
export function transformNewEntity(
  apiEntity: NewEntityPublic,
  context?: { currentUserId?: string }
): NewEntityViewModel {
  return {
    id: apiEntity.id,
    displayName: apiEntity.name ?? "Unknown",
    createdAt: new Date(apiEntity.created_at),
  }
}

// 3. Add service methods that use the transformation
export const NewEntityService = {
  async getAll(): Promise<NewEntityViewModel[]> {
    const response = await sdk.getNewEntities()
    return response.data?.map(transformNewEntity) ?? []
  },
}
```

**Checklist:**
- [ ] ViewModel interface defined with JSDoc
- [ ] Transformation function handles null/undefined gracefully
- [ ] Service methods return ViewModels, not raw API types
- [ ] No `any` types

**Verify:** After adding, grep for the raw API type in components. It should only appear in the service file.

---

### Adding a New Hook

**When:** You need reusable stateful logic that multiple components will share.

**⚠️ Requires Approval:** New hooks require explicit authorization. Before creating, ask:
1. Does an existing hook already cover this? (Check Hook Catalog)
2. Can this be a service method instead?
3. Is this truly reusable, or is it component-specific logic?

**Where:** `frontend/src/hooks/`

**Pattern:**
```typescript
/**
 * useNewFeature Hook
 *
 * Brief description of purpose
 * - Key capability 1
 * - Key capability 2
 *
 * @param entityId - The entity to operate on
 * @param options - Configuration options
 */
export function useNewFeature(
  entityId: string,
  options: UseNewFeatureOptions = {}
) {
  const { enabled = true } = options

  // Query for data
  const query = useQuery({
    queryKey: ["new-feature", entityId],
    queryFn: () => NewFeatureService.get(entityId),
    enabled,
  })

  // Mutations
  const mutation = useMutation({
    mutationFn: NewFeatureService.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["new-feature", entityId] })
    },
  })

  return {
    // Data
    data: query.data,
    isLoading: query.isLoading,
    error: query.error,

    // Mutations
    update: mutation.mutateAsync,
    isUpdating: mutation.isPending,
  }
}
```

**Checklist:**
- [ ] Approval obtained and documented
- [ ] JSDoc header with description and params
- [ ] Query key follows hierarchy pattern
- [ ] Loading/error states exposed
- [ ] Mutations handle cache invalidation
- [ ] No direct API calls (use services)

**Verify:** New hook must be added to Hook Catalog in this ontology document.

---

### Adding a New AG-UI Primitive

**When:** Agents need to emit a new type of structured UI.

**Where:**
1. Type definition: `frontend/src/components/AgentUI/types.ts`
2. Primitive component: `frontend/src/components/AgentUI/primitives/`
3. Renderer dispatch: `frontend/src/components/AgentUI/AgentUIRenderer.tsx`

**Step 1 — Add Type:**
```typescript
// In types.ts

// Add to union
type UIComponentType =
  | "card" | "list" | /* existing... */ | "new_primitive"

// Define data shape
export interface UINewPrimitiveData {
  requiredField: string
  optionalField?: number
}
```

**Step 2 — Create Primitive:**
```typescript
// In primitives/UINewPrimitiveBlock.tsx

import type { UINewPrimitiveData } from "../types"

interface UINewPrimitiveBlockProps {
  data: UINewPrimitiveData
  onAction?: (action: string, componentId?: string) => void  // If interactive
}

/**
 * UINewPrimitiveBlock
 *
 * Description of what this primitive displays
 * - Feature 1
 * - Feature 2
 */
export function UINewPrimitiveBlock({ data, onAction }: UINewPrimitiveBlockProps) {
  return (
    <div className="...">
      {/* Implementation */}
    </div>
  )
}
```

**Step 3 — Add to Renderer:**
```typescript
// In AgentUIRenderer.tsx

import { UINewPrimitiveBlock } from "./primitives/UINewPrimitiveBlock"

// In switch statement:
case "new_primitive":
  return <UINewPrimitiveBlock data={component.data as UINewPrimitiveData} onAction={onAction} />
```

**Checklist:**
- [ ] Type added to `UIComponentType` union
- [ ] Data interface defined with JSDoc
- [ ] Primitive component created with JSDoc header
- [ ] Renderer dispatch case added
- [ ] Added to AG-UI Component Summary Table in this ontology

**Verify:** Create a test message with the new component type. Confirm it renders without errors.

---

### Adding a New Demo

**When:** You have a new demo scenario to showcase.

**Where:**
1. Seed script: `backend/app/test_scripts/story_things/`
2. Config registration: `frontend/src/config/demos.ts`

**Step 1 — Create Seed Script:**
Follow the pattern in `docs/demos/demo-engineering-reference.md`. Key points:
- Use API calls, not direct DB access
- Return all generated IDs as JSON
- Support `--json` flag for scripting

**Step 2 — Register Config:**
```typescript
// In config/demos.ts

export const DEMOS: Record<string, DemoConfig> = {
  // ... existing demos

  "your-demo-slug": {
    slug: "your-demo-slug",
    title: "Your Demo Title",
    description: "One-line description of what this demonstrates.",
    roomId: "<room_id from seed output>",  // Run seed first!
    autoRespond: true,
    theme: "default",  // Optional theme
  },
}
```

**Checklist:**
- [ ] Seed script follows API-based pattern
- [ ] Seed script returns room_id in output
- [ ] Config registered with correct room_id
- [ ] Demo accessible at `/demo/your-demo-slug`

**Verify:** Run seed, copy room_id to config, navigate to demo URL. Confirm it loads without "not found" error.

---

### Adding a New Service Method

**When:** You need to call a new API endpoint or encapsulate a data operation.

**Where:** Appropriate service file in `frontend/src/services/`

**Pattern:**
```typescript
// In existing service file (e.g., roomService.ts)

export const RoomService = {
  // ... existing methods

  /**
   * Brief description of what this does
   *
   * @param roomId - The room to operate on
   * @param data - The payload
   * @returns Description of return value
   */
  async newOperation(roomId: string, data: NewOperationInput): Promise<NewOperationViewModel> {
    const response = await sdk.newOperation({
      path: { room_id: roomId },
      body: data,
    })

    if (response.error) {
      throw response.error
    }

    return transformNewOperation(response.data!)
  },
}
```

**Checklist:**
- [ ] Method has JSDoc documentation
- [ ] Returns ViewModel (transformed), not raw API type
- [ ] Handles error response appropriately
- [ ] Uses SDK client, not fetch/axios directly

**Verify:** Service method should be the only place that imports from `@/client/sdk.gen` for this operation.

---

### Adding a New Room Panel

**When:** You need a new panel type in the room layout system.

**Where:** `frontend/src/components/Room/panels/`

**Pattern:**
```typescript
// In panels/NewFeaturePanel.tsx

import { useRoomMessages } from "@/hooks/useRoomMessages"
// ... other imports

interface NewFeaturePanelProps {
  roomId: string
  // ... other props
}

/**
 * NewFeaturePanel
 *
 * Description of panel purpose
 * - Feature 1
 * - Feature 2
 */
export function NewFeaturePanel({ roomId }: NewFeaturePanelProps) {
  const { messages } = useRoomMessages(roomId)

  return (
    <div className="flex flex-col h-full">
      {/* Panel content */}
    </div>
  )
}
```

**Integration:** Panels are used within `ResizablePanelGroup` layouts. See `frontend/src/components/Demo/DemoPage.tsx` for integration pattern.

**Checklist:**
- [ ] Component has JSDoc header
- [ ] Uses hooks for data (not direct service calls in component)
- [ ] Follows `h-full` flex pattern for proper sizing
- [ ] Under 300 lines (or includes justification comment)

**Verify:** Integrate panel into a test layout. Confirm it respects resize handles and doesn't break overflow.

---

### Protected Locations (DO NOT MODIFY)

| Location | Reason | How to Change |
|----------|--------|---------------|
| `frontend/src/client/` | Auto-generated from OpenAPI | Run `npm run generate-client` after backend changes |
| `frontend/src/components/ui/` | shadcn primitives | Use shadcn CLI: `npx shadcn@latest add <component>` |

**Verify:** Run `git diff frontend/src/client/` before committing. If you see manual changes, revert them.

---

### Extension Point Summary

| I want to... | Location | Approval Required? |
|--------------|----------|-------------------|
| Add a ViewModel | `services/*.ts` | No |
| Add a hook | `hooks/*.ts` | **Yes** |
| Add AG-UI primitive | `components/AgentUI/` | No |
| Add a demo | `config/demos.ts` + seed script | No |
| Add a service method | `services/*.ts` | No |
| Add a room panel | `components/Room/panels/` | No |
| Modify API client | — | **Never** (regenerate instead) |
| Modify shadcn component | — | **Never** (use CLI) |

**Verify:** Before starting any extension, check this table to confirm you're in the right location.

---

## Addendum A: Open Questions — Context Manipulation Demos

> These questions must be answered before writing Guide A. Check off questions as they are resolved and add answers to the ontology.

### A.1 Data Model Questions

- [ ] What field controls whether a message is included in agent context?
- [ ] What field marks a message as important/pinned?
- [ ] Does pinning automatically include a message in context?
- [ ] What permissions are required to toggle context?
- [ ] What permissions are required to edit/delete messages?

### A.2 API & Hook Questions

- [ ] What hook provides context toggle functionality?
- [ ] What's the loading state for context toggle?
- [ ] How does the UI know which messages are in context?
- [ ] What event fires when context is toggled?
- [ ] What's the event payload shape for context toggle?

### A.3 Backend/Agent Context Questions

- [ ] How does the backend filter messages for agent context?
- [ ] Is there a maximum context window size?
- [ ] Are messages filtered by `active_for_context` before being sent to LLM?
- [ ] Can we "re-run" a conversation from a specific message?
- [ ] What happens to agent responses when context changes mid-conversation?

### A.4 UI/UX Questions

- [ ] Where is the context toggle UI located?
- [ ] How do we visualize which messages are in/out of context?
- [ ] Can we bulk-select messages for context manipulation?
- [ ] Is there a "context preview" showing what the agent sees?

### A.5 Demo-Specific Questions

- [ ] What's the demo use case for "re-run from checkpoint"?
- [ ] How do we create a "checkpoint" in a conversation?
- [ ] Can we fork a conversation into parallel branches?
- [ ] How do we compare agent outputs before/after context changes?

---

## Addendum B: Open Questions — Story Runtime Navigation Demos

> These questions must be answered before writing Guide B. Check off questions as they are resolved and add answers to the ontology.

### B.1 Data Model Questions

- [ ] What fields track story navigation history?
- [ ] How does the `revision` field work for optimistic concurrency?
- [ ] What is `head_choice_id` and how does it enable rewind?
- [ ] How is `node_chain` constructed and maintained?
- [ ] What's the relationship between `UserStoryProgress` and `RoomStoryProgress`?

### B.2 Rewind/Reset Mechanics Questions

- [ ] What's the difference between rewind and reset?
- [ ] Can we rewind to any arbitrary point, or only one step back?
- [ ] What happens to story_state when we rewind?
- [ ] Are rewound messages preserved or deleted?
- [ ] How does rewind affect agent context?

### B.3 Model Swapping Questions

- [ ] How do we change an agent's model mid-conversation?
- [ ] Is model swapping a runtime operation or does it require agent reconfiguration?
- [ ] Can we swap models for a single response without permanent change?
- [ ] What API endpoints support model configuration?
- [ ] How do we access the `provider` and `model_name` fields for an agent in a room?

### B.4 Comparison & A/B Testing Questions

- [ ] How do we run the same prompt through two different models?
- [ ] Can we create parallel conversation branches for comparison?
- [ ] Is there a diff/comparison UI pattern for agent outputs?
- [ ] How do we store and retrieve comparison results?
- [ ] Can we replay a conversation segment with a different model?

### B.5 UI/UX Questions

- [ ] How do we visualize the story path/node history?
- [ ] Where are rewind/reset controls located?
- [ ] How do we show "what-if" branching options?
- [ ] Is there a timeline or breadcrumb UI for story navigation?
- [ ] How do we indicate which model generated which response?

### B.6 Demo-Specific Questions

- [ ] What's the demo use case for "swap model and compare"?
- [ ] How do we set up a side-by-side comparison view?
- [ ] Can we automate regression testing across models?
- [ ] What metrics should we capture for model comparison?

---

## Addendum C: Open Questions — Hidden Orchestrator Demos

> These questions must be answered before writing Guide C. Check off questions as they are resolved and add answers to the ontology.

### C.1 Architecture Questions

- [ ] What is the "hidden orchestrator" pattern?
- [ ] How do orchestrators differ from regular agents?
- [ ] What's the relationship between orchestrators and subagents?
- [ ] How does A2A (agent-to-agent) messaging work?
- [ ] What's the message flow: user → orchestrator → subagent → AG-UI?

### C.2 A2A Messaging Questions

- [ ] What is `sender_type: "agent_internal"` and when is it used?
- [ ] How do agents send messages to other agents?
- [ ] Are A2A messages visible to users by default?
- [ ] How do we filter/show A2A messages for debugging?
- [ ] What events fire for A2A message exchange?

### C.3 Hidden Room/UI Questions

- [ ] How do we hide the chat panel and show only AG-UI?
- [ ] Can we create a "headless" room that only emits AG-UI?
- [ ] How do we hide the story panel while keeping runtime active?
- [ ] What layout configurations support AG-UI-only views?
- [ ] How do we prevent users from sending direct messages?

### C.4 AG-UI Navigation Questions

- [ ] How do action_buttons drive story/conversation navigation?
- [ ] Can AG-UI buttons trigger story choices (advance/rewind)?
- [ ] How do we map button actions to runtime operations?
- [ ] What's the action string format for navigation buttons?
- [ ] How does the backend interpret AG-UI action payloads?

### C.5 Orchestrator Coordination Questions

- [ ] How does an orchestrator decide which subagent to invoke?
- [ ] Can an orchestrator invoke multiple subagents in sequence?
- [ ] How do subagent responses flow back through the orchestrator?
- [ ] Is there a state machine pattern for orchestrator workflows?
- [ ] How do we handle orchestrator errors/timeouts?

### C.6 Demo-Specific Questions

- [ ] What's the demo use case for "wizard-style guided experience"?
- [ ] How do we design a progressive disclosure flow with AG-UI?
- [ ] Can we create branching wizard paths based on user choices?
- [ ] How do we track user progress through an orchestrated flow?
- [ ] What's the minimum viable hidden orchestrator demo?
