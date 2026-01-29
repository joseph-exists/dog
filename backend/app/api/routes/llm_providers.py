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
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import encrypt_api_key
from app.models import (
    Message,
    UserAccessProvider,
    UserAccessProviderCreate,
    UserAccessProviderPublic,
    UserAccessProviderUpdate,
    UserAccessProvidersPublic,
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
    statement = (
        select(UserAccessProvider)
        .where(UserAccessProvider.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    providers = session.exec(statement).all()
    data = [
        UserAccessProviderPublic(**provider.model_dump())
        for provider in providers
    ]
    return UserAccessProvidersPublic(data=data, count=len(data))


@router.post("/", response_model=UserAccessProviderPublic)
def create_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: UserAccessProviderCreate,
) -> Any:
    """Create a new access provider configuration."""
    # If setting as default, unset other defaults for this user
    if provider_in.is_default:
        _unset_defaults(session, current_user.id)

    provider_data = provider_in.model_dump(exclude={"api_key"})
    provider = UserAccessProvider(
        **provider_data,
        user_id=current_user.id,
        api_key_encrypted=encrypt_api_key(provider_in.api_key),
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return UserAccessProviderPublic(**provider.model_dump())


@router.get("/{provider_id}", response_model=UserAccessProviderPublic)
def get_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get a specific LLM provider configuration."""
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
    provider.updated_at = datetime.now()
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
        UserAccessProvider.is_default == True,
    )
    for provider in session.exec(statement).all():
        provider.is_default = False
        session.add(provider)


# TODO: Add back test connection helpers when test endpoint is redesigned
# Will need to test specific model + provider combinations
