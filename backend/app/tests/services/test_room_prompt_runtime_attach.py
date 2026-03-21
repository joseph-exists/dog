from __future__ import annotations

import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import app.crud as crud_module
from app.crud import list_room_agent_settings, upsert_room_agent_settings
from app.models import (
    PromptConfig,
    PromptConfigDraft,
    PromptConfigVersion,
    RoomAgentSettings,
    RoomAgentSettingsUpdate,
)
from app.services.prompt_runtime_resolver import _resolve_room_settings_prompt_patch


def _draft_payload(
    *,
    model_id: str,
    system: str,
    user_message: str,
) -> dict:
    draft = PromptConfigDraft.model_validate(
        {
            "provider": {
                "user_access_provider_id": None,
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
            "tools": {"tool_mode": "optional", "tool_allowlist": []},
            "metadata": {},
        }
    )
    return draft.model_dump(mode="json", exclude_none=True)


class _ExecResult:
    def __init__(self, *, first=None, one_or_none=None):
        self._first = first
        self._one_or_none = one_or_none

    def first(self):
        return self._first

    def one_or_none(self):
        return self._one_or_none


class _FakeSession:
    def __init__(
        self,
        *,
        prompt_config: PromptConfig | None = None,
        version: PromptConfigVersion | None = None,
        existing_settings=None,
    ) -> None:
        self.prompt_config = prompt_config
        self.version = version
        self.existing_settings = existing_settings
        self.added = []

    async def get(self, model, id_):
        if model is PromptConfig and self.prompt_config and self.prompt_config.id == id_:
            return self.prompt_config
        return None

    async def exec(self, stmt):
        query_text = str(stmt)
        if "prompt_config_versions" in query_text:
            return _ExecResult(first=self.version)
        if "room_agent_settings" in query_text:
            return _ExecResult(one_or_none=self.existing_settings)
        raise AssertionError(f"Unexpected query: {query_text}")

    def add(self, obj):
        self.added.append(obj)
        if obj.__class__.__name__ == "RoomAgentSettings":
            self.existing_settings = obj

    async def flush(self):
        return None


@pytest.mark.asyncio
async def test_room_prompt_config_reference_and_inline_overlay_merge() -> None:
    prompt_config = PromptConfig(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        slug="room-default-reference",
        name="room-default-reference",
        latest_version=1,
    )
    version = PromptConfigVersion(
        id=uuid.uuid4(),
        prompt_config_id=prompt_config.id,
        version_number=1,
        payload_json=_draft_payload(
            model_id="gpt-4.1",
            system="Referenced room system",
            user_message="Referenced instructions",
        ),
        created_by=prompt_config.owner_id,
    )
    session = _FakeSession(prompt_config=prompt_config, version=version)
    room_settings = SimpleNamespace(
        prompt_config_id=prompt_config.id,
        prompt_config_version_policy="latest",
        prompt_config_version_number=None,
        prompt_config=_draft_payload(
            model_id="",
            system="Inline room system",
            user_message="Inline instructions",
        ),
    )

    patch = await _resolve_room_settings_prompt_patch(
        session=session,
        room_settings=room_settings,
        owner_id=prompt_config.owner_id,
        source_prefix="room_defaults",
    )

    assert patch is not None
    assert patch.payload["model"] == "gpt-4.1"
    assert patch.payload["custom_system_prompt"] == "Inline room system"
    assert patch.payload["instructions"] == "[user] Inline instructions"
    assert patch.provenance["model"] == "room_defaults_prompt_config"
    assert patch.provenance["custom_system_prompt"] == "room_defaults_inline_override"
    assert patch.provenance["instructions"] == "room_defaults_inline_override"


@pytest.mark.asyncio
async def test_upsert_room_agent_settings_can_clear_prompt_binding_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_config = PromptConfig(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        slug="room-agent-reference",
        name="room-agent-reference",
        latest_version=1,
    )
    session = _FakeSession(prompt_config=prompt_config)

    async def _true(*args, **kwargs):
        return True

    async def _noop_emit_event(*args, **kwargs):
        return None

    monkeypatch.setattr(crud_module, "check_room_membership", _true)
    monkeypatch.setattr(crud_module, "check_room_owner", _true)
    monkeypatch.setattr(crud_module, "emit_event", _noop_emit_event)

    created = await upsert_room_agent_settings(
        room_id=uuid.uuid4(),
        user_id=prompt_config.owner_id,
        agent_slug="story-advisor",
        settings_in=RoomAgentSettingsUpdate(
            prompt_config_id=prompt_config.id,
            prompt_config_version_policy="pinned",
            prompt_config_version_number=1,
            tool_policy={"mode": "strict"},
        ),
        session=session,
    )

    cleared = await upsert_room_agent_settings(
        room_id=uuid.uuid4(),
        user_id=prompt_config.owner_id,
        agent_slug="story-advisor",
        settings_in=RoomAgentSettingsUpdate(
            prompt_config_id=None,
            prompt_config_version_policy=None,
            prompt_config_version_number=None,
            prompt_config=None,
            expected_revision=created.revision,
        ),
        session=session,
    )

    assert cleared.prompt_config_id is None
    assert cleared.prompt_config_version_policy is None
    assert cleared.prompt_config_version_number is None
    assert cleared.prompt_config is None
    assert cleared.tool_policy == {"mode": "strict"}


@pytest.mark.asyncio
async def test_upsert_room_agent_settings_rejects_foreign_prompt_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompt_config = PromptConfig(
        id=uuid.uuid4(),
        owner_id=uuid.uuid4(),
        slug="foreign-reference",
        name="foreign-reference",
        latest_version=1,
    )
    session = _FakeSession(prompt_config=prompt_config)

    async def _true(*args, **kwargs):
        return True

    monkeypatch.setattr(crud_module, "check_room_membership", _true)
    monkeypatch.setattr(crud_module, "check_room_owner", _true)

    with pytest.raises(HTTPException) as exc_info:
        await upsert_room_agent_settings(
            room_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            agent_slug=None,
            settings_in=RoomAgentSettingsUpdate(
                prompt_config_id=prompt_config.id,
                prompt_config_version_policy="latest",
            ),
            session=session,
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied for PromptConfig binding"


@pytest.mark.asyncio
async def test_list_room_agent_settings_returns_bundle_without_participant_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    room_id = uuid.uuid4()
    owner_id = uuid.uuid4()
    room_defaults = RoomAgentSettings(
        id=uuid.uuid4(),
        room_id=room_id,
        agent_slug=None,
        revision=0,
    )
    agent_override = RoomAgentSettings(
        id=uuid.uuid4(),
        room_id=room_id,
        agent_slug="story-advisor",
        revision=1,
    )
    session = _FakeSession(existing_settings=None)

    async def fake_exec(stmt):
        query_text = str(stmt)
        if "room_agent_settings" in query_text:
            return _ExecResult(first=None, one_or_none=None)
        raise AssertionError(f"Unexpected query: {query_text}")

    session.exec = fake_exec  # type: ignore[method-assign]

    async def _true(*args, **kwargs):
        return True

    monkeypatch.setattr(crud_module, "check_room_membership", _true)

    async def fake_session_exec(stmt):
        query_text = str(stmt)
        if "room_agent_settings" in query_text:
            return SimpleNamespace(all=lambda: [room_defaults, agent_override])
        raise AssertionError(f"Unexpected query: {query_text}")

    session.exec = fake_session_exec  # type: ignore[method-assign]

    bundle = await list_room_agent_settings(
        room_id=room_id,
        user_id=owner_id,
        session=session,  # type: ignore[arg-type]
    )

    assert bundle.room_defaults is not None
    assert bundle.room_defaults.agent_slug is None
    assert len(bundle.agent_overrides) == 1
    assert bundle.agent_overrides[0].agent_slug == "story-advisor"
