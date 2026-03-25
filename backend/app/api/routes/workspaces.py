from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.models import Message, WorkspacePublic, WorkspaceCreate, WorkspacesPublic
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
    return await workspace_service.to_workspace_public(
        session,
        workspace,
        user=current_user,
    )


@router.get("/", response_model=WorkspacesPublic)
async def list_workspaces(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    workspaces = await workspace_service.list_workspaces_visible_to_user(
        session,
        user=current_user,
    )
    return WorkspacesPublic(
        data=[
            await workspace_service.to_workspace_public(
                session,
                workspace,
                user=current_user,
            )
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
    workspace = await workspace_service.get_workspace_for_user(
        session,
        workspace_id=workspace_id,
        user=current_user,
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    return await workspace_service.to_workspace_public(
        session,
        workspace,
        user=current_user,
    )


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
            current_user,
        )
    except ValueError as exc:
        detail = str(exc)
        status_code = status.HTTP_404_NOT_FOUND if detail == "Workspace not found" else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=detail) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    return {"terminal_url": url}


@router.post("/{workspace_id}/stop", response_model=Message)
async def stop_workspace(
    *,
    workspace_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await workspace_service.get_workspace_for_user(
        session,
        workspace_id=workspace_id,
        user=current_user,
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    allowed_actions = await workspace_service.get_allowed_actions_for_user(
        session,
        workspace=workspace,
        user=current_user,
    )
    if workspace_service.WorkspaceAction.stop not in allowed_actions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace stop is not allowed")
    await workspace_service.stop_workspace(session, workspace_id)
    return Message(message="Workspace stopped")


@router.post("/{workspace_id}/start", response_model=Message)
async def start_workspace(
    *,
    workspace_id: UUID,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    workspace = await workspace_service.get_workspace_for_user(
        session,
        workspace_id=workspace_id,
        user=current_user,
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    allowed_actions = await workspace_service.get_allowed_actions_for_user(
        session,
        workspace=workspace,
        user=current_user,
    )
    if workspace_service.WorkspaceAction.start not in allowed_actions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace start is not allowed")
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
    workspace = await workspace_service.get_workspace_for_user(
        session,
        workspace_id=workspace_id,
        user=current_user,
    )
    if workspace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workspace not found")
    allowed_actions = await workspace_service.get_allowed_actions_for_user(
        session,
        workspace=workspace,
        user=current_user,
    )
    if workspace_service.WorkspaceAction.destroy not in allowed_actions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace destroy is not allowed")
    await workspace_service.destroy_workspace(session, workspace_id)
    return Message(message="Workspace destroyed")
