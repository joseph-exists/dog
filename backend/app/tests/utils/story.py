"""Helper functions for creating test stories and nodes via API."""

from typing import Any
from fastapi.testclient import TestClient

from app.core.config import settings
from app.tests.utils.utils import random_lower_string


def create_test_story(
    client: TestClient,
    headers: dict[str, str],
    title: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a test story via API.

    Args:
        client: FastAPI test client
        headers: Authentication headers
        title: Story title (auto-generated if None)
        description: Story description (auto-generated if None)

    Returns:
        Story JSON response

    Example:
        story = create_test_story(client, superuser_token_headers)
        assert "id" in story
    """
    data = {
        "title": title or f"Test Story {random_lower_string()[:8]}",
        "description": description or "Test story description",
    }

    response = client.post(
        f"{settings.API_V1_STR}/stories",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, f"Failed to create story: {response.text}"
    return response.json()


def create_test_node(
    client: TestClient,
    headers: dict[str, str],
    story_id: str,
    title: str | None = None,
    content: str | None = None,
    is_start: bool = False,
    is_end: bool = False,
    story_version: int = 1,
) -> dict[str, Any]:
    """
    Create a test story node via API.

    Args:
        client: FastAPI test client
        headers: Authentication headers
        story_id: UUID of the story this node belongs to
        title: Node title (auto-generated if None)
        content: Node content (auto-generated if None)
        is_start: Whether this is a start node
        is_end: Whether this is an end node
        story_version: Story version (default 1)

    Returns:
        StoryNode JSON response

    Example:
        story = create_test_story(client, headers)
        start_node = create_test_node(client, headers, story["id"], is_start=True)
        end_node = create_test_node(client, headers, story["id"], is_end=True)
    """
    data = {
        "story_id": story_id,
        "story_version": story_version,
        "title": title or f"Test Node {random_lower_string()[:8]}",
        "content": content or "Test node content",
        "is_start_node": is_start,
        "is_end_node": is_end,
    }

    response = client.post(
        f"{settings.API_V1_STR}/storynodes",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, f"Failed to create node: {response.text}"
    return response.json()


def create_test_choice(
    client: TestClient,
    headers: dict[str, str],
    from_node_id: str,
    to_node_id: str,
    text: str | None = None,
    order: int = 0,
    sets_state: dict | None = None,
    requires_state: dict | None = None,
) -> dict[str, Any]:
    """
    Create a test node choice via API.

    Args:
        client: FastAPI test client
        headers: Authentication headers
        from_node_id: Source node UUID
        to_node_id: Destination node UUID
        text: Choice text (auto-generated if None)
        order: Display order
        sets_state: State changes to apply
        requires_state: Required state conditions

    Returns:
        NodeChoice JSON response

    Example:
        choice = create_test_choice(
            client, headers,
            from_node_id=node1["id"],
            to_node_id=node2["id"],
            text="Go forward",
            sets_state={"visited_node1": True}
        )
    """
    data = {
        "from_node_id": from_node_id,
        "to_node_id": to_node_id,
        "text": text or f"Test choice {random_lower_string()[:8]}",
        "order": order,
    }

    if sets_state is not None:
        data["sets_state"] = sets_state

    if requires_state is not None:
        data["requires_state"] = requires_state

    response = client.post(
        f"{settings.API_V1_STR}/node-choices",
        headers=headers,
        json=data,
    )

    assert response.status_code == 200, f"Failed to create choice: {response.text}"
    return response.json()
