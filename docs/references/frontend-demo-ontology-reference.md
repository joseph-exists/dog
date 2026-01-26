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
- Guide D: The Massive Mystery

Each guide assumes familiarity with the ontology and will reference terms defined here without re-explaining them.

---

## Demo Synopses

### Demo A: Context Manipulation — "The Memory Surgeon"

Imagine giving users a scalpel for AI memory. Demo A transforms the opaque "context window" into something tangible and manipulable—a visual tapestry where every message glows with its inclusion state, where users can surgically remove a single exchange and watch the AI reconstruct its understanding in real-time. This isn't just about toggling flags; it's about revealing the profound truth that AI responses are shaped entirely by what they're allowed to remember. Users will checkpoint conversations like save points in a game, fork timelines to explore "what if I'd never mentioned the budget constraint?", and witness side-by-side how the same AI produces radically different solutions when its memory is sculpted differently. The demo exposes context as the invisible hand it truly is—and puts that hand under user control.

### Demo B: Story Runtime Navigation — "The Quantum Narrator"

What if you could rewind reality? Demo B gives users a time machine for narrative AI, letting them scrub backward through a branching story to any decision point and then—here's where it gets magical—swap the storyteller mid-scene. The same narrative moment, the same accumulated context, but suddenly rendered through a different model's voice and reasoning. Users will watch Claude become GPT-4 become Gemini, observing how each AI interprets the same story state with its own personality and capabilities. This is A/B testing elevated to art: not just comparing outputs, but experiencing the uncanny valley between AI minds. The story becomes a laboratory where users can isolate the variable of "which intelligence is speaking" while holding everything else constant. It's not just navigation—it's comparative consciousness exploration.

### Demo C: Hidden Orchestrator — "The Invisible Conductor"

The most powerful interfaces hide their complexity. Demo C strips away every visible trace of rooms, messages, and chat—leaving only crystalline AG-UI components floating in space, responding to user intent through elegant buttons and cards. Behind this serene surface, an invisible orchestrator coordinates a symphony of specialized subagents through A2A messaging, each contributing their expertise without ever appearing directly. Users experience a wizard-like guided journey, making choices through beautifully rendered UI components, never suspecting that their clicks are triggering cascades of agent-to-agent deliberation. This is the magic trick: the user sees a seamless, almost game-like interface while underneath, a distributed AI system collaborates in whispers. Demo C proves that the most sophisticated AI experiences are the ones where the AI disappears entirely into the experience.

### Demo D: The Loom of Infinite Stories — "Where Memory, Time, and Voice Converge"

---

**The Vision**

Demo D is not merely a combination—it is an *emergence*. When context manipulation, temporal navigation, and hidden orchestration interweave, something unprecedented becomes possible: an experience where users don't just consume AI-generated narrative, but become weavers of possibility itself.

Imagine entering what appears to be a simple, elegant interface—perhaps a glowing tapestry, perhaps a constellation map, perhaps something that defies easy metaphor. There are no chat windows. No visible messages. Only luminous threads representing story moments, model voices, and memory states, all rendered as interactive AG-UI elements that respond to touch and intention.

**The Core Experience**

The user begins a story. But this story isn't linear—it's a living probability space. An invisible orchestrator (C) guides them through narrative beats using only visual components: cards that reveal story moments, buttons that represent choices, progress indicators that show how deep into the tale they've ventured.

But here's where it transcends: at any point, the user can reach into the tapestry and *alter what the story remembers* (A). They can dim certain threads—make the AI "forget" that the protagonist found the key, or that the villain revealed their motivation. The orchestrator seamlessly reweaves the narrative around these holes, consulting subagents specialized in continuity, tension, and surprise.

And they can *change who tells the story* (B). Mid-scene, mid-breath, the user can summon a different narrative voice. The orchestrator doesn't just swap models—it coordinates between them, having Claude hand off to GPT-4 with a hidden A2A message that says "continue from here, but make it darker." The user sees only the seamless transition, the subtle shift in tone, as if the story itself learned a new way to speak.

**The Profound Interaction**

The true magic emerges from the intersection:

- **Memory + Time**: Rewind to a past moment, alter what was remembered, and branch into an entirely new timeline that the AI generates fresh, informed by the surgically modified context.

- **Time + Voice**: Navigate to any story node and experience that same moment told by three different AI voices, displayed side-by-side in elegant AG-UI cards, each interpretation highlighting how model architecture shapes narrative soul.

- **Voice + Memory**: Have one AI tell the story while another AI secretly curates what it remembers—a hidden subagent that dynamically manages context based on dramatic principles, ensuring the storyteller always has exactly the right memories to create maximum impact.

- **All Three Together**: The ultimate mode. An orchestrator coordinates multiple AIs in real-time, each with different memory states and model capabilities, weaving a story that no single AI could produce. One model excels at dialogue; give it only conversation context. Another excels at world-building; let it remember every environmental detail. A third masters emotional beats; grant it access to all character development. The orchestrator braids their outputs into a unified narrative, presented through AG-UI components that make the user feel like they're conducting an orchestra of imagination.

**The Interface Philosophy**

The user never sees the machinery. They see only the Loom: threads of light representing narrative possibilities, bright where memory is strong, dim where it's been suppressed, colored by the voice currently speaking. They interact by touching threads, by pulling them together or apart, by invoking different weavers to contribute their talents.

The AG-UI renders everything: choice points as glowing knots in the tapestry, model options as different colored threads to weave in, memory states as brightness and shadow. Action buttons don't say "toggle context" or "swap model"—they say "remember this moment" or "hear it differently" or "let another voice speak."

**Why It Matters**

Demo D proves that the constraints we accept in AI interaction are artificial. We act as if context is fixed, as if we must speak to one model at a time, as if the interface must be conversational. The Loom shatters these assumptions and reveals what becomes possible when we treat AI capabilities as composable primitives rather than monolithic products.

This is a demo that will make engineers *feel something*—not just understand a capability, but experience wonder at what becomes possible when the pieces we've built combine into something greater than their sum.

**The Challenge**

Building Demo D requires perfect coordination across every system in our architecture. It demands that context manipulation be instant and visual. That runtime navigation be smooth and unlimited. That orchestration be so reliable it becomes invisible. It requires AG-UI components we haven't imagined yet—ones that render probability spaces and memory states and multi-voice harmonies.

But that's exactly why we document. That's why we question. That's why we build the ontology before the implementation.

Because Demo D isn't just a demo. It's a proof that our architecture was designed for emergence.

---

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

**Multi-Agent Behavior:**
- **Message broadcasting:** When a message is sent to a room, ALL agents in the room receive it (tested with up to 100 agents).
- **A/B testing:** To compare models, add multiple agents with different `model_name`/`provider` values. Each responds independently.
- **Parallel branches:** The backend fully supports parallel conversation branches for comparison views.
- **Replay:** Any conversation segment can be replayed with a different model by swapping the AgentConfig and re-triggering.

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

### Message Management System

The message management system (Phase 5) provides fine-grained control over messages in rooms.

#### Message Management Fields

| Field | Type | Default | Notes |
|-------|------|---------|-------|
| `active_for_context` | boolean | `true` | Whether message is included in agent context |
| `is_pinned` | boolean | `false` | Whether message is marked as important |
| `pinned_at` | datetime \| null | null | When message was pinned |
| `pinned_by` | UUID \| null | null | Who pinned the message |
| `edited_at` | datetime \| null | null | When content was last edited |
| `edited_by` | UUID \| null | null | Who last edited the content |
| `can_edit` | boolean | computed | Backend-computed permission flag |
| `can_delete` | boolean | computed | Backend-computed permission flag |
| `can_pin` | boolean | computed | Backend-computed permission flag |

**Key Insight:** Permission flags (`can_edit`, `can_delete`, `can_pin`) are computed by the backend based on ownership, roles, and time windows. Never compute these client-side.

**Verify:** In `backend/app/models.py`, search for `class RoomMessage` and confirm these fields exist with their indexes.

---

#### Message Management Permissions

| Operation | Permission Level | Notes |
|-----------|-----------------|-------|
| **Toggle Context** | Any active participant | Everyone can control what agents see |
| **Pin/Unpin** | Room owner only | Pinning auto-sets `active_for_context=true` |
| **Edit** | Message author OR room owner | Time-limited for authors |
| **Delete** | Room owner only | Soft delete |

**Key Insight:** Pinning automatically sets `active_for_context=true`. Unpinning does NOT change `active_for_context`.

**Verify:** In `backend/app/api/routes/rooms.py`, find `pin_message_endpoint` and confirm the docstring mentions "auto-mark as active for context."

---

#### Message Management UI Components

| Component | Location | Purpose |
|-----------|----------|---------|
| `MessageActionMenu` | `components/Rooms/MessageActionMenu.tsx` | Dropdown with Edit, Pin, Toggle Context, Delete |
| `MessageBadge` | `components/ui/message-badge.tsx` | Visual indicators for edited, pinned, active, inactive states |

**MessageActionMenu Options:**
- Edit (pencil icon) — shown if `can_edit`
- Pin/Unpin (pin icon) — shown if `can_pin`
- Add/Remove from Context (eye/eye-off icon) — always shown
- Delete (trash icon) — shown if `can_delete`

**MessageBadge Variants:**
- `edited` — gray, pencil icon
- `pinned` — yellow, pin icon
- `active` — green, check-circle icon (active for context)
- `inactive` — gray, circle icon (excluded from context)

**Verify:** Open `frontend/src/components/Rooms/MessageActionMenu.tsx` and confirm the toggle context option uses Eye/EyeOff icons.

---

#### Message Management Events

| Event Type | Trigger | Payload | Frontend Action |
|------------|---------|---------|-----------------|
| `message.edited` | Content updated | `{ message_id, content, edited_at, edited_by }` | Invalidate messages |
| `message.pinned` | Message pinned | `{ message_id, pinned_at, pinned_by }` | Invalidate messages |
| `message.unpinned` | Message unpinned | `{ message_id }` | Invalidate messages |
| `message.context_toggled` | Context flag changed | `{ message_id, active_for_context }` | Invalidate messages |
| `message.deleted` | Message soft deleted | `{ message_id }` | Invalidate messages |

**Verify:** In `frontend/src/hooks/useRoomStream.ts`, find the `handleMessage` function and confirm these event types trigger query invalidation.

---

#### Message Management Hook Integration

The `useRoomMessages` hook exposes all message management operations:

```typescript
const {
  // Data
  messages,          // MessageViewModel[]

  // Context management
  toggleContext,     // (messageId: string, active: boolean) => Promise<void>
  isTogglingContext, // boolean

  // Pinning
  pinMessage,        // (messageId: string) => Promise<void>
  unpinMessage,      // (messageId: string) => Promise<void>
  isPinning,         // boolean
  isUnpinning,       // boolean

  // Editing
  editMessage,       // (messageId: string, content: string) => Promise<void>
  isEditing,         // boolean

  // Deletion
  deleteMessage,     // (messageId: string) => Promise<void>
  isDeleting,        // boolean
} = useRoomMessages(roomId)
```

**Verify:** In `frontend/src/hooks/useRoomMessages.ts`, confirm the `UseRoomMessagesResult` interface includes all these fields.

---

#### Backend Context Building

The backend `context_provider.py` filters messages by `active_for_context` when building agent context. Only messages marked as active for context are included.

```python
# Behavior in context_provider.py (lines 265-273):
messages_result = await session.exec(
    select(RoomMessage)
    .where(
        RoomMessage.room_id == room_id,
        RoomMessage.active_for_context == True,  # Context filtering enabled
    )
    .order_by(RoomMessage.created_at.desc())
    .limit(message_limit)  # Default: 20
)
```

**Implication:** Toggling `active_for_context` via the UI directly affects what agents "remember" — messages excluded from context are invisible to agents in subsequent responses.

**Verify:** In `backend/app/services/context_provider.py`, find `build_room_context` and confirm the `.where(RoomMessage.active_for_context == True)` clause is present.

---

#### Conversation Re-run Pattern

A key demo capability: re-running a conversation from a specific point with modified context.

**Pattern:** Given a conversation like:
```
User: message 1
AI: message 2
User: message 3
AI: message 4
User: message 5
AI: message 6
```

To "re-run" starting from message 2 (because the AI's response was effective):
1. Remove message 1 from context (`toggleContext(msg1Id, false)`)
2. Either:
   - **Re-send:** Hit "resend" on message 5 (sends messages 2,3,4,5 as context)
   - **Regenerate:** Hit "regenerate" on message 6 (agent regenerates response)

**Result:** Agent responds with only messages 2-5 in context, effectively "forgetting" message 1.

**Implementation Status:**
- Context toggle: ✅ Implemented (`useRoomMessages.toggleContext`)
- Re-send button: Needs frontend implementation (simple POST to send message)
- Regenerate button: Needs frontend implementation (POST to trigger agent on existing message)

**Verify:** Test by toggling a message's context, then observing the next agent response doesn't reference the excluded content.

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
| `provider` | string \| null | LLM provider (e.g., "anthropic", "openai", "openai_compatible") |

**Key Insight:** `participation_mode: "always"` is required for agents to respond to synthetic messages in demos.

**Model Swapping:**
- **Runtime model changes:** PATCH `/api/v1/agents/{id}` to update `model_name` and/or `provider`. The next message in the room uses the new model.
- **Single-response swaps:** Temporarily PATCH the AgentConfig before triggering a response, then PATCH back. The room doesn't need to be recreated.
- **Model attribution:** `MessageViewModel.agent_name` identifies which agent generated each response. To track model changes, store `model_name` in message metadata or query the agent config at response time.

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

#### Runtime Behavior: Rewind, Reset, and State

Understanding how runtime operations affect state is critical for demos.

**Rewind Mechanics:**
| Operation | Effect on `story_state` | Effect on Messages | Effect on `node_chain` |
|-----------|-------------------------|-------------------|------------------------|
| `rewind(targetChoiceId)` | Reverts to state at target point | Messages preserved (separate from runtime) | Truncates to target |
| `reset()` | Clears to initial state | Messages preserved | Clears to start node |
| `advance(choiceId)` | Accumulates via `sets_state` | Creates new agent context | Appends new node |

**Key Behaviors:**
- **Multi-step rewind:** Backend supports rewinding to any arbitrary point in the choice history, not just one step. Pass `targetChoiceId` to `rewind()`.
- **Message independence:** Room messages exist independently of story runtime. Rewinding does NOT delete messages—only the story position changes.
- **Agent context rebuilding:** Agent context is built fresh on each invocation from current `UserStoryProgress`. After rewind, the next agent call sees the rewound state.
- **state reversion:** On rewind, `story_state` reverts to what it was at that point in the journey. Choices made after that point lose their accumulated state.

**Verify:** Trigger a rewind via `useRoomRuntime.rewind()`, then call `GET /api/v1/rooms/{roomId}/runtime` and confirm `story_state` reflects the rewound state, not the original.

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

**Multi-Step Rewind:** The `rewind(targetChoiceId)` mutation supports jumping to any arbitrary point in the choice history, not just one step back. Pass any valid choice ID from the `node_chain` ancestry.

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

- [x] What field controls whether a message is included in agent context?
  > **Answer:** `MessageViewModel.active_for_context` (boolean, default `true`). See: Entity Dictionary → Message Management System → Message Management Fields
- [x] What field marks a message as important/pinned?
  > **Answer:** `MessageViewModel.is_pinned` (boolean, default `false`). See: Entity Dictionary → Message Management System → Message Management Fields
- [x] Does pinning automatically include a message in context?
  > **Answer:** Yes. Pinning auto-sets `active_for_context=true`. Unpinning does NOT change `active_for_context`. See: Entity Dictionary → Message Management System → Message Management Permissions
- [x] What permissions are required to toggle context?
  > **Answer:** Any active participant can toggle context. See: Entity Dictionary → Message Management System → Message Management Permissions
- [x] What permissions are required to edit/delete messages?
  > **Answer:** Edit: message author OR room owner. Delete: room owner only. Permissions computed by backend via `can_edit`, `can_delete` flags. See: Entity Dictionary → Message Management System → Message Management Permissions

### A.2 API & Hook Questions

- [x] What hook provides context toggle functionality?
  > **Answer:** `useRoomMessages.toggleContext(messageId, active)`. See: Entity Dictionary → Message Management System → Message Management Hook Integration
- [x] What's the loading state for context toggle?
  > **Answer:** `useRoomMessages.isTogglingContext` (boolean). See: Entity Dictionary → Message Management System → Message Management Hook Integration
- [x] How does the UI know which messages are in context?
  > **Answer:** `MessageViewModel.active_for_context` boolean field. Visualized via `MessageBadge` component with "active" or "inactive" variant. See: Entity Dictionary → Message Management System → Message Management UI Components
- [x] What event fires when context is toggled?
  > **Answer:** `message.context_toggled`. See: Entity Dictionary → Message Management System → Message Management Events
- [x] What's the event payload shape for context toggle?
  > **Answer:** `{ message_id, active_for_context }`. See: Entity Dictionary → Message Management System → Message Management Events

### A.3 Backend/Agent Context Questions

- [x] How does the backend filter messages for agent context?
  > **Answer:** The backend loads last N messages filtered by `active_for_context`. See: Entity Dictionary → Message Management System → Backend Context Building 
- [x] Is there a maximum context window size?
  > **Answer:** Default limit is 20 messages (`message_limit` parameter in `build_room_context`). See: `backend/app/services/context_provider.py`
- [x] Are messages filtered by `active_for_context` before being sent to LLM?
  > **Answer:** **Yes.** The backend filters messages by `active_for_context == True` in `build_room_context()`. See: Entity Dictionary → Message Management System → Backend Context Building
- [x] Can we "re-run" a conversation from a specific message?
  > **Answer:** Yes via context manipulation. Remove earlier messages from context, then resend/regenerate. See: Entity Dictionary → Conversation Re-run Pattern
- [x] What happens to agent responses when context changes mid-conversation?
  > **Answer:** The next agent response uses the updated context (filtered by `active_for_context`). No mid-stream interruption—changes take effect on next request.

### A.4 UI/UX Questions

- [x] Where is the context toggle UI located?
  > **Answer:** In `MessageActionMenu` dropdown, accessible via "..." button on each message. Shows "Add to Context" / "Remove from Context" with Eye/EyeOff icons. See: Entity Dictionary → Message Management System → Message Management UI Components
- [x] How do we visualize which messages are in/out of context?
  > **Answer:** `MessageBadge` component with variant "active" (green, check-circle) or "inactive" (gray, circle). See: Entity Dictionary → Message Management System → Message Management UI Components
- [ ] Can we bulk-select messages for context manipulation?
  > **Note:** Not implemented. Needs frontend development (multi-select UI pattern).
- [ ] Is there a "context preview" showing what the agent sees?
  > **Note:** Not implemented. High priority for demos—needs new panel component showing filtered message list.

### A.5 Demo-Specific Questions

- [ ] What's the demo use case for "re-run from checkpoint"?
  > **Note:** Design needed. Concept: user marks "checkpoint", changes context, triggers re-generation. Multiple use cases possible—narrow to one for MVP.
- [x] How do we create a "checkpoint" in a conversation?
  > **Answer:** Backend complete. Use pinned messages or story_state markers. Frontend needs interface to expose checkpoint creation.
- [x] Can we fork a conversation into parallel branches?
  > **Answer:** Data model and backend fully support forking. Frontend needs interface design for branch visualization and selection.
- [ ] How do we compare agent outputs before/after context changes?
  > **Note:** No comparison UI exists. Needs side-by-side panel component.

---

## Addendum B: Open Questions — Story Runtime Navigation Demos

> These questions must be answered before writing Guide B. Check off questions as they are resolved and add answers to the ontology.

### B.1 Data Model Questions

- [x] What fields track story navigation history?
  > **Answer:** `UserStoryProgress.head_version` (choice count), `UserStoryProgress.current_node_id`, `RoomStoryProgress.revision`. The `node_chain` in the API projection provides the breadcrumb trail. See: Entity Dictionary → Runtime Entities
- [x] How does the `revision` field work for optimistic concurrency?
  > **Answer:** All runtime mutations require `expected_revision`. On 409 conflict, the hook auto-refetches. See: Entity Dictionary → RoomStoryProgress and Hook Catalog → useRoomRuntime
- [x] What is `head_choice_id` and how does it enable rewind?
  > **Answer:** `head_choice_id` is the last choice made, stored in `RoomRuntimePublic`. It's used to traverse the choice ancestor chain for rewind. See: Entity Dictionary → RoomRuntimePublic (API Projection)
- [x] How is `node_chain` constructed and maintained?
  > **Answer:** Built from the choice ancestor chain via `get_choice_ancestor_chain_async` in `context_provider.py`. Collects from_node → to_node IDs in traversal order. See: `backend/app/services/context_provider.py` lines 224-247
- [x] What's the relationship between `UserStoryProgress` and `RoomStoryProgress`?
  > **Answer:** `RoomStoryProgress` points to `UserStoryProgress` via `active_progress_id`. Room-level has `revision` for concurrency, user-level has `head_version` for choice count. See: Entity Dictionary → Runtime Entities

### B.2 Rewind/Reset Mechanics Questions

- [x] What's the difference between rewind and reset?
  > **Answer:** `rewind(targetChoiceId)` goes back to a specific choice point. `reset()` returns to start node. Both exposed via `useRoomRuntime`. See: Hook Catalog → useRoomRuntime
- [x] Can we rewind to any arbitrary point, or only one step back?
  > **Answer:** Arbitrary points supported. Pass any `targetChoiceId` to `rewind()`. Backend supports multi-step rewind to any point in the tree. See: Entity Dictionary → Runtime Behavior and Hook Catalog → useRoomRuntime
- [x] What happens to story_state when we rewind?
  > **Answer:** `story_state` reverts to what it was at the target point. See: Entity Dictionary → Runtime Behavior: Rewind, Reset, and State
- [x] Are rewound messages preserved or deleted?
  > **Answer:** Messages are preserved. Room messages exist independently of story runtime state. See: Entity Dictionary → Runtime Behavior
- [x] How does rewind affect agent context?
  > **Answer:** Agent context rebuilds fresh on each invocation from current `UserStoryProgress`. After rewind, the next agent call sees the rewound state. See: Entity Dictionary → Runtime Behavior

### B.3 Model Swapping Questions

- [x] How do we change an agent's model mid-conversation?
  > **Answer:** PATCH `/api/v1/agents/{id}` with new `model_name` and/or `provider`. Next message in room uses new model. See: Entity Dictionary → AgentConfig → Model Swapping
- [x] Is model swapping a runtime operation or does it require agent reconfiguration?
  > **Answer:** Requires AgentConfig PATCH. The update takes effect immediately—next room message uses the new configuration.
- [x] Can we swap models for a single response without permanent change?
  > **Answer:** Yes. PATCH AgentConfig before triggering response, then PATCH back. See: Entity Dictionary → AgentConfig → Model Swapping
- [ ] What API endpoints support model configuration?
  > **Note:** PATCH `/api/v1/agents/{id}` exists. Need to document full capabilities and available model options per provider.

- [x] How do we access the `provider` and `model_name` fields for an agent in a room?
  > **Answer:** `AgentConfig` has `provider` (string | null) and `model_name` (string) fields. Agents in rooms are accessed via participant lookup → slug → AgentConfig. See: Entity Dictionary → AgentConfig

### B.4 Comparison & A/B Testing Questions

- [x] How do we run the same prompt through two different models?
  > **Answer:** Add multiple agents with different `model_name`/`provider` values to the same room. All agents receive all messages (tested up to 100 agents). See: Entity Dictionary → Room → Multi-Agent Behavior
- [x] Can we create parallel conversation branches for comparison?
  > **Answer:** Yes. Backend fully supports parallel branches. Frontend needs design for retrieval interface.
- [x] Is there a diff/comparison UI pattern for agent outputs?
  > **Answer:** Implemented on backend. Frontend needs design to request interfaces and exports.
- [x] How do we store and retrieve comparison results?
  > **Answer:** Backend stores everything. Frontend needs to request interface specifications.
- [x] Can we replay a conversation segment with a different model?
  > **Answer:** Yes, fully supported. Swap AgentConfig, re-trigger message. See: Entity Dictionary → Room → Multi-Agent Behavior

### B.5 UI/UX Questions

- [x] How do we visualize the story path/node history?
  > **Answer:** `RoomRuntimeViewModel.nodeChain` contains the breadcrumb trail of `NodeViewModel[]`. StoryPanel renders this. See: ViewModel Glossary → RoomRuntimeViewModel
- [x] Where are rewind/reset controls located?
  > **Answer:** In StoryPanel component, controlled by `useRoomRuntime` hook. `canRewind` and `canReset` flags determine visibility. See: Hook Catalog → useRoomRuntime
- [x] How do we show "what-if" branching options?
  > **Answer:** Timeline and tree branching visualization exists in StoryRuntime and StoryEditor components. See: `frontend/src/components/Story/`
- [x] Is there a timeline or breadcrumb UI for story navigation?
  > **Answer:** `nodeChain` provides breadcrumb data. Basic display exists in StoryPanel. See: ViewModel Glossary → RoomRuntimeViewModel
- [x] How do we indicate which model generated which response?
  > **Answer:** `MessageViewModel.agent_name` identifies the agent. To track model per response, correlate with AgentConfig state at generation time.

### B.6 Demo-Specific Questions

- [ ] What's the demo use case for "swap model and compare"?
  > **Note:** Design needed. Concept: same story node, same context, different AI voice.
- [ ] How do we set up a side-by-side comparison view?
  > **Note:** Would need new SideBySidePanel component or multi-column layout.
- [ ] Can we automate regression testing across models?
  > **Note:** No automation exists. Would need test harness + comparison framework.
- [ ] What metrics should we capture for model comparison?
  > **Note:** Design needed. Candidates: response time, token count, content similarity, user preference.

---

## Addendum C: Open Questions — Hidden Orchestrator Demos

> These questions must be answered before writing Guide C. Check off questions as they are resolved and add answers to the ontology.

### C.1 Architecture Questions

- [x] What is the "hidden orchestrator" pattern?
  > **Answer:** Design pattern where orchestrator agent is invisible to user, coordinates subagents via A2A, emits only AG-UI components to user.
- [x] How do orchestrators differ from regular agents?
  > **Answer:** Same AgentConfig model. Differentiated by: (1) system_prompt instructing coordination behavior, (2) participation_mode, (3) UI hides their messages from user.
- [x] What's the relationship between orchestrators and subagents?
  > **Answer:** All are AgentConfig instances in the same room. Orchestrator invokes others via @mention or A2A messages with `sender_type: "agent_internal"`.
- [x] How does A2A (agent-to-agent) messaging work?
  > **Answer:** Agent emits message with `sender_type: "agent_internal"`. Backend routes based on @mentions or participation_mode. See: Entity Dictionary → Message
- [ ] What's the message flow: user → orchestrator → subagent → AG-UI?
  > **Note:** Flow: user message → orchestrator triggered → orchestrator emits A2A → subagent triggered → subagent emits AG-UI. Needs sequence diagram.

### C.2 A2A Messaging Questions

- [x] What is `sender_type: "agent_internal"` and when is it used?
  > **Answer:** A2A message type for agent-to-agent communication. Not shown to users by default. See: Entity Dictionary → Message
- [x] How do agents send messages to other agents?
  > **Answer:** Agent emits message with `sender_type: "agent_internal"`. Backend routes based on @mentions or participation_mode. See: Entity Dictionary → Message
- [x] Are A2A messages visible to users by default?
  > **Answer:** No. Filtered out by default. See: Hook Catalog → useRoomMessages (`includeInternalMessages` option)
- [x] How do we filter/show A2A messages for debugging?
  > **Answer:** Pass `includeInternalMessages: true` to `useRoomMessages`. Query key becomes `["rooms", roomId, "messages", "with-internal"]`. See: Hook Catalog → useRoomMessages
- [x] What events fire for A2A message exchange?
  > **Answer:** `room_message.agent_internal` event. Invalidates messages query only if `includeInternalMessages` enabled. See: Real-time Event Types → Message Events

### C.3 Hidden Room/UI Questions

- [x] How do we hide the chat panel and show only AG-UI?
  > **Answer:** Layout customization via ResizablePanelGroup. Render only A2UIPanel, collapse or omit chat panels.
- [x] Can we create a "headless" room that only emits AG-UI?
  > **Answer:** Yes. Room exists normally; UI chooses what to render. Create AG-UI-only layout variant.
- [x] How do we hide the story panel while keeping runtime active?
  > **Answer:** StoryPanel is optional. `useRoomRuntime` hook works independently of panel visibility.
- [x] What layout configurations support AG-UI-only views?
  > **Answer:** DemoPage uses ResizablePanelGroup. Create variant with only A2UIPanel visible.
- [x] How do we prevent users from sending direct messages?
  > **Answer:** UI-level only—hide MessageInput component. Backend doesn't enforce (room still accepts messages via API).

### C.4 AG-UI Navigation Questions

- [x] How do action_buttons drive story/conversation navigation?
  > **Answer:** Button click → `onAction(action, componentId)` → `RoomService.sendUIAction()` → backend handles action. See: AG-UI Component Types → action_buttons
- [ ] Can AG-UI buttons trigger story choices (advance/rewind)?
  > **Note:** Backend would need action handler mapping action strings to runtime mutations. Pattern: `"advance:{choiceId}"` or `"rewind:{choiceId}"`.
- [ ] How do we map button actions to runtime operations?
  > **Note:** Needs backend action handler. Proposed: parse action string, extract operation and ID, call runtime mutation.
- [ ] What's the action string format for navigation buttons?
  > **Note:** Custom per-implementation. Proposed convention: `"operation:param"` (e.g., `"advance:abc-123"`, `"rewind:def-456"`).
- [x] How does the backend interpret AG-UI action payloads?
  > **Answer:** `UIActionRequest` contains `action`, `source_message_id`, `component_id`. Backend looks up originating agent and invokes with action as context. See: `backend/app/models.py` UIActionRequest class

### C.5 Orchestrator Coordination Questions

- [ ] How does an orchestrator decide which subagent to invoke?
  > **Note:** System prompt + conversation context. Could use capabilities field for routing.
- [ ] Can an orchestrator invoke multiple subagents in sequence?
  > **Note:** Yes via multiple A2A messages, but need to verify concurrency handling.
- [ ] How do subagent responses flow back through the orchestrator?
  > **Note:** Subagent emits to room → all agents see it → orchestrator can react. Need formal pattern.
- [ ] Is there a state machine pattern for orchestrator workflows?
  > **Note:** Not implemented. Could use story_state or custom context for workflow tracking.
- [ ] How do we handle orchestrator errors/timeouts?
  > **Note:** Standard agent error handling applies. No orchestrator-specific patterns exist.

### C.6 Demo-Specific Questions

- [ ] What's the demo use case for "wizard-style guided experience"?
  > **Note:** Design needed. User sees only AG-UI cards/buttons, hidden orchestrator guides flow.
- [ ] How do we design a progressive disclosure flow with AG-UI?
  > **Note:** Orchestrator emits collapsible/tabs components, reveals more based on user actions.
- [ ] Can we create branching wizard paths based on user choices?
  > **Note:** Button actions could drive different orchestrator responses. Need state tracking.
- [ ] How do we track user progress through an orchestrated flow?
  > **Note:** Could use story_state, or custom context_store items, or external state.
- [ ] What's the minimum viable hidden orchestrator demo?
  > **Note:** Single orchestrator + one subagent, hidden chat, AG-UI buttons for navigation.

---

## Addendum D: Open Questions — The Loom of Infinite Stories

> These questions must be answered before writing Guide D. Demo D synthesizes capabilities from A, B, and C into an emergent experience. Questions are organized by the intersections that create magic.

### D.1 Foundation Integration Questions

- [ ] Can all three systems (context manipulation, runtime navigation, hidden orchestration) operate simultaneously in a single room?
- [ ] What's the initialization sequence for a room with context controls, runtime, AND hidden orchestration?
- [ ] How do we ensure the three systems don't conflict (e.g., orchestrator changing context while user is manipulating it)?
- [ ] What's the unified state model that tracks context state + runtime position + orchestrator workflow state?
- [ ] Can we create a "meta-ViewModel" that exposes the combined state of all three systems?

### D.2 Memory × Time Questions (Context + Runtime)

- [ ] When rewinding runtime, should context exclusions also rewind, or persist as "meta-memory"?
- [ ] Can we create a "context checkpoint" tied to a specific runtime revision?
- [ ] How do we branch both context AND runtime simultaneously into parallel timelines?
- [ ] What happens to `active_for_context` flags on messages that get "rewound past"?
- [ ] Can the story runtime's `story_state` influence which messages are auto-included in context?

### D.3 Time × Voice Questions (Runtime + Model Swapping)

- [ ] Can we store multiple model outputs for the same runtime position?
- [ ] How do we render the same story node content from different models side-by-side?
- [ ] Is model selection per-room, per-agent, or can it be per-response?
- [ ] Can we "replay" a runtime segment with a different model without affecting the canonical timeline?
- [ ] How do we attribute which model generated which historical response?

### D.4 Voice × Memory Questions (Model Swapping + Context)

- [ ] Can different models in the same room see different context subsets?
- [ ] How do we coordinate context windows when models have different context limits?
- [ ] Can an agent's system prompt dynamically adjust based on context inclusion state?
- [ ] Is it possible to have "model-specific memories" (Claude remembers X, GPT sees Y)?
- [ ] How do we visualize the delta between what different models would "see" given the same context flags?

### D.5 Orchestrator × Memory Questions (Hidden Orchestration + Context)

- [ ] Can the orchestrator programmatically toggle `active_for_context` on messages?
- [ ] How does the orchestrator make context decisions without user visibility?
- [ ] Can subagents have different context views than the orchestrator?
- [ ] What's the A2A message format for instructing context manipulation?
- [ ] How do we audit/log orchestrator context decisions for debugging?

### D.6 Orchestrator × Time Questions (Hidden Orchestration + Runtime)

- [ ] Can the orchestrator trigger advance/rewind/reset without user interaction?
- [ ] How do we synchronize orchestrator workflow state with runtime revision?
- [ ] Can AG-UI buttons directly invoke runtime operations (advance, rewind)?
- [ ] What happens if the orchestrator rewinds while a subagent is mid-response?
- [ ] How do we prevent infinite loops (orchestrator rewinds → triggers event → orchestrator rewinds)?

### D.7 Orchestrator × Voice Questions (Hidden Orchestration + Model Selection)

- [ ] Can the orchestrator dynamically select which model handles each subagent response?
- [ ] How does the orchestrator coordinate handoffs between different models?
- [ ] Can A2A messages include model routing hints?
- [ ] How do we handle model-specific capabilities in orchestrated workflows (e.g., Claude for reasoning, GPT for creativity)?
- [ ] Can the orchestrator spawn temporary "ephemeral" agents with specific model configurations?

### D.8 The Triple Intersection Questions (All Three Systems)

- [ ] What's the data structure that represents a "moment" in the Loom (context state + runtime position + active model + orchestrator state)?
- [ ] Can we serialize and restore a complete Loom state for "save points"?
- [ ] How do we visualize the three-dimensional possibility space (memory × time × voice)?
- [ ] What AG-UI components are needed to represent threads, brightness, and color in the tapestry metaphor?
- [ ] How do we prevent combinatorial explosion (N context states × M runtime positions × K model options)?

### D.9 Novel AG-UI Component Questions

- [ ] What does a "thread" component look like (representing a story-moment-with-memory-state)?
- [ ] How do we render "brightness" (memory strength) visually in AG-UI?
- [ ] What's the interaction model for "pulling threads together" (merging timelines)?
- [ ] Can AG-UI components have continuous state (not just discrete actions)?
- [ ] How do we animate transitions between Loom states?

### D.10 Performance & Architecture Questions

- [ ] What's the latency budget for a Loom state change (context + runtime + model)?
- [ ] How do we cache/precompute alternative timeline branches?
- [ ] Can we use optimistic UI for Loom interactions (show predicted state before confirmation)?
- [ ] What's the WebSocket event model for coordinated state changes?
- [ ] How do we handle partial failures (e.g., context toggle succeeds but model swap fails)?

### D.11 Experience Design Questions

- [ ] What's the onboarding experience for users encountering the Loom?
- [ ] How do we teach the metaphor without breaking immersion?
- [ ] What are the "undo" semantics when everything is already about time manipulation?
- [ ] How do we prevent overwhelm from too many possibilities?
- [ ] What's the "default" mode that feels simple but reveals depth on demand?

### D.12 Ethical & Safety Questions


- [ ] How do we prevent the Loom from generating contradictory or harmful content across branches?

- [ ] How do we handle "prompt injection via context manipulation"?

- [ ] How do we audit Loom sessions for safety review?

---

## Addendum E: Open Questions — Discovered During Documentation Review

> These questions emerged while reviewing the implementation status against Addendums A–D. They represent gaps between documented features and actual implementation, or areas where documentation is silent.

### E.1 Backend API Completeness

> **Context:** Addendum questions assume certain backend capabilities. These questions verify whether those capabilities exist.

- [x] Does the backend support multi-step rewind (rewinding multiple choices at once)?
  > **Answer:** Yes. See: Entity Dictionary → Runtime Behavior and Addendum B.2
- [x] Can `POST /rooms/{room_id}/runtime/rewind` accept a `target_choice_id` to rewind to a specific point?
  > **Answer:** Yes. Pass any valid choice ID from the ancestry chain. See: Hook Catalog → useRoomRuntime
- [x] What API endpoint configures which model an agent uses at runtime?
  > **Answer:** PATCH `/api/v1/agents/{id}` with `model_name`/`provider`. See: Entity Dictionary → AgentConfig → Model Swapping
- [ ] Is there an API to list available models per provider for the UI dropdown?
- [x] Can agent model configuration be changed per-room, or only globally?
  > **Answer:** Globally per AgentConfig. To vary per-room, create separate agent instances or swap config at runtime.
- [ ] Does `RoomService.toggleMessageContext()` exist in the generated client? (Validation needed)
- [ ] What's the API contract for bulk context operations (e.g., "exclude all messages before X")?

### E.2 Event System Completeness

> **Context:** Real-time events drive UI updates. These questions verify event coverage.

- [ ] Is there a `runtime.model_changed` event when an agent's model is swapped?
- [ ] What event is emitted when the story runtime is reset (not just rewound)?
- [ ] Are message management events (`message.edited`, etc.) emitted for system-generated messages?
- [ ] Can the frontend subscribe to events for specific message IDs rather than room-wide?
- [x] What's the event payload for `message.context_toggled`? Does it include the new `active_for_context` value?
  > **Answer:** `{ message_id, active_for_context }`. See: Entity Dictionary → Message Management Events
- [ ] Is there an event for when an agent "joins" vs "is enabled" in a room?

### E.3 Hook and Mutation Verification

> **Context:** Hooks documented in the ontology need verification against actual implementation.

- [ ] Does `useRoomMessages` correctly handle optimistic updates for `toggleContext`?
- [ ] What's the error recovery behavior when `pinMessage` fails (e.g., already pinned)?
- [x] Is there a hook for story runtime state (`useStoryRuntime` or similar)?
  > **Answer:** `useRoomRuntime` manages story runtime state. See: Hook Catalog → useRoomRuntime
- [ ] How does `useRoomStream` handle reconnection during a multi-step operation?
- [ ] Are mutation loading states (`isEditing`, `isPinning`) used anywhere in UI currently?
- [ ] Can we add optimistic UI for context toggling (immediate visual feedback)?

### E.4 ViewModel Mapping Gaps

> **Context:** ViewModels transform API types for the UI. These questions explore transformation edge cases.

- [ ] Does `MessageViewModel` include `edited_by` user info or just the ID?
- [ ] How is `pinned_at` formatted in the ViewModel (ISO string, relative time, or both)?
- [ ] Is there a ViewModel for story runtime state, or is the raw API response used?
- [ ] What happens to `MessageViewModel` if the message is deleted server-side but cached client-side?
- [ ] Does the ViewModel include computed fields like "isOwnMessage" or "canEditThisMessage"?
- [ ] How are permission flags (`can_edit`, `can_delete`, `can_pin`) populated for agent messages?

### E.5 AG-UI Integration Questions

> **Context:** AG-UI components enable rich agent interactions. These questions explore integration points.

- [ ] Can an AG-UI button trigger a context toggle operation?
- [ ] Can an AG-UI component display real-time context inclusion state?
- [ ] How do AG-UI components receive updates when message state changes?
- [ ] Can the orchestrator emit AG-UI components that visualize story runtime position?
- [ ] What's the AG-UI component for a "context selector" (multi-select messages)?
- [ ] Can AG-UI forms submit data that affects story state?

### E.6 Demo Feasibility Verification

> **Context:** These questions validate whether the demos are actually buildable with current infrastructure.

- [ ] **Demo B Dependency:** Is `revision` field actually used for optimistic concurrency in rewind?
- [ ] **Demo B Question:** What visual feedback exists during story rewind? (Loading state?)
- [ ] **Demo C Question:** Are A2A messages (`sender_type: "agent_internal"`) visible in any debugging UI?
- [ ] **Demo C Question:** How do we verify the orchestrator received an A2A message?
- [ ] **Demo D Feasibility:** What's the minimum viable state sync between context, runtime, and orchestrator?

### E.7 Testing and Validation Questions

> **Context:** Engineers need ways to verify their implementations.

- [ ] How do we write a unit test for `active_for_context` affecting agent responses?
- [ ] Is there a test environment with pre-seeded rooms demonstrating message management?
- [ ] Can we mock the WebSocket connection for testing event handlers?
- [ ] What's the test strategy for optimistic update rollback on error?
- [ ] How do we test orchestrator workflows without a full multi-agent setup?
- [ ] Are there Playwright tests covering message management UI actions?

### E.8 Documentation Discrepancies

> **Context:** Questions arising from inconsistencies in existing documentation.

- [ ] Phase 5 Architecture Review mentions `MessageFilters` component but it's not in the ontology. Should it be added?
- [ ] The ontology lists `useAgentStream` but message-management docs don't reference it. Is it relevant?
- [ ] Where is the canonical source of truth for message permission rules?
- [ ] Are there sequence diagrams showing the full message management flow?

### E.9 Future Considerations

> **Context:** Questions that inform architectural decisions for upcoming work.

- [ ] What's the MVP scope for each demo to prove the concept before full implementation?
- [ ] Can we create a "demo harness" that pre-configures rooms for each demo scenario?
- [ ] Should demos have their own routes (e.g., `/demo/memory-surgeon`) or use standard room views?
- [ ] How do we measure demo success (user engagement, error rates, completion)?
