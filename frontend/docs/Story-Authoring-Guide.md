# Story Authoring UI Implementation Guide

**Version:** 1.2
**Date:** 2026-01-07
**Status:** Still in Review.
**Backend Status:** ✅ All APIs, services, auth, and infra: Implemented and Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Understanding the Story System](#understanding-the-story-system)
3. [API Reference by Use Case](#api-reference-by-use-case)
4. [UI/UX Requirements](#uiux-requirements)
5. [Implementation Patterns](#implementation-patterns)
6. [Testing Strategy](#testing-strategy)
7. [Complete API Reference](#complete-api-reference)
8. [Data Model Reference](#data-model-reference)
9. [Common Recipes](#common-recipes)

---

## Executive Summary

### What You're Building

You're building a **Story Authoring UI** that enables authors to create, edit, and publish interactive Choose-Your-Own-Adventure (CYOA) stories with:

- **Branching narratives** with multiple nodes and choices
- **Conditional logic** (choices appear based on player state)
- **State management** (items, directions, equipment tracked as story progresses)
- **Version control** (authors can edit published stories without affecting active players)
- **Timeline navigation** (players can undo and explore different paths - Phase 3 feature)

### Why This Matters

This is the **author-facing tooling** that transforms TinyFoot from a story player into a story creation platform. Authors need an intuitive, powerful interface to:

1. Design complex branching stories
2. Test their narratives before publishing
3. Update published stories safely
4. Visualize story structure and flow

### What's Ready

✅ **All backend APIs are implemented** (as of 2025-12-28)
✅ **All CRUD operations available** for stories, nodes, and choices
✅ **Publishing workflow complete** with version management
✅ **Timeline navigation features** (undo/jump) implemented
✅ **OpenAPI client has been regenerated** from latest spec

### What You Need to Do

**Core Features (MVP)**:
1. [x] Regenerate API client from OpenAPI spec
2. Build Story List view (authoring context)
3. Build Story Editor with node/choice management
4. Implement Publish/Unpublish workflow
5. Add story structure visualization

**Future Enhancements**:
- Visual story graph editor
- Timeline navigation UI (Phase 3 integration)
- Catalog browser (discovery context)
- Test mode for authors

---

## Understanding the Story System

### The Three Namespaces

The story system operates in **three distinct contexts** with separate APIs and purposes:

```
┌─────────────────────────────────────────────────────────────────┐
│                        STORY LIFECYCLE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. AUTHORING (/stories)                                        │
│     ↓                                                           │
│     Purpose: Create and edit stories                            │
│     Users: Story authors (owners)                               │
│     State: Mutable (current_version)                            │
│     UI: "My Stories" / Story Editor                             │
│                                                                 │
│  2. DISCOVERY (/catalog)                                        │
│     ↓                                                           │
│     Purpose: Browse published stories                           │
│     Users: All users (public/gated)                             │
│     State: Immutable (published_version)                        │
│     UI: "Browse Catalog" / Story Preview                        │
│                                                                 │
│  3. PLAYING (/user-personas/{id}/stories)                       │
│     ↓                                                           │
│     Purpose: Experience interactive stories                     │
│     Users: Players (persona owners)                             │
│     State: Per-player instance with timeline                    │
│     UI: "My Adventures" / Story Player                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**For this guide, focus on AUTHORING namespace** - the Story Editor UI.

### Mental Model: Stories as Versioned Templates

Think of stories as **code repositories with versions**:

```typescript
// Story = Repository with branches
Story {
  id: UUID                           // Unique story identifier
  title: "The Dark Forest"           // Story name
  current_version: 2                 // Working draft (like "main" branch)
  published_version: 1               // Production release (like "v1.0.0" tag)
  is_published: true                 // Visible in catalog?
}

// StoryNode = Scenes/chapters that belong to specific versions
StoryNode {
  id: UUID
  story_id: UUID                     // Which story?
  story_version: 1                   // Which version? (CRITICAL!)
  title: "Forest Entrance"
  content: "You stand before a dark forest..."
  is_start_node: true                // Entry point for this version
  is_end_node: false                 // Ending for this version
}

// NodeChoice = Branching decisions - a player can move from StoryNode X to StoryNode Y, Z, or ... - a NodeChoice is the path that they can take from a StoryNode. StoryNode X may have multiple NodeChoices that have the same destination, but with different state changes.
NodeChoice {
  id: UUID
  from_node_id: UUID                 // Origin node
  to_node_id: UUID                   // Destination node
  text: "Enter the forest"           // Choice text shown to player
  order: 0                           // Display order
  requires_state: { has_torch: true } // Conditional visibility
  sets_state: { entered_forest: true } // State changes when chosen
}
```

**Key Concepts**:

1. **current_version**: The author's workspace (editable)
2. **published_version**: What players see (immutable once published)
3. **story_version field on nodes**: Nodes belong to specific versions
4. **Version locking**: Players lock to published_version when they start

### Versioning Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                    AUTHORING WORKFLOW                          │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  1. Create Story                                               │
│     POST /stories { title, description }                       │
│     → current_version = 1, is_published = false                │
│                                                                │
│  2. Add Nodes & Choices                                        │
│     POST /storynodes { story_id, story_version: 1, ... }       │
│     (Choices created via direct SQL - see recipes)             │
│                                                                │
│  3. Publish Story                                              │
│     PUT /stories/{id}/publish                                  │
│     → published_version = 1, is_published = true               │
│     → Story appears in /catalog                                │
│     → Players can start story (lock to version 1)              │
│                                                                │
│  4. Create New Version (to edit published story)               │
│     POST /stories/{id}/new-version                             │
│     → current_version = 2                                      │
│     → Copies all v1 nodes/choices to v2                        │
│     → published_version = 1 (unchanged)                        │
│     → Existing players continue on v1                          │
│                                                                │
│  5. Edit Version 2                                             │
│     PUT /storynodes/{node_id} { content: "Updated..." }        │
│     → Only affects story_version = 2 nodes                     │
│                                                                │
│  6. Publish Version 2                                          │
│     PUT /stories/{id}/publish                                  │
│     → published_version = 2                                    │
│     → New players lock to v2                                   │
│     → Existing players stay on v1                              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### State Accumulation Pattern

Stories track player state as a **JSON dictionary that grows through choices**:


```typescript
// Player starts story
UserStoryProgress {
  story_state: {}  // Empty at start
}

// Player chooses "Pick up torch"
NodeChoice {
  text: "Pick up torch",
  sets_state: { has_torch: true, torch_fuel: 100 }
}
// After choice:
UserStoryProgress {
  story_state: { has_torch: true, torch_fuel: 100 }
}

// Player chooses "Enter cave"
NodeChoice {
  text: "Enter dark cave",
  requires_state: { has_torch: true },  // Only visible if has torch
  sets_state: { in_cave: true, torch_fuel: 80 }
}
// After choice:
UserStoryProgress {
  story_state: { has_torch: true, torch_fuel: 80, in_cave: true }
}
```

**State Design Principles**:
- **Shallow merge**: New state merges into existing (later values overwrite)
- **Conditional choices**: `requires_state` uses AND logic (all conditions must match)
- **No schema**: State keys are freeform strings (document in story description)
- **Use cases**: Items, locations, flags, counters, any game state

### Timeline Navigation (Phase 3 - Future Enhancement)

Players can **undo choices and explore different paths**:

```
Timeline Example:
  Start → Choice A → Choice B → Choice C (current)
                  └→ [ABANDONED] Choice D

Player can:
- Undo to B (C becomes abandoned)
- Jump to A (B and C become abandoned)
- Jump to Start (all choices abandoned)
- Make new choice from any ancestor point
```

**Frontend Impact**: 
This will be a very near-term upcoming frontend enhancement. 
For MVP Story Editor, just know:
- Choices form a tree structure (not linear sequence)
- Backend preserves abandoned branches for analytics
- Players see only active timeline (root → head)

---

## Use Cases

### Use Case 1: List Author's Stories

**Service**: `import StoriesService from /src/client, import readStories from StoriesService`

**Purpose**: Show "My Stories" list in authoring UI

**Request**:


**Response**:
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

**UI Display**:
- Show title, description
- Badge: "Published v1" (if is_published)
- Badge: "Draft v2" (if current_version > published_version)
- Actions: Edit, Publish, Delete

---

### Use Case 2: Create New Story

**Endpoint**: `import createStory from StoriesService`

**Purpose**: Author creates new story draft

**Request**:

requires title and and description.

**Response**:
```json
{
  "id": "uuid",
  "title": "My Adventure",
  "description": "An epic tale of adventure",
  "current_version": 1,
  "published_version": null,
  "is_published": false,
  "owner_id": "current-user-uuid",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:00:00Z"
}
```

**Important**: Do NOT send `current_version` in body - it's set automatically by database.

---

### Use Case 3: Get Story Details

**Endpoint**: `readStory from StoryService`

**Purpose**: Load story for review and potential editing

**Next Steps**: After loading story, fetch nodes for `current_version`

---

### Use Case 4: Create Story Node



### Use Case 5: Update Story Node


**Purpose**: Edit existing node content


---

### Use Case 6: List Nodes for Story


**Purpose**: Get all nodes for current editing version




---

### Use Case 7: Create Choices Between Nodes

**Purpose**: Enable Pathing by players when there is a branch.

---

### Use Case 8: Publish Story to Catalog


**Purpose**: Make story visible in catalog, lock version for players


**Effect**:
- Sets `published_version = current_version`
- Sets `is_published = true`
- Story appears in `/catalog`
- Players can start story (lock to published_version)

**Validation**: Backend verifies story has valid start node before publishing

**Response**: Updated story object with new published_version

---

### Use Case 9: Unpublish Story


**Purpose**: Hide story from catalog (but keep for existing players)


**Effect**:
- Sets `is_published = false`
- Keeps `published_version` intact
- Hides from `/catalog`
- Existing players continue on their locked version

---

### Use Case 10: Create New Version (Edit Published Story)


**Purpose**: Increment version to edit published story without affecting players


**Effect**:
1. Increments `current_version` (e.g., 1 → 2)
2. Copies all nodes from `published_version` to new `current_version`
3. Copies all choices, remapping node IDs
4. `published_version` remains locked
5. Author can now edit v2 without affecting v1 players

**Requires**: Story must have been published at least once

**Response**: Updated story with new current_version

**Workflow**:
```
Story v1 published → Players active on v1
       ↓
Create new version → current_version = 2
       ↓
Edit v2 nodes → Only v2 affected
       ↓
Publish v2 → New players get v2, existing stay on v1
```

---

## UI/UX Requirements

### Story List View ("My Stories")


**Layout**:
```
┌────────────────────────────────────────────────────────────┐
│  My Stories                                    [+ New]     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ The Dark Forest                     Published v1  📘│ │
│  │ A spooky adventure                  Draft v2      ✏️│ │
│  │                                                      │ │
│  │ Last updated: 2 days ago                            │ │
│  │ [Edit] [Publish v2] [Unpublish] [Delete]            │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ Lost in Time                        Draft v1      ✏️│ │
│  │ A time travel mystery                               │ │
│  │                                                      │ │
│  │ Last updated: 1 week ago                            │ │
│  │ [Edit] [Publish] [Delete]                           │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

**Features**:
- List all user's stories (GET /stories)
- Show publish status badges
- Show version info (current vs published)
- Actions: Edit, Publish/Unpublish, Delete
- [+ New] button → Create story modal

**Status Badges**:
- `is_published = true` → "Published v{published_version}" (blue)
- `is_published = false` → "Draft v{current_version}" (gray)
- `current_version > published_version` → "Draft v{current_version}" (orange) - indicates unpublished changes

---

### Story Editor (Main Interface)


**Layout** (Three-panel design):

```
┌─────────────────────────────────────────────────────────────────┐
│  The Dark Forest (v2 - Draft)              [Publish] [Preview]  │
├──────────────┬──────────────────────────────────┬───────────────┤
│              │                                  │               │
│  Node Tree   │         Node Editor              │  Properties   │
│  (Left)      │         (Center)                 │  (Right)      │
│              │                                  │               │
│  📄 Start    │  Title: Forest Entrance          │  Story Info   │
│  │           │                                  │  Version: 2   │
│  ├─ Node 1   │  Content:                        │  Status: Draft│
│  │  ├─ A     │  ┌────────────────────────────┐ │               │
│  │  └─ B     │  │ You stand before a dark    │ │  Node Stats   │
│  │           │  │ forest. The trees loom     │ │  Total: 12    │
│  └─ Node 2   │  │ overhead...                │ │  Orphaned: 0  │
│     └─ End   │  │                            │ │               │
│              │  └────────────────────────────┘ │  Actions      │
│  [+ Node]    │                                  │  [New Version]│
│              │  Choices from this node:         │  [Delete]     │
│              │  ┌────────────────────────────┐ │               │
│              │  │ → Enter forest             │ │               │
│              │  │   Target: Node 1           │ │               │
│              │  │   State: entered = true    │ │               │
│              │  │   [Edit] [Delete]          │ │               │
│              │  └────────────────────────────┘ │               │
│              │  [+ Add Choice]                  │               │
│              │                                  │               │
└──────────────┴──────────────────────────────────┴───────────────┘
```

**Left Panel: Node Tree**
- Hierarchical view of story structure
- Start node at top (marked with icon)
- Indentation shows branching
- Click to select node for editing
- Drag to reorder (future)
- [+ Node] button to add new node

**Center Panel: Node Editor**
- Title input
- Content textarea (rich text future)
- Choice list for selected node
- Add/edit/delete choices
- Preview mode toggle

**Right Panel: Properties**
- Story metadata
- Version info
- Node statistics
- Bulk actions
- Validation warnings

---

### Node Editor Details

**Node Form Fields**:

```typescript
interface NodeEditorForm {
  title: string;              // Required, max 200 chars
  content: string;            // Required, max 10000 chars
  node_type: "text" | "image" | "choice";  // Default "text"
  is_start_node: boolean;     // Only one per version!
  is_end_node: boolean;       // Can have multiple
}
```

**Validation Rules**:
- Title required (1-200 chars)
- Content required (1-10000 chars)
- Exactly one start node per story version
- At least one end node recommended
- Warn if node has no outgoing choices (unless end node)
- Warn if node has no incoming choices (unless start node) → "Orphan node"

---

### Choice Editor Modal

**Trigger**: Click [+ Add Choice] in Node Editor

**Form**:
```
┌────────────────────────────────────────────────┐
│  Add Choice from "Forest Entrance"            │
├────────────────────────────────────────────────┤
│                                                │
│  Choice Text: *                                │
│  ┌──────────────────────────────────────────┐ │
│  │ Enter the dark forest                    │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Target Node: *                                │
│  ┌──────────────────────────────────────────┐ │
│  │ [Select] Deep Forest Clearing           │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  Display Order: 0                              │
│                                                │
│  ──────────────────────────────────────────   │
│  Conditional Logic (Advanced)                  │
│                                                │
│  Show this choice only if:                     │
│  ┌──────────────────────────────────────────┐ │
│  │ [+ Add Condition]                        │ │
│  │ has_torch = true                         │ │
│  │ [Remove]                                 │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  When chosen, set state:                       │
│  ┌──────────────────────────────────────────┐ │
│  │ [+ Add State Change]                     │ │
│  │ entered_forest = true                    │ │
│  │ [Remove]                                 │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│                          [Cancel]  [Save]      │
└────────────────────────────────────────────────┘
```

**Choice Form Fields**:
```typescript
interface ChoiceForm {
  text: string;                    // Required, what player sees
  to_node_id: UUID;                // Required, target node
  order: number;                   // Display order, default 0
  requires_state: Record<string, any> | null;  // Conditional
  sets_state: Record<string, any> | null;      // State changes
}
```

**State Condition Editor**:
- Key-value pairs
- All conditions use AND logic
- Support: boolean, string, number values
- JSON preview for advanced users

**State Change Editor**:
- Key-value pairs
- Shallow merge into player state
- JSON preview for advanced users

---

### Publish Workflow Modal

**Trigger**: Click [Publish] button

**Pre-Publish Validation**:
```
┌────────────────────────────────────────────────┐
│  Publish "The Dark Forest" v2?                 │
├────────────────────────────────────────────────┤
│                                                │
│  ✅ Story has start node                       │
│  ✅ Story has at least one end node            │
│  ✅ All nodes reachable from start             │
│  ⚠️  3 orphan nodes detected                   │
│                                                │
│  Orphan nodes (not reachable from start):      │
│  • "Secret Path" (node_id: abc...)            │
│  • "Hidden Cave" (node_id: def...)            │
│  • "Bonus Ending" (node_id: ghi...)           │
│                                                │
│  These nodes will be included in the published │
│  version but players won't be able to reach    │
│  them. Consider adding choices leading to them.│
│                                                │
│  ☐ Publish anyway (not recommended)           │
│                                                │
│                          [Cancel]  [Publish]   │
└────────────────────────────────────────────────┘
```

**Validation Checks**:
1. Has exactly one start node
2. Has at least one end node
3. No orphan nodes (warn, don't block)
4. All choices have valid target nodes

**On Success**:
- Show success toast: "Story published as v2! Now visible in catalog."
- Update story list to show "Published v2"
- Offer "View in Catalog" link

---

### Version Management UI

**Scenario**: Author wants to edit published story

**Flow**:
1. Author loads story with `published_version = 1, current_version = 1`
2. UI shows "This story is published. Create new version to edit?"
3. Author clicks [Create New Version]
4. (cut)
5. UI refreshes, displays `current_version = 2, published_version = 1`
6. Author edits v2 nodes
7. UI shows "You're editing v2 (draft). v1 is still published."
8. Author clicks [Publish]
9. v2 becomes published_version, new players see v2 going forward

**Visual Indicators**:
- Badge: "Editing v2 (Draft)" 
- Badge: "v1 Published" 
- Warning: "Changes won't affect existing players"

---

## Implementation Patterns

### Component Structure

```
src/hooks/useStories.ts       # API Hook for StoryList
src/components/Stories/
src/components/Stories/
├── StoryList/
│   ├── StoryList.tsx         # Main list component
│   ├── StoryCard.tsx         # Individual story card
│   ├── CreateStoryModal.tsx  # New story dialog
│
│
├── StoryEditor/
│   ├── StoryEditor.tsx       # Main editor container
│   ├── NodeTree/
│   │   ├── NodeTree.tsx      # Left panel tree view
│   │   ├── NodeTreeItem.tsx  # Individual node in tree
│   │   └── useNodeTree.ts    # Tree state management
│   │
│   ├── NodeEditor/
│   │   ├── NodeEditor.tsx    # Center panel editor
│   │   ├── NodeForm.tsx      # Node edit form
│   │   ├── ChoiceList.tsx    # Choices for node
│   │   ├── ChoiceEditor.tsx  # Choice edit modal
│   │   └── useNodeEditor.ts  # Editor state
│   │
│   └── PropertiesPanel/
│       ├── PropertiesPanel.tsx  # Right panel
│       ├── StoryInfo.tsx        # Metadata display
│       ├── NodeStats.tsx        # Statistics
│       └── ValidationWarnings.tsx  # Validation errors
│
└── PublishWorkflow/
    ├── PublishModal.tsx      # Publish dialog
    ├── ValidationChecker.tsx # Pre-publish validation
    └── usePublish.ts         # Publish logic

src/components/Stories/StoryValidation.ts

```

---

### State Management Pattern

Use **TanStack Query** for server state and **local component state** for form state.



---

### Story List Component Example

TODO: Implement `src/components/stories/StoryList/StoryList.tsx`


---

### Story Card Component 

TODO: Implement`src/components/stories/StoryList/StoryCard.tsx` for implementation

---

### Node Editor State Management


TODO: Implement `src/components/stories/StoryEditor/NodeEditor/useNodeEditor.ts` 

---

### Validation Helper


TODO: Implement`src/components/stories/storyValidation.ts` 


## Testing Strategy

### Unit Tests

**Test Coverage Areas**:

1. **Hooks**:
   - `useStories` - fetching, creating, updating
   - `useNodeEditor` - node operations
   - `usePublish` - publish/unpublish workflow

2. **Validation Logic**:
   - `validateStoryForPublish` - all validation rules
   - State condition parsing
   - State change parsing

3. **Components** (basic rendering):
   - StoryCard renders badges correctly
   - NodeEditor displays selected node
   - ChoiceEditor form validation



---

### Integration Tests

**Test Scenarios**:

1. **Story Creation Flow**:
   - Create story → appears in list
   - Create story → can be edited
   - Create story → can be deleted

2. **Node Management**:
   - Create node → appears in tree
   - Update node → changes persist
   - Delete node → removed from tree

3. **Publishing Workflow**:
   - Publish story → appears in catalog
   - Unpublish story → hidden from catalog
   - Create new version → increments version

4. **Version Isolation**:
   - Edit published story (v1) → create v2 → changes only affect v2
   - Publish v2 → v1 still exists for existing players


---



**Lifecycle States**:
- **Draft**: `is_published = false`, no `published_version`
- **Published**: `is_published = true`, `published_version` set
- **Unpublished**: `is_published = false`, `published_version` still set (existing players unaffected)
- **Multi-version**: `current_version > published_version` (editing new version)

---

### StoryNode Model


**Key Constraints**:
- Exactly ONE `is_start_node: true` per `story_version`
- `story_version` determines which version this node belongs to
- Nodes are immutable once their version is published (best practice)

---

### NodeChoice Model


**State Logic**:
- `requires_state`: Choice only visible if ALL conditions match player state (AND)
- `sets_state`: Shallow merge into player's `story_state` when chosen
- Values can be: boolean, string, number, nested objects

**Example**:
```json
{
  "text": "Use the torch to enter the cave",
  "requires_state": {
    "has_torch": true,
    "torch_fuel": 50  // Must have at least 50% fuel
  },
  "sets_state": {
    "in_cave": true,
    "torch_fuel": 30  // Consumes fuel
  }
}
```

---

## Common Recipes

### Recipe 1: Create Complete Story Programmatically


---

### Recipe 2: Choice Creation Workaround


---

### Recipe 3: Filtering Nodes by Story Version



---

### Recipe 4: Pre-Publish Validation


---

### Recipe 5: Version Management Flow


---

### Recipe 6: Building Node Tree Structure

---

### Recipe 7: State Condition Editor Component

---

## Appendix: Next Steps

### Immediate Actions

1. **Review Generated API Client SDK and Types**:
  - `core/client`

3. **Implement Story List** (MVP):
   - List stories
   - Create story modal
   - Publish/unpublish buttons
   - Navigate to editor

4. **Implement Story Editor** (MVP):
   - Three-panel layout
   - Node tree (left)
   - Node editor (center)
   - Properties panel (right)

### Phase 1 Deliverables

**Core Features**:
- ✅ Story List view with create/edit/delete
- ✅ Basic Story Editor with node management
- ✅ Publish workflow with validation
- ✅ Version management UI

**Deferred**:
- ⏸️ Choice creation (pending backend API)
- ⏸️ Visual story graph
- ⏸️ Timeline navigation UI
- ⏸️ Catalog browser

### Backend Coordination Required


### Questions for Backend Team


---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial release based on backend handoff docs |

---

**Questions or Issues?**

Contact the backend team or file issues in the project repository with label `frontend:story-editor`.
