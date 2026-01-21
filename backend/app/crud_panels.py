"""
CRUD operations for room panel configuration.

All operations are async to match the codebase patterns.
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    PanelPreset,
    PanelPresetPublic,
    Room,
    RoomPanelDefaults,
    UserPanelDefaults,
    UserPanelDefaultsUpdate,
    UserRoomPanelConfig,
)

# Default panel configs by room type
DEFAULT_PANELS = {
    "chat": [
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "story": [
        {"id": "story", "kind": "storyEditor", "prominence": "primary"},
        {"id": "chat", "kind": "chat", "prominence": "primary"},
        {"id": "agents", "kind": "agentPanel", "prominence": "auxiliary"},
    ],
    "workspace": [],
}


async def get_room_panel_defaults(
    session: AsyncSession, room_id: UUID
) -> RoomPanelDefaults | None:
    """Get room's default panel configuration."""
    statement = select(RoomPanelDefaults).where(
        RoomPanelDefaults.room_id == room_id
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def set_room_panel_defaults(
    session: AsyncSession, room_id: UUID, panels: list[dict]
) -> RoomPanelDefaults:
    """Set or update room's default panel configuration."""
    existing = await get_room_panel_defaults(session, room_id)

    if existing:
        existing.panels = panels
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = RoomPanelDefaults(
            room_id=room_id,
            panels=panels,
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def get_user_room_panel_config(
    session: AsyncSession, user_id: UUID, room_id: UUID
) -> UserRoomPanelConfig | None:
    """Get user's panel config override for a room."""
    statement = select(UserRoomPanelConfig).where(
        UserRoomPanelConfig.user_id == user_id,
        UserRoomPanelConfig.room_id == room_id,
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()


async def set_user_room_panel_config(
    session: AsyncSession,
    user_id: UUID,
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
) -> UserRoomPanelConfig:
    """Set or update user's panel config for a room."""
    existing = await get_user_room_panel_config(session, user_id, room_id)

    if existing:
        existing.panels = panels
        existing.use_room_defaults = use_room_defaults
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = UserRoomPanelConfig(
            user_id=user_id,
            room_id=room_id,
            panels=panels,
            use_room_defaults=use_room_defaults,
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def resolve_panels_for_user(
    session: AsyncSession, user_id: UUID, room_id: UUID
) -> tuple[list[dict], str]:
    """
    Resolve the effective panel configuration for a user in a room.

    Returns: (panels, source) where source is one of:
        - "room_override": User has custom config for this room
        - "room_defaults": Using room owner's defaults
        - "user_defaults": Using user's global defaults
        - "system_defaults": Using built-in system defaults
    """
    # Import here to avoid circular imports
    from app.api.routes.presets import SYSTEM_PRESETS

    # 1. Check for user's room override
    user_room_config = await get_user_room_panel_config(session, user_id, room_id)
    if user_room_config and not user_room_config.use_room_defaults and user_room_config.panels:
        return user_room_config.panels, "room_override"

    # 2. Check for room defaults (set by owner)
    room_defaults = await get_room_panel_defaults(session, room_id)
    if room_defaults and room_defaults.panels:
        return room_defaults.panels, "room_defaults"

    # 3. Check for user's global defaults
    user_defaults = await get_user_panel_defaults(session, user_id)
    if user_defaults:
        # If user has a preset selected, use that
        if user_defaults.preset_id and user_defaults.preset_id in SYSTEM_PRESETS:
            return SYSTEM_PRESETS[user_defaults.preset_id]["panels"], "user_defaults"
        # Otherwise use their custom panels
        if user_defaults.panels:
            return user_defaults.panels, "user_defaults"

    # 4. Fall back to system default (collaborate)
    return SYSTEM_PRESETS["collaborate"]["panels"], "system_defaults"


# ==================== User Panel Defaults ====================


async def get_user_panel_defaults(
    session: AsyncSession, user_id: UUID
) -> UserPanelDefaults | None:
    """Get user's global panel defaults."""
    statement = select(UserPanelDefaults).where(
        UserPanelDefaults.user_id == user_id
    )
    result = await session.exec(statement)
    return result.one_or_none()


async def create_user_panel_defaults(
    session: AsyncSession,
    user_id: UUID,
    preset_id: str | None = None,
    panels: list[dict] | None = None,
    reduce_motion: bool = False,
) -> UserPanelDefaults:
    """Create user's panel defaults."""
    defaults = UserPanelDefaults(
        user_id=user_id,
        preset_id=preset_id,
        panels=panels or [],
        reduce_motion=reduce_motion,
    )
    session.add(defaults)
    await session.commit()
    await session.refresh(defaults)
    return defaults


async def update_user_panel_defaults(
    session: AsyncSession,
    user_id: UUID,
    update_data: UserPanelDefaultsUpdate,
) -> UserPanelDefaults:
    """Update user's panel defaults, creating if doesn't exist."""
    existing = await get_user_panel_defaults(session, user_id)

    if existing:
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(existing, key, value)
        existing.updated_at = datetime.utcnow()
        session.add(existing)
    else:
        existing = UserPanelDefaults(
            user_id=user_id,
            preset_id=update_data.preset_id,
            panels=update_data.panels or [],
            reduce_motion=update_data.reduce_motion or False,
        )
        session.add(existing)

    await session.commit()
    await session.refresh(existing)
    return existing


async def delete_user_panel_defaults(
    session: AsyncSession, user_id: UUID
) -> bool:
    """Delete user's panel defaults."""
    existing = await get_user_panel_defaults(session, user_id)
    if existing:
        await session.delete(existing)
        await session.commit()
        return True
    return False


# ==================== Panel Presets ====================


async def get_preset(
    session: AsyncSession, preset_id: UUID
) -> PanelPreset | None:
    """Get a preset by ID."""
    return await session.get(PanelPreset, preset_id)


async def get_system_presets(
    session: AsyncSession,
) -> list[PanelPreset]:
    """Get all system presets."""
    statement = select(PanelPreset).where(PanelPreset.is_system == True)
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_user_presets(
    session: AsyncSession, user_id: UUID
) -> list[PanelPreset]:
    """Get all presets owned by a user."""
    statement = select(PanelPreset).where(
        PanelPreset.owner_id == user_id,
        PanelPreset.is_system == False,
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def get_room_shared_presets(
    session: AsyncSession, room_id: UUID
) -> list[PanelPreset]:
    """Get all presets shared to a room."""
    statement = select(PanelPreset).where(
        PanelPreset.shared_to_room_id == room_id
    )
    result = await session.execute(statement)
    return list(result.scalars().all())


async def create_preset(
    session: AsyncSession,
    owner_id: UUID,
    name: str,
    panels: list[dict],
    description: str | None = None,
    shared_to_room_id: UUID | None = None,
) -> PanelPreset:
    """Create a user preset."""
    preset = PanelPreset(
        owner_id=owner_id,
        name=name,
        description=description,
        panels=panels,
        is_system=False,
        shared_to_room_id=shared_to_room_id,
    )
    session.add(preset)
    await session.commit()
    await session.refresh(preset)
    return preset


async def update_preset(
    session: AsyncSession,
    preset_id: UUID,
    owner_id: UUID,
    name: str | None = None,
    description: str | None = None,
    panels: list[dict] | None = None,
    shared_to_room_id: UUID | None = None,
) -> PanelPreset | None:
    """Update a user preset (only owner can update)."""
    preset = await get_preset(session, preset_id)
    if not preset or preset.owner_id != owner_id or preset.is_system:
        return None

    if name is not None:
        preset.name = name
    if description is not None:
        preset.description = description
    if panels is not None:
        preset.panels = panels
    if shared_to_room_id is not None:
        preset.shared_to_room_id = shared_to_room_id

    session.add(preset)
    await session.commit()
    await session.refresh(preset)
    return preset


async def delete_preset(
    session: AsyncSession, preset_id: UUID, owner_id: UUID
) -> bool:
    """Delete a user preset (only owner can delete)."""
    preset = await get_preset(session, preset_id)
    if not preset or preset.owner_id != owner_id or preset.is_system:
        return False

    await session.delete(preset)
    await session.commit()
    return True
