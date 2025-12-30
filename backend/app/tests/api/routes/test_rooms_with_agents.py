"""Integration tests for rooms API with agent functionality."""
import pytest
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient

from app.core.config import settings


class TestRoomsWithAgents:
    """Integration tests for agent features in rooms API."""

    def test_send_message_triggers_agents(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        api_test_room_with_agent,
    ):
        """Sending message should trigger agent responses."""
        with patch("app.api.routes.rooms.run_agents_for_message") as mock_run:
            mock_run.return_value = [{"success": True, "content": "Agent response"}]

            response = client.post(
                f"{settings.API_V1_STR}/rooms/{api_test_room_with_agent.room_id}/messages",
                headers=superuser_token_headers,
                json={"content": "Please help with my story"},
            )

            assert response.status_code == 200
            mock_run.assert_called_once()

    def test_add_agent_participant(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        api_test_room,
    ):
        """Should be able to add agent as participant."""
        response = client.post(
            f"{settings.API_V1_STR}/rooms/{api_test_room.room_id}/participants",
            headers=superuser_token_headers,
            json={
                "participant_id": "StoryAdvisor",
                "participant_type": "agent",
                "role": "member",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["participant_id"] == "StoryAdvisor"
        assert data["participant_type"] == "agent"

    def test_list_participants_includes_agents(
        self,
        client: TestClient,
        superuser_token_headers: dict[str, str],
        api_test_room_with_agent,
    ):
        """Participant list should include agents."""
        response = client.get(
            f"{settings.API_V1_STR}/rooms/{api_test_room_with_agent.room_id}/participants",
            headers=superuser_token_headers,
        )

        assert response.status_code == 200
        data = response.json()

        agent_participants = [
            p for p in data["data"]
            if p["participant_type"] == "agent"
        ]
        assert len(agent_participants) > 0
