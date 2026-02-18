# Agent Card Presentation Guide

A user guide explaining how to customize the appearance of Agent cards in the application, from page-wide defaults down to individual agent styling.

---

## Understanding the Theme Cascade

Agent cards can be styled at multiple levels, with more specific settings overriding general ones:

```
Page Cards Theme (broadest)
    ↓
Agent Type Defaults (advisor, creative, analyst...)
    ↓
Individual Agent Presentation (most specific)
```

Each level adds or overrides visual properties from the level above. This lets you set sensible defaults while still customizing individual agents.

---

## Level 1: Page-Wide Cards Theme

### What It Controls

The Cards theme affects **all card-based content** on a page, including:
- Agent cards on the Agents listing page
- Agent cards in sidebars and panels
- Any other card components that inherit the theme

### How to Apply

1. Navigate to **Settings** → **Themes** tab
2. In the **Card Themes** section, browse available themes
3. Click a theme to preview it
4. Use the **Set as Default** option to make it your default cards theme

Alternatively, some pages offer a theme selector in the page header or toolbar:
- Look for a palette icon or "Theme" dropdown
- Select from available card themes
- Your choice is saved as your preference for that page context

### What Changes

When you apply a Cards theme, these visual properties may change:
- Card background color
- Text colors (titles, descriptions, muted text)
- Border colors and styles
- General accent colors for interactive elements

### Example Themes

| Theme | Description |
|-------|-------------|
| **Upstream** | Inherits from page theme (default) |
| **Midnight** | Deep blue-violet dark surface |
| **Warm Sand** | Warm neutral light surface |
| **Forest** | Dark green surface |
| **Cool Ocean** | Cool blue-tinted light surface |
| **Slate** | Cool neutral dark surface |

---

## Level 2: Agent Type Defaults

### What It Controls

Each agent has a **type** that determines its role and default visual identity:

| Agent Type | Role | Default Color | Default Icon |
|------------|------|---------------|--------------|
| **Advisor** | Guidance and recommendations | Green | 🧭 |
| **Creative** | Content generation and ideation | Magenta | 🎨 |
| **Analyst** | Data analysis and insights | Blue | 📊 |
| **Guardian** | Safety, moderation, oversight | Orange | 🛡️ |
| **Oracle** | Knowledge and predictions | Purple | 🔮 |
| **Engineer** | Technical problem-solving | Yellow | ⚙️ |

### How Type Defaults Apply

When you create an agent and select a type:
- The agent automatically receives that type's **accent color**
- The accent color appears in the card's top strip and status badge
- The type's **emoji** appears as the avatar (unless you customize it)
- These defaults apply even without any custom presentation settings

### How to Set Agent Type

1. Open an agent for editing (click on the agent card or use the edit button)
2. In **Section 2: Agent Identity**, find the **Agent Type** dropdown
3. Select the appropriate type for your agent's role
4. Save changes

The type influences both the agent's behavior categorization and its visual presentation.

---

## Level 3: Individual Agent Presentation

### What It Controls

Individual presentation settings let you fully customize a specific agent's appearance, overriding both the page theme and type defaults.

### Accessing Presentation Settings

1. Navigate to the **Agents** page
2. Click on an agent to open the edit dialog
3. Expand **Section 6: Presentation**

### Available Customizations

#### Card Theme Selection

Select a pre-built card theme to apply to this specific agent:

1. Open the **Card Theme** dropdown
2. Browse available themes (system themes and any you've created)
3. Select a theme to apply its colors and styling
4. The theme's tokens are copied to this agent's presentation

**Note:** This overrides both the page-level cards theme AND the agent type's default colors.

#### What Theme Tokens Control

| Visual Element | Token | Effect |
|----------------|-------|--------|
| Card background | `--card` | Main card surface color |
| Card text | `--card-foreground` | Title and primary text |
| Descriptions | `--muted-foreground` | Secondary text like descriptions |
| Borders | `--border` | Card outline color |
| Accent strip | `--agent-accent` | Colored bar (top/left/bottom) |
| Status badge | `--agent-accent` | "Active" badge color |
| Avatar background | `--agent-accent` | Avatar circle (when using emoji) |

#### Accent Strip Position

Some themes position the accent color bar differently:
- **Top** (default) — Horizontal strip at card top
- **Left** — Vertical strip on card left edge
- **Bottom** — Horizontal strip at card bottom
- **None** — No accent strip displayed

#### Typography Style (Decoration Hint)

Advanced themes may include a decoration hint that affects typography:

| Style | Effect |
|-------|--------|
| **Brutalist** | Monospace font, uppercase titles, wide letter spacing |
| **Ethereal** | Serif font, italic titles, elegant feel |
| *(default)* | Standard sans-serif typography |

---

## The Override Hierarchy in Practice

### Example Scenario

Let's walk through how themes combine:

1. **You set "Midnight" as your page Cards theme**
   - All agent cards now have a deep blue-violet background
   - Text is light-colored for contrast

2. **You have an Advisor agent (type = advisor)**
   - The card inherits Midnight's background colors
   - BUT the accent strip and badge show the Advisor's green color
   - The avatar displays the 🧭 compass emoji

3. **You apply "Oracle" card theme to that specific agent**
   - The card now uses Oracle theme's mystical green colors
   - This overrides both Midnight AND the Advisor green
   - The agent now has the Oracle's visual identity despite being an Advisor type

### What Wins?

| Property | Determined By |
|----------|---------------|
| Card background | Individual theme > Page theme |
| Card text colors | Individual theme > Page theme |
| Accent color | Individual theme > Agent type > Page theme |
| Avatar emoji | Individual setting > Agent type default |
| Typography | Individual decorationHint > (none) |

---

## Step-by-Step: Customizing Your Agents Page

### Setting a Default Look

1. Go to **Settings** → **Themes**
2. Click the **Card** category tab
3. Find a theme that matches your preference
4. Click **Set as Default** (or use the page-level selector)

Now all agent cards use this baseline appearance.

### Letting Agent Types Shine Through

If you want agent types to be visually distinct:

1. Use **Upstream** as your cards theme (inherits from page)
2. Or choose a neutral theme like **Slate**
3. Agent type colors will now be prominent on each card

### Making a Special Agent Stand Out

For an important agent that should be visually distinct:

1. Click on the agent to edit
2. Go to **Section 6: Presentation**
3. Select a unique card theme (e.g., "Neon" or "Oracle")
4. Optionally customize the avatar emoji
5. Save changes

This agent now has its own visual identity regardless of type.

---

## Creating Custom Themes

If the built-in themes don't meet your needs:

### Via Settings

1. Go to **Settings** → **Themes**
2. Click **Create Theme**
3. Enter a name and description
4. Select **Card** as the category
5. Choose scope:
   - **Personal** — Only you can see and use it
   - **Shared** — Available to all users in your organization
6. Configure the color tokens
7. Click **Create**

Your custom theme now appears in all card theme selectors.

### Color Format

All colors use the `oklch()` format:
- **L** (Lightness): 0 = black, 1 = white
- **C** (Chroma): 0 = gray, 0.3+ = vivid
- **H** (Hue): 0-360 degrees (red=30, yellow=90, green=150, blue=240, purple=300)

Example: `oklch(0.6 0.15 240)` = medium brightness, moderate saturation, blue hue

---

## Quick Reference: Where to Change What

| I want to... | Go to... |
|--------------|----------|
| Change all cards on a page | Page theme selector or Settings → Themes |
| Set my default card look | Settings → Themes → Card → Set as Default |
| Change an agent's type (and default color) | Edit Agent → Section 2: Agent Identity |
| Customize one agent's appearance | Edit Agent → Section 6: Presentation |
| Create a reusable custom theme | Settings → Themes → Create Theme |
| Remove custom styling from an agent | Edit Agent → Presentation → Select "Upstream" theme |

---

## Visual Elements Reference

### Agent Card Anatomy

```
┌─────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓ ACCENT STRIP ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  ← --agent-accent
├─────────────────────────────────────────┤
│                                         │
│  ┌────┐  Agent Name      [Active]       │  ← Title + Status Badge
│  │ 🧭 │  @agent-slug                    │  ← Avatar + Slug
│  └────┘  Description text goes here     │  ← --muted-foreground
│          and can wrap to multiple...    │
│                                         │
│  [System] [Always Active] [model-name]  │  ← Badges
│                                         │
└─────────────────────────────────────────┘
     ↑ --card (background)    ↑ --border
```

### Color Relationships

For readable cards, ensure sufficient contrast:
- `--card` and `--card-foreground` need high contrast
- `--muted-foreground` should be visible but subdued
- `--agent-accent` should stand out from `--card`
- `--agent-accent-foreground` must be readable on `--agent-accent`

---

## Tips & Best Practices

### For Consistency
- Use the page-level cards theme as your baseline
- Let agent types provide visual categorization
- Only customize individual agents when they need to stand out

### For Accessibility
- Ensure text contrast meets accessibility standards
- Avoid very low lightness values for text on dark backgrounds
- Test themes in both light and dark mode if applicable

### For Organization
- Use **Shared** scope for team-wide themes
- Use **Personal** scope for experimental themes
- Name themes descriptively (e.g., "Sales Team Blue" not "Theme 1")

---

## Troubleshooting

### "My theme changes aren't showing"
- Refresh the page after saving
- Check that you saved the agent after selecting a theme
- Verify the theme was applied (check presentation section)

### "The accent color is wrong"
- Individual presentation overrides agent type color
- To restore type color: remove the custom theme or select "Upstream"

### "Cards look different than expected"
- Check if you have a page-level theme set
- The cascade applies: Page → Type → Individual
- More specific settings always win

---

## Related Documentation

- [Card Themes Technical Reference](./CARD-THEMES-REFERENCE.md) — For engineers and API usage
- [Theme Cascade Architecture](../../../Common/Themes/CASCADING-THEMES.md) — System design details
