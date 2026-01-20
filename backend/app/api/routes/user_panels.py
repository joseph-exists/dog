"""
API routes for user panel defaults.
"""

from typing import Any

from fastapi import APIRouter

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud_panels import (
    get_user_panel_defaults,
    update_user_panel_defaults,
)
from app.models import (
    UserPanelDefaultsPublic,
    UserPanelDefaultsUpdate,
)

router = APIRouter()


@router.get("/me/panel-defaults", response_model=UserPanelDefaultsPublic | None)
async def get_my_panel_defaults(
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get current user's global panel defaults."""
    return await get_user_panel_defaults(session, current_user.id)


@router.put("/me/panel-defaults", response_model=UserPanelDefaultsPublic)
async def update_my_panel_defaults(
    update_data: UserPanelDefaultsUpdate,
    session: AsyncSessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update current user's global panel defaults."""
    return await update_user_panel_defaults(
        session, current_user.id, update_data
    )
