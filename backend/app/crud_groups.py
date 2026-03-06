"""
CRUD operations for user groups (Phase 0).

Groups are user-owned collections that can be used as share targets.
Phase-0 constraint: only the group owner manages membership.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import UserGroup, UserGroupCreate, UserGroupMembership, UserGroupMembershipRole


async def create_group(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_in: UserGroupCreate,
) -> UserGroup:
    group = UserGroup(owner_id=owner_id, name=group_in.name)
    session.add(group)
    await session.flush()
    await session.refresh(group)
    return group


async def list_groups_for_owner(
    session: AsyncSession,
    *,
    owner_id: UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[UserGroup], int]:
    statement = (
        select(UserGroup)
        .where(UserGroup.owner_id == owner_id)
        .order_by(UserGroup.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    groups = list((await session.exec(statement)).all())

    count_stmt = select(func.count()).select_from(UserGroup).where(UserGroup.owner_id == owner_id)
    count = (await session.exec(count_stmt)).one()
    return groups, int(count)


async def get_group_owned_by_user(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_id: UUID,
) -> UserGroup | None:
    group = await session.get(UserGroup, group_id)
    if not group:
        return None
    if group.owner_id != owner_id:
        return None
    return group


async def delete_group(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_id: UUID,
) -> None:
    group = await get_group_owned_by_user(session, owner_id=owner_id, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    await session.delete(group)


async def list_group_memberships(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_id: UUID,
) -> list[UserGroupMembership]:
    group = await get_group_owned_by_user(session, owner_id=owner_id, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    statement = (
        select(UserGroupMembership)
        .where(UserGroupMembership.group_id == group_id)
        .order_by(UserGroupMembership.created_at.desc())
    )
    return list((await session.exec(statement)).all())


async def upsert_group_member(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_id: UUID,
    user_id: UUID,
    role: UserGroupMembershipRole = UserGroupMembershipRole.member,
) -> UserGroupMembership:
    group = await get_group_owned_by_user(session, owner_id=owner_id, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    existing_stmt = select(UserGroupMembership).where(
        UserGroupMembership.group_id == group_id,
        UserGroupMembership.user_id == user_id,
    )
    existing = (await session.exec(existing_stmt)).one_or_none()
    if existing:
        existing.role = role
        session.add(existing)
        await session.flush()
        await session.refresh(existing)
        return existing

    membership = UserGroupMembership(group_id=group_id, user_id=user_id, role=role)
    session.add(membership)
    await session.flush()
    await session.refresh(membership)
    return membership


async def remove_group_member(
    session: AsyncSession,
    *,
    owner_id: UUID,
    group_id: UUID,
    user_id: UUID,
) -> None:
    group = await get_group_owned_by_user(session, owner_id=owner_id, group_id=group_id)
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")

    stmt = select(UserGroupMembership).where(
        UserGroupMembership.group_id == group_id,
        UserGroupMembership.user_id == user_id,
    )
    membership = (await session.exec(stmt)).one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membership not found")
    await session.delete(membership)

