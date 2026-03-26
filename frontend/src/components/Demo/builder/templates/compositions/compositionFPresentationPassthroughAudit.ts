import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"

export function buildCompositionFPresentationPassthroughAuditTemplate(
  context: TemplateBuilderContext,
): EditableComposition {
  const { createEmptyComposition, createPanelTemplate, createBlockTemplate } =
    context
  const composition = createEmptyComposition()
  composition.layout_mode = "tabs"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.page_theme_id = null
  composition.cards_theme_id = null
  // NOTE: Only using fields that demoPresentationResolver.ts actually consumes
  composition.presentation_json = {
    motion: {
      panel_enter_ms: 320,
      block_stagger_ms: 80,
      easing: "cubic-bezier(0.22, 1, 0.36, 1)",
    },
    typography: {
      size: "sm",
      line_height: "normal",
    },
    backgrounds: {
      page_gradient:
        "linear-gradient(130deg, rgba(255,132,0,0.22), rgba(0,130,255,0.2), rgba(15,23,42,0.95))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 6px 20px rgba(15, 23, 42, 0.28)",
      },
    },
  }
  composition.metadata_json = {
    template_id: "composition_f_presentation_passthrough_audit",
    description: "Pass-through audit across all active panel/block surfaces.",
    audit_goal:
      "motion/typography/backgrounds/effects/overlays passthrough validation",
  }

  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "audit-story-runtime",
      order: 1,
      title: "Audit Panel: Story Runtime (header overlay + motion expected)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(100deg, rgba(251,146,60,0.45), rgba(56,189,248,0.28))",
          },
        },
        motion: {
          panel_enter_ms: 340,
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "audit-chat",
      order: 2,
      title: "Audit Panel: Chat (compact typography + row highlight expected)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        typography: { size: "xs" },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(34,197,94,0.4), 0 6px 18px rgba(3,7,18,0.45)",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("content"),
      id: "audit-content-panel",
      order: 3,
      title: "Audit Panel: Content (markdown style card expected)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      options: {
        content_json: {
          format: "markdown",
          value:
            "## Panel Audit Instructions\nLook for bold heading font and gradient panel chrome.",
          metadata: {
            variant: "card",
          },
        },
      },
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(120deg, rgba(168,85,247,0.35), rgba(6,182,212,0.28))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("gitView"),
      id: "audit-git-view-panel",
      order: 4,
      title: "Audit Panel: Git View (repo surface + context toggle)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      options: {},
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(100deg, rgba(59,130,246,0.34), rgba(16,185,129,0.24))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "audit-participants",
      order: 5,
      title: "Audit Panel: Participants (density + overlay expected)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(140deg, rgba(14,165,233,0.35), rgba(20,184,166,0.28))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("canvas"),
      id: "audit-canvas",
      order: 6,
      title: "Audit Panel: Canvas (container theming expected)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        effects: { card_glow: { enable: true } },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("a2ui"),
      id: "audit-a2ui",
      order: 7,
      title: "Audit Panel: A2UI (theme shell expected)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        motion: { panel_enter_ms: 260 },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("storyEditor"),
      id: "audit-story-editor",
      order: 8,
      title: "Audit Panel: Story Editor (story-bound surface)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(145deg, rgba(244,114,182,0.3), rgba(129,140,248,0.24))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("storyPlayer"),
      id: "audit-story-player",
      order: 9,
      title: "Audit Panel: Solo Story Player (story-bound surface)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(130deg, rgba(16,185,129,0.35), rgba(14,165,233,0.22))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("debug"),
      id: "audit-debug",
      order: 10,
      title: "Audit Panel: Debug (monospace contrast expected)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        typography: { size: "xs" },
      },
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("context"),
      id: "audit-context-top",
      region: "top",
      order: 1,
      title: "Audit Block: Context (top callout)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "lg" },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 10px, rgba(0,0,0,0.08) 10px 20px)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Expected Visuals\nYou should see bold typography, patterned background, and styled card chrome.",
        metadata: { variant: "card" },
      },
    },
    {
      ...createBlockTemplate("content"),
      id: "audit-content-top",
      region: "top",
      order: 2,
      title: "Audit Block: Content (typography and callouts)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "sm", line_height: "relaxed" },
        effects: { card_glow: { enable: true } },
      },
      content_json: {
        format: "markdown",
        value:
          "#### Checkpoint\nIf passthrough works, this card should look distinct from default content cards.",
        metadata: { variant: "card" },
      },
    },
    {
      ...createBlockTemplate("story"),
      id: "audit-story-block",
      region: "primary",
      order: 1,
      title: "Audit Block: Story (structured fallback style shell)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: {
          block_header: {
            css: "linear-gradient(140deg, rgba(253,224,71,0.34), rgba(59,130,246,0.2))",
          },
        },
      },
    },
    {
      ...createBlockTemplate("storyMetadata"),
      id: "audit-story-metadata",
      region: "primary",
      order: 2,
      title: "Audit Block: Story Metadata (runtime text + debug config)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "base", line_height: "relaxed" },
        backgrounds: {
          card_pattern: {
            css: "linear-gradient(180deg, rgba(148,163,184,0.18), rgba(15,23,42,0.15))",
          },
        },
      },
      config_json: {
        show_config_json: true,
      },
    },
    {
      ...createBlockTemplate("agentRoster"),
      id: "audit-agent-roster",
      region: "primary",
      order: 3,
      title: "Audit Block: Agent Roster",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        effects: { card_glow: { enable: true } },
      },
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "audit-orchestrator-state",
      region: "auxiliary",
      order: 1,
      title: "Audit Block: Orchestrator State (header overlay)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: {
          block_header: {
            css: "linear-gradient(125deg, rgba(192,132,252,0.35), rgba(45,212,191,0.2))",
          },
        },
      },
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
        show_config_json: true,
      },
    },
    {
      ...createBlockTemplate("toolCapability"),
      id: "audit-tool-capability",
      region: "auxiliary",
      order: 2,
      title: "Audit Block: Tool Capability (glow effect)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        effects: { card_glow: { enable: true } },
      },
      config_json: {
        only_active_agents: true,
        show_agent_matrix: true,
        show_config_json: true,
        capability_map: {
          orchestrator: ["plan", "route"],
          coder: ["code", "diff"],
          analyst: ["review", "summarize"],
        },
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "audit-contribution-feed",
      region: "auxiliary",
      order: 3,
      title:
        "Audit Block: Contribution Feed (row highlight + sender/timestamps)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        effects: {
          message_row_highlight: {
            css: "inset 0 0 0 1px rgba(56,189,248,0.28)",
          },
        },
      },
      config_json: {
        max_items: 10,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
        show_config_json: true,
      },
    },
    {
      ...createBlockTemplate("gitView"),
      id: "audit-git-view",
      region: "footer",
      order: 1,
      title: "Audit Block: Git View (footer shell styling)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: {
          block_header: {
            css: "linear-gradient(120deg, rgba(52,211,153,0.25), rgba(59,130,246,0.2))",
          },
        },
      },
      config_json: {
        mode: "summary",
      },
    },
    {
      ...createBlockTemplate("fileExplorer"),
      id: "audit-file-explorer",
      region: "footer",
      order: 2,
      title: "Audit Block: File Explorer (footer shell styling)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: {
          block_header: {
            css: "linear-gradient(140deg, rgba(244,63,94,0.24), rgba(34,211,238,0.2))",
          },
        },
      },
      config_json: {
        root_path: "/workspace",
      },
    },
  ]

  return composition
}
