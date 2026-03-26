# Workspace Platform Service Access Decision

## Purpose

This note defines the implementation shape for workspace-to-platform service
access in the MVP closing sequence.

The direction is:

- canonical model: backend-issued runtime config
- convenience layer: environment projection

These two pieces work together as a single platform-service access model:

- the backend owns current access truth
- runtimes receive a small, scoped access payload
- workspace-side processes can also consume that access through a simple
  projected runtime environment

## Decision

Workspace-to-platform service access will be delivered through a hybrid model:

1. backend-issued runtime config is the canonical service-access surface
2. environment projection is the convenience layer for workspace-side processes

This keeps access explicit, refreshable, and operator-legible while also making
runtime consumption practical for the first MVP slice.

## Canonical Model

### Backend-Issued Runtime Config

The canonical workspace-to-platform access model is a narrow backend-issued
runtime config.

This runtime config should:

- be issued for a concrete workspace consumer
- carry current scoped grants for named platform services
- include issuance and expiry metadata
- expose transport, service identity, and capability metadata
- be refreshable without changing workspace lifecycle state

Near-term consumer kinds:

- `workspace_runtime`
- `agent_runtime`

Near-term shape:

```ts
interface WorkspaceRuntimePlatformConfig {
  workspace_id: string
  consumer_kind: "workspace_runtime" | "agent_runtime"
  issued_at: string
  expires_at: string | null
  services: Array<{
    grant_id: string
    service_id: string
    transport: string
    url: string
    auth_mode: string
    require_approval: string
    scopes: string[]
    tags: string[]
    scope: Record<string, string>
  }>
}
```

### Reasons For The Canonical Model

- It gives the backend a clear operational responsibility for current
  platform-service access.
- It gives runtimes a compact, typed contract that can be refreshed throughout
  the life of a workspace.
- It gives operators a consistent place to inspect issued grants, scope, and
  expiry.
- It gives the system one shared vocabulary for service identity, transport,
  approval, and capabilities.
- It gives room/workspace connectivity and workspace/platform access a coherent
  trust language across the milestone.
- It gives future runtime kinds a stable seam for growth without changing the
  core access contract.
- It gives platform services a clean integration point for policy, audit, and
  issuance metadata.

## Convenience Layer

### Environment Projection

The convenience layer is an environment projection derived from the canonical
runtime config.

This projection should:

- make approved platform services easy to consume from workspace-side processes
- expose a lightweight runtime-oriented view of issued service access
- support simple process startup and local operator inspection
- stay derived from the backend-issued config so the trust model remains unified

Near-term projection examples:

- `DOG_PLATFORM_SERVICES_JSON`
- `DOG_PLATFORM_SERVICE_AFFORDANCE_URL`
- `DOG_PLATFORM_SERVICE_STORY_URL`
- `DOG_PLATFORM_SERVICE_ACCESS_ISSUED_AT`
- `DOG_PLATFORM_SERVICE_ACCESS_EXPIRES_AT`

These may be projected through:

- environment variables
- a generated runtime file inside the workspace
- launcher-specific runtime wrappers where useful

### Reasons For The Convenience Layer

- It gives workspace-side runtimes an easy on-ramp for consuming approved
  platform services.
- It gives agent launch profiles a simple way to inherit platform connectivity
  without extra runtime-specific wiring in the first pass.
- It gives operators familiar inspection surfaces when debugging workspace-side
  service access.
- It gives launcher and bootstrap code a practical runtime-facing adapter that
  stays aligned with backend truth.
- It gives the system a fast path for enabling useful workspace-side
  integrations while keeping the backend access contract central.
- It gives future process types a straightforward adoption path with minimal
  local ceremony.

## Recommended Hybrid Implementation Sequence

### Step 1. Runtime Config Route

Add a narrow backend runtime-config route for workspace consumers.

Primary outcome:

- a workspace runtime or agent runtime can request a typed current-access config

Likely touchpoints:

- `/home/josep/dog/backend/app/api/routes/workspaces.py`
- `/home/josep/dog/backend/app/services/workspace_platform_service_access.py`
- `/home/josep/dog/backend/app/models.py`

Status:

- implemented
- backend now exposes a narrow runtime-config route for workspace consumers:
  - `POST /api/v1/workspaces/{workspace_id}/platform-runtime-config`

### Step 2. Runtime Config Consumer Helper

Add a backend helper that resolves the current platform-service config for a
workspace consumer.

Primary outcome:

- one internal service seam for policy checks, issuance, refresh, and future
  audit hooks

Likely touchpoints:

- `/home/josep/dog/backend/app/services/workspace_platform_service_access.py`
- runtime-facing backend services that need to shape workspace access state

Status:

- implemented for the first internal seam
- backend now resolves canonical runtime config through dedicated helper paths
  instead of only exposing grant issuance

### Step 3. Environment Projection Adapter

Project the canonical runtime config into a runtime-facing environment form.

Primary outcome:

- workspace-side processes can consume platform-service access with minimal
  setup

Likely touchpoints:

- `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`
- `/home/josep/dog/kennel/src/server.py`

Status:

- implemented for the first runtime-facing projection slice
- canonical runtime config is now projected into workspace env vars during
  provisioning
- workspace runtimes receive `DOG_PLATFORM_*` access variables
- agent runtimes receive `DOG_AGENT_PLATFORM_*` access variables when an
  `agent_service` startup profile is requested
- runtime projections now materialize stable platform-service files inside the
  workspace for refreshable consumption

### Step 4. Agent Runtime Profile Alignment

Wire the projection into the current agent runtime profiles so the first
workspace-hosted agents can consume platform services directly.

Primary outcome:

- `codex`, `claude_code`, and `hermes` profiles receive runtime-facing platform
  service access affordances

Likely touchpoints:

- `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- `/home/josep/dog/kennel/src/server.py`
- profile-specific launch wrappers or environment materialization points

Status:

- implemented for the first active-consumption slice
- current agent runtime profiles now consume projected platform-service access
  through stable runtime-facing aliases
- launchers now materialize a runtime-local JSON file for process consumption
  and operator inspection at:
  - `~/.dog/agent-runtime/platform-services.json`
- current agent launchers now prefer the stable projected platform-services path
  maintained by the backend refresh loop

### Step 5. Operator And UI Visibility

Surface the runtime config and projection summary in the workspace detail view.

Primary outcome:

- operators can inspect the canonical grant state and the runtime-facing access
  view from one place

Likely touchpoints:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`

Status:

- implemented for the first operator visibility slice
- workspace detail now exposes:
  - projected runtime access summaries from workspace metadata
  - on-demand inspection of the current canonical runtime config
  - the existing explicit grant issuance surface
- operators can now refresh runtime projections from the workspace detail page
- the detail surface now makes expired projections and no-longer-available
  workspaces visible in the runtime access workflow
- projection summaries now surface runtime file paths and inject notes so the
  runtime-facing materialization is directly inspectable during live operations

## Operator Affordances

This hybrid direction gives operators:

- a clear grant issuance surface
- visible consumer-specific access state
- a compact runtime config for backend and service inspection
- a practical runtime-facing projection for process-level debugging
- a clean mental model for refresh and expiry

## Operational Shape

This hybrid direction gives the platform:

- backend-owned current-access truth
- explicit issuance and expiry boundaries
- small runtime payloads
- practical runtime adoption for the first service-access slice
- a stable seam for future policy, audit, caching, and transport evolution

## Extensibility

This direction creates a strong path for:

- additional workspace-side consumer kinds
- richer service catalogs
- profile-specific runtime affordances
- future proxy-aware transport handling
- deeper audit and policy instrumentation
