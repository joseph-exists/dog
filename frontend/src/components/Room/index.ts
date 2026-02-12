/**
 * Room Component System
 *
 * Unified room system with multi-panel support.
 * See: docs/plans/2026-01-19-rooms-ui-design.md
 */

// Cards
export * from "./cards"
// Layout Dialog
export {
  PanelLayoutDialog,
  type PanelLayoutDialogProps,
} from "./Dialogs/PanelLayoutDialog"
// Panels
export * from "./panels"
// Primitives
export * from "./primitives"
export {
  InteractivePreview,
  type InteractivePreviewProps,
  type PreviewPanel,
} from "./RoomShell/InteractivePreview"
export {
  type LayoutSource,
  LayoutSourceSelector,
  type LayoutSourceSelectorProps,
} from "./RoomShell/LayoutSourceSelector"
// Header
export { RoomHeader, type RoomType } from "./RoomShell/RoomHeader"
// Layout
export { type PanelConfig, RoomLayout } from "./RoomShell/RoomLayout"
// Shell
export { RoomShell } from "./RoomShell/RoomShell"
