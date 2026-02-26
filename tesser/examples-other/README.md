# Examples Organization

This directory is organized by intent and execution mode:

- `animation/`
  - `topology/`: graph/DAG/topology stress stories
  - `operations/`: operational/system risk narratives
  - `camera/`: camera behavior stress tests
  - `physics/`: physics-overlay examples
- `static/`
  - `core/`: static baseline examples
  - `lineage/`: static lineage/risk maps and runners
  - `force-directed/`: force-directed planning/reference docs
- `data/`
  - `tufte/`: Tufte-style charts
  - `converters/`: data conversion utilities
- `reference/`
  - `index.md`: primary reference card with CLI usage
- `results/`
  - generated outputs
- `sugiyama-stories/`
  - Sugiyama concept notes

## Start Here

- Reference card: `examples-other/reference/index.md`
- Animation example (ops):
  - `./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook.py --output incident.gif`
- Animation matrix runner:
  - `./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook_runner.py --duration 4 --fps 10 --output-dir ./incident_compare`
- Static lineage map:
  - `./.venv/bin/python examples-other/static/lineage/static_data_lineage_map.py --output lineage.svg`

## Notes

- Most animation scripts follow the same contract:
  - `--scenario`, `--policy`, `--report-json`, `--output`
- Runner scripts generate:
  - leaderboard CSV/JSON plus per-run reports under `reports/`
- Core render contract:
  - `RenderConfig` + `render_scene(...)` / `render_batch(...)`
  - Optional lifecycle hooks (`RenderLifecycleHooks`) for `before_play`, `after_frame`, `before_save`, `after_save`
  - Hooked example: `examples-other/animation/physics/animation_physics_overlay.py`
- Planning status:
  - `examples-other/closed-API-implementation-plan.md` is closed (Step 4 complete, February 18, 2026).
  - Active follow-on planning is tracked in `examples-other/dataset_storyboard_scope.md` and `docs-other/physics_event_hooks_rfc.md`.
  - Ordered remaining migration backlog: `examples-other/api_migration_backlog.md`.
