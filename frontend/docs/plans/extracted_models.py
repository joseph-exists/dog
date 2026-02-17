# import uuid
# from datetime import datetime
# from enum import Enum as PyEnum
# from typing import Annotated, Any, Literal, Union
# from uuid import UUID

# from pydantic import EmailStr, field_validator
# from sqlalchemy import JSON, UniqueConstraint
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlmodel import Column, Field, Relationship, SQLModel

# note: these imports won't resolve - this extract is only to give understanding and context for the models which
# will be integrated within the actual models.py file by the backend team


# =============================================================================
# Theme System Models
# =============================================================================
#
# Following data_model_rules.md patterns:
# 1. Use string-based forward references for type hints
# 2. Define field-only models first
# 3. Add relationships after all models are defined
# 4. Keep Create/Update/Response models simple
#
# Reference: docs/plans/2026-02-17-theme-system-specification.md
# =============================================================================


# -----------------------------------------------------------------------------
# Theme Enums
# -----------------------------------------------------------------------------

class ThemeCategory(str, PyEnum):
    """
    Classification of theme purpose. Each category has distinct token schemas.

    - page: Page surface theming (includes --background)
    - card: Card/panel content areas (excludes --background)
    - syntax: Code syntax highlighting (Shiki theme or token colors)
    - motion: Animation characteristics (duration, easing, spring physics)
    """
    page = "page"
    card = "card"
    syntax = "syntax"
    motion = "motion"


class ThemeScope(str, PyEnum):
    """
    Visibility and ownership rules for themes.

    - system: Immutable system-seeded themes, visible to all users
    - org: Admin-created themes, visible to all org users
    - personal: User-created themes, visible only to owner
    - shared: User-created themes, visible to all org users
    """
    system = "system"
    org = "org"
    personal = "personal"
    shared = "shared"


class BindingType(str, PyEnum):
    """
    Classification of theme binding ownership.

    - user_pref: owner_id = user_id (viewer's personal preferences)
    - authored: owner_id = entity_id (creator's content theming)
    """
    user_pref = "user_pref"
    authored = "authored"


class ThemeSlot(str, PyEnum):
    """
    Which theme category slot is being filled by a binding.
    Matches ThemeCategory values.
    """
    page = "page"
    cards = "cards"
    syntax = "syntax"
    motion = "motion"


# -----------------------------------------------------------------------------
# Theme Models (Base -> Create -> Update -> Database -> Public -> Collection)
# -----------------------------------------------------------------------------

class ThemeBase(SQLModel):
    """
    Shared properties for Theme entity.
    Contains all common fields used across Create, Update, and Public models.
    """
    name: str = Field(min_length=1, max_length=100, description="Human-readable theme name")
    description: str | None = Field(default=None, max_length=500, description="Optional theme description")
    category: ThemeCategory = Field(description="Classification of theme purpose")
    scope: ThemeScope = Field(default=ThemeScope.personal, description="Visibility and ownership rules")
    tokens: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Category-specific token payload (CSS variables, Shiki config, motion params)"
    )


class ThemeCreate(ThemeBase):
    """
    API input for creating a new theme.
    owner_id is set by the system based on authenticated user.
    is_system is always False for user-created themes.
    """
    pass


class ThemeUpdate(SQLModel):
    """
    API input for updating an existing theme.
    All fields optional - only provided fields are updated.

    Constraints:
    - Cannot update is_system themes
    - Cannot change scope to/from 'system'
    - Cannot change category (would invalidate tokens)
    """
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    scope: ThemeScope | None = None
    tokens: dict[str, Any] | None = None


class Theme(ThemeBase, table=True):
    """
    Database model for Theme entity.

    Invariants:
    1. System themes (is_system=True) cannot be modified or deleted
    2. owner_id must be null if scope='system'
    3. owner_id must be non-null if scope in {personal, shared}
    4. Token payload must conform to category-specific schema
    """
    __tablename__ = "theme"

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description="Creator reference (null for system themes)"
    )
    is_system: bool = Field(default=False, description="Immutable system-seeded flag")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships defined via post-definition binding (see end of file)
    # - owner: User (optional, null for system themes)
    # - bindings: list["ThemeBinding"] (themes bound to contexts)


class ThemePublic(ThemeBase):
    """
    API response model for Theme entity.
    Includes all fields visible to API consumers.
    """
    id: UUID
    owner_id: UUID | None
    is_system: bool
    created_at: datetime
    updated_at: datetime


class ThemesPublic(SQLModel):
    """
    Paginated collection response for Theme list endpoints.
    """
    data: list[ThemePublic]
    count: int


# -----------------------------------------------------------------------------
# ThemeBinding Models (Base -> Create -> Database -> Public -> Collection)
# -----------------------------------------------------------------------------

class ThemeBindingBase(SQLModel):
    """
    Shared properties for ThemeBinding entity.

    Context key grammar:
        context_key ::= segment ("/" segment)*
        segment     ::= type ":" identifier
        type        ::= "page" | "panel" | "story" | "room" | "node"
        identifier  ::= slug | uuid | "*"

    Examples:
        "page:story" - Story listing page
        "page:story/panel:debug" - Debug panel on story page
        "story:{uuid}" - Specific story's base theme
        "page:*/panel:*" - All panels on all pages (global default)
    """
    binding_type: BindingType = Field(description="Classification of binding ownership")
    context_key: str = Field(
        min_length=1,
        max_length=500,
        description="Composite context path (e.g., 'page:story/panel:debug')"
    )
    slot: ThemeSlot = Field(description="Which theme category slot this binding fills")


class ThemeBindingCreate(ThemeBindingBase):
    """
    API input for creating a theme binding.

    For user_pref bindings: owner_id is set by system to authenticated user
    For authored bindings: owner_id is validated against entity ownership
    """
    theme_id: UUID = Field(description="Reference to theme being bound")


class ThemeBindingUpdate(SQLModel):
    """
    API input for updating a theme binding.
    Only theme_id can be changed - context_key and slot define the binding identity.
    """
    theme_id: UUID = Field(description="New theme to bind")


class ThemeBinding(ThemeBindingBase, table=True):
    """
    Database model for ThemeBinding entity.
    Connects themes to specific contexts where they apply.

    Uniqueness: (binding_type, owner_id, context_key, slot) must be unique

    Invariants:
    1. theme_id must reference a Theme with matching category for the slot
    2. For binding_type='user_pref', owner_id must be a valid user
    3. For binding_type='authored', owner_id must be a valid entity of the type implied by context_key
    """
    __tablename__ = "theme_binding"
    __table_args__ = (
        UniqueConstraint(
            "binding_type", "owner_id", "context_key", "slot",
            name="uq_theme_binding_context"
        ),
    )

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: UUID = Field(
        description="Reference to owner (user for user_pref, entity for authored)"
    )
    theme_id: UUID = Field(foreign_key="theme.id", description="Foreign key to Theme")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships defined via post-definition binding (see end of file)
    # - theme: Theme (the theme being bound)


class ThemeBindingPublic(ThemeBindingBase):
    """
    API response model for ThemeBinding entity.
    """
    id: UUID
    owner_id: UUID
    theme_id: UUID
    created_at: datetime
    updated_at: datetime


class ThemeBindingsPublic(SQLModel):
    """
    Paginated collection response for ThemeBinding list endpoints.
    """
    data: list[ThemeBindingPublic]
    count: int


# -----------------------------------------------------------------------------
# Resolution Models (Domain Service Input/Output)
# -----------------------------------------------------------------------------

class ResolutionSource(str, PyEnum):
    """
    How a theme was resolved in the cascade.
    """
    authored = "authored"       # Matched an authored binding
    user_pref = "user_pref"     # Matched a user preference binding
    system_default = "system_default"  # No binding found, using system default
    none = "none"               # No theme available


class EntityContext(SQLModel):
    """
    Optional context for resolving authored bindings.
    Provides information about the entity being viewed.
    """
    entity_type: str = Field(description="Type of entity (story, room, etc.)")
    entity_id: UUID = Field(description="ID of the entity")
    owner_id: UUID = Field(description="Owner of the entity (for authorization)")


class ResolveThemeRequest(SQLModel):
    """
    Input for theme resolution domain service.
    """
    context_path: list[str] = Field(
        description="Ordered path segments (e.g., ['page:story', 'panel:debug'])"
    )
    slot: ThemeSlot = Field(description="Which theme category to resolve")
    entity_context: EntityContext | None = Field(
        default=None,
        description="Optional authored content context"
    )


class ResolvedThemeResponse(SQLModel):
    """
    Output from theme resolution domain service.
    """
    theme: ThemePublic | None = Field(description="Resolved theme or null")
    source: ResolutionSource = Field(description="How the theme was resolved")
    context_key_matched: str | None = Field(
        default=None,
        description="Which binding context_key matched (null for system_default/none)"
    )


class BatchResolveThemeRequest(SQLModel):
    """
    Input for batch theme resolution.
    Resolves multiple slots in a single request for efficiency.
    """
    context_path: list[str] = Field(description="Ordered path segments")
    slots: list[ThemeSlot] = Field(description="Which theme categories to resolve")
    entity_context: EntityContext | None = None


class BatchResolvedThemesResponse(SQLModel):
    """
    Output from batch theme resolution.
    """
    results: dict[ThemeSlot, ResolvedThemeResponse] = Field(
        description="Resolution results keyed by slot"
    )


# -----------------------------------------------------------------------------
# Post-Definition Relationship Bindings
# -----------------------------------------------------------------------------
# Following data_model_rules.md: Define relationships after all models exist
# to avoid circular reference issues.
# -----------------------------------------------------------------------------

# Theme -> ThemeBinding (one-to-many)
# A theme can be bound to multiple contexts
Theme.bindings = Relationship(
    back_populates="theme",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

# ThemeBinding -> Theme (many-to-one)
# Each binding references exactly one theme
ThemeBinding.theme = Relationship(back_populates="bindings")

# Theme -> User (many-to-one, optional)
# Note: User model assumed to exist in models.py
# owner relationship added where Theme is integrated into main models.py
# Theme.owner = Relationship(back_populates="themes")
