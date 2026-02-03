"""
Redis Connection Management

Provides async Redis client for:
- Event pub/sub (Phase 4 streaming)
- Session management
- Caching (future)

Pattern follows app/core/db.py for consistency.
"""
import asyncio
import logging
import weakref
from collections.abc import AsyncGenerator

from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis_pools: dict[int, ConnectionPool] = {}
_loop_refs: dict[int, weakref.ReferenceType[asyncio.AbstractEventLoop]] = {}


def _create_pool() -> ConnectionPool:
    #logger.info(
    #    "[REDIS_INIT] Creating Redis connection pool: %s:%s",
    #    settings.REDIS_HOST,
    #    settings.REDIS_PORT,
    #)
    pool = ConnectionPool.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        max_connections=20,
        # decode_responses=True,  # Automatically decode bytes to strings
    )
    #logger.info("[REDIS_INIT] Redis connection pool created: %s", pool)
    return pool


def _get_pool_for_loop(loop: asyncio.AbstractEventLoop) -> ConnectionPool:
    key = id(loop)
    ref = _loop_refs.get(key)
    pool = _redis_pools.get(key)
    if ref is not None and ref() is loop and pool is not None and not loop.is_closed():
        return pool
    pool = _create_pool()
    _redis_pools[key] = pool
    _loop_refs[key] = weakref.ref(loop)
    return pool


async def get_redis() -> Redis:
    """
    Get async Redis client from connection pool.

    Used throughout Phase 4 for:
    - Publishing events to Redis pub/sub (event_emitter.py)
    - WebSocket connection management (websocket_manager.py)
    - Agent token streaming

    Connection pooling ensures efficient resource usage across workers.

    Usage:
        redis = await get_redis()
        await redis.publish("room:123", json.dumps(message))
        # Note: Client auto-closes when garbage collected
        # Pool manages connection lifecycle

    Note: This returns a client directly (not a generator) because
    event_emitter.py and websocket_manager.py use it in non-dependency
    injection contexts where they can't use 'async for' generators.
    """
    loop = asyncio.get_running_loop()
    pool = _get_pool_for_loop(loop)
    #logger.debug(f"[REDIS_GET] Creating Redis client from pool")
    client = Redis(connection_pool=pool)
    #logger.debug(f"[REDIS_GET] Redis client created: {client}")
    return client
