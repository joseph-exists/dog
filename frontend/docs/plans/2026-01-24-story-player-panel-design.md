# StoryPlayerPanel Design

## Summary

Add a solo/local story player panel to the Room panels system. Players can play through
stories attached to a room, making choices locally without server round-trips. Story
progression emits events to the room so agents can react to narrative context.

## Panel Registration

- **Kind**: `storyPlayer`
- **Display name**: "Story Player"
- **Coexists with**: `storyRuntime` (server-managed shared player, already exists)

## Props Interface

```typescript
interface StoryPlayerPanelProps {
  storyId: string
  onStoryEvent?: (event: StoryProgressEvent) => void
}

interface StoryProgressEvent {
  type: "choice_made" | "story_started" | "story_ended" | "story_restarted" | "story_rewound"
  nodeTitle: string
  choiceText?: string
  isEndNode?: boolean
}
```

## Data Flow

1. Panel mounts → `useStoryEditor(storyId)` fetches story/nodes/choices
2. Player interacts → local state updates (currentNodeId, playerState, history)
3. Each interaction → calls `onStoryEvent()` → room sends WebSocket message
4. Agents in room see story context in chat → can respond narratively

## Events Emitted

| Event | Trigger | Message Format |
|-------|---------|----------------|
| `story_started` | Player begins or restarts | `[Story: started "Title"]` |
| `choice_made` | Player selects a choice | `[Story: chose "X" → NodeTitle]` |
| `story_ended` | Player reaches end node | `[Story: reached ending "Title"]` |
| `story_rewound` | Player undoes a choice | `[Story: rewound to "NodeTitle"]` |
| `story_restarted` | Player resets | `[Story: restarted]` |

## Layout (Panel Context)

```
┌─ PanelContainer("Story Player") ─────┐
│  [Header: story title + undo/restart] │
│  ┌─ Scrollable content ─────────────┐ │
│  │  Node title                       │ │
│  │  Node content (html/text/json)    │ │
│  │  ─────────────                    │ │
│  │  "What do you do?"                │ │
│  │  [ Choice 1               → ]    │ │
│  │  [ Choice 2               → ]    │ │
│  │  ─────────────                    │ │
│  │  ▸ Debug: State (2)              │ │
│  │  ▸ Debug: History (5)            │ │
│  └───────────────────────────────────┘ │
└────────────────────────────────────────┘
```

## Files

- **New**: `frontend/src/components/Room/panels/StoryPlayerPanel.tsx`
- **Modified**: `frontend/src/components/Room/panels/index.ts` (export)
- **Modified**: `frontend/src/routes/_layout/r.$roomId.tsx` (register in panelComponents)
- **Modified**: `frontend/src/services/panelService.ts` (display name)

## Key Differences from StoryPreview

- No `onExit` prop (panel lifecycle)
- Wrapped in `PanelContainer` (no standalone header)
- Debug panel = collapsible sections at bottom (not sidebar)
- Emits room events on player actions
- Fetches own data via `useStoryEditor` hook
