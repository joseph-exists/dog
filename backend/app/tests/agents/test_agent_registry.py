"""Tests for Agent Registry."""
import pytest
from unittest.mock import MagicMock

from app.agents.agent_registry import (
    AGENT_REGISTRY,
    register_agent,
    get_agent,
    list_agents,
    is_agent_registered,
)


class TestAgentRegistry:
    """Test suite for agent registry."""

    def setup_method(self):
        """Clear registry before each test."""
        AGENT_REGISTRY.clear()

    def test_register_agent(self):
        """Should register agent successfully."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        assert "TestAgent" in AGENT_REGISTRY
        assert AGENT_REGISTRY["TestAgent"] is mock_agent

    def test_register_duplicate_raises(self):
        """Should raise error when registering duplicate name."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        with pytest.raises(ValueError, match="already registered"):
            register_agent("TestAgent", MagicMock())

    def test_get_agent(self):
        """Should return registered agent."""
        mock_agent = MagicMock()
        register_agent("TestAgent", mock_agent)

        result = get_agent("TestAgent")
        assert result is mock_agent

    def test_get_nonexistent_agent_raises(self):
        """Should raise KeyError for unregistered agent."""
        with pytest.raises(KeyError, match="not found"):
            get_agent("NonexistentAgent")

    def test_list_agents(self):
        """Should return list of registered agent names."""
        register_agent("Agent1", MagicMock())
        register_agent("Agent2", MagicMock())

        names = list_agents()
        assert "Agent1" in names
        assert "Agent2" in names

    def test_is_agent_registered(self):
        """Should correctly report registration status."""
        register_agent("TestAgent", MagicMock())

        assert is_agent_registered("TestAgent") is True
        assert is_agent_registered("OtherAgent") is False
