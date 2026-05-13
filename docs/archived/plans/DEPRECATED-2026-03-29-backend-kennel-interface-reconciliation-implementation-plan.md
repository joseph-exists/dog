# Backend-Kennel Interface Reconciliation Implementation Plan

**Date:** 2026-03-29
**Status:** Draft
**Driver:** Reconcile backend and kennel workspace interfaces without removing either explicit backend control or kennel-local preset extensibility

## Context

The current backend and kennel integration already supports two useful modes:

- backend-defined environments driven by explicit `flavour` and explicit `bootstrap_plan`
- kennel-defined runtime defaults driven by `runtime_preset` and `bootstrap_profile`

The main issue is not that both layers contain preset/profile logic. The issue is that the combined interface is not surfaced or documented consistently enough for callers to know:

- which fields act as defaults,
- which fields act as explicit overrides,
- what order they apply in,
- and which values must stay aligned across both services.

This plan turns the reconciliation note in [backend-kennel-interface-reconciliation.md](/home/josep/dog/kennel/docs/backend-kennel-interface-reconciliation.md) into a concrete implementation sequence.

## Goals

1. Preserve backend’s ability to define and override environments explicitly.
2. Preserve kennel’s ability to add new `runtime_preset` values locally.
3. Make create and inject precedence explicit in the backend API contract and kennel integration layer.
4. Pass runtime assets and metadata through the interface in a way that keeps runtime startup, files, and service discovery aligned.
5. Support multiple integration cases without forcing all callers into one runtime ownership model.

## Non-Goals

- Removing kennel `runtime_preset`
- Removing backend-generated bootstrap plans
- Forcing all runtimes to use one startup path
- Refactoring kennel service discovery beyond what is needed for interface alignment

## Working Model

The reconciled system should expose three interface layers.

### 1. Explicit caller/backend layer

These remain authoritative when present.

- create: `base_container`, `base_snapshot`, explicit non-default `flavour`
- inject: `bootstrap_plan`, explicit `bootstrap_profile`, explicit `runtime_files`, explicit `env_vars`, explicit `repo_url`

### 2. Kennel defaulting layer

These apply only when more explicit fields are absent.

- create: `runtime_preset` may provide default `flavour`
- inject: `runtime_preset` may provide default `bootstrap_profile`
- inject: `bootstrap_profile` may provide default runtime files and a default execution plan

### 3. Legacy compatibility layer

This remains as the final fallback.

- inject: derive minimal plan from `ssh_pubkey`, `env_vars`, and `repo_url` if no explicit or profile-derived plan is present

## Contract Decisions

These decisions should be documented first and then enforced in code.

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
2. caller/backend `runtime_files` override or extend them

### Env var merge

1. baseline runtime defaults, if any
2. backend-projected platform-service env vars
3. caller/backend explicit env vars

The exact env-var merge rule should be implemented at the backend integration seam so the final inject payload is deterministic before it reaches kennel.

## API Design

### Backend create contract

Extend the backend workspace create surface so it can express:

- optional `runtime_preset`
- optional explicit `flavour`
- existing explicit bootstrap intent

Backend should not be forced to choose between `runtime_preset` and explicit `flavour`. Instead, backend should pass both when the caller intends “preset plus override,” and rely on kennel’s documented ordering.

### Backend inject contract

Extend backend’s kennel inject payload assembly so it can express:

- optional `runtime_preset`
- optional explicit `bootstrap_profile`
- optional explicit `runtime_files`
- optional explicit `bootstrap_plan`
- merged env vars

This creates a full interface that can represent all four integration cases:

1. backend-defined generic env
2. kennel preset-driven env
3. kennel preset with backend override
4. backend plan with kennel runtime assets

### Backend internal representation

Introduce a normalized backend-side integration model for kennel provisioning, separate from the user-facing bootstrap intent.

Suggested shape:

```python
@dataclass(frozen=True)
class WorkspaceKennelProvisioningRequest:
    create_flavour: str | None
    create_runtime_preset: str | None
    create_base_container: str | None
    inject_runtime_preset: str | None
    inject_bootstrap_profile: str | None
    inject_runtime_files: dict[str, str]
    inject_env_vars: dict[str, str]
    inject_bootstrap_plan: WorkspaceBootstrapPlan | None
    repo_url: str | None
```

This becomes the single backend assembly point for precedence and merging.

## Implementation Plan

### Phase 1: Document and encode the precedence contract

**Objective:** Make ordering explicit before broadening the interface.

Changes:

- update backend workspace docs to mirror the create/inject precedence contract
- add inline service comments around the integration seam in backend and kennel
- codify the precedence matrix in tests first

Files:

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- [kennel/docs/runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)

Tests:

- kennel tests for create precedence
- kennel tests for inject precedence
- backend tests for final inject payload assembly

### Phase 2: Surface `runtime_preset` through backend create/inject flows

**Objective:** Allow backend callers to opt into kennel presets without losing explicit backend control.

Changes:

- add optional `runtime_preset` to backend workspace request models
- thread `runtime_preset` through normalization and provisioning
- update kennel client create and inject methods to accept optional `runtime_preset`
- ensure backend can pass the same preset to both create and inject when desired

Files:

- [backend/app/models.py](/home/josep/dog/backend/app/models.py)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- backend workspace route handlers and tests

Acceptance criteria:

- backend can create a workspace with `runtime_preset` and no explicit plan
- backend can still create a workspace with explicit `flavour` and no preset
- backend can pass preset plus explicit `flavour` without silent backend-side rewriting

### Phase 3: Introduce backend-side kennel payload normalization

**Objective:** Centralize precedence and merge behavior in one backend assembly path.

Changes:

- add `WorkspaceKennelProvisioningRequest` or equivalent normalized structure
- extract final create payload assembly from `_provision_workspace()`
- extract final inject payload assembly from `_provision_workspace()`
- make payload assembly pure and unit-testable

Files:

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py)

Acceptance criteria:

- one backend function determines create payload precedence
- one backend function determines inject payload precedence and merges
- provisioning code becomes orchestration, not implicit business logic

### Phase 4: Pass runtime files through the backend integration seam

**Objective:** Ensure backend-computed runtime files become real container state.

Changes:

- merge platform-service `runtime_files` into the final inject payload
- support additional backend-generated runtime files for runtime adapters or runtime-specific config
- document the merge rule between kennel profile files and backend files

Files:

- [backend/app/services/workspace_platform_service_access.py](/home/josep/dog/backend/app/services/workspace_platform_service_access.py)
- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)

Acceptance criteria:

- `/home/dev/.dog/platform-services/*.json` files are actually written when backend projects them
- backend runtime file overlays can override kennel profile-provided files intentionally

### Phase 5: Reconcile runtime startup metadata with service discovery

**Objective:** Keep backend startup intent and kennel service metadata aligned.

Changes:

- define a documented runtime/service registry contract for shared identifiers such as `codex`, `claude_code`, and `hermes`
- decide which metadata belongs in backend plan generation versus kennel profile metadata
- ensure `service_name`, expected protocol, expected port, and readiness behavior remain coherent across the interface

Files:

- [backend/app/services/workspace_bootstrap_service.py](/home/josep/dog/backend/app/services/workspace_bootstrap_service.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- new shared documentation artifact if needed

Acceptance criteria:

- every backend-emitted runtime `service_name` maps to clear kennel discovery semantics
- service descriptors no longer rely on unstated conventions

### Phase 6: Support backend plan plus kennel runtime assets

**Objective:** Enable the mixed mode where backend drives execution explicitly while kennel still contributes preset/profile-owned assets.

Changes:

- add a backend-side way to request profile-derived runtime files without requiring kennel to own the final execution plan
- or add kennel support for profile materialization plus explicit plan execution in one inject request
- document which mixed-mode combinations are valid and which are intentionally unsupported

Files:

- [backend/app/services/workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [kennel/src/server.py](/home/josep/dog/kennel/src/server.py)
- [kennel/docs/runtime-preset-api-reference.md](/home/josep/dog/kennel/docs/runtime-preset-api-reference.md)

Acceptance criteria:

- mixed mode can be expressed without relying on undocumented side effects
- preset/profile-derived assets and explicit plans do not silently fight each other

### Phase 7: Rollout and compatibility hardening

**Objective:** Land the reconciliation without breaking current consumers.

Changes:

- keep existing backend explicit-plan path working throughout rollout
- keep kennel legacy derivation path intact
- gate new backend request fields behind additive schema changes only
- add migration notes for current workspace consumers

Acceptance criteria:

- existing explicit backend-driven workspaces still provision successfully
- kennel-only preset workflows remain valid
- new preset-aware backend workflows work without regressing existing tests

## Test Plan

### Backend unit tests

- create payload precedence with `runtime_preset`, explicit `flavour`, and explicit `base_container`
- inject payload precedence with `runtime_preset`, explicit `bootstrap_profile`, and explicit `bootstrap_plan`
- env var merge ordering
- runtime file merge ordering
- platform-service runtime files included in inject payload

### Kennel unit tests

- `runtime_preset` only applies create defaults when `flavour` is still default `dev`
- `runtime_preset` only applies inject profile defaults when `bootstrap_profile` is absent
- explicit `bootstrap_plan` wins over profile-derived plan
- caller `runtime_files` override profile-generated runtime files

### Integration tests

- backend explicit-plan flow remains unchanged
- kennel preset-driven flow works end-to-end
- preset plus backend override works end-to-end
- runtime service discovery remains aligned with emitted `service_name`

## Open Questions

1. Should backend expose `bootstrap_profile` directly in its public workspace API, or keep it as an internal integration concern?
2. Should kennel provide a first-class “materialize profile assets only” mode for mixed backend-plan cases?
3. Where should the shared runtime/service registry live if we want machine-enforced alignment rather than parallel constants?
4. Do we want backend request validation to reject obviously conflicting combinations, or allow them and rely on precedence rules?

## Recommended Execution Order

1. Phase 1: precedence tests and contract documentation
2. Phase 2: surface `runtime_preset` through backend
3. Phase 3: centralize payload normalization
4. Phase 4: pass `runtime_files`
5. Phase 5: align runtime/service metadata
6. Phase 6: support mixed asset-plus-plan mode
7. Phase 7: compatibility hardening and rollout

This order reduces risk because it locks in the ordering contract before widening the API surface, then closes the most concrete current gap (`runtime_files`) before tackling deeper mixed-mode support.
