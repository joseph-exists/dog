# Workspaces Frontend Roadmap

> Scope: initial frontend slice for kennel-backed workspace provisioning and terminal access.
> Goal: establish a clear, testable top-level page model for local development and early user validation.

## Context

The backend now exposes a viable workspace lifecycle:

- create workspace
- poll workspace status
- request terminal URL when ready
- stop workspace
- destroy workspace

The frontend should meet that lifecycle with a page model that feels native to this codebase.

For this slice, we will intentionally prefer a feature-local structure over broad abstraction:

- borrow the route-orchestrator pattern from `Agents`
- borrow panel/shell ideas from `Page`
- keep the implementation specific to `Workspaces`
- extract shared patterns later only if the feature proves them out

## Product Shape

This slice should produce two top-level pages.

### 1. Workspaces Index Page

Route:

- `/_layout/workspaces`

Purpose:

- list existing user workspaces
- create a new workspace
- monitor provisioning progress
- navigate into a selected workspace

Primary user story:

- “I want to spin up an environment and see when it becomes available.”

### 2. Workspace Detail Page

Route:

- `/_layout/workspace.$workspaceId`

Purpose:

- operate a single workspace
- access its terminal
- inspect status and configuration
- stop or destroy it

Primary user story:

- “I want to enter and manage a live environment.”

## Route Design

We should follow the existing pattern used by `Agents`:

- route owns data loading, mutations, panel registry, and theme bindings
- shell owns structure, layout, and rendering
- panels stay focused on a single domain surface

### Route Responsibilities

`workspaces.tsx`

- fetch workspace list
- expose create mutation
- manage optimistic or transitional UI state for provisioning
- define index-page panel registry
- resolve page/cards themes

`workspace.$workspaceId.tsx`

- fetch single workspace detail
- poll while provisioning
- request terminal URL when appropriate
- expose stop/destroy actions
- define detail-page panel registry
- resolve page/cards themes

## Shell Design

The shell should be closer to `AgentsShell` than `PageShell`.

Why:

- this feature is panel-first, not block-editor-first
- we want a top-level operational surface, not a content composition tool
- the route/shell split in `Agents` is already close to what this page needs

### Proposed Shell Components

- `WorkspacesShell.tsx`
- `WorkspacesHeader.tsx`
- `WorkspacesLayout.tsx`

### Shell Responsibilities

`WorkspacesShell`

- outer page theme wrapper
- header composition
- cards theme wrapper
- handoff to layout

`WorkspacesHeader`

- page title and context
- create workspace action entry point
- optional theme selectors
- optional layout mode controls if we decide to support tabs/panels early

`WorkspacesLayout`

- render panel configuration
- place primary vs auxiliary panels
- stay simple and explicit in v1

## Panel Model

We should start with a small, feature-local panel set.

### Index Page Panels

- `workspace-list`
  Purpose: show all user workspaces, status, and entry actions

- `workspace-create`
  Purpose: create a new workspace with name/flavour/kind/repo/key/env input

- `workspace-help` (optional)
  Purpose: lightweight instructions for local dev and terminal expectations

- `workspace-activity` (optional)
  Purpose: later surface provisioning events or recent actions

### Detail Page Panels

- `workspace-terminal`
  Purpose: connect to and render the live terminal session

- `workspace-details`
  Purpose: show workspace metadata, status, flavour, kind, timestamps

- `workspace-controls`
  Purpose: stop, destroy, reconnect, copy terminal endpoint, etc.

- `workspace-debug` (optional, local/dev)
  Purpose: raw terminal URL, token timing, status transitions, useful errors

## Panel Layout Guidance

We should remain compatible in spirit with the panel layout system from `panel-layout-reference.md`, but we do not need to over-integrate on day one.

For this slice:

- use `PanelConfig[]`-style thinking at the shell/layout level
- keep the registry local to `Workspaces`
- avoid introducing full nested composition unless the page actually needs it

Suggested early layout defaults:

### `/_layout/workspaces`

- primary: `workspace-list`
- auxiliary: `workspace-create`

### `/_layout/workspace.$workspaceId`

- primary: `workspace-terminal`
- auxiliary: `workspace-details`
- auxiliary: `workspace-controls`

## Data and Service Layer

We should follow the service + hook + view model pattern already used across the frontend.

### Service

File:

- `frontend/src/services/workspaceService.ts`

Responsibilities:

- wrap generated API client methods
- transform raw API types into frontend-friendly view models
- centralize workspace-specific response shaping

### Hooks

Files:

- `frontend/src/hooks/useWorkspaces.ts`
- `frontend/src/hooks/useWorkspace.ts`
- `frontend/src/hooks/useWorkspaceTerminal.ts`

Responsibilities:

`useWorkspaces`

- fetch list of workspaces
- expose create mutation
- expose stop/destroy mutations if convenient for list row actions

`useWorkspace`

- fetch one workspace
- poll while status is `provisioning`
- expose refetch helpers

`useWorkspaceTerminal`

- fetch terminal descriptor from backend
- expose connection state for panel integration
- keep terminal transport concerns separated from UI rendering concerns

## Proposed View Models

We should not pass raw generated API types into components.

### `WorkspaceListItemViewModel`

Fields:

- `id`
- `name`
- `status`
- `flavour`
- `kind`
- `createdAt`
- `updatedAt`
- `hasTerminal`

### `WorkspaceDetailViewModel`

Fields:

- all core workspace identity fields
- normalized metadata
- derived flags such as:
  - `isProvisioning`
  - `isReady`
  - `canOpenTerminal`
  - `canStop`
  - `canDestroy`

### `WorkspaceTerminalDescriptor`

Fields:

- `terminalUrl`
- `protocol`
- `host`
- `isDirectConnection`

This last model is useful because the terminal layer is operationally unusual:

- browser connects directly to kennel
- websocket traffic is binary PTY stream data, not JSON

## API Surface We Expect to Consume

Index page:

- `GET /api/v1/workspaces/`
- `POST /api/v1/workspaces/`

Detail page:

- `GET /api/v1/workspaces/{workspace_id}`
- `GET /api/v1/workspaces/{workspace_id}/terminal`
- `POST /api/v1/workspaces/{workspace_id}/stop`
- `DELETE /api/v1/workspaces/{workspace_id}`

## Terminal UX Contract

The frontend must treat the terminal as a direct websocket client flow.

Implications:

- do not synthesize the websocket URL
- request it from the backend
- pass it directly into the terminal connection layer
- assume binary websocket frames
- avoid building the terminal panel around JSON message semantics

For local dev, this direct-connect model is desirable because it is fast and easy to reason about.

## Theme Strategy

This feature should follow the current page/cards theme pattern already present in `Agents`.

We do not need to invent a new theming mechanism here.

Suggested approach:

- context key for index page: `page:workspaces`
- context key for detail page: `page:workspace:{workspaceId}`
- page theme wraps header and page surface
- cards theme wraps panel content area

## First Implementation Pass

The first pass should aim for a thin, real vertical slice rather than polished completeness.

### Phase 1: Route + Service Skeleton

Create:

- `frontend/src/services/workspaceService.ts`
- `frontend/src/hooks/useWorkspaces.ts`
- `frontend/src/hooks/useWorkspace.ts`
- `frontend/src/routes/_layout/workspaces.tsx`
- `frontend/src/routes/_layout/workspace.$workspaceId.tsx`

Outcome:

- routes exist
- queries and mutations exist
- pages can render placeholder shells with real data

### Phase 2: Index Page Panels

Create:

- `WorkspacesShell.tsx`
- `WorkspacesHeader.tsx`
- `WorkspacesLayout.tsx`
- `panels/WorkspaceListPanel.tsx`
- `panels/WorkspaceCreatePanel.tsx`

Outcome:

- user can create a workspace
- user can observe provisioning state
- user can navigate into a workspace

### Phase 3: Detail Page Panels

Create:

- `panels/WorkspaceTerminalPanel.tsx`
- `panels/WorkspaceDetailsPanel.tsx`
- `panels/WorkspaceControlsPanel.tsx`
- `hooks/useWorkspaceTerminal.ts`

Outcome:

- user can open a ready workspace
- user can request terminal URL
- user can stop/destroy workspace

### Phase 4: Refinement

Possible additions:

- local debug panel
- theme selectors
- richer empty states
- helper copy for terminal connectivity expectations
- panel customization integration if the feature benefits from it

## File Touch List

Expected new files:

- `frontend/src/components/Workspaces/WorkspacesShell.tsx`
- `frontend/src/components/Workspaces/WorkspacesHeader.tsx`
- `frontend/src/components/Workspaces/WorkspacesLayout.tsx`
- `frontend/src/components/Workspaces/index.ts`
- `frontend/src/components/Workspaces/panels/WorkspaceListPanel.tsx`
- `frontend/src/components/Workspaces/panels/WorkspaceCreatePanel.tsx`
- `frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx`
- `frontend/src/components/Workspaces/panels/WorkspaceDetailsPanel.tsx`
- `frontend/src/components/Workspaces/panels/WorkspaceControlsPanel.tsx`
- `frontend/src/components/Workspaces/panels/index.ts`
- `frontend/src/routes/_layout/workspaces.tsx`
- `frontend/src/routes/_layout/workspace.$workspaceId.tsx`
- `frontend/src/services/workspaceService.ts`
- `frontend/src/hooks/useWorkspaces.ts`
- `frontend/src/hooks/useWorkspace.ts`
- `frontend/src/hooks/useWorkspaceTerminal.ts`

Possible touched existing files:

- route layout index exports if needed
- shared theme hooks if we need a new context key helper
- generated client usage sites only through service layer

## Risks and Deliberate Non-Goals

### Risks

- terminal panel complexity may expand once the actual terminal renderer is integrated
- direct websocket connectivity may be straightforward in local dev but more constrained in deployed environments
- polling behavior needs to feel responsive without becoming noisy

### Non-Goals for This Slice

- generalized page template integration
- full block-editor support
- universal panel composition abstraction
- backend-proxied terminal transport
- cross-entity panel system generalization beyond what the feature immediately needs

## Review Questions Before Coding

1. Do we want the first pass to include both routes, or should we land the index page first?
2. Should the first terminal panel be a thin connection scaffold, or should we immediately integrate the intended terminal UI library?
3. Do we want panel customization in v1, or should layout remain static until the operational flow is proven?
