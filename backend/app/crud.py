import uuid
from typing import Any

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    User,
    UserCreate,
    UserUpdate,
    Archetype,
    ArchetypeCreate,
    Persona,
    PersonaCreate,
    Trait,
    TraitCreate,
    Quality,
    QualityCreate
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    session_user = session.exec(statement).first()
    return session_user


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


def create_archetype(
    *, session: Session, archetype_in: ArchetypeCreate, owner_id: uuid.UUID
) -> Archetype:
    db_archetype = Archetype.model_validate(archetype_in, update={"owner_id": owner_id})
    session.add(db_archetype)
    session.commit()
    session.refresh(db_archetype)
    return db_archetype


def create_persona(
    *, session: Session, persona_in: PersonaCreate, owner_id: uuid.UUID
) -> Persona:
    db_persona = Persona.model_validate(persona_in, update={"owner_id": owner_id})
    session.add(db_persona)
    session.commit()
    session.refresh(db_persona)
    return db_persona

def create_quality(*, session: Session, item_in: QualityCreate, owner_id: uuid.UUID) -> Quality:
    db_quality = Quality.model_validate(quality_in, update={"owner_id": owner_id})
    session.add(db_quality)
    session.commit()
    session.refresh(db_quality)
    return db_quality


def create_trait(
    *, session: Session, trait_in: TraitCreate, owner_id: uuid.UUID
) -> Trait:
    db_trait = Trait.model_validate(trait_in, update={"owner_id": owner_id})
    session.add(db_trait)
    session.commit()
    session.refresh(db_trait)
    return db_trait
