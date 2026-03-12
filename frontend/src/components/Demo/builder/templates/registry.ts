import type { EditableComposition } from "@/components/Demo/builder/demoBuilderSchema"
import { buildCompositionABaselineTemplate } from "@/components/Demo/builder/templates/compositions/compositionABaseline"
import { buildCompositionBRuntimeCoupledTemplate } from "@/components/Demo/builder/templates/compositions/compositionBRuntimeCoupled"
import { buildCompositionCVisibilitySemanticsTemplate } from "@/components/Demo/builder/templates/compositions/compositionCVisibilitySemantics"
import { buildCompositionD1EnhancedNormalTemplate } from "@/components/Demo/builder/templates/compositions/compositionD1EnhancedNormal"
import { buildCompositionD2EnhancedBonkersTemplate } from "@/components/Demo/builder/templates/compositions/compositionD2EnhancedBonkers"
import { buildCompositionDStylizedAgentOpsTemplate } from "@/components/Demo/builder/templates/compositions/compositionDStylizedAgentOps"
import { buildCompositionETabsContentStudioTemplate } from "@/components/Demo/builder/templates/compositions/compositionETabsContentStudio"
import { buildCompositionFPresentationPassthroughAuditTemplate } from "@/components/Demo/builder/templates/compositions/compositionFPresentationPassthroughAudit"
import { buildCompositionGUXStyleMatrixTemplate } from "@/components/Demo/builder/templates/compositions/compositionGUXStyleMatrix"
import { buildCompositionHChaoticCombinatoricsTemplate } from "@/components/Demo/builder/templates/compositions/compositionHChaoticCombinatorics"
import { buildCompositionIIntensityTemplate } from "@/components/Demo/builder/templates/compositions/compositionIIntensity"
import type {
  BuilderCompositionTemplateOption,
  BuilderCompositionTemplateSchema,
  BuilderTemplateId,
} from "@/components/Demo/builder/templates/types"
import type {
  TemplateBuilder,
  TemplateBuilderContext,
} from "@/components/Demo/builder/templates/templateBuilderContext"

export const BUILDER_COMPOSITION_TEMPLATE_SCHEMAS: Record<
  BuilderTemplateId,
  BuilderCompositionTemplateSchema
> = {
  composition_a_baseline: {
    id: "composition_a_baseline",
    label: "Composition A: Baseline Story + Chat",
    description:
      "Story runtime + chat with a constant instructional content block.",
    requiredAssumptions: ["story_id", "runtime_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Set metadata_json.story_id so story-dependent renderers can resolve content.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime start behavior for this demo flow.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description:
          "Confirm participant/observer mode for intended QA scenario.",
        severity: "warning",
      },
    ],
  },
  composition_b_runtime_coupled: {
    id: "composition_b_runtime_coupled",
    label: "Composition B: Runtime-Coupled Blocks",
    description:
      "Adds story metadata, orchestrator state, and contribution feed coverage.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for storyMetadata and story runtime coupling.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime lifecycle mode for coupled block data.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm persona selection behavior for orchestration visibility.",
        severity: "warning",
      },
      {
        id: "fixed_user_persona_id",
        label: "Fixed Persona ID",
        description: "Set when persona_policy is fixed_user_persona.",
        severity: "warning",
      },
    ],
  },
  composition_c_visibility_semantics: {
    id: "composition_c_visibility_semantics",
    label: "Composition C: Visibility Semantics",
    description:
      "Exercises visible, hidden_mounted, and hidden_unmounted block permutations.",
    requiredAssumptions: ["story_id", "runtime_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for storyMetadata visibility validation coverage.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime mode expected by visibility test flows.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description:
          "Confirm mode used while validating mounted/unmounted visibility behavior.",
        severity: "warning",
      },
    ],
  },
  composition_d_stylized_agent_ops: {
    id: "composition_d_stylized_agent_ops",
    label: "Composition D: Stylized Agent Ops",
    description:
      "Plug-and-play story/chat + participant/tooling coverage with stylized presentation defaults.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story runtime, story metadata, and narrative chat callouts.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description:
          "Confirm runtime lifecycle for orchestrator/contribution behavior.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm participant policy for preloaded UserAgentConfig scenarios.",
        severity: "warning",
      },
      {
        id: "fixed_user_persona_id",
        label: "Fixed Persona ID",
        description:
          "Set when persona policy is fixed persona for deterministic QA playback.",
        severity: "warning",
      },
    ],
  },
  composition_d1_enhanced_normal: {
    id: "composition_d1_enhanced_normal",
    label: "Composition D1: Enhanced Normal",
    description:
      "Full-feature showcase with professional styling. Exercises fonts, callouts, SVG overlays, and density tokens using cohesive, production-appropriate patterns.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story runtime, story metadata, and narrative chat callouts.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description:
          "Confirm runtime lifecycle for orchestrator/contribution behavior.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm participant policy for preloaded UserAgentConfig scenarios.",
        severity: "warning",
      },
    ],
  },
  composition_d2_enhanced_bonkers: {
    id: "composition_d2_enhanced_bonkers",
    label: "Composition D2: Enhanced Bonkers",
    description:
      "Extreme visual differentiation for regression detection. Wild fonts, neon callouts, mixed SVG patterns, and compact density everywhere. If something breaks, you'll see it.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story runtime, story metadata, and narrative chat callouts.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description:
          "Confirm runtime lifecycle for orchestrator/contribution behavior.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm participant policy for preloaded UserAgentConfig scenarios.",
        severity: "warning",
      },
    ],
  },
  composition_e_tabs_content_studio: {
    id: "composition_e_tabs_content_studio",
    label: "Composition E: Tabs Content Studio",
    description:
      "Tabs layout with content/browser-style blocks for product curation and LLM prompt walkthroughs.",
    requiredAssumptions: ["story_id", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story-linked views in tabbed composition flows.",
        severity: "error",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description:
          "Confirm participant/observer behavior for walkthrough and review sessions.",
        severity: "warning",
      },
    ],
  },
  composition_f_presentation_passthrough_audit: {
    id: "composition_f_presentation_passthrough_audit",
    label: "Composition F: Presentation Passthrough Audit",
    description:
      "Comprehensive panel/block style audit template with explicit visual expectation text.",
    requiredAssumptions: [
      "story_id",
      "runtime_policy",
      "persona_policy",
      "chat_mode",
    ],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story-linked panels/blocks in this full-surface audit.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description:
          "Confirm runtime mode before auditing runtime-coupled visuals and motion.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm persona mode for participant and tooling visual checks.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description:
          "Confirm chat rendering mode for callout/typography checks.",
        severity: "warning",
      },
    ],
  },
  composition_g_ux_style_matrix: {
    id: "composition_g_ux_style_matrix",
    label: "Composition G: UX Style Matrix Review",
    description:
      "Full-surface manual review matrix with varied typography, motion, overlays, and callout semantics.",
    requiredAssumptions: [
      "story_id",
      "runtime_policy",
      "persona_policy",
      "chat_mode",
    ],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description:
          "Required for story-linked panel and runtime-coupled block review.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description:
          "Confirm runtime mode used during motion/callout visual review.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description:
          "Confirm participant/persona setup for roster and capability matrix checks.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description:
          "Confirm participant chat rendering for feed-density/highlight evaluation.",
        severity: "warning",
      },
    ],
  },
  composition_h_chaotic_combinatorics: {
    id: "composition_h_chaotic_combinatorics",
    label: "Composition H: Chaotic Combinatorics",
    description:
      "Solo story player + chat with hidden runtime, compact participant picker, and wildly varied content blocks. Tests if motion/color changes are working or just too subtle.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for solo story player and hidden runtime panel.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Must be auto for runtime coupling validation.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description: "Confirm participant picker mode for compact roster.",
        severity: "warning",
      },
    ],
  },
  composition_i_intensity: {
    id: "composition_i_intensity",
    label: "Composition I: Intensity",
    description:
      "A gallery of wonder-blocks pushing every visual boundary — wild animations, extreme typography, daring colors, and philosophical reflections. No panels, just pure block intensity.",
    requiredAssumptions: [],
    checklistItems: [],
  },
}

export const BUILDER_COMPOSITION_TEMPLATES: BuilderCompositionTemplateOption[] =
  Object.values(BUILDER_COMPOSITION_TEMPLATE_SCHEMAS).map(
    ({ id, label, description }) => ({ id, label, description }),
  )

const BUILDER_COMPOSITION_TEMPLATE_BUILDERS: Record<
  BuilderTemplateId,
  TemplateBuilder
> = {
  composition_a_baseline: buildCompositionABaselineTemplate,
  composition_b_runtime_coupled: buildCompositionBRuntimeCoupledTemplate,
  composition_c_visibility_semantics: buildCompositionCVisibilitySemanticsTemplate,
  composition_d_stylized_agent_ops: buildCompositionDStylizedAgentOpsTemplate,
  composition_d1_enhanced_normal: buildCompositionD1EnhancedNormalTemplate,
  composition_d2_enhanced_bonkers: buildCompositionD2EnhancedBonkersTemplate,
  composition_e_tabs_content_studio: buildCompositionETabsContentStudioTemplate,
  composition_f_presentation_passthrough_audit:
    buildCompositionFPresentationPassthroughAuditTemplate,
  composition_g_ux_style_matrix: buildCompositionGUXStyleMatrixTemplate,
  composition_h_chaotic_combinatorics: buildCompositionHChaoticCombinatoricsTemplate,
  composition_i_intensity: buildCompositionIIntensityTemplate,
}

export function createCompositionTemplateFromRegistry(
  templateId: BuilderTemplateId,
  context: TemplateBuilderContext,
): EditableComposition {
  const builder = BUILDER_COMPOSITION_TEMPLATE_BUILDERS[templateId]
  return builder(context)
}
