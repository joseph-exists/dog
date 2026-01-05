"""Tests for Phase 1: Event tree structure."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.models import UserNodeChoice, UserStoryProgress, ProgressSnapshot


def test_choice_creates_parent_link(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,  # Assumes fixture exists
) -> None:
    """
    Test that making a choice sets parent_choice_id correctly.

    Given: A story progress at start (head_choice_id = None)
    When: Player makes first choice
    Then: New choice has parent_choice_id = None

    When: Player makes second choice
    Then: New choice has parent_choice_id = first_choice.id
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Get available choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    first_choice_id = data["available_choices"][0]["id"]

    # Make first choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{first_choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify first choice has parent_choice_id = None
    first_user_choice = db.exec(
        select(UserNodeChoice)
        .where(UserNodeChoice.progress_id == progress.id)
        .order_by(UserNodeChoice.choice_time)
    ).first()
    assert first_user_choice is not None
    assert first_user_choice.parent_choice_id is None

    # Make second choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    second_choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{second_choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify second choice has parent_choice_id = first choice
    choices = db.exec(
        select(UserNodeChoice)
        .where(UserNodeChoice.progress_id == progress.id)
        .order_by(UserNodeChoice.choice_time)
    ).all()
    assert len(choices) == 2
    assert choices[1].parent_choice_id == choices[0].id


def test_head_pointer_updates(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that head_choice_id and head_version update correctly.

    Given: Progress at start (head_choice_id=None, head_version=0)
    When: Player makes choice
    Then: head_choice_id = new_choice.id, head_version = 1
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Verify initial state
    db.refresh(progress)
    assert progress.head_choice_id is None
    assert progress.head_version == 0

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify head updated
    db.refresh(progress)
    assert progress.head_choice_id is not None
    assert progress.head_version == 1

    # Verify head points to the choice we made
    user_choice = db.get(UserNodeChoice, progress.head_choice_id)
    assert user_choice is not None
    assert user_choice.progress_id == progress.id


def test_rng_data_field_exists(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that rng_data field can be set (even if null in Phase 1).

    Given: A choice is made
    Then: UserNodeChoice has rng_data field (even if null)
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make choice
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Verify rng_data exists
    user_choice = db.exec(
        select(UserNodeChoice).where(UserNodeChoice.progress_id == progress.id)
    ).first()
    assert user_choice is not None
    assert hasattr(user_choice, "rng_data")
    # In Phase 1, this will be None
    assert user_choice.rng_data is None