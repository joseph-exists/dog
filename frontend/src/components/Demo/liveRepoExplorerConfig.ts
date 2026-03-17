import {
  GIT_VIEW_METADATA_KEY_PRESETS,
  type GitViewEntityIdMode,
} from "@/components/Demo/gitViewConfig"

export type LiveRepoExplorerSource = "user_repo" | "shadow_repo"

export interface LiveRepoExplorerConfig {
  source: LiveRepoExplorerSource
  entity_type: string
  entity_id_mode: GitViewEntityIdMode
  entity_id?: string
  entity_id_metadata_key?: string
  initial_path: string
  ref?: string | null
  selection_key?: string | null
  title?: string | null
  show_sizes: boolean
  show_commit_badge: boolean
  empty_label?: string | null
}

export interface ResolvedLiveRepoExplorerConfig extends LiveRepoExplorerConfig {
  entity_id: string
}

export const LIVE_REPO_EXPLORER_METADATA_KEY_PRESETS =
  GIT_VIEW_METADATA_KEY_PRESETS

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizeOptionalString(value: unknown): string | null {
  return typeof value === "string" && value.trim().length > 0 ? value.trim() : null
}

export function createDefaultLiveRepoExplorerConfig(
  selectionKey?: string | null,
): LiveRepoExplorerConfig {
  return {
    source: "user_repo",
    entity_type: "user_repo",
    entity_id_mode: "metadata",
    entity_id_metadata_key: "repo_id",
    initial_path: "",
    ref: null,
    selection_key: selectionKey ?? null,
    title: null,
    show_sizes: true,
    show_commit_badge: true,
    empty_label: null,
  }
}

export function isLiveRepoExplorerConfig(value: unknown): boolean {
  if (!isObjectRecord(value)) return false
  return (
    value.source === "user_repo" ||
    value.source === "shadow_repo" ||
    typeof value.entity_type === "string" ||
    value.entity_id_mode === "metadata" ||
    value.entity_id_mode === "explicit" ||
    typeof value.entity_id === "string" ||
    typeof value.entity_id_metadata_key === "string" ||
    typeof value.selection_key === "string" ||
    typeof value.ref === "string" ||
    typeof value.title === "string" ||
    typeof value.empty_label === "string" ||
    typeof value.show_sizes === "boolean" ||
    typeof value.show_commit_badge === "boolean"
  )
}

export function parseLiveRepoExplorerConfig(
  value: unknown,
  fallbackSelectionKey?: string,
): LiveRepoExplorerConfig | null {
  if (!isLiveRepoExplorerConfig(value)) return null

  const defaults = createDefaultLiveRepoExplorerConfig(fallbackSelectionKey)
  const record = value as Record<string, unknown>

  return {
    source:
      record.source === "shadow_repo" || record.source === "user_repo"
        ? record.source
        : defaults.source,
    entity_type:
      normalizeOptionalString(record.entity_type) ?? defaults.entity_type,
    entity_id_mode:
      record.entity_id_mode === "explicit" ? "explicit" : defaults.entity_id_mode,
    entity_id: normalizeOptionalString(record.entity_id) ?? undefined,
    entity_id_metadata_key:
      normalizeOptionalString(record.entity_id_metadata_key) ??
      defaults.entity_id_metadata_key,
    initial_path:
      typeof record.initial_path === "string" ? record.initial_path.trim() : "",
    ref: normalizeOptionalString(record.ref),
    selection_key:
      normalizeOptionalString(record.selection_key) ?? defaults.selection_key,
    title: normalizeOptionalString(record.title),
    show_sizes: record.show_sizes !== false,
    show_commit_badge: record.show_commit_badge !== false,
    empty_label: normalizeOptionalString(record.empty_label),
  }
}

export function resolveLiveRepoExplorerConfig(
  value: unknown,
  metadataJson: unknown,
  fallbackSelectionKey: string,
): ResolvedLiveRepoExplorerConfig | null {
  const parsed = parseLiveRepoExplorerConfig(value, fallbackSelectionKey)
  if (!parsed) return null

  const entityId =
    parsed.entity_id_mode === "explicit"
      ? parsed.entity_id?.trim() ?? ""
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
