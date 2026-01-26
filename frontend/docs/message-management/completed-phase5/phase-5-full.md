  Implementation Plan: Message Management Features Suite

  ALL WORK COMPLETED AND DOCUMENTED.
  THIS IS AN HISTORICAL PLAN KEPT FOR REFERENCE - AND MAY NOT BE UPDATED WITH CURRENT STATE - BUT ALL FEATURES BELOW ARE ACTIVE AND VALID.

  Overview

  Features to implement:
  1. ✅ Toggle Message Context Inclusion (any participant)
  2. ✅ Delete Message (owner only)
  3. ✅ Edit Message (author or owner, shows "edited", no history, preserves active status)
  4. ✅ Pin Message (owner only, auto-marks active for context)
  5. ✅ Message Filtering UI (persistence TBD)

  ---
  Backend Implementation

  1. New Event Types

  // Already documented:
  "message.context_toggled"  // payload: { message_id, active_for_context, toggled_by }
  "message.deleted"          // payload: { message_id, deleted_by, deleted_at }

  // New events needed:
  "message.edited"           // payload: { message_id, new_content, edited_by, edited_at, original_content? }
  "message.pinned"           // payload: { message_id, pinned_by, pinned_at }
  "message.unpinned"         // payload: { message_id, unpinned_by, unpinned_at }

  2. Database Schema 

room_messages projection table:


tinyfoot=# \d room_messages
                           Table "public.room_messages"
       Column       |            Type             | Collation | Nullable | Default
--------------------+-----------------------------+-----------+----------+---------
 content            | character varying           |           | not null |
 sender_type        | character varying(20)       |           | not null |
 message_id         | uuid                        |           | not null |
 room_id            | uuid                        |           | not null |
 sender_id          | uuid                        |           |          |
 agent_name         | character varying(255)      |           |          |
 created_at         | timestamp without time zone |           | not null |
 button_options     | json                        |           |          |
 edited_at          | timestamp without time zone |           |          |
 edited_by          | uuid                        |           |          |
 is_pinned          | boolean                     |           | not null |
 pinned_at          | timestamp without time zone |           |          |
 pinned_by          | uuid                        |           |          |
 active_for_context | boolean                     |           | not null |
 ui_components      | jsonb                       |           |          |
Indexes:
    "room_messages_pkey" PRIMARY KEY, btree (message_id)
    "ix_room_messages_active_for_context" btree (active_for_context)
    "ix_room_messages_created_at" btree (created_at)
    "ix_room_messages_is_pinned" btree (is_pinned)
    "ix_room_messages_room_id" btree (room_id)
Foreign-key constraints:
    "room_messages_edited_by_fkey" FOREIGN KEY (edited_by) REFERENCES "user"(id)
    "room_messages_pinned_by_fkey" FOREIGN KEY (pinned_by) REFERENCES "user"(id)
    "room_messages_room_id_fkey" FOREIGN KEY (room_id) REFERENCES rooms(room_id)
    "room_messages_sender_id_fkey" FOREIGN KEY (sender_id) REFERENCES "user"(id)

  3. API Endpoints

  # Edit message
  PATCH /api/v1/rooms/{room_id}/messages/{message_id}
  Request: { "content": "new content" }
  Response: { message_id, content, edited_at, edited_by }
  Auth: Author OR room owner

  # Pin message
  POST /api/v1/rooms/{room_id}/messages/{message_id}/pin
  Response: { message_id, is_pinned: true, pinned_at, pinned_by }
  Auth: Room owner only

  # Unpin message
  DELETE /api/v1/rooms/{room_id}/messages/{message_id}/pin
  Response: RoomMessagePublic (returns updated message)
  Auth: Room owner only

  # Already documented:
  PATCH /api/v1/rooms/{room_id}/messages/{message_id}/context  # Toggle context
  DELETE /api/v1/rooms/{room_id}/messages/{message_id}          # Delete message

  4. Authorization Logic

  # ✅ IMPLEMENTED - Authorization helpers in backend/app/crud.py:

  async def check_can_edit_message(
      room_id: UUID,
      message_id: UUID,
      user_id: UUID,
      session: AsyncSession
  ) -> bool:
      """
      User messages: Author OR room owner can edit
      Agent messages: Owner only can edit
      Returns True if authorized
      """

  async def check_can_pin_message(
      room_id: UUID,
      user_id: UUID,
      session: AsyncSession
  ) -> bool:
      """Only room owner can pin. Returns True if authorized."""

  async def check_can_delete_message(
      room_id: UUID,
      user_id: UUID,
      session: AsyncSession
  ) -> bool:
      """Only room owner can delete. Returns True if authorized."""

  # Toggle context: Any active room participant (checked via check_room_membership)

  5. Event Handler Updates

  When message is pinned:
  # Pin handler must:
  1. Emit message.pinned event
  2. Update room_messages projection: is_pinned=True, pinned_at, pinned_by
  3. ALSO update active_for_context=True (auto-mark as active)
  4. Publish to Redis for WebSocket fan-out

  When message is edited:
  # Edit handler must:
  1. Emit message.edited event with new_content
  2. Update room_messages projection: content, edited_at, edited_by
  3. Do NOT change active_for_context status
  4. Publish to Redis for WebSocket fan-out

  ---
  Frontend Implementation

  1. Updated TypeScript Types

  // Update Message interface
  interface Message {
    message_id: string
    room_id: string
    content: string
    sender_id: string | null
    agent_name: string | null
    sender_type: 'user' | 'agent'
    active_for_context: boolean
    created_at: string

    // New fields:
    edited_at?: string
    edited_by?: string
    is_pinned: boolean
    pinned_at?: string
    pinned_by?: string
  }

  2. New API Client Functions

  // Auto-generated from OpenAPI after backend implementation
  RoomsService.editMessage({ roomId, messageId, requestBody: { content } })
  RoomsService.pinMessage({ roomId, messageId })
  RoomsService.unpinMessage({ roomId, messageId })
  RoomsService.toggleMessageContext({ roomId, messageId, requestBody: { active_for_context } })
  RoomsService.deleteMessage({ roomId, messageId })

  3. Component Structure

  New/Updated Components:

  frontend/src/components/
    Rooms/                          # Feature-specific (from ComponentDevelopmentWalkthrough)
      MessageList.tsx              # UPDATE: Add filtering, pinned section
      MessageItem.tsx              # UPDATE: Show edited indicator, pin badge
      MessageActions.tsx           # NEW: Dropdown/menu for all actions
      EditMessageDialog.tsx        # NEW: Inline or modal editor
      MessageFilters.tsx           # NEW: Filter controls
      PinnedMessagesSection.tsx    # NEW: Separate section for pinned messages

    Common/
      ConfirmationDialog.tsx       # UPDATE: Reuse for delete/unpin confirmations

  4. State Management Patterns

  // Message editing mutation
  const editMessageMutation = useMutation({
    mutationFn: ({ messageId, content }: { messageId: string; content: string }) =>
      RoomsService.editMessage({
        roomId,
        messageId,
        requestBody: { content }
      }),
    onSuccess: (data) => {
      showSuccessToast('Message updated')
      queryClient.invalidateQueries(['rooms', roomId, 'messages'])
    },
    onError: (err: ApiError) => {
      handleError(err)
    }
  })

  // Pin message mutation
  const pinMessageMutation = useMutation({
    mutationFn: (messageId: string) =>
      RoomsService.pinMessage({ roomId, messageId }),
    onSuccess: () => {
      showSuccessToast('Message pinned')
      queryClient.invalidateQueries(['rooms', roomId, 'messages'])
    },
    onError: (err: ApiError) => {
      handleError(err)
    }
  })

  // Message filtering state (localStorage + React state)
  const [filters, setFilters] = useState<MessageFilters>(() => {
    // Load from localStorage if user-preference persistence chosen
    const saved = localStorage.getItem(`room-${roomId}-filters`)
    return saved ? JSON.parse(saved) : defaultFilters
  })

  interface MessageFilters {
    showInactive: boolean      // Show messages not active for context
    showActive: boolean        // Show messages active for context
    showPinnedOnly: boolean    // Show only pinned messages
    senderFilter: 'all' | 'users' | 'agents' | string  // Specific sender
    dateRange?: { start: Date; end: Date }
  }

  5. WebSocket Event Handlers

  // Update existing handler to include new event types
  function handleRoomEvent(event: WebSocketMessage) {
    if (event.type !== 'event') return

    switch (event.event_type) {
      case 'message.context_toggled':
        updateMessageInCache(event.payload.message_id, {
          active_for_context: event.payload.active_for_context
        })
        break

      case 'message.deleted':
        removeMessageFromCache(event.payload.message_id)
        break

      case 'message.edited':
        updateMessageInCache(event.payload.message_id, {
          content: event.payload.new_content,
          edited_at: event.created_at,  // Use event timestamp
          edited_by: event.payload.edited_by
        })
        break

      case 'message.pinned':
        updateMessageInCache(event.payload.message_id, {
          is_pinned: true,
          pinned_at: event.created_at,  // Use event timestamp
          pinned_by: event.payload.pinned_by,
          active_for_context: true  // Auto-marked active
        })
        break

      case 'message.unpinned':
        updateMessageInCache(event.payload.message_id, {
          is_pinned: false,
          pinned_at: null,
          pinned_by: null
          // Note: active_for_context remains unchanged
        })
        break
    }
  }

  6. UI/UX Patterns

  MessageItem Component:
  // Visual indicators needed:
  - "Edited" badge (small, subtle, with timestamp on hover)
  - Pin icon (prominent, maybe gold/yellow color)
  - Active/inactive indicator (opacity or badge)
  - Sender attribution (user name or agent name)

  // Action menu (shown on hover or via overflow menu):
  - Edit (if author or owner, not for agent messages)
  - Delete (if owner)
  - Pin/Unpin (if owner)
  - Toggle Context (any participant)
  - Copy message

  PinnedMessagesSection:
  // At top of message list or collapsible section
  - Shows all pinned messages
  - Sorted by pinned_at (newest first? or custom order later?)
  - Click to scroll to message in main list (optional)
  - Unpin action available to room owner

  MessageFilters Component:
  // Filter controls (probably as a toolbar above message list)
  - Checkbox: "Show active for context" (default: true)
  - Checkbox: "Show inactive for context" (default: true)
  - Checkbox: "Show pinned only" (default: false)
  - Dropdown: "Filter by sender" (All / Users / Agents / Specific person)
  - Date range picker (optional, can defer)
  - Clear filters button

  ---
  Implementation Order

  Phase 1: Backend Foundation (2-3 days) (COMPLETE)

  1. Add database columns to room_messages projection
  2. Create Alembic migration
  3. Implement edit message endpoint + authorization
  4. Implement pin/unpin endpoints + authorization
  5. Add event emission for message.edited, message.pinned, message.unpinned
  6. Update event handlers to update projections correctly
  7. Test authorization patterns thoroughly
  8. Update OpenAPI spec

  Phase 2: Frontend Core Features (2-3 days) 

  1. Regenerate API client
  2. Update Message TypeScript interface
  3. Implement MessageActions component (action menu/dropdown)
  4. Implement EditMessageDialog component
  5. Add mutations for edit, pin, unpin
  6. Update MessageItem to show edited/pinned indicators
  7. Update WebSocket event handlers

  Phase 3: Filtering & Polish (1-2 days)

  1. Implement MessageFilters component
  2. Add filtering logic to message list
  3. Implement PinnedMessagesSection (optional separate section)
  4. Add filter persistence (localStorage or backend, based on your decision)
  5. Polish UI/UX (confirmations, loading states, optimistic updates)
  6. Test all features together

  Phase 4: Testing & Documentation (1 day)

  1. Test all permission patterns
  2. Test WebSocket propagation for all events
  3. Test filter combinations
  4. Update user-facing documentation
  5. Add E2E tests for critical paths


    Final Implementation Plan: Message Management Features Suite

  Specifications Summary

  ✅ Filter Persistence: localStorage (per-browser)
  ✅ Pinned Messages: Separate section at top + inline badges
  ✅ Edit UI: Slide-out panel
  ✅ Agent Message Editing: Owner only
  ✅ Filtering: Server-side with query parameters

  ---
  Backend Implementation Details

  ✅ COMPLETE - All backend features implemented!

  Implemented Components:
  - ✅ Database schema with edited_at, edited_by, is_pinned, pinned_at, pinned_by fields
  - ✅ Event-sourced architecture with message.edited, message.pinned, message.unpinned events
  - ✅ Authorization helpers: check_can_edit_message, check_can_pin_message, check_can_delete_message
  - ✅ CRUD functions: edit_message, pin_message, unpin_message, toggle_message_context, delete_message
  - ✅ Event handlers in event_emitter.py for all new event types
  - ✅ API routes with proper authorization, transactions, and error handling
  - ✅ Redis pub/sub for real-time WebSocket updates

  Files Modified:
  - backend/app/models.py - Added MessageEdit, MessageContextToggle request models
  - backend/app/crud.py - Added authorization helpers and CRUD functions
  - backend/app/services/event_emitter.py - Added 5 new event handlers
  - backend/app/api/routes/rooms.py - Added 5 new route endpoints

  Ready for Frontend Implementation!

  WebSocket Event Payloads (from backend):

  All events follow this structure:
  {
    "type": "event",
    "sequence": <room_sequence_number>,
    "event_type": "<event_type>",
    "payload": { ... },
    "created_at": "<ISO_timestamp>"
  }

  Event Payloads:

  message.edited:
  {
    "message_id": "uuid-string",
    "new_content": "edited text",
    "edited_by": "user-uuid-string"
  }
  Note: edited_at comes from event.created_at (not in payload)

  message.pinned:
  {
    "message_id": "uuid-string",
    "pinned_by": "user-uuid-string"
  }
  Notes:
  - pinned_at comes from event.created_at (not in payload)
  - Backend automatically sets active_for_context=true

  message.unpinned:
  {
    "message_id": "uuid-string"
  }

  message.context_toggled:
  {
    "message_id": "uuid-string",
    "active_for_context": true/false
  }

  message.deleted:
  {
    "message_id": "uuid-string",
    "deleted_by": "user-uuid-string"
  }

  ---
  Frontend Implementation Details

  1. Component Architecture

  frontend/src/components/Rooms/
  ├── MessageList.tsx                 # Container - fetches with filters, shows pinned section
  ├── PinnedMessagesSection.tsx       # Top section showing pinned messages
  ├── MessageItem.tsx                 # Individual message with badges/indicators
  ├── MessageActionMenu.tsx           # Dropdown menu for message actions
  ├── MessageFilters.tsx              # Filter toolbar (room-specific wrapper)
  └── hooks/
      ├── useMessageFilters.ts        # Filter state + localStorage + debouncing
      ├── useMessageMutations.ts      # All message mutations
      ├── useRoomPermissions.ts       # Permission checks (owner, author, etc.)
      └── useRoomEvents.ts            # AG-UI event handler for room (NEW)

  frontend/src/components/Common/
  ├── EditDrawer.tsx                  # Generic slide-out drawer (extracted from Rooms)
  └── (FilterToolbar.tsx)             # Optional: Generic filter controls

  frontend/src/components/ui/
  └── message-badge.tsx               # Reusable status badges (edited, pinned, active)

  frontend/src/hooks/
  └── useAGUISession.ts               # AG-UI WebSocket connection + sequence tracking (NEW)

  2. AG-UI WebSocket Session Hook (CRITICAL)

  // frontend/src/hooks/useAGUISession.ts
  // Implements AG-UI protocol from Minimog.md (AP4)

  interface AGUIEvent {
    type: 'event'
    sequence: number
    event_type: string
    payload: Record<string, any>
    created_at: string
  }

  interface AGUISessionOptions {
    roomId: string
    onEvent: (event: AGUIEvent) => void
    onReconnect?: () => void
  }

  export function useAGUISession({ roomId, onEvent, onReconnect }: AGUISessionOptions) {
    const { user } = useAuth()
    const wsRef = useRef<WebSocket | null>(null)

    const [lastSequence, setLastSequence] = useState(() => {
      // Load from localStorage for persistence across page reloads
      const stored = localStorage.getItem(`room-${roomId}-last-seq`)
      return stored ? parseInt(stored, 10) : 0
    })

    const [connectionState, setConnectionState] = useState<'connecting' | 'connected' | 'disconnected'>('connecting')

    useEffect(() => {
      const ws = new WebSocket(`${import.meta.env.VITE_WS_URL}/ui/session`)
      wsRef.current = ws

      ws.onopen = () => {
        // AG-UI handshake (Minimog.md C3.1)
        ws.send(JSON.stringify({
          auth: { token: user.token },
          room_id: roomId,
          last_sequence: lastSequence  // Request replay from this point
        }))
        setConnectionState('connected')
      }

      ws.onmessage = (msg) => {
        const event: AGUIEvent = JSON.parse(msg.data)

        if (event.type === 'event') {
          // Update last sequence and persist
          setLastSequence(event.sequence)
          localStorage.setItem(`room-${roomId}-last-seq`, String(event.sequence))

          // Forward to event handler
          onEvent(event)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setConnectionState('disconnected')
      }

      ws.onclose = () => {
        setConnectionState('disconnected')
        // Reconnect after delay with event replay
        setTimeout(() => {
          if (onReconnect) onReconnect()
        }, 2000)
      }

      return () => {
        ws.close()
      }
    }, [roomId, lastSequence, user.token, onEvent, onReconnect])

    return {
      lastSequence,
      connectionState,
      disconnect: () => wsRef.current?.close()
    }
  }

  3. Room Events Handler Hook

  // frontend/src/components/Rooms/hooks/useRoomEvents.ts
  // Handles all AG-UI events for a room

  export function useRoomEvents(roomId: string) {
    const queryClient = useQueryClient()

    const updateMessageInCache = useCallback((messageId: string, updates: Partial<Message>) => {
      queryClient.setQueryData(
        ['rooms', roomId, 'messages'],
        (old: { data: Message[] } | undefined) => {
          if (!old) return old
          return {
            ...old,
            data: old.data.map(msg =>
              msg.message_id === messageId ? { ...msg, ...updates } : msg
            )
          }
        }
      )
    }, [queryClient, roomId])

    const removeMessageFromCache = useCallback((messageId: string) => {
      queryClient.setQueryData(
        ['rooms', roomId, 'messages'],
        (old: { data: Message[] } | undefined) => {
          if (!old) return old
          return {
            ...old,
            data: old.data.filter(msg => msg.message_id !== messageId)
          }
        }
      )
    }, [queryClient, roomId])

    const handleEvent = useCallback((event: AGUIEvent) => {
      // Event catalog from Minimog.md + Phase 5 extensions
      switch (event.event_type) {
        // Core AG-UI events (Minimog.md)
        case 'room.created':
        case 'room.updated':
          queryClient.invalidateQueries(['rooms', roomId])
          break

        case 'participant.joined':
        case 'participant.left':
        case 'participant.role_changed':
          queryClient.invalidateQueries(['rooms', roomId, 'participants'])
          break

        case 'room_message.user':
        case 'room_message.agent':
          queryClient.invalidateQueries(['rooms', roomId, 'messages'])
          break

        // Phase 5: Message Management Events
        case 'message.edited':
          updateMessageInCache(event.payload.message_id, {
            content: event.payload.new_content,
            edited_at: event.created_at,  // Use event timestamp
            edited_by: event.payload.edited_by
          })
          break

        case 'message.pinned':
          updateMessageInCache(event.payload.message_id, {
            is_pinned: true,
            pinned_at: event.created_at,  // Use event timestamp
            pinned_by: event.payload.pinned_by,
            active_for_context: true  // Auto-marked active
          })
          break

        case 'message.unpinned':
          updateMessageInCache(event.payload.message_id, {
            is_pinned: false,
            pinned_at: null,
            pinned_by: null
            // Note: active_for_context remains unchanged
          })
          break

        case 'message.context_toggled':
          updateMessageInCache(event.payload.message_id, {
            active_for_context: event.payload.active_for_context
          })
          break

        case 'message.deleted':
          removeMessageFromCache(event.payload.message_id)
          break

        default:
          console.warn('Unhandled event type:', event.event_type)
      }
    }, [queryClient, roomId, updateMessageInCache, removeMessageFromCache])

    // Connect to AG-UI session
    const { lastSequence, connectionState } = useAGUISession({
      roomId,
      onEvent: handleEvent,
      onReconnect: () => {
        // Refresh entire room state on reconnect
        queryClient.invalidateQueries(['rooms', roomId])
      }
    })

    return { lastSequence, connectionState }
  }

  4. Message Filters Hook (Updated with Debouncing)

  // frontend/src/components/Rooms/hooks/useMessageFilters.ts

  interface MessageFilters {
    activeForContext: boolean | null   // null = both, true = active only, false = inactive only
    isPinned: boolean | null          // null = both, true = pinned only
    senderType: 'all' | 'user' | 'agent'
    senderId: string | null           // Specific sender UUID
  }

  const DEFAULT_FILTERS: MessageFilters = {
    activeForContext: null,  // Show both by default
    isPinned: null,          // Show both
    senderType: 'all',
    senderId: null
  }

  export function useMessageFilters(roomId: string) {
    const [filters, setFilters] = useState<MessageFilters>(() => {
      try {
        const stored = localStorage.getItem(`room-${roomId}-filters`)
        return stored ? JSON.parse(stored) : DEFAULT_FILTERS
      } catch {
        return DEFAULT_FILTERS
      }
    })

    // Debounced filters for API queries (avoid excessive calls)
    const [debouncedFilters, setDebouncedFilters] = useState(filters)

    // Persist to localStorage on change
    useEffect(() => {
      localStorage.setItem(`room-${roomId}-filters`, JSON.stringify(filters))
    }, [filters, roomId])

    // Debounce filter changes (300ms delay)
    useEffect(() => {
      const timer = setTimeout(() => {
        setDebouncedFilters(filters)
      }, 300)

      return () => clearTimeout(timer)
    }, [filters])

    const updateFilter = <K extends keyof MessageFilters>(
      key: K,
      value: MessageFilters[K]
    ) => {
      setFilters(prev => ({ ...prev, [key]: value }))
    }

    const clearFilters = () => setFilters(DEFAULT_FILTERS)

    return {
      filters,           // For UI state (immediate)
      debouncedFilters,  // For API queries (debounced)
      updateFilter,
      clearFilters
    }
  }

  5. Message Mutations Hook

  // frontend/src/components/Rooms/hooks/useMessageMutations.ts

  export function useMessageMutations(roomId: string) {
    const queryClient = useQueryClient()
    const { showSuccessToast, showErrorToast } = useCustomToast()

    const editMessage = useMutation({
      mutationFn: ({ messageId, content }: { messageId: string; content: string }) =>
        RoomsService.editMessage({ roomId, messageId, requestBody: { content } }),
      onSuccess: () => {
        showSuccessToast('Message updated')
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      },
      onError: (err: ApiError) => handleError(err, showErrorToast)
    })

    const pinMessage = useMutation({
      mutationFn: (messageId: string) =>
        RoomsService.pinMessage({ roomId, messageId }),
      onSuccess: () => {
        showSuccessToast('Message pinned')
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      },
      onError: (err: ApiError) => handleError(err, showErrorToast)
    })

    const unpinMessage = useMutation({
      mutationFn: (messageId: string) =>
        RoomsService.unpinMessage({ roomId, messageId }),
      onSuccess: () => {
        showSuccessToast('Message unpinned')
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      },
      onError: (err: ApiError) => handleError(err, showErrorToast)
    })

    const toggleContext = useMutation({
      mutationFn: ({ messageId, active }: { messageId: string; active: boolean }) =>
        RoomsService.toggleMessageContext({
          roomId,
          messageId,
          requestBody: { active_for_context: active }
        }),
      onSuccess: () => {
        showSuccessToast('Context updated')
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      },
      onError: (err: ApiError) => handleError(err, showErrorToast)
    })

    const deleteMessage = useMutation({
      mutationFn: (messageId: string) =>
        RoomsService.deleteMessage({ roomId, messageId }),
      onSuccess: () => {
        showSuccessToast('Message deleted')
        queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      },
      onError: (err: ApiError) => handleError(err, showErrorToast)
    })

    return {
      editMessage,
      pinMessage,
      unpinMessage,
      toggleContext,
      deleteMessage
    }
  }

  6. Room Permissions Hook

  // frontend/src/components/Rooms/hooks/useRoomPermissions.ts

  export function useRoomPermissions(room: Room, currentUserId: string) {
    const isOwner = room.created_by === currentUserId

    const canEditMessage = (message: Message) => {
      // Agent messages: owner only
      if (message.sender_type === 'agent') {
        return isOwner
      }
      // User messages: author or owner
      return message.sender_id === currentUserId || isOwner
    }

    const canDeleteMessage = () => isOwner

    const canPinMessage = () => isOwner

    const canToggleContext = () => true  // Any participant

    return {
      isOwner,
      canEditMessage,
      canDeleteMessage,
      canPinMessage,
      canToggleContext
    }
  }

  7. Message Badge UI Component (Design System)

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
      active: { icon: FaCheckCircle, color: 'green.500', label: 'Active for Context' },
      inactive: { icon: FaCircle, color: 'gray.400', label: 'Inactive' }
    }[variant]

    return (
      <Tooltip label={timestamp ? `${config.label} - ${timestamp}` : config.label}>
        <Badge
          display="inline-flex"
          alignItems="center"
          gap={1}
          fontSize="xs"
          color={config.color}
          variant="subtle"
        >
          <Icon as={config.icon} boxSize={3} />
          {config.label}
        </Badge>
      </Tooltip>
    )
  }

  // Usage in MessageItem:
  // <MessageBadge variant="edited" timestamp={message.edited_at} />
  // <MessageBadge variant="pinned" timestamp={message.pinned_at} />

  8. Edit Message Panel Component

  // frontend/src/components/Common/EditDrawer.tsx (extracted to Common for reusability)

  interface EditMessagePanelProps {
    message: Message
    isOpen: boolean
    onClose: () => void
    onSave: (content: string) => void
    isSaving: boolean
  }

  export default function EditMessagePanel({
    message,
    isOpen,
    onClose,
    onSave,
    isSaving
  }: EditMessagePanelProps) {
    const [content, setContent] = useState(message.content)

    useEffect(() => {
      setContent(message.content)
    }, [message.content])

    const handleSave = () => {
      if (content.trim() && content !== message.content) {
        onSave(content)
      }
    }

    return (
      <Drawer
        isOpen={isOpen}
        placement="right"
        onClose={onClose}
        size="md"
      >
        <DrawerOverlay />
        <DrawerContent>
          <DrawerHeader>Edit Message</DrawerHeader>
          <DrawerCloseButton />

          <DrawerBody>
            <VStack spacing={4} align="stretch">
              <Text fontSize="sm" color="gray.600">
                Original sender: {message.sender_type === 'agent'
                  ? message.agent_name
                  : 'User'}
              </Text>

              <Textarea
                value={content}
                onChange={(e) => setContent(e.target.value)}
                rows={10}
                placeholder="Edit message content..."
              />

              <Text fontSize="xs" color="gray.500">
                Note: Editing does not change whether this message is included in agent context.
              </Text>
            </VStack>
          </DrawerBody>

          <DrawerFooter gap={2}>
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleSave}
              isLoading={isSaving}
              isDisabled={!content.trim() || content === message.content}
            >
              Save Changes
            </Button>
          </DrawerFooter>
        </DrawerContent>
      </Drawer>
    )
  }

  9. Message Filters Component

  // frontend/src/components/Rooms/MessageFilters.tsx

  interface MessageFiltersProps {
    filters: MessageFilters
    onFilterChange: <K extends keyof MessageFilters>(
      key: K,
      value: MessageFilters[K]
    ) => void
    onClearFilters: () => void
  }

  export default function MessageFilters({
    filters,
    onFilterChange,
    onClearFilters
  }: MessageFiltersProps) {
    return (
      <HStack spacing={4} p={4} bg="gray.50" borderRadius="md">
        <Text fontWeight="medium" fontSize="sm">Filters:</Text>

        {/* Active/Inactive Filter */}
        <Select
          size="sm"
          maxW="200px"
          value={filters.activeForContext === null ? 'all' : filters.activeForContext.toString()}
          onChange={(e) => {
            const val = e.target.value
            onFilterChange('activeForContext',
              val === 'all' ? null : val === 'true'
            )
          }}
        >
          <option value="all">All Messages</option>
          <option value="true">Active for Context</option>
          <option value="false">Inactive for Context</option>
        </Select>

        {/* Pinned Filter */}
        <Select
          size="sm"
          maxW="180px"
          value={filters.isPinned === null ? 'all' : filters.isPinned.toString()}
          onChange={(e) => {
            const val = e.target.value
            onFilterChange('isPinned',
              val === 'all' ? null : val === 'true'
            )
          }}
        >
          <option value="all">All / Pinned</option>
          <option value="true">Pinned Only</option>
          <option value="false">Unpinned Only</option>
        </Select>

        {/* Sender Type Filter */}
        <Select
          size="sm"
          maxW="150px"
          value={filters.senderType}
          onChange={(e) => onFilterChange('senderType', e.target.value as any)}
        >
          <option value="all">All Senders</option>
          <option value="user">Users Only</option>
          <option value="agent">Agents Only</option>
        </Select>

        {/* Clear Filters Button */}
        <IconButton
          size="sm"
          icon={<FaTimes />}
          aria-label="Clear filters"
          onClick={onClearFilters}
          variant="ghost"
        />
      </HStack>
    )
  }

  10. Message List with Filters and AG-UI Events

  // frontend/src/components/Rooms/MessageList.tsx

  export default function MessageList({ roomId }: { roomId: string }) {
    const { filters, debouncedFilters, updateFilter, clearFilters } = useMessageFilters(roomId)

    // Connect to AG-UI session for real-time updates
    const { connectionState } = useRoomEvents(roomId)

    // Fetch messages with server-side filters (debounced to avoid excessive API calls)
    const { data, isLoading } = useQuery({
      queryKey: ['rooms', roomId, 'messages', debouncedFilters],
      queryFn: () => RoomsService.getMessages({
        roomId,
        activeForContext: debouncedFilters.activeForContext,
        isPinned: debouncedFilters.isPinned,
        senderType: debouncedFilters.senderType === 'all' ? undefined : debouncedFilters.senderType,
        senderId: debouncedFilters.senderId
      })
    })

    const messages = data?.data || []
    const pinnedMessages = messages.filter(m => m.is_pinned)
    const regularMessages = messages.filter(m => !m.is_pinned)

    return (
      <VStack align="stretch" spacing={4}>
        {/* Filter Toolbar */}
        <MessageFilters
          filters={filters}
          onFilterChange={updateFilter}
          onClearFilters={clearFilters}
        />

        {/* Pinned Messages Section */}
        {pinnedMessages.length > 0 && (
          <PinnedMessagesSection
            messages={pinnedMessages}
            roomId={roomId}
          />
        )}

        {/* Regular Messages */}
        <VStack align="stretch" spacing={2}>
          {regularMessages.map(message => (
            <MessageItem
              key={message.message_id}
              message={message}
              roomId={roomId}
            />
          ))}
        </VStack>

        {isLoading && <Spinner />}
        {!isLoading && messages.length === 0 && (
          <Text color="gray.500" textAlign="center">
            No messages match the current filters
          </Text>
        )}
      </VStack>
    )
  }

  11. Pinned Messages Section

  // frontend/src/components/Rooms/PinnedMessagesSection.tsx

  export default function PinnedMessagesSection({
    messages,
    roomId
  }: {
    messages: Message[]
    roomId: string
  }) {
    return (
      <Box
        bg="yellow.50"
        borderLeft="4px solid"
        borderColor="yellow.400"
        p={4}
        borderRadius="md"
      >
        <HStack mb={2}>
          <Icon as={FaThumbTack} color="yellow.600" />
          <Text fontWeight="bold" color="yellow.800">
            Pinned Messages ({messages.length})
          </Text>
        </HStack>

        <VStack align="stretch" spacing={2}>
          {messages.map(message => (
            <MessageItem
              key={message.message_id}
              message={message}
              roomId={roomId}
              compact={true}  // Optional compact view
            />
          ))}
        </VStack>
      </Box>
    )
  }

  12. Connection Status Indicator (Optional Enhancement)

  // Show WebSocket connection status to users

  const ConnectionStatus = ({ state }: { state: 'connecting' | 'connected' | 'disconnected' }) => {
    const config = {
      connecting: { color: 'orange', icon: FaSpinner, label: 'Connecting...' },
      connected: { color: 'green', icon: FaCheckCircle, label: 'Connected' },
      disconnected: { color: 'red', icon: FaExclamationCircle, label: 'Disconnected' }
    }[state]

    return (
      <HStack spacing={2} fontSize="sm" color={`${config.color}.600`}>
        <Icon as={config.icon} boxSize={4} />
        <Text>{config.label}</Text>
      </HStack>
    )
  }

  // Usage in MessageList:
  // <ConnectionStatus state={connectionState} />

  ---
  Implementation Phases

  Phase 1: Backend - Database & Core Endpoints ✅ COMPLETE

  Tasks:
  1. ✅ Add edited_at, edited_by, is_pinned, pinned_at, pinned_by to RoomMessage model
  2. ✅ Create Alembic migration: alembic revision --autogenerate -m "Add message editing and pinning"
  3. ✅ Run migration: alembic upgrade head
  4. ✅ Implement PATCH /rooms/{room_id}/messages/{message_id} (edit)
  5. ✅ Implement POST /rooms/{room_id}/messages/{message_id}/pin
  6. ✅ Implement DELETE /rooms/{room_id}/messages/{message_id}/pin
  7. ✅ Update GET /rooms/{room_id}/messages with filter parameters
  8. ✅ Implement authorization helpers (can_edit_message, etc.)
  9. ✅ Add event emission for message.edited, message.pinned, message.unpinned
  10. ✅ Test all endpoints with Swagger UI
  11. ✅ Test authorization edge cases (agent messages, non-owners, etc.)

  Success Criteria:
  - All endpoints return correct responses
  - Authorization blocks unauthorized actions
  - Events are emitted and projections updated transactionally
  - Pinning auto-marks message as active for context
  - Editing preserves active_for_context status

  ---
  Phase 2: Frontend - AG-UI Compliance & Core Hooks (2-3 days) 🔴 CRITICAL

  Tasks:
  1. ✅  Create useAGUISession.ts hook (WebSocket handshake + sequence tracking)
  2. ✅  Create useRoomEvents.ts hook (event handling + cache updates)
  3. ✅  Test WebSocket reconnection and event replay
  4. ✅  Verify sequence tracking persists in localStorage
  5. ✅ Regenerate OpenAPI client: cd frontend && npm run generate-client
  6. ✅ Create useMessageFilters.ts hook with localStorage + debouncing
  7. ✅ Create useMessageMutations.ts hook with all mutations
  8. ✅ Create useRoomPermissions.ts hook
  9. ✅ Update TypeScript Message interface

  Success Criteria:
  - AG-UI handshake completes successfully with JWT auth
  - Sequence tracking works (last_sequence persists and replays)
  - WebSocket reconnection triggers event replay
  - All message management events handled correctly
  - API client types match backend spec
  - Filters debounce properly (300ms delay)
  - Mutations trigger cache invalidation
  - Permissions computed correctly

  ---
  Phase 3: Frontend - UI Components (2-3 days)

  Tasks:
  1. ✅ Create ui/message-badge.tsx (reusable design system component)
  2. ✅ Create Common/EditDrawer.tsx (generic slide-out drawer)
  3. ✅ Create Rooms/MessageFilters.tsx (room-specific filter toolbar)
  4. ✅ Create Rooms/PinnedMessagesSection.tsx
  5. ✅ Update Rooms/MessageItem.tsx to show badges using MessageBadge component
  6. ✅ Update Rooms/MessageActionMenu.tsx with all actions
  7. ✅ Update Rooms/MessageList.tsx to:
     - Use useRoomEvents for AG-UI connection
     - Use debounced filters for API queries
     - Show connection status indicator
     - Display pinned section
  8. ✅ Add confirmation dialogs for destructive actions
  9. ✅ Add ConnectionStatus indicator component (optional)

  Success Criteria:
  - Edit drawer opens/closes smoothly
  - Filters update message list with debouncing (no excessive API calls)
  - Pinned messages appear in dedicated section at top
  - Visual indicators (badges) show message state clearly
  - Actions menu shows/hides based on permissions
  - Connection status visible to users
  - Real-time updates work via AG-UI WebSocket

  ---
  Phase 4: Integration & Testing (1-2 days)

  Tasks:
  1. ✅  Test AG-UI WebSocket handshake and connection
  2. ✅  Test event replay on reconnection (disconnect, reconnect, verify catch-up)
  3. ✅  Test sequence tracking persistence (page reload, verify last_sequence)
  4. ✅ Test full edit workflow (open panel, edit, save, see real-time update)
  5. ✅ Test pin/unpin workflow (pin message, appears in section, unpin)
  6. ✅ Test filtering with debouncing (verify 300ms delay, no excessive calls)
  7. ✅ Test multi-user scenarios (user A edits, user B sees real-time update via WebSocket)
  8. ✅ Test WebSocket real-time updates for all event types
  9. ✅ Test permission boundaries (non-owner can't delete, agent msg editing, etc.)
  10. ✅ Test edge cases (empty states, error handling, network failures, WebSocket errors)
  11. ✅ Performance test with 100+ messages
  12. ✅ Test connection status indicator updates
  13. ✅ Write E2E tests for critical paths

  Success Criteria:
  - AG-UI handshake works with JWT authentication
  - Event replay catches up missed events after reconnection
  - Sequence tracking persists across page reloads
  - All features work end-to-end
  - Real-time updates propagate correctly to all connected clients
  - Filters debounce properly and perform well with large message lists
  - No permission bypasses
  - Error states handled gracefully (WebSocket disconnect, API errors)
  - Connection status visible and accurate

  ---
  Testing Checklist

  Backend Tests

  - Edit message: author can edit their own messages
  - Edit message: owner can edit any user message
  - Edit message: owner can edit agent messages
  - Edit message: non-owner cannot edit others' messages
  - Edit message: editing preserves active_for_context
  - Pin message: owner can pin
  - Pin message: non-owner cannot pin
  - Pin message: pinning sets active_for_context = true
  - Unpin message: owner can unpin
  - Unpin message: unpinning preserves active_for_context
  - Filter messages: active_for_context=true returns only active
  - Filter messages: is_pinned=true returns only pinned
  - Filter messages: sender_type=agent returns only agent messages
  - Filter messages: combined filters work correctly
  - Events emitted for all operations
  - Projections updated transactionally

  Frontend Tests

  - Edit panel opens when clicking edit action
  - Edit panel saves and closes on successful edit
  - Edit panel shows loading state during save
  - Filters update URL/state and fetch filtered results
  - Pinned messages appear in top section
  - Pinned messages also appear inline with badge
  - Message badges show correct state (edited, pinned, active/inactive)
  - Action menu shows only permitted actions
  - WebSocket updates reflected immediately
  - Filter persistence works across page reloads
  - Empty states show helpful messages
  - Error handling shows appropriate toasts

  ---
