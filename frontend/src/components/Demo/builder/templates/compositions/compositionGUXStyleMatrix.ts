import type {
  EditableComposition,
  EditablePanel,
} from "@/components/Demo/builder/demoBuilderSchema"
import type { TemplateBuilderContext } from "@/components/Demo/builder/templates/templateBuilderContext"
import { createDefaultGitViewConfig } from "@/components/Demo/gitViewConfig"

export function buildCompositionGUXStyleMatrixTemplate(
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
      panel_enter_ms: 300,
      block_stagger_ms: 70,
      easing: "cubic-bezier(0.2, 0.9, 0.2, 1)",
    },
    typography: {
      size: "sm",
      line_height: "relaxed",
    },
    backgrounds: {
      page_gradient:
        "radial-gradient(1200px 600px at 10% 0%, rgba(34,197,94,0.18), rgba(59,130,246,0.14), rgba(2,6,23,0.92))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 10px 30px rgba(2, 6, 23, 0.32)",
      },
    },
  }
  composition.metadata_json = {
    template_id: "composition_g_ux_style_matrix",
    description:
      "Manual UX style-matrix review across panel/block/capability combinations.",
    audit_goal:
      "Subjective and objective pass/fail for motion, typography, backgrounds, effects, overlays.",
    // NOTE: preloaded_participants is pass-through metadata for backend/runtime consumption
    preloaded_participants: {
      user_agent_config_ids: ["orchestrator", "coder", "analyst", "reviewer"],
      activate_on_session_start: ["orchestrator", "coder", "reviewer"],
    },
  }

  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "matrix-story-runtime",
      order: 1,
      title: "Matrix Panel: Story Runtime (overlay + motion)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(90deg, rgba(45,212,191,0.36), rgba(59,130,246,0.24))",
          },
        },
        motion: { panel_enter_ms: 360 },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "matrix-chat",
      order: 2,
      title: "Matrix Panel: Chat (row highlight)",
      prominence: "auxiliary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        effects: {
          message_row_highlight: {
            enable: true,
            css: "inset 0 0 0 1px rgba(14,165,233,0.4), 0 10px 24px rgba(15,23,42,0.35)",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("content"),
      id: "matrix-content",
      order: 3,
      title: "Matrix Panel: Content (rich markdown shell)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      options: {
        content_json: {
          format: "markdown",
          value:
            "## UX Review Panel\nThis panel should show a distinct overlay and subtle entry motion.",
          metadata: { variant: "card" },
        },
      },
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(120deg, rgba(244,114,182,0.3), rgba(34,211,238,0.24))",
          },
        },
        motion: { panel_enter_ms: 240 },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("gitView"),
      id: "matrix-git-view-panel",
      order: 4,
      title: "Matrix Panel: Git View",
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(115deg, rgba(56,189,248,0.24), rgba(251,146,60,0.24))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "matrix-participants",
      order: 5,
      title: "Matrix Panel: Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: {
            css: "linear-gradient(130deg, rgba(250,204,21,0.25), rgba(251,146,60,0.22))",
          },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("canvas"),
      id: "matrix-canvas",
      order: 6,
      title: "Matrix Panel: Canvas",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("a2ui"),
      id: "matrix-a2ui",
      order: 7,
      title: "Matrix Panel: A2UI",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("storyEditor"),
      id: "matrix-story-editor",
      order: 8,
      title: "Matrix Panel: Story Editor",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("storyPlayer"),
      id: "matrix-story-player",
      order: 9,
      title: "Matrix Panel: Solo Story Player",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("debug"),
      id: "matrix-debug",
      order: 10,
      title: "Matrix Panel: Debug",
      prominence: "auxiliary",
      viewport_mode: "panel",
      presentation_json: { typography: { size: "xs" } },
    } as EditablePanel,
  ]

  composition.blocks = [
    {
      ...createBlockTemplate("context"),
      id: "matrix-context",
      region: "top",
      order: 1,
      title: "Matrix Block: Context (top hero)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "lg", line_height: "relaxed" },
        backgrounds: {
          card_pattern: {
            css: "repeating-linear-gradient(135deg, rgba(255,255,255,0.04) 0 14px, rgba(15,23,42,0.12) 14px 28px)",
          },
        },
      },
      content_json: {
        format: "markdown",
        value:
          "### Visual Matrix Checklist\nConfirm typography, surface layering, and background pass-through.",
        metadata: { variant: "card" },
      },
    },
    {
      ...createBlockTemplate("content"),
      id: "matrix-content-block",
      region: "top",
      order: 2,
      title: "Matrix Block: Content (glow effect)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        effects: { card_glow: { enable: true } },
      },
      content_json: {
        format: "markdown",
        value:
          "#### Subjective Review Prompt\nDoes this block feel visually distinct and intentional?",
        metadata: { variant: "card" },
      },
    },
    {
      ...createBlockTemplate("story"),
      id: "matrix-story",
      region: "primary",
      order: 1,
      title: "Matrix Block: Story",
      visibility: "visible",
      theme_id: null,
    },
    {
      ...createBlockTemplate("storyMetadata"),
      id: "matrix-story-meta",
      region: "primary",
      order: 2,
      title: "Matrix Block: Story Metadata",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        backgrounds: {
          card_pattern: {
            css: "linear-gradient(180deg, rgba(30,41,59,0.12), rgba(2,6,23,0.2))",
          },
        },
      },
      config_json: { show_config_json: true },
    },
    {
      ...createBlockTemplate("agentRoster"),
      id: "matrix-roster",
      region: "primary",
      order: 3,
      title: "Matrix Block: Agent Roster",
      visibility: "visible",
      theme_id: null,
      presentation_json: { effects: { card_glow: { enable: true } } },
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "matrix-orchestrator",
      region: "auxiliary",
      order: 1,
      title: "Matrix Block: Orchestrator State (header overlay)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: {
          block_header: {
            css: "linear-gradient(110deg, rgba(147,51,234,0.35), rgba(14,165,233,0.22))",
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
      id: "matrix-tooling",
      region: "auxiliary",
      order: 2,
      title: "Matrix Block: Tool Capability (glow effect)",
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
          coder: ["code", "diff", "execute"],
          analyst: ["review", "summarize"],
          reviewer: ["verify", "approve"],
        },
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "matrix-feed",
      region: "auxiliary",
      order: 3,
      title: "Matrix Block: Contribution Feed (row highlight)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        effects: {
          message_row_highlight: {
            css: "inset 0 0 0 1px rgba(56,189,248,0.24), 0 3px 10px rgba(2,6,23,0.28)",
          },
        },
      },
      config_json: {
        max_items: 14,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
        show_config_json: true,
      },
    },
    {
      ...createBlockTemplate("gitView"),
      id: "matrix-git",
      region: "footer",
      order: 1,
      title: "Matrix Block: Git View",
      visibility: "visible",
      theme_id: null,
      config_json: {
        ...createDefaultGitViewConfig(),
        source: "shadow_repo",
        entity_type: "story",
        entity_id_mode: "metadata",
        entity_id_metadata_key: "story_id",
      },
    },
    {
      ...createBlockTemplate("fileExplorer"),
      id: "matrix-files",
      region: "footer",
      order: 2,
      title: "Matrix Block: File Explorer",
      visibility: "visible",
      theme_id: null,
      config_json: { root_path: "/workspace" },
    },
  ]

  return composition
}

// ============================================================================
// COMPOSITION I: INTENSITY
// ============================================================================
// A gallery of wonder-blocks pushing every visual boundary.
// Each block is a small universe — different typography, motion, color, and
// a fragment of thought from poetry, philosophy, psychology, or art.
// No panels. Just the blocks. Just the wonder.
// ============================================================================
