import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionBRuntimeCoupledTemplate(
  context: TemplateBuilderContext,
): EditableComposition {
  const { createEmptyComposition, createPanelTemplate, createBlockTemplate } =
    context
  const composition = createEmptyComposition()
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.metadata_json = {
    template_id: "composition_b_runtime_coupled",
  }
  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-primary",
      order: 1,
      title: "Story Runtime",
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        send_runtime_events_to_chat: true,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-aux",
      order: 2,
      title: "Room Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {
        mode: "participant",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-aux",
      order: 3,
      title: "Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
    } as EditablePanel,
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("storyMetadata"),
      id: "story-meta-top",
      region: "top",
      order: 1,
      title: "Story Metadata",
      visibility: "visible",
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-primary",
      region: "primary",
      order: 1,
      title: "Orchestrator State",
      visibility: "visible",
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-aux",
      region: "auxiliary",
      order: 1,
      title: "Contribution Feed",
      visibility: "visible",
      config_json: {
        max_items: 8,
        include_internal: true,
        show_sender_type: true,
      },
    },
  ]
  return composition
}
