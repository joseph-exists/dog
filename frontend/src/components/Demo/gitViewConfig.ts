export type GitViewEntityIdMode = "explicit" | "metadata"

export interface ShadowRepoGitViewConfig {
  source: "shadow_repo"
  entity_type: string
  entity_id_mode: GitViewEntityIdMode
  entity_id?: string
  entity_id_metadata_key?: string
  initial_path: string
  commit_limit: number
  show_file_content: boolean
  show_config_json: boolean
}

export interface ResolvedShadowRepoGitViewConfig extends ShadowRepoGitViewConfig {
  entity_id: string
}

export const GIT_VIEW_METADATA_KEY_PRESETS = [
  "story_id",
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
  return {
    source: "shadow_repo",
    entity_type: "story",
    entity_id_mode: "metadata",
    entity_id_metadata_key: "story_id",
    initial_path: "",
    commit_limit: 10,
    show_file_content: true,
    show_config_json: false,
  }
}

export function parseShadowRepoGitViewConfig(
  value: unknown,
): ShadowRepoGitViewConfig | null {
  const defaults = createDefaultShadowRepoGitViewConfig()
  if (!isObjectRecord(value)) return null
  if (value.source !== "shadow_repo") return null

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

  return {
    source: "shadow_repo",
    entity_type: entityType,
    entity_id_mode: entityIdMode,
    entity_id: entityId,
    entity_id_metadata_key: entityIdMetadataKey,
    initial_path:
      typeof value.initial_path === "string" ? value.initial_path.trim() : "",
    commit_limit: normalizeCommitLimit(value.commit_limit),
    show_file_content: value.show_file_content !== false,
    show_config_json: value.show_config_json === true,
  }
}

export function resolveShadowRepoGitViewConfig(
  value: unknown,
  metadataJson?: unknown,
): ResolvedShadowRepoGitViewConfig | null {
  const parsed = parseShadowRepoGitViewConfig(value)
  if (!parsed) return null

  const entityId =
    parsed.entity_id_mode === "explicit"
      ? parsed.entity_id?.trim() ?? ""
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
