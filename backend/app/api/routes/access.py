from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud_access import (
    get_effective_access_role,
    list_access_grants,
    revoke_access_grant,
    upsert_access_grant,
)
from app.models import (
    AccessEffectiveRolePublic,
    AccessGrantPublic,
    AccessGrantRevokeRequest,
    AccessGrantsPublic,
    AccessGrantUpsertRequest,
    Message,
)

router = APIRouter(prefix="/access", tags=["access"])


@router.get("/{resource_type}/{resource_id}/me", response_model=AccessEffectiveRolePublic)
async def get_my_effective_resource_role(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    resource_type: str,
    resource_id: UUID,
) -> Any:
    role = await get_effective_access_role(
        session,
        actor=current_user,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return AccessEffectiveRolePublic(
        resource_type=resource_type,
        resource_id=resource_id,
        role=role,
    )


@router.get("/{resource_type}/{resource_id}", response_model=AccessGrantsPublic)
async def list_resource_access_grants(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    resource_type: str,
    resource_id: UUID,
) -> Any:
    grants = await list_access_grants(
        session,
        actor=current_user,
        resource_type=resource_type,
        resource_id=resource_id,
    )
    return AccessGrantsPublic(
        data=[AccessGrantPublic.model_validate(g) for g in grants],
        count=len(grants),
    )


@router.post("/{resource_type}/{resource_id}", response_model=AccessGrantPublic)
async def upsert_resource_access_grant(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    resource_type: str,
    resource_id: UUID,
    grant_in: AccessGrantUpsertRequest,
) -> Any:
    grant = await upsert_access_grant(
        session,
        actor=current_user,
        resource_type=resource_type,
        resource_id=resource_id,
        grant_in=grant_in,
    )
    return AccessGrantPublic.model_validate(grant)


@router.delete("/{resource_type}/{resource_id}", response_model=Message)
async def revoke_resource_access_grant(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    resource_type: str,
    resource_id: UUID,
    revoke_in: AccessGrantRevokeRequest,
) -> Any:
    await revoke_access_grant(
        session,
        actor=current_user,
        resource_type=resource_type,
        resource_id=resource_id,
        revoke_in=revoke_in,
    )
    return Message(message="Grant revoked")
