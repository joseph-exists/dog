import httpx

from app.core.config import settings
from app.services.workspace_bootstrap_service import WorkspaceBootstrapPlan

KENNEL_HEADERS = {"x-kennel-secret": settings.KENNEL_SECRET}

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.KENNEL_BASE_URL.rstrip("/"),
            headers=KENNEL_HEADERS,
            timeout=httpx.Timeout(10.0, read=120.0),
        )
    return _client


async def create_env(
    name: str,
    kind: str = "ephemeral",
    flavour: str = "dev",
    runtime_preset: str | None = None,
    base_container: str | None = None,
    base_snapshot: str | None = None,
) -> dict:
    payload = {"name": name, "kind": kind, "flavour": flavour}
    if runtime_preset is not None:
        payload["runtime_preset"] = runtime_preset
    if base_container is not None:
        payload["base_container"] = base_container
    if base_snapshot is not None:
        payload["base_snapshot"] = base_snapshot
    response = await get_client().post(
        "/envs",
        json=payload,
    )
    response.raise_for_status()
    return response.json()


async def poll_job(job_id: str) -> dict:
    response = await get_client().get(f"/jobs/{job_id}")
    response.raise_for_status()
    return response.json()


async def inject_workspace(
    kennel_name: str,
    *,
    user: str = "dev",
    ssh_pubkey: str | None = None,
    repo_url: str | None = None,
    env_vars: dict[str, str] | None = None,
    git_name: str | None = None,
    git_email: str | None = None,
    token_ttl: int | None = None,
    runtime_preset: str | None = None,
    bootstrap_profile: str | None = None,
    bootstrap_plan: WorkspaceBootstrapPlan | dict | None = None,
    runtime_files: dict[str, str] | None = None,
) -> dict:
    payload: dict[str, object] = {
        "user": user,
        "env_vars": dict(env_vars or {}),
    }
    if ssh_pubkey is not None:
        payload["ssh_pubkey"] = ssh_pubkey
    if repo_url is not None:
        payload["repo_url"] = repo_url
    if git_name is not None:
        payload["git_name"] = git_name
    if git_email is not None:
        payload["git_email"] = git_email
    if token_ttl is not None:
        payload["token_ttl"] = token_ttl
    if runtime_preset is not None:
        payload["runtime_preset"] = runtime_preset
    if bootstrap_profile is not None:
        payload["bootstrap_profile"] = bootstrap_profile
    if bootstrap_plan is not None:
        payload["bootstrap_plan"] = (
            bootstrap_plan.model_dump(mode="json")
            if isinstance(bootstrap_plan, WorkspaceBootstrapPlan)
            else bootstrap_plan
        )
    if runtime_files:
        payload["runtime_files"] = dict(runtime_files)

    response = await get_client().post(f"/envs/{kennel_name}/inject", json=payload)
    response.raise_for_status()
    return response.json()


async def issue_terminal_token(kennel_name: str, ttl: int = 3600) -> dict:
    response = await get_client().post(
        f"/envs/{kennel_name}/terminal-token",
        json={"token_ttl": ttl},
    )
    response.raise_for_status()
    return response.json()


async def get_env_services(kennel_name: str) -> dict:
    response = await get_client().get(f"/envs/{kennel_name}/services")
    response.raise_for_status()
    return response.json()


async def list_flavours() -> dict:
    response = await get_client().get("/flavours")
    response.raise_for_status()
    return response.json()


async def destroy_env(kennel_name: str) -> dict:
    response = await get_client().delete(f"/envs/{kennel_name}")
    response.raise_for_status()
    return response.json()


async def stop_env(kennel_name: str) -> dict:
    response = await get_client().post(
        f"/envs/{kennel_name}/action",
        json={"action": "stop"},
    )
    response.raise_for_status()
    return response.json()


def terminal_url(kennel_name: str, token: str, external: bool = True) -> str:
    if external:
        base = settings.KENNEL_EXTERNAL_WS_BASE_URL
    else:
        base = settings.KENNEL_WS_BASE_URL
    return f"{base.rstrip('/')}/envs/{kennel_name}/ws?token={token}"
