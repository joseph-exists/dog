"""
CRUD operations for room panel configuration.
"""

from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select

from app.models import (
    Room,
    RoomPanelDefaults,
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


def get_room_panel_defaults(
    session: Session, room_id: UUID
) -> RoomPanelDefaults | None:
    """Get room's default panel configuration."""
    statement = select(RoomPanelDefaults).where(
        RoomPanelDefaults.room_id == room_id
    )
    return session.exec(statement).first()


def set_room_panel_defaults(
    session: Session, room_id: UUID, panels: list[dict]
) -> RoomPanelDefaults:
    """Set or update room's default panel configuration."""
    existing = get_room_panel_defaults(session, room_id)

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

    session.commit()
    session.refresh(existing)
    return existing


def get_user_room_panel_config(
    session: Session, user_id: UUID, room_id: UUID
) -> UserRoomPanelConfig | None:
    """Get user's panel config override for a room."""
    statement = select(UserRoomPanelConfig).where(
        UserRoomPanelConfig.user_id == user_id,
        UserRoomPanelConfig.room_id == room_id,
    )
    return session.exec(statement).first()


def set_user_room_panel_config(
    session: Session,
    user_id: UUID,
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
) -> UserRoomPanelConfig:
    """Set or update user's panel config for a room."""
    existing = get_user_room_panel_config(session, user_id, room_id)

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

    session.commit()
    session.refresh(existing)
    return existing


def resolve_panels_for_user(
    session: Session, user_id: UUID, room_id: UUID
) -> tuple[list[dict], str]:
    """
    Resolve the effective panel configuration for a user in a room.

    Returns: (panels, source) where source is one of:
        - "user_override": User has custom config
        - "room_defaults": Using room owner's defaults
        - "type_defaults": Using built-in type defaults
    """
    # Check for user override
    user_config = get_user_room_panel_config(session, user_id, room_id)
    if user_config and not user_config.use_room_defaults and user_config.panels:
        return user_config.panels, "user_override"

    # Check for room defaults
    room_defaults = get_room_panel_defaults(session, room_id)
    if room_defaults and room_defaults.panels:
        return room_defaults.panels, "room_defaults"

    # Fall back to type defaults
    room = session.get(Room, room_id)
    room_type = getattr(room, "type", "chat") if room else "chat"
    return DEFAULT_PANELS.get(room_type, DEFAULT_PANELS["chat"]), "type_defaults"