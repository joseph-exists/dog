# SVG Steel Thread Interface Assessment

## Context

The next milestone is no longer a broad capability inventory. The goal is to prove the steel thread and the golden path with a small, intentional subset.

The questions for this pass are:

1. Among animation-oriented scripts, which have the widest user-input surface?
2. Among static SVG scripts, which is the most broadly useful across domains while still enabling diverse visualizations?
3. How should `tufte` and `sugiyama` fit into that assessment?
4. What is the right frontend/backend interaction shape for this subset?

## Key Finding Up Front

There are currently no registered `animation/*` scripts that advertise SVG output.

Current `animation/*` scripts are `gif`/`mp4` oriented.

The one important bridge surface is:

- `examples.data.tufte.tufte_small_multiples`

That script supports:

- `svg`
- `gif`
- `mp4`

So if the near-term steel thread remains SVG-first, `tufte_small_multiples` is the closest thing to an animation-adjacent script that still fits the SVG milestone.

## Assessment 1: Widest Input Surface Among Animation-Oriented Scripts

For pure animation-oriented scripts, the broadest parameter surfaces appear to be:

1. `examples.animation.operations.animation_supply_chain_resilience`
2. `examples.animation.topology.graph_routing_showcase`
3. `examples.animation.topology.animation_sugiyama_story_workflow`
4. `examples.animation.physics.animation_physics_overlay`

### `animation_supply_chain_resilience`

Why it stands out:

- richest operational parameter surface
- multiple scenario and policy controls
- camera configuration
- disruption timing controls
- capacity and backlog behavior controls
- packet controls

Assessment:

- widest general-purpose user input surface among the animation scripts reviewed
- strong candidate if the product later wants a highly tunable, scenario-driven animated interface

Tradeoff:

- this is broad, but it is also relatively specialized to supply-chain/logistics narratives

### `graph_routing_showcase`

Why it stands out:

- broad topology/routing control surface
- scenario and policy inputs
- routing mode selection
- topology selection
- packet and route geometry controls
- camera controls

Assessment:

- likely the broadest topology-oriented animation interface
- especially good if future users want to manipulate graph-routing behavior

Tradeoff:

- conceptually powerful, but more technical than a first general-purpose frontend surface

### `animation_sugiyama_story_workflow`

Why it matters:

- strong domain interest from your users
- meaningful workflow-story interface
- scenario and policy structure
- event timing controls
- packet controls
- camera controls

Assessment:

- not the widest animation input surface overall
- but one of the strongest story-driven topology interfaces
- likely a better product-facing candidate than some broader but more niche animation scripts

Tradeoff:

- currently not SVG-capable in the registered contract
- better aligned with the later GIF/MP4 milestone unless you explicitly treat it as a deferred-but-priority path

### `animation_physics_overlay`

Why it matters:

- relatively broad physical simulation surface
- strong technical demonstration value

Assessment:

- broad and impressive
- less obviously tied to the broadest set of user-facing domains than routing, workflow, or Tufte-style surfaces

## Assessment 2: Best Static SVG Surface For Broad Domain Coverage

For static SVG generation, the strongest broadly applicable script is:

- `examples.static.core.design_patterns_gallery`

### Why `design_patterns_gallery` is the best cross-domain static choice

It already contains multiple visualization families:

- state chart
- timeline
- network diagnostics panel

That makes it different from the other static scripts:

- `simple_convolution` is too narrow
- `static_data_lineage_map` is very strong, but domain-shaped
- `neural_network_refined` is visually rich, but specialized
- `tufte_small_multiples_extended` is broad for analytical/reporting use, but still chart-centric

`design_patterns_gallery` is the strongest candidate for broad diversity because it is already organized around reusable visual recipes rather than one story.

### Important caveat

It is batch-oriented, not single-render-oriented.

That means it is best treated in the interface as several named options:

- State Chart
- Timeline
- Network Diagnostics

not as one opaque “gallery” action that returns multiple SVGs unexpectedly.

## Assessment 3: Tufte and Sugiyama

These deserve explicit inclusion because they matter to your users, even though they do not sit in the same exact technical bucket.

### Tufte

The strongest Tufte-related candidates are:

1. `examples.data.tufte.tufte_small_multiples`
2. `examples.data.tufte.tufte_small_multiples_extended`

#### `tufte_small_multiples`

Why it matters:

- supports `svg`, `gif`, and `mp4`
- bridges the current SVG milestone and a later animation milestone
- gives users a consistent conceptual model across static and animated output

Assessment:

- highest strategic value of the Tufte scripts for the steel thread
- best bridge between SVG MVP and later richer media support

Recommended role:

- include now in the assessment and probably in the interface plan
- likely expose first as SVG
- keep the idea of later animation expansion visible but not active yet

#### `tufte_small_multiples_extended`

Why it matters:

- richer analytical structure
- data-source flexibility
- stronger report-oriented visualization surface

Assessment:

- strongest pure-SVG Tufte option for structured analytical use
- good follow-on or advanced option after the simplest SVG allowlist is proven

Recommended role:

- include in the subset
- probably not the very first option a user sees
- better placed as an “Advanced Tufte” interface

### Sugiyama

Primary script:

- `examples.animation.topology.animation_sugiyama_story_workflow`

Assessment:

- important because of known user demand
- strong future golden-path candidate for topology/workflow storytelling
- not currently part of the SVG-only milestone in strict terms

Recommended role:

- include it in the assessed subset
- expose it in the interface plan as “coming next” or “video/animation path”
- do not force it into the SVG steel thread if the service contract does not support that today

## Recommended Subset For Interface Design

For the interface-design thought exercise, I recommend working with this subset:

### Steel Thread SVG Set

- `examples.static.core.design_patterns_gallery`
- `examples.static.lineage.static_data_lineage_map`
- `examples.data.tufte.tufte_small_multiples`
- `examples.data.tufte.tufte_small_multiples_extended`

### Included Because Of Strategic Importance

- `examples.animation.topology.animation_sugiyama_story_workflow`

### Included Because It Represents The Broadest Animation Input Surface

- `examples.animation.operations.animation_supply_chain_resilience`
- `examples.animation.topology.graph_routing_showcase`

## Interface Recommendation

## Short Answer

Yes, the overall shape is basically right.

But I would tighten the boundaries slightly:

- the frontend should not need to understand the worker or API chain in detail
- the backend should own the orchestration contract
- the frontend should deal in:
  - catalog entry
  - parameter form
  - submit
  - queued/running/completed status
  - final artifact/result

## Recommended User Interaction Shape

### Step 1: User sees a curated list

The frontend should show a curated list of approved interfaces, not raw script IDs.

Each card should contain:

- title
- short description
- output type
- complexity level
- example preview text

Recommended first grouping:

- Patterns
- Analytics
- Domain Maps
- Story Workflows

Concrete examples:

- State Chart
- Timeline
- Network Diagnostics
- Data Lineage Map
- Tufte Small Multiples
- Tufte Small Multiples Extended
- Sugiyama Story Workflow

### Step 2: Progressive elaboration after selection

After selection, show parameters in three layers.

#### Layer 1: Starter

Show only the small set of controls most users need.

Examples:

- preset
- scenario
- policy
- seed
- width
- height

#### Layer 2: Advanced

Reveal richer but still understandable controls.

Examples:

- panel count
- packet rate
- camera mode
- topology choice
- route or stress intensity

#### Layer 3: Expert / Command View

Show the exact command or parameter payload being constructed.

Purpose:

- debugging
- trust
- reproducibility
- operator confidence

This aligns well with your “shown/given the commands with progressive elaboration” idea.

I would expose:

- human-friendly form controls first
- generated command or request payload second

not the other way around

## Recommended Backend Flow

The overall async shape is right, but I would phrase it more precisely as:

1. Frontend selects an approved interface.
2. Frontend sends a request to the `dog` backend.
3. `dog` backend translates the UI state into a known `tesser` script request.
4. `dog` backend submits the request to `tesser` using one enqueue path.
5. `tesser` resolves runtime profile and writes the job.
6. `tesser` worker executes the render.
7. Status and final result come back to `dog`.
8. Frontend updates from queued to running to completed.

## Important refinement

I would not describe this as:

- backend calls the service
- which enqueues the job
- which then calls the API

because in the current project, the worker executes the render directly. The API and worker are parallel service entry points, not a worker-calls-API chain.

For the frontend and `dog`, the cleaner mental model is:

- synchronous render path for very small/direct cases
- asynchronous job path for the real interface flow

For this milestone, I would use the asynchronous job path as the default mental model even for SVG.

## Suggested Interface Shapes For The Assessed Subset

### 1. `design_patterns_gallery`

Expose as:

- State Chart
- Timeline
- Network Diagnostics

Starter controls:

- preset
- width
- height
- seed

Advanced controls:

- recipe-specific overrides

Reason:

- users should choose a concrete visual pattern, not a batch script

### 2. `static_data_lineage_map`

Expose as:

- Data Lineage Map

Starter controls:

- scenario
- policy
- seed

Advanced controls:

- corruption
- freshness decay
- schema drift
- layout iterations
- canvas size

Reason:

- strong, explainable, domain-shaped SVG use case

### 3. `tufte_small_multiples`

Expose as:

- Tufte Small Multiples

Starter controls:

- panels
- columns
- series
- seed

Advanced controls:

- points
- events
- duration
- fps

Expert note:

- later this same interface can grow from SVG-only into animated output without changing its conceptual identity

### 4. `tufte_small_multiples_extended`

Expose as:

- Tufte Small Multiples Advanced

Starter controls:

- data source
- panels
- cohorts
- columns

Advanced controls:

- highlight cohort
- width
- height
- external data path or uploaded dataset mapping once that contract exists

Reason:

- a stronger analytical tool, but less universal than the simpler Tufte path

### 5. `animation_sugiyama_story_workflow`

Expose as:

- Sugiyama Story Workflow

Starter controls:

- scenario
- policy
- camera mode

Advanced controls:

- event timing
- stress intensity
- replay factor
- packet rate

Recommended UI treatment:

- include in the catalog if you want to signal direction
- but badge it clearly as animation-oriented, not part of the immediate SVG steel thread

### 6. `graph_routing_showcase`

Expose as:

- Graph Routing Showcase

Starter controls:

- scenario
- policy
- mode
- topology

Advanced controls:

- packet rate
- packet speed
- curvature
- bundling and turn controls
- camera mode

Reason:

- high-value technical interface, but probably an advanced option

### 7. `animation_supply_chain_resilience`

Expose as:

- Supply Chain Resilience

Starter controls:

- scenario
- policy

Advanced controls:

- demand and supply tuning
- shock timing
- shock severity
- route capacity scale
- packet controls
- camera controls

Reason:

- extremely broad control surface, but much more domain-specific

## Recommendation For The Steel Thread

If the goal is to prove one golden path cleanly, I would not try to make all of these first-class at once.

I would recommend this progression:

1. `design_patterns_gallery` as recipe-mapped SVG interfaces
2. `static_data_lineage_map` as a domain-shaped SVG interface
3. `tufte_small_multiples` as the bridge interface between SVG now and animation later

Then keep:

- `tufte_small_multiples_extended`
- `animation_sugiyama_story_workflow`
- `graph_routing_showcase`
- `animation_supply_chain_resilience`

as the next assessed wave rather than the first delivered wave

## Final Answer

Yes, the frontend shape you described is broadly the right one.

The main refinements I would make are:

1. expose curated interfaces, not raw scripts
2. use progressive elaboration from starter to advanced to expert payload view
3. let `dog` backend own translation from UI state to `tesser` request
4. use the queued job path as the normal contract
5. keep Sugiyama in scope conceptually, but not force it into the SVG steel thread if the code does not support that today

The best single bridge interface for your current milestone is probably:

- `tufte_small_multiples`

because it can participate in the SVG MVP now while preserving continuity into later animation work

The best broad static interface for cross-domain visual diversity is:

- `design_patterns_gallery`

and the best domain-shaped SVG interface is:

- `static_data_lineage_map`
