from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_emitter import emit_event, publish_agent_token


class AgentEventPublisher:
    """Publish agent tokens and messages with a stable interface."""

    async def publish_token(
        self,
        *,
        room_id: uuid.UUID,
        agent_name: str,
        token: str,
    ) -> None:
        await publish_agent_token(
            room_id=room_id,
            agent_name=agent_name,
            token=token,
        )

    async def emit_message(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
        agent_name: str,
        content: str,
        ui_components: list[dict[str, Any]] | None = None,
    ) -> None:
        payload: dict[str, Any] = {
            "agent_name": agent_name,
            "content": content,
        }
        if ui_components:
            payload["ui_components"] = ui_components

        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload=payload,
        )
