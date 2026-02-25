# Demo Builder Composition Template Authoring Reference Card
> Audience: QA, Product, and LLM engineers  
> Purpose: define and apply reusable composition templates with reliable renderer coverage, varied layout/style/content profiles, and plug-and-play runtime scenarios.

## Source of Truth
1. Template constructors and IDs:
- `frontend/src/components/Demo/builder/demoBuilderSchema.ts`
2. Renderer/runtime coverage envelope:
- `frontend/src/components/Demo/demo-docs/demo-testing-references/renderer-registry-test-matrix.md`
3. Existing QA composition payloads:
- `frontend/src/components/Demo/demo-docs/demo-testing-references/qa-demo-composition-reference.md`
4. Validation baseline tests:
- `frontend/tests-unit/demo-builder-schema.spec.ts`
- `frontend/tests-unit/demo-builder-capability-registry.spec.ts`
- `frontend/tests-unit/demo-builder-presentation-guided.spec.tsx`

## Current Built-In Template Inventory
1. `composition_a_baseline`
- Story runtime + chat + constant top instructions.
2. `composition_b_runtime_coupled`
- Adds `storyMetadata`, `orchestratorState`, `contributionFeed`.
3. `composition_c_visibility_semantics`
- Explicit `visible`/`hidden_mounted`/`hidden_unmounted` permutations.
4. `composition_d_stylized_agent_ops`
- Story/chat/participant + agent/tool/feed blocks with pre-applied visual treatment and seeded participant metadata.
5. `composition_e_tabs_content_studio`
- Tabs layout with content curation, git/file explorer blocks, and observer chat.
6. `composition_f_presentation_passthrough_audit`
- Full-surface pass-through audit across all active panel kinds and block types, with explicit expected-visual copy in rendered content/titles.

## Authoring Dimensions (Template Design Axes)
Use these axes to generate new templates systematically.

1. Layout axis
- `layout_mode`: `panels` or `tabs`
- panel split intent: primary/auxiliary sizing (`default_size`, `min_size`, `max_size`)

2. Runtime/persona axis
- `runtime_policy`: `auto`, `manual`, `owner_only`
- `persona_policy`: `first_available`, `manual_prompt`, `fixed_user_persona`
- `fixed_user_persona_id` when deterministic persona behavior is required

3. Panel mix axis
- Base: `storyRuntime`, `chat`
- Add-ons: `participantPanel`, `content`, `debug`, `storyEditor`, `storyPlayer`

4. Block mix axis
- Content/context: `content`, `context`
- Runtime-coupled: `storyMetadata`, `orchestratorState`, `contributionFeed`, `toolCapability`, `agentRoster`
- Workspace visuals: `gitView`, `fileExplorer`

5. Visibility axis
- `visibility`: `visible`, `hidden_mounted`, `hidden_unmounted`

6. Presentation/style axis
- composition: `page_theme_id`, `cards_theme_id`, `presentation_json`
- panel/block: `theme_id`, `presentation_json`

## Plug-and-Play Agent + Stylized Chat Pattern
This is the fastest path for the “seed agents + stylized chat” scenario.

1. Seed participants in metadata/options (authoring contract-safe pass-through)
```json
{
  "metadata_json": {
    "preloaded_participants": {
      "user_agent_config_ids": ["orchestrator", "coder", "analyst"],
      "activate_on_session_start": ["orchestrator", "coder"]
    }
  },
  "panels": [
    {
      "id": "participants",
      "kind": "participantPanel",
      "options": {
        "user_agent_config_ids": ["orchestrator", "coder", "analyst"]
      }
    }
  ]
}
```

## Presentation Pass-Through Audit Template (F)
Use this when teams report typography/CSS/animation/background/callout fields not applying.

1. Apply template:
- `composition_f_presentation_passthrough_audit`
2. Verify scope:
- all active panel kinds are present
- all active block types are present
- each panel/block carries non-trivial `presentation_json` and a descriptive title
3. Verify visual signals:
- composition-level font + motion + background changes
- panel header overlays and compact density settings
- block-level overlays/effects/density/typography overrides
4. Capture regressions:
- note exactly which level fails (`composition`, `panel`, or `block`)
- include panel/block id from the template for debugging

2. Stylize chat with theme + presentation hooks
```json
{
  "panels": [
    {
      "id": "chat-stylized",
      "kind": "chat",
      "theme_id": "qa-chat-neon",
      "presentation_json": {
        "typography": { "size": "sm" },
        "tokens": { "feed_density": "compact" },
        "effects": {
          "message_row_highlight": {
            "enable": true,
            "css": "inset 0 0 0 1px rgba(56,189,248,0.35), 0 8px 24px rgba(2,8,23,0.45)"
          }
        }
      }
    }
  ]
}
```

3. Add background/motion/callout treatment at composition level
```json
{
  "page_theme_id": "qa-aurora-page",
  "cards_theme_id": "qa-glass-cards",
  "presentation_json": {
    "typography": {
      "heading_font": "Space Grotesk",
      "body_font": "IBM Plex Sans"
    },
    "motion": {
      "panel_enter_ms": 260,
      "block_stagger_ms": 55
    },
    "backgrounds": {
      "page_gradient": "radial-gradient(1200px 500px at 20% 0%, rgba(0, 200, 255, 0.18), rgba(14, 18, 36, 0.9))",
      "svg_overlay": "grid-wave-v1"
    },
    "callouts": {
      "chat_notice": {
        "style": "frosted",
        "icon": "spark"
      }
    }
  }
}
```

## Template Construction Checklist (Cross-Team)
1. Define target mode:
- QA regression, product walkthrough, or LLM prompt-demo narrative.
2. Pick panel baseline:
- At minimum `storyRuntime` + `chat`, then add required companions.
3. Add content anchors:
- Include one always-visible top `content/context` block with instructions.
4. Add runtime-coupled blocks as needed:
- `storyMetadata`, `orchestratorState`, `contributionFeed`, `toolCapability`.
5. Add style profile:
- choose `page_theme_id`/`cards_theme_id`, then layer `presentation_json`.
6. Set assumptions for checklist:
- ensure `metadata_json.story_id` and confirmations for runtime/persona/chat as applicable.
7. Validate semantics:
- no error-level issues from builder validation panel.
8. Validate renderer fit:
- confirm chosen kinds/types are in the renderer matrix.

## Quick Capacity Map (What’s Safe to Template Today)
1. Safe/high-confidence:
- All active panel kinds in matrix, all active block kinds in matrix.
- Runtime-coupled block behavior permutations covered by tests.
- Visibility semantics and region ordering covered.
2. Needs extra validation when used heavily:
- very large capability maps
- ambiguous agent id/slug/name mapping
- deep async transition scenarios for runtime-coupled blocks

## Recommended New Template Profiles
1. `qa_regression_runtime_dense`
- A/B/C + D runtime blocks in one composition with explicit visibility permutations.
2. `product_walkthrough_tabs`
- tabs-first editorial composition with rich content callouts and observer chat.
3. `llm_ops_stylized_collab`
- stylized chat + seeded agents + tool capability matrix + orchestration status.
