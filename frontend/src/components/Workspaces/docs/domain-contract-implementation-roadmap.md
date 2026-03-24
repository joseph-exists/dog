# Workspace Domain Contract Implementation Roadmap

## Context

Track 1 is the first implementation pass for turning `Workspace` from a thin kennel wrapper into a real platform object with explicit lifecycle, access, and operational semantics.

The current backend implementation is functional but too small for the next milestone:

- lifecycle is limited to `provisioning`, `ready`, `stopping`, `stopped`, `destroyed`
- failure is currently collapsed into `destroyed`
- project and access semantics are absent from the workspace contract
- terminal gating is inferred from status rather than modeled as an explicit capability
- the frontend service layer is deriving too much from incomplete backend truth

This roadmap intentionally focuses on the narrowest useful subset of the domain contract draft so we can improve truth at the source without accidentally pulling in all later tracks at once.

## Current Implementation Status

Completed so far:

- Step 1: backend model expansion and migration
- Step 2: backend service lifecycle truth in `workspace_service.py`
- Step 3: backend route/API projection and `start` endpoint exposure
- Step 4: frontend service and hook alignment
- Step 5: panel and route presentation alignment

What is now true in the backend service layer:

- workspace creation begins at `requested`
- provisioning transitions through `provisioning`
- bootstrap/injection transitions through `starting`
- successful completion reaches `ready`
- provisioning, stop, restart, and destroy failures now resolve to `failed` with `failure_message`
- destroy now transitions through `destroying` before `destroyed`
- terminal eligibility is now aligned with backend-owned action semantics via `get_allowed_actions()`

What is still pending for Track 1:

- close-out documentation and sequencing review
- optional UX refinement if we decide the current panel surface still hides important state

## Scope

This pass should implement:

- expanded lifecycle states
- first-class failure semantics
- explicit `allowed_actions`
- projected visibility and project association fields
- first-class lifecycle timestamps needed for operator clarity
- backend and frontend model alignment

This pass should not yet implement:

- full repo/bootstrap restructuring
- service discovery endpoints
- room/workspace connectivity issuance
- full tags/capabilities management
- arbitrary start/install command flows

## API Design

### Status Enum

Replace the current workspace status set with:

- `requested`
- `provisioning`
- `starting`
- `ready`
- `stopping`
- `stopped`
- `failed`
- `destroying`
- `destroyed`

### Allowed Actions

Add a backend-owned action enum exposed on `WorkspacePublic`.

Near-term values:

- `destroy`
- `stop`
- `start`
- `request_terminal`
- `discover_services`

### WorkspacePublic Delta

Add to `WorkspacePublic`:

```ts
allowed_actions: WorkspaceAction[]
visibility: "private" | "project"
project_id: UUID | null
project_summary: { id: UUID; name: string } | null
last_transition_at: datetime
failure_message: str | null
requested_at: datetime | null
started_at: datetime | null
ready_at: datetime | null
stopped_at: datetime | null
destroyed_at: datetime | null
terminal_status: "unavailable" | "available" | "expired"
```

Notes:

- `project_id` and `project_summary` are projected convenience fields, not canonical persistence.
- `visibility` should be projected from project attachment state for now.
- `terminal_status` should remain simple in this pass.

### WorkspaceCreate Compatibility

Keep the existing request shape for this pass:

- `name`
- `flavour`
- `kind`
- `repo_url`
- `ssh_pubkey`
- `env_vars`

Do not expand create input yet. That belongs to the repo/bootstrap track.

### Endpoint Changes

Keep existing endpoints:

- `POST /api/v1/workspaces/`
- `GET /api/v1/workspaces/`
- `GET /api/v1/workspaces/{workspace_id}`
- `GET /api/v1/workspaces/{workspace_id}/terminal`
- `POST /api/v1/workspaces/{workspace_id}/stop`
- `DELETE /api/v1/workspaces/{workspace_id}`

Add:

- `POST /api/v1/workspaces/{workspace_id}/start`

Defer:

- `PATCH /api/v1/workspaces/{workspace_id}`
- `GET /api/v1/workspaces/{workspace_id}/services`

### Backend Behavior Changes

Provisioning flow should become:

1. create workspace in `requested`
2. move to `provisioning` when kennel job is issued
3. move to `starting` when injection/bootstrap begins
4. move to `ready` when terminal-ready bootstrap completes
5. move to `failed` on provisioning/bootstrap error
6. move to `destroying` before destroy
7. move to `destroyed` only after destroy succeeds

Terminal endpoint should validate:

- caller has access
- workspace state allows `request_terminal`
- terminal status is `available`

Project projection should resolve:

- zero or one `ProjectResource(resource_type="workspace")`

## Implementation Plan

### Step 1: Backend Model Expansion

Update backend model definitions to support the first-pass contract.

Files:

- `/home/josep/dog/backend/app/models.py`
- new alembic migration under `/home/josep/dog/backend/app/alembic/versions`

Changes:

- expand `WorkspaceStatus`
- add `WorkspaceAction`
- add new lifecycle timestamp fields
- add `failure_message`
- add projected visibility/project fields to public model only
- add `terminal_status` to public model

Important constraint:

- do not make canonical project linkage live on `Workspace`
- project fields on public response should be projected

### Step 2: Backend Service Truth

Refactor workspace service logic to emit the new lifecycle semantics.

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`

Changes:

- create with `requested`
- update transitions in provisioning flow
- set failure state to `failed` with `failure_message`
- set lifecycle timestamps when transitions occur
- add a helper that computes `allowed_actions`
- add a helper that computes `terminal_status`
- add `start_workspace()` for `stopped -> starting/provisioning` path

Important constraint:

- do not implement repo/bootstrap expansion here beyond status correctness

Status:

- implemented
- `start_workspace()` now exists in the service layer and uses kennel's restart action
- route exposure for restart is still pending in Step 3

### Step 3: Workspace Projection Layer

Teach workspace routes to return the richer projected contract.

Files:

- `/home/josep/dog/backend/app/api/routes/workspaces.py`
- likely supporting query/helper logic in `/home/josep/dog/backend/app/services/workspace_service.py`
- possibly `/home/josep/dog/backend/app/crud_projects.py` if a shared lookup helper is useful

Changes:

- list/detail responses should include:
  - `allowed_actions`
  - `visibility`
  - `project_id`
  - `project_summary`
  - `terminal_status`
- add `POST /workspaces/{id}/start`

Important constraint:

- project projection should derive from `ProjectResource(resource_type="workspace")`
- enforce near-term zero-or-one relationship rule in projection code

Status:

- implemented
- create/list/detail now project:
  - `allowed_actions`
  - `visibility`
  - `project_id`
  - `project_summary`
  - `terminal_status`
- `POST /workspaces/{id}/start` now exists at the route layer
- project linkage is projected from `ProjectResource(resource_type="workspace")`

### Step 4: Frontend Service And Hook Alignment

Update frontend service and query logic to consume the new contract without continuing to infer old semantics.

Files:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaces.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspace.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaceTerminal.ts`

Changes:

- map expanded statuses directly
- replace local capability guessing with `allowed_actions`
- surface failure state and projected project summary
- support `start` mutation

Important constraint:

- keep view models concise
- do not pull in repo/bootstrap contract fields yet unless needed for compatibility

Status:

- implemented
- frontend service and hooks now consume:
  - expanded lifecycle states
  - `allowed_actions`
  - projected project context
  - terminal status
  - lifecycle timestamps
- `useStartWorkspace()` now exists and is wired to the regenerated client

### Step 5: UI Surface Update

Update workspace panels and routes to reflect the richer contract.

Files:

- `/home/josep/dog/frontend/src/routes/_layout/workspaces.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/workspace.$workspaceId.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceControlsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx`

Changes:

- show clearer state labels
- show failure state distinctly
- show project association projection
- gate controls from backend actions
- show terminal availability more explicitly

Important constraint:

- keep layout stable
- do not redesign the feature shell in this pass

Status:

- implemented
- detail route now wires the new `start` mutation
- status badge supports the expanded lifecycle
- list/detail/terminal panels now surface:
  - failure state
  - project projection
  - terminal availability
  - current backend action surface
- frontend typecheck passes against the regenerated client

### Step 6: Verification And Documentation

Verify the backend/frontend contract and update planning docs to reflect reality.

Files:

- `/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md`
- `/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md`
- `/home/josep/dog/frontend/src/components/Workspaces/docs/implemented-roadmap.md` if implementation meaningfully changes current truth

Verification targets:

- create returns `requested` or immediate first valid transition
- provisioning errors land in `failed`, not `destroyed`
- stopped workspaces can be restarted
- terminal request is denied when `request_terminal` is absent
- list/detail surfaces render projected project context and failure state correctly
- frontend typecheck passes

Status:

- partial completion
- Python syntax checks passed for the backend files touched in this track
- frontend `npm run typecheck` passes after the alignment work
- route/API behavior still needs runtime verification in the app before this track should be considered fully closed

## File Touch List

Backend:

- `/home/josep/dog/backend/app/models.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`
- `/home/josep/dog/backend/app/api/routes/workspaces.py`
- `/home/josep/dog/backend/app/alembic/versions/<new_migration>.py`

Possible backend helper touchpoints:

- `/home/josep/dog/backend/app/crud_projects.py`

Frontend:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaces.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspace.ts`
- `/home/josep/dog/frontend/src/hooks/useWorkspaceTerminal.ts`
- `/home/josep/dog/frontend/src/routes/_layout/workspaces.tsx`
- `/home/josep/dog/frontend/src/routes/_layout/workspace.$workspaceId.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceControlsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx`

Docs:

- `/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md`
- `/home/josep/dog/frontend/src/components/Workspaces/docs/planning.md`

## Risks

- enum and schema changes will require regenerated client types if the frontend depends on generated workspace models
- projecting project attachment may add query complexity faster than expected
- restart semantics may expose kennel behavior that is currently only safe for destroy/recreate
- terminal gating may reveal assumptions in the shared terminal path

## Recommended Execution Order

1. backend model and migration
2. backend service transitions
3. backend route projection and start endpoint
4. frontend service/hook alignment
5. panel and route updates
6. verification and document updates

## Sequencing Review

The sequencing still holds.

Why:

- Track 1 successfully made workspace identity and lifecycle legible without dragging in Track 2 complexity prematurely
- the API and UI now have a stable enough operational model to support repo/bootstrap work next
- the remaining uncertainty is no longer “what is a workspace?” but “how should repo/bootstrap intent and readiness be expressed on top of that workspace?”

Recommendation:

- move into Track 2 next
- keep Track 1 open only for targeted cleanup discovered while implementing repo/bootstrap semantics
