"""Backend-owned workspace bootstrap plan generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from app.models import (
    WorkspaceBootstrapIntent,
    WorkspaceBootstrapPhase,
    WorkspaceExternalUrlRepoSource,
    WorkspaceInstallIntentAuto,
    WorkspaceInstallIntentNone,
    WorkspaceInstallIntentProfile,
    WorkspaceStartupIntentAgentService,
    WorkspaceStartupIntentProfile,
    WorkspaceStartupIntentTerminalOnly,
    WorkspaceUserRepoSource,
)

DEFAULT_WORKSPACE_USER = "dev"
DEFAULT_WORKSPACE_PATH = f"/home/{DEFAULT_WORKSPACE_USER}/workspace"


class WorkspaceBootstrapValidationError(ValueError):
    """Raised when the submitted bootstrap intent is invalid for this slice."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        error_code: str = "WORKSPACE_BOOTSTRAP_INVALID",
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class BootstrapSshKeyStep(BaseModel):
    """Authorize an SSH key inside the workspace."""

    type: Literal["add_ssh_key"] = "add_ssh_key"
    phase: WorkspaceBootstrapPhase = WorkspaceBootstrapPhase.resolving_source
    label: str
    ssh_pubkey: str


class BootstrapEnvVarsStep(BaseModel):
    """Persist env vars into the workspace shell profile."""

    type: Literal["write_env_vars"] = "write_env_vars"
    phase: WorkspaceBootstrapPhase = WorkspaceBootstrapPhase.resolving_source
    label: str
    env_vars: dict[str, str] = Field(default_factory=dict)


class BootstrapCloneRepoStep(BaseModel):
    """Clone a repository into the workspace."""

    type: Literal["clone_repo"] = "clone_repo"
    phase: WorkspaceBootstrapPhase = WorkspaceBootstrapPhase.materializing_repo
    label: str
    repo_url: str
    target_path: str
    ref: str | None = None


class BootstrapRunCommandStep(BaseModel):
    """Run a named shell command inside the workspace."""

    type: Literal["run_command"] = "run_command"
    phase: WorkspaceBootstrapPhase
    label: str
    command: str
    cwd: str | None = None
    background: bool = False
    service_name: str | None = None


WorkspaceBootstrapPlanStep = (
    BootstrapSshKeyStep
    | BootstrapEnvVarsStep
    | BootstrapCloneRepoStep
    | BootstrapRunCommandStep
)


class WorkspaceBootstrapPlan(BaseModel):
    """Normalized kennel execution plan derived from typed bootstrap intent."""

    workspace_path: str = DEFAULT_WORKSPACE_PATH
    steps: list[WorkspaceBootstrapPlanStep] = Field(default_factory=list)


INSTALL_PROFILE_COMMANDS: dict[str, str] = {
    "npm": "npm install",
    "pnpm": "pnpm install",
    "yarn": "yarn install",
    "uv": "uv sync",
    "pip": "pip install -r requirements.txt",
}

STARTUP_PROFILE_COMMANDS: dict[str, tuple[str, str]] = {
    "vite": ("npm run dev -- --host 0.0.0.0", "vite"),
    "nextjs": ("npm run dev -- --hostname 0.0.0.0", "nextjs"),
    "fastapi": ("uvicorn main:app --host 0.0.0.0 --port 8000", "fastapi"),
}


@dataclass(frozen=True)
class AgentServiceProfile:
    """Backend-owned runtime profile for agent-oriented startup."""

    profile_id: str
    label: str
    default_command: str
    command_env_var: str
    host_env_var: str
    port_env_var: str
    default_port: int
    service_name: str


AGENT_SERVICE_PROFILES: dict[str, AgentServiceProfile] = {
    "codex": AgentServiceProfile(
        profile_id="codex",
        label="Codex Runtime",
        default_command="codex",
        command_env_var="DOG_WORKSPACE_AGENT_CODEX_CMD",
        host_env_var="DOG_WORKSPACE_AGENT_CODEX_HOST",
        port_env_var="DOG_WORKSPACE_AGENT_CODEX_PORT",
        default_port=4317,
        service_name="codex",
    ),
    "claude_code": AgentServiceProfile(
        profile_id="claude_code",
        label="Claude Code Runtime",
        default_command="claude",
        command_env_var="DOG_WORKSPACE_AGENT_CLAUDE_CODE_CMD",
        host_env_var="DOG_WORKSPACE_AGENT_CLAUDE_CODE_HOST",
        port_env_var="DOG_WORKSPACE_AGENT_CLAUDE_CODE_PORT",
        default_port=4318,
        service_name="claude_code",
    ),
    "hermes": AgentServiceProfile(
        profile_id="hermes",
        label="Hermes Runtime",
        default_command="hermes",
        command_env_var="DOG_WORKSPACE_AGENT_HERMES_CMD",
        host_env_var="DOG_WORKSPACE_AGENT_HERMES_HOST",
        port_env_var="DOG_WORKSPACE_AGENT_HERMES_PORT",
        default_port=4319,
        service_name="hermes",
    ),
}


def _agent_service_start_command(profile: AgentServiceProfile) -> str:
    """
    Build the shell launcher for an agent runtime profile.

    The default command stays intentionally compact in this slice. Operators can
    override the launcher per profile with an env var while the concrete runtime
    semantics are still evolving.
    """

    return (
        f'export DOG_WORKSPACE_AGENT_PROFILE="{profile.profile_id}"; '
        f'export DOG_WORKSPACE_AGENT_HOST="${{{profile.host_env_var}:-0.0.0.0}}"; '
        f'export DOG_WORKSPACE_AGENT_PORT="${{{profile.port_env_var}:-{profile.default_port}}}"; '
        f'AGENT_CMD="${{{profile.command_env_var}:-{profile.default_command}}}"; '
        f'echo "Starting {profile.label} using: $AGENT_CMD"; '
        'exec bash -lc "$AGENT_CMD"'
    )


def generate_bootstrap_plan(
    intent: WorkspaceBootstrapIntent,
    *,
    materialized_repo_url: str | None,
    workspace_user: str = DEFAULT_WORKSPACE_USER,
) -> WorkspaceBootstrapPlan:
    """
    Convert user-declared bootstrap intent into a backend-owned execution plan.

    The plan stays intentionally small and linear in this slice:
    - it is expressive enough for current repo/install/start needs
    - it remains readable and easy to extend as future bootstrap modes land
    """

    workspace_path = intent.workspace_path or f"/home/{workspace_user}/workspace"
    steps: list[WorkspaceBootstrapPlanStep] = []

    if intent.ssh_pubkey:
        steps.append(
            BootstrapSshKeyStep(
                label="Authorize SSH key",
                ssh_pubkey=intent.ssh_pubkey,
            )
        )

    if intent.env_vars:
        steps.append(
            BootstrapEnvVarsStep(
                label="Write workspace environment",
                env_vars=intent.env_vars,
            )
        )

    repo_source = intent.repo_source
    repo_ref = None
    if isinstance(repo_source, WorkspaceExternalUrlRepoSource | WorkspaceUserRepoSource):
        repo_ref = repo_source.ref
    if materialized_repo_url:
        steps.append(
            BootstrapCloneRepoStep(
                label="Clone repository",
                repo_url=materialized_repo_url,
                target_path=workspace_path,
                ref=repo_ref,
            )
        )

    install_intent = intent.install_intent or WorkspaceInstallIntentNone()
    if isinstance(install_intent, WorkspaceInstallIntentAuto):
        steps.append(
            BootstrapRunCommandStep(
                phase=WorkspaceBootstrapPhase.installing_dependencies,
                label="Install dependencies automatically",
                cwd=workspace_path,
                command=(
                    "if [ -f pnpm-lock.yaml ]; then pnpm install; "
                    "elif [ -f package-lock.json ]; then npm install; "
                    "elif [ -f yarn.lock ]; then yarn install; "
                    "elif [ -f uv.lock ]; then uv sync; "
                    "elif [ -f requirements.txt ]; then pip install -r requirements.txt; "
                    "elif [ -f pyproject.toml ] && command -v uv >/dev/null 2>&1; then uv sync; "
                    "elif [ -f pyproject.toml ]; then pip install -e .; "
                    "else echo 'No supported install manifest found; skipping install'; fi"
                ),
            )
        )
    elif isinstance(install_intent, WorkspaceInstallIntentProfile):
        command = INSTALL_PROFILE_COMMANDS.get(install_intent.profile)
        if command is None:
            raise WorkspaceBootstrapValidationError(
                f"Unsupported install profile: {install_intent.profile}",
                error_code="WORKSPACE_INSTALL_PROFILE_UNSUPPORTED",
            )
        steps.append(
            BootstrapRunCommandStep(
                phase=WorkspaceBootstrapPhase.installing_dependencies,
                label=f"Install dependencies with profile '{install_intent.profile}'",
                cwd=workspace_path,
                command=command,
            )
        )

    startup_intent = intent.startup_intent or WorkspaceStartupIntentTerminalOnly()
    if isinstance(startup_intent, WorkspaceStartupIntentProfile):
        startup_profile = STARTUP_PROFILE_COMMANDS.get(startup_intent.profile)
        if startup_profile is None:
            raise WorkspaceBootstrapValidationError(
                f"Unsupported startup profile: {startup_intent.profile}",
                error_code="WORKSPACE_STARTUP_PROFILE_UNSUPPORTED",
            )
        command, service_name = startup_profile
        steps.append(
            BootstrapRunCommandStep(
                phase=WorkspaceBootstrapPhase.starting_services,
                label=f"Start service profile '{startup_intent.profile}'",
                cwd=workspace_path,
                command=command,
                background=True,
                service_name=service_name,
            )
        )
    elif isinstance(startup_intent, WorkspaceStartupIntentAgentService):
        agent_profile = AGENT_SERVICE_PROFILES.get(startup_intent.agent_profile)
        if agent_profile is None:
            raise WorkspaceBootstrapValidationError(
                f"Unsupported agent-service profile: {startup_intent.agent_profile}",
                error_code="WORKSPACE_AGENT_PROFILE_UNSUPPORTED",
            )
        steps.append(
            BootstrapRunCommandStep(
                phase=WorkspaceBootstrapPhase.starting_services,
                label=f"Start {agent_profile.label}",
                cwd=workspace_path,
                command=_agent_service_start_command(agent_profile),
                background=True,
                service_name=agent_profile.service_name,
            )
        )

    return WorkspaceBootstrapPlan(workspace_path=workspace_path, steps=steps)
