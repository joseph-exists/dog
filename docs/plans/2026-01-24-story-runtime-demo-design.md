# Story Runtime Demo — Design Document

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** A proof-of-concept demo page that showcases the story runtime + agent context integration, accessible at `/demo/story-runtime`.

**Architecture:** A slug-routed demo page that composes StoryPanel (left) and ChatPanel (right) for a pre-seeded room with two AI agents. Agents receive live story context (current node, path, choices, state) in their prompts. Users can advance, rewind, or reset the story — and optionally have agents auto-respond to state changes.

**Tech Stack:** React + TanStack Router, existing StoryPanel/Chat components, existing useRoomRuntime/useRoom hooks, backend seed script (Python).

---

## Route & Layout

- **Route:** `/demo/$slug` (e.g., `/demo/story-runtime`)
- **Route file:** `frontend/src/routes/_layout/demo.$slug.tsx`
- **Layout:** Full-bleed, horizontal `ResizablePanelGroup`:
  - Left panel (60%): StoryPanel — current node, choices, node chain, story state, rewind/reset controls
  - Right panel (40%): Chat — MessageList + MessageInput, WebSocket-connected

## Component Tree

```
DemoPage (route: /demo/$slug)
├── DemoHeader
│   ├── Title + Description
│   ├── Auto-Respond Toggle (Switch)
│   └── Room connection status indicator
├── ResizablePanelGroup (horizontal)
│   ├── ResizablePanel (60%) — DemoStoryPanel
│   │   └── StoryPanel (existing, canWrite=true)
│   └── ResizablePanel (40%) — ChatPanel
│       ├── MessageList (existing, from useRoom hook)
│       └── MessageInput (existing)
```

## Data Flow

### Story State → Agent Context

```
User clicks choice → useRoomRuntime.advance(choiceId)
    → Backend updates UserStoryProgress (current_node_id, story_state)
    → Backend returns updated RoomRuntimePublic
    → Frontend query cache updates → StoryPanel re-renders

    If autoRespond enabled:
        → DemoPage sends synthetic message via room API
        → Backend agent_runner triggers (agents have participation_mode: "always")
        → build_room_context() loads current story_runtime
        → build_agent_prompt() formats node, path, choices, state into prompt
        → Agent responds with story-aware context
        → Response streams via WebSocket → MessageList updates
```

### Rewind/Reset → Context Reset

Because `build_room_context()` queries the *current* `UserStoryProgress` state at call-time, rewind/reset automatically means agents see the rewound state. No special "context reset" logic is needed.

### Synthetic Message Formats

- Advance: `"[Chose: {choice_text}]"`
- Rewind: `"[Rewound to: {node_title}]"`
- Reset: `"[Reset story to beginning]"`

Bracket-wrapped format signals system-generated messages; gives agents enough context to respond naturally.

## Auto-Respond Mechanism

DemoPage wraps `useRoomRuntime` mutations with post-mutation message sending:

```typescript
const advanceWithAutoRespond = async (choiceId: string) => {
  await runtime.advance(choiceId)
  if (autoRespond) {
    const choice = runtime.runtime?.availableChoices.find(c => c.id === choiceId)
    await sendMessage(`[Chose: ${choice?.text ?? "unknown"}]`)
  }
}
```

Agents have `participation_mode: "always"` so they respond to every message including synthetic ones.

## Demo Seeding

### Story: "The Enchanted Library"

A short branching narrative (3-5 nodes):
- Start node: Entrance to an old library
- 2-3 choice points with `sets_state` (e.g., `has_key`, `trust_librarian`)
- At least one conditional branch (`requires_state`)
- End node(s): Different endings based on state

### Agents

1. **Narrator** (`participation_mode: "always"`)
   - Reacts to current node, describes atmosphere, hints at consequences
   - System prompt references story context sections

2. **Guide** (`participation_mode: "always"`)
   - References story state, reminds user of items/facts collected
   - Suggests which choices align with their path

### Seed Script

`backend/app/scripts/seed_demo_story_runtime.py`
- Creates story, nodes, choices, room, agents, room participants
- Starts the runtime (creates RoomStoryProgress + UserStoryProgress)
- Idempotent: checks if demo room already exists before creating

## Demo Configuration

```typescript
// frontend/src/config/demos.ts
interface DemoConfig {
  slug: string
  title: string
  description: string
  roomId: string
  autoRespond: boolean  // Default toggle state
}

const DEMOS: Record<string, DemoConfig> = {
  "story-runtime": {
    slug: "story-runtime",
    title: "Story Runtime Demo",
    description: "Interactive branching narrative with AI agents that see your story context.",
    roomId: "SEEDED_ROOM_UUID",
    autoRespond: true,
  },
}
```

## File Map

| File | Purpose |
|------|---------|
| `frontend/src/routes/_layout/demo.$slug.tsx` | Route entry point, resolves slug → config |
| `frontend/src/components/Demo/DemoPage.tsx` | Main demo layout (panels, auto-respond logic) |
| `frontend/src/components/Demo/DemoHeader.tsx` | Header with title, description, auto-respond toggle |
| `frontend/src/components/Demo/DemoStoryPanel.tsx` | Thin wrapper adding auto-respond callbacks to StoryPanel |
| `frontend/src/config/demos.ts` | Demo configuration registry |
| `backend/app/scripts/seed_demo_story_runtime.py` | Database seeding script |

## Route Registration

In `frontend/src/routes/_layout.tsx`:
- Add `"/demo/"` to `fullBleedRoutes` array
- Add `"/demo/"` → `"Demo"` to `routeTitles` map

## Implementation Order

1. **Seed script** — Create the story, room, and agents in DB
2. **Demo config** — `demos.ts` with hardcoded room UUID from seed
3. **Route + DemoPage** — Basic route that renders the two-panel layout
4. **DemoStoryPanel** — Wrapper with auto-respond callbacks
5. **DemoHeader** — Title, description, toggle switch
6. **Route registration** — fullBleedRoutes + routeTitles in _layout.tsx
7. **End-to-end test** — Verify agents see story context in their prompts
