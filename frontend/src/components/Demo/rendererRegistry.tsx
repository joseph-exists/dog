import { useQuery } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { UserReposService } from "@/client/sdk.gen"
import type { UserAgentConfigPublic, UserRepoPublic } from "@/client/types.gen"
import { resolveGitViewConfig } from "@/components/Demo/gitViewConfig"
import { resolveLiveRepoExplorerConfig } from "@/components/Demo/liveRepoExplorerConfig"
import { resolveLiveRepoFileViewerConfig } from "@/components/Demo/liveRepoFileViewerConfig"
import { RepoCapabilityPlaceholderPanel } from "@/components/Repo/panels/RepoCapabilityPlaceholderPanel"
import { RepoExplorerPanel } from "@/components/Repo/panels/RepoExplorerPanel"
import { RepoFileViewerPanel } from "@/components/Repo/panels/RepoFileViewerPanel"
import {
  A2UIPanel,
  CanvasPanel,
  DebugPanel,
  ParticipantPanel,
  SoloStoryPlayerPanel,
  StoryEditorPanel,
} from "@/components/Room"
import type {
  ResolvedDemoSessionViewModel,
  TesserScript,
} from "@/services/demoService"
import type {
  MessageViewModel,
  ParticipantViewModel,
} from "@/services/roomService"
import { AgentRosterBlock } from "./blocks/AgentRosterBlock"
import { ContributionFeedBlock } from "./blocks/ContributionFeedBlock"
import { FileExplorerBlock } from "./blocks/FileExplorerBlock"
import { OrchestratorStateBlock } from "./blocks/OrchestratorStateBlock"
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
  onAddUser: (userId: string) => Promise<void>
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
  repoSelections: Record<string, string | null>
  setRepoSelection: (selectionKey: string, path: string | null) => void
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
  repoSelections: Record<string, string | null>
  setRepoSelection: (selectionKey: string, path: string | null) => void
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

function resolveDemoRepoCapabilities(repo: UserRepoPublic) {
  return {
    hasRepoIdentity: true,
    hasFileTree: repo.capabilities?.has_file_tree === true,
    hasBlobContent: repo.capabilities?.has_blob_content === true,
    hasCommitHistory: repo.capabilities?.has_commit_history === true,
  }
}

function useDemoUserRepo(repoId: string | null) {
  return useQuery({
    queryKey: ["demo-live-user-repo", repoId],
    queryFn: () => UserReposService.getUserRepo({ repoId: repoId ?? "" }),
    enabled: typeof repoId === "string" && repoId.length > 0,
  })
}

function DemoRepoGitViewSurface({
  surfaceId,
  title,
  config,
  metadataJson,
  repoSelections,
  setRepoSelection,
  getRoomContextState,
  onToggleRoomContext,
}: {
  surfaceId: string
  title?: string | null
  config: unknown
  metadataJson: Record<string, unknown>
  repoSelections: Record<string, string | null>
  setRepoSelection: (selectionKey: string, path: string | null) => void
  getRoomContextState?: DemoBlockRendererContext["getFileRoomContextState"]
  onToggleRoomContext?: DemoBlockRendererContext["onToggleFileRoomContext"]
}) {
  const resolvedConfig = resolveGitViewConfig(config, metadataJson)

  if (!resolvedConfig || resolvedConfig.entity_type !== "user_repo") {
    return (
      <RepoCapabilityPlaceholderPanel
        title={title ?? "Git View"}
        description="Git view needs a resolvable user repo."
        unmetRequirements={[
          'metadata_json.repo_id or explicit config for entity_type "user_repo"',
        ]}
      />
    )
  }
  const repoQuery = useDemoUserRepo(resolvedConfig.entity_id)

  if (repoQuery.isLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading repository view...
      </div>
    )
  }

  if (repoQuery.isError || !repoQuery.data) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={title ?? "Git View"}
        description="Could not load the configured user repo."
        unmetRequirements={["user repo visibility"]}
      />
    )
  }

  const repo = repoQuery.data
  const capabilities = resolveDemoRepoCapabilities(repo)
  const displayMode =
    resolvedConfig.display_mode ??
    (resolvedConfig.show_file_content ? "split" : "explorer")
  const viewerPathMode =
    displayMode === "viewer"
      ? (resolvedConfig.path_mode ?? "selection")
      : "selection"
  const selectionKey =
    viewerPathMode === "readme"
      ? null
      : resolvedConfig.selection_key || `${surfaceId}.selection`

  if (displayMode === "explorer") {
    return (
      <RepoExplorerPanel
        repo={repo}
        panelId={`${surfaceId}:explorer`}
        config={{
          source: "user_repo",
          entity_type: "user_repo",
          entity_id_source: "repo_id",
          repo_id: repo.id,
          initial_path: resolvedConfig.initial_path,
          ref: resolvedConfig.ref,
          selection_key: selectionKey ?? `${surfaceId}.selection`,
          title: title ?? "Repo Explorer",
          show_sizes: resolvedConfig.show_sizes !== false,
          show_commit_badge: resolvedConfig.show_commit_badge !== false,
          empty_label: resolvedConfig.empty_label,
        }}
        enabled={capabilities.hasFileTree}
        selectedPath={
          selectionKey ? (repoSelections[selectionKey] ?? null) : null
        }
        onSelectPath={(path) =>
          setRepoSelection(selectionKey ?? `${surfaceId}.selection`, path)
        }
      />
    )
  }

  if (displayMode === "viewer") {
    return (
      <RepoFileViewerPanel
        repo={repo}
        panelId={`${surfaceId}:viewer`}
        config={{
          source: "user_repo",
          entity_type: "user_repo",
          entity_id_source: "repo_id",
          repo_id: repo.id,
          path_mode: viewerPathMode,
          fixed_path: resolvedConfig.fixed_path ?? "",
          ref: resolvedConfig.ref,
          selection_key: selectionKey,
          title: title ?? "File Viewer",
          show_path_badge: resolvedConfig.show_path_badge !== false,
          show_copy_control: resolvedConfig.show_copy_control !== false,
          empty_label: resolvedConfig.empty_label,
        }}
        enabled={capabilities.hasBlobContent}
        selectedPath={
          selectionKey ? (repoSelections[selectionKey] ?? null) : null
        }
        getRoomContextState={getRoomContextState}
        onToggleRoomContext={onToggleRoomContext}
      />
    )
  }

  const splitSelectionKey = selectionKey ?? `${surfaceId}.selection`

  return (
    <div className="grid h-full min-h-0 gap-3 lg:grid-cols-[minmax(0,0.85fr)_minmax(0,1.15fr)]">
      <div className="min-h-0">
        <RepoExplorerPanel
          repo={repo}
          panelId={`${surfaceId}:explorer`}
          config={{
            source: "user_repo",
            entity_type: "user_repo",
            entity_id_source: "repo_id",
            repo_id: repo.id,
            initial_path: resolvedConfig.initial_path,
            ref: resolvedConfig.ref,
            selection_key: splitSelectionKey,
            title: title ?? "Repo Explorer",
            show_sizes: resolvedConfig.show_sizes !== false,
            show_commit_badge: resolvedConfig.show_commit_badge !== false,
            empty_label: resolvedConfig.empty_label,
          }}
          enabled={capabilities.hasFileTree}
          selectedPath={repoSelections[splitSelectionKey] ?? null}
          onSelectPath={(path) => setRepoSelection(splitSelectionKey, path)}
        />
      </div>
      <div className="min-h-0">
        <RepoFileViewerPanel
          repo={repo}
          panelId={`${surfaceId}:viewer`}
          config={{
            source: "user_repo",
            entity_type: "user_repo",
            entity_id_source: "repo_id",
            repo_id: repo.id,
            path_mode: "selection",
            fixed_path: "",
            ref: resolvedConfig.ref,
            selection_key: splitSelectionKey,
            title: title ?? "Git View",
            show_path_badge: resolvedConfig.show_path_badge !== false,
            show_copy_control: resolvedConfig.show_copy_control !== false,
            empty_label: resolvedConfig.empty_label,
          }}
          enabled={capabilities.hasBlobContent}
          selectedPath={repoSelections[splitSelectionKey] ?? null}
          getRoomContextState={getRoomContextState}
          onToggleRoomContext={onToggleRoomContext}
        />
      </div>
    </div>
  )
}

function DemoRepoExplorerSurface({
  blockId,
  title,
  config,
  metadataJson,
  repoSelections,
  setRepoSelection,
}: {
  blockId: string
  title?: string | null
  config: unknown
  metadataJson: Record<string, unknown>
  repoSelections: Record<string, string | null>
  setRepoSelection: (selectionKey: string, path: string | null) => void
}) {
  const liveConfig = resolveLiveRepoExplorerConfig(
    config,
    metadataJson,
    `${blockId}.selection`,
  )

  if (!liveConfig) {
    return <FileExplorerBlock title={title} config={config} />
  }

  const repoQuery = useDemoUserRepo(liveConfig.entity_id)

  if (repoQuery.isLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading repository explorer...
      </div>
    )
  }

  if (repoQuery.isError || !repoQuery.data) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={title ?? liveConfig.title ?? "File Explorer"}
        description="Could not load the configured user repo."
        unmetRequirements={["user repo visibility"]}
      />
    )
  }

  const repo = repoQuery.data
  const capabilities = resolveDemoRepoCapabilities(repo)
  const selectionKey = liveConfig.selection_key || `${blockId}.selection`

  return (
    <RepoExplorerPanel
      repo={repo}
      panelId={`${blockId}:explorer`}
      config={{
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_source: "repo_id",
        repo_id: repo.id,
        initial_path: liveConfig.initial_path,
        ref: liveConfig.ref,
        selection_key: selectionKey,
        title: title ?? liveConfig.title ?? "File Explorer",
        show_sizes: liveConfig.show_sizes,
        show_commit_badge: liveConfig.show_commit_badge,
        empty_label: liveConfig.empty_label,
      }}
      enabled={capabilities.hasFileTree}
      selectedPath={repoSelections[selectionKey] ?? null}
      onSelectPath={(path) => setRepoSelection(selectionKey, path)}
    />
  )
}

function DemoRepoFileViewerSurface({
  surfaceId,
  title,
  config,
  metadataJson,
  repoSelections,
  getRoomContextState,
  onToggleRoomContext,
}: {
  surfaceId: string
  title?: string | null
  config: unknown
  metadataJson: Record<string, unknown>
  repoSelections: Record<string, string | null>
  getRoomContextState?: DemoBlockRendererContext["getFileRoomContextState"]
  onToggleRoomContext?: DemoBlockRendererContext["onToggleFileRoomContext"]
}) {
  const resolvedConfig = resolveLiveRepoFileViewerConfig(
    config,
    metadataJson,
    `${surfaceId}.selection`,
  )

  if (!resolvedConfig) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={title ?? "File Viewer"}
        description="File viewer needs a resolvable user repo."
        unmetRequirements={[
          'metadata_json.repo_id or explicit config for entity_type "user_repo"',
        ]}
      />
    )
  }

  const repoQuery = useDemoUserRepo(resolvedConfig.entity_id)

  if (repoQuery.isLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading repository file viewer...
      </div>
    )
  }

  if (repoQuery.isError || !repoQuery.data) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={title ?? resolvedConfig.title ?? "File Viewer"}
        description="Could not load the configured user repo."
        unmetRequirements={["user repo visibility"]}
      />
    )
  }

  const repo = repoQuery.data
  const capabilities = resolveDemoRepoCapabilities(repo)
  const selectionKey =
    resolvedConfig.path_mode === "readme"
      ? null
      : resolvedConfig.selection_key || `${surfaceId}.selection`

  return (
    <RepoFileViewerPanel
      repo={repo}
      panelId={`${surfaceId}:viewer`}
      config={{
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_source: "repo_id",
        repo_id: repo.id,
        path_mode: resolvedConfig.path_mode,
        fixed_path: resolvedConfig.fixed_path ?? "",
        ref: resolvedConfig.ref,
        selection_key: selectionKey,
        title: title ?? resolvedConfig.title ?? "File Viewer",
        show_path_badge: resolvedConfig.show_path_badge,
        show_copy_control: resolvedConfig.show_copy_control,
        empty_label: resolvedConfig.empty_label,
      }}
      enabled={capabilities.hasBlobContent}
      selectedPath={
        selectionKey ? (repoSelections[selectionKey] ?? null) : null
      }
      getRoomContextState={getRoomContextState}
      onToggleRoomContext={onToggleRoomContext}
    />
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
    <DemoRepoGitViewSurface
      surfaceId={`gitViewPanel:${panel.id}`}
      title={panel.title}
      metadataJson={ctx.metadataJson}
      config={(panel as { options?: unknown }).options}
      repoSelections={ctx.repoSelections}
      setRepoSelection={ctx.setRepoSelection}
      getRoomContextState={ctx.getFileRoomContextState}
      onToggleRoomContext={ctx.onToggleFileRoomContext}
    />
  ),
  fileExplorer: (panel, ctx) => (
    <DemoRepoExplorerSurface
      blockId={`fileExplorerPanel:${panel.id}`}
      title={panel.title}
      config={(panel as { options?: unknown }).options}
      metadataJson={ctx.metadataJson}
      repoSelections={ctx.repoSelections}
      setRepoSelection={ctx.setRepoSelection}
    />
  ),
  fileViewer: (panel, ctx) => (
    <DemoRepoFileViewerSurface
      surfaceId={`fileViewerPanel:${panel.id}`}
      title={panel.title}
      config={(panel as { options?: unknown }).options}
      metadataJson={ctx.metadataJson}
      repoSelections={ctx.repoSelections}
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
      onAddUser={ctx.onAddUser}
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
      roomId={ctx.roomId}
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
    <DemoRepoGitViewSurface
      surfaceId={`gitView:${block.id}`}
      title={block.title}
      config={resolveGitViewConfig(
        (block as { config_json?: unknown }).config_json,
        ctx.metadataJson,
      )}
      metadataJson={ctx.metadataJson}
      repoSelections={ctx.repoSelections}
      setRepoSelection={ctx.setRepoSelection}
      getRoomContextState={ctx.getFileRoomContextState}
      onToggleRoomContext={ctx.onToggleFileRoomContext}
    />
  ),
  fileExplorer: (block, ctx) => (
    <DemoRepoExplorerSurface
      blockId={block.id}
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      metadataJson={ctx.metadataJson}
      repoSelections={ctx.repoSelections}
      setRepoSelection={ctx.setRepoSelection}
    />
  ),
  fileViewer: (block, ctx) => (
    <DemoRepoFileViewerSurface
      surfaceId={`fileViewer:${block.id}`}
      title={block.title}
      config={(block as { config_json?: unknown }).config_json}
      metadataJson={ctx.metadataJson}
      repoSelections={ctx.repoSelections}
      getRoomContextState={ctx.getFileRoomContextState}
      onToggleRoomContext={ctx.onToggleFileRoomContext}
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
