# Phase 3: Frontend Room UI - Technical Specification

**Version:** 1.0
**Status:** Design Review
**Last Updated:** 2025-12-28
**Dependencies:** Phase 2 Backend (Complete), OpenAPI Client Generated

---

## Executive Summary

Phase 3 delivers a browser-based collaborative room interface that enables multiple users to interact with AI agents in shared story creation sessions. This specification defines the technical architecture, data flow patterns, and integration contracts required to build the UI layer on top of the completed Phase 2 backend.

**Key Principle:** This specification establishes *what* the system must accomplish and *how* data flows through it, but deliberately defers *visual design decisions* and *component selection* until design preconditions are satisfied.

---

## 1. Functional Requirements

### 1.1 Core User Flows

#### FR1.1: Room Discovery and Access
**Description:** Users must be able to discover available rooms, create new rooms, and join existing rooms.

**Capabilities Required:**
- List all rooms accessible to the current user
- Filter/search rooms by title, last activity, or participants
- Create a new room with optional initial configuration (title, story attachment, initial agents)
- Join an existing room by room_id or invitation
- View room metadata (participant count, last activity timestamp)

**Backend Dependencies:**
- `GET /api/rooms` - List user's accessible rooms
- `POST /api/rooms` - Create new room
- `POST /api/rooms/{room_id}/participants` - Join room as participant

**Authorization Constraints:**
- User must be authenticated (JWT required)
- Room creation available to all authenticated users
- Joining requires invitation or room owner approval (Phase 4 enhancement)

---

#### FR1.2: Room Participation Management
**Description:** Users must be able to view and manage room participants, including both human users and AI agents.

**Capabilities Required:**
- View list of all active participants (users + agents) in a room
- Distinguish between user participants and agent participants visually
- Add agents to the room (if user has permission)
- View participant roles (owner, member)
- See participant online/offline status (Phase 4 WebSocket enhancement)

**Backend Dependencies:**
- `GET /api/rooms/{room_id}/participants` - Retrieve participant list
- `POST /api/rooms/{room_id}/participants` - Add participant (user or agent)
- `DELETE /api/rooms/{room_id}/participants/{participant_id}` - Remove participant

**Data Contracts:**
```typescript
interface RoomParticipant {
  user_id?: string;          // Present for user participants
  agent_id?: string;         // Present for agent participants
  participant_type: 'user' | 'agent';
  role: 'owner' | 'member';
  display_name: string;
  avatar_url?: string;       // For users
  is_active: boolean;
  joined_at: string;
}
```

---

#### FR1.3: Message Exchange
**Description:** Users must be able to send messages to the room and view chronological message history with clear attribution to senders (users or agents).

**Capabilities Required:**
- Display message history in chronological order
- Show sender attribution (user name or agent name)
- Distinguish visually between user messages and agent messages
- Send new text messages to the room
- Auto-trigger agent responses after user message (backend behavior)
- Handle message pagination for long conversations
- Display timestamps for all messages

**Backend Dependencies:**
- `GET /api/rooms/{room_id}/messages?limit=50&before={cursor}` - Retrieve paginated message history
- `POST /api/rooms/{room_id}/messages` - Send user message (triggers agent responses)

**Data Contracts:**
```typescript
interface RoomMessage {
  message_id: number;
  room_id: string;
  sender_id?: string;         // Present for user messages
  agent_id?: string;          // Present for agent messages
  sender_type: 'user' | 'agent';
  content: string;
  button_options?: ButtonOption[];  // Phase 4 interactive elements
  created_at: string;
}

interface ButtonOption {
  label: string;
  value: string;
  style: 'primary' | 'secondary';
}
```

---

#### FR1.4: Room Context Awareness
**Description:** The UI must maintain awareness of room state, including active story attachment, participant changes, and message updates.

**Capabilities Required:**
- Display currently attached story (if any)
- Detect when participants join/leave (polling in Phase 3, WebSocket in Phase 4)
- Detect new messages from other participants (polling in Phase 3)
- Maintain scroll position and read state
- Handle room state transitions (created → active → archived)

**Backend Dependencies:**
- `GET /api/rooms/{room_id}` - Retrieve room metadata
- `GET /api/stories/{story_id}` - Retrieve attached story data (if applicable)

---

### 1.2 Non-Functional Requirements

#### NFR1: Performance Targets
- Initial room load (metadata + last 50 messages): < 2 seconds
- Message send latency (user message → backend acknowledgment): < 500ms
- Message history pagination: < 1 second per page
- Polling interval for new messages (Phase 3): 3-5 seconds
- UI responsiveness: No blocking operations during data fetching

#### NFR2: Data Freshness Guarantees
- User's own messages visible immediately after send (optimistic update)
- Other participants' messages visible within polling interval (3-5s in Phase 3)
- Participant list updates visible within polling interval
- Agent responses visible after backend processing completes (variable, typically 2-10s)

#### NFR3: Error Handling Requirements
- Network failures: Retry with exponential backoff (3 attempts max)
- Unauthorized access (403): Redirect to room list with error message
- Room not found (404): Display "Room unavailable" message
- Server errors (500): Display user-friendly error with retry option
- Validation errors (400): Display inline form errors

---

## 2. Architecture and Design Patterns

### 2.1 Separation of Concerns

The Phase 3 implementation follows strict separation across these layers:

```
┌─────────────────────────────────────────────────────┐
│              UI Presentation Layer                  │
│  (React Components - Deferred to Design Phase)      │
└──────────────────┬──────────────────────────────────┘
                   │ Props/Events
┌──────────────────▼──────────────────────────────────┐
│           State Management Layer                    │
│  - Custom Hooks (useRoom, useRoomMessages)          │
│  - TanStack Query (caching, invalidation)           │
│  - Local UI State (modals, forms)                   │
└──────────────────┬──────────────────────────────────┘
                   │ API Calls
┌──────────────────▼──────────────────────────────────┐
│         Data Integration Layer                      │
│  - Service Adapters (roomService.ts)                │
│  - OpenAPI Client (auto-generated)                  │
│  - Request/Response Transformations                 │
└──────────────────┬──────────────────────────────────┘
                   │ HTTP/REST
┌──────────────────▼──────────────────────────────────┐
│              Backend API (Phase 2)                  │
│  - Room Management, Messages, Participants          │
└─────────────────────────────────────────────────────┘
```

**Responsibilities:**

1. **UI Presentation Layer (Components)**
   - Render data provided by state management
   - Dispatch user actions (button clicks, form submissions)
   - Handle local UI state (accordion open/close, modal visibility)
   - **NO direct API calls**
   - **NO business logic**

2. **State Management Layer (Hooks + TanStack Query)**
   - Manage server state via TanStack Query
   - Provide data and mutation functions to components
   - Handle optimistic updates
   - Coordinate cache invalidation
   - Aggregate data from multiple sources

3. **Data Integration Layer (Services)**
   - Wrap OpenAPI client methods
   - Transform backend responses to frontend domain models
   - Handle request payload construction
   - Centralize API endpoint usage
   - Provide type-safe interfaces

---

### 2.2 State Management Strategy

#### 2.2.1 Server State (TanStack Query)

**Pattern:** All backend data is managed exclusively through TanStack Query.

**Query Key Structure:**
```typescript
// Room metadata
['rooms']                          // All rooms list
['rooms', roomId]                  // Single room detail

// Messages
['rooms', roomId, 'messages']      // Message list for room

// Participants
['rooms', roomId, 'participants']  // Participant list for room

// Stories (context)
['stories', storyId]               // Story attached to room
```

**Cache Invalidation Rules:**
- After sending message → Invalidate `['rooms', roomId, 'messages']`
- After adding participant → Invalidate `['rooms', roomId, 'participants']`
- After creating room → Invalidate `['rooms']`
- After room metadata update → Invalidate `['rooms', roomId]`

**Polling Strategy (Phase 3):**
- Messages: Poll every 3 seconds when room is active
- Participants: Poll every 5 seconds when room is active
- Disable polling when browser tab is inactive (`visibilitychange` event)
- Stop polling when user navigates away from room

---

#### 2.2.2 Local UI State (React State)

**Pattern:** Component-level state for UI-only concerns.

**Appropriate Use Cases:**
- Modal/dialog open/close state
- Form input values (before submission)
- Accordion/collapse expanded state
- Scroll position tracking
- Loading indicators (in addition to TanStack Query status)

**Anti-Patterns to Avoid:**
- Storing fetched data in local state (use TanStack Query)
- Duplicating server state in component state
- Prop drilling through multiple levels (use composition or context)

---

### 2.3 Data Flow Patterns

#### 2.3.1 Read Flow (Display Messages)

```
Component Mount
    ↓
useRoomMessages(roomId) hook invoked
    ↓
TanStack Query checks cache
    ↓
[CACHE MISS] → Call RoomService.getMessages(roomId)
    ↓
OpenAPI Client → GET /api/rooms/{roomId}/messages
    ↓
Backend returns { messages: [...], has_more: boolean }
    ↓
Transform response to MessageViewModel[]
    ↓
TanStack Query caches result
    ↓
Hook returns { messages, isLoading, error }
    ↓
Component renders messages
```

---

#### 2.3.2 Write Flow (Send Message)

```
User types message + clicks Send
    ↓
Component calls sendMessage(content) from hook
    ↓
useMutation triggers optimistic update
    ↓
[OPTIMISTIC] Add temporary message to cache with pending ID
    ↓
Component re-renders with optimistic message shown
    ↓
POST /api/rooms/{roomId}/messages with { content }
    ↓
Backend processes message + triggers agents
    ↓
Backend returns created message + agent responses
    ↓
[ON SUCCESS] Replace optimistic message with server response
    ↓
Invalidate ['rooms', roomId, 'messages'] cache
    ↓
TanStack Query refetches to get agent responses
    ↓
Component re-renders with all messages
    ↓
[ON ERROR] Remove optimistic message, show error toast
```

---

#### 2.3.3 Polling Flow (Detect New Messages)

```
Component mounted with useRoomMessages(roomId, { polling: true })
    ↓
TanStack Query starts refetch interval (3s)
    ↓
Every 3 seconds: GET /api/rooms/{roomId}/messages?limit=50
    ↓
Compare fetched messages with cached messages
    ↓
[NEW MESSAGES DETECTED]
    ↓
Update cache with new messages
    ↓
Component re-renders with new messages
    ↓
Scroll to new message if user is at bottom of chat
    ↓
Continue polling until component unmounts
```

---

## 3. Data Integration Layer

### 3.1 Service Adapter Pattern

**File:** `frontend/src/services/roomService.ts`

**Purpose:** Provide a clean, type-safe abstraction over the OpenAPI client for room-related operations.

**Interface Design:**

```typescript
// Type Definitions (transformed from OpenAPI models)
export interface RoomViewModel {
  room_id: string;
  title: string;
  created_by: string;
  is_group: boolean;
  last_activity: string;
  participant_count: number;
  unread_count?: number;
}

export interface MessageViewModel {
  message_id: number;
  sender_type: 'user' | 'agent';
  sender_name: string;
  sender_id?: string;
  agent_id?: string;
  content: string;
  created_at: Date;
  is_own_message: boolean;
}

export interface ParticipantViewModel {
  participant_id: string;
  participant_type: 'user' | 'agent';
  display_name: string;
  role: 'owner' | 'member';
  avatar_url?: string;
  is_active: boolean;
}

// Service Interface
export const RoomService = {
  // Room Operations
  listRooms: async (): Promise<RoomViewModel[]> => { /* ... */ },

  getRoom: async (roomId: string): Promise<RoomViewModel> => { /* ... */ },

  createRoom: async (data: {
    title: string;
    is_group: boolean;
    initial_participants?: string[];
  }): Promise<RoomViewModel> => { /* ... */ },

  // Message Operations
  getMessages: async (
    roomId: string,
    options?: { limit?: number; before?: number }
  ): Promise<{
    messages: MessageViewModel[];
    has_more: boolean;
    next_cursor?: number;
  }> => { /* ... */ },

  sendMessage: async (
    roomId: string,
    content: string
  ): Promise<MessageViewModel> => { /* ... */ },

  // Participant Operations
  getParticipants: async (
    roomId: string
  ): Promise<ParticipantViewModel[]> => { /* ... */ },

  addParticipant: async (
    roomId: string,
    participantId: string,
    participantType: 'user' | 'agent',
    role?: 'owner' | 'member'
  ): Promise<ParticipantViewModel> => { /* ... */ },

  removeParticipant: async (
    roomId: string,
    participantId: string
  ): Promise<void> => { /* ... */ },
};
```

**Transformation Responsibilities:**
- Convert ISO timestamp strings to Date objects
- Flatten nested API response structures
- Compute derived fields (e.g., `is_own_message`, `participant_count`)
- Enrich data with client-side context (current user ID)
- Normalize inconsistencies in backend response formats

---

### 3.2 Custom Hooks Interface

**File:** `frontend/src/hooks/useRoom.ts`

**Purpose:** Provide room-level state management, aggregating messages, participants, and metadata.

**Interface Design:**

```typescript
export interface UseRoomOptions {
  enablePolling?: boolean;
  pollingInterval?: number;
  autoScrollToBottom?: boolean;
}

export interface UseRoomResult {
  // Room State
  room: RoomViewModel | undefined;
  messages: MessageViewModel[];
  participants: ParticipantViewModel[];

  // Loading States
  isLoadingRoom: boolean;
  isLoadingMessages: boolean;
  isLoadingParticipants: boolean;

  // Error States
  roomError: Error | null;
  messagesError: Error | null;
  participantsError: Error | null;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  addParticipant: (participantId: string, type: 'user' | 'agent') => Promise<void>;
  removeParticipant: (participantId: string) => Promise<void>;
  loadMoreMessages: () => Promise<void>;

  // Pagination
  hasMoreMessages: boolean;
  isLoadingMoreMessages: boolean;

  // Derived State
  currentUserRole: 'owner' | 'member' | null;
  activeAgents: ParticipantViewModel[];
  activeUsers: ParticipantViewModel[];
}

export function useRoom(
  roomId: string,
  options?: UseRoomOptions
): UseRoomResult {
  // Implementation using TanStack Query
}
```

---

**File:** `frontend/src/hooks/useRoomMessages.ts`

**Purpose:** Focused hook for message-specific operations with pagination and polling.

```typescript
export interface UseRoomMessagesOptions {
  enablePolling?: boolean;
  pollingInterval?: number;
  pageSize?: number;
}

export interface UseRoomMessagesResult {
  messages: MessageViewModel[];
  isLoading: boolean;
  error: Error | null;

  // Pagination
  hasMore: boolean;
  loadMore: () => Promise<void>;
  isLoadingMore: boolean;

  // Actions
  sendMessage: (content: string) => Promise<void>;
  isSending: boolean;

  // Polling Status
  isPolling: boolean;
  lastUpdated: Date | null;
}

export function useRoomMessages(
  roomId: string,
  options?: UseRoomMessagesOptions
): UseRoomMessagesResult {
  // Implementation
}
```

---

## 4. Integration Contracts

### 4.1 Backend API Dependencies

Phase 3 relies on the following backend endpoints (documented in Minimog §C2):

#### C4.1: Room Management API
```
GET    /api/rooms
POST   /api/rooms
GET    /api/rooms/{room_id}
DELETE /api/rooms/{room_id}  (Phase 3.2 - Archive/Delete)
```

#### C4.2: Message API
```
GET    /api/rooms/{room_id}/messages?limit=50&before={cursor}
POST   /api/rooms/{room_id}/messages
```

#### C4.3: Participant API
```
GET    /api/rooms/{room_id}/participants
POST   /api/rooms/{room_id}/participants
DELETE /api/rooms/{room_id}/participants/{participant_id}
```

#### C4.4: Authentication API (Existing)
```
POST   /api/login/access-token
GET    /api/users/me
```

**Assumptions:**
- All endpoints require JWT authentication (`Authorization: Bearer {token}`)
- All endpoints return JSON responses
- Error responses follow OpenAPI error schema
- Backend handles agent triggering automatically after user message

---

### 4.2 OpenAPI Client Assumptions

**Dependency:** Auto-generated client from backend OpenAPI spec.

**Expected Client Interface:**
```typescript
import { RoomsService, MessagesService, ParticipantsService } from '@/client';

// Type imports
import type {
  RoomPublic,
  RoomCreate,
  RoomMessagePublic,
  RoomMessageSend,
  ParticipantPublic,
  ParticipantAdd,
} from '@/client/types.gen';
```

**Requirements:**
- Client must be regenerated whenever backend schema changes
- Client must include TypeScript types for all request/response bodies
- Client must handle authentication token injection automatically
- Client must throw `ApiError` with status code for error responses

---

### 4.3 Authorization Contract

**Constraint:** Users can only access rooms where they are active participants.

**Frontend Responsibilities:**
1. Never display rooms the user is not a participant of
2. Handle 403 Forbidden errors gracefully (redirect to room list)
3. Check authorization before rendering "Add Participant" or "Remove Participant" actions
4. Visually distinguish room owner from members

**Backend Guarantees (from Phase 2):**
- Endpoint returns 403 if user is not an active participant
- Backend validates room membership before any operation
- Participant status (`is_active`) is authoritative

---

## 5. Design Preconditions

Before proceeding to component implementation, the following design decisions must be finalized:

### 5.1 Information Architecture

**Required Decisions for V2**
1. **Room Discovery Pattern**
   - How do users discover available rooms?
   - Navigation: Separate page vs. sidebar vs. modal?
   - Search/filter capabilities needed?

2. **Room Selection Behavior**
   - Single active room vs. multi-room tabs?
   - Persist last-viewed room in session?
   - Handle deep linking to specific room?

3. **Room Creation Flow**
   - Inline creation vs. modal vs. separate page?
   - Required fields vs. optional fields?
   - Default values (e.g., auto-attach current story)?

---

### 5.2 Interaction Patterns

**Required Decisions:**
1. **Message Sending Mechanism**
   - Enter key submits vs. requires button click?
   - Shift+Enter for line breaks?
   - Character limits or formatting restrictions?

2. **Participant Management UX**
   - Where is participant list displayed (sidebar, header, modal)?
   - How to add agents (dropdown, search, dedicated button)?
   - Confirmation required for removing participants?

3. **Message History Behavior**
   - Auto-scroll to bottom on new messages?
   - Infinite scroll vs. "Load More" button?
   - Jump to latest unread message?
   - Scroll position preservation on pagination?

---

### 5.3 Visual Design System

**Required Decisions:**
1. **Message Visual Distinction**
   - How to distinguish user messages from agent messages?
   - Avatar placement and size?
   - Message bubble styling (colors, borders, backgrounds)?
   - Timestamp placement and format?

2. **Participant Visual Representation**
   - How to distinguish users from agents in participant list?
   - Agent avatars/icons?
   - Online/offline indicators (Phase 4)?
   - Role badges (owner vs. member)?

3. **Layout Structure**
   - Room list placement (left sidebar, top bar, separate page)?
   - Message area vs. participant list ratio?
   - Fixed header/footer vs. scrollable?
   - Mobile responsive behavior?

---

### 5.4 Error and Loading States

**Required Decisions:**
1. **Loading Indicators**
   - Skeleton screens vs. spinners vs. progress bars?
   - Optimistic message rendering style?
   - Partial content display during loading?

2. **Error Display**
   - Toast notifications vs. inline errors vs. modal dialogs?
   - Retry mechanisms (automatic vs. manual)?
   - Fallback content for failed loads?

3. **Empty States**
   - No rooms available message?
   - Empty message history (new room)?
   - No participants beyond user?

---

## 6. Implementation Phases

### Phase 3.1: Core Room Experience (MVP)

**Goal:** Enable basic room interaction with message send/receive and participant viewing.

**Deliverables:**
1. Room list view (read-only, display all accessible rooms)
2. Single room view with message history
3. Message input and send functionality
4. Participant list display (read-only)
5. Polling-based message updates
6. Basic error handling

**Technical Scope:**
- `useRoom` hook implemented
- `useRoomMessages` hook implemented
- `RoomService` adapter complete
- TanStack Query integration complete
- No WebSocket (polling only)

**Design Preconditions Required:**
- 5.1: Information Architecture (room discovery, selection)
- 5.2: Message sending mechanism
- 5.3: Message visual distinction, layout structure

---

### Phase 3.2: Room Management

**Goal:** Enable users to create rooms, add participants, and manage room lifecycle.

**Deliverables:**
1. Create room form/flow
2. Add participant functionality (users and agents)
3. Remove participant functionality (if owner)
4. Room archive/delete functionality
5. Room metadata editing (title, settings)
6. Users can toggle Agents (active/inactive)
7. Usernames and agent names displayed with chat messages

**Technical Scope:**
- Room creation mutations
- Participant management mutations
- Form validation and error handling
- Optimistic updates for participant add/remove

**Design Preconditions Required:**
- 5.1: Room creation flow
- 5.2: Participant management UX
- 5.4: Error display for validation failures

---

### Phase 3.3: Enhanced UX

**Goal:** Improve usability with pagination, search, and polish.

**Deliverables:**
1. Message history pagination ("Load More" or infinite scroll)
2. Room search/filter functionality
3. Unread message indicators
4. Auto-scroll behavior refinement
5. Keyboard shortcuts (Enter to send, etc.)
6. Loading states and skeleton screens

**Technical Scope:**
- Pagination logic in `useRoomMessages`
- Cursor-based message loading
- Scroll position management
- Keyboard event handling

**Design Preconditions Required:**
- 5.2: Message history behavior (scroll, pagination)
- 5.4: Loading indicators, empty states

---

## 7. Testing Strategy

### 7.1 Unit Testing

**Scope:** Custom hooks and service adapters.

**Required Tests:**
- `useRoom` hook behavior with mocked TanStack Query
- `useRoomMessages` hook pagination logic
- `RoomService` transformation functions
- Optimistic update logic
- Cache invalidation triggers

**Tools:** Vitest + React Testing Library

---

### 7.2 Integration Testing

**Scope:** Component integration with hooks and services.

**Required Tests:**
- Message send flow (user input → API call → UI update)
- Participant add flow
- Room creation flow
- Error handling (network failure, 403, 404)
- Polling behavior (enable/disable based on component state)

**Tools:** Vitest + Mock Service Worker (MSW)

---

### 7.3 E2E Testing (Future)

**Scope:** Full user workflows.

**Test Scenarios:**
- Create room → Send message → See agent response
- Join room → View message history → Add participant
- Multi-user scenario: User A sends message, User B receives via polling

**Tools:** Playwright (deferred to Phase 4 for WebSocket support)

---

## 8. Success Criteria

Phase 3 is complete when:

1. ✅ User can view list of accessible rooms
2. ✅ User can create a new room
3. ✅ User can select a room and view message history
4. ✅ User can send a message and see it appear immediately (optimistic update)
5. ✅ User sees agent responses appear after backend processing
6. ✅ User can view participant list (users and agents)
7. ✅ User can add agents to the room
8. ✅ User with owner role can remove participants
9. ✅ Message history paginates correctly (50 messages per page)
10. ✅ Polling updates messages every 3-5 seconds when room is active
11. ✅ Authorization errors (403) redirect to room list with error message
12. ✅ Network errors show retry option
13. ✅ All tests pass (unit + integration)
14. ✅ No regressions in existing frontend features
15. ✅ OpenAPI client remains synchronized with backend

---

## 9. Out of Scope (Deferred to Phase 4)

The following features are explicitly **not** part of Phase 3:

- WebSocket real-time updates (replaced by polling)
- Streaming agent responses (token-by-token)
- Button interactions / interactive elements (AG-UI protocol)
- Online/offline participant status
- Typing indicators
- Read receipts
- Message reactions
- Rich text formatting
- File attachments
- Voice/video integration

These will be addressed in Phase 4 (Streaming) or later phases.

---

## 10. Risks and Mitigations

### Risk 1: Polling Performance Impact
**Impact:** High polling frequency may cause excessive backend load or battery drain.

**Mitigation:**
- Use `visibilitychange` API to disable polling on inactive tabs
- Implement exponential backoff if server returns errors
- Monitor backend load and adjust polling interval if needed
- Plan WebSocket migration (Phase 4) to eliminate polling

---

### Risk 2: Optimistic Update Conflicts
**Impact:** User's optimistic message may conflict with concurrent messages from other users.

**Mitigation:**
- Assign temporary IDs to optimistic messages (negative integers)
- Replace optimistic message with server response on success
- Use message timestamps for conflict-free ordering
- Display pending indicator on optimistic messages

---

### Risk 3: Design Decisions Blocking Implementation
**Impact:** Cannot implement components without finalizing visual design.

**Mitigation:**
- This specification establishes clear design preconditions (§5)
- Implementation can begin on data layer (services, hooks) immediately
- Component implementation starts only after design decisions documented
- Use placeholder/wireframe components during design phase

---

### Risk 4: Backend Schema Changes
**Impact:** Backend API changes may break frontend integration.

**Mitigation:**
- Regenerate OpenAPI client on every backend deployment
- Version API endpoints if breaking changes needed
- Service adapter layer isolates components from API changes
- Integration tests detect schema mismatches early

---

## 11. Dependencies and Handoffs

### 11.1 Dependencies on Other Work

**Blocking Dependencies:**
- ✅ Phase 2 Backend (Complete) - Room API, Participant API, Message API
- ✅ OpenAPI client generation (Complete) - Auto-generated TypeScript client

**Concurrent Dependencies (can proceed in parallel):**
- Design System Decisions (§5) - Required before component implementation
- Testing Infrastructure Setup (MSW, Vitest config)

---

### 11.2 Handoffs to Future Phases

**Handoff to Phase 4 (Streaming):**
- Replace polling with WebSocket subscriptions
- Implement real-time participant status
- Stream agent responses token-by-token
- Add typing indicators

**Handoff to Phase 5 (Advanced Multi-Agent):**
- Display step execution progress (tool invocations)
- Show agent handoff events
- Button interactions for agent responses

---

## 12. Next Steps

### Immediate Actions (Before Component Development)

1. **Design Workshop** - Finalize decisions in §5 (Design Preconditions)
   - Output: Design decisions document with mockups/wireframes
   - Owner: Design + Product
   - Timeline: 2-3 days

2. **Service Layer Implementation** - Build data integration layer (§3)
   - Implement `RoomService` adapter
   - Write unit tests for service transformations
   - Owner: Frontend Developer
   - Timeline: 1-2 days

3. **Hook Implementation** - Build state management layer (§3.2)
   - Implement `useRoom` and `useRoomMessages` hooks
   - Write unit tests with mocked TanStack Query
   - Owner: Frontend Developer
   - Timeline: 2-3 days

4. **Component Development** - Build UI layer (after design finalized)
   - Implement components following ComponentDevelopmentWalkthrough.md
   - Follow FrontendRULES.md patterns
   - Owner: Frontend Developer
   - Timeline: 5-7 days

---

## Appendix A: Key Terminology

- **Room**: A collaborative space where users and agents exchange messages
- **Participant**: A user or agent that is a member of a room
- **Message**: A text communication from a user or agent in a room
- **Agent**: An AI participant (e.g., StoryAdvisor) that responds to messages
- **Polling**: Periodic API requests to check for new data (replaced by WebSocket in Phase 4)
- **Optimistic Update**: Immediately displaying user action result before server confirms
- **Cursor-based Pagination**: Using message_id as a cursor to load older messages

---

## Appendix B: Reference Documents

- **Backend Architecture:** `/backend/docs/Minimog.md`
- **Phase 2 Review:** `/backend/docs/phase-2-review.md`
- **Steel Thread Reference:** `/backend/docs/SteelThreadReference.md`
- **Frontend Patterns:** `/frontend/docs/ComponentDevelopmentWalkthrough.md`
- **Frontend Rules:** `/frontend/docs/FrontendRULES.md`
- **API Contracts:** Backend OpenAPI spec at `http://localhost:8000/docs`

---

**End of Technical Specification**
