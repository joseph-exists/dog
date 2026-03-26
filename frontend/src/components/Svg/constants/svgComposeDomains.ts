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

// FAMILY_QUOTAS — mirrors svg_library_tools.FAMILY_QUOTAS
// Reserved for future weighted family sampling. Currently buildScenarios uses
// uniform random selection; weighted allocation is a planned enhancement.
// @ts-expect-error TS6133 — intentionally unused reference constant
const _FAMILY_QUOTAS: Record<StyleFamily, number> = {
  organic: 0.18,
  geometric: 0.18,
  glitch: 0.14,
  minimal: 0.16,
  atmospheric: 0.18,
  diagrammatic: 0.16,
}

// ---------------------------------------------------------------------------
// § A. Geometry/Base Composition — svg_combinatorics_reference_card.md §2A
// ---------------------------------------------------------------------------
export const SHAPE_FAMILIES = [
  "curves",
  "polygons",
  "rings",
  "stripes",
  "particles",
] as const
export const LAYER_COUNTS = ["1", "2", "4", "6"] as const
export const DENSITIES = ["sparse", "medium", "dense"] as const
export const SYMMETRIES = ["none", "radial", "mirror-x", "mirror-y"] as const
export const VIEWBOXES = [
  "square(1024)",
  "landscape(1366x768)",
  "portrait(768x1366)",
] as const

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
export const DISTORTION_SCOPES = [
  "background-only",
  "subject-only",
  "global",
] as const

// ---------------------------------------------------------------------------
// § D. Blur / Fuzzing / Edge Softness — svg_combinatorics_reference_card.md §2D
// ---------------------------------------------------------------------------
export const GAUSSIAN_BLURS = ["0", "0.8", "2", "6", "14"] as const
export const MORPHOLOGIES = [
  "none",
  "erode(1)",
  "dilate(1)",
  "dilate(3)",
] as const
export const DROP_SHADOWS = ["off", "subtle", "strong"] as const
export const FUZZ_MASKS = ["off", "low", "high"] as const

// ---------------------------------------------------------------------------
// § E. Color / Palette — svg_combinatorics_reference_card.md §2E
// ---------------------------------------------------------------------------
export const PALETTE_FAMILIES = [
  "warm",
  "cool",
  "duotone",
  "neon",
  "earth",
  "mono",
] as const
export const PALETTE_CARDINALITIES = ["1", "2", "4", "6"] as const
export const CONTRAST_BANDS = ["low", "mid", "high"] as const
export const SATURATION_BANDS = ["desat", "balanced", "vivid"] as const
export const LUMINANCE_BIASES = ["dark", "balanced", "light"] as const

// ---------------------------------------------------------------------------
// § F. Blending / Compositing — svg_combinatorics_reference_card.md §2F
// ---------------------------------------------------------------------------
export const BLEND_MODES_PRIMARY = [
  "normal",
  "multiply",
  "screen",
  "overlay",
  "darken",
  "lighten",
] as const
export const BLEND_MODES_SECONDARY = [
  "none",
  "multiply",
  "screen",
  "overlay",
] as const
export const OPACITY_STACKS = [
  "flat(1.0)",
  "stepped(1/0.7/0.4)",
  "mist(0.15-0.55)",
] as const
export const COMPOSITE_OPS = ["over", "in", "out", "atop", "xor"] as const

// ---------------------------------------------------------------------------
// § G. Motion-Like Texture — svg_combinatorics_reference_card.md §2G
// ---------------------------------------------------------------------------
export const DIRECTIONALITIES = [
  "none",
  "horizontal",
  "vertical",
  "diagonal",
  "radial",
] as const
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
  /** For kind: "number" — rendered as Input[type=number] with hint text */
  min?: number
  max?: number
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
    tooltip:
      "Shape family, layer stacking, density, symmetry, and output dimensions.",
    knobs: [
      {
        key: "shape_family",
        label: "Shape Family",
        kind: "enum-short",
        options: SHAPE_FAMILIES,
        defaultValue: "curves",
      },
      {
        key: "layer_count",
        label: "Layers",
        kind: "enum-short",
        options: LAYER_COUNTS,
        defaultValue: "2",
      },
      {
        key: "density",
        label: "Density",
        kind: "enum-short",
        options: DENSITIES,
        defaultValue: "medium",
      },
      {
        key: "symmetry",
        label: "Symmetry",
        kind: "enum-short",
        options: SYMMETRIES,
        defaultValue: "none",
      },
      {
        key: "viewbox",
        label: "Viewbox",
        kind: "enum-long",
        options: VIEWBOXES,
        defaultValue: "square(1024)",
      },
    ],
  },
  {
    key: "turbulence",
    label: "Turbulence",
    referenceSection: "§ B. Turbulence / Noise",
    tooltip:
      "SVG feTurbulence filter settings — controls the noise character and frequency.",
    knobs: [
      {
        key: "turbulence_type",
        label: "Type",
        kind: "enum-short",
        options: TURBULENCE_TYPES,
        defaultValue: "fractalNoise",
      },
      {
        key: "base_frequency",
        label: "Base Frequency",
        kind: "enum-short",
        options: BASE_FREQUENCIES,
        defaultValue: "0.01",
      },
      {
        key: "num_octaves",
        label: "Octaves",
        kind: "enum-short",
        options: NUM_OCTAVES,
        defaultValue: "2",
      },
      {
        key: "seed_bucket",
        label: "Seed Bucket",
        kind: "enum-short",
        options: SEED_BUCKETS,
        defaultValue: "0-99",
      },
      {
        key: "stitch_tiles",
        label: "Stitch Tiles",
        kind: "enum-short",
        options: STITCH_TILES,
        defaultValue: "stitch",
      },
    ],
  },
  {
    key: "displacement",
    label: "Displacement",
    referenceSection: "§ C. Displacement / Distortion",
    tooltip:
      "feDisplacementMap settings — scale, channel mapping, and scope of distortion.",
    knobs: [
      {
        key: "displacement_scale",
        label: "Scale",
        kind: "enum-short",
        options: DISPLACEMENT_SCALES,
        defaultValue: "0",
      },
      {
        key: "channel_x",
        label: "Channel X",
        kind: "enum-short",
        options: CHANNELS,
        defaultValue: "R",
      },
      {
        key: "channel_y",
        label: "Channel Y",
        kind: "enum-short",
        options: CHANNELS,
        defaultValue: "G",
      },
      {
        key: "distortion_scope",
        label: "Scope",
        kind: "enum-short",
        options: DISTORTION_SCOPES,
        defaultValue: "background-only",
      },
    ],
  },
  {
    key: "blur",
    label: "Blur & Edge",
    referenceSection: "§ D. Blur / Fuzzing / Edge Softness",
    tooltip:
      "Gaussian blur, morphology operations, drop shadow, and fuzz mask controls.",
    knobs: [
      {
        key: "gaussian_blur",
        label: "Gaussian Blur",
        kind: "enum-short",
        options: GAUSSIAN_BLURS,
        defaultValue: "0",
      },
      {
        key: "morphology",
        label: "Morphology",
        kind: "enum-short",
        options: MORPHOLOGIES,
        defaultValue: "none",
      },
      {
        key: "drop_shadow",
        label: "Drop Shadow",
        kind: "enum-short",
        options: DROP_SHADOWS,
        defaultValue: "off",
      },
      {
        key: "fuzz_mask",
        label: "Fuzz Mask",
        kind: "enum-short",
        options: FUZZ_MASKS,
        defaultValue: "off",
      },
    ],
  },
  {
    key: "color",
    label: "Color & Palette",
    referenceSection: "§ E. Color / Palette",
    tooltip:
      "Palette family, number of colors, contrast, saturation, and luminance bias.",
    knobs: [
      {
        key: "palette_family",
        label: "Palette",
        kind: "enum-short",
        options: PALETTE_FAMILIES,
        defaultValue: "warm",
      },
      {
        key: "palette_cardinality",
        label: "Color Count",
        kind: "enum-short",
        options: PALETTE_CARDINALITIES,
        defaultValue: "2",
      },
      {
        key: "contrast_band",
        label: "Contrast",
        kind: "enum-short",
        options: CONTRAST_BANDS,
        defaultValue: "mid",
      },
      {
        key: "saturation_band",
        label: "Saturation",
        kind: "enum-short",
        options: SATURATION_BANDS,
        defaultValue: "balanced",
      },
      {
        key: "luminance_bias",
        label: "Luminance",
        kind: "enum-short",
        options: LUMINANCE_BIASES,
        defaultValue: "balanced",
      },
    ],
  },
  {
    key: "blending",
    label: "Blending",
    referenceSection: "§ F. Blending / Compositing",
    tooltip:
      "Layer blend modes, opacity stacking strategy, and compositing operator.",
    knobs: [
      {
        key: "blend_mode_primary",
        label: "Primary Blend",
        kind: "enum-long",
        options: BLEND_MODES_PRIMARY,
        defaultValue: "normal",
      },
      {
        key: "blend_mode_secondary",
        label: "Secondary Blend",
        kind: "enum-short",
        options: BLEND_MODES_SECONDARY,
        defaultValue: "none",
      },
      {
        key: "opacity_stack",
        label: "Opacity Stack",
        kind: "enum-long",
        options: OPACITY_STACKS,
        defaultValue: "flat(1.0)",
      },
      {
        key: "composite_op",
        label: "Composite Op",
        kind: "enum-short",
        options: COMPOSITE_OPS,
        defaultValue: "over",
      },
    ],
  },
  {
    key: "texture",
    label: "Texture & Motion",
    referenceSection: "§ G. Motion-Like Texture (Static Illusion)",
    tooltip:
      "Directional flow, frequency jitter, and phase offset for implied motion.",
    knobs: [
      {
        key: "directionality",
        label: "Directionality",
        kind: "enum-short",
        options: DIRECTIONALITIES,
        defaultValue: "none",
      },
      {
        key: "frequency_jitter",
        label: "Freq Jitter",
        kind: "enum-short",
        options: FREQUENCY_JITTERS,
        defaultValue: "none",
      },
      {
        key: "phase_offset",
        label: "Phase Offset",
        kind: "enum-short",
        options: PHASE_OFFSETS,
        defaultValue: "0",
      },
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

// ---------------------------------------------------------------------------
// Seeded random utility
// Simple LCG — not cryptographic, purely for deterministic UI scenario generation.
// ---------------------------------------------------------------------------

export function makeSeededRandom(seed: number) {
  let s = seed >>> 0
  return (): number => {
    s = (Math.imul(1664525, s) + 1013904223) >>> 0
    return s / 0x100000000
  }
}

// NOTE: arr is typed as readonly T[] rather than readonly [T, ...T[]] because
// PAIRWISE_DOMAINS values are readonly string[] (no non-empty tuple guarantee).
// The as T cast is safe here — all call sites pass non-empty arrays.
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
  const out: KnobState = { ...base, style_family: family }

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

function applyHeroOverride(
  base: KnobState,
  family: StyleFamily,
  rng: () => number,
): KnobState {
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

function applySafeOverride(
  base: KnobState,
  family: StyleFamily,
  rng: () => number,
): KnobState {
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

  // Mirrors Python build_generation_plan: safe tier restricts to conservative families only.
  const SAFE_FAMILIES: StyleFamily[] = ["minimal", "diagrammatic", "geometric"]
  const families =
    tier === "safe"
      ? input.families.filter((f) => SAFE_FAMILIES.includes(f)).length > 0
        ? input.families.filter((f) => SAFE_FAMILIES.includes(f))
        : SAFE_FAMILIES
      : input.families.length > 0
        ? input.families
        : [...STYLE_FAMILIES]

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
