/**
 * nodeToContent - Adapter for StoryNodePublic → Content
 *
 * Converts backend StoryNodePublic objects to the Content shape
 * expected by ContentRenderer.
 */
import type { ContentFormat, StoryNodePublic } from "@/client"
import type { Content, ContentVariant } from "@/components/Page/primitives/ContentRenderer"

/**
 * Convert a StoryNodePublic to a Content object
 *
 * @param node - The story node from backend
 * @param variant - Optional UX variant override
 * @returns Content object for ContentRenderer
 */
export function nodeToContent(
  node: StoryNodePublic,
  variant: ContentVariant = "card"
): Content {
  return {
    format: (node.content_format as ContentFormat) || "text",
    value: node.content || "",
    metadata: {
      variant,
      label: node.title,
    },
  }
}

/**
 * Convert raw content string and format to Content object
 *
 * @param content - Raw content string
 * @param format - ContentFormat
 * @param variant - Optional UX variant
 * @returns Content object for ContentRenderer
 */
export function toContent(
  content: string,
  format: ContentFormat | null,
  variant: ContentVariant = "card"
): Content {
  return {
    format: format || "text",
    value: content || "",
    metadata: { variant },
  }
}