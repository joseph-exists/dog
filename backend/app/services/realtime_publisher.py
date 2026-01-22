"""
Shared real-time event publisher for all event-sourced systems.
Used by both Room Chat and CYOA systems.
"""

import json
import logging
from datetime import datetime
from typing import Any
import asyncio

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


async def publish_event_to_redis(
    channel: str,
    event_type: str,
    sequence: int | None,
    payload: dict[str, Any],
    created_at: datetime,
) -> None:
    """
    Publish event to Redis pub/sub for real-time delivery.

    This is a shared utility used by:
    - Room Chat system (event_emitter.py)
    - CYOA Story system (user_story_progress routes)

    Channel naming conventions:
    - Room chat: room:{room_id}
    - CYOA stories: story:{story_id}

    Message format:
    {
        "type": "event",
        "sequence": int | null,  # For room chat; null for CYOA
        "event_type": str,
        "payload": {...},
        "created_at": ISO timestamp
    }

    Failure handling:
    - If Redis unavailable, logs error but does NOT raise exception
    - Clients will catch up via database replay on reconnect
    - This ensures graceful degradation
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            logger.warning(
                "Skipping Redis publish for %s; event loop is closed.",
                channel,
            )
            return
    except RuntimeError:
        logger.warning(
            "Skipping Redis publish for %s; no running event loop.",
            channel,
        )
        return

    try:
        redis = await get_redis()

        message = {
            "type": "event",
            "sequence": sequence,
            "event_type": event_type,
            "payload": payload,
            "created_at": created_at.isoformat(),
        }

        message_json = json.dumps(message)
        result = await redis.publish(channel, message_json)

        logger.info(
            f"Published {event_type} to Redis channel {channel}, "
            f"subscribers: {result}"
        )

        if result == 0:
            logger.warning(
                f"No subscribers for channel {channel}. "
                f"Event will not be delivered in real-time."
            )

    except Exception as e:
        # Don't fail transaction if Redis publish fails
        # Clients will catch up via replay on reconnect
        logger.error(
            f"Failed to publish event to Redis channel {channel}: "
            f"{type(e).__name__}: {e}",
            exc_info=True
        )


async def publish_ephemeral_message(
    channel: str,
    message_type: str,
    payload: dict[str, Any],
) -> None:
    """
    Publish ephemeral (non-persisted) message to Redis.

    Used for:
    - Agent token streaming (message.delta)
    - Typing indicators
    - Presence updates

    These messages are NOT stored in the event log.
    """
    try:
        loop = asyncio.get_running_loop()
        if loop.is_closed():
            logger.warning(
                "Skipping Redis publish for %s; event loop is closed.",
                channel,
            )
            return
    except RuntimeError:
        logger.warning(
            "Skipping Redis publish for %s; no running event loop.",
            channel,
        )
        return

    try:
        redis = await get_redis()

        message = {
            "type": message_type,
            **payload,
        }

        await redis.publish(channel, json.dumps(message))
        logger.debug(f"Published ephemeral {message_type} to {channel}")

    except Exception as e:
        # Gracefully ignore - these are best-effort delivery
        logger.warning(
            f"Failed to publish ephemeral message: {type(e).__name__}: {e}"
        )
