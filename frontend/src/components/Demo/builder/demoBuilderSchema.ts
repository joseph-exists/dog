import type {
  DemoChatMode,
  DemoLayoutMode,
  DemoPageCompositionBase_Input,
  DemoPageCompositionPublic,
  DemoPersonaPolicy,
  DemoRuntimePolicy,
} from "@/client/types.gen"

// ============================================================================
// Builder Schema: Canonical Authoring Layer
// ============================================================================
// This module is intentionally a frontend authoring/view-model layer on top of
// generated API contracts. Persisted payloads still use DemoPageCompositionBase_Input.
//
// Goals:
// 1. Keep builder defaults consistent and centralized.
// 2. Restrict authoring to active panel/block kinds.
// 3. Provide semantic validation rules for guided UX.
// 4. Prepare for future capability/plugin descriptor expansion.
//
// NOTE: We avoid importing runtime renderer code here to keep schema validation
// deterministic and side-effect free.

export type EditableComposition = DemoPageCompositionBase_Input
export type EditablePanel = NonNullable<EditableComposition["panels"]>[number]
export type EditableBlock = NonNullable<EditableComposition["blocks"]>[number]

export type BuilderPanelProminence = "primary" | "auxiliary"
export type BuilderBlockRegion = "top" | "primary" | "auxiliary" | "footer"
export type BuilderBlockVisibility =
  | "visible"
  | "hidden_unmounted"
  | "hidden_mounted"

export type BuilderFieldControl =
  | "text"
  | "number"
  | "boolean"
  | "enum"
  | "json"
  | "id"

export interface BuilderFieldSpec {
  key: string
  label: string
  control: BuilderFieldControl
  description?: string
  required?: boolean
  enumValues?: readonly string[]
  placeholder?: string
  category?: "core" | "theme" | "advanced"
}

export interface BuilderTopLevelFieldSpec extends BuilderFieldSpec {
  scope: "composition"
}

export interface BuilderPanelFieldSpec extends BuilderFieldSpec {
  scope: "panel"
}

export interface BuilderBlockFieldSpec extends BuilderFieldSpec {
  scope: "block"
}

// Active authoring domains. Compatibility/deferred kinds are intentionally
// excluded from guided builder controls.
export const ACTIVE_BUILDER_PANEL_KINDS = [
  "storyRuntime",
  "chat",
  "content",
  "participantPanel",
  "canvas",
  "a2ui",
  "storyEditor",
  "storyPlayer",
  "debug",
] as const

export const ACTIVE_BUILDER_BLOCK_TYPES = [
  "context",
  "content",
  "story",
  "storyMetadata",
  "agentRoster",
  "orchestratorState",
  "toolCapability",
  "contributionFeed",
  "gitView",
  "fileExplorer",
] as const

export type ActiveBuilderPanelKind = (typeof ACTIVE_BUILDER_PANEL_KINDS)[number]
export type ActiveBuilderBlockType = (typeof ACTIVE_BUILDER_BLOCK_TYPES)[number]

export const BUILDER_BLOCK_REGIONS: BuilderBlockRegion[] = [
  "top",
  "primary",
  "auxiliary",
  "footer",
]

export const BUILDER_BLOCK_VISIBILITY: BuilderBlockVisibility[] = [
  "visible",
  "hidden_unmounted",
  "hidden_mounted",
]

const LAYOUT_MODE_VALUES: DemoLayoutMode[] = ["panels", "tabs"]
const RUNTIME_POLICY_VALUES: DemoRuntimePolicy[] = [
  "auto",
  "manual",
  "owner_only",
]
const PERSONA_POLICY_VALUES: DemoPersonaPolicy[] = [
  "first_available",
  "fixed_user_persona",
  "manual_prompt",
]
const CHAT_MODE_VALUES: DemoChatMode[] = ["participant", "observer"]

export const BUILDER_COMPOSITION_FIELD_SPECS: BuilderTopLevelFieldSpec[] = [
  {
    scope: "composition",
    key: "layout_mode",
    label: "Layout Mode",
    control: "enum",
    enumValues: LAYOUT_MODE_VALUES,
    category: "core",
  },
  {
    scope: "composition",
    key: "runtime_policy",
    label: "Runtime Policy",
    control: "enum",
    enumValues: RUNTIME_POLICY_VALUES,
    category: "core",
  },
  {
    scope: "composition",
    key: "persona_policy",
    label: "Persona Policy",
    control: "enum",
    enumValues: PERSONA_POLICY_VALUES,
    category: "core",
  },
  {
    scope: "composition",
    key: "chat_mode",
    label: "Chat Mode",
    control: "enum",
    enumValues: CHAT_MODE_VALUES,
    category: "core",
  },
  {
    scope: "composition",
    key: "fixed_user_persona_id",
    label: "Fixed Persona ID",
    control: "id",
    category: "advanced",
  },
  {
    scope: "composition",
    key: "page_theme_id",
    label: "Page Theme ID",
    control: "id",
    category: "theme",
  },
  {
    scope: "composition",
    key: "cards_theme_id",
    label: "Cards Theme ID",
    control: "id",
    category: "theme",
  },
  {
    scope: "composition",
    key: "presentation_json",
    label: "Presentation JSON",
    control: "json",
    category: "theme",
  },
  {
    scope: "composition",
    key: "metadata_json",
    label: "Metadata JSON",
    control: "json",
    category: "advanced",
  },
]

const PANEL_COMMON_FIELD_SPECS: BuilderPanelFieldSpec[] = [
  {
    scope: "panel",
    key: "kind",
    label: "Kind",
    control: "enum",
    enumValues: ACTIVE_BUILDER_PANEL_KINDS,
    required: true,
    category: "core",
  },
  {
    scope: "panel",
    key: "id",
    label: "ID",
    control: "id",
    required: true,
    category: "core",
  },
  {
    scope: "panel",
    key: "title",
    label: "Title",
    control: "text",
    category: "core",
  },
  {
    scope: "panel",
    key: "order",
    label: "Order",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "default_size",
    label: "Default Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "min_size",
    label: "Min Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "max_size",
    label: "Max Size",
    control: "number",
    category: "core",
  },
  {
    scope: "panel",
    key: "prominence",
    label: "Prominence",
    control: "enum",
    enumValues: ["primary", "auxiliary"],
    category: "core",
  },
  {
    scope: "panel",
    key: "viewport_mode",
    label: "Viewport Mode",
    control: "enum",
    enumValues: ["panel", "page"],
    category: "core",
  },
  {
    scope: "panel",
    key: "theme_id",
    label: "Theme ID",
    control: "id",
    category: "theme",
  },
  {
    scope: "panel",
    key: "presentation_json",
    label: "Presentation JSON",
    control: "json",
    category: "theme",
  },
  {
    scope: "panel",
    key: "options",
    label: "Options JSON",
    control: "json",
    category: "advanced",
  },
]

const BLOCK_COMMON_FIELD_SPECS: BuilderBlockFieldSpec[] = [
  {
    scope: "block",
    key: "type",
    label: "Type",
    control: "enum",
    enumValues: ACTIVE_BUILDER_BLOCK_TYPES,
    required: true,
    category: "core",
  },
  {
    scope: "block",
    key: "id",
    label: "ID",
    control: "id",
    required: true,
    category: "core",
  },
  {
    scope: "block",
    key: "title",
    label: "Title",
    control: "text",
    category: "core",
  },
  {
    scope: "block",
    key: "order",
    label: "Order",
    control: "number",
    category: "core",
  },
  {
    scope: "block",
    key: "region",
    label: "Region",
    control: "enum",
    enumValues: BUILDER_BLOCK_REGIONS,
    category: "core",
  },
  {
    scope: "block",
    key: "visibility",
    label: "Visibility",
    control: "enum",
    enumValues: BUILDER_BLOCK_VISIBILITY,
    category: "core",
  },
  {
    scope: "block",
    key: "theme_id",
    label: "Theme ID",
    control: "id",
    category: "theme",
  },
  {
    scope: "block",
    key: "presentation_json",
    label: "Presentation JSON",
    control: "json",
    category: "theme",
  },
  {
    scope: "block",
    key: "config_json",
    label: "Config JSON",
    control: "json",
    category: "advanced",
  },
  {
    scope: "block",
    key: "content_json",
    label: "Content JSON",
    control: "json",
    category: "advanced",
  },
]

export interface BuilderPanelKindSchema {
  kind: ActiveBuilderPanelKind
  displayName: string
  defaults: Partial<EditablePanel>
  fieldSpecs: BuilderPanelFieldSpec[]
  requiresStoryId?: boolean
}

export interface BuilderBlockTypeSchema {
  type: ActiveBuilderBlockType
  displayName: string
  defaults: Partial<EditableBlock>
  fieldSpecs: BuilderBlockFieldSpec[]
  requiresStoryId?: boolean
  requiresContentPayload?: boolean
}

export type BuilderTemplateAssumptionKey =
  | "story_id"
  | "runtime_policy"
  | "persona_policy"
  | "chat_mode"
  | "fixed_user_persona_id"

export interface BuilderTemplateChecklistItemDefinition {
  id: BuilderTemplateAssumptionKey
  label: string
  description: string
  severity: "warning" | "error"
}

export type BuilderTemplateConfirmations = Partial<
  Record<BuilderTemplateAssumptionKey, boolean>
>

export interface BuilderTemplateSetupState {
  templateId: BuilderTemplateId
  dismissed: boolean
  confirmations: BuilderTemplateConfirmations
}

export type BuilderTemplateId =
  | "composition_a_baseline"
  | "composition_b_runtime_coupled"
  | "composition_c_visibility_semantics"
  | "composition_d_stylized_agent_ops"
  | "composition_d1_enhanced_normal"
  | "composition_d2_enhanced_bonkers"
  | "composition_e_tabs_content_studio"
  | "composition_f_presentation_passthrough_audit"
  | "composition_g_ux_style_matrix"
  | "composition_h_chaotic_combinatorics"
  | "composition_i_intensity"

export interface BuilderCompositionTemplateOption {
  id: BuilderTemplateId
  label: string
  description: string
}

export interface BuilderCompositionTemplateSchema
  extends BuilderCompositionTemplateOption {
  requiredAssumptions: BuilderTemplateAssumptionKey[]
  checklistItems: BuilderTemplateChecklistItemDefinition[]
}

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

const TEMPLATE_SETUP_METADATA_KEY = "template_setup"

export const BUILDER_PANEL_KIND_SCHEMAS: Record<
  ActiveBuilderPanelKind,
  BuilderPanelKindSchema
> = {
  storyRuntime: {
    kind: "storyRuntime",
    displayName: "Story Runtime",
    requiresStoryId: true,
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  chat: {
    kind: "chat",
    displayName: "Chat",
    defaults: {
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  content: {
    kind: "content",
    displayName: "Content",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  participantPanel: {
    kind: "participantPanel",
    displayName: "Participant Panel",
    defaults: {
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  canvas: {
    kind: "canvas",
    displayName: "Canvas",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  a2ui: {
    kind: "a2ui",
    displayName: "A2UI",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  storyEditor: {
    kind: "storyEditor",
    displayName: "Story Editor",
    requiresStoryId: true,
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  storyPlayer: {
    kind: "storyPlayer",
    displayName: "Solo Story Player",
    requiresStoryId: true,
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  debug: {
    kind: "debug",
    displayName: "Debug",
    defaults: {
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
}

export const BUILDER_BLOCK_TYPE_SCHEMAS: Record<
  ActiveBuilderBlockType,
  BuilderBlockTypeSchema
> = {
  context: {
    type: "context",
    displayName: "Context",
    requiresContentPayload: true,
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  content: {
    type: "content",
    displayName: "Content",
    requiresContentPayload: true,
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  story: {
    type: "story",
    displayName: "Story",
    requiresStoryId: true,
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  storyMetadata: {
    type: "storyMetadata",
    displayName: "Story Metadata",
    requiresStoryId: true,
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  agentRoster: {
    type: "agentRoster",
    displayName: "Agent Roster",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  orchestratorState: {
    type: "orchestratorState",
    displayName: "Orchestrator State",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  toolCapability: {
    type: "toolCapability",
    displayName: "Tool Capability",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  contributionFeed: {
    type: "contributionFeed",
    displayName: "Contribution Feed",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  gitView: {
    type: "gitView",
    displayName: "Git View",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  fileExplorer: {
    type: "fileExplorer",
    displayName: "File Explorer",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {},
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
}

// Kinds/types with runtime/story coupling requirements derived from the schema registry.
const STORY_DEPENDENT_PANEL_KINDS = new Set<ActiveBuilderPanelKind>(
  Object.values(BUILDER_PANEL_KIND_SCHEMAS)
    .filter((schema) => schema.requiresStoryId)
    .map((schema) => schema.kind),
)
const STORY_DEPENDENT_BLOCK_TYPES = new Set<ActiveBuilderBlockType>(
  Object.values(BUILDER_BLOCK_TYPE_SCHEMAS)
    .filter((schema) => schema.requiresStoryId)
    .map((schema) => schema.type),
)
const CONTENT_CAPABLE_BLOCK_TYPES = new Set<ActiveBuilderBlockType>(
  Object.values(BUILDER_BLOCK_TYPE_SCHEMAS)
    .filter((schema) => schema.requiresContentPayload)
    .map((schema) => schema.type),
)

export function getBuilderPanelKindSchema(
  kind: ActiveBuilderPanelKind,
): BuilderPanelKindSchema {
  return BUILDER_PANEL_KIND_SCHEMAS[kind]
}

export function getBuilderBlockTypeSchema(
  type: ActiveBuilderBlockType,
): BuilderBlockTypeSchema {
  return BUILDER_BLOCK_TYPE_SCHEMAS[type]
}

export function getBuilderCompositionTemplateSchema(
  templateId: BuilderTemplateId,
): BuilderCompositionTemplateSchema {
  return BUILDER_COMPOSITION_TEMPLATE_SCHEMAS[templateId]
}

export function getBuilderCompositionFieldSpec(
  key: string,
): BuilderTopLevelFieldSpec | undefined {
  return BUILDER_COMPOSITION_FIELD_SPECS.find((field) => field.key === key)
}

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

function isUuidString(value: unknown): value is string {
  return typeof value === "string" && UUID_PATTERN.test(value.trim())
}

export function getCompositionStoryId(
  composition: EditableComposition,
): string | null {
  const metadata = composition.metadata_json
  if (!isObjectRecord(metadata)) return null
  const storyId = metadata.story_id
  return isUuidString(storyId) ? storyId.trim() : null
}

function isTemplateId(value: unknown): value is BuilderTemplateId {
  return (
    typeof value === "string" && value in BUILDER_COMPOSITION_TEMPLATE_SCHEMAS
  )
}

function parseTemplateConfirmations(
  value: unknown,
): BuilderTemplateConfirmations {
  if (!isObjectRecord(value)) return {}
  const parsed: BuilderTemplateConfirmations = {}
  for (const key of Object.keys(value)) {
    if (
      (key === "story_id" ||
        key === "runtime_policy" ||
        key === "persona_policy" ||
        key === "chat_mode" ||
        key === "fixed_user_persona_id") &&
      typeof value[key] === "boolean"
    ) {
      parsed[key] = value[key]
    }
  }
  return parsed
}

export function getTemplateSetupState(
  composition: EditableComposition,
): BuilderTemplateSetupState | null {
  const metadata = composition.metadata_json
  if (!isObjectRecord(metadata)) return null
  const rawSetup = metadata[TEMPLATE_SETUP_METADATA_KEY]
  if (!isObjectRecord(rawSetup)) return null
  const rawTemplateId = rawSetup.template_id
  if (!isTemplateId(rawTemplateId)) return null
  return {
    templateId: rawTemplateId,
    dismissed: Boolean(rawSetup.dismissed),
    confirmations: parseTemplateConfirmations(rawSetup.confirmations),
  }
}

export function withTemplateSetupState(
  composition: EditableComposition,
  setupState: BuilderTemplateSetupState | null,
): EditableComposition {
  const metadata = isObjectRecord(composition.metadata_json)
    ? { ...composition.metadata_json }
    : {}
  if (!setupState) {
    delete metadata[TEMPLATE_SETUP_METADATA_KEY]
  } else {
    metadata[TEMPLATE_SETUP_METADATA_KEY] = {
      template_id: setupState.templateId,
      dismissed: setupState.dismissed,
      confirmations: setupState.confirmations,
    }
  }
  return {
    ...composition,
    metadata_json: metadata,
  }
}

export function createEmptyComposition(): EditableComposition {
  return {
    schema_version: 1,
    layout_mode: "panels",
    runtime_policy: "auto",
    persona_policy: "first_available",
    chat_mode: "participant",
    fixed_user_persona_id: null,
    page_theme_id: null,
    cards_theme_id: null,
    presentation_json: {},
    metadata_json: {},
    panels: [],
    blocks: [],
  }
}

export function normalizeComposition(
  value:
    | DemoPageCompositionPublic
    | DemoPageCompositionBase_Input
    | null
    | undefined,
): EditableComposition {
  // Deep clone so edits never mutate React Query cache references.
  const cloned = value ? JSON.parse(JSON.stringify(value)) : {}

  return {
    ...createEmptyComposition(),
    ...(cloned as EditableComposition),
    panels: Array.isArray((cloned as EditableComposition).panels)
      ? (cloned as EditableComposition).panels
      : [],
    blocks: Array.isArray((cloned as EditableComposition).blocks)
      ? (cloned as EditableComposition).blocks
      : [],
  }
}

export function createPanelTemplate(
  kind: ActiveBuilderPanelKind,
): EditablePanel {
  const schema = getBuilderPanelKindSchema(kind)
  const template = {
    id: `${kind}-${Date.now()}`,
    kind,
    order: 1,
    title: kind,
    ...schema.defaults,
  }
  return template as EditablePanel
}

export function createBlockTemplate(
  type: ActiveBuilderBlockType,
): EditableBlock {
  const schema = getBuilderBlockTypeSchema(type)
  const template = {
    id: `${type}-${Date.now()}`,
    type,
    order: 1,
    title: type,
    ...schema.defaults,
  }
  return template as EditableBlock
}

function createCompositionABaselineTemplate(): EditableComposition {
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
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("content"),
      id: "instructions-top",
      region: "top",
      order: 1,
      title: "Instructions",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Test Steps\n1. Run story\n2. Send chat message\n3. Verify instructions remain visible.",
        metadata: {
          variant: "card",
        },
      },
    },
  ]
  return composition
}

function createCompositionBRuntimeCoupledTemplate(): EditableComposition {
  const composition = createEmptyComposition()
  composition.layout_mode = "panels"
  composition.runtime_policy = "auto"
  composition.persona_policy = "first_available"
  composition.chat_mode = "participant"
  composition.metadata_json = {
    template_id: "composition_b_runtime_coupled",
  }
  composition.panels = [
    {
      ...createPanelTemplate("storyRuntime"),
      id: "story-runtime-primary",
      order: 1,
      title: "Story Runtime",
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        send_runtime_events_to_chat: true,
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("chat"),
      id: "chat-aux",
      order: 2,
      title: "Room Chat",
      prominence: "auxiliary",
      viewport_mode: "panel",
      options: {
        mode: "participant",
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("participantPanel"),
      id: "participants-aux",
      order: 3,
      title: "Participants",
      prominence: "auxiliary",
      viewport_mode: "panel",
    } as EditablePanel,
  ]
  composition.blocks = [
    {
      ...createBlockTemplate("storyMetadata"),
      id: "story-meta-top",
      region: "top",
      order: 1,
      title: "Story Metadata",
      visibility: "visible",
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-primary",
      region: "primary",
      order: 1,
      title: "Orchestrator State",
      visibility: "visible",
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-aux",
      region: "auxiliary",
      order: 1,
      title: "Contribution Feed",
      visibility: "visible",
      config_json: {
        max_items: 8,
        include_internal: true,
        show_sender_type: true,
      },
    },
  ]
  return composition
}

function createCompositionCVisibilitySemanticsTemplate(): EditableComposition {
  const composition = createCompositionBRuntimeCoupledTemplate()
  composition.metadata_json = {
    ...(isObjectRecord(composition.metadata_json)
      ? composition.metadata_json
      : {}),
    template_id: "composition_c_visibility_semantics",
  }
  composition.blocks = [
    {
      ...createBlockTemplate("storyMetadata"),
      id: "story-meta-visible",
      region: "top",
      order: 1,
      title: "Story Metadata (Visible)",
      visibility: "visible",
    },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "orchestrator-mounted",
      region: "primary",
      order: 1,
      title: "Orchestrator (Hidden Mounted)",
      visibility: "hidden_mounted",
      config_json: {
        show_agent_list: true,
        only_active_agents: false,
      },
    },
    {
      ...createBlockTemplate("contributionFeed"),
      id: "feed-unmounted",
      region: "auxiliary",
      order: 1,
      title: "Contribution Feed (Hidden Unmounted)",
      visibility: "hidden_unmounted",
      config_json: {
        max_items: 8,
        include_internal: true,
        show_sender_type: true,
      },
    },
  ]
  return composition
}

function createCompositionDStylizedAgentOpsTemplate(): EditableComposition {
  const composition = createCompositionBRuntimeCoupledTemplate()
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
      id: "mission-brief-top",
      region: "top",
      order: 1,
      title: "Mission Brief",
      visibility: "visible",
      content_json: {
        format: "markdown",
        value:
          "### Launch Checklist\n- Verify runtime attach\n- Verify seeded agents\n- Verify stylized chat rendering",
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

function createCompositionD1EnhancedNormalTemplate(): EditableComposition {
  const composition = createCompositionBRuntimeCoupledTemplate()
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

function createCompositionD2EnhancedBonkersTemplate(): EditableComposition {
  const composition = createCompositionBRuntimeCoupledTemplate()
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

function createCompositionHChaoticCombinatoricsTemplate(): EditableComposition {
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

function createCompositionETabsContentStudioTemplate(): EditableComposition {
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

function createCompositionFPresentationPassthroughAuditTemplate(): EditableComposition {
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
      ...createPanelTemplate("participantPanel"),
      id: "audit-participants",
      order: 4,
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
      order: 5,
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
      order: 6,
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
      order: 7,
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
      order: 8,
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
      order: 9,
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

function createCompositionGUXStyleMatrixTemplate(): EditableComposition {
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
      ...createPanelTemplate("participantPanel"),
      id: "matrix-participants",
      order: 4,
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
      order: 5,
      title: "Matrix Panel: Canvas",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("a2ui"),
      id: "matrix-a2ui",
      order: 6,
      title: "Matrix Panel: A2UI",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("storyEditor"),
      id: "matrix-story-editor",
      order: 7,
      title: "Matrix Panel: Story Editor",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("storyPlayer"),
      id: "matrix-story-player",
      order: 8,
      title: "Matrix Panel: Solo Story Player",
      prominence: "primary",
      viewport_mode: "panel",
    } as EditablePanel,
    {
      ...createPanelTemplate("debug"),
      id: "matrix-debug",
      order: 9,
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
      config_json: { mode: "summary" },
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

function createCompositionIIntensityTemplate(): EditableComposition {
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
          "## Live the Questions\n\n> *\"Be patient toward all that is unsolved in your heart and try to love the questions themselves, like locked rooms and like books that are now written in a very foreign tongue.\"*\n\n— Letters to a Young Poet, 1903",
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
          "## One Wild and Precious Life\n\n> *\"Tell me, what is it you plan to do with your one wild and precious life?\"*\n\nThe question that refuses to let us sleep.",
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
          "### The Shadow Work\n\n> *\"Until you make the unconscious conscious, it will direct your life and you will call it fate.\"*\n\nWhat we resist persists. What we embrace transforms.",
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
          "## The Field Beyond\n\n> *\"Out beyond ideas of wrongdoing and rightdoing, there is a field. I'll meet you there.*\n>\n> *When the soul lies down in that grass, the world is too full to talk about.\"*\n\nThe field is always there. We just forget how to see it.",
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
          "## God Is Change\n\n> *\"All that you touch, you Change.*\n> *All that you Change, Changes you.*\n> *The only lasting truth is Change.*\n> *God is Change.\"*\n\nThe shape of God is in the shaping.",
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

export function createCompositionTemplate(
  templateId: BuilderTemplateId,
): EditableComposition {
  switch (templateId) {
    case "composition_a_baseline":
      return createCompositionABaselineTemplate()
    case "composition_b_runtime_coupled":
      return createCompositionBRuntimeCoupledTemplate()
    case "composition_c_visibility_semantics":
      return createCompositionCVisibilitySemanticsTemplate()
    case "composition_d_stylized_agent_ops":
      return createCompositionDStylizedAgentOpsTemplate()
    case "composition_d1_enhanced_normal":
      return createCompositionD1EnhancedNormalTemplate()
    case "composition_d2_enhanced_bonkers":
      return createCompositionD2EnhancedBonkersTemplate()
    case "composition_e_tabs_content_studio":
      return createCompositionETabsContentStudioTemplate()
    case "composition_f_presentation_passthrough_audit":
      return createCompositionFPresentationPassthroughAuditTemplate()
    case "composition_g_ux_style_matrix":
      return createCompositionGUXStyleMatrixTemplate()
    case "composition_h_chaotic_combinatorics":
      return createCompositionHChaoticCombinatoricsTemplate()
    case "composition_i_intensity":
      return createCompositionIIntensityTemplate()
    default: {
      const unreachableTemplateId: never = templateId
      throw new Error(
        `Unsupported composition template: ${String(unreachableTemplateId)}`,
      )
    }
  }
}

export interface BuilderTemplateChecklistItemStatus {
  id: BuilderTemplateAssumptionKey
  label: string
  description: string
  severity: "warning" | "error"
  resolved: boolean
  relatedIssues: BuilderValidationIssue[]
}

export interface BuilderTemplateChecklistStatus {
  templateId: BuilderTemplateId
  items: BuilderTemplateChecklistItemStatus[]
  resolvedCount: number
  totalCount: number
}

function getChecklistItemResolvedState(
  itemId: BuilderTemplateAssumptionKey,
  composition: EditableComposition,
  confirmations: Partial<Record<BuilderTemplateAssumptionKey, boolean>>,
): boolean {
  if (itemId === "story_id") {
    return Boolean(getCompositionStoryId(composition))
  }
  if (itemId === "fixed_user_persona_id") {
    if (composition.persona_policy !== "fixed_user_persona") return true
    return (
      typeof composition.fixed_user_persona_id === "string" &&
      composition.fixed_user_persona_id.trim().length > 0
    )
  }
  return Boolean(confirmations[itemId])
}

export function resolveTemplateChecklistStatus(params: {
  templateId: BuilderTemplateId
  composition: EditableComposition
  semanticIssues: BuilderValidationIssue[]
  confirmations?: Partial<Record<BuilderTemplateAssumptionKey, boolean>>
}): BuilderTemplateChecklistStatus {
  const { templateId, composition, semanticIssues, confirmations = {} } = params
  const schema = getBuilderCompositionTemplateSchema(templateId)

  const items = schema.checklistItems.map((item) => {
    const relatedIssues = semanticIssues.filter((issue) => {
      if (item.id === "story_id") return issue.code === "story_id_required"
      return false
    })
    return {
      ...item,
      resolved: getChecklistItemResolvedState(
        item.id,
        composition,
        confirmations,
      ),
      relatedIssues,
    }
  })

  const resolvedCount = items.filter((item) => item.resolved).length
  return {
    templateId,
    items,
    resolvedCount,
    totalCount: items.length,
  }
}

export interface BuilderValidationIssue {
  code:
    | "story_id_required"
    | "too_many_page_viewports"
    | "unsupported_panel_kind"
    | "unsupported_block_type"
    | "invalid_block_visibility"
    | "content_payload_missing"
    | "story_player_local_only"
    | "capability_validation"
  severity: "error" | "warning"
  message: string
  path?: string
}

function hasStoryId(composition: EditableComposition): boolean {
  return Boolean(getCompositionStoryId(composition))
}

function hasContentPayload(block: EditableBlock): boolean {
  const content = (block as { content_json?: unknown }).content_json
  if (!isObjectRecord(content)) return false
  return typeof content.format === "string" && "value" in content
}

export function validateCompositionSemantics(
  composition: EditableComposition,
): BuilderValidationIssue[] {
  const issues: BuilderValidationIssue[] = []
  const panels = composition.panels ?? []
  const blocks = composition.blocks ?? []
  const storyIdPresent = hasStoryId(composition)
  const hasStoryPlayer = panels.some((panel) => panel.kind === "storyPlayer")
  const hasStoryRuntime = panels.some((panel) => panel.kind === "storyRuntime")

  const pageViewportPanels = panels.filter(
    (panel) => panel.viewport_mode === "page",
  )
  if (pageViewportPanels.length > 1) {
    issues.push({
      code: "too_many_page_viewports",
      severity: "error",
      message: "At most one panel can use viewport_mode='page'.",
      path: "panels",
    })
  }

  for (const [index, panel] of panels.entries()) {
    const kind = panel.kind as ActiveBuilderPanelKind | undefined
    if (kind && !ACTIVE_BUILDER_PANEL_KINDS.includes(kind)) {
      issues.push({
        code: "unsupported_panel_kind",
        severity: "warning",
        message: `Panel kind "${panel.kind}" is outside active builder support.`,
        path: `panels[${index}].kind`,
      })
      continue
    }

    if (kind && STORY_DEPENDENT_PANEL_KINDS.has(kind) && !storyIdPresent) {
      issues.push({
        code: "story_id_required",
        severity: "error",
        message: `Panel kind "${kind}" requires metadata_json.story_id.`,
        path: `panels[${index}]`,
      })
    }
  }

  for (const [index, block] of blocks.entries()) {
    const type = block.type as ActiveBuilderBlockType | undefined
    if (type && !ACTIVE_BUILDER_BLOCK_TYPES.includes(type)) {
      issues.push({
        code: "unsupported_block_type",
        severity: "warning",
        message: `Block type "${block.type}" is outside active builder support.`,
        path: `blocks[${index}].type`,
      })
      continue
    }

    if (
      block.visibility &&
      !BUILDER_BLOCK_VISIBILITY.includes(
        block.visibility as BuilderBlockVisibility,
      )
    ) {
      issues.push({
        code: "invalid_block_visibility",
        severity: "error",
        message: `Block visibility "${String(block.visibility)}" is invalid.`,
        path: `blocks[${index}].visibility`,
      })
    }

    if (type && STORY_DEPENDENT_BLOCK_TYPES.has(type) && !storyIdPresent) {
      issues.push({
        code: "story_id_required",
        severity: "error",
        message: `Block type "${type}" requires metadata_json.story_id.`,
        path: `blocks[${index}]`,
      })
    }

    if (
      type &&
      CONTENT_CAPABLE_BLOCK_TYPES.has(type) &&
      !hasContentPayload(block)
    ) {
      issues.push({
        code: "content_payload_missing",
        severity: "warning",
        message: `Block type "${type}" is missing a content_json payload with format/value.`,
        path: `blocks[${index}].content_json`,
      })
    }
  }

  if (hasStoryPlayer) {
    issues.push({
      code: "story_player_local_only",
      severity: "warning",
      message: hasStoryRuntime
        ? "storyPlayer is local-only. It does not share state with storyRuntime even when both panels are present."
        : "storyPlayer is local-only. It does not read from or write to shared room runtime.",
      path: "panels",
    })
  }

  return issues
}
