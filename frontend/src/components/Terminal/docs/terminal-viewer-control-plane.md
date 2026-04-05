# Terminal Viewer Control Plane

This note documents the current shared terminal stack used by Workspaces and other terminal-capable surfaces.

Its purpose is to replace older planning assumptions with the implementation we actually have today, and to make the extension seams explicit before more UX work lands.

Implementation roadmap derived from this note:

- [terminal-viewer-advanced-ux-roadmap.md](/home/josep/dog/frontend/src/components/Terminal/docs/terminal-viewer-advanced-ux-roadmap.md)

## Why This Exists

The current terminal experience is no longer a workspace-only scaffold.

We now have a shared terminal stack with:

- transport state in a hook
- session/document normalization in a service
- a live viewer and transcript viewer
- reusable panel and block wrappers
- workspace-specific metadata and access affordances wrapped around the shared primitives

That means future changes need a clear answer to:

- what is configurable today
- what is only configurable by code
- what is not supported yet
- where richer affordances should attach without destabilizing the transport path

## Current Component Stack

### 1. `useTerminalSession`

File:

- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)

Owns:

- direct websocket lifecycle
- raw frame decode
- local terminal session state
- send-input behavior
- clear / disconnect actions

Current public hook inputs:

- `url`
- `enabled`
- `maxFrames`
- `maxChars`

Current public hook outputs:

- `session`
- `status`
- `error`
- `connect()`
- `disconnect()`
- `clear()`
- `sendInput(data)`
- `setViewport(cols, rows)`
- `capabilities`

Important implementation facts:

- websocket ownership is centralized here
- terminal traffic is treated as raw text/binary PTY data, not JSON envelopes
- the hook reports `sendResize: false`
- `connect()` currently only bumps local state and does not force a new socket beyond the existing effect lifecycle

### 2. `terminalSessionService`

File:

- [terminalSessionService.ts](/home/josep/dog/frontend/src/services/terminalSessionService.ts)

Owns:

- session model
- frame model
- ANSI stripping for transcript readability
- bounded frame and character retention
- transcript adapter for `ContentRenderer`

Current durable session fields:

- `id`
- `url`
- `status`
- `connectedAt`
- `lastFrameAt`
- `frames`
- `plainText`
- `ansiChunks`
- `viewport`

Important implementation facts:

- transcript mode is derived from a normalized document, not from the live emulator instance
- raw ANSI chunks are preserved separately from stripped plain text
- retention is bounded by frame count and total plain-text characters

### 3. `TerminalViewer`

File:

- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)

Owns:

- xterm instance creation for live mode
- transcript rendering through `ContentRenderer`
- replay of accumulated ANSI chunks into xterm
- empty-state display

Current props:

- `session`
- `status`
- `mode`
- `autoScroll`
- `className`
- `emptyLabel`

Important implementation facts:

- live mode is read-only from xterm's point of view: `disableStdin: true`
- keyboard interaction does not happen through xterm itself
- input is sent through an external line input control
- xterm options are currently hard-coded in the component
- resize fitting is not wired in
- no xterm addons are currently mounted

### 4. `TerminalPanel`

File:

- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)

Owns:

- panel chrome
- live/transcript mode toggle
- connect / reconnect / disconnect / clear actions
- request-terminal action when provided
- line-input composer
- status bar placement

Current props:

- `title`
- `terminalUrl`
- `canRequestTerminal`
- `isRequestingTerminal`
- `terminalError`
- `onRequestTerminal`
- `metadata`
- `className`

Important implementation facts:

- this wrapper instantiates `useTerminalSession` directly
- line input is a plain text field outside the live terminal surface
- transcript/live mode is local component state
- the panel is reusable outside Workspaces when a raw terminal URL exists

### 5. `WorkspaceTerminalPanel`

File:

- [WorkspaceTerminalPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx)

Owns:

- workspace-specific metadata
- terminal access messaging
- bootstrap failure visibility
- runtime/service discovery summaries
- terminal descriptor visibility

Important implementation facts:

- it does not own websocket transport
- it does not own terminal rendering
- it is best understood as Workspaces-specific chrome around `TerminalPanel`

## What Is Configurable Today

There are two separate questions here:

1. what a caller can configure through props
2. what an engineer can configure by editing code without redesigning the architecture

### Caller-Level Configurability

Today callers can configure:

- whether the terminal surface is fed a URL at all
- whether request-terminal affordances are shown
- whether transcript or live mode is shown first in `TerminalBlock`
- viewer `autoScroll`
- viewer `emptyLabel`
- wrapper title and metadata surfaces

Today callers cannot configure:

- xterm theme
- font size
- font family
- line height
- scrollback depth
- keyboard-capture mode
- paste semantics
- resize semantics
- transcript retention
- toolbar action set

### Engineer-Level Configurability

Without changing the overall architecture, engineers can already change:

- frame retention limits in `useTerminalSession`
- transcript generation strategy in `terminalSessionService`
- xterm styling and basic options in `TerminalViewer`
- wrapper composition in `TerminalPanel` and `WorkspaceTerminalPanel`
- transport labels and status vocabulary

These are real extension seams, but they are code-only seams today, not user-facing affordances.

## What The UX Actually Is Today

The current UX is not a fully interactive terminal emulator in the conventional sense.

It is a hybrid surface:

- output is rendered in xterm for live viewing
- input is submitted as line-based text through a separate form control
- transcript mode is a document-style replay, not emulator replay

That gives us a stable operational path, but it also creates predictable UX friction:

- users may expect to type directly into the terminal canvas
- reconnect behavior is exposed, but connection state recovery is still fairly thin
- transcript and live mode are useful, but their relationship is not yet explained in-product
- the status bar is honest, but minimal
- terminal metadata in Workspaces is rich, while terminal interaction affordances are still sparse

## Current Capability Matrix

### Supported

- direct websocket connection to the terminal endpoint
- binary and text frame decoding
- bounded local session buffering
- read-only live terminal rendering
- transcript rendering through `ContentRenderer`
- line-based input send
- clear local session buffer
- disconnect and reconnect controls
- workspace-scoped metadata / readiness / service status display

### Partially Supported

- reconnect semantics
  The UI exposes reconnect, but the underlying hook does not yet model reconnection as a first-class connection strategy.
- viewport tracking
  The session model has a viewport field, but no resize transport is wired.
- transcript quality
  ANSI is stripped for readability, but richer replay fidelity is intentionally out of scope for the current implementation.

### Not Supported Yet

- direct keyboard capture into xterm
- terminal resize negotiation
- copy-mode semantics
- search within terminal output
- command history UI
- multi-line input composer
- theming knobs for end users
- persistence or export of transcript history beyond local session state
- pluggable toolbar actions
- per-user terminal preferences

## Main Control Plane Boundaries

This is the most important implementation truth to keep visible:

### Boundary 1. Transport Is Shared Infrastructure

The websocket lifecycle belongs to:

- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)

This layer should stay authoritative for:

- socket ownership
- frame decode
- transport status
- send semantics
- bounded buffering

UI components should not grow ad hoc socket logic around it.

### Boundary 2. Viewer Is Not The Input Surface

The xterm viewer currently renders output, but it is not the canonical input capture layer.

That means any UX proposal that assumes:

- shell-like key capture
- local prompt editing
- hotkey routing
- terminal-native paste

is a control-plane change, not just a styling change.

### Boundary 3. Workspace Metadata Is Separate From Terminal Mechanics

`WorkspaceTerminalPanel` includes:

- service readiness
- bootstrap status
- access explanations
- endpoint summaries

Those are valuable, but they are workspace chrome, not terminal engine behavior.

We should keep those concerns separate so the shared terminal primitives remain reusable.

## Where The Docs Drifted

The broader Workspaces docs still describe the terminal direction as if the main uncertainty were whether we would create a shared terminal foundation.

That is out of date.

What is true now:

- the shared foundation already exists
- the terminal is already composed across hook/service/viewer/panel layers
- the main uncertainty is affordance design and configurability policy, not whether to extract the terminal from Workspaces

## Recommended UX Affordance Tracks

These are the highest-signal next improvements if the goal is better user affordances without destabilizing the architecture.

### Track A. Make Interaction Model Explicit

Users should not have to infer whether they can type directly into the live terminal canvas.

Recommended additions:

- explain that live mode is output-first and input is line-based today
- label the input field more explicitly than "Send a line of terminal input"
- add a small note near the mode toggle clarifying the difference between `Live` and `Transcript`

### Track B. Expose Terminal Preferences At The Viewer Layer

The safest user-facing preferences are viewer-only and do not affect transport.

Good candidates:

- font size
- wrap on/off
- auto-scroll on/off
- transcript as default secondary mode
- status bar visibility

These should become props or a small viewer preferences object before they become persisted user settings.

### Track C. Clarify Session Recovery

Reconnect and request-terminal are both present, but they solve different problems.

Good affordances:

- distinguish "request a fresh endpoint" from "reconnect to current socket"
- surface whether the current terminal URL is stale vs merely disconnected
- show more explicit recovery guidance when the websocket closes

### Track D. Separate Operator Metadata From Interaction Chrome

The current workspace terminal panel mixes:

- terminal interaction
- runtime/service observability
- provisioning diagnostics

That is useful, but dense.

A likely next refinement is:

- keep `TerminalPanel` focused on interaction
- move some operational metadata into adjacent collapsible sections or tabs

This would improve usability without changing terminal transport at all.

### Track E. Decide Whether We Want True Direct Typing

This is the biggest branch point.

If we want:

- users to click into the terminal and type naturally
- shell-like interaction
- terminal-native paste and shortcuts

then we need to treat xterm as an active input surface and evolve the control plane accordingly.

That means work in:

- focus management
- keyboard routing
- paste handling
- resize support
- possibly xterm addons such as fit

This is a real capability expansion, not a copy tweak.

## Practical Extension Seams

If we want to evolve the current implementation cleanly, these are the best seams to use.

### Add A Terminal Preferences Object

Best home:

- `TerminalViewer`
- `TerminalPanel`

Suggested shape:

```ts
type TerminalViewerPreferences = {
  fontSize?: number
  wrap?: boolean
  autoScroll?: boolean
  showStatusBar?: boolean
  themeId?: string
}
```

This keeps viewer customization explicit and avoids scattering terminal options across ad hoc props.

### Add An Input Mode Concept

Best home:

- `TerminalPanel`

Suggested initial enum:

```ts
type TerminalInputMode = "line" | "direct"
```

Right now only `line` is implemented, but modeling the distinction would make the UX honest and prepare us for deeper interactivity later.

### Promote Capabilities From The Hook

Best home:

- `useTerminalSession`

Current capability surface:

- `sendInput: true`
- `sendResize: false`

This should become the contract the viewer and toolbar read from, rather than assuming everything is always available.

That would let us expose future affordances conditionally instead of overpromising.

## Immediate Documentation Recommendation

This document should become the canonical reference for:

- terminal control-plane ownership
- current configurability
- current UX limitations
- extension seams

The broader Workspaces planning docs should link here rather than carrying their own partial terminal architecture narratives forward.

## Source References

- [useTerminalSession.ts](/home/josep/dog/frontend/src/hooks/useTerminalSession.ts)
- [terminalSessionService.ts](/home/josep/dog/frontend/src/services/terminalSessionService.ts)
- [TerminalViewer.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalViewer.tsx)
- [TerminalPanel.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalPanel.tsx)
- [TerminalBlock.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalBlock.tsx)
- [TerminalStatusBar.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalStatusBar.tsx)
- [TerminalToolbar.tsx](/home/josep/dog/frontend/src/components/Terminal/TerminalToolbar.tsx)
- [WorkspaceTerminalPanel.tsx](/home/josep/dog/frontend/src/components/Workspaces/panels/WorkspaceTerminalPanel.tsx)
