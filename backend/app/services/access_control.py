"""
Minimal access-control primitives (Phase 0).

This module provides:
- Object-scoped access checks via AccessGrant (user + group subjects)
- Ownership + superuser bypass semantics

Deliberate constraints (Phase 0):
- Share-management is not delegated; only resource owners and superusers can
  create/revoke grants.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import String, cast
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    AccessGrant,
    AccessGrantRole,
    AccessGrantSubjectType,
    AudienceScope,
    DemoSession,
    Page,
    PersonaGroupMembership,
    Project,
    ProjectResource,
    ResolvedUserPageAudiencePublic,
    Story,
    User,
    UserGroupMembership,
    UserPersona,
)


_ROLE_LEVEL: dict[AccessGrantRole, int] = {
    AccessGrantRole.viewer: 10,
    AccessGrantRole.editor: 20,
    AccessGrantRole.manager: 30,
}


@dataclass(frozen=True)
class ResourceSpec:
    model: type
    owner_attr: str


_RESOURCE_REGISTRY: dict[str, ResourceSpec] = {
    "story": ResourceSpec(model=Story, owner_attr="owner_id"),
    "demo_session": ResourceSpec(model=DemoSession, owner_attr="user_id"),
    "project": ResourceSpec(model=Project, owner_attr="owner_id"),
    "page": ResourceSpec(model=Page, owner_attr="owner_id"),
}


def _subject_type_matches(*values: str):
    return cast(AccessGrant.subject_type, String).in_(values)


def _role_meets_minimum(*, role: AccessGrantRole, minimum: AccessGrantRole) -> bool:
    return _ROLE_LEVEL[role] >= _ROLE_LEVEL[minimum]


async def get_resource_owner_id(
    session: AsyncSession,
    *,
    resource_type: str,
    resource_id: UUID,
) -> UUID | None:
    """
    Resolve the owner_id for a resource.

    Returns:
        Owner UUID if the resource exists and has an owner, otherwise None.
    """
    spec = _RESOURCE_REGISTRY.get(resource_type)
    if not spec:
        return None

    statement = select(spec.model).where(spec.model.id == resource_id)  # type: ignore[attr-defined]
    result = await session.exec(statement)
    resource = result.one_or_none()
    if not resource:
        return None
    return getattr(resource, spec.owner_attr, None)


async def get_effective_role(
    session: AsyncSession,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
) -> AccessGrantRole | None:
    """
    Return the user's effective role for a resource, or None if no access.

    Precedence:
    1) superuser -> manager
    2) resource owner -> manager
    3) best direct user grant
    4) best group grant across all memberships
    """
    if user.is_superuser:
        return AccessGrantRole.manager

    owner_id = await get_resource_owner_id(
        session, resource_type=resource_type, resource_id=resource_id
    )
    if owner_id is not None and owner_id == user.id:
        return AccessGrantRole.manager

    # Direct user grant
    direct_stmt = select(AccessGrant.role).where(
        AccessGrant.resource_type == resource_type,
        AccessGrant.resource_id == resource_id,
        AccessGrant.subject_type == AccessGrantSubjectType.user,
        AccessGrant.subject_id == user.id,
    )
    direct = (await session.exec(direct_stmt)).all()

    owned_persona_ids_stmt = select(UserPersona.id).where(UserPersona.user_id == user.id)
    owned_persona_ids = (await session.exec(owned_persona_ids_stmt)).all()

    persona_direct: list[AccessGrantRole] = []
    if owned_persona_ids:
        persona_direct_stmt = select(AccessGrant.role).where(
            AccessGrant.resource_type == resource_type,
            AccessGrant.resource_id == resource_id,
            _subject_type_matches(
                AccessGrantSubjectType.user_persona.value,
                "userpersona",
            ),
            AccessGrant.subject_id.in_(owned_persona_ids),
        )
        persona_direct = (await session.exec(persona_direct_stmt)).all()

    # Group grants (subject_id in user's group memberships)
    group_ids_stmt = select(UserGroupMembership.group_id).where(
        UserGroupMembership.user_id == user.id
    )
    group_ids = (await session.exec(group_ids_stmt)).all()
    group_roles: list[AccessGrantRole] = []
    if group_ids:
        group_stmt = select(AccessGrant.role).where(
            AccessGrant.resource_type == resource_type,
            AccessGrant.resource_id == resource_id,
            AccessGrant.subject_type == AccessGrantSubjectType.group,
            AccessGrant.subject_id.in_(group_ids),
        )
        group_roles = (await session.exec(group_stmt)).all()

    persona_group_ids: list[UUID] = []
    persona_group_roles: list[AccessGrantRole] = []
    if owned_persona_ids:
        persona_group_ids_stmt = select(PersonaGroupMembership.group_id).where(
            PersonaGroupMembership.user_persona_id.in_(owned_persona_ids),
            PersonaGroupMembership.is_active == True,  # noqa: E712
        )
        persona_group_ids = (await session.exec(persona_group_ids_stmt)).all()
        if persona_group_ids:
            persona_group_stmt = select(AccessGrant.role).where(
                AccessGrant.resource_type == resource_type,
                AccessGrant.resource_id == resource_id,
                _subject_type_matches(
                    AccessGrantSubjectType.persona_group.value,
                    "personagroup",
                ),
                AccessGrant.subject_id.in_(persona_group_ids),
            )
            persona_group_roles = (await session.exec(persona_group_stmt)).all()

    roles: list[AccessGrantRole] = [*direct, *persona_direct, *group_roles, *persona_group_roles]
    if not roles:
        roles = []

    best_direct = max(roles, key=lambda r: _ROLE_LEVEL[r]) if roles else None

    # Project-derived access: if the resource is attached to one or more projects,
    # project grants contribute to effective role. This does not apply to projects
    # themselves (no recursion) and does not handle rooms (rooms remain membership-gated).
    if resource_type != "project":
        project_ids_stmt = select(ProjectResource.project_id).where(
            ProjectResource.resource_type == resource_type,
            ProjectResource.resource_id == resource_id,
        )
        project_ids = (await session.exec(project_ids_stmt)).all()
        if project_ids:
            # Owner check for projects (treat project owners as manager).
            owners_stmt = select(Project.owner_id).where(Project.id.in_(project_ids))
            owner_ids = (await session.exec(owners_stmt)).all()
            if user.id in owner_ids:
                return AccessGrantRole.manager

            project_direct_stmt = select(AccessGrant.role).where(
                AccessGrant.resource_type == "project",
                AccessGrant.resource_id.in_(project_ids),
                AccessGrant.subject_type == AccessGrantSubjectType.user,
                AccessGrant.subject_id == user.id,
            )
            project_direct = (await session.exec(project_direct_stmt)).all()

            project_persona_direct: list[AccessGrantRole] = []
            if owned_persona_ids:
                project_persona_direct_stmt = select(AccessGrant.role).where(
                    AccessGrant.resource_type == "project",
                    AccessGrant.resource_id.in_(project_ids),
                    _subject_type_matches(
                        AccessGrantSubjectType.user_persona.value,
                        "userpersona",
                    ),
                    AccessGrant.subject_id.in_(owned_persona_ids),
                )
                project_persona_direct = (await session.exec(project_persona_direct_stmt)).all()

            group_ids_stmt = select(UserGroupMembership.group_id).where(
                UserGroupMembership.user_id == user.id
            )
            group_ids = (await session.exec(group_ids_stmt)).all()
            project_group: list[AccessGrantRole] = []
            if group_ids:
                project_group_stmt = select(AccessGrant.role).where(
                    AccessGrant.resource_type == "project",
                    AccessGrant.resource_id.in_(project_ids),
                    AccessGrant.subject_type == AccessGrantSubjectType.group,
                    AccessGrant.subject_id.in_(group_ids),
                )
                project_group = (await session.exec(project_group_stmt)).all()

            project_persona_group: list[AccessGrantRole] = []
            if persona_group_ids:
                project_persona_group_stmt = select(AccessGrant.role).where(
                    AccessGrant.resource_type == "project",
                    AccessGrant.resource_id.in_(project_ids),
                    _subject_type_matches(
                        AccessGrantSubjectType.persona_group.value,
                        "personagroup",
                    ),
                    AccessGrant.subject_id.in_(persona_group_ids),
                )
                project_persona_group = (
                    await session.exec(project_persona_group_stmt)
                ).all()

            project_roles: list[AccessGrantRole] = [
                *project_direct,
                *project_persona_direct,
                *project_group,
                *project_persona_group,
            ]
            best_project = (
                max(project_roles, key=lambda r: _ROLE_LEVEL[r]) if project_roles else None
            )

            candidates = [r for r in (best_direct, best_project) if r is not None]
            if candidates:
                return max(candidates, key=lambda r: _ROLE_LEVEL[r])

    return best_direct


async def has_access(
    session: AsyncSession,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
    minimum_role: AccessGrantRole,
) -> bool:
    """Return True if the user has at least minimum_role on the resource."""
    effective = await get_effective_role(
        session, user=user, resource_type=resource_type, resource_id=resource_id
    )
    if effective is None:
        return False
    return _role_meets_minimum(role=effective, minimum=minimum_role)


async def require_access(
    session: AsyncSession,
    *,
    user: User,
    resource_type: str,
    resource_id: UUID,
    minimum_role: AccessGrantRole,
    detail: str = "Access denied",
) -> None:
    """Raise 403 if the user lacks the required role."""
    if await has_access(
        session,
        user=user,
        resource_type=resource_type,
        resource_id=resource_id,
        minimum_role=minimum_role,
    ):
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _extract_custom_audience_keys(page: Page) -> set[str]:
    for block in page.layout_json:
        if block.get("type") != "audiencePresentation":
            continue
        content = block.get("content")
        if not isinstance(content, dict):
            continue
        presentations = content.get("presentations")
        if not isinstance(presentations, list):
            continue

        keys: set[str] = set()
        for presentation in presentations:
            if not isinstance(presentation, dict):
                continue
            if presentation.get("audienceScope") != "custom":
                continue
            audience_key = presentation.get("audienceKey")
            if isinstance(audience_key, str) and audience_key.strip():
                keys.add(audience_key.strip())
        return keys

    return set()


async def resolve_user_page_audience(
    session: AsyncSession,
    *,
    page: Page,
    viewer: User | None,
) -> ResolvedUserPageAudiencePublic:
    if viewer is None:
        return ResolvedUserPageAudiencePublic(scope=AudienceScope.PUBLIC)

    if viewer.is_superuser or viewer.id == page.owner_id:
        return ResolvedUserPageAudiencePublic(
            scope=AudienceScope.CUSTOM,
            is_owner=True,
            matched_user_ids=[viewer.id],
        )

    owned_persona_ids_stmt = select(UserPersona.id).where(UserPersona.user_id == viewer.id)
    owned_persona_ids = list((await session.exec(owned_persona_ids_stmt)).all())

    user_group_ids_stmt = select(UserGroupMembership.group_id).where(
        UserGroupMembership.user_id == viewer.id
    )
    user_group_ids = list((await session.exec(user_group_ids_stmt)).all())

    persona_group_ids: list[UUID] = []
    if owned_persona_ids:
        persona_group_ids_stmt = select(PersonaGroupMembership.group_id).where(
            PersonaGroupMembership.user_persona_id.in_(owned_persona_ids),
            PersonaGroupMembership.is_active == True,  # noqa: E712
        )
        persona_group_ids = list((await session.exec(persona_group_ids_stmt)).all())

    matched_user_ids = list(
        (
            await session.exec(
                select(AccessGrant.subject_id).where(
                    AccessGrant.resource_type == "page",
                    AccessGrant.resource_id == page.id,
                    AccessGrant.subject_type == AccessGrantSubjectType.user,
                    AccessGrant.subject_id == viewer.id,
                )
            )
        ).all()
    )

    matched_user_persona_ids: list[UUID] = []
    if owned_persona_ids:
        matched_user_persona_ids = list(
            (
                await session.exec(
                    select(AccessGrant.subject_id).where(
                        AccessGrant.resource_type == "page",
                        AccessGrant.resource_id == page.id,
                        _subject_type_matches(
                            AccessGrantSubjectType.user_persona.value,
                            "userpersona",
                        ),
                        AccessGrant.subject_id.in_(owned_persona_ids),
                    )
                )
            ).all()
        )

    matched_group_ids: list[UUID] = []
    if user_group_ids:
        matched_group_ids = list(
            (
                await session.exec(
                    select(AccessGrant.subject_id).where(
                        AccessGrant.resource_type == "page",
                        AccessGrant.resource_id == page.id,
                        AccessGrant.subject_type == AccessGrantSubjectType.group,
                        AccessGrant.subject_id.in_(user_group_ids),
                    )
                )
            ).all()
        )

    matched_persona_group_ids: list[UUID] = []
    if persona_group_ids:
        matched_persona_group_ids = list(
            (
                await session.exec(
                    select(AccessGrant.subject_id).where(
                        AccessGrant.resource_type == "page",
                        AccessGrant.resource_id == page.id,
                        _subject_type_matches(
                            AccessGrantSubjectType.persona_group.value,
                            "personagroup",
                        ),
                        AccessGrant.subject_id.in_(persona_group_ids),
                    )
                )
            ).all()
        )

    candidate_audience_keys = {
        str(viewer.id),
        *(str(subject_id) for subject_id in owned_persona_ids),
        *(str(subject_id) for subject_id in user_group_ids),
        *(str(subject_id) for subject_id in persona_group_ids),
        *(str(subject_id) for subject_id in matched_user_ids),
        *(str(subject_id) for subject_id in matched_user_persona_ids),
        *(str(subject_id) for subject_id in matched_group_ids),
        *(str(subject_id) for subject_id in matched_persona_group_ids),
    }
    matched_audience_keys = sorted(
        _extract_custom_audience_keys(page).intersection(candidate_audience_keys)
    )

    if matched_audience_keys:
        scope = AudienceScope.CUSTOM
    elif matched_user_ids or matched_user_persona_ids:
        scope = AudienceScope.TRUSTED
    elif matched_group_ids or matched_persona_group_ids:
        scope = AudienceScope.COLLABORATORS
    else:
        scope = AudienceScope.PUBLIC

    return ResolvedUserPageAudiencePublic(
        scope=scope,
        matched_user_ids=matched_user_ids,
        matched_user_persona_ids=matched_user_persona_ids,
        matched_group_ids=matched_group_ids,
        matched_persona_group_ids=matched_persona_group_ids,
        matched_audience_keys=matched_audience_keys,
    )
