from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ContextItem:
    """Normalized context payload tied to a room and optional agent scope."""

    id: str
    room_id: uuid.UUID
    agent_slug: str | None
    context_type: str
    payload: dict[str, Any]
    source: str
    created_at: datetime
    expires_at: datetime | None = None


class ContextItemStore(Protocol):
    async def add(self, item: ContextItem) -> None:
        ...

    async def list(
        self, *, room_id: uuid.UUID, agent_slug: str | None = None
    ) -> list[ContextItem]:
        ...

    async def delete(self, *, room_id: uuid.UUID, context_id: str) -> bool:
        ...


@dataclass
class InMemoryContextStore:
    """Simple in-memory context store for tests and development."""

    _items: dict[uuid.UUID, list[ContextItem]] = field(default_factory=dict)

    async def add(self, item: ContextItem) -> None:
        self._items.setdefault(item.room_id, []).append(item)

    async def list(
        self, *, room_id: uuid.UUID, agent_slug: str | None = None
    ) -> list[ContextItem]:
        items = self._items.get(room_id, [])
        if agent_slug is None:
            return [item for item in items if item.agent_slug is None]
        return [
            item for item in items if item.agent_slug is None or item.agent_slug == agent_slug
        ]

    async def delete(self, *, room_id: uuid.UUID, context_id: str) -> bool:
        items = self._items.get(room_id, [])
        original_len = len(items)
        self._items[room_id] = [item for item in items if item.id != context_id]
        return len(self._items[room_id]) != original_len


@dataclass
class RedisContextStore:
    """Redis-backed context store compatible with event-emitter Redis usage."""

    key_prefix: str = "room"
    key_suffix: str = "contexts"

    async def add(self, item: ContextItem) -> None:
        try:
            redis = await get_redis()
            key = self._key(item.room_id)
            await redis.rpush(key, json.dumps(self._serialize(item)))
        except Exception as exc:
            logger.warning(f"Failed to add context item to Redis: {exc}")

    async def list(
        self, *, room_id: uuid.UUID, agent_slug: str | None = None
    ) -> list[ContextItem]:
        try:
            redis = await get_redis()
            key = self._key(room_id)
            raw_items = await redis.lrange(key, 0, -1)
        except Exception as exc:
            logger.warning(f"Failed to read context items from Redis: {exc}")
            return []

        items: list[ContextItem] = []
        now = datetime.now(tz=timezone.utc)
        for raw in raw_items:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                item = self._deserialize(json.loads(raw))
            except Exception as exc:
                logger.warning(f"Failed to decode context item: {exc}")
                continue
            if item.expires_at and item.expires_at <= now:
                continue
            items.append(item)

        if agent_slug is None:
            return [item for item in items if item.agent_slug is None]
        return [
            item for item in items if item.agent_slug is None or item.agent_slug == agent_slug
        ]

    async def delete(self, *, room_id: uuid.UUID, context_id: str) -> bool:
        try:
            redis = await get_redis()
            key = self._key(room_id)
            raw_items = await redis.lrange(key, 0, -1)
        except Exception as exc:
            logger.warning(f"Failed to read context items from Redis: {exc}")
            return False

        filtered: list[str] = []
        removed = False
        for raw in raw_items:
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            try:
                data = json.loads(raw)
            except Exception:
                filtered.append(raw)
                continue
            if data.get("id") == context_id:
                removed = True
                continue
            filtered.append(raw if isinstance(raw, str) else json.dumps(data))

        if not removed:
            return False

        try:
            await redis.delete(key)
            if filtered:
                await redis.rpush(key, *filtered)
        except Exception as exc:
            logger.warning(f"Failed to rewrite context items in Redis: {exc}")
            return False

        return True

    def _key(self, room_id: uuid.UUID) -> str:
        return f"{self.key_prefix}:{room_id}:{self.key_suffix}"

    def _serialize(self, item: ContextItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "room_id": str(item.room_id),
            "agent_slug": item.agent_slug,
            "context_type": item.context_type,
            "payload": item.payload,
            "source": item.source,
            "created_at": item.created_at.isoformat(),
            "expires_at": item.expires_at.isoformat() if item.expires_at else None,
        }

    def _deserialize(self, data: dict[str, Any]) -> ContextItem:
        created_at = datetime.fromisoformat(data["created_at"])
        expires_at = (
            datetime.fromisoformat(data["expires_at"])
            if data.get("expires_at")
            else None
        )
        return ContextItem(
            id=data["id"],
            room_id=uuid.UUID(data["room_id"]),
            agent_slug=data.get("agent_slug"),
            context_type=data["context_type"],
            payload=data["payload"],
            source=data["source"],
            created_at=created_at,
            expires_at=expires_at,
        )
