"""Tests for StreamingAgentRunner."""
from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services.agent_runner_streaming import StreamingAgentRunner
from app.services.agent_runner_types import AgentRunRequest


class _ContextService:
    async def build(self, *, room_id, session, message_limit: int = 20, agent_slug=None):
        return object()


class _EventPublisher:
    def __init__(self) -> None:
        self.messages: list[dict[str, str]] = []
        self.tokens: list[str] = []

    async def publish_token(self, *, room_id, agent_name, token):
        self.tokens.append(token)

    async def emit_message(self, *, session, room_id, agent_name, content, ui_components=None):
        self.messages.append(
            {"room_id": str(room_id), "agent_name": agent_name, "content": content}
        )


class _StreamingResult:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def stream_text(self):
        for chunk in ["hel", "hello"]:
            yield chunk


class _Agent:
    def __init__(self, request_limit: int) -> None:
        self.model = "gpt-4.1-mini"
        self._runtime_request_limit = request_limit
        self.seen_request_limit: int | None = None

    def run_stream(self, prompt: str, *, deps, usage_limits):
        self.seen_request_limit = usage_limits.request_limit
        return _StreamingResult()


class _A2AOrchestrator:
    async def process_mentions(self, **kwargs):
        return []


@pytest.mark.asyncio
async def test_streaming_runner_uses_resolved_runtime_request_limit() -> None:
    context_service = _ContextService()
    event_publisher = _EventPublisher()
    agent = _Agent(request_limit=7)

    async def is_agent_available(session, agent_name: str) -> bool:
        return True

    async def get_agent_instance_with_tools(
        session, agent_name: str, user_id=None, enable_a2a_tool=False, enable_ag_ui_tool=False, room_id=None  # noqa: ARG001
    ):
        return agent

    def build_agent_prompt(trigger_message, context, current_agent_slug=None) -> str:  # noqa: ARG001
        return f"prompt:{trigger_message}"

    def deps_factory(session, room_id, agent_name, depth, acting_user_id):  # noqa: ARG001
        return SimpleNamespace(ui_components=[])

    async def run_agent(**kwargs):
        return {"success": True}

    runner = StreamingAgentRunner(
        context_service=context_service,
        event_publisher=event_publisher,
        is_agent_available=is_agent_available,
        get_agent_instance_with_tools=get_agent_instance_with_tools,
        build_agent_prompt=build_agent_prompt,
        deps_factory=deps_factory,
        a2a_orchestrator=_A2AOrchestrator(),
        run_agent=run_agent,
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
    assert result.content == "hello"
    assert event_publisher.tokens == ["hel", "lo"]
    assert event_publisher.messages
    assert agent.seen_request_limit == 7
