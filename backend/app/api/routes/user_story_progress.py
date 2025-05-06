import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UserStoryProgress,
    UserStoryProgressCreate,
    UserStoryProgressPublic,
    UserStoryProgressesPublic,
    UserStoryProgressUpdate,
    Message,
    UserPersona,
)

router = APIRouter(prefix="/user-personas/{user_persona_id}/stories", tags=["user-story-progress"])


@router.get("/", response_model=UserStoryProgressesPublic)
def read_user_story_progresses(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve story progresses for a specific user persona.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progresses, count = crud.get_user_story_progresses(
        session=session, user_persona_id=user_persona_id, skip=skip, limit=limit
    )
    return UserStoryProgressesPublic(data=progresses, count=count)


@router.get("/{story_id}", response_model=UserStoryProgressPublic)
def read_user_story_progress(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID
) -> Any:
    """
    Get a user's progress in a specific story.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    return progress


@router.post("/{story_id}", response_model=UserStoryProgressPublic)
def create_user_story_progress(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID
) -> Any:
    """
    Start a new story with a user persona.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Check if the story exists
    story = session.get("Story", story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check if the user already has progress for this story
    existing_progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if existing_progress:
        raise HTTPException(
            status_code=400,
            detail="Progress for this story already exists"
        )

    # Check if the user persona meets the story requirements
    if not crud.check_story_requirements(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    ):
        raise HTTPException(
            status_code=403,
            detail="User persona does not meet story requirements"
        )

    # Find the starting node of the story
    statement = select(StoryNode).where(
        StoryNode.story_id == story_id,
        StoryNode.is_start_node == True
    )
    start_node = session.exec(statement).first()

    # Create the progress
    progress_in = UserStoryProgressCreate(
        user_persona_id=user_persona_id,
        story_id=story_id,
        current_node_id=start_node.id if start_node else None
    )

    progress = crud.create_user_story_progress(
        session=session, progress_in=progress_in
    )
    return progress


@router.put("/{story_id}", response_model=UserStoryProgressPublic)
def update_user_story_progress(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    progress_in: UserStoryProgressUpdate,
) -> Any:
    """
    Update a user's progress in a story.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Update the progress
    progress = crud.update_user_story_progress(
        session=session, db_progress=progress, progress_in=progress_in
    )
    return progress

@router.post("/{story_id}/nodes/{node_id}/choices", response_model=UserStoryProgressPublic)
def make_node_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    node_id: uuid.UUID,
    choice_id: uuid.UUID,
) -> Any:
    """
    Make a choice at the current node and progress the story.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Get the user's progress in this story
    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Check if the current node matches
    if progress.current_node_id != node_id:
        raise HTTPException(
            status_code=400,
            detail="Invalid node ID. This is not the current node in your story."
        )

    # Get the choice
    choice = session.get(NodeChoice, choice_id)
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")

    # Verify the choice belongs to the current node
    if choice.from_node_id != node_id:
        raise HTTPException(
            status_code=400,
            detail="This choice is not available for the current node."
        )

    # Create a record of the choice
    user_choice = UserNodeChoice(
        progress_id=progress.id,
        choice_text=choice.text,
        from_node_id=node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state
    )
    session.add(user_choice)

    # Update the story state if needed
    if choice.sets_state and progress.story_state:
        # Merge the existing state with the new state changes
        progress.story_state.update(choice.sets_state)
    elif choice.sets_state:
        progress.story_state = choice.sets_state

    # Update the current node
    progress.current_node_id = choice.to_node_id

    # Check if this is an end node
    to_node = session.get(StoryNode, choice.to_node_id)
    if to_node and to_node.is_end_node:
        progress.is_completed = True

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
