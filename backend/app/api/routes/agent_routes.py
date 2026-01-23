import logging
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from datetime import datetime

from sqlmodel import select

from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.models import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigPublic,
    AgentConfigsPublic,
    AgentConfigUpdate,
    Message,
    UserAgentSettings,
    UserAgentSettingsCreate,
    UserAgentSettingsPublic,
    UserAgentSettingsUpdate,
    UserLLMProvider,
)
from app.services.agent_registry_service import agent_registry_service
from app.services.shadow_service import shadow_service
from app.services.shadow_exporters import build_agent_snapshot

logger = logging.getLogger(__name__)

from app import crud

from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.responses import Response



router = APIRouter(prefix="/agents", tags=["agents"])


class GeneratedSlugResponse(BaseModel):
    slug: str

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


@router.get("/generate-slug", response_model=GeneratedSlugResponse)
def generate_agent_slug(
    session: SessionDep,
    current_user: CurrentUser,
) -> GeneratedSlugResponse:
    """Generate a unique agent slug."""
    slug = agent_registry_service.generate_slug(session=session)
    return GeneratedSlugResponse(slug=slug)


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


@router.get("/slug/{slug}", response_model=AgentConfigPublic)
def get_agent_by_slug(
    session: SessionDep,
    current_user: CurrentUser,
    slug: str,
) -> Any:
    """Get agent configuration by slug."""
    config = crud.get_agent_config_by_slug(session=session, slug=slug)
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
            snapshot = build_agent_snapshot(session=session, agent_id=config.id)
            version = shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=config.id,
                entity_data=snapshot,
                message=f"Create agent: {config.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} enqueued for agent {config.slug}")
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
            snapshot = build_agent_snapshot(session=session, agent_id=updated.id)
            version = shadow_service.enqueue_entity_version(
                session=session,
                user=current_user,
                entity_type="agent",
                entity_id=updated.id,
                entity_data=snapshot,
                message=f"Update agent: {updated.name}",
            )
            if version:
                logger.info(f"Shadow version {version.version_number} enqueued for agent {updated.slug}")
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


# @router.post("/pydantic-agent")
# async def run_agent(request: Request) -> Response:
#     return await AGUIAdapter.dispatch_request(request, agent=agent)


# ============================================================================
# User Agent Settings (per-user provider associations)
# ============================================================================


@router.get("/{agent_id}/my-settings", response_model=UserAgentSettingsPublic | None)
def get_my_agent_settings(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Any:
    """Get user's personal settings for an agent (provider, etc.).

    Returns the user's settings for this agent, or null if none configured.
    Settings include chosen LLM provider and optional custom system prompt.
    """
    # Verify agent exists and user has access
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    # Get user's settings for this agent
    statement = select(UserAgentSettings).where(
        UserAgentSettings.user_id == current_user.id,
        UserAgentSettings.agent_config_id == agent_id,
    )
    settings = session.exec(statement).first()
    return settings


@router.put("/{agent_id}/my-settings", response_model=UserAgentSettingsPublic)
def update_my_agent_settings(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    settings_in: UserAgentSettingsUpdate,
) -> Any:
    """Create or update user's personal settings for an agent.

    Allows user to associate their LLM provider with any agent:
    - For personal agents: customize your own agent
    - For system agents: use your own API key without affecting others
    """
    # Verify agent exists and user has access
    config = crud.get_agent_config(session=session, agent_id=agent_id)
    if not config:
        raise HTTPException(status_code=404, detail="Agent not found")

    if config.scope == "personal" and config.owner_id != current_user.id:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="Access denied")

    # Validate provider_id if provided
    if settings_in.provider_id:
        provider = session.get(UserLLMProvider, settings_in.provider_id)
        if not provider or provider.user_id != current_user.id:
            raise HTTPException(status_code=400, detail="Invalid provider ID")

    # Get or create settings
    statement = select(UserAgentSettings).where(
        UserAgentSettings.user_id == current_user.id,
        UserAgentSettings.agent_config_id == agent_id,
    )
    settings = session.exec(statement).first()

    if settings:
        # Update existing
        update_data = settings_in.model_dump(exclude_unset=True)
        settings.sqlmodel_update(update_data)
        settings.updated_at = datetime.now()
    else:
        # Create new
        settings = UserAgentSettings(
            user_id=current_user.id,
            agent_config_id=agent_id,
            **settings_in.model_dump(exclude_unset=True),
        )
        session.add(settings)

    session.commit()
    session.refresh(settings)
    return settings


@router.delete("/{agent_id}/my-settings")
def delete_my_agent_settings(
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
) -> Message:
    """Remove user's personal settings for an agent.

    After deletion, agent will use system defaults.
    """
    statement = select(UserAgentSettings).where(
        UserAgentSettings.user_id == current_user.id,
        UserAgentSettings.agent_config_id == agent_id,
    )
    settings = session.exec(statement).first()

    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")

    session.delete(settings)
    session.commit()
    return Message(message="Settings removed")
