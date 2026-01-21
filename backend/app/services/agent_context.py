from __future__ import annotations

import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.context_provider import RoomContext, build_room_context
from app.services.context_store import ContextItemStore, RedisContextStore


class RoomContextService:
    """Thin wrapper around build_room_context with a stable interface."""

    def __init__(self, context_store: ContextItemStore | None = None) -> None:
        self._context_store = context_store or RedisContextStore()

    async def build(
        self,
        *,
        room_id: uuid.UUID,
        session: AsyncSession,
        message_limit: int = 20,
        agent_slug: str | None = None,
        context_store: ContextItemStore | None = None,
    ) -> RoomContext:
        store = context_store or self._context_store
        return await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=message_limit,
            agent_slug=agent_slug,
            context_store=store,
        )
