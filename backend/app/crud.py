from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlmodel import Session, and_, desc, func, or_, select, true
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    AgentPersona,
    AgentPersonaCreate,
    AgentPersonaUpdate,
    Archetype,
    ArchetypeCreate,
    ArchetypePersonaLink,
    ArchetypeQualityLink,
    ArchetypeTraitLink,
    Event,
    EventCreate,
    Item,
    ItemCreate,
    LLMModel,
    LLMModelCreate,
    LLMProvider,
    LLMProviderType,
    Message,
    NodeChoice,
    NodeChoicePublic,
    Persona,
    PersonaCreate,
    PersonaQualityLink,
    PersonaTraitLink,
    ProgressSnapshot,
    Quality,
    QualityCreate,
    QualityEventTrigger,
    QualityEventTriggerCreate,
    QualitySourceType,
    QualityState,
    QualityTraitLink,
    QualityTraitLinkCreate,
    Room,
    RoomAgentSettings,
    RoomAgentSettingsBundle,
    RoomAgentSettingsPublic,
    RoomAgentSettingsUpdate,
    RoomContextItemCreate,
    RoomContextItemPublic,
    RoomContextItemsPublic,
    RoomMessage,
    RoomMessagePublic,
    RoomMessagesPublic,
    RoomParticipant,
    RoomParticipantBinding,
    RoomParticipantBindingsPublic,
    RoomPublic,
    RoomRuntimeAdvanceRequest,
    RoomRuntimePublic,
    RoomRuntimeResetRequest,
    RoomRuntimeRewindRequest,
    RoomRuntimeStartRequest,
    RoomsPublic,
    RoomStoryProgress,
    StateSchemaValidationError,
    StateSchemaValidationResult,
    StateValueType,
    Story,
    StoryCreate,
    StoryNode,
    StoryNodeCreate,
    StoryNodePublic,
    StoryRequirement,
    StoryRequirementCreate,
    StoryStateVariable,
    StoryStateVariableCreate,
    StoryStateVariableUpdate,
    StoryUpdate,
    Trait,
    TraitConflictGroup,
    TraitConflictGroupCreate,
    TraitConflictGroupMember,
    TraitConflictGroupMemberCreate,
    TraitConflictGroupUpdate,
    TraitCreate,
    User,
    UserCreate,
    UserLLMProvider,
    UserNodeChoice,
    UserPersona,
    UserPersonaCreate,
    UserPersonaUpdate,
    UserStoryProgress,
    UserStoryProgressCreate,
    UserStoryProgressUpdate,
    UserUpdate,
)
from app.services.context_store import ContextItem, ContextItemStore, RedisContextStore
from app.services.event_emitter import emit_event


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


# Agent Persona CRUD functions


def create_agent_persona(
    *,
    session: Session,
    agent_persona_in: AgentPersonaCreate,
    agent_id: uuid.UUID,
) -> AgentPersona:
    """Create a new agent persona library entry."""
    db_agent_persona = AgentPersona.model_validate(
        agent_persona_in,
        update={"agent_id": agent_id},
    )
    session.add(db_agent_persona)
    session.commit()
    session.refresh(db_agent_persona)
    return db_agent_persona


def get_agent_personas(
    *,
    session: Session,
    agent_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[AgentPersona], int]:
    """Get all agent personas for an agent."""
    count_statement = (
        select(func.count())
        .select_from(AgentPersona)
        .where(AgentPersona.agent_id == agent_id)
    )
    count = session.exec(count_statement).one()

    statement = (
        select(AgentPersona)
        .where(AgentPersona.agent_id == agent_id)
        .offset(skip)
        .limit(limit)
    )
    agent_personas = session.exec(statement).all()
    return list(agent_personas), count


def get_agent_persona(
    *,
    session: Session,
    id: uuid.UUID,
    agent_id: uuid.UUID,
) -> AgentPersona | None:
    """Get an agent persona by ID (scoped to agent_id)."""
    statement = select(AgentPersona).where(
        AgentPersona.id == id,
        AgentPersona.agent_id == agent_id,
    )
    return session.exec(statement).first()


def update_agent_persona(
    *,
    session: Session,
    db_agent_persona: AgentPersona,
    agent_persona_in: AgentPersonaUpdate,
) -> AgentPersona:
    """Update an agent persona."""
    update_data = agent_persona_in.model_dump(exclude_unset=True)
    db_agent_persona.sqlmodel_update(update_data)
    session.add(db_agent_persona)
    session.commit()
    session.refresh(db_agent_persona)
    return db_agent_persona


def delete_agent_persona(*, session: Session, db_agent_persona: AgentPersona) -> None:
    """Delete an agent persona."""
    session.delete(db_agent_persona)
    session.commit()


# User Story Progress CRUD functions


def create_user_story_progress(
    *, session: Session, progress_in: UserStoryProgressCreate
) -> UserStoryProgress:
    """
    Create a new user story progress.
    Locks the progress to the story's version specified in progress_in.
    The calling code should ensure this matches the story's current_version.
    Args:
        session: Database session
        progress_in: UserStoryProgressCreate input model
    Returns:
        Created UserStoryProgress
    """
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


async def get_available_choices(
    *, session: AsyncSession, node_id: uuid.UUID, story_state: dict | None = None
) -> list[NodeChoice]:
    """
    Get available choices for a node, filtering by story state requirements.

    Choices are filtered based on their requires_state field:
    - If a choice has no requires_state, it's always available
    - If a choice has requires_state, all key-value pairs must match story_state

    Args:
        session: Database session
        node_id: StoryNode ID
        story_state: Current story state dictionary (from UserStoryProgress)

    Returns:
        List of available NodeChoice objects
    """
    # Get all choices for this node
    statement = select(NodeChoice).where(NodeChoice.from_node_id == node_id)
    result = await session.exec(statement)
    choices = result.all()

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

    return list[NodeChoice](available_choices)


def get_available_choices_sync(
    *, session: Session, node_id: uuid.UUID, story_state: dict | None = None
) -> list[NodeChoice]:
    """
    Sync wrapper for get_available_choices (used by sync routes).
    """
    statement = select(NodeChoice).where(NodeChoice.from_node_id == node_id)
    result = session.exec(statement)
    choices = result.all()

    if not story_state:
        return list(choices)

    available_choices = []
    for choice in choices:
        if not choice.requires_state:
            available_choices.append(choice)
            continue

        requirements_met = True
        for key, value in choice.requires_state.items():
            if key not in story_state or story_state[key] != value:
                requirements_met = False
                break

        if requirements_met:
            available_choices.append(choice)

    return list[NodeChoice](available_choices)


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

def check_trait_conflicts(
    session: Session,
    persona_id: uuid.UUID,
    new_trait_id: uuid.UUID
) -> list[dict]:
    """
    Check if adding a trait would create a logical conflict.

    Returns list of conflicts found, empty if no conflicts.
    """
    # Get all conflict groups that include the new trait
    conflict_groups = session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == new_trait_id)
    ).all()

    # Get persona's current traits
    current_trait_ids = {
        link.trait_id for link in
        session.exec(
            select(PersonaTraitLink)
            .where(PersonaTraitLink.persona_id == persona_id)
        ).all()
    }

    conflicts = []
    for group in conflict_groups:
        # Get all trait IDs in this conflict group
        group_trait_ids = {
            member.trait_id for member in
            session.exec(
                select(TraitConflictGroupMember)
                .where(TraitConflictGroupMember.group_id == group.id)
            ).all()
        }

        # Check for overlap with current traits (excluding the new trait)
        conflicting_traits = current_trait_ids & group_trait_ids

        if conflicting_traits:
            conflicts.append({
                "group_id": group.id,
                "group_name": group.name,
                "conflict_type": group.conflict_type,
                "reason": group.reason,
                "conflicting_trait_ids": list(conflicting_traits)
            })

    return conflicts

def create_trait_conflict_group(
    *,
    session: Session,
    group_in: TraitConflictGroupCreate
) -> TraitConflictGroup:
    """
    Create a new trait conflict group, optionally with initial members.
    """
    # Validate conflict_type
    valid_types = {"contradictory", "contrary", "subcontrary"}
    if group_in.conflict_type not in valid_types:
        raise ValueError(f"conflict_type must be one of: {valid_types}")

    # Create the group (exclude trait_ids from model creation)
    group_data = group_in.model_dump(exclude={"trait_ids"})
    group = TraitConflictGroup.model_validate(group_data)
    session.add(group)
    session.commit()
    session.refresh(group)

    # Add initial members if provided
    if group_in.trait_ids:
        for trait_id in group_in.trait_ids:
            add_trait_to_conflict_group(
                session=session,
                group_id=group.id,
                member_in=TraitConflictGroupMemberCreate(trait_id=trait_id)
            )

    return group


def get_trait_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID
) -> TraitConflictGroup | None:
    """Get a trait conflict group by ID."""
    return session.get(TraitConflictGroup, group_id)


def get_trait_conflict_groups(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    conflict_type: str | None = None
) -> tuple[list[TraitConflictGroup], int]:
    """
    Get all trait conflict groups with optional filtering.
    Returns (groups, total_count).
    """
    query = select(TraitConflictGroup)

    if conflict_type:
        query = query.where(TraitConflictGroup.conflict_type == conflict_type)

    # Get count
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Get paginated results
    groups = session.exec(query.offset(skip).limit(limit)).all()

    return list(groups), count


def update_trait_conflict_group(
    *,
    session: Session,
    db_group: TraitConflictGroup,
    group_in: TraitConflictGroupUpdate
) -> TraitConflictGroup:
    """Update an existing trait conflict group."""
    update_data = group_in.model_dump(exclude_unset=True)

    # Validate conflict_type if being updated
    if "conflict_type" in update_data:
        valid_types = {"contradictory", "contrary", "subcontrary"}
        if update_data["conflict_type"] not in valid_types:
            raise ValueError(f"conflict_type must be one of: {valid_types}")

    db_group.sqlmodel_update(update_data)
    db_group.updated_at = datetime.utcnow()
    session.add(db_group)
    session.commit()
    session.refresh(db_group)
    return db_group


def delete_trait_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID
) -> bool:
    """
    Delete a trait conflict group and all its members.
    Returns True if deleted, False if not found.
    """
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        return False

    session.delete(group)
    session.commit()
    return True


# =============================================================================
# TRAIT CONFLICT GROUP MEMBER CRUD
# =============================================================================

def add_trait_to_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID,
    member_in: TraitConflictGroupMemberCreate
) -> TraitConflictGroupMember:
    """
    Add a trait to a conflict group.
    Validates that the trait exists and isn't already in the group.
    """
    # Verify group exists
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        raise ValueError(f"Conflict group {group_id} not found")

    # Verify trait exists
    trait = session.get(Trait, member_in.trait_id)
    if not trait:
        raise ValueError(f"Trait {member_in.trait_id} not found")

    # Check if already a member
    existing = session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
        .where(TraitConflictGroupMember.trait_id == member_in.trait_id)
    ).first()

    if existing:
        raise ValueError(f"Trait {member_in.trait_id} is already in this conflict group")

    # Create the membership
    member = TraitConflictGroupMember(
        group_id=group_id,
        trait_id=member_in.trait_id
    )
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def remove_trait_from_conflict_group(
    *,
    session: Session,
    group_id: uuid.UUID,
    trait_id: uuid.UUID
) -> bool:
    """
    Remove a trait from a conflict group.
    Returns True if removed, False if not found.
    """
    member = session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
        .where(TraitConflictGroupMember.trait_id == trait_id)
    ).first()

    if not member:
        return False

    session.delete(member)
    session.commit()
    return True


def get_conflict_group_members(
    *,
    session: Session,
    group_id: uuid.UUID
) -> list[TraitConflictGroupMember]:
    """Get all trait members of a conflict group."""
    return list(session.exec(
        select(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.group_id == group_id)
    ).all())


def get_trait_conflict_memberships(
    *,
    session: Session,
    trait_id: uuid.UUID
) -> list[TraitConflictGroup]:
    """Get all conflict groups that contain a specific trait."""
    return list(session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == trait_id)
    ).all())


# =============================================================================
# CONFLICT VALIDATION
# =============================================================================


def check_archetype_trait_conflicts(
    *,
    session: Session,
    archetype_id: uuid.UUID,
    new_trait_id: uuid.UUID
) -> list[dict]:
    """
    Check if adding a trait to an archetype would create a logical conflict.
    Similar to persona check but uses ArchetypeTraitLink.
    """
    conflict_groups = session.exec(
        select(TraitConflictGroup)
        .join(TraitConflictGroupMember)
        .where(TraitConflictGroupMember.trait_id == new_trait_id)
    ).all()

    if not conflict_groups:
        return []

    current_trait_ids = {
        link.trait_id for link in
        session.exec(
            select(ArchetypeTraitLink)
            .where(ArchetypeTraitLink.archetype_id == archetype_id)
        ).all()
    }

    conflicts = []
    for group in conflict_groups:
        group_trait_ids = {
            member.trait_id for member in
            session.exec(
                select(TraitConflictGroupMember)
                .where(TraitConflictGroupMember.group_id == group.id)
            ).all()
        }

        conflicting_traits = current_trait_ids & group_trait_ids

        if conflicting_traits:
            conflicts.append({
                "group_id": str(group.id),
                "group_name": group.name,
                "conflict_type": group.conflict_type,
                "reason": group.reason,
                "conflicting_trait_ids": [str(tid) for tid in conflicting_traits]
            })

    return conflicts


def validate_conflict_group_cardinality(
    *,
    session: Session,
    group_id: uuid.UUID
) -> dict:
    """
    Validate that a conflict group has appropriate member count for its type.
    Returns validation result with any warnings/errors.
    """
    group = session.get(TraitConflictGroup, group_id)
    if not group:
        return {"valid": False, "error": "Group not found"}

    members = get_conflict_group_members(session=session, group_id=group_id)
    member_count = len(members)

    result = {
        "valid": True,
        "group_id": str(group_id),
        "conflict_type": group.conflict_type,
        "member_count": member_count,
        "warnings": [],
        "errors": []
    }

    if group.conflict_type == "contradictory":
        if member_count < 2:
            result["errors"].append("Contradictory requires exactly 2 traits")
            result["valid"] = False
        elif member_count > 2:
            result["warnings"].append(
                f"Contradictory typically has exactly 2 traits, found {member_count}"
            )
    else:  # contrary or subcontrary
        if member_count < 2:
            result["errors"].append(f"{group.conflict_type} requires at least 2 traits")
            result["valid"] = False

    return result

# ============================================================================
# StoryStateVariable CRUD Operations
# ============================================================================


def get_story_state_variables(
    *,
    session: Session,
    story_id: uuid.UUID,
    story_version: int,
    skip: int = 0,
    limit: int = 100,
) -> tuple[list[StoryStateVariable], int]:
    """
    Get all state variables for a story version.

    Args:
        session: Database session
        story_id: UUID of the story
        story_version: Version number of the story
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        Tuple of (list of StoryStateVariable, total count)
    """
    count_statement = (
        select(func.count())
        .select_from(StoryStateVariable)
        .where(
            StoryStateVariable.story_id == story_id,
            StoryStateVariable.story_version == story_version,
        )
    )
    count = session.exec(count_statement).one()

    statement = (
        select(StoryStateVariable)
        .where(
            StoryStateVariable.story_id == story_id,
            StoryStateVariable.story_version == story_version,
        )
        .offset(skip)
        .limit(limit)
    )
    variables = session.exec(statement).all()
    return list(variables), count


def create_story_state_variable(
    *, session: Session, variable_in: StoryStateVariableCreate
) -> StoryStateVariable:
    """
    Create a new story state variable.

    Validates that enum_values is provided when value_type is ENUM.

    Args:
        session: Database session
        variable_in: StoryStateVariableCreate with variable data

    Returns:
        Created StoryStateVariable

    Raises:
        ValueError: If value_type is ENUM but enum_values is empty
    """
    # Validate enum_values if value_type is enum
    if variable_in.value_type == StateValueType.ENUM:
        if not variable_in.enum_values or len(variable_in.enum_values) == 0:
            raise ValueError("enum_values required when value_type is 'enum'")

    db_variable = StoryStateVariable.model_validate(variable_in)
    session.add(db_variable)
    session.commit()
    session.refresh(db_variable)
    return db_variable


def update_story_state_variable(
    *, session: Session, variable_id: uuid.UUID, variable_in: StoryStateVariableUpdate
) -> StoryStateVariable:
    """
    Update a story state variable.

    Args:
        session: Database session
        variable_id: UUID of the variable to update
        variable_in: StoryStateVariableUpdate with fields to update

    Returns:
        Updated StoryStateVariable

    Raises:
        ValueError: If variable not found
    """
    variable = session.get(StoryStateVariable, variable_id)
    if not variable:
        raise ValueError("Variable not found")

    update_data = variable_in.model_dump(exclude_unset=True)
    variable.sqlmodel_update(update_data)
    variable.updated_at = datetime.now()
    session.add(variable)
    session.commit()
    session.refresh(variable)
    return variable


def delete_story_state_variable(*, session: Session, variable_id: uuid.UUID) -> None:
    """
    Delete a story state variable.

    Args:
        session: Database session
        variable_id: UUID of the variable to delete

    Raises:
        ValueError: If variable not found
    """
    variable = session.get(StoryStateVariable, variable_id)
    if not variable:
        raise ValueError("Variable not found")
    session.delete(variable)
    session.commit()


def get_undefined_variables_in_choices(
    *, session: Session, story_id: uuid.UUID, story_version: int
) -> StateSchemaValidationResult:
    """
    Check all choices for undefined variables (for publish validation).

    This function validates that all state variables used in requires_state
    and sets_state fields of choices are defined in the story's state schema.

    Args:
        session: Database session
        story_id: UUID of the story
        story_version: Version number to validate

    Returns:
        StateSchemaValidationResult with validation errors and variable lists
    """
    # Get all defined variable keys from schema
    variables, _ = get_story_state_variables(
        session=session,
        story_id=story_id,
        story_version=story_version,
        limit=1000,
    )
    defined_keys = {v.key for v in variables}

    # Get all nodes for this story version
    nodes_stmt = select(StoryNode).where(
        StoryNode.story_id == story_id,
        StoryNode.story_version == story_version,
    )
    nodes = session.exec(nodes_stmt).all()
    node_map = {n.id: n for n in nodes}
    node_ids = list(node_map.keys())

    # Get all choices for these nodes
    if not node_ids:
        return StateSchemaValidationResult(
            is_valid=True,
            errors=[],
            defined_variables=list(defined_keys),
            used_variables=[],
            undefined_variables=[],
        )

    choices_stmt = select(NodeChoice).where(NodeChoice.from_node_id.in_(node_ids))
    choices = session.exec(choices_stmt).all()

    # Collect all used variables and errors
    errors: list[StateSchemaValidationError] = []
    used_keys: set[str] = set()
    undefined_keys: set[str] = set()

    # Operators that should be skipped (not variable names)
    OPERATORS = {"$and", "$or", "$not", "$eq", "$ne", "$gt", "$gte", "$lt", "$lte",
                 "$in", "$nin", "$exists", "$set", "$inc", "$dec", "$toggle", "$unset", "$expr"}

    def extract_variable_keys(obj: dict | list | None) -> set[str]:
        """
        Recursively extract variable keys from a state condition/mutation object.
        Skips operator keys (those starting with $) and descends into nested structures.
        """
        if obj is None:
            return set()

        keys: set[str] = set()

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key.startswith("$"):
                    # This is an operator - descend into its value
                    if isinstance(value, list):
                        # $and, $or contain arrays of conditions
                        for item in value:
                            keys.update(extract_variable_keys(item))
                    elif isinstance(value, dict):
                        # $not contains a nested condition
                        keys.update(extract_variable_keys(value))
                    # Otherwise it's an operator value like $eq: 10, skip
                else:
                    # This is a variable key
                    keys.add(key)
                    # The value might also contain operators with nested keys
                    if isinstance(value, dict):
                        # Check if value is operator syntax like { $gte: 10 }
                        # In this case, no nested variable keys
                        # But { $not: { other_var: true } } would have nested keys
                        keys.update(extract_variable_keys(value))
        elif isinstance(obj, list):
            for item in obj:
                keys.update(extract_variable_keys(item))

        return keys

    for choice in choices:
        from_node = node_map.get(choice.from_node_id)

        # Check requires_state
        if choice.requires_state:
            keys_in_requires = extract_variable_keys(choice.requires_state)
            for key in keys_in_requires:
                used_keys.add(key)
                if key not in defined_keys:
                    undefined_keys.add(key)
                    errors.append(
                        StateSchemaValidationError(
                            variable_key=key,
                            used_in="requires_state",
                            choice_id=choice.id,
                            choice_text=choice.text,
                            from_node_id=choice.from_node_id,
                            from_node_title=from_node.title if from_node else "Unknown",
                        )
                    )

        # Check sets_state
        if choice.sets_state:
            keys_in_sets = extract_variable_keys(choice.sets_state)
            for key in keys_in_sets:
                used_keys.add(key)
                if key not in defined_keys:
                    undefined_keys.add(key)
                    errors.append(
                        StateSchemaValidationError(
                            variable_key=key,
                            used_in="sets_state",
                            choice_id=choice.id,
                            choice_text=choice.text,
                            from_node_id=choice.from_node_id,
                            from_node_title=from_node.title if from_node else "Unknown",
                        )
                    )

    return StateSchemaValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        defined_variables=list(defined_keys),
        used_variables=list(used_keys),
        undefined_variables=list(undefined_keys),
    )


"""
Room CRUD Operations

This module contains room-related CRUD operations

All operations:
- Use async for I/O operations
- Enforce room-based authorization via RoomParticipant membership
- Use event_emitter.emit_event() for all writes (no direct projection updates)
- Support both user and agent participants as first-class entities

Authorization Pattern:
- All room reads require active membership
- Owner-only operations verify role == 'owner'
- Uses existing patterns, no bespoke utilities
"""



# ============================================================================
# Authorization Helpers
# ============================================================================


async def check_room_membership(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user_id is an active user participant in room_id.

    This is the foundational authorization check for all room operations.
    Only active participants can read or write to a room.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is an active participant, False otherwise
    """
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.one_or_none()
    return participant is not None


async def check_room_owner(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user_id is an active participant with role == 'owner'.

    Owner-only operations (adding participants, changing roles, etc.)
    must verify ownership before proceeding.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is an active owner, False otherwise
    """
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.role == "owner",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.one_or_none()
    return participant is not None


# ============================================================================
# Room Runtime (Shared Room Run)
# ============================================================================


async def _build_room_runtime_public(
    *,
    room_id: UUID,
    room_story_progress: RoomStoryProgress,
    progress: UserStoryProgress,
    session: AsyncSession,
) -> RoomRuntimePublic:
    current_node = None
    node_chain: list[StoryNodePublic] = []
    available_choices: list[NodeChoicePublic] = []

    if progress.current_node_id is not None:
        available_choices_result = await get_available_choices(
            session=session,
            node_id=progress.current_node_id,
            story_state=progress.story_state or {},
        )
        available_choices = [NodeChoicePublic.model_validate(c) for c in available_choices_result]

    node_chain_ids: list[uuid.UUID] = []
    if progress.head_choice_id:
        chain = get_choice_ancestor_chain(
            session=session.sync_session, choice_id=progress.head_choice_id
        )
        if chain:
            node_chain_ids.append(chain[0].from_node_id)
            node_chain_ids.extend([choice.to_node_id for choice in chain])
    else:
        start_node_result = await session.exec(
            select(StoryNode).where(
                StoryNode.story_id == progress.story_id,
                StoryNode.story_version == progress.story_version,
                StoryNode.is_start_node == True,  # noqa: E712
            )
        )
        start_node = start_node_result.one_or_none()
        if start_node:
            node_chain_ids.append(start_node.id)

    if node_chain_ids:
        nodes_result = await session.exec(
            select(StoryNode).where(StoryNode.id.in_([str(nid) for nid in node_chain_ids]))
        )
        nodes = nodes_result.all()
        nodes_by_id = {node.id: node for node in nodes}
        node_chain = [
            StoryNodePublic.model_validate(nodes_by_id[node_id])
            for node_id in node_chain_ids
            if node_id in nodes_by_id
        ]

    if progress.current_node_id is not None:
        available_choices_result = await get_available_choices(
            session=session,
            node_id=progress.current_node_id,
            story_state=progress.story_state or {},
        )
        available_choices = [NodeChoicePublic.model_validate(c) for c in available_choices_result]

    return RoomRuntimePublic(
        room_id=room_id,
        story_id=room_story_progress.story_id,
        story_version=room_story_progress.story_version,
        active_progress_id=room_story_progress.active_progress_id,
        revision=room_story_progress.revision,
        current_node_id=progress.current_node_id,
        head_choice_id=progress.head_choice_id,
        head_version=progress.head_version,
        story_state=progress.story_state,
        updated_at=room_story_progress.updated_at,
        current_node=current_node,
        node_chain=node_chain,
        available_choices=available_choices,
    )


async def get_room_runtime(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> RoomRuntimePublic:
    """
    Read-only runtime projection for a room's shared story run.

    Authorization: active room membership required.
    """
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")

    rsp_result = await session.exec(
        select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
    )
    room_story_progress = rsp_result.one_or_none()
    if not room_story_progress:
        raise HTTPException(status_code=404, detail="Room runtime not initialized")

    progress_result = await session.exec(
        select(UserStoryProgress).where(
            UserStoryProgress.id == room_story_progress.active_progress_id
        )
    )
    progress = progress_result.one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Active progress not found")

    return await _build_room_runtime_public(
        room_id=room_id,
        room_story_progress=room_story_progress,
        progress=progress,
        session=session,
    )


async def start_room_runtime(
    *,
    room_id: UUID,
    user_id: UUID,
    req: RoomRuntimeStartRequest,
    session: AsyncSession,
) -> RoomRuntimePublic:
    """
    Initialize (or re-initialize) a room's shared story run ("party progress").

    Creates a new underlying UserStoryProgress record and points the room's
    RoomStoryProgress.active_progress_id at it. Existing progress is preserved
    for audit/debugging (branching semantics).

    Authorization:
    - active membership required
    - owner-only (default policy) to start/restart the shared run
    """
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can start the room runtime")

    room_result = await session.exec(select(Room).where(Room.room_id == room_id))
    room = room_result.one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    if not room.story_id:
        raise HTTPException(status_code=400, detail="Room has no story selected")

    # Validate user persona ownership (we reuse the persona-bound progress model).
    user_persona_result = await session.exec(
        select(UserPersona).where(
            UserPersona.id == req.user_persona_id,
            UserPersona.user_id == user_id,
        )
    )
    user_persona = user_persona_result.one_or_none()
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    story = await session.get(Story, room.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    target_version = req.story_version
    if target_version is None:
        target_version = story.published_version or story.current_version

    # Find start node for the selected version.
    start_node_result = await session.exec(
        select(StoryNode).where(
            StoryNode.story_id == story.id,
            StoryNode.story_version == target_version,
            StoryNode.is_start_node == True,  # noqa: E712
        )
    )
    start_node = start_node_result.one_or_none()
    if not start_node:
        raise HTTPException(
            status_code=400,
            detail=f"No start node found for story version {target_version}",
        )

    # Initialize state from schema defaults for this version.
    state_vars_result = await session.exec(
        select(StoryStateVariable).where(
            StoryStateVariable.story_id == story.id,
            StoryStateVariable.story_version == target_version,
        )
    )
    state_vars = state_vars_result.all()
    initial_state: dict[str, Any] = {}
    for var in state_vars:
        initial_state[var.key] = var.default_value

    now = datetime.utcnow()
    new_progress = UserStoryProgress(
        id=uuid.uuid4(),
        user_persona_id=req.user_persona_id,
        story_id=story.id,
        story_version=target_version,
        current_node_id=start_node.id,
        story_state=initial_state,
        head_choice_id=None,
        head_version=0,
        started_at=now,
        updated_at=now,
    )
    session.add(new_progress)
    await session.flush()

    rsp_result = await session.exec(
        select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
    )
    room_story_progress = rsp_result.one_or_none()

    if room_story_progress is None:
        room_story_progress = RoomStoryProgress(
            id=uuid.uuid4(),
            room_id=room_id,
            story_id=story.id,
            story_version=target_version,
            active_progress_id=new_progress.id,
            revision=0,
            created_at=now,
            updated_at=now,
        )
        session.add(room_story_progress)
    else:
        if req.expected_revision is not None and req.expected_revision != room_story_progress.revision:
            raise HTTPException(status_code=409, detail="Room runtime revision mismatch")
        room_story_progress.story_id = story.id
        room_story_progress.story_version = target_version
        room_story_progress.active_progress_id = new_progress.id
        room_story_progress.revision += 1
        room_story_progress.updated_at = now
        session.add(room_story_progress)

    await session.flush()

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.runtime.started",
        payload={
            "story_id": str(story.id),
            "story_version": target_version,
            "active_progress_id": str(new_progress.id),
            "revision": room_story_progress.revision,
        },
    )

    return await _build_room_runtime_public(
        room_id=room_id,
        room_story_progress=room_story_progress,
        progress=new_progress,
        session=session,
    )


async def advance_room_runtime(
    *,
    room_id: UUID,
    user_id: UUID,
    req: RoomRuntimeAdvanceRequest,
    session: AsyncSession,
) -> RoomRuntimePublic:
    """
    Advance the room's shared story run by applying a choice.

    Authorization: active membership + owner-only (default policy).
    """
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can advance the room runtime")

    rsp_result = await session.exec(
        select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
    )
    room_story_progress = rsp_result.one_or_none()
    if not room_story_progress:
        raise HTTPException(status_code=404, detail="Room runtime not initialized")

    if req.expected_revision is not None and req.expected_revision != room_story_progress.revision:
        raise HTTPException(status_code=409, detail="Room runtime revision mismatch")

    progress_result = await session.exec(
        select(UserStoryProgress).where(
            UserStoryProgress.id == room_story_progress.active_progress_id
        )
    )
    progress = progress_result.one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Active progress not found")

    choice_result = await session.exec(
        select(NodeChoice).where(NodeChoice.id == req.choice_id)
    )
    choice = choice_result.one_or_none()
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")

    if progress.current_node_id != choice.from_node_id:
        raise HTTPException(
            status_code=400, detail="Choice is not available for the current node"
        )

    available_choices = await get_available_choices(
        session=session,
        node_id=progress.current_node_id,
        story_state=progress.story_state or {},
    )
    if not any(c.id == choice.id for c in available_choices):
        raise HTTPException(
            status_code=403,
            detail="Choice requirements not met for current story state",
        )

    user_choice = UserNodeChoice(
        id=uuid.uuid4(),
        progress_id=progress.id,
        parent_choice_id=progress.head_choice_id,
        choice_text=choice.text,
        from_node_id=choice.from_node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state,
        rng_data=None,
    )
    session.add(user_choice)
    await session.flush()

    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.story_state = replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id,
    )
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version,
    )

    snapshot = create_snapshot_if_needed(
        session=session.sync_session,
        progress=progress,
        snapshot_interval=10,
    )
    if snapshot:
        session.add(snapshot)

    now = datetime.utcnow()
    progress.updated_at = now

    room_story_progress.revision += 1
    room_story_progress.updated_at = now
    session.add(progress)
    session.add(room_story_progress)

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.runtime.advanced",
        payload={
            "choice_id": str(user_choice.id),
            "active_progress_id": str(progress.id),
            "revision": room_story_progress.revision,
        },
    )

    return await _build_room_runtime_public(
        room_id=room_id,
        room_story_progress=room_story_progress,
        progress=progress,
        session=session,
    )


async def rewind_room_runtime(
    *,
    room_id: UUID,
    user_id: UUID,
    req: RoomRuntimeRewindRequest,
    session: AsyncSession,
) -> RoomRuntimePublic:
    """
    Rewind the room's shared story run by branching to a prior choice.

    Creates a new progress branch with a cloned ancestor chain.
    """
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can rewind the room runtime")

    rsp_result = await session.exec(
        select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
    )
    room_story_progress = rsp_result.one_or_none()
    if not room_story_progress:
        raise HTTPException(status_code=404, detail="Room runtime not initialized")

    if req.expected_revision is not None and req.expected_revision != room_story_progress.revision:
        raise HTTPException(status_code=409, detail="Room runtime revision mismatch")

    progress_result = await session.exec(
        select(UserStoryProgress).where(
            UserStoryProgress.id == room_story_progress.active_progress_id
        )
    )
    progress = progress_result.one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Active progress not found")

    target_result = await session.exec(
        select(UserNodeChoice).where(
            UserNodeChoice.id == req.target_choice_id,
            UserNodeChoice.progress_id == progress.id,
        )
    )
    target_choice = target_result.one_or_none()
    if not target_choice:
        raise HTTPException(status_code=404, detail="Target choice not found in active progress")

    chain = get_choice_ancestor_chain(
        session=session.sync_session,
        choice_id=req.target_choice_id,
    )

    now = datetime.utcnow()
    new_progress = UserStoryProgress(
        id=uuid.uuid4(),
        user_persona_id=progress.user_persona_id,
        story_id=progress.story_id,
        story_version=progress.story_version,
        current_node_id=progress.current_node_id,
        is_completed=False,
        story_state={},
        head_choice_id=None,
        head_version=0,
        started_at=now,
        updated_at=now,
    )
    session.add(new_progress)
    await session.flush()

    new_head_id: uuid.UUID | None = None
    previous_id: uuid.UUID | None = None
    for choice in chain:
        new_choice_id = uuid.uuid4()
        new_choice = UserNodeChoice(
            id=new_choice_id,
            progress_id=new_progress.id,
            parent_choice_id=previous_id,
            choice_text=choice.choice_text,
            from_node_id=choice.from_node_id,
            to_node_id=choice.to_node_id,
            state_changes=choice.state_changes,
            rng_data=choice.rng_data,
            choice_time=choice.choice_time,
        )
        session.add(new_choice)
        previous_id = new_choice_id
        new_head_id = new_choice_id

    await session.flush()

    new_progress.head_choice_id = new_head_id
    new_progress.head_version = len(chain)
    new_progress.story_state = replay_state_from_head_optimized(
        session=session.sync_session,
        progress_id=new_progress.id,
        head_choice_id=new_head_id,
    )
    new_progress.current_node_id = get_current_node_from_head(
        session=session.sync_session,
        head_choice_id=new_head_id,
        story_id=new_progress.story_id,
        story_version=new_progress.story_version,
    )

    node_result = await session.exec(
        select(StoryNode).where(StoryNode.id == new_progress.current_node_id)
    )
    node = node_result.one_or_none()
    new_progress.is_completed = bool(node and node.is_end_node)

    new_progress.updated_at = now

    room_story_progress.active_progress_id = new_progress.id
    room_story_progress.revision += 1
    room_story_progress.updated_at = now
    session.add(new_progress)
    session.add(room_story_progress)

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.runtime.rewound",
        payload={
            "target_choice_id": str(req.target_choice_id),
            "active_progress_id": str(new_progress.id),
            "revision": room_story_progress.revision,
        },
    )

    return await _build_room_runtime_public(
        room_id=room_id,
        room_story_progress=room_story_progress,
        progress=new_progress,
        session=session,
    )


async def reset_room_runtime(
    *,
    room_id: UUID,
    user_id: UUID,
    req: RoomRuntimeResetRequest,
    session: AsyncSession,
) -> RoomRuntimePublic:
    """
    Reset the room's shared story run by branching to a new start state.
    """
    rsp_result = await session.exec(
        select(RoomStoryProgress).where(RoomStoryProgress.room_id == room_id)
    )
    room_story_progress = rsp_result.one_or_none()
    if not room_story_progress:
        raise HTTPException(status_code=404, detail="Room runtime not initialized")

    progress_result = await session.exec(
        select(UserStoryProgress).where(
            UserStoryProgress.id == room_story_progress.active_progress_id
        )
    )
    progress = progress_result.one_or_none()
    if not progress:
        raise HTTPException(status_code=404, detail="Active progress not found")

    result = await start_room_runtime(
        room_id=room_id,
        user_id=user_id,
        req=RoomRuntimeStartRequest(
            user_persona_id=progress.user_persona_id,
            story_version=room_story_progress.story_version,
            expected_revision=req.expected_revision,
        ),
        session=session,
    )

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.runtime.reset",
        payload={
            "active_progress_id": str(result.active_progress_id),
            "revision": result.revision,
        },
    )

    return result


# ============================================================================
# Room Context Item API (Supplemental Context)
# ============================================================================


def _context_store(store: ContextItemStore | None) -> ContextItemStore:
    return store or RedisContextStore()


def _validate_context_item(
    *,
    context_type: str,
    payload: dict[str, Any],
    source: str,
) -> None:
    allowed_prefixes = (
        "upload.",
        "note.",
        "system.",
        "shadow.",
    )
    if not context_type or len(context_type) > 100:
        raise HTTPException(status_code=400, detail="Invalid context_type")
    if not any(context_type.startswith(prefix) for prefix in allowed_prefixes):
        raise HTTPException(status_code=400, detail="context_type not allowed")
    if not source or len(source) > 50:
        raise HTTPException(status_code=400, detail="Invalid source")
    try:
        payload_bytes = len(json.dumps(payload).encode("utf-8"))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Invalid payload: {exc}") from exc
    if payload_bytes > 50_000:
        raise HTTPException(status_code=400, detail="Payload too large")


async def list_room_context_items(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
    agent_slug: str | None = None,
    store: ContextItemStore | None = None,
) -> RoomContextItemsPublic:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")

    items = await _context_store(store).list(room_id=room_id, agent_slug=agent_slug)
    return RoomContextItemsPublic(
        data=[
            RoomContextItemPublic(
                id=item.id,
                room_id=item.room_id,
                agent_slug=item.agent_slug,
                context_type=item.context_type,
                payload=item.payload,
                source=item.source,
                created_at=item.created_at,
                expires_at=item.expires_at,
            )
            for item in items
        ],
        count=len(items),
    )


async def add_room_context_item(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
    context_in: RoomContextItemCreate,
    store: ContextItemStore | None = None,
) -> RoomContextItemPublic:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can add context items")

    _validate_context_item(
        context_type=context_in.context_type,
        payload=context_in.payload,
        source=context_in.source,
    )

    item = ContextItem(
        id=str(uuid.uuid4()),
        room_id=room_id,
        agent_slug=context_in.agent_slug,
        context_type=context_in.context_type,
        payload=context_in.payload,
        source=context_in.source,
        created_at=datetime.utcnow(),
        expires_at=context_in.expires_at,
    )
    await _context_store(store).add(item)

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.context_item.created",
        payload={
            "context_id": item.id,
            "context_type": item.context_type,
            "source": item.source,
            "agent_slug": item.agent_slug,
        },
    )
    return RoomContextItemPublic(
        id=item.id,
        room_id=item.room_id,
        agent_slug=item.agent_slug,
        context_type=item.context_type,
        payload=item.payload,
        source=item.source,
        created_at=item.created_at,
        expires_at=item.expires_at,
    )


async def upsert_room_context_item(
    *,
    room_id: UUID,
    user_id: UUID,
    context_id: str,
    session: AsyncSession,
    context_in: RoomContextItemCreate,
    replace_by_type: bool = False,
    store: ContextItemStore | None = None,
) -> RoomContextItemPublic:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can upsert context items")

    _validate_context_item(
        context_type=context_in.context_type,
        payload=context_in.payload,
        source=context_in.source,
    )

    store_obj = _context_store(store)
    if replace_by_type:
        existing = await store_obj.list(room_id=room_id, agent_slug=context_in.agent_slug)
        for item in existing:
            if item.context_type == context_in.context_type:
                await store_obj.delete(room_id=room_id, context_id=item.id)

    await store_obj.delete(room_id=room_id, context_id=context_id)

    item = ContextItem(
        id=context_id,
        room_id=room_id,
        agent_slug=context_in.agent_slug,
        context_type=context_in.context_type,
        payload=context_in.payload,
        source=context_in.source,
        created_at=datetime.utcnow(),
        expires_at=context_in.expires_at,
    )
    await store_obj.add(item)

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.context_item.upserted",
        payload={
            "context_id": item.id,
            "context_type": item.context_type,
            "source": item.source,
            "agent_slug": item.agent_slug,
            "replace_by_type": replace_by_type,
        },
    )

    return RoomContextItemPublic(
        id=item.id,
        room_id=item.room_id,
        agent_slug=item.agent_slug,
        context_type=item.context_type,
        payload=item.payload,
        source=item.source,
        created_at=item.created_at,
        expires_at=item.expires_at,
    )


async def delete_room_context_item(
    *,
    room_id: UUID,
    user_id: UUID,
    context_id: str,
    session: AsyncSession,
    store: ContextItemStore | None = None,
) -> None:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can delete context items")

    removed = await _context_store(store).delete(room_id=room_id, context_id=context_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Context item not found")

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.context_item.deleted",
        payload={"context_id": context_id},
    )


# ============================================================================
# Room Agent Settings (Prompt/Tool Policy)
# ============================================================================


async def list_room_agent_settings(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> RoomAgentSettingsBundle:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")

    settings_result = await session.exec(
        select(RoomAgentSettings).where(RoomAgentSettings.room_id == room_id)
    )
    settings = settings_result.all()

    room_defaults = next((s for s in settings if s.agent_slug is None), None)
    overrides = [s for s in settings if s.agent_slug is not None]

    return RoomAgentSettingsBundle(
        room_defaults=RoomAgentSettingsPublic.model_validate(room_defaults)
        if room_defaults
        else None,
        agent_overrides=[RoomAgentSettingsPublic.model_validate(s) for s in overrides],
    )


async def upsert_room_agent_settings(
    *,
    room_id: UUID,
    user_id: UUID,
    agent_slug: str | None,
    settings_in: RoomAgentSettingsUpdate,
    session: AsyncSession,
) -> RoomAgentSettingsPublic:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can update agent settings")

    result = await session.exec(
        select(RoomAgentSettings).where(
            RoomAgentSettings.room_id == room_id,
            RoomAgentSettings.agent_slug == agent_slug,
        )
    )
    settings = result.one_or_none()

    now = datetime.utcnow()
    if settings is None:
        settings = RoomAgentSettings(
            id=uuid.uuid4(),
            room_id=room_id,
            agent_slug=agent_slug,
            prompt_config=settings_in.prompt_config,
            tool_policy=settings_in.tool_policy,
            rule_config=settings_in.rule_config,
            revision=0,
            created_at=now,
            updated_at=now,
        )
        session.add(settings)
    else:
        if settings_in.expected_revision is not None and settings_in.expected_revision != settings.revision:
            raise HTTPException(status_code=409, detail="Room agent settings revision mismatch")
        if settings_in.prompt_config is not None:
            settings.prompt_config = settings_in.prompt_config
        if settings_in.tool_policy is not None:
            settings.tool_policy = settings_in.tool_policy
        if settings_in.rule_config is not None:
            settings.rule_config = settings_in.rule_config
        settings.revision += 1
        settings.updated_at = now
        session.add(settings)

    await session.flush()

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.agent_settings.updated",
        payload={
            "agent_slug": agent_slug,
            "revision": settings.revision,
        },
    )

    return RoomAgentSettingsPublic.model_validate(settings)


async def delete_room_agent_settings_override(
    *,
    room_id: UUID,
    user_id: UUID,
    agent_slug: str,
    session: AsyncSession,
) -> None:
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a member of this room")
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Only room owners can update agent settings")

    result = await session.exec(
        select(RoomAgentSettings).where(
            RoomAgentSettings.room_id == room_id,
            RoomAgentSettings.agent_slug == agent_slug,
        )
    )
    settings = result.one_or_none()
    if not settings:
        raise HTTPException(status_code=404, detail="Agent settings override not found")

    await session.delete(settings)
    await session.flush()

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.agent_settings.deleted",
        payload={"agent_slug": agent_slug},
    )


async def check_can_edit_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user can edit the message.

    Authorization rules:
    - User messages: Author OR room owner can edit
    - Agent messages: Owner only can edit

    Args:
        room_id: UUID of the room
        message_id: UUID of the message
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is authorized to edit the message, False otherwise
    """
    # Get the message
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()
    if not message:
        return False

    # Check if room owner
    is_owner = await check_room_owner(
        room_id=room_id, user_id=user_id, session=session
    )

    # Agent messages: owner only
    if message.sender_type == "agent":
        return is_owner

    # User messages: author or owner
    return message.sender_id == user_id or is_owner


async def check_can_pin_message(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user can pin messages (owner only).

    Reuses existing check_room_owner helper.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is a room owner, False otherwise
    """
    return await check_room_owner(
        room_id=room_id, user_id=user_id, session=session
    )


async def check_can_delete_message(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> bool:
    """
    Return True if user can delete messages (owner only).

    Reuses existing check_room_owner helper.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        True if user is a room owner, False otherwise
    """
    return await check_room_owner(
        room_id=room_id, user_id=user_id, session=session
    )


# ============================================================================
# Room Creation & Management
# ============================================================================


async def create_room(
    *,
    creator_id: UUID,
    story_id: UUID | None,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Create a new room by emitting room.created and participant.joined events.

    NOTE: This function expects to be called within an active transaction.
    Use AsyncSessionTransactionDep in route handlers to ensure proper
    transaction management.

    This operation creates a room with the creator as the owner participant.
    All state changes are recorded as events and projections are updated
    transactionally.

    Args:
        creator_id: UUID of the user creating the room
        story_id: Optional UUID of associated story
        title: Optional room title
        session: Async database session with active transaction

    Returns:
        The created Room projection

    Example:
        # In route handler:
        async def create_new_room(session: AsyncSessionTransactionDep, ...):
            room = await create_room(
                creator_id=user.id,
                story_id=story.id,
                title="Chapter 1 Discussion",
                session=session,  # Transaction managed by route
            )
            return room
    """
    # Generate room_id upfront (required for event sourcing - the event log
    # is the source of truth, so we need the identifier before emitting events)
    room_id = uuid4()

    # Emit room.created event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.created",
        payload={
            "creator_id": str(creator_id),
            "story_id": str(story_id) if story_id else None,
            "title": title,
        },
    )

    # Emit participant.joined event for creator (as owner)
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.joined",
        payload={
            "participant_id": str(creator_id),
            "participant_type": "user",
            "role": "owner",
        },
    )

    # Fetch and return the created room projection
    result = await session.exec(select(Room).where(Room.room_id == room_id))
    room = result.one()
    return room

async def list_rooms_for_story(
    *,
    user_id: UUID,
    story_id: UUID,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 10,
) -> RoomsPublic:
    """
    Return rooms for a story where the user is either a creator or an active participant, ordered by last_activity_desc.

    This provides the user's room list for a particular story for UI display. Only shows rooms where the user has active membership.

    Notes: uses rooms_story_id_fkey index for O(log n) lookup

    Args:
        user_id: UUID of the user
        session: Async database session
        story_id: story to check for rooms
        skip: Number of rooms to skip (pagination)
        limit: Maximum number of rooms to return

    Returns:
        RoomsPublic with data and count

"""
    # Query rooms for story where user is creator or active participant
    result = await session.exec(
        select(Room)
        .where(
        Room.story_id == str(story_id),  # Filter by story_id (uses FK index)
        )
        .order_by(desc(Room.last_activity))
        .offset(skip)
        .limit(limit)
    )
    rooms = result.all()

    # Get total count (same filter)
    count_result = await session.exec(
        select(func.count(Room.room_id))
        .join(RoomParticipant)
        .where(
            Room.story_id == str(story_id),
            or_(
                Room.creator_id == str(user_id),
                and_(
                    RoomParticipant.participant_type == "user",
                    RoomParticipant.participant_id == str(user_id),
                    RoomParticipant.active == True,  # noqa: E712
                )
            )
        )
    )
    total_count = count_result.one()

    return RoomsPublic(
        data=[RoomPublic.model_validate(room) for room in rooms],
        count=total_count,
    )


async def list_rooms_for_user(
    *,
    user_id: UUID,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> RoomsPublic:
    """
    Return rooms where the user is an active participant, ordered by last_activity desc.

    This provides the user's room list for UI display. Only shows rooms where
    the user has active membership.

    Args:
        user_id: UUID of the user
        session: Async database session
        skip: Number of rooms to skip (pagination)
        limit: Maximum number of rooms to return

    Returns:
        RoomsPublic with data and count
    """
    # Query rooms where user is an active participant
    result = await session.exec(
        select(Room)
        .join(RoomParticipant)
        .where(
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
        .order_by(desc(Room.last_activity))
        .offset(skip)
        .limit(limit)
    )
    rooms = result.all()

    # Get total count
    count_result = await session.exec(
        select(func.count(Room.room_id))
        .join(RoomParticipant)
        .where(
            RoomParticipant.participant_type == "user",
            RoomParticipant.participant_id == str(user_id),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    #total_count = len(count_result.all())
    total_count = count_result.one()

    return RoomsPublic(
        data=[RoomPublic.model_validate(room) for room in rooms],
        count=total_count,
    )


async def get_room_for_user(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> Room:
    """
    Fetch a room projection, only if the user is an active participant.

    This enforces authorization at the CRUD level. Non-participants
    cannot access room data.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user
        session: Async database session

    Returns:
        Room projection

    Raises:
        HTTPException: 403 if user is not an active participant
        HTTPException: 404 if room does not exist
    """
    # Check membership first
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Fetch room
    result = await session.exec(select(Room).where(Room.room_id == room_id))
    room = result.one_or_none()

    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    return room


async def update_room_metadata(
    *,
    room_id: UUID,
    user_id: UUID,
    title: str | None,
    session: AsyncSession,
) -> Room:
    """
    Update room metadata via event emission (room.updated).

    NOTE: This function expects to be called within an active transaction.

    Policy: Owner-only operation (enforced in Phase 1).
    Future phases may allow members to update certain fields.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user (must be owner)
        title: New title for the room
        session: Async database session with active transaction

    Returns:
        Updated Room projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 404 if room does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can update room metadata",
        )

    # Build updated fields payload
    updated_fields = {}
    if title is not None:
        updated_fields["title"] = title

    if not updated_fields:
        # No changes requested, return current room
        return await get_room_for_user(room_id=room_id, user_id=user_id, session=session)

    # Emit room.updated event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room.updated",
        payload={"updated_fields": updated_fields},
    )

    # Fetch and return updated room
    result = await session.exec(select(Room).where(Room.room_id == room_id))
    room = result.one()
    return room


# ============================================================================
# Participant Management
# ============================================================================


async def add_participant(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    participant_type: str,
    role: str,
    session: AsyncSession,
) -> RoomParticipant:
    """
    Add a user or agent to a room (owner-only operation).

    NOTE: This function expects to be called within an active transaction.

    This operation is idempotent: re-adding an inactive participant
    will reactivate them via the participant.joined event handler.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        participant_type: "user" or "agent"
        role: "owner" or "member"
        session: Async database session with active transaction

    Returns:
        RoomParticipant projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 400 if participant_type or role is invalid
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can add participants",
        )

    # Validate participant_type
    if participant_type not in ("user", "agent"):
        raise HTTPException(
            status_code=400,
            detail="participant_type must be 'user' or 'agent'",
        )

    # Validate role
    if role not in ("owner", "member"):
        raise HTTPException(
            status_code=400,
            detail="role must be 'owner' or 'member'",
        )

    # Standardize agent participant_id to AgentConfig.slug (preferred addressing key).
    # PRI-1 TODO: Remove agent UUID participant_id support once Milestone 1.1 tasks
    # 2, 3, and 4 are complete and validated (bindings table + binding event flow + APIs).
    normalized_participant_id = participant_id
    if participant_type == "agent":
        # Accept UUID strings temporarily, but normalize to slug internally.
        try:
            agent_uuid = UUID(participant_id)
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.id == agent_uuid)
            )
            agent_config = agent_config_result.one_or_none()
            if not agent_config:
                raise HTTPException(status_code=400, detail="Agent not found")
            normalized_participant_id = agent_config.slug
        except ValueError:
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.slug == participant_id)
            )
            agent_config = agent_config_result.one_or_none()
            if not agent_config:
                raise HTTPException(status_code=400, detail="Agent not found")
            normalized_participant_id = agent_config.slug

    # Emit participant.joined event (idempotent via handler)
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.joined",
        payload={
            "participant_id": normalized_participant_id,
            "participant_type": participant_type,
            "role": role,
        },
    )

    # Fetch and return participant
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == normalized_participant_id,
        )
    )
    participant = result.one()
    return participant


async def remove_participant(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    session: AsyncSession,
) -> None:
    """
    Remove a participant from a room (owner-only, soft delete).

    NOTE: This function expects to be called within an active transaction.

    Emits participant.left event which sets active=False in the projection.
    Historical events are preserved (never deleted).

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        session: Async database session with active transaction

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 404 if participant does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can remove participants",
        )

    # Verify participant exists (normalize agent UUID/slug mismatch if needed).
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.one_or_none()

    normalized_participant_id = participant_id
    if not participant:
        # If caller provided an agent UUID string but the room stores slug (or vice versa),
        # attempt to resolve and retry.
        try:
            agent_uuid = UUID(participant_id)
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.id == agent_uuid)
            )
            agent_config = agent_config_result.one_or_none()
            if agent_config:
                normalized_participant_id = agent_config.slug
        except ValueError:
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.slug == participant_id)
            )
            agent_config = agent_config_result.one_or_none()
            if agent_config:
                normalized_participant_id = agent_config.slug

        if normalized_participant_id != participant_id:
            result = await session.exec(
                select(RoomParticipant).where(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.participant_id == normalized_participant_id,
                )
            )
            participant = result.one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Emit participant.left event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.left",
        payload={
            "participant_id": normalized_participant_id,
            # Optional field for forward compatibility; handler should not require it.
            "participant_type": participant.participant_type,
        },
    )


async def change_participant_role(
    *,
    room_id: UUID,
    user_id: UUID,
    participant_id: str,
    new_role: str,
    session: AsyncSession,
) -> RoomParticipant:
    """
    Change a participant's role (owner-only operation).

    NOTE: This function expects to be called within an active transaction.

    Emits participant.role_changed event to update the projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user performing the operation (must be owner)
        participant_id: UUID string for users, agent name for agents
        new_role: "owner" or "member"
        session: Async database session with active transaction

    Returns:
        Updated RoomParticipant projection

    Raises:
        HTTPException: 403 if user is not the owner
        HTTPException: 400 if new_role is invalid
        HTTPException: 404 if participant does not exist
    """
    # Verify owner permission
    if not await check_room_owner(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(
            status_code=403,
            detail="Only room owners can change participant roles",
        )

    # Validate new_role
    if new_role not in ("owner", "member"):
        raise HTTPException(
            status_code=400,
            detail="new_role must be 'owner' or 'member'",
        )

    # Verify participant exists (normalize agent UUID/slug mismatch if needed).
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == participant_id,
        )
    )
    participant = result.one_or_none()

    normalized_participant_id = participant_id
    if not participant:
        # Try resolve slug/UUID mismatch for agents.
        try:
            agent_uuid = UUID(participant_id)
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.id == agent_uuid)
            )
            agent_config = agent_config_result.one_or_none()
            if agent_config:
                normalized_participant_id = agent_config.slug
        except ValueError:
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.slug == participant_id)
            )
            agent_config = agent_config_result.one_or_none()
            if agent_config:
                normalized_participant_id = agent_config.slug

        if normalized_participant_id != participant_id:
            result = await session.exec(
                select(RoomParticipant).where(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.participant_id == normalized_participant_id,
                )
            )
            participant = result.one_or_none()

    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")

    # Emit participant.role_changed event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.role_changed",
        payload={
            "participant_id": normalized_participant_id,
            "new_role": new_role,
            # Optional field for forward compatibility; handler should not require it.
            "participant_type": participant.participant_type,
        },
    )

    # Fetch and return updated participant
    result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_id == normalized_participant_id,
        )
    )
    participant = result.one()
    return participant


# ============================================================================
# Room Participant Bindings (Shadow Milestone 1.1 tasks 2/3/4)
# ============================================================================


async def list_room_participant_bindings(
    *,
    room_id: UUID,
    user_id: UUID,
    session: AsyncSession,
    include_history: bool = False,
) -> RoomParticipantBindingsPublic:
    """
    List runtime bindings for participants in a room.

    Authorization: active room membership required.
    """
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Not a room participant")

    stmt = select(RoomParticipantBinding).where(
        RoomParticipantBinding.room_id == room_id
    )
    if not include_history:
        stmt = stmt.where(RoomParticipantBinding.ended_at.is_(None))

    result = await session.exec(
        stmt.order_by(RoomParticipantBinding.effective_at.desc())
    )
    rows = list(result.all())
    return RoomParticipantBindingsPublic(data=rows, count=len(rows))


async def set_participant_binding(
    *,
    room_id: UUID,
    acting_user: User,
    participant_type: str,
    participant_id: str,
    persona_id: UUID | None,
    model_name: str | None,
    user_llm_provider_id: UUID | None,
    session: AsyncSession,
) -> RoomParticipantBinding:
    """
    Set a participant's active binding (event-sourced).

    Rules (agreed defaults, with clarified ownership semantics):
    - user_llm_provider_id (if set) must belong to acting_user
    - for agent participants: only agent owner or superuser may change any binding
    - for user participants: user themselves or room owner may change binding
    """
    if not await check_room_membership(
        room_id=room_id, user_id=acting_user.id, session=session
    ):
        raise HTTPException(status_code=403, detail="Not a room participant")

    resolved_user_id: UUID | None = None
    resolved_agent_id: UUID | None = None
    normalized_participant_id = participant_id
    agent_config: AgentConfig | None = None

    if participant_type == "user":
        try:
            resolved_user_id = UUID(participant_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid user participant_id (must be UUID string)",
            )
        normalized_participant_id = str(resolved_user_id)
    elif participant_type == "agent":
        # PRI-1 TODO: Remove agent UUID participant_id support once Milestone 1.1 tasks
        # 2, 3, and 4 are complete and validated (bindings table + binding event flow + APIs).
        try:
            agent_uuid = UUID(participant_id)
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.id == agent_uuid)
            )
            agent_config = agent_config_result.one_or_none()
        except ValueError:
            agent_config_result = await session.exec(
                select(AgentConfig).where(AgentConfig.slug == participant_id)
            )
            agent_config = agent_config_result.one_or_none()

        if not agent_config:
            raise HTTPException(status_code=400, detail="Agent not found")
        resolved_agent_id = agent_config.id
        normalized_participant_id = agent_config.slug
    else:
        raise HTTPException(
            status_code=400, detail="participant_type must be 'user' or 'agent'"
        )

    participant_result = await session.exec(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == participant_type,
            RoomParticipant.participant_id == normalized_participant_id,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = participant_result.one_or_none()
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found in room")

    is_owner = await check_room_owner(
        room_id=room_id, user_id=acting_user.id, session=session
    )
    if participant_type == "user":
        if not (is_owner or (resolved_user_id == acting_user.id)):
            raise HTTPException(status_code=403, detail="Access denied")
    else:
        # For agents, only the agent owner or superuser can change bindings.
        if not acting_user.is_superuser and agent_config.owner_id != acting_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the agent owner can change this agent's binding",
            )

    # Provider ownership rule (hard rule): only acting_user's providers can be referenced.
    if user_llm_provider_id is not None:
        provider_result = await session.exec(
            select(UserLLMProvider).where(
                UserLLMProvider.id == user_llm_provider_id,
                UserLLMProvider.user_id == acting_user.id,
            )
        )
        provider = provider_result.one_or_none()
        if not provider:
            raise HTTPException(
                status_code=403, detail="Invalid provider_id for current user"
            )

    # Persona ownership rule: must exist in participant's library (when persona_id is set).
    if persona_id is not None:
        if participant_type == "user":
            user_persona_result = await session.exec(
                select(UserPersona).where(
                    UserPersona.user_id == resolved_user_id,
                    UserPersona.persona_id == persona_id,
                )
            )
            if not user_persona_result.one_or_none():
                raise HTTPException(
                    status_code=400, detail="Persona not in user's library"
                )
        else:
            agent_persona_result = await session.exec(
                select(AgentPersona).where(
                    AgentPersona.agent_id == resolved_agent_id,
                    AgentPersona.persona_id == persona_id,
                )
            )
            if not agent_persona_result.one_or_none():
                raise HTTPException(
                    status_code=400, detail="Persona not in agent's library"
                )

    await emit_event(
        session=session,
        room_id=room_id,
        event_type="participant.binding_changed",
        payload={
            "participant_type": participant_type,
            "participant_id": normalized_participant_id,
            "persona_id": str(persona_id) if persona_id else None,
            "model_name": model_name,
            "user_llm_provider_id": (
                str(user_llm_provider_id) if user_llm_provider_id else None
            ),
            "actor_user_id": str(acting_user.id),
        },
    )

    binding_result = await session.exec(
        select(RoomParticipantBinding)
        .where(
            RoomParticipantBinding.room_id == room_id,
            RoomParticipantBinding.participant_type == participant_type,
            RoomParticipantBinding.participant_id == normalized_participant_id,
            RoomParticipantBinding.ended_at.is_(None),
        )
        .order_by(RoomParticipantBinding.effective_at.desc())
    )
    binding = binding_result.one()
    return binding


# ============================================================================
# Message Operations
# ============================================================================


async def list_room_messages(
      *,
      room_id: UUID,
      user_id: UUID,
      active_for_context: bool | None = None,
      is_pinned: bool | None = None,
      sender_type: str | None = None,
      sender_id: UUID | None = None,
      include_internal: bool = False,
      limit: int,
      before: datetime | None,
      session: AsyncSession,
  ) -> RoomMessagesPublic:
      """
      List room_messages from the RoomMessage projection with pagination constraints.
      ...
      """
      # Check membership
      if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
          raise HTTPException(status_code=403, detail="Access denied")

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ USER JOIN GOES HERE                                                  │
      # │ Join User table to get display names for user-sent messages         │
      # └─────────────────────────────────────────────────────────────────────┘
      query = (
          select(
              RoomMessage,
              User.full_name.label("sender_full_name"),  # ADD: user's full name
              User.email.label("sender_email"),          # ADD: fallback to email
          )
          .outerjoin(User, RoomMessage.sender_id == User.id)  # ADD: LEFT OUTER JOIN
          .where(RoomMessage.room_id == room_id)
          .order_by(RoomMessage.created_at.desc())
          .limit(limit)
      )

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ FILTERS GO HERE                                                      │
      # │ Apply the optional filters that are already defined in params       │
      # └─────────────────────────────────────────────────────────────────────┘
      if before:
          query = query.where(RoomMessage.created_at < before)

      if active_for_context is not None:  # ADD: filter by context status
          query = query.where(RoomMessage.active_for_context == active_for_context)

      if is_pinned is not None:  # ADD: filter by pinned status
          query = query.where(RoomMessage.is_pinned == is_pinned)

      if sender_type is not None:  # ADD: filter by sender type
          query = query.where(RoomMessage.sender_type == sender_type)
      elif not include_internal:
          query = query.where(RoomMessage.sender_type != "agent_internal")

      if sender_id is not None:
          query = query.where(RoomMessage.sender_id == sender_id)

      result = await session.exec(query)

      # ┌─────────────────────────────────────────────────────────────────────┐
      # │ RESULT PROCESSING CHANGES HERE                                       │
      # │ Now we get tuples of (RoomMessage, full_name, email) instead of     │
      # │ just RoomMessage objects                                             │
      # └─────────────────────────────────────────────────────────────────────┘
      rows = result.all()  # CHANGE: .all() instead of .scalars().all()

      # Build response with enriched display names
      messages = []
      for row in rows:
          msg = row[0]  # RoomMessage object
          sender_full_name = row[1]  # User.full_name (or None for agents)
          sender_email = row[2]  # User.email (or None for agents)

          # Compute display name
          if msg.sender_type == "agent":
              display_name = msg.agent_name
          else:
              display_name = sender_full_name or sender_email or "Unknown User"

          # Validate and add display name
          msg_public = RoomMessagePublic.model_validate(msg)
          msg_public.sender_display_name = display_name  # ADD field to model
          messages.append(msg_public)

      # Get total count for this room (consider if filters should apply here too)
      count_result = await session.exec(
          select(func.count()).select_from(RoomMessage).where(RoomMessage.room_id == room_id)
      )
      total_count = count_result.one()  # CHANGE: more efficient count query

      return RoomMessagesPublic(
          data=messages,
          count=total_count,
      )


async def send_user_message(
    *,
    room_id: UUID,
    user_id: UUID,
    content: str,
    session: AsyncSession,
) -> RoomMessage:
    """
    Send a user message to a room.

    NOTE: This function expects to be called within an active transaction.

    Emits room_message.user event which creates the message projection.

    Args:
        room_id: UUID of the room
        user_id: UUID of the user sending the message
        content: Message content
        session: Async database session with active transaction

    Returns:
        Created RoomMessage projection

    Raises:
        HTTPException: 403 if user is not an active participant
    """
    # Check membership
    if not await check_room_membership(room_id=room_id, user_id=user_id, session=session):
        raise HTTPException(status_code=403, detail="Access denied")

    # Emit message.user event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="room_message.user",
        payload={
            "sender_id": str(user_id),
            "content": content,
        },
    )

    # Fetch the most recent message for this user
    result = await session.exec(
        select(RoomMessage)
        .where(
            RoomMessage.room_id == room_id,
            RoomMessage.sender_id == user_id,
        )
        .order_by(RoomMessage.created_at.desc())
        .limit(1)
    )
    room_message = result.one()
    return room_message


# ============================================================================
# Message Management Operations (Phase 5)
# ============================================================================


async def edit_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    new_content: str,
    session: AsyncSession,
) -> RoomMessage:
    """
    Edit a message's content.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller:
    - User messages: Author OR room owner can edit
    - Agent messages: Owner only can edit

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to edit
        user_id: UUID of the user performing the edit
        new_content: New message content
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.edited event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.edited",
        payload={
            "message_id": str(message_id),
            "new_content": new_content,
            "edited_by": str(user_id),
        },
    )

    # Fetch and return updated message
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.one()


async def pin_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> RoomMessage:
    """
    Pin a message and auto-mark it as active for context.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to pin
        user_id: UUID of the user performing the pin
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.pinned event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.pinned",
        payload={
            "message_id": str(message_id),
            "pinned_by": str(user_id),
        },
    )

    # Fetch and return updated message
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.one()


async def unpin_message(
    *,
    room_id: UUID,
    message_id: UUID,
    session: AsyncSession,
) -> RoomMessage:
    """
    Unpin a message. Does NOT change active_for_context status.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to unpin
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.unpinned event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.unpinned",
        payload={
            "message_id": str(message_id),
        },
    )

    # Fetch and return updated message
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.one()


async def toggle_message_context(
    *,
    room_id: UUID,
    message_id: UUID,
    active_for_context: bool,
    session: AsyncSession,
) -> RoomMessage:
    """
    Toggle message active_for_context status.

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (any active participant).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message
        active_for_context: New active_for_context value
        session: Async database session with active transaction

    Returns:
        Updated RoomMessage projection

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.context_toggled event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.context_toggled",
        payload={
            "message_id": str(message_id),
            "active_for_context": active_for_context,
        },
    )

    # Fetch and return updated message
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    return result.one()


async def delete_message(
    *,
    room_id: UUID,
    message_id: UUID,
    user_id: UUID,
    session: AsyncSession,
) -> None:
    """
    Delete a message (soft delete via event).

    NOTE: This function expects to be called within an active transaction.

    Authorization must be checked by caller (owner only).

    Args:
        room_id: UUID of the room
        message_id: UUID of the message to delete
        user_id: UUID of the user performing the deletion
        session: Async database session with active transaction

    Raises:
        HTTPException: 404 if message does not exist
    """
    # Verify message exists
    result = await session.exec(
        select(RoomMessage).where(RoomMessage.message_id == message_id)
    )
    message = result.one_or_none()

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Emit message.deleted event
    await emit_event(
        session=session,
        room_id=room_id,
        event_type="message.deleted",
        payload={
            "message_id": str(message_id),
            "deleted_by": str(user_id),
        },
    )

# ==================== Phase 2 CYOA: State Replay Functions ====================
#
# These functions implement event sourcing replay logic:
#
# 1. get_choice_ancestor_chain() - Traverses parent pointers from head to root
# 2. replay_state_from_head() - Reconstructs state by merging state_changes
# 3. get_current_node_from_head() - Derives current node from head position
#
# In Phase 2, these functions VALIDATE existing mutable state.
# In Phase 5, these become the SOURCE OF TRUTH for state.
#
# Performance: O(n) where n = chain length. Target < 50ms for 100 choices.
# Optimization: Snapshots added in Phase 5 reduce replay cost.
# ===========================================================================

def get_choice_ancestor_chain(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get ancestor chain from root to specified choice (inclusive).

    Returns events in order: [root_choice, ..., parent_choice, choice_id]
    Used for replay and timeline display.

    Args:
        session: Database session
        choice_id: Target choice UUID

    Returns:
        List of UserNodeChoice objects from root to target (ordered)

    Raises:
        ValueError: If choice_id doesn't exist in database
    """
    chain = []
    current_id = choice_id

    while current_id is not None:
        choice = session.get(UserNodeChoice, current_id)
        if not choice:
            # If we can't find a choice in the chain, something is corrupt
            raise ValueError(f"Choice {current_id} not found in database (data corruption)")
        chain.append(choice)
        current_id = choice.parent_choice_id

    return list(reversed(chain))  # Root → head order

def replay_state_from_head(
    *, session: Session, progress_id: uuid.UUID, head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying all events from root to head.

    This is the SOURCE OF TRUTH for state in event-sourced model.
    The UserStoryProgress.story_state field becomes a denormalized cache.

    Args:
        session: Database session
        progress_id: UserStoryProgress UUID (for validation)
        head_choice_id: Current head position (null = story start)

    Returns:
        Reconstructed state dictionary

    Raises:
        ValueError: If choice doesn't belong to progress_id
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get all events from root to head
    chain = get_choice_ancestor_chain(session=session, choice_id=head_choice_id)

    # Validate all choices belong to this progress
    for choice in chain:
        if choice.progress_id != progress_id:
            raise ValueError(
                f"Choice {choice.id} doesn't belong to progress {progress_id}"
            )

    # Replay events (shallow merge)
    state: dict[str, Any] = {}
    for choice in chain:
        if choice.state_changes:
            state.update(choice.state_changes)

    return state

def get_current_node_from_head(
    *,
    session: Session,
    head_choice_id: uuid.UUID | None,
    story_id: uuid.UUID,
    story_version: int,
) -> uuid.UUID:
    """
    Derive current_node_id from head position.

    If head_choice_id is None, return start node.
    Otherwise, return to_node_id of head choice.

    Args:
        session: Database session
        head_choice_id: Current head position (null = story start)
        story_id: Story UUID (for finding start node)
        story_version: Story version (for finding start node)

    Returns:
        UUID of current story node

    Raises:
        ValueError: If no start node found or head choice missing
    """
    if head_choice_id is None:
        # At story start - find start node
        statement = select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == story_version,
            StoryNode.is_start_node == True,  # noqa: E712
        )
        start_node = session.exec(statement).first()
        if not start_node:
            raise ValueError(
                f"No start node for story {story_id} version {story_version}"
            )
        return start_node.id

    # Return destination of head choice
    choice = session.get(UserNodeChoice, head_choice_id)
    if not choice:
        raise ValueError(f"Head choice {head_choice_id} not found")
    return choice.to_node_id

def get_choice_children(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get all direct children of a choice (for debugging/admin tools).

    In normal gameplay, children are hidden (abandoned branches).
    This is used for admin visualization of the full event tree.

    Args:
        session: Database session
        choice_id: Parent choice UUID

    Returns:
        List of child UserNodeChoice objects
    """
    statement = select(UserNodeChoice).where(
        UserNodeChoice.parent_choice_id == choice_id
    )
    return list(session.exec(statement).all())

# ==================== Phase 3: Timeline Navigation Functions ====================
#
# IMPROVEMENT OVER MIGRATION PLAN:
# The migration plan shows inline replay logic in undo/jump endpoints.
# These helper functions extract common logic for DRY and maintainability.
# This follows TinyFoot functional patterns from RULES.md.
# ==============================================================================

def validate_ancestor_constraint(
    *, session: Session, target_choice_id: uuid.UUID, current_head_id: uuid.UUID
) -> bool:
    """
    Validate that target choice is an ancestor of current head.

    Used by jump endpoint to prevent forward jumps (which would expose hidden branches).
    Forward jumps are prohibited because they would reveal abandoned timeline branches.

    Args:
        session: Database session
        target_choice_id: Proposed jump target
        current_head_id: Current head position

    Returns:
        True if target is ancestor of current head, False otherwise

    Raises:
        ValueError: If current_head_id doesn't exist (via get_choice_ancestor_chain)

    Example:
        # Before jump, validate target is in ancestor chain
        is_ancestor = crud.validate_ancestor_constraint(
            session=session,
            target_choice_id=target,
            current_head_id=progress.head_choice_id
        )
        if not is_ancestor:
            raise HTTPException(400, "Target is not an ancestor")
    """
    # Get ancestor chain from current head to root
    ancestors = get_choice_ancestor_chain(session=session, choice_id=current_head_id)
    ancestor_ids = {c.id for c in ancestors}

    # Check if target is in the ancestor chain
    return target_choice_id in ancestor_ids


def move_head_to_choice(
    *,
    session: Session,
    progress: UserStoryProgress,
    target_choice_id: uuid.UUID | None,
) -> UserStoryProgress:
    """
    Move head pointer to target choice and update derived state.

    This is the core function for undo/jump operations.
    Encapsulates head movement, state replay, and node derivation.

    IMPORTANT: This function uses replay to UPDATE story_state.
    Unlike make_story_choice (which still uses mutable updates in Phase 3),
    timeline navigation MUST replay because we're moving backward in time.

    Args:
        session: Database session
        progress: UserStoryProgress instance to update
        target_choice_id: Target choice (null = story start)

    Returns:
        Updated UserStoryProgress instance (mutated in place)

    Side effects:
        - Updates progress.head_choice_id to target
        - Increments progress.head_version (optimistic lock)
        - Replays state from new head (replaces progress.story_state)
        - Updates progress.current_node_id
        - Resets progress.is_completed flag (might not be at end anymore)

    Raises:
        ValueError: If target_choice_id doesn't exist or state replay fails

    Example:
        # In undo endpoint
        current_choice = session.get(UserNodeChoice, progress.head_choice_id)
        progress = crud.move_head_to_choice(
            session=session,
            progress=progress,
            target_choice_id=current_choice.parent_choice_id  # Move to parent
        )
        session.add(progress)
        session.commit()
    """
    # Move head pointer
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # Replay state from new head position
    # Uses Phase 2 replay_state_from_head (NOT the optimized version from Phase 5)
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=target_choice_id,
    )

    # Derive current node from new head position
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=target_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version,
    )

    # Reset completion flag (might not be at end node anymore)
    progress.is_completed = False

    return progress

def replay_state_from_head_optimized(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying events, using snapshots for optimization.

    This is the FINAL SOURCE OF TRUTH for state in event-sourced model.

    Algorithm:
    1. If head is None, return {} (at story start)
    2. Get ancestor chain (root → head)
    3. Find nearest snapshot in ancestor chain
    4. If snapshot exists, start from snapshot and replay events after it
    5. If no snapshot, replay from root

    Args:
        session: Database session
        progress_id: UserStoryProgress ID
        head_choice_id: Current head position (null = story start)

    Returns:
        Reconstructed state dict

    Performance:
        - Without snapshots: O(n) where n = chain length
        - With snapshots: O(k) where k = choices since last snapshot
        - Target: < 10ms for 100-choice chain with snapshots
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get full ancestor chain
    ancestor_chain = get_choice_ancestor_chain(
        session=session,
        choice_id=head_choice_id
    )

    if not ancestor_chain:
        return {}

    # Find nearest snapshot in ancestor chain
    ancestor_ids = [c.id for c in ancestor_chain]

    snapshot_stmt = (
        select(ProgressSnapshot)
        .where(
            ProgressSnapshot.progress_id == progress_id,
            ProgressSnapshot.choice_id.in_(ancestor_ids),
        )
        .order_by(desc(ProgressSnapshot.created_at))
        .limit(1)
    )

    snapshot = session.exec(snapshot_stmt).first()

    if snapshot:
        # Start from snapshot and replay events after it
        state = snapshot.story_state.copy()

        # Find snapshot position in ancestor chain
        snapshot_idx = next(
            i for i, c in enumerate(ancestor_chain)
            if c.id == snapshot.choice_id
        )

        # Replay events AFTER snapshot
        for choice in ancestor_chain[snapshot_idx + 1:]:
            if choice.state_changes:
                state.update(choice.state_changes)
    else:
        # No snapshot - replay from root
        state = {}
        for choice in ancestor_chain:
            if choice.state_changes:
                state.update(choice.state_changes)

    return state


def create_snapshot_if_needed(
    *,
    session: Session,
    progress: UserStoryProgress,
    snapshot_interval: int = 10
) -> ProgressSnapshot | None:
    """
    Create snapshot if we've reached the snapshot interval.

    Call this after making a choice or moving head.

    Args:
        session: Database session
        progress: UserStoryProgress record (must have head_choice_id set)
        snapshot_interval: Create snapshot every N choices (default: 10)

    Returns:
        Created snapshot, or None if not needed

    Example:
        # After creating choice
        progress.head_choice_id = user_choice.id
        snapshot = crud.create_snapshot_if_needed(
            session=session,
            progress=progress,
            snapshot_interval=10
        )
        if snapshot:
            session.add(snapshot)
    """
    if progress.head_choice_id is None:
        return None  # At story start, no snapshot needed

    # Get chain length
    chain = get_choice_ancestor_chain(
        session=session,
        choice_id=progress.head_choice_id
    )
    chain_length = len(chain)

    # Check if we should create snapshot
    if chain_length % snapshot_interval == 0:
        # Check if snapshot already exists at this position
        existing = session.exec(
            select(ProgressSnapshot).where(
                ProgressSnapshot.progress_id == progress.id,
                ProgressSnapshot.choice_id == progress.head_choice_id
            )
        ).first()

        if existing:
            return None  # Already have snapshot at this position

        # Create snapshot
        snapshot = ProgressSnapshot(
            progress_id=progress.id,
            choice_id=progress.head_choice_id,
            story_state=progress.story_state.copy() if progress.story_state else {},
            current_node_id=progress.current_node_id
        )

        return snapshot

    return None


def get_nearest_snapshot(
    *,
    session: Session,
    progress_id: uuid.UUID,
    head_choice_id: uuid.UUID
) -> ProgressSnapshot | None:
    """
    Get nearest snapshot at or before head position.

    Args:
        session: Database session
        progress_id: UserStoryProgress ID
        head_choice_id: Target head position

    Returns:
        Nearest snapshot, or None if no snapshots exist
    """
    # Get ancestor chain to find all possible snapshot positions
    chain = get_choice_ancestor_chain(
        session=session,
        choice_id=head_choice_id
    )

    if not chain:
        return None

    ancestor_ids = [c.id for c in chain]

    # Find most recent snapshot in ancestor chain
    statement = (
        select(ProgressSnapshot)
        .where(
            ProgressSnapshot.progress_id == progress_id,
            ProgressSnapshot.choice_id.in_(ancestor_ids),
        )
        .order_by(desc(ProgressSnapshot.created_at))
        .limit(1)
    )

    return session.exec(statement).first()

def create_agent_config(
     *,
     session: Session,
     agent_in: AgentConfigCreate,
     owner_id: uuid.UUID | None = None,
 ) -> AgentConfig:
     """Create a new agent configuration."""
     db_obj = AgentConfig.model_validate(agent_in, update={"owner_id": owner_id})
     session.add(db_obj)
     session.commit()
     session.refresh(db_obj)
     return db_obj


def get_agent_config(*, session: Session, agent_id: uuid.UUID) -> AgentConfig | None:
     return session.get(AgentConfig, agent_id)


def get_agent_config_by_slug(*, session: Session, slug: str) -> AgentConfig | None:
     statement = select(AgentConfig).where(AgentConfig.slug == slug)
     return session.exec(statement).first()


def get_agent_configs(
     *,
     session: Session,
     skip: int = 0,
     limit: int = 100,
     enabled_only: bool = True,
     scope: str | None = None,
     owner_id: uuid.UUID | None = None,
 ) -> tuple[list[AgentConfig], int]:
     """Get paginated agent configs with filtering."""
     filters = []
     if enabled_only:
         filters.append(AgentConfig.is_enabled)
     if scope:
         filters.append(AgentConfig.scope == scope)
     if owner_id:
         filters.append(AgentConfig.owner_id == owner_id)

     count_stmt = select(func.count()).select_from(AgentConfig).where(*filters)
     count = session.exec(count_stmt).one()

     stmt = select(AgentConfig).where(*filters).offset(skip).limit(limit)
     configs = session.exec(stmt).all()
     return list(configs), count


def update_agent_config(
     *,
     session: Session,
     db_agent: AgentConfig,
     agent_in: AgentConfigUpdate,
 ) -> AgentConfig:
     update_data = agent_in.model_dump(exclude_unset=True)
     db_agent.sqlmodel_update(update_data)
     db_agent.version += 1
     session.add(db_agent)
     session.commit()
     session.refresh(db_agent)
     return db_agent

def delete_agent_config(*, session: Session, db_agent: AgentConfig) -> None:
    session.delete(db_agent)
    session.commit()



# =============================================================================
# LLM User Model CRUD Operations
# =============================================================================


def _generate_display_name(model_id: str) -> str:
    """Simple display name from model_id: 'llama3:70b' -> 'Llama3 70B'"""
    name = model_id.replace(":", " ").replace("-", " ").replace("_", " ")
    return name.title()


def create_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_in: LLMModelCreate,
) -> LLMModel:
    """Create a user-owned custom model."""
    data = model_in.model_dump(exclude={"provider_id", "is_system"})

    # Auto-generate display_name if not provided
    if not data.get("display_name"):
        data["display_name"] = _generate_display_name(model_in.model_id)

    model = LLMModel(
        **data,
        provider_id=model_in.provider_id,
        created_by_user_id=user_id,
        is_system=False,
    )
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_user_models(
    *,
    session: Session,
    user_id: uuid.UUID,
    provider_type: LLMProviderType | None = None,
) -> list[LLMModel]:
    """Get all custom models for a user."""
    filters = [
        LLMModel.created_by_user_id == user_id,
        not LLMModel.is_deleted,
    ]

    stmt = select(LLMModel).where(*filters).order_by(LLMModel.display_name)

    # Filter by provider_type requires join to LLMProvider
    if provider_type is not None:
        stmt = (
            select(LLMModel)
            .join(LLMProvider)
            .where(*filters, LLMProvider.provider_type == provider_type)
            .order_by(LLMModel.display_name)
        )

    return list(session.exec(stmt).all())


def delete_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_id: uuid.UUID,
) -> bool:
    """Soft-delete a user's custom model. Returns True if deleted."""
    model = session.get(LLMModel, model_id)
    if not model or model.created_by_user_id != user_id:
        return False

    model.is_deleted = True
    model.deleted_at = datetime.now()
    session.add(model)
    session.commit()
    return True


# =============================================================================
# LLM Catalog CRUD Operations
# =============================================================================


def get_llm_providers(
    *,
    session: Session,
    skip: int = 0,
    limit: int = 100,
    provider_type: LLMProviderType | None = None,
    is_enabled: bool | None = None,
    is_system: bool | None = None,
    include_deleted: bool = False,
) -> tuple[list[LLMProvider], int]:
    """Get paginated LLM providers with filtering."""
    filters = []
    if not include_deleted:
        filters.append(not LLMProvider.is_deleted)
    if provider_type is not None:
        filters.append(LLMProvider.provider_type == provider_type)
    if is_enabled is not None:
        filters.append(LLMProvider.is_enabled == is_enabled)
    if is_system is not None:
        filters.append(LLMProvider.is_system == is_system)

    count_stmt = select(func.count()).select_from(LLMProvider).where(*filters)
    count = session.exec(count_stmt).one()

    stmt = (
        select(LLMProvider)
        .where(*filters)
        .order_by(LLMProvider.name)
        .offset(skip)
        .limit(limit)
    )
    providers = session.exec(stmt).all()
    return list(providers), count


def get_llm_provider(
    *,
    session: Session,
    provider_id: uuid.UUID,
    include_deleted: bool = False,
) -> LLMProvider | None:
    """Get a single LLM provider by ID."""
    provider = session.get(LLMProvider, provider_id)
    if provider and not include_deleted and provider.is_deleted:
        return None
    return provider


def get_llm_provider_model_count(
    *,
    session: Session,
    provider_id: uuid.UUID,
    include_deleted: bool = False,
) -> int:
    """Get count of active models for a provider."""
    filters = [LLMModel.provider_id == provider_id]
    if not include_deleted:
        filters.append(not LLMModel.is_deleted)
        filters.append(LLMModel.is_enabled)

    stmt = select(func.count()).select_from(LLMModel).where(*filters)
    return session.exec(stmt).one()


def get_llm_models(
    *,
    session: Session,
    user_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    provider_id: uuid.UUID | None = None,
    provider_type: LLMProviderType | None = None,
    is_enabled: bool | None = None,
    is_deprecated: bool | None = None,
    is_default: bool | None = None,
    has_vision: bool | None = None,
    has_function_calling: bool | None = None,
    has_streaming: bool | None = None,
    has_json_mode: bool | None = None,
    include_deleted: bool = False,
) -> tuple[list[tuple[LLMModel, LLMProvider]], int]:
    """
    Get paginated LLM models with filtering. Returns tuples of (model, provider).

    If user_id is provided, includes the user's custom models alongside system models.
    """
    filters = []
    if not include_deleted:
        filters.append(not LLMModel.is_deleted)
        filters.append(not LLMProvider.is_deleted)

    # Ownership filter: system models OR user's custom models
    if user_id is not None:
        filters.append(
            or_(
                LLMModel.is_system,
                LLMModel.created_by_user_id == user_id,
            )
        )
    else:
        # No user - only system models
        filters.append(LLMModel.is_system)

    if provider_id is not None:
        filters.append(LLMModel.provider_id == provider_id)
    if provider_type is not None:
        filters.append(LLMProvider.provider_type == provider_type)
    if is_enabled is not None:
        filters.append(LLMModel.is_enabled == is_enabled)
    if is_deprecated is not None:
        filters.append(LLMModel.is_deprecated == is_deprecated)
    if is_default is not None:
        filters.append(LLMModel.is_default == is_default)
    if has_vision is not None:
        filters.append(LLMModel.has_vision == has_vision)
    if has_function_calling is not None:
        filters.append(LLMModel.has_function_calling == has_function_calling)
    if has_streaming is not None:
        filters.append(LLMModel.has_streaming == has_streaming)
    if has_json_mode is not None:
        filters.append(LLMModel.has_json_mode == has_json_mode)

    count_stmt = (
        select(func.count())
        .select_from(LLMModel)
        .join(LLMProvider)
        .where(*filters)
    )
    count = session.exec(count_stmt).one()

    stmt = (
        select(LLMModel, LLMProvider)
        .join(LLMProvider)
        .where(*filters)
        .order_by(LLMProvider.name, LLMModel.sort_order, LLMModel.display_name)
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(stmt).all()
    return list(results), count


def get_llm_model(
    *,
    session: Session,
    model_id: uuid.UUID,
    include_deleted: bool = False,
) -> tuple[LLMModel, LLMProvider] | None:
    """Get a single LLM model by ID with its provider."""
    model = session.get(LLMModel, model_id)
    if not model:
        return None
    if not include_deleted and model.is_deleted:
        return None

    provider = session.get(LLMProvider, model.provider_id)
    if not provider:
        return None
    if not include_deleted and provider.is_deleted:
        return None

    return model, provider


def get_llm_models_grouped(
    *,
    session: Session,
    user_id: uuid.UUID | None = None,
    provider_type: LLMProviderType | None = None,
    is_enabled: bool | None = None,
    include_deleted: bool = False,
) -> list[tuple[LLMProvider, list[LLMModel]]]:
    """
    Get models grouped by provider for UI display.

    If user_id is provided, includes the user's custom models alongside system models.
    """
    # Get providers
    provider_filters = []
    if not include_deleted:
        provider_filters.append(not LLMProvider.is_deleted)
    if provider_type is not None:
        provider_filters.append(LLMProvider.provider_type == provider_type)
    if is_enabled is not None:
        provider_filters.append(LLMProvider.is_enabled == is_enabled)

    provider_stmt = (
        select(LLMProvider)
        .where(*provider_filters)
        .order_by(LLMProvider.name)
    )
    providers = session.exec(provider_stmt).all()

    # Get models for each provider
    result = []
    for provider in providers:
        model_filters = [LLMModel.provider_id == provider.id]
        if not include_deleted:
            model_filters.append(not LLMModel.is_deleted)
        if is_enabled is not None:
            model_filters.append(LLMModel.is_enabled == is_enabled)

        # Ownership filter: system models OR user's custom models
        if user_id is not None:
            model_filters.append(
                or_(
                    LLMModel.is_system,
                    LLMModel.created_by_user_id == user_id,
                )
            )
        else:
            model_filters.append(LLMModel.is_system)

        model_stmt = (
            select(LLMModel)
            .where(*model_filters)
            .order_by(LLMModel.sort_order, LLMModel.display_name)
        )
        models = list(session.exec(model_stmt).all())
        if models:  # Only include providers with models
            result.append((provider, models))

    return result
