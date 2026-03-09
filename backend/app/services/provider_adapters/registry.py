"""
Provider adapter registry.

Maps provider_type_id (from LLMProviderType) to the appropriate adapter class.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

from app.core.provider_types import TYPE1, TYPE2, TYPE3, TYPE4, TYPE5
from app.core.security import decrypt_api_key

from .anthropic_adapter import anthropic_adapter
from .azure_adapter import azure_adapter  # noqa: F401
from .base import (
    AccountInfo,
    AdapterConfig,
    ModelInfo,
    ProviderAdapter,
    TestResult,
    TestResultStatus,
    create_error_result,
)
from .generic_adapter import generic_adapter
from .google_adapter import google_adapter
from .openai_adapter import openai_adapter

if TYPE_CHECKING:
    from app.models import UserAccessProvider

logger = logging.getLogger(__name__)


# =============================================================================
# Provider Type ID Mapping
# =============================================================================

# Map provider type UUIDs to adapter instances
# TYPE1 = OpenAI
# TYPE2 = Anthropic
# TYPE3 = OpenAI Compatible
# TYPE4 = Custom
# TYPE5 = Google

PROVIDER_ADAPTERS: dict[str, ProviderAdapter] = {
    TYPE1: openai_adapter,  # OpenAI
    TYPE2: anthropic_adapter,  # Anthropic
    TYPE3: generic_adapter,  # OpenAI Compatible
    TYPE4: generic_adapter,  # Custom (fallback to generic)
    TYPE5: google_adapter,  # Google
}


def get_adapter_for_provider_type(provider_type_id: uuid.UUID | str) -> ProviderAdapter:
    """
    Get the appropriate adapter for a provider type.

    Args:
        provider_type_id: The UUID of the LLMProviderType

    Returns:
        The adapter instance for that provider type

    Raises:
        ValueError: If no adapter is registered for the provider type
    """
    # Convert UUID to string for lookup
    type_id_str = str(provider_type_id)

    adapter = PROVIDER_ADAPTERS.get(type_id_str)
    if adapter is None:
        # Fallback to generic adapter for unknown types
        logger.warning(
            f"No adapter registered for provider_type_id={type_id_str}, "
            "falling back to generic adapter"
        )
        return generic_adapter

    return adapter


def build_adapter_config(provider: UserAccessProvider) -> AdapterConfig:
    """
    Build an AdapterConfig from a UserAccessProvider model.

    This decrypts the API key and collects all configuration.

    Args:
        provider: The UserAccessProvider database model

    Returns:
        AdapterConfig ready to use with an adapter

    Raises:
        ValueError: If API key cannot be decrypted
    """
    # Decrypt the API key
    # Note: The model stores encrypted key in api_key_encrypted
    api_key = ""
    if hasattr(provider, "api_key_encrypted") and provider.api_key_encrypted:
        try:
            api_key = decrypt_api_key(provider.api_key_encrypted)
        except Exception as e:
            logger.error(f"Failed to decrypt API key for provider {provider.id}: {e}")
            raise ValueError("Failed to decrypt API key") from e
    elif hasattr(provider, "api_key") and provider.api_key:
        # Fallback for when api_key is already decrypted (e.g., in tests)
        api_key = provider.api_key

    return AdapterConfig(
        api_key=api_key,
        base_url=provider.base_url,
        timeout_seconds=provider.timeout_seconds,
        max_retries=provider.max_retries,
        retry_delay_ms=provider.retry_delay_ms,
        proxy_url=provider.proxy_url,
        custom_headers=provider.custom_headers,  # type: ignore[arg-type]
        provider_config=provider.provider_config,
    )


# =============================================================================
# High-Level Service Functions
# =============================================================================


async def test_provider_connection(provider: UserAccessProvider) -> TestResult:
    """
    Test connection for a UserAccessProvider.

    This is the main entry point for testing a provider's connection.
    It automatically selects the right adapter based on provider type.

    Args:
        provider: The UserAccessProvider to test

    Returns:
        TestResult with success/failure status
    """
    try:
        adapter = get_adapter_for_provider_type(provider.alpha_provider_type_id)
        config = build_adapter_config(provider)
        return await adapter.test_connection(config)
    except ValueError as e:
        return create_error_result(
            status=TestResultStatus.INVALID_CONFIG,
            message=str(e),
        )
    except Exception:
        logger.exception(f"Error testing provider {provider.id}")
        return create_error_result(
            status=TestResultStatus.UNKNOWN_ERROR,
            message="Internal error occurred",
        )


async def list_provider_models(provider: UserAccessProvider) -> list[ModelInfo]:
    """
    List available models for a UserAccessProvider.

    Args:
        provider: The UserAccessProvider to query

    Returns:
        List of available models, empty list on error
    """
    try:
        adapter = get_adapter_for_provider_type(provider.alpha_provider_type_id)
        config = build_adapter_config(provider)
        return await adapter.list_models(config)
    except Exception:
        logger.exception(f"Error listing models for provider {provider.id}")
        return []


async def get_provider_account_info(
    provider: UserAccessProvider,
) -> AccountInfo | None:
    """
    Get account info for a UserAccessProvider.

    Args:
        provider: The UserAccessProvider to query

    Returns:
        AccountInfo if available, None otherwise
    """
    try:
        adapter = get_adapter_for_provider_type(provider.alpha_provider_type_id)
        config = build_adapter_config(provider)
        return await adapter.get_account_info(config)
    except Exception:
        logger.exception(f"Error getting account info for provider {provider.id}")
        return None
