"""
CRUD operations for persona-mediated collaboration groups.

These coexist with the legacy user-group model.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    PersonaGroup,
    PersonaGroupCreate,
    PersonaGroupMembership,
    PersonaGroupMembershipUpdate,
    UserPersona,
    UserGroupMembershipRole,
)


async def get_owned_user_persona(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    user_persona_id: UUID,
) -> UserPersona | None:
    persona = await session.get(UserPersona, user_persona_id)
    if not persona or persona.user_id != owner_user_id:
        return None
    return persona


async def create_persona_group(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_in: PersonaGroupCreate,
) -> PersonaGroup:
    owner_persona = await get_owned_user_persona(
        session,
        owner_user_id=owner_user_id,
        user_persona_id=group_in.owner_user_persona_id,
    )
    if not owner_persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Owner user persona not found",
        )

    group = PersonaGroup.model_validate(group_in)
    session.add(group)
    await session.flush()
    await session.refresh(group)

    owner_membership = PersonaGroupMembership(
        group_id=group.id,
        user_persona_id=group.owner_user_persona_id,
        role=UserGroupMembershipRole.manager,
        is_active=True,
    )
    session.add(owner_membership)
    await session.flush()
    return group


async def list_persona_groups_for_owner(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[PersonaGroup], int]:
    owned_persona_ids_stmt = select(UserPersona.id).where(UserPersona.user_id == owner_user_id)
    owned_persona_ids = list((await session.exec(owned_persona_ids_stmt)).all())

    if not owned_persona_ids:
        return [], 0

    statement = (
        select(PersonaGroup)
        .where(PersonaGroup.owner_user_persona_id.in_(owned_persona_ids))
        .order_by(PersonaGroup.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    groups = list((await session.exec(statement)).all())

    count_stmt = (
        select(func.count())
        .select_from(PersonaGroup)
        .where(PersonaGroup.owner_user_persona_id.in_(owned_persona_ids))
    )
    count = int((await session.exec(count_stmt)).one())
    return groups, count


async def get_persona_group_owned_by_user(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
) -> PersonaGroup | None:
    group = await session.get(PersonaGroup, group_id)
    if not group:
        return None
    owner_persona = await get_owned_user_persona(
        session,
        owner_user_id=owner_user_id,
        user_persona_id=group.owner_user_persona_id,
    )
    if not owner_persona:
        return None
    return group


async def delete_persona_group(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
) -> None:
    group = await get_persona_group_owned_by_user(
        session,
        owner_user_id=owner_user_id,
        group_id=group_id,
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona group not found")
    await session.delete(group)


async def list_persona_group_memberships(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
) -> list[PersonaGroupMembership]:
    group = await get_persona_group_owned_by_user(
        session,
        owner_user_id=owner_user_id,
        group_id=group_id,
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona group not found")

    statement = (
        select(PersonaGroupMembership)
        .where(PersonaGroupMembership.group_id == group_id)
        .order_by(PersonaGroupMembership.created_at.desc())
    )
    return list((await session.exec(statement)).all())


async def upsert_persona_group_member(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
    user_persona_id: UUID,
    role: UserGroupMembershipRole = UserGroupMembershipRole.member,
    is_active: bool = True,
) -> PersonaGroupMembership:
    group = await get_persona_group_owned_by_user(
        session,
        owner_user_id=owner_user_id,
        group_id=group_id,
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona group not found")

    target_persona = await session.get(UserPersona, user_persona_id)
    if not target_persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User persona not found",
        )

    existing_stmt = select(PersonaGroupMembership).where(
        PersonaGroupMembership.group_id == group_id,
        PersonaGroupMembership.user_persona_id == user_persona_id,
    )
    existing = (await session.exec(existing_stmt)).one_or_none()
    if existing:
        existing.role = role
        existing.is_active = is_active
        session.add(existing)
        await session.flush()
        await session.refresh(existing)
        return existing

    membership = PersonaGroupMembership(
        group_id=group_id,
        user_persona_id=user_persona_id,
        role=role,
        is_active=is_active,
    )
    session.add(membership)
    await session.flush()
    await session.refresh(membership)
    return membership


async def update_persona_group_member(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
    user_persona_id: UUID,
    membership_in: PersonaGroupMembershipUpdate,
) -> PersonaGroupMembership:
    group = await get_persona_group_owned_by_user(
        session,
        owner_user_id=owner_user_id,
        group_id=group_id,
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona group not found")

    stmt = select(PersonaGroupMembership).where(
        PersonaGroupMembership.group_id == group_id,
        PersonaGroupMembership.user_persona_id == user_persona_id,
    )
    membership = (await session.exec(stmt)).one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")

    update_data = membership_in.model_dump(exclude_unset=True)
    membership.sqlmodel_update(update_data)
    session.add(membership)
    await session.flush()
    await session.refresh(membership)
    return membership


async def remove_persona_group_member(
    session: AsyncSession,
    *,
    owner_user_id: UUID,
    group_id: UUID,
    user_persona_id: UUID,
) -> None:
    group = await get_persona_group_owned_by_user(
        session,
        owner_user_id=owner_user_id,
        group_id=group_id,
    )
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona group not found")
    if group.owner_user_persona_id == user_persona_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner user persona cannot be removed from its own group",
        )

    stmt = select(PersonaGroupMembership).where(
        PersonaGroupMembership.group_id == group_id,
        PersonaGroupMembership.user_persona_id == user_persona_id,
    )
    membership = (await session.exec(stmt)).one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await session.delete(membership)
