import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionABaselineTemplate(
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
    template_id: "composition_a_baseline",
  }
  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-primary",
      order: 1,
      title: "Story Runtime",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 68,
      min_size: 35,
      options: {
        send_runtime_events_to_chat: true,
        viewer_mode: false,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-aux",
      order: 2,
      title: "Room Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 32,
      min_size: 20,
      options: {
        mode: "participant",
        include_internal_messages: false,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-aux",
      order: 3,
      title: "Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 24,
      min_size: 15,
      options: {},
    } as EditablePanel,
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "instructions-footer",
      region: "footer",
      order: 1,
      title: "Demo Footer",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value: "### Just an Extra Block for Funsies",
        metadata: {
          variant: "card",
        },
      },
    },
  ]
  return composition
}
