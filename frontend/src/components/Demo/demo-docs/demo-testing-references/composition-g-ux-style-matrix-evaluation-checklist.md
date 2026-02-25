# Composition G Evaluation Checklist

Audience: UX, QA, Product, and Engineering reviewers with mixed technical background.

Purpose: help you evaluate whether Demo Builder styling and behavior controls are working as expected in `composition_g_ux_style_matrix`.

Companion docs:
- Quick mode (1-page): `frontend/src/components/Demo/demo-docs/demo-testing-references/composition-g-ux-style-matrix-quick-mode.md`
- Glossary: `frontend/src/components/Demo/demo-docs/demo-testing-references/demo-builder-style-glossary.md`

## What This Template Is For

`composition_g_ux_style_matrix` is a broad manual-review template that exercises:
- panel and block styling across all active kinds/types
- motion (entry timing/easing)
- overlays and backgrounds
- typography density/size shifts
- capability-specific behavior (chat/feed highlights, runtime callout banners)

Use this template when you want to answer:
- "Did my styling changes actually show up?"
- "Where do I set animation?"
- "How do I change block size/shape exactly?"
- "Which capabilities support which presentation behaviors?"

## Fast Start (No Engineering Required)

1. Open Demo Builder and apply template: `Composition G: UX Style Matrix Review`.
2. Make sure `story_id` is set in `metadata_json` so story-coupled panels/blocks render fully.
3. Open preview mode and compare:
- top-level composition visuals
- panel visuals
- block visuals
- runtime-coupled block behavior
4. Record pass/fail per section below.

## Pass/Fail Matrix

Use `Pass`, `Partial`, or `Fail` for each item.

### A) Global Composition Layer

- Page-level background gradient is visible (not flat default background).
- Top-level typography feels distinct from default demo style.
- Global motion feels consistent (panels/blocks enter smoothly).
- Visual layering is clear: page surface, cards surface, then local overrides.

### B) Panel Layer

- Panel header overlays render for configured panels (Story Runtime, Content, Participants).
- Chat panel shows compact density when configured.
- Panel-level motion timing differences are visible where configured.
- Panel visuals do not leak incorrectly to unrelated panels.

### C) Block Layer

- Top context/content blocks show clear style differentiation.
- Runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `toolCapability`, `contributionFeed`) display callout banners if configured.
- Contribution feed row highlight is visible on message rows.
- Block-level styling is local (changes in one block do not globally override other blocks unexpectedly).

### D) Capability Behavior Layer

- Chat-specific presentation settings affect chat behavior (density/highlight/callout).
- Contribution feed-specific settings affect feed row styling/callout.
- Runtime-coupled block callouts appear where configured.
- Capability-specific behavior remains readable and does not reduce usability.

## Common Questions (Quick Answers)

### How do I add animations here?

Use `presentation_json.motion`.

- Composition-level example:
`"motion": { "panel_enter_ms": 300, "block_stagger_ms": 70, "easing": "cubic-bezier(0.2, 0.9, 0.2, 1)" }`
- Panel-level example:
`"motion": { "panel_enter_ms": 360 }`
- Block-level example:
`"motion": { "block_enter_ms": 220 }` or `block_stagger_ms`

Tip: change one field at a time and re-check preview.

### How can I change block size/shape exactly?

There are two kinds of size/shape controls:

1. Layout size (panel geometry):
- `default_size`, `min_size`, `max_size`
- `prominence`, `viewport_mode`

2. Visual shape (surface styling):
- token-style fields in `presentation_json` (for example radius-related tokens where supported)
- backgrounds/overlays for perceived shape emphasis

Practical rule:
- If you want panel width/height behavior, change layout fields.
- If you want visual look/feel (rounded, framed, highlighted), change `presentation_json`.

### What capabilities exist for X, Y, Z?

Current high-value capability examples:

- Chat:
  - `tokens.feed_density`
  - `effects.message_row_highlight.{enable,css}`
  - `callouts.*.style`

- Contribution Feed:
  - `effects.message_row_highlight.css`
  - `callouts.*.style`
  - plus config-based behavior (`max_items`, `show_timestamps`, etc.)

- Runtime-coupled blocks (`storyMetadata`, `orchestratorState`, `toolCapability`):
  - callout styles (`callouts.*.style`)
  - overlay/background effects
  - block-local motion/typography settings

## Suggested Review Workflow By Persona

### UX reviewer

1. Focus on clarity, hierarchy, and visual consistency.
2. Flag any surfaces that feel visually "stuck" to defaults.
3. Flag any style settings that produce unreadable contrast or noisy motion.

### QA reviewer

1. Verify each configured setting is observable in UI.
2. Log exact setting path + expected result + actual result.
3. Check regression risk: does one change unexpectedly affect unrelated panels/blocks?

### Product reviewer

1. Confirm the template can represent intended demo storytelling style.
2. Identify missing controls needed for recurring demo scenarios.
3. Validate that setup flow is understandable for non-engineering users.

### Engineering reviewer

1. Confirm effect precedence works: composition -> panel/block -> capability behavior.
2. Verify no contract-shape drift (persisted schema unchanged).
3. Capture candidates for next capability-level expansion.

## Report Format (Copy/Paste)

Use this in tickets/slack:

```md
Template: composition_g_ux_style_matrix
Reviewer: <name/team>
Area: <global/panel/block/capability>
Setting path: <json path>
Expected: <what should happen>
Actual: <what happened>
Result: Pass | Partial | Fail
Screenshot/video: <link>
Notes: <optional>
```

## Where To Edit

- Template definition:
`frontend/src/components/Demo/builder/demoBuilderSchema.ts`
- Shared presentation interpreter:
`frontend/src/components/Demo/demoPresentationResolver.ts`
- Capability render behavior:
`frontend/src/components/Demo/rendererRegistry.tsx`
