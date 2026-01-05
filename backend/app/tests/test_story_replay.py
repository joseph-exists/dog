"""Tests for Phase 2: Replay logic."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings

from app import crud
from app.models import UserNodeChoice, UserStoryProgress, ProgressSnapshot


def test_replay_state_from_single_choice(
    db: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay reconstructs state from single choice.

    Given: Progress with one choice that sets state {"has_torch": true}
    When: replay_state_from_head()
    Then: Returns {"has_torch": true}
    """
    story, progress = db_story_with_progress

    # Create a choice with state changes
    choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Pick up torch",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_torch": True},
    )
    db.add(choice)
    db.commit()
    db.refresh(choice)

    # Replay state
    replayed = crud.replay_state_from_head(
        session=db,
        progress_id=progress.id,
        head_choice_id=choice.id,
    )

    assert replayed == {"has_torch": True}


def test_replay_state_from_chain(
    db: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay correctly merges state from chain.

    Given: Chain of 3 choices with state changes
    When: replay_state_from_head(choice_3)
    Then: Returns merged state from all 3 choices
    """
    story, progress = db_story_with_progress

    # Create choice chain
    choice1 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Pick up torch",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_torch": True, "location": "forest"},
    )
    db.add(choice1)
    db.flush()

    choice2 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice1.id,
        choice_text="Enter cave",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"location": "cave", "visited_cave": True},
    )
    db.add(choice2)
    db.flush()

    choice3 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice2.id,
        choice_text="Find treasure",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_treasure": True, "gold": 100},
    )
    db.add(choice3)
    db.commit()

    # Replay state from choice3
    replayed = crud.replay_state_from_head(
        session=db,
        progress_id=progress.id,
        head_choice_id=choice3.id,
    )

    # Should merge all state changes (shallow merge, later values override)
    expected = {
        "has_torch": True,
        "location": "cave",  # Overridden by choice2
        "visited_cave": True,
        "has_treasure": True,
        "gold": 100,
    }
    assert replayed == expected


def test_replay_state_at_story_start(
    db: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay returns empty state when head is None.

    Given: Progress with head_choice_id = None
    When: replay_state_from_head()
    Then: Returns {}
    """
    story, progress = db_story_with_progress

    replayed = crud.replay_state_from_head(
        session=db,
        progress_id=progress.id,
        head_choice_id=None,
    )

    assert replayed == {}


def test_ancestor_chain_order(
    db: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that get_choice_ancestor_chain returns correct order.

    Given: Chain A → B → C
    When: get_choice_ancestor_chain(C)
    Then: Returns [A, B, C] in that order
    """
    story, progress = db_story_with_progress

    # Create chain
    choice_a = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Choice A",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    db.add(choice_a)
    db.flush()

    choice_b = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice_a.id,
        choice_text="Choice B",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    db.add(choice_b)
    db.flush()

    choice_c = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice_b.id,
        choice_text="Choice C",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    db.add(choice_c)
    db.commit()

    # Get ancestor chain
    chain = crud.get_choice_ancestor_chain(session=db, choice_id=choice_c.id)

    assert len(chain) == 3
    assert chain[0].id == choice_a.id
    assert chain[1].id == choice_b.id
    assert chain[2].id == choice_c.id


def test_validate_state_endpoint(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that validate-state endpoint correctly compares stored vs replayed.

    Given: Progress with choices made
    When: GET /validate-state
    Then: Returns match=true and both states equal
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make a choice (this updates both mutable state and creates event)
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )

    # Validate state
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/validate-state",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["match"] is True
    assert data["differences"] == {}
    assert data["stored_state"] == data["replayed_state"]


def test_replay_validates_progress_ownership(
    db: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay raises error if choice doesn't belong to progress.

    Given: Choice from different progress
    When: replay_state_from_head() with wrong progress_id
    Then: Raises ValueError
    """
    story, progress1 = db_story_with_progress

    # Create second progress
    progress2 = UserStoryProgress(
        user_persona_id=progress1.user_persona_id,
        story_id=story.id,
        story_version=1,
    )
    db.add(progress2)
    db.flush()

    # Create choice for progress1
    choice = UserNodeChoice(
        progress_id=progress1.id,
        parent_choice_id=None,
        choice_text="Test",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"test": True},
    )
    db.add(choice)
    db.commit()

    # Try to replay with wrong progress_id
    import pytest

    with pytest.raises(ValueError, match="doesn't belong to progress"):
        crud.replay_state_from_head(
            session=db,
            progress_id=progress2.id,
            head_choice_id=choice.id,
        )