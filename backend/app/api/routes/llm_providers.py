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
from sqlmodel import Session, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.core.security import encrypt_api_key, decrypt_api_key
from app.models import (
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
    canonical_type = _canonical_provider_type_name(session, provider_in.provider_type)
    if not canonical_type:
        raise HTTPException(status_code=400, detail="Unknown provider type")

    # If setting as default, unset other defaults of same type
    if provider_in.is_default:
        _unset_defaults(session, current_user.id, canonical_type)

    provider_data = provider_in.model_dump(exclude={"api_key"})
    provider_data["provider_type"] = canonical_type
    provider = UserLLMProvider(
        **provider_data,
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
        provider_type_name = _canonical_provider_type_name(session, provider.provider_type)
        if not provider_type_name:
            raise HTTPException(status_code=400, detail="Unknown provider type")

        success = await _test_provider_connection(
            provider_type=provider_type_name,
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


def _unset_defaults(session: SessionDep, user_id: uuid.UUID, provider_type: str) -> None:
    """Unset default flag on all providers of a type for a user."""
    if not provider_type:
        return
    statement = select(UserLLMProvider).where(
        UserLLMProvider.user_id == user_id,
        UserLLMProvider.provider_type == provider_type,
        UserLLMProvider.is_default == True,
    )
    for provider in session.exec(statement).all():
        provider.is_default = False
        session.add(provider)


async def _test_provider_connection(
    provider_type: str,
    api_key: str,
    base_url: str | None,
) -> bool:
    """
    Test connection to an LLM provider.

    Makes minimal API calls to validate credentials without incurring
    significant costs. Each provider has a different validation approach.
    """
    normalized = provider_type.lower() if provider_type else ""
    async with httpx.AsyncClient(timeout=15.0) as client:
        if normalized in ("openai", "openai_compatible"):
            if not api_key:
                return False
            url = (base_url.rstrip("/") if base_url else "https://api.openai.com/v1") + "/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = await client.get(url, headers=headers)
            return response.status_code == 200

        if normalized == "anthropic":
            url = (base_url.rstrip("/") if base_url else "https://api.anthropic.com/v1") + "/messages"
            headers = {
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            }
            response = await client.post(
                url,
                headers=headers,
                json={
                    "model": "claude-3-haiku-20240307",
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "hi"}],
                },
            )
            return response.status_code in (200, 400)

        if normalized == "google":
            if not api_key:
                return False
            url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            response = await client.get(url)
            return response.status_code == 200

        return False


def _canonical_provider_type_name(session: Session, raw_provider_type: str | None) -> str | None:
    """Return the canonical provider type name, or None if the type is unknown."""
    if not raw_provider_type:
        return None
    type_obj = crud.get_llm_provider_type_by_name(
        session=session, name=raw_provider_type
    )
    return type_obj.name if type_obj else None
