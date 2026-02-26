# Tesserax Integration Working Implementation Plan

Last updated: February 18, 2026

## Plan Status

- Status: Closed (Step 4 complete)
- Closeout date: February 18, 2026
- Closure basis:
  - All Week 1 and Week 2 checklist deliverables are complete.
  - API acceptance criteria and definition-of-done checks are complete.
  - Step 4 backlog items are complete, including render-result telemetry (`frame_count`/`duration`).
- Active follow-on planning is now tracked in:
  - `examples-other/dataset_storyboard_scope.md`
  - `docs-other/physics_event_hooks_rfc.md`

## Objective

Prepare Tesserax for deeper project integration by first stabilizing the rendering contract, then adding reusable motion primitives, then seeding integration-facing examples.

## Why This Sequence

1. Build the core rendering API first (`C`) to establish a stable contract for CLI/UI integration and future features.
2. Build path-follow/tangent orientation second (`B`) to unlock high-value animation capabilities on top of that contract.
3. Defer physics constraints/event hooks (`A`) until the API and motion primitives are stable, reducing rework and integration risk.
4. Start with `design_patterns_gallery.py` before `dataset_storyboard.py` to maximize onboarding value while keeping scope controlled.

## Timeline (2 Weeks)

## Cross-Priority Dependency Map (`C` -> `B` -> `A`)

- [x] Priority `C` (core rendering API) must complete first:
  - [x] Single render/export contract in core
  - [x] Shared validation, naming, deterministic behavior
  - [x] Example migrations proving no-loss parameter parity
- [x] Priority `B` (path-follow/tangent) depends on `C`:
  - [x] New path primitives exposed through stable API surface
  - [x] At least one migrated showcase consumes those primitives
  - [x] Behavior tests lock endpoint/orientation semantics
- [x] Priority `A` (physics constraints + event hooks) depends on `C` and `B`:
  - [x] Hook lifecycle attached to render contract (not script internals)
  - [x] Physics events align with timeline/path semantics where applicable
  - [x] Event payload contract and versioning policy agreed before implementation

## Week 1 (Feb 17 to Feb 23): Core Rendering API (`C`)

### Deliverable

A stable core API for fixed-output rendering, replacing script-level ad hoc behavior.

### Exit Criteria

- Migrated examples render equivalent outputs to baseline behavior.
- Core validation and output handling live in library API (not duplicated in scripts).
- API usage is documented with at least one migration example.
- Contract tests pass for config validation and output contract behavior.

### Checklist

- [x] Define API surface and naming:
  - [x] `RenderConfig` (or equivalent typed config object)
  - [x] `render_scene(...)`
  - [x] `render_batch(...)`
- [x] Define stable input contract:
  - [x] Width/height semantics
  - [x] FPS and duration semantics
  - [x] Format semantics (`svg`, `gif`, `mp4`, etc.)
  - [x] Output path and extension coercion rules
- [x] Centralize validation in core:
  - [x] Numeric bounds checks (fps > 0, duration > 0, dimensions > 0)
  - [x] Format compatibility checks
  - [x] Actionable exception messages
- [x] Centralize output behavior in core:
  - [x] Naming policy
  - [x] Overwrite policy
  - [x] Parent directory creation policy
- [x] Add deterministic options:
  - [x] Seed handling for repeatable runs
  - [x] Metadata capture for reproducibility
- [x] Add tests:
  - [x] Unit tests for config parsing/validation
  - [x] Unit tests for output path/format behavior
  - [x] At least one integration-style render smoke test
- [x] Migrate representative examples:
  - [x] One static example
  - [x] One animation example
  - [x] One topology-heavy example
- [x] Document migration:
  - [x] Before/after code snippet
  - [x] Deprecation notes for old script-level rendering paths

### Week 1 Implementation Checklist (File-Level)

Target API freeze for Week 1:

- [x] `RenderConfig`
- [x] `render_scene(...)`
- [x] `render_batch(...)`

Workstream A: Core render API scaffolding

- [x] `src/tesserax/render.py`
  - [x] Add config dataclasses/types (`RenderConfig` and nested specs)
  - [x] Add config validation with typed errors
  - [x] Add output path normalization and export policy
  - [x] Add `render_scene(...)` and `render_batch(...)` entrypoints
- [x] `src/tesserax/errors.py` (or equivalent location)
  - [x] Add `RenderConfigError`, `RenderExportError`, `RenderDependencyError`
- [x] `src/tesserax/__init__.py`
  - [x] Add controlled exports for Week 1-stable render symbols

Workstream B: Existing runtime integration

- [x] `src/tesserax/animation.py`
  - [x] Integrate with render output policy where needed
  - [x] Keep `Scene` usage backward-compatible during migration
- [x] `src/tesserax/canvas.py`
  - [x] Ensure static export paths align with render output normalization policy

Workstream C: Tests (contract-first)

- [x] `tests/test_render.py` (new)
  - [x] Config validation tests
  - [x] Output suffix normalization tests
  - [x] Overwrite policy and parent-dir policy tests
  - [x] Error-type/message coverage tests
- [x] `tests/test_core.py` / `tests/test_basics.py` (if needed)
  - [x] Add regression checks for unchanged existing behavior

Workstream D: Example migrations (Week 1 minimum set)

- [x] Static migration target:
  - [x] `examples-other/static/lineage/static_data_lineage_map.py`
- [x] Animation migration target:
  - [x] `examples-other/animation/physics/animation_physics_overlay.py`
- [x] Topology-heavy migration target:
  - [x] `examples-other/animation/topology/graph_routing_showcase.py`
- [x] Batch rendering adoption target:
  - [x] `examples-other/static/core/advanced_examples.py` uses `render_batch(...)`

Workstream E: Documentation and parity artifacts

- [x] `examples-other/reference/index.md`
  - [x] Note new render API usage in migrated examples
- [x] `examples-other/closed-API-implementation-plan.md`
  - [x] Add parameter parity tables for migrated examples

### Parameter Parity Tables (Migrated Week 1 Examples)

`examples-other/static/lineage/static_data_lineage_map.py`

| Legacy Script Parameter | New API Mapping | Status |
|---|---|---|
| `--output` | `RenderConfig.output_path` | preserved |
| `--format` | `RenderConfig.format` | preserved |
| `canvas.fit(padding=26, crop=False)` | `RenderConfig.fit_padding=26`, `RenderConfig.fit_crop=False` | preserved |
| `--seed` | `RenderConfig.timing.seed` (captured in result metadata) | aliased |
| `--report-json` | `RenderConfig.report_json_path` and/or `report_hook` | aliased |

`examples-other/animation/physics/animation_physics_overlay.py`

| Legacy Script Parameter | New API Mapping | Status |
|---|---|---|
| `--output` | `RenderConfig.output_path` | preserved |
| `--format` | `RenderConfig.format` | preserved |
| `--fps` | `RenderConfig.timing.fps` | aliased |
| `--duration` | `RenderConfig.timing.duration` | aliased |
| `--seed` | `RenderConfig.timing.seed` (captured in result metadata) | aliased |

`examples-other/animation/topology/graph_routing_showcase.py`

| Legacy Script Parameter | New API Mapping | Status |
|---|---|---|
| `--output` | `RenderConfig.output_path` | preserved |
| `--format` | `RenderConfig.format` | preserved |
| `--fps` | `RenderConfig.timing.fps` | aliased |
| `--duration` | `RenderConfig.timing.duration` | aliased |
| `--seed` | `RenderConfig.timing.seed` (captured in result metadata) | aliased |
| `--report-json` | `RenderConfig.report_json_path` and/or `report_hook` | aliased |

## Week 2, Part 1 (Feb 24 to Feb 27): Path-Follow + Tangent Orientation (`B`)

### Deliverable

Reusable path sampling and orientation primitives, integrated into animation flows.

### Exit Criteria

- `point_at(t)` behavior is well-defined and tested.
- Tangent orientation helper is available and stable at edge cases.
- At least one showcase uses the new primitives with reduced custom math.

### Checklist

- [x] Add path substrate in core (new prerequisite for `B`):
  - [x] Define canonical path protocol used by animation follow APIs
  - [x] Implement shared arc-length sampling utilities in core
  - [x] Ensure `Following` can call stable path methods (not ad hoc `hasattr` behavior)
- [x] Specify path API behavior:
  - [x] Domain of `t` (`[0,1]` or normalized equivalent)
  - [x] Clamp vs wrap behavior
  - [x] Endpoint guarantees
- [x] Implement core primitives:
  - [x] `point_at(t)`
  - [x] `angle_at(t)` or equivalent tangent helper
  - [x] Optional `sample(n)` helper for debug/preview
- [x] Ensure cross-path consistency:
  - [x] Line
  - [x] Polyline
  - [x] Curve (where supported)
- [x] Timeline integration:
  - [x] Easing/time mapping support
  - [x] Stable behavior under non-linear progression
- [x] Add tests:
  - [x] Endpoints and monotonic traversal checks
  - [x] Orientation behavior near discontinuities
  - [x] Degenerate-path handling
- [x] Migrate one high-value demo:
  - [x] Prefer `examples-other/animation/camera/animation_camera_track.py`
  - [x] Remove bespoke path/orientation math where possible

## Week 2, Part 2 (Feb 28 to Mar 2): Integration Prep + Gallery Seed

### Deliverable

An integration-ready baseline plus initial gallery content for onboarding and pattern reuse, with `A` implementation-ready scope.

### Exit Criteria

- `design_patterns_gallery.py` renders via core API.
- Examples reference docs reflect migrated entry points.
- Physics constraints/hooks (`A`) are scoped as next-sprint work with explicit design decisions and acceptance criteria.

### Checklist

- [x] Create initial `design_patterns_gallery.py`:
  - [x] 2-3 curated recipes (state chart, timeline, network, or diagnostics panel)
  - [x] Consistent invocation and output structure
- [x] Align docs/index:
  - [x] Update `examples-other/reference/index.md` for new paths/flags
  - [x] Keep `examples-other/examples_reference.md` as compatibility pointer
- [x] Integration readiness pass:
  - [x] Verify CLI-facing render contract from migrated examples
  - [x] Verify output naming consistency across demos
  - [x] Verify deterministic reruns with fixed seeds
  - [x] Verify render report metadata + hooks are consumed by at least one integration-facing example
- [x] Scope next sprint for physics/event hooks:
  - [x] Define minimal event model
  - [x] Identify which constraints/joints are first-class
  - [x] List API touchpoints needed (no implementation yet)
  - [x] Define event payload schema (`type`, `timestamp`, `entities`, `metadata`)
  - [x] Define dispatch lifecycle (`before_step`, `after_step`, `on_collision`, etc.)
  - [x] Define deterministic replay expectations for event streams
  - [x] Documented in `docs-other/physics_event_hooks_rfc.md`

## API Design Decisions (Recommended)

### 1) Public API boundaries

Recommendation:

- [x] Introduce a stable `tesserax.render` API module for integration contracts.
- [x] Keep low-level `Canvas`/`Scene` available, but treat them as composition/runtime primitives.
- [x] Re-export only stable render symbols at top level after one migration cycle.

### 2) Separation of concerns

Recommendation:

- [x] Standardize three explicit layers:
  - [x] Composition (shape/layout/animation construction)
  - [x] Execution (timeline stepping and frame capture)
  - [x] Export (format, naming, filesystem policy)
- [x] Move output suffix coercion and path normalization out of scripts into render/export layer.

### 3) Extensibility

Recommendation:

- [x] Add lifecycle hooks in render flow:
  - [x] `before_play`
  - [x] `after_frame`
  - [x] `before_save`
  - [x] `after_save`
- [x] Return a structured render result object with:
  - [x] Effective config
  - [x] Output artifact paths
  - [x] Frame count/duration
  - [x] Seed and metadata for reproducibility

### 4) Error model

Recommendation:

- [x] Add typed errors:
  - [x] `RenderConfigError`
  - [x] `RenderExportError`
  - [x] `RenderDependencyError`
- [x] Ensure all user-facing errors include:
  - [x] Parameter name
  - [x] Invalid value
  - [x] Allowed range/options
  - [x] Suggested fix
  - Enforced via shared formatter: `src/tesserax/errors.py` (`actionable_error(...)`)
  - Coverage: `tests/test_render.py`, `tests/test_params.py`

### 5) Backward compatibility

Recommendation:

- [x] Legacy adapter path intentionally not required for this phase (new API is authoritative).
- [x] Preserve high-impact legacy parameter names via aliases for at least one deprecation cycle.
- [x] Publish migration map per script with status (`preserved`, `aliased`, `deprecated`).

## API Acceptance Criteria (For `C` Completion)

- [x] One canonical output policy handles suffix normalization, overwrite policy, and parent directory policy.
- [x] Example scripts no longer implement their own output-format path coercion.
- [x] Render lifecycle hooks exist and are exercised by at least one migrated example:
  - Hook API: `RenderLifecycleHooks` in `src/tesserax/render.py`
  - Example consumer: `examples-other/animation/physics/animation_physics_overlay.py`
  - Coverage: `tests/test_render.py`
- [x] Typed render errors are covered by tests and surfaced with actionable messages.
- [x] Parameter parity map exists for migrated examples and shows no dropped high-impact knobs.

## Priority `A` (Next Sprint) Readiness Checklist

- [x] Event model RFC exists and is approved.
  - Approved contract version: `1.0.0` (February 17, 2026)
  - Reference: `docs-other/physics_event_hooks_rfc.md`
- [x] First constraint/joint set selected (small, explicit scope).
- [x] Hook API aligns with render lifecycle from `C`.
- [x] At least one candidate example identified for end-to-end `A` validation:
  - `examples-other/animation/physics/animation_physics_overlay.py`
- [x] Test strategy defined for deterministic event replay and collision hook behavior.

## Priority `A` Scaffold Status

- [x] Added event scaffold module:
  - `src/tesserax/physics/events.py`
- [x] Added world-step event dispatch for:
  - `world.before_step`
  - `constraint.applied`
  - `joint.limit_hit`
  - `world.collision_start`
  - `world.collision_persist`
  - `world.collision_end`
  - `world.after_step`
- [x] Added deterministic event ordering fields:
  - `step_index`
  - `timestamp`
  - `emission_order`
- [x] Added event tests:
  - `tests/test_physics_events.py`
- [x] Added example-level deterministic event summary regression test:
  - `tests/test_animation_physics_overlay_events.py`
- [x] Implemented first end-to-end `A` example consumer:
  - `examples-other/animation/physics/animation_physics_overlay.py`
  - Consumes `world.events` and renders collision marker + event diagnostics overlays
  - Supports optional age-based marker fading (`--event-marker-fade`)
- [x] Implemented first constraint slice aligned to RFC baseline:
  - Added constraint identity + diagnostics metadata (`constraint_id`, `error`, `impulse`) in `constraint.applied`
  - Added explicit entities for constraint events (`body:*` IDs)
  - Added `Pin` and `Distance` (`Rod` alias-style naming) in `src/tesserax/physics/constraints.py`
  - Coverage in `tests/test_physics_events.py`
- [x] Implemented first joint slice aligned to RFC baseline:
  - Added `RevoluteJoint` and `PrismaticJoint` in `src/tesserax/physics/joints.py`
  - Added `World.joint(...)` registration path in `src/tesserax/physics/world.py`
  - Added `joint.limit_hit` emission with `joint_id`, `error`, `impulse`, `active_limits`
  - Coverage in `tests/test_physics_events.py`

## Refactor Risk Register

Status: Monitored risks; not closeout blockers for this phase.

- Drift between old and new render paths causes visual regressions.
- Incomplete config validation leaks errors into exporters.
- Non-deterministic behavior breaks reproducibility and trust.
- API over-coupling to current examples reduces future flexibility.
- Parameter granularity is accidentally reduced during API consolidation.

Mitigations:

- [x] Baseline outputs for migrated examples and compare after refactor.
  - `tests/test_dataset_storyboard_regression.py`
  - `tests/test_design_patterns_gallery_regression.py`
- [x] Add contract-level tests before broad migration.
  - `tests/test_render.py`
  - `tests/test_physics_event_contract.py`
- [x] Adapter/deprecation transition is out of scope for this phase (no legacy support requirement).

## Parameter Granularity Preservation Plan

Goal: standardize render execution while preserving fine-grained expressive control from bespoke scripts.

### Step 4 Backlog Sequence (No Legacy Mode)

1. [x] **Parameter schema foundation**: two-layer API + namespaced config + extras pass-through + metadata contract (`default`, `allowed`, `stability`) with round-trip tests.
2. [x] **No-lost-knobs enforcement**: parity maps for actively migrated examples + fail-fast gate on dropped high-impact knobs.
3. [x] **Behavior/toggle testing**: high-impact knob structural-difference regressions.
4. [x] **Preset/expert UX split**: add presets while preserving full expert parameter surface and document both paths.

### Step 4 Closeout Status

1. [x] **Preset/expert UX split** completed: onboarding presets added while preserving explicit expert overrides.
2. [x] **Actionable error-model completion** delivered: user-facing render/config errors include parameter/value/allowed/fix guidance.
3. [x] **Definition-of-done reconciliation** completed: checklists align with shipped RFC + scaffold state.

### Next Work Prioritization (Post-Step 4)

1. Advance next-phase physics/event work from RFC scaffolding into additional example coverage.
2. Expand deterministic regression coverage where high-impact parameter toggles are still untested.
3. Formalize a successor execution plan that references `dataset_storyboard_scope.md` as the active implementation tracker.

### Design Rules

- [x] Use a two-layer API:
  - [x] Core lifecycle/render contract in stable API.
  - [x] Domain/example parameter schemas for advanced controls.
  - Initial implementation: `src/tesserax/params.py`, wired in `examples-other/static/core/design_patterns_gallery.py`
- [x] Use namespaced config instead of flattening:
  - [x] `layout.*`, `motion.*`, `routing.*`, `style.*`, `export.*`
  - Initial implementation uses `layout.*`, `motion.*`, `style.*`, `export.*` in gallery schema
- [x] Keep a pass-through extension area:
  - [x] `advanced`/`extras` block for niche controls without core API churn.
  - Implemented via `extras.*` acceptance in `ParameterSchema`
- [x] Require parameter metadata:
  - [x] Default value
  - [x] Valid range/options
  - [x] Stability level (`stable`, `experimental`)

### Migration Gates (No-Lost-Knobs Policy)

- [x] For each migrated example, produce a parameter parity map:
  - [x] Old script parameter
  - [x] New API parameter path
  - [x] Status (`preserved`, `aliased`, `deprecated`)
  - Source of truth: `examples-other/parameter_parity_manifest.json`
- [x] Block migration completion if any high-impact parameter is dropped.
  - Fail-fast gate: `examples-other/validate_parameter_parity.py`
  - Validation + logging coverage: `tests/test_parameter_parity_gate.py`
- [x] Preserve old-name alias/deprecation cycle is not required in no-legacy mode.
- [x] Explicit deprecation warning flow is not required in no-legacy mode.

### Testing Requirements

- [x] Add behavior tests for high-impact knobs (layout density, path bias, pulse timing, etc.).
  - Foundational schema tests added: `tests/test_params.py`
- [x] Add regression checks verifying parameter toggles still produce expected structural differences.
  - Implemented in `tests/test_parameter_toggle_regressions.py`
- [x] Add serialization tests to ensure advanced/namespaced parameters round-trip cleanly.
  - Implemented in `tests/test_params.py`

### UX Strategy (Beginner + Expert)

- [x] Provide presets for quick starts (onboarding path).
  - Implemented in `examples-other/static/core/design_patterns_gallery.py` (`--preset`)
- [x] Keep full expert parameter surface available (power-user path).
  - Explicit CLI flags override presets in gallery parameter resolution.
- [x] Document both paths clearly so simplification does not imply capability loss.
  - Updated in `examples-other/reference/index.md`

## Definition of Done (End of This Plan)

- [x] Core rendering API adopted by key examples.
- [x] Path-follow/tangent primitives in active use by at least one showcase.
- [x] Gallery seed exists and is documented in the reference index.
- [x] Physics/event hooks have an approved scoped design brief for the next phase.
  - Approved + documented in `docs-other/physics_event_hooks_rfc.md` (contract `1.0.0`, February 17, 2026).

## Next Phase Handoff

- Dataset storyboard scope (Phase 1 implemented):
  - `examples-other/dataset_storyboard_scope.md`
- Physics/event hooks RFC:
  - `docs-other/physics_event_hooks_rfc.md`
- Dataset storyboard deterministic regression:
  - `tests/test_dataset_storyboard_regression.py`
