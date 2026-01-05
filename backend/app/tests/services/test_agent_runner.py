"""Tests for Agent Runner Service."""
import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch

from app.services.agent_runner import (
    run_agent_for_room,
    should_agent_respond,
    run_agents_for_message,
    run_story_advisor,
)


class TestAgentRunner:
    """Test suite for agent runner service."""

    @pytest.mark.asyncio
    async def test_run_agent_unregistered_returns_error(
        self, async_session, test_room
    ):
        """Should return error for unregistered agent."""
        result = await run_agent_for_room(
            room_id=test_room.room_id,
            agent_name="NonexistentAgent",
            trigger_message="Hello",
            session=async_session,
        )

        assert result["success"] is False
        assert "not found" in result["error"]

    # @pytest.mark.asyncio
    # async def test_run_agent_emits_event(
    #     self, async_session, test_room_with_agent
    # ):
    #     """Running agent should emit room_message.agent event."""
    #     with patch("app.services.agent_runner.run_story_advisor", new_callable=AsyncMock) as mock_run:
    #         mock_run.return_value = "Test response"

    #         result = await run_agent_for_room(
    #             room_id=test_room_with_agent.room_id,
    #             agent_name="StoryAdvisor",
    #             trigger_message="Help with my story",
    #             session=async_session,
    #         )

    #         assert result["success"] is True
    #         assert result["content"] == "Test response"

    @pytest.mark.asyncio
    async def test_should_agent_respond_active_participant(
        self, async_session, test_room_with_agent
    ):
        """Agent should respond if active participant."""
        should_respond = await should_agent_respond(
            room_id=test_room_with_agent.room_id,
            agent_name="StoryAdvisor",
            session=async_session,
        )

        assert should_respond is True

    @pytest.mark.asyncio
    async def test_should_agent_respond_not_participant(
        self, async_session, test_room
    ):
        """Agent should not respond if not participant."""
        should_respond = await should_agent_respond(
            room_id=test_room.room_id,
            agent_name="StoryAdvisor",
            session=async_session,
        )

        assert should_respond is False

#    @pytest.mark.asyncio
#    async def test_run_agents_for_message_triggers_all(
#        self, async_session, test_room_with_multiple_agents
#    ):
#        """Should run all active REGISTERED agents in room."""
#        with patch("app.services.agent_runner.run_agent_for_room") as mock_run:
#            mock_run.return_value = {"success": True, "content": "Response"}#
#
#            results = await run_agents_for_message(
#                room_id=test_room_with_multiple_agents.room_id,
#                trigger_message="Test message",
#                session=async_session,
#            )
#
#            # Should call run_agent_for_room only for registered agents
#            # Fixture has 2 agents: StoryAdvisor (registered) and TestAgent2 (not registered)
#            assert mock_run.call_count == 1  # Only StoryAdvisor is registered
#            assert len(results) == 1  # Only one agent responded
