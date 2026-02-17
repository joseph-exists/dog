# Page Theme Layer: Design Document

> **Location:** `frontend/src/components/Agents/AgentsShell/`
> **Status:** Ready for implementation
> **Created:** 2026-02-11
LAST REVISION 2.17 josep & claude

---

REVIEW THESE CHANGES FIRST:

  ★ Insight ─────────────────────────────────────
  Plan vs Reality: The plan was executed successfully, but with one key refinement—we split AMBIENT_THEMES into
   PAGE_THEMES and CARD_THEMES to enforce the rule that cards themes shouldn't include --background. This is an
   improvement over the original design.
  ─────────────────────────────────────────────────

  Reconciliation Analysis

  ✅ Fully Implemented (No Changes Needed)
  ┌────────────────────────────────────┬──────────────────────────────────────────────┐
  │              Planned               │                 Implemented                  │
  ├────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Two nested wrappers in Shell       │ ✅ Both AgentsShell and StoryShell have this │
  ├────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Page + Cards dropdowns in Header   │ ✅ Both headers have dual selectors          │
  ├────────────────────────────────────┼──────────────────────────────────────────────┤
  │ Dual state with nullish coalescing │ ✅ Implemented with localStorage persistence │
  ├────────────────────────────────────┼──────────────────────────────────────────────┤
  │ tokens: PresentationTokens type    │ ✅ Using this in all theme definitions       │
  ├────────────────────────────────────┼──────────────────────────────────────────────┤
  │ CSS variable cascade mechanism     │ ✅ Working as designed                       │
  └────────────────────────────────────┴──────────────────────────────────────────────┘
  🔄 Evolved Beyond Plan (Document Needs Update)
  Plan Says: Single AMBIENT_THEMES array for both dropdowns
  Reality: Split into PAGE_THEMES + CARD_THEMES
  Action Needed: Update plan to reflect this refinement
  ────────────────────────────────────────
  Plan Says: AgentsShell/themes.ts location
  Reality: Common/Themes/ with multiple files
  Action Needed: Update plan with new file structure
  ────────────────────────────────────────
  Plan Says: getThemeStyle() single function
  Reality: getPageThemeStyle() + getCardThemeStyle()
  Action Needed: Update plan with actual function names
  📋 Backend Contracts (Ready to Implement)

  The backend section looks good and compatible with our frontend:

  # This model aligns with our frontend PresentationTokens
  class Theme(SQLModel, table=True):
      id: UUID
      name: str
      tokens: dict  # JSON column - maps to PresentationTokens
      scope: Literal["system", "personal"]

  One consideration: The plan has a single Theme table, but our frontend now distinguishes page vs cards
  themes. You have options:

  1. Single table with theme_type column:
  theme_type: Literal["page", "cards", "ambient"]
  2. Single table, let frontend filter:
    - Page themes = themes that include --background
    - Cards themes = themes that don't include --background
  3. Keep as-is:
    - All themes can be used for either purpose
    - Frontend just knows not to use cards themes for page layer

  🔧 Suggested Plan Updates

  Would you like me to update the plan document to reflect:

  1. File structure change: Common/Themes/ with page_themes.ts, card_themes.ts, types.ts, resolve.ts
  2. Split theme arrays: Explain why PAGE_THEMES includes --background and CARD_THEMES excludes it
  3. localStorage implementation: Document the current persistence pattern as a stepping stone to backend
  4. Story parity: Note that Story now follows the same architecture as Agents
  5. Backend model consideration: Add note about theme_type column or filtering strategy

## Goal

Add a **Page-level theme layer** to the AgentsShell, proving the full 4-layer CSS variable cascade:

```
Application (Dark) → Page (Oatmeal) → Cards (Warm Sand) → Individual Card (Neon)
```

This iteration proves the cascade mechanism works. User preference persistence comes later.

---

## Design Principles Alignment

This design adheres to the established presentation-as-data principles from `Presentation/REFERENCE.md`:

1. **Presentation is data, not style.** — Themes are data objects with `tokens: PresentationTokens`, ready for database migration.
2. **Components are unmodified.** — Only wrapper divs with CSS variables are added. No shadcn component changes.
3. **Specificity is the composition model.** — Nested wrapper divs; CSS custom property inheritance means inner wins. No `!important`, no hacks.
4. **Partial override is the default.** — Each layer specifies only what it changes. Unspecified variables fall through.
5. **Variant scaling is a component concern.** — Not affected; AgentCard continues to handle density variants.
6. **Decoration hints are interpreted, not literal.** — Not affected; themes don't carry decoration hints.

---

## Architecture

### CSS Variable Cascade

```
:root / .dark (Application theme - index.css)
└── Page Theme Wrapper (div with page theme tokens)
    ├── AgentsHeader (inside page theme scope)
    └── Cards Theme Wrapper (div with cards theme tokens)
        └── AgentsLayout
            └── AgentCard Wrapper (individual presentation tokens)
                └── <Card> (reads CSS variables via Tailwind utilities)
```

Each nested wrapper's inline styles set CSS custom properties. Descendants inherit from the nearest ancestor that defines each variable.

### Component Structure

```
AgentsShell
├── Page Theme Wrapper (outermost - affects header + content)
│   ├── AgentsHeader
│   │   ├── Page Theme Dropdown (new)
│   │   ├── Cards Theme Dropdown (renamed from existing)
│   │   ├── Layout Toggle (unchanged)
│   │   └── Create Actions (unchanged)
│   └── Cards Theme Wrapper (nested - overrides page for card areas)
│       └── AgentsLayout
│           └── Panels → AgentCards
```

---

## Implementation Details

### 1. Type Refactoring (`themes.ts`)

**Before:**
```typescript
export interface AmbientTheme {
  id: string
  name: string
  description?: string
  style: React.CSSProperties
}
```

**After:**
```typescript
import type { PresentationTokens } from "../types"
import { presentationToStyle } from "../resolve"

export interface AmbientTheme {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens  // Unified with AgentPresentation.tokens
}

/** Convert theme tokens to inline style for wrapper div */
export function getThemeStyle(theme: AmbientTheme): React.CSSProperties | undefined {
  return presentationToStyle(theme.tokens)
}
```

**Theme definitions migrate from `style:` to `tokens:`** — same values, different property name. Mechanical change.

### 2. Shell Changes (`AgentsShell.tsx`)

**Props expand:**
```typescript
export interface AgentsShellProps {
  title: string
  panels: PanelConfig[]
  pageThemeId: string           // New
  cardsThemeId: string          // Renamed from selectedThemeId
  onPageThemeChange: (themeId: string) => void   // New
  onCardsThemeChange: (themeId: string) => void  // Renamed
  className?: string
}
```

**Two nested wrappers:**
```tsx
function AgentsShell({ pageThemeId, cardsThemeId, ... }: AgentsShellProps) {
  const pageTheme = getThemeById(pageThemeId)
  const cardsTheme = getThemeById(cardsThemeId)

  return (
    <div style={getThemeStyle(pageTheme)} className={cn("flex flex-col h-full", className)}>
      <AgentsHeader
        pageThemeId={pageThemeId}
        cardsThemeId={cardsThemeId}
        onPageThemeChange={onPageThemeChange}
        onCardsThemeChange={onCardsThemeChange}
        {...headerProps}
      />
      <div style={getThemeStyle(cardsTheme)} className="flex-1 min-h-0">
        <AgentsLayout panels={panels} mode={layoutMode} />
      </div>
    </div>
  )
}
```

### 3. Header Changes (`AgentsHeader.tsx`)

**Props expand:**
```typescript
export interface AgentsHeaderProps {
  title: string
  pageThemeId: string
  cardsThemeId: string
  onPageThemeChange: (themeId: string) => void
  onCardsThemeChange: (themeId: string) => void
  layoutMode: "panels" | "tabs"
  onLayoutModeChange: (mode: "panels" | "tabs") => void
}
```

**Two dropdowns with labels + tooltips:**
- Page dropdown: "Page: {themeName}" — tooltip: "Theme for page surface"
- Cards dropdown: "Cards: {themeName}" — tooltip: "Ambient theme for cards without presentation"
- Both pull from same `AMBIENT_THEMES` array

### 4. Route Changes (`agents.tsx`)

**Dual state with nullish coalescing:**
```typescript
function AgentsPage() {
  const savedPrefs = null // Future: useUserPagePrefs("agents")

  const [pageThemeId, setPageThemeId] = useState(savedPrefs?.pageTheme ?? "default")
  const [cardsThemeId, setCardsThemeId] = useState(savedPrefs?.cardsTheme ?? "default")

  return (
    <AgentsShell
      title="Agents"
      panels={panels}
      pageThemeId={pageThemeId}
      cardsThemeId={cardsThemeId}
      onPageThemeChange={setPageThemeId}
      onCardsThemeChange={setCardsThemeId}
    />
  )
}
```

---

## File Changes Summary

| File | Change Type | Description |
|------|-------------|-------------|
| `AgentsShell/themes.ts` | Modify | Refactor `AmbientTheme.style` → `tokens: PresentationTokens`, add `getThemeStyle()` |
| `AgentsShell/AgentsShell.tsx` | Modify | Add page theme wrapper, expand props for dual themes |
| `AgentsShell/AgentsHeader.tsx` | Modify | Add page theme dropdown, rename existing to cards dropdown, add tooltips |
| `routes/_layout/agents.tsx` | Modify | Dual theme state with nullish coalescing |
| `AgentsShell/index.ts` | Verify | Ensure exports are correct |

---

## Cascade Proof: Success Criteria

After implementation, demonstrate:

1. **Default state:** Both themes = Default. Page renders with Application theme only.
2. **Page theme only:** Page = Midnight, Cards = Default. Header and content area tinted blue-violet. Cards inherit page theme.
3. **Cards theme only:** Page = Default, Cards = Warm Sand. Header uses Application theme. Card area is warm neutral.
4. **Both themes:** Page = Midnight, Cards = Warm Sand. Header is blue-violet. Card area is warm neutral (overrides page).
5. **Full cascade:** Page = Midnight, Cards = Warm Sand, individual card has Neon presentation. Card shows neon, others show warm sand, header shows midnight.

---

## Future Contracts (Not This Iteration)

Documented for backend integration planning.

### Backend Model (Expected)

```python
class Theme(SQLModel, table=True):
    id: UUID
    name: str
    description: str | None
    tokens: dict  # JSON column storing PresentationTokens shape
    scope: Literal["system", "personal"]
    owner_id: UUID | None  # null for system themes
    created_at: datetime
    updated_at: datetime

class UserPagePreference(SQLModel, table=True):
    id: UUID
    user_id: UUID
    page_key: str  # e.g., "agents", "rooms", "room:{roomId}"
    page_theme_id: UUID | None  # FK to Theme
    cards_theme_id: UUID | None  # FK to Theme
```

### API Endpoints (Expected)

```
GET  /api/themes              → list available themes (system + user's personal)
POST /api/themes              → create personal theme
GET  /api/preferences/{page}  → get user's theme selections for page
PUT  /api/preferences/{page}  → save user's theme selections for page
```

### Client SDK Types (To Be Generated)

```typescript
interface ThemePublic {
  id: string
  name: string
  description?: string
  tokens: PresentationTokens
  scope: "system" | "personal"
}

interface UserPagePreference {
  page_key: string
  page_theme_id?: string
  cards_theme_id?: string
}
```

### Frontend Integration Point

```typescript
// Future replacement in agents.tsx
const { data: prefs } = useUserPagePrefs("agents")
const [pageThemeId, setPageThemeId] = useState(prefs?.page_theme_id ?? "default")
```

---

## Implementation Order

1. **themes.ts** — Refactor type, add `getThemeStyle()`, migrate theme definitions
2. **AgentsShell.tsx** — Add page theme wrapper, expand props
3. **AgentsHeader.tsx** — Add page dropdown, tooltips, rename existing dropdown
4. **agents.tsx** — Dual state with nullish coalescing
5. **Visual testing** — Prove cascade with theme combinations

---

## Risks and Watchpoints

1. **Header theming edge cases.** Header controls (dropdowns, buttons) may look odd with extreme themes. Monitor and adjust if needed.
2. **Theme completeness.** Each theme in `AMBIENT_THEMES` must include full variable surface to avoid invisible text. Existing themes already comply.
3. **Import paths.** `presentationToStyle` imported from `../resolve` — verify relative path after any moves.
4. **Tooltip provider.** Header may need `TooltipProvider` wrapper if not already present in component tree.
