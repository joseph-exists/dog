import logging
import uuid
from typing import Any

from coolname import generate_slug as coolname_generate_slug
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.models import (
    Message,
    PromptConfig,
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


class CloneAgentRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    retain_user_access_provider: bool = False


def _generate_unique_agent_slug(*, session: SessionDep) -> str:
    for _ in range(10):
        candidate = coolname_generate_slug()
        if not crud.get_user_agent_config_by_slug(session=session, slug=candidate):
            return candidate
    raise HTTPException(status_code=500, detail="Unable to generate a unique slug")


def _can_clone_agent(
    *,
    current_user: CurrentUser,
    source_agent: UserAgentConfig,
) -> bool:
    if current_user.is_superuser:
        return True
    if source_agent.owner_id == current_user.id:
        return True
    if source_agent.scope == "system":
        return True
    return bool(source_agent.is_visible and source_agent.is_clonable)


def _validate_prompt_binding_access(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    prompt_config_id: uuid.UUID | None,
) -> None:
    if prompt_config_id is None:
        return
    prompt_config = session.get(PromptConfig, prompt_config_id)
    if not prompt_config:
        raise HTTPException(status_code=404, detail="PromptConfig not found")
    if not current_user.is_superuser and prompt_config.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied for PromptConfig binding")

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


@router.post("/{agent_id}/clone", response_model=UserAgentConfigPublic)
def clone_agent(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    agent_id: uuid.UUID,
    clone_in: CloneAgentRequest,
) -> Any:
    """
    Clone an existing agent into the current user's personal scope.

    Policy:
    - Superusers can clone any agent.
    - Users can clone their own agents.
    - Users can clone system agents.
    - Users can clone another user's personal agent only when
      source agent is both visible and clonable.
    """
    source_agent = crud.get_user_agent_config(session=session, agent_id=agent_id)
    if not source_agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if not _can_clone_agent(current_user=current_user, source_agent=source_agent):
        raise HTTPException(status_code=403, detail="Access denied")

    requested_name = (clone_in.name or "").strip()
    requested_slug = (clone_in.slug or "").strip()
    clone_name = requested_name or f"{source_agent.name} (Copy)"
    clone_slug = requested_slug or _generate_unique_agent_slug(session=session)

    existing_slug = crud.get_user_agent_config_by_slug(session=session, slug=clone_slug)
    if existing_slug:
        raise HTTPException(status_code=400, detail="Slug already exists")

    # Retain user-access-provider only for self-copy and only when explicitly requested.
    can_retain_provider_link = (
        bool(clone_in.retain_user_access_provider)
        and source_agent.owner_id == current_user.id
        and source_agent.scope == "personal"
    )
    cloned_user_access_provider = (
        source_agent.user_access_provider if can_retain_provider_link else None
    )

    clone_data = source_agent.model_dump()
    clone_data.pop("id", None)
    clone_data.pop("created_at", None)
    clone_data.pop("updated_at", None)
    clone_data.pop("version", None)
    clone_data.update(
        {
            "name": clone_name,
            "slug": clone_slug,
            "owner_id": current_user.id,
            "scope": "personal",
            "user_access_provider": cloned_user_access_provider,
        }
    )

    # Prompt bindings are user-owned. If source prompt config is inaccessible to the
    # cloning user, detach it to avoid leaking cross-user configuration.
    prompt_config_id = clone_data.get("prompt_config_id")
    if prompt_config_id is not None and not current_user.is_superuser:
        prompt_config = session.get(PromptConfig, prompt_config_id)
        if prompt_config is None or prompt_config.owner_id != current_user.id:
            clone_data["prompt_config_id"] = None
            clone_data["prompt_config_version_policy"] = "latest"
            clone_data["prompt_config_version_number"] = None

    cloned_agent = UserAgentConfig.model_validate(clone_data)
    session.add(cloned_agent)
    session.commit()
    session.refresh(cloned_agent)

    try:
        snapshot = build_agent_snapshot(session=session, agent_id=cloned_agent.id)
        shadow_service.enqueue_entity_version(
            session=session,
            user=current_user,
            entity_type="agent",
            entity_id=cloned_agent.id,
            entity_data=snapshot,
            message=f"Clone agent: {source_agent.name} -> {cloned_agent.name}",
        )
    except Exception as e:
        logger.warning(f"Shadow versioning failed for cloned agent {cloned_agent.slug}: {e}")

    return cloned_agent


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
    if agent_in.scope == "system" and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only admins can create system agents",
        )

    _validate_prompt_binding_access(
        session=session,
        current_user=current_user,
        prompt_config_id=agent_in.prompt_config_id,
    )
    agentconfig = UserAgentConfig.model_validate(
        agent_in.model_dump(),
        update={"owner_id": current_user.id},
    )
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
    if (
        not current_user.is_superuser
        and update_dict.get("scope") == "system"
        and agentconfig.scope != "system"
    ):
        raise HTTPException(
            status_code=403,
            detail="Only admins can set scope to system",
        )

    if "prompt_config_id" in update_dict:
        _validate_prompt_binding_access(
            session=session,
            current_user=current_user,
            prompt_config_id=update_dict.get("prompt_config_id"),
        )
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
