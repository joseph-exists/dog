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