import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionDStylizedAgentOpsTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createPanelTemplate, createBlockTemplate, createTemplate } = context
  const composition = createTemplate("composition_b_runtime_coupled")
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.page_theme_id = null
  composition.cards_theme_id = null
  // NOTE: Only using fields that demoPresentationResolver.ts actually consumes
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 260,
      block_stagger_ms: 55,
      easing: "cubic-bezier(0.22, 1, 0.36, 1)",
    },
    typography: {
      size: "sm",
      line_height: "relaxed",
    },
    backgrounds: {
      page_gradient:
        "radial-gradient(1200px 500px at 20% 0%, rgba(0, 200, 255, 0.18), rgba(14, 18, 36, 0.9))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 8px 24px rgba(2, 8, 23, 0.35)",
      },
    },
  }
  composition.metadata_json = {
    template_id: "composition_d_stylized_agent_ops",
    description: "Stylized ops baseline with themed panels and chat.",
    // NOTE: preloaded_participants is pass-through metadata for backend/runtime consumption
    preloaded_participants: {
      user_agent_config_ids: ["orchestrator", "coder", "analyst"],
      activate_on_session_start: ["orchestrator", "coder"],
    },
  }
  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-primary",
      order: 1,
      title: "Live Story Runtime",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 62,
      min_size: 36,
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(120deg, rgba(32, 196, 255, 0.16), rgba(12, 22, 42, 0.85))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-stylized-aux",
      order: 2,
      title: "Stylized Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 38,
      min_size: 24,
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(56,189,248,0.35), 0 8px 24px rgba(2,8,23,0.45)",
          },
        },
      },
      options: {
        mode: "participant",
        include_internal_messages: true,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-ops-aux",
      order: 3,
      title: "Ops Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 26,
      options: {},
    } as EditablePanel,
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "mission-brief-bottom",
      region: "footer",
      order: 1,
      title: "Mission Brief",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Beep Beep",
        metadata: {
          variant: "callout",
        },
      },
    },
    {
      ...createBlockTemplate("agentRoster"),
      id: "roster-primary",
      region: "primary",
      order: 1,
      title: "Agent Roster",
      visibility: "visible",
      config_json: {
        show_participant_status: true,
      },
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-primary",
      region: "primary",
      order: 2,
      title: "Orchestrator State",
      visibility: "visible",
      config_json: {
        show_agent_list: true,
        only_active_agents: true,
      },
    },
    {
      ...createBlockTemplate("toolCapability"),
      id: "tools-aux",
      region: "auxiliary",
      order: 1,
      title: "Tool Capability",
      visibility: "visible",
      config_json: {
        only_active_agents: true,
        show_agent_matrix: true,
        capability_map: {
          orchestrator: ["plan", "route"],
          coder: ["code", "diff", "execute"],
          analyst: ["review", "summarize"],
        },
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-aux",
      region: "auxiliary",
      order: 2,
      title: "Contribution Feed",
      visibility: "visible",
      config_json: {
        max_items: 12,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
      },
    },
  ]
  return composition
}

// =============================================================================
// COMPOSITION D1: ENHANCED NORMAL
// =============================================================================
//
// Full-feature showcase with professional, cohesive styling.
// Exercises ALL implemented presentation features:
// - Typography: heading_font (Space Grotesk), body_font (Inter)
// - Callouts: header (frosted), footer (glass-pill)
// - SVG Overlay: constellation-dots-v1
// - Density: comfortable throughout
// - Plus: motion, backgrounds, effects, overlays
//
// This template demonstrates what a polished, production-ready composition
// looks like when using the full range of presentation capabilities.
//
// =============================================================================

