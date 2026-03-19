from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest

from app.services import agent_instance


class _FakeFastMCPToolset:
    def __init__(self, client, *, id=None, max_retries=1, tool_error_behavior="model_retry"):  # noqa: ARG002
        self.client = client
        self.id = id


class _FakeFilteredToolset:
    def __init__(self, *, wrapped, filter_func):
        self.wrapped = wrapped
        self.filter_func = filter_func


class _FakeApprovalRequiredToolset:
    def __init__(self, *, wrapped, approval_required_func=None):
        self.wrapped = wrapped
        self.approval_required_func = approval_required_func


def _base_config(*, slug: str, toolsets: list[object] | None = None) -> SimpleNamespace:
    return SimpleNamespace(
        slug=slug,
        name="MCP Agent",
        description="",
        enable_a2a_tool=False,
        enable_ag_ui_tool=False,
        tool_config=None,
        toolsets=toolsets,
    )


def _resolved_payload(tool_config: dict) -> SimpleNamespace:
    return SimpleNamespace(
        payload={
            "model_name": "gpt-4.1-mini",
            "tool_config": tool_config,
        },
        provenance={"tool_config": "prompt_config"},
    )


def _install_common_mocks(
    monkeypatch: pytest.MonkeyPatch,
    *,
    config: SimpleNamespace,
    resolved: SimpleNamespace,
    captured: dict[str, object],
) -> None:
    class FakeAgent:
        def __init__(self, **kwargs):
            captured["toolsets"] = kwargs.get("toolsets")
            captured["tools"] = kwargs.get("tools") or []

    async def fake_get_agent_config(session, slug):  # noqa: ARG001
        return config

    async def fake_resolve_effective_prompt_runtime_config_for_room(*, session, agent_config, room_id):  # noqa: ARG001
        return resolved

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


@pytest.mark.asyncio
async def test_mcp_toolset_uses_registry_descriptor_not_prompt_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    config = _base_config(slug="mcp-agent")
    resolved = _resolved_payload(
        {
            "mcp": {
                "servers": [
                    {
                        "id": "affordance",
                        "url": "https://evil.example.test/mcp",
                        "require_approval": "never",
                    }
                ]
            }
        }
    )

    _install_common_mocks(monkeypatch, config=config, resolved=resolved, captured=captured)
    monkeypatch.setattr(agent_instance, "FastMCPToolset", _FakeFastMCPToolset)
    monkeypatch.setattr(agent_instance, "FilteredToolset", _FakeFilteredToolset)
    monkeypatch.setattr(agent_instance, "ApprovalRequiredToolset", _FakeApprovalRequiredToolset)
    monkeypatch.setattr(
        agent_instance,
        "get_mcp_server_descriptor",
        lambda server_id: SimpleNamespace(
            id=server_id,
            url="http://mcpmvp:8080/mcp/affordance",
            enabled=True,
            require_approval_default="never",
        ),
    )

    agent = await agent_instance.get_agent_instance_with_tools(
        session=None,  # type: ignore[arg-type]
        slug="mcp-agent",
        user_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
    )

    toolsets = captured["toolsets"]
    assert isinstance(toolsets, list)
    assert len(toolsets) == 1
    toolset = toolsets[0]
    assert isinstance(toolset, _FakeFastMCPToolset)
    assert toolset.client == "http://mcpmvp:8080/mcp/affordance"
    assert toolset.id == "affordance"
    assert getattr(agent, "_runtime_mcp_attached_ids") == ["affordance"]
    assert getattr(agent, "_runtime_mcp_rejected_ids") == []


@pytest.mark.asyncio
async def test_mcp_toolset_wraps_allowlist_and_approval_and_preserves_existing_toolsets(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    existing_toolset = object()
    config = _base_config(slug="story-agent", toolsets=[existing_toolset])
    resolved = _resolved_payload(
        {
            "mcp": {
                "allowed_tools": ["ignored_global_tool"],
                "servers": [
                    {
                        "id": "story",
                        "allowed_tools": ["story_affordance_list"],
                        "require_approval": "always",
                    }
                ]
            }
        }
    )

    _install_common_mocks(monkeypatch, config=config, resolved=resolved, captured=captured)
    monkeypatch.setattr(agent_instance, "FastMCPToolset", _FakeFastMCPToolset)
    monkeypatch.setattr(agent_instance, "FilteredToolset", _FakeFilteredToolset)
    monkeypatch.setattr(agent_instance, "ApprovalRequiredToolset", _FakeApprovalRequiredToolset)
    monkeypatch.setattr(
        agent_instance,
        "get_mcp_server_descriptor",
        lambda server_id: SimpleNamespace(
            id=server_id,
            url="http://mcpmvp:8080/mcp/story",
            enabled=True,
            require_approval_default="never",
        ),
    )

    _agent = await agent_instance.get_agent_instance_with_tools(
        session=None,  # type: ignore[arg-type]
        slug="story-agent",
        user_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
    )

    toolsets = captured["toolsets"]
    assert isinstance(toolsets, list)
    assert len(toolsets) == 2
    assert toolsets[0] is existing_toolset
    wrapped = toolsets[1]
    assert isinstance(wrapped, _FakeApprovalRequiredToolset)
    assert isinstance(wrapped.wrapped, _FakeFilteredToolset)
    assert isinstance(wrapped.wrapped.wrapped, _FakeFastMCPToolset)
    filter_func = wrapped.wrapped.filter_func
    assert filter_func(None, SimpleNamespace(name="story_affordance_list")) is True
    assert filter_func(None, SimpleNamespace(name="story_affordance_get")) is False


@pytest.mark.asyncio
async def test_mcp_toolset_rejects_unknown_and_disabled_servers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    config = _base_config(slug="rejecting-agent")
    resolved = _resolved_payload(
        {
            "mcp": {
                "servers": [
                    {"id": "missing"},
                    {"id": "story"},
                ]
            }
        }
    )

    _install_common_mocks(monkeypatch, config=config, resolved=resolved, captured=captured)
    monkeypatch.setattr(agent_instance, "FastMCPToolset", _FakeFastMCPToolset)
    monkeypatch.setattr(agent_instance, "FilteredToolset", _FakeFilteredToolset)
    monkeypatch.setattr(agent_instance, "ApprovalRequiredToolset", _FakeApprovalRequiredToolset)

    def fake_get_descriptor(server_id: str):
        if server_id == "missing":
            return None
        return SimpleNamespace(
            id=server_id,
            url="http://mcpmvp:8080/mcp/story",
            enabled=False,
            require_approval_default="never",
        )

    monkeypatch.setattr(agent_instance, "get_mcp_server_descriptor", fake_get_descriptor)

    agent = await agent_instance.get_agent_instance_with_tools(
        session=None,  # type: ignore[arg-type]
        slug="rejecting-agent",
        user_id=uuid.uuid4(),
        room_id=uuid.uuid4(),
    )

    toolsets = captured["toolsets"]
    assert toolsets is None
    assert getattr(agent, "_runtime_mcp_attached_ids") == []
    assert getattr(agent, "_runtime_mcp_rejected_ids") == [
        "missing:unknown",
        "story:disabled",
    ]
