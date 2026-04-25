from __future__ import annotations

import uuid

from app.services.agent_invocation_audit import (
    hash_prompt,
    redact_prompt,
    serialize_room_context,
)
from app.services.context_provider import AgentInfo, RoomContext, StoryRuntimeContext


def test_serialize_room_context_includes_story_runtime() -> None:
    room_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    story_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
    context = RoomContext(
        room_id=room_id,
        story_id=story_id,
        story_data={"id": str(story_id), "title": "A Fine Scene"},
        story_runtime=StoryRuntimeContext(
            current_node_title="Threshold",
            current_node_content="A door waits.",
            current_node_type="scene",
            is_end_node=False,
            node_chain=["Start", "Threshold"],
            available_choices=["Open it"],
            story_state={"has_key": True},
        ),
        recent_messages=[{"content": "hello"}],
        participants=[{"participant_id": str(room_id)}],
        room_metadata={"title": "Room"},
        active_agents=[
            AgentInfo(
                slug="guide",
                name="Guide",
                description="Helpful",
                participation_mode="manual",
                capabilities=["story"],
            )
        ],
        extra_contexts=[{"context_type": "note", "payload": {"safe": True}}],
    )

    data = serialize_room_context(context)

    assert data["room_id"] == str(room_id)
    assert data["story_id"] == str(story_id)
    assert data["story_runtime"]["current_node_title"] == "Threshold"
    assert data["active_agents"][0]["slug"] == "guide"


def test_hash_prompt_is_stable() -> None:
    assert hash_prompt("same prompt") == hash_prompt("same prompt")
    assert hash_prompt("same prompt") != hash_prompt("different prompt")


def test_redact_prompt_is_deterministic() -> None:
    prompt = "secret-ish prompt"
    assert redact_prompt(prompt) == redact_prompt(prompt)
