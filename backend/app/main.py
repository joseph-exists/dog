import logging
import os
import threading
import asyncio
from contextlib import asynccontextmanager
import sentry_sdk
import logfire
from fastapi import FastAPI, Request
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware

# Initialize agent registry
import app.agents  # noqa: F401
from app.api.main import api_router
from app.api.routes.demos import run_demo_canvas_tesser_callback_listener
from app.core.config import settings
from app.services.kennel_event_listener import listen as run_kennel_event_listener
from app.services.shadow_outbox_worker import run_worker as run_shadow_outbox_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _demo_canvas_listener_stop_event, _demo_canvas_listener_task
    global _kennel_listener_stop_event, _kennel_listener_task

    # Start long-lived in-process listeners on app startup and stop them on shutdown.
    if os.getenv("SHADOW_OUTBOX_AUTOSTART", "1") != "1":
        logger.info("Shadow outbox worker autostart disabled")
    else:
        thread = threading.Thread(
            target=run_shadow_outbox_worker,
            name="shadow-outbox-worker",
            daemon=True,
        )
        thread.start()
        logger.info("Shadow outbox worker started")

    if _demo_canvas_listener_task is None or _demo_canvas_listener_task.done():
        _demo_canvas_listener_stop_event = asyncio.Event()
        _demo_canvas_listener_task = asyncio.create_task(
            run_demo_canvas_tesser_callback_listener(_demo_canvas_listener_stop_event)
        )
        logger.info("Demo canvas callback listener started")

    if _kennel_listener_task is None or _kennel_listener_task.done():
        _kennel_listener_stop_event = asyncio.Event()
        _kennel_listener_task = asyncio.create_task(
            run_kennel_event_listener(_kennel_listener_stop_event)
        )
        logger.info("Kennel event listener started")

    try:
        yield
    finally:
        if _demo_canvas_listener_stop_event is not None:
            _demo_canvas_listener_stop_event.set()
        if _kennel_listener_stop_event is not None:
            _kennel_listener_stop_event.set()

        if _demo_canvas_listener_task is not None:
            _demo_canvas_listener_task.cancel()
        if _kennel_listener_task is not None:
            _kennel_listener_task.cancel()

        if _demo_canvas_listener_task is not None:
            try:
                await _demo_canvas_listener_task
            except asyncio.CancelledError:
                pass

        if _kennel_listener_task is not None:
            try:
                await _kennel_listener_task
            except asyncio.CancelledError:
                pass

        _demo_canvas_listener_stop_event = None
        _demo_canvas_listener_task = None
        _kennel_listener_stop_event = None
        _kennel_listener_task = None


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"


if settings.SENTRY_DSN and settings.ENVIRONMENT != "local":
    sentry_sdk.init(dsn=str(settings.SENTRY_DSN), enable_tracing=True)

if settings.ENVIRONMENT == "woohoo":
    logfire.configure()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)
logger = logging.getLogger(__name__)


_demo_canvas_listener_stop_event: asyncio.Event | None = None
_demo_canvas_listener_task: asyncio.Task[None] | None = None
_kennel_listener_stop_event: asyncio.Event | None = None
_kennel_listener_task: asyncio.Task[None] | None = None


@app.exception_handler(ResponseValidationError)
async def response_validation_exception_handler(
    request: Request,
    exc: ResponseValidationError,
) -> JSONResponse:
    logger.exception(
        "Response validation error",
        extra={"path": request.url.path, "errors": exc.errors()},
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Response validation error"},
    )

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)
