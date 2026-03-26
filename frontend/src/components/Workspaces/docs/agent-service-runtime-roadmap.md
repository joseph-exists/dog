# Agent Service Runtime Roadmap

## Purpose

This artifact defines the next Track 2 slice: enabling `agent_service` startup intent as a real backend-owned runtime path rather than a typed-but-rejected contract branch.

The goal of this slice is not to finalize the entire agent runtime vocabulary. It is to make the first agent-oriented runtime/service kind real enough that later project and room integration work can build on explicit behavior instead of placeholder semantics.

## Current State

Today:

- `WorkspaceStartupIntentAgentService` exists in the backend and frontend contract
- the create UI can submit `startup_intent.mode = "agent_service"`
- the backend bootstrap plan generator explicitly rejects it with `WORKSPACE_AGENT_SERVICE_UNAVAILABLE`
- kennel discovery already has a service kind for `agent_runtime`
- frontend list/detail/terminal surfaces can now present discovered services and readiness

That means the contract shape is already present. The missing work is the execution and discovery path.

## Guiding Decision

The first `agent_service` implementation should be profile-based and backend-owned.

That means:

- frontend submits an `agent_profile`
- backend resolves that profile into install/start steps and discovery metadata
- kennel executes those steps as a normal structured bootstrap plan
- backend projects the resulting runtime as a discovered `agent_runtime` service

This should stay intentionally narrow in the first slice. We do not need a generalized agent marketplace or arbitrary operator shell input to make this useful.

## First-Pass Goal

Enable one or more backend-defined `agent_service` profiles that:

- install or prepare the required runtime tools
- start a long-running agent process in the workspace
- emit a discoverable runtime manifest
- project as a `WorkspaceServiceSummary(kind="agent_runtime")`

The ideal outcome is that a workspace can say:

- this agent runtime was requested
- this process was started
- this runtime is pending, ready, failed, or unknown
- this is the endpoint or connection model the rest of the platform should understand

## Scope

This pass should implement:

- backend support for `agent_service` startup profiles
- backend-generated plan steps for agent install/start
- kennel execution support where needed for agent runtime metadata
- kennel discovery of agent runtime services
- backend projection of the resulting runtime as a discovered service
- frontend visibility for agent runtime readiness in the existing panels

This pass should not yet implement:

- arbitrary user-provided agent startup commands
- full room/workspace connection issuance
- final room authorization policy
- final `shadow_repo` execution semantics
- a permanent profile catalog API unless it becomes necessary during the slice

## Recommended First Profiles

The first slice should prefer profiles that are operationally legible and already meaningful in the product context.

Recommended first-pass profiles:

- `codex`
- `claude_code`
- `hermes`

Important note:

- these names should be treated as backend-controlled profile ids
- the actual install and startup commands can evolve without changing the frontend contract

## Contract Shape

No new top-level workspace create field is needed for this slice.

We should continue using:

```ts
startup_intent: { mode: "agent_service"; agent_profile: string }
```

What does need to become more explicit is the backend plan output and discovery semantics.

### Backend Plan Expectations

For agent profiles, the generated plan should be able to express:

- optional install preparation
- optional env var wiring
- long-running background runtime startup
- service metadata that discovery can later recognize

The current linear plan is sufficient if we add a small amount of runtime-specific metadata to the background startup step or to the generated service manifest.

### Discovery Expectations

An `agent_service` startup should eventually project something like:

```ts
{
  id: "codex",
  kind: "agent_runtime",
  label: "Codex Runtime",
  status: "pending" | "ready" | "failed" | "unknown",
  source: "bootstrap_profile",
  url: string | null,
  readiness_message: string | null
}
```

The endpoint may be a local HTTP/WebSocket service or a “process ready, endpoint not yet surfaced” runtime. The important point is that the runtime is represented explicitly instead of disappearing into generic bootstrap progress.

## Implementation Steps

### Step 1: Backend Profile Registry And Plan Generation

Files:

- `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- `/home/josep/dog/backend/app/tests/services/test_workspace_bootstrap_service.py`

Changes:

- add a backend-controlled `AGENT_SERVICE_PROFILES` registry
- map supported `agent_profile` ids to install/start behavior
- stop rejecting supported `agent_service` profiles
- keep unsupported profiles explicit with a structured validation error

Definition of done:

- `generate_bootstrap_plan()` can produce start plans for the first supported profile set:
  - `codex`
  - `claude_code`
  - `hermes`

### Step 2: Kennel Manifest And Runtime Discovery

Files:

- `/home/josep/dog/kennel/src/server.py`

Changes:

- ensure background startup steps for agent profiles emit a service manifest with:
  - `kind = "agent_runtime"`
  - stable `id`
  - human-readable `label`
  - any known process or endpoint hints
- update discovery logic so agent runtime services participate in the same readiness model as web services where possible

Status:

- implemented for the kennel discovery slice
- kennel now recognizes `codex`, `claude_code`, and `hermes` as declared `agent_runtime` services
- `GET /envs/{name}/services` now returns those runtimes with stable ids and human-readable labels
- for portless agent runtimes, a live process now projects as `ready` rather than remaining permanently `pending`
- endpoint publishing is still intentionally open-ended: the current discovery contract can represent an agent runtime cleanly even when no browser-facing URL exists

Definition of done:

- kennel `GET /envs/{name}/services` can return an `agent_runtime` entry for a workspace that started an agent profile

### Step 3: Backend Workspace Projection And Readiness

Files:

- `/home/josep/dog/backend/app/services/workspace_service.py`

Changes:

- no new top-level contract fields should be required if the discovered service shape is already sufficient
- ensure readiness summaries remain sensible when the primary runtime is an `agent_runtime`
- ensure fallback declared-service behavior includes agent runtime descriptors when live discovery is temporarily unavailable

Status:

- implemented for the current backend projection slice
- declared `agent_runtime` services now fall back to `unknown` in `ready` workspaces when live discovery is unavailable, which is more accurate than implying a port-based service is still merely pending
- readiness evaluation now treats discovered `agent_runtime` services as first-class runtime signals instead of only counting port-oriented web services
- focused service-layer unit coverage was added for the new fallback and readiness behavior
- local pytest execution for that file is currently blocked by a missing host dependency: `pytest_asyncio`

Definition of done:

- workspace detail/list responses expose the agent runtime through `services` and `connectivity_summary`

### Step 4: Frontend Visibility And Affordances

Files:

- `/home/josep/dog/frontend/src/services/workspaceService.ts`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx`

Changes:

- surface supported agent profile options clearly in create flows
- label discovered `agent_runtime` services distinctly from general web apps
- keep the readiness messaging legible when there is no browser URL but the agent process is still a real runtime surface

Status:

- implemented for the current frontend slice
- workspace create now exposes `agent_service` as a startup mode with the current supported profile set:
  - `codex`
  - `claude_code`
  - `hermes`
- list, detail, and terminal surfaces now distinguish agent runtimes from browser-oriented web services
- the UI now explains that an agent runtime may be healthy and discoverable even when it does not publish a browser-facing endpoint

Definition of done:

- an operator can request an agent runtime and understand whether it started successfully from the normal workspace UI

### Step 5: Runtime Consumption Alignment

Files:

- `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- `/home/josep/dog/backend/app/services/workspace_platform_service_access.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`

Changes:

- materialize projected platform-service access into agent-runtime launch context
- export stable agent-facing aliases for the projected platform-service variables
- write a runtime-local services JSON file for active process consumption and
  operator inspection

Status:

- implemented for the first alignment slice
- current agent runtime profiles now actively consume projected
  `DOG_AGENT_PLATFORM_*` variables during launch
- launchers now export stable runtime-facing aliases such as:
  - `DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_JSON`
  - `DOG_WORKSPACE_AGENT_PLATFORM_SERVICES_PATH`
  - `DOG_WORKSPACE_AGENT_AFFORDANCE_URL`
  - `DOG_WORKSPACE_AGENT_STORY_URL`
- launchers now materialize a runtime-local services file at:
  - `~/.dog/agent-runtime/platform-services.json`

Definition of done:

- the first agent runtime profiles receive projected platform-service access in a
  runtime-facing form without additional operator wiring

## Sequencing Read

This slice still belongs in Track 2, and it is a good precursor to Tracks 3 and 4.

Why:

- Track 3 benefits from workspaces that can expose real runtime purpose beyond “terminal only”
- Track 4 benefits from an explicit `agent_runtime` service kind before room/workspace trust and connection descriptors are finalized

So this is not sequencing drift. It is a productive deepening of Track 2 that should make the later relationship and connectivity work more concrete.

## Recommendation

The first coding step should be Step 1:

- implement a small backend-owned `agent_service` registry
- support one profile end to end before widening the matrix
- verify that the generated plan remains inspectable and easy to extend

If that lands cleanly, the next step is kennel discovery, then backend projection, then frontend affordances.
