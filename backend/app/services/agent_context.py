from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.context_provider import RoomContext, build_room_context


class RoomContextService:
    """Thin wrapper around build_room_context with a stable interface."""

    async def build(
        self,
        *,
        room_id: uuid.UUID,
        session: AsyncSession,
        message_limit: int = 20,
    ) -> RoomContext:
        return await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=message_limit,
        )
