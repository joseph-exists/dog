from __future__ import annotations

import uuid

import pytest

from app.core.provider_types import TYPE1
from app.models import Type1Create


def _base_payload() -> dict:
    return {
        "name": "Agent One",
        "slug": "agent-one",
        "description": "desc",
        "provider_type": TYPE1,
        "system_prompt": "You are helpful.",
        "model_name": "gpt-4o-mini",
    }


def test_prompt_binding_latest_clears_version_number() -> None:
    payload = {
        **_base_payload(),
        "prompt_config_id": str(uuid.uuid4()),
        "prompt_config_version_policy": "latest",
        "prompt_config_version_number": 3,
    }
    model = Type1Create.model_validate(payload)
    assert model.prompt_config_version_policy == "latest"
    assert model.prompt_config_version_number is None


def test_prompt_binding_pinned_requires_version_number() -> None:
    payload = {
        **_base_payload(),
        "prompt_config_id": str(uuid.uuid4()),
        "prompt_config_version_policy": "pinned",
    }
    with pytest.raises(ValueError):
        Type1Create.model_validate(payload)


def test_prompt_binding_without_prompt_id_clears_version_number() -> None:
    payload = {
        **_base_payload(),
        "prompt_config_id": None,
        "prompt_config_version_policy": "pinned",
        "prompt_config_version_number": 7,
    }
    model = Type1Create.model_validate(payload)
    assert model.prompt_config_id is None
    assert model.prompt_config_version_number is None
