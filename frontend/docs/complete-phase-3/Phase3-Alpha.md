# Phase 3 Alpha: Minimal Viable Room UI

**Goal:** Enable multi-user and multi-LLM chat within the application to validate Phase 4 implementation.

**Status:** Data Layer Complete ✅ | Component Layer In Progress 🚧

---

## User Story (Core Flow)

1. ✅ **Existing user logs in** (functionality previously exists)
2. **User selects "Rooms" from the LeftNav** of the application
3. **User sees a list of rooms** they have access to
4. **User selects a room** they already have access to (backend pre-configured)
5. **User sees conversation history** for that room (existing backend data)
6. **User sends a message** to the room from the Frontend UI
7. **User sees messages from other users** associated with the room
8. **User sees their own messages** in the room
9. **User sees agent responses** appear in the room (via polling)

---

## Prerequisites (Completed ✅)

### Backend (Phase 2)
- ✅ Room API endpoints (`/api/v1/rooms/*`)
- ✅ Message API endpoints (`/api/v1/rooms/{id}/messages`)
- ✅ Participant API endpoints (`/api/v1/rooms/{id}/participants`)
- ✅ Agent integration (StoryAdvisor auto-responds)
- ✅ Event sourcing foundation

### Frontend Data Layer (Phase 3)
- ✅ `RoomService` adapter (`src/services/roomService.ts`)
- ✅ `useRoom` hook (`src/hooks/useRoom.ts`)
- ✅ `useRoomMessages` hook (`src/hooks/useRoomMessages.ts`)
- ✅ Type definitions and ViewModels
- ✅ Optimistic updates, polling, error handling

---

## Component Implementation Checklist

### 1. Navigation Integration

#### 1.1 Add Rooms to Sidebar
**File:** `src/components/Common/SidebarItems.tsx`

**Task:** Add "Rooms" navigation item to sidebar

**Requirements:**
- Add navigation link to `/rooms`
- Use appropriate icon (e.g., `FaComments` from react-icons)
- Follow existing sidebar item pattern

**Acceptance Criteria:**
- [ ] Rooms link appears in sidebar
- [ ] Clicking navigates to `/rooms` route
- [ ] Icon is consistent with app design
- [ ] Active state highlights when on rooms page

**Implementation Hint:**
```tsx
import { FaComments } from "react-icons/fa"

const items: SidebarItemsType = [
  // ... existing items
  {
    title: "Rooms",
    path: "/rooms",
    icon: FaComments,
  },
]
```

---

### 2. Routing Setup

#### 2.1 Room List Route
**File:** `src/routes/_layout/rooms.tsx` (NEW)

**Task:** Create route for room list page

**Requirements:**
- Display list of user's accessible rooms
- Use `RoomService.listRooms()`
- Handle loading and error states
- Navigate to individual room on click

**Acceptance Criteria:**
- [ ] Route renders at `/rooms`
- [ ] Fetches and displays room list
- [ ] Shows loading indicator during fetch
- [ ] Shows error message if fetch fails
- [ ] Clicking room navigates to `/rooms/{roomId}`
- [ ] Shows empty state if no rooms

**Data Flow:**
```tsx
// Use TanStack Query directly for room list
const { data: rooms, isLoading, error } = useQuery({
  queryKey: ['rooms'],
  queryFn: RoomService.listRooms,
});
```

---

#### 2.2 Individual Room Route
**File:** `src/routes/_layout/rooms.$roomId.tsx` (NEW)

**Task:** Create route for individual room view

**Requirements:**
- Display room title, messages, participants
- Use `useRoom(roomId)` hook
- Handle loading states for all data sources
- Enable message sending
- Show polling status

**Acceptance Criteria:**
- [ ] Route renders at `/rooms/{roomId}`
- [ ] Displays room title from metadata
- [ ] Displays message history chronologically
- [ ] Displays message input component
- [ ] Displays participant list (users + agents)
- [ ] Handles authorization errors (403 redirect to /rooms)
- [ ] Handles room not found (404 error display)

**Data Flow:**
```tsx
const { roomId } = useParams();
const {
  room,
  messages,
  participants,
  sendMessage,
  isLoadingRoom,
  isLoadingMessages,
  currentUserRole,
  activeAgents,
} = useRoom(roomId, { enablePolling: true });
```

---

### 3. Room List Components

#### 3.1 RoomList Component
**File:** `src/components/Rooms/RoomList.tsx` (NEW)

**Task:** Display list of rooms with metadata

**Requirements:**
- Map over rooms array
- Display room title, last activity time, participant count
- Handle click to navigate to room
- Show visual indicator for unread (future enhancement)

**Props:**
```tsx
interface RoomListProps {
  rooms: RoomViewModel[];
  onRoomSelect: (roomId: string) => void;
  isLoading?: boolean;
}
```

**Acceptance Criteria:**
- [ ] Displays all rooms in grid or list layout
- [ ] Shows room title
- [ ] Shows last activity timestamp (relative time)
- [ ] Clicking room calls onRoomSelect
- [ ] Empty state when rooms array is empty
- [ ] Loading skeleton during fetch

**Component Type:** Feature-specific (`src/components/Rooms/`)

---

#### 3.2 RoomCard Component
**File:** `src/components/Rooms/RoomCard.tsx` (NEW)

**Task:** Display individual room summary

**Requirements:**
- Display room title
- Display last activity timestamp
- Display participant count (optional for alpha)
- Hover and active states

**Props:**
```tsx
interface RoomCardProps {
  room: RoomViewModel;
  onClick: () => void;
  isActive?: boolean;
}
```

**Acceptance Criteria:**
- [ ] Shows room title prominently
- [ ] Shows formatted last activity time ("2 hours ago")
- [ ] Clickable with hover effect
- [ ] Active state when selected (optional)

**Component Type:** Feature-specific (`src/components/Rooms/`)

---

### 4. Room View Components

#### 4.1 RoomHeader Component
**File:** `src/components/Rooms/RoomHeader.tsx` (NEW)

**Task:** Display room title and metadata

**Requirements:**
- Display room title
- Display participant count
- Display polling status indicator (optional)
- Minimal for alpha - can be enhanced later

**Props:**
```tsx
interface RoomHeaderProps {
  room: RoomViewModel;
  participantCount: number;
  isPolling?: boolean;
}
```

**Acceptance Criteria:**
- [ ] Shows room title
- [ ] Shows participant count badge
- [ ] Fixed at top of room view
- [ ] Responsive design

**Component Type:** Feature-specific (`src/components/Rooms/`)

---

#### 4.2 MessageList Component
**File:** `src/components/Rooms/MessageList.tsx` (NEW)

**Task:** Display chronological message history

**Requirements:**
- Map over messages array
- Distinguish user vs. agent messages visually
- Auto-scroll to bottom on new messages
- Handle empty state (no messages)
- Show "Load More" button if `hasMoreMessages`

**Props:**
```tsx
interface MessageListProps {
  messages: MessageViewModel[];
  hasMore: boolean;
  onLoadMore: () => Promise<void>;
  isLoadingMore: boolean;
  currentUserId: string;
}
```

**Acceptance Criteria:**
- [ ] Displays all messages in chronological order (oldest to newest)
- [ ] User messages aligned right, agent messages aligned left
- [ ] Auto-scrolls to bottom when new message arrives
- [ ] "Load More" button at top if hasMore is true
- [ ] Loading indicator when fetching older messages
- [ ] Empty state with helpful message ("No messages yet")

**Component Type:** Feature-specific (`src/components/Rooms/`)

**Key Implementation Details:**
```tsx
// Auto-scroll logic
const messagesEndRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [messages.length]);

// Render
<VStack>
  {hasMore && <Button onClick={onLoadMore}>Load More</Button>}
  {messages.map(msg => <Message key={msg.message_id} message={msg} />)}
  <div ref={messagesEndRef} />
</VStack>
```

---

#### 4.3 Message Component
**File:** `src/components/Rooms/Message.tsx` (NEW)

**Task:** Display individual message with sender attribution

**Requirements:**
- Display sender name (user or agent)
- Display message content
- Display timestamp
- Visual distinction for user vs. agent
- Visual distinction for own messages

**Props:**
```tsx
interface MessageProps {
  message: MessageViewModel;
  isOwnMessage?: boolean; // Computed from message.is_own_message
}
```

**Acceptance Criteria:**
- [ ] Shows sender name above message
- [ ] Shows message content
- [ ] Shows timestamp (relative format: "2 minutes ago")
- [ ] User messages: Right-aligned, blue background
- [ ] Agent messages: Left-aligned, gray background
- [ ] Own messages: Different visual indicator (darker blue)
- [ ] Handles long messages with word wrap

**Component Type:** Feature-specific (`src/components/Rooms/`)

**Design Pattern (Minimal):**
```tsx
<Box
  alignSelf={message.sender_type === 'user' ? 'flex-end' : 'flex-start'}
  bg={message.is_own_message ? 'blue.600' : message.sender_type === 'agent' ? 'gray.200' : 'blue.500'}
  color={message.sender_type === 'agent' ? 'black' : 'white'}
  borderRadius="md"
  p={3}
  maxW="70%"
>
  <Text fontSize="xs" opacity={0.8}>{message.sender_name}</Text>
  <Text>{message.content}</Text>
  <Text fontSize="xs" opacity={0.6}>{formatTimestamp(message.created_at)}</Text>
</Box>
```

---

#### 4.4 MessageInput Component
**File:** `src/components/Rooms/MessageInput.tsx` (NEW)

**Task:** Text input for sending messages

**Requirements:**
- Controlled input with local state
- Send message on Enter key
- Shift+Enter for line breaks (optional for alpha)
- Clear input after send
- Disable while sending (show loading state)
- Validation (no empty messages)

**Props:**
```tsx
interface MessageInputProps {
  onSendMessage: (content: string) => Promise<void>;
  isSending: boolean;
  disabled?: boolean;
}
```

**Acceptance Criteria:**
- [ ] Text input with placeholder "Type a message..."
- [ ] Send button next to input
- [ ] Enter key sends message
- [ ] Input clears after successful send
- [ ] Disabled state while sending
- [ ] Empty messages not sent (validation)
- [ ] Shows loading indicator on send button while sending

**Component Type:** Feature-specific (`src/components/Rooms/`)

**Implementation Pattern:**
```tsx
const [content, setContent] = useState('');

const handleSend = async () => {
  if (!content.trim() || isSending) return;

  await onSendMessage(content.trim());
  setContent(''); // Clear on success
};

const handleKeyDown = (e: React.KeyboardEvent) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
};
```

---

#### 4.5 ParticipantList Component
**File:** `src/components/Rooms/ParticipantList.tsx` (NEW)

**Task:** Display active participants (users + agents)

**Requirements:**
- Display all active participants
- Distinguish users from agents visually
- Show participant count
- Minimal for alpha (can be enhanced with roles, avatars later)

**Props:**
```tsx
interface ParticipantListProps {
  participants: ParticipantViewModel[];
  activeAgents: ParticipantViewModel[];
  activeUsers: ParticipantViewModel[];
}
```

**Acceptance Criteria:**
- [ ] Shows section for "Users" and section for "Agents"
- [ ] Displays participant display_name
- [ ] Agent icon/badge for agents
- [ ] User count badge
- [ ] Collapsible (optional for alpha)

**Component Type:** Feature-specific (`src/components/Rooms/`)

**Minimal Design:**
```tsx
<VStack align="start">
  <Text fontWeight="bold">Users ({activeUsers.length})</Text>
  {activeUsers.map(p => (
    <Text key={p.participant_id}>{p.display_name}</Text>
  ))}

  <Text fontWeight="bold" mt={4}>Agents ({activeAgents.length})</Text>
  {activeAgents.map(p => (
    <HStack key={p.participant_id}>
      <Icon as={FaRobot} />
      <Text>{p.display_name}</Text>
    </HStack>
  ))}
</VStack>
```

---

### 5. Utility Components (Optional for Alpha)

#### 5.1 EmptyState Component
**File:** `src/components/Common/EmptyState.tsx` (Reusable)

**Task:** Display when no data is available

**Usage:**
- No rooms available
- No messages in room
- No participants

**Props:**
```tsx
interface EmptyStateProps {
  icon: IconType;
  title: string;
  description?: string;
  action?: React.ReactNode; // Optional button/link
}
```

**Component Type:** Common (`src/components/Common/`)

---

## Implementation Order (Recommended)

### Phase 1: Navigation & Routing (Day 1)
1. [X] Add Rooms to SidebarItems.tsx
2. [X] Create `/rooms` route (room list)
3. [X] Create `/rooms/$roomId` route (room view)
4. [X] Test navigation flow

### Phase 2: Room List (Day 2)
5. [X] Create RoomCard component
6. [X] Create RoomList component
7. [X] Integrate with `/rooms` route
8. [X] Test room selection navigation

### Phase 3: Message Display (Day 3)
9. [X] Create Message component
10. [X] Create MessageList component
11. [X] Create RoomHeader component
12. [X] Integrate with `/rooms/$roomId` route
13. [X] Test message display and polling

### Phase 4: Message Input (Day 4)
14. [X] Create MessageInput component
15. [X] Integrate with room view


18. [X] Create ParticipantList component
19. [X] Integrate with room view
20. [X] Test participant display

### Phase 6: Polish & Testing (Day 6)  (DEFERRED)
21. [ ] Add loading states (skeletons)
22. [ ] Add error handling (error boundaries)
23. [ ] Add empty states
24. [ ] End-to-end testing
25. [ ] Fix bugs and UX issues
16. [ ] Test message sending and optimistic updates
17. [ ] Test agent responses appear via polling
---

## Design Decisions (Minimal for Alpha)

### Layout Structure
```
┌─────────────────────────────────────────┐
│  Sidebar   │  Room View                 │
│            │  ┌─────────────────────┐   │
│  - Home    │  │ RoomHeader          │   │
│  - Stories │  │ (title, count)      │   │
│  - Rooms ◄ │  └─────────────────────┘   │
│            │  ┌─────────────────────┐   │
│            │  │ MessageList         │   │
│            │  │ - Message           │   │
│            │  │ - Message           │   │
│            │  │ - Message           │   │
│            │  └─────────────────────┘   │
│            │  ┌─────────────────────┐   │
│            │  │ MessageInput        │   │
│            │  └─────────────────────┘   │
│            │  ┌─────────────────────┐   │
│            │  │ ParticipantList     │   │
│            │  │ (sidebar/collapse)  │   │
│            │  └─────────────────────┘   │
└─────────────────────────────────────────┘
```

### Message Visual Distinction
- **User Messages:** Right-aligned, blue background, white text
- **Agent Messages:** Left-aligned, gray background, black text
- **Own Messages:** Darker blue shade

### Responsive Behavior (Alpha)
- Desktop: Sidebar + Room view side-by-side
- Mobile: Simplified (defer to post-alpha)

---

## Testing Strategy

### Manual Testing Scenarios

**Scenario 1: View Room List**
1. Log in as existing user
2. Click "Rooms" in sidebar
3. Verify room list appears
4. Verify room metadata displays correctly

**Scenario 2: View Room Messages**
1. From room list, click a room
2. Verify message history loads
3. Verify messages display chronologically
4. Verify user vs. agent messages are visually distinct

**Scenario 3: Send Message**
1. Type message in input
2. Press Enter
3. Verify message appears immediately (optimistic)
4. Verify agent response appears after ~3-5 seconds (polling)
5. Verify input clears after send

**Scenario 4: Multi-User Simulation**
1. Open room in two browser windows (different users)
2. Send message from User A
3. Verify message appears in User B's window within 3 seconds
4. Send message from User B
5. Verify appears in User A's window

**Scenario 5: Pagination**
1. Navigate to room with >50 messages
2. Verify "Load More" button appears
3. Click "Load More"
4. Verify older messages load and prepend to list

---

## Known Limitations (Alpha)

### By Design (Phase 3)
- ⚠️ **Polling-based updates** (3-second delay)
- ⚠️ **No typing indicators**
- ⚠️ **No read receipts**
- ⚠️ **No online/offline status**
- ⚠️ **No message reactions**
- ⚠️ **No file attachments**

### Technical Debt (Acceptable for Alpha)
- ⚠️ **User names show as IDs** (enrichment not implemented)
- ⚠️ **Basic styling** (polish deferred)
- ⚠️ **Limited error handling** (happy path focus)
- ⚠️ **No mobile optimization**

### Deferred to Phase 4
- WebSocket real-time updates
- Streaming agent responses
- Typing indicators
- Presence system

---

## Success Criteria

### Alpha is complete when:
1. ✅ User can navigate to Rooms from sidebar
2. ✅ User can see list of their accessible rooms
3. ✅ User can select a room and view message history
4. ✅ User can send a message and see it appear immediately
5. ✅ User can see agent responses appear (via polling)
6. ✅ Multiple users can chat in the same room (verified manually)
7. ✅ Pagination works for loading older messages
8. ✅ No critical bugs in happy path
9. ✅ Basic error handling (403, 404, network errors)
10. ✅ Code compiles with no TypeScript errors

---

## Files to Create/Modify

### New Files (Components)
```
src/components/Rooms/
├── RoomList.tsx
├── RoomCard.tsx
├── RoomHeader.tsx
├── MessageList.tsx
├── Message.tsx
├── MessageInput.tsx
└── ParticipantList.tsx
```

### New Files (Routes)
```
src/routes/_layout/
├── rooms.tsx           # Room list route
└── rooms.$roomId.tsx   # Individual room route
```

### Modified Files
```
src/components/Common/SidebarItems.tsx  # Add Rooms link
```

---

## Next Steps After Alpha

### Phase 3 Complete (Post-Alpha)
- [X] Room creation UI
- [X] Add participant UI (invite users/agents)
- [X] Remove participant UI (owner only)
- [ ] Room settings/metadata editing
- [ ] Enhanced styling and UX polish
- [ ] Mobile responsive design
- [ ] Comprehensive error handling
- [ ] Loading skeletons
- [ ] Unit tests
- [ ] Integration tests

### Phase 4 (WebSocket Streaming)
- [ ] Replace polling with WebSocket subscriptions
- [ ] Real-time message delivery
- [ ] Streaming agent responses (token-by-token)
- [ ] Typing indicators
- [ ] Online/offline presence
- [ ] Read receipts

---

## Dependencies

### Existing (Already Available)
- ✅ Chakra UI components
- ✅ TanStack Query
- ✅ TanStack Router
- ✅ React Hook Form (for forms if needed)
- ✅ React Icons
- ✅ useAuth hook
- ✅ handleError utility

### New (Created in Phase 3)
- ✅ RoomService
- ✅ useRoom hook
- ✅ useRoomMessages hook
- ✅ ViewModels and types

---

## Estimated Timeline

**Total:** 5-6 days for Alpha implementation

- Navigation & Routing: 0.5 days
- Room List: 1 day
- Message Display: 1.5 days
- Message Input: 1 day
- Participants: 0.5 days
- Polish & Testing: 1.5 days

**Contingency:** +2 days for unexpected issues

---

## Risk Mitigation

### High Risk ⚠️
**Issue:** User display names showing as UUIDs instead of names
**Mitigation:** Implement user profile lookup and enrichment functions (already stubbed in RoomService)

**Issue:** Polling performance on slow connections
**Mitigation:** Adjust polling intervals, add manual refresh button

**Issue:** Auto-scroll conflicts with user scrolling up
**Mitigation:** Disable auto-scroll when user is not at bottom of chat

### Medium Risk ⚠️
**Issue:** Agent responses not appearing
**Mitigation:** Add polling status indicator, manual refresh option

**Issue:** Optimistic update rollback UX
**Mitigation:** Show error toast, highlight failed message

---

## Conclusion

This Phase 3 Alpha implementation provides the **minimum viable functionality** to validate the multi-user, multi-agent chat system before proceeding to Phase 4 (WebSocket streaming).

All components integrate with the completed data layer (`RoomService`, `useRoom`, `useRoomMessages`) and follow established patterns from `ComponentDevelopmentWalkthrough.md`.

Once Alpha is validated, we can proceed with Phase 4 WebSocket implementation while continuing to enhance Phase 3 UI in parallel.
