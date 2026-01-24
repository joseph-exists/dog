import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Archetype,
    ArchetypeQualityLink,
    Message,
    Quality,
    QualityPublic,
)

router = APIRouter(
    prefix="/archetypes/{archetype_id}/qualities", tags=["archetype-qualities"]
)


@router.get("/", response_model=list[QualityPublic])
def read_archetype_qualities(
    session: SessionDep, current_user: CurrentUser, archetype_id: uuid.UUID
) -> Any:
    """
    Get all qualities for an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    statement = (
        select(Quality)
        .join(
            ArchetypeQualityLink,
            ArchetypeQualityLink.quality_id == Quality.id,
        )
        .where(ArchetypeQualityLink.archetype_id == archetype_id)
    )
    qualities = session.exec(statement).all()
    return qualities


@router.post("/{quality_id}", response_model=Message)
def add_quality_to_archetype(
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    quality_id: uuid.UUID,
) -> Any:
    """
    Add a quality to an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    quality = session.get(Quality, quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality not found")

    # Check if link already exists
    existing = session.exec(
        select(ArchetypeQualityLink).where(
            ArchetypeQualityLink.archetype_id == archetype_id,
            ArchetypeQualityLink.quality_id == quality_id,
        )
    ).first()
    if existing:
        return Message(message="Quality already linked to archetype")

    link = ArchetypeQualityLink(archetype_id=archetype_id, quality_id=quality_id)
    session.add(link)
    session.commit()
    return Message(message="Quality added to archetype successfully")


@router.delete("/{quality_id}", response_model=Message)
def remove_quality_from_archetype(
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    quality_id: uuid.UUID,
) -> Any:
    """
    Remove a quality from an archetype.
    """
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    link = session.exec(
        select(ArchetypeQualityLink).where(
            ArchetypeQualityLink.archetype_id == archetype_id,
            ArchetypeQualityLink.quality_id == quality_id,
        )
    ).first()
    if not link:
        raise HTTPException(
            status_code=404, detail="Quality not linked to archetype"
        )

    session.delete(link)
    session.commit()
    return Message(message="Quality removed from archetype successfully")
