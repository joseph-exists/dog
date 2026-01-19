"""Tests for agent prompt extra context rendering."""
from __future__ import annotations

import uuid

from app.services.context_provider import RoomContext
from app.services.agent_prompt import build_agent_prompt


def test_build_agent_prompt_includes_extra_contexts() -> None:
    context = RoomContext(
        room_id=uuid.uuid4(),
        story_id=None,
        story_data=None,
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
