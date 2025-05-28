import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Story,
    StoryCreate,
    StoryPublic,
    StoriesPublic,
    StoryUpdate,
    Message,
)

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("/", response_model=StoriesPublic)
def read_stories(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve stories.
    """

    count_statement = select(func.count()).select_from(Story)
    count = session.exec(count_statement).one()
    statement = select(Story).offset(skip).limit(limit)
    stories = session.exec(statement).all()

    return StoriesPublic(data=stories, count=count)  # type: ignore


@router.get("/{id}", response_model=StoryPublic)
def read_story(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Retrieve a story by ID.
    """

    story = session.exec(select(Story).where(Story.id == id)).one_or_none()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.post("/", response_model=StoryPublic)
def create_story(
    *, session: SessionDep, current_user: CurrentUser, story_in: StoryCreate
) -> Any:
    """
    Create a new story.
    """
    story = Story(**story_in.model_dump(), owner_id=current_user.id)
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


@router.put("/{id}", response_model=StoryPublic)
def update_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    story_in: StoryUpdate
) -> Any:
    """
    Update a story by ID.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = story_in.model_dump(exclude_unset=True)
    story.sqlmodel_update(update_dict)
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


@router.delete("/{id}")
def delete_story(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a story by ID.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(story)
    session.commit()
    return Message(message="Story deleted successfully")

@router.get("/{story_id}/current-node", response_model=Dict[str, Any])
def get_current_node(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get the current node and available choices for the user's story progress.
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

    if not progress.current_node_id:
        raise HTTPException(status_code=400, detail="No current node in this story")

    # Get the current node
    current_node = session.get(StoryNode, progress.current_node_id)
    if not current_node:
        raise HTTPException(status_code=404, detail="Current node not found")

    # Get available choices
    available_choices = crud.get_available_choices(
        session=session,
        node_id=progress.current_node_id,
        story_state=progress.story_state,
    )

    # Return the node and available choices
    return {
        "node": current_node,
        "available_choices": available_choices,
        "story_state": progress.story_state,
    }