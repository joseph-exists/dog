"""
Agent Runner Service: Execute agents in room context.

This service:
1. Loads room context via ContextProvider
2. Looks up agent via database AgentConfig
3. Checks participation mode before responding
4. Runs the agent with context
5. Emits room_message.agent event with response
6. Handles errors gracefully

Participation Modes:
- "always": Agent responds to every message in the room
- "on_mention": Agent responds only when @mentioned (default)
- "manual": Agent only responds when explicitly invoked via API

Transaction Management:
- Agent runner receives session from caller
- Does NOT manage its own transaction
- Route handler controls transaction lifecycle
"""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from pydantic_ai import Agent
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentConfig, RoomParticipant
from app.services.context_provider import build_room_context
from app.services.event_emitter import emit_event, publish_agent_token

logger = logging.getLogger(__name__)


# =============================================================================
# Mention Detection
# =============================================================================

def detect_mentions(message: str) -> set[str]:
    """
    Extract @mentions from a message.

    Supports formats:
    - @AgentName (display name with spaces requires quotes or camelCase)
    - @agent-slug (slug format)
    - @"Agent Name" (quoted for names with spaces)

    Returns:
        Set of mentioned names/slugs (lowercase for case-insensitive matching)
    """
    mentions = set()

    # Pattern 1: @"Quoted Name" - names with spaces
    quoted_pattern = r'@"([^"]+)"'
    for match in re.finditer(quoted_pattern, message):
        mentions.add(match.group(1).lower())

    # Pattern 2: @word - simple mentions (alphanumeric, hyphens, underscores)
    # Must not be inside quotes
    simple_pattern = r'@(\w[\w-]*)'
    for match in re.finditer(simple_pattern, message):
        mentions.add(match.group(1).lower())

    return mentions


def is_agent_mentioned(
    message: str,
    agent_slug: str,
    agent_name: str,
) -> bool:
    """
    Check if an agent is mentioned in a message.

    Matches against:
    - Agent slug (e.g., "StoryAdvisor", "story-advisor")
    - Agent display name (e.g., "Story Advisor")

    Case-insensitive matching.
    """
    mentions = detect_mentions(message)

    if not mentions:
        return False

    # Check slug match
    if agent_slug.lower() in mentions:
        return True

    # Check display name match (with and without spaces)
    if agent_name.lower() in mentions:
        return True

    # Check display name without spaces (camelCase mention)
    name_no_spaces = agent_name.replace(" ", "").lower()
    if name_no_spaces in mentions:
        return True

    return False


# =============================================================================
# Agent Resolution and Instantiation
# =============================================================================

async def get_agent_config(session: AsyncSession, slug: str) -> AgentConfig | None:
    """
    Get agent configuration from database by slug.
    """
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == slug)
    )
    return result.scalar_one_or_none()


async def get_agent_instance(session: AsyncSession, slug: str) -> Agent[Any, Any] | None:
    """
    Get agent instance from database AgentConfig.

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Uses the model_name and system_prompt from AgentConfig.
    """
    config = await get_agent_config(session, slug)

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
) -> tuple[str | None, str | None, AgentConfig | None]:
    """
    Resolve a participant_id to an agent slug, display name, and config.

    participant_id can be either:
    - A UUID string (database agent ID - the standard case)
    - An agent slug (for direct lookups)

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        Tuple of (agent_slug, display_name, config) or (None, None, None) if not found.
        - agent_slug: Used for registry lookups and running the agent
        - display_name: Used for message attribution (agent's name field)
        - config: Full AgentConfig for participation mode checks
    """
    # First, try to parse as UUID (database-registered agent)
    try:
        agent_uuid = uuid.UUID(participant_id)
        agent_config = await session.get(AgentConfig, agent_uuid)

        if agent_config and agent_config.is_enabled:
            logger.debug(f"Resolved UUID {participant_id} to agent slug: {agent_config.slug}")
            return agent_config.slug, agent_config.name, agent_config

        logger.warning(f"Agent UUID {participant_id} not found or disabled in database")
        return None, None, None

    except ValueError:
        # Not a valid UUID, treat as agent slug
        pass

    # Check database registry by slug
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == participant_id)
    )
    agent_config = result.scalar_one_or_none()

    if agent_config and agent_config.is_enabled:
        logger.debug(f"Found database agent by slug: {participant_id}")
        return agent_config.slug, agent_config.name, agent_config

    logger.warning(f"Agent '{participant_id}' not found in database")
    return None, None, None


async def is_agent_available(session: AsyncSession, participant_id: str) -> bool:
    """
    Check if an agent is available in the database.

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        True if agent can be run, False otherwise
    """
    slug, _, _ = await resolve_agent_identifier(session, participant_id)
    return slug is not None


# =============================================================================
# Participation Mode Logic
# =============================================================================

def should_agent_respond_to_message(
    config: AgentConfig,
    trigger_message: str,
) -> tuple[bool, str]:
    """
    Determine if an agent should respond based on participation mode.

    Args:
        config: Agent configuration with participation_mode
        trigger_message: The message that triggered the check

    Returns:
        Tuple of (should_respond, reason)
    """
    mode = config.participation_mode or "on_mention"

    if mode == "always":
        return True, "mode=always"

    if mode == "manual":
        # Manual agents never auto-respond; they must be explicitly invoked
        return False, "mode=manual (requires explicit invocation)"

    if mode == "on_mention":
        # Check for @mention
        if is_agent_mentioned(trigger_message, config.slug, config.name):
            return True, "mentioned in message"
        return False, "not mentioned (mode=on_mention)"

    # Unknown mode - default to not responding
    logger.warning(f"Unknown participation mode '{mode}' for agent {config.slug}")
    return False, f"unknown mode '{mode}'"


# =============================================================================
# Prompt Building
# =============================================================================

def build_agent_prompt(trigger_message: str, context: Any) -> str:
    """
    Build the full prompt for an agent including room context.

    Args:
        trigger_message: The user's message that triggered the agent
        context: RoomContext from context_provider

    Returns:
        Full prompt string with context prepended
    """
    conversation_context = ""

    # Add story context if available
    if context.story_data:
        conversation_context += f"\nStory: {context.story_data.get('title', 'Untitled')}\n"
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    # Add recent messages for conversation continuity
    if context.recent_messages:
        recent = context.recent_messages[-5:]
        conversation_context += "\nRecent conversation:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    # Combine context with user message
    if conversation_context:
        return f"{conversation_context}\nUser message: {trigger_message}"
    return trigger_message


# =============================================================================
# Agent Execution
# =============================================================================

async def run_agent_for_room(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Run an agent in a room context and emit its response as an event.

    This is the main entry point for agent execution (non-streaming). It:
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
    # Validate agent exists
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

        # Get agent instance
        agent = await get_agent_instance(session, agent_name)
        if not agent:
            return {
                "agent_name": agent_name,
                "content": "",
                "success": False,
                "error": f"Failed to instantiate agent '{agent_name}'",
            }

        # Build prompt with context
        full_prompt = build_agent_prompt(trigger_message, context)

        # Run agent
        result = await agent.run(full_prompt)
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
    For participation mode checks, use should_agent_respond_to_message().

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
    # Check agent availability
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

        # Get agent instance
        agent = await get_agent_instance(session, agent_name)
        if not agent:
            return {
                "agent_name": agent_name,
                "content": "",
                "success": False,
                "error": f"Failed to instantiate agent '{agent_name}'",
            }

        # Build prompt with context
        full_prompt = build_agent_prompt(trigger_message, context)

        # Run agent with streaming
        # NOTE: stream_text() yields CUMULATIVE text (full message so far), not deltas
        full_response = ""
        prev_len = 0

        async with agent.run_stream(full_prompt) as result:
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


# =============================================================================
# High-Level Entry Point
# =============================================================================

async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Run agents in a room that should respond to a message based on participation mode.

    This is the high-level function called from route handlers.
    It checks which agents are active in the room and respects their participation modes:
    - "always": Agent responds to every message
    - "on_mention": Agent responds only when @mentioned
    - "manual": Agent does not auto-respond (must be explicitly invoked)

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

        # Resolve participant_id to agent slug and config
        agent_slug, display_name, config = await resolve_agent_identifier(
            session, participant_id
        )

        if not agent_slug or not config:
            logger.warning(
                f"Agent participant '{participant_id}' in room {room_id} "
                f"could not be resolved to a registered agent"
            )
            continue

        # Check participation mode
        should_respond, reason = should_agent_respond_to_message(config, trigger_message)

        if not should_respond:
            logger.debug(
                f"Agent '{display_name}' skipped in room {room_id}: {reason}"
            )
            continue

        logger.info(
            f"Running agent '{display_name}' (slug: {agent_slug}) "
            f"in room {room_id} ({reason})"
        )

        response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=agent_slug,
            trigger_message=trigger_message,
            session=session,
        )
        responses.append(response)

    return responses


async def invoke_agent_manually(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Explicitly invoke an agent regardless of participation mode.

    Use this for:
    - Manual mode agents that need explicit invocation
    - Testing/debugging agents
    - Admin-triggered agent responses

    Args:
        room_id: UUID of the room
        agent_slug: Slug of the agent to invoke
        trigger_message: The message/prompt for the agent
        session: Async database session

    Returns:
        Agent response dict
    """
    # Verify agent exists and is in the room
    slug, display_name, config = await resolve_agent_identifier(session, agent_slug)

    if not slug or not config:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_slug}' not found",
        }

    # Check if agent is participant in room
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.participant_id.in_([agent_slug, str(config.id)]),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Agent '{display_name}' is not a participant in this room",
        }

    logger.info(
        f"Manually invoking agent '{display_name}' (slug: {slug}) "
        f"in room {room_id}"
    )

    return await run_agent_for_room_streaming(
        room_id=room_id,
        agent_name=slug,
        trigger_message=trigger_message,
        session=session,
    )
