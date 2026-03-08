from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud_persona_groups import (
    create_persona_group,
    delete_persona_group,
    list_persona_group_memberships,
    list_persona_groups_for_owner,
    remove_persona_group_member,
    update_persona_group_member,
    upsert_persona_group_member,
)
from app.models import (
    Message,
    PersonaGroupCreate,
    PersonaGroupMembershipCreate,
    PersonaGroupMembershipPublic,
    PersonaGroupMembershipsPublic,
    PersonaGroupMembershipUpdate,
    PersonaGroupPublic,
    PersonaGroupsPublic,
)

router = APIRouter(prefix="/persona-groups", tags=["persona-groups"])


@router.post("/", response_model=PersonaGroupPublic)
async def create_new_persona_group(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_in: PersonaGroupCreate,
) -> Any:
    group = await create_persona_group(
        session,
        owner_user_id=current_user.id,
        group_in=group_in,
    )
    return PersonaGroupPublic.model_validate(group)


@router.get("/", response_model=PersonaGroupsPublic)
async def list_persona_groups(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    groups, count = await list_persona_groups_for_owner(
        session,
        owner_user_id=current_user.id,
        skip=skip,
        limit=limit,
    )
    return PersonaGroupsPublic(
        data=[PersonaGroupPublic.model_validate(g) for g in groups],
        count=count,
    )


@router.delete("/{group_id}", response_model=Message)
async def delete_persona_group_route(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
) -> Any:
    await delete_persona_group(
        session,
        owner_user_id=current_user.id,
        group_id=group_id,
    )
    return Message(message="Persona group deleted")


@router.get("/{group_id}/members", response_model=PersonaGroupMembershipsPublic)
async def list_persona_group_members(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    group_id: UUID,
) -> Any:
    memberships = await list_persona_group_memberships(
        session,
        owner_user_id=current_user.id,
        group_id=group_id,
    )
    return PersonaGroupMembershipsPublic(
        data=[PersonaGroupMembershipPublic.model_validate(m) for m in memberships],
        count=len(memberships),
    )


@router.post("/{group_id}/members", response_model=PersonaGroupMembershipPublic)
async def add_persona_group_member(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
    member_in: PersonaGroupMembershipCreate,
) -> Any:
    membership = await upsert_persona_group_member(
        session,
        owner_user_id=current_user.id,
        group_id=group_id,
        user_persona_id=member_in.user_persona_id,
        role=member_in.role,
        is_active=member_in.is_active,
    )
    return PersonaGroupMembershipPublic.model_validate(membership)


@router.patch("/{group_id}/members/{user_persona_id}", response_model=PersonaGroupMembershipPublic)
async def patch_persona_group_member(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
    user_persona_id: UUID,
    membership_in: PersonaGroupMembershipUpdate,
) -> Any:
    membership = await update_persona_group_member(
        session,
        owner_user_id=current_user.id,
        group_id=group_id,
        user_persona_id=user_persona_id,
        membership_in=membership_in,
    )
    return PersonaGroupMembershipPublic.model_validate(membership)


@router.delete("/{group_id}/members/{user_persona_id}", response_model=Message)
async def delete_persona_group_member(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    group_id: UUID,
    user_persona_id: UUID,
) -> Any:
    await remove_persona_group_member(
        session,
        owner_user_id=current_user.id,
        group_id=group_id,
        user_persona_id=user_persona_id,
    )
    return Message(message="Persona-group member removed")
