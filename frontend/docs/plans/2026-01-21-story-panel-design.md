# StoryPanel Implementation Design

> Room runtime panel for playing through stories - the "player" view distinct from StoryEditorPanel (authoring).

## Overview

The StoryPanel displays the live room runtime state and allows users to advance/rewind through a 'story'. It follows a hybrid UX approach: immersive user/player view by default with collapsible operator controls (node chain, state inspector, runtime controls).

Important: NodeContent can be designed with full richtext, md, or html capabilities, and can also embed other objects.

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
5. **End node reached** - Final content, no choices, "Story Complete" badge, Reset or Rewind prominent

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
- `onInspect` = open detail view (ChoiceCard)

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

**ViewModels:** (see other ViewModels for requirements and structure)

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
  storyState: Record<string, unknown> | null
  rewindTargets: RewindTargetViewModel[] | null

  hasRuntime: boolean
  isAtEndNode: boolean
  canRewind: boolean
  canReset: boolean
}
```

**Inline documentation requirement:** add terse, in-code comments for any derived fields in ViewModels (e.g., `isAtEndNode`, `canRewind`, `rewindTargets`) so the next implementer can reconstruct the logic quickly.

**Near-term TODO:** `rewindTargets` is not yet available from the runtime projection; treat it as `null` and wire a follow-up task to add a backend surface or projection expansion.

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

## StoryPanel Implementation Checklist (Live)

- [x] Add `src/services/roomRuntimeService.ts` with ViewModels, transforms, and API functions
- [x] Add `src/hooks/useRoomRuntime.ts` hook with query/mutations and state flags
- [x] Add StoryPanel components (NodeDisplay, ChoiceItem, ChoiceList)
- [x] Add operator components (NodeChainCollapsible, StoryStateCollapsible, RuntimeControls)
- [x] Add `StoryPanel.tsx` and barrel `index.ts`
- [x] Export StoryPanel from `src/components/Room/panels/index.ts`
- [x] Add `story_runtime` preset in `src/components/Room/primitives/PresetPicker.tsx`
- [x] Wire StoryPanel into the room route/panel layout

## Story Loader Flow Checklist (Live)

- [x] Add runtime start mutation to `useRoomRuntime` and expose loading state
- [x] Add start-runtime dialog with persona selection in StoryPanel
- [x] Start runtime for rooms with `story_id` using catalog info for version defaults
- [x] If room has no `story_id`, create a new story from room title, create a new room linked to it, and start runtime there

## Revisit This Session

- [x] Runtime start policy: backend enforces owner-only; confirm UI guard vs backend change
- [x] Story loader contract: catalog selection + new room creation when `story_id` is missing
- [x] Persona empty-state: add persona creation path or clear blocking copy
- [ ] Content rendering policy: pick markdown renderer + sanitization rules
- [ ] Rewind behavior: confirm one-step UI copy + disabled state behavior
- [x] Locked choices: confirm hide vs show-with-reason
- [x] Realtime invalidation wiring: subscribe to `room.runtime.*` and invalidate runtime query
- [x] Error handling copy: confirm 404/410/422 user messaging
- [x] Telemetry events: define payload + owner (stubbed for now)
- [ ] Accessibility pass: focus return after advance + collapsible labels

## Testing Notes

- [ ] Add tests for realtime invalidation warnings when runtime events arrive
- Recommended approach: unit-test `shouldInvalidateRuntime` for the event list, then add a lightweight integration test that stubs room event delivery and asserts the runtime query is invalidated once per event.

## shadcn/ui Components Required

- Collapsible
- Button
- Badge
- Tooltip
- AlertDialog
- Skeleton
- Sheet
- 

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

## Additions: Missing Data + Workflow Requirements

### Rewind Target Selection
- Backend rewind requires `target_choice_id`, but the runtime projection only exposes `head_choice_id`.
- UI needs one of:
  - a list of rewind targets (choice history/checkpoints) in the runtime projection, or
  - a dedicated endpoint to fetch rewind targets for a room.
- If only "rewind one step" is supported initially, call it out explicitly and derive the target from backend-provided data.

### Choice Availability + Locked Reasons
- Runtime projection returns `available_choices` only (filtered by `requires_state`).
- If the UX needs locked choices or `unavailableReason`, backend must return:
  - full choice list + evaluation results, or
  - a structured "locked choices" list with reason codes.

### Story Start Persona Requirement
- `PUT /rooms/{room_id}/runtime` requires `user_persona_id`.
- Story loader must provide persona selection or defaulting logic.
- On missing persona: block start and prompt user to select.

### Runtime State Null Handling
- `story_state` and `current_node` can be null in the projection.
- UI should handle null by showing a minimal placeholder instead of a JSON dump.
- `isAtEndNode` should use `current_node?.is_end_node` with null-safe fallback.

### Realtime Updates (Multi-user Sync)
- Subscribe to room events and refetch runtime on:
  - `room.runtime.started`
  - `room.runtime.advanced`
  - `room.runtime.rewound`
  - `room.runtime.reset`
- Do not derive canonical state from events; always refetch.

### Permissions + Write Gating
- Reads require room membership; writes may be owner-only.
- UI should disable advance/rewind/reset if user lacks write permission.
- If permission is denied (403), show a clear "read-only" banner.

### Error Codes Beyond 409
- 404/410: runtime missing or cleared → return to "No Story" state.
- 422: invalid choice or rewind target → show validation toast and refetch.

## Implementation Requirements (Atomic + Sequential)

- [x] 1) Define story loader contract and flow.
Decision: use the existing story/version list source from the Story Editor flow (same service used to populate story pickers). Default to the most recent version of the most recently used story for the room, falling back to the newest story by updated_at. If a runtime already exists, show a confirm dialog with two actions: "Replace Runtime" (PUT runtime with new story + version) and "Cancel" (keep current). Required persona: default to the room owner's primary persona; if unavailable, block start and prompt selection.

- [x] 2) Decide interim rewind behavior before `rewindTargets`.
Decision: support "rewind one step" only. Use `head_choice_id` from runtime (or equivalent API field if exposed) as the target; if missing, disable rewind with helper text "Rewind unavailable yet." Button label: "Rewind one step".

- [x] 3) Specify runtime refresh via realtime events.
Decision: subscribe to room events and invalidate `["rooms", roomId, "runtime"]` on:
`room.runtime.started`, `room.runtime.advanced`, `room.runtime.rewound`, `room.runtime.reset`, `room.runtime.cleared`. No local state patching; always refetch.

- [x] 4) Define write permissions and read-only mode UX.
Decision: if the user lacks write permission, show a read-only banner in the StoryPanel and disable advance/rewind/reset (buttons visible but disabled with tooltip "Read-only room"). On 403 from any mutation, show toast "You don't have permission to modify this runtime" and refetch.

- [x] 5) Finalize content rendering policy.
Decision: use markdown rendering for `content_format: "markdown"` via the existing markdown renderer used in the app (align with Story Editor). `content_format: "html"` is rendered as sanitized HTML (DOMPurify). `content_format: "json"` renders a pretty JSON block with monospace. `null` or unknown formats fall back to plain text rendering.

- [x] 6) Document choice ordering and availability display.
Decision: sort `available_choices` by `order` ascending, then by `id` as a stable tie-breaker. When locked choices are available from the backend, render them as visible-but-disabled; keep unavailable reasons for future rule-state work (hidden vs disabled nuance).

- [x] 7) Lock in node chain window rule.
Decision: show an ancestors-only chain limited to the last 12 nodes (current node included). On mobile, collapse the chain by default and show only the last 5 entries when expanded.

- [x] 8) Enumerate non-409 error behaviors.
Decision: 404/410 from runtime read -> show "No Story" state. 422 from mutations -> toast "That choice is no longer valid" and refetch. Network errors -> show inline error with Retry.

- [x] 9) Add basic telemetry plan.
Decision: emit frontend analytics events:
`story.runtime.attach`, `story.runtime.advance`, `story.runtime.rewind`, `story.runtime.reset` with payload `{ roomId, storyId, storyVersion, revision, choiceId?, targetChoiceId? }`.

- [x] 10) Accessibility pass for core interactions.
Decision: choice buttons are keyboard-focusable in DOM order, Enter/Space triggers selection, focus returns to NodeDisplay title after advance. Collapsibles use shadcn ARIA defaults; ensure trigger buttons have descriptive labels (e.g., "Toggle node chain").

## Testing Checkpoints

- After step 1: Story loader flow has automated unit tests for selection + attach/replace behavior.
- After step 2: Rewind interim behavior has automated unit tests for target selection or blocked UI state.
- After step 3: Realtime refresh wiring has automated unit tests for event-driven invalidation.
- After step 4: Permission gating has automated unit tests for read-only and 403 handling.
- After step 5: Content rendering policy has automated unit tests for markdown/text/json handling.
- After step 6: Choice ordering/availability rules have automated unit tests for sort + display states.
- After step 7: Node chain window rule has automated unit tests for window sizing and mobile fallback.
- After step 8: Error handling has automated unit tests for 404/410/422 responses.
- After step 9: Telemetry events have automated unit tests for payload shape.
- After step 10: Accessibility behaviors have automated unit tests for keyboard and focus flows.


## Next Steps:

- **ChoiceCard**: Add `onInspect` callback to ChoiceItem, render modal/popover
- **NodeCard**: Add `onNodeClick` to NodeDisplay/NodeChainItem
- **Rich content**: Swap `renderContent` for embedded media, interactive elements
