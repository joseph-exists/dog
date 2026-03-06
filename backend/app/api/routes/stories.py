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

Story Requirement Routes - Access Gating CRUD

Handles creating and managing story access requirements.
Requirements gate which UserPersonas can start a story.

Endpoints:
- GET /stories/{story_id}/requirements - List story requirements
- POST /stories/{story_id}/requirements - Create requirement
- DELETE /stories/{story_id}/requirements/{requirement_id} - Delete requirement

Note: these are story requirements, not node requirements.
Note: No update endpoint - requirements are create/delete only


"""

import uuid
import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlalchemy import or_, union
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.services.access_control_sync import has_access_sync
from app.services.shadow_exporters import build_story_snapshot
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)
from app.models import (
    AccessGrant,
    AccessGrantRole,
    AccessGrantSubjectType,
    Message,
    NodeChoice,
    Quality,
    StateSchemaValidationResult,
    StoriesPublic,
    Story,
    StoryCreate,
    StoryNode,
    StoryNodePublic,
    StoryNodeTree,
    StoryNodeTreeNode,
    StoryPublic,
    StoryRequirement,
    StoryRequirementBase,
    StoryRequirementPublic,
    StoryRequirementsPublic,
    StoryStateVariable,
    StoryStateVariableBase,
    StoryStateVariableCreate,
    StoryStateVariablePublic,
    StoryStateVariablesPublic,
    StoryStateVariableUpdate,
    StoryUpdate,
    StoryValidationResult,
    Trait,
    User,
    UserGroupMembership,
)

router = APIRouter(prefix="/stories", tags=["stories"])


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
        count_statement = (
            select(func.count())
            .select_from(Story)
            .where(Story.deleted_at == None)  # noqa: E711
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Story)
            .where(Story.deleted_at == None)  # noqa: E711
            .offset(skip)
            .limit(limit)
        )
        stories = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(Story)
            .where(Story.owner_id == current_user.id)
            .where(Story.deleted_at == None)  # noqa: E711
        )
        count = session.exec(count_statement).one()
        statement = (
            select(Story)
            .where(Story.owner_id == current_user.id)
            .where(Story.deleted_at == None)  # noqa: E711
            .offset(skip)
            .limit(limit)
        )
        stories = session.exec(statement).all()
        # Include stories shared to the user (directly or via groups).
        direct_ids_stmt = select(AccessGrant.resource_id.label("resource_id")).where(
            AccessGrant.resource_type == "story",
            AccessGrant.subject_type == AccessGrantSubjectType.user,
            AccessGrant.subject_id == current_user.id,
        )
        group_ids_subq = select(UserGroupMembership.group_id).where(
            UserGroupMembership.user_id == current_user.id
        )
        group_ids_stmt = select(AccessGrant.resource_id.label("resource_id")).where(
            AccessGrant.resource_type == "story",
            AccessGrant.subject_type == AccessGrantSubjectType.group,
            AccessGrant.subject_id.in_(group_ids_subq),
        )
        shared_ids_subq = union(direct_ids_stmt, group_ids_stmt).subquery()

        shared_count_statement = (
            select(func.count())
            .select_from(Story)
            .where(Story.id.in_(select(shared_ids_subq.c.resource_id)))
            .where(Story.deleted_at == None)  # noqa: E711
        )
        shared_count = session.exec(shared_count_statement).one()
        shared_statement = (
            select(Story)
            .where(Story.id.in_(select(shared_ids_subq.c.resource_id)))
            .where(Story.deleted_at == None)  # noqa: E711
            .offset(skip)
            .limit(limit)
        )
        shared_stories = session.exec(shared_statement).all()

        # De-dupe by id while preserving order (owned first).
        by_id: dict[uuid.UUID, Story] = {s.id: s for s in stories}
        for s in shared_stories:
            by_id.setdefault(s.id, s)
        stories = list(by_id.values())
        count = int(count) + int(shared_count)

    return StoriesPublic(data=stories, count=count)  # type: ignore


@router.get("/{id}", response_model=StoryPublic)
def read_story(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Retrieve a story by ID.

    Users can only access their own stories unless they are superusers.
    """
    story = session.get(Story, id)
    if not story or story.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Story not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=id,
        minimum_role=AccessGrantRole.viewer,
    )
    return story


# ============================================================================
# Story Validation Endpoint (Task 2)
# ============================================================================


def _build_node_graph(choices: list[NodeChoice]) -> dict[uuid.UUID, list[uuid.UUID]]:
    """Build adjacency list: node_id -> list of destination node_ids."""
    graph: dict[uuid.UUID, list[uuid.UUID]] = {}
    for choice in choices:
        if choice.from_node_id not in graph:
            graph[choice.from_node_id] = []
        graph[choice.from_node_id].append(choice.to_node_id)
    return graph


def _find_reachable_nodes(
    start_node_id: uuid.UUID,
    graph: dict[uuid.UUID, list[uuid.UUID]],
) -> set[uuid.UUID]:
    """Find all nodes reachable from start using BFS."""
    visited: set[uuid.UUID] = set()
    queue = [start_node_id]

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        for dest_id in graph.get(current, []):
            if dest_id not in visited:
                queue.append(dest_id)

    return visited


@router.post("/{id}/validate", response_model=StoryValidationResult)
def validate_story(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    version: int | None = None,
    include_state_schema: bool = True,
) -> Any:
    """
    Validate a story's graph structure for publishing.

    Checks:
    1. At least one node exists
    2. Exactly one start node
    3. At least one end node
    4. All choices point to valid nodes in same version
    5. All non-end nodes have outgoing choices (warning)
    6. All nodes are reachable from start (warning)
    7. State schema validation (optional, included by default)

    Args:
        id: Story UUID
        version: Version to validate (defaults to current_version)
        include_state_schema: Whether to include state schema validation

    Returns:
        StoryValidationResult with errors, warnings, and statistics
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=id,
        minimum_role=AccessGrantRole.editor,
    )

    # Use specified version or default to current_version
    target_version = version if version is not None else story.current_version

    # Get all nodes for this version
    nodes_statement = select(StoryNode).where(
        StoryNode.story_id == id,
        StoryNode.story_version == target_version,
    )
    nodes = list(session.exec(nodes_statement).all())
    node_ids = {n.id for n in nodes}
    node_map = {n.id: n for n in nodes}

    # Get all choices from these nodes
    if node_ids:
        choices_statement = select(NodeChoice).where(
            NodeChoice.from_node_id.in_(node_ids)
        )
        choices = list(session.exec(choices_statement).all())
    else:
        choices = []

    errors: list[str] = []
    warnings: list[str] = []

    # Check 1: Must have at least one node
    if len(nodes) == 0:
        errors.append("Story must have at least one node")
        return StoryValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            node_count=0,
            choice_count=0,
            start_node_count=0,
            end_node_count=0,
            orphaned_node_count=0,
            state_schema_validation=None,
        )

    # Check 2: Must have exactly one start node
    start_nodes = [n for n in nodes if n.is_start_node]
    if len(start_nodes) == 0:
        errors.append("Story must have exactly one start node")
    elif len(start_nodes) > 1:
        errors.append(
            f"Story has {len(start_nodes)} start nodes, but must have exactly one"
        )

    # Check 3: Must have at least one end node
    end_nodes = [n for n in nodes if n.is_end_node]
    if len(end_nodes) == 0:
        errors.append("Story must have at least one end node")

    # Check 4: All choices must point to valid nodes in same version
    for choice in choices:
        if choice.to_node_id not in node_ids:
            from_node = node_map.get(choice.from_node_id)
            from_title = from_node.title if from_node else "Unknown"
            errors.append(
                f'Choice "{choice.text}" from node "{from_title}" '
                f"points to non-existent or wrong-version node"
            )

    # If we have blocking errors, calculate stats and return early
    if errors:
        state_validation = None
        if include_state_schema:
            state_validation = crud.get_undefined_variables_in_choices(
                session=session, story_id=id, story_version=target_version
            )
        return StoryValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings,
            node_count=len(nodes),
            choice_count=len(choices),
            start_node_count=len(start_nodes),
            end_node_count=len(end_nodes),
            orphaned_node_count=0,
            state_schema_validation=state_validation,
        )

    # Check 5 & 6: Reachability analysis (warnings only)
    start_node = start_nodes[0]
    graph = _build_node_graph(choices)
    reachable_nodes = _find_reachable_nodes(start_node.id, graph)

    # Find orphaned nodes
    orphaned_nodes = [n for n in nodes if n.id not in reachable_nodes]
    if orphaned_nodes:
        orphan_titles = ", ".join(f'"{n.title}"' for n in orphaned_nodes[:5])
        if len(orphaned_nodes) > 5:
            orphan_titles += f" and {len(orphaned_nodes) - 5} more"
        warnings.append(
            f"{len(orphaned_nodes)} orphan node(s) not reachable from start: {orphan_titles}"
        )

    # Check for dead-end nodes (non-end nodes with no outgoing choices)
    non_end_nodes = [n for n in nodes if not n.is_end_node]
    for node in non_end_nodes:
        outgoing = [c for c in choices if c.from_node_id == node.id]
        if not outgoing:
            warnings.append(f'Node "{node.title}" has no outgoing choices (dead end)')

    # State schema validation (optional)
    state_validation = None
    if include_state_schema:
        state_validation = crud.get_undefined_variables_in_choices(
            session=session, story_id=id, story_version=target_version
        )

    return StoryValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        node_count=len(nodes),
        choice_count=len(choices),
        start_node_count=len(start_nodes),
        end_node_count=len(end_nodes),
        orphaned_node_count=len(orphaned_nodes),
        state_schema_validation=state_validation,
    )


# ============================================================================
# Story Tree Structure Endpoint (Task 6)
# ============================================================================


def _build_story_tree(
    nodes: list[StoryNode],
    choices: list[NodeChoice],
) -> StoryNodeTree:
    """Build a hierarchical tree structure from nodes and choices."""
    if not nodes:
        return StoryNodeTree(
            root=None,
            orphaned_nodes=[],
            total_nodes=0,
            reachable_nodes=0,
        )

    # Find start node
    start_node = next((n for n in nodes if n.is_start_node), None)
    if not start_node:
        # No start node - all nodes are orphaned
        orphaned = [
            StoryNodeTreeNode(
                id=n.id,
                title=n.title,
                is_start_node=n.is_start_node,
                is_end_node=n.is_end_node,
                level=0,
                children=[],
            )
            for n in nodes
        ]
        return StoryNodeTree(
            root=None,
            orphaned_nodes=orphaned,
            total_nodes=len(nodes),
            reachable_nodes=0,
        )

    # Build adjacency map: node_id -> choices sorted by order
    adjacency_map: dict[uuid.UUID, list[NodeChoice]] = {}
    for choice in choices:
        if choice.from_node_id not in adjacency_map:
            adjacency_map[choice.from_node_id] = []
        adjacency_map[choice.from_node_id].append(choice)

    # Sort choices by order
    for choice_list in adjacency_map.values():
        choice_list.sort(key=lambda c: c.order if c.order is not None else 0)

    node_map = {n.id: n for n in nodes}
    visited: set[uuid.UUID] = set()

    def build_subtree(node: StoryNode, level: int) -> StoryNodeTreeNode:
        visited.add(node.id)
        children: list[StoryNodeTreeNode] = []

        for choice in adjacency_map.get(node.id, []):
            if choice.to_node_id not in visited:
                child_node = node_map.get(choice.to_node_id)
                if child_node:
                    children.append(build_subtree(child_node, level + 1))

        return StoryNodeTreeNode(
            id=node.id,
            title=node.title,
            is_start_node=node.is_start_node,
            is_end_node=node.is_end_node,
            level=level,
            children=children,
        )

    root = build_subtree(start_node, 0)

    # Find orphaned nodes (not visited during tree building)
    orphaned = [
        StoryNodeTreeNode(
            id=n.id,
            title=n.title,
            is_start_node=n.is_start_node,
            is_end_node=n.is_end_node,
            level=0,
            children=[],
        )
        for n in nodes
        if n.id not in visited
    ]

    return StoryNodeTree(
        root=root,
        orphaned_nodes=orphaned,
        total_nodes=len(nodes),
        reachable_nodes=len(visited),
    )


@router.get("/{id}/tree", response_model=StoryNodeTree)
def get_story_tree(
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    version: int | None = None,
) -> Any:
    """
    Get the pre-computed tree structure for a story version.

    Returns a hierarchical tree starting from the start node, with
    orphaned nodes listed separately.

    Args:
        id: Story UUID
        version: Version to get tree for (defaults to current_version)

    Returns:
        StoryNodeTree with root node and orphaned nodes
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=id,
        minimum_role=AccessGrantRole.viewer,
    )

    # Use specified version or default to current_version
    target_version = version if version is not None else story.current_version

    # Get all nodes for this version
    nodes_statement = select(StoryNode).where(
        StoryNode.story_id == id,
        StoryNode.story_version == target_version,
    )
    nodes = list(session.exec(nodes_statement).all())
    node_ids = {n.id for n in nodes}

    # Get all choices from these nodes
    if node_ids:
        choices_statement = select(NodeChoice).where(
            NodeChoice.from_node_id.in_(node_ids)
        )
        choices = list(session.exec(choices_statement).all())
    else:
        choices = []

    return _build_story_tree(nodes, choices)


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
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=id,
        minimum_role=AccessGrantRole.viewer,
    )

    # Find the start node for the current version
    statement = select(StoryNode).where(
        StoryNode.story_id == id,
        StoryNode.story_version == story.current_version,
        StoryNode.is_start_node is True,
    )
    start_node = session.exec(statement).first()

    if not start_node:
        raise HTTPException(
            status_code=404,
            detail=f"No start node found for story version {story.current_version}",
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

    # Shadow versioning (non-blocking - skips if user not set up)
    try:
        snapshot = build_story_snapshot(session=session, story_id=story.id)
        version = shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="story",
            entity_id=story.id,
            entity_data=snapshot,
            message=f"Create story: {story.title}",
        )
        if version:
            logger.info(f"Shadow version {version.version_number} enqueued for story {story.title}")
    except Exception as e:
        logger.warning(f"Shadow versioning failed for story {story.title}: {e}")

    return story


@router.put("/{id}", response_model=StoryPublic)
def update_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    story_in: StoryUpdate,
) -> Any:
    """
    Update a story by ID.

    Only the story owner or superusers can update a story.
    This updates the story metadata but not its version.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=id,
        minimum_role=AccessGrantRole.editor,
    )

    update_dict = story_in.model_dump(exclude_unset=True)
    story.sqlmodel_update(update_dict)
    session.add(story)
    session.commit()
    session.refresh(story)

    # Shadow versioning (non-blocking - skips if user not set up)
    try:
        snapshot = build_story_snapshot(session=session, story_id=story.id)
        version = shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="story",
            entity_id=story.id,
            entity_data=snapshot,
            message=f"Update story: {story.title}",
        )
        if version:
            logger.info(f"Shadow version {version.version_number} enqueued for story {story.title}")
    except Exception as e:
        logger.warning(f"Shadow versioning failed for story {story.title}: {e}")

    return story


@router.put("/{id}/publish", response_model=StoryPublic)
def publish_story(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    force: bool = False,
) -> Any:
    """
    Publish a story by ID.

    Only the story owner or superusers can publish a story.
    This locks the current_version as published_version and sets is_published=True.
    Players will be locked to this published_version when they start the story.

    State schema validation is performed before publishing. If there are undefined
    variables in requires_state/sets_state, a 422 error is returned unless force=True.
    """
    story = session.get(Story, id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    # Validate state schema (soft block unless force=True)
    if not force:
        validation = crud.get_undefined_variables_in_choices(
            session=session, story_id=id, story_version=story.current_version
        )

        if not validation.is_valid:
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "Story has undefined state variables",
                    "undefined_variables": validation.undefined_variables,
                    "error_count": len(validation.errors),
                    "hint": "Define these variables in the state schema or use force=true to publish anyway",
                },
            )

    # Lock current_version as published_version
    story.published_version = story.current_version
    story.is_published = True
    session.add(story)
    session.commit()
    session.refresh(story)
    return story


@router.put("/{id}/unpublish", response_model=StoryPublic)
def unpublish_story(
    *, session: SessionDep, current_user: CurrentUser, id: uuid.UUID
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
    *, session: SessionDep, current_user: CurrentUser, id: uuid.UUID
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
            detail="Cannot create new version - story has never been published",
        )

    # Increment current_version
    new_version = story.current_version + 1
    story.current_version = new_version

    # Copy all nodes from published_version to new current_version
    # Get all nodes from published version
    published_nodes_statement = select(StoryNode).where(
        StoryNode.story_id == id, StoryNode.story_version == story.published_version
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
            },
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
            },
        )
        session.add(new_choice)

    # Copy all state variables from published_version to new current_version
    state_vars_statement = select(StoryStateVariable).where(
        StoryStateVariable.story_id == id,
        StoryStateVariable.story_version == story.published_version,
    )
    published_vars = session.exec(state_vars_statement).all()

    for var in published_vars:
        new_var = StoryStateVariable.model_validate(
            var,
            update={
                "id": uuid.uuid4(),  # New UUID for the copy
                "story_version": new_version,  # New version
            },
        )
        session.add(new_var)

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
    if not story or story.deleted_at is not None:
        raise HTTPException(status_code=404, detail="Story not found")
    if not current_user.is_superuser and (story.owner_id != current_user.id):
        raise HTTPException(status_code=400, detail="Not enough permissions")

    from app.crud import delete_story as crud_delete_story

    return crud_delete_story(session=session, story_id=id)


@router.get("/{story_id}/requirements", response_model=StoryRequirementsPublic)
def read_story_requirements(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve story requirements.

    Requirements gate which UserPersonas can start this story.
    Public endpoint (anyone can see requirements).
    """
    # Verify story exists
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Count total
    count_query = (
        select(func.count())
        .select_from(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
    )
    count = session.exec(count_query).one()

    # Get requirements
    query = (
        select(StoryRequirement)
        .where(StoryRequirement.story_id == story_id)
        .offset(skip)
        .limit(limit)
    )

    requirements = session.exec(query).all()

    return StoryRequirementsPublic(data=requirements, count=count)


@router.post("/{story_id}/requirements", response_model=StoryRequirementPublic)
def create_story_requirement(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    requirement_in: StoryRequirementBase,  # Uses base, not create (no story_id)
) -> Any:
    """
    Create story requirement.

    Validates:
    - Story exists
    - User owns story
    - No duplicate requirements
    - requirement_type is valid
    """
    # Verify story exists
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    # Validate requirement_type
    # TODO this should be an enum on the model not here
    valid_types = ["quality", "trait", "archetype", "level"]
    if requirement_in.requirement_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid requirement_type. Must be one of: {valid_types}",
        )

    # Check for duplicate
    existing = session.exec(
        select(StoryRequirement).where(
            StoryRequirement.story_id == story_id,
            StoryRequirement.requirement_type == requirement_in.requirement_type,
            StoryRequirement.target_id == requirement_in.target_id,
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=400, detail="Requirement already exists for this story"
        )

    # Soft validation: warn if target doesn't exist (don't fail)
    if requirement_in.requirement_type == "quality":
        target = session.get(Quality, requirement_in.target_id)
        if not target:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Creating requirement for non-existent quality: {requirement_in.target_id}"
            )
    elif requirement_in.requirement_type == "trait":
        target = session.get(Trait, requirement_in.target_id)
        if not target:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Creating requirement for non-existent trait: {requirement_in.target_id}"
            )

    # Create requirement
    requirement = StoryRequirement(
        story_id=story_id,
        requirement_type=requirement_in.requirement_type,
        target_id=requirement_in.target_id,
        description=requirement_in.description,
    )

    session.add(requirement)
    session.commit()
    session.refresh(requirement)

    try:
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        owner = session.get(User, story.owner_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story requirement created: {requirement.id}",
            )
    except Exception:
        pass

    return requirement


@router.delete("/{story_id}/requirements/{requirement_id}")
def delete_story_requirement(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    requirement_id: uuid.UUID,
) -> Message:
    """
    Delete story requirement.

    Validates:
    - Requirement exists
    - Requirement belongs to this story
    - User owns story
    """
    # Get requirement
    requirement = session.get(StoryRequirement, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")

    # Verify belongs to story
    if requirement.story_id != story_id:
        raise HTTPException(
            status_code=400, detail="Requirement does not belong to this story"
        )

    # Get story for ownership check
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    session.delete(requirement)
    session.commit()

    try:
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        owner = session.get(User, story.owner_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story requirement deleted: {requirement_id}",
            )
    except Exception:
        pass

    return Message(message="Requirement deleted successfully")


# ============================================================================
# State Schema Routes - Story State Variable CRUD
# ============================================================================


@router.get(
    "/{story_id}/versions/{version}/state-schema",
    response_model=StoryStateVariablesPublic,
)
def read_story_state_schema(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    version: int,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Get all state variables for a story version.

    Any authenticated user can read the state schema.
    This enables players to understand the game mechanics.
    """
    # Verify story exists
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    variables, count = crud.get_story_state_variables(
        session=session,
        story_id=story_id,
        story_version=version,
        skip=skip,
        limit=limit,
    )

    return StoryStateVariablesPublic(data=variables, count=count)


@router.post(
    "/{story_id}/versions/{version}/state-schema",
    response_model=StoryStateVariablePublic,
)
def create_story_state_variable(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    version: int,
    variable_in: StoryStateVariableBase,
) -> Any:
    """
    Create a state variable in the schema.

    Only story owner or superuser can create variables.
    Cannot modify published_version - must create new version first.
    """
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    # Prevent editing published version
    if version == story.published_version:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify state schema in published version. Create a new version first.",
        )

    # Check for duplicate key
    existing_vars, _ = crud.get_story_state_variables(
        session=session, story_id=story_id, story_version=version, limit=1000
    )
    if any(v.key == variable_in.key for v in existing_vars):
        raise HTTPException(
            status_code=400, detail=f"Variable '{variable_in.key}' already exists"
        )

    # Create the variable
    create_data = StoryStateVariableCreate(
        story_id=story_id,
        story_version=version,
        **variable_in.model_dump(),
    )

    try:
        variable = crud.create_story_state_variable(
            session=session, variable_in=create_data
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        owner = session.get(User, story.owner_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story state variable created: {variable.id}",
            )
    except Exception:
        pass

    return variable


@router.put(
    "/{story_id}/versions/{version}/state-schema/{variable_id}",
    response_model=StoryStateVariablePublic,
)
def update_story_state_variable(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    version: int,
    variable_id: uuid.UUID,
    variable_in: StoryStateVariableUpdate,
) -> Any:
    """
    Update a state variable.

    Only story owner or superuser can update variables.
    Cannot modify published_version.
    """
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    # Prevent editing published version
    if version == story.published_version:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify state schema in published version. Create a new version first.",
        )

    # Verify variable exists and belongs to this story/version
    variable = session.get(StoryStateVariable, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    if variable.story_id != story_id or variable.story_version != version:
        raise HTTPException(
            status_code=400,
            detail="Variable does not belong to this story version",
        )

    # Check for duplicate key if key is being changed
    if variable_in.key is not None and variable_in.key != variable.key:
        existing_vars, _ = crud.get_story_state_variables(
            session=session, story_id=story_id, story_version=version, limit=1000
        )
        if any(v.key == variable_in.key and v.id != variable_id for v in existing_vars):
            raise HTTPException(
                status_code=400, detail=f"Variable '{variable_in.key}' already exists"
            )

    try:
        updated = crud.update_story_state_variable(
            session=session, variable_id=variable_id, variable_in=variable_in
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        owner = session.get(User, story.owner_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story state variable updated: {variable_id}",
            )
    except Exception:
        pass

    return updated


@router.delete("/{story_id}/versions/{version}/state-schema/{variable_id}")
def delete_story_state_variable(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    version: int,
    variable_id: uuid.UUID,
) -> Message:
    """
    Delete a state variable from the schema.

    Only story owner or superuser can delete variables.
    Cannot modify published_version.
    """
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    # Prevent editing published version
    if version == story.published_version:
        raise HTTPException(
            status_code=400,
            detail="Cannot modify state schema in published version. Create a new version first.",
        )

    # Verify variable exists and belongs to this story/version
    variable = session.get(StoryStateVariable, variable_id)
    if not variable:
        raise HTTPException(status_code=404, detail="Variable not found")
    if variable.story_id != story_id or variable.story_version != version:
        raise HTTPException(
            status_code=400,
            detail="Variable does not belong to this story version",
        )

    try:
        crud.delete_story_state_variable(session=session, variable_id=variable_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        snapshot = build_story_snapshot(session=session, story_id=story_id)
        owner = session.get(User, story.owner_id)
        if owner:
            shadow_service.enqueue_entity_version_with_owner(
                session=session,
                owner=owner,
                actor=current_user,
                entity_type="story",
                entity_id=story_id,
                entity_data=snapshot,
                message=f"Story state variable deleted: {variable_id}",
            )
    except Exception:
        pass

    return Message(message="Variable deleted successfully")


@router.get(
    "/{story_id}/versions/{version}/state-schema/validate",
    response_model=StateSchemaValidationResult,
)
def validate_story_state_schema(
    session: SessionDep,
    current_user: CurrentUser,
    story_id: uuid.UUID,
    version: int,
) -> Any:
    """
    Validate all choices against the state schema.

    Returns undefined variables used in requires_state/sets_state.
    Only story owner or superuser can run validation.
    """
    story = session.get(Story, story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # Check ownership
    _require_story_role(
        session=session,
        current_user=current_user,
        story_id=story_id,
        minimum_role=AccessGrantRole.editor,
    )

    return crud.get_undefined_variables_in_choices(
        session=session, story_id=story_id, story_version=version
    )
