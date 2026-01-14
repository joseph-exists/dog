# Frontend Migration Plan: Chakra UI → shadcn/Tailwind

## Overview

**Source**: `frontend/` (Chakra UI + React)
**Target**: `frontend-test/` (shadcn + Tailwind + React)
**Strategy**: Big-bang with parallel development
**Focus**: Rooms and Stories components first

## Phase 1: Backend Logic Migration

### High Priority - Move to Backend

#### ✅ 1. Message Filtering (Rooms) - **FIXED**
**Current**: Client filters messages by `activeForContext`, `isPinned`, `senderType`
**Discovery**: Backend route ALREADY defines these params (rooms.py:364-367) but they're NOT passed to `list_room_messages()`!
**Backend Change**: Fix `crud.py` to accept and use these filters - NOT a new feature, just completing existing work
```python
# rooms.py already has:
active_for_context: bool | None = None,
is_pinned: bool | None = None,
sender_type: str | None = None,
sender_id: UUID | None = None,
# BUT crud.list_room_messages() ignores them!
```
**Status**: ✅ COMPLETE


#### ✅ 2. Story Validation (Stories) - **IMPLEMENTED**
**Current**: 136 lines of graph traversal in `storyValidation.ts`
**Backend Change**: New endpoint `POST /api/v1/stories/{id}/validate`
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": ["Node 'X' has no outgoing choices"],
  "node_count": 12,
  "choice_count": 18,
  "start_node_count": 1,
  "end_node_count": 3,
  "orphaned_node_count": 1,
  "state_schema_validation": {...}
}
```
**Benefit**: Single source of truth, prevents invalid publishes via API
**Status**: ✅ COMPLETE
- Endpoint: `POST /api/v1/stories/{id}/validate`
- Location: `backend/app/api/routes/stories.py:158-313`
- Typer CLI: `python main.py stories validate <story_id>`

#### ✅ 3. State Condition Parsing (Stories) - **ALREADY EXISTS**
**Current**: 105 lines of transformation logic in `StateConditionEditor.tsx`
**Backend Change**: Validate and normalize conditions on save
**Benefit**: Type safety, malformed condition prevention
**Status**: ✅ ALREADY COMPLETE (discovered during implementation)
- Endpoint: `GET /api/v1/stories/{story_id}/versions/{version}/state-schema/validate`
- Location: `backend/app/api/routes/stories.py:769-795`
- CRUD function: `crud.get_undefined_variables_in_choices()`
- Typer CLI: `python main.py stories validate-state-schema <story_id>`

#### ✅ 4. Permission Flags (Rooms) - **FIXED**
**Current**: Client calculates `canEdit`, `canDelete`, `canPin` from role
**Backend Change**: Include permission booleans in API responses
```json
{
  "message_id": "...",
  "can_edit": true,
  "can_delete": false,
  "can_pin": true
}
```
**Benefit**: Eliminates permission logic drift between client/server
**Status**: ✅ COMPLETE

#### ✅ 5. Available Agents (Rooms) - **IMPLEMENTED**
**Current**: Hardcoded `AVAILABLE_AGENTS` array in frontend
**Backend Change**: New endpoint `GET /api/v1/agents/available`
**Benefit**: Dynamic agent registry, single source of truth
**Status**: ✅ COMPLETE
- Endpoint: `GET /api/v1/agents/available`
- Location: `backend/app/api/routes/agent_routes.py:44-58`
- Typer CLI: `python main.py agents list-available`

### Medium Priority

#### ✅ 6. Tree Structure (Stories) - **IMPLEMENTED**
**Current**: `treeUtils.ts` builds tree on every render
**Backend Change**: Return pre-structured tree in story response
```json
{
  "root": {
    "id": "uuid",
    "title": "Chapter 1",
    "is_start_node": true,
    "is_end_node": false,
    "level": 0,
    "children": [...]
  },
  "orphaned_nodes": [...],
  "total_nodes": 12,
  "reachable_nodes": 11
}
```
**Note**: Stories use traditional CRUD (not event-sourced like Rooms), so this is safe to implement
**Benefit**: Reduced client computation, cacheable
**Status**: ✅ COMPLETE
- Endpoint: `GET /api/v1/stories/{id}/tree`
- Location: `backend/app/api/routes/stories.py:413-459`
- Typer CLI: `python main.py stories tree <story_id>`

#### ✅ 7. User Display Names (Rooms) - **FIXED**
**Current**: Frontend does N+1 API calls with in-memory cache (`userCache` Map in roomService.ts)
**Challenge**: Backend is event-sourced, stores `sender_id` (UUID), not names
**Options**:
  - **A) JOIN on read** (recommended): Add LEFT JOIN to `list_room_messages()` query
  - **B) Denormalize**: Store name in message projection (violates event-sourcing, stale on name change)
  - **C) Keep current**: Frontend caching works, just optimize batch fetching
**Decision**: Option A - JOIN is acceptable for projections, maintains event purity
**Benefit**: Eliminates N+1 calls while preserving event-sourcing integrity

#### 8. Pagination Cursors (Rooms)
**Current**: Client calculates next cursor from timestamps
**Backend Change**: Return opaque `next_cursor` token
**Benefit**: Supports alternative pagination without client changes

### Low Priority

#### 9. Relative Time Formatting
**Current**: Duplicate `formatTimestamp()` in multiple components
**Backend Change**: Return `relative_time` or `seconds_ago` field
**Benefit**: Consistent formatting, less duplication

#### 10. Default Value Formatting (Stories)
**Current**: `formatDefaultValue()` in StateSchemaEditor
**Backend Change**: Return formatted default in schema response

---

---

## Architectural Alignment Analysis

### Backend Architecture Summary

**Rooms**: Event-sourced via `event_emitter.py`
- Single write-path: `emit_event()` → projections
- Event types: `room.created`, `participant.joined`, `room_message.user`, `message.pinned`, etc.
- Redis pub/sub for real-time delivery (already implemented!)
- Immutable event log with sequence numbers

**Stories**: Traditional CRUD via `crud.py`
- Standard SQLModel operations
- No event sourcing
- Direct database mutations

### Frontend Service Layer Purpose

`roomService.ts` explicitly states:
> "Purpose: Provide a clean, type-safe abstraction over the OpenAPI client...
> Transforms backend response models to frontend ViewModels optimized for UI consumption."

**Migration Impact**: This layer should become THINNER, not eliminated:
- Remove: User lookup/caching (move to backend JOIN)
- Remove: Client-side filtering (already in backend, just unused)
- Keep: Date parsing (TypeScript Date objects)
- Keep: `is_own_message` computation (requires auth context)
- Keep: Type transformations (backend DTO → frontend ViewModel)

### What Already Works (Leverage, Don't Rebuild)

| Feature | Status | Location |
|---------|--------|----------|
| Message filtering | 80% done (params defined, not used) | `rooms.py:364-367` |
| Real-time events | Working | `event_emitter.py` → Redis pub/sub |
| Permission enforcement | Complete | `crud.py` check functions |
| Event replay | Working | `event_emitter.py:755-794` |

### Contradictions Requiring Decisions

| Issue | Options | Recommendation |
|-------|---------|----------------|
| User display names | JOIN vs denormalize vs keep frontend cache | JOIN on read |
| Permission flags in response | Return flags vs let frontend compute | Return flags (single source of truth) |
| Tree structure (Stories) | Backend compute vs frontend compute | Backend (Stories aren't event-sourced) |

---

## Phase 2: Layout & Design Revisitation

### Rooms Components - Design Decisions

#### Current Layout
```
┌─────────────────────────────────────────────┐
│ RoomHeader (title, participants, actions)   │
├──────────────────────────┬──────────────────┤
│                          │                  │
│     MessageList          │ ParticipantList  │
│     (scrollable)         │   (sidebar)      │
│                          │                  │
├──────────────────────────┴──────────────────┤
│ MessageInput                                │
└─────────────────────────────────────────────┘
```

#### Questions to Revisit
1. **Sidebar positioning**: Right sidebar for participants vs collapsible drawer?
2. **Message density**: Should messages be compact or comfortable spacing?
3. **Pinned messages**: Inline section vs floating panel?
4. **Filter placement**: Top bar vs sidebar filters?
5. **Mobile layout**: Stack everything or hide sidebar?

#### Proposed Simplifications
- Remove separate `MessageFilters` component - integrate into header dropdown
- Collapse `PinnedMessagesSection` into a toggle instead of always-visible
- Simplify `ParticipantList` to avatar row, expand on click

### Stories Components - Design Decisions

#### Current Layout (StoryEditor)
```
┌─────────────────────────────────────────────────────┐
│ Header (story title, actions, preview toggle)       │
├───────────┬─────────────────────────┬───────────────┤
│           │                         │               │
│ NodeTree  │     NodeEditor          │ Properties    │
│ (250px)   │     (flexible)          │   Panel       │
│           │                         │   (300px)     │
│           │                         │               │
└───────────┴─────────────────────────┴───────────────┘
```

#### Questions to Revisit
1. **Three-panel layout**: Is it necessary? Could use drawer for properties?
2. **NodeTree width**: Fixed 250px vs resizable?
3. **State schema**: Separate drawer vs inline in properties?
4. **Validation display**: Panel vs toast notifications?
5. **Choice editing**: Modal vs inline editing?

#### Proposed Simplifications
- **Merge PropertiesPanel into header actions** - properties rarely edited
- **Remove StateSchemaDrawer** - integrate into story settings modal
- **Simplify ChoiceEditor** - inline form instead of modal
- **Reduce StateConditionEditor complexity** - simpler condition builder

### Component Consolidation

| Current (28 files) | Proposed |
|--------------------|----------|
| StoryList/ (3 files) | StoryList.tsx, StoryCard.tsx |
| StoryEditor/ (12 files) | StoryEditor.tsx, NodeTree.tsx, NodeEditor.tsx |
| PublishWorkflow/ (4 files) | PublishDialog.tsx |
| StoryPlayer/ (1 file) | StoryPreview.tsx |
| shared/ (8 files) | RichTextEditor.tsx, ConditionBuilder.tsx |

**Target**: 28 files → ~10 files

---

## Phase 3: shadcn Component Mapping

### Direct Replacements

| Chakra | shadcn | Notes |
|--------|--------|-------|
| Button | Button | Same API, use `variant` prop |
| Input | Input | Direct replacement |
| Dialog* | Dialog | Radix-based, similar API |
| Card | Card | Direct replacement |
| Badge | Badge | Direct replacement |
| Tooltip | Tooltip | Direct replacement |
| Checkbox | Checkbox | Direct replacement |
| Table | Table | Direct replacement |
| Drawer* | Sheet | Rename, similar API |

### Custom Components Needed

1. **EmptyState** - No shadcn equivalent, build custom
2. **Field** - Form field wrapper (label + error + helper)
3. **NativeSelect** → **Select** - Upgrade to Radix Select
4. **IconButton** - Use Button with icon, no text

### Tailwind Utility Mapping

```tsx
// Chakra
<Box p={4} bg="gray.100" borderRadius="md" _dark={{ bg: "gray.800" }}>

// Tailwind
<div className="p-4 bg-gray-100 rounded-md dark:bg-gray-800">
```

```tsx
// Chakra
<Flex justify="space-between" align="center" gap={4}>

// Tailwind
<div className="flex justify-between items-center gap-4">
```

```tsx
// Chakra
<Grid templateColumns={{ base: "1fr", md: "repeat(2, 1fr)" }} gap={6}>

// Tailwind
<div className="grid grid-cols-1 md:grid-cols-2 gap-6">
```

---

## Phase 4: Implementation Order

### Week 1: Backend API Changes
- [x] Add message filtering query params *(already existed, just needed wiring)*
- [x] Add story validation endpoint → `POST /stories/{id}/validate`
- [x] Add permission flags to message responses *(completed previously)*
- [x] Add agents list endpoint → `GET /agents/available`
- [x] Add user display names to messages *(completed previously)*
- [x] Add story tree structure endpoint → `GET /stories/{id}/tree`
- [x] Add Typer CLI commands for new endpoints

### Week 2: Frontend Setup
- [X] Initialize frontend-test with Vite + React + TypeScript
- [X] Install and configure Tailwind CSS
- [X] Install shadcn/ui and configure components
- [X] Set up TanStack Query + Router
- [X] Copy over API client generation
- [X] **Leverage existing WebSocket infrastructure** - Backend already publishes to Redis channels `room:{room_id}`

### Week 3: Rooms Migration
- [X] RoomList + RoomCard
- [X] RoomHeader (simplified)
- [X] MessageList + Message (use backend filtering)
- [X] MessageInput
- [X] ParticipantList (simplified)
- [X] Dialogs (AddRoom, EditRoom, AddParticipant)

### Week 4: Stories Migration
- [ ] StoryList + StoryCard
- [ ] StoryEditor (simplified 2-panel)
- [ ] NodeTree + NodeEditor
- [ ] ChoiceEditor (inline)
- [ ] PublishDialog
- [ ] StoryPreview

### Week 5: Polish & Testing
- [ ] Dark mode verification
- [ ] Responsive breakpoints
- [ ] Accessibility audit
- [ ] E2E test updates
- [ ] Performance comparison

---

## File Structure: frontend-test/

```
frontend-test/
├── src/
│   ├── components/
│   │   ├── ui/           # shadcn components
│   │   ├── rooms/
│   │   │   ├── RoomList.tsx
│   │   │   ├── RoomCard.tsx
│   │   │   ├── RoomView.tsx      # combines header, messages, input
│   │   │   ├── Message.tsx
│   │   │   └── dialogs/
│   │   │       ├── AddRoomDialog.tsx
│   │   │       └── EditRoomDialog.tsx
│   │   └── stories/
│   │       ├── StoryList.tsx
│   │       ├── StoryCard.tsx
│   │       ├── StoryEditor.tsx   # simplified 2-panel
│   │       ├── NodeTree.tsx
│   │       ├── NodeEditor.tsx
│   │       ├── StoryPreview.tsx
│   │       └── dialogs/
│   │           └── PublishDialog.tsx
│   ├── hooks/
│   │   ├── useRoom.ts
│   │   ├── useRoomMessages.ts    # simplified (backend filtering)
│   │   ├── useStories.ts
│   │   └── useStoryEditor.ts     # simplified (backend validation)
│   ├── services/
│   │   └── roomService.ts        # slimmed down
│   ├── routes/
│   │   └── ...                   # TanStack Router
│   └── lib/
│       └── utils.ts              # cn() helper
├── tailwind.config.js
├── components.json               # shadcn config
└── package.json
```

---

## Success Metrics

1. **Bundle size**: Target 40% reduction from Chakra
2. **Component count**: Rooms 15→8, Stories 28→10
3. **Client-side logic**: Move 8+ functions to backend
4. **API calls**: Reduce N+1 patterns
5. **Load time**: Faster initial render with less JS

---

## Next Steps

1. ~~**Review this plan** - Confirm priorities and approach~~ ✅
2. ~~**Create backend tickets** - For API changes (Phase 1)~~ ✅ All Phase 1 backend work complete
3. **Scaffold frontend-test** - Initialize project structure
4. **Start with RoomList** - Simplest component to validate approach

---

## Implementation Log

### 2024-01-13: Phase 1 Backend Work Complete

#### New API Endpoints

| Endpoint | Method | Purpose | Location |
|----------|--------|---------|----------|
| `/stories/{id}/validate` | POST | Graph structure validation | `stories.py:158-313` |
| `/stories/{id}/tree` | GET | Pre-computed tree structure | `stories.py:413-459` |
| `/agents/available` | GET | Available agents registry | `agent_routes.py:44-58` |

#### New Models Added (`models.py`)

| Model | Purpose |
|-------|---------|
| `StoryValidationResult` | Validation response with errors, warnings, stats |
| `StoryValidationError` | Individual validation error with context |
| `StoryNodeTree` | Tree structure response |
| `StoryNodeTreeNode` | Individual tree node |
| `AvailableAgent` | Agent definition |
| `AvailableAgentsPublic` | Agents list response |

#### New Typer CLI Commands

| Command | Description |
|---------|-------------|
| `stories validate <id>` | Validate story graph structure |
| `stories tree <id>` | Display story node tree |
| `agents list-available` | List available agents |

#### Frontend Files Now Replaceable

| Frontend File | Lines | Replaced By |
|---------------|-------|-------------|
| `storyValidation.ts` | 136 | `POST /stories/{id}/validate` |
| `treeUtils.ts` | 153 | `GET /stories/{id}/tree` |
| `AVAILABLE_AGENTS` in `AddParticipantDialog.tsx` | 7 | `GET /agents/available` |

**Total frontend code that can be removed**: ~300 lines
