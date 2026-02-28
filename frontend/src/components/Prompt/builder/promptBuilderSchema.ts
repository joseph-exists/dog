import type {
  LLMModelPublic,
  UserAccessProviderPublic,
} from "@/client/types.gen"

// ============================================================================
// Prompt Builder Schema (M1)
// ============================================================================
// Frontend authoring/view-model layer for Prompt Builder.
// This is intentionally contract-safe and can evolve without forcing persisted
// contract churn in backend DTOs.

export type PromptProviderKind =
  | "openai_compatible"
  | "openai"
  | "anthropic"
  | "google"
  | "xai"
  | "custom"

export type PromptInputKind = "simple_text" | "messages"
export type PromptMessageRole = "system" | "user" | "assistant" | "tool"

export type PromptBuilderFieldControl =
  | "text"
  | "number"
  | "boolean"
  | "enum"
  | "json"
  | "id"

export interface PromptBuilderFieldSpec {
  key: string
  label: string
  control: PromptBuilderFieldControl
  description?: string
  required?: boolean
  enumValues?: readonly string[]
  placeholder?: string
  category?: "provider" | "model" | "input" | "params" | "tools" | "advanced"
}

export interface PromptProviderBinding {
  user_access_provider_id: string | null
  provider_type_id: string | null
  provider_kind: PromptProviderKind | null
  base_url: string | null
  account_label: string | null
}

export interface PromptModelBinding {
  model_catalog_id: string | null
  model_id: string | null
  model_name: string | null
  model_family: string | null
}

export type PromptInputPayload =
  | {
      kind: "simple_text"
      text: string
    }
  | {
      kind: "messages"
      system?: string
      messages: Array<{ role: PromptMessageRole; content: string }>
    }

function normalizePromptMessageRole(value: unknown): PromptMessageRole {
  if (
    value === "system" ||
    value === "user" ||
    value === "assistant" ||
    value === "tool"
  ) {
    return value
  }
  return "user"
}

export interface PromptParamsCommon {
  temperature?: number | null
  top_p?: number | null
  max_output_tokens?: number | null
  stop?: string[] | null
  seed?: number | null
  response_format?:
    | {
        type: "text" | "json_object"
      }
    | {
        type: "json_schema"
        json_schema: {
          name: string
          schema: Record<string, unknown>
          strict?: boolean | null
        }
      }
    | null
  // Deprecated compatibility alias. Normalized into response_format.
  response_format_json?: boolean | null
  openai?: {
    previous_response_id?: string | null
    reasoning?: {
      summary?: "auto" | "concise" | "detailed" | null
    } | null
  } | null
}

export type PromptParamsByProvider = PromptParamsCommon & {
  provider_kind: PromptProviderKind
  parallel_tool_calls?: boolean | null
  reasoning_effort?: "low" | "medium" | "high" | null
  top_k?: number | null
}

export interface PromptToolingConfig {
  tool_mode?: "none" | "optional" | "required"
  tool_allowlist?: string[] | null
  tool_choice?:
    | "auto"
    | "none"
    | "required"
    | {
        type: "named"
        name: string
      }
    | null
  max_tool_calls?: number | null
  builtin?: Array<Record<string, unknown>> | null
  mcp?: {
    servers?: Array<{
      id: string
      url?: string | null
      allowed_tools?: string[] | null
      require_approval?: "always" | "never" | null
    }> | null
    allowed_tools?: string[] | null
  } | null
}

export interface PromptBuilderMetadata {
  tags?: string[]
  notes?: string | null
  template_id?: string | null
  template_setup?: Record<string, unknown> | null
}

export interface PromptConfigDraft {
  id: string
  owner_id: string | null
  provider: PromptProviderBinding
  model: PromptModelBinding
  input: PromptInputPayload
  params: PromptParamsByProvider
  tools: PromptToolingConfig | null
  metadata: PromptBuilderMetadata | null
}

export interface PromptSemanticIssue {
  code:
    | "provider_required"
    | "provider_disabled"
    | "provider_unvalidated"
    | "model_required"
    | "provider_model_mismatch"
    | "input_required"
    | "param_out_of_range"
    | "provider_param_unrecognized"
    | "provider_kind_mismatch"
    | "json_mode_not_supported"
    | "function_calling_not_supported"
    | "anthropic_top_k_without_anthropic_provider"
    | "reasoning_effort_without_openai_provider"
  severity: "error" | "warning"
  message: string
  path?: string
}

export interface PromptSemanticValidationContext {
  selectedProvider?: UserAccessProviderPublic | null
  selectedModel?: LLMModelPublic | null
}

export const PROMPT_PROVIDER_KIND_VALUES: PromptProviderKind[] = [
  "openai_compatible",
  "openai",
  "anthropic",
  "google",
  "xai",
  "custom",
]

export const PROMPT_INPUT_KIND_VALUES: PromptInputKind[] = [
  "simple_text",
  "messages",
]

export const PROMPT_BUILDER_FIELD_SPECS: PromptBuilderFieldSpec[] = [
  {
    key: "provider.user_access_provider_id",
    label: "Access Provider",
    control: "id",
    required: true,
    category: "provider",
  },
  {
    key: "provider.provider_kind",
    label: "Provider Kind",
    control: "enum",
    enumValues: PROMPT_PROVIDER_KIND_VALUES,
    category: "provider",
  },
  {
    key: "model.model_id",
    label: "Model",
    control: "id",
    required: true,
    category: "model",
  },
  {
    key: "input.kind",
    label: "Input Kind",
    control: "enum",
    enumValues: PROMPT_INPUT_KIND_VALUES,
    category: "input",
  },
  {
    key: "input.text",
    label: "Prompt Text",
    control: "text",
    category: "input",
  },
  {
    key: "input.messages",
    label: "Messages",
    control: "json",
    category: "input",
  },
  {
    key: "params.temperature",
    label: "Temperature",
    control: "number",
    category: "params",
  },
  {
    key: "params.top_p",
    label: "Top P",
    control: "number",
    category: "params",
  },
  {
    key: "params.max_output_tokens",
    label: "Max Output Tokens",
    control: "number",
    category: "params",
  },
  {
    key: "params.stop",
    label: "Stop Sequences",
    control: "json",
    category: "params",
  },
  {
    key: "params.response_format",
    label: "Response Format",
    control: "json",
    category: "params",
  },
  {
    key: "params.openai.previous_response_id",
    label: "Previous Response ID",
    control: "text",
    category: "advanced",
  },
  {
    key: "params.openai.reasoning",
    label: "OpenAI Reasoning",
    control: "json",
    category: "advanced",
  },
  {
    key: "tools",
    label: "Tool Config",
    control: "json",
    category: "tools",
  },
  {
    key: "metadata",
    label: "Metadata",
    control: "json",
    category: "advanced",
  },
]

function isObjectRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value)
}

function normalizePromptInputPayload(input: unknown): PromptInputPayload {
  if (!isObjectRecord(input)) {
    return {
      kind: "simple_text",
      text: "",
    }
  }

  const kind = input.kind === "messages" ? "messages" : "simple_text"
  if (kind === "messages") {
    const rawMessages = Array.isArray(input.messages) ? input.messages : []
    const messages = rawMessages
      .filter((msg): msg is Record<string, unknown> => isObjectRecord(msg))
      .map((msg) => ({
        role: normalizePromptMessageRole(msg.role),
        content: typeof msg.content === "string" ? msg.content : "",
      }))
    return {
      kind: "messages",
      system: typeof input.system === "string" ? input.system : undefined,
      messages,
    }
  }

  return {
    kind: "simple_text",
    text: typeof input.text === "string" ? input.text : "",
  }
}

function normalizePromptResponseFormat(
  value: unknown,
): PromptParamsCommon["response_format"] {
  if (!isObjectRecord(value)) return null
  const rawType = value.type
  if (rawType === "text" || rawType === "json_object") {
    return { type: rawType }
  }
  if (rawType === "json_schema") {
    const jsonSchema = value.json_schema
    if (!isObjectRecord(jsonSchema)) return null
    const name =
      typeof jsonSchema.name === "string" && jsonSchema.name.trim().length > 0
        ? jsonSchema.name.trim()
        : "response_schema"
    const schema = isObjectRecord(jsonSchema.schema) ? jsonSchema.schema : {}
    return {
      type: "json_schema",
      json_schema: {
        name,
        schema,
        strict:
          typeof jsonSchema.strict === "boolean" ? jsonSchema.strict : undefined,
      },
    }
  }
  return null
}

function normalizePromptToolChoice(
  value: unknown,
): PromptToolingConfig["tool_choice"] {
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
  if (isObjectRecord(value) && value.type === "named") {
    const name = typeof value.name === "string" ? value.name.trim() : ""
    if (!name) return null
    return {
      type: "named",
      name,
    }
  }
  return null
}

function normalizePromptParams(input: unknown): PromptParamsByProvider {
  const raw = isObjectRecord(input) ? input : {}
  const rawProviderKind = raw.provider_kind
  const providerKind: PromptProviderKind =
    rawProviderKind === "openai_compatible" ||
    rawProviderKind === "openai" ||
    rawProviderKind === "anthropic" ||
    rawProviderKind === "google" ||
    rawProviderKind === "xai" ||
    rawProviderKind === "custom"
      ? rawProviderKind
      : "openai_compatible"
  const responseFormat = normalizePromptResponseFormat(raw.response_format)
  const responseFormatJsonLegacy =
    typeof raw.response_format_json === "boolean" ? raw.response_format_json : null
  const resolvedResponseFormat =
    responseFormat ??
    (responseFormatJsonLegacy === true
      ? ({ type: "json_object" } as const)
      : null)

  const openai = isObjectRecord(raw.openai)
    ? {
        previous_response_id:
          typeof raw.openai.previous_response_id === "string"
            ? raw.openai.previous_response_id.trim() || null
            : null,
        reasoning: isObjectRecord(raw.openai.reasoning)
          ? {
              summary:
                raw.openai.reasoning.summary === "auto" ||
                raw.openai.reasoning.summary === "concise" ||
                raw.openai.reasoning.summary === "detailed"
                  ? raw.openai.reasoning.summary
                  : null,
            }
          : null,
      }
    : null

  return {
    provider_kind: providerKind,
    temperature: typeof raw.temperature === "number" ? raw.temperature : null,
    top_p: typeof raw.top_p === "number" ? raw.top_p : null,
    max_output_tokens:
      typeof raw.max_output_tokens === "number" ? raw.max_output_tokens : null,
    stop: Array.isArray(raw.stop)
      ? raw.stop.filter((item): item is string => typeof item === "string")
      : null,
    seed: typeof raw.seed === "number" ? raw.seed : null,
    response_format: resolvedResponseFormat,
    response_format_json: responseFormatJsonLegacy,
    openai,
    parallel_tool_calls:
      typeof raw.parallel_tool_calls === "boolean"
        ? raw.parallel_tool_calls
        : null,
    reasoning_effort:
      raw.reasoning_effort === "low" ||
      raw.reasoning_effort === "medium" ||
      raw.reasoning_effort === "high"
        ? raw.reasoning_effort
        : null,
    top_k: typeof raw.top_k === "number" ? raw.top_k : null,
  } as PromptParamsByProvider
}

function normalizePromptTools(input: unknown): PromptToolingConfig | null {
  if (!isObjectRecord(input)) return null
  const mode =
    input.tool_mode === "none" ||
    input.tool_mode === "optional" ||
    input.tool_mode === "required"
      ? input.tool_mode
      : "none"
  return {
    tool_mode: mode,
    tool_allowlist: Array.isArray(input.tool_allowlist)
      ? Array.from(
          new Set(
            input.tool_allowlist
              .filter((item): item is string => typeof item === "string")
              .map((item) => item.trim())
              .filter((item) => item.length > 0),
          ),
        )
      : null,
    tool_choice: normalizePromptToolChoice(input.tool_choice),
    max_tool_calls:
      typeof input.max_tool_calls === "number" ? input.max_tool_calls : null,
    builtin: Array.isArray(input.builtin)
      ? input.builtin.filter((item): item is Record<string, unknown> =>
          isObjectRecord(item),
        )
      : null,
    mcp: isObjectRecord(input.mcp)
      ? {
          servers: Array.isArray(input.mcp.servers)
            ? input.mcp.servers
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
          allowed_tools: Array.isArray(input.mcp.allowed_tools)
            ? input.mcp.allowed_tools.filter(
                (item): item is string => typeof item === "string",
              )
            : null,
        }
      : null,
  }
}

export function createEmptyPromptDraft(
  overrides?: Partial<PromptConfigDraft>,
): PromptConfigDraft {
  return {
    id: overrides?.id ?? "",
    owner_id: overrides?.owner_id ?? null,
    provider: {
      user_access_provider_id:
        overrides?.provider?.user_access_provider_id ?? null,
      provider_type_id: overrides?.provider?.provider_type_id ?? null,
      provider_kind: overrides?.provider?.provider_kind ?? null,
      base_url: overrides?.provider?.base_url ?? null,
      account_label: overrides?.provider?.account_label ?? null,
    },
    model: {
      model_catalog_id: overrides?.model?.model_catalog_id ?? null,
      model_id: overrides?.model?.model_id ?? null,
      model_name: overrides?.model?.model_name ?? null,
      model_family: overrides?.model?.model_family ?? null,
    },
    input: normalizePromptInputPayload(overrides?.input),
    params: overrides?.params ?? {
      provider_kind: "openai_compatible",
      temperature: 0.7,
      top_p: null,
      max_output_tokens: null,
      stop: null,
      seed: null,
      response_format: null,
      response_format_json: null,
      openai: null,
      parallel_tool_calls: null,
      reasoning_effort: null,
      top_k: null,
    },
    tools: normalizePromptTools(overrides?.tools),
    metadata: overrides?.metadata ?? null,
  }
}

export function normalizePromptDraft(
  input?: Partial<PromptConfigDraft> | null,
): PromptConfigDraft {
  const base = createEmptyPromptDraft(input ?? undefined)
  return {
    ...base,
    provider: {
      ...base.provider,
      user_access_provider_id:
        typeof base.provider.user_access_provider_id === "string"
          ? base.provider.user_access_provider_id.trim() || null
          : null,
      provider_type_id:
        typeof base.provider.provider_type_id === "string"
          ? base.provider.provider_type_id.trim() || null
          : null,
      base_url:
        typeof base.provider.base_url === "string"
          ? base.provider.base_url.trim() || null
          : null,
      account_label:
        typeof base.provider.account_label === "string"
          ? base.provider.account_label.trim() || null
          : null,
    },
    model: {
      ...base.model,
      model_catalog_id:
        typeof base.model.model_catalog_id === "string"
          ? base.model.model_catalog_id.trim() || null
          : null,
      model_id:
        typeof base.model.model_id === "string"
          ? base.model.model_id.trim() || null
          : null,
      model_name:
        typeof base.model.model_name === "string"
          ? base.model.model_name.trim() || null
          : null,
      model_family:
        typeof base.model.model_family === "string"
          ? base.model.model_family.trim() || null
          : null,
    },
    input: normalizePromptInputPayload(base.input),
    params: normalizePromptParams(base.params),
    tools: normalizePromptTools(base.tools),
  }
}

function hasPromptInput(input: PromptInputPayload): boolean {
  if (input.kind === "simple_text") {
    return input.text.trim().length > 0
  }
  if ((input.system ?? "").trim().length > 0) return true
  return input.messages.some((msg) => msg.content.trim().length > 0)
}

function validateCommonParameterRanges(
  params: PromptParamsCommon,
): PromptSemanticIssue[] {
  const issues: PromptSemanticIssue[] = []
  const numericChecks: Array<{
    value: number | null | undefined
    min: number
    max: number
    key: string
    label: string
  }> = [
    {
      value: params.temperature,
      min: 0,
      max: 2,
      key: "temperature",
      label: "temperature",
    },
    { value: params.top_p, min: 0, max: 1, key: "top_p", label: "top_p" },
  ]
  for (const check of numericChecks) {
    if (check.value == null) continue
    if (
      Number.isFinite(check.value) &&
      (check.value < check.min || check.value > check.max)
    ) {
      issues.push({
        code: "param_out_of_range",
        severity: "error",
        message: `Parameter "${check.label}" must be between ${check.min} and ${check.max}.`,
        path: `params.${check.key}`,
      })
    }
  }
  if (
    params.max_output_tokens != null &&
    (!Number.isFinite(params.max_output_tokens) ||
      params.max_output_tokens <= 0)
  ) {
    issues.push({
      code: "param_out_of_range",
      severity: "error",
      message: 'Parameter "max_output_tokens" must be a positive number.',
      path: "params.max_output_tokens",
    })
  }
  return issues
}

function validateProviderSpecificParamsStub(
  draft: PromptConfigDraft,
  context?: PromptSemanticValidationContext,
): PromptSemanticIssue[] {
  const issues: PromptSemanticIssue[] = []
  const selectedModel = context?.selectedModel
  const providerKind = draft.provider.provider_kind
  const paramsProviderKind = draft.params.provider_kind

  if (
    providerKind &&
    paramsProviderKind &&
    providerKind !== paramsProviderKind
  ) {
    issues.push({
      code: "provider_kind_mismatch",
      severity: "warning",
      message: "Provider kind and params.provider_kind are not aligned.",
      path: "params.provider_kind",
    })
  }

  if (
    ((draft.params.response_format?.type === "json_object" ||
      draft.params.response_format?.type === "json_schema") &&
      selectedModel?.has_json_mode === false) ||
    (draft.params.response_format_json === true &&
      selectedModel?.has_json_mode === false)
  ) {
    issues.push({
      code: "json_mode_not_supported",
      severity: "error",
      message: "Selected model does not support JSON mode.",
      path:
        draft.params.response_format?.type != null
          ? "params.response_format"
          : "params.response_format_json",
    })
  }

  if (
    draft.tools?.max_tool_calls != null &&
    (!Number.isFinite(draft.tools.max_tool_calls) ||
      draft.tools.max_tool_calls <= 0)
  ) {
    issues.push({
      code: "param_out_of_range",
      severity: "error",
      message: 'Parameter "tools.max_tool_calls" must be a positive number.',
      path: "tools.max_tool_calls",
    })
  }

  const requiresFunctionCalling =
    ("parallel_tool_calls" in draft.params &&
      draft.params.parallel_tool_calls === true) ||
    draft.tools?.tool_mode === "required"

  if (
    requiresFunctionCalling &&
    selectedModel?.has_function_calling === false
  ) {
    issues.push({
      code: "function_calling_not_supported",
      severity: "error",
      message: "Selected model does not support function/tool calling.",
      path: "tools",
    })
  }

  if (
    "top_k" in draft.params &&
    draft.params.top_k != null &&
    providerKind !== "anthropic"
  ) {
    issues.push({
      code: "anthropic_top_k_without_anthropic_provider",
      severity: "warning",
      message:
        'Parameter "top_k" is typically valid only for anthropic providers.',
      path: "params.top_k",
    })
  }

  if (
    "reasoning_effort" in draft.params &&
    draft.params.reasoning_effort != null &&
    providerKind &&
    providerKind !== "openai" &&
    providerKind !== "openai_compatible"
  ) {
    issues.push({
      code: "reasoning_effort_without_openai_provider",
      severity: "warning",
      message:
        'Parameter "reasoning_effort" is primarily intended for openai/openai_compatible providers.',
      path: "params.reasoning_effort",
    })
  }

  return issues
}

export function validatePromptDraftSemantics(
  input: PromptConfigDraft,
  context?: PromptSemanticValidationContext,
): PromptSemanticIssue[] {
  const draft = normalizePromptDraft(input)
  const issues: PromptSemanticIssue[] = []

  if (!draft.provider.user_access_provider_id) {
    issues.push({
      code: "provider_required",
      severity: "error",
      message: "A user access provider is required.",
      path: "provider.user_access_provider_id",
    })
  }

  if (!draft.model.model_id) {
    issues.push({
      code: "model_required",
      severity: "error",
      message: "A model selection is required.",
      path: "model.model_id",
    })
  }

  if (!hasPromptInput(draft.input)) {
    issues.push({
      code: "input_required",
      severity: "error",
      message: "Prompt input is required.",
      path: "input",
    })
  }

  if (context?.selectedProvider?.is_enabled === false) {
    issues.push({
      code: "provider_disabled",
      severity: "error",
      message: "Selected provider is disabled.",
      path: "provider.user_access_provider_id",
    })
  }

  if (context?.selectedProvider?.is_validated === false) {
    issues.push({
      code: "provider_unvalidated",
      severity: "warning",
      message: "Selected provider has not been validated yet.",
      path: "provider.user_access_provider_id",
    })
  }

  const providerTypeId =
    context?.selectedProvider?.alpha_provider_type_id ?? null
  const modelProviderTypeId =
    context?.selectedModel?.primary_provider_type_id ?? null
  if (
    providerTypeId &&
    modelProviderTypeId &&
    providerTypeId !== modelProviderTypeId
  ) {
    issues.push({
      code: "provider_model_mismatch",
      severity: "error",
      message: "Selected model does not match the selected provider type.",
      path: "model.model_id",
    })
  }

  issues.push(...validateCommonParameterRanges(draft.params))
  issues.push(...validateProviderSpecificParamsStub(draft, context))

  return issues
}
