import { expect, test } from "@playwright/test"
import {
  BUILDER_BLOCK_CAPABILITIES,
  BUILDER_CAPABILITY_PACK_REGISTRATIONS,
  BUILDER_COMPOSITION_CAPABILITIES,
  BUILDER_PANEL_CAPABILITIES,
  buildCapabilityRegistry,
  getBlockCapabilityAvailability,
  getBuilderCapabilityCoverageGaps,
  getBuilderCapabilityPackRegistrationInventory,
  getBuilderCapabilitySafetyGaps,
  getBuilderRequirementCompatibilityGaps,
  getBuilderCapabilityRegistrySnapshot,
  getBuilderRuntimeExpectationGaps,
  getBuilderRuntimeCompatibilityGaps,
  getBlockCapabilityByType,
  getPanelCapabilityByKind,
  getBlockCapabilityPreviewAdapterOverrides,
  getPanelCapabilityPreviewAdapterOverrides,
  normalizeBlockCapabilityPatch,
  normalizePanelCapabilityPatch,
  resolveBuilderCapabilityPacks,
  runBlockCapabilitySemanticValidators,
  getPanelCapabilityAvailability,
  runPanelCapabilitySemanticValidators,
} from "@/components/Demo/builder/demoBuilderCapabilityRegistry"
import {
  ACTIVE_BUILDER_BLOCK_TYPES,
  ACTIVE_BUILDER_PANEL_KINDS,
  createEmptyComposition,
} from "@/components/Demo/builder/demoBuilderSchema"

test.describe("demoBuilder capability registry", () => {
  test("covers all active panel and block kinds", async () => {
    expect(BUILDER_PANEL_CAPABILITIES.map((capability) => capability.kind).sort())
      .toEqual([...ACTIVE_BUILDER_PANEL_KINDS].sort())
    expect(BUILDER_BLOCK_CAPABILITIES.map((capability) => capability.type).sort())
      .toEqual([...ACTIVE_BUILDER_BLOCK_TYPES].sort())
  })

  test("provides composition capabilities for core theme and advanced controls", async () => {
    const categories = new Set(BUILDER_COMPOSITION_CAPABILITIES.map((capability) => capability.category))
    expect(categories.has("core")).toBeTruthy()
    expect(categories.has("theme")).toBeTruthy()
    expect(categories.has("advanced")).toBeTruthy()
  })

  test("snapshot exposes registry sections", async () => {
    const snapshot = getBuilderCapabilityRegistrySnapshot()
    expect(snapshot.panels.length).toBeGreaterThan(0)
    expect(snapshot.blocks.length).toBeGreaterThan(0)
    expect(snapshot.composition.length).toBeGreaterThan(0)
    expect(snapshot.conflicts).toEqual([])
  })

  test("pack registration inventory exposes registered pack metadata", async () => {
    expect(BUILDER_CAPABILITY_PACK_REGISTRATIONS.length).toBeGreaterThan(0)
    const inventory = getBuilderCapabilityPackRegistrationInventory()
    expect(inventory).toContainEqual({
      id: "internal.plugin.demo-builder.v1",
      description: "Internal builder plugin spike pack (participantPanel/toolCapability overrides).",
    })
    expect(inventory).toContainEqual({
      id: "example.ux-enhancer.v1",
      description: "UX-focused example pack for theme-oriented labels/placeholders and naming.",
    })
  })

  test("resolveBuilderCapabilityPacks resolves explicit pack ids and reports unknown ids", async () => {
    const resolution = resolveBuilderCapabilityPacks({
      enabledPackIds: ["internal.plugin.demo-builder.v1", "unknown.pack"],
      includeLegacyInternalFlag: false,
    })
    expect(resolution.enabledPackIds).toEqual(["internal.plugin.demo-builder.v1"])
    expect(resolution.packs).toHaveLength(1)
    expect(resolution.unknownPackIds).toEqual(["unknown.pack"])
  })

  test("resolveBuilderCapabilityPacks supports env-driven pack selection and legacy flag compatibility", async () => {
    const byPackList = resolveBuilderCapabilityPacks({
      env: {
        VITE_DEMO_BUILDER_PACKS: "internal.plugin.demo-builder.v1",
      },
      includeLegacyInternalFlag: false,
    })
    expect(byPackList.enabledPackIds).toEqual(["internal.plugin.demo-builder.v1"])
    expect(byPackList.packs).toHaveLength(1)

    const byLegacyFlag = resolveBuilderCapabilityPacks({
      env: {
        VITE_DEMO_BUILDER_ENABLE_INTERNAL_PLUGIN_PACK: "true",
      },
      includeLegacyInternalFlag: true,
    })
    expect(byLegacyFlag.enabledPackIds).toEqual(["internal.plugin.demo-builder.v1"])
    expect(byLegacyFlag.packs).toHaveLength(1)
  })

  test("ux-enhancer example pack overrides theme-focused composition capability metadata", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: resolveBuilderCapabilityPacks({
        enabledPackIds: ["example.ux-enhancer.v1"],
        includeLegacyInternalFlag: false,
      }).packs,
    })
    const pageThemeCapability = registry.composition.find((capability) => capability.key === "page_theme_id")
    const presentationCapability = registry.composition.find((capability) => capability.key === "presentation_json")
    expect(pageThemeCapability?.label).toBe("Page Theme Preset")
    expect(pageThemeCapability?.placeholder).toBe("e.g. ux-sunrise-canvas")
    expect(presentationCapability?.label).toBe("Presentation JSON (Fonts/Motion/Overlays/SVG)")
  })

  test("buildCapabilityRegistry applies deterministic pack ordering (order then id)", async () => {
    const registry = buildCapabilityRegistry({
      includeCoreCapabilities: false,
      packs: [
        {
          id: "z-pack",
          order: 10,
          compositionCapabilities: [{
            key: "zeta",
            label: "Zeta",
            category: "advanced",
            control: "text",
            enumValues: [],
          }],
        },
        {
          id: "a-pack",
          order: 10,
          compositionCapabilities: [{
            key: "alpha",
            label: "Alpha",
            category: "core",
            control: "text",
            enumValues: [],
          }],
        },
        {
          id: "m-pack",
          order: 5,
          compositionCapabilities: [{
            key: "middle",
            label: "Middle",
            category: "theme",
            control: "text",
            enumValues: [],
          }],
        },
      ],
    })

    expect(registry.composition.map((capability) => capability.key)).toEqual([
      "middle",
      "alpha",
      "zeta",
    ])
  })

  test("buildCapabilityRegistry keeps existing entries on key collisions by default", async () => {
    const registry = buildCapabilityRegistry({
      includeCoreCapabilities: false,
      packs: [
        {
          id: "first-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "First",
            category: "core",
            control: "text",
            enumValues: [],
          }],
        },
        {
          id: "second-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "Second",
            category: "advanced",
            control: "text",
            enumValues: [],
          }],
        },
      ],
    })

    expect(registry.composition).toHaveLength(1)
    expect(registry.composition[0].label).toBe("First")
    expect(registry.conflicts).toEqual([
      {
        scope: "composition",
        key: "shared_key",
        existingPackId: "first-pack",
        incomingPackId: "second-pack",
        policy: "keep_existing",
      },
    ])
  })

  test("buildCapabilityRegistry replaces entries when conflictPolicy is replace_existing", async () => {
    const registry = buildCapabilityRegistry({
      includeCoreCapabilities: false,
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "first-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "First",
            category: "core",
            control: "text",
            enumValues: [],
          }],
        },
        {
          id: "second-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "Second",
            category: "advanced",
            control: "text",
            enumValues: [],
          }],
        },
      ],
    })

    expect(registry.composition).toHaveLength(1)
    expect(registry.composition[0].label).toBe("Second")
    expect(registry.conflicts[0]?.policy).toBe("replace_existing")
  })

  test("buildCapabilityRegistry throws when conflictPolicy is error", async () => {
    expect(() => buildCapabilityRegistry({
      includeCoreCapabilities: false,
      conflictPolicy: "error",
      packs: [
        {
          id: "first-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "First",
            category: "core",
            control: "text",
            enumValues: [],
          }],
        },
        {
          id: "second-pack",
          compositionCapabilities: [{
            key: "shared_key",
            label: "Second",
            category: "theme",
            control: "text",
            enumValues: [],
          }],
        },
      ],
    })).toThrow("Capability registry conflict (composition:shared_key)")
  })

  test("coverage gap helper reports no gaps for current registry", async () => {
    const gaps = getBuilderCapabilityCoverageGaps()
    expect(gaps.missingPanelCapabilities).toEqual([])
    expect(gaps.missingBlockCapabilities).toEqual([])
  })

  test("builder/runtime compatibility helper reports no drift", async () => {
    const gaps = getBuilderRuntimeCompatibilityGaps()
    expect(gaps.missingBuilderPanelsInRuntime).toEqual([])
    expect(gaps.missingRuntimePanelsInBuilder).toEqual([])
    expect(gaps.missingBuilderBlocksInRuntime).toEqual([])
    expect(gaps.missingRuntimeBlocksInBuilder).toEqual([])
  })

  test("runtime expectation helper reports no gaps for default registry", async () => {
    const gaps = getBuilderRuntimeExpectationGaps()
    expect(gaps.issues).toEqual([])
  })

  test("requirement compatibility helper reports no mismatches for default registry", async () => {
    const gaps = getBuilderRequirementCompatibilityGaps()
    expect(gaps.mismatches).toEqual([])
  })

  test("runtime expectation helper reports missing hooks for runtime-coupled overrides", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "bad-runtime-pack",
          blockCapabilities: [{
            type: "toolCapability",
            displayName: "Tool Capability Broken",
            requirements: {
              requiresStory: false,
              requiresRuntime: false,
              requiresPersona: true,
            },
            hooks: {},
          }],
        },
      ],
    })
    const gaps = getBuilderRuntimeExpectationGaps(registry)
    expect(gaps.issues).toContainEqual(expect.objectContaining({
      code: "missing_editor_component",
      blockType: "toolCapability",
    }))
    expect(gaps.issues).toContainEqual(expect.objectContaining({
      code: "missing_patch_normalizer",
      blockType: "toolCapability",
    }))
    expect(gaps.issues).toContainEqual(expect.objectContaining({
      code: "missing_semantic_validator",
      blockType: "toolCapability",
    }))
  })

  test("invalid example pack triggers runtime expectation + safety issues", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: resolveBuilderCapabilityPacks({
        enabledPackIds: ["example.invalid.v1"],
        includeLegacyInternalFlag: false,
      }).packs,
    })
    const runtimeGaps = getBuilderRuntimeExpectationGaps(registry)
    expect(runtimeGaps.issues).toContainEqual(expect.objectContaining({
      code: "missing_editor_component",
      blockType: "toolCapability",
    }))
    const safetyGaps = getBuilderCapabilitySafetyGaps(registry)
    expect(safetyGaps.issues).toContainEqual(expect.objectContaining({
      code: "unsupported_control",
      key: "invalid_unsupported_toggle",
      severity: "error",
    }))
  })

  test("policy-guarded example pack triggers requirement escalation safety signal", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: resolveBuilderCapabilityPacks({
        enabledPackIds: ["example.policy-guarded.v1"],
        includeLegacyInternalFlag: false,
      }).packs,
    })
    const safetyGaps = getBuilderCapabilitySafetyGaps(registry)
    expect(safetyGaps.issues).toContainEqual(expect.objectContaining({
      code: "requirement_escalation",
      scope: "panel",
      key: "participantPanel",
      severity: "error",
    }))
  })

  test("requirement compatibility helper reports mismatches for overridden requirements", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "req-override-pack",
          panelCapabilities: [{
            kind: "participantPanel",
            displayName: "Participant Panel Override",
            requirements: {
              requiresStory: false,
              requiresRuntime: true,
              requiresPersona: false,
            },
            hooks: {},
          }],
        },
      ],
    })
    const gaps = getBuilderRequirementCompatibilityGaps(registry)
    expect(gaps.mismatches).toContainEqual({
      scope: "panel",
      key: "participantPanel",
      requirement: "requiresRuntime",
      expected: false,
      actual: true,
    })
    expect(gaps.mismatches).toContainEqual({
      scope: "panel",
      key: "participantPanel",
      requirement: "requiresPersona",
      expected: true,
      actual: false,
    })
  })

  test("registry composition supports plugin-style override packs", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "plugin-pack",
          order: 500,
          blockCapabilities: [{
            type: "toolCapability",
            displayName: "Tool Capability (Plugin)",
            requirements: {
              requiresStory: false,
              requiresRuntime: false,
              requiresPersona: true,
            },
            hooks: {
              editorComponent: "ToolCapabilityPluginEditor",
            },
          }],
        },
      ],
    })

    const toolCapability = registry.blocks.find((capability) => capability.type === "toolCapability")
    expect(toolCapability?.displayName).toBe("Tool Capability (Plugin)")
    expect(toolCapability?.hooks?.editorComponent).toBe("ToolCapabilityPluginEditor")
  })

  test("capability safety helper reports unsupported controls and requirement escalations", async () => {
    const registry = buildCapabilityRegistry({
      includeCoreCapabilities: false,
      packs: [
        {
          id: "unsafe-pack",
          compositionCapabilities: [{
            key: "unsafe_bool",
            label: "Unsafe Bool",
            category: "advanced",
            control: "boolean",
            enumValues: [],
          }],
          panelCapabilities: [{
            kind: "chat",
            displayName: "Chat Elevated",
            requirements: {
              requiresStory: true,
              requiresRuntime: true,
              requiresPersona: false,
            },
            hooks: {},
          }],
        },
      ],
    })
    const gaps = getBuilderCapabilitySafetyGaps(registry)
    expect(gaps.issues).toContainEqual({
      code: "unsupported_control",
      scope: "composition",
      key: "unsafe_bool",
      severity: "error",
      message: 'Unsupported composition control "boolean" for capability "unsafe_bool".',
    })
    expect(gaps.issues).toContainEqual(expect.objectContaining({
      code: "requirement_escalation",
      scope: "panel",
      key: "chat",
      severity: "error",
    }))
  })

  test("capability safety helper reports requirement relaxations as warnings", async () => {
    const registry = buildCapabilityRegistry({
      conflictPolicy: "replace_existing",
      packs: [
        {
          id: "relax-pack",
          panelCapabilities: [{
            kind: "participantPanel",
            displayName: "Participant Relaxed",
            requirements: {
              requiresStory: false,
              requiresRuntime: false,
              requiresPersona: false,
            },
            hooks: {},
          }],
        },
      ],
    })
    const gaps = getBuilderCapabilitySafetyGaps(registry)
    expect(gaps.issues).toContainEqual(expect.objectContaining({
      code: "requirement_relaxation",
      scope: "panel",
      key: "participantPanel",
      severity: "warning",
    }))
  })

  test("availability predicates gate story/runtime/persona-dependent capabilities", async () => {
    const composition = createEmptyComposition()
    composition.runtime_policy = undefined
    composition.persona_policy = "fixed_user_persona"
    composition.fixed_user_persona_id = null
    composition.metadata_json = {}

    const storyRuntimePanel = BUILDER_PANEL_CAPABILITIES.find((capability) => capability.kind === "storyRuntime")
    const participantPanel = BUILDER_PANEL_CAPABILITIES.find((capability) => capability.kind === "participantPanel")
    const storyMetadataBlock = BUILDER_BLOCK_CAPABILITIES.find((capability) => capability.type === "storyMetadata")
    const toolCapabilityBlock = BUILDER_BLOCK_CAPABILITIES.find((capability) => capability.type === "toolCapability")

    expect(storyRuntimePanel).toBeTruthy()
    expect(participantPanel).toBeTruthy()
    expect(storyMetadataBlock).toBeTruthy()
    expect(toolCapabilityBlock).toBeTruthy()

    const storyRuntimeAvailability = getPanelCapabilityAvailability(storyRuntimePanel!, composition)
    expect(storyRuntimeAvailability.available).toBeFalsy()
    expect(storyRuntimeAvailability.unmetRequirements).toContain("story setup")
    expect(storyRuntimeAvailability.unmetRequirements).toContain("runtime setup")

    const participantAvailability = getPanelCapabilityAvailability(participantPanel!, composition)
    expect(participantAvailability.available).toBeFalsy()
    expect(participantAvailability.unmetRequirements).toContain("persona setup")

    const storyMetadataAvailability = getBlockCapabilityAvailability(storyMetadataBlock!, composition)
    expect(storyMetadataAvailability.available).toBeFalsy()
    expect(storyMetadataAvailability.unmetRequirements).toContain("story setup")
    expect(storyMetadataAvailability.unmetRequirements).toContain("runtime setup")

    const toolCapabilityAvailability = getBlockCapabilityAvailability(toolCapabilityBlock!, composition)
    expect(toolCapabilityAvailability.available).toBeFalsy()
    expect(toolCapabilityAvailability.unmetRequirements).toContain("persona setup")
  })

  test("descriptor hook helpers preserve no-op behavior when hooks are absent", async () => {
    const composition = createEmptyComposition()
    const panelCapability = BUILDER_PANEL_CAPABILITIES[0]
    const blockCapability = BUILDER_BLOCK_CAPABILITIES[0]
    const panelPatch = { title: "x" }
    const blockPatch = { title: "y" }

    expect(normalizePanelCapabilityPatch(panelCapability, panelPatch, composition)).toEqual(panelPatch)
    expect(normalizeBlockCapabilityPatch(blockCapability, blockPatch, composition)).toEqual(blockPatch)
    expect(runPanelCapabilitySemanticValidators(panelCapability, composition)).toEqual([])
    expect(runBlockCapabilitySemanticValidators(blockCapability, composition)).toEqual([])
  })

  test("descriptor hook helpers execute normalize and semantic validator hooks", async () => {
    const composition = createEmptyComposition()
    const panelCapability = {
      ...BUILDER_PANEL_CAPABILITIES[0],
      hooks: {
        normalizeCompositionPatch: (patch: Record<string, unknown>) => ({
          ...patch,
          title: "normalized-panel",
        }),
        semanticValidators: [() => [{ code: "panel_test", message: "panel", severity: "warning" as const }]],
      },
    }
    const blockCapability = {
      ...BUILDER_BLOCK_CAPABILITIES[0],
      hooks: {
        normalizeCompositionPatch: (patch: Record<string, unknown>) => ({
          ...patch,
          title: "normalized-block",
        }),
        semanticValidators: [() => [{ code: "block_test", message: "block", severity: "error" as const }]],
      },
    }

    expect(normalizePanelCapabilityPatch(panelCapability, { title: "raw" }, composition)).toEqual({
      title: "normalized-panel",
    })
    expect(normalizeBlockCapabilityPatch(blockCapability, { title: "raw" }, composition)).toEqual({
      title: "normalized-block",
    })
    expect(runPanelCapabilitySemanticValidators(panelCapability, composition)).toEqual([
      { code: "panel_test", message: "panel", severity: "warning" },
    ])
    expect(runBlockCapabilitySemanticValidators(blockCapability, composition)).toEqual([
      { code: "block_test", message: "block", severity: "error" },
    ])
  })

  test("storyMetadata hook normalizes config_json and emits warning when debug config view is enabled", async () => {
    const composition = createEmptyComposition()
    composition.blocks = [
      {
        id: "story-meta-1",
        type: "storyMetadata",
        title: "Story Metadata",
        order: 1,
        region: "top",
        visibility: "visible",
        config_json: {
          show_config_json: true,
        },
      },
    ]

    const capability = BUILDER_BLOCK_CAPABILITIES.find((item) => item.type === "storyMetadata")
    expect(capability).toBeTruthy()

    const normalizedPatch = normalizeBlockCapabilityPatch(
      capability!,
      { config_json: { show_config_json: "yes" } },
      composition,
    )
    expect(normalizedPatch).toEqual({
      config_json: {
        show_config_json: false,
      },
    })

    expect(runBlockCapabilitySemanticValidators(capability!, composition)).toEqual([
      {
        code: "story_metadata_config_visible",
        message: "storyMetadata config_json debug output is enabled (show_config_json=true).",
        severity: "warning",
      },
    ])
  })

  test("orchestratorState hook normalizes defaults and warns when agent list is hidden", async () => {
    const composition = createEmptyComposition()
    composition.blocks = [
      {
        id: "orchestrator-1",
        type: "orchestratorState",
        title: "Orchestrator State",
        order: 1,
        region: "top",
        visibility: "visible",
        config_json: {
          show_agent_list: false,
        },
      },
    ]

    const capability = BUILDER_BLOCK_CAPABILITIES.find((item) => item.type === "orchestratorState")
    expect(capability).toBeTruthy()

    const normalizedPatch = normalizeBlockCapabilityPatch(
      capability!,
      { config_json: { show_config_json: "debug" } },
      composition,
    )
    expect(normalizedPatch).toEqual({
      config_json: {
        show_agent_list: true,
        only_active_agents: true,
        show_config_json: false,
      },
    })

    expect(runBlockCapabilitySemanticValidators(capability!, composition)).toEqual([
      {
        code: "orchestrator_agent_list_hidden",
        message: "orchestratorState hides agent list (show_agent_list=false); orchestration visibility is reduced.",
        severity: "warning",
      },
    ])
  })

  test("contributionFeed hook normalizes feed config and emits permissive warnings", async () => {
    const composition = createEmptyComposition()
    composition.blocks = [
      {
        id: "feed-1",
        type: "contributionFeed",
        title: "Contribution Feed",
        order: 1,
        region: "top",
        visibility: "visible",
        config_json: {
          include_internal: true,
          max_items: 64,
        },
      },
    ]

    const capability = BUILDER_BLOCK_CAPABILITIES.find((item) => item.type === "contributionFeed")
    expect(capability).toBeTruthy()

    const normalizedPatch = normalizeBlockCapabilityPatch(
      capability!,
      { config_json: { max_items: -7, show_timestamps: 1 } },
      composition,
    )
    expect(normalizedPatch).toEqual({
      config_json: {
        max_items: 12,
        include_internal: false,
        show_sender_type: false,
        show_timestamps: true,
        show_config_json: false,
      },
    })

    expect(runBlockCapabilitySemanticValidators(capability!, composition)).toEqual([
      {
        code: "contribution_feed_internal_enabled",
        message: "contributionFeed includes internal messages (include_internal=true).",
        severity: "warning",
      },
      {
        code: "contribution_feed_large_window",
        message: "contributionFeed max_items is high (>50) and may add UI noise.",
        severity: "warning",
      },
    ])
  })

  test("toolCapability hook normalizes mapping shape and warns on invalid mapping entries", async () => {
    const composition = createEmptyComposition()
    composition.blocks = [
      {
        id: "tools-1",
        type: "toolCapability",
        title: "Tool Capability",
        order: 1,
        region: "top",
        visibility: "visible",
        config_json: {
          capability_map: {
            coder: [123, null],
          },
        },
      },
    ]

    const capability = BUILDER_BLOCK_CAPABILITIES.find((item) => item.type === "toolCapability")
    expect(capability).toBeTruthy()

    const normalizedPatch = normalizeBlockCapabilityPatch(
      capability!,
      { config_json: { capability_map: { analyst: [" summary ", "", "summary"] } } },
      composition,
    )
    expect(normalizedPatch).toEqual({
      config_json: {
        only_active_agents: true,
        show_agent_matrix: true,
        show_config_json: false,
        capability_map: {
          analyst: ["summary"],
        },
      },
    })

    expect(runBlockCapabilitySemanticValidators(capability!, composition)).toEqual([
      {
        code: "tool_capability_invalid_mapping",
        message: "toolCapability capability_map contains invalid entries and was normalized.",
        severity: "warning",
      },
    ])
  })

  test("storyRuntime panel preview adapter reflects story and runtime policy", async () => {
    const composition = createEmptyComposition()
    composition.runtime_policy = "manual"
    composition.metadata_json = { story_id: "story-123" }
    const capability = getPanelCapabilityByKind("storyRuntime")
    expect(capability).toBeTruthy()

    const overrides = getPanelCapabilityPreviewAdapterOverrides(
      capability!,
      { kind: "storyRuntime" },
      composition,
    )

    expect(overrides.roomStoryId).toBe("story-123")
    expect(overrides.autoRespond).toBeFalsy()
  })

  test("storyMetadata block preview adapter emits auto-start guidance when story is missing", async () => {
    const composition = createEmptyComposition()
    composition.runtime_policy = "auto"
    composition.metadata_json = {}
    const capability = getBlockCapabilityByType("storyMetadata")
    expect(capability).toBeTruthy()

    const overrides = getBlockCapabilityPreviewAdapterOverrides(
      capability!,
      { type: "storyMetadata", config_json: {} },
      composition,
    )

    expect(overrides.roomStoryId).toBeNull()
    expect(overrides.runtimePolicy).toBe("auto")
    expect(overrides.runtimeHasRuntime).toBeFalsy()
    expect(overrides.autoStartError).toContain("metadata_json.story_id")
  })

  test("contributionFeed block preview adapter injects synthetic messages", async () => {
    const composition = createEmptyComposition()
    composition.runtime_policy = "auto"
    const capability = getBlockCapabilityByType("contributionFeed")
    expect(capability).toBeTruthy()

    const overrides = getBlockCapabilityPreviewAdapterOverrides(
      capability!,
      { type: "contributionFeed", config_json: {} },
      composition,
    )

    expect((overrides.debugMessages ?? []).length).toBeGreaterThan(0)
    expect(overrides.streamingMessage?.agent_name).toBe("Orchestrator")
  })

  test("toolCapability block preview adapter maps capability_map to available agents", async () => {
    const composition = createEmptyComposition()
    const capability = getBlockCapabilityByType("toolCapability")
    expect(capability).toBeTruthy()

    const overrides = getBlockCapabilityPreviewAdapterOverrides(
      capability!,
      {
        type: "toolCapability",
        config_json: {
          capability_map: {
            coder: ["diff", "code"],
          },
        },
      },
      composition,
    )

    const availableAgents = overrides.availableAgents ?? []
    expect(availableAgents.length).toBeGreaterThan(0)
    const coder = availableAgents.find((agent) => agent.id === "coder")
    expect(coder).toBeTruthy()
    expect(coder?.capabilities).toEqual(["diff", "code"])
  })
})
