# SVG Interface Spec MVP

## Context

This spec defines the first concrete frontend-to-backend interface for the SVG steel thread.

It is intentionally narrow and designed to prove one reliable path:

- user selects a curated visualization interface
- user adjusts a small set of parameters
- frontend submits the request to `dog`
- `dog` submits a render job to `tesser`
- `tesser` renders the SVG
- `tesser` posts the completed SVG to the existing API/storage layer
- the stored SVG reference flows back through job status to the frontend

This spec covers three selected surfaces:

1. `design_patterns_gallery`
2. `static_data_lineage_map`
3. `tufte_small_multiples`

## Assumptions

- The frontend allowlist is curated and hardcoded for now.
- The backend contract is owned by `dog`, not by the frontend directly.
- `tesser` should no longer inline or stream SVG back for this flow.
- Instead, `tesser` posts the SVG to the existing API/storage layer and returns an artifact reference.
- The queued async job path is the default execution model, even for SVG.

## MVP Catalog

The frontend should present five user-facing interfaces.

These are curated interfaces, not raw script IDs.

| Interface ID | User Title | Backing Script | Notes |
|---|---|---|---|
| `pattern.state_chart` | State Chart | `examples.static.core.design_patterns_gallery` | recipe-backed |
| `pattern.timeline` | Timeline | `examples.static.core.design_patterns_gallery` | recipe-backed |
| `pattern.network_diagnostics` | Network Diagnostics | `examples.static.core.design_patterns_gallery` | recipe-backed |
| `lineage.data_map` | Data Lineage Map | `examples.static.lineage.static_data_lineage_map` | domain-shaped SVG |
| `analytics.tufte_small_multiples` | Tufte Small Multiples | `examples.data.tufte.tufte_small_multiples` | bridge surface for SVG now, animation later |

## Frontend Catalog Record Shape

Recommended catalog entry fields:

- `id`
- `title`
- `description`
- `scriptId`
- `surface`
- `outputType`
- `complexity`
- `starterFields`
- `advancedFields`
- `defaultParams`
- `tags`
- `status`

Recommended meanings:

- `surface`: `pattern`, `lineage`, or `analytics`
- `outputType`: `svg`
- `complexity`: `starter`, `intermediate`
- `status`: `active`

## User Interaction Model

Each interface should use progressive elaboration with three levels.

### Level 1: Starter

Visible by default.

Purpose:

- help most users succeed quickly
- prevent overwhelming forms

### Level 2: Advanced

Collapsed by default.

Purpose:

- expose meaningful tuning without requiring an expert mode

### Level 3: Request Preview

Read-only by default.

Purpose:

- show the exact effective request and equivalent command shape
- support trust, debugging, and reproducibility

The frontend should show:

- a simple form first
- the generated request payload second
- an equivalent command preview third

## Interface 1: State Chart

### Catalog Entry

- `id`: `pattern.state_chart`
- `title`: `State Chart`
- `scriptId`: `examples.static.core.design_patterns_gallery`
- `surface`: `pattern`
- `outputType`: `svg`

### Starter Fields

- `preset`
- `width`
- `height`
- `seed`

### Advanced Fields

- none for MVP beyond starter fields

### Fixed Backend Parameters

- `recipes=state_chart`
- `format=svg`

### Default Params

- `preset=balanced`
- `width=1280`
- `height=720`
- `seed=71`

## Interface 2: Timeline

### Catalog Entry

- `id`: `pattern.timeline`
- `title`: `Timeline`
- `scriptId`: `examples.static.core.design_patterns_gallery`
- `surface`: `pattern`
- `outputType`: `svg`

### Starter Fields

- `preset`
- `width`
- `height`
- `seed`

### Advanced Fields

- none for MVP beyond starter fields

### Fixed Backend Parameters

- `recipes=timeline`
- `format=svg`

### Default Params

- `preset=balanced`
- `width=1280`
- `height=720`
- `seed=71`

## Interface 3: Network Diagnostics

### Catalog Entry

- `id`: `pattern.network_diagnostics`
- `title`: `Network Diagnostics`
- `scriptId`: `examples.static.core.design_patterns_gallery`
- `surface`: `pattern`
- `outputType`: `svg`

### Starter Fields

- `preset`
- `width`
- `height`
- `seed`

### Advanced Fields

- none for MVP beyond starter fields

### Fixed Backend Parameters

- `recipes=network`
- `format=svg`

### Default Params

- `preset=network_review`
- `width=1360`
- `height=780`
- `seed=83`

## Interface 4: Data Lineage Map

### Catalog Entry

- `id`: `lineage.data_map`
- `title`: `Data Lineage Map`
- `scriptId`: `examples.static.lineage.static_data_lineage_map`
- `surface`: `lineage`
- `outputType`: `svg`

### Starter Fields

- `scenario`
- `policy`
- `seed`

### Advanced Fields

- `corruptionInjection`
- `freshnessDecay`
- `schemaDrift`
- `worldWidth`
- `worldHeight`
- `layoutIterations`

### Default Params

- `scenario=late_arrivals`
- `policy=balanced`
- `seed=227`
- `worldWidth=2200`
- `worldHeight=1400`
- `layoutIterations=220`

### Allowed Starter Values

`scenario`:

- `late_arrivals`
- `schema_break`
- `source_corruption`
- `upstream_outage`

`policy`:

- `strict`
- `balanced`
- `fast`

## Interface 5: Tufte Small Multiples

### Catalog Entry

- `id`: `analytics.tufte_small_multiples`
- `title`: `Tufte Small Multiples`
- `scriptId`: `examples.data.tufte.tufte_small_multiples`
- `surface`: `analytics`
- `outputType`: `svg`

### Starter Fields

- `panels`
- `columns`
- `series`
- `seed`

### Advanced Fields

- `points`
- `events`
- `width`
- `height`

### Hidden MVP Fields

For the first SVG-only pass, keep these fixed and do not expose them in the form:

- `format=svg`
- `animate=false`
- `duration=8.0`
- `fps=24`

### Default Params

- `panels=8`
- `columns=4`
- `series=3`
- `seed=97`
- `points=48`
- `events=3`
- `width=1900`
- `height=1180`

## Frontend Submission Contract

The frontend should submit a normalized request to `dog`.

Recommended request shape:

- `interfaceId`
- `requestId`
- `params`
- `uiContext`

Recommended meanings:

- `interfaceId`: selected curated interface
- `requestId`: client-generated or backend-generated request correlation id
- `params`: normalized effective user parameters
- `uiContext`: optional metadata such as user/session/source page

## Example Conceptual Request Shapes

### State Chart

- `interfaceId`: `pattern.state_chart`
- `params`:
  - `preset=balanced`
  - `width=1280`
  - `height=720`
  - `seed=71`

### Data Lineage Map

- `interfaceId`: `lineage.data_map`
- `params`:
  - `scenario=late_arrivals`
  - `policy=balanced`
  - `seed=227`

### Tufte Small Multiples

- `interfaceId`: `analytics.tufte_small_multiples`
- `params`:
  - `panels=8`
  - `columns=4`
  - `series=3`
  - `seed=97`

## `dog` Backend Translation Contract

`dog` should own the mapping from curated interface to `tesser` script request.

The frontend should not know:

- raw script ids
- worker/runtime profile details
- storage upload details
- output path details

The backend should map each interface into:

- `script_id`
- `formats=["svg"]`
- `params`
- `request_id`
- output and callback metadata as needed by `tesser`

### Required Translation Rules

#### `pattern.state_chart`

Maps to:

- `script_id=examples.static.core.design_patterns_gallery`
- `params.recipes=state_chart`
- `params.format=svg`

#### `pattern.timeline`

Maps to:

- `script_id=examples.static.core.design_patterns_gallery`
- `params.recipes=timeline`
- `params.format=svg`

#### `pattern.network_diagnostics`

Maps to:

- `script_id=examples.static.core.design_patterns_gallery`
- `params.recipes=network`
- `params.format=svg`

#### `lineage.data_map`

Maps to:

- `script_id=examples.static.lineage.static_data_lineage_map`
- `params.format=svg`

#### `analytics.tufte_small_multiples`

Maps to:

- `script_id=examples.data.tufte.tufte_small_multiples`
- `params.format=svg`
- `params.animate=false`

## Storage/Artifact Contract

Because SVG will now be posted to the existing API/storage layer, the completion contract should center on an asset reference, not inline SVG.

### Required Completion Data

Each completed job should resolve to:

- `jobId`
- `status`
- `scriptId`
- `interfaceId`
- `artifactType=svg`
- `svgAssetId`
- `svgUrl`
- `storageStatus`
- optional render metadata

Recommended render metadata:

- `width`
- `height`
- `format`
- `requestId`
- `configFingerprint`
- script-specific summary if available

## Suggested End-to-End Async Flow

1. Frontend loads the curated interface list.
2. User selects one interface.
3. Frontend shows starter controls.
4. User optionally opens advanced controls.
5. Frontend shows request preview.
6. User presses `Run`.
7. Frontend submits the request to `dog`.
8. `dog` maps the interface to a `tesser` job request and submits it.
9. `tesser` enqueues the render job.
10. Worker executes the render.
11. Worker or completion handler posts the SVG to the storage API.
12. Storage API returns `svgAssetId` and `svgUrl`.
13. Job status is updated with the stored SVG reference.
14. Frontend polls or subscribes for status updates.
15. Frontend renders the completed SVG via `svgUrl`.

## Recommended Job States

Suggested visible states:

- `draft`
- `submitting`
- `queued`
- `running`
- `uploading`
- `completed`
- `failed`

`uploading` is useful now because storage is part of the success path.

## Request Preview Requirements

The frontend should show two read-only representations before submit.

### Request JSON Preview

Purpose:

- confirms the actual request the backend will send
- reduces ambiguity

### Equivalent Command Preview

Purpose:

- helps operators and power users
- creates easy reproducibility

For MVP, the command preview can be approximate as long as it is faithful to the selected params.

## Validation Rules

### General

- only allow approved interface ids
- clamp widths and heights to reasonable bounds
- reject unknown params at the `dog` boundary

### `design_patterns_gallery` Interfaces

- `preset` must be one of the supported preset names
- width and height must be positive integers
- seed must be an integer

### `lineage.data_map`

- scenario and policy must be from known allowlists
- override floats must be numeric when provided

### `analytics.tufte_small_multiples`

- panels, points, columns, series, and events must be positive integers
- format is fixed to `svg`
- animate is fixed to `false` for MVP

## Why This Shape Fits The Project

This interface shape matches the current structure well because:

- it respects the current script contracts instead of inventing new ones
- it keeps the frontend simple and curated
- it puts orchestration and translation inside `dog`
- it keeps `tesser` responsible for rendering work
- it aligns with the queue-based worker model already present
- it adapts cleanly to stored SVG artifacts instead of inline returns

## Recommended Next Step

If this spec looks right, the next useful artifact should be:

- a backend mapping table that defines the exact `interfaceId -> script request` transformation

That would be the implementation-facing companion to this frontend/interface spec.
