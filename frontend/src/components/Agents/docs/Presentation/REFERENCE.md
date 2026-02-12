# Presentation-as-Data: Architecture Reference

> **Location:** `frontend/src/components/Agents/Presentation/`  
> **Status:** Nearing MVP - solid foundations, proven workflow with 'some' dev-only requirements.
> **Last updated:** 2025-02-09


---
## Current Status

Agents is an ontology overload for the sake of our users.  When we reference an AgentCard we don't mean an actual Agent - an actual agent is the composition of multiple elements and the emergent behavior from that composition.

Agents in our system are a composition as well.  We have Agent objects on the frontend.  These Agent objects are composed references to data on the backend - and that data is stored in a postgres table user_agent_config, and managed on the backend with the pydantic & sqlmodel UserAgentConfig object.  We have exported types, client, and schema from that object on the frontend.

The Agent, derived from UserAgentConfig and with data stored in user_agent_config, can be managed by the user through a set of forms. Through these forms, the User will be able to save their objects visual identity - as seen below.  What we have proof of, as working, is that if a developer adds the JSON data for the visual representation to a UserAgentConfig (by saving valid json to presentation.user_agent_config with an API call) that presentation will be shown on the AgentCard.  

What we need to prove in our build out of the agents.tsx page is that Ambient themes (even as inline imports on the page object) can be specified at the Page level, and that they can be used together with AgentCard themes, with appropriate cascades.

With that in mind, we need to build out the agents.tsx page, using the constructs being worked through in this document, and using the structures of compositionality and abstraction in the src/components/Page directory.  The Page directory structure has been proven as an Agents listing capable page in the past, and the Page structure has been applied to Room as the most sophisticated example. 

We should think of this as a net-new Agents Page and Agent Page - we can use the existing page as a template or reference artifact, but if we try to refactor them, we'll box ourselves in.  We will need to satisfy the contracts with other components - which have been written with this in mind, and should be modularized to the degree where this is an effective strategy.

The Full, Compact, and Mini cards and their cascade were all tested and validated in the demo presentation.  At this point, we don't have a place to validate Cards other than Full.  Our Agent Page(s) for individual agents (agent.$agentId.tsx && agent.$slug.tsx) will be where users, and we, can see these visually.

We also need to develop agents.tsx around the concept of the existing ambient theme system.  We have the top-level system in place: Application level themes.  We have the lower level proved with the steel thread (AgentCards currently show their db-driven presentation JSON as visual effects). We can review the src/components/REFERENCE-ONLY-OLD-BROKEN_PresentationDemo.tsx.md - and I can get that working fairly quickly, and ported over to the new AgentCard system as a rapid testing environment.

We will be creating a set of models and tables to store and reference these ambient themes and user selections.  That is already designed, but waiting for this implementation to tell us if we should move forward.  



---

## What This System Does

Objects carry their own visual identity as data, alongside content. An object's warm amber palette is stored in the same record as its name and description. The component renders both — no separate theming system needed.

This coexists with **application defaults**, **user defaults**,and **ambient themes** (page-level visual context set by a page owner). These systems use different mechanisms, have different lifecycles, and compose via CSS specificity: ambient sets the canvas, object presentation overrides it locally.

---

## Core Mechanism

A wrapper `<div>` around each component sets CSS custom properties as inline styles. Shadcn components inside the wrapper read those properties via Tailwind utilities (`bg-card` → `var(--card)`, `text-muted-foreground` → `var(--muted-foreground)`, etc). The components themselves are never modified.

```
┌─ wrapper div ────────────────────────────────┐
│  style="--card: oklch(0.18 0.04 300);        │
│          --card-foreground: oklch(0.92 ...);  │
│          --foreground: oklch(0.92 ...);       │
│          ..."                                 │
│                                               │
│  ┌─ <Card> (shadcn, untouched) ────────────┐ │
│  │  bg-card → reads --card from wrapper     │ │
│  │  text-card-foreground → reads wrapper    │ │
│  │                                          │ │
│  │  ┌─ <Badge variant="outline"> ────────┐ │ │
│  │  │  text-foreground → reads wrapper   │ │ │
│  │  └────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────┘ │
└───────────────────────────────────────────────┘
```

---

## The Complete Variable Surface

### Rule: if you change lightness, you must override the full set.

This is the single most important lesson from building this system. Every ambient theme and every object presentation that changes the surface lightness (light ↔ dark) **must** override all variables that any descendant component might read. A partial override creates invisible text.

**Why it happens:** Tailwind/shadcn components use different variable names depending on their variant. `<Card>` reads `--card`. `<Badge variant="secondary">` reads `--secondary`. `<Badge variant="outline">` reads `--foreground`. If you override `--card` to be dark but leave `--foreground` at its app-level light-mode value, outline badges render dark-on-dark.

### Minimum complete set for any scope that changes surface lightness:

```typescript
// REQUIRED — components will read all of these
"--card"                    // Card, container backgrounds
"--card-foreground"         // Card body text
"--foreground"              // outline badges, inherited text, standalone elements
"--border"                  // Card border, badge borders, dividers
"--muted"                   // Muted backgrounds (model badge, "by Author" badge)
"--muted-foreground"        // Descriptions, slugs, secondary text
"--secondary"               // System scope badge background
"--secondary-foreground"    // System scope badge text
"--accent"                  // Hover states, selected states
"--accent-foreground"       // Text on hover/selected backgrounds
```

### Which components read which variables:

| Variable | Read by |
|---|---|
| `--card`, `--card-foreground` | `<Card>`, any container with `bg-card text-card-foreground` |
| `--foreground` | `<Badge variant="outline">` (scope:personal, all activation badges), compact/mini name text if not explicitly classed |
| `--border` | `<Card>` border, `<Badge>` border, dividers |
| `--muted`, `--muted-foreground` | `<CardDescription>`, slug text, model badge, "by Author" badge, `<AvatarFallback>` default bg |
| `--secondary`, `--secondary-foreground` | `<Badge variant="secondary">` (scope:system) |
| `--accent`, `--accent-foreground` | Hover states (`hover:bg-accent`), selected mini chips |



---

## Two Scoping Levels

### Ambient Theme (page-level)

- **Set by:** Page owner's theme selection
- **Applied as:** CSS variables on a container div wrapping all page content
- **Stored in:** Themes table / theme configuration
- **Overrides:** The full variable set above
- **Purpose:** Sets the canvas for the page

### Object Presentation (instance-level)

- **Set by:** Agent creator when customizing their agent
- **Applied as:** CSS variables on wrapper div around individual component
- **Stored in:** `presentation` field on the agent record, inline with other content
- **Overrides:** Same variable set, but scoped to one component instance
- **Purpose:** Gives the object a visual identity that travels with it

Inline styles (object) have higher specificity than inherited variables (ambient), so object presentation naturally wins. No specificity hacks needed.

---

## Resolution Chain

```
Type defaults → Instance overrides → Merged result
```

```typescript
import { resolveAgentPresentation } from "./resolve"

const resolved = resolveAgentPresentation(
  agent.agentType,    // e.g., "advisor" → green accent, 🧭 emoji
  agent.presentation, // instance overrides, or null
)
```

- If instance has no presentation → type defaults apply
- If instance overrides some tokens → those win, rest fall through to type
- If instance overrides all tokens → fully custom appearance

Merge is shallow per sub-object: `tokens` merged via spread, `avatar` merged via spread, `decorationHint` last-write-wins.

---

## Token Categories

### Applied via CSS variable scoping (wrapper div)

These override shadcn's design tokens. Components read them automatically.

```typescript
interface PresentationTokens {
  // Surface (the full variable set from above)
  "--card"?: string
  "--card-foreground"?: string
  "--foreground"?: string
  "--border"?: string
  "--muted"?: string
  "--muted-foreground"?: string
  "--secondary"?: string
  "--secondary-foreground"?: string
  "--accent"?: string
  "--accent-foreground"?: string

  // Agent accent (used by accent strip, avatar ring)
  "--agent-accent"?: string
  "--agent-accent-foreground"?: string

  // Extended (not in shadcn defaults — component reads explicitly)
  "--agent-card-shadow"?: string
  "--agent-card-radius"?: string
  "--agent-accent-position"?: "top" | "bottom" | "left" | "none"
  "--agent-accent-width"?: string
}
```

### Applied directly (not via CSS variables)

```typescript
interface AvatarPresentation {
  emoji?: string              // Replaces hash-derived initials
  backgroundColor?: string    // Replaces hash-derived color
}

type DecorationHint = "warm" | "neon" | "precise" | "organic" | "brutalist" | "ethereal"
```

The `decorationHint` is an **interpreted signal**, not raw CSS. The component maps it to Tailwind classes:

| Hint | Effect |
|---|---|
| `brutalist` | `font-mono`, title: `uppercase tracking-wide text-[13px]` |
| `ethereal` | `font-serif`, title: `italic font-normal text-[16px]` |
| others | No typographic change (reserved for future) |

This is intentional: the object says "I'm brutalist" and the component decides what that means. The component can adapt the interpretation per variant or viewport without the object knowing.

---

## Variant Scaling

The same presentation data renders differently at each density. Not all tokens are relevant at all sizes.

| Token | Full | Compact | Mini |
|---|---|---|---|
| Surface variables (`--card`, `--foreground`, etc) | ✓ via wrapper | ✓ via wrapper | ✗ |
| `--agent-card-shadow` | ✓ inline on Card | ✗ | ✗ |
| `--agent-card-radius` | ✓ inline on Card | ✗ | ✗ |
| `--agent-accent` color | ✓ accent strip | ✓ left border | ✓ selected tint |
| `--agent-accent-position` | ✓ | ✗ (always left) | ✗ |
| `avatar.emoji` / `backgroundColor` | ✓ | ✓ | ✓ |
| `decorationHint` | ✓ font + title style | ✓ font + title style | ✗ |

Design rationale: compact/mini contexts are tight. Shadows and custom radii would fight with surrounding layout. Accent color and avatar are the minimum identity signal at small scale.

---

## Gotcha: Shadow and Radius on Card

### Problem

Tailwind's `shadow-sm` class sets `--tw-shadow` directly on the `<Card>` element. A CSS custom property set on the wrapper div is inherited, but the Card's own class declaration **overrides the inherited value**. So setting `--tw-shadow` on the wrapper has no effect.

### Solution

Apply `boxShadow` and `borderRadius` as **inline styles directly on the `<Card>` element**, not on the wrapper. Inline styles beat Tailwind classes.

```typescript
// In PresentableCardFull:
const cardInlineStyle: React.CSSProperties = {
  ...(presentationEnabled && resolved.tokens?.["--agent-card-radius"]
    ? { borderRadius: resolved.tokens["--agent-card-radius"] }
    : {}),
  ...(presentationEnabled && resolved.tokens?.["--agent-card-shadow"]
    ? { boxShadow: resolved.tokens["--agent-card-shadow"] }
    : {}),
}

<Card style={Object.keys(cardInlineStyle).length > 0 ? cardInlineStyle : undefined}>
```

### General rule

If a Tailwind class sets the same CSS property you're trying to override via a variable, you must use an inline style on the **same element** that has the class. Variable inheritance from ancestors will lose.

---


### General rule

Never rely on color inheritance across scope boundaries. If a container sets its own background via a scoped variable, it must also set its own foreground.

---

## File Structure

TODO: add file structures

```

```

---

## Adding a New Element with Presentation

TODO: DOCUMENT: add new element

```typescript

```

All color values use **oklch()** format to match the project's design token system in `index.css`.

---

## Adding a New Ambient Theme

```typescript
const myTheme = {
  name: "My Theme",
  style: {
    // MUST include the full variable surface:
    "--card": "...",
    "--card-foreground": "...",
    "--foreground": "...",          // ← don't forget
    "--border": "...",
    "--muted": "...",
    "--muted-foreground": "...",
    "--secondary": "...",
    "--secondary-foreground": "...",
    "--accent": "...",              // ← don't forget
    "--accent-foreground": "...",   // ← don't forget
  } as React.CSSProperties,
}
```

The three most commonly forgotten variables are `--foreground`, `--accent`, and `--accent-foreground`. If you see invisible badge text, check these first.

---

## Extending to New Component Types

The pattern is not agent-specific. Any entity that should carry visual identity can use it:

# TODO: migrate utils, resolv, and hooks from Agents to top level
# TODO: modify Agents imports for above

1. Define a `presentation` field on the entity's data type
(see `UserAgentConfig`)
2. Wrap the component's outermost element with `style={presentationToStyle(resolved.tokens)}`
3. Apply shadow/radius as inline styles on the element that has Tailwind shadow/radius classes
4. Ensure all containers pair `bg-*` with `text-*-foreground`
5. If the entity can have a dark surface on a light page (or vice versa), its presentation must include the full variable set


---

## Design Principles

1. **Presentation is data, not style.** It lives in the database alongside name and description, not in a stylesheet.

2. **Components are unmodified.** Shadcn Card, Badge, Avatar are used as-is. The wrapper div's CSS variables are the only injection point.

3. **Specificity is the composition model.** Ambient themes set inherited variables. Object presentation sets them closer to the component. Inline styles set them on the component itself. CSS specificity rules handle the rest — no cascade layers, no `!important`, no specificity hacks.

4. **Partial override is the default.** An object only specifies what it changes. Everything else falls through to type defaults, then to ambient, then to app-level `:root`. This is `Object.assign` semantics.

5. **Variant scaling is a component concern.** The data doesn't know about full/compact/mini. The component decides which tokens are relevant at each density. Data authors don't need to think about variants.

6. **Decoration hints are interpreted, not literal.** The object says "I'm brutalist." The component decides what that means in each variant, viewport, and context. This keeps the data portable and the component in control.


NOTES: 

"So: no, the migration doesn't break the design. The one thing to lock down is that the presentation JSON column is treated as an opaque blob that round-trips without key transformation. Test that with one agent end-to-end (write presentation JSON to DB, read it back via API, confirm --agent-accent key survives intact) before wiring up the full grid."

