// Story component exports
//
// Main exports for the Story feature.
// Use StoryShell as the main container, configure with panel configs.

// Dialogs and Lists
export { CreatePageDialog } from "./Dialogs/CreatePageDialog"
// Panels (for use in PanelConfig.render())
export { StoryDebugPanel, StoryPlayerPanel } from "./panels"
// Registry
export * from "./registry"
// Header
export { StoryHeader, type StoryHeaderProps } from "./StoryHeader"
export { type PanelConfig, StoryLayout } from "./StoryLayout"
export { CreateStoryModal, StoryCard, StoryList } from "./StoryList"
// Context (for custom panels that need player state)
export {
  type HistoryEntry,
  type StoryPlayerContextValue,
  StoryPlayerProvider,
  useStoryPlayerContext,
} from "./StoryPlayer"
// Shell and Layout
export { StoryShell, type StoryShellProps } from "./StoryShell"
