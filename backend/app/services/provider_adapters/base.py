"""
Base classes and models for provider adapters.

This module defines the abstract interface that all provider adapters must implement,
as well as the Pydantic models for standardized responses.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

# =============================================================================
# Result Models
# =============================================================================


class TestResultStatus(str, Enum):
    """Status codes for connection tests."""

    SUCCESS = "success"
    AUTH_FAILED = "auth_failed"
    CONNECTION_ERROR = "connection_error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    INVALID_CONFIG = "invalid_config"
    NOT_IMPLEMENTED = "not_implemented"
    UNKNOWN_ERROR = "unknown_error"


class TestResult(BaseModel):
    """Result of a provider connection test."""

    success: bool = Field(description="Whether the test passed")
    status: TestResultStatus = Field(description="Status code for the test result")
    message: str = Field(description="Human-readable message describing the result")
    latency_ms: int | None = Field(
        default=None, description="Response latency in milliseconds"
    )
    tested_at: datetime = Field(
        default_factory=datetime.utcnow, description="When the test was performed"
    )
    details: dict[str, Any] | None = Field(
        default=None, description="Additional provider-specific details"
    )


class ModelInfo(BaseModel):
    """Information about a model available from a provider."""

    model_id: str = Field(description="The model identifier used in API calls")
    display_name: str | None = Field(
        default=None, description="Human-readable model name"
    )
    description: str | None = Field(default=None, description="Model description")
    context_window: int | None = Field(
        default=None, description="Maximum context window size in tokens"
    )
    max_output_tokens: int | None = Field(
        default=None, description="Maximum output tokens"
    )
    supports_vision: bool = Field(
        default=False, description="Whether model supports image inputs"
    )
    supports_function_calling: bool = Field(
        default=False, description="Whether model supports function/tool calling"
    )
    supports_streaming: bool = Field(
        default=True, description="Whether model supports streaming responses"
    )
    is_deprecated: bool = Field(
        default=False, description="Whether model is deprecated"
    )
    created_at: datetime | None = Field(
        default=None, description="When the model was created/released"
    )
    owned_by: str | None = Field(
        default=None, description="Organization that owns/created the model"
    )


class RateLimitInfo(BaseModel):
    """Rate limit information for an account."""

    requests_limit: int | None = Field(
        default=None, description="Maximum requests per time period"
    )
    requests_remaining: int | None = Field(
        default=None, description="Remaining requests in current period"
    )
    tokens_limit: int | None = Field(
        default=None, description="Maximum tokens per time period"
    )
    tokens_remaining: int | None = Field(
        default=None, description="Remaining tokens in current period"
    )
    reset_at: datetime | None = Field(
        default=None, description="When the rate limit resets"
    )


class AccountInfo(BaseModel):
    """Account/billing information from a provider."""

    account_name: str | None = Field(
        default=None, description="Account or organization name"
    )
    account_type: str | None = Field(
        default=None, description="Account tier (free, paid, enterprise, etc.)"
    )
    email: str | None = Field(default=None, description="Account email if available")
    organization_id: str | None = Field(
        default=None, description="Organization identifier"
    )
    rate_limits: RateLimitInfo | None = Field(
        default=None, description="Current rate limit status"
    )
    credits_remaining: float | None = Field(
        default=None, description="Remaining API credits if applicable"
    )
    hard_limit_usd: float | None = Field(
        default=None, description="Hard spending limit in USD"
    )
    soft_limit_usd: float | None = Field(
        default=None, description="Soft spending limit in USD"
    )


class AdapterConfig(BaseModel):
    """Configuration passed to adapter methods."""

    api_key: str = Field(description="Decrypted API key")
    base_url: str | None = Field(default=None, description="API base URL override")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    retry_delay_ms: int = Field(default=1000, description="Base delay between retries")
    proxy_url: str | None = Field(default=None, description="HTTP proxy URL")
    custom_headers: dict[str, str] | None = Field(
        default=None, description="Additional HTTP headers"
    )
    provider_config: dict[str, Any] | None = Field(
        default=None, description="Provider-specific configuration"
    )


# =============================================================================
# Abstract Base Adapter
# =============================================================================


class ProviderAdapter(ABC):
    """
    Abstract base class for provider adapters.

    Each provider (OpenAI, Anthropic, etc.) implements this interface
    to provide standardized connection testing, model listing, and
    account information retrieval.
    """

    # Human-readable name for the provider
    provider_name: str = "Unknown Provider"

    @abstractmethod
    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test if the API key and configuration are valid.

        This should make a minimal API call to verify credentials work.

        Args:
            config: Adapter configuration with decrypted API key

        Returns:
            TestResult indicating success/failure with details
        """
        ...

    @abstractmethod
    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available models from the provider.

        Args:
            config: Adapter configuration with decrypted API key

        Returns:
            List of available models with their capabilities

        Raises:
            Exception: If API call fails (test_connection should be called first)
        """
        ...

    @abstractmethod
    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account/billing information if available.

        Not all providers support this - return None if unavailable.

        Args:
            config: Adapter configuration with decrypted API key

        Returns:
            AccountInfo if available, None otherwise
        """
        ...


# =============================================================================
# Helper Functions
# =============================================================================


def create_error_result(
    status: TestResultStatus,
    message: str,
    details: dict[str, Any] | None = None,
) -> TestResult:
    """Create a failed TestResult with the given status and message."""
    return TestResult(
        success=False,
        status=status,
        message=message,
        details=details,
    )


def create_success_result(
    message: str = "Connection successful",
    latency_ms: int | None = None,
    details: dict[str, Any] | None = None,
) -> TestResult:
    """Create a successful TestResult."""
    return TestResult(
        success=True,
        status=TestResultStatus.SUCCESS,
        message=message,
        latency_ms=latency_ms,
        details=details,
    )
