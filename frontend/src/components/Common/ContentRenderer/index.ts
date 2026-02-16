/**
 * Common ContentRenderer Re-exports
 *
 * This module provides a stable import path for ContentRenderer across the app.
 * Primary implementation lives at @/components/Page/primitives/ContentRenderer/
 *
 * Usage:
 *   import { ContentRenderer, type Content } from "@/components/Common/ContentRenderer"
 */

// Re-export everything from the primary implementation
export * from "@/components/Page/primitives/ContentRenderer"

// Re-export compatibility helpers
export { renderContent, renderNodeContent } from "./renderContent"
export { nodeToContent, toContent } from "./nodeToContent"