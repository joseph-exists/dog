"""Tests for NonStreamingAgentRunner."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services.agent_runner_non_streaming import NonStreamingAgentRunner
from app.services.agent_runner_types import AgentRunRequest


class _ContextService:
    async def build(self, *, room_id, session, message_limit: int = 20, agent_slug=None):
        return object()


class _EventPublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []

    async def emit_message(self, *, session, room_id, agent_name, content, ui_components=None):
        self.messages.append(
            {"room_id": str(room_id), "agent_name": agent_name, "content": content}
        )


class _Agent:
    async def run(self, prompt: str):
        return SimpleNamespace(output="hello world")


@pytest.mark.asyncio
async def test_non_streaming_runner_success() -> None:
    context_service = _ContextService()
    event_publisher = _EventPublisher()

    async def is_agent_available(session, agent_name: str) -> bool:
        return True

    async def get_agent_instance(session, agent_name: str):
        return _Agent()

    def build_agent_prompt(trigger_message, context, current_agent_slug=None) -> str:  # noqa: ARG001
        return f"prompt:{trigger_message}"

    runner = NonStreamingAgentRunner(
        context_service=context_service,
        event_publisher=event_publisher,
        is_agent_available=is_agent_available,
        get_agent_instance=get_agent_instance,
        build_agent_prompt=build_agent_prompt,
    )

    result = await runner.run(
        req=AgentRunRequest(
            room_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            agent_slug="story-advisor",
            trigger_message="hi",
        ),
        session=None,
    )

    assert result.success is True
    assert result.content == "hello world"
    assert event_publisher.messages
