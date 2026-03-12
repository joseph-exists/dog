import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionD1EnhancedNormalTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createPanelTemplate, createBlockTemplate, createTemplate } = context
  const composition = createTemplate("composition_b_runtime_coupled")
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.page_theme_id = null
  composition.cards_theme_id = null

  // Composition-level presentation: Professional, cohesive styling
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 280,
      block_stagger_ms: 60,
      easing: "cubic-bezier(0.22, 1, 0.36, 1)",
    },
    typography: {
      size: "sm",
      line_height: "relaxed",
      heading_font: "Space Grotesk",
      body_font: "Inter",
    },
    backgrounds: {
      page_gradient:
        "radial-gradient(ellipse 1400px 600px at 15% 0%, rgba(99, 102, 241, 0.15), rgba(15, 23, 42, 0.95))",
      svg_overlay: "constellation-dots-v1",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 8px 32px rgba(99, 102, 241, 0.12), 0 4px 12px rgba(0, 0, 0, 0.25)",
      },
    },
    callouts: {
      header: {
        style: "frosted",
        text: "Enhanced Normal Template",
        icon: "sparkles",
      },
    },
    tokens: {
      feed_density: "comfortable",
      stack_density: "comfortable",
      matrix_density: "standard",
    },
  }

  composition.metadata_json = {
    template_id: "composition_d1_enhanced_normal",
    description:
      "Full-feature showcase with professional styling. Demonstrates fonts, callouts, SVG overlays, and density tokens working together.",
    preloaded_participants: {
      user_agent_config_ids: ["orchestrator", "coder", "analyst"],
      activate_on_session_start: ["orchestrator", "coder"],
    },
  }

  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-d1",
      order: 1,
      title: "Story Runtime",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 60,
      min_size: 36,
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(15, 23, 42, 0.9))",
          },
        },
        callouts: {
          footer: {
            style: "glass-pill",
            text: "Runtime Active",
            icon: "zap",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-d1",
      order: 2,
      title: "Team Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 40,
      min_size: 24,
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        tokens: {
          feed_density: "comfortable",
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(99, 102, 241, 0.25), 0 4px 16px rgba(0, 0, 0, 0.2)",
          },
        },
      },
      options: {
        mode: "participant",
        include_internal_messages: false,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-d1",
      order: 3,
      title: "Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 28,
      theme_id: null,
      presentation_json: {
        tokens: {
          stack_density: "comfortable",
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(99, 102, 241, 0.12), transparent)",
          },
        },
      },
      options: {},
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "intro-d1",
      region: "top",
      order: 1,
      title: "Template Overview",
      visibility: "visible",
      presentation_json: {
        typography: {
          heading_font: "Space Grotesk",
          body_font: "Inter",
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### D1: Enhanced Normal\nThis template demonstrates all implemented presentation features with **professional, cohesive styling**.\n\n- Custom fonts (Space Grotesk / Inter)\n- Constellation dots SVG overlay\n- Frosted callouts\n- Comfortable density throughout",
        metadata: { variant: "callout" },
      },
    },
    {
      ...createBlockTemplate("storyMetadata"),
      id: "metadata-d1",
      region: "primary",
      order: 1,
      title: "Story Metadata",
      visibility: "visible",
      presentation_json: {
        typography: {
          size: "sm",
          line_height: "normal",
        },
        backgrounds: {
          card_pattern: {
            css: "radial-gradient(circle at 80% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%)",
          },
        },
      },
      config_json: {
        show_config_json: false,
      },
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-d1",
      region: "primary",
      order: 2,
      title: "Orchestrator State",
      visibility: "visible",
      presentation_json: {
        tokens: {
          stack_density: "comfortable",
          status_badge_style: "default",
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 4px 16px rgba(99, 102, 241, 0.15)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(99, 102, 241, 0.15), transparent)",
          },
        },
      },
      config_json: {
        show_agent_list: true,
        only_active_agents: true,
      },
    },
    {
      ...createBlockTemplate("agentRoster"),
      id: "roster-d1",
      region: "auxiliary",
      order: 1,
      title: "Agent Roster",
      visibility: "visible",
      presentation_json: {
        tokens: {
          stack_density: "comfortable",
        },
        typography: { size: "sm" },
      },
      config_json: {
        show_participant_status: true,
      },
    },
    {
      ...createBlockTemplate("toolCapability"),
      id: "tools-d1",
      region: "auxiliary",
      order: 2,
      title: "Tool Capabilities",
      visibility: "visible",
      presentation_json: {
        tokens: {
          matrix_density: "standard",
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(34, 197, 94, 0.12), transparent)",
          },
        },
      },
      config_json: {
        only_active_agents: true,
        show_agent_matrix: true,
        capability_map: {
          orchestrator: ["plan", "route", "delegate"],
          coder: ["code", "diff", "execute"],
          analyst: ["review", "summarize", "validate"],
        },
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-d1",
      region: "auxiliary",
      order: 3,
      title: "Contribution Feed",
      visibility: "visible",
      presentation_json: {
        tokens: {
          feed_density: "comfortable",
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(99, 102, 241, 0.2)",
          },
        },
      },
      config_json: {
        max_items: 15,
        include_internal: false,
        show_sender_type: true,
        show_timestamps: true,
      },
    },
  ]

  return composition
}

// =============================================================================
// COMPOSITION D2: ENHANCED BONKERS
// =============================================================================
//
// INTENTIONALLY EXTREME visual styling for regression detection.
// If any feature breaks, you'll notice immediately because everything
// is dialed up to maximum contrast and differentiation.
//
// Features exercised at MAXIMUM VISIBILITY:
// - Typography: Playfair Display (serif!) headings, JetBrains Mono body
// - Callouts: neon-frame headers, status-pill footers
// - SVG Overlay: grid-wave-v1 at composition, rings-grid-v2 on panels
// - Density: COMPACT everywhere
// - Colors: Hot pink, electric cyan, lime green
//
// This is NOT meant to look good. It's meant to make regressions OBVIOUS.
//
// =============================================================================

