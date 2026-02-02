"""
LLM Provider configuration routes.

Users can manage their own LLM provider configurations including
API keys and custom endpoints. API keys are encrypted at rest.
"""
import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select, func

from app.api.deps import CurrentUser, SessionDep
from app.core.security import encrypt_api_key
from app.models import (
    LLMProviderType,
    LLMProviderTypesPublic,
    Message,
    UserAccessProvider,
    UserAccessProviderCreate,
    UserAccessProviderPublic,
    UserAccessProviderUpdate,
    UserAccessProvidersPublic,
    LLMProviderTypePublic
)

router = APIRouter(prefix="/llm-providers", tags=["llm-providers"])
logger = logging.getLogger(__name__)


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
            .where(LLMProviderType.is_system.is_(False))
        )
        count = session.exec(count_statement).one()
        statement = select(LLMProviderType).where(LLMProviderType.is_system.is_(False))
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

    # TODO : add encryption back once this isn't stupidly broken
    provider_data = provider_in.model_dump(exclude={"api_key"})
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


# TODO: Redesign test endpoint - need model_id to know which API protocol to test
# @router.post("/{provider_id}/test", response_model=Message)
# async def test_provider(
#     provider_id: uuid.UUID,
#     session: SessionDep,
#     current_user: CurrentUser,
#     model_id: uuid.UUID,  # Need this to determine API protocol
# ) -> Any:
#     """
#     Test LLM provider connection with a specific model.
#
#     Since provider can serve multiple API types (OpenAI + Google),
#     we need to know which model to test against.
#     """
#     pass


def _unset_defaults(session: SessionDep, user_id: uuid.UUID) -> None:
    """Unset default flag on all providers for a user."""
    statement = select(UserAccessProvider).where(
        UserAccessProvider.user_id == user_id,
        UserAccessProvider.is_default,
    )
    for provider in session.exec(statement).all():
        provider.is_default = False
        session.add(provider)


# TODO: Add back test connection helpers when test endpoint is redesigned
# Will need to test specific model + provider combinations

