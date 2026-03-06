from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud_projects import (
    attach_project_resource,
    create_project,
    delete_project,
    detach_project_resource,
    get_project_by_id,
    list_project_resources,
    list_projects_visible_to_user,
    require_project_owner_or_superuser,
    update_project,
)
from app.models import (
    AccessGrantRole,
    Message,
    ProjectCreate,
    ProjectPublic,
    ProjectsPublic,
    ProjectResourceCreate,
    ProjectResourcePublic,
    ProjectResourcesPublic,
    ProjectUpdate,
)
from app.services.access_control import require_access

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def create_new_project(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    project_in: ProjectCreate,
) -> Any:
    project = await create_project(session, owner_id=current_user.id, project_in=project_in)
    return ProjectPublic.model_validate(project)


@router.get("/", response_model=ProjectsPublic)
async def list_projects(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    projects, count = await list_projects_visible_to_user(
        session, user=current_user, skip=skip, limit=limit
    )
    return ProjectsPublic(
        data=[ProjectPublic.model_validate(p) for p in projects],
        count=count,
    )


@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    project_id: UUID,
) -> Any:
    project = await get_project_by_id(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    await require_access(
        session,
        user=current_user,
        resource_type="project",
        resource_id=project_id,
        minimum_role=AccessGrantRole.viewer,
        detail="Access denied",
    )
    return ProjectPublic.model_validate(project)


@router.patch("/{project_id}", response_model=ProjectPublic)
async def patch_project(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    project_id: UUID,
    project_in: ProjectUpdate,
) -> Any:
    updated = await update_project(
        session, actor=current_user, project_id=project_id, project_in=project_in
    )
    return ProjectPublic.model_validate(updated)


@router.delete("/{project_id}", response_model=Message)
async def delete_project_route(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    project_id: UUID,
) -> Any:
    await delete_project(session, actor=current_user, project_id=project_id)
    return Message(message="Project deleted")


@router.get("/{project_id}/resources", response_model=ProjectResourcesPublic)
async def get_project_resources(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    project_id: UUID,
) -> Any:
    rows = await list_project_resources(session, actor=current_user, project_id=project_id)
    return ProjectResourcesPublic(
        data=[ProjectResourcePublic.model_validate(r) for r in rows],
        count=len(rows),
    )


@router.post(
    "/{project_id}/resources",
    response_model=ProjectResourcePublic,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_resource(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    project_id: UUID,
    resource_in: ProjectResourceCreate,
) -> Any:
    row = await attach_project_resource(
        session,
        actor=current_user,
        project_id=project_id,
        resource_in=resource_in,
    )
    return ProjectResourcePublic.model_validate(row)


@router.delete("/{project_id}/resources", response_model=Message)
async def remove_project_resource(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    project_id: UUID,
    resource_in: ProjectResourceCreate,
) -> Any:
    await detach_project_resource(
        session,
        actor=current_user,
        project_id=project_id,
        resource_in=resource_in,
    )
    return Message(message="Resource detached")

