/**
 * renderContent - Compatibility helper for migration
 *
 * This function provides backwards compatibility for files that use the
 * old `renderContent(node)` pattern. New code should use ContentRenderer
 * component directly.
 *
 * MIGRATION PATH:
 *   Before: {renderContent(currentNode)}
 *   After:  <ContentRenderer content={nodeToContent(currentNode)} />
 *
 * This helper enables incremental migration without breaking changes.
 */
import type { ReactNode } from "react"
import type { ContentFormat, StoryNodePublic } from "@/client"
import {
  ContentRenderer,
  type ContentVariant,
} from "@/components/Page/primitives/ContentRenderer"
import { nodeToContent, toContent } from "./nodeToContent"

/**
 * Render content from a StoryNodePublic
 *
 * @deprecated Use <ContentRenderer content={nodeToContent(node)} /> instead
 * @param node - The story node to render
 * @param variant - UX variant (default: "card")
 * @returns ReactNode
 */
export function renderContent(
  node: StoryNodePublic,
  variant: ContentVariant = "card"
): ReactNode {
  const content = nodeToContent(node, variant)
  return <ContentRenderer content={content} safeMode={true} />
}

/**
 * Render content from raw string and format
 *
 * @deprecated Use <ContentRenderer content={...} /> directly
 * @param content - Raw content string
 * @param format - ContentFormat
 * @param variant - UX variant (default: "card")
 * @returns ReactNode
 */
export function renderNodeContent(
  content: string,
  format: ContentFormat | null,
  variant: ContentVariant = "card"
): ReactNode {
  const contentObj = toContent(content, format, variant)
  return <ContentRenderer content={contentObj} safeMode={true} />
}