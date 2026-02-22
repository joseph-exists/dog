import type { ReactNode } from "react"
import { A2UIPanel, CanvasPanel, DebugPanel, ParticipantPanel, StoryEditorPanel, StoryPlayerPanel } from "@/components/Room"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import type { MessageViewModel, ParticipantViewModel } from "@/services/roomService"
import type { ResolvedDemoSessionViewModel } from "@/services/demoService"
import { AgentRosterBlock } from "./blocks/AgentRosterBlock"
import { ContributionFeedBlock } from "./blocks/ContributionFeedBlock"
import { FileExplorerBlock } from "./blocks/FileExplorerBlock"
import { GitViewBlock } from "./blocks/GitViewBlock"
import { OrchestratorStateBlock } from "./blocks/OrchestratorStateBlock"
import { StoryMetadataBlock } from "./blocks/StoryMetadataBlock"
import { ToolCapabilityBlock } from "./blocks/ToolCapabilityBlock"
import { DemoChatPanel } from "./DemoChatPanel"
import { DemoStoryPanel } from "./DemoStoryPanel"

type DemoPanelSpec = NonNullable<ResolvedDemoSessionViewModel["composition"]["panels"]>[number]
type DemoBlockSpec = NonNullable<ResolvedDemoSessionViewModel["composition"]["blocks"]>[number]

type ActiveDemoPanelKind =
  | "storyRuntime"
  | "chat"
  | "content"
  | "participantPanel"
  | "canvas"
  | "a2ui"
  | "storyEditor"
  | "storyPlayer"
  | "debug"

type ActiveDemoBlockType =
  | "context"
  | "content"
  | "story"
  | "storyMetadata"
  | "agentRoster"
  | "orchestratorState"
  | "toolCapability"
  | "contributionFeed"
  | "gitView"
  | "fileExplorer"

export interface DemoRoomAgentData {
  id: string
  name: string
  description: string | null
  participation_mode: string
  scope: string
  is_coordinator: boolean
  is_enabled: boolean
}

export interface DemoPanelRendererContext {
  roomId: string
  roomTitle: string
  roomStoryId: string | null
  canWrite: boolean
  autoRespond: boolean
  onSendMessage: (message: string) => void
  isConnected: boolean
  sendViaWebSocket: (content: string) => void
  streamingMessage: { agent_name: string; content: string } | null
  activeUsers: ParticipantViewModel[]
  roomAgentsAsAgentData: DemoRoomAgentData[]
  debugActiveAgents: ParticipantViewModel[]
  availableAgents: UserAgentConfigPublic[]
  existingAgentIds: string[]
  onAddAgent: (agent: { id: string; name?: string | null }) => Promise<void>
  onRemoveAgent: (agent: { id: string; name?: string | null }) => Promise<void>
  onToggleAgent: (agentId: string, activate: boolean) => Promise<void>
  onRemoveUser: (participantId: string) => Promise<void>
  isParticipantPanelLoading: boolean
  debugMessages: MessageViewModel[]
  showInternalMessages: boolean
  onToggleInternalMessages: (enabled: boolean) => void
  renderContentPayload: (value: unknown, fallbackLabel: string) => ReactNode
}

export interface DemoBlockRendererContext {
  renderContentPayload: (value: unknown, fallbackLabel: string) => ReactNode
  roomId: string
  roomTitle: string
  roomStoryId: string | null
  runtimePolicy: "auto" | "manual" | "owner_only"
  runtimeHasRuntime: boolean
  autoStartError: string | null
  autoRespond: boolean
  isConnected: boolean
  debugMessages: MessageViewModel[]
  streamingMessage: { agent_name: string; content: string } | null
  activeUsers: ParticipantViewModel[]
  roomAgentsAsAgentData: DemoRoomAgentData[]
  availableAgents: UserAgentConfigPublic[]
}

type DemoPanelRenderer = (
  panel: DemoPanelSpec,
  ctx: DemoPanelRendererContext,
) => ReactNode

type DemoBlockRenderer = (
  block: DemoBlockSpec,
  ctx: DemoBlockRendererContext,
) => ReactNode

function getPanelContentPayload(panel: DemoPanelSpec): unknown {
  const options = panel.options as { content_json?: unknown } | undefined
  return options?.content_json
}

function renderJSON(payload: unknown): ReactNode {
  return (
    <pre className="mt-2 max-h-64 overflow-auto rounded border bg-muted/40 p-3 text-xs">
      {JSON.stringify(payload ?? {}, null, 2)}
    </pre>
  )
}

function renderStructuredBlock(
  block: DemoBlockSpec,
  label: string,
): ReactNode {
  const configJSON = (block as { config_json?: unknown }).config_json ?? {}
  return (
    <div className="p-4">
      <div className="text-sm font-medium">{label}</div>
      <div className="text-xs text-muted-foreground mt-1">
        This block type is wired and awaiting dedicated presentation.
      </div>
      {renderJSON(configJSON)}
    </div>
  )
}

const panelRenderers: Record<ActiveDemoPanelKind, DemoPanelRenderer> = {
  storyRuntime: (_panel, ctx) => (
    <DemoStoryPanel
      roomId={ctx.roomId}
      roomTitle={ctx.roomTitle}
      roomStoryId={ctx.roomStoryId}
      canWrite={ctx.canWrite}
      autoRespond={ctx.autoRespond}
      onSendMessage={ctx.onSendMessage}
    />
  ),
  chat: (_panel, ctx) => (
    <DemoChatPanel
      roomId={ctx.roomId}
      isConnected={ctx.isConnected}
      sendViaWebSocket={ctx.sendViaWebSocket}
      streamingMessage={ctx.streamingMessage}
    />
  ),
  content: (panel, ctx) =>
    ctx.renderContentPayload(
      getPanelContentPayload(panel),
      "Content panel is configured, but no valid content_json payload was provided.",
    ),
  participantPanel: (_panel, ctx) => (
    <ParticipantPanel
      activeUsers={ctx.activeUsers}
      roomAgents={ctx.roomAgentsAsAgentData}
      availableAgents={ctx.availableAgents}
      existingAgentIds={ctx.existingAgentIds}
      onAddAgent={ctx.onAddAgent}
      onRemoveAgent={ctx.onRemoveAgent}
      onToggleAgent={ctx.onToggleAgent}
      onRemoveParticipant={ctx.onRemoveUser}
      canManage={ctx.canWrite}
      isLoading={ctx.isParticipantPanelLoading}
    />
  ),
  canvas: () => <CanvasPanel />,
  a2ui: (_panel, ctx) => <A2UIPanel roomId={ctx.roomId} />,
  storyEditor: (_panel, ctx) =>
    ctx.roomStoryId ? (
      <StoryEditorPanel storyId={ctx.roomStoryId} />
    ) : (
      <div className="h-full p-4 text-sm text-muted-foreground">
        Story editor panel requires a story attached to this room.
      </div>
    ),
  storyPlayer: (_panel, ctx) =>
    ctx.roomStoryId ? (
      <StoryPlayerPanel storyId={ctx.roomStoryId} />
    ) : (
      <div className="h-full p-4 text-sm text-muted-foreground">
        Story player panel requires a story attached to this room.
      </div>
    ),
  debug: (_panel, ctx) => (
    <DebugPanel
      messages={ctx.debugMessages}
      streamingMessage={ctx.streamingMessage}
      isConnected={ctx.isConnected}
      activeAgents={ctx.debugActiveAgents}
      showInternalMessages={ctx.showInternalMessages}
      onToggleInternalMessages={ctx.onToggleInternalMessages}
    />
  ),
}

const blockRenderers: Record<ActiveDemoBlockType, DemoBlockRenderer> = {
  context: (block, ctx) =>
    ctx.renderContentPayload(
      (block as { content_json?: unknown }).content_json,
      `Block "${block.id}" has no supported content payload.`,
    ),
  content: (block, ctx) =>
    ctx.renderContentPayload(
      (block as { content_json?: unknown }).content_json,
      `Block "${block.id}" has no supported content payload.`,
    ),
  story: (block) => renderStructuredBlock(block, "Story Block"),
  storyMetadata: (block, ctx) => (
    <StoryMetadataBlock
      title={block.title}
      roomId={ctx.roomId}
      roomTitle={ctx.roomTitle}
      roomStoryId={ctx.roomStoryId}
      runtimePolicy={ctx.runtimePolicy}
      runtimeHasRuntime={ctx.runtimeHasRuntime}
      autoStartError={ctx.autoStartError}
      config={(block as { config_json?: unknown }).config_json}
    />
  ),
  agentRoster: (block, ctx) => (
    <AgentRosterBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      activeUsers={ctx.activeUsers}
      roomAgents={ctx.roomAgentsAsAgentData}
    />
  ),
  orchestratorState: (block, ctx) => (
    <OrchestratorStateBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      isConnected={ctx.isConnected}
      autoRespond={ctx.autoRespond}
      runtimePolicy={ctx.runtimePolicy}
      runtimeHasRuntime={ctx.runtimeHasRuntime}
      roomAgents={ctx.roomAgentsAsAgentData}
    />
  ),
  toolCapability: (block, ctx) => (
    <ToolCapabilityBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      roomAgents={ctx.roomAgentsAsAgentData}
      availableAgents={ctx.availableAgents}
    />
  ),
  contributionFeed: (block, ctx) => (
    <ContributionFeedBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      messages={ctx.debugMessages}
      streamingMessage={ctx.streamingMessage}
    />
  ),
  gitView: (block) => (
    <GitViewBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
    />
  ),
  fileExplorer: (block) => (
    <FileExplorerBlock
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
    />
  ),
}

export function renderDemoPanel(
  panel: DemoPanelSpec,
  ctx: DemoPanelRendererContext,
): ReactNode {
  const panelKind = panel.kind as ActiveDemoPanelKind
  const renderer = panelRenderers[panelKind]
  if (!renderer) {
    return (
      <div className="h-full p-4 text-sm text-muted-foreground">
        Unsupported panel kind: {panel.kind}
      </div>
    )
  }
  return renderer(panel, ctx)
}

export function renderDemoBlock(
  block: DemoBlockSpec,
  ctx: DemoBlockRendererContext,
): ReactNode {
  const blockType = block.type as ActiveDemoBlockType
  const renderer = blockRenderers[blockType]
  if (!renderer) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Block type "{block.type}" is not mapped yet.
      </div>
    )
  }
  return renderer(block, ctx)
}
