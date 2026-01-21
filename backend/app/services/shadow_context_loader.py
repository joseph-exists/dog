from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models import AgentConfig, Room, RoomParticipantBinding
from app.services.context_store import ContextItem
from app.services.shadow_read_service import ShadowRepoNotFound, ShadowVersionNotFound
from app.services.shadow_summary_service import shadow_summary_service

logger = logging.getLogger(__name__)


def _context_item(
    *,
    room_id: uuid.UUID,
    agent_slug: str | None,
    context_type: str,
    payload: dict[str, Any],
    created_at: datetime,
    ttl_seconds: int,
    item_id: str,
) -> ContextItem:
    return ContextItem(
        id=item_id,
        room_id=room_id,
        agent_slug=agent_slug,
        context_type=context_type,
        payload=payload,
        source="shadow",
        created_at=created_at,
        expires_at=created_at + timedelta(seconds=ttl_seconds),
    )


def _missing_shadow_snapshot_item(
    *,
    room_id: uuid.UUID,
    agent_slug: str | None,
    context_type: str,
    entity_type: str,
    entity_id: uuid.UUID | str | None,
    reason: str,
    created_at: datetime,
    ttl_seconds: int,
    item_id: str,
) -> ContextItem:
    payload = {
        "missing_shadow_snapshot": True,
        "entity_type": entity_type,
        "entity_id": str(entity_id) if entity_id is not None else None,
        "reason": reason,
        "is_stale": True,
    }
    return _context_item(
        room_id=room_id,
        agent_slug=agent_slug,
        context_type=context_type,
        payload=payload,
        created_at=created_at,
        ttl_seconds=ttl_seconds,
        item_id=item_id,
    )


async def build_shadow_context_items(
    *,
    room_id: uuid.UUID,
    agent_slug: str | None,
    session: AsyncSession,
) -> list[ContextItem]:
    """
    Build Shadow-derived context items for a room.

    - Room-wide: room summary + story summary (if any)
    - Agent-scoped: agent summary + persona summary + runtime summary
    """
    now = datetime.now(tz=timezone.utc)
    items: list[ContextItem] = []

    room_result = await session.exec(select(Room).where(Room.room_id == room_id))
    room = room_result.one_or_none()
    if not room:
        return items

    # Room summary
    try:
        room_summary = await shadow_summary_service.get_latest_summary(
            session=session.sync_session,
            entity_type="room",
            entity_id=room_id,
        )
        items.append(
            _context_item(
                room_id=room_id,
                agent_slug=None,
                context_type="shadow.room.summary",
                payload=room_summary.__dict__,
                created_at=now,
                ttl_seconds=120,
                item_id=f"shadow:room:{room_id}:latest",
            )
        )
    except (ShadowRepoNotFound, ShadowVersionNotFound) as exc:
        logger.warning(f"Missing Shadow snapshot for room {room_id}: {exc}")
        items.append(
            _missing_shadow_snapshot_item(
                room_id=room_id,
                agent_slug=None,
                context_type="shadow.room.summary",
                entity_type="room",
                entity_id=room_id,
                reason=str(exc),
                created_at=now,
                ttl_seconds=120,
                item_id=f"shadow:room:{room_id}:missing",
            )
        )

    # Story summary (if room has a story)
    if room.story_id:
        try:
            story_summary = await shadow_summary_service.get_latest_summary(
                session=session.sync_session,
                entity_type="story",
                entity_id=room.story_id,
            )
            items.append(
                _context_item(
                    room_id=room_id,
                    agent_slug=None,
                    context_type="shadow.story.summary",
                    payload=story_summary.__dict__,
                    created_at=now,
                    ttl_seconds=300,
                    item_id=f"shadow:story:{room.story_id}:latest",
                )
            )
        except (ShadowRepoNotFound, ShadowVersionNotFound) as exc:
            logger.warning(f"Missing Shadow snapshot for story {room.story_id}: {exc}")
            items.append(
                _missing_shadow_snapshot_item(
                    room_id=room_id,
                    agent_slug=None,
                    context_type="shadow.story.summary",
                    entity_type="story",
                    entity_id=room.story_id,
                    reason=str(exc),
                    created_at=now,
                    ttl_seconds=300,
                    item_id=f"shadow:story:{room.story_id}:missing",
                )
            )

    if not agent_slug:
        return items

    # Agent summary (agent-scoped)
    agent_result = await session.exec(
        select(AgentConfig).where(AgentConfig.slug == agent_slug)
    )
    agent_config = agent_result.one_or_none()
    if not agent_config:
        return items

    try:
        agent_summary = await shadow_summary_service.get_latest_summary(
            session=session.sync_session,
            entity_type="agent",
            entity_id=agent_config.id,
        )
        items.append(
            _context_item(
                room_id=room_id,
                agent_slug=agent_slug,
                context_type="shadow.agent.summary",
                payload=agent_summary.__dict__,
                created_at=now,
                ttl_seconds=300,
                item_id=f"shadow:agent:{agent_config.id}:latest",
            )
        )
    except (ShadowRepoNotFound, ShadowVersionNotFound) as exc:
        logger.warning(f"Missing Shadow snapshot for agent {agent_config.id}: {exc}")
        items.append(
            _missing_shadow_snapshot_item(
                room_id=room_id,
                agent_slug=agent_slug,
                context_type="shadow.agent.summary",
                entity_type="agent",
                entity_id=agent_config.id,
                reason=str(exc),
                created_at=now,
                ttl_seconds=300,
                item_id=f"shadow:agent:{agent_config.id}:missing",
            )
        )

    # Binding-driven persona + runtime (agent-scoped)
    binding_result = await session.exec(
        select(RoomParticipantBinding).where(
            RoomParticipantBinding.room_id == room_id,
            RoomParticipantBinding.participant_type == "agent",
            RoomParticipantBinding.participant_id == agent_slug,
            RoomParticipantBinding.ended_at.is_(None),
        )
    )
    binding = binding_result.one_or_none()
    if not binding:
        return items

    if binding.persona_id:
        try:
            persona_summary = await shadow_summary_service.get_latest_summary(
                session=session.sync_session,
                entity_type="persona",
                entity_id=binding.persona_id,
            )
            items.append(
                _context_item(
                    room_id=room_id,
                    agent_slug=agent_slug,
                    context_type="shadow.persona.summary",
                    payload=persona_summary.__dict__,
                    created_at=now,
                    ttl_seconds=300,
                    item_id=f"shadow:persona:{binding.persona_id}:latest",
                )
            )
        except (ShadowRepoNotFound, ShadowVersionNotFound) as exc:
            logger.warning(
                f"Missing Shadow snapshot for persona {binding.persona_id}: {exc}"
            )
            items.append(
                _missing_shadow_snapshot_item(
                    room_id=room_id,
                    agent_slug=agent_slug,
                    context_type="shadow.persona.summary",
                    entity_type="persona",
                    entity_id=binding.persona_id,
                    reason=str(exc),
                    created_at=now,
                    ttl_seconds=300,
                    item_id=f"shadow:persona:{binding.persona_id}:missing",
                )
            )

    runtime_payload = {
        "binding": {
            "participant_type": binding.participant_type,
            "participant_id": binding.participant_id,
            "persona_id": str(binding.persona_id) if binding.persona_id else None,
            "model_name": binding.model_name,
            "user_llm_provider_id": (
                str(binding.user_llm_provider_id) if binding.user_llm_provider_id else None
            ),
            "effective_at": binding.effective_at.isoformat() if binding.effective_at else None,
        }
    }

    if binding.user_llm_provider_id:
        try:
            provider_summary = await shadow_summary_service.get_latest_summary(
                session=session.sync_session,
                entity_type="user_llm_provider",
                entity_id=binding.user_llm_provider_id,
            )
            runtime_payload["user_llm_provider"] = provider_summary.__dict__
        except (ShadowRepoNotFound, ShadowVersionNotFound) as exc:
            logger.warning(
                f"Missing Shadow snapshot for user_llm_provider {binding.user_llm_provider_id}: {exc}"
            )
            runtime_payload["user_llm_provider_missing"] = {
                "missing_shadow_snapshot": True,
                "entity_type": "user_llm_provider",
                "entity_id": str(binding.user_llm_provider_id),
                "reason": str(exc),
                "is_stale": True,
            }

    items.append(
        _context_item(
            room_id=room_id,
            agent_slug=agent_slug,
            context_type="shadow.runtime.summary",
            payload=runtime_payload,
            created_at=now,
            ttl_seconds=120,
            item_id=f"shadow:runtime:{binding.id}:active",
        )
    )

    return items
