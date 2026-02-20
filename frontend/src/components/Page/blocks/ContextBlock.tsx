// src/components/Page/blocks/BioBlock.tsx
import { BlockContainer } from "../primitives"

export interface ContextBlockConfig {
  maxLength?: number
  allowRichText?: boolean
}

export interface ContextContent {
  text: string
}

export interface ContextBlockProps {
  config: ContextBlockConfig
  content?: ContextContent
  className?: string
}

/**
 * ContextBlock - Displays a "Details" section with text
 *
 * Shows  text with optional truncation based on maxLength config.
 * Returns null if no text content exists.
 * View-only block - no edit functionality.
 */
export function ContextBlock({ config, content, className }: ContextBlockProps) {
  // Empty state — show placeholder so block is visible in edit mode
  if (!content?.text) {
    return (
      <BlockContainer title="Details" className={className}>
        <div className="p-4">
          <p className="text-sm text-muted-foreground italic">
            no text yet.
          </p>
        </div>
      </BlockContainer>
    )
  }

  const { maxLength } = config

  // Truncate bio if maxLength is set and exceeded
  const displayContext =
    maxLength && content.text.length > maxLength
      ? `${content.text.slice(0, maxLength)}...`
      : content.text

  return (
    <BlockContainer title="About" className={className}>
      <div className="p-4">
        <p className="text-sm text-foreground whitespace-pre-wrap">
          {displayContext}
        </p>
      </div>
    </BlockContainer>
  )
}
