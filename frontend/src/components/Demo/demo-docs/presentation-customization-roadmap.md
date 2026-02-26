# Demo Presentation Customization Roadmap

> Status: Working Draft
> Last Updated: 2026-02-25
> Context: Templates D-G cleaned up to use only implemented fields
> Recent: Density tokens implemented (Priority 2 complete), Callout system implemented (Priority 3 complete), Font loading system implemented (Priority 1 complete)

## Current State

### What Works (in `demoPresentationResolver.ts`)

| Feature | Fields | Notes |
|---------|--------|-------|
| **Motion** | `panel_enter_ms`, `block_enter_ms`, `block_stagger_ms`, `easing` | Returns timing values for animations |
| **Typography** | `size` (xs/sm/base/lg), `line_height` (tight/normal/relaxed) | Maps to CSS fontSize/lineHeight |
| **Backgrounds** | `page_gradient`, `card_pattern.css` | Applied as `backgroundImage` |
| **Effects** | `card_glow.enable/css`, `message_row_highlight.enable/css` | Applied as `boxShadow` |
| **Overlays** | `panel_header.css`, `block_header.css`, `header.css` | Returned as `overlayCss` for wrappers |
| **CSS Variables** | `tokens.*`, `theme_tokens.*`, `css_vars.*` | Any `--prefixed` key applied inline |

### What Doesn't Work (documented but not consumed)

| Feature | Fields | Gap |
|---------|--------|-----|
| ~~**Font Families**~~ | ~~`typography.heading_font`, `typography.body_font`~~ | ✅ **IMPLEMENTED** - See Priority 1 |
| **SVG Overlays** | `backgrounds.svg_overlay` | String hint only; no asset loader |
| ~~**Callouts**~~ | ~~`callouts.*`~~ | ✅ **IMPLEMENTED** - See Priority 3 |
| ~~**Density Tokens**~~ | ~~`feed_density`, `stack_density`, `matrix_density`~~ | ✅ **IMPLEMENTED** - See Priority 2 |
| **Style Hints** | `status_badge_style`, `surface_radius` | Capability-specific; renderers must consume |

---

## Priority 1: Font Loading System ✅ IMPLEMENTED

**Problem:** `typography.heading_font` and `typography.body_font` are specified but never applied.

**Solution Implemented:** Dynamic Google Fonts loader with CSS custom properties

### Implementation Details (2026-02-25)

The font loading system was implemented following the capability registry pattern:

#### 1. Capability Pack (`demoBuilderCapabilityRegistry.ts`)

Added `typography.fonts.v1` pack that extends all panel and block capabilities with font field specs:

```typescript
export const TYPOGRAPHY_FONT_PRESETS = [
  "system",      // Uses default --font-sans stack
  "Inter",
  "Space Grotesk",
  "IBM Plex Sans",
  "JetBrains Mono",
  "Playfair Display",
  "Source Sans Pro",
  "Lora",
  "Fira Code",
  "Work Sans",
] as const
```

To enable: Add `typography.fonts.v1` to `VITE_DEMO_BUILDER_PACKS` env variable.

#### 2. Presentation Resolver (`demoPresentationResolver.ts`)

Added `resolveFontStyle()` function that:
- Reads `typography.heading_font` and `typography.body_font` from presentation_json
- Outputs CSS custom properties: `--font-heading`, `--font-body`
- Collects font family names for dynamic loading
- Skips "system" value (uses default font stack)

#### 3. Font Loading Hook (`DemoPresentationFrame.tsx`)

Added `useFontLoader()` hook that:
- Injects Google Fonts `<link>` tags into document.head
- Deduplicates fonts via `data-demo-font` attribute
- Persists links after unmount (fonts are page-level resources)
- Includes weights 400, 500, 600, 700 for heading/body needs

#### 4. CSS Consumption (`demo-themes.css`)

Added rules that apply font variables to demo elements:
- `.demo-shell h1, h2, h3, [class*="heading"], [class*="title"]` → `--font-heading`
- `.demo-shell p, span, li, [class*="content"], [class*="text"]` → `--font-body`
- Code elements preserve `--font-mono`

### Usage

```json
{
  "presentation_json": {
    "typography": {
      "heading_font": "Space Grotesk",
      "body_font": "Inter"
    }
  }
}
```

**Complexity:** Low-Medium
**Impact:** High - enables any Google Font with dynamic loading

---

## Priority 2: Capability-Aware Token Consumption ✅ IMPLEMENTED

**Problem:** Tokens like `feed_density: "compact"` are passed through but not consumed by renderers.

**Solution Implemented:** Preset-based density class mappings in each block component

### Implementation Details (2026-02-25)

The density token system follows a preset-based approach where each density value maps to a bundle of Tailwind classes.

#### 1. Renderer Registry (`rendererRegistry.tsx`)

Added parse functions for each density token:

```typescript
function parseContributionFeedPresentation(presentationJson: unknown): {
  feedDensity: "comfortable" | "compact"
  // ... other fields
}

function parseOrchestratorStatePresentation(presentationJson: unknown): {
  stackDensity: "comfortable" | "compact"
  // ... other fields
}

function parseToolCapabilityPresentation(presentationJson: unknown): {
  matrixDensity: "standard" | "compact"
  // ... other fields
}
```

#### 2. Block Components

Each block defines a density class mapping object:

```typescript
// Example from ContributionFeedBlock.tsx
const FEED_DENSITY_CLASSES = {
  comfortable: {
    container: "p-4",
    sections: "space-y-4",
    card: "p-3",
    cardInner: "p-2.5",
    items: "space-y-2",
  },
  compact: {
    container: "p-2",
    sections: "space-y-2",
    card: "p-2",
    cardInner: "p-1.5",
    items: "space-y-1",
  },
} as const
```

Components receive density as a prop and apply classes via `cn()`:

```tsx
const density = FEED_DENSITY_CLASSES[feedDensity]
return (
  <div className={cn(density.container, density.sections)}>
    {/* ... */}
  </div>
)
```

#### 3. Extensibility

Inline comments mark extension points for future per-property overrides:

```typescript
// Future: If per-property overrides are needed, add tokens like
// tokens.feed_container_padding that take precedence over preset values
```

### Usage

```json
{
  "presentation_json": {
    "tokens": {
      "feed_density": "compact",
      "stack_density": "compact",
      "matrix_density": "compact"
    }
  }
}
```

### Components Affected

| Component | Token | Values |
|-----------|-------|--------|
| `DemoChatPanel` | `feed_density` | comfortable (default), compact |
| `ContributionFeedBlock` | `feed_density` | comfortable (default), compact |
| `OrchestratorStateBlock` | `stack_density` | comfortable (default), compact |
| `ToolCapabilityBlock` | `matrix_density` | standard (default), compact |

**Complexity:** Low-Medium
**Impact:** Medium - enables fine-grained layout control per block

---

## Priority 3: Callout System ✅ IMPLEMENTED

**Problem:** `callouts.*` is documented but not rendered.

**Solution Implemented:** Page primitive component with capability pack integration

### Implementation Details (2026-02-25)

The callout system follows the established architecture: Page/ primitives provide the component, Demo/ consumes it via presentation_json.

#### 1. Page Primitives (`Page/primitives/Callout/`)

Created a complete Callout primitive module:

```typescript
// types.ts - Core type definitions
export type CalloutStylePreset =
  | "frosted"
  | "neon-frame"
  | "glass-pill"
  | "framed-note"
  | "status-pill"
  | "runtime-banner"

export type CalloutSlot = "header" | "footer" | "overlay"

export interface CalloutConfig {
  style: CalloutStylePreset
  text?: string
  icon?: string      // Lucide icon name (e.g., "eye", "alert-triangle")
  visible?: boolean  // Defaults to true
}

export type CalloutSlotMap = Partial<Record<CalloutSlot, CalloutConfig>>
```

```typescript
// calloutStylePresets.ts - Tailwind class definitions
export const CALLOUT_STYLE_PRESETS: Record<CalloutStylePreset, string> = {
  frosted: "bg-white/10 backdrop-blur-md border border-white/20 rounded-lg text-white/90 shadow-sm",
  "neon-frame": "bg-slate-900/80 border-2 border-cyan-400/60 rounded-md text-cyan-100 shadow-[0_0_15px_rgba(34,211,238,0.25)]",
  "glass-pill": "bg-white/5 backdrop-blur-sm border border-white/10 rounded-full text-white/80 text-xs",
  "framed-note": "bg-slate-800/60 border-l-4 border-amber-400/70 rounded-r-md text-slate-200",
  "status-pill": "bg-emerald-500/20 border border-emerald-400/30 rounded-full text-emerald-300 text-xs font-medium",
  "runtime-banner": "bg-gradient-to-r from-purple-500/20 via-fuchsia-500/20 to-pink-500/20 border-y border-white/10 text-white/90",
}
```

```tsx
// CalloutBanner.tsx - Main rendering component
export function CalloutBanner({ config, className, customStyle }: CalloutBannerProps) {
  if (config.visible === false) return null
  const IconComponent = getLucideIcon(config.icon)
  const presetClasses = getCalloutPresetClasses(config.style)
  return (
    <div className={cn("flex items-center gap-2", presetClasses, className)} style={customStyle}>
      {IconComponent && <IconComponent className="h-4 w-4" aria-hidden />}
      {config.text && <span className="truncate">{config.text}</span>}
    </div>
  )
}
```

#### 2. Capability Pack (`demoBuilderCapabilityRegistry.ts`)

Added `presentation.callouts.v1` pack that extends all panel and block capabilities with callout field specs:

```typescript
export const CALLOUT_STYLE_PRESETS = [
  "frosted", "neon-frame", "glass-pill",
  "framed-note", "status-pill", "runtime-banner",
] as const

// Presentation field specs for header/footer callouts
const CALLOUT_PRESENTATION_FIELD_SPECS: BuilderPresentationFieldSpec[] = [
  { path: "callouts.header.style", label: "Header Callout Style", control: "enum", enumValues: CALLOUT_STYLE_PRESETS },
  { path: "callouts.header.text", label: "Header Callout Text", control: "text" },
  { path: "callouts.header.icon", label: "Header Callout Icon", control: "text" },
  { path: "callouts.footer.style", label: "Footer Callout Style", control: "enum", enumValues: CALLOUT_STYLE_PRESETS },
  { path: "callouts.footer.text", label: "Footer Callout Text", control: "text" },
  { path: "callouts.footer.icon", label: "Footer Callout Icon", control: "text" },
]
```

To enable: Add `presentation.callouts.v1` to `VITE_DEMO_BUILDER_PACKS` env variable.

#### 3. Presentation Resolver (`demoPresentationResolver.ts`)

Added `resolveCalloutConfigs()` function that:
- Reads `callouts.header` and `callouts.footer` from presentation_json
- Validates each config with `isValidCalloutConfig()` type guard
- Returns a `CalloutSlotMap` for rendering

#### 4. Frame Rendering (`DemoPresentationFrame.tsx`)

Extended component to render callouts at header/footer slots:

```tsx
{shouldRenderCallout(frame.callouts?.header) && (
  <CalloutBanner config={frame.callouts.header} className="mb-2" />
)}
<div className={cn("relative z-20", contentClassName)}>{children}</div>
{shouldRenderCallout(frame.callouts?.footer) && (
  <CalloutBanner config={frame.callouts.footer} className="mt-2" />
)}
```

### Usage

```json
{
  "presentation_json": {
    "callouts": {
      "header": {
        "style": "frosted",
        "text": "Preview Mode",
        "icon": "eye"
      },
      "footer": {
        "style": "neon-frame",
        "text": "Runtime Active",
        "icon": "zap"
      }
    }
  }
}
```

**Complexity:** Medium
**Impact:** High - enables rich visual callouts with style presets and icon support

---

## Priority 4: SVG Overlay System ✅ IMPLEMENTED

**Problem:** `backgrounds.svg_overlay: "grid-wave-v1"` is a string hint with no asset loader.

**Solution Implemented:** Data URI-based SVG registry with presentation resolver integration

### Implementation Details (2026-02-25)

The SVG overlay system follows the established architecture: registry provides lookup, resolver consumes it.

#### 1. SVG Overlay Registry (`svgOverlayRegistry.ts`)

Created a new registry file with:
- SVG patterns stored as inline data URIs for zero-latency loading
- Patterns use `currentColor` for theme adaptation
- Three initial presets: `grid-wave-v1`, `rings-grid-v2`, `constellation-dots-v1`

```typescript
export const SVG_OVERLAY_PRESETS = [
  "grid-wave-v1",
  "rings-grid-v2",
  "constellation-dots-v1",
] as const

export function getSvgOverlayUrl(preset: string): string | undefined {
  return SVG_OVERLAY_REGISTRY[preset as SvgOverlayPreset]
}
```

#### 2. Presentation Resolver (`demoPresentationResolver.ts`)

Updated `resolveEffectStyle()` to layer SVG overlays:

```typescript
const svgOverlayPreset = getNestedString(presentationJson, "backgrounds", "svg_overlay")
const svgOverlayUrl = svgOverlayPreset ? getSvgOverlayUrl(svgOverlayPreset) : undefined

if (pageGradientCss || svgOverlayUrl || cardPatternCss) {
  const layers: string[] = []
  if (pageGradientCss) layers.push(pageGradientCss)
  if (svgOverlayUrl) layers.push(svgOverlayUrl)
  if (cardPatternCss) layers.push(cardPatternCss)
  style.backgroundImage = layers.join(", ")
}
```

Layer order: page_gradient (top) → svg_overlay (middle) → card_pattern (bottom)

#### 3. Capability Pack (`demoBuilderCapabilityRegistry.ts`)

Added `presentation.svg-overlays.v1` pack:

```typescript
{
  id: "presentation.svg-overlays.v1",
  description: "SVG overlay background patterns for composition-level styling.",
  createPack: () => buildSvgOverlaysPack(),
}
```

To enable: Add `presentation.svg-overlays.v1` to `VITE_DEMO_BUILDER_PACKS` env variable.

### Usage

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

**Complexity:** Low-Medium
**Impact:** Medium - enables branded pattern overlays with theme adaptation

---

## Priority 5: Theme Integration Improvements

**Problem:** Templates use `theme_id: null` everywhere because creating themes is cumbersome.

**Solution:**

1. **Seed Default Themes:** Add demo-specific themes to backend seed data:
   - `demo-aurora-page` (page theme with gradient)
   - `demo-glass-cards` (cards theme with frosted effect)
   - `demo-neon-panels` (high-contrast accent theme)

2. **Theme Picker in Builder:** Add a dropdown that lists available themes from the API.

3. **Inline Theme Preview:** Show color swatches when hovering over theme options.

**Complexity:** Medium
**Impact:** High - makes theming accessible

---

## Implementation Order

| Phase | Task | Effort | Impact | Status |
|-------|------|--------|--------|--------|
| 1 | Font CSS variables + consumption | 2h | High | ✅ Complete |
| 2 | Density tokens in blocks | 2h | Medium | ✅ Complete |
| 3 | Callout component + integration | 3h | High | ✅ Complete |
| 4 | SVG overlay registry | 2h | Medium | ✅ Complete |
| 5 | Seed demo themes + builder picker | 4h | High | Pending |

---

## Testing Checklist

After each implementation:

1. Verify in `Composition F: Passthrough Audit` template
2. Confirm resolver output matches expected CSS
3. Test cascade: composition → panel → block precedence
4. Visual regression check in demo preview

---

## Files Modified (Font System)

| File | Changes |
|------|---------|
| `demoBuilderCapabilityRegistry.ts` | Added `typography.fonts.v1` pack with font presets |
| `demoPresentationResolver.ts` | Added `resolveFontStyle()`, updated frame resolution |
| `DemoPresentationFrame.tsx` | Added `useFontLoader()` hook for Google Fonts |
| `demo-themes.css` | Added CSS rules for `--font-heading`, `--font-body` consumption |

## Files Modified (Callout System)

| File | Changes |
|------|---------|
| `Page/primitives/Callout/types.ts` | Core type definitions (CalloutStylePreset, CalloutConfig, etc.) |
| `Page/primitives/Callout/calloutStylePresets.ts` | Tailwind class definitions for six style presets |
| `Page/primitives/Callout/CalloutBanner.tsx` | Main component with Lucide icon support |
| `Page/primitives/Callout/index.ts` | Public exports |
| `Page/primitives/index.ts` | Added Callout exports to barrel file |
| `demoBuilderCapabilityRegistry.ts` | Added `presentation.callouts.v1` pack with callout field specs |
| `demoPresentationResolver.ts` | Added `resolveCalloutConfigs()` and `isValidCalloutConfig()` |
| `DemoPresentationFrame.tsx` | Added callout rendering at header/footer slots |

## Files Modified (Density Tokens)

| File | Changes |
|------|---------|
| `rendererRegistry.tsx` | Added `parseOrchestratorStatePresentation()`, `parseToolCapabilityPresentation()`, updated `parseContributionFeedPresentation()` |
| `blocks/ContributionFeedBlock.tsx` | Added `feedDensity` prop, `FEED_DENSITY_CLASSES` mapping |
| `blocks/OrchestratorStateBlock.tsx` | Added `stackDensity` prop, `STACK_DENSITY_CLASSES` mapping |
| `blocks/ToolCapabilityBlock.tsx` | Added `matrixDensity` prop, `MATRIX_DENSITY_CLASSES` mapping |

## Files Modified (SVG Overlays)

| File | Changes |
|------|---------|
| `svgOverlayRegistry.ts` | NEW: SVG patterns as data URIs, `getSvgOverlayUrl()` lookup function |
| `demoPresentationResolver.ts` | Import registry, update `resolveEffectStyle()` to layer svg_overlay |
| `demoBuilderCapabilityRegistry.ts` | Added `presentation.svg-overlays.v1` pack with composition capability |

## Files to Modify (Remaining Phases)

| File | Changes |
|------|---------|
| `DemoChatPanel.tsx` | Consume density tokens |
| `ContributionFeedBlock.tsx` | Consume density + highlight tokens |
| `demoBuilderSchema.ts` | Update template field specs |
| `backend/app/alembic/seed_themes_full.sql` | Add demo themes |
