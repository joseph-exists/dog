# Redis Connection Pattern Review

**Date:** 2025-12-30
**Context:** Phase 4 implementation review
**Status:** ✅ Fixed - Ready for MVP

---

## Issues Found and Fixed

### Critical Issues (Blocking)

1. **Syntax Error** - Line 2 called `redis.Redis()` without importing `redis` module
   - ❌ Before: `from redis.asyncio import Redis` → `redis.Redis()`
   - ✅ After: Properly using `Redis()` class directly

2. **Missing Function** - `get_redis()` didn't exist but was imported everywhere
   - ❌ Before: No function defined
   - ✅ After: `async def get_redis() -> Redis` implemented

3. **No Connection Pool** - Created new connection on every call
   - ❌ Before: Direct client instantiation
   - ✅ After: Module-level `ConnectionPool` with 20 max connections

4. **Hardcoded Configuration** - Host/port hardcoded as strings
   - ❌ Before: `host='localhost', port=6379`
   - ✅ After: Uses `settings.REDIS_HOST` and `settings.REDIS_PORT`

---

## Current Implementation Pattern

### Architecture (Following `app/core/db.py`)

```python
# Module-level connection pool (created once on import)
redis_pool = ConnectionPool.from_url(
    f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
    max_connections=20,
    decode_responses=True,
)

# Async accessor function (returns client from pool)
async def get_redis() -> Redis:
    """Returns Redis client from connection pool"""
    return Redis(connection_pool=redis_pool)
```

### Why This Pattern?

1. **Matches Project Convention** - Follows same pattern as `db.py`
2. **Connection Pooling** - Reuses connections across requests
3. **Multi-Worker Safe** - Each worker has own pool (stateless)
4. **Simple Usage** - `redis = await get_redis()` works everywhere
5. **Auto Cleanup** - Pool manages connection lifecycle

### Usage Examples

**In Services (event_emitter.py, websocket_manager.py):**
```python
from app.core.redis import get_redis

async def _publish_to_redis(room_id: uuid.UUID, event: RoomEvent) -> None:
    redis = await get_redis()
    await redis.publish(f"room:{room_id}", json.dumps(message))
    # No explicit close needed - pool handles it
```

**In Route Handlers (future, with dependency injection):**
```python
from typing import Annotated
from fastapi import Depends

async def my_route(
    redis: Annotated[Redis, Depends(get_redis)]
) -> dict:
    await redis.publish("channel", "data")
    return {"status": "published"}
```

---

## Is This Pattern Right for MVP?

### ✅ YES - This is Production-Ready

**Reasons:**

1. **Proven Pattern** - Standard FastAPI/SQLAlchemy connection pooling approach
2. **Scales Horizontally** - Works with multiple workers (no shared state)
3. **Efficient** - Connection pooling prevents connection exhaustion
4. **Simple** - Easy to understand and maintain
5. **Consistent** - Matches existing `db.py` pattern

### What's Good for MVP

- ✅ Connection pooling (20 connections per worker)
- ✅ Graceful degradation (Redis failures logged, don't crash)
- ✅ Environment-based config (`REDIS_HOST`, `REDIS_PORT`)
- ✅ Follows project conventions
- ✅ Auto-reconnection via pool

### What Could Be Enhanced (Post-MVP)

**Not Critical, but Nice to Have:**

1. **Health Checks**
   ```python
   async def check_redis_health() -> bool:
       try:
           redis = await get_redis()
           await redis.ping()
           return True
       except Exception:
           return False
   ```

2. **Redis Sentinel Support** (for HA deployments)
   ```python
   # For production with Redis Sentinel
   from redis.asyncio.sentinel import Sentinel
   ```

3. **Metrics/Monitoring**
   - Track pub/sub message counts
   - Monitor connection pool usage
   - Alert on Redis unavailability

4. **Retry Logic** (for transient failures)
   ```python
   # Retry publish on network errors
   for attempt in range(3):
       try:
           await redis.publish(...)
           break
       except ConnectionError:
           await asyncio.sleep(0.1)
   ```

---

## Configuration

### Environment Variables (.env)

```bash
# For local development (outside Docker)
REDIS_HOST=127.0.0.1  # ✅ Configured in .env
REDIS_PORT=6379       # ✅ Default
```

**Important:** These values are **overridden** in `docker-compose.yml` for containerized environments.

### Docker Compose

```yaml
# Redis service
redis:
  image: redis:8.2-alpine
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]

# Backend service (CRITICAL: Override REDIS_HOST for Docker networking)
backend:
  environment:
    # ... other env vars ...
    - POSTGRES_SERVER=db           # Uses Docker service name
    - REDIS_HOST=redis             # ✅ MUST use Docker service name
    - REDIS_PORT=${REDIS_PORT:-6379}

prestart:
  environment:
    # ... other env vars ...
    - POSTGRES_SERVER=db
    - REDIS_HOST=redis             # ✅ Same override needed
    - REDIS_PORT=${REDIS_PORT:-6379}
```

**Why the Override?**
- Inside Docker containers, `localhost` = the container itself, not other containers
- Containers communicate via **service names** (`redis`, `db`, etc.)
- This matches the existing pattern for Postgres (`POSTGRES_SERVER=db`)

### Settings (app/core/config.py)

```python
class Settings(BaseSettings):
    # Redis Configuration (Phase 4)
    REDIS_HOST: str = "localhost"  # ✅ Added
    REDIS_PORT: int = 6379         # ✅ Added
```

---

## Testing Redis Connectivity

```python
# Quick test to verify Redis is working
from app.core.redis import get_redis
import asyncio

async def test_redis():
    redis = await get_redis()

    # Test ping
    assert await redis.ping() == True

    # Test pub/sub
    await redis.publish("test", "hello")

    print("✅ Redis working!")

asyncio.run(test_redis())
```

---

## Comparison with Database Pattern

| Feature | Database (db.py) | Redis (redis.py) |
|---------|------------------|------------------|
| **Pool** | `sessionmaker` | `ConnectionPool` |
| **Accessor** | `get_async_session()` | `get_redis()` |
| **Returns** | `AsyncGenerator[AsyncSession]` | `Redis` (direct) |
| **DI Compatible** | ✅ Generator for FastAPI | ⚠️ Direct (but works) |
| **Config Source** | `settings.SQLALCHEMY_DATABASE_URI` | `settings.REDIS_HOST/PORT` |
| **Multi-Worker** | ✅ Stateless | ✅ Stateless |

### Why Redis Returns Direct Client vs Generator?

**Pragmatic Choice for Phase 4:**

1. **Usage Context** - Most calls are in services (`event_emitter.py`, `websocket_manager.py`), not route handlers
2. **Simplicity** - `redis = await get_redis()` is cleaner than `async for redis in get_redis(): ...`
3. **Pool Handles Cleanup** - Connection returned to pool automatically
4. **FastAPI Compatible** - Can still use with `Depends()` if needed

**If we wanted generator pattern (like db.py):**
```python
async def get_redis() -> AsyncGenerator[Redis, None]:
    client = Redis(connection_pool=redis_pool)
    try:
        yield client
    finally:
        await client.aclose()
```

But current direct return is simpler for our use case.

---

## Verdict

✅ **Current pattern is CORRECT and PRODUCTION-READY for MVP**

- Fixes all critical issues
- Follows project conventions
- Scales horizontally
- Simple to maintain
- No technical debt

**No changes needed for MVP.** Post-MVP enhancements (health checks, metrics, sentinel) are nice-to-have, not blockers.

---

## Related Files

- `/backend/app/core/redis.py` - Redis connection management ✅
- `/backend/app/core/config.py` - Settings with REDIS_HOST/PORT ✅
- `/backend/app/services/event_emitter.py` - Uses `get_redis()` ✅
- `/backend/app/services/websocket_manager.py` - Uses `get_redis()` ✅
- `/.env` - Contains `REDIS_HOST=localhost` ✅
- `/docker-compose.yml` - Redis service on port 6379 ✅
