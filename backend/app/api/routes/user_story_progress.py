"""
User Story Progress Routes - Player Instance Operations

Handles playing concerns for user story instances.
Each UserStoryProgress represents a player's playthrough of a story,
locked to a specific story version at creation time.

Timeline Navigation
- Undo: Rewind one step (move head to parent)
- Jump: Rewind to arbitrary ancestor
- Timeline: Get breadcrumb trail (root → head)

Timeline Semantics:
- Active path: root → head (visible to player via timeline endpoint)
- Abandoned branches: sibling choices (hidden from player, retained in DB)
- Forward jumps: Prohibited (would expose hidden branches)
- Optimistic concurrency: Use head_version to prevent conflicts

Endpoints:
- GET /user-personas/{user_persona_id}/stories - List player's story instances
- GET /user-personas/{user_persona_id}/stories/{story_id} - Get specific instance
- POST /user-personas/{user_persona_id}/stories/{story_id} - Start new story instance
- GET /user-personas/{user_persona_id}/stories/{story_id}/current-node - Get current position
- POST /user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id} - Make a choice
- POST /user-personas/{user_persona_id}/stories/{story_id}/undo - Undo last choice (Phase 3)
- POST /user-personas/{user_persona_id}/stories/{story_id}/jump - Jump to ancestor (Phase 3)
- GET /user-personas/{user_persona_id}/stories/{story_id}/timeline - Get breadcrumb trail (Phase 3)
- PUT /user-personas/{user_persona_id}/stories/{story_id} - Update progress (admin/debug)
"""
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sqlmodel import select
from app.services.realtime_publisher import publish_event_to_redis
from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    JumpRequest,
    Timeline,
    TimelineEvent,
    UserStoryProgress,
    UserStoryProgressCreate,
    UserStoryProgressPublic,
    UserStoryProgressesPublic,
    UserStoryProgressUpdate,
    ProgressSnapshotsPublic,
    ProgressSnapshotPublic,
    ProgressSnapshot,
    Story,
    StoryNode,
    NodeChoice,
    UserNodeChoice,
    CurrentNodePublic,
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
    
    Returns all story instances (playthroughs) for this persona.
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
    
    Returns the player's instance of this story including version lock
    and current state.
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
    
    Creates a new UserStoryProgress locked to the story's current_version.
    Validates story requirements and finds the starting node.
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Check if the story exists
    story = session.get(Story, story_id)
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

    # Check if the story is published
    if not story.is_published:
        raise HTTPException(
            status_code=400,
            detail="Story is not published"
        )

    # Find the starting node of the story (for published version)
    statement = select(StoryNode).where(
        StoryNode.story_id == story_id,
        StoryNode.story_version == story.published_version,
        StoryNode.is_start_node == True  # noqa: E712
    )
    start_node = session.exec(statement).first()

    if not start_node:
        raise HTTPException(
            status_code=500,
            detail=f"No start node found for story version {story.current_version}"
        )


    # Create the progress locked to published version
    progress_in = UserStoryProgressCreate(
        user_persona_id=user_persona_id,
        story_id=story_id,
        story_version=story.published_version,  # Lock to current published version at time of creating the player story play
        current_node_id=start_node.id
    )

    progress = crud.create_user_story_progress(
        session=session, progress_in=progress_in
    )
    return progress


@router.get("/{story_id}/current-node", response_model=CurrentNodePublic)
def get_current_node(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get the current node and available choices for the user's story progress.
    
    Returns:
    - The current StoryNode
    - List of available NodeChoices (filtered by story state)
    - Current story state
    
    This endpoint helps players understand their current position and options.
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

    # Get available choices (filtered by story state)
    available_choices = crud.get_available_choices(
        session=session,
        node_id=progress.current_node_id,
        story_state=progress.story_state,
    )

    # Return the node and available choices
    return CurrentNodePublic(
        node=current_node,  # type: ignore
        available_choices=available_choices,  # type: ignore
        story_state=progress.story_state,
    )


@router.post("/{story_id}/choices/{choice_id}", response_model=UserStoryProgressPublic)
def make_story_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    choice_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Make a choice in the story and progress to the next node.
    
    Validates:
    - User owns the persona
    - Progress exists
    - Choice exists and belongs to current node
    - Choice requirements are met (via story state)
    
    Then:
    - Records the choice in UserNodeChoice
    - Updates story state with choice's state changes
    - Moves to the next node
    - Marks story as completed if reaching an end node
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

    # Get the choice
    choice = session.get(NodeChoice, choice_id)
    if not choice:
        raise HTTPException(status_code=404, detail="Choice not found")

    # Verify the choice belongs to the current node
    if choice.from_node_id != progress.current_node_id:
        raise HTTPException(
            status_code=400,
            detail="This choice is not available for the current node"
        )

    # Check if the choice's requirements are met
    available_choices = crud.get_available_choices(
        session=session,
        node_id=progress.current_node_id,
        story_state=progress.story_state,
    )
    
    if choice not in available_choices:
        raise HTTPException(
            status_code=403,
            detail="This choice's requirements are not met in your current story state"
        )

    # Create a record of the choice
    user_choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=progress.head_choice_id,
        choice_text=choice.text,
        from_node_id=choice.from_node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state,
        rng_data=None 
    )
    session.add(user_choice)
    session.flush() # get the id


    # Phase 5 - derive state from events (single source of truth)
    # Update head pointer (atomic move)
    progress.head_choice_id = user_choice.id
    progress.head_version += 1

    # FINAL: Always derive state from events (single source of truth)
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    progress.current_node_id = crud.get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Create snapshot if needed (every 10 choices)
    snapshot = crud.create_snapshot_if_needed(
        session=session,
        progress=progress,
        snapshot_interval=10
    )
    if snapshot:
        session.add(snapshot)

    session.commit()

    # Update the current node
    progress.current_node_id = choice.to_node_id

    # Check if this is an end node
    to_node = session.get(StoryNode, choice.to_node_id)
    if to_node and to_node.is_end_node:
        progress.is_completed = True

    session.add(progress)
    session.commit()
    session.refresh(progress)

    # Publish to Redis in background (non-blocking)
    background_tasks.add_task(
        publish_event_to_redis,
        channel=f"story:{progress.story_id}",
        event_type="choice.made",
        sequence=None,  # CYOA doesn't use sequences, uses parent pointers
        payload={
            "progress_id": str(progress.story_id),
            "user_persona_id": str(user_persona_id),
            "choice_id": str(user_choice.id),
            "choice_text": user_choice.choice_text,
            "head_version": progress.head_version,
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state,
            "is_completed": progress.is_completed,
        },
        created_at=user_choice.choice_time,
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
    
    This is primarily for admin/debugging purposes.
    Normal gameplay should use the make_story_choice endpoint.
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

@router.get("/{story_id}/validate-state", response_model=dict[str, Any])
def validate_story_state(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Validate that replayed state matches stored state.

    This is a Phase 2 diagnostic endpoint to verify replay logic correctness.
    In production, replayed state is the source of truth.

    Returns:
        {
            "stored_state": {...},
            "replayed_state": {...},
            "match": true/false,
            "differences": {...}
        }
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

    # Get stored state
    stored_state = progress.story_state or {}

    # Replay state from head
    replayed_state = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id,
    )

    # Compare
    match = stored_state == replayed_state

    # Find differences
    differences = {}
    all_keys = set(stored_state.keys()) | set(replayed_state.keys())
    for key in all_keys:
        stored_val = stored_state.get(key)
        replayed_val = replayed_state.get(key)
        if stored_val != replayed_val:
            differences[key] = {
                "stored": stored_val,
                "replayed": replayed_val,
            }

    return {
        "stored_state": stored_state,
        "replayed_state": replayed_state,
        "match": match,
        "differences": differences,
    }

@router.post("/{story_id}/undo", response_model=UserStoryProgressPublic)
def undo_story_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Move head to parent choice (rewind one step).

    Behavior:
    - Moves head_choice_id to parent of current head
    - Increments head_version (optimistic lock)
    - Replays state from new head
    - Old future remains in database but becomes hidden

    Errors:
        400: Already at story start, cannot undo
        404: User persona or story progress not found

    Returns:
        Updated progress with new head position

    Example:
        POST /api/v1/user-personas/{id}/stories/{story_id}/undo

        Response: UserStoryProgressPublic with head at parent choice
    """
    # Verify ownership
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Get progress
    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Check if at story start
    if progress.head_choice_id is None:
        raise HTTPException(
            status_code=400,
            detail="Already at story start, cannot undo"
        )

    # Get current choice to find parent
    current_choice = session.get(UserNodeChoice, progress.head_choice_id)
    if not current_choice:
        raise HTTPException(
            status_code=500,
            detail="Head choice not found (data corruptiton possible)"
        )

    # Save old head for event payload
    old_head_id = progress.head_choice_id
    old_node_id = progress.current_node_id

    # move head to parent (atomic update)
    progress.head_choice_id = current_choice.parent_choice_id
    progress.head_version += 1

    # OLD: Move head to parent using helper function
    # progress = crud.move_head_to_choice(
    #     session=session,
    #     progress=progress,
    #     target_choice_id=current_choice.parent_choice_id,
    # )

    # PHASE 5: Always derive state from events (single source of truth)
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Derive current node from new head
    progress.current_node_id = crud.get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Check if still completed (may no longer be at end node)
    if progress.current_node_id:
        current_node = session.get(StoryNode, progress.current_node_id)
        if current_node:
            progress.is_completed = current_node.is_end_node
        else:
            progress.is_completed = False
    else:
        progress.is_completed = False

    session.add(progress)
    session.commit()
    session.refresh(progress)

    # Publish HeadMoved event to Redis in background
    background_tasks.add_task(
        publish_event_to_redis,
        channel=f"story:{story_id}",
        event_type="head.moved",
        sequence=None,  # CYOA doesn't use sequences
        payload={
            "progress_id": str(progress.id),
            "user_persona_id": str(user_persona_id),
            "operation": "undo",
            "old_head_id": str(old_head_id) if old_head_id else None,
            "new_head_id": str(progress.head_choice_id) if progress.head_choice_id else None,
            "head_version": progress.head_version,
            "old_node_id": str(old_node_id),
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state,
            "is_completed": progress.is_completed,
        },
        created_at=datetime.utcnow(),
    )

    return progress

@router.post("/{story_id}/jump", response_model=UserStoryProgressPublic)
def jump_story_head(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    jump_request: JumpRequest,
    background_tasks: BackgroundTasks,
) -> Any:
    """
    Jump head to any ancestor choice (rewind to arbitrary point).
    - Uses optimized replay with snapshots for state derivation
    - Publishes real-time events to WebSocket clients
    - Enforces ancestor constraint (no forward jumps)


    Validation:
    - Target choice must be ancestor of current head (enforces no forward jumps)
    - Optimistic concurrency via expected_head_version
    - Target can be None (jump to story start)
    
    Behavior:
    - Moves head_choice_id to target
    - Replays state from target using nearest snapshot
    - All future choices after target become hidden
    - Increments head_version

    Errors:
        400: Target not ancestor, or other validation error
        404: User persona, story progress, or target choice not found
        409: Head version conflict (concurrent modification)

    Returns:
        Updated progress at new head position with replayed state

    Example:
        POST /api/v1/user-personas/{id}/stories/{story_id}/jump
        Body: {
            "choice_id": "uuid-of-ancestor", # or null for story start
            "expected_head_version": 5
        }

        Response: UserStoryProgressPublic with head at target choice
    """
    # Verify ownership
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Get progress
    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Optimistic concurrency check
    if jump_request.expected_head_version != progress.head_version:
        raise HTTPException(
            status_code=409,
            detail=f"Head version conflict: expected {jump_request.expected_head_version}, "
            f"got {progress.head_version}. Refetch progress and retry."
        )

    target_choice_id = jump_request.choice_id

    # Validate target is ancestor (if not jumping to start)
    if target_choice_id is not None:
        # Check target exists and belongs to this progress
        target_choice = session.get(UserNodeChoice, target_choice_id)
        if not target_choice or target_choice.progress_id != progress.id:
            raise HTTPException(
                status_code=404,
                detail="Target choice not found or doesn't belong to this progress"
            )

        # Verify target is ancestor of current head (prevents forward jumps)
        if progress.head_choice_id is not None:
            is_ancestor = crud.validate_ancestor_constraint(
                session=session,
                target_choice_id=target_choice_id,
                current_head_id=progress.head_choice_id,
            )

            if not is_ancestor:
                raise HTTPException(
                    status_code=400,
                    detail="Target choice is not an ancestor of current head "
                    "(forward jumps not allowed - would expose hidden branches)"
                )

    # Save old head for event payload
    old_head_id = progress.head_choice_id
    old_node_id = progress.current_node_id
    # Move head to target (atomic update)
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # PHASE 5: Always derive state from events (single source of truth)
    progress.story_state = crud.replay_state_from_head_optimized(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id
    )

    # Derive current node from new head
    progress.current_node_id = crud.get_current_node_from_head(
        session=session,
        head_choice_id=progress.head_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version
    )

    # Check if still completed (may no longer be at end node)
    if progress.current_node_id:
        current_node = session.get(StoryNode, progress.current_node_id)
        if current_node:
            progress.is_completed = current_node.is_end_node
        else:
            progress.is_completed = False
    else:
        progress.is_completed = False

    # ========== Database Commit ==========

    session.add(progress)
    session.commit()
    session.refresh(progress)


    # Publish HeadMoved event to Redis (non-blocking)
    background_tasks.add_task(
        publish_event_to_redis,
        channel=f"story:{story_id}",
        event_type="head.moved",
        sequence=None,  # CYOA doesn't use sequences
        payload={
            "progress_id": str(progress.id),
            "user_persona_id": str(user_persona_id),
            "operation": "jump",
            "old_head_id": str(old_head_id) if old_head_id else None,
            "new_head_id": str(progress.head_choice_id) if progress.head_choice_id else None,
            "target_choice_id": str(target_choice_id) if target_choice_id else None,
            "head_version": progress.head_version,
            "old_node_id": str(old_node_id),
            "new_node_id": str(progress.current_node_id),
            "new_state": progress.story_state,
            "is_completed": progress.is_completed,
        },
        created_at=datetime.utcnow(),
    )

    return progress

@router.get("/{story_id}/timeline", response_model=Timeline)
def read_story_timeline(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get active timeline (root → head) for breadcrumb UI.

    Returns ONLY the ancestor chain, never siblings or abandoned branches.
    This ensures abandoned branches remain hidden from the player.

    Response includes:
    - Story start event (choice_id=null)
    - All choices from root to current head
    - Current head_version for optimistic locking

    Returns:
        Timeline with events list and head_version

    Example:
        GET /api/v1/user-personas/{id}/stories/{story_id}/timeline

        Response: {
            "events": [
                {"choice_id": null, "choice_text": "Story Start", "is_current": false, ...},
                {"choice_id": "uuid-1", "choice_text": "Enter forest", "is_current": false, ...},
                {"choice_id": "uuid-2", "choice_text": "Find cave", "is_current": true, ...}
            ],
            "head_version": 3
        }
    """
    # Verify ownership
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    # Get progress
    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Get start node for story start event
    start_node = session.exec(
        select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == progress.story_version,
            StoryNode.is_start_node == True,  # noqa: E712
        )
    ).first()

    # Build timeline starting with story start
    events = [
        TimelineEvent(
            choice_id=None,
            choice_text="Story Start",
            node_title=start_node.title if start_node else "Unknown",
            choice_time=progress.started_at,
            is_current=(progress.head_choice_id is None),
        )
    ]

    # Add ancestor chain (root → head)
    # Uses Phase 2 get_choice_ancestor_chain to get only active path
    if progress.head_choice_id:
        chain = crud.get_choice_ancestor_chain(
            session=session, choice_id=progress.head_choice_id
        )

        for choice in chain:
            # Get the node this choice led to
            node = session.get(StoryNode, choice.to_node_id)

            events.append(
                TimelineEvent(
                    choice_id=choice.id,
                    choice_text=choice.choice_text,
                    node_title=node.title if node else "Unknown",
                    choice_time=choice.choice_time,
                    is_current=(choice.id == progress.head_choice_id),
                )
            )

    return Timeline(events=events, head_version=progress.head_version)
@router.get("/{story_id}/snapshots", response_model=ProgressSnapshotsPublic)
def read_story_snapshots(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Get all snapshots for this story progress (admin/debug).

    Useful for monitoring snapshot coverage and debugging replay.
    """
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

    # Get all snapshots for this progress
    statement = (
        select(ProgressSnapshot)
        .where(ProgressSnapshot.progress_id == progress.id)
        .order_by(ProgressSnapshot.created_at.asc())
    )

    snapshots = session.exec(statement).all()

    return ProgressSnapshotsPublic(
        data=snapshots,
        count=len(snapshots)
    )


@router.post("/{story_id}/snapshots/create", response_model=ProgressSnapshotPublic)
def create_story_snapshot(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Manually create snapshot at current head position (admin/debug).

    Normally snapshots are created automatically every N choices.
    This endpoint allows manual snapshot creation for testing.
    """
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

    if progress.head_choice_id is None:
        raise HTTPException(
            status_code=400,
            detail="Cannot create snapshot at story start"
        )

    # Check if snapshot already exists
    existing = session.exec(
        select(ProgressSnapshot).where(
            ProgressSnapshot.progress_id == progress.id,
            ProgressSnapshot.choice_id == progress.head_choice_id
        )
    ).first()

    if existing:
        return existing  # Already have snapshot

    # Create snapshot
    snapshot = ProgressSnapshot(
        progress_id=progress.id,
        choice_id=progress.head_choice_id,
        story_state=progress.story_state.copy() if progress.story_state else {},
        current_node_id=progress.current_node_id
    )

    session.add(snapshot)
    session.commit()
    session.refresh(snapshot)

    return snapshot
