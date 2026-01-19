// src/components/Page/blocks/ProfileImageBlock.tsx
import { Camera } from "lucide-react"

import { cn } from "@/lib/utils"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"

export interface ProfileImageBlockConfig {
  shape: "circle" | "square"
  size: "sm" | "md" | "lg"
}

export interface ProfileImageBlockProps {
  config: ProfileImageBlockConfig
  entity: { name: string; avatarUrl?: string }
  canEdit?: boolean
  onEdit?: () => void
}

/** Size-based styling configurations */
const sizeClasses = {
  sm: "h-20 w-20",
  md: "h-32 w-32",
  lg: "h-40 w-40",
}

/** Shape-based styling configurations */
const shapeClasses = {
  circle: "rounded-full",
  square: "rounded-xl",
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
 * ProfileImageBlock - Displays an entity avatar with optional edit overlay
 *
 * Supports different sizes (sm, md, lg) and shapes (circle, square).
 * When canEdit is true, shows a camera icon button for editing.
 */
export function ProfileImageBlock({
  config,
  entity,
  canEdit = false,
  onEdit,
}: ProfileImageBlockProps) {
  const sizeClass = sizeClasses[config.size]
  const shapeClass = shapeClasses[config.shape]

  return (
    <div className="flex justify-center">
      <div className="relative inline-block">
        <Avatar className={cn(sizeClass, shapeClass)}>
          <AvatarImage src={entity.avatarUrl} alt={entity.name} />
          <AvatarFallback className={cn(shapeClass, "text-2xl")}>
            {getInitials(entity.name)}
          </AvatarFallback>
        </Avatar>
        {canEdit && (
          <Button
            type="button"
            variant="secondary"
            size="icon-sm"
            className="absolute bottom-0 right-0 rounded-full shadow-md"
            onClick={onEdit}
            aria-label="Edit profile image"
          >
            <Camera className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}
