"""
Story Routes - Story Template CRUD Operations

Handles authoring concerns for Story templates.
Stories track versioning and publication state.

Endpoints:
- GET /stories - List stories (with pagination)
- GET /stories/{id} - Get single story
- GET /stories/{id}/start-node - Get the starting node for a story
- POST /stories - Create new story
- PUT /stories/{id} - Update story
- DELETE /stories/{id} - Delete story
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    Story,
    StoryCreate,
    StoryPublic,
    StoriesPublic,
    StoryUpdate,
    StoryNode,
    StoryNodePublic,
)

router = APIRouter(prefix="/stories", tags=["stories"])


@router.get("/", response_model=StoriesPublic)
def read_stories(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 10
) -> Any:
    """
    Retrieve stories.
    
    Superusers see all stories.
    Regular users see only their own stories.
    """
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Story)
        count = session.exec(count_statement).one()
        statement = select(Story).offset(skip).limit(limit)
        stories = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Story)
            .where(Story.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Story)
            .where(Story.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
        )
        stories = session.exec(statement).all()

    return StoriesPublic(data=stories, count=count)  # type: ignore


@router.get("/{id}", response_model=StoryPublic)
def read_story(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Retrieve a story by ID.
    
    Users can only access their own stories unless they are superusers.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return story


@router.get("/{id}/start-node", response_model=StoryNodePublic)
def get_story_start_node(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get the starting node for a story.
    
    Returns the node marked as is_start_node=True for the story's current_version.
    This is a helper endpoint to make it easier for clients to initialize
    story progress without querying all nodes.
    
    Users can only access their own stories unless they are superusers.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Find the start node for the current version
    statement = select(StoryNode).where(
        StoryNode.story_id == id,
        StoryNode.story_version == story.current_version,
        StoryNode.is_start_node is True
    )
    start_node = session.exec(statement).first()
    
    if not start_node:
        raise HTTPException(
            status_code=404,
            detail=f"No start node found for story version {story.current_version}"
        )
    
    return start_node


@router.post("/", response_model=StoryPublic)
def create_story(
    *, session: SessionDep, current_user: CurrentUser, story_in: StoryCreate
) -> Any:
    """
    Create a new story.
    
    New stories start at version 1 and are unpublished by default.
    The story is automatically associated with the current user as owner.
    """
    story = Story.model_validate(story_in, update={"owner_id": current_user.id})
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
    
    Only the story owner or superusers can update a story.
    This updates the story metadata but not its version.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
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
    
    Only the story owner or superusers can delete a story.
    This cascades to all nodes, choices, and user progresses.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    session.delete(story)
    session.commit()
    return Message(message="Story deleted successfully")