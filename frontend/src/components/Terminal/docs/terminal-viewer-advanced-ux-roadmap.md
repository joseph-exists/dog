# Terminal Viewer Advanced UX Roadmap

Source of truth:

- [terminal-viewer-control-plane.md](/home/josep/dog/frontend/src/components/Terminal/docs/terminal-viewer-control-plane.md)

This roadmap converts the current control-plane reference into a sequenced implementation plan for a significantly more advanced user terminal experience.

The guiding direction for this plan is explicit:

- xterm becomes an active input surface
- capabilities are promoted from the hook and consumed by viewer chrome
- shell-like interaction becomes the default live experience
- operational metadata moves out of the main terminal interaction surface and into an adjacent tab
- terminal transport, viewer, and workspace-specific operational concerns stay clearly separated

## Purpose

The current terminal stack is structurally sound, but the user experience is still a hybrid:

- xterm renders output
- a separate text field captures input
- workspace operational metadata is mixed into the same panel as the main interaction surface


This roadmap defines the next major evolution:

- keep the control plane explicit and maintainable
- improve extensibility while maintaining a separation of concerns between UI affordances and transport ownership

## Guiding Decisions

### 1. xterm as primary live interaction surface in Terminal Viewer.

The current line-input field is a transitional affordance.

The target state is:

- click or focus the terminal
- type directly into the terminal
- paste directly into the terminal
- send shell input without routing through a separate form field

### 2. Transport capabilities should be explicit and authoritative

The hook should become the single source of truth for what the terminal client can do.

UI controls should not assume:

- input is always supported
- resize is supported
- paste is supported
- reconnect is equivalent to endpoint refresh

### 3. Interaction chrome and operational metadata are separate concerns

The main terminal tab should prioritize:

- shell interaction
- connection state
- immediate recovery controls

Operational metadata will be migrated to an adjacent tab:

- bootstrap state
- workspace access explanation
- discovered services
- runtime readiness
- endpoint descriptors

### 4. Transcript mode remains document-oriented


Transcript mode remains valuable for:

- readable replay
- copy/debug workflows
- saved output excerpts

The live tab and transcript tab coexist.

## Target UX Shape

The target terminal panel should have at least the following three adjacent tabs:

1. `Live`
   Interactive xterm surface with direct typing, paste, and shell-like focus behavior.

2. `Transcript`
   Read-only document-oriented replay of the current session buffer.

3. `Runtime`
   Workspace-specific operational metadata, readiness, service status, and access explanation.

That separation clarifies the three distinct concerns:

- terminal interaction
- terminal replay/documentation
- workspace operations and diagnostics

## Current State Summary

Today:

- `useTerminalSession` owns websocket transport and basic session state
- `TerminalViewer` mounts xterm in read-only mode
- `TerminalPanel` adds toolbar, transcript toggle, status bar, and a separate line-input form
- `WorkspaceTerminalPanel` wraps `TerminalPanel` and injects a large amount of workspace metadata

Main limitations:

- xterm is not an input surface
- resize and other user-capabilities are not wired
- capability reporting is thin
- reconnect semantics need extension and curation
- difficult for users to specify configuration or usability parameters

## Sequenced Implementation Plan

### Phase 1: Control-Plane Clarification

Goal:

- make capabilities explicit and separable before changing the UX deeply

Files:

- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)
- [terminalSessionService.ts](/home/josep/dog/frontend/src/services/terminalSessionService.ts)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)

Changes:

- formalize a `TerminalCapabilities` type
- expand the hook to report capabilities such as:
  - `sendInput`
  - `sendResize`
  - `directInput`
  - `paste`
  - `reconnect`
  - `transcript`
- distinguish connection actions from endpoint actions
- make reconnect semantics explicit in the hook 
- model input mode explicitly:
  - `line`
  - `direct`

Definition of done:

- `TerminalPanel` and future viewer chrome can render from hook capabilities instead of assumptions
- control labels can distinguish:
  - reconnect socket
  - request fresh terminal endpoint

### Phase 2: Active xterm Input Surface

Goal:

- make xterm the primary live input surface for TerminalViewer.

Files:

- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)

Changes:

- remove `disableStdin: true` for interactive live mode
- bind xterm keyboard data events to `sendInput`
- support focus/click-to-type behavior
- support direct paste into xterm
- keep transcript mode unchanged
- preserve a fallback line-input mode only where capabilities or environment constraints require it

Important constraint:

- direct input belongs in the viewer layer, but transport still belongs in the hook

Definition of done:

- a user can click into the live terminal and type shell input directly
- shell interaction no longer requires the external line-input field in the default path
- fallback behavior remains possible where direct input is disabled

### Phase 3: Resize And Viewport Negotiation

Goal:

- make the live terminal behave more like a real shell viewport

Files:

- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)
- backend/kennel terminal websocket handling if resize frames need transport support

Changes:

- introduce xterm fit behavior
- observe host container size changes
- propagate viewport dimensions through `setViewport`
- wire resize transport if kennel/websocket protocol can support it
- gate resize affordances behind hook capabilities

Definition of done:

- the terminal viewport tracks its container
- status bar and viewer both reflect real viewport state
- if resize transport is unsupported, the UI says so honestly and degrades gracefully

### Phase 4: Terminal Preferences And Viewer Configuration

Goal:

- expose meaningful viewer customization without destabilizing transport

Files:

- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)

Changes:

- introduce a `TerminalViewerPreferences` shape
- move hard-coded xterm options behind that preference object
- first-pass configurable concerns:
  - font size
  - line height
  - wrap mode
  - auto-scroll
  - scrollback depth
  - viewer theme preset
  - status bar visibility
- keep websocket ownership and transport behavior non-configurable at the caller level

Definition of done:

- viewer behavior is configurable through explicit preferences
- future user persistence can build on stable prop contracts rather than one-off edits

### Phase 5: Adjacent Runtime Metadata Tab

Goal:

- separate workspace operations/diagnostics from terminal interaction

Files:

- [WorkspaceTerminalPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)

Changes:

- remove large operational metadata blocks from the main live interaction surface
- create adjacent tabs for:
  - `Live`
  - `Transcript`
  - `Runtime`
- move these sections into the `Runtime` tab:
  - workspace status / terminal status / access summary
  - bootstrap failure and progress messaging
  - started services
  - agent runtime status
  - discovered services
  - terminal descriptor details

Definition of done:

- the Live tab is focused on terminal interaction
- transcript remains easy to access
- workspace diagnostics remain available without competing with typing/focus

### Phase 6: Recovery UX And Endpoint Semantics

Goal:

- make failure and recovery flows legible

Files:

- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)
- [WorkspaceTerminalPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx)
- [useWorkspaceTerminal.ts](/home/josep/dog/frontend/src/hooks/useWorkspaceTerminal.ts)

Changes:

- distinguish:
  - socket disconnected
  - endpoint expired
  - endpoint unavailable
  - terminal not allowed
- separate actions:
  - reconnect current websocket
  - request fresh terminal endpoint
- improve empty/error state copy around those branches
- reflect terminal descriptor freshness in the Runtime tab

Definition of done:

- users can tell whether they need to reconnect or request a fresh endpoint
- failure states no longer collapse into one generic terminal error banner

### Phase 7: Shell-Like Interaction Refinement

Goal:

- close the gap between “active xterm input” and a genuinely usable shell experience

Files:

- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [TerminalToolbar.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalToolbar.tsx)
- [TerminalStatusBar.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalStatusBar.tsx)

Changes:

- improve focus-ring and active-session affordances
- support paste shortcuts and explicit paste action where useful
- add optional copy-visible-buffer action
- improve keyboard handling around modifier keys and browser conflicts
- consider a compact command palette for terminal actions rather than only icon buttons

Definition of done:

- the terminal feels credible as a shell interaction surface
- the toolbar complements interaction rather than substituting for it

### Phase 8: Transcript Quality And Durable Session UX

Goal:

- improve replay quality without conflating replay and live emulation

Files:

- [terminalSessionService.ts](/home/josep/dog/frontend/src/services/terminalSessionService.ts)
- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)

Changes:

- improve transcript segmentation and labeling
- make transcript truncation more legible
- optionally distinguish input vs output in transcript rendering
- consider export/copy affordances for transcript slices
- preserve the current architectural split:
  - live emulator for interaction
  - document-oriented transcript for replay

Definition of done:

- transcript mode is more useful for debugging and documentation
- transcript quality improves without requiring a redesign of the live control plane

## Capability Promotion Model

This is the key control-plane shift for the roadmap.

The hook should become authoritative for capability negotiation, and the UI should become a consumer of that contract.

Suggested shape:

```ts
type TerminalCapabilities = {
  connect: boolean
  reconnect: boolean
  disconnect: boolean
  sendInput: boolean
  directInput: boolean
  paste: boolean
  sendResize: boolean
  transcript: boolean
  clearBuffer: boolean
}
```

Usage rule:

- the hook declares what is possible
- the viewer consumes input-related capabilities
- the toolbar consumes connection/recovery capabilities
- the workspace wrapper consumes terminal-endpoint and workspace-operation capabilities

## Separation of Concerns After The Migration

Target ownership model:

### `useTerminalSession`

Owns:

- websocket transport
- connection lifecycle
- capability reporting
- terminal session state
- input and resize send semantics

### `TerminalViewer`

Owns:

- xterm lifecycle
- active input surface behavior
- transcript rendering
- viewer preferences

### `TerminalPanel`

Owns:

- viewer composition
- mode tabs for `Live` and `Transcript`
- terminal interaction toolbar
- terminal status bar
- endpoint refresh affordances when present

### `WorkspaceTerminalPanel`

Owns:

- workspace-specific `Runtime` tab
- access and readiness explanation
- runtime/service/diagnostic presentation

This is the cleanest path to richer UX without collapsing the terminal into a workspace-only special case.

## Recommended Execution Order

Recommended order:

1. Phase 1 first, because capability promotion stabilizes the rest of the work.
2. Phase 2 second, because active xterm input is the highest-value UX shift.
3. Phase 3 third, because resize support should follow direct interaction.
4. Phase 4 fourth, because preferences are safer once the active viewer contract exists.
5. Phase 5 fifth, because metadata separation becomes clearer after the live surface is credible.
6. Phase 6 sixth, because recovery semantics are easier to explain after the tab split is in place.
7. Phase 7 seventh, because shell polish should refine a stable interaction model.
8. Phase 8 last, because transcript quality should evolve without blocking the live interaction improvements.

## Definition Of Success

We should consider this roadmap successful when:

- users type directly into the terminal surface by default
- the terminal UI reads from explicit capabilities rather than assumptions
- the main interaction surface is no longer crowded by workspace diagnostics
- operational metadata remains accessible in a neighboring tab
- transcript mode remains useful and distinct
- transport, viewer, and workspace concerns stay cleanly separated in code

## Source References

- [terminal-viewer-control-plane.md](/home/josep/dog/frontend/src/components/Terminal/docs/terminal-viewer-control-plane.md)
- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)
- [terminalSessionService.ts](/home/josep/dog/frontend/src/services/terminalSessionService.ts)
- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)
- [WorkspaceTerminalPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx)
