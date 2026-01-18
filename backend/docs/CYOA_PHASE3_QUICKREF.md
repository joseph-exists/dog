# Phase 3 Quick Reference Card - Undo & Rewind APIs

**Goal:** Expose timeline navigation (undo, jump to ancestor, timeline breadcrumbs)

**Estimated Time:** 1 week
**Branch:** `feature/cyoa-phase-3-timeline-navigation`
**Prerequisites:** Phase 1 and Phase 2 complete and merged

---

## Pre-Implementation Checklist

- [x ] Phase 1 and Phase 2 merged to main
- [ x] Read CYOA_MIGRATION_PLAN.md Phase 3 section
- [x ] Read CYOA_MIGRATION_ADDENDUM.md API patterns
- [ x] Pull latest main branch
- [x ] Create feature branch from main
- [x ] Ensure local dev environment running

---

## [x] complete Step 1: Add Timeline Models (20 minutes)

### Location: `backend/app/models.py`

Add these models near the UserStoryProgress models (around line 630):

```python
# ==================== Timeline Navigation Models (Phase 3) ====================

class JumpRequest(SQLModel):
    """
    Request model for jumping to ancestor choice.

    Used by jump endpoint to specify target and optimistic concurrency check.
    """
    choice_id: uuid.UUID | None = Field(
        default=None,
        description="Target choice to jump to (null = jump to story start)"
    )
    expected_head_version: int = Field(
        description="Optimistic concurrency check - must match current head_version"
    )


class TimelineEvent(SQLModel):
    """
    Timeline entry for UI breadcrumbs.

    Represents a single event in the player's active timeline.
    Abandoned branches are NOT included in timeline responses.
    """
    choice_id: uuid.UUID | None = Field(
        description="Choice ID (null for story start event)"
    )
    choice_text: str = Field(description="Text of the choice made")
    node_title: str = Field(description="Title of the node reached")
    choice_time: datetime = Field(description="When choice was made")
    is_current: bool = Field(description="Is this the current head position?")


class Timeline(SQLModel):
    """
    Active timeline from root → head.

    Contains only the ancestor chain (root to current head).
    Siblings and abandoned branches are filtered out.
    """
    events: list[TimelineEvent]
    head_version: int = Field(description="Current head version for optimistic locking")
```

**NOTE**: These are request/response models (not database models), so they don't need the full Base/Create/Update/Database/Public/Collection pattern per TinyFoot data-model-best-practices.md.

---

## Step 2: Add CRUD Functions (45 minutes)

### Location: `backend/app/crud.py`

Add at the end of the file, after Phase 2 functions:

```python
# ==================== Phase 3: Timeline Navigation Functions ====================
#
# IMPROVEMENT OVER MIGRATION PLAN:
# The migration plan shows inline replay logic in undo/jump endpoints.
# These helper functions extract common logic for DRY and maintainability.
# This follows TinyFoot functional patterns from RULES.md.
# ==============================================================================

def validate_ancestor_constraint(
    *, session: Session, target_choice_id: uuid.UUID, current_head_id: uuid.UUID
) -> bool:
    """
    Validate that target choice is an ancestor of current head.

    Used by jump endpoint to prevent forward jumps (which would expose hidden branches).
    Forward jumps are prohibited because they would reveal abandoned timeline branches.

    Args:
        session: Database session
        target_choice_id: Proposed jump target
        current_head_id: Current head position

    Returns:
        True if target is ancestor of current head, False otherwise

    Raises:
        ValueError: If current_head_id doesn't exist (via get_choice_ancestor_chain)

    Example:
        # Before jump, validate target is in ancestor chain
        is_ancestor = crud.validate_ancestor_constraint(
            session=session,
            target_choice_id=target,
            current_head_id=progress.head_choice_id
        )
        if not is_ancestor:
            raise HTTPException(400, "Target is not an ancestor")
    """
    # Get ancestor chain from current head to root
    ancestors = get_choice_ancestor_chain(session=session, choice_id=current_head_id)
    ancestor_ids = {c.id for c in ancestors}

    # Check if target is in the ancestor chain
    return target_choice_id in ancestor_ids


def move_head_to_choice(
    *,
    session: Session,
    progress: UserStoryProgress,
    target_choice_id: uuid.UUID | None,
) -> UserStoryProgress:
    """
    Move head pointer to target choice and update derived state.

    This is the core function for undo/jump operations.
    Encapsulates head movement, state replay, and node derivation.

    IMPORTANT: This function uses replay to UPDATE story_state.
    Unlike make_story_choice (which still uses mutable updates in Phase 3),
    timeline navigation MUST replay because we're moving backward in time.

    Args:
        session: Database session
        progress: UserStoryProgress instance to update
        target_choice_id: Target choice (null = story start)

    Returns:
        Updated UserStoryProgress instance (mutated in place)

    Side effects:
        - Updates progress.head_choice_id to target
        - Increments progress.head_version (optimistic lock)
        - Replays state from new head (replaces progress.story_state)
        - Updates progress.current_node_id
        - Resets progress.is_completed flag (might not be at end anymore)

    Raises:
        ValueError: If target_choice_id doesn't exist or state replay fails

    Example:
        # In undo endpoint
        current_choice = session.get(UserNodeChoice, progress.head_choice_id)
        progress = crud.move_head_to_choice(
            session=session,
            progress=progress,
            target_choice_id=current_choice.parent_choice_id  # Move to parent
        )
        session.add(progress)
        session.commit()
    """
    # Move head pointer
    progress.head_choice_id = target_choice_id
    progress.head_version += 1

    # Replay state from new head position
    # Uses Phase 2 replay_state_from_head (NOT the optimized version from Phase 5)
    progress.story_state = replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=target_choice_id,
    )

    # Derive current node from new head position
    progress.current_node_id = get_current_node_from_head(
        session=session,
        head_choice_id=target_choice_id,
        story_id=progress.story_id,
        story_version=progress.story_version,
    )

    # Reset completion flag (might not be at end node anymore)
    progress.is_completed = False

    return progress
```

**NOTE**: These helper functions are an improvement over the migration plan (which shows inline logic). They follow DRY principles and functional patterns from RULES.md.

---

## [x] Step 3: Add Timeline Endpoints (2 hours)

### Location: `backend/app/api/routes/user_story_progress.py`

Add these three new endpoints after the existing `make_story_choice` endpoint:

#### 3.1 Add Undo Endpoint

```python
@router.post("/{story_id}/undo", response_model=UserStoryProgressPublic)
def undo_story_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
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

    # Get parent choice
    current_choice = session.get(UserNodeChoice, progress.head_choice_id)
    if not current_choice:
        raise HTTPException(
            status_code=500,
            detail="Head choice not found (data corruption)"
        )

    # Move head to parent using helper function
    progress = crud.move_head_to_choice(
        session=session,
        progress=progress,
        target_choice_id=current_choice.parent_choice_id,
    )

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

#### 3.2 Add Jump Endpoint

```python
@router.post("/{story_id}/jump", response_model=UserStoryProgressPublic)
def jump_story_head(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    jump_request: JumpRequest,
) -> Any:
    """
    Jump head to any ancestor choice (rewind to arbitrary point).

    Validation:
    - Target choice must be ancestor of current head (enforces no forward jumps)
    - Optimistic concurrency via expected_head_version

    Behavior:
    - Moves head_choice_id to target
    - Replays state from target
    - All future choices after target become hidden

    Errors:
        400: Target not ancestor, or other validation error
        404: User persona, story progress, or target choice not found
        409: Head version conflict (concurrent modification)

    Returns:
        Updated progress at new head position

    Example:
        POST /api/v1/user-personas/{id}/stories/{story_id}/jump
        Body: {
            "choice_id": "uuid-of-ancestor",
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

    # Move head to target using helper function
    progress = crud.move_head_to_choice(
        session=session,
        progress=progress,
        target_choice_id=target_choice_id,
    )

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

#### 3.3 Add Timeline Endpoint

```python
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
```

---

## Step 4: Write Tests (2 hours)

### Location: `backend/app/tests/test_story_timeline.py` (NEW FILE)
[x] 
```python
"""Tests for Phase 3: Timeline navigation (undo/jump)."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import UserNodeChoice, UserStoryProgress


def test_undo_moves_to_parent(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that undo moves head to parent choice.

    Given: Progress with 2 choices (A → B), head at B
    When: POST /undo
    Then: head moves to A, state replayed from A
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 2 choices
    for _ in range(2):
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
        choice_id = response.json()["available_choices"][0]["id"]

        client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )

    # Get current state
    session.refresh(progress)
    initial_head = progress.head_choice_id
    initial_version = progress.head_version

    # Undo
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Verify head moved to parent
    choice = session.get(UserNodeChoice, initial_head)
    assert data["head_choice_id"] == str(choice.parent_choice_id)
    assert data["head_version"] == initial_version + 1


def test_undo_at_start_returns_error(
    client: TestClient,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that undo at story start returns 400 error.

    Given: Progress at story start (head_choice_id = None)
    When: POST /undo
    Then: Returns 400 "Already at story start"
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Attempt undo at start
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 400
    assert "already at story start" in response.json()["detail"].lower()


def test_jump_to_ancestor(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that jump moves head to specified ancestor.

    Given: Chain A → B → C → D, head at D
    When: POST /jump with target=B
    Then: head moves to B, state replayed from B
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 4 choices
    choice_ids = []
    for _ in range(4):
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
        choice_id = response.json()["available_choices"][0]["id"]

        response = client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )
        choice_ids.append(response.json()["head_choice_id"])

    # Get head version
    session.refresh(progress)
    head_version = progress.head_version

    # Jump to second choice
    target_choice_id = choice_ids[1]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/jump",
        headers=normal_user_token_headers,
        json={
            "choice_id": target_choice_id,
            "expected_head_version": head_version,
        },
    )

    assert response.status_code == 200
    data = response.json()

    # Verify head at target
    assert data["head_choice_id"] == target_choice_id
    assert data["head_version"] == head_version + 1


def test_jump_non_ancestor_returns_error(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that jump to non-ancestor returns 400 error.

    Given: Linear chain A → B, head at B
    When: Create abandoned branch C from A (via manual DB insert)
    And: POST /jump with target=C
    Then: Returns 400 "not an ancestor"
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 2 choices (A → B)
    for _ in range(2):
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
        choice_id = response.json()["available_choices"][0]["id"]

        client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )

    # Manually create abandoned branch C from A
    session.refresh(progress)
    chain = crud.get_choice_ancestor_chain(
        session=session, choice_id=progress.head_choice_id
    )
    choice_a = chain[0]

    # Create choice C as sibling of B (both from A)
    abandoned_choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice_a.id,
        choice_text="Abandoned path",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"abandoned": True},
    )
    session.add(abandoned_choice)
    session.commit()

    # Try to jump to abandoned choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/jump",
        headers=normal_user_token_headers,
        json={
            "choice_id": str(abandoned_choice.id),
            "expected_head_version": progress.head_version,
        },
    )

    assert response.status_code == 400
    assert "not an ancestor" in response.json()["detail"].lower()


def test_jump_optimistic_concurrency(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that jump rejects stale head_version.

    Given: Progress at version N
    When: POST /jump with expected_head_version=N-1
    Then: Returns 409 conflict
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )

    session.refresh(progress)
    current_version = progress.head_version
    stale_version = current_version - 1

    # Try jump with stale version
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/jump",
        headers=normal_user_token_headers,
        json={
            "choice_id": None,  # Jump to start
            "expected_head_version": stale_version,
        },
    )

    assert response.status_code == 409
    assert "version conflict" in response.json()["detail"].lower()


def test_timeline_shows_active_path_only(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that timeline returns only active path, not abandoned branches.

    Given: Path A → B → C, then undo to A, then make D (abandons B, C)
    When: GET /timeline
    Then: Returns [Start, A, D] only (not B or C)
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 3 choices (A → B → C)
    for i in range(3):
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
        choice_id = response.json()["available_choices"][0]["id"]

        client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )

    # Undo 2 times (back to A)
    for _ in range(2):
        client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
            headers=normal_user_token_headers,
        )

    # Make new choice D (abandons B and C)
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )

    # Get timeline
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/timeline",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()

    # Timeline should have: Start + A + D = 3 events
    assert len(data["events"]) == 3

    # Verify order and content
    assert data["events"][0]["choice_text"] == "Story Start"
    assert data["events"][0]["is_current"] is False

    # Last event should be current
    assert data["events"][-1]["is_current"] is True


def test_make_choice_after_undo_creates_branch(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that making choice after undo creates new branch.

    Given: Chain A → B, head at B
    When: Undo to A, then make choice C
    Then: Tree is A → B (abandoned), A → C (active)
    And: Timeline shows only [Start, A, C]
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make 2 choices (A → B)
    for _ in range(2):
        response = client.get(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
            headers=normal_user_token_headers,
        )
        choice_id = response.json()["available_choices"][0]["id"]

        client.post(
            f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
            headers=normal_user_token_headers,
        )

    # Undo to A
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Make new choice C
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )

    session.refresh(progress)

    # Verify tree structure in database
    all_choices = session.exec(
        select(UserNodeChoice).where(
            UserNodeChoice.progress_id == progress.id
        )
    ).all()

    # Should have 3 choices: A, B, C
    assert len(all_choices) == 3

    # Find choice A (parent_choice_id = None)
    choice_a = next(c for c in all_choices if c.parent_choice_id is None)

    # Both B and C should have A as parent
    children_of_a = [c for c in all_choices if c.parent_choice_id == choice_a.id]
    assert len(children_of_a) == 2  # B and C are siblings

    # Timeline should show only active path: Start → A → C
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/timeline",
        headers=normal_user_token_headers,
    )

    data = response.json()
    assert len(data["events"]) == 3  # Start, A, C (not B)
```

---

## Step 5: Update API Documentation (30 minutes)

### Location: `backend/app/api/routes/user_story_progress.py`

Update module docstring at the top of the file:

```python
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
```

---

## Step 6: Commit Changes (15 minutes)

```bash
# Check status
git status

# Stage changes
git add backend/app/models.py
git add backend/app/crud.py
git add backend/app/api/routes/user_story_progress.py
git add backend/app/tests/test_story_timeline.py

# Commit
git commit -m "feat: Add timeline navigation (undo/jump/breadcrumbs) for CYOA (Phase 3)

- Add JumpRequest, TimelineEvent, Timeline models
- Add validate_ancestor_constraint() to prevent forward jumps
- Add move_head_to_choice() for atomic head updates (DRY improvement)
- Add undo_story_choice endpoint (POST /undo)
- Add jump_story_head endpoint (POST /jump)
- Add read_story_timeline endpoint (GET /timeline)
- Implement optimistic concurrency via head_version
- Add comprehensive timeline navigation tests
- Update API documentation

Timeline navigation enables:
- Undo last choice (rewind one step)
- Jump to any ancestor (rewind to arbitrary point)
- View active path breadcrumbs (hidden branch filtering)

Helper functions (validate_ancestor_constraint, move_head_to_choice)
improve code reuse over migration plan's inline approach.

Abandoned branches remain in database but are hidden from
timeline queries, enabling future 'branch explorer' features.

Refs: CYOA_MIGRATION_PLAN.md Phase 3, CYOA_MIGRATION_ADDENDUM.md"

# Push branch
git push origin feature/cyoa-phase-3-timeline-navigation
```

---

## Step 7: Verify Timeline Behavior (45 minutes)

### 7.1 Run Full Test Suite

```bash
docker compose exec backend bash
pytest app/tests/ -v
exit
```

### 7.2 Manual Timeline Testing

```bash
# Use API docs
open http://localhost:8000/docs

# Test undo flow:
# 1. Start story
# 2. Make 3 choices
# 3. GET /timeline - should show Start + 3 choices
# 4. POST /undo
# 5. GET /timeline - should show Start + 2 choices
# 6. POST /undo
# 7. GET /timeline - should show Start + 1 choice

# Test branch creation:
# 1. Start story
# 2. Make 2 choices (A → B)
# 3. POST /undo (back to A)
# 4. Make new choice (C)
# 5. GET /timeline - should show Start, A, C (not B)

# Test jump:
# 1. Start story
# 2. Make 5 choices
# 3. GET /timeline - note head_version and choice IDs
# 4. POST /jump to 2nd choice with correct head_version
# 5. GET /timeline - should show Start + first 2 choices
# 6. POST /jump with stale head_version - should get 409
```

### 7.3 Database Inspection

```bash
docker compose exec backend bash
psql -U app -d app

-- View full tree (including abandoned branches)
SELECT
    id,
    parent_choice_id,
    choice_text,
    choice_time,
    progress_id
FROM usernodechoice
WHERE progress_id = '<progress-id>'
ORDER BY choice_time;

-- Identify abandoned branches
WITH RECURSIVE ancestors AS (
    -- Start with current head
    SELECT id, parent_choice_id, choice_text
    FROM usernodechoice
    WHERE id = '<current-head-id>'

    UNION ALL

    -- Walk up to root
    SELECT n.id, n.parent_choice_id, n.choice_text
    FROM usernodechoice n
    INNER JOIN ancestors a ON n.id = a.parent_choice_id
)
SELECT
    c.id,
    c.choice_text,
    CASE
        WHEN a.id IS NOT NULL THEN 'Active'
        ELSE 'Abandoned'
    END AS status
FROM usernodechoice c
LEFT JOIN ancestors a ON c.id = a.id
WHERE c.progress_id = '<progress-id>'
ORDER BY c.choice_time;

\q
exit
```

---

## Troubleshooting

### Undo Doesn't Update State

**Error:** After undo, `story_state` still has values from future

**Cause:** `move_head_to_choice` not replaying state correctly

**Debug:**
```python
# Add logging in move_head_to_choice
import logging
logger = logging.getLogger(__name__)

logger.info(f"Moving head from {progress.head_choice_id} to {target_choice_id}")
logger.info(f"Old state: {progress.story_state}")

progress.story_state = replay_state_from_head(...)

logger.info(f"New state: {progress.story_state}")
```

### Jump Allows Forward Jumps

**Error:** Can jump to non-ancestor choices

**Cause:** `validate_ancestor_constraint` not being called or failing

**Fix:**
```python
# Verify in jump endpoint:
if target_choice_id is not None and progress.head_choice_id is not None:
    is_ancestor = crud.validate_ancestor_constraint(
        session=session,
        target_choice_id=target_choice_id,
        current_head_id=progress.head_choice_id,
    )

    if not is_ancestor:
        # Log for debugging
        logger.warning(
            f"Jump attempt to non-ancestor: "
            f"target={target_choice_id}, head={progress.head_choice_id}"
        )
        raise HTTPException(status_code=400, detail="Not an ancestor")
```

### Timeline Shows Abandoned Branches

**Error:** Timeline includes siblings

**Cause:** Not using `get_choice_ancestor_chain`

**Fix:** Verify timeline endpoint uses:
```python
chain = crud.get_choice_ancestor_chain(
    session=session,
    choice_id=progress.head_choice_id
)
# Only iterate over chain, never query siblings
```

### Optimistic Concurrency Not Working

**Error:** Two clients can jump simultaneously

**Cause:** Not checking `expected_head_version`

**Fix:** Ensure in jump endpoint:
```python
if jump_request.expected_head_version != progress.head_version:
    raise HTTPException(status_code=409, detail="Version conflict")
```

---

## Success Criteria

- [ ] Undo endpoint works (moves to parent)
- [ ] Jump endpoint works (moves to ancestor)
- [ ] Jump rejects non-ancestors (400 error)
- [ ] Jump enforces optimistic concurrency (409 on stale version)
- [ ] Timeline shows only active path
- [ ] Timeline hides abandoned branches
- [ ] Making choice after undo creates new branch
- [ ] All Phase 1 & 2 tests still pass
- [ ] All Phase 3 tests pass (7 tests)
- [ ] Code committed and pushed

---

## Estimated Time Breakdown

| Task | Time | Running Total |
|------|------|---------------|
| Add timeline models | 20min | 20min |
| Add CRUD functions | 45min | 1h 5min |
| Add timeline endpoints | 2h | 3h 5min |
| Write tests | 2h | 5h 5min |
| Update documentation | 30min | 5h 35min |
| Commit changes | 15min | 5h 50min |
| Verify timeline behavior | 45min | **6h 35min** |

**Buffer for issues:** +1h 25min
**Total with buffer:** ~8 hours (1 work day)

---

## Next Steps After Phase 3

1. **Create PR** to main branch
2. **Team review** focusing on:
   - Timeline navigation correctness
   - Abandoned branch hiding
   - Optimistic concurrency
   - Test coverage
3. **Merge** after approval
4. **Update frontend** to add:
   - Undo button
   - Timeline breadcrumbs UI
   - Jump to earlier choice
5. **Begin Phase 4** (Real-time Distribution)

---

## Quick Commands Reference

```bash
# Run timeline tests
pytest app/tests/test_story_timeline.py -v

# Test specific function
pytest app/tests/test_story_timeline.py::test_undo_moves_to_parent -v

# Test undo endpoint manually
curl -X POST http://localhost:8000/api/v1/user-personas/{id}/stories/{id}/undo \
  -H "Authorization: Bearer $TOKEN"

# Test timeline endpoint
curl http://localhost:8000/api/v1/user-personas/{id}/stories/{id}/timeline \
  -H "Authorization: Bearer $TOKEN"
```

---

## Support Resources

- **Main Plan:** `backend/docs/CYOA_MIGRATION_PLAN.md` (Phase 3 section)
- **Patterns:** `backend/docs/CYOA_MIGRATION_ADDENDUM.md` (API patterns)
- **Phase 1 Quickref:** `backend/docs/CYOA_PHASE1_QUICKREF.md`
- **Phase 2 Quickref:** `backend/docs/CYOA_PHASE2_QUICKREF.md`
- **Story System:** `backend/docs/STORY_SYSTEM.md`

**Questions?** Reference documents above or ping backend team.
