"""
CRUD operations for object-scoped access grants (Phase 0).

Phase-0 constraint: share-management is not delegated.
Only the resource owner (or a superuser) can create/revoke grants.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    AccessGrant,
    AccessGrantRevokeRequest,
    AccessGrantRole,
    AccessGrantSubjectType,
    AccessGrantUpsertRequest,
    DemoSession,
    PersonaGroup,
    User,
    UserGroup,
    UserPersona,
)
from app.services.access_control import get_effective_role, get_resource_owner_id
from app.crud import add_participant, remove_participant


async def _require_owner_or_superuser(
    session: AsyncSession,
    *,
    actor: User,
    resource_type: str,
    resource_id: UUID,
) -> None:
    if actor.is_superuser:
        return
    owner_id = await get_resource_owner_id(
        session, resource_type=resource_type, resource_id=resource_id
    )
    if owner_id is None or owner_id != actor.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _validate_requested_role(role: AccessGrantRole) -> None:
    # No delegated share-management in Phase 0.
    if role == AccessGrantRole.manager:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="manager role is not assignable in Phase 0",
        )


async def _validate_subject_exists(
    session: AsyncSession,
    *,
    subject_type: AccessGrantSubjectType,
    subject_id: UUID,
) -> None:
    if subject_type == AccessGrantSubjectType.user:
        subject = await session.get(User, subject_id)
    elif subject_type == AccessGrantSubjectType.group:
        subject = await session.get(UserGroup, subject_id)
    elif subject_type == AccessGrantSubjectType.user_persona:
        subject = await session.get(UserPersona, subject_id)
    elif subject_type == AccessGrantSubjectType.persona_group:
        subject = await session.get(PersonaGroup, subject_id)
    else:
        subject = None

    if subject is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Grant subject not found",
        )


async def list_access_grants(
    session: AsyncSession,
    *,
    actor: User,
    resource_type: str,
    resource_id: UUID,
) -> list[AccessGrant]:
    await _require_owner_or_superuser(
        session, actor=actor, resource_type=resource_type, resource_id=resource_id
    )
    stmt = (
        select(AccessGrant)
        .where(
            AccessGrant.resource_type == resource_type,
            AccessGrant.resource_id == resource_id,
        )
        .order_by(AccessGrant.created_at.desc())
    )
    return list((await session.exec(stmt)).all())


async def get_effective_access_role(
    session: AsyncSession,
    *,
    actor: User,
    resource_type: str,
    resource_id: UUID,
) -> AccessGrantRole | None:
    return await get_effective_role(
        session,
        user=actor,
        resource_type=resource_type,
        resource_id=resource_id,
    )


async def upsert_access_grant(
    session: AsyncSession,
    *,
    actor: User,
    resource_type: str,
    resource_id: UUID,
    grant_in: AccessGrantUpsertRequest,
) -> AccessGrant:
    await _require_owner_or_superuser(
        session, actor=actor, resource_type=resource_type, resource_id=resource_id
    )
    _validate_requested_role(grant_in.role)
    await _validate_subject_exists(
        session,
        subject_type=grant_in.subject_type,
        subject_id=grant_in.subject_id,
    )

    existing_stmt = select(AccessGrant).where(
        AccessGrant.resource_type == resource_type,
        AccessGrant.resource_id == resource_id,
        AccessGrant.subject_type == grant_in.subject_type,
        AccessGrant.subject_id == grant_in.subject_id,
    )
    existing = (await session.exec(existing_stmt)).one_or_none()
    if existing:
        existing.role = grant_in.role
        session.add(existing)
        await session.flush()
        await session.refresh(existing)
        if resource_type == "demo_session" and grant_in.subject_type == "user":
            demo_session = await session.get(DemoSession, resource_id)
            if demo_session:
                await add_participant(
                    room_id=demo_session.room_id,
                    user_id=actor.id,
                    participant_id=str(grant_in.subject_id),
                    participant_type="user",
                    role="member",
                    session=session,
                )
        return existing

    grant = AccessGrant(
        resource_type=resource_type,
        resource_id=resource_id,
        subject_type=grant_in.subject_type,
        subject_id=grant_in.subject_id,
        role=grant_in.role,
        granted_by_user_id=actor.id,
    )
    session.add(grant)
    await session.flush()
    await session.refresh(grant)

    # Phase-0 convenience: sharing a demo session with a user also invites them
    # to the backing room as a member (so room auth works as expected).
    if resource_type == "demo_session" and grant_in.subject_type == "user":
        demo_session = await session.get(DemoSession, resource_id)
        if demo_session:
            await add_participant(
                room_id=demo_session.room_id,
                user_id=actor.id,
                participant_id=str(grant_in.subject_id),
                participant_type="user",
                role="member",
                session=session,
            )
    return grant


async def revoke_access_grant(
    session: AsyncSession,
    *,
    actor: User,
    resource_type: str,
    resource_id: UUID,
    revoke_in: AccessGrantRevokeRequest,
) -> None:
    await _require_owner_or_superuser(
        session, actor=actor, resource_type=resource_type, resource_id=resource_id
    )
    stmt = select(AccessGrant).where(
        AccessGrant.resource_type == resource_type,
        AccessGrant.resource_id == resource_id,
        AccessGrant.subject_type == revoke_in.subject_type,
        AccessGrant.subject_id == revoke_in.subject_id,
    )
    grant = (await session.exec(stmt)).one_or_none()
    if not grant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")

    if resource_type == "demo_session" and revoke_in.subject_type == "user":
        demo_session = await session.get(DemoSession, resource_id)
        if demo_session:
            # Best-effort: revoke also removes room membership (soft delete) for direct user grants.
            await remove_participant(
                room_id=demo_session.room_id,
                user_id=actor.id,
                participant_id=str(revoke_in.subject_id),
                session=session,
            )
    await session.delete(grant)
