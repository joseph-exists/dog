# backend/app/services/kennel_event_listener.py
import asyncio
import json
import logging

import redis.asyncio as aioredis
from app.core.config import settings
from app.db import get_session_context
from app.models.workspace import Workspace, WorkspaceStatus
from sqlmodel import select

log = logging.getLogger(__name__)

CHANNEL = settings.KENNEL_REDIS_EVENT_CHANNEL  # "kennel:events"


async def listen():
    r = aioredis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )
    pubsub = r.pubsub()
    await pubsub.subscribe(CHANNEL)
    log.info(f"Subscribed to {CHANNEL}")

    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            data = json.loads(message["data"])
            await _handle(data)
        except Exception as e:
            log.exception(f"kennel event handler error: {e}")


async def _handle(data: dict):
    kennel_name = data.get("env")
    event       = data.get("event")

    if not kennel_name or not event:
        return

    status_map = {
        "created":          None,               # handled by provisioner
        "destroyed":        WorkspaceStatus.destroyed,
        "ws_disconnected":  None,               # could log/metric
        "stop":             WorkspaceStatus.stopped,
    }

    new_status = status_map.get(event)
    if not new_status:
        return

    async with get_session_context() as db:
        result = await db.exec(
            select(Workspace).where(Workspace.kennel_name == kennel_name)
        )
        ws = result.first()
        if ws:
            ws.status = new_status
            await db.commit()
            log.info(f"[{kennel_name}] status → {new_status} via event:{event}")