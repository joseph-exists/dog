"""
Generic OpenAI-compatible API adapter.

This adapter works with any API that follows the OpenAI API spec,
such as local LLM servers (Ollama, LM Studio, vLLM) or third-party
OpenAI-compatible services.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from .base import (
    AccountInfo,
    AdapterConfig,
    ModelInfo,
    ProviderAdapter,
    TestResult,
    TestResultStatus,
    create_error_result,
    create_success_result,
)

logger = logging.getLogger(__name__)


class GenericOpenAIAdapter(ProviderAdapter):
    """
    Generic adapter for OpenAI-compatible APIs.

    Works with any service that implements the OpenAI API spec:
    - Local: Ollama, LM Studio, text-generation-webui, vLLM
    - Cloud: Together AI, Anyscale, Groq, etc.

    Requires base_url to be set in config.
    """

    provider_name = "OpenAI Compatible"

    def _get_client(self, config: AdapterConfig) -> httpx.AsyncClient:
        """Create an async HTTP client with the given configuration."""
        if not config.base_url:
            raise ValueError(
                "base_url is required for generic OpenAI-compatible adapter"
            )

        headers = {
            "Content-Type": "application/json",
        }

        # Add authorization if API key is provided (some local servers don't need it)
        if config.api_key and config.api_key.strip():
            headers["Authorization"] = f"Bearer {config.api_key}"

        # Add custom headers
        if config.custom_headers:
            headers.update(config.custom_headers)

        return httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(config.timeout_seconds),
            proxy=config.proxy_url,
        )

    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test connection to an OpenAI-compatible API.

        Tries multiple endpoints to find one that works:
        1. /v1/models (standard OpenAI)
        2. /models (some servers)
        3. /api/tags (Ollama)
        """
        if not config.base_url:
            return create_error_result(
                status=TestResultStatus.INVALID_CONFIG,
                message="base_url is required for OpenAI-compatible providers",
            )

        start_time = time.monotonic()
        last_error: str | None = None

        # Try different endpoint patterns
        endpoints = ["/v1/models", "/models", "/api/tags"]

        try:
            async with self._get_client(config) as client:
                for endpoint in endpoints:
                    try:
                        response = await client.get(endpoint)
                        latency_ms = int((time.monotonic() - start_time) * 1000)

                        if response.status_code == 200:
                            data = response.json()
                            model_count = self._count_models(data, endpoint)
                            return create_success_result(
                                message=f"Connected successfully. {model_count} models available.",
                                latency_ms=latency_ms,
                                details={
                                    "endpoint": endpoint,
                                    "model_count": model_count,
                                },
                            )
                        elif response.status_code == 401:
                            return create_error_result(
                                status=TestResultStatus.AUTH_FAILED,
                                message="Authentication failed. Check your API key.",
                                details={"endpoint": endpoint},
                            )
                        elif response.status_code == 404:
                            # Try next endpoint
                            last_error = f"Endpoint {endpoint} not found"
                            continue
                        else:
                            last_error = (
                                f"Endpoint {endpoint} returned {response.status_code}"
                            )

                    except httpx.TimeoutException:
                        return create_error_result(
                            status=TestResultStatus.TIMEOUT,
                            message=f"Connection timed out after {config.timeout_seconds}s",
                        )
                    except Exception as e:
                        last_error = f"Error on {endpoint}: {e!s}"
                        continue

                # None of the endpoints worked
                return create_error_result(
                    status=TestResultStatus.CONNECTION_ERROR,
                    message=f"Could not connect to any known endpoint. Last error: {last_error}",
                    details={"tried_endpoints": endpoints},
                )

        except httpx.ConnectError as e:
            return create_error_result(
                status=TestResultStatus.CONNECTION_ERROR,
                message=f"Failed to connect to {config.base_url}: {e!s}",
            )
        except Exception as e:
            logger.exception("Unexpected error testing generic OpenAI connection")
            return create_error_result(
                status=TestResultStatus.UNKNOWN_ERROR,
                message=f"Unexpected error: {e!s}",
            )

    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available models from an OpenAI-compatible API.

        Tries multiple endpoint patterns to accommodate different servers.
        """
        if not config.base_url:
            return []

        endpoints = ["/v1/models", "/models", "/api/tags"]

        async with self._get_client(config) as client:
            for endpoint in endpoints:
                try:
                    response = await client.get(endpoint)
                    if response.status_code != 200:
                        continue

                    data = response.json()
                    return self._parse_models(data, endpoint)

                except Exception as e:
                    logger.debug(f"Failed to list models from {endpoint}: {e}")
                    continue

        # No endpoint worked
        logger.warning(f"Could not list models from {config.base_url}")
        return []

    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account info - not typically available for generic providers.

        Most OpenAI-compatible servers don't expose account information,
        so this returns None.
        """
        return None

    def _count_models(self, data: dict[str, Any], endpoint: str) -> int:
        """Count models from various response formats."""
        if endpoint == "/api/tags":
            # Ollama format
            return len(data.get("models", []))
        else:
            # OpenAI format
            return len(data.get("data", []))

    def _parse_models(self, data: dict[str, Any], endpoint: str) -> list[ModelInfo]:
        """Parse models from various response formats."""
        models: list[ModelInfo] = []

        if endpoint == "/api/tags":
            # Ollama format: {"models": [{"name": "llama2", ...}]}
            for model_data in data.get("models", []):
                name = model_data.get("name", "")
                models.append(
                    ModelInfo(
                        model_id=name,
                        display_name=name,
                        description=model_data.get("description"),
                        supports_streaming=True,
                    )
                )
        else:
            # OpenAI format: {"data": [{"id": "gpt-4", ...}]}
            for model_data in data.get("data", []):
                model_id = model_data.get("id", "")
                models.append(
                    ModelInfo(
                        model_id=model_id,
                        display_name=model_id,
                        owned_by=model_data.get("owned_by"),
                        supports_streaming=True,
                    )
                )

        models.sort(key=lambda m: m.model_id)
        return models


# Singleton instance
generic_adapter = GenericOpenAIAdapter()
