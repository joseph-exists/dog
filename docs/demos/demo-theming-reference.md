# Demo Theming — Engineering Reference Card

> How to create visual themes for demo pages. Multiple demos can share the same room and functionality while presenting a completely different visual experience.

  ★ Insights
  ─────────────────────────────────────
  Design philosophy across themes:
  - Color-only themes (gruvbox, dracula, enchanted-rose,
  dark-forest): Override backgrounds, borders, and text colors. Stay
   within the existing geometry.
  - Typography themes (medieval, math, ancient-tome): Change fonts,
  letter-spacing, and font-variant in addition to colors.
  - Geometry themes (bauhaus, dekonstruct): Change border-radius,
  box-shadow offsets, even transform: rotate() to break the expected
   layout.
  - Effect themes (technorave, terminal, vaporwave, spiritual-math):
   Add text-shadow, neon box-shadow glows, CSS ::before content, and
   background patterns.

  Some highlights:
  - terminal uses ::before { content: "> " } and "$ "
  pseudo-elements for authentic CLI feel, plus a
  repeating-linear-gradient for scanline effects
  - math uses a graph-paper background pattern via tiny grid
  gradients
  - bauhaus and dekonstruct use transform on hover for physical
  displacement effects
  - spiritual-math uses border-radius: 50% / 10% for an elliptical
  "cosmic" node shape
  ─────────────────────────────────────────────────

## Architecture

```
DemoConfig.theme = "enchanted-rose"
        │
        ▼
DemoPage: <div data-demo-theme="enchanted-rose">
        │
        ▼
demo-themes.css: [data-demo-theme="enchanted-rose"] .demo-node { ... }
        │
        ▼
Components: <div class="demo-node rounded-lg border bg-card ...">
                   ▲                ▲
                   │                └── Tailwind defaults (no theme = standard look)
                   └── Semantic hook (theme CSS targets this)
```

**Key principle:** Themes are additive CSS overrides. When no theme is set, the existing Tailwind classes render the default look. When a theme is active, CSS specificity overrides the visual properties.

---

## Quick Start: Creating a New Theme

### 1. Add a theme block to `frontend/src/styles/demo-themes.css`

```css
/* Theme: your-theme-name */
[data-demo-theme="your-theme-name"] .demo-node {
  background: #your-color;
  border-color: #your-border;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

[data-demo-theme="your-theme-name"] .demo-node-title {
  color: #your-title-color;
}

[data-demo-theme="your-theme-name"] .demo-choice {
  background: #your-choice-bg;
  border-color: #your-choice-border;
  color: #your-choice-text;
}

/* ... override as many or as few classes as needed */
```

### 2. Add a demo config entry

```typescript
// frontend/src/config/demos.ts
"your-demo-slug": {
  slug: "your-demo-slug",
  title: "Your Themed Demo",
  description: "Same story, different vibe.",
  roomId: "existing-room-uuid",  // Can share a room with other demos
  autoRespond: true,
  theme: "your-theme-name",      // Matches data-demo-theme value
},
```

### 3. Visit `/demo/your-demo-slug`

That's it. The theme CSS overrides take effect immediately.

---

## Semantic Class Reference

These classes are placed on components as styling hooks. They don't affect default rendering — they only become active when targeted by theme CSS.

| Class | Component | Element | What to Override |
|-------|-----------|---------|-----------------|
| `.demo-header` | `DemoHeader` | Header bar | `background`, `border-bottom-color` |
| `.demo-story-content` | `StoryPanel` | Content wrapper | `background` |
| `.demo-node` | `NodeDisplay` | Card container | `background`, `border-color`, `box-shadow`, `border-radius` |
| `.demo-node-title` | `NodeDisplay` | Title `<h3>` | `color`, `font-*`, `letter-spacing` |
| `.demo-node-content` | `NodeDisplay` | Content wrapper | `color`, `font-family`, `line-height` |
| `.demo-choice` | `ChoiceItem` | Button/card (all variants) | `background`, `border-color`, `color`, `border-radius` |
| `.demo-choice-list` | `ChoiceList` | List wrapper | `gap` |
| `.demo-choice-empty` | `ChoiceList` | Empty state | `border-color`, `color`, `background` |
| `.demo-controls` | `RuntimeControls` | Controls wrapper | (layout) |
| `.demo-control` | `RuntimeControls` | Rewind/Reset buttons | `border-color`, `color`, `background` |
| `.demo-chain` | `NodeChainCollapsible` | Chain content area | `background`, `border-color` |
| `.demo-chain-active` | `NodeChainCollapsible` | Active node entry | `background`, `color` |
| `.demo-state` | `StoryStateCollapsible` | State JSON area | `background`, `border-color`, `color` |

---

## Interaction States

Always define hover/disabled states for interactive elements:

```css
/* Hover — only when not disabled */
[data-demo-theme="X"] .demo-choice:hover:not(:disabled) {
  background: ...;
  border-color: ...;
  box-shadow: ...;
}

/* Disabled state */
[data-demo-theme="X"] .demo-choice:disabled {
  background: ...;
  opacity: 0.6;
}

/* Control buttons follow the same pattern */
[data-demo-theme="X"] .demo-control:hover:not(:disabled) {
  background: ...;
}
```

---

## Targeting Nested Elements

For elements inside semantic containers that don't have their own class:

```css
/* Header title and description */
[data-demo-theme="X"] .demo-header h1 {
  color: ...;
  font-style: italic;
}
[data-demo-theme="X"] .demo-header p {
  color: ...;
}

/* All chain buttons (non-active) */
[data-demo-theme="X"] .demo-chain button {
  color: ...;
}
[data-demo-theme="X"] .demo-chain button:hover {
  background: ...;
}
```

---

## Sharing Rooms Between Themes

Multiple demo configs can point to the same `roomId`. The theme is purely a frontend presentation concern — the backend doesn't know or care about themes.

```typescript
// Same room, three different looks:
"library-default": { roomId: "abc-123", /* no theme */ },
"library-rose":    { roomId: "abc-123", theme: "enchanted-rose" },
"library-forest":  { roomId: "abc-123", theme: "dark-forest" },
```

**Implications:**
- Messages sent in one themed view appear in all others (same room)
- Agents respond identically regardless of which theme is active
- Story progress is shared (advancing in one view advances in all)

---

## Available Themes

| Theme | Slug | Vibe |
|-------|------|------|
| (default) | `story-runtime` | Standard shadcn/Tailwind look |
| `enchanted-rose` | `story-runtime-rose` | Warm rose/pink, soft shadows, romantic |
| `dark-forest` | `story-runtime-forest` | Deep emerald, moody, nature-inspired |
| `ancient-tome` | `story-runtime-tome` | Parchment sepia, serif fonts, scholarly |
| `gruvbox` | `story-runtime-gruvbox` | Warm retro — earthy browns, orange/yellow accents |
| `dracula` | `story-runtime-dracula` | Rich purples, soft pinks, glowing cyans |
| `bauhaus` | `story-runtime-bauhaus` | Bold primary colors, geometric, modernist |
| `dekonstruct` | `story-runtime-dekonstruct` | Fragmented, brutalist, monospace, angular |
| `medieval` | `story-runtime-medieval` | Illuminated manuscript — crimsons, golds, navy |
| `math` | `story-runtime-math` | Graph paper, monospace, LaTeX-inspired, blue accents |
| `technorave` | `story-runtime-technorave` | Cyberpunk neon — cyan, magenta, acid lime, glow |
| `spiritual-math` | `story-runtime-spiritual-math` | Sacred geometry — indigo, gold, transcendent |
| `terminal` | `story-runtime-terminal` | Green-on-black CRT, phosphor glow, scanlines |
| `vaporwave` | `story-runtime-vaporwave` | Retro-futurist pastels — pink, blue, purple, dreamy |

---

## File Map

| File | Purpose |
|------|---------|
| `frontend/src/styles/demo-themes.css` | All theme definitions |
| `frontend/src/config/demos.ts` | Theme → slug assignment |
| `frontend/src/components/Demo/DemoPage.tsx` | Applies `data-demo-theme` attribute |
| `frontend/src/main.tsx` | Imports the themes CSS |

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Semantic classes + CSS overrides (not CSS variables) | Simpler than fighting Tailwind's opacity/color handling with `var()` fallbacks |
| Additive-only (no Tailwind class removal) | Zero risk of breaking default rendering; themes are purely additional |
| `data-demo-theme` attribute (not class) | Attribute selectors are explicit and don't collide with utility classes |
| Theme CSS in one file | Easy to find all themes, compare patterns, copy-paste for new ones |
| Hover/disabled states via `:hover:not(:disabled)` | Ensures disabled buttons don't show hover effects |
| No component prop drilling | Theme awareness is in CSS, not React — components stay simple |

---

## Extending the System

### Adding New Themeable Surfaces

If a new component is added to StoryPanel:

1. Add a semantic class to the component's root element:
   ```tsx
   <div className="demo-my-widget ...tailwind-classes...">
   ```

2. Document it in the reference table above

3. Override it in any themes that need it:
   ```css
   [data-demo-theme="enchanted-rose"] .demo-my-widget { ... }
   ```

### Dark Mode Compatibility

Theme colors should work in both light and dark mode if your app supports it. Test both, or scope themes to one mode:

```css
/* Only apply in light mode */
:root[class="light"] [data-demo-theme="enchanted-rose"] .demo-node { ... }

/* Only apply in dark mode */
:root[class="dark"] [data-demo-theme="dark-forest"] .demo-node { ... }
```

### Typography Themes

The `ancient-tome` theme demonstrates typography overrides:

```css
[data-demo-theme="ancient-tome"] .demo-node-title {
  font-variant: small-caps;
  letter-spacing: 0.05em;
}

[data-demo-theme="ancient-tome"] .demo-node-content {
  font-family: Georgia, "Times New Roman", serif;
  line-height: 1.7;
}
```

Any CSS property can be overridden — not just colors. Consider `font-family`, `letter-spacing`, `border-radius`, `border-width`, gradients, animations, and transforms.

### Animation/Transition Themes

```css
[data-demo-theme="magical"] .demo-node {
  transition: all 0.3s ease;
  animation: fade-in 0.5s ease-out;
}

[data-demo-theme="magical"] .demo-choice:hover:not(:disabled) {
  transform: translateX(4px);
  transition: transform 0.2s ease;
}
```

---

## Debugging

| Symptom | Check |
|---------|-------|
| Theme not applying | Does `data-demo-theme` attribute appear in DOM? Check DemoPage renders with the attribute. |
| Only some overrides work | CSS specificity issue. Ensure selector matches: `[data-demo-theme="X"] .demo-Y` |
| Tailwind fights override | The semantic class override should win via specificity. If not, add `!important` as last resort. |
| Theme leaks to non-demo pages | Impossible — `data-demo-theme` is only set on the DemoPage root. |
| Hover styles on disabled buttons | Use `:hover:not(:disabled)` in your CSS. |
| Theme looks wrong in dark mode | Theme colors may be designed for light mode only. Add mode-specific selectors if needed. |

---

## Gotchas and Pitfalls

### 1. The `:disabled` Hover Trap

**Problem:** If you define `.demo-choice:hover` without excluding disabled state, disabled buttons will still show hover effects.

```css
/* ❌ BAD — disabled buttons will glow on hover */
[data-demo-theme="X"] .demo-choice:hover {
  box-shadow: 0 0 10px cyan;
}

/* ✅ GOOD — disabled buttons stay inert */
[data-demo-theme="X"] .demo-choice:hover:not(:disabled) {
  box-shadow: 0 0 10px cyan;
}
```

### 2. Shadcn Button Internals

The `.demo-choice` class targets the `<Button>` component's root element, but shadcn buttons have internal structure. If you need to style the text specifically:

```css
/* Target the span inside the button */
[data-demo-theme="X"] .demo-choice span {
  text-transform: uppercase;
}
```

### 3. Collapsible Trigger Buttons

The `NodeChainCollapsible` and `StoryStateCollapsible` components use shadcn's `Collapsible` with a `Button` as the trigger. The trigger button is NOT inside `.demo-chain` — it's a sibling. To style the trigger:

```css
/* The trigger button is a sibling, not a child */
[data-demo-theme="X"] .demo-chain + button,
[data-demo-theme="X"] .demo-state + button {
  /* Won't work — wrong DOM structure */
}

/* Instead, target via the Collapsible wrapper if needed */
```

**Current limitation:** The collapsible triggers don't have semantic classes. For most themes, they inherit from shadcn's `Button variant="ghost"` which looks acceptable. If you need to style them, consider adding `demo-chain-trigger` and `demo-state-trigger` classes to the components.

### 4. CSS Specificity Battles

Theme selectors like `[data-demo-theme="X"] .demo-node` have specificity `(0, 2, 0)`. Tailwind utilities typically have `(0, 1, 0)`. You should win — but if something doesn't override:

```css
/* Nuclear option — use sparingly */
[data-demo-theme="X"] .demo-node {
  background: #123456 !important;
}
```

**Better:** Check if there's an inline style or a more specific selector. Tailwind's arbitrary values like `bg-[#abc]` can sometimes create issues.

### 5. Border Shorthand Resets

When you use the `border` shorthand, it resets all border properties:

```css
/* ❌ This removes border-radius set by Tailwind */
[data-demo-theme="X"] .demo-node {
  border: 3px solid red;
}

/* ✅ Only override what you need */
[data-demo-theme="X"] .demo-node {
  border-width: 3px;
  border-style: solid;
  border-color: red;
}
```

### 6. Gradient Backgrounds and Borders

You can't use `border-color` with a gradient. For gradient borders:

```css
[data-demo-theme="X"] .demo-node {
  border: 2px solid transparent;
  background:
    linear-gradient(#1a1a1a, #1a1a1a) padding-box,
    linear-gradient(135deg, cyan, magenta) border-box;
}
```

### 7. Font Stacks and Fallbacks

Always include fallback fonts. Users may not have your preferred font:

```css
/* ❌ Will fall back to browser default if missing */
font-family: "Fira Code";

/* ✅ Graceful degradation */
font-family: "Fira Code", "Courier New", monospace;
```

### 8. The `content` Property Gotcha

When using `::before` or `::after` pseudo-elements, the `content` property is required:

```css
/* ❌ Nothing will render */
[data-demo-theme="X"] .demo-choice::before {
  color: green;
}

/* ✅ Must have content */
[data-demo-theme="X"] .demo-choice::before {
  content: "→ ";
  color: green;
}
```

---

## Advanced Techniques

### Pseudo-Element Prefixes (terminal, math themes)

Add visual prefixes without changing component markup:

```css
/* Terminal prompt prefix */
[data-demo-theme="terminal"] .demo-choice::before {
  content: "$ ";
  color: #1a991a;
}

/* Math arrow prefix */
[data-demo-theme="math"] .demo-choice::before {
  content: "→ ";
  color: #2563eb;
}

/* Bracket-wrapped titles */
[data-demo-theme="terminal"] .demo-node-title::before {
  content: "[ ";
  color: #1a991a;
}
[data-demo-theme="terminal"] .demo-node-title::after {
  content: " ]";
  color: #1a991a;
}
```

### Background Patterns (math, terminal themes)

Create texture without images:

```css
/* Graph paper grid */
[data-demo-theme="math"] .demo-story-content {
  background:
    linear-gradient(rgba(200, 220, 240, 0.15) 1px, transparent 1px),
    linear-gradient(90deg, rgba(200, 220, 240, 0.15) 1px, transparent 1px);
  background-size: 20px 20px;
  background-color: #ffffff;
}

/* CRT scanlines */
[data-demo-theme="terminal"] .demo-story-content {
  background-image: repeating-linear-gradient(
    0deg,
    rgba(51, 255, 51, 0.03) 0px,
    rgba(51, 255, 51, 0.03) 1px,
    transparent 1px,
    transparent 3px
  );
  background-color: #0a0a0a;
}
```

### Neon Glow Effects (technorave, vaporwave, terminal themes)

Layer multiple box-shadows for depth:

```css
[data-demo-theme="technorave"] .demo-node {
  box-shadow:
    0 0 10px rgba(0, 255, 255, 0.3),      /* Inner glow */
    inset 0 0 20px rgba(0, 255, 255, 0.05); /* Subtle inner light */
}

[data-demo-theme="technorave"] .demo-choice:hover:not(:disabled) {
  box-shadow:
    0 0 15px rgba(255, 0, 255, 0.4),      /* Outer glow */
    inset 0 0 15px rgba(255, 0, 255, 0.1); /* Inner glow */
  text-shadow: 0 0 8px rgba(255, 0, 255, 0.6);
}
```

### Text Glow (technorave, terminal, vaporwave themes)

```css
[data-demo-theme="terminal"] .demo-node-title {
  color: #33ff33;
  text-shadow: 0 0 6px rgba(51, 255, 51, 0.4);
}

/* Layered text glow for intensity */
[data-demo-theme="vaporwave"] .demo-header h1 {
  text-shadow:
    0 0 10px rgba(255, 113, 206, 0.5),
    0 0 20px rgba(255, 113, 206, 0.3),
    0 0 40px rgba(255, 113, 206, 0.1);
}
```

### Physical Displacement (bauhaus, dekonstruct themes)

Make elements feel tangible:

```css
/* Offset shadow for "lifted" appearance */
[data-demo-theme="bauhaus"] .demo-node {
  box-shadow: 6px 6px 0 #1a1a1a;
}

/* Hover lifts further */
[data-demo-theme="bauhaus"] .demo-choice:hover:not(:disabled) {
  transform: translate(-2px, -2px);
  box-shadow: 4px 4px 0 #1a1a1a;
}

/* Slight rotation for "handmade" feel */
[data-demo-theme="dekonstruct"] .demo-node {
  transform: rotate(-0.5deg);
}

[data-demo-theme="dekonstruct"] .demo-choice:hover:not(:disabled) {
  transform: rotate(1deg) scale(1.02);
}
```

### Gradient Backgrounds (medieval, vaporwave, spiritual-math themes)

```css
/* Subtle directional gradient */
[data-demo-theme="medieval"] .demo-story-content {
  background: linear-gradient(180deg, #f5e6c8, #ede0c8);
}

/* Multi-stop gradient for depth */
[data-demo-theme="vaporwave"] .demo-header {
  background: linear-gradient(135deg, #1a0033, #330066, #1a0033);
}

/* Semi-transparent overlays */
[data-demo-theme="spiritual-math"] .demo-node {
  background: linear-gradient(
    145deg,
    rgba(49, 46, 129, 0.8),
    rgba(30, 27, 75, 0.9)
  );
}
```

### Non-Standard Border Radius (spiritual-math theme)

Create unusual shapes:

```css
/* Elliptical/pill shape */
[data-demo-theme="spiritual-math"] .demo-node {
  border-radius: 50% / 10%;  /* horizontal / vertical */
}

/* Asymmetric corners */
[data-demo-theme="asymmetric"] .demo-node {
  border-radius: 24px 4px 24px 4px;
}
```

### Double Borders (medieval theme)

```css
[data-demo-theme="medieval"] .demo-node {
  border: 3px double #8b0000;
}
```

### Inset Shadows for Depth (medieval, gruvbox themes)

```css
[data-demo-theme="medieval"] .demo-node {
  box-shadow:
    0 2px 8px rgba(139, 0, 0, 0.15),              /* Outer shadow */
    inset 0 0 20px rgba(184, 134, 11, 0.05);      /* Inner golden glow */
}
```

---

## Theme Design Patterns

When creating a new theme, consider which pattern fits your vision:

### Pattern 1: Color Swap

Minimal changes — just replace the color palette. Good for editor themes (gruvbox, dracula) where the structure should stay familiar.

**Override:** `background`, `border-color`, `color` on all elements.
**Preserve:** All geometry, typography, spacing.

### Pattern 2: Typography Transformation

Change the reading experience. Serif for classical, monospace for technical, display fonts for playful.

**Override:** `font-family`, `font-weight`, `font-style`, `letter-spacing`, `line-height`, `font-variant`.
**Consider:** `text-transform`, `text-decoration`, `word-spacing`.

### Pattern 3: Geometric Restructuring

Break expectations about shape and space. Remove rounded corners for brutalism, add extreme rounding for softness.

**Override:** `border-radius`, `border-width`, `padding`, `gap`.
**Consider:** `transform: rotate()` for off-kilter layouts.

### Pattern 4: Effect Layering

Add depth and atmosphere through shadows, glows, and gradients.

**Override:** `box-shadow` (multiple layers), `text-shadow`, `background` (gradients).
**Consider:** `filter: blur()` or `filter: brightness()` for ambient effects.

### Pattern 5: Synthetic Content

Use `::before` and `::after` to add visual elements that don't exist in the markup.

**Add:** Prefixes, suffixes, decorative elements, background patterns.
**Consider:** `content: url()` for small images, `content: attr()` for dynamic content.

### Pattern 6: Motion and Interaction

Define how elements respond to user interaction.

**Add:** `transition` for smooth state changes, `transform` on hover.
**Consider:** `animation` for ambient motion (use sparingly for accessibility).

---

## Color System Guidelines

### Cohesive Palette Construction

Each theme should have:

1. **Background hierarchy** (3-4 levels of depth)
   - Page background (deepest)
   - Card/panel background
   - Interactive element background
   - Hover/active state background

2. **Text hierarchy** (3 levels)
   - Primary text (titles, important content)
   - Secondary text (body content)
   - Muted text (hints, metadata)

3. **Border hierarchy** (2-3 levels)
   - Strong borders (cards, primary divisions)
   - Subtle borders (internal divisions)
   - Accent borders (active states)

4. **Accent color(s)**
   - Primary accent (active states, links)
   - Secondary accent (highlights, badges)

### Example: gruvbox palette mapping

```
Page bg:        #282828 (bg0)
Card bg:        #3c3836 (bg1)
Interactive bg: #504945 (bg2)
Hover bg:       #665c54 (bg3)

Primary text:   #ebdbb2 (fg)
Secondary text: #d5c4a1 (fg2)
Muted text:     #928374 (gray)

Primary border: #665c54
Subtle border:  #504945

Primary accent: #fe8019 (orange)
Secondary:      #fabd2f (yellow)
Tertiary:       #83a598 (blue)
```

### Contrast Requirements

Ensure sufficient contrast for readability:

- **Text on background:** Aim for WCAG AA (4.5:1 for normal text, 3:1 for large text)
- **Interactive elements:** Should be distinguishable from surrounding content
- **Disabled states:** Should look "muted" but text should remain readable

Dark themes (terminal, technorave, dracula) need extra attention — don't make text too dim.

---

## Integrating Theming with Non-Demo Pages

The theming system can extend beyond demos. Here's how:

### Option 1: Reuse the data attribute pattern

Any page can use `data-demo-theme`:

```tsx
// In any component
<div data-demo-theme="technorave" className="p-4">
  <div className="demo-node">
    This will render with technorave styling
  </div>
</div>
```

### Option 2: Create a ThemeProvider component

```tsx
// components/ThemeProvider.tsx
interface ThemeProviderProps {
  theme?: string;
  children: React.ReactNode;
}

export function ThemeProvider({ theme, children }: ThemeProviderProps) {
  return (
    <div {...(theme ? { "data-demo-theme": theme } : {})}>
      {children}
    </div>
  );
}
```

### Option 3: Add semantic classes to shared components

If you have components used across the app that should be themeable:

1. Add semantic classes (`demo-*` or a new namespace like `themed-*`)
2. Import `demo-themes.css` (already imported in `main.tsx`)
3. Wrap the page section in `data-demo-theme`

### Option 4: Create separate theme files per feature

For large features with their own theming needs:

```
frontend/src/styles/
├── demo-themes.css       # Demo-specific themes
├── story-editor-themes.css   # Story editor themes
└── chat-themes.css       # Chat interface themes
```

Each file follows the same pattern: `[data-X-theme="Y"] .semantic-class { ... }`

---

## Performance Considerations

### CSS File Size

Each theme adds ~80-150 lines of CSS. With 13 themes, the file is ~1500 lines. This is acceptable for most applications, but consider:

- **Code splitting:** If themes are rarely used, consider dynamic imports
- **Purging:** Unused themes won't be tree-shaken (CSS isn't analyzed like JS)
- **Compression:** CSS compresses well with gzip/brotli

### Selector Performance

Attribute selectors `[data-demo-theme="X"]` are slightly slower than class selectors, but the difference is negligible for this use case. The browser only evaluates these selectors within the scoped subtree.

### Animation Performance

If adding animations:

```css
/* ✅ GPU-accelerated properties */
transform: translateX(10px);
opacity: 0.5;

/* ❌ Triggers layout/paint (avoid animating) */
width: 100px;
padding: 10px;
border-width: 2px;
```

---

## Ideas for Future Expansion

### 1. Seasonal/Event Themes

Create themes for holidays, events, or campaigns:

- `theme: "halloween"` — Orange and black, spider web patterns
- `theme: "winter"` — Frost effects, blue/white palette, snowflake backgrounds
- `theme: "launch-party"` — Confetti animations, celebration colors

### 2. Accessibility Themes

Themes optimized for specific needs:

- `theme: "high-contrast"` — Maximum contrast, thick borders, clear focus states
- `theme: "reduced-motion"` — Disables all animations/transitions
- `theme: "large-text"` — Increased font sizes, adjusted spacing
- `theme: "dyslexia-friendly"` — OpenDyslexic font, adjusted spacing

### 3. Story-Content-Aware Theming

Themes that respond to story metadata:

```typescript
// In StoryPanel, derive theme from story data
const storyGenre = runtime.storyMetadata?.genre;
const autoTheme = genreToTheme[storyGenre] ?? config.theme;
```

Mapping: horror → `dark-forest`, romance → `enchanted-rose`, sci-fi → `technorave`.

### 4. User-Selectable Themes

Add a theme picker to the demo header:

```typescript
// DemoHeader.tsx
<Select value={theme} onValueChange={setTheme}>
  <SelectItem value="">Default</SelectItem>
  <SelectItem value="dracula">Dracula</SelectItem>
  <SelectItem value="gruvbox">Gruvbox</SelectItem>
  {/* ... */}
</Select>
```

### 5. Theme Transitions

Smooth transitions when switching themes:

```css
[data-demo-theme] * {
  transition:
    background-color 0.3s ease,
    border-color 0.3s ease,
    color 0.3s ease,
    box-shadow 0.3s ease;
}
```

### 6. Generative/Dynamic Themes

Themes built from seed values:

```typescript
// Generate cohesive palette from a single hue
function generateTheme(hue: number) {
  return {
    primary: `hsl(${hue}, 70%, 50%)`,
    background: `hsl(${hue}, 20%, 10%)`,
    // ...
  };
}
```

Apply via CSS custom properties or inline styles.

### 7. Audio-Visual Themes

Themes that include ambient audio:

```typescript
// Play background audio when theme is active
useEffect(() => {
  if (theme === "medieval") {
    playAmbientAudio("/audio/tavern-ambiance.mp3");
  }
  return () => stopAmbientAudio();
}, [theme]);
```

### 8. Time-Based Themes

Themes that change based on time of day:

```typescript
const hour = new Date().getHours();
const autoTheme = hour < 6 ? "terminal" :
                  hour < 18 ? "math" :
                  "dracula";
```

### 9. Reading Progress Themes

Themes that evolve as the user progresses:

```css
/* Color intensity increases with story progress */
[data-demo-theme="evolving"][data-progress="early"] .demo-node {
  background: rgba(100, 100, 200, 0.3);
}
[data-demo-theme="evolving"][data-progress="late"] .demo-node {
  background: rgba(100, 100, 200, 0.8);
}
```

### 10. Collaborative Themes

Themes where each participant sees personalized colors:

```typescript
// Assign user-specific accent color
const userHue = hashStringToHue(currentUser.id);
style={{ '--user-accent': `hsl(${userHue}, 70%, 50%)` }}
```

---

## Testing Themes

### Visual Regression Testing

Consider adding visual regression tests for themes:

```typescript
// playwright/themes.spec.ts
for (const theme of allThemes) {
  test(`${theme} renders correctly`, async ({ page }) => {
    await page.goto(`/demo/story-runtime-${theme}`);
    await expect(page).toHaveScreenshot(`${theme}.png`);
  });
}
```

### Manual Testing Checklist

When creating a new theme, verify:

- [ ] Node card is readable (title, content)
- [ ] All choice states work (normal, hover, disabled)
- [ ] Empty state is visible
- [ ] Control buttons are visible and interactive
- [ ] Collapsible sections expand/collapse correctly
- [ ] Active node in chain is distinguishable
- [ ] Story state JSON is readable
- [ ] Header title and description are readable
- [ ] Connection badge is visible
- [ ] Works in both light and dark system modes (if applicable)

---

## Contributing a Theme

To add a theme to the codebase:

1. **Choose a distinctive identity** — What makes this theme special?
2. **Create the CSS block** — Start from a similar existing theme
3. **Test all states** — Normal, hover, disabled, empty, active
4. **Add the demo config** — With an evocative title and description
5. **Update this reference** — Add to the Available Themes table
6. **Consider documentation** — If using advanced techniques, document them

Theme contributions that add genuine personality and don't duplicate existing vibes are welcome!
