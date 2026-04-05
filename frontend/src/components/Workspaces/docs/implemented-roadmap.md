# Workspaces Frontend Roadmap

> Scope: initial frontend slice for kennel-backed workspace provisioning and terminal access.
> Goal: establish a clear, testable top-level page model for local development and early user validation.

## Working Notes

This roadmap is intended to stay close to reality as the slice evolves.

- keep the plan legible and implementation-facing
- prefer explicit local structure over premature generalization
- update the artifact when reality changes in a meaningful way
- preserve rationale so the next pass can inherit decisions rather than rediscover them

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

## First Pass Outcome

The first pass was completed as a thin, real vertical slice rather than a polished terminal experience.

Implemented:

- route pair:
  - `/_layout/workspaces`
  - `/_layout/workspace.$workspaceId`
- service and hooks:
  - `workspaceService.ts`
  - `useWorkspaces.ts`
  - `useWorkspace.ts`
  - `useWorkspaceTerminal.ts`
- shell and panel layer:
  - `WorkspacesShell.tsx`
  - `WorkspacesHeader.tsx`
  - `WorkspacesLayout.tsx`
  - `WorkspaceListPanel.tsx`
  - `WorkspaceCreatePanel.tsx`
  - `WorkspaceDetailsPanel.tsx`
  - `WorkspaceControlsPanel.tsx`
  - `WorkspaceTerminalPanel.tsx`

Verified:

- routes compile and participate in the generated TanStack route tree
- list page can fetch and create workspaces
- detail page can fetch one workspace and poll while provisioning
- detail page can request the backend-issued terminal URL
- detail page can stop and destroy a workspace
- feature passes `npm run typecheck`

## Second Pass Outcome

The second pass established a shared terminal foundation instead of keeping terminal behavior locked inside the workspaces feature.

Implemented:

- shared transport/session layer:
  - `terminalSessionService.ts`
  - `useTerminalSession.ts`
- shared terminal primitives:
  - `TerminalViewer.tsx`
  - `TerminalPanel.tsx`
  - `TerminalBlock.tsx`
  - `TerminalStatusBar.tsx`
  - `TerminalToolbar.tsx`
- workspace integration:
  - `WorkspaceTerminalPanel.tsx` now wraps shared terminal primitives rather than owning terminal behavior directly

Verified:

- direct kennel websocket connection is owned by a shared hook
- terminal output is normalized into a reusable session document
- live and transcript viewing modes both exist
- transcript mode uses `ContentRenderer`, preserving the shared content/shiki path
- simple line input can be sent over the active websocket session
- feature still passes `npm run typecheck`

## What We Learned

### 1. The feature-local route and shell model was the right choice

The current implementation confirms the earlier instinct:

- `Agents` was the correct structural inspiration
- `PageShell` would have been too heavy for the first pass
- a local `PanelConfig[]` model was sufficient to get a real slice working

This should remain the default direction until the terminal experience itself starts demanding extraction.

### 2. The direct terminal flow is clean at the API boundary

The current backend contract is easy for the frontend to consume:

- request terminal descriptor from backend
- receive a direct websocket URL
- let the browser connect to kennel directly

That means the terminal problem is now mostly a frontend rendering and transport problem, not a backend contract problem.

### 3. Starting narrow on terminal UX was the right move

The earlier narrow panel let us validate the backend and route seams before we committed to a shared terminal design.

That made the current second pass cleaner because the transport/viewer split now grows out of confirmed behavior rather than speculation.

What it let us confirm:

- workspace readiness gating
- backend terminal request shape
- direct-connect assumptions
- route and panel ergonomics

We now have enough certainty to move the terminal into shared primitives without overcommitting to a full emulator yet.

### 4. Theme context is currently page-scoped, not workspace-instance-scoped

The implemented detail route uses a stable context key:

- `page:workspace`

rather than:

- `page:workspace:{workspaceId}`

This is acceptable for the first pass because it keeps the theme behavior simple and predictable. If users need per-workspace visual memory later, that can be added deliberately rather than accidentally.

### 5. The current complexity is terminal UX quality, not terminal plumbing

The transport and viewer foundation now exist. The next design problem is narrower:

- how far the live surface should go toward true terminal emulation
- how much ANSI fidelity we need in the near term
- how keyboard interaction should evolve beyond line-based input
- how customization should surface without destabilizing the transport layer

## Terminal Viewer Direction

Current canonical reference:

- [terminal-viewer-control-plane.md](/home/josep/dog/frontend/src/components/Terminal/docs/terminal-viewer-control-plane.md)

The terminal viewer should be treated as a composed capability with four layers:

1. `transport`
   Own the direct websocket connection to kennel and convert raw frames into a frontend-friendly event stream.

2. `document`
   Maintain a terminal session model that can support both live viewing and renderer-based replay.

3. `viewer`
   Render the session model in either panel or block form.

4. `chrome`
   Provide controls, metadata, layout, and customization surfaces around the viewer.

### Recommended Shape

Suggested new pieces:

- `frontend/src/services/terminalSessionService.ts`
- `frontend/src/hooks/useTerminalSession.ts`
- `frontend/src/components/Terminal/TerminalViewer.tsx`
- `frontend/src/components/Terminal/TerminalBlock.tsx`
- `frontend/src/components/Terminal/TerminalPanel.tsx`
- `frontend/src/components/Terminal/TerminalStatusBar.tsx`
- `frontend/src/components/Terminal/TerminalToolbar.tsx`

And then:

- `WorkspaceTerminalPanel` should become a workspaces-specific wrapper around shared terminal primitives

Status:

- implemented

## Terminal Transport Design

The existing websocket precedent in the app is `useRoomStream`.

We should borrow from it:

- lifecycle managed by a hook
- explicit connection state
- one hook owns the socket instance
- cleanup on unmount
- no UI component should instantiate `new WebSocket(...)` directly

We should not borrow its message semantics:

- room streams are JSON event envelopes
- kennel terminal traffic is raw PTY data

So the correct move is not “reuse `useRoomStream` directly,” but “reuse its ownership pattern.”

### Hook Contract

`useTerminalSession({ url, enabled })`

Responsibilities:

- open and close the websocket
- set `binaryType` deliberately
- accept text and binary frames
- normalize frames into terminal events
- expose connection status
- expose send helpers for input and reconnect
- keep a bounded local session buffer for replay/debug/customization

Current return shape:

- `status`: `idle | connecting | open | closed | error`
- `session`: terminal session state object
- `error`
- `connect()`
- `disconnect()`
- `sendInput(data)`
- `clear()`

Deferred:

- richer resize support
- paste-specific affordances
- keyboard-capture mode

## Terminal Session Model

To support both a live emulator and renderer-based display, the terminal should not only keep a mutable emulator instance. It should also keep a lightweight session document.

Suggested session model:

- `id`
- `url`
- `status`
- `connectedAt`
- `lastFrameAt`
- `frames`
- `plainText`
- `ansiChunks`
- `viewport`

The important point is that live transport and rendered content should not be fused together.

That separation lets us:

- render a terminal interactively
- expose a read-only transcript block
- pass terminal content through `ContentRenderer` when helpful
- support future persistence or replay without redesigning the terminal surface

## ContentRenderer and Shiki Integration

The current `ContentRenderer` stack is strong for durable content and code-like artifacts. It is not, by itself, a terminal emulator.

So the right integration point is selective, not total.

### Use ContentRenderer For

- terminal transcript snapshots
- copied command/output segments
- debug views of recent terminal frames
- read-only block renderings of terminal sessions
- code-oriented segments that benefit from Shiki highlighting

### Do Not Force ContentRenderer To Be

- the live cursor surface
- the keystroke/input transport layer
- the primary VT/ANSI state machine

That means the terminal viewer should have two coordinated rendering modes:

1. `live`
   A dedicated terminal surface for active interaction.

2. `document`
   A `ContentRenderer`-friendly representation for replay, excerpts, saved outputs, and composition inside other surfaces.

### Practical Integration Shape

Use a terminal content adapter, not a renderer fork.

Suggested adapter shape:

- `toTerminalTranscriptContent(session)`
- output `Content` with:
  - `format: "code"` for plain transcript slices, or
  - `format: "markdown"` / `format: "text"` for structured summaries

Shiki remains useful where it already shines:

- syntax-highlighted command snippets
- saved scripts
- transcript excerpts that are meaningfully code-like

## Panel Primitive and Block Primitive

The terminal should exist in two reusable forms built on the same viewer core.

### Terminal Panel Primitive

Purpose:

- operational, live, interactive

Recommended wrapper:

- card or panel shell
- toolbar
- connection status
- resize and reconnect controls
- workspace-specific actions nearby

### Terminal Block Primitive

Purpose:

- embeddable, composable, optionally read-only

Recommended wrapper:

- `BlockContainer`
- shared `TerminalViewer` inside
- optional transcript mode instead of live mode
- suited for `Page`/document contexts later without redoing the core viewer

This gives us the flexibility you asked for:

- one terminal engine
- two presentation wrappers
- no need to choose between panels and blocks up front

## Customization Strategy

Customization should be layered around the shared viewer, not baked into transport.

Suggested customizable concerns:

- density
- chrome visibility
- transcript vs live mode
- line wrap preference
- font size
- theme preset
- status bar visibility
- helper overlays

Suggested non-customizable core concerns:

- websocket URL sourcing
- websocket ownership
- frame decoding
- readiness gating

This keeps customization fluid for users without letting the operational contract drift.

## Revised Next Phases

### Phase 5: Shared Terminal Foundation

Create:

- `terminalSessionService.ts`
- `useTerminalSession.ts`
- shared terminal state/types

Outcome:

- direct kennel websocket is managed through one reusable transport hook
- workspace feature no longer treats terminal access as a URL-only scaffold

Status:

- completed

### Phase 6: Shared Terminal Viewer

Create:

- `TerminalViewer.tsx`
- `TerminalPanel.tsx`
- `TerminalBlock.tsx`

Outcome:

- one viewer core can serve both panel and block use
- workspace detail page upgrades cleanly

Status:

- completed in initial form

### Phase 7: Terminal Interaction Refinement

Focus:

- improve live interaction beyond single-line send
- evaluate keyboard capture and focus behavior
- decide whether resize semantics are available and worth supporting
- improve terminal status and recovery UX

Outcome:

- the terminal becomes more usable without changing the shared architecture

### Phase 8: ANSI Fidelity and Durable Transcript Quality

Focus:

- improve handling of ANSI control sequences
- decide whether to introduce a dedicated emulator layer later
- refine transcript adapters for better replay/debug readability

Outcome:

- terminal output quality improves while preserving the current shared viewer contract

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
