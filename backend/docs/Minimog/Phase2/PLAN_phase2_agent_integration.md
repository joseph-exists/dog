# Phase 2 Implementation Plan: Agent Integration

## Goal

Make agents first-class room participants and run them with room-aware context. Agent responses are visible to all participants, include story-aware context, and are persisted and replayable from events.

---

## Analysis Summary

### Phase 1 Status (Complete)
- `room_events` table: Append-only event log with `room_sequence` ordering
- `rooms` table: Projection with `room_id`, `creator_id`, `title`, `story_id`, `last_activity`
- `room_participants` table: Tracks users and agents with `participant_type`, `role`, `active`
- `room_messages` table: Message projection with `sender_type` ("user" or "agent"), `sender_id`, `agent_name`
- Event emitter service: `emit_event()` with transactional projection updates
- Route-level transactions: `AsyncSessionTransactionDep` pattern for write operations
- CRUD functions: Transaction-agnostic, receive session from route handlers

### Key Integration Points
1. **Routes** (`/home/josep/dog/backend/app/api/routes/rooms.py`):
   - `POST /rooms/{room_id}/messages` - Send message (needs agent trigger)
   - `POST /rooms/{room_id}/participants` - Add participant (agent registration)

2. **Event Emitter** (`/home/josep/dog/backend/app/services/event_emitter.py`):
   - `room_message.agent` event type already supported
   - Projection handler `_handle_room_message_agent()` exists

3. **Models** (`/home/josep/dog/backend/app/models.py`):
   - `RoomMessage.agent_name` field for agent identification
   - `RoomParticipant.participant_type` supports "agent"

---

## Deliverables

### 1. Context Provider Service
**File:** `/home/josep/dog/backend/app/services/context_provider.py`

**Purpose:** Build room-aware context for agents, loading recent messages and story data.

**Implementation:**

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

**Dependencies:** None (foundational component)

---

### 2. Agent Registry
**File:** `/home/josep/dog/backend/app/agents/agent_registry.py`

**Purpose:** Central registry for managing available agents. Decouples agent lookup from hardcoded references.

**Implementation:**

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

**Dependencies:** None (foundational component)

---

### 3. StoryAdvisor Agent
**File:** `/home/josep/dog/backend/app/agents/story_advisor.py`

**Purpose:** The primary agent for story-related assistance. Demonstrates the agent pattern with tools and room-aware context.

**Implementation:**

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

**Dependencies:**
- Agent Registry (for registration)
- Context Provider (for RoomContext type)

---

### 4. Agent Runner Service
**File:** `/home/josep/dog/backend/app/services/agent_runner.py`

**Purpose:** Execute agents in room context and emit agent message events.

**Implementation:**

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

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_registry import get_agent, is_agent_registered
from app.agents.story_advisor import run_story_advisor
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
    from sqlalchemy import select
    from app.models import RoomParticipant

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
    from sqlalchemy import select
    from app.models import RoomParticipant

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

**Dependencies:**
- Agent Registry
- Context Provider
- Event Emitter
- StoryAdvisor agent

---

### 5. Route Integration
**File:** `/home/josep/dog/backend/app/api/routes/rooms.py` (modify existing)

**Purpose:** Integrate agent execution with message sending endpoint.

**Changes Required:**

```python
# Add import at top of file
from app.services.agent_runner import run_agents_for_message

# Modify send_message endpoint:

@router.post("/{room_id}/messages", response_model=RoomMessagePublic)
async def send_message(
    *,
    room_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    message_in: RoomMessageSend,
) -> Any:
    """
    Send a message to a room.

    Transaction automatically managed. Emits message.user event.
    After user message is persisted, triggers any active agents in the room.

    Agent responses are emitted as separate room_message.agent events within
    the same transaction, ensuring atomicity.
    """
    # Send user message
    room_message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,
    )

    # Trigger agents (within same transaction)
    await run_agents_for_message(
        room_id=room_id,
        trigger_message=message_in.content,
        session=session,
    )

    return room_message
```

**Dependencies:**
- Agent Runner service

---

### 6. Agent Initialization
**File:** `/home/josep/dog/backend/app/agents/__init__.py`

**Purpose:** Ensure agents are registered when the module is imported.

**Implementation:**

```python
"""
Agent module initialization.

Imports agent modules to trigger registration with the global registry.
Add new agents here to ensure they're available at startup.
"""

# Import agents to trigger registration
from app.agents import story_advisor  # noqa: F401

# Future agents:
# from app.agents import character_helper  # noqa: F401
# from app.agents import plot_assistant  # noqa: F401
```

**Dependencies:** All agent modules

---

### 7. Main Application Integration
**File:** `/home/josep/dog/backend/app/main.py` (modify existing)

**Purpose:** Import agents module at startup to ensure registration.

**Changes Required:**

```python
# Add near top of file, after other imports:

# Initialize agent registry
import app.agents  # noqa: F401
```

---

## Testing Strategy

### Test File: `/home/josep/dog/backend/app/tests/services/test_context_provider.py`

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

### Test File: `/home/josep/dog/backend/app/tests/agents/test_agent_registry.py`

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

### Test File: `/home/josep/dog/backend/app/tests/services/test_agent_runner.py`

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

### Test File: `/home/Josep/dog/backend/app/tests/api/routes/test_rooms_with_agents.py`

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

## Implementation Order (Dependencies)

```
Phase 2 Implementation Order:

1. Agent Registry (no dependencies)
   /home/josep/dog/backend/app/agents/agent_registry.py

2. Context Provider (no dependencies)
   /home/josep/dog/backend/app/services/context_provider.py

3. StoryAdvisor Agent (depends on: Agent Registry, Context Provider)
   /home/josep/dog/backend/app/agents/story_advisor.py

4. Agent Runner Service (depends on: all above)
   /home/josep/dog/backend/app/services/agent_runner.py

5. Agent Module Init (depends on: StoryAdvisor)
   /home/josep/dog/backend/app/agents/__init__.py

6. Route Integration (depends on: Agent Runner)
   Modify: /home/josep/dog/backend/app/api/routes/rooms.py

7. Main App Init (depends on: Agent Module)
   Modify: /home/josep/dog/backend/app/main.py

8. Tests (run after each component)
   /home/josep/dog/backend/app/tests/agents/
   /home/josep/dog/backend/app/tests/services/
```

---

## Acceptance Criteria

### 1. Context Provider
- [ ] `build_room_context()` returns `RoomContext` with all fields populated
- [ ] Room without story returns `story_data=None`
- [ ] Message limit is respected (default 20)
- [ ] Messages are in chronological order
- [ ] Only active participants are included
- [ ] Non-existent room raises `ValueError`

### 2. Agent Registry
- [ ] `register_agent()` adds agent to registry
- [ ] `register_agent()` raises on duplicate name
- [ ] `get_agent()` returns registered agent
- [ ] `get_agent()` raises on unknown name
- [ ] `list_agents()` returns all registered names
- [ ] `is_agent_registered()` returns correct status

### 3. StoryAdvisor Agent
- [ ] Agent is registered as "StoryAdvisor" on import
- [ ] `get_story_outline` tool returns story data when available
- [ ] `get_conversation_summary` tool summarizes recent messages
- [ ] `get_room_participants` tool lists participants
- [ ] `run_story_advisor()` returns response string
- [ ] Errors are handled gracefully with user-friendly message

### 4. Agent Runner
- [ ] `run_agent_for_room()` validates agent exists
- [ ] `run_agent_for_room()` emits `room_message.agent` event
- [ ] `run_agent_for_room()` returns success/error dict
- [ ] `should_agent_respond()` checks participant status
- [ ] `run_agents_for_message()` triggers all active agents
- [ ] Errors don't crash transaction (graceful handling)

### 5. Route Integration
- [ ] `POST /rooms/{room_id}/messages` triggers agents after user message
- [ ] Agent messages appear in message list
- [ ] Agent messages have correct `sender_type="agent"` and `agent_name`
- [ ] Transaction includes both user message and agent responses

### 6. End-to-End
- [ ] Can add StoryAdvisor as room participant
- [ ] Sending message in room with StoryAdvisor triggers response
- [ ] Agent response is visible to all participants
- [ ] Agent response is persisted (survives reload)
- [ ] Multiple agents can respond in same room
- [ ] All agent responses are replayable from events

---

## Files Summary

### New Files to Create
1. `/home/josep/dog/backend/app/services/context_provider.py`
2. `/home/josep/dog/backend/app/agents/agent_registry.py`
3. `/home/josep/dog/backend/app/agents/story_advisor.py`
4. `/home/josep/dog/backend/app/services/agent_runner.py`
5. `/home/josep/dog/backend/app/agents/__init__.py`
6. `/home/josep/dog/backend/app/tests/services/test_context_provider.py`
7. `/home/josep/dog/backend/app/tests/agents/test_agent_registry.py`
8. `/home/josep/dog/backend/app/tests/services/test_agent_runner.py`
9. `/home/josep/dog/backend/app/tests/api/routes/test_rooms_with_agents.py`

### Files to Modify
1. `/home/josep/dog/backend/app/api/routes/rooms.py` - Add agent trigger
2. `/home/josep/dog/backend/app/main.py` - Import agents module

---

## Environment Requirements

Ensure the following environment variable is set:
```bash
OPENAI_API_KEY=sk-your-key-here
```

This can be added to `.env` file or set directly in the environment.

---

## Notes for Worker Agents

1. **Transaction Pattern**: All CRUD operations receive `session` from route. Do NOT call `session.begin()` in services.

2. **Event Emission**: Always use `emit_event()` for writes. It handles projections and `flush()`.

3. **Agent Registration**: Import agent modules in `__init__.py` to trigger registration.

4. **Error Handling**: Agents should never crash the transaction. Wrap in try/except and return friendly error.

5. **Testing**: Use `pytest.mark.asyncio` for async tests. Mock external API calls (OpenAI).

6. **Context Limits**: Default to 20 messages to prevent context overflow. Story outline is lightweight.
