from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models import UserAgentConfig, Room, RoomParticipantBinding
from app.services.context_store import ContextItem
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


def _missing_shadow_snapshot_reason(
    *,
    entity_type: str,
    entity_id: uuid.UUID | str | None,
) -> str:
    entity_id_str = str(entity_id) if entity_id is not None else "unknown"
    return f"No Shadow snapshot available for {entity_type}/{entity_id_str}"


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
    room_row = room_result.one_or_none()
    room = room_row[0] if room_row and not isinstance(room_row, Room) else room_row
    if not room:
        return items

    # Room summary
    room_summary = await shadow_summary_service.get_latest_summary(
        session=session,
        entity_type="room",
        entity_id=room_id,
    )
    if room_summary:
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
    else:
        reason = _missing_shadow_snapshot_reason(
            entity_type="room", entity_id=room_id
        )
        logger.warning(reason)

    # Story summary (if room has a story)
    if room.story_id:
        reason = _missing_shadow_snapshot_reason(
            entity_type="story", entity_id=room.story_id
        )
        story_summary = await shadow_summary_service.get_latest_summary(
            session=session,
            entity_type="story",
            entity_id=room.story_id,
        )
        if story_summary:
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
        else:
            logger.warning(reason)
            items.append(
                _missing_shadow_snapshot_item(
                    room_id=room_id,
                    agent_slug=None,
                    context_type="shadow.story.summary",
                    entity_type="story",
                    entity_id=room.story_id,
                    reason=reason,
                    created_at=now,
                    ttl_seconds=300,
                    item_id=f"shadow:story:{room.story_id}:missing",
                )
            )

    if not agent_slug:
        return items

    # Agent summary (agent-scoped)
    agent_result = await session.exec(
        select(UserAgentConfig).where(UserAgentConfig.slug == agent_slug)
    )
    agent_config = agent_result.first()
    if not agent_config:
        return items

    agent_summary = await shadow_summary_service.get_latest_summary(
        session=session,
        entity_type="agent",
        entity_id=agent_config.id,
    )
    if agent_summary:
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
    else:
        reason = _missing_shadow_snapshot_reason(
            entity_type="agent", entity_id=agent_config.id
        )
        logger.warning(reason)
        items.append(
            _missing_shadow_snapshot_item(
                room_id=room_id,
                agent_slug=agent_slug,
                context_type="shadow.agent.summary",
                entity_type="agent",
                entity_id=agent_config.id,
                reason=reason,
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
    binding_row = binding_result.one_or_none()
    binding = (
        binding_row[0]
        if binding_row and not isinstance(binding_row, RoomParticipantBinding)
        else binding_row
    )
    if not binding:
        return items

    if binding.persona_id:
        persona_summary = await shadow_summary_service.get_latest_summary(
            session=session,
            entity_type="persona",
            entity_id=binding.persona_id,
        )
        if persona_summary:
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
        else:
            reason = _missing_shadow_snapshot_reason(
                entity_type="persona", entity_id=binding.persona_id
            )
            logger.warning(reason)
            items.append(
                _missing_shadow_snapshot_item(
                    room_id=room_id,
                    agent_slug=agent_slug,
                    context_type="shadow.persona.summary",
                    entity_type="persona",
                    entity_id=binding.persona_id,
                    reason=reason,
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
        provider_summary = await shadow_summary_service.get_latest_summary(
            session=session,
            entity_type="user_llm_provider",
            entity_id=binding.user_llm_provider_id,
        )
        if provider_summary:
            runtime_payload["user_llm_provider"] = provider_summary.__dict__
        else:
            reason = _missing_shadow_snapshot_reason(
                entity_type="user_llm_provider",
                entity_id=binding.user_llm_provider_id,
            )
            logger.warning(reason)
            runtime_payload["user_llm_provider_missing"] = {
                "missing_shadow_snapshot": True,
                "entity_type": "user_llm_provider",
                "entity_id": str(binding.user_llm_provider_id),
                "reason": reason,
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
