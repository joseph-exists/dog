import uuid

from typing import List
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime



# Shared properties
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

class ArchetypeBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)
    # do core traits go here or somewhere else?


class ArchetypeCreate(ArchetypeBase):
    pass


class ArchetypeUpdate(ArchetypeBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore

    # TODO: this needs to add or remove core traits that a specific Archetype


class Archetype(ArchetypeBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    archetype_name: str = Field(index=True)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
    personas: List["Persona"] = Relationship(
        back_populates="archetype", sa_relationship_kwargs={"lazy": "selectin"}
    )
    # core_traits: List["Trait"] = Relationship(
    #   back_populates="archetypal_source", sa_relationship_kwargs={"lazy": "selectin"}
    # )


class ArchetypePublic(ArchetypeBase):
    id: uuid.UUID


class ArchetypesPublic(SQLModel):
    data: list[ArchetypePublic]
    count: int


class PersonaBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)



class PersonaCreate(PersonaBase):
    pass


class PersonaUpdate(PersonaBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


class Persona(PersonaBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    enabled: bool = True
    title: str = Field(max_length=255)
    persona_name: str | None = Field(index=True)
    # foreign key to archetype
    archetype_id: uuid.UUID | None = Field(foreign_key="archetype.id", index=True)
    archetype: Archetype = Relationship(back_populates="personas")
    # TODO: add custom per-persona traits
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    # owner: User | None = Relationship(back_populates="personas")


class PersonaPublic(PersonaBase):
    id: uuid.UUID


class PersonasPublic(SQLModel):
    data: list[PersonaPublic]
    count: int

# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


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


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)
