import httpx

from app.core.config import settings

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
) -> dict:
    response = await get_client().post(
        "/envs",
        json={"name": name, "kind": kind, "flavour": flavour},
    )
    response.raise_for_status()
    return response.json()


async def poll_job(job_id: str) -> dict:
    response = await get_client().get(f"/jobs/{job_id}")
    response.raise_for_status()
    return response.json()


async def inject_workspace(kennel_name: str, config: dict) -> dict:
    response = await get_client().post(f"/envs/{kennel_name}/inject", json=config)
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
