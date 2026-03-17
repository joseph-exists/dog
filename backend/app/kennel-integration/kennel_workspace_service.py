# backend/app/services/workspace_service.py
import asyncio
import uuid
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.models.workspace import (
    Workspace, WorkspaceCreate, WorkspaceStatus
)
from app.services import kennel_client
from app.core.config import settings
import redis.asyncio as aioredis
import logging

log = logging.getLogger(__name__)


# ── Step 3: Spawn ─────────────────────────────────────────────────────────────

async def spawn_workspace(
    db: AsyncSession,
    owner_id: uuid.UUID,
    req: WorkspaceCreate,
) -> Workspace:
    """
    Creates the DB record and kicks off async provisioning.
    Returns immediately — status will be 'provisioning'.
    """
    kennel_name = f"env-{uuid.uuid4().hex[:8]}"

    ws = Workspace(
        name        = req.name,
        flavour     = req.flavour,
        kind        = req.kind,
        owner_id    = owner_id,
        kennel_name = kennel_name,
        status      = WorkspaceStatus.provisioning,
        meta        = {
            "repo_url":   req.repo_url,
            "ssh_pubkey": req.ssh_pubkey,
            "env_vars":   req.env_vars,
        }
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)

    # Kick off provisioning in background — don't await
    asyncio.create_task(
        _provision(ws_id=ws.id, kennel_name=kennel_name, req=req)
    )

    return ws


# ── Step 4: Provision (background task) ───────────────────────────────────────

async def _provision(
    ws_id: uuid.UUID,
    kennel_name: str,
    req: WorkspaceCreate,
) -> None:
    """
    Drives the full lifecycle:
      kennel create → poll until done → inject workspace → mark ready
    """
    from app.db import get_session_context  # avoids circular import

    try:
        # 1. Request container creation
        job = await kennel_client.create_env(
            name    = kennel_name,
            kind    = req.kind,
            flavour = req.flavour.value,
        )
        job_id = job["job_id"]

        log.info(f"[workspace:{ws_id}] kennel job {job_id} started")

        # 2. Poll until done (max 10 min)
        result = await _poll_until_done(job_id, timeout=600)

        if result["status"] == "failed":
            await _set_status(ws_id, WorkspaceStatus.destroyed,
                              error=result.get("error"))
            return

        log.info(f"[workspace:{ws_id}] container up, injecting workspace")

        # 3. Inject user-specific config
        await kennel_client.inject_workspace(kennel_name, {
            "ssh_pubkey": req.ssh_pubkey,
            "repo_url":   req.repo_url,
            "env_vars":   req.env_vars,
            "user":       "dev",
        })

        # 4. Issue a ws_token and mark ready
        token = kennel_client.make_ws_token()
        await _set_ready(ws_id, token)

        log.info(f"[workspace:{ws_id}] ready — terminal at "
                 f"{kennel_client.terminal_url(kennel_name, token)}")

    except Exception as e:
        log.exception(f"[workspace:{ws_id}] provisioning failed: {e}")
        await _set_status(ws_id, WorkspaceStatus.destroyed, error=str(e))


async def _poll_until_done(job_id: str, timeout: int = 600) -> dict:
    deadline = asyncio.get_event_loop().time() + timeout
    while asyncio.get_event_loop().time() < deadline:
        result = await kennel_client.poll_job(job_id)
        if result["status"] in ("done", "failed"):
            return result
        await asyncio.sleep(3)
    return {"status": "failed", "error": "provision timeout"}


async def _set_status(
    ws_id: uuid.UUID,
    status: WorkspaceStatus,
    error: str | None = None,
) -> None:
    from app.db import get_session_context
    async with get_session_context() as db:
        ws = await db.get(Workspace, ws_id)
        if ws:
            ws.status     = status
            ws.updated_at = datetime.utcnow()
            if error:
                ws.meta = {**(ws.meta or {}), "error": error}
            await db.commit()


async def _set_ready(ws_id: uuid.UUID, token: str) -> None:
    from app.db import get_session_context
    async with get_session_context() as db:
        ws = await db.get(Workspace, ws_id)
        if ws:
            ws.status     = WorkspaceStatus.ready
            ws.ws_token   = token
            ws.updated_at = datetime.utcnow()
            await db.commit()


# ── Step 5: Terminal URL issuance ─────────────────────────────────────────────

async def get_terminal_url(
    db: AsyncSession,
    ws_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> str:
    """
    Returns the wss:// URL for the terminal.
    Validates ownership and readiness before issuing.
    """
    ws = await db.get(Workspace, ws_id)

    if not ws or ws.owner_id != owner_id:
        raise ValueError("Workspace not found")
    if ws.status != WorkspaceStatus.ready:
        raise ValueError(f"Workspace not ready: {ws.status}")

    return kennel_client.terminal_url(ws.kennel_name, ws.ws_token)


# ── Teardown ──────────────────────────────────────────────────────────────────

async def stop_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    ws = await db.get(Workspace, ws_id)
    if not ws:
        return
    ws.status = WorkspaceStatus.stopping
    await db.commit()
    await kennel_client.stop_env(ws.kennel_name)
    ws.status = WorkspaceStatus.stopped
    await db.commit()


async def destroy_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    ws = await db.get(Workspace, ws_id)
    if not ws:
        return
    await kennel_client.destroy_env(ws.kennel_name)
    ws.status     = WorkspaceStatus.destroyed
    ws.updated_at = datetime.utcnow()
    await db.commit()