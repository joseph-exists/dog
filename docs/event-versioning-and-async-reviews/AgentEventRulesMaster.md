
## Agent and Event Sourcing Patterns for TinyFoot
### Multi-User Room Architecture

**Status:** In review
**Last Review:** December 18, 2025  
**Architecture:** Multi-user collaborative rooms with event sourcing

---

## Agent Development Patterns

### Agent Structure

All agents should follow this structure in the `app/agents/` directory:

```python
# app/agents/example_agent.py
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from uuid import UUID

# 1. Define room-aware context type with all dependencies
class RoomContext(BaseModel):
    room_id: UUID
    user_id: UUID
    # Room metadata for multi-user awareness
    participants: list[dict]  # [{participant_id, participant_type, role}, ...]
    room_metadata: dict  # {created_at, story_id, last_activity, etc}
    # Add any other context needed by tools
    story_id: UUID | None = None

# 2. Create agent with explicit context type
example_agent = Agent(
    'openai:gpt-4',  # or 'openai:gpt-3.5-turbo' for simpler tasks
    system_prompt="""You are an example agent collaborating with multiple users in a room.
    You can see all participants and should provide context-aware assistance.
    Be specific about the agent's role and capabilities.""",
    deps_type=RoomContext
)

# 3. Define tools that use room-aware context
@example_agent.tool
async def example_tool(ctx: RunContext[RoomContext], param: str) -> str:
    """Tool description for the LLM to understand when to use this.

    Args:
        ctx: Runtime context with room, participants, and user info
        param: Parameter description

    Returns:
        Result description
    """
    # Access room context via ctx.deps
    room_id = ctx.deps.room_id
    participants = ctx.deps.participants
    story_id = ctx.deps.room_metadata.get('story_id')

    # Perform tool logic with room awareness
    result = await do_something(param, room_id, participants)

    return result
```

### Agent Tool Best Practices

**DO:**
- Keep tools focused on single responsibilities
- Use async/await for all I/O operations
- Provide clear docstrings (LLM reads these)
- Return JSON-serializable types (str, dict, list)
- Access database via session dependency
- Log tool execution for debugging
- Consider multi-user context (participants see all agent actions)
- Access participant information from ctx.deps.participants

**DON'T:**
- Don't make tools do multiple unrelated things
- Don't use blocking operations (time.sleep, requests.get)
- Don't access request-scoped state from tools
- Don't raise exceptions without returning error messages
- Don't return large payloads (>10KB) - summarize instead
- Don't assume single-user context (rooms have multiple participants)
- Don't bypass room membership validation

### Agent Registration

## TODO : RETHINK THIS PATTERN. 

All production agents must be registered in `app/agents/registry.py`:

```python
# app/agents/registry.py
from app.agents.story_advisor import story_advisor
from app.agents.character_expert import character_expert

AGENT_REGISTRY = {
    "story_advisor": {
        "agent": story_advisor,
        "display_name": "Story Advisor",
        "description": "Helps authors with plot development and pacing",
        "context_type": "RoomContext",
        "participant_type": "agent",  # Agents are room participants
        "available_for": ["story_editing"],  # Where agent can be used
    },
    "character_expert": {
        "agent": character_expert,
        "display_name": "Character Expert",
        "description": "Specializes in character development and arcs",
        "context_type": "RoomContext",
        "participant_type": "agent",
        "available_for": ["story_editing"],
    },
}

def get_agent_metadata(agent_name: str) -> dict:
    """Get agent metadata for display purposes"""
    if agent_name not in AGENT_REGISTRY:
        return None

    info = AGENT_REGISTRY[agent_name]
    return {
        "name": agent_name,
        "display_name": info["display_name"],
        "description": info["description"],
        "participant_type": info["participant_type"]
    }
```

### Agent Routes Pattern

Agent execution happens through room message endpoints in `app/api/routes/rooms.py`.
Agents are invoked when messages are sent to rooms where they are participants.

```python
# app/api/routes/rooms.py
from fastapi import APIRouter, HTTPException
from app.services.agent_runner import AgentRunner
from app.crud import check_room_membership

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post('/{room_id}/messages')
async def send_message(
    room_id: UUID,
    message: MessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> MessagePublic:
    """Send a message to room and trigger agent responses"""

    # Validate room membership
    if not await check_room_membership(room_id, current_user.id, session):
        raise HTTPException(403, "Not a room participant")

    # Emit user message event
    with session.begin():
        await emit_event(
            room_id=room_id,
            event_type="message.user",
            payload={
                "sender_id": str(current_user.id),
                "content": message.content
            },
            session=session
        )

    # Run agent participants (if any)
    await AgentRunner().run_room_agents(
        room_id=room_id,
        user_message=message.content,
        user_id=current_user.id,
        session=session
    )

    return MessagePublic(
        sender_type="user",
        content=message.content,
        created_at=datetime.now()
    )

# Optional: Standalone agent execution endpoint for AG-UI integration
@router.post('/agents/{agent_name}')
async def run_agent_standalone(
    agent_name: str,
    request: Request
) -> Response:
    """Execute a registered agent via AG-UI protocol"""
    from pydantic_ai.ui.ag_ui import AGUIAdapter

    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(404, f"Agent '{agent_name}' not found")

    agent = AGENT_REGISTRY[agent_name]["agent"]
    return await AGUIAdapter.dispatch_request(request, agent=agent)

@router.get('/agents')
async def list_agents() -> dict:
    """Get list of available agents with their metadata"""
    return {
        "agents": [
            {
                "name": name,
                "display_name": info["display_name"],
                "description": info["description"],
                "participant_type": info["participant_type"]
            }
            for name, info in AGENT_REGISTRY.items()
        ]
    }
```

### Testing Agents

Agent tests should be in `app/tests/agents/`:

```python
# app/tests/agents/test_story_advisor.py
import pytest
from app.agents.story_advisor import story_advisor, RoomContext
from uuid import uuid4

@pytest.mark.asyncio
async def test_story_advisor_basic_response():
    """Test agent can respond to basic query in room context"""
    ctx = RoomContext(
        room_id=uuid4(),
        user_id=uuid4(),
        participants=[
            {"participant_id": str(uuid4()), "participant_type": "user", "role": "owner"},
            {"participant_id": "story_advisor", "participant_type": "agent", "role": "member"}
        ],
        room_metadata={
            "created_at": "2025-12-12T10:00:00Z",
            "story_id": None
        },
        story_id=None
    )

    result = await story_advisor.run(
        "How do I create tension?",
        deps=ctx
    )

    assert result.data is not None
    assert len(result.data) > 50  # Reasonable response length

@pytest.mark.asyncio
async def test_agent_tool_execution():
    """Test agent can use tools with room context"""
    story_id = uuid4()
    ctx = RoomContext(
        room_id=uuid4(),
        user_id=uuid4(),
        participants=[
            {"participant_id": str(uuid4()), "participant_type": "user", "role": "owner"},
            {"participant_id": "story_advisor", "participant_type": "agent", "role": "member"}
        ],
        room_metadata={
            "created_at": "2025-12-12T10:00:00Z",
            "story_id": str(story_id)
        },
        story_id=story_id  # Provide story context
    )

    result = await story_advisor.run(
        "Analyze my story's pacing",
        deps=ctx
    )

    # Agent should have called the analyze_pacing tool
    assert any(
        call.tool_name == "analyze_pacing" 
        for call in result.all_messages() 
        if hasattr(call, 'tool_name')
    )

@pytest.mark.asyncio
async def test_agent_multi_user_awareness():
    """Test agent is aware of multiple participants"""
    ctx = RoomContext(
        room_id=uuid4(),
        user_id=uuid4(),
        participants=[
            {"participant_id": str(uuid4()), "participant_type": "user", "role": "owner"},
            {"participant_id": str(uuid4()), "participant_type": "user", "role": "member"},
            {"participant_id": "story_advisor", "participant_type": "agent", "role": "member"}
        ],
        room_metadata={"created_at": "2025-12-12T10:00:00Z"},
        story_id=None
    )

    result = await story_advisor.run(
        "Who else is in this room?",
        deps=ctx
    )

    # Agent should acknowledge multiple participants
    assert result.data is not None
```

---

## Event Sourcing Patterns

### Event Structure

All events follow this structure in the `room_events` table:

```sql
-- Event log is append-only (room-scoped)
CREATE TABLE room_events (
    event_id BIGSERIAL PRIMARY KEY,
    room_id UUID NOT NULL,
    room_sequence BIGINT NOT NULL,  -- Per-room monotonic sequence
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (room_id, room_sequence)
);

CREATE INDEX idx_room_events_room_seq ON room_events (room_id, room_sequence);
CREATE INDEX idx_room_events_type ON room_events (event_type, created_at);
```

### Event Types

Standard event types for multi-user room system:

| Event Type | When Emitted | Payload Schema | Visibility |
|------------|--------------|----------------|------------|
| `room.created` | New room created | `{creator_id, story_id?, title?}` | All future participants |
| `room.updated` | Room metadata changed | `{updated_fields}` | All participants |
| `participant.joined` | User or agent joins room | `{participant_id, participant_type, role}` | All participants |
| `participant.left` | User or agent leaves room | `{participant_id, participant_type}` | All participants |
| `participant.role_changed` | Participant role updated | `{participant_id, old_role, new_role}` | All participants |
| `message.user` | User sends message | `{sender_id, content}` | All participants |
| `message.agent` | Agent completes response | `{agent_name, content, model}` | All participants |
| `agent.handoff` | Agent transfers conversation | `{from_agent, to_agent, reason}` | All participants |
| `tool.start` | Tool execution begins | `{tool_name, input, agent_name}` | All participants (observability) |
| `tool.end` | Tool execution completes | `{tool_name, output, duration_ms, agent_name}` | All participants (observability) |

**Key Principle:** All events are visible to all room participants for transparency in multi-user collaboration.

### Emitting Events

Use the centralized event emitter in `app/services/event_emitter.py`:

```python
# app/services/event_emitter.py
from uuid import UUID
import json
from sqlmodel import Session
from sqlalchemy import text

async def emit_event(
    room_id: UUID,
    event_type: str,
    payload: dict,
    session: Session
) -> int:
    """
    Emit an event to the room event log.

    Args:
        room_id: Room ID (multi-user room)
        event_type: Type of event (e.g., 'message.user', 'participant.joined')
        payload: Event-specific data (JSON-serializable dict)
        session: Database session (for transaction)

    Returns:
        room_sequence: The sequence number for this event in the room

    Raises:
        ValueError: If payload is not JSON-serializable
        IntegrityError: If sequence collision occurs (retry)
    """
    # Generate next sequence number for this room
    result = session.exec(
        text("""
            SELECT COALESCE(MAX(room_sequence), 0) + 1 
            FROM room_events 
            WHERE room_id = :room_id
        """),
        {"room_id": room_id}
    ).first()

    room_sequence = result[0] if result else 1

    # Insert event
    session.exec(
        text("""
            INSERT INTO room_events 
            (room_id, room_sequence, event_type, payload)
            VALUES (:room_id, :sequence, :type, :payload)
        """),
        {
            "room_id": room_id,
            "sequence": room_sequence,
            "type": event_type,
            "payload": json.dumps(payload)
        }
    )

    # Update projections in same transaction
    await update_projection(room_id, event_type, payload, session)

    return room_sequence
```

### Projection Updates

Projections are materialized views derived from events.
**Critical:** Projections update in the SAME TRANSACTION as event writes.

```python
# app/services/event_emitter.py (continued)
async def update_projection(
    room_id: UUID,
    event_type: str,
    payload: dict,
    session: Session
):
    """
    Update projection tables based on event type.
    This runs in the SAME TRANSACTION as the event write.

    Projections updated:
    - rooms: Room metadata and activity
    - room_participants: Participant membership
    - messages: Message history for queries
    """
    if event_type == "room.created":
        # Insert into rooms projection
        session.exec(
            text("""
                INSERT INTO rooms 
                (room_id, creator_id, story_id, title, created_at, last_activity)
                VALUES (:room_id, :creator_id, :story_id, :title, NOW(), NOW())
            """),
            {
                "room_id": room_id,
                "creator_id": payload["creator_id"],
                "story_id": payload.get("story_id"),
                "title": payload.get("title", "Untitled Room")
            }
        )

        # Creator is automatically first participant (handled by participant.joined event)

    elif event_type == "room.updated":
        # Update room metadata
        update_fields = payload.get("updated_fields", {})
        if "title" in update_fields:
            session.exec(
                text("UPDATE rooms SET title = :title WHERE room_id = :room_id"),
                {"title": update_fields["title"], "room_id": room_id}
            )
        session.exec(
            text("UPDATE rooms SET last_activity = NOW() WHERE room_id = :room_id"),
            {"room_id": room_id}
        )

    elif event_type == "participant.joined":
        # Add participant to room_participants projection
        session.exec(
            text("""
                INSERT INTO room_participants 
                (room_id, participant_id, participant_type, role, joined_at, active)
                VALUES (:room_id, :participant_id, :participant_type, :role, NOW(), true)
                ON CONFLICT (room_id, participant_id) 
                DO UPDATE SET active = true, joined_at = NOW()
            """),
            {
                "room_id": room_id,
                "participant_id": payload["participant_id"],
                "participant_type": payload["participant_type"],  # 'user' or 'agent'
                "role": payload.get("role", "member")  # 'owner' or 'member'
            }
        )
        # Update room activity
        session.exec(
            text("UPDATE rooms SET last_activity = NOW() WHERE room_id = :room_id"),
            {"room_id": room_id}
        )

    elif event_type == "participant.left":
        # Mark participant as inactive
        session.exec(
            text("""
                UPDATE room_participants 
                SET active = false, left_at = NOW()
                WHERE room_id = :room_id AND participant_id = :participant_id
            """),
            {
                "room_id": room_id,
                "participant_id": payload["participant_id"]
            }
        )

    elif event_type == "participant.role_changed":
        # Update participant role
        session.exec(
            text("""
                UPDATE room_participants 
                SET role = :new_role
                WHERE room_id = :room_id AND participant_id = :participant_id
            """),
            {
                "room_id": room_id,
                "participant_id": payload["participant_id"],
                "new_role": payload["new_role"]
            }
        )

    elif event_type == "message.user":
        # Insert into messages projection
        session.exec(
            text("""
                INSERT INTO messages 
                (room_id, sender_type, sender_id, content, created_at)
                VALUES (:room_id, 'user', :sender_id, :content, NOW())
            """),
            {
                "room_id": room_id,
                "sender_id": payload["sender_id"],
                "content": payload["content"]
            }
        )
        # Update room last_activity
        session.exec(
            text("UPDATE rooms SET last_activity = NOW() WHERE room_id = :room_id"),
            {"room_id": room_id}
        )

    elif event_type == "message.agent":
        # Agent messages (agents are room participants)
        session.exec(
            text("""
                INSERT INTO messages 
                (room_id, sender_type, agent_name, content, created_at)
                VALUES (:room_id, 'agent', :agent_name, :content, NOW())
            """),
            {
                "room_id": room_id,
                "agent_name": payload["agent_name"],
                "content": payload["content"]
            }
        )
        # Update room last_activity
        session.exec(
            text("UPDATE rooms SET last_activity = NOW() WHERE room_id = :room_id"),
            {"room_id": room_id}
        )

    elif event_type in ["tool.start", "tool.end", "agent.handoff"]:
        # Observability events - update room activity but no projection
        session.exec(
            text("UPDATE rooms SET last_activity = NOW() WHERE room_id = :room_id"),
            {"room_id": room_id}
        )
```

### Event Sourcing in Routes

Example of using event sourcing in API routes:

```python
# app/api/routes/rooms.py
from app.services.event_emitter import emit_event
from app.services.agent_runner import AgentRunner
from app.crud import check_room_membership

@router.post("/rooms/{room_id}/messages")
async def send_message(
    room_id: UUID,
    message: MessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> MessagePublic:
    """Send a message to room and trigger agent responses"""

    # Validate room membership
    if not await check_room_membership(room_id, current_user.id, session):
        raise HTTPException(403, "Not a room participant")

    # Start transaction
    with session.begin():
        # 1. Emit user message event
        await emit_event(
            room_id=room_id,
            event_type="message.user",
            payload={
                "sender_id": str(current_user.id),
                "content": message.content
            },
            session=session
        )
        # Transaction commits here - event and projections persisted atomically

    # 2. Run agent participants (outside transaction to avoid long-running LLM calls in transaction)
    agent_participants = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.participant_type == "agent")
        .where(RoomParticipant.active == True)
    ).all()

    # Run each agent participant
    for agent_participant in agent_participants:
        await AgentRunner().run_agent(
            room_id=room_id,
            user_message=message.content,
            user_id=current_user.id,
            agent_name=agent_participant.participant_id,
            session=session
        )

    # Agent runner will emit message.agent events internally

    return MessagePublic(
        sender_type="user",
        content=message.content,
        created_at=datetime.now()
    )

@router.post("/rooms/{room_id}/participants")
async def add_participant(
    room_id: UUID,
    participant: ParticipantCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ParticipantPublic:
    """Add a user or agent to the room (owner only)"""

    # Check if current user is room owner
    owner_check = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.participant_id == str(current_user.id))
        .where(RoomParticipant.role == "owner")
    ).first()

    if not owner_check:
        raise HTTPException(403, "Only room owner can add participants")

    # Emit participant.joined event
    with session.begin():
        await emit_event(
            room_id=room_id,
            event_type="participant.joined",
            payload={
                "participant_id": participant.participant_id,
                "participant_type": participant.participant_type,  # 'user' or 'agent'
                "role": "member"
            },
            session=session
        )

    return ParticipantPublic(
        participant_id=participant.participant_id,
        participant_type=participant.participant_type,
        role="member",
        joined_at=datetime.now()
    )
```

### Event Immutability Rules

**CRITICAL:** Events are **immutable** once written to `room_events`.

```python
# WRONG - Never do this
session.exec(
    text("UPDATE room_events SET payload = ... WHERE event_id = ...")
)

# WRONG - Never do this
session.exec(
    text("DELETE FROM room_events WHERE event_id = ...")
)

# RIGHT - Emit a new event to record the change
await emit_event(
    room_id=room_id,
    event_type="message.deleted",
    payload={
        "deleted_message_id": message_id,
        "deleted_by": user_id,
        "reason": "user_request"
    },
    session=session
)

# Then update projection to hide deleted message
session.exec(
    text("""
        UPDATE messages 
        SET deleted = true, deleted_at = NOW(), deleted_by = :user_id
        WHERE message_id = :message_id
    """),
    {"message_id": message_id, "user_id": user_id}
)
```

### Event Replay Testing

All projections must be rebuildable from events:

```python
# app/tests/services/test_event_replay.py
import pytest
from sqlmodel import Session, select, text
from app.services.event_emitter import update_projection
from app.models import RoomEvent, Room, RoomParticipant, Message
import json

@pytest.mark.asyncio
async def test_projection_can_be_rebuilt_from_events():
    """Verify projections can be rebuilt from event log"""

    # 1. Create some events via normal flow
    room_id = await create_room(creator_id, story_id)
    await add_participant(room_id, user_id, "user", "owner")
    await add_participant(room_id, "story_advisor", "agent", "member")
    await send_message(room_id, "Hello")
    await send_message(room_id, "World")

    # 2. Save current projection state
    messages_before = session.exec(
        select(Message).where(Message.room_id == room_id)
    ).all()

    participants_before = session.exec(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    ).all()

    room_before = session.get(Room, room_id)

    # 3. Truncate projections (not events!)
    session.exec(text("TRUNCATE messages, room_participants, rooms CASCADE"))
    session.commit()

    # 4. Replay all events in order
    events = session.exec(
        select(RoomEvent)
        .where(RoomEvent.room_id == room_id)
        .order_by(RoomEvent.room_sequence)
    ).all()

    for event in events:
        await update_projection(
            room_id=event.room_id,
            event_type=event.event_type,
            payload=json.loads(event.payload),
            session=session
        )

    session.commit()

    # 5. Verify projections match original
    messages_after = session.exec(
        select(Message).where(Message.room_id == room_id)
    ).all()

    participants_after = session.exec(
        select(RoomParticipant).where(RoomParticipant.room_id == room_id)
    ).all()

    room_after = session.get(Room, room_id)

    assert len(messages_after) == len(messages_before)
    assert all(
        before.content == after.content
        for before, after in zip(messages_before, messages_after)
    )

    assert len(participants_after) == len(participants_before)
    assert room_after.title == room_before.title

@pytest.mark.asyncio
async def test_multi_user_event_replay():
    """Verify participant events are correctly replayed"""

    # Create room with multiple participants
    room_id = await create_room(creator_id, story_id)
    await add_participant(room_id, user1_id, "user", "owner")
    await add_participant(room_id, user2_id, "user", "member")
    await add_participant(room_id, "story_advisor", "agent", "member")

    # Truncate and replay
    session.exec(text("TRUNCATE room_participants CASCADE"))

    events = session.exec(
        select(RoomEvent)
        .where(RoomEvent.room_id == room_id)
        .where(RoomEvent.event_type.in_(["participant.joined", "participant.left"]))
        .order_by(RoomEvent.room_sequence)
    ).all()

    for event in events:
        await update_projection(
            room_id=event.room_id,
            event_type=event.event_type,
            payload=json.loads(event.payload),
            session=session
        )

    # Verify participant count
    participants = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.active == True)
    ).all()

    assert len(participants) == 3  # 2 users + 1 agent
    assert sum(1 for p in participants if p.participant_type == "user") == 2
    assert sum(1 for p in participants if p.participant_type == "agent") == 1
```

---

## Context Provider Pattern

### Building Room-Aware Agent Context

Agents need room context including participants for multi-user awareness:

```python
# app/services/context_provider.py
from uuid import UUID
from sqlmodel import Session, select
from app.models import Story, StoryNode, Message, Room, RoomParticipant

async def build_room_context(
    room_id: UUID,
    user_id: UUID,
    session: Session
) -> RoomContext:
    """
    Build room-aware context for agent execution.

    Includes:
    - Recent message history (last 20 messages)
    - Room metadata (story_id, created_at, etc.)
    - Active participants (users and agents)
    - Story outline (if room is story-specific)

    Args:
        room_id: Room ID
        user_id: User ID making the request
        session: Database session

    Returns:
        RoomContext with all required fields

    Raises:
        ValueError: If room not found
    """

    # Get room metadata
    room = session.get(Room, room_id)
    if not room:
        raise ValueError(f"Room {room_id} not found")

    # Get active participants
    participants = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.active == True)
    ).all()

    participant_list = [
        {
            "participant_id": str(p.participant_id),
            "participant_type": p.participant_type,
            "role": p.role,
            "joined_at": p.joined_at.isoformat() if p.joined_at else None
        }
        for p in participants
    ]

    # Get message history (last 20 messages)
    messages = session.exec(
        select(Message)
        .where(Message.room_id == room_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    ).all()

    message_history = [
        {
            "role": "user" if msg.sender_type == "user" else "assistant",
            "content": msg.content,
            "sender_id": str(msg.sender_id) if msg.sender_id else msg.agent_name,
            "created_at": msg.created_at.isoformat()
        }
        for msg in reversed(messages)  # Chronological order
    ]

    # Get story context if available
    story_data = None
    if room.story_id:
        story = session.get(Story, room.story_id)
        if story:
            story_data = {
                "title": story.title,
                "description": story.description,
                "node_count": len(story.nodes),
                "outline": format_story_outline(story)
            }

    return RoomContext(
        room_id=room_id,
        user_id=user_id,
        participants=participant_list,
        room_metadata={
            "created_at": room.created_at.isoformat(),
            "story_id": str(room.story_id) if room.story_id else None,
            "last_activity": room.last_activity.isoformat(),
            "title": room.title,
            "participant_count": len(participant_list)
        },
        story_id=room.story_id,
        story_data=story_data,
        message_history=message_history
    )

def format_story_outline(story: Story) -> str:
    """Format story structure for agent context"""
    outline = f"# {story.title}\n\n{story.description}\n\n## Nodes:\n"

    # Limit to first 10 nodes to manage context size
    for node in story.nodes[:10]:
        outline += f"- {node.title}: {node.text[:100]}...\n"

    if len(story.nodes) > 10:
        outline += f"\n... and {len(story.nodes) - 10} more nodes\n"

    return outline
```

### Context Size Management

**Context Token Limits:**
- GPT-3.5-turbo: 4,096 tokens (~3,000 words)
- GPT-4: 8,192 tokens (~6,000 words)
- GPT-4-32k: 32,768 tokens (~24,000 words)

**Rules:**
- Keep message history to last 20 messages
- Truncate long story outlines
- Summarize instead of including full text
- Monitor token usage via logging
- Include participant count but not full user details

```python
# Estimate tokens (rough approximation)
def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token"""
    return len(text) // 4

# Check context size before agent run
def validate_context_size(ctx: RoomContext) -> RoomContext:
    """Ensure context fits within token limits"""
    # Estimate total tokens
    message_tokens = sum(estimate_tokens(msg["content"]) for msg in ctx.message_history)
    story_tokens = estimate_tokens(ctx.story_data.get("outline", "")) if ctx.story_data else 0

    total_tokens = message_tokens + story_tokens

    # If over 3000 tokens, truncate
    if total_tokens > 3000:
        # Keep only last 10 messages
        ctx.message_history = ctx.message_history[-10:]

        # Truncate story outline
        if ctx.story_data and "outline" in ctx.story_data:
            ctx.story_data["outline"] = ctx.story_data["outline"][:500] + "..."

    return ctx
```

---

## Agent Runner Service

### Service Structure

```python
# app/services/agent_runner.py
from uuid import UUID
from sqlmodel import Session, select
from app.agents.registry import AGENT_REGISTRY
from app.services.context_provider import build_room_context, validate_context_size
from app.services.event_emitter import emit_event
from app.models import RoomParticipant
import logging

logger = logging.getLogger(__name__)

class AgentRunner:
    """Executes agents with proper room context and event emission"""

    async def run_agent(
        self,
        room_id: UUID,
        user_message: str,
        user_id: UUID,
        agent_name: str = "story_advisor",
        session: Session = None
    ) -> str:
        """
        Execute agent as room participant and return response.

        Args:
            room_id: Room ID (multi-user room)
            user_message: User's message content
            user_id: User ID for context
            agent_name: Which agent to run (from registry)
            session: Database session

        Returns:
            Agent's response text

        Raises:
            ValueError: If agent not found or not a room participant
        """
        # Verify agent is a participant in this room
        agent_participant = session.exec(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.participant_id == agent_name)
            .where(RoomParticipant.participant_type == "agent")
            .where(RoomParticipant.active == True)
        ).first()

        if not agent_participant:
            raise ValueError(f"Agent {agent_name} not a participant in room {room_id}")

        # Get agent from registry
        if agent_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_name}")

        agent = AGENT_REGISTRY[agent_name]["agent"]

        # Build room-aware context
        ctx = await build_room_context(room_id, user_id, session)
        ctx = validate_context_size(ctx)

        # Log execution
        logger.info(
            f"Running agent {agent_name} for room {room_id}",
            extra={
                "room_id": str(room_id),
                "agent_name": agent_name,
                "participant_count": len(ctx.participants),
                "message_length": len(user_message)
            }
        )

        # Run agent
        try:
            result = await agent.run(user_message, deps=ctx)

            # Emit response event (visible to all room participants)
            with session.begin():
                await emit_event(
                    room_id=room_id,
                    event_type="message.agent",
                    payload={
                        "agent_name": agent_name,
                        "content": result.data,
                        "model": agent.model_name
                    },
                    session=session
                )

            logger.info(
                f"Agent {agent_name} completed successfully",
                extra={
                    "room_id": str(room_id),
                    "response_length": len(result.data)
                }
            )

            return result.data

        except TimeoutError:
            logger.error(f"Agent timeout for room {room_id}, agent {agent_name}")
            return "I'm sorry, I'm taking too long to respond. Please try again."

        except Exception as e:
            logger.exception(f"Agent error for room {room_id}, agent {agent_name}: {e}")

            # Emit error event (visible to all room participants for transparency)
            await emit_event(
                room_id=room_id,
                event_type="agent.error",
                payload={
                    "agent_name": agent_name,
                    "error": str(e),
                    "user_message": user_message[:100]
                },
                session=session
            )

            return "I encountered an error. Please try rephrasing your question."

    async def run_room_agents(
        self,
        room_id: UUID,
        user_message: str,
        user_id: UUID,
        session: Session
    ):
        """
        Run all active agent participants in a room.

        Args:
            room_id: Room ID
            user_message: User's message
            user_id: User ID for context
            session: Database session
        """
        # Get all active agent participants
        agent_participants = session.exec(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.participant_type == "agent")
            .where(RoomParticipant.active == True)
        ).all()

        # Run each agent
        for agent_participant in agent_participants:
            try:
                await self.run_agent(
                    room_id=room_id,
                    user_message=user_message,
                    user_id=user_id,
                    agent_name=agent_participant.participant_id,
                    session=session
                )
            except Exception as e:
                logger.exception(
                    f"Failed to run agent {agent_participant.participant_id}: {e}"
                )
                # Continue with other agents
                continue

    async def stream_agent_response(
        self,
        room_id: UUID,
        user_message: str,
        user_id: UUID,
        agent_name: str = "story_advisor",
        session: Session = None
    ) -> AsyncIterator[str]:
        """
        Stream agent response token-by-token to all room participants (for WebSocket).
        Used in Phase 4 (Streaming).

        Args:
            room_id: Room ID
            user_message: User's message
            user_id: User ID for context
            agent_name: Agent to run
            session: Database session

        Yields:
            Response tokens as they're generated
        """
        # Verify agent is room participant
        agent_participant = session.exec(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.participant_id == agent_name)
            .where(RoomParticipant.active == True)
        ).first()

        if not agent_participant:
            raise ValueError(f"Agent {agent_name} not a participant in room {room_id}")

        agent = AGENT_REGISTRY[agent_name]["agent"]
        ctx = await build_room_context(room_id, user_id, session)
        ctx = validate_context_size(ctx)

        full_response = ""
        async with agent.run_stream(user_message, deps=ctx) as result:
            async for chunk in result.stream_text():
                full_response += chunk
                yield chunk  # Stream to all connected room participants via WebSocket

        # After streaming completes, emit final event (visible to all participants)
        with session.begin():
            await emit_event(
                room_id=room_id,
                event_type="message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": full_response,
                    "model": agent.model_name
                },
                session=session
            )
```

---

## Migration Workflow

### Creating Room Event Sourcing Tables

When adding the room feature:

```bash
# 1. Create migration
docker compose exec backend alembic revision --autogenerate -m "Add room event sourcing tables"

# 2. Review the generated migration
# Check: backend/app/alembic/versions/XXX_add_room_event_sourcing_tables.py

# 3. Apply migration
docker compose exec backend alembic upgrade head

# 4. Verify tables created
docker compose exec db psql -U postgres -d tinyfoot -c "\dt room_*"
docker compose exec db psql -U postgres -d tinyfoot -c "\dt messages"
```

### Migration Template

```python
# alembic/versions/XXX_add_room_event_sourcing_tables.py
"""Add room event sourcing tables

Revision ID: XXX
Revises: YYY
Create Date: 2025-12-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXX'
down_revision = 'YYY'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Event log (append-only, room-scoped)
    op.create_table('room_events',
        sa.Column('event_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('room_sequence', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('room_id', 'room_sequence')
    )
    op.create_index('idx_room_events_room_seq', 'room_events', ['room_id', 'room_sequence'])
    op.create_index('idx_room_events_type', 'room_events', ['event_type', 'created_at'])

    # Trigger to prevent event mutations (CRITICAL for event sourcing)
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_room_event_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'room_events table is append-only - UPDATE/DELETE forbidden';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER prevent_room_event_update
            BEFORE UPDATE OR DELETE ON room_events
            FOR EACH ROW EXECUTE FUNCTION prevent_room_event_mutation();
    """)

    # Rooms (multi-user)
    op.create_table('rooms',
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('creator_id', sa.UUID(), nullable=False),
        sa.Column('story_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['creator_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['story_id'], ['story.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('room_id')
    )
    op.create_index('idx_rooms_creator_activity', 'rooms', ['creator_id', 'last_activity'])

    # Room participants (CRITICAL - users AND agents as first-class participants)
    op.create_table('room_participants',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('participant_id', sa.String(length=100), nullable=False),  # user UUID or agent name
        sa.Column('participant_type', sa.String(length=20), nullable=False),  # 'user' or 'agent'
        sa.Column('role', sa.String(length=20), nullable=False),  # 'owner' or 'member'
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('left_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.room_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('room_id', 'participant_id', name='uq_room_participant')
    )
    op.create_index('idx_room_participants_room_active', 'room_participants', ['room_id', 'active'])
    op.create_index('idx_room_participants_type', 'room_participants', ['participant_type'])

    # Message projection (room-scoped)
    op.create_table('messages',
        sa.Column('message_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('room_id', sa.UUID(), nullable=False),
        sa.Column('sender_type', sa.String(length=20), nullable=False),  # 'user' or 'agent'
        sa.Column('sender_id', sa.UUID(), nullable=True),  # For user messages
        sa.Column('agent_name', sa.String(length=50), nullable=True),  # For agent messages
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['room_id'], ['rooms.room_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('message_id')
    )
    op.create_index('idx_messages_room_time', 'messages', ['room_id', 'created_at'])

def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('room_participants')
    op.drop_table('rooms')
    op.execute('DROP TRIGGER IF EXISTS prevent_room_event_update ON room_events')
    op.execute('DROP FUNCTION IF EXISTS prevent_room_event_mutation')
    op.drop_table('room_events')
```

---

## Performance Considerations

### Database Indexes

Critical indexes for multi-user room system:

```sql
-- Event log queries (room-scoped)
CREATE INDEX idx_room_events_room_seq ON room_events (room_id, room_sequence);
CREATE INDEX idx_room_events_type ON room_events (event_type, created_at);

-- Room queries
CREATE INDEX idx_rooms_creator_activity ON rooms (creator_id, last_activity DESC);

-- Participant queries (CRITICAL for authorization)
CREATE INDEX idx_room_participants_room_active ON room_participants (room_id, active);
CREATE INDEX idx_room_participants_type ON room_participants (participant_type);
CREATE INDEX idx_room_participants_user ON room_participants (participant_id) WHERE participant_type = 'user';

-- Message queries
CREATE INDEX idx_messages_room_time ON messages (room_id, created_at DESC);
```

### Query Optimization

**Fast Message Retrieval:**
```python
# Good - uses index
messages = session.exec(
    select(Message)
    .where(Message.room_id == room_id)
    .order_by(Message.created_at.desc())
    .limit(20)
).all()

# Bad - full table scan without room filter
messages = session.exec(
    select(Message)
    .order_by(Message.created_at.desc())
).all()

# Good - query participants for authorization
participants = session.exec(
    select(RoomParticipant)
    .where(RoomParticipant.room_id == room_id)
    .where(RoomParticipant.active == True)
).all()

# Good - check specific participant membership
is_participant = session.exec(
    select(RoomParticipant)
    .where(RoomParticipant.room_id == room_id)
    .where(RoomParticipant.participant_id == str(user_id))
    .where(RoomParticipant.active == True)
).first() is not None
```

### Connection Pooling

Configure appropriate pool sizes in `app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Database pool for general queries
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20

    # Separate pool for agent execution (long-running)
    AGENT_POOL_SIZE: int = 5
    AGENT_MAX_OVERFLOW: int = 10
```

---

## Error Handling

### Agent Execution Errors

```python
# app/services/agent_runner.py
import logging

logger = logging.getLogger(__name__)

async def run_agent(self, ...):
    try:
        result = await agent.run(user_message, deps=ctx)
        return result.data

    except TimeoutError:
        logger.error(
            f"Agent timeout for room {room_id}, agent {agent_name}",
            extra={"room_id": str(room_id), "agent_name": agent_name}
        )
        return "I'm sorry, I'm taking too long to respond. Please try again."

    except Exception as e:
        logger.exception(
            f"Agent error for room {room_id}, agent {agent_name}: {e}",
            extra={
                "room_id": str(room_id),
                "agent_name": agent_name,
                "participant_count": len(ctx.participants)
            }
        )

        # Emit error event (visible to all room participants for transparency)
        await emit_event(
            room_id=room_id,
            event_type="agent.error",
            payload={
                "agent_name": agent_name,
                "error": str(e),
                "user_message": user_message[:100]
            },
            session=session
        )

        return "I encountered an error. Please try rephrasing your question."
```

### Event Emission Errors

```python
# If event emission fails, the entire transaction should rollback
async def send_message(...):
    try:
        with session.begin():
            await emit_event(...)  # room_id, event_type, payload
            # If this fails, transaction rolls back
    except Exception as e:
        logger.exception(f"Event emission failed for room {room_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save message. Please try again."
        )
```

---

## Security Considerations

### Authorization

Always check room membership before any room operation:

```python
# app/crud.py
async def check_room_membership(
    room_id: UUID,
    user_id: UUID,
    session: Session
) -> bool:
    """
    Check if user is an active participant in the room.

    Args:
        room_id: Room ID
        user_id: User ID
        session: Database session

    Returns:
        True if user is active participant, False otherwise
    """
    result = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.participant_id == str(user_id))
        .where(RoomParticipant.participant_type == "user")
        .where(RoomParticipant.active == True)
    ).first()

    return result is not None

# In routes - ALWAYS check before operations
if not await check_room_membership(room_id, current_user.id, session):
    raise HTTPException(status_code=403, detail="Not a room participant")
```

### Rate Limiting

Implement rate limiting for room operations:

```python
# app/api/routes/rooms.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/rooms/{room_id}/messages")
@limiter.limit("10/minute")  # 10 messages per minute per IP
async def send_message(...):
    # First check room membership
    if not await check_room_membership(room_id, current_user.id, session):
        raise HTTPException(403, "Not a room participant")
    # ... rest of endpoint
```

---

## Monitoring and Logging

### Key Metrics to Track

```python
# app/services/agent_runner.py
from prometheus_client import Counter, Histogram

# Metrics
agent_calls_total = Counter(
    'agent_calls_total', 
    'Total agent executions',
    ['agent_name', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent execution duration',
    ['agent_name']
)

room_participants_gauge = Gauge(
    'room_participants_total',
    'Number of participants per room',
    ['room_id']
)

# In run_agent()
with agent_duration.labels(agent_name=agent_name).time():
    try:
        result = await agent.run(...)
        agent_calls_total.labels(agent_name=agent_name, status='success').inc()
    except Exception:
        agent_calls_total.labels(agent_name=agent_name, status='error').inc()
        raise
```

### Structured Logging

```python
logger.info(
    "Agent execution completed",
    extra={
        "room_id": str(room_id),
        "user_id": str(user_id),
        "agent_name": agent_name,
        "participant_count": len(ctx.participants),
        "message_length": len(user_message),
        "response_length": len(result.data),
        "duration_ms": duration_ms
    }
)
```

---

## Summary: Key Takeaways

1. **Agents are room participants** - First-class members with equal standing in event log, not external responders
2. **Agents are stateless** - All context comes from RoomContext dependency with participant awareness
3. **Events are immutable** - Never UPDATE or DELETE events from room_events table
4. **Projections are transactional** - Updated in same transaction as events (rooms, room_participants, messages)
5. **Tools should be focused** - One responsibility per tool, with room-aware context
6. **Context is room-aware** - Includes participants, room metadata, last 20 messages, and story outline
7. **Always check room membership** - Before any room read/write operations via room_participants table
8. **Multi-user visibility** - All events visible to all room participants for transparency
9. **Log everything** - Agent calls, errors, durations, participant context for observability
10. **Test event replay** - Projections must be rebuildable from room_events

---

## Multi-User Collaboration Principles

### Participant Equality
- Users and agents are both participants in room_participants table
- All participants see all events (messages, errors, tool executions)
- participant_type field distinguishes 'user' from 'agent'
- role field defines 'owner' vs 'member' permissions

### Authorization Model
- Room membership checked via active flag in room_participants
- Only room owner can add/remove participants
- All participants can send messages and view history
- Agents automatically respond when they are active participants

### Event Visibility
- All room events visible to all participants
- No private messages between subset of participants (V1)
- Transparency enables collaborative story development
- Error events visible to all for debugging assistance

---

**Next Steps After Phase 1:**
1. Review these patterns with team
2. Create first room-aware agent following these patterns
3. Write comprehensive tests including multi-user scenarios
4. Implement room_participants management in API
5. Update this document with learnings and edge cases

---

**Version:** 1.0  
**Last Updated:** December 12, 2025  
**Status:** Production Ready - Aligned with MasterImplementationPlan  
**Maintainer:** Backend Team
