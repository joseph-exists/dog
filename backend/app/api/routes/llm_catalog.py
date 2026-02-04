"""
LLM Catalog routes.

Provides endpoints for browsing and managing the LLM model catalog.

Read operations (GET) are available to authenticated users.
Write operations (POST/PATCH/DELETE) require superuser privileges.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    LLMModel,
    LLMModelCreate,
    LLMModelPublic,
    LLMModelsPublic,
    LLMModelUpdate,
    LLMProviderType,
    LLMProviderTypesPublic,
    LLMProviderTypeCreate,
    LLMProviderTypePublic,
    Message,
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
    return provider_type

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
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all models for a specific user's user access provider."""
    provider = crud.get_user_access_provider(
        session=session,
        user_access_provider_id=provider_id,
        user_id=current_user.id,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="user access provider not found")
    models, count = crud.get_llm_models(
        session=session,
        primary_provider_type_id=provider.alpha_provider_type_id,
        skip=skip,
        limit=limit,
    )
    return LLMModelsPublic(
        data=[LLMModelPublic(**m.model_dump()) for m in models],
        count=count,
    )


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
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all LLM models available to current user."""
    models, count = crud.get_llm_models(
        session=session,
        primary_provider_type_id=None,
        skip=skip,
        limit=limit,
    )
    return LLMModelsPublic(
        data=[LLMModelPublic(**m.model_dump()) for m in models],
        count=count,
    )


@router.get("/models/uap", response_model=LLMModelsPublic)
def list_models_for_uap(
    session: SessionDep,
    current_user: CurrentUser,
    user_access_provider_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """List all models for a specific user's user access provider's provider_type."""
    user_access_provider = crud.get_user_access_provider(
        session=session,
        user_access_provider_id=user_access_provider_id,
        user_id=current_user.id,
    )
    if not user_access_provider:
        raise HTTPException(status_code=404, detail="user access provider not found")
    models, count = crud.get_llm_models(
        session=session,
        primary_provider_type_id=user_access_provider.alpha_provider_type_id,
        skip=skip,
        limit=limit,
    )
    return LLMModelsPublic(
        data=[LLMModelPublic(**m.model_dump()) for m in models],
        count=count,
    )


# =============================================================================
# Single Model Endpoints
# =============================================================================


@router.get("/models/{model_id}", response_model=LLMModelPublic)
def get_model(
    model_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> Any:
    """
    Get a single LLM model by UUID.

    Available to all authenticated users.
    """
    model = crud.get_llm_model(session=session, llm_model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return LLMModelPublic(**model.model_dump())


# =============================================================================
# Model Admin Endpoints (Superuser Only)
# =============================================================================


@router.post(
    "/models",
    response_model=LLMModelPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def create_model(
    session: SessionDep,
    current_user: CurrentUser,
    model_in: LLMModelCreate,
) -> Any:
    """
    Create a new LLM model in the catalog.

    **Superuser only.**

    The model will be linked to a provider type via `primary_provider_type_id`.
    The combination of (primary_provider_type_id, model_id) must be unique.
    """
    # Verify provider type exists
    provider_type = crud.get_llm_provider_type(
        session=session,
        llm_provider_type_id=model_in.primary_provider_type_id,
    )
    if not provider_type:
        raise HTTPException(
            status_code=400,
            detail=f"Provider type not found: {model_in.primary_provider_type_id}"
        )

    model = crud.create_llm_model(
        session=session,
        llm_model_in=model_in,
        owner_id=current_user.id,
    )
    return LLMModelPublic(**model.model_dump())


@router.patch(
    "/models/{model_id}",
    response_model=LLMModelPublic,
    dependencies=[Depends(get_current_active_superuser)],
)
def update_model(
    model_id: uuid.UUID,
    session: SessionDep,
    model_in: LLMModelUpdate,
) -> Any:
    """
    Update an LLM model in the catalog.

    **Superuser only.**

    Only provide the fields you want to change.
    """
    model = crud.get_llm_model(session=session, llm_model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # If changing provider type, verify new one exists
    update_data = model_in.model_dump(exclude_unset=True)
    if "primary_provider_type_id" in update_data:
        provider_type = crud.get_llm_provider_type(
            session=session,
            llm_provider_type_id=update_data["primary_provider_type_id"],
        )
        if not provider_type:
            raise HTTPException(
                status_code=400,
                detail=f"Provider type not found: {update_data['primary_provider_type_id']}"
            )

    updated_model = crud.update_llm_model(
        session=session,
        llm_model=model,
        llm_model_update=model_in,
    )
    return LLMModelPublic(**updated_model.model_dump())


@router.delete(
    "/models/{model_id}",
    response_model=Message,
    dependencies=[Depends(get_current_active_superuser)],
)
def delete_model(
    model_id: uuid.UUID,
    session: SessionDep,
) -> Any:
    """
    Delete an LLM model from the catalog.

    **Superuser only.**

    Warning: This is permanent and may affect agents using this model.
    """
    model = crud.get_llm_model(session=session, llm_model_id=model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    crud.delete_llm_model(session=session, llm_model=model)
    return Message(message=f"Model '{model.display_name}' deleted successfully")
