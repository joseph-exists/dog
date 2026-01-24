from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import AgentConfig, RoomParticipant

logger = logging.getLogger(__name__)

DEFAULT_MAX_A2A_DEPTH = 2


class A2AOrchestrator:
    """Handle agent-to-agent mention detection and triggering."""

    def __init__(self, *, max_depth: int = DEFAULT_MAX_A2A_DEPTH) -> None:
        self._max_depth = max_depth

    def detect_mentions(self, message: str) -> set[str]:
        mentions: set[str] = set()

        quoted_pattern = r'@"([^"]+)"'
        for match in re.finditer(quoted_pattern, message):
            mentions.add(match.group(1).lower())

        simple_pattern = r"@(\w[\w-]*)"
        for match in re.finditer(simple_pattern, message):
            mentions.add(match.group(1).lower())

        return mentions

    async def is_agent_in_room(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
        agent_identifier: str,
    ) -> tuple[bool, str | None, AgentConfig | None]:
        result = await session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.participant_type == "agent",
                RoomParticipant.active == True,  # noqa: E712
            )
        )
        agent_participants = result.all()

        for participant in agent_participants:
            slug, name, config = await self._resolve_agent_identifier(
                session=session,
                participant_id=participant.participant_id,
            )
            if not slug or not config:
                continue

            identifier_lower = agent_identifier.lower()
            if (
                slug.lower() == identifier_lower
                or name.lower() == identifier_lower
                or name.replace(" ", "").lower() == identifier_lower
            ):
                return True, slug, config

        return False, None, None

    async def process_mentions(
        self,
        *,
        response: str,
        responding_agent_slug: str,
        room_id: uuid.UUID,
        session: AsyncSession,
        current_depth: int,
        run_agent: Any,
        user_id: uuid.UUID | None = None,
        emit_internal_message: Any | None = None,
    ) -> list[dict[str, Any]]:
        if current_depth >= self._max_depth:
            logger.debug(
                f"A2A depth limit reached ({current_depth}/{self._max_depth}), "
                f"not processing mentions in {responding_agent_slug}'s response"
            )
            return []

        mentions = self.detect_mentions(response)
        if not mentions:
            return []

        logger.info(
            f"Agent {responding_agent_slug} mentioned {len(mentions)} potential agents: {mentions}"
        )

        triggered_responses: list[dict[str, Any]] = []

        for mention in mentions:
            if mention.lower() == responding_agent_slug.lower():
                continue

            is_in_room, agent_slug, config = await self.is_agent_in_room(
                session=session,
                room_id=room_id,
                agent_identifier=mention,
            )

            if not is_in_room or not agent_slug or not config:
                logger.debug(f"Mentioned '{mention}' is not an agent in room {room_id}")
                continue

            if config.participation_mode == "manual":
                logger.debug(
                    f"Agent {agent_slug} is in manual mode, skipping A2A trigger"
                )
                continue

            logger.info(
                f"A2A: {responding_agent_slug} triggered {agent_slug} "
                f"(depth {current_depth} -> {current_depth + 1})"
            )

            if emit_internal_message:
                await emit_internal_message(
                    session=session,
                    room_id=room_id,
                    from_agent=responding_agent_slug,
                    to_agent=agent_slug,
                    content=f"[A2A Trigger] Requesting assistance from @{agent_slug}",
                    visible_to_users=False,
                )

            trigger_message = f"@{responding_agent_slug} said: {response}"

            agent_response = await run_agent(
                room_id=room_id,
                agent_name=agent_slug,
                trigger_message=trigger_message,
                session=session,
                a2a_depth=current_depth + 1,
                user_id=user_id,
            )
            triggered_responses.append(agent_response)

        return triggered_responses

    async def _resolve_agent_identifier(
        self,
        *,
        session: AsyncSession,
        participant_id: str,
    ) -> tuple[str | None, str | None, AgentConfig | None]:
        try:
            agent_uuid = uuid.UUID(participant_id)
            agent_config = await session.get(AgentConfig, agent_uuid)

            if agent_config and agent_config.is_enabled:
                logger.debug(
                    f"Resolved UUID {participant_id} to agent slug: {agent_config.slug}"
                )
                return agent_config.slug, agent_config.name, agent_config

            logger.warning(
                f"Agent UUID {participant_id} not found or disabled in database"
            )
            return None, None, None

        except ValueError:
            pass

        result = await session.exec(
            select(AgentConfig).where(AgentConfig.slug == participant_id)
        )
        row = result.one_or_none()
        agent_config = (
            row[0] if row and not isinstance(row, AgentConfig) else row
        )

        if agent_config and agent_config.is_enabled:
            logger.debug(f"Found database agent by slug: {participant_id}")
            return agent_config.slug, agent_config.name, agent_config

        logger.warning(f"Agent '{participant_id}' not found in database")
        return None, None, None
