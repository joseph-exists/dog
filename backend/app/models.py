import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import EmailStr
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship


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


class QualityState(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    REMOVED = "removed"


class QualitySourceType(str, Enum):
    TRAIT_DEPENDENT = "trait_dependent"
    DEFAULT = "default"
    MANUALLY_ADDED = "manually_added"

class ContentFormat(str, Enum):
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
    # this might need to change to Persona? not sure how to do cascading multiple ownership


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

PersonaTraitLink.trait = Relationship(back_populates="persona_links")

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
UserNodeChoice.to_node = Relationship(
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
        description="UUID string for users, agent name for agents",
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
        description="UUID string for users, agent name for agents",
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
# Message Models (Projection)
# ============================================================================


class RoomMessageBase(SQLModel):
    """Shared properties for Message projection."""

    content: str = Field(description="Message text content")
    sender_type: str = Field(
        max_length=10,
        description="Either 'user' or 'agent'",
    )


class RoomMessageCreate(RoomMessageBase):
    """Properties required when creating a message via API."""

    pass
    # sender_id and agent_name will be injected based on sender_type

class RoomMessageSend(SQLModel):
    """Properties required when sending a message via API."""

    content: str = Field(description="Message text content")


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

    button_options: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class RoomMessagesPublic(SQLModel):
    """Paginated collection of messages."""

    data: list[RoomMessagePublic]
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

class StateValueType(str, Enum):
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
