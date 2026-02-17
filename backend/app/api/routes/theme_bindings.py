"""
API routes for Theme bindings.

Provides endpoints for user preference bindings and theme resolution.
Authored bindings are managed through entity-specific endpoints (stories, rooms).
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, CurrentUser
from app.crud_theme_bindings import (
    batch_resolve_themes,
    clear_user_pref_binding,
    get_user_bindings,
    resolve_theme,
    set_user_pref_binding,
)
from app.crud_themes import get_theme_visible_to_user
from app.models import (
    BatchResolvedThemesResponse,
    BatchResolveThemeRequest,
    EntityContext,
    ResolvedThemeResponse,
    ResolveThemeRequest,
    ThemeBinding,
    ThemeBindingCreate,
    ThemeBindingPublic,
    ThemeBindingsPublic,
    ThemeSlot,
)

router = APIRouter()


# =============================================================================
# User Preference Bindings
# =============================================================================


@router.get("/user", response_model=ThemeBindingsPublic)
async def get_my_bindings(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    context_prefix: str | None = None,
) -> Any:
    """
    Get current user's theme bindings.

    Optionally filter by context_key prefix (e.g., "page:story" to get
    all bindings for story page and its panels).
    """
    bindings = await get_user_bindings(
        session, current_user.id, context_prefix
    )
    return ThemeBindingsPublic(
        data=[ThemeBindingPublic.model_validate(b) for b in bindings],
        count=len(bindings),
    )


@router.put("/user", response_model=ThemeBindingPublic)
async def set_my_binding(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    binding_in: ThemeBindingCreate,
) -> Any:
    """
    Set a user preference binding.

    Creates or updates a binding for the specified context_key and slot.
    The theme must be visible to the user and match the slot's category.
    """
    # Validate theme exists and is visible
    theme = await get_theme_visible_to_user(
        session, binding_in.theme_id, current_user.id
    )
    if not theme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Theme not found",
        )

    # Validate theme category matches slot
    slot_to_category = {
        ThemeSlot.page: "page",
        ThemeSlot.cards: "card",
        ThemeSlot.syntax: "syntax",
        ThemeSlot.motion: "motion",
    }
    if theme.category.value != slot_to_category[binding_in.slot]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Theme category '{theme.category.value}' does not match slot '{binding_in.slot.value}'",
        )

    binding = await set_user_pref_binding(
        session,
        user_id=current_user.id,
        context_key=binding_in.context_key,
        slot=binding_in.slot,
        theme_id=binding_in.theme_id,
    )
    return ThemeBindingPublic.model_validate(binding)


@router.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
async def clear_my_binding(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    context_key: str,
    slot: ThemeSlot,
) -> None:
    """
    Clear a user preference binding.

    After clearing, resolution will fall through to less specific bindings
    or system defaults.
    """
    deleted = await clear_user_pref_binding(
        session,
        user_id=current_user.id,
        context_key=context_key,
        slot=slot,
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binding not found",
        )


# =============================================================================
# Theme Resolution
# =============================================================================


@router.get("/resolve", response_model=ResolvedThemeResponse)
async def resolve_single_theme(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    slot: ThemeSlot,
    context_path: str,  # Comma-separated, e.g., "page:story,panel:debug"
    entity_type: str | None = None,
    entity_id: UUID | None = None,
    entity_owner_id: UUID | None = None,
) -> Any:
    """
    Resolve the effective theme for a context.

    Resolution cascade:
    1. Authored bindings (if entity context provided)
    2. User preference bindings
    3. System default

    The context_path is comma-separated segments, e.g., "page:story,panel:debug"
    """
    # Parse context path
    path_segments = [s.strip() for s in context_path.split(",") if s.strip()]

    # Build entity context if provided
    entity_context = None
    if entity_type and entity_id and entity_owner_id:
        entity_context = EntityContext(
            entity_type=entity_type,
            entity_id=entity_id,
            owner_id=entity_owner_id,
        )

    return await resolve_theme(
        session,
        user_id=current_user.id,
        context_path=path_segments,
        slot=slot,
        entity_context=entity_context,
    )


@router.post("/resolve/batch", response_model=BatchResolvedThemesResponse)
async def resolve_multiple_themes(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    request: BatchResolveThemeRequest,
) -> Any:
    """
    Resolve multiple theme slots in a single request.

    More efficient than multiple single resolutions when loading a page
    that needs page, cards, syntax, and motion themes.
    """
    entity_context = None
    if request.entity_context:
        entity_context = request.entity_context

    return await batch_resolve_themes(
        session,
        user_id=current_user.id,
        context_path=request.context_path,
        slots=request.slots,
        entity_context=entity_context,
    )
