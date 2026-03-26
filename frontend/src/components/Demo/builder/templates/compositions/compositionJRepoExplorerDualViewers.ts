import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionJRepoExplorerDualViewersTemplate(
  context: TemplateBuilderContext,
): EditableComposition {
  const { createEmptyComposition, createPanelTemplate, createBlockTemplate } =
    context
  const composition = createEmptyComposition()

  composition.layout_mode = "panels"
  composition.runtime_policy = "manual"
  composition.persona_policy = "manual_prompt"
  composition.chat_mode = "participant"
  composition.metadata_json = {
    template_id: "composition_j_repo_explorer_dual_viewers",
    repo_id: "",
    description:
      "Repo-first composition with one live explorer, one selection-driven viewer, and one README companion viewer.",
  }

  composition.panels = [
    {
      ...createPanelTemplate("fileExplorer"),
      id: "repo-explorer-main",
      order: 1,
      title: "Repo Explorer",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 34,
      min_size: 22,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        selection_key: "repo.primary.selection",
        initial_path: "",
        ref: null,
        show_sizes: true,
        show_commit_badge: true,
        empty_label: "Pick a repo file to inspect.",
        title: "Repo Explorer",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("fileViewer"),
      id: "repo-viewer-selection",
      order: 2,
      title: "Selected File",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 38,
      min_size: 25,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        path_mode: "selection",
        selection_key: "repo.primary.selection",
        ref: null,
        title: "Selected File",
        show_path_badge: true,
        show_copy_control: true,
        empty_label: "Select a file in the explorer to load it here.",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("fileViewer"),
      id: "repo-viewer-readme",
      order: 3,
      title: "Repo README",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 28,
      min_size: 20,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        path_mode: "readme",
        ref: null,
        title: "Repo README",
        show_path_badge: true,
        show_copy_control: true,
        empty_label:
          "README content will appear here when the repo exposes one.",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "repo-chat-aux",
      order: 4,
      title: "Room Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 24,
      min_size: 18,
      options: {
        mode: "participant",
        include_internal_messages: false,
      },
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "repo-layout-guide",
      region: "top",
      order: 1,
      title: "Repo Collaboration Pattern",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Explorer + Dual Viewers\n- Set `metadata_json.repo_id` to the repo you want to demo.\n- `Repo Explorer` drives `Selected File` through `repo.primary.selection`.\n- `Repo README` stays pinned as a stable companion surface.\n- Duplicate the selection-driven viewer and change its `selection_key` or `path_mode` to support more advanced multi-file review flows.",
        metadata: {
          variant: "card",
        },
      },
    },
  ]

  return composition
}
