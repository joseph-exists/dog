import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionHChaoticCombinatoricsTemplate(context: TemplateBuilderContext): EditableComposition {
  const { createEmptyComposition, createPanelTemplate, createBlockTemplate } = context
  const composition = createEmptyComposition()
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.page_theme_id = null
  composition.cards_theme_id = null

  // Composition-level: Set baseline chaos
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 400,
      block_stagger_ms: 150, // Very noticeable stagger
      easing: "cubic-bezier(0.34, 1.56, 0.64, 1)", // Overshoot bounce
    },
    typography: {
      size: "base",
      line_height: "normal",
      heading_font: "Playfair Display",
      body_font: "Source Sans Pro",
    },
    backgrounds: {
      page_gradient:
        "conic-gradient(from 45deg at 30% 30%, rgba(251, 146, 60, 0.2), rgba(168, 85, 247, 0.2), rgba(34, 211, 238, 0.2), rgba(251, 146, 60, 0.2))",
      svg_overlay: "grid-wave-v1",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 0 40px rgba(251, 146, 60, 0.3), 0 0 80px rgba(168, 85, 247, 0.15)",
      },
    },
    callouts: {
      header: {
        style: "runtime-banner",
        text: "🎰 CHAOTIC COMBINATORICS 🎰",
        icon: "shuffle",
      },
    },
    tokens: {
      feed_density: "comfortable",
      stack_density: "comfortable",
      matrix_density: "standard",
    },
  }

  composition.metadata_json = {
    template_id: "composition_h_chaotic_combinatorics",
    description:
      "Tests if presentation features are working by making every element DIFFERENT. If they look the same, something is broken.",
    preloaded_participants: {
      user_agent_config_ids: ["orchestrator", "coder", "analyst"],
      activate_on_session_start: ["orchestrator"],
    },
  }

  composition.panels = [
    // STORY PLAYER: Primary, SLOW motion, serif fonts, rings overlay
    {
      ...createPanelTemplate("storyPlayer"),
      id: "player-h",
      order: 1,
      title: "📽️ Story Player (SLOW 600ms)",
      prominence: "primary",
      viewport_mode: "panel",
      default_size: 45,
      min_size: 30,
      theme_id: null,
      presentation_json: {
        motion: {
          panel_enter_ms: 600, // VERY SLOW
          easing: "cubic-bezier(0.87, 0, 0.13, 1)", // Smooth decel
        },
        typography: {
          size: "lg",
          heading_font: "Lora", // Serif
          body_font: "Lora",
        },
        backgrounds: {
          svg_overlay: "rings-grid-v2",
          page_gradient:
            "linear-gradient(180deg, rgba(217, 70, 239, 0.15) 0%, transparent 50%)",
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(217, 70, 239, 0.4), rgba(168, 85, 247, 0.4))",
          },
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "SLOW PANEL (600ms)",
            icon: "clock",
          },
          footer: {
            style: "glass-pill",
            text: "Serif typography active",
            icon: "type",
          },
        },
      },
    } as EditablePanel,

    // CHAT: Auxiliary, FAST motion, monospace fonts, constellation overlay
    {
      ...createPanelTemplate("chat"),
      id: "chat-h",
      order: 2,
      title: "💬 Chat (FAST 100ms)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 35,
      min_size: 20,
      theme_id: null,
      presentation_json: {
        motion: {
          panel_enter_ms: 100, // VERY FAST
          easing: "linear", // No easing - instant
        },
        typography: {
          size: "sm",
          heading_font: "JetBrains Mono",
          body_font: "Fira Code",
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1",
        },
        tokens: {
          feed_density: "compact",
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 2px rgba(34, 211, 238, 0.6), 0 0 30px rgba(34, 211, 238, 0.3)",
          },
        },
        callouts: {
          header: {
            style: "status-pill",
            text: "FAST PANEL (100ms)",
            icon: "zap",
          },
        },
      },
      options: {
        mode: "participant",
        include_internal_messages: true,
      },
    } as EditablePanel,

    // STORY RUNTIME: Minimal panel providing runtime context for story player
    // Note: Panels don't support hidden_mounted like blocks - using small size
    {
      ...createPanelTemplate("storyRuntime"),
      id: "runtime-h-minimal",
      order: 3,
      title: "🔌 Runtime (Minimal)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 10, // Small but visible - proves runtime is active
      min_size: 8,
      theme_id: null,
      presentation_json: {
        // Extreme rainbow styling to make it unmistakable
        backgrounds: {
          page_gradient:
            "linear-gradient(90deg, rgba(239, 68, 68, 0.3), rgba(234, 179, 8, 0.3), rgba(34, 197, 94, 0.3), rgba(6, 182, 212, 0.3))",
          svg_overlay: "rings-grid-v2",
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "RUNTIME ACTIVE",
            icon: "cpu",
          },
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(239, 68, 68, 0.5), rgba(234, 179, 8, 0.5), rgba(34, 197, 94, 0.5))",
          },
        },
      },
    } as EditablePanel,

    // PARTICIPANT PANEL: Compact, picker enabled, different styling
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-h",
      order: 4,
      title: "👥 Compact Picker",
      prominence: "auxiliary",
      viewport_mode: "panel",
      default_size: 20,
      min_size: 15,
      theme_id: null,
      presentation_json: {
        motion: {
          panel_enter_ms: 300,
          easing: "cubic-bezier(0.68, -0.6, 0.32, 1.6)", // Strong overshoot
        },
        typography: {
          size: "xs",
          heading_font: "Work Sans",
        },
        tokens: {
          stack_density: "compact",
        },
        backgrounds: {
          svg_overlay: "grid-wave-v1",
          page_gradient:
            "linear-gradient(135deg, rgba(132, 204, 22, 0.2), transparent)",
        },
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(132, 204, 22, 0.4), rgba(234, 179, 8, 0.4))",
          },
        },
        callouts: {
          footer: {
            style: "framed-note",
            text: "Picker enabled, compact density",
            icon: "users",
          },
        },
      },
      options: {
        compact: true,
        allowQuickAdd: true,
      },
    } as EditablePanel,
  ]

  // CONTENT BLOCKS: 8 blocks with combinatoric variation
  composition.blocks = [
    // Block 1: XS text, tight line height, frosted callout header
    {
      ...createBlockTemplate("content"),
      id: "block-combo-1",
      region: "top",
      order: 1,
      title: "Block 1: XS + Tight + Frosted",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 50 },
        typography: {
          size: "xs",
          line_height: "tight",
          heading_font: "Inter",
          body_font: "Inter",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "XS/Tight/Frosted",
            icon: "minimize-2",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Block 1\n`size: xs` | `line_height: tight` | `callout: frosted header`\n\nIf this text is NOT tiny and compressed, typography is broken.",
        metadata: { variant: "card" },
      },
    },

    // Block 2: LG text, relaxed line height, neon-frame callout footer
    {
      ...createBlockTemplate("content"),
      id: "block-combo-2",
      region: "top",
      order: 2,
      title: "Block 2: LG + Relaxed + Neon",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 200 },
        typography: {
          size: "lg",
          line_height: "relaxed",
          heading_font: "Playfair Display",
          body_font: "Source Sans Pro",
        },
        callouts: {
          footer: {
            style: "neon-frame",
            text: "LG/Relaxed/Neon",
            icon: "maximize-2",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(45deg, rgba(6, 182, 212, 0.1) 0px 10px, transparent 10px 20px)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Block 2\n`size: lg` | `line_height: relaxed` | `callout: neon-frame footer`\n\nIf this text is NOT large and spacious, typography is broken.",
        metadata: { variant: "card" },
      },
    },

    // Block 3: SM text, glass-pill both slots, card glow
    {
      ...createBlockTemplate("content"),
      id: "block-combo-3",
      region: "primary",
      order: 1,
      title: "Block 3: SM + Both Callouts + Glow",
      visibility: "visible",
      presentation_json: {
        typography: {
          size: "sm",
          heading_font: "Space Grotesk",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Header pill",
            icon: "arrow-up",
          },
          footer: {
            style: "glass-pill",
            text: "Footer pill",
            icon: "arrow-down",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 50px rgba(236, 72, 153, 0.5), inset 0 0 30px rgba(236, 72, 153, 0.1)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Block 3\n`size: sm` | Both callout slots | Strong pink glow\n\nShould have header AND footer pills, plus pink glow.",
        metadata: { variant: "card" },
      },
    },

    // Block 4: BASE text, framed-note callout, rings SVG overlay
    {
      ...createBlockTemplate("content"),
      id: "block-combo-4",
      region: "primary",
      order: 2,
      title: "Block 4: Base + Framed + Rings SVG",
      visibility: "visible",
      presentation_json: {
        typography: {
          size: "base",
          line_height: "normal",
          body_font: "IBM Plex Sans",
        },
        callouts: {
          header: {
            style: "framed-note",
            text: "Framed note style",
            icon: "file-text",
          },
        },
        backgrounds: {
          svg_overlay: "rings-grid-v2",
          page_gradient:
            "linear-gradient(180deg, rgba(234, 179, 8, 0.2), transparent)",
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Block 4\n`size: base` | `framed-note` callout | `rings-grid-v2` SVG\n\nShould have amber border on callout and rings pattern.",
        metadata: { variant: "card" },
      },
    },

    // Block 5: XS + status-pill + constellation SVG + compact feed density
    {
      ...createBlockTemplate("contributionFeed"),
      id: "block-combo-5",
      region: "auxiliary",
      order: 1,
      title: "Block 5: Feed + Status Pill + Constellation",
      visibility: "visible",
      presentation_json: {
        typography: { size: "xs" },
        tokens: { feed_density: "compact" },
        callouts: {
          header: { style: "status-pill", text: "Compact feed", icon: "list" },
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1",
        },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(132, 204, 22, 0.5)",
          },
        },
      },
      config_json: {
        max_items: 8,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
      },
    },

    // Block 6: Orchestrator state + runtime-banner + compact stack
    {
      ...createBlockTemplate("orchestratorState"),
      id: "block-combo-6",
      region: "auxiliary",
      order: 2,
      title: "Block 6: Orchestrator + Runtime Banner",
      visibility: "visible",
      presentation_json: {
        tokens: {
          stack_density: "compact",
          status_badge_style: "high-contrast",
        },
        callouts: {
          header: {
            style: "runtime-banner",
            text: "Orchestrator view",
            icon: "activity",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(168, 85, 247, 0.4), rgba(236, 72, 153, 0.4))",
          },
        },
      },
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
        show_config_json: true,
      },
    },

    // Block 7: Tool capability + compact matrix + multiple effects
    {
      ...createBlockTemplate("toolCapability"),
      id: "block-combo-7",
      region: "auxiliary",
      order: 3,
      title: "Block 7: Tools + Compact Matrix",
      visibility: "visible",
      presentation_json: {
        typography: {
          heading_font: "JetBrains Mono",
          body_font: "JetBrains Mono",
        },
        tokens: { matrix_density: "compact" },
        callouts: {
          footer: {
            style: "neon-frame",
            text: "Matrix density: compact",
            icon: "grid",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 35px rgba(6, 182, 212, 0.4)",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-conic-gradient(from 0deg at 50% 50%, rgba(6, 182, 212, 0.05) 0deg 10deg, transparent 10deg 20deg)",
          },
        },
      },
      config_json: {
        only_active_agents: false,
        show_agent_matrix: true,
        capability_map: {
          orchestrator: ["plan", "route"],
          coder: ["code", "execute"],
          analyst: ["review"],
        },
      },
    },

    // Block 8: Story metadata + ALL features maxed out
    {
      ...createBlockTemplate("storyMetadata"),
      id: "block-combo-8",
      region: "primary",
      order: 3,
      title: "Block 8: Metadata + EVERYTHING",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 300 },
        typography: {
          size: "sm",
          line_height: "relaxed",
          heading_font: "Lora",
          body_font: "Work Sans",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "Story metadata",
            icon: "book-open",
          },
          footer: {
            style: "status-pill",
            text: "All features active",
            icon: "check-circle",
          },
        },
        backgrounds: {
          svg_overlay: "grid-wave-v1",
          card_pattern: {
            css: "radial-gradient(circle at 100% 0%, rgba(251, 146, 60, 0.15) 0%, transparent 40%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 4px 20px rgba(251, 146, 60, 0.25), 0 0 40px rgba(168, 85, 247, 0.15)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(251, 146, 60, 0.3), rgba(234, 179, 8, 0.3))",
          },
        },
      },
      config_json: {
        show_config_json: true,
      },
    },
  ]

  return composition
}

