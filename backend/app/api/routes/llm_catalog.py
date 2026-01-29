"""
LLM Catalog routes.

Public API for browsing available LLM providers and models.
Most endpoints are public (no auth required).
TODO: shift to authentication required.
TODO: only superuser can see/access/add system model default provider or assign it to an agent.


Custom model endpoints require authentication.
"""

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from sqlmodel import Session

from app import crud
from app.api.deps import CurrentUser, OptionalUser, SessionDep
from app.models import (
    LLMModelCreate,
    LLMModelPublic,
    LLMModelsGrouped,
    LLMModelsPublic,
    LLMProvider,
    LLMProviderPublic,
    LLMProvidersPublic,
    LLMProviderWithModels,
)

router = APIRouter(prefix="/llm-catalog", tags=["llm-catalog"])


# =============================================================================
# Provider Endpoints
# =============================================================================


@router.get("/providers", response_model=LLMProvidersPublic)
def list_providers(
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    provider_type: str | None = Query(
        default=None, description="Filter by provider type name"
    ),
    is_enabled: bool | None = Query(
        default=None, description="Filter by enabled status"
    ),
    is_system: bool | None = Query(
        default=None, description="Filter by system vs user-created"
    ),
    include_deleted: bool = Query(
        default=False, description="Include soft-deleted providers"
    ),
) -> Any:
    """
    List all LLM providers in the catalog.
    TODO: ENRICHMENT AND MODEL COUNT FUNCTION BROKEN
    No authentication required. Returns providers with their model counts.
    """
    provider_type_id = _resolve_provider_type_id(session=session, provider_type=provider_type)
    providers, count = crud.get_llm_providers(
        session=session,
        skip=skip,
        limit=limit,
        provider_type_id=provider_type_id,
        is_enabled=is_enabled,
        is_system=is_system,
        include_deleted=include_deleted,
    )

    # Enrich with model counts
    data = []
    for provider in providers:
        model_count = crud.get_llm_provider_model_count(
            session=session,
            provider_id=provider.id,
            include_deleted=include_deleted,
        )
        data.append(
            LLMProviderPublic(
                **provider.model_dump(),
                model_count=model_count,
                provider_type=_get_provider_type_name(provider),
            )
        )

    return LLMProvidersPublic(data=data, count=count)


@router.get("/providers/{provider_id}", response_model=LLMProviderPublic)
def get_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    include_deleted: bool = Query(default=False, description="Include if soft-deleted"),
) -> Any:
    """
    Get a single LLM provider by ID.

    No authentication required.
    """
    provider = crud.get_llm_provider(
        session=session,
        provider_id=provider_id,
        include_deleted=include_deleted,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model_count = crud.get_llm_provider_model_count(
        session=session,
        provider_id=provider.id,
        include_deleted=include_deleted,
    )

    return LLMProviderPublic(
        **provider.model_dump(),
        model_count=model_count,
        provider_type=_get_provider_type_name(provider),
    )


@router.get("/providers/{provider_id}/models", response_model=LLMModelsPublic)
def list_provider_models(
    provider_id: uuid.UUID,
    session: SessionDep,
    skip: int = 0,
    limit: int = 100,
    is_enabled: bool | None = Query(
        default=None, description="Filter by enabled status"
    ),
    is_deprecated: bool | None = Query(
        default=None, description="Filter by deprecation status"
    ),
    include_deleted: bool = Query(
        default=False, description="Include soft-deleted models"
    ),
) -> Any:
    """
    List all models for a specific provider.

    No authentication required.
    """
    # Verify provider exists
    provider = crud.get_llm_provider(
        session=session,
        provider_id=provider_id,
        include_deleted=include_deleted,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    results, count = crud.get_llm_models(
        session=session,
        skip=skip,
        limit=limit,
        provider_id=provider_id,
        is_enabled=is_enabled,
        is_deprecated=is_deprecated,
        include_deleted=include_deleted,
    )

    data = [
        LLMModelPublic(
            **model.model_dump(),
            provider_type=_get_provider_type_name(prov),
            provider_name=prov.name,
        )
        for model, prov in results
    ]

    return LLMModelsPublic(data=data, count=count)


# =============================================================================
# Custom Model Endpoints (Authenticated)
# =============================================================================


@router.post("/models/custom", response_model=LLMModelPublic)
def create_custom_model(
    session: SessionDep,
    current_user: CurrentUser,
    model_in: LLMModelCreate,
) -> Any:
    """
    Create a custom model for the current user.

    Requires authentication. The model will be associated with the user
    and marked as non-system (is_system=False).

    If display_name is not provided, it will be auto-generated from model_id.
    """
    # Verify provider exists
    provider = crud.get_llm_provider(session=session, provider_id=model_in.provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    model = crud.create_user_model(
        session=session,
        user_id=current_user.id,
        model_in=model_in,
    )

    return LLMModelPublic(
        **model.model_dump(),
        provider_type=_get_provider_type_name(provider),
        provider_name=provider.name,
    )


@router.get("/models/custom", response_model=LLMModelsPublic)
def list_custom_models(
    session: SessionDep,
    current_user: CurrentUser,
    provider_type: str | None = Query(
        default=None, description="Filter by provider type"
    ),
) -> Any:
    """
    List the current user's custom models.

    Requires authentication. Returns only models created by the authenticated user.
    """
    models = crud.get_user_models(
        session=session,
        user_id=current_user.id,
        provider_type_id=_resolve_provider_type_id(session=session, provider_type=provider_type),
    )

    # Enrich with provider info
    data = []
    for model in models:
        provider = model.provider
        data.append(
            LLMModelPublic(
                **model.model_dump(),
                provider_type=_get_provider_type_name(provider),
                provider_name=provider.name if provider else None,
            )
        )

    return LLMModelsPublic(data=data, count=len(data))


# =============================================================================
# Model Endpoints
# =============================================================================


@router.get("/models", response_model=LLMModelsPublic)
def list_models(
    session: SessionDep,
    current_user: OptionalUser,
    skip: int = 0,
    limit: int = 100,
    provider_id: uuid.UUID | None = Query(
        default=None, description="Filter by provider ID"
    ),
    provider_type: str | None = Query(
        default=None, description="Filter by provider type name"
    ),
    is_enabled: bool | None = Query(
        default=None, description="Filter by enabled status"
    ),
    is_deprecated: bool | None = Query(
        default=None, description="Filter by deprecation status"
    ),
    is_default: bool | None = Query(
        default=None, description="Filter by default model flag"
    ),
    has_vision: bool | None = Query(
        default=None, description="Filter by vision capability"
    ),
    has_function_calling: bool | None = Query(
        default=None, description="Filter by function calling"
    ),
    has_streaming: bool | None = Query(
        default=None, description="Filter by streaming support"
    ),
    has_json_mode: bool | None = Query(
        default=None, description="Filter by JSON mode support"
    ),
    include_deleted: bool = Query(
        default=False, description="Include soft-deleted models"
    ),
) -> Any:
    """
    List all LLM models in the catalog (flat list).

    Supports rich filtering by capabilities.
    If authenticated, includes the user's custom models alongside system models.
    """
    results, count = crud.get_llm_models(
        session=session,
        user_id=current_user.id if current_user else None,
        skip=skip,
        limit=limit,
        provider_id=provider_id,
        provider_type_id=_resolve_provider_type_id(session=session, provider_type=provider_type),
        is_enabled=is_enabled,
        is_deprecated=is_deprecated,
        is_default=is_default,
        has_vision=has_vision,
        has_function_calling=has_function_calling,
        has_streaming=has_streaming,
        has_json_mode=has_json_mode,
        include_deleted=include_deleted,
    )

    data = [
        LLMModelPublic(
            **model.model_dump(),
            provider_type=_get_provider_type_name(provider),
            provider_name=provider.name,
        )
        for model, provider in results
    ]

    return LLMModelsPublic(data=data, count=count)


@router.get("/models/grouped", response_model=LLMModelsGrouped)
def list_models_grouped(
    session: SessionDep,
    current_user: OptionalUser,
    provider_type: str | None = Query(
        default=None, description="Filter by provider type name"
    ),
    is_enabled: bool | None = Query(
        default=None, description="Filter by enabled status"
    ),
    include_deleted: bool = Query(default=False, description="Include soft-deleted"),
) -> Any:
    """
    List all models grouped by provider.

    Useful for UI dropdowns showing models organized by provider.
    If authenticated, includes the user's custom models alongside system models.
    """
    grouped = crud.get_llm_models_grouped(
        session=session,
        user_id=current_user.id if current_user else None,
        provider_type_id=_resolve_provider_type_id(session=session, provider_type=provider_type),
        is_enabled=is_enabled,
        include_deleted=include_deleted,
    )

    providers_with_models = []
    total_models = 0

    for provider, models in grouped:
        model_count = len(models)
        total_models += model_count

        model_public_list = [
            LLMModelPublic(
                **m.model_dump(),
                provider_type=_get_provider_type_name(provider),
                provider_name=provider.name,
            )
            for m in models
        ]

        providers_with_models.append(
            LLMProviderWithModels(
                **provider.model_dump(),
                model_count=model_count,
                models=model_public_list,
                provider_type=_get_provider_type_name(provider),
            )
        )

    return LLMModelsGrouped(
        providers=providers_with_models,
        total_models=total_models,
    )


@router.get("/models/{model_id}", response_model=LLMModelPublic)
def get_model(
    model_id: uuid.UUID,
    session: SessionDep,
    include_deleted: bool = Query(default=False, description="Include if soft-deleted"),
) -> Any:
    """
    Get a single LLM model by ID.

    No authentication required.
    """
    result = crud.get_llm_model(
        session=session,
        model_id=model_id,
        include_deleted=include_deleted,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Model not found")

    model, provider = result
    return LLMModelPublic(
        **model.model_dump(),
        provider_type=_get_provider_type_name(provider),
        provider_name=provider.name,
    )


def _resolve_provider_type_id(
    session: Session,
    provider_type: str | None,
) -> uuid.UUID | None:
    if not provider_type:
        return None
    type_obj = crud.get_llm_provider_type_by_name(session=session, name=provider_type)
    return type_obj.id if type_obj else None


def _get_provider_type_name(provider: LLMProvider | None) -> str | None:
    if not provider or not provider.provider_type:
        return None
    return provider.provider_type.name
