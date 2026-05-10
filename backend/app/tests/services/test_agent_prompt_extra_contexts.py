"""Tests for agent prompt extra context rendering."""
from __future__ import annotations

import uuid

from app.services.agent_prompt import build_agent_prompt
from app.services.context_provider import RoomContext


def test_build_agent_prompt_includes_extra_contexts() -> None:
    context = RoomContext(
        room_id=uuid.uuid4(),
        story_id=None,
        story_data=None,
        story_runtime=None,
        recent_messages=[],
        participants=[],
        room_metadata={},
        active_agents=[],
        extra_contexts=[
            {"context_type": "upload", "payload": {"doc": "text"}, "source": "frontend"}
        ],
    )

    prompt = build_agent_prompt("hello", context, current_agent_slug=None)
    assert "Additional context:" in prompt
    assert "upload" in prompt


def test_build_agent_prompt_omits_current_agent_shadow_audit_metadata() -> None:
    agent_id = str(uuid.uuid4())
    context = RoomContext(
        room_id=uuid.uuid4(),
        story_id=None,
        story_data=None,
        story_runtime=None,
        recent_messages=[],
        participants=[],
        room_metadata={},
        active_agents=[],
        extra_contexts=[
            {
                "context_type": "shadow.agent.summary",
                "source": "shadow",
                "payload": {
                    "entity_type": "agent",
                    "entity_id": agent_id,
                    "version_number": 3,
                    "commit_sha": "abc123",
                    "source": "db",
                    "is_stale": True,
                    "summary": {
                        "agent": {
                            "id": agent_id,
                            "slug": "qwen-agent",
                            "name": "Qwenzorius",
                            "description": "Qwen the mighty",
                            "participation_mode": "always",
                            "capabilities": [],
                        },
                        "agent_personas": [],
                    },
                },
            }
        ],
    )

    prompt = build_agent_prompt("hello", context, current_agent_slug="qwen-agent")

    assert "shadow.agent.summary" not in prompt
    assert "commit_sha" not in prompt
    assert "entity_id" not in prompt
    assert prompt == "hello"


def test_build_agent_prompt_sanitizes_non_self_shadow_summary() -> None:
    agent_id = str(uuid.uuid4())
    context = RoomContext(
        room_id=uuid.uuid4(),
        story_id=None,
        story_data=None,
        story_runtime=None,
        recent_messages=[],
        participants=[],
        room_metadata={},
        active_agents=[],
        extra_contexts=[
            {
                "context_type": "shadow.agent.summary",
                "source": "shadow",
                "payload": {
                    "entity_type": "agent",
                    "entity_id": agent_id,
                    "version_number": 3,
                    "commit_sha": "abc123",
                    "source": "db",
                    "is_stale": True,
                    "summary": {
                        "agent": {
                            "id": agent_id,
                            "slug": "reviewer",
                            "name": "Reviewer",
                            "description": "Reviews code",
                            "participation_mode": "always",
                            "capabilities": ["review"],
                        },
                        "agent_personas": [],
                    },
                },
            }
        ],
    )

    prompt = build_agent_prompt("hello", context, current_agent_slug="qwen-agent")

    assert "Agent summary - Reviewer: Reviews code." in prompt
    assert "Capabilities: review." in prompt
    assert "commit_sha" not in prompt
    assert "entity_id" not in prompt
