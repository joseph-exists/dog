task review: we've added the models as specified to models.py.  we are attempting to build the backend, and we get the following error:

```
Foreign key associated with column 'room_panel_defaults.room_id' could not find table 'room' with which to generate a foreign key to target column 'id'
```

Question: do the models below align with backend/docs/DATA_MODEL_RULES.md?  




ADDED TO : `backend/app/models.py`:

```python
# =============================================================================
# Room Panel Configuration
# =============================================================================

class PanelConfigItem(SQLModel):
    """Individual panel configuration"""
    id: str
    kind: str  # chat, storyEditor, agentPanel, debug, canvas, a2ui
    prominence: str  # primary, auxiliary


class RoomPanelDefaultsBase(SQLModel):
    """Base properties for room panel defaults"""
    panels: list[dict] = Field(default=[], sa_column=Column(JSON))


class RoomPanelDefaults(RoomPanelDefaultsBase, table=True):
    """Default panel configuration set by room owner"""
    __tablename__ = "room_panel_defaults"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(foreign_key="room.id", unique=True, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



class RoomPanelDefaultsPublic(RoomPanelDefaultsBase):
    """Public response for room panel defaults"""
    id: uuid.UUID
    room_id: uuid.UUID
    updated_at: datetime


class UserRoomPanelConfigBase(SQLModel):
    """Base properties for user room panel config"""
    panels: list[dict] | None = Field(default=None, sa_column=Column(JSON))
    use_room_defaults: bool = Field(default=True)


class UserRoomPanelConfig(UserRoomPanelConfigBase, table=True):
    """User's personal panel override for a specific room"""
    __tablename__ = "user_room_panel_config"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    room_id: uuid.UUID = Field(foreign_key="room.id", index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Composite unique constraint
    __table_args__ = (UniqueConstraint("user_id", "room_id"),)


class UserRoomPanelConfigPublic(UserRoomPanelConfigBase):
    """Public response for user panel config"""
    id: uuid.UUID
    user_id: uuid.UUID
    room_id: uuid.UUID
    updated_at: datetime


class ResolvedPanelConfig(SQLModel):
    """Resolved panel config for a user in a room"""
    panels: list[dict]
    source: str  # "user_override", "room_defaults", "type_defaults"
```

This has been added to the relationship bindings section of our models.py:

```python

Room.panel_defaults = Relationship(
    back_populates="room",
    sa_relationship_kwargs={
        "foreign_keys": "[RoomPanelDefaults.room_id]",
        "uselist": False
    }
)

# At the bottom of your models file, after all classes are defined

RoomPanelDefaults.room = Relationship(
    back_populates="panel_defaults"
)



```


### Task 26: Create Panel Config CRUD

**Files:**
- Create: `backend/app/crud_panels.py`

**Step 1: Create CRUD functions**

```python
"""
CRUD operations for room panel configuration.
"""

from uuid import UUID
from datetime import datetime
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
```
### Task 27: Create Panel Config Routes

**Files:**
- Create: `backend/app/api/routes/room_panels.py`
- Modify: `backend/app/api/main.py`

**Step 1: Create routes**

```python
"""
API routes for room panel configuration.
"""

from uuid import UUID
from typing import Any

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, SessionDep
from app.crud_panels import (
    get_room_panel_defaults,
    set_room_panel_defaults,
    get_user_room_panel_config,
    set_user_room_panel_config,
    resolve_panels_for_user,
)
from app.models import (
    Room,
    RoomPanelDefaultsPublic,
    UserRoomPanelConfigPublic,
    ResolvedPanelConfig,
)
from app.crud import get_room_participant

router = APIRouter()


@router.get("/{room_id}/panels", response_model=ResolvedPanelConfig)
def get_resolved_panels(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get resolved panel configuration for current user.
    Returns the effective panels based on user override or room/type defaults.
    """
    # Verify room exists and user has access
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    panels, source = resolve_panels_for_user(session, current_user.id, room_id)
    return ResolvedPanelConfig(panels=panels, source=source)


@router.get("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic | None)
def get_room_defaults(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get room's default panel configuration (set by owner)."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return get_room_panel_defaults(session, room_id)


@router.put("/{room_id}/panels/defaults", response_model=RoomPanelDefaultsPublic)
def update_room_defaults(
    room_id: UUID,
    panels: list[dict],
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Update room's default panel configuration.
    Only room owner can modify.
    """
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    # Check ownership
    participant = get_room_participant(session, room_id, current_user.id)
    if not participant or participant.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only room owner can set default panels",
        )

    return set_room_panel_defaults(session, room_id, panels)


@router.get("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic | None)
def get_my_panel_config(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get current user's panel configuration override for this room."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return get_user_room_panel_config(session, current_user.id, room_id)


@router.put("/{room_id}/panels/me", response_model=UserRoomPanelConfigPublic)
def update_my_panel_config(
    room_id: UUID,
    panels: list[dict] | None,
    use_room_defaults: bool,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Update current user's panel configuration for this room."""
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return set_user_room_panel_config(
        session, current_user.id, room_id, panels, use_room_defaults
    )
```

**Step 2: Register router in main.py**

Add to `backend/app/api/main.py`:
```python
from app.api.routes import room_panels

api_router.include_router(
    room_panels.router,
    prefix="/rooms",
    tags=["room-panels"],
)
```