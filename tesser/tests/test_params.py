from __future__ import annotations

import json

import pytest

from tesserax.errors import RenderConfigError
from tesserax.params import ParameterSchema, ParameterSpec


def _schema() -> ParameterSchema:
    return ParameterSchema(
        [
            ParameterSpec("layout.width", 1280, stability="stable"),
            ParameterSpec("layout.height", 720, stability="stable"),
            ParameterSpec("export.format", "svg", allowed=("svg", "gif"), stability="stable"),
            ParameterSpec("motion.mode", "steady", allowed=("steady", "pulse"), stability="experimental"),
        ]
    )


def test_parameter_schema_applies_defaults_and_validation() -> None:
    schema = _schema()
    out = schema.validate({"layout.width": 1440})
    assert out["layout.width"] == 1440
    assert out["layout.height"] == 720
    assert out["export.format"] == "svg"
    assert out["motion.mode"] == "steady"


def test_parameter_schema_rejects_invalid_allowed_value() -> None:
    schema = _schema()
    with pytest.raises(RenderConfigError) as exc:
        schema.validate({"export.format": "pdf"})
    msg = str(exc.value)
    assert "parameter='export.format'" in msg
    assert "invalid_value='pdf'" in msg
    assert "allowed=" in msg
    assert "suggested_fix=" in msg


def test_parameter_schema_rejects_unknown_non_extras_key() -> None:
    schema = _schema()
    with pytest.raises(RenderConfigError) as exc:
        schema.validate({"layout.depth": 4})
    msg = str(exc.value)
    assert "parameter='unknown_keys'" in msg
    assert "invalid_value=['layout.depth']" in msg
    assert "allowed=" in msg
    assert "suggested_fix=" in msg


def test_parameter_schema_allows_extras_prefix_and_round_trip() -> None:
    schema = _schema()
    payload = {
        "layout.width": 1400,
        "export.format": "gif",
        "motion.mode": "pulse",
        "extras.story.variant": "dense",
    }
    encoded = schema.to_json(payload)
    decoded = schema.from_json(encoded)
    assert decoded["layout.width"] == 1400
    assert decoded["layout.height"] == 720
    assert decoded["export.format"] == "gif"
    assert decoded["motion.mode"] == "pulse"
    assert decoded["extras.story.variant"] == "dense"

    # Ensure serialized output is stable object JSON.
    parsed = json.loads(encoded)
    assert isinstance(parsed, dict)
