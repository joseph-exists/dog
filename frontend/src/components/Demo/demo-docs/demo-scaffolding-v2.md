# Demo Scaffolding Requirements
> **Status:** Planning artifact — working document, round 2 annotations  
> **Last updated:** 2025-02-20  
> **Purpose:** Map four demo surfaces against current Page/panel/block infrastructure. Identify gaps, composition requirements, and sequencing.

---

## Framing

The four demos are not independent exhibits. They are four projections of a single ontological claim: that the platform's morphism model works across creation method, display surface, and runtime modification. The Demo page's job is to make that claim legible to a viewer who may not arrive with the vocabulary to understand what they're seeing.

This document operates at two levels simultaneously:
- **Structural** — what panels/blocks/primitives are required
- **Compositional** — how those elements compose, and what PageShell needs to be able to hold

When crossing from one to the other, this document will signal explicitly.

@claude-note: After reading demo-eng-reference.md, the framing holds but the ground has shifted. A working Demo system already exists: `DemoPage`, `DemoHeader`, `DemoStoryPanel`, seed scripts, slug-based routing. The gap is not "build from zero" but "generalize an existing specific implementation." That's different work. The ontological claim about multiple creation methods is already partially proven — seed scripts are API-based, importable, and composable via `--json` piping. The DemoConfig backend migration is the next step proving it from the other direction. This changes the urgency gradient across the phases below.

---

## Shared Infrastructure Requirements (all four demos)

Before any demo-specific work, the following must be reliable:
@josep-note: changed PageShell to DemoShell

### DemoShell 
- Must support a `demo` entity type cleanly — `entity_type: "demo"`, `entity_id: "<slug or uuid>"`  @josep-note: correct.  added DemoShell.tsx, refactoring now. working through slug vs id issues. 
- Must handle panel-only layouts (no blocks) without layout thrash
- Must handle mixed layouts (blocks describing the demo + panels showing it)
- The `/demo` entry and `?id=` subpage routing pattern needs to resolve to DemoShell correctly 

@claude-note: **Naming collision: DemoShell vs DemoPage.** The eng reference has `DemoPage` as the existing orchestrator (`Route → DemoPage → DemoHeader + ResizablePanelGroup`). `DemoShell` is being added now. Before these diverge further, the relationship needs to be explicit:
- Option A: DemoShell *replaces* DemoPage - this is correct.  DemoShell is a hard refactor/iteration of DemoPage after lots of churn in the system since it was built.  DemoShell will use the new patterns for composition, inheritance, imports, and heirarchy.

@claude-note: **Routing pattern resolved.** Eng reference confirms slug-based routing (`/demo/$slug`), already working. The `?id=` subpage pattern from the original scaffolding was incorrect framing — open question 4 below is answered. Slug vs ID tension Josep notes is likely about the backend DemoConfig model (does slug serve as primary key or is it alongside UUID?) — worth a single explicit decision before the config migration lands.

@claude-note: **ResizablePanelGroup vs PanelContainer.** PanelContainer holds all ResizablePanelGroup objects.  RPG never exists outside of a PanelContainer (Old demos might reflect this, that's fine but should be cleaned up if/when we have the time. new demos should *not* use this pattern.)

### PanelContainer
- Must be stable under real panel content — this is the primary load-bearing primitive 
- Panel resize behavior needs to be predictable (not fight with panel content)
- Must support a "presentation mode" state where chrome (edit controls, toolbars) is hidden

@claude-note: The current DemoPage uses a hardcoded 60/40 split — two panels, fixed types (story left, chat right). The flexible panel composition this doc envisions (any panel in any slot) is aspirational and not yet implemented. This is probably the biggest structural gap between current state and the four-demo vision. The eng reference even acknowledges it explicitly under "Adding a Non-Story Demo" — replace the left panel content. The `panelType?: "story" | "custom"` extension to DemoConfig is the seed of this flexibility, but it's not built yet.

### Presentation / Theming 
@josep-note: theming at this level is a solved problem. we will integrate as a second-order part of the sequence when we've stabilized the surface. all of the following (and more) already exist, will be integrated at the appropriate time.
- Demo pages will need their own ambient theme — the demo surface should feel distinct from the app chrome 
- The full variable set (per REFERENCE.md) must be set on the demo page container
- Per-demo theming (each demo has its own visual identity) should compose cleanly via the existing specificity model

@claude-note: Confirmed — theming is a solved layer. Agree with Josep: second-order concern. The surface needs to stabilize before theming is wired in. No new gap here.

### New primitive needed: `DemoShell`
@josep-note: in progress. pending DemoConfig definition and implementation.
- Wraps a demo instance
- Sets ambient theme from demo's presentation data
- Provides the "entry" and "subpage" routing context
- There is no distinct DemoPage after this refactor.

Capability requirements of DemoShell:
- flexible panel slot composition, including:
- room, chat, story, canvas, ??
- toggles for state
- useEffect based runtime
- connection management (legacy DemoPage used old model, fine(?) for demos, but significantly awful compared to our rewritten websockets library... if we have to, then fine)
- DemoHeader, DemoLayout, Demo... etc
- block support for context/description blocks
- entity type aware routing

---

## Demo A: Multiplayer / Multi-LLM Chat Room

**Claim being demonstrated:** Multiple humans and multiple LLMs can share a real-time communication surface. Participants are legible — you can tell who is human and who is agent.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `ChatPanel` | exists, needs (visual/layout) refinement | Primary surface |
| `ParticipantPanel` | exists | Shows participant stack with agent/human distinction |

@claude-note: The current DemoPage already has chat on the right (40%) and story on the left (60%). For Demo A, chat *is* the primary surface — the story panel slot becomes either ParticipantPanel or something else. This is the first case where the hardcoded 60/40 layout fights us. Demo A needs chat dominant, not chat secondary.

### Blocks required
| Block | Status | Notes |
|---|---|---|
| A intro/description block | missing | Sets context for the viewer — "what am I looking at?" |
| Participant identity display | partial (`IdentityBlock` is person-centric) | Needs to handle agent identity presentation |
@josep-note: we will use the ParticipantsPanel - once we're set on it, we can theme/restyle/overload it however we need.

### Composition level
Two-panel layout: ChatPanel (primary, large) + ParticipantPanel (secondary, sidebar or collapsible). A description block above or alongside.
@todo : add mode prop to ChatPanel (`"participant" | "observer"`)

### Gaps
- `ParticipantPanel` needs to render agent presentation (emoji, accent color) not just user avatars
@todo add agent presentation flair back into ParticipantPanel

- The intro block needs to be a general-purpose `DescriptionBlock` or `ContextBlock`, not a person-bio block
@todo review ContextBlock

### Open question
Is Demo A best served as a live Room (join-able) or a replay? Both are valid. The answer changes whether we need real-time connection infrastructure or just playback.

@josep-note: both are present in the same component. we'll change the visual display as needed - these toggles are easy once we have the frame ready.  

@claude-note: **Resolved.** The WebSocket infrastructure is already live in DemoPage (the eng reference shows connection badge, WebSocket state). Demo A is live by default. The toggle Josep refers to is the auto-respond toggle already in DemoHeader. No new infrastructure needed.

---

## Demo B: Story Pause / Replayability

**Claim being demonstrated:** A story is a state machine. It can be paused, serialized, and resumed. The viewer can see this happen.

@claude-note: **This demo is mostly working.** The eng reference describes exactly this: `StoryPanel` with `RuntimeControls.tsx` (advance/rewind/reset), `DemoStoryPanel` watching `runtime.revision` via `useEffect`, synthetic messages triggering agent responses on state change. The enchanted library seed is the live demo of this. The gaps here are presentation and legibility, not infrastructure.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `StoryPlayerPanel` | import from Story/panels/| Primary playback surface |
| `StoryPlayerPanel` (runtime controls) |  | `RuntimeControls.tsx` — pause/resume/state display |

@josep-note: use the right imports/websocket connections - all panels that require interactivity should provide them. @josep will wire in higher-level websocket connectivity when needed to bridge - but we have all the bridges I can think of at this time.  do not rewrite/add websockets without checking explicitly - getting one working in a bespoke location risks breaking other places, and it's not the right pattern.

### Visibility required
| Display Element | Status | Notes |
|---|---|---|
| Story metadata display | need visualization | Title, description, version, current state summary |

| State visualization | Visible - exists in panel.  needs refinement for demo | A readable representation of "where we are" in the state machine |

we need a presentation mode for StoryStateCollapsible (mode?: "debug" | "viewer")


### Composition level
StoryPlayerPanel is the dominant surface. RuntimeControls compose within or beside it. A metadata block contextualizes the story for the viewer before they engage.

### Gaps
- `StoryPlayerPanel` — currently wired to real story data.

legacy documentation may reference StoryPlayer: this happened because the StoryPlayer was written before the Panel architecture existed for it to be migrated into.  The StoryPlayerPanel is a legible, proven, tested and more comprehensive set of functionality - it exists in components/Page/StoryPlayerPanel as an import or to clone and extend (limited)

- A `StoryBlock` (metadata/description) needs to exist — distinct from the player panel itself @josep-note : we can use ContextBlock for this purpose.

- The "pause and see the state" moment is the demo's climax — `StoryStateCollapsible` exists but needs presentation refinement for demo context (not debug context)

### Open question
Does the viewer interact with the story, or observe it?
@josep-response: interaction possible, but not in full debug/author mode.  limited scope.

---

## Demo C: Human/LLM Co-engagement with Story Logic Types

**Claim being demonstrated:** An orchestrator can manage a set of sub-agents with different tool capabilities, spawn new sub-agents, refine tools mid-execution, and produce interactive UI elements that both users and agents can engage with.

This is the most complex demo. It has the most moving parts and the most dependencies.

@claude-note: The eng reference notes UAC (UserAgentConfig) should be first-class here but currently falls back to direct `build_agent_prompt()`. The multi-agent orchestration Josep described (orchestrator + sub-agents + tool refinement) depends on UAC-level configuration being in place, not just prompt-level. This is the "needs extended" note in the eng reference. Demo C may have a backend prerequisite (UAC as first-class) before the frontend composition work is meaningful.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `StoryEditorPanel` | exists | Where the story logic is visible/editable |
| `A2UIPanel` | exists | Agent-generated UI elements |
| `ChatPanel` | exists | Communication channel alongside execution |
| `ParticipantPanel` | exists | Agent participant visibility |
| `DebugPanel` | exists, needs caution | Useful for showing orchestrator state — "advanced, needs more tests" |

### Blocks required
| Block | Status | Notes |
|---|---|---|
| Orchestrator state block | missing | Shows current orchestrator + active sub-agents |
| Tool capability display | missing | What tools are currently available / being refined |
| Story logic type explainer | missing | Contextualizes "what kind of story is this" for the viewer |

### Composition level
This is a multi-panel composition — the most complex layout of the four demos. Likely: StoryEditorPanel (primary), A2UIPanel (secondary, dynamic), ChatPanel (tertiary), with ParticipantPanel showing the agent roster.

The challenge here is not the panels but the **narrative thread** — the viewer needs to be able to follow what's happening across multiple simultaneous surfaces. This is a UX/sequencing problem, not just a panel availability problem.

### Gaps
- No "orchestrator view" block or panel — the viewer needs a reading of the multi-agent state that isn't raw debug output
- A2UIPanel generating interactive elements in real-time is the centerpiece — is this currently wired?
- The "tool refinement" moment needs to be visually legible — currently no display primitive for this
- `DebugPanel` note: "needs more tests before any changes are made" — treat as read-only for demo purposes

### New primitive candidate: `AgentRosterBlock`
- Shows active agents in a demo/story context
- Uses existing Presentation-as-Data system for agent identity
- Distinct from `ParticipantPanel` — static roster display vs. live participant management
- Could serve Demo A as well

(this exists too.)

---

## Demo D: Flock of Starlings (Collaborative Canvas)

**Claim being demonstrated:** Multiple agents, each receiving updates from the others, each contributing to a shared drawing. Emergent collective behavior on a shared canvas.

@claude-note: Demo D is notably absent from the eng reference entirely. The reference covers story-based demos. CanvasPanel and gRPC are mentioned in PageConstructs but not in the engineering reference at all — suggesting Demo D is at a different maturity level than A, B, C. This is either because it's further from the current working system, or because it has a separate engineering reference that wasn't included here.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `CanvasPanel` | exists, "pending integration" | Primary surface — the canvas itself |
| `ParticipantPanel` | exists | Show which agents are drawing |

### Blocks required
| Block | Status | Notes |
|---|---|---|
| Agent contribution display | missing | Who contributed what — a legend or activity feed |
| Demo context block | missing | "What are you looking at / why does this matter" |

### Composition level
CanvasPanel dominant (full or near-full width). ParticipantPanel sidebar showing agent identities with their visual presentation. An optional contribution legend below or overlay.

### Gaps
- `CanvasPanel` is "pending integration" — this is the most significant structural gap for Demo D. Need to understand what "pending" means in practice.
- No agent-contribution attribution primitive exists — we'd need something that shows "agent X contributed this stroke/region" in a legible way
- The *visual* demo may be the most immediately arresting of the four — if CanvasPanel can render agent contributions with their respective presentation colors, the demo speaks for itself

### Open question
Is the "pending integration" on CanvasPanel a frontend wiring issue or a backend/gRPC issue? If frontend: potentially unblocked quickly. If backend: Demo D sequencing may need to shift.

@claude-note: This remains the most important unanswered question in this document. Everything about Demo D sequencing depends on it. Until answered, Demo D should stay at the end of the sequence regardless of its visual appeal.

---

## Cross-Demo: Blocks Needed

Rationalizing across all four, the new blocks required are:

| Block | Serves | Priority | Notes |
|---|---|---|---|
| `ContextBlock` | A, B, C, D | High | General-purpose "what is this" block. Renamed from DescriptionBlock — "context" generalizes better to dynamic demos. |
| `StoryBlock` | B, C | High | Story metadata, current state summary, version |
| `AgentRosterBlock` | A, C, D | High | Active agent display using Presentation-as-Data — blocked on P-a-D migration |
| `OrchestratorStateBlock` | C | Medium | Multi-agent orchestration state — readable, not debug. Blocked on UAC being first-class. |
| `ToolCapabilityBlock` | C | Medium | Current tool roster, refinement state. Same blocker as above. |
| `ContributionFeedBlock` | D | Medium | Agent attribution / activity feed. Blocked on CanvasPanel status. |

Blocks that already exist but need generalization:
- `IdentityBlock` — currently person-centric, needs to handle agent identity
- `ActivityFeedBlock` — may serve Demo D's contribution feed with minimal modification
- `StoryStateCollapsible` — exists inside StoryPanel, needs viewer mode variant before StoryBlock is needed

@claude-note: The two Medium-priority blocks for Demo C (OrchestratorStateBlock, ToolCapabilityBlock) are downstream of a backend prerequisite (UAC as first-class). Building them before the backend is ready produces components with nowhere to get real data. These should be explicitly marked as backend-blocked, not just lower priority.

---

## Cross-Demo: Primitives Needed or Needing Attention

| Primitive | Status | Need |
|---|---|---|
| `ResizablePanelGroup` | exists, in use | Current layout primitive in DemoPage — hardcoded 60/40. Needs flexible slot system for Demos A, C, D. |
| `PanelContainer` | exists | Relationship to ResizablePanelGroup needs clarification before demo wiring |
| `DemoShell` | in progress (clone of PageShell) | Needs to resolve: what does it add over current DemoPage? |
| `DemoPage` | exists, working | Relationship to DemoShell in progress needs to be explicit |
| `AgentIdentityDisplay` | partial (in Presentation/) | Needs to be usable from Page/primitives context — blocked on P-a-D migration |
| Presentation-as-Data migration | noted in REFERENCE.md TODOs | Blocks AgentRosterBlock and AgentIdentityDisplay in demo contexts |

---

## Sequencing Recommendation

*Conceptual level note:* the original sequencing (B → A → D → C) still holds as a presentation sequence. What's changed: B is closer to done than initially assessed, and C has explicit backend prerequisites. The implementation sequence should reflect actual blockers, not just complexity gradient.

**Phase 0 — Resolve the ambiguities (do this first, it's cheap)**
1. Clarify DemoShell vs DemoPage relationship — what's being replaced, what's being extended
2. Clarify StoryPlayerPanel vs StoryPanel — which is the working one, what does the other do
3. Confirm CanvasPanel blocker — frontend or backend
4. Confirm UAC first-class status — does Demo C need to wait for it

**Phase 1 — Shared foundations**
1. Migrate Presentation-as-Data utils/resolve/hooks to top level (unblocks AgentRosterBlock and all agent identity display)
2. Create `ContextBlock` (general purpose, serves all four, no blockers)
3. Flexible panel slot system in DemoShell (unblocks Demo A layout, Demo C composition)
4. DemoConfig backend migration (unblocks the "create via multiple interfaces" claim)

**Phase 2 — Demo B (Story playback, mostly already working)**
1. Clarify which Story panel is primary and reconnect if needed
2. Add viewer mode to `StoryStateCollapsible` for demo presentation
3. Create `StoryBlock` for metadata display
4. Polish existing enchanted library demo to demo-ready standard

**Phase 3 — Demo A (Chat room)**
1. Rework layout: ChatPanel dominant, ParticipantPanel secondary
2. Viewer/participant mode toggle on ChatPanel
3. Wire agent identity display in ParticipantPanel

**Phase 4 — Demo D (Canvas, if unblocked)**
1. Wire CanvasPanel to real agent output
2. Agent contribution attribution display

**Phase 5 — Demo C (Orchestration, after backend prerequisites)**
1. Build `OrchestratorStateBlock` and `ToolCapabilityBlock` once UAC is first-class
2. Multi-panel composition in DemoShell
3. Wire A2UIPanel to real agent output
4. Narrative thread / UX sequencing work

---

## Open Questions — Updated Status

| # | Question | Status |
|---|---|---|
| 1 | CanvasPanel — frontend or backend blocker? | **Still open. Highest priority to answer.** |
| 2 | StoryPlayerPanel — wired or shell? | **Still open. Clarify vs StoryPanel.** |
| 3 | Demo A — live or replay? | **Resolved: live. WebSocket infrastructure already exists.** |
| 4 | DemoShell routing — query param or route segments? | **Resolved: slug-based route segments (`/demo/$slug`), already working.** |
| 5 | Presentation-as-Data migration — waiting for right moment? | **Still open. Now explicitly blocking AgentRosterBlock and demo agent identity display.** |
| 6 | DemoShell vs DemoPage — what's the relationship? | **New. Needs resolution before DemoShell work goes further.** |
| 7 | UAC as first-class — backend prerequisite for Demo C? | **New. Eng reference flags this explicitly. Blocks OrchestratorStateBlock and ToolCapabilityBlock.** |

---

## Notes for Future Sessions

- This document should be updated as blockers are resolved — especially the Phase 0 ambiguities
- The `DebugPanel` constraint ("needs more tests before changes") holds — read-only in demo contexts
- The `layout_json` blob structure for demo pages should be documented once the first demo page is created via CLI
- The eng reference seed script pattern (API-based, importable, `--json` flag) is the canonical model for how new demos get created programmatically — new demos should follow it exactly
- When DemoConfig backend migration lands, update eng reference's "Register the Demo Config" section to reflect the new flow
- Consider whether `demo-eng-reference.md` and this doc should eventually merge or remain separate — current split (eng reference = how to create demos, scaffolding = what we're building) is functional but has overlap