# User Pages — Engineering Reference Card

> Quick reference for extending, integrating, or debugging the block-based page editor system.

## Architecture at a Glance

```
Route (/u/$slug)
└── PageShell (orchestrator)
    ├── BlockPalette (sidebar, edit mode)
    ├── PageHeader (breadcrumbs, save, edit toggle)
    ├── PageLayout (resizable two-column)
    │   ├── Primary Column → BlockWrapper → [Block]
    │   └── Auxiliary Column → BlockWrapper → [Block]
    └── BlockEditorSheet (right slide-out form)
```

**Hook:** `usePageEditor(entityType, entityId)` — manages all state, CRUD, and save lifecycle.

**Layout Mode:** User pages are full-bleed (`_layout.tsx` → `fullBleedRoutes`). Required for proper flex height constraints.

---

## File Map

| Layer | Path | Purpose |
|-------|------|---------|
| Route | `src/routes/_layout/u.$slug.tsx` | Entry point, ownership check, create-page flow |
| Shell | `src/components/Page/PageShell.tsx` | Orchestrator, renders blocks via switch, wires actions |
| Layout | `src/components/Page/PageLayout.tsx` | Responsive resizable two-column layout |
| Header | `src/components/Page/PageHeader.tsx` | Breadcrumbs, Save button, Edit toggle, actions |
| Wrapper | `src/components/Page/BlockWrapper.tsx` | Edit-mode toolbar (move/hide/delete) per block |
| Registry | `src/components/Page/registry/` | Block types, entity types, templates, relationships |
| Blocks | `src/components/Page/blocks/` | View components for each block type |
| Editor | `src/components/Page/editor/` | Palette, Sheet, and edit forms |
| Hook | `src/hooks/usePageEditor.ts` | State management, draft blocks, save mutation |
| Service | `src/services/pageService.ts` | API layer (`GET/POST /api/v1/pages/...`) |

---

## Adding a New Block Type

### 1. Registry Entry (`registry/blockTypes.ts`)

```tsx
// Add to BlockType union:
export type BlockType = ... | "myNewBlock"

// Add to BLOCK_TYPES array:
{
  type: "myNewBlock",
  label: "My New Block",
  description: "What it does",
  icon: SomeIcon,  // from lucide-react
  defaultConfig: { /* initial config */ },
  defaultContent: { /* initial content structure */ },
}
```

### 2. Block Component (`blocks/MyNewBlock.tsx`)

```tsx
export interface MyNewBlockConfig {
  someSetting: boolean
}

export interface MyNewBlockContent {
  someData: string
}

export interface MyNewBlockProps {
  config: MyNewBlockConfig
  content?: MyNewBlockContent
  className?: string
}

export function MyNewBlock({ config, content, className }: MyNewBlockProps) {
  // Render view-only UI
}
```

Export from `blocks/index.ts`:
```tsx
export { MyNewBlock } from "./MyNewBlock"
export type { MyNewBlockConfig, MyNewBlockContent, MyNewBlockProps } from "./MyNewBlock"
```

### 3. Render Case (`PageShell.tsx` → `renderBlock`)

```tsx
case "myNewBlock":
  return (
    <MyNewBlock
      config={{
        someSetting: (config.someSetting as boolean) ?? true,
      }}
      content={content ? { someData: (content.someData as string) ?? "" } : undefined}
    />
  )
```

### 4. Edit Form (optional) (`editor/forms/MyNewBlockForm.tsx`)

Follow the pattern in `LinksForm.tsx` or `RelationshipsForm.tsx`:
- Props: `{ content, config, onSave, onCancel }`
- Uses `react-hook-form` + `zod` for validation
- Calls `onSave(newContent)` on submit

Export from `editor/forms/index.ts`, then add case in `BlockEditorSheet.tsx`.

### 5. Done!

The block will automatically appear in the palette, be selectable, and support the toolbar (move/hide/delete).

---

## Key Patterns

### Block Data Shape

Every block in a page layout has this structure (`TemplateBlock`):

```tsx
{
  id: string           // UUID
  type: BlockType      // "identity", "bio", etc.
  column: "primary" | "auxiliary"
  order: number        // Sort position within column
  config: Record<string, unknown>   // Appearance settings
  content: Record<string, unknown>  // User data
  visibility: "visible" | "hidden"
}
```

### Edit Lifecycle

```
startEditing() → copies serverBlocks to draftBlocks
  ↓
User makes changes (add/remove/reorder/update blocks)
  ↓ isDirty = JSON.stringify(draft) !== JSON.stringify(server)
save() → POST draftBlocks to API → invalidates query → exits editing
cancelEditing() → discards draft → exits editing
```

### Column Layout

- **Primary** (left, ~70%): Main content blocks
- **Auxiliary** (right, ~30%): Sidebar blocks
- Desktop: Resizable panels via `ResizablePanelGroup`
- Mobile: Stacked single column

### Block Selection & Editing

1. Click block in edit mode → `selectBlock(id)` → highlight ring
2. BlockEditorSheet opens with appropriate form
3. Form calls `onSave(content)` → `updateBlockContent(blockId, content)`
4. Sheet closes, block re-renders with new content

---

## usePageEditor Hook API

```tsx
const {
  // Data
  blocks,                    // TemplateBlock[] | undefined
  selectedBlockId,           // string | null
  selectedBlock,             // TemplateBlock | null

  // State
  isLoading, isEditing, isDirty, isSaving, pageExists,

  // Lifecycle
  startEditing,              // () => void
  cancelEditing,             // () => void
  save,                      // () => Promise<void>

  // Selection
  selectBlock,               // (id: string | null) => void

  // Block Operations
  addBlock,                  // (type, column) => void
  removeBlock,               // (blockId) => void
  reorderBlocks,             // (column, orderedIds[]) => void
  toggleBlockVisibility,     // (blockId) => void
  updateBlockContent,        // (blockId, content) => void
  updateBlockConfig,         // (blockId, config) => void

  // Page Creation
  createPage,                // (templateId) => Promise<void>
} = usePageEditor(entityType, entityId)
```

---

## Backend API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/v1/pages/{entityType}/{entityId}` | Fetch layout (returns null if no page) |
| POST | `/api/v1/pages/{entityType}/{entityId}/layout` | Create or overwrite layout |
| PUT | `/api/v1/pages/{pageId}` | Update layout by page ID |

**Payload shape:**
```json
{
  "layout_json": [ ...TemplateBlock[] ],
  "layout_version": 1
}
```

---

## Registry Quick Reference

### Entity Types (`registry/entityTypes.ts`)

| ID | Label | Route | Color |
|----|-------|-------|-------|
| user | User | `/u/:slug` | blue |
| agent | Agent | `/agent/:id` | purple |
| team | Team | `/team/:slug` | green |
| room | Room | `/r/:id` | orange |

### Page Templates (`registry/pageTemplates.ts`)

| ID | For Entity Types | Description |
|----|-----------------|-------------|
| standard | user, agent, team | Full profile with sidebar |
| minimal | user, agent, team | Single-column, simple |
| showcase | user, team | Visual-focused with gallery |
| agent | agent | Specialized with activity feed |

### Relationship Types (`registry/relationshipTypes.ts`)

| ID | Inverse | Valid Pairs |
|----|---------|-------------|
| member | has_member | user→team |
| has_member | member | team→user |
| owner | owned_by | user→team, user→agent |
| owned_by | owner | team→user, agent→user |
| creator | created_by | user→agent |
| created_by | creator | agent→user |
| participant | — | user/agent→room |

---

## Common Extension Scenarios

### Adding a new entity type that has pages

1. Add entry to `registry/entityTypes.ts`
2. Create route file (e.g., `routes/_layout/team.$slug.tsx`) — follow `u.$slug.tsx` pattern
3. Add route to `fullBleedRoutes` in `_layout.tsx`
4. Add route title to `routeTitles` in `_layout.tsx`
5. Create/assign page templates for the entity type

### Adding a new page template

Add to `registry/pageTemplates.ts`:
```tsx
{
  id: "myTemplate",
  label: "My Template",
  description: "...",
  forEntityTypes: ["user", "agent"],
  defaultBlocks: [
    { type: "identity", column: "primary", order: 1, config: {...}, visibility: "visible" },
    // ... more blocks
  ],
}
```

### Integrating page data elsewhere in the app

```tsx
import { PageService } from "@/services/pageService"

// Fetch a page layout
const layout = await PageService.getLayout("user", userId)
if (layout) {
  const blocks = layout.layout  // TemplateBlock[]
  const identityBlock = blocks.find(b => b.type === "identity")
  const name = identityBlock?.content?.name as string
}
```

### Adding a form for an existing block without one

Blocks without forms: `activityFeed`, `dataTable`, `chart`, `personas`

1. Create `editor/forms/ActivityFeedForm.tsx`
2. Export from `editor/forms/index.ts`
3. Add case to `BlockEditorSheet.tsx` switch statement
4. Import the content/config types from the block

---

## Debugging Checklist

| Symptom | Check |
|---------|-------|
| Page shows "Dashboard" header | Is route in `routeTitles`? |
| Layout broken / no height | Is route in `fullBleedRoutes`? |
| Block not in palette | Is it in `BLOCK_TYPES` array? |
| Block renders as nothing | Is there a case in `PageShell.renderBlock()`? |
| Block not editable | Is there a form + case in `BlockEditorSheet`? |
| Save does nothing | Check browser DevTools Network tab for API errors |
| Toolbar not showing | Is `isEditing` true? Check `BlockWrapper` props |
| Changes lost on toggle-off | Is `isDirty` correctly detected? Check JSON comparison |
