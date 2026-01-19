"""
Agent Runner Service: Execute agents in room context.

This service:
1. Loads room context via ContextProvider
2. Looks up agent via database AgentConfig
3. Checks participation mode before responding
4. Runs the agent with context
5. Emits room_message.agent event with response
6. Handles errors gracefully
7. Supports Coordinator Pattern for agent orchestration

Participation Modes:
- "always": Agent responds to every message in the room
- "on_mention": Agent responds only when @mentioned (default)
- "manual": Agent only responds when explicitly invoked via API

Coordinator Pattern:
- Agents with is_coordinator=True run FIRST, before participation mode checks
- Coordinators can analyze user intent and @mention specialists
- This enables orchestration where a primary agent routes to others
- Only one coordinator per room is typical, but multiple are allowed

Transaction Management:
- Agent runner receives session from caller
- Does NOT manage its own transaction
- Route handler controls transaction lifecycle
"""

from __future__ import annotations

import logging
import uuid
from typing import Any

from dataclasses import asdict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    RoomParticipant,
)
from app.services.a2a_orchestrator import A2AOrchestrator, DEFAULT_MAX_A2A_DEPTH
from app.services.agent_context import RoomContextService
from app.services.agent_events import AgentEventPublisher
from app.services.agent_instance import get_agent_instance, get_agent_instance_with_tools
from app.services.agent_prompt import build_agent_prompt
from app.services.agent_selection import AgentSelectionService
from app.services.agent_runner_non_streaming import NonStreamingAgentRunner
from app.services.agent_runner_streaming import StreamingAgentRunner
from app.services.agent_runner_types import AgentRunRequest
from app.services.agent_tools import AgentDeps, emit_ui_component, request_agent_assistance

logger = logging.getLogger(__name__)

# Service singletons (thin wrappers for future modularization)
_context_service = RoomContextService()
_event_publisher = AgentEventPublisher()
_selection_service = AgentSelectionService()
_a2a_orchestrator = A2AOrchestrator(max_depth=DEFAULT_MAX_A2A_DEPTH)


def _make_agent_deps(
    session: AsyncSession,
    room_id: uuid.UUID,
    agent_slug: str,
    a2a_depth: int,
) -> AgentDeps:
    return AgentDeps(
        session=session,
        room_id=room_id,
        current_agent_slug=agent_slug,
        a2a_depth=a2a_depth,
    )


_streaming_runner: StreamingAgentRunner | None = None
_non_streaming_runner: NonStreamingAgentRunner | None = None


def _get_streaming_runner() -> StreamingAgentRunner:
    global _streaming_runner
    if _streaming_runner is None:
        _streaming_runner = StreamingAgentRunner(
            context_service=_context_service,
            event_publisher=_event_publisher,
            is_agent_available=_selection_service.is_agent_available,
            get_agent_instance_with_tools=get_agent_instance_with_tools,
            build_agent_prompt=build_agent_prompt,
            deps_factory=_make_agent_deps,
            a2a_orchestrator=_a2a_orchestrator,
            run_agent=_run_agent_for_a2a,
        )
    return _streaming_runner


def _get_non_streaming_runner() -> NonStreamingAgentRunner:
    global _non_streaming_runner
    if _non_streaming_runner is None:
        _non_streaming_runner = NonStreamingAgentRunner(
            context_service=_context_service,
            event_publisher=_event_publisher,
            is_agent_available=_selection_service.is_agent_available,
            get_agent_instance=get_agent_instance,
            build_agent_prompt=build_agent_prompt,
        )
    return _non_streaming_runner


async def _run_agent_for_a2a(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
    a2a_depth: int = 0,
) -> dict[str, Any]:
    result = await _get_streaming_runner().run(
        req=AgentRunRequest(
            room_id=room_id,
            agent_slug=agent_name,
            trigger_message=trigger_message,
            a2a_depth=a2a_depth,
        ),
        session=session,
    )
    return asdict(result)



# =============================================================================
# Agent Resolution and Instantiation
# =============================================================================




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
    result = await _get_non_streaming_runner().run(
        req=AgentRunRequest(
            room_id=room_id,
            agent_slug=agent_name,
            trigger_message=trigger_message,
        ),
        session=session,
    )
    return asdict(result)


async def should_agent_respond(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    session: AsyncSession,
) -> bool:
    """
    Check if an agent should respond to a message.

    Currently checks if the agent is an active participant in the room.
    For participation mode checks, use AgentSelectionService.should_agent_respond_to_message().

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
    user_id: uuid.UUID | None = None,
    a2a_depth: int = 0,
) -> dict[str, Any]:
    """
    Run an agent with token-by-token streaming and A2A support.

    Differences from non-streaming version:
    1. Uses agent.run_stream() instead of agent.run()
    2. Publishes tokens to Redis as they arrive
    3. Still emits final room_message.agent event with complete response
    4. Processes @mentions in response to trigger other agents (A2A)

    Token streaming:
    - Tokens published via Redis as ephemeral message.delta events
    - NOT persisted to Postgres (only final message is persisted)
    - Clients receive tokens in real-time for progressive rendering

    A2A (Agent-to-Agent):
    - After response, detects @mentions of other agents
    - Triggers mentioned agents if they're in the room
    - Respects the configured A2A depth limit to prevent infinite loops

    Args:
        room_id: UUID of the room
        agent_name: Name/slug of the agent to run
        trigger_message: The message that triggered the agent
        session: Async database session
        user_id: User ID for resolving API credentials (None = use env vars)
        a2a_depth: Current depth in A2A chain (0 = user-triggered, default)

    Returns:
        Dict with agent response details
    """
    result = await _get_streaming_runner().run(
        req=AgentRunRequest(
            room_id=room_id,
            agent_slug=agent_name,
            trigger_message=trigger_message,
            user_id=user_id,
            a2a_depth=a2a_depth,
        ),
        session=session,
    )
    return asdict(result)


# =============================================================================
# High-Level Entry Point
# =============================================================================

async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """
    Run agents in a room that should respond to a message based on participation mode.

    This is the high-level function called from route handlers.

    Execution order:
    1. Coordinator agents run FIRST (regardless of participation mode)
       - Coordinators can analyze intent and @mention specialists
       - Only one coordinator typically, but multiple are allowed
    2. Regular agents run based on their participation modes:
       - "always": Agent responds to every message
       - "on_mention": Agent responds only when @mentioned
       - "manual": Agent does not auto-respond (must be explicitly invoked)

    The Coordinator Pattern enables orchestration where a primary agent
    routes to specialists based on message content.

    Args:
        room_id: UUID of the room
        trigger_message: The message that triggered agents
        session: Async database session (transaction managed by caller)
        user_id: User ID for resolving API credentials (None = use env vars)

    Returns:
        List of agent response dicts (one per agent that ran)
    """
    coordinators, regular_agents = await _selection_service.select_agents_for_message(
        session=session,
        room_id=room_id,
        trigger_message=trigger_message,
    )

    responses = []

    # Phase 1: Run coordinator agents first (bypass participation mode)
    for agent_slug, display_name, _config in coordinators:
        logger.info(
            f"Running coordinator agent '{display_name}' (slug: {agent_slug}) "
            f"in room {room_id}"
        )

        response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=agent_slug,
            trigger_message=trigger_message,
            session=session,
            user_id=user_id,
        )
        responses.append(response)

    # Phase 2: Run regular agents based on participation mode
    for agent_slug, display_name, config, _ in regular_agents:
        # Check participation mode
        should_respond, reason = _selection_service.should_agent_respond_to_message(
            config=config,
            trigger_message=trigger_message,
        )

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
            user_id=user_id,
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
    slug, display_name, config = await _selection_service.resolve_agent_identifier(
        session=session,
        participant_id=agent_slug,
    )

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
