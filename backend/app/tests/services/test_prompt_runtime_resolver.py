from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from app.models import PromptConfigDraft
from app.services.prompt_runtime_resolver import resolve_effective_prompt_runtime_config


def _agent_stub() -> SimpleNamespace:
    return SimpleNamespace(
        slug="demo-agent",
        model="gpt-4o-mini",
        model_name="gpt-4o-mini",
        system_prompt="Base system prompt",
        custom_system_prompt=None,
        instructions="Base instructions",
        user_access_provider=uuid4(),
        provider_type=uuid4(),
        tool_config={"enable_tools": False, "require_tools": False, "allowed_tools": []},
        deps_config=None,
        max_tool_iterations=10,
    )


def _draft_payload(
    *,
    model_id: str = "gpt-4.1-mini",
    system: str = "Prompt system",
    user_message: str = "Prompt user message",
    provider_id: str | None = None,
) -> PromptConfigDraft:
    return PromptConfigDraft.model_validate(
        {
            "provider": {
                "user_access_provider_id": provider_id,
                "provider_type_id": None,
                "provider_kind": "openai_compatible",
                "base_url": None,
                "account_label": None,
            },
            "model": {
                "model_catalog_id": None,
                "model_id": model_id,
                "model_name": model_id,
                "model_family": "gpt",
            },
            "input": {
                "kind": "messages",
                "system": system,
                "messages": [{"role": "user", "content": user_message}],
            },
            "params": {"provider_kind": "openai_compatible"},
            "tools": {
                "tool_mode": "required",
                "tool_allowlist": ["search_docs"],
                "tool_choice": "search_docs",
                "max_tool_calls": 3,
            },
            "metadata": {},
        }
    )


def test_resolver_uses_agent_base_when_no_prompt_layers() -> None:
    agent = _agent_stub()
    resolved = resolve_effective_prompt_runtime_config(agent_config=agent)
    assert resolved.payload["model_name"] == "gpt-4o-mini"
    assert resolved.payload["instructions"] == "Base instructions"
    assert resolved.payload["max_tool_iterations"] == 10
    assert resolved.provenance["model_name"] == "user_agent_config"
    assert resolved.provenance["max_tool_iterations"] == "user_agent_config"


def test_resolver_applies_bound_prompt_patch() -> None:
    agent = _agent_stub()
    bound = _draft_payload(model_id="gpt-4.1")
    resolved = resolve_effective_prompt_runtime_config(
        agent_config=agent,
        bound_prompt=bound,
    )
    assert resolved.payload["model"] == "gpt-4.1"
    assert resolved.payload["custom_system_prompt"] == "Prompt system"
    assert resolved.payload["tool_config"]["require_tools"] is True
    assert resolved.provenance["model"] == "bound_prompt_config"
    assert resolved.payload["max_tool_iterations"] == 10
    assert resolved.provenance["max_tool_iterations"] == "user_agent_config"


def test_resolver_room_agent_override_wins_over_room_defaults_and_bound() -> None:
    agent = _agent_stub()
    bound = _draft_payload(model_id="gpt-4.1")
    room_defaults = _draft_payload(model_id="gpt-4.1-mini", system="Room default system")
    room_agent = _draft_payload(model_id="gpt-4.1-nano", system="Room agent system")

    resolved = resolve_effective_prompt_runtime_config(
        agent_config=agent,
        bound_prompt=bound,
        room_defaults_prompt=room_defaults,
        room_agent_prompt=room_agent,
    )

    assert resolved.payload["model"] == "gpt-4.1-nano"
    assert resolved.payload["custom_system_prompt"] == "Room agent system"
    assert resolved.provenance["model"] == "room_agent_override"
    assert resolved.provenance["custom_system_prompt"] == "room_agent_override"
