"""
Node Choice Routes - Story Decision Branch CRUD

Handles creating and managing choices between story nodes.
Choices define the decision tree structure of interactive narratives.

Endpoints:
- GET /node-choices - List all choices (filtered by query params)
- GET /node-choices/{choice_id} - Get single choice
- POST /node-choices - Create new choice
- PUT /node-choices/{choice_id} - Update choice
- DELETE /node-choices/{choice_id} - Delete choice

Optional convenience endpoints:
- GET /storynodes/{node_id}/choices - List choices from this node
- POST /storynodes/{node_id}/choices - Create choice from this node
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    NodeChoice,
    Story,
    StoryNode,
    NodeChoicesPublic,
    NodeChoicePublic,
    NodeChoiceCreate,
    NodeChoiceUpdate,
    UserNodeChoice,
    Message,
)
from app import crud

router = APIRouter(prefix="/node-choices", tags=["node-choices"])

@router.get("/", response_model=NodeChoicesPublic)
def read_node_choices(
    session: SessionDep,
    current_user: CurrentUser,
    from_node_id: uuid.UUID | None = None,
    story_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Retrieve node choices with optional filtering.

    Filters:
    - from_node_id: Get choices originating from specific node
    - story_id: Get all choices for a story (joins through StoryNode)
    """
    query = select(NodeChoice)

    # Filter by from_node_id if provided
    if from_node_id:
        query = query.where(NodeChoice.from_node_id == from_node_id)

    # Filter by story_id if provided (requires join with StoryNode)
    if story_id:
        query = query.join(
            StoryNode,
            NodeChoice.from_node_id == StoryNode.id
        ).where(StoryNode.story_id == story_id)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    count = session.exec(count_query).one()

    # Get paginated results
    choices = session.exec(query.offset(skip).limit(limit)).all()

    return NodeChoicesPublic(data=choices, count=count)

@router.get("/{choice_id}", response_model=NodeChoicePublic)
def read_node_choice(
    session: SessionDep,
    current_user: CurrentUser,
    choice_id: uuid.UUID
) -> Any:
    """
    Get node choice by ID.
    """
    choice = session.get(NodeChoice, choice_id)
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")
    return choice

@router.post("/", response_model=NodeChoicePublic)
def create_node_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    choice_in: NodeChoiceCreate
) -> Any:
    """
    Create new node choice.

    Validates:
    - Both nodes exist
    - Nodes belong to same story and version
    - from_node is not an end node
    - User owns the story
    """
    # Get nodes
    from_node = session.get(StoryNode, choice_in.from_node_id)
    to_node = session.get(StoryNode, choice_in.to_node_id)

    if not from_node:
        raise HTTPException(status_code=404, detail="from_node not found")
    if not to_node:
        raise HTTPException(status_code=404, detail="to_node not found")

    # Validate same story
    if from_node.story_id != to_node.story_id:
        raise HTTPException(
            status_code=400,
            detail="Both nodes must belong to the same story"
        )

    # Validate same version
    if from_node.story_version != to_node.story_version:
        raise HTTPException(
            status_code=400,
            detail="Both nodes must belong to the same story version"
        )

    # Validate from_node is not an end node
    if from_node.is_end_node:
        raise HTTPException(
            status_code=400,
            detail="Cannot create choices from an end node"
        )

    # Check ownership
    story = session.get(Story, from_node.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if not current_user.is_superuser and story.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Create choice
    choice = NodeChoice.model_validate(choice_in)
    session.add(choice)
    session.commit()
    session.refresh(choice)

    return choice

@router.put("/{choice_id}", response_model=NodeChoicePublic)
def update_node_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    choice_id: uuid.UUID,
    choice_in: NodeChoiceUpdate
) -> Any:
    """
    Update a node choice.

    Validates:
    - Choice exists
    - User owns the story
    - If updating to_node_id, new node is valid
    - Choice belongs to current_version (not published_version)
    """
    choice = session.get(NodeChoice, choice_id)
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")

    # Get from_node to find story
    from_node = session.get(StoryNode, choice.from_node_id)
    if not from_node:
        raise HTTPException(status_code=500, detail="from_node not found (data corruption)")

    story = session.get(Story, from_node.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    if not current_user.is_superuser and story.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Prevent editing published version
    if from_node.story_version == story.published_version:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify choices in published version. Create new version first."
        )

    # If updating to_node_id, validate new node
    if choice_in.to_node_id is not None:
        new_to_node = session.get(StoryNode, choice_in.to_node_id)
        if not new_to_node:
            raise HTTPException(status_code=404, detail="New to_node not found")

        if new_to_node.story_id != from_node.story_id:
            raise HTTPException(
                status_code=400,
                detail="New to_node must belong to same story"
            )

        if new_to_node.story_version != from_node.story_version:
            raise HTTPException(
                status_code=400,
                detail="New to_node must belong to same version"
            )

    # Update choice
    update_dict = choice_in.model_dump(exclude_unset=True)
    choice.sqlmodel_update(update_dict)
    session.add(choice)
    session.commit()
    session.refresh(choice)

    return choice
@router.delete("/{choice_id}")
def delete_node_choice(
    session: SessionDep,
    current_user: CurrentUser,
    choice_id: uuid.UUID
) -> Message:
    """
    Delete a node choice.

    Validates:
    - Choice exists
    - User owns the story
    - Choice belongs to current_version (not published_version)

    Warning: This will not cascade delete UserNodeChoice records.
    Players who made this choice will have orphaned history.
    """
    choice = session.get(NodeChoice, choice_id)
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")

    # Get from_node to find story
    from_node = session.get(StoryNode, choice.from_node_id)
    if not from_node:
        raise HTTPException(status_code=500, detail="from_node not found")

    story = session.get(Story, from_node.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    if not current_user.is_superuser and story.owner_id != current_user.id:
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Prevent deleting from published version
    if from_node.story_version == story.published_version:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete choices in published version. Create new version first."
        )

    # Check if any players have made this choice (warning only)
    user_choice_count = session.exec(
        select(func.count()).select_from(UserNodeChoice).where(
            UserNodeChoice.choice_text == choice.text,
            UserNodeChoice.from_node_id == choice.from_node_id,
            UserNodeChoice.to_node_id == choice.to_node_id
        )
    ).one()

    if user_choice_count > 0:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"Deleting choice {choice_id} that has {user_choice_count} player history records. "
            f"Player history will be orphaned."
        )

    session.delete(choice)
    session.commit()

    return Message(message="Choice deleted successfully")



