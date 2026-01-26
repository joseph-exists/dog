from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Literal

import tomli
from pydantic import BaseModel, Field

LOGGER = logging.getLogger(__name__)
LogfireLevel = Literal["debug", "info", "warning", "error"]
LEVEL_ORDER = {"debug": 0, "info": 1, "warning": 2, "error": 3}


class TelemetryConfig(BaseModel):
    traces: bool = Field(default=False)
    events: bool = Field(default=False)


class DefaultsConfig(BaseModel):
    enabled: bool = Field(default=False)
    level: LogfireLevel = Field(default="info")
    telemetry: TelemetryConfig = Field(default_factory=TelemetryConfig)


class BundleConfig(BaseModel):
    services: list[str] = Field(default_factory=list)
    enabled: bool | None = None
    level: LogfireLevel | None = None
    telemetry: TelemetryConfig | None = None


class ServiceConfig(BaseModel):
    enabled: bool | None = None
    level: LogfireLevel | None = None
    telemetry: TelemetryConfig | None = None
    bundles: list[str] = Field(default_factory=list)


class EffectiveLogfireConfig(BaseModel):
    enabled: bool
    level: LogfireLevel
    telemetry: TelemetryConfig
    bundles: list[str] = Field(default_factory=list)

    class Config:
        frozen = True


class LogfireConfig(BaseModel):
    version: int = 1
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    bundles: dict[str, BundleConfig] = Field(default_factory=dict)
    services: dict[str, ServiceConfig] = Field(default_factory=dict)

    def get_service_effective_config(self, service_id: str) -> EffectiveLogfireConfig:
        override = self.services.get(service_id)
        bundle_names = self._resolve_bundles_for_service(service_id, override)

        enabled = self.defaults.enabled
        for bundle_name in bundle_names:
            bundle = self.bundles[bundle_name]
            if bundle.enabled:
                enabled = True

        if override:
            if override.enabled is False:
                enabled = False
            elif override.enabled is True:
                enabled = True

        level = self.defaults.level
        for bundle_name in bundle_names:
            bundle = self.bundles[bundle_name]
            level = self._select_lower(level, bundle.level)
        if override and override.level:
            level = override.level

        telemetry = TelemetryConfig(**self.defaults.telemetry.model_dump())
        for bundle_name in bundle_names:
            bundle = self.bundles[bundle_name]
            if bundle.telemetry:
                telemetry.traces |= bundle.telemetry.traces
                telemetry.events |= bundle.telemetry.events

        if override and override.telemetry:
            telemetry.traces |= override.telemetry.traces
            telemetry.events |= override.telemetry.events

        return EffectiveLogfireConfig(
            enabled=enabled,
            level=level,
            telemetry=telemetry,
            bundles=bundle_names,
        )

    def _resolve_bundles_for_service(
        self, service_id: str, override: ServiceConfig | None
    ) -> list[str]:
        bundle_names: list[str] = [
            name
            for name, bundle in self.bundles.items()
            if service_id in bundle.services
        ]

        if override:
            for requested in override.bundles:
                if requested not in self.bundles:
                    LOGGER.warning(
                        "Logfire bundle %s referenced by %s does not exist", requested, service_id
                    )
                    continue
                if requested not in bundle_names:
                    bundle_names.append(requested)

        return bundle_names

    @staticmethod
    def _select_lower(current: LogfireLevel, candidate: LogfireLevel | None) -> LogfireLevel:
        if candidate is None:
            return current
        return candidate if LEVEL_ORDER[candidate] < LEVEL_ORDER[current] else current


CONFIG_PATH = Path(__file__).resolve().parent / "logfire_config.toml"


@lru_cache(maxsize=1)
def load_logfire_config() -> LogfireConfig:
    if not CONFIG_PATH.exists():
        LOGGER.debug("Logfire config missing at %s, using defaults", CONFIG_PATH)
        return LogfireConfig()

    try:
        with CONFIG_PATH.open("rb") as handle:
            raw = tomli.load(handle)
    except tomli.TOMLDecodeError as error:
        LOGGER.error("Failed to parse %s: %s", CONFIG_PATH, error)
        raise

    return LogfireConfig(**raw)


def get_service_logfire_config(service_id: str) -> EffectiveLogfireConfig:
    return load_logfire_config().get_service_effective_config(service_id)


def reload_logfire_config() -> LogfireConfig:
    load_logfire_config.cache_clear()
    return load_logfire_config()
