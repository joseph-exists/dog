import type { EditableComposition } from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionIIntensityTemplate(
  context: TemplateBuilderContext,
): EditableComposition {
  const { createEmptyComposition, createBlockTemplate } = context
  const composition = createEmptyComposition()
  composition.layout_mode = "panels"
  composition.runtime_policy = "manual"
  composition.persona_policy = "first_available"
  composition.chat_mode = "observer"
  composition.page_theme_id = null
  composition.cards_theme_id = null

  // Composition-level: deep cosmic gradient, constellation overlay
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 400,
      block_stagger_ms: 120,
      easing: "cubic-bezier(0.34, 1.56, 0.64, 1)", // Bouncy, playful
    },
    typography: {
      size: "base",
      line_height: "relaxed",
      heading_font: "Playfair Display",
      body_font: "Source Sans Pro",
    },
    backgrounds: {
      page_gradient:
        "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)",
      svg_overlay: "constellation-dots-v1",
    },
    stack_density: "comfortable",
  }

  composition.metadata_json = {
    template_id: "composition_i_intensity",
    description:
      "A gallery of wonder-blocks — wild animations, extreme typography, philosophical fragments.",
  }

  // No panels — just blocks
  composition.panels = []

  // THE BLOCKS: Each one a small universe
  composition.blocks = [
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 1: Rilke — The Questions
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-rilke",
      region: "top",
      order: 1,
      title: "Rilke",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 0 }, // First to appear, no delay
        typography: {
          size: "2xl",
          line_height: "loose",
          heading_font: "Playfair Display",
          body_font: "Lora",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Rainer Maria Rilke",
            icon: "feather",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "radial-gradient(ellipse at 20% 80%, rgba(167, 139, 250, 0.25) 0%, transparent 50%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 60px rgba(167, 139, 250, 0.3)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          '## Live the Questions\n\n> *"Be patient toward all that is unsolved in your heart and try to love the questions themselves, like locked rooms and like books that are now written in a very foreign tongue."*\n\n— Letters to a Young Poet, 1903',
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 2: Mary Oliver — The Wild Life
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-oliver",
      region: "top",
      order: 2,
      title: "Mary Oliver",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 150 },
        typography: {
          size: "xl",
          line_height: "relaxed",
          heading_font: "Space Grotesk",
          body_font: "Inter",
        },
        callouts: {
          footer: {
            style: "neon-frame",
            text: "The Summer Day",
            icon: "sun",
          },
        },
        backgrounds: {
          svg_overlay: "rings-grid-v2",
          card_pattern: {
            css: "linear-gradient(45deg, rgba(34, 197, 94, 0.15) 0%, rgba(52, 211, 153, 0.1) 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 8px 32px rgba(34, 197, 94, 0.25)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          '## One Wild and Precious Life\n\n> *"Tell me, what is it you plan to do with your one wild and precious life?"*\n\nThe question that refuses to let us sleep.',
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 3: Carl Jung — The Unconscious
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("context"),
      id: "intensity-jung",
      region: "primary",
      order: 1,
      title: "Carl Jung",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 300 },
        typography: {
          size: "lg",
          line_height: "normal",
          heading_font: "JetBrains Mono",
          body_font: "Source Sans Pro",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "Psychology",
            icon: "brain",
          },
          footer: {
            style: "status-pill",
            text: "Make the unconscious conscious",
            icon: "eye",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(135deg, rgba(139, 92, 246, 0.08) 0px, rgba(139, 92, 246, 0.08) 2px, transparent 2px, transparent 12px)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(139, 92, 246, 0.4), rgba(236, 72, 153, 0.3))",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          '### The Shadow Work\n\n> *"Until you make the unconscious conscious, it will direct your life and you will call it fate."*\n\nWhat we resist persists. What we embrace transforms.',
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 4: Heraclitus — The River
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-heraclitus",
      region: "primary",
      order: 2,
      title: "Heraclitus",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 450 },
        typography: {
          size: "xs",
          line_height: "tight",
          heading_font: "Inter",
          body_font: "JetBrains Mono",
        },
        callouts: {
          header: {
            style: "framed-note",
            text: "φύσις",
            icon: "waves",
          },
        },
        backgrounds: {
          svg_overlay: "grid-wave-v1",
          card_pattern: {
            css: "linear-gradient(180deg, rgba(14, 165, 233, 0.2) 0%, rgba(6, 182, 212, 0.15) 50%, transparent 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 4px 24px rgba(14, 165, 233, 0.35), inset 0 0 20px rgba(6, 182, 212, 0.1)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "#### FLUX\n\n```\nπάντα ῥεῖ\n\"everything flows\"\n```\n\n> *No man ever steps in the same river twice, for it's not the same river and he's not the same man.*\n\n**535 BCE — 475 BCE**",
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 5: Whitman — Multitudes
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("agentRoster"),
      id: "intensity-whitman",
      region: "auxiliary",
      order: 1,
      title: "Whitman — Multitudes",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 600 },
        typography: {
          size: "sm",
          line_height: "relaxed",
          heading_font: "Playfair Display",
          body_font: "Lora",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Song of Myself",
            icon: "users",
          },
          footer: {
            style: "frosted",
            text: "Do I contradict myself? Very well then, I contradict myself.",
            icon: "sparkles",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "conic-gradient(from 180deg at 50% 50%, rgba(251, 146, 60, 0.12) 0deg, rgba(234, 179, 8, 0.08) 120deg, rgba(245, 158, 11, 0.1) 240deg, rgba(251, 146, 60, 0.12) 360deg)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 40px rgba(251, 146, 60, 0.2)",
          },
        },
      },
      config_json: {
        show_agent_status: true,
        roster_mode: "grid",
        show_capabilities: true,
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 6: Emily Dickinson — Possibility
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-dickinson",
      region: "auxiliary",
      order: 2,
      title: "Emily Dickinson",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 750 },
        typography: {
          size: "base",
          line_height: "loose",
          heading_font: "Lora",
          body_font: "Lora",
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "Poem 657",
            icon: "pen-tool",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "radial-gradient(circle at 80% 20%, rgba(236, 72, 153, 0.2) 0%, transparent 40%), radial-gradient(circle at 20% 80%, rgba(244, 114, 182, 0.15) 0%, transparent 40%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 50px rgba(236, 72, 153, 0.25), 0 0 100px rgba(244, 114, 182, 0.1)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(135deg, rgba(236, 72, 153, 0.5), rgba(168, 85, 247, 0.4))",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "## I Dwell in Possibility\n\n> *I dwell in Possibility —*\n> *A fairer House than Prose —*\n> *More numerous of Windows —*\n> *Superior — for Doors —*\n\nShe wrote 1,800 poems. Published 10 in her lifetime.\nThe rest waited in a drawer.",
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 7: William Blake — Infinity
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("orchestratorState"),
      id: "intensity-blake",
      region: "footer",
      order: 1,
      title: "Blake — Auguries of Innocence",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 900 },
        typography: {
          size: "lg",
          line_height: "normal",
          heading_font: "Space Grotesk",
          body_font: "Inter",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "To see a World in a Grain of Sand",
            icon: "infinity",
          },
          footer: {
            style: "glass-pill",
            text: "Eternity in an hour",
            icon: "clock",
          },
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1",
          card_pattern: {
            css: "linear-gradient(225deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.1) 50%, rgba(167, 139, 250, 0.15) 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 8px 40px rgba(99, 102, 241, 0.3)",
          },
        },
      },
      config_json: {
        show_current_step: true,
        show_step_history: true,
        show_agent_thoughts: true,
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 8: Rumi — The Field
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-rumi",
      region: "footer",
      order: 2,
      title: "Rumi",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1050 },
        typography: {
          size: "xl",
          line_height: "loose",
          heading_font: "Playfair Display",
          body_font: "Source Sans Pro",
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "13th Century Persia",
            icon: "compass",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "radial-gradient(ellipse at 50% 0%, rgba(234, 179, 8, 0.2) 0%, transparent 50%), radial-gradient(ellipse at 50% 100%, rgba(245, 158, 11, 0.15) 0%, transparent 50%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 60px rgba(234, 179, 8, 0.25), 0 0 120px rgba(245, 158, 11, 0.1)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(234, 179, 8, 0.5), rgba(251, 146, 60, 0.4))",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          '## The Field Beyond\n\n> *"Out beyond ideas of wrongdoing and rightdoing, there is a field. I\'ll meet you there.*\n>\n> *When the soul lies down in that grass, the world is too full to talk about."*\n\nThe field is always there. We just forget how to see it.',
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 9: Simone Weil — Attention
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("toolCapability"),
      id: "intensity-weil",
      region: "primary",
      order: 3,
      title: "Simone Weil — Attention",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1200 },
        typography: {
          size: "sm",
          line_height: "relaxed",
          heading_font: "Inter",
          body_font: "Source Sans Pro",
        },
        callouts: {
          header: {
            style: "status-pill",
            text: "Gravity and Grace",
            icon: "heart",
          },
          footer: {
            style: "framed-note",
            text: "Attention is the rarest and purest form of generosity",
            icon: "focus",
          },
        },
        backgrounds: {
          svg_overlay: "rings-grid-v2",
          card_pattern: {
            css: "linear-gradient(180deg, rgba(244, 63, 94, 0.12) 0%, rgba(251, 113, 133, 0.08) 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 4px 30px rgba(244, 63, 94, 0.2)",
          },
        },
      },
      config_json: {
        only_active_agents: false,
        show_agent_matrix: true,
        capability_map: {
          attention: ["observe", "witness", "presence"],
          grace: ["receive", "give", "transform"],
        },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 10: Fernando Pessoa — Wholeness
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-pessoa",
      region: "top",
      order: 3,
      title: "Fernando Pessoa",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1350 },
        typography: {
          size: "base",
          line_height: "normal",
          heading_font: "JetBrains Mono",
          body_font: "JetBrains Mono",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Heteronyms",
            icon: "layers",
          },
          footer: {
            style: "neon-frame",
            text: "Alberto Caeiro · Ricardo Reis · Álvaro de Campos",
            icon: "users",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "repeating-conic-gradient(from 45deg at 50% 50%, rgba(20, 184, 166, 0.08) 0deg 30deg, transparent 30deg 60deg)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 45px rgba(20, 184, 166, 0.25)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "```poem\nTo be great, be whole:\n    don't exaggerate\n    or leave out any part of you.\nBe complete in each thing.\n    Put all you are\n    into the smallest thing you do.\n```\n\n— Ricardo Reis (Fernando Pessoa), *Odes*",
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 11: Ursula K. Le Guin — Darkness
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("contributionFeed"),
      id: "intensity-leguin",
      region: "auxiliary",
      order: 3,
      title: "Le Guin — The Left Hand",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1500 },
        typography: {
          size: "xs",
          line_height: "snug",
          heading_font: "Space Grotesk",
          body_font: "Inter",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "Light is the left hand of darkness",
            icon: "moon",
          },
        },
        backgrounds: {
          svg_overlay: "grid-wave-v1",
          card_pattern: {
            css: "linear-gradient(135deg, rgba(30, 41, 59, 0.9) 0%, rgba(15, 23, 42, 0.95) 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 30px rgba(148, 163, 184, 0.15), inset 0 0 30px rgba(30, 41, 59, 0.5)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(71, 85, 105, 0.6), rgba(100, 116, 139, 0.4))",
          },
        },
      },
      config_json: {
        show_timestamps: true,
        contribution_types: ["thought", "action", "reflection"],
        max_contributions: 5,
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 12: Marcus Aurelius — Impermanence
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("storyMetadata"),
      id: "intensity-aurelius",
      region: "footer",
      order: 3,
      title: "Marcus Aurelius",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1650 },
        typography: {
          size: "lg",
          line_height: "relaxed",
          heading_font: "Playfair Display",
          body_font: "Lora",
        },
        callouts: {
          header: {
            style: "framed-note",
            text: "Meditations, Book IV",
            icon: "scroll",
          },
          footer: {
            style: "status-pill",
            text: "Written 170-180 CE",
            icon: "calendar",
          },
        },
        backgrounds: {
          card_pattern: {
            css: "radial-gradient(circle at 0% 100%, rgba(120, 113, 108, 0.2) 0%, transparent 40%), radial-gradient(circle at 100% 0%, rgba(168, 162, 158, 0.15) 0%, transparent 40%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 8px 32px rgba(120, 113, 108, 0.2)",
          },
        },
      },
      config_json: {
        show_config_json: true,
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 13: Octavia Butler — Change
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-butler",
      region: "primary",
      order: 4,
      title: "Octavia Butler",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1800 },
        typography: {
          size: "xl",
          line_height: "loose",
          heading_font: "Space Grotesk",
          body_font: "Source Sans Pro",
        },
        callouts: {
          header: {
            style: "neon-frame",
            text: "Parable of the Sower",
            icon: "flame",
          },
          footer: {
            style: "glass-pill",
            text: "Earthseed: The Books of the Living",
            icon: "book-open",
          },
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1",
          card_pattern: {
            css: "linear-gradient(45deg, rgba(249, 115, 22, 0.15) 0%, rgba(234, 88, 12, 0.1) 50%, rgba(194, 65, 12, 0.15) 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 50px rgba(249, 115, 22, 0.3), 0 0 100px rgba(234, 88, 12, 0.15)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(90deg, rgba(249, 115, 22, 0.5), rgba(234, 88, 12, 0.4))",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          '## God Is Change\n\n> *"All that you touch, you Change.*\n> *All that you Change, Changes you.*\n> *The only lasting truth is Change.*\n> *God is Change."*\n\nThe shape of God is in the shaping.',
        metadata: { variant: "card" },
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 14: Jorge Luis Borges — The Library
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("gitView"),
      id: "intensity-borges",
      region: "auxiliary",
      order: 4,
      title: "Borges — The Library of Babel",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 1950 },
        typography: {
          size: "sm",
          line_height: "normal",
          heading_font: "JetBrains Mono",
          body_font: "JetBrains Mono",
        },
        callouts: {
          header: {
            style: "frosted",
            text: "The universe (which others call the Library)",
            icon: "library",
          },
          footer: {
            style: "framed-note",
            text: "∞ hexagonal galleries",
            icon: "hexagon",
          },
        },
        backgrounds: {
          svg_overlay: "rings-grid-v2",
          card_pattern: {
            css: "repeating-linear-gradient(0deg, rgba(59, 130, 246, 0.05) 0px, rgba(59, 130, 246, 0.05) 1px, transparent 1px, transparent 20px), repeating-linear-gradient(90deg, rgba(59, 130, 246, 0.05) 0px, rgba(59, 130, 246, 0.05) 1px, transparent 1px, transparent 20px)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 40px rgba(59, 130, 246, 0.2)",
          },
        },
      },
      config_json: {
        show_diff: true,
        show_commit_history: true,
        max_commits: 5,
      },
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // BLOCK 15: Closing — The Intensity Within
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {
      ...createBlockTemplate("content"),
      id: "intensity-closing",
      region: "footer",
      order: 99,
      title: "The Intensity Within",
      visibility: "visible",
      presentation_json: {
        motion: { block_stagger_ms: 2100 },
        typography: {
          size: "2xl",
          line_height: "loose",
          heading_font: "Playfair Display",
          body_font: "Playfair Display",
        },
        callouts: {
          header: {
            style: "glass-pill",
            text: "Composition I",
            icon: "zap",
          },
          footer: {
            style: "neon-frame",
            text: "The wonder is not that the field of stars is so vast, but that we have measured it.",
            icon: "star",
          },
        },
        backgrounds: {
          svg_overlay: "constellation-dots-v1",
          card_pattern: {
            css: "radial-gradient(ellipse at 50% 50%, rgba(167, 139, 250, 0.2) 0%, rgba(139, 92, 246, 0.15) 30%, rgba(99, 102, 241, 0.1) 60%, transparent 100%)",
          },
        },
        effects: {
          card_glow: {
            enable: true,
            css: "0 0 80px rgba(167, 139, 250, 0.35), 0 0 160px rgba(139, 92, 246, 0.2), 0 0 240px rgba(99, 102, 241, 0.1)",
          },
        },
        overlays: {
          block_header: {
            css: "linear-gradient(135deg, rgba(167, 139, 250, 0.4), rgba(236, 72, 153, 0.3), rgba(251, 146, 60, 0.2))",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "# ✦\n\n*Every block is a window.*\n*Every window is a world.*\n*Every world contains the question:*\n\n## What will you build with your intensity?",
        metadata: { variant: "card" },
      },
    },
  ]

  return composition
}
