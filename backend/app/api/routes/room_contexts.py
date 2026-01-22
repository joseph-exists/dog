import logging
from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter, Query

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import (
    add_room_context_item,
    delete_room_context_item,
    list_room_context_items,
    upsert_room_context_item,
)
from app.models import RoomContextItemCreate, RoomContextItemPublic, RoomContextItemsPublic

router = APIRouter(prefix="/rooms", tags=["room-contexts"])
logger = logging.getLogger(__name__)


@router.get("/{room_id}/contexts", response_model=RoomContextItemsPublic)
async def list_room_contexts(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
    agent_slug: str | None = Query(default=None),
) -> Any:
    logger.debug(
        "Room contexts list room_id=%s user_id=%s agent_slug=%s",
        room_id,
        current_user.id,
        agent_slug,
    )
    return await list_room_context_items(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
        agent_slug=agent_slug,
    )


@router.post("/{room_id}/contexts", response_model=RoomContextItemPublic)
async def create_room_context(
    *,
    room_id: UUID,
    context_in: RoomContextItemCreate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    replace_by_type: bool = Query(default=False),
) -> Any:
    logger.info(
        "Room context create room_id=%s user_id=%s context_type=%s agent_slug=%s replace_by_type=%s",
        room_id,
        current_user.id,
        context_in.context_type,
        context_in.agent_slug,
        replace_by_type,
    )
    if replace_by_type:
        context_id = str(uuid4())
        return await upsert_room_context_item(
            room_id=room_id,
            user_id=current_user.id,
            context_id=context_id,
            context_in=context_in,
            replace_by_type=True,
            session=session,
        )
    return await add_room_context_item(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
        context_in=context_in,
    )


@router.delete("/{room_id}/contexts/{context_id}")
async def delete_room_context(
    *,
    room_id: UUID,
    context_id: str,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    logger.info(
        "Room context delete room_id=%s user_id=%s context_id=%s",
        room_id,
        current_user.id,
        context_id,
    )
    await delete_room_context_item(
        room_id=room_id,
        user_id=current_user.id,
        context_id=context_id,
        session=session,
    )
    return {"status": "ok"}


@router.put("/{room_id}/contexts/{context_id}", response_model=RoomContextItemPublic)
async def upsert_room_context(
    *,
    room_id: UUID,
    context_id: str,
    context_in: RoomContextItemCreate,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    replace_by_type: bool = Query(default=False),
) -> Any:
    logger.info(
        "Room context upsert room_id=%s user_id=%s context_id=%s context_type=%s agent_slug=%s replace_by_type=%s",
        room_id,
        current_user.id,
        context_id,
        context_in.context_type,
        context_in.agent_slug,
        replace_by_type,
    )
    return await upsert_room_context_item(
        room_id=room_id,
        user_id=current_user.id,
        context_id=context_id,
        context_in=context_in,
        replace_by_type=replace_by_type,
        session=session,
    )
