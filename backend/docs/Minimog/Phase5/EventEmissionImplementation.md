# Phase 5: Message Management Event Emission Implementation

## Overview

This document specifies the event emission logic for message management features following the existing event-sourcing architecture in `app/services/event_emitter.py`.

## Architecture Pattern

**Critical**: All writes go through `emit_event()` which is the single write-path for room state changes.

```
Route Handler → CRUD Function → emit_event() → _update_projections() → _handle_*()
                                      ↓
                                 Redis Publish
```

**CRUD functions**: Only call `emit_event()` with appropriate payload
**Event handlers**: Private `_handle_*()` functions in `event_emitter.py` update projections
**Redis**: Automatically published by `emit_event()` via `_publish_to_redis()`
**Transactions**: Managed by route handlers using `AsyncSessionTransactionDep`

---

## New Event Types

Three new event types will be added to support message management:

```python
"message.edited"    # Message content updated
"message.pinned"    # Message pinned by owner
"message.unpinned"  # Message unpinned by owner
```

**Note**: Context toggling and message deletion events already exist or are trivial additions.

---

## CRUD Function Implementations

### Location: `backend/app/crud.py`

Add these functions to the Message Operations section (after `send_user_message`):

```python
# ============================================================================
# Message Management Operations (Phase 5)
# ============================================================================


async def edit_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    new_content: str,
    session: AsyncSession,
) -> RoomMessage:
    """
    Edit a message's content.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller:
    - User messages: Author OR room owner can edit
    - Agent messages: Owner only can edit

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to edit
        user_id: UUID of the user performing the edit
        new_content: New message content
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.edited event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.edited",
        payload={
            "message_id": str(message_id),
            "new_content": new_content,
            "edited_by": str(user_id),
        },
    )

    # Fetch and return updated message
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.scalar_one()


async def pin_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> RoomMessage:
    """
    Pin a message and auto-mark it as active for context.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to pin
        user_id: UUID of the user performing the pin
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.pinned event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.pinned",
        payload={
            "message_id": str(message_id),
            "pinned_by": str(user_id),
        },
    )

    # Fetch and return updated message
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.scalar_one()


async def unpin_message(
    *,
    room_id: UUID,
    message_id: UUID,
    session: AsyncSession,
) -> RoomMessage:
    """
    Unpin a message. Does NOT change active_for_context status.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to unpin
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.unpinned event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.unpinned",
        payload={
            "message_id": str(message_id),
        },
    )

    # Fetch and return updated message
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.scalar_one()


async def toggle_message_context(
    *,
    room_id: UUID,
    message_id: UUID,
    active_for_context: bool,
    session: AsyncSession,
) -> RoomMessage:
    """
    Toggle message active_for_context status.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (any active participant).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message
        active_for_context: New active_for_context value
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.context_toggled event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.context_toggled",
        payload={
            "message_id": str(message_id),
            "active_for_context": active_for_context,
        },
    )

    # Fetch and return updated message
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.scalar_one()


async def delete_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Delete a message (soft delete via event).

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to delete
        user_id: UUID of the user performing the deletion
        session: Async database session with active transaction

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.execute(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.scalar_one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.deleted event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.deleted",
        payload={
            "message_id": str(message_id),
            "deleted_by": str(user_id),
        },
    )
```

---

## Event Handler Implementations

### Location: `backend/app/services/event_emitter.py`

### Step 1: Update handlers dictionary in `_update_projections()`

Around line 306, add the new event types:

```python
async def _update_projections(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """Update projection tables based on event type."""
    handlers = {
        "room.created": _handle_room_created,
        "room.updated": _handle_room_updated,
        "participant.joined": _handle_participant_joined,
        "participant.left": _handle_participant_left,
        "participant.role_changed": _handle_participant_role_changed,
        "room_message.user": _handle_room_message_user,
        "room_message.agent": _handle_room_message_agent,
        # Phase 5: Message Management
        "message.edited": _handle_message_edited,
        "message.pinned": _handle_message_pinned,
        "message.unpinned": _handle_message_unpinned,
        "message.context_toggled": _handle_message_context_toggled,
        "message.deleted": _handle_message_deleted,
    }

    handler = handlers.get(event.event_type)
    if handler is None:
        raise ValueError(f"Unsupported event type: {event.event_type}")

    await handler(session, event)

    # Update room.last_activity for all event types
    await _update_room_last_activity(session, event.room_id, event.created_at)
```

### Step 2: Add handler functions

Add these after the existing message handlers (after line 554):

```python
# ============================================================================
# Message Management Event Handlers (Phase 5)
# ============================================================================


async def _handle_message_edited(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle message.edited event.

    Updates message content and editing metadata.
    Does NOT change active_for_context status.

    Payload:
        - message_id: UUID string (required)
        - new_content: str (required)
        - edited_by: UUID string (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomMessage).where(
            RoomMessage.message_id == uuid.UUID(payload["message_id"])
        )
    )
    message = result.scalar_one()

    message.content = payload["new_content"]
    message.edited_at = event.created_at
    message.edited_by = uuid.UUID(payload["edited_by"])

    session.add(message)


async def _handle_message_pinned(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle message.pinned event.

    Pins message and auto-marks it as active for context.

    Payload:
        - message_id: UUID string (required)
        - pinned_by: UUID string (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomMessage).where(
            RoomMessage.message_id == uuid.UUID(payload["message_id"])
        )
    )
    message = result.scalar_one()

    message.is_pinned = True
    message.pinned_at = event.created_at
    message.pinned_by = uuid.UUID(payload["pinned_by"])
    message.active_for_context = True  # Auto-mark active

    session.add(message)


async def _handle_message_unpinned(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle message.unpinned event.

    Unpins message. Does NOT change active_for_context status.

    Payload:
        - message_id: UUID string (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomMessage).where(
            RoomMessage.message_id == uuid.UUID(payload["message_id"])
        )
    )
    message = result.scalar_one()

    message.is_pinned = False
    message.pinned_at = None
    message.pinned_by = None

    session.add(message)


async def _handle_message_context_toggled(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle message.context_toggled event.

    Updates active_for_context status.

    Payload:
        - message_id: UUID string (required)
        - active_for_context: bool (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomMessage).where(
            RoomMessage.message_id == uuid.UUID(payload["message_id"])
        )
    )
    message = result.scalar_one()

    message.active_for_context = payload["active_for_context"]

    session.add(message)


async def _handle_message_deleted(
    session: AsyncSession,
    event: RoomEvent,
) -> None:
    """
    Handle message.deleted event.

    Soft-deletes message by removing from projection.
    Historical event is preserved in room_events table.

    Payload:
        - message_id: UUID string (required)
        - deleted_by: UUID string (required)
    """
    payload = event.payload

    result = await session.execute(
        select(RoomMessage).where(
            RoomMessage.message_id == uuid.UUID(payload["message_id"])
        )
    )
    message = result.scalar_one_or_none()

    if message:
        await session.delete(message)
```

---

## Implementation Checklist

### Backend (Event System)

- [ ] Add CRUD functions to `app/crud.py`:
  - [ ] `edit_message()`
  - [ ] `pin_message()`
  - [ ] `unpin_message()`
  - [ ] `toggle_message_context()`
  - [ ] `delete_message()`

- [ ] Update `app/services/event_emitter.py`:
  - [ ] Add event types to handlers dictionary in `_update_projections()`
  - [ ] Add `_handle_message_edited()`
  - [ ] Add `_handle_message_pinned()`
  - [ ] Add `_handle_message_unpinned()`
  - [ ] Add `_handle_message_context_toggled()`
  - [ ] Add `_handle_message_deleted()`

- [ ] Test event emission:
  - [ ] Verify events are persisted with correct payload
  - [ ] Verify projections are updated correctly
  - [ ] Verify Redis publishing works
  - [ ] Test event replay rebuilds projections correctly

---

## Notes

1. **Transaction Management**: All CRUD functions expect active transactions (managed by route handlers)

2. **Redis Publishing**: Automatic via `emit_event()` - no manual publishing needed

3. **Authorization**: CRUD functions document auth requirements but don't enforce them - route handlers must check using authorization helpers from `crud.py`

4. **Event Replay**: All handlers must be idempotent and produce same result when replayed

5. **Soft Delete**: `message.deleted` removes from projection but preserves event history

6. **Auto-activation**: Pinning a message automatically marks it `active_for_context=True`

---

## WebSocket Message Format

Events published to Redis follow the AG-UI compatible format (already handled by `_publish_to_redis()`):

```json
{
  "type": "event",
  "sequence": 123,
  "event_type": "message.pinned",
  "payload": {
    "message_id": "uuid-string",
    "pinned_by": "user-uuid-string"
  },
  "created_at": "2025-01-01T12:00:00.000Z"
}
```

Clients receive these messages via WebSocket and update UI accordingly.
