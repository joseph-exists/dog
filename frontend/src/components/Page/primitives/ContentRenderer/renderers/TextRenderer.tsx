/**
 * TextRenderer - Plain text content
 *
 * Respects variant for layout decisions.
 */
import type { ContentProps } from "../types"

export function TextRenderer({
  content,
  variant,
  className,
}: ContentProps<"text">) {
  const text = typeof content.value === "string" ? content.value : ""

  // Variant-specific rendering
  switch (variant) {
    case "tooltip":
      return (
        <span className={`text-sm truncate max-w-xs ${className ?? ""}`}>
          {text.slice(0, 100)}
          {text.length > 100 && "..."}
        </span>
      )

    case "inline":
      return <span className={`truncate ${className ?? ""}`}>{text}</span>

    case "background":
      // Text as background doesn't make sense - render nothing
      return null

    default:
      // card, page, preview, embed, modal, thumbnail
      return (
        <p className={`whitespace-pre-wrap ${className ?? ""}`}>
          {text || "(No content)"}
        </p>
      )
  }
}
