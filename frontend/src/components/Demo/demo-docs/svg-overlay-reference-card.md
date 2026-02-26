# SVG Overlay Reference Card

> Quick reference for using and extending SVG background overlays in demo presentations.

---

## Quick Start (Demo Authors)

Add an SVG overlay pattern to your composition's `presentation_json`:

```json
{
  "presentation_json": {
    "backgrounds": {
      "svg_overlay": "grid-wave-v1"
    }
  }
}
```

Combine with gradients for layered effects:

```json
{
  "presentation_json": {
    "backgrounds": {
      "page_gradient": "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)",
      "svg_overlay": "constellation-dots-v1",
      "card_pattern": "radial-gradient(circle at 50% 50%, rgba(255,255,255,0.03) 0%, transparent 70%)"
    }
  }
}
```

---

## Available Presets

| Preset | Description | Best For |
|--------|-------------|----------|
| `grid-wave-v1` | Horizontal wavy lines (60×30px tile, 8% opacity) | Tech/modern aesthetics |
| `rings-grid-v2` | Concentric circles (40×40px tile, 6% opacity) | Professional/clean designs |
| `constellation-dots-v1` | Scattered dots (80×80px tile, 6-10% opacity) | Dark backgrounds, space themes |

---

## Layer Order

When multiple backgrounds are specified, they stack in CSS `background-image` order:

```
┌─────────────────────────────────┐
│  page_gradient (top, visible)   │
├─────────────────────────────────┤
│  svg_overlay (middle, texture)  │
├─────────────────────────────────┤
│  card_pattern (bottom, base)    │
└─────────────────────────────────┘
```

Each layer shows through transparent areas of layers above it.

---

## Enabling in Demo Builder

Add the capability pack to your environment:

```bash
# .env or .env.local
VITE_DEMO_BUILDER_PACKS=presentation.svg-overlays.v1
```

Multiple packs can be comma-separated:

```bash
VITE_DEMO_BUILDER_PACKS=typography.fonts.v1,presentation.callouts.v1,presentation.svg-overlays.v1
```

---

## Adding New Patterns (Engineers)

### Step 1: Design Your SVG

Follow these design guidelines:

- **Use `currentColor`** for strokes/fills so patterns adapt to themes
- **Keep opacity low** (6-12%) for subtle background texture
- **Design for seamless tiling** (edges should connect when repeated)
- **Keep it simple** (<1KB) to minimize bundle size

Example pattern:

```svg
<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50">
  <path d="M0 25 L25 0 L50 25 L25 50 Z"
        fill="none"
        stroke="currentColor"
        stroke-opacity="0.06"
        stroke-width="1"/>
</svg>
```

### Step 2: Add to Registry

Edit `svgOverlayRegistry.ts`:

```typescript
// 1. Add your SVG as a constant
const DIAMOND_GRID_SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="50" height="50" viewBox="0 0 50 50">
  <path d="M0 25 L25 0 L50 25 L25 50 Z" fill="none" stroke="currentColor" stroke-opacity="0.06" stroke-width="1"/>
</svg>`

// 2. Add preset name to the array
export const SVG_OVERLAY_PRESETS = [
  "grid-wave-v1",
  "rings-grid-v2",
  "constellation-dots-v1",
  "diamond-grid-v1",  // NEW
] as const

// 3. Add to the registry object
const SVG_OVERLAY_REGISTRY: Record<SvgOverlayPreset, string> = {
  "grid-wave-v1": encodeSvgAsUrl(GRID_WAVE_SVG),
  "rings-grid-v2": encodeSvgAsUrl(RINGS_GRID_SVG),
  "constellation-dots-v1": encodeSvgAsUrl(CONSTELLATION_DOTS_SVG),
  "diamond-grid-v1": encodeSvgAsUrl(DIAMOND_GRID_SVG),  // NEW
}
```

### Step 3: Verify

The new preset is automatically available:
- In `presentation_json.backgrounds.svg_overlay`
- In the demo builder UI (if pack is enabled)

No changes needed to resolver or capability registry.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     presentation_json                            │
│         { "backgrounds": { "svg_overlay": "grid-wave-v1" } }    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│               demoPresentationResolver.ts                        │
│                    resolveEffectStyle()                          │
│                           │                                      │
│                           ▼                                      │
│              getSvgOverlayUrl("grid-wave-v1")                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  svgOverlayRegistry.ts                           │
│                                                                  │
│   Returns: url("data:image/svg+xml,%3Csvg...")                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   CSS backgroundImage                            │
│                                                                  │
│   "linear-gradient(...), url('data:...'), radial-gradient(...)" │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Locations

| File | Purpose |
|------|---------|
| `Demo/svgOverlayRegistry.ts` | SVG patterns + lookup function |
| `Demo/demoPresentationResolver.ts` | Reads presentation_json, calls registry |
| `Demo/builder/demoBuilderCapabilityRegistry.ts` | Exposes field in builder UI |

---

## Cascade Behavior

Each scope resolves independently—**no inheritance**:

| Scope | Reads From | Effect |
|-------|------------|--------|
| Composition | `composition.presentation_json.backgrounds.svg_overlay` | Applies to composition container |
| Panel | `panel.presentation_json.backgrounds.svg_overlay` | Applies to panel container |
| Block | `block.presentation_json.backgrounds.svg_overlay` | Applies to block container |

If a panel specifies its own `svg_overlay`, it uses that value, not the composition's.

---

## Troubleshooting

### Pattern not showing

1. **Check preset name** - Must match exactly (case-sensitive)
2. **Check layer order** - Opaque gradients above will hide the pattern
3. **Check pack enabled** - For builder UI, verify `VITE_DEMO_BUILDER_PACKS`

### Pattern too visible/subtle

Adjust opacity in the SVG definition:
- `stroke-opacity="0.04"` for very subtle
- `stroke-opacity="0.08"` for moderate (default)
- `stroke-opacity="0.12"` for more visible

### Pattern doesn't tile correctly

Ensure SVG `width`, `height`, and `viewBox` are consistent and the pattern edges connect seamlessly.

### Theme colors not working

Verify using `currentColor` instead of hardcoded colors:
```svg
<!-- Good -->
<circle stroke="currentColor" stroke-opacity="0.08" />

<!-- Bad - won't adapt to themes -->
<circle stroke="#ffffff" stroke-opacity="0.08" />
```

---

## Related Documentation

- [Presentation Customization Roadmap](./presentation-customization-roadmap.md)
- [SVG Overlay Registry Design](../../../../docs/plans/2026-02-25-svg-overlay-registry-design.md)
- [Theme Cascade Reference](./THEME-CASCADE-REFERENCE.md)
