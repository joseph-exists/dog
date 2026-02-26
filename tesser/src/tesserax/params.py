from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal

from .errors import RenderConfigError, actionable_error

type Stability = Literal["stable", "experimental"]


@dataclass(frozen=True, slots=True)
class ParameterSpec:
    key: str
    default: Any
    allowed: tuple[Any, ...] | None = None
    stability: Stability = "stable"

    def validate(self, value: Any) -> Any:
        if self.allowed is not None and value not in self.allowed:
            allowed = ", ".join(str(v) for v in self.allowed)
            raise RenderConfigError(
                actionable_error(
                    parameter=self.key,
                    invalid_value=value,
                    allowed=allowed,
                    suggested_fix=f"Set {self.key} to one of: {allowed}.",
                )
            )
        return value


class ParameterSchema:
    """Namespaced parameter schema with metadata + extras pass-through."""

    def __init__(
        self,
        specs: list[ParameterSpec],
        *,
        extras_prefix: str = "extras.",
    ) -> None:
        self._specs = {s.key: s for s in specs}
        self._extras_prefix = extras_prefix

    @property
    def specs(self) -> dict[str, ParameterSpec]:
        return dict(self._specs)

    def validate(self, values: dict[str, Any]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        unknown: list[str] = []

        for key, spec in self._specs.items():
            value = values.get(key, spec.default)
            out[key] = spec.validate(value)

        for key, value in values.items():
            if key in self._specs:
                continue
            if key.startswith(self._extras_prefix):
                out[key] = value
                continue
            unknown.append(key)

        if unknown:
            raise RenderConfigError(
                actionable_error(
                    parameter="unknown_keys",
                    invalid_value=sorted(unknown),
                    allowed="known schema keys or extras.*",
                    suggested_fix=f"Rename unknown keys or prefix advanced keys with '{self._extras_prefix}'.",
                )
            )

        return out

    def to_json(self, values: dict[str, Any]) -> str:
        validated = self.validate(values)
        return json.dumps(validated, sort_keys=True, separators=(",", ":"))

    def from_json(self, payload: str) -> dict[str, Any]:
        parsed = json.loads(payload)
        if not isinstance(parsed, dict):
            raise RenderConfigError(
                actionable_error(
                    parameter="payload",
                    invalid_value=type(parsed).__name__,
                    allowed="JSON object",
                    suggested_fix="Provide a JSON object mapping parameter keys to values.",
                )
            )
        return self.validate(parsed)
