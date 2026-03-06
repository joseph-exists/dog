"""
CRUD operations for Projects container (Phase 0).

Projects are user-owned collaboration containers. Membership is expressed via
`access_grants` with `resource_type="project"`.

Phase-0 constraint: only project owners (or superusers) can mutate project
metadata and attachments.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    AccessGrant,
    AccessGrantSubjectType,
    Project,
    ProjectCreate,
    ProjectResource,
    ProjectResourceCreate,
    ProjectUpdate,
    User,
    UserGroupMembership,
)
from app.services.access_control import require_access
from app.models import AccessGrantRole


async def create_project(
    session: AsyncSession,
    *,
    owner_id: UUID,
    project_in: ProjectCreate,
) -> Project:
    project = Project(owner_id=owner_id, name=project_in.name, description=project_in.description)
    session.add(project)
    await session.flush()
    await session.refresh(project)
    return project


async def get_project_by_id(session: AsyncSession, project_id: UUID) -> Project | None:
    return await session.get(Project, project_id)


async def require_project_owner_or_superuser(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
) -> Project:
    project = await get_project_by_id(session, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if actor.is_superuser or project.owner_id == actor.id:
        return project
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


async def list_projects_visible_to_user(
    session: AsyncSession,
    *,
    user: User,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[Project], int]:
    if user.is_superuser:
        statement = select(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit)
        projects = list((await session.exec(statement)).all())
        count_stmt = select(func.count()).select_from(Project)
        count = int((await session.exec(count_stmt)).one())
        return projects, count

    group_ids_stmt = select(UserGroupMembership.group_id).where(UserGroupMembership.user_id == user.id)
    group_ids = (await session.exec(group_ids_stmt)).all()

    direct_stmt = select(AccessGrant.resource_id).where(
        AccessGrant.resource_type == "project",
        AccessGrant.subject_type == AccessGrantSubjectType.user,
        AccessGrant.subject_id == user.id,
    )
    shared_ids = set((await session.exec(direct_stmt)).all())

    if group_ids:
        group_stmt = select(AccessGrant.resource_id).where(
            AccessGrant.resource_type == "project",
            AccessGrant.subject_type == AccessGrantSubjectType.group,
            AccessGrant.subject_id.in_(group_ids),
        )
        shared_ids.update((await session.exec(group_stmt)).all())

    # Owner projects are always visible.
    statement = (
        select(Project)
        .where((Project.owner_id == user.id) | (Project.id.in_(shared_ids)))
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    projects = list((await session.exec(statement)).all())

    count_stmt = select(func.count()).select_from(Project).where(
        (Project.owner_id == user.id) | (Project.id.in_(shared_ids))
    )
    count = int((await session.exec(count_stmt)).one())
    return projects, count


async def update_project(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
    project_in: ProjectUpdate,
) -> Project:
    project = await require_project_owner_or_superuser(session, actor=actor, project_id=project_id)
    update_data = project_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)
    session.add(project)
    await session.flush()
    await session.refresh(project)
    return project


async def delete_project(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
) -> None:
    project = await require_project_owner_or_superuser(session, actor=actor, project_id=project_id)
    await session.delete(project)


async def list_project_resources(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
) -> list[ProjectResource]:
    await require_access(
        session,
        user=actor,
        resource_type="project",
        resource_id=project_id,
        minimum_role=AccessGrantRole.viewer,
        detail="Access denied",
    )
    stmt = (
        select(ProjectResource)
        .where(ProjectResource.project_id == project_id)
        .order_by(ProjectResource.created_at.desc())
    )
    return list((await session.exec(stmt)).all())


async def attach_project_resource(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
    resource_in: ProjectResourceCreate,
) -> ProjectResource:
    await require_project_owner_or_superuser(session, actor=actor, project_id=project_id)

    existing_stmt = select(ProjectResource).where(
        ProjectResource.project_id == project_id,
        ProjectResource.resource_type == resource_in.resource_type,
        ProjectResource.resource_id == resource_in.resource_id,
    )
    existing = (await session.exec(existing_stmt)).one_or_none()
    if existing:
        return existing

    row = ProjectResource(
        project_id=project_id,
        resource_type=resource_in.resource_type,
        resource_id=resource_in.resource_id,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)
    return row


async def detach_project_resource(
    session: AsyncSession,
    *,
    actor: User,
    project_id: UUID,
    resource_in: ProjectResourceCreate,
) -> None:
    await require_project_owner_or_superuser(session, actor=actor, project_id=project_id)

    stmt = select(ProjectResource).where(
        ProjectResource.project_id == project_id,
        ProjectResource.resource_type == resource_in.resource_type,
        ProjectResource.resource_id == resource_in.resource_id,
    )
    row = (await session.exec(stmt)).one_or_none()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Attachment not found")
    await session.delete(row)

