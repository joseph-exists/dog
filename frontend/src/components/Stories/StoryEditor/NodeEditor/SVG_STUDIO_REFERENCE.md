# SVG Studio Reference Card

## Attribution
Recommended credit line for gallery entries derived from this work:

`Co-created by the Dog team with Codex (GPT-5) assistance.`

If you want stricter provenance, add optional metadata fields in gallery records:
- `author_human`
- `author_ai_assist`
- `source_node_id`
- `source_story_id`
- `generation_notes`

## What Exists Today
Primary implementation lives in:
- `frontend/src/components/Stories/StoryEditor/NodeEditor/NodeEditorForm.tsx`

Core capabilities:
- Multi-tab node creative studio (`Compose`, `Design`, `SVG Studio`, `Preview`, `Inspect`)
- Layered SVG composition with per-layer transforms
- Blend modes and filter chains
- Preset + custom filter primitive pipeline
- Apply planner with merge modes:
  - `replace`
  - `prepend`
  - `append`
  - `background` wrapper (MDX `div style={{ backgroundImage: ... }}`)
- Before/After apply panel
- Save/Reload + dirty patch sync behavior

## Mental Model
The node still has one content payload:
- `content`
- `content_format`

`SVG Studio` does not store separate backend layer state yet.
It generates output and applies that output into node content.

Implication:
- Treat Studio as a composer + writer into node body.
- Use apply planner modes to avoid destructive authoring.

## Key Extension Points
Inside `NodeEditorForm.tsx`, these are the main hooks/functions to evolve:

- `SvgLayer`, `LayerFilterStep` types
  - Extend layer model (z-index lock, masks, tags, animation params).

- `filterDefForLayer(...)`
  - Controls how filter step chains compile to `<filter>` defs.
  - Add primitive-specific validation and defaults here.

- `buildCompositeSvg(...)`
  - Controls final composed SVG + layer ordering.
  - Good place for clipping/masking/group-level effects.

- `buildSvgApplyPlan(...)`
  - Governs `replace/prepend/append/background` semantics.
  - Add future modes here (`overlay`, `underlay`, `slot`/`region` targeting).

- `convertNodeBodyToMdx(...)`
  - Safe conversion layer for non-MDX formats.
  - Improve preserving semantics for `json/code/image` when merging.

## Safe Changes Checklist
When extending Studio:
1. Preserve node save semantics (`mutateNode`, dirty patch behavior).
2. Keep apply plan preview truthful (before/after must match actual mutation).
3. Confirm `content_format` transitions are explicit and expected.
4. Typecheck after each extension.
5. Validate MDX output for parser safety (`className`, JSX comments, no HTML comments).

## Creative Extensions (High-Value Next)
1. Filter UX
- Primitive-specific forms (instead of raw attrs) for:
  - `feColorMatrix`
  - `feTurbulence`
  - `feDisplacementMap`
- Live validation warnings for malformed attributes.

2. Reusable Assets
- Save/load `Layer Presets` and `Filter Recipes`.
- Node-local “recent composites” list.

3. Gallery Integration
- Export payload shape:
  - `composite_svg`
  - `mdx_wrapper`
  - `layer_manifest` (JSON)
  - `thumbnail_data_url`
- Add import path to instantiate Studio from gallery artifact.

4. Collaboration and Provenance
- Save generation metadata (`source`, `author`, `timestamp`, `model-assist`).
- Track derivations (`derived_from_gallery_asset_id`).

5. Future Node Model
- Move visual state to dedicated metadata (e.g., `metadata_json.presentation.svg_layers`)
  while still compiling to renderable content for runtime compatibility.

## Known Constraints
- `svg` target is replace-oriented by nature.
- Merge behavior is currently MDX-centric for non-destructive composition.
- Layer state is UI-local unless explicitly exported/applied.

## Suggested Engineer Workflow
1. Reproduce in `SVG Studio` tab.
2. Inspect `buildSvgApplyPlan(...)` outcome.
3. Verify mutation payload in `Inspect` tab.
4. Confirm node render output in `Preview` tab.
5. Run `npm run typecheck` in `frontend`.

