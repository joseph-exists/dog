import {
  GIT_VIEW_METADATA_KEY_PRESETS,
  type GitViewEntityIdMode,
} from "@/components/Demo/gitViewConfig"

export type LiveRepoFileViewerSource = "user_repo" | "shadow_repo"
export type LiveRepoFileViewerPathMode = "selection" | "fixed" | "readme"

export interface LiveRepoFileViewerConfig {
  source: LiveRepoFileViewerSource
  entity_type: string
  entity_id_mode: GitViewEntityIdMode
  entity_id?: string
  entity_id_metadata_key?: string
  path_mode: LiveRepoFileViewerPathMode
  fixed_path?: string
  ref?: string | null
  selection_key?: string | null
  title?: string | null
  show_path_badge: boolean
  show_copy_control: boolean
  empty_label?: string | null
}

export interface ResolvedLiveRepoFileViewerConfig
  extends LiveRepoFileViewerConfig {
  entity_id: string
}

export const LIVE_REPO_FILE_VIEWER_METADATA_KEY_PRESETS =
  GIT_VIEW_METADATA_KEY_PRESETS

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizeOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0
    ? value.trim()
    : null
}

export function createDefaultLiveRepoFileViewerConfig(
  selectionKey?: string | null,
): LiveRepoFileViewerConfig {
  return {
    source: "user_repo",
    entity_type: "user_repo",
    entity_id_mode: "metadata",
    entity_id_metadata_key: "repo_id",
    path_mode: "selection",
    fixed_path: "",
    ref: null,
    selection_key: selectionKey ?? null,
    title: null,
    show_path_badge: true,
    show_copy_control: true,
    empty_label: null,
  }
}

export function isLiveRepoFileViewerConfig(value: unknown): boolean {
  if (!isObjectRecord(value)) return false
  return (
    value.source === "user_repo" ||
    value.source === "shadow_repo" ||
    typeof value.entity_type === "string" ||
    value.entity_id_mode === "metadata" ||
    value.entity_id_mode === "explicit" ||
    typeof value.entity_id === "string" ||
    typeof value.entity_id_metadata_key === "string" ||
    value.path_mode === "selection" ||
    value.path_mode === "fixed" ||
    value.path_mode === "readme" ||
    typeof value.fixed_path === "string" ||
    typeof value.selection_key === "string" ||
    typeof value.ref === "string" ||
    typeof value.title === "string" ||
    typeof value.empty_label === "string" ||
    typeof value.show_path_badge === "boolean" ||
    typeof value.show_copy_control === "boolean"
  )
}

export function parseLiveRepoFileViewerConfig(
  value: unknown,
  fallbackSelectionKey?: string,
): LiveRepoFileViewerConfig | null {
  if (!isLiveRepoFileViewerConfig(value)) return null

  const defaults = createDefaultLiveRepoFileViewerConfig(fallbackSelectionKey)
  const record = value as Record<string, unknown>
  const pathMode =
    record.path_mode === "fixed"
      ? "fixed"
      : record.path_mode === "readme"
        ? "readme"
        : defaults.path_mode

  return {
    source:
      record.source === "shadow_repo" || record.source === "user_repo"
        ? record.source
        : defaults.source,
    entity_type:
      normalizeOptionalString(record.entity_type) ?? defaults.entity_type,
    entity_id_mode:
      record.entity_id_mode === "explicit"
        ? "explicit"
        : defaults.entity_id_mode,
    entity_id: normalizeOptionalString(record.entity_id) ?? undefined,
    entity_id_metadata_key:
      normalizeOptionalString(record.entity_id_metadata_key) ??
      defaults.entity_id_metadata_key,
    path_mode: pathMode,
    fixed_path:
      typeof record.fixed_path === "string"
        ? record.fixed_path.trim()
        : defaults.fixed_path,
    ref: normalizeOptionalString(record.ref),
    selection_key:
      pathMode === "readme"
        ? null
        : (normalizeOptionalString(record.selection_key) ??
          defaults.selection_key),
    title: normalizeOptionalString(record.title),
    show_path_badge: record.show_path_badge !== false,
    show_copy_control: record.show_copy_control !== false,
    empty_label: normalizeOptionalString(record.empty_label),
  }
}

export function resolveLiveRepoFileViewerConfig(
  value: unknown,
  metadataJson: unknown,
  fallbackSelectionKey: string,
): ResolvedLiveRepoFileViewerConfig | null {
  const parsed = parseLiveRepoFileViewerConfig(value, fallbackSelectionKey)
  if (!parsed) return null

  const entityId =
    parsed.entity_id_mode === "explicit"
      ? (parsed.entity_id?.trim() ?? "")
      : (() => {
          if (!isObjectRecord(metadataJson)) return ""
          const candidate = metadataJson[parsed.entity_id_metadata_key ?? ""]
          return typeof candidate === "string" ? candidate.trim() : ""
        })()

  if (!entityId || parsed.entity_type !== "user_repo") return null

  return {
    ...parsed,
    entity_id: entityId,
  }
}
