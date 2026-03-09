"""
Provider Adapters - Service layer for LLM provider operations.

This module provides a unified interface for interacting with different LLM providers
(OpenAI, Anthropic, Azure, Google, etc.). Each provider has an adapter that implements
the same interface for:

1. Connection testing (validate API keys)
2. Model listing (discover available models)
3. Account info retrieval (billing, rate limits)

Usage:
    from app.services.provider_adapters import (
        test_provider_connection,
        list_provider_models,
        get_provider_account_info,
    )

    # Test a user's provider configuration
    result = await test_provider_connection(user_access_provider)
    if result.success:
        models = await list_provider_models(user_access_provider)

For lower-level access:
    from app.services.provider_adapters import (
        get_adapter_for_provider_type,
        build_adapter_config,
    )

    adapter = get_adapter_for_provider_type(provider.alpha_provider_type_id)
    config = build_adapter_config(provider)
    result = await adapter.test_connection(config)
"""

# Re-export base models
# Re-export individual adapters for direct use if needed
from .anthropic_adapter import anthropic_adapter
from .azure_adapter import azure_adapter
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
from .generic_adapter import generic_adapter
from .google_adapter import google_adapter
from .openai_adapter import openai_adapter

# Re-export registry functions (main entry points)
from .registry import (
    PROVIDER_ADAPTERS,
    build_adapter_config,
    get_adapter_for_provider_type,
    get_provider_account_info,
    list_provider_models,
    test_provider_connection,
)

__all__ = [
    # Base models
    "AccountInfo",
    "AdapterConfig",
    "ModelInfo",
    "ProviderAdapter",
    "RateLimitInfo",
    "TestResult",
    "TestResultStatus",
    "create_error_result",
    "create_success_result",
    # Registry functions
    "PROVIDER_ADAPTERS",
    "build_adapter_config",
    "get_adapter_for_provider_type",
    "get_provider_account_info",
    "list_provider_models",
    "test_provider_connection",
    # Individual adapters
    "anthropic_adapter",
    "azure_adapter",
    "generic_adapter",
    "google_adapter",
    "openai_adapter",
]
