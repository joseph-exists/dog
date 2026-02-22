// src/components/Page/registry/entityTypes.ts
import {
  Bot,
  Crown,
  Gem,
  type LucideIcon,
  MessageSquare,
  Smile,
  SmilePlusIcon,
  Sparkles,
  User,
  Users,
} from "lucide-react"

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
    id: "demo",
    label: "Demo",
    labelPlural: "Demos",
    icon: SmilePlusIcon,
    color: "yellow",
    pageRoutePattern: "/demo/:slug",
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
  {
    id: "persona",
    label: "Persona",
    labelPlural: "Personas",
    icon: Smile,
    color: "pink",
    pageRoutePattern: "/persona/:id",
  },
  {
    id: "archetype",
    label: "Archetype",
    labelPlural: "Archetypes",
    icon: Crown,
    color: "amber",
    pageRoutePattern: "/archetype/:id",
  },
  {
    id: "quality",
    label: "Quality",
    labelPlural: "Qualities",
    icon: Gem,
    color: "violet",
    pageRoutePattern: "/quality/:id",
  },
  {
    id: "trait",
    label: "Trait",
    labelPlural: "Traits",
    icon: Sparkles,
    color: "rose",
    pageRoutePattern: "/trait/:id",
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
