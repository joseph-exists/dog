# SVG Library: Compose Studio, Batch Seed, Gallery — Implementation Plan


**Goal:** Implement the D→B sequence from the design doc: Compose Studio tab, rebuilt Batch Seed dialog, and Gallery tagging/filtering/sort.

**Architecture:** All new compose functionality routes through the existing `useEnqueueTesserScript` hook targeting `svg.compose`. Domain constants live in a single TS file mirroring the Python source. Gallery features are client-side over already-loaded data.

**Tech Stack:** React 18, TypeScript strict, TanStack Query, ShadCN (Collapsible, ToggleGroup, Select, Badge, Popover, Input, Switch), Tailwind, Biome lint

**Design doc:** `docs/plans/2026-03-25-svg-library-compose-gallery-design.md`
**Python source:** `backend/app/test_scripts/render_things/svg_library_tools.py`
**Reference card:** `backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md`

---

## Task 1: `svgComposeDomains.ts` — constants, types, knob group definitions

**Files:**
- Create: `src/components/Svg/constants/svgComposeDomains.ts`

**Step 1: Create the file**

```typescript
/**
 * SVG Compose Domain Definitions
 *
 * Frontend mirror of the Python combinatorics domain definitions.
 * Authoritative sources:
 *   - backend/app/test_scripts/render_things/svg_library_tools.py (PAIRWISE_DOMAINS, STYLE_FAMILIES, FAMILY_QUOTAS, _apply_family_bias)
 *   - backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md
 *   - backend/app/test_scripts/typer/commands/svgs.py (RINGS_INPUT_SCHEMA, SOFT_GRADIENT_INPUT_SCHEMA)
 *
 * NOTE: buildScenarios() is a pragmatic approximation of the Python pairwise planner.
 * It does NOT guarantee pairwise coverage. For exhaustive library population use the CLI:
 *   python -m app.test_scripts.typer svgs seed --count N
 */

// ---------------------------------------------------------------------------
// Core types
// ---------------------------------------------------------------------------

/** A flat record of knob key → string value (booleans encoded as "true"/"false") */
export type KnobState = Record<string, string>

export const STYLE_FAMILIES = [
  "organic",
  "geometric",
  "glitch",
  "minimal",
  "atmospheric",
  "diagrammatic",
] as const

export type StyleFamily = (typeof STYLE_FAMILIES)[number]

export const FAMILY_DESCRIPTORS: Record<StyleFamily, string> = {
  organic: "flowing curves, earth tones, natural symmetry",
  geometric: "hard edges, radial order, structured contrast",
  glitch: "neon displacement, global distortion, high chaos",
  minimal: "sparse, monochrome, low blur, quiet",
  atmospheric: "particles, screen blend, low-frequency noise",
  diagrammatic: "stripes, high contrast, multiply blend",
}

/** Tailwind accent class per family — used for card border/glow in the preset row */
export const FAMILY_ACCENT: Record<StyleFamily, string> = {
  organic: "border-emerald-500/50 bg-emerald-950/20",
  geometric: "border-blue-500/50 bg-blue-950/20",
  glitch: "border-fuchsia-500/50 bg-fuchsia-950/20",
  minimal: "border-slate-400/40 bg-slate-900/20",
  atmospheric: "border-sky-400/40 bg-sky-950/20",
  diagrammatic: "border-amber-500/50 bg-amber-950/20",
}

// ---------------------------------------------------------------------------
// § A. Geometry/Base Composition — svg_combinatorics_reference_card.md §2A
// ---------------------------------------------------------------------------
export const SHAPE_FAMILIES = ["curves", "polygons", "rings", "stripes", "particles"] as const
export const LAYER_COUNTS = ["1", "2", "4", "6"] as const
export const DENSITIES = ["sparse", "medium", "dense"] as const
export const SYMMETRIES = ["none", "radial", "mirror-x", "mirror-y"] as const
export const VIEWBOXES = ["square(1024)", "landscape(1366x768)", "portrait(768x1366)"] as const

// ---------------------------------------------------------------------------
// § B. Turbulence / Noise — svg_combinatorics_reference_card.md §2B
// ---------------------------------------------------------------------------
export const TURBULENCE_TYPES = ["fractalNoise", "turbulence"] as const
export const BASE_FREQUENCIES = ["0.003", "0.01", "0.03", "0.08"] as const
export const NUM_OCTAVES = ["1", "2", "4", "6"] as const
export const SEED_BUCKETS = ["0-99", "100-999", "1000-9999"] as const
export const STITCH_TILES = ["stitch", "noStitch"] as const

// ---------------------------------------------------------------------------
// § C. Displacement / Distortion — svg_combinatorics_reference_card.md §2C
// ---------------------------------------------------------------------------
export const DISPLACEMENT_SCALES = ["0", "8", "24", "64", "120"] as const
export const CHANNELS = ["R", "G", "B", "A"] as const
export const DISTORTION_SCOPES = ["background-only", "subject-only", "global"] as const

// ---------------------------------------------------------------------------
// § D. Blur / Fuzzing / Edge Softness — svg_combinatorics_reference_card.md §2D
// ---------------------------------------------------------------------------
export const GAUSSIAN_BLURS = ["0", "0.8", "2", "6", "14"] as const
export const MORPHOLOGIES = ["none", "erode(1)", "dilate(1)", "dilate(3)"] as const
export const DROP_SHADOWS = ["off", "subtle", "strong"] as const
export const FUZZ_MASKS = ["off", "low", "high"] as const

// ---------------------------------------------------------------------------
// § E. Color / Palette — svg_combinatorics_reference_card.md §2E
// ---------------------------------------------------------------------------
export const PALETTE_FAMILIES = ["warm", "cool", "duotone", "neon", "earth", "mono"] as const
export const PALETTE_CARDINALITIES = ["1", "2", "4", "6"] as const
export const CONTRAST_BANDS = ["low", "mid", "high"] as const
export const SATURATION_BANDS = ["desat", "balanced", "vivid"] as const
export const LUMINANCE_BIASES = ["dark", "balanced", "light"] as const

// ---------------------------------------------------------------------------
// § F. Blending / Compositing — svg_combinatorics_reference_card.md §2F
// ---------------------------------------------------------------------------
export const BLEND_MODES_PRIMARY = ["normal", "multiply", "screen", "overlay", "darken", "lighten"] as const
export const BLEND_MODES_SECONDARY = ["none", "multiply", "screen", "overlay"] as const
export const OPACITY_STACKS = ["flat(1.0)", "stepped(1/0.7/0.4)", "mist(0.15-0.55)"] as const
export const COMPOSITE_OPS = ["over", "in", "out", "atop", "xor"] as const

// ---------------------------------------------------------------------------
// § G. Motion-Like Texture — svg_combinatorics_reference_card.md §2G
// ---------------------------------------------------------------------------
export const DIRECTIONALITIES = ["none", "horizontal", "vertical", "diagonal", "radial"] as const
export const FREQUENCY_JITTERS = ["none", "low", "high"] as const
export const PHASE_OFFSETS = ["0", "0.25", "0.5", "0.75"] as const

// ---------------------------------------------------------------------------
// Flat domain map — mirrors PAIRWISE_DOMAINS in svg_library_tools.py
// ---------------------------------------------------------------------------
export const PAIRWISE_DOMAINS: Record<string, readonly string[]> = {
  shape_family: SHAPE_FAMILIES,
  layer_count: LAYER_COUNTS,
  density: DENSITIES,
  symmetry: SYMMETRIES,
  viewbox: VIEWBOXES,
  turbulence_type: TURBULENCE_TYPES,
  base_frequency: BASE_FREQUENCIES,
  num_octaves: NUM_OCTAVES,
  seed_bucket: SEED_BUCKETS,
  stitch_tiles: STITCH_TILES,
  displacement_scale: DISPLACEMENT_SCALES,
  channel_x: CHANNELS,
  channel_y: CHANNELS,
  distortion_scope: DISTORTION_SCOPES,
  gaussian_blur: GAUSSIAN_BLURS,
  morphology: MORPHOLOGIES,
  drop_shadow: DROP_SHADOWS,
  fuzz_mask: FUZZ_MASKS,
  palette_family: PALETTE_FAMILIES,
  palette_cardinality: PALETTE_CARDINALITIES,
  contrast_band: CONTRAST_BANDS,
  saturation_band: SATURATION_BANDS,
  luminance_bias: LUMINANCE_BIASES,
  blend_mode_primary: BLEND_MODES_PRIMARY,
  blend_mode_secondary: BLEND_MODES_SECONDARY,
  opacity_stack: OPACITY_STACKS,
  composite_op: COMPOSITE_OPS,
  directionality: DIRECTIONALITIES,
  frequency_jitter: FREQUENCY_JITTERS,
  phase_offset: PHASE_OFFSETS,
}

// ---------------------------------------------------------------------------
// Knob group definitions — drives both ComposeStudioTab and BatchSeedDialog
// ---------------------------------------------------------------------------

export interface KnobDef {
  key: string
  label: string
  kind: "enum-short" | "enum-long" | "number"
  options?: readonly string[]
  defaultValue: string
  description?: string
}

export interface KnobGroupDef {
  key: string
  label: string
  /** Reference card section, shown in tooltip */
  referenceSection: string
  tooltip: string
  knobs: KnobDef[]
}

export const KNOB_GROUPS: KnobGroupDef[] = [
  {
    key: "geometry",
    label: "Geometry",
    referenceSection: "§ A. Geometry/Base Composition",
    tooltip: "Shape family, layer stacking, density, symmetry, and output dimensions.",
    knobs: [
      { key: "shape_family", label: "Shape Family", kind: "enum-short", options: SHAPE_FAMILIES, defaultValue: "curves" },
      { key: "layer_count", label: "Layers", kind: "enum-short", options: LAYER_COUNTS, defaultValue: "2" },
      { key: "density", label: "Density", kind: "enum-short", options: DENSITIES, defaultValue: "medium" },
      { key: "symmetry", label: "Symmetry", kind: "enum-short", options: SYMMETRIES, defaultValue: "none" },
      { key: "viewbox", label: "Viewbox", kind: "enum-long", options: VIEWBOXES, defaultValue: "square(1024)" },
    ],
  },
  {
    key: "turbulence",
    label: "Turbulence",
    referenceSection: "§ B. Turbulence / Noise",
    tooltip: "SVG feTurbulence filter settings — controls the noise character and frequency.",
    knobs: [
      { key: "turbulence_type", label: "Type", kind: "enum-short", options: TURBULENCE_TYPES, defaultValue: "fractalNoise" },
      { key: "base_frequency", label: "Base Frequency", kind: "enum-short", options: BASE_FREQUENCIES, defaultValue: "0.01" },
      { key: "num_octaves", label: "Octaves", kind: "enum-short", options: NUM_OCTAVES, defaultValue: "2" },
      { key: "seed_bucket", label: "Seed Bucket", kind: "enum-short", options: SEED_BUCKETS, defaultValue: "0-99" },
      { key: "stitch_tiles", label: "Stitch Tiles", kind: "enum-short", options: STITCH_TILES, defaultValue: "stitch" },
    ],
  },
  {
    key: "displacement",
    label: "Displacement",
    referenceSection: "§ C. Displacement / Distortion",
    tooltip: "feDisplacementMap settings — scale, channel mapping, and scope of distortion.",
    knobs: [
      { key: "displacement_scale", label: "Scale", kind: "enum-short", options: DISPLACEMENT_SCALES, defaultValue: "0" },
      { key: "channel_x", label: "Channel X", kind: "enum-short", options: CHANNELS, defaultValue: "R" },
      { key: "channel_y", label: "Channel Y", kind: "enum-short", options: CHANNELS, defaultValue: "G" },
      { key: "distortion_scope", label: "Scope", kind: "enum-short", options: DISTORTION_SCOPES, defaultValue: "background-only" },
    ],
  },
  {
    key: "blur",
    label: "Blur & Edge",
    referenceSection: "§ D. Blur / Fuzzing / Edge Softness",
    tooltip: "Gaussian blur, morphology operations, drop shadow, and fuzz mask controls.",
    knobs: [
      { key: "gaussian_blur", label: "Gaussian Blur", kind: "enum-short", options: GAUSSIAN_BLURS, defaultValue: "0" },
      { key: "morphology", label: "Morphology", kind: "enum-short", options: MORPHOLOGIES, defaultValue: "none" },
      { key: "drop_shadow", label: "Drop Shadow", kind: "enum-short", options: DROP_SHADOWS, defaultValue: "off" },
      { key: "fuzz_mask", label: "Fuzz Mask", kind: "enum-short", options: FUZZ_MASKS, defaultValue: "off" },
    ],
  },
  {
    key: "color",
    label: "Color & Palette",
    referenceSection: "§ E. Color / Palette",
    tooltip: "Palette family, number of colors, contrast, saturation, and luminance bias.",
    knobs: [
      { key: "palette_family", label: "Palette", kind: "enum-short", options: PALETTE_FAMILIES, defaultValue: "warm" },
      { key: "palette_cardinality", label: "Color Count", kind: "enum-short", options: PALETTE_CARDINALITIES, defaultValue: "2" },
      { key: "contrast_band", label: "Contrast", kind: "enum-short", options: CONTRAST_BANDS, defaultValue: "mid" },
      { key: "saturation_band", label: "Saturation", kind: "enum-short", options: SATURATION_BANDS, defaultValue: "balanced" },
      { key: "luminance_bias", label: "Luminance", kind: "enum-short", options: LUMINANCE_BIASES, defaultValue: "balanced" },
    ],
  },
  {
    key: "blending",
    label: "Blending",
    referenceSection: "§ F. Blending / Compositing",
    tooltip: "Layer blend modes, opacity stacking strategy, and compositing operator.",
    knobs: [
      { key: "blend_mode_primary", label: "Primary Blend", kind: "enum-long", options: BLEND_MODES_PRIMARY, defaultValue: "normal" },
      { key: "blend_mode_secondary", label: "Secondary Blend", kind: "enum-short", options: BLEND_MODES_SECONDARY, defaultValue: "none" },
      { key: "opacity_stack", label: "Opacity Stack", kind: "enum-long", options: OPACITY_STACKS, defaultValue: "flat(1.0)" },
      { key: "composite_op", label: "Composite Op", kind: "enum-short", options: COMPOSITE_OPS, defaultValue: "over" },
    ],
  },
  {
    key: "texture",
    label: "Texture & Motion",
    referenceSection: "§ G. Motion-Like Texture (Static Illusion)",
    tooltip: "Directional flow, frequency jitter, and phase offset for implied motion.",
    knobs: [
      { key: "directionality", label: "Directionality", kind: "enum-short", options: DIRECTIONALITIES, defaultValue: "none" },
      { key: "frequency_jitter", label: "Freq Jitter", kind: "enum-short", options: FREQUENCY_JITTERS, defaultValue: "none" },
      { key: "phase_offset", label: "Phase Offset", kind: "enum-short", options: PHASE_OFFSETS, defaultValue: "0" },
    ],
  },
]

/** Build a KnobState with all defaults from KNOB_GROUPS */
export function buildDefaultKnobs(): KnobState {
  const state: KnobState = {}
  for (const group of KNOB_GROUPS) {
    for (const knob of group.knobs) {
      state[knob.key] = knob.defaultValue
    }
  }
  return state
}
```

**Step 2: Verify it compiles**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```
Expected: no errors for this file (others may have pre-existing issues).

**Step 3: Commit**

```bash
git add src/components/Svg/constants/svgComposeDomains.ts
git commit -m "feat: add svgComposeDomains constants, types, and knob group definitions"
```

---

## Task 2: `svgComposeDomains.ts` — `buildScenarios` + `applyFamilyBias`

**Files:**
- Modify: `src/components/Svg/constants/svgComposeDomains.ts` (append)

**Step 1: Append the seeded random utility and pure functions**

Add to the bottom of `svgComposeDomains.ts`:

```typescript
// ---------------------------------------------------------------------------
// Seeded random utility
// Simple LCG — not cryptographic, purely for deterministic UI scenario generation.
// ---------------------------------------------------------------------------

export function makeSeededRandom(seed: number) {
  let s = seed >>> 0
  return function (): number {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0
    return s / 0x100000000
  }
}

function seededChoice<T>(rng: () => number, arr: readonly T[]): T {
  return arr[Math.floor(rng() * arr.length)] as T
}

// ---------------------------------------------------------------------------
// applyFamilyBias
// TS port of svg_library_tools._apply_family_bias.
// Applies mild family-specific defaults. Caller may override any field after.
// ---------------------------------------------------------------------------

export function applyFamilyBias(
  family: StyleFamily,
  base: KnobState,
  rng: () => number,
): KnobState {
  const out = { ...base, style_family: family }

  if (family === "organic") {
    out.shape_family = "curves"
    out.palette_family = seededChoice(rng, ["earth", "cool"])
    out.symmetry = seededChoice(rng, ["none", "radial"])
  } else if (family === "geometric") {
    out.shape_family = seededChoice(rng, ["polygons", "rings", "stripes"])
    out.symmetry = seededChoice(rng, ["radial", "mirror-x", "mirror-y"])
  } else if (family === "glitch") {
    out.palette_family = "neon"
    out.distortion_scope = "global"
    out.displacement_scale = seededChoice(rng, ["24", "64", "120"])
  } else if (family === "minimal") {
    out.density = "sparse"
    out.gaussian_blur = seededChoice(rng, ["0", "0.8"])
    out.palette_family = "mono"
  } else if (family === "atmospheric") {
    out.shape_family = seededChoice(rng, ["curves", "particles"])
    out.base_frequency = seededChoice(rng, ["0.003", "0.01"])
    out.blend_mode_primary = seededChoice(rng, ["screen", "overlay"])
  } else if (family === "diagrammatic") {
    out.shape_family = seededChoice(rng, ["stripes", "rings", "polygons"])
    out.contrast_band = "high"
    out.blend_mode_primary = seededChoice(rng, ["normal", "multiply"])
  }

  return out
}

// ---------------------------------------------------------------------------
// Hero and safe tier overrides — mirrors _hero_override / _safe_override
// ---------------------------------------------------------------------------

function applyHeroOverride(base: KnobState, family: StyleFamily, rng: () => number): KnobState {
  const out = { ...base }
  out.density = "dense"
  out.layer_count = "6"
  out.displacement_scale = seededChoice(rng, ["64", "120"])
  out.gaussian_blur = seededChoice(rng, ["6", "14"])
  out.contrast_band = "high"
  out.saturation_band = "vivid"
  out.palette_cardinality = "6"
  out.opacity_stack = "mist(0.15-0.55)"
  if (family === "minimal") {
    out.density = "medium"
    out.gaussian_blur = "0.8"
    out.palette_cardinality = "2"
  }
  if (family === "diagrammatic") {
    out.shape_family = "stripes"
    out.gaussian_blur = "0"
  }
  return out
}

function applySafeOverride(base: KnobState, family: StyleFamily, rng: () => number): KnobState {
  return {
    ...base,
    shape_family: seededChoice(rng, ["stripes", "rings", "curves"]),
    density: "sparse",
    layer_count: seededChoice(rng, ["1", "2"]),
    displacement_scale: "0",
    gaussian_blur: seededChoice(rng, ["0", "0.8"]),
    palette_cardinality: seededChoice(rng, ["1", "2"]),
    contrast_band: "mid",
    opacity_stack: "flat(1.0)",
    style_family: family,
  }
}

// ---------------------------------------------------------------------------
// buildScenarios
//
// Simplified random sampling from PAIRWISE_DOMAINS with family bias applied.
// NOTE: Does NOT guarantee pairwise coverage — pragmatic approximation only.
// For exhaustive library population, use the CLI:
//   python -m app.test_scripts.typer svgs seed --count N
// ---------------------------------------------------------------------------

export type ScenarioTier = "pairwise" | "hero" | "safe"

export interface Scenario {
  index: number
  family: StyleFamily
  tier: ScenarioTier
  knobs: KnobState
}

export function buildScenarios(input: {
  count: number
  seed: number
  families: StyleFamily[]
  tier: ScenarioTier
}): Scenario[] {
  const { count, seed, tier } = input
  const families = input.families.length > 0 ? input.families : [...STYLE_FAMILIES]
  const rng = makeSeededRandom(seed)

  return Array.from({ length: count }, (_, index) => {
    const family = seededChoice(rng, families)

    // Build a random base row from PAIRWISE_DOMAINS
    const base: KnobState = {}
    for (const [key, domain] of Object.entries(PAIRWISE_DOMAINS)) {
      base[key] = seededChoice(rng, domain)
    }

    let knobs = applyFamilyBias(family, base, rng)
    if (tier === "hero") knobs = applyHeroOverride(knobs, family, rng)
    if (tier === "safe") knobs = applySafeOverride(knobs, family, rng)

    return { index, family, tier, knobs }
  })
}
```

**Step 2: Verify**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

**Step 3: Commit**

```bash
git add src/components/Svg/constants/svgComposeDomains.ts
git commit -m "feat: add buildScenarios and applyFamilyBias to svgComposeDomains"
```

---

## Task 3: Extract `TesserJobRow` to shared display component

**Files:**
- Create: `src/components/Svg/display/TesserJobRow.tsx`
- Modify: `src/components/Svg/panels/TesserStudioPanel.tsx`

**Step 1: Create `TesserJobRow.tsx`**

Cut the `LocalTesserJob` interface, `TesserJobRow` component, and its props interface from `TesserStudioPanel.tsx` and paste into the new file. Add the required imports.

```typescript
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useState } from "react"
import type { SvgAssetCreatePrivate } from "@/client"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { svgsQueryKeys } from "@/hooks/useSvgs"
import { useTesserJob } from "@/hooks/useTesserJob"
import { SvgAppService } from "@/services/svgService"
import {
  TesserService,
  type TesserJobStatusResponse,
  type TesserRenderPayload,
} from "@/services/tesserService"

export interface LocalTesserJob {
  jobId: string
  requestId?: string | null
  scriptName: string
  queuedAt?: string | null
  scriptInput: Record<string, unknown>
}

export interface TesserJobRowProps {
  job: LocalTesserJob
  onSave: (input: {
    scriptName: string
    job: TesserJobStatusResponse
    scriptInput: Record<string, unknown>
  }) => Promise<void>
  savedAssetId?: string | null
}

export function TesserJobRow({ job, onSave, savedAssetId }: TesserJobRowProps) {
  // ... paste full component body from TesserStudioPanel.tsx lines 318-415
}
```

The full body of `TesserJobRow` is cut verbatim from `TesserStudioPanel.tsx` lines 318–415.

**Step 2: Update `TesserStudioPanel.tsx`**

Remove the `LocalTesserJob` interface and `TesserJobRow` component definition. Replace with:

```typescript
import { TesserJobRow, type LocalTesserJob } from "../display/TesserJobRow"
```

Also remove imports no longer needed directly in TesserStudioPanel (check: `useTesserJob`, `SvgAppService`, `svgsQueryKeys` — these are now only in TesserJobRow).

**Step 3: Verify**

```bash
cd frontend && npm run lint 2>&1 | head -30
cd frontend && npx tsc --noEmit 2>&1 | head -30
```
Expected: no new errors.

**Step 4: Commit**

```bash
git add src/components/Svg/display/TesserJobRow.tsx src/components/Svg/panels/TesserStudioPanel.tsx
git commit -m "refactor: extract TesserJobRow to shared display component"
```

---

## Task 4: Build `ComposeStudioTab` component

**Files:**
- Create: `src/components/Svg/panels/ComposeStudioTab.tsx`

**Step 1: Create the file**

```typescript
/**
 * ComposeStudioTab
 *
 * Knob-driven interface for the svg.compose Tesser script.
 * Family presets prime the config; all 30 knobs remain individually overridable.
 *
 * Script: svg.compose (via useEnqueueTesserScript)
 * Knob reference: src/components/Svg/constants/svgComposeDomains.ts
 * Python source: backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md
 */
import { ChevronDown, HelpCircle, Shuffle, Zap } from "lucide-react"
import { useState } from "react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Switch } from "@/components/ui/switch"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useCreatePrivateSvg } from "@/hooks/useSvgs"
import { useEnqueueTesserScript } from "@/hooks/useTesser"
import { TesserService, type TesserJobStatusResponse } from "@/services/tesserService"
import { TesserJobRow, type LocalTesserJob } from "../display/TesserJobRow"
import {
  FAMILY_ACCENT,
  FAMILY_DESCRIPTORS,
  KNOB_GROUPS,
  STYLE_FAMILIES,
  applyFamilyBias,
  buildDefaultKnobs,
  makeSeededRandom,
  type KnobState,
  type StyleFamily,
} from "../constants/svgComposeDomains"

// ---------------------------------------------------------------------------
// Text layer state — forwarded to svg.compose script_input as text_layer.
// text_layer is a frontend extension: svg.compose may silently ignore unknown
// keys until the script is updated to consume them.
// See: tesserax_service/scripts/svg_compose.py for current consumption support.
// ---------------------------------------------------------------------------
interface TextLayerState {
  enabled: boolean
  content: string
  font_size: string
  anchor: "start" | "middle" | "end"
  fill: string
  x_pct: string
  y_pct: string
}

const DEFAULT_TEXT_LAYER: TextLayerState = {
  enabled: false,
  content: "",
  font_size: "24",
  anchor: "middle",
  fill: "#ffffff",
  x_pct: "50",
  y_pct: "90",
}

function buildScriptInput(knobs: KnobState, textLayer: TextLayerState): Record<string, unknown> {
  const input: Record<string, unknown> = { ...knobs }
  if (textLayer.enabled) {
    input.text_layer = {
      enabled: true,
      content: textLayer.content,
      font_size: Number(textLayer.font_size) || 24,
      anchor: textLayer.anchor,
      fill: textLayer.fill,
      x_pct: Number(textLayer.x_pct) || 50,
      y_pct: Number(textLayer.y_pct) || 90,
    }
  }
  return input
}

function buildSavedAssetName(knobs: KnobState): string {
  const family = knobs.style_family ?? "compose"
  const palette = knobs.palette_family ?? ""
  const stamp = new Date().toISOString().replace(/[:.]/g, "-")
  return `compose-${family}-${palette}-${stamp}`
}

// ---------------------------------------------------------------------------
// FamilyPresetRow — 6 clickable cards, active family highlighted
// ---------------------------------------------------------------------------
function FamilyPresetRow({
  active,
  onSelect,
}: {
  active: StyleFamily | null
  onSelect: (family: StyleFamily) => void
}) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {STYLE_FAMILIES.map((family) => (
        <button
          key={family}
          type="button"
          onClick={() => onSelect(family)}
          className={[
            "rounded-lg border p-2 text-left transition-all hover:opacity-90",
            active === family
              ? `${FAMILY_ACCENT[family]} ring-1 ring-current`
              : "border-border bg-muted/20 hover:bg-muted/40",
          ].join(" ")}
        >
          <div className="text-xs font-semibold capitalize">{family}</div>
          <div className="mt-0.5 text-[10px] leading-tight text-muted-foreground">
            {FAMILY_DESCRIPTORS[family]}
          </div>
        </button>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// KnobGroupPanel — collapsible section for one group of knobs
// ---------------------------------------------------------------------------
function KnobGroupPanel({
  group,
  knobs,
  open,
  onOpenChange,
  onChange,
}: {
  group: (typeof KNOB_GROUPS)[number]
  knobs: KnobState
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (key: string, value: string) => void
}) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg border bg-muted/20 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/40"
        >
          <div className="flex items-center gap-2">
            {group.label}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="size-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-60">
                  <p className="text-xs">{group.tooltip}</p>
                  <p className="mt-1 text-[10px] text-muted-foreground">{group.referenceSection}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <ChevronDown className={["size-4 transition-transform", open ? "rotate-180" : ""].join(" ")} />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 space-y-3 rounded-lg border border-t-0 bg-background/50 p-3">
          {group.knobs.map((knob) => (
            <div key={knob.key} className="space-y-1">
              <Label className="text-xs">{knob.label}</Label>
              {knob.kind === "enum-short" && knob.options ? (
                <ToggleGroup
                  type="single"
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onValueChange={(v) => { if (v) onChange(knob.key, v) }}
                  variant="outline"
                  className="flex-wrap justify-start"
                >
                  {knob.options.map((opt) => (
                    <ToggleGroupItem key={opt} value={opt} className="h-7 px-2 text-xs">
                      {opt}
                    </ToggleGroupItem>
                  ))}
                </ToggleGroup>
              ) : knob.kind === "enum-long" && knob.options ? (
                <Select
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onValueChange={(v) => onChange(knob.key, v)}
                >
                  <SelectTrigger className="h-8 text-xs">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {knob.options.map((opt) => (
                      <SelectItem key={opt} value={opt} className="text-xs">{opt}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              ) : knob.kind === "number" ? (
                <Input
                  type="number"
                  className="h-8 text-xs"
                  value={knobs[knob.key] ?? knob.defaultValue}
                  onChange={(e) => onChange(knob.key, e.target.value)}
                />
              ) : null}
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

// ---------------------------------------------------------------------------
// TextLayerPanel — 8th knob group, off by default
// ---------------------------------------------------------------------------
function TextLayerPanel({
  state,
  open,
  onOpenChange,
  onChange,
}: {
  state: TextLayerState
  open: boolean
  onOpenChange: (open: boolean) => void
  onChange: (patch: Partial<TextLayerState>) => void
}) {
  return (
    <Collapsible open={open} onOpenChange={onOpenChange}>
      <CollapsibleTrigger asChild>
        <button
          type="button"
          className="flex w-full items-center justify-between rounded-lg border bg-muted/20 px-3 py-2 text-sm font-medium transition-colors hover:bg-muted/40"
        >
          <div className="flex items-center gap-2">
            Text Layer
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="size-3.5 text-muted-foreground" />
                </TooltipTrigger>
                <TooltipContent className="max-w-60">
                  <p className="text-xs">
                    Adds a text element to the SVG output. Forwarded to svg.compose as{" "}
                    <code>text_layer</code>. Script may silently ignore if not yet supported.
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
          <ChevronDown className={["size-4 transition-transform", open ? "rotate-180" : ""].join(" ")} />
        </button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-1 space-y-3 rounded-lg border border-t-0 bg-background/50 p-3">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Enable Text Layer</Label>
            <Switch
              checked={state.enabled}
              onCheckedChange={(checked) => onChange({ enabled: checked })}
            />
          </div>
          {state.enabled ? (
            <>
              <div className="space-y-1">
                <Label className="text-xs">Content</Label>
                <Input
                  className="h-8 text-xs"
                  value={state.content}
                  onChange={(e) => onChange({ content: e.target.value })}
                  placeholder="Text to render"
                />
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">Font Size</Label>
                  <Input
                    type="number"
                    className="h-8 text-xs"
                    value={state.font_size}
                    onChange={(e) => onChange({ font_size: e.target.value })}
                  />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Fill Color</Label>
                  <Input
                    className="h-8 text-xs"
                    value={state.fill}
                    onChange={(e) => onChange({ fill: e.target.value })}
                    placeholder="#ffffff"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <Label className="text-xs">Anchor</Label>
                <ToggleGroup
                  type="single"
                  value={state.anchor}
                  onValueChange={(v) => { if (v) onChange({ anchor: v as TextLayerState["anchor"] }) }}
                  variant="outline"
                >
                  {(["start", "middle", "end"] as const).map((a) => (
                    <ToggleGroupItem key={a} value={a} className="h-7 px-2 text-xs">{a}</ToggleGroupItem>
                  ))}
                </ToggleGroup>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div className="space-y-1">
                  <Label className="text-xs">X Position %</Label>
                  <Input type="number" min={0} max={100} className="h-8 text-xs" value={state.x_pct} onChange={(e) => onChange({ x_pct: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Y Position %</Label>
                  <Input type="number" min={0} max={100} className="h-8 text-xs" value={state.y_pct} onChange={(e) => onChange({ y_pct: e.target.value })} />
                </div>
              </div>
            </>
          ) : (
            <p className="text-xs text-muted-foreground">Enable to add a text overlay to the rendered SVG.</p>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  )
}

// ---------------------------------------------------------------------------
// ComposeStudioTab — main export
// ---------------------------------------------------------------------------
export function ComposeStudioTab() {
  const enqueueMutation = useEnqueueTesserScript()
  const createSvgMutation = useCreatePrivateSvg()

  const [activeFamily, setActiveFamily] = useState<StyleFamily | null>(null)
  const [knobs, setKnobs] = useState<KnobState>(buildDefaultKnobs)
  const [seed, setSeed] = useState(String(Math.floor(Math.random() * 99999)))
  const [openGroups, setOpenGroups] = useState<Set<string>>(new Set(["geometry"]))
  const [textLayerOpen, setTextLayerOpen] = useState(false)
  const [textLayer, setTextLayer] = useState<TextLayerState>(DEFAULT_TEXT_LAYER)
  const [jobs, setJobs] = useState<LocalTesserJob[]>([])
  const [savedAssetIdByJobId, setSavedAssetIdByJobId] = useState<Record<string, string>>({})

  function handleFamilySelect(family: StyleFamily) {
    setActiveFamily(family)
    const rng = makeSeededRandom(Number(seed) || 42)
    setKnobs((prev) => applyFamilyBias(family, prev, rng))
  }

  function handleRandomize() {
    const newSeed = Math.floor(Math.random() * 99999)
    setSeed(String(newSeed))
    const rng = makeSeededRandom(newSeed)
    const family = activeFamily ?? "organic"
    const base: KnobState = {}
    for (const group of KNOB_GROUPS) {
      for (const knob of group.knobs) {
        const opts = knob.options ?? []
        base[knob.key] = opts[Math.floor(rng() * opts.length)] ?? knob.defaultValue
      }
    }
    setKnobs(applyFamilyBias(family as StyleFamily, base, rng))
  }

  function handleKnobChange(key: string, value: string) {
    setKnobs((prev) => ({ ...prev, [key]: value }))
  }

  function toggleGroup(key: string) {
    setOpenGroups((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  async function handleEnqueue() {
    if (enqueueMutation.isPending) return
    const scriptInput = buildScriptInput(knobs, textLayer)
    const response = await enqueueMutation.mutateAsync({
      scriptName: "svg.compose",
      payload: { script_input: scriptInput },
    })
    setJobs((prev) => [
      {
        jobId: response.job_id,
        requestId: response.request_id,
        scriptName: response.script_name,
        queuedAt: response.queued_at,
        scriptInput,
      },
      ...prev,
    ])
    showSuccessToast("Compose job enqueued")
  }

  async function handleSaveJob(input: {
    scriptName: string
    job: TesserJobStatusResponse
    scriptInput: Record<string, unknown>
  }) {
    if (savedAssetIdByJobId[input.job.job_id]) return
    const svgMarkup = TesserService.getSvgMarkupFromRender(input.job.render)
    if (!svgMarkup) return
    const created = await createSvgMutation.mutateAsync({
      visibility: "private",
      name: buildSavedAssetName(knobs),
      description: `Compose Studio render — family: ${knobs.style_family ?? "—"}, palette: ${knobs.palette_family ?? "—"}`,
      svg_markup: svgMarkup,
      metadata_json: {
        source: "compose-studio",
        script_name: input.scriptName,
        script_input: input.scriptInput,
        job_id: input.job.job_id,
        family: knobs.style_family ?? null,
        knobs,
      },
    })
    setSavedAssetIdByJobId((prev) => ({ ...prev, [input.job.job_id]: String(created.id) }))
  }

  return (
    <div className="space-y-4">
      {/* Family preset row */}
      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <Label className="text-sm">Style Family</Label>
          <Button type="button" size="sm" variant="ghost" onClick={handleRandomize}>
            <Shuffle className="mr-1 size-3.5" />
            Randomize
          </Button>
        </div>
        <FamilyPresetRow active={activeFamily} onSelect={handleFamilySelect} />
      </div>

      {/* Knob groups */}
      <div className="space-y-1.5">
        {KNOB_GROUPS.map((group) => (
          <KnobGroupPanel
            key={group.key}
            group={group}
            knobs={knobs}
            open={openGroups.has(group.key)}
            onOpenChange={() => toggleGroup(group.key)}
            onChange={handleKnobChange}
          />
        ))}
        <TextLayerPanel
          state={textLayer}
          open={textLayerOpen}
          onOpenChange={setTextLayerOpen}
          onChange={(patch) => setTextLayer((prev) => ({ ...prev, ...patch }))}
        />
      </div>

      {/* Seed + action bar */}
      <div className="flex flex-wrap items-end gap-2">
        <div className="flex-1 space-y-1 min-w-32">
          <Label className="text-xs">Seed</Label>
          <div className="flex gap-1">
            <Input
              className="h-8 text-xs font-mono"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="h-8 px-2"
              onClick={() => setSeed(String(Math.floor(Math.random() * 99999)))}
            >
              <Shuffle className="size-3.5" />
            </Button>
          </div>
        </div>
        <Button onClick={() => void handleEnqueue()} disabled={enqueueMutation.isPending}>
          <Zap className="mr-1.5 size-4" />
          {enqueueMutation.isPending ? "Queueing..." : "Enqueue Render"}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            setKnobs(buildDefaultKnobs())
            setActiveFamily(null)
            setTextLayer(DEFAULT_TEXT_LAYER)
          }}
        >
          Reset
        </Button>
      </div>

      {/* Jobs section */}
      {jobs.length > 0 ? (
        <div className="space-y-2 border-t pt-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-medium">Render Jobs</div>
            <Badge variant="outline">{jobs.length}</Badge>
          </div>
          {jobs.map((job) => (
            <TesserJobRow
              key={job.jobId}
              job={job}
              onSave={handleSaveJob}
              savedAssetId={savedAssetIdByJobId[job.jobId] ?? null}
            />
          ))}
        </div>
      ) : null}
    </div>
  )
}
```

**Step 2: Verify**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
```
Expected: no errors in the new file.

**Step 3: Commit**

```bash
git add src/components/Svg/panels/ComposeStudioTab.tsx
git commit -m "feat: add ComposeStudioTab with family presets and full knob UI"
```

---

## Task 5: Add Compose Studio tab to `SvgOperationsPanel`

**Files:**
- Modify: `src/components/Svg/panels/SvgOperationsPanel.tsx`

**Step 1: Update the tabs grid and add import**

Add to imports:
```typescript
import { ComposeStudioTab } from "./ComposeStudioTab"
```

Change the TabsList grid from `grid-cols-2` to `grid-cols-3` and add the new tab:

```tsx
<TabsList className="grid w-full grid-cols-3">
  <TabsTrigger value="compose">Compose Studio</TabsTrigger>
  <TabsTrigger value="studio">Combinatorics</TabsTrigger>
  <TabsTrigger value="editor">Asset Editor</TabsTrigger>
</TabsList>
```

Change `defaultValue` from `"studio"` to `"compose"`.

Add the new tab content before the existing `TabsContent value="studio"`:

```tsx
<TabsContent value="compose" className="space-y-4">
  <ComposeStudioTab />
</TabsContent>
```

**Step 2: Verify the app builds**

```bash
cd frontend && npm run build 2>&1 | tail -20
```

**Step 3: Commit**

```bash
git add src/components/Svg/panels/SvgOperationsPanel.tsx
git commit -m "feat: add Compose Studio as primary tab in SvgOperationsPanel"
```

---

## Task 6: Rebuild `BatchSeedSvgDialog`

**Files:**
- Modify: `src/components/Svg/dialogs/BatchSeedSvgDialog.tsx` (full rewrite)

**Step 1: Rewrite the file**

```typescript
/**
 * BatchSeedSvgDialog — rebuilt
 *
 * Three-phase flow: Configure → Preview & Override → Enqueue & Track
 *
 * Scenario generation uses buildScenarios() from svgComposeDomains.ts,
 * a simplified approximation of the Python pairwise planner.
 * Each scenario is enqueued as an individual svg.compose Tesser job.
 *
 * For exhaustive library population, use the CLI instead:
 *   python -m app.test_scripts.typer svgs seed --count N
 *
 * See: backend/app/test_scripts/render_things/svg_combinatorics_reference_card.md
 */
import { ChevronDown, ChevronUp, Shuffle } from "lucide-react"
import { useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Progress } from "@/components/ui/progress"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { showSuccessToast } from "@/hooks/useCustomToast"
import { useEnqueueTesserScript } from "@/hooks/useTesser"
import {
  FAMILY_ACCENT,
  KNOB_GROUPS,
  STYLE_FAMILIES,
  buildScenarios,
  type KnobState,
  type Scenario,
  type ScenarioTier,
  type StyleFamily,
} from "../constants/svgComposeDomains"
import { TesserJobRow, type LocalTesserJob } from "../display/TesserJobRow"

type Phase = "configure" | "preview" | "enqueuing" | "done"

// ---------------------------------------------------------------------------
// ScenarioRow — shows one scenario in the preview accordion
// ---------------------------------------------------------------------------
function ScenarioRow({
  scenario,
  onKnobChange,
}: {
  scenario: Scenario
  onKnobChange: (index: number, key: string, value: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const keyKnobs = ["palette_family", "shape_family", "displacement_scale", "density", "gaussian_blur"]

  return (
    <div className="rounded-lg border bg-muted/10">
      <div className="flex items-center justify-between gap-2 px-3 py-2">
        <div className="flex flex-wrap items-center gap-1.5 min-w-0">
          <Badge
            variant="outline"
            className={`text-[10px] capitalize ${FAMILY_ACCENT[scenario.family]}`}
          >
            {scenario.family}
          </Badge>
          {keyKnobs.map((k) => (
            scenario.knobs[k] ? (
              <span key={k} className="text-[10px] text-muted-foreground">
                {scenario.knobs[k]}
              </span>
            ) : null
          ))}
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={() => setExpanded((p) => !p)}
        >
          {expanded ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
          Edit
        </Button>
      </div>

      {expanded ? (
        <div className="border-t px-3 py-2 space-y-3">
          {KNOB_GROUPS.map((group) => (
            <div key={group.key} className="space-y-1.5">
              <div className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                {group.label}
              </div>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {group.knobs.map((knob) => (
                  <div key={knob.key} className="space-y-0.5">
                    <Label className="text-[10px]">{knob.label}</Label>
                    {knob.options && knob.options.length <= 4 ? (
                      <ToggleGroup
                        type="single"
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onValueChange={(v) => { if (v) onKnobChange(scenario.index, knob.key, v) }}
                        variant="outline"
                        className="flex-wrap justify-start"
                      >
                        {knob.options.map((opt) => (
                          <ToggleGroupItem key={opt} value={opt} className="h-6 px-1.5 text-[10px]">
                            {opt}
                          </ToggleGroupItem>
                        ))}
                      </ToggleGroup>
                    ) : knob.options ? (
                      <Select
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onValueChange={(v) => onKnobChange(scenario.index, knob.key, v)}
                      >
                        <SelectTrigger className="h-6 text-[10px]">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {knob.options.map((opt) => (
                            <SelectItem key={opt} value={opt} className="text-[10px]">{opt}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    ) : (
                      <Input
                        className="h-6 text-[10px]"
                        value={scenario.knobs[knob.key] ?? knob.defaultValue}
                        onChange={(e) => onKnobChange(scenario.index, knob.key, e.target.value)}
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  )
}

// ---------------------------------------------------------------------------
// BatchSeedSvgDialog
// ---------------------------------------------------------------------------
export function BatchSeedSvgDialog() {
  const enqueueMutation = useEnqueueTesserScript()

  const [open, setOpen] = useState(false)
  const [phase, setPhase] = useState<Phase>("configure")

  // Configure state
  const [count, setCount] = useState("8")
  const [seed, setSeed] = useState(String(Math.floor(Math.random() * 99999)))
  const [families, setFamilies] = useState<StyleFamily[]>([...STYLE_FAMILIES])
  const [tier, setTier] = useState<ScenarioTier>("pairwise")

  // Preview state
  const [scenarios, setScenarios] = useState<Scenario[]>([])

  // Enqueue state
  const [jobs, setJobs] = useState<LocalTesserJob[]>([])
  const [progress, setProgress] = useState({ done: 0, total: 0 })
  const [savedAssetIdByJobId, setSavedAssetIdByJobId] = useState<Record<string, string>>({})

  const parsedCount = Math.min(Math.max(Number.parseInt(count, 10) || 1, 1), 24)

  function handleGeneratePlan() {
    const generated = buildScenarios({
      count: parsedCount,
      seed: Number(seed) || 42,
      families,
      tier,
    })
    setScenarios(generated)
    setPhase("preview")
  }

  function handleKnobChange(index: number, key: string, value: string) {
    setScenarios((prev) =>
      prev.map((s) =>
        s.index === index ? { ...s, knobs: { ...s.knobs, [key]: value } } : s,
      ),
    )
  }

  async function handleEnqueueAll() {
    setPhase("enqueuing")
    setProgress({ done: 0, total: scenarios.length })
    const newJobs: LocalTesserJob[] = []

    for (const scenario of scenarios) {
      const scriptInput: Record<string, unknown> = { ...scenario.knobs }
      try {
        const response = await enqueueMutation.mutateAsync({
          scriptName: "svg.compose",
          payload: { script_input: scriptInput },
        })
        newJobs.push({
          jobId: response.job_id,
          requestId: response.request_id,
          scriptName: response.script_name,
          queuedAt: response.queued_at,
          scriptInput,
        })
        setProgress((p) => ({ ...p, done: p.done + 1 }))
      } catch {
        setProgress((p) => ({ ...p, done: p.done + 1 }))
      }
    }

    setJobs(newJobs)
    setPhase("done")
    showSuccessToast(`Enqueued ${newJobs.length} compose jobs`)
  }

  function handleReset() {
    setPhase("configure")
    setScenarios([])
    setJobs([])
    setProgress({ done: 0, total: 0 })
    setSavedAssetIdByJobId({})
  }

  function handleClose(isOpen: boolean) {
    setOpen(isOpen)
    if (!isOpen) handleReset()
  }

  function toggleFamily(family: StyleFamily) {
    setFamilies((prev) =>
      prev.includes(family)
        ? prev.length > 1 ? prev.filter((f) => f !== family) : prev // keep at least one
        : [...prev, family],
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Batch Seed</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Batch Seed SVG Library</DialogTitle>
          <DialogDescription>
            Generate scenarios from combinatoric domains and enqueue as{" "}
            <code>svg.compose</code> Tesser jobs. Review and override any scenario before
            queueing.
          </DialogDescription>
        </DialogHeader>

        {/* Phase: configure */}
        {phase === "configure" ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label>Count <span className="text-xs text-muted-foreground">(max 24 — use CLI for bulk)</span></Label>
                <Input
                  type="number"
                  min={1}
                  max={24}
                  value={count}
                  onChange={(e) => setCount(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <Label>Seed</Label>
                <div className="flex gap-1">
                  <Input
                    value={seed}
                    onChange={(e) => setSeed(e.target.value)}
                    className="font-mono"
                  />
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    className="px-2"
                    onClick={() => setSeed(String(Math.floor(Math.random() * 99999)))}
                  >
                    <Shuffle className="size-3.5" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Style Families</Label>
              <div className="flex flex-wrap gap-1.5">
                {STYLE_FAMILIES.map((family) => (
                  <button
                    key={family}
                    type="button"
                    onClick={() => toggleFamily(family)}
                    className={[
                      "rounded-md border px-2 py-1 text-xs capitalize transition-all",
                      families.includes(family)
                        ? `${FAMILY_ACCENT[family]} font-medium`
                        : "border-border bg-muted/20 text-muted-foreground",
                    ].join(" ")}
                  >
                    {family}
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-1.5">
              <Label>Generation Tier</Label>
              <ToggleGroup
                type="single"
                value={tier}
                onValueChange={(v) => { if (v) setTier(v as ScenarioTier) }}
                variant="outline"
              >
                <ToggleGroupItem value="pairwise" className="text-xs">
                  Pairwise
                  <span className="ml-1 hidden sm:inline text-muted-foreground">broad coverage</span>
                </ToggleGroupItem>
                <ToggleGroupItem value="hero" className="text-xs">
                  Hero
                  <span className="ml-1 hidden sm:inline text-muted-foreground">maxed drama</span>
                </ToggleGroupItem>
                <ToggleGroupItem value="safe" className="text-xs">
                  Safe
                  <span className="ml-1 hidden sm:inline text-muted-foreground">sparse utility</span>
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            <Button onClick={handleGeneratePlan} className="w-full">
              Generate Plan ({parsedCount} scenarios)
            </Button>
          </div>
        ) : null}

        {/* Phase: preview */}
        {phase === "preview" ? (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">
                {scenarios.length} scenarios — review and edit before enqueuing
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={() => setPhase("configure")}>
                ← Back
              </Button>
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {scenarios.map((scenario) => (
                <ScenarioRow
                  key={scenario.index}
                  scenario={scenario}
                  onKnobChange={handleKnobChange}
                />
              ))}
            </div>

            <Button onClick={() => void handleEnqueueAll()} className="w-full">
              Enqueue All {scenarios.length} Jobs
            </Button>
          </div>
        ) : null}

        {/* Phase: enqueuing */}
        {phase === "enqueuing" ? (
          <div className="space-y-3 py-4">
            <div className="text-sm font-medium text-center">
              Enqueuing {progress.done} / {progress.total}...
            </div>
            <Progress value={(progress.done / Math.max(progress.total, 1)) * 100} />
          </div>
        ) : null}

        {/* Phase: done */}
        {phase === "done" ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="text-sm font-medium">{jobs.length} jobs queued</div>
              <Button type="button" variant="ghost" size="sm" onClick={handleReset}>
                Seed Again
              </Button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto pr-1">
              {jobs.map((job) => (
                <TesserJobRow
                  key={job.jobId}
                  job={job}
                  onSave={async () => {}}
                  savedAssetId={savedAssetIdByJobId[job.jobId] ?? null}
                />
              ))}
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
```

Note: `Progress` component from shadcn may need installing. Check with:
```bash
ls frontend/src/components/ui/progress.tsx
```
If missing: `npx shadcn@latest add progress`

**Step 2: Verify**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
cd frontend && npm run lint 2>&1 | head -20
```

**Step 3: Commit**

```bash
git add src/components/Svg/dialogs/BatchSeedSvgDialog.tsx
git commit -m "feat: rebuild BatchSeedSvgDialog with Tesser compose jobs and scenario override"
```

---

## Task 7: Add tag display + inline editor to `SvgCard`

**Files:**
- Modify: `src/components/Svg/display/SvgCard.tsx`

**Step 1: Add tag utility functions and updated component**

The full updated `SvgCard.tsx`:

```typescript
import { CalendarClock, Eye, Globe2, Lock, Plus, Tag, X } from "lucide-react"
import { useState } from "react"
import type { SvgAssetPublic } from "@/client"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { usePatchSvg } from "@/hooks/useSvgs"

// ---------------------------------------------------------------------------
// deriveTags — computes display tags from metadata without writing to backend.
// Combines user-defined tags (metadata_json.tags) with tags derived from knobs.
// ---------------------------------------------------------------------------
function deriveTags(asset: SvgAssetPublic): string[] {
  const meta = (asset.metadata_json ?? {}) as Record<string, unknown>
  const tags: string[] = []

  // User-defined tags stored in metadata_json.tags
  const userTags = meta.tags
  if (Array.isArray(userTags)) {
    for (const t of userTags) {
      if (typeof t === "string" && t.trim()) tags.push(t.trim())
    }
  }

  // Derived: style family
  if (typeof meta.family === "string") tags.push(meta.family)

  // Derived: generation tier (short form)
  if (typeof meta.generation_tier === "string") {
    tags.push(meta.generation_tier.replace("-", " "))
  }

  // Derived: palette family from knobs
  const knobs = meta.knobs as Record<string, unknown> | undefined
  if (knobs && typeof knobs.palette_family === "string") {
    tags.push(knobs.palette_family)
  }

  // Derived: source
  if (typeof meta.source === "string") tags.push(meta.source.replace(/-/g, " "))

  // Derived: complexity bucket
  if (typeof meta.complexity_score === "number") {
    const score = meta.complexity_score
    tags.push(score < 0.33 ? "complexity:low" : score < 0.66 ? "complexity:mid" : "complexity:high")
  }

  // Deduplicate while preserving order
  return [...new Set(tags)].slice(0, 8)
}

function getUserTags(asset: SvgAssetPublic): string[] {
  const meta = (asset.metadata_json ?? {}) as Record<string, unknown>
  const userTags = meta.tags
  if (!Array.isArray(userTags)) return []
  return userTags.filter((t): t is string => typeof t === "string" && Boolean(t.trim()))
}

// ---------------------------------------------------------------------------
// TagEditor — popover for adding/removing user-defined tags
// ---------------------------------------------------------------------------
function TagEditor({ asset }: { asset: SvgAssetPublic }) {
  const patchMutation = usePatchSvg()
  const [input, setInput] = useState("")
  const userTags = getUserTags(asset)

  async function addTag(tag: string) {
    const trimmed = tag.trim()
    if (!trimmed || userTags.includes(trimmed)) return
    const next = [...userTags, trimmed]
    await patchMutation.mutateAsync({
      svgId: asset.id,
      patch: {
        metadata_json: {
          ...(asset.metadata_json as Record<string, unknown> ?? {}),
          tags: next,
        },
      },
    })
    setInput("")
  }

  async function removeTag(tag: string) {
    const next = userTags.filter((t) => t !== tag)
    await patchMutation.mutateAsync({
      svgId: asset.id,
      patch: {
        metadata_json: {
          ...(asset.metadata_json as Record<string, unknown> ?? {}),
          tags: next,
        },
      },
    })
  }

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="sm" className="h-5 w-5 rounded-full p-0">
          <Plus className="size-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-2" align="start">
        <div className="space-y-2">
          <div className="text-xs font-medium">User Tags</div>
          {userTags.length > 0 ? (
            <div className="flex flex-wrap gap-1">
              {userTags.map((tag) => (
                <span
                  key={tag}
                  className="flex items-center gap-0.5 rounded bg-muted px-1.5 py-0.5 text-[10px]"
                >
                  {tag}
                  <button
                    type="button"
                    onClick={() => void removeTag(tag)}
                    className="text-muted-foreground hover:text-foreground"
                  >
                    <X className="size-2.5" />
                  </button>
                </span>
              ))}
            </div>
          ) : null}
          <div className="flex gap-1">
            <Input
              className="h-6 text-xs"
              placeholder="new tag"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") void addTag(input)
              }}
            />
            <Button
              type="button"
              size="sm"
              className="h-6 px-2 text-xs"
              onClick={() => void addTag(input)}
              disabled={patchMutation.isPending}
            >
              Add
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}

// ---------------------------------------------------------------------------
// SvgCard
// ---------------------------------------------------------------------------
interface SvgCardProps {
  asset: SvgAssetPublic
  onPreview: (asset: SvgAssetPublic) => void
  onDelete: (asset: SvgAssetPublic) => void
  onCreatePublicCopy: (asset: SvgAssetPublic) => void
  onTagFilter?: (tag: string) => void
}

export function SvgCard({
  asset,
  onPreview,
  onDelete,
  onCreatePublicCopy,
  onTagFilter,
}: SvgCardProps) {
  const isPublic = asset.visibility === "public"
  const svgDataUrl = `data:image/svg+xml,${encodeURIComponent(asset.svg_markup)}`
  const updatedLabel = new Date(asset.updated_at).toLocaleString()
  const allTags = deriveTags(asset)
  const visibleTags = allTags.slice(0, 4)
  const overflowCount = allTags.length - visibleTags.length

  return (
    <Card className="overflow-hidden">
      <div className="relative h-36 w-full bg-muted/30">
        <img
          src={svgDataUrl}
          alt={asset.name}
          className="h-full w-full object-cover"
          loading="lazy"
        />
      </div>
      <CardHeader className="space-y-1">
        <div className="flex items-center justify-between gap-2">
          <CardTitle className="line-clamp-1 text-base">{asset.name}</CardTitle>
          <Badge variant={isPublic ? "secondary" : "outline"} className="gap-1 shrink-0">
            {isPublic ? <Globe2 className="size-3" /> : <Lock className="size-3" />}
            {asset.visibility ?? "private"}
          </Badge>
        </div>
        <CardDescription className="line-clamp-2">
          {asset.description || "No description"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Tag row */}
        <div className="flex flex-wrap items-center gap-1">
          <Tag className="size-3 shrink-0 text-muted-foreground" />
          {visibleTags.map((tag) => (
            <Badge
              key={tag}
              variant="outline"
              className="cursor-pointer px-1.5 py-0 text-[10px] hover:bg-muted transition-colors"
              onClick={() => onTagFilter?.(tag)}
            >
              {tag}
            </Badge>
          ))}
          {overflowCount > 0 ? (
            <span className="text-[10px] text-muted-foreground">+{overflowCount}</span>
          ) : null}
          <TagEditor asset={asset} />
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <CalendarClock className="size-3.5" />
          Updated {updatedLabel}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={() => onPreview(asset)}>
            <Eye className="mr-1 size-3.5" />
            Preview
          </Button>
          {!isPublic ? (
            <Button size="sm" variant="outline" onClick={() => onCreatePublicCopy(asset)}>
              Make Public
            </Button>
          ) : null}
          <Button size="sm" variant="destructive" onClick={() => onDelete(asset)}>
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
```

**Step 2: Update `SvgsGalleryPanel` to pass `onTagFilter`**

In `SvgsGalleryPanel.tsx`, add a handler and pass it to `SvgCard`:

```typescript
const onTagFilter = (tag: string) => {
  setSearch(tag)  // simplest approach: seed search with the tag
}
```

Then in the SvgCard render: `onTagFilter={onTagFilter}`.

(The filter bar in Task 8 will replace this with proper filter state.)

**Step 3: Verify**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
```

**Step 4: Commit**

```bash
git add src/components/Svg/display/SvgCard.tsx src/components/Svg/panels/SvgsGalleryPanel.tsx
git commit -m "feat: add tag display and inline tag editor to SvgCard"
```

---

## Task 8: Filter bar + sort controls in `SvgsGalleryPanel`

**Files:**
- Modify: `src/components/Svg/panels/SvgsGalleryPanel.tsx`

**Step 1: Replace the panel with the extended version**

Key additions to state:
```typescript
// Filter state
const [filterFamilies, setFilterFamilies] = useState<Set<string>>(new Set())
const [filterTiers, setFilterTiers] = useState<Set<string>>(new Set())
const [filterComplexity, setFilterComplexity] = useState<"all" | "low" | "mid" | "high">("all")
const [filterPalette, setFilterPalette] = useState<Set<string>>(new Set())
const [filterUserTags, setFilterUserTags] = useState<Set<string>>(new Set())
const [filterBarOpen, setFilterBarOpen] = useState(false)

// Sort state
const [sortBy, setSortBy] = useState<"name" | "updated" | "created" | "complexity" | "contrast">("updated")
const [sortDir, setSortDir] = useState<"asc" | "desc">("desc")
```

Replace the `filtered` memo with `filteredAndSorted`:
```typescript
const filteredAndSorted = useMemo(() => {
  const term = search.trim().toLowerCase()
  let rows = listQuery.data?.data ?? []

  // Text search
  if (term) {
    rows = rows.filter((row) => {
      const haystack = [row.name, row.description ?? "", JSON.stringify(row.metadata_json ?? {})]
        .join(" ").toLowerCase()
      return haystack.includes(term)
    })
  }

  // Family filter
  if (filterFamilies.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      return filterFamilies.has(meta.family as string)
    })
  }

  // Tier filter
  if (filterTiers.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      return filterTiers.has(meta.generation_tier as string) ||
        filterTiers.has(meta.source as string)
    })
  }

  // Complexity filter
  if (filterComplexity !== "all") {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const score = typeof meta.complexity_score === "number" ? meta.complexity_score : null
      if (score === null) return false
      if (filterComplexity === "low") return score < 0.33
      if (filterComplexity === "mid") return score >= 0.33 && score < 0.66
      return score >= 0.66
    })
  }

  // Palette filter
  if (filterPalette.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const knobs = meta.knobs as Record<string, unknown> | undefined
      return knobs && filterPalette.has(knobs.palette_family as string)
    })
  }

  // User tag filter
  if (filterUserTags.size > 0) {
    rows = rows.filter((row) => {
      const meta = (row.metadata_json ?? {}) as Record<string, unknown>
      const tags = Array.isArray(meta.tags) ? (meta.tags as string[]) : []
      return [...filterUserTags].every((t) => tags.includes(t))
    })
  }

  // Sort
  rows = [...rows].sort((a, b) => {
    let cmp = 0
    if (sortBy === "name") {
      cmp = a.name.localeCompare(b.name)
    } else if (sortBy === "updated") {
      cmp = new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
    } else if (sortBy === "created") {
      cmp = new Date(a.created_at ?? a.updated_at).getTime() - new Date(b.created_at ?? b.updated_at).getTime()
    } else if (sortBy === "complexity") {
      const aScore = ((a.metadata_json ?? {}) as Record<string, unknown>).complexity_score as number ?? 0
      const bScore = ((b.metadata_json ?? {}) as Record<string, unknown>).complexity_score as number ?? 0
      cmp = aScore - bScore
    } else if (sortBy === "contrast") {
      const aScore = ((a.metadata_json ?? {}) as Record<string, unknown>).contrast_score as number ?? 0
      const bScore = ((b.metadata_json ?? {}) as Record<string, unknown>).contrast_score as number ?? 0
      cmp = aScore - bScore
    }
    return sortDir === "asc" ? cmp : -cmp
  })

  return rows
}, [listQuery.data?.data, search, filterFamilies, filterTiers, filterComplexity, filterPalette, filterUserTags, sortBy, sortDir])
```

Active filter count badge:
```typescript
const activeFilterCount = filterFamilies.size + filterTiers.size +
  (filterComplexity !== "all" ? 1 : 0) + filterPalette.size + filterUserTags.size
```

Filter bar JSX (add below the search input, above the grid):
```tsx
<Collapsible open={filterBarOpen} onOpenChange={setFilterBarOpen}>
  <CollapsibleTrigger asChild>
    <Button variant="outline" size="sm" className="gap-2">
      Filters
      {activeFilterCount > 0 ? (
        <Badge variant="secondary" className="h-4 px-1 text-[10px]">{activeFilterCount}</Badge>
      ) : null}
      <ChevronDown className={["size-3.5 transition-transform", filterBarOpen ? "rotate-180" : ""].join(" ")} />
    </Button>
  </CollapsibleTrigger>
  <CollapsibleContent>
    <div className="mt-2 space-y-3 rounded-lg border bg-muted/10 p-3">

      {/* Family */}
      <div className="space-y-1.5">
        <Label className="text-xs">Family</Label>
        <div className="flex flex-wrap gap-1.5">
          {STYLE_FAMILIES.map((f) => (
            <Badge
              key={f}
              variant={filterFamilies.has(f) ? "default" : "outline"}
              className="cursor-pointer capitalize"
              onClick={() => setFilterFamilies((prev) => {
                const next = new Set(prev)
                next.has(f) ? next.delete(f) : next.add(f)
                return next
              })}
            >
              {f}
            </Badge>
          ))}
        </div>
      </div>

      {/* Tier */}
      <div className="space-y-1.5">
        <Label className="text-xs">Tier</Label>
        <div className="flex flex-wrap gap-1.5">
          {["pairwise-core", "hero-extreme", "safe-utility", "compose-studio", "tesser"].map((t) => (
            <Badge
              key={t}
              variant={filterTiers.has(t) ? "default" : "outline"}
              className="cursor-pointer"
              onClick={() => setFilterTiers((prev) => {
                const next = new Set(prev)
                next.has(t) ? next.delete(t) : next.add(t)
                return next
              })}
            >
              {t}
            </Badge>
          ))}
        </div>
      </div>

      {/* Complexity */}
      <div className="space-y-1.5">
        <Label className="text-xs">Complexity</Label>
        <ToggleGroup
          type="single"
          value={filterComplexity}
          onValueChange={(v) => setFilterComplexity((v || "all") as typeof filterComplexity)}
          variant="outline"
        >
          {(["all", "low", "mid", "high"] as const).map((c) => (
            <ToggleGroupItem key={c} value={c} className="h-7 text-xs">{c}</ToggleGroupItem>
          ))}
        </ToggleGroup>
      </div>

      {/* Clear */}
      {activeFilterCount > 0 ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => {
            setFilterFamilies(new Set())
            setFilterTiers(new Set())
            setFilterComplexity("all")
            setFilterPalette(new Set())
            setFilterUserTags(new Set())
          }}
        >
          Clear all filters
        </Button>
      ) : null}
    </div>
  </CollapsibleContent>
</Collapsible>
```

Sort row JSX (add above the grid, right-aligned):
```tsx
<div className="flex items-center justify-end gap-1 flex-wrap">
  <span className="text-xs text-muted-foreground mr-1">Sort:</span>
  {(["name", "updated", "created", "complexity", "contrast"] as const).map((field) => (
    <Button
      key={field}
      size="sm"
      variant={sortBy === field ? "default" : "ghost"}
      className="h-7 px-2 text-xs capitalize"
      onClick={() => {
        if (sortBy === field) setSortDir((d) => d === "asc" ? "desc" : "asc")
        else { setSortBy(field); setSortDir("desc") }
      }}
    >
      {field}
      {sortBy === field ? (sortDir === "asc" ? " ↑" : " ↓") : null}
    </Button>
  ))}
</div>
```

Also update `SvgCard` usage to pass `onTagFilter`:
```tsx
onTagFilter={(tag) => {
  setFilterUserTags((prev) => {
    const next = new Set(prev)
    next.add(tag)
    return next
  })
  setFilterBarOpen(true)
}}
```

Required new imports in `SvgsGalleryPanel.tsx`:
```typescript
import { ChevronDown } from "lucide-react"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"
import { STYLE_FAMILIES } from "@/components/Svg/constants/svgComposeDomains"
```

**Step 2: Verify**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -40
cd frontend && npm run lint 2>&1 | head -20
```

**Step 3: Final build check**

```bash
cd frontend && npm run build 2>&1 | tail -20
```
Expected: successful build, no type errors.

**Step 4: Commit**

```bash
git add src/components/Svg/panels/SvgsGalleryPanel.tsx
git commit -m "feat: add filter bar and sort controls to SvgsGalleryPanel"
```

---

## Verification Checklist

After all 8 tasks:

- [ ] `npm run build` completes without errors
- [ ] `npm run lint` passes
- [ ] Dev server starts: `npm run dev`
- [ ] Operations panel shows 3 tabs: Compose Studio (default), Combinatorics, Asset Editor
- [ ] Compose Studio: clicking a family preset updates knob values
- [ ] Compose Studio: Geometry group open by default, others collapsed
- [ ] Compose Studio: Enqueue Render creates a job visible in the Jobs section
- [ ] Batch Seed: opens dialog, Generate Plan shows accordion of scenarios
- [ ] Batch Seed: Edit chevron expands inline knob editor
- [ ] Batch Seed: Enqueue All shows progress counter then job list
- [ ] Gallery: SvgCard shows tag row with derived tags
- [ ] Gallery: clicking a tag opens filter bar with that tag active
- [ ] Gallery: sort buttons change order of cards
- [ ] TesserStudioPanel still works (TesserJobRow extraction didn't break it)
