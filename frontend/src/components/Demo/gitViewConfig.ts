export type GitViewEntityIdMode = "explicit" | "metadata"
export type GitViewSource = "user_repo" | "shadow_repo"
export type GitViewDisplayMode = "split" | "explorer" | "viewer"
export type GitViewPathMode = "selection" | "fixed" | "readme"

export interface GitViewConfig {
  source: GitViewSource
  entity_type: string
  entity_id_mode: GitViewEntityIdMode
  entity_id?: string
  entity_id_metadata_key?: string
  selection_key?: string
  initial_path: string
  display_mode?: GitViewDisplayMode
  path_mode?: GitViewPathMode
  fixed_path?: string
  ref?: string | null
  commit_limit: number
  show_file_content: boolean
  show_config_json: boolean
  show_path_badge?: boolean
  show_copy_control?: boolean
  show_sizes?: boolean
  show_commit_badge?: boolean
  empty_label?: string | null
}

export interface ResolvedGitViewConfig extends GitViewConfig {
  entity_id: string
}

export const GIT_VIEW_METADATA_KEY_PRESETS = [
  "story_id",
  "repo_id",
  "agent_id",
  "persona_id",
  "room_id",
  "demo_config_id",
] as const

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizeCommitLimit(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value) && value > 0) {
    return Math.floor(value)
  }
  return 10
}

export function createDefaultShadowRepoGitViewConfig(): ShadowRepoGitViewConfig {
  return createDefaultGitViewConfig()
}

export function createDefaultGitViewConfig(): GitViewConfig {
  return {
    source: "user_repo",
    entity_type: "user_repo",
    entity_id_mode: "metadata",
    entity_id_metadata_key: "repo_id",
    selection_key: undefined,
    initial_path: "",
    display_mode: "split",
    path_mode: "selection",
    fixed_path: "",
    ref: null,
    commit_limit: 10,
    show_file_content: true,
    show_config_json: false,
    show_path_badge: true,
    show_copy_control: true,
    show_sizes: true,
    show_commit_badge: true,
    empty_label: null,
  }
}

export function parseShadowRepoGitViewConfig(
  value: unknown,
): ShadowRepoGitViewConfig | null {
  return parseGitViewConfig(value)
}

export function parseGitViewConfig(value: unknown): GitViewConfig | null {
  const defaults = createDefaultGitViewConfig()
  if (!isObjectRecord(value)) return null
  const rawSource = value.source
  const source =
    rawSource === "shadow_repo" || rawSource === "user_repo"
      ? rawSource
      : defaults.source

  const entityType =
    typeof value.entity_type === "string" && value.entity_type.trim().length > 0
      ? value.entity_type.trim()
      : defaults.entity_type
  const entityIdMode =
    value.entity_id_mode === "explicit" ? "explicit" : defaults.entity_id_mode
  const entityId =
    typeof value.entity_id === "string" && value.entity_id.trim().length > 0
      ? value.entity_id.trim()
      : undefined
  const entityIdMetadataKey =
    typeof value.entity_id_metadata_key === "string" &&
    value.entity_id_metadata_key.trim().length > 0
      ? value.entity_id_metadata_key.trim()
      : defaults.entity_id_metadata_key
  const selectionKey =
    typeof value.selection_key === "string" &&
    value.selection_key.trim().length > 0
      ? value.selection_key.trim()
      : defaults.selection_key
  const displayMode =
    value.display_mode === "explorer" || value.display_mode === "viewer"
      ? value.display_mode
      : defaults.display_mode
  const pathMode =
    value.path_mode === "fixed" || value.path_mode === "readme"
      ? value.path_mode
      : defaults.path_mode

  return {
    source,
    entity_type: entityType,
    entity_id_mode: entityIdMode,
    entity_id: entityId,
    entity_id_metadata_key: entityIdMetadataKey,
    selection_key: selectionKey,
    initial_path:
      typeof value.initial_path === "string" ? value.initial_path.trim() : "",
    display_mode: displayMode,
    path_mode: pathMode,
    fixed_path:
      typeof value.fixed_path === "string"
        ? value.fixed_path.trim()
        : defaults.fixed_path,
    ref:
      typeof value.ref === "string" && value.ref.trim().length > 0
        ? value.ref.trim()
        : defaults.ref,
    commit_limit: normalizeCommitLimit(value.commit_limit),
    show_file_content: value.show_file_content !== false,
    show_config_json: value.show_config_json === true,
    show_path_badge: value.show_path_badge !== false,
    show_copy_control: value.show_copy_control !== false,
    show_sizes: value.show_sizes !== false,
    show_commit_badge: value.show_commit_badge !== false,
    empty_label:
      typeof value.empty_label === "string" &&
      value.empty_label.trim().length > 0
        ? value.empty_label.trim()
        : defaults.empty_label,
  }
}

export function resolveShadowRepoGitViewConfig(
  value: unknown,
  metadataJson?: unknown,
): ResolvedShadowRepoGitViewConfig | null {
  return resolveGitViewConfig(value, metadataJson)
}

export function resolveGitViewConfig(
  value: unknown,
  metadataJson?: unknown,
): ResolvedGitViewConfig | null {
  const parsed = parseGitViewConfig(value)
  if (!parsed) return null

  const entityId =
    parsed.entity_id_mode === "explicit"
      ? (parsed.entity_id?.trim() ?? "")
      : (() => {
          if (!isObjectRecord(metadataJson)) return ""
          const candidate = metadataJson[parsed.entity_id_metadata_key ?? ""]
          return typeof candidate === "string" ? candidate.trim() : ""
        })()

  if (!parsed.entity_type.trim() || !entityId) return null

  return {
    ...parsed,
    entity_id: entityId,
  }
}

// Backward-compatible aliases for legacy call sites/config names.
export type ShadowRepoGitViewConfig = GitViewConfig
export type ResolvedShadowRepoGitViewConfig = ResolvedGitViewConfig
