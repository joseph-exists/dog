# Phase 4 Implementation Plan: Real-Time Streaming

**Duration:** 6-8 days
**Goal:** Enable real-time multi-user collaboration with WebSocket streaming, agent token streaming, and seamless reconnection.

## Executive Summary

### Deliverables
- Redis pub/sub integration for multi-worker event fanout
- AG-UI compliant WebSocket endpoint with session management
- Token-by-token agent response streaming
- Sequence-based reconnection and event replay
- Frontend useRoomStream hook for real-time updates
- Backpressure handling for slow consumers
- Load testing for 50+ concurrent users

### Success Criteria
✅ Multiple users see messages in real-time across workers
✅ Agent responses stream token-by-token to all room participants
✅ Disconnected clients reconnect and replay missed events seamlessly
✅ No duplicate or dropped events under normal conditions
✅ System handles 50+ concurrent WebSocket connections with <100ms latency (p95)
✅ Graceful degradation when Redis unavailable (events still persisted)

---

## Phases 1-3 Status (Complete ✅)

### Phase 1: Event Sourcing Infrastructure
- `room_events` table: Append-only log with per-room `room_sequence`
- Projection tables: `rooms`, `room_participants`, `room_messages`
- Event emitter service: Transactional writes with `session.flush()`
- Route-level transactions: `AsyncSessionTransactionDep` pattern

### Phase 2: Agent Integration
- StoryAdvisor agent with room-aware context
- Agent registry and runner services
- Context provider for building agent deps
- Agent responses persisted as `room_message.agent` events

### Phase 3: Frontend UI
- Room components with participant list
- Message rendering with sender attribution
- Message input and submission
- Agent toggling and room navigation

### Key Integration Points for Phase 4

1. [x] **Event Emitter** (`app/services/event_emitter.py`):
   - Already has placeholder comment for Redis pub/sub (line 138-139)
   - `emit_event()` function will be extended to publish to Redis

2. [x] **Models** (`app/models.py`):
   - `RoomEvent.room_sequence` exists for ordering ✅
   - No schema changes required for Phase 4 ✅

3. [x] **Agent Runner** (`app/services/agent_runner.py`):
   - Will be extended to support streaming with `agent.run_stream()`
   - Token chunks will be published to Redis for real-time delivery

4. [x] **Frontend Hooks**:
   - New `useRoomStream` hook for WebSocket management
   - Existing `useRoom` and `useRoomMessages` will integrate with streaming

---

## Implementation Order (Dependencies)

```
1. Redis Event Publisher (extends existing event_emitter.py)
   └─ app/services/event_emitter.py (modify)
   └─ app/core/redis.py (verify)

2. WebSocket Connection Manager (infrastructure)
   └─ app/services/websocket_manager.py (new)

3. AG-UI Protocol Handler (WebSocket endpoint)
   └─ app/api/routes/websocket.py (new)
   └─ Depends on: 1, 2

4. Agent Streaming Service (extends agent_runner.py)
   └─ app/services/agent_runner.py (modify)
   └─ Depends on: 1

5. Reconnection & Replay Handler
   └─ app/services/event_replay.py (new)
   └─ Depends on: 3

6. Frontend WebSocket Hook
   └─ frontend/src/hooks/useRoomStream.ts (new)
   └─ Depends on: 3

7. Frontend UI Integration
   └─ Modify: frontend/src/components/Rooms/*.tsx
   └─ Depends on: 6

8. Load Testing & Optimization
   └─ backend/tests/load/test_websocket_load.py (new)
   └─ Depends on: 1-7
```

---

## [x] Deliverable 1: Redis Event Publisher

**File:** `app/services/event_emitter.py` (modify)
**Purpose:** Publish events to Redis for real-time fanout
**Dependencies:** Redis connection (Phase 0 complete)

### Implementation Changes

```python
# Add at top of file
from app.core.redis import get_redis
import json

# Modify emit_event() function (after line 136)
async def emit_event(
    session: AsyncSession,
    room_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
    enrichment_metadata: dict[str, Any] | None = None,
) -> RoomEvent:
    """
    Emit a room event and update projections transactionally.

    Phase 4 Enhancement: Publishes event to Redis after transaction flush
    for real-time delivery to WebSocket clients.
    """
    # ... existing code up to session.flush() ...

    await session.flush()

    # Phase 4: Publish to Redis for real-time streaming
    await _publish_to_redis(room_id, event)

    return event


async def _publish_to_redis(room_id: uuid.UUID, event: RoomEvent) -> None:
    """
    Publish event to Redis pub/sub for real-time delivery.

    This enables multi-worker fanout - all workers subscribed to the room
    channel will receive the event and forward to their connected WebSocket clients.

    Channel naming: room:{room_id}

    Message format (AG-UI compatible):
    {
        "type": "event",
        "sequence": room_sequence,
        "event_type": event_type,
        "payload": {...},
        "created_at": ISO timestamp
    }

    Failure handling:
    - If Redis unavailable, logs error but does NOT fail transaction
    - Event is still persisted in Postgres (clients will catch up via replay)
    - This ensures graceful degradation
    """
    try:
        redis = await get_redis()

        message = {
            "type": "event",
            "sequence": event.room_sequence,
            "event_type": event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }

        channel = f"room:{room_id}"
        await redis.publish(channel, json.dumps(message))

    except Exception as e:
        # Don't fail transaction if Redis publish fails
        # Clients will catch up via replay on reconnect
        logger.warning(f"Failed to publish event to Redis: {e}")
```

### [x] Agent Token Streaming Support

```python
async def publish_agent_token(
    room_id: uuid.UUID,
    agent_name: str,
    token: str,
) -> None:
    """
    Publish a single token from agent streaming.

    This is an EPHEMERAL message (not persisted to Postgres).
    Used for real-time token-by-token streaming during agent responses.

    Final complete message is still persisted via room_message.agent event.

    Message format (AG-UI compatible):
    {
        "type": "message.delta",
        "agent_name": str,
        "content": str (single token)
    }
    """
    try:
        redis = await get_redis()

        message = {
            "type": "message.delta",
            "agent_name": agent_name,
            "content": token,
        }

        channel = f"room:{room_id}"
        await redis.publish(channel, json.dumps(message))

    except Exception as e:
        # Gracefully ignore - full message will be delivered via event
        logger.debug(f"Failed to publish token to Redis: {e}")
```

### Acceptance Criteria
- [x] `emit_event()` publishes to Redis channel `room:{room_id}`
- [x] Message format is AG-UI compatible
- [x] Redis failures don't break transaction (graceful degradation)
- [x] `publish_agent_token()` sends ephemeral deltas
- [x] Token publish failures are logged at debug level (not warnings)

---

## [x] Deliverable 2: WebSocket Connection Manager

**File:** `app/services/websocket_manager.py` (new)
**Purpose:** Manage WebSocket connections and Redis subscriptions per worker
**Dependencies:** Redis connection

### Complete Implementation

```python
"""
WebSocket Connection Manager: Per-worker connection and subscription management.

This service manages:
1. Active WebSocket connections on this worker
2. Redis pub/sub subscriptions for active rooms
3. Fanout from Redis to connected clients
4. Connection lifecycle (connect, disconnect, subscribe, unsubscribe)

Architecture:
- Each worker maintains its own connection manager instance
- No shared state between workers (stateless design)
- Redis pub/sub provides cross-worker event fanout
- Reconnecting clients may land on different worker (no sticky sessions)
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket
from redis.asyncio.client import PubSub

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections and Redis subscriptions for this worker.

    NOT thread-safe - each worker runs single-threaded async event loop.
    """

    def __init__(self):
        # Map: room_id -> set of WebSocket connections
        self.room_connections: dict[UUID, set[WebSocket]] = {}

        # Map: room_id -> Redis PubSub instance
        self.room_subscriptions: dict[UUID, PubSub] = {}

        # Map: WebSocket -> room_id (for cleanup on disconnect)
        self.websocket_rooms: dict[WebSocket, UUID] = {}

    async def connect(self, websocket: WebSocket, room_id: UUID) -> None:
        """
        Register a new WebSocket connection for a room.

        Args:
            websocket: FastAPI WebSocket connection
            room_id: UUID of the room to subscribe to
        """
        await websocket.accept()

        # Add to room connections
        if room_id not in self.room_connections:
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)

        # Track websocket -> room mapping
        self.websocket_rooms[websocket] = room_id

        # Subscribe to Redis channel if not already subscribed
        if room_id not in self.room_subscriptions:
            await self._subscribe_to_room(room_id)

        logger.info(f"WebSocket connected to room {room_id}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        Clean up a disconnected WebSocket.

        Args:
            websocket: The disconnected WebSocket
        """
        room_id = self.websocket_rooms.pop(websocket, None)
        if not room_id:
            return

        # Remove from room connections
        if room_id in self.room_connections:
            self.room_connections[room_id].discard(websocket)

            # If no more connections for this room, unsubscribe from Redis
            if not self.room_connections[room_id]:
                await self._unsubscribe_from_room(room_id)
                del self.room_connections[room_id]

        logger.info(f"WebSocket disconnected from room {room_id}")

    async def send_to_room(self, room_id: UUID, message: dict[str, Any]) -> None:
        """
        Send a message to all WebSocket clients in a room on this worker.

        Called by Redis listener when event received.

        Args:
            room_id: UUID of the room
            message: Message dict to send (will be JSON serialized)
        """
        if room_id not in self.room_connections:
            return

        message_text = json.dumps(message)

        # Send to all connected clients in this room
        disconnected = []
        for websocket in self.room_connections[room_id]:
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected sockets
        for websocket in disconnected:
            await self.disconnect(websocket)

    async def _subscribe_to_room(self, room_id: UUID) -> None:
        """
        Subscribe to Redis pub/sub channel for a room.

        Starts background task to listen for events and forward to clients.
        """
        try:
            redis = await get_redis()
            pubsub = redis.pubsub()

            channel = f"room:{room_id}"
            await pubsub.subscribe(channel)

            self.room_subscriptions[room_id] = pubsub

            # Start background listener
            asyncio.create_task(self._listen_to_room(room_id, pubsub))

            logger.info(f"Subscribed to Redis channel: {channel}")

        except Exception as e:
            logger.error(f"Failed to subscribe to room {room_id}: {e}")

    async def _unsubscribe_from_room(self, room_id: UUID) -> None:
        """
        Unsubscribe from Redis pub/sub channel when no clients remain.
        """
        pubsub = self.room_subscriptions.pop(room_id, None)
        if pubsub:
            try:
                await pubsub.unsubscribe()
                await pubsub.close()
                logger.info(f"Unsubscribed from room {room_id}")
            except Exception as e:
                logger.error(f"Error unsubscribing from room {room_id}: {e}")

    async def _listen_to_room(self, room_id: UUID, pubsub: PubSub) -> None:
        """
        Background task: Listen to Redis pub/sub and forward to WebSocket clients.

        Runs until room has no more connections.
        """
        try:
            async for message in pubsub.listen():
                # Only process actual messages (not subscribe confirmations)
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self.send_to_room(room_id, data)

                # Exit if room no longer has connections
                if room_id not in self.room_subscriptions:
                    break

        except Exception as e:
            logger.error(f"Error in Redis listener for room {room_id}: {e}")


# Global connection manager instance per worker
connection_manager = ConnectionManager()
```

### Acceptance Criteria
- [ ] `connect()` accepts WebSocket and subscribes to Redis channel
- [ ] `disconnect()` cleans up and unsubscribes if last connection
- [ ] `send_to_room()` broadcasts to all local connections
- [ ] Redis listener forwards events to WebSocket clients
- [ ] Multiple connections to same room share one Redis subscription
- [ ] Disconnected sockets removed automatically

---

## Deliverable 3: AG-UI WebSocket Endpoint

**File:** `app/api/routes/websocket.py` (new)
**Purpose:** AG-UI protocol compliant WebSocket endpoint
**Dependencies:** ConnectionManager, Event Replay, Auth

### Complete Implementation

```python
"""
WebSocket Routes: AG-UI protocol implementation for real-time streaming.

Implements AG-UI JSON-RPC WebSocket protocol:
- Session handshake with JWT authentication
- Room subscription with replay
- Bidirectional messaging
- Event streaming
"""
from __future__ import annotations

import json
import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user_from_token
from app.models import User
from app.services.websocket_manager import connection_manager
from app.services.event_replay import replay_events_since
from app.services.agent_runner import run_agents_for_message
from app.services.event_emitter import emit_event
from app.crud import check_room_membership, send_user_message

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/rooms/{room_id}")
async def websocket_room_session(
    websocket: WebSocket,
    room_id: UUID,
) -> None:
    """
    AG-UI WebSocket endpoint for real-time room sessions.

    Protocol Flow:
    1. Client connects with JWT in query param
    2. Server validates auth and room membership
    3. Client sends handshake with last_sequence (optional)
    4. Server replays missed events (if any)
    5. Server subscribes to Redis for live events
    6. Bidirectional messaging begins

    URL: ws://host/api/v1/ws/rooms/{room_id}?token={jwt}

    Client -> Server messages:
    - message.send: User sends message
    - room.subscribe: Switch to different room (not implemented v1)

    Server -> Client messages:
    - session.created: Handshake complete
    - event: Persisted event from event log
    - message.delta: Ephemeral agent token streaming
    - error: Error notification
    """
    # Extract token from query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authenticate user
    try:
        user = await get_current_user_from_token(token)
    except Exception as e:
        logger.warning(f"WebSocket auth failed: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get database session
    async for session in get_db():
        # Check room membership
        is_member = await check_room_membership(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        if not is_member:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        # Connect WebSocket
        await connection_manager.connect(websocket, room_id)

        try:
            # Wait for handshake from client
            handshake_data = await websocket.receive_json()
            last_sequence = handshake_data.get("last_sequence", 0)

            # Replay missed events
            if last_sequence > 0:
                missed_events = await replay_events_since(
                    session=session,
                    room_id=room_id,
                    after_sequence=last_sequence,
                )

                for event in missed_events:
                    await websocket.send_json(event)

            # Send handshake response
            await websocket.send_json({
                "type": "session.created",
                "room_id": str(room_id),
            })

            # Main message loop
            while True:
                data = await websocket.receive_json()

                if data.get("type") == "message.send":
                    await handle_user_message(
                        websocket=websocket,
                        room_id=room_id,
                        user=user,
                        content=data.get("content", ""),
                        session=session,
                    )

                # Future: handle room.subscribe, typing indicators, etc.

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected: user={user.id}, room={room_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error",
            })
        finally:
            await connection_manager.disconnect(websocket)


async def handle_user_message(
    websocket: WebSocket,
    room_id: UUID,
    user: User,
    content: str,
    session: AsyncSession,
) -> None:
    """
    Handle user message from WebSocket.

    1. Emit room_message.user event (persisted + published to Redis)
    2. Trigger agents (if any active in room)
    3. Agents stream responses via Redis pub/sub

    Note: This creates a NEW transaction for the message.
    WebSocket connections are long-lived, not transactional.
    """
    try:
        # Start new transaction for this message
        async with session.begin():
            # Emit user message event
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.user",
                payload={
                    "sender_id": str(user.id),
                    "content": content,
                },
            )

            # Trigger agents (within same transaction)
            await run_agents_for_message(
                room_id=room_id,
                trigger_message=content,
                session=session,
            )

            # Transaction commits here

    except Exception as e:
        logger.error(f"Error handling user message: {e}")
        await websocket.send_json({
            "type": "error",
            "message": "Failed to send message",
        })
```

### Authentication Helper

```python
# In app/api/deps.py - add this function

async def get_current_user_from_token(token: str) -> User:
    """
    Validate JWT token and return user.

    Used for WebSocket authentication (can't use Depends() in WebSocket routes).
    """
    from app.core.security import verify_token

    payload = verify_token(token)
    user_id = UUID(payload.get("sub"))

    # Get user from database
    async for session in get_db():
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
            )

        return user
```

### Acceptance Criteria
- [ ] WebSocket connects with JWT in query param
- [ ] Invalid token/auth closes connection with 1008
- [ ] Non-member of room closes connection with 1008
- [ ] Handshake response sent after replay complete
- [ ] User messages trigger event emission and agents
- [ ] Errors sent as JSON error messages
- [ ] Disconnect cleans up connection manager

---

## Deliverable 4: Agent Streaming Service

**File:** `app/services/agent_runner.py` (modify)
**Purpose:** Stream agent responses token-by-token
**Dependencies:** Redis Event Publisher

### Implementation Changes

```python
# Add import
from app.services.event_emitter import publish_agent_token

# Add new function
async def run_agent_for_room_streaming(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Run an agent with token-by-token streaming.

    This is the Phase 4 enhancement of run_agent_for_room().

    Differences from non-streaming version:
    1. Uses agent.run_stream() instead of agent.run()
    2. Publishes tokens to Redis as they arrive
    3. Still emits final room_message.agent event with complete response

    Token streaming:
    - Tokens published via Redis as ephemeral message.delta events
    - NOT persisted to Postgres (only final message is persisted)
    - Clients receive tokens in real-time for progressive rendering

    Args:
        room_id: UUID of the room
        agent_name: Name of the agent to run
        trigger_message: The message that triggered the agent
        session: Async database session

    Returns:
        Dict with agent response details
    """
    if not is_agent_registered(agent_name):
        logger.warning(f"Attempted to run unregistered agent: {agent_name}")
        return {
            "agent_name": agent_name,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }

    try:
        # Build room context
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
        )

        # Run agent with streaming
        full_response = ""

        if agent_name == "StoryAdvisor":
            # StoryAdvisor with streaming
            from app.agents.story_advisor import story_advisor, StoryAdvisorDeps

            deps = StoryAdvisorDeps(context=context)

            # Build prompt with context
            conversation_context = ""
            if context.story_data:
                conversation_context += f"\nStory: {context.story_data.get('title', 'Untitled')}\n"

            if context.recent_messages:
                recent = context.recent_messages[-5:]
                conversation_context += "\nRecent messages:\n"
                for msg in recent:
                    sender = msg.get("agent_name") or "User"
                    conversation_context += f"{sender}: {msg.get('content', '')}\n"

            full_prompt = f"{conversation_context}\nUser message: {trigger_message}"

            # Stream response
            async with story_advisor.run_stream(full_prompt, deps=deps) as result:
                async for token in result.stream_text():
                    full_response += token

                    # Publish token to Redis for real-time delivery
                    await publish_agent_token(
                        room_id=room_id,
                        agent_name=agent_name,
                        token=token,
                    )

        else:
            # Generic agent streaming
            agent = get_agent(agent_name)
            async with agent.run_stream(trigger_message) as result:
                async for token in result.stream_text():
                    full_response += token
                    await publish_agent_token(
                        room_id=room_id,
                        agent_name=agent_name,
                        token=token,
                    )

        # Emit final complete message event
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload={
                "agent_name": agent_name,
                "content": full_response,
            },
        )

        logger.info(f"Agent {agent_name} streamed response in room {room_id}")

        return {
            "agent_name": agent_name,
            "content": full_response,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Agent {agent_name} streaming error in room {room_id}: {e}")

        error_content = "I encountered an error while processing your request."

        try:
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": error_content,
                },
            )
        except Exception as emit_error:
            logger.error(f"Failed to emit error message: {emit_error}")

        return {
            "agent_name": agent_name,
            "content": error_content,
            "success": False,
            "error": str(e),
        }


# Update run_agents_for_message to use streaming version
async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
) -> list[dict[str, Any]]:
    """
    Run all active agents in a room with streaming support.

    Phase 4: Uses streaming version of agent execution.
    """
    # Find all active agent participants
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    agent_participants = result.scalars().all()

    responses = []
    for participant in agent_participants:
        agent_name = participant.participant_id

        if is_agent_registered(agent_name):
            # Use streaming version (Phase 4)
            response = await run_agent_for_room_streaming(
                room_id=room_id,
                agent_name=agent_name,
                trigger_message=trigger_message,
                session=session,
            )
            responses.append(response)
        else:
            logger.warning(
                f"Agent '{agent_name}' is participant in room {room_id} "
                f"but not registered in AGENT_REGISTRY"
            )

    return responses
```

### Acceptance Criteria
- [ ] `run_agent_for_room_streaming()` uses `agent.run_stream()`
- [ ] Tokens published to Redis as `message.delta` events
- [ ] Final complete message persisted as `room_message.agent` event
- [ ] Streaming errors handled gracefully
- [ ] StoryAdvisor supports streaming with context

---

## Deliverable 5: Event Replay Service

**File:** `app/services/event_replay.py` (new)
**Purpose:** Replay missed events for reconnecting clients
**Dependencies:** Database, RoomEvent model

### Complete Implementation

```python
"""
Event Replay Service: Sequence-based event replay for reconnecting clients.

When a client reconnects, they provide the last sequence number they received.
This service queries the event log and returns all events with higher sequences.

This enables:
1. Seamless reconnection after temporary network issues
2. Catching up after client was offline
3. No message loss under normal conditions
"""
from __future__ import annotations

import logging
from uuid import UUID
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RoomEvent

logger = logging.getLogger(__name__)


async def replay_events_since(
    *,
    session: AsyncSession,
    room_id: UUID,
    after_sequence: int,
    limit: int = 1000,
) -> list[dict[str, Any]]:
    """
    Replay events from event log for a room.

    Used for reconnection and catching up on missed events.

    Args:
        session: Async database session
        room_id: UUID of the room
        after_sequence: Last sequence the client received
        limit: Max events to return (default 1000, prevents huge replays)

    Returns:
        List of event dicts in AG-UI format:
        {
            "type": "event",
            "sequence": int,
            "event_type": str,
            "payload": {...},
            "created_at": ISO timestamp
        }

    Notes:
    - Events are ordered by room_sequence (ascending)
    - Large replays (>limit) return first N events + warning
    - Client should handle pagination if needed (future enhancement)
    """
    result = await session.execute(
        select(RoomEvent)
        .where(
            RoomEvent.room_id == room_id,
            RoomEvent.room_sequence > after_sequence,
        )
        .order_by(RoomEvent.room_sequence)
        .limit(limit)
    )
    events = result.scalars().all()

    if len(events) >= limit:
        logger.warning(
            f"Replay limit reached for room {room_id}: "
            f"{len(events)} events after sequence {after_sequence}"
        )

    return [
        {
            "type": "event",
            "sequence": event.room_sequence,
            "event_type": event.event_type,
            "payload": event.payload,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ]


async def get_latest_sequence(
    *,
    session: AsyncSession,
    room_id: UUID,
) -> int:
    """
    Get the latest sequence number for a room.

    Used for clients to know if they're caught up.

    Returns:
        Latest sequence number, or 0 if no events
    """
    result = await session.execute(
        select(RoomEvent.room_sequence)
        .where(RoomEvent.room_id == room_id)
        .order_by(RoomEvent.room_sequence.desc())
        .limit(1)
    )
    latest = result.scalar_one_or_none()

    return latest if latest is not None else 0
```

### Acceptance Criteria
- [ ] Returns events with sequence > after_sequence
- [ ] Events ordered by room_sequence ascending
- [ ] Respects limit parameter (default 1000)
- [ ] Returns AG-UI compatible format
- [ ] Empty result if no new events
- [ ] Logs warning if limit reached

---

## Deliverable 6: Frontend WebSocket Hook

**File:** `frontend/src/hooks/useRoomStream.ts` (new)
**Purpose:** React hook for WebSocket connection management
**Dependencies:** OpenAPI client (for types)

### Complete Implementation

```typescript
/**
 * useRoomStream: React hook for real-time room updates via WebSocket.
 *
 * Features:
 * - Automatic connection/disconnection based on room ID
 * - Sequence-based reconnection with replay
 * - Token streaming for agent responses
 * - Event handling for all AG-UI message types
 * - Optimistic UI updates
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

interface RoomEvent {
  type: 'event'
  sequence: number
  event_type: string
  payload: any
  created_at: string
}

interface MessageDelta {
  type: 'message.delta'
  agent_name: string
  content: string
}

interface SessionCreated {
  type: 'session.created'
  room_id: string
}

interface ErrorMessage {
  type: 'error'
  message: string
}

type WebSocketMessage = RoomEvent | MessageDelta | SessionCreated | ErrorMessage

interface UseRoomStreamOptions {
  enabled?: boolean
  onError?: (error: Error) => void
}

export function useRoomStream(
  roomId: string | undefined,
  options: UseRoomStreamOptions = {}
) {
  const { enabled = true, onError } = options

  const wsRef = useRef<WebSocket | null>(null)
  const queryClient = useQueryClient()

  const [isConnected, setIsConnected] = useState(false)
  const [lastSequence, setLastSequence] = useState(0)
  const [streamingMessage, setStreamingMessage] = useState<{
    agent_name: string
    content: string
  } | null>(null)

  // Send message to room
  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected')
      return
    }

    wsRef.current.send(JSON.stringify({
      type: 'message.send',
      content,
    }))
  }, [])

  // Handle incoming WebSocket messages
  const handleMessage = useCallback((event: MessageEvent) => {
    try {
      const message: WebSocketMessage = JSON.parse(event.data)

      switch (message.type) {
        case 'session.created':
          console.log('WebSocket session created')
          setIsConnected(true)
          break

        case 'event':
          // Update last sequence
          setLastSequence(message.sequence)

          // Invalidate queries to refresh UI
          if (message.event_type === 'room_message.user' ||
              message.event_type === 'room_message.agent') {
            queryClient.invalidateQueries({
              queryKey: ['rooms', roomId, 'messages']
            })
          }

          if (message.event_type.startsWith('participant.')) {
            queryClient.invalidateQueries({
              queryKey: ['rooms', roomId, 'participants']
            })
          }

          // Clear streaming message when agent message complete
          if (message.event_type === 'room_message.agent') {
            setStreamingMessage(null)
          }
          break

        case 'message.delta':
          // Accumulate streaming tokens
          setStreamingMessage(prev => ({
            agent_name: message.agent_name,
            content: (prev?.content || '') + message.content,
          }))
          break

        case 'error':
          console.error('WebSocket error:', message.message)
          onError?.(new Error(message.message))
          break
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error)
    }
  }, [queryClient, roomId, onError])

  // Connect to WebSocket
  useEffect(() => {
    if (!roomId || !enabled) return

    const token = localStorage.getItem('token')
    if (!token) {
      console.error('No auth token available')
      return
    }

    // WebSocket URL
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/rooms/${roomId}?token=${token}`

    console.log('Connecting to WebSocket:', wsUrl)

    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')

      // Send handshake with last sequence
      ws.send(JSON.stringify({
        type: 'session.create',
        last_sequence: lastSequence,
      }))
    }

    ws.onmessage = handleMessage

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      setIsConnected(false)
      onError?.(new Error('WebSocket connection error'))
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setIsConnected(false)
    }

    // Cleanup on unmount
    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close()
      }
    }
  }, [roomId, enabled, lastSequence, handleMessage, onError])

  return {
    isConnected,
    sendMessage,
    streamingMessage,
    lastSequence,
  }
}
```

### Acceptance Criteria
- [ ] Connects to WebSocket on mount
- [ ] Sends handshake with last_sequence
- [ ] Handles all AG-UI message types
- [ ] Invalidates React Query cache on events
- [ ] Accumulates streaming tokens
- [ ] Disconnects on unmount
- [ ] Handles errors gracefully

---

## Deliverable 7: Frontend UI Integration

**Files:** Modify existing room components
**Purpose:** Integrate streaming hook and display real-time updates
**Dependencies:** useRoomStream hook

### Message List Component Enhancement

```typescript
// In frontend/src/components/Rooms/MessageList.tsx

import { useRoomStream } from '@/hooks/useRoomStream'

export function MessageList({ roomId }: { roomId: string }) {
  const { data: messages } = useRoomMessages(roomId)
  const { streamingMessage } = useRoomStream(roomId)

  return (
    <Box>
      {/* Existing messages */}
      {messages?.map(msg => (
        <Message key={msg.message_id} message={msg} />
      ))}

      {/* Streaming message (optimistic UI) */}
      {streamingMessage && (
        <Message
          message={{
            message_id: 'streaming',
            sender_type: 'agent',
            agent_name: streamingMessage.agent_name,
            content: streamingMessage.content,
            created_at: new Date().toISOString(),
          }}
          isStreaming={true}
        />
      )}
    </Box>
  )
}
```

### Message Input Component Enhancement

```typescript
// In frontend/src/components/Rooms/MessageInput.tsx

import { useRoomStream } from '@/hooks/useRoomStream'

export function MessageInput({ roomId }: { roomId: string }) {
  const [content, setContent] = useState('')
  const { sendMessage, isConnected } = useRoomStream(roomId)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (!content.trim()) return

    // Send via WebSocket if connected, fallback to REST API
    if (isConnected) {
      sendMessage(content)
    } else {
      // Fallback to REST API (Phase 1-3 behavior)
      sendMessageMutation.mutate({ content })
    }

    setContent('')
  }

  return (
    <form onSubmit={handleSubmit}>
      <Input
        value={content}
        onChange={(e) => setContent(e.target.value)}
        placeholder={isConnected ? 'Type a message...' : 'Connecting...'}
        disabled={!isConnected}
      />
      <Button type="submit" disabled={!isConnected}>
        Send
      </Button>
    </form>
  )
}
```

### Acceptance Criteria
- [ ] MessageList shows streaming messages optimistically
- [ ] Streaming messages have visual indicator (e.g., typing effect)
- [ ] MessageInput uses WebSocket when connected
- [ ] Falls back to REST API if WebSocket unavailable
- [ ] Connection status visible to user
- [ ] Streaming messages replace with persisted message on completion

---

## Deliverable 8: Load Testing & Optimization

**File:** `backend/tests/load/test_websocket_load.py` (new)
**Purpose:** Validate system under 50+ concurrent connections
**Dependencies:** Locust or similar load testing framework

### Load Test Implementation

```python
"""
Load tests for WebSocket streaming.

Tests:
1. 50+ concurrent WebSocket connections
2. Simultaneous message sending
3. Agent response streaming to all clients
4. Reconnection storm (all disconnect/reconnect)
5. Redis failure graceful degradation

Requirements:
- pip install locust
- Run: locust -f tests/load/test_websocket_load.py
"""
import asyncio
import json
import time
from uuid import uuid4

from locust import User, task, events
from locust.contrib.fastapi import FastAPIUser
import websockets


class WebSocketUser(User):
    """
    Simulated WebSocket user for load testing.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws = None
        self.room_id = None
        self.messages_received = 0

    async def connect(self):
        """Connect to WebSocket."""
        # Get auth token (use test user)
        token = "test-token"  # Replace with actual auth

        # Create or join test room
        self.room_id = "test-room-id"  # Replace with actual room creation

        # Connect to WebSocket
        ws_url = f"ws://localhost:8000/api/v1/ws/rooms/{self.room_id}?token={token}"

        start_time = time.time()
        try:
            self.ws = await websockets.connect(ws_url)

            # Send handshake
            await self.ws.send(json.dumps({
                "type": "session.create",
                "last_sequence": 0,
            }))

            # Wait for session.created
            response = await self.ws.recv()
            data = json.loads(response)

            if data.get("type") == "session.created":
                latency = (time.time() - start_time) * 1000
                events.request.fire(
                    request_type="WebSocket",
                    name="connect",
                    response_time=latency,
                    response_length=len(response),
                    exception=None,
                )

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="connect",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )

    @task
    async def send_message(self):
        """Send a message and measure response time."""
        if not self.ws:
            await self.connect()

        message_content = f"Load test message {uuid4()}"

        start_time = time.time()
        try:
            # Send message
            await self.ws.send(json.dumps({
                "type": "message.send",
                "content": message_content,
            }))

            # Wait for event confirmation
            response = await asyncio.wait_for(self.ws.recv(), timeout=5.0)

            latency = (time.time() - start_time) * 1000
            self.messages_received += 1

            events.request.fire(
                request_type="WebSocket",
                name="send_message",
                response_time=latency,
                response_length=len(response),
                exception=None,
            )

        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="send_message",
                response_time=(time.time() - start_time) * 1000,
                response_length=0,
                exception=e,
            )

    async def on_stop(self):
        """Disconnect on test end."""
        if self.ws:
            await self.ws.close()
```

### Load Test Scenarios

```bash
# Scenario 1: Ramp up to 50 users
locust -f tests/load/test_websocket_load.py --users 50 --spawn-rate 5

# Scenario 2: Spike test (50 -> 100 -> 50)
locust -f tests/load/test_websocket_load.py --users 100 --spawn-rate 10

# Scenario 3: Sustained load (50 users, 10 minutes)
locust -f tests/load/test_websocket_load.py --users 50 --run-time 10m
```

### Performance Targets

| Metric | Target | Degradation Threshold |
|--------|--------|----------------------|
| WebSocket connect latency (p95) | <100ms | <500ms |
| Message send latency (p95) | <100ms | <500ms |
| Agent response start (p95) | <2s | <5s |
| Concurrent connections | 50+ | 100+ |
| Message throughput | 100/sec | 50/sec |
| Redis fanout latency | <10ms | <50ms |

### Acceptance Criteria
- [ ] 50 concurrent WebSocket connections stable
- [ ] Message latency <100ms (p95)
- [ ] Agent streaming works with 50 clients
- [ ] Reconnection storm doesn't crash system
- [ ] Redis failure doesn't lose messages
- [ ] No memory leaks over 10 minute test

---

## Testing Strategy

### Unit Tests

#### Event Publisher (`tests/services/test_event_emitter_redis.py`)
- [ ] `_publish_to_redis()` publishes to correct channel
- [ ] Redis failures don't break transaction
- [ ] `publish_agent_token()` sends ephemeral deltas
- [ ] Message format is AG-UI compatible

#### Connection Manager (`tests/services/test_websocket_manager.py`)
- [ ] `connect()` adds WebSocket and subscribes to Redis
- [ ] `disconnect()` removes WebSocket and unsubscribes
- [ ] `send_to_room()` broadcasts to all connections
- [ ] Redis listener forwards events correctly
- [ ] Multiple connections share one subscription
- [ ] Disconnected sockets cleaned up automatically

#### Event Replay (`tests/services/test_event_replay.py`)
- [ ] Returns events with sequence > after_sequence
- [ ] Events ordered by room_sequence
- [ ] Respects limit parameter
- [ ] Empty result if no new events
- [ ] Returns AG-UI compatible format

### Integration Tests

#### WebSocket Endpoint (`tests/api/test_websocket.py`)
- [ ] Connection requires valid JWT
- [ ] Invalid auth closes with 1008
- [ ] Non-member closes with 1008
- [ ] Handshake response sent
- [ ] User messages trigger events and agents
- [ ] Reconnection replays missed events
- [ ] Multiple clients receive same events

#### End-to-End Streaming (`tests/integration/test_streaming_e2e.py`)
- [ ] User sends message via WebSocket
- [ ] Agent streams response token-by-token
- [ ] All room participants receive tokens
- [ ] Final message persisted in database
- [ ] Disconnected client reconnects and catches up
- [ ] No duplicate events received

### Manual Testing Checklist

#### Basic Streaming
- [ ] Connect to room via WebSocket
- [ ] Send message - appears in real-time
- [ ] Agent response streams token-by-token
- [ ] Other user sees agent response streaming
- [ ] Messages persist after refresh

#### Reconnection
- [ ] Disconnect network
- [ ] Send messages from another client
- [ ] Reconnect - missed messages replay
- [ ] No duplicate messages
- [ ] Sequence numbers correct

#### Multi-User
- [ ] Open room in 3 browser windows
- [ ] Send message from window 1
- [ ] Windows 2 and 3 see message instantly
- [ ] Agent response visible in all windows
- [ ] Token streaming synchronized

#### Error Handling
- [ ] Stop Redis - messages still persist
- [ ] Restart Redis - streaming resumes
- [ ] Kill backend worker - client reconnects
- [ ] Agent error - friendly message shown
- [ ] Network timeout - reconnect works

---

## Key Architectural Patterns

### 1. Multi-Worker Event Fanout
```
User Message → Worker A
                ↓
            emit_event()
                ↓
            Postgres (event log)
                ↓
            Redis pub/sub
                ↓ ↓ ↓
         Worker A, B, C (all subscribed)
                ↓ ↓ ↓
         WebSocket clients on each worker
```

### 2. Stateless Reconnection
```
Client disconnect (last_sequence = 42)
    ↓
Client reconnect to Worker B (different from A)
    ↓
Send handshake: {last_sequence: 42}
    ↓
Worker B queries Postgres: WHERE sequence > 42
    ↓
Replay events 43, 44, 45, ...
    ↓
Subscribe to Redis for live events
```

### 3. Dual-Path Messaging
```
Ephemeral (Redis only):
- message.delta (agent tokens)
- typing indicators (future)

Persisted (Postgres + Redis):
- room_message.user
- room_message.agent
- participant.joined
- all other events
```

### 4. Graceful Degradation
```
Redis Available:
- Real-time streaming ✓
- Multi-worker fanout ✓
- <10ms latency ✓

Redis Unavailable:
- Events still persisted ✓
- Clients reconnect and replay ✓
- Degraded latency (~1s polling fallback)
```

---

## Environment Configuration

### Backend `.env` additions

```bash
# Redis Configuration (already exists from Phase 0)
REDIS_URL=redis://localhost:6379

# WebSocket Configuration
WS_HEARTBEAT_INTERVAL=30  # seconds
WS_MAX_MESSAGE_SIZE=1048576  # 1MB

# Performance Tuning
REDIS_MAX_CONNECTIONS=50
WS_MAX_CONNECTIONS_PER_WORKER=100
```

### Frontend environment

```typescript
// frontend/src/config.ts
export const WS_RECONNECT_DELAY = 1000 // ms
export const WS_MAX_RETRIES = 5
export const WS_HEARTBEAT_INTERVAL = 30000 // ms
```

---

## Acceptance Criteria Summary

### Functional Requirements
- [ ] Multiple users see messages in real-time (all workers)
- [ ] Agent responses stream token-by-token to all participants
- [ ] Disconnected clients reconnect and replay missed events
- [ ] No duplicate events under normal conditions
- [ ] Sequence-based ordering maintained
- [ ] WebSocket and REST API both work (fallback)

### Non-Functional Requirements
- [ ] 50+ concurrent WebSocket connections supported
- [ ] Message latency <100ms (p95)
- [ ] Agent response start <2s (p95)
- [ ] Graceful degradation if Redis unavailable
- [ ] No memory leaks over sustained load
- [ ] Worker crashes don't lose events (Redis unavailable = Postgres fallback)

### Integration Requirements
- [ ] Follows Phase 1 event sourcing patterns
- [ ] Uses existing emit_event() function
- [ ] No database schema changes required
- [ ] Compatible with Phases 2-3 (agents, frontend)
- [ ] AG-UI protocol compliance

---

## Files Summary

### New Files (6 total)
1. `app/services/websocket_manager.py` - Connection and subscription manager
2. `app/api/routes/websocket.py` - AG-UI WebSocket endpoint
3. `app/services/event_replay.py` - Sequence-based replay
4. `frontend/src/hooks/useRoomStream.ts` - React WebSocket hook
5. `tests/load/test_websocket_load.py` - Load testing
6. `backend/docs/Minimog/Phase4/Phase-4-Plan.md` - This document

### Modified Files (5 total)
1. `app/services/event_emitter.py` - Add Redis pub/sub
2. `app/services/agent_runner.py` - Add token streaming
3. `app/api/deps.py` - Add `get_current_user_from_token()`
4. `frontend/src/components/Rooms/MessageList.tsx` - Show streaming messages
5. `frontend/src/components/Rooms/MessageInput.tsx` - Use WebSocket

---

## Risk Mitigation

### Risk: Redis becomes single point of failure
**Mitigation:**
- Events still persist to Postgres if Redis down
- Clients reconnect and replay from Postgres
- Monitor Redis health and auto-restart

### Risk: WebSocket connections exhaust resources
**Mitigation:**
- Limit connections per worker (100 default)
- Load balancer distributes across workers
- Monitor connection count and memory usage

### Risk: Token streaming causes message loss
**Mitigation:**
- Tokens are ephemeral (not critical)
- Final complete message always persisted
- Client displays "..." if tokens missed

### Risk: Sequence gaps confuse clients
**Mitigation:**
- Document that gaps are normal (concurrent writes)
- Client uses sequence only for deduplication, not validation
- Replay fills all gaps on reconnect

### Risk: Large replays (1000+ events) slow reconnection
**Mitigation:**
- Limit replay to 1000 events (configurable)
- Log warning if limit reached
- Future: pagination support for large replays

---

## Next Steps After Phase 4

**Phase 5:** Performance & Scale
- Horizontal Redis clustering
- Database read replicas
- CDN for static assets
- Metrics and monitoring (Prometheus, Grafana)

**Phase 6:** Advanced Features
- Typing indicators
- Read receipts
- File upload and sharing
- Voice/video (future consideration)

**Phase 7:** Analytics & Insights
- pg_duckdb queries for conversation analysis
- Agent performance metrics
- User engagement analytics
- Property graph queries (room relationships)

---

## Implementation Checklist

### Week 1: Backend Infrastructure (Days 1-4)
- [ ] Day 1: Redis event publisher + tests
- [ ] Day 2: WebSocket connection manager + tests
- [ ] Day 3: AG-UI WebSocket endpoint + auth
- [ ] Day 4: Event replay service + tests

### Week 2: Streaming & Frontend (Days 5-8)
- [ ] Day 5: Agent token streaming + tests
- [ ] Day 6: Frontend useRoomStream hook
- [ ] Day 7: Frontend UI integration
- [ ] Day 8: Load testing + optimization

---

## Notes for Implementation

### Critical Patterns

1. **Redis Pub/Sub Pattern**
   - Each worker subscribes to room channels they have clients for
   - Unsubscribe when last client disconnects (resource cleanup)
   - Publish AFTER transaction flush (ensures event persisted)

2. **Stateless Reconnection**
   - No server-side session state (can reconnect to different worker)
   - Client tracks last_sequence locally
   - Server replays from Postgres, then subscribes to Redis

3. **Dual-Path Events**
   - Persistent events: Postgres + Redis
   - Ephemeral events: Redis only (tokens, typing, etc.)
   - Client handles both uniformly

4. **Error Handling**
   - Redis errors: log and continue (graceful degradation)
   - WebSocket errors: close connection cleanly
   - Agent errors: emit error event, don't crash worker

5. **Testing Strategy**
   - Mock Redis in unit tests (fast)
   - Real Redis in integration tests
   - Load tests with real infrastructure

6. **Performance Optimization**
   - Connection pooling for Redis
   - Batch event replay (stream, don't buffer)
   - Monitor memory usage (WebSocket connections)

### Implementation Order

1. **Start with Redis publisher** (extends existing code)
   - Minimal changes to event_emitter.py
   - Immediately testable

2. **Build connection manager** (infrastructure)
   - No dependencies on WebSocket endpoint
   - Can be tested with mock WebSockets

3. **WebSocket endpoint next**
   - Brings everything together
   - Most complex integration

4. **Agent streaming** (builds on Phase 2)
   - Incremental enhancement
   - Backward compatible

5. **Frontend last**
   - Depends on backend working
   - Progressive enhancement (REST API fallback)

6. **Load test throughout**
   - Don't wait until end
   - Find bottlenecks early

---

**Ready to implement? Start with Deliverable 1 (Redis Event Publisher) →**
