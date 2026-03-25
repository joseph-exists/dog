# Service Readiness And Discovery Roadmap

## Context

Track 2 now has a coherent bootstrap vertical slice:

- bootstrap intent is typed
- backend generates the execution plan
- kennel executes the plan
- workspace detail surfaces show bootstrap progress and started services

The next ambiguity is no longer bootstrap mechanics. It is service readiness and discovery:

- what a workspace claims is running
- what the backend can verify is actually discoverable
- which parts belong in workspace detail
- which parts belong in room/workspace connectivity later

This roadmap defines the next implementation pass before coding.

## Guiding Decision

Service readiness should be a backend-issued summary built from explicit discovery data.

Not:

- inferred from bootstrap profile names alone
- inferred from frontend heuristics
- inferred from operator rebuild job state

Operator rebuild jobs are still valuable, but they belong to flavour health and kennel operations, not to the canonical runtime readiness contract for an individual workspace.

## What Rebuild Jobs Are Good For

The newer kennel rebuild conveniences are useful in this milestone, but at the right layer.

They should contribute:

- flavour snapshot availability
- latest rebuild outcome for the chosen flavour
- operator-facing diagnostics when workspace creation fails because the base layer is unhealthy

They should not directly decide:

- whether a specific workspace service is discoverable
- whether a room may connect to a workspace service
- whether a workspace is `ready` for a purpose-specific runtime capability

## Scope

This pass should implement:

- a backend-owned workspace service discovery summary
- kennel-side runtime discovery for a narrow first set of endpoint kinds
- workspace detail API projection for discovered services
- purpose-specific readiness summary that remains compatible with Track 4 room connectivity
- optional flavour-health projection for operator awareness

This pass should not yet implement:

- room/workspace connection descriptor issuance
- full room authorization flow
- arbitrary service registration APIs from inside the workspace
- a generalized service mesh or proxy layer

## Proposed Contract Additions

### Workspace Service Summary

Add a typed service discovery summary to the workspace public contract.

Recommended shape:

```ts
interface WorkspaceServiceSummary {
  id: string
  kind: "web_app" | "agent_runtime" | "jupyter" | "custom"
  label: string
  status: "pending" | "ready" | "failed" | "unknown"
  protocol: "http" | "https" | "ws" | "wss"
  host: string | null
  port: number | null
  path: string | null
  url: string | null
  source: "bootstrap_profile" | "runtime_probe" | "operator_declared"
  readiness_message: string | null
}
```

### Workspace Connectivity Summary

Add a workspace-facing summary that helps both detail UI and later room attachment logic.

Recommended shape:

```ts
interface WorkspaceConnectivitySummary {
  terminal_ready: boolean
  bootstrap_complete: boolean
  services_ready: boolean
  service_count: number
  ready_service_count: number
}
```

This can replace or subsume the current thin `readiness_summary`.

### Optional Flavour Health Projection

Add a narrow operator-oriented summary to the workspace detail projection.

Recommended shape:

```ts
interface WorkspaceFlavourHealthSummary {
  flavour: string
  snapshot_ready: boolean
  latest_rebuild_status: "pending" | "running" | "done" | "failed" | null
  latest_rebuild_job_id: string | null
}
```

Important:

- this is contextual operator information
- it should not be treated as proof that the runtime inside the workspace is healthy

## Implementation Tracks

### Step 1: Backend Models

Files:

- `/home/josep/dog/backend/app/models.py`

Changes:

- add typed service summary model
- add typed connectivity summary model
- add optional flavour health summary model
- extend `WorkspacePublic`

Status:

- implemented
- `WorkspacePublic` now has:
  - `services`
  - `connectivity_summary`
  - `flavour_health`
- `WorkspaceReadinessSummary` now also carries service counts so existing consumers can evolve gently while the richer connectivity summary comes online

### Step 2: Kennel Discovery Contract

Files:

- `/home/josep/dog/kennel/src/server.py`
- possibly helper module inside `kennel/src/`

Changes:

- add a management endpoint like `GET /envs/{name}/services`
- inspect runtime state for a narrow set of first-pass signals:
  - background service pids/log files created by bootstrap start steps
  - listening ports where practical
  - profile-derived defaults for known startup profiles

Important constraint:

- keep the first pass conservative and inspectable
- avoid pretending to discover everything

Status:

- implemented for the first slice
- kennel now exposes `GET /envs/{name}/services`
- bootstrap injection now writes a small service manifest for background startup steps
- first-pass readiness inference is:
  - `ready` when the expected port is listening
  - `pending` when the service pid is running but the expected port is not listening yet
  - `failed` when the expected service process is no longer running
  - `unknown` when no meaningful runtime process metadata exists
- known startup profiles currently inferred:
  - `vite` → `http://127.0.0.1:5173/`
  - `nextjs` → `http://127.0.0.1:3000/`
  - `fastapi` → `http://127.0.0.1:8000/docs`
- custom background services still appear in discovery, but without profile-specific endpoint defaults

### Step 3: Backend Workspace Projection

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`
- `/home/josep/dog/backend/app/services/kennel_client.py`

Changes:

- fetch or derive service summaries for eligible workspaces
- project service readiness into `WorkspacePublic`
- keep `allowed_actions` authoritative for connectivity capability

Important constraint:

- service discovery failure should degrade to explicit unknown/failed service state
- it should not silently collapse into generic workspace failure

Status:

- implemented for the current slice
- backend workspace projection now:
  - fetches discovered services from kennel for `starting` and `ready` workspaces
  - falls back to declared bootstrap services when runtime discovery is unavailable
  - projects `services`, `connectivity_summary`, and richer `readiness_summary`
  - projects optional flavour-health context from kennel `/flavours`
- flavour-health fetching is cached briefly in the backend service layer so workspace list/detail views do not repeatedly hit kennel for identical flavour metadata

### Step 4: Frontend Detail And Fleet Alignment

Files:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx`

Changes:

- show discovered services distinctly from bootstrap intent
- separate bootstrap complete from service ready
- add flavour-health cues only where they help operators

Status:

- implemented for the current slice
- frontend service/view-model alignment now projects:
  - discovered `services`
  - `connectivity_summary`
  - `flavour_health`
- workspace detail polling now continues while discovered services are still pending, which keeps readiness feedback live through the final startup phase
- workspace list now surfaces service counts, primary endpoint context, and flavour snapshot cues
- workspace detail now separates bootstrap state from discovered runtime services and shows direct endpoint links where available
- workspace terminal metadata now includes discovered service readiness so terminal use and service availability can be understood together

### Step 5: Sequencing Hand-Off To Track 4

At the end of this slice, the next room/workspace connectivity pass should be able to rely on:

- explicit service summaries
- purpose-specific readiness
- backend-issued discoverability semantics

That gives Track 4 a better foundation than using bootstrap profiles alone.

## First-Pass Recommendation

The narrowest useful first implementation is:

1. add `services` to `WorkspacePublic`
2. add kennel `GET /envs/{name}/services`
3. discover only known startup-profile services at first:
   - `vite`
   - `nextjs`
   - `fastapi`
4. mark service status from runtime evidence where available
5. project a richer `readiness_summary`
6. add optional flavour health summary from kennel `/flavours`

## Why This Sequencing Still Holds

This is the right next step because:

- Track 2 still owns runtime intent and readiness semantics
- Track 4 depends on readiness and discovery but should not define them retroactively

## Current Assessment

This slice now forms a coherent vertical path:

- bootstrap intent declares what should happen
- kennel discovery reports what appears to be running
- backend workspace projection turns that into typed readiness and service summaries
- frontend list, detail, and terminal surfaces make that runtime state visible

The remaining sequencing question is no longer whether service discovery belongs in Track 2. It does.

The next question is where to spend the next implementation energy:

- deepen runtime intent for additional service kinds such as `agent_service` and later `shadow_repo` materialization, or
- move into Track 3 and Track 4 now that readiness, discovery, and projected project context are all explicit enough to support relationship and trust work
- operator rebuild jobs can now be folded in as support signals without letting operator tooling distort the user-facing runtime contract

## Open Questions

- Should first-pass service discovery read directly from bootstrap-created pid/log files, or should kennel create a more explicit runtime registration artifact?
- Should flavour-health data be shown to all workspace viewers or only operators/owners?
- Should `services_ready` mean “at least one declared service is ready” or “all declared services are ready” for the current slice?
- Do we want discovery polling only on workspace detail, or also in list cards when a service-oriented startup profile is present?
