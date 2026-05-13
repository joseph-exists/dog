# SVG Library: Compose Studio, Batch Seed, Gallery Power Features
**Date:** 2026-03-25
**Scope:** Issues from `src/components/Svg/current-svg-library-issues.md`
**Implementation order:** D (Operations + Dialogs) → B (Gallery tagging/filter/sort) → C (Gentle Mode) → A (Gallery UX polish)

---

## Guiding Principles

- **Visibility over magic:** every enqueued job is traceable; users see what Tesser is doing
- **Presets as starting points, never constraints:** family bias pre-fills knobs, nothing is locked
- **Kind to future selves:** inline documentation at every seam between frontend and backend
- **Progressive disclosure:** defaults are usable, depth is reachable

---

## D: Operations Panel + Dialogs

### D1: `svgComposeDomains.ts` (new file)

**Path:** `src/components/Svg/constants/svgComposeDomains.ts`

The authoritative frontend mirror of the Python domain definitions. Opens with a block comment citing:
- `backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md`
- `backend/app/test_scripts/render_things/svg_library_tools.py`
- `backend/app/test_scripts/typer/commands/svgs.py`

**Contents:**

```ts
// PAIRWISE_DOMAINS — mirrors svg_library_tools.PAIRWISE_DOMAINS
// Discrete knob values for scenario generation and the Compose Studio UI.
// § A. Geometry/Base Composition
export const SHAPE_FAMILIES = ["curves", "polygons", "rings", "stripes", "particles"]
export const LAYER_COUNTS = ["1", "2", "4", "6"]
export const DENSITIES = ["sparse", "medium", "dense"]
export const SYMMETRIES = ["none", "radial", "mirror-x", "mirror-y"]
export const VIEWBOXES = ["square(1024)", "landscape(1366x768)", "portrait(768x1366)"]
// § B. Turbulence / Noise
// ... (all 30 knob domains)

export const STYLE_FAMILIES = ["organic", "geometric", "glitch", "minimal", "atmospheric", "diagrammatic"] as const
export type StyleFamily = typeof STYLE_FAMILIES[number]

// Family personality hints for UI display
export const FAMILY_DESCRIPTORS: Record<StyleFamily, string> = {
  organic: "flowing curves, earth tones, natural symmetry",
  geometric: "hard edges, radial order, structured contrast",
  glitch: "neon displacement, global distortion, high chaos",
  minimal: "sparse, monochrome, low blur, quiet",
  atmospheric: "particles, screen blend, low-frequency noise",
  diagrammatic: "stripes, high contrast, multiply blend",
}

// applyFamilyBias — TS port of svg_library_tools._apply_family_bias
// Applies mild family-specific defaults; caller may override any field after.
export function applyFamilyBias(family: StyleFamily, base: KnobState, seed: number): KnobState { ... }

// buildScenarios — simplified random sampling from PAIRWISE_DOMAINS
// NOTE: This is a pragmatic approximation of the Python pairwise planner.
// It does not guarantee pairwise coverage. For exhaustive library population,
// use the CLI: `python -m app.test_scripts.typer svgs seed --count N`
export function buildScenarios(input: {
  count: number
  seed: number
  families: StyleFamily[]
  tier: "pairwise" | "hero" | "safe"
}): KnobState[] { ... }
```

Each knob domain is grouped by reference card section with inline `// §` comments.

---

### D2: Compose Studio Tab (in `SvgOperationsPanel.tsx`)

New `Compose Studio` tab alongside `Combinatorics Studio` and `Asset Editor`.

**Layout (top to bottom):**

#### Family Preset Row
6 compact clickable `Card` tiles. Each shows:
- Family name
- One-line descriptor from `FAMILY_DESCRIPTORS`
- Subtle color accent matching the family's visual character
- Active state highlighted

Clicking applies `applyFamilyBias(family, currentKnobs, seed)` — updates state, locks nothing.
`Randomize` button: re-seeds all knobs from active family with a fresh random seed.

#### Knob Groups — 7 Collapsible Sections
Defaults: Geometry open, all others closed.

Each section header carries:
- Group name
- `(?)` tooltip with one-sentence description
- Reference card section citation in a code comment

| Group | Reference Card Section | Default open |
|---|---|---|
| Geometry | § A | ✓ |
| Turbulence | § B | — |
| Displacement | § C | — |
| Blur & Edge | § D | — |
| Color & Palette | § E | — |
| Blending | § F | — |
| Texture & Motion | § G | — |
| Text Layer | (frontend extension) | — |

**Knob rendering by type:**
- `enum` (short: ≤4 options) → `ToggleGroup`
- `enum` (long: >4 options) → `Select`
- `number` → `Input` with min/max hint text
- `seed` → `Input` + inline `Shuffle` icon button

#### Text Layer Group (8th group)
Toggle off by default. When on:
- Text content `Input`
- Font size `Input` (number)
- Anchor `ToggleGroup`: start / middle / end
- Fill `Input` (hex)
- X position % `Input`, Y position % `Input`

Serialized into `script_input` as `text_layer: { enabled, content, font_size, anchor, fill, x_pct, y_pct }`.

**Component comment:** `// text_layer is forwarded to svg.compose script_input as-is. See tesserax_service/scripts/svg_compose.py for current consumption support. Frontend surface is ready; script may silently ignore unknown keys.`

#### Seed + Action Bar
- Seed `Input` + `Shuffle` button
- `Enqueue Render` → calls `useEnqueueTesserScript` with script `svg.compose`
- `Reset to Defaults` ghost button

#### Jobs Section
Reuses `TesserJobRow` directly — no new infrastructure. Component import from `TesserStudioPanel` extracted to shared location or duplicated cleanly.

---

### D3: Batch Seed Dialog Rebuild (`BatchSeedSvgDialog.tsx`)

Full replacement of the toy gradient generator. Two-phase flow.

#### Phase 1 — Configure

| Field | Control | Notes |
|---|---|---|
| Count | `Input` (1–24) | Tooltip: "for bulk runs, use `svgs seed` CLI" |
| Seed | `Input` + Shuffle | Deterministic reproducibility |
| Families | Multi-select chip row | All 6, default all selected |
| Tier | Radio: Pairwise / Hero / Safe | Default Pairwise |

`Generate Plan` button → runs `buildScenarios()` client-side.

#### Phase 2 — Preview & Override

Accordion list of generated scenarios. Each row shows:
- Family badge
- 4–5 key knob values: palette_family, shape_family, displacement_scale, density
- `Edit ›` chevron → expands inline knob editor (same 7-group structure, pre-populated)
- `Regenerate` button → re-samples this slot only, preserving others

Text Overlay (collapsible):
- Template: `{family}-{index}` / custom string / off
- Font size, anchor, position x/y %

#### Phase 3 — Enqueue & Track

`Enqueue All` fires `useEnqueueTesserScript` for each scenario with `svg.compose`.
Progress: `Enqueuing 3 / 12...` counter inline.
After queuing: job summary using existing `TesserJobRow` per job.

---

### D4: Inline Documentation Contract

Every new file and function in D follows this pattern:

1. **File header:** cites Python source file(s) it mirrors or extends
2. **Function header:** documents simplifications vs. the Python original where they exist
3. **Knob group comments:** `// § X. Section Name — svg_combinatorics_reference_card.md`
4. **Forward-compatibility comments:** anywhere the frontend surface is ahead of script support

---

## B: Gallery Tagging, Filtering, Sort

### Tagging

No new backend model field. Tags live in `metadata_json.tags: string[]`.

**Derived tags** (computed client-side for display, not written to backend):
- `metadata_json.family` → family tag
- `metadata_json.generation_tier` → tier tag
- `metadata_json.knobs?.palette_family` → palette tag
- `metadata_json.complexity_score` bucketed → `complexity:low` / `complexity:mid` / `complexity:high`
- `metadata_json.source` → `source:tesser`, `source:combinatorics`, etc.

**User tags** written back via existing PATCH endpoint (`usePatchSvg`) updating `metadata_json.tags`.

**SvgCard changes:**
- Tag row below description: up to 4 tags as `Badge` chips, `+N more` overflow
- Clicking a tag activates that filter in the gallery (via callback up to parent)
- Inline tag editor: `+` button opens a small popover with text input + existing tag chips

### Filtering

Collapsible filter bar between search and grid in `SvgsGalleryPanel`. Toggle button shows active filter count badge.

**Filter sections:**
- **Family** — chips from `STYLE_FAMILIES`
- **Tier** — chips: pairwise-core / hero-extreme / safe-utility / tesser / manual
- **Complexity** — Low / Mid / High toggle (bucketed from `complexity_score`)
- **Palette** — chips derived from loaded dataset's `knobs.palette_family` values
- **User Tags** — autocomplete chip input from all `metadata_json.tags` seen in loaded data

All filters AND-combine. State is local to `SvgsGalleryPanel`.

### Sort

Compact row above grid, right-aligned:
- Sort by buttons: `Name` · `Updated` · `Created` · `Complexity` · `Contrast`
- `↑↓` direction toggle
- Default: Updated descending

The existing `filtered` memo in `SvgsGalleryPanel` extends to a `filteredAndSorted` memo handling both in one pass.

---

## C: Tesser Studio Gentle Mode (after B)

Third `InputMode` option: `"guided" | "json" | "gentle"`.

Gentle Mode renders a simplified surface:
- Family preset picker (from `svgComposeDomains.ts`)
- 5–6 "feels" controls: Mood, Complexity, Color Temperature, Chaos Level, Palette, Shape Character
- Each "feel" maps internally to a combination of knob values via a `gentleModeToKnobs()` mapping function
- The JSON mirror (already present in guided mode) stays visible as a disclosure — users can see what their "feels" translate to

Modal tooltips and expressive callouts are additive — the core works first, expressiveness layers in.

Infrastructure reuse: `applyFamilyBias`, `svgComposeDomains.ts`, existing job/save flow.

---

## A: Gallery UX Polish (after B)

With B's tag/filter infrastructure in place, A's items are straightforward:

- **Preview CSS fixes:** center SVG in container, add `whitespace-pre-wrap` to code block, copy button (clipboard API), syntax-highlighted code block (prism or highlight.js — or simply a styled `<pre>`), collapsible for code section, "show exact size" opens a second dialog with viewport-sized panel
- **Rename:** inline edit on `SvgCard` title, saves via `usePatchSvg`
- **Multi-select delete:** checkbox overlay on cards in selection mode, bulk delete with single confirm
- **Preview edit mode:** edit SVG markup in preview dialog, live re-render on change, Save creates new private asset (not overwrite) — reuses the patch/create infrastructure already in place

---

## Implementation Sequence

```
1. svgComposeDomains.ts — constants + buildScenarios + applyFamilyBias
2. Compose Studio tab in SvgOperationsPanel
3. BatchSeedSvgDialog rebuild
4. SvgCard tag display + inline tag editor
5. SvgsGalleryPanel filter bar + sort controls
6. (C) Gentle Mode in TesserStudioPanel
7. (A) Preview dialog polish + rename + multi-select + edit mode
```
