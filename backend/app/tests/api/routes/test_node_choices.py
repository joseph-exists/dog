from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.config import settings
from app.tests.utils.story import create_test_story, create_test_node


def test_create_node_choice(client: TestClient, superuser_token_headers: dict):
    """Test creating a node choice."""
    # Setup: Create story and nodes
    story = create_test_story(client, superuser_token_headers)
    node_1 = create_test_node(client, superuser_token_headers, story["id"], is_start=True)
    node_2 = create_test_node(client, superuser_token_headers, story["id"])

    # Create choice
    data = {
        "from_node_id": node_1["id"],
        "to_node_id": node_2["id"],
        "text": "Test choice",
        "order": 0,
        "sets_state": {"test": True}
    }

    response = client.post(
        f"{settings.API_V1_STR}/node-choices",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 200
    choice = response.json()
    assert choice["text"] == "Test choice"
    assert choice["from_node_id"] == node_1["id"]
    assert choice["to_node_id"] == node_2["id"]


def test_cannot_create_choice_from_end_node(client: TestClient, superuser_token_headers: dict):
    """Test that choices cannot be created from end nodes."""
    story = create_test_story(client, superuser_token_headers)
    end_node = create_test_node(client, superuser_token_headers, story["id"], is_end=True)
    other_node = create_test_node(client, superuser_token_headers, story["id"])

    data = {
        "from_node_id": end_node["id"],
        "to_node_id": other_node["id"],
        "text": "Should fail",
        "order": 0
    }

    response = client.post(
        f"{settings.API_V1_STR}/node-choices",
        headers=superuser_token_headers,
        json=data
    )

    assert response.status_code == 400
    assert "end node" in response.json()["detail"].lower()