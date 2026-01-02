# CYOA Phase 4 Quick Reference Card
## Real-Time Distribution (WebSocket + Redis Pub/Sub)

**Last Updated:** 2026-01-01
**Status:** 🎯 Implementation Guide
**Prerequisites:** ✅ Phase 1, 2, 3 complete
**Estimated Time:** ~10 hours

---

## Overview

Phase 4 adds real-time event distribution so connected clients receive live updates when:
- Players make choices
- Timeline navigation occurs (undo/jump)
- Game state changes

**Key Technologies:**
- Redis pub/sub for event distribution
- WebSocket for client connections
- Transactional outbox pattern for reliability

---

## Pre-Implementation Checklist

- [ ] Phase 3 complete and tested
- [ ] Redis server accessible (local or cloud)
- [ ] `redis` Python package installed
- [ ] Docker Compose updated with Redis service
- [ ] WebSocket support enabled in FastAPI

---

## Implementation Steps

### Step 1: Add Redis to Infrastructure (30 min)

#### 1.1 Update docker-compose.yml

Add Redis service:

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  redis-data:
```

#### 1.2 Update .env

Add Redis connection string:

```bash
REDIS_URL=redis://redis:6379/0
```

#### 1.3 Add Redis Dependency

```bash
# In backend container
uv add redis
```

---

### Step 2: Create Outbox Model (45 min)

#### 2.1 Add Outbox Model to models.py

Add this AFTER UserStoryProgress models, BEFORE relationship definitions:

```python
# ==================== Outbox Models (REAL-TIME) ====================

class OutboxBase(SQLModel):
    """
    Base model for transactional outbox.
    Ensures event publication is atomic with database commit.
    """
    topic: str = Field(max_length=255)  # e.g., "story:{story_id}"
    event_type: str = Field(max_length=100)  # "HeadMoved", "ChoiceMade"
    payload: dict[str, Any] = Field(sa_column=Column(JSON))


class OutboxCreate(OutboxBase):
    """Input model for creating outbox event"""
    pass


class OutboxUpdate(SQLModel):
    """Update model for Outbox (used by publisher)"""
    published_at: datetime | None = Field(default=None)
    retry_count: int | None = Field(default=None)
    last_error: str | None = Field(default=None)


class Outbox(OutboxBase, table=True):
    """
    Database model for transactional outbox.

    Events written here in same transaction as domain changes.
    Background publisher reads unpublished events and pushes to Redis.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    created_at: datetime = Field(default_factory=datetime.now)
    published_at: datetime | None = Field(default=None)

    # Retry tracking
    retry_count: int = Field(default=0)
    last_error: str | None = Field(default=None, max_length=1000)


class OutboxPublic(OutboxBase):
    """Public API response model for Outbox (admin only)"""
    id: uuid.UUID
    created_at: datetime
    published_at: datetime | None
    retry_count: int
    last_error: str | None


class OutboxesPublic(SQLModel):
    """Collection response for Outboxes"""
    data: list[OutboxPublic]
    count: int
```

#### 2.2 Create Alembic Migration

```bash
# In backend container
alembic revision --autogenerate -m "Add Outbox model for real-time event distribution"
```

**Review migration file** - verify it includes:
- `outbox` table creation
- Index on `published_at` for unpublished events query
- All columns: id, topic, event_type, payload, created_at, published_at, retry_count, last_error

#### 2.3 Apply Migration

```bash
alembic upgrade head
alembic current  # Verify migration applied
```

---

### Step 3: Create Redis Connection Module (30 min)

#### 3.1 Create backend/app/core/redis.py

```python
"""Redis connection management."""

import redis.asyncio as redis
from app.core.config import settings

redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """
    Get Redis client instance (singleton pattern).

    Returns:
        Redis client configured from settings.REDIS_URL

    Raises:
        redis.ConnectionError: If Redis is unavailable
    """
    global redis_client

    if redis_client is None:
        redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )

    return redis_client


async def close_redis() -> None:
    """Close Redis connection (call on app shutdown)."""
    global redis_client

    if redis_client is not None:
        await redis_client.close()
        redis_client = None
```

#### 3.2 Update backend/app/core/config.py

Add Redis URL to settings:

```python
class Settings(BaseSettings):
    # ... existing fields ...

    REDIS_URL: str = Field(default="redis://localhost:6379/0")
```

#### 3.3 Update backend/app/main.py

Add Redis lifecycle hooks:

```python
from app.core.redis import close_redis

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown."""
    await close_redis()
```

---

### Step 4: Create Outbox Publisher Worker (90 min)

#### 4.1 Create backend/app/workers/__init__.py

```python
"""Background workers for async tasks."""
```

#### 4.2 Create backend/app/workers/outbox_publisher.py

```python
"""Outbox publisher - polls database and publishes to Redis."""

import asyncio
import json
import logging
from datetime import datetime

from sqlmodel import select
from app.core.db import engine
from app.core.redis import get_redis
from app.models import Outbox
from sqlmodel import Session

logger = logging.getLogger(__name__)


async def publish_outbox_events():
    """
    Background worker that polls outbox table and publishes to Redis.

    Runs continuously with 100ms poll interval.
    Handles retries and error logging.
    """
    logger.info("Starting outbox publisher worker")

    redis = await get_redis()

    while True:
        try:
            with Session(engine) as session:
                # Get unpublished events (oldest first)
                statement = (
                    select(Outbox)
                    .where(Outbox.published_at == None)  # noqa: E711
                    .order_by(Outbox.created_at.asc())
                    .limit(100)
                )

                events = session.exec(statement).all()

                for event in events:
                    try:
                        # Publish to Redis
                        message = json.dumps({
                            "event_id": str(event.id),
                            "event_type": event.event_type,
                            "payload": event.payload,
                            "published_at": datetime.now().isoformat()
                        })

                        await redis.publish(event.topic, message)

                        # Mark as published
                        event.published_at = datetime.now()
                        session.add(event)
                        session.commit()

                        logger.debug(f"Published event {event.id} to {event.topic}")

                    except Exception as e:
                        # Retry tracking
                        event.retry_count += 1
                        event.last_error = str(e)[:1000]  # Truncate
                        session.add(event)
                        session.commit()

                        logger.error(f"Failed to publish event {event.id}: {e}")

                        # Give up after 10 retries
                        if event.retry_count >= 10:
                            logger.error(f"Giving up on event {event.id} after 10 retries")
                            event.published_at = datetime.now()  # Mark as published to stop retrying
                            session.add(event)
                            session.commit()

        except Exception as e:
            logger.error(f"Outbox publisher error: {e}")

        await asyncio.sleep(0.1)  # 100ms poll interval


async def start_outbox_publisher():
    """Entry point for outbox publisher (call from main.py)."""
    await publish_outbox_events()
```

#### 4.3 Add Worker Startup to backend/app/main.py

```python
import asyncio
from contextlib import asynccontextmanager
from app.workers.outbox_publisher import start_outbox_publisher

# Background task holder
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    task = asyncio.create_task(start_outbox_publisher())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

    yield

    # Shutdown
    await close_redis()
    for task in background_tasks:
        task.cancel()


app = FastAPI(lifespan=lifespan)  # Update this line
```

---

### Step 5: Create WebSocket Endpoint (60 min)

#### 5.1 Create backend/app/api/routes/websocket.py

```python
"""WebSocket endpoints for real-time story updates."""

import json
import logging
from typing import Any
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from app.core.redis import get_redis
from app.api.deps import SessionDep, get_current_user
from app.models import User

router = APIRouter()
logger = logging.getLogger(__name__)


async def authenticate_websocket_token(token: str, session: SessionDep) -> User:
    """
    Authenticate WebSocket connection using JWT token.

    Args:
        token: JWT access token from query param
        session: Database session

    Returns:
        Authenticated User

    Raises:
        HTTPException: If token is invalid
    """
    # Use existing auth logic from deps.py
    from app.api.deps import get_current_user
    from app.core import security
    from sqlmodel import select

    try:
        payload = security.decode_token(token)
        token_data = security.TokenPayload(**payload)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    return user


@router.websocket("/stories/{story_id}/stream")
async def story_stream(
    websocket: WebSocket,
    story_id: uuid.UUID,
    token: str = Query(..., description="JWT access token"),
):
    """
    WebSocket endpoint for real-time story updates.

    Subscribes to Redis topic: story:{story_id}

    Events pushed to clients:
    - ChoiceMade: New choice appended to timeline
    - HeadMoved: Timeline navigation (undo/jump)
    - StateChanged: Story state updated

    Query params:
        token: JWT access token for authentication

    Example client usage:
        ws = new WebSocket("ws://localhost:8000/api/v1/ws/stories/{id}/stream?token={jwt}")
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log(data.event_type, data.payload)
        }
    """
    # Note: Proper authentication requires session, but WebSocket doesn't have SessionDep
    # For MVP, we'll validate token but skip full auth
    # TODO: Implement proper WebSocket auth

    await websocket.accept()
    logger.info(f"WebSocket connected for story {story_id}")

    redis = await get_redis()
    pubsub = redis.pubsub()
    topic = f"story:{story_id}"

    try:
        await pubsub.subscribe(topic)
        logger.info(f"Subscribed to {topic}")

        # Send connection confirmation
        await websocket.send_text(json.dumps({
            "event_type": "Connected",
            "payload": {"story_id": str(story_id)}
        }))

        # Listen for Redis messages
        async for message in pubsub.listen():
            if message["type"] == "message":
                # Forward Redis message to WebSocket client
                await websocket.send_text(message["data"])

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for story {story_id}")
    except Exception as e:
        logger.error(f"WebSocket error for story {story_id}: {e}")
    finally:
        await pubsub.unsubscribe(topic)
        await pubsub.close()
```

#### 5.2 Register WebSocket Router in backend/app/api/main.py

```python
from app.api.routes import websocket

api_router.include_router(
    websocket.router,
    prefix="/ws",
    tags=["websocket"]
)
```

---

### Step 6: Add Outbox CRUD Functions (45 min)

#### 6.1 Add to backend/app/crud.py

```python
# ==================== Outbox CRUD (Phase 4) ====================

def create_outbox_event(
    *,
    session: Session,
    topic: str,
    event_type: str,
    payload: dict[str, Any]
) -> Outbox:
    """
    Create outbox event in same transaction as domain operation.

    This is called from within choice/undo/jump endpoints to ensure
    event publication is atomic with state changes.

    Args:
        session: Database session (must be in active transaction)
        topic: Redis topic (e.g., "story:{story_id}")
        event_type: Event type (e.g., "ChoiceMade", "HeadMoved")
        payload: Event payload (serializable dict)

    Returns:
        Created Outbox event (unpublished)

    Example:
        # In endpoint, after creating choice:
        outbox_event = crud.create_outbox_event(
            session=session,
            topic=f"story:{story_id}",
            event_type="ChoiceMade",
            payload={
                "progress_id": str(progress.id),
                "choice_id": str(user_choice.id),
                "head_version": progress.head_version
            }
        )
        session.add(outbox_event)
        session.commit()  # Commits both choice AND outbox event atomically
    """
    outbox = Outbox(
        topic=topic,
        event_type=event_type,
        payload=payload
    )
    return outbox


def get_unpublished_outbox_events(
    *, session: Session, limit: int = 100
) -> list[Outbox]:
    """
    Get unpublished outbox events for publisher worker.

    Args:
        session: Database session
        limit: Max events to return

    Returns:
        List of unpublished events (oldest first)
    """
    statement = (
        select(Outbox)
        .where(Outbox.published_at == None)  # noqa: E711
        .order_by(Outbox.created_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())
```

---

### Step 7: Update Choice Endpoint with Outbox (45 min)

#### 7.1 Modify make_story_choice in backend/app/api/routes/user_story_progress.py

Find the `make_story_choice` function and modify the transaction section:

**BEFORE:**
```python
    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

**AFTER:**
```python
    # NEW: Add outbox event in same transaction
    outbox_event = crud.create_outbox_event(
        session=session,
        topic=f"story:{story_id}",
        event_type="ChoiceMade",
        payload={
            "progress_id": str(progress.id),
            "user_persona_id": str(user_persona_id),
            "choice_id": str(user_choice.id),
            "choice_text": user_choice.choice_text,
            "head_version": progress.head_version,
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state,
            "is_completed": progress.is_completed
        }
    )
    session.add(outbox_event)

    session.add(progress)
    session.commit()  # Commits choice, progress, AND outbox event atomically
    session.refresh(progress)

    return progress
```

---

### Step 8: Update Undo/Jump Endpoints with Outbox (60 min)

#### 8.1 Modify undo_story_choice in backend/app/api/routes/user_story_progress.py

Add outbox event before commit:

```python
    # ... existing undo logic ...

    # NEW: Add outbox event
    outbox_event = crud.create_outbox_event(
        session=session,
        topic=f"story:{story_id}",
        event_type="HeadMoved",
        payload={
            "progress_id": str(progress.id),
            "user_persona_id": str(user_persona_id),
            "operation": "undo",
            "old_head_id": str(current_choice.id) if current_choice else None,
            "new_head_id": str(progress.head_choice_id) if progress.head_choice_id else None,
            "head_version": progress.head_version,
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state
        }
    )
    session.add(outbox_event)

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

#### 8.2 Modify jump_story_head in backend/app/api/routes/user_story_progress.py

Add outbox event before commit:

```python
    # ... existing jump logic ...

    # NEW: Add outbox event
    outbox_event = crud.create_outbox_event(
        session=session,
        topic=f"story:{story_id}",
        event_type="HeadMoved",
        payload={
            "progress_id": str(progress.id),
            "user_persona_id": str(user_persona_id),
            "operation": "jump",
            "old_head_id": str(old_head_id) if old_head_id else None,
            "new_head_id": str(progress.head_choice_id) if progress.head_choice_id else None,
            "head_version": progress.head_version,
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state
        }
    )
    session.add(outbox_event)

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

---

## Testing

### 8.1 Create backend/app/tests/test_outbox.py

```python
"""Tests for outbox pattern and real-time distribution."""

import uuid
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import Outbox
from app import crud


def test_outbox_event_created_with_choice(
    client: TestClient, session: Session, user_persona_with_story
):
    """Test that making a choice creates an outbox event in same transaction."""
    user_persona_id, story_id = user_persona_with_story

    # Get current node and available choices
    response = client.get(f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node")
    assert response.status_code == 200
    current_node = response.json()

    # Make choice
    choice_id = current_node["choices"][0]["id"]
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}"
    )
    assert response.status_code == 200

    # Verify outbox event was created
    statement = select(Outbox).where(Outbox.topic == f"story:{story_id}")
    outbox_events = session.exec(statement).all()

    assert len(outbox_events) >= 1
    latest_event = outbox_events[-1]

    assert latest_event.event_type == "ChoiceMade"
    assert latest_event.payload["choice_id"] is not None
    assert latest_event.payload["head_version"] == 1
    assert latest_event.published_at is None  # Not published yet


def test_outbox_event_created_on_undo(
    client: TestClient, session: Session, user_persona_with_progress
):
    """Test that undo creates HeadMoved outbox event."""
    user_persona_id, story_id = user_persona_with_progress

    # Undo
    response = client.post(f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/undo")
    assert response.status_code == 200

    # Verify outbox event
    statement = select(Outbox).where(
        Outbox.topic == f"story:{story_id}",
        Outbox.event_type == "HeadMoved"
    )
    events = session.exec(statement).all()

    assert len(events) >= 1
    latest_event = events[-1]

    assert latest_event.payload["operation"] == "undo"
    assert "old_head_id" in latest_event.payload
    assert "new_head_id" in latest_event.payload


def test_outbox_event_created_on_jump(
    client: TestClient, session: Session, user_persona_with_progress
):
    """Test that jump creates HeadMoved outbox event."""
    user_persona_id, story_id = user_persona_with_progress

    # Get timeline to find ancestor
    response = client.get(f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/timeline")
    assert response.status_code == 200
    timeline = response.json()

    # Jump to story start
    response = client.post(
        f"/api/v1/user-personas/{user_persona_id}/stories/{story_id}/jump",
        json={
            "choice_id": None,
            "expected_head_version": timeline["head_version"]
        }
    )
    assert response.status_code == 200

    # Verify outbox event
    statement = select(Outbox).where(
        Outbox.topic == f"story:{story_id}",
        Outbox.event_type == "HeadMoved"
    )
    events = session.exec(statement).all()

    latest_event = events[-1]
    assert latest_event.payload["operation"] == "jump"
    assert latest_event.payload["new_head_id"] is None  # Jumped to start


@pytest.mark.asyncio
async def test_outbox_publisher_publishes_events(session: Session):
    """Test that outbox publisher marks events as published."""
    # Create test outbox event
    outbox = Outbox(
        topic="test-topic",
        event_type="TestEvent",
        payload={"test": "data"}
    )
    session.add(outbox)
    session.commit()

    # Import and run publisher once (not in loop)
    from app.workers.outbox_publisher import publish_outbox_events
    from app.core.redis import get_redis

    # Run publisher for 1 second
    task = asyncio.create_task(publish_outbox_events())
    await asyncio.sleep(1)
    task.cancel()

    # Verify event was published
    session.refresh(outbox)
    assert outbox.published_at is not None
    assert outbox.retry_count == 0


def test_websocket_connection(client: TestClient, user_token_headers):
    """Test WebSocket connection (basic connectivity)."""
    # Extract token from headers
    token = user_token_headers["Authorization"].replace("Bearer ", "")

    with client.websocket_connect(f"/api/v1/ws/stories/{uuid.uuid4()}/stream?token={token}") as websocket:
        # Should receive connection confirmation
        data = websocket.receive_json()
        assert data["event_type"] == "Connected"
```

### 8.2 Run Tests

```bash
# In backend container
pytest app/tests/test_outbox.py -v

# Expected output:
# test_outbox_event_created_with_choice PASSED
# test_outbox_event_created_on_undo PASSED
# test_outbox_event_created_on_jump PASSED
# test_outbox_publisher_publishes_events PASSED
# test_websocket_connection PASSED
```

---

## Verification Checklist

After completing all steps, verify:

- [ ] Redis service running and accessible
- [ ] Outbox model created and migrated
- [ ] Outbox publisher worker starts with app
- [ ] WebSocket endpoint accepts connections
- [ ] Making choice creates outbox event
- [ ] Undo creates HeadMoved event
- [ ] Jump creates HeadMoved event
- [ ] Outbox events get published to Redis
- [ ] WebSocket clients receive published events
- [ ] All tests pass

---

## Manual Testing

### Test Real-Time Updates

**Terminal 1 - Redis Monitor:**
```bash
docker compose exec redis redis-cli
127.0.0.1:6379> SUBSCRIBE story:*
```

**Terminal 2 - Make Choice:**
```bash
curl -X POST "http://localhost:8000/api/v1/user-personas/{id}/stories/{id}/choices/{id}" \
  -H "Authorization: Bearer {token}"
```

**Expected:** Terminal 1 receives message:
```
1) "message"
2) "story:{story_id}"
3) "{\"event_type\":\"ChoiceMade\",\"payload\":{...}}"
```

### Test WebSocket Client

Create `test_ws.html`:

```html
<!DOCTYPE html>
<html>
<body>
  <h1>Story WebSocket Test</h1>
  <pre id="output"></pre>

  <script>
    const storyId = "YOUR_STORY_ID";
    const token = "YOUR_JWT_TOKEN";
    const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/stories/${storyId}/stream?token=${token}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      document.getElementById("output").textContent += JSON.stringify(data, null, 2) + "\n\n";
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };
  </script>
</body>
</html>
```

Open in browser, make choice in another tab, verify event appears.

---

## Troubleshooting

### Problem: Redis connection refused

**Solution:**
```bash
# Check Redis is running
docker compose ps redis

# Check logs
docker compose logs redis

# Restart Redis
docker compose restart redis
```

### Problem: Outbox events not publishing

**Solution:**
```bash
# Check worker is running
docker compose logs backend | grep "outbox publisher"

# Check for unpublished events
docker compose exec backend bash
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT * FROM outbox WHERE published_at IS NULL;"

# Check retry errors
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c "SELECT id, event_type, retry_count, last_error FROM outbox WHERE retry_count > 0;"
```

### Problem: WebSocket disconnects immediately

**Solution:**
- Check JWT token is valid
- Check CORS settings in main.py
- Check Redis is accessible from backend
- Check browser console for errors

### Problem: Events published but WebSocket not receiving

**Solution:**
- Verify WebSocket subscribed to correct topic
- Check Redis subscription: `docker compose exec redis redis-cli` then `PUBSUB CHANNELS`
- Check outbox payload format is valid JSON

---

## Quick Command Reference

```bash
# Check Redis
docker compose exec redis redis-cli ping                    # Should return PONG

# Monitor Redis pub/sub
docker compose exec redis redis-cli
> SUBSCRIBE story:*                                          # Listen to all story events

# Check outbox status
docker compose exec backend bash
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT event_type, COUNT(*) FROM outbox GROUP BY event_type;"

# Check unpublished events
psql $POSTGRES_SERVER -U $POSTGRES_USER -d $POSTGRES_DB -c \
  "SELECT COUNT(*) FROM outbox WHERE published_at IS NULL;"

# Test WebSocket with wscat
npm install -g wscat
wscat -c "ws://localhost:8000/api/v1/ws/stories/{id}/stream?token={jwt}"
```

---

## Time Breakdown

| Step | Task | Time |
|------|------|------|
| 1 | Add Redis to infrastructure | 30 min |
| 2 | Create Outbox model & migration | 45 min |
| 3 | Create Redis connection module | 30 min |
| 4 | Create outbox publisher worker | 90 min |
| 5 | Create WebSocket endpoint | 60 min |
| 6 | Add outbox CRUD functions | 45 min |
| 7 | Update choice endpoint | 45 min |
| 8 | Update undo/jump endpoints | 60 min |
| 9 | Testing | 60 min |
| **Total** | | **~10 hours** |

---

## Success Criteria

✅ **Phase 4 Complete When:**
1. Redis service running in Docker Compose
2. Outbox model exists and migrated
3. Outbox publisher worker running
4. WebSocket endpoint accepts connections
5. All endpoints (choice/undo/jump) create outbox events
6. Events published to Redis within 200ms
7. WebSocket clients receive events in real-time
8. All tests pass (5 tests minimum)
9. Manual testing shows live updates working
10. No errors in backend logs

---

## Next Steps

After Phase 4 is complete and tested:
1. Review performance (outbox publish latency)
2. Test with multiple concurrent WebSocket clients
3. Proceed to Phase 5 (Full Event Sourcing)

---

**Questions? See:**
- CYOA_MIGRATION_PLAN.md - Overall strategy
- CYOA_MIGRATION_ADDENDUM.md - TinyFoot patterns
- backend/docs/RULES.md - Backend conventions
