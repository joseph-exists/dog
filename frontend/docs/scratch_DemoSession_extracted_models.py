# import uuid
# from datetime import datetime
# from enum import Enum as PyEnum
# from typing import Any
# from uuid import UUID
#
# from sqlalchemy import UniqueConstraint
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlmodel import Column, Field, Relationship, SQLModel

# NOTE:
# This is an extracted planning document for backend integration.
# It is intentionally colocated in frontend/docs for design review.


# =============================================================================
# Demo Models (Template + Per-User Runtime Session)
# =============================================================================
#
# Architecture split:
# - DemoConfig: reusable demo template (slug-routed, shared metadata/defaults)
# - DemoSession: user-specific runtime instance (room + page context anchor)
#
# This avoids mixing template concerns with per-user room/session concerns.
# =============================================================================


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class DemoConfigScope(str, PyEnum):
    """
    Visibility and ownership rules for demo templates.
    """
    system = "system"
    personal = "personal"
    shared = "shared"


class DemoSessionStatus(str, PyEnum):
    """
    Session lifecycle state.
    """
    active = "active"
    archived = "archived"
    ended = "ended"


# -----------------------------------------------------------------------------
# DemoConfig Models (Base -> Create -> Update -> Database -> Public -> List)
# -----------------------------------------------------------------------------

class DemoConfigBase(SQLModel):
    """
    Shared properties for a demo template.
    """
    slug: str = Field(
        min_length=1,
        max_length=100,
        description="URL-safe identifier used by /demo/$slug",
    )
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    scope: DemoConfigScope = Field(default=DemoConfigScope.system)
    is_active: bool = Field(default=True)

    # Defaults used when creating a DemoSession for a user
    default_auto_respond: bool = Field(default=True)
    default_panels_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Default panel composition for DemoShell",
    )
    default_layout_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Default page block layout (TemplateBlock-like payload)",
    )
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Extensible config for demo-specific integrations",
    )


class DemoConfigCreate(DemoConfigBase):
    """
    API input for creating a demo template.
    """
    pass


class DemoConfigUpdate(SQLModel):
    """
    API input for updating an existing demo template.
    """
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    scope: DemoConfigScope | None = None
    is_active: bool | None = None
    default_auto_respond: bool | None = None
    default_panels_json: list[dict[str, Any]] | None = None
    default_layout_json: list[dict[str, Any]] | None = None
    metadata_json: dict[str, Any] | None = None


class DemoConfig(DemoConfigBase, table=True):
    """
    Database model for demo template config.
    """
    __tablename__ = "demo_configs"
    __table_args__ = (UniqueConstraint("slug", name="uq_demo_config_slug"),)

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description="Null for system templates",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DemoConfigPublic(DemoConfigBase):
    id: UUID
    owner_id: UUID | None
    created_at: datetime
    updated_at: datetime


class DemoConfigsPublic(SQLModel):
    data: list[DemoConfigPublic]
    count: int


# -----------------------------------------------------------------------------
# DemoSession Models (Base -> Create -> Update -> Database -> Public -> List)
# -----------------------------------------------------------------------------

class DemoSessionBase(SQLModel):
    """
    Shared properties for per-user runtime demo sessions.

    page_entity_type/page_entity_id anchor page layout persistence.
    """
    auto_respond: bool = Field(default=True)
    status: DemoSessionStatus = Field(default=DemoSessionStatus.active)
    page_entity_type: str = Field(default="demo", max_length=50, index=True)
    page_entity_id: str = Field(
        min_length=1,
        max_length=255,
        index=True,
        description="Stable entity_id used by PageService for demo layouts",
    )


class DemoSessionCreate(SQLModel):
    """
    API input for explicit session creation.
    user_id is inferred from auth in normal API usage.
    """
    demo_config_id: UUID = Field(description="Demo template to instantiate")
    auto_respond: bool | None = None


class DemoSessionUpdate(SQLModel):
    auto_respond: bool | None = None
    status: DemoSessionStatus | None = None


class DemoSession(DemoSessionBase, table=True):
    """
    Database model for a user's instantiated demo environment.

    Invariant:
    - One active session per (user_id, demo_config_id) pair by default.
    """
    __tablename__ = "demo_sessions"
    __table_args__ = (
        UniqueConstraint("user_id", "demo_config_id", name="uq_demo_session_user_demo"),
    )

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    demo_config_id: UUID = Field(foreign_key="demo_configs.id", index=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    room_id: UUID = Field(
        foreign_key="rooms.room_id",
        description="Per-user room backing this demo session",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_accessed_at: datetime = Field(default_factory=datetime.utcnow)


class DemoSessionPublic(DemoSessionBase):
    id: UUID
    demo_config_id: UUID
    user_id: UUID
    room_id: UUID
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime


class DemoSessionsPublic(SQLModel):
    data: list[DemoSessionPublic]
    count: int


# -----------------------------------------------------------------------------
# Route/Service Resolution Shapes
# -----------------------------------------------------------------------------

class ResolveDemoSessionRequest(SQLModel):
    """
    Input for route-layer get-or-create resolution.
    Used by /demo/{slug} and /d/{id}-style entry routes.
    """
    demo_slug: str = Field(min_length=1, max_length=100)


class ResolveDemoSessionResponse(SQLModel):
    """
    Output from get-or-create resolution.
    """
    demo_config: DemoConfigPublic
    demo_session: DemoSessionPublic
    created: bool = Field(
        description="True if session (and room) were created during this request"
    )


# -----------------------------------------------------------------------------
# Post-Definition Relationship Bindings
# -----------------------------------------------------------------------------
# Define after all models to align with data_model_rules.md.
# -----------------------------------------------------------------------------

DemoConfig.sessions = Relationship(
    back_populates="demo_config",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

DemoSession.demo_config = Relationship(back_populates="sessions")

# Optional back-populates on User/Room should be added in backend app/models.py.
