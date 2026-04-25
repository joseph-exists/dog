from __future__ import annotations

import uuid
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import RoomEvent
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
        enrichment_metadata: dict[str, Any] | None = None,
    ) -> RoomEvent:
        payload: dict[str, Any] = {
            "agent_name": agent_name,
            "content": content,
        }
        if ui_components:
            payload["ui_components"] = ui_components

        return await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload=payload,
            enrichment_metadata=enrichment_metadata,
        )
