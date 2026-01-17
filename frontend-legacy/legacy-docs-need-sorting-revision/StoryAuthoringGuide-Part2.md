# Story Authoring UI Implementation Requirements

**Version:** 2.0  
**Date:** 2026-01-07  
**Status:** Ready for Implementation  
**Backend Status:** ✅ All APIs implemented and ready

---

## Table of Contents

1. [Overview](#overview)
2. [Domain Concepts](#domain-concepts)
3. [Component Architecture](#component-architecture)
4. [SDK Reference](#sdk-reference)
5. [Implementation Patterns](#implementation-patterns)
6. [Component Specifications](#component-specifications)
7. [State Management](#state-management)
8. [Validation Requirements](#validation-requirements)
9. [Testing Strategy](#testing-strategy)
10. [Implementation Checklist](#implementation-checklist)

---

## Overview

### Purpose

The Story Authoring UI enables authors to create, edit, and publish interactive Choose-Your-Own-Adventure (CYOA) stories. This is the author-facing tooling that transforms TinyFoot from a story player into a story creation platform.

### Core Capabilities

- **Branching narratives** with nodes and choices
- **Conditional logic** using requires_state for choice visibility
- **State management** via sets_state for tracking items, flags, and counters
- **Version control** allowing edits to published stories without affecting active players

### Tech Stack Alignment

Per the Frontend Tech Spec, all components must use:

- **React with TypeScript** for component development
- **TanStack Query** for server state management
- **TanStack Router** for routing
- **React Hook Form** for form handling
- **Auto-generated SDK** from `@/client` for API communication

---

## Domain Concepts

### Story Lifecycle States

Stories exist in one of four states based on their properties:

| State | Conditions | Meaning |
|-------|------------|---------|
| **Draft** | `is_published = false`, `published_version = null` | New story, never published |
| **Published** | `is_published = true`, `published_version` set | Active in catalog, players can start |
| **Unpublished** | `is_published = false`, `published_version` set | Hidden from catalog, existing players continue |
| **Editing** | `current_version > published_version` | Author editing a new version |

### Version Model

Stories use a versioning system for safe editing:

- **current_version**: The author's working draft (always editable)
- **published_version**: What players see (immutable once set)
- **story_version on nodes**: Each node belongs to a specific version

When an author publishes:
1. `published_version` is set to `current_version`
2. `is_published` becomes `true`
3. Players lock to `published_version` when they start

When an author creates a new version:
1. `current_version` increments
2. All nodes/choices from published version are copied to the new version
3. `published_version` remains unchanged
4. Existing players continue on their locked version

### State Accumulation

Player state is a JSON dictionary that grows through choices:

- **requires_state**: Object defining conditions for choice visibility (AND logic)
- **sets_state**: Object defining state changes when choice is made (shallow merge)

---

## Component Architecture

### Directory Structure

Following the Component Development Walkthrough decision tree:

```
src/
├── components/
│   ├── Stories/                    # Feature-specific components
│   │   ├── StoryList/
│   │   │   ├── StoryList.tsx       # Main list view
│   │   │   ├── StoryCard.tsx       # Individual story card
│   │   │   └── CreateStoryModal.tsx
│   │   │
│   │   ├── StoryEditor/
│   │   │   ├── StoryEditor.tsx     # Main editor layout
│   │   │   ├── NodeTree/
│   │   │   │   ├── NodeTree.tsx    # Left panel - node navigation
│   │   │   │   └── NodeTreeItem.tsx
│   │   │   ├── NodeEditor/
│   │   │   │   ├── NodeEditor.tsx  # Center panel - node editing
│   │   │   │   ├── CreateNodeModal.tsx
│   │   │   │   └── ChoiceEditor.tsx
│   │   │   └── PropertiesPanel/
│   │   │       ├── PropertiesPanel.tsx  # Right panel
│   │   │       └── StoryMetadata.tsx
│   │   │
│   │   ├── PublishWorkflow/
│   │   │   ├── PublishModal.tsx
│   │   │   └── ValidationSummary.tsx
│   │   │
│   │   └── shared/
│   │       ├── StateConditionEditor.tsx  # Reusable state editor
│   │       └── storyValidation.ts        # Validation utilities
│   │
│   ├── Common/                     # Cross-feature components
│   │   └── (existing components)
│   │
│   └── ui/                         # UI primitives
│       └── (existing components)
│
├── hooks/
│   └── stories/
│       ├── useStories.ts           # Story list operations
│       ├── useStoryEditor.ts       # Editor state management
│       ├── useStoryNodes.ts        # Node CRUD operations
│       ├── useNodeChoices.ts       # Choice CRUD operations
│       └── usePublishWorkflow.ts   # Publish/unpublish logic
│
└── routes/
    └── _layout/
        └── stories/
            ├── index.tsx           # Story list route
            └── $storyId/
                └── edit.tsx        # Story editor route
```

### Component Placement Rationale

Per the decision tree in the Component Development Walkthrough:

1. **Stories/*** → Feature-specific, handles story domain logic
2. **hooks/stories/*** → Custom hooks extracting complex state logic
3. **shared/*** → Components reused within the Stories feature only

---

## SDK Reference

### Available Services

The auto-generated SDK in `@/client` provides these services for story authoring:

#### StoriesService

| Method | Purpose | Key Parameters |
|--------|---------|----------------|
| `readStories` | List author's stories | `skip`, `limit` |
| `createStory` | Create new story | `requestBody: StoryCreate` |
| `readStory` | Get single story | `id` |
| `updateStory` | Update story metadata | `id`, `requestBody: StoryUpdate` |
| `deleteStory` | Delete story (superuser only) | `id` |
| `publishStory` | Publish current version | `id` |
| `unpublishStory` | Hide from catalog | `id` |
| `createNewStoryVersion` | Create editable copy | `id` |
| `getStoryStartNode` | Get entry node | `id` |

#### StorynodesService

| Method | Purpose | Key Parameters |
|--------|---------|----------------|
| `readStorynodes` | List all nodes | `skip`, `limit` |
| `createStorynode` | Create new node | `requestBody: StoryNodeCreate` |
| `readStorynode` | Get single node | `id` |
| `updateStorynode` | Update node content | `id`, `requestBody: StoryNodeUpdate` |
| `deleteStorynode` | Delete node | `id` |
| `readNodeChoices` | Get choices from node | `nodeId`, `skip`, `limit` |
| `createNodeChoiceFromNode` | Create choice from node | `nodeId`, `requestBody: NodeChoiceBase` |

#### NodeChoicesService

| Method | Purpose | Key Parameters |
|--------|---------|----------------|
| `readNodeChoices` | List choices with filters | `fromNodeId`, `storyId`, `skip`, `limit` |
| `createNodeChoice` | Create choice with full data | `requestBody: NodeChoiceCreate` |
| `readNodeChoice` | Get single choice | `choiceId` |
| `updateNodeChoice` | Update choice | `choiceId`, `requestBody: NodeChoiceUpdate` |
| `deleteNodeChoice` | Delete choice | `choiceId` |

### Key Types

Import these types from `@/client`:

```typescript
// Stories
StoryCreate, StoryUpdate, StoryPublic, StoriesPublic

// Nodes
StoryNodeCreate, StoryNodeUpdate, StoryNodePublic, StoryNodesPublic

// Choices
NodeChoiceCreate, NodeChoiceUpdate, NodeChoicePublic, NodeChoicesPublic, NodeChoiceBase
```

### Type Definitions Quick Reference

**StoryPublic**:
- `id: string`
- `title: string`
- `description: string | null`
- `is_published: boolean`
- `current_version: number`
- `published_version: number | null`
- `owner_id: string`
- `created_at: string`
- `updated_at: string`

**StoryNodePublic**:
- `id: string`
- `story_id: string`
- `story_version: number`
- `title: string`
- `content: string`
- `node_type: string`
- `is_start_node: boolean`
- `is_end_node: boolean`
- `created_at: string`
- `updated_at: string`

**NodeChoicePublic**:
- `id: string`
- `from_node_id: string`
- `to_node_id: string`
- `text: string`
- `order: number`
- `requires_state: Record<string, unknown> | null`
- `sets_state: Record<string, unknown> | null`

---

## Implementation Patterns

### Query Key Convention

Following Frontend Rules for query key patterns:

```typescript
// Entity lists
["stories"]
["stories", storyId, "nodes"]
["stories", storyId, "nodes", nodeId, "choices"]

// Single entities
["stories", storyId]
["nodes", nodeId]
["choices", choiceId]
```

### Mutation Pattern

Per Component Development Walkthrough, mutations follow this structure:

1. Call service method from `@/client`
2. Show success toast via `useCustomToast`
3. Invalidate relevant queries via `queryClient.invalidateQueries`
4. Handle errors via `handleError` utility
5. Reset form state as needed

### Form Pattern

Per Frontend Rules, forms use React Hook Form:

1. Define form type matching the SDK's Create/Update type
2. Use `mode: "onBlur"` for validation timing
3. Set `defaultValues` for all fields
4. Use `<Field>` component from `@/components/ui/field`
5. Disable submit button when `!isValid`
6. Show loading state when `isSubmitting`

### Error Handling

Per Frontend Rules:

1. Use `handleError(err: ApiError)` utility for API errors
2. Show form field errors via `errors.fieldName?.message`
3. Use `useCustomToast` for user feedback

---

## Component Specifications

### StoryList

**Purpose**: Display author's stories with CRUD operations

**Location**: `src/components/Stories/StoryList/StoryList.tsx`

**Data Requirements**:
- Fetch stories via `StoriesService.readStories()`
- Query key: `["stories"]`

**UI Elements**:
- Grid/list of StoryCard components
- "Create Story" button triggering CreateStoryModal
- Empty state for no stories
- Loading state during fetch

**Actions**:
- Navigate to editor: `/stories/{storyId}/edit`
- Create story: Opens CreateStoryModal
- Delete story: Confirmation dialog (superuser only per API)

### StoryCard

**Purpose**: Display individual story with status badges and actions

**Location**: `src/components/Stories/StoryList/StoryCard.tsx`

**Props**: `story: StoryPublic`

**Display Elements**:
- Title, description (truncated)
- Status badge derived from story state
- Version info: `v{current_version}` / `Published: v{published_version}`
- Timestamps: created, updated

**Badge Logic**:
- Draft: `is_published === false && published_version === null`
- Published: `is_published === true`
- Unpublished: `is_published === false && published_version !== null`
- Editing: `current_version > (published_version ?? 0)`

**Actions**:
- Edit button → navigate to editor
- Publish/Unpublish toggle
- Delete button (conditional on permissions)

### CreateStoryModal

**Purpose**: Form for creating new stories

**Location**: `src/components/Stories/StoryList/CreateStoryModal.tsx`

**Form Fields**:
- `title` (required, string)
- `description` (optional, string)

**Mutation**: `StoriesService.createStory()`

**On Success**:
1. Show success toast
2. Invalidate `["stories"]`
3. Close modal
4. Navigate to editor (optional)

### StoryEditor

**Purpose**: Main editing interface with three-panel layout

**Location**: `src/components/Stories/StoryEditor/StoryEditor.tsx`

**Layout**: Three resizable panels
- Left: NodeTree (navigation)
- Center: NodeEditor (editing)
- Right: PropertiesPanel (metadata)

**State Requirements**:
- Selected node ID (local state)
- Story data (TanStack Query)
- Nodes for current_version (TanStack Query)

**Data Fetching**:
- Story: `StoriesService.readStory({ id: storyId })`
- Nodes: Filter `StorynodesService.readStorynodes()` by `story_id` and `story_version`

### NodeTree

**Purpose**: Hierarchical navigation of story nodes

**Location**: `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx`

**Props**:
- `storyId: string`
- `storyVersion: number`
- `selectedNodeId: string | null`
- `onSelectNode: (nodeId: string) => void`

**Display**:
- Tree structure showing node relationships via choices
- Icons for start/end nodes
- Selection highlight

**Data**: Nodes and choices for the story version

### NodeEditor

**Purpose**: Edit selected node content and choices

**Location**: `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx`

**Props**:
- `nodeId: string`
- `storyId: string`
- `storyVersion: number`

**Sections**:
1. **Node Details Form**
   - Title (required)
   - Content (rich text or markdown)
   - Node type (optional)
   - Flags: is_start_node, is_end_node

2. **Choices List**
   - Display outgoing choices
   - Add choice button
   - Edit/delete choice actions

**Mutations**:
- Update node: `StorynodesService.updateStorynode()`
- Create choice: `StorynodesService.createNodeChoiceFromNode()`
- Query invalidation: `["stories", storyId, "nodes"]`, `["nodes", nodeId]`

### CreateNodeModal

**Purpose**: Create new story node

**Location**: `src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx`

**Form Fields**:
- `title` (required)
- `content` (optional)
- `node_type` (optional)
- `is_start_node` (boolean, default false)
- `is_end_node` (boolean, default false)

**Hidden Fields** (set automatically):
- `story_id`: From context
- `story_version`: From story's current_version

**Validation**:
- Warn if setting is_start_node when one already exists

### ChoiceEditor

**Purpose**: Edit individual choice properties

**Location**: `src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx`

**Props**: `choice: NodeChoicePublic`, `availableNodes: StoryNodePublic[]`

**Form Fields**:
- `text` (required) - Choice display text
- `to_node_id` (required) - Destination node selector
- `order` (optional) - Display order
- `requires_state` - StateConditionEditor component
- `sets_state` - StateConditionEditor component

**Mutations**: `NodeChoicesService.updateNodeChoice()`

### StateConditionEditor

**Purpose**: Reusable editor for requires_state and sets_state JSON objects

**Location**: `src/components/Stories/shared/StateConditionEditor.tsx`

**Props**:
- `value: Record<string, unknown> | null`
- `onChange: (value: Record<string, unknown> | null) => void`
- `label: string`

**Features**:
- Add/remove key-value pairs
- Support for boolean, string, and number values
- JSON preview mode
- Validation of key uniqueness

### PropertiesPanel

**Purpose**: Display story metadata and statistics

**Location**: `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx`

**Sections**:
1. **Story Metadata**
   - Title, description (editable)
   - Version info
   - Timestamps

2. **Statistics**
   - Node count
   - Choice count
   - End node count
   - Orphan node detection

3. **Validation Warnings**
   - Missing start node
   - Unreachable nodes
   - Missing end nodes

### PublishModal

**Purpose**: Confirm publish action with validation summary

**Location**: `src/components/Stories/PublishWorkflow/PublishModal.tsx`

**Props**: `storyId: string`, `onClose: () => void`

**Pre-publish Checks**:
- Has exactly one start node
- Has at least one end node
- No orphaned nodes
- All choices have valid destinations

**Actions**:
- Publish: `StoriesService.publishStory()`
- Cancel: Close modal

---

## State Management

### Server State (TanStack Query)

Per Frontend Rules, use TanStack Query for all server data:

| Data | Query Key | Service Method |
|------|-----------|----------------|
| Story list | `["stories"]` | `StoriesService.readStories()` |
| Single story | `["stories", storyId]` | `StoriesService.readStory()` |
| Story nodes | `["stories", storyId, "nodes"]` | Filter from `StorynodesService.readStorynodes()` |
| Node choices | `["nodes", nodeId, "choices"]` | `StorynodesService.readNodeChoices()` |

### UI State (React useState)

Keep local to components:

- `selectedNodeId` - Current node being edited
- `isModalOpen` - Modal visibility states
- Form state via React Hook Form

### Custom Hooks

Extract to `src/hooks/stories/`:

**useStories**
- List stories for current user
- Create/delete story mutations

**useStoryEditor**
- Load story + nodes for editing
- Track selected node
- Compute validation state

**useStoryNodes**
- CRUD operations for nodes
- Filter by story version

**useNodeChoices**
- CRUD operations for choices
- Associated with specific node

**usePublishWorkflow**
- Publish/unpublish mutations
- Pre-publish validation

---

## Validation Requirements

### Pre-Publish Validation

Before publishing, validate:

1. **Start Node**: Exactly one node with `is_start_node: true` for current_version
2. **End Nodes**: At least one node with `is_end_node: true`
3. **Reachability**: All nodes reachable from start (via choice graph traversal)
4. **Choice Validity**: All choices point to nodes in same story_version
5. **No Orphans**: No nodes with no incoming choices (except start node)

### Form Validation

**Story Creation/Update**:
- Title: Required, max 100 characters
- Description: Optional, max 500 characters

**Node Creation/Update**:
- Title: Required, max 100 characters
- Content: Optional (but recommended)
- Only one is_start_node per version

**Choice Creation/Update**:
- Text: Required, max 200 characters
- to_node_id: Required, must exist in same story_version
- requires_state: Valid JSON object or null
- sets_state: Valid JSON object or null

---

## Testing Strategy

### Unit Tests

**Validation Functions**:
- `validateStoryForPublish` - All validation rules
- State condition parsing
- Graph traversal for reachability

**Hooks**:
- `useStories` - Fetch, create, delete operations
- `useStoryEditor` - State selection, validation computation
- `usePublishWorkflow` - Publish/unpublish flows

### Component Tests

**StoryCard**:
- Renders correct badge for each state
- Displays version info correctly
- Action buttons work

**NodeEditor**:
- Displays node data
- Form submission updates node
- Choice list displays correctly

**StateConditionEditor**:
- Add/remove key-value pairs
- Type coercion works
- JSON output is valid

### Integration Tests

**Story Creation Flow**:
1. Create story → appears in list
2. Navigate to editor → loads correctly
3. Add nodes and choices
4. Publish → appears in catalog

**Version Management**:
1. Create and publish story (v1)
2. Create new version → current_version = 2
3. Edit v2 → v1 unchanged
4. Publish v2 → new players get v2

---

## Implementation Checklist

### Phase 1: Story List (MVP)

- [ ] Create `src/components/Stories/StoryList/StoryList.tsx`
- [ ] Create `src/components/Stories/StoryList/StoryCard.tsx`
- [ ] Create `src/components/Stories/StoryList/CreateStoryModal.tsx`
- [ ] Create `src/hooks/stories/useStories.ts`
- [ ] Create route `src/routes/_layout/stories/index.tsx`
- [ ] Implement publish/unpublish toggle on StoryCard

### Phase 2: Story Editor

- [ ] Create `src/components/Stories/StoryEditor/StoryEditor.tsx` (layout)
- [ ] Create `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx`
- [ ] Create `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx`
- [ ] Create `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx`
- [ ] Create `src/hooks/stories/useStoryEditor.ts`
- [ ] Create route `src/routes/_layout/stories/$storyId/edit.tsx`

### Phase 3: Node & Choice Management

- [ ] Create `src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx`
- [ ] Create `src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx`
- [ ] Create `src/components/Stories/shared/StateConditionEditor.tsx`
- [ ] Create `src/hooks/stories/useStoryNodes.ts`
- [ ] Create `src/hooks/stories/useNodeChoices.ts`

### Phase 4: Publish Workflow

- [ ] Create `src/components/Stories/PublishWorkflow/PublishModal.tsx`
- [ ] Create `src/components/Stories/PublishWorkflow/ValidationSummary.tsx`
- [ ] Create `src/components/Stories/shared/storyValidation.ts`
- [ ] Create `src/hooks/stories/usePublishWorkflow.ts`

### Phase 5: Polish

- [ ] Add keyboard shortcuts for common actions
- [ ] Implement undo/redo for node editing
- [ ] Add autosave functionality
- [ ] Improve node tree with drag-and-drop reordering

---

## Appendix: API Endpoint Summary

### Stories Namespace (`/api/v1/stories`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/stories/` | List author's stories |
| POST | `/stories/` | Create story |
| GET | `/stories/{id}` | Get story |
| PUT | `/stories/{id}` | Update story |
| DELETE | `/stories/{id}` | Delete story |
| GET | `/stories/{id}/start-node` | Get start node |
| PUT | `/stories/{id}/publish` | Publish story |
| PUT | `/stories/{id}/unpublish` | Unpublish story |
| POST | `/stories/{id}/new-version` | Create new version |

### StoryNodes Namespace (`/api/v1/storynodes`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/storynodes/` | List nodes |
| POST | `/storynodes/` | Create node |
| GET | `/storynodes/{id}` | Get node |
| PUT | `/storynodes/{id}` | Update node |
| DELETE | `/storynodes/{id}` | Delete node |
| GET | `/storynodes/{node_id}/choices` | Get node's choices |
| POST | `/storynodes/{node_id}/choices` | Create choice from node |

### NodeChoices Namespace (`/api/v1/node-choices`)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/node-choices/` | List choices (with filters) |
| POST | `/node-choices/` | Create choice |
| GET | `/node-choices/{choice_id}` | Get choice |
| PUT | `/node-choices/{choice_id}` | Update choice |
| DELETE | `/node-choices/{choice_id}` | Delete choice |

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-06 | Initial release |
| 2.0 | 2026-01-07 | Complete rewrite aligned with Frontend Tech Spec, Frontend Rules, and Component Development Walkthrough. Added SDK reference. Removed inline code per abstraction principles. |

---

**Implementation Support**

For questions or issues, file tickets with label `frontend:story-editor` or reference:
- Frontend Tech Spec for architectural decisions
- Frontend Rules for coding standards
- Component Development Walkthrough for implementation patterns
- SDK files (`sdk_gen.ts`, `types_gen.ts`) for API signatures