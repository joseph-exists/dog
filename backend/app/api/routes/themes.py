"""
API routes for Theme registry.

Provides CRUD operations for themes with scope-based authorization.
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud_themes import (
    create_theme,
    delete_theme,
    get_theme_visible_to_user,
    list_available_themes,
    list_themes,
    update_theme,
)
from app.models import (
    ThemeCategory,
    ThemeCreate,
    ThemePublic,
    ThemeScope,
    ThemesPublic,
    ThemeUpdate,
)

router = APIRouter()


@router.get("/", response_model=ThemesPublic)
async def list_all_themes(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    category: ThemeCategory | None = None,
    scope: ThemeScope | None = None,
    include_system: bool = True,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    List all themes visible to the current user.

    Filters:
    - category: Filter by theme category (page, card, syntax, motion)
    - scope: Filter by scope (system, org, personal, shared)
    - include_system: Include system themes (default: True)
    """
    themes, count = await list_themes(
        session,
        user_id=current_user.id,
        category=category,
        scope=scope,
        include_system=include_system,
        skip=skip,
        limit=limit,
    )
    return ThemesPublic(
        data=[ThemePublic.model_validate(t) for t in themes],
        count=count,
    )


@router.get("/available", response_model=list[ThemePublic])
async def get_available_themes(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    category: ThemeCategory,
) -> Any:
    """
    List all themes available for binding in a specific category.

    This is the primary endpoint for theme pickers - returns all themes
    the user can select from for a given slot.
    """
    themes = await list_available_themes(session, current_user.id, category)
    return [ThemePublic.model_validate(t) for t in themes]


@router.get("/{theme_id}", response_model=ThemePublic)
async def get_theme(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    theme_id: UUID,
) -> Any:
    """
    Get a theme by ID.

    Returns 404 if theme doesn't exist or isn't visible to user.
    """
    theme = await get_theme_visible_to_user(session, theme_id, current_user.id)
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found",
        )
    return ThemePublic.model_validate(theme)


@router.post("/", response_model=ThemePublic, status_code=status.HTTP_201_CREATED)
async def create_new_theme(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    theme_in: ThemeCreate,
) -> Any:
    """
    Create a new theme.

    Users can create personal or shared themes.
    Only admins can create org themes (not implemented yet).
    System themes cannot be created via API.
    """
    # Validate scope
    if theme_in.scope == ThemeScope.system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create system themes via API",
        )

    if theme_in.scope == ThemeScope.org:
        # TODO: Check admin permission
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create org themes",
        )

    theme = await create_theme(
        session,
        owner_id=current_user.id,
        theme_in=theme_in,
    )
    return ThemePublic.model_validate(theme)


@router.patch("/{theme_id}", response_model=ThemePublic)
async def update_existing_theme(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    theme_id: UUID,
    theme_update: ThemeUpdate,
) -> Any:
    """
    Update an existing theme.

    Only the owner can update personal/shared themes.
    System themes cannot be updated.
    """
    theme = await get_theme_visible_to_user(session, theme_id, current_user.id)
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found",
        )

    # Cannot update system themes
    if theme.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system themes",
        )

    # Only owner can update
    if theme.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only theme owner can update",
        )

    # Cannot change scope to/from system
    if theme_update.scope == ThemeScope.system:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change scope to system",
        )

    updated = await update_theme(session, theme, theme_update)
    return ThemePublic.model_validate(updated)


@router.delete("/{theme_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_theme(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    theme_id: UUID,
) -> None:
    """
    Delete a theme.

    Only the owner can delete personal/shared themes.
    System themes cannot be deleted.
    Deleting a theme also removes all bindings to it.
    """
    theme = await get_theme_visible_to_user(session, theme_id, current_user.id)
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found",
        )

    # Cannot delete system themes
    if theme.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system themes",
        )

    # Only owner can delete
    if theme.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only theme owner can delete",
        )

    await delete_theme(session, theme)
