"""Shared configuration for the TinyFoot Typer CLI."""

from __future__ import annotations

import os

DEFAULT_API_ROOT_URL = "http://localhost:8000"


def _without_trailing_slash(value: str) -> str:
    return value.rstrip("/")


def get_api_v1_url() -> str:
    """
    Return the API v1 base URL used by command modules.

    TINYFOOT_API_V1_URL is the exact endpoint prefix, while TINYFOOT_API_URL and
    TINYFOOT_API_ROOT_URL may point at either the service root or /api/v1.
    """

    explicit_v1 = os.getenv("TINYFOOT_API_V1_URL")
    if explicit_v1:
        return _without_trailing_slash(explicit_v1)

    api_url = os.getenv("TINYFOOT_API_URL") or os.getenv("TINYFOOT_API_ROOT_URL") or DEFAULT_API_ROOT_URL
    api_url = _without_trailing_slash(api_url)
    if api_url.endswith("/api/v1"):
        return api_url
    return f"{api_url}/api/v1"


def get_api_root_url() -> str:
    """Return the API service root URL without the /api/v1 suffix."""

    api_v1_url = get_api_v1_url()
    suffix = "/api/v1"
    if api_v1_url.endswith(suffix):
        return api_v1_url[: -len(suffix)] or DEFAULT_API_ROOT_URL
    return api_v1_url
