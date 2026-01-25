# Room Panels & Story Player Engineering Reference Card

> Quick reference for engineers working with room panels, story integration, and extending the panel system.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Room Panel Architecture                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────┐     ┌──────────────────┐     ┌───────────────┐   │
│   │    Panel Config     │────▶│   panelService   │────▶│   Backend     │   │
│   │   (DB/User Prefs)   │     │   (resolution)   │     │   API         │   │
│   └─────────────────────┘     └──────────────────┘     └───────────────┘   │
│              │                                                               │
│              ▼                                                               │
│   ┌─────────────────────┐     ┌──────────────────┐                          │
│   │   useRoomPanels     │────▶│ panelComponents  │ ◀── Component Registry   │
│   │   (hook)            │     │ (r.$roomId.tsx)  │                          │
│   └─────────────────────┘     └──────────────────┘                          │
│              │                         │                                     │
│              ▼                         ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         RoomShell                                    │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │   │
│   │  │ ChatPanel    │  │ StoryPlayer  │  │ Participants │  ...          │   │
│   │  │ (primary)    │  │ (auxiliary)  │  │ (auxiliary)  │               │   │
│   │  └──────────────┘  └──────────────┘  └──────────────┘               │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Panel System

### Available Panel Kinds

| Kind | Component | Purpose |
|------|-----------|---------|
| `chat` | `ChatPanel` | Main chat interface with message list & input |
| `storyEditor` | `StoryEditorPanel` | Story authoring/editing (owner only) |
| `storyRuntime` | `StoryPanel` | **Shared** story player - server-managed state |
| `storyPlayer` | `StoryPlayerPanel` | **Solo** story player - local state, emits events |
| `debug` | `DebugPanel` | Developer debug info (messages, connections) |
| `canvas` | `CanvasPanel` | Placeholder for drawing canvas |
| `a2ui` | `A2UIPanel` | Agent-generated UI components |
| `participantPanel` | `ParticipantPanel` | Users & agents list with management |

### Key Files

| Layer | File | Purpose |
|-------|------|---------|
| **Service** | `services/panelService.ts` | Panel types, validation, display names |
| **Hook** | `hooks/useRoomPanels.ts` | Fetch resolved panel config for room |
| **Route** | `routes/_layout/r.$roomId.tsx` | Panel component registry (`panelComponents`) |
| **Shell** | `components/Room/RoomShell.tsx` | Renders panels in layout |
| **Primitives** | `components/Room/primitives/` | `PanelContainer`, `PlaceholderContent` |
| **Panels** | `components/Room/panels/` | Individual panel implementations |

### Panel Configuration Flow

```
1. Backend stores panel config per room/user
2. useRoomPanels(roomId) fetches resolved config
3. panelConfigs.map() builds PanelConfig[] with render functions
4. RoomShell renders panels by prominence (primary/auxiliary)
```

---

## Story Integration

### Two Story Modes

| Mode | Panel Kind | State Location | Use Case |
|------|------------|----------------|----------|
| **Shared Runtime** | `storyRuntime` | Server (DB) | Multiplayer - all participants see same story state |
| **Solo Player** | `storyPlayer` | Browser (React state) | Single player - each person plays independently |

### StoryPlayerPanel (Solo)

**Data flow:**
```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ useStory-    │────▶│ StoryPlayer-    │────▶│ WebSocket        │
│ Editor hook  │     │ Panel           │     │ (room events)    │
│              │     │ (local state)   │     │                  │
└──────────────┘     └─────────────────┘     └──────────────────┘
   ↓ fetches            ↓ manages              ↓ emits
 story/nodes/         currentNode,           story events
 choices              playerState,           to chat
                      history
```

**Story events emitted:**
```typescript
interface StoryProgressEvent {
  type: "choice_made" | "story_started" | "story_ended" | "story_restarted" | "story_rewound"
  nodeTitle: string
  choiceText?: string   // For choice_made
  isEndNode?: boolean   // For story_ended
}
```

**Event message formats:**
| Event | Chat Message |
|-------|--------------|
| `story_started` | `[Story: started "The Beginning"]` |
| `choice_made` | `[Story: chose "Enter cave" → The Dark Forest]` |
| `story_ended` | `[Story: reached ending "Victory"]` |
| `story_rewound` | `[Story: rewound to "The Crossroads"]` |
| `story_restarted` | `[Story: restarted "The Beginning"]` |

**Agent integration:** Agents in the room can see these events and respond contextually (e.g., a narrator agent adding flavor text).

### StoryPanel (Shared Runtime)

Uses `useRoomRuntime` hook for server-managed state:
```typescript
const {
  runtime,        // Current runtime state
  start,          // Initialize runtime
  advance,        // Make a choice
  rewind,         // Go back one step
  reset,          // Reset to beginning
} = useRoomRuntime(roomId)
```

---

## Adding a New Panel

### Step 1: Create the Component

```typescript
// src/components/Room/panels/MyNewPanel.tsx
import { PanelContainer } from "../primitives/PanelContainer"

interface MyNewPanelProps {
  roomId: string
  // ... other props
}

export function MyNewPanel({ roomId }: MyNewPanelProps) {
  return (
    <PanelContainer title="My Panel" headerActions={/* optional */}>
      {/* Panel content */}
    </PanelContainer>
  )
}
```

### Step 2: Export from Panels Index

```typescript
// src/components/Room/panels/index.ts
export { MyNewPanel } from "./MyNewPanel"
```

### Step 3: Add Panel Kind to Service

```typescript
// src/services/panelService.ts

// 1. Add to kind union (line ~36)
kind: "chat" | "storyEditor" | ... | "myNewPanel"

// 2. Add to validation array (line ~168)
return ["chat", ..., "myNewPanel"].includes(kind)

// 3. Add display name (line ~183)
myNewPanel: "My New Panel",
```

### Step 4: Register in Room View

```typescript
// src/routes/_layout/r.$roomId.tsx

// 1. Import
import { MyNewPanel } from "@/components/Room"

// 2. Add to panelComponents registry
const panelComponents: Record<string, () => React.ReactNode> = {
  // ...existing panels...
  myNewPanel: () => (
    <MyNewPanel roomId={roomId} />
  ),
}

// 3. Update type cast (if not using inferred types)
config.kind as "chat" | ... | "myNewPanel"
```

### Step 5: (Optional) Add Backend Support

If the panel needs to be selectable in panel configuration:
```python
# backend/app/crud_panels.py - add to VALID_PANEL_KINDS
# backend/app/schemas/panels.py - add to PanelKind enum
```

---

## Common Patterns

### Emitting Room Events from a Panel

```typescript
// In room view, pass sendViaWebSocket to your panel
myNewPanel: () => (
  <MyNewPanel
    roomId={roomId}
    onEvent={(message) => sendViaWebSocket(message)}
  />
)

// In your panel component
interface MyNewPanelProps {
  roomId: string
  onEvent?: (message: string) => void
}

function handleSomething() {
  onEvent?.("[MyPanel: something happened]")
}
```

### Using PanelContainer

```typescript
import { PanelContainer } from "../primitives/PanelContainer"
import { PlaceholderContent } from "../primitives/PlaceholderContent"

// Basic panel
<PanelContainer title="My Panel">
  {content}
</PanelContainer>

// With header actions
<PanelContainer
  title="My Panel"
  headerActions={<Button size="icon" variant="ghost">...</Button>}
>
  {content}
</PanelContainer>

// With footer
<PanelContainer title="My Panel" footer={<StatusBar />}>
  {content}
</PanelContainer>

// Empty/loading state
<PanelContainer title="My Panel">
  <PlaceholderContent
    icon={Loader2}
    title="Loading..."
    description="Please wait"
    className="[&_svg]:animate-spin"
  />
</PanelContainer>
```

### Accessing Room Context in Panels

Panels receive props from the room view. Common data available:
- `roomId` - always passed
- `room?.story_id` - for story-related panels
- `canManage` - whether current user is room owner
- `sendViaWebSocket` - for emitting room events
- `participants` / `activeAgents` - for participant-aware panels

---

## Story State Engine

### Local State Model (StoryPlayerPanel)

```typescript
// Core state
const [currentNodeId, setCurrentNodeId] = useState<string | null>(null)
const [playerState, setPlayerState] = useState<Record<string, unknown>>({})
const [history, setHistory] = useState<HistoryEntry[]>([])

// History entry for undo
interface HistoryEntry {
  nodeId: string
  state: Record<string, unknown>
  choiceText?: string
}
```

### State Conditions (requires_state / sets_state)

```typescript
import { evaluateRequiresState, applySetsState } from "@/utils/stateConditions"

// Filter choices by state conditions
const availableChoices = choices.filter((c) =>
  evaluateRequiresState(c.requires_state, playerState)
)

// Apply state mutations when choice is made
if (choice.sets_state) {
  setPlayerState(prev => applySetsState(choice.sets_state, prev))
}
```

---

## API Endpoints

### Panel Configuration

```
GET  /api/v1/rooms/{room_id}/panels/resolved  → ResolvedPanelConfig
GET  /api/v1/rooms/{room_id}/panels/defaults  → RoomPanelDefaultsPublic
PUT  /api/v1/rooms/{room_id}/panels/defaults  → RoomPanelDefaultsPublic
GET  /api/v1/rooms/{room_id}/panels/me        → UserRoomPanelConfigPublic
PUT  /api/v1/rooms/{room_id}/panels/me        → UserRoomPanelConfigPublic
```

### Story Data (for StoryPlayerPanel)

```
GET  /api/v1/stories/{id}           → StoryPublic
GET  /api/v1/storynodes/            → StoryNodesPublic (filter client-side)
GET  /api/v1/node-choices/?story_id → NodeChoicesPublic
```

### Room Runtime (for StoryPanel shared mode)

```
GET  /api/v1/rooms/{room_id}/runtime        → RoomRuntimePublic | null
POST /api/v1/rooms/{room_id}/runtime/start  → RoomRuntimePublic
POST /api/v1/rooms/{room_id}/runtime/advance → RoomRuntimePublic
POST /api/v1/rooms/{room_id}/runtime/rewind  → RoomRuntimePublic
POST /api/v1/rooms/{room_id}/runtime/reset   → RoomRuntimePublic
```

---

## Query Keys

```typescript
// Panel configuration
["rooms", roomId, "panels"]              // Resolved panels
["rooms", roomId, "panels", "defaults"]  // Room defaults
["rooms", roomId, "panels", "me"]        // User's room config

// Story data (used by useStoryEditor)
["stories", storyId]                     // Story metadata
["stories", storyId, "nodes"]            // Story nodes
["stories", storyId, "choices"]          // Node choices

// Room runtime
["rooms", roomId, "runtime"]             // Shared runtime state
```

---

## Caveats & Tips

1. **Hooks must be unconditional** - Call `useStoryEditor` even if storyId is empty; handle empty state in render
2. **Panel registry is client-side** - `panelComponents` is a render-time mapping, not persisted
3. **Solo vs Shared** - `storyPlayer` = local state (fast, independent); `storyRuntime` = server state (synchronized, slower)
4. **Event format matters** - Agents parse `[Story: ...]` messages for context; keep format consistent
5. **useStoryEditor fetches per-node** - For large stories, consider batch fetching via `NodeChoicesService.readNodeChoices({ storyId })`
6. **PanelContainer scrolls by default** - Set `scrollable={false}` for fixed-height panels

---

## Related Documentation

- Panel layout system: `docs/user-ui-customization/panel-layout-reference.md`
- Story state schema: `docs/story-management/story-state-schema/StoryStateSchema.md`
- Agent UI system: `docs/agent-ui-reference.md`
- Design docs: `docs/plans/2026-01-24-story-player-panel-design.md`
