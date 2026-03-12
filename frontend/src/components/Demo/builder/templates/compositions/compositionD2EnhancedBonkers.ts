import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionD2EnhancedBonkersTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createPanelTemplate, createBlockTemplate, createTemplate } = context
  const composition = createTemplate("composition_b_runtime_coupled")
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.page_theme_id = null
  composition.cards_theme_id = null

  // Composition-level presentation: MAXIMUM VISUAL CHAOS
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 450, // Slow enough to notice
      block_stagger_ms: 120, // Very noticeable stagger
      easing: "cubic-bezier(0.68, -0.55, 0.265, 1.55)", // Bouncy!
    },
    typography: {
      size: "base", // Larger for visibility
      line_height: "tight", // Compressed
      heading_font: "Playfair Display", // Serif! Very different!
      body_font: "JetBrains Mono", // Monospace body text!
    },
    backgrounds: {
      page_gradient:
        "linear-gradient(135deg, rgba(236, 72, 153, 0.25) 0%, rgba(6, 182, 212, 0.2) 50%, rgba(132, 204, 22, 0.15) 100%)",
      svg_overlay: "grid-wave-v1",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 0 30px rgba(236, 72, 153, 0.4), 0 0 60px rgba(6, 182, 212, 0.2)",
      },
    },
    callouts: {
      header: {
        style: "neon-frame",
        text: "BONKERS MODE ACTIVE",
        icon: "alert-triangle",
      },
      footer: {
        style: "runtime-banner",
        text: "If you can read this, callouts work!",
        icon: "check-circle",
      },
    },
    tokens: {
      feed_density: "compact",
      stack_density: "compact",
      matrix_density: "compact",
    },
  }

  composition.metadata_json = {
    template_id: "composition_d2_enhanced_bonkers",
    description:
      "EXTREME visual differentiation for regression detection. Serif headings, monospace body, neon callouts, compact everything. NOT meant to look good - meant to make problems OBVIOUS.",
    preloaded_participants: {
      user_agent_config_ids: ["orchestrator", "coder", "analyst", "reviewer"],
      activate_on_session_start: ["orchestrator", "coder", "analyst"],
    },
  }

  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-d2",
      order: 1,
      title: "🔥 BONKERS RUNTIME 🔥",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 55,
      min_size: 30,
      theme_id: null,
      presentation_json: {
        backgrounds: {
          svg_overlay: "rings-grid-v2", // Different from composition!
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(236, 72, 153, 0.4), rgba(6, 182, 212, 0.4), rgba(132, 204, 22, 0.4))",
          },
        },
        callouts: {
          header: {
            style: "status-pill",
            text: "Panel Override",
            icon: "eye",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-d2",
      order: 2,
      title: "💬 CHAOTIC CHAT 💬",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 45,
      min_size: 20,
      theme_id: null,
      presentation_json: {
        typography: {
          size: "lg", // LARGE chat text
          heading_font: "Playfair Display",
          body_font: "Fira Code", // Different mono font!
        },
        tokens: {
          feed_density: "compact",
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 2px rgba(132, 204, 22, 0.6), 0 0 20px rgba(132, 204, 22, 0.3)",
          },
        },
        callouts: {
          footer: {
            style: "framed-note",
            text: "Chat callout test",
            icon: "message-circle",
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
      id: "participants-d2",
      order: 3,
      title: "👥 WILD PARTICIPANTS 👥",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 30,
      theme_id: null,
      presentation_json: {
        typography: {
          heading_font: "Lora", // Yet another font!
        },
        tokens: {
          stack_density: "compact",
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1", // Third pattern!
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(45deg, rgba(168, 85, 247, 0.4), rgba(236, 72, 153, 0.4))",
          },
        },
      },
      options: {},
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "intro-d2",
      region: "top",
      order: 1,
      title: "⚠️ BONKERS WARNING ⚠️",
      visibility: "visible",
      presentation_json: {
        typography: {
          size: "lg",
          heading_font: "Playfair Display",
          body_font: "JetBrains Mono",
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "Block-level callout",
            icon: "zap",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### D2: ENHANCED BONKERS 🎪\n\nThis template uses **EXTREME styling** to make regressions impossible to miss:\n\n- **Serif headings** (Playfair Display)\n- **Monospace body** (JetBrains Mono)\n- **Neon callouts** with icons\n- **Compact density** everywhere\n- **Three different SVG patterns**\n\nIf something looks normal here, something is broken!",
        metadata: { variant: "callout" },
      },
    },
    {
      ...createBlockTemplate("storyMetadata"),
      id: "metadata-d2",
      region: "primary",
      order: 1,
      title: "📖 Story Metadata",
      visibility: "visible",
      presentation_json: {
        typography: {
          size: "base",
          line_height: "tight",
          heading_font: "Work Sans",
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(45deg, rgba(236, 72, 153, 0.1) 0px, rgba(236, 72, 153, 0.1) 10px, transparent 10px, transparent 20px)",
          },
        },
        callouts: {
          footer: {
            style: "status-pill",
            text: "Metadata loaded",
            icon: "check-circle",
          },
        },
      },
      config_json: {
        show_config_json: true, // Show debug for visibility
      },
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-d2",
      region: "primary",
      order: 2,
      title: "🎭 Orchestrator State",
      visibility: "visible",
      presentation_json: {
        tokens: {
          stack_density: "compact",
          status_badge_style: "high-contrast",
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 40px rgba(6, 182, 212, 0.5), inset 0 0 20px rgba(6, 182, 212, 0.1)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(6, 182, 212, 0.4), rgba(132, 204, 22, 0.4))",
          },
        },
      },
      config_json: {
        show_agent_list: true,
        only_active_agents: false, // Show ALL agents
        show_config_json: true,
      },
    },
    {
      ...createBlockTemplate("agentRoster"),
      id: "roster-d2",
      region: "auxiliary",
      order: 1,
      title: "🤖 Agent Roster",
      visibility: "visible",
      presentation_json: {
        tokens: {
          stack_density: "compact",
        },
        typography: {
          size: "base",
          heading_font: "IBM Plex Sans",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Agents online",
            icon: "users",
          },
        },
      },
      config_json: {
        show_participant_status: true,
      },
    },
    {
      ...createBlockTemplate("toolCapability"),
      id: "tools-d2",
      region: "auxiliary",
      order: 2,
      title: "🛠️ Tool Matrix",
      visibility: "visible",
      presentation_json: {
        tokens: {
          matrix_density: "compact",
        },
        typography: {
          body_font: "Fira Code",
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 25px rgba(132, 204, 22, 0.4)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(132, 204, 22, 0.4), rgba(234, 179, 8, 0.4))",
          },
        },
      },
      config_json: {
        only_active_agents: false,
        show_agent_matrix: true,
        show_config_json: true,
        capability_map: {
          orchestrator: ["plan", "route", "delegate", "monitor"],
          coder: ["code", "diff", "execute", "debug", "refactor"],
          analyst: ["review", "summarize", "validate", "report"],
          reviewer: ["critique", "approve", "reject"],
        },
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-d2",
      region: "auxiliary",
      order: 3,
      title: "📊 Contribution Feed",
      visibility: "visible",
      presentation_json: {
        tokens: {
          feed_density: "compact",
        },
        typography: {
          size: "xs", // Tiny for contrast with chat's LG
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 3px rgba(236, 72, 153, 0.5), 0 0 15px rgba(236, 72, 153, 0.25)",
          },
        },
        callouts: {
          header: {
            style: "runtime-banner",
            text: "Live feed active",
            icon: "activity",
          },
          footer: {
            style: "framed-note",
            text: "Scroll for more",
            icon: "chevron-down",
          },
        },
      },
      config_json: {
        max_items: 25,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
        show_config_json: true,
      },
    },
  ]

  return composition
}

// =============================================================================
// COMPOSITION H: CHAOTIC COMBINATORICS
// =============================================================================
//
// Solo story player + chat with WILDLY VARIED content blocks.
// Hidden storyRuntime (mounted) provides a separate runtime surface.
// Compact participantPanel with picker enabled.
//
// PURPOSE: Determine if motion/color changes are:
// a) Working but too subtle to notice
// b) Actually broken/not rendering
//
// STRATEGY: Every single element has DIFFERENT settings.
// If they all look the same, something is broken.
// If they look chaotically different, everything works.
//
// Panel Configuration:
// - storyPlayer: VISIBLE, primary, slow motion (600ms), serif font
// - chat: VISIBLE, auxiliary, fast motion (100ms), monospace font
// - storyRuntime: HIDDEN_MOUNTED, separate from the solo player state
// - participantPanel: VISIBLE, compact, picker enabled, different SVG
//
// Block Configuration: 8 content blocks, each with unique combinations of:
// - Typography (size, line_height, fonts)
// - Backgrounds (gradients, SVG overlays, card patterns)
// - Effects (card glow variations)
// - Callouts (different slots, styles, icons)
// - Density tokens
// - Motion timing
//
// =============================================================================

