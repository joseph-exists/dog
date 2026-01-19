// src/components/Page/blocks/BioBlock.tsx
import { Pencil } from "lucide-react"

import { Button } from "@/components/ui/button"
import { BlockContainer } from "../primitives"

export interface BioBlockConfig {
  maxLength?: number
  allowRichText?: boolean
}

export interface BioBlockProps {
  config: BioBlockConfig
  bio?: string
  canEdit?: boolean
  onEdit?: () => void
}

/**
 * BioBlock - Displays an "About" section with bio text
 *
 * Shows bio text with optional truncation based on maxLength config.
 * When canEdit is true and no bio exists, shows a placeholder.
 * When canEdit is false and no bio exists, renders nothing.
 */
export function BioBlock({
  config,
  bio,
  canEdit = false,
  onEdit,
}: BioBlockProps) {
  // If no bio and can't edit, hide the block entirely
  if (!bio && !canEdit) {
    return null
  }

  const { maxLength } = config

  // Truncate bio if maxLength is set and exceeded
  const displayBio =
    bio && maxLength && bio.length > maxLength
      ? `${bio.slice(0, maxLength)}...`
      : bio

  const headerActions = canEdit ? (
    <Button
      type="button"
      variant="ghost"
      size="icon-sm"
      onClick={onEdit}
      aria-label="Edit bio"
    >
      <Pencil className="h-4 w-4" />
    </Button>
  ) : undefined

  return (
    <BlockContainer title="About" headerActions={headerActions}>
      <div className="p-4">
        {displayBio ? (
          <p className="text-sm text-foreground whitespace-pre-wrap">
            {displayBio}
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
