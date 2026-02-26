import { expect, test } from "@playwright/test"

import type {
  LLMModelPublic,
  UserAccessProviderPublic,
  UserAgentConfigPublic,
} from "@/client/types.gen"
import {
  buildPromptValidationContext,
  hydratePromptDraftProviderAndModel,
  inferProviderKindFromProviderTypeName,
  mapPromptDraftToAgentUpdatePayload,
  mapUserAgentConfigToPromptDraft,
} from "@/components/Prompt/builder/promptBuilderAdapters"

const PROVIDERS: UserAccessProviderPublic[] = [
  {
    id: "provider-1",
    name: "Work OpenAI",
    base_url: "https://api.openai.com/v1",
    alpha_provider_type_id: "ptype-openai",
    is_enabled: true,
    is_validated: true,
  },
]

const MODELS: LLMModelPublic[] = [
  {
    id: "model-1",
    model_id: "gpt-4o",
    display_name: "GPT 4o",
    primary_provider_type_id: "ptype-openai",
  },
]

function createAgent(
  overrides?: Partial<UserAgentConfigPublic>,
): UserAgentConfigPublic {
  return {
    id: "agent-1",
    created_at: "2026-02-24T00:00:00Z",
    updated_at: null,
    version: 1,
    ...overrides,
  }
}

test.describe("promptBuilderAdapters inference", () => {
  test("maps known provider names to provider kind", async () => {
    expect(inferProviderKindFromProviderTypeName("openai")).toBe("openai")
    expect(inferProviderKindFromProviderTypeName("anthropic")).toBe("anthropic")
    expect(inferProviderKindFromProviderTypeName("Azure OpenAI")).toBe(
      "openai_compatible",
    )
    expect(inferProviderKindFromProviderTypeName("unknown-provider")).toBe(
      "custom",
    )
    expect(inferProviderKindFromProviderTypeName(null)).toBeNull()
  })
})

test.describe("promptBuilderAdapters mapping", () => {
  test("maps UserAgentConfigPublic to prompt draft", async () => {
    const agent = createAgent({
      owner_id: "user-1",
      user_access_provider: "provider-1",
      provider_type: "openai",
      model_id: "gpt-4o",
      model_name: "GPT 4o",
      custom_system_prompt: "You are concise.",
      instructions: "Answer in one paragraph.",
      description: "Prompt test",
      capabilities: ["summarize", "rewrite"],
      tool_config: {
        require_tools: true,
        allowed_tools: ["search", "python"],
      },
    })

    const draft = mapUserAgentConfigToPromptDraft(agent)

    expect(draft.id).toBe("agent-1")
    expect(draft.provider.user_access_provider_id).toBe("provider-1")
    expect(draft.provider.provider_kind).toBe("openai")
    expect(draft.model.model_id).toBe("gpt-4o")
    expect(draft.input.kind).toBe("messages")
    if (draft.input.kind !== "messages")
      throw new Error("Expected messages input")
    expect(draft.input.system).toBe("You are concise.")
    expect(draft.input.messages[0]?.content).toBe("Answer in one paragraph.")
    expect(draft.tools?.tool_mode).toBe("required")
    expect(draft.tools?.tool_allowlist).toEqual(["search", "python"])
    expect(draft.metadata?.tags).toEqual(["summarize", "rewrite"])
  })
})

test.describe("promptBuilderAdapters hydration", () => {
  test("hydrates provider/model details from catalogs", async () => {
    const draft = mapUserAgentConfigToPromptDraft(
      createAgent({
        user_access_provider: "provider-1",
        model_id: "gpt-4o",
      }),
    )

    const hydrated = hydratePromptDraftProviderAndModel(
      draft,
      PROVIDERS,
      MODELS,
    )
    expect(hydrated.selectedProvider?.id).toBe("provider-1")
    expect(hydrated.selectedModel?.id).toBe("model-1")
    expect(hydrated.draft.provider.provider_type_id).toBe("ptype-openai")
    expect(hydrated.draft.provider.base_url).toBe("https://api.openai.com/v1")
    expect(hydrated.draft.model.model_catalog_id).toBe("model-1")
    expect(hydrated.draft.model.model_name).toBe("GPT 4o")
    expect(hydrated.draft.model.model_family).toBe("gpt")
  })

  test("builds semantic validation context from hydration result", async () => {
    const draft = mapUserAgentConfigToPromptDraft(
      createAgent({
        user_access_provider: "provider-1",
        model_id: "gpt-4o",
      }),
    )

    const hydrated = hydratePromptDraftProviderAndModel(
      draft,
      PROVIDERS,
      MODELS,
    )
    const context = buildPromptValidationContext(hydrated)

    expect(context.selectedProvider?.id).toBe("provider-1")
    expect(context.selectedModel?.id).toBe("model-1")
  })
})

test.describe("promptBuilderAdapters reverse mapping", () => {
  test("maps prompt draft back to agent update payload", async () => {
    const sourceAgent = createAgent({
      name: "Prompt Agent",
      slug: "prompt-agent",
      provider_type: "673f1787-8474-4e1c-986c-8e19f14c989c",
      is_enabled: true,
      is_visible: true,
      is_clonable: true,
      participation_mode: "manual",
      scope: "personal",
      max_tool_iterations: 8,
      capabilities: ["summarize"],
    })
    const draft = mapUserAgentConfigToPromptDraft(
      createAgent({
        user_access_provider: "provider-1",
        provider_type: "openai",
        model_id: "gpt-4o",
        instructions: "Respond in two bullet points.",
      }),
    )
    const payload = mapPromptDraftToAgentUpdatePayload(
      draft,
      sourceAgent,
      PROVIDERS[0]!,
    )

    expect(payload.name).toBe("Prompt Agent")
    expect(payload.slug).toBe("prompt-agent")
    expect(payload.provider_type).toBe("673f1787-8474-4e1c-986c-8e19f14c989c")
    expect(payload.user_access_provider).toBe("provider-1")
    expect(payload.model_id).toBe("gpt-4o")
    expect(payload.instructions).toContain("[user]")
  })
})
