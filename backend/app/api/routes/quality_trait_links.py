import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.services.shadow_exporters import build_quality_snapshot, build_trait_snapshot
from app.services.shadow_service import shadow_service
from app.models import (
    QualitiesPublic,
    QualityPublic,
    QualityTraitLink,
    QualityTraitLinkCreate,
    QualityTraitLinkPublic,
    QualityTraitLinkUpdate,
    Message,
    Trait,
    TraitPublic,
    Quality,
)
from app import crud

router = APIRouter(prefix="/quality-trait-links", tags=["quality-trait-links"])


@router.get("/{quality_id}/traits", response_model=list[TraitPublic])
def read_quality_traits(
    session: SessionDep, current_user: CurrentUser, quality_id: uuid.UUID
) -> Any:
    """
    Get all traits linked to a quality.
    """
    # verify that quality exists
    quality = session.get(Quality, quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="This not quality, Grug. Be shame.")

    # Get all qualities for this trait
    statement = (
        select(Trait)
        .join(QualityTraitLink)
        .where(QualityTraitLink.quality_id == quality_id)
    )
    traits = session.exec(statement).all()

    return traits


@router.get("/{trait_id}/qualities", response_model=list[QualityPublic])
def read_trait_qualities(
    session: SessionDep, current_user: CurrentUser, trait_id: uuid.UUID
) -> Any:
    """
    Get all qualities linked to a trait.
    """
    # Verify the trait exists
    trait = session.get(Trait, trait_id)
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")

    # Get all qualities for this trait
    statement = (
        select(Quality)
        .join(QualityTraitLink)
        .where(QualityTraitLink.trait_id == trait_id)
    )
    qualities = session.exec(statement).all()

    return qualities



@router.post("/", response_model=QualityTraitLinkPublic)
def create_quality_trait_link(
    *, session: SessionDep, current_user: CurrentUser, link_in: QualityTraitLinkCreate
) -> Any:
    """
    Create new quality-trait link.
    """
    # Verify the quality exists
    quality = session.get(Quality, link_in.quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality not found")

    # Verify the trait exists
    trait = session.get(Trait, link_in.trait_id)
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")

    # Check if this link already exists
    statement = select(QualityTraitLink).where(
        QualityTraitLink.quality_id == link_in.quality_id,
        QualityTraitLink.trait_id == link_in.trait_id
    )
    existing_link = session.exec(statement).first()
    if existing_link:
        # Convert to a dict and add the trait and quality objects
        link_data = existing_link.model_dump()
        link_data["trait"] = trait
        link_data["quality"] = quality
        # Create a new public model with all the data
        return QualityTraitLinkPublic.model_validate(link_data)

    # Create new link
    link = QualityTraitLink.model_validate(link_in)
    session.add(link)
    session.commit()
    session.refresh(link)
    try:
        quality_snapshot = build_quality_snapshot(session=session, quality_id=quality.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="quality",
            entity_id=quality.id,
            entity_data=quality_snapshot,
            message=f"Quality-trait link created: {quality.id} -> {trait.id}",
        )
        trait_snapshot = build_trait_snapshot(session=session, trait_id=trait.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="trait",
            entity_id=trait.id,
            entity_data=trait_snapshot,
            message=f"Quality-trait link created: {quality.id} -> {trait.id}",
        )
    except Exception:
        pass

    # Convert to a dict and add the trait and quality objects
    link_data = link.model_dump()
    link_data["trait"] = trait
    link_data["quality"] = quality
    # Create a new public model with all the data
    return QualityTraitLinkPublic.model_validate(link_data)


@router.delete("/{quality_id}/{trait_id}")
def delete_quality_trait_link(
    session: SessionDep,
    current_user: CurrentUser,
    quality_id: uuid.UUID,
    trait_id: uuid.UUID
) -> Message:
    """
    Delete a quality-trait link.
    """
    statement = select(QualityTraitLink).where(
        QualityTraitLink.quality_id == quality_id,
        QualityTraitLink.trait_id == trait_id
    )
    link = session.exec(statement).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    try:
        quality_snapshot = build_quality_snapshot(session=session, quality_id=quality_id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="quality",
            entity_id=quality_id,
            entity_data=quality_snapshot,
            message=f"Quality-trait link deleted: {quality_id} -> {trait_id}",
        )
        trait_snapshot = build_trait_snapshot(session=session, trait_id=trait_id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="trait",
            entity_id=trait_id,
            entity_data=trait_snapshot,
            message=f"Quality-trait link deleted: {quality_id} -> {trait_id}",
        )
    except Exception:
        pass
    session.delete(link)
    session.commit()
    return Message(message="Quality-Trait link deleted successfully")
