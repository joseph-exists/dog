from fastapi import APIRouter, HTTPException, Depends, Request
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser

from app.models import (
    AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigPublic, AgentConfigsPublic,
    Message,
)

from typing import Any
import uuid
import logging

from app.services.agent_registry_service import agent_registry_service
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)

from app import crud

from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.responses import Response

from app.agents.quixote import agent

router = APIRouter(prefix="/agents", tags=["agents"])

# ============================================================================
# Available Agents Registry (Task 5)
# ============================================================================
# This is the single source of truth for available agents.
# Previously hardcoded in frontend as AVAILABLE_AGENTS array.


@router.get("/", response_model=AgentConfigsPublic)
def list_agents(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    scope: str | None = None,
) -> Any:
    """List agent configurations.

    Users see: system agents + their own personal agents
    Admins see: all agents
    """
    if current_user.is_superuser:
        configs, count = crud.get_agent_configs(session=session, skip=skip, limit=limit, scope=scope)
    else:
        # Get system agents + user's personal agents
        system_configs, _ = crud.get_agent_configs(
            session=session, scope="system", enabled_only=True
        )
        personal_configs, _ = crud.get_agent_configs(
            session=session, scope="personal", owner_id=current_user.id
        )
        configs = system_configs + personal_configs
        count = len(configs)

    return AgentConfigsPublic(data=configs, count=count)


@router.get("/available", response_model=AgentConfigsPublic)
def list_available_agents(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    scope: str | None = None,
) -> Any:
    """List agents available for room participation (enabled system agents and enabled personal agents)."""
    if current_user.is_superuser:
        configs, count = crud.get_agent_configs(
            session=session, skip=skip, limit=limit, scope=scope
        )
    else:
        # Get system agents + user's personal agents
        system_configs, _ = crud.get_agent_configs(
            session=session, scope="system", enabled_only=True
        )
        personal_configs, _ = crud.get_agent_configs(
            session=session, scope="personal", owner_id=current_user.id
        )
        configs = system_configs + personal_configs
        count = len(configs)
    return AgentConfigsPublic(data=configs, count=count)


@router.get("/{agent_id}", response_model=AgentConfigPublic)
def get_agent(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Any:
    """Get agent configuration by ID."""
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check access: system agents visible to all, personal only to owner/admin
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    return config


@router.post("/", response_model=AgentConfigPublic)
def create_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_in: AgentConfigCreate,
) -> Any:
    """Create a new agent configuration.

    - Users can create personal agents (scope="personal")
    - Only admins can create system agents (scope="system")
    """
    if agent_in.scope == "system" and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can create system agents"
        )

    # Force personal scope for non-admins
    if not current_user.is_superuser:
        agent_in.scope = "personal"

    try:
        config = agent_registry_service.register_agent(
            session=session,
            agent_in=agent_in,
            owner_id=current_user.id if agent_in.scope == "personal" else None,
        )

        # Shadow versioning (non-blocking - skips if user not set up)
        try:
            version = shadow_service.create_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=config.id,
                entity_data=config.model_dump(mode="json"),
                message=f"Create agent: {config.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} created for agent {config.slug}")
        except Exception as e:
            logger.warning(f"Shadow versioning failed for agent {config.slug}: {e}")

        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{agent_id}", response_model=AgentConfigPublic)
def update_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    agent_in: AgentConfigUpdate,
) -> Any:
    """Update an agent configuration."""
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permissions
    if config.scope == "system" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can modify system agents")
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    updated = agent_registry_service.update_agent(
        session=session,
        slug=config.slug,
        agent_in=agent_in,
    )

    # Shadow versioning (non-blocking - skips if user not set up)
    if updated:
        try:
            version = shadow_service.create_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=updated.id,
                entity_data=updated.model_dump(mode="json"),
                message=f"Update agent: {updated.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} created for agent {updated.slug}")
        except Exception as e:
            logger.warning(f"Shadow versioning failed for agent {updated.slug}: {e}")

    return updated


@router.delete("/{agent_id}")
def delete_agent(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Message:
    """Delete an agent configuration."""
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permissions
    if config.scope == "system" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can delete system agents")
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    crud.delete_agent_config(session=session, db_agent=config)
    return Message(message="Agent deleted successfully")


@router.post("/pydantic-agent")
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)
