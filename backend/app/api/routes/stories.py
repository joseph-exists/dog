"""
Story Routes - Story Template CRUD Operations (AUTHORING Namespace)

Handles authoring concerns for Story templates.
Stories track versioning and publication state.

Endpoints:
- GET /stories - List user's stories (owner check)
- GET /stories/{id} - Get story details
- GET /stories/{id}/start-node - Get starting node for current_version
- POST /stories - Create new story
- PUT /stories/{id} - Update story metadata
- PUT /stories/{id}/publish - Publish current_version to catalog
- PUT /stories/{id}/unpublish - Hide from catalog (keeps published_version)
- POST /stories/{id}/new-version - Increment version, copy nodes from published
- DELETE /stories/{id} - Delete story (superuser only)

Note: These endpoints work with current_version for editing.
For browsing published stories, use /catalog endpoints instead.
"""
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    NodeChoice,
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

@router.put("/{id}/publish", response_model=StoryPublic)
def publish_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> Any:
    """
    Publish a story by ID.

    Only the story owner or superusers can publish a story.
    This locks the current_version as published_version and sets is_published=True.
    Players will be locked to this published_version when they start the story.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Lock current_version as published_version
    story.published_version = story.current_version
    story.is_published = True
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


@router.put("/{id}/unpublish", response_model=StoryPublic)
def unpublish_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> Any:
    """
    Unpublish a story by ID.

    Only the story owner or superusers can unpublish a story.
    This sets is_published=False but keeps published_version intact.
    Existing players continue playing the published_version unaffected.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")
    
    story.is_published = False
    session.add(story)
    session.commit()
    session.refresh(story)
    return story

@router.post("/{id}/new-version", response_model=StoryPublic)
def create_new_story_version(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID
) -> Any:
    """
    Create a new version of a story by incrementing current_version.

    Only the story owner or superusers can create new versions.
    This copies all nodes from the current published_version to the new current_version.
    The published_version remains locked and unchanged.

    Use this when you want to edit a published story without affecting existing players.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Verify story has been published at least once
    if story.published_version is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot create new version - story has never been published"
        )

    # Increment current_version
    new_version = story.current_version + 1
    story.current_version = new_version

    # Copy all nodes from published_version to new current_version
    # Get all nodes from published version
    published_nodes_statement = select(StoryNode).where(
        StoryNode.story_id == id,
        StoryNode.story_version == story.published_version
    )
    published_nodes = session.exec(published_nodes_statement).all()

    # Create mapping of old node IDs to new node IDs (for choices)
    node_id_mapping: dict[uuid.UUID, uuid.UUID] = {}

    # Create copies with new version number
    for node in published_nodes:
        new_node_id = uuid.uuid4()
        node_id_mapping[node.id] = new_node_id

        new_node = StoryNode.model_validate(
            node,
            update={
                "id": new_node_id,  # New UUID for the copy
                "story_version": new_version,  # New version
            }
        )
        session.add(new_node)

    # Flush to make new nodes available for choice copying
    session.flush()

    # Copy all choices, updating node references to new IDs
    old_node_ids = list(node_id_mapping.keys())
    choices_statement = select(NodeChoice).where(
        NodeChoice.from_node_id.in_(old_node_ids)
    )
    published_choices = session.exec(choices_statement).all()

    for choice in published_choices:
        new_choice = NodeChoice.model_validate(
            choice,
            update={
                "id": uuid.uuid4(),  # New UUID for the copy
                "from_node_id": node_id_mapping[choice.from_node_id],  # Map to new node
                "to_node_id": node_id_mapping[choice.to_node_id],  # Map to new node
            }
        )
        session.add(new_choice)

    # Commit all changes
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
    
    Only superusers can delete a story.  Authors cannot delete stories yet.
    This will be changed in the future to allow authors to delete their own unpublished stories.
    Problem is with stories that are in play or associated with other data.
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