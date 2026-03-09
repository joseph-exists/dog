"""
Azure OpenAI API adapter implementation.

Handles connection testing, model listing, and account info for Azure's OpenAI service.
"""

from __future__ import annotations

import logging

from .base import (
    AccountInfo,
    AdapterConfig,
    ModelInfo,
    ProviderAdapter,
    TestResult,
    TestResultStatus,
    create_error_result,
)

logger = logging.getLogger(__name__)


class AzureOpenAIAdapter(ProviderAdapter):
    """
    Adapter for Azure OpenAI Service.

    Azure OpenAI differs from OpenAI's API:
    - Uses api-key header instead of Bearer token
    - Requires deployment names in URLs
    - Has different endpoint structure

    TODO: Full implementation pending.
    """

    provider_name = "Azure OpenAI"

    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test Azure OpenAI connection.

        Requires:
        - base_url: Azure endpoint (e.g., https://myresource.openai.azure.com)
        - api_key: Azure API key
        - provider_config.deployment_name: Deployment name

        TODO: Implement full Azure OpenAI support.
        """
        return create_error_result(
            status=TestResultStatus.NOT_IMPLEMENTED,
            message="Azure OpenAI adapter not yet implemented. "
            "Use the generic OpenAI-compatible adapter with your Azure endpoint.",
            details={
                "provider": self.provider_name,
                "hint": "Set base_url to your Azure endpoint and provide api_key",
            },
        )

    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available models from Azure OpenAI.

        Azure uses deployments rather than models, so this would need
        to list deployments from the Azure resource.

        TODO: Implement full Azure OpenAI support.
        """
        logger.warning("Azure OpenAI list_models not implemented")
        return []

    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account information from Azure.

        Azure doesn't expose account info via the OpenAI API.

        TODO: Could potentially use Azure Resource Manager API.
        """
        return None


# Singleton instance
azure_adapter = AzureOpenAIAdapter()
