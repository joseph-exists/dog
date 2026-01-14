"""
 Agent Registry Service

 Bridges database-stored AgentConfig entities and runtime PydanticAI Agent instances.
 """

from __future__ import annotations
import logging
import uuid
from typing import Any

from pydantic_ai import Agent
from sqlmodel import Session

from app.models import AgentConfig, AgentConfigCreate, AgentConfigUpdate
from app import crud

logger = logging.getLogger(__name__)


class AgentRegistryService:
     """Service for managing agent configurations and runtime instances."""

     def __init__(self):
         self._runtime_agents: dict[str, Agent[Any, Any]] = {}
         self._config_cache: dict[str, AgentConfig] = {}

     def register_agent(
         self,
         session: Session,
         agent_in: AgentConfigCreate,
         owner_id: uuid.UUID | None = None,
     ) -> AgentConfig:
         """Register a new agent configuration."""
         existing = crud.get_agent_config_by_slug(session=session, slug=agent_in.slug)
         if existing:
             raise ValueError(f"Agent with slug '{agent_in.slug}' already exists")

         config = crud.create_agent_config(
             session=session,
             agent_in=agent_in,
             owner_id=owner_id,
         )
         self._invalidate_cache(agent_in.slug)
         logger.info(f"Registered agent: {config.slug}")
         return config

     def get_agent(self, session: Session, slug: str) -> Agent[Any, Any] | None:
         """Get runtime Agent instance by slug, instantiating if needed."""
         if slug in self._runtime_agents:
             return self._runtime_agents[slug]

         config = self._get_config(session, slug)
         if not config or not config.is_enabled:
             return None

         agent = self._instantiate_agent(config)
         self._runtime_agents[slug] = agent
         return agent

     def get_config(self, session: Session, slug: str) -> AgentConfig | None:
         return self._get_config(session, slug)

     def list_agents(
         self,
         session: Session,
         skip: int = 0,
         limit: int = 100,
         enabled_only: bool = True,
         scope: str | None = None,
         owner_id: uuid.UUID | None = None,
     ) -> tuple[list[AgentConfig], int]:
         return crud.get_agent_configs(
             session=session,
             skip=skip,
             limit=limit,
             enabled_only=enabled_only,
             scope=scope,
             owner_id=owner_id,
         )

     def update_agent(
         self,
         session: Session,
         slug: str,
         agent_in: AgentConfigUpdate,
     ) -> AgentConfig | None:
         config = crud.get_agent_config_by_slug(session=session, slug=slug)
         if not config:
             return None

         updated = crud.update_agent_config(
             session=session,
             db_agent=config,
             agent_in=agent_in,
         )
         self._invalidate_cache(slug)
         return updated
# lets remove this as quick as we can :)
     def bootstrap_system_agents(self, session: Session) -> None:
         """Ensure system agents exist. Called on startup."""
         system_agents = [
             AgentConfigCreate(
                 slug="StoryAdvisor",
                 name="Story Advisor",
                 description="Helps with story structure, pacing, and narrative flow",
                 scope="system",
             ),
             AgentConfigCreate(
                 slug="CharacterForge",
                 name="Character Forge",
                 description="Character development, motivations, and arcs",
                 scope="system",
             ),
             AgentConfigCreate(
                 slug="SymbolWeaver",
                 name="Symbol Weaver",
                 description="Explores themes, symbolism, and deeper meanings",
                 scope="system",
             ),
             AgentConfigCreate(
                 slug="PlotTwistArchitect",
                 name="Plot Twist Architect",
                 description="Crafts plot twists and narrative surprises",
                 scope="system",
             ),
             AgentConfigCreate(
                 slug="DialogueCoach",
                 name="Dialogue Coach",
                 description="Refines character voice and conversation flow",
                 scope="system",
             ),
         ]

         for agent_def in system_agents:
             existing = crud.get_agent_config_by_slug(session=session, slug=agent_def.slug)
             if not existing:
                 crud.create_agent_config(session=session, agent_in=agent_def)
                 logger.info(f"Bootstrapped system agent: {agent_def.slug}")

     def _get_config(self, session: Session, slug: str) -> AgentConfig | None:
         if slug in self._config_cache:
             return self._config_cache[slug]
         config = crud.get_agent_config_by_slug(session=session, slug=slug)
         if config:
             self._config_cache[slug] = config
         return config

     def _instantiate_agent(self, config: AgentConfig) -> Agent[Any, Any]:
         """Create PydanticAI Agent from config."""
         system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"
         agent = Agent(config.model_name, system_prompt=system_prompt)
         logger.debug(f"Instantiated agent: {config.slug}")
         return agent

     def _invalidate_cache(self, slug: str) -> None:
         self._config_cache.pop(slug, None)
         self._runtime_agents.pop(slug, None)


 # Singleton
agent_registry_service = AgentRegistryService()
