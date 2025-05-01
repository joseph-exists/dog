import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    StoryNode,
    StoryNodeCreate,
    StoryNodePublic,
    StoryNodesPublic,
    StoryNodeUpdate,
    Message,
)

router = APIRouter(prefix="/storynodes", tags=["storynodes"])


@router.get("/", response_model=StoryNodesPublic)
def read_storynodes(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve storynodes.
    """

    count_statement = select(func.count()).select_from(StoryNode)
    count = session.exec(count_statement).one()
    statement = select(StoryNode).offset(skip).limit(limit)
    storynodes = session.exec(statement).all()

    return StoryNodesPublic(data=storynodes, count=count)  # type: ignore


@router.get("/{id}", response_model=StoryNodePublic)
def read_storynode(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get storynode by ID.
    """
    storynode = session.get(StoryNode, id)
    if not storynode:
        raise HTTPException(status_code=404, detail="storynode not found")
    return storynode


@router.post("/", response_model=StoryNodePublic)
def create_storynode(
    *, session: SessionDep, current_user: CurrentUser, storynode_in: StoryNodeCreate
) -> Any:
    """
    Create new storynode.
    """
    # Generate storynode_title from title
    storynode_title = storynode_in.title.lower().replace(" ", "_")[:50]

    storynode = StoryNode.model_validate(
        storynode_in, update={"enabled": True, "storynode_title": storynode_title}
    )
    session.add(storynode)
    session.commit()
    session.refresh(storynode)
    return storynode


@router.put("/{id}", response_model=StoryNodePublic)
def update_storynode(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    storynode_in: StoryNodeUpdate,
) -> Any:
    """
    Update an storynode.
    """
    storynode = session.get(StoryNode, id)
    if not storynode:
        raise HTTPException(status_code=404, detail="StoryNode not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = storynode_in.model_dump(exclude_unset=True)
    storynode.sqlmodel_update(update_dict)
    session.add(storynode)
    session.commit()
    session.refresh(storynode)
    return storynode


@router.delete("/{id}")
def delete_storynode(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an storynode.
    """
    storynode = session.get(StoryNode, id)
    if not storynode:
        raise HTTPException(status_code=404, detail="storynode not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(storynode)
    session.commit()
    return Message(message="StoryNode deleted successfully")
