# Theme Cascade Reference

> Audience: engineers implementing or migrating UI surfaces to the shared cascade model.
> Canonical architecture: `frontend/src/components/Common/Themes/CASCADING-THEMES.md`

## Purpose

Use this reference when you need predictable theming across page shells, card surfaces, and per-entity presentation data.

## Cascade Model

The project uses a 4-layer CSS variable cascade:

1. Application defaults (`:root` / dark mode)
2. Page theme scope (`getPageThemeStyle`) 
3. Cards theme scope (`getCardThemeStyle`)
4. Instance presentation (`presentationToStyle`)

Nearest scope wins for overlapping CSS variables.

## Source of Truth Files

- `frontend/src/components/Common/Themes/page_themes.ts`
- `frontend/src/components/Common/Themes/card_themes.ts`
- `frontend/src/components/Common/Themes/resolve.ts`
- `frontend/src/components/Common/Themes/types.ts`
- `frontend/src/components/Common/Themes/CASCADING-THEMES.md`

## Required Rules

1. Theme wrappers must be transparent scopes.
- Wrapper elements set CSS variables only.
- Do not add a visual surface class (for example `bg-card`) on the wrapper itself.

2. Page themes own the page surface.
- Page themes should include `--background`.

3. Cards themes must not override the page surface.
- Card themes must exclude `--background`.

4. Presentation data is layered last.
- Per-entity (or per-instance) presentation tokens override upstream page/cards values.

5. Keep tokens CSS-variable-first.
- Use CSS variables as the integration contract, not ad-hoc class branching.

## Minimal Implementation Pattern

```tsx
import { getPageThemeStyle } from "@/components/Common/Themes/page_themes"
import { getCardThemeStyle } from "@/components/Common/Themes/card_themes"
import { presentationToStyle } from "@/components/Common/Themes/resolve"

<div style={getPageThemeStyle(pageTheme)} className="flex h-full flex-col">
  <Header />
  <div style={getCardThemeStyle(cardsTheme)} className="flex-1 min-h-0">
    <div style={presentationToStyle(instancePresentation?.tokens)}>
      <Card />
    </div>
  </div>
</div>
```

## Migration Checklist

1. Replace local/per-feature theme arrays with shared `Common/Themes` exports.
2. Replace generic helpers (for example legacy `getThemeStyle`) with:
- `getPageThemeStyle`
- `getCardThemeStyle`
3. Verify card theme token sets do not include `--background`.
4. Ensure wrappers are transparent scopes.
5. Add/keep tests for cascade precedence:
- page token applies when cards token absent
- cards token overrides page token for card-scoped variables
- instance presentation overrides both

## Common Failure Modes

- Page background unexpectedly changes when selecting a cards theme.
- Cause: cards theme includes `--background`.

- Theme appears to apply only partially.
- Cause: wrapper renders its own visual surface, masking inherited variables.

- Instance-level customization appears ignored.
- Cause: no `presentationToStyle` wrapper at the leaf instance boundary.

## Notes For Demo Surfaces

Demo pages currently use the same page/cards token-scope idea, but may not yet fully consume all presentation metadata across every panel/block capability.

When migrating Demo to full parity with the shared cascade model, prefer:

1. Keep persisted contract shape unchanged (`theme_id`, `presentation_json`).
2. Normalize `presentation_json` into CSS-variable tokens per capability.
3. Apply those tokens at panel/block instance wrappers with `presentationToStyle`.
4. Add parity tests against the same cascade precedence rules listed above.
