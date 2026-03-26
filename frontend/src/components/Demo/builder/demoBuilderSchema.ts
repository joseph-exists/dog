import type {
  DemoChatMode,
  DemoLayoutMode,
  DemoPageCompositionBase_Input,
  DemoPageCompositionPublic,
  DemoPersonaPolicy,
  DemoRuntimePolicy,
} from "@/client/types.gen"
import {
  BUILDER_COMPOSITION_TEMPLATE_SCHEMAS,
  createCompositionTemplateFromRegistry,
} from "@/components/Demo/builder/templates/registry"
import type {
  BuilderCompositionTemplateSchema,
  BuilderTemplateAssumptionKey,
  BuilderTemplateConfirmations,
  BuilderTemplateId,
} from "@/components/Demo/builder/templates/types"
import { createDefaultGitViewConfig } from "@/components/Demo/gitViewConfig"
import { createDefaultLiveRepoExplorerConfig } from "@/components/Demo/liveRepoExplorerConfig"
import { createDefaultLiveRepoFileViewerConfig } from "@/components/Demo/liveRepoFileViewerConfig"

export {
  BUILDER_COMPOSITION_TEMPLATE_SCHEMAS,
  BUILDER_COMPOSITION_TEMPLATES,
} from "@/components/Demo/builder/templates/registry"
export type {
  BuilderCompositionTemplateOption,
  BuilderCompositionTemplateSchema,
  BuilderTemplateAssumptionKey,
  BuilderTemplateChecklistItemDefinition,
  BuilderTemplateConfirmations,
  BuilderTemplateId,
} from "@/components/Demo/builder/templates/types"

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
  "gitView",
  "fileExplorer",
  "fileViewer",
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
  "fileViewer",
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

export interface BuilderTemplateSetupState {
  templateId: BuilderTemplateId
  dismissed: boolean
  confirmations: BuilderTemplateConfirmations
}

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
  gitView: {
    kind: "gitView",
    displayName: "Git View",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        ...createDefaultGitViewConfig(),
      },
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  fileExplorer: {
    kind: "fileExplorer",
    displayName: "File Explorer",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        ...createDefaultLiveRepoExplorerConfig(),
      },
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: PANEL_COMMON_FIELD_SPECS,
  },
  fileViewer: {
    kind: "fileViewer",
    displayName: "File Viewer",
    defaults: {
      prominence: "primary",
      viewport_mode: "panel",
      options: {
        ...createDefaultLiveRepoFileViewerConfig(),
      },
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
      config_json: {
        ...createDefaultGitViewConfig(),
      },
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
      config_json: {
        ...createDefaultLiveRepoExplorerConfig(),
      },
      presentation_json: {},
      theme_id: null,
    },
    fieldSpecs: BLOCK_COMMON_FIELD_SPECS,
  },
  fileViewer: {
    type: "fileViewer",
    displayName: "File Viewer",
    defaults: {
      region: "top",
      visibility: "visible",
      config_json: {
        ...createDefaultLiveRepoFileViewerConfig(),
      },
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

export function createCompositionTemplate(
  templateId: BuilderTemplateId,
): EditableComposition {
  return createCompositionTemplateFromRegistry(templateId, {
    createEmptyComposition,
    createPanelTemplate,
    createBlockTemplate,
    createTemplate: createCompositionTemplate,
  })
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
  if (itemId === "repo_id") {
    if (!isObjectRecord(composition.metadata_json)) return false
    const repoId = composition.metadata_json.repo_id
    return typeof repoId === "string" && repoId.trim().length > 0
  }
  if (itemId === "repo_id_secondary") {
    if (!isObjectRecord(composition.metadata_json)) return false
    const repoId = composition.metadata_json.repo_id_secondary
    return typeof repoId === "string" && repoId.trim().length > 0
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
