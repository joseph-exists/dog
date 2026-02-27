"""
API routes for DemoConfig and DemoSession.

Provides:
- Demo template config CRUD
- Per-user demo session lifecycle
- Slug-based get-or-create session resolution for /demo/{slug}
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
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
from app.core.config import settings
from app.models import (
    DemoCanvasRenderRequest,
    DemoCanvasRenderResponse,
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
from app.services.shadow_git import commit_text_file, get_repo_path, get_repo_remote_url
from app.services.tesser_service import (
    TesserRenderTimeoutError,
    request_tesser,
)
from app.services.context_store import ContextItem, RedisContextStore

router = APIRouter()
_context_store = RedisContextStore()


def _canvas_context_type(panel_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "-" for ch in panel_id)
    # Keep context_type under validation max length (100 chars) with system. prefix.
    return f"system.canvas.{safe[:80]}.svg"


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


@router.post(
    "/configs/{demo_config_id}/canvas/render",
    response_model=DemoCanvasRenderResponse,
)
async def render_demo_canvas_panel(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
) -> Any:
    """
    Minimal steel-thread endpoint:
    1) request SVG from tesser via Redis channel
    2) persist SVG in selected canvas panel options.extras.render_svg
    3) optionally commit SVG to demo shadow git repo
    """
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
    demo_session = await get_demo_session_for_user(
        session,
        user_id=current_user.id,
        demo_config_id=demo_config_id,
    )
    if not demo_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo session not found for current user",
        )

    comp_row, _ = await get_or_create_demo_page_composition(
        session,
        demo_config=config,
        owner_id=(config.owner_id or current_user.id),
    )
    composition = DemoPageCompositionBase.model_validate(
        {
            "schema_version": comp_row.schema_version,
            "layout_mode": comp_row.layout_mode,
            "runtime_policy": comp_row.runtime_policy,
            "persona_policy": comp_row.persona_policy,
            "chat_mode": comp_row.chat_mode,
            "fixed_user_persona_id": comp_row.fixed_user_persona_id,
            "page_theme_id": comp_row.page_theme_id,
            "cards_theme_id": comp_row.cards_theme_id,
            "presentation_json": comp_row.presentation_json,
            "panels": comp_row.panels,
            "blocks": comp_row.blocks,
            "metadata_json": comp_row.metadata_json,
        }
    )

    canvas_panels = [panel for panel in composition.panels if panel.kind == "canvas"]
    if not canvas_panels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Composition has no canvas panel to receive SVG output",
        )

    selected_panel = None
    if payload.panel_id:
        for panel in canvas_panels:
            if panel.id == payload.panel_id:
                selected_panel = panel
                break
        if selected_panel is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Canvas panel '{payload.panel_id}' not found",
            )
    else:
        selected_panel = canvas_panels[0]

    room_id = str(demo_session.room_id)
    script_input = dict(payload.script_input or {})
    if payload.script_name in {"simple_svg", "entity_badge", "status_strip"}:
        script_input.setdefault("title", payload.title)
        if payload.subtitle is not None:
            script_input.setdefault("subtitle", payload.subtitle)
    if payload.script_name == "entity_badge":
        script_input.setdefault("entity_type", "demo")
        script_input.setdefault("entity_id", str(demo_config_id))

    try:
        render_response = await request_tesser(
            script_name=payload.script_name,
            script_input=script_input,
            room_id=room_id,
        )
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    if str(render_response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=render_response.get("error")
            or f"Tesser failed to run script '{payload.script_name}'",
        )

    svg = (
        (render_response.get("render") or {}).get("svg")
        if isinstance(render_response.get("render"), dict)
        else None
    )
    if not isinstance(svg, str) or not svg.strip():
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tesser response did not include SVG payload",
        )

    persisted = False
    if payload.persist_to_composition:
        extras = dict(getattr(selected_panel.options, "extras", {}) or {})
        extras["render_svg"] = svg
        extras["rendered_at"] = render_response.get("completed_at")
        extras["request_id"] = render_response.get("request_id")
        selected_panel.options.extras = extras

        await put_demo_page_composition(
            session,
            demo_config_id=demo_config_id,
            owner_id=(config.owner_id or current_user.id),
            composition_in=composition,
        )
        persisted = True

    # Publish rendered canvas artifact into room context so agents can see it.
    # Use one deterministic context item per canvas panel to avoid unbounded growth.
    context_type = _canvas_context_type(selected_panel.id)
    context_id = f"canvas:{room_id}:{selected_panel.id}"
    await _context_store.delete(room_id=demo_session.room_id, context_id=context_id)
    await _context_store.add(
        ContextItem(
            id=context_id,
            room_id=demo_session.room_id,
            agent_slug=None,
            context_type=context_type,
            payload={
                "panel_id": selected_panel.id,
                "script_name": payload.script_name,
                "request_id": render_response.get("request_id"),
                "rendered_at": render_response.get("completed_at"),
                "svg": svg,
            },
            source="system",
            created_at=datetime.now(timezone.utc),
            expires_at=None,
        )
    )

    shadow_commit_sha = None
    if payload.commit_to_shadow_repo:
        repo_path = get_repo_path(
            Path(settings.SHADOW_REPOS_PATH),
            "demo",
            str(demo_config_id),
        )
        repo_remote_url = get_repo_remote_url(
            settings.SHADOW_REPO_URL_TEMPLATE,
            "demo",
            str(demo_config_id),
        )
        shadow_commit_sha = await asyncio.to_thread(
            commit_text_file,
            repo_path,
            filename=f"canvas/{selected_panel.id}.svg",
            content=svg,
            message=f"Update canvas render for demo {config.slug}",
            remote_url=repo_remote_url,
            default_branch=settings.SHADOW_REPO_DEFAULT_BRANCH,
        )

    return DemoCanvasRenderResponse(
        demo_config_id=demo_config_id,
        panel_id=selected_panel.id,
        request_id=render_response.get("request_id"),
        status=render_response.get("status", "ok"),
        svg=svg,
        persisted=persisted,
        shadow_commit_sha=shadow_commit_sha,
    )


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
