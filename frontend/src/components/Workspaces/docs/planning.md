# Workspaces Planning

## Primary Next Collective Milestone

A user is able to:

- provision an instance with a repository
- install packages from that repository
- launch services on the instance, especially coding agents such as Codex, Claude Code, or Hermes Agent
- associate that provisioned instance with a project
- launch a room with agents
- allow agents launched within the room to connect to services on that instance over websocket connections
- allow agents running on that provisioned instance to call instantiated platform services over websockets after access has been granted and authenticated, either through the backend or directly through `mcpmvp`

This milestone is not just a Workspaces UI milestone. It is a cross-stack operational milestone:

- workspace provisioning must become dependable
- workspace identity and ownership must become legible
- project and room relationships must become explicit
- websocket trust and routing paths must become coherent

The main goal of the next phase should be clarity of orientation, not breadth of features. We need the system to answer a small set of important questions cleanly:

- what a workspace is
- who can use it
- what it can connect to
- what platform objects it can belong to
- which layer owns each part of that truth

## Current Pressure

Operators need more management controls, and the frontend needs to reflect current state more accurately.

The application also needs to support:

- grouping and tagging of provisioned instances
- relationship management between instances
- differentiation between private/operator-only instances and project-enabled/team-usable instances
- deletion that remains faithful to kennel reality so the app does not retain deleted instances as stale local truth

Relationship management likely has two levels:

1. conceptual relatedness
   Example: "these systems are CUDA-enabled"

2. operational relatedness
   Example: "these systems belong to the same stack"

The first level looks appropriate for the near milestone. The second level is important, but can remain a stretch goal if command-line workflows can bridge it temporarily.

## Domain Contract Assessment

### What a workspace appears to be

A workspace is no longer just a temporary shell with a terminal URL. It is becoming a durable operational resource with:

- provisioner-backed lifecycle state
- ownership and access semantics
- optional project association
- optional repository/bootstrap configuration
- service endpoints
- websocket connectivity to rooms and platform services
- descriptive metadata for search, grouping, and policy

That means the next milestone needs a stronger domain contract than the current frontend-derived `isReady` / `canStop` style flags alone.

### Canonical workspace lifecycle states

The lifecycle should become explicit and backend-owned. The frontend should derive presentation from canonical state, not invent the state model locally.

Recommended near-term state set:

- `requested`
  Workspace creation was accepted but provisioning has not materially started.

- `provisioning`
  Infrastructure and bootstrap work are in progress.

- `starting`
  The workspace exists and is beginning service startup or agent bootstrap.

- `ready`
  The workspace can accept terminal access and declared services are available or expected to become available imminently.

- `stopping`
  Stop has been requested and the workspace is draining or shutting down.

- `stopped`
  The workspace still exists as a managed object, but its runtime is not active.

- `failed`
  Provisioning or startup did not complete successfully.

- `destroying`
  Destruction has been requested and the object should be treated as leaving the system.

- `destroyed`
  The backend should stop presenting the workspace as an active resource. In practice, list endpoints may omit this entirely once destruction completes.

### Allowed transitions

Recommended first-pass transitions:

- `requested -> provisioning`
- `provisioning -> starting`
- `provisioning -> failed`
- `starting -> ready`
- `starting -> failed`
- `ready -> stopping`
- `ready -> destroying`
- `stopping -> stopped`
- `stopping -> failed`
- `stopped -> starting`
- `stopped -> destroying`
- `failed -> destroying`
- `destroying -> destroyed`

This gives the UI and service layer a cleaner basis for:

- showing accurate controls
- explaining why an action is unavailable
- deciding when polling should continue
- deciding when terminal or service discovery is valid

### Domain fields that should become explicit

The next milestone likely needs the backend contract to expose, directly or through a service wrapper:

- workspace identity
  `id`, `name`, `owner`, `createdAt`, `updatedAt`

- runtime state
  canonical lifecycle state, last transition time, failure summary, stop reason if applicable

- topology and access
  project association, visibility mode, membership or ACL summary

- bootstrap intent
  repo source, repo kind, install command or bootstrap profile, requested agent/runtime profile

- connectivity
  terminal descriptor, declared service endpoints, room connectivity metadata, websocket capability descriptors

- classification
  tags, labels, capability markers such as CUDA/GPU, persistent/ephemeral, dev/test/research

The important point is not that every field must ship immediately. It is that the contract should be shaped around these concerns now so the next additions accumulate coherently.

## Likely Integration Targets

The next milestone should prioritize integration targets by dependency pressure, not by org chart or frontend/backend boundary.

### 1. Projects

This is the most important immediate integration after core workspace lifecycle.

Minimal contract:

- associate a workspace with zero or one project initially
- expose project identity on workspace detail and list surfaces
- define who can see and use the workspace once attached to a project
- support granting access to other users through project membership or explicit ACLs

Why it comes first:

- it clarifies whether a workspace is personal, shared, or project-bound
- it gives orientation to future rooms and service access decisions
- it helps prevent Workspaces from remaining an isolated operational island

### 2. Repos

Repo integration is part of the milestone itself, not a later enhancement.

Minimal contract:

- workspace creation can reference a repo source explicitly
- support both `user_repos` and `shadow_repos`
- expose repo association after provisioning
- clarify whether bootstrap/install is backend-managed, workspace-agent-managed, or operator-driven

Why it comes early:

- provisioning without repo/bootstrap truth will hide the real shape of failure
- repo source strongly influences startup commands, service launch, and agent placement

### 3. Rooms

Rooms are the first cross-system connectivity target that will test whether Workspaces is truly part of the platform.

Minimal contract:

- a room can reference a workspace as a reachable execution or service surface
- agents in a room can discover the approved websocket endpoints for that workspace
- the platform can represent whether the room-to-workspace path is available, pending, or denied

Why it matters:

- it turns the workspace from a terminal destination into a collaborative substrate
- it forces clearer thinking about trust, routing, and capability exposure

### 4. Service Access / MCPMVP

This is slightly later than Rooms in sequencing, but it is part of the same orientation.

Minimal contract:

- a workspace or agent can request access to named platform services
- access is granted through an explicit capability or token model
- websocket invocation paths are discoverable and auditable

Why it should not be left vague:

- this is one of the highest-risk seams in the milestone
- if service access stays implicit, both security and operator UX will become confusing quickly

### 5. Tags, Grouping, and Relationship Management

This should be treated as a first-class management concern, but it can follow after identity and access are clearer.

Minimal contract:

- assign tags and labels to workspaces
- filter and group by tags, capability markers, and project association
- optionally define lightweight workspace-to-workspace relationships

Why it is not first:

- tagging without strong identity, access, and lifecycle semantics produces a nice UI on top of ambiguous objects

## Responsibility Boundaries

The frontend should stay thin and legible. That does not mean “dumb”; it means the frontend should orchestrate and present, while backend and service boundaries own durable truth.

### Backend / service boundary should own

- canonical lifecycle state and allowed actions
- provisioning and bootstrap execution
- repo attachment semantics
- project association and access policy
- room/workspace connectivity descriptors
- service capability grants and websocket access descriptors
- deletion truth so removed workspaces disappear from authoritative list/detail responses

### Frontend should own

- route orchestration and query lifecycles
- panel composition and page structure
- derived presentation state from backend truth
- optimistic or transitional UI only where it improves operator clarity
- filtering, grouping, and local layout preferences

### Shared service layer should translate

- raw backend types into stable frontend view models
- lifecycle state into UI-friendly capabilities
- connectivity descriptors into terminal/session/service clients

## Recommended Orientation For The Next Milestone

The collective next milestone should be framed as:

## Track 4 Status

Track 4 now has the first two descriptor-consumption steps in place:

- room-aware workspace candidate selection
- room-side current descriptor-backed connection state
- descriptor-backed runtime consumption in room UX

That means room/workspace connectivity is no longer only an inspection path. The
room can now choose a relevant workspace, request a purpose-scoped descriptor,
hold that descriptor as the current session connection, and consume issued
endpoints from room runtime UX.

The next Track 4 pressure point is no longer “can we evaluate a descriptor?” It
is “what deeper trust, token, or transport hardening should sit behind the
descriptor-backed workflows that now exist?”

The next focused artifact for that work is:

- [room-workspace-current-connection-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-current-connection-roadmap.md)

That current-connection slice is now in progress through:

- backend current room/workspace connection routes
- backend-scoped descriptor endpoint metadata
- frontend hydration of current room connection state from backend truth

1. make the workspace domain explicit
2. make project/repo/room relationships real
3. make websocket trust and service discovery understandable

In practical terms, the next implementation goals should likely aim for:

- a clearer backend workspace contract with explicit lifecycle and relationship fields
- project association on the workspace model and UI
- repo-backed bootstrap semantics that are visible in both provisioning and detail views
- room/workspace connectivity descriptors rather than ad hoc websocket assumptions
- deletion and refresh behavior that faithfully mirrors kennel state

## Proposed Immediate Planning Questions

- What is the canonical source of truth for workspace lifecycle transitions and failure reasons?
- Is project association single-project in the next milestone, or do we need a broader relationship model immediately?
- What is the minimum repo/bootstrap contract needed to support agent launch on a fresh workspace?
- How should room-to-workspace websocket access be authorized and described?
- Which service-access capabilities must be explicit before `mcpmvp`-style direct access is safe enough to support?

## Four Implementation Tracks

These tracks are intended to be concrete enough to guide work allocation and sequencing, while still preserving the ability to move across frontend, backend, and kennel code whenever that is the most efficient place to resolve a problem.

The tracks are ordered by dependency pressure, not by team boundary.

### Track 1: Workspace Domain Contract And Lifecycle Truth

Purpose:

- replace the current thin workspace contract with a domain model that can support provisioning, bootstrap, sharing, and connectivity without forcing the frontend to infer too much

Why this goes first:

- the current backend model is still too small for the next milestone
- current status values in [models.py](/home/josep/dog/backend/app/models.py#L7264) only cover `provisioning`, `ready`, `stopping`, `stopped`, and `destroyed`
- current workspace routes in [workspaces.py](/home/josep/dog/backend/app/api/routes/workspaces.py) are owner-only and expose no relationship or access semantics
- current provisioning flow in [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py) collapses failure into `destroyed`, which will become misleading once workspaces are expected to be durable managed resources

Primary outcomes:

- explicit lifecycle states and allowed actions
- explicit failure state instead of overloading `destroyed`
- explicit workspace identity, classification, and relationship fields
- authoritative deletion behavior so list/detail views reflect kennel reality

Likely backend touchpoints:

- [models.py](/home/josep/dog/backend/app/models.py#L7264)
- [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [workspaces.py](/home/josep/dog/backend/app/api/routes/workspaces.py)
- new alembic migration for workspace schema changes
- kennel event integration if we want lifecycle transitions to reflect external signals rather than only request-local updates

Likely frontend touchpoints:

- [workspaceService.ts](/home/josep/dog/frontend/src/services/workspaceService.ts)
- [useWorkspaces.ts](/home/josep/dog/frontend/src/hooks/useWorkspaces.ts)
- [useWorkspace.ts](/home/josep/dog/frontend/src/hooks/useWorkspace.ts)
- [WorkspaceDetailsPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx)
- [WorkspaceControlsPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceControlsPanel.tsx)

Decisions this track should force:

- whether `requested`, `starting`, `failed`, and `destroying` become canonical states now
- whether deleted workspaces should disappear from list endpoints immediately or remain queryable for a short terminal state
- whether action availability is returned directly by backend or derived in the shared frontend service layer

Definition of done for this track:

- the frontend no longer needs to guess the important lifecycle semantics
- the backend can explain why a workspace is not usable
- failure, stop, destroy, and readiness all have distinct meanings

### Track 2: Repo-Backed Bootstrap And Runtime Intent

Purpose:

- make workspace provisioning mean more than “spawn a terminal”; it should carry repo, install, and runtime intent clearly enough to support agent launch and service startup

Why this is second:

- the milestone explicitly depends on repo-backed instance setup
- current provisioning already accepts `repo_url`, `ssh_pubkey`, and `env_vars`, but they are mostly passed through as injected config rather than represented as stable domain intent
- kennel already contains the bootstrap seam in [01-dev.sh](/home/josep/dog/kennel/provision/01-dev.sh), [00-base.sh](/home/josep/dog/kennel/provision/00-base.sh), and injection logic documented in [frontend-integration-reference-card.md](/home/josep/dog/kennel/frontend-integration-reference-card.md)

Primary outcomes:

- a clearer workspace bootstrap contract
- support for both `user_repos` and `shadow_repos`
- visible bootstrap progress and failure information
- explicit declaration of which services or agents should be started after repo setup

Likely backend and kennel touchpoints:

- [workspace_service.py](/home/josep/dog/backend/app/services/workspace_service.py)
- [kennel_client.py](/home/josep/dog/backend/app/services/kennel_client.py)
- [user-repo-frontend-reference.md](/home/josep/dog/backend/app/services/service-docs/user-repo-frontend-reference.md)
- [01-dev.sh](/home/josep/dog/kennel/provision/01-dev.sh)
- [00-base.sh](/home/josep/dog/kennel/provision/00-base.sh)
- any kennel injection or spawn scripts that own clone/install/start behavior

Likely frontend touchpoints:

- [WorkspaceCreatePanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx)
- [WorkspaceDetailsPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx)
- [workspaceService.ts](/home/josep/dog/frontend/src/services/workspaceService.ts)
- possible reuse of repo selection patterns from repo routes and services rather than freeform URL-only input

Decisions this track should force:

- whether the create flow references repos by platform resource id, raw source URL, or both
- whether install/start commands are backend-managed profiles, operator-supplied commands, or agent-managed bootstrap steps
- what counts as “ready”: terminal-ready only, or repo-and-service-ready

Definition of done for this track:

- a workspace can be provisioned with enough declared runtime intent to support the next milestone’s agent and service workflows
- the UI can show what bootstrap was requested, what happened, and where it failed

### Track 3: Project Association, Sharing, And Management Surface

Purpose:

- make workspaces part of the platform’s collaboration model rather than owner-only kennel objects

Why this is third:

- project association is one of the cleanest ways to turn private compute into shared platform infrastructure
- project APIs and resource attachment patterns already exist in [projects.py](/home/josep/dog/backend/app/api/routes/projects.py) and [crud_projects.py](/home/josep/dog/backend/app/crud_projects.py)
- the current workspace API remains single-owner in [workspaces.py](/home/josep/dog/backend/app/api/routes/workspaces.py), so this track is where ownership semantics start becoming platform semantics

Primary outcomes:

- workspace can be attached to a project
- visibility and access become understandable
- project-aware list/detail UI exists for workspaces
- operators can distinguish personal, shared, and project-enabled instances

Likely backend touchpoints:

- [projects.py](/home/josep/dog/backend/app/api/routes/projects.py)
- [crud_projects.py](/home/josep/dog/backend/app/crud_projects.py)
- workspace model and service updates to include project association or project-resource projection
- access-control surfaces if workspace visibility should derive from project membership

Likely frontend touchpoints:

- [projectsService.ts](/home/josep/dog/frontend/src/services/projectsService.ts)
- [workspaces.tsx](/home/josep/dog/frontend/src/routes/_layout/workspaces.tsx)
- [workspace.$workspaceId.tsx](/home/josep/dog/frontend/src/routes/_layout/workspace.$workspaceId.tsx)
- [WorkspaceListPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx)
- [WorkspaceDetailsPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx)

Decisions this track should force:

- whether project linkage is a field on `Workspace`, a `ProjectResource` attachment, or both
- whether one workspace can belong to multiple projects in the near term
- whether sharing is only project-mediated for now or also supports direct ACLs on workspaces

Definition of done for this track:

- the system can express “this workspace belongs to this project and these users can use it”
- the UI can distinguish ownership from project availability

### Track 4: Room Connectivity, Service Discovery, And Websocket Trust

Purpose:

- define how rooms, agents, and workspaces actually connect to one another once a workspace exists

Why this is fourth:

- it depends on the earlier tracks to clarify workspace identity, readiness, and access
- it is also the highest-risk integration seam because it mixes runtime discovery, websocket connectivity, and authorization
- room infrastructure already exists in [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py) and frontend room services such as [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts)

Primary outcomes:

- room-to-workspace connectivity descriptors
- explicit service endpoint and capability discovery
- authorization model for websocket access from agents and rooms
- clear distinction between direct terminal transport, room-mediated service transport, and future `mcpmvp` direct service calls

Likely backend touchpoints:

- [rooms.py](/home/josep/dog/backend/app/api/routes/rooms.py)
- room runtime routes and services
- workspace routes/services for endpoint discovery
- access control and token issuance for websocket-capable services
- kennel token and websocket issuance paths if room agents will connect directly

Likely frontend touchpoints:

- [roomService.ts](/home/josep/dog/frontend/src/services/roomService.ts)
- [roomRuntimeService.ts](/home/josep/dog/frontend/src/services/roomRuntimeService.ts)
- [useWorkspaceTerminal.ts](/home/josep/dog/frontend/src/hooks/useWorkspaceTerminal.ts)
- shared terminal/session primitives under [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)
- future room/workspace connection surfaces in both routes

Decisions this track should force:

- whether room agents receive backend-issued endpoint descriptors, backend-proxied websocket routes, or direct kennel/service routes with scoped credentials
- whether service discovery is represented as workspace metadata, a dedicated endpoint, or a room runtime contract
- how to separate terminal access from general service access so the security model stays legible

Definition of done for this track:

- an agent in a room can connect to an approved workspace-hosted service through a clear, auditable path
- a workspace-hosted agent can reach approved platform services through a similarly explicit path

## Sequencing Guidance

Recommended execution order:

1. Track 1 first, because it establishes domain truth.
2. Track 2 second, because repo/bootstrap intent is part of the milestone itself.
3. Track 3 third, because project association gives the workspace a real collaboration context.
4. Track 4 fourth, because connectivity and trust should be built on top of explicit identity, readiness, and access semantics.

Important caveat:

- these tracks are not walls
- if Track 2 reveals a missing lifecycle state, pause and return to Track 1
- if Track 4 reveals that project access is too vague, pause and return to Track 3
- if kennel bootstrap reality forces a better backend contract, move the change to the source rather than carrying compensating complexity in the frontend

## Suggested Immediate Deliverables

Before coding deeply across all four tracks, the next planning artifacts should probably be:

- a workspace domain contract draft with proposed API and model changes
- a repo/bootstrap contract draft covering `user_repos`, `shadow_repos`, and service launch intent
- a project/workspace relationship note choosing between direct field association and project-resource attachment
- a room/workspace connectivity note describing websocket endpoint discovery, token issuance, and trust boundaries

Current artifact:

- [workspace-domain-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-domain-contract.md)
- [domain-contract-implementation-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/domain-contract-implementation-roadmap.md)
- [repo-bootstrap-contract.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-contract.md)
- [repo-bootstrap-implementation-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-implementation-roadmap.md)
- [agent-service-runtime-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/agent-service-runtime-roadmap.md)
- [service-readiness-discovery-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/service-readiness-discovery-roadmap.md)
- [project-workspace-relationship.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-workspace-relationship.md)
- [project-management-access-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/project-management-access-roadmap.md)
- [room-workspace-connectivity.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-connectivity.md)
- [room-workspace-descriptor-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-descriptor-roadmap.md)

Track 1 status:

- Step 1 completed: backend workspace model and migration expanded for lifecycle truth
- Step 2 completed: backend service lifecycle transitions now use the richer status model and failure semantics
- Step 3 completed: backend routes now project the richer workspace contract and expose workspace start
- Step 4 completed: frontend service and hook alignment now consume the richer contract
- Step 5 completed: key list/detail/terminal surfaces now present the richer operational state

Sequencing review:

- the current sequencing still holds
- Track 1 did what it needed to do: it made workspace lifecycle, actions, and projected project context explicit enough that subsequent work has a stable operational base
- the main remaining ambiguity is no longer lifecycle truth; it is repo/bootstrap intent and readiness

Track 2 status:

- typed bootstrap intent, backend plan generation, kennel execution, and frontend bootstrap visibility are now in place
- service-readiness discovery is also now implemented through a coherent first pass:
  - kennel exposes per-workspace service discovery
  - backend projects discovered services, connectivity summary, and flavour health
  - frontend list, detail, and terminal surfaces show runtime readiness distinctly from bootstrap progress
- that means the system is now much clearer about a second important question:
  - not just what a workspace is
  - but what it appears to be running, and whether those services are becoming reachable

Current sequencing read:

- the broader ordering still holds
- Track 2 is now strong enough that the next decision can be made from a better foundation
- the likely next branch point is:
  - deepen Track 2 for additional runtime/service kinds such as `agent_service` or later `shadow_repo`, or
  - move into Track 3 and Track 4 work now that readiness, discovery, and projected project context are explicit enough to support relationship and trust decisions

Recommended next move:

- proceed to Track 2
- keep Track 1 open only for targeted cleanup discovered while implementing repo/bootstrap semantics
- begin Track 2 from the backend contract expansion and repo-source validation slice described in [repo-bootstrap-implementation-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/repo-bootstrap-implementation-roadmap.md)

Track 2 status:

- Step 1 completed: backend workspace create/detail contract now has typed bootstrap intent and progress
- Step 2 completed for the first slice: backend now validates and normalizes `external_url` and `user_repo`
- Step 3 completed for the current slice: backend now generates a structured bootstrap plan from typed intent
- Step 4 completed for the current slice: kennel inject now executes that structured plan and returns step-level results
- Step 5 partially completed: workspace provisioning now records generated plans and execution results in lifecycle metadata
- Step 6 completed for the current frontend slice: create, list, detail, and terminal surfaces now expose bootstrap intent and progress
- `user_repo` currently uses a documented bridge through `source_repo_url`, which preserves delivery velocity while keeping the design open for platform-native materialization later
- `shadow_repo` is recognized in the typed contract but intentionally deferred at execution time for now
- current install-profile support is intentionally small and backend-owned: `npm`, `pnpm`, `yarn`, `uv`, `pip`
- current startup-profile support is intentionally small and backend-owned: `vite`, `nextjs`, `fastapi`
- `agent_service` is now part of the active execution slice through a first backend-owned profile set:
  - `codex`
  - `claude_code`
  - `hermes`
- the current launcher commands remain intentionally overrideable while kennel manifest/discovery semantics are being shaped
- kennel manifest and discovery support for `agent_runtime` is now in place for that first profile set
- agent runtimes now project through readiness/discovery semantics that account for non-browser workloads instead of assuming every healthy service must look like a web app
- backend workspace projection and readiness semantics are now aligned for `agent_runtime` as well
- when live discovery is unavailable, declared agent runtimes now fall back to `unknown` rather than being misread as port-based pending services
- frontend affordances are now aligned too:
  - workspace create supports `agent_service` startup selection
  - list, detail, and terminal surfaces distinguish agent runtimes from ordinary web endpoints
  - the UI now explains that some runtime surfaces are process-backed rather than browser-backed
- frontend client/schema alignment is now caught up with the richer workspace bootstrap and readiness contract
- operator-facing kennel rebuild jobs are now relevant as flavour-health diagnostics, but they should remain secondary to explicit per-workspace runtime discovery
- service-readiness Step 1 is complete: backend models now express service summaries, connectivity summary, and flavour-health projection
- service-readiness Step 2 is complete for the first slice: kennel now exposes runtime service discovery for known startup profiles
- service-readiness Step 3 is complete for the current slice: backend workspace projection now exposes services, connectivity summary, richer readiness, and flavour-health context
- service-readiness Step 4 is complete for the current slice: frontend detail, list, and terminal surfaces now expose discovered services and connectivity state
- `agent_runtime` frontend visibility and affordances are now complete for the current slice, as scoped in [agent-service-runtime-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/agent-service-runtime-roadmap.md)

Sequencing review:

- the next most important work after the agent-runtime slice is Track 3, not Track 4
- the reason is straightforward: room/workspace trust wants shared project attachment to be real, not just projected
- that makes project/workspace relationship work the tighter dependency before broader room connectivity issuance

Track 3 status:

- first implementation slice is now in place
- canonical relationship remains `ProjectResource(resource_type="workspace", resource_id=<workspace_id>)`
- backend now enforces the near-term zero-or-one project rule for workspace attachment
- workspace detail now exposes attach/detach through the canonical project-resource path rather than inventing a second mechanism
- project/workspace relationship is therefore no longer only architectural intent; it is now becoming a real product affordance
- Track 3 Step 1 is now complete:
  - workspace list/detail visibility is no longer owner-only
  - project-attached workspaces can now be retrieved through the shared access-control path when the current user has project viewer access or higher
- Track 3 Step 2 is now complete:
  - backend `allowed_actions` is now actor-aware
  - project-derived viewers can receive use-oriented actions such as terminal and service discovery
  - destructive runtime operations remain owner-anchored in this slice
- Track 3 Step 3 is now complete:
  - frontend workspace view models now distinguish use-versus-manage semantics
  - workspace list/detail surfaces no longer assume that every visible workspace is owner-operated
  - owner-only affordances are now suppressed or disabled where the current slice still keeps management authority narrow
- Track 3 Step 4 is now complete for the main workspace surfaces:
  - shell copy, terminal, controls, project assignment, list, and detail panels now reflect the shared-workspace policy more consistently
  - the main remaining question is sequencing rather than semantic cleanup

Current next pending step:

- pause for sequencing review:
  - decide whether the next most valuable work is additional Track 3 management breadth
  - or a return to richer Track 4 descriptor behavior now that shared-workspace access semantics are explicit across backend and frontend

Track 4 status:

- the first backend descriptor slice is now in place
- `POST /api/v1/rooms/{room_id}/workspace-connections` now issues a backend-evaluated room/workspace descriptor
- the frontend client and shared room service layer now expose that descriptor route directly
- the room route now includes a lightweight `Workspace Links` inspector surface for live descriptor evaluation
- the current route evaluates:
  - caller room membership
  - shared-project or owner-private authorization
  - workspace lifecycle/connectability
  - purpose-specific discovered services
- current first-slice behavior is intentionally honest:
  - web-service purposes can return backend-issued descriptors derived from discovered container-routable URLs
  - `agent_runtime_connect` can now move to `available` when the runtime binds its canonical port and discovery sees a real container IP endpoint
  - process-healthy agent runtimes that have not yet published a network endpoint still remain explicitly `pending`
- the current frontend surface is intentionally small:
  - choose a workspace
  - choose `service_connect` or `agent_runtime_connect`
  - inspect live `available | pending | denied` status, capabilities, and endpoints

Concrete recommendation:

- the next Track 4 slice should move from descriptor inspection to descriptor consumption
- that recommendation is now captured in [room-workspace-descriptor-roadmap.md](/home/josep/dog/frontend/src/components/Workspaces/docs/room-workspace-descriptor-roadmap.md)
- the key next implementation sequence should be:
  - room-aware workspace candidate selection
  - room-side current connection state
  - descriptor-backed runtime/service consumption in room UX
- Track 4 Step 1 is now complete:
  - backend now exposes `GET /api/v1/rooms/{room_id}/workspace-candidates`
  - the room workspace panel now uses ranked room-aware candidates instead of a generic visible workspace list
