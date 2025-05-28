import uuid
from typing import Any

from sqlmodel import Session, select, func, or_, and_, true

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
    # StoryPublic,
    # StoriesPublic,
    StoryNode,
    StoryNodeCreate,
    # StoryNodeUpdate,
    # StoryNodePublic,
    # StoryNodesPublic,
    # PersonaUpdate,
    Message,
    UserPersona,
    UserPersonaCreate,
    UserPersonaUpdate,
    UserStoryProgress,
    UserStoryProgressCreate,
    UserStoryProgressUpdate,
    StoryRequirement,
    StoryRequirementCreate,
    NodeChoice,
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


def update_story(
    *, session: Session, story_id: uuid.UUID, story_in: StoryUpdate
) -> Story:
    story = session.get(Story, story_id)
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


# User Persona CRUD functions


def create_user_persona(
    *, session: Session, user_persona_in: UserPersonaCreate, user_id: uuid.UUID
) -> UserPersona:
    """Create a new user persona."""
    db_user_persona = UserPersona.model_validate(
        user_persona_in, update={"user_id": user_id}
    )
    session.add(db_user_persona)
    session.commit()
    session.refresh(db_user_persona)
    return db_user_persona


def get_user_personas(
    *, session: Session, user_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[UserPersona], int]:
    """Get all user personas for a user."""
    count_statement = (
        select(func.count())
        .select_from(UserPersona)
        .where(UserPersona.user_id == user_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(UserPersona)
        .where(UserPersona.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    user_personas = session.exec(statement).all()
    return list(user_personas), count


def get_user_persona(
    *, session: Session, id: uuid.UUID, user_id: uuid.UUID
) -> UserPersona | None:
    """Get a user persona by ID."""
    statement = select(UserPersona).where(
        UserPersona.id == id, UserPersona.user_id == user_id
    )
    return session.exec(statement).first()


def update_user_persona(
    *,
    session: Session,
    db_user_persona: UserPersona,
    user_persona_in: UserPersonaUpdate
) -> UserPersona:
    """Update a user persona."""
    update_data = user_persona_in.model_dump(exclude_unset=True)
    db_user_persona.sqlmodel_update(update_data)
    session.add(db_user_persona)
    session.commit()
    session.refresh(db_user_persona)
    return db_user_persona


def delete_user_persona(*, session: Session, db_user_persona: UserPersona) -> None:
    """Delete a user persona."""
    session.delete(db_user_persona)
    session.commit()


# User Story Progress CRUD functions


def create_user_story_progress(
    *, session: Session, progress_in: UserStoryProgressCreate
) -> UserStoryProgress:
    """Create a new user story progress."""
    db_progress = UserStoryProgress.model_validate(progress_in)
    session.add(db_progress)
    session.commit()
    session.refresh(db_progress)
    return db_progress


def get_user_story_progresses(
    *, session: Session, user_persona_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[UserStoryProgress], int]:
    """Get all story progresses for a user persona."""
    count_statement = (
        select(func.count())
        .select_from(UserStoryProgress)
        .where(UserStoryProgress.user_persona_id == user_persona_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(UserStoryProgress)
        .where(UserStoryProgress.user_persona_id == user_persona_id)
        .offset(skip)
        .limit(limit)
    )
    progresses = session.exec(statement).all()
    return list(progresses), count


def get_user_story_progress(
    *, session: Session, user_persona_id: uuid.UUID, story_id: uuid.UUID
) -> UserStoryProgress | None:
    """Get a user's progress in a specific story."""
    statement = select(UserStoryProgress).where(
        UserStoryProgress.user_persona_id == user_persona_id,
        UserStoryProgress.story_id == story_id,
    )
    return session.exec(statement).first()


def update_user_story_progress(
    *,
    session: Session,
    db_progress: UserStoryProgress,
    progress_in: UserStoryProgressUpdate
) -> UserStoryProgress:
    """Update a user's story progress."""
    update_data = progress_in.model_dump(exclude_unset=True)
    db_progress.sqlmodel_update(update_data)
    session.add(db_progress)
    session.commit()
    session.refresh(db_progress)
    return db_progress


# Story Requirement CRUD functions


def create_story_requirement(
    *, session: Session, requirement_in: StoryRequirementCreate
) -> StoryRequirement:
    """Create a new story requirement."""
    db_requirement = StoryRequirement.model_validate(requirement_in)
    session.add(db_requirement)
    session.commit()
    session.refresh(db_requirement)
    return db_requirement


def get_story_requirements(
    *, session: Session, story_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> tuple[list[StoryRequirement], int]:
    """Get all requirements for a story."""
    count_statement = (
        select(func.count())
        .select_from(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
        .offset(skip)
        .limit(limit)
    )
    requirements = session.exec(statement).all()
    return list(requirements), count


def check_story_requirements(
    *, session: Session, user_persona_id: uuid.UUID, story_id: uuid.UUID
) -> bool:
    """Check if a user persona meets all requirements for a story."""
    # Get the story requirements
    statement = select(StoryRequirement).where(StoryRequirement.story_id == story_id)
    requirements = session.exec(statement).all()

    # If there are no requirements, anyone can access the story
    if not requirements:
        return True

    # Get the user persona
    user_persona_stmt = select(UserPersona).where(UserPersona.id == user_persona_id)
    user_persona = session.exec(user_persona_stmt).first()
    if not user_persona:
        return False

    # Check each requirement
    for req in requirements:
        if req.requirement_type == "quality":
            # Check if the user persona has this quality enabled
            quality_stmt = select(PersonaQualityLink).where(
                PersonaQualityLink.persona_id == user_persona.persona_id,
                PersonaQualityLink.quality_id == req.target_id,
                PersonaQualityLink.state == QualityState.ENABLED,
            )
            quality_link = session.exec(quality_stmt).first()
            if not quality_link:
                return False
        elif req.requirement_type == "trait":
            # Check if the persona has this trait
            trait_stmt = select(PersonaTraitLink).where(
                PersonaTraitLink.persona_id == user_persona.persona_id,
                PersonaTraitLink.trait_id == req.target_id,
            )
            trait_link = session.exec(trait_stmt).first()
            if not trait_link:
                return False

    # All requirements are met
    return True


def get_available_choices(
    *, session: Session, node_id: uuid.UUID, story_state: dict | None = None
) -> list[NodeChoice]:
    """
    Get available choices for a node, considering the story state.
    """
    # Get all choices for this node
    statement = select(NodeChoice).where(NodeChoice.from_node_id == node_id)
    choices = session.exec(statement).all()

    # If there's no story state, return all choices
    if not story_state:
        return list(choices)

    # Filter choices based on requirements
    available_choices = []
    for choice in choices:
        # If the choice has no requirements, it's always available
        if not choice.requires_state:
            available_choices.append(choice)
            continue

        # Check if all required states are met
        requirements_met = True
        for key, value in choice.requires_state.items():
            if key not in story_state or story_state[key] != value:
                requirements_met = False
                break

        if requirements_met:
            available_choices.append(choice)

    return list(available_choices)
