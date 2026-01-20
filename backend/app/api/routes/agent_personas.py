import uuid
from typing import Any

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.models import (
    AgentPersonaCreate,
    AgentPersonaPublic,
    AgentPersonasPublic,
    AgentPersonaUpdate,
    Message,
)

router = APIRouter(prefix="/agents/{agent_id}/personas", tags=["agent-personas"])


def _require_agent_view_access(
    *, session: SessionDep, current_user: CurrentUser, agent_id: uuid.UUID
) -> Any:
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    return config


def _require_agent_modify_access(
    *, session: SessionDep, current_user: CurrentUser, agent_id: uuid.UUID
) -> Any:
    config = _require_agent_view_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    if config.scope == "system" and not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="Only admins can modify system agents"
        )
    return config


@router.get("/", response_model=AgentPersonasPublic)
def read_agent_personas(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve agent personas for an agent configuration.
    """
    _require_agent_view_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    agent_personas, count = crud.get_agent_personas(
        session=session, agent_id=agent_id, skip=skip, limit=limit
    )
    return AgentPersonasPublic(data=agent_personas, count=count)


@router.get("/{id}", response_model=AgentPersonaPublic)
def read_agent_persona(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    id: uuid.UUID,
) -> Any:
    """
    Get agent persona by ID.
    """
    _require_agent_view_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    agent_persona = crud.get_agent_persona(session=session, id=id, agent_id=agent_id)
    if not agent_persona:
        raise HTTPException(status_code=404, detail="Agent persona not found")
    return agent_persona


@router.post("/", response_model=AgentPersonaPublic)
def create_agent_persona(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    agent_persona_in: AgentPersonaCreate,
) -> Any:
    """
    Create a new agent persona entry.
    """
    _require_agent_modify_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    try:
        return crud.create_agent_persona(
            session=session, agent_persona_in=agent_persona_in, agent_id=agent_id
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{id}", response_model=AgentPersonaPublic)
def update_agent_persona(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    id: uuid.UUID,
    agent_persona_in: AgentPersonaUpdate,
) -> Any:
    """
    Update an agent persona.
    """
    _require_agent_modify_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    agent_persona = crud.get_agent_persona(session=session, id=id, agent_id=agent_id)
    if not agent_persona:
        raise HTTPException(status_code=404, detail="Agent persona not found")

    return crud.update_agent_persona(
        session=session,
        db_agent_persona=agent_persona,
        agent_persona_in=agent_persona_in,
    )


@router.delete("/{id}")
def delete_agent_persona(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    id: uuid.UUID,
) -> Message:
    """
    Delete an agent persona.
    """
    _require_agent_modify_access(
        session=session, current_user=current_user, agent_id=agent_id
    )
    agent_persona = crud.get_agent_persona(session=session, id=id, agent_id=agent_id)
    if not agent_persona:
        raise HTTPException(status_code=404, detail="Agent persona not found")

    crud.delete_agent_persona(session=session, db_agent_persona=agent_persona)
    return Message(message="Agent persona deleted successfully")
