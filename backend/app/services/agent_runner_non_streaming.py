from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.agent_context import RoomContextService
from app.services.agent_events import AgentEventPublisher
from app.services.agent_runner_types import AgentRunRequest, AgentRunResult
from app.services.logfire_client import ServiceLogfire

logger = logging.getLogger(__name__)

SERVICE_ID = "agent_runner_non_streaming"
logfire = ServiceLogfire(SERVICE_ID)


class NonStreamingAgentRunner:
    """Run agents without token streaming."""

    def __init__(
        self,
        *,
        context_service: RoomContextService,
        event_publisher: AgentEventPublisher,
        is_agent_available: Callable[[AsyncSession, str], Awaitable[bool]],
        get_agent_instance: Callable[[AsyncSession, str], Awaitable[Any]],
        build_agent_prompt: Callable[[str, Any, str | None], str],
    ) -> None:
        self._context_service = context_service
        self._event_publisher = event_publisher
        self._is_agent_available = is_agent_available
        self._get_agent_instance = get_agent_instance
        self._build_agent_prompt = build_agent_prompt

    async def run(
        self,
        *,
        req: AgentRunRequest,
        session: AsyncSession,
    ) -> AgentRunResult:
        room_id = req.room_id
        agent_name = req.agent_slug
        trigger_message = req.trigger_message
        room_id_str = str(room_id)

        span_tags = {
            "room_id": room_id_str,
            "agent_name": agent_name,
        }

        with logfire.span("agent.run_non_streaming", **span_tags):
            if not await self._is_agent_available(session, agent_name):
                logger.warning(f"Attempted to run unregistered agent: {agent_name}")
                logfire.warning("agent.not_available", **span_tags)
                return AgentRunResult(
                    agent_name=agent_name,
                    content="",
                    success=False,
                    error=f"Agent '{agent_name}' not found",
                )

            try:
                context = await self._context_service.build(
                    room_id=room_id,
                    session=session,
                    message_limit=20,
                    agent_slug=agent_name,
                )

                with logfire.span("agent.instantiate", **span_tags):
                    agent = await self._get_agent_instance(session, agent_name)
                    logfire.info(
                        "agent.instantiated",
                        **span_tags,
                        agent_model=getattr(agent, "model", None),
                    )
                if not agent:
                    logfire.warning("agent.instantiate_failed", **span_tags)
                    return AgentRunResult(
                        agent_name=agent_name,
                        content="",
                        success=False,
                        error=f"Failed to instantiate agent '{agent_name}'",
                    )

                full_prompt = self._build_agent_prompt(
                    trigger_message, context, current_agent_slug=agent_name
                )

                result = await agent.run(full_prompt)
                response_content = result.output

                await self._event_publisher.emit_message(
                    session=session,
                    room_id=room_id,
                    agent_name=agent_name,
                    content=response_content,
                )

                logger.info(f"Agent {agent_name} responded in room {room_id}")
                logfire.info(
                    "agent.non_streaming_completed",
                    **span_tags,
                    response_length=len(response_content),
                )

                return AgentRunResult(
                    agent_name=agent_name,
                    content=response_content,
                    success=True,
                    error=None,
                )

            except Exception as exc:
                logger.error(f"Agent {agent_name} error in room {room_id}: {exc}")
                logfire.exception(
                    "agent.non_streaming_error",
                    **span_tags,
                    error=str(exc),
                )

                error_content = (
                    "I encountered an error while processing your request. Please try again."
                )

                try:
                    await self._event_publisher.emit_message(
                        session=session,
                        room_id=room_id,
                        agent_name=agent_name,
                        content=error_content,
                    )
                except Exception as emit_error:
                    logger.error(f"Failed to emit error message: {emit_error}")
                    logfire.exception(
                        "agent.emit_error_failed",
                        **span_tags,
                        error=str(emit_error),
                    )

                return AgentRunResult(
                    agent_name=agent_name,
                    content=error_content,
                    success=False,
                    error=str(exc),
                )
