import { expect, test } from "@playwright/test"
import {
  ACTIVE_BUILDER_BLOCK_TYPES,
  ACTIVE_BUILDER_PANEL_KINDS,
  BUILDER_BLOCK_TYPE_SCHEMAS,
  BUILDER_COMPOSITION_TEMPLATES,
  BUILDER_COMPOSITION_FIELD_SPECS,
  BUILDER_PANEL_KIND_SCHEMAS,
  createBlockTemplate,
  createEmptyComposition,
  createPanelTemplate,
  createCompositionTemplate,
  getBuilderCompositionTemplateSchema,
  getTemplateSetupState,
  getBuilderBlockTypeSchema,
  getBuilderPanelKindSchema,
  normalizeComposition,
  resolveTemplateChecklistStatus,
  validateCompositionSemantics,
  withTemplateSetupState,
} from "@/components/Demo/builder/demoBuilderSchema"

test.describe("demoBuilderSchema normalization", () => {
  test("createEmptyComposition returns canonical defaults", async () => {
    const composition = createEmptyComposition()
    expect(composition.schema_version).toBe(1)
    expect(composition.layout_mode).toBe("panels")
    expect(composition.runtime_policy).toBe("auto")
    expect(composition.persona_policy).toBe("first_available")
    expect(composition.chat_mode).toBe("participant")
    expect(composition.panels).toEqual([])
    expect(composition.blocks).toEqual([])
  })

  test("normalizeComposition fills missing arrays and preserves provided values", async () => {
    const normalized = normalizeComposition({
      layout_mode: "tabs",
      metadata_json: { story_id: "story-1" },
    })
    expect(normalized.layout_mode).toBe("tabs")
    expect(normalized.metadata_json).toEqual({ story_id: "story-1" })
    expect(normalized.panels).toEqual([])
    expect(normalized.blocks).toEqual([])
  })
})

test.describe("demoBuilderSchema v2 field specs", () => {
  test("composition field specs include theme metadata controls", async () => {
    const keys = BUILDER_COMPOSITION_FIELD_SPECS.map((field) => field.key)
    expect(keys).toContain("page_theme_id")
    expect(keys).toContain("cards_theme_id")
    expect(keys).toContain("presentation_json")
  })

  test("panel schema map covers all active panel kinds and includes theme field metadata", async () => {
    expect(Object.keys(BUILDER_PANEL_KIND_SCHEMAS).sort()).toEqual([...ACTIVE_BUILDER_PANEL_KINDS].sort())
    for (const kind of ACTIVE_BUILDER_PANEL_KINDS) {
      const schema = getBuilderPanelKindSchema(kind)
      expect(schema.kind).toBe(kind)
      expect(schema.fieldSpecs.some((field) => field.key === "theme_id")).toBeTruthy()
    }
  })

  test("block schema map covers all active block types and includes theme field metadata", async () => {
    expect(Object.keys(BUILDER_BLOCK_TYPE_SCHEMAS).sort()).toEqual([...ACTIVE_BUILDER_BLOCK_TYPES].sort())
    for (const type of ACTIVE_BUILDER_BLOCK_TYPES) {
      const schema = getBuilderBlockTypeSchema(type)
      expect(schema.type).toBe(type)
      expect(schema.fieldSpecs.some((field) => field.key === "theme_id")).toBeTruthy()
    }
  })

  test("template options expose the expected A/B/C/D/E/F/G entries", async () => {
    expect(BUILDER_COMPOSITION_TEMPLATES.map((template) => template.id)).toEqual([
      "composition_a_baseline",
      "composition_b_runtime_coupled",
      "composition_c_visibility_semantics",
      "composition_d_stylized_agent_ops",
      "composition_e_tabs_content_studio",
      "composition_f_presentation_passthrough_audit",
      "composition_g_ux_style_matrix",
    ])
  })
})

test.describe("demoBuilderSchema semantic validation", () => {
  test("flags story-dependent panel when story_id is missing", async () => {
    const composition = createEmptyComposition()
    composition.panels = [createPanelTemplate("storyRuntime")]

    const issues = validateCompositionSemantics(composition)
    expect(issues.some((issue) => issue.code === "story_id_required")).toBeTruthy()
  })

  test("does not flag story-dependent panel when story_id is present", async () => {
    const composition = createEmptyComposition()
    composition.metadata_json = { story_id: "story-1" }
    composition.panels = [createPanelTemplate("storyRuntime")]

    const issues = validateCompositionSemantics(composition)
    expect(issues.some((issue) => issue.code === "story_id_required")).toBeFalsy()
  })

  test("flags multiple page viewport panels", async () => {
    const composition = createEmptyComposition()
    const left = createPanelTemplate("storyRuntime")
    left.viewport_mode = "page"
    const right = createPanelTemplate("chat")
    right.viewport_mode = "page"
    composition.panels = [left, right]

    const issues = validateCompositionSemantics(composition)
    expect(issues.some((issue) => issue.code === "too_many_page_viewports")).toBeTruthy()
  })

  test("flags missing content payload for content-capable blocks", async () => {
    const composition = createEmptyComposition()
    const block = createBlockTemplate("content")
    delete (block as { content_json?: unknown }).content_json
    composition.blocks = [block]

    const issues = validateCompositionSemantics(composition)
    expect(issues.some((issue) => issue.code === "content_payload_missing")).toBeTruthy()
  })

  test("composition A template includes story/chat baseline and no error-level issues", async () => {
    const composition = createCompositionTemplate("composition_a_baseline")
    const panelKinds = (composition.panels ?? []).map((panel) => panel.kind)
    const blockTypes = (composition.blocks ?? []).map((block) => block.type)

    expect(panelKinds).toEqual(expect.arrayContaining(["storyRuntime", "chat"]))
    expect(blockTypes).toEqual(expect.arrayContaining(["content"]))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition B template includes runtime-coupled coverage and no error-level issues", async () => {
    const composition = createCompositionTemplate("composition_b_runtime_coupled")
    const blockTypes = (composition.blocks ?? []).map((block) => block.type)

    expect(blockTypes).toEqual(expect.arrayContaining([
      "storyMetadata",
      "orchestratorState",
      "contributionFeed",
    ]))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition C template applies explicit visibility permutations", async () => {
    const composition = createCompositionTemplate("composition_c_visibility_semantics")
    const visibilities = (composition.blocks ?? []).map((block) => block.visibility)

    expect(visibilities).toEqual(expect.arrayContaining([
      "visible",
      "hidden_mounted",
      "hidden_unmounted",
    ]))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition D template includes stylized chat and preloaded participant metadata", async () => {
    const composition = createCompositionTemplate("composition_d_stylized_agent_ops")
    const chatPanel = (composition.panels ?? []).find((panel) => panel.kind === "chat")
    const metadata = composition.metadata_json as Record<string, unknown>

    expect(chatPanel).toBeTruthy()
    expect(chatPanel?.title).toBe("Stylized Chat")
    expect(chatPanel?.theme_id).toBeNull()
    expect(chatPanel?.presentation_json).toEqual(expect.objectContaining({
      effects: expect.any(Object),
    }))
    expect(metadata.template_id).toBe("composition_d_stylized_agent_ops")
    expect(metadata.theme_title_hints).toEqual(expect.objectContaining({
      panel_theme_title: "qa-chat-neon",
    }))
    expect(metadata.preloaded_participants).toEqual(expect.objectContaining({
      user_agent_config_ids: ["orchestrator", "coder", "analyst"],
    }))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition E template uses tabs layout with content + git/file coverage", async () => {
    const composition = createCompositionTemplate("composition_e_tabs_content_studio")
    const panelKinds = (composition.panels ?? []).map((panel) => panel.kind)
    const blockTypes = (composition.blocks ?? []).map((block) => block.type)

    expect(composition.layout_mode).toBe("tabs")
    expect(panelKinds).toEqual(expect.arrayContaining(["content", "chat", "debug"]))
    expect(blockTypes).toEqual(expect.arrayContaining(["gitView", "fileExplorer", "context", "content"]))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition F template covers all active panel kinds and block types for passthrough auditing", async () => {
    const composition = createCompositionTemplate("composition_f_presentation_passthrough_audit")
    const panelKinds = new Set((composition.panels ?? []).map((panel) => panel.kind))
    const blockTypes = new Set((composition.blocks ?? []).map((block) => block.type))

    expect(composition.layout_mode).toBe("tabs")
    expect(panelKinds).toEqual(new Set(ACTIVE_BUILDER_PANEL_KINDS))
    expect(blockTypes).toEqual(new Set(ACTIVE_BUILDER_BLOCK_TYPES))
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })

  test("composition G template provides full-surface UX style matrix coverage", async () => {
    const composition = createCompositionTemplate("composition_g_ux_style_matrix")
    const panelKinds = new Set((composition.panels ?? []).map((panel) => panel.kind))
    const blockTypes = new Set((composition.blocks ?? []).map((block) => block.type))
    const metadata = composition.metadata_json as Record<string, unknown>
    const presentation = composition.presentation_json as Record<string, unknown>

    expect(panelKinds).toEqual(new Set(ACTIVE_BUILDER_PANEL_KINDS))
    expect(blockTypes).toEqual(new Set(ACTIVE_BUILDER_BLOCK_TYPES))
    expect(metadata.template_id).toBe("composition_g_ux_style_matrix")
    expect(metadata.audit_goal).toBeTruthy()
    expect(presentation.motion).toBeTruthy()
    expect(presentation.backgrounds).toBeTruthy()
    expect(validateCompositionSemantics(composition).every((issue) => issue.severity !== "error")).toBeTruthy()
  })
})

test.describe("demoBuilderSchema template checklist status", () => {
  test("tracks story_id as pending/resolved from composition metadata", async () => {
    const composition = createCompositionTemplate("composition_a_baseline")
    const noStory = normalizeComposition(composition)
    noStory.metadata_json = {}
    const noStoryIssues = validateCompositionSemantics(noStory)

    const pendingStatus = resolveTemplateChecklistStatus({
      templateId: "composition_a_baseline",
      composition: noStory,
      semanticIssues: noStoryIssues,
      confirmations: {},
    })
    expect(pendingStatus.items.find((item) => item.id === "story_id")?.resolved).toBeFalsy()

    const withStory = normalizeComposition(composition)
    withStory.metadata_json = { story_id: "story-1" }
    const resolvedStatus = resolveTemplateChecklistStatus({
      templateId: "composition_a_baseline",
      composition: withStory,
      semanticIssues: validateCompositionSemantics(withStory),
      confirmations: {},
    })
    expect(resolvedStatus.items.find((item) => item.id === "story_id")?.resolved).toBeTruthy()
  })

  test("requires confirmation for runtime/persona/chat assumptions", async () => {
    const composition = createCompositionTemplate("composition_b_runtime_coupled")
    const statusWithoutConfirm = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })
    expect(statusWithoutConfirm.items.find((item) => item.id === "runtime_policy")?.resolved).toBeFalsy()
    expect(statusWithoutConfirm.items.find((item) => item.id === "persona_policy")?.resolved).toBeFalsy()

    const statusWithConfirm = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: { runtime_policy: true, persona_policy: true },
    })
    expect(statusWithConfirm.items.find((item) => item.id === "runtime_policy")?.resolved).toBeTruthy()
    expect(statusWithConfirm.items.find((item) => item.id === "persona_policy")?.resolved).toBeTruthy()
  })

  test("fixed_user_persona_id item only blocks when fixed persona policy is selected", async () => {
    const composition = createCompositionTemplate("composition_b_runtime_coupled")
    composition.persona_policy = "first_available"
    let status = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })
    expect(status.items.find((item) => item.id === "fixed_user_persona_id")?.resolved).toBeTruthy()

    composition.persona_policy = "fixed_user_persona"
    composition.fixed_user_persona_id = null
    status = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })
    expect(status.items.find((item) => item.id === "fixed_user_persona_id")?.resolved).toBeFalsy()

    composition.fixed_user_persona_id = "persona-1"
    status = resolveTemplateChecklistStatus({
      templateId: "composition_b_runtime_coupled",
      composition,
      semanticIssues: validateCompositionSemantics(composition),
      confirmations: {},
    })
    expect(status.items.find((item) => item.id === "fixed_user_persona_id")?.resolved).toBeTruthy()
  })

  test("template schema exposes checklist metadata", async () => {
    const schema = getBuilderCompositionTemplateSchema("composition_c_visibility_semantics")
    expect(schema.requiredAssumptions).toEqual(expect.arrayContaining(["story_id", "runtime_policy"]))
    expect(schema.checklistItems.length).toBeGreaterThan(0)
  })

  test("template setup state persists under metadata_json.template_setup", async () => {
    const composition = createEmptyComposition()
    const withSetup = withTemplateSetupState(composition, {
      templateId: "composition_b_runtime_coupled",
      dismissed: true,
      confirmations: {
        runtime_policy: true,
        persona_policy: false,
      },
    })
    const parsed = getTemplateSetupState(withSetup)
    expect(parsed).toEqual({
      templateId: "composition_b_runtime_coupled",
      dismissed: true,
      confirmations: {
        runtime_policy: true,
        persona_policy: false,
      },
    })
  })

  test("template setup state can be cleared from metadata_json", async () => {
    const composition = withTemplateSetupState(createEmptyComposition(), {
      templateId: "composition_a_baseline",
      dismissed: false,
      confirmations: { story_id: true },
    })
    const cleared = withTemplateSetupState(composition, null)
    expect(getTemplateSetupState(cleared)).toBeNull()
  })
})
