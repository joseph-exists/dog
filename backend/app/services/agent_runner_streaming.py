from __future__ import annotations

import logging
import uuid
from typing import Any, Awaitable, Callable

from pydantic_ai import ModelAPIError
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.a2a_orchestrator import A2AOrchestrator
from app.services.agent_context import RoomContextService
from app.services.agent_events import AgentEventPublisher
from app.services.agent_runner_types import AgentRunRequest, AgentRunResult

logger = logging.getLogger(__name__)


class StreamingAgentRunner:
    """Run agents with token streaming and optional A2A."""

    def __init__(
        self,
        *,
        context_service: RoomContextService,
        event_publisher: AgentEventPublisher,
        is_agent_available: Callable[[AsyncSession, str], Awaitable[bool]],
        get_agent_instance_with_tools: Callable[..., Awaitable[Any]],
        build_agent_prompt: Callable[[str, Any, str | None], str],
        deps_factory: Callable[[AsyncSession, uuid.UUID, str, int], Any],
        a2a_orchestrator: A2AOrchestrator,
        run_agent: Callable[..., Awaitable[dict[str, Any]]],
    ) -> None:
        self._context_service = context_service
        self._event_publisher = event_publisher
        self._is_agent_available = is_agent_available
        self._get_agent_instance_with_tools = get_agent_instance_with_tools
        self._build_agent_prompt = build_agent_prompt
        self._deps_factory = deps_factory
        self._a2a_orchestrator = a2a_orchestrator
        self._run_agent = run_agent

    async def run(
        self,
        *,
        req: AgentRunRequest,
        session: AsyncSession,
    ) -> AgentRunResult:
        room_id = req.room_id
        agent_name = req.agent_slug
        trigger_message = req.trigger_message

        if not await self._is_agent_available(session, agent_name):
            logger.warning(f"Attempted to run unregistered agent: {agent_name}")
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

            agent = await self._get_agent_instance_with_tools(
                session, agent_name, user_id=req.user_id, enable_a2a_tool=True
            )
            if not agent:
                return AgentRunResult(
                    agent_name=agent_name,
                    content="",
                    success=False,
                    error=f"Failed to instantiate agent '{agent_name}'",
                )

            deps = self._deps_factory(session, room_id, agent_name, req.a2a_depth)

            full_prompt = self._build_agent_prompt(
                trigger_message, context, current_agent_slug=agent_name
            )

            logger.debug(
                f"Agent {agent_name} making LLM call:\n"
                f"  Model: {agent.model}\n"
                f"  Prompt length: {len(full_prompt)} chars\n"
                f"  Prompt preview: {full_prompt[:500]}..."
            )

            full_response = ""
            prev_len = 0

            async with agent.run_stream(full_prompt, deps=deps) as result:
                async for chunk in result.stream_text():
                    new_content = chunk[prev_len:]
                    full_response = chunk
                    prev_len = len(chunk)

                    if new_content:
                        await self._event_publisher.publish_token(
                            room_id=room_id,
                            agent_name=agent_name,
                            token=new_content,
                        )

            ui_components = getattr(deps, "ui_components", None) or []
            ui_components_data = [c.model_dump() for c in ui_components]

            await self._event_publisher.emit_message(
                session=session,
                room_id=room_id,
                agent_name=agent_name,
                content=full_response,
                ui_components=ui_components_data if ui_components_data else None,
            )

            if ui_components:
                logger.info(
                    f"Agent {agent_name} emitted {len(ui_components)} UI component(s)"
                )

            logger.info(f"Agent {agent_name} streamed response in room {room_id}")

            a2a_responses = await self._a2a_orchestrator.process_mentions(
                response=full_response,
                responding_agent_slug=agent_name,
                room_id=room_id,
                session=session,
                current_depth=req.a2a_depth,
                run_agent=self._run_agent,
            )

            if a2a_responses:
                logger.info(
                    f"A2A: {agent_name} triggered {len(a2a_responses)} agent(s)"
                )

            return AgentRunResult(
                agent_name=agent_name,
                content=full_response,
                success=True,
                error=None,
                a2a_triggered=[
                    r["agent_name"] for r in a2a_responses if r.get("success")
                ],
                ui_components=ui_components_data if ui_components_data else None,
            )

        except ModelAPIError as exc:
            logger.error(
                f"Agent {agent_name} API error in room {room_id}:\n"
                f"  Error: {exc}\n"
                f"  Status: {getattr(exc, 'status_code', 'N/A')}\n"
                f"  Body: {getattr(exc, 'body', 'N/A')}",
                exc_info=True,
            )
            error_content = f"API Error: {exc}"

            try:
                await self._event_publisher.emit_message(
                    session=session,
                    room_id=room_id,
                    agent_name=agent_name,
                    content=error_content,
                )
            except Exception as emit_error:
                logger.error(f"Failed to emit error message: {emit_error}")

            return AgentRunResult(
                agent_name=agent_name,
                content=error_content,
                success=False,
                error=str(exc),
            )

        except Exception as exc:
            logger.error(
                f"Agent {agent_name} streaming error in room {room_id}: {exc}",
                exc_info=True,
            )
            error_content = "I encountered an error while processing your request."

            try:
                await self._event_publisher.emit_message(
                    session=session,
                    room_id=room_id,
                    agent_name=agent_name,
                    content=error_content,
                )
            except Exception as emit_error:
                logger.error(f"Failed to emit error message: {emit_error}")

            return AgentRunResult(
                agent_name=agent_name,
                content=error_content,
                success=False,
                error=str(exc),
            )
