/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Cards
export * from "./cards"
export {
  InteractivePreview,
  type InteractivePreviewProps,
  type PreviewPanel,
} from "./InteractivePreview"
export {
  type LayoutSource,
  LayoutSourceSelector,
  type LayoutSourceSelectorProps,
} from "./LayoutSourceSelector"
// Layout Dialog
export {
  PanelLayoutDialog,
  type PanelLayoutDialogProps,
} from "./PanelLayoutDialog"
// Panels
export * from "./panels"
// Primitives
export * from "./primitives"
// Header
export { RoomHeader, type RoomType } from "./RoomHeader"
// Layout
export { type PanelConfig, RoomLayout } from "./RoomLayout"
// Shell
export { RoomShell } from "./RoomShell"
