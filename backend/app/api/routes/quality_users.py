import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Archetype,
    ArchetypePublic,
    ArchetypeQualityLink,
    Persona,
    PersonaPublic,
    PersonaQualityLink,
    Quality,
)

router = APIRouter(prefix="/qualities/{quality_id}", tags=["quality-users"])


@router.get("/archetypes", response_model=list[ArchetypePublic])
def read_quality_archetypes(
    session: SessionDep, current_user: CurrentUser, quality_id: uuid.UUID
) -> Any:
    """
    Get all archetypes that use a given quality.
    """
    quality = session.get(Quality, quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality not found")

    statement = (
        select(Archetype)
        .join(
            ArchetypeQualityLink,
            ArchetypeQualityLink.archetype_id == Archetype.id,
        )
        .where(ArchetypeQualityLink.quality_id == quality_id)
    )
    archetypes = session.exec(statement).all()
    return archetypes


@router.get("/personas", response_model=list[PersonaPublic])
def read_quality_personas(
    session: SessionDep, current_user: CurrentUser, quality_id: uuid.UUID
) -> Any:
    """
    Get all personas that have a given quality.
    """
    quality = session.get(Quality, quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality not found")

    statement = (
        select(Persona)
        .join(PersonaQualityLink, PersonaQualityLink.persona_id == Persona.id)
        .where(PersonaQualityLink.quality_id == quality_id)
    )
    personas = session.exec(statement).all()
    return personas
