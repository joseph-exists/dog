import {
  createEmptyPromptDraft,
  normalizePromptDraft,
  PROMPT_BUILDER_FIELD_SPECS,
  type PromptBuilderFieldSpec,
  type PromptConfigDraft,
  type PromptSemanticIssue,
  type PromptSemanticValidationContext,
  validatePromptDraftSemantics,
} from "./promptBuilderSchema"

export type PromptCapabilityConflictPolicy =
  | "error"
  | "keep_existing"
  | "replace_existing"

export interface PromptCapabilitySemanticIssue {
  code: string
  message: string
  severity: "warning" | "error"
  path?: string
}

export interface PromptCapabilityHookContext {
  capabilityKey: string
  draft: PromptConfigDraft
}

export type PromptCapabilityValueNormalizer = (
  value: unknown,
  context: PromptCapabilityHookContext,
) => unknown

export type PromptCapabilitySemanticValidator = (
  context: PromptCapabilityHookContext,
) => PromptCapabilitySemanticIssue[]

export interface PromptCapabilityHooks {
  editorComponent?: string
  normalizeValue?: PromptCapabilityValueNormalizer
  semanticValidators?: PromptCapabilitySemanticValidator[]
}

export interface PromptCapability extends PromptBuilderFieldSpec {
  hooks?: PromptCapabilityHooks
}

export interface PromptCapabilityRegistryPack {
  id: string
  order?: number
  capabilities?: PromptCapability[]
}

export interface PromptCapabilityRegistryBuildOptions {
  includeCoreCapabilities?: boolean
  conflictPolicy?: PromptCapabilityConflictPolicy
  packs?: PromptCapabilityRegistryPack[]
}

export interface PromptCapabilityRegistryConflict {
  key: string
  existingPackId: string
  incomingPackId: string
  policy: PromptCapabilityConflictPolicy
}

export interface PromptCapabilityRegistry {
  capabilities: PromptCapability[]
  conflicts: PromptCapabilityRegistryConflict[]
}

export interface PromptCapabilityCoverageGaps {
  missingCapabilities: string[]
}

type PromptToolChoice = NonNullable<PromptConfigDraft["tools"]>["tool_choice"]

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function asTrimmedString(value: unknown): string | null {
  if (typeof value !== "string") return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

function normalizeStopSequences(value: unknown): string[] | null {
  if (!Array.isArray(value)) return null
  const normalized = value
    .filter((item): item is string => typeof item === "string")
    .map((item) => item.trim())
    .filter((item) => item.length > 0)
  return normalized.length > 0 ? Array.from(new Set(normalized)) : null
}

function normalizeToolChoice(value: unknown): PromptToolChoice {
  if (value == null) return null
  if (value === "auto" || value === "none" || value === "required") {
    return value
  }
  if (typeof value === "string") {
    const trimmed = value.trim()
    if (!trimmed) return null
    return {
      type: "named",
      name: trimmed,
    }
  }
  if (
    isObjectRecord(value) &&
    value.type === "named" &&
    typeof value.name === "string" &&
    value.name.trim().length > 0
  ) {
    return {
      type: "named",
      name: value.name.trim(),
    }
  }
  return null
}

function normalizeToolConfig(value: unknown): PromptConfigDraft["tools"] {
  if (!isObjectRecord(value)) return null
  const modeRaw = value.tool_mode
  const mode =
    modeRaw === "required" || modeRaw === "optional" || modeRaw === "none"
      ? modeRaw
      : "none"
  return {
    tool_mode: mode,
    tool_choice: normalizeToolChoice(value.tool_choice),
    tool_allowlist: Array.isArray(value.tool_allowlist)
      ? Array.from(
          new Set(
            value.tool_allowlist
              .filter((item): item is string => typeof item === "string")
              .map((item) => item.trim())
              .filter((item) => item.length > 0),
          ),
        )
      : null,
    max_tool_calls:
      typeof value.max_tool_calls === "number" ? value.max_tool_calls : null,
    builtin: Array.isArray(value.builtin)
      ? value.builtin.filter((item): item is Record<string, unknown> =>
          isObjectRecord(item),
        )
      : null,
    mcp: isObjectRecord(value.mcp)
      ? {
          servers: Array.isArray(value.mcp.servers)
            ? value.mcp.servers
                .filter((server): server is Record<string, unknown> =>
                  isObjectRecord(server),
                )
                .map((server) => ({
                  id:
                    typeof server.id === "string" ? server.id.trim() : "server",
                  url:
                    typeof server.url === "string"
                      ? server.url.trim() || null
                      : null,
                  allowed_tools: Array.isArray(server.allowed_tools)
                    ? server.allowed_tools.filter(
                        (item): item is string => typeof item === "string",
                      )
                    : null,
                  require_approval:
                    server.require_approval === "always" ||
                    server.require_approval === "never"
                      ? server.require_approval
                      : null,
                }))
            : null,
          allowed_tools: Array.isArray(value.mcp.allowed_tools)
            ? value.mcp.allowed_tools.filter(
                (item): item is string => typeof item === "string",
              )
            : null,
        }
      : null,
  }
}

function getCoreCapabilityHooks(key: string): PromptCapabilityHooks {
  if (
    key === "provider.user_access_provider_id" ||
    key === "model.model_id" ||
    key === "provider.provider_kind"
  ) {
    return {
      normalizeValue: (value) => asTrimmedString(value),
    }
  }
  if (key === "params.stop") {
    return {
      normalizeValue: (value) => normalizeStopSequences(value),
      semanticValidators: [
        ({ draft }) => {
          const stop = draft.params.stop
          if (!Array.isArray(stop)) return []
          if (stop.length <= 8) return []
          return [
            {
              code: "stop_sequence_count_high",
              severity: "warning",
              message:
                "Many stop sequences configured (>8); verify provider behavior.",
              path: "params.stop",
            },
          ]
        },
      ],
    }
  }
  if (key === "tools") {
    return {
      normalizeValue: (value) => normalizeToolConfig(value),
      semanticValidators: [
        ({ draft }) => {
          if (!draft.tools || draft.tools.tool_mode !== "required") return []
          if ((draft.tools.tool_allowlist?.length ?? 0) > 0) return []
          return [
            {
              code: "tool_mode_required_without_allowlist",
              severity: "warning",
              message: "tool_mode is required but tool_allowlist is empty.",
              path: "tools",
            },
          ]
        },
        ({ draft }) => {
          if (!draft.tools || draft.tools.max_tool_calls == null) return []
          if (
            Number.isFinite(draft.tools.max_tool_calls) &&
            draft.tools.max_tool_calls > 0
          ) {
            return []
          }
          return [
            {
              code: "max_tool_calls_invalid",
              severity: "error",
              message: "tools.max_tool_calls must be a positive number.",
              path: "tools.max_tool_calls",
            },
          ]
        },
      ],
    }
  }
  if (key === "input.messages") {
    return {
      semanticValidators: [
        ({ draft }) => {
          if (draft.input.kind !== "messages") return []
          if (draft.input.messages.length > 0) return []
          return [
            {
              code: "messages_input_empty",
              severity: "warning",
              message: "Input kind is messages but no messages are defined.",
              path: "input.messages",
            },
          ]
        },
      ],
    }
  }
  return {}
}

function mergeCapabilityHooks(
  base: PromptCapabilityHooks | undefined,
  extension: PromptCapabilityHooks | undefined,
): PromptCapabilityHooks {
  if (!base && !extension) return {}
  const mergedValidators = [
    ...(base?.semanticValidators ?? []),
    ...(extension?.semanticValidators ?? []),
  ]
  return {
    ...base,
    ...extension,
    semanticValidators:
      mergedValidators.length > 0 ? mergedValidators : undefined,
  }
}

const CORE_PROMPT_CAPABILITIES: PromptCapability[] =
  PROMPT_BUILDER_FIELD_SPECS.map((field) => ({
    ...field,
    hooks: getCoreCapabilityHooks(field.key),
  }))

function sortedPacks(
  packs: PromptCapabilityRegistryPack[],
): PromptCapabilityRegistryPack[] {
  return [...packs].sort((left, right) => {
    const leftOrder = left.order ?? 1000
    const rightOrder = right.order ?? 1000
    if (leftOrder !== rightOrder) return leftOrder - rightOrder
    return left.id.localeCompare(right.id)
  })
}

function resolveCollision(
  existing: PromptCapability,
  incoming: PromptCapability,
  policy: PromptCapabilityConflictPolicy,
): PromptCapability {
  if (policy === "keep_existing") {
    return existing
  }
  if (policy === "replace_existing") {
    return {
      ...incoming,
      hooks: mergeCapabilityHooks(existing.hooks, incoming.hooks),
    }
  }
  throw new Error(`Prompt capability registry conflict (${incoming.key})`)
}

export function buildPromptCapabilityRegistry(
  options: PromptCapabilityRegistryBuildOptions = {},
): PromptCapabilityRegistry {
  const includeCoreCapabilities = options.includeCoreCapabilities ?? true
  const conflictPolicy = options.conflictPolicy ?? "keep_existing"
  const packs = sortedPacks(options.packs ?? [])

  const capabilities: PromptCapability[] = []
  const keyToPackId = new Map<string, string>()
  const conflicts: PromptCapabilityRegistryConflict[] = []

  function addCapability(capability: PromptCapability, packId: string) {
    const existingIndex = capabilities.findIndex(
      (item) => item.key === capability.key,
    )
    if (existingIndex === -1) {
      capabilities.push(capability)
      keyToPackId.set(capability.key, packId)
      return
    }
    const existing = capabilities[existingIndex]
    const existingPackId = keyToPackId.get(capability.key) ?? "unknown"
    conflicts.push({
      key: capability.key,
      existingPackId,
      incomingPackId: packId,
      policy: conflictPolicy,
    })
    const resolved = resolveCollision(existing, capability, conflictPolicy)
    capabilities[existingIndex] = resolved
    if (conflictPolicy === "replace_existing") {
      keyToPackId.set(capability.key, packId)
    }
  }

  if (includeCoreCapabilities) {
    for (const capability of CORE_PROMPT_CAPABILITIES) {
      addCapability(capability, "core")
    }
  }

  for (const pack of packs) {
    for (const capability of pack.capabilities ?? []) {
      addCapability(capability, pack.id)
    }
  }

  return {
    capabilities,
    conflicts,
  }
}

const DEFAULT_PROMPT_REGISTRY = buildPromptCapabilityRegistry()

export const PROMPT_CAPABILITIES = DEFAULT_PROMPT_REGISTRY.capabilities
export const PROMPT_CAPABILITY_CONFLICTS = DEFAULT_PROMPT_REGISTRY.conflicts

export function getPromptCapabilityByKey(key: string): PromptCapability | null {
  return (
    PROMPT_CAPABILITIES.find((capability) => capability.key === key) ?? null
  )
}

export function normalizePromptCapabilityValue(
  capability: PromptCapability,
  value: unknown,
  draft: PromptConfigDraft,
): unknown {
  const normalizer = capability.hooks?.normalizeValue
  if (!normalizer) return value
  return normalizer(value, {
    capabilityKey: capability.key,
    draft,
  })
}

export function runPromptCapabilitySemanticValidators(
  capability: PromptCapability,
  draft: PromptConfigDraft,
): PromptCapabilitySemanticIssue[] {
  const validators = capability.hooks?.semanticValidators ?? []
  if (validators.length === 0) return []
  return validators.flatMap((validator) =>
    validator({
      capabilityKey: capability.key,
      draft,
    }),
  )
}

export function getPromptCapabilityCoverageGaps(
  registry: PromptCapabilityRegistry = DEFAULT_PROMPT_REGISTRY,
): PromptCapabilityCoverageGaps {
  const registryKeys = new Set(
    registry.capabilities.map((capability) => capability.key),
  )
  const missingCapabilities = PROMPT_BUILDER_FIELD_SPECS.map(
    (field) => field.key,
  ).filter((key) => !registryKeys.has(key))
  return { missingCapabilities }
}

export function validatePromptDraftWithCapabilityHooks(
  input: PromptConfigDraft,
  context?: PromptSemanticValidationContext,
  registry: PromptCapabilityRegistry = DEFAULT_PROMPT_REGISTRY,
): PromptSemanticIssue[] {
  const draft = normalizePromptDraft(input)
  const issues: PromptSemanticIssue[] = [
    ...validatePromptDraftSemantics(draft, context),
  ]
  for (const capability of registry.capabilities) {
    const capabilityIssues = runPromptCapabilitySemanticValidators(
      capability,
      draft,
    ).map((issue) => ({
      code: issue.code as PromptSemanticIssue["code"],
      severity: issue.severity,
      message: issue.message,
      path: issue.path,
    }))
    issues.push(...capabilityIssues)
  }
  return issues
}

export function getPromptCapabilityRegistrySnapshot(
  registry: PromptCapabilityRegistry = DEFAULT_PROMPT_REGISTRY,
): {
  capabilities: PromptCapability[]
  conflicts: PromptCapabilityRegistryConflict[]
} {
  return {
    capabilities: registry.capabilities.map((capability) => ({
      ...capability,
    })),
    conflicts: [...registry.conflicts],
  }
}

// Helper for day-one editor usage while route wiring is incomplete.
export function createPromptDraftForCapabilityTests(): PromptConfigDraft {
  return createEmptyPromptDraft({
    provider: {
      user_access_provider_id: "provider-1",
      provider_type_id: "ptype-openai",
      provider_kind: "openai_compatible",
      base_url: "https://api.example.com/v1",
      account_label: "Default Provider",
    },
    model: {
      model_catalog_id: "model-1",
      model_id: "gpt-4o",
      model_name: "GPT 4o",
      model_family: "gpt",
    },
    input: {
      kind: "simple_text",
      text: "Summarize the latest deployment notes.",
    },
  })
}
