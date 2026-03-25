from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.models import Message, Workspace, WorkspacePublic, WorkspaceCreate, WorkspacesPublic
from app.services import workspace_service

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


@router.post("/", response_model=WorkspacePublic, status_code=status.HTTP_202_ACCEPTED)
async def create_workspace(
    *,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    workspace_in: WorkspaceCreate,
) -> Any:
    try:
        workspace = await workspace_service.spawn_workspace(
            session,
            current_user.id,
            workspace_in,
        )
    except workspace_service.WorkspaceBootstrapValidationError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "message": str(exc),
                "error_code": exc.error_code,
            },
        ) from exc
    return await workspace_service.to_workspace_public(session, workspace)


@router.get("/", response_model=WorkspacesPublic)
async def list_workspaces(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    result = await session.exec(
        select(Workspace).where(Workspace.owner_id == current_user.id)
    )
    workspaces = result.all()
    return WorkspacesPublic(
        data=[
            await workspace_service.to_workspace_public(session, workspace)
            for workspace in workspaces
        ],
        count=len(workspaces),
    )


@router.get("/{workspace_id}", response_model=WorkspacePublic)
async def get_workspace(
    workspace_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await workspace_service.to_workspace_public(session, workspace)


@router.get("/{workspace_id}/terminal")
async def get_workspace_terminal(
    workspace_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> dict[str, str]:
    try:
        url = await workspace_service.get_terminal_url(
            session,
            workspace_id,
            current_user.id,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if detail == "Workspace not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    return {"terminal_url": url}


@router.post("/{workspace_id}/stop", response_model=Message)
async def stop_workspace(
    *,
    workspace_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    await workspace_service.stop_workspace(session, workspace_id)
    return Message(message="Workspace stopped")


@router.post("/{workspace_id}/start", response_model=Message)
async def start_workspace(
    *,
    workspace_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    try:
        await workspace_service.start_workspace(session, workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return Message(message="Workspace started")


@router.delete("/{workspace_id}", response_model=Message)
async def destroy_workspace(
    *,
    workspace_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await session.get(Workspace, workspace_id)
    if workspace is None or workspace.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    await workspace_service.destroy_workspace(session, workspace_id)
    return Message(message="Workspace destroyed")
