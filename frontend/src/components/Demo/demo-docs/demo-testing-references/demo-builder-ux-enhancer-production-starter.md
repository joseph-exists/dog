# Demo Builder UX Production Starter (`example.ux-enhancer.v1`)

## Purpose

This starter gives UX/product teams a practical path to author high-impact demo presentation payloads using:

- `page_theme_id`
- `cards_theme_id`
- `presentation_json`

It is designed for progressive rollout from simple polish to complex visual storytelling.

For A/B/C composition-specific copy/paste presets, see:

- `frontend/src/components/Demo/demo-docs/demo-testing-references/demo-builder-ux-enhancer-presentation-presets.md`

## Important Scope Note

`presentation_json` is a contract-safe, free-form metadata surface.  
Use the snippets below as the shared UX-to-engineering payload convention for theming/render behavior.  
Some keys may require renderer/theme-token wiring depending on current implementation depth.

## Quick Start

1. Enable pack:
```bash
VITE_DEMO_BUILDER_PACKS=example.ux-enhancer.v1
```
2. Open Demo Builder and select a demo config.
3. In top-level composition fields:
- set `Page Theme Preset` (`page_theme_id`)
- set `Card Theme Preset` (`cards_theme_id`)
- paste one of the `presentation_json` snippets below
4. Save and validate in `/demo/{slug}`.

## Suggested `presentation_json` Convention

Use this top-level structure so UX and engineering can iterate without churn:

```json
{
  "typography": {},
  "motion": {},
  "overlays": {},
  "backgrounds": {},
  "effects": {},
  "tokens": {}
}
```

## Simple To Complex Snippet Library

### Level 1: Simple (Typography + Basic Motion)

Use for quick visual uplift with minimal risk.

```json
{
  "typography": {
    "font_family_ui": "\"Space Grotesk\", \"Inter\", sans-serif",
    "font_family_display": "\"Fraunces\", serif",
    "scale": "comfortable",
    "tracking": "normal"
  },
  "motion": {
    "enable": true,
    "duration_ms": 180,
    "easing": "ease-out",
    "reduce_motion_respect": true
  }
}
```

### Level 2: Moderate (Overlay + SVG Background Layer)

Use for branded atmosphere while keeping readability high.

```json
{
  "overlays": {
    "header_gradient": {
      "enable": true,
      "css": "linear-gradient(120deg, rgba(16,185,129,0.18), rgba(59,130,246,0.14))"
    },
    "card_tint": {
      "enable": true,
      "css": "rgba(255,255,255,0.04)"
    }
  },
  "backgrounds": {
    "canvas_svg": {
      "enable": true,
      "type": "inline_svg_data_uri",
      "svg_data_uri": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='140' height='140' viewBox='0 0 140 140'%3E%3Cg fill='none' stroke='%23ffffff' stroke-opacity='0.08'%3E%3Cpath d='M0 70h140M70 0v140'/%3E%3C/g%3E%3C/svg%3E",
      "size": "140px 140px",
      "blend_mode": "soft-light",
      "opacity": 0.5
    }
  }
}
```

### Level 3: Advanced (Layered Motion + Focused Visual Language)

Use for showcase demos with stronger narrative identity.

```json
{
  "typography": {
    "font_family_ui": "\"Sora\", \"Inter\", sans-serif",
    "font_family_display": "\"DM Serif Display\", serif",
    "weights": {
      "body": 400,
      "heading": 600,
      "accent": 700
    }
  },
  "motion": {
    "enable": true,
    "stagger": {
      "panel_ms": 70,
      "block_ms": 45
    },
    "transitions": {
      "panel_enter": "cubic-bezier(0.22, 1, 0.36, 1)",
      "block_hover": "cubic-bezier(0.16, 1, 0.3, 1)"
    },
    "reduce_motion_respect": true
  },
  "overlays": {
    "backdrop": {
      "enable": true,
      "css": "radial-gradient(circle at 20% 10%, rgba(244,114,182,0.12), transparent 35%), radial-gradient(circle at 85% 0%, rgba(59,130,246,0.15), transparent 40%)"
    }
  },
  "backgrounds": {
    "canvas_svg": {
      "enable": true,
      "type": "inline_svg_data_uri",
      "svg_data_uri": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='120' viewBox='0 0 240 120'%3E%3Cg fill='none' stroke='%23ffffff' stroke-opacity='0.07'%3E%3Cpath d='M0 100c40-20 80-20 120 0s80 20 120 0'/%3E%3Cpath d='M0 80c40-20 80-20 120 0s80 20 120 0'/%3E%3C/g%3E%3C/svg%3E",
      "size": "240px 120px",
      "opacity": 0.65
    }
  },
  "effects": {
    "card_glow": {
      "enable": true,
      "css": "0 0 0 1px rgba(255,255,255,0.06), 0 12px 36px rgba(15,23,42,0.28)"
    }
  }
}
```

## Panel/Block Scoped Overrides

For targeted treatment, use `presentation_json` on specific panel/block entries.

### Panel Example (Chat panel emphasis)

```json
{
  "overlays": {
    "panel_header": {
      "enable": true,
      "css": "linear-gradient(90deg, rgba(14,165,233,0.18), rgba(139,92,246,0.12))"
    }
  },
  "motion": {
    "panel_enter_ms": 140
  }
}
```

### Block Example (Story metadata readability mode)

```json
{
  "typography": {
    "size": "sm",
    "line_height": "relaxed"
  },
  "backgrounds": {
    "card_pattern": {
      "enable": true,
      "css": "repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0, rgba(255,255,255,0.02) 2px, transparent 2px, transparent 10px)"
    }
  }
}
```

## Walkthrough (Simple -> Complex)

1. Baseline polish (Level 1)
- Set `page_theme_id` and `cards_theme_id`
- Apply Level 1 snippet
- Validate legibility and spacing on desktop + mobile

2. Brand atmosphere (Level 2)
- Add overlay + SVG background
- Check contrast for text over overlays
- Verify no visual noise in dense block layouts

3. Showcase mode (Level 3)
- Add staggered motion + richer backgrounds/effects
- Test reduced-motion behavior
- Confirm chat/story/runtime panels remain readable and performant

## Review Checklist For UX + Eng

1. Accessibility:
- contrast on primary text and controls
- motion respects reduced-motion preferences

2. Visual consistency:
- typography hierarchy stays coherent across panels
- overlays do not reduce content clarity

3. Runtime safety:
- builder validators pass
- pack safety/expectation analyzers pass

4. Performance:
- animations stay smooth on mid-range hardware
- SVG backgrounds are optimized (small data URI payloads)

## Recommended Activation Profiles

1. Team sandbox:
```bash
VITE_DEMO_BUILDER_PACKS=example.ux-enhancer.v1
```
2. UX + runtime-safe combo:
```bash
VITE_DEMO_BUILDER_PACKS=example.runtime-safe.v1,example.ux-enhancer.v1
```
3. Governance review:
```bash
VITE_DEMO_BUILDER_PACKS=example.policy-guarded.v1
```
