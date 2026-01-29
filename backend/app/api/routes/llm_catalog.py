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
    LLMModelsPublic,
    UserAccessProvider,
    UserAccessProviderPublic,
    UserAccessProvidersPublic,
)

router = APIRouter(prefix="/llm-catalog", tags=["llm-catalog"])


# =============================================================================
# Helper Functions
# =============================================================================


def _resolve_provider_type_id(*, session: SessionDep, provider_type: str | None) -> uuid.UUID | None:
    """Resolve provider type name to UUID."""
    if not provider_type:
        return None

    from app.models import LLMProviderType
    from sqlmodel import select

    statement = select(LLMProviderType).where(LLMProviderType.name == provider_type)
    result = session.exec(statement).first()
    return result.id if result else None


def _get_provider_type_name(provider: Any) -> str | None:
    """Get provider type name from a UserAccessProvider instance."""
    if not provider:
        return None

    # If provider has a provider_type_id, fetch the LLMProviderType name
    if hasattr(provider, 'provider_type_id') and provider.provider_type_id:
        from app.models import LLMProviderType
        from sqlmodel import Session

        # We need a session here - for now return None, will fix with proper join
        # TODO: This should be done with a proper join in the CRUD layer
        return None

    return None


# =============================================================================
# Provider Endpoints
# =============================================================================


# TODO: This endpoint needs to be authenticated and scoped to current user
# @router.get("/providers", response_model=UserAccessProvidersPublic)
# def list_providers(
#     session: SessionDep,
#     current_user: CurrentUser,  # Should require auth
#     skip: int = 0,
#     limit: int = 100,
#     is_enabled: bool | None = Query(
#         default=None, description="Filter by enabled status"
#     ),
#     is_validated: bool | None = Query(
#         default=None, description="Filter by validated status"
#     ),
# ) -> Any:
#     """
#     List current user's access providers.
#     Each provider represents an API endpoint + key combo.
#     """
#     providers, count = crud.get_access_providers(
#         session=session,
#         user_id=current_user.id,
#         skip=skip,
#         limit=limit,
#         is_enabled=is_enabled,
#         is_validated=is_validated,
#     )
#
#     return UserAccessProvidersPublic(data=[
#         UserAccessProviderPublic(**p.model_dump())
#         for p in providers
#     ], count=count)


@router.get("/providers/{provider_id}", response_model=UserAccessProviderPublic)
def get_provider(
    provider_id: uuid.UUID,
    session: SessionDep,
    include_deleted: bool = Query(default=False, description="Include if soft-deleted"),
) -> Any:
    """
    Get a single user access provider by ID.

    No authentication required.
    """
    provider = crud.get_access_provider(
        session=session,
        provider_id=provider_id,
    )
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # TODO: Implement model_count CRUD function
    model_count = 0

    return UserAccessProviderPublic(
        **provider.model_dump(),
        model_count=model_count,
        provider_type=_get_provider_type_name(provider) if hasattr(provider, 'provider_type_id') else None,
    )


# TODO: Implement after LLM model CRUD functions exist
# @router.get("/providers/{provider_id}/models", response_model=LLMModelsPublic)
# def list_provider_models(
#     provider_id: uuid.UUID,
#     session: SessionDep,
#     current_user: CurrentUser,
#     skip: int = 0,
#     limit: int = 100,
# ) -> Any:
#     """List all models for a specific user's provider."""
#     provider = crud.get_access_provider(
#         session=session,
#         provider_id=provider_id,
#         user_id=current_user.id,
#     )
#     if not provider:
#         raise HTTPException(status_code=404, detail="Provider not found")
#
#     # TODO: Implement crud.get_llm_models()
#     return LLMModelsPublic(data=[], count=0)


# =============================================================================
# Custom Model Endpoints (Authenticated)
# =============================================================================

# TODO: Implement after LLM model CRUD functions exist
# @router.post("/models/custom", response_model=LLMModelPublic)
# def create_custom_model(
#     session: SessionDep,
#     current_user: CurrentUser,
#     model_in: LLMModelCreate,
# ) -> Any:
#     """Create a custom model for the current user."""
#     pass

# TODO: Implement after LLM model CRUD functions exist
# @router.get("/models/custom", response_model=LLMModelsPublic)
# def list_custom_models(
#     session: SessionDep,
#     current_user: CurrentUser,
# ) -> Any:
#     """List the current user's custom models."""
#     pass


# =============================================================================
# Model Endpoints
# =============================================================================


# TODO: Implement after LLM model CRUD functions exist
# @router.get("/models", response_model=LLMModelsPublic)
# def list_models(
#     session: SessionDep,
#     current_user: OptionalUser,
#     skip: int = 0,
#     limit: int = 100,
# ) -> Any:
#     """List all LLM models available to current user."""
#     # TODO: Implement crud.get_llm_models()
#     return LLMModelsPublic(data=[], count=0)


# @router.get("/models/grouped", response_model=LLMModelsGrouped)
# def list_models_grouped(
#     session: SessionDep,
#     current_user: OptionalUser,
#     provider_type: str | None = Query(
#         default=None, description="Filter by provider type name"
#     ),
#     is_enabled: bool | None = Query(
#         default=None, description="Filter by enabled status"
#     ),
#     include_deleted: bool = Query(default=False, description="Include soft-deleted"),
# ) -> Any:
#     """
#     List all models grouped by provider.
#
#     TODO: Implement if needed - can be done client-side by grouping flat list
#     Useful for UI dropdowns showing models organized by provider.
#     If authenticated, includes the user's custom models alongside system models.
#     """
#     pass


# TODO: Implement after LLM model CRUD functions exist
# @router.get("/models/{model_id}", response_model=LLMModelPublic)
# def get_model(
#     model_id: uuid.UUID,
#     session: SessionDep,
# ) -> Any:
#     """Get a single LLM model by ID."""
#     # TODO: Implement crud.get_llm_model()
#     raise HTTPException(status_code=404, detail="Model not found")
