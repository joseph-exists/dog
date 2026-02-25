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
const RUNTIME_POLICY_VALUES: DemoRuntimePolicy[] = ["auto", "manual", "owner_only"]
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
  { scope: "panel", key: "id", label: "ID", control: "id", required: true, category: "core" },
  { scope: "panel", key: "title", label: "Title", control: "text", category: "core" },
  { scope: "panel", key: "order", label: "Order", control: "number", category: "core" },
  { scope: "panel", key: "default_size", label: "Default Size", control: "number", category: "core" },
  { scope: "panel", key: "min_size", label: "Min Size", control: "number", category: "core" },
  { scope: "panel", key: "max_size", label: "Max Size", control: "number", category: "core" },
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
  { scope: "panel", key: "theme_id", label: "Theme ID", control: "id", category: "theme" },
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
  { scope: "block", key: "id", label: "ID", control: "id", required: true, category: "core" },
  { scope: "block", key: "title", label: "Title", control: "text", category: "core" },
  { scope: "block", key: "order", label: "Order", control: "number", category: "core" },
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
  { scope: "block", key: "theme_id", label: "Theme ID", control: "id", category: "theme" },
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

export type BuilderTemplateConfirmations = Partial<Record<BuilderTemplateAssumptionKey, boolean>>

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
  | "composition_e_tabs_content_studio"
  | "composition_f_presentation_passthrough_audit"
  | "composition_g_ux_style_matrix"

export interface BuilderCompositionTemplateOption {
  id: BuilderTemplateId
  label: string
  description: string
}

export interface BuilderCompositionTemplateSchema extends BuilderCompositionTemplateOption {
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
    description: "Story runtime + chat with a constant instructional content block.",
    requiredAssumptions: ["story_id", "runtime_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Set metadata_json.story_id so story-dependent renderers can resolve content.",
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
        description: "Confirm participant/observer mode for intended QA scenario.",
        severity: "warning",
      },
    ],
  },
  composition_b_runtime_coupled: {
    id: "composition_b_runtime_coupled",
    label: "Composition B: Runtime-Coupled Blocks",
    description: "Adds story metadata, orchestrator state, and contribution feed coverage.",
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
        description: "Confirm persona selection behavior for orchestration visibility.",
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
    description: "Exercises visible, hidden_mounted, and hidden_unmounted block permutations.",
    requiredAssumptions: ["story_id", "runtime_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for storyMetadata visibility validation coverage.",
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
        description: "Confirm mode used while validating mounted/unmounted visibility behavior.",
        severity: "warning",
      },
    ],
  },
  composition_d_stylized_agent_ops: {
    id: "composition_d_stylized_agent_ops",
    label: "Composition D: Stylized Agent Ops",
    description: "Plug-and-play story/chat + participant/tooling coverage with stylized presentation defaults.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for story runtime, story metadata, and narrative chat callouts.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime lifecycle for orchestrator/contribution behavior.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description: "Confirm participant policy for preloaded UserAgentConfig scenarios.",
        severity: "warning",
      },
      {
        id: "fixed_user_persona_id",
        label: "Fixed Persona ID",
        description: "Set when persona policy is fixed persona for deterministic QA playback.",
        severity: "warning",
      },
    ],
  },
  composition_e_tabs_content_studio: {
    id: "composition_e_tabs_content_studio",
    label: "Composition E: Tabs Content Studio",
    description: "Tabs layout with content/browser-style blocks for product curation and LLM prompt walkthroughs.",
    requiredAssumptions: ["story_id", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for story-linked views in tabbed composition flows.",
        severity: "error",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description: "Confirm participant/observer behavior for walkthrough and review sessions.",
        severity: "warning",
      },
    ],
  },
  composition_f_presentation_passthrough_audit: {
    id: "composition_f_presentation_passthrough_audit",
    label: "Composition F: Presentation Passthrough Audit",
    description: "Comprehensive panel/block style audit template with explicit visual expectation text.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for story-linked panels/blocks in this full-surface audit.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime mode before auditing runtime-coupled visuals and motion.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description: "Confirm persona mode for participant and tooling visual checks.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description: "Confirm chat rendering mode for callout/typography checks.",
        severity: "warning",
      },
    ],
  },
  composition_g_ux_style_matrix: {
    id: "composition_g_ux_style_matrix",
    label: "Composition G: UX Style Matrix Review",
    description: "Full-surface manual review matrix with varied typography, motion, overlays, and callout semantics.",
    requiredAssumptions: ["story_id", "runtime_policy", "persona_policy", "chat_mode"],
    checklistItems: [
      {
        id: "story_id",
        label: "Story Attachment",
        description: "Required for story-linked panel and runtime-coupled block review.",
        severity: "error",
      },
      {
        id: "runtime_policy",
        label: "Runtime Policy",
        description: "Confirm runtime mode used during motion/callout visual review.",
        severity: "warning",
      },
      {
        id: "persona_policy",
        label: "Persona Policy",
        description: "Confirm participant/persona setup for roster and capability matrix checks.",
        severity: "warning",
      },
      {
        id: "chat_mode",
        label: "Chat Mode",
        description: "Confirm participant chat rendering for feed-density/highlight evaluation.",
        severity: "warning",
      },
    ],
  },
}

export const BUILDER_COMPOSITION_TEMPLATES: BuilderCompositionTemplateOption[] = Object.values(
  BUILDER_COMPOSITION_TEMPLATE_SCHEMAS,
).map(({ id, label, description }) => ({ id, label, description }))

const TEMPLATE_SETUP_METADATA_KEY = "template_setup"

export const BUILDER_PANEL_KIND_SCHEMAS: Record<ActiveBuilderPanelKind, BuilderPanelKindSchema> = {
  storyRuntime: {
    kind: "storyRuntime",
    displayName: "Story Runtime",
    requiresStoryId: true,
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  chat: {
    kind: "chat",
    displayName: "Chat",
    defaults: { prominence: "auxiliary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  content: {
    kind: "content",
    displayName: "Content",
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  participantPanel: {
    kind: "participantPanel",
    displayName: "Participant Panel",
    defaults: { prominence: "auxiliary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  canvas: {
    kind: "canvas",
    displayName: "Canvas",
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  a2ui: {
    kind: "a2ui",
    displayName: "A2UI",
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  storyEditor: {
    kind: "storyEditor",
    displayName: "Story Editor",
    requiresStoryId: true,
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  storyPlayer: {
    kind: "storyPlayer",
    displayName: "Story Player",
    requiresStoryId: true,
    defaults: { prominence: "primary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  debug: {
    kind: "debug",
    displayName: "Debug",
    defaults: { prominence: "auxiliary", viewport_mode: "panel", options: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
}

export const BUILDER_BLOCK_TYPE_SCHEMAS: Record<ActiveBuilderBlockType, BuilderBlockTypeSchema> = {
  context: {
    type: "context",
    displayName: "Context",
    requiresContentPayload: true,
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  content: {
    type: "content",
    displayName: "Content",
    requiresContentPayload: true,
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  story: {
    type: "story",
    displayName: "Story",
    requiresStoryId: true,
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  storyMetadata: {
    type: "storyMetadata",
    displayName: "Story Metadata",
    requiresStoryId: true,
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  agentRoster: {
    type: "agentRoster",
    displayName: "Agent Roster",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  orchestratorState: {
    type: "orchestratorState",
    displayName: "Orchestrator State",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  toolCapability: {
    type: "toolCapability",
    displayName: "Tool Capability",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  contributionFeed: {
    type: "contributionFeed",
    displayName: "Contribution Feed",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  gitView: {
    type: "gitView",
    displayName: "Git View",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  fileExplorer: {
    type: "fileExplorer",
    displayName: "File Explorer",
    defaults: { region: "top", visibility: "visible", config_json: {}, presentation_json: {}, theme_id: null },
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

export function getBuilderPanelKindSchema(kind: ActiveBuilderPanelKind): BuilderPanelKindSchema {
  return BUILDER_PANEL_KIND_SCHEMAS[kind]
}

export function getBuilderBlockTypeSchema(type: ActiveBuilderBlockType): BuilderBlockTypeSchema {
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

export function getCompositionStoryId(composition: EditableComposition): string | null {
  const metadata = composition.metadata_json
  if (!isObjectRecord(metadata)) return null
  const storyId = metadata.story_id
  return typeof storyId === "string" && storyId.trim().length > 0 ? storyId.trim() : null
}

function isTemplateId(value: unknown): value is BuilderTemplateId {
  return typeof value === "string" && value in BUILDER_COMPOSITION_TEMPLATE_SCHEMAS
}

function parseTemplateConfirmations(value: unknown): BuilderTemplateConfirmations {
  if (!isObjectRecord(value)) return {}
  const parsed: BuilderTemplateConfirmations = {}
  for (const key of Object.keys(value)) {
    if (
      (key === "story_id"
        || key === "runtime_policy"
        || key === "persona_policy"
        || key === "chat_mode"
        || key === "fixed_user_persona_id")
      && typeof value[key] === "boolean"
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
  value: DemoPageCompositionPublic | DemoPageCompositionBase_Input | null | undefined,
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

export function createPanelTemplate(kind: ActiveBuilderPanelKind): EditablePanel {
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

export function createBlockTemplate(type: ActiveBuilderBlockType): EditableBlock {
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
    story_id: "story-placeholder",
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
        value: "### Test Steps\n1. Run story\n2. Send chat message\n3. Verify instructions remain visible.",
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
    story_id: "story-placeholder",
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
    ...(isObjectRecord(composition.metadata_json) ? composition.metadata_json : {}),
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
      page_gradient: "radial-gradient(1200px 500px at 20% 0%, rgba(0, 200, 255, 0.18), rgba(14, 18, 36, 0.9))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 8px 24px rgba(2, 8, 23, 0.35)",
      },
    },
  }
  composition.metadata_json = {
    story_id: "story-placeholder",
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
          panel_header: { css: "linear-gradient(120deg, rgba(32, 196, 255, 0.16), rgba(12, 22, 42, 0.85))" },
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
        value: "### Launch Checklist\n- Verify runtime attach\n- Verify seeded agents\n- Verify stylized chat rendering",
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
      page_gradient: "linear-gradient(165deg, rgba(255, 244, 214, 0.65), rgba(232, 245, 255, 0.72))",
    },
  }
  composition.metadata_json = {
    story_id: "story-placeholder",
    template_id: "composition_e_tabs_content_studio",
    description: "Tabbed demo for content curation, git/file walkthrough, and observer chat.",
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
          value: "## Product Review Script\nUse this tabbed composition for QA/Product walkthroughs.",
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
        value: "### Studio Notes\n- Validate tab flow\n- Validate content readability\n- Validate observer chat",
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
        value: "> Use this slot to stage prompt and rubric snippets during review.",
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
      page_gradient: "linear-gradient(130deg, rgba(255,132,0,0.22), rgba(0,130,255,0.2), rgba(15,23,42,0.95))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 6px 20px rgba(15, 23, 42, 0.28)",
      },
    },
  }
  composition.metadata_json = {
    story_id: "story-placeholder",
    template_id: "composition_f_presentation_passthrough_audit",
    description: "Pass-through audit across all active panel/block surfaces.",
    audit_goal: "motion/typography/backgrounds/effects/overlays passthrough validation",
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
          panel_header: { css: "linear-gradient(100deg, rgba(251,146,60,0.45), rgba(56,189,248,0.28))" },
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
          value: "## Panel Audit Instructions\nLook for bold heading font and gradient panel chrome.",
          metadata: {
            variant: "card",
          },
        },
      },
      presentation_json: {
        overlays: {
          panel_header: { css: "linear-gradient(120deg, rgba(168,85,247,0.35), rgba(6,182,212,0.28))" },
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
          panel_header: { css: "linear-gradient(140deg, rgba(14,165,233,0.35), rgba(20,184,166,0.28))" },
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
          panel_header: { css: "linear-gradient(145deg, rgba(244,114,182,0.3), rgba(129,140,248,0.24))" },
        },
      },
    } as EditablePanel,
    {
      ...createPanelTemplate("storyPlayer"),
      id: "audit-story-player",
      order: 8,
      title: "Audit Panel: Story Player (story-bound surface)",
      prominence: "primary",
      viewport_mode: "panel",
      theme_id: null,
      presentation_json: {
        overlays: {
          panel_header: { css: "linear-gradient(130deg, rgba(16,185,129,0.35), rgba(14,165,233,0.22))" },
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
        backgrounds: { card_pattern: { css: "repeating-linear-gradient(45deg, rgba(255,255,255,0.05) 0 10px, rgba(0,0,0,0.08) 10px 20px)" } },
      },
      content_json: {
        format: "markdown",
        value: "### Expected Visuals\nYou should see bold typography, patterned background, and styled card chrome.",
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
        value: "#### Checkpoint\nIf passthrough works, this card should look distinct from default content cards.",
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
        overlays: { block_header: { css: "linear-gradient(140deg, rgba(253,224,71,0.34), rgba(59,130,246,0.2))" } },
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
        backgrounds: { card_pattern: { css: "linear-gradient(180deg, rgba(148,163,184,0.18), rgba(15,23,42,0.15))" } },
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
        overlays: { block_header: { css: "linear-gradient(125deg, rgba(192,132,252,0.35), rgba(45,212,191,0.2))" } },
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
      title: "Audit Block: Contribution Feed (row highlight + sender/timestamps)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        typography: { size: "sm" },
        effects: { message_row_highlight: { css: "inset 0 0 0 1px rgba(56,189,248,0.28)" } },
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
        overlays: { block_header: { css: "linear-gradient(120deg, rgba(52,211,153,0.25), rgba(59,130,246,0.2))" } },
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
        overlays: { block_header: { css: "linear-gradient(140deg, rgba(244,63,94,0.24), rgba(34,211,238,0.2))" } },
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
      page_gradient: "radial-gradient(1200px 600px at 10% 0%, rgba(34,197,94,0.18), rgba(59,130,246,0.14), rgba(2,6,23,0.92))",
    },
    effects: {
      card_glow: {
        enable: true,
        css: "0 10px 30px rgba(2, 6, 23, 0.32)",
      },
    },
  }
  composition.metadata_json = {
    story_id: "story-placeholder",
    template_id: "composition_g_ux_style_matrix",
    description: "Manual UX style-matrix review across panel/block/capability combinations.",
    audit_goal: "Subjective and objective pass/fail for motion, typography, backgrounds, effects, overlays.",
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
          panel_header: { css: "linear-gradient(90deg, rgba(45,212,191,0.36), rgba(59,130,246,0.24))" },
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
          value: "## UX Review Panel\nThis panel should show a distinct overlay and subtle entry motion.",
          metadata: { variant: "card" },
        },
      },
      presentation_json: {
        overlays: {
          panel_header: { css: "linear-gradient(120deg, rgba(244,114,182,0.3), rgba(34,211,238,0.24))" },
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
          panel_header: { css: "linear-gradient(130deg, rgba(250,204,21,0.25), rgba(251,146,60,0.22))" },
        },
      },
    } as EditablePanel,
    { ...createPanelTemplate("canvas"), id: "matrix-canvas", order: 5, title: "Matrix Panel: Canvas", prominence: "primary", viewport_mode: "panel" } as EditablePanel,
    { ...createPanelTemplate("a2ui"), id: "matrix-a2ui", order: 6, title: "Matrix Panel: A2UI", prominence: "primary", viewport_mode: "panel" } as EditablePanel,
    { ...createPanelTemplate("storyEditor"), id: "matrix-story-editor", order: 7, title: "Matrix Panel: Story Editor", prominence: "primary", viewport_mode: "panel" } as EditablePanel,
    { ...createPanelTemplate("storyPlayer"), id: "matrix-story-player", order: 8, title: "Matrix Panel: Story Player", prominence: "primary", viewport_mode: "panel" } as EditablePanel,
    { ...createPanelTemplate("debug"), id: "matrix-debug", order: 9, title: "Matrix Panel: Debug", prominence: "auxiliary", viewport_mode: "panel", presentation_json: { typography: { size: "xs" } } } as EditablePanel,
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
          card_pattern: { css: "repeating-linear-gradient(135deg, rgba(255,255,255,0.04) 0 14px, rgba(15,23,42,0.12) 14px 28px)" },
        },
      },
      content_json: {
        format: "markdown",
        value: "### Visual Matrix Checklist\nConfirm typography, surface layering, and background pass-through.",
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
        value: "#### Subjective Review Prompt\nDoes this block feel visually distinct and intentional?",
        metadata: { variant: "card" },
      },
    },
    { ...createBlockTemplate("story"), id: "matrix-story", region: "primary", order: 1, title: "Matrix Block: Story", visibility: "visible", theme_id: null },
    {
      ...createBlockTemplate("storyMetadata"),
      id: "matrix-story-meta",
      region: "primary",
      order: 2,
      title: "Matrix Block: Story Metadata",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        backgrounds: { card_pattern: { css: "linear-gradient(180deg, rgba(30,41,59,0.12), rgba(2,6,23,0.2))" } },
      },
      config_json: { show_config_json: true },
    },
    { ...createBlockTemplate("agentRoster"), id: "matrix-roster", region: "primary", order: 3, title: "Matrix Block: Agent Roster", visibility: "visible", theme_id: null, presentation_json: { effects: { card_glow: { enable: true } } } },
    {
      ...createBlockTemplate("orchestratorState"),
      id: "matrix-orchestrator",
      region: "auxiliary",
      order: 1,
      title: "Matrix Block: Orchestrator State (header overlay)",
      visibility: "visible",
      theme_id: null,
      presentation_json: {
        overlays: { block_header: { css: "linear-gradient(110deg, rgba(147,51,234,0.35), rgba(14,165,233,0.22))" } },
      },
      config_json: { show_agent_list: true, only_active_agents: false, show_config_json: true },
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
        effects: { message_row_highlight: { css: "inset 0 0 0 1px rgba(56,189,248,0.24), 0 3px 10px rgba(2,6,23,0.28)" } },
      },
      config_json: {
        max_items: 14,
        include_internal: true,
        show_sender_type: true,
        show_timestamps: true,
        show_config_json: true,
      },
    },
    { ...createBlockTemplate("gitView"), id: "matrix-git", region: "footer", order: 1, title: "Matrix Block: Git View", visibility: "visible", theme_id: null, config_json: { mode: "summary" } },
    { ...createBlockTemplate("fileExplorer"), id: "matrix-files", region: "footer", order: 2, title: "Matrix Block: File Explorer", visibility: "visible", theme_id: null, config_json: { root_path: "/workspace" } },
  ]

  return composition
}

export function createCompositionTemplate(templateId: BuilderTemplateId): EditableComposition {
  switch (templateId) {
    case "composition_a_baseline":
      return createCompositionABaselineTemplate()
    case "composition_b_runtime_coupled":
      return createCompositionBRuntimeCoupledTemplate()
    case "composition_c_visibility_semantics":
      return createCompositionCVisibilitySemanticsTemplate()
    case "composition_d_stylized_agent_ops":
      return createCompositionDStylizedAgentOpsTemplate()
    case "composition_e_tabs_content_studio":
      return createCompositionETabsContentStudioTemplate()
    case "composition_f_presentation_passthrough_audit":
      return createCompositionFPresentationPassthroughAuditTemplate()
    case "composition_g_ux_style_matrix":
      return createCompositionGUXStyleMatrixTemplate()
    default: {
      const unreachableTemplateId: never = templateId
      throw new Error(`Unsupported composition template: ${String(unreachableTemplateId)}`)
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
    return typeof composition.fixed_user_persona_id === "string"
      && composition.fixed_user_persona_id.trim().length > 0
  }
  return Boolean(confirmations[itemId])
}

export function resolveTemplateChecklistStatus(params: {
  templateId: BuilderTemplateId
  composition: EditableComposition
  semanticIssues: BuilderValidationIssue[]
  confirmations?: Partial<Record<BuilderTemplateAssumptionKey, boolean>>
}): BuilderTemplateChecklistStatus {
  const {
    templateId,
    composition,
    semanticIssues,
    confirmations = {},
  } = params
  const schema = getBuilderCompositionTemplateSchema(templateId)

  const items = schema.checklistItems.map((item) => {
    const relatedIssues = semanticIssues.filter((issue) => {
      if (item.id === "story_id") return issue.code === "story_id_required"
      return false
    })
    return {
      ...item,
      resolved: getChecklistItemResolvedState(item.id, composition, confirmations),
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

  const pageViewportPanels = panels.filter((panel) => panel.viewport_mode === "page")
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
      block.visibility
      && !BUILDER_BLOCK_VISIBILITY.includes(block.visibility as BuilderBlockVisibility)
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

    if (type && CONTENT_CAPABLE_BLOCK_TYPES.has(type) && !hasContentPayload(block)) {
      issues.push({
        code: "content_payload_missing",
        severity: "warning",
        message: `Block type "${type}" is missing a content_json payload with format/value.`,
        path: `blocks[${index}].content_json`,
      })
    }
  }

  return issues
}
