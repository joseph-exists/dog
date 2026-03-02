# Examples Reference (examples-other)

This card documents the currently available example scripts and how to run them.

## Environment Notes

- Run from repository root: `tesserax`
- Prefer project venv:
  - `./.venv/bin/python <script>`
- Animation export (`gif`/`mp4`) requires optional export deps:
  - `imageio[ffmpeg]`
  - `cairosvg`
  - Declared in `pyproject.toml` under `[project.optional-dependencies].export`

## Week 1 Render API Migration Notes

Core render API introduced:

- `RenderConfig`: typed render/output contract
- `render_scene(target, config)`: single target render entrypoint
- `render_batch([(target, config), ...])`: batch render entrypoint
- `ParameterSchema` + `ParameterSpec`: namespaced example/domain parameter contract with metadata and extras pass-through
- Deterministic result metadata includes timing/seed + config fingerprint
- `RenderResult` telemetry now includes `frame_count` and effective `duration`
- Optional report hooks:
  - `report_json_path` to write render result JSON
  - `report_hook` callback for custom reporting
- Optional lifecycle hooks (`RenderLifecycleHooks`):
  - `before_play(target, config)`
  - `after_frame(frame_index, frame_total, config)`
  - `before_save(output_path, target, config)`
  - `after_save(result, config)`

### Before/After: Static Output (`static_data_lineage_map.py`)

Before:
```python
out = Path(args.output)
if out.suffix.lower() != f".{args.format}":
    out = out.with_suffix(f".{args.format}")
canvas.fit(padding=26, crop=False)
canvas.save(str(out))
```

After:
```python
result = render_scene(
    canvas,
    RenderConfig(
        output_path=args.output,
        format=args.format,
        fit_padding=26,
        fit_crop=False,
    ),
)
print(result.output_path)
```

### Before/After: Animation Output (`animation_physics_overlay.py`, `graph_routing_showcase.py`)

Before:
```python
out = Path(args.output)
if out.suffix.lower() != f".{args.format}":
    out = out.with_suffix(f".{args.format}")
scene.save(str(out), format=args.format)
```

After:
```python
result = render_scene(scene, RenderConfig(output_path=args.output, format=args.format))
print(result.output_path)
```

### Before/After: Batch Static Rendering (`advanced_examples.py`)

Before:
```python
canvas.fit(padding=24, crop=False)
filename = f"{name}.svg"
canvas.save(filename)
```

After:
```python
cfg = RenderConfig(
    output_path=f"{name}.svg",
    format="svg",
    viewport=ViewportSpec(fit_padding=24, fit_crop=False),
)
results = render_batch(batch)
```

### Deprecation Notes (Script-Level Rendering Paths)

- Legacy per-script output suffix normalization (`Path(args.output)` + `.with_suffix(...)`) is deprecated in favor of `render_scene(...)`.
- Legacy direct `scene.save(..., format=...)` and `canvas.save(...)` output-policy handling in examples is deprecated for migrated scripts.
- Preferred migration path:
  - Build target (`Canvas` or `Scene`)
  - Build `RenderConfig`
  - Call `render_scene(...)` or `render_batch(...)`
- Consume `RenderResult` metadata/report + lifecycle hooks for deterministic reporting

## Next Scope Drafts

- Working implementation plan status:
  - `examples-other/closed-API-implementation-plan.md` is closed as of February 18, 2026 (Step 4 complete).
  - Follow-on implementation tracking shifts to:
    - `examples-other/dataset_storyboard_scope.md`
    - `docs-other/physics_event_hooks_rfc.md`
- Ordered remaining API migration backlog:
  - `examples-other/api_migration_backlog.md`
  - Quick-wins, Phase 2, and Phase 3 are complete; render API migration backlog is closed.
- Dataset storyboard scope:
  - `examples-other/dataset_storyboard_scope.md`
- Physics/event hooks RFC:
  - `docs-other/physics_event_hooks_rfc.md`
  - Contract approved: `1.0.0` (February 17, 2026)
  - Current scaffold coverage includes `constraint.applied` and `joint.limit_hit`
- Step 4 hardening regressions:
  - `tests/test_dataset_storyboard_regression.py`
  - `tests/test_design_patterns_gallery_regression.py`
  - `tests/test_physics_event_contract.py`
  - `tests/test_parameter_toggle_regressions.py`
- Parameter parity gate (fail-fast, reason-coded logging):
  - Manifest: `examples-other/parameter_parity_manifest.json`
  - Runner: `examples-other/validate_parameter_parity.py`
  - Coverage: `tests/test_parameter_parity_gate.py`

## Quick Index

- `examples-other/static/core/simple_convolution.py`
- `examples-other/static/core/advanced_examples.py`
- `examples-other/static/core/design_patterns_gallery.py`
- `examples-other/static/core/neural_network_refined.py`
- `examples-other/animation/topology/animation_flow_dag.py`
- `examples-other/animation/topology/animation_attention_heads.py`
- `examples-other/animation/topology/animation_packet_ring.py`
- `examples-other/animation/topology/animation_residual_pipeline.py`
- `examples-other/animation/topology/animation_topology_morph.py`
- `examples-other/animation/physics/animation_physics_overlay.py`
- `examples-other/animation/camera/animation_camera_track.py`
- `examples-other/animation/camera/animation_camera_zoom_stress.py`
- `examples-other/animation/operations/animation_state_machine_cinematics.py`
- `examples-other/animation/topology/feynman_like_interactions.py`
- `examples-other/data/tufte/tufte_small_multiples.py`
- `examples-other/data/tufte/tufte_small_multiples_extended.py`
- `examples-other/data/converters/tufte_wide_to_long.py`
- `examples-other/data/storyboard/dataset_storyboard.py`
- `examples-other/animation/operations/hybrid_control_systems.py`
- `examples-other/animation/operations/animation_supply_chain_resilience.py`
- `examples-other/animation/operations/animation_supply_chain_resilience_runner.py`
- `examples-other/animation/operations/animation_incident_response_playbook.py`
- `examples-other/animation/operations/animation_incident_response_playbook_runner.py`
- `examples-other/animation/topology/animation_grid_contingency_cascade.py`
- `examples-other/animation/topology/animation_grid_contingency_cascade_runner.py`
- `examples-other/animation/topology/animation_sugiyama_story_workflow.py`
- `examples-other/animation/topology/animation_cicd_dependency_risk.py`
- `examples-other/animation/topology/animation_cicd_dependency_risk_runner.py`
- `examples-other/animation/topology/graph_routing_showcase.py`
- `examples-other/animation/topology/graph_routing_showcase_runner.py`
- `examples-other/animation/topology/animation_regression_suite.py`
- `examples-other/animation/topology/animation_regression_suite_runner.py`
- `examples-other/static/lineage/static_data_lineage_map.py`
- `examples-other/static/lineage/static_data_lineage_map_runner.py`

## simple_convolution.py

Purpose:
- Minimal matrix/convolution-style static SVG example
- Good for checking text/cell positioning and viewBox framing

Run:
```bash
./.venv/bin/python examples-other/static/core/simple_convolution.py
```

Output:
- `convolution_demo.svg`

Notes:
- No CLI flags currently
- Script calls `canvas.fit(...)` to avoid clipping

## advanced_examples.py

Purpose:
- Multi-scene static SVG showcase:
  - force-directed graph
  - hierarchical tree
  - neural network layout
  - convolution visualization
  - physics setup scene

Run:
```bash
./.venv/bin/python examples-other/static/core/advanced_examples.py
```

Outputs:
- `force_network.svg`
- `hierarchical_tree.svg`
- `neural_network.svg`
- `convolution_demo.svg`
- `physics_bounce.svg`

Notes:
- No CLI flags currently
- Save loop applies `canvas.fit(padding=24, crop=False)` for framing consistency

## design_patterns_gallery.py

Purpose:
- Curated onboarding gallery of reusable diagram recipes:
  - state chart
  - timeline
  - network diagnostics panel
- Demonstrates consistent invocation/output using `render_batch(...)`
- Optional per-recipe render JSON reports via `report_json_path`

Run:
```bash
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py [flags]
```

Flags:
- `--preset {balanced,quickstart,network_review}`: starter profile (default: `balanced`)
- `--recipes <csv|all>`: `state_chart,timeline,network` or `all` (expert override)
- `--seed <int>`: deterministic recipe details (expert override)
- `--width <int>`: canvas width (expert override)
- `--height <int>`: canvas height (expert override)
- `--format {svg}`: output format (default: `svg`)
- `--output-prefix <path>`: output file prefix (expert override)
- `--report-dir <path>`: optional per-recipe JSON report directory (expert override)
- `--summary-report <path>`: optional aggregate summary JSON generated via `report_hook` (expert override)

Examples:
```bash
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py --recipes all --output-prefix ./design_patterns_gallery
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py --recipes state_chart,network --report-dir ./design_pattern_reports
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py --recipes all --summary-report ./design_pattern_reports/summary.json
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py --preset quickstart --summary-report ./design_pattern_reports/summary.json
./.venv/bin/python examples-other/static/core/design_patterns_gallery.py --preset network_review --recipes state_chart --width 1500 --output-prefix ./design_patterns_gallery_override
```

Outputs:
- `<output-prefix>_state_chart.svg`
- `<output-prefix>_timeline.svg`
- `<output-prefix>_network.svg`
- Optional: `<report-dir>/{state_chart,timeline,network}.json`
- Optional: `<summary-report>.json` with hook-captured aggregate metadata
- Preset values are defaults; any explicit expert flag overrides the preset.

## neural_network_refined.py

Purpose:
- High-complexity neural diagrams to stress composition and rendering:
  - dense all-to-all MLP
  - hybrid residual/attention-style network

Run:
```bash
./.venv/bin/python examples-other/static/core/neural_network_refined.py [flags]
```

Flags:
- `--mode {dense,hybrid,both}`: which diagram(s) to render (default: `both`)
- `--fanout <int>`: connections per source neuron in hybrid mode (default: `4`)
- `--scale <float>`: global edge width scale (default: `1.0`)

Examples:
```bash
./.venv/bin/python examples-other/static/core/neural_network_refined.py --mode dense --scale 1.4
./.venv/bin/python examples-other/static/core/neural_network_refined.py --mode hybrid --fanout 6 --scale 0.8
```

Outputs:
- `neural_network_dense.svg`
- `neural_network_hybrid.svg`

Notes:
- Output set depends on `--mode`
- Values are clamped in script (`fanout >= 1`, `scale >= 0.1`)

## dataset_storyboard.py

Purpose:
- Phase 1 storyboard scaffold for real/synthetic datasets.
- Lands Scene A (dataset profile), Scene B (small multiples breakdown), and Scene C (annotated callouts) with deterministic render/report contract wiring.
- Uses `render_batch(...)`, `report_json_path`, and `report_hook` summary output.

Run:
```bash
./.venv/bin/python examples-other/data/storyboard/dataset_storyboard.py [flags]
```

Core flags:
- `--mode {csv,synthetic}` (default: `synthetic`)
- `--input-csv <path>`: required for `--mode csv`
- `--seed <int>`: deterministic seed (default: `131`)
- `--scene-b-panels <int>`: Scene B panel cap (default: `6`)
- `--scene-b-series <int>`: Scene B series cap per panel (default: `4`)
- `--scene-c-topn <int>`: Scene C callout cap (default: `6`)
- `--width <int>` / `--height <int>`
- `--output-prefix <path>` (default: `dataset_storyboard`)
- `--report-dir <path>`: optional per-scene report output directory
- `--summary-report <path>`: optional aggregate hook summary JSON

CSV schema flags:
- `--group-col <name>` (default: `group`)
- `--category-col <name>` (default: `category`)
- `--time-col <name>` (default: `time`)
- `--value-col <name>` (default: `value`)

Synthetic data flags:
- `--groups <int>` (default: `4`)
- `--categories <int>` (default: `5`)
- `--points <int>` (default: `18`)

Example:
```bash
./.venv/bin/python examples-other/data/storyboard/dataset_storyboard.py --mode synthetic --output-prefix ./dataset_storyboard --report-dir ./dataset_storyboard_reports --summary-report ./dataset_storyboard_reports/summary.json
```

Outputs:
- `<output-prefix>_scene_a_profile.svg`
- `<output-prefix>_scene_b_small_multiples.svg`
- `<output-prefix>_scene_c_callouts.svg`
- Optional: `<report-dir>/scene_a_profile.json`
- Optional: `<report-dir>/scene_b_small_multiples.json`
- Optional: `<report-dir>/scene_c_callouts.json`
- Optional: `<summary-report>.json`

## animation_flow_dag.py

Purpose:
- Animated DAG flow stress test for `animation.py`
- Exercises `Parallel`, `Delayed`, `KeyframeAnimation`, and high-packet throughput
- Supports routing behavior comparison modes

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py [flags]
```

Core flags:
- `--nodes <int>`: DAG nodes (default: `42`)
- `--layers <int>`: DAG layers (default: `6`)
- `--packets <int>`: moving packets (default: `140`)
- `--duration <float>`: animation seconds (default: `10.0`)
- `--fps <int>`: capture FPS (default: `24`)
- `--max-out <int>`: max outgoing edges per node (default: `3`)

Routing flags:
- `--routing {random,shortest,biased}` (default: `random`)
- `--bias-strength <float>`: distance preference for `biased` mode (default: `1.2`)
- `--y-penalty <float>`: vertical jump penalty for `biased` mode (default: `0.010`)

Pulse/timing flags:
- `--lag <float>`: node pulse lag ratio (default: `0.035`)
- `--pulse-cycles <float>`: pulse repeats over full duration (default: `3.0`)
- `--seed <int>`: RNG seed (default: `7`)

Render/output flags:
- `--width <int>`: canvas width (default: `1600`)
- `--height <int>`: canvas height (default: `950`)
- `--format {gif,mp4}` (default: `gif`)
- `--output <path>`: output file path; extension is coerced to selected format

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py --routing random --output flow_random.gif
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py --routing shortest --packets 300 --duration 12 --fps 30 --output flow_shortest.gif
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py --routing biased --bias-strength 1.6 --y-penalty 0.02 --output flow_biased.gif
```

Stress presets:
```bash
# Medium stress
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py --nodes 80 --layers 8 --packets 600 --duration 12 --fps 24 --output flow_medium.gif

# Heavy stress
./.venv/bin/python examples-other/animation/topology/animation_flow_dag.py --nodes 120 --layers 10 --packets 1200 --duration 18 --fps 30 --format mp4 --output flow_heavy.mp4
```

Notes:
- Large `packets * duration * fps` drives memory/runtime
- `mp4` export depends on ffmpeg backend via `imageio[ffmpeg]`

## animation_attention_heads.py

Purpose:
- Animated multi-head token flow stress test
- Exercises dense curved-edge rendering plus packet, edge, and badge animations

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_attention_heads.py [flags]
```

Core flags:
- `--tokens <int>`: token count per side (default: `24`)
- `--heads <int>`: number of attention heads (default: `8`)
- `--topk <int>`: connections per query per head (default: `4`)
- `--packets <int>`: animated packets (default: `320`)
- `--duration <float>`: animation seconds (default: `10.0`)
- `--fps <int>`: capture FPS (default: `24`)

Animation flags:
- `--pulse-cycles <float>`: pulse repetitions over total duration (default: `3.0`)
- `--lag <float>`: head indicator lag ratio (default: `0.045`)
- `--edge-pulses <int>`: number of edges with width-pulse animation (default: `24`)
- `--seed <int>`: RNG seed (default: `11`)

Render/output flags:
- `--width <int>`: canvas width (default: `1800`)
- `--height <int>`: canvas height (default: `1000`)
- `--format {gif,mp4}` (default: `gif`)
- `--output <path>`: output path; extension is coerced to selected format

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_attention_heads.py --output attention_heads.gif
./.venv/bin/python examples-other/animation/topology/animation_attention_heads.py --tokens 40 --heads 12 --topk 6 --packets 900 --duration 14 --fps 30 --format mp4 --output attention_heads_heavy.mp4
```

Notes:
- Total static edge count is approximately `heads * tokens * topk`
- This script is useful for spotting animation bottlenecks in high-fan-out scenes

## animation_packet_ring.py

Purpose:
- Animated ring network with rerouting packets and optional chord shortcuts
- Good for comparing routing behavior in cyclic topologies

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_packet_ring.py [flags]
```

Topology/traffic flags:
- `--nodes <int>`: ring node count (default: `28`)
- `--chords <int>`: undirected chord pairs (default: `20`)
- `--packets <int>`: animated packets (default: `280`)
- `--routing {random,clockwise,shortest,biased}` (default: `random`)
- `--hop-time <float>`: seconds per hop (default: `0.35`)
- `--retarget-prob <float>`: chance to retarget destination after each hop (default: `0.22`)

Routing-bias flags:
- `--bias-strength <float>`: distance weighting in `biased` mode (default: `0.9`)
- `--chord-boost <float>`: chord preference multiplier in `biased` mode (default: `0.6`)

Animation/render flags:
- `--duration <float>`: animation seconds (default: `10.0`)
- `--fps <int>`: capture FPS (default: `24`)
- `--pulse-cycles <float>`: node pulse cycles (default: `3.0`)
- `--lag <float>`: node pulse lag ratio (default: `0.03`)
- `--seed <int>`: RNG seed (default: `17`)
- `--width <int>` / `--height <int>`: canvas size (defaults: `1700` / `1000`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_packet_ring.py --routing clockwise --output packet_ring_clockwise.gif
./.venv/bin/python examples-other/animation/topology/animation_packet_ring.py --routing shortest --nodes 40 --chords 30 --packets 700 --duration 14 --fps 30 --output packet_ring_shortest.gif
./.venv/bin/python examples-other/animation/topology/animation_packet_ring.py --routing biased --bias-strength 1.2 --chord-boost 1.0 --output packet_ring_biased.gif
```

Notes:
- `clockwise` is the baseline deterministic behavior
- `shortest` highlights convergence properties with rerouting targets
- `biased` balances distance reduction and chord usage preference

## animation_residual_pipeline.py

Purpose:
- Animated residual/branching pipeline stress test
- Exercises `Sequence`, `Parallel`, `Delayed`, keyframes, and mixed route packets

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_residual_pipeline.py [flags]
```

Topology/traffic flags:
- `--blocks <int>`: main pipeline block count (default: `7`)
- `--branches <int>`: auxiliary branch module count (default: `2`)
- `--packets <int>`: animated packet count (default: `260`)

Animation flags:
- `--duration <float>`: animation seconds (default: `10.0`)
- `--fps <int>`: capture FPS (default: `24`)
- `--lag <float>`: delayed pulse lag ratio (default: `0.04`)
- `--pulse-cycles <float>`: pulse repeats (default: `3.0`)
- `--edge-pulses <int>`: pulsing connector edge count (default: `28`)
- `--seed <int>`: RNG seed (default: `23`)

Render/output flags:
- `--width <int>` / `--height <int>`: canvas size (defaults: `1800` / `1000`)
- `--format {gif,mp4}` (default: `gif`)
- `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_residual_pipeline.py --output residual_pipeline.gif
./.venv/bin/python examples-other/animation/topology/animation_residual_pipeline.py --blocks 10 --branches 3 --packets 700 --duration 14 --fps 30 --format mp4 --output residual_pipeline_heavy.mp4
```

Notes:
- Uses staged composition: short intro pulse via `Sequence`, then full pipeline activity
- Good target for timing drift and orchestration regression checks

## animation_topology_morph.py

Purpose:
- Morphs a shared node set through graph topologies:
  - star -> ring -> tree -> cluster
- Exercises node/edge keyframes and explicit `Morphed` animation on a polyline overlay

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_topology_morph.py [flags]
```

Flags:
- `--nodes <int>`: node count used in all topologies (default: `18`)
- `--duration <float>`: animation seconds (default: `12.0`)
- `--fps <int>`: capture FPS (default: `24`)
- `--edge-pulse-cycles <float>`: active-edge pulse repetitions (default: `2.5`)
- `--lag <float>`: delayed node pulse lag ratio (default: `0.03`)
- `--seed <int>`: RNG seed (default: `31`)
- `--width <int>` / `--height <int>`: canvas size (defaults: `1800` / `1040`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_topology_morph.py --output topology_morph.gif
./.venv/bin/python examples-other/animation/topology/animation_topology_morph.py --nodes 26 --duration 16 --fps 30 --format mp4 --output topology_morph_heavy.mp4
```

Notes:
- Edge visibility is encoded through width keyframes on a shared superset edge set
- Includes a closed polyline morph sequence to validate point-wise shape morphing

## animation_physics_overlay.py

Purpose:
- Physics + animation integration stress test
- Bakes physics trajectories and overlays velocity vectors/trails on top of animated bodies

Run:
```bash
./.venv/bin/python examples-other/animation/physics/animation_physics_overlay.py [flags]
```

Simulation/control flags:
- `--balls <int>`: dynamic ball count (default: `8`)
- `--duration <float>`: simulation and animation seconds (default: `8.0`)
- `--dt <float>`: physics step size (default: `0.02`)
- `--fps <int>`: render FPS (default: `24`)
- `--gravity <float>`: gravity acceleration (default: `980.0`)
- `--drag <float>`: linear drag coefficient (default: `0.06`)
- `--restitution <float>`: ball bounciness in `[0,1]` (default: `0.78`)
- `--joint-demo {none,revolute,prismatic}`: optional joint limit-hit event demo (default: `none`)

Overlay flags:
- `--vector-scale <float>`: velocity-to-arrow scale (default: `0.10`)
- `--trail-step <int>`: sample stride for static trails (default: `5`)
- `--event-markers <int>`: max rendered collision-contact markers from physics events (default: `100`)
- `--event-marker-fade <float>`: optional age-based marker fade strength in `[0,1]` (default: `0.0`)
- `--hook-log-json <path>`: optional lifecycle hook trace output JSON
- `--seed <int>`: RNG seed (default: `41`)

Render/output flags:
- `--width <int>` / `--height <int>`: canvas size (defaults: `1400` / `900`)
- `--format {gif,mp4}` (default: `gif`)
- `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/physics/animation_physics_overlay.py --output physics_overlay.gif
./.venv/bin/python examples-other/animation/physics/animation_physics_overlay.py --balls 16 --duration 14 --dt 0.01 --fps 30 --format mp4 --output physics_overlay_heavy.mp4
```

Notes:
- Smaller `--dt` increases physical fidelity but costs more runtime
- High `balls * duration * fps` can be expensive when exporting
- Useful for validating physics bake + animation playback consistency
- Consumes `world.events` and renders event diagnostics (`before/after`, collision lifecycle, constraints)
- Includes joint limit-hit callouts from `joint.limit_hit` events
- Exercises `RenderLifecycleHooks` via `render_scene(...)` and can emit hook traces (`--hook-log-json`)
- Deterministic event-summary regression coverage:
  - `tests/test_animation_physics_overlay_events.py`
  - `tests/test_physics_events.py`
  - `tests/test_render.py`

## animation_camera_track.py

Purpose:
- Camera/viewbox control stress test over a large world scene
- Demonstrates target-follow tracking, scripted camera moves, and target switching

Run:
```bash
./.venv/bin/python examples-other/animation/camera/animation_camera_track.py [flags]
```

Behavior flags:
- `--mode {track,scripted,hybrid,switch}` (default: `hybrid`)
  - `track`: camera continuously follows hero
  - `scripted`: camera follows explicit keyframed path
  - `switch`: track hero then switch to decoy
  - `hybrid`: track hero, transition shot, then track decoy

Timing/random flags:
- `--duration <float>`: animation seconds (default: `10.0`)
- `--fps <int>`: capture FPS (default: `24`)
- `--seed <int>`: RNG seed (default: `53`)

Scene/camera flags:
- `--world-width <int>` / `--world-height <int>`: world canvas (defaults: `2800` / `1800`)
- `--camera-width <float>` / `--camera-height <float>`: camera viewport size (defaults: `840` / `520`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/camera/animation_camera_track.py --mode track --output camera_track_track.gif
./.venv/bin/python examples-other/animation/camera/animation_camera_track.py --mode scripted --duration 12 --fps 30 --output camera_track_scripted.gif
./.venv/bin/python examples-other/animation/camera/animation_camera_track.py --mode switch --output camera_track_switch.gif
```

Notes:
- This script focuses on camera translation/follow behavior.
- Camera zoom (animated width/height) currently causes variable frame size in GIF stacking, so modes keep camera dimensions fixed.

## animation_camera_zoom_stress.py

Purpose:
- Explicit camera zoom stress test (animated camera width/height)
- Uses frame normalization during export so GIF/MP4 remain valid despite per-frame camera crop size changes

Run:
```bash
./.venv/bin/python examples-other/animation/camera/animation_camera_zoom_stress.py [flags]
```

Mode/timing flags:
- `--mode {hero,scripted,hybrid}` (default: `hybrid`)
- `--duration <float>` (default: `10.0`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `61`)

World/camera flags:
- `--world-width <int>` / `--world-height <int>` (defaults: `3200` / `2200`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--zoom-min <float>` (default: `0.45`)
- `--zoom-max <float>` (default: `1.05`)
- `--zoom-cycles <float>` (default: `3.0`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/camera/animation_camera_zoom_stress.py --mode hero --output camera_zoom_hero.gif
./.venv/bin/python examples-other/animation/camera/animation_camera_zoom_stress.py --mode hybrid --zoom-min 0.40 --zoom-max 1.30 --zoom-cycles 4 --duration 12 --fps 30 --output camera_zoom_hybrid.gif
```

Notes:
- Unlike `animation_camera_track.py`, this script intentionally animates camera size.
- Export path normalizes all captured frames to fixed output dimensions (`camera-width x camera-height`).

## animation_state_machine_cinematics.py

Purpose:
- Finite-state mechanics + cinematic camera stress test
- Demonstrates guard-driven state transitions with scene choreography and dynamic zoom

Run:
```bash
./.venv/bin/python examples-other/animation/operations/animation_state_machine_cinematics.py [flags]
```

FSM/camera flags:
- `--camera-mode {track,scripted,hybrid}` (default: `hybrid`)
- `--duration <float>` (default: `12.0`)
- `--dt <float>` simulation step (default: `0.03`)
- `--fps <int>` render FPS (default: `24`)
- `--seed <int>` (default: `73`)

World/camera sizing:
- `--world-width <int>` / `--world-height <int>` (defaults: `3000` / `2000`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `960` / `620`)
- `--zoom-min <float>` / `--zoom-max <float>` (defaults: `0.52` / `1.02`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/animation_state_machine_cinematics.py --output state_machine_cinematics.gif
./.venv/bin/python examples-other/animation/operations/animation_state_machine_cinematics.py --camera-mode scripted --duration 14 --fps 30 --format mp4 --output state_machine_cinematics_scripted.mp4
```

Notes:
- States used: `PATROL -> INVESTIGATE -> CHASE -> EVADE -> RESOLVE -> IDLE`
- The script prints transition logs with time and guard reason.
- As with zoom stress, export normalizes variable camera-crop frame sizes.

## feynman_like_interactions.py

Purpose:
- Feynman-inspired interaction diagram stress test
- Mixes straight fermion propagators, wavy photon-like lines, and coiled gluon-like lines
- Adds moving quanta packets + vertex/edge pulse dynamics

Run:
```bash
./.venv/bin/python examples-other/animation/topology/feynman_like_interactions.py [flags]
```

Topology/style flags:
- `--style {qed,qcd,mixed}` (default: `mixed`)
- `--packets <int>`: animated quanta packet count (default: `260`)
- `--wave-amp <float>`: wave/coil amplitude (default: `12.0`)
- `--wave-cycles <float>`: wave/coil cycle count (default: `7.0`)
- `--edge-pulses <int>`: number of pulsing propagators (default: `18`)
- `--seed <int>`: RNG seed (default: `83`)

Animation/render flags:
- `--duration <float>` (default: `10.0`)
- `--fps <int>` (default: `24`)
- `--width <int>` / `--height <int>` (defaults: `1800` / `1000`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/feynman_like_interactions.py --style qed --output feynman_qed.gif
./.venv/bin/python examples-other/animation/topology/feynman_like_interactions.py --style mixed --packets 800 --duration 14 --fps 30 --format mp4 --output feynman_mixed_heavy.mp4
```

Notes:
- This is a visual metaphor/stress harness, not a physics-accurate symbolic engine.
- Useful for evaluating expressive line grammars and annotation-heavy interaction layouts.

## tufte_small_multiples.py

Purpose:
- Tufte-inspired dense analytical panels:
  - direct labels over legends
  - context + focus series
  - event markers and residual strips
  - slope-summary mini-overlays
- Supports static SVG and optional lightweight animation overlays for GIF/MP4

Run:
```bash
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples.py [flags]
```

Layout/data flags:
- `--panels <int>`: panel count (default: `8`)
- `--points <int>`: points per panel (default: `48`)
- `--columns <int>`: panel columns (default: `4`)
- `--series <int>`: series per panel (default: `3`)
- `--events <int>`: event markers per panel (default: `3`)
- `--seed <int>`: RNG seed (default: `97`)

Animation/render flags:
- `--animate`: enable moving cursor/dot overlays
- `--duration <float>` (default: `8.0`)
- `--fps <int>` (default: `24`)
- `--width <int>` / `--height <int>` (defaults: `1900` / `1180`)
- `--format {svg,gif,mp4}` (default: `svg`)
- `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples.py --format svg --output tufte_small_multiples.svg
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples.py --format gif --animate --panels 12 --columns 4 --points 60 --duration 10 --fps 24 --output tufte_small_multiples_animated.gif
```

Notes:
- `svg` mode exports a static high-density dashboard (no scene playback).
- `gif/mp4` modes use animated cursors and focus dots to compare trend progression.
- Useful foundation for richer Tufte variants (small multiples by cohort, uncertainty bands, annotation callouts).

## tufte_small_multiples_extended.py

Purpose:
- Extended analytical dashboard with higher-information encodings:
  - uncertainty/confidence bands
  - panel-level callouts/annotations
  - real data adapters (`synthetic`, `csv`, `json`)
  - richer comparative overlays (cohort facets + rank-shift summaries)

Run:
```bash
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples_extended.py [flags]
```

Data adapter flags:
- `--data-source {synthetic,csv,json}` (default: `synthetic`)
- `--data-path <path>` (required for `csv/json`)
- expected schema (CSV columns or JSON keys):
  - `panel`, `cohort`, `time`, `value`, `lower`, `upper`, `event`(optional)

Synthetic generation flags:
- `--panels <int>` (default: `9`)
- `--cohorts <int>` (default: `5`)
- `--points <int>` (default: `52`)
- `--seed <int>` (default: `121`)

Layout/highlight flags:
- `--columns <int>` (default: `3`)
- `--highlight-cohort <label>` (defaults to last cohort if omitted/invalid)
- `--width <int>` / `--height <int>` (defaults: `2100` / `1320`)
- `--output <path>` (`.svg` export)

Examples:
```bash
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples_extended.py --data-source synthetic --panels 12 --cohorts 6 --points 64 --columns 4 --output tufte_extended.svg
./.venv/bin/python examples-other/data/tufte/tufte_small_multiples_extended.py --data-source csv --data-path ./my_metrics.csv --columns 3 --highlight-cohort Cohort_A --output tufte_extended_csv.svg
```

Notes:
- This is currently a static SVG analysis dashboard by design.
- It is intended as an extensible base for future:
  - uncertainty glyph variants
  - cohort comparison lenses
  - richer annotation grammars
  - external dataset adapters.

## tufte_wide_to_long.py

Purpose:
- Companion converter utility to map wide tables into the long schema used by
  `tufte_small_multiples_extended.py`.

Run:
```bash
./.venv/bin/python examples-other/data/converters/tufte_wide_to_long.py --input <wide.csv|wide.json> --output <long.csv|long.json>
```

Core flags:
- `--input`, `--output` (required)
- `--input-format {csv,json,auto}` (default: `auto`)
- `--output-format {csv,json,auto}` (default: `auto`)
- `--wide-mode {row,grouped}` (default: `row`)
- `--panel-col` (default: `panel`)
- `--cohort-col` (default: `cohort`)
- `--time-columns` comma list (explicit time/value columns)
- `--exclude-columns` comma list (inference exclusions)
- `--time-regex` (default: `^(t?\\d+(\\.\\d+)?)$`)
- `--panel-time-regex` (default: `^(?P<panel>.+)_(?P<time>t?\\d+(?:\\.\\d+)?)$`)
- `--default-panel`, `--default-cohort`
- `--strict` (fail if no time columns inferred)

Wide-format expectations:
- `row` mode:
  - each row is one `(panel, cohort)` record with many time columns (e.g., `t0,t1,t2,...`)
- `grouped` mode:
  - each row is one `cohort` record with grouped panel columns (e.g., `Revenue_t0, Revenue_t1, Cost_t0, Cost_t1`)
  - panel/time split is controlled by `--panel-time-regex`
- Optional uncertainty companions (any of these patterns):
  - `lower_t0` / `upper_t0`
  - `t0_lower` / `t0_upper`
  - `t0_lo` / `t0_hi`
- Optional event companions:
  - `event_t0` or `t0_event`

Output long schema:
- `panel`, `cohort`, `time`, `value`, `lower`, `upper`, `event`

Examples:
```bash
./.venv/bin/python examples-other/data/converters/tufte_wide_to_long.py --input ./wide_metrics.csv --output ./long_metrics.csv
./.venv/bin/python examples-other/data/converters/tufte_wide_to_long.py --input ./wide_metrics.csv --output ./long_metrics.json --output-format json
./.venv/bin/python examples-other/data/converters/tufte_wide_to_long.py --input ./wide_metrics.csv --output ./long_metrics.csv --time-columns t0,t1,t2,t3
./.venv/bin/python examples-other/data/converters/tufte_wide_to_long.py --input ./wide_grouped.csv --output ./long_grouped.csv --wide-mode grouped
```

Notes:
- If uncertainty columns are missing for a timepoint, `lower`/`upper` default to `value`.
- Time parsing supports `t0`, `t1.5`, or numeric column names; otherwise fallback is column index.

## hybrid_control_systems.py

Purpose:
- Hybrid automaton stress test combining:
  - discrete modes (`CRUISE`, `AVOID`, `RECOVER`, `HOLD`)
  - continuous dynamics (position/velocity integration)
  - guard-based transitions (obstacle proximity, clearance, goal events)
- Includes cinematic camera cues and zoom with normalized frame export

Run:
```bash
./.venv/bin/python examples-other/animation/operations/hybrid_control_systems.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `131`)
- `--obstacles <int>` (default: `6`)

Camera/world flags:
- `--camera {track,scripted,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2800` / `1900`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `920` / `600`)
- `--zoom-min <float>` / `--zoom-max <float>` (defaults: `0.58` / `1.00`)
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/hybrid_control_systems.py --output hybrid_control.gif
./.venv/bin/python examples-other/animation/operations/hybrid_control_systems.py --camera scripted --obstacles 10 --duration 14 --dt 0.02 --fps 30 --format mp4 --output hybrid_control_scripted.mp4
```

Notes:
- Script prints transition logs with reasons, useful for debugging guard logic.
- Export path normalizes camera-cropped frames to fixed output dimensions.

## animation_supply_chain_resilience.py

Purpose:
- Supply-chain resilience stress test combining:
  - directed logistics network (`ports -> hubs -> stores`)
  - disruption windows and degraded corridor capacity
  - adaptive rerouting and hub balancing under pressure
- Visual overlays for phase changes and node stress (inventory deficit/backlog)

Run:
```bash
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.04`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `211`)
- `--scenario {baseline,port_strike,demand_surge,multi_shock}` (default: `baseline`)
- `--policy {balanced,service_first,cost_first}` (default: `balanced`)
- `--demand-scale <float>` (default from scenario)
- `--supply-rate <float>` (default from scenario)
- `--route-capacity-scale <float>` (default from scenario)
- `--alt-route-boost <float>` (default from scenario)
- `--hub-balance-gain <float>` (default from scenario)
- `--backlog-relief-rate <float>` (default from scenario)
- `--packets-max <int>` (default: `480`)
- `--packet-size <float>` (default: `6.0`)

Disruption flags:
- `--shock-start-ratio <float>` (default from scenario)
- `--shock-duration-ratio <float>` (default from scenario)
- `--shock-severity <float>` (default from scenario)
- `--shock-target {none,west,east,both}` (default from scenario)
- `--demand-spike <float>` (default from scenario)
- `--store-spike {none,A,B,both}` (default from scenario)

Camera/world flags:
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2500` / `1550`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--report-json <path>` optional metrics report for scenario comparison
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience.py --scenario baseline --output supply_chain_resilience.gif
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience.py --scenario port_strike --policy service_first --report-json ./port_strike_report.json --output supply_chain_port_strike.gif
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience.py --scenario multi_shock --camera-mode track --duration 14 --format mp4 --output supply_chain_resilience_heavy.mp4
```

Notes:
- Script prints diagnostics including service level, peak backlog, and dominant phase.
- `--report-json` is useful for A/B comparisons across scenarios and policy variants.
- If MP4 dimensions are not codec-friendly (not divisible by 16), imageio/ffmpeg may auto-resize output.

## animation_supply_chain_resilience_runner.py

Purpose:
- Companion batch runner for `animation_supply_chain_resilience.py`
- Executes scenario/policy matrices, collects per-run JSON metrics, and ranks outcomes
- Writes leaderboard outputs for quick A/B comparison

Run:
```bash
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `211`)
- `--seed-step <int>` (default: `37`)

Forwarded simulation/render flags:
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.04`)
- `--fps <int>` (default: `16`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--format {gif,mp4}` (default: `gif`)

Output/control flags:
- `--output-dir <path>` (default: `supply_chain_resilience_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run rendered media (otherwise stored in scratch dir)
- `--fail-fast` stop immediately on first failing run

Ranking logic:
- Sorted by:
  - highest `service_level`
  - then lowest `peak_total_backlog`
  - then lowest `total_unmet`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience_runner.py --duration 4 --fps 10 --output-dir ./supply_chain_compare
./.venv/bin/python examples-other/animation/operations/animation_supply_chain_resilience_runner.py --scenarios baseline,port_strike,multi_shock --policies balanced,service_first --repeats 2 --save-media --output-dir ./supply_chain_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: flat ranked table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failures list
- `<output-dir>/reports/*.json`: raw per-run reports from the animation script

## animation_incident_response_playbook.py

Purpose:
- Incident response stress harness combining:
  - service dependency graph (`edge/api/auth/queue/worker/db`)
  - attack injection + compromise propagation
  - finite playbook phases (`DETECT`, `TRIAGE`, `CONTAIN`, `ERADICATE`, `RECOVER`, `POSTMORTEM`)
- Useful for comparing response policies and scenario severity in a concrete ops context

Run:
```bash
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `151`)
- `--scenario {credential_stuffing,lateral_movement,data_exfiltration,ransomware_drill}` (default: `credential_stuffing`)
- `--policy {manual,assisted,autonomous}` (default: `assisted`)

Scenario override flags:
- `--attack-target <name>` (default from scenario)
- `--attack-start-ratio <float>` (default from scenario)
- `--attack-duration-ratio <float>` (default from scenario)
- `--attack-intensity <float>` (default from scenario)
- `--propagation-rate <float>` (default from scenario)
- `--traffic-spike <float>` (default from scenario)
- `--alert-noise <float>` (default from scenario)

Render/report flags:
- `--packet-rate <float>` (default: `2.6`)
- `--packets-max <int>` (default: `560`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2500` / `1600`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--report-json <path>` optional metrics output for runner/comparison workflows
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook.py --scenario credential_stuffing --policy assisted --output incident_playbook.gif
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook.py --scenario ransomware_drill --policy manual --duration 14 --report-json ./incident_manual.json --output incident_manual.gif
```

Notes:
- Script prints key metrics: `service_level`, `peak_impact`, `breach_time`, `mttd`, and `mttr`.
- `--report-json` emits a stable schema intended for matrix runner aggregation.

## animation_incident_response_playbook_runner.py

Purpose:
- Companion matrix runner for `animation_incident_response_playbook.py`
- Executes scenario/policy combinations with repeat seeds and ranks outcomes

Run:
```bash
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `151`)
- `--seed-step <int>` (default: `31`)

Forwarded run flags:
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `16`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--format {gif,mp4}` (default: `gif`)

Output/control flags:
- `--output-dir <path>` (default: `incident_response_playbook_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run rendered media
- `--fail-fast` stop at first failed run

Ranking logic:
- Sorted by:
  - highest `service_level`
  - then lowest `mttr`
  - then lowest `peak_impact`
  - then lowest `breach_time`

Examples:
```bash
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook_runner.py --duration 4 --fps 10 --output-dir ./incident_compare
./.venv/bin/python examples-other/animation/operations/animation_incident_response_playbook_runner.py --scenarios credential_stuffing,ransomware_drill --policies manual,autonomous --repeats 2 --save-media --output-dir ./incident_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: ranked flat table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failure details
- `<output-dir>/reports/*.json`: per-run raw reports from playbook script

## animation_grid_contingency_cascade.py

Purpose:
- Grid contingency cascade stress harness combining:
  - topology stress on generator/substation/load graph
  - explicit state guards (`trip`, `isolate`, `recover`) with hysteresis/cooldowns
  - cascading dynamics with bounded ramps and clamped overload behavior
- Designed for deterministic scenario comparison and interpretability-first diagnostics

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `97`)
- `--scenario {line_trip,substation_loss,demand_spike,multi_fault}` (default: `line_trip`)
- `--policy {conservative,balanced,aggressive}` (default: `balanced`)

Scenario override flags:
- `--event-start-ratio <float>` (default from scenario)
- `--event-duration-ratio <float>` (default from scenario)
- `--fault-line <name>` (default from scenario)
- `--fault-substation <name>` (default from scenario)
- `--demand-spike-zone <name>` (default from scenario)
- `--demand-spike-scale <float>` (default from scenario)
- `--event-severity <float>` (default from scenario)

Render/report flags:
- `--packet-rate <float>` (default: `2.3`)
- `--packets-max <int>` (default: `640`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2500` / `1550`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--report-json <path>` optional metrics output for matrix runner workflows
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade.py --scenario line_trip --policy balanced --output grid_cascade.gif
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade.py --scenario multi_fault --policy conservative --duration 14 --report-json ./grid_multi_fault.json --output grid_multi_fault.gif
```

Required day-one metrics (in `--report-json`):
- `peak_overload`
- `island_count`
- `shed_load`
- `recovery_time`

Notes:
- Guard behavior includes overload trip hold, isolate hold, cooldown windows, and stable recover hold.
- Dynamics are bounded with load/gen ramp limits and clamped node/edge stress values to reduce runaway oscillation.

## animation_grid_contingency_cascade_runner.py

Purpose:
- Companion matrix runner for `animation_grid_contingency_cascade.py`
- Executes scenario/policy combinations and ranks resilience outcomes

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `97`)
- `--seed-step <int>` (default: `19`)

Forwarded run flags:
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `16`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--format {gif,mp4}` (default: `gif`)

Output/control flags:
- `--output-dir <path>` (default: `grid_contingency_cascade_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run rendered media
- `--fail-fast` stop at first failed run

Ranking logic:
- Sorted by:
  - highest `service_level`
  - then lowest `shed_load`
  - then lowest `peak_overload`
  - then lowest `recovery_time`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade_runner.py --duration 4 --fps 10 --output-dir ./grid_cascade_compare
./.venv/bin/python examples-other/animation/topology/animation_grid_contingency_cascade_runner.py --scenarios line_trip,multi_fault --policies conservative,aggressive --repeats 2 --save-media --output-dir ./grid_cascade_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: ranked flat table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failure details
- `<output-dir>/reports/*.json`: per-run raw reports from cascade script

## animation_sugiyama_story_workflow.py

Purpose:
- Animated Sugiyama-style DAG story harness focused on workflow operations
- Embeds notation/legend elements directly in the rendered canvas (not external docs)
- Uses scenario/policy/report pattern for reproducible behavior comparisons

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_sugiyama_story_workflow.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `173`)
- `--scenario {validation_storm,enrichment_latency,review_backlog,downstream_degradation}` (default: `validation_storm`)
- `--policy {strict,balanced,throughput}` (default: `balanced`)

Scenario override flags:
- `--event-start-ratio <float>` (default from scenario)
- `--event-duration-ratio <float>` (default from scenario)
- `--stress-intensity <float>` (default from scenario)
- `--replay-factor <float>` (default from scenario)
- `--branch-bias <float>` (default from scenario)

Render/report flags:
- `--packet-rate <float>` (default: `2.5`)
- `--packets-max <int>` (default: `620`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2600` / `1600`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--report-json <path>` optional metrics output
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_sugiyama_story_workflow.py --scenario validation_storm --policy balanced --output sugiyama_story.gif
./.venv/bin/python examples-other/animation/topology/animation_sugiyama_story_workflow.py --scenario review_backlog --policy strict --camera-mode track --duration 14 --report-json ./sugiyama_story_review.json --output sugiyama_story_review.gif
```

Notes:
- Notation panel in-canvas defines visual semantics:
  - node halo width, queue bars, edge width, and packet colors
- Script intentionally includes richer inline comments around layout, phase guards, and bounded dynamics.

## animation_cicd_dependency_risk.py

Purpose:
- CI/CD dependency risk scaffold using a layered DAG pipeline
- Combines stage risk propagation, queue pressure, and policy-driven gating/recovery
- Includes in-canvas legend/notation and structured metrics output

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk.py [flags]
```

Control/sim flags:
- `--duration <float>` (default: `12.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `211`)
- `--scenario {flaky_tests,vuln_spike,infra_drift,hotfix_rush}` (default: `flaky_tests`)
- `--policy {strict,balanced,fast_track}` (default: `balanced`)

Scenario override flags:
- `--event-start-ratio <float>` (default from scenario)
- `--event-duration-ratio <float>` (default from scenario)
- `--risk-intensity <float>` (default from scenario)
- `--replay-factor <float>` (default from scenario)
- `--approval-drag <float>` (default from scenario)

Render/report flags:
- `--packet-rate <float>` (default: `2.5`)
- `--packets-max <int>` (default: `620`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--world-width <int>` / `--world-height <int>` (defaults: `2600` / `1600`)
- `--camera-width <float>` / `--camera-height <float>` (defaults: `980` / `620`)
- `--report-json <path>` optional metrics output
- `--format {gif,mp4}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk.py --scenario flaky_tests --policy balanced --output cicd_dependency_risk.gif
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk.py --scenario hotfix_rush --policy fast_track --camera-mode track --duration 14 --report-json ./cicd_hotfix.json --output cicd_hotfix.gif
```

Notes:
- Key metrics: `success_rate`, `peak_stage_risk`, `blocked_stage_count`, `mttd`, `mttr`.
- Designed as scaffold for broader delivery-governance examples.

## animation_cicd_dependency_risk_runner.py

Purpose:
- Companion matrix runner for `animation_cicd_dependency_risk.py`
- Executes scenario/policy sweeps and ranks outcomes via leaderboard outputs

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `211`)
- `--seed-step <int>` (default: `17`)

Forwarded run flags:
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `16`)
- `--camera-mode {fixed,track,hybrid}` (default: `hybrid`)
- `--format {gif,mp4}` (default: `gif`)

Output/control flags:
- `--output-dir <path>` (default: `cicd_dependency_risk_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run rendered media
- `--fail-fast` stop at first failed run

Ranking logic:
- Sorted by:
  - highest `success_rate`
  - then lowest `blocked_stage_count`
  - then lowest `peak_stage_risk`
  - then lowest `mttr`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk_runner.py --duration 4 --fps 10 --output-dir ./cicd_risk_compare
./.venv/bin/python examples-other/animation/topology/animation_cicd_dependency_risk_runner.py --scenarios flaky_tests,hotfix_rush --policies strict,fast_track --repeats 2 --save-media --output-dir ./cicd_risk_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: ranked flat table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failure details
- `<output-dir>/reports/*.json`: per-run raw reports

## graph_routing_showcase.py

Purpose:
- Compare routing strategies on the same graph in one scene (`compare`) or single-mode renders
- Demonstrates obstacle-aware orthogonal routing with `tesserax.path.Grid`
- Includes in-canvas notation/legend and readability metrics

Run:
```bash
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase.py [flags]
```

Core flags:
- `--scenario {balanced,hotspot_h,cross_region,downstream_pressure}` (default: `balanced`)
- `--policy {baseline,stability,throughput}` (default: `baseline`)
- `--mode {compare,straight,curved,orthogonal,bundled}` (default: `compare`)
- `--topology {default,sparse,dense,clustered}` (default: `default`)
- `--duration <float>` (default: `11.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `24`)
- `--seed <int>` (default: `251`)

Routing/control flags:
- `--curvature <float>` (default: `0.22`)
- `--bundle-x-ratio <float>` (default: `0.55`)
- `--bundle-lane-step <float>` (default: `18.0`)
- `--turn-penalty <float>` (default: `1.4`)
- `--packet-rate <float>` (default: `2.1`)
- `--packets-max <int>` (default: `760`)
- `--packet-speed <float>` pixels/sec (default: `350.0`)

Scenario override flags:
- `--pulse-start-ratio <float>` (default from scenario)
- `--pulse-duration-ratio <float>` (default from scenario)
- `--intensity <float>` (default from scenario)
- `--burstiness <float>` (default from scenario)

Render/report flags:
- `--camera-mode {fixed,track,hybrid}` (default: `fixed`)
- `--world-width <int>` / `--world-height <int>`
- `--camera-width <float>` / `--camera-height <float>`
- `--format {gif,mp4}` and `--output <path>`
- `--report-json <path>` optional metrics report

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase.py --mode compare --output graph_routing_showcase.gif
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase.py --mode orthogonal --topology dense --scenario hotspot_h --policy stability --report-json ./routing_orthogonal_dense.json --output routing_orthogonal_dense.gif
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase.py --mode bundled --topology clustered --camera-mode hybrid --format mp4 --output routing_bundled_clustered.mp4
```

Notes:
- `compare` renders a 2x2 panel of `straight/curved/orthogonal/bundled`.
- Topology presets let you stress routing in different graph densities/shapes without hand-editing script internals.
- `bundled` now uses destination-aware trunk/lane guides, which usually reduces crossings versus a single global corridor.
- Report metrics include per-mode `score`, `crossings`, `avg_bends`, `ink`, and packet counts.

## graph_routing_showcase_runner.py

Purpose:
- Companion matrix runner for `graph_routing_showcase.py`
- Produces a readability leaderboard across scenario/policy/topology/mode combinations

Run:
```bash
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--topologies <csv|all>` (default: `all`)
- `--modes <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `251`)
- `--seed-step <int>` (default: `19`)

Forwarded render flags:
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `16`)
- `--camera-mode {fixed,track,hybrid}` (default: `fixed`)
- `--packet-rate <float>` (default: `1.6`)
- `--packets-max <int>` (default: `520`)
- `--format {gif,mp4}` (default: `gif`)

Output/control flags:
- `--output-dir <path>` (default: `graph_routing_showcase_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run artifacts
- `--fail-fast` stop at first failed run

Ranking logic:
- Sorted by:
  - highest `score`
  - then lowest `crossings`
  - then lowest `avg_bends`
  - then lowest `ink`

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase_runner.py --output-dir ./routing_compare
./.venv/bin/python examples-other/animation/topology/graph_routing_showcase_runner.py --scenarios hotspot_h,cross_region --policies baseline,stability --topologies sparse,dense --modes straight,orthogonal,bundled --repeats 2 --save-media --output-dir ./routing_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: ranked flat table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failure details
- `<output-dir>/reports/*.json`: per-run raw reports

## animation_regression_suite.py

Purpose:
- Deterministic animation regression harness with fixed fixtures and frame-hash signatures
- Produces machine-readable signatures for CI validation and baseline comparisons
- Uses scenario/policy controls while keeping seeded output reproducible

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_regression_suite.py [flags]
```

Core flags:
- `--scenario {baseline,stress,recovery}` (default: `baseline`)
- `--policy {strict,balanced,throughput}` (default: `balanced`)
- `--fixture {pipeline,ring,mesh}` (default: `pipeline`)
- `--duration <float>` (default: `6.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `16`)
- `--seed <int>` (default: `311`)

Traffic/hash flags:
- `--packet-rate <float>` (default: `2.0`)
- `--packets-max <int>` (default: `520`)
- `--packet-speed <float>` (default: `320.0`)
- `--hash-sample-step <int>` (default: `1`)
- `--signature-ref <path>` optional reference signature/report
- `--signature-out <path>` optional raw signature output

Render/report flags:
- `--save-media` persist gif/mp4 output (default is report-only mode)
- `--format {gif,mp4}` and `--output <path>`
- `--report-json <path>` optional full run report

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_regression_suite.py --fixture pipeline --report-json ./reg_pipeline.json
./.venv/bin/python examples-other/animation/topology/animation_regression_suite.py --fixture mesh --scenario stress --policy strict --save-media --output regression_mesh.gif --report-json ./reg_mesh.json
./.venv/bin/python examples-other/animation/topology/animation_regression_suite.py --fixture ring --signature-ref ./baseline/ring_sig.json --report-json ./reg_ring_compare.json
```

Notes:
- Report includes `metrics.signature` with `combined_hash`, `first_hash`, `mid_hash`, and `last_hash`.
- `status=fail` occurs when `--signature-ref` is provided and signature checks mismatch.

## animation_regression_suite_runner.py

Purpose:
- Matrix runner for deterministic regression fixtures
- Supports repeat-stability checks, optional baseline comparison, and baseline generation

Run:
```bash
./.venv/bin/python examples-other/animation/topology/animation_regression_suite_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--fixtures <csv|all>` (default: `all`)
- `--repeats <int>` (default: `2`)
- `--seed-start <int>` (default: `311`)
- `--seed-step <int>` (default: `0`)

Forwarded run flags:
- `--duration <float>` (default: `4.0`)
- `--dt <float>` (default: `0.03`)
- `--fps <int>` (default: `12`)
- `--packet-rate <float>` (default: `1.8`)
- `--packets-max <int>` (default: `420`)
- `--hash-sample-step <int>` (default: `1`)
- `--format {gif,mp4}` and optional `--save-media`

Baseline flags:
- `--baseline-dir <path>` optional signature directory
- `--write-baseline` write computed signatures to baseline dir
- `--overwrite-baseline` overwrite existing baseline files

Output/control flags:
- `--output-dir <path>` (default: `animation_regression_suite_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--fail-fast`

Ranking logic:
- Sorted by:
  - `status=pass` first
  - repeat-stable groups first (`repeat_unique_hashes == 1`)
  - lowest `mismatch_count`
  - then highest packet visibility

Examples:
```bash
./.venv/bin/python examples-other/animation/topology/animation_regression_suite_runner.py --output-dir ./regression_compare
./.venv/bin/python examples-other/animation/topology/animation_regression_suite_runner.py --fixtures pipeline,mesh --repeats 3 --seed-step 0 --write-baseline --baseline-dir ./regression_baseline --output-dir ./regression_compare_baseline
./.venv/bin/python examples-other/animation/topology/animation_regression_suite_runner.py --baseline-dir ./regression_baseline --repeats 2 --seed-step 0 --output-dir ./regression_compare_verify
```

Outputs:
- `<output-dir>/leaderboard.csv`
- `<output-dir>/leaderboard.json`
- `<output-dir>/reports/*.json`

## static_data_lineage_map.py

Purpose:
- Static lineage map scaffold with force-directed topology and risk overlays
- Suited for governance/reporting snapshots where animation is not required
- Uses scenario/policy/report pattern for deterministic comparative outputs

Run:
```bash
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map.py [flags]
```

Control flags:
- `--seed <int>` (default: `227`)
- `--scenario {late_arrivals,schema_break,source_corruption,upstream_outage}` (default: `late_arrivals`)
- `--policy {strict,balanced,fast}` (default: `balanced`)
- `--corruption-injection <float>` (default from scenario)
- `--freshness-decay <float>` (default from scenario)
- `--schema-drift <float>` (default from scenario)
- `--world-width <int>` / `--world-height <int>` (defaults: `2200` / `1400`)
- `--layout-iterations <int>` (default: `220`)
- `--report-json <path>` optional metrics output
- `--format {svg}` and `--output <path>`

Examples:
```bash
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map.py --scenario late_arrivals --policy balanced --output lineage_map.svg
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map.py --scenario schema_break --policy strict --report-json ./lineage_schema_break.json --output lineage_schema_break.svg
```

Notes:
- In-canvas notation defines risk/freshness semantics.
- Metrics include `global_trust`, `lineage_risk`, `blast_radius`, `unresolved_alerts`.

## static_data_lineage_map_runner.py

Purpose:
- Companion matrix runner for `static_data_lineage_map.py`
- Generates ranked trust/risk leaderboards across scenario/policy sweeps

Run:
```bash
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map_runner.py [flags]
```

Core flags:
- `--scenarios <csv|all>` (default: `all`)
- `--policies <csv|all>` (default: `all`)
- `--repeats <int>` (default: `1`)
- `--seed-start <int>` (default: `227`)
- `--seed-step <int>` (default: `13`)
- `--format {svg}` (default: `svg`)
- `--world-width <int>` / `--world-height <int>`
- `--layout-iterations <int>`

Output/control flags:
- `--output-dir <path>` (default: `static_data_lineage_map_comparison`)
- `--csv-name <file>` (default: `leaderboard.csv`)
- `--json-name <file>` (default: `leaderboard.json`)
- `--save-media` keep per-run map files
- `--fail-fast` stop at first failed run

Ranking logic:
- Sorted by:
  - highest `global_trust`
  - then lowest `lineage_risk`
  - then lowest `unresolved_alerts`
  - then lowest `blast_radius`

Examples:
```bash
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map_runner.py --output-dir ./lineage_compare
./.venv/bin/python examples-other/static/lineage/static_data_lineage_map_runner.py --scenarios late_arrivals,schema_break --policies strict,fast --repeats 2 --save-media --output-dir ./lineage_compare_media
```

Outputs:
- `<output-dir>/leaderboard.csv`: ranked flat table
- `<output-dir>/leaderboard.json`: summary + ranked runs + failure details
- `<output-dir>/reports/*.json`: per-run raw reports



- `hybrid_control_systems.py`
  - Coupled discrete state logic and continuous dynamics with branch outcomes
- `animation_supply_chain_resilience.py`
  - Logistics disruption + rerouting + backlog recovery in one scenario

Advanced visualization directions to explore:

- State-based mechanics:
  - Finite-state automata with guard conditions, timed transitions, and event overlays
  - Hybrid control systems (state + continuous dynamics) with branch outcomes
- Physics-informed interaction diagrams:
  - Feynman-like topologies, interaction vertices, and semantic edge encodings
- Information-dense explanatory graphics:
  - Tufte-style small multiples, direct labels, annotation layers, minimal chartjunk

Potential engine extensions that unlock these:

- `Camera`/`Scene`:
  - Built-in fixed-output rendering mode with automatic frame normalization
- `Path`/`Line`:
  - Native `point_at(t)` / tangent methods for robust follow/orient animations
- `Animation`:
  - First-class state-machine timeline API (states/events/guards/transitions)
- Layout/routing:
  - Orthogonal/bundled/obstacle-avoiding edge routing for dense graph diagrams
- Physics:
  - Joint/constraint presets and collision event hooks for semantic overlays

Recommended proof-suite order:
1. `animation_flow_dag.py`
2. `animation_attention_heads.py`
3. `animation_packet_ring.py`
4. `animation_residual_pipeline.py`
5. `animation_topology_morph.py`
6. `animation_physics_overlay.py`
7. `animation_camera_track.py`
8. `animation_camera_zoom_stress.py`
9. `animation_state_machine_cinematics.py`
10. `feynman_like_interactions.py`
11. `tufte_small_multiples.py`
12. `tufte_small_multiples_extended.py`
13. `tufte_wide_to_long.py`
14. `hybrid_control_systems.py`
15. `animation_supply_chain_resilience.py`
16. `animation_supply_chain_resilience_runner.py`
17. `animation_incident_response_playbook.py`
18. `animation_incident_response_playbook_runner.py`
19. `animation_grid_contingency_cascade.py`
20. `animation_grid_contingency_cascade_runner.py`
21. `animation_sugiyama_story_workflow.py`
22. `animation_cicd_dependency_risk.py`
23. `animation_cicd_dependency_risk_runner.py`
24. `static_data_lineage_map.py`
25. `static_data_lineage_map_runner.py`
26. `graph_routing_showcase.py`
27. `graph_routing_showcase_runner.py`
28. `animation_regression_suite.py`
29. `animation_regression_suite_runner.py`

## Planned High-Value Scripts (Roadmap)

These are candidate next scripts for proving additional animation capabilities:
