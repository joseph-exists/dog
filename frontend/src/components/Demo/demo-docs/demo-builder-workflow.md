# Demo Builder Workflow
> **Status:** Active architecture + implementation workflow  
> **Last Revised:** 2026-02-25

## Goal
Composable, guided Demo Builder authoring with reusable editors, schema-driven validation, and capability-driven extension.

## Architecture
1. Canonical persisted contract:
- `DemoPageCompositionBase_Input`

2. Builder authoring layer:
- `demoBuilderSchema.ts` defines active kinds, defaults, templates, field specs, and semantic validators.

3. Builder capability layer:
- `demoBuilderCapabilityRegistry.ts` defines descriptor metadata, hook extension points, pack composition, and compatibility checks.

4. Runtime renderer layer:
- `rendererRegistry.tsx` remains runtime-facing and separate from builder authoring registry.

## Current Implementation State
### Complete
1. Route decomposition to reusable editors (`DemoTopLevelEditor`, `DemoValidationPanel`, `DemoPanelEditor`, `DemoBlockEditor`, `DemoRawJsonEditor`, `DemoSaveBar`).
2. Schema v2 field-spec layer and semantic validator model.
3. Template constructors A/B/C/D/E/F/G.
4. Post-apply template setup checklist and persistence in `metadata_json.template_setup`.
5. In-context dependency pickers for unresolved assumptions.
6. Capability registry composition API and env-gated pack activation.
7. Capability hook implementations for runtime-coupled blocks:
- `storyMetadata`
- `orchestratorState`
- `contributionFeed`
- `toolCapability`
8. Baseline capability compatibility/safety analyzers.
9. Guided + fallback presentation editing path with targeted unit coverage.
10. Interactive block handler vertical slice:
- `config_json.interaction.kind = "click_prompt_dispatch.v1"` on `content`/`context` blocks
- click source capture (`trigger.selector`)
- inline spawned input modal (`modal.*`)
- submit dispatch envelope to chat socket (`dispatch.*`)

## Interaction Schema (V1)
Use this in block `config_json` for `content` or `context` blocks:

```json
{
  "interaction": {
    "kind": "click_prompt_dispatch.v1",
    "enabled": true,
    "trigger": {
      "selector": "pre code, code",
      "max_source_chars": 1200
    },
    "modal": {
      "title": "Ask about selected code",
      "helper_text": "This sends your message plus clicked-code context to the configured chat receiver.",
      "placeholder": "What should the invisible chat analyze or explain?",
      "submit_label": "Send",
      "cancel_label": "Cancel",
      "multiline": false,
      "max_message_chars": 1000
    },
    "dispatch": {
      "target": "hidden_chat_panel",
      "target_panel_id": null,
      "format": "json",
      "text_prefix": "[demo-block-interaction]",
      "enforce_registered_receiver": false
    }
  }
}
```

Register chat receivers in panel `options`:

```json
{
  "interaction_receiver": {
    "enabled": true,
    "receiver_id": "hidden-chat-panel",
    "accepts": ["click_prompt_dispatch.v1"]
  }
}
```

### In Progress
1. Theme/token cascade convergence with shared theme system.
2. Rich runtime-coupled preview fidelity expansion.

### Next
1. Descriptor-complete controls:
- remove remaining editor-specific rendering branches by moving control behavior into descriptors.

2. Capability-level preview adapters:
- bring guided presentation fields closer to runtime visual behavior.

3. Diagnostics overlays:
- inline capability-aware diagnostics in editor/preview for setup and rendering constraints.

## Sequencing (Low Churn / High Value)
1. Finish descriptor completeness first.
2. Then expand preview adapters.
3. Then add diagnostics overlays.
4. Then continue pack/template expansion for UX/QA and Agent-Builder reuse.

## Test Strategy
1. Schema tests:
- defaults/normalization/template constructors/semantic validators.

2. Registry tests:
- composition rules, conflict policy, requirement/safety analyzers, capability hooks.

3. Editor tests:
- field-spec rendering paths and guided/fallback round-trip behavior.

4. Runtime-coupled behavior tests:
- preview and renderer behavior across capability permutations.

## Handoff Notes
1. Use `current-key-priorities.md` for milestone status and next-slice plan.
2. Use `active-implementation-history.md` only for implementation chronology.
3. Keep persisted contract unchanged when adding builder UX capabilities.
