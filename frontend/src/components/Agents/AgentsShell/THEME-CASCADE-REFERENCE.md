# Theme Cascade Reference Card

> **Audience:** Junior engineers migrating other Page components to the theme cascade system
> **Location:** `frontend/src/components/Agents/AgentsShell/`
> **Last Updated:** 2026-02-11

---

## Overview

This document explains how to implement the 4-layer theme cascade system used on the Agents page. The system allows themes to be applied at multiple levels, with downstream themes overriding upstream ones.

```
Application Theme → Page Theme → Cards Theme → Individual Card Theme
      (A)              (B)           (C)              (D)
```

Each layer can override the previous. The closest theme to a component wins.

---

## Core Principle: Transparent Scopes

**Theme wrappers are transparent.** They set CSS variables but do NOT render surfaces.

```tsx
// CORRECT: Transparent wrapper, only sets variables
<div style={getThemeStyle(theme)} className="flex-1">
  <ChildComponent />  // Child renders with inherited variables
</div>

// WRONG: Wrapper renders its own surface
<div style={getThemeStyle(theme)} className="flex-1 bg-card">
  <ChildComponent />
</div>
```

**Why?** If wrappers render surfaces, you get layered backgrounds that conflict visually. Instead, let leaf components (Header, PanelContainer, Cards) render their own surfaces using inherited CSS variables.

---

## The 4-Layer Cascade

### Layer A: Application Theme

- **Source:** `src/index.css` (`:root` and `.dark` selectors)
- **Scope:** Entire application
- **Variables:** All CSS custom properties (`--background`, `--card`, `--foreground`, etc.)
- **You don't touch this.** It's the base layer everything inherits from.

### Layer B: Page Theme

- **Source:** Theme selector in page header
- **Scope:** Entire page content (header + content area)
- **Applied via:** Wrapper div with `style={getThemeStyle(pageTheme)}`
- **Wrapper is transparent:** No `bg-*` class on the wrapper itself
- **Components inside:** Header uses `bg-background text-foreground` to render with page theme

```tsx
// Page theme wrapper (transparent scope)
<div style={getThemeStyle(pageTheme)} className="flex flex-col h-full">
  <PageHeader />  {/* Has bg-background, renders with page theme */}
  <CardsWrapper />
</div>
```

### Layer C: Cards/Ambient Theme

- **Source:** Theme selector in page header (separate from page theme)
- **Scope:** Content area below header
- **Applied via:** Nested wrapper div with `style={getThemeStyle(cardsTheme)}`
- **Wrapper is transparent:** No `bg-*` class on the wrapper itself
- **Components inside:** PanelContainer uses `bg-background` to render with cards theme

```tsx
// Cards theme wrapper (transparent scope, nested inside page wrapper)
<div style={getThemeStyle(cardsTheme)} className="flex-1 min-h-0">
  <Layout />  {/* Contains PanelContainer which has bg-background */}
</div>
```

### Layer D: Individual Card Theme

- **Source:** `presentation` field on the entity (stored in database)
- **Scope:** Single card/component instance
- **Applied via:** Wrapper div directly around the Card component
- **This is the "presentation-as-data" pattern**

```tsx
// Card presentation wrapper (closest to component, always wins)
<div style={presentationToStyle(resolved.tokens)}>
  <Card>...</Card>
</div>
```

---

## CSS Variable Inheritance

CSS custom properties cascade via inheritance. When multiple ancestors set the same variable, the **nearest ancestor wins**.

```
Page wrapper sets:    --background: midnight-blue
  └── Header reads:   --background → gets midnight-blue ✓
  └── Cards wrapper sets: --background: warm-sand
        └── PanelContainer reads: --background → gets warm-sand ✓
        └── Card wrapper sets: --background: neon-pink
              └── Card reads: --background → gets neon-pink ✓
```

**Key insight:** The wrapper that sets a variable doesn't need to consume it. It just scopes the variable for descendants.

---

## Required CSS Variables

Each theme MUST define the complete variable surface. Partial themes cause invisible text.

```typescript
interface ThemeTokens {
  // Page surface (containers use bg-background)
  "--background": string

  // Card surface (Card component uses bg-card)
  "--card": string
  "--card-foreground": string

  // Text colors
  "--foreground": string
  "--muted-foreground": string
  "--secondary-foreground": string
  "--accent-foreground": string

  // Background variants
  "--muted": string
  "--secondary": string
  "--accent": string

  // Borders
  "--border": string
}
```

**The "default" theme is empty** — it defers entirely to the Application theme (`:root`).

---

## File Structure for Theme Cascade

```
src/components/YourFeature/
├── YourShell/
│   ├── index.ts              # Barrel exports
│   ├── themes.ts             # Theme definitions + getThemeStyle()
│   ├── YourShell.tsx         # Outer container with theme wrappers
│   ├── YourHeader.tsx        # Header with theme selectors + bg-background
│   ├── YourLayout.tsx        # Panel arrangement (no bg-* classes)
│   └── panels/
│       └── YourGridPanel.tsx # Panel using PanelContainer
```

---

## Step-by-Step Migration Guide

### Step 1: Create themes.ts

```typescript
import type { PresentationTokens } from "../types"
import { presentationToStyle } from "../resolve"

export interface AmbientTheme {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens
}

export function getThemeStyle(theme: AmbientTheme): React.CSSProperties | undefined {
  return presentationToStyle(theme.tokens)
}

export const AMBIENT_THEMES: AmbientTheme[] = [
  {
    id: "default",
    name: "Default",
    description: "Application theme",
    tokens: {},  // Empty = inherit from :root
  },
  {
    id: "your-theme",
    name: "Your Theme",
    tokens: {
      "--background": "oklch(...)",
      "--card": "oklch(...)",
      "--card-foreground": "oklch(...)",
      "--foreground": "oklch(...)",
      "--border": "oklch(...)",
      "--muted": "oklch(...)",
      "--muted-foreground": "oklch(...)",
      "--secondary": "oklch(...)",
      "--secondary-foreground": "oklch(...)",
      "--accent": "oklch(...)",
      "--accent-foreground": "oklch(...)",
    },
  },
]

export function getThemeById(id: string): AmbientTheme {
  return AMBIENT_THEMES.find((t) => t.id === id) ?? AMBIENT_THEMES[0]
}
```

### Step 2: Create the Shell Component

```tsx
import { getThemeById, getThemeStyle } from "./themes"
import { YourHeader } from "./YourHeader"
import { YourLayout } from "./YourLayout"

interface YourShellProps {
  pageThemeId: string
  cardsThemeId: string
  onPageThemeChange: (id: string) => void
  onCardsThemeChange: (id: string) => void
  // ... other props
}

export function YourShell({
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
}: YourShellProps) {
  const pageTheme = getThemeById(pageThemeId)
  const cardsTheme = getThemeById(cardsThemeId)

  return (
    // Page theme wrapper — TRANSPARENT (no bg-* class)
    <div style={getThemeStyle(pageTheme)} className="flex flex-col h-full">

      <YourHeader
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
      />

      {/* Cards theme wrapper — TRANSPARENT (no bg-* class) */}
      <div style={getThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        <YourLayout />
      </div>
    </div>
  )
}
```

### Step 3: Create the Header Component

```tsx
import { AMBIENT_THEMES, getThemeById } from "./themes"

interface YourHeaderProps {
  pageThemeId: string
  cardsThemeId: string
  onPageThemeChange: (id: string) => void
  onCardsThemeChange: (id: string) => void
}

export function YourHeader({
  pageThemeId,
  cardsThemeId,
  onPageThemeChange,
  onCardsThemeChange,
}: YourHeaderProps) {
  const pageTheme = getThemeById(pageThemeId)
  const cardsTheme = getThemeById(cardsThemeId)

  return (
    // Header renders with page theme via bg-background
    <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0 bg-background text-foreground">

      <h1>Your Page Title</h1>

      <div className="flex items-center gap-3">
        {/* Page theme selector */}
        <Select value={pageThemeId} onValueChange={onPageThemeChange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue>Page: {pageTheme.name}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {AMBIENT_THEMES.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                {theme.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Cards theme selector */}
        <Select value={cardsThemeId} onValueChange={onCardsThemeChange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue>Cards: {cardsTheme.name}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {AMBIENT_THEMES.map((theme) => (
              <SelectItem key={theme.id} value={theme.id}>
                {theme.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
```

### Step 4: Update the Route

```tsx
function YourPage() {
  // Future: useUserPagePrefs("your-page") will provide saved preferences
  const savedPrefs = null as { pageTheme?: string; cardsTheme?: string } | null

  const [pageThemeId, setPageThemeId] = useState(
    savedPrefs?.pageTheme ?? "default"
  )
  const [cardsThemeId, setCardsThemeId] = useState(
    savedPrefs?.cardsTheme ?? "default"
  )

  return (
    <YourShell
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={setPageThemeId}
      onCardsThemeChange={setCardsThemeId}
    />
  )
}
```

---

## Common Mistakes

### Mistake 1: Adding bg-* to theme wrappers

```tsx
// WRONG
<div style={getThemeStyle(theme)} className="bg-card">

// CORRECT
<div style={getThemeStyle(theme)}>
```

Theme wrappers should be transparent. Let downstream components render surfaces.

### Mistake 2: Forgetting --background in themes

```typescript
// WRONG — PanelContainer uses bg-background, will fall through to :root
tokens: {
  "--card": "...",
  "--foreground": "...",
}

// CORRECT — includes --background
tokens: {
  "--background": "...",
  "--card": "...",
  "--foreground": "...",
}
```

### Mistake 3: Missing bg-background on Header

```tsx
// WRONG — header is transparent, doesn't show page theme
<div className="border-b border-border">

// CORRECT — header renders with inherited --background
<div className="border-b border-border bg-background text-foreground">
```

### Mistake 4: Partial theme variable sets

If you change surface lightness (light ↔ dark), you MUST override ALL variables. Otherwise you get invisible text (dark text on dark background, or vice versa).

### Mistake 5: Wrapping wrong components

```tsx
// WRONG — theme wrapper inside the layout
<Layout>
  <div style={getThemeStyle(theme)}>
    <Panel />
  </div>
</Layout>

// CORRECT — theme wrapper outside the layout
<div style={getThemeStyle(theme)}>
  <Layout>
    <Panel />
  </Layout>
</div>
```

---

## Debugging Theme Issues

### In DevTools:

1. **Inspect the element** that's not showing the right theme
2. **Check Computed Styles** → look at the CSS variable values
3. **Trace up the DOM** to find which ancestor set each variable
4. **Verify the variable exists** in the theme definition

### Common symptoms:

| Symptom | Likely Cause |
|---------|--------------|
| Component ignores theme | Missing `bg-*` or `text-*` class that reads the variable |
| Component uses app theme | Variable not set by theme wrapper (falls through to `:root`) |
| Invisible text | Theme changes lightness but doesn't include foreground variables |
| Layered backgrounds | Theme wrapper has `bg-*` class (should be transparent) |

---

## Design Principles

1. **Presentation is data, not style.** Themes are data objects that will migrate to database.

2. **Components are unmodified.** Shadcn Card, Badge, etc. are used as-is. CSS variables are the only injection point.

3. **Specificity is the composition model.** Nested wrappers override outer ones via CSS inheritance. No `!important`, no hacks.

4. **Partial override is the default.** Themes only specify what they change. Unspecified variables fall through to outer layers.

5. **Wrappers are transparent scopes.** They set variables, they don't render surfaces.

6. **Leaf components render surfaces.** Header, PanelContainer, Card — these have `bg-*` classes.

---

## Related Files

| File | Purpose |
|------|---------|
| `src/components/Agents/types.ts` | `PresentationTokens` interface |
| `src/components/Agents/resolve.ts` | `presentationToStyle()` function |
| `src/components/Agents/Presentation/REFERENCE.md` | Full architecture guide |
| `src/index.css` | Application theme (`:root` variables) |
| `src/components/Page/primitives/PanelContainer.tsx` | Standard panel container (uses `bg-background`) |

---

## Questions?

If this document doesn't answer your question, check:
1. `Presentation/REFERENCE.md` for the full architecture
2. `AgentsShell/IMPLEMENTATION-PLAN.md` for historical context
3. The working implementation in `AgentsShell/*.tsx`
