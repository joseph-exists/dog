# Event Types Reference

## Table of Contents
1. [Event Structure](#event-structure)
2. [Room Events](#room-events)
3. [Participant Events](#participant-events)
4. [Message Events](#message-events)
5. [Internal Agent Messages (A2A)](#room_messageagent_internal)
6. [Message Management Events](#message-management-events)
7. [Ephemeral Messages](#ephemeral-messages)

---

## Event Structure

### RoomEvent (Persisted)

```python
RoomEvent(
    event_id: UUID,           # Unique event identifier
    room_id: UUID,            # Room this event belongs to
    room_sequence: int,       # Monotonic sequence per room (1, 2, 3...)
    event_type: str,          # Event type identifier
    payload: dict,            # Event-specific data
    enrichment_metadata: dict | None,  # Optional trace_id, latency_ms, model, etc.
    created_at: datetime,     # Event timestamp
)
```

### Redis Message Format

```json
{
    "type": "event",
    "sequence": 42,
    "event_type": "room_message.user",
    "payload": {...},
    "created_at": "2024-01-15T10:30:00Z"
}
```

---

## Room Events

### room.created

Creates a new room.

**Payload:**
```python
{
    "creator_id": str,      # UUID of creating user (required)
    "title": str | None,    # Room title (optional)
    "story_id": str | None  # Associated story UUID (optional)
}
```

**Projection:** Creates new `Room` record.

**Example:**
```python
await emit_event(
    session, room_id, "room.created",
    {
        "creator_id": str(user.id),
        "title": "Strategy Discussion",
        "story_id": str(story.id),
    }
)
```

---

### room.updated

Updates room metadata.

**Payload:**
```python
{
    "updated_fields": {
        "title": str,       # New title (optional)
        # Other Room fields...
    }
}
```

**Projection:** Updates `Room` record with specified fields.

**Example:**
```python
await emit_event(
    session, room_id, "room.updated",
    {"updated_fields": {"title": "New Room Title"}}
)
```

---

## Participant Events

### participant.joined

User or agent joins a room. Handles both initial join and re-join.

**Payload:**
```python
{
    "participant_id": str,        # UUID string (users) or agent name (agents)
    "participant_type": str,      # "user" | "agent" (required)
    "role": str                   # "owner" | "member" (required)
}
```

**Projection:**
- New participant: Creates `RoomParticipant` record
- Re-join: Reactivates existing record (sets `active=True`, clears `left_at`)

**Example:**
```python
# User joining
await emit_event(
    session, room_id, "participant.joined",
    {
        "participant_id": str(user.id),
        "participant_type": "user",
        "role": "member",
    }
)

# Agent joining
await emit_event(
    session, room_id, "participant.joined",
    {
        "participant_id": "assistant-v1",
        "participant_type": "agent",
        "role": "member",
    }
)
```

---

### participant.left

User or agent leaves a room (soft delete).

**Payload:**
```python
{
    "participant_id": str  # UUID string (users) or agent name (agents)
}
```

**Projection:** Sets `active=False` and `left_at=event.created_at` on `RoomParticipant`.

**Example:**
```python
await emit_event(
    session, room_id, "participant.left",
    {"participant_id": str(user.id)}
)
```

---

### participant.role_changed

Changes participant's role in the room.

**Payload:**
```python
{
    "participant_id": str,  # UUID string (users) or agent name (agents)
    "new_role": str         # "owner" | "member" (required)
}
```

**Projection:** Updates `role` field on `RoomParticipant`.

**Example:**
```python
await emit_event(
    session, room_id, "participant.role_changed",
    {
        "participant_id": str(user.id),
        "new_role": "owner",
    }
)
```

---

## Message Events

### room_message.user

User sends a message.

**Payload:**
```python
{
    "sender_id": str,  # UUID string of sending user (required)
    "content": str     # Message content (required)
}
```

**Projection:** Creates `RoomMessage` with `sender_type="user"`.

**Example:**
```python
await emit_event(
    session, room_id, "room_message.user",
    {
        "sender_id": str(current_user.id),
        "content": "Hello, world!",
    }
)
```

---

### room_message.agent

Agent sends a message, optionally with structured UI components (AG-UI).

**Payload:**
```python
{
    "agent_name": str,                    # Agent identifier (required)
    "content": str,                       # Message content (required)
    "ui_components": list[dict] | None    # AG-UI components (optional)
}
```

**Projection:** Creates `RoomMessage` with `sender_type="agent"`.

**AG-UI Component Structure:**
```python
{
    "type": str,              # Component type (card, list, table, etc.)
    "data": dict,             # Component-specific data
    "id": str | None,         # Optional unique ID
    "fallback_text": str | None  # Fallback if component not supported
}
```

**Available Component Types:**
- `card` - Highlighted information card
- `list` - Bulleted or numbered list
- `table` - Data table with columns
- `progress` - Progress bars/metrics
- `action_buttons` - Clickable actions
- `code` - Code blocks with highlighting
- `quote` - Blockquotes/dialogue
- `alert` - Info/warning/error notices
- `collapsible` - Expandable sections
- `tabs` - Tabbed content
- `divider` - Visual separator

**Example (basic):**
```python
await emit_event(
    session, room_id, "room_message.agent",
    {
        "agent_name": "assistant-v1",
        "content": "I can help with that!",
    },
    enrichment_metadata={
        "model": "claude-3-opus",
        "latency_ms": 1234,
    }
)
```

**Example (with AG-UI):**
```python
await emit_event(
    session, room_id, "room_message.agent",
    {
        "agent_name": "StoryAdvisor",
        "content": "Here's your character analysis:",
        "ui_components": [
            {
                "type": "card",
                "data": {
                    "title": "Character: Elena",
                    "subtitle": "Protagonist",
                    "body": "A determined scientist...",
                    "variant": "highlight",
                },
            },
            {
                "type": "action_buttons",
                "data": {
                    "buttons": [
                        {"label": "Expand", "action": "expand_character"},
                        {"label": "Generate Dialogue", "action": "gen_dialogue"},
                    ],
                },
            },
        ],
    }
)
```

**Frontend Handling:**
```typescript
// Render text content
<MessageContent content={message.content} />

// Render UI components if present
{message.ui_components?.map((component) => (
  <AgentUIRenderer key={component.id} component={component} />
))}
```

---

### room_message.agent_internal

Agent-to-agent internal message (A2A communication).

Internal messages are persisted for audit/debugging but marked for frontend filtering.
Users typically don't see these unless explicitly enabled.

**Payload:**
```python
{
    "from_agent": str,           # Sending agent slug (required)
    "to_agent": str | None,      # Target agent slug (optional, None = broadcast)
    "content": str,              # Message content (required)
    "visible_to_users": bool     # Frontend hint (optional, default False)
}
```

**Projection:** Creates `RoomMessage` with `sender_type="agent_internal"`.

**Example:**
```python
await emit_event(
    session, room_id, "room_message.agent_internal",
    {
        "from_agent": "StoryAdvisor",
        "to_agent": "DialogueCoach",
        "content": "Please review the dialogue in scene 3",
        "visible_to_users": False,
    }
)

# Or use the convenience helper:
from app.services.event_emitter import emit_agent_internal_message

await emit_agent_internal_message(
    session, room_id,
    from_agent="StoryAdvisor",
    to_agent="DialogueCoach",
    content="Please review the dialogue in scene 3",
)
```

**Frontend Filtering:**
```typescript
// Filter out internal messages for normal users
const visibleMessages = messages.filter(m => m.sender_type !== "agent_internal")
```

---

## Message Management Events

### message.edited

Edits message content.

**Payload:**
```python
{
    "message_id": str,   # UUID string of message (required)
    "new_content": str,  # Updated content (required)
    "edited_by": str     # UUID string of editor (required)
}
```

**Projection:** Updates `content`, `edited_at`, `edited_by` on `RoomMessage`.

**Note:** Does NOT change `active_for_context` status.

**Example:**
```python
await emit_event(
    session, room_id, "message.edited",
    {
        "message_id": str(message.message_id),
        "new_content": "Updated message content",
        "edited_by": str(current_user.id),
    }
)
```

---

### message.pinned

Pins a message. Auto-marks as active for context.

**Payload:**
```python
{
    "message_id": str,  # UUID string of message (required)
    "pinned_by": str    # UUID string of user pinning (required)
}
```

**Projection:** Sets `is_pinned=True`, `pinned_at`, `pinned_by`, `active_for_context=True`.

**Example:**
```python
await emit_event(
    session, room_id, "message.pinned",
    {
        "message_id": str(message.message_id),
        "pinned_by": str(current_user.id),
    }
)
```

---

### message.unpinned

Unpins a message.

**Payload:**
```python
{
    "message_id": str  # UUID string of message (required)
}
```

**Projection:** Sets `is_pinned=False`, clears `pinned_at` and `pinned_by`.

**Note:** Does NOT change `active_for_context` status.

**Example:**
```python
await emit_event(
    session, room_id, "message.unpinned",
    {"message_id": str(message.message_id)}
)
```

---

### message.context_toggled

Toggles whether message is active for agent context.

**Payload:**
```python
{
    "message_id": str,        # UUID string of message (required)
    "active_for_context": bool  # New status (required)
}
```

**Projection:** Updates `active_for_context` on `RoomMessage`.

**Example:**
```python
await emit_event(
    session, room_id, "message.context_toggled",
    {
        "message_id": str(message.message_id),
        "active_for_context": True,
    }
)
```

---

### message.deleted

Soft-deletes a message from projection (event preserved).

**Payload:**
```python
{
    "message_id": str,  # UUID string of message (required)
    "deleted_by": str   # UUID string of deleter (required)
}
```

**Projection:** Deletes `RoomMessage` from projection table.

**Note:** Historical event is preserved in `room_events` table.

**Example:**
```python
await emit_event(
    session, room_id, "message.deleted",
    {
        "message_id": str(message.message_id),
        "deleted_by": str(current_user.id),
    }
)
```

---

## Ephemeral Messages

### message.delta (Token Streaming)

Published via `publish_agent_token()`. NOT persisted.

**Redis Message Format:**
```json
{
    "type": "message.delta",
    "agent_name": "assistant-v1",
    "content": "tok"
}
```

**Usage:**
```python
await publish_agent_token(
    room_id=room_id,
    agent_name="assistant-v1",
    token="Hello",  # Single token
)
```

**Note:** Final complete message is persisted via `room_message.agent` event.

---

## Enrichment Metadata

Optional metadata for observability:

```python
enrichment_metadata = {
    "trace_id": "abc-123",     # Request correlation ID
    "latency_ms": 1234,        # Processing time
    "model": "claude-3-opus",  # LLM model used
    # Custom fields as needed
}
```

Pass to `emit_event()`:
```python
await emit_event(
    session, room_id, event_type, payload,
    enrichment_metadata={"trace_id": request.state.trace_id}
)
```
