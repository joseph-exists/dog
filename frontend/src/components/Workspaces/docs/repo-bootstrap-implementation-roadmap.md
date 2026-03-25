# Repo And Bootstrap Implementation Roadmap

## Context

Track 2 is the next implementation pass after the workspace domain contract work.

Track 1 made the workspace itself legible:

- lifecycle is explicit
- failure semantics are explicit
- action availability is explicit
- project context is projected
- the frontend now consumes that richer truth

That means the next layer of uncertainty is no longer the workspace object itself. It is the meaning of repo-backed bootstrap:

- what source a workspace is bootstrapping from
- what install intent should run
- what startup intent should run
- how progress and failure should be surfaced
- what `ready` means for a repo-backed workspace

This roadmap turns the repo/bootstrap contract into a concrete implementation sequence before code changes begin.

## Scope

This pass should implement:

- explicit workspace bootstrap intent
- explicit repo source types:
  - `external_url`
  - `user_repo`
  - `shadow_repo`
- backend validation and normalization of repo/bootstrap intent
- backend-owned bootstrap plan generation
- bootstrap progress reporting
- first-pass kennel execution that follows the normalized plan
- frontend create/detail surfaces that expose bootstrap intent and progress

This pass should not yet implement:

- room/workspace connection issuance
- full service discovery and endpoint registration
- arbitrary user-supplied install/start commands
- generalized writeback semantics for shadow repos
- full tags/capabilities management

## Current Implementation Status

Completed so far:

- Step 1: backend workspace create/detail contract expanded with typed bootstrap intent and progress
- Step 2: backend validation and normalization for `external_url` and `user_repo`
- Step 3: backend-generated bootstrap plan now exists for the current repo/install/start slice
- Step 4: kennel inject now consumes a structured bootstrap plan and returns structured step results
- Step 5: workspace provisioning now persists the generated plan and records kennel execution results

What is now true:

- `WorkspaceCreate` can express a typed `bootstrap` payload
- `WorkspacePublic` can express typed `bootstrap` and `readiness_summary` projections
- repo source, install intent, startup intent, and bootstrap progress now have explicit backend model types
- legacy create fields remain available for compatibility during the transition
- backend normalization now:
  - converts legacy `repo_url` input into typed `external_url` bootstrap intent
  - validates `external_url` references conservatively
  - validates `user_repo` ownership/readiness
  - materializes `user_repo` through its current `source_repo_url` as a temporary bridge
  - recognizes `shadow_repo` in the contract but rejects execution in this slice with an explicit validation error
- create-route validation errors now return structured API errors instead of falling through as generic failures
- bootstrap execution is now backend-owned and plan-driven rather than inferred from a thin kennel payload
- the generated plan is stored in workspace metadata so later engineers can inspect the backend's operational intent
- kennel inject now executes a small set of explicit step types:
  - `add_ssh_key`
  - `write_env_vars`
  - `clone_repo`
  - `run_command`
- kennel now returns structured `step_results`, `started_services`, `workspace_path`, and a `bootstrap_success` signal
- install intent support in this slice is:
  - `none`
  - `auto`
  - named profiles: `npm`, `pnpm`, `yarn`, `uv`, `pip`
- startup intent support in this slice is:
  - `terminal_only`
  - named profiles: `vite`, `nextjs`, `fastapi`
- `agent_service` startup is now enabled through a backend-owned first profile set:
  - `codex`
  - `claude_code`
  - `hermes`
- the current launcher commands are intentionally overrideable by environment variable while the runtime semantics and kennel discovery path continue to mature

What is still pending:

- deeper repo-source support beyond the first slice, especially platform-native `user_repo` materialization and `shadow_repo` execution
- deeper `agent_service` execution and discovery semantics
- richer runtime/service readiness checks and service discovery

## Design Intent

The key principle of Track 2 is:

- frontend declares intent
- backend validates and resolves intent
- kennel executes a normalized plan

This avoids three failure modes:

- frontend composing operational shell logic
- backend passing under-modeled bootstrap blobs into kennel
- workspace readiness meaning different things in different layers

## Proposed API Design

### Workspace Create Request

Current request shape is too small:

- `name`
- `flavour`
- `kind`
- `repo_url`
- `ssh_pubkey`
- `env_vars`

Recommended near-term request shape:

```ts
interface WorkspaceCreate {
  name: string
  flavour?: WorkspaceFlavour
  kind?: string

  bootstrap?: {
    repo_source?:
      | { type: "external_url"; repo_url: string; ref?: string | null }
      | { type: "user_repo"; repo_id: string; ref?: string | null }
      | { type: "shadow_repo"; entity_type: string; entity_id: string; ref?: string | null }
      | null

    install_intent?:
      | { mode: "none" }
      | { mode: "auto" }
      | { mode: "profile"; profile: string }

    startup_intent?:
      | { mode: "terminal_only" }
      | { mode: "profile"; profile: string }
      | { mode: "agent_service"; agent_profile: string }

    workspace_path?: string | null
    env_vars?: Record<string, string>
    ssh_pubkey?: string | null
  }
}
```

Compatibility rule:

- keep accepting legacy top-level `repo_url`, `ssh_pubkey`, and `env_vars` for a transition period
- backend normalizes legacy input into the new `bootstrap` shape

### Workspace Detail Response

Recommended additions to `WorkspacePublic`:

```ts
bootstrap: {
  intent: WorkspaceBootstrapIntent | null
  progress: WorkspaceBootstrapProgress | null
}

readiness_summary: {
  terminal_ready: boolean
  bootstrap_complete: boolean
  services_ready: boolean
}
```

This should sit alongside the lifecycle contract from Track 1 rather than replacing it.

### Optional Discovery Endpoint

Add:

- `GET /api/v1/workspaces/bootstrap-profiles`

Purpose:

- expose backend-supported install/start profiles so frontend create UI does not hardcode them

### Error Shape

Introduce explicit bootstrap validation errors where helpful:

- repo not ready
- repo not accessible
- unsupported bootstrap profile
- unsupported startup profile
- invalid repo source

The user-facing value is that repo/bootstrap failures become clearly attributable before kennel work begins.

## Data Model Design

### Near-Term Persistence Strategy

Avoid a full new bootstrap table set in the first pass unless needed.

Recommended near-term strategy:

- persist normalized bootstrap intent in explicit workspace response fields where already available
- store structured bootstrap progress in `meta` initially if that keeps the schema smaller
- move to dedicated structured columns or child tables later if the progress model grows beyond operational convenience

### Recommended Near-Term Additions

Add to workspace persistence or strongly structured metadata:

- `bootstrap.intent`
- `bootstrap.progress`

If stored in `meta` initially, it should still follow a stable backend-owned shape and not be treated as arbitrary freeform metadata.

## Implementation Plan

### Step 1: Backend Contract Expansion

Expand backend models to express bootstrap intent in the workspace contract.

Files:

- `/home/josep/dog/backend/app/models.py`
- new alembic migration if explicit persisted fields are added

Changes:

- add typed bootstrap intent models
- add typed bootstrap progress models
- extend `WorkspaceCreate`
- extend `WorkspacePublic`
- preserve backward compatibility for the existing create request during transition

Important constraint:

- do not expose arbitrary `command` execution in this first pass

Status:

- implemented
- typed bootstrap intent and progress now exist on the backend workspace create/detail contract
- persistence and execution behavior remain for later steps

### Step 2: Repo Source Validation And Resolution

Introduce backend helpers that validate and resolve repo sources before kennel bootstrap begins.

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`
- likely new helper module such as:
  - `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`

Related read/authorization surfaces:

- `/home/josep/dog/backend/app/api/routes/user_repos.py`
- `/home/josep/dog/backend/app/api/routes/shadow_repos.py`
- underlying user-repo and shadow-repo services

Changes:

- validate `external_url`
- authorize and validate `user_repo`
- authorize and validate `shadow_repo`
- reject `user_repo` when import status is not `ready`
- normalize bootstrap intent into a backend-generated resolved plan

Important constraint:

- repo source authorization should stay backend-owned
- frontend should never turn a repo id into a clone path or forge URL

Status:

- implemented for the first slice
- `external_url` and `user_repo` now validate and normalize in the backend service layer
- `user_repo` currently bridges through `source_repo_url` so we can keep delivery moving while preserving a clear extension point for platform-native materialization
- `shadow_repo` is intentionally deferred at execution time even though the typed contract already recognizes it

### Step 3: Bootstrap Plan Generation

Generate a normalized execution plan before kennel work begins.

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`
- likely new helper module such as:
  - `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`

Changes:

- resolve repo materialization mode:
  - none
  - git clone
  - platform repo export/materialization
- resolve install steps from:
  - `none`
  - `auto`
  - backend-defined `profile`
- resolve startup steps from:
  - `terminal_only`
  - backend-defined `profile`
  - backend-defined `agent_service`
- define readiness checks for the plan

Important constraint:

- the plan should be backend-generated
- the frontend should only submit intent, not executable step arrays

Status:

- implemented for the current first slice
- the plan is intentionally linear and compact so it remains easy to evolve
- install/start profile registries are small by design and should be treated as extension points, not final ceilings

### Step 4: Kennel Execution Contract

Adjust kennel-side execution to consume a structured plan rather than only loose injected values.

Files:

- `/home/josep/dog/kennel/provision/00-base.sh`
- `/home/josep/dog/kennel/provision/01-dev.sh`
- kennel inject/start handling code as needed

Changes:

- preserve the current base image preparation
- add plan-aware materialization/install/start execution
- report structured step progress or failure back to backend

Important constraint:

- do not try to build a full remote workflow engine here
- keep the first pass linear and operationally understandable

Status:

- implemented for the first slice
- kennel inject now supports explicit plan execution with structured results while keeping legacy fields for compatibility

### Step 5: Workspace Service Integration

Integrate bootstrap plan generation and progress recording into workspace provisioning.

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`

Changes:

- normalize create input into bootstrap intent
- record bootstrap intent on the workspace
- record bootstrap progress during provisioning
- define `ready` as:
  - repo materialization complete
  - install intent complete
  - startup intent complete
  - readiness checks passed
  - terminal available

Important constraint:

- Track 1 lifecycle semantics should remain authoritative
- bootstrap progress should refine readiness, not replace lifecycle state

Status:

- implemented for the current slice
- workspace metadata now records:
  - `bootstrap_intent`
  - `bootstrap_plan`
  - `bootstrap_progress`
  - `bootstrap_step_results`
  - `bootstrap_started_services`
  - `bootstrap_workspace_path`
- lifecycle state still owns the top-level truth; bootstrap plan execution now gives that lifecycle more meaningful internals

### Step 6: Frontend Service And Create Surface Alignment

Update frontend service and create/detail surfaces to work with bootstrap intent and progress.

Files:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaces.ts`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- possibly `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`

Changes:

- create flow can choose repo source type
- create flow can choose install/start profile in a constrained way
- detail surface can show bootstrap intent and progress
- failure surface can distinguish lifecycle failure from bootstrap failure

Important constraint:

- start simple
- avoid building a large multi-mode create wizard until the backend contract is stable

Status:

- implemented for the current frontend slice
- the create surface now supports:
  - repo source selection for `none`, `external_url`, and `user_repo`
  - optional repo ref and workspace path
  - install intent `none | auto | profile`
  - startup intent `terminal_only | profile`
- the list/detail/terminal surfaces now project:
  - bootstrap intent
  - bootstrap progress
  - started services
  - workspace bootstrap path
- the generated client now includes the richer workspace bootstrap and readiness schema
- frontend service alignment now reads bootstrap/readiness from generated contract fields directly
- structured metadata remains in use only for execution details that are still intentionally metadata-backed, such as step results and started services

### Step 7: Verification And Documentation

Update the source notes so they reflect the implemented bootstrap semantics rather than only the proposal.

Files:

- `/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md`
- `/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md`
- this roadmap file
- `/home/josep/dog/frontend/src/components/Workspaces/docs/implemented-roadmap.md` if the implementation materially shifts the existing frontend truth

Verification targets:

- create with `external_url` still works
- create with `user_repo` rejects non-ready repos cleanly
- create with `shadow_repo` resolves read-oriented materialization cleanly
- bootstrap progress is visible during provisioning
- `ready` is not emitted before the bootstrap plan is complete
- frontend typecheck passes

## File Touch List

Backend:

- `/home/josep/dog/backend/app/models.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`
- likely `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- possibly helper/service files for user-repo and shadow-repo resolution
- new alembic migration if explicit persisted fields are added

Backend route surfaces:

- `/home/josep/dog/backend/app/api/routes/workspaces.py`
- possibly a new bootstrap-profile discovery route

Kennel:

- `/home/josep/dog/kennel/provision/00-base.sh`
- `/home/josep/dog/kennel/provision/01-dev.sh`
- kennel inject/start handling code as needed

Frontend:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaces.ts`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- optionally `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`

Docs:

- `/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md`
- `/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md`
- this roadmap file

## Risks

- bootstrap intent can sprawl quickly if install/start profiles are not constrained early
- mixing repo resolution and kennel execution inside one service can become hard to maintain
- `shadow_repo` semantics can drift if read-oriented materialization is not kept narrow
- readiness can become ambiguous again if bootstrap progress and lifecycle state are not kept distinct

## Recommended Execution Order

1. backend contract expansion
2. repo source validation and resolution
3. bootstrap plan generation
4. kennel execution contract
5. workspace service integration
6. frontend create/detail alignment
7. verification and documentation

## Recommended First Coding Slice

The best first coding slice for Track 2 is:

1. extend backend workspace create/detail models with typed bootstrap intent and progress
2. add backend validation for `external_url` and `user_repo`
3. keep the first pass to:
   - `external_url`
   - `user_repo`
   - install intent `none | auto | profile`
   - startup intent `terminal_only | profile | agent_service`
4. defer `shadow_repo` execution support until the contract and validation path are stable, even if the model shape includes it

That gives us a disciplined first vertical slice instead of trying to solve the whole bootstrap matrix in one move.
