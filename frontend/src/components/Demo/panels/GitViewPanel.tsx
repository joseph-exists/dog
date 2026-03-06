import {
  createDefaultShadowRepoGitViewConfig,
  resolveShadowRepoGitViewConfig,
} from "@/components/Demo/gitViewConfig"
import {
  GitViewCore,
  GitViewInvalidConfig,
  type GetGitViewRoomContextState,
  type ToggleGitViewRoomContext,
} from "@/components/Demo/gitView/GitViewCore"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function resolvePanelGitViewConfig(options: unknown): unknown {
  if (!isObjectRecord(options)) return null
  const nested = options.git_view_config
  if (isObjectRecord(nested)) return nested
  return options.source === "shadow_repo" ? options : null
}

interface GitViewPanelProps {
  panelId: string
  title?: string | null
  selectionKey?: string
  options?: unknown
  metadataJson?: unknown
  onSelectFileForDebug?: (selectionKey: string, path: string | null) => void
  getRoomContextState?: GetGitViewRoomContextState
  onToggleRoomContext?: ToggleGitViewRoomContext
}

export function GitViewPanel({
  panelId,
  title,
  selectionKey,
  options,
  metadataJson,
  onSelectFileForDebug,
  getRoomContextState,
  onToggleRoomContext,
}: GitViewPanelProps) {
  const panelConfig =
    resolvePanelGitViewConfig(options) ?? {
      ...createDefaultShadowRepoGitViewConfig(),
      entity_type: "user_repo",
      entity_id_mode: "metadata",
      entity_id_metadata_key: "repo_id",
    }
  const resolvedConfig = resolveShadowRepoGitViewConfig(panelConfig, metadataJson)

  if (!resolvedConfig) {
    return (
      <GitViewInvalidConfig
        title={title}
        subtitle='Git View panel needs a resolvable repo id (typically metadata_json.repo_id).'
        expectedConfig={{
          metadata_json: {
            repo_id: "your-user-repo-id",
          },
          options: {
            source: "shadow_repo",
            entity_type: "user_repo",
            entity_id_mode: "metadata",
            entity_id_metadata_key: "repo_id",
            initial_path: "",
            commit_limit: 10,
            show_file_content: true,
          },
        }}
      />
    )
  }

  return (
    <GitViewCore
      title={title}
      selectionKey={selectionKey ?? `gitViewPanel:${panelId}`}
      config={resolvedConfig}
      rawConfig={panelConfig}
      onSelectFileForDebug={onSelectFileForDebug}
      getRoomContextState={getRoomContextState}
      onToggleRoomContext={onToggleRoomContext}
    />
  )
}
