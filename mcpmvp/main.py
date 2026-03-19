from __future__ import annotations

import os
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from affordance_server import mcp as affordance_mcp
from story_server import mcp as story_mcp

HOST = os.getenv("MCPMVP_HOST", "0.0.0.0")
PORT = int(os.getenv("MCPMVP_PORT", "8080"))

affordance_app = affordance_mcp.http_app(path="/")
story_app = story_mcp.http_app(path="/")


async def health(_: Request) -> JSONResponse:
    return JSONResponse(
        {
            "status": "ok",
            "service": "mcpmvp",
            "servers": {
                "affordance": "/mcp/affordance",
                "story": "/mcp/story",
            },
        }
    )


@asynccontextmanager
async def lifespan(app: Starlette):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(affordance_app.lifespan(affordance_app))
        await stack.enter_async_context(story_app.lifespan(story_app))
        yield


app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/mcp/affordance", app=affordance_app),
        Mount("/mcp/story", app=story_app),
    ],
    lifespan=lifespan,
)


def main() -> None:
    uvicorn.run("main:app", host=HOST, port=PORT)


if __name__ == "__main__":
    main()
