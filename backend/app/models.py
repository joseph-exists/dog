import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import EmailStr, field_validator, model_validator
from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel

from app.core.provider_types import TYPE1, TYPE2, TYPE3, TYPE4, TYPE5

# ===== Model Overview for Relational References Ordering
#
# First the User system relationships
# Then the Story system relationships
# Followed by Gameplay State relationships
# Then Character system relationships
# Event system relationships
# And finally Link model relationships


class Message(SQLModel):
    message: str

class PersonaVisibility(str, PyEnum):
    PRIVATE = "private"
    SYSTEM = "system"


class UserPersonaPublicationState(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class AudienceScope(str, PyEnum):
    PUBLIC = "public"
    TRUSTED = "trusted"
    COLLABORATORS = "collaborators"
    CUSTOM = "custom"


class PresentationPublicationState(str, PyEnum):
    DRAFT = "draft"
    PUBLISHED = "published"

# ==================== ProgressSnapshot Models (PHASE 5) ====================

class ProgressSnapshotBase(SQLModel):
    """
    Base model for progress snapshots.

    Snapshots are performance optimization - cached replayed state
    at specific head positions to avoid replaying from root.
    """
    story_state: dict[str, Any] = Field(sa_column=Column(JSON))
    current_node_id: uuid.UUID


class ProgressSnapshotCreate(ProgressSnapshotBase):
    """Input model for creating snapshot"""
    progress_id: uuid.UUID
    choice_id: uuid.UUID


class ProgressSnapshotUpdate(SQLModel):
    """Update model for ProgressSnapshot (rarely used)"""
    story_state: dict[str, Any] | None = Field(default=None)
    current_node_id: uuid.UUID | None = Field(default=None)


class ProgressSnapshot(ProgressSnapshotBase, table=True):
    """
    Database model for progress state snapshots.

    Created every N choices to optimize replay performance.
    Replay can start from nearest snapshot instead of root.

    Semantics:
    - Immutable once created (no updates after creation)
    - Each snapshot linked to specific choice_id (head position)
    - Replaying from snapshot: start with snapshot.story_state,
      then apply events from (snapshot.choice_id → target]
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(
        foreign_key="userstoryprogress.id",
        nullable=False,
        ondelete="CASCADE"
    )
    choice_id: uuid.UUID = Field(
        foreign_key="usernodechoice.id",
        nullable=False,
        description="Head position of this snapshot"
    )

    created_at: datetime = Field(default_factory=datetime.now)



class ProgressSnapshotPublic(ProgressSnapshotBase):
    """Public API response model for ProgressSnapshot"""
    id: uuid.UUID
    progress_id: uuid.UUID
    choice_id: uuid.UUID
    created_at: datetime


class ProgressSnapshotsPublic(SQLModel):
    """Collection response for ProgressSnapshots"""
    data: list[ProgressSnapshotPublic]
    count: int


# for the JWT Tokn
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# ========= enum and constant classes here =================


class QualityState(str, PyEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    REMOVED = "removed"


class QualitySourceType(str, PyEnum):
    TRAIT_DEPENDENT = "trait_dependent"
    DEFAULT = "default"
    MANUALLY_ADDED = "manually_added"

class ContentFormat(str, PyEnum):
    TEXT = "text"
    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    YAML = "yaml"
    MDX = "mdx"
    CODE = "code"
    SVG = "svg"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    EMPTY = "empty"
    UNKNOWN = "unknown"
    TEST = "test"


class SvgAssetVisibility(str, PyEnum):
    """Visibility states for SVG assets."""

    PRIVATE = "private"
    PUBLIC = "public"


class UserRepoImportStatus(str, PyEnum):
    PENDING = "pending"
    IMPORTING = "importing"
    READY = "ready"
    FAILED = "failed"

class AccessGrantSubjectType(str, PyEnum):
    """Subject types supported by AccessGrant."""

    user = "user"
    group = "group"
    user_persona = "user_persona"
    persona_group = "persona_group"


class AccessGrantRole(str, PyEnum):
    """
    Minimal object-scoped roles for access grants.

    NOTE: We currently avoid delegated share-management; object owners and
    superusers manage shares. `manager` is reserved for future expansion.
    """

    viewer = "viewer"
    editor = "editor"
    manager = "manager"


class UserGroupMembershipRole(str, PyEnum):
    """Membership role within a user-owned group."""

    member = "member"
    manager = "manager"


class PersonaGroupType(str, PyEnum):
    """Persona-mediated collaboration container type."""

    group = "group"
    workspace = "workspace"



# ============ Base Models ++++++++


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

class UserPersonaBase(SQLModel):
    """
    User-owned derived state.

    This is the product model that should replace page-JSON as the source of truth
    for authored persona identity/state on user pages.
    """

    nickname: str | None = Field(default=None, max_length=255)
    description: str | None = Field(
        default=None,
        max_length=255,
        description="Short user-authored summary for this derived persona.",
    )
    short_bio: str | None = Field(default=None, max_length=500)
    long_bio: str | None = Field(default=None)

    tags_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Weighted tags. Example: "
            '[{"id":"systems-0","label":"systems","weight":0.8,"source":"user"}]'
        ),
    )

    publication_state: UserPersonaPublicationState = Field(
        default=UserPersonaPublicationState.DRAFT
    )
    is_primary: bool = Field(default=False)
    is_active: bool = Field(default=True)
    sort_order: int = Field(default=0, ge=0)

    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Visual presentation-as-data for this UserPersona. "
            "Not audience resolution, permissioning, or segmentation."
        ),
    )




class UserPersonaCreate(UserPersonaBase):
    persona_id: uuid.UUID


class UserPersonaUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    short_bio: str | None = Field(default=None, max_length=500)
    long_bio: str | None = Field(default=None)
    tags_json: list[dict[str, Any]] | None = None
    publication_state: UserPersonaPublicationState | None = None
    is_primary: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = Field(default=None, ge=0)
    presentation_json: dict[str, Any] | None = None


class UserPersona(UserPersonaBase, table=True):
    """Database model for User's instance of a Persona"""

    __tablename__ = "userpersona"
    __table_args__ = (
        UniqueConstraint("user_id", "persona_id", name="uq_userpersona_user_persona"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    persona_id: uuid.UUID = Field(
        foreign_key="persona.id",
        nullable=False,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class UserPersonaPublic(UserPersonaBase):
    """Public model for UserPersona API responses"""

    id: uuid.UUID
    user_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPersonasPublic(SQLModel):
    """Collection model for UserPersona API responses"""

    data: list[UserPersonaPublic]
    count: int


class DiscoveredUserPersonaPublic(SQLModel):
    """Search result for a discoverable published user persona."""

    id: uuid.UUID
    user_id: uuid.UUID
    persona_id: uuid.UUID
    name: str
    nickname: str | None = None
    short_bio: str | None = None
    publication_state: UserPersonaPublicationState
    owner_display_name: str
    is_primary: bool = False


class DiscoveredUserPersonasPublic(SQLModel):
    """Collection response for discoverable user persona search."""

    data: list[DiscoveredUserPersonaPublic]
    count: int

# ---------------------------------------------------------------------------
# Recommended UserPersonaPresentation model
# ---------------------------------------------------------------------------


class UserPersonaPresentationBase(SQLModel):
    """
    Audience-specific presentation of a UserPersona.

    This is where audience-facing framing belongs.
    It is intentionally separate from UserPersona.presentation_json.
    """

    audience_scope: AudienceScope = Field(default=AudienceScope.PUBLIC)
    audience_key: str | None = Field(
        default=None,
        max_length=255,
        description=(
            "Optional identifier for custom/manual audience grouping. "
            "Null for standard scopes."
        ),
    )
    audience_label: str = Field(min_length=1, max_length=255)

    headline: str = Field(min_length=1, max_length=255)
    framing_text: str | None = Field(default=None)

    visible_work_ids_json: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Interim work references exposed to this audience presentation."
        ),
    )

    relation_call_to_action: str = Field(
        default="none",
        max_length=64,
        description=(
            "UI affordance only. Example values: none, request_contact, "
            "invite_collaboration, follow_work."
        ),
    )

    publication_state: PresentationPublicationState = Field(
        default=PresentationPublicationState.DRAFT
    )

    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description=(
            "Visual presentation-as-data for this audience-specific presentation."
        ),
    )


class UserPersonaPresentationCreate(
    UserPersonaPresentationBase
):
    user_persona_id: uuid.UUID


class UserPersonaPresentationUpdate(SQLModel):
    audience_scope: AudienceScope | None = None
    audience_key: str | None = Field(default=None, max_length=255)
    audience_label: str | None = Field(default=None, min_length=1, max_length=255)
    headline: str | None = Field(default=None, min_length=1, max_length=255)
    framing_text: str | None = None
    visible_work_ids_json: list[str] | None = None
    relation_call_to_action: str | None = Field(default=None, max_length=64)
    publication_state: PresentationPublicationState | None = None
    presentation_json: dict[str, Any] | None = None


class UserPersonaPresentation(
    UserPersonaPresentationBase, table=True
):
    __tablename__ = "userpersonapresentation"
    __table_args__ = (
        UniqueConstraint(
            "user_persona_id",
            "audience_scope",
            "audience_key",
            name="uq_userpersona_presentation_audience",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class UserPersonaPresentationPublic(UserPersonaPresentationBase):
    """Public model for UserPersonaPresentation API responses."""

    id: uuid.UUID
    user_persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class UserPersonaPresentationsPublic(SQLModel):
    """Collection model for UserPersonaPresentation API responses."""

    data: list[UserPersonaPresentationPublic]
    count: int


"""
UserPersonaPresentation invariants:

1. One UserPersona may have many presentations.
2. Each presentation targets exactly one audience scope (+ optional audience_key).
3. publication_state is per presentation, not folded into UserPersona.
4. presentation_json remains visual only.
"""


class AgentPersonaBase(SQLModel):
    """Base model for an agent's library entry of a Persona."""

    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class AgentPersonaCreate(AgentPersonaBase):
    persona_id: uuid.UUID


class AgentPersonaUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class AgentPersona(AgentPersonaBase, table=True):
    """Database model for an agent's library entry of a Persona."""

    __tablename__ = "agent_personas"
    __table_args__ = (
        UniqueConstraint("agent_id", "persona_id", name="uq_agent_personas_agent_persona"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agent_id: uuid.UUID = Field(
        foreign_key="user_agent_configs.id", nullable=False, ondelete="CASCADE"
    )
    persona_id: uuid.UUID = Field(
        foreign_key="persona.id", nullable=False, ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
    )


class AgentPersonaPublic(AgentPersonaBase):
    """Public model for AgentPersona API responses."""

    id: uuid.UUID
    agent_id: uuid.UUID
    persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class AgentPersonasPublic(SQLModel):
    """Collection model for AgentPersona API responses."""

    data: list[AgentPersonaPublic]
    count: int


class EventBase(SQLModel):
    """Base model for events that can trigger state changes"""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    # NOTE: event_type categories and structure?

class StoryBase(SQLModel):
    """Base model for Story template properties"""
    title: str = Field(min_length=1, max_length=255)
    content_format: ContentFormat | None = Field(default=ContentFormat.TEXT)
    description: str | None = Field(default=None, max_length=1000)
    is_published: bool = Field(default=False)
    story_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))

class ItemBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ArchetypeBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class PersonaBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    long_description: str | None = Field(default=None)
    general_domain: str | None = Field(default=None, max_length=255)
    specific_domain: str | None = Field(default=None, max_length=255)
    general_domain_high: str | None = Field(default=None, max_length=255)
    specific_domain_high: str | None = Field(default=None, max_length=255)

    visibility: PersonaVisibility = Field(default=PersonaVisibility.PRIVATE)
    owner_user_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description=(
            "Required when visibility=private. Null for system personas."
        ),
    )

class TraitBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    # archetype_only: bool = Field(default=False)
    # max_active_personas: int | None = Field(default=None, ge=0)


class QualityBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ArchetypeTraitLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    trait_id: uuid.UUID = Field(foreign_key="trait.id")


class PersonaTraitLinkBase(SQLModel):
    persona_id: uuid.UUID = Field(foreign_key="persona.id")
    trait_id: uuid.UUID = Field(foreign_key="trait.id")
    is_inherited: bool = Field(default=False)


class ArchetypeQualityLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    quality_id: uuid.UUID = Field(foreign_key="quality.id")


class PersonaQualityLinkBase(SQLModel):
    persona_id: uuid.UUID = Field(foreign_key="persona.id")
    quality_id: uuid.UUID = Field(foreign_key="quality.id")
    source_type: QualitySourceType = Field(default=QualitySourceType.TRAIT_DEPENDENT)
    state: QualityState = Field(default=QualityState.ENABLED)


class ArchetypePersonaLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    persona_id: uuid.UUID = Field(foreign_key="persona.id")


class QualityTraitLinkBase(SQLModel):
    quality_id: uuid.UUID = Field(foreign_key="quality.id")
    trait_id: uuid.UUID = Field(foreign_key="trait.id")


# ========== Create Models ===========


class PersonaCreate(PersonaBase):
    pass


class ArchetypeCreate(ArchetypeBase):
    pass


class TraitCreate(TraitBase):
    pass


class QualityCreate(QualityBase):
    pass


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class EventCreate(EventBase):
    """Model for creating events"""

    pass

class StoryCreate(StoryBase):
    """Input model for creating a new Story template"""
    pass

# ======== Update Models ===========


class UserBasePartial(SQLModel):
    """Base model for user fields that can be updated (all optional)"""

    email: EmailStr | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)
    is_superuser: bool | None = Field(default=None)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBasePartial):
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


class ItemBasePartial(SQLModel):
    """Base model for item fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item update
class ItemUpdate(ItemBasePartial):
    pass


class ArchetypeBasePartial(SQLModel):
    """Base model for archetype fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class ArchetypeUpdate(ArchetypeBasePartial):
    pass


class PersonaBasePartial(SQLModel):
    """Base model for persona fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    long_description: str | None = Field(default=None)
    general_domain: str | None = Field(default=None, max_length=255)
    specific_domain: str | None = Field(default=None, max_length=255)
    general_domain_high: str | None = Field(default=None, max_length=255)
    specific_domain_high: str | None = Field(default=None, max_length=255)


class PersonaUpdate(PersonaBasePartial):
    pass


class EventBasePartial(SQLModel):
    """Base model for event fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=100)
    event_type: str | None = Field(default=None, min_length=1, max_length=100)


class EventUpdate(EventBasePartial):
    """Model for updating events"""

    pass


class QualityBasePartial(SQLModel):
    """Base model for quality fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class QualityUpdate(QualityBasePartial):
    pass


class TraitBasePartial(SQLModel):
    """Base model for trait fields that can be updated (all optional)"""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class TraitUpdate(TraitBasePartial):
    pass


class QualityEventTriggerBase(SQLModel):
    """
    Base model for defining events that can trigger quality state changes.
    """

    quality_id: uuid.UUID = Field(foreign_key="quality.id")
    event_id: uuid.UUID = Field(foreign_key="event.id")
    new_state: QualityState


class QualityEventTrigger(QualityEventTriggerBase, table=True):
    """
    Database model for quality event triggers.
    Defines what happens to a quality when a specific event occurs.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # Optional condition logic (could be expanded later or refactored with maybe functor)
    condition_json: str | None = Field(default=None)

class StoryUpdate(SQLModel):
    """Input model for updating Story template (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    description: str | None = Field(default=None, max_length=1000)
    content_format: ContentFormat | None = Field(default=ContentFormat.TEXT)  # type: ignore

class Story(StoryBase, table=True):
    """
    Database model for Story template.
    Tracks versioning and publication state.
    
    Version semantics:
    - current_version: what authors are editing (draft space)
    - published_version: what's visible in catalog (locked)
    - is_published: whether any version is public
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")

    # Versioning fields
    current_version: int = Field(default=1)
    published_version: int | None = Field(default=None)
    is_published: bool = Field(default=False)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    deleted_at: datetime | None = Field(default=None, nullable=True)
    story_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))

    # Relationships defined after all models
    # nodes: list["StoryNode"] = Relationship(back_populates="story")
    # requirements: list["StoryRequirement"] = Relationship(back_populates="story")
    # user_progresses: list["UserStoryProgress"] = Relationship(back_populates="story")


class StoryPublic(StoryBase):
    """Public API response model for Story template"""
    id: uuid.UUID
    owner_id: uuid.UUID
    current_version: int
    published_version: int | None
    is_published: bool
    created_at: datetime
    updated_at: datetime
    story_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))


class StoriesPublic(SQLModel):
    """Collection response for Story templates"""
    data: list[StoryPublic]
    count: int


# ==================== StoryNode Models (AUTHORING) ====================

class StoryNodeBase(SQLModel):
    """Base model for StoryNode template properties"""
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(default="")
    content_format: ContentFormat = Field(default=ContentFormat.TEXT) # not nullable
    node_type: str | None = Field(default=None, max_length=50)  # type: ignore
    is_start_node: bool = Field(default=False)
    is_end_node: bool = Field(default=False)


class StoryNodeCreate(StoryNodeBase):
    """Input model for creating a StoryNode"""
    story_id: uuid.UUID
    story_version: int  # Must specify which version this node belongs to
    content_format: ContentFormat = Field(default=ContentFormat.TEXT)


class StoryNodeUpdate(SQLModel):
    """Input model for updating StoryNode (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    content: str | None = Field(default=None)  # type: ignore
    content_format: ContentFormat | None = Field(default=None, max_length=50)
    node_type: str | None = Field(default=None, max_length=50)  # type: ignore
    is_start_node: bool | None = Field(default=None)
    is_end_node: bool | None = Field(default=None)


class StoryNode(StoryNodeBase, table=True):
    """
    Database model for StoryNode template.
    Nodes are versioned and belong to specific story versions.
    Once a story version is published, its nodes become immutable.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False, ondelete="CASCADE")
    story_version: int = Field(nullable=False)  # Which version this node belongs to

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    content_format: ContentFormat | None = Field(default=ContentFormat.TEXT)

    # Relationships defined after all models
    # story: "Story" = Relationship(back_populates="nodes")
    # choices_from: list["NodeChoice"] = Relationship(back_populates="from_node")
    # choices_to: list["NodeChoice"] = Relationship(back_populates="to_node")
    # current_for_progresses: list["UserStoryProgress"] = Relationship(back_populates="current_node")


class StoryNodePublic(StoryNodeBase):
    """Public API response model for StoryNode"""
    id: uuid.UUID
    story_id: uuid.UUID
    story_version: int
    content_format: ContentFormat | None = Field(default=ContentFormat.TEXT)
    created_at: datetime
    updated_at: datetime


class StoryNodesPublic(SQLModel):
    """Collection response for StoryNodes"""
    data: list[StoryNodePublic]
    count: int


# ==================== NodeChoice Models (AUTHORING) ====================

class NodeChoiceBase(SQLModel):
    """Base model for NodeChoice (decision branch in story template)"""
    text: str = Field(min_length=1, max_length=500)
    order: int = Field(default=0)  # Display order for choices

    # State management for conditional branches
    requires_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # Conditions to show this choice
    sets_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))  # State changes when chosen


class NodeChoiceCreate(NodeChoiceBase):
    """Input model for creating a NodeChoice"""
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID


class NodeChoiceUpdate(SQLModel):
    """Input model for updating NodeChoice (all fields optional)"""
    text: str | None = Field(default=None, min_length=1, max_length=500)  # type: ignore
    order: int | None = Field(default=None)
    to_node_id: uuid.UUID | None = Field(default=None)
    requires_state: dict[str, Any] | None = Field(default=None)
    sets_state: dict[str, Any] | None = Field(default=None)


class NodeChoice(NodeChoiceBase, table=True):
    """
    Database model for NodeChoice.
    Represents a decision branch from one node to another.
    Includes conditional logic via requires_state and sets_state.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    from_node_id: uuid.UUID = Field(foreign_key="storynode.id", nullable=False, ondelete="CASCADE")
    to_node_id: uuid.UUID = Field(foreign_key="storynode.id", nullable=False, ondelete="CASCADE")

    # Relationships defined after all models
    # from_node: "StoryNode" = Relationship(back_populates="choices_from")
    # to_node: "StoryNode" = Relationship(back_populates="choices_to")


class NodeChoicePublic(NodeChoiceBase):
    """Public API response model for NodeChoice"""
    id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID


class NodeChoicesPublic(SQLModel):
    """Collection response for NodeChoices"""
    data: list[NodeChoicePublic]
    count: int


# ==================== StoryRequirement Models (AUTHORING) ====================

class StoryRequirementBase(SQLModel):
    """Base model for Story access requirements"""
    requirement_type: str = Field(max_length=50)  # "quality", "trait", etc.
    target_id: uuid.UUID  # The ID of the required quality/trait
    description: str | None = Field(default=None, max_length=255)


class StoryRequirementCreate(StoryRequirementBase):
    """Input model for creating a StoryRequirement"""
    story_id: uuid.UUID


class StoryRequirementUpdate(SQLModel):
    """Input model for updating StoryRequirement (all fields optional)"""
    requirement_type: str | None = Field(default=None, max_length=50)  # type: ignore
    target_id: uuid.UUID | None = Field(default=None)
    description: str | None = Field(default=None, max_length=255)  # type: ignore


class StoryRequirement(StoryRequirementBase, table=True):
    """
    Database model for StoryRequirement.
    Gates which UserPersonas can start a Story.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False, ondelete="CASCADE")

    # Relationships defined after all models
    # story: "Story" = Relationship(back_populates="requirements")


class StoryRequirementPublic(StoryRequirementBase):
    """Public API response model for StoryRequirement"""
    id: uuid.UUID
    story_id: uuid.UUID


class StoryRequirementsPublic(SQLModel):
    """Collection response for StoryRequirements"""
    data: list[StoryRequirementPublic]
    count: int


# ==================== UserStoryProgress Models (PLAYING) ====================

class UserStoryProgressBase(SQLModel):
    """
    Base model for tracking a player's progress through a Story.
    This is the player's instance - locked to a specific story version.
    """
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool = Field(default=False)

    # State accumulator - grows as player makes choices
    story_state: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class UserStoryProgressCreate(UserStoryProgressBase):
    """Input model for starting a Story (creating progress instance)"""
    user_persona_id: uuid.UUID
    story_id: uuid.UUID
    story_version: int  # Lock to this version at creation


class UserStoryProgressUpdate(SQLModel):
    """Input model for updating progress (all fields optional)"""
    current_node_id: uuid.UUID | None = Field(default=None)
    is_completed: bool | None = Field(default=None)
    story_state: dict[str, Any] | None = Field(default=None)
    #(for admin/debug only)
    head_choice_id: uuid.UUID | None = Field(default=None)
    head_version: int | None = Field(default=None)

class UserStoryProgress(UserStoryProgressBase, table=True):
    """
    Database model for player's Story instance.
    
    Key semantics:
    - Locked to story_version at creation (immutable)
    - References template StoryNodes via current_node_id
    - Accumulates state in story_state dict
    - Tracks history via UserNodeChoice records
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_persona_id: uuid.UUID = Field(foreign_key="userpersona.id", nullable=False, ondelete="CASCADE")
    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False, ondelete="CASCADE")
    story_version: int = Field(nullable=False)  # Locked at creation

    # NEW: Head pointer (active timeline position) - Phase 1
    head_choice_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="usernodechoice.id",
        description="Current active event in timeline tree (null = at story start)"
    )

    # Optimistic concurrency control
    head_version: int = Field(
        default=0,
        description="Increments on every head move (for optimistic locking)"
    )

    # Timestamps
    started_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # Relationships defined after all models
    # user_persona: "UserPersona" = Relationship(back_populates="story_progresses")
    # story: "Story" = Relationship(back_populates="user_progresses")
    # current_node: "StoryNode" = Relationship(back_populates="current_for_progresses")
    # choice_history: list["UserNodeChoice"] = Relationship(back_populates="progress")


class UserStoryProgressPublic(UserStoryProgressBase):
    """Public API response model for UserStoryProgress"""
    id: uuid.UUID
    user_persona_id: uuid.UUID
    story_id: uuid.UUID
    story_version: int
    head_choice_id: uuid.UUID | None  # NEW in Phase 1
    head_version: int  # NEW in Phase 1
    started_at: datetime
    updated_at: datetime


class UserStoryProgressesPublic(SQLModel):
    """Collection response for UserStoryProgresses"""
    data: list[UserStoryProgressPublic]
    count: int

# ==================== Timeline Navigation Models (Phase 3) ====================

class JumpRequest(SQLModel):
    """
    Request model for jumping to ancestor choice.

    Used by jump endpoint to specify target and optimistic concurrency check.
    """
    choice_id: uuid.UUID | None = Field(
        default=None,
        description="Target choice to jump to (null = jump to story start)"
    )
    expected_head_version: int = Field(
        description="Optimistic concurrency check - must match current head_version"
    )


class TimelineEvent(SQLModel):
    """
    Timeline entry for UI breadcrumbs.

    Represents a single event in the player's active timeline.
    Abandoned branches are NOT included in timeline responses.
    """
    choice_id: uuid.UUID | None = Field(
        description="Choice ID (null for story start event)"
    )
    choice_text: str = Field(description="Text of the choice made")
    node_title: str = Field(description="Title of the node reached")
    choice_time: datetime = Field(description="When choice was made")
    is_current: bool = Field(description="Is this the current head position?")


class Timeline(SQLModel):
    """
    Active timeline from root → head.

    Contains only the ancestor chain (root to current head).
    Siblings and abandoned branches are filtered out.
    """
    events: list[TimelineEvent]
    head_version: int = Field(description="Current head version for optimistic locking")


# NOTE: These are request/response models (not database models)
# so they don't need the full Base/Create/Update/Database/Public/Collection pattern per TinyFoot data-model-best-practices.md.
# ==================== UserNodeChoice Models (PLAYING) ====================

class UserNodeChoiceBase(SQLModel):
    """
    Base model for recording a player's choice at a node.
    Historical breadcrumb trail through the story.
    Choice text can be modified by Pydantic AI as necessary for summary.
    """
    choice_text: str = Field(max_length=1000)
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID

    # Snapshot of state changes applied by this choice
    state_changes: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class UserNodeChoiceCreate(UserNodeChoiceBase):
    """Input model for recording a choice"""
    progress_id: uuid.UUID
    parent_choice_id: uuid.UUID | None = Field(
        default=None,
        description="Parent event in timeline tree (null for initial state)"
    )

    rng_data: dict[str, Any] | None = Field(
        default=None,
        description="Captured RNG outcomes for deterministic replay"
    )

class UserNodeChoice(UserNodeChoiceBase, table=True):
    """
    Database model for player's choice history.
    parent_choice_id for tree structure and branching timelines
    Immutable record of decisions made.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(foreign_key="userstoryprogress.id", nullable=False, ondelete="CASCADE")

    parent_choice_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="usernodechoice.id",
        description="Parent event in timeline tree (null for initial state)"
    )

    choice_time: datetime = Field(default_factory=datetime.now)

    # Relationships defined after all models
    # progress: "UserStoryProgress" = Relationship(back_populates="choice_history")
    # from_node: "StoryNode" = Relationship()
    # to_node: "StoryNode" = Relationship()
    rng_data: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Captured RNG outcomes for deterministic replay (seeds, rolls, outcomes)"
    )

class UserNodeChoicePublic(UserNodeChoiceBase):
    """Public API response model for UserNodeChoice"""
    id: uuid.UUID
    progress_id: uuid.UUID
    parent_choice_id: uuid.UUID | None  # NEW in Phase 1
    choice_time: datetime
    rng_data: dict[str, Any] | None
    state_changes: dict[str, Any] | None


class UserNodeChoicesPublic(SQLModel):
    """Collection response for UserNodeChoices"""
    data: list[UserNodeChoicePublic]
    count: int

class UserNodeChoiceUpdate(SQLModel):
    """
    Update model for UserNodeChoice.
    Note: In event sourcing, choices are immutable - this exists for consistency
    but should rarely/never be used.
    """
    choice_text: str | None = Field(default=None, max_length=1000)  # type: ignore
    state_changes: dict[str, Any] | None = Field(default=None)
    rng_data: dict[str, Any] | None = Field(default=None)

# ========= Database Models ===========


class ArchetypeTraitLink(ArchetypeTraitLinkBase, table=True):
    """
    Database model for the many-to-many relationship between Archetypes and Traits.
    Relationships will be defined after all models are declared.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class ArchetypePersonaLink(ArchetypePersonaLinkBase, table=True):
    """
    Database model for the one-to-many relationship between Archetypes and Personas.
    Relationships are be defined after model declaration.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class ArchetypeQualityLink(ArchetypeQualityLinkBase, table=True):
    """
    Database model for the one-to-many relationship between Archetypes and Personas.
    Relationships are be defined after model declaration.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class PersonaTraitLink(PersonaTraitLinkBase, table=True):
    """
    Database model for the many-to-many relationship between Personas and Traits.
    Relationships will be defined after all models are declared.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # If inherited, track which Archetype it came from
    source_archetype_id: uuid.UUID | None = Field(
        default=None, foreign_key="archetype.id"
    )


class PersonaQualityLink(PersonaQualityLinkBase, table=True):
    """
    database model for many-to-many relationship between Personas and Qualities.
    relationships defined post model declaration.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    # if quality is trait dependent
    source_trait_id: uuid.UUID | None = Field(default=None, foreign_key="trait.id")
    # if a quality is inherited from an archetype
    source_archetype_id: uuid.UUID | None = Field(
        default=None, foreign_key="archetype.id"
    )


class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# ============================================================================
# Minimal RBAC + User Groups (Phase 0)
# ============================================================================


class UserGroupBase(SQLModel):
    """User-owned group used as a share target."""

    name: str = Field(min_length=1, max_length=100)


class UserGroupCreate(UserGroupBase):
    """Input model for creating a user group."""

    pass


class UserGroupUpdate(SQLModel):
    """Update model for user groups (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)


class UserGroup(UserGroupBase, table=True):
    """Database model for user-owned groups."""

    __tablename__ = "user_groups"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_user_groups_owner_name"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserGroupPublic(UserGroupBase):
    """Public API response model for a user group."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime


class UserGroupsPublic(SQLModel):
    """Collection response for user groups."""

    data: list[UserGroupPublic]
    count: int


class UserGroupMembershipBase(SQLModel):
    """Shared properties for group memberships."""

    role: UserGroupMembershipRole = Field(default=UserGroupMembershipRole.member)


class UserGroupMembershipCreate(UserGroupMembershipBase):
    """Input model for adding a user to a group."""

    user_id: uuid.UUID


class UserGroupMembership(UserGroupMembershipBase, table=True):
    """Database model for group memberships."""

    __tablename__ = "user_group_memberships"
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_user_group_memberships_group_user"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="user_groups.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserGroupMembershipPublic(UserGroupMembershipBase):
    """Public API response model for group memberships."""

    id: uuid.UUID
    group_id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class UserGroupMembershipsPublic(SQLModel):
    """Collection response for group memberships."""

    data: list[UserGroupMembershipPublic]
    count: int


class PersonaGroupBase(SQLModel):
    """Persona-owned collaboration container."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    group_type: PersonaGroupType = Field(default=PersonaGroupType.group)
    is_active: bool = Field(default=True)


class PersonaGroupCreate(PersonaGroupBase):
    """Input model for creating a persona group."""

    owner_user_persona_id: uuid.UUID


class PersonaGroupUpdate(SQLModel):
    """Update model for persona groups (all fields optional)."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class PersonaGroup(PersonaGroupBase, table=True):
    """Database model for persona-mediated collaboration groups/workspaces."""

    __tablename__ = "persona_groups"
    __table_args__ = (
        UniqueConstraint(
            "owner_user_persona_id",
            "name",
            name="uq_persona_groups_owner_persona_name",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class PersonaGroupPublic(PersonaGroupBase):
    """Public API response model for a persona group."""

    id: uuid.UUID
    owner_user_persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PersonaGroupsPublic(SQLModel):
    """Collection response for persona groups."""

    data: list[PersonaGroupPublic]
    count: int


class PersonaGroupMembershipBase(SQLModel):
    """Shared properties for persona-group memberships."""

    role: UserGroupMembershipRole = Field(default=UserGroupMembershipRole.member)
    is_active: bool = Field(default=True)


class PersonaGroupMembershipCreate(PersonaGroupMembershipBase):
    """Input model for adding a user persona to a persona group."""

    user_persona_id: uuid.UUID


class PersonaGroupMembershipUpdate(SQLModel):
    """Update model for persona-group memberships."""

    role: UserGroupMembershipRole | None = None
    is_active: bool | None = None


class PersonaGroupMembership(PersonaGroupMembershipBase, table=True):
    """Database model for persona-mediated group membership."""

    __tablename__ = "persona_group_memberships"
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_persona_id",
            name="uq_persona_group_memberships_group_user_persona",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(
        foreign_key="persona_groups.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    user_persona_id: uuid.UUID = Field(
        foreign_key="userpersona.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class PersonaGroupMembershipPublic(PersonaGroupMembershipBase):
    """Public API response model for persona-group memberships."""

    id: uuid.UUID
    group_id: uuid.UUID
    user_persona_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class PersonaGroupMembershipsPublic(SQLModel):
    """Collection response for persona-group memberships."""

    data: list[PersonaGroupMembershipPublic]
    count: int


class AccessGrantBase(SQLModel):
    """Shared properties for object-scoped access grants."""

    resource_type: str = Field(min_length=1, max_length=50, index=True)
    resource_id: uuid.UUID = Field(index=True)

    subject_type: AccessGrantSubjectType
    subject_id: uuid.UUID

    role: AccessGrantRole = Field(default=AccessGrantRole.viewer)


class AccessGrantCreate(AccessGrantBase):
    """Input model for creating an access grant."""

    pass


class AccessGrant(AccessGrantBase, table=True):
    """Database model for object-scoped access grants."""

    __tablename__ = "access_grants"
    __table_args__ = (
        UniqueConstraint(
            "resource_type",
            "resource_id",
            "subject_type",
            "subject_id",
            name="uq_access_grants_resource_subject",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    granted_by_user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AccessGrantPublic(AccessGrantBase):
    """Public API response model for an access grant."""

    id: uuid.UUID
    granted_by_user_id: uuid.UUID
    created_at: datetime


class AccessGrantsPublic(SQLModel):
    """Collection response for access grants."""

    data: list[AccessGrantPublic]
    count: int


class AccessEffectiveRolePublic(SQLModel):
    """Effective role for the current user on a resource."""

    resource_type: str
    resource_id: uuid.UUID
    role: AccessGrantRole | None


class ResolvedUserPageAudiencePublic(SQLModel):
    """Resolved visitor audience context for a user page."""

    scope: AudienceScope
    is_owner: bool = False
    matched_user_ids: list[uuid.UUID] = Field(default_factory=list)
    matched_user_persona_ids: list[uuid.UUID] = Field(default_factory=list)
    matched_group_ids: list[uuid.UUID] = Field(default_factory=list)
    matched_persona_group_ids: list[uuid.UUID] = Field(default_factory=list)
    matched_audience_keys: list[str] = Field(default_factory=list)


class AccessGrantUpsertRequest(SQLModel):
    """
    Request model for granting access to a resource.

    View-only is the default role.
    """

    subject_type: AccessGrantSubjectType
    subject_id: uuid.UUID
    role: AccessGrantRole = Field(default=AccessGrantRole.viewer)


class AccessGrantRevokeRequest(SQLModel):
    """Request model for revoking access to a resource."""

    subject_type: AccessGrantSubjectType
    subject_id: uuid.UUID


# ============================================================================
# Projects Container (Workspace) — Phase 0
# ============================================================================


class ProjectBase(SQLModel):
    """User-owned collaboration container for attaching resources."""

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=1000)


class Project(ProjectBase, table=True):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_projects_owner_name"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectPublic(ProjectBase):
    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ProjectsPublic(SQLModel):
    data: list[ProjectPublic]
    count: int


class ProjectResourceBase(SQLModel):
    """Attachment row linking a project to a resource."""

    resource_type: str = Field(min_length=1, max_length=50, index=True)
    resource_id: uuid.UUID = Field(index=True)


class ProjectResourceCreate(ProjectResourceBase):
    pass


class ProjectResource(ProjectResourceBase, table=True):
    __tablename__ = "project_resources"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "resource_type",
            "resource_id",
            name="uq_project_resources_project_resource",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    project_id: uuid.UUID = Field(
        foreign_key="projects.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProjectResourcePublic(ProjectResourceBase):
    id: uuid.UUID
    project_id: uuid.UUID
    created_at: datetime


class ProjectResourcesPublic(SQLModel):
    data: list[ProjectResourcePublic]
    count: int


class FrontierAccessProviderBase(SQLModel):
    """Model for holding frontier model access providers for cloning and updates"""
    base_url: str | None = Field(default=None, max_length=100, description="Endpoint URL")
    testing_api_key: str | None = Field(min_length=1, description="Plain text API key for testing endpoint (will be encrypted)")
    name: str = Field(max_length=100, description="name of the FAP")
    provider_type_id: uuid.UUID
    is_enabled: bool = Field(default=True, description="Whether this provider is active")
    is_visible: bool = Field(default=False, description="is this shared for people to clone?")
    is_deprecated: bool =   Field(default=False, description="are people still allowed to clone")
    description: str | None = Field(default=None, max_length=500)

class FrontierAccessProviderCreate(FrontierAccessProviderBase):
    """Input model for creating provider """
    pass

class FrontierAccessProviderBasePartial(SQLModel):
    """base model for FAP fields that can be updated.  all optional."""
    name: str | None = Field(default=None, max_length=100)
    is_enabled: bool | None = None
    is_default: bool | None = None
    is_validated: bool | None = None
    base_url: str | None = Field(default=None, max_length=500)
    provider_type_id: uuid.UUID | None
    description: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, description="New API key to encrypt, if changing")


class FrontierAccessProviderUpdate(FrontierAccessProviderBasePartial):
    """Update model - all fields optional."""
    pass

class FrontierAccessProvider(FrontierAccessProviderBase, table=True):
    """
    Database model for frontier access provider configurations.
    Stores encrypted frontier access keys for test and validation.

    """
    __tablename__ = "frontier_access_provider"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    provider_type_id: uuid.UUID = Field(
        foreign_key="provider_type.id",
        nullable=False,
        index=True,
        description="API base (anthropic, google, openai, openai_compatible, multiple, custom, empty)"
    )

class FrontierAccessProviderPublic(FrontierAccessProviderBase):
    """Public API response - NEVER includes API key."""
    id: uuid.UUID

class FrontierAccessProvidersPublic(SQLModel):
    """Collection response for FrontierAccessProviders."""
    data: list[FrontierAccessProviderPublic]
    count: int


# ==================== UserAccessProviders Models ====================
#

class UserAccessProviderBase(SQLModel):
    """Base model for user LLM access provider and API key configurations."""
    api_key: str | None = Field(default=None, description="New API key to encrypt, if changing")
    owner_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    base_url: str | None = Field(default=None, max_length=100, description="Endpoint URL")
    name: str = Field(max_length=100, description="User-friendly name like 'My OpenAI' or 'Work Azure'")
    provider_type_multiple: bool = Field(default=False, description="if there's more than one provider type.")
    alpha_provider_type_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    is_enabled: bool = Field(default=True, description="Whether this provider is active")
    is_default: bool = Field(default=False, description="is this the user's default access provider?")
    is_validated: bool =Field(default=False, description="has this api key and url been tested?")
    description: str | None = Field(default=None, max_length=500)

    # Adapter configuration fields
    timeout_seconds: int = Field(default=30, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry count for failed requests")
    retry_delay_ms: int = Field(default=1000, description="Base delay between retries in milliseconds")
    proxy_url: str | None = Field(default=None, max_length=255, description="Optional HTTP proxy URL")

    # Validation state fields
    last_validated_at: datetime | None = Field(default=None, description="Timestamp of last successful validation")
    validation_error: str | None = Field(default=None, max_length=1000, description="Last validation error message")

    # Provider-specific config and headers (JSON in table model)
    provider_config: dict[str, Any] | None = Field(
        default=None,
        description="Provider-specific settings (org_id, deployment_name, etc.)",
    )
    custom_headers: dict[str, Any] | None = Field(
        default=None,
        description="Additional HTTP headers for API requests",
    )

    # Model cache (JSON in table model)
    available_models_cache: list[str] | None = Field(
        default=None,
        description="Cached list of available models from provider API",
    )
    models_cached_at: datetime | None = Field(
        default=None,
        description="When the models cache was last refreshed",
    )

class UserAccessProviderCreate(UserAccessProviderBase):
    """Input model for creating provider"""
    pass

class UserAccessProviderBasePartial(SQLModel):
    """Update model - all fields optional."""
    name: str | None = Field(default=None, max_length=100)
    is_enabled: bool | None = None
    is_default: bool | None = None
    is_validated: bool | None = None
    # users validate an access provider by pushing the 'Test' button on the front end
    base_url: str | None = Field(default=None, max_length=500)
    description: str | None = Field(default=None, max_length=500)
    api_key: str | None = Field(default=None, description="New API key to encrypt, if changing")
    alpha_provider_type_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    # Adapter configuration fields (optional for updates)
    provider_config: dict[str, Any] | None = None
    timeout_seconds: int | None = None
    max_retries: int | None = None
    retry_delay_ms: int | None = None
    proxy_url: str | None = Field(default=None, max_length=255)
    custom_headers: dict[str, Any] | None = None

    # Validation state fields (optional for updates)
    last_validated_at: datetime | None = None
    validation_error: str | None = Field(default=None, max_length=1000)
    available_models_cache: list[str] | None = None
    models_cached_at: datetime | None = None

class UserAccessProviderUpdate(UserAccessProviderBasePartial):
    pass

class UserAccessProvider(UserAccessProviderBase, table=True):
    """
    Database model for user access provider configurations.

    Stores encrypted API keys per-user. Each user can have multiple
    providers of the same type (e.g., personal and work OpenAI keys).
    """
    __tablename__ = "user_access_provider"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    alpha_provider_type_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        foreign_key="provider_type.id",
        nullable=False,
        index=True,
        description="api base (anthropic, google, openai, openai_compatible, multiple, custom, empty)"
    )

    # JSON fields that need sa_column for database storage
    provider_config: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Provider-specific settings (org_id, deployment_name, etc.)"
    )
    custom_headers: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Additional HTTP headers for API requests"
    )
    available_models_cache: list[str] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Cached list of available models from provider API"
    )
    models_cached_at: datetime | None = Field(
        default=None,
        description="Timestamp when models cache was last refreshed"
    )

class UserAccessProviderPublic(SQLModel):
    """Public API response - NEVER includes API key."""
    id: uuid.UUID
    owner_id: uuid.UUID
    base_url: str | None = None
    name: str
    provider_type_multiple: bool = False
    alpha_provider_type_id: uuid.UUID
    is_enabled: bool = True
    is_default: bool = False
    is_validated: bool = False
    description: str | None = None

    # Adapter configuration fields
    provider_config: dict[str, Any] | None = None
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_ms: int = 1000
    proxy_url: str | None = None
    custom_headers: dict[str, Any] | None = None

    # Validation state fields
    last_validated_at: datetime | None = None
    validation_error: str | None = None
    available_models_cache: list[str] | None = None
    models_cached_at: datetime | None = None


class UserAccessProvidersPublic(SQLModel):
    """Collection response for UserAccessProviders."""
    data: list[UserAccessProviderPublic]
    count: int


class LLMProviderTypeBase(SQLModel):
    """Table that holds all the different provider types fk many to one to many relationships"""
    name: str = Field(max_length=30, description="LLM Provider type")
    details: str | None  = Field(default=None, max_length=500, description="notes if necessary")
    validated: bool = Field(default=False, description="updated when proven valid at least once")
    is_system: bool = Field(default=False, description="is this a system-level provider type?")

    # Template gallery fields
    category: str = Field(
        default="custom",
        max_length=30,
        description="Provider category: major | cloud | self_hosted | custom"
    )
    display_name: str = Field(
        default="",
        max_length=100,
        description="User-friendly name like 'OpenAI'"
    )
    logo_url: str | None = Field(
        default=None,
        max_length=255,
        description="Path to provider logo"
    )
    docs_url: str | None = Field(
        default=None,
        max_length=255,
        description="Link to provider documentation"
    )
    default_base_url: str | None = Field(
        default=None,
        max_length=255,
        description="Default API endpoint"
    )
    config_schema: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="JSON Schema for provider-specific fields"
    )
    sort_order: int = Field(
        default=0,
        description="Display ordering within category"
    )

class LLMProviderTypeCreate(LLMProviderTypeBase):
    """Input model for creating an LLMProviderType"""
    pass

class LLMProviderTypeBasePartial(SQLModel):
    """Update model for LLM Provider types"""
    name: str | None = Field(max_length=30, description="LLM Provider type", default=None)
    details: str | None = Field(default=None, max_length=500, description="notes if necessary")
    validated: bool | None = Field(default=None, description="updated when proven valid at least once",)
    is_system: bool | None = Field(default=None, description="is this a validated provider_type?" )

    # Template gallery fields (all optional for updates)
    category: str | None = Field(
        default=None,
        max_length=30,
        description="Provider category: major | cloud | self_hosted | custom"
    )
    display_name: str | None = Field(
        default=None,
        max_length=100,
        description="User-friendly name like 'OpenAI'"
    )
    logo_url: str | None = Field(
        default=None,
        max_length=255,
        description="Path to provider logo"
    )
    docs_url: str | None = Field(
        default=None,
        max_length=255,
        description="Link to provider documentation"
    )
    default_base_url: str | None = Field(
        default=None,
        max_length=255,
        description="Default API endpoint"
    )
    config_schema: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="JSON Schema for provider-specific fields"
    )
    sort_order: int | None = Field(
        default=None,
        description="Display ordering within category"
    )

class LLMProviderTypeUpdate(LLMProviderTypeBasePartial):
    pass

class LLMProviderType(LLMProviderTypeBase, table=True):
    __tablename__ = "provider_type"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

class LLMProviderTypePublic(LLMProviderTypeBase):
    """public api response"""
    id: uuid.UUID

class LLMProviderTypesPublic(SQLModel):
    """collection response"""
    data: list[LLMProviderTypePublic]
    count: int

class LLMModelBase(SQLModel):
    """Base model for LLM model catalog entries."""
    owner_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    model_id: str = Field(max_length=100, description="Model identifier (e.g., 'gpt-4o', no provider prefix)")
    display_name: str = Field(max_length=100, description="Human-friendly name (e.g., 'GPT 4o')")
    primary_provider_type_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    multiple_provider_type_support: bool = Field(default=False, description="this overload might be neat in the future for swapping?")
    description: str | None = Field(default=None, max_length=500)
    context_window: int | None = Field(default=None, description="Max tokens in context window")
    is_default: bool = Field(default=False, description="Default/cheapest model for this provider")
    is_enabled: bool = Field(default=True, description="Whether model is available for use")
    is_deprecated: bool = Field(default=False, description="Model is deprecated (still works)")
    sort_order: int = Field(default=0, description="Display ordering within provider")
    is_system: bool = Field(default=False, index=True, description="system level model")

    # Known capabilities (nullable = unknown)
    has_vision: bool | None = Field(default=None, description="Supports image input")
    has_function_calling: bool | None = Field(default=None, description="Supports function/tool calling")
    has_streaming: bool | None = Field(default=None, description="Supports streaming responses")
    has_json_mode: bool | None = Field(default=None, description="Supports JSON output mode")

    # Additional capabilities as JSON for extensibility
    secondary_capabilities: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )


class LLMModelCreate(LLMModelBase):
    """Input model for creating a model catalog entry."""
    pass

class LLMModelBasePartial(SQLModel):
    """Update model for model catalog entries - all fields optional."""
    primary_provider_type_id: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    display_name: str | None = Field(default=None, max_length=100, description="so much effery")
    description: str | None = Field(default=None, max_length=500)
    context_window: int | None = Field(default=None, description="Max tokens in context window")
    is_default: bool | None = Field(default=None, description="Default/cheapest model for this provider")
    is_enabled: bool | None = Field(default=None, description="Whether model is available for use")
    is_deprecated: bool | None = Field(default=None, description="Model is deprecated (still works)")
    sort_order: int | None = Field(default=None, description="Display ordering within provider")
    has_vision: bool | None = Field(default=None, description="Supports image input")
    has_function_calling: bool | None = Field(default=None, description="Supports function/tool calling")
    has_streaming: bool | None = Field(default=None, description="Supports streaming responses")
    has_json_mode: bool | None = Field(default=None, description="Supports JSON output mode")
    secondary_capabilities: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )

class LLMModelUpdate(LLMModelBasePartial):
    """update model, all fields optional"""
    pass


class LLMModel(LLMModelBase, table=True):
    """
    Database model for LLM model catalog.

    Stores available models per provider with their capabilities.
    model_id is the normalized name without provider prefix (e.g., 'gpt-4o').
    """
    __tablename__ = "llmmodel"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    primary_provider_type_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        foreign_key="provider_type.id",
        nullable=False,
        index=True,
        description="API base provider (anthropic, google, openai, openai_compatible, custom, empty)"
    )
        # Fields inherited: model_id, primary_provider_type_id
    __table_args__ = (
        UniqueConstraint("primary_provider_type_id", "model_id",
                        name="uq_llmmodel_provider_model"),
    )


class LLMModelPublic(LLMModelBase):
    """Public API response for a model catalog entry."""
    id: uuid.UUID
    primary_provider_type_id: uuid.UUID


class LLMModelsPublic(SQLModel):
    """Collection response for LLMModels."""
    data: list[LLMModelPublic]
    count: int


class LLMModelPublicWithPinStatus(LLMModelPublic):
    """
    Public API response for a model catalog entry with pin status.

    Extends LLMModelPublic with optional pin information for the current user.
    Pin fields are only populated when include_pin_status=true and user is authenticated.
    """
    is_pinned: bool = Field(default=False, description="Whether the model is pinned by the current user")
    pin_sort_order: int | None = Field(default=None, description="Sort order of the pin (if pinned)")


class LLMModelsPublicWithPinStatus(SQLModel):
    """Collection response for LLMModels with pin status."""
    data: list[LLMModelPublicWithPinStatus]
    count: int


# ==================== UserModelPin Models ====================
# Junction table for user-pinned favorite LLM models
# Allows users to pin/favorite models for quick access


class UserModelPinBase(SQLModel):
    """Base model for user model pins."""

    sort_order: int = Field(default=0, description="Sort order for pinned models")


class UserModelPinCreate(UserModelPinBase):
    """Create model for user model pins."""

    llm_model_id: uuid.UUID = Field(description="The LLM model to pin")


class UserModelPin(UserModelPinBase, table=True):
    """
    Database model for user-pinned LLM models.

    Junction table allowing users to pin/favorite specific LLM models
    for quick access. Each user can pin a model only once.
    """

    __tablename__ = "user_model_pin"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "llm_model_id", name="uq_user_model_pin_user_model"
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
        description="User who pinned the model",
    )
    llm_model_id: uuid.UUID = Field(
        foreign_key="llmmodel.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
        description="The pinned LLM model",
    )
    pinned_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="When the model was pinned",
    )


class UserModelPinPublic(UserModelPinBase):
    """Public API response for a user model pin."""

    id: uuid.UUID
    user_id: uuid.UUID
    llm_model_id: uuid.UUID
    pinned_at: datetime


class UserModelPinsPublic(SQLModel):
    """Collection response for user model pins."""

    data: list[UserModelPinPublic]
    count: int


class UserModelPinReorderItem(SQLModel):
    """Single item for reordering a user model pin."""

    llm_model_id: uuid.UUID = Field(description="The pinned LLM model to reorder")
    sort_order: int = Field(description="New sort order for this pin")


class UserModelPinReorder(SQLModel):
    """Request body for reordering user model pins."""

    order: list[UserModelPinReorderItem] = Field(
        description="List of pins with their new sort orders"
    )


class Event(EventBase, table=True):
    """Database model for events."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Archetype(ArchetypeBase, table=True):
    """
    Database model for Archetype.
    Relationships are defined after model declarations.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    # The traits relationship will be defined later


class Persona(PersonaBase, table=True):
    """
    Database model for Persona.
    Relationships defined after model declarations.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Quality(QualityBase, table=True):
    """
    Database model for Quality.
    Relationships defined after model declarations.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class Trait(TraitBase, table=True):
    """
    Database model for Trait.
    Relationships will be defined after all models are declared.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)


class QualityTraitLink(QualityTraitLinkBase, table=True):
    """
    Database model for the many-to-many relationship between Qualities and Traits.
    Defines which Qualities are automatically associated with which Traits.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

    # Define whether this Quality is automatically enabled when the Trait is present
    auto_enable: bool = Field(default=True)

    # Define the requirement level of this Quality for the Trait
    is_required: bool = Field(default=False)


# ========== api models for quality trait link special case ======


class QualityTraitLinkCreate(QualityTraitLinkBase):
    auto_enable: bool = Field(default=True)
    is_required: bool = Field(default=False)


class QualityTraitLinkUpdate(SQLModel):
    auto_enable: bool = Field(default=True)
    is_required: bool = Field(default=None)


# ========== Public Models ========


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class EventPublic(EventBase):
    """Public model for Event API responses."""

    id: uuid.UUID
    created_at: datetime


class ArchetypePublic(ArchetypeBase):
    """Public model for Archetype API responses."""

    id: uuid.UUID
    created_at: datetime


class PersonaPublic(PersonaBase):
    """Public model for Persona API responses."""

    id: uuid.UUID
    created_at: datetime


class TraitPublic(TraitBase):
    """Public model for Trait API responses."""

    id: uuid.UUID
    created_at: datetime


class QualityPublic(QualityBase):
    """Public model for Quality API responses."""

    id: uuid.UUID
    created_at: datetime


# ============ Public collection models for API requests ==============


class UsersPublic(SQLModel):
    """Collection model for User API responses."""

    data: list[UserPublic]
    count: int


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


class EventsPublic(SQLModel):
    """Collection model for Event API responses."""

    data: list[EventPublic]
    count: int


class ArchetypesPublic(SQLModel):
    """Collection model for Archetype API responses."""

    data: list[ArchetypePublic]
    count: int


class PersonasPublic(SQLModel):
    """Collection model for Personas API responses."""

    data: list[PersonaPublic]
    count: int


class TraitsPublic(SQLModel):
    """Collection model for Trait API responses."""

    data: list[TraitPublic]
    count: int


class QualitiesPublic(SQLModel):
    """Collection model for Quality API responses."""

    data: list[QualityPublic]
    count: int


# need to understand union models - ephemeral, dynamic, and static?

# ====== QualityTraitLink and QualityEvent classes need to go here after the above class declarations


class QualityTraitLinkPublic(QualityTraitLinkBase):
    id: uuid.UUID
    created_at: datetime
    auto_enable: bool
    is_required: bool

    # including ids - there was a strange sqlmodel issue with relationship defs
    trait_id: uuid.UUID
    quality_id: uuid.UUID

    # leaving these optional nested objects that can be loaded separately
    trait: TraitPublic | None = None
    quality: QualityPublic | None = None


class QualityEventTriggerCreate(QualityEventTriggerBase):
    condition_json: str | None = Field(default=None)


class QualityEventTriggerUpdate(SQLModel):
    new_state: QualityState | None = Field(default=None)
    condition_json: str | None = Field(default=None)


class QualityEventTriggerPublic(QualityEventTriggerBase):
    id: uuid.UUID
    created_at: datetime
    condition_json: str | None
    event: EventPublic | None = None
    quality: QualityPublic | None = None

# potential duplicate - exception of sa_column defintions
# class NodeChoiceBaseOld?(SQLModel):
#     """Base model for NodeChoice (decision branch in story template)"""

#     text: str = Field(min_length=1, max_length=500)
#     order: int = Field(default=0)

#     # State management for conditional branches
#     requires_state: dict[str, Any] | None = Field(default=None)  # Conditions to show this choice
#     sets_state: dict[str, Any] | None = Field(default=None)  # State changes when chosen


class StoryUserLinkBase(SQLModel):
    story_id: uuid.UUID = Field(foreign_key="story.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")



class StoryBasePartial(SQLModel):
    """Base model for story fields that can be updated (all optional)"""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    is_published: bool | None = Field(default=None)


class StoryNodePartial(SQLModel):
    """Base model for story fields that can be updated (all optional)"""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    content: str | None = Field(default=None)
    node_type: str | None = Field(default=None, max_length=50)
    content_format: ContentFormat | None = Field(default=ContentFormat.TEXT)
    is_start_node: bool | None = Field(default=None)
    is_end_node: bool | None = Field(default=None)
    # metadata: dict | None = Field(default=None)


class NodeChoiceBasePartial(SQLModel):
    """Base model for node choice fields that can be updated, all optional"""

    text: str = Field(min_length=1, max_length=500)
    order: int | None = Field(default=0)
    requires_state: dict | None = Field(
        default=None
    )  # JSON field for required state variables
    sets_state: dict | None = Field(
        default=None
    )  # JSON field for  state variables to set


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


class DemoConfigScope(str, PyEnum):
    system = "system"
    personal = "personal"
    shared = "shared"


class DemoSessionStatus(str, PyEnum):
    active = "active"
    archived = "archived"
    ended = "ended"


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



class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=50, unique=True)
    color: str | None = Field(default=None, max_length=20)


class TagBasePartial(SQLModel):
    name: str = Field(min_length=1, max_length=50, unique=True)
    color: str | None = Field(default=None, max_length=20)


class TagPublic(TagBase):
    id: uuid.UUID


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int


# Create model for Tag
class TagCreate(TagBase):
    pass


# Update model for Tag
class TagUpdate(TagBasePartial):
    pass


# Database model for Tag
class Tag(TagBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class SvgAssetBase(SQLModel):
    """Shared validated contract for SVG assets."""

    visibility: SvgAssetVisibility = Field(default=SvgAssetVisibility.PRIVATE, index=True)
    name: str = Field(min_length=1, max_length=255, index=True)
    description: str | None = Field(default=None, max_length=2000)
    svg_markup: str = Field(min_length=1)
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
        description="Arbitrary metadata for model/prompt/style provenance.",
    )
    source_private_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="svgasset.id",
        index=True,
    )

    @field_validator("svg_markup")
    @classmethod
    def validate_svg_markup(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("svg_markup cannot be empty")
        lower = normalized.lower()
        if "<svg" not in lower or "</svg>" not in lower:
            raise ValueError("svg_markup must include a valid <svg> root element")
        return v

    @model_validator(mode="after")
    def validate_visibility_source_pair(self) -> "SvgAssetBase":
        if self.visibility == SvgAssetVisibility.PUBLIC and self.source_private_id is None:
            raise ValueError("source_private_id is required when visibility is public")
        if self.visibility == SvgAssetVisibility.PRIVATE and self.source_private_id is not None:
            raise ValueError("source_private_id must be null when visibility is private")
        return self


class SvgAssetCreatePrivate(SQLModel):
    """Input contract for creating a private SVG asset."""

    visibility: Literal[SvgAssetVisibility.PRIVATE] = Field(default=SvgAssetVisibility.PRIVATE)
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    svg_markup: str = Field(min_length=1)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("svg_markup")
    @classmethod
    def validate_svg_markup(cls, v: str) -> str:
        normalized = v.strip()
        if not normalized:
            raise ValueError("svg_markup cannot be empty")
        lower = normalized.lower()
        if "<svg" not in lower or "</svg>" not in lower:
            raise ValueError("svg_markup must include a valid <svg> root element")
        return v


class SvgAssetCreatePublicFromPrivate(SQLModel):
    """Input contract for creating a public copy from an existing private asset."""

    visibility: Literal[SvgAssetVisibility.PUBLIC] = Field(default=SvgAssetVisibility.PUBLIC)
    source_private_id: uuid.UUID
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    metadata_json: dict[str, Any] | None = None


SvgAssetCreate = Annotated[
    SvgAssetCreatePrivate | SvgAssetCreatePublicFromPrivate,
    Field(discriminator="visibility"),
]


class SvgAssetUpdate(SQLModel):
    """Patch contract for SVG assets."""

    visibility: SvgAssetVisibility | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)
    svg_markup: str | None = Field(default=None, min_length=1)
    metadata_json: dict[str, Any] | None = None
    source_private_id: uuid.UUID | None = None

    @field_validator("svg_markup")
    @classmethod
    def validate_svg_markup(cls, v: str | None) -> str | None:
        if v is None:
            return v
        normalized = v.strip()
        if not normalized:
            raise ValueError("svg_markup cannot be empty")
        lower = normalized.lower()
        if "<svg" not in lower or "</svg>" not in lower:
            raise ValueError("svg_markup must include a valid <svg> root element")
        return v

    @model_validator(mode="after")
    def validate_visibility_source_pair(self) -> "SvgAssetUpdate":
        if self.visibility is None:
            return self
        source_was_provided = "source_private_id" in self.model_fields_set
        if (
            self.visibility == SvgAssetVisibility.PUBLIC
            and source_was_provided
            and self.source_private_id is None
        ):
            raise ValueError("source_private_id is required when visibility is public")
        if self.visibility == SvgAssetVisibility.PRIVATE and self.source_private_id is not None:
            raise ValueError("source_private_id must be null when visibility is private")
        return self


class SvgAsset(SvgAssetBase, table=True):
    """Database model for persisted SVG assets."""

    __tablename__ = "svgasset"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        index=True,
    )


class SvgAssetPublic(SvgAssetBase):
    """Public API response model for SVG assets."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class SvgAssetsPublic(SQLModel):
    """Collection response model for SVG assets."""

    data: list[SvgAssetPublic]
    count: int


# Many-to-many relationship between Story and Tag
class StoryToTag(SQLModel, table=True):
    story_id: uuid.UUID = Field(
        foreign_key="story.id", primary_key=True, ondelete="CASCADE"
    )
    tag_id: uuid.UUID = Field(
        foreign_key="tag.id", primary_key=True, ondelete="CASCADE"
    )


# ---- StoryPlay Models for Tracking Game State ----


# Base model for StoryPlay
class StoryPlayBase(SQLModel):
    player_name: str | None = Field(default=None, max_length=255)
    is_completed: bool = Field(default=False)
    # state_data: dict | None = Field(default=None)  # JSON field for storing game state


# Create model for StoryPlay
class StoryPlayCreate(StoryPlayBase):
    story_id: uuid.UUID


class StoryPlayBasePartial(SQLModel):
    player_name: str | None = Field(default=None, max_length=255)
    is_completed: bool | None = Field(default=None)
    # state_data: dict | None = Field(default=None)


# Update model for StoryPlay
class StoryPlayUpdate(StoryPlayBasePartial):
    pass


# Database model for StoryPlay
class StoryPlay(StoryPlayBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    story_id: uuid.UUID = Field(
        foreign_key="story.id", nullable=False, ondelete="CASCADE"
    )
    user_id: uuid.UUID | None = Field(
        foreign_key="user.id", nullable=True, ondelete="SET NULL"
    )


# Public model for StoryPlay
class StoryPlayPublic(StoryPlayBase):
    id: uuid.UUID
    story_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_id: uuid.UUID | None


# Collection response for StoryPlays
class StoryPlaysPublic(SQLModel):
    data: list[StoryPlayPublic]
    count: int


# ---- PlayState Models for Tracking Node Visits ----


# Base model for PlayState
class PlayStateBase(SQLModel):
    visited_at: datetime = Field(default_factory=datetime.now)
    # state_data: dict | None = Field(default=None)  # JSON field for node-specific state


# Create model for PlayState
class PlayStateCreate(PlayStateBase):
    play_id: uuid.UUID
    node_id: uuid.UUID


# Update model for PlayState
class PlayStateUpdate(PlayStateBase):
    state_data: dict | None = Field(default=None)


# Database model for PlayState
class PlayState(PlayStateBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    play_id: uuid.UUID = Field(
        foreign_key="storyplay.id", nullable=False, ondelete="CASCADE"
    )
    node_id: uuid.UUID = Field(
        foreign_key="storynode.id", nullable=False, ondelete="CASCADE"
    )


# Public model for PlayState
class PlayStatePublic(PlayStateBase):
    id: uuid.UUID
    play_id: uuid.UUID
    node_id: uuid.UUID


# Collection response for PlayStates
class PlayStatesPublic(SQLModel):
    data: list[PlayStatePublic]
    count: int

class CurrentNodePublic(SQLModel):
    """
    Response model for getting current node with available choices.
    Used by players to understand their current position in a story.
    """
    node: StoryNodePublic
    available_choices: list[NodeChoicePublic]
    story_state: dict[str, Any] | None

# Story to StoryRequirement relationship
Story.requirements = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

# StoryRequirement to Story relationship
StoryRequirement.story = Relationship(back_populates="requirements")

# ==================== Define Relationships ====================

# User to UserPersona relationship
User.user_personas = Relationship(
    back_populates="user",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

# User to SvgAsset relationship
User.svg_assets = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

# UserPersona to User relationship
UserPersona.user = Relationship(back_populates="user_personas")

# SvgAsset to User relationship
SvgAsset.owner = Relationship(back_populates="svg_assets")

# SvgAsset self-referential copy lineage relationships
SvgAsset.source_private = Relationship(
    back_populates="public_copies",
    sa_relationship_kwargs={
        "foreign_keys": "[SvgAsset.source_private_id]",
        "remote_side": "[SvgAsset.id]",
    },
)
SvgAsset.public_copies = Relationship(
    back_populates="source_private",
    sa_relationship_kwargs={"foreign_keys": "[SvgAsset.source_private_id]"},
)

# Persona to UserPersona relationship
Persona.user_personas = Relationship(back_populates="persona")

# UserPersona to Persona relationship
UserPersona.persona = Relationship(back_populates="user_personas")

# UserPersona to UserStoryProgress relationship
UserPersona.story_progresses = Relationship(
    back_populates="user_persona",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

# UserStoryProgress to UserPersona relationship
UserStoryProgress.user_persona = Relationship(back_populates="story_progresses")

# Story to UserStoryProgress relationship
Story.user_progresses = Relationship(back_populates="story")

# UserStoryProgress to Story relationship
UserStoryProgress.story = Relationship(back_populates="user_progresses")

# StoryNode to UserStoryProgress relationship
StoryNode.current_for_progresses = Relationship(back_populates="current_node")

# UserStoryProgress to StoryNode relationship
UserStoryProgress.current_node = Relationship(back_populates="current_for_progresses")




# UserStoryProgress to UserNodeChoice relationship
UserStoryProgress.node_choices = Relationship(
    back_populates="progress",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)

# UserNodeChoice to UserStoryProgress relationship
UserNodeChoice.progress = Relationship(back_populates="node_choices")

# StoryNode relationships for from_node and to_node
UserNodeChoice.from_node = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[UserNodeChoice.from_node_id]"}
)
UserNodeChoice.to_node = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[UserNodeChoice.to_node_id]"}
)


# ============ Character System Relationships ============

# Archetype to Trait relationship
Archetype.traits = Relationship(
    back_populates="archetypes",
    link_model=ArchetypeTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Trait to Archetype relationship
Trait.archetypes = Relationship(
    back_populates="traits",
    link_model=ArchetypeTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Archetype to Persona relationship
Archetype.personas = Relationship(
    back_populates="archetypes",
    link_model=ArchetypePersonaLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Persona to Archetype relationship
Persona.archetypes = Relationship(
    back_populates="personas",
    link_model=ArchetypePersonaLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Archetype to Quality relationship
Archetype.qualities = Relationship(
    back_populates="archetypes",
    link_model=ArchetypeQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Quality to Archetype relationship
Quality.archetypes = Relationship(
    back_populates="qualities",
    link_model=ArchetypeQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Persona to Quality relationship
Persona.qualities = Relationship(
    back_populates="personas",
    link_model=PersonaQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Quality to Persona relationship
Quality.personas = Relationship(
    back_populates="qualities",
    link_model=PersonaQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Persona to Trait relationship
Persona.traits = Relationship(
    back_populates="personas",
    link_model=PersonaTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Trait to Persona relationship
Trait.personas = Relationship(
    back_populates="traits",
    link_model=PersonaTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Quality to Trait relationship
Quality.traits = Relationship(
    back_populates="qualities",
    link_model=QualityTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# Trait to Quality relationship
Trait.qualities = Relationship(
    back_populates="traits",
    link_model=QualityTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"},
)

# ============ Event System Relationships ============

# Event to QualityEventTrigger relationship
Event.quality_triggers = Relationship(back_populates="event")

# QualityEventTrigger to Event relationship
QualityEventTrigger.event = Relationship(back_populates="quality_triggers")

# QualityEventTrigger to Quality relationship
QualityEventTrigger.quality = Relationship(back_populates="event_triggers")

# Quality to QualityEventTrigger relationship
Quality.event_triggers = Relationship(back_populates="quality")

# ============ Link Model Relationships ============

# Link table to parent table relationships
ArchetypeTraitLink.archetype = Relationship(back_populates="trait_links")

ArchetypeTraitLink.trait = Relationship(back_populates="archetype_links")

ArchetypePersonaLink.archetype = Relationship(back_populates="persona_links")

ArchetypePersonaLink.persona = Relationship(back_populates="archetype_links")

ArchetypeQualityLink.archetype = Relationship(back_populates="quality_links")

ArchetypeQualityLink.quality = Relationship(back_populates="archetype_links")

PersonaTraitLink.persona = Relationship(back_populates="trait_links")

PersonaTraitLink.trait = Relationship(back_populates="persona_links")  # ty:ignore[unresolved-attribute]

PersonaQualityLink.persona = Relationship(back_populates="quality_links")

PersonaQualityLink.quality = Relationship(back_populates="persona_links")

QualityTraitLink.quality = Relationship(back_populates="trait_links")

QualityTraitLink.trait = Relationship(back_populates="quality_links")

# Source relationships for quality links (special case)
PersonaQualityLink.source_trait = Relationship()
PersonaQualityLink.source_archetype = Relationship()

# Parent table to link table backref relationships
Archetype.trait_links = Relationship(back_populates="archetype")

Trait.archetype_links = Relationship(back_populates="trait")

Archetype.persona_links = Relationship(back_populates="archetype")

Persona.archetype_links = Relationship(back_populates="persona")

Archetype.quality_links = Relationship(back_populates="archetype")

Quality.archetype_links = Relationship(back_populates="quality")

Persona.trait_links = Relationship(back_populates="persona")

Trait.persona_links = Relationship(back_populates="trait")

Persona.quality_links = Relationship(back_populates="persona")

Quality.persona_links = Relationship(back_populates="quality")

Quality.trait_links = Relationship(back_populates="quality")

Trait.quality_links = Relationship(back_populates="trait")


# Story relationships
Story.nodes = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
Story.requirements = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
Story.user_progresses = Relationship(back_populates="story")

# StoryNode relationships
StoryNode.story = Relationship(back_populates="nodes")
StoryNode.choices_from = Relationship(
    back_populates="from_node",
    sa_relationship_kwargs={
        "foreign_keys": "[NodeChoice.from_node_id]",
        "cascade": "all, delete-orphan"
    }
)
StoryNode.choices_to = Relationship(
    back_populates="to_node",
    sa_relationship_kwargs={"foreign_keys": "[NodeChoice.to_node_id]"}
)
StoryNode.current_for_progresses = Relationship(back_populates="current_node")

# NodeChoice relationships
NodeChoice.from_node = Relationship(
    back_populates="choices_from",
    sa_relationship_kwargs={"foreign_keys": "[NodeChoice.from_node_id]"}
)
NodeChoice.to_node = Relationship(
    back_populates="choices_to",
    sa_relationship_kwargs={"foreign_keys": "[NodeChoice.to_node_id]"}
)

# StoryRequirement relationships
StoryRequirement.story = Relationship(back_populates="requirements")

# UserStoryProgress relationships
UserStoryProgress.user_persona = Relationship(back_populates="story_progresses")
UserStoryProgress.story = Relationship(back_populates="user_progresses")
UserStoryProgress.current_node = Relationship(back_populates="current_for_progresses")
UserStoryProgress.choice_history = Relationship(
    back_populates="progress",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

# UserNodeChoice relationships
UserNodeChoice.progress = Relationship(back_populates="choice_history")
UserNodeChoice.from_node = Relationship(
    sa_relationship_kwargs={"foreign_keys": "[UserNodeChoice.from_node_id]"}
)
UserNodeChoice.to_node = Relationship(  # ty:ignore[unresolved-attribute]
    sa_relationship_kwargs={"foreign_keys": "[UserNodeChoice.to_node_id]"}
)


# Schemas for public trait configuration display and manipulation


class TraitConfigBase(SQLModel):
    is_modifiable: bool = Field(default=True)
    modifiable_at_creation_only: bool = Field(default=False)
    is_required: bool = Field(default=False)


class TraitConfigBasePartial(SQLModel):
    """Base model for trait config fields that can be updated (all optional)"""

    is_modifiable: bool | None = Field(default=None)
    modifiable_at_creation_only: bool | None = Field(default=None)
    is_required: bool | None = Field(default=None)


class TraitConfigCreate(TraitConfigBase):
    trait_id: uuid.UUID


class TraitConfigUpdate(TraitConfigBasePartial):
    pass


class TraitConfigPublic(TraitConfigBase):
    trait_id: uuid.UUID
    trait: TraitPublic | None = None


class TraitConfigsPublic(SQLModel):
    data: list[TraitConfigPublic]
    count: int

# =============================================================================
# TRAIT CONFLICT GROUP - The conflict relationship container
# =============================================================================

class TraitConflictGroupBase(SQLModel):
    """Base model for TraitConflictGroup - shared properties."""
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    conflict_type: str = Field(
        max_length=50,
        description="Type of logical conflict: 'contradictory', 'contrary', or 'subcontrary'"
    )
    reason: str | None = Field(
        default=None,
        max_length=2000,
        description="Explanation of why these traits conflict - aids author judgment for edge cases"
    )


class TraitConflictGroupCreate(TraitConflictGroupBase):
    """Input model for creating a TraitConflictGroup."""
    # Optionally include initial trait IDs during creation
    trait_ids: list[uuid.UUID] | None = Field(
        default=None,
        description="Optional list of trait IDs to add as members during creation"
    )


class TraitConflictGroupUpdate(SQLModel):
    """Update model for TraitConflictGroup - all fields optional."""
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    conflict_type: str | None = Field(default=None, max_length=50)
    reason: str | None = Field(default=None, max_length=2000)


class TraitConflictGroup(TraitConflictGroupBase, table=True):
    """Database model for TraitConflictGroup."""
    __tablename__ = "traitconflictgroup"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)

    # Relationship to members (defined post-definition for circular ref safety)
    # members: list["TraitConflictGroupMember"] = Relationship(back_populates="group", cascade_delete=True)


class TraitConflictGroupPublic(TraitConflictGroupBase):
    """Public model for TraitConflictGroup API responses."""
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime | None


class TraitConflictGroupPublicWithMembers(TraitConflictGroupPublic):
    """Public model with nested member traits for detailed responses."""
    members: list["TraitConflictGroupMemberPublic"] = []


class TraitConflictGroupsPublic(SQLModel):
    """Collection model for paginated TraitConflictGroup responses."""
    data: list[TraitConflictGroupPublic]
    count: int


# =============================================================================
# TRAIT CONFLICT GROUP MEMBER - Link table connecting traits to conflict groups
# =============================================================================

class TraitConflictGroupMemberBase(SQLModel):
    """Base model for TraitConflictGroupMember link."""
    # No additional base fields beyond the FKs


class TraitConflictGroupMemberCreate(SQLModel):
    """Input model for adding a trait to a conflict group."""
    trait_id: uuid.UUID = Field(description="ID of the trait to add to this conflict group")


class TraitConflictGroupMember(SQLModel, table=True):
    """Database model for TraitConflictGroupMember - links traits to conflict groups."""
    __tablename__ = "traitconflictgroupmember"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    group_id: uuid.UUID = Field(foreign_key="traitconflictgroup.id", index=True)
    trait_id: uuid.UUID = Field(foreign_key="trait.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships (defined post-definition for circular ref safety)
    # group: "TraitConflictGroup" = Relationship(back_populates="members")
    # trait: "Trait" = Relationship(back_populates="conflict_memberships")


class TraitConflictGroupMemberPublic(SQLModel):
    """Public model for TraitConflictGroupMember API responses."""
    id: uuid.UUID
    group_id: uuid.UUID
    trait_id: uuid.UUID
    created_at: datetime


class TraitConflictGroupMembersPublic(SQLModel):
    """Collection model for paginated member responses."""
    data: list[TraitConflictGroupMemberPublic]
    count: int



# =============== user management stuff ===============


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# ============================================================================
# Room Models (Projection)
# ============================================================================


class RoomBase(SQLModel):
    """Shared properties for Room projection."""

    title: str | None = Field(default=None, max_length=255)
    story_id: uuid.UUID | None = Field(default=None, foreign_key="story.id")


class RoomCreate(RoomBase):
    """Properties required when creating a room via API."""

    # creator_id will be injected from current_user, not from API input
    pass


class RoomUpdate(SQLModel):
    """Properties that can be updated via API."""

    title: str | None = Field(default=None, max_length=255)


class Room(RoomBase, table=True):
    """
    Room projection table (derived from RoomEvent log).

    This is a query-optimized view of room state, updated transactionally
    with event writes to ensure read-after-write consistency.
    """

    __tablename__ = "rooms"

    room_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    creator_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    last_activity: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    deleted_at: datetime | None = Field(default=None, nullable=True)

    # Relationships (using string forward references)
    participants: list["RoomParticipant"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )
    room_messages: list["RoomMessage"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )
    events: list["RoomEvent"] = Relationship(
        back_populates="room",
        cascade_delete=True,
    )



class RoomPublic(RoomBase):
    """Public room response model for API."""

    room_id: uuid.UUID
    creator_id: uuid.UUID
    created_at: datetime
    last_activity: datetime


class RoomsPublic(SQLModel):
    """Paginated collection of rooms."""

    data: list[RoomPublic]
    count: int


# ============================================================================
# RoomParticipant Models (Projection)
# ============================================================================


class RoomParticipantBase(SQLModel):
    """Shared properties for RoomParticipant projection."""

    participant_id: str = Field(
        max_length=255,
        description="UUID string for users, UserAgentConfig.slug for agents",
    )
    participant_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )
    role: str = Field(
        max_length=20,
        default="member",
        description="Either 'owner' or 'member'",
    )


class RoomParticipantCreate(RoomParticipantBase):
    """Properties required when adding a participant via API."""

    pass


class RoomParticipantUpdate(SQLModel):
    """Properties that can be updated via API."""

    role: str | None = Field(default=None, max_length=20)
    active: bool | None = None


class RoomParticipant(RoomParticipantBase, table=True):
    """
    RoomParticipant projection table (derived from RoomEvent log).

    Tracks both user and agent participants in rooms with their roles
    and active status. Updated transactionally with participant.joined,
    participant.left, and participant.role_changed events.
    """

    __tablename__ = "room_participants"
    __table_args__ = (
        # Unique constraint: one participant entry per room
        {"sqlite_autoincrement": True},
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(foreign_key="rooms.room_id", nullable=False, index=True)
    joined_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    left_at: datetime | None = Field(default=None)
    active: bool = Field(default=True, nullable=False)

    # Relationships
    room: Room = Relationship(back_populates="participants")


class RoomParticipantPublic(RoomParticipantBase):
    """Public participant response model for API."""

    id: uuid.UUID
    room_id: uuid.UUID
    joined_at: datetime
    left_at: datetime | None
    active: bool


class RoomParticipantsPublic(SQLModel):
    """Paginated collection of room participants."""

    data: list[RoomParticipantPublic]
    count: int


class ParticipantAddRequest(SQLModel):
    """
    Request model for adding a participant to a room.
    
    Used by: POST /rooms/{room_id}/participants
    """
    participant_id: str = Field(
        ...,
        max_length=255,
        description="UUID string for users, UserAgentConfig.slug for agents",
        # examples=["550e8400-e29b-41d4-a716-446655440000", "StoryAdvisor"],
    )
    participant_type: Literal["user", "agent"] = Field(
        ...,
        description="Type of participant (user or agent)",
    )
    role: Literal["owner", "member"] = Field(
        default="member",
        description="Participant role (default: member)",
    )


class ParticipantRoleChangeRequest(SQLModel):
    """
    Request model for changing a participant's role.
    
    Used by: PATCH /rooms/{room_id}/participants/{participant_id}/role
    """
    new_role: Literal["owner", "member"] = Field(
        ...,
        description="New role for the participant",
    )


class MessageResponse(SQLModel):
    """
    Generic success message response.
    
    Used for operations that need to return a simple success message.
    """
    message: str = Field(
        ...,
        description="Success message",
    )

# ============================================================================
# RoomParticipantBinding Models (Room-scoped runtime persona + model/provider)
# ============================================================================


class RoomParticipantBindingBase(SQLModel):
    """Shared properties for room participant runtime bindings."""

    participant_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )
    participant_id: str = Field(
        max_length=255,
        description="UUID string for users; UserAgentConfig.slug for agents",
    )

    persona_id: uuid.UUID | None = Field(default=None, foreign_key="persona.id")

    model_name: str | None = Field(
        default=None,
        max_length=100,
        description="Same format as UserAgentConfig.model_name (e.g., 'openai:gpt-4o-mini')",
    )
    user_access_provider_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user_access_provider.id",
        description="User-owned provider config to use (must belong to current user)",
    )


class RoomParticipantBindingCreate(RoomParticipantBindingBase):
    room_id: uuid.UUID
    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
    agent_id: uuid.UUID | None = Field(default=None, foreign_key="user_agent_configs.id")
    effective_at: datetime
    ended_at: datetime | None = None


class RoomParticipantBindingUpdate(SQLModel):
    persona_id: uuid.UUID | None = None
    model_name: str | None = None
    user_llm_provider_id: uuid.UUID | None = None


class RoomParticipantBinding(RoomParticipantBindingBase, table=True):
    """
    Room-scoped runtime binding for a participant with history.

    Invariant: one active binding per (room_id, participant_type, participant_id),
    where active means ended_at IS NULL.
    """

    __tablename__ = "room_participant_bindings"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )

    user_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", nullable=True)
    agent_id: uuid.UUID | None = Field(
        default=None, foreign_key="user_agent_configs.id", nullable=True
    )

    effective_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    ended_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RoomParticipantBindingPublic(RoomParticipantBindingBase):
    id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    effective_at: datetime
    ended_at: datetime | None
    created_at: datetime


class RoomParticipantBindingsPublic(SQLModel):
    data: list[RoomParticipantBindingPublic]
    count: int


class ParticipantBindingChangeRequest(SQLModel):
    """
    Request model for setting a participant's active binding in a room.

    Payload is event-sourced via participant.binding_changed.
    """
    participant_type: Literal["user", "agent"] = Field(
        ...,
        description="Type of participant (user or agent)",
    )
    persona_id: uuid.UUID | None = Field(
        default=None,
        description="Persona to bind for this participant (optional).",
    )
    model_name: str | None = Field(
        default=None,
        max_length=100,
        description="Model identifier (e.g., 'openai:gpt-4o-mini').",
    )
    user_access_provider_id: uuid.UUID | None = Field(
        default=None,
        description="User-owned provider config to use (must belong to current user).",
    )


# ============================================================================
# RoomStoryProgress Models (Shared Room Run)
# ============================================================================


class RoomStoryProgressBase(SQLModel):
    """
    Room-scoped pointer to the active shared story run ("party progress").

    The underlying run state is stored using existing progress primitives:
    - UserStoryProgress.story_state (canonical state block)
    - UserNodeChoice (choice history / event log)
    - ProgressSnapshot (periodic immutable snapshots)
    """

    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False)
    story_version: int = Field(nullable=False)
    active_progress_id: uuid.UUID = Field(
        foreign_key="userstoryprogress.id", nullable=False
    )
    revision: int = Field(
        default=0, description="Monotonically increasing optimistic concurrency token."
    )


class RoomStoryProgress(RoomStoryProgressBase, table=True):
    __tablename__ = "room_story_progresses"
    __table_args__ = (UniqueConstraint("room_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id", nullable=False, ondelete="CASCADE", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RoomStoryProgressPublic(RoomStoryProgressBase):
    id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RoomRuntimePublic(SQLModel):
    """
    Read model for the room's shared story run, suitable for UI and agent projection.

    This is intentionally a projection, not a dump of the full event log.
    """

    room_id: uuid.UUID
    story_id: uuid.UUID
    story_version: int
    active_progress_id: uuid.UUID
    revision: int

    current_node_id: uuid.UUID | None
    head_choice_id: uuid.UUID | None
    head_version: int
    story_state: dict[str, Any] | None
    updated_at: datetime
    current_node: StoryNodePublic | None = None
    node_chain: list[StoryNodePublic] = Field(default_factory=list)
    available_choices: list[NodeChoicePublic] = Field(default_factory=list)


class RoomRuntimeStartRequest(SQLModel):
    """
    Request model to initialize (or re-initialize) a room's shared story run.

    A room run is backed by an underlying UserStoryProgress record.
    """

    user_persona_id: uuid.UUID
    story_version: int | None = None
    expected_revision: int | None = None


class RoomRuntimeAdvanceRequest(SQLModel):
    """
    Request model to advance the room's shared story run.
    """

    choice_id: uuid.UUID
    expected_revision: int | None = None


class RoomRuntimeRewindRequest(SQLModel):
    """
    Request model to rewind the room's shared story run to a prior choice.
    """

    target_choice_id: uuid.UUID
    expected_revision: int | None = None


class RoomRuntimeResetRequest(SQLModel):
    """
    Request model to reset the room's shared story run to the start node.
    """

    expected_revision: int | None = None


class RoomContextItemCreate(SQLModel):
    """
    Request model to attach supplemental context to a room.
    """

    context_type: str
    payload: dict[str, Any]
    source: str
    agent_slug: str | None = None
    expires_at: datetime | None = None


class RoomContextItemPublic(SQLModel):
    id: str
    room_id: uuid.UUID
    agent_slug: str | None
    context_type: str
    payload: dict[str, Any]
    source: str
    created_at: datetime
    expires_at: datetime | None


class RoomContextItemsPublic(SQLModel):
    data: list[RoomContextItemPublic]
    count: int


# ============================================================================
# Room Agent Settings Models (Room-scoped agent policy)
# ============================================================================


class RoomAgentSettingsBase(SQLModel):
    """
    Room-scoped runtime policy settings.

    Extensibility contract:
    - `prompt_config_id` + version fields are the canonical persisted attach points for
      reusable PromptConfig recipes at room/session scope.
    - `prompt_config` remains an inline ad hoc overlay payload for temporary edits and
      future inspector/panel surfaces that need to expose the effective recipe shape.
    - Runtime must resolve both through the shared prompt runtime resolver; callers
      should not read or merge these fields directly.
    """

    agent_slug: str | None = Field(
        default=None,
        max_length=50,
        description="Null for room-wide defaults; set for per-agent overrides.",
    )
    prompt_config_id: uuid.UUID | None = Field(
        default=None,
        description="Optional bound PromptConfig recipe for this room-scoped layer.",
    )
    prompt_config_version_policy: str | None = Field(
        default="latest",
        description="How runtime resolves the attached PromptConfig version for this room-scoped layer.",
    )
    prompt_config_version_number: int | None = Field(
        default=None,
        description="Pinned PromptConfig version when version policy is 'pinned'.",
    )
    prompt_config: dict[str, Any] | None = Field(
        default=None,
        sa_column=Column(JSON),
        description="Optional inline PromptConfigDraft overlay applied after any attached PromptConfig reference.",
    )
    tool_policy: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    rule_config: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    revision: int = Field(default=0)

    @model_validator(mode="after")
    def validate_prompt_binding(self) -> "RoomAgentSettingsBase":
        if self.prompt_config_id is None:
            self.prompt_config_version_number = None
            return self
        policy = self.prompt_config_version_policy or "latest"
        self.prompt_config_version_policy = policy
        if policy == "latest":
            self.prompt_config_version_number = None
            return self
        if not isinstance(self.prompt_config_version_number, int) or self.prompt_config_version_number <= 0:
            raise ValueError(
                "prompt_config_version_number must be a positive integer when prompt_config_version_policy is 'pinned'"
            )
        return self


class RoomAgentSettings(RoomAgentSettingsBase, table=True):
    __tablename__ = "room_agent_settings"
    __table_args__ = (UniqueConstraint("room_id", "agent_slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id", nullable=False, ondelete="CASCADE", index=True
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class RoomAgentSettingsPublic(RoomAgentSettingsBase):
    id: uuid.UUID
    room_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RoomAgentSettingsUpdate(SQLModel):
    prompt_config_id: uuid.UUID | None = None
    prompt_config_version_policy: Literal["latest", "pinned"] | None = None
    prompt_config_version_number: int | None = None
    prompt_config: dict[str, Any] | None = None
    tool_policy: dict[str, Any] | None = None
    rule_config: dict[str, Any] | None = None
    expected_revision: int | None = None

    @model_validator(mode="after")
    def validate_prompt_binding(self) -> "RoomAgentSettingsUpdate":
        fields_set = self.model_fields_set
        has_binding_fields = bool(
            {"prompt_config_id", "prompt_config_version_policy", "prompt_config_version_number"} & fields_set
        )
        if not has_binding_fields:
            return self

        if self.prompt_config_id is None:
            if "prompt_config_version_number" in fields_set and self.prompt_config_version_number not in (None,):
                raise ValueError(
                    "prompt_config_version_number cannot be set when prompt_config_id is null"
                )
            return self

        policy = self.prompt_config_version_policy or "latest"
        if policy == "latest":
            if (
                "prompt_config_version_number" in fields_set
                and self.prompt_config_version_number not in (None,)
            ):
                raise ValueError(
                    "prompt_config_version_number must be null when prompt_config_version_policy is 'latest'"
                )
            return self
        if not isinstance(self.prompt_config_version_number, int) or self.prompt_config_version_number <= 0:
            raise ValueError(
                "prompt_config_version_number must be a positive integer when prompt_config_version_policy is 'pinned'"
            )
        return self


class RoomAgentSettingsBundle(SQLModel):
    room_defaults: RoomAgentSettingsPublic | None
    agent_overrides: list[RoomAgentSettingsPublic]

# ============================================================================
# Message Models (Projection)
# ============================================================================


class RoomMessageBase(SQLModel):
    """Shared properties for Message projection."""

    content: str = Field(description="Message text content")
    sender_type: str = Field(
        max_length=20,
        description="Either 'user', 'agent', or 'agent_internal'",
    )


class RoomMessageCreate(RoomMessageBase):
    """Properties required when creating a message via API."""

    pass
    # sender_id and agent_name will be injected based on sender_type

class RoomMessageSend(SQLModel):
    """Properties required when sending a message via API."""

    content: str = Field(description="Message text content")


class UIActionRequest(SQLModel):
    """
    Request body for AG-UI action button clicks.

    When a user clicks an action button emitted by an agent, the frontend sends
    this payload to POST /rooms/{room_id}/ui-action. The backend looks up the
    originating agent from the source message and invokes it with the action
    string as context, bypassing normal participation mode checks.

    This enables bidirectional agent interaction without polluting the chat
    history with raw action strings.
    """

    # The action identifier from the UIActionButton (e.g., "expand_section",
    # "regenerate", "accept_layout"). Passed to the agent as trigger context.
    action: str = Field(description="Action identifier from the button that was clicked")

    # The message_id of the agent message that contained the UI component.
    # Used to look up which agent should handle this action.
    source_message_id: UUID = Field(
        description="ID of the agent message that emitted the action button"
    )

    # Optional: identifies the specific component within a message (if the
    # message contained multiple action_buttons components). Currently used
    # for logging/debugging; agents receive the action string regardless.
    component_id: str | None = Field(
        default=None,
        description="Optional ID of the specific UI component that was clicked",
    )


class RepoRoomEventRequest(SQLModel):
    """
    Request body for room-scoped repository collaboration events.

    This payload is used by frontend repo panels embedded in Room to emit
    structured selection/open/ref actions into the room event log.
    """

    action: Literal["selection", "open", "ref"] = Field(
        description="Repo collaboration action type"
    )
    panel_id: str | None = Field(
        default=None,
        description="Optional panel instance id that emitted the action",
    )
    selection_key: str | None = Field(
        default=None,
        description="Shared selection key for cross-panel coordination",
    )
    path: str | None = Field(
        default=None,
        description="Repository file path associated with this action",
    )
    ref: str | None = Field(
        default=None,
        description="Git ref associated with this action",
    )
    repo_id: uuid.UUID | None = Field(
        default=None,
        description="Platform user_repo identifier for the emitted action",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional opaque metadata for future expansion",
    )


class RoomMessageUpdate(SQLModel):
    """
    Messages are immutable once created.

    To "edit" a room_message, emit a new room_message.edited event.
    Update model exists for consistency but should not be used.
    """

    pass


class RoomMessage(RoomMessageBase, table=True):
    """
    Message projection table (derived from RoomEvent log).

    Stores conversation messages for efficient querying. Updated transactionally
    with room_message.user and room_message.agent events.
    """

    __tablename__ = "room_messages"

    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id",
        nullable=False,
        index=True,
    )
    sender_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="user.id",
        description="User ID if sender_type='user'",
    )
    agent_name: str | None = Field(
        default=None,
        max_length=255,
        description="Agent name if sender_type='agent'",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )
    # Editing fields
    edited_at: datetime | None = None
    edited_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")

    # Pinning fields
    is_pinned: bool = Field(default=False, index=True)  # Index for filtering
    pinned_at: datetime | None = None
    pinned_by: uuid.UUID | None = Field(default=None, foreign_key="user.id")

    # Context inclusion field
    active_for_context: bool = Field(default=True, index=True)  # Index for filtering

    button_options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # AG-UI interactive buttons: [{"label": str, "value": str, "style": str}]
    ui_components: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )
    # Relationships
    room: Room = Relationship(back_populates="room_messages")


class RoomMessagePublic(RoomMessageBase):
    """Public message response model for API."""

    message_id: uuid.UUID
    room_id: uuid.UUID
    sender_id: uuid.UUID | None
    agent_name: str | None
    created_at: datetime

    # Message management fields (Phase 5)
    edited_at: datetime | None = None
    edited_by: uuid.UUID | None = None
    is_pinned: bool = False
    pinned_at: datetime | None = None
    pinned_by: uuid.UUID | None = None
    active_for_context: bool = True
    can_edit: bool = False
    can_delete: bool = False
    can_pin: bool = False
    sender_display_name: str | None = None

    button_options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    ui_components: list[dict[str, Any]] | None = Field(
        default=None,
        sa_column=Column(JSONB),
    )


class RoomMessagesPublic(SQLModel):
    """Paginated collection of messages."""

    data: list[RoomMessagePublic]
    count: int


# ============================================================================
# Page Layout Models (Agent-Authored Pages)
# ============================================================================


class PageBase(SQLModel):
    """Shared properties for persisted page layouts."""

    entity_type: str = Field(max_length=50, index=True)
    entity_id: str = Field(max_length=255, index=True)
    layout_version: int = Field(default=1)
    layout_json: list[dict[str, Any]] = Field(sa_column=Column(JSONB))
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False),
    )


class PageCreate(PageBase):
    """Input model for creating a page layout."""

    owner_id: uuid.UUID


class PageLayoutUpdate(SQLModel):
    """Update model for page layout."""

    layout_json: list[dict[str, Any]]
    layout_version: int | None = None
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(default_factory=dict)


class Page(PageBase, table=True):
    """
    Persisted page layouts for entities.

    One layout per entity_type/entity_id pair.
    """

    __tablename__ = "pages"
    __table_args__ = (UniqueConstraint("entity_type", "entity_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(foreign_key="user.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PagePublic(PageBase):
    """Public response model for pages."""

    id: uuid.UUID
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class PagesPublic(SQLModel):
    """Paginated collection of pages."""
    data: list[PagePublic]
    count: int


# ============================================================================
# DemoConfig / DemoSession Models
# ============================================================================


class DemoConfigBase(SQLModel):
    """Shared properties for a demo template."""

    slug: str = Field(
        min_length=1,
        max_length=100,
        description="URL-safe identifier used by /demo/$slug",
    )
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=1000)
    scope: DemoConfigScope = Field(default=DemoConfigScope.system)
    is_active: bool = Field(default=True)

    default_auto_respond: bool = Field(default=True)
    default_panels_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Default panel composition for DemoShell",
    )
    default_layout_json: list[dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSONB),
        description="Default page block layout payload",
    )
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
        description="Extensible config for demo-specific integrations",
    )


class DemoConfigCreate(DemoConfigBase):
    pass


class DemoConfigUpdate(SQLModel):
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


class DemoSessionBase(SQLModel):
    """Shared properties for per-user runtime demo sessions."""

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
    demo_config_id: UUID = Field(description="Demo template to instantiate")
    auto_respond: bool | None = None


class DemoSessionUpdate(SQLModel):
    auto_respond: bool | None = None
    status: DemoSessionStatus | None = None


class DemoSession(DemoSessionBase, table=True):
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


class ResolveDemoSessionRequest(SQLModel):
    demo_slug: str = Field(min_length=1, max_length=100)


class ResolveDemoSessionResponse(SQLModel):
    demo_config: DemoConfigPublic
    demo_session: DemoSessionPublic
    created: bool = Field(
        description="True if session (and room) were created during this request"
    )


# ============================================================================
# Message Management Request Models (Phase 5)
# ============================================================================


class MessageEdit(SQLModel):
    """Request model for editing message content."""

    content: str


class MessageContextToggle(SQLModel):
    """Request model for toggling message context inclusion."""

    active_for_context: bool


# ============================================================================
# RoomEvent Models (System of Record - Append-Only)
# ============================================================================


class RoomEventBase(SQLModel):
    """Shared properties for RoomEvent."""

    event_type: str = Field(
        max_length=50,
        description="Event type (e.g., room.created, room_message.user, participant.joined)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific data as JSON",
        sa_type=JSON,  # Will be JSONB in PostgreSQL
    )


class RoomEventCreate(RoomEventBase):
    """Properties required when creating an event."""

    room_id: uuid.UUID
    # room_sequence will be auto-generated


class RoomEvent(RoomEventBase, table=True):
    """
    RoomEvent: Immutable append-only event log (system of record).

    This is the source of truth for all room state changes. Projections
    (Room, RoomParticipant, RoomMessage) are derived from this log.

    CRITICAL INVARIANTS:
    - Events are NEVER updated or deleted (append-only)
    - room_sequence is monotonically increasing per room
    - (room_id, room_sequence) is unique
    - All projections can be rebuilt by replaying events in sequence order

    Event Types (Phase 1 minimum):
    - room.created: New room created
    - room.updated: Room metadata updated
    - participant.joined: User or agent joined room
    - participant.left: User or agent left room (soft delete)
    - participant.role_changed: Participant role updated
    - room_message.user: User sent message
    - room_message.agent: Agent sent message
    """

    __tablename__ = "room_events"
    __table_args__ = (
        # Unique constraint on (room_id, room_sequence) for ordering
        # TODO - why is this sqlite instead of postgres?
        {"sqlite_autoincrement": True},
    )

    event_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    room_id: uuid.UUID = Field(
        foreign_key="rooms.room_id",
        nullable=False,
        index=True,
    )
    room_sequence: int = Field(
        nullable=False,
        description="Monotonically increasing sequence number per room",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        index=True,
    )
    enrichment_metadata: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # Optional metadata for event enrichment (trace IDs, performance metrics, etc.)
    # Relationships
    room: Room = Relationship(back_populates="events")


class RoomEventPublic(RoomEventBase):
    """Public event response model for API (for debugging/replay)."""

    event_id: uuid.UUID
    room_id: uuid.UUID
    room_sequence: int
    created_at: datetime


class RoomEventsPublic(SQLModel):
    """Paginated collection of room events."""

    data: list[RoomEventPublic]
    count: int

class StateValueType(str, PyEnum):
    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    ENUM = "enum"

class StoryStateVariableBase(SQLModel):
    key: str = Field(min_length=1, max_length=100)
    value_type: StateValueType = Field(default=StateValueType.STRING)
    default_value: Any | None = Field(default=None, sa_column=Column(JSON))
    enum_values: list[str] | None = Field(default=None, sa_column=Column(JSON))
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)

class StoryStateVariableCreate(StoryStateVariableBase):
    story_id: uuid.UUID
    story_version: int

class StoryStateVariableUpdate(SQLModel):
    key: str | None = Field(default=None, min_length=1, max_length=100)
    value_type: StateValueType | None = None
    default_value: Any | None = None
    enum_values: list[str] | None = None
    description: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=100)

class StoryStateVariable(StoryStateVariableBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    story_id: uuid.UUID = Field(foreign_key="story.id", nullable=False, ondelete="CASCADE")
    story_version: int = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class StoryStateVariablePublic(StoryStateVariableBase):
    id: uuid.UUID
    story_id: uuid.UUID
    story_version: int

class StoryStateVariablesPublic(SQLModel):
    data: list[StoryStateVariablePublic]
    count: int

class StateSchemaValidationError(SQLModel):
    variable_key: str
    used_in: str  # "requires_state" or "sets_state"
    choice_id: uuid.UUID
    choice_text: str
    from_node_id: uuid.UUID
    from_node_title: str

class StateSchemaValidationResult(SQLModel):
    is_valid: bool
    errors: list[StateSchemaValidationError]
    defined_variables: list[str]
    used_variables: list[str]
    undefined_variables: list[str]


# ============================================================================
# Story Validation Models (Graph Structure Validation)
# ============================================================================


class StoryValidationError(SQLModel):
    """Individual validation error with context."""
    message: str
    node_id: uuid.UUID | None = None
    node_title: str | None = None
    choice_id: uuid.UUID | None = None
    choice_text: str | None = None


class StoryValidationResult(SQLModel):
    """Result of validating a story's graph structure for publishing."""
    is_valid: bool
    errors: list[str]  # Blocking errors that prevent publishing
    warnings: list[str]  # Non-blocking warnings (orphan nodes, dead ends)
    node_count: int
    choice_count: int
    start_node_count: int
    end_node_count: int
    orphaned_node_count: int
    state_schema_validation: StateSchemaValidationResult | None = None


# ============================================================================
# Story Node Tree Models (Pre-computed Tree Structure)
# ============================================================================


class StoryNodeTreeNode(SQLModel):
    """A node in the pre-computed story tree structure."""
    id: uuid.UUID
    title: str
    is_start_node: bool
    is_end_node: bool
    level: int
    children: list["StoryNodeTreeNode"] = []


class StoryNodeTree(SQLModel):
    """Pre-computed tree structure for a story version."""
    root: StoryNodeTreeNode | None = None
    orphaned_nodes: list[StoryNodeTreeNode] = []
    total_nodes: int
    reachable_nodes: int



 # ═══════════════════════════════════════════════════════════════════════════════
 # Agent Configuration Models
 # ═══════════════════════════════════════════════════════════════════════════════

class UserAgentConfigBase(SQLModel):
    """Base properties shared by all agent config representations."""
    name: str = Field(max_length=100, description="Display name")
    slug: str = Field(max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default_factory=uuid.uuid4, foreign_key="user_access_provider.id", description="User-selected provider associated with this agent config" )
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=50, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, foreign_key="user_access_provider.id", description="model associated with this agent config")
    # LLMModels table
    model_name: str = Field(default="friendly model name")
    system_prompt: str | None = None
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    # JSON configuration fields
    tool_config: dict | None = Field(default=None, sa_column=Column(JSON))
    deps_config: dict | None = Field(default=None, sa_column=Column(JSON))
    prompt_config_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="prompt_configs.id",
        description="Optional bound PromptConfig for runtime prompt/tool recipe.",
    )
    prompt_config_version_policy: Literal["latest", "pinned"] | None = Field(
        default="latest",
        description="How runtime resolves prompt version for prompt_config_id.",
    )
    prompt_config_version_number: int | None = Field(
        default=None,
        description="Pinned version when prompt_config_version_policy is 'pinned'.",
    )
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    agent_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))

    # Behavior flags
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
    scope: str = Field(default="personal")  # "personal" | "system"
    participation_mode: str = Field(default="on_mention")  # "always" | "on_mention" | "manual"

    # Coordinator mode: if True, this agent processes messages FIRST
    # before other agents, acting as an orchestrator that routes to specialists
    is_coordinator: bool = Field(default=False)

    # Tool enablement flags - agents can self-declare which tools they need.
    # These work as an OR with runtime flags: tool is enabled if EITHER
    # the config declares it OR the runtime caller injects it.
    # This supports both agent self-declaration and dependency injection patterns.
    enable_a2a_tool: bool = Field(
        default=False,
        description="Enable request_agent_assistance tool for agent-to-agent calls"
    )
    enable_ag_ui_tool: bool = Field(
        default=False,
        description="Enable emit_ui_component tool for rich UI emission"
    )

    # Maximum number of LLM requests per agent run (prevents runaway tool loops)
    max_tool_iterations: int = Field(default=10)

    # Agent capabilities for discovery and A2A coordination
    # e.g., ["story-structure", "dialogue", "character-development", "plot-twists"]
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator("capabilities", mode="before")
    @classmethod
    def capabilities_none_to_list(cls, v: list[str] | None) -> list[str]:
        """Convert NULL from database to empty list."""
        return v if v is not None else []

    @model_validator(mode="before")
    @classmethod
    def validate_prompt_config_binding(cls, data: Any) -> Any:
        """
        Validate and normalize prompt binding fields before model construction.
        Using `before` avoids mutating SQLAlchemy-instrumented attributes during
        `model_validate()` for table models.
        """
        if data is None:
            return data

        if isinstance(data, dict):
            payload = dict(data)
        elif hasattr(data, "model_dump"):
            payload = data.model_dump()
        else:
            return data

        policy = payload.get("prompt_config_version_policy") or "latest"
        if policy not in {"latest", "pinned"}:
            raise ValueError("prompt_config_version_policy must be 'latest' or 'pinned'")

        prompt_config_id = payload.get("prompt_config_id")
        if prompt_config_id is None or policy == "latest":
            payload["prompt_config_version_number"] = None
            payload["prompt_config_version_policy"] = policy
            return payload

        version_number = payload.get("prompt_config_version_number")
        if version_number is None or version_number <= 0:
            raise ValueError(
                "prompt_config_version_number must be a positive integer when policy is 'pinned'"
            )

        payload["prompt_config_version_policy"] = policy
        return payload

class Type1Create(UserAgentConfigBase):
    provider_type: Literal[TYPE1]
    system_prompt: str
    description: str
    agent_type: str = Field(default="advisor",max_length=30)
    model_name: str = Field(default="friendly model name")
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
    scope: str = Field(default="personal")  # "personal" | "system"
    participation_mode: str = Field(default="on_mention")
    is_coordinator: bool = Field(default=False)
    max_tool_iterations: int = Field(default=10)
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator('description')
    @classmethod
    def validate_type1_scope(cls, v: str)->str:
        if not v or v.strip() == '':
            raise ValueError("description required for Type1")
        return v


class Type2Create(UserAgentConfigBase):
    provider_type: Literal[TYPE2]


class Type3Create(UserAgentConfigBase):
    provider_type: Literal[TYPE3]
    system_prompt: str = Field(max_length=5000)
    model_name: str = Field(default="friendly model name")
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
    agent_type: str = Field(default="advisor",max_length=30)
    scope: str = Field(default="personal")  # "personal" | "system"
    participation_mode: str = Field(default="on_mention")
    is_coordinator: bool = Field(default=False)
    max_tool_iterations: int = Field(default=10)
    capabilities: list[str] = Field(default_factory=list, sa_column=Column(JSON))

    @field_validator('system_prompt')
    @classmethod
    def validate_type3_system_prompt(cls, v: str) -> str:
        if not v or v.strip() == '':
            raise ValueError("system prompt required for Type3")


class Type4Create(UserAgentConfigBase):
    provider_type: Literal[TYPE4]


class Type5Create(UserAgentConfigBase):
    provider_type: Literal[TYPE5]


UserAgentConfigCreate = Annotated[
    Type1Create | Type2Create | Type3Create | Type4Create | Type5Create,
    Field(discriminator='provider_type')
]

class Type1Update(UserAgentConfigBase):
    provider_type: Literal[TYPE1]
    description: str | None = None # optional for updates, but this will cause validation if it is passed again


class Type2Update(UserAgentConfigBase):
    provider_type: Literal[TYPE2]


class Type3Update(UserAgentConfigBase):
    provider_type: Literal[TYPE3]
    system_prompt: str | None = None # optional for update, but causes validation trigger if passed


class Type4Update(UserAgentConfigBase):
    provider_type: Literal[TYPE4]


class Type5Update(UserAgentConfigBase):
    provider_type: Literal[TYPE5]


UserAgentConfigUpdate = Annotated[
    Type1Update | Type2Update | Type3Update | Type4Update | Type5Update,
    Field(discriminator='provider_type')
]

# class UserAgentConfigUpdate(UserAgentConfigBase):
#     name: str | None = Field(default=None, max_length=100, description="Display name")
#     slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
#     description: str | None = Field(default=None, max_length=500)
#     user_access_provider: uuid.UUID | None = Field(default=None, description="User-selected provider associated with this agent config")
#     provider_type: uuid.UUID | None=Field(default_factory=uuid.uuid4)
#     model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
#     model: str | None=Field(default=None, max_length=20, description="friendly name of model as specified by api and user access providers")
#     model_name: str | None = Field(default=None)
#     system_prompt: str | None = Field(default=None)
#     custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
#     instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
#     tool_config: dict | None = Field(default=None)
#     deps_config: dict | None = Field(default=None)
#     agent_metadata: dict | None = Field(default=None)
#     is_enabled: bool | None = Field(default=None)
#     is_clonable: bool | None = Field(default=None)
#     is_visible: bool | None = Field(default=None)
#     scope: str | None = Field(default=None)
#     participation_mode: str | None = Field(default=None)
#     is_coordinator: bool | None = Field(default=None)
#     max_tool_iterations: int | None = Field(default=None)
#     capabilities: list[str] | None = Field(default=None)

class UserAgentConfig(UserAgentConfigBase, table=True):
    __tablename__ = "user_agent_configs"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default_factory=uuid.uuid4, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None, sa_column_kwargs={"onupdate": datetime.now})
    version: int = Field(default=1)
    name: str | None = Field(default=None, max_length=100, description="Display name")
    slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default_factory=uuid.uuid4,  description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=100, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
    model_name: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    tool_config: dict | None = Field(default=None, sa_column=Column(JSON))
    deps_config: dict | None = Field(default=None, sa_column=Column(JSON))
    prompt_config_id: uuid.UUID | None = Field(default=None, foreign_key="prompt_configs.id", index=True)
    prompt_config_version_policy: str | None = Field(default="latest", max_length=20)
    prompt_config_version_number: int | None = Field(default=None)
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None, sa_column=Column(JSON))
    agent_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))

class UserAgentConfigPublic(UserAgentConfigBase):
    id: uuid.UUID
    owner_id: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    created_at: datetime
    updated_at: datetime | None
    version: int
    name: str | None = Field(default=None, max_length=100, description="Display name")
    slug: str | None = Field(default=None, max_length=50, description="Unique identifier/registry key")
    description: str | None = Field(default=None, max_length=500)
    user_access_provider: uuid.UUID | None = Field(default_factory=uuid.uuid4, description="User-selected provider associated with this agent config")
    provider_type: uuid.UUID | None = Field(default_factory=uuid.uuid4)
    model: str | None=Field(default=None, max_length=100, description="friendly name of model as specified by api and user access providers")
    model_id: uuid.UUID | None = Field(default=None, description="model associated with this agent config")
    model_name: str | None = Field(default=None)
    system_prompt: str | None = Field(default=None)
    custom_system_prompt: str | None = Field(default=None, description="Optional user override for system prompt")
    instructions: str | None = Field(default=None, description="big ass text field for lots of words.")
    tool_config: dict | None = Field(default=None)
    deps_config: dict | None = Field(default=None)
    prompt_config_id: uuid.UUID | None = Field(default=None)
    prompt_config_version_policy: Literal["latest", "pinned"] | None = Field(default="latest")
    prompt_config_version_number: int | None = Field(default=None)
    agent_metadata: dict | None = Field(default=None)
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None)
    agent_type: str | None = Field(default=None, description="text for type that can be overloaded in presentation")
    presentation: dict | None = Field(default=None, sa_column=Column(JSON))

class UserAgentConfigsPublic(SQLModel):
    data: list[UserAgentConfigPublic]
    count: int


# =============================================================================
# Prompt Builder Models (M1)
# =============================================================================


class PromptProviderKind(str, PyEnum):
    openai_compatible = "openai_compatible"
    openai = "openai"
    anthropic = "anthropic"
    google = "google"
    xai = "xai"
    custom = "custom"


class PromptInputKind(str, PyEnum):
    simple_text = "simple_text"
    messages = "messages"


class PromptMessageRole(str, PyEnum):
    system = "system"
    user = "user"
    assistant = "assistant"
    tool = "tool"


class PromptProviderBinding(SQLModel):
    user_access_provider_id: uuid.UUID | None = Field(default=None)
    provider_type_id: uuid.UUID | None = Field(default=None)
    provider_kind: PromptProviderKind | None = Field(default=None)
    base_url: str | None = Field(default=None, max_length=500)
    account_label: str | None = Field(default=None, max_length=255)


class PromptModelBinding(SQLModel):
    model_catalog_id: uuid.UUID | None = Field(default=None)
    model_id: str | None = Field(default=None, max_length=255)
    model_name: str | None = Field(default=None, max_length=255)
    model_family: str | None = Field(default=None, max_length=120)


class PromptMessage(SQLModel):
    role: PromptMessageRole
    content: str = Field(default="", max_length=100000)


class PromptInputPayload(SQLModel):
    kind: PromptInputKind = Field(default=PromptInputKind.simple_text)
    text: str | None = Field(default=None, max_length=100000)
    system: str | None = Field(default=None, max_length=100000)
    messages: list[PromptMessage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_input_kind_shape(self) -> "PromptInputPayload":
        if self.kind == PromptInputKind.simple_text:
            if self.text is None:
                self.text = ""
            self.messages = []
            return self

        # messages mode
        if self.messages is None:
            self.messages = []
        self.text = None
        return self


class PromptParams(SQLModel):
    provider_kind: PromptProviderKind | None = Field(default=PromptProviderKind.openai_compatible)
    temperature: float | None = Field(default=None)
    top_p: float | None = Field(default=None)
    max_output_tokens: int | None = Field(default=None)
    stop: list[str] | None = Field(default=None)
    seed: int | None = Field(default=None)
    response_format: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    # Deprecated compatibility alias; normalized into response_format.
    response_format_json: bool | None = Field(default=None)
    openai: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    parallel_tool_calls: bool | None = Field(default=None)
    reasoning_effort: Literal["low", "medium", "high"] | None = Field(default=None)
    top_k: int | None = Field(default=None)

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < 0 or value > 2:
            raise ValueError("temperature must be between 0 and 2")
        return value

    @field_validator("top_p")
    @classmethod
    def validate_top_p(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < 0 or value > 1:
            raise ValueError("top_p must be between 0 and 1")
        return value

    @field_validator("max_output_tokens")
    @classmethod
    def validate_max_output_tokens(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("max_output_tokens must be greater than 0")
        return value

    @model_validator(mode="after")
    def normalize_response_format_alias(self) -> "PromptParams":
        if self.response_format is None and self.response_format_json is True:
            self.response_format = {"type": "json_object"}
        return self

    @field_validator("response_format")
    @classmethod
    def validate_response_format(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        format_type = value.get("type")
        if format_type not in {"text", "json_object", "json_schema"}:
            raise ValueError("response_format.type must be one of: text, json_object, json_schema")
        if format_type == "json_schema":
            json_schema = value.get("json_schema")
            if not isinstance(json_schema, dict):
                raise ValueError("response_format.json_schema is required when type=json_schema")
            name = json_schema.get("name")
            schema = json_schema.get("schema")
            if not isinstance(name, str) or not name.strip():
                raise ValueError("response_format.json_schema.name must be a non-empty string")
            if not isinstance(schema, dict):
                raise ValueError("response_format.json_schema.schema must be an object")
        return value

    @field_validator("openai")
    @classmethod
    def validate_openai_extension(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        previous_response_id = value.get("previous_response_id")
        if previous_response_id is not None:
            if not isinstance(previous_response_id, str) or not previous_response_id.strip():
                raise ValueError("openai.previous_response_id must be a non-empty string")
            value["previous_response_id"] = previous_response_id.strip()
        reasoning = value.get("reasoning")
        if reasoning is not None:
            if not isinstance(reasoning, dict):
                raise ValueError("openai.reasoning must be an object")
            summary = reasoning.get("summary")
            if summary is not None and summary not in {"auto", "concise", "detailed"}:
                raise ValueError("openai.reasoning.summary must be one of: auto, concise, detailed")
        return value


class PromptToolingConfig(SQLModel):
    tool_mode: Literal["none", "optional", "required"] | None = Field(default="none")
    tool_allowlist: list[str] | None = Field(default=None)
    tool_choice: str | dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    max_tool_calls: int | None = Field(default=None)
    builtin: list[dict[str, Any]] | None = Field(default=None, sa_column=Column(JSON))
    mcp: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))

    @field_validator("max_tool_calls")
    @classmethod
    def validate_max_tool_calls(cls, value: int | None) -> int | None:
        if value is None:
            return value
        if value <= 0:
            raise ValueError("max_tool_calls must be greater than 0")
        return value

    @field_validator("tool_choice", mode="before")
    @classmethod
    def normalize_tool_choice(cls, value: Any) -> str | dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, str):
            trimmed = value.strip()
            if trimmed in {"auto", "none", "required"}:
                return trimmed
            if trimmed:
                # Backward compatibility: free-form string becomes named tool choice.
                return {"type": "named", "name": trimmed}
            return None
        if isinstance(value, dict):
            choice_type = value.get("type")
            if choice_type == "named":
                name = value.get("name")
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("tool_choice.name is required when tool_choice.type=named")
                return {"type": "named", "name": name.strip()}
            raise ValueError("tool_choice.type must be 'named' for object form")
        raise ValueError("tool_choice must be a string or object")

    @field_validator("mcp")
    @classmethod
    def validate_mcp_config(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is None:
            return value
        servers = value.get("servers")
        if servers is not None:
            if not isinstance(servers, list):
                raise ValueError("mcp.servers must be a list")
            for server in servers:
                if not isinstance(server, dict):
                    raise ValueError("mcp.servers entries must be objects")
                server_id = server.get("id")
                if not isinstance(server_id, str) or not server_id.strip():
                    raise ValueError("mcp.servers[].id must be a non-empty string")
                require_approval = server.get("require_approval")
                if require_approval is not None and require_approval not in {"always", "never"}:
                    raise ValueError("mcp.servers[].require_approval must be 'always' or 'never'")
        return value


class PromptBuilderMetadata(SQLModel):
    tags: list[str] | None = Field(default=None)
    notes: str | None = Field(default=None, max_length=5000)
    template_id: str | None = Field(default=None, max_length=200)
    template_setup: dict[str, Any] | None = Field(default=None)


class PromptConfigDraft(SQLModel):
    provider: PromptProviderBinding
    model: PromptModelBinding
    input: PromptInputPayload
    params: PromptParams
    tools: PromptToolingConfig | None = Field(default=None)
    metadata: PromptBuilderMetadata | None = Field(default=None)


class PromptConfigValidationIssue(SQLModel):
    code: str
    severity: Literal["warning", "error"]
    message: str
    path: str | None = None


class PromptConfigValidationResponse(SQLModel):
    issues: list[PromptConfigValidationIssue]


class PromptConfigResolvePreviewRequest(SQLModel):
    agent_slug: str = Field(max_length=50)
    room_id: uuid.UUID | None = Field(default=None)
    payload: PromptConfigDraft | None = Field(default=None)


class PromptConfigResolvePreviewResponse(SQLModel):
    effective_config: dict[str, Any]
    provenance: dict[str, str]


class PromptConfigBase(SQLModel):
    slug: str = Field(min_length=1, max_length=100)
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    metadata_json: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    is_archived: bool = Field(default=False)


class PromptConfigCreate(SQLModel):
    slug: str | None = Field(default=None, min_length=1, max_length=100)
    name: str = Field(max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    metadata_json: dict[str, Any] | None = Field(default=None)
    payload: PromptConfigDraft
    commit_message: str | None = Field(default="Initial version", max_length=500)


class PromptConfigUpdate(SQLModel):
    slug: str | None = Field(default=None, max_length=100)
    name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, max_length=1000)
    metadata_json: dict[str, Any] | None = Field(default=None)
    is_archived: bool | None = Field(default=None)


class PromptConfig(PromptConfigBase, table=True):
    __tablename__ = "prompt_configs"
    __table_args__ = (UniqueConstraint("slug", name="uq_prompt_config_slug"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    latest_version: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None, sa_column_kwargs={"onupdate": datetime.now})


class PromptConfigPublic(PromptConfigBase):
    id: uuid.UUID
    owner_id: uuid.UUID | None
    latest_version: int
    created_at: datetime
    updated_at: datetime | None


class PromptConfigsPublic(SQLModel):
    data: list[PromptConfigPublic]
    count: int


class PromptConfigVersionBase(SQLModel):
    version_number: int = Field(ge=1)
    parent_version_id: uuid.UUID | None = Field(default=None)
    commit_message: str | None = Field(default=None, max_length=500)
    payload_json: dict[str, Any] = Field(sa_column=Column(JSON))
    created_by: uuid.UUID | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)


class PromptConfigVersion(PromptConfigVersionBase, table=True):
    __tablename__ = "prompt_config_versions"
    __table_args__ = (UniqueConstraint("prompt_config_id", "version_number"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    prompt_config_id: uuid.UUID = Field(
        foreign_key="prompt_configs.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )


class PromptConfigVersionPublic(SQLModel):
    id: uuid.UUID
    prompt_config_id: uuid.UUID
    version_number: int
    parent_version_id: uuid.UUID | None = Field(default=None)
    commit_message: str | None = Field(default=None)
    payload: PromptConfigDraft
    created_by: uuid.UUID | None = Field(default=None)
    created_at: datetime


class PromptConfigVersionsPublic(SQLModel):
    data: list[PromptConfigVersionPublic]
    count: int


class PromptConfigWorkingCopyBase(SQLModel):
    base_version: int | None = Field(default=None)
    payload_json: dict[str, Any] = Field(sa_column=Column(JSON))
    has_uncommitted_changes: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.now)
    updated_by: uuid.UUID | None = Field(default=None)


class PromptConfigWorkingCopy(PromptConfigWorkingCopyBase, table=True):
    __tablename__ = "prompt_config_working_copies"
    __table_args__ = (UniqueConstraint("prompt_config_id"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    prompt_config_id: uuid.UUID = Field(
        foreign_key="prompt_configs.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )


class PromptConfigWorkingCopyPublic(SQLModel):
    id: uuid.UUID
    prompt_config_id: uuid.UUID
    base_version: int | None
    payload: PromptConfigDraft
    has_uncommitted_changes: bool
    updated_at: datetime
    updated_by: uuid.UUID | None = None


class PromptConfigWorkingCopyUpdate(SQLModel):
    payload: PromptConfigDraft
    base_version: int | None = Field(default=None)
    has_uncommitted_changes: bool | None = Field(default=True)


class PromptConfigCommitRequest(SQLModel):
    commit_message: str | None = Field(default=None, max_length=500)
    parent_version_id: uuid.UUID | None = Field(default=None)


class PromptConfigResetWorkingCopyRequest(SQLModel):
    version_id: uuid.UUID | None = Field(default=None)



# =============================================================================
# Enums / Literals
# =============================================================================


class DemoRuntimePolicy(str, PyEnum):
    """How room runtime is started for a demo session."""

    auto = "auto"
    manual = "manual"
    owner_only = "owner_only"


class DemoPersonaPolicy(str, PyEnum):
    """How a user persona is selected when runtime starts."""

    first_available = "first_available"
    fixed_user_persona = "fixed_user_persona"
    manual_prompt = "manual_prompt"


class DemoChatMode(str, PyEnum):
    """UI mode for chat surfaces in demo routes."""

    participant = "participant"
    observer = "observer"


class DemoLayoutMode(str, PyEnum):
    """Preferred shell layout mode."""

    panels = "panels"
    tabs = "tabs"


class DemoCompositionSource(str, PyEnum):
    """How a resolved composition was produced."""

    demo_config = "demo_config"
    session_override = "session_override"
    type_defaults = "type_defaults"


DemoPanelKind = Literal[
    "chat",
    "storyRuntime",
    "participantPanel",
    "content",
    "a2ui",
    "debug",
    "canvas",
    "storyEditor",
    "storyPlayer",
    "storyPlayerPanel",
    "strange",
    "gitView",
    "fileExplorer",
    "fileViewer",
]

DemoPanelProminence = Literal["primary", "auxiliary"]
DemoPanelViewportMode = Literal["panel", "page"]

DemoBlockType = Literal[
    "context",
    "story",
    "storyMetadata",
    "agentRoster",
    "orchestratorState",
    "toolCapability",
    "contributionFeed",
    "content",
    "gitView",
    "fileExplorer",
    "fileViewer",
    "strange",
]
DemoBlockRegion = Literal["top", "primary", "auxiliary", "footer"]
DemoBlockVisibility = Literal["visible", "hidden_unmounted", "hidden_mounted"]


# =============================================================================
# Panel Options
# =============================================================================


class DemoContentMetadataConstraints(SQLModel):
    """Optional constraints applied by content renderers."""

    isTrustedSource: bool | None = Field(default=None)
    cacheKey: str | None = Field(default=None)


class DemoContentMetadata(SQLModel):
    """Metadata envelope for renderer hints and formatting options."""

    variant: str | None = Field(default=None, max_length=100)
    label: str | None = Field(default=None, max_length=200)
    constraints: DemoContentMetadataConstraints | None = Field(default=None)
    options: dict[str, Any] | None = Field(default=None)


class DemoContent(SQLModel):
    """
    Canonical renderable content payload for demo panels and blocks.

    This mirrors the frontend ContentRenderer contract:
    - format: canonical content format discriminator
    - value: renderable payload
    - metadata: optional display/configuration hints
    """

    id: str | None = Field(default=None, max_length=120)
    format: ContentFormat
    value: str | int | float | bool | dict[str, Any] | list[Any] | None
    metadata: DemoContentMetadata | None = Field(default=None)


class DemoChatPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    mode: DemoChatMode = Field(default=DemoChatMode.participant)
    include_internal_messages: bool = Field(default=False)


class DemoStoryRuntimePanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    send_runtime_events_to_chat: bool = Field(default=True)
    viewer_mode: bool = Field(default=False)


DemoRepoSource = Literal["user_repo", "shadow_repo"]
DemoRepoEntityIdMode = Literal["explicit", "metadata"]
DemoGitViewDisplayMode = Literal["split", "explorer", "viewer"]
DemoRepoFileViewerPathMode = Literal["selection", "fixed", "readme"]


class DemoGitViewPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    source: DemoRepoSource = Field(default="user_repo")
    entity_type: str = Field(default="user_repo", max_length=100)
    entity_id_mode: DemoRepoEntityIdMode = Field(default="metadata")
    entity_id: str | None = Field(default=None, max_length=255)
    entity_id_metadata_key: str | None = Field(default="repo_id", max_length=255)
    selection_key: str | None = Field(default=None, max_length=255)
    initial_path: str = Field(default="", max_length=2000)
    display_mode: DemoGitViewDisplayMode = Field(default="split")
    path_mode: DemoRepoFileViewerPathMode = Field(default="selection")
    fixed_path: str = Field(default="", max_length=2000)
    ref: str | None = Field(default=None, max_length=255)
    commit_limit: int = Field(default=10, ge=1)
    show_file_content: bool = Field(default=True)
    show_config_json: bool = Field(default=False)
    show_path_badge: bool = Field(default=True)
    show_copy_control: bool = Field(default=True)
    show_sizes: bool = Field(default=True)
    show_commit_badge: bool = Field(default=True)
    empty_label: str | None = Field(default=None, max_length=500)
    extras: dict[str, Any] = Field(default_factory=dict)


class DemoFileExplorerPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    source: DemoRepoSource = Field(default="user_repo")
    entity_type: str = Field(default="user_repo", max_length=100)
    entity_id_mode: DemoRepoEntityIdMode = Field(default="metadata")
    entity_id: str | None = Field(default=None, max_length=255)
    entity_id_metadata_key: str | None = Field(default="repo_id", max_length=255)
    initial_path: str = Field(default="", max_length=2000)
    ref: str | None = Field(default=None, max_length=255)
    selection_key: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=200)
    show_sizes: bool = Field(default=True)
    show_commit_badge: bool = Field(default=True)
    empty_label: str | None = Field(default=None, max_length=500)
    extras: dict[str, Any] = Field(default_factory=dict)


class DemoFileViewerPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    source: DemoRepoSource = Field(default="user_repo")
    entity_type: str = Field(default="user_repo", max_length=100)
    entity_id_mode: DemoRepoEntityIdMode = Field(default="metadata")
    entity_id: str | None = Field(default=None, max_length=255)
    entity_id_metadata_key: str | None = Field(default="repo_id", max_length=255)
    path_mode: DemoRepoFileViewerPathMode = Field(default="selection")
    fixed_path: str = Field(default="", max_length=2000)
    ref: str | None = Field(default=None, max_length=255)
    selection_key: str | None = Field(default=None, max_length=255)
    title: str | None = Field(default=None, max_length=200)
    show_path_badge: bool = Field(default=True)
    show_copy_control: bool = Field(default=True)
    empty_label: str | None = Field(default=None, max_length=500)
    extras: dict[str, Any] = Field(default_factory=dict)

class DemoContentPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    """
    Content payload for 'content' panel kind.

    Expected format aligns with frontend ContentRenderer contract.
    """

    sticky: bool = Field(default=True)
    content_json: DemoContent | None = Field(default=None)


class DemoParticipantPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    showUsers: bool = Field(default=True)
    showAgents: bool = Field(default=True)
    compact: bool = Field(default=False)
    allowQuickAdd: bool = Field(default=True)


class DemoCanvasPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    extras: dict[str, Any] = Field(default_factory=dict)


class DemoA2UIPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    extras: dict[str, Any] = Field(default_factory=dict)


class DemoDebugPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    extras: dict[str, Any] = Field(default_factory=dict)


class DemoStoryEditorPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    extras: dict[str, Any] = Field(default_factory=dict)


class DemoStoryPlayerPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    viewer_mode: bool = Field(default=False)
    extras: dict[str, Any] = Field(default_factory=dict)


class DemoStoryPlayerLegacyPanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    viewer_mode: bool = Field(default=False)
    extras: dict[str, Any] = Field(default_factory=dict)


class DemoStrangePanelOptions(SQLModel):
    model_config = {"extra": "forbid"}

    extras: dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Panel Specs
# =============================================================================


class DemoPanelSpecBase(SQLModel):
    id: str = Field(min_length=1, max_length=100)
    kind: DemoPanelKind
    prominence: DemoPanelProminence = Field(default="primary")
    order: int = Field(default=1, ge=1)
    title: str | None = Field(default=None, max_length=200)
    theme_id: UUID | None = Field(
        default=None,
        description=(
            "Optional panel-level theme override. "
            "If absent, composition/page theme resolution applies."
        ),
    )
    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Panel-level presentation overrides (e.g., viewer/compact/chrome mode)."
        ),
    )

    default_size: int | None = Field(default=None, ge=1, le=100)
    min_size: int | None = Field(default=None, ge=1, le=100)
    max_size: int | None = Field(default=None, ge=1, le=100)
    viewport_mode: DemoPanelViewportMode = Field(default="panel")

    @model_validator(mode="after")
    def validate_size_bounds(self) -> "DemoPanelSpecBase":
        if (
            self.min_size is not None
            and self.max_size is not None
            and self.min_size > self.max_size
        ):
            raise ValueError("Panel min_size cannot be greater than max_size")
        if (
            self.default_size is not None
            and self.min_size is not None
            and self.default_size < self.min_size
        ):
            raise ValueError("Panel default_size cannot be less than min_size")
        if (
            self.default_size is not None
            and self.max_size is not None
            and self.default_size > self.max_size
        ):
            raise ValueError("Panel default_size cannot be greater than max_size")
        return self


class DemoChatPanelSpec(DemoPanelSpecBase):
    kind: Literal["chat"] = "chat"
    options: DemoChatPanelOptions = Field(default_factory=DemoChatPanelOptions)

class DemoGitViewPanelSpec(DemoPanelSpecBase):
    kind: Literal["gitView"] = "gitView"
    options: DemoGitViewPanelOptions = Field(default_factory=DemoGitViewPanelOptions)

class DemoFileExplorerPanelSpec(DemoPanelSpecBase):
    kind: Literal["fileExplorer"] = "fileExplorer"
    options: DemoFileExplorerPanelOptions = Field(default_factory=DemoFileExplorerPanelOptions)


class DemoFileViewerPanelSpec(DemoPanelSpecBase):
    kind: Literal["fileViewer"] = "fileViewer"
    options: DemoFileViewerPanelOptions = Field(default_factory=DemoFileViewerPanelOptions)


class DemoStoryRuntimePanelSpec(DemoPanelSpecBase):
    kind: Literal["storyRuntime"] = "storyRuntime"
    options: DemoStoryRuntimePanelOptions = Field(
        default_factory=DemoStoryRuntimePanelOptions
    )


class DemoContentPanelSpec(DemoPanelSpecBase):
    kind: Literal["content"] = "content"
    options: DemoContentPanelOptions = Field(default_factory=DemoContentPanelOptions)


class DemoParticipantPanelSpec(DemoPanelSpecBase):
    kind: Literal["participantPanel"] = "participantPanel"
    options: DemoParticipantPanelOptions = Field(
        default_factory=DemoParticipantPanelOptions
    )


class DemoCanvasPanelSpec(DemoPanelSpecBase):
    kind: Literal["canvas"] = "canvas"
    options: DemoCanvasPanelOptions = Field(default_factory=DemoCanvasPanelOptions)


class DemoA2UIPanelSpec(DemoPanelSpecBase):
    kind: Literal["a2ui"] = "a2ui"
    options: DemoA2UIPanelOptions = Field(default_factory=DemoA2UIPanelOptions)


class DemoDebugPanelSpec(DemoPanelSpecBase):
    kind: Literal["debug"] = "debug"
    options: DemoDebugPanelOptions = Field(default_factory=DemoDebugPanelOptions)


class DemoStoryEditorPanelSpec(DemoPanelSpecBase):
    kind: Literal["storyEditor"] = "storyEditor"
    options: DemoStoryEditorPanelOptions = Field(
        default_factory=DemoStoryEditorPanelOptions
    )


class DemoStoryPlayerPanelSpec(DemoPanelSpecBase):
    kind: Literal["storyPlayer"] = "storyPlayer"
    options: DemoStoryPlayerPanelOptions = Field(
        default_factory=DemoStoryPlayerPanelOptions
    )


class DemoStoryPlayerLegacyPanelSpec(DemoPanelSpecBase):
    kind: Literal["storyPlayerPanel"] = "storyPlayerPanel"
    options: DemoStoryPlayerLegacyPanelOptions = Field(
        default_factory=DemoStoryPlayerLegacyPanelOptions
    )


class DemoStrangePanelSpec(DemoPanelSpecBase):
    kind: Literal["strange"] = "strange"
    options: DemoStrangePanelOptions = Field(default_factory=DemoStrangePanelOptions)


DemoPanelSpec = Annotated[
    DemoChatPanelSpec
        | DemoStoryRuntimePanelSpec
        | DemoContentPanelSpec
        | DemoParticipantPanelSpec
        | DemoCanvasPanelSpec
        | DemoA2UIPanelSpec
        | DemoDebugPanelSpec
        | DemoStoryEditorPanelSpec
        | DemoStoryPlayerPanelSpec
        | DemoStoryPlayerLegacyPanelSpec
        | DemoStrangePanelSpec
        | DemoGitViewPanelSpec
        | DemoFileExplorerPanelSpec
        | DemoFileViewerPanelSpec,
    Field(discriminator="kind"),
]


# =============================================================================
# Block Specs
# =============================================================================


class DemoBlockSpecBase(SQLModel):
    id: str = Field(min_length=1, max_length=100)
    type: DemoBlockType
    region: DemoBlockRegion = Field(default="top")
    order: int = Field(default=1, ge=1)
    title: str | None = Field(default=None, max_length=200)
    visibility: DemoBlockVisibility = Field(default="visible")
    theme_id: UUID | None = Field(
        default=None,
        description=(
            "Optional block-level theme override. "
            "If absent, composition/page theme resolution applies."
        ),
    )
    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Block-level presentation overrides (e.g., density, chrome, emphasis)."
        ),
    )


class DemoContextBlockSpec(DemoBlockSpecBase):
    type: Literal["context"] = "context"
    config_json: dict[str, Any] = Field(default_factory=dict)
    content_json: DemoContent | None = Field(default=None)


class DemoContentBlockSpec(DemoBlockSpecBase):
    type: Literal["content"] = "content"
    config_json: dict[str, Any] = Field(default_factory=dict)
    content_json: DemoContent | None = Field(default=None)


class DemoStoryBlockSpec(DemoBlockSpecBase):
    type: Literal["story"] = "story"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoStoryMetadataBlockSpec(DemoBlockSpecBase):
    type: Literal["storyMetadata"] = "storyMetadata"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoAgentRosterBlockSpec(DemoBlockSpecBase):
    type: Literal["agentRoster"] = "agentRoster"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoOrchestratorStateBlockSpec(DemoBlockSpecBase):
    type: Literal["orchestratorState"] = "orchestratorState"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoToolCapabilityBlockSpec(DemoBlockSpecBase):
    type: Literal["toolCapability"] = "toolCapability"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoContributionFeedBlockSpec(DemoBlockSpecBase):
    type: Literal["contributionFeed"] = "contributionFeed"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoGitViewBlockSpec(DemoBlockSpecBase):
    type: Literal["gitView"] = "gitView"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoFileExplorerBlockSpec(DemoBlockSpecBase):
    type: Literal["fileExplorer"] = "fileExplorer"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoFileViewerBlockSpec(DemoBlockSpecBase):
    type: Literal["fileViewer"] = "fileViewer"
    config_json: dict[str, Any] = Field(default_factory=dict)


class DemoStrangeBlockSpec(DemoBlockSpecBase):
    type: Literal["strange"] = "strange"
    config_json: dict[str, Any] = Field(default_factory=dict)


DemoBlockSpec = Annotated[
    DemoContextBlockSpec
        | DemoContentBlockSpec
        | DemoStoryBlockSpec
        | DemoStoryMetadataBlockSpec
        | DemoAgentRosterBlockSpec
        | DemoOrchestratorStateBlockSpec
        | DemoToolCapabilityBlockSpec
        | DemoContributionFeedBlockSpec
        | DemoGitViewBlockSpec
        | DemoFileExplorerBlockSpec
        | DemoFileViewerBlockSpec
        | DemoStrangeBlockSpec,
    Field(discriminator="type"),
]


# =============================================================================
# Composition Models (Base / Create / Update / Public / Collection)
# =============================================================================


class DemoPageCompositionBase(SQLModel):
    """
    Canonical demo composition contract consumed by frontend renderers.

    Notes:
    - panels and blocks are composable and independently ordered.
    - runtime/persona/chat policies are route-level behavior contracts.
    """

    schema_version: int = Field(default=1, ge=1)
    layout_mode: DemoLayoutMode = Field(default=DemoLayoutMode.panels)

    runtime_policy: DemoRuntimePolicy = Field(default=DemoRuntimePolicy.auto)
    persona_policy: DemoPersonaPolicy = Field(default=DemoPersonaPolicy.first_available)
    chat_mode: DemoChatMode = Field(default=DemoChatMode.participant)

    fixed_user_persona_id: UUID | None = Field(
        default=None,
        description=(
            "Required when persona_policy=fixed_user_persona. "
            "Ignored by other persona policies."
        ),
    )

    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Composition-level presentation overrides for DemoShell/layout/header."
        ),
    )

    panels: list[DemoPanelSpec] = Field(default_factory=list)
    blocks: list[DemoBlockSpec] = Field(default_factory=list)
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    @field_validator("panels", mode="after")
    @classmethod
    def validate_panels(cls, value: list[DemoPanelSpec]) -> list[DemoPanelSpec]:
        panel_ids = [panel.id for panel in value]
        if len(panel_ids) != len(set(panel_ids)):
            raise ValueError("Panel IDs must be unique")

        page_sized = [panel for panel in value if panel.viewport_mode == "page"]
        if len(page_sized) > 1:
            raise ValueError("At most one panel may use viewport_mode='page'")

        return value

    @field_validator("blocks", mode="after")
    @classmethod
    def validate_blocks(cls, value: list[DemoBlockSpec]) -> list[DemoBlockSpec]:
        block_ids = [block.id for block in value]
        if len(block_ids) != len(set(block_ids)):
            raise ValueError("Block IDs must be unique")

        return value

    @model_validator(mode="after")
    def validate_policy_dependencies(self) -> "DemoPageCompositionBase":
        if (
            self.persona_policy == DemoPersonaPolicy.fixed_user_persona
            and self.fixed_user_persona_id is None
        ):
            raise ValueError(
                "fixed_user_persona_id is required when "
                "persona_policy=fixed_user_persona"
            )

        if not self.panels and not self.blocks:
            raise ValueError(
                "Composition must include at least one panel or one block"
            )

        return self


class DemoPageCompositionCreate(DemoPageCompositionBase):
    demo_config_id: UUID = Field(description="Owning DemoConfig ID")


class DemoPageCompositionUpdate(SQLModel):
    schema_version: int | None = Field(default=None, ge=1)
    layout_mode: DemoLayoutMode | None = None

    runtime_policy: DemoRuntimePolicy | None = None
    persona_policy: DemoPersonaPolicy | None = None
    chat_mode: DemoChatMode | None = None

    fixed_user_persona_id: UUID | None = None
    page_theme_id: UUID | None = None
    cards_theme_id: UUID | None = None
    presentation_json: dict[str, Any] | None = None

    panels: list[DemoPanelSpec] | None = None
    blocks: list[DemoBlockSpec] | None = None
    metadata_json: dict[str, Any] | None = None


class DemoPageCompositionPublic(DemoPageCompositionBase):
    id: UUID
    demo_config_id: UUID
    owner_id: UUID | None
    created_at: datetime
    updated_at: datetime


class DemoPageCompositionsPublic(SQLModel):
    data: list[DemoPageCompositionPublic]
    count: int


# =============================================================================
# Persistence Models (table=True)
# =============================================================================


class DemoPageComposition(DemoPageCompositionBase, table=True):
    """
    Persisted composition template for a DemoConfig.

    One composition record per demo_config_id. This acts as the canonical
    template used to resolve DemoShell composition.
    """

    __tablename__ = "demo_page_compositions"
    __table_args__ = (
        UniqueConstraint(
            "demo_config_id",
            name="uq_demo_page_composition_demo_config",
        ),
    )

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    demo_config_id: UUID = Field(foreign_key="demo_configs.id", index=True)
    owner_id: UUID | None = Field(default=None, foreign_key="user.id", index=True)

    # Persist typed composition data as JSONB; API models validate the shape.
    panels: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSONB))
    blocks: list[dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSONB))
    presentation_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSONB),
    )
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserDemoPageCompositionOverrideBase(SQLModel):
    """
    Per-user override record for a demo composition.

    If use_composition_defaults=True, override_json is ignored.
    """

    use_composition_defaults: bool = Field(default=True)
    override_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))
    metadata_json: dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSONB))


class UserDemoPageCompositionOverrideCreate(UserDemoPageCompositionOverrideBase):
    demo_config_id: UUID
    user_id: UUID


class UserDemoPageCompositionOverrideUpdate(SQLModel):
    use_composition_defaults: bool | None = None
    override_json: dict[str, Any] | None = None
    metadata_json: dict[str, Any] | None = None


class UserDemoPageCompositionOverride(UserDemoPageCompositionOverrideBase, table=True):
    """
    Optional user-level composition override.

    At most one override record per (user_id, demo_config_id).
    """

    __tablename__ = "user_demo_page_composition_overrides"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "demo_config_id",
            name="uq_user_demo_page_composition_override",
        ),
    )

    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", index=True)
    demo_config_id: UUID = Field(foreign_key="demo_configs.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserDemoPageCompositionOverridePublic(UserDemoPageCompositionOverrideBase):
    id: UUID
    user_id: UUID
    demo_config_id: UUID
    created_at: datetime
    updated_at: datetime


class UserDemoPageCompositionOverridesPublic(SQLModel):
    data: list[UserDemoPageCompositionOverridePublic]
    count: int


# =============================================================================
# Resolve / Runtime Shapes
# =============================================================================


class ResolveDemoPageCompositionResponse(SQLModel):
    """
    Resolved composition for route entry points.
    """

    demo_config_id: UUID
    composition: DemoPageCompositionBase
    source: DemoCompositionSource
    created: bool = Field(
        description=(
            "True when a new composition record was created during resolution "
            "(e.g., first-touch copy from defaults)."
        )
    )


class DemoResolvedRoomContext(SQLModel):
    room_id: UUID
    story_id: UUID | None = None
    title: str | None = None
    can_write: bool = False


class DemoResolvedRuntimeContext(SQLModel):
    has_runtime: bool = False
    runtime_policy: DemoRuntimePolicy
    persona_policy: DemoPersonaPolicy
    auto_start_attempted: bool = False
    auto_start_succeeded: bool = False
    auto_start_error: str | None = None


class ResolveDemoEntryPayload(SQLModel):
    """
    Proposed route payload for /demos/{slug}/session resolution.

    This consolidates route orchestration data into one API response and
    avoids frontend-side recomposition drift.
    """

    # Existing response objects
    demo_config_id: UUID
    demo_session_id: UUID
    created: bool

    # Resolved composition and execution context
    composition: DemoPageCompositionBase
    composition_source: DemoCompositionSource
    room: DemoResolvedRoomContext
    runtime: DemoResolvedRuntimeContext


class DemoCanvasRenderRequest(SQLModel):
    panel_id: str | None = None
    script_name: str = Field(default="simple_svg")
    script_input: dict[str, Any] = Field(default_factory=dict)
    title: str = Field(default="Tesser Render")
    subtitle: str | None = None
    persist_to_composition: bool = True
    commit_to_shadow_repo: bool = True


class DemoCanvasRenderResponse(SQLModel):
    demo_config_id: UUID
    panel_id: str
    request_id: str | None = None
    status: str
    svg: str
    persisted: bool
    shadow_commit_sha: str | None = None


class DemoCanvasRenderJobResponse(SQLModel):
    demo_config_id: UUID
    panel_id: str
    job_id: str
    request_id: str | None = None
    script_name: str | None = None
    status: str
    runtime_profile: str | None = None
    resolved_capabilities: list[str] = Field(default_factory=list)
    queued_at: str | None = None
    completed_at: str | None = None
    svg: str | None = None
    persisted: bool = False
    shadow_commit_sha: str | None = None
    error: str | None = None


class TesserScriptPublic(SQLModel):
    name: str
    description: str
    supported_formats: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    help_text: str | None = None
    source_path: str | None = None
    kind: str | None = None


class TesserScriptsPublic(SQLModel):
    data: list[TesserScriptPublic]
    count: int


class TesserScriptRunRequest(SQLModel):
    script_input: dict[str, Any] = Field(default_factory=dict)
    room_id: str | None = None
    timeout_seconds: float = Field(default=15.0, ge=1.0, le=300.0)


class TesserScriptEnqueueRequest(SQLModel):
    script_input: dict[str, Any] = Field(default_factory=dict)
    room_id: str | None = None


class TesserScriptRunResponse(SQLModel):
    request_id: str | None = None
    script_name: str
    status: str
    render: dict[str, Any] | None = None
    error: str | None = None
    completed_at: str | None = None
    worker_id: str | None = None


class TesserScriptEnqueueResponse(SQLModel):
    request_id: str
    job_id: str
    script_name: str
    status: str
    runtime_profile: str | None = None
    resolved_capabilities: list[str] = Field(default_factory=list)
    queued_at: str | None = None
    completed_at: str | None = None
    render: dict[str, Any] | None = None
    error: str | None = None
    worker_id: str | None = None


class TesserJobStatusResponse(SQLModel):
    request_id: str
    job_id: str
    status: str
    script_name: str | None = None
    room_id: str | None = None
    runtime_profile: str | None = None
    resolved_capabilities: list[str] = Field(default_factory=list)
    queued_at: str | None = None
    completed_at: str | None = None
    render: dict[str, Any] | None = None
    error: str | None = None
    worker_id: str | None = None


class TesserScriptHelpResponse(SQLModel):
    script_name: str
    help_text: str | None = None
    description: str | None = None
    supported_formats: list[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)


class TesserExamplesIndexResponse(SQLModel):
    path: str
    content: str


# Resolution precedence (service-level contract):
# 1) user_demo_page_composition_overrides where use_composition_defaults=False
# 2) demo_page_compositions for demo_config_id
# 3) fallback composition from DemoConfig defaults (panels/layout/metadata)


# ==================== ShadowUser Models ====================

class ShadowUserBase(SQLModel):
    """
    Base model for Shadow Forgejo user profile mappings.

    Maps application users to their shadow profile repository.
    This is system-managed and invisible to end users - they never
    interact with Forgejo directly. Acts like a CMS for user profiles.
    """
    forgejo_repo_name: str = Field(max_length=255)
    forgejo_repo_id: int | None = Field(default=None)


class ShadowUserCreate(ShadowUserBase):
    """Input model for creating ShadowUser mapping (system use only)"""
    user_id: uuid.UUID


class ShadowUserUpdate(SQLModel):
    """Update model for ShadowUser"""
    forgejo_repo_id: int | None = None


class ShadowUser(ShadowUserBase, table=True):
    """
    Database model for user profile shadow tracking.

    System-managed mapping between application User and their
    shadow profile repository. Users don't see or control this -
    all operations happen automatically via service accounts.

    The shadow-users service account owns all user profile repos.
    Repo naming: user-{uuid}
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        unique=True,
        nullable=False,
        ondelete="CASCADE"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ShadowUserPublic(ShadowUserBase):
    """Public API response model for ShadowUser (admin use only)"""
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime


class ShadowUsersPublic(SQLModel):
    """Collection response for ShadowUsers"""
    data: list[ShadowUserPublic]
    count: int

# ==================== ShadowRepo Models ====================

class ShadowRepoBase(SQLModel):
    """
    Base model for entity-to-repository mappings.

    Each versioned entity (agent, story, etc.) gets its own
    Forgejo repository following repo-per-entity pattern.

    Repos are owned by service accounts (shadow-agents, shadow-stories)
    not by individual users. This is invisible to end users.
    """
    entity_type: str = Field(max_length=50)  # 'agent', 'story', 'user'
    entity_id: uuid.UUID
    forgejo_repo_name: str = Field(max_length=255)
    forgejo_repo_id: int | None = Field(default=None)


class ShadowRepoCreate(ShadowRepoBase):
    """Input model for creating ShadowRepo (system use only)"""
    owner_id: uuid.UUID  # User who owns this entity
    forked_from_id: uuid.UUID | None = None


class ShadowRepoUpdate(SQLModel):
    """Update model for ShadowRepo"""
    forgejo_repo_id: int | None = None
    forked_from_id: uuid.UUID | None = None


class ShadowRepo(ShadowRepoBase, table=True):
    """
    Database model for entity-to-repo mapping.

    Repo naming convention: {entity_type}-{entity_id_short}
    e.g., agent-550e8400

    Service account ownership by entity_type:
    - 'agent' → shadow-agents service account
    - 'story' → shadow-stories service account
    - 'user'  → shadow-users service account

    forked_from_id enables clone/fork tracking for branching.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
        description="Application user who owns this entity"
    )
    forked_from_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="shadowrepo.id",
        description="Source repo if this is a fork/clone"
    )
    created_at: datetime = Field(default_factory=datetime.now)


class ShadowRepoPublic(ShadowRepoBase):
    """Public API response model for ShadowRepo (admin use only)"""
    id: uuid.UUID
    owner_id: uuid.UUID
    forked_from_id: uuid.UUID | None
    created_at: datetime


class ShadowReposPublic(SQLModel):
    """Collection response for ShadowRepos"""
    data: list[ShadowRepoPublic]
    count: int


class ShadowRepoCommitSummary(SQLModel):
    sha: str
    short_sha: str
    message: str
    author_name: str | None = None
    authored_at: datetime | None = None


class ShadowRepoTreeEntry(SQLModel):
    path: str
    name: str
    entry_type: str
    size_bytes: int | None = None


class ShadowRepoSummary(SQLModel):
    entity_type: str
    entity_id: uuid.UUID
    repo_available: bool
    default_branch: str
    latest_commit_sha: str | None = None
    latest_commit_message: str | None = None
    latest_commit_authored_at: datetime | None = None


class ShadowRepoViewResponse(SQLModel):
    summary: ShadowRepoSummary
    commits: list[ShadowRepoCommitSummary] = Field(default_factory=list)
    tree: list[ShadowRepoTreeEntry] = Field(default_factory=list)
    tree_root_path: str = ""
    ref: str


class ShadowRepoFileContent(SQLModel):
    path: str
    ref: str
    content: str
    encoding: str = "utf-8"
    size_bytes: int
    content_type: str | None = None
    is_binary: bool = False
    is_truncated: bool = False
    truncation_reason: str | None = None
    is_unsupported_preview: bool = False


class UserRepoBase(SQLModel):
    """Base model for user-visible repositories owned by the platform."""

    slug: str = Field(max_length=100)
    display_name: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    source_repo_url: str | None = Field(default=None, max_length=2000)
    source_branch: str = Field(default="main", max_length=255)
    import_status: UserRepoImportStatus = Field(default=UserRepoImportStatus.PENDING)
    import_error: str | None = Field(default=None, max_length=2000)
    imported_at: datetime | None = Field(default=None)
    gogs_repo_name: str = Field(max_length=255)
    gogs_repo_id: int | None = Field(default=None)
    gogs_full_name: str | None = Field(default=None, max_length=255)
    gogs_html_url: str | None = Field(default=None, max_length=1000)
    is_private: bool = Field(default=False)


class UserRepoCreate(UserRepoBase):
    """Input model for creating a user-visible repo."""

    owner_user_id: uuid.UUID


class UserRepoProvisionRequest(SQLModel):
    """Request payload for creating a user-visible repo."""

    source_repo_url: str = Field(max_length=2000)
    display_name: str | None = Field(default=None, max_length=255)
    slug: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    is_private: bool = Field(default=False)


class UserRepoUpdate(SQLModel):
    """Update model for user-visible repos."""

    description: str | None = None
    source_repo_url: str | None = None
    source_branch: str | None = None
    import_status: UserRepoImportStatus | None = None
    import_error: str | None = None
    imported_at: datetime | None = None
    gogs_repo_id: int | None = None
    gogs_full_name: str | None = None
    gogs_html_url: str | None = None
    is_private: bool | None = None


class UserRepo(UserRepoBase, table=True):
    """Database model for user-visible repositories in the `dog` org."""

    __tablename__ = "user_repos"
    __table_args__ = (
        UniqueConstraint("gogs_repo_name", name="uq_user_repos_gogs_repo_name"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRepoPublic(UserRepoBase):
    """Public API response model for a user-visible repo."""

    id: uuid.UUID
    owner_user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    default_branch: str | None = None
    capabilities: "UserRepoViewerCapabilities | None" = None


class UserRepoViewerCapabilities(SQLModel):
    has_file_tree: bool = False
    has_blob_content: bool = False
    has_commit_history: bool = False
    has_search: bool = False
    has_branches: bool = False
    default_branch: str = "main"


class UserRepoSummary(SQLModel):
    repo_id: uuid.UUID
    slug: str
    display_name: str
    repo_available: bool
    default_branch: str
    latest_commit_sha: str | None = None
    latest_commit_message: str | None = None
    latest_commit_authored_at: datetime | None = None


class UserRepoViewResponse(SQLModel):
    summary: UserRepoSummary
    commits: list[ShadowRepoCommitSummary] = Field(default_factory=list)
    tree: list[ShadowRepoTreeEntry] = Field(default_factory=list)
    tree_root_path: str = ""
    ref: str


class UserRepoFileContent(ShadowRepoFileContent):
    pass


class UserRepoReadmeContent(UserRepoFileContent):
    resolved_from_path: str


class UserRepoFileMutationInput(SQLModel):
    path: str = Field(max_length=2000)
    operation: str = Field(max_length=20)
    content: str | None = None
    encoding: str = Field(default="utf-8", max_length=50)


class UserRepoCommitRequest(SQLModel):
    branch: str = Field(default="main", max_length=255)
    mutations: list[UserRepoFileMutationInput] = Field(default_factory=list)
    commit_message: str = Field(max_length=500)
    expected_head_sha: str = Field(max_length=255)


class UserRepoCommitResponse(SQLModel):
    repo_id: uuid.UUID
    branch: str
    previous_head_sha: str
    new_head_sha: str
    commit_message: str
    committed_at: datetime
    changed_paths: list[str] = Field(default_factory=list)

class UserRepoOutboxJob(SQLModel, table=True):
    """
    Outbox job for async user repo provisioning.

    One row represents one pending Gogs provisioning operation for a UserRepo.
    Supports retry with exponential backoff for transient failures.
    """

    __tablename__ = "user_repo_outbox_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_repo_id: uuid.UUID = Field(foreign_key="user_repos.id", index=True)

    status: str = Field(
        default="queued",
        max_length=30,
        index=True,
        description="queued, processing, completed, retryable_error, dead",
    )
    priority: int = Field(default=100, index=True, description="Lower = higher priority")
    attempt_count: int = Field(default=0)
    run_after: datetime = Field(default_factory=datetime.utcnow, index=True)

    locked_at: datetime | None = Field(default=None)
    locked_by: str | None = Field(default=None, max_length=255)

    last_error: str | None = Field(default=None)
    last_error_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class UserReposPublic(SQLModel):
    """Collection response for user-visible repos."""

    data: list[UserRepoPublic]
    count: int


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
    room_id: uuid.UUID = Field(foreign_key="rooms.room_id", unique=True, index=True)
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
    room_id: uuid.UUID = Field(foreign_key="rooms.room_id", index=True)
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


class UserPanelDefaults(SQLModel, table=True):
    """User's global default panel layout (applies to all rooms)"""
    __tablename__ = "user_panel_defaults"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", unique=True, index=True)
    preset_id: str | None = Field(default=None)  # "focus", "collaborate", etc.
    panels: list[dict] = Field(default=[], sa_column=Column(JSON))
    reduce_motion: bool = Field(default=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserPanelDefaultsPublic(SQLModel):
    """Public response for user panel defaults"""
    id: uuid.UUID
    user_id: uuid.UUID
    preset_id: str | None
    panels: list[dict]
    reduce_motion: bool
    updated_at: datetime


class UserPanelDefaultsUpdate(SQLModel):
    """Update payload for user panel defaults"""
    preset_id: str | None = None
    panels: list[dict] | None = None
    reduce_motion: bool | None = None


class PanelPreset(SQLModel, table=True):
    """Panel layout preset (system or user-created)"""
    __tablename__ = "panel_presets"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", index=True)
    name: str
    description: str | None = None
    panels: list[dict] = Field(sa_column=Column(JSON))
    is_system: bool = Field(default=False)
    shared_to_room_id: uuid.UUID | None = Field(default=None, foreign_key="rooms.room_id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PanelPresetPublic(SQLModel):
    """Public response for panel preset"""
    id: uuid.UUID
    owner_id: uuid.UUID | None
    name: str
    description: str | None
    panels: list[dict]
    is_system: bool
    created_at: datetime


# ==================== ShadowVersion Models ====================

class ShadowVersionBase(SQLModel):
    """
    Base model for version/commit records.
    
    Each save operation creates a new version with full
    JSON snapshot of entity state.
    """
    commit_sha: str = Field(max_length=40)
    version_number: int
    message: str = Field(max_length=500)


class ShadowVersionCreate(ShadowVersionBase):
    """Input model for creating ShadowVersion"""
    shadow_repo_id: uuid.UUID
    snapshot_json: dict[str, Any]  # Full entity state
    created_by_id: uuid.UUID


class ShadowVersionUpdate(SQLModel):
    """Update model for ShadowVersion (immutable - not used)"""
    pass  # Versions are immutable


class ShadowVersion(ShadowVersionBase, table=True):
    """
    Database model for version records.
    
    Stores complete JSON snapshot of entity at each save.
    Pretty-printed JSON for git diff readability.
    Immutable once created - never updated.
    """
    __table_args__ = (UniqueConstraint("shadow_repo_id", "version_number"),)

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    shadow_repo_id: uuid.UUID = Field(
        foreign_key="shadowrepo.id",
        nullable=False,
        ondelete="CASCADE"
    )
    snapshot_json: dict[str, Any] = Field(
        sa_column=Column(JSON),
        description="Full entity state at this version"
    )
    created_by_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        description="User who created this version"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    # Milestone 3: async Forgejo commit finalization metadata
    status: str = Field(default="committed", max_length=20)
    committed_at: datetime | None = Field(default=None)
    last_error: str | None = Field(default=None)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ShadowVersionPublic(ShadowVersionBase):
    """Public API response model for ShadowVersion"""
    id: uuid.UUID
    shadow_repo_id: uuid.UUID
    created_by_id: uuid.UUID
    created_at: datetime
    # Note: snapshot_json excluded by default (large), use detail endpoint


class ShadowVersionDetail(ShadowVersionPublic):
    """Detailed response including full snapshot"""
    snapshot_json: dict[str, Any]


class ShadowVersionsPublic(SQLModel):
    """Collection response for ShadowVersions"""
    data: list[ShadowVersionPublic]
    count: int

# ==================== Shadow Outbox Models (Milestone 3) ====================

class ShadowOutboxJobBase(SQLModel):
    """
    Durable outbox job for asynchronous Shadow Forgejo writes.

    One row represents one intended Forgejo write for one ShadowVersion.
    """
    shadow_repo_id: uuid.UUID = Field(foreign_key="shadowrepo.id", nullable=False, index=True)
    shadow_version_id: uuid.UUID = Field(
        foreign_key="shadowversion.id",
        nullable=False,
        unique=True,
        index=True,
        description="Idempotency anchor: one job per ShadowVersion"
    )
    entity_type: str = Field(max_length=50, index=True)
    entity_id: uuid.UUID = Field(index=True)

    status: str = Field(default="queued", max_length=30, index=True)
    attempt_count: int = Field(default=0)
    run_after: datetime = Field(default_factory=datetime.utcnow, index=True)

    locked_at: datetime | None = Field(default=None)
    locked_by: str | None = Field(default=None, max_length=255)

    last_error: str | None = Field(default=None)
    last_error_at: datetime | None = Field(default=None)

    priority: int = Field(default=100)


class ShadowOutboxJob(ShadowOutboxJobBase, table=True):
    __tablename__ = "shadow_outbox_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ShadowOutboxAttemptBase(SQLModel):
    outbox_job_id: uuid.UUID = Field(foreign_key="shadow_outbox_jobs.id", nullable=False, index=True)
    attempt_number: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: datetime | None = Field(default=None)
    result: str = Field(max_length=30)
    error_type: str | None = Field(default=None, max_length=100)
    error_message: str | None = Field(default=None)
    forgejo_repo: str | None = Field(default=None, max_length=255)
    forgejo_commit_sha: str | None = Field(default=None, max_length=40)


class ShadowOutboxAttempt(ShadowOutboxAttemptBase, table=True):
    __tablename__ = "shadow_outbox_attempts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class ShadowOutboxRepoLeaseBase(SQLModel):
    shadow_repo_id: uuid.UUID = Field(
        foreign_key="shadowrepo.id",
        nullable=False,
        primary_key=True,
        description="One lease row per shadow repo"
    )
    locked_at: datetime | None = Field(default=None)
    locked_by: str | None = Field(default=None, max_length=255)


class ShadowOutboxRepoLease(ShadowOutboxRepoLeaseBase, table=True):
    __tablename__ = "shadow_outbox_repo_leases"


class ShadowRepoVersionCounterBase(SQLModel):
    shadow_repo_id: uuid.UUID = Field(
        foreign_key="shadowrepo.id",
        nullable=False,
        primary_key=True,
        description="Per-repo sequence counter for ShadowVersion.version_number allocation"
    )
    next_version_number: int = Field(default=1)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ShadowRepoVersionCounter(ShadowRepoVersionCounterBase, table=True):
    __tablename__ = "shadow_repo_version_counters"

# ============================================================================
# Shadow Forgejo Relationships
# ============================================================================

# ShadowUser → User (many-to-one)
ShadowUser.user = Relationship(
    back_populates="shadow_user",
    sa_relationship_kwargs={"lazy": "joined"}
)

# User → ShadowUser (one-to-one, reverse)
User.shadow_user = Relationship(
    back_populates="user",
    sa_relationship_kwargs={
        "uselist": False,  # One-to-one
        "lazy": "select"
    }
)

# ShadowRepo → User (many-to-one, entity owner)
ShadowRepo.owner = Relationship(
    back_populates="shadow_repos",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.owner_id]",
        "lazy": "joined"
    }
)

# User → ShadowRepo (one-to-many, entities owned by user)
User.shadow_repos = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.owner_id]",
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)

# ShadowRepo self-referential (forked_from)
ShadowRepo.forked_from = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.forked_from_id]",
        "remote_side": "[ShadowRepo.id]"
    }
)

ShadowRepo.forks = Relationship(
    back_populates="forked_from",
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowRepo.forked_from_id]"
    }
)

# ShadowVersion → ShadowRepo (many-to-one)
ShadowVersion.repo = Relationship(
    back_populates="versions",
    sa_relationship_kwargs={"lazy": "joined"}
)

# ShadowRepo → ShadowVersion (one-to-many)
ShadowRepo.versions = Relationship(
    back_populates="repo",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select",
        "order_by": "ShadowVersion.version_number.desc()"
    }
)

# ShadowVersion → User (many-to-one, created_by)
ShadowVersion.created_by = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[ShadowVersion.created_by_id]",
        "lazy": "joined"
    }
)

Story.state_variables = Relationship(
    back_populates="story",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
StoryStateVariable.story = Relationship(back_populates="state_variables")


# ============================================================================
#  Event Tree Relationships
# ============================================================================

# UserNodeChoice tree structure relationships
UserNodeChoice.parent_choice = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[UserNodeChoice.parent_choice_id]",
        "remote_side": "[UserNodeChoice.id]"
    }
)

UserNodeChoice.children = Relationship(
    back_populates="parent_choice",
    sa_relationship_kwargs={
        "foreign_keys": "[UserNodeChoice.parent_choice_id]"
    }
)

# UserStoryProgress to head choice relationship
UserStoryProgress.head_choice = Relationship(
    sa_relationship_kwargs={
        "foreign_keys": "[UserStoryProgress.head_choice_id]"
    }
)

# ProgressSnapshot → UserStoryProgress (many-to-one)
ProgressSnapshot.progress = Relationship(
    back_populates="snapshots",
    sa_relationship_kwargs={"lazy": "joined"}
)

# ProgressSnapshot → UserNodeChoice (many-to-one)
ProgressSnapshot.choice = Relationship(
    back_populates="snapshots",
    sa_relationship_kwargs={"lazy": "joined"}
)

# UserStoryProgress → ProgressSnapshot (one-to-many, reverse)
UserStoryProgress.snapshots = Relationship(
    back_populates="progress",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)

# UserNodeChoice → ProgressSnapshot (one-to-many, reverse)
UserNodeChoice.snapshots = Relationship(
    back_populates="choice",
    sa_relationship_kwargs={
        "cascade": "all, delete-orphan",
        "lazy": "select"
    }
)


# ============================================================================
# Post-Definition Relationship Binding
# ============================================================================
#
# Per data-model-best-practices.md, complex circular relationships should be
# defined after all classes exist. However, for Rooms and RoomMessages, all relationships
# are already defined inline using string-based forward references, which is
# sufficient for SQLModel to resolve them correctly.
#
# If additional complex relationships are needed in future phases, add them here.

TraitConflictGroup.members = Relationship(
    back_populates="group",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

TraitConflictGroupMember.group = Relationship(back_populates="members")
TraitConflictGroupMember.trait = Relationship(back_populates="conflict_memberships")

# Also add to Trait model:
Trait.conflict_memberships: list["TraitConflictGroupMember"] = Relationship(
    back_populates="trait"
)

# User → UserAgentConfig relationship
User.user_agent_configs = Relationship(
    back_populates="owner",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)


# UserAgentConfig <-> AgentPersona (agent persona library)
UserAgentConfig.agent_personas = Relationship(
    back_populates="user_agent_config",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)
AgentPersona.agent_config = Relationship(back_populates="agent_personas")

# Persona <-> AgentPersona
Persona.agent_personas = Relationship(back_populates="persona")
AgentPersona.persona = Relationship(back_populates="agent_personas")

RoomPanelDefaults.room = Relationship(
    back_populates="panel_defaults"
)

Room.panel_defaults = Relationship(
    back_populates="room",
    sa_relationship_kwargs={
        "foreign_keys": "[RoomPanelDefaults.room_id]",
        "uselist": False
    }
)

# User <-> Page relationship
User.pages = Relationship(back_populates="owner")
Page.owner = Relationship(back_populates="pages")

# DemoConfig <-> DemoSession relationship
DemoConfig.sessions = Relationship(
    back_populates="demo_config",
    sa_relationship_kwargs={"cascade": "all, delete-orphan"},
)
DemoSession.demo_config = Relationship(back_populates="sessions")


# Theme -> User (many-to-one, optional)
# Note: User model assumed to exist in models.py
# owner relationship added where Theme is integrated into main models.py
Theme.owner = Relationship(back_populates="themes")


# ============================================================================
# Workspace Models (Kennel-backed development environments)
# ============================================================================


class WorkspaceStatus(str, PyEnum):
    """Lifecycle state for a kennel-backed workspace."""

    requested = "requested"
    provisioning = "provisioning"
    starting = "starting"
    ready = "ready"
    stopping = "stopping"
    stopped = "stopped"
    failed = "failed"
    destroying = "destroying"
    destroyed = "destroyed"


class WorkspaceFlavour(str, PyEnum):
    """Requested workspace image/profile."""

    base = "base"
    dev = "dev"
    python = "python"
    node = "node"
    jupyter = "jupyter"


class WorkspaceAction(str, PyEnum):
    """Backend-authoritative actions currently allowed for a workspace."""

    destroy = "destroy"
    stop = "stop"
    start = "start"
    request_terminal = "request_terminal"
    discover_services = "discover_services"


class WorkspaceVisibility(str, PyEnum):
    """Projected visibility state for a workspace."""

    private = "private"
    project = "project"
    shared = "shared"


class WorkspaceTerminalStatus(str, PyEnum):
    """Projected terminal availability state for a workspace."""

    unavailable = "unavailable"
    available = "available"
    expired = "expired"


class WorkspaceProjectSummary(SQLModel):
    """Lightweight project projection for workspace responses."""

    id: uuid.UUID
    name: str


class WorkspaceBase(SQLModel):
    """Shared workspace fields for persistence and API models."""

    name: str = Field(min_length=1, max_length=120, index=True)
    flavour: WorkspaceFlavour = Field(default=WorkspaceFlavour.dev)
    kind: str = Field(default="ephemeral", min_length=1, max_length=32)
    status: WorkspaceStatus = Field(default=WorkspaceStatus.requested)
    kennel_name: str | None = Field(default=None, max_length=120)
    kennel_job: str | None = Field(default=None, max_length=120)
    ws_token: str | None = Field(default=None, max_length=255)
    failure_message: str | None = Field(default=None)
    last_transition_at: datetime = Field(default_factory=datetime.utcnow)
    requested_at: datetime | None = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = Field(default=None)
    ready_at: datetime | None = Field(default=None)
    stopped_at: datetime | None = Field(default=None)
    destroyed_at: datetime | None = Field(default=None)
    meta: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class WorkspaceCreate(SQLModel):
    """Request model for provisioning a workspace."""

    name: str = Field(min_length=1, max_length=120)
    flavour: WorkspaceFlavour = WorkspaceFlavour.dev
    kind: str = Field(default="ephemeral", min_length=1, max_length=32)
    repo_url: str | None = Field(default=None, max_length=2000)
    ssh_pubkey: str | None = None
    env_vars: dict[str, str] = Field(default_factory=dict)


class Workspace(WorkspaceBase, table=True):
    """Database model for a user-owned kennel workspace."""

    __tablename__ = "workspaces"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
    )


class WorkspacePublic(WorkspaceBase):
    """Public API response model for a workspace."""

    id: uuid.UUID
    owner_id: uuid.UUID
    allowed_actions: list[WorkspaceAction] = Field(default_factory=list)
    visibility: WorkspaceVisibility = Field(default=WorkspaceVisibility.private)
    project_id: uuid.UUID | None = None
    project_summary: WorkspaceProjectSummary | None = None
    terminal_status: WorkspaceTerminalStatus = Field(default=WorkspaceTerminalStatus.unavailable)
    created_at: datetime
    updated_at: datetime
    terminal_url: str | None = None


class WorkspacesPublic(SQLModel):
    """Collection response model for workspaces."""

    data: list[WorkspacePublic]
    count: int
