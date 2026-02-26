# Callout System Reference Card

> Dual-purpose guide for engineers (integration/extension) and demo builders (usage)
> Last Updated: 2026-02-25

---

## Quick Start (Demo Builder)

Add callouts to any composition, panel, or block via `presentation_json`:

- Runtime support: composition, panel, and block callouts are resolved and rendered.
- Guided editor support (with `presentation.callouts.v1` enabled):
  - composition: `style` + `text`
  - panel/block: `style` + `text` + `icon`
- `visible` is currently JSON-only (raw `presentation_json`).

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

### Available Style Presets

| Style | Visual Description | Best For |
|-------|-------------------|----------|
| `frosted` | Glassmorphism with blur, white borders | Dark backgrounds, subtle notices |
| `neon-frame` | Glowing cyan border, cyber aesthetic | Tech/futuristic demos |
| `glass-pill` | Compact frosted pill shape | Small status indicators |
| `framed-note` | Card with amber left accent | Important notes, warnings |
| `status-pill` | Minimal emerald badge | Success states, active indicators |
| `runtime-banner` | Full-width gradient banner | Runtime status, system messages |

### Available Icon Names

Any [Lucide icon](https://lucide.dev/icons/) works. Common choices:

| Icon | Use Case |
|------|----------|
| `eye` | Preview mode, visibility |
| `info` | Information, help |
| `alert-triangle` | Warnings |
| `check-circle` | Success, completion |
| `clock` | Timing, scheduling |
| `zap` | Power, runtime |
| `sparkles` | New features, magic |
| `lightbulb` | Ideas, tips |
| `bell` | Notifications |
| `message-circle` | Chat, communication |

### Callout Slots

| Slot | Position | Notes |
|------|----------|-------|
| `header` | Before content | Good for mode indicators, preview notices |
| `footer` | After content | Good for status, runtime info |
| `overlay` | Reserved | Not yet implemented |

### Visibility Control

Hide a callout without removing config:

```json
{
  "callouts": {
    "header": {
      "style": "frosted",
      "text": "Hidden callout",
      "visible": false
    }
  }
}
```

---

## Architecture Overview (Engineer)

```
┌─────────────────────────────────────────────────────────────────┐
│                     presentation_json                            │
│  { "callouts": { "header": { style, text, icon } } }            │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              demoPresentationResolver.ts                         │
│  resolveCalloutConfigs() → validates → CalloutSlotMap           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│              DemoPresentationFrame.tsx                           │
│  Reads frame.callouts → renders CalloutBanner at slots          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│          Page/primitives/Callout/CalloutBanner.tsx              │
│  Applies preset classes → renders icon + text                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Files

| File | Purpose |
|------|---------|
| `Page/primitives/Callout/types.ts` | Type definitions |
| `Page/primitives/Callout/calloutStylePresets.ts` | Tailwind class mappings |
| `Page/primitives/Callout/CalloutBanner.tsx` | Rendering component |
| `Demo/demoPresentationResolver.ts` | Config validation & resolution |
| `Demo/DemoPresentationFrame.tsx` | Slot rendering integration |
| `Demo/builder/demoBuilderCapabilityRegistry.ts` | Capability pack registration |

---

## Extending the System (Engineer)

### Adding a New Style Preset

1. **Define the style in `calloutStylePresets.ts`:**

```typescript
// In CALLOUT_STYLE_PRESETS
export const CALLOUT_STYLE_PRESETS: Record<CalloutStylePreset, string> = {
  // ... existing styles
  "my-new-style": "bg-indigo-500/20 border border-indigo-400/50 rounded-lg text-indigo-100",
}
```

2. **Add to type union in `types.ts`:**

```typescript
export type CalloutStylePreset =
  | "frosted"
  | "neon-frame"
  // ... existing styles
  | "my-new-style"  // Add here
```

3. **Update capability registry validation in `demoBuilderCapabilityRegistry.ts`:**

```typescript
export const CALLOUT_STYLE_PRESETS = [
  // ... existing styles
  "my-new-style",  // Add here
] as const
```

4. **Update resolver validation in `demoPresentationResolver.ts`:**

```typescript
const VALID_CALLOUT_STYLES = new Set([
  // ... existing styles
  "my-new-style",  // Add here
])
```

### Adding a New Slot

1. **Add to type union in `types.ts`:**

```typescript
export type CalloutSlot =
  | "header"
  | "footer"
  | "overlay"
  | "sidebar"  // New slot
```

2. **Update resolver validation:**

```typescript
const VALID_CALLOUT_SLOTS = new Set(["header", "footer", "overlay", "sidebar"])
```

3. **Add rendering in `DemoPresentationFrame.tsx`:**

```tsx
{shouldRenderCallout(frame.callouts?.sidebar) && (
  <CalloutBanner
    config={frame.callouts.sidebar}
    className="absolute right-0 top-1/2 -translate-y-1/2"
  />
)}
```

### Creating a Custom Capability Pack

To extend or override callout behavior for specific use cases:

```typescript
// In demoBuilderCapabilityRegistry.ts

function buildCustomCalloutsPack(): BuilderCapabilityRegistryPack {
  return {
    id: "custom.callouts.v1",
    order: 220,  // After presentation.callouts.v1 (210)

    // Override panel capabilities with custom callout fields
    panelCapabilities: ACTIVE_BUILDER_PANEL_KINDS.map((kind) => ({
      kind,
      displayName: `${kind} (Custom Callouts)`,
      requirements: getPanelRequirements(kind),
      presentationFieldSpecs: [
        // Custom callout fields
        {
          path: "callouts.sidebar.style",
          label: "Sidebar Callout",
          control: "enum",
          enumValues: ["frosted", "neon-frame"],  // Limited options
        },
      ],
    })),
  }
}

// Register in getBuiltinBuilderCapabilityPackRegistrations()
{
  id: "custom.callouts.v1",
  description: "Custom callout configuration for specialized panels.",
  createPack: () => buildCustomCalloutsPack(),
},
```

### Enabling Capability Packs

Via environment variable:

```bash
# .env
VITE_DEMO_BUILDER_PACKS=typography.fonts.v1,presentation.callouts.v1
```

Via code:

```typescript
const registry = buildCapabilityRegistry({
  packs: [
    buildTypographyFontsPack(),
    buildCalloutsPack(),
    buildCustomCalloutsPack(),
  ],
})
```

---

## Demo Builder Workflow

### Step-by-Step: Adding Callouts to a Panel

1. **Open the Demo Builder** at `/demo-builder`

2. **Select or create a composition**

3. **Navigate to a panel** you want to add callouts to

4. **Find the presentation_json editor** (if capability pack is enabled)

5. **Add callout configuration:**
   - Select a style preset from the dropdown
   - Enter display text
   - Optionally add an icon name (panel/block guided fields; composition via raw JSON)

6. **Preview** - callouts render immediately on save

### Best Practices for Demo Builders

| Do | Don't |
|----|-------|
| Use callouts sparingly for emphasis | Overload with multiple callouts |
| Match style to theme (frosted for dark) | Mix incompatible visual styles |
| Keep text concise (2-5 words) | Write paragraphs in callouts |
| Use icons that reinforce meaning | Use random decorative icons |
| Test visibility on different viewports | Assume desktop-only viewing |

### Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Callout not appearing | Invalid style name | Check spelling matches preset |
| Icon not showing | Invalid icon name | Use kebab-case (e.g., `alert-triangle`) |
| Callout invisible | `visible: false` | Remove or set to `true` |
| Style looks wrong | Theme mismatch | Try different preset for your background |
| Pack fields not in editor | Pack not enabled | Add to `VITE_DEMO_BUILDER_PACKS` |
| Composition icon field missing in guided editor | Composition capability exposes style/text only | Set `presentation_json.callouts.*.icon` in raw JSON |

---

## Type Reference

```typescript
// Core types from Page/primitives/Callout/types.ts

export type CalloutStylePreset =
  | "frosted"
  | "neon-frame"
  | "glass-pill"
  | "framed-note"
  | "status-pill"
  | "runtime-banner"

export type CalloutSlot = "header" | "footer" | "overlay"

export interface CalloutConfig {
  /** Visual style preset - required */
  style: CalloutStylePreset
  /** Display text - optional */
  text?: string
  /** Lucide icon name (e.g., "eye", "alert-triangle") - optional */
  icon?: string
  /** Visibility toggle, defaults to true - optional */
  visible?: boolean
}

export type CalloutSlotMap = Partial<Record<CalloutSlot, CalloutConfig>>

export interface CalloutBannerProps {
  /** Callout configuration */
  config: CalloutConfig
  /** Additional CSS classes */
  className?: string
  /** Inline style overrides */
  customStyle?: React.CSSProperties
}
```

---

## Related Documentation

- [Presentation Customization Roadmap](./presentation-customization-roadmap.md) - Overall presentation system status
- [Demo Builder Workflow](./demo-builder-workflow.md) - General builder usage
- [Theme Cascade Reference](../../Agents/docs/THEME-CASCADE-REFERENCE.md) - How styles cascade
- [Page Primitives Index](../../Page/primitives/index.ts) - All available primitives

---

## Changelog

### 2026-02-25: Initial Implementation

- Added `Page/primitives/Callout/` module with types, presets, and component
- Added `presentation.callouts.v1` capability pack
- Extended `demoPresentationResolver.ts` with callout validation
- Extended `DemoPresentationFrame.tsx` with slot rendering
- Six style presets: frosted, neon-frame, glass-pill, framed-note, status-pill, runtime-banner
- Two slots: header, footer (overlay reserved for future)
- Lucide icon support via dynamic lookup
