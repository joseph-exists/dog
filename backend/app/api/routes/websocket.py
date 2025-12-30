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