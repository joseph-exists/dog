# Agent UI (AG-UI) Engineering Reference Card

> Quick reference for integrating, extending, or debugging the Agent-Generated UI component system.

---

## File Structure

```
src/
├── components/AgentUI/
│   ├── index.ts                         # Public API (exports all layers)
│   ├── types.ts                         # All TypeScript interfaces (mirrors backend ag_ui.py)
│   ├── AgentUIRenderer.tsx              # Thin orchestrator (dispatches to primitives)
│   ├── primitives/                      # Individual UI block renderers
│   │   ├── index.ts                     #   Barrel export (12 components)
│   │   ├── UICardBlock.tsx              #   Card with variants (highlight, warning, etc.)
│   │   ├── UIListBlock.tsx              #   Ordered/unordered list with badges
│   │   ├── UITableBlock.tsx             #   Data table with alignment and striping
│   │   ├── UIProgressBlock.tsx          #   Progress bars with colors
│   │   ├── UIActionButtons.tsx          #   Interactive buttons (fires onAction)
│   │   ├── UICodeBlock.tsx              #   Code block with language class
│   │   ├── UIQuoteBlock.tsx             #   Blockquote with attribution
│   │   ├── UIAlertBlock.tsx             #   Dismissible alert with variants
│   │   ├── UICollapsibleBlock.tsx       #   Expandable accordion section
│   │   ├── UITabsBlock.tsx              #   Tabbed content panels
│   │   ├── UIDividerBlock.tsx           #   Separator with optional label
│   │   └── UIPageLayoutPreview.tsx      #   Page layout proposal preview
│   └── content/                         # Composite layout components
│       ├── index.ts                     #   Barrel export
│       ├── AgentUIStack.tsx             #   Renders UIComponent[] with spacing
│       └── AgentUIEmpty.tsx             #   Empty state for panels
├── hooks/
│   └── useAgentUI.ts                    # Extracts UI components from room messages
├── services/
│   └── roomService.ts                   # MessageViewModel carries ui_components
└── components/Room/panels/
    └── A2UIPanel.tsx                    # Room panel showing aggregated agent UI
```

**Backend counterparts:**
```
backend/app/
├── schemas/ag_ui.py                     # Pydantic models (UIComponent, UICard, etc.)
└── services/agent_tools.py              # emit_ui_component() tool function
```

---

## Current User Workflows

### 1. Viewing Agent UI in Chat Messages

When an agent responds with UI components, they render inline below the message text.

**User experience:**
1. User sends a message in a room or chat
2. Agent processes and responds with text + structured UI components
3. UI components render below the agent's text message
4. User sees cards, lists, tables, progress bars, etc. alongside the response

**Technical flow:**
```
Agent tool: emit_ui_component("card", { title: "...", body: "..." })
  → Stored in RoomMessage.ui_components (JSONB)
  → Frontend: MessageViewModel.ui_components[]
  → Rooms/Message.tsx or Chat/Message.tsx renders <AgentUIRenderer> per component
```

**Where it happens:** `src/components/Rooms/Message.tsx:140-149` and `src/components/Chat/Message.tsx:140-149`

### 2. Interacting with Action Buttons

Agents can emit `action_buttons` components with clickable buttons. Currently the action callback is plumbed through the component tree but not yet connected to a handler upstream.

**User experience:**
1. Agent emits action buttons (e.g., "Expand", "Regenerate", "Accept")
2. Buttons render with appropriate styling (primary, secondary, outline, ghost)
3. User clicks a button
4. Action string is passed to `onAction` callback

**Current status:** The `onUiAction` prop is defined on `Message` and `MessageList` components but not yet wired from ChatPanel or the Room route. Action clicks currently no-op.

**Integration point for connecting:** Wire `onUiAction` in the panel/route that renders `MessageList`, and route the action string back to the agent (e.g., via a new message or API call).

### 3. Dismissing Alerts

Agents can emit dismissible alerts (`dismissible: true`).

**User experience:**
1. Agent emits an alert with `dismissible: true`
2. User sees alert with a "×" close button
3. User clicks close → alert disappears (local state only, not persisted)

### 4. Expanding/Collapsing Sections

Agents can emit collapsible sections for optional detail.

**User experience:**
1. Agent emits a collapsible (e.g., "Show details")
2. User clicks the trigger → content expands with animation
3. User clicks again → collapses

### 5. Browsing Tabs

Agents can emit tabbed content for organizing alternatives.

**User experience:**
1. Agent emits tabs (e.g., "Option A", "Option B", "Option C")
2. User clicks between tabs to view different content
3. Default tab is configurable via `default_tab` index

### 6. Viewing Agent UI Panel (A2UIPanel)

The A2UI panel aggregates all UI components from all agents in a room into a persistent, scrollable view.

**User experience:**
1. User opens a room with agent participants
2. User opens the "Agent UI" panel (panel kind: `a2ui`)
3. Panel shows all UI components grouped by agent name with count badges
4. As agents emit new components, they appear in the panel
5. Empty state shown when no agents have emitted components yet

**Where it happens:** `src/components/Room/panels/A2UIPanel.tsx`

**Panel configuration:** The panel is registered as kind `"a2ui"` in the panel system. Display name: "Agent UI". Must be added to room's panel configuration to be visible.

---

## Quick Usage

### Render a Single Component

```tsx
import { AgentUIRenderer } from "@/components/AgentUI"

<AgentUIRenderer
  component={{ type: "card", data: { title: "Hello", body: "World" } }}
  onAction={(action) => console.log("Clicked:", action)}
/>
```

### Render a Stack of Components

```tsx
import { AgentUIStack } from "@/components/AgentUI"

<AgentUIStack
  components={message.ui_components ?? []}
  onAction={(action, component) => handleAction(action, component)}
  spacing="compact"  // "compact" | "normal" | "relaxed"
/>
```

### Use Individual Primitives Directly

```tsx
import { UICardBlock, UIProgressBlock } from "@/components/AgentUI"

<UICardBlock data={{ title: "Status", body: "All good", variant: "success" }} />
<UIProgressBlock data={{ items: [{ label: "Done", value: 75, color: "green" }] }} />
```

### Extract UI Components from Room Messages

```tsx
import { useAgentUI } from "@/hooks/useAgentUI"
import { useRoomMessages } from "@/hooks/useRoomMessages"

function MyPanel({ roomId }: { roomId: string }) {
  const { messages } = useRoomMessages(roomId)
  const { entries, byAgent, hasComponents, count } = useAgentUI({
    messages: messages ?? [],
  })

  // entries: flat chronological list of AgentUIEntry
  // byAgent: Map<agentName, AgentUIEntry[]>
  // hasComponents: boolean (for conditional rendering)
  // count: total number of components
}
```

---

## Key Types

| Type | Purpose |
|------|---------|
| `UIComponent` | `{ type, data, id?, fallback_text? }` — the envelope |
| `UIComponentType` | Union of 12 component type strings |
| `UICardData` | `{ title, subtitle?, body, footer?, variant?, icon? }` |
| `UIListData` | `{ title?, items: UIListItem[], ordered?, variant? }` |
| `UITableData` | `{ title?, columns: UITableColumn[], rows, striped?, compact? }` |
| `UIProgressData` | `{ title?, items: UIProgressItem[], show_percentage? }` |
| `UIActionButtonsData` | `{ buttons: UIActionButton[], layout? }` |
| `UICodeData` | `{ code, language?, title?, line_numbers? }` |
| `UIQuoteData` | `{ text, attribution?, variant? }` |
| `UIAlertData` | `{ title?, message, variant?, dismissible? }` |
| `UICollapsibleData` | `{ title, content, default_open?, icon? }` |
| `UITabsData` | `{ tabs: UITabData[], default_tab? }` |
| `UIDividerData` | `{ label?, variant? }` |
| `UIPageLayoutPreviewData` | `{ entity_type, entity_id, layout_json, summary? }` |
| `AgentUIEntry` | Hook output: `{ component, agentName, messageId, timestamp }` |

---

## Component Variant Matrix

| Component | Variants | Interactive |
|-----------|----------|-------------|
| `card` | default, highlight, warning, success, info | No |
| `list` | default, compact, detailed | No |
| `table` | striped/compact flags | No |
| `progress` | blue, green, yellow, red, purple (per bar) | No |
| `action_buttons` | horizontal, vertical, grid layout | **Yes** (fires `onAction`) |
| `code` | Any language class | No |
| `quote` | default, highlight, subtle | No |
| `alert` | info, success, warning, error | **Yes** (dismissible) |
| `collapsible` | default_open flag | **Yes** (expand/collapse) |
| `tabs` | default_tab index | **Yes** (tab switching) |
| `divider` | solid, dashed, dotted | No |
| `page_layout_preview` | — | No |

---

## Data Flow

### Agent → Frontend (How Components Are Created)

```
1. Agent calls emit_ui_component(type, data, fallback_text?)
     ↓
2. UIComponent added to AgentDeps.ui_components list
     ↓
3. Agent run completes → agent_runner collects ui_components
     ↓
4. emit_message() publishes room_message.agent event with ui_components
     ↓
5. Event handler stores in RoomMessage.ui_components (PostgreSQL JSONB)
     ↓
6. API returns RoomMessagePublic with ui_components field
     ↓
7. Frontend transforms to MessageViewModel.ui_components: UIComponent[]
     ↓
8. Message component renders <AgentUIRenderer> per component
```

### Frontend Rendering

```
MessageViewModel.ui_components[]
    │
    ├─ Inline in messages ─→ <AgentUIRenderer component={c} />
    │                              ↓ switch(type)
    │                         <UICardBlock> / <UIListBlock> / ...
    │
    └─ A2UIPanel ─→ useRoomMessages() → useAgentUI()
                         ↓ groups by agent
                    <AgentUIStack components={[...]} />
                         ↓ iterates
                    <AgentUIRenderer> per component
```

---

## Spacing Convention

**Primitives have NO margin/spacing.** Parent containers control spacing:

| Context | Spacing Applied By |
|---------|-------------------|
| Inline in message | `<div className="mt-3 space-y-2">` in Message.tsx |
| AgentUIStack | `space-y-1` / `space-y-3` / `space-y-4` via `spacing` prop |
| Direct usage | Consumer applies their own spacing |

This enables the same primitives to work at different densities without modification.

---

## Extending the System

### Adding a New Component Type

1. **Backend:** Add Pydantic model to `backend/app/schemas/ag_ui.py`
2. **Backend:** Add type to `UIComponentType` literal union in same file
3. **Frontend types:** Add data interface to `src/components/AgentUI/types.ts`
4. **Frontend types:** Add type string to `UIComponentType` union
5. **Frontend primitive:** Create `src/components/AgentUI/primitives/UIMyBlock.tsx`
6. **Barrel export:** Add to `primitives/index.ts` (alphabetical order)
7. **Renderer:** Add case to switch in `AgentUIRenderer.tsx`
8. **Top-level export:** Add to `index.ts`

### Using a Primitive Standalone

All primitives accept a single `{ data: UIXxxData }` prop (except `UIActionButtons` which also takes `onAction`). Import directly:

```tsx
import { UICardBlock } from "@/components/AgentUI/primitives"

// Use anywhere — no renderer needed
<UICardBlock data={{ title: "My Card", body: "Content", variant: "info" }} />
```

### Creating a Custom Aggregation View

Use the `useAgentUI` hook with your own rendering:

```tsx
import { useAgentUI } from "@/hooks/useAgentUI"

function RecentAgentCards({ messages }) {
  const { entries } = useAgentUI({ messages })

  // Filter to just cards from the last 5 minutes
  const recentCards = entries
    .filter((e) => e.component.type === "card")
    .filter((e) => isRecent(e.timestamp, 5))

  return recentCards.map((entry) => (
    <UICardBlock key={entry.component.id} data={entry.component.data} />
  ))
}
```

### Wiring Action Buttons to Agents

The `onAction` callback currently receives an action string (e.g., `"expand_section"`, `"regenerate"`). To complete the loop:

1. In `ChatPanel` or Room route, wire `onUiAction` to `MessageList`:
   ```tsx
   <MessageList
     onUiAction={(action, message) => {
       // Send action back as a user message or API call
       sendMessage(`[Action: ${action}]`, { targetAgent: message.agent_name })
     }}
   />
   ```

2. Agent receives action in next conversation turn and responds accordingly.

---

## Backend: Creating UI Components in Agents

### Using the Tool

```python
from pydantic_ai import RunContext
from app.services.agent_tools import emit_ui_component

# In agent tool or system prompt, agent calls:
emit_ui_component(ctx, "card", {
    "title": "Analysis Complete",
    "body": "Found 3 issues...",
    "variant": "warning",
})
```

### Using Helper Functions

```python
from app.schemas.ag_ui import make_card, make_alert, make_list, make_action_buttons

components = [
    make_card("Status", "Everything looks good", variant="success"),
    make_list(["Item 1", "Item 2", "Item 3"], title="Results"),
    make_action_buttons(
        ("Expand", "expand_details"),
        ("Regenerate", "regenerate"),
    ),
]
```

### AgentDeps Integration

```python
@dataclass
class AgentDeps:
    session: AsyncSession
    room_id: uuid.UUID
    current_agent_slug: str
    ui_components: list[UIComponent] | None = None

    def add_ui_component(self, component: UIComponent) -> None:
        if self.ui_components is None:
            self.ui_components = []
        self.ui_components.append(component)
```

---

## Debugging Tips

| Symptom | Check |
|---------|-------|
| Components not rendering | Verify `message.ui_components` is not null in React DevTools |
| Fallback text showing | Component type not in `UIComponentType` union — check for typos |
| Action buttons do nothing | `onUiAction` prop is not wired in parent MessageList/ChatPanel |
| A2UIPanel shows empty | No agent messages with `ui_components` in the room yet |
| A2UIPanel not visible | Panel kind `"a2ui"` must be in room's panel configuration |
| Components render without spacing | Use `AgentUIStack` or wrap in `space-y-*` container |
| TypeScript errors on data | Data arrives as `Record<string, unknown>` — cast through `unknown` |
| New component type not rendering | Add case to `AgentUIRenderer.tsx` switch + import from primitives |
| Components render in wrong order | `ui_components` array order is preserved from backend |

---

## Query Keys

The A2UIPanel uses room messages which are cached under:
```ts
["room-messages", roomId]
```

No separate query for UI components — they're part of the message data. When new messages arrive (via polling or WebSocket), UI components update automatically.
