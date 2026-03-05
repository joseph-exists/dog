import type {
  RepoBlockType,
  RepoPanelKind,
  RepoPanelProminence,
} from "@/components/Repo/registry"
import { getDefaultRepoPanelConfigs } from "@/components/Repo/registry"

export type RepoBuilderFieldControl =
  | "text"
  | "number"
  | "boolean"
  | "enum"
  | "json"
  | "id"

export type RepoBuilderBlockRegion = "top" | "primary" | "auxiliary" | "footer"
export type RepoBuilderBlockVisibility =
  | "visible"
  | "hidden_unmounted"
  | "hidden_mounted"

export interface RepoBuilderFieldSpec {
  key: string
  label: string
  control: RepoBuilderFieldControl
  required?: boolean
  enumValues?: readonly string[]
  category?: "core" | "theme" | "advanced"
}

export interface RepoBuilderPanelFieldSpec extends RepoBuilderFieldSpec {
  scope: "panel"
}

export interface RepoBuilderBlockFieldSpec extends RepoBuilderFieldSpec {
  scope: "block"
}

export interface RepoBuilderPanelConfig {
  id: string
  kind: RepoPanelKind
  title?: string
  order?: number
  prominence: RepoPanelProminence
  default_size?: number
  min_size?: number
  max_size?: number
  config_json?: Record<string, unknown> | null
}

export interface RepoBuilderBlockConfig {
  id: string
  type: RepoBlockType
  title?: string
  order?: number
  region: RepoBuilderBlockRegion
  visibility: RepoBuilderBlockVisibility
  config_json?: Record<string, unknown> | null
  content_json?: Record<string, unknown> | null
}

export interface RepoBuilderComposition {
  layout_mode: "panels" | "tabs"
  panels: RepoBuilderPanelConfig[]
  blocks: RepoBuilderBlockConfig[]
  metadata_json?: Record<string, unknown> | null
}

export const ACTIVE_REPO_BUILDER_PANEL_KINDS = [
  "repoOverview",
  "repoImportStatus",
  "repoExplorer",
  "fileViewer",
  "repoActivity",
  "repoSearch",
] as const satisfies readonly RepoPanelKind[]

export const ACTIVE_REPO_BUILDER_BLOCK_TYPES = [
  "repoMetadata",
  "repoImportSummary",
  "repoImportRecord",
  "repoFailureDiagnostics",
  "repoReadme",
] as const satisfies readonly RepoBlockType[]

export type ActiveRepoBuilderPanelKind =
  (typeof ACTIVE_REPO_BUILDER_PANEL_KINDS)[number]
export type ActiveRepoBuilderBlockType =
  (typeof ACTIVE_REPO_BUILDER_BLOCK_TYPES)[number]

export const REPO_BUILDER_BLOCK_REGIONS: RepoBuilderBlockRegion[] = [
  "top",
  "primary",
  "auxiliary",
  "footer",
]

export const REPO_BUILDER_BLOCK_VISIBILITY: RepoBuilderBlockVisibility[] = [
  "visible",
  "hidden_unmounted",
  "hidden_mounted",
]

export const REPO_BUILDER_PANEL_FIELD_SPECS: RepoBuilderPanelFieldSpec[] = [
  {
    scope: "panel",
    key: "kind",
    label: "Kind",
    control: "enum",
    enumValues: ACTIVE_REPO_BUILDER_PANEL_KINDS,
    required: true,
    category: "core",
  },
  {
    scope: "panel",
    key: "id",
    label: "ID",
    control: "id",
    required: true,
    category: "core",
  },
  { scope: "panel", key: "title", label: "Title", control: "text", category: "core" },
  { scope: "panel", key: "order", label: "Order", control: "number", category: "core" },
  {
    scope: "panel",
    key: "prominence",
    label: "Prominence",
    control: "enum",
    enumValues: ["primary", "auxiliary"],
    category: "core",
  },
  {
    scope: "panel",
    key: "default_size",
    label: "Default Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "min_size",
    label: "Min Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "max_size",
    label: "Max Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "config_json",
    label: "Config JSON",
    control: "json",
    category: "advanced",
  },
]

export const REPO_BUILDER_BLOCK_FIELD_SPECS: RepoBuilderBlockFieldSpec[] = [
  {
    scope: "block",
    key: "type",
    label: "Type",
    control: "enum",
    enumValues: ACTIVE_REPO_BUILDER_BLOCK_TYPES,
    required: true,
    category: "core",
  },
  {
    scope: "block",
    key: "id",
    label: "ID",
    control: "id",
    required: true,
    category: "core",
  },
  { scope: "block", key: "title", label: "Title", control: "text", category: "core" },
  { scope: "block", key: "order", label: "Order", control: "number", category: "core" },
  {
    scope: "block",
    key: "region",
    label: "Region",
    control: "enum",
    enumValues: REPO_BUILDER_BLOCK_REGIONS,
    category: "core",
  },
  {
    scope: "block",
    key: "visibility",
    label: "Visibility",
    control: "enum",
    enumValues: REPO_BUILDER_BLOCK_VISIBILITY,
    category: "core",
  },
  {
    scope: "block",
    key: "config_json",
    label: "Config JSON",
    control: "json",
    category: "advanced",
  },
  {
    scope: "block",
    key: "content_json",
    label: "Content JSON",
    control: "json",
    category: "advanced",
  },
]

export function createDefaultRepoBuilderComposition(): RepoBuilderComposition {
  return {
    layout_mode: "panels",
    panels: getDefaultRepoPanelConfigs().map((panel) => ({
      id: panel.id,
      kind: panel.kind,
      title: panel.title,
      prominence: panel.prominence,
      default_size: panel.default_size,
      min_size: panel.min_size,
      max_size: panel.max_size,
      config_json: panel.config_json,
    })),
    blocks: [
      {
        id: "repoMetadata",
        type: "repoMetadata",
        title: "Repository Metadata",
        region: "primary",
        visibility: "visible",
      },
      {
        id: "repoImportSummary",
        type: "repoImportSummary",
        title: "Import Summary",
        region: "primary",
        visibility: "visible",
      },
      {
        id: "repoImportRecord",
        type: "repoImportRecord",
        title: "Import Record",
        region: "auxiliary",
        visibility: "visible",
      },
    ],
    metadata_json: null,
  }
}
