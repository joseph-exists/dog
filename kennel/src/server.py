import asyncio
import errno
import fcntl
import json
import logging
import os
import pty
import shlex
import signal
import struct
import subprocess
import termios
import uuid
import threading
from contextlib import asynccontextmanager, suppress
from enum import Enum
import time
from typing import Annotated, Literal

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Header
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import websockets

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
    kennel_gittin_guest_host:   str = "gittin"
    kennel_gittin_guest_ip:     str = "10.0.3.1"
    kennel_tinyfoot_api_url:    str = "http://10.0.3.1:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"

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


class RuntimePreset(str, Enum):
    codex = "codex"
    claude_code = "claude_code"
    hermes = "hermes"
    typer = "typer"
    codex_typer = "codex_typer"
    claude_code_typer = "claude_code_typer"
    hermes_typer = "hermes_typer"

class CreateEnvRequest(BaseModel):
    name:               str | None = None
    kind:               EnvKind    = EnvKind.ephemeral
    flavour:            str        = "dev"
    runtime_preset:     RuntimePreset | None = None
    template:           str        = "download"
    distro:             str        = "ubuntu"
    release:            str        = "noble"
    arch:               str        = "amd64"
    base_container:     str | None = None
    # Deprecated compatibility fields from the older snapshot-based model.
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
    runtime_preset: RuntimePreset | None = None
    bootstrap_profile: str | None = None
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
    runtime_id: str | None = None
    runtime_profile: str | None = None
    transport_kind: str | None = None
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
    runtime_id: str | None = None
    runtime_profile: str | None = None
    transport_kind: str | None = None
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
# This registry is kennel's current interpretation of shared runtime/service
# identifiers when a bootstrap step declares `service_name`.
#
# These entries are intentionally operational rather than absolute. They capture
# kennel's current metadata and readiness expectations so backend and kennel can
# reason about the same runtime identifiers explicitly, while still leaving room
# to refine those expectations in later iterations.
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
        runtime_id="codex",
        runtime_profile="codex_app_server",
        transport_kind="websocket",
        protocol="ws",
        port=4500,
        path="/",
        source="bootstrap_profile",
        service_name_hint="codex",
    ),
    "claude_code": DeclaredWorkspaceService(
        id="claude_code",
        service_name="claude_code",
        label="Claude Code Runtime",
        kind="agent_runtime",
        runtime_id="claude_code",
        runtime_profile="claude_code_remote_control",
        transport_kind="websocket",
        protocol="ws",
        port=None,
        path=None,
        source="bootstrap_profile",
        service_name_hint="claude",
    ),
    "hermes": DeclaredWorkspaceService(
        id="hermes",
        service_name="hermes",
        label="Hermes Runtime",
        kind="agent_runtime",
        runtime_id="hermes",
        runtime_profile="hermes_gateway_ws",
        # This websocket endpoint is consumed through backend-routed runtime
        # invoke semantics for rooms, not as a browser-owned transport.
        transport_kind="websocket",
        protocol="ws",
        port=4319,
        path="/",
        source="bootstrap_profile",
        service_name_hint="hermes",
    ),
    "hermes_api": DeclaredWorkspaceService(
        id="hermes_api",
        service_name="hermes_api",
        label="Hermes API Server",
        kind="agent_runtime",
        runtime_id="hermes",
        runtime_profile="hermes_api_server",
        transport_kind="http",
        protocol="http",
        port=8642,
        path="/",
        source="bootstrap_profile",
        service_name_hint="hermes",
    ),
}


class IssueTerminalTokenRequest(BaseModel):
    token_ttl: int = 3600


class AgentRuntimeInvokeRequest(BaseModel):
    invoke_mode: Literal["websocket", "command", "json_rpc", "http"] = "websocket"
    payload: dict | list | str | None = None
    json_rpc_session: "JsonRpcInvokeSessionRequest | None" = None
    argv: list[str] = Field(default_factory=list)
    cwd: str | None = None
    http_path: str = "/"
    user: str = "dev"
    timeout_seconds: float = Field(default=15.0, ge=1.0, le=300.0)


class JsonRpcInvokeRequestMessage(BaseModel):
    id: str | int
    method: str
    params: object | None = None


class JsonRpcInvokeSessionRequest(BaseModel):
    requests: list[JsonRpcInvokeRequestMessage] = Field(default_factory=list)
    terminal_notification_methods: list[str] = Field(default_factory=list)
    tracked_notification_methods: list[str] = Field(default_factory=list)
    fail_on_server_request: bool = True


AgentRuntimeInvokeRequest.model_rebuild()


# ── Job state ─────────────────────────────────────────────────────────────────

jobs: dict[str, dict] = {}


RUNTIME_PRESET_DEFAULTS: dict[RuntimePreset, dict[str, str]] = {
    RuntimePreset.codex: {
        "flavour": "dev-codex",
        "bootstrap_profile": "codex_app_server",
    },
    RuntimePreset.claude_code: {
        "flavour": "dev-claude-code",
        "bootstrap_profile": "claude_code_remote_control",
    },
    RuntimePreset.hermes: {
        "flavour": "hermes-agent",
        "bootstrap_profile": "hermes_agent_runtime",
    },
    RuntimePreset.typer: {
        "flavour": "dev",
        "bootstrap_profile": "",
    },
    RuntimePreset.codex_typer: {
        "flavour": "dev-codex",
        "bootstrap_profile": "codex_app_server",
    },
    RuntimePreset.claude_code_typer: {
        "flavour": "dev-claude-code",
        "bootstrap_profile": "claude_code_remote_control",
    },
    RuntimePreset.hermes_typer: {
        "flavour": "hermes-agent",
        "bootstrap_profile": "hermes_agent_runtime",
    },
}

RUNTIME_PRESETS_WITH_TYPER_ENV: frozenset[RuntimePreset] = frozenset(
    {
        RuntimePreset.typer,
        RuntimePreset.codex_typer,
        RuntimePreset.claude_code_typer,
        RuntimePreset.hermes_typer,
    }
)

# Presets map a kennel-facing runtime identifier to kennel-owned default flavour
# and bootstrap-profile choices. This is a defaulting layer, not a statement
# that every caller or integration path must adopt the same runtime semantics.


# ── Helpers ───────────────────────────────────────────────────────────────────

def lxc(*args, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        list(args), capture_output=True, text=True, timeout=timeout
    )


def _container_exists(name: str) -> bool:
    result = lxc("lxc-info", "-n", name)
    return result.returncode == 0


def _wait_for_attach_ready(
    name: str,
    *,
    timeout: float = 30.0,
    interval: float = 0.5,
) -> tuple[bool, str | None]:
    """
    Wait until a started container is ready for `lxc-attach`.

    Create jobs should not be marked done until inject operations can actually
    attach and run commands inside the environment.
    """

    deadline = time.monotonic() + timeout
    last_error: str | None = None

    while time.monotonic() < deadline:
        result = subprocess.run(
            ["lxc-attach", "-n", name, "--", "true"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return True, None
        last_error = (result.stderr or result.stdout or "").strip() or None
        time.sleep(interval)

    return False, last_error


def _start_env_container(name: str, *, kind: EnvKind) -> subprocess.CompletedProcess:
    """
    Start a container with plain lxc-start.

    Ephemerality is handled at creation time via `lxc-copy -s -B overlay`, so
    lxc-start -e is never needed here — it would try to layer a second overlay
    on an already-overlay-backed container, which causes lxc to create a monitor
    cgroup and then abort without cleaning it up, leaving a stale cgroup entry
    that breaks every subsequent start attempt on that container.
    """
    return lxc("lxc-start", "-n", name, timeout=30)


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


def _background_launch_command(
    *,
    cwd: str | None,
    command: str,
    log_path: str,
    pid_path: str,
) -> str:
    """
    Launch a long-lived workspace service without keeping `lxc-attach` alive.

    `nohup ... &` from within the attached shell leaves the spawned process tied
    closely enough to the attach session that `subprocess.run()` can block until
    timeout for long-running runtimes like `codex app-server`. Launching via a
    short Python supervisor lets the attached process exit promptly after it has
    spawned and verified the detached child.
    """

    launcher = {
        "cwd": cwd,
        "command": command,
        "log_path": log_path,
        "pid_path": pid_path,
    }
    launcher_json = json.dumps(launcher)
    return (
        "python3 -c "
        + shlex.quote(
            """
import json
import os
import signal
import subprocess
import sys
import time

cfg = json.loads(sys.argv[1])
with open(cfg["log_path"], "ab", buffering=0) as log_file:
    proc = subprocess.Popen(
        ["bash", "-lc", cfg["command"]],
        cwd=cfg["cwd"],
        stdin=subprocess.DEVNULL,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

with open(cfg["pid_path"], "w", encoding="utf-8") as pid_file:
    pid_file.write(f"{proc.pid}\\n")

time.sleep(1.0)
os.kill(proc.pid, 0)
"""
        )
        + " "
        + shlex.quote(launcher_json)
    )


def _terminal_shell_command() -> str:
    """
    Prefer the workspace user for browser terminals when available.

    Runtime tooling is currently provisioned primarily for the `dev` user, so a
    root login shell can present a misleadingly incomplete PATH even when the
    environment itself is healthy. Browser terminal sessions now run on a PTY,
    but startup should still source the user runtime environment explicitly
    instead of relying on interactive shell initialization alone. Falling back
    to root keeps terminal access available for older or partially initialized
    envs.
    """

    return (
        'export TERM="${TERM:-xterm-256color}"; '
        'export COLORTERM="${COLORTERM:-truecolor}"; '
        "if id -u dev >/dev/null 2>&1; then "
        "exec su - dev -c "
        + shlex.quote(
            'export TERM="${TERM:-xterm-256color}"; '
            'export COLORTERM="${COLORTERM:-truecolor}"; '
            'export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; '
            'if [ -s "$NVM_DIR/nvm.sh" ]; then '
            '. "$NVM_DIR/nvm.sh" >/dev/null 2>&1; '
            'nvm use default >/dev/null 2>&1 || true; '
            'fi; '
            'exec bash -il'
        )
        + "; "
        "else "
        "exec bash --login; "
        "fi"
    )


class TerminalControlResize(BaseModel):
    type: Literal["terminal_control"] = "terminal_control"
    control: Literal["resize"] = "resize"
    cols: int = Field(..., ge=1, le=1000)
    rows: int = Field(..., ge=1, le=1000)


def _parse_terminal_control_message(text: str) -> TerminalControlResize | None:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict) or payload.get("type") != "terminal_control":
        return None

    try:
        return TerminalControlResize.model_validate(payload)
    except Exception:
        logger.warning("terminal control message rejected payload=%s", payload)
        return None


def _spawn_terminal_pty(env_name: str) -> tuple[int, int]:
    pid, master_fd = pty.fork()
    if pid == 0:
        os.execvpe(
            "lxc-attach",
            [
                "lxc-attach",
                "-n",
                env_name,
                "--",
                "bash",
                "-lc",
                _terminal_shell_command(),
            ],
            {
                **os.environ,
                "TERM": os.environ.get("TERM", "xterm-256color"),
                "COLORTERM": os.environ.get("COLORTERM", "truecolor"),
            },
        )
    return pid, master_fd


def _set_pty_winsize(fd: int, cols: int, rows: int) -> None:
    fcntl.ioctl(
        fd,
        termios.TIOCSWINSZ,
        struct.pack("HHHH", rows, cols, 0, 0),
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


def _codex_runtime_files(user: str) -> dict[str, str]:
    user_home = f"/home/{user}"
    return {
        f"{user_home}/.codex/config.toml": """model = "gpt-5.4"
model_provider = "openai"
cli_auth_credentials_store = "file"
"""
    }


def _claude_code_runtime_files(user: str) -> dict[str, str]:
    user_home = f"/home/{user}"
    return {
        f"{user_home}/.claude/settings.json": json.dumps(
            {
                "env": {
                    "DISABLE_AUTOUPDATER": "1",
                }
            },
            indent=2,
        )
    }


def _hermes_runtime_files(user: str) -> dict[str, str]:
    user_home = f"/home/{user}"
    hermes_test_env = (
        "# Test-environment Hermes settings for kennel-managed workspaces.\n"
        "GATEWAY_ALLOW_ALL_USERS=true\n"
        "OPENROUTER_API_KEY=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\n"
    )
    return {
        f"{user_home}/.hermes/config.yaml": (
            "# Hermes runtime configuration for kennel-managed workspaces.\n"
            "# Align these values with Hermes gateway setup from the official quickstart.\n"
            "gateway:\n"
            "  listen: ${HERMES_GATEWAY_LISTEN:-ws://0.0.0.0:4319}\n"
            "  transport: websocket\n"
            "runtime:\n"
            "  profile: kennel\n"
            "  workspace_path: /home/dev/workspace\n"
        ),
        f"{user_home}/.hermes.env": hermes_test_env,
        f"{user_home}/.hermes/.env": (
            "# Workspace-scoped Hermes secrets.\n"
            "# Keep real values in this file or inject them through workspace env vars.\n"
            "HERMES_API_KEY=\n"
            "HERMES_GATEWAY_TOKEN=\n"
            "API_SERVER_ENABLED=false\n"
            "API_SERVER_HOST=127.0.0.1\n"
            "API_SERVER_PORT=8642\n"
            "API_SERVER_KEY=\n"
        ),
        f"{user_home}/.hermes/hermes-agent-launcher": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "export PATH=\"$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH\"\n"
            "export DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE=\"${DOG_WORKSPACE_AGENT_HERMES_RUNTIME_MODE:-gateway_ws}\"\n"
            "export DOG_WORKSPACE_AGENT_HERMES_HOST=\"${DOG_WORKSPACE_AGENT_HERMES_HOST:-0.0.0.0}\"\n"
            "export DOG_WORKSPACE_AGENT_HERMES_PORT=\"${DOG_WORKSPACE_AGENT_HERMES_PORT:-4319}\"\n"
            "export HERMES_GATEWAY_LISTEN=\"${HERMES_GATEWAY_LISTEN:-ws://${DOG_WORKSPACE_AGENT_HERMES_HOST}:${DOG_WORKSPACE_AGENT_HERMES_PORT}}\"\n"
            "if [ -f \"$HOME/.hermes.env\" ]; then\n"
            "  set -a\n"
            "  # shellcheck disable=SC1090\n"
            "  source \"$HOME/.hermes.env\"\n"
            "  set +a\n"
            "fi\n"
            "if [ -f \"$HOME/.hermes/.env\" ]; then\n"
            "  set -a\n"
            "  # shellcheck disable=SC1090\n"
            "  source \"$HOME/.hermes/.env\"\n"
            "  set +a\n"
            "fi\n"
            "if ! command -v hermes >/dev/null 2>&1 && ! command -v hermes-agent >/dev/null 2>&1; then\n"
            "  if [ \"${DOG_WORKSPACE_AGENT_HERMES_AUTO_INSTALL:-true}\" = \"true\" ] && command -v curl >/dev/null 2>&1; then\n"
            "    echo \"Hermes runtime command not found; attempting installer bootstrap.\" >&2\n"
            "    if command -v getent >/dev/null 2>&1 && ! getent hosts raw.githubusercontent.com >/dev/null 2>&1; then\n"
            "      echo \"Hermes installer bootstrap skipped: raw.githubusercontent.com is not resolvable in this workspace.\" >&2\n"
            "    else\n"
            "      curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup || true\n"
            "    fi\n"
            "    export PATH=\"$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH\"\n"
            "  fi\n"
            "fi\n"
            "if command -v hermes >/dev/null 2>&1; then\n"
            "  hermes config set model openrouter/free || echo \"Hermes model config update failed; continuing startup.\" >&2\n"
            "elif command -v hermes-agent >/dev/null 2>&1; then\n"
            "  hermes-agent config set model openrouter/free || echo \"Hermes Agent model config update failed; continuing startup.\" >&2\n"
            "fi\n"
            "if [ \"$#\" -gt 0 ]; then\n"
            "  if command -v hermes >/dev/null 2>&1; then exec hermes \"$@\"; fi\n"
            "  if command -v hermes-agent >/dev/null 2>&1; then exec hermes-agent \"$@\"; fi\n"
            "fi\n"
            "if [ -n \"${DOG_WORKSPACE_AGENT_HERMES_GATEWAY_CMD:-}\" ]; then\n"
            "  exec bash -lc \"$DOG_WORKSPACE_AGENT_HERMES_GATEWAY_CMD\"\n"
            "fi\n"
            "if command -v hermes >/dev/null 2>&1; then\n"
            "  exec hermes gateway run\n"
            "fi\n"
            "if command -v hermes-agent >/dev/null 2>&1; then\n"
            "  exec hermes-agent gateway run\n"
            "fi\n"
            "echo \"Hermes runtime command not found after bootstrap attempt; install Hermes Agent or adjust PATH.\" >&2\n"
            "exec tail -f /dev/null\n"
        ),
    }


def _hermes_api_runtime_files(user: str) -> dict[str, str]:
    user_home = f"/home/{user}"
    hermes_test_env = (
        "# Test-environment Hermes settings for kennel-managed workspaces.\n"
        "GATEWAY_ALLOW_ALL_USERS=true\n"
        "OPENROUTER_API_KEY=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\n"
    )
    return {
        f"{user_home}/.hermes/config.yaml": (
            "# Hermes API runtime configuration for kennel-managed workspaces.\n"
            "runtime:\n"
            "  profile: kennel-api\n"
            "  workspace_path: /home/dev/workspace\n"
        ),
        f"{user_home}/.hermes.env": hermes_test_env,
        f"{user_home}/.hermes/.env": (
            "# Workspace-scoped Hermes API settings.\n"
            "# Keep real values in this file or inject them through workspace env vars.\n"
            "HERMES_API_KEY=\n"
            "API_SERVER_ENABLED=true\n"
            "API_SERVER_HOST=127.0.0.1\n"
            "API_SERVER_PORT=8642\n"
            "API_SERVER_KEY=\n"
            "API_SERVER_MODEL_NAME=hermes\n"
        ),
        f"{user_home}/.hermes/hermes-api-launcher": (
            "#!/usr/bin/env bash\n"
            "set -euo pipefail\n"
            "export PATH=\"$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH\"\n"
            "export DOG_WORKSPACE_AGENT_HERMES_API_HOST=\"${DOG_WORKSPACE_AGENT_HERMES_API_HOST:-127.0.0.1}\"\n"
            "export DOG_WORKSPACE_AGENT_HERMES_API_PORT=\"${DOG_WORKSPACE_AGENT_HERMES_API_PORT:-8642}\"\n"
            "if [ -f \"$HOME/.hermes.env\" ]; then\n"
            "  set -a\n"
            "  # shellcheck disable=SC1090\n"
            "  source \"$HOME/.hermes.env\"\n"
            "  set +a\n"
            "fi\n"
            "if [ -f \"$HOME/.hermes/.env\" ]; then\n"
            "  set -a\n"
            "  # shellcheck disable=SC1090\n"
            "  source \"$HOME/.hermes/.env\"\n"
            "  set +a\n"
            "fi\n"
            "if ! command -v hermes >/dev/null 2>&1 && ! command -v hermes-agent >/dev/null 2>&1; then\n"
            "  if [ \"${DOG_WORKSPACE_AGENT_HERMES_AUTO_INSTALL:-true}\" = \"true\" ] && command -v curl >/dev/null 2>&1; then\n"
            "    echo \"Hermes API runtime command not found; attempting installer bootstrap.\" >&2\n"
            "    if command -v getent >/dev/null 2>&1 && ! getent hosts raw.githubusercontent.com >/dev/null 2>&1; then\n"
            "      echo \"Hermes installer bootstrap skipped: raw.githubusercontent.com is not resolvable in this workspace.\" >&2\n"
            "    else\n"
            "      curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.sh | bash -s -- --skip-setup || true\n"
            "    fi\n"
            "    export PATH=\"$HOME/.local/bin:$HOME/.cargo/bin:/usr/local/bin:$PATH\"\n"
            "  fi\n"
            "fi\n"
            "if command -v hermes >/dev/null 2>&1; then\n"
            "  hermes config set model openrouter/free || echo \"Hermes model config update failed; continuing startup.\" >&2\n"
            "elif command -v hermes-agent >/dev/null 2>&1; then\n"
            "  hermes-agent config set model openrouter/free || echo \"Hermes Agent model config update failed; continuing startup.\" >&2\n"
            "fi\n"
            "if [ -n \"${DOG_WORKSPACE_AGENT_HERMES_CMD:-}\" ]; then\n"
            "  exec bash -lc \"$DOG_WORKSPACE_AGENT_HERMES_CMD\"\n"
            "fi\n"
            "if command -v hermes >/dev/null 2>&1; then\n"
            "  exec hermes gateway run\n"
            "fi\n"
            "if command -v hermes-agent >/dev/null 2>&1; then\n"
            "  exec hermes-agent gateway run\n"
            "fi\n"
            "echo \"Hermes API runtime command not found after bootstrap attempt; install Hermes Agent or adjust PATH.\" >&2\n"
            "exit 1\n"
        ),
    }


def _bootstrap_profile_runtime_files(req: InjectRequest) -> dict[str, str]:
    if req.bootstrap_profile == "codex_app_server":
        return _codex_runtime_files(req.user)
    if req.bootstrap_profile == "claude_code_remote_control":
        return _claude_code_runtime_files(req.user)
    if req.bootstrap_profile == "hermes_agent_runtime":
        return _hermes_runtime_files(req.user)
    if req.bootstrap_profile == "hermes_api_server":
        return _hermes_api_runtime_files(req.user)
    if req.bootstrap_profile:
        raise ValueError(f"Unknown bootstrap_profile: {req.bootstrap_profile}")
    return {}


def _node_runtime_shell_preamble() -> str:
    """
    Load nvm-managed Node before starting npm-installed runtime CLIs.

    Built-in runtime profiles should not rely on non-interactive shell startup
    behavior to place user-level Node installations on PATH.
    """

    return (
        'export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"; '
        'if [ -s "$NVM_DIR/nvm.sh" ]; then '
        '. "$NVM_DIR/nvm.sh" >/dev/null 2>&1; '
        'nvm use default >/dev/null 2>&1 || true; '
        'fi; '
    )


def _bootstrap_profile_plan(req: InjectRequest) -> BootstrapExecutionPlan | None:
    if not req.bootstrap_profile:
        return None

    if req.bootstrap_profile == "claude_code_remote_control":
        plan = _legacy_bootstrap_plan(req)
        workspace_path = plan.workspace_path

        if not any(
            isinstance(step, BootstrapCloneRepoStep) and step.target_path == workspace_path
            for step in plan.steps
        ):
            plan.steps.append(
                BootstrapRunCommandStep(
                    phase="preparing_workspace",
                    label="Create workspace directory",
                    command=f"mkdir -p {shlex.quote(workspace_path)}",
                )
            )

        plan.steps.append(
            BootstrapRunCommandStep(
                phase="starting_runtime",
                label="Start Claude Code remote control",
                command=(
                    f"{_node_runtime_shell_preamble()}"
                    "claude remote-control "
                    "--name kennel "
                    "--permission-mode bypassPermissions "
                    "--spawn same-dir"
                ),
                cwd=workspace_path,
                background=True,
                service_name="claude_code",
            )
        )

        return plan

    if req.bootstrap_profile == "hermes_agent_runtime":
        plan = _legacy_bootstrap_plan(req)
        workspace_path = plan.workspace_path

        if not any(
            isinstance(step, BootstrapCloneRepoStep) and step.target_path == workspace_path
            for step in plan.steps
        ):
            plan.steps.append(
                BootstrapRunCommandStep(
                    phase="preparing_workspace",
                    label="Create workspace directory",
                    command=f"mkdir -p {shlex.quote(workspace_path)}",
                )
            )

        plan.steps.append(
            BootstrapRunCommandStep(
                phase="starting_runtime",
                label="Start Hermes agent runtime",
                command=(
                    "if [ -f \"$HOME/.hermes/hermes-agent-launcher\" ] && [ -x \"$HOME/.hermes/hermes-agent-launcher\" ]; then "
                    "exec \"$HOME/.hermes/hermes-agent-launcher\"; "
                    "elif [ -f \"$HOME/.hermes/hermes-agent\" ] && [ -x \"$HOME/.hermes/hermes-agent\" ]; then "
                    "exec \"$HOME/.hermes/hermes-agent\"; "
                    "elif command -v hermes >/dev/null 2>&1; then "
                    "exec hermes gateway run; "
                    "elif command -v hermes-agent >/dev/null 2>&1; then "
                    "exec hermes-agent gateway run; "
                    "fi; "
                    "echo 'Hermes runtime command not found; keeping service alive for operator inspection.'; "
                    "exec tail -f /dev/null"
                ),
                cwd=workspace_path,
                background=True,
                service_name="hermes",
            )
        )

        return plan

    if req.bootstrap_profile == "hermes_api_server":
        plan = _legacy_bootstrap_plan(req)
        workspace_path = plan.workspace_path

        if not any(
            isinstance(step, BootstrapCloneRepoStep) and step.target_path == workspace_path
            for step in plan.steps
        ):
            plan.steps.append(
                BootstrapRunCommandStep(
                    phase="preparing_workspace",
                    label="Create workspace directory",
                    command=f"mkdir -p {shlex.quote(workspace_path)}",
                )
            )

        plan.steps.append(
            BootstrapRunCommandStep(
                phase="starting_runtime",
                label="Start Hermes API server",
                command=(
                    "if [ -f \"$HOME/.hermes/hermes-api-launcher\" ] && [ -x \"$HOME/.hermes/hermes-api-launcher\" ]; then "
                    "exec \"$HOME/.hermes/hermes-api-launcher\"; "
                    "elif command -v hermes >/dev/null 2>&1; then "
                    "exec hermes gateway run; "
                    "elif command -v hermes-agent >/dev/null 2>&1; then "
                    "exec hermes-agent gateway run; "
                    "fi; "
                    "echo 'Hermes API runtime command not found.' >&2; "
                    "exit 1"
                ),
                cwd=workspace_path,
                background=True,
                service_name="hermes_api",
            )
        )

        return plan

    if req.bootstrap_profile != "codex_app_server":
        raise ValueError(f"Unknown bootstrap_profile: {req.bootstrap_profile}")

    plan = _legacy_bootstrap_plan(req)
    workspace_path = plan.workspace_path

    if not any(
        isinstance(step, BootstrapCloneRepoStep) and step.target_path == workspace_path
        for step in plan.steps
    ):
        plan.steps.append(
            BootstrapRunCommandStep(
                phase="preparing_workspace",
                label="Create workspace directory",
                command=f"mkdir -p {shlex.quote(workspace_path)}",
            )
        )

    plan.steps.append(
        BootstrapRunCommandStep(
            phase="starting_runtime",
            label="Start Codex app server",
            command=(
                f"{_node_runtime_shell_preamble()}"
                "codex app-server --listen ws://0.0.0.0:4500"
            ),
            cwd=workspace_path,
            background=True,
            service_name="codex",
        )
    )

    return plan


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
    mode = "644"
    if path.endswith("/.env"):
        mode = "600"
    elif content.lstrip().startswith("#!"):
        mode = "755"
    return _attach_exec(
        env_name,
        (
            f"mkdir -p {parent_dir} && "
            f"if [ -d {escaped_path} ]; then rm -rf {escaped_path}; fi && "
            f"cat > {escaped_path} <<'RUNTIMEFILE'\n{payload}\nRUNTIMEFILE\n"
            f"chown -R {user}:{user} {parent_dir} && "
            f"chmod {mode} {escaped_path}"
        ),
        timeout=30,
    )


def _ensure_workspace_user(
    env_name: str,
    *,
    user: str,
) -> subprocess.CompletedProcess:
    quoted_user = shlex.quote(user)
    quoted_home = shlex.quote(f"/home/{user}")
    return _attach_exec(
        env_name,
        f"""
        set -e
        if ! getent group {quoted_user} >/dev/null 2>&1; then
          groupadd {quoted_user}
        fi
        if ! id -u {quoted_user} >/dev/null 2>&1; then
          useradd -m -g {quoted_user} -G sudo -s /bin/bash {quoted_user}
        fi
        mkdir -p {quoted_home}
        chown {quoted_user}:{quoted_user} {quoted_home}
        usermod -d {quoted_home} -s /bin/bash -a -G sudo {quoted_user}
        echo {quoted_user}' ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/{quoted_user}
        chmod 0440 /etc/sudoers.d/{quoted_user}
        """,
        timeout=30,
    )


def _ensure_static_host_alias(
    env_name: str,
    *,
    hostname: str,
    address: str,
) -> subprocess.CompletedProcess:
    return _attach_exec(
        env_name,
        f"""
        set -e
        python3 - <<'PY'
from pathlib import Path

hosts_path = Path("/etc/hosts")
hostname = {hostname!r}
address = {address!r}
line = f"{{address}} {{hostname}}"

existing_lines = hosts_path.read_text(encoding="utf-8").splitlines()
filtered_lines = []
for existing_line in existing_lines:
    stripped = existing_line.strip()
    if not stripped or stripped.startswith("#"):
        filtered_lines.append(existing_line)
        continue
    parts = stripped.split()
    if hostname in parts[1:]:
        continue
    filtered_lines.append(existing_line)

filtered_lines.append(line)
hosts_path.write_text("\\n".join(filtered_lines) + "\\n", encoding="utf-8")
PY
        """,
        timeout=30,
    )


def _service_manifest_for_plan(plan: BootstrapExecutionPlan) -> list[DeclaredWorkspaceService]:
    services: list[DeclaredWorkspaceService] = []

    for step in plan.steps:
        if not isinstance(step, BootstrapRunCommandStep) or not step.background or not step.service_name:
            continue

        # The service manifest is the hand-off from bootstrap execution intent to
        # kennel discovery semantics. If a known runtime/service identifier is
        # used, kennel attaches the current metadata/readiness defaults from
        # `SERVICE_PROFILE_DEFAULTS`. Unknown identifiers stay valid, but are
        # treated as custom services with more conservative assumptions.
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


def _is_http_endpoint_ready(
    env_name: str,
    *,
    port: int,
    path: str = "/v1/models",
) -> bool:
    result = _attach_exec(
        env_name,
        (
            "python3 - <<'PY'\n"
            "import sys\n"
            "import urllib.error\n"
            "import urllib.request\n"
            f"url = 'http://127.0.0.1:{port}{path}'\n"
            "request = urllib.request.Request(url)\n"
            "try:\n"
            "    with urllib.request.urlopen(request, timeout=3) as response:\n"
            "        code = response.getcode() or 0\n"
            "        raise SystemExit(0 if code < 500 else 1)\n"
            "except urllib.error.HTTPError as exc:\n"
            "    raise SystemExit(0 if exc.code < 500 else 1)\n"
            "except Exception:\n"
            "    raise SystemExit(1)\n"
            "PY"
        ),
        timeout=10,
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
    http_ready = (
        _is_http_endpoint_ready(env_name, port=declared.port)
        if declared.runtime_profile == "hermes_api_server" and declared.port is not None
        else False
    )
    env_host = _get_env_ipv4(env_name)

    # Readiness is derived from kennel's current interpretation of the declared
    # service metadata. Different deployments may reasonably tighten or relax
    # these expectations later; the important thing in this slice is that the
    # runtime identifier -> metadata -> readiness path is explicit and reviewable.
    status: Literal["pending", "ready", "failed", "unknown"]
    readiness_message: str | None

    if declared.runtime_profile == "hermes_api_server" and declared.port is not None and http_ready:
        status = "ready"
        readiness_message = f"HTTP endpoint on port {declared.port} responded successfully."
    elif declared.runtime_profile == "hermes_api_server" and declared.port is not None and pid_running:
        status = "pending"
        readiness_message = (
            f"Hermes API process is running, but HTTP port {declared.port} is not responding successfully yet. "
            "Inspect /tmp/hermes_api.log for startup errors."
        )
    elif declared.port is not None and port_listening:
        status = "ready"
        readiness_message = f"Port {declared.port} is listening."
    elif pid_running and declared.port is None:
        status = "ready"
        readiness_message = "Runtime process is running."
    elif pid_running:
        status = "pending"
        if declared.runtime_id == "hermes" and declared.port == 4319:
            readiness_message = (
                "Hermes runtime process is running, but websocket port 4319 is not listening yet. "
                "Inspect /tmp/hermes.log for startup errors."
            )
        else:
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
        runtime_id=declared.runtime_id,
        runtime_profile=declared.runtime_profile,
        transport_kind=declared.transport_kind,
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


async def _invoke_agent_runtime_websocket(
    *,
    service: DiscoveredWorkspaceService,
    payload: dict | list | str,
    timeout_seconds: float,
) -> dict[str, object]:
    if not service.url:
        raise HTTPException(
            status_code=400,
            detail="Agent runtime does not have a routable URL.",
        )

    message = json.dumps(payload) if not isinstance(payload, str) else payload

    try:
        async with websockets.connect(
            service.url,
            open_timeout=timeout_seconds,
            close_timeout=timeout_seconds,
        ) as websocket:
            await websocket.send(message)
            response = await asyncio.wait_for(websocket.recv(), timeout=timeout_seconds)
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Agent runtime invocation timed out.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent runtime invocation failed: {exc}",
        ) from exc

    raw: object = response
    if isinstance(response, bytes):
        try:
            raw = response.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail="Agent runtime returned a non-UTF-8 websocket payload.",
            ) from exc

    parsed: object = raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw

    return {
        "status": "completed",
        "transport_kind": service.transport_kind,
        "protocol": service.protocol,
        "response": parsed,
    }


def _decode_json_rpc_message(raw: object) -> object:
    if isinstance(raw, bytes):
        try:
            raw = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail="Agent runtime returned a non-UTF-8 websocket payload.",
            ) from exc

    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=502,
                detail="Agent runtime returned a non-JSON JSON-RPC frame.",
            ) from exc

    return raw


async def _invoke_agent_runtime_json_rpc(
    *,
    service: DiscoveredWorkspaceService,
    session_request: JsonRpcInvokeSessionRequest,
    timeout_seconds: float,
) -> dict[str, object]:
    if not service.url:
        raise HTTPException(
            status_code=400,
            detail="Agent runtime does not have a routable URL.",
        )
    if len(session_request.requests) == 0:
        raise HTTPException(
            status_code=400,
            detail="Agent runtime JSON-RPC invocation requires at least one request.",
        )

    responses: list[object] = []
    notifications: list[object] = []
    terminal_notification: object | None = None

    async def recv_message(websocket) -> object:
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=timeout_seconds)
        except asyncio.TimeoutError as exc:
            raise HTTPException(
                status_code=504,
                detail="Agent runtime invocation timed out.",
            ) from exc
        return _decode_json_rpc_message(raw)

    try:
        async with websockets.connect(
            service.url,
            open_timeout=timeout_seconds,
            close_timeout=timeout_seconds,
        ) as websocket:
            for request in session_request.requests:
                await websocket.send(
                    json.dumps(
                        {
                            "id": request.id,
                            "method": request.method,
                            "params": request.params,
                        }
                    )
                )

                while True:
                    message = await recv_message(websocket)
                    if not isinstance(message, dict):
                        raise HTTPException(
                            status_code=502,
                            detail="Agent runtime returned an invalid JSON-RPC frame.",
                        )

                    if "id" in message and ("result" in message or "error" in message):
                        if message.get("id") == request.id:
                            if "error" in message:
                                raise HTTPException(
                                    status_code=502,
                                    detail=f"Agent runtime JSON-RPC error: {message['error']}",
                                )
                            responses.append(message)
                            break
                        responses.append(message)
                        continue

                    method = message.get("method")
                    if isinstance(method, str):
                        if "id" in message and session_request.fail_on_server_request:
                            raise HTTPException(
                                status_code=502,
                                detail=(
                                    "Agent runtime issued a JSON-RPC server request that "
                                    f"the kennel bridge is not handling: {method}"
                                ),
                            )
                        if (
                            method in session_request.tracked_notification_methods
                            or method in session_request.terminal_notification_methods
                        ):
                            notifications.append(message)
                        if method in session_request.terminal_notification_methods:
                            terminal_notification = message
                            return {
                                "status": "completed",
                                "transport_kind": service.transport_kind,
                                "protocol": service.protocol,
                                "response": {
                                    "responses": responses,
                                    "notifications": notifications,
                                    "terminal_notification": terminal_notification,
                                },
                            }

            if session_request.terminal_notification_methods:
                while True:
                    message = await recv_message(websocket)
                    if not isinstance(message, dict):
                        raise HTTPException(
                            status_code=502,
                            detail="Agent runtime returned an invalid JSON-RPC frame.",
                        )
                    method = message.get("method")
                    if isinstance(method, str):
                        if "id" in message and session_request.fail_on_server_request:
                            raise HTTPException(
                                status_code=502,
                                detail=(
                                    "Agent runtime issued a JSON-RPC server request that "
                                    f"the kennel bridge is not handling: {method}"
                                ),
                            )
                        if (
                            method in session_request.tracked_notification_methods
                            or method in session_request.terminal_notification_methods
                        ):
                            notifications.append(message)
                        if method in session_request.terminal_notification_methods:
                            terminal_notification = message
                            break
                    elif "id" in message and ("result" in message or "error" in message):
                        responses.append(message)
    except HTTPException:
        raise
    except asyncio.TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail="Agent runtime invocation timed out.",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Agent runtime invocation failed: {exc}",
        ) from exc

    return {
        "status": "completed",
        "transport_kind": service.transport_kind,
        "protocol": service.protocol,
        "response": {
            "responses": responses,
            "notifications": notifications,
            "terminal_notification": terminal_notification,
        },
    }


def _invoke_agent_runtime_command(
    *,
    env_name: str,
    service: DeclaredWorkspaceService,
    argv: list[str],
    cwd: str | None,
    user: str,
    timeout_seconds: float,
) -> dict[str, object]:
    if not argv:
        raise HTTPException(
            status_code=400,
            detail="Agent runtime command invocation requires argv.",
        )

    command = " ".join(shlex.quote(part) for part in argv)
    if cwd:
        command = f"cd {shlex.quote(cwd)} && {command}"

    result = _run_as_user(
        env_name,
        user=user,
        command=command,
        timeout=max(1, min(int(timeout_seconds), 300)),
    )
    if result.returncode != 0:
        error_output = (result.stderr or result.stdout or "").strip() or "Agent runtime command failed."
        raise HTTPException(
            status_code=502,
            detail=error_output,
        )

    output_text = (result.stdout or "").strip()
    return {
        "status": "completed",
        "transport_kind": "command",
        "protocol": service.protocol,
        "response": {
            "success": True,
            "output_text": output_text,
        },
    }


def _invoke_agent_runtime_http(
    *,
    env_name: str,
    service: DeclaredWorkspaceService,
    payload: dict | list | str,
    path: str,
    timeout_seconds: float,
) -> dict[str, object]:
    if service.port is None:
        raise HTTPException(
            status_code=400,
            detail="Agent runtime HTTP invocation requires a declared port.",
        )
    if service.protocol not in {"http", "https"}:
        raise HTTPException(
            status_code=400,
            detail=f"Agent runtime HTTP invocation requires HTTP(S), got {service.protocol}.",
        )

    safe_path = path if path.startswith("/") else f"/{path}"
    payload_json = json.dumps(payload)
    command = (
        "python3 - "
        f"{shlex.quote(service.protocol)} "
        f"{shlex.quote(str(service.port))} "
        f"{shlex.quote(safe_path)} "
        f"{shlex.quote(str(max(1, min(int(timeout_seconds), 300))))} "
        f"{shlex.quote(payload_json)} <<'PY'\n"
        "import json\n"
        "import sys\n"
        "import urllib.error\n"
        "import urllib.request\n"
        "protocol, port, path, timeout, payload = sys.argv[1:6]\n"
        "url = f'{protocol}://127.0.0.1:{port}{path}'\n"
        "request = urllib.request.Request(\n"
        "    url,\n"
        "    data=payload.encode('utf-8'),\n"
        "    headers={'Content-Type': 'application/json'},\n"
        "    method='POST',\n"
        ")\n"
        "try:\n"
        "    with urllib.request.urlopen(request, timeout=float(timeout)) as response:\n"
        "        body = response.read().decode('utf-8', errors='replace')\n"
        "        print(json.dumps({'status_code': response.getcode(), 'body': body}))\n"
        "except urllib.error.HTTPError as exc:\n"
        "    body = exc.read().decode('utf-8', errors='replace')\n"
        "    print(json.dumps({'status_code': exc.code, 'body': body}))\n"
        "    raise SystemExit(0)\n"
        "except Exception as exc:\n"
        "    print(json.dumps({'error': str(exc)}))\n"
        "    raise SystemExit(1)\n"
        "PY"
    )
    result = _attach_exec(
        env_name,
        command,
        timeout=max(1, min(int(timeout_seconds), 300)) + 5,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or "Agent runtime HTTP invocation failed."
        raise HTTPException(status_code=502, detail=detail)

    try:
        response_payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=502,
            detail="Agent runtime HTTP invocation returned an invalid response envelope.",
        ) from exc

    if response_payload.get("error"):
        raise HTTPException(status_code=502, detail=str(response_payload["error"]))

    status_code = response_payload.get("status_code")
    body = response_payload.get("body")
    if not isinstance(status_code, int) or not isinstance(body, str):
        raise HTTPException(
            status_code=502,
            detail="Agent runtime HTTP invocation returned an incomplete response envelope.",
        )
    if status_code >= 400:
        raise HTTPException(
            status_code=502,
            detail=f"Agent runtime HTTP invocation failed with status {status_code}: {body}",
        )

    try:
        parsed_body: object = json.loads(body) if body else {}
    except json.JSONDecodeError:
        parsed_body = body

    return {
        "status": "completed",
        "transport_kind": service.transport_kind or "http",
        "protocol": service.protocol,
        "response": parsed_body,
    }


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
        repo_url = shlex.quote(step.repo_url)
        target_path = shlex.quote(step.target_path)
        clone_command = (
            f"if [ -e {target_path} ]; then "
            f"echo 'Target path already exists: {step.target_path}' >&2; exit 1; "
            "fi && "
            "attempt=1; "
            "until git ls-remote "
            f"{repo_url} "
            "> /dev/null 2>&1; do "
            'if [ "$attempt" -ge 20 ]; then '
            f"echo 'Repository did not become reachable for clone: {step.repo_url}' >&2; "
            "exit 1; "
            "fi; "
            'echo "Waiting for repository endpoint to become reachable '
            f'($attempt/20): {step.repo_url}" >&2; '
            "attempt=$((attempt + 1)); "
            "sleep 1; "
            "done && "
            f"git clone {repo_url} {target_path}"
        )
        if step.ref:
            clone_command += (
                f" && cd {target_path} "
                f"&& git checkout {shlex.quote(step.ref)}"
            )
        r = _run_as_user(env_name, user=user, command=clone_command, timeout=240)
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
        if step.background:
            service_name = step.service_name or "workspace-service"
            log_path = f"/tmp/{service_name}.log"
            pid_path = f"/tmp/{service_name}.pid"
            command = _background_launch_command(
                cwd=step.cwd,
                command=step.command,
                log_path=log_path,
                pid_path=pid_path,
            )
        else:
            cwd_prefix = f"cd {shlex.quote(step.cwd)} && " if step.cwd else ""
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


def _inject_workspace_sync(
    name: str,
    req: InjectRequest,
    *,
    profile_runtime_files: dict[str, str],
    plan: BootstrapExecutionPlan,
    service_manifest: list[DeclaredWorkspaceService],
) -> dict[str, object]:
    errors: list[str] = []
    step_results: list[dict] = []
    started_services: list[str] = []
    fatal_error: str | None = None
    runtime_files = {**profile_runtime_files, **req.runtime_files}

    ensure_user_result = _ensure_workspace_user(name, user=req.user)
    if ensure_user_result.returncode != 0:
        raise RuntimeError(
            f"Failed to ensure workspace user '{req.user}': {ensure_user_result.stderr.strip()}"
        )

    host_alias_result = _ensure_static_host_alias(
        name,
        hostname=settings.kennel_gittin_guest_host,
        address=settings.kennel_gittin_guest_ip,
    )
    if host_alias_result.returncode != 0:
        raise RuntimeError(
            "Failed to configure guest host alias "
            f"'{settings.kennel_gittin_guest_host}': {host_alias_result.stderr.strip()}"
        )

    if req.git_name or req.git_email:
        git_cmds = []
        if req.git_name:
            git_cmds.append(f"git config --global user.name '{req.git_name}'")
        if req.git_email:
            git_cmds.append(f"git config --global user.email '{req.git_email}'")
        r = _attach_exec(name, f"su - {req.user} -c \"{' && '.join(git_cmds)}\"")
        if r.returncode != 0:
            errors.append(f"git_config: {r.stderr.strip()}")

    for path, content in runtime_files.items():
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

    manifest_result = _write_service_manifest(name, manifest=service_manifest)
    if manifest_result.returncode != 0:
        errors.append(f"service_manifest: {manifest_result.stderr.strip()}")

    return {
        "errors": errors,
        "step_results": step_results,
        "started_services": started_services,
        "fatal_error": fatal_error,
        "workspace_path": plan.workspace_path,
        "declared_services": [service.model_dump(mode="json") for service in service_manifest],
    }


# ── Background create worker ──────────────────────────────────────────────────

def _resolve_base_container(req: CreateEnvRequest) -> str | None:
    if req.base_container:
        return req.base_container
    if req.base_snapshot:
        return req.base_snapshot
    if req.flavour in FLAVOURS:
        return f"base-{req.flavour}"
    return None


def _apply_runtime_preset_to_create_request(req: CreateEnvRequest) -> None:
    if not req.runtime_preset:
        return

    defaults = RUNTIME_PRESET_DEFAULTS[req.runtime_preset]
    # Create-time precedence stays additive:
    # 1. explicit base_container / base_snapshot
    # 2. explicit non-default flavour
    # 3. runtime_preset default flavour
    # 4. kennel default flavour
    #
    # So runtime_preset only rewrites flavour while the request is still on the
    # default generic flavour path.
    if not req.base_container and not req.base_snapshot and req.flavour == "dev":
        req.flavour = defaults["flavour"]


def _apply_runtime_preset_to_inject_request(req: InjectRequest) -> None:
    if not req.runtime_preset:
        return

    defaults = RUNTIME_PRESET_DEFAULTS[req.runtime_preset]
    # Inject-time precedence is:
    # 1. explicit bootstrap_plan
    # 2. explicit bootstrap_profile
    # 3. runtime_preset default bootstrap_profile
    # 4. legacy inject derivation
    #
    # This helper only fills bootstrap_profile when the caller has not already
    # supplied a more explicit profile override.
    if req.bootstrap_profile is None:
        req.bootstrap_profile = defaults["bootstrap_profile"] or None

    preset_env_vars = _runtime_preset_env_vars(req.runtime_preset)
    if preset_env_vars:
        req.env_vars = {**preset_env_vars, **req.env_vars}


def _runtime_preset_env_vars(runtime_preset: RuntimePreset) -> dict[str, str]:
    if runtime_preset not in RUNTIME_PRESETS_WITH_TYPER_ENV:
        return {}

    api_root = settings.kennel_tinyfoot_api_url.rstrip("/")
    return {
        "TINYFOOT_API_URL": api_root,
    }

def _create_env_worker(job_id: str, name: str, req: CreateEnvRequest):
    jobs[job_id]["status"] = JobStatus.running
    try:
        base_container = _resolve_base_container(req)
        if base_container:
            r = subprocess.run(
                ["lxc-copy", "-n", base_container,
                 "-N", name, "-s", "-B", "overlay"],
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

        start_result = _start_env_container(name, kind=req.kind)
        if start_result.returncode != 0:
            jobs[job_id].update(
                {
                    "status": JobStatus.failed,
                    "error": (start_result.stderr or start_result.stdout or "").strip(),
                }
            )
            return

        ready, ready_error = _wait_for_attach_ready(name)
        if not ready:
            jobs[job_id].update(
                {
                    "status": JobStatus.failed,
                    "error": ready_error or "Container did not become attachable after start.",
                }
            )
            return

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
    """List all flavours and their current base-container readiness."""
    result = {}
    for name, defn in FLAVOURS.items():
        base = f"base-{name}"
        latest_job = rebuild_store.latest_for(name)
        result[name] = {
            "description":   defn.description,
            "parent":        defn.parent,
            "scripts":       defn.scripts,
            "base_container": base,
            "base_ready":    _container_exists(base),
            "latest_job":    latest_job.job_id if latest_job else None,
            "latest_status": latest_job.status if latest_job else None,
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

    _apply_runtime_preset_to_create_request(req)
    base_container = _resolve_base_container(req)
    if base_container is None and req.flavour in FLAVOURS:
        base_container = f"base-{req.flavour}"

    if base_container is not None:
        req.base_container = base_container
        if not _container_exists(base_container):
            raise HTTPException(
                400,
                detail=(
                    f"Base container not ready: {base_container}. "
                    f"Rebuild flavour '{req.flavour}' first."
                ),
            )
    elif req.flavour not in FLAVOURS:
        raise HTTPException(400, detail=f"Unknown flavour: {req.flavour}")

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
    _apply_runtime_preset_to_inject_request(req)
    try:
        # Kennel resolves the final inject execution shape in precedence order:
        # explicit bootstrap_plan -> profile-derived plan -> legacy plan.
        # Runtime files also layer in order:
        # profile runtime files -> caller runtime_files.
        profile_runtime_files = _bootstrap_profile_runtime_files(req)
        plan = req.bootstrap_plan or _bootstrap_profile_plan(req) or _legacy_bootstrap_plan(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    service_manifest = _service_manifest_for_plan(plan)
    try:
        sync_result = await asyncio.to_thread(
            _inject_workspace_sync,
            name,
            req,
            profile_runtime_files=profile_runtime_files,
            plan=plan,
            service_manifest=service_manifest,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    ws_token = token_store.issue(name, ttl=req.token_ttl)
    errors = sync_result["errors"]
    step_results = sync_result["step_results"]
    started_services = sync_result["started_services"]
    fatal_error = sync_result["fatal_error"]

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
        "workspace_path":    sync_result["workspace_path"],
        "declared_services": sync_result["declared_services"],
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


@app.post("/envs/{name}/agent-runtimes/{service_id}/invoke")
async def invoke_agent_runtime(
    name: str,
    service_id: str,
    req: AgentRuntimeInvokeRequest,
    _=Depends(require_management_secret),
):
    info = lxc("lxc-info", "-n", name)
    if info.returncode != 0:
        raise HTTPException(404, detail=f"Environment not found: {name}")

    declared_services = _read_service_manifest(name)
    declared = next((service for service in declared_services if service.id == service_id), None)
    if declared is None:
        raise HTTPException(
            status_code=404,
            detail=f"Declared agent runtime not found: {service_id}",
        )
    if declared.kind != "agent_runtime":
        raise HTTPException(
            status_code=400,
            detail=f"Declared service '{service_id}' is not an agent runtime.",
        )

    discovered = _discover_service(name, declared)
    if discovered.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=discovered.readiness_message or "Agent runtime is not ready.",
        )

    if req.invoke_mode == "command":
        result = await asyncio.to_thread(
            _invoke_agent_runtime_command,
            env_name=name,
            service=declared,
            argv=req.argv,
            cwd=req.cwd or declared.workspace_path,
            user=req.user,
            timeout_seconds=req.timeout_seconds,
        )
    elif req.invoke_mode == "http":
        if discovered.transport_kind != "http":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Agent runtime transport is not supported by the kennel HTTP invoke endpoint: "
                    f"{discovered.transport_kind or discovered.protocol}"
                ),
            )
        if req.payload is None:
            raise HTTPException(
                status_code=400,
                detail="Agent runtime HTTP invocation requires payload.",
            )
        result = await asyncio.to_thread(
            _invoke_agent_runtime_http,
            env_name=name,
            service=declared,
            payload=req.payload,
            path=req.http_path,
            timeout_seconds=req.timeout_seconds,
        )
    elif req.invoke_mode == "json_rpc":
        if discovered.transport_kind != "websocket":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Agent runtime transport is not supported by the kennel JSON-RPC invoke endpoint yet: "
                    f"{discovered.transport_kind or discovered.protocol}"
                ),
            )
        if req.json_rpc_session is None:
            raise HTTPException(
                status_code=400,
                detail="Agent runtime JSON-RPC invocation requires json_rpc_session.",
            )
        result = await _invoke_agent_runtime_json_rpc(
            service=discovered,
            session_request=req.json_rpc_session,
            timeout_seconds=req.timeout_seconds,
        )
    else:
        if discovered.transport_kind != "websocket":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Agent runtime transport is not supported by the kennel invoke endpoint yet: "
                    f"{discovered.transport_kind or discovered.protocol}"
                ),
            )
        if req.payload is None:
            raise HTTPException(
                status_code=400,
                detail="Agent runtime websocket invocation requires payload.",
            )
        result = await _invoke_agent_runtime_websocket(
            service=discovered,
            payload=req.payload,
            timeout_seconds=req.timeout_seconds,
        )

    return {
        "env": name,
        "service_id": service_id,
        "runtime_id": discovered.runtime_id,
        "runtime_profile": discovered.runtime_profile,
        **result,
    }


# ── WebSocket: terminal ───────────────────────────────────────────────────────

@app.websocket("/envs/{name}/ws")
async def env_terminal(websocket: WebSocket, name: str):
    """
    Browser connects here with the token issued by /inject.
    Token is validated before the lxc-attach subprocess is spawned.
    """
    token = websocket.query_params.get("token", "")
    debug_session_id = websocket.query_params.get("debug_session_id")
    client_host = getattr(websocket.client, "host", None)
    origin = websocket.headers.get("origin")
    user_agent = websocket.headers.get("user-agent")

    logger.info(
        "terminal websocket attempt env=%s client=%s origin=%s user_agent=%s token_prefix=%s debug_session_id=%s",
        name,
        client_host,
        origin,
        user_agent,
        token[:8],
        debug_session_id,
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
    logger.info(
        "terminal websocket accepted env=%s client=%s debug_session_id=%s",
        name,
        client_host,
        debug_session_id,
    )
    loop = asyncio.get_running_loop()
    child_pid, pty_master_fd = await loop.run_in_executor(None, _spawn_terminal_pty, name)
    await loop.run_in_executor(None, _set_pty_winsize, pty_master_fd, 120, 32)

    async def read_output():
        first_output_logged = False
        try:
            while True:
                chunk = await loop.run_in_executor(None, os.read, pty_master_fd, 4096)
                if not chunk:
                    break
                if debug_session_id and not first_output_logged:
                    first_output_logged = True
                    logger.info(
                        "terminal websocket first output env=%s client=%s debug_session_id=%s bytes=%s",
                        name,
                        client_host,
                        debug_session_id,
                        len(chunk),
                    )
                await websocket.send_bytes(chunk)
        except OSError as exc:
            if exc.errno != errno.EIO:
                logger.exception("terminal websocket output pump failed env=%s", name)
        except Exception:
            logger.exception("terminal websocket output pump failed env=%s", name)
        finally:
            with suppress(Exception):
                await websocket.close()

    async def read_input():
        first_input_logged = False
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
                    control = _parse_terminal_control_message(text)
                    if control is not None:
                        if debug_session_id:
                            logger.info(
                                "terminal websocket resize control env=%s client=%s debug_session_id=%s cols=%s rows=%s",
                                name,
                                client_host,
                                debug_session_id,
                                control.cols,
                                control.rows,
                            )
                        await loop.run_in_executor(
                            None,
                            _set_pty_winsize,
                            pty_master_fd,
                            control.cols,
                            control.rows,
                        )
                        continue
                    data = text.encode()

                if debug_session_id and not first_input_logged:
                    first_input_logged = True
                    logger.info(
                        "terminal websocket first input env=%s client=%s debug_session_id=%s bytes=%s",
                        name,
                        client_host,
                        debug_session_id,
                        len(data),
                    )
                await loop.run_in_executor(None, os.write, pty_master_fd, data)
        except WebSocketDisconnect:
            logger.info(
                "terminal websocket client disconnected env=%s client=%s debug_session_id=%s",
                name,
                client_host,
                debug_session_id,
            )
        except Exception:
            logger.exception("terminal websocket input pump failed env=%s", name)

    await asyncio.gather(read_output(), read_input())
    with suppress(OSError):
        os.close(pty_master_fd)
    with suppress(ProcessLookupError):
        os.kill(child_pid, signal.SIGTERM)
    with suppress(ChildProcessError):
        await loop.run_in_executor(None, os.waitpid, child_pid, 0)
    logger.info(
        "terminal websocket closed env=%s client=%s debug_session_id=%s",
        name,
        client_host,
        debug_session_id,
    )
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
