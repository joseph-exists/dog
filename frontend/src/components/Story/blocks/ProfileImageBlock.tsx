// src/components/Page/blocks/ProfileImageBlock.tsx
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

export interface ProfileImageBlockConfig {
  shape: "circle" | "square"
  size: "sm" | "md" | "lg"
}

export interface ProfileImageContent {
  imageUrl?: string
  alt?: string
}

export interface ProfileImageBlockProps {
  config: ProfileImageBlockConfig
  content?: ProfileImageContent
  className?: string
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
 * Get initials for avatar fallback
 * Returns "?" when no alt text is available
 */
function getInitials(alt?: string): string {
  if (!alt) {
    return "?"
  }
  const parts = alt.trim().split(/\s+/)
  if (parts.length === 1) {
    return parts[0].substring(0, 2).toUpperCase()
  }
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
}

/**
 * ProfileImageBlock - Displays a profile avatar image
 *
 * Supports different sizes (sm, md, lg) and shapes (circle, square).
 * Shows initials fallback when no image is available.
 * View-only block - no edit functionality.
 */
export function ProfileImageBlock({
  config,
  content,
  className,
}: ProfileImageBlockProps) {
  const sizeClass = sizeClasses[config.size]
  const shapeClass = shapeClasses[config.shape]

  return (
    <div className={cn("flex justify-center", className)}>
      <div className="relative inline-block">
        <Avatar className={cn(sizeClass, shapeClass)}>
          <AvatarImage src={content?.imageUrl} alt={content?.alt || ""} />
          <AvatarFallback className={cn(shapeClass, "text-2xl")}>
            {getInitials(content?.alt)}
          </AvatarFallback>
        </Avatar>
      </div>
    </div>
  )
}
