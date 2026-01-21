from __future__ import annotations

import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from app.services.agent_runner_types import AgentRunResult


class AgentErrorHandler:
    """Normalize error handling for agent runs."""

    async def handle_error(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
        agent_name: str,
        exc: Exception,
    ) -> AgentRunResult:
        raise NotImplementedError
