from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from typing import Any

from pydantic_ai import RunContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.ag_ui import UIComponent, UIComponentType
from app.services.a2a_orchestrator import A2AOrchestrator, DEFAULT_MAX_A2A_DEPTH
from app.services.agent_prompt import build_agent_prompt
from app.services.context_provider import build_room_context
from app.services.context_store import RedisContextStore

logger = logging.getLogger(__name__)

_a2a_orchestrator = A2AOrchestrator(max_depth=DEFAULT_MAX_A2A_DEPTH)


@dataclass
class AgentDeps:
    """
    Dependencies passed to agent tools via PydanticAI's RunContext.

    This enables tools to access:
    - Database session for queries
    - Room context for multi-agent coordination
    - Current agent info for self-awareness
    - UI components collector for AG-UI

    Usage in tools:
        async def my_tool(ctx: RunContext[AgentDeps], arg: str) -> str:
            session = ctx.deps.session
            room_id = ctx.deps.room_id
            ...
    """

    session: AsyncSession
    room_id: uuid.UUID
    current_agent_slug: str
    a2a_depth: int = 0
    # AG-UI: Collected UI components (populated by emit_ui_component tool)
    ui_components: list[UIComponent] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.ui_components is None:
            self.ui_components = []

    def add_ui_component(self, component: UIComponent) -> None:
        """Add a UI component to the collection."""
        if self.ui_components is None:
            self.ui_components = []
        self.ui_components.append(component)


async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,
    request: str,
) -> str:
    """
    Request another agent's expertise on a specific topic.

    Use this tool when you need specialized help from another agent in the room.
    The target agent will process your request and return their response.
    """
    deps = ctx.deps

    if deps.a2a_depth >= DEFAULT_MAX_A2A_DEPTH:
        return (
            f"[A2A limit reached] Cannot request assistance from {target_agent} - "
            f"maximum agent chain depth ({DEFAULT_MAX_A2A_DEPTH}) exceeded."
        )

    if target_agent.lower() == deps.current_agent_slug.lower():
        return "[Error] Cannot request assistance from yourself."

    is_in_room, agent_slug, config = await _a2a_orchestrator.is_agent_in_room(
        session=deps.session,
        room_id=deps.room_id,
        agent_identifier=target_agent,
    )

    if not is_in_room or not agent_slug:
        return (
            f"[Agent not found] '{target_agent}' is not available in this room. "
            f"Check the agent name or ask the user to add them to the room."
        )

    logger.info(
        f"A2A Tool: {deps.current_agent_slug} requesting assistance from {agent_slug} "
        f"(depth {deps.a2a_depth} -> {deps.a2a_depth + 1})"
    )

    response = await _run_agent_for_tool_call(
        room_id=deps.room_id,
        agent_slug=agent_slug,
        request=request,
        requesting_agent=deps.current_agent_slug,
        session=deps.session,
        _a2a_depth=deps.a2a_depth + 1,
    )

    if response["success"]:
        return response["content"]
    else:
        return f"[Error from {agent_slug}] {response.get('error', 'Unknown error')}"


async def _run_agent_for_tool_call(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    request: str,
    requesting_agent: str,
    session: AsyncSession,
    _a2a_depth: int,
) -> dict[str, Any]:
    """
    Internal function to run an agent for a tool call (non-streaming).

    Unlike run_agent_for_room_streaming, this:
    - Does NOT emit room_message.agent events (response goes back to calling agent)
    - Does NOT publish tokens to Redis
    - Does NOT enable A2A tools on target agent (prevents infinite recursion)
    - Returns response directly to the calling tool
    """
    from app.services.agent_instance import get_agent_instance

    agent = await get_agent_instance(session, agent_slug)
    if not agent:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Failed to instantiate agent '{agent_slug}'",
        }

    try:
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
            agent_slug=agent_slug,
            context_store=RedisContextStore(),
        )

        prompt = f"@{requesting_agent} is asking for your assistance:\n\n{request}"
        full_prompt = build_agent_prompt(prompt, context, current_agent_slug=agent_slug)

        result = await agent.run(full_prompt)

        logger.debug(
            f"A2A Tool: {agent_slug} responded to {requesting_agent} "
            f"({len(result.output)} chars)"
        )

        return {
            "agent_name": agent_slug,
            "content": result.output,
            "success": True,
            "error": None,
        }

    except Exception as exc:
        logger.error(f"A2A Tool error: {agent_slug} failed to respond: {exc}")
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": str(exc),
        }


def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str:
    """
    Emit a structured UI component to be displayed alongside your response.
    """
    component = UIComponent(
        type=component_type,
        data=data,
        fallback_text=fallback_text,
    )

    ctx.deps.add_ui_component(component)

    logger.debug(
        f"AG-UI: Agent {ctx.deps.current_agent_slug} emitted {component_type} component"
    )

    return f"[UI Component Added: {component_type}] Component will be displayed with your response."
