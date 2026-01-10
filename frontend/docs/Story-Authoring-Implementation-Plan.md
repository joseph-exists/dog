# Story Authoring UI: Implementation Plan 🎭📖

**Version:** 1.0
**Date:** 2026-01-07
**Status:** Ready for Adventure

---

## Welcome to the Story Forge! ⚒️✨

You're about to embark on building TinyFoot's **Story Authoring UI** - the magical workshop where authors craft branching CYOA adventures. This is where creativity meets code, where narrative possibilities unfold like a choose-your-own-adventure book (meta, right?).

Think of this plan as your quest guide. Each phase is a chapter, each task is a step on the path. Complete them in order, and you'll forge a powerful tool for storytellers everywhere.

---

## Prerequisites: Pack Your Bags 🎒

Before we begin our journey:

- ✅ **Backend APIs**: All story endpoints are implemented and ready
- ✅ **OpenAPI Client**: Generated SDK available at `@/client`
- ✅ **Tech Stack**: React, TypeScript, TanStack Query/Router, Chakra UI, React Hook Form
- ✅ **Documentation**: All guides reviewed (you're reading the implementation plan now!)
- ✅ **Development Environment**: Frontend dev server ready (`npm run dev`)

**Key Concepts to Remember:**
- Stories have `current_version` (your draft) and `published_version` (what players see)
- Nodes belong to a `story_version` - always filter by this!
- State flows through choices: `requires_state` (visibility) and `sets_state` (changes)
- Query keys follow the pattern: `["stories"]`, `["stories", storyId]`, `["stories", storyId, "nodes"]`

---

## The Five Acts: Implementation Phases 🎬

### Act I: The Story Gallery (MVP Foundation)
**Goal:** Create the "My Stories" list where authors see their creations

### Act II: The Three-Panel Workshop (Editor Shell)
**Goal:** Build the editing environment - NodeTree, NodeEditor, PropertiesPanel

### Act III: Crafting Nodes & Choices (Core Authoring)
**Goal:** Enable creating/editing nodes and choices with state conditions

### Act IV: The Publishing Ceremony (Validation & Publishing)
**Goal:** Add publish workflow with validation and version management

### Act V: The Finishing Touches (Polish & Enhancement)
**Goal:** Add quality-of-life features and refinements

---

## Act I: The Story Gallery 📚

**What We're Building:**
A grid/list view of the author's stories with cards showing status badges, version info, and actions (Edit, Publish/Unpublish, Delete).

### Task 1.1: Create Story List Hook
**File:** `src/hooks/stories/useStories.ts`

**Acceptance Criteria:**
- [X] Export `useStories` hook that calls `StoriesService.readStories()`
- [X] Use query key `["stories"]`
- [X] Return query result with `data`, `isLoading`, `error`
- [X] Export `useCreateStory` mutation hook
- [X] Export `useDeleteStory` mutation hook (for superusers)
- [X] Mutations invalidate `["stories"]` on success
- [X] Use `useCustomToast` for success messages
- [X] Use `handleError` for error handling

**Technical Notes:**
```typescript
// Query pattern
useQuery({
  queryKey: ["stories"],
  queryFn: () => StoriesService.readStories({ skip: 0, limit: 100 })
})

// Mutation pattern
useMutation({
  mutationFn: (data: StoryCreate) => StoriesService.createStory({ requestBody: data }),
  onSuccess: () => {
    showSuccessToast("Story created!")
    queryClient.invalidateQueries({ queryKey: ["stories"] })
  },
  onError: handleError
})
```

---

### Task 1.2: Create StoryCard Component
**File:** `src/components/Stories/StoryList/StoryCard.tsx`

**Acceptance Criteria:**
- [X] Accepts `story: StoryPublic` as prop
- [X] Display title, description (truncated to 150 chars), timestamps
- [X] Calculate and show status badge based on lifecycle state:
  - Draft: `is_published === false && published_version === null` (gray badge)
  - Published: `is_published === true` (blue badge with version)
  - Unpublished: `is_published === false && published_version !== null` (orange badge)
  - Editing: `current_version > (published_version ?? 0)` (yellow badge "Draft v{N}")
- [X] Show version info: "v{current_version}" / "Published: v{published_version}"
- [X] Include "Edit" button that navigates to `/stories/${storyId}/edit`
- [X] Include Publish/Unpublish toggle (uses mutation from Task 1.5)
- [X] Include Delete button (conditional on user permissions)
- [X] Use Chakra UI Card/Box component for layout
- [X] Responsive design (stack on mobile, grid on desktop)

**UI Requirements:**
- Use Chakra `Card`, `Badge`, `Button`, `Text`, `HStack`, `VStack`
- Badges use `colorPalette` prop for theming
- Truncate description with CSS `noOfLines={2}`
- Edit button uses primary color, Delete uses red

---

### Task 1.3: Create CreateStoryModal Component
**File:** `src/components/Stories/StoryList/CreateStoryModal.tsx`

**Acceptance Criteria:**
- [X] Renders Chakra `DialogRoot` with trigger button "+ New Story"
- [X] Form uses React Hook Form with `mode: "onBlur"`
- [X] Form fields: `title` (required, max 100 chars), `description` (optional, max 500 chars)
- [X] Uses `Field` component from `@/components/ui/field` for inputs
- [X] Submit button disabled when form invalid
- [X] On success: show toast, close modal, invalidate queries
- [X] On error: use `handleError` utility
- [X] Form includes `defaultValues`: `{ title: "", description: "" }`

**Form Validation:**
```typescript
register("title", {
  required: "Story title is required",
  maxLength: { value: 100, message: "Title must be 100 characters or less" }
})
register("description", {
  maxLength: { value: 500, message: "Description must be 500 characters or less" }
})
```

---

### Task 1.4: Create StoryList Container
**File:** `src/components/Stories/StoryList/StoryList.tsx`

**Acceptance Criteria:**
- [X] Uses `useStories` hook to fetch data
- [X] Shows loading state with Chakra `Spinner` or skeleton
- [X] Shows empty state with friendly message and CreateStoryModal trigger
- [X] Renders grid of StoryCard components
- [X] Grid responsive: 1 column mobile, 2 tablet, 3 desktop
- [X] Includes page header "My Stories" with CreateStoryModal button
- [X] Handles error state with error message

**Layout:**
```tsx
<Container maxW="container.xl" py={8}>
  <Flex justify="space-between" align="center" mb={6}>
    <Heading size="lg">My Stories</Heading>
    <CreateStoryModal />
  </Flex>
  <Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)", lg: "repeat(3, 1fr)" }} gap={6}>
    {stories.map(story => <StoryCard key={story.id} story={story} />)}
  </Grid>
</Container>
```

---

### Task 1.5: Add Publish/Unpublish Mutations
**File:** `src/hooks/stories/useStories.ts` (extend)

**Acceptance Criteria:**
- [X] Export `usePublishStory` mutation hook
- [X] Export `useUnpublishStory` mutation hook
- [X] Both call respective `StoriesService` methods
- [X] Invalidate `["stories"]` and `["stories", storyId]` on success
- [X] Show success toast with appropriate message
- [X] Handle errors with `handleError`
- [X] Publish mutation accepts `storyId: string`
- [X] Unpublish mutation accepts `storyId: string`

---

### Task 1.6: Create Story List Route
**File:** `src/routes/_layout/stories/index.tsx`

**Acceptance Criteria:**
- [X] Route path: `/stories`
- [X] Uses TanStack Router's `createFileRoute`
- [X] Protected with `beforeLoad` auth check
- [X] Renders `StoryList` component
- [X] Includes page title/meta for SEO
- [X] Exports route configuration

**Route Pattern:**
```typescript
export const Route = createFileRoute('/_layout/stories/')({
  component: StoryList,
  beforeLoad: async ({ context }) => {
    if (!context.auth.user) {
      throw redirect({ to: '/login' })
    }
  }
})
```

---

### 🎯 Act I Checkpoint

**What You've Built:**
- Story list with cards showing status and versions
- Create story modal with validation
- Publish/unpublish toggle on cards
- Protected route at `/stories`

**Test Your Work:**
1. Navigate to `/stories` - should see your stories or empty state
2. Click "+ New Story" - modal opens with form
3. Create story with valid data - appears in list
4. Publish/unpublish - badge changes correctly
5. Click "Edit" - navigates to editor (will implement next)

---

## Act II: The Three-Panel Workshop 🛠️

**What We're Building:**
The main editing interface with three panels: NodeTree (left), NodeEditor (center), PropertiesPanel (right).

### Task 2.1: Create Story Editor Hook
**File:** `src/hooks/stories/useStoryEditor.ts`

**Acceptance Criteria:**
- [X] Export `useStoryEditor` hook accepting `storyId: string`
- [X] Fetch story with query key `["stories", storyId]`
- [X] Fetch nodes for story with query key `["stories", storyId, "nodes"]`
- [X] Filter nodes by `story.current_version` in the fetch or post-processing
- [X] Return `story`, `nodes`, `isLoading`, `error`
- [X] Include helper: `getStartNode()` - finds node with `is_start_node === true`
- [X] Include helper: `getEndNodes()` - filters nodes with `is_end_node === true`
- [X] Include helper: `validateForPublish()` - runs validation checks

**Key Implementation:**
```typescript
const nodesQuery = useQuery({
  queryKey: ["stories", storyId, "nodes"],
  queryFn: async () => {
    const result = await StorynodesService.readStorynodes({ skip: 0, limit: 1000 })
    // Filter for current story and version
    return result.data.filter(
      node => node.story_id === storyId && node.story_version === story.current_version
    )
  },
  enabled: !!story
})
```

---

### Task 2.2: Create NodeTree Component
**File:** `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx`

**Acceptance Criteria:**
- [X] Props: `nodes: StoryNodePublic[]`, `selectedNodeId: string | null`, `onSelectNode: (id: string) => void`
- [X] Display hierarchical tree of nodes
- [X] Start node at top with special icon (🏁 or star)
- [X] End nodes marked with icon (🏆 or flag)
- [X] Selected node highlighted with different background
- [X] Click on node triggers `onSelectNode`
- [X] Shows node title and truncated content
- [X] Empty state: "No nodes yet. Create your first node!"
- [X] Scrollable if many nodes


---

### Task 2.3: Create NodeTreeItem Component
**File:** `src/components/Stories/StoryEditor/NodeTree/NodeTreeItem.tsx`

**Acceptance Criteria:**
- [X] Props: `node: StoryNodePublic`, `isSelected: boolean`, `onClick: () => void`
- [X] Display node title and icon based on type
- [X] Hover effect with cursor pointer
- [X] Selected state with highlighted background
- [X] Badge showing node type if not standard
- [X] Compact layout for list view

**Styling:**
```tsx
<Box
  p={3}
  borderRadius="md"
  bg={isSelected ? "blue.100" : "transparent"}
  _hover={{ bg: isSelected ? "blue.100" : "gray.50" }}
  cursor="pointer"
  onClick={onClick}
>
  <HStack spacing={2}>
    {node.is_start_node && <Icon as={FaFlag} color="green.500" />}
    {node.is_end_node && <Icon as={FaTrophy} color="gold" />}
    <Text fontWeight={isSelected ? "bold" : "normal"}>{node.title}</Text>
  </HStack>
</Box>
```

---

### Task 2.4: Create PropertiesPanel Component
**File:** `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx`

**Acceptance Criteria:**
- [X] Props: `story: StoryPublic`, `nodes: StoryNodePublic[]`
- [X] Display story metadata: title, description, created/updated dates
- [X] Show version info: current_version, published_version
- [X] Display statistics:
  - Total node count
  - Start node count (should be 1)
  - End node count
  - Warning if no start node or multiple start nodes
- [X] Show publish status badge
- [X] Include "Create New Version" button (if published)
- [X] Include "Publish" button (triggers modal from Act IV)

**Layout Sections:**
1. Story Info (title, desc, dates)
2. Version Status (current vs published)
3. Node Statistics (counts, warnings)
4. Actions (Publish, New Version buttons)

---

### Task 2.5: Create StoryMetadata Component
**File:** `src/components/Stories/StoryEditor/PropertiesPanel/StoryMetadata.tsx`

**Acceptance Criteria:**
- [X] Props: `story: StoryPublic`
- [X] Editable title and description using inline editing or modal
- [X] Uses `useUpdateStory` mutation (create in hook)
- [X] Displays created/updated timestamps with relative time
- [X] Shows owner info if available
- [X] Version badges for current and published versions

---

### Task 2.6: Create NodeEditor Container
**File:** `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx`

**Acceptance Criteria:**
- [X] Props: `nodeId: string | null`, `storyId: string`, `storyVersion: number`
- [X] If `nodeId` is null, show empty state: "Select a node to edit"
- [X] If `nodeId` is set, fetch and display node details
- [X] Two sections: Node Form (top) and Choices List (bottom)
- [X] Node form uses React Hook Form for editing
- [X] Form fields: title, content, node_type, is_start_node, is_end_node
- [X] Save button triggers update mutation
- [X] Choices list shows outgoing choices from this node
- [X] "+ Add Choice" button 

---

### Task 2.7: Create StoryEditor Layout Container
**File:** `src/components/Stories/StoryEditor/StoryEditor.tsx`

**Acceptance Criteria:**
- [X] Three-panel layout: NodeTree (left), NodeEditor (center), PropertiesPanel (right)
- [X] Uses Chakra `Grid` or `Flex` for responsive layout
- [X] On mobile: stack vertically, show one panel at a time with tabs
- [X] On desktop: three columns (20% / 50% / 30% width)
- [X] Manages `selectedNodeId` in local state
- [X] Passes data and callbacks to child components
- [X] Header shows story title and "Back to My Stories" link
- [X] Uses `useStoryEditor` hook to fetch data

**Layout Structure:**
```tsx
<Grid
  templateColumns={{ base: "1fr", lg: "250px 1fr 300px" }}
  gap={4}
  h="calc(100vh - 200px)"
>
  <Box overflowY="auto" borderRight="1px" borderColor="gray.200">
    <NodeTree ... />
  </Box>
  <Box overflowY="auto" p={4}>
    <NodeEditor ... />
  </Box>
  <Box overflowY="auto" borderLeft="1px" borderColor="gray.200" p={4}>
    <PropertiesPanel ... />
  </Box>
</Grid>
```

---

### Task 2.8: Create Story Editor Route
**File:** `src/routes/_layout/stories/$storyId/edit.tsx`

**Acceptance Criteria:**
- [X] Route path: `/stories/:storyId/edit`
- [X] Uses TanStack Router's `createFileRoute`
- [X] Protected with `beforeLoad` auth check
- [X] Validates `storyId` param exists
- [X] Renders `StoryEditor` component with `storyId` from params
- [X] Includes breadcrumb navigation
- [X] Page title shows story name

---

### 🎯 Act II Checkpoint

**What You've Built:**
- Three-panel editing interface
- Node tree navigation (flat list for MVP)
- Node editing form
- Properties panel with stats and actions

**Test Your Work:**
1. Click "Edit" on a story from list
2. Should see three-panel layout
3. Node tree shows existing nodes (or empty state)
4. Click a node - NodeEditor loads it
5. Edit node title/content - save works
6. Properties panel shows correct stats

---

## Act III: Crafting Nodes & Choices ✨

**What We're Building:**
Modals and forms for creating nodes and choices, including the powerful StateConditionEditor.

### Task 3.1: Create Node CRUD Hooks
**File:** `src/hooks/stories/useStoryNodes.ts`

**Acceptance Criteria:**
- [X] Export `useCreateNode` mutation hook
- [x] Export `useUpdateNode` mutation hook
- [X] Export `useDeleteNode` mutation hook
- [X] All mutations invalidate `["stories", storyId, "nodes"]` and `["nodes", nodeId]`
- [X] Create mutation enforces `story_id` and `story_version` from context
- [X] Update mutation accepts `nodeId` and `StoryNodeUpdate` data
- [X] Delete mutation confirms before deletion (or just executes, leave confirm to UI)
- [X] Success toasts for each operation
- [X] Error handling with `handleError`

---

### Task 3.2: Create CreateNodeModal Component
**File:** `src/components/Stories/StoryEditor/NodeEditor/CreateNodeModal.tsx`

**Acceptance Criteria:**
- [X] Props: `storyId: string`, `storyVersion: number`, `onSuccess?: () => void`
- [X] Trigger button: "+ New Node"
- [X] Form fields:
  - `title` (required, max 100 chars)
  - `content` (optional, textarea)
  - `node_type` (optional, select: "text" | "image" | "choice")
  - `is_start_node` (checkbox)
  - `is_end_node` (checkbox)
- [X] Validation warning if setting `is_start_node` and one already exists
- [X] Uses `useCreateNode` mutation
- [X] Auto-sets `story_id` and `story_version` in mutation payload
- [X] Closes modal and calls `onSuccess` after creation

---

### Task 3.3: Create StateConditionEditor Component
**File:** `src/components/Stories/shared/StateConditionEditor.tsx`

**Acceptance Criteria:**
- [X] Props: `value: Record<string, unknown> | null`, `onChange: (val) => void`, `label: string`
- [X] Displays key-value pairs as editable rows
- [X] "+ Add Condition" button adds new row
- [X] Each row: key input, type selector (boolean/string/number), value input
- [X] Type selector changes value input type
- [X] Remove button for each row
- [X] JSON preview toggle showing raw JSON
- [X] Validates key uniqueness (no duplicate keys)
- [X] Emits valid JSON object or null

**UI Pattern:**
```tsx
{Object.entries(value || {}).map(([key, val]) => (
  <HStack key={key}>
    <Input value={key} onChange={...} placeholder="Key" />
    <Select value={typeof val} onChange={...}>
      <option value="boolean">Boolean</option>
      <option value="string">String</option>
      <option value="number">Number</option>
    </Select>
    <Input value={val} onChange={...} placeholder="Value" type={...} />
    <IconButton icon={<FaTrash />} onClick={...} />
  </HStack>
))}
```

---

### Task 3.4: Create Choice CRUD Hooks
**File:** `src/hooks/stories/useNodeChoices.ts`

**Acceptance Criteria:**
- [X] Export `useChoicesForNode` query hook - fetches choices from a node
- [X] Export `useCreateChoice` mutation hook
- [X] Export `useUpdateChoice` mutation hook
- [X] Export `useDeleteChoice` mutation hook
- [X] Query key: `["nodes", nodeId, "choices"]`
- [X] Mutations invalidate relevant queries
- [X] Create uses `StorynodesService.createNodeChoiceFromNode` or `NodeChoicesService.createNodeChoice`
- [X] Update uses `NodeChoicesService.updateNodeChoice`
- [X] Delete uses `NodeChoicesService.deleteNodeChoice`

---

### Task 3.5: Create ChoiceEditor Component
**File:** `src/components/Stories/StoryEditor/NodeEditor/ChoiceEditor.tsx`

**Acceptance Criteria:**
- [X] Props: `choice: NodeChoicePublic`, `availableNodes: StoryNodePublic[]`, `onSuccess?: () => void`
- [X] Can be used for both create and edit modes
- [X] Form fields:
  - `text` (required, max 200 chars) - what player sees
  - `to_node_id` (required, select from availableNodes)
  - `order` (number, default 0)
  - `requires_state` (uses StateConditionEditor)
  - `sets_state` (uses StateConditionEditor)
- [X] Uses `useUpdateChoice` or `useCreateChoice` based on mode
- [X] Dialog/modal pattern for editing
- [X] Shows node title for destination instead of just ID

**Advanced UI:**
- Collapsible "Advanced" section for state conditions
- Visual indicator if choice has conditions

---

### Task 3.6: Add Choice List to NodeEditor
**File:** `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx` (extend)

**Acceptance Criteria:**
- [X] Below node form, show "Choices from this node"
- [X] Use `useChoicesForNode` to fetch choices
- [X] Display each choice with: text, destination node title, order
- [X] Show badges if choice has `requires_state` or `sets_state`
- [X] Edit button opens ChoiceEditor in edit mode
- [X] Delete button with confirmation
- [X] "+ Add Choice" button opens ChoiceEditor in create mode
- [X] Empty state: "No choices yet. Add one to create branching paths!"

---

### Task 3.7: Integrate Create Node Button
**File:** `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx` (extend)

**Acceptance Criteria:**
- [X] Add "+ New Node" button at top or bottom of tree
- [X] Opens CreateNodeModal
- [X] After node creation, auto-select the new node in tree
- [X] Refresh node list after creation

---

### 🎯 Act III Checkpoint

**What You've Built:**
- Full node CRUD with modal
- Choice creation and editing
- StateConditionEditor for requires_state and sets_state
- Complete authoring flow: create nodes → add choices → set conditions

**Test Your Work:**
1. Create a new node via modal
2. Select node in tree
3. Add a choice to the node
4. Set requires_state condition: `has_torch: true`
5. Set sets_state change: `entered_cave: true`
6. Edit choice text and order
7. Create another node and choice linking to it

---

## Act IV: The Publishing Ceremony 🎊

**What We're Building:**
Validation system and publish workflow to safely release stories.

### Task 4.1: Create Validation Utilities
**File:** `src/components/Stories/shared/storyValidation.ts`

**Acceptance Criteria:**
- [X] Export `validateStoryForPublish` function
- [X] Takes `story: StoryPublic`, `nodes: StoryNodePublic[]`, `choices: NodeChoicePublic[]`
- [X] Returns validation result object:
  ```typescript
  {
    isValid: boolean
    errors: string[]
    warnings: string[]
  }
  ```
- [X] Checks:
  1. Exactly one start node
  2. At least one end node
  3. All nodes reachable from start (graph traversal)
  4. All choices have valid `to_node_id` in same version
  5. No orphaned nodes (optional warning, not error)
- [ ] Export helper: `buildNodeGraph` - creates adjacency list from choices
- [ ] Export helper: `findReachableNodes` - BFS/DFS from start node

**Graph Traversal Pseudo-code:**
```typescript
function findReachableNodes(startNode, choices) {
  const visited = new Set()
  const queue = [startNode.id]

  while (queue.length > 0) {
    const current = queue.shift()
    visited.add(current)

    // Find choices from current node
    const outgoing = choices.filter(c => c.from_node_id === current)
    outgoing.forEach(choice => {
      if (!visited.has(choice.to_node_id)) {
        queue.push(choice.to_node_id)
      }
    })
  }

  return visited
}
```

---

### Task 4.2: Create Publish Workflow Hook
**File:** `src/hooks/stories/usePublishWorkflow.ts`

**Acceptance Criteria:**
- [ ] Export `usePublishWorkflow` hook accepting `storyId: string`
- [ ] Fetches story, nodes, and choices
- [ ] Runs `validateStoryForPublish` automatically
- [ ] Returns: `validation`, `isReady`, `publish`, `unpublish`
- [ ] `publish` mutation calls `StoriesService.publishStory`
- [ ] Invalidates queries after publish
- [ ] Shows success toast with version number

---

### Task 4.3: Create ValidationSummary Component
**File:** `src/components/Stories/PublishWorkflow/ValidationSummary.tsx`

**Acceptance Criteria:**
- [ ] Props: `validation: ValidationResult`
- [ ] Shows checkmarks for passed validations
- [ ] Shows errors in red with warning icon
- [ ] Shows warnings in orange with info icon
- [ ] Groups by severity: errors first, then warnings
- [ ] Clean, scannable layout

**UI Example:**
```tsx
<VStack align="stretch" spacing={2}>
  {validation.errors.map(error => (
    <HStack key={error} color="red.600">
      <Icon as={FaTimesCircle} />
      <Text>{error}</Text>
    </HStack>
  ))}
  {validation.warnings.map(warning => (
    <HStack key={warning} color="orange.600">
      <Icon as={FaExclamationTriangle} />
      <Text>{warning}</Text>
    </HStack>
  ))}
</VStack>
```

---

### Task 4.4: Create PublishModal Component
**File:** `src/components/Stories/PublishWorkflow/PublishModal.tsx`

**Acceptance Criteria:**
- [ ] Props: `storyId: string`, `isOpen: boolean`, `onClose: () => void`
- [ ] Uses `usePublishWorkflow` hook
- [ ] Shows ValidationSummary component
- [ ] If validation fails: disable publish button, show errors
- [ ] If validation passes: enable publish button
- [ ] Publish button text: "Publish v{current_version}"
- [ ] Checkbox: "I understand this will make the story available in the catalog"
- [ ] Cancel button closes modal
- [ ] After publish: close modal, show success toast, redirect or refresh

---

### Task 4.5: Integrate Publish Button
**File:** `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx` (extend)

**Acceptance Criteria:**
- [ ] Add "Publish" button in actions section
- [ ] Button opens PublishModal
- [ ] If already published: show "Publish v{next_version}" or "Unpublish"
- [ ] Show current publish status clearly

---

### Task 4.6: Add Create New Version Feature
**File:** `src/hooks/stories/useStories.ts` (extend)

**Acceptance Criteria:**
- [ ] Export `useCreateNewVersion` mutation hook
- [ ] Calls `StoriesService.createNewStoryVersion`
- [ ] Invalidates story and nodes queries
- [ ] Shows success toast: "Version {new_version} created! You can now edit without affecting published version."
- [ ] Only available if story is published

---

### Task 4.7: Integrate New Version Button
**File:** `src/components/Stories/StoryEditor/PropertiesPanel/PropertiesPanel.tsx` (extend)

**Acceptance Criteria:**
- [ ] Add "Create New Version" button
- [ ] Only visible if `published_version !== null && current_version === published_version`
- [ ] Opens confirmation dialog explaining what happens
- [ ] Triggers `useCreateNewVersion` mutation
- [ ] After success, editor reloads with new version

---

### 🎯 Act IV Checkpoint

**What You've Built:**
- Complete validation system with graph traversal
- Publish modal with validation summary
- Unpublish functionality
- Version management (create new version for safe editing)

**Test Your Work:**
1. Create a story with nodes and choices
2. Click "Publish" - validation runs
3. Fix any errors (add start node, end node, etc.)
4. Publish successfully - see version number change
5. Create new version - current_version increments
6. Edit new version - published version unchanged
7. Unpublish story - disappears from catalog (when implemented)

---

## Act V: The Finishing Touches ✨

**What We're Building:**
Quality-of-life improvements and polish.

### DEFERRED:  Task 5.1: Add Keyboard Shortcuts

**Files to Update:**
- `src/components/Stories/StoryEditor/StoryEditor.tsx`

**Acceptance Criteria:**
- [ ] Implement keyboard event listener at editor level
- [ ] Shortcuts:
  - `Ctrl+S` / `Cmd+S`: Save current node
  - `Ctrl+N` / `Cmd+N`: New node
  - `Ctrl+P` / `Cmd+P`: Publish
  - `Esc`: Close any open modal
- [ ] Show keyboard hints in UI (tooltip or help section)
- [ ] Prevent default browser behavior

---

### DEFERRED:  Task 5.2: Add Autosave for Node Content

**Files to Update:**
- `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx`

**Acceptance Criteria:**
- [ ] Debounce node content changes (3-5 seconds)
- [ ] Auto-save using `useUpdateNode` mutation
- [ ] Show "Saving..." indicator
- [ ] Show "Saved ✓" confirmation
- [ ] Don't block user interaction during save

---

### Task 5.3: Improve Node Tree Visualization

**Files to Update:**
- `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx`

**Acceptance Criteria:**
- [X] Show hierarchical relationships based on choices (not just flat list)
- [X] Indent child nodes
- [X] Collapse/expand branches
- [X] Visual lines connecting parent to child nodes
- [X] Highlight path from start to selected node

**Enhancement Approach:**
- Build tree structure from choices
- Use recursive component pattern for nesting
- Consider library like `react-complex-tree` if manual implementation too complex

---

### Task 5.4: Add Drag-and-Drop Node Reordering

**Files to Update:**
- `src/components/Stories/StoryEditor/NodeTree/NodeTree.tsx`

**Acceptance Criteria:**
- [X] Enable drag-and-drop to reorder nodes in tree
- [X] Visual feedback during drag (ghost element)
- [X] Update node `order` field on drop (may need to add this field to backend)
- [X] Persist order to backend
- [X] Works on touch devices

**Libraries to Consider:**
- `@dnd-kit/core` (recommended by Chakra docs)

---

### Task 5.5: Add Undo/Redo for Node Editing

**Files to Create:**
- `src/hooks/stories/useNodeHistory.ts`

**Acceptance Criteria:**
- [ ] Track history of node content changes
- [ ] Implement undo stack (array of previous states)
- [ ] Implement redo stack
- [ ] `Ctrl+Z` / `Cmd+Z`: Undo
- [ ] `Ctrl+Shift+Z` / `Cmd+Shift+Z`: Redo
- [ ] Clear redo stack on new edit
- [ ] Limit history to last 50 changes

---

### Task 5.6: Add Rich Text Editor for Node Content

**Files to Update:**
- `src/components/Stories/StoryEditor/NodeEditor/NodeEditor.tsx`

**Acceptance Criteria:**
- [ ] Replace plain textarea with rich text editor
- [ ] Support: code blocks, bold, italic, headings, lists, links
- [ ] Store as HTML or Markdown in backend
- [ ] Use library: `@tiptap/react` (already installed in project)
- [ ] Maintain current autosave behavior

---

### Task 5.7: Add Story Preview Mode

**Files to Create:**
- `src/components/Stories/StoryPlayer/StoryPreview.tsx`

**Acceptance Criteria:**
- [X] "Preview" button in editor header
- [X] Opens story player in test mode
- [X] Starts from start node
- [X] Shows choices, allows navigation
- [X] Displays current state (debug panel)
- [X] "Exit Preview" button returns to editor
- [X] Uses same story playing logic as player (if exists)

---

### 🎯 Act V Checkpoint

**What You've Built:**
- Keyboard shortcuts for faster workflows
- Autosave for peace of mind
- Enhanced tree visualization
- Drag-and-drop reordering
- Undo/redo for content editing
- Rich text editing
- Story preview mode

**Test Your Work:**
1. Use keyboard shortcuts to create/save nodes
2. Edit node content - autosave indicator appears
3. Undo/redo changes with keyboard
4. Drag nodes to reorder in tree
5. Use rich text formatting in node content
6. Click "Preview" to test story flow

---

## Final Quest Checklist 📋

### Phase 1: Story Gallery ✅
- [X] useStories hook with queries and mutations
- [X] StoryCard component with status badges
- [X] CreateStoryModal with validation
- [X] StoryList container with grid layout
- [X] Publish/unpublish mutations
- [X] Story list route at `/stories`

### Phase 2: Three-Panel Workshop ✅
- [X] useStoryEditor hook with data fetching
- [X] NodeTree component with selection
- [X] NodeTreeItem component
- [X] PropertiesPanel with stats
- [ ] StoryMetadata component
- [X] NodeEditor container
- [X] StoryEditor layout with three panels
- [X] Story editor route at `/stories/:storyId/edit`

### Phase 3: Nodes & Choices ✅
- [ ] useStoryNodes hook with CRUD operations
- [ ] CreateNodeModal with validation
- [ ] StateConditionEditor component
- [ ] useNodeChoices hook with CRUD operations
- [ ] ChoiceEditor component
- [ ] Choice list integration in NodeEditor
- [ ] Create node button in NodeTree

### Phase 4: Publishing ✅
- [ ] Validation utilities with graph traversal
- [ ] usePublishWorkflow hook
- [ ] ValidationSummary component
- [ ] PublishModal component
- [ ] Publish button integration
- [ ] useCreateNewVersion mutation
- [ ] New version button integration

### Phase 5: Polish ✅
- [ ] Keyboard shortcuts
- [ ] Autosave for node content
- [ ] Enhanced tree visualization
- [ ] Drag-and-drop reordering
- [ ] Undo/redo functionality
- [ ] Rich text editor
- [ ] Story preview mode

---

## Testing Your Story Forge 🧪

### Unit Tests to Write

**Hooks:**
```typescript
describe('useStories', () => {
  it('fetches stories successfully')
  it('creates story with validation')
  it('publishes story')
  it('unpublishes story')
})

describe('useStoryEditor', () => {
  it('fetches story and nodes')
  it('filters nodes by current version')
  it('finds start node')
})

describe('useStoryNodes', () => {
  it('creates node with story_id and version')
  it('updates node')
  it('deletes node')
})
```

**Validation:**
```typescript
describe('validateStoryForPublish', () => {
  it('fails when no start node')
  it('fails when multiple start nodes')
  it('fails when no end node')
  it('fails when nodes unreachable')
  it('warns about orphaned nodes')
  it('passes with valid story structure')
})
```

**Components:**
```typescript
describe('StoryCard', () => {
  it('shows correct badge for draft story')
  it('shows correct badge for published story')
  it('shows correct badge for editing state')
})

describe('StateConditionEditor', () => {
  it('adds new condition')
  it('removes condition')
  it('validates key uniqueness')
  it('outputs valid JSON')
})
```

### Integration Tests

**Story Creation Flow:**
1. User navigates to `/stories`
2. User clicks "+ New Story"
3. User fills form and submits
4. Story appears in list
5. User clicks "Edit"
6. Editor loads with empty state

**Publishing Flow:**
1. User creates story with nodes and choices
2. User clicks "Publish"
3. Validation runs and shows errors
4. User fixes errors
5. User publishes successfully
6. Story shows "Published v1" badge

**Version Management Flow:**
1. User publishes story v1
2. User clicks "Create New Version"
3. current_version increments to 2
4. User edits v2 nodes
5. published_version remains 1
6. User publishes v2
7. published_version updates to 2

---

## Common Pitfalls & Solutions 🛡️

### Pitfall 1: Forgetting to Filter by story_version
**Problem:** Fetching all nodes for a story shows nodes from multiple versions
**Solution:** Always filter: `nodes.filter(n => n.story_version === story.current_version)`

### Pitfall 2: Not Invalidating Queries
**Problem:** UI doesn't update after mutations
**Solution:** Always call `queryClient.invalidateQueries({ queryKey: [...] })` in `onSuccess`

### Pitfall 3: Circular Dependencies in State
**Problem:** requires_state and sets_state can create infinite loops
**Solution:** Validation should warn about circular dependencies (advanced feature)

### Pitfall 4: Graph Traversal Performance
**Problem:** Large stories make reachability check slow
**Solution:** Memoize graph building, add loading indicator

### Pitfall 5: Modal State Management
**Problem:** Form state persists after closing modal
**Solution:** Always `reset()` form in modal `onClose` handler

---

## Celebration & Next Steps 🎉

Congratulations! You've built a complete Story Authoring UI. Authors can now:

- 📚 Manage their story library
- ✍️ Create and edit nodes with rich content
- 🔀 Build branching paths with conditional choices
- 🎭 Track player state through the narrative
- 📦 Publish stories safely with version control
- 🔮 Preview their creations before releasing

**What's Next:**

1. **Timeline Navigation UI** (Phase 3 integration)
   - Show player timeline with undo/jump features
   - Breadcrumb navigation of choices
   - Abandoned branch visualization

2. **Catalog Browser** (Discovery context)
   - Public story catalog
   - Search and filtering
   - Story previews and ratings

3. **Visual Story Graph**
   - Canvas-based node editor
   - Drag nodes to position
   - Visual connections between nodes
   - Zoom and pan

4. **Analytics Dashboard**
   - Player progress tracking
   - Popular paths analysis
   - Drop-off points identification

5. **Collaborative Authoring**
   - Share stories with co-authors
   - Comments and suggestions
   - Version history with diffs

---

## Quick Reference: Key Patterns 📖

### Query Pattern
```typescript
const { data, isLoading } = useQuery({
  queryKey: ["stories", storyId],
  queryFn: () => StoriesService.readStory({ id: storyId })
})
```

### Mutation Pattern
```typescript
const mutation = useMutation({
  mutationFn: (data) => Service.method({ requestBody: data }),
  onSuccess: () => {
    showSuccessToast("Success!")
    queryClient.invalidateQueries({ queryKey: ["key"] })
  },
  onError: handleError
})
```

### Form Pattern
```typescript
const { register, handleSubmit, formState: { errors, isValid } } = useForm({
  mode: "onBlur",
  defaultValues: { field: "" }
})
```

### Modal Pattern
```typescript
<DialogRoot open={isOpen} onOpenChange={({ open }) => setIsOpen(open)}>
  <DialogTrigger asChild><Button>Open</Button></DialogTrigger>
  <DialogContent>
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* form fields */}
    </form>
  </DialogContent>
</DialogRoot>
```

---

## Support & Resources 🤝

- **Frontend Rules**: `/frontend/docs/FrontendRULES.md`
- **Component Walkthrough**: `/frontend/docs/ComponentDevelopmentWalkthrough.md`
- **Story Authoring Guide**: `/frontend/docs/Story-Authoring-Guide.md`
- **API Reference**: `/frontend/docs/StoryAuthoringGuide-Part2.md`

**Need Help?**
File issues with label `frontend:story-editor` or reference this implementation plan in discussions.

---

**May your stories branch well and your state accumulate wisely!** 📖✨
