from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud import check_room_membership, check_room_owner
from app.models import (
    AgentInvocation,
    AgentInvocationPublic,
    AgentInvocationsPublic,
    AgentInvocationSummaryPublic,
)

router = APIRouter(prefix="/rooms", tags=["agent-invocations"])


def _public_invocation(
    invocation: AgentInvocation,
    *,
    include_full_prompt: bool,
) -> AgentInvocationPublic:
    data = AgentInvocationPublic.model_validate(invocation)
    if not include_full_prompt:
        data.full_prompt = None
    return data


@router.get("/{room_id}/agent-invocations", response_model=AgentInvocationsPublic)
async def list_agent_invocations(
    *,
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    limit: int = Query(default=20, ge=1, le=100),
) -> Any:
    if not await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    ):
        raise HTTPException(status_code=403, detail="Not a room member")

    result = await session.exec(
        select(AgentInvocation)
        .where(AgentInvocation.room_id == room_id)
        .order_by(AgentInvocation.started_at.desc())
        .limit(limit)
    )
    invocations = list(result.all())
    return AgentInvocationsPublic(
        data=[AgentInvocationSummaryPublic.model_validate(item) for item in invocations],
        count=len(invocations),
    )


@router.get(
    "/{room_id}/agent-invocations/{invocation_id}",
    response_model=AgentInvocationPublic,
)
async def get_agent_invocation(
    *,
    room_id: UUID,
    invocation_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    if not await check_room_membership(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    ):
        raise HTTPException(status_code=403, detail="Not a room member")

    invocation = await session.get(AgentInvocation, invocation_id)
    if invocation is None or invocation.room_id != room_id:
        raise HTTPException(status_code=404, detail="Agent invocation not found")

    include_full_prompt = await check_room_owner(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    return _public_invocation(invocation, include_full_prompt=include_full_prompt)
