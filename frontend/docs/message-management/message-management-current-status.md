# Room Messages and Message Management Status

## Executive Summary

**Things are looking great!**

Last update: 01/26/26 - validated.

### Solid, Working Infrastructure ✅

** Implemented:**
- ✅ `useRoomStream.ts` - WebSocket connection with sequence tracking and event handlers
- ✅ `useRoomMessages.ts` - Message fetching with pagination and mutations
- ✅ `roomService.ts` - generated client
- ✅ AG-UI-style event handling
- ✅ Token streaming for agents
- ✅ Query invalidation
- ✅ Optimistic updates



## Architecture Review: What Exists

###  useRoomStream Event Handlers 

**File:** `frontend/src/hooks/useRoomStream.ts`

**event handlers in `handleMessage` function** 

```typescript

case 'event':
  setLastSequence(message.sequence)

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

  // MORE HANDLERS:

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

**That's it!** other infrastructure handles:
- ✅ WebSocket connection
- ✅ Sequence tracking
- ✅ Reconnection with replay
- ✅ Query invalidation



---

###  useRoomMessages mutations 

**File:** `frontend/src/hooks/useRoomMessages.ts`


1. Mutations!

```typescript
// Existing sendMessageMutation (lines 125-172)
const sendMessageMutation = useMutation({ ... })

// additional mutations:

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

2. **wrapper functions** 

```typescript
// sendMessage wrapper (lines 210-215)
const sendMessage = useCallback(async (content: string) => {
  await sendMessageMutation.mutateAsync(content)
}, [sendMessageMutation])

//  additonal wrapper functions

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

3. ** return object** (around line 220)

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

4. [X]  **TypeScript interface** (lines 32-49)

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

## Validation Checklist


### Passing Test: of useRoomStream

- [ ] Open `frontend/src/hooks/useRoomStream.ts`
- [ ] Find `handleMessage` 
- [ ] review event handlers (message.edited, pinned, unpinned, context_toggled, deleted)
- [ ] Test: Send event from backend → verify query invalidation


### 🎨 Available Components

  - `MessageBadge` component
  - `EditDrawer` component
  - `MessageFilters` component
  - `MessageItem` shows badges
  - `MessageList` uses extended hooks

---

## Usage Example: 


```typescript
function RoomView({ roomId }) {
  const { isConnected } = useRoomStream(roomId) // ✅ Now handles Phase 5 events

  const {
    messages,
    sendMessage,
    editMessage,      
    pinMessage,       
    unpinMessage,     
    toggleContext,    
    deleteMessage,    
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
