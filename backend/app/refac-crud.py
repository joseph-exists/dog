

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
