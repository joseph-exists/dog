// Story component exports
//
// Main exports for the Story feature.
// Use StoryShell as the main container, configure with panel configs.

// Shell and Layout
export { StoryShell, type StoryShellProps } from "./StoryShell"
export { StoryLayout, type PanelConfig } from "./StoryLayout"

// Panels (for use in PanelConfig.render())
export { StoryPlayerPanel, StoryDebugPanel } from "./panels"

// Context (for custom panels that need player state)
export {
  StoryPlayerProvider,
  useStoryPlayerContext,
  type StoryPlayerContextValue,
  type HistoryEntry,
} from "./StoryPlayer"

// Header
export { StoryHeader, type StoryHeaderProps } from "./StoryHeader"

// Dialogs and Lists
export { CreatePageDialog } from "./Dialogs/CreatePageDialog"
export { StoryCard, StoryList, CreateStoryModal } from "./StoryList"

// Registry
export * from "./registry"
