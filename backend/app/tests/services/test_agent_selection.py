"""Tests for AgentSelectionService mention parsing and participation modes."""
from __future__ import annotations

import pytest

from app.models import UserAgentConfig
from app.services.agent_selection import AgentSelectionService


@pytest.mark.parametrize(
    ("trigger_message", "expected"),
    [
        ("Hi @story-advisor", True),
        ('Hi @"Story Advisor"', True),
        ("Hi @StoryAdvisor", True),
        ("Hi there", False),
    ],
)
def test_on_mention_participation_modes(trigger_message: str, expected: bool) -> None:
    service = AgentSelectionService()
    config = UserAgentConfig(
        name="Story Advisor",
        slug="story-advisor",
        participation_mode="on_mention",
        model_name="openai:gpt-4o-mini",
    )

    should_respond, reason = service.should_agent_respond_to_message(
        config=config,
        trigger_message=trigger_message,
    )

    assert should_respond is expected
    if expected:
        assert reason == "mentioned in message"
    else:
        assert reason == "not mentioned (mode=on_mention)"


@pytest.mark.parametrize(
    ("participation_mode", "expected", "reason"),
    [
        ("always", True, "mode=always"),
        ("manual", False, "mode=manual (requires explicit invocation)"),
    ],
)
def test_participation_modes(participation_mode: str, expected: bool, reason: str) -> None:
    service = AgentSelectionService()
    config = UserAgentConfig(
        name="Story Advisor",
        slug="story-advisor",
        participation_mode=participation_mode,
        model_name="openai:gpt-4o-mini",
    )

    should_respond, actual_reason = service.should_agent_respond_to_message(
        config=config,
        trigger_message="Hi there",
    )

    assert should_respond is expected
    assert actual_reason == reason
