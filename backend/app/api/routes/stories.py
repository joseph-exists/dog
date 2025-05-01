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
