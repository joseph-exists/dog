import uuid

from typing import List
from pydantic import EmailStr
from sqlalchemy.sql.sqltypes import UUID
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime


# investigate datetime
# investigate other sqlmodel imports


class Message(SQLModel):
    message: str

# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)

# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"

# User class and item class are from original template - if any changes are made
# make all reasons explicit and maintain documentation on original
# best to maintain these classes as is to help decrease any learning curve


class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str | None = Field(default=None, max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int

# Item classes from template all original
#
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

# maintain item class as an example of this ownership model
# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int

# ============ Base Models ++++++++

class ArchetypeBase(SQLModel):
    title: str = Field(min_length=1, max_length=255) # type: ignore
    description: str | None = Field(default=None, max_length=255)

class PersonaBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

class TraitBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
   #  archetype_only: bool = Field(default=False)
    # max_active_personas: int | None = Field(default=None, ge=0)
class QualityBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)

# =========== base models for creating linked relationships between classes

class ArchetypeTraitLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    trait_id: uuid.UUID = Field(foreign_key="trait.id")

class PersonaTraitLinkBase(SQLModel):
    persona_id: uuid.UUID = Field(foreign_key="persona.id")
    trait_id: uuid.UUID = Field(foreign_key="trait.id")

class ArchetypeQualityLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    quality_id: uuid.UUID = Field(foreign_key="quality.id")

class PersonaQualityLinkBase(SQLModel):
    persona_id: uuid.UUID = Field(foreign_key="persona.id")
    quality_id: uuid.UUID = Field(foreign_key="quality.id")

class ArchetypePersonaLinkBase(SQLModel):
    archetype_id: uuid.UUID = Field(foreign_key="archetype.id")
    persona_id: uuid.UUID = Field(foreign_key="persona.id")

class QualityTraitLinkbase(SQLModel):
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

# ======== Update Models ===========

class ArchetypeUpdate(ArchetypeBase):
    title: str | None = Field(default=None, min_length=1, max_length=255) # type: ignore

class PersonaUpdate(PersonaBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

class QualityUpdate(QualityBase):
    title: str | None = Field(default=None, min_length=1, max_length=255) # type: ignore

class TraitUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

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

class PersonaQualityLink(PersonaQualityLinkBase, table=True):
    """
    database model for many-to-many relationship between Personas and Qualities.
    relationships defined post model declaration.
    """
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)

class Archetype(ArchetypeBase, table=True):
    """
    Database model for Archetype.
    Relationships will be defined after all models are declared.
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



# ========== Public Models ========

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

class ArchetypesPublic(SQLModel):
    """Collection model for Archetype API responses."""
    data: List[ArchetypePublic]
    count: int

class PersonasPublic(SQLModel):
    """Collection model for Personas API responses."""
    data: List[PersonaPublic]
    count: int

class TraitsPublic(SQLModel):
    """Collection model for Trait API responses."""
    data: List[TraitPublic]
    count: int

class QualitiesPublic(SQLModel):
    """Collection model for Quality API responses."""
    data: List[QualityPublic]
    count: int

# need to understand union models - ephemeral, dynamic, and static?

# ==================== Define Relationships ====================

# Define relationships after all classes to avoid circular reference issues

# Define the relationship from Archetype to Trait
Archetype.traits = Relationship(
    back_populates="archetypes",
    link_model=ArchetypeTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

# Define the relationship from Trait to Archetype
Trait.archetypes = Relationship(
    back_populates="traits",
    link_model=ArchetypeTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

# Define the relationship from Persona to Archetype
Archetype.personas = Relationship(
    back_populates="archetypes",
    link_model=ArchetypePersonaLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Persona.archetypes = Relationship(
    back_populates="personas",
    link_model=ArchetypePersonaLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

# Define the relationship from Quality to Archetype
Archetype.qualities = Relationship(
    back_populates="archetypes",
    link_model=ArchetypeQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Quality.archetypes = Relationship(
    back_populates="qualities",
    link_model=ArchetypeQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Quality.personas = Relationship(
    back_populates="qualities",
    link_model=PersonaQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Persona.qualities = Relationship(
    back_populates="personas",
    link_model=PersonaQualityLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Persona.traits = Relationship(
    back_populates="personas",
    link_model=PersonaTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)

Trait.personas = Relationship(
    back_populates="traits",
    link_model=PersonaTraitLink,
    sa_relationship_kwargs={"lazy": "selectin"}
)


# Define relationships for the link model
ArchetypeTraitLink.archetype = Relationship(back_populates="trait_links")
ArchetypeTraitLink.trait = Relationship(back_populates="archetype_links")

ArchetypePersonaLink.archetype = Relationship(back_populates="persona_links")
ArchetypePersonaLink.persona = Relationship(back_populates="archetype_links")

ArchetypeQualityLink.archetype = Relationship(back_populates="quality_links")
ArchetypeQualityLink.quality = Relationship(back_populates="archetype_links")

PersonaTraitLink.persona = Relationship(back_populates="trait_links")
PersonaTraitLink.trait = Relationship(back_populates="persona_links")

# Add backref relationships to main models for the link tables
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



# Schemas for public trait configuration display and manipulation
# THIS IS NEXT BIG TODO

class TraitConfigBase(SQLModel):
    is_modifiable: bool = Field(default=True)
    modifiable_at_creation_only: bool = Field(default=False)
    is_required: bool = Field(default=False)


class TraitConfigCreate(TraitConfigBase):
    trait_id: uuid.UUID


class TraitConfigUpdate(TraitConfigBase):
    is_modifiable: bool | None = Field(default=None)
    modifiable_at_creation_only: bool | None = Field(default=None)
    is_required: bool | None = Field(default=None)


class TraitConfigPublic(TraitConfigBase):
    trait_id: uuid.UUID
    trait: TraitPublic | None = None


class TraitConfigsPublic(SQLModel):
    data: list[TraitConfigPublic]
    count: int
