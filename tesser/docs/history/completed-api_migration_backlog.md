# Examples Render API Migration Backlog

Last updated: February 18, 2026

## Objective

Complete migration of remaining `examples-other` rendering scripts to the core render API contract (`RenderConfig` + `render_scene(...)` / `render_batch(...)`) with fast, low-risk sequencing.

## Summary

- Total rendering scripts: `28`
- Already migrated: `28`
- Remaining migration targets: `0`
- Ordering strategy:
  - Quick wins first (highest throughput, lowest risk)
  - Medium complexity next (multi-output or dual-path scripts)
  - High complexity last (normalized-export scripts that need a shared solution)

## Shared Migration Contract (Applies to All Items)

- [ ] Use `RenderConfig` for output format/path policy.
- [ ] Remove script-level suffix coercion (`Path(args.output)` + `.with_suffix(...)`) where render API handles it.
- [ ] Route final output through `render_scene(...)` or `render_batch(...)`.
- [ ] Preserve existing CLI knobs and reporting behavior.
- [ ] Keep deterministic seed/timing metadata capture when available.

## Phase 1: Quick Wins (13 small animation scripts + 2 static scripts)

- [x] `examples-other/animation/operations/animation_incident_response_playbook.py`
- [x] `examples-other/animation/operations/animation_service_blast_radius.py`
- [x] `examples-other/animation/operations/animation_supply_chain_network_stress.py`
- [x] `examples-other/animation/operations/animation_supply_chain_resilience.py`
- [x] `examples-other/animation/topology/animation_attention_heads.py`
- [x] `examples-other/animation/topology/animation_cicd_dependency_risk.py`
- [x] `examples-other/animation/topology/animation_flow_dag.py`
- [x] `examples-other/animation/topology/animation_grid_contingency_cascade.py`
- [x] `examples-other/animation/topology/animation_packet_ring.py`
- [x] `examples-other/animation/topology/animation_residual_pipeline.py`
- [x] `examples-other/animation/topology/animation_sugiyama_story_workflow.py`
- [x] `examples-other/animation/topology/animation_topology_morph.py`
- [x] `examples-other/animation/topology/feynman_like_interactions.py`
- [x] `examples-other/static/core/simple_convolution.py`
- [x] `examples-other/data/tufte/tufte_small_multiples_extended.py`

Expected work pattern for each Phase 1 file:

- [x] Replace final save block with `RenderConfig` + `render_scene(...)`.
- [x] Preserve existing fit behavior via `fit_padding` / `viewport` settings as needed.
- [x] Keep existing print/report output semantics.

## Phase 2: Medium Complexity

- [x] `examples-other/animation/topology/animation_regression_suite.py`
- [x] `examples-other/data/tufte/tufte_small_multiples.py`
- [x] `examples-other/static/core/neural_network_refined.py`

Expected work focus:

- [x] `animation_regression_suite.py`: migrate optional media export path while preserving signature computation and report logic.
- [x] `tufte_small_multiples.py`: migrate both static and animated branches to the render contract.
- [x] `neural_network_refined.py`: move hardcoded multi-output saves to `render_batch(...)` with explicit output naming policy.

## Phase 3: High Complexity Normalized-Export Cluster

- [x] `examples-other/animation/camera/animation_camera_zoom_stress.py`
- [x] `examples-other/animation/operations/animation_state_machine_cinematics.py`
- [x] `examples-other/animation/operations/hybrid_control_systems.py`

### Shared Implementation Strategy (Intentional Velocity)

- [x] Create one shared normalization/export utility module used by all three scripts (avoid three bespoke implementations).
- [x] Introduce a scene-like adapter or export helper compatible with `render_scene(...)` while preserving normalized frame dimensions.
- [x] Migrate one anchor script first (`animation_camera_zoom_stress.py`) and lock behavior with a regression test.
- [x] Apply the same adapter pattern to the remaining two scripts with minimal per-file deltas.
- [x] Add focused tests for normalized frame-size guarantees and output parity.

## Validation and Closeout Checklist

- [x] Add/expand regression coverage for migrated files where behavior is sensitive.
- [x] Run parameter parity gate after each phase (`examples-other/validate_parameter_parity.py`).
- [x] Update `examples-other/reference/index.md` migration notes for newly migrated scripts.
- [x] Mark script status updates in this checklist as each migration lands.
