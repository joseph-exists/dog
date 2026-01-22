# StoryPanel Implementation Design

> Room runtime panel for playing through stories - the "player" view distinct from StoryEditorPanel (authoring).

## Overview

The StoryPanel displays the live room runtime state and allows users to advance/rewind through a story. It follows a hybrid UX approach: immersive player view by default with collapsible operator controls (node chain, state inspector, runtime controls).

## Component Architecture

### Hierarchy

```
StoryPanel (main panel component)
├── StoryPanelHeader (title, story info, operator toggle)
├── NodeDisplay (current node content - immersive view)
│   └── NodeContent (renders markdown/text with content_format)
├── ChoiceList (available choices as action buttons)
│   └── ChoiceItem (individual choice with optional state badge)
├── NodeChainCollapsible (operator section - collapsible)
│   └── NodeChainItem (individual node in the chain)
├── StoryStateCollapsible (operator section - collapsible)
│   └── StateDisplay (JSON viewer for story_state)
└── RuntimeControls (rewind/reset controls - collapsible)
```

### Data Flow

```
RoomRuntimeService.readRoomRuntime(roomId)
    ↓
useRoomRuntime hook (TanStack Query)
    ↓
RoomRuntimeViewModel (transformed for UI)
    ↓
StoryPanel (renders sub-components)
```

## Panel States

1. **No story attached** - PlaceholderContent with BookOpen icon, "Attach a story to begin"
2. **Loading** - PlaceholderContent with spinning Loader2 icon
3. **Error** - PlaceholderContent with AlertCircle, error message, Retry button
4. **Active runtime** - Full panel with all sections
5. **End node reached** - Final content, no choices, "Story Complete" badge, Reset prominent

## Visual Layout (Active Runtime)

```
┌─────────────────────────────────────────┐
│ [StoryTitle]          v3 │ ⚙️ Operator │  ← Header
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      [Current Node Title]       │   │  ← NodeDisplay
│  │      Node content rendered      │   │     (scrollable)
│  │      with proper formatting...  │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ▶ Try the key          [+trust]│   │  ← ChoiceList
│  │ ▶ Look around                  │   │
│  │ ▶ Go back              [locked]│   │
│  └─────────────────────────────────┘   │
│                                         │
│  ▼ Node Chain (3)                       │  ← Collapsible (closed)
│  ▼ Story State                          │  ← Collapsible (closed)
│  ▼ Runtime Controls                     │  ← Collapsible (closed)
└─────────────────────────────────────────┘
```

## Component Abstractions

### NodeDisplay

```typescript
interface NodeDisplayProps {
  node: NodeViewModel
  onNodeClick?: (node: NodeViewModel) => void
  actions?: React.ReactNode
  renderContent?: (content: string, format: ContentFormat) => React.ReactNode
}
```

- `onNodeClick` enables future: expand to modal, open NodeCard popover
- `renderContent` override enables custom formats, rich content

### ChoiceItem

```typescript
interface ChoiceItemProps {
  choice: ChoiceViewModel
  isAvailable: boolean
  unavailableReason?: string
  isLoading?: boolean
  onSelect: (choice: ChoiceViewModel) => void
  onInspect?: (choice: ChoiceViewModel) => void  // Future: ChoiceCard
  variant?: "button" | "card" | "compact"
}
```

- `onSelect` = immediate advance
- `onInspect` = open detail view (future ChoiceCard extension)

### NodeChainItem

```typescript
interface NodeChainItemProps {
  node: NodeViewModel
  isStart: boolean
  isEnd: boolean
  isCurrent: boolean
  onClick?: (node: NodeViewModel) => void
}
```

## Service Layer

### File: `src/services/roomRuntimeService.ts`

**ViewModels:**

```typescript
export interface NodeViewModel {
  id: string
  title: string
  content: string
  contentFormat: ContentFormat | null
  isStartNode: boolean
  isEndNode: boolean
}

export interface ChoiceViewModel {
  id: string
  text: string
  toNodeId: string
  order: number
  requiresState: Record<string, unknown> | null
  setsState: Record<string, unknown> | null
  isAvailable: boolean           // Computed from requires_state
  unavailableReason: string | null
}

export interface RoomRuntimeViewModel {
  roomId: string
  storyId: string
  storyVersion: number
  revision: number

  currentNode: NodeViewModel | null
  nodeChain: NodeViewModel[]
  availableChoices: ChoiceViewModel[]
  storyState: Record<string, unknown>

  hasRuntime: boolean
  isAtEndNode: boolean
  canRewind: boolean
  canReset: boolean
}
```

**Service functions:**
- `toViewModel(runtime, roomId)` - Transform API response
- `getRuntime(roomId)` - Fetch runtime projection
- `startRuntime(roomId, params)` - Start/attach story
- `advance(roomId, choiceId, expectedRevision)` - Select choice
- `rewind(roomId, targetChoiceId, expectedRevision)` - Go back
- `reset(roomId, expectedRevision)` - Restart story

## Hook

### File: `src/hooks/useRoomRuntime.ts`

```typescript
interface UseRoomRuntimeResult {
  runtime: RoomRuntimeViewModel | null
  isLoading: boolean
  error: ApiError | null

  advance: (choiceId: string) => Promise<void>
  rewind: (targetChoiceId: string) => Promise<void>
  reset: () => Promise<void>

  isAdvancing: boolean
  isRewinding: boolean
  isResetting: boolean
  pendingChoiceId: string | null
}
```

**Query key:** `["rooms", roomId, "runtime"]`

## File Structure

### New Files

```
src/
├── services/
│   └── roomRuntimeService.ts
├── hooks/
│   └── useRoomRuntime.ts
└── components/Room/panels/StoryPanel/
    ├── index.ts
    ├── StoryPanel.tsx
    ├── NodeDisplay.tsx
    ├── ChoiceList.tsx
    ├── ChoiceItem.tsx
    ├── NodeChainCollapsible.tsx
    ├── StoryStateCollapsible.tsx
    └── RuntimeControls.tsx
```

### Modified Files

- `src/components/Room/panels/index.ts` - Add StoryPanel export
- `src/components/Room/primitives/PresetPicker.tsx` - Add story_runtime preset

## Implementation Checklist

| # | Task | Output |
|---|------|--------|
| 1 | Create `roomRuntimeService.ts` with ViewModels + transforms | Service file |
| 2 | Create `useRoomRuntime.ts` hook | Hook file |
| 3 | Create `NodeDisplay.tsx` | Presentational component |
| 4 | Create `ChoiceItem.tsx` | Presentational component |
| 5 | Create `ChoiceList.tsx` | Container component |
| 6 | Create `NodeChainCollapsible.tsx` | Operator section |
| 7 | Create `StoryStateCollapsible.tsx` | Operator section |
| 8 | Create `RuntimeControls.tsx` | Operator section |
| 9 | Create `StoryPanel.tsx` | Main panel |
| 10 | Create `StoryPanel/index.ts` barrel | Clean export |
| 11 | Update `panels/index.ts` | Panel available |
| 12 | Add `story_runtime` preset | Preset selectable |
| 13 | Wire up in room route | Full integration |

## shadcn/ui Components Required

- Collapsible
- Button
- Badge
- Tooltip
- AlertDialog
- Skeleton (optional)

## Edge Cases & Error Handling

### Optimistic Concurrency (409 Conflict)
- Pass `expectedRevision` on all mutations
- On 409: Invalidate query, refetch, toast "Story updated by someone else"

### Rapid Click Prevention
- Disable all choices while `isAdvancing` is true
- Show spinner on `pendingChoiceId` only

### Story Detached Mid-Session
- Runtime returns null/404 → show "No Story" state
- Future: WebSocket `room.runtime.cleared` event

### Content Format Handling
- `null` defaults to "text"
- "markdown" uses markdown renderer
- Future: "html" with sanitization

## Testing Checkpoints

- After step 2: Hook returns data correctly
- After step 5: ChoiceList renders in isolation
- After step 9: StoryPanel renders all states
- After step 13: Full flow works in room

## Future Extensions

- **ChoiceCard**: Add `onInspect` callback to ChoiceItem, render modal/popover
- **NodeCard**: Add `onNodeClick` to NodeDisplay/NodeChainItem
- **Rich content**: Swap `renderContent` for embedded media, interactive elements
- **WebSocket**: Subscribe to runtime events for real-time updates
