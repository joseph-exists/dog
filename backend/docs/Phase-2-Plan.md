# Phase 2 Implementation Plan: Agent Integration

**Duration:** 5-6 days
**Goal:** Make agents first-class room participants and run them with room-aware context.

## Executive Summary

### Deliverables
- StoryAdvisor agent with tools (get_story_outline, get_conversation_summary, get_room_participants)
- Agent registry for managing multiple agents
- Context provider for room-aware agent execution
- Agent runner service emitting `room_message.agent` events
- Integration with rooms API for automatic agent responses
- Support for multiple agents in one room

### Success Criteria
✅ Agent responses are visible to all room participants
✅ Agents have access to story-aware context (story data + recent messages)
✅ All agent interactions are persisted and replayable from events
✅ Multiple agents can coexist in one room
✅ All operations follow Phase 1 transaction patterns

---

## Phase 1 Status (Complete ✅)

### Infrastructure
- `room_events` table: Append-only event log with `room_sequence` ordering
- `rooms` table: Projection with `room_id`, `creator_id`, `title`, `story_id`, `last_activity`
- `room_participants` table: Tracks users and agents with `participant_type`, `role`, `active`
- `room_messages` table: Message projection with `sender_type` ("user" or "agent"), `sender_id`, `agent_name`
- Event emitter service: `emit_event()` with transactional projection updates and `session.flush()`
- Route-level transactions: `AsyncSessionTransactionDep` pattern for write operations
- CRUD functions: Transaction-agnostic, receive session from route handlers

### Key Integration Points
1. **Routes** (`app/api/routes/rooms.py`):
   - `POST /rooms/{room_id}/messages` - Send message (will add agent trigger)
   - `POST /rooms/{room_id}/participants` - Add participant (supports agents)

2. **Event Emitter** (`app/services/event_emitter.py`):
   - `room_message.agent` event type already supported ✅
   - Projection handler `_handle_room_message_agent()` exists ✅

3. **Models** (`app/models.py`):
   - `RoomMessage.agent_name` field for agent identification ✅
   - `RoomParticipant.participant_type` supports "agent" ✅

---

## Implementation Order (Dependencies)

```
1. Agent Registry (no dependencies)
   └─ app/agents/agent_registry.py

2. Context Provider (no dependencies)
   └─ app/services/context_provider.py

3. StoryAdvisor Agent (depends on: 1, 2)
   └─ app/agents/story_advisor.py

4. Agent Runner Service (depends on: 1, 2, 3)
   └─ app/services/agent_runner.py

5. Agent Module Init (depends on: 3)
   └─ app/agents/__init__.py

6. Route Integration (depends on: 4)
   └─ Modify: app/api/routes/rooms.py

7. Main App Init (depends on: 5)
   └─ Modify: app/main.py

8. Tests (after each component)
   └─ app/tests/agents/
   └─ app/tests/services/
   └─ app/tests/api/routes/
```

---

## Deliverable 1: Agent Registry

**File:** `app/agents/agent_registry.py`
**Purpose:** Central registry for managing available agents
**Dependencies:** None (foundational)

### Complete Implementation

```python
"""
Agent Registry: Central registry for room-participating agents.

Provides agent lookup by name and validation. Agents register themselves
at module load time. This enables multiple agents in one room without
tight coupling.

Usage:
    from app.agents.agent_registry import AGENT_REGISTRY, get_agent

    # Register an agent
    AGENT_REGISTRY["StoryAdvisor"] = story_advisor_agent

    # Get an agent
    agent = get_agent("StoryAdvisor")
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic_ai import Agent

# Global registry mapping agent names to Agent instances
AGENT_REGISTRY: dict[str, "Agent"] = {}


def register_agent(name: str, agent: "Agent") -> None:
    """
    Register an agent with the given name.

    Args:
        name: Unique agent name (e.g., "StoryAdvisor")
        agent: PydanticAI Agent instance

    Raises:
        ValueError: If agent with name already registered
    """
    if name in AGENT_REGISTRY:
        raise ValueError(f"Agent '{name}' already registered")
    AGENT_REGISTRY[name] = agent


def get_agent(name: str) -> "Agent":
    """
    Get an agent by name.

    Args:
        name: Agent name to look up

    Returns:
        The registered Agent instance

    Raises:
        KeyError: If agent not found
    """
    if name not in AGENT_REGISTRY:
        raise KeyError(f"Agent '{name}' not found in registry")
    return AGENT_REGISTRY[name]


def list_agents() -> list[str]:
    """Return list of registered agent names."""
    return list(AGENT_REGISTRY.keys())


def is_agent_registered(name: str) -> bool:
    """Check if an agent is registered."""
    return name in AGENT_REGISTRY
```

### Acceptance Criteria
- [ ] Registry stores agents by name
- [ ] Duplicate registration raises `ValueError`
- [ ] Unknown agent lookup raises `KeyError`
- [ ] `list_agents()` returns all names
- [ ] `is_agent_registered()` returns correct boolean

---

## Deliverable 2: Context Provider

**File:** `app/services/context_provider.py`
**Purpose:** Build room-aware context for agents
**Dependencies:** None (foundational)

### Complete Implementation

```python
"""
Context Provider Service: Room-aware context builder for agents.

Provides limited context (20 messages + story outline) to prevent
context window overflow while maintaining conversation relevance.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Room, RoomMessage, RoomParticipant, Story


@dataclass
class RoomContext:
    """
    Context object passed to agents for room-aware responses.

    Attributes:
        room_id: UUID of the current room
        story_id: Optional UUID of associated story
        story_data: Story details (title, description) if available
        recent_messages: Last N messages for conversation context
        participants: List of active participants (users and agents)
        room_metadata: Room title, creator, timestamps
    """
    room_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict[str, Any] | None
    recent_messages: list[dict[str, Any]]
    participants: list[dict[str, Any]]
    room_metadata: dict[str, Any]


async def build_room_context(
    *,
    room_id: uuid.UUID,
    session: AsyncSession,
    message_limit: int = 20,
) -> RoomContext:
    """
    Build context for an agent given a room_id.

    This function:
    1. Loads room metadata (title, story_id, etc.)
    2. Loads associated story data if present
    3. Fetches last N messages for conversation context
    4. Lists active participants

    Args:
        room_id: UUID of the room
        session: Async database session
        message_limit: Max messages to include (default 20)

    Returns:
        RoomContext with all data needed for agent response

    Raises:
        ValueError: If room does not exist
    """
    # Load room
    result = await session.execute(
        select(Room).where(Room.room_id == room_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise ValueError(f"Room {room_id} not found")

    # Load story data if associated
    story_data = None
    if room.story_id:
        story_result = await session.execute(
            select(Story).where(Story.id == room.story_id)
        )
        story = story_result.scalar_one_or_none()
        if story:
            story_data = {
                "id": str(story.id),
                "title": story.title,
                "description": story.description,
                "is_published": story.is_published,
            }

    # Load recent messages (ordered by created_at desc, then reversed)
    messages_result = await session.execute(
        select(RoomMessage)
        .where(RoomMessage.room_id == room_id)
        .order_by(RoomMessage.created_at.desc())
        .limit(message_limit)
    )
    messages = messages_result.scalars().all()

    recent_messages = [
        {
            "message_id": str(msg.message_id),
            "sender_type": msg.sender_type,
            "sender_id": str(msg.sender_id) if msg.sender_id else None,
            "agent_name": msg.agent_name,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        for msg in reversed(messages)  # Chronological order
    ]

    # Load active participants
    participants_result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participants_list = participants_result.scalars().all()

    participants = [
        {
            "participant_id": p.participant_id,
            "participant_type": p.participant_type,
            "role": p.role,
            "joined_at": p.joined_at.isoformat(),
        }
        for p in participants_list
    ]

    room_metadata = {
        "room_id": str(room.room_id),
        "title": room.title,
        "creator_id": str(room.creator_id),
        "created_at": room.created_at.isoformat(),
        "last_activity": room.last_activity.isoformat(),
    }

    return RoomContext(
        room_id=room_id,
        story_id=room.story_id,
        story_data=story_data,
        recent_messages=recent_messages,
        participants=participants,
        room_metadata=room_metadata,
    )
```

### Context Loading Strategy
1. Load room metadata (title, creator, timestamps)
2. Load associated story data if `story_id` is set
3. Fetch last N messages (default 20, chronological order)
4. List active participants (users and agents)

### Acceptance Criteria
- [ ] Returns `RoomContext` with all fields populated
- [ ] Room without story has `story_data=None`
- [ ] Message limit is respected (default 20)
- [ ] Messages in chronological order (oldest first)
- [ ] Only active participants included
- [ ] Non-existent room raises `ValueError`

---

## Deliverable 3: StoryAdvisor Agent

**File:** `app/agents/story_advisor.py`
**Purpose:** AI assistant for story writing and development
**Dependencies:** Agent Registry, Context Provider

### Complete Implementation

```python
"""
StoryAdvisor Agent: AI assistant for story writing and development.

This agent participates in rooms to help authors with:
- Story structure and pacing
- Character development
- Plot consistency
- Writing suggestions

The agent is room-aware and uses story context when available.
"""
from __future__ import annotations

import logging
from typing import Any

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

from app.agents.agent_registry import register_agent
from app.services.context_provider import RoomContext

logger = logging.getLogger(__name__)


class StoryAdvisorDeps(BaseModel):
    """Dependencies for StoryAdvisor agent tools."""
    context: RoomContext

    class Config:
        arbitrary_types_allowed = True


# Create the agent
story_advisor = Agent(
    "openai:gpt-4o-mini",  # Cost-effective for advisory tasks
    deps_type=StoryAdvisorDeps,
    system_prompt="""You are StoryAdvisor, an expert writing assistant who helps authors develop their stories.

Your responsibilities:
- Provide constructive feedback on story elements
- Help with plot development and pacing
- Suggest character arcs and motivations
- Maintain consistency with established story details
- Be encouraging while offering specific, actionable suggestions

When you have story context available, reference specific details from the story.
When responding in a room with multiple participants, be conversational and address
the group naturally.

Keep responses concise but helpful. Avoid generic advice - be specific to the story
and conversation context provided.""",
)


@story_advisor.tool
async def get_story_outline(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get the current story's outline and description.

    Use this tool when you need to reference story details to provide
    contextual advice.
    """
    story_data = ctx.deps.context.story_data
    if not story_data:
        return "No story is currently associated with this room."

    return f"""Story: {story_data.get('title', 'Untitled')}

Description: {story_data.get('description', 'No description provided.')}

Published: {'Yes' if story_data.get('is_published') else 'No (draft)'}"""


@story_advisor.tool
async def get_conversation_summary(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get a summary of recent conversation in the room.

    Use this to understand what has been discussed before responding.
    """
    messages = ctx.deps.context.recent_messages
    if not messages:
        return "No previous messages in this conversation."

    summary_parts = []
    for msg in messages[-10:]:  # Last 10 messages for summary
        sender = msg.get("agent_name") or f"User {msg.get('sender_id', 'unknown')[:8]}"
        content = msg.get("content", "")[:200]  # Truncate long messages
        summary_parts.append(f"- {sender}: {content}")

    return "Recent conversation:\n" + "\n".join(summary_parts)


@story_advisor.tool
async def get_room_participants(ctx: RunContext[StoryAdvisorDeps]) -> str:
    """
    Get list of participants in the current room.

    Use this to understand who is in the conversation.
    """
    participants = ctx.deps.context.participants
    if not participants:
        return "No participants found."

    parts = []
    for p in participants:
        ptype = p.get("participant_type", "unknown")
        pid = p.get("participant_id", "unknown")
        role = p.get("role", "member")

        if ptype == "agent":
            parts.append(f"- {pid} (agent)")
        else:
            parts.append(f"- User {pid[:8]}... ({role})")

    return "Room participants:\n" + "\n".join(parts)


# Register on module load
register_agent("StoryAdvisor", story_advisor)


async def run_story_advisor(
    user_message: str,
    context: RoomContext,
) -> str:
    """
    Run the StoryAdvisor agent with given context.

    Args:
        user_message: The message to respond to
        context: Room context with story data and conversation history

    Returns:
        Agent response text
    """
    deps = StoryAdvisorDeps(context=context)

    # Build conversation context for the agent
    conversation_context = ""
    if context.story_data:
        conversation_context += f"\nStory context: {context.story_data.get('title', 'Untitled')}\n"

    if context.recent_messages:
        recent = context.recent_messages[-5:]  # Include last 5 messages
        conversation_context += "\nRecent messages:\n"
        for msg in recent:
            sender = msg.get("agent_name") or f"User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    full_prompt = f"{conversation_context}\nUser message: {user_message}"

    try:
        result = await story_advisor.run(full_prompt, deps=deps)
        return result.data
    except Exception as e:
        logger.error(f"StoryAdvisor error: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again."
```

### Tools Overview
1. **`get_story_outline`** - Returns story title, description, published status
2. **`get_conversation_summary`** - Summarizes recent messages (last 10)
3. **`get_room_participants`** - Lists active participants with roles

### Acceptance Criteria
- [ ] Agent registers as "StoryAdvisor" on import
- [ ] Tools return expected data formats
- [ ] `run_story_advisor()` returns string response
- [ ] Errors handled gracefully with friendly message
- [ ] Agent uses story context when available

---

## Deliverable 4: Agent Runner Service

**File:** `app/services/agent_runner.py`
**Purpose:** Execute agents in room context and emit events
**Dependencies:** Agent Registry, Context Provider, StoryAdvisor

### Complete Implementation

```python
"""
Agent Runner Service: Execute agents in room context.

This service:
1. Loads room context via ContextProvider
2. Looks up agent via AgentRegistry
3. Runs the agent with context
4. Emits room_message.agent event with response
5. Handles errors gracefully

Transaction Management:
- Agent runner receives session from caller
- Does NOT manage its own transaction
- Route handler controls transaction lifecycle
"""
from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_registry import get_agent, is_agent_registered
from app.agents.story_advisor import run_story_advisor
from app.models import RoomParticipant
from app.services.context_provider import build_room_context
from app.services.event_emitter import emit_event

logger = logging.getLogger(__name__)


async def run_agent_for_room(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Run an agent in a room context and emit its response as an event.

    This is the main entry point for agent execution. It:
    1. Validates the agent exists
    2. Builds room context
    3. Runs the agent
    4. Emits room_message.agent event

    Args:
        room_id: UUID of the room
        agent_name: Name of the agent to run (e.g., "StoryAdvisor")
        trigger_message: The message that triggered the agent
        session: Async database session (transaction managed by caller)

    Returns:
        Dict with agent response details:
        {
            "agent_name": str,
            "content": str,
            "success": bool,
            "error": str | None
        }

    Note:
        This function does NOT manage transactions. The caller (route handler)
        must use AsyncSessionTransactionDep to ensure atomic operations.
    """
    # Validate agent exists
    if not is_agent_registered(agent_name):
        logger.warning(f"Attempted to run unregistered agent: {agent_name}")
        return {
            "agent_name": agent_name,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }

    try:
        # Build room context
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
        )

        # Run agent based on name
        # Currently we have special handling for StoryAdvisor
        # Future agents can be added with similar patterns
        if agent_name == "StoryAdvisor":
            response_content = await run_story_advisor(
                user_message=trigger_message,
                context=context,
            )
        else:
            # Generic agent execution path
            agent = get_agent(agent_name)
            result = await agent.run(trigger_message)
            response_content = result.data

        # Emit agent message event
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload={
                "agent_name": agent_name,
                "content": response_content,
            },
        )

        logger.info(f"Agent {agent_name} responded in room {room_id}")

        return {
            "agent_name": agent_name,
            "content": response_content,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Agent {agent_name} error in room {room_id}: {e}")

        # Emit error message as agent response
        error_content = f"I encountered an error while processing your request. Please try again."

        try:
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": error_content,
                },
            )
        except Exception as emit_error:
            logger.error(f"Failed to emit error message: {emit_error}")

        return {
            "agent_name": agent_name,
            "content": error_content,
            "success": False,
            "error": str(e),
        }


async def should_agent_respond(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    session: AsyncSession,
) -> bool:
    """
    Check if an agent should respond to a message.

    Currently checks if the agent is an active participant in the room.
    Future enhancements could add:
    - Rate limiting
    - @mention detection
    - Cooldown periods

    Args:
        room_id: UUID of the room
        agent_name: Name of the agent
        session: Async database session

    Returns:
        True if agent should respond, False otherwise
    """
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.participant_id == agent_name,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()

    return participant is not None


async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Run all active agents in a room that should respond to a message.

    This is the high-level function called from route handlers.
    It checks which agents are active in the room and runs each one.

    Args:
        room_id: UUID of the room
        trigger_message: The message that triggered agents
        session: Async database session (transaction managed by caller)

    Returns:
        List of agent response dicts (one per agent that ran)
    """
    # Find all active agent participants
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    agent_participants = result.scalars().all()

    responses = []
    for participant in agent_participants:
        agent_name = participant.participant_id

        # Only run if agent is registered
        if is_agent_registered(agent_name):
            response = await run_agent_for_room(
                room_id=room_id,
                agent_name=agent_name,
                trigger_message=trigger_message,
                session=session,
            )
            responses.append(response)
        else:
            logger.warning(
                f"Agent '{agent_name}' is participant in room {room_id} "
                f"but not registered in AGENT_REGISTRY"
            )

    return responses
```

### Transaction Pattern
⚠️ **CRITICAL**: Agent Runner does NOT manage transactions.
- Receives `session` from route handler (already in transaction)
- Uses `emit_event()` which calls `session.flush()`
- Route commits transaction on success, rolls back on error

### Acceptance Criteria
- [ ] Unregistered agent returns error dict (no crash)
- [ ] `run_agent_for_room()` emits `room_message.agent` event
- [ ] `should_agent_respond()` checks participant status
- [ ] `run_agents_for_message()` triggers all active agents
- [ ] Errors don't crash transaction
- [ ] Agent responses visible via subsequent queries (after flush)

---

## Deliverable 5: Route Integration

**File:** `app/api/routes/rooms.py` (modify existing)
**Purpose:** Trigger agents after user messages
**Dependencies:** Agent Runner

### Modification to `send_message` Endpoint

```python
from app.services.agent_runner import run_agents_for_message

@router.post("/{room_id}/messages", response_model=RoomMessagePublic)
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,  # Transaction managed here
    current_user: CurrentUser,
    message_in: RoomMessageSend,
) -> Any:
    """
    Send a message to a room.

    After user message is persisted, triggers any active agents in the room.
    All operations (user message + agent responses) are atomic within one transaction.
    """
    # 1. Send user message
    room_message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,
    )

    # 2. Trigger agents (within same transaction)
    await run_agents_for_message(
        room_id=room_id,
        trigger_message=message_in.content,
        session=session,
    )

    # 3. Transaction commits here (on return)
    return room_message
```

### Transaction Flow
```
Route (AsyncSessionTransactionDep)
  ↓ [TRANSACTION STARTS]
  ├─ send_user_message()
  │   └─ emit_event("room_message.user")
  │       └─ session.flush()
  ├─ run_agents_for_message()
  │   └─ run_agent_for_room()
  │       └─ emit_event("room_message.agent")
  │           └─ session.flush()
  ↓ [TRANSACTION COMMITS]
```

### Acceptance Criteria
- [ ] User message and agent responses in same transaction
- [ ] Agent messages appear in subsequent GET requests
- [ ] Transaction rolls back if agent runner fails
- [ ] Multiple agents can respond in same request

---

## Deliverable 6: Agent Initialization

**Files:**
- `app/agents/__init__.py` (create)
- `app/main.py` (modify)

### Agent Module Init
```python
"""
Agent module initialization.
Imports agent modules to trigger registration.
"""
from app.agents import story_advisor  # noqa: F401

# Future agents:
# from app.agents import character_helper  # noqa: F401
```

### Main App Integration
```python
# In app/main.py, add after imports:

# Initialize agent registry
import app.agents  # noqa: F401
```

### Acceptance Criteria
- [ ] StoryAdvisor is registered on app startup
- [ ] `list_agents()` returns ["StoryAdvisor"]
- [ ] Agent is available for room participation

---

## Testing Strategy

### Unit Tests

#### Context Provider (`tests/services/test_context_provider.py`)
- [ ] Context for room without story
- [ ] Context with story includes story data
- [ ] Recent messages limited and ordered
- [ ] Only active participants included
- [ ] Non-existent room raises ValueError

#### Agent Registry (`tests/agents/test_agent_registry.py`)
- [ ] Register agent successfully
- [ ] Duplicate registration raises error
- [ ] Get registered agent
- [ ] Unknown agent raises error
- [ ] List and check functions work

#### Agent Runner (`tests/services/test_agent_runner.py`)
- [ ] Unregistered agent returns error
- [ ] Agent emits event on success
- [ ] `should_agent_respond()` checks participation
- [ ] `run_agents_for_message()` triggers all active
- [ ] Errors handled gracefully

### Integration Tests

#### Rooms API with Agents (`tests/api/routes/test_rooms_with_agents.py`)
- [ ] Send message triggers agents
- [ ] Add agent as participant
- [ ] List participants includes agents
- [ ] Agent messages visible in message list
- [ ] Multiple agents respond to same message

### Manual Testing Checklist
- [ ] Add StoryAdvisor to room via API
- [ ] Send message and verify agent response
- [ ] Agent response visible to all participants
- [ ] Agent mentions story details (context-aware)
- [ ] Multiple agents can be added to room
- [ ] Reload page - conversation persists
- [ ] Agent responses in event log

### Complete Test Implementations

#### `tests/services/test_context_provider.py`

```python
"""Tests for Context Provider Service."""
import pytest
from uuid import uuid4

from app.services.context_provider import build_room_context, RoomContext


class TestContextProvider:
    """Test suite for context provider."""

    @pytest.mark.asyncio
    async def test_build_context_for_room_without_story(
        self, async_session, test_room
    ):
        """Context should work for rooms without associated stories."""
        context = await build_room_context(
            room_id=test_room.room_id,
            session=async_session,
        )

        assert isinstance(context, RoomContext)
        assert context.room_id == test_room.room_id
        assert context.story_data is None
        assert context.room_metadata["title"] == test_room.title

    @pytest.mark.asyncio
    async def test_build_context_with_story(
        self, async_session, test_room_with_story
    ):
        """Context should include story data when available."""
        context = await build_room_context(
            room_id=test_room_with_story.room_id,
            session=async_session,
        )

        assert context.story_data is not None
        assert "title" in context.story_data
        assert "description" in context.story_data

    @pytest.mark.asyncio
    async def test_build_context_includes_recent_messages(
        self, async_session, test_room_with_messages
    ):
        """Context should include recent messages."""
        context = await build_room_context(
            room_id=test_room_with_messages.room_id,
            session=async_session,
            message_limit=5,
        )

        assert len(context.recent_messages) <= 5
        # Messages should be in chronological order
        if len(context.recent_messages) > 1:
            first_time = context.recent_messages[0]["created_at"]
            last_time = context.recent_messages[-1]["created_at"]
            assert first_time <= last_time

    @pytest.mark.asyncio
    async def test_build_context_includes_participants(
        self, async_session, test_room_with_participants
    ):
        """Context should list active participants."""
        context = await build_room_context(
            room_id=test_room_with_participants.room_id,
            session=async_session,
        )

        assert len(context.participants) > 0
        # All participants should be active
        for p in context.participants:
            assert "participant_type" in p
            assert "role" in p

    @pytest.mark.asyncio
    async def test_build_context_nonexistent_room_raises(
        self, async_session
    ):
        """Should raise ValueError for non-existent room."""
        with pytest.raises(ValueError, match="not found"):
            await build_room_context(
                room_id=uuid4(),
                session=async_session,
            )
```

#### `tests/agents/test_agent_registry.py`

```python
"""Tests for Agent Registry."""
import pytest
from unittest.mock import MagicMock

from app.agents.agent_registry import (
    AGENT_REGISTRY,
    register_agent,
    get_agent,
    list_agents,
    is_agent_registered,
)


class TestAgentRegistry:
    """Test suite for agent registry."""

    def setup_method(self):
        """Clear registry before each test."""
        AGENT_REGISTRY.clear()

    def test_register_agent(self):
        """Should register agent successfully."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        assert "TestAgent" in AGENT_REGISTRY
        assert AGENT_REGISTRY["TestAgent"] is mock_agent

    def test_register_duplicate_raises(self):
        """Should raise error when registering duplicate name."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        with pytest.raises(ValueError, match="already registered"):
            register_agent("TestAgent", MagicMock())

    def test_get_agent(self):
        """Should return registered agent."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        result = get_agent("TestAgent")
        assert result is mock_agent

    def test_get_nonexistent_agent_raises(self):
        """Should raise KeyError for unregistered agent."""
        with pytest.raises(KeyError, match="not found"):
            get_agent("NonexistentAgent")

    def test_list_agents(self):
        """Should return list of registered agent names."""
        register_agent("Agent1", MagicMock())
        register_agent("Agent2", MagicMock())

        names = list_agents()
        assert "Agent1" in names
        assert "Agent2" in names

    def test_is_agent_registered(self):
        """Should correctly report registration status."""
        register_agent("TestAgent", MagicMock())

        assert is_agent_registered("TestAgent") is True
        assert is_agent_registered("OtherAgent") is False
```

#### `tests/services/test_agent_runner.py`

```python
"""Tests for Agent Runner Service."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.services.agent_runner import (
    run_agent_for_room,
    should_agent_respond,
    run_agents_for_message,
)


class TestAgentRunner:
    """Test suite for agent runner service."""

    @pytest.mark.asyncio
    async def test_run_agent_unregistered_returns_error(
        self, async_session, test_room
    ):
        """Should return error for unregistered agent."""
        result = await run_agent_for_room(
            room_id=test_room.room_id,
            agent_name="NonexistentAgent",
            trigger_message="Hello",
            session=async_session,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_run_agent_emits_event(
        self, async_session, test_room_with_agent
    ):
        """Running agent should emit room_message.agent event."""
        with patch("app.services.agent_runner.run_story_advisor") as mock_run:
            mock_run.return_value = "Test response"

            result = await run_agent_for_room(
                room_id=test_room_with_agent.room_id,
                agent_name="StoryAdvisor",
                trigger_message="Help with my story",
                session=async_session,
            )

            assert result["success"] is True
            assert result["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_should_agent_respond_active_participant(
        self, async_session, test_room_with_agent
    ):
        """Agent should respond if active participant."""
        should_respond = await should_agent_respond(
            room_id=test_room_with_agent.room_id,
            agent_name="StoryAdvisor",
            session=async_session,
        )

        assert should_respond is True

    @pytest.mark.asyncio
    async def test_should_agent_respond_not_participant(
        self, async_session, test_room
    ):
        """Agent should not respond if not participant."""
        should_respond = await should_agent_respond(
            room_id=test_room.room_id,
            agent_name="StoryAdvisor",
            session=async_session,
        )

        assert should_respond is False

    @pytest.mark.asyncio
    async def test_run_agents_for_message_triggers_all(
        self, async_session, test_room_with_multiple_agents
    ):
        """Should run all active agents in room."""
        with patch("app.services.agent_runner.run_agent_for_room") as mock_run:
            mock_run.return_value = {"success": True, "content": "Response"}

            results = await run_agents_for_message(
                room_id=test_room_with_multiple_agents.room_id,
                trigger_message="Test message",
                session=async_session,
            )

            # Should call run_agent_for_room for each agent
            assert mock_run.call_count == 2  # Assuming 2 agents in fixture
```

#### `tests/api/routes/test_rooms_with_agents.py`

```python
"""Integration tests for rooms API with agent functionality."""
import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from app.core.config import settings


class TestRoomsWithAgents:
    """Integration tests for agent features in rooms API."""

    def test_send_message_triggers_agents(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_room_with_agent,
    ):
        """Sending message should trigger agent responses."""
        with patch("app.api.routes.rooms.run_agents_for_message") as mock_run:
            mock_run.return_value = [{"success": True, "content": "Agent response"}]

            response = client.post(
                f"{settings.API_V1_STR}/rooms/{test_room_with_agent.room_id}/messages",
                headers=superuser_token_headers,
                json={"content": "Please help with my story"},
            )

            assert response.status_code == 200
            mock_run.assert_called_once()

    def test_add_agent_participant(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_room,
    ):
        """Should be able to add agent as participant."""
        response = client.post(
            f"{settings.API_V1_STR}/rooms/{test_room.room_id}/participants",
            headers=superuser_token_headers,
            json={
                "participant_id": "StoryAdvisor",
                "participant_type": "agent",
                "role": "member",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["participant_id"] == "StoryAdvisor"
        assert data["participant_type"] == "agent"

    def test_list_participants_includes_agents(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        test_room_with_agent,
    ):
        """Participant list should include agents."""
        response = client.get(
            f"{settings.API_V1_STR}/rooms/{test_room_with_agent.room_id}/participants",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        data = response.json()

        agent_participants = [
            p for p in data["data"]
            if p["participant_type"] == "agent"
        ]
        assert len(agent_participants) > 0
```

---

## Environment Configuration

Add to `.env` file:
```bash
OPENAI_API_KEY=sk-your-key-here
```

For development/testing, you can use a test API key or mock the OpenAI responses.

---

## Key Architectural Patterns

### 1. Transaction Pattern (Route-Level)
✅ **CORRECT:**
```python
@router.post("/")
async def endpoint(session: AsyncSessionTransactionDep, ...):
    await crud_function(session, ...)
    # Transaction commits on return
```

❌ **WRONG:**
```python
async def crud_function(session: AsyncSession, ...):
    async with session.begin():  # NO! Route already started transaction
        await emit_event(...)
```

### 2. Event Emission Pattern
```python
# emit_event() handles:
# 1. Write to room_events
# 2. Update projections
# 3. session.flush() for read-after-write
await emit_event(
    session=session,
    room_id=room_id,
    event_type="room_message.agent",
    payload={"agent_name": "StoryAdvisor", "content": "..."},
)
```

### 3. Agent Registration Pattern
```python
# At end of agent module:
register_agent("AgentName", agent_instance)
```

### 4. Error Handling Pattern
```python
try:
    response = await run_agent(...)
except Exception as e:
    logger.error(f"Error: {e}")
    # Still emit event with friendly error message
    await emit_event(..., payload={"content": "I encountered an error..."})
```

---

## Acceptance Criteria Summary

### Functional Requirements
- [ ] Can add StoryAdvisor as room participant via API
- [ ] Sending message in room with StoryAdvisor triggers response
- [ ] Agent response is visible to all room participants
- [ ] Agent response includes story-aware context (when story attached)
- [ ] Multiple agents can be added to one room
- [ ] All agents respond to user messages (if active participants)

### Non-Functional Requirements
- [ ] All agent operations are transactional (atomic with user message)
- [ ] All agent interactions are persisted in `room_events`
- [ ] Agent responses are replayable from event log
- [ ] Errors don't crash transactions (graceful degradation)
- [ ] Context is limited (20 messages max to prevent overflow)
- [ ] Tests achieve >80% coverage

### Integration Requirements
- [ ] Follows Phase 1 transaction patterns
- [ ] Uses existing event emitter service
- [ ] No database schema changes required
- [ ] Compatible with future Phase 4 (WebSocket streaming)

---

## Files Summary

### New Files (9 total)
1. `app/agents/agent_registry.py`
2. `app/agents/story_advisor.py`
3. `app/agents/__init__.py`
4. `app/services/context_provider.py`
5. `app/services/agent_runner.py`
6. `tests/agents/test_agent_registry.py`
7. `tests/services/test_context_provider.py`
8. `tests/services/test_agent_runner.py`
9. `tests/api/routes/test_rooms_with_agents.py`

### Modified Files (2 total)
1. `app/api/routes/rooms.py` - Add agent trigger
2. `app/main.py` - Import agents module

---

## Risk Mitigation

### Risk: OpenAI API failures crash requests
**Mitigation:** Wrap agent execution in try/except, emit friendly error message

### Risk: Context overflow (too many messages)
**Mitigation:** Limit to 20 messages by default, lightweight story outline only

### Risk: Multiple agents cause performance issues
**Mitigation:** Phase 2 executes agents synchronously; Phase 4 will add async streaming

### Risk: Agent breaks transaction
**Mitigation:** Agent runner never manages transactions, receives session from route

---

## Next Steps After Phase 2

**Phase 3:** Frontend UI
- Room components with participant list
- Message rendering with sender attribution
- Agent responses styled differently from users

**Phase 4:** Streaming & WebSocket
- Redis pub/sub fanout
- Real-time message streaming
- Agent response streaming (token-by-token)

---

## Notes for Implementation

### Critical Patterns

1. **Transaction Pattern**
   - All CRUD operations receive `session` from route handler
   - **NEVER** call `session.begin()` in services or CRUD functions
   - Routes use `AsyncSessionTransactionDep` for write operations
   - Transaction commits automatically on successful return, rolls back on exception

2. **Event Emission**
   - Always use `emit_event()` for writes - it handles:
     - Writing to `room_events` table
     - Updating projections transactionally
     - Calling `session.flush()` for read-after-write consistency
   - Never manipulate projection tables directly

3. **Agent Registration**
   - Import agent modules in `app/agents/__init__.py` to trigger registration
   - Agents self-register using `register_agent()` at module load time
   - Import agents in `app/main.py` to ensure registration at startup

4. **Error Handling**
   - Agents should **never** crash transactions
   - Wrap all agent execution in try/except
   - Return friendly error messages on failure
   - Still emit `room_message.agent` event with error content

5. **Testing**
   - Use `pytest.mark.asyncio` for async test functions
   - Mock external API calls (OpenAI) in tests
   - Clear `AGENT_REGISTRY` in test setup to avoid conflicts
   - Test fixtures should create rooms, participants, and messages as needed

6. **Context Limits**
   - Default to 20 messages to prevent context overflow
   - Story outline is lightweight (title + description only)
   - Agent tools should truncate long content (e.g., 200 char limit in summaries)

### Implementation Order

1. **Start with foundational components** (Agent Registry, Context Provider)
   - They have no dependencies
   - Can be built and tested independently

2. **Build StoryAdvisor Agent next**
   - Depends on registry and context provider
   - Provides concrete implementation to test against

3. **Build Agent Runner**
   - Depends on all above components
   - Most complex service - take time to get right

4. **Integration last**
   - Modify routes and main.py
   - Run full integration tests

5. **Test as you build**
   - Write tests immediately after each component
   - Don't wait until the end to test

---

**Ready to implement? Start with Deliverable 1 (Agent Registry) →**
