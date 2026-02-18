/**
 * Renderer Registry - Format to renderer mapping
 *
 * Assembles all format renderers for ContentRenderer dispatch.
 *
 * Note: Uses RendererEntry (loose typing) internally because TypeScript's
 * function parameter contravariance prevents storing format-specific
 * renderers in a generic collection. Type safety is maintained by:
 * - Each renderer being individually strongly typed
 * - Runtime dispatch matching format to correct renderer
 */

import type { ContentFormat } from "@/client"
// Import plugin resolution (lazy to avoid circular deps)
import { resolveRenderer as pluginResolveRenderer } from "./pluginRegistry"
import { CodeRenderer } from "./renderers/CodeRenderer"
import { HTMLRenderer } from "./renderers/HTMLRenderer"
import { ImageRenderer } from "./renderers/ImageRenderer"
import { JSONRenderer } from "./renderers/JSONRenderer"
import { MarkdownRenderer } from "./renderers/MarkdownRenderer"
import { MDXRenderer } from "./renderers/MDXRenderer"
import { SVGRenderer } from "./renderers/SVGRenderer"
import { TextRenderer } from "./renderers/TextRenderer"
import type { PluginResolutionResult, RendererEntry } from "./types"

/**
 * Core registry mapping ContentFormat to renderer components
 */
export const rendererRegistry: Partial<Record<ContentFormat, RendererEntry>> = {
  text: { format: "text", Component: TextRenderer },
  code: { format: "code", Component: CodeRenderer },
  html: { format: "html", Component: HTMLRenderer },
  json: { format: "json", Component: JSONRenderer },
  svg: { format: "svg", Component: SVGRenderer },
  image: { format: "image", Component: ImageRenderer },
  markdown: { format: "markdown", Component: MarkdownRenderer },
  mdx: { format: "mdx", Component: MDXRenderer },
}

/**
 * Get renderer for a given format
 *
 * UPDATED: Checks plugin registry first, then falls back to core.
 */
export function getRenderer(format: ContentFormat): RendererEntry | undefined {
  // Check plugins first
  const resolved = pluginResolveRenderer(format)
  if (resolved) {
    return resolved.renderer
  }

  // Fallback to core registry (shouldn't reach here if pluginResolveRenderer
  // already checks core, but kept for safety)
  return rendererRegistry[format]
}

/**
 * Get full resolution info including plugin source
 *
 * Use this when you need to know which plugin provided the renderer.
 */
export function resolveRenderer(
  format: ContentFormat,
): PluginResolutionResult | null {
  return pluginResolveRenderer(format)
}
// /**
//  * Registry mapping ContentFormat to renderer components
//  */
// export const rendererRegistry: Partial<Record<ContentFormat, RendererEntry>> = {
//   text: { format: "text", Component: TextRenderer },
//   code: { format: "code", Component: CodeRenderer },
//   html: { format: "html", Component: HTMLRenderer },
//   json: { format: "json", Component: JSONRenderer },
//   svg: { format: "svg", Component: SVGRenderer },
//   image: { format: "image", Component: ImageRenderer },
//   markdown: { format: "markdown", Component: MarkdownRenderer },
//   mdx: { format: "mdx", Component: MDXRenderer },
//   // yaml: Future
//   // audio: Future
//   // video: Future
// }

// /**
//  * Get renderer for a given format
//  */
// export function getRenderer(format: ContentFormat): RendererEntry | undefined {
//   return rendererRegistry[format]
// }
