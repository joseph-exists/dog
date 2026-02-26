import { expect, test } from "@playwright/test"

import {
  createEmptyPromptDraft,
  normalizePromptDraft,
  PROMPT_BUILDER_FIELD_SPECS,
  validatePromptDraftSemantics,
} from "@/components/Prompt/builder/promptBuilderSchema"

test.describe("promptBuilderSchema defaults", () => {
  test("createEmptyPromptDraft returns canonical defaults", async () => {
    const draft = createEmptyPromptDraft()
    expect(draft.provider.user_access_provider_id).toBeNull()
    expect(draft.model.model_id).toBeNull()
    expect(draft.input.kind).toBe("simple_text")
    expect(draft.params.provider_kind).toBe("openai_compatible")
    expect(draft.tools).toBeNull()
  })

  test("normalizePromptDraft trims id-like string fields", async () => {
    const normalized = normalizePromptDraft({
      provider: {
        user_access_provider_id: "  provider-1  ",
        provider_type_id: "  ptype-1  ",
        provider_kind: "openai_compatible",
        base_url: "  https://example.com  ",
        account_label: "  Work Provider  ",
      },
      model: {
        model_catalog_id: "  model-catalog-1  ",
        model_id: "  gpt-4o  ",
        model_name: "  GPT 4o  ",
        model_family: "  gpt  ",
      },
    })
    expect(normalized.provider.user_access_provider_id).toBe("provider-1")
    expect(normalized.provider.provider_type_id).toBe("ptype-1")
    expect(normalized.provider.base_url).toBe("https://example.com")
    expect(normalized.provider.account_label).toBe("Work Provider")
    expect(normalized.model.model_id).toBe("gpt-4o")
    expect(normalized.model.model_name).toBe("GPT 4o")
  })

  test("normalizePromptDraft hydrates input shape when kind switches to messages", async () => {
    const normalized = normalizePromptDraft({
      input: {
        kind: "messages",
      } as any,
    })
    expect(normalized.input.kind).toBe("messages")
    if (normalized.input.kind !== "messages")
      throw new Error("Expected messages input")
    expect(Array.isArray(normalized.input.messages)).toBeTruthy()
    expect(normalized.input.messages).toEqual([])
  })
})

test.describe("promptBuilderSchema field specs", () => {
  test("exposes required provider/model/input controls", async () => {
    const keys = PROMPT_BUILDER_FIELD_SPECS.map((field) => field.key)
    expect(keys).toEqual(
      expect.arrayContaining([
        "provider.user_access_provider_id",
        "provider.provider_kind",
        "model.model_id",
        "input.kind",
        "input.text",
        "params.temperature",
        "metadata",
      ]),
    )
  })
})

test.describe("promptBuilderSchema semantic validation", () => {
  test("flags required fields when missing", async () => {
    const draft = createEmptyPromptDraft()
    const issues = validatePromptDraftSemantics(draft)
    expect(
      issues.some((issue) => issue.code === "provider_required"),
    ).toBeTruthy()
    expect(issues.some((issue) => issue.code === "model_required")).toBeTruthy()
    expect(issues.some((issue) => issue.code === "input_required")).toBeTruthy()
  })

  test("accepts valid minimal prompt draft", async () => {
    const draft = createEmptyPromptDraft({
      provider: {
        user_access_provider_id: "provider-1",
        provider_type_id: null,
        provider_kind: "openai_compatible",
        base_url: null,
        account_label: null,
      },
      model: {
        model_catalog_id: null,
        model_id: "gpt-4o",
        model_name: "GPT 4o",
        model_family: "gpt",
      },
      input: {
        kind: "simple_text",
        text: "Write a one-line haiku about tests.",
      },
    })
    const issues = validatePromptDraftSemantics(draft)
    expect(issues.filter((issue) => issue.severity === "error")).toEqual([])
  })

  test("flags provider-model mismatch and disabled provider from context", async () => {
    const draft = createEmptyPromptDraft({
      provider: {
        user_access_provider_id: "provider-1",
        provider_type_id: "provider-type-a",
        provider_kind: "openai_compatible",
        base_url: null,
        account_label: null,
      },
      model: {
        model_catalog_id: "model-1",
        model_id: "gpt-4o",
        model_name: "GPT 4o",
        model_family: "gpt",
      },
      input: {
        kind: "simple_text",
        text: "Hello",
      },
    })

    const issues = validatePromptDraftSemantics(draft, {
      selectedProvider: {
        id: "provider-1",
        name: "Work Provider",
        base_url: "https://example.com",
        alpha_provider_type_id: "provider-type-a",
        is_enabled: false,
        is_validated: false,
      },
      selectedModel: {
        id: "model-1",
        model_id: "gpt-4o",
        display_name: "GPT 4o",
        primary_provider_type_id: "provider-type-b",
      },
    })

    expect(
      issues.some((issue) => issue.code === "provider_disabled"),
    ).toBeTruthy()
    expect(
      issues.some((issue) => issue.code === "provider_unvalidated"),
    ).toBeTruthy()
    expect(
      issues.some((issue) => issue.code === "provider_model_mismatch"),
    ).toBeTruthy()
  })

  test("flags out-of-range common parameters", async () => {
    const draft = createEmptyPromptDraft({
      provider: {
        user_access_provider_id: "provider-1",
        provider_type_id: null,
        provider_kind: "openai_compatible",
        base_url: null,
        account_label: null,
      },
      model: {
        model_catalog_id: null,
        model_id: "gpt-4o",
        model_name: "GPT 4o",
        model_family: "gpt",
      },
      input: {
        kind: "simple_text",
        text: "Hi",
      },
      params: {
        provider_kind: "openai_compatible",
        temperature: 3,
        top_p: -0.2,
        max_output_tokens: 0,
      },
    })
    const issues = validatePromptDraftSemantics(draft)
    expect(
      issues.filter((issue) => issue.code === "param_out_of_range").length,
    ).toBe(3)
  })

  test("flags provider/model capability compatibility issues", async () => {
    const draft = createEmptyPromptDraft({
      provider: {
        user_access_provider_id: "provider-1",
        provider_type_id: "provider-type-a",
        provider_kind: "anthropic",
        base_url: null,
        account_label: null,
      },
      model: {
        model_catalog_id: "model-1",
        model_id: "claude-test",
        model_name: "Claude Test",
        model_family: "claude",
      },
      input: {
        kind: "simple_text",
        text: "Hi",
      },
      params: {
        provider_kind: "openai_compatible",
        response_format_json: true,
        parallel_tool_calls: true,
        reasoning_effort: "high",
      },
      tools: {
        tool_mode: "required",
        tool_allowlist: ["search"],
        tool_choice: null,
      },
    })
    const issues = validatePromptDraftSemantics(draft, {
      selectedProvider: {
        id: "provider-1",
        name: "Anthropic Provider",
        alpha_provider_type_id: "provider-type-a",
      },
      selectedModel: {
        id: "model-1",
        model_id: "claude-test",
        display_name: "Claude Test",
        primary_provider_type_id: "provider-type-a",
        has_json_mode: false,
        has_function_calling: false,
      },
    })
    expect(
      issues.some((issue) => issue.code === "provider_kind_mismatch"),
    ).toBeTruthy()
    expect(
      issues.some((issue) => issue.code === "json_mode_not_supported"),
    ).toBeTruthy()
    expect(
      issues.some((issue) => issue.code === "function_calling_not_supported"),
    ).toBeTruthy()
    expect(
      issues.some(
        (issue) => issue.code === "reasoning_effort_without_openai_provider",
      ),
    ).toBeTruthy()
  })
})
