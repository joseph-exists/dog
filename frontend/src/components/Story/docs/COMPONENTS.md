# Story Components Reference

Quick reference for working with Story components. For architectural decisions, see the main project docs.

## Directory Structure

```
src/components/Story/
├── Dialogs/
│   └── PanelLayoutDialog.tsx    # Story panel layout customization
├── Display/
│   ├── CreateStoryModal.tsx     # Modal for creating new stories
│   └── StoryAvatar.tsx          # Story avatar with presentation support
├── Forms/
│   └── FormSelectors/
│       └── LayoutSourceSelector.tsx  # Layout source picker (custom/defaults)
├── panels/
│   ├── StoryPlayerPanel.tsx     # Panel wrapper for StoryPlayer
│   └── StoryDebugPanel.tsx      # Debug panel for player state
├── primitives/
│   ├── PresetPicker.tsx         # Quick preset selection buttons
│   └── InteractivePreview.tsx   # Drag-and-drop panel arrangement
├── registry/
│   ├── index.ts                 # Re-exports all registry modules
│   └── panelTypes.ts            # Panel definitions for story context
├── StoryList/
│   ├── StoryCard.tsx            # Individual story card (see below)
│   └── StoryList.tsx            # Grid of story cards
├── StoryPlayer/
│   ├── StoryPlayer.tsx          # Main player component
│   ├── StoryPlayerProvider.tsx  # Player context provider
│   └── useStoryPlayerContext.ts # Player state hook
├── StoryHeader.tsx              # Page header for story routes
├── StoryShell.tsx               # Main layout orchestrator
└── StoryLayout.tsx              # Panel layout renderer
```

---

## StoryCard

**Location:** `Story/StoryList/StoryCard.tsx`

Versatile card component with three variants and optional CRUD functionality.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `story` | `StoryPublic` | required | Story data object |
| `variant` | `"full" \| "compact" \| "mini"` | `"full"` | Card size/layout variant |
| `href` | `string` | - | Makes title/avatar clickable links |
| `presentationEnabled` | `boolean` | auto | Enable theming system |
| `isSelected` | `boolean` | - | Visual selection state |
| `onClick` | `() => void` | - | Card click handler |
| `action` | `ReactNode` | - | Custom action slot (when `showActions=false`) |
| `showActions` | `boolean` | `false` | Show Edit/Publish/Delete buttons |
| `showLinkedRooms` | `boolean` | `false` | Show linked rooms section |
| `showVersionInfo` | `boolean` | `false` | Show version numbers and timestamp |
| `className` | `string` | - | Additional CSS classes |
| `debug` | `boolean` | `false` | Show presentation debug panel |

### Usage Patterns

```tsx
// Minimal mode - for pickers, previews, embeds
<StoryCard
  story={story}
  variant="compact"
  onClick={handleSelect}
  isSelected={selectedId === story.id}
/>

// Management mode - for library grids with full CRUD
<StoryCard
  story={story}
  showActions
  showLinkedRooms
  showVersionInfo
  href={`/story/${story.id}`}
/>

// Custom action slot
<StoryCard
  story={story}
  action={<Button size="sm">Add to Room</Button>}
/>

// Mini variant for lists/sidebars
<StoryCard story={story} variant="mini" onClick={handleSelect} />
```

### Variants

| Variant | Use Case | Features |
|---------|----------|----------|
| `full` | Library grid, detail views | Avatar, title, description, badges, actions, linked rooms |
| `compact` | Selection lists, panels | Horizontal layout, avatar, title, status badge |
| `mini` | Sidebar lists, dropdowns | Minimal: avatar + title only |

### Presentation System

The card supports theming via the presentation system:

```tsx
// Auto-enabled when story has presentation data or story_type
const enabled = presentationEnabled ?? !!(story.presentation || storyType)
```

Tokens supported:
- `--story-accent` - Accent color for strips/borders
- `--story-accent-position` - `top` | `bottom` | `left` | `none`
- `--story-accent-width` - e.g., `3px`
- `--story-card-radius` - Border radius override
- `--story-card-shadow` - Box shadow override

Decoration hints: `brutalist` (mono, uppercase), `ethereal` (serif, italic)

---

## PanelLayoutDialog

**Location:** `Story/Dialogs/PanelLayoutDialog.tsx`

Dialog for customizing panel layout on story pages.

### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `open` | `boolean` | required | Dialog open state |
| `onOpenChange` | `(open: boolean) => void` | required | Open state callback |
| `storyId` | `string \| null` | required | Story ID (null for user defaults) |
| `isOwner` | `boolean` | `false` | User owns the story |
| `userPermission` | `PanelPermission` | `"none"` | User's permission level |
| `isAdmin` | `boolean` | `false` | User is admin/superuser |

### Usage

```tsx
<PanelLayoutDialog
  open={layoutDialogOpen}
  onOpenChange={setLayoutDialogOpen}
  storyId={storyId}
  isOwner={canEdit}
  userPermission={canEdit ? "owner" : "none"}
/>
```

### Panel Filtering

Panels are filtered by:
1. **Context** - Only `"story"` context panels shown
2. **Permission** - Filtered by `userPermission` level
3. **System role** - Admin-only panels hidden for non-admins

---

## Panel Registry

**Location:** `Story/registry/panelTypes.ts`

Defines available panels for story context.

### Story Panels

| Kind | Label | Permission | Description |
|------|-------|------------|-------------|
| `storyPlayer` | Story Player | `none` | Interactive story playback |
| `storyDebug` | Story Debug | `owner` | Player state debugging |
| `storyEditor` | Story Editor | `owner` | Node-based authoring |
| `debug` | Debug | `admin` | General debug panel |

### Helper Functions

```tsx
import {
  getPanelsForContext,      // Get panels for "story" context
  getPanelsForEntityPermission,  // Filter by permission level
  getPanelDisplayName,      // Get human-readable label
  getDefaultPanelConfig,    // Get default config for a panel kind
} from "../registry"

// Example: Get all story panels for an owner
const panels = getPanelsForContext("story")
  .filter(p => getPanelsForEntityPermission("owner").some(pp => pp.kind === p.kind))
```

---

## StoryShell & StoryHeader

**StoryShell** (`Story/StoryShell.tsx`) - Main layout orchestrator
- Wraps content with theme providers
- Renders StoryHeader + StoryLayout
- Provides StoryPlayerProvider context when `storyId` is set

**StoryHeader** (`Story/StoryHeader.tsx`) - Page header
- Theme selectors (page/cards)
- Layout mode toggle (panels/tabs)
- Panel layout dialog trigger
- Type-aware icon display

### Props (StoryShell)

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `storyId` | `string` | No | Story ID for player context |
| `title` | `string` | Yes | Page title |
| `type` | `StoryType` | Yes | `"process"` \| `"workspace"` \| `"play"` |
| `canEdit` | `boolean` | Yes | Enable edit-related menu items |
| `panels` | `PanelConfig[]` | Yes | Panel configurations |
| `pageThemeId` | `string` | Yes | Current page theme |
| `cardsThemeId` | `string` | Yes | Current cards theme |
| `onPageThemeChange` | `(id: string) => void` | Yes | Theme change callback |
| `onCardsThemeChange` | `(id: string) => void` | Yes | Theme change callback |

---

## Common Patterns

### Adding a New Story Panel

1. Add panel kind to `registry/panelTypes.ts`:
   ```tsx
   export type PanelKind = ... | "myNewPanel"

   // In PANEL_TYPES array:
   {
     kind: "myNewPanel",
     label: "My Panel",
     description: "Does something useful",
     icon: SomeIcon,
     defaultProminence: "auxiliary",
     contexts: ["story"],
     permission: "none",
   }
   ```

2. Create panel component in `panels/MyNewPanel.tsx`

3. Register in route's panel config (e.g., `story_.$storyId.tsx`)

### Using StoryPlayer Context

```tsx
import { useStoryPlayerContext } from "@/components/Story/StoryPlayer"

function MyComponent() {
  const {
    story,           // Story data
    currentNode,     // Current story node
    playerState,     // Player state object
    makeChoice,      // Function to make a choice
    resetPlayer,     // Reset to start
  } = useStoryPlayerContext()

  // ...
}
```

---

## Migration Notes

### Stories → Story

The codebase has two parallel implementations:

| Old (`Stories/`) | New (`Story/`) | Status |
|------------------|----------------|--------|
| `Stories/StoryList/StoryCard.tsx` | `Story/StoryList/StoryCard.tsx` | New has presentation system |
| `Stories/StoryList/StoryList.tsx` | `Story/StoryList/StoryList.tsx` | Both functional |

The `/story` route uses the new `Story/` components.
The `/stories` route uses the old `Stories/` components.

Eventually, consolidate to `Story/` only.
