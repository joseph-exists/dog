import httpx
from app.core.config import settings  # your existing settings

KENNEL_BASE = "http://kennel:8090"
KENNEL_HEADERS = {"x-kennel-secret": settings.KENNEL_SECRET}


async def create_env(
    name: str | None = None,
    kind: str = "ephemeral",
    base_snapshot: str | None = None,
) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{KENNEL_BASE}/envs",
            json={"name": name, "kind": kind, "base_snapshot": base_snapshot},
            headers=KENNEL_HEADERS,
            timeout=120,  # lxc-create can be slow first time
        )
        r.raise_for_status()
        return r.json()


async def destroy_env(name: str) -> dict:
    async with httpx.AsyncClient() as client:
        r = await client.delete(
            f"{KENNEL_BASE}/envs/{name}",
            headers=KENNEL_HEADERS,
        )
        r.raise_for_status()
        return r.json()


async def list_envs() -> list:
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{KENNEL_BASE}/envs", headers=KENNEL_HEADERS)
        r.raise_for_status()
        return r.json()["envs"]


def ws_terminal_url(env_name: str, external: bool = False) -> str:
    """
    Returns the WebSocket URL for terminal access.
    external=True: URL for browser clients (goes through Traefik)
    external=False: internal URL (for server-side proxying)
    """
    base = f"wss://kennel.{settings.DOMAIN}" if external else "ws://kennel:8090"
    return f"{base}/envs/{env_name}/ws?token={settings.KENNEL_SECRET}"

# ## Architecture Flow
# ```
# Browser
#   │
#   │ wss://kennel.domain/envs/env-abc123/ws?token=...
#   ▼
# Traefik (terminates TLS, passes WebSocket through)
#   │
#   ▼
# kennel:8090  ──lxc-attach──►  LXC container env-abc123
#                                (bash session, full pty)

# Backend API
#   │  POST http://kennel:8090/envs  (internal network, no Traefik)
#   ▼
# kennel:8090  ──lxc-create──►  new LXC container
#               ──pub/sub──►    redis kennel:events  ──►  backend listeners