# Pages System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a generic, extensible Page system for entity profiles (Users, Agents, Teams) with modular content blocks, user-defined data blocks, and registry-driven architecture.

**Architecture:** Pages use a shell-layout-block architecture (like Rooms) with type registries for entities, relationships, and blocks. All blocks are configurable and can be placed in either column. Data blocks allow user-defined DataTable/Chart components with custom data sources.

**Tech Stack:** React 19, TypeScript, TanStack Query, TanStack Router, shadcn/ui (ResizablePanelGroup, Tabs, Popover), Lucide icons

---

## Phase 1: Registries (Foundation)

The registry pattern is the core of extensibility. Types are defined as data, not hardcoded in components.

---

### Task 1: Create Entity Types Registry

**Files:**
- Create: `src/components/Page/registry/entityTypes.ts`

**Step 1: Create the registry file**

```typescript
// src/components/Page/registry/entityTypes.ts
import { Bot, MessageSquare, User, Users, type LucideIcon } from "lucide-react"

/**
 * Entity type definition for the registry.
 * Add new entity types here - no component changes needed.
 */
export interface EntityTypeDefinition {
  /** Unique identifier (e.g., 'user', 'agent') */
  id: string
  /** Singular display name */
  label: string
  /** Plural display name for lists */
  labelPlural: string
  /** Lucide icon component */
  icon: LucideIcon
  /** Tailwind color class (e.g., 'blue', 'purple') */
  color: string
  /** Route pattern for this entity's page */
  pageRoutePattern: string
}

export const entityTypes: EntityTypeDefinition[] = [
  {
    id: "user",
    label: "User",
    labelPlural: "Users",
    icon: User,
    color: "blue",
    pageRoutePattern: "/u/:slug",
  },
  {
    id: "agent",
    label: "Agent",
    labelPlural: "Agents",
    icon: Bot,
    color: "purple",
    pageRoutePattern: "/agent/:id",
  },
  {
    id: "team",
    label: "Team",
    labelPlural: "Teams",
    icon: Users,
    color: "green",
    pageRoutePattern: "/team/:slug",
  },
  {
    id: "room",
    label: "Room",
    labelPlural: "Rooms",
    icon: MessageSquare,
    color: "orange",
    pageRoutePattern: "/r/:id",
  },
]

/**
 * Get entity type definition by ID
 */
export function getEntityType(id: string): EntityTypeDefinition | undefined {
  return entityTypes.find((e) => e.id === id)
}

/**
 * Get entity type definition by ID, throws if not found
 */
export function getEntityTypeOrThrow(id: string): EntityTypeDefinition {
  const entityType = getEntityType(id)
  if (!entityType) {
    throw new Error(`Unknown entity type: ${id}`)
  }
  return entityType
}
```

**Step 2: Verify the file compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/entityTypes.ts 2>&1 | head -20`
Expected: No errors (or create the directory first if needed)

**Step 3: Commit**

```bash
git add src/components/Page/registry/entityTypes.ts
git commit -m "feat(pages): add entity types registry"
```

---

### Task 2: Create Relationship Types Registry

**Files:**
- Create: `src/components/Page/registry/relationshipTypes.ts`

**Step 1: Create the registry file**

```typescript
// src/components/Page/registry/relationshipTypes.ts

/**
 * Valid source-target pair for a relationship type.
 */
export interface RelationshipPair {
  source: string // Entity type ID
  target: string // Entity type ID
}

/**
 * Relationship type definition for the registry.
 * Add new relationship types here - no component changes needed.
 */
export interface RelationshipTypeDefinition {
  /** Unique identifier */
  id: string
  /** Display label */
  label: string
  /** Inverse relationship ID for bidirectional relationships */
  inverseId?: string
  /** Valid entity type combinations */
  validPairs: RelationshipPair[]
}

export const relationshipTypes: RelationshipTypeDefinition[] = [
  {
    id: "member",
    label: "Member",
    inverseId: "has_member",
    validPairs: [{ source: "user", target: "team" }],
  },
  {
    id: "has_member",
    label: "Has Member",
    inverseId: "member",
    validPairs: [{ source: "team", target: "user" }],
  },
  {
    id: "owner",
    label: "Owner",
    inverseId: "owned_by",
    validPairs: [
      { source: "user", target: "team" },
      { source: "user", target: "agent" },
    ],
  },
  {
    id: "owned_by",
    label: "Owned By",
    inverseId: "owner",
    validPairs: [
      { source: "team", target: "user" },
      { source: "agent", target: "user" },
    ],
  },
  {
    id: "creator",
    label: "Creator",
    inverseId: "created_by",
    validPairs: [{ source: "user", target: "agent" }],
  },
  {
    id: "created_by",
    label: "Created By",
    inverseId: "creator",
    validPairs: [{ source: "agent", target: "user" }],
  },
  {
    id: "participant",
    label: "Participant",
    validPairs: [
      { source: "user", target: "room" },
      { source: "agent", target: "room" },
    ],
  },
]

/**
 * Get relationship type definition by ID
 */
export function getRelationshipType(
  id: string
): RelationshipTypeDefinition | undefined {
  return relationshipTypes.find((r) => r.id === id)
}

/**
 * Check if a relationship is valid between two entity types
 */
export function isValidRelationship(
  relationshipId: string,
  sourceTypeId: string,
  targetTypeId: string
): boolean {
  const relType = getRelationshipType(relationshipId)
  if (!relType) return false
  return relType.validPairs.some(
    (pair) => pair.source === sourceTypeId && pair.target === targetTypeId
  )
}
```

**Step 2: Verify the file compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/relationshipTypes.ts 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/registry/relationshipTypes.ts
git commit -m "feat(pages): add relationship types registry"
```

---

### Task 3: Create Block Types Registry

**Files:**
- Create: `src/components/Page/registry/blockTypes.ts`

**Step 1: Create the registry file**

```typescript
// src/components/Page/registry/blockTypes.ts
import type { ComponentType } from "react"

/**
 * Block type IDs
 */
export type BlockType =
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

/**
 * Schema field types for block configuration
 */
export type ConfigFieldType =
  | "string"
  | "number"
  | "boolean"
  | "select"
  | "columnConfig"

/**
 * Configuration field schema
 */
export interface ConfigFieldSchema {
  type: ConfigFieldType
  label: string
  default?: unknown
  options?: string[] // For 'select' type
}

/**
 * Block type definition for the registry.
 */
export interface BlockTypeDefinition {
  /** Unique identifier */
  id: BlockType
  /** Display label */
  label: string
  /** Description for block picker */
  description: string
  /** Component to render (lazy-loaded) */
  component: ComponentType<{ config: Record<string, unknown> }>
  /** Configuration schema for settings UI */
  configSchema: Record<string, ConfigFieldSchema>
  /** Whether this is a user-defined data block */
  isDataBlock?: boolean
}

// Placeholder components - will be replaced with actual implementations
const PlaceholderBlock = ({ config }: { config: Record<string, unknown> }) => (
  <div>Block: {JSON.stringify(config)}</div>
)

export const blockTypes: BlockTypeDefinition[] = [
  {
    id: "profileImage",
    label: "Profile Image",
    description: "Avatar with optional edit overlay",
    component: PlaceholderBlock,
    configSchema: {
      shape: {
        type: "select",
        label: "Shape",
        options: ["circle", "square"],
        default: "circle",
      },
      size: {
        type: "select",
        label: "Size",
        options: ["sm", "md", "lg"],
        default: "lg",
      },
    },
  },
  {
    id: "identity",
    label: "Identity",
    description: "Name and optional tagline",
    component: PlaceholderBlock,
    configSchema: {
      showTagline: {
        type: "boolean",
        label: "Show Tagline",
        default: true,
      },
    },
  },
  {
    id: "bio",
    label: "Bio",
    description: "Rich text biography or description",
    component: PlaceholderBlock,
    configSchema: {
      maxLength: { type: "number", label: "Max Length", default: 500 },
      allowRichText: {
        type: "boolean",
        label: "Allow Rich Text",
        default: true,
      },
    },
  },
  {
    id: "contact",
    label: "Contact",
    description: "Contact information with copy buttons",
    component: PlaceholderBlock,
    configSchema: {
      showEmail: { type: "boolean", label: "Show Email", default: true },
      showPhone: { type: "boolean", label: "Show Phone", default: false },
    },
  },
  {
    id: "links",
    label: "Links",
    description: "Social and external links with icons",
    component: PlaceholderBlock,
    configSchema: {
      layout: {
        type: "select",
        label: "Layout",
        options: ["list", "grid"],
        default: "list",
      },
    },
  },
  {
    id: "relationships",
    label: "Relationships",
    description: "Card grid of related entities",
    component: PlaceholderBlock,
    configSchema: {
      groupByType: {
        type: "boolean",
        label: "Group by Type",
        default: true,
      },
      maxVisible: { type: "number", label: "Max Visible", default: 12 },
    },
  },
  {
    id: "activityFeed",
    label: "Activity Feed",
    description: "Timeline of recent actions",
    component: PlaceholderBlock,
    configSchema: {
      maxItems: { type: "number", label: "Max Items", default: 10 },
    },
  },
  {
    id: "gallery",
    label: "Gallery",
    description: "Image grid with lightbox viewer",
    component: PlaceholderBlock,
    configSchema: {
      columns: { type: "number", label: "Columns", default: 3 },
      lightbox: { type: "boolean", label: "Enable Lightbox", default: true },
    },
  },
  {
    id: "dataTable",
    label: "Data Table",
    description: "Display any data as a configurable table",
    component: PlaceholderBlock,
    configSchema: {
      title: { type: "string", label: "Block Title", default: "Data Table" },
      dataSource: {
        type: "select",
        label: "Data Source",
        options: ["favorites", "myAgents", "myRooms", "custom"],
        default: "favorites",
      },
      columns: { type: "columnConfig", label: "Columns" },
      maxRows: { type: "number", label: "Max Rows", default: 10 },
    },
    isDataBlock: true,
  },
  {
    id: "chart",
    label: "Chart",
    description: "Visualize data as a chart",
    component: PlaceholderBlock,
    configSchema: {
      title: { type: "string", label: "Block Title", default: "Chart" },
      chartType: {
        type: "select",
        label: "Chart Type",
        options: ["area", "bar", "line", "pie"],
        default: "bar",
      },
      dataSource: {
        type: "select",
        label: "Data Source",
        options: ["activity", "custom"],
        default: "activity",
      },
    },
    isDataBlock: true,
  },
]

/**
 * Get block type definition by ID
 */
export function getBlockType(id: BlockType): BlockTypeDefinition | undefined {
  return blockTypes.find((b) => b.id === id)
}

/**
 * Get all standard blocks (non-data blocks)
 */
export function getStandardBlocks(): BlockTypeDefinition[] {
  return blockTypes.filter((b) => !b.isDataBlock)
}

/**
 * Get all data blocks (user-defined)
 */
export function getDataBlocks(): BlockTypeDefinition[] {
  return blockTypes.filter((b) => b.isDataBlock)
}
```

**Step 2: Verify the file compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/blockTypes.ts 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/registry/blockTypes.ts
git commit -m "feat(pages): add block types registry"
```

---

### Task 4: Create Page Templates Registry

**Files:**
- Create: `src/components/Page/registry/pageTemplates.ts`

**Step 1: Create the registry file**

```typescript
// src/components/Page/registry/pageTemplates.ts
import type { BlockType } from "./blockTypes"

/**
 * Default block configuration for a template
 */
export interface TemplateBlock {
  type: BlockType
  column: "primary" | "auxiliary"
  order: number
  config: Record<string, unknown>
}

/**
 * Page template definition
 */
export interface PageTemplate {
  /** Unique identifier */
  id: string
  /** Display name */
  label: string
  /** Description for template picker */
  description: string
  /** Which entity types can use this template */
  forEntityTypes: string[]
  /** Default blocks with positions and configs */
  defaultBlocks: TemplateBlock[]
}

export const pageTemplates: PageTemplate[] = [
  {
    id: "standard",
    label: "Standard Profile",
    description: "Classic profile layout with image, bio, and sidebar",
    forEntityTypes: ["user", "agent", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 0,
        config: { shape: "circle", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
      },
      { type: "bio", column: "primary", order: 2, config: {} },
      {
        type: "relationships",
        column: "primary",
        order: 3,
        config: { groupByType: true },
      },
      { type: "contact", column: "auxiliary", order: 0, config: {} },
      {
        type: "links",
        column: "auxiliary",
        order: 1,
        config: { layout: "list" },
      },
    ],
  },
  {
    id: "minimal",
    label: "Minimal",
    description: "Clean single-column layout",
    forEntityTypes: ["user", "agent", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 0,
        config: { shape: "circle", size: "md" },
      },
      {
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
      },
      { type: "bio", column: "primary", order: 2, config: {} },
      {
        type: "links",
        column: "primary",
        order: 3,
        config: { layout: "grid" },
      },
    ],
  },
  {
    id: "showcase",
    label: "Showcase",
    description: "Gallery-focused with large visuals",
    forEntityTypes: ["user", "team"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 0,
        config: { shape: "square", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
      },
      {
        type: "gallery",
        column: "primary",
        order: 2,
        config: { columns: 3 },
      },
      { type: "bio", column: "auxiliary", order: 0, config: {} },
      { type: "links", column: "auxiliary", order: 1, config: {} },
    ],
  },
  {
    id: "agent",
    label: "Agent Profile",
    description: "Optimized for AI agent profiles",
    forEntityTypes: ["agent"],
    defaultBlocks: [
      {
        type: "profileImage",
        column: "primary",
        order: 0,
        config: { shape: "square", size: "lg" },
      },
      {
        type: "identity",
        column: "primary",
        order: 1,
        config: { showTagline: true },
      },
      {
        type: "bio",
        column: "primary",
        order: 2,
        config: { allowRichText: true },
      },
      {
        type: "relationships",
        column: "primary",
        order: 3,
        config: { groupByType: true },
      },
      {
        type: "activityFeed",
        column: "auxiliary",
        order: 0,
        config: { maxItems: 5 },
      },
    ],
  },
]

/**
 * Get template by ID
 */
export function getPageTemplate(id: string): PageTemplate | undefined {
  return pageTemplates.find((t) => t.id === id)
}

/**
 * Get templates available for an entity type
 */
export function getTemplatesForEntityType(entityTypeId: string): PageTemplate[] {
  return pageTemplates.filter((t) => t.forEntityTypes.includes(entityTypeId))
}

/**
 * Get default template for an entity type
 */
export function getDefaultTemplate(entityTypeId: string): PageTemplate {
  const templates = getTemplatesForEntityType(entityTypeId)
  // Prefer entity-specific templates, fall back to 'standard'
  const specific = templates.find((t) => t.id === entityTypeId)
  return specific || templates.find((t) => t.id === "standard") || templates[0]
}
```

**Step 2: Verify the file compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/pageTemplates.ts 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/registry/pageTemplates.ts
git commit -m "feat(pages): add page templates registry"
```

---

### Task 5: Create Data Sources Registry

**Files:**
- Create: `src/components/Page/registry/dataSources.ts`

**Step 1: Create the registry file**

```typescript
// src/components/Page/registry/dataSources.ts

/**
 * Data source definition for user-defined blocks
 */
export interface DataSourceDefinition {
  /** Unique identifier */
  id: string
  /** Display label */
  label: string
  /** Description */
  description: string
  /** Fetch function - returns array of data */
  fetcher: () => Promise<unknown[]>
}

// Placeholder fetchers - will be connected to actual services
const placeholderFetcher = async (): Promise<unknown[]> => []

export const dataSources: DataSourceDefinition[] = [
  {
    id: "favorites",
    label: "My Favorites",
    description: "Items you have favorited",
    fetcher: placeholderFetcher,
  },
  {
    id: "myAgents",
    label: "My Agents",
    description: "Agents you have created",
    fetcher: placeholderFetcher,
  },
  {
    id: "myRooms",
    label: "My Rooms",
    description: "Rooms you participate in",
    fetcher: placeholderFetcher,
  },
  {
    id: "activity",
    label: "Activity",
    description: "Recent activity data for charts",
    fetcher: placeholderFetcher,
  },
]

/**
 * Get data source by ID
 */
export function getDataSource(id: string): DataSourceDefinition | undefined {
  return dataSources.find((d) => d.id === id)
}

/**
 * Fetch data from a data source by ID
 */
export async function fetchDataSource(id: string): Promise<unknown[]> {
  const source = getDataSource(id)
  if (!source) {
    console.warn(`Unknown data source: ${id}`)
    return []
  }
  return source.fetcher()
}
```

**Step 2: Verify the file compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/dataSources.ts 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/registry/dataSources.ts
git commit -m "feat(pages): add data sources registry"
```

---

### Task 6: Create Registry Index

**Files:**
- Create: `src/components/Page/registry/index.ts`

**Step 1: Create the index file**

```typescript
// src/components/Page/registry/index.ts

// Entity types
export {
  entityTypes,
  getEntityType,
  getEntityTypeOrThrow,
  type EntityTypeDefinition,
} from "./entityTypes"

// Relationship types
export {
  relationshipTypes,
  getRelationshipType,
  isValidRelationship,
  type RelationshipTypeDefinition,
  type RelationshipPair,
} from "./relationshipTypes"

// Block types
export {
  blockTypes,
  getBlockType,
  getStandardBlocks,
  getDataBlocks,
  type BlockType,
  type BlockTypeDefinition,
  type ConfigFieldSchema,
  type ConfigFieldType,
} from "./blockTypes"

// Page templates
export {
  pageTemplates,
  getPageTemplate,
  getTemplatesForEntityType,
  getDefaultTemplate,
  type PageTemplate,
  type TemplateBlock,
} from "./pageTemplates"

// Data sources
export {
  dataSources,
  getDataSource,
  fetchDataSource,
  type DataSourceDefinition,
} from "./dataSources"
```

**Step 2: Verify the index compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/registry/index.ts 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/registry/index.ts
git commit -m "feat(pages): add registry barrel export"
```

---

## Phase 2: Primitives (Shared Components)

These components are the building blocks used by both Pages and Rooms.

---

### Task 7: Create BlockContainer Primitive

**Files:**
- Create: `src/components/Page/primitives/BlockContainer.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/primitives/BlockContainer.tsx
import { cn } from "@/lib/utils"
import { GripVertical, Settings, X } from "lucide-react"

import { Button } from "@/components/ui/button"

interface BlockContainerProps {
  /** Optional title displayed in header */
  title?: string
  /** Optional actions for header */
  headerActions?: React.ReactNode
  /** Main content */
  children: React.ReactNode
  /** Additional CSS classes */
  className?: string
  /** Whether content should scroll */
  scrollable?: boolean
  /** Edit mode - shows drag handle and controls */
  editMode?: boolean
  /** Called when remove button clicked in edit mode */
  onRemove?: () => void
  /** Called when settings button clicked in edit mode */
  onSettings?: () => void
}

/**
 * BlockContainer - Wrapper for page blocks
 *
 * Provides consistent styling and edit mode controls for all block types.
 * - Optional header with title and actions
 * - Edit mode shows drag handle, settings, and remove buttons
 * - Scrollable content area
 */
export function BlockContainer({
  title,
  headerActions,
  children,
  className,
  scrollable = false,
  editMode = false,
  onRemove,
  onSettings,
}: BlockContainerProps) {
  const showHeader = title || headerActions || editMode

  return (
    <div
      className={cn(
        "flex flex-col rounded-lg border border-border bg-card",
        className
      )}
    >
      {showHeader && (
        <div className="flex items-center justify-between px-4 py-3 border-b border-border">
          <div className="flex items-center gap-2">
            {editMode && (
              <GripVertical className="h-4 w-4 text-muted-foreground cursor-grab" />
            )}
            {title && (
              <h3 className="text-sm font-medium text-foreground">{title}</h3>
            )}
          </div>
          <div className="flex items-center gap-1">
            {headerActions}
            {editMode && onSettings && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                onClick={onSettings}
              >
                <Settings className="h-3.5 w-3.5" />
              </Button>
            )}
            {editMode && onRemove && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 text-muted-foreground hover:text-destructive"
                onClick={onRemove}
              >
                <X className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>
      )}
      <div className={cn("flex-1", scrollable && "overflow-y-auto")}>
        {children}
      </div>
    </div>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/primitives/BlockContainer.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/primitives/BlockContainer.tsx
git commit -m "feat(pages): add BlockContainer primitive"
```

---

### Task 8: Create EntityCard Primitive

**Files:**
- Create: `src/components/Page/primitives/EntityCard.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/primitives/EntityCard.tsx
import { cn } from "@/lib/utils"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"

import {
  getEntityTypeOrThrow,
  getRelationshipType,
} from "../registry"

interface EntityCardProps {
  /** Entity data */
  entity: {
    id: string
    typeId: string
    name: string
    avatarUrl?: string
    badges?: string[]
  }
  /** Optional relationship context */
  relationship?: {
    typeId: string
  }
  /** Click handler for navigation */
  onClick?: () => void
  /** Size variant */
  size?: "sm" | "md" | "lg"
  /** Additional CSS classes */
  className?: string
}

/**
 * EntityCard - Displays an entity with type icon and optional relationship
 *
 * Uses registry lookups for entity and relationship types, so no hardcoded types.
 * Clicking navigates to the entity's page.
 */
export function EntityCard({
  entity,
  relationship,
  onClick,
  size = "md",
  className,
}: EntityCardProps) {
  const entityType = getEntityTypeOrThrow(entity.typeId)
  const relType = relationship
    ? getRelationshipType(relationship.typeId)
    : null
  const Icon = entityType.icon

  const sizeClasses = {
    sm: "p-2 gap-2",
    md: "p-3 gap-3",
    lg: "p-4 gap-4",
  }

  const avatarSizes = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
  }

  const initials = entity.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <div
      className={cn(
        "flex items-center rounded-lg border border-border bg-card transition-colors",
        onClick && "cursor-pointer hover:bg-accent",
        sizeClasses[size],
        className
      )}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault()
                onClick()
              }
            }
          : undefined
      }
    >
      <Avatar className={avatarSizes[size]}>
        <AvatarImage src={entity.avatarUrl} alt={entity.name} />
        <AvatarFallback
          className={cn(
            "text-xs",
            entityType.color === "blue" && "bg-blue-100 text-blue-700",
            entityType.color === "purple" && "bg-purple-100 text-purple-700",
            entityType.color === "green" && "bg-green-100 text-green-700",
            entityType.color === "orange" && "bg-orange-100 text-orange-700"
          )}
        >
          {initials}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-foreground truncate">
            {entity.name}
          </span>
          {entity.badges?.map((badge) => (
            <Badge key={badge} variant="secondary" className="text-[10px] px-1">
              {badge}
            </Badge>
          ))}
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Icon className="h-3 w-3" />
          <span>{entityType.label}</span>
          {relType && (
            <>
              <span>·</span>
              <span>{relType.label}</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/primitives/EntityCard.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/primitives/EntityCard.tsx
git commit -m "feat(pages): add EntityCard primitive"
```

---

### Task 9: Create Primitives Index

**Files:**
- Create: `src/components/Page/primitives/index.ts`

**Step 1: Create the index file**

```typescript
// src/components/Page/primitives/index.ts
export { BlockContainer } from "./BlockContainer"
export { EntityCard } from "./EntityCard"
```

**Step 2: Commit**

```bash
git add src/components/Page/primitives/index.ts
git commit -m "feat(pages): add primitives barrel export"
```

---

## Phase 3: Standard Blocks

These are the core content blocks for entity profiles.

---

### Task 10: Create ProfileImageBlock

**Files:**
- Create: `src/components/Page/blocks/ProfileImageBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/ProfileImageBlock.tsx
import { cn } from "@/lib/utils"
import { Camera } from "lucide-react"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"

interface ProfileImageBlockConfig {
  shape: "circle" | "square"
  size: "sm" | "md" | "lg"
}

interface ProfileImageBlockProps {
  config: ProfileImageBlockConfig
  /** Entity data */
  entity: {
    name: string
    avatarUrl?: string
  }
  /** Whether the viewer can edit */
  canEdit?: boolean
  /** Called when edit clicked */
  onEdit?: () => void
}

/**
 * ProfileImageBlock - Displays entity avatar with optional edit overlay
 */
export function ProfileImageBlock({
  config,
  entity,
  canEdit = false,
  onEdit,
}: ProfileImageBlockProps) {
  const sizeClasses = {
    sm: "h-20 w-20",
    md: "h-32 w-32",
    lg: "h-40 w-40",
  }

  const initials = entity.name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className="flex justify-center p-4">
      <div className="relative">
        <Avatar
          className={cn(
            sizeClasses[config.size],
            config.shape === "square" && "rounded-xl"
          )}
        >
          <AvatarImage src={entity.avatarUrl} alt={entity.name} />
          <AvatarFallback
            className={cn(
              "text-2xl",
              config.shape === "square" && "rounded-xl"
            )}
          >
            {initials}
          </AvatarFallback>
        </Avatar>
        {canEdit && (
          <Button
            variant="secondary"
            size="icon"
            className="absolute bottom-0 right-0 h-8 w-8 rounded-full shadow-md"
            onClick={onEdit}
          >
            <Camera className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/ProfileImageBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/ProfileImageBlock.tsx
git commit -m "feat(pages): add ProfileImageBlock"
```

---

### Task 11: Create IdentityBlock

**Files:**
- Create: `src/components/Page/blocks/IdentityBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/IdentityBlock.tsx
import { Pencil } from "lucide-react"

import { Button } from "@/components/ui/button"

interface IdentityBlockConfig {
  showTagline: boolean
}

interface IdentityBlockProps {
  config: IdentityBlockConfig
  /** Entity data */
  entity: {
    name: string
    tagline?: string
  }
  /** Whether the viewer can edit */
  canEdit?: boolean
  /** Called when edit clicked */
  onEdit?: () => void
}

/**
 * IdentityBlock - Displays entity name and optional tagline
 */
export function IdentityBlock({
  config,
  entity,
  canEdit = false,
  onEdit,
}: IdentityBlockProps) {
  return (
    <div className="px-4 py-3 text-center">
      <div className="flex items-center justify-center gap-2">
        <h1 className="text-2xl font-bold text-foreground">{entity.name}</h1>
        {canEdit && (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onEdit}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        )}
      </div>
      {config.showTagline && entity.tagline && (
        <p className="mt-1 text-sm text-muted-foreground">{entity.tagline}</p>
      )}
    </div>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/IdentityBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/IdentityBlock.tsx
git commit -m "feat(pages): add IdentityBlock"
```

---

### Task 12: Create BioBlock

**Files:**
- Create: `src/components/Page/blocks/BioBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/BioBlock.tsx
import { Pencil } from "lucide-react"

import { Button } from "@/components/ui/button"

import { BlockContainer } from "../primitives"

interface BioBlockConfig {
  maxLength?: number
  allowRichText?: boolean
}

interface BioBlockProps {
  config: BioBlockConfig
  /** Entity bio text */
  bio?: string
  /** Whether the viewer can edit */
  canEdit?: boolean
  /** Called when edit clicked */
  onEdit?: () => void
}

/**
 * BioBlock - Displays entity biography/description
 */
export function BioBlock({
  config,
  bio,
  canEdit = false,
  onEdit,
}: BioBlockProps) {
  const truncatedBio =
    config.maxLength && bio && bio.length > config.maxLength
      ? `${bio.slice(0, config.maxLength)}...`
      : bio

  if (!bio && !canEdit) {
    return null
  }

  return (
    <BlockContainer
      title="About"
      headerActions={
        canEdit ? (
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={onEdit}
          >
            <Pencil className="h-3.5 w-3.5" />
          </Button>
        ) : undefined
      }
    >
      <div className="p-4">
        {bio ? (
          <p className="text-sm text-foreground whitespace-pre-wrap">
            {truncatedBio}
          </p>
        ) : (
          <p className="text-sm text-muted-foreground italic">
            No bio yet. Click to add one.
          </p>
        )}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/BioBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/BioBlock.tsx
git commit -m "feat(pages): add BioBlock"
```

---

### Task 13: Create ContactBlock

**Files:**
- Create: `src/components/Page/blocks/ContactBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/ContactBlock.tsx
import { Check, Copy, Mail, Phone } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"

import { BlockContainer } from "../primitives"

interface ContactBlockConfig {
  showEmail?: boolean
  showPhone?: boolean
}

interface ContactBlockProps {
  config: ContactBlockConfig
  /** Contact information */
  contact: {
    email?: string
    phone?: string
  }
}

/**
 * ContactBlock - Displays contact information with copy buttons
 */
export function ContactBlock({ config, contact }: ContactBlockProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null)

  const handleCopy = async (field: string, value: string) => {
    await navigator.clipboard.writeText(value)
    setCopiedField(field)
    setTimeout(() => setCopiedField(null), 2000)
  }

  const hasContent =
    (config.showEmail !== false && contact.email) ||
    (config.showPhone && contact.phone)

  if (!hasContent) {
    return null
  }

  return (
    <BlockContainer title="Contact">
      <div className="p-4 space-y-3">
        {config.showEmail !== false && contact.email && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-muted-foreground" />
              <span className="text-foreground">{contact.email}</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => handleCopy("email", contact.email!)}
            >
              {copiedField === "email" ? (
                <Check className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        )}
        {config.showPhone && contact.phone && (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground" />
              <span className="text-foreground">{contact.phone}</span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => handleCopy("phone", contact.phone!)}
            >
              {copiedField === "phone" ? (
                <Check className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        )}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/ContactBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/ContactBlock.tsx
git commit -m "feat(pages): add ContactBlock"
```

---

### Task 14: Create LinksBlock

**Files:**
- Create: `src/components/Page/blocks/LinksBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/LinksBlock.tsx
import { cn } from "@/lib/utils"
import {
  ExternalLink,
  Github,
  Globe,
  Linkedin,
  Twitter,
  type LucideIcon,
} from "lucide-react"

import { BlockContainer } from "../primitives"

interface Link {
  id: string
  type: "website" | "github" | "twitter" | "linkedin" | "other"
  url: string
  label?: string
}

interface LinksBlockConfig {
  layout: "list" | "grid"
}

interface LinksBlockProps {
  config: LinksBlockConfig
  /** Array of links */
  links: Link[]
}

const linkIcons: Record<Link["type"], LucideIcon> = {
  website: Globe,
  github: Github,
  twitter: Twitter,
  linkedin: Linkedin,
  other: ExternalLink,
}

/**
 * LinksBlock - Displays social and external links with icons
 */
export function LinksBlock({ config, links }: LinksBlockProps) {
  if (links.length === 0) {
    return null
  }

  const getDisplayLabel = (link: Link): string => {
    if (link.label) return link.label
    try {
      const url = new URL(link.url)
      return url.hostname.replace("www.", "")
    } catch {
      return link.url
    }
  }

  return (
    <BlockContainer title="Links">
      <div
        className={cn(
          "p-4",
          config.layout === "grid"
            ? "grid grid-cols-2 gap-2"
            : "flex flex-col gap-2"
        )}
      >
        {links.map((link) => {
          const Icon = linkIcons[link.type]
          return (
            <a
              key={link.id}
              href={link.url}
              target="_blank"
              rel="noopener noreferrer"
              className={cn(
                "flex items-center gap-2 px-3 py-2 rounded-md text-sm",
                "text-foreground hover:bg-accent transition-colors",
                config.layout === "grid" && "justify-center"
              )}
            >
              <Icon className="h-4 w-4 text-muted-foreground" />
              <span className="truncate">{getDisplayLabel(link)}</span>
            </a>
          )
        })}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/LinksBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/LinksBlock.tsx
git commit -m "feat(pages): add LinksBlock"
```

---

### Task 15: Create RelationshipsBlock

**Files:**
- Create: `src/components/Page/blocks/RelationshipsBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/RelationshipsBlock.tsx
import { Plus } from "lucide-react"
import { useMemo } from "react"

import { Button } from "@/components/ui/button"

import { BlockContainer, EntityCard } from "../primitives"
import { getEntityType } from "../registry"

interface RelatedEntity {
  id: string
  typeId: string
  name: string
  avatarUrl?: string
  badges?: string[]
  relationshipTypeId: string
}

interface RelationshipsBlockConfig {
  groupByType: boolean
  maxVisible: number
}

interface RelationshipsBlockProps {
  config: RelationshipsBlockConfig
  /** Related entities */
  relationships: RelatedEntity[]
  /** Whether the viewer can edit */
  canEdit?: boolean
  /** Called when add clicked */
  onAdd?: () => void
  /** Called when entity card clicked */
  onEntityClick?: (entity: RelatedEntity) => void
}

/**
 * RelationshipsBlock - Card grid of related entities grouped by type
 */
export function RelationshipsBlock({
  config,
  relationships,
  canEdit = false,
  onAdd,
  onEntityClick,
}: RelationshipsBlockProps) {
  const visibleRelationships = relationships.slice(0, config.maxVisible)
  const hasMore = relationships.length > config.maxVisible

  const grouped = useMemo(() => {
    if (!config.groupByType) {
      return { all: visibleRelationships }
    }

    return visibleRelationships.reduce<Record<string, RelatedEntity[]>>(
      (acc, rel) => {
        const key = rel.typeId
        if (!acc[key]) acc[key] = []
        acc[key].push(rel)
        return acc
      },
      {}
    )
  }, [visibleRelationships, config.groupByType])

  if (relationships.length === 0 && !canEdit) {
    return null
  }

  return (
    <BlockContainer
      title="Relationships"
      headerActions={
        canEdit ? (
          <Button variant="ghost" size="sm" className="h-7 gap-1" onClick={onAdd}>
            <Plus className="h-3.5 w-3.5" />
            Add
          </Button>
        ) : undefined
      }
    >
      <div className="p-4 space-y-4">
        {Object.entries(grouped).map(([typeId, entities]) => {
          const entityType = getEntityType(typeId)
          const groupLabel = config.groupByType
            ? entityType?.labelPlural || typeId
            : undefined

          return (
            <div key={typeId}>
              {groupLabel && (
                <h4 className="text-xs font-medium text-muted-foreground mb-2">
                  {groupLabel} ({entities.length})
                </h4>
              )}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {entities.map((entity) => (
                  <EntityCard
                    key={entity.id}
                    entity={entity}
                    relationship={{ typeId: entity.relationshipTypeId }}
                    onClick={
                      onEntityClick ? () => onEntityClick(entity) : undefined
                    }
                    size="sm"
                  />
                ))}
              </div>
            </div>
          )
        })}
        {hasMore && (
          <p className="text-xs text-muted-foreground text-center">
            +{relationships.length - config.maxVisible} more
          </p>
        )}
        {relationships.length === 0 && canEdit && (
          <p className="text-sm text-muted-foreground text-center italic">
            No relationships yet. Click Add to create one.
          </p>
        )}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/RelationshipsBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/RelationshipsBlock.tsx
git commit -m "feat(pages): add RelationshipsBlock"
```

---

### Task 16: Create ActivityFeedBlock

**Files:**
- Create: `src/components/Page/blocks/ActivityFeedBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/ActivityFeedBlock.tsx
import { formatDistanceToNow } from "date-fns"
import { Activity, MessageSquare, Settings, UserPlus } from "lucide-react"

import { BlockContainer } from "../primitives"

interface ActivityItem {
  id: string
  type: "message" | "joined" | "updated" | "other"
  description: string
  timestamp: Date
}

interface ActivityFeedBlockConfig {
  maxItems: number
}

interface ActivityFeedBlockProps {
  config: ActivityFeedBlockConfig
  /** Activity items */
  activities: ActivityItem[]
}

const activityIcons = {
  message: MessageSquare,
  joined: UserPlus,
  updated: Settings,
  other: Activity,
}

/**
 * ActivityFeedBlock - Timeline of recent actions
 */
export function ActivityFeedBlock({
  config,
  activities,
}: ActivityFeedBlockProps) {
  const visibleActivities = activities.slice(0, config.maxItems)

  if (activities.length === 0) {
    return null
  }

  return (
    <BlockContainer title="Activity" scrollable>
      <div className="p-4">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[11px] top-2 bottom-2 w-px bg-border" />

          <div className="space-y-4">
            {visibleActivities.map((activity) => {
              const Icon = activityIcons[activity.type]
              return (
                <div key={activity.id} className="flex gap-3">
                  <div className="relative z-10 flex h-6 w-6 items-center justify-center rounded-full bg-muted">
                    <Icon className="h-3 w-3 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-foreground">
                      {activity.description}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDistanceToNow(activity.timestamp, {
                        addSuffix: true,
                      })}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/ActivityFeedBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/ActivityFeedBlock.tsx
git commit -m "feat(pages): add ActivityFeedBlock"
```

---

### Task 17: Create GalleryBlock

**Files:**
- Create: `src/components/Page/blocks/GalleryBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/GalleryBlock.tsx
import { cn } from "@/lib/utils"
import { X } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog"

import { BlockContainer } from "../primitives"

interface GalleryImage {
  id: string
  url: string
  alt?: string
  caption?: string
}

interface GalleryBlockConfig {
  columns: number
  lightbox: boolean
}

interface GalleryBlockProps {
  config: GalleryBlockConfig
  /** Gallery images */
  images: GalleryImage[]
}

/**
 * GalleryBlock - Image grid with optional lightbox viewer
 */
export function GalleryBlock({ config, images }: GalleryBlockProps) {
  const [selectedImage, setSelectedImage] = useState<GalleryImage | null>(null)

  if (images.length === 0) {
    return null
  }

  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-4",
  }[config.columns] || "grid-cols-3"

  return (
    <>
      <BlockContainer title="Gallery">
        <div className={cn("grid gap-2 p-4", gridCols)}>
          {images.map((image) => (
            <button
              key={image.id}
              type="button"
              className={cn(
                "aspect-square overflow-hidden rounded-md",
                config.lightbox && "cursor-pointer hover:opacity-90 transition-opacity"
              )}
              onClick={() => config.lightbox && setSelectedImage(image)}
              disabled={!config.lightbox}
            >
              <img
                src={image.url}
                alt={image.alt || "Gallery image"}
                className="h-full w-full object-cover"
              />
            </button>
          ))}
        </div>
      </BlockContainer>

      {config.lightbox && (
        <Dialog
          open={selectedImage !== null}
          onOpenChange={(open) => !open && setSelectedImage(null)}
        >
          <DialogContent className="max-w-4xl p-0 overflow-hidden">
            <DialogTitle className="sr-only">
              {selectedImage?.alt || "Gallery image"}
            </DialogTitle>
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                className="absolute top-2 right-2 z-10 bg-black/50 hover:bg-black/70 text-white"
                onClick={() => setSelectedImage(null)}
              >
                <X className="h-4 w-4" />
              </Button>
              {selectedImage && (
                <>
                  <img
                    src={selectedImage.url}
                    alt={selectedImage.alt || "Gallery image"}
                    className="w-full h-auto max-h-[80vh] object-contain"
                  />
                  {selectedImage.caption && (
                    <div className="p-4 bg-background">
                      <p className="text-sm text-muted-foreground">
                        {selectedImage.caption}
                      </p>
                    </div>
                  )}
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/GalleryBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/GalleryBlock.tsx
git commit -m "feat(pages): add GalleryBlock"
```

---

### Task 18: Create Blocks Index

**Files:**
- Create: `src/components/Page/blocks/index.ts`

**Step 1: Create the index file**

```typescript
// src/components/Page/blocks/index.ts
export { ProfileImageBlock } from "./ProfileImageBlock"
export { IdentityBlock } from "./IdentityBlock"
export { BioBlock } from "./BioBlock"
export { ContactBlock } from "./ContactBlock"
export { LinksBlock } from "./LinksBlock"
export { RelationshipsBlock } from "./RelationshipsBlock"
export { ActivityFeedBlock } from "./ActivityFeedBlock"
export { GalleryBlock } from "./GalleryBlock"

// Data blocks will be added in Phase 4
```

**Step 2: Commit**

```bash
git add src/components/Page/blocks/index.ts
git commit -m "feat(pages): add blocks barrel export"
```

---

## Phase 4: Data Blocks (User-Defined)

These configurable blocks allow users to display custom data.

---

### Task 19: Create DataTableBlock

**Files:**
- Create: `src/components/Page/blocks/DataTableBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/DataTableBlock.tsx
import { useQuery } from "@tanstack/react-query"

import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

import { BlockContainer } from "../primitives"
import { fetchDataSource } from "../registry"

interface ColumnConfig {
  key: string
  label: string
  width?: string
}

interface DataTableBlockConfig {
  title: string
  dataSource: string
  columns: ColumnConfig[]
  maxRows: number
}

interface DataTableBlockProps {
  config: DataTableBlockConfig
}

/**
 * DataTableBlock - User-defined data table with configurable data source
 */
export function DataTableBlock({ config }: DataTableBlockProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["blockData", config.dataSource],
    queryFn: () => fetchDataSource(config.dataSource),
  })

  const visibleData = data?.slice(0, config.maxRows) || []

  return (
    <BlockContainer title={config.title}>
      <div className="p-4">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        ) : error ? (
          <p className="text-sm text-destructive">Failed to load data</p>
        ) : visibleData.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center italic">
            No data available
          </p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                {config.columns.map((col) => (
                  <TableHead key={col.key} style={{ width: col.width }}>
                    {col.label}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {visibleData.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {config.columns.map((col) => (
                    <TableCell key={col.key}>
                      {String((row as Record<string, unknown>)[col.key] ?? "")}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/DataTableBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/DataTableBlock.tsx
git commit -m "feat(pages): add DataTableBlock"
```

---

### Task 20: Create ChartBlock

**Files:**
- Create: `src/components/Page/blocks/ChartBlock.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/blocks/ChartBlock.tsx
import { useQuery } from "@tanstack/react-query"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, XAxis, YAxis } from "recharts"

import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from "@/components/ui/chart"
import { Skeleton } from "@/components/ui/skeleton"

import { BlockContainer } from "../primitives"
import { fetchDataSource } from "../registry"

interface ChartBlockConfig {
  title: string
  chartType: "area" | "bar" | "line" | "pie"
  dataSource: string
}

interface ChartBlockProps {
  config: ChartBlockConfig
}

const chartConfig = {
  value: {
    label: "Value",
    color: "hsl(var(--chart-1))",
  },
} satisfies ChartConfig

/**
 * ChartBlock - User-defined chart with configurable data source
 */
export function ChartBlock({ config }: ChartBlockProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["blockData", config.dataSource],
    queryFn: () => fetchDataSource(config.dataSource),
  })

  const chartData = (data as Array<{ name: string; value: number }>) || []

  const renderChart = () => {
    switch (config.chartType) {
      case "bar":
        return (
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Bar dataKey="value" fill="var(--color-value)" radius={4} />
          </BarChart>
        )
      case "area":
      case "line":
      default:
        return (
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} />
            <YAxis tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Area
              type="monotone"
              dataKey="value"
              fill="var(--color-value)"
              fillOpacity={0.3}
              stroke="var(--color-value)"
            />
          </AreaChart>
        )
    }
  }

  return (
    <BlockContainer title={config.title}>
      <div className="p-4">
        {isLoading ? (
          <Skeleton className="h-[200px] w-full" />
        ) : error ? (
          <p className="text-sm text-destructive">Failed to load data</p>
        ) : chartData.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center italic">
            No data available
          </p>
        ) : (
          <ChartContainer config={chartConfig} className="h-[200px] w-full">
            {renderChart()}
          </ChartContainer>
        )}
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/blocks/ChartBlock.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/blocks/ChartBlock.tsx
git commit -m "feat(pages): add ChartBlock"
```

---

### Task 21: Update Blocks Index with Data Blocks

**Files:**
- Modify: `src/components/Page/blocks/index.ts`

**Step 1: Update the index file**

```typescript
// src/components/Page/blocks/index.ts
export { ProfileImageBlock } from "./ProfileImageBlock"
export { IdentityBlock } from "./IdentityBlock"
export { BioBlock } from "./BioBlock"
export { ContactBlock } from "./ContactBlock"
export { LinksBlock } from "./LinksBlock"
export { RelationshipsBlock } from "./RelationshipsBlock"
export { ActivityFeedBlock } from "./ActivityFeedBlock"
export { GalleryBlock } from "./GalleryBlock"
export { DataTableBlock } from "./DataTableBlock"
export { ChartBlock } from "./ChartBlock"
```

**Step 2: Commit**

```bash
git add src/components/Page/blocks/index.ts
git commit -m "feat(pages): add data blocks to export"
```

---

## Phase 5: Shell & Layout

The main container components that compose blocks.

---

### Task 22: Create PageHeader

**Files:**
- Create: `src/components/Page/PageHeader.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/PageHeader.tsx
import { formatDistanceToNow } from "date-fns"
import { ChevronRight, MoreVertical, Pencil, Share2 } from "lucide-react"
import { Link } from "@tanstack/react-router"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Switch } from "@/components/ui/switch"

import { getEntityTypeOrThrow } from "./registry"

interface PageHeaderProps {
  /** Entity type ID */
  entityTypeId: string
  /** Entity name for breadcrumb */
  entityName: string
  /** Created timestamp */
  createdAt: Date
  /** Last updated timestamp */
  updatedAt: Date
  /** Whether the viewer is the owner */
  isOwner: boolean
  /** Edit mode state */
  editMode: boolean
  /** Called when edit mode toggled */
  onEditModeChange: (enabled: boolean) => void
  /** Called when share clicked */
  onShare: () => void
  /** Called when delete clicked (owner only) */
  onDelete?: () => void
}

/**
 * PageHeader - Top bar with breadcrumb, timestamps, and actions
 */
export function PageHeader({
  entityTypeId,
  entityName,
  createdAt,
  updatedAt,
  isOwner,
  editMode,
  onEditModeChange,
  onShare,
  onDelete,
}: PageHeaderProps) {
  const entityType = getEntityTypeOrThrow(entityTypeId)

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b border-border bg-background">
      {/* Left: Breadcrumb + Meta */}
      <div>
        <div className="flex items-center gap-1 text-sm">
          <Link
            to="/"
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            {entityType.labelPlural}
          </Link>
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium text-foreground">{entityName}</span>
        </div>
        <div className="text-xs text-muted-foreground mt-0.5">
          Created {formatDistanceToNow(createdAt, { addSuffix: true })} · Updated{" "}
          {formatDistanceToNow(updatedAt, { addSuffix: true })}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-2">
        {isOwner && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Edit</span>
            <Switch
              checked={editMode}
              onCheckedChange={onEditModeChange}
              aria-label="Toggle edit mode"
            />
          </div>
        )}

        <Button variant="outline" size="sm" className="gap-1.5" onClick={onShare}>
          <Share2 className="h-3.5 w-3.5" />
          Share
        </Button>

        {isOwner && (
          <Button
            variant="outline"
            size="sm"
            className="gap-1.5"
            onClick={() => onEditModeChange(true)}
          >
            <Pencil className="h-3.5 w-3.5" />
            Edit
          </Button>
        )}

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="h-8 w-8">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>Change Template</DropdownMenuItem>
            <DropdownMenuItem>Export</DropdownMenuItem>
            {isOwner && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  className="text-destructive"
                  onClick={onDelete}
                >
                  Delete
                </DropdownMenuItem>
              </>
            )}
            {!isOwner && (
              <>
                <DropdownMenuSeparator />
                <DropdownMenuItem>Report</DropdownMenuItem>
              </>
            )}
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/PageHeader.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/PageHeader.tsx
git commit -m "feat(pages): add PageHeader"
```

---

### Task 23: Create PageLayout

**Files:**
- Create: `src/components/Page/PageLayout.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/PageLayout.tsx
import { cn } from "@/lib/utils"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable"

import type { BlockType, TemplateBlock } from "./registry"

interface PageLayoutProps {
  /** Blocks to render */
  blocks: TemplateBlock[]
  /** Edit mode state */
  editMode: boolean
  /** Called when add block clicked */
  onAddBlock?: (column: "primary" | "auxiliary") => void
  /** Render function for blocks */
  renderBlock: (block: TemplateBlock, editMode: boolean) => React.ReactNode
}

/**
 * PageLayout - Two-column resizable layout for blocks
 *
 * Desktop: Two columns with resizable divider
 * Mobile: Single column (blocks stacked)
 */
export function PageLayout({
  blocks,
  editMode,
  onAddBlock,
  renderBlock,
}: PageLayoutProps) {
  const primaryBlocks = blocks
    .filter((b) => b.column === "primary")
    .sort((a, b) => a.order - b.order)

  const auxiliaryBlocks = blocks
    .filter((b) => b.column === "auxiliary")
    .sort((a, b) => a.order - b.order)

  const hasAuxiliary = auxiliaryBlocks.length > 0 || editMode

  return (
    <div className="flex-1 min-h-0">
      {/* Desktop: Resizable two-column */}
      <div className="hidden md:block h-full">
        <ResizablePanelGroup direction="horizontal">
          {/* Primary Column */}
          <ResizablePanel defaultSize={hasAuxiliary ? 70 : 100} minSize={40}>
            <div className="h-full overflow-y-auto p-4 space-y-4">
              {primaryBlocks.map((block) => (
                <div key={`${block.type}-${block.order}`}>
                  {renderBlock(block, editMode)}
                </div>
              ))}
              {editMode && (
                <AddBlockButton onClick={() => onAddBlock?.("primary")} />
              )}
            </div>
          </ResizablePanel>

          {/* Auxiliary Column */}
          {hasAuxiliary && (
            <>
              <ResizableHandle withHandle />
              <ResizablePanel defaultSize={30} minSize={20} maxSize={40}>
                <div className="h-full overflow-y-auto p-4 space-y-4 bg-muted/30">
                  {auxiliaryBlocks.map((block) => (
                    <div key={`${block.type}-${block.order}`}>
                      {renderBlock(block, editMode)}
                    </div>
                  ))}
                  {editMode && (
                    <AddBlockButton onClick={() => onAddBlock?.("auxiliary")} />
                  )}
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>
      </div>

      {/* Mobile: Single column stacked */}
      <div className="md:hidden h-full overflow-y-auto p-4 space-y-4">
        {primaryBlocks.map((block) => (
          <div key={`${block.type}-${block.order}`}>
            {renderBlock(block, editMode)}
          </div>
        ))}
        {auxiliaryBlocks.map((block) => (
          <div key={`${block.type}-${block.order}`}>
            {renderBlock(block, editMode)}
          </div>
        ))}
        {editMode && (
          <AddBlockButton onClick={() => onAddBlock?.("primary")} />
        )}
      </div>
    </div>
  )
}

function AddBlockButton({ onClick }: { onClick: () => void }) {
  return (
    <Button
      variant="outline"
      className={cn(
        "w-full h-16 border-dashed",
        "flex items-center justify-center gap-2",
        "text-muted-foreground hover:text-foreground"
      )}
      onClick={onClick}
    >
      <Plus className="h-4 w-4" />
      Add Block
    </Button>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/PageLayout.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/PageLayout.tsx
git commit -m "feat(pages): add PageLayout"
```

---

### Task 24: Create PageShell

**Files:**
- Create: `src/components/Page/PageShell.tsx`

**Step 1: Create the component**

```typescript
// src/components/Page/PageShell.tsx
import { useCallback, useState } from "react"

import { PageHeader } from "./PageHeader"
import { PageLayout } from "./PageLayout"
import {
  getDefaultTemplate,
  type TemplateBlock,
} from "./registry"
import {
  ActivityFeedBlock,
  BioBlock,
  ContactBlock,
  GalleryBlock,
  IdentityBlock,
  LinksBlock,
  ProfileImageBlock,
  RelationshipsBlock,
  DataTableBlock,
  ChartBlock,
} from "./blocks"

interface PageEntity {
  id: string
  typeId: string
  name: string
  slug?: string
  avatarUrl?: string
  tagline?: string
  bio?: string
  email?: string
  phone?: string
  links?: Array<{ id: string; type: "website" | "github" | "twitter" | "linkedin" | "other"; url: string; label?: string }>
  relationships?: Array<{ id: string; typeId: string; name: string; avatarUrl?: string; badges?: string[]; relationshipTypeId: string }>
  activities?: Array<{ id: string; type: "message" | "joined" | "updated" | "other"; description: string; timestamp: Date }>
  images?: Array<{ id: string; url: string; alt?: string; caption?: string }>
  createdAt: Date
  updatedAt: Date
}

interface PageShellProps {
  /** Entity data */
  entity: PageEntity
  /** Whether current user is the owner */
  isOwner: boolean
  /** Custom blocks override (optional) */
  blocks?: TemplateBlock[]
  /** Called when entity is deleted */
  onDelete?: () => void
}

/**
 * PageShell - Main container for entity pages
 *
 * Composes PageHeader and PageLayout with block rendering logic.
 */
export function PageShell({
  entity,
  isOwner,
  blocks: customBlocks,
  onDelete,
}: PageShellProps) {
  const [editMode, setEditMode] = useState(false)

  // Use custom blocks or default template
  const template = getDefaultTemplate(entity.typeId)
  const blocks = customBlocks || template.defaultBlocks

  const handleShare = useCallback(() => {
    const url = window.location.href
    navigator.clipboard.writeText(url)
    // TODO: Show toast
  }, [])

  const handleAddBlock = useCallback((column: "primary" | "auxiliary") => {
    // TODO: Open block picker dialog
    console.log("Add block to", column)
  }, [])

  const renderBlock = useCallback(
    (block: TemplateBlock, isEditMode: boolean) => {
      const config = block.config as Record<string, unknown>

      switch (block.type) {
        case "profileImage":
          return (
            <ProfileImageBlock
              config={config as { shape: "circle" | "square"; size: "sm" | "md" | "lg" }}
              entity={{ name: entity.name, avatarUrl: entity.avatarUrl }}
              canEdit={isEditMode}
            />
          )
        case "identity":
          return (
            <IdentityBlock
              config={config as { showTagline: boolean }}
              entity={{ name: entity.name, tagline: entity.tagline }}
              canEdit={isEditMode}
            />
          )
        case "bio":
          return (
            <BioBlock
              config={config as { maxLength?: number; allowRichText?: boolean }}
              bio={entity.bio}
              canEdit={isEditMode}
            />
          )
        case "contact":
          return (
            <ContactBlock
              config={config as { showEmail?: boolean; showPhone?: boolean }}
              contact={{ email: entity.email, phone: entity.phone }}
            />
          )
        case "links":
          return (
            <LinksBlock
              config={config as { layout: "list" | "grid" }}
              links={entity.links || []}
            />
          )
        case "relationships":
          return (
            <RelationshipsBlock
              config={config as { groupByType: boolean; maxVisible: number }}
              relationships={entity.relationships || []}
              canEdit={isEditMode}
            />
          )
        case "activityFeed":
          return (
            <ActivityFeedBlock
              config={config as { maxItems: number }}
              activities={entity.activities || []}
            />
          )
        case "gallery":
          return (
            <GalleryBlock
              config={config as { columns: number; lightbox: boolean }}
              images={entity.images || []}
            />
          )
        case "dataTable":
          return (
            <DataTableBlock
              config={config as { title: string; dataSource: string; columns: Array<{ key: string; label: string; width?: string }>; maxRows: number }}
            />
          )
        case "chart":
          return (
            <ChartBlock
              config={config as { title: string; chartType: "area" | "bar" | "line" | "pie"; dataSource: string }}
            />
          )
        default:
          return <div>Unknown block type: {block.type}</div>
      }
    },
    [entity]
  )

  return (
    <div className="flex flex-col h-full">
      <PageHeader
        entityTypeId={entity.typeId}
        entityName={entity.name}
        createdAt={entity.createdAt}
        updatedAt={entity.updatedAt}
        isOwner={isOwner}
        editMode={editMode}
        onEditModeChange={setEditMode}
        onShare={handleShare}
        onDelete={onDelete}
      />
      <PageLayout
        blocks={blocks}
        editMode={editMode}
        onAddBlock={handleAddBlock}
        renderBlock={renderBlock}
      />
    </div>
  )
}
```

**Step 2: Verify the component compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/components/Page/PageShell.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/components/Page/PageShell.tsx
git commit -m "feat(pages): add PageShell"
```

---

### Task 25: Create Page Module Index

**Files:**
- Create: `src/components/Page/index.ts`

**Step 1: Create the index file**

```typescript
// src/components/Page/index.ts

// Main components
export { PageShell } from "./PageShell"
export { PageHeader } from "./PageHeader"
export { PageLayout } from "./PageLayout"

// Primitives
export { BlockContainer, EntityCard } from "./primitives"

// Blocks
export {
  ProfileImageBlock,
  IdentityBlock,
  BioBlock,
  ContactBlock,
  LinksBlock,
  RelationshipsBlock,
  ActivityFeedBlock,
  GalleryBlock,
  DataTableBlock,
  ChartBlock,
} from "./blocks"

// Registry
export * from "./registry"
```

**Step 2: Commit**

```bash
git add src/components/Page/index.ts
git commit -m "feat(pages): add Page module barrel export"
```

---

## Phase 6: Routes

Create the TanStack Router routes for entity pages.

---

### Task 26: Create User Page Route

**Files:**
- Create: `src/routes/_layout/u.$slug.tsx`

**Step 1: Create the route**

```typescript
// src/routes/_layout/u.$slug.tsx
import { createFileRoute, useParams, useNavigate } from "@tanstack/react-router"
import { useSuspenseQuery } from "@tanstack/react-query"

import { PageShell } from "@/components/Page"

// TODO: Replace with actual service
const mockUser = {
  id: "1",
  typeId: "user",
  name: "Alice Example",
  slug: "alice",
  avatarUrl: undefined,
  tagline: "Software Engineer & Open Source Enthusiast",
  bio: "I build things with code. Currently working on distributed systems and developer tools.",
  email: "alice@example.com",
  phone: undefined,
  links: [
    { id: "1", type: "github" as const, url: "https://github.com/alice", label: "GitHub" },
    { id: "2", type: "twitter" as const, url: "https://twitter.com/alice", label: "@alice" },
    { id: "3", type: "website" as const, url: "https://alice.dev", label: "Blog" },
  ],
  relationships: [
    { id: "t1", typeId: "team", name: "Alpha Team", relationshipTypeId: "member" },
    { id: "a1", typeId: "agent", name: "Claude", avatarUrl: undefined, badges: ["GPT-4"], relationshipTypeId: "creator" },
  ],
  activities: [],
  images: [],
  createdAt: new Date("2024-01-15"),
  updatedAt: new Date(),
}

export const Route = createFileRoute("/_layout/u/$slug")({
  component: UserPage,
})

function UserPage() {
  const { slug } = useParams({ from: "/_layout/u/$slug" })
  const navigate = useNavigate()

  // TODO: Replace with actual query
  // const { data: user } = useSuspenseQuery({
  //   queryKey: ["users", slug],
  //   queryFn: () => UserService.getBySlug(slug),
  // })

  const user = { ...mockUser, slug }

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    // TODO: Implement delete
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entity={user}
      isOwner={isOwner}
      onDelete={handleDelete}
    />
  )
}
```

**Step 2: Verify the route compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/routes/_layout/u.\$slug.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/routes/_layout/u.\$slug.tsx
git commit -m "feat(pages): add user page route /u/:slug"
```

---

### Task 27: Create Agent Page Route

**Files:**
- Create: `src/routes/_layout/agent.$agentId.tsx`

**Step 1: Create the route**

```typescript
// src/routes/_layout/agent.$agentId.tsx
import { createFileRoute, useParams, useNavigate } from "@tanstack/react-router"

import { PageShell } from "@/components/Page"

// TODO: Replace with actual service
const mockAgent = {
  id: "agent-123",
  typeId: "agent",
  name: "Claude Assistant",
  avatarUrl: undefined,
  tagline: "AI-powered coding assistant",
  bio: "I help developers write, review, and debug code. Powered by Claude.",
  email: undefined,
  phone: undefined,
  links: [],
  relationships: [
    { id: "u1", typeId: "user", name: "Alice", relationshipTypeId: "created_by" },
  ],
  activities: [
    { id: "a1", type: "message" as const, description: "Helped review PR #123", timestamp: new Date() },
  ],
  images: [],
  createdAt: new Date("2024-06-01"),
  updatedAt: new Date(),
}

export const Route = createFileRoute("/_layout/agent/$agentId")({
  component: AgentPage,
})

function AgentPage() {
  const { agentId } = useParams({ from: "/_layout/agent/$agentId" })
  const navigate = useNavigate()

  // TODO: Replace with actual query
  const agent = { ...mockAgent, id: agentId }

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entity={agent}
      isOwner={isOwner}
      onDelete={handleDelete}
    />
  )
}
```

**Step 2: Verify the route compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/routes/_layout/agent.\$agentId.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/routes/_layout/agent.\$agentId.tsx
git commit -m "feat(pages): add agent page route /agent/:id"
```

---

### Task 28: Create Team Page Route

**Files:**
- Create: `src/routes/_layout/team.$slug.tsx`

**Step 1: Create the route**

```typescript
// src/routes/_layout/team.$slug.tsx
import { createFileRoute, useParams, useNavigate } from "@tanstack/react-router"

import { PageShell } from "@/components/Page"

// TODO: Replace with actual service
const mockTeam = {
  id: "team-alpha",
  typeId: "team",
  name: "Alpha Team",
  slug: "alpha",
  avatarUrl: undefined,
  tagline: "Building the future of collaboration",
  bio: "We are a cross-functional team focused on creating tools that help people work together more effectively.",
  email: "alpha@example.com",
  phone: undefined,
  links: [
    { id: "1", type: "website" as const, url: "https://alpha.team", label: "Website" },
  ],
  relationships: [
    { id: "u1", typeId: "user", name: "Alice", relationshipTypeId: "has_member", badges: ["Lead"] },
    { id: "u2", typeId: "user", name: "Bob", relationshipTypeId: "has_member" },
    { id: "u3", typeId: "user", name: "Charlie", relationshipTypeId: "has_member" },
  ],
  activities: [],
  images: [],
  createdAt: new Date("2024-03-01"),
  updatedAt: new Date(),
}

export const Route = createFileRoute("/_layout/team/$slug")({
  component: TeamPage,
})

function TeamPage() {
  const { slug } = useParams({ from: "/_layout/team/$slug" })
  const navigate = useNavigate()

  // TODO: Replace with actual query
  const team = { ...mockTeam, slug }

  // TODO: Check actual ownership
  const isOwner = true

  const handleDelete = () => {
    navigate({ to: "/" })
  }

  return (
    <PageShell
      entity={team}
      isOwner={isOwner}
      onDelete={handleDelete}
    />
  )
}
```

**Step 2: Verify the route compiles**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npx tsc --noEmit src/routes/_layout/team.\$slug.tsx 2>&1 | head -20`
Expected: No errors

**Step 3: Commit**

```bash
git add src/routes/_layout/team.\$slug.tsx
git commit -m "feat(pages): add team page route /team/:slug"
```

---

## Phase 7: Integration & Polish

Final steps to wire everything together.

---

### Task 29: Update Block Types Registry with Real Components

**Files:**
- Modify: `src/components/Page/registry/blockTypes.ts`

**Step 1: Update to import real components**

Replace the placeholder imports at the top of the file with:

```typescript
// src/components/Page/registry/blockTypes.ts
import type { ComponentType } from "react"

// Import actual block components (lazy loading for code splitting)
import { lazy } from "react"

const ProfileImageBlock = lazy(() =>
  import("../blocks/ProfileImageBlock").then((m) => ({ default: m.ProfileImageBlock }))
)
const IdentityBlock = lazy(() =>
  import("../blocks/IdentityBlock").then((m) => ({ default: m.IdentityBlock }))
)
const BioBlock = lazy(() =>
  import("../blocks/BioBlock").then((m) => ({ default: m.BioBlock }))
)
const ContactBlock = lazy(() =>
  import("../blocks/ContactBlock").then((m) => ({ default: m.ContactBlock }))
)
const LinksBlock = lazy(() =>
  import("../blocks/LinksBlock").then((m) => ({ default: m.LinksBlock }))
)
const RelationshipsBlock = lazy(() =>
  import("../blocks/RelationshipsBlock").then((m) => ({ default: m.RelationshipsBlock }))
)
const ActivityFeedBlock = lazy(() =>
  import("../blocks/ActivityFeedBlock").then((m) => ({ default: m.ActivityFeedBlock }))
)
const GalleryBlock = lazy(() =>
  import("../blocks/GalleryBlock").then((m) => ({ default: m.GalleryBlock }))
)
const DataTableBlock = lazy(() =>
  import("../blocks/DataTableBlock").then((m) => ({ default: m.DataTableBlock }))
)
const ChartBlock = lazy(() =>
  import("../blocks/ChartBlock").then((m) => ({ default: m.ChartBlock }))
)

// Then update the blockTypes array to use these components
// (see Task 3 for the array structure, just change `component: PlaceholderBlock` to the real components)
```

**Step 2: Commit**

```bash
git add src/components/Page/registry/blockTypes.ts
git commit -m "feat(pages): wire block types to real components"
```

---

### Task 30: Verify Full Build

**Step 1: Run type check**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npm run build 2>&1 | tail -30`
Expected: Build succeeds

**Step 2: Run linter**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npm run lint 2>&1 | tail -30`
Expected: No errors (warnings OK)

**Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix(pages): resolve build and lint issues"
```

---

### Task 31: Run Dev Server and Manual Test

**Step 1: Start development server**

Run: `cd /home/josep/dog/.worktrees/pages-system/frontend && npm run dev &`
Expected: Server starts on localhost:5173

**Step 2: Manual verification**

Navigate to:
- `http://localhost:5173/u/alice` - User page
- `http://localhost:5173/agent/test` - Agent page
- `http://localhost:5173/team/alpha` - Team page

**Step 3: Commit final state**

```bash
git add -A
git commit -m "feat(pages): complete Pages system implementation"
```

---

## Summary

**Total Tasks:** 31

**Phases:**
1. **Registries (6 tasks)** - Entity, Relationship, Block, Template, DataSource registries
2. **Primitives (3 tasks)** - BlockContainer, EntityCard
3. **Standard Blocks (9 tasks)** - ProfileImage, Identity, Bio, Contact, Links, Relationships, ActivityFeed, Gallery
4. **Data Blocks (3 tasks)** - DataTable, Chart
5. **Shell & Layout (4 tasks)** - PageHeader, PageLayout, PageShell
6. **Routes (3 tasks)** - User, Agent, Team routes
7. **Integration (3 tasks)** - Wire components, build verify, manual test

**Key Files Created:**
- `src/components/Page/registry/*.ts` - All type registries
- `src/components/Page/primitives/*.tsx` - Shared UI primitives
- `src/components/Page/blocks/*.tsx` - All content blocks
- `src/components/Page/Page*.tsx` - Shell, Header, Layout
- `src/routes/_layout/u.$slug.tsx` - User pages
- `src/routes/_layout/agent.$agentId.tsx` - Agent pages
- `src/routes/_layout/team.$slug.tsx` - Team pages

**Extensibility:**
- Add entity type: Edit `entityTypes.ts` only
- Add relationship type: Edit `relationshipTypes.ts` only
- Add block type: Edit `blockTypes.ts` + create component
- Add data source: Edit `dataSources.ts` only
- Add template: Edit `pageTemplates.ts` only
