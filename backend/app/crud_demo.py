"""
CRUD operations for DemoConfig and DemoSession.

Follows the same house style as crud_themes.py:
- explicit visibility helpers
- list + count queries
- mutation helpers that commit + refresh
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import func, or_, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.crud import get_room_runtime
from app.models import (
    DemoConfig,
    DemoConfigCreate,
    DemoCompositionSource,
    DemoConfigScope,
    DemoConfigUpdate,
    DemoPageComposition,
    DemoPageCompositionBase,
    DemoPageCompositionCreate,
    DemoPageCompositionUpdate,
    DemoPersonaPolicy,
    DemoResolvedRoomContext,
    DemoResolvedRuntimeContext,
    DemoRuntimePolicy,
    DemoSession,
    DemoSessionStatus,
    DemoSessionUpdate,
    ResolveDemoEntryPayload,
    Room,
    RoomParticipant,
    Story,
    UserDemoPageCompositionOverride,
)


# =============================================================================
# DemoConfig CRUD
# =============================================================================


async def get_demo_config_by_id(
    session: AsyncSession,
    demo_config_id: UUID,
) -> DemoConfig | None:
    """Fetch a demo config by ID."""
    return await session.get(DemoConfig, demo_config_id)


async def get_demo_config_by_slug(
    session: AsyncSession,
    slug: str,
) -> DemoConfig | None:
    """Fetch a demo config by slug."""
    statement = select(DemoConfig).where(DemoConfig.slug == slug)
    result = await session.exec(statement)
    return result.one_or_none()


async def get_demo_config_visible_to_user(
    session: AsyncSession,
    demo_config_id: UUID,
    user_id: UUID,
) -> DemoConfig | None:
    """
    Fetch a demo config by ID if visible to the user.

    Visibility rules:
    - system/shared: visible to all authenticated users
    - personal: visible only to owner
    """
    config = await session.get(DemoConfig, demo_config_id)
    if not config:
        return None

    if config.scope in (DemoConfigScope.system, DemoConfigScope.shared):
        return config

    if config.scope == DemoConfigScope.personal and config.owner_id == user_id:
        return config

    return None


async def get_demo_config_by_slug_visible_to_user(
    session: AsyncSession,
    slug: str,
    user_id: UUID,
) -> DemoConfig | None:
    """
    Fetch a demo config by slug if visible to the user.

    Visibility rules mirror get_demo_config_visible_to_user().
    """
    config = await get_demo_config_by_slug(session, slug)
    if not config:
        return None

    if config.scope in (DemoConfigScope.system, DemoConfigScope.shared):
        return config

    if config.scope == DemoConfigScope.personal and config.owner_id == user_id:
        return config

    return None


async def list_demo_configs(
    session: AsyncSession,
    *,
    user_id: UUID,
    scope: DemoConfigScope | None = None,
    include_system: bool = True,
    include_inactive: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[DemoConfig], int]:
    """
    List demo configs visible to the user with optional filters.
    """
    visibility_conditions = []
    if include_system:
        visibility_conditions.append(DemoConfig.scope == DemoConfigScope.system)

    visibility_conditions.append(DemoConfig.scope == DemoConfigScope.shared)
    visibility_conditions.append(
        (DemoConfig.scope == DemoConfigScope.personal)
        & (DemoConfig.owner_id == user_id)
    )

    filters = [or_(*visibility_conditions)]

    if scope:
        filters.append(DemoConfig.scope == scope)
    if not include_inactive:
        filters.append(DemoConfig.is_active == True)

    statement = (
        select(DemoConfig)
        .where(*filters)
        .order_by(DemoConfig.title)
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    configs = list(result.all())

    count_statement = select(func.count()).select_from(DemoConfig).where(*filters)
    count_result = await session.exec(count_statement)
    count = count_result.one()

    return configs, count


async def create_demo_config(
    session: AsyncSession,
    *,
    owner_id: UUID | None,
    demo_config_in: DemoConfigCreate,
) -> DemoConfig:
    """
    Create a demo config.

    Caller is responsible for authorization policy:
    - personal/shared generally require owner_id
    - system generally uses owner_id=None
    """
    config = DemoConfig(
        slug=demo_config_in.slug,
        title=demo_config_in.title,
        description=demo_config_in.description,
        scope=demo_config_in.scope,
        is_active=demo_config_in.is_active,
        default_auto_respond=demo_config_in.default_auto_respond,
        default_panels_json=demo_config_in.default_panels_json,
        default_layout_json=demo_config_in.default_layout_json,
        metadata_json=demo_config_in.metadata_json,
        owner_id=owner_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(config)
    await session.flush()
    await session.refresh(config)
    return config


async def update_demo_config(
    session: AsyncSession,
    config: DemoConfig,
    demo_config_update: DemoConfigUpdate,
) -> DemoConfig:
    """Update an existing demo config."""
    update_data = demo_config_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)

    config.updated_at = datetime.utcnow()
    session.add(config)
    await session.flush()
    await session.refresh(config)
    return config


async def delete_demo_config(
    session: AsyncSession,
    config: DemoConfig,
) -> None:
    """
    Delete a demo config.

    Note: associated demo sessions are cascade-deleted via ORM relationship.
    """
    await session.delete(config)


# =============================================================================
# DemoSession CRUD
# =============================================================================


async def get_demo_session_by_id(
    session: AsyncSession,
    demo_session_id: UUID,
) -> DemoSession | None:
    """Fetch a demo session by ID."""
    return await session.get(DemoSession, demo_session_id)


async def get_demo_session_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    demo_config_id: UUID,
) -> DemoSession | None:
    """
    Fetch a user's demo session for a config.
    """
    statement = select(DemoSession).where(
        DemoSession.user_id == user_id,
        DemoSession.demo_config_id == demo_config_id,
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def list_demo_sessions_for_user(
    session: AsyncSession,
    *,
    user_id: UUID,
    status: DemoSessionStatus | None = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[DemoSession], int]:
    """
    List demo sessions for the current user.
    """
    filters = [DemoSession.user_id == user_id]
    if status:
        filters.append(DemoSession.status == status)

    statement = (
        select(DemoSession)
        .where(*filters)
        .order_by(DemoSession.last_accessed_at.desc())
        .offset(skip)
        .limit(limit)
    )
    result = await session.exec(statement)
    sessions = list(result.all())

    count_statement = select(func.count()).select_from(DemoSession).where(*filters)
    count_result = await session.exec(count_statement)
    count = count_result.one()
    return sessions, count


async def create_demo_session(
    session: AsyncSession,
    *,
    user_id: UUID,
    demo_config_id: UUID,
    room_id: UUID,
    page_entity_id: str,
    page_entity_type: str = "demo",
    auto_respond: bool = True,
    status: DemoSessionStatus = DemoSessionStatus.active,
) -> DemoSession:
    """
    Create a new demo session.

    Caller is responsible for:
    - visibility/authorization checks on demo_config
    - creating/providing room_id
    """
    demo_session = DemoSession(
        user_id=user_id,
        demo_config_id=demo_config_id,
        room_id=room_id,
        page_entity_type=page_entity_type,
        page_entity_id=page_entity_id,
        auto_respond=auto_respond,
        status=status,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_accessed_at=datetime.utcnow(),
    )
    session.add(demo_session)
    await session.flush()
    await session.refresh(demo_session)
    return demo_session


async def update_demo_session(
    session: AsyncSession,
    demo_session: DemoSession,
    demo_session_update: DemoSessionUpdate,
) -> DemoSession:
    """Update an existing demo session."""
    update_data = demo_session_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(demo_session, key, value)

    demo_session.updated_at = datetime.utcnow()
    demo_session.last_accessed_at = datetime.utcnow()
    session.add(demo_session)
    await session.flush()
    await session.refresh(demo_session)
    return demo_session


async def touch_demo_session(
    session: AsyncSession,
    demo_session: DemoSession,
) -> DemoSession:
    """
    Update last_accessed_at (and updated_at) for an existing session.
    """
    now = datetime.utcnow()
    demo_session.last_accessed_at = now
    demo_session.updated_at = now
    session.add(demo_session)
    await session.flush()
    await session.refresh(demo_session)
    return demo_session


async def delete_demo_session(
    session: AsyncSession,
    demo_session: DemoSession,
) -> None:
    """Delete a demo session."""
    await session.delete(demo_session)


# =============================================================================
# Route-level Helper
# =============================================================================


async def get_or_create_demo_session_by_slug(
    session: AsyncSession,
    *,
    user_id: UUID,
    demo_slug: str,
    room_id: UUID,
    page_entity_id: str,
) -> tuple[DemoConfig, DemoSession, bool] | None:
    """
    Resolve a visible demo config by slug, then return the user's session.

    Returns:
    - (demo_config, demo_session, created)
    - None if demo slug does not exist or is not visible to user

    Notes:
    - auto_respond defaults from DemoConfig.default_auto_respond
    - handles unique-constraint race on (user_id, demo_config_id)
    """
    demo_config = await get_demo_config_by_slug_visible_to_user(
        session, demo_slug, user_id
    )
    if not demo_config or not demo_config.is_active:
        return None

    existing = await get_demo_session_for_user(
        session,
        user_id=user_id,
        demo_config_id=demo_config.id,
    )
    if existing:
        return demo_config, existing, False

    demo_session = DemoSession(
        user_id=user_id,
        demo_config_id=demo_config.id,
        room_id=room_id,
        page_entity_type="demo",
        page_entity_id=page_entity_id,
        auto_respond=demo_config.default_auto_respond,
        status=DemoSessionStatus.active,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_accessed_at=datetime.utcnow(),
    )
    try:
        async with session.begin_nested():
            session.add(demo_session)
            await session.flush()
        await session.refresh(demo_session)
        return demo_config, demo_session, True
    except IntegrityError:
        # Another request created the row concurrently.
        existing = await get_demo_session_for_user(
            session,
            user_id=user_id,
            demo_config_id=demo_config.id,
        )
        if existing:
            return demo_config, existing, False
        raise


# =============================================================================
# DemoPageComposition CRUD / Resolution
# =============================================================================


def _default_panel_specs() -> list[dict[str, object]]:
    return [
        {"id": "story-runtime", "kind": "storyRuntime", "prominence": "primary", "order": 1},
        {"id": "chat", "kind": "chat", "prominence": "auxiliary", "order": 2},
    ]


def _safe_uuid(value: object) -> UUID | None:
    if isinstance(value, UUID):
        return value
    if not isinstance(value, str):
        return None
    try:
        return UUID(value)
    except ValueError:
        return None


async def resolve_demo_story_id_for_user(
    session: AsyncSession,
    *,
    demo_config: DemoConfig,
    user_id: UUID,
) -> UUID | None:
    """
    Resolve the story_id to attach when creating a room for this demo.

    Precedence:
    1) Resolved composition metadata_json.story_id (includes user override path)
    2) DemoConfig metadata_json.story_id
    3) None

    Raises:
    - HTTP 400 when a story_id is provided but does not exist.
    """
    composition, _ = await resolve_demo_composition_for_user(
        session,
        demo_config=demo_config,
        user_id=user_id,
    )

    composition_story_id = None
    if isinstance(composition.metadata_json, dict):
        composition_story_id = _safe_uuid(composition.metadata_json.get("story_id"))
    config_story_id = None
    if isinstance(demo_config.metadata_json, dict):
        config_story_id = _safe_uuid(demo_config.metadata_json.get("story_id"))

    story_id = composition_story_id or config_story_id
    if not story_id:
        return None

    story = await session.get(Story, story_id)
    if not story:
        raise HTTPException(
            status_code=400,
            detail="Configured demo story_id does not reference an existing story",
        )
    return story_id


def _build_fallback_composition_from_config(
    demo_config: DemoConfig,
) -> DemoPageCompositionBase:
    metadata = demo_config.metadata_json if isinstance(demo_config.metadata_json, dict) else {}

    panels_payload = (
        demo_config.default_panels_json
        if isinstance(demo_config.default_panels_json, list)
        else []
    )
    blocks_payload: list[dict[str, object]] = []
    if isinstance(demo_config.default_layout_json, list):
        blocks_payload = demo_config.default_layout_json
    elif isinstance(metadata.get("blocks"), list):
        blocks_payload = metadata["blocks"]  # type: ignore[assignment]

    candidate = {
        "schema_version": 1,
        "layout_mode": metadata.get("layout_mode", "panels"),
        "runtime_policy": metadata.get("runtime_policy", DemoRuntimePolicy.auto),
        "persona_policy": metadata.get(
            "persona_policy",
            DemoPersonaPolicy.first_available,
        ),
        "chat_mode": metadata.get("chat_mode", "participant"),
        "fixed_user_persona_id": metadata.get("fixed_user_persona_id"),
        "page_theme_id": _safe_uuid(metadata.get("page_theme_id")),
        "cards_theme_id": _safe_uuid(metadata.get("cards_theme_id")),
        "presentation_json": (
            metadata.get("presentation_json")
            if isinstance(metadata.get("presentation_json"), dict)
            else {}
        ),
        "panels": panels_payload,
        "blocks": blocks_payload,
        "metadata_json": metadata,
    }

    try:
        return DemoPageCompositionBase.model_validate(candidate)
    except Exception:
        # Final hard fallback to guaranteed valid defaults.
        return DemoPageCompositionBase.model_validate(
            {
                "schema_version": 1,
                "layout_mode": "panels",
                "runtime_policy": DemoRuntimePolicy.auto,
                "persona_policy": DemoPersonaPolicy.first_available,
                "chat_mode": "participant",
                "fixed_user_persona_id": None,
                "page_theme_id": None,
                "cards_theme_id": None,
                "presentation_json": {},
                "panels": _default_panel_specs(),
                "blocks": [],
                "metadata_json": metadata,
            }
        )


def _deserialize_composition_row(row: DemoPageComposition) -> DemoPageCompositionBase:
    return DemoPageCompositionBase.model_validate(
        {
            "schema_version": row.schema_version,
            "layout_mode": row.layout_mode,
            "runtime_policy": row.runtime_policy,
            "persona_policy": row.persona_policy,
            "chat_mode": row.chat_mode,
            "fixed_user_persona_id": row.fixed_user_persona_id,
            "page_theme_id": row.page_theme_id,
            "cards_theme_id": row.cards_theme_id,
            "presentation_json": row.presentation_json,
            "panels": row.panels,
            "blocks": row.blocks,
            "metadata_json": row.metadata_json,
        }
    )


async def get_demo_page_composition_by_demo_config_id(
    session: AsyncSession,
    *,
    demo_config_id: UUID,
) -> DemoPageComposition | None:
    statement = select(DemoPageComposition).where(
        DemoPageComposition.demo_config_id == demo_config_id
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def put_demo_page_composition(
    session: AsyncSession,
    *,
    demo_config_id: UUID,
    owner_id: UUID | None,
    composition_in: DemoPageCompositionBase,
) -> DemoPageComposition:
    existing = await get_demo_page_composition_by_demo_config_id(
        session,
        demo_config_id=demo_config_id,
    )
    payload = composition_in.model_dump(mode="json")
    now = datetime.utcnow()

    if existing:
        existing.schema_version = payload["schema_version"]
        existing.layout_mode = payload["layout_mode"]
        existing.runtime_policy = payload["runtime_policy"]
        existing.persona_policy = payload["persona_policy"]
        existing.chat_mode = payload["chat_mode"]
        existing.fixed_user_persona_id = payload["fixed_user_persona_id"]
        existing.page_theme_id = payload["page_theme_id"]
        existing.cards_theme_id = payload["cards_theme_id"]
        existing.presentation_json = payload["presentation_json"]
        existing.panels = payload["panels"]
        existing.blocks = payload["blocks"]
        existing.metadata_json = payload["metadata_json"]
        existing.owner_id = owner_id
        existing.updated_at = now
        session.add(existing)
        await session.flush()
        await session.refresh(existing)
        return existing

    created = DemoPageComposition(
        demo_config_id=demo_config_id,
        owner_id=owner_id,
        schema_version=payload["schema_version"],
        layout_mode=payload["layout_mode"],
        runtime_policy=payload["runtime_policy"],
        persona_policy=payload["persona_policy"],
        chat_mode=payload["chat_mode"],
        fixed_user_persona_id=payload["fixed_user_persona_id"],
        page_theme_id=payload["page_theme_id"],
        cards_theme_id=payload["cards_theme_id"],
        presentation_json=payload["presentation_json"],
        panels=payload["panels"],
        blocks=payload["blocks"],
        metadata_json=payload["metadata_json"],
        created_at=now,
        updated_at=now,
    )
    session.add(created)
    await session.flush()
    await session.refresh(created)
    return created


async def patch_demo_page_composition(
    session: AsyncSession,
    *,
    demo_config_id: UUID,
    owner_id: UUID | None,
    patch_in: DemoPageCompositionUpdate,
) -> DemoPageComposition:
    existing = await get_demo_page_composition_by_demo_config_id(
        session,
        demo_config_id=demo_config_id,
    )
    if existing:
        base = _deserialize_composition_row(existing)
    else:
        raise HTTPException(status_code=404, detail="Demo composition not found")

    merged = base.model_copy(
        update=patch_in.model_dump(exclude_unset=True, mode="json"),
    )
    normalized = DemoPageCompositionBase.model_validate(
        merged.model_dump(mode="json")
    )
    return await put_demo_page_composition(
        session,
        demo_config_id=demo_config_id,
        owner_id=owner_id,
        composition_in=normalized,
    )


async def get_or_create_demo_page_composition(
    session: AsyncSession,
    *,
    demo_config: DemoConfig,
    owner_id: UUID | None,
) -> tuple[DemoPageComposition, bool]:
    existing = await get_demo_page_composition_by_demo_config_id(
        session,
        demo_config_id=demo_config.id,
    )
    if existing:
        return existing, False

    fallback = _build_fallback_composition_from_config(demo_config)
    created = await put_demo_page_composition(
        session,
        demo_config_id=demo_config.id,
        owner_id=owner_id,
        composition_in=fallback,
    )
    return created, True


async def resolve_demo_composition_for_user(
    session: AsyncSession,
    *,
    demo_config: DemoConfig,
    user_id: UUID,
) -> tuple[DemoPageCompositionBase, DemoCompositionSource]:
    override_statement = select(UserDemoPageCompositionOverride).where(
        UserDemoPageCompositionOverride.user_id == user_id,
        UserDemoPageCompositionOverride.demo_config_id == demo_config.id,
    )
    override_result = await session.exec(override_statement)
    override = override_result.one_or_none()
    if override and not override.use_composition_defaults:
        try:
            return (
                DemoPageCompositionBase.model_validate(override.override_json),
                DemoCompositionSource.session_override,
            )
        except Exception:
            pass

    config_comp = await get_demo_page_composition_by_demo_config_id(
        session,
        demo_config_id=demo_config.id,
    )
    if config_comp:
        try:
            return (
                _deserialize_composition_row(config_comp),
                DemoCompositionSource.demo_config,
            )
        except Exception:
            pass

    fallback = _build_fallback_composition_from_config(demo_config)
    return fallback, DemoCompositionSource.type_defaults


async def build_resolve_demo_entry_payload(
    session: AsyncSession,
    *,
    user_id: UUID,
    demo_config: DemoConfig,
    demo_session: DemoSession,
    created: bool,
) -> ResolveDemoEntryPayload:
    room = await session.get(Room, demo_session.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Demo room not found")

    participant_statement = select(RoomParticipant).where(
        RoomParticipant.room_id == demo_session.room_id,
        RoomParticipant.participant_type == "user",
        RoomParticipant.participant_id == str(user_id),
        RoomParticipant.active == True,  # noqa: E712
    )
    participant_result = await session.exec(participant_statement)
    participant = participant_result.one_or_none()
    can_write = bool(participant and participant.role == "owner")

    composition, source = await resolve_demo_composition_for_user(
        session,
        demo_config=demo_config,
        user_id=user_id,
    )

    has_runtime = False
    try:
        await get_room_runtime(
            room_id=demo_session.room_id,
            user_id=user_id,
            session=session,
        )
        has_runtime = True
    except HTTPException as exc:
        if exc.status_code not in (403, 404, 410):
            raise

    return ResolveDemoEntryPayload(
        demo_config_id=demo_config.id,
        demo_session_id=demo_session.id,
        created=created,
        composition=composition,
        composition_source=source,
        room=DemoResolvedRoomContext(
            room_id=demo_session.room_id,
            story_id=room.story_id,
            title=room.title,
            can_write=can_write,
        ),
        runtime=DemoResolvedRuntimeContext(
            has_runtime=has_runtime,
            runtime_policy=composition.runtime_policy,
            persona_policy=composition.persona_policy,
            auto_start_attempted=False,
            auto_start_succeeded=False,
            auto_start_error=None,
        ),
    )
