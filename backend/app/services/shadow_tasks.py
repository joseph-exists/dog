from __future__ import annotations

import logging
import uuid

from sqlmodel import Session

from app.core.db import engine
from app.models import Room, User
from app.services.shadow_exporters import build_room_snapshot
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)


def shadow_room_version_best_effort(
    *,
    room_id: uuid.UUID,
    actor_user_id: uuid.UUID,
    message: str,
) -> None:
    """
    Post-commit best-effort Shadow version write for a room snapshot.

    Intended to be scheduled via FastAPI BackgroundTasks from async routes.
    """
    try:
        with Session(engine) as session:
            room = session.get(Room, room_id)
            if not room:
                logger.debug(f"Shadow room version skipped; room not found: {room_id}")
                return

            owner = session.get(User, room.creator_id)
            actor = session.get(User, actor_user_id) or owner
            if not owner or not actor:
                logger.debug(f"Shadow room version skipped; missing users for room {room_id}")
                return

            snapshot = build_room_snapshot(session=session, room_id=room_id)
            shadow_service.create_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=actor,
                entity_type="room",
                entity_id=room_id,
                entity_data=snapshot,
                message=message,
            )
    except Exception as e:
        logger.warning(f"Shadow room versioning failed for room {room_id}: {e}")

