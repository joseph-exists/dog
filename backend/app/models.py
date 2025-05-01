import uuid
from datetime import datetime
from enum import Enum

from pydantic import EmailStr
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


# ============ Base Models ++++++++


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)


class EventBase(SQLModel):
    """Base model for events that can trigger state changes"""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=100)
    event_type: str = Field(min_length=1, max_length=100)
    # NOTE: event_type categories and structure?


class ItemBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class StoryBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)
    is_published: bool = Field(default=False)


class ArchetypeBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class PersonaBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class TraitBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    # archetype_only: bool = Field(default=False)
    # max_active_personas: int | None = Field(default=None, ge=0)


class QualityBase(SQLModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


class StoryNodeBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(default="")
    node_type: str = Field(
        default="text", max_length=50
    )  # text, image, choice, paradox, graph, calendly, etc.
    is_start_node: bool = Field(default=False)
    is_end_node: bool = Field(default=False)
    # metadata: dict | None = Field(default=None)  # JSON field for storing type-specific data


class TagBase(SQLModel):
    name: str = Field(min_length=1, max_length=50, unique=True)
    color: str | None = Field(default=None, max_length=20)


class NodeChoiceBase(SQLModel):
    """Base model for NodeChoice"""

    text: str = Field(min_length=1, max_length=500)
    order: int = Field(default=0)
    # TODO : figure out if these can be passed in to NodeChoice model directly in NodeChoiceCreate Model
    # requires_state: dict | None = Field (default=None)  # JSON field for required state variables
    # sets_state: dict | None = Field(default=None)  # JSON field for state variables to set


# =========== base models for creating linked relationships between classes


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


class StoryUserLinkBase(SQLModel):
    story_id: uuid.UUID = Field(foreign_key="story.id")
    user_id: uuid.UUID = Field(foreign_key="user.id")


# ========== Create Models ===========


class PersonaCreate(PersonaBase):
    pass


class ArchetypeCreate(ArchetypeBase):
    pass


class TraitCreate(TraitBase):
    pass


class QualityCreate(QualityBase):
    pass


class StoryCreate(StoryBase):
    pass


class StoryNodeCreate(StoryNodeBase):
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


class StoryBasePartial(SQLModel):
    """Base model for story fields that can be updated (all optional)"""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    is_published: bool | None = Field(default=None)


class StoryUpdate(StoryBasePartial):
    pass


class StoryNodePartial(SQLModel):
    """Base model for story fields that can be updated (all optional)"""

    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore
    content: str | None = Field(default=None)
    node_type: str | None = Field(default=None, max_length=50)
    is_start_node: bool | None = Field(default=None)
    is_end_node: bool | None = Field(default=None)
    # metadata: dict | None = Field(default=None)


class StoryNodeUpdate(StoryNodePartial):
    pass


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


class Story(StoryBase, table=True):
    """
    DB model for Story
    Relationships defined after models are declared.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )


# Database model for StoryNode
class StoryNode(StoryNodeBase, table=True):
    """
    DB model for StoryNode
    Relationships defined after model declaration
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    story_id: uuid.UUID = Field(
        foreign_key="story.id", nullable=False, ondelete="CASCADE"
    )


class NodeChoice(NodeChoiceBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


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


class NodeChoicePublic(NodeChoiceBase):
    id: uuid.UUID
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID


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


class StoryPublic(StoryBase):
    """Public model for Story API responses."""

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    owner_id: uuid.UUID


class StoryNodePublic(StoryNodeBase):
    """Public Model for Story Node API responses"""

    id: uuid.UUID
    story_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TagPublic(TagBase):
    id: uuid.UUID


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


class TagsPublic(SQLModel):
    data: list[TagPublic]
    count: int


class ArchetypesPublic(SQLModel):
    """Collection model for Archetype API responses."""

    data: list[ArchetypePublic]
    count: int


class NodeChoicesPublic(SQLModel):
    data: list[NodeChoicePublic]
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


class StoriesPublic(SQLModel):
    """Collection model for Stories API responses."""

    data: list[StoryPublic]
    count: int


class StoryNodesPublic(SQLModel):
    """Collection model for Story Node responses."""

    data: list[StoryNodePublic]
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


# ==================== Define Relationships ====================


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


# Schemas for public trait configuration display and manipulation
# THIS IS NEXT BIG TODO


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


# ---- NodeChoice Models ----

# Base model for NodeChoice


class NodeChoiceCreate(NodeChoiceBase):
    from_node_id: uuid.UUID
    to_node_id: uuid.UUID


class TagBasePartial(SQLModel):
    name: str = Field(min_length=1, max_length=50, unique=True)
    color: str | None = Field(default=None, max_length=20)


# Create model for NodeChoice


# Update model for NodeChoice
class NodeChoiceUpdate(NodeChoiceBasePartial):
    text: str | None = Field(default=None, min_length=1, max_length=500)  # type: ignore
    order: int | None = Field(default=None)
    to_node_id: uuid.UUID | None = Field(default=None)
    requires_state: dict | None = Field(default=None)
    sets_state: dict | None = Field(default=None)


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


# =============== user management stuff ===============


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)
