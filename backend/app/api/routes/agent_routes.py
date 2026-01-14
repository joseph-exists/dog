from fastapi import APIRouter, HTTPException, Depends, Request
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser

from app.models import (
    AgentConfig, AgentConfigCreate, AgentConfigUpdate, AgentConfigPublic, AgentConfigsPublic,
    Message,
)

from typing import Any
import uuid


from app.services.agent_registry_service import agent_registry_service

from app import crud

from pydantic_ai.ui.ag_ui import AGUIAdapter
from starlette.responses import Response

from app.agents.quixote import agent
from app.models import AvailableAgent, AvailableAgentsPublic

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


@router.get("/available", response_model=AgentConfigsPublic)
def list_available_agents(session: SessionDep, current_user: CurrentUser) -> Any:
     """List agents available for room participation (enabled system agents)."""
     configs, count = crud.get_agent_configs(
         session=session, enabled_only=True, scope="system"
     )
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



AVAILABLE_AGENTS = [
    AvailableAgent(
        id="StoryAdvisor",
        name="Story Advisor",
        description="Helps with story structure, pacing, and narrative flow",
    ),
    AvailableAgent(
        id="SymbolWeaver",
        name="Symbol Weaver",
        description="Assists with themes, symbolism, and deeper meanings",
    ),
    AvailableAgent(
        id="CharacterForge",
        name="Character Forge",
        description="Develops character backgrounds, motivations, and arcs",
    ),
    AvailableAgent(
        id="PlotTwistArchitect",
        name="Plot Twist Architect",
        description="Creates surprising yet logical plot developments",
    ),
    AvailableAgent(
        id="DialogueCoach",
        name="Dialogue Coach",
        description="Improves character voice and conversational flow",
    ),
]


@router.get("/available", response_model=AvailableAgentsPublic)
def get_available_agents() -> AvailableAgentsPublic:
    """
    Get list of available agents for room participation.

    This endpoint provides the canonical list of agents that can be
    added to collaborative rooms. No authentication required.

    Returns:
        AvailableAgentsPublic with list of agents and count
    """
    return AvailableAgentsPublic(
        data=AVAILABLE_AGENTS,
        count=len(AVAILABLE_AGENTS),
    )


@router.post("/pydantic-agent")
async def run_agent(request: Request) -> Response:
    return await AGUIAdapter.dispatch_request(request, agent=agent)
