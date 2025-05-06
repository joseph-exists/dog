import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    UserPersona,
    UserPersonaCreate,
    UserPersonaPublic,
    UserPersonasPublic,
    UserPersonaUpdate,
    Message,
)

# TODO:

router = APIRouter(prefix="/user-personas", tags=["user-personas"])


@router.get("/", response_model=UserPersonasPublic)
def read_user_personas(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve user personas for the current user.
    """
    user_personas, count = crud.get_user_personas(
        session=session, user_id=current_user.id, skip=skip, limit=limit
    )
    return UserPersonasPublic(data=user_personas, count=count)


@router.get("/{id}", response_model=UserPersonaPublic)
def read_user_persona(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get user persona by ID.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")
    return user_persona


@router.post("/", response_model=UserPersonaPublic)
def create_user_persona(
    *, session: SessionDep, current_user: CurrentUser, user_persona_in: UserPersonaCreate
) -> Any:
    """
    Create new user persona.
    """
    user_persona = crud.create_user_persona(
        session=session, user_persona_in=user_persona_in, user_id=current_user.id
    )
    return user_persona


@router.put("/{id}", response_model=UserPersonaPublic)
def update_user_persona(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    user_persona_in: UserPersonaUpdate,
) -> Any:
    """
    Update a user persona.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    user_persona = crud.update_user_persona(
        session=session,
        db_user_persona=user_persona,
        user_persona_in=user_persona_in
    )
    return user_persona


@router.delete("/{id}")
def delete_user_persona(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete a user persona.
    """
    user_persona = crud.get_user_persona(
        session=session, id=id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    crud.delete_user_persona(session=session, db_user_persona=user_persona)
    return Message(message="User persona deleted successfully")
