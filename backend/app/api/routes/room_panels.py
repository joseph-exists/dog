"""
API routes for room panel configuration.

Follows the async pattern used by other room routes.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud import check_room_owner
from app.crud_panels import (
    get_room_panel_defaults,
    get_user_room_panel_config,
    resolve_panels_for_user,
    set_room_panel_defaults,
    set_user_room_panel_config,
)
from app.models import (
    ResolvedPanelConfig,
    Room,
    RoomPanelDefaultsPublic,
    UserRoomPanelConfigPublic,
)

router = APIRouter()


@router.get("/{room_id}/panels", response_model=ResolvedPanelConfig)
async def get_resolved_panels(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get resolved panel configuration for current user.
    Returns the effective panels based on user override or room/type defaults.
    """
    # Verify room exists
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    panels, source = await resolve_panels_for_user(session, current_user.id, room_id)
    return ResolvedPanelConfig(panels=panels, source=source)


@router.get("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic | None)
async def get_room_defaults(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get room's default panel configuration (set by owner)."""
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return await get_room_panel_defaults(session, room_id)


@router.put("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic)
async def update_room_defaults(
    room_id: UUID,
    panels: list[dict],
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Update room's default panel configuration.
    Only room owner can modify.
    """
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check ownership - check_room_owner returns bool
    is_owner = await check_room_owner(
        room_id=room_id,
        user_id=current_user.id,
        session=session,
    )
    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room owner can set default panels",
        )

    return await set_room_panel_defaults(session, room_id, panels)


@router.get("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic | None)
async def get_my_panel_config(
    room_id: UUID,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get current user's panel configuration override for this room."""
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return await get_user_room_panel_config(session, current_user.id, room_id)


@router.put("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic)
async def update_my_panel_config(
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update current user's panel configuration for this room."""
    room = await session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return await set_user_room_panel_config(
        session, current_user.id, room_id, panels, use_room_defaults
    )
