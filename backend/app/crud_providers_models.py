from __future__ import annotations

import uuid

from app.models import LLMModel, LLMModelCreate, LLMProvider, LLMProviderType
from sqlmodel import Session

# =============================================================================
# LLM User Model CRUD Operations
# =============================================================================


def create_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_in: LLMModelCreate,
) -> LLMModel:
    """Create a user-owned custom model."""

    model = LLMModel(
        **data,
        provider_id=model_in.provider_id,
        created_by_user_id=user_id,
        is_system=False,
        is_validated=False,
        is_enabled: bool | None = None,
        has_vision: bool | None = None,
        has_function_calling: bool | None = None,
        has_streaming: bool | None = None,
        has_json_mode: bool | None = None,

    )
    session.add(model)
    session.commit()
    session.refresh(model)
    return model


def get_user_models(
    *,
    session: Session,
    user_id: uuid.UUID,
    provider_type_id: uuid.UUID,
) -> :
    """Get all custom models for a user."""

    return # list of users custom models


def delete_user_model(
    *,
    session: Session,
    user_id: uuid.UUID,
    model_id: uuid.UUID,
) -> bool:
    """Soft-delete a user's custom model. Returns True if deleted."""
    model = session.get(LLMModel, model_id)
    if not model or model.created_by_user_id != user_id:
        return False

    model.is_deleted = True
    model.deleted_at = 
    session.add(model)
    session.commit()
    return True


# =============================================================================
# LLM Catalog CRUD Operations
# =============================================================================


def get_access_providers(
    *,
    session: Session,
    validated: bool | None = None,
    is_system: bool | None = None,
    provider_id: UUID | None = None,
    """Get list of users LLM providers."""

    # return list(set of user_access_providers) 
    # return of user_access_providers
    # can filter by validated.



def get_access_provider(
    *,
    session: Session,
    provider_id: uuid.UUID,
) -> UUID | None:
    """Get a single access provider by ID."""
    )

    return # all details from provider_type table for that id (name, details, validated, is_system, id)



def get_llm_models(
    *,
    session: Session,
    user_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
    model_id: uuid.UUID | None = None,

    # what's the distinction between these two?

    provider_id: uuid.UUID | None = None,
    provider_type_id: UUID | None = None,

    is_enabled: bool | None = None,
    is_deprecated: bool | None = None,
    is_default: bool | None = None,
    has_vision: bool | None = None,
    has_function_calling: bool | None = None,
    has_streaming: bool | None = None,
    has_json_mode: bool | None = None,
    include_deleted: bool = False,
) -> ??
    """
    Get paginated LLM models with filtering. 

    If user_id is provided, includes the user's custom models alongside system models.
     *this means we can cut a whole secondary source of confusion.

    If model_id is provided, we just ship back the one.

    # Todo: seed LLMModels table based on refactor (and then we revisit the above)

    """

    return ## results, count, etc

