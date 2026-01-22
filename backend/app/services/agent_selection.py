from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import AgentConfig, RoomParticipant

logger = logging.getLogger(__name__)


def _detect_mentions(message: str) -> set[str]:
    mentions: set[str] = set()

    quoted_pattern = r'@"([^"]+)"'
    for match in re.finditer(quoted_pattern, message):
        mentions.add(match.group(1).lower())

    simple_pattern = r"@(\w[\w-]*)"
    for match in re.finditer(simple_pattern, message):
        mentions.add(match.group(1).lower())

    return mentions


def _is_agent_mentioned(message: str, agent_slug: str, agent_name: str) -> bool:
    mentions = _detect_mentions(message)
    if not mentions:
        return False

    if agent_slug.lower() in mentions:
        return True

    if agent_name.lower() in mentions:
        return True

    name_no_spaces = agent_name.replace(" ", "").lower()
    if name_no_spaces in mentions:
        return True

    return False


class AgentSelectionService:
    """Resolve and select agents for message handling."""

    async def resolve_participants(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
    ) -> list[RoomParticipant]:
        result = await session.exec(
            select(RoomParticipant).where(
                RoomParticipant.room_id == room_id,
                RoomParticipant.participant_type == "agent",
                RoomParticipant.active == True,  # noqa: E712
            )
        )
        rows = result.all()
        return [row[0] for row in rows]

    async def resolve_agent_identifier(
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
        agent_config = row[0] if row else None

        if agent_config and agent_config.is_enabled:
            logger.debug(f"Found database agent by slug: {participant_id}")
            return agent_config.slug, agent_config.name, agent_config

        logger.warning(f"Agent '{participant_id}' not found in database")
        return None, None, None

    async def is_agent_available(
        self,
        session: AsyncSession,
        participant_id: str,
    ) -> bool:
        """Check if an agent is available in the database."""
        slug, _, _ = await self.resolve_agent_identifier(
            session=session,
            participant_id=participant_id,
        )
        return slug is not None

    def should_agent_respond_to_message(
        self,
        *,
        config: AgentConfig,
        trigger_message: str,
    ) -> tuple[bool, str]:
        mode = config.participation_mode or "on_mention"

        if mode == "always":
            return True, "mode=always"

        if mode == "manual":
            return False, "mode=manual (requires explicit invocation)"

        if mode == "on_mention":
            if _is_agent_mentioned(trigger_message, config.slug, config.name):
                return True, "mentioned in message"
            return False, "not mentioned (mode=on_mention)"

        logger.warning(f"Unknown participation mode '{mode}' for agent {config.slug}")
        return False, f"unknown mode '{mode}'"

    async def select_agents_for_message(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
        trigger_message: str,
    ) -> tuple[
        list[tuple[str, str, AgentConfig]],
        list[tuple[str, str, AgentConfig, str]],
    ]:
        participants = await self.resolve_participants(
            session=session,
            room_id=room_id,
        )

        coordinators: list[tuple[str, str, AgentConfig]] = []
        regular_agents: list[tuple[str, str, AgentConfig, str]] = []

        for participant in participants:
            participant_id = participant.participant_id
            agent_slug, display_name, config = await self.resolve_agent_identifier(
                session=session,
                participant_id=participant_id,
            )

            if not agent_slug or not config:
                logger.warning(
                    f"Agent participant '{participant_id}' in room {room_id} "
                    f"could not be resolved to a registered agent"
                )
                continue

            if config.is_coordinator:
                coordinators.append((agent_slug, display_name, config))
            else:
                regular_agents.append(
                    (agent_slug, display_name, config, participant_id)
                )

        return coordinators, regular_agents
