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

from app.services.logfire_client import ServiceLogfire

from dataclasses import asdict
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

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

SERVICE_ID = "agent_runner"
logfire = ServiceLogfire(SERVICE_ID)

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


def _uuid_to_str(value: uuid.UUID | None) -> str | None:
    return str(value) if value else None


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
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    result = await _get_streaming_runner().run(
        req=AgentRunRequest(
            room_id=room_id,
            agent_slug=agent_name,
            trigger_message=trigger_message,
            a2a_depth=a2a_depth,
            user_id=user_id,
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
    room_id_str = str(room_id)
    span_tags = {
        "room_id": room_id_str,
        "agent_name": agent_name,
    }

    with logfire.span("agent.run_agent_for_room", **span_tags):
        logfire.info("agent.run_requested", **span_tags)
        result = await _get_non_streaming_runner().run(
            req=AgentRunRequest(
                room_id=room_id,
                agent_slug=agent_name,
                trigger_message=trigger_message,
            ),
            session=session,
        )
        serialized = asdict(result)
        logfire.info(
            "agent.run_completed",
            **span_tags,
            success=serialized.get("success"),
        )
        return serialized


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
    # NOTE: SQLModel annotates columns (e.g., `RoomParticipant.active`) as plain
    # Python types like `bool`, which can confuse static type checkers (pyright)
    # into thinking we're passing a `bool` into `where(...)`. Using table columns
    # avoids that and also makes the generated SQL explicit.
    rp = RoomParticipant.__table__.c
    result = await session.exec(
        select(RoomParticipant).where(
            rp.room_id == room_id,
            rp.participant_type == "agent",
            rp.participant_id == agent_name,
            rp.active.is_(True),
        )
    )
    participant_row = result.one_or_none()
    participant = (
        participant_row[0]
        if participant_row and not isinstance(participant_row, RoomParticipant)
        else participant_row
    )

    return participant is not None


async def run_agent_for_room_streaming(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    a2a_depth: int = 0,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
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
    room_id_str = str(room_id)
    user_id_str = _uuid_to_str(user_id)
    span_tags = {
        "room_id": room_id_str,
        "agent_name": agent_name,
        "user_id": user_id_str,
        "a2a_depth": a2a_depth,
        "a2a_tool_enabled": enable_a2a_tool,
        "ag_ui_tool_enabled": enable_ag_ui_tool,
    }

    with logfire.span("agent.run_agent_for_room_streaming", **span_tags):
        logfire.info("agent.run_requested", **span_tags)
        result = await _get_streaming_runner().run(
            req=AgentRunRequest(
                room_id=room_id,
                agent_slug=agent_name,
                trigger_message=trigger_message,
                user_id=user_id,
                a2a_depth=a2a_depth,
                enable_a2a_tool=enable_a2a_tool,
                enable_ag_ui_tool=enable_ag_ui_tool,
            ),
            session=session,
        )
        serialized = asdict(result)
        logfire.info(
            "agent.run_completed",
            **span_tags,
            success=serialized.get("success"),
        )
        return serialized


# =============================================================================
# High-Level Entry Point
# =============================================================================

async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
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
    room_id_str = str(room_id)
    user_id_str = _uuid_to_str(user_id)
    span_tags = {
        "room_id": room_id_str,
        "user_id": user_id_str,
        "trigger_length": len(trigger_message),
        "a2a_tool_enabled": enable_a2a_tool,
        "ag_ui_tool_enabled": enable_ag_ui_tool,
    }

    with logfire.span("agent.run_agents_for_message", **span_tags):
        logfire.info("agent.run_agents_started", **span_tags)
        coordinators, regular_agents = await _selection_service.select_agents_for_message(
            session=session,
            room_id=room_id,
            trigger_message=trigger_message,
        )

        responses: list[dict[str, Any]] = []

        # Phase 1: Run coordinator agents first (bypass participation mode)
        for agent_slug, display_name, _config in coordinators:
            agent_tags = {
                **span_tags,
                "agent_slug": agent_slug,
                "agent_display_name": display_name,
                "phase": "coordinator",
            }
            logger.info(
                f"Running coordinator agent '{display_name}' (slug: {agent_slug}) "
                f"in room {room_id}"
            )
            logfire.info("agent.phase_start", **agent_tags)
            with logfire.span("agent.run_coordinator", **agent_tags):
                response = await run_agent_for_room_streaming(
                    room_id=room_id,
                    agent_name=agent_slug,
                    trigger_message=trigger_message,
                    session=session,
                    user_id=user_id,
                    enable_a2a_tool=enable_a2a_tool,
                    enable_ag_ui_tool=enable_ag_ui_tool,
                )
            logfire.info(
                "agent.phase_completed",
                **agent_tags,
                success=response.get("success"),
            )
            responses.append(response)

        # Phase 2: Run regular agents based on participation mode
        for agent_slug, display_name, config, _ in regular_agents:
            should_respond, reason = _selection_service.should_agent_respond_to_message(
                config=config,
                trigger_message=trigger_message,
            )

            if not should_respond:
                logger.debug(
                    f"Agent '{display_name}' skipped in room {room_id}: {reason}"
                )
                logfire.info(
                    "agent.skipped",
                    **span_tags,
                    agent_slug=agent_slug,
                    agent_display_name=display_name,
                    reason=reason,
                )
                continue

            agent_tags = {
                **span_tags,
                "agent_slug": agent_slug,
                "agent_display_name": display_name,
                "phase": "regular",
                "reason": reason,
            }
            logger.info(
                f"Running agent '{display_name}' (slug: {agent_slug}) "
                f"in room {room_id} ({reason})"
            )
            logfire.info("agent.phase_start", **agent_tags)
            with logfire.span("agent.run_regular", **agent_tags):
                response = await run_agent_for_room_streaming(
                    room_id=room_id,
                    agent_name=agent_slug,
                    trigger_message=trigger_message,
                    session=session,
                    user_id=user_id,
                    enable_a2a_tool=enable_a2a_tool,
                    enable_ag_ui_tool=enable_ag_ui_tool,
                )
            logfire.info(
                "agent.phase_completed",
                **agent_tags,
                success=response.get("success"),
            )
            responses.append(response)

        logfire.info(
            "agent.run_agents_completed",
            **span_tags,
            total_responses=len(responses),
        )
        return responses


async def invoke_agent_manually(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
) -> dict[str, Any]:
    """
    Explicitly invoke an agent regardless of participation mode.

    Use this for:
    - Manual mode agents that need explicit invocation
    - UI action button responses
    - Testing/debugging agents
    - Admin-triggered agent responses

    Args:
        room_id: UUID of the room
        agent_slug: Slug of the agent to invoke
        trigger_message: The message/prompt for the agent
        session: Async database session
        user_id: User ID for resolving API credentials (None = use env vars)

    Returns:
        Agent response dict
    """
    room_id_str = str(room_id)
    user_id_str = _uuid_to_str(user_id)
    span_tags = {
        "room_id": room_id_str,
        "agent_slug": agent_slug,
        "user_id": user_id_str,
        "a2a_tool_enabled": enable_a2a_tool,
        "ag_ui_tool_enabled": enable_ag_ui_tool,
    }

    with logfire.span("agent.invoke_manually", **span_tags):
        logfire.info("agent.invoke_requested", **span_tags)
        # Verify agent exists and is in the room
        slug, display_name, config = await _selection_service.resolve_agent_identifier(
            session=session,
            participant_id=agent_slug,
        )

        if not slug or not config:
            logfire.warning(
                "agent.invoke_failed",
                **span_tags,
                reason="agent_not_found",
            )
            return {
                "agent_name": agent_slug,
                "content": "",
                "success": False,
                "error": f"Agent '{agent_slug}' not found",
            }

        # Check if agent is participant in room
        rp = RoomParticipant.__table__.c
        result = await session.exec(
            select(RoomParticipant).where(
                rp.room_id == room_id,
                rp.participant_type == "agent",
                rp.participant_id.in_([agent_slug, str(config.id)]),
                rp.active.is_(True),
            )
        )
        participant_row = result.one_or_none()
        participant = (
            participant_row[0]
            if participant_row and not isinstance(participant_row, RoomParticipant)
            else participant_row
        )

        if not participant:
            logfire.warning(
                "agent.invoke_failed",
                **span_tags,
                reason="agent_not_in_room",
            )
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
        logfire.info(
            "agent.invoke_validated",
            **span_tags,
            resolved_agent_slug=slug,
        )

        response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=slug,
            trigger_message=trigger_message,
            session=session,
            user_id=user_id,
            enable_a2a_tool=enable_a2a_tool,
            enable_ag_ui_tool=enable_ag_ui_tool,
        )
        logfire.info(
            "agent.invoke_completed",
            **span_tags,
            success=response.get("success"),
            resolved_agent_slug=slug,
        )
        return response
