"""
API routes for DemoConfig and DemoSession.

Provides:
- Demo template config CRUD
- Per-user demo session lifecycle
- Slug-based get-or-create session resolution for /demo/{slug}
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import AsyncSessionDep, AsyncSessionTransactionDep, CurrentUser
from app.crud import create_room
from app.crud_demo import (
    build_resolve_demo_entry_payload,
    create_demo_config,
    create_demo_session,
    delete_demo_config,
    delete_demo_session,
    get_demo_page_composition_by_demo_config_id,
    get_or_create_demo_page_composition,
    get_or_create_demo_session_by_slug,
    patch_demo_page_composition,
    get_demo_config_by_id,
    get_demo_config_by_slug_visible_to_user,
    get_demo_config_visible_to_user,
    get_demo_session_by_id,
    get_demo_session_for_user,
    list_demo_configs,
    list_demo_sessions_for_user,
    put_demo_page_composition,
    resolve_demo_story_id_for_user,
    touch_demo_session,
    update_demo_config,
    update_demo_session,
)
from app.models import (
    DemoConfigCreate,
    DemoConfigPublic,
    DemoConfigsPublic,
    DemoConfigScope,
    DemoConfigUpdate,
    DemoPageCompositionBase,
    DemoPageCompositionPublic,
    DemoPageCompositionUpdate,
    DemoSessionCreate,
    DemoSessionPublic,
    DemoSessionsPublic,
    DemoSessionStatus,
    DemoSessionUpdate,
    Message,
    ResolveDemoEntryPayload,
)

router = APIRouter()


# =============================================================================
# DemoConfig Endpoints
# =============================================================================


@router.get("/", response_model=DemoConfigsPublic)
async def list_all_demo_configs(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    scope: DemoConfigScope | None = None,
    include_system: bool = True,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List demo configs visible to the current user."""
    configs, count = await list_demo_configs(
        session,
        user_id=current_user.id,
        scope=scope,
        include_system=include_system,
        include_inactive=include_inactive,
        skip=skip,
        limit=limit,
    )
    return DemoConfigsPublic(
        data=[DemoConfigPublic.model_validate(c) for c in configs],
        count=count,
    )


@router.get("/configs/{demo_config_id}", response_model=DemoConfigPublic)
async def get_demo_config(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
) -> Any:
    """Get a demo config by ID if visible to current user."""
    config = await get_demo_config_visible_to_user(
        session, demo_config_id, current_user.id
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo config not found",
        )
    return DemoConfigPublic.model_validate(config)


@router.post("/", response_model=DemoConfigPublic, status_code=status.HTTP_201_CREATED)
async def create_new_demo_config(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_in: DemoConfigCreate,
) -> Any:
    """Create a new demo config."""
    # Scope policy mirrors theme-style guardrails.
    if demo_config_in.scope == DemoConfigScope.system and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can create system demo configs",
        )

    owner_id = None if demo_config_in.scope == DemoConfigScope.system else current_user.id
    config = await create_demo_config(
        session,
        owner_id=owner_id,
        demo_config_in=demo_config_in,
    )
    return DemoConfigPublic.model_validate(config)


@router.patch("/configs/{demo_config_id}", response_model=DemoConfigPublic)
async def update_existing_demo_config(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    demo_config_update: DemoConfigUpdate,
) -> Any:
    """Update an existing demo config."""
    config = await get_demo_config_by_id(session, demo_config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo config not found",
        )

    # System configs are restricted to superusers.
    if config.scope == DemoConfigScope.system and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system demo config",
        )

    # Non-system configs: owner or superuser only.
    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only demo config owner can update",
        )

    # Prevent non-superusers from promoting to system scope.
    if (
        demo_config_update.scope == DemoConfigScope.system
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change scope to system",
        )

    updated = await update_demo_config(session, config, demo_config_update)
    return DemoConfigPublic.model_validate(updated)


@router.delete("/configs/{demo_config_id}")
async def delete_existing_demo_config(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
) -> Message:
    """Delete a demo config."""
    config = await get_demo_config_by_id(session, demo_config_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo config not found",
        )

    if config.scope == DemoConfigScope.system and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system demo config",
        )

    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only demo config owner can delete",
        )

    await delete_demo_config(session, config)
    return Message(message="Demo config deleted successfully")


# =============================================================================
# DemoComposition Endpoints
# =============================================================================


@router.get("/configs/{demo_config_id}/composition", response_model=DemoPageCompositionPublic)
async def get_demo_composition(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
) -> Any:
    config = await get_demo_config_visible_to_user(session, demo_config_id, current_user.id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo config not found")

    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    comp, _ = await get_or_create_demo_page_composition(
        session,
        demo_config=config,
        owner_id=(config.owner_id or current_user.id),
    )
    return DemoPageCompositionPublic.model_validate(comp)


@router.put("/configs/{demo_config_id}/composition", response_model=DemoPageCompositionPublic)
async def put_demo_composition(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    composition_in: DemoPageCompositionBase,
) -> Any:
    config = await get_demo_config_by_id(session, demo_config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo config not found")
    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if config.scope == DemoConfigScope.system and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system demo config composition",
        )

    comp = await put_demo_page_composition(
        session,
        demo_config_id=demo_config_id,
        owner_id=(config.owner_id or current_user.id),
        composition_in=composition_in,
    )
    return DemoPageCompositionPublic.model_validate(comp)


@router.patch("/configs/{demo_config_id}/composition", response_model=DemoPageCompositionPublic)
async def patch_existing_demo_composition(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    composition_patch: DemoPageCompositionUpdate,
) -> Any:
    config = await get_demo_config_by_id(session, demo_config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo config not found")
    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if config.scope == DemoConfigScope.system and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system demo config composition",
        )

    existing = await get_demo_page_composition_by_demo_config_id(
        session,
        demo_config_id=demo_config_id,
    )
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo composition not found",
        )

    comp = await patch_demo_page_composition(
        session,
        demo_config_id=demo_config_id,
        owner_id=(config.owner_id or current_user.id),
        patch_in=composition_patch,
    )
    return DemoPageCompositionPublic.model_validate(comp)


# =============================================================================
# DemoSession Endpoints
# =============================================================================


@router.get("/sessions", response_model=DemoSessionsPublic)
async def list_my_demo_sessions(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    status_filter: DemoSessionStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List current user's demo sessions."""
    sessions, count = await list_demo_sessions_for_user(
        session,
        user_id=current_user.id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )
    return DemoSessionsPublic(
        data=[DemoSessionPublic.model_validate(s) for s in sessions],
        count=count,
    )


@router.get("/sessions/{demo_session_id}", response_model=DemoSessionPublic)
async def get_my_demo_session(
    session: AsyncSessionDep,
    current_user: CurrentUser,
    demo_session_id: UUID,
) -> Any:
    """Get a single demo session owned by current user."""
    demo_session = await get_demo_session_by_id(session, demo_session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found",
        )
    if demo_session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    return DemoSessionPublic.model_validate(demo_session)


@router.post("/sessions", response_model=DemoSessionPublic, status_code=status.HTTP_201_CREATED)
async def create_my_demo_session(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_session_in: DemoSessionCreate,
) -> Any:
    """
    Explicitly create a demo session for current user.

    If a session already exists for (user, demo_config), returns it.
    """
    config = await get_demo_config_visible_to_user(
        session, demo_session_in.demo_config_id, current_user.id
    )
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo config not found",
        )

    existing = await get_demo_session_for_user(
        session,
        user_id=current_user.id,
        demo_config_id=config.id,
    )
    if existing:
        existing = await touch_demo_session(session, existing)
        return DemoSessionPublic.model_validate(existing)

    room = await create_room(
        creator_id=current_user.id,
        story_id=await resolve_demo_story_id_for_user(
            session,
            demo_config=config,
            user_id=current_user.id,
        ),
        title=f"{config.title} Demo",
        session=session,
    )

    created = await create_demo_session(
        session,
        user_id=current_user.id,
        demo_config_id=config.id,
        room_id=room.room_id,
        page_entity_id=str(room.room_id),
        auto_respond=(
            demo_session_in.auto_respond
            if demo_session_in.auto_respond is not None
            else config.default_auto_respond
        ),
    )
    return DemoSessionPublic.model_validate(created)


@router.patch("/sessions/{demo_session_id}", response_model=DemoSessionPublic)
async def update_my_demo_session(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_session_id: UUID,
    demo_session_update: DemoSessionUpdate,
) -> Any:
    """Update current user's demo session."""
    demo_session = await get_demo_session_by_id(session, demo_session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found",
        )
    if demo_session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    updated = await update_demo_session(session, demo_session, demo_session_update)
    return DemoSessionPublic.model_validate(updated)


@router.delete("/sessions/{demo_session_id}")
async def delete_my_demo_session(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_session_id: UUID,
) -> Message:
    """Delete current user's demo session."""
    demo_session = await get_demo_session_by_id(session, demo_session_id)
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found",
        )
    if demo_session.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    await delete_demo_session(session, demo_session)
    return Message(message="Demo session deleted successfully")


@router.post("/{demo_slug}/session", response_model=ResolveDemoEntryPayload)
async def resolve_demo_session_for_slug(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_slug: str,
) -> Any:
    """
    Get-or-create current user's demo session for a slug.

    This is the primary route entrypoint for /demo/{slug}.
    """
    config = await get_demo_config_by_slug_visible_to_user(
        session,
        slug=demo_slug,
        user_id=current_user.id,
    )
    if not config or not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found",
        )

    existing = await get_demo_session_for_user(
        session,
        user_id=current_user.id,
        demo_config_id=config.id,
    )
    if existing:
        existing = await touch_demo_session(session, existing)
        return await build_resolve_demo_entry_payload(
            session,
            user_id=current_user.id,
            demo_config=config,
            demo_session=existing,
            created=False,
        )

    room = await create_room(
        creator_id=current_user.id,
        story_id=await resolve_demo_story_id_for_user(
            session,
            demo_config=config,
            user_id=current_user.id,
        ),
        title=f"{config.title} Demo",
        session=session,
    )
    resolved = await get_or_create_demo_session_by_slug(
        session,
        user_id=current_user.id,
        demo_slug=demo_slug,
        room_id=room.room_id,
        page_entity_id=str(room.room_id),
    )
    if not resolved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found",
        )
    resolved_config, resolved_session, created = resolved
    if not created:
        resolved_session = await touch_demo_session(session, resolved_session)

    return await build_resolve_demo_entry_payload(
        session,
        user_id=current_user.id,
        demo_config=resolved_config,
        demo_session=resolved_session,
        created=created,
    )
