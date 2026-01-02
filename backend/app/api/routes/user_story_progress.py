"""
User Story Progress Routes - Player Instance Operations

Handles playing concerns for user story instances.
Each UserStoryProgress represents a player's playthrough of a story,
locked to a specific story version at creation time.

PHASE 3 ADDITIONS: Timeline Navigation
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

    # Find the starting node of the story (for current version)
    statement = select(StoryNode).where(
        StoryNode.story_id == story_id,
        StoryNode.story_version == story.current_version,
        StoryNode.is_start_node is True
    )
    start_node = session.exec(statement).first()

    if not start_node:
        raise HTTPException(
            status_code=500,
            detail=f"No start node found for story version {story.current_version}"
        )

    # Create the progress locked to current version
    progress_in = UserStoryProgressCreate(
        user_persona_id=user_persona_id,
        story_id=story_id,
        story_version=story.current_version,  # Lock to current version
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

    # Update head pointer - NEW
    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.current_node_id = choice.to_node_id

    # Update the story state if needed
    if choice.sets_state:
        if progress.story_state:
            # Merge the existing state with the new state changes
            progress.story_state.update(choice.sets_state)
        else:
            progress.story_state = choice.sets_state

    replayed_state = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id,
    )

    # Log warning if mismatch (should never happen)
    if replayed_state != progress.story_state:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"State mismatch for progress {progress.id}: "
            f"stored={progress.story_state}, replayed={replayed_state}"
        )


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