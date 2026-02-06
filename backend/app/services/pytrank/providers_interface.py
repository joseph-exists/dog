"""Providers for the API clients.

The providers are in charge of providing an authenticated client to the API.
"""

from __future__ import annotations as _annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from .profile_manager import ModelProfile

InterfaceClient = TypeVar("InterfaceClient")


class Provider(ABC, Generic[InterfaceClient]):
    """Abstract class for a provider.

    The provider is in charge of providing an authenticated client to the API.

    Each provider only supports a specific interface. A interface can be supported by multiple providers.

    For example, the `OpenAIChatModel` interface can be supported by the `OpenAIProvider` and the `DeepSeekProvider`.
    """

    _client: InterfaceClient

    @property
    @abstractmethod
    def name(self) -> str:
        """The provider name."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def base_url(self) -> str:
        """The base URL for the provider API."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def client(self) -> InterfaceClient:
        """The client for the provider."""
        raise NotImplementedError()

    def model_profile(self, model_name: str) -> ModelProfile | None:
        """The model profile for the named model, if available."""
        return None  # pragma: no cover

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, base_url={self.base_url})"  # pragma: lax no cover


def infer_provider_class(provider: str) -> type[Provider[Any]]:  # noqa: C901
    """Infers the provider class from the provider name."""
    if provider in ("openai", "openai-chat", "openai-responses"):
        from pydantic_ai.providers.openai import OpenAIProvider

        return OpenAIProvider
    elif provider == "deepseek":
        from pydantic_ai.providers.deepseek import DeepSeekProvider

        return DeepSeekProvider
    elif provider == "openrouter":
        from pydantic_ai.providers.openrouter import OpenRouterProvider

        return OpenRouterProvider
    elif provider == "vercel":
        from pydantic_ai.providers.vercel import VercelProvider

        return VercelProvider
    elif provider == "azure":
        from pydantic_ai.providers.azure import AzureProvider

        return AzureProvider
    elif provider in ("google-vertex", "google-gla"):
        from pydantic_ai.providers.google import GoogleProvider

        return GoogleProvider
    elif provider == "bedrock":
        from pydantic_ai.providers.bedrock import BedrockProvider

        return BedrockProvider
    elif provider == "groq":
        from pydantic_ai.providers.groq import GroqProvider

        return GroqProvider
    elif provider == "anthropic":
        from pydantic_ai.providers.anthropic import AnthropicProvider

        return AnthropicProvider
    elif provider == "mistral":
        from pydantic_ai.providers.mistral import MistralProvider

        return MistralProvider
    elif provider == "cerebras":
        from pydantic_ai.providers.cerebras import CerebrasProvider

        return CerebrasProvider
    elif provider == "cohere":
        from pydantic_ai.providers.cohere import CohereProvider

        return CohereProvider
    elif provider == "grok":
        from pydantic_ai.providers.grok import GrokProvider

        return GrokProvider
    elif provider == "moonshotai":
        from pydantic_ai.providers.moonshotai import MoonshotAIProvider

        return MoonshotAIProvider
    elif provider == "fireworks":
        from pydantic_ai.providers.fireworks import FireworksProvider

        return FireworksProvider
    elif provider == "together":
        from pydantic_ai.providers.together import TogetherProvider

        return TogetherProvider
    elif provider == "heroku":
        from pydantic_ai.providers.heroku import HerokuProvider

        return HerokuProvider
    elif provider == "huggingface":
        from pydantic_ai.providers.huggingface import HuggingFaceProvider

        return HuggingFaceProvider
    elif provider == "ollama":
        from pydantic_ai.providers.ollama import OllamaProvider

        return OllamaProvider
    elif provider == "github":
        from pydantic_ai.providers.github import GitHubProvider

        return GitHubProvider
    elif provider == "litellm":
        from pydantic_ai.providers.litellm import LiteLLMProvider

        return LiteLLMProvider
    elif provider == "nebius":
        from pydantic_ai.providers.nebius import NebiusProvider

        return NebiusProvider
    elif provider == "ovhcloud":
        from pydantic_ai.providers.ovhcloud import OVHcloudProvider

        return OVHcloudProvider
    elif provider == "outlines":
        from pydantic_ai.providers.outlines import OutlinesProvider

        return OutlinesProvider
    elif provider == "nous":
        from .provider_gateway import NousProvider

        return NousProvider
    else:  # pragma: no cover
        raise ValueError(f"Unknown provider: {provider}")


def infer_provider(provider: str) -> Provider[Any]:
    """Infer the provider from the provider name."""
    if provider.startswith("nous/"):
        from .provider_gateway import NousProvider

        # TODO : figure this out ASAP.
        return NousProvider(...)
    if provider.startswith("gateway/"):
        from .provider_gateway import gateway_provider

        upstream_provider = provider.removeprefix("gateway/")
        return gateway_provider(upstream_provider)
    elif provider in ("google-vertex", "google-gla"):
        from pydantic_ai.providers.google import GoogleProvider

        return GoogleProvider(vertexai=provider == "google-vertex")
    else:
        provider_class = infer_provider_class(provider)
        return provider_class()
