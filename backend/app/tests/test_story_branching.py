"""Tests for story branching functionality."""

from fastapi.testclient import TestClient
from sqlmodel import Session


def test_start_node_has_multiple_choices(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that start node presents multiple available choices.

    Given: Story with branching start node
    When: GET current-node at start
    Then: Returns 2 available_choices
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["available_choices"]) == 2

    # Verify choices are distinct
    choice_texts = [c["text"] for c in data["available_choices"]]
    assert "left" in choice_texts[0].lower() or "right" in choice_texts[0].lower()
    assert "left" in choice_texts[1].lower() or "right" in choice_texts[1].lower()
    assert choice_texts[0] != choice_texts[1]


def test_different_choices_lead_to_different_nodes(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that taking different choices leads to different nodes.

    Given: Story with 2 choices from start
    When: User A takes choice 0, User B takes choice 1
    Then: They end up at different nodes with different content
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices = response.json()["available_choices"]
    choice_0_id = choices[0]["id"]
    choice_1_id = choices[1]["id"]

    # Take choice 0
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_0_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Get current node after choice 0
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    node_after_choice_0 = response.json()

    # Undo to test other path
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Take choice 1
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_1_id}",
        headers=normal_user_token_headers,
    )
    assert response.status_code == 200

    # Get current node after choice 1
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    node_after_choice_1 = response.json()

    # Verify different nodes
    assert node_after_choice_0["node"]["id"] != node_after_choice_1["node"]["id"]
    assert node_after_choice_0["node"]["title"] != node_after_choice_1["node"]["title"]


def test_branch_state_changes_differ(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that state changes differ based on which branch is taken.

    Given: Story with 2 branches setting different state
    When: Take left branch (sets path="left")
    Then: story_state contains {"path": "left"}
    When: Undo and take right branch (sets path="right")
    Then: story_state contains {"path": "right"}
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get choices (assume [0]=left, [1]=right based on order)
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices = response.json()["available_choices"]

    # Take first choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choices[0]['id']}",
        headers=normal_user_token_headers,
    )
    state_after_first = response.json()["story_state"]

    # Undo
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Take second choice
    response = client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choices[1]['id']}",
        headers=normal_user_token_headers,
    )
    state_after_second = response.json()["story_state"]

    # Verify states are different
    assert state_after_first != state_after_second
    assert "path" in state_after_first or "path" in state_after_second


def test_undo_from_branch_preserves_all_choices(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_simple_branch: tuple,
) -> None:
    """
    Test that undo from a branch returns to branch point with all choices available.

    Given: User takes left branch
    When: User undos back to start
    Then: Both left and right choices are still available
    """
    story, progress = db_story_with_simple_branch
    persona_id = progress.user_persona_id

    # Get initial choices
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    initial_choices = response.json()["available_choices"]
    assert len(initial_choices) == 2

    # Take first choice
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{initial_choices[0]['id']}",
        headers=normal_user_token_headers,
    )

    # Undo
    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/undo",
        headers=normal_user_token_headers,
    )

    # Get choices after undo
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choices_after_undo = response.json()["available_choices"]

    # Verify all choices still available
    assert len(choices_after_undo) == 2
    # Choice IDs should match (order may differ)
    initial_ids = {c["id"] for c in initial_choices}
    after_undo_ids = {c["id"] for c in choices_after_undo}
    assert initial_ids == after_undo_ids