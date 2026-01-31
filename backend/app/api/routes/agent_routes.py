import logging
import uuid
from typing import Any

from coolname import generate_slug as coolname_generate_slug
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    UserAgentConfig,
    UserAgentConfigCreate,
    UserAgentConfigPublic,
    UserAgentConfigsPublic,
    UserAgentConfigUpdate,
)
from app.services.shadow_exporters import build_agent_snapshot
from app.services.shadow_service import shadow_service

logger = logging.getLogger(__name__)

from pydantic_ai.ui.ag_ui import AGUIAdapter

from app import crud

router = APIRouter(prefix="/agents", tags=["agents"])


class GeneratedSlugResponse(BaseModel):
    slug: str

# ============================================================================
# Available Agents Registry (Task 5)
# ============================================================================
# This is the single source of truth for available agents.
# Previously hardcoded in frontend as AVAILABLE_AGENTS array.


@router.get("/", response_model=UserAgentConfigsPublic)
def list_agents(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    scope: str | None = None,
) -> Any:
    """
    Retrieve Agents.
    Users see: system agents + their own personal agents
    Admins see: all agents
    """
    if current_user.is_superuser:
        configs, count = crud.get_user_agent_configs(session=session, skip=skip, limit=limit, scope=scope)
    else:
        # Get system agents + user's personal agents
        system_configs, _ = crud.get_user_agent_configs(
            session=session, scope="system", enabled_only=True
        )
        personal_configs, _ = crud.get_user_agent_configs(
            session=session, scope="personal", owner_id=current_user.id
        )
        configs = system_configs + personal_configs
        count = len(configs)

    return UserAgentConfigsPublic(data=configs, count=count)


@router.get("/available", response_model=UserAgentConfigsPublic)
def list_available_agents(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
    scope: str | None = None,
) -> Any:
    """List agents available for room participation (enabled system agents and enabled personal agents)."""
    if current_user.is_superuser:
        configs, count = crud.get_user_agent_configs(
            session=session, skip=skip, limit=limit, scope=scope
        )
    else:
        # Get system agents + user's personal agents
        system_configs, _ = crud.get_user_agent_configs(
            session=session, scope="system", enabled_only=True
        )
        personal_configs, _ = crud.get_user_agent_configs(
            session=session, scope="personal", owner_id=current_user.id
        )
        configs = system_configs + personal_configs
        count = len(configs)
    return UserAgentConfigsPublic(data=configs, count=count)

@router.get("/generate-slug", response_model=GeneratedSlugResponse)
def generate_agent_slug(
    # session: SessionDep,
    # current_user: CurrentUser,
) -> GeneratedSlugResponse:
    """Generate a unique agent slug."""
    slug = coolname_generate_slug()
    return GeneratedSlugResponse(slug=slug)

@router.get("/{agent_id}", response_model=UserAgentConfigPublic)
def get_agent(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Any:
    """Get agent configuration by ID."""
    config = crud.get_user_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check access: system agents visible to all, personal only to owner/admin
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    return config


@router.get("/slug/{slug}", response_model=UserAgentConfigPublic)
def get_agent_by_slug(
    session: SessionDep,
    current_user: CurrentUser,
    slug: str,
) -> Any:
    """Get agent configuration by slug."""
    config = crud.get_user_agent_config_by_slug(session=session, slug=slug)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check access: system agents visible to all, personal only to owner/admin
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    return config


@router.post("/", response_model=UserAgentConfigPublic)
def create_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_in: UserAgentConfigCreate,
) -> Any:
    """
    Create a new agent configuration.
    """
    agentconfig = UserAgentConfig.model_validate(agent_in, update={"owner_id": current_user.id})
    session.add(agentconfig)
    session.commit()
    session.refresh(agentconfig)
        # Shadow versioning (non-blocking - skips if user not set up)
    try:
            snapshot = build_agent_snapshot(session=session, agent_id=agentconfig.id)
            version = shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=agentconfig.id,
                entity_data=snapshot,
                message=f"Create agent: {agentconfig.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} enqueued for agent {agentconfig.slug}")
    except Exception as e:
            logger.warning(f"Shadow versioning failed for agent {agentconfig.slug}: {e}")

    return agentconfig


@router.put("/{agent_id}", response_model=UserAgentConfigPublic)
def update_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    agentconfig_in: UserAgentConfigUpdate,
) -> Any:
    """
    Update an agent configuration.
    """
    agentconfig = session.get(UserAgentConfig, agent_id)
    if not agentconfig:
        raise HTTPException(status_code=404, detail="Agent Config not found")

    # Check permissions
    if agentconfig.scope == "system" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can modify system agents")
    if agentconfig.scope == "personal" and agentconfig.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")
    if not agentconfig.slug:
        raise HTTPException(status_code=500, detail="Agent config has no slug")
    update_dict: dict[str, Any] = agentconfig_in.model_dump(exclude_unset=True)
    agentconfig.sqlmodel_update(update_dict)
    session.add(agentconfig)
    session.commit()
    session.refresh(agentconfig)

    # Shadow versioning (non-blocking )
    try:
            snapshot = build_agent_snapshot(session=session, agent_id=agentconfig.id)
            version = shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=agentconfig.id,
                entity_data=snapshot,
                message=f"Update agent: {agentconfig.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} enqueued for agent {agentconfig.slug}")
    except Exception as e:
            logger.warning(f"Shadow versioning failed for agent {agentconfig.slug}: {e}")

    return agentconfig


@router.delete("/{agent_id}")
def delete_agent(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Message:
    """Delete an agent configuration."""
    config = crud.get_user_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check permissions
    if config.scope == "system" and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Only admins can delete system agents")
    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    crud.delete_user_agent_config(session=session, db_agent=config)
    return Message(message="Agent deleted successfully")


# @router.post("/pydantic-agent")
# async def run_agent(request: Request) -> Response:
#     return await AGUIAdapter.dispatch_request(request, agent=agent)
