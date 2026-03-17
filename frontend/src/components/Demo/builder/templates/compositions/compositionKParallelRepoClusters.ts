import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionKParallelRepoClustersTemplate(
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
    template_id: "composition_k_parallel_repo_clusters",
    repo_id: "",
    repo_id_secondary: "",
    description:
      "Two independent repo clusters in one room, each with its own explorer and viewer pair.",
  }

  composition.panels = [
    {
      ...createPanelTemplate("fileExplorer"),
      id: "repo-a-explorer",
      order: 1,
      title: "Repo A Explorer",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 24,
      min_size: 18,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        selection_key: "repo.cluster.a.selection",
        initial_path: "",
        ref: null,
        show_sizes: true,
        show_commit_badge: true,
        empty_label: "Select a file from the first repo.",
        title: "Repo A Explorer",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("fileViewer"),
      id: "repo-a-viewer",
      order: 2,
      title: "Repo A Viewer",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 26,
      min_size: 20,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id",
        path_mode: "selection",
        selection_key: "repo.cluster.a.selection",
        ref: null,
        title: "Repo A Viewer",
        show_path_badge: true,
        show_copy_control: true,
        empty_label: "Repo A files selected in the explorer appear here.",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("fileExplorer"),
      id: "repo-b-explorer",
      order: 3,
      title: "Repo B Explorer",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 24,
      min_size: 18,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id_secondary",
        selection_key: "repo.cluster.b.selection",
        initial_path: "",
        ref: null,
        show_sizes: true,
        show_commit_badge: true,
        empty_label: "Select a file from the second repo.",
        title: "Repo B Explorer",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("fileViewer"),
      id: "repo-b-viewer",
      order: 4,
      title: "Repo B Viewer",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 26,
      min_size: 20,
      options: {
        source: "user_repo",
        entity_type: "user_repo",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "repo_id_secondary",
        path_mode: "selection",
        selection_key: "repo.cluster.b.selection",
        ref: null,
        title: "Repo B Viewer",
        show_path_badge: true,
        show_copy_control: true,
        empty_label: "Repo B files selected in the explorer appear here.",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "parallel-repo-chat",
      order: 5,
      title: "Coordination Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 20,
      min_size: 16,
      options: {
        mode: "participant",
        include_internal_messages: false,
      },
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "parallel-repo-guide",
      region: "top",
      order: 1,
      title: "Parallel Repo Clusters",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Two Repos, One Room\n- Set `metadata_json.repo_id` and `metadata_json.repo_id_secondary`.\n- Each explorer/viewer pair has its own `selection_key`, so repo clusters stay isolated.\n- This is the proof point for multi-repo review rooms, side-by-side implementation comparisons, and coordinated agent/user workflows across separate repositories.",
        metadata: {
          variant: "card",
        },
      },
    },
  ]

  return composition
}
