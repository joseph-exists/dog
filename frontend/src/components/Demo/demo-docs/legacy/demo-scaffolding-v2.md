# Demo Scaffolding Requirements
> **Status:** Planning artifact — working document, round 2 annotations  
> **Last updated:** 2025-02-21  
> **Purpose:** Map four demo surfaces against current Page/panel/block infrastructure. Identify gaps, composition requirements, and sequencing.

---


## Framing

The four demos are not independent exhibits. They are four projections of a single ontological claim: that the platform's morphism model works across creation method, display surface, and runtime modification. The Demo page's job is to make that claim legible to a viewer who may not arrive with the vocabulary to understand what they're seeing.

This document operates at two levels simultaneously:
- **Structural** — what panels/blocks/primitives are required
- **Compositional** — how those elements compose, and what PageShell needs to be able to hold

When crossing from one to the other, this document will signal explicitly.



---

## Shared Infrastructure Requirements (all four demos)


### DemoShell - 
- Must support a `demo` entity type cleanly — `entity_type: "demo"`, `entity_id: "<slug or uuid>"`
- Must handle panel-only layouts (no blocks) without layout thrash
- Must handle mixed layouts (with blocks describing the demo + panels showing it) - example: a ContentBlock - or panel containing a ContentBlock - that changes content dependent on the Node.
- The `/demo` entry and `?id=` subpage routing pattern needs to resolve to DemoShell correctly 



### PanelContainer
- Must be stable under real panel content — this is the primary load-bearing primitive 
- Panel resize behavior needs to be predictable (not fight with panel content)
- Must support a "presentation mode" state where chrome (edit controls, toolbars) is hidden


### Presentation / Theming 

- Demo pages will need their own ambient theme — the demo surface should feel distinct from the app chrome 
- The full variable set must be set on the demo shell container
- Per-demo theming (each demo has its own visual identity) should compose cleanly via the existing specificity model


### New created:  `DemoShell`

- Wraps a demo instance
- Sets ambient theme from demo's presentation data
- Provides the "entry" and "subpage" routing context
- There is no distinct DemoPage after this refactor.

Capability requirements of DemoShell:
- flexible panel slot composition, including:
- room, chat, story, canvas, content, agentui
- flexible content block management (any of our supported content types)
- toggles for state
- useEffect based runtime
- connection management 
- DemoHeader, DemoLayout
- block support for context/description blocks
- entity type aware routing

---

## Demo A: Multiplayer / Multi-LLM Chat Room

**Claim being demonstrated:** Multiple humans and multiple LLMs can share a real-time communication surface. Participants are legible — you can tell who is human and who is agent.

### Panels required
| Panel | Status | 
|---|---|---|
| `ChatPanel` | exists |
| `ParticipantPanel` | exists | 


### Blocks required
| Block | Status | Notes |
|---|---|---|
| `ContentBlock` | exists | 


### Composition level
multi-panel layout: ChatPanel (primary, large) + ParticipantPanel (secondary, sidebar or collapsible). A description block above or alongside.

use mode prop on ChatPanel (`"participant" | "observer"`)

### Gaps
- `ParticipantPanel` needs to render agent presentation (emoji, accent color) not just user avatars

---

## Demo B: Story Pause / Replayability

**Claim being demonstrated:** A story is a state machine. It can be paused, serialized, and resumed. The viewer can see this happen.


### Panels required
| Panel | Status | Notes |
|---|---|---|
| `StoryPlayerPanel` | import from Story/panels/| Primary playback surface |
| `StoryPlayerPanel` (runtime controls) |  | `RuntimeControls.tsx` — pause/resume/state display |


### Visibility required
| Display Element | Status | Notes |
|---|---|---|
| Story metadata display | need visualization | Title, description, version, current state summary |

| State visualization | Visible - exists in panel.  needs refinement for demo | A readable representation of "where we are" in the state machine |

@todo: need a presentation mode for StoryStateCollapsible (mode?: "debug" | "viewer")


### Composition level
StoryPlayerPanel is the dominant surface. RuntimeControls compose within or beside it. A metadata block contextualizes the story for the viewer before they engage.

### Gaps
- `StoryPlayerPanel` — currently wired to real story data.

- A `StoryBlock` (metadata/description) needs to exist — distinct from the player panel itself.

- add ContextBlock as derived instantiation with relational association to Node?

- The "pause and see the state" moment is the demo's climax — `StoryStateCollapsible` 

---

## Demo C: Human/LLM Co-engagement with Story Logic Types

**Claim being demonstrated:** An orchestrator can manage a set of sub-agents with different tool capabilities, spawn new sub-agents, refine tools mid-execution, and produce interactive UI elements that both users and agents can engage with.

This is the most complex demo. It has the most moving parts and the most dependencies.


### Panels required
| Panel | Status | Notes |
|---|---|---|
| `StoryEditorPanel` | exists | Where the story logic is visible/editable |
| `A2UIPanel` | exists | Agent-generated UI elements |
| `ChatPanel` | exists | Communication channel alongside execution |
| `ParticipantPanel` | exists | Agent participant visibility |
| `DebugPanel` | exists | Useful for showing orchestrator state —  ensure demo can use|

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

### NOTE: IGNORE New primitive candidate: `AgentRosterBlock`
- Shows active agents in a demo/story context
- Uses existing Presentation-as-Data system for agent identity
- Distinct from `ParticipantPanel` — static roster display vs. live participant management
- Could serve Demo A as well



---

## Demo D: Flock of Starlings (Collaborative Canvas)

**Claim being demonstrated:** Multiple agents, each receiving updates from the others, each contributing to a shared drawing. Emergent collective behavior on a shared canvas.

Demo D is notably absent from the eng reference entirely. The reference covers story-based demos. CanvasPanel and gRPC are mentioned in PageConstructs but not in the engineering reference at all — suggesting Demo D is at a different maturity level than A, B, C. This is either because it's further from the current working system, or because it has a separate engineering reference that wasn't included here.

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




000 0 LEGACY BELOW 0 000

# Demo Scaffolding Requirements
> **Status:** Planning artifact — working document  
> **Last updated:** 2025-02-22  
> **Purpose:** Map four demo surfaces against current Page/panel/block infrastructure. Identify gaps, composition requirements, and sequencing.


---

## Framing

The four demos are not independent exhibits. They are four projections of a single ontological claim: that the platform's morphism model works across creation method, display surface, and runtime modification. The Demo page's job is to make that claim legible to a viewer who may not arrive with the vocabulary to understand what they're seeing.

This document operates at two levels simultaneously:
- **Structural** — what panels/blocks/primitives are required
- **Compositional** — how those elements compose, and what PageShell needs to be able to hold

When crossing from one to the other, this document will signal explicitly.

---

## Shared Infrastructure Requirements (all four demos)

### DemoShell 
- Must support a `demo` entity type cleanly — `entity_type: "demo"`, `entity_id: "<slug or uuid>"` 
- Must handle panel-only layouts (no blocks) without layout thrash
- Must handle mixed layouts (blocks describing the demo + panels showing it)
- The `/demo` entry and `?id=` subpage routing pattern needs to resolve to DemShell correctly 
- Must handle panels within blocks and blocks within panels.
- Must handle ALL panel functionality
- Must enable ALL theming functionality

### PanelContainer
- Must be stable under real panel content — this is the primary load-bearing primitive 
- Panel resize behavior needs to be predictable (not fight with panel content)
- Must support a "presentation mode" state where chrome (edit controls, toolbars) is hidden

### Presentation / Theming 

- Demo pages will need their own ambient theme — the demo surface should feel distinct from the app chrome 
- The full variable set (per REFERENCE.md) must be set on the demo page container
- Per-demo theming (each demo has its own visual identity) should compose cleanly via the existing specificity model

### New primitive: `DemoShell`

- Wraps a demo instance
- Sets ambient theme from demo's presentation data
- Provides the "entry" and "subpage" routing context


---

## Demo A: Multiplayer / Multi-LLM Chat Room

**Claim being demonstrated:** Multiple humans and multiple LLMs can share a real-time communication surface. Participants are legible — you can tell who is human and who is agent.

### Panels required

ChatPanel, ParticipantPanel, ContentBlock

### Composition level
Two-panel layout: ChatPanel (primary, large) + ParticipantPanel (secondary, sidebar or collapsible). A description block above or alongside.


---

## Demo B: Story Pause / Replayability

**Claim being demonstrated:** A story is a state machine. It can be paused, serialized, and resumed. The viewer can see this happen.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `StoryPlayerPanel` | exists | Primary playback surface |
| `StoryPanel` (runtime controls) | exists | `RuntimeControls.tsx` — pause/resume/state display |

### Blocks required
| Block | Status | Notes |
|---|---|---|
| Story metadata display | missing | Title, description, version, current state summary |
| State visualization | missing | A readable representation of "where we are" in the state machine |


### Composition level
StoryPlayerPanel is the dominant surface. RuntimeControls compose within or beside it. A metadata block contextualizes the story for the viewer before they engage.

### Gaps
- `StoryPlayerPanel` — is it currently wired to real story data, or is it a structural shell waiting for reconnection?
- A `StoryBlock` (metadata/description) needs to exist — distinct from the player panel itself
- The "pause and see the state" moment is the demo's climax — `StoryStateCollapsible` exists but may need presentation refinement for demo context (not debug context)

### Open question
Does the viewer interact with the story, or observe it? If observe: we need a clear "spectator" mode. If interact: the demo becomes Demo C territory.

---

## Demo C: Human/LLM Co-engagement with Story Logic Types

**Claim being demonstrated:** An orchestrator can manage a set of sub-agents with different tool capabilities, spawn new sub-agents, refine tools mid-execution, and produce interactive UI elements that both users and agents can engage with.

This is the most complex demo. It has the most moving parts and the most dependencies.

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

---

## Demo D: Flock of Starlings (Collaborative Canvas)

**Claim being demonstrated:** Multiple agents, each receiving updates from the others, each contributing to a shared drawing. Emergent collective behavior on a shared canvas.

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

---

## Cross-Demo: Blocks Needed

Rationalizing across all four, the new blocks required are:

| Block | Serves | Priority | Notes |
|---|---|---|---|
| `ContextBlock` / `DescriptionBlock` | A, B, C, D | High | General-purpose "what is this" block. Replaces person-centric bio in demo contexts. |
| `StoryBlock` | B, C | High | Story metadata, current state summary, version |
| `AgentRosterBlock` | A, C, D | High | Active agent display using Presentation-as-Data |
| `OrchestratorStateBlock` | C | Medium | Multi-agent orchestration state — readable, not debug |
| `ToolCapabilityBlock` | C | Medium | Current tool roster, refinement state |
| `ContributionFeedBlock` | D | Medium | Agent attribution / activity feed |

Blocks that already exist but need generalization:
- `IdentityBlock` — currently person-centric, needs to handle agent identity
- `ActivityFeedBlock` — may serve Demo D's contribution feed with minimal modification

---

## Cross-Demo: Primitives Needed or Needing Attention

| Primitive | Status | Need |
|---|---|---|
| `PanelContainer` | exists | Validate stability under real load before wiring demos |
| `DemoShell` | missing | New — ambient theme + routing context for demo instances |
| `AgentIdentityDisplay` | partial (in Presentation/) | Needs to be usable from Page/primitives context |
| Presentation-as-Data migration | noted in REFERENCE.md TODOs | `utils`, `resolve`, `hooks` need to move to top level before demo panels can use them cleanly |

---

## Sequencing Recommendation

*Stepping back to conceptual level briefly:* the four demos form a natural difficulty gradient — A is the most structurally proven, D is the most visually arresting, B is the clearest ontological proof, C is the most complex. A good demo sequence might be B → A → D → C (proof of concept → social → visual → complex) but that's a presentation decision, not an architecture one.

For **implementation sequencing**:

**Phase 1 — Shared foundations**
1. Validate PanelContainer under real panel content
2. Create `ContextBlock` / `DescriptionBlock` (general purpose, serves all four)
3. Create `AgentRosterBlock` (serves A, C, D)
4. Migrate Presentation-as-Data utils/resolve/hooks to top level (REFERENCE.md TODO)
5. Wire `DemoShell` routing for `/demo` and `?id=` subpages

**Phase 2 — Demo B (Story playback)**
1. Confirm `StoryPlayerPanel` reconnection path
2. Create `StoryBlock` for metadata display
3. Validate `StoryStateCollapsible` in demo (non-debug) presentation mode

**Phase 3 — Demo A (Chat room)**
1. Add observer/viewer mode to `ChatPanel`
2. Generalize `ParticipantPanel` for agent identity display

**Phase 4 — Demo D (Canvas)**
1. Determine CanvasPanel "pending integration" blockers
2. Wire agent contribution display if CanvasPanel is unblocked

**Phase 5 — Demo C (Orchestration)**
1. Build `OrchestratorStateBlock` and `ToolCapabilityBlock`
2. Wire A2UIPanel to real agent output
3. Composition / UX sequencing work

---

## Open Questions Requiring Your Input

1. **CanvasPanel "pending integration"** — frontend or backend blocker?
2. **StoryPlayerPanel** — structural shell or wired to real story data pre-intentional disconnection?
3. **Demo A** — live Room or replay? This changes the real-time infrastructure requirement significantly.
4. **DemoShell routing** — `/demo` as a static page with subpage routing via query param, or full route segments (`/demo/[id]`)?
5. **Presentation-as-Data migration** — is there a reason this hasn't moved to top level yet, or is it waiting for the right moment?

---

## Notes for Future Sessions

- This document should be updated as gaps are closed
- Phase sequencing should be revisited after CanvasPanel blocker is understood
- The `DebugPanel` note ("needs more tests before changes") should be treated as a hard constraint — use read-only in demo contexts, no modifications
- The `layout_json` blob structure for demo pages should be documented once the first demo page is created via CLI — that will be the canonical example for the others