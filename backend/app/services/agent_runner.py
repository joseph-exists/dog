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

from pydantic_ai import Agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.agent_registry import get_agent as legacy_get_agent
from app.agents.agent_registry import is_agent_registered
from app.agents.character_forge import run_character_forge
from app.agents.dialogue_coach import run_dialogue_coach
from app.agents.plot_twist_architect import run_plot_twist_architect
from app.agents.story_advisor import run_story_advisor
from app.agents.symbol_weaver import run_symbol_weaver
from app.models import RoomParticipant
from app.services.context_provider import build_room_context
from app.services.event_emitter import emit_event, publish_agent_token

logger = logging.getLogger(__name__)

async def get_agent_instance(session: AsyncSession, slug: str) -> Agent[Any, Any] | None:
    """
    Get agent instance, with fallback to legacy registry during transition.

    Supports both:
    - Database-registered agents (loaded from AgentConfig)
    - Legacy in-memory agents (from AGENT_REGISTRY)
    """
    # First, try legacy registry (these are pre-configured agents)
    if is_agent_registered(slug):
        try:
            return legacy_get_agent(slug)
        except KeyError:
            pass

    # Try database registry - load config and instantiate agent
    from app.models import AgentConfig

    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == slug)
    )
    config = result.scalar_one_or_none()

    if config and config.is_enabled:
        # Instantiate PydanticAI Agent from database config
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"
        agent = Agent(config.model_name, system_prompt=system_prompt)
        logger.debug(f"Instantiated database agent: {config.slug} with model {config.model_name}")
        return agent

    return None


async def resolve_agent_identifier(
    session: AsyncSession,
    participant_id: str,
) -> tuple[str | None, str | None]:
    """
    Resolve a participant_id to an agent slug and display name.

    During the transition from legacy to database-backed agents, participant_id
    can be either:
    - A UUID string (database agent ID)
    - An agent slug/name (legacy agent)

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        Tuple of (agent_slug, display_name) or (None, None) if not found.
        - agent_slug: Used for registry lookups and running the agent
        - display_name: Used for message attribution (agent's name field)
    """
    # First, try to parse as UUID (database-registered agent)
    try:
        agent_uuid = uuid.UUID(participant_id)
        # Look up agent config by ID using async session
        from app.models import AgentConfig

        agent_config = await session.get(AgentConfig, agent_uuid)

        if agent_config and agent_config.is_enabled:
            logger.debug(f"Resolved UUID {participant_id} to agent slug: {agent_config.slug}")
            return agent_config.slug, agent_config.name

        logger.warning(f"Agent UUID {participant_id} not found or disabled in database")
        return None, None

    except ValueError:
        # Not a valid UUID, treat as legacy agent name/slug
        pass

    # Check legacy registry
    if is_agent_registered(participant_id):
        logger.debug(f"Found legacy agent: {participant_id}")
        return participant_id, participant_id

    # Check database registry by slug (in case slug was passed directly)
    from app.models import AgentConfig

    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == participant_id)
    )
    agent_config = result.scalar_one_or_none()

    if agent_config and agent_config.is_enabled:
        logger.debug(f"Found database agent by slug: {participant_id}")
        return agent_config.slug, agent_config.name

    logger.warning(f"Agent '{participant_id}' not found in any registry")
    return None, None


async def is_agent_available(session: AsyncSession, participant_id: str) -> bool:
    """
    Check if an agent is available (either in database or legacy registry).

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        True if agent can be run, False otherwise
    """
    slug, _ = await resolve_agent_identifier(session, participant_id)
    return slug is not None


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
        agent_name: Name/slug of the agent to run (e.g., "StoryAdvisor")
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
    # Validate agent exists (checks both legacy and database registries)
    if not await is_agent_available(session, agent_name):
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
            agent = await get_agent_instance(session, agent_name)
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
        agent_name: Name/slug of the agent to run
        trigger_message: The message that triggered the agent
        session: Async database session

    Returns:
        Dict with agent response details
    """
    # Check both legacy registry and database registry
    if not await is_agent_available(session, agent_name):
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
            from app.agents.story_advisor import StoryAdvisorDeps, story_advisor

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
            agent = await get_agent_instance(session, agent_name)
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

    Supports both:
    - Database-registered agents (participant_id is UUID)
    - Legacy agents (participant_id is agent name/slug)

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
        participant_id = participant.participant_id

        # Resolve participant_id to agent slug (handles both UUID and legacy names)
        agent_slug, display_name = await resolve_agent_identifier(session, participant_id)

        if agent_slug:
            logger.info(
                f"Running agent '{display_name}' (slug: {agent_slug}) "
                f"in room {room_id}"
            )
            response = await run_agent_for_room_streaming(
                room_id=room_id,
                agent_name=agent_slug,
                trigger_message=trigger_message,
                session=session,
            )
            responses.append(response)
        else:
            logger.warning(
                f"Agent participant '{participant_id}' in room {room_id} "
                f"could not be resolved to a registered agent"
            )

    return responses
