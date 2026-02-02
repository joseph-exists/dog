"""
LLM Catalog routes.
"""

from os import name
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    LLMModel,
    LLMModelCreate,
    LLMModelPublic,
    LLMModelsPublic,
    LLMProviderType,
    LLMProviderTypesPublic,
    LLMProviderTypeCreate,
    LLMProviderTypePublic,
    UserAccessProvider,
    UserAccessProviderPublic,
    UserAccessProvidersPublic,
)

router = APIRouter(prefix="/llm-catalog", tags=["llm-catalog"])


# =============================================================================
# LLMProviderTypes ahhh yeah
# =============================================================================

# LLM ProviderTypes are heckin neat

@router.get("/providers/types/{provider_type_id}", response_model=LLMProviderTypePublic)
def get_provider_type(
    provider_type_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """ Get provider type by ID. """
    provider_type = session.get(LLMProviderType, provider_type_id)
    if not provider_type:
        raise HTTPException(status_code=404, detail="provider type not found")
    return LLMProviderType

# @router.get("providers/types/provider_type_id", response_model=uuid.UUID)
# def get_provider_type_id(
#     provider_type_id: uuid.UUID,
#     session: SessionDep,
# ) -> Any:
#     """Get a single provider type by ID."""
#     provider_type = crud.get_llm_provider_type(
#         session=session,
#         llm_provider_type_id=provider_type_id,
#     )
#     if not provider_type:
#         raise HTTPException(status_code=404, detail="provider type not found")
#     return provider_type.id



    # provider_type = crud.get_llm_provider_type_id_by_name(
    #     session=session,
    #     name=provider_type_name,
    # )
    # if not provider_type:
    #     raise HTTPException(status_code=404, detail="provider type not found")
    # return LLMProviderTypePublic(**provider_type.model_dump())






    # user_access_provider = crud.get_user_access_provider(
    #     session=session,
    #     user_access_provider_id=user_access_provider_id,
    #     user_id=current_user.id,
    # )
    # if not user
    # if not user_access_provider:
    #     raise HTTPException(status_code=404, detail="user access provider not found")
    # return user_access_provider.alpha_provider_type_id







# =============================================================================
# Provider Endpoints
# =============================================================================

# migrated to list_providers in llm_providers.py




@router.get("/providers/{provider_id}/models", response_model=LLMModelsPublic)
def list_provider_models(
    provider_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    # skip: int = 0,
    # limit: int = 100,
) -> Any:
    """List all models for a specific user's user access provider."""
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
    # TODO review get providers/uap-apti
    # add some frickin models
    # use the model add script
    
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
