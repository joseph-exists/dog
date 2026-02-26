# Dataset Storyboard Scope

Last updated: February 17, 2026

## Objective

Define the first implementation slice for `dataset_storyboard.py`: ingest a real dataset and generate a deterministic, multi-scene explanatory visual sequence using the established render/report contract.

## Proposed Deliverable

- New script: `examples-other/data/storyboard/dataset_storyboard.py`
- Optional runner (if needed for scenario sweeps): `examples-other/data/storyboard/dataset_storyboard_runner.py`
- Outputs:
  - One static storyboard SVG per scenario
  - Optional animation variant (gif/mp4) in a later increment
  - Per-run JSON report metadata and aggregate hook summary

## Additional Potential Deliverables

1. Advance next-phase physics/event work from RFC scaffolding into additional example coverage.
2. Expand deterministic regression coverage where high-impact parameter toggles are still untested.


## Contract Alignment (Must Reuse Existing Pattern)

- Use `RenderConfig` + `render_scene(...)` or `render_batch(...)` only.
- Use deterministic configuration:
  - `TimingSpec(seed=...)`
  - explicit width/height
- Use report plumbing:
  - `report_json_path` for per-output report artifacts
  - `report_hook` for aggregate summary capture
- Ensure output naming follows render API policy (no ad hoc suffix logic).

## Phase 1 Scope (Recommended)

Data ingestion:

- Accept CSV input path (`--input-csv`) and optional synthetic fallback mode.
- Parse wide/long tabular data with explicit schema expectations.
- Validate required columns and emit actionable errors.

Scene model:

- Scene A: dataset profile (coverage, missingness, key dimensions)
- Scene B: small multiples breakdown (group/time/category)
- Scene C: annotated callouts (top deltas/outliers/drivers)

Rendering:

- Generate 3 canvases (one per scene) and output via `render_batch(...)`.
- Uniform visual frame: title, subtitle, notation panel.
- Deterministic styling from seed.

Reporting:

- Per-scene report JSON via `report_json_path`.
- Aggregate summary JSON via `report_hook` capture.
- Include `config_fingerprint`, seed, source dataset metadata.

## CLI Contract (Draft)

- `--input-csv <path>`: source dataset path
- `--mode {csv,synthetic}`: data source mode
- `--seed <int>`: deterministic seed
- `--width <int>`
- `--height <int>`
- `--output-prefix <path>`
- `--report-dir <path>`: per-scene reports
- `--summary-report <path>`: aggregate report
- `--format {svg}` (Phase 1 static-only)

## Parameter Parity and Granularity Gates

- Preserve high-value knobs in namespaced form:
  - `data.*`: filters, grouping keys, normalization
  - `scene.*`: scene enable/disable, callout density
  - `style.*`: label density, contrast mode, annotation size
  - `export.*`: output/report behavior
- No-lost-knobs gate for each migration increment:
  - old param
  - new mapping
  - status (`preserved`, `aliased`, `deprecated`)

## Acceptance Criteria (Phase 1)

- Script renders all storyboard scenes with one deterministic command.
- Output contract fully uses render API (no script-level output coercion).
- Repeated run with same seed produces stable artifact hash.
- Per-scene and aggregate report artifacts are generated and valid JSON.
- Reference docs include run examples and output contract notes.

## Out of Scope (Phase 1)

- Interactive controls/knobs UI
- Multi-user annotations
- MP4 timeline with scene transitions (defer to Phase 2)
- Automated narrative text generation

## Risks and Mitigations

- Risk: Dataset schema variance causes fragile scenes.
  - Mitigation: strict schema validation + clear errors + synthetic fallback.
- Risk: Storyboard becomes over-opinionated for one dataset shape.
  - Mitigation: scene templates accept configurable grouping/key fields.
- Risk: Contract drift from current render/report API.
  - Mitigation: enforce render API usage in tests and parity checklist.

## First Execution Plan

1. Create `dataset_storyboard.py` skeleton with CLI + data validation. [completed]
2. Implement Scene A profile canvas. [completed]
3. Implement Scene B small multiples canvas. [completed]
4. Implement Scene C callout canvas. [completed]
5. Wire `render_batch(...)` + report hooks. [completed]
6. Add deterministic regression smoke test and docs entry. [completed]

## Acceptance Status (Phase 1)

- [x] Script renders all storyboard scenes with one deterministic command.
- [x] Output contract fully uses render API (no script-level output coercion).
- [x] Repeated run with same seed produces stable artifact hash.
- [x] Per-scene and aggregate report artifacts are generated and valid JSON.
- [x] Reference docs include run examples and output contract notes.

## Current Status

- Implemented: `examples-other/data/storyboard/dataset_storyboard.py`
- Implemented:
  - CSV/synthetic ingest + schema validation
  - Scene A profile render
  - Scene B small multiples render
  - Scene C annotated callouts render
  - `RenderConfig` + `render_batch(...)` contract wiring
  - Per-scene JSON report + summary report hook output
  - Deterministic regression test:
    - `tests/test_dataset_storyboard_regression.py`
- Documented in:
  - `examples-other/reference/index.md`
- Cross-referenced in:
  - `examples-other/closed-API-implementation-plan.md`
  - `examples-other/api_migration_backlog.md`
