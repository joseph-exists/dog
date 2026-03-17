import asyncio
import json
import subprocess
import uuid
from contextlib import asynccontextmanager
from enum import Enum

import redis.asyncio as aioredis
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    kennel_redis_host: str = "redis"
    kennel_redis_port: int = 6379
    kennel_redis_event_channel: str = "kennel:events"
    kennel_secret: str = ""
    kennel_base_image: str = "ubuntu"
    kennel_base_release: str = "noble"
    kennel_max_envs: int = 20

    class Config:
        env_file = ".env"

settings = Settings()
redis_client: aioredis.Redis = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    redis_client = aioredis.Redis(
        host=settings.kennel_redis_host,
        port=settings.kennel_redis_port,
        decode_responses=True
    )
    yield
    await redis_client.aclose()


app = FastAPI(lifespan=lifespan)


# ── Auth ──────────────────────────────────────────────────────────────────────

def verify_secret(x_kennel_secret: str = Header(None)):
    if settings.kennel_secret and x_kennel_secret != settings.kennel_secret:
        raise HTTPException(status_code=403, detail="Invalid kennel secret")


# ── Models ────────────────────────────────────────────────────────────────────

class EnvKind(str, Enum):
    ephemeral = "ephemeral"
    persistent = "persistent"

class CreateEnvRequest(BaseModel):
    name: str | None = None        # auto-generated if not provided
    kind: EnvKind = EnvKind.ephemeral
    template: str = "ubuntu"
    release: str = "noble"
    # optional: clone from a named base snapshot
    base_snapshot: str | None = None

class EnvAction(BaseModel):
    action: str   # start | stop | restart


# ── Helpers ───────────────────────────────────────────────────────────────────

def lxc(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args), capture_output=True, text=True, timeout=60
    )

async def publish_event(env_name: str, event: str, data: dict = {}):
    payload = json.dumps({"env": env_name, "event": event, **data})
    await redis_client.publish(settings.kennel_redis_event_channel, payload)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/envs")
def list_envs():
    result = lxc("lxc-ls", "--fancy",
                 "--fancy-format", "name,state,ipv4,pid")
    lines = result.stdout.strip().splitlines()
    return {"envs": lines}

@app.post("/envs")
async def create_env(req: CreateEnvRequest):
    name = req.name or f"env-{uuid.uuid4().hex[:8]}"

    if req.base_snapshot:
        # Clone from snapshot for fast boot
        r = lxc("lxc-copy", "-n", req.base_snapshot, "-N", name, "-s")
    else:
        r = lxc("lxc-create", "-n", name,
                "-t", req.template,
                "--", "--release", req.release)

    if r.returncode != 0:
        raise HTTPException(500, detail=r.stderr)

    if req.kind == EnvKind.ephemeral:
        # Ephemeral: auto-destroys on stop
        lxc("lxc-start", "-n", name, "-e")
    else:
        lxc("lxc-start", "-n", name)

    await publish_event(name, "created", {"kind": req.kind})
    return {"name": name, "kind": req.kind}

@app.delete("/envs/{name}")
async def destroy_env(name: str):
    lxc("lxc-stop", "-n", name, "-k")
    r = lxc("lxc-destroy", "-n", name)
    if r.returncode != 0:
        raise HTTPException(500, detail=r.stderr)
    await publish_event(name, "destroyed")
    return {"destroyed": name}

@app.post("/envs/{name}/action")
async def env_action(name: str, body: EnvAction):
    cmds = {
        "start":   ["lxc-start", "-n", name],
        "stop":    ["lxc-stop",  "-n", name],
        "restart": ["lxc-stop",  "-n", name],
    }
    if body.action not in cmds:
        raise HTTPException(400, "Unknown action")
    lxc(*cmds[body.action])
    if body.action == "restart":
        lxc("lxc-start", "-n", name)
    await publish_event(name, body.action)
    return {"env": name, "action": body.action}

@app.get("/envs/{name}/snapshot")
def snapshot_env(name: str, snapshot_name: str | None = None):
    snap = snapshot_name or f"snap-{uuid.uuid4().hex[:6]}"
    r = lxc("lxc-snapshot", "-n", name, "-c", snap)
    if r.returncode != 0:
        raise HTTPException(500, detail=r.stderr)
    return {"env": name, "snapshot": snap}


# ── WebSocket terminal ─────────────────────────────────────────────────────────
#
# ws://kennel.domain/envs/{name}/ws
# Bidirectional: client sends stdin, server streams stdout+stderr
#
@app.websocket("/envs/{name}/ws")
async def env_terminal(websocket: WebSocket, name: str):
    # Validate secret in query param for WS (headers unreliable in browsers)
    token = websocket.query_params.get("token", "")
    if settings.kennel_secret and token != settings.kennel_secret:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    proc = await asyncio.create_subprocess_exec(
        "lxc-attach", "-n", name, "--",
        "bash", "--login",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    async def read_output():
        """Pump proc stdout → WebSocket."""
        try:
            while True:
                chunk = await proc.stdout.read(4096)
                if not chunk:
                    break
                await websocket.send_bytes(chunk)
        except Exception:
            pass
        finally:
            await websocket.close()

    async def read_input():
        """Pump WebSocket → proc stdin."""
        try:
            while True:
                data = await websocket.receive_bytes()
                proc.stdin.write(data)
                await proc.stdin.drain()
        except WebSocketDisconnect:
            pass
        finally:
            proc.stdin.close()

    await asyncio.gather(read_output(), read_input())
    proc.kill()
    await publish_event(name, "ws_disconnected")


# ── Log stream WebSocket ───────────────────────────────────────────────────────
#
# ws://kennel.domain/envs/{name}/logs
# Server-only stream of lxc-monitor output for this container
#
@app.websocket("/envs/{name}/logs")
async def env_logs(websocket: WebSocket, name: str):
    token = websocket.query_params.get("token", "")
    if settings.kennel_secret and token != settings.kennel_secret:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    proc = await asyncio.create_subprocess_exec(
        "lxc-monitor", "--name", name,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            await websocket.send_text(line.decode())
    except WebSocketDisconnect:
        pass
    finally:
        proc.kill()