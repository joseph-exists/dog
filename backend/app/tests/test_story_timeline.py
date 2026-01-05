"""Tests for Phase 3: Timeline navigation (undo/jump)."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app import crud
from app.models import UserNodeChoice, UserStoryProgress, ProgressSnapshot


def test_undo_moves_to_parent(
    client: TestClient,
    db: Session,
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
    db.refresh(progress)
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
    choice = db.get(UserNodeChoice, initial_head)
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
    db: Session,
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
    db.refresh(progress)
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
    db: Session,
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
    db.refresh(progress)
    chain = crud.get_choice_ancestor_chain(
        session=db, choice_id=progress.head_choice_id
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
    db.add(abandoned_choice)
    db.commit()

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
    db: Session,
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

    db.refresh(progress)
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
    db: Session,
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
    db: Session,
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

    db.refresh(progress)

    # Verify tree structure in database
    all_choices = db.exec(
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