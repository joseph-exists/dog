from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class TesserRenderTimeoutError(RuntimeError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _request_tesser_message(
    *,
    request_type: str,
    payload: dict[str, Any] | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    request_id = str(uuid.uuid4())
    request_payload = dict(payload or {})
    request_payload["type"] = request_type
    request_payload["request_id"] = request_id
    request_payload["sent_at"] = _now_iso()

    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.TESSER_RESPONSE_CHANNEL)

    try:
        await redis.publish(settings.TESSER_REQUEST_CHANNEL, json.dumps(request_payload))
        deadline = asyncio.get_running_loop().time() + timeout_seconds

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TesserRenderTimeoutError(
                    f"Tesser render timed out after {timeout_seconds:.1f}s"
                )

            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=min(remaining, 1.0),
            )
            if not message:
                continue

            raw_data = message.get("data")
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode()
            if not isinstance(raw_data, str):
                continue

            try:
                parsed = json.loads(raw_data)
            except json.JSONDecodeError:
                logger.debug("Ignoring non-JSON tesser response payload")
                continue

            if parsed.get("request_id") != request_id:
                continue

            return parsed
    finally:
        await pubsub.unsubscribe(settings.TESSER_RESPONSE_CHANNEL)
        await pubsub.close()


async def list_tesser_scripts(timeout_seconds: float = 10.0) -> list[dict[str, Any]]:
    response = await _request_tesser_message(
        request_type="tesser.scripts.list.request",
        payload={},
        timeout_seconds=timeout_seconds,
    )
    if str(response.get("status") or "") == "error":
        raise RuntimeError(str(response.get("error") or "Failed to list tesser scripts"))
    scripts = response.get("scripts")
    if isinstance(scripts, list):
        return [item for item in scripts if isinstance(item, dict)]
    return []


async def get_tesser_script_help(
    script_name: str, timeout_seconds: float = 10.0
) -> dict[str, Any]:
    return await _request_tesser_message(
        request_type="tesser.script.help.request",
        payload={"script_name": script_name},
        timeout_seconds=timeout_seconds,
    )


async def get_tesser_examples_index(timeout_seconds: float = 10.0) -> dict[str, Any]:
    return await _request_tesser_message(
        request_type="tesser.examples.index.request",
        payload={},
        timeout_seconds=timeout_seconds,
    )


async def request_tesser(
    *,
    script_name: str,
    script_input: dict[str, Any] | None = None,
    room_id: str | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    return await _request_tesser_message(
        request_type="tesser.script.request",
        payload={
            "script_name": script_name,
            "script_input": script_input or {},
            "room_id": room_id,
        },
        timeout_seconds=timeout_seconds,
    )


async def request_tesser_svg(
    *,
    title: str,
    subtitle: str | None = None,
    room_id: str | None = None,
    timeout_seconds: float = 15.0,
) -> dict[str, Any]:
    return await request_tesser(
        script_name="simple_svg",
        script_input={"title": title, "subtitle": subtitle},
        room_id=room_id,
        timeout_seconds=timeout_seconds,
    )
