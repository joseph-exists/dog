# Story System Documentation

**Last Updated:** 2026-01-01
**Status:** ✅ Production Ready
**Source of Truth:** This document reflects the actual backend implementation

---

## Table of Contents

1. [Overview & Philosophy](#overview--philosophy)
2. [Architecture](#architecture)
3. [Data Models](#data-models)
4. [API Reference](#api-reference)
5. [Common Workflows](#common-workflows)
6. [State Management](#state-management)
7. [Development Guide](#development-guide)
8. [Known Limitations](#known-limitations)

---

## Overview & Philosophy

The Story System implements **versioned, template-based interactive narratives** with three distinct concerns:

### Core Principles

1. **Stories are Templates**: Authors create story templates that can be played by many users
2. **Version Locking**: When a player starts a story, they lock to a specific version - never experiencing mid-game changes
3. **State Accumulation**: Player state grows through choices, enabling branching narratives
4. **Reference-Based**: Players reference story nodes; no data duplication
5. **Three Namespaces**: Clear separation between authoring, discovering, and playing stories

### The Three Namespaces

```
┌─────────────────┐
│   AUTHORING     │ /stories         → Story creators draft, version, publish
├─────────────────┤
│   DISCOVERY     │ /catalog         → Users browse published stories
├─────────────────┤
│   PLAYING       │ /user-personas/  → Players navigate locked story instances
│                 │ {id}/stories
└─────────────────┘
```

---

## Architecture

### Versioning System

```
Story (version 1, draft)  ──┐
                            │── Author publishes
                            ↓
Story (version 1, published) → Players lock to v1
Story (version 2, draft)     → Author continues editing

Player A: Locked to v1 ─→ Always plays v1
Player B: Locked to v1 ─→ Always plays v1
```

**Version Fields:**
- `current_version` (int): What authors are currently editing (mutable draft)
- `published_version` (int | null): What's visible in catalog (locked)
- `is_published` (bool): Whether story appears in catalog

**Publishing Flow:**
1. Author creates story (v1, unpublished)
2. Author publishes → `published_version = 1`, `is_published = true`
3. Players start story → locked to `published_version = 1`
4. Author creates new version → `current_version = 2` (copies v1 nodes/choices)
5. Author edits v2, publishes → `published_version = 2`
6. Existing players continue on v1, new players lock to v2

### State Accumulation Pattern

```
Player starts → story_state = {}
               ↓
Player chooses "Pick up torch" (sets_state: {has_torch: true})
               ↓
story_state = {has_torch: true}
               ↓
Player sees "Enter cave" choice (requires_state: {has_torch: true}) ✓ Available
Player sees "Enter cave without light" (no requires_state) ✓ Available
Player sees "Use magic" (requires_state: {has_magic: true}) ✗ Hidden
```

**Key Behaviors:**
- `story_state` is a JSON dict in `UserStoryProgress`
- `NodeChoice.sets_state` merges into `story_state` when chosen
- `NodeChoice.requires_state` gates choice visibility (AND logic)
- State is shallow-merged (not deep)

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
    node_type: str              # "text", "image", "choice", etc. (default: "text")

    is_start_node: bool         # One per story_version (default: False)
    is_end_node: bool           # Can have multiple ends (default: False)

    created_at: datetime
    updated_at: datetime
```

**Relationships:**
- `story: Story`
- `choices_from: list[NodeChoice]` - Decisions leaving this node
- `choices_to: list[NodeChoice]` - Decisions arriving at this node
- `current_for_progresses: list[UserStoryProgress]` - Players currently here

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

### UserStoryProgress (Player Instance)

```python
class UserStoryProgress:
    id: UUID
    user_persona_id: UUID       # Player identity
    story_id: UUID              # Which story template
    story_version: int          # Locked at creation (immutable!)

    current_node_id: UUID | None  # Where player is now
    is_completed: bool          # Reached an end node (default: False)

    # State accumulator (JSON dict)
    story_state: dict[str, Any] | None  # Game variables

    started_at: datetime
    updated_at: datetime
```

**Relationships:**
- `user_persona: UserPersona`
- `story: Story`
- `current_node: StoryNode` - Current position (references template)
- `choice_history: list[UserNodeChoice]` - Breadcrumb trail

### UserNodeChoice (Decision History)

```python
class UserNodeChoice:
    id: UUID
    progress_id: UUID           # Which playthrough

    choice_text: str            # What the player chose
    from_node_id: UUID          # Where they were
    to_node_id: UUID            # Where they went

    state_changes: dict[str, Any] | None  # Snapshot of sets_state applied
    choice_time: datetime
```

**Purpose:** Immutable audit trail for replays, achievements, analytics

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

### DISCOVERY Namespace: `/catalog`

**Who:** All users browsing for stories
**Access:** Public (with optional requirement gating)

#### Browse Catalog

```http
GET /catalog?skip=0&limit=10
```

**Returns:** Published stories (`is_published=true` only)

**Response:** Same format as `GET /stories`

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

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "story_id": "uuid",
      "story_version": 1,
      "title": "Chapter 1: The Forest",
      "content": "You wake up in a dark forest...",
      "node_type": "text",
      "is_start_node": true,
      "is_end_node": false,
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 15
}
```

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

**Response:**
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

**Returns:** Player's instance of this story (version lock, state, position)

#### Start Story

```http
POST /user-personas/{user_persona_id}/stories/{story_id}
```

**Effect:**
1. Validates persona meets story requirements
2. Creates `UserStoryProgress` locked to `story.current_version`
3. Sets `current_node_id` to story's start node
4. Initializes `story_state = {}`

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
    "story_id": "uuid",
    "story_version": 1,
    "title": "The Dark Cave",
    "content": "You stand before a dark cave entrance...",
    "node_type": "text",
    "is_start_node": false,
    "is_end_node": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  },
  "available_choices": [
    {
      "id": "choice-uuid",
      "from_node_id": "current-node-uuid",
      "to_node_id": "cave-interior-uuid",
      "text": "Light your torch and enter",
      "order": 1,
      "requires_state": {"has_torch": true},
      "sets_state": {"entered_cave": true}
    },
    {
      "id": "choice-uuid-2",
      "from_node_id": "current-node-uuid",
      "to_node_id": "return-path-uuid",
      "text": "Return to the village",
      "order": 2,
      "requires_state": null,
      "sets_state": {"returned_to_village": true}
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

**Effect:**
1. Validates choice belongs to current node
2. Validates `requires_state` against `story_state`
3. Creates `UserNodeChoice` record (history)
4. Merges `choice.sets_state` into `progress.story_state`
5. Updates `current_node_id` to `choice.to_node_id`
6. If `to_node.is_end_node`, sets `is_completed = true`

**Errors:**
- `400`: Choice not from current node
- `403`: Choice requirements not met
- `404`: Choice or progress not found

**Returns:** Updated progress

#### Update Progress (Admin/Debug)

```http
PUT /user-personas/{user_persona_id}/stories/{story_id}
Content-Type: application/json

{
  "current_node_id": "uuid",
  "story_state": {"key": "value"}
}
```

**Use Case:** Debugging, save editing, admin fixes

**Returns:** Updated progress

---

### NODE MANAGEMENT Namespace: `/storynodes`

**Who:** Authors (currently superuser only for updates/deletes)
**Access:** Authenticated users (create), superuser (update/delete)

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
POST /storynodes (repeat)
→ node_2_id, node_3_id, etc.

# Step 4: Create choices (MANUAL - NO API YET)
# Currently requires direct database insertion or SQL
# Future: POST /storynodes/{node_id}/choices

# Step 5: Verify structure
GET /stories/{story_id}/start-node
→ Verify start node exists

# Step 6: Publish
PUT /stories/{story_id}/publish
→ published_version=1, is_published=true
```

### Workflow 2: Player Plays Story

```bash
# Step 1: Browse catalog
GET /catalog
→ Find interesting story

# Step 2: Check requirements
GET /catalog/{story_id}/requirements
→ Verify persona meets requirements

# Step 3: Start story
POST /user-personas/{persona_id}/stories/{story_id}
→ progress_id, locked to published_version

# Step 4: Get current position
GET /user-personas/{persona_id}/stories/{story_id}/current-node
→ Current node, available choices, state

# Step 5: Make choice
POST /user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}
→ State updated, moved to next node

# Step 6: Repeat steps 4-5 until is_completed=true
```

### Workflow 3: Author Updates Published Story

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
→ Existing players stay on v1
```

---

## State Management

### Conditional Choices

#### Simple Requirement

```json
{
  "text": "Use the torch",
  "requires_state": {"has_torch": true}
}
```

**Behavior:** Only visible if `story_state.has_torch === true`

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

**Behavior:** Visible only if **both** conditions are met

#### No Requirements

```json
{
  "text": "Walk away",
  "requires_state": null
}
```

**Behavior:** Always visible

### State Changes

#### Simple Flag

```json
{
  "text": "Pick up the torch",
  "sets_state": {"has_torch": true}
}
```

**Effect:** `story_state` becomes `{...existing, has_torch: true}`

#### Multiple Changes

```json
{
  "text": "Drink the potion",
  "sets_state": {
    "has_potion": false,
    "health": 100,
    "status": "healed"
  }
}
```

**Effect:** Shallow merge into `story_state`

#### Combining Requires & Sets

```json
{
  "text": "Use key on door",
  "requires_state": {"has_key": true, "at_door": true},
  "sets_state": {"door_unlocked": true, "has_key": false}
}
```

**Flow:**
1. Check player has key and is at door
2. If yes, show choice
3. Player chooses → key consumed, door unlocked

### State Filtering Logic (CRUD Function)

```python
def get_available_choices(
    *, session: Session, node_id: UUID, story_state: dict | None
) -> list[NodeChoice]:
    """
    Returns choices filtered by requires_state.

    Logic:
    - No requires_state → always available
    - With requires_state → all key-value pairs must match story_state
    - Missing keys or mismatched values → hidden
    """
    choices = session.exec(select(NodeChoice).where(
        NodeChoice.from_node_id == node_id
    )).all()

    if not story_state:
        return [c for c in choices if not c.requires_state]

    available = []
    for choice in choices:
        if not choice.requires_state:
            available.append(choice)
            continue

        # Check all requirements
        if all(
            key in story_state and story_state[key] == value
            for key, value in choice.requires_state.items()
        ):
            available.append(choice)

    return available
```

---

## Development Guide

### Adding a New Story

1. **Create Story**
   ```python
   POST /stories {"title": "...", "description": "..."}
   ```

2. **Create Nodes** (for `current_version`)
   ```python
   POST /storynodes {
       "story_id": "...",
       "story_version": 1,  # Match current_version
       "title": "...",
       "content": "...",
       "is_start_node": true  # At least one!
   }
   ```

3. **Create Choices** (⚠️ NO API YET - Use SQL or wait for implementation)
   ```sql
   INSERT INTO nodechoice (id, from_node_id, to_node_id, text, "order")
   VALUES (gen_random_uuid(), '...', '...', 'Enter cave', 0);
   ```

4. **Validate**
   ```python
   GET /stories/{story_id}/start-node  # Verify start node exists
   ```

5. **Publish**
   ```python
   PUT /stories/{story_id}/publish
   ```

### Testing a Story

```python
# Start as test player
POST /user-personas/{test_persona_id}/stories/{story_id}

# Navigate
GET /user-personas/{test_persona_id}/stories/{story_id}/current-node
POST /user-personas/{test_persona_id}/stories/{story_id}/choices/{choice_id}

# Check state accumulation
# Verify conditional choices appear/disappear correctly
# Test end node detection (is_completed=true)
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

**Warning:** Deleting a published story with active players will cascade-delete their progress

#### Indexes

Recommended (not all implemented yet):
- `StoryNode(story_id, story_version)` - Fast version queries
- `NodeChoice(from_node_id)` - Fast choice lookups
- `UserStoryProgress(user_persona_id, story_id)` - Unique per player
- `UserNodeChoice(progress_id)` - Fast history queries

#### JSON Columns

- `NodeChoice.requires_state` - JSONB in PostgreSQL
- `NodeChoice.sets_state` - JSONB in PostgreSQL
- `UserStoryProgress.story_state` - JSONB in PostgreSQL
- `UserNodeChoice.state_changes` - JSONB in PostgreSQL

**Query Example:**
```sql
-- Find choices requiring a torch
SELECT * FROM nodechoice
WHERE requires_state @> '{"has_torch": true}';
```

---

## Known Limitations

### Missing Features (Not Yet Implemented)

#### 1. NodeChoice CRUD API

**Current State:** No REST endpoints for managing choices

**Workaround:** Direct database insertion

**Future Implementation Needed:**
```http
POST   /storynodes/{node_id}/choices
GET    /storynodes/{node_id}/choices
PUT    /storynodes/{node_id}/choices/{choice_id}
DELETE /storynodes/{node_id}/choices/{choice_id}
```

**Impact:** Authors must use SQL or admin tools to create story branches

#### 2. StoryRequirement CRUD API

**Current State:** No REST endpoints for managing requirements

**Workaround:** Direct database insertion

**Future Implementation Needed:**
```http
POST   /stories/{story_id}/requirements
GET    /stories/{story_id}/requirements
DELETE /stories/{story_id}/requirements/{requirement_id}
```

**Impact:** Story access gating must be configured via database

#### 3. Version Comparison

**Missing:** API to compare nodes/choices between versions

**Use Case:** "Show me what changed between v1 and v2"

#### 4. Story Cloning

**Missing:** Duplicate a story as starting point for new story

**Use Case:** Template stories, story variants

#### 5. Choice Reordering

**Current:** Must manually set `order` field

**Future:** Drag-and-drop API with automatic reordering

#### 6. Story Preview Mode

**Missing:** Test story without creating progress record

**Use Case:** Author testing during development

### Current Constraints

#### 1. Version Locking Behavior

**Issue:** `POST /user-personas/{id}/stories/{story_id}` locks to `current_version`, not `published_version`

**Expected:** Should lock to `published_version`

**Impact:** If story is unpublished, players lock to draft version

**Workaround:** Always publish before sharing

#### 2. No Version History UI

**Issue:** Can't see list of all versions for a story

**Impact:** Hard to audit version changes over time

#### 3. Single Start Node Enforcement

**Issue:** Not validated - can create multiple `is_start_node=true` nodes

**Impact:** Undefined behavior when starting story

**Best Practice:** Manually ensure only one start node per version

#### 4. No Orphan Node Detection

**Issue:** Nodes without incoming choices (except start node) are not flagged

**Impact:** Unreachable content

**Recommendation:** Build validation tool to detect orphans

#### 5. State Schema-less

**Issue:** No schema validation for `story_state` dict

**Impact:** Typos in state keys can cause logic errors

**Best Practice:** Document state keys in story description

### Performance Considerations

#### 1. Large Story State

**Scenario:** Story with 100+ state variables

**Impact:** JSON serialization overhead

**Mitigation:** Limit state to essential variables, archive old state to history

#### 2. Deep Story Trees

**Scenario:** Story with 1000+ nodes

**Impact:** Slow catalog preview (`GET /catalog/{id}/nodes`)

**Mitigation:** Add pagination, consider lazy loading

#### 3. Many Active Players

**Scenario:** 10,000+ concurrent players in same story

**Impact:** Hot node queries (same nodes accessed repeatedly)

**Mitigation:** Add caching layer for `StoryNode` reads

---

## Error Codes Reference

### 400 Bad Request

- Not enough permissions (non-owner/non-superuser)
- Progress already exists for this story
- Choice not from current node
- No current node in progress
- Cannot create new version (never published)

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

### 500 Internal Server Error

- No start node found for story version (data integrity issue)

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

### Requirement Functions

```python
create_story_requirement(session, requirement_in) -> StoryRequirement
get_story_requirements(session, story_id, skip, limit) -> (list, count)
check_story_requirements(session, user_persona_id, story_id) -> bool
# Validates persona has required qualities/traits
```

### UserPersona Functions

```python
create_user_persona(session, user_persona_in, user_id) -> UserPersona
get_user_personas(session, user_id, skip, limit) -> (list, count)
get_user_persona(session, id, user_id) -> UserPersona | None
update_user_persona(session, db_user_persona, user_persona_in) -> UserPersona
delete_user_persona(session, db_user_persona) -> None
```

---

## Best Practices

### For Authors

1. **Always create one `is_start_node=true` per version**
2. **Use `order` field** to control choice display sequence
3. **Document state keys** in story description or external docs
4. **Test story paths** before publishing
5. **Use descriptive node titles** (shown in history/debugging)
6. **Create new version** before editing published stories

### For Players

1. **Check `available_choices`** - don't assume all choices are available
2. **Watch `is_completed` flag** when reaching story end
3. **`story_state` is your save game** - accumulated over entire playthrough

### For Developers

1. **Version lock happens at progress creation** (immutable after)
2. **State merging is shallow** (not deep merge)
3. **Choice filtering happens in `get_available_choices()`** (AND logic)
4. **All operations validate permissions** (owner or superuser)
5. **Cascade deletes handle cleanup** automatically
6. **Use transactions** when creating nodes + choices together
7. **Test with multiple versions** to verify isolation

---

## Future Roadmap

### Short-Term (Next Sprint)

- [ ] Implement NodeChoice CRUD API
- [ ] Implement StoryRequirement CRUD API
- [ ] Fix version locking bug (lock to published_version, not current_version)
- [ ] Add single start node validation

### Medium-Term

- [ ] Story preview mode (test without creating progress)
- [ ] Version comparison API
- [ ] Orphan node detection tool
- [ ] State schema validation (optional)

### Long-Term

- [ ] Story cloning API
- [ ] Visual story editor integration
- [ ] Advanced state logic (OR, NOT, numeric comparisons)
- [ ] Story analytics (completion rates, popular paths)
- [ ] Multiplayer story support

---

## Appendix: Model Relationships Diagram

```
Story
 ├─> StoryNode (1:many)
 │    ├─> NodeChoice (from_node, 1:many)
 │    └─> NodeChoice (to_node, 1:many)
 ├─> StoryRequirement (1:many)
 └─> UserStoryProgress (1:many)
      ├─> UserNodeChoice (1:many)
      └─> StoryNode (current_node, many:1)

UserPersona
 └─> UserStoryProgress (1:many)

Quality/Trait
 └─> StoryRequirement (1:many)
```

---

**End of Documentation**

For questions or issues, contact the backend team or file an issue in the project repository.
