# Persona Picker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a unified persona picker component system with service layer, hooks, primitives, variants, and Pages block integration.

**Architecture:** Service transforms API junction data (UserPersona/AgentPersona) + persona data into a unified `LibraryPersona` ViewModel. A `usePersonaPicker` hook manages selection/filter state. The `PersonaPicker` orchestrator routes to four variant shells (dropdown, popover, sheet, inline), each rendering shared content components (list/grid) composed of shared primitives (item, card, avatar).

**Tech Stack:** React, TypeScript, TanStack Query, shadcn/ui (Avatar, Badge, Button, Card, DropdownMenu, Popover, Sheet, Input, Tooltip), lucide-react, zod

---

## Task 1: Create Type Definitions

**Files:**
- Create: `frontend/src/components/Persona/types.ts`

**Step 1: Write the type definitions file**

All types the system needs. No dependencies on API types in public interfaces.

```tsx
// src/components/Persona/types.ts

/**
 * Identifies who owns a persona library.
 * The picker is agnostic to owner type.
 */
export interface PersonaLibraryOwner {
  type: "user" | "agent"
  id: string
  name: string
}

/**
 * Unified view of a persona in someone's library.
 * Normalizes UserPersonaPublic + PersonaPublic into one shape.
 */
export interface LibraryPersona {
  // Junction data
  libraryEntryId: string
  ownerId: string
  ownerType: "user" | "agent"

  // Persona data (denormalized for display)
  personaId: string
  name: string
  nickname: string | null
  description: string | null
  isActive: boolean

  // Rich data (loaded on demand)
  longDescription?: string | null
  domains?: string[]
  traits?: Array<{ id: string; name: string }>
  qualities?: Array<{ id: string; name: string }>
}

/**
 * Picker interaction modes.
 */
export type PersonaPickerMode =
  | "select-single"
  | "select-multiple"
  | "manage"
  | "browse"

/**
 * Visual presentation variants.
 */
export type PersonaPickerVariant =
  | "dropdown"
  | "popover"
  | "sheet"
  | "inline"

/**
 * Filter options for narrowing persona list.
 */
export interface PersonaFilter {
  isActive?: boolean
  domains?: string[]
  searchQuery?: string
}

/**
 * Main picker props - the unified interface.
 */
export interface PersonaPickerProps {
  owner: PersonaLibraryOwner
  mode: PersonaPickerMode
  variant: PersonaPickerVariant
  selected?: string | string[] | null
  onSelect?: (selected: string | string[] | null) => void
  filter?: PersonaFilter
  layout?: "list" | "grid"
  maxVisible?: number
  className?: string
  trigger?: React.ReactNode
  placeholder?: string
}

/**
 * PersonaItem props - compact single-line display.
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
 * PersonaCard props - expanded detail view.
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
 * PersonaAvatar props.
 */
export interface PersonaAvatarProps {
  name: string
  imageUrl?: string | null
  size?: "sm" | "md" | "lg"
  showActiveIndicator?: boolean
  isActive?: boolean
  className?: string
}

/**
 * Content component shared props.
 */
export interface PersonaContentProps {
  personas: LibraryPersona[]
  selectedIds: string[]
  selectionMode: "none" | "radio" | "checkbox"
  onSelect: (personaId: string) => void
  onEditNickname?: (entryId: string, nickname: string) => void
  onRemove?: (entryId: string) => void
  showActions: boolean
  className?: string
}
```

**Step 2: Verify TypeScript compiles**

Run: `cd frontend && npx tsc --noEmit --strict frontend/src/components/Persona/types.ts 2>&1 | head -5`
Expected: No errors (or minor import issues resolved in next task)

**Step 3: Commit**

```bash
git add frontend/src/components/Persona/types.ts
git commit -m "feat(persona-picker): add type definitions"
```

---

## Task 2: Create personaLibraryService

**Files:**
- Create: `frontend/src/services/personaLibraryService.ts`

**Step 1: Write the persona library service**

Routes to UserPersonasService or AgentPersonasService based on owner type.
Fetches junction entries + full persona data, joins them into LibraryPersona[].

```tsx
// src/services/personaLibraryService.ts

import {
  AgentPersonasService,
  PersonasService,
  UserPersonasService,
} from "@/client"
import type {
  AgentPersonaPublic,
  PersonaPublic,
  UserPersonaPublic,
} from "@/client"
import type { LibraryPersona, PersonaLibraryOwner } from "@/components/Persona/types"

// ============================================================================
// Transformation
// ============================================================================

function toLibraryPersona(
  entry: UserPersonaPublic | AgentPersonaPublic,
  persona: PersonaPublic,
  ownerType: "user" | "agent",
): LibraryPersona {
  const ownerId = ownerType === "user"
    ? (entry as UserPersonaPublic).user_id
    : (entry as AgentPersonaPublic).agent_id

  return {
    libraryEntryId: entry.id,
    ownerId,
    ownerType,
    personaId: entry.persona_id,
    name: persona.name,
    nickname: entry.nickname ?? null,
    description: persona.description ?? null,
    isActive: entry.is_active ?? true,
    longDescription: persona.long_description ?? null,
    domains: [
      persona.general_domain,
      persona.specific_domain,
    ].filter(Boolean) as string[],
  }
}

// ============================================================================
// Service
// ============================================================================

export const PersonaLibraryService = {
  /**
   * Fetch the full library for an owner.
   * Joins junction entries with persona data.
   */
  async getLibrary(owner: PersonaLibraryOwner): Promise<LibraryPersona[]> {
    // 1. Fetch junction entries
    let entries: (UserPersonaPublic | AgentPersonaPublic)[]

    if (owner.type === "user") {
      const result = await UserPersonasService.readUserPersonas({ limit: 100 })
      entries = result.data
    } else {
      const result = await AgentPersonasService.readAgentPersonas({
        agentId: owner.id,
        limit: 100,
      })
      entries = result.data
    }

    if (entries.length === 0) return []

    // 2. Fetch all persona details in batch
    const personaIds = [...new Set(entries.map((e) => e.persona_id))]
    const personaMap = new Map<string, PersonaPublic>()

    // Fetch personas individually (no batch endpoint available)
    const personaPromises = personaIds.map(async (id) => {
      try {
        const persona = await PersonasService.readPersona({ id })
        personaMap.set(id, persona)
      } catch {
        // Skip personas that can't be fetched
      }
    })
    await Promise.all(personaPromises)

    // 3. Join and transform
    return entries
      .filter((entry) => personaMap.has(entry.persona_id))
      .map((entry) =>
        toLibraryPersona(entry, personaMap.get(entry.persona_id)!, owner.type)
      )
  },

  /**
   * Add a persona to the library.
   */
  async addToLibrary(
    owner: PersonaLibraryOwner,
    personaId: string,
    nickname?: string,
  ): Promise<LibraryPersona> {
    let entry: UserPersonaPublic | AgentPersonaPublic

    if (owner.type === "user") {
      entry = await UserPersonasService.createUserPersona({
        requestBody: { persona_id: personaId, nickname },
      })
    } else {
      entry = await AgentPersonasService.createAgentPersona({
        agentId: owner.id,
        requestBody: { persona_id: personaId, nickname },
      })
    }

    const persona = await PersonasService.readPersona({ id: personaId })
    return toLibraryPersona(entry, persona, owner.type)
  },

  /**
   * Update a library entry (nickname, is_active).
   */
  async updateEntry(
    owner: PersonaLibraryOwner,
    entryId: string,
    updates: { nickname?: string | null; is_active?: boolean },
  ): Promise<void> {
    if (owner.type === "user") {
      await UserPersonasService.updateUserPersona({
        id: entryId,
        requestBody: updates,
      })
    } else {
      await AgentPersonasService.updateAgentPersona({
        agentId: owner.id,
        id: entryId,
        requestBody: updates,
      })
    }
  },

  /**
   * Remove a persona from the library.
   */
  async removeFromLibrary(
    owner: PersonaLibraryOwner,
    entryId: string,
  ): Promise<void> {
    if (owner.type === "user") {
      await UserPersonasService.deleteUserPersona({ id: entryId })
    } else {
      await AgentPersonasService.deleteAgentPersona({
        agentId: owner.id,
        id: entryId,
      })
    }
  },

  /**
   * Fetch all available personas (for adding new ones).
   */
  async getAvailablePersonas(): Promise<PersonaPublic[]> {
    const result = await PersonasService.readPersonas({ limit: 100 })
    return result.data
  },
}
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/services/personaLibraryService.ts
git commit -m "feat(persona-picker): add personaLibraryService with owner-agnostic API"
```

---

## Task 3: Create usePersonaLibrary Hook

**Files:**
- Create: `frontend/src/hooks/usePersonaLibrary.ts`

**Step 1: Write the hook**

```tsx
// src/hooks/usePersonaLibrary.ts

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import type { LibraryPersona, PersonaLibraryOwner } from "@/components/Persona/types"
import { PersonaLibraryService } from "@/services/personaLibraryService"

interface UsePersonaLibraryOptions {
  owner: PersonaLibraryOwner
  enabled?: boolean
}

export function usePersonaLibrary({ owner, enabled = true }: UsePersonaLibraryOptions) {
  const queryClient = useQueryClient()
  const queryKey = ["persona-library", owner.type, owner.id] as const

  const libraryQuery = useQuery({
    queryKey,
    queryFn: () => PersonaLibraryService.getLibrary(owner),
    enabled,
  })

  const addMutation = useMutation({
    mutationFn: ({ personaId, nickname }: { personaId: string; nickname?: string }) =>
      PersonaLibraryService.addToLibrary(owner, personaId, nickname),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ entryId, updates }: { entryId: string; updates: { nickname?: string | null; is_active?: boolean } }) =>
      PersonaLibraryService.updateEntry(owner, entryId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  const removeMutation = useMutation({
    mutationFn: (entryId: string) =>
      PersonaLibraryService.removeFromLibrary(owner, entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
    },
  })

  return {
    // Data
    personas: libraryQuery.data ?? [],
    isLoading: libraryQuery.isLoading,
    error: libraryQuery.error,

    // Mutations
    addPersona: addMutation.mutate,
    updateEntry: updateMutation.mutate,
    removePersona: removeMutation.mutate,

    // Mutation states
    isAdding: addMutation.isPending,
    isUpdating: updateMutation.isPending,
    isRemoving: removeMutation.isPending,
  }
}
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/hooks/usePersonaLibrary.ts
git commit -m "feat(persona-picker): add usePersonaLibrary hook"
```

---

## Task 4: Create usePersonaPicker Hook

**Files:**
- Create: `frontend/src/hooks/usePersonaPicker.ts`

**Step 1: Write the hook**

```tsx
// src/hooks/usePersonaPicker.ts

import { useCallback, useMemo, useState } from "react"
import type {
  LibraryPersona,
  PersonaFilter,
  PersonaLibraryOwner,
  PersonaPickerMode,
} from "@/components/Persona/types"
import { usePersonaLibrary } from "./usePersonaLibrary"

interface UsePersonaPickerOptions {
  owner: PersonaLibraryOwner
  mode: PersonaPickerMode
  initialSelected?: string | string[] | null
  filter?: PersonaFilter
}

export function usePersonaPicker({
  owner,
  mode,
  initialSelected,
  filter: externalFilter,
}: UsePersonaPickerOptions) {
  const library = usePersonaLibrary({ owner })

  // Selection state
  const [selectedIds, setSelectedIds] = useState<string[]>(() => {
    if (!initialSelected) return []
    return Array.isArray(initialSelected) ? initialSelected : [initialSelected]
  })

  // Search state
  const [searchQuery, setSearchQuery] = useState("")

  // UI state
  const [isOpen, setIsOpen] = useState(false)

  // Filter personas
  const filteredPersonas = useMemo(() => {
    let result = library.personas

    // Apply active filter
    if (externalFilter?.isActive !== undefined) {
      result = result.filter((p) => p.isActive === externalFilter.isActive)
    }

    // Apply domain filter
    if (externalFilter?.domains?.length) {
      result = result.filter((p) =>
        p.domains?.some((d) => externalFilter.domains!.includes(d))
      )
    }

    // Apply search
    const query = (externalFilter?.searchQuery || searchQuery).toLowerCase().trim()
    if (query) {
      result = result.filter(
        (p) =>
          p.name.toLowerCase().includes(query) ||
          (p.nickname && p.nickname.toLowerCase().includes(query)) ||
          (p.description && p.description.toLowerCase().includes(query))
      )
    }

    return result
  }, [library.personas, externalFilter, searchQuery])

  // Selection helpers
  const selectPersona = useCallback(
    (personaId: string) => {
      if (mode === "select-single") {
        const newSelected = selectedIds[0] === personaId ? [] : [personaId]
        setSelectedIds(newSelected)
      } else if (mode === "select-multiple") {
        setSelectedIds((prev) =>
          prev.includes(personaId)
            ? prev.filter((id) => id !== personaId)
            : [...prev, personaId]
        )
      }
    },
    [mode, selectedIds]
  )

  const clearSelection = useCallback(() => {
    setSelectedIds([])
  }, [])

  // Derive selection mode for UI
  const selectionMode = useMemo(() => {
    if (mode === "browse") return "none" as const
    if (mode === "manage") return "none" as const
    if (mode === "select-single") return "radio" as const
    return "checkbox" as const
  }, [mode])

  return {
    // Library data
    personas: filteredPersonas,
    allPersonas: library.personas,
    isLoading: library.isLoading,
    error: library.error,

    // Selection
    selectedIds,
    selectPersona,
    clearSelection,
    selectionMode,

    // Search
    searchQuery,
    setSearchQuery,

    // UI
    isOpen,
    setIsOpen,

    // Library mutations (pass through)
    addPersona: library.addPersona,
    updateEntry: library.updateEntry,
    removePersona: library.removePersona,
    isAdding: library.isAdding,
    isUpdating: library.isUpdating,
    isRemoving: library.isRemoving,

    // Mode
    mode,
    showActions: mode === "manage",
    readonly: mode === "browse",
  }
}
```

**Step 2: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 3: Commit**

```bash
git add frontend/src/hooks/usePersonaPicker.ts
git commit -m "feat(persona-picker): add usePersonaPicker state management hook"
```

---

## Task 5: Create Primitives (PersonaAvatar, PersonaBadges, PersonaActions)

**Files:**
- Create: `frontend/src/components/Persona/primitives/PersonaAvatar.tsx`
- Create: `frontend/src/components/Persona/primitives/PersonaBadges.tsx`
- Create: `frontend/src/components/Persona/primitives/PersonaActions.tsx`
- Create: `frontend/src/components/Persona/primitives/index.ts`

**Step 1: Create PersonaAvatar**

```tsx
// src/components/Persona/primitives/PersonaAvatar.tsx
import { Smile } from "lucide-react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"
import type { PersonaAvatarProps } from "../types"

const sizeClasses = {
  sm: "h-6 w-6",
  md: "h-8 w-8",
  lg: "h-12 w-12",
}

const iconSizes = {
  sm: "h-3 w-3",
  md: "h-4 w-4",
  lg: "h-6 w-6",
}

export function PersonaAvatar({
  name,
  imageUrl,
  size = "md",
  showActiveIndicator = false,
  isActive = false,
  className,
}: PersonaAvatarProps) {
  const initials = name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)

  return (
    <div className={cn("relative", className)}>
      <Avatar className={cn(sizeClasses[size])}>
        {imageUrl && <AvatarImage src={imageUrl} alt={name} />}
        <AvatarFallback className="text-xs">
          {initials || <Smile className={iconSizes[size]} />}
        </AvatarFallback>
      </Avatar>
      {showActiveIndicator && (
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-background",
            isActive ? "bg-green-500" : "bg-muted-foreground/40"
          )}
        />
      )}
    </div>
  )
}
```

**Step 2: Create PersonaBadges**

```tsx
// src/components/Persona/primitives/PersonaBadges.tsx
import { Badge } from "@/components/ui/badge"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface PersonaBadgesProps {
  traits?: Array<{ id: string; name: string }>
  qualities?: Array<{ id: string; name: string }>
  domains?: string[]
  variant?: "compact" | "expanded"
  maxVisible?: number
  className?: string
}

export function PersonaBadges({
  traits = [],
  qualities = [],
  domains = [],
  variant = "compact",
  maxVisible = 3,
  className,
}: PersonaBadgesProps) {
  if (variant === "compact") {
    const parts: string[] = []
    if (traits.length) parts.push(`${traits.length} traits`)
    if (qualities.length) parts.push(`${qualities.length} qualities`)
    if (domains.length) parts.push(domains.join(", "))

    if (parts.length === 0) return null

    return (
      <span className={cn("text-xs text-muted-foreground", className)}>
        {parts.join(" · ")}
      </span>
    )
  }

  // Expanded variant
  const allBadges = [
    ...traits.map((t) => ({ ...t, color: "blue" as const })),
    ...qualities.map((q) => ({ ...q, color: "purple" as const })),
  ]

  const visible = allBadges.slice(0, maxVisible)
  const hidden = allBadges.slice(maxVisible)

  return (
    <div className={cn("flex flex-wrap gap-1", className)}>
      {visible.map((badge) => (
        <Badge
          key={badge.id}
          variant="secondary"
          className={cn(
            "text-xs",
            badge.color === "blue" && "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200",
            badge.color === "purple" && "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
          )}
        >
          {badge.name}
        </Badge>
      ))}
      {hidden.length > 0 && (
        <Tooltip>
          <TooltipTrigger asChild>
            <Badge variant="outline" className="text-xs cursor-default">
              +{hidden.length} more
            </Badge>
          </TooltipTrigger>
          <TooltipContent>
            <div className="space-y-1">
              {hidden.map((b) => (
                <div key={b.id} className="text-xs">{b.name}</div>
              ))}
            </div>
          </TooltipContent>
        </Tooltip>
      )}
      {domains.map((domain) => (
        <Badge key={domain} variant="outline" className="text-xs">
          {domain}
        </Badge>
      ))}
    </div>
  )
}
```

**Step 3: Create PersonaActions**

```tsx
// src/components/Persona/primitives/PersonaActions.tsx
import { Edit2, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type ActionType = "add" | "edit" | "remove"

interface PersonaActionsProps {
  actions: ActionType[]
  onAdd?: () => void
  onEdit?: () => void
  onRemove?: () => void
  isLoading?: boolean
  className?: string
}

const actionConfig = {
  add: { icon: Plus, label: "Add", variant: "ghost" as const },
  edit: { icon: Edit2, label: "Edit", variant: "ghost" as const },
  remove: { icon: Trash2, label: "Remove", variant: "ghost" as const },
}

export function PersonaActions({
  actions,
  onAdd,
  onEdit,
  onRemove,
  isLoading = false,
  className,
}: PersonaActionsProps) {
  const handlers = { add: onAdd, edit: onEdit, remove: onRemove }

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {actions.map((action) => {
        const config = actionConfig[action]
        const Icon = config.icon
        return (
          <Button
            key={action}
            variant={config.variant}
            size="icon"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation()
              handlers[action]?.()
            }}
            disabled={isLoading}
            aria-label={config.label}
          >
            <Icon className="h-4 w-4" />
          </Button>
        )
      })}
    </div>
  )
}
```

**Step 4: Create primitives barrel export**

```tsx
// src/components/Persona/primitives/index.ts
export { PersonaAvatar } from "./PersonaAvatar"
export { PersonaBadges } from "./PersonaBadges"
export { PersonaActions } from "./PersonaActions"
```

**Step 5: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 6: Commit**

```bash
git add frontend/src/components/Persona/primitives/
git commit -m "feat(persona-picker): add primitives (Avatar, Badges, Actions)"
```

---

## Task 6: Create PersonaItem and PersonaCard

**Files:**
- Create: `frontend/src/components/Persona/primitives/PersonaItem.tsx`
- Create: `frontend/src/components/Persona/primitives/PersonaCard.tsx`
- Modify: `frontend/src/components/Persona/primitives/index.ts`

**Step 1: Create PersonaItem**

```tsx
// src/components/Persona/primitives/PersonaItem.tsx
import { Check, Circle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { PersonaItemProps } from "../types"
import { PersonaActions } from "./PersonaActions"
import { PersonaAvatar } from "./PersonaAvatar"

export function PersonaItem({
  persona,
  isSelected = false,
  selectionMode = "none",
  onSelect,
  onEdit,
  onRemove,
  showActions = false,
  className,
}: PersonaItemProps) {
  const displayName = persona.nickname || persona.name

  return (
    <div
      className={cn(
        "group flex items-center gap-3 px-3 py-2 rounded-md cursor-pointer",
        "hover:bg-accent/50 transition-colors",
        isSelected && "bg-accent",
        className
      )}
      onClick={onSelect}
      role={selectionMode !== "none" ? "option" : undefined}
      aria-selected={isSelected}
    >
      {/* Selection indicator */}
      {selectionMode === "radio" && (
        <div className="shrink-0">
          {isSelected ? (
            <Check className="h-4 w-4 text-primary" />
          ) : (
            <Circle className="h-4 w-4 text-muted-foreground/40" />
          )}
        </div>
      )}
      {selectionMode === "checkbox" && (
        <div
          className={cn(
            "shrink-0 h-4 w-4 rounded border",
            isSelected
              ? "bg-primary border-primary"
              : "border-muted-foreground/40"
          )}
        >
          {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
        </div>
      )}

      {/* Avatar */}
      <PersonaAvatar
        name={persona.name}
        size="sm"
        showActiveIndicator
        isActive={persona.isActive}
      />

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{displayName}</div>
        {persona.description && (
          <div className="text-xs text-muted-foreground truncate">
            {persona.description}
          </div>
        )}
      </div>

      {/* Actions (hover only) */}
      {showActions && (
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <PersonaActions
            actions={[
              ...(onEdit ? ["edit" as const] : []),
              ...(onRemove ? ["remove" as const] : []),
            ]}
            onEdit={onEdit}
            onRemove={onRemove}
          />
        </div>
      )}
    </div>
  )
}
```

**Step 2: Create PersonaCard**

```tsx
// src/components/Persona/primitives/PersonaCard.tsx
import { useState } from "react"
import { Check } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { cn } from "@/lib/utils"
import type { PersonaCardProps } from "../types"
import { PersonaAvatar } from "./PersonaAvatar"
import { PersonaBadges } from "./PersonaBadges"

export function PersonaCard({
  persona,
  isSelected = false,
  onSelect,
  onEditNickname,
  onRemove,
  readonly = false,
  className,
}: PersonaCardProps) {
  const [isEditingNickname, setIsEditingNickname] = useState(false)
  const [nicknameValue, setNicknameValue] = useState(persona.nickname || "")

  const handleSaveNickname = () => {
    onEditNickname?.(nicknameValue)
    setIsEditingNickname(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSaveNickname()
    if (e.key === "Escape") setIsEditingNickname(false)
  }

  return (
    <Card
      className={cn(
        "relative transition-all cursor-pointer",
        "hover:shadow-md",
        isSelected && "ring-2 ring-primary",
        className
      )}
      onClick={onSelect}
    >
      {isSelected && (
        <div className="absolute top-2 right-2">
          <Check className="h-4 w-4 text-primary" />
        </div>
      )}

      <CardContent className="p-4 space-y-3">
        {/* Header: avatar + name */}
        <div className="flex items-center gap-3">
          <PersonaAvatar
            name={persona.name}
            size="lg"
            showActiveIndicator
            isActive={persona.isActive}
          />
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{persona.name}</div>
            {isEditingNickname ? (
              <Input
                value={nicknameValue}
                onChange={(e) => setNicknameValue(e.target.value)}
                onBlur={handleSaveNickname}
                onKeyDown={handleKeyDown}
                placeholder="Nickname..."
                className="h-6 text-xs mt-1"
                autoFocus
                onClick={(e) => e.stopPropagation()}
              />
            ) : (
              persona.nickname && (
                <div
                  className="text-xs text-muted-foreground truncate cursor-text"
                  onClick={(e) => {
                    if (!readonly && onEditNickname) {
                      e.stopPropagation()
                      setIsEditingNickname(true)
                    }
                  }}
                >
                  aka "{persona.nickname}"
                </div>
              )
            )}
          </div>
        </div>

        {/* Description */}
        {persona.description && (
          <p className="text-sm text-muted-foreground line-clamp-2">
            {persona.description}
          </p>
        )}

        {/* Badges */}
        <PersonaBadges
          traits={persona.traits}
          qualities={persona.qualities}
          domains={persona.domains}
          variant="compact"
        />
      </CardContent>

      {/* Actions footer */}
      {!readonly && (onEditNickname || onRemove) && (
        <CardFooter className="p-3 pt-0 gap-2">
          {onEditNickname && !isEditingNickname && (
            <Button
              variant="outline"
              size="sm"
              className="text-xs"
              onClick={(e) => {
                e.stopPropagation()
                setIsEditingNickname(true)
              }}
            >
              Edit nickname
            </Button>
          )}
          {onRemove && (
            <Button
              variant="ghost"
              size="sm"
              className="text-xs text-destructive hover:text-destructive"
              onClick={(e) => {
                e.stopPropagation()
                onRemove()
              }}
            >
              Remove
            </Button>
          )}
        </CardFooter>
      )}
    </Card>
  )
}
```

**Step 3: Update primitives index**

```tsx
// src/components/Persona/primitives/index.ts
export { PersonaAvatar } from "./PersonaAvatar"
export { PersonaBadges } from "./PersonaBadges"
export { PersonaActions } from "./PersonaActions"
export { PersonaItem } from "./PersonaItem"
export { PersonaCard } from "./PersonaCard"
```

**Step 4: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/Persona/primitives/
git commit -m "feat(persona-picker): add PersonaItem and PersonaCard primitives"
```

---

## Task 7: Create Content Components (Search, List, Grid, Empty)

**Files:**
- Create: `frontend/src/components/Persona/content/PersonaSearch.tsx`
- Create: `frontend/src/components/Persona/content/PersonaList.tsx`
- Create: `frontend/src/components/Persona/content/PersonaGrid.tsx`
- Create: `frontend/src/components/Persona/content/PersonaEmpty.tsx`
- Create: `frontend/src/components/Persona/content/index.ts`

**Step 1: Create PersonaSearch**

```tsx
// src/components/Persona/content/PersonaSearch.tsx
import { Search, X } from "lucide-react"
import { useEffect, useRef, useState } from "react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PersonaSearchProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  autoFocus?: boolean
}

export function PersonaSearch({
  value,
  onChange,
  placeholder = "Search personas...",
  className,
  autoFocus = false,
}: PersonaSearchProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [localValue, setLocalValue] = useState(value)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>()

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  const handleChange = (newValue: string) => {
    setLocalValue(newValue)
    clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      onChange(newValue)
    }, 300)
  }

  useEffect(() => {
    return () => clearTimeout(debounceRef.current)
  }, [])

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
      <Input
        ref={inputRef}
        value={localValue}
        onChange={(e) => handleChange(e.target.value)}
        placeholder={placeholder}
        className="pl-9 pr-8"
        autoFocus={autoFocus}
      />
      {localValue && (
        <Button
          variant="ghost"
          size="icon"
          className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6"
          onClick={() => {
            handleChange("")
            inputRef.current?.focus()
          }}
          aria-label="Clear search"
        >
          <X className="h-3 w-3" />
        </Button>
      )}
    </div>
  )
}
```

**Step 2: Create PersonaList**

```tsx
// src/components/Persona/content/PersonaList.tsx
import { cn } from "@/lib/utils"
import { PersonaItem } from "../primitives"
import type { PersonaContentProps } from "../types"

export function PersonaList({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  className,
}: PersonaContentProps) {
  return (
    <div
      className={cn("space-y-1 overflow-y-auto max-h-[300px]", className)}
      role="listbox"
      aria-multiselectable={selectionMode === "checkbox"}
    >
      {personas.map((persona) => (
        <PersonaItem
          key={persona.libraryEntryId}
          persona={persona}
          isSelected={selectedIds.includes(persona.personaId)}
          selectionMode={selectionMode}
          onSelect={() => onSelect(persona.personaId)}
          onEdit={
            onEditNickname
              ? () => onEditNickname(persona.libraryEntryId, persona.nickname || "")
              : undefined
          }
          onRemove={
            onRemove
              ? () => onRemove(persona.libraryEntryId)
              : undefined
          }
          showActions={showActions}
        />
      ))}
    </div>
  )
}
```

**Step 3: Create PersonaGrid**

```tsx
// src/components/Persona/content/PersonaGrid.tsx
import { cn } from "@/lib/utils"
import { PersonaCard } from "../primitives"
import type { PersonaContentProps } from "../types"

export function PersonaGrid({
  personas,
  selectedIds,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  className,
}: PersonaContentProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto max-h-[400px]",
        className
      )}
    >
      {personas.map((persona) => (
        <PersonaCard
          key={persona.libraryEntryId}
          persona={persona}
          isSelected={selectedIds.includes(persona.personaId)}
          onSelect={() => onSelect(persona.personaId)}
          onEditNickname={
            showActions && onEditNickname
              ? (nickname) => onEditNickname(persona.libraryEntryId, nickname)
              : undefined
          }
          onRemove={
            showActions && onRemove
              ? () => onRemove(persona.libraryEntryId)
              : undefined
          }
          readonly={!showActions}
        />
      ))}
    </div>
  )
}
```

**Step 4: Create PersonaEmpty**

```tsx
// src/components/Persona/content/PersonaEmpty.tsx
import { Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type EmptyContext = "no-personas" | "no-results" | "no-matches"

interface PersonaEmptyProps {
  context?: EmptyContext
  onAction?: () => void
  actionLabel?: string
  className?: string
}

const messages: Record<EmptyContext, { title: string; description: string }> = {
  "no-personas": {
    title: "No Personas",
    description: "This library is empty. Add personas to get started.",
  },
  "no-results": {
    title: "No Results",
    description: "No personas match your search. Try a different query.",
  },
  "no-matches": {
    title: "No Matches",
    description: "No personas match the current filters.",
  },
}

export function PersonaEmpty({
  context = "no-personas",
  onAction,
  actionLabel = "Add Persona",
  className,
}: PersonaEmptyProps) {
  const message = messages[context]

  return (
    <div className={cn("flex flex-col items-center justify-center py-8 px-4 text-center", className)}>
      <Smile className="h-10 w-10 text-muted-foreground/50 mb-3" />
      <h3 className="text-sm font-medium">{message.title}</h3>
      <p className="text-xs text-muted-foreground mt-1 max-w-[200px]">
        {message.description}
      </p>
      {onAction && context === "no-personas" && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  )
}
```

**Step 5: Create content barrel export**

```tsx
// src/components/Persona/content/index.ts
export { PersonaSearch } from "./PersonaSearch"
export { PersonaList } from "./PersonaList"
export { PersonaGrid } from "./PersonaGrid"
export { PersonaEmpty } from "./PersonaEmpty"
```

**Step 6: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 7: Commit**

```bash
git add frontend/src/components/Persona/content/
git commit -m "feat(persona-picker): add content components (Search, List, Grid, Empty)"
```

---

## Task 8: Create Variant Shells (Dropdown, Popover, Sheet, Inline)

**Files:**
- Create: `frontend/src/components/Persona/variants/PersonaDropdown.tsx`
- Create: `frontend/src/components/Persona/variants/PersonaPopover.tsx`
- Create: `frontend/src/components/Persona/variants/PersonaSheet.tsx`
- Create: `frontend/src/components/Persona/variants/PersonaInline.tsx`
- Create: `frontend/src/components/Persona/variants/index.ts`

**Step 1: Create PersonaDropdown**

```tsx
// src/components/Persona/variants/PersonaDropdown.tsx
import { ChevronDown, Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { cn } from "@/lib/utils"
import { PersonaEmpty, PersonaList, PersonaSearch } from "../content"
import { PersonaAvatar } from "../primitives"
import type { LibraryPersona, PersonaContentProps } from "../types"

interface PersonaDropdownProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  allPersonas: LibraryPersona[]
  trigger?: React.ReactNode
  placeholder?: string
  className?: string
}

export function PersonaDropdown({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  isOpen,
  setIsOpen,
  searchQuery,
  setSearchQuery,
  allPersonas,
  trigger,
  placeholder = "Select persona...",
  className,
}: PersonaDropdownProps) {
  const selectedPersona = allPersonas.find(
    (p) => p.personaId === selectedIds[0]
  )

  const defaultTrigger = (
    <Button
      variant="outline"
      className={cn("w-full justify-between", className)}
    >
      {selectedPersona ? (
        <span className="flex items-center gap-2">
          <PersonaAvatar name={selectedPersona.name} size="sm" />
          <span className="truncate">
            {selectedPersona.nickname || selectedPersona.name}
          </span>
        </span>
      ) : (
        <span className="flex items-center gap-2 text-muted-foreground">
          <Smile className="h-4 w-4" />
          {placeholder}
        </span>
      )}
      <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
    </Button>
  )

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>{trigger || defaultTrigger}</PopoverTrigger>
      <PopoverContent className="w-[280px] p-0" align="start">
        <div className="p-2 border-b">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>
        {personas.length === 0 ? (
          <PersonaEmpty
            context={searchQuery ? "no-results" : "no-personas"}
          />
        ) : (
          <PersonaList
            personas={personas}
            selectedIds={selectedIds}
            selectionMode={selectionMode}
            onSelect={(id) => {
              onSelect(id)
              if (selectionMode === "radio") setIsOpen(false)
            }}
            showActions={false}
          />
        )}
      </PopoverContent>
    </Popover>
  )
}
```

**Step 2: Create PersonaPopover**

```tsx
// src/components/Persona/variants/PersonaPopover.tsx
import { Smile } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { PersonaEmpty, PersonaGrid, PersonaList, PersonaSearch } from "../content"
import { PersonaAvatar } from "../primitives"
import type { LibraryPersona, PersonaContentProps } from "../types"

interface PersonaPopoverProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  allPersonas: LibraryPersona[]
  layout?: "list" | "grid"
  trigger?: React.ReactNode
  placeholder?: string
}

export function PersonaPopover({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  isOpen,
  setIsOpen,
  searchQuery,
  setSearchQuery,
  allPersonas,
  layout = "list",
  trigger,
  placeholder = "Select persona...",
}: PersonaPopoverProps) {
  const selectedPersona = allPersonas.find(
    (p) => p.personaId === selectedIds[0]
  )

  const defaultTrigger = (
    <Button variant="outline" className="gap-2">
      {selectedPersona ? (
        <>
          <PersonaAvatar name={selectedPersona.name} size="sm" />
          <span>{selectedPersona.nickname || selectedPersona.name}</span>
        </>
      ) : (
        <>
          <Smile className="h-4 w-4" />
          {placeholder}
        </>
      )}
    </Button>
  )

  const ContentComponent = layout === "grid" ? PersonaGrid : PersonaList

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>{trigger || defaultTrigger}</PopoverTrigger>
      <PopoverContent className="w-[400px] p-0" align="start">
        <div className="p-3 border-b">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>
        <div className="p-3">
          {personas.length === 0 ? (
            <PersonaEmpty
              context={searchQuery ? "no-results" : "no-personas"}
            />
          ) : (
            <ContentComponent
              personas={personas}
              selectedIds={selectedIds}
              selectionMode={selectionMode}
              onSelect={onSelect}
              onEditNickname={onEditNickname}
              onRemove={onRemove}
              showActions={showActions}
            />
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
```

**Step 3: Create PersonaSheet**

```tsx
// src/components/Persona/variants/PersonaSheet.tsx
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { PersonaEmpty, PersonaGrid, PersonaSearch } from "../content"
import type { PersonaContentProps } from "../types"

interface PersonaSheetProps extends PersonaContentProps {
  isOpen: boolean
  setIsOpen: (open: boolean) => void
  searchQuery: string
  setSearchQuery: (query: string) => void
  title?: string
  onAddNew?: () => void
}

export function PersonaSheet({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  isOpen,
  setIsOpen,
  searchQuery,
  setSearchQuery,
  title = "Persona Library",
  onAddNew,
}: PersonaSheetProps) {
  return (
    <Sheet open={isOpen} onOpenChange={setIsOpen}>
      <SheetContent side="right" className="w-[400px] sm:w-[540px] flex flex-col">
        <SheetHeader>
          <SheetTitle>{title}</SheetTitle>
        </SheetHeader>

        <div className="py-3">
          <PersonaSearch
            value={searchQuery}
            onChange={setSearchQuery}
            autoFocus
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          {personas.length === 0 ? (
            <PersonaEmpty
              context={searchQuery ? "no-results" : "no-personas"}
              onAction={onAddNew}
            />
          ) : (
            <PersonaGrid
              personas={personas}
              selectedIds={selectedIds}
              selectionMode={selectionMode}
              onSelect={onSelect}
              onEditNickname={onEditNickname}
              onRemove={onRemove}
              showActions={showActions}
              className="max-h-none"
            />
          )}
        </div>

        <SheetFooter className="pt-4 border-t">
          <Button variant="outline" onClick={() => setIsOpen(false)}>
            Done
          </Button>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  )
}
```

**Step 4: Create PersonaInline**

```tsx
// src/components/Persona/variants/PersonaInline.tsx
import { cn } from "@/lib/utils"
import { PersonaEmpty, PersonaGrid, PersonaList, PersonaSearch } from "../content"
import type { PersonaContentProps } from "../types"

interface PersonaInlineProps extends PersonaContentProps {
  layout?: "list" | "grid"
  searchQuery: string
  setSearchQuery: (query: string) => void
  showSearch?: boolean
  maxVisible?: number
  onAddNew?: () => void
}

export function PersonaInline({
  personas,
  selectedIds,
  selectionMode,
  onSelect,
  onEditNickname,
  onRemove,
  showActions,
  layout = "grid",
  searchQuery,
  setSearchQuery,
  showSearch = true,
  maxVisible,
  onAddNew,
  className,
}: PersonaInlineProps) {
  const visiblePersonas = maxVisible
    ? personas.slice(0, maxVisible)
    : personas

  const ContentComponent = layout === "grid" ? PersonaGrid : PersonaList

  return (
    <div className={cn("space-y-3", className)}>
      {showSearch && personas.length > 3 && (
        <PersonaSearch value={searchQuery} onChange={setSearchQuery} />
      )}

      {visiblePersonas.length === 0 ? (
        <PersonaEmpty
          context={searchQuery ? "no-results" : "no-personas"}
          onAction={onAddNew}
        />
      ) : (
        <ContentComponent
          personas={visiblePersonas}
          selectedIds={selectedIds}
          selectionMode={selectionMode}
          onSelect={onSelect}
          onEditNickname={onEditNickname}
          onRemove={onRemove}
          showActions={showActions}
          className="max-h-none overflow-visible"
        />
      )}

      {maxVisible && personas.length > maxVisible && (
        <p className="text-xs text-muted-foreground text-center">
          +{personas.length - maxVisible} more
        </p>
      )}
    </div>
  )
}
```

**Step 5: Create variants barrel export**

```tsx
// src/components/Persona/variants/index.ts
export { PersonaDropdown } from "./PersonaDropdown"
export { PersonaPopover } from "./PersonaPopover"
export { PersonaSheet } from "./PersonaSheet"
export { PersonaInline } from "./PersonaInline"
```

**Step 6: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 7: Commit**

```bash
git add frontend/src/components/Persona/variants/
git commit -m "feat(persona-picker): add variant shells (Dropdown, Popover, Sheet, Inline)"
```

---

## Task 9: Create PersonaPicker Orchestrator

**Files:**
- Create: `frontend/src/components/Persona/PersonaPicker.tsx`
- Create: `frontend/src/components/Persona/index.ts`

**Step 1: Create PersonaPicker**

```tsx
// src/components/Persona/PersonaPicker.tsx
import { usePersonaPicker } from "@/hooks/usePersonaPicker"
import type { PersonaPickerProps } from "./types"
import {
  PersonaDropdown,
  PersonaInline,
  PersonaPopover,
  PersonaSheet,
} from "./variants"

/**
 * PersonaPicker - Unified persona selection component.
 *
 * Routes to the correct variant shell based on the `variant` prop.
 * Uses usePersonaPicker hook for all state management.
 */
export function PersonaPicker({
  owner,
  mode,
  variant,
  selected,
  onSelect,
  filter,
  layout = "list",
  maxVisible,
  className,
  trigger,
  placeholder,
}: PersonaPickerProps) {
  const picker = usePersonaPicker({
    owner,
    mode,
    initialSelected: selected,
    filter,
  })

  // Sync external selection changes
  const handleSelect = (personaId: string) => {
    picker.selectPersona(personaId)
    if (mode === "select-single") {
      onSelect?.(personaId)
    } else if (mode === "select-multiple") {
      const newSelected = picker.selectedIds.includes(personaId)
        ? picker.selectedIds.filter((id) => id !== personaId)
        : [...picker.selectedIds, personaId]
      onSelect?.(newSelected)
    }
  }

  const handleEditNickname = (entryId: string, nickname: string) => {
    picker.updateEntry({ entryId, updates: { nickname } })
  }

  const handleRemove = (entryId: string) => {
    picker.removePersona(entryId)
  }

  // Shared content props
  const contentProps = {
    personas: picker.personas,
    selectedIds: picker.selectedIds,
    selectionMode: picker.selectionMode,
    onSelect: handleSelect,
    onEditNickname: picker.showActions ? handleEditNickname : undefined,
    onRemove: picker.showActions ? handleRemove : undefined,
    showActions: picker.showActions,
  }

  switch (variant) {
    case "dropdown":
      return (
        <PersonaDropdown
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          allPersonas={picker.allPersonas}
          trigger={trigger}
          placeholder={placeholder}
          className={className}
        />
      )

    case "popover":
      return (
        <PersonaPopover
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          allPersonas={picker.allPersonas}
          layout={layout}
          trigger={trigger}
          placeholder={placeholder}
        />
      )

    case "sheet":
      return (
        <PersonaSheet
          {...contentProps}
          isOpen={picker.isOpen}
          setIsOpen={picker.setIsOpen}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          title={`${owner.name}'s Personas`}
        />
      )

    case "inline":
      return (
        <PersonaInline
          {...contentProps}
          layout={layout}
          searchQuery={picker.searchQuery}
          setSearchQuery={picker.setSearchQuery}
          maxVisible={maxVisible}
          className={className}
        />
      )
  }
}
```

**Step 2: Create barrel export**

```tsx
// src/components/Persona/index.ts
export { PersonaPicker } from "./PersonaPicker"
export type {
  LibraryPersona,
  PersonaFilter,
  PersonaLibraryOwner,
  PersonaPickerMode,
  PersonaPickerProps,
  PersonaPickerVariant,
} from "./types"
export { PersonaAvatar, PersonaCard, PersonaItem } from "./primitives"
```

**Step 3: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 4: Verify build succeeds**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 5: Commit**

```bash
git add frontend/src/components/Persona/PersonaPicker.tsx
git add frontend/src/components/Persona/index.ts
git commit -m "feat(persona-picker): add PersonaPicker orchestrator and barrel exports"
```

---

## Task 10: Create PersonasBlock for Pages Integration

**Files:**
- Create: `frontend/src/components/Page/blocks/PersonasBlock.tsx`
- Modify: `frontend/src/components/Page/blocks/index.ts`
- Modify: `frontend/src/components/Page/registry/blockTypes.ts`

**Step 1: Create PersonasBlock**

```tsx
// src/components/Page/blocks/PersonasBlock.tsx
import { PersonaPicker } from "@/components/Persona"
import type { PersonaLibraryOwner } from "@/components/Persona"
import { cn } from "@/lib/utils"
import { BlockContainer } from "../primitives"

export interface PersonasBlockConfig {
  layout: "list" | "grid"
  maxVisible: number
  showAddButton: boolean
}

export interface PersonasBlockProps {
  config: PersonasBlockConfig
  entityType: string
  entityId: string
  entityName?: string
  isEditing?: boolean
  className?: string
}

/**
 * PersonasBlock - Displays persona library inline on a Page.
 *
 * In view mode: browse-only display of persona library.
 * In edit mode: full management UI with add/edit/remove.
 */
export function PersonasBlock({
  config,
  entityType,
  entityId,
  entityName,
  isEditing = false,
  className,
}: PersonasBlockProps) {
  const owner: PersonaLibraryOwner = {
    type: entityType as "user" | "agent",
    id: entityId,
    name: entityName || (entityType === "user" ? "Your" : "Agent's"),
  }

  return (
    <BlockContainer title="Personas" className={cn(className)}>
      <div className="p-4">
        <PersonaPicker
          owner={owner}
          mode={isEditing ? "manage" : "browse"}
          variant="inline"
          layout={config.layout}
          maxVisible={config.maxVisible}
        />
      </div>
    </BlockContainer>
  )
}
```

**Step 2: Update blocks index**

Add to `frontend/src/components/Page/blocks/index.ts`:

```ts
// Personas Block
export { PersonasBlock } from "./PersonasBlock"
export type {
  PersonasBlockConfig,
  PersonasBlockProps,
} from "./PersonasBlock"
```

**Step 3: Add to blockTypes registry**

Add to the BLOCK_TYPES array in `frontend/src/components/Page/registry/blockTypes.ts`:

```ts
// Add to imports:
import { Smile } from "lucide-react"  // Add Smile to the existing import

// Add to BLOCK_TYPES array after "chart":
{
  type: "personas",
  label: "Personas",
  description: "Display persona library for this entity",
  icon: Smile,
  defaultConfig: {
    layout: "grid",
    maxVisible: 6,
    showAddButton: true,
  },
  defaultContent: {},
},
```

Also add `"personas"` to the `BlockType` union:

```ts
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
  | "personas"  // Add this
```

**Step 4: Wire up PersonasBlock in PageShell renderBlock**

Add the following case in the `renderBlock` switch statement in `frontend/src/components/Page/PageShell.tsx`:

```tsx
// Add import at top:
import { PersonasBlock } from "./blocks"

// Add case in switch:
case "personas":
  return (
    <PersonasBlock
      config={{
        layout: (config.layout as "list" | "grid") ?? "grid",
        maxVisible: (config.maxVisible as number) ?? 6,
        showAddButton: (config.showAddButton as boolean) ?? true,
      }}
      entityType={entityType}
      entityId={entityId}
      isEditing={isEditing}
    />
  )
```

**Step 5: Verify lint passes**

Run: `cd frontend && npm run lint`
Expected: No errors

**Step 6: Verify build passes**

Run: `cd frontend && npm run build`
Expected: Build succeeds

**Step 7: Commit**

```bash
git add frontend/src/components/Page/blocks/PersonasBlock.tsx
git add frontend/src/components/Page/blocks/index.ts
git add frontend/src/components/Page/registry/blockTypes.ts
git add frontend/src/components/Page/PageShell.tsx
git commit -m "feat(persona-picker): add PersonasBlock page integration with registry entry"
```

---

## Verification Checklist

After all tasks are complete, verify:

- [ ] `npm run lint` passes
- [ ] `npm run build` succeeds
- [ ] All files are properly organized under `components/Persona/`
- [ ] `PersonaPicker` exported from `@/components/Persona`
- [ ] `PersonasBlock` appears in block palette
- [ ] No TypeScript errors in strict mode
- [ ] No console errors

### Integration Tests (manual)

- [ ] Navigate to user page → add PersonasBlock → see inline picker
- [ ] PersonaPicker with `variant="dropdown"` renders trigger + menu
- [ ] PersonaPicker with `variant="sheet"` opens side panel
- [ ] Add persona to library → appears in list
- [ ] Edit nickname → saves and displays
- [ ] Remove persona → disappears from list
- [ ] Search filters list in real time
- [ ] Empty state shows when library is empty
