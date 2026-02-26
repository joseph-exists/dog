# Physics Event Hooks RFC (Next Sprint Scope)

Last updated: February 17, 2026
Contract version: `1.0.0`

## Approval Status

- Status: Approved for implementation in this repository
- Approved date: February 17, 2026
- Scope lock:
  - Event families in this RFC are the `1.0.0` baseline contract.
  - New event types may be added in minor versions.
  - Existing required fields may not be removed or renamed outside a major version.

## Goal

Define a minimal, deterministic event model for physics-aware visualizations without coupling event semantics to individual example scripts.

## Minimal Event Model

Core principle: event emission happens at stable lifecycle boundaries of simulation and render, with typed payloads and deterministic ordering.

Event families:

- `world.before_step`
- `world.after_step`
- `world.collision_start`
- `world.collision_persist`
- `world.collision_end`
- `constraint.applied`
- `joint.limit_hit`

## First-Class Constraints/Joints (Initial Set)

Constraints:

- Distance constraint
- Spring constraint
- Pin/anchor constraint

Joints:

- Revolute joint (hinge)
- Prismatic joint (slider)

Rationale:

- These cover most educational and operational overlay examples without overextending API surface.

## API Touchpoints (Current + Next)

- Physics world update loop:
  - emits `world.before_step` and `world.after_step` in `src/tesserax/physics/world.py`
- Collision resolver:
  - emits `world.collision_start` / `world.collision_persist` / `world.collision_end` keyed by canonical body-pair IDs
- Constraint/joint solvers:
  - emits `constraint.applied` for current constraint solve loop
  - emits `joint.limit_hit` with `joint_id`, `error`, `impulse`, `active_limits` when joint limits activate
- Render layer integration:
  - event stream is consumed by `examples-other/animation/physics/animation_physics_overlay.py` for collision diagnostics overlays

## Event Payload Schema

Required fields:

- `schema_version`: semantic version string for payload contract (default for this RFC: `1.0.0`)
- `type`: string event type
- `timestamp`: float simulation time (seconds)
- `step_index`: integer simulation step index
- `entities`: list of stable entity identifiers
- `metadata`: object, type-specific fields

Collision metadata baseline:

- `normal`: `{x, y}`
- `penetration`
- `relative_speed`
- `contact_points`: list of `{x, y}`

Constraint/joint metadata baseline:

- `constraint_id` or `joint_id`
- `error`
- `impulse`
- `active_limits` (optional list)

## Versioning + Compatibility Policy

Versioning rules:

- Semantic versioning applies to the event payload contract (`schema_version`).
- Patch (`1.0.x`):
  - Clarifications, stricter docs, non-behavioral fixes.
  - No payload shape changes.
- Minor (`1.x.0`):
  - Additive changes only (new event types, new optional metadata keys).
  - Existing consumers must continue to parse old required fields unchanged.
- Major (`x.0.0`):
  - Breaking payload changes allowed (remove/rename required fields, semantic redefinition).

Producer guarantees:

- Producers must emit all required fields for the active major version.
- Producers may add optional metadata keys at any time within the same major version.
- Event ordering guarantee remains stable: `(step_index, emission_order)`.

Consumer guidance:

- Consumers must ignore unknown metadata keys.
- Consumers should branch behavior by `schema_version` major version if needed.
- Consumers should treat unknown event `type` values as non-fatal and skip by default.

Deprecation policy:

- Any planned breaking change requires a deprecation notice in RFC + docs before major bump.
- Minimum deprecation window for renamed/removed semantics: one minor release cycle.

## Dispatch Lifecycle

Within each physics step:

1. `world.before_step`
2. force accumulation
3. integration
4. broadphase/narrowphase
5. collision events (`start`/`persist`/`end`)
6. constraint/joint solve + related events
7. `world.after_step`

Dispatch requirements:

- Stable order by `(step_index, emission_order)`
- No mutation of emitted payload after dispatch
- Hook exceptions isolated and surfaced as non-fatal diagnostics by default

## Deterministic Replay Expectations

Determinism contract:

- Same initial conditions + seed + dt + solver settings => byte-stable event sequence
- Event IDs stable across reruns
- Collision pair ordering canonicalized (sorted by stable body IDs)

Replay artifacts:

- Optional newline-delimited JSON event log
- Header includes simulation config fingerprint and seed
- Validation utility compares replay logs for drift

## Acceptance Criteria for Sprint Start

- Event model approved
- Initial constraints/joints approved
- Payload schema approved
- Dispatch order approved
- Replay determinism criteria approved
- Versioning and compatibility policy approved

## Current Implementation References

- Event types and dispatcher:
  - `src/tesserax/physics/events.py`
  - Includes `schema_version` field on `PhysicsEvent` (default `1.0.0`)
- World emission wiring:
  - `src/tesserax/physics/world.py`
  - `constraint.applied` includes `constraint_id`, `error`, `impulse`, and canonical `body:*` entities
  - `joint.limit_hit` includes `joint_id`, `error`, `impulse`, `active_limits`, and canonical `body:*` entities
- Example consumer:
  - `examples-other/animation/physics/animation_physics_overlay.py`
- Deterministic event behavior tests:
  - `tests/test_physics_events.py`
  - `tests/test_animation_physics_overlay_events.py`
- Initial constraints implementation:
  - `src/tesserax/physics/constraints.py` (`Spring`, `Distance`/`Rod`, `Pin`)
- Initial joints implementation:
  - `src/tesserax/physics/joints.py` (`RevoluteJoint`, `PrismaticJoint`)
- Render lifecycle hook contract used by integrations:
  - `src/tesserax/render.py`
  - `tests/test_render.py`
