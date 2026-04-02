# Backend-Kennel Interface Reconciliation

This note documents how `dog/backend` and `dog/kennel` can reconcile their current interfaces for ephemeral environments without removing existing capabilities from either side.

## Scope

The objective is to preserve both of these capacities:

1. Backend can define and override environments explicitly.
2. Kennel can define additional `runtime_preset` values locally and apply them as defaults.

This is an interface-ordering problem, not a requirement to collapse both systems into one ownership model.

## Current Interface Layers

### Backend layer

Backend currently contributes:

- workspace creation API contract,
- bootstrap intent normalization,
- repo materialization rules,
- bootstrap plan generation,
- platform-service access projection,
- workspace status projection from kennel responses.

References:

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L90)
- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py#L204)
- [backend/app/services/workspace_platform_service_access.py](/home/josep/dog/backend/app/services/workspace_platform_service_access.py#L170)

### Kennel layer

Kennel currently contributes:

- flavour rebuild and base-container selection,
- env creation and start,
- runtime preset defaulting,
- bootstrap profile expansion,
- bootstrap plan execution,
- runtime file writes,
- service manifest generation and readiness probing.

References:

- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L907)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L916)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L1226)

## Current Disconnects To Reconcile

### 1. Backend only partially surfaces kennel `runtime_preset`

Kennel supports `runtime_preset` on both create and inject. Backend now uses it for the default Codex agent-runtime handoff, while many other flows still send:

- explicit `flavour` on create,
- explicit `bootstrap_plan` on inject.

References:

- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py#L21)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L183)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L281)

### 2. Backend and kennel each have runtime-oriented startup logic

Backend defines agent-service startup commands.
Kennel defines bootstrap-profile startup commands.

Those capabilities can coexist, but the current interface does not clearly express when one is intended to supply defaults for the other versus when one is intended to override the other.

References:

- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py#L127)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L438)

### 3. Backend computes runtime files conceptually but does not currently pass them through

Backend’s platform-service projection returns both env vars and runtime files.
Current inject usage forwards env vars but not `runtime_files`.

References:

- [backend/app/services/workspace_platform_service_access.py](/home/josep/dog/backend/app/services/workspace_platform_service_access.py#L182)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py#L281)

### 4. Service-name alignment is implicit

Backend chooses `service_name` in bootstrap steps.
Kennel uses `service_name` to attach service metadata and readiness expectations.

That interface exists already, but it is partly conventional rather than explicitly documented.

References:

- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py#L301)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py#L557)

## Non-Breaking Reconciliation Model

The existing combined interface can be described in three layers:

### 1. Backend explicit layer

These fields are caller-directed and should remain authoritative when present:

- create: `base_container`, `base_snapshot`, explicit non-default `flavour`
- inject: `bootstrap_plan`, explicit `runtime_files`, explicit `env_vars`, explicit `repo_url`

### 2. Kennel preset/profile default layer

These fields supply defaults when explicit fields are absent:

- create: `runtime_preset` may supply a default `flavour`
- inject: `runtime_preset` may supply a default `bootstrap_profile`
- inject: `bootstrap_profile` may supply default runtime files and a default execution plan

### 3. Kennel legacy compatibility layer

If no explicit plan and no profile-derived plan are present, kennel can still derive a minimal legacy plan from:

- `ssh_pubkey`
- `env_vars`
- `repo_url`

## Proposed Ordering Contract

This is the reconciliation contract that preserves both sides’ functionality.

### Create precedence

1. `base_container` / `base_snapshot`
2. explicit non-default `flavour`
3. kennel `runtime_preset` default flavour
4. kennel default `dev`

### Inject precedence

1. explicit `bootstrap_plan`
2. explicit `bootstrap_profile`
3. kennel `runtime_preset` default bootstrap profile
4. legacy bootstrap derivation

### Runtime file merge

1. profile-owned runtime files
2. caller-supplied `runtime_files` override or extend them

### Env var merge

1. preset/profile defaults if any
2. backend-projected platform-service env vars
3. caller-supplied env vars for final override where allowed by the integrating layer

The exact env-var merge policy should be documented at the integration point that assembles the final inject payload.

## Integration Cases

### Case A: Backend-defined generic env

Use when backend wants full control over flavour and bootstrap execution.

Expected shape:

- create with explicit `flavour`
- inject with explicit `bootstrap_plan`
- no `runtime_preset` required

### Case B: Kennel preset-driven runtime env

Use when the caller wants kennel to select the runtime flavour/profile pair.

Expected shape:

- create with `runtime_preset`
- inject with the same `runtime_preset`
- omit explicit `bootstrap_plan`

This is now the default backend path for Codex agent-runtime workspaces.

### Case C: Kennel preset with backend override

Use when kennel should provide runtime defaults, but backend still needs targeted overrides.

Expected shape:

- create with `runtime_preset` and optionally explicit `flavour`
- inject with `runtime_preset`
- optionally explicit `bootstrap_profile`
- optionally extra `runtime_files` and `env_vars`
- omit `bootstrap_plan` if kennel profile execution should remain active

### Case D: Backend plan with kennel runtime assets

Use when backend wants to drive execution explicitly but still rely on kennel-owned runtime assets or preset naming.

This case requires the interface to expose both:

- a way to request preset/profile-derived files or metadata,
- and a way to supply the final explicit `bootstrap_plan`.

That combined shape is not fully surfaced through backend today.

## Practical Follow-Through

The reconciliation work is therefore documentation and interface-shape work:

- document create and inject precedence clearly,
- surface kennel `runtime_preset` through backend where useful,
- preserve backend’s explicit plan path,
- pass through `runtime_files` where backend already computes them,
- document service-name expectations where backend and kennel meet.

## Working Summary

Backend and kennel can both continue to contain preset/profile logic.

The current concrete ownership split is:

- Codex agent-runtime default startup: kennel-owned via `runtime_preset`
- generic/startup-profile/backend-custom runtime startup: backend-owned via explicit `bootstrap_plan`

What needs to be reconciled is:

- which fields are defaults,
- which fields are explicit overrides,
- what order they apply in,
- and which values must be shared across the interface so that service startup, runtime files, and readiness metadata remain aligned.
