"""
Refactored Story System Models - Versioned Templates with Player Instances

Organization:
1. Shared/utility models (Message)
2. Story Template models (authoring concern)
3. Story Navigation models (playing concern)
4. Relationship definitions (post-model declaration)

Following TinyFoot best practices:
- Base â†’ Create â†’ Update â†’ Database (table=True) â†’ Public â†’ Collection
- UUID primary keys
- String-based forward references for type hints
- Post-definition relationship binding for circular refs
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import EmailStr
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship


# ==================== Utility Models ====================

class Message(SQLModel):
    message: str


# ==================== Story Template Models (AUTHORING) ====================

class StoryBase(SQLModel):
    """Base model for Story template properties"""
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class StoryCreate(StoryBase):
    """Input model for creating a new Story template"""
    pass


class StoryUpdate(SQLModel):
    """Input model for updating Story template (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    description: str | None = Field(default=None, max_length=1000)  # type: ignore


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
    node_type: str = Field(default="text", max_length=50)  # text, image, choice, etc.
    is_start_node: bool = Field(default=False)
    is_end_node: bool = Field(default=False)


class StoryNodeCreate(StoryNodeBase):
    """Input model for creating a StoryNode"""
    story_id: uuid.UUID
    story_version: int  # Must specify which version this node belongs to


class StoryNodeUpdate(SQLModel):
    """Input model for updating StoryNode (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    content: str | None = Field(default=None)  # type: ignore
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
    started_at: datetime
    updated_at: datetime


class UserStoryProgressesPublic(SQLModel):
    """Collection response for UserStoryProgresses"""
    data: list[UserStoryProgressPublic]
    count: int


# ==================== UserNodeChoice Models (PLAYING) ====================

class UserNodeChoiceBase(SQLModel):
    """
    Base model for recording a player's choice at a node.
    Historical breadcrumb trail through the story.
    """
    choice_text: str = Field(max_length=500)
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    
    # Snapshot of state changes applied by this choice
    state_changes: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))


class UserNodeChoiceCreate(UserNodeChoiceBase):
    """Input model for recording a choice"""
    progress_id: uuid.UUID


class UserNodeChoice(UserNodeChoiceBase, table=True):
    """
    Database model for player's choice history.
    Immutable record of decisions made.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(foreign_key="userstoryprogress.id", nullable=False, ondelete="CASCADE")
    choice_time: datetime = Field(default_factory=datetime.now)
    
    # Relationships defined after all models
    # progress: "UserStoryProgress" = Relationship(back_populates="choice_history")
    # from_node: "StoryNode" = Relationship()
    # to_node: "StoryNode" = Relationship()


class UserNodeChoicePublic(UserNodeChoiceBase):
    """Public API response model for UserNodeChoice"""
    id: uuid.UUID
    progress_id: uuid.UUID
    choice_time: datetime


class UserNodeChoicesPublic(SQLModel):
    """Collection response for UserNodeChoices"""
    data: list[UserNodeChoicePublic]
    count: int


# ==================== Composite Response Models ====================

class CurrentNodePublic(SQLModel):
    """
    Response model for getting current node with available choices.
    Used by players to understand their current position in a story.
    """
    node: StoryNodePublic
    available_choices: list[NodeChoicePublic]
    story_state: dict[str, Any] | None


# ==================== Relationship Definitions ====================
# Following TinyFoot best practices: define relationships after all models exist

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


"""
Refactored Story System Models - Versioned Templates with Player Instances

Organization:
1. Shared/utility models (Message)
2. Story Template models (authoring concern)
3. Story Navigation models (playing concern)
4. Relationship definitions (post-model declaration)

Following TinyFoot best practices:
- Base → Create → Update → Database (table=True) → Public → Collection
- UUID primary keys
- String-based forward references for type hints
- Post-definition relationship binding for circular refs
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from pydantic import EmailStr
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship


# ==================== Utility Models ====================

class Message(SQLModel):
    message: str


# ==================== Story Template Models (AUTHORING) ====================

class StoryBase(SQLModel):
    """Base model for Story template properties"""
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class StoryCreate(StoryBase):
    """Input model for creating a new Story template"""
    pass


class StoryUpdate(SQLModel):
    """Input model for updating Story template (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    description: str | None = Field(default=None, max_length=1000)  # type: ignore


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
    node_type: str = Field(default="text", max_length=50)  # text, image, choice, etc.
    is_start_node: bool = Field(default=False)
    is_end_node: bool = Field(default=False)


class StoryNodeCreate(StoryNodeBase):
    """Input model for creating a StoryNode"""
    story_id: uuid.UUID
    story_version: int  # Must specify which version this node belongs to


class StoryNodeUpdate(SQLModel):
    """Input model for updating StoryNode (all fields optional)"""
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    content: str | None = Field(default=None)  # type: ignore
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
    started_at: datetime
    updated_at: datetime


class UserStoryProgressesPublic(SQLModel):
    """Collection response for UserStoryProgresses"""
    data: list[UserStoryProgressPublic]
    count: int


# ==================== UserNodeChoice Models (PLAYING) ====================

class UserNodeChoiceBase(SQLModel):
    """
    Base model for recording a player's choice at a node.
    Historical breadcrumb trail through the story.
    """
    choice_text: str = Field(max_length=500)
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID
    
    # Snapshot of state changes applied by this choice
    state_changes: dict[str, Any] | None = Field(default=None,)


class UserNodeChoiceCreate(UserNodeChoiceBase):
    """Input model for recording a choice"""
    progress_id: uuid.UUID


class UserNodeChoice(UserNodeChoiceBase, table=True):
    """
    Database model for player's choice history.
    Immutable record of decisions made.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    progress_id: uuid.UUID = Field(foreign_key="userstoryprogress.id", nullable=False, ondelete="CASCADE")
    choice_time: datetime = Field(default_factory=datetime.now)
    
    # Relationships defined after all models
    # progress: "UserStoryProgress" = Relationship(back_populates="choice_history")
    # from_node: "StoryNode" = Relationship()
    # to_node: "StoryNode" = Relationship()


class UserNodeChoicePublic(UserNodeChoiceBase):
    """Public API response model for UserNodeChoice"""
    id: uuid.UUID
    progress_id: uuid.UUID
    choice_time: datetime


class UserNodeChoicesPublic(SQLModel):
    """Collection response for UserNodeChoices"""
    data: list[UserNodeChoicePublic]
    count: int


# ==================== Relationship Definitions ====================
# Following TinyFoot best practices: define relationships after all models exist

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