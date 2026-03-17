import {
  resolveGitViewConfig,
  type ResolvedGitViewConfig,
} from "@/components/Demo/gitViewConfig"
import {
  GitViewCore,
  GitViewInvalidConfig,
  type GetGitViewRoomContextState,
  type ToggleGitViewRoomContext,
} from "@/components/Demo/gitView/GitViewCore"

interface GitViewBlockProps {
  title?: string | null
  selectionKey?: string
  config: unknown
  rawConfig?: unknown
  onSelectFileForDebug?: (selectionKey: string, path: string | null) => void
  getRoomContextState?: GetGitViewRoomContextState
  onToggleRoomContext?: ToggleGitViewRoomContext
}

function renderInvalidConfig(title: string | null | undefined) {
  return (
      <GitViewInvalidConfig
      title={title}
      subtitle="Git view requires a live repo configuration."
      expectedConfig={{
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        initial_path: "",
        commit_limit: 10,
        show_file_content: true,
      }}
    />
  )
}

function resolveConfig(config: unknown): ResolvedGitViewConfig | null {
  return resolveGitViewConfig(config)
}

export function GitViewBlock({
  title,
  selectionKey,
  config,
  rawConfig,
  onSelectFileForDebug,
  getRoomContextState,
  onToggleRoomContext,
}: GitViewBlockProps) {
  const liveConfig = resolveConfig(config)
  const displayConfig = rawConfig ?? config

  if (!liveConfig) {
    return renderInvalidConfig(title)
  }

  return (
    <GitViewCore
      title={title}
      selectionKey={selectionKey}
      config={liveConfig}
      rawConfig={displayConfig}
      onSelectFileForDebug={onSelectFileForDebug}
      getRoomContextState={getRoomContextState}
      onToggleRoomContext={onToggleRoomContext}
    />
  )
}
