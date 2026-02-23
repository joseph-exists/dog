export const ACTIVE_RUNTIME_DEMO_PANEL_KINDS = [
  "storyRuntime",
  "chat",
  "content",
  "participantPanel",
  "canvas",
  "a2ui",
  "storyEditor",
  "storyPlayer",
  "debug",
] as const

export const ACTIVE_RUNTIME_DEMO_BLOCK_TYPES = [
  "context",
  "content",
  "story",
  "storyMetadata",
  "agentRoster",
  "orchestratorState",
  "toolCapability",
  "contributionFeed",
  "gitView",
  "fileExplorer",
] as const

export type RuntimeDemoPanelKind = (typeof ACTIVE_RUNTIME_DEMO_PANEL_KINDS)[number]
export type RuntimeDemoBlockType = (typeof ACTIVE_RUNTIME_DEMO_BLOCK_TYPES)[number]
