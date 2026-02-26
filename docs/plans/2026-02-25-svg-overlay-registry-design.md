# SVG Overlay Registry Design

> Status: Approved
> Date: 2026-02-25
> Context: Priority 4 from presentation-customization-roadmap.md

## Overview

Implement an SVG overlay registry that maps preset names to inline SVG data URIs, enabling decorative background patterns via `presentation_json.backgrounds.svg_overlay`.

## Scope

### What We're Building

- Registry file with SVG patterns as data URIs
- Integration into `resolveEffectStyle()` for background layering
- Capability pack registration for demo builder UI

### Initial Presets

| Preset | Description | Opacity | Tile Size |
|--------|-------------|---------|-----------|
| `grid-wave-v1` | Horizontal wavy lines | 8% | 60x30px |
| `rings-grid-v2` | Concentric circles | 6% | 40x40px |
| `constellation-dots-v1` | Scattered dots pattern | 10% | 80x80px |

### Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Storage format | Inline data URI | No external fetching, works offline, bundled |
| Registry location | `svgOverlayRegistry.ts` | Keeps SVG strings separate from resolver |
| Integration point | `resolveEffectStyle()` | Already handles background layers |
| Color approach | `currentColor` | Adapts to theme automatically |

## Data Flow

```
presentation_json
  { "backgrounds": { "svg_overlay": "grid-wave-v1" } }
                    │
                    ▼
demoPresentationResolver.ts
  resolveEffectStyle() reads backgrounds.svg_overlay
  looks up in getSvgOverlayUrl()
                    │
                    ▼
svgOverlayRegistry.ts
  Returns: url("data:image/svg+xml,...")
                    │
                    ▼
backgroundImage CSS
  Layered: page_gradient, svg_overlay, card_pattern
```

## Layer Order

When multiple background types are specified, they stack:

1. `page_gradient` (top - most visible)
2. `svg_overlay` (middle - texture layer)
3. `card_pattern` (bottom - base pattern)

## Cascade Behavior

Each scope (composition, panel, block) resolves independently. No inheritance - if a panel doesn't specify `svg_overlay`, it won't inherit from composition.

## File Structure

```
Demo/
├── demoPresentationResolver.ts   # Import registry, update resolveEffectStyle
├── svgOverlayRegistry.ts         # NEW: Registry + SVG constants
└── builder/
    └── demoBuilderCapabilityRegistry.ts  # Add svg_overlay field spec
```

## Implementation Plan

### 1. Create svgOverlayRegistry.ts

```typescript
export const SVG_OVERLAY_PRESETS = [
  "grid-wave-v1",
  "rings-grid-v2",
  "constellation-dots-v1",
] as const

export type SvgOverlayPreset = typeof SVG_OVERLAY_PRESETS[number]

const SVG_OVERLAY_REGISTRY: Record<SvgOverlayPreset, string> = {
  "grid-wave-v1": `url("data:image/svg+xml,${encodeURIComponent(GRID_WAVE_SVG)}")`,
  // ...
}

export function getSvgOverlayUrl(preset: string): string | undefined {
  return SVG_OVERLAY_REGISTRY[preset as SvgOverlayPreset]
}
```

### 2. Update resolveEffectStyle()

```typescript
import { getSvgOverlayUrl } from "./svgOverlayRegistry"

function resolveEffectStyle(presentationJson: unknown): React.CSSProperties {
  // ... existing code ...
  const svgOverlay = getNestedString(presentationJson, "backgrounds", "svg_overlay")

  if (pageGradientCss || svgOverlay || cardPatternCss) {
    const layers: string[] = []
    if (pageGradientCss) layers.push(pageGradientCss)
    if (svgOverlay) {
      const svgUrl = getSvgOverlayUrl(svgOverlay)
      if (svgUrl) layers.push(svgUrl)
    }
    if (cardPatternCss) layers.push(cardPatternCss)
    style.backgroundImage = layers.join(", ")
  }
  // ...
}
```

### 3. Add capability pack field

Add `backgrounds.svg_overlay` enum field to composition capabilities.

## SVG Pattern Specifications

### grid-wave-v1

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="60" height="30">
  <path d="M0 15 Q15 5 30 15 T60 15"
        fill="none"
        stroke="currentColor"
        stroke-opacity="0.08"
        stroke-width="1"/>
</svg>
```

### rings-grid-v2

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40">
  <circle cx="20" cy="20" r="15"
          fill="none"
          stroke="currentColor"
          stroke-opacity="0.06"
          stroke-width="1"/>
</svg>
```

### constellation-dots-v1

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="80" height="80">
  <circle cx="10" cy="10" r="2" fill="currentColor" fill-opacity="0.1"/>
  <circle cx="50" cy="25" r="1.5" fill="currentColor" fill-opacity="0.08"/>
  <circle cx="30" cy="60" r="2" fill="currentColor" fill-opacity="0.1"/>
  <circle cx="70" cy="70" r="1" fill="currentColor" fill-opacity="0.06"/>
</svg>
```

## Testing

1. Verify default (no svg_overlay) renders without pattern
2. Verify each preset renders correctly
3. Test layering with page_gradient and card_pattern
4. Visual check in demo builder preview

## Usage

```json
{
  "presentation_json": {
    "backgrounds": {
      "svg_overlay": "grid-wave-v1",
      "page_gradient": "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)"
    }
  }
}
```
