import type {
  EditableComposition,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

export function buildCompositionCVisibilitySemanticsTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createBlockTemplate, createTemplate } = context
  const composition = createTemplate("composition_b_runtime_coupled")
  composition.metadata_json = {
    ...(isObjectRecord(composition.metadata_json)
      ? composition.metadata_json
      : {}),
    template_id: "composition_c_visibility_semantics",
  }
  composition.blocks = [
    {
      ...createBlockTemplate("storyMetadata"),
      id: "story-meta-visible",
      region: "top",
      order: 1,
      title: "Story Metadata (Visible)",
      visibility: "visible",
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-mounted",
      region: "primary",
      order: 1,
      title: "Orchestrator (Hidden Mounted)",
      visibility: "hidden_mounted",
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-unmounted",
      region: "auxiliary",
      order: 1,
      title: "Contribution Feed (Hidden Unmounted)",
      visibility: "hidden_unmounted",
      config_json: {
        max_items: 8,
        include_internal: true,
        show_sender_type: true,
      },
    },
  ]
  return composition
}

