import type { UserRepoPublic } from "@/client/types.gen"
import {
  getRepoCapabilityAvailability,
  getRepoPanelDefinition,
  type RepoPanelKind,
} from "@/components/Repo/registry"
import type { RepoPanelConfig } from "@/components/Repo/RepoLayout"
import { RepoExplorerPanel } from "./RepoExplorerPanel"
import { RepoFileViewerPanel } from "./RepoFileViewerPanel"
import { RepoImportStatusPanel } from "./RepoImportStatusPanel"
import { RepoOverviewPanel } from "./RepoOverviewPanel"
import { RepoCapabilityPlaceholderPanel } from "./RepoCapabilityPlaceholderPanel"
import {
  parseRepoExplorerPanelConfig,
  parseRepoFileViewerPanelConfig,
} from "./config"

export interface RepoPanelRendererContext {
  repo: UserRepoPublic
  capabilities: {
    hasRepoIdentity: boolean
    hasFileTree: boolean
    hasBlobContent: boolean
    hasCommitHistory: boolean
    hasSearch: boolean
    hasManageAccess: boolean
  }
  panelSelections: Record<string, string | null>
  setPanelSelection: (selectionKey: string, path: string | null) => void
  onFileOpened?: (payload: {
    panelId: string
    repoId: string
    path: string
    ref: string
  }) => void
  onRefObserved?: (payload: {
    panelId: string
    repoId: string
    ref: string
    path?: string | null
  }) => void
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
  }) => Promise<void> | void
}

export function renderRepoPanel(
  panel: Pick<RepoPanelConfig, "id" | "kind" | "config_json">,
  context: RepoPanelRendererContext,
) {
  const kind: RepoPanelKind = panel.kind
  const definition = getRepoPanelDefinition(kind)
  const availability = definition
    ? getRepoCapabilityAvailability(definition.requirements, context.capabilities)
    : { available: false, unmetRequirements: ["unknown panel kind"] }

  if (!availability.available || !definition) {
    return (
      <RepoCapabilityPlaceholderPanel
        title={definition?.label ?? kind}
        description={
          definition?.description ?? "This repository panel is not available."
        }
        unmetRequirements={availability.unmetRequirements}
      />
    )
  }

  switch (kind) {
    case "repoOverview":
      return <RepoOverviewPanel repo={context.repo} />
    case "repoImportStatus":
      return <RepoImportStatusPanel repo={context.repo} />
    case "repoExplorer": {
      const config = parseRepoExplorerPanelConfig(panel.config_json, panel.id)
      const selectionKey = config.selection_key || `${panel.id}.selection`
      return (
        <RepoExplorerPanel
          repo={context.repo}
          panelId={panel.id}
          config={config}
          enabled={availability.available}
          selectedPath={context.panelSelections[selectionKey] ?? null}
          onSelectPath={(path) => context.setPanelSelection(selectionKey, path)}
          onRefObserved={context.onRefObserved}
        />
      )
    }
    case "fileViewer": {
      const config = parseRepoFileViewerPanelConfig(panel.config_json, panel.id)
      const selectionKey =
        config.path_mode === "readme"
          ? null
          : config.selection_key || `${panel.id}.selection`
      return (
        <RepoFileViewerPanel
          repo={context.repo}
          panelId={panel.id}
          config={config}
          enabled={availability.available}
          selectedPath={selectionKey ? context.panelSelections[selectionKey] ?? null : null}
          onFileOpened={context.onFileOpened}
          onRefObserved={context.onRefObserved}
          getRoomContextState={context.getFileRoomContextState}
          onToggleRoomContext={context.onToggleFileRoomContext}
        />
      )
    }
    case "repoSearch":
    case "repoActivity":
    case "repoHistory":
      return (
        <RepoCapabilityPlaceholderPanel
          title={definition.label}
          description={definition.description}
          unmetRequirements={["panel implementation pending"]}
        />
      )
    default:
      return (
        <RepoCapabilityPlaceholderPanel
          title={kind}
          description="Unsupported repository panel."
          unmetRequirements={["unsupported kind"]}
        />
      )
  }
}
