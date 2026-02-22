


backend-1  | DEBUG:python_multipart.multipart:Calling on_field_start with no data
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_name with data[0:8]
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_data with data[9:43]
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_end with no data
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_start with no data
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_name with data[44:52]
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_data with data[53:61]
backend-1  | DEBUG:python_multipart.multipart:Calling on_field_end with no data
backend-1  | DEBUG:python_multipart.multipart:Calling on_end with no data
backend-1  |       INFO   172.23.0.1:45354 - "POST /api/v1/login/access-token HTTP/1.1" 200
backend-1  |       INFO   172.23.0.1:45362 - "GET
backend-1  |              /api/v1/stories/172109da-8b5f-48f2-9e7a-4259657691dc HTTP/1.1" 200
backend-1  |       INFO   172.23.0.1:45362 - "GET
backend-1  |              /api/v1/stories/172109da-8b5f-48f2-9e7a-4259657691dc HTTP/1.1" 200
backend-1  |       INFO   172.23.0.1:45362 - "GET
backend-1  |              /api/v1/demos?limit=200&include_inactive=True HTTP/1.1" 307
backend-1  |       INFO   172.23.0.1:45362 - "GET
backend-1  |              /api/v1/demos/?limit=200&include_inactive=True HTTP/1.1" 200
backend-1  |       INFO   172.23.0.1:45362 - "POST
backend-1  |              /api/v1/demos/172109da-8b5f-48f2-9e7a-4259657691dc/session
backend-1  |              HTTP/1.1" 500
backend-1  |      ERROR   Exception in ASGI application
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/app/api/routes/demos.py", line 379, in resolve_demo_session_for_slug
backend-1  |     existing = await touch_demo_session(session, existing)
backend-1  |   File "/app/app/crud_demo.py", line 338, in touch_demo_session
backend-1  |     await session.refresh(demo_session)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/ext/asyncio/session.py", line 329, in refresh
backend-1  |     await greenlet_spawn(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 190, in greenlet_spawn
backend-1  |     result = context.switch(*args, **kwargs)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 3154, in refresh
backend-1  |     loading.load_on_ident(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/loading.py", line 510, in load_on_ident
backend-1  |     return load_on_pk_identity(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/loading.py", line 695, in load_on_pk_identity
backend-1  |     session.execute(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlmodel/orm/session.py", line 144, in execute
backend-1  |     return super().execute(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2351, in execute
backend-1  |     return self._execute_internal(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2239, in _execute_internal
backend-1  |     conn = self._connection_for_bind(bind)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2103, in _connection_for_bind
backend-1  |     TransactionalContext._trans_ctx_check(self)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/util.py", line 111, in _trans_ctx_check
backend-1  |     raise exc.InvalidRequestError(
backend-1  | sqlalchemy.exc.InvalidRequestError: Can't operate on closed transaction inside context manager.  Please complete the context manager before emitting further commands.
backend-1  | ERROR:uvicorn.error:Exception in ASGI application
backend-1  | Traceback (most recent call last):
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/uvicorn/protocols/http/httptools_impl.py", line 409, in run_asgi
backend-1  |     result = await app(  # type: ignore[func-returns-value]
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
backend-1  |     return await self.app(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/fastapi/applications.py", line 1054, in __call__
backend-1  |     await super().__call__(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/applications.py", line 112, in __call__
backend-1  |     await self.middleware_stack(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/middleware/errors.py", line 187, in __call__
backend-1  |     raise exc
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/middleware/errors.py", line 165, in __call__
backend-1  |     await self.app(scope, receive, _send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/middleware/cors.py", line 85, in __call__
backend-1  |     await self.app(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/middleware/exceptions.py", line 62, in __call__
backend-1  |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
backend-1  |     raise exc
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
backend-1  |     await app(scope, receive, sender)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/routing.py", line 714, in __call__
backend-1  |     await self.middleware_stack(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/routing.py", line 734, in app
backend-1  |     await route.handle(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/routing.py", line 288, in handle
backend-1  |     await self.app(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/routing.py", line 76, in app
backend-1  |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
backend-1  |     raise exc
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
backend-1  |     await app(scope, receive, sender)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/starlette/routing.py", line 73, in app
backend-1  |     response = await f(request)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/fastapi/routing.py", line 301, in app
backend-1  |     raw_response = await run_endpoint_function(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/fastapi/routing.py", line 212, in run_endpoint_function
backend-1  |     return await dependant.call(**values)
backend-1  |   File "/app/app/api/routes/demos.py", line 379, in resolve_demo_session_for_slug
backend-1  |     existing = await touch_demo_session(session, existing)
backend-1  |   File "/app/app/crud_demo.py", line 338, in touch_demo_session
backend-1  |     await session.refresh(demo_session)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/ext/asyncio/session.py", line 329, in refresh
backend-1  |     await greenlet_spawn(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/util/_concurrency_py3k.py", line 190, in greenlet_spawn
backend-1  |     result = context.switch(*args, **kwargs)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 3154, in refresh
backend-1  |     loading.load_on_ident(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/loading.py", line 510, in load_on_ident
backend-1  |     return load_on_pk_identity(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/loading.py", line 695, in load_on_pk_identity
backend-1  |     session.execute(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlmodel/orm/session.py", line 144, in execute
backend-1  |     return super().execute(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2351, in execute
backend-1  |     return self._execute_internal(
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2239, in _execute_internal
backend-1  |     conn = self._connection_for_bind(bind)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/orm/session.py", line 2103, in _connection_for_bind
backend-1  |     TransactionalContext._trans_ctx_check(self)
backend-1  |   File "/app/.venv/lib/python3.10/site-packages/sqlalchemy/engine/util.py", line 111, in _trans_ctx_check
backend-1  |     raise exc.InvalidRequestError(
backend-1  | sqlalchemy.exc.InvalidRequestError: Can't operate on closed transaction inside context manager.  Please complete the context manager before emitting further commands.
