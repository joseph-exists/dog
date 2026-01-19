// src/components/Page/blocks/IdentityBlock.tsx
import { Pencil } from "lucide-react"

import { Button } from "@/components/ui/button"

export interface IdentityBlockConfig {
  showTagline: boolean
}

export interface IdentityBlockProps {
  config: IdentityBlockConfig
  entity: { name: string; tagline?: string }
  canEdit?: boolean
  onEdit?: () => void
}

/**
 * IdentityBlock - Displays entity name and optional tagline
 *
 * Centered layout with large heading for the name.
 * Shows tagline below when configured and available.
 * When canEdit is true, shows a pencil icon button for editing.
 */
export function IdentityBlock({
  config,
  entity,
  canEdit = false,
  onEdit,
}: IdentityBlockProps) {
  return (
    <div className="text-center">
      <div className="inline-flex items-center gap-2">
        <h1 className="text-2xl font-bold">{entity.name}</h1>
        {canEdit && (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            onClick={onEdit}
            aria-label="Edit identity"
          >
            <Pencil className="h-4 w-4" />
          </Button>
        )}
      </div>
      {config.showTagline && entity.tagline && (
        <p className="text-sm text-muted-foreground">{entity.tagline}</p>
      )}
    </div>
  )
}
