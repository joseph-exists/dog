# SVG Combinatorics Reference Card

Purpose: generate a broad, curated SVG library (target ~10k assets) with strong visual diversity while staying compatible with `NodeEditor`/`ContentRenderer`.

## 1) Generation Strategy
Use a two-stage approach:

1. Pairwise coverage plan
- Build a small finite domain for each major knob.
- Generate a pairwise set over those domains (instead of full Cartesian explosion).
- Ensure every pair of parameter values appears together at least once.

2. Style family quotas
- Partition runs into families (`organic`, `geometric`, `glitch`, `minimal`, `atmospheric`, `diagrammatic`).
- Enforce per-family quotas so pairwise does not collapse into one visual mode.

## 2) Core Knob Domains (Pairwise Inputs)
Use these as starter domains. Keep values discrete for pairwise tooling.

### A. Geometry/Base Composition
- `shape_family`: `curves`, `polygons`, `rings`, `stripes`, `particles`
- `layer_count`: `1`, `2`, `4`, `6`
- `density`: `sparse`, `medium`, `dense`
- `symmetry`: `none`, `radial`, `mirror-x`, `mirror-y`
- `viewbox`: `square(1024)`, `landscape(1366x768)`, `portrait(768x1366)`

### B. Turbulence / Noise
- `turbulence_type`: `fractalNoise`, `turbulence`
- `base_frequency`: `0.003`, `0.01`, `0.03`, `0.08`
- `num_octaves`: `1`, `2`, `4`, `6`
- `seed_bucket`: `0-99`, `100-999`, `1000-9999`
- `stitch_tiles`: `stitch`, `noStitch`

### C. Displacement / Distortion
- `displacement_scale`: `0`, `8`, `24`, `64`, `120`
- `channel_x`: `R`, `G`, `B`, `A`
- `channel_y`: `R`, `G`, `B`, `A`
- `distortion_scope`: `background-only`, `subject-only`, `global`

### D. Blur / Fuzzing / Edge Softness
- `gaussian_blur`: `0`, `0.8`, `2`, `6`, `14`
- `morphology`: `none`, `erode(1)`, `dilate(1)`, `dilate(3)`
- `drop_shadow`: `off`, `subtle`, `strong`
- `fuzz_mask`: `off`, `low`, `high`

### E. Color / Palette
- `palette_family`: `warm`, `cool`, `duotone`, `neon`, `earth`, `mono`
- `palette_cardinality`: `1`, `2`, `4`, `6`
- `contrast_band`: `low`, `mid`, `high`
- `saturation_band`: `desat`, `balanced`, `vivid`
- `luminance_bias`: `dark`, `balanced`, `light`

### F. Blending / Compositing
- `blend_mode_primary`: `normal`, `multiply`, `screen`, `overlay`, `darken`, `lighten`
- `blend_mode_secondary`: `none`, `multiply`, `screen`, `overlay`
- `opacity_stack`: `flat(1.0)`, `stepped(1/0.7/0.4)`, `mist(0.15-0.55)`
- `composite_op`: `over`, `in`, `out`, `atop`, `xor`

### G. Motion-Like Texture (Static Illusion)
- `directionality`: `none`, `horizontal`, `vertical`, `diagonal`, `radial`
- `frequency_jitter`: `none`, `low`, `high`
- `phase_offset`: `0`, `0.25`, `0.5`, `0.75`

## 3) Pairwise Execution Recipe
1. Define the above knobs in a machine-readable manifest (`json`/`yaml`).
2. Mark hard constraints (invalid pairs) before generation.
3. Use pairwise generator to output scenario rows.
4. For each row:
- derive deterministic RNG seed from row id
- render SVG
- run validator + sanitizer
- store SVG + manifest metadata

Recommended metadata fields per artifact:
- `asset_id`, `scenario_id`, `seed`, `family`
- all knob values
- `bytes`, `element_count`, `filter_count`, `has_turbulence`, `has_displacement`
- `dominant_colors`, `contrast_score`, `complexity_score`

## 4) Hard Constraints (Compatibility/Safety)
- Single `<svg>` root with `viewBox`
- No scripts/event handlers/foreignObject/external refs
- Namespaced IDs and rewritten `url(#...)` refs
- Size target `<100KB`, hard cap `<250KB`
- Element cap (example): `<2000`
- Filter chain cap (example): `<=12 primitives` total, `<=2` heavy primitives (`feTurbulence`, `feDisplacementMap`, `feConvolveMatrix`)

## 5) Diversity Guardrails
Add post-generation checks so 10k assets are not near-duplicates:
- Perceptual hash distance threshold
- Histogram distance threshold (color + edge)
- Structural distance (node/filter signature)
- Cap assets per near-identical cluster

## 6) Suggested Coverage Targets
For 10k output:
- `70%` pairwise core set (broad coverage)
- `20%` curated “hero” extremes (high drama)
- `10%` safe/minimal utility backgrounds

## 7) Creative Extension Ideas
- Palette-conditioned turbulence presets (e.g. "aurora", "smoke", "plasma")
- Semantic tags generated from knobs (`organic`, `calm`, `aggressive`, `noisy`, `diagrammatic`)
- Auto-generate MDX background wrapper snippets from each asset for one-click Node import

## 8) Minimal Starter Families
If you need a quick first batch:
- `mist-field`: low-frequency turbulence + screen blend + cool palette
- `signal-glitch`: medium displacement + overlay + neon duotone
- `paper-grain`: subtle noise + multiply + warm desaturated palette
- `vector-rings`: radial symmetry + low blur + high contrast
- `soft-gradient`: no displacement + low complexity + utility-safe

