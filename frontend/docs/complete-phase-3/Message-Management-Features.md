# Message Management Features - Frontend Implementation Guide

**Date:** 2025-12-30
**Target Audience:** Frontend Developers
**Backend API Version:** v1

---

## Overview

This document provides guidance for implementing two message management features:

1. **Toggle Message Context Inclusion** - Mark messages as active/inactive for agent context
2. **Delete Message** - Permanently remove messages (room owner only)

**Important Notes:**
- This guide focuses on backend API integration and data flow
- UI component selection and design are left to frontend team discretion
- All operations follow event sourcing patterns (append-only, immutable)

---

## Feature 1: Toggle Message Context Inclusion

### Purpose

Allow users to exclude specific messages from being included in agent context without deleting them. This is useful for:
- Removing off-topic messages from agent consideration
- Excluding old/outdated information
- Fine-tuning agent responses by controlling what context they see

### Backend Behavior

**Event Sourcing Pattern:**
- Messages are **never modified** in the database
- A new event is emitted: `message.context_toggled`
- The `room_messages` projection is updated with the new `active_for_context` status
- Previous message content remains unchanged and visible in the event log

**Authorization:**
- Any active room participant can toggle message context status
- No special permissions required (unlike delete)

### API Endpoint

```typescript
PATCH /api/v1/rooms/{room_id}/messages/{message_id}/context
```

**Request Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
```json
{
  "active_for_context": false  // or true
}
```

**Success Response (200 OK):**
```json
{
  "message_id": "uuid",
  "room_id": "uuid",
  "active_for_context": false,
  "updated_at": "2025-12-30T12:00:00Z"
}
```

**Error Responses:**

```json
// 403 Forbidden - Not a room participant
{
  "detail": "Access denied"
}

// 404 Not Found - Message doesn't exist
{
  "detail": "Message not found"
}

// 404 Not Found - Room doesn't exist
{
  "detail": "Room not found"
}
```

### Expected Backend Events

When a message context status is toggled, the backend emits:

```json
{
  "type": "event",
  "sequence": 123,
  "event_type": "message.context_toggled",
  "payload": {
    "message_id": "uuid",
    "active_for_context": false,
    "toggled_by": "user_uuid"
  },
  "created_at": "2025-12-30T12:00:00Z"
}
```

**WebSocket Delivery:**
- If WebSocket connected, all room participants receive this event in real-time
- Frontend should update local message state when receiving this event
- REST API polling clients will see changes on next refresh

### Frontend Implementation Considerations

#### State Management

```typescript
// Example state structure (adapt to your state management solution)
interface Message {
  message_id: string
  room_id: string
  content: string
  sender_id: string | null
  agent_name: string | null
  sender_type: 'user' | 'agent'
  active_for_context: boolean  // ← Key field
  created_at: string
}
```

#### API Call Pattern

```typescript
// Example API call (adapt to your HTTP client)
async function toggleMessageContext(
  roomId: string,
  messageId: string,
  activeForContext: boolean
): Promise<void> {
  const response = await fetch(
    `/api/v1/rooms/${roomId}/messages/${messageId}/context`,
    {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ active_for_context: activeForContext }),
    }
  )

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('You do not have permission to modify this message')
    }
    if (response.status === 404) {
      throw new Error('Message not found')
    }
    throw new Error('Failed to update message')
  }

  return response.json()
}
```

#### WebSocket Event Handling

```typescript
// Example WebSocket event handler
function handleWebSocketMessage(event: WebSocketMessage) {
  if (event.type === 'event' && event.event_type === 'message.context_toggled') {
    const { message_id, active_for_context } = event.payload

    // Update local state to reflect the change
    updateMessageInCache(message_id, { active_for_context })

    // If using React Query or similar, invalidate cache
    queryClient.invalidateQueries(['rooms', roomId, 'messages'])
  }
}
```

#### Optimistic Updates (Optional)

```typescript
// Example optimistic update pattern
async function toggleMessageContextOptimistic(
  messageId: string,
  newStatus: boolean
) {
  // 1. Immediately update local state
  const previousState = getMessageState(messageId)
  updateMessageInCache(messageId, { active_for_context: newStatus })

  try {
    // 2. Make API call
    await toggleMessageContext(roomId, messageId, newStatus)

    // 3. Success - optimistic update was correct
    // (WebSocket event will confirm or state is already correct)

  } catch (error) {
    // 4. Error - rollback to previous state
    updateMessageInCache(messageId, { active_for_context: previousState })

    // Show error to user
    showError('Failed to update message. Please try again.')
  }
}
```

#### UI/UX Considerations

**Visual Indicators:**
- Messages inactive for context should be visually distinct (e.g., opacity, badge, icon)
- Consider showing a tooltip explaining what "inactive for context" means
- Provide clear affordance for toggling (button, toggle switch, menu item)

**User Feedback:**
- Show loading state while API call is in progress
- Show success confirmation (toast, message state change)
- Show error message if operation fails

**Edge Cases:**
- Disable toggle UI if user is not a room participant
- Handle race conditions if multiple users toggle same message simultaneously
- Consider what happens if message is deleted while toggle operation is in flight

### Testing Scenarios

1. **Happy Path:**
   - User toggles message to inactive
   - API call succeeds
   - Message visually indicates inactive status
   - Agent no longer sees this message in context

2. **Concurrent Updates:**
   - Two users toggle same message at same time
   - Last write wins (event sourcing guarantees ordering)
   - All clients eventually consistent via WebSocket events

3. **Permission Denial:**
   - User who is not a room participant attempts toggle
   - API returns 403 Forbidden
   - UI shows appropriate error message

4. **Network Failure:**
   - API call fails due to network issue
   - Optimistic update is rolled back (if used)
   - User sees error and can retry

---

## Feature 2: Delete Message

### Purpose

Permanently remove messages from the room (room owner only). This is useful for:
- Removing inappropriate content
- Correcting mistakes
- Moderating room content

### Backend Behavior

**Event Sourcing Pattern:**
- Messages are **never deleted** from the event log (`room_events` table)
- A new event is emitted: `message.deleted`
- The `room_messages` projection marks the message as deleted (sets `deleted_at` timestamp)
- Original message content is preserved in event log for audit/replay purposes
- Deleted messages are **filtered out** of all API responses

**Authorization:**
- **Only the room owner** (`created_by` user) can delete messages
- Other participants (including agents) **cannot** delete messages
- Attempting to delete without owner permission returns 403 Forbidden

**Important:** This is a **soft delete** from the user perspective but permanent from the API perspective. Deleted messages:
- ✅ Are preserved in event log (for event sourcing replay)
- ❌ Are NOT returned in `GET /rooms/{room_id}/messages`
- ❌ Are NOT included in agent context
- ❌ Cannot be "undeleted" via API (would require database intervention)

### API Endpoint

```typescript
DELETE /api/v1/rooms/{room_id}/messages/{message_id}
```

**Request Headers:**
```
Authorization: Bearer {jwt_token}
```

**Request Body:**
None

**Success Response (204 No Content):**
```
(Empty body)
```

**Error Responses:**

```json
// 403 Forbidden - Not the room owner
{
  "detail": "Only the room owner can delete messages"
}

// 403 Forbidden - Not a room participant
{
  "detail": "Access denied"
}

// 404 Not Found - Message doesn't exist or already deleted
{
  "detail": "Message not found"
}

// 404 Not Found - Room doesn't exist
{
  "detail": "Room not found"
}
```

### Expected Backend Events

When a message is deleted, the backend emits:

```json
{
  "type": "event",
  "sequence": 124,
  "event_type": "message.deleted",
  "payload": {
    "message_id": "uuid",
    "deleted_by": "user_uuid",
    "deleted_at": "2025-12-30T12:00:00Z"
  },
  "created_at": "2025-12-30T12:00:00Z"
}
```

**WebSocket Delivery:**
- If WebSocket connected, all room participants receive this event in real-time
- Frontend should **remove** the message from local state when receiving this event
- REST API polling clients will no longer see the message on next refresh

### Frontend Implementation Considerations

#### State Management

```typescript
// Messages are removed from state after deletion
// No need to store "deleted" flag since deleted messages
// are not returned by the API

// If you want to show "Message deleted" placeholder:
interface Message {
  message_id: string
  room_id: string
  content: string
  // ... other fields
  deleted_at?: string  // Optional: only if showing deletion placeholders
}
```

#### API Call Pattern

```typescript
// Example API call
async function deleteMessage(
  roomId: string,
  messageId: string
): Promise<void> {
  const response = await fetch(
    `/api/v1/rooms/${roomId}/messages/${messageId}`,
    {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
      },
    }
  )

  if (!response.ok) {
    if (response.status === 403) {
      throw new Error('Only the room owner can delete messages')
    }
    if (response.status === 404) {
      throw new Error('Message not found or already deleted')
    }
    throw new Error('Failed to delete message')
  }

  // 204 No Content - success
}
```

#### WebSocket Event Handling

```typescript
// Example WebSocket event handler
function handleWebSocketMessage(event: WebSocketMessage) {
  if (event.type === 'event' && event.event_type === 'message.deleted') {
    const { message_id } = event.payload

    // Remove message from local state
    removeMessageFromCache(message_id)

    // If using React Query or similar, invalidate cache
    queryClient.invalidateQueries(['rooms', roomId, 'messages'])
  }
}
```

#### Optimistic Deletion (Recommended)

```typescript
// Example optimistic deletion pattern
async function deleteMessageOptimistic(messageId: string) {
  // 1. Immediately remove from local state
  const deletedMessage = getMessageFromCache(messageId)
  removeMessageFromCache(messageId)

  try {
    // 2. Make API call
    await deleteMessage(roomId, messageId)

    // 3. Success - message is permanently removed
    // (WebSocket event will confirm or state is already correct)

  } catch (error) {
    // 4. Error - restore message to state
    addMessageToCache(deletedMessage)

    // Show error to user
    if (error.message.includes('owner')) {
      showError('Only the room owner can delete messages')
    } else {
      showError('Failed to delete message. Please try again.')
    }
  }
}
```

#### Confirmation Dialog (Recommended)

```typescript
// Example confirmation flow
async function handleDeleteClick(messageId: string) {
  // Show confirmation dialog
  const confirmed = await showConfirmationDialog({
    title: 'Delete Message',
    message: 'Are you sure you want to delete this message? This action cannot be undone.',
    confirmText: 'Delete',
    cancelText: 'Cancel',
    destructive: true,
  })

  if (!confirmed) {
    return
  }

  // Proceed with deletion
  await deleteMessageOptimistic(messageId)
}
```

#### UI/UX Considerations

**Permission Checks:**
- Only show delete button/option if current user is the room owner
- Get room owner from room metadata: `GET /api/v1/rooms/{room_id}`
- Compare `current_user.id` with `room.created_by`

```typescript
// Example permission check
function canDeleteMessages(currentUserId: string, room: Room): boolean {
  return currentUserId === room.created_by
}
```

**Visual Design:**
- Delete action should be clearly destructive (red color, trash icon)
- Consider placing in overflow menu or requiring hover/long-press to reveal
- Show confirmation dialog before deletion
- Provide clear feedback during and after deletion

**Edge Cases:**
- Disable delete UI if user is not room owner
- Handle case where message is deleted while user is viewing it
- Consider what happens if user tries to delete a message that no longer exists
- Handle streaming messages (agent responses in progress) - should not be deletable

### Testing Scenarios

1. **Happy Path (Room Owner):**
   - Room owner clicks delete on a message
   - Confirmation dialog appears
   - User confirms
   - Message is removed from UI
   - API call succeeds
   - Other participants see message disappear via WebSocket

2. **Permission Denial (Non-Owner):**
   - Non-owner user attempts to delete message
   - API returns 403 Forbidden
   - UI shows error: "Only the room owner can delete messages"
   - Message remains visible

3. **Concurrent Deletion:**
   - Two users attempt to delete same message
   - First deletion succeeds
   - Second deletion receives 404 (message already deleted)
   - Both clients show message removed

4. **Network Failure:**
   - API call fails due to network issue
   - Optimistic deletion is rolled back
   - Message reappears in UI
   - User sees error and can retry

5. **Already Deleted:**
   - User attempts to delete message that was just deleted by another user
   - API returns 404
   - UI gracefully handles (message already removed or shows "already deleted")

---

## Integration Patterns

### Combined State Management Example

```typescript
interface Message {
  message_id: string
  room_id: string
  content: string
  sender_id: string | null
  agent_name: string | null
  sender_type: 'user' | 'agent'
  active_for_context: boolean  // For feature 1
  created_at: string
  // deleted_at not needed - deleted messages are filtered out by API
}

interface Room {
  room_id: string
  title: string
  created_by: string  // User UUID of room owner
  // ... other fields
}

// Permission helpers
function canToggleMessageContext(
  currentUserId: string,
  room: Room
): boolean {
  // Any active participant can toggle
  return true  // Check actual participation status from room data
}

function canDeleteMessage(
  currentUserId: string,
  room: Room
): boolean {
  // Only room owner can delete
  return currentUserId === room.created_by
}
```

### WebSocket Event Handler Example

```typescript
function handleRoomEvent(event: WebSocketMessage) {
  if (event.type !== 'event') return

  switch (event.event_type) {
    case 'message.context_toggled':
      // Update message active_for_context status
      updateMessageInCache(event.payload.message_id, {
        active_for_context: event.payload.active_for_context
      })
      break

    case 'message.deleted':
      // Remove message from cache
      removeMessageFromCache(event.payload.message_id)
      break

    case 'room_message.user':
    case 'room_message.agent':
      // New message added - refresh message list
      queryClient.invalidateQueries(['rooms', roomId, 'messages'])
      break
  }
}
```

### Error Handling Pattern

```typescript
class MessageManagementError extends Error {
  constructor(
    message: string,
    public code: 'FORBIDDEN' | 'NOT_FOUND' | 'NETWORK_ERROR'
  ) {
    super(message)
  }
}

async function handleMessageOperation<T>(
  operation: () => Promise<T>
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (error instanceof Response) {
      if (error.status === 403) {
        throw new MessageManagementError(
          'You do not have permission to perform this action',
          'FORBIDDEN'
        )
      }
      if (error.status === 404) {
        throw new MessageManagementError(
          'Message not found',
          'NOT_FOUND'
        )
      }
    }
    throw new MessageManagementError(
      'An unexpected error occurred',
      'NETWORK_ERROR'
    )
  }
}

// Usage
try {
  await handleMessageOperation(() =>
    deleteMessage(roomId, messageId)
  )
  showSuccess('Message deleted')
} catch (error) {
  if (error instanceof MessageManagementError) {
    showError(error.message)
  }
}
```

---

## API Reference Summary

### Get Room Details (for permission checks)

```typescript
GET /api/v1/rooms/{room_id}

Response (200 OK):
{
  "room_id": "uuid",
  "title": "Room Title",
  "created_by": "user_uuid",  // ← Room owner
  "created_at": "2025-12-30T12:00:00Z",
  "last_activity": "2025-12-30T12:00:00Z",
  "story_id": "uuid" | null
}
```

### Get Messages (for current state)

```typescript
GET /api/v1/rooms/{room_id}/messages?skip=0&limit=100

Response (200 OK):
{
  "data": [
    {
      "message_id": "uuid",
      "room_id": "uuid",
      "content": "Message content",
      "sender_id": "uuid" | null,
      "agent_name": "AgentName" | null,
      "sender_type": "user" | "agent",
      "active_for_context": true,  // ← For feature 1
      "created_at": "2025-12-30T12:00:00Z"
    }
  ],
  "count": 100
}

Note: Deleted messages are NOT included in this response
```

### Toggle Message Context

```typescript
PATCH /api/v1/rooms/{room_id}/messages/{message_id}/context

Request Body:
{
  "active_for_context": false
}

Response (200 OK):
{
  "message_id": "uuid",
  "room_id": "uuid",
  "active_for_context": false,
  "updated_at": "2025-12-30T12:00:00Z"
}
```

### Delete Message

```typescript
DELETE /api/v1/rooms/{room_id}/messages/{message_id}

Response (204 No Content):
(Empty body)
```

---

## Event Sourcing Implications

### What Frontend Developers Should Know

**Event Log Immutability:**
- All operations (toggle context, delete) create new events
- Original messages are never modified in the event log
- This enables audit trails and event replay

**Eventual Consistency:**
- WebSocket clients receive events in real-time
- REST API clients are eventually consistent (next poll)
- Race conditions are resolved by event sequence ordering

**Projection Updates:**
- Backend updates `room_messages` projection table
- API queries return current projected state
- Deleted messages are filtered out automatically

**Implications for Frontend:**
- Trust the API as source of truth
- WebSocket events keep state synchronized
- Optimistic updates should be rolled back on error
- Don't cache deleted messages - they won't come back

---

## Testing Checklist

### Feature 1: Toggle Message Context

- [ ] Can toggle message to inactive for context
- [ ] Can toggle message back to active for context
- [ ] Visual indicator shows inactive status
- [ ] Non-participants cannot toggle (403 error)
- [ ] WebSocket event updates all connected clients
- [ ] Optimistic update works correctly
- [ ] Error handling shows appropriate messages
- [ ] Works with REST fallback (no WebSocket)

### Feature 2: Delete Message

- [ ] Room owner can delete messages
- [ ] Non-owners cannot delete (403 error)
- [ ] Confirmation dialog prevents accidental deletion
- [ ] Message disappears after deletion
- [ ] WebSocket event removes message for all clients
- [ ] Optimistic deletion works correctly
- [ ] Already-deleted message shows 404 gracefully
- [ ] Delete button only visible to room owner
- [ ] Works with REST fallback (no WebSocket)

### Integration Tests

- [ ] Toggle then delete same message works
- [ ] Delete button hidden if not room owner
- [ ] Concurrent operations handled correctly
- [ ] Network errors handled gracefully
- [ ] Page refresh shows correct state

---

## Common Pitfalls

### ❌ Don't Do This

1. **Don't modify message objects in place** - Create new objects to trigger reactive updates
2. **Don't cache deleted messages** - They won't reappear, remove from cache completely
3. **Don't skip permission checks** - Always verify room owner status before showing delete UI
4. **Don't skip confirmation dialogs** - Deletion is permanent (from user perspective)
5. **Don't ignore WebSocket events** - They keep all clients synchronized

### ✅ Do This Instead

1. **Create new message objects** when updating state
2. **Remove deleted messages** completely from cache
3. **Check `room.created_by === current_user.id`** before showing delete options
4. **Always confirm** destructive actions with user
5. **Listen to WebSocket events** and update local state accordingly

---

## Support & Questions

**Backend API Documentation:** `http://localhost:8000/docs` (OpenAPI/Swagger)

**Related Documentation:**
- WebSocket Streaming: `frontend/docs/WebSocket-Integration.md` (if exists)
- Authentication: `frontend/docs/Authentication.md` (if exists)
- State Management: Your team's state management documentation

**Questions or Issues:**
- Check API documentation at `/docs` endpoint
- Test API calls directly using Swagger UI
- Verify authorization by checking JWT token and room permissions
- Check backend logs for detailed error messages

---

**Last Updated:** 2025-12-30
**API Version:** v1
**Phase:** Post-Phase 4 (WebSocket streaming available)
