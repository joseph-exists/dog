"""
LLM Provider configuration routes.

Users can manage their own LLM provider configurations including
API keys and custom endpoints. API keys are encrypted at rest.
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import encrypt_api_key
from app.models import (
    LLMProviderType,
    LLMProviderTypePublic,
    LLMProviderTypesPublic,
    Message,
    UserAccessProvider,
    UserAccessProviderCreate,
    UserAccessProviderPublic,
    UserAccessProvidersPublic,
    UserAccessProviderUpdate,
)
from app.services.provider_adapters import (
    AccountInfo,
    ModelInfo,
    RateLimitInfo,
    TestResult,
    get_provider_account_info,
    list_provider_models,
    test_provider_connection,
)

router = APIRouter(prefix="/llm-providers", tags=["llm-providers"])
logger = logging.getLogger(__name__)

# Cache freshness threshold (1 hour)
MODELS_CACHE_MAX_AGE = timedelta(hours=1)


# =============================================================================
# Response Models for Validation/Testing Endpoints
# =============================================================================


class QuickTestResult(BaseModel):
    """Quick pass/fail validation result."""
    valid: bool = Field(description="Whether the provider credentials are valid")
    error: str | None = Field(default=None, description="Error message if invalid")
    error_code: str | None = Field(default=None, description="Error code for programmatic handling")


class DetailedTestResult(BaseModel):
    """Detailed test result with diagnostics."""
    valid: bool = Field(description="Whether the provider credentials are valid")
    error: str | None = Field(default=None, description="Error message if invalid")
    error_code: str | None = Field(default=None, description="Error code for programmatic handling")
    models: list[ModelInfo] = Field(default_factory=list, description="Available models from provider")
    rate_limits: RateLimitInfo | None = Field(default=None, description="Current rate limit status")
    account_info: AccountInfo | None = Field(default=None, description="Account information if available")
    latency_ms: int | None = Field(default=None, description="Connection latency in milliseconds")


class ModelsListResponse(BaseModel):
    """Response for cached/live model listing."""
    models: list[str] = Field(description="List of available model IDs")
    cached: bool = Field(description="Whether this was served from cache")
    cached_at: datetime | None = Field(default=None, description="When the cache was last updated")


@router.get("/", response_model=UserAccessProvidersPublic)
def list_providers(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List user's LLM provider configurations."""

    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(UserAccessProvider)
        count = session.exec(count_statement).one()
        statement = select(UserAccessProvider).offset(skip).limit(limit)
        providers = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(UserAccessProvider)
            .where(UserAccessProvider.owner_id == current_user.id)
        )
        count = session.exec(count_statement).one()

    statement = (
        select(UserAccessProvider)
        .where(UserAccessProvider.owner_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )

    providers = session.exec(statement).all()

    return UserAccessProvidersPublic(data=providers, count=count)


@router.get("/provider-type-list", response_model=LLMProviderTypesPublic)
def get_provider_type_list(
    current_user: CurrentUser,
    session: SessionDep,
) -> Any:
    """Return all provider types."""
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(LLMProviderType)
        count = session.exec(count_statement).one()
        statement = select(LLMProviderType)
        llmprovidertypes = session.exec(statement).all()
    else:
        count_statement = (
            select(func.count())
            .select_from(LLMProviderType)
            .where(LLMProviderType.validated.is_(True))
        )
        # if an LLMProviderType isn't validated, it can't be seen by non-superusers.  hacky overload, not what we want,
        # need to think about distinctions here.
        count = session.exec(count_statement).one()
        statement = select(LLMProviderType).where(LLMProviderType.is_system.is_(True))
        llmprovidertypes = session.exec(statement).all()
        if not llmprovidertypes:
            raise HTTPException(status_code=404, detail="nothing not for finding")
    return LLMProviderTypesPublic(data=llmprovidertypes, count=count)  # type: ignore


@router.get("/providers/uap-apti", response_model=UserAccessProviderPublic)
def get_alpha_provider_type_id_for_user_access_provider(
    current_user: CurrentUser,
    session: SessionDep,
    user_access_provider_id: uuid.UUID | None = None,
    user_access_provider: uuid.UUID | None = None,
) -> Any:
    """
    Return the user access provider (including alpha_provider_type_id).
    ID from path (user_access_provider_id) or query (user_access_provider).
    """
    provider_id = user_access_provider_id or user_access_provider
    if not provider_id:
        raise HTTPException(status_code=400, detail="user_access_provider_id required")
    uap = session.get(UserAccessProvider, provider_id)
    if not uap:
        raise HTTPException(status_code=404, detail="uap not found")
    if not current_user.is_superuser and uap.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Not Found")
    return uap


@router.get("/by_name/{provider_type_name}", response_model=LLMProviderTypePublic)
def get_provider_type_id_by_name(
    provider_type_name: str,
    session: SessionDep,
) -> LLMProviderTypePublic:
    """Get a single provider type by name, return the id"""
    provider_type = session.exec(
        select(LLMProviderType).where(LLMProviderType.name == provider_type_name)
    ).first()
    if not provider_type:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider_type


@router.post("/", response_model=UserAccessProviderPublic)
def create_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: UserAccessProviderCreate,
) -> Any:
    """Create a new access provider configuration."""
    # If setting as default, unset other defaults for this user
    # TODO: add this back in once it's working again.
    # if provider_in.is_default:
    #     _unset_defaults(session, current_user.id)

    provider = UserAccessProvider.model_validate(provider_in, update={"user_id": current_user.id})
    # provider_data = provider_in.model_dump(exclude={"api_key"})
    provider_data = provider_in.model_dump()
    provider = UserAccessProvider(
        **provider_data,
        user_id=current_user.id,
        api_key_encrypted=encrypt_api_key(provider_in.api_key),
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=UserAccessProviderPublic)
def get_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """returns a user access provider when called by its id."""
    provider = session.get(UserAccessProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")
    return UserAccessProviderPublic(**provider.model_dump())


@router.patch("/{provider_id}", response_model=UserAccessProviderPublic)
def update_provider(
    *,
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: UserAccessProviderUpdate,
) -> Any:
    """Update an LLM provider configuration."""
    provider = session.get(UserAccessProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_in.model_dump(exclude_unset=True)

    # Handle default flag - unset others if setting this as default
    if update_data.get("is_default"):
        _unset_defaults(session, current_user.id)

    # Handle API key update - encrypt new key
    if "api_key" in update_data:
        api_key = update_data.pop("api_key")
        if api_key:
            provider.api_key_encrypted = encrypt_api_key(api_key)

    # Update other fields
    provider.sqlmodel_update(update_data)
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return UserAccessProviderPublic(**provider.model_dump())


@router.delete("/{provider_id}", response_model=Message)
def delete_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete an LLM provider configuration."""
    provider = session.get(UserAccessProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")
    session.delete(provider)
    session.commit()
    return Message(message="Provider deleted successfully")


# =============================================================================
# Validation/Testing Endpoints
# =============================================================================


@router.post("/{provider_id}/test", response_model=QuickTestResult)
async def test_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> QuickTestResult:
    """
    Quick pass/fail validation of provider credentials.

    Tests the API key and connection to the provider.
    Updates the provider's validation state fields.
    """
    # Load provider
    provider = session.get(UserAccessProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to test this provider")

    # Test connection using adapter service
    result: TestResult = await test_provider_connection(provider)

    # Update provider validation state
    provider.is_validated = result.success
    provider.last_validated_at = datetime.now(timezone.utc)
    provider.validation_error = None if result.success else result.message

    session.add(provider)
    session.commit()
    session.refresh(provider)

    return QuickTestResult(
        valid=result.success,
        error=None if result.success else result.message,
        error_code=None if result.success else result.status.value,
    )


@router.post("/{provider_id}/test/detailed", response_model=DetailedTestResult)
async def test_provider_detailed(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> DetailedTestResult:
    """
    Detailed provider validation with full diagnostics.

    Tests credentials, retrieves available models, and gets account info.
    Updates the provider's validation state and model cache.
    """
    # Load provider
    provider = session.get(UserAccessProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to test this provider")

    # Test connection using adapter service
    test_result: TestResult = await test_provider_connection(provider)

    # Update provider validation state
    provider.is_validated = test_result.success
    provider.last_validated_at = datetime.now(timezone.utc)
    provider.validation_error = None if test_result.success else test_result.message

    # If connection succeeded, fetch models and account info
    models: list[ModelInfo] = []
    account_info: AccountInfo | None = None

    if test_result.success:
        # Fetch models
        models = await list_provider_models(provider)

        # Update model cache with model IDs
        now = datetime.now(timezone.utc)
        provider.available_models_cache = [m.model_id for m in models]
        provider.models_cached_at = now

        # Fetch account info
        account_info = await get_provider_account_info(provider)

    session.add(provider)
    session.commit()
    session.refresh(provider)

    return DetailedTestResult(
        valid=test_result.success,
        error=None if test_result.success else test_result.message,
        error_code=None if test_result.success else test_result.status.value,
        models=models,
        rate_limits=account_info.rate_limits if account_info else None,
        account_info=account_info,
        latency_ms=test_result.latency_ms,
    )


@router.get("/{provider_id}/models", response_model=ModelsListResponse)
async def get_provider_models(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    force_refresh: bool = False,
) -> ModelsListResponse:
    """
    Get available models for a provider.

    Returns cached models if available and fresh (< 1 hour).
    Otherwise fetches live from the provider API and updates cache.

    Args:
        force_refresh: If True, bypass cache and fetch fresh data
    """
    # Load provider
    provider = session.get(UserAccessProvider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized to access this provider")

    # Check if cache is fresh
    now = datetime.now(timezone.utc)
    cache_is_fresh = (
        not force_refresh
        and provider.available_models_cache is not None
        and provider.models_cached_at is not None
        and (now - provider.models_cached_at.replace(tzinfo=timezone.utc)) < MODELS_CACHE_MAX_AGE
    )

    if cache_is_fresh:
        return ModelsListResponse(
            models=provider.available_models_cache or [],
            cached=True,
            cached_at=provider.models_cached_at,
        )

    # Fetch fresh models
    models = await list_provider_models(provider)
    model_ids = [m.model_id for m in models]

    # Update cache
    provider.available_models_cache = model_ids
    provider.models_cached_at = now
    session.add(provider)
    session.commit()
    session.refresh(provider)

    return ModelsListResponse(
        models=model_ids,
        cached=False,
        cached_at=now,
    )


def _unset_defaults(session: SessionDep, user_id: uuid.UUID) -> None:
    """Unset default flag on all providers for a user."""
    statement = select(UserAccessProvider).where(
        UserAccessProvider.user_id == user_id,
        UserAccessProvider.is_default,
    )
    for provider in session.exec(statement).all():
        provider.is_default = False
        session.add(provider)



