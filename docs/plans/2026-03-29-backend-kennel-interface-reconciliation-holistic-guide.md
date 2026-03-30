# Backend-Kennel Interface Reconciliation Holistic Implementation Guide

**Date:** 2026-03-29
**Status:** Draft
**Driver:** Reconcile backend and kennel workspace interfaces with stable sequencing and minimal churn

## Purpose

This guide supersedes the sequencing in the earlier reconciliation implementation plan.

The target outcomes remain the same:

- backend can explicitly define and override environments,
- kennel can add and apply `runtime_preset` values locally,
- precedence and ordering are applied consistently,
- runtime files, startup semantics, and service discovery remain aligned,
- mixed-mode flows are supported deliberately rather than by accident.

What changes here is the execution order.

The earlier plan separated the work by topic, but that ordering expands backend surface area too early. That creates re-work because the backend request model, kennel client payloads, and mixed-mode semantics would all need to be reshaped once runtime/service alignment and asset materialization are resolved.

This guide sequences the work by dependency.

## Core Sequencing Principle

The shared seam has to stabilize before the public surface expands.

That means the work should proceed in this order:

1. Stabilize shared runtime/service semantics.
2. Centralize backend payload normalization.
3. Add mixed-mode asset/materialization support at the seam.
4. Pass runtime files and merged env vars through that seam.
5. Surface `runtime_preset` and related controls through backend.
6. Harden compatibility and rollout.

This avoids exposing a public backend contract that would need to be revised after the internal seam is corrected.

## Stable End-State

The reconciled system still ends with the same ordering rules.

### Create precedence

1. `base_container` / `base_snapshot`
2. explicit non-default `flavour`
3. `runtime_preset` default flavour
4. kennel default `dev`

### Inject precedence

1. explicit `bootstrap_plan`
2. explicit `bootstrap_profile`
3. `runtime_preset` default bootstrap profile
4. legacy inject derivation

### Runtime file merge

1. profile-owned runtime files
2. caller/backend `runtime_files`

### Env var merge

1. baseline runtime defaults, if any
2. backend-projected platform-service env vars
3. caller/backend explicit env vars

## Implementation Tracks

The work is best understood as three coupled tracks:

### Track A: Shared seam semantics

Define what a runtime identifier means across backend and kennel.

This includes:

- `service_name`
- expected protocol
- expected port
- profile-owned runtime files
- readiness expectations
- which parts are default metadata vs explicit override

### Track B: Backend integration normalization

Create one backend-owned structure that assembles the final kennel create and inject payloads deterministically.

This becomes the only place where precedence, merging, and mixed-mode behavior are resolved.

### Track C: Public API surfacing

Only after Tracks A and B are stable should the backend expose additional request fields such as `runtime_preset`, `bootstrap_profile`, or mixed-mode runtime controls.

## Recommended Execution Order

## Stage 1: Shared runtime and service alignment

**Why first:** Every later change depends on a stable understanding of what backend-emitted runtime identifiers mean to kennel. Without this, normalization logic and public request fields will be built on moving assumptions.

### Objective

Align backend startup intent with kennel service metadata and discovery semantics.

### Changes

- define a documented runtime/service registry contract for shared identifiers such as `codex`, `claude_code`, and `hermes`
- decide which runtime metadata is canonical in backend plan generation and which metadata is kennel-local default metadata
- define the shared meaning of:
  - `service_name`
  - expected protocol
  - expected port
  - readiness behavior
  - profile-owned runtime files
- document mixed-mode behavior
### Files

- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- runtime/service contract docs under `kennel/docs` or `docs/plans`

### Acceptance criteria

- every backend-emitted runtime `service_name` maps to clear kennel discovery semantics
- service descriptors no longer rely on unstated conventions
- profile-owned assets and startup metadata are explicitly documented per runtime
- Codex, Claude Code, and Hermes all have defined cross-service semantics

## Stage 2: Backend seam normalization

**Primary source work:** former Phase 3

**Why second:** Once runtime semantics are stable, backend can centralize payload assembly.

### Objective

Centralize create/inject precedence, merge behavior, and mixed-mode assembly in one backend integration path.

### Changes

- add `WorkspaceKennelProvisioningRequest` or equivalent normalized structure
- extract final create payload assembly from `_provision_workspace()`
- extract final inject payload assembly from `_provision_workspace()`
- make payload assembly pure and unit-testable
- keep orchestration and state transitions separate from payload construction

### Files

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)

### Acceptance criteria

- one backend function determines create payload precedence
- one backend function determines inject payload precedence and merges
- provisioning code becomes orchestration, not implicit business logic
- the normalized backend seam can represent:
  - explicit backend plan flow
  - preset-driven flow
  - preset-plus-override flow
  - mixed asset-plus-plan flow

## Stage 3: Mixed-mode capability at the seam

**Primary source work:** former Phase 6

**Why third:** Mixed mode is the hardest seam behavior. If it is added after public API surfacing, request models and payloads will churn. It has to be supported before the backend exposes the final shape externally.

### Objective

Support the case where backend drives execution explicitly while kennel still contributes preset/profile-owned assets or metadata.

### Changes

- add a backend-side way to request profile-derived runtime files and metadata without requiring kennel to own the final execution plan
- or add kennel support for profile materialization plus explicit plan execution in one inject request
- define whether mixed mode is expressed by:
  - `runtime_preset + bootstrap_plan`
  - `bootstrap_profile + bootstrap_plan`
  - explicit profile asset materialization fields
- document which mixed-mode combinations are valid and which are intentionally unsupported

### Files

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- [kennel/docs/runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)

### Acceptance criteria

- mixed mode can be expressed without relying on undocumented side effects
- preset/profile-derived assets and explicit plans do not silently fight each other
- the seam can request runtime assets independently from final execution ownership

## Stage 4: Runtime file and env-var materialization

**Primary source work:** former Phase 4

**Why fourth:** Runtime file pass-through should land after mixed-mode semantics exist, otherwise the first pass will likely be too narrow and need immediate revision.

### Objective

Ensure backend-computed runtime files and merged env vars become real container state through the stabilized seam.

### Changes

- merge platform-service `runtime_files` into the final inject payload
- support additional backend-generated runtime files for runtime adapters or runtime-specific config
- implement the agreed runtime file merge order
- implement the agreed env-var merge order
- ensure kennel applies profile-owned files first, then caller/backend overrides
- assume the stabilized kennel client create/inject method signatures are already
  available at this stage so materialization work lands on the explicit seam API,
  not on a temporary dict-shaped client path

Addition: - update kennel client create and inject methods to accept the stabilized optional fields that will be created in Stage 5.

### Files

- [backend/app/services/workspace_platform_service_access.py](/home/josep/dog/backend/app/services/workspace_platform_service_access.py)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)

### Acceptance criteria

- `/home/dev/.dog/platform-services/*.json` files are actually written when backend projects them
- backend runtime file overlays can override kennel profile-provided files intentionally
- env-var merge ordering is deterministic and tested

## Stage 5: Surface `runtime_preset` and explicit override controls through backend

**Primary source work:** former Phase 2

**Why fifth:** At this point the seam is stable, mixed mode is defined, and asset/materialization behavior is real. Public backend request shape can now reflect the real integration model instead of anticipating it.

### Objective

Allow backend callers to opt into kennel presets and explicit overrides without later request-shape churn.

### Changes

- add optional `runtime_preset` to backend workspace request models
- add optional explicit override fields that match the stabilized seam
- thread `runtime_preset` through normalization and provisioning

- ensure backend can pass the same preset to both create and inject when desired

### Files

- [backend/app/models.py](/home/josep/dog/backend/app/models.py)
- [backend/app/api/routes/workspaces.py](/home/josep/dog/backend/app/api/routes/workspaces.py)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- frontend workspace contract/docs if needed

### Acceptance criteria

- backend can create a workspace with `runtime_preset` and no explicit plan
- backend can still create a workspace with explicit `flavour` and no preset
- backend can pass preset plus explicit `flavour` without silent backend-side rewriting
- backend can express whichever explicit inject override fields are adopted in Stages 2 and 3 without additional payload refactors

## Stage 6: Compatibility hardening and rollout

**Primary source work:** former Phase 7

**Why last:** This stage hardens the now-stable seam and public surface rather than trying to protect an interface still in flux.

### Objective

Land the reconciliation without regressing current flows.

### Changes

- keep existing backend explicit-plan path working throughout rollout
- keep kennel legacy derivation path intact
- gate new backend request fields behind additive schema changes only
- add migration notes for current workspace consumers
- add tracing or structured logging around normalized create and inject payload selection

### Acceptance criteria

- existing explicit backend-driven workspaces still provision successfully
- kennel-only preset workflows remain valid
- new preset-aware backend workflows work without regressing existing tests
- rollout diagnostics make precedence and override selection observable

## What Moves Earlier Than Before

Compared with the prior plan, these work items move earlier:

- runtime/service registry alignment
- backend payload normalization
- mixed-mode definition

These must come before backend API expansion because they define the real seam contract.

## What Moves Later Than Before

Compared with the prior plan, these work items move later:

- surfacing `runtime_preset` through backend public models
- expanding backend request options

Those should reflect the stabilized seam rather than driving it.

## Test Strategy

### Stage 1 and 2 tests

- runtime/service mapping tests for each shared runtime identifier
- backend create payload precedence tests
- backend inject payload precedence tests
- normalization tests for explicit flow, preset flow, override flow, and mixed flow

### Stage 3 and 4 tests

- mixed-mode seam tests
- profile-derived asset materialization tests
- runtime file merge ordering tests
- env-var merge ordering tests
- platform-service runtime files included in inject payload

### Stage 5 and 6 tests

- backend API request model tests for new optional fields
- backend explicit-plan flow remains unchanged
- kennel preset-driven flow works end-to-end
- preset plus backend override works end-to-end
- runtime service discovery remains aligned with emitted `service_name`

## Consolidated Outcomes

This sequencing still delivers the same substantive outcomes as the previous plan:

- backend explicit env definition remains intact
- kennel-local preset creation remains intact
- `runtime_preset` becomes available through backend without forcing callers into it
- backend-generated runtime files are actually materialized
- service discovery semantics align with runtime startup semantics
- mixed-mode execution is supported deliberately

## Implementation Summary

The least wasteful path is:

1. align what shared runtime identifiers mean
2. build one backend seam that encodes precedence and merging
3. make mixed-mode behavior explicit at that seam
4. pass real runtime assets through it
5. then expose the stabilized controls publicly

That sequence produces the same end-state as the original reconciliation plan, but avoids the churn of widening backend inputs before the backend-to-kennel seam is actually stable.
