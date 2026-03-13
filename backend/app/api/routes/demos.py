"""
API routes for DemoConfig and DemoSession.

Provides:
- Demo template config CRUD
- Per-user demo session lifecycle
- Slug-based get-or-create session resolution for /demo/{slug}
"""

from __future__ import annotations

import asyncio
import json
import logging
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
    get_accessible_demo_session_for_slug,
    get_demo_config_by_slug,
    get_demo_page_composition_by_demo_config_id,
    get_or_create_demo_page_composition,
    get_or_create_demo_session_by_slug,
    patch_demo_page_composition,
    get_demo_config_by_id,
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
from app.core.db import async_session_maker
from app.core.redis import get_redis
from app.models import (
    AccessGrantRole,
    DemoCanvasRenderJobResponse,
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
    User,
)
from app.services.access_control import require_access
from app.services.event_emitter import emit_event
from app.services.shadow_git import commit_text_file, get_repo_path, get_repo_remote_url
from app.services.tesser_service import (
    enqueue_tesser,
    get_tesser_job_status,
    TesserRenderTimeoutError,
    request_tesser,
)
from app.services.context_store import ContextItem, RedisContextStore

router = APIRouter()
logger = logging.getLogger(__name__)
_context_store = RedisContextStore()
_DEMO_CANVAS_JOB_TTL_SECONDS = 60 * 60 * 24


def _canvas_context_type(panel_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in ("-", "_", ".") else "-" for ch in panel_id)
    # Keep context_type under validation max length (100 chars) with system. prefix.
    return f"system.canvas.{safe[:80]}.svg"


def _demo_canvas_job_key(job_id: str) -> str:
    return f"demo:canvas:job:{job_id}"


def _demo_canvas_job_claim_key(job_id: str) -> str:
    return f"demo:canvas:job:{job_id}:terminal-claim"


async def _store_demo_canvas_job(job_id: str, payload: dict[str, Any]) -> None:
    redis = await get_redis()
    await redis.set(
        _demo_canvas_job_key(job_id),
        json.dumps(payload),
        ex=_DEMO_CANVAS_JOB_TTL_SECONDS,
    )


async def _load_demo_canvas_job(job_id: str) -> dict[str, Any] | None:
    redis = await get_redis()
    raw = await redis.get(_demo_canvas_job_key(job_id))
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    if not isinstance(raw, str):
        return None
    parsed = json.loads(raw)
    return parsed if isinstance(parsed, dict) else None


async def _claim_demo_canvas_job_terminal_processing(job_id: str) -> bool:
    redis = await get_redis()
    claimed = await redis.set(
        _demo_canvas_job_claim_key(job_id),
        "1",
        ex=300,
        nx=True,
    )
    return bool(claimed)


def _demo_canvas_event_payload(
    *,
    room_id: str,
    job_state: dict[str, Any],
) -> dict[str, Any]:
    return {
        "room_id": room_id,
        "demo_config_id": str(job_state.get("demo_config_id") or ""),
        "panel_id": str(job_state.get("panel_id") or ""),
        "job_id": str(job_state.get("job_id") or ""),
        "request_id": (
            str(job_state.get("request_id"))
            if job_state.get("request_id") is not None
            else None
        ),
        "script_name": (
            str(job_state.get("script_name"))
            if job_state.get("script_name") is not None
            else None
        ),
        "status": str(job_state.get("status") or "queued"),
        "runtime_profile": (
            str(job_state.get("runtime_profile"))
            if job_state.get("runtime_profile") is not None
            else None
        ),
        "resolved_capabilities": (
            list(job_state.get("resolved_capabilities"))
            if isinstance(job_state.get("resolved_capabilities"), list)
            else []
        ),
        "queued_at": (
            str(job_state.get("queued_at"))
            if job_state.get("queued_at") is not None
            else None
        ),
        "completed_at": (
            str(job_state.get("completed_at"))
            if job_state.get("completed_at") is not None
            else None
        ),
        "svg": (
            str(job_state.get("svg")) if isinstance(job_state.get("svg"), str) else None
        ),
        "persisted": bool(job_state.get("persisted")),
        "shadow_commit_sha": (
            str(job_state.get("shadow_commit_sha"))
            if job_state.get("shadow_commit_sha") is not None
            else None
        ),
        "error": (
            str(job_state.get("error")) if job_state.get("error") is not None else None
        ),
    }


async def _emit_demo_canvas_terminal_event(
    session: AsyncSessionTransactionDep,
    *,
    room_id: UUID,
    job_state: dict[str, Any],
) -> None:
    status_value = str(job_state.get("status") or "")
    if status_value == "completed":
        event_type = "room.canvas_render.completed"
    elif status_value == "error":
        event_type = "room.canvas_render.failed"
    else:
        return

    await emit_event(
        session=session,
        room_id=room_id,
        event_type=event_type,
        payload=_demo_canvas_event_payload(room_id=str(room_id), job_state=job_state),
    )


async def _prepare_demo_canvas_render_for_actor(
    session: AsyncSessionTransactionDep,
    actor_user: User,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
) -> tuple[Any, Any, DemoPageCompositionBase, Any, dict[str, Any], str]:
    config = await get_demo_config_by_id(session, demo_config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demo config not found")
    if (
        config.scope != DemoConfigScope.system
        and config.owner_id != actor_user.id
        and not actor_user.is_superuser
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if config.scope == DemoConfigScope.system and not actor_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system demo config composition",
        )
    demo_session = await get_demo_session_for_user(
        session,
        user_id=actor_user.id,
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
        owner_id=(config.owner_id or actor_user.id),
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

    return config, demo_session, composition, selected_panel, script_input, room_id


async def _prepare_demo_canvas_render(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
) -> tuple[Any, Any, DemoPageCompositionBase, Any, dict[str, Any], str]:
    return await _prepare_demo_canvas_render_for_actor(
        session,
        current_user,
        demo_config_id,
        payload,
    )


async def _finalize_demo_canvas_render_for_actor(
    session: AsyncSessionTransactionDep,
    actor_user: User,
    *,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
    render_response: dict[str, Any],
) -> tuple[DemoCanvasRenderResponse, Any]:
    config, demo_session, composition, selected_panel, _, _ = await _prepare_demo_canvas_render_for_actor(
        session,
        actor_user,
        demo_config_id,
        payload,
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
            owner_id=(config.owner_id or actor_user.id),
            composition_in=composition,
        )
        persisted = True

    context_type = _canvas_context_type(selected_panel.id)
    context_id = f"canvas:{demo_session.room_id}:{selected_panel.id}"
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

    return (
        DemoCanvasRenderResponse(
            demo_config_id=demo_config_id,
            panel_id=selected_panel.id,
            request_id=render_response.get("request_id"),
            status=str(render_response.get("status") or "completed"),
            svg=svg,
            persisted=persisted,
            shadow_commit_sha=shadow_commit_sha,
        ),
        demo_session,
    )


async def _finalize_demo_canvas_render(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    *,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
    render_response: dict[str, Any],
) -> DemoCanvasRenderResponse:
    response, _ = await _finalize_demo_canvas_render_for_actor(
        session,
        current_user,
        demo_config_id=demo_config_id,
        payload=payload,
        render_response=render_response,
    )
    return response


async def process_demo_canvas_tesser_callback(callback_payload: dict[str, Any]) -> None:
    request_id = callback_payload.get("request_id")
    job_id = str(request_id) if request_id is not None else ""
    if not job_id:
        return

    job_state = await _load_demo_canvas_job(job_id)
    if not job_state or bool(job_state.get("terminal")):
        return
    if not await _claim_demo_canvas_job_terminal_processing(job_id):
        return

    demo_config_id_raw = job_state.get("demo_config_id")
    user_id_raw = job_state.get("user_id")
    if not isinstance(demo_config_id_raw, str) or not isinstance(user_id_raw, str):
        return

    payload = DemoCanvasRenderRequest.model_validate(job_state.get("payload") or {})

    async with async_session_maker() as session:
        async with session.begin():
            actor_user = await session.get(User, UUID(user_id_raw))
            if actor_user is None:
                job_state.update(
                    {
                        "terminal": True,
                        "status": "error",
                        "error": f"User '{user_id_raw}' not found for canvas render job",
                        "completed_at": (
                            str(callback_payload.get("completed_at"))
                            if callback_payload.get("completed_at") is not None
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    }
                )
            elif str(callback_payload.get("status") or "") == "error":
                job_state.update(
                    {
                        "terminal": True,
                        "status": "error",
                        "error": (
                            str(callback_payload.get("error"))
                            if callback_payload.get("error") is not None
                            else "Canvas render failed"
                        ),
                        "completed_at": (
                            str(callback_payload.get("completed_at"))
                            if callback_payload.get("completed_at") is not None
                            else datetime.now(timezone.utc).isoformat()
                        ),
                    }
                )
            else:
                final_response, demo_session = await _finalize_demo_canvas_render_for_actor(
                    session,
                    actor_user,
                    demo_config_id=UUID(demo_config_id_raw),
                    payload=payload,
                    render_response=callback_payload,
                )
                job_state.update(
                    {
                        "terminal": True,
                        "status": final_response.status,
                        "svg": final_response.svg,
                        "persisted": final_response.persisted,
                        "shadow_commit_sha": final_response.shadow_commit_sha,
                        "error": None,
                        "completed_at": (
                            str(callback_payload.get("completed_at"))
                            if callback_payload.get("completed_at") is not None
                            else job_state.get("completed_at")
                        ),
                    }
                )
                await _emit_demo_canvas_terminal_event(
                    session,
                    room_id=demo_session.room_id,
                    job_state=job_state,
                )
                await _store_demo_canvas_job(job_id, job_state)
                return

            room_id_value = job_state.get("room_id")
            if isinstance(room_id_value, str) and room_id_value:
                await _emit_demo_canvas_terminal_event(
                    session,
                    room_id=UUID(room_id_value),
                    job_state=job_state,
                )

    await _store_demo_canvas_job(job_id, job_state)


async def run_demo_canvas_tesser_callback_listener(stop_event: asyncio.Event) -> None:
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.TESSER_DEMO_CANVAS_CALLBACK_CHANNEL)
    try:
        while not stop_event.is_set():
            message = await pubsub.get_message(
                ignore_subscribe_messages=True,
                timeout=1.0,
            )
            if not message:
                continue

            raw_data = message.get("data")
            if isinstance(raw_data, bytes):
                raw_data = raw_data.decode()
            if not isinstance(raw_data, str):
                continue

            try:
                parsed = json.loads(raw_data)
            except json.JSONDecodeError:
                continue
            if not isinstance(parsed, dict):
                continue
            try:
                await process_demo_canvas_tesser_callback(parsed)
            except Exception:
                logger.exception("Failed to process demo canvas tesser callback")
    finally:
        await pubsub.unsubscribe(settings.TESSER_DEMO_CANVAS_CALLBACK_CHANNEL)
        await pubsub.close()


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
    _, _, _, _, script_input, room_id = await _prepare_demo_canvas_render(
        session,
        current_user,
        demo_config_id,
        payload,
    )

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
    return await _finalize_demo_canvas_render(
        session,
        current_user,
        demo_config_id=demo_config_id,
        payload=payload,
        render_response=render_response,
    )


@router.post(
    "/configs/{demo_config_id}/canvas/render/enqueue",
    response_model=DemoCanvasRenderJobResponse,
)
async def enqueue_demo_canvas_panel_render(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    payload: DemoCanvasRenderRequest,
) -> Any:
    _, _, _, selected_panel, script_input, room_id = await _prepare_demo_canvas_render(
        session,
        current_user,
        demo_config_id,
        payload,
    )

    try:
        enqueue_response = await enqueue_tesser(
            script_name=payload.script_name,
            script_input=script_input,
            room_id=room_id,
            callback={
                "kind": "redis",
                "response_channel": settings.TESSER_DEMO_CANVAS_CALLBACK_CHANNEL,
            },
        )
    except TesserRenderTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=str(exc),
        ) from exc
    if str(enqueue_response.get("status") or "") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=enqueue_response.get("error")
            or f"Tesser failed to enqueue script '{payload.script_name}'",
        )

    job_id = str(
        enqueue_response.get("job_id") or enqueue_response.get("request_id") or ""
    )
    if not job_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Tesser enqueue response missing job_id",
        )

    job_state = {
        "demo_config_id": str(demo_config_id),
        "panel_id": selected_panel.id,
        "job_id": job_id,
        "request_id": (
            str(enqueue_response.get("request_id"))
            if enqueue_response.get("request_id") is not None
            else None
        ),
        "script_name": payload.script_name,
        "status": str(enqueue_response.get("status") or "queued"),
        "runtime_profile": (
            str(enqueue_response.get("runtime_profile"))
            if enqueue_response.get("runtime_profile") is not None
            else None
        ),
        "resolved_capabilities": (
            list(enqueue_response.get("resolved_capabilities"))
            if isinstance(enqueue_response.get("resolved_capabilities"), list)
            else []
        ),
        "queued_at": (
            str(enqueue_response.get("queued_at"))
            if enqueue_response.get("queued_at") is not None
            else None
        ),
        "payload": payload.model_dump(),
        "room_id": room_id,
        "user_id": str(current_user.id),
        "terminal": False,
        "persisted": False,
        "shadow_commit_sha": None,
        "svg": None,
        "error": None,
        "completed_at": None,
    }

    if job_state["status"] == "completed":
        final_response, demo_session = await _finalize_demo_canvas_render_for_actor(
            session,
            current_user,
            demo_config_id=demo_config_id,
            payload=payload,
            render_response=enqueue_response,
        )
        job_state.update(
            {
                "terminal": True,
                "status": final_response.status,
                "svg": final_response.svg,
                "persisted": final_response.persisted,
                "shadow_commit_sha": final_response.shadow_commit_sha,
                "completed_at": enqueue_response.get("completed_at"),
            }
        )
        await _emit_demo_canvas_terminal_event(
            session,
            room_id=demo_session.room_id,
            job_state=job_state,
        )

    await _store_demo_canvas_job(job_id, job_state)

    return DemoCanvasRenderJobResponse(
        demo_config_id=demo_config_id,
        panel_id=selected_panel.id,
        job_id=job_id,
        request_id=job_state["request_id"],
        script_name=payload.script_name,
        status=str(job_state["status"]),
        runtime_profile=job_state["runtime_profile"],
        resolved_capabilities=list(job_state["resolved_capabilities"]),
        queued_at=job_state["queued_at"],
        completed_at=job_state["completed_at"],
        svg=job_state["svg"],
        persisted=bool(job_state["persisted"]),
        shadow_commit_sha=job_state["shadow_commit_sha"],
        error=job_state["error"],
    )


@router.get(
    "/configs/{demo_config_id}/canvas/render/jobs/{job_id}",
    response_model=DemoCanvasRenderJobResponse,
)
async def get_demo_canvas_panel_render_job(
    session: AsyncSessionTransactionDep,
    current_user: CurrentUser,
    demo_config_id: UUID,
    job_id: str,
) -> Any:
    job_state = await _load_demo_canvas_job(job_id)
    if not job_state or job_state.get("demo_config_id") != str(demo_config_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Canvas render job '{job_id}' not found",
        )

    payload = DemoCanvasRenderRequest.model_validate(job_state.get("payload") or {})
    await _prepare_demo_canvas_render(
        session,
        current_user,
        demo_config_id,
        payload,
    )

    if not job_state.get("terminal"):
        try:
            tesser_status = await get_tesser_job_status(job_id=job_id)
        except TesserRenderTimeoutError as exc:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=str(exc),
            ) from exc

        tesser_state = str(tesser_status.get("status") or "queued")
        job_state["status"] = tesser_state
        job_state["runtime_profile"] = (
            str(tesser_status.get("runtime_profile"))
            if tesser_status.get("runtime_profile") is not None
            else job_state.get("runtime_profile")
        )
        job_state["resolved_capabilities"] = (
            list(tesser_status.get("resolved_capabilities"))
            if isinstance(tesser_status.get("resolved_capabilities"), list)
            else job_state.get("resolved_capabilities", [])
        )
        job_state["completed_at"] = (
            str(tesser_status.get("completed_at"))
            if tesser_status.get("completed_at") is not None
            else job_state.get("completed_at")
        )

        if tesser_state == "completed":
            if await _claim_demo_canvas_job_terminal_processing(job_id):
                final_response, demo_session = await _finalize_demo_canvas_render_for_actor(
                    session,
                    current_user,
                    demo_config_id=demo_config_id,
                    payload=payload,
                    render_response=tesser_status,
                )
                job_state.update(
                    {
                        "terminal": True,
                        "status": final_response.status,
                        "svg": final_response.svg,
                        "persisted": final_response.persisted,
                        "shadow_commit_sha": final_response.shadow_commit_sha,
                        "error": None,
                    }
                )
                await _emit_demo_canvas_terminal_event(
                    session,
                    room_id=demo_session.room_id,
                    job_state=job_state,
                )
            else:
                latest_job_state = await _load_demo_canvas_job(job_id)
                if latest_job_state:
                    job_state = latest_job_state
        elif tesser_state == "error":
            if await _claim_demo_canvas_job_terminal_processing(job_id):
                job_state.update(
                    {
                        "terminal": True,
                        "error": (
                            str(tesser_status.get("error"))
                            if tesser_status.get("error") is not None
                            else "Canvas render failed"
                        ),
                    }
                )
                room_id_value = job_state.get("room_id")
                if isinstance(room_id_value, str) and room_id_value:
                    await _emit_demo_canvas_terminal_event(
                        session,
                        room_id=UUID(room_id_value),
                        job_state=job_state,
                    )
            else:
                latest_job_state = await _load_demo_canvas_job(job_id)
                if latest_job_state:
                    job_state = latest_job_state
        elif tesser_state == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=tesser_status.get("error") or f"Unknown tesser job '{job_id}'",
            )

        await _store_demo_canvas_job(job_id, job_state)

    return DemoCanvasRenderJobResponse(
        demo_config_id=demo_config_id,
        panel_id=str(job_state.get("panel_id") or ""),
        job_id=job_id,
        request_id=(
            str(job_state.get("request_id"))
            if job_state.get("request_id") is not None
            else None
        ),
        script_name=(
            str(job_state.get("script_name"))
            if job_state.get("script_name") is not None
            else None
        ),
        status=str(job_state.get("status") or "queued"),
        runtime_profile=(
            str(job_state.get("runtime_profile"))
            if job_state.get("runtime_profile") is not None
            else None
        ),
        resolved_capabilities=(
            list(job_state.get("resolved_capabilities"))
            if isinstance(job_state.get("resolved_capabilities"), list)
            else []
        ),
        queued_at=(
            str(job_state.get("queued_at"))
            if job_state.get("queued_at") is not None
            else None
        ),
        completed_at=(
            str(job_state.get("completed_at"))
            if job_state.get("completed_at") is not None
            else None
        ),
        svg=(str(job_state.get("svg")) if isinstance(job_state.get("svg"), str) else None),
        persisted=bool(job_state.get("persisted")),
        shadow_commit_sha=(
            str(job_state.get("shadow_commit_sha"))
            if job_state.get("shadow_commit_sha") is not None
            else None
        ),
        error=(
            str(job_state.get("error")) if job_state.get("error") is not None else None
        ),
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
        await require_access(
            session,
            user=current_user,
            resource_type="demo_session",
            resource_id=demo_session_id,
            minimum_role=AccessGrantRole.viewer,
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
    config = await get_demo_config_by_slug(session, demo_slug)
    if not config or not config.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found",
        )

    # First: allow resolving any session the user can access (including
    # project-derived access grants on demo_session resources).
    existing = await get_accessible_demo_session_for_slug(
        session,
        viewer=current_user,
        demo_config_id=config.id,
    )
    if existing:
        if existing.user_id == current_user.id:
            existing = await touch_demo_session(session, existing)
        return await build_resolve_demo_entry_payload(
            session,
            user_id=current_user.id,
            demo_config=config,
            demo_session=existing,
            created=False,
        )

    # No accessible session exists; only users who can view this config can
    # create a new per-user session via slug resolution.
    if not await get_demo_config_visible_to_user(session, config.id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demo not found",
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
