"""
Google AI / Vertex AI adapter implementation.

Handles connection testing, model listing, and account info for Google's AI APIs.
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


class GoogleAIAdapter(ProviderAdapter):
    """
    Adapter for Google AI (Gemini) and Vertex AI.

    Google's AI API differs significantly from OpenAI:
    - Uses different authentication (API key or service account)
    - Different endpoint structure
    - Different model naming

    TODO: Full implementation pending.
    """

    provider_name = "Google AI"

    async def test_connection(self, config: AdapterConfig) -> TestResult:
        """
        Test Google AI connection.

        For Google AI Studio:
        - base_url: https://generativelanguage.googleapis.com/v1beta
        - api_key: Google AI API key

        For Vertex AI:
        - Requires service account authentication
        - Different endpoint structure

        TODO: Implement full Google AI support.
        """
        return create_error_result(
            status=TestResultStatus.NOT_IMPLEMENTED,
            message="Google AI adapter not yet implemented. "
            "Google AI/Vertex AI support coming soon.",
            details={
                "provider": self.provider_name,
                "hint": "For Google AI, the API structure differs from OpenAI",
            },
        )

    async def list_models(self, config: AdapterConfig) -> list[ModelInfo]:
        """
        List available models from Google AI.

        Google AI has a models endpoint:
        GET https://generativelanguage.googleapis.com/v1beta/models

        TODO: Implement full Google AI support.
        """
        logger.warning("Google AI list_models not implemented")
        return []

    async def get_account_info(self, config: AdapterConfig) -> AccountInfo | None:
        """
        Get account information from Google.

        Google AI doesn't expose detailed account info via API.
        """
        return None


# Singleton instance
google_adapter = GoogleAIAdapter()
