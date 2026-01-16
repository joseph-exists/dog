"""
LLM Provider configuration routes.

Users can manage their own LLM provider configurations including
API keys and custom endpoints. API keys are encrypted at rest.
"""
import uuid
from datetime import datetime
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.core.security import encrypt_api_key, decrypt_api_key
from app.models import (
    LLMProviderType,
    Message,
    UserLLMProvider,
    UserLLMProviderCreate,
    UserLLMProviderPublic,
    UserLLMProviderUpdate,
    UserLLMProvidersPublic,
)

router = APIRouter(prefix="/llm-providers", tags=["llm-providers"])


@router.get("/", response_model=UserLLMProvidersPublic)
def list_providers(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 50,
) -> Any:
    """List user's LLM provider configurations."""
    statement = (
        select(UserLLMProvider)
        .where(UserLLMProvider.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    providers = session.exec(statement).all()
    count = len(providers)
    return UserLLMProvidersPublic(data=providers, count=count)


@router.post("/", response_model=UserLLMProviderPublic)
def create_provider(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: UserLLMProviderCreate,
) -> Any:
    """Create a new LLM provider configuration."""
    # If setting as default, unset other defaults of same type
    if provider_in.is_default:
        _unset_defaults(session, current_user.id, provider_in.provider_type)

    provider = UserLLMProvider(
        **provider_in.model_dump(exclude={"api_key"}),
        user_id=current_user.id,
        api_key_encrypted=encrypt_api_key(provider_in.api_key),
    )
    session.add(provider)
    session.commit()
    session.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=UserLLMProviderPublic)
def get_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Get a specific LLM provider configuration."""
    provider = session.get(UserLLMProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.patch("/{provider_id}", response_model=UserLLMProviderPublic)
def update_provider(
    *,
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    provider_in: UserLLMProviderUpdate,
) -> Any:
    """Update an LLM provider configuration."""
    provider = session.get(UserLLMProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    update_data = provider_in.model_dump(exclude_unset=True)

    # Handle default flag - unset others if setting this as default
    if update_data.get("is_default"):
        _unset_defaults(session, current_user.id, provider.provider_type)

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
    return provider


@router.delete("/{provider_id}", response_model=Message)
def delete_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """Delete an LLM provider configuration."""
    provider = session.get(UserLLMProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")
    session.delete(provider)
    session.commit()
    return Message(message="Provider deleted successfully")


@router.post("/{provider_id}/test", response_model=Message)
async def test_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Test LLM provider connection.

    Makes a minimal API call to verify credentials work.
    """
    provider = session.get(UserLLMProvider, provider_id)
    if not provider or provider.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Provider not found")

    api_key = decrypt_api_key(provider.api_key_encrypted)

    try:
        success = await _test_provider_connection(
            provider_type=provider.provider_type,
            api_key=api_key,
            base_url=provider.base_url,
        )

        provider.last_tested_at = datetime.now()
        provider.last_test_success = success
        session.add(provider)
        session.commit()

        if success:
            return Message(message="Connection successful")
        else:
            raise HTTPException(status_code=400, detail="Connection test failed")

    except HTTPException:
        raise
    except Exception as e:
        provider.last_tested_at = datetime.now()
        provider.last_test_success = False
        session.add(provider)
        session.commit()
        raise HTTPException(status_code=400, detail=f"Connection test failed: {str(e)}")


def _unset_defaults(session: SessionDep, user_id: uuid.UUID, provider_type: LLMProviderType) -> None:
    """Unset default flag on all providers of a type for a user."""
    statement = select(UserLLMProvider).where(
        UserLLMProvider.user_id == user_id,
        UserLLMProvider.provider_type == provider_type,
        UserLLMProvider.is_default == True,
    )
    for provider in session.exec(statement).all():
        provider.is_default = False
        session.add(provider)


async def _test_provider_connection(
    provider_type: LLMProviderType,
    api_key: str,
    base_url: str | None,
) -> bool:
    """
    Test connection to an LLM provider.

    Makes minimal API calls to validate credentials without incurring
    significant costs. Each provider has a different validation approach.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        if provider_type in (LLMProviderType.OPENAI, LLMProviderType.OPENAI_COMPATIBLE):
            # List models endpoint - lightweight, validates API key
            url = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(url, headers=headers)
            return response.status_code == 200

        elif provider_type == LLMProviderType.ANTHROPIC:
            # Anthropic doesn't have a models list endpoint, so we check with a minimal message
            # Using /v1/messages endpoint with tiny max_tokens
            url = (base_url.rstrip("/") if base_url else "https://api.anthropic.com/v1") + "/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            # This will return 400 with valid key (bad request due to empty content)
            # but 401 with invalid key
            response = await client.post(
                url,
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            # 200 = success, 400 = valid key but request issue (still means key works)
            return response.status_code in (200, 400)

        elif provider_type == LLMProviderType.GOOGLE:
            # Google AI - list models endpoint
            url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            response = await client.get(url)
            return response.status_code == 200

        else:
            return False
