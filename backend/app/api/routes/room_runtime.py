from typing import Any
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import (
    advance_room_runtime,
    get_room_runtime,
    reset_room_runtime,
    rewind_room_runtime,
    start_room_runtime,
)
from app.models import (
    RoomRuntimeAdvanceRequest,
    RoomRuntimePublic,
    RoomRuntimeResetRequest,
    RoomRuntimeRewindRequest,
    RoomRuntimeStartRequest,
)

router = APIRouter(prefix="/rooms", tags=["room-runtime"])


@router.get("/{room_id}/runtime", response_model=RoomRuntimePublic)
async def read_room_runtime(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Read the room's shared runtime projection (Surface 1, read-only).

    This endpoint is the UI-friendly "current story run state" for a room.
    """
    return await get_room_runtime(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )


@router.put("/{room_id}/runtime", response_model=RoomRuntimePublic)
async def put_room_runtime(
    *,
    room_id: UUID,
    runtime_in: RoomRuntimeStartRequest,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Initialize (or restart) the room's shared story run (Surface 1).

    Branching semantics:
    - Always creates a new underlying progress record
    - Points the room's active progress at the new branch
    """
    return await start_room_runtime(
        room_id=room_id,
        user_id=current_user.id,
        req=runtime_in,
        session=session,
    )


@router.post("/{room_id}/runtime/advance", response_model=RoomRuntimePublic)
async def advance_room_runtime_route(
    *,
    room_id: UUID,
    advance_in: RoomRuntimeAdvanceRequest,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Advance the room's shared story run by applying a choice.
    """
    return await advance_room_runtime(
        room_id=room_id,
        user_id=current_user.id,
        req=advance_in,
        session=session,
    )


@router.post("/{room_id}/runtime/rewind", response_model=RoomRuntimePublic)
async def rewind_room_runtime_route(
    *,
    room_id: UUID,
    rewind_in: RoomRuntimeRewindRequest,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Rewind the room's shared story run by branching to a prior choice.
    """
    return await rewind_room_runtime(
        room_id=room_id,
        user_id=current_user.id,
        req=rewind_in,
        session=session,
    )


@router.post("/{room_id}/runtime/reset", response_model=RoomRuntimePublic)
async def reset_room_runtime_route(
    *,
    room_id: UUID,
    reset_in: RoomRuntimeResetRequest,
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Reset the room's shared story run by branching to a new start state.
    """
    return await reset_room_runtime(
        room_id=room_id,
        user_id=current_user.id,
        req=reset_in,
        session=session,
    )
