import uuid
from typing import Any

from sqlmodel import Session, select, or_, and_
from sqlalchemy import true

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
    QualityCreate,
    Event,
    EventCreate,
    QualityTraitLink,
    QualityTraitLinkCreate,
    QualityEventTrigger,
    QualityEventTriggerCreate,
    PersonaQualityLink,
    ArchetypeTraitLink,
    ArchetypeQualityLink,
    ArchetypePersonaLink,
    QualityState,
    QualitySourceType,
    PersonaTraitLink,
    Story,
    StoryCreate,
    StoryUpdate,
    StoryPublic,
    StoriesPublic,
    StoryNode,
    StoryNodeCreate,
    StoryNodeUpdate,
    StoryNodePublic,
    StoryNodesPublic,
    Message,
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


def create_quality(
    *, session: Session, quality_in: QualityCreate, owner_id: uuid.UUID
) -> Quality:
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


# New CRUD functions for Event
def create_event(*, session: Session, event_in: EventCreate) -> Event:
    db_event = Event.model_validate(event_in)
    session.add(db_event)
    session.commit()
    session.refresh(db_event)
    return db_event


# New CRUD functions for QualityTraitLink
def create_quality_trait_link(
    *, session: Session, link_in: QualityTraitLinkCreate
) -> QualityTraitLink:
    db_link = QualityTraitLink.model_validate(link_in)
    session.add(db_link)
    session.commit()
    session.refresh(db_link)
    return db_link


# New CRUD functions for QualityEventTrigger
def create_quality_event_trigger(
    *, session: Session, trigger_in: QualityEventTriggerCreate
) -> QualityEventTrigger:
    db_trigger = QualityEventTrigger.model_validate(trigger_in)
    session.add(db_trigger)
    session.commit()
    session.refresh(db_trigger)
    return db_trigger


# Enhanced Persona creation with Archetype inheritance
def create_persona_with_archetype(
    *, session: Session, persona_in: PersonaCreate, archetype_id: uuid.UUID
) -> Persona:
    # Create the persona first
    db_persona = Persona.model_validate(persona_in)
    session.add(db_persona)
    session.flush()  # Flush to get the ID without committing

    # Create the archetype-persona link
    archetype_link = ArchetypePersonaLink(
        archetype_id=archetype_id, persona_id=db_persona.id
    )
    session.add(archetype_link)

    # Get all traits from the archetype
    trait_stmt = (
        select(Trait)
        .join(ArchetypeTraitLink)
        .where(ArchetypeTraitLink.archetype_id == archetype_id)
    )
    archetype_traits = session.exec(trait_stmt).all()

    # Add all traits to the persona with inheritance tracking
    for trait in archetype_traits:
        trait_link = PersonaTraitLink(
            persona_id=db_persona.id,
            trait_id=trait.id,
            is_inherited=True,
            source_archetype_id=archetype_id,
        )
        session.add(trait_link)

    # Get all qualities that are trait-dependent
    trait_ids = [trait.id for trait in archetype_traits]
    # Build OR conditions for each trait_id
    trait_id_conditions = [
        QualityTraitLink.trait_id == trait_id for trait_id in trait_ids
    ]
    quality_trait_stmt = (
        select(Quality)
        .join(QualityTraitLink)
        .where(or_(*trait_id_conditions) if trait_id_conditions else true())
    )
    trait_qualities = session.exec(quality_trait_stmt).all()

    # Add trait-dependent qualities to the persona
    for quality in trait_qualities:
        # Find trait links for this quality
        # Build OR conditions for each trait_id for this quality
        qt_trait_id_conditions = [
            and_(
                QualityTraitLink.quality_id == quality.id,
                QualityTraitLink.trait_id == trait_id,
            )
            for trait_id in trait_ids
        ]
        qt_link_stmt = select(QualityTraitLink).where(
            or_(*qt_trait_id_conditions) if qt_trait_id_conditions else true()
        )
        qt_links = session.exec(qt_link_stmt).all()

        # Use the first matching trait id if found
        source_trait_id = next((link.trait_id for link in qt_links), None)

        quality_link = PersonaQualityLink(
            persona_id=db_persona.id,
            quality_id=quality.id,
            source_type=QualitySourceType.TRAIT_DEPENDENT,
            state=QualityState.ENABLED,
            source_trait_id=source_trait_id,
            source_archetype_id=archetype_id,
        )
        session.add(quality_link)

    # Get all qualities that are directly associated with the archetype
    quality_archetype_stmt = (
        select(Quality)
        .join(ArchetypeQualityLink)
        .where(ArchetypeQualityLink.archetype_id == archetype_id)
    )
    archetype_qualities = session.exec(quality_archetype_stmt).all()

    # Add archetype-dependent qualities to the persona
    for quality in archetype_qualities:
        quality_link = PersonaQualityLink(
            persona_id=db_persona.id,
            quality_id=quality.id,
            source_type=QualitySourceType.DEFAULT,
            state=QualityState.ENABLED,
            source_archetype_id=archetype_id,
        )
        session.add(quality_link)

    # Commit everything
    session.commit()
    session.refresh(db_persona)
    return db_persona


# Function to handle event processing for a persona
def process_persona_event(
    *, session: Session, persona_id: uuid.UUID, event_id: uuid.UUID
) -> list[PersonaQualityLink]:
    # Find all quality event triggers for this event
    trigger_stmt = select(QualityEventTrigger).where(
        QualityEventTrigger.event_id == event_id
    )
    triggers = session.exec(trigger_stmt).all()

    affected_links = []

    for trigger in triggers:
        # Check if the persona has this quality
        link_stmt = select(PersonaQualityLink).where(
            PersonaQualityLink.persona_id == persona_id,
            PersonaQualityLink.quality_id == trigger.quality_id,
        )
        quality_link = session.exec(link_stmt).first()

        if quality_link:
            # Update the quality state according to the trigger
            quality_link.state = trigger.new_state
            session.add(quality_link)
            affected_links.append(quality_link)

    if affected_links:
        session.commit()
        for link in affected_links:
            session.refresh(link)

    return affected_links


# Function to add a quality to a persona
def add_quality_to_persona(
    *, session: Session, persona_id: uuid.UUID, quality_id: uuid.UUID
) -> PersonaQualityLink:
    # Check if the persona already has this quality
    stmt = select(PersonaQualityLink).where(
        PersonaQualityLink.persona_id == persona_id,
        PersonaQualityLink.quality_id == quality_id,
    )
    existing_link = session.exec(stmt).first()

    if existing_link:
        # If it exists but was removed, reactivate it
        if existing_link.state == QualityState.REMOVED:
            existing_link.state = QualityState.ENABLED
            session.add(existing_link)
            session.commit()
            session.refresh(existing_link)
            return existing_link
        return existing_link

    # Create a new link
    quality_link = PersonaQualityLink(
        persona_id=persona_id,
        quality_id=quality_id,
        source_type=QualitySourceType.MANUALLY_ADDED,
        state=QualityState.ENABLED,
    )
    session.add(quality_link)
    session.commit()
    session.refresh(quality_link)
    return quality_link


# Function to remove a quality from a persona
def remove_quality_from_persona(
    *, session: Session, persona_id: uuid.UUID, quality_id: uuid.UUID
) -> PersonaQualityLink:
    # Find the quality link
    stmt = select(PersonaQualityLink).where(
        PersonaQualityLink.persona_id == persona_id,
        PersonaQualityLink.quality_id == quality_id,
    )
    quality_link = session.exec(stmt).first()

    if not quality_link:
        raise ValueError("Quality not found for this persona")

    # Mark it as removed
    quality_link.state = QualityState.REMOVED
    session.add(quality_link)
    session.commit()
    session.refresh(quality_link)
    return quality_link


def create_story(
    *, session: Session, story_in: StoryCreate, owner_id: uuid.UUID
) -> Story:
    db_story = Story.model_validate(story_in, update={"owner_id": owner_id})
    session.add(db_story)
    session.commit()
    session.refresh(db_story)
    return db_story


def create_storynode(
    *, session: Session, storynode_in: StoryNodeCreate, owner_id: uuid.UUID
) -> StoryNode:
    db_storynode = StoryNode.model_validate(storynode_in, update={"owner_id": owner_id})
    session.add(db_storynode)
    session.commit()
    session.refresh(db_storynode)
    return db_storynode


def update_story(*, session: Session, story_in: StoryUpdate) -> Story:
    story = session.get(Story, story_in.id)
    if not story:
        raise ValueError("Story not found")
    story.sqlmodel_update(story_in.model_dump(exclude_unset=True))
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


def delete_story(*, session: Session, story_id: uuid.UUID) -> Message:
    story = session.get(Story, story_id)
    if not story:
        raise ValueError("Story not found")
    session.delete(story)
    session.commit()
    return Message(message="Story deleted successfully")
