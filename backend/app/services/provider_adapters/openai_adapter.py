"""
OpenAI API adapter implementation.

Handles connection testing, model listing, and account info for OpenAI's API.
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

# Default OpenAI API base URL
OPENAI_API_BASE = "https://api.openai.com/v1"


class OpenAIAdapter(ProviderAdapter):
    """
    Adapter for OpenAI's API.

    Supports both OpenAI's official API and API-compatible endpoints
    when base_url is overridden.
    """

    provider_name = "OpenAI"

    def _get_client(self, config: AdapterConfig) -> httpx.AsyncClient:
        """Create an async HTTP client with the given configuration."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        # Add organization header if specified
        if config.provider_config:
            org_id = config.provider_config.get("organization_id")
            if org_id:
                headers["OpenAI-Organization"] = org_id

        # Add custom headers
        if config.custom_headers:
            headers.update(config.custom_headers)

        base_url = config.base_url or OPENAI_API_BASE

        return httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers=headers,
            timeout=httpx.Timeout(config.timeout_seconds),
            proxy=config.proxy_url,
        )

    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test OpenAI connection by listing models.

        This is a lightweight call that validates the API key works.
        """
        start_time = time.monotonic()

        try:
            async with self._get_client(config) as client:
                response = await client.get("/models")
                latency_ms = int((time.monotonic() - start_time) * 1000)

                if response.status_code == 200:
                    data = response.json()
                    model_count = len(data.get("data", []))
                    return create_success_result(
                        message=f"Connected successfully. {model_count} models available.",
                        latency_ms=latency_ms,
                        details={"model_count": model_count},
                    )
                elif response.status_code == 401:
                    return create_error_result(
                        status=TestResultStatus.AUTH_FAILED,
                        message="Invalid API key. Please check your credentials.",
                        details=self._extract_error_details(response),
                    )
                elif response.status_code == 429:
                    return create_error_result(
                        status=TestResultStatus.RATE_LIMITED,
                        message="Rate limited. Please try again later.",
                        details=self._extract_error_details(response),
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
            logger.exception("Unexpected error testing OpenAI connection")
            return create_error_result(
                status=TestResultStatus.UNKNOWN_ERROR,
                message=f"Unexpected error: {e!s}",
            )

    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available models from OpenAI.

        Returns all models the API key has access to, with capability info.
        """
        async with self._get_client(config) as client:
            response = await client.get("/models")
            response.raise_for_status()
            data = response.json()

        models: list[ModelInfo] = []
        for model_data in data.get("data", []):
            model_id = model_data.get("id", "")
            models.append(
                ModelInfo(
                    model_id=model_id,
                    display_name=model_id,
                    owned_by=model_data.get("owned_by"),
                    created_at=self._parse_timestamp(model_data.get("created")),
                    # Infer capabilities from model name
                    supports_vision=self._supports_vision(model_id),
                    supports_function_calling=self._supports_function_calling(model_id),
                    supports_streaming=True,
                    context_window=self._get_context_window(model_id),
                )
            )

        # Sort by model ID for consistent ordering
        models.sort(key=lambda m: m.model_id)
        return models

    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account information from OpenAI.

        Note: OpenAI doesn't expose detailed account info via API.
        We return what we can infer from rate limit headers.
        """
        try:
            async with self._get_client(config) as client:
                # Make a lightweight request to get headers
                response = await client.get("/models")

                if response.status_code != 200:
                    return None

                # Extract rate limit info from headers if present
                rate_limits = self._extract_rate_limits(response.headers)

                # Extract org info if in provider_config
                org_id = None
                if config.provider_config:
                    org_id = config.provider_config.get("organization_id")

                return AccountInfo(
                    organization_id=org_id,
                    rate_limits=rate_limits if rate_limits else None,
                )

        except Exception as e:
            logger.warning(f"Failed to get OpenAI account info: {e}")
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
        """Extract rate limit info from response headers."""
        # OpenAI uses these headers for rate limits
        requests_limit = headers.get("x-ratelimit-limit-requests")
        requests_remaining = headers.get("x-ratelimit-remaining-requests")
        tokens_limit = headers.get("x-ratelimit-limit-tokens")
        tokens_remaining = headers.get("x-ratelimit-remaining-tokens")

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

    def _parse_timestamp(self, ts: int | None) -> Any:
        """Parse a Unix timestamp to datetime."""
        if ts is None:
            return None
        from datetime import datetime, timezone

        return datetime.fromtimestamp(ts, tz=timezone.utc)

    def _supports_vision(self, model_id: str) -> bool:
        """Check if model supports vision based on ID."""
        vision_indicators = ["vision", "gpt-4o", "gpt-4-turbo"]
        model_lower = model_id.lower()
        return any(ind in model_lower for ind in vision_indicators)

    def _supports_function_calling(self, model_id: str) -> bool:
        """Check if model supports function calling based on ID."""
        # Most GPT-4 and GPT-3.5-turbo models support function calling
        model_lower = model_id.lower()
        if "gpt-4" in model_lower or "gpt-3.5-turbo" in model_lower:
            # Exclude instruct models
            if "instruct" not in model_lower:
                return True
        return False

    def _get_context_window(self, model_id: str) -> int | None:
        """Get context window size based on model ID."""
        model_lower = model_id.lower()

        # Known context windows (approximate)
        if "gpt-4o" in model_lower:
            return 128000
        elif "gpt-4-turbo" in model_lower or "gpt-4-1106" in model_lower:
            return 128000
        elif "gpt-4-32k" in model_lower:
            return 32768
        elif "gpt-4" in model_lower:
            return 8192
        elif "gpt-3.5-turbo-16k" in model_lower:
            return 16384
        elif "gpt-3.5-turbo" in model_lower:
            return 4096

        return None


# Singleton instance
openai_adapter = OpenAIAdapter()
