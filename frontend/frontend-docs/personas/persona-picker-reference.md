# PersonaPicker Engineering Reference Card

> Quick reference for integrating, extending, or debugging the PersonaPicker component system.

---

## File Structure

```
src/
├── components/Persona/
│   ├── index.ts                    # Public API (exports PersonaPicker + types)
│   ├── PersonaPicker.tsx           # Orchestrator (routes to variants)
│   ├── types.ts                    # All TypeScript interfaces
│   ├── primitives/                 # Atomic display components
│   │   ├── PersonaAvatar.tsx       #   Avatar with active indicator
│   │   ├── PersonaItem.tsx         #   Compact single-line row
│   │   ├── PersonaCard.tsx         #   Expanded card with nickname editing
│   │   ├── PersonaBadges.tsx       #   Traits/qualities/domains display
│   │   └── PersonaActions.tsx      #   Add/edit/remove icon buttons
│   ├── content/                    # Composite layout components
│   │   ├── PersonaSearch.tsx       #   Debounced search input
│   │   ├── PersonaList.tsx         #   Vertical list of PersonaItems
│   │   ├── PersonaGrid.tsx         #   Card grid of PersonaCards
│   │   └── PersonaEmpty.tsx        #   Empty state messaging
│   └── variants/                   # Presentation shells
│       ├── PersonaDropdown.tsx     #   Compact select-style popover
│       ├── PersonaPopover.tsx      #   Wider popover with list/grid toggle
│       ├── PersonaSheet.tsx        #   Full side panel
│       └── PersonaInline.tsx       #   Embedded directly in page
├── hooks/
│   ├── usePersonaLibrary.ts        # Data layer (TanStack Query)
│   └── usePersonaPicker.ts         # State layer (selection + search + UI)
├── services/
│   └── personaLibraryService.ts    # API abstraction (owner-agnostic)
└── components/Page/blocks/
    └── PersonasBlock.tsx           # Pages block integration
```

---

## Quick Usage

### Basic Dropdown (select one persona)

```tsx
import { PersonaPicker } from "@/components/Persona"

<PersonaPicker
  owner={{ type: "user", id: userId, name: "User" }}
  mode="select-single"
  variant="dropdown"
  onSelect={(personaId) => console.log(personaId)}
/>
```

### Multi-select Popover (grid layout)

```tsx
<PersonaPicker
  owner={{ type: "agent", id: agentId, name: agent.name }}
  mode="select-multiple"
  variant="popover"
  layout="grid"
  selected={selectedIds}
  onSelect={(ids) => setSelectedIds(ids as string[])}
/>
```

### Management Sheet (add/edit/remove)

```tsx
<PersonaPicker
  owner={{ type: "user", id: userId, name: "Your" }}
  mode="manage"
  variant="sheet"
/>
```

### Inline Browse (read-only, limited)

```tsx
<PersonaPicker
  owner={{ type: "agent", id: agentId, name: agent.name }}
  mode="browse"
  variant="inline"
  layout="grid"
  maxVisible={6}
/>
```

### With Custom Trigger

```tsx
<PersonaPicker
  owner={owner}
  mode="select-single"
  variant="dropdown"
  trigger={<Button variant="ghost">Choose Persona</Button>}
  placeholder="Pick one..."
/>
```

### With External Filter

```tsx
<PersonaPicker
  owner={owner}
  mode="select-single"
  variant="popover"
  filter={{ isActive: true, domains: ["creative"] }}
/>
```

---

## Key Types

| Type | Purpose |
|------|---------|
| `PersonaLibraryOwner` | `{ type: "user" | "agent", id: string, name: string }` |
| `LibraryPersona` | Unified view model (junction + persona data merged) |
| `PersonaPickerMode` | `"select-single" | "select-multiple" | "manage" | "browse"` |
| `PersonaPickerVariant` | `"dropdown" | "popover" | "sheet" | "inline"` |
| `PersonaFilter` | `{ isActive?, domains?, searchQuery? }` |
| `PersonaPickerProps` | Full prop interface for the orchestrator |

---

## Mode Behavior Matrix

| Mode | Selection UI | Edit Actions | Remove Actions | Search |
|------|-------------|-------------|----------------|--------|
| `select-single` | Radio | No | No | Yes |
| `select-multiple` | Checkbox | No | No | Yes |
| `manage` | None | Yes (nickname) | Yes | Yes |
| `browse` | None | No | No | Yes |

---

## Data Flow

```
PersonaPicker (props: owner, mode, variant)
    │
    ▼
usePersonaPicker (adds: selection, search, UI state)
    │
    ▼
usePersonaLibrary (adds: TanStack Query caching, mutations)
    │
    ▼
PersonaLibraryService (API calls, joins junction + persona data)
    │
    ▼
UserPersonasService / AgentPersonasService + PersonasService (generated client)
```

### Query Keys

```ts
["persona-library", ownerType, ownerId]
// Example: ["persona-library", "user", "abc-123"]
```

Mutations auto-invalidate the library query on success.

---

## Extending the System

### Adding a New Variant

1. Create `src/components/Persona/variants/PersonaMyVariant.tsx`
2. Accept `PersonaContentProps` + variant-specific props
3. Compose from `content/` components (PersonaSearch, PersonaList/Grid, PersonaEmpty)
4. Add to `PersonaPickerVariant` union in `types.ts`
5. Add case in `PersonaPicker.tsx` switch statement
6. Export from `variants/index.ts`

### Adding a New Primitive

1. Create in `primitives/` directory
2. Define props interface in `types.ts`
3. Export from `primitives/index.ts`
4. If publicly useful, also export from top-level `index.ts`

### Using the Hook Directly (advanced)

```tsx
import { usePersonaPicker } from "@/hooks/usePersonaPicker"

function MyCustomPersonaUI() {
  const picker = usePersonaPicker({
    owner: { type: "user", id: userId, name: "User" },
    mode: "select-single",
  })

  return (
    <div>
      {picker.personas.map((p) => (
        <button
          key={p.personaId}
          onClick={() => picker.selectPersona(p.personaId)}
          data-selected={picker.selectedIds.includes(p.personaId)}
        >
          {p.nickname || p.name}
        </button>
      ))}
    </div>
  )
}
```

### Using the Data Hook Only (no UI state)

```tsx
import { usePersonaLibrary } from "@/hooks/usePersonaLibrary"

function PersonaCount({ owner }) {
  const { personas, isLoading } = usePersonaLibrary({ owner })
  if (isLoading) return <Skeleton />
  return <Badge>{personas.length} personas</Badge>
}
```

---

## Pages Block Integration

The `PersonasBlock` is registered in the block palette and renders `PersonaPicker` with `variant="inline"`.

### Block Config Schema

```ts
{
  layout: "list" | "grid"   // Default: "grid"
  maxVisible: number         // Default: 6
  showAddButton: boolean     // Default: true
}
```

### How It Maps

| Page State | PersonaPicker Mode |
|------------|-------------------|
| Viewing | `"browse"` |
| Editing | `"manage"` |

### Adding to a Template

In `registry/pageTemplates.ts`:

```ts
{
  type: "personas",
  column: "primary",
  order: 5,
  config: { layout: "grid", maxVisible: 6, showAddButton: true },
}
```

---

## Service API

```ts
import { PersonaLibraryService } from "@/services/personaLibraryService"

// Fetch library (joins junction entries + persona details)
await PersonaLibraryService.getLibrary(owner)
// Returns: LibraryPersona[]

// Add persona to library
await PersonaLibraryService.addToLibrary(owner, personaId, nickname?)
// Returns: LibraryPersona

// Update entry (nickname, active status)
await PersonaLibraryService.updateEntry(owner, entryId, { nickname?, is_active? })

// Remove from library
await PersonaLibraryService.removeFromLibrary(owner, entryId)

// Get all available personas (for "add" UI)
await PersonaLibraryService.getAvailablePersonas()
// Returns: PersonaPublic[]
```

---

## Common Patterns

### Controlled Selection

```tsx
const [selected, setSelected] = useState<string | null>(null)

<PersonaPicker
  owner={owner}
  mode="select-single"
  variant="dropdown"
  selected={selected}
  onSelect={(id) => setSelected(id as string)}
/>
```

### Pre-filtered by Domain

```tsx
<PersonaPicker
  owner={owner}
  mode="select-single"
  variant="popover"
  filter={{ domains: ["technical", "creative"], isActive: true }}
/>
```

### Listening to Library Changes

```tsx
const { personas, isLoading } = usePersonaLibrary({ owner })

useEffect(() => {
  // React to library changes (e.g., update parent form)
  onChange(personas.map((p) => p.personaId))
}, [personas])
```

---

## Debugging Tips

| Symptom | Check |
|---------|-------|
| Empty list despite data | Verify `owner.type` matches actual owner (`"user"` vs `"agent"`) |
| Stale data after mutation | Query key includes `[owner.type, owner.id]` — ensure owner is stable |
| No search results | Filter combines `externalFilter.searchQuery` OR local `searchQuery` |
| Actions not showing | Only visible in `mode="manage"` — check `showActions` derivation |
| Sheet won't open | `variant="sheet"` requires external open state; use `isOpen`/`setIsOpen` from hook |
| PersonasBlock blank | Ensure `entityType` is `"user"` or `"agent"` (not other entity types) |
