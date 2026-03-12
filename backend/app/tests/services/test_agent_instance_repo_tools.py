from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services import agent_instance


@pytest.mark.asyncio
async def test_repo_tools_enabled_via_tool_config(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["tools"] = kwargs.get("tools") or []

    async def fake_get_agent_config(session, slug):  # noqa: ARG001
        return SimpleNamespace(
            slug=slug,
            name="Repo Agent",
            description="",
            enable_a2a_tool=False,
            enable_ag_ui_tool=False,
            tool_config={"enabled_tools": ["read_repo_file", "write_repo_files"]},
        )

    async def fake_resolve_effective_prompt_runtime_config_for_room(*, session, agent_config, room_id):  # noqa: ARG001
        return SimpleNamespace(
            payload={
                "model_name": "gpt-4.1-mini",
                "tool_config": {"enabled_tools": ["read_repo_file", "write_repo_files"]},
            },
            provenance={"tool_config": "agent"},
        )

    async def fake_provider_type(session, slug):  # noqa: ARG001
        return "openai"

    monkeypatch.setattr(agent_instance, "Agent", FakeAgent)
    monkeypatch.setattr(agent_instance, "get_agent_config", fake_get_agent_config)
    monkeypatch.setattr(
        agent_instance,
        "resolve_effective_prompt_runtime_config_for_room",
        fake_resolve_effective_prompt_runtime_config_for_room,
    )
    monkeypatch.setattr(
        agent_instance,
        "get_user_agent_config_provider_type_name_for_model_concat_by_slug",
        fake_provider_type,
    )
    monkeypatch.setattr(
        agent_instance,
        "create_model_subclass_with_credentials",
        lambda **kwargs: kwargs["model_name"],
    )
    monkeypatch.setattr(agent_instance.settings, "AGENT_REPO_TOOLS_ENABLED", True)

    _agent = await agent_instance.get_agent_instance_with_tools(
        session=None,  # type: ignore[arg-type]
        slug="repo-agent",
        user_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
    )

    tools = captured["tools"]
    assert isinstance(tools, list)
    tool_names = {getattr(t, "__name__", "") for t in tools}
    assert "read_repo_file" in tool_names
    assert "write_repo_files" in tool_names


@pytest.mark.asyncio
async def test_repo_tools_disabled_by_kill_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, **kwargs):
            captured["tools"] = kwargs.get("tools") or []

    async def fake_get_agent_config(session, slug):  # noqa: ARG001
        return SimpleNamespace(
            slug=slug,
            name="Repo Agent",
            description="",
            enable_a2a_tool=False,
            enable_ag_ui_tool=False,
            tool_config={"enabled_tools": ["read_repo_file", "write_repo_files"]},
        )

    async def fake_resolve_effective_prompt_runtime_config_for_room(*, session, agent_config, room_id):  # noqa: ARG001
        return SimpleNamespace(
            payload={
                "model_name": "gpt-4.1-mini",
                "tool_config": {"enabled_tools": ["read_repo_file", "write_repo_files"]},
            },
            provenance={"tool_config": "agent"},
        )

    async def fake_provider_type(session, slug):  # noqa: ARG001
        return "openai"

    monkeypatch.setattr(agent_instance, "Agent", FakeAgent)
    monkeypatch.setattr(agent_instance, "get_agent_config", fake_get_agent_config)
    monkeypatch.setattr(
        agent_instance,
        "resolve_effective_prompt_runtime_config_for_room",
        fake_resolve_effective_prompt_runtime_config_for_room,
    )
    monkeypatch.setattr(
        agent_instance,
        "get_user_agent_config_provider_type_name_for_model_concat_by_slug",
        fake_provider_type,
    )
    monkeypatch.setattr(
        agent_instance,
        "create_model_subclass_with_credentials",
        lambda **kwargs: kwargs["model_name"],
    )
    monkeypatch.setattr(agent_instance.settings, "AGENT_REPO_TOOLS_ENABLED", False)

    _agent = await agent_instance.get_agent_instance_with_tools(
        session=None,  # type: ignore[arg-type]
        slug="repo-agent",
        user_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
    )

    tools = captured["tools"]
    assert isinstance(tools, list)
    tool_names = {getattr(t, "__name__", "") for t in tools}
    assert "read_repo_file" not in tool_names
    assert "write_repo_files" not in tool_names
