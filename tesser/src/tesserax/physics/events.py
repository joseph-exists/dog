from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass(frozen=True)
class PhysicsEvent:
    type: str
    timestamp: float
    step_index: int
    entities: tuple[str, ...]
    metadata: dict[str, object] = field(default_factory=dict)
    emission_order: int = 0
    schema_version: str = "1.0.0"


class EventDispatcher:
    """Best-effort event dispatcher with isolated handler failures."""

    def __init__(self) -> None:
        self._handlers: list[Callable[[PhysicsEvent], None]] = []
        self.handler_errors: list[tuple[str, str]] = []

    def subscribe(self, handler: Callable[[PhysicsEvent], None]) -> None:
        self._handlers.append(handler)

    def clear(self) -> None:
        self._handlers.clear()
        self.handler_errors.clear()

    def emit(self, event: PhysicsEvent) -> None:
        for handler in list(self._handlers):
            try:
                handler(event)
            except Exception as exc:  # pragma: no cover - defensive path
                self.handler_errors.append((event.type, str(exc)))
