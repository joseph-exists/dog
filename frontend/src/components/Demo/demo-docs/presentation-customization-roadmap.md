# Demo Presentation Customization Roadmap

> Status: Working Draft
> Last Updated: 2026-02-24
> Context: Templates D-G cleaned up to use only implemented fields

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
| **Font Families** | `typography.heading_font`, `typography.body_font` | Resolver doesn't apply; no font loader |
| **SVG Overlays** | `backgrounds.svg_overlay` | String hint only; no asset loader |
| **Callouts** | `callouts.*` | Pass-through only; requires capability-aware rendering |
| **Density Tokens** | `feed_density`, `stack_density`, `matrix_density` | Capability-specific; renderers must consume |
| **Style Hints** | `status_badge_style`, `surface_radius` | Capability-specific; renderers must consume |

---

## Priority 1: Font Loading System

**Problem:** `typography.heading_font` and `typography.body_font` are specified but never applied.

**Solution Options:**

### Option A: CSS Variable Font Stack (Recommended)

1. Add to `demoPresentationResolver.ts`:
```typescript
function resolveTypographyStyle(presentationJson: unknown): React.CSSProperties {
  const style: React.CSSProperties = {}
  // existing size/line_height logic...

  const headingFont = getNestedString(presentationJson, "typography", "heading_font")
  const bodyFont = getNestedString(presentationJson, "typography", "body_font")

  if (headingFont) {
    style["--font-heading" as string] = `"${headingFont}", var(--font-sans)`
  }
  if (bodyFont) {
    style["--font-body" as string] = `"${bodyFont}", var(--font-sans)`
  }
  return style
}
```

2. Update Tailwind/CSS to use variables:
```css
.demo-shell h1, .demo-shell h2, .demo-shell h3 {
  font-family: var(--font-heading, var(--font-sans));
}
.demo-shell p, .demo-shell span {
  font-family: var(--font-body, var(--font-sans));
}
```

3. **Font Loading:** Require fonts to be pre-loaded via:
   - Global CSS `@import` for Google Fonts
   - Or use only system fonts / already-loaded fonts

**Complexity:** Low
**Impact:** High - enables authored font customization

### Option B: Dynamic Font Loader

Create a React hook that dynamically loads Google Fonts based on presentation_json.

**Complexity:** Medium
**Impact:** High - enables any Google Font

---

## Priority 2: Capability-Aware Token Consumption

**Problem:** Tokens like `feed_density: "compact"` are passed through but not consumed by renderers.

**Solution:**

1. Define a capability token interface:
```typescript
interface CapabilityPresentationTokens {
  feed_density?: "compact" | "comfortable" | "spacious"
  stack_density?: "compact" | "comfortable" | "spacious"
  matrix_density?: "compact" | "standard"
  status_badge_style?: "default" | "high-contrast" | "minimal"
}
```

2. Update `DemoChatPanel.tsx`, `ContributionFeedBlock.tsx`, etc. to read tokens:
```typescript
const feedDensity = presentation_json?.tokens?.feed_density ?? "comfortable"
const densityClasses = {
  compact: "gap-1 py-1 text-sm",
  comfortable: "gap-2 py-2",
  spacious: "gap-4 py-3 text-base",
}
```

**Complexity:** Medium (per-capability implementation)
**Impact:** Medium - enables fine-grained layout control

---

## Priority 3: Callout System

**Problem:** `callouts.*` is documented but not rendered.

**Solution:**

1. Define callout types and styles:
```typescript
type CalloutStyle =
  | "frosted"
  | "neon-frame"
  | "glass-pill"
  | "framed-note"
  | "alert-inline"
  | "status-pill"
  | "runtime-banner"

interface CalloutConfig {
  style: CalloutStyle
  text?: string
  icon?: string
}
```

2. Create a `CalloutBanner` component:
```tsx
function CalloutBanner({ config }: { config: CalloutConfig }) {
  const styleClasses = {
    frosted: "bg-white/10 backdrop-blur-md border border-white/20 rounded-lg",
    "neon-frame": "border-2 border-cyan-400/50 shadow-[0_0_15px_rgba(34,211,238,0.3)]",
    // ...
  }
  return (
    <div className={styleClasses[config.style]}>
      {config.icon && <Icon name={config.icon} />}
      {config.text}
    </div>
  )
}
```

3. Integrate into block/panel renderers.

**Complexity:** Medium
**Impact:** High - enables rich visual callouts

---

## Priority 4: SVG Overlay System

**Problem:** `backgrounds.svg_overlay: "grid-wave-v1"` is a string hint with no asset loader.

**Solution:**

1. Create an SVG asset registry:
```typescript
const SVG_OVERLAYS: Record<string, string> = {
  "grid-wave-v1": `url("data:image/svg+xml,${encodeURIComponent(gridWaveSvg)}")`,
  "rings-grid-v2": `url("data:image/svg+xml,${encodeURIComponent(ringsGridSvg)}")`,
  "qa-constellation-grid-v1": `url("data:image/svg+xml,${encodeURIComponent(constellationSvg)}")`,
}
```

2. Update `resolveEffectStyle`:
```typescript
const svgOverlay = getNestedString(presentationJson, "backgrounds", "svg_overlay")
if (svgOverlay && SVG_OVERLAYS[svgOverlay]) {
  layers.push(SVG_OVERLAYS[svgOverlay])
}
```

**Complexity:** Low-Medium (depends on SVG asset creation)
**Impact:** Medium - enables branded pattern overlays

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

| Phase | Task | Effort | Impact |
|-------|------|--------|--------|
| 1 | Font CSS variables + consumption | 2h | High |
| 2 | Seed demo themes + builder picker | 4h | High |
| 3 | SVG overlay registry | 2h | Medium |
| 4 | Density tokens in chat/feed | 3h | Medium |
| 5 | Callout component + integration | 4h | High |

---

## Testing Checklist

After each implementation:

1. Verify in `Composition F: Passthrough Audit` template
2. Confirm resolver output matches expected CSS
3. Test cascade: composition → panel → block precedence
4. Visual regression check in demo preview

---

## Files to Modify

| File | Changes |
|------|---------|
| `demoPresentationResolver.ts` | Add font variables, SVG lookup |
| `DemoChatPanel.tsx` | Consume density tokens |
| `ContributionFeedBlock.tsx` | Consume density + highlight tokens |
| `DemoShell.tsx` | Apply font CSS classes |
| `demoBuilderSchema.ts` | Update template field specs |
| `backend/app/alembic/seed_themes_full.sql` | Add demo themes |
