# Persona Picker System - Implementation Design

> **Goal:** Create a unified, composable persona selection system that adapts to multiple contexts (rooms, stories, pages) for both users and agents.

**Date:** 2025-01-21

---

## Design Philosophy

### Core Insight: Structural Symmetry

UserPersona and AgentPersona are structurally identical:
- Both are junction tables between an owner (user/agent) and a persona
- Both carry the same metadata (nickname, is_active)
- Both form a "persona library" for their owner

**This symmetry is the foundation of our design.** Rather than building separate user and agent persona pickers, we build ONE picker that's parameterized by owner type. This reduces code, ensures consistency, and makes the system easier to extend.

### Design Principles

| Principle | Application |
|-----------|-------------|
| **Single source of truth** | One `PersonaPicker` component serves all contexts |
| **Composition over configuration** | Small primitives combine into variants |
| **Context-agnostic core** | Picker doesn't know about rooms/stories/pages - it just knows about persona libraries |
| **Symmetry preservation** | User and agent paths remain parallel at every layer |
| **Registry-driven extensibility** | New modes/variants added via configuration, not code changes |

### Alignment with Existing Patterns

This design intentionally mirrors established patterns in the codebase:

| System | Pattern | Persona Picker Equivalent |
|--------|---------|---------------------------|
| **Pages** | BlockContainer + Block variants | PersonaItem + PersonaCard variants |
| **Pages** | PageShell orchestrates blocks | PersonaPicker orchestrates variants |
| **Room** | PanelContainer + Panel types | Variant shells + content components |
| **Services** | ViewModel transformation | `LibraryPersona` unified view model |
| **Hooks** | TanStack Query + mutations | `usePersonaLibrary` follows same pattern |

---

## Intended Outcomes

### Immediate Capabilities

1. **Users can manage their persona library**
   - View all personas in their collection
   - Add new personas from available pool
   - Edit nicknames for personalization
   - Remove personas they no longer want
   - Set active/inactive status

2. **Agents can have persona libraries**
   - Same capabilities as users
   - Managed by agent owner/operator
   - Displayed on agent pages

3. **Persona selection in context**
   - Quick selection when joining a room
   - Selection when starting a story
   - Inline display on user/agent pages

### Future-Ready Extensibility

The design explicitly supports these future features without architectural changes:

| Future Feature | How Design Supports It |
|----------------|------------------------|
| Persona creation | Add `PersonaCreatorForm`, render in sheet variant |
| Persona sharing | Add sharing service, extend `PersonaActions` |
| Story compatibility filtering | Expand `filter` prop with `compatibleWithStory` |
| Persona marketplace | Add `source` parameter to `useAvailablePersonas` |
| Persona versioning | Extend `LibraryPersona` type with version fields |
| Trait/quality editing | Expand `PersonaCard` with inline editing |

### Success Criteria

- [ ] Same component works for user and agent persona libraries
- [ ] All four variants (dropdown, popover, inline, sheet) render correctly
- [ ] All modes (select-single, select-multiple, manage, browse) function properly
- [ ] Integrates seamlessly with Pages block system
- [ ] Integrates with room join flow
- [ ] No code duplication between user/agent paths
- [ ] Consistent with existing service/hook/component patterns

---

## System Constraints

### Must Follow

| Constraint | Rationale |
|------------|-----------|
| **Use existing shadcn components** | Dropdown, Popover, Sheet, Avatar, Badge, Button - no new UI primitives |
| **Service + ViewModel pattern** | All API data transformed to ViewModels before reaching components |
| **TanStack Query for server state** | Consistent with all other data fetching in app |
| **No inline API calls in components** | All fetching goes through hooks that use services |
| **Barrel exports** | All public components exported from `index.ts` |
| **Biome linting** | Code must pass `npm run lint` |
| **TypeScript strict mode** | No `any` types, all props typed |

### Must Avoid

| Anti-pattern | Why |
|--------------|-----|
| Separate UserPersonaPicker and AgentPersonaPicker | Violates symmetry principle, duplicates code |
| Hardcoded owner type checks in components | Components should be owner-agnostic |
| Direct API calls in components | Breaks service layer abstraction |
| New UI primitives when shadcn has equivalent | Inconsistent styling, maintenance burden |
| Props drilling beyond 2 levels | Use hooks or context instead |
| Components over 300 lines | Extract into smaller pieces |

### Query Key Convention

```typescript
// Follow existing patterns:
["rooms", roomId]
["rooms", roomId, "messages"]
["pages", entityType, entityId]

// New persona patterns:
["persona-library", ownerType, ownerId]           // Full library
["persona-library", ownerType, ownerId, entryId]  // Single entry
["personas"]                                       // All available
["personas", personaId]                           // Single persona
```

---

## Type Definitions

### Core Types

```typescript
// src/components/Persona/types.ts

/**
 * Identifies who owns a persona library.
 * The picker is agnostic to owner type - this abstraction enables that.
 */
export interface PersonaLibraryOwner {
  type: "user" | "agent"
  id: string
  name: string  // Display name: "Your Personas" or "Claude's Personas"
}

/**
 * Unified view of a persona in someone's library.
 * Normalizes UserPersonaPublic and AgentPersonaPublic into one shape.
 */
export interface LibraryPersona {
  // Junction data
  libraryEntryId: string      // UserPersona.id or AgentPersona.id
  ownerId: string             // user_id or agent_id
  ownerType: "user" | "agent"

  // Persona data (denormalized for display)
  personaId: string
  name: string
  nickname: string | null
  description: string | null
  isActive: boolean

  // Rich data for detailed views (optional, loaded on demand)
  longDescription?: string | null
  domains?: string[]
  traits?: Array<{ id: string; name: string }>
  qualities?: Array<{ id: string; name: string }>
}

/**
 * Picker interaction modes.
 */
export type PersonaPickerMode =
  | "select-single"    // Pick one persona (room join, story start)
  | "select-multiple"  // Pick many personas (batch assignment)
  | "manage"           // Full CRUD (user's page, agent config)
  | "browse"           // Read-only viewing (public page)

/**
 * Visual presentation variants.
 */
export type PersonaPickerVariant =
  | "dropdown"   // Compact trigger + menu
  | "popover"    // Trigger + floating card
  | "sheet"      // Slide-out panel
  | "inline"     // Embedded in page

/**
 * Filter options for narrowing persona list.
 */
export interface PersonaFilter {
  isActive?: boolean
  domains?: string[]
  requiredTraits?: string[]
  searchQuery?: string
}

/**
 * Main picker props - the unified interface.
 */
export interface PersonaPickerProps {
  // Whose library?
  owner: PersonaLibraryOwner

  // What can user do?
  mode: PersonaPickerMode

  // How does it appear?
  variant: PersonaPickerVariant

  // Selection (controlled)
  selected?: string | string[] | null
  onSelect?: (selected: string | string[] | null) => void

  // Optional filtering
  filter?: PersonaFilter

  // Layout options (for inline/sheet)
  layout?: "list" | "grid"
  maxVisible?: number

  // Styling
  className?: string

  // Trigger customization (for dropdown/popover)
  trigger?: React.ReactNode
  placeholder?: string
}
```

### Props Interfaces for Primitives

```typescript
/**
 * PersonaItem - compact single-line display
 */
export interface PersonaItemProps {
  persona: LibraryPersona
  isSelected?: boolean
  selectionMode?: "none" | "radio" | "checkbox"
  onSelect?: () => void
  onEdit?: () => void
  onRemove?: () => void
  showActions?: boolean
  className?: string
}

/**
 * PersonaCard - expanded detail view
 */
export interface PersonaCardProps {
  persona: LibraryPersona
  isSelected?: boolean
  onSelect?: () => void
  onEditNickname?: (nickname: string) => void
  onRemove?: () => void
  readonly?: boolean
  className?: string
}

/**
 * PersonaAvatar - icon/image display
 */
export interface PersonaAvatarProps {
  name: string
  imageUrl?: string | null
  size?: "sm" | "md" | "lg"
  showActiveIndicator?: boolean
  isActive?: boolean
  className?: string
}
```

---

## Component Architecture

### Hierarchy

```
PersonaPicker (orchestrator)
├── Manages state via usePersonaPicker hook
├── Routes to variant based on props
│
├── Variants (shells)
│   ├── PersonaDropdown    → shadcn DropdownMenu
│   ├── PersonaPopover     → shadcn Popover
│   ├── PersonaSheet       → shadcn Sheet
│   └── PersonaInline      → div wrapper
│
├── Content (layouts)
│   ├── PersonaList        → scrollable list
│   ├── PersonaGrid        → responsive card grid
│   ├── PersonaSearch      → filter input
│   └── PersonaEmpty       → empty state
│
└── Primitives (atoms)
    ├── PersonaItem        → compact row
    ├── PersonaCard        → detail card
    ├── PersonaAvatar      → icon/image
    ├── PersonaBadges      → traits/qualities chips
    └── PersonaActions     → add/edit/remove buttons
```

### Data Flow

```
PersonaPicker
    │
    ├─ usePersonaPicker (state management)
    │   ├─ usePersonaLibrary (server state)
    │   │   └─ personaLibraryService (API calls)
    │   ├─ selection state (local)
    │   ├─ search/filter state (local)
    │   └─ UI state (open/closed)
    │
    └─ Renders variant shell
        └─ Renders content (list/grid)
            └─ Renders primitives (item/card)
```

---

## File Structure

```
src/
├── components/Persona/
│   ├── index.ts                          # Barrel exports
│   ├── types.ts                          # All type definitions
│   ├── PersonaPicker.tsx                 # Main orchestrator
│   │
│   ├── variants/
│   │   ├── index.ts
│   │   ├── PersonaDropdown.tsx
│   │   ├── PersonaPopover.tsx
│   │   ├── PersonaSheet.tsx
│   │   └── PersonaInline.tsx
│   │
│   ├── content/
│   │   ├── index.ts
│   │   ├── PersonaList.tsx
│   │   ├── PersonaGrid.tsx
│   │   ├── PersonaSearch.tsx
│   │   └── PersonaEmpty.tsx
│   │
│   └── primitives/
│       ├── index.ts
│       ├── PersonaItem.tsx
│       ├── PersonaCard.tsx
│       ├── PersonaAvatar.tsx
│       ├── PersonaBadges.tsx
│       └── PersonaActions.tsx
│
├── services/
│   └── personaLibraryService.ts
│
├── hooks/
│   ├── usePersonaLibrary.ts
│   ├── usePersonaPicker.ts
│   └── useAvailablePersonas.ts
│
└── components/Page/blocks/
    └── PersonasBlock.tsx                 # Pages integration
```

---

## Implementation Checklist

### Phase 1: Foundation

#### Step 1: Create Type Definitions

**File:** `src/components/Persona/types.ts`

**Requirements:**
- Define all interfaces listed in Type Definitions section
- Export all types
- Add JSDoc comments explaining purpose of each type

**Constraints:**
- No dependencies on specific API types in public interfaces
- Types must work for both user and agent owners

**Validation:**
- [ ] TypeScript compiles without errors
- [ ] Can create test instances of each type
- [ ] JSDoc appears in IDE tooltips

---

#### Step 2: Create personaLibraryService

**File:** `src/services/personaLibraryService.ts`

**Requirements:**
- `getLibrary(owner)` - fetch library, transform to `LibraryPersona[]`
- `getLibraryEntry(owner, entryId)` - fetch single entry with full persona data
- `addToLibrary(owner, personaId, nickname?)` - create junction entry
- `updateEntry(owner, entryId, updates)` - update nickname/active
- `removeFromLibrary(owner, entryId)` - delete junction entry
- `getAvailablePersonas(filter?)` - fetch personas not in library
- Internal `toLibraryPersona()` transform function

**Constraints:**
- Route to `UserPersonasService` or `AgentPersonasService` based on `owner.type`
- Must fetch related Persona data to populate name/description
- Follow existing service patterns (see `roomService.ts`)

**Validation:**
- [ ] `getLibrary` works for user owner
- [ ] `getLibrary` works for agent owner
- [ ] `addToLibrary` creates entry and returns transformed result
- [ ] `updateEntry` modifies nickname correctly
- [ ] `removeFromLibrary` deletes entry
- [ ] Error handling matches existing service patterns

---

#### Step 3: Create usePersonaLibrary Hook

**File:** `src/hooks/usePersonaLibrary.ts`

**Requirements:**
- Accept `{ owner: PersonaLibraryOwner, enabled?: boolean }`
- Use `useQuery` for fetching library
- Use `useMutation` for add/update/remove operations
- Invalidate queries on successful mutations
- Return: `personas`, `isLoading`, `error`, mutations, mutation states

**Query Key:** `["persona-library", owner.type, owner.id]`

**Constraints:**
- Follow `useRoomRuntime` pattern for structure
- Handle undefined owner with `enabled: false`
- Type mutations correctly

**Validation:**
- [ ] Query fetches on mount when enabled
- [ ] Query doesn't fetch when disabled
- [ ] Mutations invalidate and refetch
- [ ] Loading/error states are accurate

---

#### Step 4: Create usePersonaPicker Hook

**File:** `src/hooks/usePersonaPicker.ts`

**Requirements:**
- Accept `{ owner, mode, initialSelected?, filter? }`
- Internally use `usePersonaLibrary`
- Manage selection state (respecting single vs multiple mode)
- Manage search query state with filtering
- Manage UI open/closed state
- Return: library data + selection helpers + filtered list + UI state

**Constraints:**
- Single mode: `selected` is `string | null`
- Multiple mode: `selected` is `string[]`
- Search filters by `name` and `nickname` (case-insensitive)

**Validation:**
- [ ] Single mode allows only one selection
- [ ] Multiple mode allows toggling selections
- [ ] Search filters list correctly
- [ ] External filter prop narrows results

---

### Phase 2: Primitives

#### Step 5: Create PersonaAvatar

**File:** `src/components/Persona/primitives/PersonaAvatar.tsx`

**Requirements:**
- Use shadcn `Avatar` component as base
- Support sizes: `sm` (24px), `md` (32px), `lg` (48px)
- Fallback: mask icon (🎭) or initials from name
- Optional green dot indicator for `isActive`

**Constraints:**
- Must use existing Avatar from `@/components/ui/avatar`
- Size classes must use Tailwind

**Validation:**
- [ ] All three sizes render correctly
- [ ] Fallback shows when no imageUrl
- [ ] Active indicator positioned correctly

---

#### Step 6: Create PersonaBadges

**File:** `src/components/Persona/primitives/PersonaBadges.tsx`

**Requirements:**
- Render arrays of traits and qualities as Badge components
- `variant="compact"`: show counts only ("3 traits · 2 qualities")
- `variant="expanded"`: show all as chips
- Truncate with "+N more" tooltip when exceeding `maxVisible`
- Color differentiation: traits = blue, qualities = purple

**Constraints:**
- Use shadcn `Badge` component
- Use shadcn `Tooltip` for overflow

**Validation:**
- [ ] Compact variant shows counts
- [ ] Expanded variant shows all badges
- [ ] Truncation triggers at correct threshold
- [ ] Tooltip shows hidden items

---

#### Step 7: Create PersonaItem

**File:** `src/components/Persona/primitives/PersonaItem.tsx`

**Requirements:**
- Horizontal layout: avatar | name + description | actions
- Display nickname if present, else name
- Brief description truncated to one line
- Selection indicator based on `selectionMode`
- Hover state shows actions if `showActions`

**Constraints:**
- Clickable area triggers `onSelect`
- Actions don't bubble click to parent
- Use `cn()` for conditional classes

**Validation:**
- [ ] Renders with all props
- [ ] Nickname overrides name display
- [ ] Selection modes render correct indicator
- [ ] Actions appear on hover in edit mode

---

#### Step 8: Create PersonaCard

**File:** `src/components/Persona/primitives/PersonaCard.tsx`

**Requirements:**
- Vertical card layout with full details
- Header: avatar + name + nickname (editable)
- Body: full description + PersonaBadges
- Footer: action buttons (Select, Edit, Remove)
- `readonly` prop hides all actions

**Constraints:**
- Use shadcn `Card` component
- Edit nickname inline with `Input`
- Confirm before remove action

**Validation:**
- [ ] All persona fields display
- [ ] Nickname edit triggers callback
- [ ] Remove shows confirmation
- [ ] Readonly hides all actions

---

#### Step 9: Create PersonaActions

**File:** `src/components/Persona/primitives/PersonaActions.tsx`

**Requirements:**
- Reusable action button group
- Support actions: add, edit, remove, select
- Configurable via `actions` array prop
- Loading state per action

**Constraints:**
- Use shadcn `Button` with appropriate variants
- Icons from lucide-react

**Validation:**
- [ ] Only specified actions render
- [ ] Loading state shows spinner
- [ ] Callbacks fire correctly

---

### Phase 3: Content Components

#### Step 10: Create PersonaSearch

**File:** `src/components/Persona/content/PersonaSearch.tsx`

**Requirements:**
- Search input with magnifying glass icon
- Debounced onChange (300ms)
- Clear button when has value
- Placeholder text customizable

**Constraints:**
- Use shadcn `Input` component
- Use `useDebouncedCallback` or similar

**Validation:**
- [ ] Typing triggers debounced callback
- [ ] Clear button resets to empty
- [ ] Focus states work correctly

---

#### Step 11: Create PersonaList

**File:** `src/components/Persona/content/PersonaList.tsx`

**Requirements:**
- Scrollable container of PersonaItems
- Pass through selection props to items
- Keyboard navigation (up/down arrows, enter to select)
- Role="listbox" for accessibility

**Constraints:**
- Max height with overflow-y-auto
- Focus management for keyboard nav

**Validation:**
- [ ] List scrolls when content exceeds height
- [ ] Arrow keys navigate items
- [ ] Enter selects focused item
- [ ] Screen reader announces correctly

---

#### Step 12: Create PersonaGrid

**File:** `src/components/Persona/content/PersonaGrid.tsx`

**Requirements:**
- Responsive grid of PersonaCards
- Columns: 1 (mobile), 2 (tablet), 3 (desktop)
- Pass through selection/action props to cards

**Constraints:**
- Use CSS grid with Tailwind responsive classes
- Gap consistent with design system

**Validation:**
- [ ] Responsive breakpoints work
- [ ] Cards maintain consistent height
- [ ] Selection flows through correctly

---

#### Step 13: Create PersonaEmpty

**File:** `src/components/Persona/content/PersonaEmpty.tsx`

**Requirements:**
- Centered empty state display
- Icon + title + description
- Optional action button
- Context variants: "no personas", "no results", "no matches"

**Constraints:**
- Follow PlaceholderContent pattern from Room system
- Icon from lucide-react

**Validation:**
- [ ] Renders centered content
- [ ] Action button triggers callback
- [ ] Context changes message appropriately

---

### Phase 4: Variant Shells

#### Step 14: Create PersonaDropdown

**File:** `src/components/Persona/variants/PersonaDropdown.tsx`

**Requirements:**
- Use shadcn `Select` or `DropdownMenu`
- Trigger shows selected persona or placeholder
- Content is PersonaList with search
- Single select mode only

**Constraints:**
- Width matches trigger width minimum
- Close on selection

**Validation:**
- [ ] Trigger displays selection
- [ ] Menu opens/closes correctly
- [ ] Search filters within dropdown
- [ ] Selection updates trigger and closes

---

#### Step 15: Create PersonaPopover

**File:** `src/components/Persona/variants/PersonaPopover.tsx`

**Requirements:**
- Use shadcn `Popover`
- Customizable trigger (default: button with avatar)
- Content: search + list or grid
- Wider than dropdown for more detail

**Constraints:**
- Use `PopoverContent` with appropriate width
- Position with collision detection

**Validation:**
- [ ] Popover positions correctly
- [ ] Custom trigger works
- [ ] Content scrolls if needed
- [ ] Click outside closes

---

#### Step 16: Create PersonaSheet

**File:** `src/components/Persona/variants/PersonaSheet.tsx`

**Requirements:**
- Use shadcn `Sheet` with `side="right"`
- Header: title + close button
- Content: search + grid layout + full CRUD
- Footer: done button
- Best for `mode="manage"`

**Constraints:**
- Width: 400px desktop, full mobile
- Scroll content, fixed header/footer

**Validation:**
- [ ] Sheet slides in/out smoothly
- [ ] All CRUD operations accessible
- [ ] Done closes sheet
- [ ] Works on mobile

---

#### Step 17: Create PersonaInline

**File:** `src/components/Persona/variants/PersonaInline.tsx`

**Requirements:**
- No trigger - renders content directly
- Respects parent container width
- Layout prop switches list/grid
- Ideal for Pages blocks

**Constraints:**
- No wrapper styling that conflicts with parent
- Full width by default

**Validation:**
- [ ] Renders without extra wrappers
- [ ] List/grid toggle works
- [ ] Integrates in Pages block

---

### Phase 5: Integration

#### Step 18: Create PersonaPicker Orchestrator

**File:** `src/components/Persona/PersonaPicker.tsx`

**Requirements:**
- Accept `PersonaPickerProps`
- Use `usePersonaPicker` hook
- Route to correct variant component
- Pass all necessary props through

**Constraints:**
- Single component handles all modes/variants
- No business logic - pure orchestration

**Validation:**
- [ ] All four variants render via props
- [ ] All modes work with each variant
- [ ] Selection callbacks fire correctly
- [ ] Filter props apply

---

#### Step 19: Create PersonasBlock for Pages

**File:** `src/components/Page/blocks/PersonasBlock.tsx`

**Requirements:**
- Integrate with Pages block system
- Infer owner from page context (entityType, entityId)
- Use `PersonaPicker` with `variant="inline"`
- `mode="manage"` when page is editing, `mode="browse"` otherwise

**Block Config:**
```typescript
interface PersonasBlockConfig {
  layout: "list" | "grid"
  maxVisible: number
  showAddButton: boolean
}
```

**Constraints:**
- Follow existing block patterns (see BioBlock, LinksBlock)
- Must work for both user and agent pages

**Validation:**
- [ ] Block renders on user page
- [ ] Block renders on agent page
- [ ] Edit mode enables management
- [ ] View mode is read-only

---

#### Step 20: Create Barrel Exports and Registry Entry

**Files:**
- `src/components/Persona/index.ts`
- `src/components/Page/blocks/index.ts`
- `src/components/Page/registry/blockTypes.ts`

**Requirements:**
- Export all public components from Persona index
- Export PersonasBlock from blocks index
- Add PersonasBlock to block type registry with icon, label, description

**Constraints:**
- Only export what's needed publicly
- Registry entry matches existing pattern

**Validation:**
- [ ] `import { PersonaPicker } from "@/components/Persona"` works
- [ ] PersonasBlock appears in block palette
- [ ] Can add PersonasBlock to a page in edit mode

---

## Verification Checklist

### Phase 1 Complete
- [ ] All types defined and exported
- [ ] Service handles both owner types correctly
- [ ] `usePersonaLibrary` fetches and mutates
- [ ] `usePersonaPicker` manages all state correctly

### Phase 2 Complete
- [ ] All primitives render in isolation
- [ ] Primitives handle missing/null data gracefully
- [ ] Styling consistent with design system

### Phase 3 Complete
- [ ] List and grid layouts render correctly
- [ ] Search debounces and filters
- [ ] Empty states show appropriate messages
- [ ] Keyboard navigation works in list

### Phase 4 Complete
- [ ] Dropdown opens/closes, selects correctly
- [ ] Popover positions and scrolls correctly
- [ ] Sheet slides and manages correctly
- [ ] Inline embeds without style conflicts

### Phase 5 Complete
- [ ] PersonaPicker routes to all variants
- [ ] PersonasBlock works on user pages
- [ ] PersonasBlock works on agent pages
- [ ] All exports resolve correctly

### Final Verification
- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds
- [ ] Manual test: user persona library CRUD
- [ ] Manual test: agent persona library CRUD
- [ ] Manual test: dropdown selection in mock dialog
- [ ] Manual test: PersonasBlock on page in view/edit modes
- [ ] No console errors or warnings

---

## Dependencies

### shadcn Components (verify installed)

```bash
npx shadcn@latest add avatar
npx shadcn@latest add badge
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add dropdown-menu
npx shadcn@latest add input
npx shadcn@latest add popover
npx shadcn@latest add select
npx shadcn@latest add sheet
npx shadcn@latest add tooltip
```

### External Packages

- None required for MVP
- Optional: `use-debounce` for search (or implement simple debounce)

---

## Out of Scope (Future Enhancements)

- Persona creation/editing forms (separate feature)
- Persona sharing between users
- Persona marketplace/discovery
- Story compatibility scoring
- Drag-drop reordering of library
- Persona versioning/history
- Trait/quality inline editing
- Bulk operations (select all, bulk remove)
