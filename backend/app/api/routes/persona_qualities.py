import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    PersonaQualityLink,
    Persona,
    Quality,
    Message,
    QualityPublic,
)
from app import crud

router = APIRouter(prefix="/personas/{persona_id}/qualities", tags=["persona-qualities"])


@router.get("/", response_model=list[QualityPublic])
def read_persona_qualities(
    session: SessionDep, current_user: CurrentUser, persona_id: uuid.UUID
) -> Any:
    """
    Get all qualities for a persona.
    """
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Get all enabled qualities
    statement = select(Quality).join(PersonaQualityLink).where(
        PersonaQualityLink.persona_id == persona_id,
        PersonaQualityLink.state == "enabled"
    )
    qualities = session.exec(statement).all()
    return qualities


@router.post("/{quality_id}", response_model=Message)
def add_quality_to_persona(
    session: SessionDep,
    current_user: CurrentUser,
    persona_id: uuid.UUID,
    quality_id: uuid.UUID
) -> Any:
    """
    Add a quality to a persona.
    """
    # Verify the persona exists
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    # Verify the quality exists
    quality = session.get(Quality, quality_id)
    if not quality:
        raise HTTPException(status_code=404, detail="Quality not found")

    try:
        crud.add_quality_to_persona(
            session=session,
            persona_id=persona_id,
            quality_id=quality_id
        )
        return Message(message="Quality added to persona successfully")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{quality_id}", response_model=Message)
def remove_quality_from_persona(
    session: SessionDep,
    current_user: CurrentUser,
    persona_id: uuid.UUID,
    quality_id: uuid.UUID
) -> Any:
    """
    Remove a quality from a persona.
    """
    # Verify the persona exists
    persona = session.get(Persona, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")

    try:
        crud.remove_quality_from_persona(
            session=session,
            persona_id=persona_id,
            quality_id=quality_id
        )
        return Message(message="Quality removed from persona successfully")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
