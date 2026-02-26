import { expect, test } from "@playwright/test"

import {
  buildPromptCapabilityRegistry,
  createPromptDraftForCapabilityTests,
  getPromptCapabilityByKey,
  getPromptCapabilityCoverageGaps,
  getPromptCapabilityRegistrySnapshot,
  normalizePromptCapabilityValue,
  runPromptCapabilitySemanticValidators,
  validatePromptDraftWithCapabilityHooks,
} from "@/components/Prompt/builder/promptBuilderCapabilityRegistry"

test.describe("promptBuilder capability registry", () => {
  test("covers all prompt builder field spec keys", async () => {
    const gaps = getPromptCapabilityCoverageGaps()
    expect(gaps.missingCapabilities).toEqual([])
  })

  test("snapshot exposes capabilities and conflicts", async () => {
    const snapshot = getPromptCapabilityRegistrySnapshot()
    expect(snapshot.capabilities.length).toBeGreaterThan(0)
    expect(snapshot.conflicts).toEqual([])
  })

  test("getPromptCapabilityByKey resolves known key", async () => {
    const capability = getPromptCapabilityByKey(
      "provider.user_access_provider_id",
    )
    expect(capability).toBeTruthy()
    expect(capability?.label).toBe("Access Provider")
  })

  test("normalizes provider/model string ids and stop sequences via capability hooks", async () => {
    const draft = createPromptDraftForCapabilityTests()
    const providerCapability = getPromptCapabilityByKey(
      "provider.user_access_provider_id",
    )
    const modelCapability = getPromptCapabilityByKey("model.model_id")
    const stopCapability = getPromptCapabilityByKey("params.stop")
    expect(providerCapability).toBeTruthy()
    expect(modelCapability).toBeTruthy()
    expect(stopCapability).toBeTruthy()

    const normalizedProvider = normalizePromptCapabilityValue(
      providerCapability!,
      "  provider-2  ",
      draft,
    )
    const normalizedModel = normalizePromptCapabilityValue(
      modelCapability!,
      "  gpt-4.1  ",
      draft,
    )
    const normalizedStop = normalizePromptCapabilityValue(
      stopCapability!,
      ["  END  ", "END", 123, ""],
      draft,
    )
    expect(normalizedProvider).toBe("provider-2")
    expect(normalizedModel).toBe("gpt-4.1")
    expect(normalizedStop).toEqual(["END"])
  })

  test("tool config semantic hook warns for required tool mode without allowlist", async () => {
    const draft = createPromptDraftForCapabilityTests()
    draft.tools = {
      tool_mode: "required",
      tool_allowlist: [],
      tool_choice: null,
    }
    const capability = getPromptCapabilityByKey("tools")
    expect(capability).toBeTruthy()

    const issues = runPromptCapabilitySemanticValidators(capability!, draft)
    expect(issues).toEqual([
      {
        code: "tool_mode_required_without_allowlist",
        message: "tool_mode is required but tool_allowlist is empty.",
        severity: "warning",
        path: "tools",
      },
    ])
  })

  test("validatePromptDraftWithCapabilityHooks includes both base and hook issues", async () => {
    const draft = createPromptDraftForCapabilityTests()
    draft.provider.user_access_provider_id = null
    draft.tools = {
      tool_mode: "required",
      tool_allowlist: [],
      tool_choice: null,
    }

    const issues = validatePromptDraftWithCapabilityHooks(draft)
    expect(
      issues.some((issue) => issue.code === "provider_required"),
    ).toBeTruthy()
    expect(
      issues.some(
        (issue) => issue.code === "tool_mode_required_without_allowlist",
      ),
    ).toBeTruthy()
  })

  test("buildPromptCapabilityRegistry keeps existing on collision by default", async () => {
    const registry = buildPromptCapabilityRegistry({
      includeCoreCapabilities: false,
      packs: [
        {
          id: "first",
          capabilities: [
            {
              key: "shared",
              label: "First",
              control: "text",
              category: "advanced",
            },
          ],
        },
        {
          id: "second",
          capabilities: [
            {
              key: "shared",
              label: "Second",
              control: "text",
              category: "advanced",
            },
          ],
        },
      ],
    })
    expect(registry.capabilities).toHaveLength(1)
    expect(registry.capabilities[0].label).toBe("First")
    expect(registry.conflicts).toEqual([
      {
        key: "shared",
        existingPackId: "first",
        incomingPackId: "second",
        policy: "keep_existing",
      },
    ])
  })

  test("buildPromptCapabilityRegistry replaces entry on replace_existing", async () => {
    const registry = buildPromptCapabilityRegistry({
      includeCoreCapabilities: false,
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "first",
          capabilities: [
            {
              key: "shared",
              label: "First",
              control: "text",
              category: "advanced",
            },
          ],
        },
        {
          id: "second",
          capabilities: [
            {
              key: "shared",
              label: "Second",
              control: "text",
              category: "advanced",
            },
          ],
        },
      ],
    })
    expect(registry.capabilities).toHaveLength(1)
    expect(registry.capabilities[0].label).toBe("Second")
    expect(registry.conflicts[0]?.policy).toBe("replace_existing")
  })
})
