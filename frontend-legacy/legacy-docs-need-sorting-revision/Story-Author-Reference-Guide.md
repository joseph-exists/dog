# Story Authoring UI Implementation Reference Guide

This guide provides a comprehensive reference for implementing the Story Authoring UI based on the Story-Authoring-GuideV2 specification.

## 1. Core Architecture

### Tech Stack
- React with TypeScript for component development
- TanStack Query for server state management
- TanStack Router for routing
- Chakra UI for styling and theming
- React Hook Form for form handling
- Auto-generated SDK from `@/client` for API communication

### Directory Structure
```
src/components/Stories/                    # Feature-specific components
├── StoryList/                             # Story listing and creation
│   ├── StoryList.tsx                      # Main list view
│   ├── StoryCard.tsx                      # Individual story card
│   └── CreateStoryModal.tsx               # Story creation modal
│
├── StoryEditor/                           # Main editor interface
│   ├── StoryEditor.tsx                    # Layout container
│   ├── NodeTree/                          # Left panel - node navigation
│   │   ├── NodeTree.tsx                   # Node tree component
│   │   └── NodeTreeItem.tsx               # Individual tree item
│   ├── NodeEditor/                        # Center panel - node editing
│   │   ├── NodeEditor.tsx                 # Node editor component
│   │   ├── CreateNodeModal.tsx            # Node creation modal
│   │   └── ChoiceEditor.tsx               # Choice editor component
│   └── PropertiesPanel/                   # Right panel - metadata
│       ├── PropertiesPanel.tsx            # Properties panel
│       └── StoryMetadata.tsx              # Story metadata display
│
├── PublishWorkflow/                       # Publishing flow
│   ├── PublishModal.tsx                   # Publish confirmation modal
│   └── ValidationSummary.tsx              # Validation summary display
│
└── shared/                                # Reusable components
    ├── StateConditionEditor.tsx           # State condition editor
    └── storyValidation.ts                 # Validation utilities
```

### Key Services
- **StoriesService**: Story CRUD operations, publishing
- **StorynodesService**: Node CRUD operations
- **NodeChoicesService**: Choice CRUD operations

## 2. Key Implementation Patterns

### State Management
- **Server State**: TanStack Query for all API data
- **UI State**: React useState for local component state
- **Custom Hooks**: Extract complex logic to `src/hooks/stories/`

### Validation
- Pre-publish validation for story integrity
- Form validation for all user inputs
- State condition validation

### Versioning
- `current_version` vs `published_version` for safe editing
- Immutable published versions
- Copy-on-write for new versions

## 3. Critical Implementation Points

### Story Lifecycle States
- **Draft**: `is_published=false`, `published_version=null`
- **Published**: `is_published=true`, `published_version` set
- **Unpublished**: `is_published=false`, `published_version` set
- **Editing**: `current_version > published_version`

### Version Model
- `current_version`: Author's working draft (editable)
- `published_version`: Player-facing version (immutable)
- Publishing: Set `published_version` = `current_version`
- New version: Copy published to new `current_version`

### State Accumulation
- `requires_state`: Conditions for choice visibility (AND logic)
- `sets_state`: State changes when choice is made (shallow merge)

## 4. Validation Requirements

### Pre-Publish Validation
- Exactly one start node (`is_start_node: true`)
- At least one end node (`is_end_node: true`)
- All nodes reachable from start
- All choices point to valid nodes in same version
- No orphaned nodes (except start node)

### Form Validation
- **Story**: Title required (max 100 chars), description optional (max 500 chars)
- **Node**: Title required (max 100 chars), only one start node per version
- **Choice**: Text required (max 200 chars), valid `to_node_id`, valid JSON for state conditions

## 5. Implementation Checklist

### Phase 1: Story List (MVP)
- [ ] Create `StoryList.tsx`, `StoryCard.tsx`, `CreateStoryModal.tsx`
- [ ] Create `useStories` hook
- [ ] Create story list route
- [ ] Implement publish/unpublish toggle

### Phase 2: Story Editor
- [ ] Create `StoryEditor` layout
- [ ] Create `NodeTree`, `NodeEditor`, `PropertiesPanel`
- [ ] Create `useStoryEditor` hook
- [ ] Create story editor route

### Phase 3: Node & Choice Management
- [ ] Create `CreateNodeModal`, `ChoiceEditor`
- [ ] Create `StateConditionEditor`
- [ ] Create `useStoryNodes`, `useNodeChoices` hooks

### Phase 4: Publish Workflow
- [ ] Create `PublishModal`, `ValidationSummary`
- [ ] Create `storyValidation` utilities
- [ ] Create `usePublishWorkflow` hook

### Phase 5: Polish
- [ ] Add keyboard shortcuts
- [ ] Implement undo/redo
- [ ] Add autosave functionality
- [ ] Implement drag-and-drop node reordering

## 6. Testing Strategy

### Unit Tests
- Validation functions
- Custom hooks
- Utility functions

### Component Tests
- StoryCard rendering and interactions
- NodeEditor form handling
- StateConditionEditor functionality

### Integration Tests
- Story creation flow
- Version management
- Publish workflow

## 7. Reference Information

### API Services
- **StoriesService**: Story CRUD, publishing, version management
- **StorynodesService**: Node CRUD operations
- **NodeChoicesService**: Choice CRUD operations

### Key Types
- **StoryPublic**: Story metadata and version info
- **StoryNodePublic**: Node content and relationships
- **NodeChoicePublic**: Choice text and state conditions

This reference guide provides a comprehensive overview of the implementation requirements, architecture, and key patterns needed to build the Story Authoring UI according to the specification.