// src/components/Page/blocks/IdentityBlock.tsx
import { cn } from "@/lib/utils"

export interface IdentityBlockConfig {
  showTagline: boolean
}

export interface IdentityContent {
  name: string
  tagline?: string
}

export interface IdentityBlockProps {
  config: IdentityBlockConfig
  content?: IdentityContent
  className?: string
}

/**
 * IdentityBlock - Displays entity name and optional tagline
 *
 * Centered layout with large heading for the name.
 * Shows tagline below when configured and available.
 * Shows "Unnamed" if no name is provided.
 * View-only block - no edit functionality.
 */
export function IdentityBlock({
  config,
  content,
  className,
}: IdentityBlockProps) {
  const displayName = content?.name || "Unnamed"

  return (
    <div className={cn("text-center", className)}>
      <h1 className="text-2xl font-bold">{displayName}</h1>
      {config.showTagline && content?.tagline && (
        <p className="text-sm text-muted-foreground">{content.tagline}</p>
      )}
    </div>
  )
}
