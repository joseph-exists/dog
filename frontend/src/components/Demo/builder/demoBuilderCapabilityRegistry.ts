import {
  ACTIVE_BUILDER_BLOCK_TYPES,
  ACTIVE_BUILDER_PANEL_KINDS,
  BUILDER_BLOCK_TYPE_SCHEMAS,
  BUILDER_COMPOSITION_FIELD_SPECS,
  BUILDER_PANEL_KIND_SCHEMAS,
  getCompositionStoryId,
  type EditableComposition,
  type ActiveBuilderBlockType,
  type ActiveBuilderPanelKind,
} from "@/components/Demo/builder/demoBuilderSchema"
import {
  ACTIVE_RUNTIME_DEMO_BLOCK_TYPES,
  ACTIVE_RUNTIME_DEMO_PANEL_KINDS,
} from "@/components/Demo/demoRuntimeCapabilities"

export interface BuilderCompositionCapability {
  key: string
  label: string
  category: "core" | "theme" | "advanced"
  control: string
  enumValues: readonly string[]
  placeholder?: string
  required?: boolean
}

export type BuilderCapabilityScope = "composition" | "panel" | "block"

export interface BuilderCapabilitySemanticIssue {
  code: string
  message: string
  severity: "warning" | "error"
}

export interface BuilderCapabilityHookContext {
  scope: BuilderCapabilityScope
  capabilityKey: string
  composition: EditableComposition
}

export type BuilderCapabilityPatchNormalizer = (
  patch: Record<string, unknown>,
  context: BuilderCapabilityHookContext,
) => Record<string, unknown>

export type BuilderCapabilitySemanticValidator = (
  context: BuilderCapabilityHookContext,
) => BuilderCapabilitySemanticIssue[]

export interface BuilderCapabilityHooks {
  // Identifier for future registry-provided custom editors.
  editorComponent?: string
  normalizeCompositionPatch?: BuilderCapabilityPatchNormalizer
  semanticValidators?: BuilderCapabilitySemanticValidator[]
}

export type BuilderPresentationFieldControl = "text" | "number" | "boolean" | "enum"

export interface BuilderPresentationFieldSpec {
  path: string
  label: string
  control: BuilderPresentationFieldControl
  description?: string
  placeholder?: string
  enumValues?: readonly string[]
}

export interface BuilderPanelCapability {
  kind: ActiveBuilderPanelKind
  displayName: string
  requirements: BuilderCapabilityRequirements
  presentationFieldSpecs?: BuilderPresentationFieldSpec[]
  hooks?: BuilderCapabilityHooks
}

export interface BuilderBlockCapability {
  type: ActiveBuilderBlockType
  displayName: string
  requirements: BuilderCapabilityRequirements
  presentationFieldSpecs?: BuilderPresentationFieldSpec[]
  hooks?: BuilderCapabilityHooks
}

export interface BuilderCapabilityRequirements {
  requiresStory: boolean
  requiresRuntime: boolean
  requiresPersona: boolean
}

export interface BuilderCapabilityAvailability {
  available: boolean
  unmetRequirements: string[]
}

export type BuilderCapabilityConflictPolicy = "error" | "keep_existing" | "replace_existing"

export interface BuilderCapabilityRegistryPack {
  id: string
  order?: number
  compositionCapabilities?: BuilderCompositionCapability[]
  panelCapabilities?: BuilderPanelCapability[]
  blockCapabilities?: BuilderBlockCapability[]
}

export interface BuilderCapabilityRegistryBuildOptions {
  includeCoreCapabilities?: boolean
  conflictPolicy?: BuilderCapabilityConflictPolicy
  packs?: BuilderCapabilityRegistryPack[]
}

export interface BuilderCapabilityRegistryConflict {
  scope: BuilderCapabilityScope
  key: string
  existingPackId: string
  incomingPackId: string
  policy: BuilderCapabilityConflictPolicy
}

export interface BuilderCapabilityRegistry {
  composition: BuilderCompositionCapability[]
  panels: BuilderPanelCapability[]
  blocks: BuilderBlockCapability[]
  conflicts: BuilderCapabilityRegistryConflict[]
}

export interface BuilderCapabilityPackRegistration {
  id: string
  description: string
  createPack: () => BuilderCapabilityRegistryPack
}

export interface BuilderCapabilityRequirementMismatch {
  scope: "panel" | "block"
  key: string
  requirement: keyof BuilderCapabilityRequirements
  expected: boolean
  actual: boolean
}

export interface BuilderCapabilityRequirementCompatibilityGaps {
  mismatches: BuilderCapabilityRequirementMismatch[]
}

export interface BuilderCapabilityRuntimeExpectationIssue {
  code:
    | "missing_runtime_coupled_capability"
    | "missing_editor_component"
    | "missing_patch_normalizer"
    | "missing_semantic_validator"
    | "requirement_mismatch"
  blockType: string
  message: string
}

export interface BuilderCapabilityRuntimeExpectationGaps {
  issues: BuilderCapabilityRuntimeExpectationIssue[]
}

export interface BuilderCapabilitySafetyIssue {
  code: "unsupported_control" | "requirement_escalation" | "requirement_relaxation"
  scope: BuilderCapabilityScope
  key: string
  severity: "warning" | "error"
  message: string
}

export interface BuilderCapabilitySafetyGaps {
  issues: BuilderCapabilitySafetyIssue[]
}

export interface BuilderCapabilityPackResolutionOptions {
  enabledPackIds?: string[]
  env?: Record<string, unknown>
  includeLegacyInternalFlag?: boolean
}

export interface BuilderCapabilityPackResolution {
  enabledPackIds: string[]
  packs: BuilderCapabilityRegistryPack[]
  unknownPackIds: string[]
}

const SUPPORTED_COMPOSITION_CONTROLS = new Set<BuilderCompositionCapability["control"]>([
  "text",
  "number",
  "enum",
  "json",
  "id",
])

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizeStoryMetadataConfigJSON(value: unknown): Record<string, unknown> {
  const config = isObjectRecord(value) ? { ...value } : {}
  config.show_config_json = config.show_config_json === true
  return config
}

function normalizeOrchestratorStateConfigJSON(value: unknown): Record<string, unknown> {
  const config = isObjectRecord(value) ? { ...value } : {}
  config.show_agent_list = config.show_agent_list !== false
  config.only_active_agents = config.only_active_agents !== false
  config.show_config_json = config.show_config_json === true
  return config
}

function normalizeContributionFeedConfigJSON(value: unknown): Record<string, unknown> {
  const config = isObjectRecord(value) ? { ...value } : {}
  const maxItemsRaw = config.max_items
  config.max_items =
    typeof maxItemsRaw === "number" && Number.isFinite(maxItemsRaw) && maxItemsRaw > 0
      ? Math.floor(maxItemsRaw)
      : 12
  config.include_internal = config.include_internal === true
  config.show_sender_type = config.show_sender_type === true
  config.show_timestamps = config.show_timestamps !== false
  config.show_config_json = config.show_config_json === true
  return config
}

function normalizeToolCapabilityConfigJSON(value: unknown): Record<string, unknown> {
  const config = isObjectRecord(value) ? { ...value } : {}
  config.only_active_agents = config.only_active_agents !== false
  config.show_agent_matrix = config.show_agent_matrix !== false
  config.show_config_json = config.show_config_json === true

  const rawCapabilityMap = config.capability_map
  if (isObjectRecord(rawCapabilityMap)) {
    const normalizedMap: Record<string, string[]> = {}
    for (const [key, mappedValue] of Object.entries(rawCapabilityMap)) {
      if (!Array.isArray(mappedValue)) continue
      const normalizedValues = mappedValue
        .filter((item): item is string => typeof item === "string")
        .map((item) => item.trim())
        .filter((item) => item.length > 0)
      if (normalizedValues.length > 0) {
        normalizedMap[key] = Array.from(new Set(normalizedValues))
      }
    }
    config.capability_map = normalizedMap
  }

  return config
}

function getBlocksByType(composition: EditableComposition, type: string) {
  return (composition.blocks ?? []).filter((candidate) => candidate.type === type)
}

function getBlockHooks(type: ActiveBuilderBlockType): BuilderCapabilityHooks {
  if (type === "storyMetadata") {
    return {
      editorComponent: "StoryMetadataBlockEditor",
      normalizeCompositionPatch: (patch) => {
        if (!Object.prototype.hasOwnProperty.call(patch, "config_json")) return patch
        return {
          ...patch,
          config_json: normalizeStoryMetadataConfigJSON(patch.config_json),
        }
      },
      semanticValidators: [
        (context) => {
          const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
          const hasVisibleDebugConfig = matchingBlocks.some((block) => {
            const config = normalizeStoryMetadataConfigJSON(block?.config_json)
            return config.show_config_json === true
          })
          if (!hasVisibleDebugConfig) return []
          return [{
            code: "story_metadata_config_visible",
            severity: "warning" as const,
            message: "storyMetadata config_json debug output is enabled (show_config_json=true).",
          }]
        },
      ],
    }
  }
  if (type === "orchestratorState") {
    return {
      editorComponent: "OrchestratorStateBlockEditor",
      normalizeCompositionPatch: (patch) => {
        if (!Object.prototype.hasOwnProperty.call(patch, "config_json")) return patch
        return {
          ...patch,
          config_json: normalizeOrchestratorStateConfigJSON(patch.config_json),
        }
      },
      semanticValidators: [
        (context) => {
          const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
          const hidesAgentList = matchingBlocks.some((block) => {
            const config = normalizeOrchestratorStateConfigJSON(block?.config_json)
            return config.show_agent_list === false
          })
          if (!hidesAgentList) return []
          return [{
            code: "orchestrator_agent_list_hidden",
            severity: "warning" as const,
            message: "orchestratorState hides agent list (show_agent_list=false); orchestration visibility is reduced.",
          }]
        },
      ],
    }
  }
  if (type === "contributionFeed") {
    return {
      editorComponent: "ContributionFeedBlockEditor",
      normalizeCompositionPatch: (patch) => {
        if (!Object.prototype.hasOwnProperty.call(patch, "config_json")) return patch
        return {
          ...patch,
          config_json: normalizeContributionFeedConfigJSON(patch.config_json),
        }
      },
      semanticValidators: [
        (context) => {
          const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
          const warnings: BuilderCapabilitySemanticIssue[] = []
          const includesInternal = matchingBlocks.some((block) => {
            const config = normalizeContributionFeedConfigJSON(block?.config_json)
            return config.include_internal === true
          })
          if (includesInternal) {
            warnings.push({
              code: "contribution_feed_internal_enabled",
              severity: "warning",
              message: "contributionFeed includes internal messages (include_internal=true).",
            })
          }
          const largeWindow = matchingBlocks.some((block) => {
            const config = normalizeContributionFeedConfigJSON(block?.config_json)
            return typeof config.max_items === "number" && config.max_items > 50
          })
          if (largeWindow) {
            warnings.push({
              code: "contribution_feed_large_window",
              severity: "warning",
              message: "contributionFeed max_items is high (>50) and may add UI noise.",
            })
          }
          return warnings
        },
      ],
    }
  }
  if (type === "toolCapability") {
    return {
      editorComponent: "ToolCapabilityBlockEditor",
      normalizeCompositionPatch: (patch) => {
        if (!Object.prototype.hasOwnProperty.call(patch, "config_json")) return patch
        return {
          ...patch,
          config_json: normalizeToolCapabilityConfigJSON(patch.config_json),
        }
      },
      semanticValidators: [
        (context) => {
          const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
          const hasInvalidMapping = matchingBlocks.some((block) => {
            const rawConfig = block.config_json
            if (!isObjectRecord(rawConfig)) return false
            if (!Object.prototype.hasOwnProperty.call(rawConfig, "capability_map")) return false
            if (!isObjectRecord(rawConfig.capability_map)) return true
            const rawCapabilityMap = rawConfig.capability_map as Record<string, unknown>
            const normalized = normalizeToolCapabilityConfigJSON(rawConfig)
            const normalizedCapabilityMap = isObjectRecord(normalized.capability_map)
              ? normalized.capability_map
              : {}
            return Object.keys(rawCapabilityMap).length > 0 && Object.keys(normalizedCapabilityMap).length === 0
          })
          if (!hasInvalidMapping) return []
          return [{
            code: "tool_capability_invalid_mapping",
            severity: "warning",
            message: "toolCapability capability_map contains invalid entries and was normalized.",
          }]
        },
      ],
    }
  }
  return {}
}

function getPanelPresentationFieldSpecs(kind: ActiveBuilderPanelKind): BuilderPresentationFieldSpec[] {
  if (kind === "storyRuntime") {
    return [
      {
        path: "overlays.panel_header.css",
        label: "Header Overlay CSS",
        control: "text",
        placeholder: "linear-gradient(...)",
      },
      {
        path: "motion.panel_enter_ms",
        label: "Panel Enter (ms)",
        control: "number",
      },
      {
        path: "tokens.surface_radius",
        label: "Surface Radius",
        control: "text",
        placeholder: "12px",
      },
    ]
  }
  if (kind === "chat") {
    return [
      {
        path: "typography.size",
        label: "Message Size",
        control: "enum",
        enumValues: ["xs", "sm", "base", "lg"],
      },
      {
        path: "tokens.feed_density",
        label: "Feed Density",
        control: "enum",
        enumValues: ["comfortable", "compact"],
      },
      {
        path: "effects.message_row_highlight.enable",
        label: "Row Highlight",
        control: "boolean",
      },
    ]
  }
  if (kind === "participantPanel") {
    return [
      {
        path: "tokens.stack_density",
        label: "Stack Density",
        control: "enum",
        enumValues: ["comfortable", "compact"],
      },
      {
        path: "overlays.panel_header.css",
        label: "Header Overlay CSS",
        control: "text",
        placeholder: "linear-gradient(...)",
      },
    ]
  }
  return []
}

function getBlockPresentationFieldSpecs(type: ActiveBuilderBlockType): BuilderPresentationFieldSpec[] {
  if (type === "storyMetadata") {
    return [
      {
        path: "typography.size",
        label: "Text Size",
        control: "enum",
        enumValues: ["xs", "sm", "base", "lg"],
      },
      {
        path: "typography.line_height",
        label: "Line Height",
        control: "enum",
        enumValues: ["tight", "normal", "relaxed"],
      },
      {
        path: "backgrounds.card_pattern.css",
        label: "Card Pattern CSS",
        control: "text",
      },
    ]
  }
  if (type === "orchestratorState") {
    return [
      {
        path: "overlays.block_header.css",
        label: "Header Overlay CSS",
        control: "text",
        placeholder: "linear-gradient(...)",
      },
      {
        path: "tokens.status_badge_style",
        label: "Status Badge Style",
        control: "enum",
        enumValues: ["default", "high-contrast", "minimal"],
      },
      {
        path: "effects.card_glow.enable",
        label: "Card Glow",
        control: "boolean",
      },
    ]
  }
  if (type === "contributionFeed") {
    return [
      {
        path: "typography.size",
        label: "Text Size",
        control: "enum",
        enumValues: ["xs", "sm", "base", "lg"],
      },
      {
        path: "tokens.feed_density",
        label: "Feed Density",
        control: "enum",
        enumValues: ["comfortable", "compact"],
      },
      {
        path: "effects.message_row_highlight.css",
        label: "Row Highlight CSS",
        control: "text",
      },
    ]
  }
  if (type === "toolCapability") {
    return [
      {
        path: "tokens.matrix_density",
        label: "Matrix Density",
        control: "enum",
        enumValues: ["comfortable", "compact"],
      },
      {
        path: "overlays.block_header.css",
        label: "Header Overlay CSS",
        control: "text",
        placeholder: "linear-gradient(...)",
      },
      {
        path: "effects.card_glow.enable",
        label: "Card Glow",
        control: "boolean",
      },
    ]
  }
  if (type === "agentRoster") {
    return [
      {
        path: "tokens.stack_density",
        label: "Roster Density",
        control: "enum",
        enumValues: ["comfortable", "compact"],
      },
      {
        path: "typography.size",
        label: "Text Size",
        control: "enum",
        enumValues: ["xs", "sm", "base", "lg"],
      },
    ]
  }
  return []
}

function getPanelRequirements(kind: ActiveBuilderPanelKind): BuilderCapabilityRequirements {
  const schema = BUILDER_PANEL_KIND_SCHEMAS[kind]
  return {
    requiresStory: Boolean(schema.requiresStoryId),
    requiresRuntime: kind === "storyRuntime",
    requiresPersona: kind === "participantPanel",
  }
}

function getBlockRequirements(type: ActiveBuilderBlockType): BuilderCapabilityRequirements {
  const schema = BUILDER_BLOCK_TYPE_SCHEMAS[type]
  return {
    requiresStory: Boolean(schema.requiresStoryId),
    requiresRuntime: type === "storyMetadata" || type === "orchestratorState" || type === "contributionFeed",
    requiresPersona: type === "agentRoster" || type === "orchestratorState" || type === "toolCapability",
  }
}

function mergeCapabilityHooks(
  base: BuilderCapabilityHooks | undefined,
  extension: BuilderCapabilityHooks | undefined,
): BuilderCapabilityHooks {
  if (!base && !extension) return {}
  const mergedValidators = [
    ...(base?.semanticValidators ?? []),
    ...(extension?.semanticValidators ?? []),
  ]
  return {
    ...base,
    ...extension,
    semanticValidators: mergedValidators.length > 0 ? mergedValidators : undefined,
  }
}

function isTruthyEnvFlag(value: string | undefined): boolean {
  if (!value) return false
  const normalized = value.trim().toLowerCase()
  return normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on"
}

function toEnvString(value: unknown): string | undefined {
  return typeof value === "string" ? value : undefined
}

function getImportMetaEnv(): Record<string, unknown> {
  const env = (import.meta as ImportMeta & { env?: Record<string, unknown> }).env
  return env ?? {}
}

function parsePackIdsCSV(value: string | undefined): string[] {
  if (!value) return []
  return value
    .split(",")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
}

const CORE_BUILDER_COMPOSITION_CAPABILITIES: BuilderCompositionCapability[] =
  BUILDER_COMPOSITION_FIELD_SPECS.map((field) => ({
    key: field.key,
    label: field.label,
    category: field.category ?? "core",
    control: field.control,
    enumValues: field.enumValues ?? [],
    placeholder: field.placeholder,
    required: field.required,
  }))

const CORE_BUILDER_PANEL_CAPABILITIES: BuilderPanelCapability[] =
  ACTIVE_BUILDER_PANEL_KINDS.map((kind) => ({
    kind,
    displayName: BUILDER_PANEL_KIND_SCHEMAS[kind].displayName,
    requirements: getPanelRequirements(kind),
    presentationFieldSpecs: getPanelPresentationFieldSpecs(kind),
    hooks: {},
  }))

const CORE_BUILDER_BLOCK_CAPABILITIES: BuilderBlockCapability[] =
  ACTIVE_BUILDER_BLOCK_TYPES.map((type) => ({
    type,
    displayName: BUILDER_BLOCK_TYPE_SCHEMAS[type].displayName,
    requirements: getBlockRequirements(type),
    presentationFieldSpecs: getBlockPresentationFieldSpecs(type),
    hooks: getBlockHooks(type),
  }))

const CORE_PANEL_REQUIREMENTS_BY_KIND = new Map<string, BuilderCapabilityRequirements>(
  CORE_BUILDER_PANEL_CAPABILITIES.map((capability) => [capability.kind, capability.requirements]),
)

const CORE_BLOCK_REQUIREMENTS_BY_TYPE = new Map<string, BuilderCapabilityRequirements>(
  CORE_BUILDER_BLOCK_CAPABILITIES.map((capability) => [capability.type, capability.requirements]),
)

type RuntimeCoupledBlockType =
  | "storyMetadata"
  | "orchestratorState"
  | "contributionFeed"
  | "toolCapability"

const RUNTIME_COUPLED_BLOCK_EXPECTATIONS: Record<RuntimeCoupledBlockType, {
  requirements: BuilderCapabilityRequirements
  requiresEditorComponent: boolean
  requiresPatchNormalizer: boolean
  requiresSemanticValidator: boolean
}> = {
  storyMetadata: {
    requirements: { requiresStory: true, requiresRuntime: true, requiresPersona: false },
    requiresEditorComponent: true,
    requiresPatchNormalizer: true,
    requiresSemanticValidator: true,
  },
  orchestratorState: {
    requirements: { requiresStory: false, requiresRuntime: true, requiresPersona: true },
    requiresEditorComponent: true,
    requiresPatchNormalizer: true,
    requiresSemanticValidator: true,
  },
  contributionFeed: {
    requirements: { requiresStory: false, requiresRuntime: true, requiresPersona: false },
    requiresEditorComponent: true,
    requiresPatchNormalizer: true,
    requiresSemanticValidator: true,
  },
  toolCapability: {
    requirements: { requiresStory: false, requiresRuntime: false, requiresPersona: true },
    requiresEditorComponent: true,
    requiresPatchNormalizer: true,
    requiresSemanticValidator: true,
  },
}

function buildInternalDemoBuilderPluginPack(): BuilderCapabilityRegistryPack {
  const basePanel = CORE_BUILDER_PANEL_CAPABILITIES.find((capability) => capability.kind === "participantPanel")
  const baseBlock = CORE_BUILDER_BLOCK_CAPABILITIES.find((capability) => capability.type === "toolCapability")
  if (!basePanel || !baseBlock) {
    return {
      id: "internal.plugin.demo-builder.v1",
      order: 500,
    }
  }
  return {
    id: "internal.plugin.demo-builder.v1",
    order: 500,
    panelCapabilities: [
      {
        ...basePanel,
        displayName: `${basePanel.displayName} (Plugin)`,
        hooks: mergeCapabilityHooks(basePanel.hooks, {
          editorComponent: "ParticipantPanelPluginEditor",
        }),
      },
    ],
    blockCapabilities: [
      {
        ...baseBlock,
        displayName: `${baseBlock.displayName} (Plugin)`,
        hooks: mergeCapabilityHooks(baseBlock.hooks, {
          editorComponent: "ToolCapabilityPluginEditor",
          semanticValidators: [
            (context) => {
              const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
              const missingMap = matchingBlocks.some((block) => {
                if (!isObjectRecord(block.config_json)) return true
                const rawMap = block.config_json.capability_map
                return !isObjectRecord(rawMap) || Object.keys(rawMap).length === 0
              })
              if (!missingMap) return []
              return [{
                code: "tool_capability_mapping_missing",
                severity: "warning",
                message: "toolCapability has no capability_map entries; matrix rendering may appear empty.",
              }]
            },
          ],
        }),
      },
    ],
  }
}

function buildRuntimeSafeExamplePack(): BuilderCapabilityRegistryPack {
  const baseStoryMetadata = CORE_BUILDER_BLOCK_CAPABILITIES.find((capability) => capability.type === "storyMetadata")
  if (!baseStoryMetadata) return { id: "example.runtime-safe.v1", order: 610 }
  return {
    id: "example.runtime-safe.v1",
    order: 610,
    blockCapabilities: [
      {
        ...baseStoryMetadata,
        displayName: "Story Metadata (Runtime Safe)",
        hooks: mergeCapabilityHooks(baseStoryMetadata.hooks, {
          editorComponent: "StoryMetadataRuntimeSafeEditor",
          semanticValidators: [
            (context) => {
              const matchingBlocks = getBlocksByType(context.composition, context.capabilityKey)
              const hasConfig = matchingBlocks.some((block) => isObjectRecord(block.config_json))
              if (hasConfig) return []
              return [{
                code: "story_metadata_missing_config",
                severity: "warning",
                message: "storyMetadata block is missing config_json object.",
              }]
            },
          ],
        }),
      },
    ],
  }
}

function buildUxEnhancerExamplePack(): BuilderCapabilityRegistryPack {
  return {
    id: "example.ux-enhancer.v1",
    order: 620,
    compositionCapabilities: [
      {
        key: "page_theme_id",
        label: "Page Theme Preset",
        category: "theme",
        control: "id",
        enumValues: [],
        placeholder: "e.g. ux-sunrise-canvas",
      },
      {
        key: "cards_theme_id",
        label: "Card Theme Preset",
        category: "theme",
        control: "id",
        enumValues: [],
        placeholder: "e.g. ux-glass-overlay",
      },
      {
        key: "presentation_json",
        label: "Presentation JSON (Fonts/Motion/Overlays/SVG)",
        category: "theme",
        control: "json",
        enumValues: [],
      },
    ],
    panelCapabilities: CORE_BUILDER_PANEL_CAPABILITIES.map((capability) => ({
      ...capability,
      displayName: `${capability.displayName} (UX)`,
    })),
    blockCapabilities: CORE_BUILDER_BLOCK_CAPABILITIES.map((capability) => ({
      ...capability,
      displayName: `${capability.displayName} (UX)`,
    })),
  }
}

function buildPolicyGuardedExamplePack(): BuilderCapabilityRegistryPack {
  const participantPanel = CORE_BUILDER_PANEL_CAPABILITIES.find((capability) => capability.kind === "participantPanel")
  if (!participantPanel) return { id: "example.policy-guarded.v1", order: 630 }
  return {
    id: "example.policy-guarded.v1",
    order: 630,
    panelCapabilities: [
      {
        ...participantPanel,
        displayName: "Participant Panel (Policy Guarded)",
        requirements: {
          ...participantPanel.requirements,
          requiresRuntime: true,
        },
      },
    ],
  }
}

function buildInvalidExamplePack(): BuilderCapabilityRegistryPack {
  return {
    id: "example.invalid.v1",
    order: 640,
    compositionCapabilities: [
      {
        key: "invalid_unsupported_toggle",
        label: "Invalid Toggle",
        category: "advanced",
        control: "boolean",
        enumValues: [],
      },
    ],
    blockCapabilities: [
      {
        type: "toolCapability",
        displayName: "Tool Capability (Invalid)",
        requirements: {
          requiresStory: false,
          requiresRuntime: false,
          requiresPersona: true,
        },
        hooks: {},
      },
    ],
  }
}

function getBuiltinBuilderCapabilityPackRegistrations(): BuilderCapabilityPackRegistration[] {
  return [
    {
      id: "internal.plugin.demo-builder.v1",
      description: "Internal builder plugin spike pack (participantPanel/toolCapability overrides).",
      createPack: () => buildInternalDemoBuilderPluginPack(),
    },
    {
      id: "example.runtime-safe.v1",
      description: "Reference runtime-coupled extension that preserves expectation/safety checks.",
      createPack: () => buildRuntimeSafeExamplePack(),
    },
    {
      id: "example.ux-enhancer.v1",
      description: "UX-focused example pack for theme-oriented labels/placeholders and naming.",
      createPack: () => buildUxEnhancerExamplePack(),
    },
    {
      id: "example.policy-guarded.v1",
      description: "Example showing policy-driven requirement escalation for gated rollouts.",
      createPack: () => buildPolicyGuardedExamplePack(),
    },
    {
      id: "example.invalid.v1",
      description: "Intentionally invalid example pack for analyzer/testing demos.",
      createPack: () => buildInvalidExamplePack(),
    },
  ]
}

export const BUILDER_CAPABILITY_PACK_REGISTRATIONS: BuilderCapabilityPackRegistration[] =
  getBuiltinBuilderCapabilityPackRegistrations()

export function getBuilderCapabilityPackRegistrationInventory(): Array<{
  id: string
  description: string
}> {
  return BUILDER_CAPABILITY_PACK_REGISTRATIONS.map((registration) => ({
    id: registration.id,
    description: registration.description,
  }))
}

export function resolveBuilderCapabilityPacks(
  options: BuilderCapabilityPackResolutionOptions = {},
): BuilderCapabilityPackResolution {
  const env = options.env ?? getImportMetaEnv()
  const includeLegacyInternalFlag = options.includeLegacyInternalFlag !== false
  const packIdsFromEnv = parsePackIdsCSV(toEnvString(env.VITE_DEMO_BUILDER_PACKS))
  const enabledPackIds = options.enabledPackIds ?? packIdsFromEnv
  const catalog = new Map(
    BUILDER_CAPABILITY_PACK_REGISTRATIONS.map((registration) => [registration.id, registration]),
  )

  const resolvedIds = new Set(enabledPackIds)
  if (includeLegacyInternalFlag) {
    const legacyFlag = toEnvString(env.VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK)
    if (isTruthyEnvFlag(legacyFlag)) {
      resolvedIds.add("internal.plugin.demo-builder.v1")
    }
  }

  const knownPackIds = Array.from(resolvedIds).filter((packId) => catalog.has(packId))
  const unknownPackIds = Array.from(resolvedIds).filter((packId) => !catalog.has(packId))
  const packs = knownPackIds.map((packId) => {
    const registration = catalog.get(packId)!
    return registration.createPack()
  })

  return {
    enabledPackIds: knownPackIds,
    packs,
    unknownPackIds,
  }
}

function getScopeEntryKey(scope: BuilderCapabilityScope, entry: unknown): string {
  if (scope === "composition") return (entry as BuilderCompositionCapability).key
  if (scope === "panel") return (entry as BuilderPanelCapability).kind
  return (entry as BuilderBlockCapability).type
}

function mergeCapabilityEntries<TEntry>(
  scope: BuilderCapabilityScope,
  entries: TEntry[],
  entryPackId: string,
  destination: TEntry[],
  sourceByKey: Map<string, string>,
  conflicts: BuilderCapabilityRegistryConflict[],
  conflictPolicy: BuilderCapabilityConflictPolicy,
): void {
  for (const entry of entries) {
    const key = getScopeEntryKey(scope, entry)
    const existingIndex = destination.findIndex((candidate) => getScopeEntryKey(scope, candidate) === key)
    if (existingIndex === -1) {
      destination.push(entry)
      sourceByKey.set(key, entryPackId)
      continue
    }

    const conflict: BuilderCapabilityRegistryConflict = {
      scope,
      key,
      existingPackId: sourceByKey.get(key) ?? "unknown",
      incomingPackId: entryPackId,
      policy: conflictPolicy,
    }
    conflicts.push(conflict)

    if (conflictPolicy === "error") {
      throw new Error(
        `Capability registry conflict (${scope}:${key}) between packs "${conflict.existingPackId}" and "${conflict.incomingPackId}".`,
      )
    }
    if (conflictPolicy === "replace_existing") {
      destination[existingIndex] = entry
      sourceByKey.set(key, entryPackId)
    }
  }
}

export function buildCapabilityRegistry(options: BuilderCapabilityRegistryBuildOptions = {}): BuilderCapabilityRegistry {
  const includeCoreCapabilities = options.includeCoreCapabilities !== false
  const conflictPolicy = options.conflictPolicy ?? "keep_existing"
  const packs = [...(options.packs ?? [])]
    .sort((a, b) => {
      const aOrder = a.order ?? 100
      const bOrder = b.order ?? 100
      if (aOrder !== bOrder) return aOrder - bOrder
      return a.id.localeCompare(b.id)
    })

  const composition: BuilderCompositionCapability[] = []
  const panels: BuilderPanelCapability[] = []
  const blocks: BuilderBlockCapability[] = []
  const conflicts: BuilderCapabilityRegistryConflict[] = []

  const compositionSources = new Map<string, string>()
  const panelSources = new Map<string, string>()
  const blockSources = new Map<string, string>()

  if (includeCoreCapabilities) {
    mergeCapabilityEntries(
      "composition",
      CORE_BUILDER_COMPOSITION_CAPABILITIES,
      "core",
      composition,
      compositionSources,
      conflicts,
      conflictPolicy,
    )
    mergeCapabilityEntries(
      "panel",
      CORE_BUILDER_PANEL_CAPABILITIES,
      "core",
      panels,
      panelSources,
      conflicts,
      conflictPolicy,
    )
    mergeCapabilityEntries(
      "block",
      CORE_BUILDER_BLOCK_CAPABILITIES,
      "core",
      blocks,
      blockSources,
      conflicts,
      conflictPolicy,
    )
  }

  for (const pack of packs) {
    mergeCapabilityEntries(
      "composition",
      pack.compositionCapabilities ?? [],
      pack.id,
      composition,
      compositionSources,
      conflicts,
      conflictPolicy,
    )
    mergeCapabilityEntries(
      "panel",
      pack.panelCapabilities ?? [],
      pack.id,
      panels,
      panelSources,
      conflicts,
      conflictPolicy,
    )
    mergeCapabilityEntries(
      "block",
      pack.blockCapabilities ?? [],
      pack.id,
      blocks,
      blockSources,
      conflicts,
      conflictPolicy,
    )
  }

  return {
    composition,
    panels,
    blocks,
    conflicts,
  }
}

const DEFAULT_BUILDER_CAPABILITY_REGISTRY = buildCapabilityRegistry({
  conflictPolicy: "replace_existing",
  packs: resolveBuilderCapabilityPacks().packs,
})

export const BUILDER_COMPOSITION_CAPABILITIES: BuilderCompositionCapability[] =
  DEFAULT_BUILDER_CAPABILITY_REGISTRY.composition

export const BUILDER_PANEL_CAPABILITIES: BuilderPanelCapability[] = DEFAULT_BUILDER_CAPABILITY_REGISTRY.panels

export const BUILDER_BLOCK_CAPABILITIES: BuilderBlockCapability[] = DEFAULT_BUILDER_CAPABILITY_REGISTRY.blocks

export function getPanelCapabilityByKind(kind: string | null | undefined): BuilderPanelCapability | null {
  if (!kind) return null
  return BUILDER_PANEL_CAPABILITIES.find((capability) => capability.kind === kind) ?? null
}

export function getBlockCapabilityByType(type: string | null | undefined): BuilderBlockCapability | null {
  if (!type) return null
  return BUILDER_BLOCK_CAPABILITIES.find((capability) => capability.type === type) ?? null
}

export function getBuilderCapabilityRegistrySnapshot(registry: BuilderCapabilityRegistry = DEFAULT_BUILDER_CAPABILITY_REGISTRY) {
  return {
    composition: registry.composition,
    panels: registry.panels,
    blocks: registry.blocks,
    conflicts: registry.conflicts,
  }
}

export function getBuilderCapabilityCoverageGaps() {
  const missingPanelCapabilities = ACTIVE_BUILDER_PANEL_KINDS.filter((kind) => {
    return !BUILDER_PANEL_CAPABILITIES.some((capability) => capability.kind === kind)
  })
  const missingBlockCapabilities = ACTIVE_BUILDER_BLOCK_TYPES.filter((type) => {
    return !BUILDER_BLOCK_CAPABILITIES.some((capability) => capability.type === type)
  })
  return {
    missingPanelCapabilities,
    missingBlockCapabilities,
  }
}

export function getBuilderRuntimeCompatibilityGaps(
  registry: BuilderCapabilityRegistry = DEFAULT_BUILDER_CAPABILITY_REGISTRY,
) {
  const runtimePanels = new Set<string>(ACTIVE_RUNTIME_DEMO_PANEL_KINDS)
  const builderPanelKinds = registry.panels.map((capability) => capability.kind)
  const builderPanels = new Set<string>(builderPanelKinds)
  const runtimeBlocks = new Set<string>(ACTIVE_RUNTIME_DEMO_BLOCK_TYPES)
  const builderBlockTypes = registry.blocks.map((capability) => capability.type)
  const builderBlocks = new Set<string>(builderBlockTypes)

  const missingBuilderPanelsInRuntime = builderPanelKinds.filter((kind) => {
    return !runtimePanels.has(kind)
  })
  const missingRuntimePanelsInBuilder = ACTIVE_RUNTIME_DEMO_PANEL_KINDS.filter((kind) => {
    return !builderPanels.has(kind)
  })
  const missingBuilderBlocksInRuntime = builderBlockTypes.filter((type) => {
    return !runtimeBlocks.has(type)
  })
  const missingRuntimeBlocksInBuilder = ACTIVE_RUNTIME_DEMO_BLOCK_TYPES.filter((type) => {
    return !builderBlocks.has(type)
  })

  return {
    missingBuilderPanelsInRuntime,
    missingRuntimePanelsInBuilder,
    missingBuilderBlocksInRuntime,
    missingRuntimeBlocksInBuilder,
  }
}

export function getBuilderRequirementCompatibilityGaps(
  registry: BuilderCapabilityRegistry = DEFAULT_BUILDER_CAPABILITY_REGISTRY,
): BuilderCapabilityRequirementCompatibilityGaps {
  const mismatches: BuilderCapabilityRequirementMismatch[] = []

  for (const panelCapability of registry.panels) {
    const expected = CORE_PANEL_REQUIREMENTS_BY_KIND.get(panelCapability.kind)
    if (!expected) continue
    for (const requirement of ["requiresStory", "requiresRuntime", "requiresPersona"] as const) {
      const actualValue = panelCapability.requirements[requirement]
      const expectedValue = expected[requirement]
      if (actualValue !== expectedValue) {
        mismatches.push({
          scope: "panel",
          key: panelCapability.kind,
          requirement,
          expected: expectedValue,
          actual: actualValue,
        })
      }
    }
  }

  for (const blockCapability of registry.blocks) {
    const expected = CORE_BLOCK_REQUIREMENTS_BY_TYPE.get(blockCapability.type)
    if (!expected) continue
    for (const requirement of ["requiresStory", "requiresRuntime", "requiresPersona"] as const) {
      const actualValue = blockCapability.requirements[requirement]
      const expectedValue = expected[requirement]
      if (actualValue !== expectedValue) {
        mismatches.push({
          scope: "block",
          key: blockCapability.type,
          requirement,
          expected: expectedValue,
          actual: actualValue,
        })
      }
    }
  }

  return { mismatches }
}

export function getBuilderRuntimeExpectationGaps(
  registry: BuilderCapabilityRegistry = DEFAULT_BUILDER_CAPABILITY_REGISTRY,
): BuilderCapabilityRuntimeExpectationGaps {
  const issues: BuilderCapabilityRuntimeExpectationIssue[] = []
  const blockByType = new Map(registry.blocks.map((capability) => [capability.type, capability]))

  for (const blockType of Object.keys(RUNTIME_COUPLED_BLOCK_EXPECTATIONS) as RuntimeCoupledBlockType[]) {
    const expectation = RUNTIME_COUPLED_BLOCK_EXPECTATIONS[blockType]
    const capability = blockByType.get(blockType)
    if (!capability) {
      issues.push({
        code: "missing_runtime_coupled_capability",
        blockType,
        message: `Missing runtime-coupled block capability "${blockType}" in registry.`,
      })
      continue
    }

    const requirements = capability.requirements
    for (const requirement of ["requiresStory", "requiresRuntime", "requiresPersona"] as const) {
      if (requirements[requirement] !== expectation.requirements[requirement]) {
        issues.push({
          code: "requirement_mismatch",
          blockType,
          message: `Requirement mismatch for "${blockType}" (${requirement} expected ${expectation.requirements[requirement]}, got ${requirements[requirement]}).`,
        })
      }
    }

    const hooks = capability.hooks ?? {}
    if (expectation.requiresEditorComponent && !hooks.editorComponent) {
      issues.push({
        code: "missing_editor_component",
        blockType,
        message: `Block "${blockType}" is missing hooks.editorComponent.`,
      })
    }
    if (expectation.requiresPatchNormalizer && !hooks.normalizeCompositionPatch) {
      issues.push({
        code: "missing_patch_normalizer",
        blockType,
        message: `Block "${blockType}" is missing hooks.normalizeCompositionPatch.`,
      })
    }
    if (expectation.requiresSemanticValidator && (hooks.semanticValidators?.length ?? 0) === 0) {
      issues.push({
        code: "missing_semantic_validator",
        blockType,
        message: `Block "${blockType}" is missing hooks.semanticValidators.`,
      })
    }
  }

  return { issues }
}

export function getBuilderCapabilitySafetyGaps(
  registry: BuilderCapabilityRegistry = DEFAULT_BUILDER_CAPABILITY_REGISTRY,
): BuilderCapabilitySafetyGaps {
  const issues: BuilderCapabilitySafetyIssue[] = []

  for (const capability of registry.composition) {
    if (!SUPPORTED_COMPOSITION_CONTROLS.has(capability.control)) {
      issues.push({
        code: "unsupported_control",
        scope: "composition",
        key: capability.key,
        severity: "error",
        message: `Unsupported composition control "${capability.control}" for capability "${capability.key}".`,
      })
    }
  }

  const requirementGaps = getBuilderRequirementCompatibilityGaps(registry)
  for (const mismatch of requirementGaps.mismatches) {
    const isEscalation = mismatch.expected === false && mismatch.actual === true
    issues.push({
      code: isEscalation ? "requirement_escalation" : "requirement_relaxation",
      scope: mismatch.scope,
      key: mismatch.key,
      severity: isEscalation ? "error" : "warning",
      message: `${mismatch.scope} "${mismatch.key}" changed ${mismatch.requirement} from ${mismatch.expected} to ${mismatch.actual}.`,
    })
  }

  return { issues }
}

function hasRuntimeSetup(composition: EditableComposition): boolean {
  return typeof composition.runtime_policy === "string" && composition.runtime_policy.length > 0
}

function hasPersonaSetup(composition: EditableComposition): boolean {
  const policy = composition.persona_policy
  if (policy === "fixed_user_persona") {
    return typeof composition.fixed_user_persona_id === "string" && composition.fixed_user_persona_id.trim().length > 0
  }
  return typeof policy === "string" && policy.length > 0
}

function getAvailabilityForRequirements(
  requirements: BuilderCapabilityRequirements,
  composition: EditableComposition,
): BuilderCapabilityAvailability {
  const unmetRequirements: string[] = []
  if (requirements.requiresStory && !getCompositionStoryId(composition)) unmetRequirements.push("story setup")
  if (requirements.requiresRuntime && !hasRuntimeSetup(composition)) unmetRequirements.push("runtime setup")
  if (requirements.requiresPersona && !hasPersonaSetup(composition)) unmetRequirements.push("persona setup")
  return {
    available: unmetRequirements.length === 0,
    unmetRequirements,
  }
}

export function getPanelCapabilityAvailability(
  capability: BuilderPanelCapability,
  composition: EditableComposition,
): BuilderCapabilityAvailability {
  return getAvailabilityForRequirements(capability.requirements, composition)
}

export function getBlockCapabilityAvailability(
  capability: BuilderBlockCapability,
  composition: EditableComposition,
): BuilderCapabilityAvailability {
  return getAvailabilityForRequirements(capability.requirements, composition)
}

function normalizeCapabilityPatch(
  capability: BuilderPanelCapability | BuilderBlockCapability,
  scope: "panel" | "block",
  capabilityKey: string,
  patch: Record<string, unknown>,
  composition: EditableComposition,
): Record<string, unknown> {
  const hook = capability.hooks?.normalizeCompositionPatch
  if (!hook) return patch
  return hook(patch, {
    scope,
    capabilityKey,
    composition,
  })
}

function runCapabilitySemanticValidators(
  capability: BuilderPanelCapability | BuilderBlockCapability,
  scope: "panel" | "block",
  capabilityKey: string,
  composition: EditableComposition,
): BuilderCapabilitySemanticIssue[] {
  const validators = capability.hooks?.semanticValidators ?? []
  return validators.flatMap((validator) => validator({
    scope,
    capabilityKey,
    composition,
  }))
}

export function normalizePanelCapabilityPatch(
  capability: BuilderPanelCapability,
  patch: Record<string, unknown>,
  composition: EditableComposition,
): Record<string, unknown> {
  return normalizeCapabilityPatch(capability, "panel", capability.kind, patch, composition)
}

export function normalizeBlockCapabilityPatch(
  capability: BuilderBlockCapability,
  patch: Record<string, unknown>,
  composition: EditableComposition,
): Record<string, unknown> {
  return normalizeCapabilityPatch(capability, "block", capability.type, patch, composition)
}

export function runPanelCapabilitySemanticValidators(
  capability: BuilderPanelCapability,
  composition: EditableComposition,
): BuilderCapabilitySemanticIssue[] {
  return runCapabilitySemanticValidators(capability, "panel", capability.kind, composition)
}

export function runBlockCapabilitySemanticValidators(
  capability: BuilderBlockCapability,
  composition: EditableComposition,
): BuilderCapabilitySemanticIssue[] {
  return runCapabilitySemanticValidators(capability, "block", capability.type, composition)
}
