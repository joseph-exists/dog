# Demo Builder Style Glossary

Purpose: plain-language definitions for style and layout terms used in Demo Builder, plus where each term appears in the kit.

## Core Terms

`Composition`
- Meaning: the full demo blueprint (all panels, blocks, settings).
- In kit: top-level JSON object in Demo Builder.

`Panel`
- Meaning: a major workspace section (for example Story Runtime, Chat).
- In kit: `composition.panels[]`.

`Block`
- Meaning: content/support card shown around panels (top/primary/auxiliary/footer).
- In kit: `composition.blocks[]`.

`Theme`
- Meaning: reusable set of style tokens (colors, surfaces, etc.).
- In kit: `page_theme_id`, `cards_theme_id`, and `theme_id` on panel/block.

`Presentation JSON`
- Meaning: per-scope visual tuning data (motion, overlays, effects, typography).
- In kit: `presentation_json` at composition, panel, and block levels.

## Layout and Sizing Terms

`layout_mode`
- Meaning: how panels are arranged (`panels` split view or `tabs`).
- In kit: `composition.layout_mode`.

`prominence`
- Meaning: whether a panel is primary vs auxiliary in split layout.
- In kit: `panel.prominence`.

`default_size` / `min_size` / `max_size`
- Meaning: panel sizing behavior in resizable layouts.
- In kit: `panel.default_size`, `panel.min_size`, `panel.max_size`.

`viewport_mode`
- Meaning: whether panel is standard panel view or page-sized mode.
- In kit: `panel.viewport_mode`.

`region`
- Meaning: where a block is rendered (`top`, `primary`, `auxiliary`, `footer`).
- In kit: `block.region`.

`visibility`
- Meaning: block visibility behavior.
- In kit: `block.visibility` (`visible`, `hidden_mounted`, `hidden_unmounted`).

## Style and Motion Terms

`overlays`
- Meaning: decorative header/surface treatment.
- In kit: `presentation_json.overlays.panel_header.css`, `presentation_json.overlays.block_header.css`.

`backgrounds`
- Meaning: background layers/patterns/gradients.
- In kit: `presentation_json.backgrounds.page_gradient`, `presentation_json.backgrounds.card_pattern.css`.

`motion`
- Meaning: timing/easing for entry and related transitions.
- In kit: `presentation_json.motion.panel_enter_ms`, `block_stagger_ms`, `block_enter_ms`, `easing`.

`typography`
- Meaning: text-level styling hints (font/size/line-height).
- In kit: `presentation_json.typography.*`.

`effects`
- Meaning: local visual effects (for example glow or row highlight).
- In kit: `presentation_json.effects.card_glow.*`, `presentation_json.effects.message_row_highlight.*`.

`callouts`
- Meaning: visual cue labels/banners used for emphasis.
- In kit: `presentation_json.callouts.*.style` (consumed by capability-aware renderers).

## Capability Terms

`Capability-level behavior`
- Meaning: renderer-specific behavior tied to a panel/block kind.
- In kit: implemented in `frontend/src/components/Demo/rendererRegistry.tsx`.

`Runtime-coupled blocks`
- Meaning: blocks that reflect live room/runtime state.
- In kit: `storyMetadata`, `orchestratorState`, `contributionFeed`, `toolCapability`.

`Guided fields`
- Meaning: form controls for known presentation paths, with JSON fallback.
- In kit: Demo Builder editors + capability registry metadata.

## Theme Cascade Terms

`Page theme`
- Meaning: style scope for page shell/surfaces.
- In kit: `page_theme_id`, resolved in shell wrappers.

`Cards theme`
- Meaning: style scope for card/content surfaces.
- In kit: `cards_theme_id`.

`Instance override`
- Meaning: nearest-level style override for a specific panel or block.
- In kit: panel/block `theme_id` + local `presentation_json`.

`Cascade order`
- Meaning: style precedence from broad to local.
- In kit: application defaults -> page theme -> cards theme -> instance-level overrides.

## Where To Look In Code

- Shared cascade docs:
`frontend/src/components/Common/Themes/CASCADING-THEMES.md`

- Quick reference:
`frontend/src/components/Agents/docs/THEME-CASCADE-REFERENCE.md`

- Demo style resolver:
`frontend/src/components/Demo/demoPresentationResolver.ts`

- Demo capability render behavior:
`frontend/src/components/Demo/rendererRegistry.tsx`

- Composition templates:
`frontend/src/components/Demo/builder/demoBuilderSchema.ts`
