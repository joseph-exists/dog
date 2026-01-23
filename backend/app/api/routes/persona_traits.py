import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Persona,
    PersonaTraitLink,
    Trait,
    TraitPublic,
)

router = APIRouter(prefix="/personas/{persona_id}/traits", tags=["persona-traits"])


@router.get("/", response_model=list[TraitPublic])
def read_persona_traits(
    session: SessionDep, current_user: CurrentUser, persona_id: uuid.UUID
) -> Any:
    """
    Get all traits for a persona.
    """
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    statement = (
        select(Trait)
        .join(PersonaTraitLink, PersonaTraitLink.trait_id == Trait.id)
        .where(PersonaTraitLink.persona_id == persona_id)
    )
    traits = session.exec(statement).all()
    return traits
