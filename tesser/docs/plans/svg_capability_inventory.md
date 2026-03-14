# SVG Capability Inventory

## Context

This document narrows the current `tesser` and `tesserax` review to one milestone:

- identify the scripts that can generate SVG today
- identify which of those are good candidates for a first-pass frontend allowlist
- provide a lightweight reference for creating new SVG-oriented scripts directly with `tesserax`

This is intentionally MVP-oriented. It assumes a temporary frontend allowlist is acceptable while deeper questions about richer service discovery and non-SVG artifact delivery remain open.

## Scope

This inventory focuses on:

- registered and enabled scripts that support SVG output
- SVG-capable scripts that are relevant to a frontend request/response flow
- direct `tesserax` SVG generation patterns already used in this repository

This inventory does not attempt to solve:

- GIF/MP4 productization
- artifact-serving strategy for non-SVG outputs
- long-term service catalog design

## Current SVG-Capable Registered Scripts

The following registered scripts are enabled and advertise SVG support today.

| Script ID | Source Path | Kind | Runtime | SVG Shape | Notes |
|---|---|---|---|---|---|
| `examples.static.core.simple_convolution` | `src/tesserax_service/scripts/examples-other/static/core/simple_convolution.py` | static | core | single SVG | simplest baseline |
| `examples.static.core.advanced_examples` | `src/tesserax_service/scripts/examples-other/static/core/advanced_examples.py` | static | core | multi-file SVG batch | more of a showcase than a single frontend render |
| `examples.static.core.design_patterns_gallery` | `src/tesserax_service/scripts/examples-other/static/core/design_patterns_gallery.py` | static | core | multi-file SVG batch | strongest preset-driven catalog candidate |
| `examples.static.core.neural_network_refined` | `src/tesserax_service/scripts/examples-other/static/core/neural_network_refined.py` | static | core | one or two SVG files | richer stress-test surface |
| `examples.static.lineage.static_data_lineage_map` | `src/tesserax_service/scripts/examples-other/static/lineage/static_data_lineage_map.py` | static | core | single SVG | parameterized and frontend-friendly |
| `examples.data.tufte.tufte_small_multiples` | `src/tesserax_service/scripts/examples-other/data/tufte/tufte_small_multiples.py` | static | core | single SVG | also supports animation formats |
| `examples.data.tufte.tufte_small_multiples_extended` | `src/tesserax_service/scripts/examples-other/data/tufte/tufte_small_multiples_extended.py` | static | core | single SVG | richer analytical static surface |

## Non-Registered But Relevant SVG-Capable Script

The following script appears relevant to the SVG milestone even though it is not currently enabled as a render job:

| Script ID | Source Path | Current Classification | Why It Matters |
|---|---|---|---|
| `examples.data.storyboard.dataset_storyboard` | `src/tesserax_service/scripts/examples-other/data/storyboard/dataset_storyboard.py` | utility | it produces SVG scene outputs and may become a strong product-facing capability later |

## Script-by-Script Notes

### `examples.static.core.simple_convolution`

Purpose:
- Minimal matrix/convolution-style SVG example
- Good baseline for verifying the frontend request-to-SVG-return path

Characteristics:
- Fixed output file
- No exposed CLI parameters
- Low ambiguity

MVP suitability:
- Excellent

Why:
- very small surface area
- predictable output
- easy smoke-test candidate

### `examples.static.core.advanced_examples`

Purpose:
- Showcase of several advanced static rendering capabilities
- Produces multiple outputs in one run

Characteristics:
- batch-oriented
- more exploratory than product-shaped
- useful as an internal demonstration of breadth

MVP suitability:
- Low

Why:
- multiple outputs are awkward for a simple frontend request/response flow
- better suited to internal review or operator tooling

### `examples.static.core.design_patterns_gallery`

Purpose:
- Curated gallery of reusable diagram recipes
- Includes preset-driven parameter handling and structured outputs

Characteristics:
- multi-output batch
- explicit parameter schema
- strong conceptual fit for frontend selection

MVP suitability:
- High, with one caveat

Why:
- it already behaves like a small catalog
- it is structured enough to support named frontend choices

Caveat:
- it produces multiple SVGs via output prefix rather than one single SVG per request
- for MVP, it may be better treated as several named frontend options rather than one generic script

### `examples.static.core.neural_network_refined`

Purpose:
- More complex neural-network-oriented SVG rendering
- Stress-tests composition and richer topology

Characteristics:
- supports multiple output variants depending on mode
- higher complexity than the simplest frontend options

MVP suitability:
- Medium

Why:
- useful if neural/ML diagrams are a near-term use case
- otherwise probably better as a second-wave SVG option

### `examples.static.lineage.static_data_lineage_map`

Purpose:
- Static lineage and data-risk map with scenario and policy controls

Characteristics:
- single SVG output
- explicit user-facing parameters
- deterministic and easy to explain

MVP suitability:
- Excellent

Why:
- looks like a real product capability rather than just a demo
- parameter shape already maps cleanly to a frontend form

### `examples.data.tufte.tufte_small_multiples`

Purpose:
- Tufte-inspired small multiples with optional animation path

Characteristics:
- supports `svg`, `gif`, and `mp4`
- can be used as a static SVG example without enabling animation
- broader parameter surface than the simplest static examples

MVP suitability:
- Medium

Why:
- useful if analytical dashboards and report graphics matter now
- but it introduces conceptual overlap with later animation work

### `examples.data.tufte.tufte_small_multiples_extended`

Purpose:
- Richer analytical small multiples with synthetic or external data

Characteristics:
- SVG-only in its current interface
- stronger data-driven story than the simpler Tufte script
- broader input surface than the minimal examples

MVP suitability:
- High for operator/internal use, Medium for first frontend release

Why:
- good long-term SVG candidate
- may be a little heavy for the smallest possible first pass

### `examples.data.storyboard.dataset_storyboard`

Purpose:
- Dataset profile and storyboard scenes

Characteristics:
- currently classified as utility
- produces SVG scene outputs via batch rendering
- carries meaningful report and summary structure

MVP suitability:
- Not first pass, but strategically important

Why:
- it looks like a likely future product capability
- but it is not yet classified as a simple render job

## Recommended MVP Frontend Allowlist

For a hardcoded first pass, I recommend starting with the smallest set that proves different kinds of SVG value without overloading the frontend.

### Tier 1: Strong First-Pass Candidates

| Frontend Name | Script ID | Why Include It |
|---|---|---|
| Simple Convolution | `examples.static.core.simple_convolution` | easiest end-to-end SVG smoke test |
| Data Lineage Map | `examples.static.lineage.static_data_lineage_map` | strongest “real use case” static render |
| Design Patterns: State Chart | `examples.static.core.design_patterns_gallery` | useful pattern-oriented starter if frontend maps recipe choices explicitly |
| Design Patterns: Timeline | `examples.static.core.design_patterns_gallery` | same as above |
| Design Patterns: Network | `examples.static.core.design_patterns_gallery` | same as above |

Recommended interpretation:

- do not expose `design_patterns_gallery` as a generic batch script at first
- instead, treat its recipes as separate frontend options backed by the same script

### Tier 2: Good Next Additions

| Frontend Name | Script ID | Why Add Later |
|---|---|---|
| Neural Network Refined | `examples.static.core.neural_network_refined` | richer but more specialized |
| Tufte Small Multiples Extended | `examples.data.tufte.tufte_small_multiples_extended` | strong analytical SVG surface |
| Tufte Small Multiples | `examples.data.tufte.tufte_small_multiples` | useful, but overlaps with later animation questions |

### Scripts I Would Not Put In The First Frontend Allowlist

| Script ID | Reason |
|---|---|
| `examples.static.core.advanced_examples` | batch showcase, not a clean single user request |
| `examples.data.storyboard.dataset_storyboard` | likely important later, but not yet positioned as a simple render job |

## Suggested Frontend Record Shape For MVP

For the hardcoded frontend list, I would keep each option simple and explicit.

Suggested fields:

- `name`
- `scriptId`
- `description`
- `svgOnly`
- `inputMode`
- `defaultParams`
- `notes`

Example conceptual record shape:

- `name`: user-facing title
- `scriptId`: backend script id
- `description`: short explanation
- `svgOnly`: `true`
- `inputMode`: `none`, `preset`, or `form`
- `defaultParams`: small fixed parameter set
- `notes`: caveats such as “recipe-based” or “operator-facing”

## Reference: How To Create New SVG-Oriented Scripts In Tesserax

The current repository already points to a stable pattern for new SVG-capable scripts.

### Preferred Core Path

Use:

- `Canvas` for static composition
- `RenderConfig` for output contract
- `render_scene(target, config)` for a single SVG
- `render_batch(batch)` when one invocation intentionally creates multiple SVGs

Relevant core API:

- `RenderConfig`
- `ViewportSpec`
- `TimingSpec`
- `render_scene(...)`
- `render_batch(...)`

See:

- `src/tesserax/render.py`
- `src/tesserax/__init__.py`

### Recommended Single-SVG Script Shape

For a frontend-friendly static SVG script, the preferred shape is:

1. Parse a small parameter set.
2. Build a `Canvas`.
3. Add shapes, text, and layout primitives.
4. Call `render_scene(...)` with `RenderConfig(output_path=..., format="svg")`.
5. Print or return the resulting output path.

Good current reference files:

- `src/tesserax_service/scripts/examples-other/static/core/simple_convolution.py`
- `src/tesserax_service/scripts/examples-other/static/lineage/static_data_lineage_map.py`

### Recommended Multi-SVG Script Shape

If one invocation is intentionally a gallery or storyboard:

1. Build multiple `Canvas` targets.
2. Pair each target with its own `RenderConfig`.
3. Use `render_batch(...)`.
4. Treat the output as a batch-oriented tool, not as the default frontend request/response model.

Good current reference files:

- `src/tesserax_service/scripts/examples-other/static/core/design_patterns_gallery.py`
- `src/tesserax_service/scripts/examples-other/data/storyboard/dataset_storyboard.py`

### Good MVP Design Rules For New SVG Scripts

For this milestone, new SVG-oriented scripts should prefer:

- single SVG output
- `format="svg"` only
- small and explicit parameter surfaces
- deterministic defaults
- clear output naming
- no dependency on export extras unless truly needed

### Good Candidate Parameter Shapes

The easiest frontend path will come from scripts that use one of these patterns:

- fixed output, no params
- preset selector plus a few overrides
- small structured form such as scenario, policy, seed, width, height

Avoid first-pass frontend exposure for scripts that require:

- multiple output files by default
- ambiguous output naming
- external data paths unless the data source contract is already solved

## Near-Term Recommendation

For the next milestone, I recommend:

1. Hardcode a small SVG-only frontend allowlist.
2. Start with `simple_convolution`, `static_data_lineage_map`, and recipe-mapped entries from `design_patterns_gallery`.
3. Keep `neural_network_refined` and the Tufte scripts as second-wave SVG additions.
4. Defer `advanced_examples`, `dataset_storyboard`, and all non-SVG questions until the SVG flow is proven.

## Follow-On Work After Review

If this inventory looks right, the next useful artifact would be:

- a frontend allowlist spec with exact names, descriptions, and parameter defaults for each approved SVG option

That would give you a concrete list to store in the frontend while keeping the backend and broader capability questions separate.
