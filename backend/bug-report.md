| ERROR:app.api.routes.rooms:run_agents_for_message failed; user message committed
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 199, in _key_not_found
backend-1  |     self._key_fallback(key, None)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 138, in _key_fallback
backend-1  |     raise KeyError(key) from err
backend-1  | KeyError: 'participant_id'
backend-1  |
backend-1  | The above exception was the direct cause of the following exception:
backend-1  |
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/rooms.py", line 353, in send_message
backend-1  |     await run_agents_for_message(
backend-1  |   File "/app/app/services/agent_runner.py", line 315, in run_agents_for_message
backend-1  |     coordinators, regular_agents = await _selection_service.select_agents_for_message(
backend-1  |   File "/app/app/services/agent_selection.py", line 154, in select_agents_for_message
backend-1  |     participant_id = participant.participant_id
backend-1  |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 66, in sqlalchemy.cyextension.resultproxy.BaseRow.__getattr__
backend-1  |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 63, in sqlalchemy.cyextension.resultproxy.BaseRow._get_by_key_impl
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 201, in _key_not_found
backend-1  |     raise AttributeError(ke.args[0]) from ke
backend-1  | AttributeError: participant_id




backend-1  | ERROR:app.api.routes.rooms:run_agents_for_message failed; user message committed
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 199, in _key_not_found
backend-1  |     self._key_fallback(key, None)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 138, in _key_fallback
backend-1  |     raise KeyError(key) from err
backend-1  | KeyError: 'participant_id'
backend-1  |
backend-1  | The above exception was the direct cause of the following exception:
backend-1  |
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/rooms.py", line 353, in send_message
backend-1  |     await run_agents_for_message(
backend-1  |   File "/app/app/services/agent_runner.py", line 315, in run_agents_for_message
backend-1  |     coordinators, regular_agents = await _selection_service.select_agents_for_message(
backend-1  |   File "/app/app/services/agent_selection.py", line 154, in select_agents_for_message
backend-1  |     participant_id = participant.participant_id
backend-1  |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 66, in sqlalchemy.cyextension.resultproxy.BaseRow.__getatt



backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event participant.joined to session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event participant.joined in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event participant.joined in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event participant.joined in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=bba92fab-7050-46eb-ba7b-ddab69cd50d1, event_type=participant.joined, sequence=10
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published participant.joined to Redis channel room:bba92fab-7050-46eb-ba7b-ddab69cd50d1, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event participant.joined in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #2 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: b'{"type": "event", "sequence": 10, "event_type": "participant.joined", "payload": {"participant_id": '
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:39140 - "POST
backend-1  |              /api/v1/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1/participants
backend-1  |              HTTP/1.1" 200
backend-1  | INFO:app.api.routes.websocket:[WS_ROUTE] ===== WebSocket route handler called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1 =====
backend-1  | INFO:app.api.routes.websocket:[WS] Connection attempt for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Disconnected: user=228d7ff2-960d-48b3-91a0-979034859cfe, room=bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Cleaning up connection for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   connection closed
backend-1  | INFO:uvicorn.error:connection closed
backend-1  | INFO:app.services.websocket_manager:Unsubscribed from room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:WebSocket disconnected from room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Authenticated user 228d7ff2-960d-48b3-91a0-979034859cfe for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.api.routes.websocket:[WS] Got DB session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:39152 - "GET
backend-1  |              /api/v1/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1/participants
backend-1  |              HTTP/1.1" 200
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Redis connection closed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1 (cleanup)
backend-1  | INFO:app.services.websocket_manager:[LISTENER] _listen_to_room exiting for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] User 228d7ff2-960d-48b3-91a0-979034859cfe verified as member of room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Calling connection_manager.connect for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] connect() called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:39156 - "WebSocket
backend-1  |              /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGc
backend-1  |              iOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyO
backend-1  |              GQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3i
backend-1  |              DZTOUtOmxpaZYwdOibOhZZrY"
backend-1  | INFO:uvicorn.error:172.24.0.1:39156 - "WebSocket /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyOGQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3iDZTOUtOmxpaZYwdOibOhZZrY" [accepted]
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket accepted for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Creating new connection set for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 now has 1 connections
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 not yet subscribed, calling _subscribe_to_room
backend-1  | INFO:app.services.websocket_manager:[REDIS] _subscribe_to_room() called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.websocket_manager:[REDIS] Got Redis client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Created pubsub client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Subscribing to channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Subscribe call completed for channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Added pubsub to room_subscriptions dict for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Creating background task for _listen_to_room for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Background task created: <Task pending name='Task-231' coro=<ConnectionManager._listen_to_room() running at /app/app/services/websocket_manager.py:174>>
backend-1  | INFO:app.services.websocket_manager:[REDIS] Successfully subscribed to Redis channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket connected to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] connection_manager.connect completed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Waiting for handshake from client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   connection open
backend-1  | INFO:uvicorn.error:connection open
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Starting _listen_to_room for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Entering pubsub.listen() loop for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #1 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: type=subscribe
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Subscription confirmed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1, channel=b'room:bba92fab-7050-46eb-ba7b-ddab69cd50d1'
backend-1  |       INFO   172.24.0.1:39140 - "GET
backend-1  |              /api/v1/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1/participants
backend-1  |              HTTP/1.1" 200
backend-1  | INFO:app.api.routes.websocket:[WS] Received handshake for room bba92fab-7050-46eb-ba7b-ddab69cd50d1, last_sequence=10
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying events since sequence 10 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:39152 - "OPTIONS /api/v1/agents/slug/nous HTTP/1.1" 200
backend-1  |       INFO   172.24.0.1:39140 - "OPTIONS /api/v1/agents/slug/nous HTTP/1.1" 200
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying 0 missed events for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Sending session.created response for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Entering main message loop for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:39152 - "GET /api/v1/agents/slug/nous HTTP/1.1" 200
backend-1  |       INFO   172.24.0.1:39152 - "GET /api/v1/agents/slug/nous HTTP/1.1" 200
backend-1  | DEBUG:app.api.routes.websocket:[WS] Received message type=message.send for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event room_message.user to session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event room_message.user in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event room_message.user in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event room_message.user in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=bba92fab-7050-46eb-ba7b-ddab69cd50d1, event_type=room_message.user, sequence=11
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published room_message.user to Redis channel room:bba92fab-7050-46eb-ba7b-ddab69cd50d1, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event room_message.user in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #2 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: b'{"type": "event", "sequence": 11, "event_type": "room_message.user", "payload": {"sender_id": "228d7'
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.agent_selection:Found database agent by slug: zebra-friday-monserrat
backend-1  | DEBUG:app.services.agent_selection:Found database agent by slug: nous
backend-1  | DEBUG:app.services.agent_runner:Agent 'zebzeb' skipped in room bba92fab-7050-46eb-ba7b-ddab69cd50d1: not mentioned (mode=on_mention)
backend-1  | INFO:app.services.agent_runner:Running agent 'nous' (slug: nous) in room bba92fab-7050-46eb-ba7b-ddab69cd50d1 (mentioned in message)
backend-1  | DEBUG:app.services.agent_selection:Found database agent by slug: nous
backend-1  |       INFO   connection closed
backend-1  | INFO:uvicorn.error:connection closed
backend-1  | INFO:app.api.routes.websocket:[WS_ROUTE] ===== WebSocket route handler called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1 =====
backend-1  | INFO:app.api.routes.websocket:[WS] Connection attempt for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | WARNING:app.services.shadow_context_loader:Missing Shadow snapshot for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: Shadow repo not found for room/bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Authenticated user 228d7ff2-960d-48b3-91a0-979034859cfe for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.api.routes.websocket:[WS] Got DB session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | WARNING:app.services.shadow_context_loader:Missing Shadow snapshot for agent ad68d446-29ba-4b1a-8dcb-8fdc92c73ffc: Shadow repo not found for agent/ad68d446-29ba-4b1a-8dcb-8fdc92c73ffc
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.api.routes.websocket:[WS] User 228d7ff2-960d-48b3-91a0-979034859cfe verified as member of room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Calling connection_manager.connect for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] connect() called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:48202 - "WebSocket
backend-1  |              /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGc
backend-1  |              iOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyO
backend-1  |              GQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3i
backend-1  |              DZTOUtOmxpaZYwdOibOhZZrY"
backend-1  | INFO:uvicorn.error:172.24.0.1:48202 - "WebSocket /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyOGQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3iDZTOUtOmxpaZYwdOibOhZZrY" [accepted]
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket accepted for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 now has 2 connections
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 already has active Redis subscription
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket connected to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] connection_manager.connect completed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Waiting for handshake from client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   connection open
backend-1  | INFO:uvicorn.error:connection open
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.api.routes.websocket:[WS] Received handshake for room bba92fab-7050-46eb-ba7b-ddab69cd50d1, last_sequence=11
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying events since sequence 11 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | ERROR:app.services.agent_runner_streaming:Agent nous streaming error in room bba92fab-7050-46eb-ba7b-ddab69cd50d1: is_enabled
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 199, in _key_not_found
backend-1  |     self._key_fallback(key, None)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 138, in _key_fallback
backend-1  |     raise KeyError(key) from err
backend-1  | KeyError: 'is_enabled'
backend-1  |
backend-1  | The above exception was the direct cause of the following exception:
backend-1  |
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/services/agent_runner_streaming.py", line 69, in run
backend-1  |     agent = await self._get_agent_instance_with_tools(
backend-1  |   File "/app/app/services/agent_instance.py", line 190, in get_agent_instance_with_tools
backend-1  |     if not config or not config.is_enabled:
backend-1  |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 66, in sqlalchemy.cyextension.resultproxy.BaseRow.__getattr__
backend-1  |   File "lib/sqlalchemy/cyextension/resultproxy.pyx", line 63, in sqlalchemy.cyextension.resultproxy.BaseRow._get_by_key_impl
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/result.py", line 201, in _key_not_found
backend-1  |     raise AttributeError(ke.args[0]) from ke
backend-1  | AttributeError: is_enabled
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying 0 missed events for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Sending session.created response for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Entering main message loop for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Added event room_message.agent to session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Updated projections for event room_message.agent in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Flushing session for event room_message.agent in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.event_emitter:[EMIT] Session flushed for event room_message.agent in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.event_emitter:[EMIT] About to publish to Redis: room=bba92fab-7050-46eb-ba7b-ddab69cd50d1, event_type=room_message.agent, sequence=12
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.realtime_publisher:Published room_message.agent to Redis channel room:bba92fab-7050-46eb-ba7b-ddab69cd50d1, subscribers: 1
backend-1  | INFO:app.services.event_emitter:[EMIT] Redis publish completed for event room_message.agent in room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #3 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: type=message
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Processing message for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: b'{"type": "event", "sequence": 12, "event_type": "room_message.agent", "payload": {"agent_name": "nou'
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Parsed JSON, sending to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | ERROR:app.services.websocket_manager:Error sending to WebSocket:
backend-1  | INFO:app.services.websocket_manager:WebSocket disconnected from room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Message forwarded to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | ERROR:app.api.routes.websocket:[WS] Error in room bba92fab-7050-46eb-ba7b-ddab69cd50d1: WebSocket is not connected. Need to call "accept" first.
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/websocket.py", line 134, in websocket_room_session
backend-1  |     data = await websocket.receive_json()
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/websockets.py", line 133, in receive_json
backend-1  |     raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
backend-1  | RuntimeError: WebSocket is not connected. Need to call "accept" first.
backend-1  | INFO:app.api.routes.websocket:[WS] Cleaning up connection for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |      ERROR   Exception in ASGI application
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/websocket.py", line 134, in websocket_room_session
backend-1  |     data = await websocket.receive_json()
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/websockets.py", line 133, in receive_json
backend-1  |     raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
backend-1  | RuntimeError: WebSocket is not connected. Need to call "accept" first.
backend-1  |
backend-1  | During handling of the above exception, another exception occurred:
backend-1  |<larger error in starlette cut>
backend-1  | RuntimeError: Cannot call "send" once a close message has been sent.
backend-1  | ERROR:uvicorn.error:Exception in ASGI application
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/websocket.py", line 134, in websocket_room_session
backend-1  |     data = await websocket.receive_json()
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/websockets.py", line 133, in receive_json
backend-1  |     raise RuntimeError('WebSocket is not connected. Need to call "accept" first.')
backend-1  | RuntimeError: WebSocket is not connected. Need to call "accept" first.
backend-1  |
backend-1  | During handling of the above exception, another exception occurred:
backend-1  |<middleware errors cut>
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/fastapi/routing.py", line 383, in app
backend-1  |     await dependant.call(**solved_result.values)
backend-1  |   File "/app/app/api/routes/websocket.py", line 151, in websocket_room_session
backend-1  |     await websocket.send_json({
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/websockets.py", line 175, in send_json
backend-1  |     await self.send({"type": "websocket.send", "text": text})
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/websockets.py", line 97, in send
backend-1  |     raise RuntimeError('Cannot call "send" once a close message has been sent.')
backend-1  | RuntimeError: Cannot call "send" once a close message has been sent.

backend-1  | INFO:app.api.routes.websocket:[WS_ROUTE] ===== WebSocket route handler called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1 =====
backend-1  | INFO:app.api.routes.websocket:[WS] Connection attempt for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Disconnected: user=228d7ff2-960d-48b3-91a0-979034859cfe, room=bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Cleaning up connection for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   connection closed
backend-1  | INFO:uvicorn.error:connection closed

backend-1  | INFO:app.services.websocket_manager:Unsubscribed from room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:WebSocket disconnected from room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Authenticated user 228d7ff2-960d-48b3-91a0-979034859cfe for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.api.routes.websocket:[WS] Got DB session for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Redis connection closed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1 (cleanup)
backend-1  | INFO:app.services.websocket_manager:[LISTENER] _listen_to_room exiting for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] User 228d7ff2-960d-48b3-91a0-979034859cfe verified as member of room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Calling connection_manager.connect for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] connect() called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:48222 - "WebSocket
backend-1  |              /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGc
backend-1  |              iOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyO
backend-1  |              GQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3i
backend-1  |              DZTOUtOmxpaZYwdOibOhZZrY"
backend-1  | INFO:uvicorn.error:172.24.0.1:48222 - "WebSocket /api/v1/ws/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Njk1NDQxNTgsInN1YiI6IjIyOGQ3ZmYyLTk2MGQtNDhiMy05MWEwLTk3OTAzNDg1OWNmZSJ9.sl12UcWM36hvqDvtf3iDZTOUtOmxpaZYwdOibOhZZrY" [accepted]
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket accepted for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Creating new connection set for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 now has 1 connections
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] Room bba92fab-7050-46eb-ba7b-ddab69cd50d1 not yet subscribed, calling _subscribe_to_room
backend-1  | INFO:app.services.websocket_manager:[REDIS] _subscribe_to_room() called for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Creating Redis client from pool
backend-1  | DEBUG:app.core.redis:[REDIS_GET] Redis client created: <redis.asyncio.client.Redis(<redis.asyncio.connection.ConnectionPool(<redis.asyncio.connection.Connection(host=redis,port=6379)>)>)>
backend-1  | INFO:app.services.websocket_manager:[REDIS] Got Redis client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Created pubsub client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Subscribing to channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Subscribe call completed for channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Added pubsub to room_subscriptions dict for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Creating background task for _listen_to_room for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[REDIS] Background task created: <Task pending name='Task-255' coro=<ConnectionManager._listen_to_room() running at /app/app/services/websocket_manager.py:174>>
backend-1  | INFO:app.services.websocket_manager:[REDIS] Successfully subscribed to Redis channel: room:bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[CONN_MGR] WebSocket connected to room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] connection_manager.connect completed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Waiting for handshake from client for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   connection open
backend-1  | INFO:uvicorn.error:connection open
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Starting _listen_to_room for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Entering pubsub.listen() loop for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | DEBUG:app.services.websocket_manager:[LISTENER] Received message #1 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1: type=subscribe
backend-1  | INFO:app.services.websocket_manager:[LISTENER] Subscription confirmed for room bba92fab-7050-46eb-ba7b-ddab69cd50d1, channel=b'room:bba92fab-7050-46eb-ba7b-ddab69cd50d1'
backend-1  | INFO:app.api.routes.websocket:[WS] Received handshake for room bba92fab-7050-46eb-ba7b-ddab69cd50d1, last_sequence=12
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying events since sequence 12 for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.rooms:list_messages success
backend-1  | INFO:app.api.routes.websocket:[WS] Replaying 0 missed events for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Sending session.created response for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  | INFO:app.api.routes.websocket:[WS] Entering main message loop for room bba92fab-7050-46eb-ba7b-ddab69cd50d1
backend-1  |       INFO   172.24.0.1:48216 - "GET
backend-1  |              /api/v1/rooms/bba92fab-7050-46eb-ba7b-ddab69cd50d1/messages?limit=5
backend-1  |              0&include_internal=false HTTP/1.1" 200