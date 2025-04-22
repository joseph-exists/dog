import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    QualityTraitLink,
    QualityTraitLinkCreate,
    QualityTraitLinkPublic,
    QualityTraitLinkUpdate,
    Message,
    Trait,
    Quality,
)
from app import crud

router = APIRouter(prefix="/quality-trait-links", tags=["quality-trait-links"])


@router.get("/{quality_id}/traits", response_model=list[QualityTraitLinkPublic])
def read_quality_traits(
    session: SessionDep, current_user: CurrentUser, quality_id: uuid.UUID
) -> Any:
    """
    Get all traits linked to a quality.
    """
    statement = select(QualityTraitLink).where(QualityTraitLink.quality_id == quality_id)
    links = session.exec(statement).all()
    return links


@router.get("/{trait_id}/qualities", response_model=list[QualityTraitLinkPublic])
def read_trait_qualities(
    session: SessionDep, current_user: CurrentUser, trait_id: uuid.UUID
) -> Any:
    """
    Get all qualities linked to a trait.
    """
    statement = select(QualityTraitLink).where(QualityTraitLink.trait_id == trait_id)
    links = session.exec(statement).all()
    return links


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
        return existing_link

    link = crud.create_quality_trait_link(session=session, link_in=link_in)
    return link


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
    session.delete(link)
    session.commit()
    return Message(message="Quality-Trait link deleted successfully")
