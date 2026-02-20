# Demo Scaffolding Requirements
> **Status:** Planning artifact — working document  
> **Last updated:** 2025-02-20  
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

Before any demo-specific work, the following must be reliable:
@josep-note: changed PageShell to DemoShell
### DemoShell 
- Must support a `demo` entity type cleanly — `entity_type: "demo"`, `entity_id: "<slug or uuid>"`  @josep-note: correct.  added DemoShell.tsx, refactoring now. working through slug vs id issues. 
- Must handle panel-only layouts (no blocks) without layout thrash
- Must handle mixed layouts (blocks describing the demo + panels showing it)
- The `/demo` entry and `?id=` subpage routing pattern needs to resolve to DemShell correctly 

### PanelContainer
- Must be stable under real panel content — this is the primary load-bearing primitive 
- Panel resize behavior needs to be predictable (not fight with panel content)
- Must support a "presentation mode" state where chrome (edit controls, toolbars) is hidden

### Presentation / Theming 
@josep-note: theming at this level is a solved problem. we will integrate as a second-order part of the sequence when we've stabilized the surface. all of the following (and more) already exist, will be integrated at the appropriate time.
- Demo pages will need their own ambient theme — the demo surface should feel distinct from the app chrome 
- The full variable set (per REFERENCE.md) must be set on the demo page container
- Per-demo theming (each demo has its own visual identity) should compose cleanly via the existing specificity model

### New primitive needed: `DemoShell`
@josep-note: in progress. currently added to directory, but as a clone from PageShell that's still being worked on.  needs more definition (through this process)
- Wraps a demo instance
- Sets ambient theme from demo's presentation data
- Provides the "entry" and "subpage" routing context
- Composes with PageShell rather than replacing it
@josep-note : replacing it is fine. Demo has a distinct enough purpose I'm fine with this.

---

## Demo A: Multiplayer / Multi-LLM Chat Room

**Claim being demonstrated:** Multiple humans and multiple LLMs can share a real-time communication surface. Participants are legible — you can tell who is human and who is agent.

### Panels required
| Panel | Status | Notes |
|---|---|---|
| `ChatPanel` | exists, needs (visual/layout) refinement | Primary surface |
| `ParticipantPanel` | exists | Shows participant stack with agent/human distinction |

### Blocks required
| Block | Status | Notes |
|---|---|---|
| A intro/description block | missing | Sets context for the viewer — "what am I looking at?" |
| Participant identity display | partial (`IdentityBlock` is person-centric) | Needs to handle agent identity presentation |
@josep-note : we will use the ParticipantsPanel - once we're set on it, we can theme/restyle/overload it however we need.

### Composition level
Two-panel layout: ChatPanel (primary, large) + ParticipantPanel (secondary, sidebar or collapsible). A description block above or alongside.
@josep-note 100%

### Gaps
- `ParticipantPanel` needs to render agent presentation (emoji, accent color) not just user avatars
@josep-note - this exists, just needs wired back in once we're ready.

- No "viewer mode" for ChatPanel — currently assumes participant, not observer
@josep-note: exists. (basically: clone ChatPanel as ChatViewPanel, remove the input field display, remove user control buttons, tada)

- The intro block needs to be a general-purpose `DescriptionBlock` or `ContextBlock`, not a person-bio block
@josep-note: agreed.  @josep-todo: pri 1 task


### Open question
Is Demo A best served as a live Room (join-able) or a replay? Both are valid. The answer changes whether we need real-time connection infrastructure or just playback.

@josep-note: both are present in the same component. we'll change the visual display as needed - these toggles are easy once we have the frame ready.  

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