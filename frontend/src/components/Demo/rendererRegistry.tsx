import type { ReactNode } from "react"
import type { UserAgentConfigPublic } from "@/client/types.gen"
import { resolveShadowRepoGitViewConfig } from "@/components/Demo/gitViewConfig"
import {
  A2UIPanel,
  CanvasPanel,
  DebugPanel,
  ParticipantPanel,
  SoloStoryPlayerPanel,
  StoryEditorPanel,
} from "@/components/Room"
import type { TesserScript } from "@/services/demoService"
import type { ResolvedDemoSessionViewModel } from "@/services/demoService"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"
import { AgentRosterBlock } from "./blocks/AgentRosterBlock"
import { ContributionFeedBlock } from "./blocks/ContributionFeedBlock"
import { FileExplorerBlock } from "./blocks/FileExplorerBlock"
import { GitViewBlock } from "./blocks/GitViewBlock"
import { OrchestratorStateBlock } from "./blocks/OrchestratorStateBlock"
import { GitViewPanel } from "./panels/GitViewPanel"
import { StoryMetadataBlock } from "./blocks/StoryMetadataBlock"
import { ToolCapabilityBlock } from "./blocks/ToolCapabilityBlock"
import { DemoChatPanel } from "./DemoChatPanel"
import { DemoStoryPanel } from "./DemoStoryPanel"
import type {
  RuntimeDemoBlockType,
  RuntimeDemoPanelKind,
} from "./demoRuntimeCapabilities"

type DemoPanelSpec = NonNullable<
  ResolvedDemoSessionViewModel["composition"]["panels"]
>[number]
type DemoBlockSpec = NonNullable<
  ResolvedDemoSessionViewModel["composition"]["blocks"]
>[number]

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
  demoConfigId: string
  metadataJson: Record<string, unknown>
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
  onSelectRepoFileForDebug?: (selectionKey: string, path: string | null) => void
  getFileRoomContextState?: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
    isBinary: boolean
    hasContent: boolean
  }) => {
    included: boolean
    pending: boolean
    canToggle: boolean
    disabledReason?: string | null
  }
  onToggleFileRoomContext?: (payload: {
    panelId: string
    repoId: string
    repoSlug: string
    path: string
    ref: string
    content: string
    contentType: string | null
    encoding: string | null
    sizeBytes: number | null
    isBinary: boolean
    isTruncated: boolean
    truncationReason: string | null
  }) => Promise<void>
  debugSelectedRepoFiles?: Array<{ selectionKey: string; path: string }>
  debugRepoContextFiles?: Array<{
    contextId: string
    repoId: string
    repoSlug: string | null
    path: string
    ref: string
    source: string
    sizeBytes: number | null
    isTruncated: boolean
    payload: Record<string, unknown>
  }>
  canManageRoomContext?: boolean
  onRemoveRepoContextFile?: (contextId: string) => Promise<void>
  renderContentPayload: (value: unknown, fallbackLabel: string) => ReactNode
  onRenderCanvas: (
    panelId: string,
    payload?: {
      scriptName?: string
      title?: string
      subtitle?: string | null
      scriptInput?: Record<string, unknown>
    },
  ) => Promise<void>
  canvasRenderStateByPanelId: Record<
    string,
      {
        isRendering: boolean
        status: string | null
        error: string | null
        lastJobId: string | null
        lastRequestId: string | null
        lastCommitSha: string | null
        lastScriptName: string | null
    }
  >
  canvasSvgOverrideByPanelId: Record<string, string>
  availableTesserScripts?: TesserScript[]
  onRequestTesserScriptHelp?: (scriptName: string) => Promise<string | null>
  onRequestTesserExamplesIndex?: () => Promise<string | null>
}

export interface DemoBlockRendererContext {
  renderContentPayload: (value: unknown, fallbackLabel: string) => ReactNode
  metadataJson: Record<string, unknown>
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
  onSelectRepoFileForDebug?: (selectionKey: string, path: string | null) => void
  getFileRoomContextState?: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
    isBinary: boolean
    hasContent: boolean
  }) => {
    included: boolean
    pending: boolean
    canToggle: boolean
    disabledReason?: string | null
  }
  onToggleFileRoomContext?: (payload: {
    panelId: string
    repoId: string
    repoSlug: string
    path: string
    ref: string
    content: string
    contentType: string | null
    encoding: string | null
    sizeBytes: number | null
    isBinary: boolean
    isTruncated: boolean
    truncationReason: string | null
  }) => Promise<void>
}

type DemoPanelRenderer = (
  panel: DemoPanelSpec,
  ctx: DemoPanelRendererContext,
) => ReactNode

type DemoBlockRenderer = (
  block: DemoBlockSpec,
  ctx: DemoBlockRendererContext,
) => ReactNode

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function getNestedRecord(
  value: unknown,
  path: string[],
): Record<string, unknown> | null {
  let cursor: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(cursor)) return null
    cursor = cursor[segment]
  }
  return isObjectRecord(cursor) ? cursor : null
}

function getNestedString(value: unknown, path: string[]): string | null {
  let cursor: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(cursor)) return null
    cursor = cursor[segment]
  }
  return typeof cursor === "string" && cursor.trim().length > 0 ? cursor : null
}

function getNestedBoolean(value: unknown, path: string[]): boolean | null {
  let cursor: unknown = value
  for (const segment of path) {
    if (!isObjectRecord(cursor)) return null
    cursor = cursor[segment]
  }
  return typeof cursor === "boolean" ? cursor : null
}

function getFirstCalloutStyleLabel(presentationJson: unknown): string | null {
  const callouts = getNestedRecord(presentationJson, ["callouts"])
  if (!callouts) return null
  for (const calloutValue of Object.values(callouts)) {
    if (!isObjectRecord(calloutValue)) continue
    const style = calloutValue.style
    if (typeof style === "string" && style.trim().length > 0) {
      return style
    }
  }
  return null
}

function parseChatPresentation(presentationJson: unknown): {
  feedDensity: "comfortable" | "compact"
  messageRowHighlightCss: string | null
  calloutLabel: string | null
} {
  const density = getNestedString(presentationJson, ["tokens", "feed_density"])
  const feedDensity = density === "compact" ? "compact" : "comfortable"
  const highlightEnabled = getNestedBoolean(presentationJson, [
    "effects",
    "message_row_highlight",
    "enable",
  ])
  const highlightCss = getNestedString(presentationJson, [
    "effects",
    "message_row_highlight",
    "css",
  ])
  const calloutStyle = getFirstCalloutStyleLabel(presentationJson)
  return {
    feedDensity,
    messageRowHighlightCss:
      highlightCss ??
      (highlightEnabled === true
        ? "inset 0 0 0 1px rgba(59, 130, 246, 0.35)"
        : null),
    calloutLabel: calloutStyle ? `Chat callout style: ${calloutStyle}` : null,
  }
}

function parseContributionFeedPresentation(presentationJson: unknown): {
  feedDensity: "comfortable" | "compact"
  rowHighlightCss: string | null
  calloutLabel: string | null
} {
  // Read feed_density token; defaults to "comfortable"
  // Future: If per-property overrides are needed, add tokens like
  // tokens.feed_container_padding that take precedence over preset values
  const density = getNestedString(presentationJson, ["tokens", "feed_density"])
  const feedDensity = density === "compact" ? "compact" : "comfortable"

  const rowHighlightCss = getNestedString(presentationJson, [
    "effects",
    "message_row_highlight",
    "css",
  ])
  const calloutStyle = getFirstCalloutStyleLabel(presentationJson)
  return {
    feedDensity,
    rowHighlightCss,
    calloutLabel: calloutStyle
      ? `Contribution callout style: ${calloutStyle}`
      : null,
  }
}

function parseOrchestratorStatePresentation(presentationJson: unknown): {
  stackDensity: "comfortable" | "compact"
  calloutLabel: string | null
} {
  // Read stack_density token; defaults to "comfortable"
  // Future: If per-property overrides are needed, add tokens like
  // tokens.stack_container_padding that take precedence over preset values
  const density = getNestedString(presentationJson, ["tokens", "stack_density"])
  const stackDensity = density === "compact" ? "compact" : "comfortable"

  const calloutStyle = getFirstCalloutStyleLabel(presentationJson)
  return {
    stackDensity,
    calloutLabel: calloutStyle ? `Orchestrator callout: ${calloutStyle}` : null,
  }
}

function parseToolCapabilityPresentation(presentationJson: unknown): {
  matrixDensity: "standard" | "compact"
  calloutLabel: string | null
} {
  // Read matrix_density token; defaults to "standard"
  // Future: If per-property overrides are needed, add tokens like
  // tokens.matrix_container_padding that take precedence over preset values
  const density = getNestedString(presentationJson, [
    "tokens",
    "matrix_density",
  ])
  const matrixDensity = density === "compact" ? "compact" : "standard"

  const calloutStyle = getFirstCalloutStyleLabel(presentationJson)
  return {
    matrixDensity,
    calloutLabel: calloutStyle
      ? `Tool capability callout: ${calloutStyle}`
      : null,
  }
}

function parseCapabilityCalloutLabel(
  presentationJson: unknown,
  prefix: string,
): string | null {
  const style = getFirstCalloutStyleLabel(presentationJson)
  return style ? `${prefix}: ${style}` : null
}

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

function renderStructuredBlock(block: DemoBlockSpec, label: string): ReactNode {
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

const panelRenderers: Record<RuntimeDemoPanelKind, DemoPanelRenderer> = {
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
  chat: (panel, ctx) => {
    const parsed = parseChatPresentation(
      (panel as { presentation_json?: unknown }).presentation_json,
    )
    return (
      <DemoChatPanel
        roomId={ctx.roomId}
        isConnected={ctx.isConnected}
        sendViaWebSocket={ctx.sendViaWebSocket}
        streamingMessage={ctx.streamingMessage}
        feedDensity={parsed.feedDensity}
        messageRowHighlightCss={parsed.messageRowHighlightCss ?? undefined}
        calloutLabel={parsed.calloutLabel}
      />
    )
  },
  content: (panel, ctx) =>
    ctx.renderContentPayload(
      getPanelContentPayload(panel),
      "Content panel is configured, but no valid content_json payload was provided.",
    ),
  gitView: (panel, ctx) => (
    <GitViewPanel
      panelId={panel.id}
      title={panel.title}
      selectionKey={`gitViewPanel:${panel.id}`}
      options={panel.options}
      metadataJson={ctx.metadataJson}
      onSelectFileForDebug={ctx.onSelectRepoFileForDebug}
      getRoomContextState={ctx.getFileRoomContextState}
      onToggleRoomContext={ctx.onToggleFileRoomContext}
    />
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
  canvas: (panel, ctx) => {
    const panelOptions = (panel as { options?: unknown }).options
    const extras = getNestedRecord(panelOptions, ["extras"])
    const persistedSvg =
      typeof extras?.render_svg === "string" ? extras.render_svg : null
    const liveSvg = ctx.canvasSvgOverrideByPanelId[panel.id]
    const svgContent = typeof liveSvg === "string" ? liveSvg : persistedSvg
    const renderState = ctx.canvasRenderStateByPanelId[panel.id]
    return (
      <CanvasPanel
        svgContent={svgContent}
        canWrite={ctx.canWrite}
        onRenderSvg={(payload) => ctx.onRenderCanvas(panel.id, payload)}
        isRendering={renderState?.isRendering ?? false}
        renderStatus={renderState?.status ?? null}
        renderError={renderState?.error ?? null}
        lastJobId={renderState?.lastJobId ?? null}
        lastRequestId={renderState?.lastRequestId ?? null}
        lastCommitSha={renderState?.lastCommitSha ?? null}
        lastScriptName={renderState?.lastScriptName ?? null}
        availableScripts={ctx.availableTesserScripts ?? []}
        onRequestScriptHelp={ctx.onRequestTesserScriptHelp}
        onRequestExamplesIndex={ctx.onRequestTesserExamplesIndex}
      />
    )
  },
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
      <SoloStoryPlayerPanel
        storyId={ctx.roomStoryId}
        runtimeNotice="Local-only panel. This player does not stay in sync with the room runtime or other panels."
      />
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
      selectedRepoFiles={ctx.debugSelectedRepoFiles ?? []}
      repoContextFiles={ctx.debugRepoContextFiles ?? []}
      canManageRoomContext={ctx.canManageRoomContext ?? false}
      onRemoveRepoContextFile={ctx.onRemoveRepoContextFile}
    />
  ),
}

const blockRenderers: Record<RuntimeDemoBlockType, DemoBlockRenderer> = {
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
      calloutLabel={parseCapabilityCalloutLabel(
        (block as { presentation_json?: unknown }).presentation_json,
        "Story metadata callout",
      )}
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
  orchestratorState: (block, ctx) => {
    const parsed = parseOrchestratorStatePresentation(
      (block as { presentation_json?: unknown }).presentation_json,
    )
    return (
      <OrchestratorStateBlock
        title={block.title}
        config={(block as { config_json?: unknown }).config_json}
        isConnected={ctx.isConnected}
        autoRespond={ctx.autoRespond}
        runtimePolicy={ctx.runtimePolicy}
        runtimeHasRuntime={ctx.runtimeHasRuntime}
        roomAgents={ctx.roomAgentsAsAgentData}
        stackDensity={parsed.stackDensity}
        calloutLabel={parsed.calloutLabel}
      />
    )
  },
  toolCapability: (block, ctx) => {
    const parsed = parseToolCapabilityPresentation(
      (block as { presentation_json?: unknown }).presentation_json,
    )
    return (
      <ToolCapabilityBlock
        title={block.title}
        config={(block as { config_json?: unknown }).config_json}
        roomAgents={ctx.roomAgentsAsAgentData}
        availableAgents={ctx.availableAgents}
        matrixDensity={parsed.matrixDensity}
        calloutLabel={parsed.calloutLabel}
      />
    )
  },
  contributionFeed: (block, ctx) => {
    const parsed = parseContributionFeedPresentation(
      (block as { presentation_json?: unknown }).presentation_json,
    )
    return (
      <ContributionFeedBlock
        title={block.title}
        config={(block as { config_json?: unknown }).config_json}
        messages={ctx.debugMessages}
        streamingMessage={ctx.streamingMessage}
        feedDensity={parsed.feedDensity}
        rowHighlightCss={parsed.rowHighlightCss ?? undefined}
        calloutLabel={parsed.calloutLabel}
      />
    )
  },
  gitView: (block, ctx) => (
    <GitViewBlock
      title={block.title}
      selectionKey={`gitView:${block.id}`}
      config={resolveShadowRepoGitViewConfig(
        (block as { config_json?: unknown }).config_json,
        ctx.metadataJson,
      )}
      rawConfig={(block as { config_json?: unknown }).config_json}
      onSelectFileForDebug={ctx.onSelectRepoFileForDebug}
      getRoomContextState={ctx.getFileRoomContextState}
      onToggleRoomContext={ctx.onToggleFileRoomContext}
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
  const panelKind = panel.kind as RuntimeDemoPanelKind
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
  const blockType = block.type as RuntimeDemoBlockType
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
