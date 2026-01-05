# Story System Documentation (V2)

**Last Updated:** 2026-01-02
**Status:** ✅ Production Ready (Phase 1-3 Complete)
**Version:** 2.0 - CYOA with Timeline Navigation
**Source of Truth:** Reflects actual backend implementation including Phase 1-3 event sourcing

---

## Table of Contents

1. [Overview & Evolution](#overview--evolution)
2. [Architecture](#architecture)
3. [Data Models](#data-models)
4. [API Reference](#api-reference)
5. [Timeline Navigation (Phase 3)](#timeline-navigation-phase-3)
6. [Common Workflows](#common-workflows)
7. [Event Sourcing & State Management](#event-sourcing--state-management)
8. [Development Guide](#development-guide)
9. [Known Limitations](#known-limitations)
10. [Migration from V1](#migration-from-v1)

---

## Overview & Evolution

The Story System implements **versioned, event-sourced interactive narratives** (CYOA - Choose Your Own Adventure) with **timeline navigation** and **branching history**.

### What's New in V2 (Phase 1-3 CYOA)

**Phase 1-2: Event Sourcing Foundation**
- ✅ Parent-child pointers in choice history (tree structure)
- ✅ Head pointer tracking current timeline position
- ✅ Optimistic concurrency control (`head_version`)
- ✅ State replay from event history

**Phase 3: Timeline Navigation**
- ✅ **Undo**: Rewind one step in timeline
- ✅ **Jump**: Rewind to arbitrary ancestor choice
- ✅ **Timeline**: View breadcrumb trail (root → head)
- ✅ Hidden branches (abandoned choices stay in DB but invisible to player)

**Phase 4 Prep: Real-time Distribution** (In Progress)
- ✅ Redis pub/sub event publishing
- ✅ WebSocket support for story updates
- 🔄 Multi-player story experiences (future)

### Core Principles

1. **Stories are Templates**: Authors create reusable story templates
2. **Version Locking**: Players lock to specific version when starting (never experience mid-game changes)
3. **Event Sourcing**: Choices are immutable events forming a tree structure
4. **Timeline Navigation**: Players can undo/jump to any ancestor, creating branching futures
5. **State Replay**: Story state is derived by replaying events from root to head
6. **Hidden Branches**: Abandoned timelines remain in database but hidden from player

### The Three Namespaces

```
┌─────────────────┐
│   AUTHORING     │ /stories         → Creators draft, version, publish
├─────────────────┤
│   DISCOVERY     │ /catalog         → Users browse published stories
├─────────────────┤
│   PLAYING       │ /user-personas/  → Players navigate with undo/jump
│                 │ {id}/stories
└─────────────────┘
```

---

## Architecture

### Event Sourcing Timeline

```
Story Start (head_choice_id=null, head_version=0)
    │
    ├─ Choice A (head_version=1, parent=null)
    │   │
    │   ├─ Choice B (head_version=2, parent=A)
    │   │   │
    │   │   └─ Choice C (head_version=3, parent=B)  ← Current head
    │   │       │
    │   │       └─ [ABANDONED] Choice D (parent=C, NOT on active path)
    │   │
    │   └─ [ABANDONED] Choice E (parent=A, NOT on active path)
    │
    └─ [ABANDONED] Choice F (parent=null, NOT on active path)

Active Timeline: Start → A → B → C (visible via /timeline)
Abandoned Branches: D, E, F (hidden from player, retained in DB)
```

**Key Concepts:**
- **Head Pointer** (`head_choice_id`): Current position in timeline tree
- **Parent Pointers** (`parent_choice_id`): Link choices into tree structure
- **Head Version** (`head_version`): Increments on every timeline mutation (undo/jump/choice)
- **Active Path**: Root to head chain (visible to player)
- **Abandoned Branches**: Sibling choices and their descendants (hidden, preserved for analytics)

### Versioning System

```
Story (version 1, draft)  ──┐
                            │── Author publishes
                            ↓
Story (version 1, published) → Players lock to v1
Story (version 2, draft)     → Author continues editing

Player A: Locked to v1 ─→ Always plays v1, can undo/jump within v1
Player B: Locked to v1 ─→ Always plays v1, independent timeline
```

**Version Fields:**
- `current_version` (int): Author's draft workspace (default: 1)
- `published_version` (int | null): Locked catalog version
- `is_published` (bool): Catalog visibility

**Publishing Flow:**
1. Author creates story (v1, unpublished)
2. Author publishes → `published_version = 1`, `is_published = true`
3. Players start story → locked to `published_version = 1`
4. Author creates new version → `current_version = 2` (copies v1 nodes/choices)
5. Existing players continue on v1, new players lock to v2

### State Accumulation with Replay

```
State Derivation:
1. Start at story_state = {}
2. Walk timeline from root to head
3. Apply each choice's state_changes in sequence
4. Result = current story_state

Example:
  Start → {}
  → Choice A (sets: {torch: true}) → {torch: true}
  → Choice B (sets: {cave: true})  → {torch: true, cave: true}
  → Undo to A → Replay to A only  → {torch: true}
```

**Benefits:**
- **Undo works correctly**: State is always re-derived
- **No state drift**: Replayed state matches timeline
- **Audit trail**: Full history preserved for analytics

---

## Data Models

### Story (Template)

```python
class Story:
    id: UUID
    owner_id: UUID              # Who created this story
    title: str
    description: str | None

    # Versioning
    current_version: int        # Draft workspace (default: 1)
    published_version: int | None  # Locked catalog version
    is_published: bool          # Catalog visibility (default: False)

    # Timestamps
    created_at: datetime
    updated_at: datetime
```

**Relationships:**
- `nodes: list[StoryNode]` - All nodes across all versions
- `requirements: list[StoryRequirement]` - Access gating
- `user_progresses: list[UserStoryProgress]` - Player instances

### StoryNode (Scene Template)

```python
class StoryNode:
    id: UUID
    story_id: UUID
    story_version: int          # Which version this node belongs to

    title: str
    content: str                # Narrative text
    node_type: str              # "text", "image", "choice" (default: "text")

    is_start_node: bool         # One per story_version (default: False)
    is_end_node: bool           # Can have multiple ends (default: False)

    created_at: datetime
    updated_at: datetime
```

**Authoring Note:** StoryNode route is `/storynodes`

### NodeChoice (Decision Branch)

```python
class NodeChoice:
    id: UUID
    from_node_id: UUID          # Starting node
    to_node_id: UUID            # Destination node

    text: str                   # Choice description shown to player
    order: int                  # Display order (default: 0)

    # Conditional logic
    requires_state: dict[str, Any] | None  # Conditions to show this choice
    sets_state: dict[str, Any] | None      # State changes when chosen
```

**Example:**
```json
{
  "text": "Enter the dark cave",
  "from_node_id": "node-forest-123",
  "to_node_id": "node-cave-456",
  "order": 1,
  "requires_state": {"has_torch": true},
  "sets_state": {"visited_cave": true, "courage": 10}
}
```

**⚠️ CAREFUL:** NodeChoice CRUD API endpoints did not exist when spec was written. There may be drift that needs review. [Known Limitations](#known-limitations).

### UserStoryProgress (Player Instance) - **UPDATED FOR PHASE 1-3**

```python
class UserStoryProgress:
    id: UUID
    user_persona_id: UUID       # Player identity
    story_id: UUID              # Which story template
    story_version: int          # Locked at creation (immutable!)

    current_node_id: UUID | None  # Where player is now (derived from head)
    is_completed: bool          # Reached an end node (default: False)

    # State accumulator (JSON dict, replayed from head)
    story_state: dict[str, Any] | None  # Game variables

    # NEW: Timeline Navigation (Phase 1-3)
    head_choice_id: UUID | None  # Current position in timeline tree
                                  # (null = at story start)
    head_version: int            # Optimistic concurrency control
                                  # (increments on every head move)

    started_at: datetime
    updated_at: datetime
```

**Head Pointer Semantics:**
- `head_choice_id = null` → Player at story start
- `head_choice_id = choice_uuid` → Player at that choice's destination node
- `head_version` → Prevents race conditions in concurrent operations

**Relationships:**
- `user_persona: UserPersona`
- `story: Story`
- `current_node: StoryNode` - Current position (references template)
- `choice_history: list[UserNodeChoice]` - Full choice tree (includes abandoned branches)

### UserNodeChoice (Decision History) - **UPDATED FOR PHASE 1-3**

```python
class UserNodeChoice:
    id: UUID
    progress_id: UUID           # Which playthrough

    # NEW: Parent pointer for tree structure (Phase 1)
    parent_choice_id: UUID | None  # Parent event (null for first choice)

    choice_text: str            # What the player chose
    from_node_id: UUID          # Where they were
    to_node_id: UUID            # Where they went

    state_changes: dict[str, Any] | None  # Snapshot of sets_state applied
    rng_data: dict[str, Any] | None       # RNG outcomes for replay
    choice_time: datetime
```

**Tree Structure:**
- First choice has `parent_choice_id = null`
- Subsequent choices point to their parent
- Forms directed acyclic graph (DAG) of player history
- Enables ancestor chain queries for timeline/undo/jump

**Purpose:** Immutable event log for:
- Timeline navigation (undo/jump)
- State replay
- Analytics and achievements
- Abandoned branch preservation

### StoryRequirement (Access Gating)

```python
class StoryRequirement:
    id: UUID
    story_id: UUID

    requirement_type: str       # "quality", "trait", etc.
    target_id: UUID             # ID of required quality/trait
    description: str | None     # Human-readable explanation
```

**Example:** Require "Detective" trait to access mystery stories

**⚠️ MISSING IMPLEMENTATION:** StoryRequirement CRUD API endpoints do not exist. Requirements must be created directly via SQL. See [Known Limitations](#known-limitations).

---

## API Reference

### AUTHORING Namespace: `/stories`

**Who:** Story creators (authors)
**Access:** Owner or superuser

#### List Stories

```http
GET /stories?skip=0&limit=10
```

**Returns:** User's stories (superusers see all)

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "owner_id": "uuid",
      "title": "The Dark Forest",
      "description": "A spooky adventure",
      "current_version": 2,
      "published_version": 1,
      "is_published": true,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

#### Get Story

```http
GET /stories/{story_id}
```

**Returns:** Story details for editing

#### Get Start Node

```http
GET /stories/{story_id}/start-node
```

**Returns:** The node marked `is_start_node=true` for `current_version`

**Use Case:** Validate story structure before publishing

#### Create Story

```http
POST /stories
Content-Type: application/json

{
  "title": "My Adventure",
  "description": "An epic tale"
}
```

**Returns:** New story with `current_version=1`, `is_published=false`

**⚠️ IMPORTANT:** Do NOT send `current_version` in payload - it's set automatically by database default.

#### Update Story

```http
PUT /stories/{story_id}
Content-Type: application/json

{
  "title": "My Adventure (Revised)",
  "description": "An even better tale"
}
```

**Returns:** Updated story (metadata only, not version)

#### Publish Story

```http
PUT /stories/{story_id}/publish
```

**Effect:**
- Sets `published_version = current_version`
- Sets `is_published = true`
- Makes story visible in catalog
- Players can now start this version

**Returns:** Updated story

#### Unpublish Story

```http
PUT /stories/{story_id}/unpublish
```

**Effect:**
- Sets `is_published = false`
- Keeps `published_version` intact
- Hides from catalog
- Existing players unaffected

**Returns:** Updated story

#### Create New Version

```http
POST /stories/{story_id}/new-version
```

**Effect:**
1. Increments `current_version` (e.g., 1 → 2)
2. Copies all nodes from `published_version` to new `current_version`
3. Copies all choices, remapping node IDs
4. `published_version` remains locked

**Requires:** Story must have been published at least once

**Use Case:** Edit a published story without affecting active players

**Returns:** Updated story

#### Delete Story

```http
DELETE /stories/{story_id}
```

**Access:** Superuser only (currently)

**Effect:** Cascades to nodes, choices, progresses

**Returns:** Success message

---

### NODE MANAGEMENT Namespace: `/storynodes`

**Who:** Authors (currently superuser only for updates/deletes)
**Access:** Authenticated users (create), superuser (update/delete)

**⚠️ ROUTE NOTE:** Endpoint is `/storynodes` (no hyphen), not `/story-nodes`

#### List Nodes

```http
GET /storynodes?skip=0&limit=100
```

**Returns:** All story nodes (across all stories and versions)

#### Get Node

```http
GET /storynodes/{node_id}
```

**Returns:** Single node details

#### Create Node

```http
POST /storynodes
Content-Type: application/json

{
  "story_id": "uuid",
  "story_version": 1,
  "title": "Chapter One",
  "content": "You wake up in a dark forest...",
  "node_type": "text",
  "is_start_node": true,
  "is_end_node": false
}
```

**Returns:** Created node

**Best Practice:** Create nodes for `current_version`, not `published_version`

**Implementation Note:** Creates `storynode_title` field from title (lowercased, spaces to underscores, max 50 chars)

#### Update Node

```http
PUT /storynodes/{node_id}
Content-Type: application/json

{
  "title": "Chapter One (Revised)",
  "content": "You wake up in a mysterious forest..."
}
```

**Access:** Superuser only

**Returns:** Updated node

#### Delete Node

```http
DELETE /storynodes/{node_id}
```

**Access:** Superuser only

**Effect:** Cascades to choices referencing this node

**Returns:** Success message

---

### DISCOVERY Namespace: `/catalog`

**Who:** All users browsing for stories
**Access:** Public (with optional requirement gating)

#### Browse Catalog

```http
GET /catalog?skip=0&limit=10
```

**Returns:** Published stories (`is_published=true` only)

#### Get Catalog Story

```http
GET /catalog/{story_id}
```

**Returns:** Published story details (404 if unpublished)

#### Preview Story Nodes

```http
GET /catalog/{story_id}/nodes?skip=0&limit=100
```

**Returns:** Nodes from `published_version` (not current_version drafts)

**Use Case:** Show story structure before starting

#### Check Story Requirements

```http
GET /catalog/{story_id}/requirements
```

**Returns:** Requirements needed to start this story

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "story_id": "uuid",
      "requirement_type": "quality",
      "target_id": "detective-quality-uuid",
      "description": "Must have Detective quality enabled"
    }
  ],
  "count": 1
}
```

---

### PLAYING Namespace: `/user-personas/{user_persona_id}/stories`

**Who:** Players experiencing adventures
**Access:** Persona owner only

#### List Player's Stories

```http
GET /user-personas/{user_persona_id}/stories?skip=0&limit=100
```

**Returns:** All story instances (playthroughs) for this persona

**Response includes Phase 3 fields:**
```json
{
  "data": [
    {
      "id": "progress-uuid",
      "user_persona_id": "persona-uuid",
      "story_id": "story-uuid",
      "story_version": 1,
      "current_node_id": "node-uuid",
      "is_completed": false,
      "story_state": {"has_torch": true, "visited_cave": false},
      "head_choice_id": "choice-uuid",
      "head_version": 3,
      "started_at": "2024-01-10T14:00:00Z",
      "updated_at": "2024-01-10T14:30:00Z"
    }
  ],
  "count": 3
}
```

#### Get Story Progress

```http
GET /user-personas/{user_persona_id}/stories/{story_id}
```

**Returns:** Player's instance of this story (version lock, state, position, head pointer)

#### Start Story

```http
POST /user-personas/{user_persona_id}/stories/{story_id}
```

**Effect:**
1. Validates persona meets story requirements
2. Creates `UserStoryProgress` locked to `story.current_version`
3. Sets `current_node_id` to story's start node
4. Initializes `story_state = {}`
5. Sets `head_choice_id = null` (at story start)
6. Sets `head_version = 0`

**Errors:**
- `400`: Progress already exists
- `403`: Persona doesn't meet requirements
- `404`: Story or persona not found
- `500`: No start node found

**Returns:** New progress instance

#### Get Current Position

```http
GET /user-personas/{user_persona_id}/stories/{story_id}/current-node
```

**Returns:** Current node + available choices + state

**Response:**
```json
{
  "node": {
    "id": "uuid",
    "title": "The Dark Cave",
    "content": "You stand before a dark cave entrance...",
    "is_end_node": false
  },
  "available_choices": [
    {
      "id": "choice-uuid",
      "text": "Light your torch and enter",
      "requires_state": {"has_torch": true},
      "sets_state": {"entered_cave": true}
    }
  ],
  "story_state": {"has_torch": true, "visited_forest": true}
}
```

**Note:** `available_choices` are pre-filtered by `requires_state` logic

#### Make Choice

```http
POST /user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}
```

**Effect (Phase 1-3 Implementation):**
1. Validates choice belongs to current node
2. Validates `requires_state` against `story_state`
3. Creates `UserNodeChoice` record with `parent_choice_id = current head`
4. Updates `head_choice_id` to new choice
5. Increments `head_version`
6. Merges `choice.sets_state` into `progress.story_state`
7. Replays state from head (validation check)
8. Updates `current_node_id` to `choice.to_node_id`
9. If `to_node.is_end_node`, sets `is_completed = true`
10. Publishes `ChoiceMade` event to Redis (Phase 4)

**Errors:**
- `400`: Choice not from current node
- `403`: Choice requirements not met
- `404`: Choice or progress not found

**Returns:** Updated progress

**State Validation:** The endpoint validates that replayed state matches stored state and logs warnings on mismatch.

#### Update Progress (Admin/Debug)

```http
PUT /user-personas/{user_persona_id}/stories/{story_id}
Content-Type: application/json

{
  "current_node_id": "uuid",
  "story_state": {"key": "value"},
  "head_choice_id": "uuid",
  "head_version": 5
}
```

**Use Case:** Debugging, save editing, admin fixes

**Returns:** Updated progress

---

## Timeline Navigation (Phase 3)

### Undo Last Choice

```http
POST /user-personas/{user_persona_id}/stories/{story_id}/undo
```

**Behavior:**
- Moves `head_choice_id` to parent of current head
- Increments `head_version` (optimistic lock)
- Replays state from new head
- Old future choices remain in database but become hidden

**Errors:**
- `400`: Already at story start, cannot undo
- `404`: User persona or story progress not found

**Returns:** Updated progress with new head position

**Example:**
```
Before: Start → A → B → C (head=C, version=3)
After:  Start → A → B (head=B, version=4)
Hidden: C (still in DB, orphaned)
```

**Implementation:** Uses `crud.move_head_to_choice()` helper, publishes `HeadMoved` event to Redis.

### Jump to Ancestor

```http
POST /user-personas/{user_persona_id}/stories/{story_id}/jump
Content-Type: application/json

{
  "choice_id": "uuid-of-ancestor",
  "expected_head_version": 5
}
```

**Validation:**
- Target choice must be ancestor of current head (prevents forward jumps)
- `expected_head_version` must match current version (optimistic concurrency)

**Behavior:**
- Moves `head_choice_id` to target
- Increments `head_version`
- Replays state from target
- All choices after target become hidden

**Errors:**
- `400`: Target not ancestor, or validation error
- `404`: User persona, story progress, or target choice not found
- `409`: Head version conflict (concurrent modification)

**Returns:** Updated progress at new head position

**Example:**
```
Before: Start → A → B → C → D (head=D, version=4)
Jump to A (version=5):
After:  Start → A (head=A, version=5)
Hidden: B, C, D (not in active timeline)
```

**Implementation:** Uses `crud.validate_ancestor_constraint()` to prevent forward jumps.

### Jump to Start

```http
POST /user-personas/{user_persona_id}/stories/{story_id}/jump
Content-Type: application/json

{
  "choice_id": null,
  "expected_head_version": 5
}
```

**Special Case:** `choice_id: null` means jump to story start

**Behavior:**
- Sets `head_choice_id = null`
- Sets `current_node_id` to start node
- Clears `story_state` (replays from empty)
- Increments `head_version`

**Returns:** Updated progress at story start

**Example:**
```
Before: Start → A → B → C (head=C, version=3)
Jump to Start (version=4):
After:  Start (head=null, version=4)
Hidden: A, B, C
```

### Get Timeline (Breadcrumbs)

```http
GET /user-personas/{user_persona_id}/stories/{story_id}/timeline
```

**Returns:** Active timeline (root → head) for breadcrumb UI

**Behavior:**
- Returns ONLY the ancestor chain
- Never includes siblings or abandoned branches
- Ensures abandoned branches remain hidden from player

**Response:**
```json
{
  "events": [
    {
      "choice_id": null,
      "choice_text": "Story Start",
      "node_title": "Awakening",
      "choice_time": "2024-01-10T14:00:00Z",
      "is_current": false
    },
    {
      "choice_id": "uuid-1",
      "choice_text": "Enter forest",
      "node_title": "The Dark Forest",
      "choice_time": "2024-01-10T14:05:00Z",
      "is_current": false
    },
    {
      "choice_id": "uuid-2",
      "choice_text": "Find cave",
      "node_title": "Cave Entrance",
      "choice_time": "2024-01-10T14:10:00Z",
      "is_current": true
    }
  ],
  "head_version": 3
}
```

**Implementation:** Uses `crud.get_choice_ancestor_chain()` to walk parent pointers from head to root.

### Validate State Replay

```http
GET /user-personas/{user_persona_id}/stories/{story_id}/validate-state
```

**Returns:** State validation for debugging

**Response:**
```json
{
  "stored_state": {"torch": true, "cave": true},
  "replayed_state": {"torch": true, "cave": true},
  "match": true,
  "differences": {}
}
```

**Use Case:** Phase 2 diagnostic endpoint to verify replay logic correctness

---

## Common Workflows

### Workflow 1: Author Creates & Publishes Story

```bash
# Step 1: Create story
POST /stories
{
  "title": "The Dark Forest",
  "description": "A spooky adventure"
}
→ story_id, current_version=1, is_published=false

# Step 2: Create start node
POST /storynodes
{
  "story_id": "{story_id}",
  "story_version": 1,
  "title": "Awakening",
  "content": "You wake up in a dark forest...",
  "is_start_node": true
}
→ start_node_id

# Step 3: Create more nodes
POST /storynodes (repeat for each scene)
→ node_2_id, node_3_id, end_node_id

# Step 4: Create choices
⚠️ MANUAL - NO API YET
Must use direct SQL or admin tools:

INSERT INTO nodechoice (id, from_node_id, to_node_id, text, "order", sets_state)
VALUES
  (gen_random_uuid(), '{start_node_id}', '{node_2_id}', 'Go left', 0, '{"path": "left"}'),
  (gen_random_uuid(), '{start_node_id}', '{node_3_id}', 'Go right', 1, '{"path": "right"}'),
  (gen_random_uuid(), '{node_2_id}', '{end_node_id}', 'Continue', 0, '{"completed": true}');

# Step 5: Verify structure
GET /stories/{story_id}/start-node
→ Verify start node exists

# Step 6: Publish
PUT /stories/{story_id}/publish
→ published_version=1, is_published=true
```

### Workflow 2: Player Plays Story (Basic)

```bash
# Step 1: Browse catalog
GET /catalog
→ Find interesting story

# Step 2: Check requirements
GET /catalog/{story_id}/requirements
→ Verify persona meets requirements

# Step 3: Start story
POST /user-personas/{persona_id}/stories/{story_id}
→ progress_id, locked to published_version, head_choice_id=null, head_version=0

# Step 4: Get current position
GET /user-personas/{persona_id}/stories/{story_id}/current-node
→ Start node, available choices, state

# Step 5: Make first choice
POST /user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}
→ head_version=1, head_choice_id=new_choice, state updated

# Step 6: Continue playing
Repeat steps 4-5 until is_completed=true
```

### Workflow 3: Player Uses Timeline Navigation (Phase 3)

```bash
# Scenario: Player made choices A → B → C, wants to explore different path

# Step 1: View current timeline
GET /user-personas/{persona_id}/stories/{story_id}/timeline
→ Shows: Start → A → B → C (current)

# Step 2: Undo last choice (C)
POST /user-personas/{persona_id}/stories/{story_id}/undo
→ head_version=4, back to B
→ C is now hidden (abandoned branch)

# Step 3: Make different choice
POST /user-personas/{persona_id}/stories/{story_id}/choices/{choice_D_id}
→ head_version=5, new path: A → B → D

# Step 4: View updated timeline
GET /user-personas/{persona_id}/stories/{story_id}/timeline
→ Shows: Start → A → B → D (current)
→ C is NOT shown (abandoned)

# Alternative: Jump directly to ancestor
POST /user-personas/{persona_id}/stories/{story_id}/jump
{
  "choice_id": "{choice_A_id}",
  "expected_head_version": 5
}
→ Jump back to A, explore completely different path

# Jump to story start
POST /user-personas/{persona_id}/stories/{story_id}/jump
{
  "choice_id": null,
  "expected_head_version": 6
}
→ Full restart, all previous choices hidden
```

### Workflow 4: Author Updates Published Story

```bash
# Scenario: Story v1 is published, players are active

# Step 1: Create new version
POST /stories/{story_id}/new-version
→ current_version=2, copies all v1 nodes/choices
→ published_version=1 (unchanged)
→ Active players continue on v1

# Step 2: Edit v2 nodes
PUT /storynodes/{node_id}
{
  "content": "Updated narrative..."
}
→ Only affects current_version=2

# Step 3: Publish v2
PUT /stories/{story_id}/publish
→ published_version=2, is_published=true
→ New players lock to v2
→ Existing players stay on v1 (with full timeline navigation)
```

---

## Event Sourcing & State Management

### State Replay Logic

**Function:** `crud.replay_state_from_head()`

```python
def replay_state_from_head(
    *, session: Session, progress_id: UUID, head_choice_id: UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying all events from root to head.

    Algorithm:
    1. If head=null, return {} (at story start)
    2. Get ancestor chain (root → head) via parent pointers
    3. Apply each choice's state_changes in sequence
    4. Return final accumulated state
    """
```

**Example:**
```
Choices:
  A: sets_state = {"torch": true, "score": 10}
  B: sets_state = {"cave": true, "score": 20}
  C: sets_state = {"treasure": true}

Timeline: Start → A → B → C

Replay:
  Start: {}
  After A: {"torch": true, "score": 10}
  After B: {"torch": true, "score": 20, "cave": true}  # score overwritten
  After C: {"torch": true, "score": 20, "cave": true, "treasure": true}
```

**State Merging:** Shallow merge (not deep) - later values overwrite earlier ones.

### Conditional Choices

**Function:** `crud.get_available_choices()`

```python
def get_available_choices(
    *, session: Session, node_id: UUID, story_state: dict | None
) -> list[NodeChoice]:
    """
    Returns choices filtered by requires_state.

    Logic:
    - No requires_state → always available
    - With requires_state → all key-value pairs must match story_state (AND)
    - Missing keys or mismatched values → hidden
    """
```

**Examples:**

#### Simple Requirement
```json
{
  "text": "Use the torch",
  "requires_state": {"has_torch": true}
}
```
**Visible if:** `story_state.has_torch === true`

#### Multiple Requirements (AND Logic)
```json
{
  "text": "Unlock the door",
  "requires_state": {
    "has_key": true,
    "found_door": true
  }
}
```
**Visible if:** BOTH conditions are met

#### No Requirements
```json
{
  "text": "Walk away",
  "requires_state": null
}
```
**Visible:** Always

### Parent Pointer Tree Structure

**Function:** `crud.get_choice_ancestor_chain()`

```python
def get_choice_ancestor_chain(
    *, session: Session, choice_id: UUID
) -> list[UserNodeChoice]:
    """
    Walk parent pointers from choice to root.

    Returns choices in chronological order (root → target).
    Used for timeline display and state replay.
    """
```

**Example:**
```
Database:
  Choice A: parent=null
  Choice B: parent=A
  Choice C: parent=B

get_choice_ancestor_chain(C) → [A, B, C]
```

### Optimistic Concurrency Control

**Field:** `UserStoryProgress.head_version`

**Purpose:** Prevent concurrent timeline modifications from corrupting state

**Pattern:**
```bash
# Client 1: Read progress
GET /stories/{id} → head_version=5

# Client 2: Read progress
GET /stories/{id} → head_version=5

# Client 1: Jump to ancestor
POST /jump {"choice_id": "X", "expected_head_version": 5}
→ SUCCESS, head_version=6

# Client 2: Jump to ancestor (using stale version)
POST /jump {"choice_id": "Y", "expected_head_version": 5}
→ ERROR 409: "Head version conflict: expected 5, got 6. Refetch and retry."
```

**Implementation:** Jump endpoint validates `expected_head_version` matches current before applying mutation.

---

## Development Guide

### Testing Timeline Navigation

```python
# Setup
persona_id = "test-persona-uuid"
story_id = "test-story-uuid"

# Start story
POST /user-personas/{persona_id}/stories/{story_id}
→ head_version=0, head_choice_id=null

# Make choices: A → B → C
POST /choices/{A_id} → head_version=1
POST /choices/{B_id} → head_version=2
POST /choices/{C_id} → head_version=3

# Test undo
POST /undo → head_version=4, back to B
GET /current-node → Should show node B

# Test state replay
GET /validate-state → stored and replayed should match

# Test jump
POST /jump {"choice_id": A_id, "expected_head_version": 4}
→ head_version=5, back to A

# Test timeline
GET /timeline → Should show: Start → A (current)
→ B and C should NOT appear (abandoned)

# Test jump to start
POST /jump {"choice_id": null, "expected_head_version": 5}
→ head_version=6, at start
→ All choices hidden

# Make new choice
POST /choices/{D_id} → head_version=7, new path
GET /timeline → Should show: Start → D (current)
```

### Database Schema Notes

#### Cascading Deletes

```
Story DELETE
  └─> StoryNode CASCADE
       └─> NodeChoice CASCADE
  └─> StoryRequirement CASCADE
  └─> UserStoryProgress (depends on policy - currently cascades)
       └─> UserNodeChoice CASCADE
```

**Warning:** Deleting a published story with active players will cascade-delete their progress (including full timeline history)

#### Self-Referencing Foreign Key

```sql
-- UserNodeChoice.parent_choice_id references UserNodeChoice.id
ALTER TABLE usernodechoice
  ADD CONSTRAINT fk_parent_choice
  FOREIGN KEY (parent_choice_id)
  REFERENCES usernodechoice(id);

-- UserStoryProgress.head_choice_id references UserNodeChoice.id
ALTER TABLE userstoryprogress
  ADD CONSTRAINT fk_head_choice
  FOREIGN KEY (head_choice_id)
  REFERENCES usernodechoice(id);
```

**Implication:** Cannot delete a choice that is someone's head or parent without updating/deleting dependent records first.

#### JSON Columns (JSONB in PostgreSQL)

- `NodeChoice.requires_state` - JSONB
- `NodeChoice.sets_state` - JSONB
- `UserStoryProgress.story_state` - JSONB
- `UserNodeChoice.state_changes` - JSONB
- `UserNodeChoice.rng_data` - JSONB

**Query Example:**
```sql
-- Find choices requiring a torch
SELECT * FROM nodechoice
WHERE requires_state @> '{"has_torch": true}';
```

---

## Known Limitations

### Missing Features (Not Yet Implemented)

#### 1. [RESOLVED] NodeChoice CRUD API 

**Current State:** All REST endpoints implemented

#### 2. [RESOLVED] StoryRequirement CRUD API

**Current State:** All REST endpoints implemented

#### 3. Timeline Visualization

**Missing:** API to get full choice tree (including abandoned branches)

**Use Case:** "Show me all my abandoned timelines for this story"

**Implementation Complexity:** Need graph query to get all descendants from root, mark active vs abandoned

#### 4. Choice Reordering API

**Current:** Must manually set `order` field

**Future:** Drag-and-drop API with automatic reordering

#### 5. Story Cloning

**Missing:** Duplicate a story as starting point for new story

**Use Case:** Template stories, story variants

### Current Constraints

#### 1. Version Locking Behavior ⚠️ KNOWN BUG

**Issue:** `POST /user-personas/{id}/stories/{story_id}` locks to `current_version`, not `published_version`

**Expected:** Should lock to `published_version`

**Impact:** If story is unpublished, players lock to draft version

**Workaround:** Always publish before sharing

**Fix Required:** Update `create_user_story_progress` route (line 178 in user_story_progress.py)

#### 2. Single Start Node Enforcement

**Issue:** Not validated - can create multiple `is_start_node=true` nodes per version

**Impact:** Undefined behavior when starting story

**Best Practice:** Manually ensure only one start node per version

#### 3. No Orphan Node Detection

**Issue:** Nodes without incoming choices (except start node) are not flagged

**Impact:** Unreachable content

**Recommendation:** Build validation tool to detect orphans

#### 4. State Schema-less

**Issue:** No schema validation for `story_state` dict

**Impact:** Typos in state keys can cause logic errors

**Best Practice:** Document state keys in story description

#### 5. Abandoned Branch Garbage Collection

**Issue:** Abandoned choices remain in database forever

**Impact:** Database growth over time for long-running stories with heavy timeline navigation

**Mitigation:** Consider archival strategy for old abandoned branches

#### 6. No Timeline Diff API

**Missing:** Compare timelines between different players or different points in time

**Use Case:** "Show me how my timeline differs from another player's"

### Performance Considerations

#### 1. Deep Timeline Trees

**Scenario:** Player who undoes/explores extensively (100+ abandoned branches)

**Impact:** Slow timeline queries, state replay overhead

**Mitigation:**
- Index on `parent_choice_id` for fast ancestor queries
- Consider caching replayed state at head
- Archive old abandoned branches

#### 2. State Replay Cost

**Scenario:** Very long active timeline (50+ choices)

**Impact:** O(n) state replay on every choice/undo/jump

**Mitigation:**
- Store replayed state in `story_state` (already done)
- Validate replay in background, not on critical path
- Consider incremental replay (cache state at checkpoints)

#### 3. Concurrent Head Moves

**Scenario:** Multiple clients manipulating same progress simultaneously

**Impact:** Race conditions, state corruption

**Mitigation:**
- Optimistic concurrency control via `head_version` (implemented)
- Client must refetch on 409 and retry

---

## Migration from V1

### Breaking Changes

1. **`UserStoryProgress` model**: Added `head_choice_id`, `head_version` fields
2. **`UserNodeChoice` model**: Added `parent_choice_id`, `rng_data` fields
3. **Timeline API**: New endpoints (`/undo`, `/jump`, `/timeline`, `/validate-state`)
4. **State management**: Introduced replay logic

### Migration Path

**Database Migration:**
```sql
-- Add Phase 1-3 fields (Alembic handles this)
ALTER TABLE userstoryprogress
  ADD COLUMN head_choice_id UUID REFERENCES usernodechoice(id),
  ADD COLUMN head_version INT DEFAULT 0;

ALTER TABLE usernodechoice
  ADD COLUMN parent_choice_id UUID REFERENCES usernodechoice(id),
  ADD COLUMN rng_data JSONB;

-- Backfill existing data
UPDATE userstoryprogress SET head_version = 0 WHERE head_version IS NULL;
```

**Code Migration:**
- All V1 endpoints remain compatible (backward compatible)
- New endpoints are opt-in (clients can ignore timeline navigation)
- State replay is validation-only (doesn't break existing flow)

### Recommended Upgrade Process

1. ✅ Apply database migrations
2. ✅ Deploy backend with Phase 1-3 code
3. ✅ Test timeline navigation with new stories
4. ✅ Gradually enable for existing stories
5. 🔄 Update frontend to use timeline UI (optional)

---

## CRUD Functions Reference

Located in `backend/app/crud.py`:

### Story Functions

```python
create_story(session, story_in, owner_id) -> Story
update_story(session, story_id, story_in) -> Story
delete_story(session, story_id) -> Message
```

### StoryNode Functions

```python
create_storynode(session, storynode_in, owner_id) -> StoryNode
# Note: owner_id parameter exists but StoryNode model doesn't have owner_id field
```

### UserStoryProgress Functions

```python
create_user_story_progress(session, progress_in) -> UserStoryProgress
get_user_story_progresses(session, user_persona_id, skip, limit) -> (list, count)
get_user_story_progress(session, user_persona_id, story_id) -> UserStoryProgress | None
update_user_story_progress(session, db_progress, progress_in) -> UserStoryProgress
```

### Choice & State Functions

```python
get_available_choices(session, node_id, story_state) -> list[NodeChoice]
# Filters choices by requires_state logic (AND semantics)
```

### Timeline Navigation Functions (Phase 1-3)

```python
get_choice_ancestor_chain(session, choice_id) -> list[UserNodeChoice]
# Walk parent pointers from choice to root

get_current_node_from_head(session, progress_id, head_choice_id) -> StoryNode
# Get node at head position

get_choice_children(session, parent_choice_id) -> list[UserNodeChoice]
# Get all direct children of a choice (for analytics)

move_head_to_choice(session, progress, target_choice_id) -> UserStoryProgress
# Move head to target, replay state, increment head_version

replay_state_from_head(session, progress_id, head_choice_id) -> dict
# Reconstruct state by replaying events from root to head

validate_ancestor_constraint(session, target_choice_id, current_head_id) -> bool
# Verify target is ancestor of current head (prevents forward jumps)
```

### Requirement Functions

```python
create_story_requirement(session, requirement_in) -> StoryRequirement
get_story_requirements(session, story_id, skip, limit) -> (list, count)
check_story_requirements(session, user_persona_id, story_id) -> bool
# Validates persona has required qualities/traits
```

---

## Best Practices

### For Authors

1. **Create exactly one `is_start_node=true` per version**
2. **Use `order` field** to control choice display sequence
3. **Document state keys** in story description (no schema validation)
4. **Test timeline navigation** before publishing (undo/jump)
5. **Use descriptive node titles** (visible in timeline breadcrumbs)
6. **Create new version** before editing published stories
7. **Set meaningful `sets_state`** for achievement tracking

### For Players

1. **Use timeline navigation** to explore different story paths
2. **Check `available_choices`** - conditional choices may be hidden
3. **Watch `head_version`** when using concurrent clients
4. **Review timeline** to see current active path
5. **Abandoned branches are hidden** but exist in database (for analytics)

### For Developers

1. **Version lock happens at progress creation** (immutable after)
2. **State replay is source of truth** (not stored state)
3. **Parent pointers form DAG** (directed acyclic graph)
4. **Head version prevents race conditions** (optimistic locking)
5. **Abandoned branches stay in DB** (never deleted)
6. **Timeline queries walk parent pointers** (O(n) where n=depth)
7. **All head moves increment version** (choice/undo/jump)
8. **Replayed state must match stored** (validation check)

---

## Future Roadmap

### Short-Term (Next Sprint)

- [X] Implement NodeChoice CRUD API (**CRITICAL**)
- [X] Implement StoryRequirement CRUD API
- [ ] Fix version locking bug (lock to published_version)
- [ ] Add single start node validation

### Medium-Term (Phase 4)

- [x] Real-time event publishing (Redis) ✅
- [x] WebSocket story updates ✅
- [ ] Multi-player story support
- [ ] Timeline visualization API
- [ ] Abandoned branch analytics

### Long-Term

- [ ] Story cloning API
- [ ] Visual story editor integration
- [ ] Advanced state logic (OR, NOT, numeric comparisons)
- [ ] Story analytics (completion rates, popular paths, undo patterns)
- [ ] Timeline diff API (compare player timelines)
- [ ] Checkpoint system (mark states for easy return)

---

## Error Codes Reference

### 400 Bad Request

- Not enough permissions (non-owner/non-superuser)
- Progress already exists for this story
- Choice not from current node
- No current node in progress
- Cannot create new version (never published)
- Already at story start, cannot undo
- Target choice not ancestor of head (forward jump attempt)

### 403 Forbidden

- User persona doesn't meet story requirements
- Choice requirements not met in story state

### 404 Not Found

- Story not found
- StoryNode not found
- NodeChoice not found
- UserPersona not found
- UserStoryProgress not found
- Start node not found
- Published story not found (catalog)
- Target choice not found (jump)

### 409 Conflict

- Head version conflict (concurrent modification)
- Expected head_version doesn't match current

### 500 Internal Server Error

- No start node found for story version (data integrity issue)
- Head choice not found (data corruption)

---

**End of Documentation**

For questions or issues, contact the backend team or file an issue in the project repository.

**Related Documentation:**
- `EVENT_SYSTEMS_ALIGNMENT.md` - Room vs Story event patterns
- `test_story_system.py` - Automated test suite for Phase 1-3
- `STORY_TEST_SUITE.md` - Test suite usage guide
