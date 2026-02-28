import type {
  LLMModelPublic,
  Type1Update,
  Type3Update,
  UserAccessProviderPublic,
  UserAgentConfigPublic,
} from "@/client/types.gen"
import {
  createEmptyPromptDraft,
  normalizePromptDraft,
  type PromptConfigDraft,
  type PromptProviderKind,
  type PromptSemanticValidationContext,
} from "./promptBuilderSchema"

const TYPE1_PROVIDER_TYPE_ID = "673f1787-8474-4e1c-986c-8e19f14c989c"
const TYPE3_PROVIDER_TYPE_ID = "e09ade10-8563-4748-8deb-1a6c87c97134"

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function asNullableString(value: unknown): string | null {
  if (typeof value !== "string") return null
  const trimmed = value.trim()
  return trimmed.length > 0 ? trimmed : null
}

export function inferProviderKindFromProviderTypeName(
  providerTypeName?: string | null,
): PromptProviderKind | null {
  const normalized = providerTypeName?.trim().toLowerCase()
  if (!normalized) return null
  if (normalized === "openai") return "openai"
  if (normalized === "anthropic") return "anthropic"
  if (normalized === "google") return "google"
  if (normalized === "xai") return "xai"
  if (
    normalized.includes("openai") ||
    normalized.includes("azure") ||
    normalized.includes("openrouter") ||
    normalized.includes("ollama")
  ) {
    return "openai_compatible"
  }
  return "custom"
}

function inferModelFamily(modelId?: string | null): string | null {
  const value = asNullableString(modelId)
  if (!value) return null
  if (value.includes("-")) {
    return value.split("-")[0] ?? value
  }
  if (value.includes("/")) {
    return value.split("/")[0] ?? value
  }
  return value
}

function parseToolingConfig(
  toolConfig: UserAgentConfigPublic["tool_config"],
): PromptConfigDraft["tools"] {
  if (!isObjectRecord(toolConfig)) return null
  const toolChoiceRaw = asNullableString(toolConfig.tool_choice)
  const toolChoice =
    toolChoiceRaw === "auto" ||
    toolChoiceRaw === "none" ||
    toolChoiceRaw === "required"
      ? toolChoiceRaw
      : toolChoiceRaw
        ? { type: "named" as const, name: toolChoiceRaw }
        : null
  return {
    tool_mode:
      toolConfig.require_tools === true
        ? "required"
        : toolConfig.enable_tools === true
          ? "optional"
          : "none",
    tool_allowlist: Array.isArray(toolConfig.allowed_tools)
      ? toolConfig.allowed_tools.filter(
          (item): item is string => typeof item === "string",
        )
      : null,
    tool_choice: toolChoice,
  }
}

export function mapUserAgentConfigToPromptDraft(
  agent: UserAgentConfigPublic,
): PromptConfigDraft {
  const modelId =
    asNullableString(agent.model_id) ??
    asNullableString(agent.model) ??
    asNullableString(agent.model_name)

  const systemPrompt =
    asNullableString(agent.custom_system_prompt) ??
    asNullableString(agent.system_prompt) ??
    ""
  const instructions = asNullableString(agent.instructions)

  const paramsSeed = createEmptyPromptDraft().params
  const providerKind =
    inferProviderKindFromProviderTypeName(agent.provider_type) ??
    paramsSeed.provider_kind

  return normalizePromptDraft({
    id: agent.id,
    owner_id: asNullableString(agent.owner_id),
    provider: {
      user_access_provider_id: asNullableString(agent.user_access_provider),
      provider_type_id: null,
      provider_kind: providerKind,
      base_url: null,
      account_label: null,
    },
    model: {
      model_catalog_id: null,
      model_id: modelId,
      model_name: asNullableString(agent.model_name),
      model_family: inferModelFamily(modelId),
    },
    input: {
      kind: "messages",
      system: systemPrompt,
      messages: instructions ? [{ role: "user", content: instructions }] : [],
    },
    params: {
      ...paramsSeed,
      provider_kind: providerKind,
    },
    tools: parseToolingConfig(agent.tool_config),
    metadata: {
      notes: asNullableString(agent.description),
      tags: Array.isArray(agent.capabilities) ? agent.capabilities : [],
      template_id: null,
      template_setup: null,
    },
  })
}

export interface PromptDraftHydrationResult {
  draft: PromptConfigDraft
  selectedProvider: UserAccessProviderPublic | null
  selectedModel: LLMModelPublic | null
}

export function hydratePromptDraftProviderAndModel(
  input: PromptConfigDraft,
  providers: UserAccessProviderPublic[],
  models: LLMModelPublic[],
): PromptDraftHydrationResult {
  const draft = normalizePromptDraft(input)
  const selectedProvider =
    providers.find(
      (provider) => provider.id === draft.provider.user_access_provider_id,
    ) ?? null

  const selectedModel =
    models.find((model) => {
      if (
        draft.model.model_catalog_id &&
        model.id === draft.model.model_catalog_id
      ) {
        return true
      }
      if (draft.model.model_id && model.model_id === draft.model.model_id) {
        return true
      }
      return false
    }) ?? null

  const hydrated: PromptConfigDraft = {
    ...draft,
    provider: {
      ...draft.provider,
      provider_type_id:
        selectedProvider?.alpha_provider_type_id ??
        draft.provider.provider_type_id ??
        null,
      base_url: selectedProvider?.base_url ?? draft.provider.base_url ?? null,
      account_label:
        selectedProvider?.name ?? draft.provider.account_label ?? null,
    },
    model: {
      ...draft.model,
      model_catalog_id:
        selectedModel?.id ?? draft.model.model_catalog_id ?? null,
      model_id: selectedModel?.model_id ?? draft.model.model_id ?? null,
      model_name: selectedModel?.display_name ?? draft.model.model_name ?? null,
      model_family: inferModelFamily(
        selectedModel?.model_id ?? draft.model.model_id,
      ),
    },
  }

  return {
    draft: normalizePromptDraft(hydrated),
    selectedProvider,
    selectedModel,
  }
}

export function buildPromptValidationContext(
  hydration: PromptDraftHydrationResult,
): PromptSemanticValidationContext {
  return {
    selectedProvider: hydration.selectedProvider,
    selectedModel: hydration.selectedModel,
  }
}

function inputToAgentInstructionFields(input: PromptConfigDraft["input"]): {
  custom_system_prompt: string | null
  instructions: string | null
} {
  if (input.kind === "simple_text") {
    return {
      custom_system_prompt: null,
      instructions: asNullableString(input.text),
    }
  }
  const messageText = input.messages
    .map((message) => `[${message.role}] ${message.content}`)
    .join("\n")
  return {
    custom_system_prompt: asNullableString(input.system),
    instructions: asNullableString(messageText),
  }
}

function promptToolsToAgentToolConfig(
  tools: PromptConfigDraft["tools"],
): Record<string, unknown> | null {
  if (!tools) return null
  const normalizedToolChoice =
    typeof tools.tool_choice === "string"
      ? tools.tool_choice
      : tools.tool_choice &&
          typeof tools.tool_choice === "object" &&
          tools.tool_choice.type === "named" &&
          typeof tools.tool_choice.name === "string"
        ? tools.tool_choice.name
        : null
  return {
    enable_tools:
      tools.tool_mode === "optional" || tools.tool_mode === "required",
    require_tools: tools.tool_mode === "required",
    allowed_tools: tools.tool_allowlist ?? [],
    tool_choice: asNullableString(normalizedToolChoice),
  }
}

function resolveAgentProviderTypeLiteral(
  providerTypeId: string | null | undefined,
): Type1Update["provider_type"] | Type3Update["provider_type"] | null {
  if (providerTypeId === TYPE1_PROVIDER_TYPE_ID) return TYPE1_PROVIDER_TYPE_ID
  if (providerTypeId === TYPE3_PROVIDER_TYPE_ID) return TYPE3_PROVIDER_TYPE_ID
  return null
}

export function mapPromptDraftToAgentUpdatePayload(
  draftInput: PromptConfigDraft,
  sourceAgent: UserAgentConfigPublic,
  selectedProvider?: UserAccessProviderPublic | null,
): Type1Update | Type3Update {
  const draft = normalizePromptDraft(draftInput)
  const providerTypeLiteral =
    resolveAgentProviderTypeLiteral(
      selectedProvider?.alpha_provider_type_id ??
        draft.provider.provider_type_id,
    ) ??
    resolveAgentProviderTypeLiteral(sourceAgent.provider_type) ??
    TYPE1_PROVIDER_TYPE_ID
  const mappedInput = inputToAgentInstructionFields(draft.input)

  return {
    name: asNullableString(sourceAgent.name) ?? "Prompt Builder Agent",
    slug: asNullableString(sourceAgent.slug) ?? sourceAgent.id,
    description: asNullableString(draft.metadata?.notes),
    user_access_provider: draft.provider.user_access_provider_id,
    provider_type: providerTypeLiteral,
    model: draft.model.model_id,
    model_id: draft.model.model_id,
    model_name: draft.model.model_name ?? draft.model.model_id ?? "",
    system_prompt: null,
    custom_system_prompt: mappedInput.custom_system_prompt,
    instructions: mappedInput.instructions,
    tool_config: promptToolsToAgentToolConfig(draft.tools),
    deps_config: sourceAgent.deps_config ?? null,
    agent_metadata: {
      ...(isObjectRecord(sourceAgent.agent_metadata)
        ? sourceAgent.agent_metadata
        : {}),
      prompt_builder: {
        metadata: draft.metadata ?? null,
        params: draft.params,
        input_kind: draft.input.kind,
      },
    },
    agent_type: asNullableString(sourceAgent.agent_type) ?? "builder",
    presentation: sourceAgent.presentation ?? null,
    is_enabled: sourceAgent.is_enabled ?? true,
    is_clonable: sourceAgent.is_clonable ?? true,
    is_visible: sourceAgent.is_visible ?? true,
    scope: asNullableString(sourceAgent.scope) ?? "personal",
    participation_mode:
      asNullableString(sourceAgent.participation_mode) ?? "manual",
    is_coordinator: sourceAgent.is_coordinator ?? false,
    max_tool_iterations: sourceAgent.max_tool_iterations ?? 8,
    capabilities: sourceAgent.capabilities ?? [],
  }
}
