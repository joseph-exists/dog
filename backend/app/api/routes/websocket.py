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

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.db import async_session_maker
from app.api.deps import get_current_user_from_token
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
    logger.info(f"[WS_ROUTE] ===== WebSocket route handler called for room {room_id} =====")
    logger.info(f"[WS] Connection attempt for room {room_id}")

    # Extract token from query params
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"[WS] No token provided for room {room_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Authenticate user
    try:
        user = await get_current_user_from_token(token)
        logger.info(f"[WS] Authenticated user {user.id} for room {room_id}")
    except Exception as e:
        logger.warning(f"[WS] Auth failed for room {room_id}: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get database session
    async with async_session_maker() as session:
        logger.debug(f"[WS] Got DB session for room {room_id}")

        # Check room membership
        is_member = await check_room_membership(
            session=session,
            room_id=room_id,
            user_id=user.id,
        )

        if not is_member:
            logger.warning(f"[WS] User {user.id} is not a member of room {room_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        logger.info(f"[WS] User {user.id} verified as member of room {room_id}")

        # Connect WebSocket
        logger.info(f"[WS] Calling connection_manager.connect for room {room_id}")
        await connection_manager.connect(websocket, room_id)
        logger.info(f"[WS] connection_manager.connect completed for room {room_id}")

        try:
            # Wait for handshake from client
            logger.info(f"[WS] Waiting for handshake from client for room {room_id}")
            handshake_data = await websocket.receive_json()
            last_sequence = handshake_data.get("last_sequence", 0)
            logger.info(f"[WS] Received handshake for room {room_id}, last_sequence={last_sequence}")

            # Replay missed events
            if last_sequence > 0:
                logger.info(f"[WS] Replaying events since sequence {last_sequence} for room {room_id}")
                missed_events = await replay_events_since(
                    session=session,
                    room_id=room_id,
                    after_sequence=last_sequence,
                )
                logger.info(f"[WS] Replaying {len(missed_events)} missed events for room {room_id}")

                for event in missed_events:
                    await websocket.send_json(event)

            # Send handshake response
            logger.info(f"[WS] Sending session.created response for room {room_id}")
            await websocket.send_json({
                "type": "session.created",
                "room_id": str(room_id),
            })

            # Main message loop
            logger.info(f"[WS] Entering main message loop for room {room_id}")
            while True:
                data = await websocket.receive_json()
                logger.debug(f"[WS] Received message type={data.get('type')} for room {room_id}")

                if data.get("type") == "message.send":
                    await handle_user_message(
                        websocket=websocket,
                        room_id=room_id,
                        user=user,
                        content=data.get("content", ""),
                    )

                # Future: handle room.subscribe, typing indicators, etc.

        except WebSocketDisconnect:
            logger.info(f"[WS] Disconnected: user={user.id}, room={room_id}")
        except Exception as e:
            logger.error(f"[WS] Error in room {room_id}: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error",
            })
        finally:
            logger.info(f"[WS] Cleaning up connection for room {room_id}")
            await connection_manager.disconnect(websocket)

@router.websocket("/ws/stories/{story_id}")
async def websocket_story_session(
    websocket: WebSocket,
    story_id: UUID,
) -> None:
    """
    WebSocket endpoint for real-time CYOA story updates.

    Protocol Flow:
    1. Client connects with JWT in query param
    2. Server validates auth and story access
    3. Client sends handshake with last_head_version (optional)
    4. Server sends current timeline if version mismatch
    5. Server subscribes to Redis for live events
    6. Bidirectional messaging begins (future: allow choices via WS)

    URL: ws://host/api/v1/ws/stories/{story_id}?token={jwt}

    Server -> Client messages:
    - session.created: Handshake complete
    - event: Story event (ChoiceMade, HeadMoved)
    - timeline.sync: Full timeline sync (on version mismatch)
    - error: Error notification
    """
    logger.info(f"[WS_STORY] Connection attempt for story {story_id}")

    # Extract token from query params
    token = websocket.query_params.get("token")
    if not token:
        logger.warning(f"[WS_STORY] No token provided for story {story_id}")
        await websocket.close(code=1008)  # Policy violation
        return

    # Authenticate user
    try:
        user = await get_current_user_from_token(token)
        logger.info(f"[WS_STORY] Authenticated user {user.id} for story {story_id}")
    except Exception as e:
        logger.warning(f"[WS_STORY] Auth failed for story {story_id}: {e}")
        await websocket.close(code=1008)
        return

    # Get database session
    async with async_session_maker() as session:
        # Verify user has access to this story
        # (Check via UserStoryProgress or Story.creator_id)
        from app import crud
        from sqlmodel import select
        from app.models import UserStoryProgress, Story

        # Check if user has progress for this story (any persona)
        has_access = await session.execute(
            select(UserStoryProgress)
            .join(Story)
            .where(
                UserStoryProgress.story_id == story_id,
                Story.creator_id == user.id,  # User owns story OR has progress
            )
        )
        if not has_access.first():
            logger.warning(f"[WS_STORY] User {user.id} has no access to story {story_id}")
            await websocket.close(code=1008)
            return

        logger.info(f"[WS_STORY] User {user.id} verified for story {story_id}")

        # Connect WebSocket using existing ConnectionManager
        # TRICK: ConnectionManager expects room_id, but it's just a UUID
        # We'll use story_id and manually subscribe to story:{story_id}
        await websocket.accept()

        # We need to subscribe to story:{story_id} channel instead of room:{story_id}
        # Two options:
        # Option A: Modify ConnectionManager to support custom channel prefix
        # Option B: Manually manage this connection (simpler for now)

        # Let's do Option B for simplicity:
        from app.core.redis import get_redis
        import json

        redis = await get_redis()
        pubsub = redis.pubsub()
        channel = f"story:{story_id}"

        try:
            await pubsub.subscribe(channel)
            logger.info(f"[WS_STORY] Subscribed to {channel}")

            # Wait for handshake from client
            handshake_data = await websocket.receive_json()
            last_head_version = handshake_data.get("last_head_version", None)
            user_persona_id = handshake_data.get("user_persona_id")  # Required

            if not user_persona_id:
                raise ValueError("user_persona_id required in handshake")

            logger.info(
                f"[WS_STORY] Handshake for story {story_id}, "
                f"persona={user_persona_id}, last_version={last_head_version}"
            )

            # Get current progress
            from app.models import UserStoryProgress
            from sqlmodel import select

            progress = await session.execute(
                select(UserStoryProgress).where(
                    UserStoryProgress.user_persona_id == UUID(user_persona_id),
                    UserStoryProgress.story_id == story_id,
                )
            )
            current_progress = progress.scalar_one_or_none()

            # If head_version changed, send timeline sync
            if current_progress and last_head_version is not None:
                if current_progress.head_version != last_head_version:
                    logger.info(
                        f"[WS_STORY] Head version mismatch: "
                        f"client={last_head_version}, server={current_progress.head_version}"
                    )

                    # Get current timeline
                    from app.crud import get_choice_ancestor_chain
                    from app.models import StoryNode

                    timeline_events = []
                    if current_progress.head_choice_id:
                        chain = await get_choice_ancestor_chain(
                            session=session,
                            choice_id=current_progress.head_choice_id
                        )
                        for choice in chain:
                            timeline_events.append({
                                "choice_id": str(choice.id),
                                "choice_text": choice.choice_text,
                                "from_node_id": str(choice.from_node_id),
                                "to_node_id": str(choice.to_node_id),
                                "choice_time": choice.choice_time.isoformat(),
                            })

                    await websocket.send_json({
                        "type": "timeline.sync",
                        "head_version": current_progress.head_version,
                        "timeline": timeline_events,
                        "current_node_id": str(current_progress.current_node_id),
                        "story_state": current_progress.story_state,
                    })

            # Send handshake response
            await websocket.send_json({
                "type": "session.created",
                "story_id": str(story_id),
                "head_version": current_progress.head_version if current_progress else 0,
            })

            # Start background task to forward Redis messages
            async def forward_redis_to_websocket():
                async for message in pubsub.listen():
                    if message["type"] == "message":
                        await websocket.send_text(message["data"])

            import asyncio
            forward_task = asyncio.create_task(forward_redis_to_websocket())

            # Main message loop (for future: accept choices via WebSocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    logger.debug(f"[WS_STORY] Received: {data.get('type')}")

                    # Future: Handle choice.make, jump, undo via WebSocket
                    # For now, just echo back as not implemented
                    await websocket.send_json({
                        "type": "error",
                        "message": "Story mutations via WebSocket not yet implemented. Use REST API.",
                    })

            except WebSocketDisconnect:
                logger.info(f"[WS_STORY] Client disconnected from story {story_id}")
                forward_task.cancel()

        except Exception as e:
            logger.error(f"[WS_STORY] Error: {e}", exc_info=True)
            await websocket.send_json({
                "type": "error",
                "message": "Internal server error",
            })
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            logger.info(f"[WS_STORY] Cleanup complete for story {story_id}")

async def handle_user_message(
    websocket: WebSocket,
    room_id: UUID,
    user: User,
    content: str,
) -> None:
    """
    Handle user message from WebSocket.

    1. Emit room_message.user event (persisted + published to Redis)
    2. Trigger agents (if any active in room)
    3. Agents stream responses via Redis pub/sub

    Note: This creates a NEW transaction for each message.
    WebSocket connections are long-lived, not transactional.
    """
    try:
        # Create new session with transaction for this message
        async with async_session_maker() as session:
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