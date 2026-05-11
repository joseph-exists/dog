import type { UserRepoPublic } from "@/client/types.gen"
import type { RepoPanelKind } from "@/components/Repo/registry"

export type RepoPanelDataSource = "user_repo" | "shadow_repo"
export type RepoPanelEntityIdSource = "repo_id" | "current_room"
export type RepoFileViewerPathMode = "selection" | "fixed" | "readme"

export interface RepoExplorerPanelConfig {
  source: RepoPanelDataSource
  entity_type: string
  entity_id_source: RepoPanelEntityIdSource
  repo_id?: string | null
  initial_path: string
  ref?: string | null
  selection_key?: string | null
  title?: string | null
  show_sizes: boolean
  show_commit_badge: boolean
  empty_label?: string | null
}

export interface RepoFileViewerPanelConfig {
  source: RepoPanelDataSource
  entity_type: string
  entity_id_source: RepoPanelEntityIdSource
  repo_id?: string | null
  path_mode: RepoFileViewerPathMode
  fixed_path?: string
  ref?: string | null
  selection_key?: string | null
  title?: string | null
  show_path_badge: boolean
  show_copy_control: boolean
  empty_label?: string | null
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizeOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null
}

function normalizeString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value.trim() : fallback
}

export function createDefaultRepoExplorerPanelConfig(
  panelId: string,
): RepoExplorerPanelConfig {
  return {
    source: "user_repo",
    entity_type: "user_repo",
    entity_id_source: "repo_id",
    repo_id: null,
    initial_path: "",
    ref: null,
    selection_key: `${panelId}.selection`,
    title: null,
    show_sizes: true,
    show_commit_badge: true,
    empty_label: null,
  }
}

export function createDefaultRepoFileViewerPanelConfig(
  panelId: string,
): RepoFileViewerPanelConfig {
  return {
    source: "user_repo",
    entity_type: "user_repo",
    entity_id_source: "repo_id",
    repo_id: null,
    path_mode: "selection",
    fixed_path: "",
    ref: null,
    selection_key: `${panelId}.selection`,
    title: null,
    show_path_badge: true,
    show_copy_control: true,
    empty_label: null,
  }
}

export function createDefaultRepoPanelConfig(
  kind: RepoPanelKind,
  panelId: string,
): RepoExplorerPanelConfig | RepoFileViewerPanelConfig | null {
  if (kind === "repoExplorer") {
    return createDefaultRepoExplorerPanelConfig(panelId)
  }
  if (kind === "fileViewer") {
    return createDefaultRepoFileViewerPanelConfig(panelId)
  }
  return null
}

export function parseRepoExplorerPanelConfig(
  value: unknown,
  panelId: string,
): RepoExplorerPanelConfig {
  const defaults = createDefaultRepoExplorerPanelConfig(panelId)
  if (!isObjectRecord(value)) return defaults

  return {
    source:
      value.source === "shadow_repo" || value.repo_model === "shadow_repo"
        ? "shadow_repo"
        : "user_repo",
    entity_type:
      normalizeOptionalString(value.entity_type) ?? defaults.entity_type,
    entity_id_source:
      value.entity_id_source === "current_room"
        ? "current_room"
        : defaults.entity_id_source,
    repo_id: normalizeOptionalString(value.repo_id),
    initial_path: normalizeString(value.initial_path),
    ref: normalizeOptionalString(value.ref),
    selection_key:
      normalizeOptionalString(value.selection_key) ?? defaults.selection_key,
    title: normalizeOptionalString(value.title),
    show_sizes: value.show_sizes !== false,
    show_commit_badge: value.show_commit_badge !== false,
    empty_label: normalizeOptionalString(value.empty_label),
  }
}

export function parseRepoFileViewerPanelConfig(
  value: unknown,
  panelId: string,
): RepoFileViewerPanelConfig {
  const defaults = createDefaultRepoFileViewerPanelConfig(panelId)
  if (!isObjectRecord(value)) return defaults

  return {
    source:
      value.source === "shadow_repo" || value.repo_model === "shadow_repo"
        ? "shadow_repo"
        : "user_repo",
    entity_type:
      normalizeOptionalString(value.entity_type) ?? defaults.entity_type,
    entity_id_source:
      value.entity_id_source === "current_room"
        ? "current_room"
        : defaults.entity_id_source,
    repo_id: normalizeOptionalString(value.repo_id),
    path_mode:
      value.path_mode === "fixed"
        ? "fixed"
        : value.path_mode === "readme"
          ? "readme"
          : defaults.path_mode,
    fixed_path: normalizeString(value.fixed_path),
    ref: normalizeOptionalString(value.ref),
    selection_key:
      normalizeOptionalString(value.selection_key) ??
      (value.path_mode === "readme" ? null : defaults.selection_key),
    title: normalizeOptionalString(value.title),
    show_path_badge: value.show_path_badge !== false,
    show_copy_control: value.show_copy_control !== false,
    empty_label: normalizeOptionalString(value.empty_label),
  }
}

export function normalizeRepoPanelConfig(
  kind: RepoPanelKind,
  panelId: string,
  value: unknown,
): Record<string, unknown> | null {
  if (kind === "repoExplorer") {
    return parseRepoExplorerPanelConfig(value, panelId) as unknown as Record<
      string,
      unknown
    >
  }
  if (kind === "fileViewer") {
    const parsed = parseRepoFileViewerPanelConfig(value, panelId)
    if (parsed.path_mode === "readme") {
      return {
        ...parsed,
        selection_key: null,
      } as unknown as Record<string, unknown>
    }
    return parsed as unknown as Record<string, unknown>
  }
  return isObjectRecord(value) ? value : null
}

export function cloneRepoPanelConfigForPanelId(
  kind: RepoPanelKind,
  sourcePanelId: string,
  nextPanelId: string,
  value: unknown,
): Record<string, unknown> | null {
  const normalized = normalizeRepoPanelConfig(kind, sourcePanelId, value)
  if (!normalized) {
    return createDefaultRepoPanelConfig(kind, nextPanelId) as unknown as Record<
      string,
      unknown
    > | null
  }

  if (kind === "repoExplorer") {
    const parsed = parseRepoExplorerPanelConfig(normalized, sourcePanelId)
    return {
      ...parsed,
      selection_key:
        parsed.selection_key === `${sourcePanelId}.selection`
          ? `${nextPanelId}.selection`
          : parsed.selection_key,
    } as unknown as Record<string, unknown>
  }

  if (kind === "fileViewer") {
    const parsed = parseRepoFileViewerPanelConfig(normalized, sourcePanelId)
    return {
      ...parsed,
      selection_key:
        parsed.selection_key === `${sourcePanelId}.selection`
          ? `${nextPanelId}.selection`
          : parsed.selection_key,
    } as unknown as Record<string, unknown>
  }

  return normalized
}

export function resolveRepoPanelEntityId(
  repo: UserRepoPublic,
  entityIdSource: RepoPanelEntityIdSource,
) {
  return entityIdSource === "repo_id" ? repo.id : repo.id
}
