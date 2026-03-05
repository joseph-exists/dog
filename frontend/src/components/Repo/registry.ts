import {
  Activity,
  CircleAlert,
  FileSearch,
  FileText,
  FolderTree,
  Info,
  type LucideIcon,
  Search,
} from "lucide-react"
import {
  createDefaultRepoExplorerPanelConfig,
  createDefaultRepoFileViewerPanelConfig,
} from "@/components/Repo/panels/config"

export type RepoPanelProminence = "primary" | "auxiliary"

export type RepoPanelKind =
  | "repoOverview"
  | "repoExplorer"
  | "fileViewer"
  | "repoImportStatus"
  | "repoSearch"
  | "repoActivity"
  | "repoHistory"

export type RepoBlockType =
  | "repoReadme"
  | "repoMetadata"
  | "repoImportSummary"
  | "repoImportRecord"
  | "repoFileStats"
  | "repoRecentFiles"
  | "repoFailureDiagnostics"
  | "repoCommitSummary"

export interface RepoCapabilityRequirements {
  requiresRepoIdentity: boolean
  requiresFileTree: boolean
  requiresBlobContent: boolean
  requiresCommitHistory: boolean
  requiresSearch: boolean
  requiresManageAccess: boolean
}

export interface RepoCapabilityAvailabilityInput {
  hasRepoIdentity?: boolean
  hasFileTree?: boolean
  hasBlobContent?: boolean
  hasCommitHistory?: boolean
  hasSearch?: boolean
  hasManageAccess?: boolean
}

export interface RepoCapabilityAvailability {
  available: boolean
  unmetRequirements: string[]
}

interface RepoSurfaceDefinitionBase {
  label: string
  description: string
  icon: LucideIcon
  requirements: RepoCapabilityRequirements
}

export interface RepoPanelDefinition extends RepoSurfaceDefinitionBase {
  kind: RepoPanelKind
  defaultProminence: RepoPanelProminence
}

export interface RepoBlockDefinition extends RepoSurfaceDefinitionBase {
  type: RepoBlockType
}

export interface DefaultRepoPanelConfig {
  id: string
  kind: RepoPanelKind
  title: string
  prominence: RepoPanelProminence
  default_size?: number
  min_size?: number
  max_size?: number
  config_json?: Record<string, unknown> | null
}

const baseRequirements: RepoCapabilityRequirements = {
  requiresRepoIdentity: true,
  requiresFileTree: false,
  requiresBlobContent: false,
  requiresCommitHistory: false,
  requiresSearch: false,
  requiresManageAccess: false,
}

export const REPO_PANEL_DEFINITIONS: RepoPanelDefinition[] = [
  {
    kind: "repoOverview",
    label: "Overview",
    description: "Summary view for platform-owned repo identity and import state.",
    icon: Info,
    defaultProminence: "primary",
    requirements: { ...baseRequirements },
  },
  {
    kind: "repoExplorer",
    label: "Explorer",
    description: "Tree browser for repository folders and files.",
    icon: FolderTree,
    defaultProminence: "primary",
    requirements: { ...baseRequirements, requiresFileTree: true },
  },
  {
    kind: "fileViewer",
    label: "File Viewer",
    description: "Blob/content viewer rendered through shared content primitives.",
    icon: FileText,
    defaultProminence: "primary",
    requirements: {
      ...baseRequirements,
      requiresFileTree: true,
      requiresBlobContent: true,
    },
  },
  {
    kind: "repoImportStatus",
    label: "Import Status",
    description: "Operational state for backend-managed repository imports.",
    icon: CircleAlert,
    defaultProminence: "auxiliary",
    requirements: { ...baseRequirements },
  },
  {
    kind: "repoSearch",
    label: "Search",
    description: "Repository-level search and indexing results.",
    icon: Search,
    defaultProminence: "auxiliary",
    requirements: { ...baseRequirements, requiresSearch: true },
  },
  {
    kind: "repoActivity",
    label: "Activity",
    description: "Operational and repository events relevant to the workspace.",
    icon: Activity,
    defaultProminence: "auxiliary",
    requirements: { ...baseRequirements },
  },
  {
    kind: "repoHistory",
    label: "History",
    description: "Commit- and change-history focused repository view.",
    icon: FileSearch,
    defaultProminence: "auxiliary",
    requirements: { ...baseRequirements, requiresCommitHistory: true },
  },
]

export const REPO_BLOCK_DEFINITIONS: RepoBlockDefinition[] = [
  {
    type: "repoReadme",
    label: "README",
    description: "Rendered markdown entry point for the repository.",
    icon: FileText,
    requirements: { ...baseRequirements, requiresBlobContent: true },
  },
  {
    type: "repoMetadata",
    label: "Repo Metadata",
    description: "Name, slug, visibility, and managed repo identifiers.",
    icon: Info,
    requirements: { ...baseRequirements },
  },
  {
    type: "repoImportSummary",
    label: "Import Summary",
    description: "High-level state for the one-time platform intake process.",
    icon: CircleAlert,
    requirements: { ...baseRequirements },
  },
  {
    type: "repoImportRecord",
    label: "Import Record",
    description: "Original intake request metadata retained for audit and reference.",
    icon: Info,
    requirements: { ...baseRequirements },
  },
  {
    type: "repoFileStats",
    label: "File Stats",
    description: "Counts and file-shape summaries derived from tree metadata.",
    icon: FolderTree,
    requirements: { ...baseRequirements, requiresFileTree: true },
  },
  {
    type: "repoRecentFiles",
    label: "Recent Files",
    description: "Curated or recent file references for navigation.",
    icon: FolderTree,
    requirements: { ...baseRequirements, requiresFileTree: true },
  },
  {
    type: "repoFailureDiagnostics",
    label: "Failure Diagnostics",
    description: "Inspectable permanent import failure details.",
    icon: CircleAlert,
    requirements: { ...baseRequirements },
  },
  {
    type: "repoCommitSummary",
    label: "Commit Summary",
    description: "Recent commit summary for repo review surfaces.",
    icon: Activity,
    requirements: { ...baseRequirements, requiresCommitHistory: true },
  },
]

export function getRepoPanelDefinition(kind: RepoPanelKind) {
  return REPO_PANEL_DEFINITIONS.find((panel) => panel.kind === kind)
}

export function getRepoBlockDefinition(type: RepoBlockType) {
  return REPO_BLOCK_DEFINITIONS.find((block) => block.type === type)
}

function resolveRequirementLabel(requirement: keyof RepoCapabilityRequirements) {
  return (
    {
      requiresRepoIdentity: "repo identity",
      requiresFileTree: "file tree endpoint",
      requiresBlobContent: "blob/content endpoint",
      requiresCommitHistory: "commit/history endpoint",
      requiresSearch: "search/indexing endpoint",
      requiresManageAccess: "manage access",
    }[requirement] ?? requirement
  )
}

export function getRepoCapabilityAvailability(
  requirements: RepoCapabilityRequirements,
  input: RepoCapabilityAvailabilityInput,
): RepoCapabilityAvailability {
  const unmetRequirements = (Object.entries(requirements) as Array<
    [keyof RepoCapabilityRequirements, boolean]
  >)
    .filter(([key, required]) => {
      if (!required) return false
      const capabilityKey = key.replace("requires", "has")
      return input[capabilityKey as keyof RepoCapabilityAvailabilityInput] !== true
    })
    .map(([key]) => resolveRequirementLabel(key))

  return {
    available: unmetRequirements.length === 0,
    unmetRequirements,
  }
}

export function getDefaultRepoPanelConfigs(): DefaultRepoPanelConfig[] {
  const sharedSelectionKey = "workspace.primary-file"
  const readmeConfig = createDefaultRepoFileViewerPanelConfig("repoReadmeViewer")
  const explorerConfig = createDefaultRepoExplorerPanelConfig("repoExplorer")
  const fileViewerConfig = createDefaultRepoFileViewerPanelConfig("fileViewer")

  return [
    {
      id: "repoOverview",
      kind: "repoOverview",
      prominence: "primary",
      title: "Overview",
      default_size: 36,
      min_size: 18,
      config_json: null,
    },
    {
      id: "repoReadmeViewer",
      kind: "fileViewer",
      prominence: "auxiliary",
      title: "README",
      default_size: 38,
      min_size: 18,
      config_json: {
        ...readmeConfig,
        path_mode: "readme",
        selection_key: null,
        empty_label: "No README is available for this repository.",
      },
    },
    {
      id: "repoExplorer",
      kind: "repoExplorer",
      prominence: "auxiliary",
      title: "Explorer",
      default_size: 38,
      min_size: 15,
      config_json: {
        ...explorerConfig,
        selection_key: sharedSelectionKey,
      },
    },
    {
      id: "fileViewer",
      kind: "fileViewer",
      prominence: "primary",
      title: "File Viewer",
      default_size: 68,
      min_size: 20,
      config_json: {
        ...fileViewerConfig,
        selection_key: sharedSelectionKey,
      },
    },
    {
      id: "repoImportStatus",
      kind: "repoImportStatus",
      prominence: "auxiliary",
      title: "Import Status",
      default_size: 24,
      min_size: 18,
      config_json: null,
    },
  ]
}
