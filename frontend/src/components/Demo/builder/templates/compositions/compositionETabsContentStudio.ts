import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionETabsContentStudioTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createEmptyComposition, createPanelTemplate, createBlockTemplate } = context
  const composition = createEmptyComposition()
  composition.layout_mode = "tabs"
  composition.runtime_policy = "manual"
  composition.persona_policy = "manual_prompt"
  composition.chat_mode = "observer"
  composition.page_theme_id = null
  composition.cards_theme_id = null
  // NOTE: Only using fields that demoPresentationResolver.ts actually consumes
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 180,
      block_stagger_ms: 40,
      easing: "cubic-bezier(0.4, 0, 0.2, 1)",
    },
    typography: {
      size: "base",
      line_height: "relaxed",
    },
    backgrounds: {
      page_gradient:
        "linear-gradient(165deg, rgba(255, 244, 214, 0.65), rgba(232, 245, 255, 0.72))",
    },
  }
  composition.metadata_json = {
    template_id: "composition_e_tabs_content_studio",
    description:
      "Tabbed demo for content curation, git/file walkthrough, and observer chat.",
  }
  composition.panels = [
    {
      ...createPanelTemplate("content"),
      id: "briefing-tab",
      order: 1,
      title: "Briefing",
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        content_json: {
          format: "markdown",
          value:
            "## Product Review Script\nUse this tabbed composition for QA/Product walkthroughs.",
          metadata: { variant: "card" },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "observer-chat-tab",
      order: 2,
      title: "Observer Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {
        mode: "observer",
        include_internal_messages: false,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("debug"),
      id: "debug-tab",
      order: 3,
      title: "Debug Trace",
      prominence: "auxiliary",
      viewport_mode: "panel",
    } as EditablePanel,
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "studio-top",
      region: "top",
      order: 1,
      title: "Studio Context",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Studio Notes\n- Validate tab flow\n- Validate content readability\n- Validate observer chat",
        metadata: { variant: "card" },
      },
    },
    {
      ...createBlockTemplate("gitView"),
      id: "git-primary",
      region: "primary",
      order: 1,
      title: "Git View",
      visibility: "visible",
      config_json: {
        mode: "summary",
      },
    },
    {
      ...createBlockTemplate("fileExplorer"),
      id: "files-primary",
      region: "primary",
      order: 2,
      title: "File Explorer",
      visibility: "visible",
      config_json: {
        root_path: "/workspace",
      },
    },
    {
      ...createBlockTemplate("context"),
      id: "prompt-aux",
      region: "auxiliary",
      order: 1,
      title: "LLM Prompt Context",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "> Use this slot to stage prompt and rubric snippets during review.",
        metadata: { variant: "callout" },
      },
    },
  ]
  return composition
}

