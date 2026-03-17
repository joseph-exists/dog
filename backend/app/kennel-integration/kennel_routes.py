# backend/app/api/routes/workspaces.py
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.workspace import (
    WorkspaceCreate, WorkspacePublic, WorkspaceStatus
)
from app.services import workspace_service
from app.services import kennel_client

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", response_model=WorkspacePublic, status_code=202)
async def create_workspace(
    req: WorkspaceCreate,
    db: AsyncSession    = Depends(get_db),
    user: User          = Depends(get_current_user),
):
    ws = await workspace_service.spawn_workspace(db, user.id, req)
    return ws


@router.get("/", response_model=list[WorkspacePublic])
async def list_workspaces(
    db:   AsyncSession = Depends(get_db),
    user: User         = Depends(get_current_user),
):
    result = await db.exec(
        select(Workspace).where(Workspace.owner_id == user.id)
    )
    return result.all()


@router.get("/{ws_id}", response_model=WorkspacePublic)
async def get_workspace(
    ws_id: uuid.UUID,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    ws = await db.get(Workspace, ws_id)
    if not ws or ws.owner_id != user.id:
        raise HTTPException(404)
    return ws


@router.get("/{ws_id}/terminal")
async def get_terminal(
    ws_id: uuid.UUID,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    """
    Issues the wss:// URL. Frontend connects directly to kennel via Traefik.
    Token is single-use scoped — rotate on each call.
    """
    try:
        url = await workspace_service.get_terminal_url(db, ws_id, user.id)
        return {"terminal_url": url}
    except ValueError as e:
        raise HTTPException(400, detail=str(e))


@router.post("/{ws_id}/stop")
async def stop_workspace(
    ws_id: uuid.UUID,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    ws = await db.get(Workspace, ws_id)
    if not ws or ws.owner_id != user.id:
        raise HTTPException(404)
    await workspace_service.stop_workspace(db, ws_id)
    return {"status": "stopped"}


@router.delete("/{ws_id}")
async def destroy_workspace(
    ws_id: uuid.UUID,
    db:    AsyncSession = Depends(get_db),
    user:  User         = Depends(get_current_user),
):
    ws = await db.get(Workspace, ws_id)
    if not ws or ws.owner_id != user.id:
        raise HTTPException(404)
    await workspace_service.destroy_workspace(db, ws_id)
    return {"status": "destroyed"}