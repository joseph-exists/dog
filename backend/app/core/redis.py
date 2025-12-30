"""
Redis Connection Management

Provides async Redis client for:
- Event pub/sub (Phase 4 streaming)
- Session management
- Caching (future)

Pattern follows app/core/db.py for consistency.
"""
from typing import AsyncGenerator

from redis.asyncio import Redis, ConnectionPool

from app.core.config import settings

# Create connection pool at module level
# This is reused across all connections for efficiency
redis_pool = ConnectionPool.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    max_connections=20,
    decode_responses=True,  # Automatically decode bytes to strings
)


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
    return Redis(connection_pool=redis_pool)
