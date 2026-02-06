import uuid
from datetime import datetime
from enum import Enum as PyEnum
from typing import Any, Literal, Annotated, Union
from uuid import UUID

from pydantic import  EmailStr, field_validator
from sqlalchemy import JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, Relationship, SQLModel

from app.core.provider_types import TYPE1, TYPE3


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


# ============ Base Models ++++++++


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class UserPersonaBase(SQLModel):
    """Base model for User's instance of a Persona"""

    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    # what other customization fields should we add?


class UserPersonaCreate(UserPersonaBase):
    persona_id: uuid.UUID


class UserPersonaUpdate(SQLModel):
    nickname: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class UserPersona(UserPersonaBase, table=True):
    """Database model for User's instance of a Persona"""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    persona_id: uuid.UUID = Field(foreign_key="persona.id", nullable=False)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(
        default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now}
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

class UserAccessProviderPublic(UserAccessProviderBase):
    """Public API response - NEVER includes API key."""
    id: uuid.UUID


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

class LLMProviderTypeCreate(LLMProviderTypeBase):
    """Input model for creating an LLMProviderType"""
    pass

class LLMProviderTypeBasePartial(SQLModel):
    """Update model for LLM Provider types"""
    name: str | None = Field(max_length=30, description="LLM Provider type", default=None)
    details: str | None = Field(default=None, max_length=500, description="notes if necessary")
    validated: bool | None = Field(default=None, description="updated when proven valid at least once",)
    is_system: bool | None = Field(default=None, description="is this a validated provider_type?" )

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

# UserPersona to User relationship
UserPersona.user = Relationship(back_populates="user_personas")

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
    Room-scoped agent policy settings (prompt + tool rules).
    """

    agent_slug: str | None = Field(
        default=None,
        max_length=50,
        description="Null for room-wide defaults; set for per-agent overrides.",
    )
    prompt_config: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    tool_policy: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    rule_config: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    revision: int = Field(default=0)


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
    prompt_config: dict[str, Any] | None = None
    tool_policy: dict[str, Any] | None = None
    rule_config: dict[str, Any] | None = None
    expected_revision: int | None = None


class RoomAgentSettingsBundle(SQLModel):
    room_defaults: RoomAgentSettingsPublic | None
    agent_overrides: list[RoomAgentSettingsPublic]

    participant_type: Literal["user", "agent"]
    persona_id: uuid.UUID | None = None
    model_name: str | None = Field(default=None, max_length=100)
    user_llm_provider_id: uuid.UUID | None = None

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


class PageCreate(PageBase):
    """Input model for creating a page layout."""

    owner_id: uuid.UUID


class PageLayoutUpdate(SQLModel):
    """Update model for page layout."""

    layout_json: list[dict[str, Any]]
    layout_version: int | None = None


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
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))

    # Behavior flags
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
    scope: str = Field(default="personal")  # "personal" | "system"
    participation_mode: str = Field(default="on_mention")  # "always" | "on_mention" | "manual"

    # Coordinator mode: if True, this agent processes messages FIRST
    # before other agents, acting as an orchestrator that routes to specialists
    is_coordinator: bool = Field(default=False)

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

class UserAgentConfigCreate(UserAgentConfigBase):
     pass

class Type1Create(UserAgentConfigBase):
    provider_type: Literal[TYPE1]
    system_prompt: str
    description: str
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


class Type3Create(UserAgentConfigBase):
    provider_type: Literal[TYPE3]
    system_prompt: str = Field(max_length=5000)
    model_name: str = Field(default="friendly model name")
    is_enabled: bool = Field(default=True)
    is_clonable: bool = Field(default=False)
    is_visible: bool = Field(default=False)
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


UserAgentConfigCreate = Annotated[
    Type1Create | Type3Create,
    Field(discriminator='provider_type')
]

class Type1Update(UserAgentConfigBase):
    provider_type: Literal[TYPE1]
    description: str | None = None # optional for updates, but this will cause validation if it is passed again


class Type3Update(UserAgentConfigBase):
    provider_type: Literal[TYPE3]
    system_prompt: str | None = None # optional for update, but causes validation trigger if passed


UserAgentConfigUpdate = Annotated[
    Type1Update | Type3Update,
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
    agent_metadata: dict | None = Field(default=None, sa_column=Column(JSON))
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None, sa_column=Column(JSON))

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
    agent_metadata: dict | None = Field(default=None)
    is_enabled: bool | None = Field(default=None)
    is_clonable: bool | None = Field(default=None)
    is_visible: bool | None = Field(default=None)
    scope: str | None = Field(default=None)
    participation_mode: str | None = Field(default=None)
    is_coordinator: bool | None = Field(default=None)
    max_tool_iterations: int | None = Field(default=None)
    capabilities: list[str] | None = Field(default=None)

class UserAgentConfigsPublic(SQLModel):
    data: list[UserAgentConfigPublic]
    count: int

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



