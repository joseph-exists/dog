/**
 * AG-UI (Agent-Generated UI) Components
 *
 * Layered component system:
 * - primitives/  — Individual UI block renderers
 * - content/     — Composite layouts (Stack, Empty)
 * - AgentUIRenderer — Orchestrator dispatching to primitives
 */

export { default as AgentUIRenderer } from "./AgentUIRenderer"
export { AgentUIEmpty, AgentUIStack } from "./content"
export {
  UIActionButtons,
  UIAlertBlock,
  UICardBlock,
  UICodeBlock,
  UICollapsibleBlock,
  UIDividerBlock,
  UIListBlock,
  UIPageLayoutPreview,
  UIProgressBlock,
  UIQuoteBlock,
  UITableBlock,
  UITabsBlock,
} from "./primitives"
export * from "./types"
