import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.services.shadow_exporters import build_persona_snapshot
from app.services.shadow_service import shadow_service
from app.models import (
    Archetype,
    Persona,
    PersonaCreate,
    PersonaVisibility,
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
    visibility_filter = (
        (Persona.visibility == PersonaVisibility.SYSTEM)
        | (
            (Persona.visibility == PersonaVisibility.PRIVATE)
            & (Persona.owner_user_id == current_user.id)
        )
    )
    count_statement = select(func.count()).select_from(Persona).where(visibility_filter)
    count = session.exec(count_statement).one()
    statement = select(Persona).where(visibility_filter).offset(skip).limit(limit)
    personas = session.exec(statement).all()

    return PersonasPublic(data=personas, count=count)  # type:ignore


@router.get("/{id}", response_model=Persona)
def read_persona(session: SessionDep, current_user: CurrentUser, id: uuid.UUID) -> Any:
    """
    Get persona by ID.
    """
    persona = session.get(Persona, id)
    if not persona:
        raise HTTPException(status_code=404, detail="persona not found")
    if not current_user.is_superuser:
        if persona.visibility == PersonaVisibility.SYSTEM:
            return persona
        if (
            persona.visibility == PersonaVisibility.PRIVATE
            and persona.owner_user_id == current_user.id
        ):
            return persona
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return persona


@router.post("/", response_model=PersonaPublic)
def create_persona(
    *, session: SessionDep, current_user: CurrentUser, persona_in: PersonaCreate
) -> Any:
    """
    Create new persona.
    """
    if persona_in.visibility == PersonaVisibility.SYSTEM and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can create system personas")

    owner_user_id = (
        None
        if persona_in.visibility == PersonaVisibility.SYSTEM
        else current_user.id
    )

    persona = Persona.model_validate(
        persona_in,
        update={"owner_user_id": owner_user_id},
    )

    session.add(persona)
    session.commit()
    session.refresh(persona)
    try:
        snapshot = build_persona_snapshot(session=session, persona_id=persona.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="persona",
            entity_id=persona.id,
            entity_data=snapshot,
            message=f"Create persona: {persona.name}",
        )
    except Exception:
        pass
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
    if persona.visibility == PersonaVisibility.SYSTEM:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    elif persona.owner_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    update_dict = persona_in.model_dump(exclude_unset=True)
    if "visibility" in update_dict and update_dict["visibility"] != persona.visibility:
        raise HTTPException(
            status_code=400,
            detail="Persona visibility migration is not supported in MVP",
        )
    update_dict.pop("owner_user_id", None)
    persona.sqlmodel_update(update_dict)
    session.add(persona)
    session.commit()
    session.refresh(persona)
    try:
        snapshot = build_persona_snapshot(session=session, persona_id=persona.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="persona",
            entity_id=persona.id,
            entity_data=snapshot,
            message=f"Update persona: {persona.name}",
        )
    except Exception:
        pass
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
    if persona.visibility == PersonaVisibility.SYSTEM:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    elif persona.owner_user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    try:
        snapshot = build_persona_snapshot(session=session, persona_id=persona.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="persona",
            entity_id=persona.id,
            entity_data=snapshot,
            message=f"Delete persona: {persona.name}",
        )
    except Exception:
        pass
    session.delete(persona)
    session.commit()
    return Message(message="Persona deleted successfully")


@router.post("/from-archetype/{archetype_id}", response_model=PersonaPublic)
def create_persona_from_archetype(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    archetype_id: uuid.UUID,
    persona_in: PersonaCreate,
) -> Any:
    """
    Create a new persona based on an archetype.
    This will inherit traits and qualities from the archetype.
    """
    # Verify the archetype exists
    archetype = session.get(Archetype, archetype_id)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")

    if persona_in.visibility == PersonaVisibility.SYSTEM and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only superusers can create system personas")

    try:
        persona = crud.create_persona_with_archetype(
            session=session,
            persona_in=persona_in,
            archetype_id=archetype_id,
            owner_user_id=(
                None
                if persona_in.visibility == PersonaVisibility.SYSTEM
                else current_user.id
            ),
        )
        try:
            snapshot = build_persona_snapshot(session=session, persona_id=persona.id)
            shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="persona",
                entity_id=persona.id,
                entity_data=snapshot,
                message=f"Create persona from archetype: {persona.name}",
            )
        except Exception:
            pass
        return persona
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
