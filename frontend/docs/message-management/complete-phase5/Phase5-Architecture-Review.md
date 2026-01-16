# Phase 5 Frontend Architecture Review

## Overview

This document reviews the Phase 5 Message Management implementation plan against:
1. **Minimog.md** - AG-UI protocol integration and event-sourcing architecture
2. **FrontendRULES.md** - Frontend development patterns and best practices
3. **ComponentDevelopmentWalkthrough.md** - Component organization strategy

## Executive Summary

### ✅ Strengths
- Strong adherence to React Query patterns for state management
- Proper component separation (hooks, UI components, mutations)
- Event-driven WebSocket integration aligns with event-sourcing backend
- Authorization patterns match backend implementation

### ⚠️ Areas Requiring Alignment

**1. AG-UI Protocol Integration** (Critical)
**2. Component Organization** (Moderate)
**3. Filter Implementation Strategy** (Minor)

---

## Critical Issue #1: AG-UI Protocol Compliance

### Current State (Phase 5 Plan)

The plan uses **custom WebSocket event handlers** that directly parse backend events:

```typescript
function handleRoomEvent(event: WebSocketMessage) {
  if (event.type !== 'event') return

  switch (event.event_type) {
    case 'message.edited':
      updateMessageInCache(event.payload.message_id, {
        content: event.payload.new_content,
        // ...
      })
  }
}
```

### Minimog.md Specification

From Minimog.md, the **AG-UI Protocol** (AP4) requires:

```typescript
// C3.1 AG-UI WebSocket Protocol
// Connection: ws://localhost:8000/ui/session

// Handshake (Client → Server):
{
  "auth": { "token": "jwt_token" },
  "room_id": "uuid",
  "last_sequence": 0  // For replay
}

// Event (Server → Client):
{
  "type": "event",
  "sequence": 123,
  "event_type": "message.user",
  "payload": { ... },
  "created_at": "2025-01-01T..."
}
```

**Key Requirements from Minimog.md:**
1. WebSocket endpoint: `/ui/session` (not custom endpoints)
2. Handshake protocol with JWT auth and `last_sequence` for reconnection
3. Sequence-based replay for missed events
4. Standardized event envelope format

### ⚠️ Alignment Issues

**Issue 1.1: WebSocket Connection Pattern**
- **Current**: Phase 5 plan doesn't specify how to establish AG-UI compliant connection
- **Required**: Implement AG-UI handshake with `last_sequence` tracking
- **Impact**: Reconnection and event replay won't work correctly

**Issue 1.2: Sequence Tracking**
- **Current**: Plan doesn't mention tracking `room_sequence` for replay
- **Required**: Client must track last received sequence and request replay on reconnect
- **Impact**: Users will miss events if connection drops

**Issue 1.3: Event Type Handling**
- **Current**: Handles message management events correctly
- **Required**: Ensure compatibility with full AG-UI event catalog
- **Impact**: ✅ No conflict - our events are additive to AG-UI spec

### 🎯 Recommended Changes

**Change 1.1: Create AG-UI WebSocket Hook**

```typescript
// frontend/src/hooks/useAGUISession.ts

interface AGUISessionOptions {
  roomId: string
  onEvent: (event: AGUIEvent) => void
  onReconnect?: () => void
}

export function useAGUISession({ roomId, onEvent, onReconnect }: AGUISessionOptions) {
  const { user } = useAuth()
  const [lastSequence, setLastSequence] = useState(() => {
    // Load from localStorage for persistence across page reloads
    return parseInt(localStorage.getItem(`room-${roomId}-last-seq`) || '0')
  })

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/ui/session`)

    ws.onopen = () => {
      // AG-UI handshake
      ws.send(JSON.stringify({
        auth: { token: user.token },
        room_id: roomId,
        last_sequence: lastSequence  // Request replay from this point
      }))
    }

    ws.onmessage = (msg) => {
      const event = JSON.parse(msg.data)

      if (event.type === 'event') {
        // Update last sequence
        setLastSequence(event.sequence)
        localStorage.setItem(`room-${roomId}-last-seq`, String(event.sequence))

        // Forward to event handler
        onEvent(event)
      }
    }

    ws.onclose = () => {
      // Reconnect with replay
      if (onReconnect) onReconnect()
    }

    return () => ws.close()
  }, [roomId, lastSequence])

  return { lastSequence }
}
```

**Change 1.2: Update WebSocket Event Handler**

Replace direct event parsing with AG-UI compliant handler:

```typescript
// frontend/src/components/Rooms/hooks/useRoomEvents.ts

export function useRoomEvents(roomId: string) {
  const queryClient = useQueryClient()

  const handleEvent = useCallback((event: AGUIEvent) => {
    // Event catalog from Minimog.md
    switch (event.event_type) {
      // Core AG-UI events
      case 'room.created':
      case 'room.updated':
        queryClient.invalidateQueries(['rooms', roomId])
        break

      case 'participant.joined':
      case 'participant.left':
        queryClient.invalidateQueries(['rooms', roomId, 'participants'])
        break

      case 'room_message.user':
      case 'room_message.agent':
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
        break

      // Phase 5 message management events
      case 'message.edited':
        updateMessageInCache(event.payload.message_id, {
          content: event.payload.new_content,
          edited_at: event.created_at,
          edited_by: event.payload.edited_by
        })
        break

      case 'message.pinned':
        updateMessageInCache(event.payload.message_id, {
          is_pinned: true,
          pinned_at: event.created_at,
          pinned_by: event.payload.pinned_by,
          active_for_context: true
        })
        break

      // ... other message management events
    }
  }, [queryClient, roomId])

  // Use AG-UI session hook
  useAGUISession({
    roomId,
    onEvent: handleEvent,
    onReconnect: () => {
      // Refresh entire room state on reconnect
      queryClient.invalidateQueries(['rooms', roomId])
    }
  })
}
```

---

## Issue #2: Component Organization Alignment

### Current State (Phase 5 Plan)

Proposed component structure:

```
frontend/src/components/Rooms/
├── MessageList.tsx
├── PinnedMessagesSection.tsx
├── MessageItem.tsx
├── MessageActionMenu.tsx
├── EditMessagePanel.tsx
├── MessageFilters.tsx
└── hooks/
    ├── useMessageFilters.ts
    ├── useMessageMutations.ts
    └── useRoomPermissions.ts
```

### ComponentDevelopmentWalkthrough.md Guidance

**Component Categories:**
1. **Feature-specific** (`src/components/Rooms/`) - ✅ Correct
2. **Common** (`src/components/Common/`) - Reusable across features
3. **UI primitives** (`src/components/ui/`) - Design system elements

### ⚠️ Alignment Issues

**Issue 2.1: MessageFilters Component**
- **Current**: Placed in `Rooms/`
- **Question**: Will other features need filtering UI?
- **Recommendation**: Consider `Common/FilterBar.tsx` with room-specific wrapper

**Issue 2.2: EditMessagePanel (Drawer)**
- **Current**: Slide-out drawer in `Rooms/`
- **Question**: Room-specific or reusable pattern?
- **Recommendation**: If pattern is reusable, extract drawer wrapper to `Common/`

**Issue 2.3: Status Badges**
- **Current**: Inline in MessageItem
- **Question**: Will edited/pinned badges be used elsewhere?
- **Recommendation**: Consider `ui/status-badge.tsx` for design system consistency

### 🎯 Recommended Changes

**Change 2.1: Refactor Filter Component**

```
# Reusable filter bar
frontend/src/components/Common/FilterToolbar.tsx

# Room-specific filter logic
frontend/src/components/Rooms/MessageFilters.tsx
  - Wraps FilterToolbar with room-specific options
  - Uses useMessageFilters hook
```

**Change 2.2: Extract Status Badges**

```typescript
// frontend/src/components/ui/message-badge.tsx

export type MessageBadgeVariant = 'edited' | 'pinned' | 'active' | 'inactive'

export interface MessageBadgeProps {
  variant: MessageBadgeVariant
  timestamp?: string
}

export const MessageBadge = ({ variant, timestamp }: MessageBadgeProps) => {
  const config = {
    edited: { icon: FaEdit, color: 'gray.500', label: 'Edited' },
    pinned: { icon: FaThumbtack, color: 'yellow.600', label: 'Pinned' },
    active: { icon: FaCheckCircle, color: 'green.500', label: 'Active' },
    inactive: { icon: FaCircle, color: 'gray.400', label: 'Inactive' }
  }[variant]

  return (
    <Badge
      display="inline-flex"
      alignItems="center"
      gap={1}
      fontSize="xs"
      color={config.color}
    >
      <Icon as={config.icon} />
      {config.label}
      {timestamp && <Tooltip content={timestamp}>(hover)</Tooltip>}
    </Badge>
  )
}
```

**Change 2.3: Component Structure**

**KEEP in `Rooms/` (Feature-Specific):**
- `MessageList.tsx` - Room message container
- `MessageItem.tsx` - Room message rendering
- `MessageActionMenu.tsx` - Room-specific actions
- `PinnedMessagesSection.tsx` - Room pinned messages

**MOVE to `Common/`:**
- `EditMessagePanel.tsx` → `Common/EditDrawer.tsx` (generic drawer pattern)

**CREATE in `ui/`:**
- `ui/message-badge.tsx` - Reusable badge component
- `ui/filter-toolbar.tsx` - Generic filter controls (if reusable)

---

## Issue #3: Filter Implementation Strategy

### Current State (Phase 5 Plan)

**Filter Persistence:** localStorage per room
**Filter Application:** Server-side query parameters

```typescript
// Current approach
const { data } = useQuery({
  queryKey: ['rooms', roomId, 'messages', filters],
  queryFn: () => RoomsService.getMessages({
    roomId,
    activeForContext: filters.activeForContext,
    isPinned: filters.isPinned,
    // ...
  })
})
```

### FrontendRULES.md Guidance

**Rule 2 - State Management:**
- React Query for server state
- Local state for UI state
- localStorage for user preferences (✅ Aligns)

**Rule 8 - Performance:**
- Implement pagination for long lists
- Avoid unnecessary re-renders

### ⚠️ Alignment Issues

**Issue 3.1: Server-Side Filtering Decision**
- **Current**: All filtering via backend API
- **Question**: Does backend support all filter parameters?
- **Impact**: Need to verify GET /messages endpoint accepts filter params

**Issue 3.2: Filter Performance**
- **Current**: Re-fetches on every filter change
- **Concern**: May cause excessive API calls
- **Recommendation**: Consider debouncing filter changes

### 🎯 Recommended Changes

**Change 3.1: Verify Backend Filter Support**

Check if backend GET endpoint supports:
- `?active_for_context=true/false`
- `?is_pinned=true/false`
- `?sender_type=user/agent`
- `?sender_id=<uuid>`

If NOT supported, add backend query parameters or use client-side filtering for some filters.

**Change 3.2: Debounce Filter Changes**

```typescript
// frontend/src/components/Rooms/hooks/useMessageFilters.ts

export function useMessageFilters(roomId: string) {
  const [filters, setFilters] = useState<MessageFilters>(/* ... */)
  const [debouncedFilters, setDebouncedFilters] = useState(filters)

  // Debounce filter changes to avoid excessive API calls
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedFilters(filters)
    }, 300) // 300ms debounce

    return () => clearTimeout(timer)
  }, [filters])

  return {
    filters,           // For UI state
    debouncedFilters,  // For API queries
    updateFilter,
    clearFilters
  }
}

// In MessageList component:
const { debouncedFilters } = useMessageFilters(roomId)

const { data } = useQuery({
  queryKey: ['rooms', roomId, 'messages', debouncedFilters],  // Use debounced
  queryFn: () => RoomsService.getMessages({ roomId, ...debouncedFilters })
})
```

---

## Issue #4: AG-UI Button Options (Future Consideration)

### Minimog.md Specification

```typescript
// P4 - Messages table
button_options JSONB  // [{label, value, style}] for AG-UI
```

**From Minimog.md F4.1:**
> "Agents must be able to present button options in responses"

### Current Phase 5 Plan

**No mention of button rendering** in message management UI.

### 🎯 Recommended Addition

While not required for Phase 5, consider future-proofing MessageItem:

```typescript
// frontend/src/components/Rooms/MessageItem.tsx

interface ButtonOption {
  label: string
  value: string
  style: 'primary' | 'secondary'
}

const MessageItem = ({ message }: { message: Message }) => {
  // ... existing code

  return (
    <Box>
      <Text>{message.content}</Text>

      {/* AG-UI button options (Phase 6+) */}
      {message.button_options && (
        <HStack mt={2}>
          {message.button_options.map((btn: ButtonOption) => (
            <Button
              key={btn.value}
              size="sm"
              variant={btn.style === 'primary' ? 'solid' : 'outline'}
              onClick={() => handleButtonClick(btn.value)}
            >
              {btn.label}
            </Button>
          ))}
        </HStack>
      )}
    </Box>
  )
}
```

---

## Summary of Recommendations

### High Priority (Must Fix)

1. **✅ Implement AG-UI WebSocket handshake** with sequence tracking
2. **✅ Create `useAGUISession` hook** for compliant connection handling
3. **✅ Add sequence-based event replay** for reconnection resilience

### Medium Priority (Should Fix)

4. **⚠️ Verify backend filter parameters** are implemented
5. **⚠️ Debounce filter changes** to avoid excessive API calls
6. **⚠️ Extract status badges** to `ui/` for reusability

### Low Priority (Consider)

7. **💡 Move EditDrawer** to `Common/` if pattern is reusable
8. **💡 Add button_options rendering** for future AG-UI compliance
9. **💡 Create generic FilterToolbar** in `Common/`

---

## Revised Component Structure

```
frontend/src/
├── components/
│   ├── Rooms/                         # Feature-specific
│   │   ├── MessageList.tsx           # Container with filters
│   │   ├── MessageItem.tsx           # Message rendering
│   │   ├── MessageActionMenu.tsx     # Action dropdown
│   │   ├── MessageFilters.tsx        # Room-specific filter wrapper
│   │   ├── PinnedMessagesSection.tsx # Pinned messages display
│   │   └── hooks/
│   │       ├── useMessageFilters.ts  # Filter state + localStorage
│   │       ├── useMessageMutations.ts # CRUD mutations
│   │       ├── useRoomPermissions.ts  # Permission checks
│   │       └── useRoomEvents.ts      # AG-UI event handler (NEW)
│   │
│   ├── Common/                        # Reusable components
│   │   ├── EditDrawer.tsx            # Generic slide-out drawer (NEW)
│   │   └── FilterToolbar.tsx         # Generic filter controls (OPTIONAL)
│   │
│   └── ui/                            # Design system
│       └── message-badge.tsx         # Edited/pinned/active badges (NEW)
│
└── hooks/
    └── useAGUISession.ts             # AG-UI WebSocket hook (NEW)
```

---

## Implementation Checklist

### Phase 5.1: AG-UI Compliance (Priority 1)

- [ ] Create `useAGUISession.ts` hook with handshake + sequence tracking
- [ ] Create `useRoomEvents.ts` hook for event handling
- [ ] Test WebSocket reconnection and event replay
- [ ] Verify all message management events integrate correctly
- [ ] Store `last_sequence` in localStorage for persistence

### Phase 5.2: Component Organization (Priority 2)

- [ ] Create `ui/message-badge.tsx` for status badges
- [ ] Extract EditMessagePanel → `Common/EditDrawer.tsx` (optional)
- [ ] Review filter components for Common extraction (optional)

### Phase 5.3: Performance & UX (Priority 3)

- [ ] Add filter debouncing (300ms)
- [ ] Verify backend supports all filter parameters
- [ ] Add loading skeletons for filter state transitions
- [ ] Test with 100+ messages for performance

### Phase 5.4: Future-Proofing (Priority 4)

- [ ] Add `button_options` rendering to MessageItem
- [ ] Document AG-UI event catalog for future events
- [ ] Plan for agent handoff UI (Minimog.md F5)

---

## Conclusion

The Phase 5 plan is **fundamentally sound** but needs critical updates for **AG-UI protocol compliance**. The component organization aligns well with frontend best practices, with minor opportunities for reusability improvements.

### Key Takeaways:

1. **AG-UI Integration**: Must implement handshake, sequence tracking, and replay
2. **Component Structure**: Mostly correct, minor refinements recommended
3. **Performance**: Add debouncing, verify backend filter support
4. **Future-Proofing**: Plan for button options and agent handoff UI

By addressing the high-priority items, Phase 5 will integrate seamlessly with the Minimog architecture and enable a robust, production-ready message management experience.
