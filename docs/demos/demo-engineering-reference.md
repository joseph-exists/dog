# Demo System — Engineering Reference Card

> Quick reference for creating new demos, writing seed scripts, and extending the demo infrastructure.

## Architecture at a Glance

```
Route (/demo/$slug)
└── DemoPage (orchestrator)
    ├── DemoHeader (title, description, auto-respond toggle, connection badge)
    └── ResizablePanelGroup
        ├── Left Panel (60%) → DemoStoryPanel → StoryPanel
        └── Right Panel (40%) → MessageList + MessageInput
```

**Config:** `frontend/src/config/demos.ts` — slug → DemoConfig resolution

**Seed:** `backend/app/test_scripts/story_things/seed_enchanted_library.py` — API-based seeding script (returns generated IDs)

**Layout Mode:** Demo routes are full-bleed (`_layout.tsx` → `fullBleedRoutes`). Required for proper flex height constraints.

---

## File Map

| Layer | Path | Purpose |
|-------|------|---------|
| Config | `frontend/src/config/demos.ts` | Demo registry (slug → roomId, title, autoRespond) |
| Route | `frontend/src/routes/_layout/demo.$slug.tsx` | Entry point, slug resolution, not-found fallback |
| Page | `frontend/src/components/Demo/DemoPage.tsx` | Resizable split layout, hooks, message routing |
| Header | `frontend/src/components/Demo/DemoHeader.tsx` | Title, description, connection badge, toggle |
| StoryWrapper | `frontend/src/components/Demo/DemoStoryPanel.tsx` | Watches runtime changes, sends synthetic messages |
| Seed | `backend/app/test_scripts/story_things/seed_enchanted_library.py` | Creates story, nodes, room, agents, runtime via API |
| Context | `backend/app/services/context_provider.py` | `StoryRuntimeContext` → agent context builder |
| Prompt | `backend/app/services/agent_prompt.py` | Formats story state into LLM prompt |

---

## Creating a New Demo

### 1. Write the Seed Script

Create a seed script in `backend/app/test_scripts/story_things/` following the API-based pattern:

```python
"""
Seed script for <Your Demo Name>.

Usage:
    python seed_your_demo.py           # Verbose output
    python seed_your_demo.py --json    # JSON-only (for piping to other scripts)
"""

import argparse
import json
import sys
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).parent))
from auth_helper import AuthenticationError, get_authenticated_session

BASE_URL = "http://localhost:8000/api/v1"


def seed_your_demo(session: requests.Session, verbose: bool = True) -> dict:
    """Create demo entities via API. Returns dict of generated IDs."""
    ids = {}

    # 1. Create Story
    resp = session.post(f"{BASE_URL}/stories", json={
        "title": "Your Demo Story",
        "description": "Description here.",
    })
    resp.raise_for_status()
    story = resp.json()
    ids["story_id"] = story["id"]
    story_id = story["id"]
    version = story["current_version"]

    # 2. Create Nodes
    # ... (POST /api/v1/storynodes for each node)

    # 3. Create State Variables (BEFORE publishing!)
    # ... (POST /api/v1/stories/{story_id}/versions/{version}/state-schema)

    # 4. Create Choices
    # ... (POST /api/v1/node-choices for each choice)

    # 5. Publish Story
    resp = session.put(f"{BASE_URL}/stories/{story_id}/publish")
    resp.raise_for_status()

    # 6. Create Agents
    # ... (POST /api/v1/agents)

    # 7. Create Room
    resp = session.post(f"{BASE_URL}/rooms", json={
        "title": "Your Demo Room",
        "story_id": story_id,
    })
    resp.raise_for_status()
    room = resp.json()
    ids["room_id"] = room["room_id"]

    # 8. Add Agent Participants
    # ... (POST /api/v1/rooms/{room_id}/participants)

    # 9. Create Persona + UserPersona
    # ... (POST /api/v1/personas, POST /api/v1/user-personas)

    # 10. Initialize Room Runtime (creates progress records automatically)
    resp = session.put(f"{BASE_URL}/rooms/{room_id}/runtime", json={
        "user_persona_id": user_persona_id,
        "story_version": published_version,
    })
    resp.raise_for_status()

    return ids


if __name__ == "__main__":
    session = get_authenticated_session()
    ids = seed_your_demo(session)
    print(json.dumps(ids, indent=2))
```

**Key patterns:**
- Uses HTTP API calls (not direct DB access)
- Server generates all UUIDs — no hardcoded IDs
- Returns a dict of generated IDs for programmatic use
- State variables must be created before publishing (API rejects edits to published versions)
- Room runtime initialization (`PUT /rooms/{room_id}/runtime`) auto-creates `UserStoryProgress` and `RoomStoryProgress`
- `--json` flag enables clean output for piping to other scripts
- The `seed_*()` function is importable for use in other test scripts

### 2. Register the Demo Config

Run the seed script and capture the room ID, then add to `frontend/src/config/demos.ts`:

```typescript
export const DEMOS: Record<string, DemoConfig> = {
  // existing demos...
  "your-demo-slug": {
    slug: "your-demo-slug",
    title: "Your Demo Title",
    description: "One-line description of what this demonstrates.",
    roomId: "<room_id from seed output>",
    autoRespond: true,
  },
}
```

### 3. Run the Seed

```bash
cd backend/app/test_scripts/story_things
python seed_enchanted_library.py          # Verbose
python seed_enchanted_library.py --json   # JSON output for scripting
```

### 4. Navigate

Visit `/demo/your-demo-slug` — the route, DemoPage, and all components are shared infrastructure.

---

## DemoConfig Interface

```typescript
export interface DemoConfig {
  slug: string       // URL-safe identifier, used in /demo/$slug
  title: string      // Display title in DemoHeader
  description: string // Subtitle text in DemoHeader
  roomId: string     // UUID of seeded room (from seed script output)
  autoRespond: boolean // Default state of auto-respond toggle
}
```

---

## Seed Script Entity Relationships

Understanding the entity graph is critical for writing correct seed scripts:

```
User (authenticated via test.env)
├── owns → Story
├── owns → AgentConfig (x2)
├── owns → Room
│   ├── has → RoomParticipant (agent, slug-based)
│   └── has → RoomStoryProgress → points to UserStoryProgress
└── has → UserPersona → Persona
         └── UserStoryProgress (current_node_id, story_state)
              └── locked to → Story + StoryVersion
```

### Entity Creation Order (dependency graph)

```
1.  Story                          POST /stories
2.  StoryNode[]                    POST /storynodes
3.  StoryStateVariable[]           POST /stories/{id}/versions/{v}/state-schema
4.  NodeChoice[]                   POST /node-choices
5.  Publish Story                  PUT  /stories/{id}/publish
6.  AgentConfig[]                  POST /agents
7.  Room                           POST /rooms (with story_id)
8.  RoomParticipant[]              POST /rooms/{id}/participants
9.  Persona                        POST /personas
10. UserPersona                    POST /user-personas
11. Room Runtime (auto-creates     PUT  /rooms/{id}/runtime
    UserStoryProgress +
    RoomStoryProgress)
```

**Important ordering constraints:**
- State variables must be created **before** publishing (step 3 before step 5)
- Room must reference the story (step 7 needs step 1)
- Runtime initialization needs user_persona_id and published story (step 11 needs steps 5, 10)

### Model Field Quick Reference

| Model | Key Fields | Notes |
|-------|-----------|-------|
| `Story` | id, owner_id, title, description, current_version, published_version, is_published | Publishing is a separate PUT call |
| `StoryNode` | id, story_id, story_version, title, content, is_start_node, is_end_node | Exactly one start node per version |
| `NodeChoice` | id, from_node_id, to_node_id, text, order, requires_state, sets_state | State fields are JSON dicts or None |
| `StoryStateVariable` | id, story_id, story_version, key, value_type, default_value | value_type: "boolean", "string", "number" |
| `Room` | room_id (PK!), title, story_id, creator_id | Note: PK is `room_id`, not `id` |
| `RoomParticipant` | id, room_id, participant_id, participant_type, role, active | participant_id = agent slug for agents |
| `AgentConfig` | id, slug, name, model_name, system_prompt, participation_mode, scope | scope="system" for demos |
| `Persona` | id, name, description | Minimal for demos |
| `UserPersona` | id, user_id, persona_id | Links user to persona |
| `UserStoryProgress` | id, user_persona_id, story_id, story_version, current_node_id, story_state, head_version | Created by room runtime init |
| `RoomStoryProgress` | id, room_id (unique), story_id, story_version, active_progress_id, revision | Created by room runtime init |

---

## Story State & Conditional Branches

The story system supports conditional branching via `requires_state` and `sets_state` on `NodeChoice`:

```python
# A choice that SETS state when taken
{
    "from_node_id": node_a_id,
    "to_node_id": node_b_id,
    "text": "Pick up the sword",
    "sets_state": {"has_sword": True, "strength": 5},  # Merged into story_state
}

# A choice that REQUIRES state to be visible
{
    "from_node_id": node_b_id,
    "to_node_id": node_c_id,
    "text": "Attack with the sword",
    "requires_state": {"has_sword": True},  # Only shown if has_sword is True
}
```

The `get_available_choices()` function in `crud.py` filters choices by `requires_state` — if all key-value pairs in `requires_state` match the current `story_state`, the choice is available.

**Declare state variables** via the state-schema endpoint (before publishing):

```python
session.post(f"{BASE_URL}/stories/{story_id}/versions/{version}/state-schema", json={
    "key": "has_sword",
    "value_type": "boolean",
    "default_value": False,
    "description": "Whether the player has picked up the sword",
})
```

---

## Agent Context Integration

### How Agents See Story State

When an agent is triggered in a room with an active story runtime, `build_room_context()` in `context_provider.py` builds a `StoryRuntimeContext`:

```python
@dataclass
class StoryRuntimeContext:
    current_node_title: str           # "The Restricted Section"
    current_node_content: str         # Full node text
    current_node_type: str | None     # Optional node type tag
    is_end_node: bool                 # True if terminal node
    node_chain: list[str]             # ["Entrance", "Reading Room", "Restricted Section"]
    available_choices: list[str]      # ["Try the hidden door", "Speak with the librarian"]
    story_state: dict[str, Any]       # {"has_key": True}
```

This is formatted into the agent prompt by `build_agent_prompt()`:

```
--- Current Story State ---
Current node: The Restricted Section
Content: Behind a velvet rope, towering shelves hold books...
Path taken: The Library Entrance → The Reading Room → The Restricted Section
Available choices:
  1. Try the hidden door
  2. Speak with the librarian
Story state: has_key=True
---
```

### Context Reset on Rewind/Reset

Because `build_room_context()` queries the **current** `UserStoryProgress` at call-time, rewind/reset automatically means agents see the rewound state. No special "context reset" logic is needed — the next agent invocation reads fresh state.

### Agent System Prompt Tips

For demo agents, reference the context sections explicitly:

```python
system_prompt = """You are the Narrator...

When responding, reference:
- The 'Current node' title and content for scene awareness
- The 'Path taken' to acknowledge the player's journey
- The 'Available choices' to hint at options without spoiling
- The 'Story state' to reference items or flags collected

Keep responses to 2-3 sentences."""
```

---

## Auto-Respond Mechanism

### How It Works

`DemoStoryPanel` watches `runtime.revision` via `useEffect`. When the revision changes (any advance/rewind/reset bumps it), a synthetic message is sent:

| Action | Synthetic Message | Example |
|--------|-------------------|---------|
| Advance | `[Story moved to: {node_title}]` | `[Story moved to: The Reading Room]` |
| Reset | `[Reset story to beginning]` | (revision becomes 0) |
| Rewind | `[Story moved to: {node_title}]` | Same as advance |

### Detection Logic

```typescript
// revision changed = state mutation happened
if (currentRevision !== prevRevisionRef.current) {
  if (currentRevision === 0 && runtime.canReset) {
    // Reset: revision went back to 0
    onSendMessage("[Reset story to beginning]")
  } else if (currentNodeId !== prevNodeIdRef.current) {
    // Node changed: advance or rewind
    onSendMessage(`[Story moved to: ${currentNodeTitle}]`)
  }
}
```

### Agent Trigger

Synthetic messages flow through the normal room message pipeline:
1. `sendMessage()` → POST to `/api/v1/rooms/{room_id}/messages`
2. Backend persists message → emits event → triggers agent runner
3. Agent runner calls `build_room_context()` → gets fresh `StoryRuntimeContext`
4. Agent responds with story-aware context

For agents to respond to synthetic messages, set `participation_mode: "always"` in the AgentConfig.

---

## Extending the Demo System

### Adding a Non-Story Demo

Not all demos need the story runtime. You can replace the left panel:

```typescript
// In a custom DemoPage variant:
<ResizablePanel defaultSize={60} minSize={30}>
  {/* Replace StoryPanel with any interactive component */}
  <YourCustomComponent roomId={config.roomId} />
</ResizablePanel>
```

To support this, extend `DemoConfig`:

```typescript
export interface DemoConfig {
  slug: string
  title: string
  description: string
  roomId: string
  autoRespond: boolean
  panelType?: "story" | "custom"  // Future: choose left panel content
}
```

### Adding Custom Auto-Respond Triggers

The current `DemoStoryPanel` only watches story runtime changes. For other demo types, create a similar wrapper that watches whatever state is relevant and sends synthetic messages.

### Adding a Demo Index Page

Create a listing page at `/demo` (no slug) that shows all available demos:

```typescript
// frontend/src/routes/_layout/demo.index.tsx
import { DEMOS } from "@/config/demos"

// Render a card grid linking to each /demo/{slug}
```

---

## Debugging Checklist

| Symptom | Check |
|---------|-------|
| Demo page shows "not found" | Is slug in `DEMOS` registry? |
| No height / layout broken | Is `/demo/` in `fullBleedRoutes`? |
| Agents don't respond | Are agents' `participation_mode` set to `"always"`? |
| Agents don't see story state | Is room runtime initialized? Does room have `story_id`? |
| Chat shows no messages | Is WebSocket connecting? Check `isConnected` badge. |
| Auto-respond not firing | Is toggle enabled? Is runtime loaded? Check browser console. |
| Story choices not visible | Is runtime initialized? Are `NodeChoice` records created? |
| Conditional choice missing | Does `story_state` satisfy `requires_state`? |
| Seed fails with 400 on state var | Story already published — create state vars before publishing |
| Seed fails with auth error | Check `test.env` credentials and backend is running |
| Agent slug conflict | Agent slugs must be unique — seed creates new ones each run |

---

## Running the Demo End-to-End

```bash
# 1. Ensure backend is running
docker compose up -d  # or: docker compose watch

# 2. Seed the demo (from backend/app/test_scripts/story_things/)
cd backend/app/test_scripts/story_things
python seed_enchanted_library.py

# 3. Copy the room_id from the output into frontend/src/config/demos.ts

# 4. Start frontend (if not using docker compose watch)
cd frontend && npm run dev

# 5. Navigate to the demo
open http://localhost:5173/demo/story-runtime

# 6. Interact
# - Click story choices (left panel)
# - Watch agents respond in chat (right panel)
# - Toggle "Auto-respond" to control agent reactions
# - Use Rewind/Reset controls to test context reset
```

---

## Seed Script Output Format

The seed script returns a structured dict of all generated IDs:

```json
{
  "story_id": "uuid",
  "story_version": 1,
  "node_ids": ["uuid", "uuid", "uuid", "uuid", "uuid"],
  "state_variable_id": "uuid",
  "choice_ids": ["uuid", "uuid", "uuid", "uuid", "uuid", "uuid", "uuid"],
  "published_version": 1,
  "agent_ids": ["uuid", "uuid"],
  "agent_slugs": ["demo-narrator", "demo-guide"],
  "room_id": "uuid",
  "persona_id": "uuid",
  "user_persona_id": "uuid",
  "room_runtime": {
    "active_progress_id": "uuid",
    "revision": 0,
    "current_node_id": "uuid"
  }
}
```

Use `--json` flag for clean output suitable for piping:

```bash
# Capture IDs in another script
ROOM_ID=$(python seed_enchanted_library.py --json | jq -r '.room_id')
```

---

## Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| API-based seeding (not direct DB) | Scripts work without DB access; validates API contracts; server generates IDs |
| Server-generated UUIDs | No hardcoded IDs to maintain; each run creates fresh entities; avoids collision |
| `StoryRuntimeContext` instead of `RoomRuntimePublic` | Agents need text-oriented data (titles, content), not UUIDs and version numbers |
| `useEffect` watching revision instead of intercepting StoryPanel calls | Avoids modifying the existing StoryPanel component |
| Synthetic messages instead of custom events | Reuses the existing message → agent trigger pipeline |
| `participation_mode: "always"` for demo agents | Ensures agents respond to synthetic messages without @mention |
| Room runtime init creates progress records | Single API call handles both `UserStoryProgress` and `RoomStoryProgress` creation |
| `--json` flag on seed scripts | Enables composability — other scripts can parse and reuse generated IDs |
| Importable `seed_*()` functions | Test scripts can call the seeder directly and get IDs back programmatically |
