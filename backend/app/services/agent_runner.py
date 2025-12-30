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
from app.agents.dialogue_coach import run_dialogue_coach
from app.agents.plot_twist_architect import run_plot_twist_architect
from app.agents.character_forge import run_character_forge
from app.agents.symbol_weaver import run_symbol_weaver
from app.models import RoomParticipant
from app.services.context_provider import build_room_context
from app.services.event_emitter import emit_event, publish_agent_token

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

        # Run agent based on name with proper context
        if agent_name == "StoryAdvisor":
            response_content = await run_story_advisor(
                user_message=trigger_message,
                context=context,
            )
        elif agent_name == "DialogueCoach":
            response_content = await run_dialogue_coach(
                user_message=trigger_message,
                context=context,
            )
        elif agent_name == "PlotTwistArchitect":
            response_content = await run_plot_twist_architect(
                user_message=trigger_message,
                context=context,
            )
        elif agent_name == "CharacterForge":
            response_content = await run_character_forge(
                user_message=trigger_message,
                context=context,
            )
        elif agent_name == "SymbolWeaver":
            response_content = await run_symbol_weaver(
                user_message=trigger_message,
                context=context,
            )
        else:
            # Fallback for any unhandled agent
            logger.warning(f"Agent {agent_name} has no specific run function, using generic path")
            agent = get_agent(agent_name)
            result = await agent.run(trigger_message)
            response_content = result.output

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
        error_content = (
            "I encountered an error while processing your request. Please try again."
        )

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

async def run_agent_for_room_streaming(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Run an agent with token-by-token streaming.

    This is the Phase 4 enhancement of run_agent_for_room().

    Differences from non-streaming version:
    1. Uses agent.run_stream() instead of agent.run()
    2. Publishes tokens to Redis as they arrive
    3. Still emits final room_message.agent event with complete response

    Token streaming:
    - Tokens published via Redis as ephemeral message.delta events
    - NOT persisted to Postgres (only final message is persisted)
    - Clients receive tokens in real-time for progressive rendering

    Args:
        room_id: UUID of the room
        agent_name: Name of the agent to run
        trigger_message: The message that triggered the agent
        session: Async database session

    Returns:
        Dict with agent response details
    """
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

        # Run agent with streaming
        full_response = ""

        if agent_name == "StoryAdvisor":
            # StoryAdvisor with streaming
            from app.agents.story_advisor import story_advisor, StoryAdvisorDeps

            deps = StoryAdvisorDeps(context=context)

            # Build prompt with context
            conversation_context = ""
            if context.story_data:
                conversation_context += f"\nStory: {context.story_data.get('title', 'Untitled')}\n"

            if context.recent_messages:
                recent = context.recent_messages[-5:]
                conversation_context += "\nRecent messages:\n"
                for msg in recent:
                    sender = msg.get("agent_name") or "User"
                    conversation_context += f"{sender}: {msg.get('content', '')}\n"

            full_prompt = f"{conversation_context}\nUser message: {trigger_message}"

            # Stream response
            # NOTE: stream_text() yields CUMULATIVE text (full message so far), not deltas
            prev_len = 0
            async with story_advisor.run_stream(full_prompt, deps=deps) as result:
                async for chunk in result.stream_text():
                    # Extract only the new content since last iteration
                    new_content = chunk[prev_len:]
                    full_response = chunk  # Update to latest full response
                    prev_len = len(chunk)

                    # Publish only the new content to Redis
                    if new_content:
                        await publish_agent_token(
                            room_id=room_id,
                            agent_name=agent_name,
                            token=new_content,
                        )

        else:
            # Generic agent streaming
            # NOTE: stream_text() yields CUMULATIVE text (full message so far), not deltas
            agent = get_agent(agent_name)
            prev_len = 0
            async with agent.run_stream(trigger_message) as result:
                async for chunk in result.stream_text():
                    # Extract only the new content since last iteration
                    new_content = chunk[prev_len:]
                    full_response = chunk  # Update to latest full response
                    prev_len = len(chunk)

                    # Publish only the new content to Redis
                    if new_content:
                        await publish_agent_token(
                            room_id=room_id,
                            agent_name=agent_name,
                            token=new_content,
                        )

        # Emit final complete message event
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload={
                "agent_name": agent_name,
                "content": full_response,
            },
        )

        logger.info(f"Agent {agent_name} streamed response in room {room_id}")

        return {
            "agent_name": agent_name,
            "content": full_response,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Agent {agent_name} streaming error in room {room_id}: {e}")

        error_content = "I encountered an error while processing your request."

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

async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Run all active agents in a room (with streaming support) that should respond to a message.

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
            response = await run_agent_for_room_streaming(
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
