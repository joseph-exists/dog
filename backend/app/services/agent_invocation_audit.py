from __future__ import annotations

import hashlib
import uuid
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import AgentInvocation, RoomEvent, RoomMessage
from app.services.agent_prompt import PROMPT_BUILDER_VERSION
from app.services.context_provider import RoomContext


def _jsonable(value: Any) -> Any:
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


def serialize_room_context(context: RoomContext) -> dict[str, Any]:
    """Convert a RoomContext snapshot to stable JSON-compatible data."""

    return _jsonable(context)


def redact_prompt(full_prompt: str) -> str:
    """Redaction boundary for prompt debug reads."""

    return full_prompt


def hash_prompt(full_prompt: str) -> str:
    return hashlib.sha256(full_prompt.encode("utf-8")).hexdigest()


def _story_runtime_snapshot(room_context_json: dict[str, Any]) -> dict[str, Any] | None:
    story_runtime = room_context_json.get("story_runtime")
    return story_runtime if isinstance(story_runtime, dict) else None


def _model_name(agent: Any) -> str | None:
    model = getattr(agent, "model", None)
    if model is None:
        return None
    return str(model)


async def create_agent_invocation(
    *,
    session: AsyncSession,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    trigger_source: str,
    a2a_depth: int,
    acting_user_id: uuid.UUID | None,
    context: RoomContext,
    full_prompt: str,
    agent: Any,
    request_limit: int | None,
    prompt_builder_version: str = PROMPT_BUILDER_VERSION,
) -> AgentInvocation:
    room_context_json = serialize_room_context(context)
    invocation = AgentInvocation(
        room_id=room_id,
        agent_slug=agent_slug,
        trigger_message=trigger_message,
        trigger_source=trigger_source,
        a2a_depth=a2a_depth,
        acting_user_id=acting_user_id,
        room_context_json=room_context_json,
        story_runtime_json=_story_runtime_snapshot(room_context_json),
        full_prompt=full_prompt,
        full_prompt_redacted=redact_prompt(full_prompt),
        prompt_sha256=hash_prompt(full_prompt),
        prompt_builder_version=prompt_builder_version,
        model_name=_model_name(agent),
        runtime_prompt_payload=_jsonable(getattr(agent, "_runtime_prompt_payload", None)),
        runtime_prompt_provenance=_jsonable(getattr(agent, "_runtime_prompt_provenance", None)),
        request_limit=request_limit,
        started_at=datetime.utcnow(),
    )
    session.add(invocation)
    await session.flush()
    return invocation


async def complete_agent_invocation(
    *,
    session: AsyncSession,
    invocation: AgentInvocation | None,
    response_text: str | None = None,
    response_event_id: uuid.UUID | None = None,
    success: bool,
    error: str | None = None,
) -> AgentInvocation | None:
    if invocation is None:
        return None

    invocation.response_text = response_text
    invocation.response_event_id = response_event_id
    invocation.success = success
    invocation.error = error
    invocation.completed_at = datetime.utcnow()

    if response_event_id is not None:
        event = await session.get(RoomEvent, response_event_id)
        if event is not None:
            message_result = await session.exec(
                select(RoomMessage).where(
                    RoomMessage.room_id == invocation.room_id,
                    RoomMessage.sender_type == "agent",
                    RoomMessage.agent_name == invocation.agent_slug,
                    RoomMessage.created_at == event.created_at,
                )
            )
            message = message_result.first()
            if message is not None:
                invocation.response_message_id = message.message_id

    session.add(invocation)
    await session.flush()
    return invocation
