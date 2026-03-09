"""
Anthropic API adapter implementation.

Handles connection testing, model listing, and account info for Anthropic's API.
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
    RateLimitInfo,
    TestResult,
    TestResultStatus,
    create_error_result,
    create_success_result,
)

logger = logging.getLogger(__name__)

# Default Anthropic API base URL
ANTHROPIC_API_BASE = "https://api.anthropic.com"

# Current Anthropic API version
ANTHROPIC_API_VERSION = "2023-06-01"

# Known Anthropic models with their capabilities
# Note: Anthropic doesn't have a models endpoint, so we maintain this list
ANTHROPIC_MODELS = [
    {
        "id": "claude-3-5-sonnet-20241022",
        "display_name": "Claude 3.5 Sonnet",
        "context_window": 200000,
        "max_output": 8192,
        "vision": True,
        "deprecated": False,
    },
    {
        "id": "claude-3-opus-20240229",
        "display_name": "Claude 3 Opus",
        "context_window": 200000,
        "max_output": 4096,
        "vision": True,
        "deprecated": False,
    },
    {
        "id": "claude-3-sonnet-20240229",
        "display_name": "Claude 3 Sonnet",
        "context_window": 200000,
        "max_output": 4096,
        "vision": True,
        "deprecated": False,
    },
    {
        "id": "claude-3-haiku-20240307",
        "display_name": "Claude 3 Haiku",
        "context_window": 200000,
        "max_output": 4096,
        "vision": True,
        "deprecated": False,
    },
    {
        "id": "claude-2.1",
        "display_name": "Claude 2.1",
        "context_window": 200000,
        "max_output": 4096,
        "vision": False,
        "deprecated": True,
    },
    {
        "id": "claude-2.0",
        "display_name": "Claude 2.0",
        "context_window": 100000,
        "max_output": 4096,
        "vision": False,
        "deprecated": True,
    },
]


class AnthropicAdapter(ProviderAdapter):
    """
    Adapter for Anthropic's Claude API.

    Note: Anthropic's API differs from OpenAI in several ways:
    - Uses x-api-key header instead of Authorization: Bearer
    - Requires anthropic-version header
    - No /models endpoint - model list is hardcoded
    """

    provider_name = "Anthropic"

    def _get_client(self, config: AdapterConfig) -> httpx.AsyncClient:
        """Create an async HTTP client with Anthropic-specific headers."""
        headers = {
            "x-api-key": config.api_key,
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Content-Type": "application/json",
        }

        # Add custom headers
        if config.custom_headers:
            headers.update(config.custom_headers)

        base_url = config.base_url or ANTHROPIC_API_BASE

        return httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(config.timeout_seconds),
            proxy=config.proxy_url,
        )

    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test Anthropic connection by making a minimal API call.

        Since Anthropic doesn't have a /models endpoint, we use a minimal
        messages request with max_tokens=1 to validate the API key.
        """
        start_time = time.monotonic()

        try:
            async with self._get_client(config) as client:
                # Make a minimal request to validate the key
                response = await client.post(
                    "/v1/messages",
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                )
                latency_ms = int((time.monotonic() - start_time) * 1000)

                if response.status_code == 200:
                    return create_success_result(
                        message=f"Connected successfully. {len(ANTHROPIC_MODELS)} models available.",
                        latency_ms=latency_ms,
                        details={"model_count": len(ANTHROPIC_MODELS)},
                    )
                elif response.status_code == 401:
                    return create_error_result(
                        status=TestResultStatus.AUTH_FAILED,
                        message="Invalid API key. Please check your credentials.",
                        details=self._extract_error_details(response),
                    )
                elif response.status_code == 429:
                    # Rate limited but key is valid
                    return create_success_result(
                        message="API key valid (rate limited). Try again later for full test.",
                        latency_ms=latency_ms,
                        details={"rate_limited": True},
                    )
                elif response.status_code == 400:
                    # Bad request usually means the key is valid but request is wrong
                    error_data = self._extract_error_details(response)

                    # "invalid_api_key" means auth failed
                    if "invalid_api_key" in str(error_data):
                        return create_error_result(
                            status=TestResultStatus.AUTH_FAILED,
                            message="Invalid API key.",
                            details=error_data,
                        )

                    # Other 400 errors with a valid-looking response means key works
                    return create_success_result(
                        message="API key appears valid.",
                        latency_ms=latency_ms,
                        details=error_data,
                    )
                else:
                    return create_error_result(
                        status=TestResultStatus.UNKNOWN_ERROR,
                        message=f"Unexpected response: {response.status_code}",
                        details=self._extract_error_details(response),
                    )

        except httpx.TimeoutException:
            return create_error_result(
                status=TestResultStatus.TIMEOUT,
                message=f"Connection timed out after {config.timeout_seconds}s",
            )
        except httpx.ConnectError as e:
            return create_error_result(
                status=TestResultStatus.CONNECTION_ERROR,
                message=f"Failed to connect: {e!s}",
            )
        except Exception as e:
            logger.exception("Unexpected error testing Anthropic connection")
            return create_error_result(
                status=TestResultStatus.UNKNOWN_ERROR,
                message=f"Unexpected error: {e!s}",
            )

    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available Anthropic models.

        Anthropic doesn't have a /models API endpoint, so we return
        a hardcoded list of known models.
        """
        # Return the hardcoded list - all models should be available
        # with a valid API key
        models = [
            ModelInfo(
                model_id=m["id"],
                display_name=m["display_name"],
                context_window=m["context_window"],
                max_output_tokens=m["max_output"],
                supports_vision=m["vision"],
                supports_function_calling=True,  # All Claude 3+ models support this
                supports_streaming=True,
                is_deprecated=m["deprecated"],
                owned_by="anthropic",
            )
            for m in ANTHROPIC_MODELS
        ]

        # Sort non-deprecated first, then by name
        models.sort(key=lambda m: (m.is_deprecated, m.model_id))
        return models

    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account information from Anthropic.

        Anthropic doesn't expose detailed account info via API.
        We can only extract rate limit info from response headers.
        """
        try:
            async with self._get_client(config) as client:
                # Make a minimal request to get headers
                response = await client.post(
                    "/v1/messages",
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "Hi"}],
                    },
                )

                if response.status_code not in (200, 429):
                    return None

                rate_limits = self._extract_rate_limits(response.headers)

                return AccountInfo(
                    rate_limits=rate_limits if rate_limits else None,
                )

        except Exception as e:
            logger.warning(f"Failed to get Anthropic account info: {e}")
            return None

    def _extract_error_details(self, response: httpx.Response) -> dict[str, Any]:
        """Extract error details from an API response."""
        try:
            data = response.json()
            return {
                "status_code": response.status_code,
                "error": data.get("error", {}),
            }
        except Exception:
            return {
                "status_code": response.status_code,
                "body": response.text[:500],
            }

    def _extract_rate_limits(self, headers: httpx.Headers) -> RateLimitInfo | None:
        """Extract rate limit info from Anthropic response headers."""
        # Anthropic uses these headers
        requests_limit = headers.get("anthropic-ratelimit-requests-limit")
        requests_remaining = headers.get("anthropic-ratelimit-requests-remaining")
        tokens_limit = headers.get("anthropic-ratelimit-tokens-limit")
        tokens_remaining = headers.get("anthropic-ratelimit-tokens-remaining")

        if not any(
            [requests_limit, requests_remaining, tokens_limit, tokens_remaining]
        ):
            return None

        return RateLimitInfo(
            requests_limit=int(requests_limit) if requests_limit else None,
            requests_remaining=int(requests_remaining) if requests_remaining else None,
            tokens_limit=int(tokens_limit) if tokens_limit else None,
            tokens_remaining=int(tokens_remaining) if tokens_remaining else None,
        )


# Singleton instance
anthropic_adapter = AnthropicAdapter()
