# Cascading Theme System Reference

This document describes how themes cascade through the application, from page-level settings down to individual cards.

## Overview

The theme system uses **CSS custom properties (variables)** that cascade through the DOM. Each layer can override variables from the layer above, creating a clean inheritance chain without specificity battles.

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 1: Application (:root)                                   │
│  ─────────────────────────────────────────────────────────────  │
│  Base CSS variables defined in globals.css                      │
│  --background, --foreground, --card, --primary, etc.            │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Page Theme                                            │
│  ─────────────────────────────────────────────────────────────  │
│  Outer wrapper div with getPageThemeStyle()                     │
│  Controls page surface: --background, --foreground              │
│  Affects header and all content                                 │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Cards Theme                                           │
│  ─────────────────────────────────────────────────────────────  │
│  Inner wrapper div with getCardThemeStyle()                     │
│  Controls card surfaces: --card, --card-foreground, --border    │
│  Does NOT set --background (preserves page theme)               │
├─────────────────────────────────────────────────────────────────┤
│  Layer 4: Instance Presentation                                 │
│  ─────────────────────────────────────────────────────────────  │
│  Individual card wrapper with presentationToStyle()             │
│  Per-entity overrides: --story-accent, decorationHint, avatar   │
│  Data stored with entity, rendered on load                      │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### Shell Components

The Shell is the top-level container that sets up theme wrappers:

```tsx
// StoryShell.tsx / AgentsShell.tsx
<div style={getPageThemeStyle(pageTheme)}>      {/* Layer 2 */}
  <Header />                                     {/* Inherits page theme */}
  <div style={getCardThemeStyle(cardsTheme)}>  {/* Layer 3 */}
    <Layout>
      {/* Cards render here, inherit both themes */}
    </Layout>
  </div>
</div>
```

**Key principle:** These wrapper divs are **transparent** — they don't render visible surfaces. They only set CSS variables that descendants inherit.

### Theme Layers in Detail

#### Layer 2: Page Theme (`page_themes.ts`)

Controls the overall page appearance including header:

```typescript
{
  id: "midnight",
  name: "Midnight",
  tokens: {
    "--background": "oklch(0.15 0.02 260)",      // Page background
    "--foreground": "oklch(0.95 0.01 260)",      // Text color
    "--card": "oklch(0.18 0.025 260)",           // Card surfaces
    "--card-foreground": "oklch(0.95 0.01 260)", // Card text
    "--border": "oklch(0.3 0.03 260)",           // Borders
    // ... more variables
  }
}
```

**Important:** Page themes INCLUDE `--background` because they control the page surface.

#### Layer 3: Cards Theme (`card_themes.ts`)

Controls card appearance within the page:

```typescript
{
  id: "oracle",
  name: "Oracle",
  tokens: {
    // NO --background here! Preserves page theme.
    "--card": "oklch(0.2 0.03 280)",
    "--card-foreground": "oklch(0.95 0.02 280)",
    "--border": "oklch(0.35 0.04 280)",
    "--agent-accent": "oklch(0.6 0.18 280)",
    "--story-accent": "oklch(0.6 0.18 280)",
    // ... more variables
  }
}
```

**Important:** Cards themes EXCLUDE `--background` to avoid double-setting the page surface.

#### Layer 4: Instance Presentation

Each entity (Story, Agent) can carry presentation data:

```typescript
// Stored with entity in database
interface StoryPresentation {
  tokens?: {
    "--story-accent": "oklch(0.6 0.15 155)",
    "--story-card-radius": "12px",
    // ...
  },
  avatar?: {
    emoji: "🧭",
    backgroundColor: "oklch(0.5 0.15 155)",
  },
  decorationHint?: "organic" | "warm" | "precise" | "brutalist" | "ethereal" | "neon",
}
```

## Decoration Hints

Decoration hints provide typographic and stylistic variations without requiring full token overrides.

### Available Hints

| Hint | Typography | Visual Character |
|------|------------|------------------|
| `organic` | Default | Natural, flowing |
| `warm` | Default | Inviting, friendly |
| `precise` | Default | Clean, exact |
| `brutalist` | `font-mono`, `uppercase`, `tracking-wide` | Industrial, stark |
| `ethereal` | `font-serif`, `italic` | Dreamy, mystical |
| `neon` | Default | Vibrant, electric |

### How Hints Apply Styles

```tsx
// In StoryCard/AgentCard
function getDecorationClasses(hint?: DecorationHint): string {
  switch (hint) {
    case "brutalist": return "font-mono"
    case "ethereal": return "font-serif"
    default: return ""
  }
}

function getDecorationTitleClasses(hint?: DecorationHint): string {
  switch (hint) {
    case "brutalist": return "uppercase tracking-wide text-[13px]"
    case "ethereal": return "italic font-normal text-[16px]"
    default: return ""
  }
}

// Applied to card wrapper and title
<div className={cn("transition-all", getDecorationClasses(resolved.decorationHint))}>
  <CardTitle className={cn("truncate", getDecorationTitleClasses(resolved.decorationHint))}>
```

### Type Defaults

Story and Agent types have default presentations including decoration hints:

```typescript
// resolve.ts
export const STORY_TYPE_PRESENTATIONS: Record<StoryTypeKey, StoryPresentation> = {
  process:    { decorationHint: "organic",   avatar: { emoji: "🧭" }, tokens: {...} },
  dynamic:    { decorationHint: "warm",      avatar: { emoji: "🎨" }, tokens: {...} },
  analytic:   { decorationHint: "precise",   avatar: { emoji: "📊" }, tokens: {...} },
  safety:     { decorationHint: "brutalist", avatar: { emoji: "🛡️" }, tokens: {...} },
  prediction: { decorationHint: "ethereal",  avatar: { emoji: "🔮" }, tokens: {...} },
  review:     { decorationHint: "neon",      avatar: { emoji: "⚙️" }, tokens: {...} },
}
```

## Resolution Order

When rendering a card, presentation is resolved in this order:

```typescript
// Later layers override earlier ones
const resolved = resolveStoryPresentation(
  typeDefaults,           // From STORY_TYPE_PRESENTATIONS based on story_type
  story.presentation,     // Instance-level overrides from database
)
```

The cascade then applies:
1. `:root` variables (application defaults)
2. Page theme variables (override application)
3. Cards theme variables (override page for card-related vars)
4. Instance presentation (override cards theme for specific card)

## CSS Variable Application

Variables are applied via inline styles on wrapper divs:

```tsx
// presentationToStyle converts tokens to React CSSProperties
export function presentationToStyle(
  tokens?: PresentationTokens,
): React.CSSProperties | undefined {
  if (!tokens || Object.keys(tokens).length === 0) return undefined

  const style: Record<string, string> = {}
  for (const [key, value] of Object.entries(tokens)) {
    if (value !== undefined) {
      style[key] = value
    }
  }
  return style as unknown as React.CSSProperties
}

// Usage in card
<div style={presentationToStyle(resolved.tokens)}>
  <Card>...</Card>
</div>
```

## Accent Strips

Cards can display a colored accent strip based on presentation:

```typescript
tokens: {
  "--story-accent": "oklch(0.6 0.15 155)",        // Color
  "--story-accent-position": "top",               // top | bottom | left | none
  "--story-accent-width": "3px",                  // Thickness
}
```

The `AccentStrip` component reads these and renders appropriately:

```tsx
function AccentStrip({ presentation, enabled }) {
  const position = presentation.tokens?.["--story-accent-position"] ?? "top"
  const width = presentation.tokens?.["--story-accent-width"] ?? "3px"
  const color = presentation.tokens?.["--story-accent"]

  if (position === "none" || !color) return null
  // ... render positioned div with backgroundColor
}
```

## Theme Persistence

Currently using localStorage for session persistence:

```tsx
// Route component (story.tsx, agents.tsx)
const STORAGE_KEYS = {
  pageTheme: "story-page-theme",
  cardsTheme: "story-cards-theme",
} as const

// Lazy initialization reads from localStorage
const [pageThemeId, setPageThemeId] = useState(() =>
  localStorage.getItem(STORAGE_KEYS.pageTheme) ?? "default"
)

// Handler persists to localStorage
const handlePageThemeChange = (themeId: string) => {
  setPageThemeId(themeId)
  localStorage.setItem(STORAGE_KEYS.pageTheme, themeId)
}
```

### Future: Backend Persistence

When implementing `useUserPagePrefs()`:

```typescript
// Hook signature
function useUserPagePrefs(pageKey: string): {
  prefs: { pageTheme: string; cardsTheme: string }
  updatePageTheme: (themeId: string) => void
  updateCardsTheme: (themeId: string) => void
  isLoading: boolean
}

// Usage in route
const { prefs, updatePageTheme, updateCardsTheme } = useUserPagePrefs("story")
```

## File Structure

```
src/components/Common/Themes/
├── CASCADING-THEMES.md      # This document
├── types.ts                 # PresentationTokens, StoryPresentation, etc.
├── resolve.ts               # Resolution functions, type defaults
├── page_themes.ts           # PAGE_THEMES array, getPageThemeStyle()
└── card_themes.ts           # CARD_THEMES array, getCardThemeStyle()

src/components/Story/
├── StoryShell.tsx           # Sets up page/cards theme wrappers
├── StoryHeader.tsx          # Theme selector dropdowns
├── StoryLayout.tsx          # Panel arrangement
└── StoryList/
    └── StoryCard.tsx        # Card variants with presentation support

src/routes/_layout/
├── story.tsx                # Route with theme state + localStorage
└── agents.tsx               # Route with theme state + localStorage
```

## Quick Reference

### Adding a New Theme

**Page Theme:**
```typescript
// page_themes.ts
{
  id: "my-theme",
  name: "My Theme",
  tokens: {
    "--background": "...",      // REQUIRED for page themes
    "--foreground": "...",
    "--card": "...",
    // ...
  }
}
```

**Cards Theme:**
```typescript
// card_themes.ts
{
  id: "my-card-theme",
  name: "My Card Theme",
  tokens: {
    // NO --background here!
    "--card": "...",
    "--card-foreground": "...",
    "--border": "...",
    "--story-accent": "...",    // Optional accent color
    // ...
  }
}
```

### Adding a New Type Presentation

```typescript
// resolve.ts
export const STORY_TYPE_PRESENTATIONS: Record<StoryTypeKey, StoryPresentation> = {
  // ...existing types
  my_type: {
    tokens: {
      "--story-accent": "oklch(0.6 0.15 200)",
      "--story-accent-foreground": "oklch(1 0 0)",
    },
    avatar: { emoji: "🆕" },
    decorationHint: "precise",
  },
}
```

### Adding a New Decoration Hint

1. Add to type definition in `types.ts`:
   ```typescript
   decorationHint?: "warm" | "neon" | "precise" | "organic" | "brutalist" | "ethereal" | "my-hint"
   ```

2. Handle in card components:
   ```typescript
   function getDecorationClasses(hint?: DecorationHint): string {
     switch (hint) {
       case "my-hint": return "font-special tracking-tight"
       // ...
     }
   }
   ```

## Debugging

Enable debug mode on cards to see presentation info:

```tsx
<StoryCard story={story} debug />
```

This renders a debug panel showing:
- Presentation source (instance vs type default)
- Token count
- Decoration hint
- Accent position

## Key Principles

1. **Transparent wrappers** — Theme layers don't render visible surfaces, only set variables
2. **No --background in cards themes** — Prevents overriding page surface
3. **CSS inheritance** — No specificity hacks needed, pure cascade
4. **Shallow merge** — Later layers override earlier, not deep merge
5. **Empty "default" themes** — Enable clean fallthrough to application defaults
6. **Presentation-as-data** — Styling stored with entity, not scattered in CSS files
