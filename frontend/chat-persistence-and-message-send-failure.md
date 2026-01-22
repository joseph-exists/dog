backend-1  | INFO:uvicorn.error:connection open
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Starting _listen_to_room for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Entering pubsub.listen() loop for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #1 for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: type=subscribe
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Subscription confirmed for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, channel=b'room:cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c'
backend-1  | INFO:app.api.routes.websocket:[WS] Received handshake for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, last_sequence=3
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying events since sequence 3 for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying 0 missed events for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.api.routes.websocket:[WS] Sending session.created response for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.api.routes.websocket:[WS] Entering main message loop for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.api.routes.websocket:[WS] Received message type=message.send for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event room_message.user to session for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, event_type=room_message.user, sequence=3
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published room_message.user to Redis channel room:cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #2 for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: b'{"type": "event", "sequence": 3, "event_type": "room_message.user", "payload": {"sender_id": "228d7f'
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.api.routes.websocket:[WS] Received message type=message.send for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event room_message.user to session for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, event_type=room_message.user, sequence=3
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published room_message.user to Redis channel room:cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #3 for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: b'{"type": "event", "sequence": 3, "event_type": "room_message.user", "payload": {"sender_id": "228d7f'
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.api.routes.websocket:[WS] Received message type=message.send for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event room_message.user to session for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, event_type=room_message.user, sequence=3
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published room_message.user to Redis channel room:cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event room_message.user in room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #4 for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c: b'{"type": "event", "sequence": 3, "event_type": "room_message.user", "payload": {"sender_id": "228d7f'
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room cd0d518d-f7b6-4259-9d8b-2d7f064b3c8c