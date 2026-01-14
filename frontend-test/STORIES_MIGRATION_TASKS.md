# Week 4: Stories Migration - Task Reference Card

> **Source**: `frontend/src/components/Stories/` (Chakra UI)
> **Target**: `frontend-test/src/components/Stories/` (shadcn/Tailwind)
> **Reference**: See `MIGRATION_PLAN.md` for architectural context

---

## Prerequisites

- [ ] **P1** Regenerate API client to include new endpoints (`npm run generate-client`)
  - Verify `validateStory` endpoint exists (`POST /stories/{id}/validate`)
  - Verify `getStoryTree` endpoint exists (`GET /stories/{id}/tree`)
- [ ] **P2** Copy story hooks from `frontend/src/hooks/stories/` to `frontend-test/src/hooks/stories/`
  - `useStories.ts`
  - `useStoryEditor.ts`
  - `useStoryNodes.ts`
  - `useNodeChoices.ts`
  - `useStateSchema.ts`
  - `usePublishWorkflow.ts`
- [ ] **P3** Update hook imports to use `@/` alias and new client paths

---

## Phase 1: Story List & Management

### StoryList Component
- [ ] **1.1** Create `Stories/StoryList.tsx` - main container
  - Grid layout with responsive columns
  - Empty state for no stories
  - "Create Story" button in header
  - Uses `useStories()` hook
- [ ] **1.2** Create `Stories/StoryCard.tsx` - individual story display
  - Title, description display
  - Status badge: Published (green), Draft (yellow), Unpublished (muted)
  - Version info: `v{current} / published: v{published}`
  - Last updated relative timestamp
  - Linked rooms count (if any)
- [ ] **1.3** Add StoryCard action buttons
  - Edit button → navigates to `/stories/{id}`
  - Publish/Unpublish toggle button
  - Delete button with confirmation dialog
- [ ] **1.4** Create `Stories/dialogs/CreateStoryDialog.tsx`
  - Form: title (required), description (optional)
  - Uses react-hook-form + zod validation
  - Uses `useCreateStory()` mutation

---

## Phase 2: Story Editor - Main Layout

### Editor Shell
- [ ] **2.1** Create `Stories/StoryEditor.tsx` - main editor layout
  - Two-panel layout: NodeTree (left, 280px) | NodeEditor (right, flex)
  - Header with: back button, story title, preview toggle, publish button
  - Uses `useStoryEditor()` hook
- [ ] **2.2** Add preview mode toggle
  - Button toggles `isPreviewMode` state
  - Conditionally renders StoryPreview when active
- [ ] **2.3** Integrate publish workflow in header
  - Show publish button if not published OR `current_version > published_version`
  - Validation status indicator (checkmark/warning icon)

---

## Phase 3: Node Tree (Left Panel)

### Tree Component
- [ ] **3.1** Create `Stories/NodeTree.tsx` - hierarchical tree view
  - Uses backend `GET /stories/{id}/tree` endpoint (if available)
  - Fallback: build tree client-side from nodes/choices
  - Expandable/collapsible nodes
  - "Orphaned Nodes" section for unconnected nodes
- [ ] **3.2** Create `Stories/NodeTreeItem.tsx` - individual tree node
  - Icon by type: Flag (start), Trophy (end), FileText (regular)
  - Node title (truncated if long)
  - Selection highlighting (primary background)
  - Indent based on depth level
- [ ] **3.3** Add "Create Node" button in tree header
  - Opens CreateNodeDialog
- [ ] **3.4** Create `Stories/dialogs/CreateNodeDialog.tsx`
  - Form: title, content_format (HTML/Text/JSON), is_start_node, is_end_node
  - Validation: only one start node allowed
  - Uses `useCreateNode()` mutation

---

## Phase 4: Node Editor (Right Panel)

### Node Editing Form
- [ ] **4.1** Create `Stories/NodeEditor.tsx` - container for selected node
  - Shows "Select a node" message when nothing selected
  - Node header with title and node type badges
  - NodeEditorForm below header
  - Choices section at bottom
- [ ] **4.2** Create `Stories/NodeEditorForm.tsx` - node editing form
  - Title input (text)
  - Content format selector (select: HTML, Text, JSON)
  - Content editor (RichTextEditor for HTML, textarea for others)
  - is_start_node checkbox (disabled if another node is start)
  - is_end_node checkbox
  - Auto-save on blur using `useUpdateNode()`
- [ ] **4.3** Add delete node functionality
  - Delete button with confirmation
  - Uses `useDeleteNode()` mutation

### Choices Section
- [ ] **4.4** Create choices list in NodeEditor
  - Display choices as cards: choice_text, destination node, order
  - Show conditional badge if has `requires_state`
  - Show mutation badge if has `sets_state`
- [ ] **4.5** Add "Add Choice" button
  - Opens ChoiceEditor dialog
- [ ] **4.6** Add edit/delete actions for each choice
  - Edit opens ChoiceEditor with existing data
  - Delete with confirmation dialog

---

## Phase 5: Choice Editor Dialog

- [ ] **5.1** Create `Stories/dialogs/ChoiceEditor.tsx` - modal for choice CRUD
  - Basic fields: choice_text (required), to_node_id (select), display_order
  - Node selector shows all nodes in current version
- [ ] **5.2** Add conditional display section (`requires_state`)
  - StateConditionEditor component for "requires" mode
  - Operators: eq, ne, gt, gte, lt, lte, in, exists
- [ ] **5.3** Add state mutation section (`sets_state`)
  - StateConditionEditor component for "sets" mode
  - Operators: set, inc, dec, toggle, unset
- [ ] **5.4** Wire up mutations
  - Create: `useCreateChoiceFromNode()` or `useCreateChoice()`
  - Update: `useUpdateChoice()`

---

## Phase 6: State Condition Editor (Shared)

- [ ] **6.1** Create `Stories/shared/StateConditionEditor.tsx`
  - Mode prop: "requires" | "sets"
  - Display existing conditions as rows
  - Each row: variable key (autocomplete from schema), operator, value
- [ ] **6.2** Add condition row management
  - "Add Condition" button
  - Delete button per row
- [ ] **6.3** Add operator selection based on mode
  - Requires mode: comparison operators
  - Sets mode: mutation operators
- [ ] **6.4** Add value input based on variable type
  - Boolean: checkbox
  - Number: number input
  - String: text input
  - Enum: select with enum values
- [ ] **6.5** Add undefined variable warnings
  - Highlight variables not in state schema
  - Show warning message

---

## Phase 7: Rich Text Editor (Shared)

- [ ] **7.1** Create `Stories/shared/RichTextEditor.tsx`
  - Wraps Tiptap editor
  - Toolbar above editor
  - Min height 300px
- [ ] **7.2** Create `Stories/shared/TiptapToolbar.tsx`
  - Bold, Italic, Strikethrough, Code (inline)
  - Headings: H1, H2, H3
  - Lists: Bullet, Numbered
  - Blockquote, Code Block
  - Link insert (URL prompt)
  - Image insert (URL prompt)
- [ ] **7.3** Create `Stories/shared/TiptapEditor.tsx`
  - Configure Tiptap with StarterKit, Link, Image extensions
  - Editable toggle for read-only mode
  - Debounced onChange callback

---

## Phase 8: Publish Dialog

- [ ] **8.1** Create `Stories/dialogs/PublishDialog.tsx`
  - Uses `usePublishWorkflow()` hook
  - Shows validation results (errors block publish, warnings require confirmation)
- [ ] **8.2** Create validation summary display
  - Error items (red, blocks publish)
  - Warning items (yellow, requires checkbox acknowledgment)
  - Stats: node count, choice count, orphaned count
- [ ] **8.3** Add publish confirmation
  - Checkbox: "I acknowledge the warnings" (if warnings exist)
  - Publish button (disabled until valid + acknowledged)
  - Loading state during publish

---

## Phase 9: Story Preview

- [ ] **9.1** Create `Stories/StoryPreview.tsx` - interactive story player
  - State: currentNodeId, playerState, history
  - Starts from start node
  - Renders current node content (HTML sanitized, Text plain, JSON formatted)
- [ ] **9.2** Add choice display
  - Filter choices by `requires_state` conditions
  - Display as clickable buttons/cards
- [ ] **9.3** Add choice selection handling
  - Update playerState with `sets_state` mutations
  - Navigate to destination node
  - Track history for undo
- [ ] **9.4** Add navigation controls
  - Undo button (go back in history)
  - Restart button (reset to start)
- [ ] **9.5** Add debug panel (collapsible)
  - Current player state (JSON)
  - Choice history
  - Available choices with condition details

---

## Phase 10: State Schema Management (Optional for Week 4)

> Note: This can be deferred if time-constrained. The existing validation endpoint covers the critical path.

- [ ] **10.1** Create `Stories/StateSchema/StateSchemaEditor.tsx`
  - Table of state variables grouped by category
  - Columns: key, type, default value, actions
- [ ] **10.2** Create `Stories/StateSchema/StateVariableDialog.tsx`
  - Form: key, description, value_type, default_value, category
  - Enum support with comma-separated values
- [ ] **10.3** Create `Stories/StateSchema/StateSchemaSheet.tsx`
  - Sheet (drawer) wrapper for StateSchemaEditor
  - Read-only mode toggle based on publication status
- [ ] **10.4** Add state schema button in editor header
  - Opens StateSchemaSheet

---

## Phase 11: Route Integration

- [ ] **11.1** Create `/stories` route
  - Renders StoryList component
- [ ] **11.2** Create `/stories/$storyId` route
  - Renders StoryEditor component
  - Extracts storyId from route params
- [ ] **11.3** Add Stories to main navigation
  - Nav link in sidebar/header
- [ ] **11.4** Verify all navigation flows
  - Story list → Create → Back to list
  - Story list → Edit → Back to list
  - Editor → Preview toggle → Back to edit

---

## Verification Checklist

- [ ] **V1** StoryList displays all user stories correctly
- [ ] **V2** Story creation flow works end-to-end
- [ ] **V3** Node tree displays correct hierarchy
- [ ] **V4** Node editing saves changes correctly
- [ ] **V5** Choice creation/editing works with state conditions
- [ ] **V6** Rich text editor formats content correctly
- [ ] **V7** Publish workflow validates and publishes
- [ ] **V8** Story preview plays through correctly
- [ ] **V9** All dialogs open/close properly
- [ ] **V10** Dark mode renders correctly (semantic colors)
- [ ] **V11** No Chakra UI imports remain

---

## Component Count Target

| Category | Original Files | Target Files |
|----------|---------------|--------------|
| StoryList | 3 | 3 (StoryList, StoryCard, CreateStoryDialog) |
| StoryEditor | 12 | 6 (StoryEditor, NodeTree, NodeTreeItem, NodeEditor, NodeEditorForm, CreateNodeDialog) |
| Choices | 1 | 1 (ChoiceEditor) |
| Publishing | 4 | 1 (PublishDialog) |
| Preview | 1 | 1 (StoryPreview) |
| Shared | 5 | 4 (RichTextEditor, TiptapEditor, TiptapToolbar, StateConditionEditor) |
| State Schema | 4 | 3 (StateSchemaEditor, StateVariableDialog, StateSchemaSheet) |
| **Total** | **30** | **19** |

---

## Files to Delete After Migration

These frontend files can be removed once the shadcn version is verified:

- `frontend/src/components/Stories/shared/storyValidation.ts` (136 lines) → Backend endpoint
- `frontend/src/components/Stories/StoryEditor/NodeTree/treeUtils.ts` (153 lines) → Backend endpoint
- Hardcoded `AVAILABLE_AGENTS` → Backend endpoint (already done in Rooms)

---

## Notes

- **Simplification**: The migration plan calls for merging PropertiesPanel into the editor header. Story info/metadata can be shown in a popover or the publish dialog.
- **Backend APIs**: The new `POST /stories/{id}/validate` and `GET /stories/{id}/tree` endpoints replace ~300 lines of client-side logic.
- **State Schema**: Can be accessed via a Sheet from the editor header. Full CRUD is optional for initial migration.
- **Dependencies**: Tiptap (`@tiptap/react`, `@tiptap/starter-kit`, `@tiptap/extension-link`, `@tiptap/extension-image`) and DOMPurify (`dompurify`) need to be installed.
