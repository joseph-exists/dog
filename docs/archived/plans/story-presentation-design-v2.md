# Story Presentation System Design (v2)

> **Status:** Working Draft — Focused on Author Experience
> **Purpose:** Define how Authors apply visual themes to Stories and Nodes
> **Scope:** Author-side theming; Viewer preferences deferred

---

## Decisions Made (from v1 discussion)

| Decision | Resolution |
|----------|------------|
| Can Viewers override? | Yes, with Author toggle at Story level. System accessibility exists but integration deferred. |
| Syntax theme precedence | Syntax (Shiki) always wins — furthest down tree takes precedence |
| Forms | Deferred — solve complex components first, forms follow |
| Accessibility responsibility | System handles it, not Author. Viewer overrides apply outside story. |
| Preview capability | Exists in StoryEditor/StoryPreview panels |
| Node types | Type-specific schemas exist. `ContentFormat='unknown'` for multi-type. Frontend registries supported. |

---

## Part 1: What Already Exists

### 1.1 Story Model (has presentation)

```typescript
// From @/client/types.gen — ALREADY EXISTS
export type StoryPublic = {
  title: string
  content_format?: ContentFormat | null
  description?: string | null
  is_published: boolean
  story_type?: string | null           // ← can influence default theme
  presentation?: {                      // ← ALREADY EXISTS
    [key: string]: unknown
  } | null
  id: string
  owner_id: string
  // ...
}
```

**Implication:** We can store Story-level presentation today. The question is: what shape should that object have?

### 1.2 StoryNode Model (needs presentation)

```typescript
// From @/client/types.gen — NO presentation field yet
export type StoryNodePublic = {
  title: string
  content?: string
  content_format?: ContentFormat | null
  node_type?: string | null            // ← can influence default theme
  is_start_node?: boolean
  is_end_node?: boolean
  id: string
  story_id: string
  // ... NO presentation field
}
```

**Implication:** Need to add `presentation` field to StoryNode model for per-node overrides.

### 1.3 Theme Binding System (exists)

```typescript
// Theme slots available
export type ThemeSlot = 'page' | 'cards' | 'syntax' | 'motion'

// Binding types
export type BindingType = 'user_pref' | 'authored'

// Context key structure (from existing system)
// "page:story/panel:debug"
// "story:{story_id}"
// "story:{story_id}/node:{node_id}"
```

**Implication:** We can use `authored` bindings with `story:` and `node:` context keys.

---

## Part 2: The Cascade Order Question

You asked for help understanding the cascade options. Let me walk through a concrete example.

### The Scenario

**Story:** "Learn Git Basics"
**Author:** Has set a "Forest" theme (dark green) for the story
**Node A:** "Introduction" — no override, uses story theme
**Node B:** "Code Example" — Author overrides with "Midnight" theme (blue-violet)
**Viewer:** Maria, who has high-contrast mode enabled in her preferences

### Option A: `Story → Node → Viewer` (Author-first)

```
Resolution order:
1. System defaults           → base styling
2. Story presentation        → Forest green surfaces
3. Node B presentation       → Midnight blue overrides Forest
4. Viewer preferences        → Maria's high-contrast applied LAST

Result: Maria sees high-contrast version of Midnight theme on Node B
```

**Characteristic:** Author's intent is the foundation, but Viewer accessibility can override.

### Option B: `Viewer → Story → Node` (Viewer-first)

```
Resolution order:
1. System defaults           → base styling
2. Viewer preferences        → Maria's high-contrast FIRST
3. Story presentation        → Forest green (may be blocked by viewer prefs)
4. Node B presentation       → Midnight blue (may be blocked by viewer prefs)

Result: Maria sees her high-contrast theme; Author's Forest/Midnight are ignored
```

**Characteristic:** Viewer's preferences dominate; Author's themes are suggestions only.

### Option C: `Story → Node`, Viewer as post-processing (Hybrid)

```
Resolution order:
1. System defaults           → base styling
2. Story presentation        → Forest green surfaces
3. Node B presentation       → Midnight blue overrides Forest
4. Viewer post-processing    → Specific adjustments ONLY (font-size, contrast boost)

Result: Maria sees Midnight theme with larger fonts and boosted contrast ratios
```

**Characteristic:** Author's visual design preserved; Viewer can adjust specific accessibility properties.

### Clarifying "Viewer"

| Term | Meaning |
|------|---------|
| **Viewer (person)** | Maria, a user reading/playing the story |
| **Viewer (component)** | StoryPlayer component that renders the story |
| **Viewer preferences** | Maria's saved settings (font size, contrast, animations off) |
| **Author-as-viewer** | The Author previewing their own story in StoryEditor |

When Author previews in StoryEditor, they see the Author cascade (Story → Node) without Viewer preferences applied — unless they toggle a "Preview as Viewer" mode.

### Recommendation

Based on your response that accessibility is system-handled and Author has a toggle:

```
Cascade: Story → Node → Viewer (if Author allows)

Where:
- Author sets `allow_viewer_override: boolean` on Story
- If true: Viewer preferences can adjust specific tokens (accessibility subset)
- If false: Author's design is canonical, system accessibility applies separately
```

---

## Part 3: Targeted Questions

### Q1: What is the shape of `story.presentation`?

**Context:** Story already has `presentation: { [key: string]: unknown }`. We need to define the structure.

**Proposed shape:**

```typescript
interface StoryPresentation {
  // Theme slot bindings (references to Theme entities)
  page_theme_id?: string      // UUID of page theme
  card_theme_id?: string      // UUID of card theme
  syntax_theme_id?: string    // UUID of syntax theme
  motion_theme_id?: string    // UUID of motion theme

  // Direct token overrides (inline, no theme reference)
  tokens?: {
    [key: string]: unknown    // e.g., "--agent-accent": "oklch(0.6 0.15 155)"
  }

  // Author control
  allow_viewer_override?: boolean  // default: true? false?

  // Node-type defaults (optional)
  node_type_themes?: {
    [node_type: string]: {
      card_theme_id?: string
      syntax_theme_id?: string
      // ...
    }
  }
}
```

**Question for you:**
- Should `allow_viewer_override` default to true (accessible by default) or false (Author vision by default)?
- Do we want `node_type_themes` at Story level, or handle that via context key bindings?

---

### Q2: What is the shape of `node.presentation`?

**Context:** StoryNode doesn't have presentation yet. When we add it, what shape?

**Proposed shape:**

```typescript
interface NodePresentation {
  // Override specific slots
  card_theme_id?: string
  syntax_theme_id?: string
  motion_theme_id?: string

  // Direct token overrides
  tokens?: {
    [key: string]: unknown
  }

  // Typography/style hint
  decoration_hint?: 'warm' | 'neon' | 'precise' | 'organic' | 'brutalist' | 'ethereal'
}
```

**Question for you:**
- Should nodes inherit `page_theme` from Story, or can a node override the page background too?
- The `decoration_hint` exists in Agent presentation — do we want the same vocabulary for Stories?

---

### Q3: How do content blocks within a Node get themed?

**Context:** Your example Node B:
```
b: secondary node with three parts:
    a text block (using font, highlights, outlines and an image background)
    a code block (using a different font, shiki hints, etc)
    an interactive text entry field with an output window
```

**Current approach for code:** Shiki handles syntax theme at render time, always wins.

**Question for you:**
When a single Node contains multiple content types (text + code + interactive), how should the Author specify which themes apply to which parts?

Options:
1. **Node-level only** — One theme per node, content types inherit
2. **Content-block metadata** — Each block in the node content has optional presentation hints
3. **ContentFormat-based defaults** — `content_format` determines which theme slots apply

---

### Q4: Do we use ThemeBinding for Story/Node, or inline presentation?

**Context:** Two patterns exist:

**Pattern A: Inline presentation (like Agents)**
```typescript
story.presentation = {
  card_theme_id: "uuid",
  tokens: { "--agent-accent": "oklch(...)" }
}
```

**Pattern B: ThemeBinding with context keys**
```typescript
// Binding record
{
  binding_type: "authored",
  owner_id: story.id,
  context_key: "story:{story_id}",
  slot: "cards",
  theme_id: "uuid"
}
```

**Trade-offs:**

| Aspect | Inline | Binding |
|--------|--------|---------|
| Simplicity | ✓ One place to look | Requires join/lookup |
| Flexibility | Limited | Rich context patterns |
| Viewer override | Custom logic | Built-in resolution |
| Existing code | Agent pattern | Theme system pattern |

**Question for you:**
- Pattern A is simpler and mirrors Agents
- Pattern B leverages the full binding system with context keys
- Or hybrid: inline for Author's base, bindings for Viewer preferences?

---

### Q5: What's the context key grammar for Stories?

**Context:** Existing system uses patterns like `"page:story/panel:debug"`.

**Proposed for Stories:**

```
story:{story_id}                       # Story-level
story:{story_id}/node:{node_id}        # Specific node
story:{story_id}/node:*                # All nodes in story
story:{story_id}/node_type:{type}      # All nodes of type in story
story:*/node_type:code                 # All code nodes globally
```

**Question for you:**
- Does this grammar feel right?
- Should `node_type` be part of context key or handled differently?

---

## Part 4: Content Type Mapping

You noted we should map content types to existing types/schemas. Here's a starter:

| Content Type | ContentFormat Value | Primary Theme Slot | Notes |
|--------------|--------------------|--------------------|-------|
| Narrative text | `markdown`, `html` | card | Typography tokens |
| Code snippet | `code` | syntax | Shiki theme |
| Directory tree | `code` (tree syntax) | syntax | Shiki or custom |
| Interactive CLI | `unknown` (custom) | card + motion | Custom renderer |
| HTML Form | `html` | card | Inherits from card theme |
| State machine | `unknown` (custom) | card + motion | Custom renderer |
| Media | `unknown` (custom) | card | Container styling |

**Question for you:**
- Is `ContentFormat` the right discriminator, or do we need `node_type` as well?
- For custom renderers (CLI, state machine), where do their presentation schemas live?

---

## Part 5: Proposed Implementation Sequence

Based on what exists and what's deferred:

### Phase 1: Story-Level Theming (use existing field)

1. Define `StoryPresentation` TypeScript interface
2. Add theme selectors to Story settings panel
3. StoryPlayer reads `story.presentation` and applies CSS variables
4. Author toggle for `allow_viewer_override`

**No backend changes needed** — `presentation` field already exists.

### Phase 2: Node-Level Overrides

1. Add `presentation` field to `StoryNode` model (backend migration)
2. Add theme override UI to NodeEditor
3. Cascade resolution: Story → Node
4. Update StoryPlayer to resolve per-node

### Phase 3: Content-Type Specifics

1. Syntax theme integration (Shiki config in presentation)
2. Custom renderer presentation schemas (CLI, state machine)
3. ContentFormat-based defaults

### Phase 4: Viewer Preferences (deferred per your notes)

---

## Summary: What We Need to Decide

| # | Question | Options | Impact |
|---|----------|---------|--------|
| 1 | `allow_viewer_override` default | true / false | Accessibility vs authorial control |
| 2 | Node-type defaults location | Story.presentation / context bindings | Complexity |
| 3 | Page theme at Node level | Yes / No | Can nodes change background? |
| 4 | Multi-content-type theming | Node-level / block-level / ContentFormat | Granularity |
| 5 | Storage pattern | Inline / Binding / Hybrid | Integration approach |
| 6 | Context key grammar | Proposed / Alternative | Binding system design |
| 7 | ContentFormat vs node_type | Which is primary discriminator | Schema design |

---

## Next Steps

Once you've reviewed:

1. **Answer Q1-Q5** above (or tell me to propose defaults)
2. **Confirm Phase 1 scope** — can we start with Story-level only?
3. **Pick a complex content type** to design first (you mentioned CLI or state machine)

Then I can produce:
- Technical spec for `StoryPresentation` interface
- UI component requirements for Story settings
- StoryPlayer integration approach
