import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Archetype,
    ArchetypeCreate,
    ArchetypePublic,
    ArchetypesPublic,
    ArchetypeUpdate,
    Message,
)

router = APIRouter(prefix="/archetypes", tags=["archetypes"])


@router.get("/", response_model=ArchetypesPublic)
def read_archetypes(
    session: SessionDep, current_user: CurrentUser, skip: int = 0, limit: int = 100
) -> Any:
    """
    Retrieve archetypes.
    """

    count_statement = select(func.count()).select_from(Archetype)
    count = session.exec(count_statement).one()
    statement = select(Archetype).offset(skip).limit(limit)
    archetypes = session.exec(statement).all()

    return ArchetypesPublic(data=archetypes, count=count)


@router.get("/{id}", response_model=ArchetypePublic)
def read_archetype(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Any:
    """
    Get archetype by ID.
    """
    archetype = session.get(Archetype, id)
    if not archetype:
        raise HTTPException(status_code=404, detail="archetype not found")
    return archetype


@router.post("/", response_model=ArchetypePublic)
def create_archetype(
    *, session: SessionDep, current_user: CurrentUser, archetype_in: ArchetypeCreate
) -> Any:
    """
    Create new archetype.
    """
    archetype = Archetype.model_validate(archetype_in, update={"enabled": True})
    session.add(archetype)
    session.commit()
    session.refresh(archetype)
    return archetype


@router.put("/{id}", response_model=ArchetypePublic)
def update_archetype(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    id: uuid.UUID,
    archetype_in: ArchetypeUpdate,
) -> Any:
    """
    Update an archetype.
    """
    archetype = session.get(Archetype, id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    update_dict = archetype_in.model_dump(exclude_unset=True)
    archetype.sqlmodel_update(update_dict)
    session.add(archetype)
    session.commit()
    session.refresh(archetype)
    return archetype


@router.delete("/{id}")
def delete_archetype(
    session: SessionDep, current_user: CurrentUser, id: uuid.UUID
) -> Message:
    """
    Delete an archetype.
    """
    archetype = session.get(Archetype, id)
    if not archetype:
        raise HTTPException(status_code=404, detail="archetype not found")
    if not current_user.is_superuser:
        raise HTTPException(status_code=400, detail="Not enough permissions")
    session.delete(archetype)
    session.commit()
    return Message(message="Archetype deleted successfully")
