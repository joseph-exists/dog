// src/components/Page/blocks/BioBlock.tsx
import { BlockContainer } from "../primitives"

export interface BioBlockConfig {
  maxLength?: number
  allowRichText?: boolean
}

export interface BioContent {
  text: string
}

export interface BioBlockProps {
  config: BioBlockConfig
  content?: BioContent
  className?: string
}

/**
 * BioBlock - Displays an "About" section with bio text
 *
 * Shows bio text with optional truncation based on maxLength config.
 * Returns null if no text content exists.
 * View-only block - no edit functionality.
 */
export function BioBlock({ config, content, className }: BioBlockProps) {
  // Empty state — show placeholder so block is visible in edit mode
  if (!content?.text) {
    return (
      <BlockContainer title="About" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">
            No bio text yet.
          </p>
        </div>
      </BlockContainer>
    )
  }

  const { maxLength } = config

  // Truncate bio if maxLength is set and exceeded
  const displayBio =
    maxLength && content.text.length > maxLength
      ? `${content.text.slice(0, maxLength)}...`
      : content.text

  return (
    <BlockContainer title="About" className={className}>
      <div className="p-4">
        <p className="text-sm text-foreground whitespace-pre-wrap">
          {displayBio}
        </p>
      </div>
    </BlockContainer>
  )
}
