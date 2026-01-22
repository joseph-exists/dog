# User Pages Revamp - Implementation Design

> **Goal:** Transform the placeholder user pages into a fully functional, composable page editor with block palette sidebar and sheet-based editing.

**Date:** 2025-01-21

---

## Design Decisions

### Approach: Page-as-Source-of-Truth

All profile data lives in the page layout JSON. Blocks store both `config` (display settings) and `content` (actual data). This decouples profile customization from the core user model and enables immediate implementation without backend schema changes.

### Block Architecture

Blocks are pure render functions following a universal interface:
- Receive `config`, `content`, `isEditing`, callbacks
- Never mutate data directly - emit events
- Support composition via `children` slot
- View mode: render content
- Edit mode: handled by external sheet, not inline

### Editor UI Pattern

- **Block Palette**: Nested sidebar (left) showing draggable block types
- **Block Editor Sheet**: Slide-out panel (right) with form for selected block
- **Blocks**: Click-to-select, visual affordance in edit mode

---

## Type Definitions

### TemplateBlock (Updated)

```typescript
interface TemplateBlock {
  id: string                              // Unique instance ID (uuid)
  type: BlockType                         // Block type identifier
  column: "primary" | "auxiliary"         // Layout column
  order: number                           // Sort order within column
  config: Record<string, unknown>         // Display settings
  content?: Record<string, unknown>       // Actual data
  visibility: "visible" | "hidden"        // Visibility toggle
}

type BlockType =
  | "profileImage"
  | "identity"
  | "bio"
  | "contact"
  | "links"
  | "relationships"
  | "activityFeed"
  | "gallery"
  | "dataTable"
  | "chart"
```

### Block Content Shapes

| Block | Config | Content |
|-------|--------|---------|
| `profileImage` | `{ shape: "circle" \| "square", size: "sm" \| "md" \| "lg" }` | `{ imageUrl?: string, alt?: string }` |
| `identity` | `{ showTagline: boolean }` | `{ name: string, tagline?: string }` |
| `bio` | `{ maxLength?: number, allowRichText?: boolean }` | `{ text: string }` |
| `contact` | `{ showEmail: boolean, showPhone: boolean }` | `{ email?: string, phone?: string }` |
| `links` | `{ layout: "list" \| "grid" }` | `{ items: Array<{ id, type, url, label }> }` |
| `relationships` | `{ groupByType: boolean, maxVisible: number }` | `{ items: Array<{ entityId, typeId, name, relationshipTypeId }> }` |
| `gallery` | `{ columns: number, lightbox: boolean }` | `{ images: Array<{ id, url, alt?, caption? }> }` |

### BlockTypeDefinition (for palette)

```typescript
interface BlockTypeDefinition {
  type: BlockType
  label: string
  description: string
  icon: LucideIcon
  defaultConfig: Record<string, unknown>
  defaultContent: Record<string, unknown>
}
```

---

## File Structure

```
src/
├── hooks/
│   └── usePageEditor.ts
├── components/Page/
│   ├── index.ts
│   ├── PageShell.tsx
│   ├── PageLayout.tsx
│   ├── PageHeader.tsx
│   ├── CreatePageDialog.tsx
│   ├── BlockWrapper.tsx
│   ├── editor/
│   │   ├── index.ts
│   │   ├── BlockPalette.tsx
│   │   ├── BlockPaletteItem.tsx
│   │   ├── BlockEditorSheet.tsx
│   │   └── forms/
│   │       ├── index.ts
│   │       ├── ProfileImageForm.tsx
│   │       ├── IdentityForm.tsx
│   │       ├── BioForm.tsx
│   │       ├── ContactForm.tsx
│   │       ├── LinksForm.tsx
│   │       ├── RelationshipsForm.tsx
│   │       └── GalleryForm.tsx
│   ├── blocks/
│   │   ├── index.ts
│   │   ├── ProfileImageBlock.tsx
│   │   ├── IdentityBlock.tsx
│   │   ├── BioBlock.tsx
│   │   ├── ContactBlock.tsx
│   │   ├── LinksBlock.tsx
│   │   ├── RelationshipsBlock.tsx
│   │   ├── GalleryBlock.tsx
│   │   ├── ActivityFeedBlock.tsx
│   │   ├── DataTableBlock.tsx
│   │   └── ChartBlock.tsx
│   ├── primitives/
│   │   ├── index.ts
│   │   └── BlockContainer.tsx
│   └── registry/
│       ├── index.ts
│       ├── blockTypes.ts
│       ├── pageTemplates.ts
│       ├── entityTypes.ts
│       └── relationshipTypes.ts
├── routes/_layout/
│   └── u.$slug.tsx
└── components/Sidebar/
    └── Sidebar.tsx
```

---

## Implementation Tasks

### Phase 1: Foundation (Steps 1-4)

#### Step 1: Update TemplateBlock Type

**File:** `src/components/Page/registry/index.ts`

**Requirements:**
- Add `id: string` field (required, UUID format)
- Add `content?: Record<string, unknown>` field (optional)
- Add `visibility: "visible" | "hidden"` field (required, default "visible")
- Export updated type

**Constraints:**
- Must be backwards compatible with existing `pageTemplates.ts`
- Type must be re-exported from `registry/index.ts`

**Validation:**
- [ ] TypeScript compiles with no errors
- [ ] Existing code that uses TemplateBlock still works
- [ ] New fields are accessible in type hints

---

#### Step 2: Update blockTypes Registry

**File:** `src/components/Page/registry/blockTypes.ts` (create if not exists)

**Requirements:**
- Create `BlockTypeDefinition` interface with: `type`, `label`, `description`, `icon`, `defaultConfig`, `defaultContent`
- Export `BLOCK_TYPES: BlockTypeDefinition[]` array with all 10 block types
- Each block type must have sensible defaults for both config and content
- Icons must use lucide-react

**Constraints:**
- Import icons from lucide-react only
- `type` field must match existing `BlockType` union exactly
- `defaultContent` must match the content shape for that block type

**Validation:**
- [ ] All 10 block types defined
- [ ] Each has icon, label, description
- [ ] `npm run lint` passes
- [ ] Types are correctly inferred

**Block type definitions:**
```typescript
{ type: "profileImage", label: "Profile Image", icon: User, ... }
{ type: "identity", label: "Identity", icon: UserCircle, ... }
{ type: "bio", label: "Bio", icon: FileText, ... }
{ type: "contact", label: "Contact", icon: Mail, ... }
{ type: "links", label: "Links", icon: Link, ... }
{ type: "relationships", label: "Relationships", icon: Users, ... }
{ type: "activityFeed", label: "Activity Feed", icon: Activity, ... }
{ type: "gallery", label: "Gallery", icon: Image, ... }
{ type: "dataTable", label: "Data Table", icon: Table, ... }
{ type: "chart", label: "Chart", icon: BarChart, ... }
```

---

#### Step 3: Update pageTemplates with Content Defaults

**File:** `src/components/Page/registry/pageTemplates.ts`

**Requirements:**
- Update all template blocks to include `id` (use descriptive string like `"default-profile-image"`)
- Add `content` with empty/placeholder values for each block
- Add `visibility: "visible"` to all blocks
- Ensure 3 templates exist: Standard, Minimal, Showcase

**Constraints:**
- Template IDs must remain: `standard`, `minimal`, `showcase`
- Block order must be logical (profileImage first, etc.)
- Content should be empty strings/arrays, not undefined

**Validation:**
- [ ] Each template block has `id`, `content`, `visibility`
- [ ] Templates render without errors
- [ ] `getDefaultTemplate()` function still works

---

#### Step 4: Create usePageEditor Hook

**File:** `src/hooks/usePageEditor.ts`

**Requirements:**
- Accept `entityType: string` and `entityId: string` parameters
- Fetch page layout using `PageService.getLayout()`
- Manage draft state separately from server state
- Provide block CRUD operations: `updateBlock`, `addBlock`, `removeBlock`, `reorderBlocks`
- Provide editing lifecycle: `startEditing`, `cancelEditing`, `save`
- Track `isDirty`, `isEditing`, `isSaving` states
- Track `selectedBlockId` for sheet editor

**Interface:**
```typescript
interface UsePageEditorReturn {
  // Data
  blocks: TemplateBlock[] | undefined
  selectedBlockId: string | null
  selectedBlock: TemplateBlock | null

  // State
  isLoading: boolean
  isEditing: boolean
  isDirty: boolean
  isSaving: boolean
  error: ApiError | null
  pageExists: boolean

  // Editing lifecycle
  startEditing: () => void
  cancelEditing: () => void
  save: () => Promise<void>

  // Block selection (for sheet)
  selectBlock: (blockId: string | null) => void

  // Block operations
  updateBlockContent: (blockId: string, content: Record<string, unknown>) => void
  updateBlockConfig: (blockId: string, config: Record<string, unknown>) => void
  addBlock: (type: BlockType, column: "primary" | "auxiliary") => void
  removeBlock: (blockId: string) => void
  reorderBlocks: (column: "primary" | "auxiliary", orderedIds: string[]) => void
  toggleBlockVisibility: (blockId: string) => void

  // Page creation
  createPage: (templateId: string) => Promise<void>
}
```

**Constraints:**
- Must use TanStack Query for server state
- Must use `useState` for draft/editing state
- Must generate UUIDs for new block IDs (use `crypto.randomUUID()`)
- Must not persist until explicit `save()` call
- Query key: `["pages", entityType, entityId]`

**Validation:**
- [ ] Hook compiles without errors
- [ ] Can call `startEditing()` and `cancelEditing()` without save
- [ ] `isDirty` becomes true after any block operation
- [ ] `save()` calls `PageService.saveLayout()` with correct payload
- [ ] `selectedBlock` returns correct block when `selectedBlockId` is set

---

### Phase 2: Primitives & Blocks (Steps 5-12)

#### Step 5: Update BlockContainer Primitive

**File:** `src/components/Page/primitives/BlockContainer.tsx`

**Requirements:**
- Add `variant` prop: `"default" | "card" | "transparent"`
- Add `isSelected` prop for edit mode highlight
- Add `onClick` prop for selection handling
- Maintain existing `title`, `headerActions`, `children` props

**Variants:**
- `default`: current styling (subtle border)
- `card`: elevated with shadow, rounded corners
- `transparent`: no background/border, just spacing

**Constraints:**
- Must not break existing block usage
- Selected state: `ring-2 ring-primary` outline
- Use `cn()` for class merging

**Validation:**
- [ ] All three variants render correctly
- [ ] `isSelected` shows visual highlight
- [ ] Existing blocks still render properly

---

#### Steps 6-12: Update Block Components

**Files:** `src/components/Page/blocks/*.tsx`

**Universal Requirements for ALL blocks:**
- Update props interface to use generic `BlockProps<TConfig, TContent>`
- Accept `content` prop (optional, with sensible fallback)
- Remove `entity` prop - data comes from `content` now
- Remove inline editing - blocks are view-only
- Accept `className` for styling override
- Use `BlockContainer` with appropriate variant

**Props pattern:**
```typescript
interface ProfileImageBlockProps {
  config: ProfileImageConfig
  content?: ProfileImageContent
  className?: string
}
```

**Constraints:**
- No `isEditing` prop on blocks - they don't handle editing
- No `onContentChange` on blocks - editing happens in sheet
- Must handle undefined/empty content gracefully
- Must maintain visual fidelity with current design

**Per-block validation:**

| Block | Validation |
|-------|------------|
| ProfileImageBlock | [ ] Renders with `content.imageUrl`, [ ] Falls back to initials from `content.name` or "?" |
| IdentityBlock | [ ] Renders `content.name`, [ ] Shows tagline if `config.showTagline && content.tagline` |
| BioBlock | [ ] Renders `content.text`, [ ] Shows placeholder if empty |
| ContactBlock | [ ] Renders email/phone based on config flags, [ ] Hides if no content |
| LinksBlock | [ ] Renders `content.items` array, [ ] Grid/list based on config |
| RelationshipsBlock | [ ] Renders `content.items` grouped by type if configured |
| GalleryBlock | [ ] Renders `content.images` in grid, [ ] Respects column count |

---

### Phase 3: Editor UI (Steps 13-22)

#### Step 13: Create BlockPaletteItem

**File:** `src/components/Page/editor/BlockPaletteItem.tsx`

**Requirements:**
- Display block type icon, label, description
- Draggable (use HTML5 drag or prepare for @dnd-kit)
- Visual feedback on hover/drag
- Compact size for sidebar

**Props:**
```typescript
interface BlockPaletteItemProps {
  blockType: BlockTypeDefinition
  onDragStart?: (type: BlockType) => void
  onDragEnd?: () => void
  onClick?: (type: BlockType) => void  // Fallback for non-drag add
}
```

**Constraints:**
- Must be accessible (keyboard support for click-to-add)
- Icon size: 16px, consistent with shadcn
- Use `Button` variant="ghost" as base

**Validation:**
- [ ] Renders icon + label correctly
- [ ] Click triggers `onClick` callback
- [ ] Drag sets correct data transfer type
- [ ] Hover state is visible

---

#### Step 14: Create BlockPalette

**File:** `src/components/Page/editor/BlockPalette.tsx`

**Requirements:**
- Use shadcn `Sidebar` component (nested variant)
- List all block types from `BLOCK_TYPES` registry
- Collapsible on mobile
- Header with "Blocks" title
- Optional search/filter (stretch goal)

**Props:**
```typescript
interface BlockPaletteProps {
  onAddBlock: (type: BlockType, column: "primary" | "auxiliary") => void
  targetColumn: "primary" | "auxiliary"  // Where drops will go
  className?: string
}
```

**Constraints:**
- Width: 200-240px when expanded
- Must use shadcn Sidebar primitives
- Scrollable if many block types

**Validation:**
- [ ] All 10 block types visible
- [ ] Clicking item calls `onAddBlock` with correct type
- [ ] Collapses on mobile breakpoint
- [ ] Accessible via keyboard

---

#### Steps 15-20: Create Block Editor Forms

**Files:** `src/components/Page/editor/forms/*.tsx`

**Universal Requirements for ALL forms:**
- Use React Hook Form + Zod for validation
- Accept `content` as `defaultValues`
- Call `onSave(content)` with updated values
- Call `onCancel()` to close without saving
- Show validation errors inline
- Auto-focus first field on mount

**Props pattern:**
```typescript
interface BioFormProps {
  content: BioContent
  config: BioConfig  // For context (e.g., maxLength)
  onSave: (content: BioContent) => void
  onCancel: () => void
}
```

**Constraints:**
- Must use shadcn Form components
- Must not auto-save - explicit Save button required
- Zod schemas must match content type definitions
- Form must be scrollable if content is long

**Per-form requirements:**

| Form | Fields | Special Handling |
|------|--------|------------------|
| ProfileImageForm | `imageUrl` (input + preview), `alt` (input) | Image preview, URL validation |
| IdentityForm | `name` (input, required), `tagline` (input) | Name is required |
| BioForm | `text` (textarea) | Character count if maxLength in config |
| ContactForm | `email` (input), `phone` (input) | Email format validation |
| LinksForm | `items` array (add/remove/reorder) | Dynamic list, type dropdown |
| RelationshipsForm | `items` array | Entity search/select (can be simplified for MVP) |
| GalleryForm | `images` array (add/remove/reorder) | Image URL inputs, preview thumbnails |

**Validation per form:**
- [ ] Form renders with existing content pre-filled
- [ ] Required fields show errors when empty
- [ ] Save button calls `onSave` with updated content
- [ ] Cancel button calls `onCancel` without saving
- [ ] No console errors or warnings

---

#### Step 21: Create BlockEditorSheet

**File:** `src/components/Page/editor/BlockEditorSheet.tsx`

**Requirements:**
- Use shadcn `Sheet` component (side="right")
- Render correct form based on `block.type`
- Header shows block type label + close button
- Footer has Cancel + Save buttons
- Controlled open state via props

**Props:**
```typescript
interface BlockEditorSheetProps {
  block: TemplateBlock | null  // null = closed
  onSave: (blockId: string, content: Record<string, unknown>) => void
  onCancel: () => void
  onDelete: (blockId: string) => void
}
```

**Constraints:**
- Sheet width: 400px on desktop, full on mobile
- Must handle all block types (switch statement)
- Delete button with confirmation
- Trap focus inside sheet when open

**Validation:**
- [ ] Opens when `block` is not null
- [ ] Closes when `block` is null
- [ ] Correct form renders for each block type
- [ ] Save calls `onSave` with block ID and new content
- [ ] Delete shows confirmation before calling `onDelete`

---

#### Step 22: Create BlockWrapper

**File:** `src/components/Page/BlockWrapper.tsx`

**Requirements:**
- Wrap blocks to add click-to-select behavior
- Visual affordance in edit mode (border, hover effect)
- Click handler to select block for editing
- Optional drag handle for reordering (stretch goal)

**Props:**
```typescript
interface BlockWrapperProps {
  blockId: string
  isEditing: boolean
  isSelected: boolean
  onSelect: (blockId: string) => void
  children: React.ReactNode
  className?: string
}
```

**Constraints:**
- Only interactive in edit mode
- View mode: transparent wrapper (no visual change)
- Edit mode: hover border, cursor pointer
- Selected: ring highlight

**Validation:**
- [ ] Click calls `onSelect` with block ID (edit mode only)
- [ ] Hover shows affordance in edit mode
- [ ] No interaction in view mode
- [ ] Selected block shows highlight ring

---

### Phase 4: Integration (Steps 23-26)

#### Step 23: Create CreatePageDialog

**File:** `src/components/Page/CreatePageDialog.tsx`

**Requirements:**
- Use shadcn `Dialog` component
- Show 3 template options with previews
- Template cards with name, description, mini-preview
- Confirm button creates page with selected template
- Controlled open state

**Props:**
```typescript
interface CreatePageDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreatePage: (templateId: string) => Promise<void>
  isCreating: boolean
}
```

**Constraints:**
- Must show loading state during creation
- Must close on successful creation
- Must handle creation errors with toast

**Validation:**
- [ ] All 3 templates displayed
- [ ] Selection highlights chosen template
- [ ] Create button disabled while `isCreating`
- [ ] Dialog closes on success
- [ ] Error shows toast notification

---

#### Step 24: Update PageShell and PageLayout

**File:** `src/components/Page/PageShell.tsx`

**Requirements:**
- Remove `entity` prop - no longer needed
- Integrate `usePageEditor` hook
- Conditionally render `BlockPalette` in edit mode
- Render `BlockEditorSheet` controlled by selected block
- Wrap blocks with `BlockWrapper` for selection
- Pass correct props through render function

**Updated Props:**
```typescript
interface PageShellProps {
  entityType: string
  entityId: string
  isOwner: boolean
  onDelete?: () => void
}
```

**File:** `src/components/Page/PageLayout.tsx`

**Requirements:**
- Accept `onBlockClick` callback for edit mode
- Update render function signature to pass selection state
- Support drag-drop zones for palette items (stretch)

**Constraints:**
- Must maintain responsive behavior (mobile stacking)
- Edit mode shows palette sidebar
- View mode hides palette

**Validation:**
- [ ] Edit mode shows palette + allows block selection
- [ ] Clicking block opens sheet with correct form
- [ ] Saving in sheet updates block content
- [ ] Cancel in sheet discards changes
- [ ] View mode shows blocks without edit UI
- [ ] Mobile layout still works

---

#### Step 25: Update u.$slug.tsx Route

**File:** `src/routes/_layout/u.$slug.tsx`

**Requirements:**
- Remove hardcoded mock user
- Use `slug` param as `entityId` for `usePageEditor`
- Handle three states: loading, no page exists, page exists
- Show `CreatePageDialog` when page doesn't exist and user is owner
- Determine `isOwner` from current user context

**State handling:**
```
Loading → Skeleton/spinner
No page + isOwner → CreatePageDialog prompt
No page + !isOwner → "Page not found" message
Page exists → PageShell
```

**Constraints:**
- Must handle 404 from API gracefully (page doesn't exist)
- Must use `useAuth` hook for current user
- Slug-based lookup (user ID = slug for now, can enhance later)

**Validation:**
- [ ] Loading state shows while fetching
- [ ] New user sees "Create Your Page" prompt
- [ ] Existing page renders correctly
- [ ] Non-owner sees "not found" for missing pages
- [ ] Page title shows in browser tab

---

#### Step 26: Add "My Page" Link to Sidebar

**File:** `src/components/Sidebar/Sidebar.tsx`

**Requirements:**
- Add "My Page" navigation item
- Link to `/u/{currentUser.id}` (or slug if available)
- Show only when user is authenticated
- Use appropriate icon (User or UserCircle)

**Constraints:**
- Must use existing sidebar item pattern
- Must get user ID from auth context
- Position: after main nav items, before settings

**Validation:**
- [ ] Link visible when logged in
- [ ] Link hidden when logged out
- [ ] Clicking navigates to user's page
- [ ] Active state shows when on own page

---

## Verification Checklist

### Phase 1 Complete
- [ ] All types updated and exporting correctly
- [ ] `usePageEditor` hook works in isolation
- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds

### Phase 2 Complete
- [ ] All blocks render with new content prop
- [ ] Blocks handle empty/undefined content gracefully
- [ ] No visual regressions from current blocks

### Phase 3 Complete
- [ ] Block palette shows all types
- [ ] All editor forms validate and save correctly
- [ ] Sheet opens/closes smoothly
- [ ] Block selection works in edit mode

### Phase 4 Complete
- [ ] End-to-end flow: Sidebar → My Page → Create → Edit → Save
- [ ] Edit mode toggle works
- [ ] Changes persist after refresh
- [ ] Unsaved changes warning on navigate away

### Final Verification
- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds
- [ ] Manual test: create new page from template
- [ ] Manual test: edit all block types
- [ ] Manual test: reorder blocks
- [ ] Manual test: mobile responsive layout
- [ ] No console errors in browser

---

## Dependencies

**shadcn components to verify/install:**
```bash
npx shadcn@latest add sidebar
npx shadcn@latest add sheet
npx shadcn@latest add dialog
npx shadcn@latest add form
npx shadcn@latest add textarea
npx shadcn@latest add avatar
```

**External packages (if not present):**
- None required for MVP
- Optional: `@dnd-kit/core` for advanced drag-drop (stretch goal)

---

## Out of Scope (Future Enhancements)

- Drag-drop reordering within page (use order buttons for MVP)
- Image upload (URL input only for MVP)
- Relationships entity search (manual entry for MVP)
- Activity feed real data (placeholder for MVP)
- Public/private visibility toggle
- Custom themes/colors
- Version history
- Export/import pages
