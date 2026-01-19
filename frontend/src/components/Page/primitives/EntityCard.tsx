// src/components/Page/primitives/EntityCard.tsx

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { getEntityTypeOrThrow, getRelationshipType } from "../registry"

interface EntityCardEntity {
  id: string
  typeId: string
  name: string
  avatarUrl?: string
  badges?: string[]
}

interface EntityCardRelationship {
  typeId: string
}

interface EntityCardProps {
  /** Entity data to display */
  entity: EntityCardEntity
  /** Optional relationship context */
  relationship?: EntityCardRelationship
  /** Click handler - makes card interactive */
  onClick?: () => void
  /** Size variant */
  size?: "sm" | "md" | "lg"
  /** Additional CSS classes */
  className?: string
}

/** Size-based styling configurations */
const sizeConfig = {
  sm: {
    padding: "p-2",
    gap: "gap-2",
    avatar: "h-8 w-8",
    avatarText: "text-xs",
    name: "text-sm",
    meta: "text-xs",
  },
  md: {
    padding: "p-3",
    gap: "gap-3",
    avatar: "h-10 w-10",
    avatarText: "text-sm",
    name: "text-base",
    meta: "text-sm",
  },
  lg: {
    padding: "p-4",
    gap: "gap-4",
    avatar: "h-12 w-12",
    avatarText: "text-base",
    name: "text-lg",
    meta: "text-sm",
  },
}

/** Color mapping for avatar backgrounds based on entity type color */
const colorClasses: Record<string, string> = {
  blue: "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300",
  purple:
    "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300",
  green: "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300",
  orange:
    "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300",
}

/**
 * Get initials from a name for avatar fallback
 */
function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/)
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * EntityCard - Displays an entity with its type icon and optional relationship context
 *
 * Uses the registry for type lookups to get icons and colors.
 * Supports clickable mode with keyboard accessibility.
 */
export function EntityCard({
  entity,
  relationship,
  onClick,
  size = "md",
  className,
}: EntityCardProps) {
  const entityType = getEntityTypeOrThrow(entity.typeId)
  const relationshipType = relationship
    ? getRelationshipType(relationship.typeId)
    : undefined
  const config = sizeConfig[size]
  const colorClass = colorClasses[entityType.color] || colorClasses.blue
  const Icon = entityType.icon

  // Build meta label (e.g., "Agent" or "Agent · Creator")
  const metaLabel = relationshipType
    ? `${entityType.label} · ${relationshipType.label}`
    : entityType.label

  const handleKeyDown = (event: React.KeyboardEvent) => {
    if (onClick && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault()
      onClick()
    }
  }

  const content = (
    <>
      <Avatar className={config.avatar}>
        <AvatarImage src={entity.avatarUrl} alt={entity.name} />
        <AvatarFallback className={cn(colorClass, config.avatarText)}>
          {getInitials(entity.name)}
        </AvatarFallback>
      </Avatar>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn("font-medium truncate", config.name)}>
            {entity.name}
          </span>
          {entity.badges?.map((badge) => (
            <Badge key={badge} variant="secondary" className="shrink-0">
              {badge}
            </Badge>
          ))}
        </div>
        <div
          className={cn(
            "flex items-center gap-1 text-muted-foreground",
            config.meta,
          )}
        >
          <Icon className="h-3.5 w-3.5 shrink-0" />
          <span className="truncate">{metaLabel}</span>
        </div>
      </div>
    </>
  )

  const baseClasses = cn(
    "flex items-center rounded-lg",
    config.padding,
    config.gap,
    className,
  )

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        onKeyDown={handleKeyDown}
        className={cn(
          baseClasses,
          "w-full text-left",
          "transition-colors",
          "hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        )}
      >
        {content}
      </button>
    )
  }

  return <div className={baseClasses}>{content}</div>
}
