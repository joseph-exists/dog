# Demo Builder UX Enhancer Presentation Presets (A/B/C)

## Purpose

Copy/paste-ready `presentation_json` bundles for demo compositions:

- Composition A: baseline story/chat + constant instructional content
- Composition B: runtime-coupled visibility for story/orchestrator/feed
- Composition C: visibility-semantics stress (`visible`, `hidden_mounted`, `hidden_unmounted`)

These presets are designed for `example.ux-enhancer.v1`.

## How To Apply

1. Enable pack:
```bash
VITE_DEMO_BUILDER_PACKS=example.ux-enhancer.v1
```
2. Use one of the JSON snippets below in:
- top-level composition `presentation_json` (recommended baseline)
- panel `presentation_json` override (targeted emphasis)
- block `presentation_json` override (local readability/focus)
3. Save and validate in the matching demo composition flow.

## Composition A Presets

### A1) Baseline Polish (safe default)

```json
{
  "typography": {
    "font_family_ui": "\"Space Grotesk\", \"Inter\", sans-serif",
    "font_family_display": "\"Fraunces\", serif",
    "scale": "comfortable"
  },
  "motion": {
    "enable": true,
    "duration_ms": 160,
    "easing": "ease-out",
    "reduce_motion_respect": true
  },
  "tokens": {
    "surface_radius": "12px",
    "card_padding": "12px"
  }
}
```

### A2) Story+Chat Split Emphasis (panel override for `storyRuntime`)

```json
{
  "overlays": {
    "panel_header": {
      "enable": true,
      "css": "linear-gradient(90deg, rgba(14,165,233,0.18), rgba(16,185,129,0.1))"
    }
  },
  "motion": {
    "panel_enter_ms": 140
  }
}
```

### A3) Instruction Block Readability (block override for `context`/`content`)

```json
{
  "typography": {
    "size": "sm",
    "line_height": "relaxed"
  },
  "effects": {
    "card_glow": {
      "enable": false
    }
  }
}
```

## Composition B Presets

### B1) Runtime-Coupled Clarity Baseline

```json
{
  "typography": {
    "font_family_ui": "\"Sora\", \"Inter\", sans-serif",
    "font_family_display": "\"DM Serif Display\", serif"
  },
  "backgrounds": {
    "canvas_svg": {
      "enable": true,
      "type": "inline_svg_data_uri",
      "svg_data_uri": "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160' viewBox='0 0 160 160'%3E%3Cg fill='none' stroke='%23ffffff' stroke-opacity='0.07'%3E%3Cpath d='M0 80h160M80 0v160'/%3E%3C/g%3E%3C/svg%3E",
      "size": "160px 160px",
      "opacity": 0.45
    }
  },
  "motion": {
    "enable": true,
    "stagger": {
      "panel_ms": 55,
      "block_ms": 40
    },
    "reduce_motion_respect": true
  }
}
```

### B2) Orchestrator Attention Mode (block override for `orchestratorState`)

```json
{
  "overlays": {
    "block_header": {
      "enable": true,
      "css": "linear-gradient(90deg, rgba(251,191,36,0.2), rgba(249,115,22,0.14))"
    }
  },
  "tokens": {
    "status_badge_style": "high-contrast"
  }
}
```

### B3) Contribution Feed Signal (block override for `contributionFeed`)

```json
{
  "typography": {
    "size": "sm",
    "tracking": "normal"
  },
  "effects": {
    "message_row_highlight": {
      "enable": true,
      "css": "inset 0 0 0 1px rgba(255,255,255,0.06)"
    }
  }
}
```

## Composition C Presets

### C1) Visibility-Semantics Diagnostic Theme

```json
{
  "typography": {
    "font_family_ui": "\"IBM Plex Sans\", \"Inter\", sans-serif",
    "font_family_display": "\"Merriweather\", serif"
  },
  "overlays": {
    "state_legend": {
      "enable": true,
      "css": "linear-gradient(120deg, rgba(59,130,246,0.12), rgba(244,114,182,0.1))"
    }
  },
  "tokens": {
    "visibility_visible_badge": "#22c55e",
    "visibility_hidden_mounted_badge": "#f59e0b",
    "visibility_hidden_unmounted_badge": "#ef4444"
  }
}
```

### C2) Hidden-Mounted Traceability (block override)

```json
{
  "effects": {
    "mounted_state_ring": {
      "enable": true,
      "css": "0 0 0 1px rgba(245,158,11,0.5)"
    }
  },
  "tokens": {
    "state_hint_label": "mounted-not-visible"
  }
}
```

### C3) Hidden-Unmounted Minimal Surface (block override)

```json
{
  "effects": {
    "unmounted_surface_reduction": {
      "enable": true,
      "css": "opacity(0.78)"
    }
  },
  "tokens": {
    "state_hint_label": "not-mounted"
  }
}
```

## Recommended A/B/C Starting Matrix

1. A: apply `A1` at composition-level, `A2` on story panel, `A3` on top context block.
2. B: apply `B1` at composition-level, `B2` on orchestrator block, `B3` on contribution feed block.
3. C: apply `C1` at composition-level, then add `C2` to hidden-mounted targets and `C3` to hidden-unmounted targets.

## Validation Checklist

1. Text remains readable in all panels and block regions.
2. Reduced-motion preference is respected when motion is enabled.
3. A/B/C runtime behavior is unchanged; only presentation metadata changed.
4. Builder semantic validators remain clean or expected warnings are understood.
