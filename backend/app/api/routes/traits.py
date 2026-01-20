import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.services.shadow_exporters import build_trait_snapshot
from app.services.shadow_service import shadow_service
from app.models import (
    Trait,
    TraitCreate,
    TraitPublic,
    TraitsPublic,
    TraitUpdate,
    Message,
)

router = APIRouter(prefix="/traits", tags=["traits"])


@router.get("/", response_model=TraitsPublic)
def read_traits(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve traits.
    """

    count_statement = select(func.count()).select_from(Trait)
    count = session.exec(count_statement).one()
    statement = select(Trait).offset(skip).limit(limit)
    traits = session.exec(statement).all()

    return TraitsPublic(data=traits, count=count)  # type: ignore


@router.get("/{id}", response_model=TraitPublic)
def read_trait(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get Trait by ID.
    """
    trait = session.get(Trait, id)
    if not trait:
        raise HTTPException(status_code=404, detail="trait not found")
    return trait


@router.post("/", response_model=TraitPublic)
def create_trait(
    *, session: SessionDep, current_user: CurrentUser, trait_in: TraitCreate
) -> Any:
    """
    Create new trait.
    """
    # Generate trait_name from name
    trait_name = trait_in.name.lower().replace(" ", "_")[:50]

    trait = Trait.model_validate(
        trait_in, update={"enabled": True, "trait_name": trait_name}
    )
    session.add(trait)
    session.commit()
    session.refresh(trait)
    try:
        snapshot = build_trait_snapshot(session=session, trait_id=trait.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="trait",
            entity_id=trait.id,
            entity_data=snapshot,
            message=f"Create trait: {trait.name}",
        )
    except Exception:
        pass
    return trait


@router.put("/{id}", response_model=TraitPublic)
def update_trait(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    trait_in: TraitUpdate,
) -> Any:
    """
    Update an trait.
    """
    trait = session.get(Trait, id)
    if not trait:
        raise HTTPException(status_code=404, detail="trait not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = trait_in.model_dump(exclude_unset=True)
    trait.sqlmodel_update(update_dict)
    session.add(trait)
    session.commit()
    session.refresh(trait)
    try:
        snapshot = build_trait_snapshot(session=session, trait_id=trait.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="trait",
            entity_id=trait.id,
            entity_data=snapshot,
            message=f"Update trait: {trait.name}",
        )
    except Exception:
        pass
    return trait


@router.delete("/{id}")
def delete_trait(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an trait.
    """
    trait = session.get(Trait, id)
    if not trait:
        raise HTTPException(status_code=404, detail="trait not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    try:
        snapshot = build_trait_snapshot(session=session, trait_id=trait.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="trait",
            entity_id=trait.id,
            entity_data=snapshot,
            message=f"Delete trait: {trait.name}",
        )
    except Exception:
        pass
    session.delete(trait)
    session.commit()
    return Message(message="Trait deleted successfully")
