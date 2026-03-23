import asyncio
import logging
import uuid
from datetime import datetime

from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.db import async_session_maker
from app.models import Workspace, WorkspaceCreate, WorkspaceStatus
from app.services import kennel_client

log = logging.getLogger(__name__)


async def spawn_workspace(
    db: AsyncSession,
    owner_id: uuid.UUID,
    req: WorkspaceCreate,
) -> Workspace:
    """
    Create the workspace record and start kennel provisioning asynchronously.
    """
    kennel_name = f"env-{uuid.uuid4().hex[:8]}"

    workspace = Workspace(
        name=req.name,
        flavour=req.flavour,
        kind=req.kind,
        owner_id=owner_id,
        kennel_name=kennel_name,
        status=WorkspaceStatus.provisioning,
        meta={
            "repo_url": req.repo_url,
            "ssh_pubkey": req.ssh_pubkey,
            "env_vars": req.env_vars,
        },
    )
    db.add(workspace)
    await db.flush()
    await db.refresh(workspace)

    asyncio.create_task(
        _provision_workspace_after_commit(
            ws_id=workspace.id,
            kennel_name=kennel_name,
            req=req,
        )
    )

    return workspace


async def _provision_workspace_after_commit(
    ws_id: uuid.UUID,
    kennel_name: str,
    req: WorkspaceCreate,
) -> None:
    """
    Yield once so the request-scoped transaction can finish before
    background provisioning starts using its own session.
    """
    await asyncio.sleep(0)
    await _provision_workspace(ws_id=ws_id, kennel_name=kennel_name, req=req)


async def _provision_workspace(
    ws_id: uuid.UUID,
    kennel_name: str,
    req: WorkspaceCreate,
) -> None:
    """
    Drive the kennel lifecycle: create -> poll -> inject -> mark ready.
    """
    try:
        job = await kennel_client.create_env(
            name=kennel_name,
            kind=req.kind,
            flavour=req.flavour.value,
        )
        job_id = job["job_id"]
        await _update_workspace(ws_id, kennel_job=job_id)

        log.info("[workspace:%s] kennel job %s started", ws_id, job_id)

        result = await _poll_until_done(job_id, timeout=600)
        if result["status"] == "failed":
            await _update_workspace(
                ws_id,
                status=WorkspaceStatus.destroyed,
                error=result.get("error"),
            )
            return

        inject_result = await kennel_client.inject_workspace(
            kennel_name,
            {
                "ssh_pubkey": req.ssh_pubkey,
                "repo_url": req.repo_url,
                "env_vars": req.env_vars,
                "user": "dev",
            },
        )

        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.ready,
            ws_token=inject_result.get("token"),
            meta_updates={"inject_errors": inject_result.get("errors", [])},
        )

        log.info(
            "[workspace:%s] ready at %s",
            ws_id,
            kennel_client.terminal_url(
                kennel_name,
                inject_result["token"],
            ),
        )
    except Exception as exc:
        log.exception("[workspace:%s] provisioning failed: %s", ws_id, exc)
        await _update_workspace(
            ws_id,
            status=WorkspaceStatus.destroyed,
            error=str(exc),
        )


async def _poll_until_done(job_id: str, timeout: int = 600) -> dict:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        result = await kennel_client.poll_job(job_id)
        if result["status"] in {"done", "failed"}:
            return result
        await asyncio.sleep(3)
    return {"status": "failed", "error": "provision timeout"}


async def _update_workspace(
    ws_id: uuid.UUID,
    *,
    status: WorkspaceStatus | None = None,
    kennel_job: str | None = None,
    ws_token: str | None = None,
    error: str | None = None,
    meta_updates: dict | None = None,
) -> None:
    async with async_session_maker() as session:
        workspace = await session.get(Workspace, ws_id)
        if workspace is None:
            return

        if status is not None:
            workspace.status = status
        if kennel_job is not None:
            workspace.kennel_job = kennel_job
        if ws_token is not None:
            workspace.ws_token = ws_token

        merged_meta = dict(workspace.meta or {})
        if meta_updates:
            merged_meta.update(meta_updates)
        if error:
            merged_meta["error"] = error
        if merged_meta:
            workspace.meta = merged_meta

        workspace.updated_at = datetime.utcnow()
        session.add(workspace)
        await session.commit()


async def get_terminal_url(
    db: AsyncSession,
    ws_id: uuid.UUID,
    owner_id: uuid.UUID,
) -> str:
    """
    Return the terminal websocket URL for a ready workspace owned by the user.
    """
    workspace = await db.get(Workspace, ws_id)
    if workspace is None or workspace.owner_id != owner_id:
        raise ValueError("Workspace not found")
    if workspace.status != WorkspaceStatus.ready:
        raise ValueError(f"Workspace not ready: {workspace.status}")
    if not workspace.kennel_name:
        raise ValueError("Workspace terminal is not available")

    token_result = await kennel_client.issue_terminal_token(workspace.kennel_name)
    token = token_result.get("token")
    if not token:
        raise ValueError("Workspace terminal is not available")

    workspace.ws_token = token
    workspace.updated_at = datetime.utcnow()
    db.add(workspace)
    await db.commit()
    await db.refresh(workspace)

    return kennel_client.terminal_url(workspace.kennel_name, token)


async def stop_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    workspace = await db.get(Workspace, ws_id)
    if workspace is None or not workspace.kennel_name:
        return

    workspace.status = WorkspaceStatus.stopping
    workspace.updated_at = datetime.utcnow()
    db.add(workspace)
    await db.flush()

    await kennel_client.stop_env(workspace.kennel_name)

    workspace.status = WorkspaceStatus.stopped
    workspace.updated_at = datetime.utcnow()
    db.add(workspace)
    await db.flush()


async def destroy_workspace(db: AsyncSession, ws_id: uuid.UUID) -> None:
    workspace = await db.get(Workspace, ws_id)
    if workspace is None:
        return

    if workspace.kennel_name:
        await kennel_client.destroy_env(workspace.kennel_name)

    workspace.status = WorkspaceStatus.destroyed
    workspace.updated_at = datetime.utcnow()
    db.add(workspace)
    await db.flush()
