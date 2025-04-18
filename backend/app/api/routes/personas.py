import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Persona,
    PersonaCreate,
    PersonaPublic,
    PersonasPublic,
    PersonaUpdate,
    Message,
)

router = APIRouter(prefix="/personas", tags=["personas"])


@router.get("/", response_model=PersonasPublic)
def read_personas(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve personas.
    """

    count_statement = select(func.count()).select_from(Persona)
    count = session.exec(count_statement).one()
    statement = select(Persona).offset(skip).limit(limit)
    personas = session.exec(statement).all()

    return PersonasPublic(data=personas, count=count)


@router.get("/{id}", response_model=Persona)
def read_persona(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get persona by ID.
    """
    persona = session.get(Persona, id)
    if not persona:
        raise HTTPException(status_code=404, detail="persona not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    return persona


@router.post("/", response_model=PersonaPublic)
def create_persona(
    *, session: SessionDep, current_user: CurrentUser, persona_in: PersonaCreate
) -> Any:
    """
    Create new persona.
    """
    persona = Persona.model_validate(persona_in, update={"enabled": True})
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona


@router.put("/{id}", response_model=PersonaPublic)
def update_persona(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    persona_in: PersonaUpdate,
) -> Any:
    """
    Update a persona.
    """
    persona = session.get(Persona, id)
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = persona_in.model_dump(exclude_unset=True)
    persona.sqlmodel_update(update_dict)
    session.add(persona)
    session.commit()
    session.refresh(persona)
    return persona


@router.delete("/{id}")
def delete_persona(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a persona.
    """
    persona = session.get(Persona, id)
    if not persona:
        raise HTTPException(status_code=404, detail="persona not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(persona)
    session.commit()
    return Message(message="Persona deleted successfully")
