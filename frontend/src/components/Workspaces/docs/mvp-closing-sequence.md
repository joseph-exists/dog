# MVP Closing Sequence

## Purpose

This artifact turns the current milestone state into the shortest high-leverage
implementation sequence that is likely to close the MVP with minimal churn.

It assumes:

- workspace lifecycle and readiness are explicit
- repo/bootstrap is real for the first operational slice
- project-aware sharing semantics are real
- room/workspace descriptor issuance and current connection state are real

The remaining work should now focus on finishing the cross-system trust and
service-access seams without overhardening temporary convenience layers.

## Ranked Sequence

### 1. Backend Descriptor Consumer Helpers

Why this is first:

- it unlocks direct chat-to-workspace and handler-driven room/workspace use
- it builds on the existing descriptor contract instead of bypassing it
- it avoids leaking frontend current-connection assumptions into backend room orchestration

Primary outcomes:

- backend helper(s) that:
  - resolve the room's current workspace connection
  - validate requested purpose/capability
  - return scoped endpoint descriptors for room handlers/tools
- first room-side consumer path for chat or runtime handlers

Primary interaction points:

- `/home/josep/dog/backend/app/services/room_workspace_connection_service.py`
- `/home/josep/dog/backend/app/services/agent_runner.py`
- `/home/josep/dog/backend/app/services/context_provider.py`
- room runtime / room tool surfaces that need a backend consumption seam

Anti-churn note:

- do not let this helper depend on frontend-only state
- do not let it assume one workspace per room forever

Status:

- implemented for the first backend consumer slice
- backend now exposes an internal room-scoped consumer helper that resolves the
  current workspace connection from backend truth
- room context now includes a normalized
  `system.room.workspace_connection.current` payload so agent/chat handlers can
  consume descriptor-backed workspace connection state without depending on
  frontend state

### 2. Token And Descriptor Hardening

Why this is second:

- the MVP already uses descriptors operationally
- the weakest remaining trust seam is token/endpoint lifecycle semantics
- this can be tightened without changing the room/workspace product surface dramatically

Primary outcomes:

- explicit short-lived auth mode semantics per endpoint kind
- better expiry and revocation behavior tied to current connection change/clear
- a clearer distinction between:
  - direct browser-openable service links
  - runtime/agent consumption credentials
  - future proxied or backend-mediated connections

Primary interaction points:

- `/home/josep/dog/backend/app/models.py`
- `/home/josep/dog/backend/app/services/room_workspace_connection_service.py`
- kennel-facing endpoint issuance paths where relevant
- frontend room/workspace consumers that surface expiry/scope

Anti-churn note:

- keep this additive
- avoid introducing a broad proxy abstraction unless a concrete service kind requires it

Status:

- implemented for the current hardening slice
- descriptors now carry:
  - `descriptor_id`
  - `issued_at`
  - `expires_at`
- current room/workspace connection records now carry a `connection_id`
- endpoint scope now ties descriptors back to:
  - room
  - workspace
  - purpose
  - endpoint
  - current connection
  - descriptor issuance
- frontend room surfaces now expose descriptor freshness and scope context rather
  than treating descriptors as timeless blobs

### 3. Workspace-To-Platform Service Access

Why this is third:

- it is the largest remaining functional delta against the milestone definition
- it completes the “other direction” of trust after room-to-workspace connectivity
- it should be built on the same capability/scoping vocabulary, not as a separate ad hoc path

Primary outcomes:

- a workspace or agent runtime can request access to named platform services
- access is explicit, scoped, and auditable
- websocket or service endpoints for platform calls become discoverable and intentional

Primary interaction points:

- backend service access / `mcpmvp` seams
- workspace bootstrap/runtime service registry
- agent runtime launch profiles and environment injection
- docs that define platform-service trust and capability grants

Anti-churn note:

- reuse the descriptor/capability model where possible
- do not fork into a separate trust language for workspace-to-platform access

Status:

- implemented for the first grant-and-inspection slice
- workspaces can now request explicit platform-service grants for
  `workspace_runtime` and `agent_runtime` consumers
- grants are backend-issued from the MCP service registry with:
  - scoped grant identity
  - issuance and expiry metadata
  - transport, approval, and capability metadata
- workspace detail UX now exposes this grant flow without hardcoding platform
  services in the frontend contract
- the next implementation decision for this slice is captured in:
  - [workspace-platform-service-access-decision.md](/home/josep/dog/frontend/src/components/Workspaces/docs/workspace-platform-service-access-decision.md)
- backend now also exposes the first canonical runtime-config path for
  workspace-side consumers through:
  - `POST /api/v1/workspaces/{workspace_id}/platform-runtime-config`
- workspace provisioning now projects canonical platform-service runtime config
  into workspace-side env vars for runtime consumption
- current agent runtime profiles now actively consume those projected variables
  through stable runtime-facing aliases and a materialized runtime services file
- workspace detail now lets operators inspect both projected runtime access and
  the current canonical runtime config
- runtime projections can now be refreshed for active workspaces, and the UI now
  signals expired projections and unavailable workspace states during runtime
  access workflows
- workspace detail now carries projection freshness, runtime file paths, and
  inject notes so operators can compare current config with runtime-facing
  materialization from one place
- room-held workspace connections now auto-refresh more intentionally as
  descriptors approach expiry, and room/runtime surfaces make expired or
  historical connections easier to understand and recover from

### 4. Repo/Bootstrap Completeness Gaps That Block Real Usage

Why this is fourth:

- Track 2 is already strong enough for the current slice
- the remaining gaps matter, but not all of them are equally leverageful
- this step should be selective and driven by real MVP blockers

Primary outcomes:

- decide whether `shadow_repo` is required for MVP
- improve `user_repo` materialization if the current bridge is too limiting
- tighten restart/recovery semantics for launched services and agent runtimes

Primary interaction points:

- `/home/josep/dog/backend/app/services/workspace_bootstrap_service.py`
- `/home/josep/dog/backend/app/services/workspace_service.py`
- `/home/josep/dog/kennel/src/server.py`
- frontend create/detail surfaces only where backend truth changes materially

Anti-churn note:

- do not broaden the bootstrap profile matrix just to make it feel complete
- close only the repo/bootstrap gaps that actually block the MVP workflow

### 5. Management And Classification Follow-Through

Why this is last:

- it matters for operator quality and system legibility
- but it is not the main blocker on the milestone's trust and execution path

Primary outcomes:

- tags, grouping, capability markers, and lightweight relationship management
- clearer operator surfaces for shared vs private vs project-bound workspaces

Primary interaction points:

- workspace list/detail service projections
- frontend workspaces panels and filters
- backend classification fields once they stop being provisional

Anti-churn note:

- avoid building polished management surfaces on top of still-moving trust semantics

## Recommendation

The next implementation energy should go into:

1. backend descriptor consumer helpers
2. token and descriptor hardening
3. workspace-to-platform service access

That is the shortest sequence that most directly closes the MVP definition while
keeping the current room/workspace convenience layer intentionally narrow.

## Guardrails

As the MVP closes, keep these boundaries explicit:

- descriptor issuance is canonical trust
- current room/workspace connection is a convenience default
- room/workspace many-to-many futures remain open
- bootstrap profiles remain backend-owned operational profiles, not final ontology
- metadata-backed bridges should keep graduating into typed contract space when they become central
