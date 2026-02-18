# Card Themes Reference

A guide for engineers and users on adding and applying themes to Agent cards through the API, UI, or direct database operations.

## Overview

Card themes control the visual presentation of Agent cards. Themes are stored in the `theme` table and applied via two mechanisms:

1. **Agent Presentation Data** - Tokens stored directly in `agent.presentation.tokens`
2. **Theme Bindings** - User preferences or entity-authored bindings that resolve themes by context

---

## Theme Token Reference

Card themes support these CSS variable tokens (all colors in `oklch()` format):

| Token | Description | Example |
|-------|-------------|---------|
| `--card` | Card background color | `oklch(0.18 0.03 280)` |
| `--card-foreground` | Card text color | `oklch(0.92 0.01 280)` |
| `--foreground` | General text color | `oklch(0.90 0.01 280)` |
| `--border` | Border color | `oklch(0.28 0.03 280)` |
| `--muted` | Muted background | `oklch(0.22 0.03 280)` |
| `--muted-foreground` | Muted text color | `oklch(0.62 0.02 280)` |
| `--secondary` | Secondary background | `oklch(0.25 0.04 280)` |
| `--secondary-foreground` | Secondary text | `oklch(0.88 0.01 280)` |
| `--accent` | Accent background | `oklch(0.30 0.04 280)` |
| `--accent-foreground` | Accent text | `oklch(0.92 0.01 280)` |
| `--agent-accent` | Agent brand color | `oklch(0.6 0.15 150)` |
| `--agent-accent-foreground` | Text on accent | `oklch(1 0 0)` |
| `--agent-card-shadow` | Box shadow | `0 4px 12px rgba(0,0,0,0.15)` |
| `--agent-card-radius` | Border radius | `1rem` |
| `--agent-accent-position` | Accent strip position | `top`, `left`, `bottom`, `none` |
| `--agent-accent-width` | Accent strip width | `4px` |

---

## Method 1: Direct Agent Presentation (Recommended for Individual Agents)

Store theme tokens directly in the agent's `presentation` JSON field.

### Via API

```bash
# Update agent with presentation tokens
curl -X PATCH /api/v1/user-agent-configs/{agent_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "presentation": {
      "card_theme_id": "b0000000-0000-0000-0000-000000000007",
      "tokens": {
        "--card": "oklch(0.12 0.05 150)",
        "--card-foreground": "oklch(0.95 0.02 150)",
        "--border": "oklch(0.22 0.04 150)",
        "--agent-accent": "oklch(0.6 0.15 150)",
        "--agent-accent-foreground": "oklch(1 0 0)"
      },
      "avatar": {
        "emoji": "🔮"
      },
      "decorationHint": "ethereal"
    }
  }'
```

### Via Frontend Hook

```typescript
import { useUpdateUserAgentConfig } from "@/hooks/useUserAgentConfigs"

const { mutate: updateAgent } = useUpdateUserAgentConfig()

// Apply a card theme to an agent
updateAgent({
  id: agentId,
  presentation: {
    card_theme_id: selectedTheme.id,
    tokens: selectedTheme.tokens,
    avatar: { emoji: "🧭" },
    decorationHint: "warm"
  }
})
```

### Via UI

1. Navigate to **Agents** page
2. Click on an agent to open edit dialog
3. Expand **Section 6: Presentation**
4. Select a card theme from the dropdown
5. Save changes

---

## Method 2: Theme Registry (For Creating Reusable Themes)

### Create a New Card Theme via API

```bash
# Create a personal card theme
curl -X POST /api/v1/themes/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Midnight Ocean",
    "description": "Deep blue card with cyan accents",
    "category": "card",
    "scope": "personal",
    "tokens": {
      "--card": "oklch(0.15 0.04 240)",
      "--card-foreground": "oklch(0.95 0.01 240)",
      "--border": "oklch(0.25 0.03 240)",
      "--muted": "oklch(0.20 0.03 240)",
      "--muted-foreground": "oklch(0.65 0.02 240)",
      "--agent-accent": "oklch(0.65 0.18 200)",
      "--agent-accent-foreground": "oklch(1 0 0)"
    }
  }'
```

### Create Theme via Frontend Hook

```typescript
import { useThemeManagement } from "@/hooks/useThemeRegistry"

const { createTheme, isCreating } = useThemeManagement()

await createTheme({
  name: "Forest Glow",
  description: "Dark green with warm accent",
  category: "card",
  scope: "shared",  // "personal" | "shared"
  tokens: {
    "--card": "oklch(0.14 0.04 155)",
    "--card-foreground": "oklch(0.92 0.02 155)",
    "--agent-accent": "oklch(0.65 0.18 85)",
    "--agent-accent-foreground": "oklch(0.15 0 0)"
  }
})
```

### Create Theme via UI

1. Navigate to **Settings** → **Themes** tab
2. Click **Create Theme**
3. Fill in name, description
4. Select category: **Card**
5. Select scope: **Personal** or **Shared**
6. Configure color tokens
7. Click **Create**

---

## Method 3: Theme Bindings (For Context-Based Defaults)

Theme bindings let users set default themes for specific contexts.

### Set User Preference Binding via API

```bash
# Set default card theme for all agent views
curl -X PUT /api/v1/theme-bindings/user \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_id": "b0000000-0000-0000-0000-000000000004",
    "context_key": "page:agents",
    "slot": "cards"
  }'
```

### Set Binding via Frontend Hook

```typescript
import { useUserThemeBindings } from "@/hooks/useThemeRegistry"

const { setBinding } = useUserThemeBindings()

// Set card theme for a specific page context
await setBinding({
  themeId: theme.id,
  contextKey: "page:agents",
  slot: "cards"
})
```

### Context Key Examples

| Context Key | Description |
|-------------|-------------|
| `*` | Global fallback |
| `page:agents` | Agents listing page |
| `page:story` | Story view page |
| `page:room` | Chat room page |
| `page:agents/panel:sidebar` | Sidebar in agents page |

---

## Method 4: Direct Database (For System Themes)

System themes can only be added via database operations.

### Insert System Card Theme

```sql
INSERT INTO theme (id, name, description, category, scope, owner_id, is_system, tokens, created_at, updated_at)
VALUES (
  'b0000000-0000-0000-0000-000000000099',
  'Neon Cyberpunk',
  'High contrast neon theme',
  'card',
  'system',
  NULL,
  true,
  '{
    "--card": "oklch(0.08 0.02 300)",
    "--card-foreground": "oklch(0.95 0.01 300)",
    "--border": "oklch(0.35 0.2 320)",
    "--agent-accent": "oklch(0.7 0.25 320)",
    "--agent-accent-foreground": "oklch(0.1 0 0)",
    "--agent-card-shadow": "0 0 20px oklch(0.5 0.2 320 / 0.3)"
  }',
  NOW(),
  NOW()
);
```

### Seed File Location

System themes are seeded from: `backend/app/alembic/seed_themes_full.sql`

---

## Fetching Available Themes

### List Available Card Themes via API

```bash
curl -X GET "/api/v1/themes/available?category=card" \
  -H "Authorization: Bearer $TOKEN"
```

### Via Frontend Hook

```typescript
import { useAvailableThemes } from "@/hooks/useThemeRegistry"

function ThemePicker() {
  const { themes, isLoading } = useAvailableThemes("card")

  return (
    <select>
      {themes.map(theme => (
        <option key={theme.id} value={theme.id}>
          {theme.name}
        </option>
      ))}
    </select>
  )
}
```

---

## Theme Resolution Order

When rendering an Agent card, themes resolve in this order (highest priority first):

1. **Instance Presentation** - `agent.presentation.tokens` (if set)
2. **Type Defaults** - Built-in defaults for agent types (advisor, creative, etc.)
3. **CSS Variable Inheritance** - Page-level theme variables

```typescript
// Resolution in AgentCard.tsx
const resolved = resolveAgentPresentation(
  agentType,           // e.g., "advisor" → green accent
  agent.presentation   // Instance overrides
)
```

---

## Type Default Presentations

Built-in defaults for each agent type (in `resolve.ts`):

| Agent Type | Accent Color | Emoji |
|------------|--------------|-------|
| `advisor` | Green `oklch(0.6 0.15 155)` | 🧭 |
| `creative` | Magenta `oklch(0.6 0.2 310)` | 🎨 |
| `analyst` | Blue `oklch(0.6 0.15 240)` | 📊 |
| `guardian` | Orange `oklch(0.65 0.18 55)` | 🛡️ |
| `oracle` | Purple `oklch(0.55 0.18 290)` | 🔮 |
| `engineer` | Yellow `oklch(0.8 0.16 85)` | ⚙️ |

---

## Decoration Hints

The `decorationHint` field affects typography and styling:

| Hint | Effect |
|------|--------|
| `brutalist` | Monospace font, uppercase titles, wide tracking |
| `ethereal` | Serif font, italic titles |
| `warm` | (Future: warmer color adjustments) |
| `neon` | (Future: glow effects) |
| `precise` | (Future: sharp edges) |
| `organic` | (Future: rounded, soft) |

---

## Complete Example: Custom Themed Agent

```typescript
// 1. Create a custom theme
const theme = await createTheme({
  name: "Royal Purple",
  category: "card",
  scope: "personal",
  tokens: {
    "--card": "oklch(0.18 0.05 290)",
    "--card-foreground": "oklch(0.95 0.02 290)",
    "--border": "oklch(0.28 0.04 290)",
    "--muted-foreground": "oklch(0.65 0.03 290)",
    "--agent-accent": "oklch(0.55 0.2 290)",
    "--agent-accent-foreground": "oklch(1 0 0)",
    "--agent-card-radius": "1.5rem",
    "--agent-accent-position": "left",
    "--agent-accent-width": "4px"
  }
})

// 2. Apply to an agent
await updateAgent({
  id: agentId,
  presentation: {
    card_theme_id: theme.id,
    tokens: theme.tokens,
    avatar: { emoji: "👑", backgroundColor: "oklch(0.55 0.2 290)" },
    decorationHint: "ethereal"
  }
})
```

---

## Troubleshooting

### Theme not applying?

1. Check that `presentation.tokens` contains the theme tokens (not just `card_theme_id`)
2. Verify the agent has `presentationEnabled` (automatic if presentation or agent_type exists)
3. Check browser dev tools for CSS variable values on the wrapper div

### Colors look wrong?

1. Ensure all colors use `oklch()` format
2. Check lightness values (0-1 scale, not 0-100)
3. Verify chroma values are reasonable (0.1-0.3 for saturated colors)

### Accent strip not showing?

1. Check `--agent-accent` token is defined
2. Verify `--agent-accent-position` is not `"none"`
3. Ensure `presentationEnabled` is true

---

## Related Files

- **Types**: `src/components/Agents/types.ts`
- **Resolution**: `src/components/Agents/resolve.ts`
- **Card Component**: `src/components/Agents/Display/AgentCard.tsx`
- **Theme Hooks**: `src/hooks/useThemeRegistry.ts`
- **Theme Service**: `src/services/themeService.ts`
- **Seed Data**: `backend/app/alembic/seed_themes_full.sql`
