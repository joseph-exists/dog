from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ScriptFn = Callable[[dict[str, Any], Path, str, list[str]], list[Path]]
CapabilityResolver = Callable[[dict[str, Any], list[str]], set[str]]


@dataclass(slots=True)
class ScriptSpec:
    script_id: str
    kind: str
    default_runtime_profile: str
    enabled: bool = True
    disabled_reason: str | None = None
    base_capabilities: set[str] = field(default_factory=set)
    resolve_capabilities: CapabilityResolver | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "script_id": self.script_id,
            "kind": self.kind,
            "default_runtime_profile": self.default_runtime_profile,
            "enabled": self.enabled,
            "disabled_reason": self.disabled_reason,
            "base_capabilities": sorted(self.base_capabilities),
        }


_REGISTRY: dict[str, ScriptFn] = {}
_SPECS: dict[str, ScriptSpec] = {}


def register_script(
    script_id: str,
    *,
    kind: str = "render",
    default_runtime_profile: str = "core",
    enabled: bool = True,
    disabled_reason: str | None = None,
    base_capabilities: set[str] | None = None,
    resolve_capabilities: CapabilityResolver | None = None,
) -> Callable[[ScriptFn], ScriptFn]:
    def decorator(func: ScriptFn) -> ScriptFn:
        if script_id in _REGISTRY:
            raise ValueError(f"Script ID already registered: {script_id}")
        _REGISTRY[script_id] = func
        _SPECS[script_id] = ScriptSpec(
            script_id=script_id,
            kind=kind,
            default_runtime_profile=default_runtime_profile,
            enabled=enabled,
            disabled_reason=disabled_reason,
            base_capabilities=base_capabilities or set(),
            resolve_capabilities=resolve_capabilities,
        )
        return func

    return decorator


def get_script(script_id: str) -> ScriptFn:
    try:
        return _REGISTRY[script_id]
    except KeyError as exc:
        known = ", ".join(sorted(_REGISTRY)) or "<none>"
        raise KeyError(f"Unknown script_id '{script_id}'. Known scripts: {known}") from exc


def get_script_spec(script_id: str) -> ScriptSpec:
    try:
        return _SPECS[script_id]
    except KeyError as exc:
        known = ", ".join(sorted(_SPECS)) or "<none>"
        raise KeyError(f"Unknown script_id '{script_id}'. Known scripts: {known}") from exc


def list_scripts() -> list[str]:
    return sorted(_REGISTRY)


def list_script_specs() -> list[ScriptSpec]:
    return [_SPECS[script_id] for script_id in sorted(_SPECS)]

