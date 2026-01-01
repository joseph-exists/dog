# Phase 5: REVISED Implementation Plan - Using Existing Hooks

## Executive Summary

**The user correctly identified that we should extend existing hooks rather than create new ones!**

### Existing Infrastructure ✅

**Already Implemented:**
- ✅ `useRoomStream.ts` - WebSocket connection with sequence tracking
- ✅ `useRoomMessages.ts` - Message fetching with pagination
- ✅ AG-UI-style event handling
- ✅ Token streaming for agents
- ✅ Query invalidation
- ✅ Optimistic updates

### What We Actually Need to Do

**Phase 5 is NOT about creating AG-UI infrastructure (it exists!)**
**Phase 5 IS about extending it with message management features.**

---

## Architecture Review: What Exists

### 1. useRoomStream Hook (src/hooks/useRoomStream.ts)

**Current Features:**
```typescript
export function useRoomStream(roomId, options) {
  // ✅ WebSocket connection
  // ✅ Sequence tracking (lastSequence state)
  // ✅ Reconnection with replay (session.create with last_sequence)
  // ✅ Event handling for:
  //    - room_message.user
  //    - room_message.agent
  //    - participant.* events
  // ✅ Token streaming (message.delta)
  // ✅ Query invalidation

  return {
    isConnected,
    sendMessage,
    streamingMessage,
    lastSequence
  }
}
```

**What's Missing for Phase 5:**
- ❌ Event handlers for: `message.edited`, `message.pinned`, `message.unpinned`, `message.context_toggled`, `message.deleted`
- ⚠️ Uses `/api/v1/ws/rooms/${roomId}?token=${token}` (need to verify AG-UI compliance)

### 2. useRoomMessages Hook (src/hooks/useRoomMessages.ts)

**Current Features:**
```typescript
export function useRoomMessages(roomId, options) {
  // ✅ Message fetching with pagination
  // ✅ sendMessage mutation with optimistic updates
  // ✅ loadMore for cursor-based pagination
  // ✅ Polling fallback (replaced by WebSocket)

  return {
    messages,
    sendMessage,
    loadMore,
    hasMore,
    // ... but NO edit/pin/delete/toggle mutations
  }
}
```

**What's Missing for Phase 5:**
- ❌ `editMessage` mutation
- ❌ `pinMessage` mutation
- ❌ `unpinMessage` mutation
- ❌ `toggleMessageContext` mutation
- ❌ `deleteMessage` mutation

---

## REVISED Implementation Plan

### [X] COMPLETE Phase 1: Extend useRoomStream (Add Event Handlers) 🔴

**File:** `frontend/src/hooks/useRoomStream.ts`

**Changes Needed:**

1. **Add Phase 5 event handlers to `handleMessage` function** (around line 92)

```typescript
// Existing code (lines 92-121):
case 'event':
  setLastSequence(message.sequence)

  // EXISTING: room_message.* and participant.* handlers
  if (message.event_type === 'room_message.agent') {
    // ...
  }

  if (message.event_type === 'room_message.user' ||
      message.event_type === 'room_message.agent') {
    queryClient.invalidateQueries({
      queryKey: ['rooms', roomId, 'messages']
    })
  }

  if (message.event_type.startsWith('participant.')) {
    queryClient.invalidateQueries({
      queryKey: ['rooms', roomId, 'participants']
    })
  }

  // 🆕 ADD PHASE 5 EVENT HANDLERS:

  // Message management events - invalidate messages query
  if (message.event_type === 'message.edited' ||
      message.event_type === 'message.pinned' ||
      message.event_type === 'message.unpinned' ||
      message.event_type === 'message.context_toggled') {
    queryClient.invalidateQueries({
      queryKey: ['rooms', roomId, 'messages']
    })
  }

  // Message deletion - invalidate messages query
  if (message.event_type === 'message.deleted') {
    queryClient.invalidateQueries({
      queryKey: ['rooms', roomId, 'messages']
    })
  }

  break
```

**That's it!** The existing infrastructure handles:
- ✅ WebSocket connection
- ✅ Sequence tracking
- ✅ Reconnection with replay
- ✅ Query invalidation

**Estimated Time:** 15 minutes

---

### [X] COMPLETE Phase 2: Extend useRoomMessages (Add Mutations) 🔴

**File:** `frontend/src/hooks/useRoomMessages.ts`

**Changes Needed:**

1. [X] COMPLETE **Add new mutations to the hook** (after `sendMessageMutation` around line 173)

```typescript
// Existing sendMessageMutation (lines 125-172)
const sendMessageMutation = useMutation({ ... })

// 🆕 ADD PHASE 5 MUTATIONS:

// Edit message mutation
const editMessageMutation = useMutation({
  mutationFn: async ({ messageId, content }: { messageId: string; content: string }) => {
    return await RoomService.editMessage(roomId, messageId, content, user?.id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: messagesQueryKey })
  },
  onError: (err: ApiError) => {
    handleError(err)
  }
})

// Pin message mutation
const pinMessageMutation = useMutation({
  mutationFn: async (messageId: string) => {
    return await RoomService.pinMessage(roomId, messageId, user?.id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: messagesQueryKey })
  },
  onError: (err: ApiError) => {
    handleError(err)
  }
})

// Unpin message mutation
const unpinMessageMutation = useMutation({
  mutationFn: async (messageId: string) => {
    return await RoomService.unpinMessage(roomId, messageId, user?.id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: messagesQueryKey })
  },
  onError: (err: ApiError) => {
    handleError(err)
  }
})

// Toggle message context mutation
const toggleContextMutation = useMutation({
  mutationFn: async ({ messageId, active }: { messageId: string; active: boolean }) => {
    return await RoomService.toggleMessageContext(roomId, messageId, active, user?.id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: messagesQueryKey })
  },
  onError: (err: ApiError) => {
    handleError(err)
  }
})

// Delete message mutation
const deleteMessageMutation = useMutation({
  mutationFn: async (messageId: string) => {
    return await RoomService.deleteMessage(roomId, messageId, user?.id)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: messagesQueryKey })
  },
  onError: (err: ApiError) => {
    handleError(err)
  }
})
```

2. **Add wrapper functions** (around line 210)

```typescript
// Existing sendMessage wrapper (lines 210-215)
const sendMessage = useCallback(async (content: string) => {
  await sendMessageMutation.mutateAsync(content)
}, [sendMessageMutation])

// 🆕 ADD WRAPPERS:

const editMessage = useCallback(async (messageId: string, content: string) => {
  await editMessageMutation.mutateAsync({ messageId, content })
}, [editMessageMutation])

const pinMessage = useCallback(async (messageId: string) => {
  await pinMessageMutation.mutateAsync(messageId)
}, [pinMessageMutation])

const unpinMessage = useCallback(async (messageId: string) => {
  await unpinMessageMutation.mutateAsync(messageId)
}, [unpinMessageMutation])

const toggleContext = useCallback(async (messageId: string, active: boolean) => {
  await toggleContextMutation.mutateAsync({ messageId, active })
}, [toggleContextMutation])

const deleteMessage = useCallback(async (messageId: string) => {
  await deleteMessageMutation.mutateAsync(messageId)
}, [deleteMessageMutation])
```

3. **Update return object** (around line 220)

```typescript
return {
  messages,
  isLoading,
  error: error as Error | null,

  // Pagination
  hasMore,
  loadMore,
  isLoadingMore,

  // Actions
  sendMessage,
  isSending: sendMessageMutation.isPending,

  // 🆕 PHASE 5 ACTIONS:
  editMessage,
  isEditing: editMessageMutation.isPending,
  pinMessage,
  isPinning: pinMessageMutation.isPending,
  unpinMessage,
  isUnpinning: unpinMessageMutation.isPending,
  toggleContext,
  isTogglingContext: toggleContextMutation.isPending,
  deleteMessage,
  isDeleting: deleteMessageMutation.isPending,

  // Polling Status
  isPolling,
  lastUpdated,
}
```

4. [X] COMPLETE **Update TypeScript interface** (lines 32-49)

```typescript
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

  // 🆕 PHASE 5 ACTIONS:
  editMessage: (messageId: string, content: string) => Promise<void>;
  isEditing: boolean;
  pinMessage: (messageId: string) => Promise<void>;
  isPinning: boolean;
  unpinMessage: (messageId: string) => Promise<void>;
  isUnpinning: boolean;
  toggleContext: (messageId: string, active: boolean) => Promise<void>;
  isTogglingContext: boolean;
  deleteMessage: (messageId: string) => Promise<void>;
  isDeleting: boolean;

  // Polling Status
  isPolling: boolean;
  lastUpdated: Date | null;
}
```

**Estimated Time:** 45 minutes

---

### [X] Phase 3: Add RoomService Methods [COMPLETE] 

**File:** `frontend/src/services/roomService.ts` (or use auto-generated client)

**Option A: Use Auto-Generated Client** (Recommended)

If OpenAPI client generation works, these should already exist:
```typescript
import { RoomsService } from '@/client'

// Then in useRoomMessages:
await RoomsService.editMessage({ roomId, messageId, requestBody: { content } })
await RoomsService.pinMessage({ roomId, messageId })
// etc.
```



---

### Phase 4: Verify AG-UI Endpoint Compliance ⚠️

**Current WebSocket Endpoint:** `/api/v1/ws/rooms/${roomId}?token=${token}`
**Minimog Spec Endpoint:** `/ui/session`

**Action Required:**
1. Check if backend supports `/ui/session` endpoint
2. If YES: Update `useRoomStream.ts` line 169
3. If NO: Verify current endpoint is AG-UI compliant

**File:** `frontend/src/hooks/useRoomStream.ts` (line 169)

```typescript
// CURRENT:
const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/rooms/${roomId}?token=${token}`

// POTENTIALLY UPDATE TO (verify with backend first):
const wsUrl = `${protocol}//${window.location.host}/ui/session`
// Then pass roomId in handshake instead of URL
```

**AND update handshake** (line 180):

```typescript
// CURRENT:
ws.send(JSON.stringify({
  type: 'session.create',
  last_sequence: lastSequence,
}))

// POTENTIALLY UPDATE TO:
ws.send(JSON.stringify({
  auth: { token },
  room_id: roomId,
  last_sequence: lastSequence
}))
```

**Estimated Time:** 30 minutes (verification + changes if needed)

---

## Revised Migration Checklist

### ✅ Pre-Implementation (10 minutes)

- [ ] Verify backend `/ui/session` endpoint exists OR confirm current endpoint is AG-UI compliant
- [ ] Regenerate API client: `npm run generate-client`
- [ ] Verify new endpoints exist in generated client

### 🔴 Phase 1: Extend useRoomStream (15 minutes)

- [ ] Open `frontend/src/hooks/useRoomStream.ts`
- [ ] Find `handleMessage` function (line 82)
- [ ] Add Phase 5 event handlers (message.edited, pinned, unpinned, context_toggled, deleted)
- [ ] Test: Send event from backend → verify query invalidation

### 🔴 Phase 2: Extend useRoomMessages (45 minutes)

- [ ] Open `frontend/src/hooks/useRoomMessages.ts`
- [ ] Add 5 new mutations (edit, pin, unpin, toggle, delete)
- [ ] Add wrapper functions for each mutation
- [ ] Update return object
- [ ] Update TypeScript interface
- [ ] Test: Call each mutation → verify success

### 🟡 Phase 3: Add Service Methods (5-30 minutes)

- [ ] Check if auto-generated client has methods
- [ ] If yes: Use `RoomsService` directly
- [ ] If no: Add methods to `RoomService`
- [ ] Test: Call service method → verify API call

### ⚠️ Phase 4: Verify AG-UI Compliance (30 minutes)

- [ ] Test current WebSocket endpoint
- [ ] Check if `/ui/session` exists
- [ ] Update endpoint if needed
- [ ] Update handshake format if needed
- [ ] Test: Connect → verify handshake works

### 🎨 Phase 5: UI Components (Same as Before)

- [ ] Create `MessageBadge` component
- [ ] Create `EditDrawer` component
- [ ] Create `MessageFilters` component
- [ ] Update `MessageItem` to show badges
- [ ] Update `MessageList` to use extended hooks

---

## Usage Example: Before vs After

### BEFORE (Current)

```typescript
function RoomView({ roomId }) {
  const { isConnected, sendMessage } = useRoomStream(roomId)
  const { messages, sendMessage: send } = useRoomMessages(roomId)

  // ❌ No way to edit/pin/delete messages

  return <MessageList messages={messages} />
}
```

### AFTER (Phase 5)

```typescript
function RoomView({ roomId }) {
  const { isConnected } = useRoomStream(roomId) // ✅ Now handles Phase 5 events

  const {
    messages,
    sendMessage,
    editMessage,      // 🆕
    pinMessage,       // 🆕
    unpinMessage,     // 🆕
    toggleContext,    // 🆕
    deleteMessage,    // 🆕
    isEditing,
    isPinning,
  } = useRoomMessages(roomId)

  return (
    <MessageList
      messages={messages}
      onEdit={editMessage}
      onPin={pinMessage}
      onDelete={deleteMessage}
    />
  )
}
```

---

## Key Insight: Less Work Than Expected! 🎉

**Original Plan:**
- Create new `useAGUISession` hook ❌
- Create new `useRoomEvents` hook ❌
- Refactor existing WebSocket logic ❌

**Revised Plan:**
- ✅ Extend `useRoomStream` with 5 event handlers (15 min)
- ✅ Extend `useRoomMessages` with 5 mutations (45 min)
- ✅ Verify AG-UI compliance (30 min)
- ✅ Build UI components (same as before)

**Saved:** ~2 days of work by reusing existing infrastructure!

---

## Next Steps

1. **Verify backend endpoint** (10 min)
   - Is it `/ui/session` or `/api/v1/ws/rooms/{roomId}`?
   - Does handshake match AG-UI spec?

2. **Extend useRoomStream** (15 min)
   - Add Phase 5 event handlers
   - Test with backend

3. **Extend useRoomMessages** (45 min)
   - Add mutations
   - Update interface
   - Test each mutation

4. **Build UI components** (as planned)
   - MessageBadge, EditDrawer, etc.

**Ready to start? Let's begin with verifying the backend endpoint!**
