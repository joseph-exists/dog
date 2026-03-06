"""
Synchronous access-control helpers (Phase 0).

Story authoring routes currently use sync SQLModel sessions.
This module mirrors `app.services.access_control` but for `sqlmodel.Session`.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import Session, select

from app.models import (
    AccessGrant,
    AccessGrantRole,
    AccessGrantSubjectType,
    DemoSession,
    Project,
    ProjectResource,
    Story,
    User,
    UserGroupMembership,
)


_ROLE_LEVEL: dict[AccessGrantRole, int] = {
    AccessGrantRole.viewer: 10,
    AccessGrantRole.editor: 20,
    AccessGrantRole.manager: 30,
}


def _role_meets_minimum(*, role: AccessGrantRole, minimum: AccessGrantRole) -> bool:
    return _ROLE_LEVEL[role] >= _ROLE_LEVEL[minimum]


def get_resource_owner_id_sync(
    session: Session,
    *,
    resource_type: str,
    resource_id: UUID,
) -> UUID | None:
    if resource_type == "story":
        story = session.get(Story, resource_id)
        return story.owner_id if story else None
    if resource_type == "demo_session":
        demo_session = session.get(DemoSession, resource_id)
        return demo_session.user_id if demo_session else None
    if resource_type == "project":
        project = session.get(Project, resource_id)
        return project.owner_id if project else None
    return None


def get_effective_role_sync(
    session: Session,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
) -> AccessGrantRole | None:
    if user.is_superuser:
        return AccessGrantRole.manager

    owner_id = get_resource_owner_id_sync(
        session, resource_type=resource_type, resource_id=resource_id
    )
    if owner_id is not None and owner_id == user.id:
        return AccessGrantRole.manager

    direct_stmt = select(AccessGrant.role).where(
        AccessGrant.resource_type == resource_type,
        AccessGrant.resource_id == resource_id,
        AccessGrant.subject_type == AccessGrantSubjectType.user,
        AccessGrant.subject_id == user.id,
    )
    direct = session.exec(direct_stmt).all()

    group_ids_stmt = select(UserGroupMembership.group_id).where(
        UserGroupMembership.user_id == user.id
    )
    group_ids = session.exec(group_ids_stmt).all()
    group_roles: list[AccessGrantRole] = []
    if group_ids:
        group_stmt = select(AccessGrant.role).where(
            AccessGrant.resource_type == resource_type,
            AccessGrant.resource_id == resource_id,
            AccessGrant.subject_type == AccessGrantSubjectType.group,
            AccessGrant.subject_id.in_(group_ids),
        )
        group_roles = session.exec(group_stmt).all()

    roles: list[AccessGrantRole] = [*direct, *group_roles]
    best_direct = max(roles, key=lambda r: _ROLE_LEVEL[r]) if roles else None

    if resource_type != "project":
        project_ids_stmt = select(ProjectResource.project_id).where(
            ProjectResource.resource_type == resource_type,
            ProjectResource.resource_id == resource_id,
        )
        project_ids = session.exec(project_ids_stmt).all()
        if project_ids:
            owners_stmt = select(Project.owner_id).where(Project.id.in_(project_ids))
            owner_ids = session.exec(owners_stmt).all()
            if user.id in owner_ids:
                return AccessGrantRole.manager

            project_direct_stmt = select(AccessGrant.role).where(
                AccessGrant.resource_type == "project",
                AccessGrant.resource_id.in_(project_ids),
                AccessGrant.subject_type == AccessGrantSubjectType.user,
                AccessGrant.subject_id == user.id,
            )
            project_direct = session.exec(project_direct_stmt).all()

            group_ids_stmt = select(UserGroupMembership.group_id).where(
                UserGroupMembership.user_id == user.id
            )
            group_ids = session.exec(group_ids_stmt).all()
            project_group: list[AccessGrantRole] = []
            if group_ids:
                project_group_stmt = select(AccessGrant.role).where(
                    AccessGrant.resource_type == "project",
                    AccessGrant.resource_id.in_(project_ids),
                    AccessGrant.subject_type == AccessGrantSubjectType.group,
                    AccessGrant.subject_id.in_(group_ids),
                )
                project_group = session.exec(project_group_stmt).all()

            project_roles: list[AccessGrantRole] = [*project_direct, *project_group]
            best_project = (
                max(project_roles, key=lambda r: _ROLE_LEVEL[r]) if project_roles else None
            )

            candidates = [r for r in (best_direct, best_project) if r is not None]
            if candidates:
                return max(candidates, key=lambda r: _ROLE_LEVEL[r])

    return best_direct


def has_access_sync(
    session: Session,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
    minimum_role: AccessGrantRole,
) -> bool:
    effective = get_effective_role_sync(
        session, user=user, resource_type=resource_type, resource_id=resource_id
    )
    if effective is None:
        return False
    return _role_meets_minimum(role=effective, minimum=minimum_role)


def require_access_sync(
    session: Session,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
    minimum_role: AccessGrantRole,
    detail: str = "Access denied",
) -> None:
    if has_access_sync(
        session,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        minimum_role=minimum_role,
    ):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
