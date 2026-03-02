# Color Tests Reference

This document explains why [color-tests.json](/home/josep/dog/frontend/docs/color-tests.json) works.

It is intended for:

- QA validating whether demo styling is rendering
- product reviewing what is currently supported
- UX authors building new demo-builder payloads

This is a contract-valid example.
It only uses styling fields that the current demo resolver and panel/block renderers actually consume.

## How To Use It

Use the JSON file as a copy-paste starter for a styled demo.

Recommended workflow:

1. Create a demo with panels/blocks that match your use case.
2. Copy one section at a time from `color-tests.json`.
3. Save and verify the change is visually obvious.
4. Only after that, layer on more styling.

Do not start by inventing new keys.
If a field is not already part of the supported contract, it will usually be ignored.

## Supported Categories Covered

The example intentionally covers the broader supported surface:

- composition-level motion
- composition-level typography
- composition-level gradient backgrounds
- composition-level SVG overlays
- composition-level glow effects
- composition-level callouts
- CSS custom property pass-through via `--prefixed` token keys
- panel header overlays
- panel callouts
- panel motion
- chat row highlight styling
- block card patterns
- block glow effects
- block header overlays
- block callouts
- density tokens for supported runtime components

## Composition-Level Styling

The top-level `presentation_json` demonstrates the safest global styling levers:

### `motion`

```json
"motion": {
  "panel_enter_ms": 320,
  "block_stagger_ms": 90,
  "easing": "cubic-bezier(0.22, 1, 0.36, 1)"
}
```

Use this for:

- making panels animate in
- staggering block entry
- testing that motion is visibly active

### `typography`

```json
"typography": {
  "size": "sm",
  "line_height": "relaxed",
  "heading_font": "Space Grotesk",
  "body_font": "IBM Plex Sans"
}
```

Use this for:

- overall type scale
- line-height changes
- heading/body font family changes

Important:

- only supported size tokens are useful here
- fonts should be readable and obviously different when testing

### `backgrounds`

```json
"backgrounds": {
  "page_gradient": "...",
  "svg_overlay": "grid-wave-v1"
}
```

Use this for:

- visible page-wide color treatment
- subtle pattern overlays behind the demo

If you want a demo to look obviously styled, `page_gradient` is one of the most reliable first changes.

### `effects.card_glow`

```json
"effects": {
  "card_glow": {
    "enable": true,
    "css": "..."
  }
}
```

Use this for:

- colored glow around framed containers
- making card surfaces feel more atmospheric

### `callouts`

```json
"callouts": {
  "header": { "style": "neon-frame", "text": "Color Ramp Demo", "icon": "palette" },
  "footer": { "style": "glass-pill", "text": "Composition-level motion, fonts, overlays, and glow", "icon": "sparkles" }
}
```

Use this for:

- visible labels that tell reviewers which styling layer they are looking at
- making it obvious whether callout rendering is active

### `tokens`

```json
"tokens": {
  "--demo-accent-primary": "#ff6b9d"
}
```

This is only useful for CSS custom property pass-through.

Rules:

- keys must be actual CSS variables
- keys must start with `--`
- descriptive keys like `"accentColor"` do not work here

## Panel-Level Styling

The payload includes 4 panels to show different supported patterns.

### Chat Panel

The chat panel demonstrates:

- `typography.size`
- `tokens.feed_density`
- `effects.message_row_highlight`
- `overlays.panel_header.css`
- `callouts.header`

This is the best pattern to copy when UX wants “more colorful chat” within the current contract.

Important limitation:

- bubble-level user/assistant colors are not currently controlled by `presentation_json`
- use row highlights, header overlays, and callouts instead

### Content Panel

The content panel demonstrates:

- `motion.panel_enter_ms`
- `overlays.panel_header.css`
- `callouts.footer`

This is useful when you want a documentation or briefing panel to feel styled without depending on special renderer behavior.

### Participant Panel

The participant panel demonstrates:

- `overlays.panel_header.css`
- `callouts.footer`

This is a good example of shell styling on a panel that does not consume many presentation-specific options itself.

### Debug Panel

The debug panel demonstrates:

- `typography.size = "xs"`
- `overlays.panel_header.css`

Use this pattern when you want supporting/debug surfaces to feel visually secondary.

## Block-Level Styling

The payload includes several blocks with different supported treatments.

### `context` Block

The `color-hero` block demonstrates:

- block-local typography
- `backgrounds.card_pattern.css`
- custom glow via `effects.card_glow.css`
- callout banner styling

This is a good “hero block” pattern.

### `content` Block

The `css-vars-note` and footer guide blocks demonstrate:

- card patterns
- block header overlays
- header/footer callouts

These are strong starter patterns for QA/Product notes and onboarding instructions.

### `orchestratorState`

This block demonstrates:

- `tokens.stack_density`
- `overlays.block_header.css`
- callout styling

Use this pattern when testing compact/comfortable stack-based layouts.

### `toolCapability`

This block demonstrates:

- `tokens.matrix_density`
- local glow
- footer callout

Use this when testing dense matrix-like information displays.

### `contributionFeed`

This block demonstrates:

- `tokens.feed_density`
- `effects.message_row_highlight.css`
- callout styling

This is the block equivalent of the chat panel styling pattern.

### `agentRoster`

This block demonstrates:

- `backgrounds.card_pattern.css`
- footer callout

Use it as a lightweight example of “styled but not overloaded.”

## Density Tokens

These tokens only matter where specific renderers consume them:

- `tokens.feed_density`
  Used by chat/contribution-feed style surfaces
- `tokens.stack_density`
  Used by orchestrator-state style surfaces
- `tokens.matrix_density`
  Used by tool-capability style surfaces

If you apply these tokens to unrelated components, nothing visible may happen.

## Fields That Commonly Fail

These patterns are commonly reported and are usually ignored:

- `metadata_json.theme`
- `metadata_json.colors`
- `presentation_json.theme`
- `presentation_json.backgroundColor`
- `presentation_json.headerGradient`
- `presentation_json.accentColor`
- `presentation_json.secondaryAccent`
- `presentation_json.bubbleColors`

If you want visible styling, prefer:

- `backgrounds.page_gradient`
- `backgrounds.svg_overlay`
- `backgrounds.card_pattern.css`
- `effects.card_glow`
- `effects.message_row_highlight`
- `overlays.panel_header.css`
- `overlays.block_header.css`
- `callouts.*`
- supported density tokens
- `theme_id`, `page_theme_id`, `cards_theme_id`

## QA Checklist

When validating a styled demo, check these visibly:

1. The page background should show a gradient or overlay, not flat default background.
2. Panels with `overlays.panel_header.css` should have visibly colored headers.
3. Blocks with `overlays.block_header.css` should have visibly distinct headers.
4. Callouts should render at header/footer positions where configured.
5. Chat and contribution surfaces should show denser spacing when `feed_density` is compact.
6. Glow effects should be visible on blocks/panels configured with `card_glow`.
7. Typography changes should be obvious enough to notice without inspecting JSON.

## Authoring Guidance

For demo-builder users, the safest authoring order is:

1. Start with composition-level `page_gradient`.
2. Add one panel overlay.
3. Add one block callout.
4. Add one glow effect.
5. Add density tokens only where the target renderer supports them.

That order makes failures easy to isolate.

If a styling change is not visually obvious, assume the field may be unsupported until proven otherwise.
