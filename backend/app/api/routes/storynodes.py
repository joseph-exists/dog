import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.services.access_control_sync import has_access_sync
from app.services.shadow_exporters import build_story_snapshot
from app.services.shadow_service import shadow_service
from app.models import (
    AccessGrantRole,
    Message,
    NodeChoice,
    NodeChoiceBase,
    NodeChoiceCreate,
    NodeChoicePublic,
    NodeChoicesPublic,
    Story,
    StoryNode,
    StoryNodeCreate,
    StoryNodePublic,
    StoryNodesPublic,
    StoryNodeUpdate,
    User,
)

router = APIRouter(prefix="/storynodes", tags=["storynodes"])

def _require_story_role(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    minimum_role: AccessGrantRole,
) -> None:
    if not has_access_sync(
        session,
        user=current_user,
        resource_type="story",
        resource_id=story_id,
        minimum_role=minimum_role,
    ):
        raise HTTPException(status_code=400, detail="Not enough permissions")


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
    story = session.get(Story, storynode_in.story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story.id,
        minimum_role=AccessGrantRole.editor,
    )

    # Generate storynode_title from title
    storynode_title = storynode_in.title.lower().replace(" ", "_")[:50]

    storynode = StoryNode.model_validate(
        storynode_in, update={"enabled": True, "storynode_title": storynode_title}
    )
    session.add(storynode)
    session.commit()
    session.refresh(storynode)
    try:
        story = session.get(Story, storynode.story_id)
        owner = session.get(User, story.owner_id) if story else None
        snapshot = build_story_snapshot(session=session, story_id=storynode.story_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=storynode.story_id,
                entity_data=snapshot,
                message=f"Story node created: {storynode.title}",
            )
    except Exception:
        pass
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
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=storynode.story_id,
        minimum_role=AccessGrantRole.editor,
    )
    update_dict = storynode_in.model_dump(exclude_unset=True)
    storynode.sqlmodel_update(update_dict)
    session.add(storynode)
    session.commit()
    session.refresh(storynode)
    try:
        story = session.get(Story, storynode.story_id)
        owner = session.get(User, story.owner_id) if story else None
        snapshot = build_story_snapshot(session=session, story_id=storynode.story_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=storynode.story_id,
                entity_data=snapshot,
                message=f"Story node updated: {storynode.title}",
            )
    except Exception:
        pass
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
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=storynode.story_id,
        minimum_role=AccessGrantRole.editor,
    )
    story_id = storynode.story_id
    session.delete(storynode)
    session.commit()
    try:
        story = session.get(Story, story_id)
        owner = session.get(User, story.owner_id) if story else None
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story node deleted: {id}",
            )
    except Exception:
        pass
    return Message(message="StoryNode deleted successfully")

@router.get("/{node_id}/choices", response_model=NodeChoicesPublic)
def read_node_choices(
    session: SessionDep,
    current_user: CurrentUser,
    node_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Any:
    """
    Get all choices originating from this node.

    Convenience endpoint for: GET /node-choices?from_node_id={node_id}
    """
    # Verify node exists
    node = session.get(StoryNode, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=node.story_id,
        minimum_role=AccessGrantRole.viewer,
    )

    # Get choices
    count_query = select(func.count()).select_from(NodeChoice).where(
        NodeChoice.from_node_id == node_id
    )
    count = session.exec(count_query).one()

    query = select(NodeChoice).where(
        NodeChoice.from_node_id == node_id
    ).order_by(NodeChoice.order).offset(skip).limit(limit)

    choices = session.exec(query).all()

    return NodeChoicesPublic(data=choices, count=count)

@router.post("/{node_id}/choices", response_model=NodeChoicePublic)
def create_node_choice_from_node(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    node_id: uuid.UUID,
    choice_in: NodeChoiceBase  # Uses base, not create (no from_node_id)
) -> Any:
    """
    Create choice from this node.

    Convenience endpoint that automatically sets from_node_id.
    """
    # Verify node exists
    from_node = session.get(StoryNode, node_id)
    if not from_node:
        raise HTTPException(status_code=404, detail="Node not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=from_node.story_id,
        minimum_role=AccessGrantRole.editor,
    )

    # Create full choice object with from_node_id
    choice_create = NodeChoiceCreate(
        from_node_id=node_id,
        to_node_id=choice_in.to_node_id,
        text=choice_in.text,
        order=choice_in.order,
        requires_state=choice_in.requires_state,
        sets_state=choice_in.sets_state
    )

    # Reuse main create logic (call the function from node_choices.py)
    return create_node_choice(
        session=session,
        current_user=current_user,
        choice_in=choice_create
    )
