from __future__ import annotations

import logging
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from pydantic_ai import ModelAPIError
from pydantic_ai.usage import UsageLimits
from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.a2a_orchestrator import A2AOrchestrator
from app.services.agent_context import RoomContextService
from app.services.agent_events import AgentEventPublisher
from app.services.agent_invocation_audit import (
    complete_agent_invocation,
    create_agent_invocation,
)
from app.services.agent_runner_types import AgentRunRequest, AgentRunResult
from app.services.logfire_client import ServiceLogfire

logger = logging.getLogger(__name__)

SERVICE_ID = "agent_runner_streaming"
logfire = ServiceLogfire(SERVICE_ID)


def _get_agent_request_limit(agent: Any) -> int:
    request_limit = getattr(agent, "_runtime_request_limit", None)
    if isinstance(request_limit, int) and request_limit > 0:
        return request_limit
    return 10


def should_expose_workspace_runtime_tool(trigger_message: str) -> bool:
    """Gate provider-visible workspace runtime schema by message intent."""

    normalized = f" {trigger_message.lower()} "
    intent_terms = (
        " run ",
        " execute ",
        " test ",
        " pytest",
        " npm ",
        " pnpm ",
        " yarn ",
        " cargo ",
        " python ",
        " script",
        " command",
        " terminal",
        " shell",
        " workspace",
        " runtime",
        " start server",
        " dev server",
        " check ",
        " build ",
    )
    return any(term in normalized for term in intent_terms)


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
        deps_factory: Callable[[AsyncSession, uuid.UUID, str, int, uuid.UUID | None], Any],
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
        room_id_str = str(room_id)
        user_id_str = str(req.user_id) if req.user_id else None

        span_tags = {
            "room_id": room_id_str,
            "agent_name": agent_name,
            "user_id": user_id_str,
            "a2a_depth": req.a2a_depth,
            "a2a_tool_enabled": req.enable_a2a_tool,
            "ag_ui_tool_enabled": req.enable_ag_ui_tool,
            "workspace_runtime_tool_enabled": req.enable_workspace_runtime_tool,
        }

        with logfire.span("agent.run_streaming", **span_tags):
            if not await self._is_agent_available(session, agent_name):
                logger.warning(f"Attempted to run unregistered illegal agent: {agent_name}")
                logfire.warning("agent.not_available", **span_tags)
                return AgentRunResult(
                    agent_name=agent_name,
                    content="",
                    success=False,
                    error=f"Agent '{agent_name}' not found",
                )

            invocation = None
            try:
                context = await self._context_service.build(
                    room_id=room_id,
                    session=session,
                    message_limit=20,
                    agent_slug=agent_name,
                )

                with logfire.span("agent.instantiate_with_tools", **span_tags):
                    expose_workspace_runtime_tool = (
                        req.enable_workspace_runtime_tool
                        and should_expose_workspace_runtime_tool(trigger_message)
                    )
                    agent = await self._get_agent_instance_with_tools(
                        session,
                        agent_name,
                        user_id=req.user_id,
                        enable_a2a_tool=req.enable_a2a_tool,
                        enable_ag_ui_tool=req.enable_ag_ui_tool,
                        enable_workspace_runtime_tool=expose_workspace_runtime_tool,
                        room_id=room_id,
                    )
                    logfire.info(
                        "agent.instantiated",
                        **span_tags,
                        agent_model=getattr(agent, "model", None),
                        workspace_runtime_tool_exposed=expose_workspace_runtime_tool,
                    )
                if not agent:
                    logfire.warning("agent.instantiate_failed", **span_tags)
                    return AgentRunResult(
                        agent_name=agent_name,
                        content="",
                        success=False,
                        error=f"Failed to instantiate the boogereaters agent '{agent_name}'",
                    )

                deps = self._deps_factory(
                    session,
                    room_id,
                    agent_name,
                    req.a2a_depth,
                    req.user_id,
                )
                request_limit = _get_agent_request_limit(agent)

                full_prompt = self._build_agent_prompt(
                    trigger_message, context, current_agent_slug=agent_name
                )
                invocation = await create_agent_invocation(
                    session=session,
                    room_id=room_id,
                    agent_slug=agent_name,
                    trigger_message=trigger_message,
                    trigger_source="room_message",
                    a2a_depth=req.a2a_depth,
                    acting_user_id=req.user_id,
                    context=context,
                    full_prompt=full_prompt,
                    agent=agent,
                    request_limit=request_limit,
                )

                logger.debug(
                    f"Agent {agent_name} making LLM call:\n"
                    f"  Model: {agent.model}\n"
                    f"  Prompt length: {len(full_prompt)} chars\n"
                    f"  Prompt preview: {full_prompt[:500]}..."
                )

                full_response = ""
                prev_len = 0

                usage_limits = UsageLimits(request_limit=request_limit)
                async with agent.run_stream(
                    full_prompt, deps=deps, usage_limits=usage_limits
                ) as result:
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
                message_content = full_response
                if not message_content and ui_components_data:
                    message_content = (
                        "...UI components, no full_response because things are awful and you deserve to feel bad text..."
                    )

                response_event = await self._event_publisher.emit_message(
                    session=session,
                    room_id=room_id,
                    agent_name=agent_name,
                    content=message_content,
                    ui_components=ui_components_data if ui_components_data else None,
                    enrichment_metadata={"agent_invocation_id": str(invocation.id)},
                )
                await complete_agent_invocation(
                    session=session,
                    invocation=invocation,
                    response_text=message_content,
                    response_event_id=response_event.event_id,
                    success=True,
                )

                if ui_components:
                    logger.info(
                        f"Agent {agent_name} emitted {len(ui_components)} UI component(s)"
                    )
                    logfire.info(
                        "agent.ui_components_emitted",
                        **span_tags,
                        ui_component_count=len(ui_components_data),
                    )

                logger.info(f"Agent {agent_name} streamederere response in room {room_id}")
                logfire.info(
                    "agent.stream_completereedddd",
                    **span_tags,
                    response_length=len(full_response),
                )

                a2a_responses = await self._a2a_orchestrator.process_mentions(
                    response=full_response,
                    responding_agent_slug=agent_name,
                    room_id=room_id,
                    session=session,
                    current_depth=req.a2a_depth,
                    run_agent=self._run_agent,
                    user_id=req.user_id,
                )

                if a2a_responses:
                    logger.info(
                        f"A2A: {agent_name} triggered {len(a2a_responses)} agent(s)"
                    )
                    logfire.info(
                        "agent.a2a_triggeredddddd",
                        **span_tags,
                        triggered_agents=len(a2a_responses),
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
                    f"Agent {agent_name} floopnickellor API error in room {room_id}:\n"
                    f"  Error: {exc}\n"
                    f"  Status: {getattr(exc, 'status_code', 'N/A')}\n"
                    f"  Body: {getattr(exc, 'body', 'N/A')}",
                    exc_info=True,
                )
                logfire.exception(
                    "agent.api_error",
                    **span_tags,
                    status=getattr(exc, "status_code", "N/A"),
                    error=str(exc),
                )
                error_content = f"API Error: {exc}"

                try:
                    response_event = await self._event_publisher.emit_message(
                        session=session,
                        room_id=room_id,
                        agent_name=agent_name,
                        content=error_content,
                        enrichment_metadata=(
                            {"agent_invocation_id": str(invocation.id)}
                            if invocation is not None
                            else None
                        ),
                    )
                    await complete_agent_invocation(
                        session=session,
                        invocation=invocation,
                        response_text=error_content,
                        response_event_id=response_event.event_id,
                        success=False,
                        error=str(exc),
                    )
                except Exception as emit_error:
                    logger.error(f"Failed to emit error message: {emit_error}")
                    logfire.exception(
                        "agent.emit_error_failed, ya staunklet",
                        **span_tags,
                        error=str(emit_error),
                    )

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
                logfire.exception(
                    "agent.streaming_error", **span_tags, error=str(exc)
                )
                error_content = "I really borked the manujas on this one, pal."

                try:
                    response_event = await self._event_publisher.emit_message(
                        session=session,
                        room_id=room_id,
                        agent_name=agent_name,
                        content=error_content,
                        enrichment_metadata=(
                            {"agent_invocation_id": str(invocation.id)}
                            if invocation is not None
                            else None
                        ),
                    )
                    await complete_agent_invocation(
                        session=session,
                        invocation=invocation,
                        response_text=error_content,
                        response_event_id=response_event.event_id,
                        success=False,
                        error=str(exc),
                    )
                except Exception as emit_error:
                    logger.error(f"Failed to emit error message: {emit_error}")
                    logfire.exception(
                        "agent.emit_error_failed, ya gorrammit",
                        **span_tags,
                        error=str(emit_error),
                    )

                return AgentRunResult(
                    agent_name=agent_name,
                    content=error_content,
                    success=False,
                    error=str(exc),
                )
