import asyncio
import json
import logging
import shlex
import subprocess
import uuid
import threading
from contextlib import asynccontextmanager
from enum import Enum
import time
from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
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
    bootstrap_plan: "BootstrapExecutionPlan | None" = None
    runtime_files: dict[str, str] = {}


class BootstrapSshKeyStep(BaseModel):
    type: Literal["add_ssh_key"] = "add_ssh_key"
    phase: str
    label: str
    ssh_pubkey: str


class BootstrapEnvVarsStep(BaseModel):
    type: Literal["write_env_vars"] = "write_env_vars"
    phase: str
    label: str
    env_vars: dict[str, str] = Field(default_factory=dict)


class BootstrapCloneRepoStep(BaseModel):
    type: Literal["clone_repo"] = "clone_repo"
    phase: str
    label: str
    repo_url: str
    target_path: str
    ref: str | None = None


class BootstrapRunCommandStep(BaseModel):
    type: Literal["run_command"] = "run_command"
    phase: str
    label: str
    command: str
    cwd: str | None = None
    background: bool = False
    service_name: str | None = None


BootstrapPlanStep = Annotated[
    BootstrapSshKeyStep
    | BootstrapEnvVarsStep
    | BootstrapCloneRepoStep
    | BootstrapRunCommandStep,
    Field(discriminator="type"),
]


class BootstrapExecutionPlan(BaseModel):
    workspace_path: str = "/home/dev/workspace"
    steps: list[BootstrapPlanStep] = Field(default_factory=list)


class BootstrapStepResult(BaseModel):
    index: int
    type: str
    phase: str
    label: str
    status: Literal["completed", "failed"]
    error: str | None = None
    service_name: str | None = None


class DeclaredWorkspaceService(BaseModel):
    id: str
    service_name: str
    label: str
    kind: Literal["web_app", "agent_runtime", "jupyter", "custom"] = "custom"
    protocol: Literal["http", "https", "ws", "wss"] = "http"
    port: int | None = None
    path: str | None = None
    source: Literal["bootstrap_profile", "runtime_probe", "operator_declared"] = "bootstrap_profile"
    workspace_path: str | None = None
    pid_path: str | None = None
    log_path: str | None = None
    service_name_hint: str | None = None


class DiscoveredWorkspaceService(BaseModel):
    id: str
    service_name: str
    label: str
    kind: Literal["web_app", "agent_runtime", "jupyter", "custom"] = "custom"
    status: Literal["pending", "ready", "failed", "unknown"] = "unknown"
    protocol: Literal["http", "https", "ws", "wss"] = "http"
    host: str | None = None
    port: int | None = None
    path: str | None = None
    url: str | None = None
    source: Literal["bootstrap_profile", "runtime_probe", "operator_declared"] = "bootstrap_profile"
    readiness_message: str | None = None
    pid_running: bool = False
    port_listening: bool = False


SERVICE_MANIFEST_PATH = "/tmp/kennel-services.json"
SERVICE_PROFILE_DEFAULTS: dict[str, DeclaredWorkspaceService] = {
    "vite": DeclaredWorkspaceService(
        id="vite",
        service_name="vite",
        label="Vite Dev Server",
        kind="web_app",
        protocol="http",
        port=5173,
        path="/",
        service_name_hint="vite",
    ),
    "nextjs": DeclaredWorkspaceService(
        id="nextjs",
        service_name="nextjs",
        label="Next.js Dev Server",
        kind="web_app",
        protocol="http",
        port=3000,
        path="/",
        service_name_hint="nextjs",
    ),
    "fastapi": DeclaredWorkspaceService(
        id="fastapi",
        service_name="fastapi",
        label="FastAPI Runtime",
        kind="web_app",
        protocol="http",
        port=8000,
        path="/docs",
        service_name_hint="uvicorn",
    ),
    "codex": DeclaredWorkspaceService(
        id="codex",
        service_name="codex",
        label="Codex Runtime",
        kind="agent_runtime",
        protocol="http",
        port=4317,
        path="/",
        source="bootstrap_profile",
        service_name_hint="codex",
    ),
    "claude_code": DeclaredWorkspaceService(
        id="claude_code",
        service_name="claude_code",
        label="Claude Code Runtime",
        kind="agent_runtime",
        protocol="http",
        port=4318,
        path="/",
        source="bootstrap_profile",
        service_name_hint="claude",
    ),
    "hermes": DeclaredWorkspaceService(
        id="hermes",
        service_name="hermes",
        label="Hermes Runtime",
        kind="agent_runtime",
        protocol="http",
        port=4319,
        path="/",
        source="bootstrap_profile",
        service_name_hint="hermes",
    ),
}


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


def _shell_single_quote(value: str) -> str:
    return shlex.quote(value)


def _run_as_user(
    env_name: str,
    *,
    user: str,
    command: str,
    timeout: int = 120,
) -> subprocess.CompletedProcess:
    quoted_command = _shell_single_quote(command)
    return _attach_exec(
        env_name,
        f"su - {user} -c {quoted_command}",
        timeout=timeout,
    )


def _ensure_parent_dir(env_name: str, path: str, *, user: str) -> subprocess.CompletedProcess:
    parent_dir = shlex.quote(path.rsplit("/", 1)[0] or "/")
    return _attach_exec(
        env_name,
        (
            f"mkdir -p {parent_dir} && "
            f"chown -R {user}:{user} {parent_dir}"
        ),
        timeout=30,
    )


def _legacy_bootstrap_plan(req: InjectRequest) -> BootstrapExecutionPlan:
    steps: list[BootstrapPlanStep] = []
    workspace_path = f"/home/{req.user}/workspace"

    if req.ssh_pubkey:
        steps.append(
            BootstrapSshKeyStep(
                phase="resolving_source",
                label="Authorize SSH key",
                ssh_pubkey=req.ssh_pubkey,
            )
        )
    if req.env_vars:
        steps.append(
            BootstrapEnvVarsStep(
                phase="resolving_source",
                label="Write workspace environment",
                env_vars=req.env_vars,
            )
        )
    if req.repo_url:
        steps.append(
            BootstrapCloneRepoStep(
                phase="materializing_repo",
                label="Clone repository",
                repo_url=req.repo_url,
                target_path=workspace_path,
            )
        )

    return BootstrapExecutionPlan(workspace_path=workspace_path, steps=steps)


def _write_runtime_file(
    env_name: str,
    *,
    path: str,
    content: str,
    user: str,
) -> subprocess.CompletedProcess:
    escaped_path = shlex.quote(path)
    parent_dir = shlex.quote(path.rsplit("/", 1)[0] or "/")
    payload = content
    return _attach_exec(
        env_name,
        (
            f"mkdir -p {parent_dir} && "
            f"cat > {escaped_path} <<'RUNTIMEFILE'\n{payload}\nRUNTIMEFILE\n"
            f"chown -R {user}:{user} {parent_dir} && "
            f"chmod 644 {escaped_path}"
        ),
        timeout=30,
    )


def _service_manifest_for_plan(plan: BootstrapExecutionPlan) -> list[DeclaredWorkspaceService]:
    services: list[DeclaredWorkspaceService] = []

    for step in plan.steps:
        if not isinstance(step, BootstrapRunCommandStep) or not step.background or not step.service_name:
            continue

        profile = SERVICE_PROFILE_DEFAULTS.get(step.service_name)
        if profile is None:
            services.append(
                DeclaredWorkspaceService(
                    id=step.service_name,
                    service_name=step.service_name,
                    label=step.label,
                    kind="custom",
                    protocol="http",
                    source="bootstrap_profile",
                    workspace_path=step.cwd,
                    pid_path=f"/tmp/{step.service_name}.pid",
                    log_path=f"/tmp/{step.service_name}.log",
                    service_name_hint=step.service_name,
                )
            )
            continue

        services.append(
            profile.model_copy(
                update={
                    "workspace_path": step.cwd,
                    "pid_path": f"/tmp/{step.service_name}.pid",
                    "log_path": f"/tmp/{step.service_name}.log",
                }
            )
        )

    return services


def _write_service_manifest(
    env_name: str,
    *,
    manifest: list[DeclaredWorkspaceService],
) -> subprocess.CompletedProcess:
    payload = json.dumps([service.model_dump(mode="json") for service in manifest])
    return _attach_exec(
        env_name,
        f"cat > {shlex.quote(SERVICE_MANIFEST_PATH)} <<'JSON'\n{payload}\nJSON\nchmod 644 {shlex.quote(SERVICE_MANIFEST_PATH)}",
        timeout=30,
    )


def _read_service_manifest(env_name: str) -> list[DeclaredWorkspaceService]:
    result = _attach_exec(
        env_name,
        f"if [ -f {shlex.quote(SERVICE_MANIFEST_PATH)} ]; then cat {shlex.quote(SERVICE_MANIFEST_PATH)}; fi",
        timeout=30,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return []
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    services: list[DeclaredWorkspaceService] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            services.append(DeclaredWorkspaceService.model_validate(item))
        except Exception:
            continue
    return services


def _is_pid_running(env_name: str, pid_path: str) -> bool:
    result = _attach_exec(
        env_name,
        (
            f"if [ -f {shlex.quote(pid_path)} ]; then "
            f"PID=$(cat {shlex.quote(pid_path)}); "
            "kill -0 \"$PID\" >/dev/null 2>&1; "
            "else exit 1; fi"
        ),
        timeout=15,
    )
    return result.returncode == 0


def _is_port_listening(env_name: str, port: int) -> bool:
    result = _attach_exec(
        env_name,
        (
            "if command -v ss >/dev/null 2>&1; then "
            f"ss -ltn '( sport = :{port} )' | tail -n +2 | grep -q LISTEN; "
            "else exit 1; fi"
        ),
        timeout=15,
    )
    return result.returncode == 0


def _get_env_ipv4(env_name: str) -> str | None:
    result = lxc("lxc-info", "-n", env_name, "-iH")
    if result.returncode != 0:
        return None
    for line in result.stdout.splitlines():
        candidate = line.strip()
        if candidate and candidate.lower() != "n/a":
            return candidate
    return None


def _discover_service(env_name: str, declared: DeclaredWorkspaceService) -> DiscoveredWorkspaceService:
    pid_running = _is_pid_running(env_name, declared.pid_path) if declared.pid_path else False
    port_listening = _is_port_listening(env_name, declared.port) if declared.port else False
    env_host = _get_env_ipv4(env_name)

    status: Literal["pending", "ready", "failed", "unknown"]
    readiness_message: str | None

    if declared.port is not None and port_listening:
        status = "ready"
        readiness_message = f"Port {declared.port} is listening."
    elif pid_running and declared.port is None:
        status = "ready"
        readiness_message = "Runtime process is running."
    elif pid_running:
        status = "pending"
        readiness_message = "Process is running, but the expected port is not listening yet."
    elif declared.pid_path:
        status = "failed"
        readiness_message = "Expected service process is not running."
    else:
        status = "unknown"
        readiness_message = "No runtime process metadata is available for this service."

    url = None
    if declared.port is not None:
        path = declared.path or "/"
        url = f"{declared.protocol}://{env_host or '127.0.0.1'}:{declared.port}{path}"

    return DiscoveredWorkspaceService(
        id=declared.id,
        service_name=declared.service_name,
        label=declared.label,
        kind=declared.kind,
        status=status,
        protocol=declared.protocol,
        host=env_host or ("127.0.0.1" if declared.port is not None else None),
        port=declared.port,
        path=declared.path,
        url=url,
        source=declared.source,
        readiness_message=readiness_message,
        pid_running=pid_running,
        port_listening=port_listening,
    )


def _execute_bootstrap_step(
    env_name: str,
    *,
    user: str,
    step: BootstrapPlanStep,
) -> tuple[BootstrapStepResult, str | None]:
    if isinstance(step, BootstrapSshKeyStep):
        r = _attach_exec(env_name, f"""
            mkdir -p /home/{user}/.ssh
            chmod 700 /home/{user}/.ssh
            echo {_shell_single_quote(step.ssh_pubkey)} >> /home/{user}/.ssh/authorized_keys
            chmod 600 /home/{user}/.ssh/authorized_keys
            chown -R {user}:{user} /home/{user}/.ssh
        """)
        if r.returncode != 0:
            return (
                BootstrapStepResult(
                    index=0,
                    type=step.type,
                    phase=step.phase,
                    label=step.label,
                    status="failed",
                    error=r.stderr.strip(),
                ),
                r.stderr.strip(),
            )
        return (
            BootstrapStepResult(
                index=0,
                type=step.type,
                phase=step.phase,
                label=step.label,
                status="completed",
            ),
            None,
        )

    if isinstance(step, BootstrapEnvVarsStep):
        env_lines = []
        for key, value in step.env_vars.items():
            env_lines.append(f"export {key}={shlex.quote(value)}")
        env_block = "\n".join(env_lines)
        r = _attach_exec(env_name, f"""
            cat >> /home/{user}/.bashrc << 'ENVEOF'
# kennel workspace env
{env_block}
ENVEOF
            cat >> /home/{user}/.profile << 'ENVEOF'
# kennel workspace env
{env_block}
ENVEOF
            chown {user}:{user} /home/{user}/.bashrc /home/{user}/.profile
        """)
        if r.returncode != 0:
            return (
                BootstrapStepResult(
                    index=0,
                    type=step.type,
                    phase=step.phase,
                    label=step.label,
                    status="failed",
                    error=r.stderr.strip(),
                ),
                r.stderr.strip(),
            )
        return (
            BootstrapStepResult(
                index=0,
                type=step.type,
                phase=step.phase,
                label=step.label,
                status="completed",
            ),
            None,
        )

    if isinstance(step, BootstrapCloneRepoStep):
        parent_result = _ensure_parent_dir(env_name, step.target_path, user=user)
        if parent_result.returncode != 0:
            return (
                BootstrapStepResult(
                    index=0,
                    type=step.type,
                    phase=step.phase,
                    label=step.label,
                    status="failed",
                    error=parent_result.stderr.strip(),
                ),
                parent_result.stderr.strip(),
            )
        clone_command = (
            f"if [ -e {shlex.quote(step.target_path)} ]; then "
            f"echo 'Target path already exists: {step.target_path}' >&2; exit 1; "
            "fi && "
            f"git clone {shlex.quote(step.repo_url)} {shlex.quote(step.target_path)}"
        )
        if step.ref:
            clone_command += (
                f" && cd {shlex.quote(step.target_path)} "
                f"&& git checkout {shlex.quote(step.ref)}"
            )
        r = _run_as_user(env_name, user=user, command=clone_command, timeout=180)
        if r.returncode != 0:
            return (
                BootstrapStepResult(
                    index=0,
                    type=step.type,
                    phase=step.phase,
                    label=step.label,
                    status="failed",
                    error=r.stderr.strip(),
                ),
                r.stderr.strip(),
            )
        return (
            BootstrapStepResult(
                index=0,
                type=step.type,
                phase=step.phase,
                label=step.label,
                status="completed",
            ),
            None,
        )

    if isinstance(step, BootstrapRunCommandStep):
        cwd_prefix = f"cd {shlex.quote(step.cwd)} && " if step.cwd else ""
        if step.background:
            service_name = step.service_name or "workspace-service"
            log_path = f"/tmp/{service_name}.log"
            pid_path = f"/tmp/{service_name}.pid"
            command = (
                f"{cwd_prefix}nohup bash -lc {shlex.quote(step.command)} "
                f"> {shlex.quote(log_path)} 2>&1 < /dev/null & echo $! > {shlex.quote(pid_path)} "
                f"&& sleep 1 && kill -0 $(cat {shlex.quote(pid_path)})"
            )
        else:
            command = f"{cwd_prefix}{step.command}"
        r = _run_as_user(env_name, user=user, command=command, timeout=300)
        if r.returncode != 0:
            return (
                BootstrapStepResult(
                    index=0,
                    type=step.type,
                    phase=step.phase,
                    label=step.label,
                    status="failed",
                    error=r.stderr.strip(),
                    service_name=step.service_name,
                ),
                r.stderr.strip(),
            )
        return (
            BootstrapStepResult(
                index=0,
                type=step.type,
                phase=step.phase,
                label=step.label,
                status="completed",
                service_name=step.service_name,
            ),
            step.service_name,
        )

    return (
        BootstrapStepResult(
            index=0,
            type="unknown",
            phase="failed",
            label="Unknown bootstrap step",
            status="failed",
            error="Unknown bootstrap step",
        ),
        "Unknown bootstrap step",
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


@app.get("/envs/{name}/services")
def get_env_services(name: str, _=Depends(require_management_secret)):
    info = lxc("lxc-info", "-n", name)
    if info.returncode != 0:
        raise HTTPException(404, detail=f"Environment not found: {name}")

    declared_services = _read_service_manifest(name)
    services = [_discover_service(name, declared) for declared in declared_services]
    ready_service_count = sum(1 for service in services if service.status == "ready")

    return {
        "env": name,
        "services": [service.model_dump(mode="json") for service in services],
        "service_count": len(services),
        "ready_service_count": ready_service_count,
    }


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
    plan = req.bootstrap_plan or _legacy_bootstrap_plan(req)
    service_manifest = _service_manifest_for_plan(plan)
    step_results: list[dict] = []
    started_services: list[str] = []
    fatal_error: str | None = None

    # Git identity remains outside the bootstrap plan for now because it is
    # workspace-scoped personalization rather than repo/runtime orchestration.
    if req.git_name or req.git_email:
        git_cmds = []
        if req.git_name:
            git_cmds.append(f"git config --global user.name '{req.git_name}'")
        if req.git_email:
            git_cmds.append(f"git config --global user.email '{req.git_email}'")
        r = _attach_exec(name, f"su - {req.user} -c \"{' && '.join(git_cmds)}\"")
        if r.returncode != 0:
            errors.append(f"git_config: {r.stderr.strip()}")

    for path, content in req.runtime_files.items():
        if not path.strip():
            continue
        runtime_file_result = _write_runtime_file(
            name,
            path=path,
            content=content,
            user=req.user,
        )
        if runtime_file_result.returncode != 0:
            errors.append(f"runtime_file:{path}: {runtime_file_result.stderr.strip()}")

    for index, step in enumerate(plan.steps):
        result, service_or_error = _execute_bootstrap_step(
            name,
            user=req.user,
            step=step,
        )
        result = result.model_copy(update={"index": index})
        step_results.append(result.model_dump(mode="json"))
        if result.status == "failed":
            fatal_error = service_or_error
            errors.append(f"{step.type}: {service_or_error}")
            break
        if result.service_name and service_or_error:
            started_services.append(service_or_error)

    # Issue terminal token even when bootstrap fails so the backend can choose
    # how to expose or suppress recovery/debug flows.
    manifest_result = _write_service_manifest(name, manifest=service_manifest)
    if manifest_result.returncode != 0:
        errors.append(f"service_manifest: {manifest_result.stderr.strip()}")

    ws_token = token_store.issue(name, ttl=req.token_ttl)

    await publish_event(
        name,
        "injected",
        {
            "errors": errors,
            "bootstrap_success": fatal_error is None,
            "step_results": step_results,
        },
    )

    return {
        "env":               name,
        "token":             ws_token,
        "errors":            errors,
        "terminal":          f"/envs/{name}/ws",
        "bootstrap_success": fatal_error is None,
        "fatal_error":       fatal_error,
        "step_results":      step_results,
        "started_services":  started_services,
        "workspace_path":    plan.workspace_path,
        "declared_services": [service.model_dump(mode="json") for service in service_manifest],
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
