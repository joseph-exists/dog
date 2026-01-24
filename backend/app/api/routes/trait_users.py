import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Archetype,
    ArchetypePublic,
    ArchetypeTraitLink,
    Persona,
    PersonaPublic,
    PersonaTraitLink,
    Trait,
)

router = APIRouter(prefix="/traits/{trait_id}", tags=["trait-users"])


@router.get("/archetypes", response_model=list[ArchetypePublic])
def read_trait_archetypes(
    session: SessionDep, current_user: CurrentUser, trait_id: uuid.UUID
) -> Any:
    """
    Get all archetypes that use a given trait.
    """
    trait = session.get(Trait, trait_id)
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")

    statement = (
        select(Archetype)
        .join(ArchetypeTraitLink, ArchetypeTraitLink.archetype_id == Archetype.id)
        .where(ArchetypeTraitLink.trait_id == trait_id)
    )
    archetypes = session.exec(statement).all()
    return archetypes


@router.get("/personas", response_model=list[PersonaPublic])
def read_trait_personas(
    session: SessionDep, current_user: CurrentUser, trait_id: uuid.UUID
) -> Any:
    """
    Get all personas that have a given trait (directly or inherited).
    """
    trait = session.get(Trait, trait_id)
    if not trait:
        raise HTTPException(status_code=404, detail="Trait not found")

    statement = (
        select(Persona)
        .join(PersonaTraitLink, PersonaTraitLink.persona_id == Persona.id)
        .where(PersonaTraitLink.trait_id == trait_id)
    )
    personas = session.exec(statement).all()
    return personas
