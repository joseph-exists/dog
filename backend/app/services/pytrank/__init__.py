"""pytrank - pydantic_ai model/provider/profile management layer."""

from .model_manager import (
    KnownModelName,
    Model,
    ModelRequestParameters,
    StreamedResponse,
    cached_async_http_client,
    infer_model,
)
from .profile_manager import (
    DEFAULT_PROFILE,
    InlineDefsJsonSchemaTransformer,
    JsonSchemaTransformer,
    ModelProfile,
    ModelProfileSpec,
)
from .providers_interface import Provider, infer_provider, infer_provider_class

__all__ = [
    # Profiles
    "ModelProfile",
    "ModelProfileSpec",
    "DEFAULT_PROFILE",
    "InlineDefsJsonSchemaTransformer",
    "JsonSchemaTransformer",
    # Providers
    "Provider",
    "infer_provider",
    "infer_provider_class",
    # Models
    "Model",
    "KnownModelName",
    "ModelRequestParameters",
    "StreamedResponse",
    "infer_model",
    "cached_async_http_client",
]
