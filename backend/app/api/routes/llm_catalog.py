"""
LLM Catalog routes.

Public API for browsing available LLM providers and models.
Requires auth for custom models


"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session

from app import crud
from app.api.deps import CurrentUser, OptionalUser, SessionDep
from app.models import (
    LLMModel,
    LLMModelCreate,
    LLMModelPublic,
    LLMModelsPublic,
    LLMProviderType,
    LLMProviderTypeCreate,
    LLMProviderTypePublic,
    UserAccessProvider,
    UserAccessProviderPublic,
    UserAccessProvidersPublic,
)

router = APIRouter(prefix="/llm-catalog", tags=["llm-catalog"])


# =============================================================================
# Helper Functions
# =============================================================================


def _get_provider_type_name(*, session: SessionDep, provider_type_id: uuid.UUID | None) -> str | None:
    """Resolve provider_type.id to to provider_type.name in LLMProviderTypePublic.
       can be called using UserAccessProvider.alpha_provider_type_id, FrontierAccessProvider.provider_type.id, LLMProviderTypePublic.id, or UserAgentConfig.provider_type_id.
    """

def _get_provider_type_id_for_user_access_provider(*, session: SessionDep, provider_type_id: uuid.UUID) -> uuid.UUID | None:
    """
    can be called using 
    UserAccessProvider.alpha_provider_type_id,
    FrontierAccessProvider.provider_type.id,
    LLMProviderTypePublic.id,
    UserAgentConfig.provider_type_id.
    """
    provider_type= provider_type_id

    return provider_type




# =============================================================================
# Provider Endpoints
# =============================================================================

@router.get("/providers", response_model=UserAccessProvidersPublic)
def list_providers(
    session: SessionDep,
    current_user: CurrentUser,  # Should require auth
    skip: int = 0,
    limit: int = 100,
    is_enabled: bool | None = Query(
        default=None, description="Filter by enabled status"
    ),
    is_validated: bool | None = Query(
        default=None, description="Filter by validated status"
    ),
) -> Any:
    """
    List current user's access providers.
    Each provider represents an API endpoint + key combo + primary provider_type on the user access provider.
    """
    providers, count = crud.get_user_access_providers(
        session=session,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        is_enabled=is_enabled,
        is_validated=is_validated,

    )

    return UserAccessProvidersPublic(data=[
        UserAccessProviderPublic(**p.model_dump())
        for p in providers
    ], count=count)


# @router.get("/user-access-providers/{llmprovidertype_id}", response_model=UserAccessProviderPublic)
# def get_provider(
#     user_access_provider_id: uuid.UUID,
#     session: SessionDep,
#     user_id: uuid.UUID,
# ) -> Any:
#     """
#     Get a single user access provider by ID.

#     No authentication required.
#     """
#     provider = crud.get_user_access_provider(
#         user_id=user_id,
#         session=session,
#         user_access_provider_id=user_access_provider_id,
#     )
#     if not provider:
#         raise HTTPException(status_code=404, detail="Provider not found")

#     # TODO: Implement model_count CRUD function
#     # TODO: understand what the hell this is talking about
#     # model_count = 0

#     return UserAccessProviderPublic(
#         **provider.model_dump(),
#         model_count=model_count,
#         provider_type=_get_provider_type_name(provider) if hasattr(provider, 'provider_type_id') else None,
#     )


@router.get("/providers/{provider_id}/models", response_model=LLMModelsPublic)
def list_provider_models(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    # skip: int = 0,
    # limit: int = 100,
) -> Any:
    """List all models for a specific user's user access provider.
       For now, what we're going to do is hand-load models in the backend into LLMModels and associate them
       with the provider_types.  #TODO near term: enable polling w/ API key, start with OpenAPI and go from there.

    """
    provider = crud.get_user_access_provider(
        session=session,
        user_access_provider_id=provider_id,
        user_id=current_user.id,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="user access provider not found")

    return LLMModelsPublic(data=[], count=0)


# =============================================================================
# Custom Model Endpoints (Authenticated)
# =============================================================================
# TODO: give users the ability to define and refine custom model types - tricky feature but important
# TODO: maybe this is easier than I'm thinking it is - use the secondary capabilities dict?
# @router.get("/models/custom", response_model=LLMModelsPublic)

# # TODO: 
# @router.post("/models/custom", response_model=LLMModelPublic)
# def create_custom_model(
#     session: SessionDep,
#     current_user: CurrentUser,
#     model_in: LLMModelCreate,
# ) -> Any:
#     """Create a custom model for the current user."""
#     pass

# TODO: Implement now that LLM functions exist

# def list_custom_models(
#     session: SessionDep,
#     current_user: CurrentUser,
# ) -> Any:
#     """List the current user's custom models."""
#     pass


# =============================================================================
# Model Endpoints
# =============================================================================


@router.get("/models", response_model=LLMModelsPublic)
def list_models(
    session: SessionDep,
    current_user: CurrentUser,
    #skip: int = 0,
    #limit: int = 100,
) -> Any:
    """List all LLM models available to current user."""
    # TODO: correctly call crud.get_llm_models() ~line 159, crud.py
    return LLMModelsPublic(data=[], count=0)

@router.get("/models/uap", response_model=LLMModelsPublic)
def list_models_for_uap(
    user_access_provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """List all models for a specific user's user access provider's provider_type -
    to get the provider type for a user_access_provider, we call:
    crud.get_user_access_provider - which returns a UserAccessProvider.
    alpha_provider_type_id.UserAccessProvider has FK on provider_type.id.
    then you can call crud.get_llm_models with that provider_type_id as primary_provider_type_id

    """
    user_access_provider =   crud.get_user_access_provider(
        session=session,
        user_access_provider_id=user_access_provider_id,
        user_id=current_user.id,
    )
    if not user_access_provider:
        raise HTTPException(status_code=404, detail="user access provider not found")

    list_of_models= crud.get_llm_models(
        session=session,
        primary_provider_type_id=user_access_provider.alpha_provider_type_id,
    )

    return list_of_models


#