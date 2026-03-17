# backend/app/services/kennel_client.py
import httpx
import secrets
from app.core.config import settings

KENNEL_BASE    = "http://kennel:8090"
KENNEL_HEADERS = {"x-kennel-secret": settings.KENNEL_SECRET}

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=KENNEL_BASE,
            headers=KENNEL_HEADERS,
            timeout=httpx.Timeout(10.0, read=120.0)  # long read for lxc ops
        )
    return _client


async def create_env(
    name: str,
    kind: str = "ephemeral",
    flavour: str = "dev",
) -> dict:
    r = await get_client().post("/envs", json={
        "name": name,
        "kind": kind,
        "flavour": flavour,
    })
    r.raise_for_status()
    return r.json()   # {job_id, name, kind, poll}


async def poll_job(job_id: str) -> dict:
    r = await get_client().get(f"/jobs/{job_id}")
    r.raise_for_status()
    return r.json()   # {status, env_name, error}


async def inject_workspace(
    kennel_name: str,
    config: dict,
) -> None:
    r = await get_client().post(
        f"/envs/{kennel_name}/inject",
        json=config,
    )
    r.raise_for_status()


async def destroy_env(kennel_name: str) -> None:
    r = await get_client().delete(f"/envs/{kennel_name}")
    r.raise_for_status()


async def stop_env(kennel_name: str) -> None:
    r = await get_client().post(
        f"/envs/{kennel_name}/action",
        json={"action": "stop"}
    )
    r.raise_for_status()


def make_ws_token() -> str:
    """One-time token scoped to a workspace session."""
    return secrets.token_urlsafe(32)


def terminal_url(kennel_name: str, token: str, external: bool = True) -> str:
    base = f"wss://kennel.{settings.DOMAIN}" if external else "ws://kennel:8090"
    return f"{base}/envs/{kennel_name}/ws?token={token}"