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
        logger.info(f"[CONN_MGR] connect() called for room {room_id}")
        await websocket.accept()
        logger.info(f"[CONN_MGR] WebSocket accepted for room {room_id}")

        # Add to room connections
        if room_id not in self.room_connections:
            logger.info(f"[CONN_MGR] Creating new connection set for room {room_id}")
            self.room_connections[room_id] = set()
        self.room_connections[room_id].add(websocket)
        logger.info(f"[CONN_MGR] Room {room_id} now has {len(self.room_connections[room_id])} connections")

        # Track websocket -> room mapping
        self.websocket_rooms[websocket] = room_id

        # Subscribe to Redis channel if not already subscribed
        if room_id not in self.room_subscriptions:
            logger.info(f"[CONN_MGR] Room {room_id} not yet subscribed, calling _subscribe_to_room")
            await self._subscribe_to_room(room_id)
        else:
            logger.info(f"[CONN_MGR] Room {room_id} already has active Redis subscription")

        logger.info(f"[CONN_MGR] WebSocket connected to room {room_id}")

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
            logger.info(f"[REDIS] _subscribe_to_room() called for room {room_id}")
            redis = await get_redis()
            logger.info(f"[REDIS] Got Redis client for room {room_id}")
            pubsub = redis.pubsub()
            logger.info(f"[REDIS] Created pubsub client for room {room_id}")

            channel = f"room:{room_id}"
            logger.info(f"[REDIS] Subscribing to channel: {channel}")
            await pubsub.subscribe(channel)
            logger.info(f"[REDIS] Subscribe call completed for channel: {channel}")

            self.room_subscriptions[room_id] = pubsub
            logger.info(f"[REDIS] Added pubsub to room_subscriptions dict for room {room_id}")

            # Start background listener
            logger.info(f"[REDIS] Creating background task for _listen_to_room for room {room_id}")
            task = asyncio.create_task(self._listen_to_room(room_id, pubsub))
            logger.info(f"[REDIS] Background task created: {task}")

            logger.info(f"[REDIS] Successfully subscribed to Redis channel: {channel}")

        except Exception as e:
            logger.error(f"[REDIS] Failed to subscribe to room {room_id}: {e}", exc_info=True)

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
        logger.info(f"[LISTENER] Starting _listen_to_room for room {room_id}")
        try:
            logger.info(f"[LISTENER] Entering pubsub.listen() loop for room {room_id}")
            message_count = 0
            async for message in pubsub.listen():
                message_count += 1
                logger.debug(f"[LISTENER] Received message #{message_count} for room {room_id}: type={message.get('type')}")

                # Only process actual messages (not subscribe confirmations)
                if message["type"] == "message":
                    logger.info(f"[LISTENER] Processing message for room {room_id}: {message.get('data', '')[:100]}")
                    try:
                        data = json.loads(message["data"])
                        logger.info(f"[LISTENER] Parsed JSON, sending to room {room_id}")
                        await self.send_to_room(room_id, data)
                        logger.info(f"[LISTENER] Message forwarded to room {room_id}")
                    except json.JSONDecodeError as e:
                        logger.error(f"[LISTENER] JSON decode error for room {room_id}: {e}")
                elif message["type"] == "subscribe":
                    logger.info(f"[LISTENER] Subscription confirmed for room {room_id}, channel={message.get('channel')}")
                else:
                    logger.debug(f"[LISTENER] Ignoring message type '{message['type']}' for room {room_id}")

                # Exit if room no longer has connections
                if room_id not in self.room_subscriptions:
                    logger.info(f"[LISTENER] Room {room_id} no longer in subscriptions, exiting listener")
                    break

        except Exception as e:
            # Connection closed during cleanup is expected, not an error
            if "Connection closed" in str(e) or "ConnectionError" in type(e).__name__:
                logger.info(f"[LISTENER] Redis connection closed for room {room_id} (cleanup)")
            else:
                logger.error(f"[LISTENER] Error in Redis listener for room {room_id}: {e}", exc_info=True)
        finally:
            logger.info(f"[LISTENER] _listen_to_room exiting for room {room_id}")

# Future extension design:  Extend ConnectionManager for reusability - required prior to release, after fan-out proof (load testing)
# async def subscribe_to_channel(
#     self,
#     channel_id: UUID,
#     channel_type: str = "room"  # "room" or "story"
# ) -> None:
#     """
#     Subscribe to Redis pub/sub channel.

#     Args:
#         channel_id: UUID of the resource
#         channel_type: Type of channel ("room", "story", etc.)
#     """
#     channel = f"{channel_type}:{channel_id}"
#     # ... rest of implementation same, just use channel variable

# Global connection manager instance per worker
connection_manager = ConnectionManager()
