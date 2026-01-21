from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import (
    delete_room_agent_settings_override,
    list_room_agent_settings,
    upsert_room_agent_settings,
)
from app.models import RoomAgentSettingsBundle, RoomAgentSettingsPublic, RoomAgentSettingsUpdate

router = APIRouter(prefix="/rooms", tags=["room-agent-settings"])


@router.get("/{room_id}/agent-settings", response_model=RoomAgentSettingsBundle)
async def read_room_agent_settings(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    return await list_room_agent_settings(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )


@router.put("/{room_id}/agent-settings", response_model=RoomAgentSettingsPublic)
async def put_room_agent_settings(
    *,
    room_id: UUID,
    settings_in: RoomAgentSettingsUpdate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    return await upsert_room_agent_settings(
        room_id=room_id,
        user_id=current_user.id,
        agent_slug=None,
        settings_in=settings_in,
        session=session,
    )


@router.put(
    "/{room_id}/agents/{agent_slug}/agent-settings",
    response_model=RoomAgentSettingsPublic,
)
async def put_room_agent_settings_override(
    *,
    room_id: UUID,
    agent_slug: str,
    settings_in: RoomAgentSettingsUpdate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    return await upsert_room_agent_settings(
        room_id=room_id,
        user_id=current_user.id,
        agent_slug=agent_slug,
        settings_in=settings_in,
        session=session,
    )


@router.delete("/{room_id}/agents/{agent_slug}/agent-settings")
async def delete_room_agent_settings(
    *,
    room_id: UUID,
    agent_slug: str,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    await delete_room_agent_settings_override(
        room_id=room_id,
        user_id=current_user.id,
        agent_slug=agent_slug,
        session=session,
    )
    return {"status": "ok"}
