# Pages System Design

> **For Claude:** This is a design document. Use superpowers:writing-plans to create an implementation plan from this design.

**Goal:** Create a generic, extensible Page system for entity profiles (Users, Agents, Teams, etc.) with modular content blocks, user-defined data blocks, and MySpace-inspired customization.

**Date:** 2026-01-19

---

## 1. Page Architecture Overview

### Core Concept: Page as Entity Profile Container

A Page is a customizable profile for any entity (User, Agent, Team, Project, etc.). Like Rooms, Pages use a **modular block system** where content blocks can be added, removed, and arranged.

```
┌─────────────────────────────────────────────────────────────┐
│ PageShell                                                   │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ PageHeader (metadata bar: slug, timestamps, actions)    │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ PageLayout (block arrangement - like RoomLayout)        │ │
│ │ ┌─────────────────────┐ ┌─────────────────────────────┐ │ │
│ │ │ Primary Column      │ │ Auxiliary Column            │ │ │
│ │ │ ┌─────────────────┐ │ │ ┌─────────────────────────┐ │ │ │
│ │ │ │ ProfileImage    │ │ │ │ Contact                 │ │ │ │
│ │ │ ├─────────────────┤ │ │ ├─────────────────────────┤ │ │ │
│ │ │ │ Identity        │ │ │ │ Links                   │ │ │ │
│ │ │ ├─────────────────┤ │ │ └─────────────────────────┘ │ │ │
│ │ │ │ Bio             │ │ │                             │ │ │
│ │ │ ├─────────────────┤ │ │                             │ │ │
│ │ │ │ Relationships   │ │ │                             │ │ │
│ │ │ └─────────────────┘ │ │                             │ │ │
│ │ └─────────────────────┘ └─────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Key Similarities to Room System

- `PageShell` ↔ `RoomShell` (outer container)
- `PageLayout` ↔ `RoomLayout` (block/panel arrangement)
- `BlockContainer` ↔ `PanelContainer` (wrapper for content)
- Resizable, rearrangeable sections
- Preset templates + custom composition

### Key Differences from Room System

- Blocks are **content-focused** (display) rather than **interaction-focused** (chat, agents)
- Pages are **public-facing** profiles, Rooms are **collaborative workspaces**
- Pages have a **slug/URL** for direct access

---

## 2. Content Block Types

### Block Schema

```typescript
interface PageBlock {
  id: string
  type: BlockType
  position: { column: 'primary' | 'auxiliary', order: number }
  config: BlockConfig  // Type-specific settings
  visibility: 'visible' | 'hidden'
}

type BlockType =
  | 'profileImage'
  | 'identity'
  | 'bio'
  | 'contact'
  | 'links'
  | 'relationships'
  | 'activityFeed'
  | 'gallery'
  | 'dataTable'      // User-defined
  | 'chart'          // User-defined
  | 'customEmbed'    // Future
```

### Standard Block Definitions

| Block | Config Options | Renders |
|-------|----------------|---------|
| `profileImage` | shape (circle/square), size (sm/md/lg) | Avatar with optional edit overlay |
| `identity` | showTagline (bool) | Name + optional tagline |
| `bio` | maxLength, allowRichText | Rich text editor / display |
| `contact` | fields to show (email, phone, etc.) | Contact info with copy buttons |
| `links` | icon style, layout (list/grid) | Social links with icons |
| `relationships` | groupByType, maxVisible | Card grid of related entities |
| `activityFeed` | maxItems, filterTypes | Timeline of recent actions |
| `gallery` | columns, lightbox | Image grid with viewer |

### Block Container Structure

```
┌─────────────────────────────────┐
│ BlockContainer                  │
│ ┌─────────────────────────────┐ │
│ │ Header: Title + Actions     │ │  ← Optional (edit, hide, move)
│ ├─────────────────────────────┤ │
│ │ Content: Block-specific     │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

## 3. User-Defined Blocks

### Core Requirement

Users can add configurable data blocks that wrap existing UI components (DataTable, Chart) with custom data sources.

### Data Block Definitions

```typescript
// registry/blockTypes.ts
export const blockTypes: BlockTypeDefinition[] = [
  // ... standard blocks ...

  {
    id: 'dataTable',
    label: 'Data Table',
    description: 'Display any data as a table',
    component: DataTableBlock,
    configSchema: {
      title: { type: 'string', label: 'Block Title' },
      dataSource: {
        type: 'select',
        label: 'Data Source',
        options: ['favorites', 'myAgents', 'myRooms', 'custom']
      },
      columns: { type: 'columnConfig', label: 'Columns to Show' },
      maxRows: { type: 'number', label: 'Max Rows', default: 10 },
    }
  },
  {
    id: 'chart',
    label: 'Chart',
    description: 'Visualize data as a chart',
    component: ChartBlock,
    configSchema: {
      title: { type: 'string', label: 'Block Title' },
      chartType: { type: 'select', options: ['area', 'bar', 'line', 'pie'] },
      dataSource: { type: 'select', options: ['activity', 'custom'] },
    }
  },
]
```

### DataTableBlock Implementation Pattern

```typescript
// blocks/DataTableBlock.tsx
import { DataTable } from "@/components/ui/data-table"
import { BlockContainer } from "../primitives/BlockContainer"

interface DataTableBlockConfig {
  title: string
  dataSource: string
  columns: ColumnConfig[]
  maxRows: number
}

const dataSourceFetchers: Record<string, () => Promise<any[]>> = {
  favorites: () => UserService.getFavorites(),
  myAgents: () => AgentService.getMyAgents(),
  myRooms: () => RoomService.getMyRooms(),
  custom: (config) => CustomDataService.fetch(config.customEndpoint),
}

export function DataTableBlock({ config }: { config: DataTableBlockConfig }) {
  const { data, isLoading } = useQuery({
    queryKey: ['blockData', config.dataSource],
    queryFn: () => dataSourceFetchers[config.dataSource](),
  })

  const columns = buildColumns(config.columns)

  return (
    <BlockContainer title={config.title}>
      <DataTable
        columns={columns}
        data={data?.slice(0, config.maxRows) || []}
        isLoading={isLoading}
      />
    </BlockContainer>
  )
}
```

### User Flow for Adding Data Block

```
Add Block → Select "Data Table" → Configure:
  - Title: "My Favorite Records"
  - Data Source: favorites
  - Columns: [Name, Type, Status]
  - Max Rows: 10
→ Block appears on page
```

---

## 4. Entity & Relationship Registries

### Core Principle

Blocks never hardcode entity or relationship types. Types are defined in registries that can be extended without modifying components.

### Entity Type Registry

```typescript
// registry/entityTypes.ts
export interface EntityTypeDefinition {
  id: string                    // 'user', 'agent', 'team', etc.
  label: string                 // Display name
  labelPlural: string           // For lists
  icon: LucideIcon              // Visual identifier
  color: string                 // Theme color (tailwind class)
  pageRoutePattern: string      // e.g., '/u/:slug', '/agent/:id'
}

export const entityTypes: EntityTypeDefinition[] = [
  { id: 'user', label: 'User', labelPlural: 'Users', icon: User, color: 'blue', pageRoutePattern: '/u/:slug' },
  { id: 'agent', label: 'Agent', labelPlural: 'Agents', icon: Bot, color: 'purple', pageRoutePattern: '/agent/:id' },
  { id: 'team', label: 'Team', labelPlural: 'Teams', icon: Users, color: 'green', pageRoutePattern: '/team/:slug' },
  { id: 'room', label: 'Room', labelPlural: 'Rooms', icon: MessageSquare, color: 'orange', pageRoutePattern: '/r/:id' },
  // Add new types here - no component changes needed
]
```

### Relationship Type Registry

```typescript
// registry/relationshipTypes.ts
export interface RelationshipTypeDefinition {
  id: string                    // 'member', 'owner', 'creator', etc.
  label: string                 // Display label
  inverseId?: string            // For bidirectional (member ↔ has_member)
  validPairs: Array<{           // Which entity combinations are valid
    source: string              // Source entity type id
    target: string              // Target entity type id
  }>
}

export const relationshipTypes: RelationshipTypeDefinition[] = [
  { id: 'member', label: 'Member', inverseId: 'has_member', validPairs: [{ source: 'user', target: 'team' }] },
  { id: 'owner', label: 'Owner', inverseId: 'owned_by', validPairs: [{ source: 'user', target: 'team' }, { source: 'user', target: 'agent' }] },
  { id: 'creator', label: 'Creator', inverseId: 'created_by', validPairs: [{ source: 'user', target: 'agent' }] },
  { id: 'participant', label: 'Participant', validPairs: [{ source: 'user', target: 'room' }, { source: 'agent', target: 'room' }] },
  // Add new relationships here
]
```

### Generic EntityCard Component

```typescript
interface EntityCardProps {
  entity: {
    id: string
    typeId: string           // Lookup in registry
    name: string
    avatarUrl?: string
    badges?: string[]
  }
  relationship?: {
    typeId: string           // Lookup in registry
  }
  onClick?: () => void
}

function EntityCard({ entity, relationship, onClick }: EntityCardProps) {
  const entityType = getEntityType(entity.typeId)  // Registry lookup
  const relType = relationship ? getRelationshipType(relationship.typeId) : null

  // Render using registry data - no hardcoded types
}
```

---

## 5. Relationships Block

### Display Format: Card Grid

```
┌─────────────────────────────────────────────────────┐
│ Relationships                              [+ Add]  │
├─────────────────────────────────────────────────────┤
│ Teams (2)                                           │
│ ┌───────────────┐ ┌───────────────┐                │
│ │ 👥 Alpha Team │ │ 👥 Beta Squad │                │
│ │ Team · Member │ │ Team · Owner  │                │
│ └───────────────┘ └───────────────┘                │
│                                                     │
│ Agents (3)                                          │
│ ┌───────────────┐ ┌───────────────┐ ┌─────────────┐│
│ │ 🤖 Claude     │ │ 🤖 Summarizer │ │ 🤖 Coder    ││
│ │ Agent·Creator │ │ Agent·Creator │ │ Agent·Collab││
│ └───────────────┘ └───────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────┘
```

### Entity Card Structure

```
┌─────────────────────────────────────┐
│ EntityCard                          │
│ ┌─────┐                             │
│ │ 👤  │  Entity Name                │
│ │     │  Entity Type · Relationship │
│ └─────┘                             │
│ Optional: badges, status indicator  │
└─────────────────────────────────────┘
```

### Click Behavior

- Clicking an EntityCard navigates to that entity's Page
- Creates a web of interconnected profiles

### Future Enhancement

- Graph/network view toggle showing visual connections

---

## 6. Page Templates

### Template Schema

```typescript
// registry/pageTemplates.ts
export interface PageTemplate {
  id: string
  label: string
  description: string
  forEntityTypes: string[]
  defaultBlocks: Array<{
    type: BlockType
    column: 'primary' | 'auxiliary'
    order: number
    config: Partial<BlockConfig>
  }>
}
```

### Preset Templates

**Standard Profile:**
```typescript
{
  id: 'standard',
  label: 'Standard Profile',
  description: 'Classic profile layout with image, bio, and sidebar',
  forEntityTypes: ['user', 'agent', 'team'],
  defaultBlocks: [
    { type: 'profileImage', column: 'primary', order: 0, config: { shape: 'circle', size: 'lg' } },
    { type: 'identity', column: 'primary', order: 1, config: { showTagline: true } },
    { type: 'bio', column: 'primary', order: 2, config: {} },
    { type: 'relationships', column: 'primary', order: 3, config: { groupByType: true } },
    { type: 'contact', column: 'auxiliary', order: 0, config: {} },
    { type: 'links', column: 'auxiliary', order: 1, config: { layout: 'list' } },
  ]
}
```

**Minimal:**
```typescript
{
  id: 'minimal',
  label: 'Minimal',
  description: 'Clean single-column layout',
  forEntityTypes: ['user', 'agent', 'team'],
  defaultBlocks: [
    { type: 'profileImage', column: 'primary', order: 0, config: { shape: 'circle', size: 'md' } },
    { type: 'identity', column: 'primary', order: 1, config: { showTagline: true } },
    { type: 'bio', column: 'primary', order: 2, config: {} },
    { type: 'links', column: 'primary', order: 3, config: { layout: 'grid' } },
  ]
}
```

**Showcase:**
```typescript
{
  id: 'showcase',
  label: 'Showcase',
  description: 'Gallery-focused with large visuals',
  forEntityTypes: ['user', 'team'],
  defaultBlocks: [
    { type: 'profileImage', column: 'primary', order: 0, config: { shape: 'square', size: 'lg' } },
    { type: 'identity', column: 'primary', order: 1, config: { showTagline: true } },
    { type: 'gallery', column: 'primary', order: 2, config: { columns: 3 } },
    { type: 'bio', column: 'auxiliary', order: 0, config: {} },
    { type: 'links', column: 'auxiliary', order: 1, config: {} },
  ]
}
```

---

## 7. Layout & Responsive Behavior

### Desktop (≥1024px)

Two-column resizable layout.

### Tablet (768-1023px)

Auxiliary column becomes collapsible drawer.

### Mobile (<768px)

Single column, blocks stack vertically.

### Edit Mode

When page owner is viewing their page, they can toggle Edit Mode:

```
┌─────────────────────────────────────────────────────┐
│ Page Header                    [Edit Mode: ON 🔘]   │
├─────────────────────────────────────────────────────┤
│ ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                           │
│ │ ⋮⋮ ProfileImage  [×] │  ← Drag handle, remove    │
│ └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                           │
│ ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                           │
│ │ ⋮⋮ Identity      [⚙] │  ← Config button          │
│ └─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                           │
│                                                     │
│        [ + Add Block ]                              │
└─────────────────────────────────────────────────────┘
```

- Blocks show drag handles for reordering
- Config button opens block settings
- Remove button hides block (doesn't delete data)
- "Add Block" shows available block types

---

## 8. Routing & Page Header

### URL Structure

```
/u/:slug          → User page (e.g., /u/alice)
/agent/:id        → Agent page (e.g., /agent/abc-123)
/team/:slug       → Team page (e.g., /team/alpha-squad)
```

### Route Implementation

```typescript
// All entity pages use the same component, differentiated by entityType param
<PageShell entityType="user" entityId={slug} />
```

### Page Header Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ┌────────────────────────────────────┐  ┌─────────────────────────────┐ │
│ │ Left: Breadcrumb + Meta            │  │ Right: Actions              │ │
│ │                                    │  │                             │ │
│ │ Users / Alice                      │  │ [Share] [Edit] [⋮]         │ │
│ │ Created Jan 15 · Updated 2h ago    │  │                             │ │
│ └────────────────────────────────────┘  └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### Header Elements

| Element | Description |
|---------|-------------|
| **Breadcrumb** | Entity type plural → Entity name |
| **Timestamps** | Created date + relative last updated |
| **Share** | Copy link, social share options |
| **Edit** | Toggle edit mode (owner only) |
| **Menu (⋮)** | Change template, Export, Delete (owner), Report (others) |

### Permissions

| Viewer | Can See | Can Edit |
|--------|---------|----------|
| Owner | Full page | All blocks + settings |
| Logged-in user | Public blocks | Nothing |
| Anonymous | Public blocks (if page is public) | Nothing |

---

## 9. File Organization

### New Component Structure

```
frontend/src/components/
├── Page/                           # NEW - Generic page system
│   ├── PageShell.tsx              # Outer container
│   ├── PageHeader.tsx             # Header with breadcrumb, actions
│   ├── PageLayout.tsx             # Block arrangement
│   ├── blocks/
│   │   ├── ProfileImageBlock.tsx
│   │   ├── IdentityBlock.tsx
│   │   ├── BioBlock.tsx
│   │   ├── ContactBlock.tsx
│   │   ├── LinksBlock.tsx
│   │   ├── RelationshipsBlock.tsx
│   │   ├── ActivityFeedBlock.tsx
│   │   ├── GalleryBlock.tsx
│   │   ├── DataTableBlock.tsx     # User-defined
│   │   ├── ChartBlock.tsx         # User-defined
│   │   └── index.ts
│   ├── primitives/
│   │   ├── BlockContainer.tsx
│   │   ├── EntityCard.tsx
│   │   └── index.ts
│   ├── registry/
│   │   ├── entityTypes.ts
│   │   ├── relationshipTypes.ts
│   │   ├── blockTypes.ts
│   │   ├── pageTemplates.ts
│   │   └── dataSources.ts
│   └── index.ts
│
├── Room/                           # Existing
│   └── ...
│
└── shared/                         # NEW - Shared between Room & Page
    ├── ResizableLayout.tsx
    └── EditModeToggle.tsx
```

### Route Structure

```
frontend/src/routes/_layout/
├── u.$slug.tsx                    # User pages
├── agent.$agentId.tsx             # Agent pages
├── team.$slug.tsx                 # Team pages
├── admin.tsx                      # Keep for superuser management
└── ...
```

### Shared Components (DRY)

| Shared Component | Used By |
|------------------|---------|
| `ResizableLayout` | `RoomLayout`, `PageLayout` |
| `BlockContainer` / `PanelContainer` | Unify into single component |
| `EntityCard` | `RelationshipsBlock`, `ParticipantStack`, Room cards |
| `ActionBar` | Both Page and Room headers |

---

## 10. Summary

### Core Requirements

1. **Registry-driven types** - All entity, relationship, and block types defined in extensible registries
2. **User-defined blocks** - Users can add DataTable/Chart blocks with custom configuration
3. **Configurable data sources** - Blocks can pull from favorites, myAgents, myRooms, or custom endpoints
4. **Shared primitives** - Reuse components between Page and Room systems
5. **Responsive layout** - Desktop columns, mobile stacking
6. **Edit mode** - Owners can rearrange and configure blocks

### Key Components

| Layer | Components |
|-------|------------|
| **Routes** | `u.$slug`, `agent.$agentId`, `team.$slug` |
| **Shell** | `PageShell` → `PageHeader` + `PageLayout` |
| **Standard Blocks** | `ProfileImageBlock`, `IdentityBlock`, `BioBlock`, `ContactBlock`, `LinksBlock`, `RelationshipsBlock`, `ActivityFeedBlock`, `GalleryBlock` |
| **Data Blocks** | `DataTableBlock`, `ChartBlock` (configurable, user-defined) |
| **Primitives** | `BlockContainer`, `EntityCard` |
| **Registry** | `entityTypes`, `relationshipTypes`, `blockTypes`, `pageTemplates`, `dataSources` |

### Extensibility

| To Add... | Modify... | Components Changed |
|-----------|-----------|-------------------|
| New entity type | `entityTypes` registry | None |
| New relationship type | `relationshipTypes` registry | None |
| New standard block | `blockTypes` registry + create component | Add one component |
| New data block | `blockTypes` registry + create wrapper | Add one component |
| New data source | `dataSources` registry | None |
| New template | `pageTemplates` registry | None |

### Design Principles

- **Registry-driven** - Types are data, not code
- **Composition over inheritance** - Blocks are interchangeable
- **DRY** - Share primitives between Page and Room
- **Progressive enhancement** - Start minimal, add graph view later
- **MySpace-inspired** - Structured freedom with sensible defaults
