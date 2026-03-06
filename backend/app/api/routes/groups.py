from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud_groups import (
    create_group,
    delete_group,
    list_group_memberships,
    list_groups_for_owner,
    remove_group_member,
    upsert_group_member,
)
from app.models import (
    Message,
    UserGroupCreate,
    UserGroupMembershipCreate,
    UserGroupMembershipPublic,
    UserGroupMembershipsPublic,
    UserGroupPublic,
    UserGroupsPublic,
)

router = APIRouter(prefix="/groups", tags=["groups"])


@router.post("/", response_model=UserGroupPublic)
async def create_user_group(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_in: UserGroupCreate,
) -> Any:
    group = await create_group(session, owner_id=current_user.id, group_in=group_in)
    return UserGroupPublic.model_validate(group)


@router.get("/", response_model=UserGroupsPublic)
async def list_user_groups(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    groups, count = await list_groups_for_owner(
        session, owner_id=current_user.id, skip=skip, limit=limit
    )
    return UserGroupsPublic(
        data=[UserGroupPublic.model_validate(g) for g in groups],
        count=count,
    )


@router.delete("/{group_id}", response_model=Message)
async def delete_user_group(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
) -> Any:
    await delete_group(session, owner_id=current_user.id, group_id=group_id)
    return Message(message="Group deleted")


@router.get("/{group_id}/members", response_model=UserGroupMembershipsPublic)
async def list_user_group_members(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    group_id: UUID,
) -> Any:
    memberships = await list_group_memberships(
        session, owner_id=current_user.id, group_id=group_id
    )
    return UserGroupMembershipsPublic(
        data=[UserGroupMembershipPublic.model_validate(m) for m in memberships],
        count=len(memberships),
    )


@router.post("/{group_id}/members", response_model=UserGroupMembershipPublic)
async def add_user_group_member(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
    member_in: UserGroupMembershipCreate,
) -> Any:
    membership = await upsert_group_member(
        session,
        owner_id=current_user.id,
        group_id=group_id,
        user_id=member_in.user_id,
        role=member_in.role,
    )
    return UserGroupMembershipPublic.model_validate(membership)


@router.delete("/{group_id}/members/{user_id}", response_model=Message)
async def delete_user_group_member(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
    user_id: UUID,
) -> Any:
    await remove_group_member(
        session,
        owner_id=current_user.id,
        group_id=group_id,
        user_id=user_id,
    )
    return Message(message="Member removed")

