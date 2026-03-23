import asyncio
import json
import logging
import subprocess
import uuid
import threading
from contextlib import asynccontextmanager
from enum import Enum
import time

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic_settings import BaseSettings

from tokens import token_store
from rebuild_jobs import rebuild_store, RebuildStatus
from rebuild_worker import rebuild_flavour
from flavours import FLAVOURS

# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    kennel_redis_host:          str = "redis"
    kennel_redis_port:          int = 6379
    kennel_redis_event_channel: str = "kennel:events"
    kennel_secret:              str = ""
    kennel_base_image:          str = "ubuntu"
    kennel_base_release:        str = "noble"
    kennel_max_envs:            int = 20

    class Config:
        env_file = ".env"

settings  = Settings()
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background token reaper
    asyncio.create_task(token_store.reap_expired())
    yield


app = FastAPI(lifespan=lifespan)


# ── Auth helpers ──────────────────────────────────────────────────────────────

def require_management_secret(x_kennel_secret: str = Header(None)):
    """
    Used on all management endpoints (create, destroy, inject, list).
    This is the shared backend→kennel secret, never exposed to browser clients.
    """
    if settings.kennel_secret and x_kennel_secret != settings.kennel_secret:
        raise HTTPException(status_code=403, detail="Invalid kennel secret")


def verify_ws_token(token: str, env_name: str) -> None:
    """
    Used on WebSocket endpoints.
    Validates per-workspace short-lived token — not the management secret.
    """
    valid, reason = token_store.validate(token, env_name)
    if not valid:
        raise HTTPException(403, detail=f"Token rejected: {reason}")


# ── Models ────────────────────────────────────────────────────────────────────

class EnvKind(str, Enum):
    ephemeral  = "ephemeral"
    persistent = "persistent"

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    done    = "done"
    failed  = "failed"

class CreateEnvRequest(BaseModel):
    name:               str | None = None
    kind:               EnvKind    = EnvKind.ephemeral
    flavour:            str        = "dev"
    template:           str        = "download"
    distro:             str        = "ubuntu"
    release:            str        = "noble"
    arch:               str        = "amd64"
    base_snapshot:      str | None = None
    base_snapshot_name: str | None = None

class EnvAction(BaseModel):
    action: str   # start | stop | restart

class InjectRequest(BaseModel):
    """
    Workspace personalisation — applied after container is running.
    All fields optional so callers can inject incrementally.
    """
    user:       str             = "dev"
    ssh_pubkey: str | None      = None
    repo_url:   str | None      = None
    env_vars:   dict[str, str]  = {}
    git_name:   str | None      = None
    git_email:  str | None      = None
    # TTL for the issued terminal token (seconds)
    token_ttl:  int             = 3600


class IssueTerminalTokenRequest(BaseModel):
    token_ttl: int = 3600


# ── Job state ─────────────────────────────────────────────────────────────────

jobs: dict[str, dict] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def lxc(*args, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args), capture_output=True, text=True, timeout=timeout
    )


async def publish_event(env_name: str, event: str, data: dict = {}):
    payload = json.dumps({"env": env_name, "event": event, **data})
    redis_client = aioredis.Redis(
        host=settings.kennel_redis_host,
        port=settings.kennel_redis_port,
        decode_responses=True,
    )
    try:
        await redis_client.publish(settings.kennel_redis_event_channel, payload)
    finally:
        await redis_client.aclose()


def _attach_exec(env_name: str, cmd: str, timeout: int = 30) -> subprocess.CompletedProcess:
    """Run a shell command inside a running LXC container."""
    return subprocess.run(
        ["lxc-attach", "-n", env_name, "--", "bash", "-c", cmd],
        capture_output=True, text=True, timeout=timeout
    )


# ── Background create worker ──────────────────────────────────────────────────

def _create_env_worker(job_id: str, name: str, req: CreateEnvRequest):
    jobs[job_id]["status"] = JobStatus.running
    try:
        if req.base_snapshot:
            r = subprocess.run(
                ["lxc-copy", "-n", req.base_snapshot,
                 "-N", name, "-s",
                 *(["-B", req.base_snapshot_name] if req.base_snapshot_name else [])],
                capture_output=True, text=True, timeout=300,
            )
        else:
            if req.template == "download":
                create_cmd = [
                    "lxc-create",
                    "-n",
                    name,
                    "-t",
                    "download",
                    "--",
                    "-d",
                    req.distro,
                    "-r",
                    req.release,
                    "-a",
                    req.arch,
                ]
            else:
                create_cmd = [
                    "lxc-create",
                    "-n",
                    name,
                    "-t",
                    req.template,
                    "--",
                    "--release",
                    req.release,
                ]
            r = subprocess.run(
                create_cmd,
                capture_output=True,
                text=True,
                timeout=600,
            )

        if r.returncode != 0:
            jobs[job_id].update({"status": JobStatus.failed, "error": r.stderr})
            return

        start_args = ["lxc-start", "-n", name]
        if req.kind == EnvKind.ephemeral:
            start_args.append("-e")
        subprocess.run(start_args, timeout=30, capture_output=True)

        jobs[job_id]["status"] = JobStatus.done

        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            publish_event(name, "created", {"kind": req.kind})
        )
        loop.close()

    except subprocess.TimeoutExpired as e:
        jobs[job_id].update({"status": JobStatus.failed, "error": str(e)})
    except Exception as e:
        jobs[job_id].update({"status": JobStatus.failed, "error": str(e)})


# ── Routes: management (require_management_secret) ────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/envs")
def list_envs(_=Depends(require_management_secret)):
    result = lxc("lxc-ls", "--fancy", "--fancy-format", "name,state,ipv4,pid")
    return {"envs": result.stdout.strip().splitlines()}

@app.get("/flavours")
def list_flavours(_=Depends(require_management_secret)):
    """List all flavours and their current snapshot status."""
    result = {}
    for name, defn in FLAVOURS.items():
        base = f"base-{name}"
        snap_check = subprocess.run(
            ["lxc-snapshot", "-n", base, "-L"],
            capture_output=True, text=True
        )
        latest_job = rebuild_store.latest_for(name)
        result[name] = {
            "description":     defn.description,
            "parent":          defn.parent,
            "scripts":         defn.scripts,
            "snapshot_ready":  "snap0" in snap_check.stdout,
            "latest_job":      latest_job.job_id if latest_job else None,
            "latest_status":   latest_job.status if latest_job else None,
        }
    return result


@app.post("/flavours/{flavour}/rebuild")
def trigger_rebuild(
    flavour:          str,
    force:            bool = False,
    _=Depends(require_management_secret),
):
    """
    Kick off a flavour rebuild. Returns immediately with a job_id.
    Poll /rebuild-jobs/{job_id} for status, or stream logs via
    GET /rebuild-jobs/{job_id}/logs
    """
    if flavour not in FLAVOURS:
        raise HTTPException(404, f"Unknown flavour: {flavour}")

    # Prevent concurrent rebuilds of the same flavour
    existing = rebuild_store.latest_for(flavour)
    if existing and existing.status == RebuildStatus.running:
        return {
            "job_id":  existing.job_id,
            "status":  existing.status,
            "message": "rebuild already in progress",
        }

    job_id = f"rebuild-{uuid.uuid4().hex[:8]}"
    rebuild_store.create(job_id, flavour)

    thread = threading.Thread(
        target=rebuild_flavour,
        args=(job_id, flavour, force),
        daemon=True,
    )
    thread.start()

    return {
        "job_id":  job_id,
        "flavour": flavour,
        "status":  RebuildStatus.pending,
        "logs":    f"/rebuild-jobs/{job_id}/logs",
        "poll":    f"/rebuild-jobs/{job_id}",
    }


@app.get("/rebuild-jobs/{job_id}")
def get_rebuild_job(job_id: str, _=Depends(require_management_secret)):
    job = rebuild_store.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    elapsed = (
        round(time.monotonic() - job.started_at, 1)
        if job.started_at else None
    )
    return {
        "job_id":     job.job_id,
        "flavour":    job.flavour,
        "status":     job.status,
        "error":      job.error,
        "elapsed_s":  elapsed,
        "log_lines":  job.log_lines,
    }


@app.get("/rebuild-jobs/{job_id}/logs")
async def stream_rebuild_logs(
    job_id:    str,
    websocket: WebSocket,
):
    """
    WebSocket stream of live build output.
    Connect immediately after triggering a rebuild — replays
    buffered lines then streams new ones as they arrive.
    """
    # Use management secret for log streaming too
    token = websocket.query_params.get("token", "")
    if settings.kennel_secret and token != settings.kennel_secret:
        await websocket.close(code=4001)
        return

    job = rebuild_store.get(job_id)
    if not job:
        await websocket.close(code=4004)
        return

    await websocket.accept()
    queue = job.subscribe()

    try:
        while True:
            # Check if job finished and queue is drained
            try:
                line = queue.get_nowait()
                await websocket.send_text(line)
            except asyncio.QueueEmpty:
                if job.status in (RebuildStatus.done, RebuildStatus.failed):
                    # Send a final sentinel and close
                    await websocket.send_text(
                        f"[build {job.status} — {job.error or 'ok'}]"
                    )
                    break
                # Still running — wait for next line
                await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass
    finally:
        job.unsubscribe(queue)

@app.post("/envs", status_code=202)
async def create_env(req: CreateEnvRequest, _=Depends(require_management_secret)):
    name   = req.name or f"env-{uuid.uuid4().hex[:8]}"
    job_id = f"job-{uuid.uuid4().hex[:8]}"

    jobs[job_id] = {"status": JobStatus.pending, "env_name": name, "error": None}

    thread = threading.Thread(
        target=_create_env_worker, args=(job_id, name, req), daemon=True
    )
    thread.start()

    return {
        "job_id": job_id,
        "name":   name,
        "kind":   req.kind,
        "status": JobStatus.pending,
        "poll":   f"/jobs/{job_id}",
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: str, _=Depends(require_management_secret)):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


@app.delete("/envs/{name}")
async def destroy_env(name: str, _=Depends(require_management_secret)):
    token_store.revoke_for_env(name)      # invalidate any live terminal token
    lxc("lxc-stop", "-n", name, "-k")
    r = lxc("lxc-destroy", "-n", name)
    if r.returncode != 0:
        raise HTTPException(500, detail=r.stderr)
    await publish_event(name, "destroyed")
    return {"destroyed": name}


@app.post("/envs/{name}/action")
async def env_action(name: str, body: EnvAction, _=Depends(require_management_secret)):
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
    if body.action in ("stop", "restart"):
        token_store.revoke_for_env(name)  # force re-auth on next connect

    await publish_event(name, body.action)
    return {"env": name, "action": body.action}


# ── Inject endpoint ───────────────────────────────────────────────────────────

@app.post("/envs/{name}/inject")
async def inject_workspace(
    name: str,
    req:  InjectRequest,
    _=Depends(require_management_secret),
):
    """
    Applies workspace personalisation to a running container, then
    issues and returns a short-lived terminal token for that env.

    Called by the backend provisioner after lxc-create completes.
    Never called by browser clients.
    """
    errors = []

    # 1. SSH public key
    if req.ssh_pubkey:
        r = _attach_exec(name, f"""
            mkdir -p /home/{req.user}/.ssh
            chmod 700 /home/{req.user}/.ssh
            echo '{req.ssh_pubkey}' >> /home/{req.user}/.ssh/authorized_keys
            chmod 600 /home/{req.user}/.ssh/authorized_keys
            chown -R {req.user}:{req.user} /home/{req.user}/.ssh
        """)
        if r.returncode != 0:
            errors.append(f"ssh_pubkey: {r.stderr.strip()}")

    # 2. Git identity
    if req.git_name or req.git_email:
        git_cmds = []
        if req.git_name:
            git_cmds.append(f"git config --global user.name '{req.git_name}'")
        if req.git_email:
            git_cmds.append(f"git config --global user.email '{req.git_email}'")
        r = _attach_exec(name, f"su - {req.user} -c \"{' && '.join(git_cmds)}\"")
        if r.returncode != 0:
            errors.append(f"git_config: {r.stderr.strip()}")

    # 3. Environment variables → .bashrc and .profile
    if req.env_vars:
        env_block = "\n".join(
            f"export {k}={v}" for k, v in req.env_vars.items()
        )
        r = _attach_exec(name, f"""
            cat >> /home/{req.user}/.bashrc << 'ENVEOF'
# kennel workspace env
{env_block}
ENVEOF
        """)
        if r.returncode != 0:
            errors.append(f"env_vars: {r.stderr.strip()}")

    # 4. Repo clone
    if req.repo_url:
        r = _attach_exec(
            name,
            f"su - {req.user} -c "
            f"'git clone {req.repo_url} /home/{req.user}/workspace'",
            timeout=120,
        )
        if r.returncode != 0:
            errors.append(f"repo_clone: {r.stderr.strip()}")

    # 5. Issue terminal token — always issued even if some inject steps soft-failed
    ws_token = token_store.issue(name, ttl=req.token_ttl)

    await publish_event(name, "injected", {"errors": errors})

    return {
        "env":      name,
        "token":    ws_token,
        "errors":   errors,          # soft failures — non-fatal, logged by backend
        "terminal": f"/envs/{name}/ws",
    }


@app.post("/envs/{name}/terminal-token")
async def issue_terminal_token(
    name: str,
    req: IssueTerminalTokenRequest,
    _=Depends(require_management_secret),
):
    r = lxc("lxc-info", "-n", name)
    if r.returncode != 0:
        raise HTTPException(404, detail=f"Environment not found: {name}")

    ws_token = token_store.issue(name, ttl=req.token_ttl)
    return {
        "env": name,
        "token": ws_token,
        "terminal": f"/envs/{name}/ws",
    }


# ── WebSocket: terminal ───────────────────────────────────────────────────────

@app.websocket("/envs/{name}/ws")
async def env_terminal(websocket: WebSocket, name: str):
    """
    Browser connects here with the token issued by /inject.
    Token is validated before the lxc-attach subprocess is spawned.
    """
    token = websocket.query_params.get("token", "")
    client_host = getattr(websocket.client, "host", None)
    origin = websocket.headers.get("origin")
    user_agent = websocket.headers.get("user-agent")

    logger.info(
        "terminal websocket attempt env=%s client=%s origin=%s user_agent=%s token_prefix=%s",
        name,
        client_host,
        origin,
        user_agent,
        token[:8],
    )

    valid, reason = token_store.validate(token, name)
    if not valid:
        logger.warning(
            "terminal websocket rejected env=%s client=%s reason=%s token_prefix=%s",
            name,
            client_host,
            reason,
            token[:8],
        )
        await websocket.close(code=4001)
        return

    await websocket.accept()
    logger.info("terminal websocket accepted env=%s client=%s", name, client_host)

    proc = await asyncio.create_subprocess_exec(
        "lxc-attach", "-n", name, "--",
        "bash", "--login",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    async def read_output():
        try:
            while True:
                chunk = await proc.stdout.read(4096)
                if not chunk:
                    break
                await websocket.send_bytes(chunk)
        except Exception:
            logger.exception("terminal websocket output pump failed env=%s", name)
        finally:
            await websocket.close()

    async def read_input():
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break

                data = message.get("bytes")
                if data is None:
                    text = message.get("text")
                    if text is None:
                        continue
                    data = text.encode()

                proc.stdin.write(data)
                await proc.stdin.drain()
        except WebSocketDisconnect:
            logger.info("terminal websocket client disconnected env=%s client=%s", name, client_host)
        except Exception:
            logger.exception("terminal websocket input pump failed env=%s", name)
        finally:
            proc.stdin.close()

    await asyncio.gather(read_output(), read_input())
    proc.kill()
    logger.info("terminal websocket closed env=%s client=%s", name, client_host)
    await publish_event(name, "ws_disconnected")


# ── WebSocket: log stream ─────────────────────────────────────────────────────

@app.websocket("/envs/{name}/logs")
async def env_logs(websocket: WebSocket, name: str):
    """
    Streams lxc-monitor output. Uses the management secret —
    this is a backend/admin tool, not exposed to end users.
    """
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
