# Workspace Domain Contract Draft

## Purpose

This artifact defines the first concrete domain-contract proposal for `Workspaces`.

This draft is based on the current implementation in:

- [models.py](/home/josep/dog/backend/app/models.py#L7264)
- [workspaces.py](/home/josep/dog/backend/app/api/routes/workspaces.py)
- [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)

## Current Contract Summary

Current strengths:

- real workspace object exists in backend persistence
- create, list, detail, terminal, stop, and destroy routes exist
- kennel-backed provisioning is real
- frontend already consumes a stable vertical slice

Current weaknesses:

- lifecycle is too small for the next milestone
- failure is currently collapsed into `destroyed`
- project association, repo identity, access semantics, and service discovery are not first-class
- important operational intent is stored only in `meta`
- terminal access exists, but broader connectivity is not yet modeled

## Current Implementation Snapshot

After the first implementation pass on backend models and service logic, the following parts of this draft are now partially real:

- expanded lifecycle states exist in the backend model:
  - `requested`
  - `provisioning`
  - `starting`
  - `ready`
  - `stopping`
  - `stopped`
  - `failed`
  - `destroying`
  - `destroyed`
- persisted lifecycle fields now exist for:
  - `failure_message`
  - `last_transition_at`
  - `requested_at`
  - `started_at`
  - `ready_at`
  - `stopped_at`
  - `destroyed_at`
- backend service transitions in `workspace_service.py` now use the expanded lifecycle and no longer collapse provisioning failure into `destroyed`
- backend service helpers now define:
  - `get_allowed_actions(workspace)`
  - `get_terminal_status(workspace)`
- backend route responses now project:
  - `allowed_actions`
  - `visibility`
  - `project_id`
  - `project_summary`
  - `terminal_status`
- `POST /api/v1/workspaces/{workspace_id}/start` is now exposed
- frontend service and main detail/list surfaces now consume the richer contract and render the new lifecycle and projection fields

Still pending:

- project projection currently assumes a near-term zero-or-one attachment model and will need a deliberate follow-up if that rule changes
- runtime verification in the app is still needed before this first pass should be considered fully closed

## Design Goals

The next workspace contract should make these things explicit:

- what the workspace is
- what state it is in
- what actions are currently allowed
- what repo/bootstrap intent it was created with
- what project or access context it belongs to
- what endpoints or capabilities it can expose

The contract should remain narrow enough that we can implement it in phases.

## Proposed Lifecycle Model

### Canonical Status Enum

Replace the current enum:

- `provisioning`
- `ready`
- `stopping`
- `stopped`
- `destroyed`

With:

- `requested`
- `provisioning`
- `starting`
- `ready`
- `stopping`
- `stopped`
- `failed`
- `destroying`
- `destroyed`

### Why These States

- `requested` separates API acceptance from actual provisioner progress.
- `starting` separates infrastructure readiness from runtime/bootstrap readiness.
- `failed` prevents destructive state from masquerading as error state.
- `destroying` makes destructive transitions visible and pollable.

### Allowed Actions By State

Recommended first-pass action matrix:

- `requested`
  - allowed: `destroy`

- `provisioning`
  - allowed: `destroy`

- `starting`
  - allowed: `destroy`

- `ready`
  - allowed: `stop`, `destroy`, `request_terminal`, `discover_services`

- `stopping`
  - allowed: none

- `stopped`
  - allowed: `start`, `destroy`

- `failed`
  - allowed: `destroy`, optional `retry_start` later

- `destroying`
  - allowed: none

- `destroyed`
  - allowed: none

The backend should be the authoritative source of these action permissions. The frontend may still derive convenience flags, but it should not invent lifecycle semantics.

## Proposed Domain Shape

### Workspace Identity

Keep:

- `id`
- `name`
- `owner_id`
- `created_at`
- `updated_at`
- `flavour`
- `kind`

Add:

- `display_name`
  Optional if we want `name` to remain slug-like later. If not needed, defer.

- `visibility`
  Enum, near-term values:
  - `private`
  - `project`
  - `shared`

- `project_id`
  Nullable in near term. Zero-or-one project is sufficient initially.

### Runtime State

Keep:

- `status`
- `kennel_name`
- `kennel_job`

Add:

- `last_transition_at`
- `failure_code`
- `failure_message`
- `stop_reason`
- `requested_at`
- `started_at`
- `ready_at`
- `stopped_at`
- `destroyed_at`

These should not all be required in the first migration, but `last_transition_at` and a failure summary should become first-class quickly.

### Bootstrap Intent

Current create fields:

- `repo_url`
- `ssh_pubkey`
- `env_vars`

These are useful, but they are too raw to support repo integration cleanly.

Recommended shape:

- `repo_source_type`
  Enum:
  - `external_url`
  - `user_repo`
  - `shadow_repo`

- `repo_source_id`
  Nullable resource id for platform-managed repos

- `repo_url`
  Still allowed for `external_url`

- `bootstrap_profile`
  Examples:
  - `dev`
  - `python`
  - `node`
  - `agent-runtime`

- `startup_profile`
  Examples:
  - `terminal_only`
  - `agent_service`
  - `custom_service_stack`

- `install_command`
  Optional, probably backend-validated if enabled

- `startup_command`
  Optional, probably backend-validated if enabled

- `requested_agent_profile`
  Optional freeform or enum-backed identifier for early agent-launch intent

This gives the system a way to express more than raw kennel injection details.

### Access And Classification

Add:

- `tags`
  List of strings for near-term grouping/filtering

- `capabilities`
  List of markers such as `gpu`, `cuda`, `python`, `node`

- `access_summary`
  Lightweight projection rather than full ACL expansion

Recommended near-term `access_summary` shape:

```ts
{
  owner_id: string
  visibility: "private" | "project" | "shared"
  project_id: string | null
  can_manage: boolean
  can_use: boolean
}
```

### Connectivity

Keep terminal issuance as a separate endpoint for now.

Add to the workspace detail shape:

- `terminal_status`
  Enum:
  - `unavailable`
  - `available`
  - `expired`

- `service_count`
  cheap summary for list/detail UI

- `connectivity_summary`
  Lightweight status for:
  - room connectivity
  - service discovery readiness
  - direct access eligibility

Do not place all endpoint descriptors directly on `WorkspacePublic` yet. That will likely grow too quickly. Use dedicated endpoints for richer discovery.

## Proposed API Model Deltas

### Backend Models

Current backend models are:

- `WorkspaceStatus`
- `WorkspaceBase`
- `WorkspaceCreate`
- `Workspace`
- `WorkspacePublic`

Recommended near-term additions:

- `WorkspaceVisibility`
- expanded `WorkspaceStatus`
- `WorkspaceAction`
- `WorkspaceAccessSummary`
- `WorkspaceBootstrapIntent`
- `WorkspaceConnectivitySummary`
- `WorkspaceUpdate`
- `WorkspaceServicesPublic`

### Proposed `WorkspaceCreate`

Recommended delta:

```ts
interface WorkspaceCreate {
  name: string
  flavour?: "base" | "dev" | "python" | "node" | "jupyter"
  kind?: string
  project_id?: string | null
  visibility?: "private" | "project" | "shared"

  repo_source_type?: "external_url" | "user_repo" | "shadow_repo" | null
  repo_source_id?: string | null
  repo_url?: string | null

  ssh_pubkey?: string | null
  env_vars?: Record<string, string>

  bootstrap_profile?: string | null
  startup_profile?: string | null
  install_command?: string | null
  startup_command?: string | null
  requested_agent_profile?: string | null

  tags?: string[]
}
```

Notes:

- `repo_url` should remain valid for external imports.
- `project_id` should be optional for the first pass.
- `visibility` should likely default to `private`.
- command fields can be accepted but initially feature-gated if needed.

### Proposed `WorkspacePublic`

Recommended delta:

```ts
interface WorkspacePublic {
  id: string
  owner_id: string
  name: string
  flavour: string
  kind: string

  status: WorkspaceStatus
  allowed_actions: WorkspaceAction[]
  last_transition_at: string

  visibility: "private" | "project" | "shared"
  project_id: string | null
  tags: string[]
  capabilities: string[]

  kennel_name: string | null
  kennel_job: string | null

  failure_code: string | null
  failure_message: string | null
  stop_reason: string | null

  bootstrap: {
    repo_source_type: "external_url" | "user_repo" | "shadow_repo" | null
    repo_source_id: string | null
    repo_url: string | null
    bootstrap_profile: string | null
    startup_profile: string | null
    requested_agent_profile: string | null
  }

  access_summary: {
    owner_id: string
    visibility: "private" | "project" | "shared"
    project_id: string | null
    can_manage: boolean
    can_use: boolean
  }

  connectivity_summary: {
    terminal_status: "unavailable" | "available" | "expired"
    services_ready: boolean
    room_attachable: boolean
  }

  created_at: string
  updated_at: string
}
```

Notes:

- `allowed_actions` is intentionally explicit.
- `bootstrap` and `connectivity_summary` reduce pressure on `meta`.
- raw `terminal_url` should not remain a durable field on the main workspace resource; keep terminal issuance separate.

## Proposed Endpoint Deltas

### Keep

- `POST /api/v1/workspaces/`
- `GET /api/v1/workspaces/`
- `GET /api/v1/workspaces/{workspace_id}`
- `GET /api/v1/workspaces/{workspace_id}/terminal`
- `POST /api/v1/workspaces/{workspace_id}/stop`
- `DELETE /api/v1/workspaces/{workspace_id}`

### Add

- `PATCH /api/v1/workspaces/{workspace_id}`
  Near-term use:
  - rename workspace
  - change visibility
  - assign or clear project
  - update tags

- `POST /api/v1/workspaces/{workspace_id}/start`
  Needed if `stopped` becomes a meaningful recoverable state.

- `GET /api/v1/workspaces/{workspace_id}/services`
  Returns approved service discovery descriptors for room/agent integration.

- `POST /api/v1/workspaces/{workspace_id}/project`
  Optional convenience route if project association is not handled via generic patching.

### List Endpoint Behavior

`GET /api/v1/workspaces/` should support near-term filters:

- `status`
- `project_id`
- `visibility`
- `tag`

Recommended default:

- exclude `destroyed` by default
- optionally include with `include_destroyed=true` for operator/debug views

### Terminal Endpoint Behavior

Keep:

- backend-issued URL
- short-lived token
- backend remains authoritative for terminal eligibility

Change:

- terminal endpoint should key off `allowed_actions` or explicit terminal readiness semantics, not raw `status == ready`

## Persistence Deltas

Recommended near-term schema changes:

- expand `WorkspaceStatus` enum
- add `visibility`
- add nullable `project_id`
- add `last_transition_at`
- add `failure_code`
- add `failure_message`
- add `stop_reason`
- add `tags` as JSON array or normalized table
- add `capabilities` as JSON array or derived projection

Potentially defer:

- full relation tables for workspace-to-workspace relationships
- full service descriptor persistence if discovery can be generated dynamically

## Service-Layer Behavior Changes

### Provisioning Flow

Current behavior in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py):

- create record in `provisioning`
- create kennel env
- poll
- inject workspace
- mark `ready`
- mark `destroyed` on failure

Recommended behavior:

- create record in `requested`
- move to `provisioning` when kennel job is issued
- move to `starting` when bootstrap / injection / startup begins
- move to `ready` only when declared readiness condition is met
- move to `failed` on provision/bootstrap/startup error
- move to `destroying` before destruction
- only move to `destroyed` when the resource is actually gone

### Readiness Semantics

Near-term recommendation:

- `ready` means terminal-ready and bootstrap-complete

Later refinement:

- service-level readiness can remain in `connectivity_summary` or service discovery routes rather than exploding the top-level status enum further

### Failure Semantics

Do not encode failure only in `meta.error`.

Instead:

- set `status = failed`
- set `failure_code`
- set `failure_message`
- keep raw diagnostic details in `meta` if useful for local/operator debugging

## Frontend Contract Impact

The frontend service layer in [workspaceService.ts](/home/josep/dog/frontend/src/services/workspaceService.ts) should evolve to:

- map explicit backend status values directly
- expose `allowed_actions` instead of deriving all capability flags locally
- present `bootstrap` and `access_summary` in detail panels
- use filters on the list route once the API supports them

The frontend route and panel layer should not need a structural rewrite. The main changes are:

- expanded view models
- more explicit control gating
- more legible detail surfaces
- eventual project/repo/room linkage UI

## Recommended First-Phase Delta Set

To avoid overloading the first implementation pass, this is the narrowest useful delta set:

1. expand `WorkspaceStatus` to include `requested`, `starting`, `failed`, and `destroying`
2. add `allowed_actions`
3. add `visibility`
4. add nullable `project_id`
5. add `last_transition_at`
6. add `failure_message`
7. move bootstrap identity out of ad hoc `meta` into explicit response fields
8. add `PATCH /workspaces/{id}` and `POST /workspaces/{id}/start`

If we do only those eight changes well, the next tracks become much easier to reason about.

## Open Questions

- Should project association live directly on `Workspace`, or should project attachment remain the canonical relationship with `WorkspacePublic` projecting the primary project?
- Should `allowed_actions` be persisted, or generated per-request from state + access rules?
- Is `ready` defined by terminal readiness, bootstrap completion, or declared service availability?
- Do we want `visibility = shared` in the near term, or should near-term access be only `private` and `project`?
- Should tags be first-class in the first migration, or stay in `meta` until project/access semantics settle?
