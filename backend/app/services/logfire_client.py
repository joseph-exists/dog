from __future__ import annotations

import logfire as _logfire

from .logfire_config import get_service_logfire_config, LogfireLevel

SEVERITY_ORDER: dict[LogfireLevel, int] = {
    "debug": 0,
    "info": 1,
    "warning": 2,
    "error": 3,
}


class _NoopContext:
    def __enter__(self) -> None:
        return None

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        return None


def _traces_enabled(service_id: str) -> bool:
    config = get_service_logfire_config(service_id)
    return config.enabled and config.telemetry.traces


def _events_enabled(service_id: str, severity: LogfireLevel) -> bool:
    config = get_service_logfire_config(service_id)
    if not (config.enabled and config.telemetry.events):
        return False
    return SEVERITY_ORDER[severity] >= SEVERITY_ORDER[config.level]


def span(service_id: str, *args: object, **kwargs: object):
    if _traces_enabled(service_id):
        return _logfire.span(*args, **kwargs)
    return _NoopContext()


def info(service_id: str, *args: object, **kwargs: object) -> None:
    if _events_enabled(service_id, "info"):
        _logfire.info(*args, **kwargs)


def warning(service_id: str, *args: object, **kwargs: object) -> None:
    if _events_enabled(service_id, "warning"):
        _logfire.warning(*args, **kwargs)


def exception(service_id: str, *args: object, **kwargs: object) -> None:
    if _events_enabled(service_id, "error"):
        _logfire.exception(*args, **kwargs)


class ServiceLogfire:
    def __init__(self, service_id: str) -> None:
        self._service_id = service_id

    def span(self, *args: object, **kwargs: object):
        return span(self._service_id, *args, **kwargs)

    def info(self, *args: object, **kwargs: object) -> None:
        info(self._service_id, *args, **kwargs)

    def warning(self, *args: object, **kwargs: object) -> None:
        warning(self._service_id, *args, **kwargs)

    def exception(self, *args: object, **kwargs: object) -> None:
        exception(self._service_id, *args, **kwargs)
