import asyncio
import json
import logging
from collections.abc import Mapping
from typing import Any

from sqlmodel import select

from app.core.config import settings
from app.core.db import async_session_maker
from app.core.redis import get_redis
from app.models import Workspace, WorkspaceStatus

log = logging.getLogger(__name__)


async def listen(stop_event: asyncio.Event) -> None:
    """
    Subscribe to kennel lifecycle events and reconcile workspace status.
    """
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.KENNEL_REDIS_EVENT_CHANNEL)
    log.info("Subscribed to %s", settings.KENNEL_REDIS_EVENT_CHANNEL)

    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if not message:
                continue

            payload = _decode_message_data(message)
            if payload is None:
                continue

            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                log.debug("Ignoring non-JSON kennel event payload")
                continue

            try:
                await _handle(data)
            except Exception:
                log.exception("kennel event handler error")
    finally:
        await pubsub.unsubscribe(settings.KENNEL_REDIS_EVENT_CHANNEL)
        await pubsub.close()


def _decode_message_data(message: Mapping[str, Any]) -> str | None:
    raw_data = message.get("data")
    if isinstance(raw_data, bytes):
        return raw_data.decode()
    if isinstance(raw_data, str):
        return raw_data
    return None


async def _handle(data: Mapping[str, Any]) -> None:
    kennel_name = data.get("env")
    event = data.get("event")

    if not isinstance(kennel_name, str) or not isinstance(event, str):
        return

    status_map = {
        "destroyed": WorkspaceStatus.destroyed,
        "stop": WorkspaceStatus.stopped,
    }
    new_status = status_map.get(event)
    if new_status is None:
        return

    async with async_session_maker() as session:
        result = await session.exec(
            select(Workspace).where(Workspace.kennel_name == kennel_name)
        )
        workspace = result.first()
        if workspace is None:
            return

        workspace.status = new_status
        session.add(workspace)
        await session.commit()
        log.info("[%s] status -> %s via event:%s", kennel_name, new_status, event)
