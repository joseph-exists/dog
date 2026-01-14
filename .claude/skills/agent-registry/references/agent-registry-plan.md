 Agent Registry System - Implementation Plan

 Overview

 Design and implement a database-backed agent registry system that:
 - Stores agent configurations in PostgreSQL via SQLModel
 - Supports tiered access (users create personal agents, admins create system-wide agents)
 - Uses hybrid tool registration (Python code + JSON config)
 - Follows the Repository Pattern with existing CRUD patterns

 Architecture

 ┌─────────────────────────────────────────────────────────────────────────┐
 │ API Layer (agent_routes.py)                                             │
 │ ├── GET  /agents              - List all agents (filtered by scope)     │
 │ ├── GET  /agents/available    - List enabled agents for rooms           │
 │ ├── GET  /agents/{id}         - Get agent details                       │
 │ ├── POST /agents              - Create agent config                     │
 │ ├── PUT  /agents/{id}         - Update agent config                     │
 │ └── DELETE /agents/{id}       - Delete/disable agent                    │
 └─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Service Layer (agent_registry_service.py)                               │
 │ ├── AgentRegistryService class                                          │
 │ │   ├── register_agent()      - Create new config + validate            │
 │ │   ├── get_agent()           - Get runtime Agent instance              │
 │ │   ├── update_agent()        - Update config + invalidate cache        │
 │ │   ├── bootstrap_system_agents() - Seed system agents on startup       │
 │ │   └── _instantiate_agent()  - Create PydanticAI Agent from config     │
 │ └── Runtime cache (slug → Agent instance)                               │
 └─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Repository Layer (crud.py)                                              │
 │ ├── create_agent_config()                                               │
 │ ├── get_agent_config() / get_agent_config_by_slug()                     │
 │ ├── get_agent_configs() - with filtering                                │
 │ ├── update_agent_config()                                               │
 │ └── delete_agent_config()                                               │
 └─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Entity Layer (models.py)                                                │
 │ ├── AgentConfigBase           - Shared properties                       │
 │ ├── AgentConfigCreate         - API input validation                    │
 │ ├── AgentConfigUpdate         - Optional fields for updates             │
 │ ├── AgentConfig (table=True)  - Database model                          │
 │ ├── AgentConfigPublic         - API response                            │
 │ └── AgentConfigsPublic        - Paginated collection                    │
 └─────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
 ┌─────────────────────────────────────────────────────────────────────────┐
 │ Tool Registry (tool_registry.py) - NEW                                  │
 │ ├── TOOL_REGISTRY: dict[str, ToolDefinition]                            │
 │ ├── register_tool(slug, implementation)                                 │
 │ ├── get_tools_for_agent(agent_slug) → list[Tool]                        │
 │ └── Core tools defined in Python, additional via JSON config            │
 └─────────────────────────────────────────────────────────────────────────┘

 Implementation Steps

 [X] Phase 1: Entity Models (models.py) (complete)

 Add the 6-tier model pattern for AgentConfig:

 # ═══════════════════════════════════════════════════════════════════════════════
 # Agent Configuration Models
 # ═══════════════════════════════════════════════════════════════════════════════

 class AgentConfigBase(SQLModel):
     """Base properties shared by all agent config representations."""
     name: str = Field(max_length=100, description="Display name")
     slug: str = Field(max_length=50, description="Unique identifier/registry key")
     description: str | None = Field(default=None, max_length=500)
     model_name: str = Field(default="openai:gpt-4o-mini")
     system_prompt: str | None = None

     # JSON configuration fields
     tool_config: dict | None = Field(default=None, sa_column=Column(JSON))
     deps_config: dict | None = Field(default=None, sa_column=Column(JSON))
     metadata: dict | None = Field(default=None, sa_column=Column(JSON))

     # Behavior flags
     is_enabled: bool = Field(default=True)
     scope: str = Field(default="personal")  # "personal" | "system"
     participation_mode: str = Field(default="on_mention")  # "always" | "on_mention" | "manual"


 class AgentConfigCreate(AgentConfigBase):
     pass


 class AgentConfigUpdate(SQLModel):
     name: str | None = None
     description: str | None = None
     model_name: str | None = None
     system_prompt: str | None = None
     tool_config: dict | None = None
     deps_config: dict | None = None
     metadata: dict | None = None
     is_enabled: bool | None = None
     participation_mode: str | None = None


 class AgentConfig(AgentConfigBase, table=True):
     __tablename__ = "agent_configs"

     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
     owner_id: uuid.UUID | None = Field(default=None, foreign_key="user.id")
     created_at: datetime = Field(default_factory=datetime.now)
     updated_at: datetime | None = Field(default=None, sa_column_kwargs={"onupdate": datetime.now})
     version: int = Field(default=1)

     # Relationships
     # owner: "User" = Relationship(back_populates="agent_configs")


 class AgentConfigPublic(AgentConfigBase):
     id: uuid.UUID
     owner_id: uuid.UUID | None
     created_at: datetime
     updated_at: datetime | None
     version: int


 class AgentConfigsPublic(SQLModel):
     data: list[AgentConfigPublic]
     count: int

 File: backend/app/models.py
 Location: Add after line ~2328 (after AvailableAgent models)

 Also add User relationship (in post-definition section at end of file):
 # User → AgentConfig relationship
 User.agent_configs = Relationship(
     back_populates="owner",
     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
 )

 [X] Phase 2: Database Migration

 Create Alembic migration for the new table.

[X] Complete  Phase 3: Repository Layer (crud.py)



 # ═══════════════════════════════════════════════════════════════════════════════
 # Agent Config CRUD
 # ═══════════════════════════════════════════════════════════════════════════════

 def create_agent_config(
     *,
     session: Session,
     agent_in: AgentConfigCreate,
     owner_id: uuid.UUID | None = None,
 ) -> AgentConfig:
     """Create a new agent configuration."""
     db_obj = AgentConfig.model_validate(agent_in, update={"owner_id": owner_id})
     session.add(db_obj)
     session.commit()
     session.refresh(db_obj)
     return db_obj


 def get_agent_config(*, session: Session, agent_id: uuid.UUID) -> AgentConfig | None:
     return session.get(AgentConfig, agent_id)


 def get_agent_config_by_slug(*, session: Session, slug: str) -> AgentConfig | None:
     statement = select(AgentConfig).where(AgentConfig.slug == slug)
     return session.exec(statement).first()


 def get_agent_configs(
     *,
     session: Session,
     skip: int = 0,
     limit: int = 100,
     enabled_only: bool = True,
     scope: str | None = None,
     owner_id: uuid.UUID | None = None,
 ) -> tuple[list[AgentConfig], int]:
     """Get paginated agent configs with filtering."""
     filters = []
     if enabled_only:
         filters.append(AgentConfig.is_enabled == True)
     if scope:
         filters.append(AgentConfig.scope == scope)
     if owner_id:
         filters.append(AgentConfig.owner_id == owner_id)

     count_stmt = select(func.count()).select_from(AgentConfig).where(*filters)
     count = session.exec(count_stmt).one()

     stmt = select(AgentConfig).where(*filters).offset(skip).limit(limit)
     configs = session.exec(stmt).all()
     return list(configs), count


 def update_agent_config(
     *,
     session: Session,
     db_agent: AgentConfig,
     agent_in: AgentConfigUpdate,
 ) -> AgentConfig:
     update_data = agent_in.model_dump(exclude_unset=True)
     db_agent.sqlmodel_update(update_data)
     db_agent.version += 1
     session.add(db_agent)
     session.commit()
     session.refresh(db_agent)
     return db_agent


 def delete_agent_config(*, session: Session, db_agent: AgentConfig) -> None:
     session.delete(db_agent)
     session.commit()

 File: backend/app/crud.py
 Location: Add at end of file

 [X] Complete : Phase 4: Tool Registry (NEW FILE)

 Create a tool registry for the hybrid approach:

 # backend/app/agents/tool_registry.py
 """
 Tool Registry - Maps agent slugs to their available tools.

 Hybrid approach:
 - Core tools defined in Python with full type safety
 - Additional tools can be added via JSON config for flexibility
 """

 from __future__ import annotations
 from dataclasses import dataclass
 from typing import Any, Callable
 import logging

 logger = logging.getLogger(__name__)

 @dataclass
 class ToolDefinition:
     """Definition of a tool that can be attached to agents."""
     name: str
     description: str
     implementation: Callable[..., Any]
     parameter_schema: dict | None = None  # For JSON-defined tools


 # Global registries
 TOOL_REGISTRY: dict[str, ToolDefinition] = {}
 AGENT_TOOL_MAPPING: dict[str, list[str]] = {}


 def register_tool(name: str, tool_def: ToolDefinition) -> None:
     """Register a tool definition."""
     if name in TOOL_REGISTRY:
         logger.warning(f"Tool '{name}' already registered, overwriting")
     TOOL_REGISTRY[name] = tool_def
     logger.debug(f"Registered tool: {name}")


 def register_agent_tools(agent_slug: str, tool_names: list[str]) -> None:
     """Associate tools with an agent by slug."""
     AGENT_TOOL_MAPPING[agent_slug] = tool_names


 def get_tools_for_agent(agent_slug: str) -> list[ToolDefinition]:
     """Get all tool definitions for an agent."""
     tool_names = AGENT_TOOL_MAPPING.get(agent_slug, [])
     return [TOOL_REGISTRY[name] for name in tool_names if name in TOOL_REGISTRY]


 def list_tools() -> list[str]:
     """List all registered tool names."""
     return list(TOOL_REGISTRY.keys())

 File: backend/app/agents/tool_registry.py (NEW)

 [X] Complete Phase 5: Agent Registry Service (NEW FILE)

 Create the service layer:

 # backend/app/services/agent_registry_service.py
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

 File: backend/app/services/agent_registry_service.py (NEW)

 [X] Complete: Phase 6: API Routes (agent_routes.py)

 Update routes with full CRUD:

 # Updated agent_routes.py

 from fastapi import APIRouter, HTTPException, Depends
 from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
 from app.models import (
     AgentConfig, AgentConfigCreate, AgentConfigUpdate,
     AgentConfigPublic, AgentConfigsPublic,
 )
 from app.services.agent_registry_service import agent_registry_service
 from app import crud

 router = APIRouter(prefix="/agents", tags=["agents"])


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

 File: backend/app/api/routes/agent_routes.py

 Phase 7: Startup Bootstrap

 Add bootstrap using lifespan context manager (FastAPI's modern approach):

 # In backend/app/main.py

 from contextlib import asynccontextmanager
 from sqlmodel import Session
 from app.services.agent_registry_service import agent_registry_service
 from app.core.db import engine

 @asynccontextmanager
 async def lifespan(app: FastAPI):
     """Application lifespan - bootstrap on startup."""
     # Startup: bootstrap system agents
     with Session(engine) as session:
         agent_registry_service.bootstrap_system_agents(session)
     yield
     # Shutdown: cleanup if needed

 app = FastAPI(
     title=settings.PROJECT_NAME,
     openapi_url=f"{settings.API_V1_STR}/openapi.json",
     generate_unique_id_function=custom_generate_unique_id,
     lifespan=lifespan,  # Add lifespan parameter
 )

 File: backend/app/main.py

 Phase 8: Integration with agent_runner.py

 Update agent_runner to use registry service:

 # In backend/app/services/agent_runner.py

 from app.services.agent_registry_service import agent_registry_service
 from app.agents.agent_registry import get_agent as legacy_get_agent

 async def get_agent_instance(session: Session, slug: str) -> Agent[Any, Any] | None:
     """Get agent instance, with fallback to legacy registry during transition."""
     # Try new registry first
     agent = agent_registry_service.get_agent(session, slug)
     if agent:
         return agent

     # Fallback to legacy registry
     try:
         return legacy_get_agent(slug)
     except KeyError:
         return None

 File: backend/app/services/agent_runner.py

 Files to Create/Modify
 ┌────────────────────────────────────────────────┬────────┬─────────────────────────────────────────┐
 │                      File                      │ Action │               Description               │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/models.py                          │ MODIFY │ Add AgentConfig models (6-tier pattern) │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/crud.py                            │ MODIFY │ Add agent config CRUD functions         │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/agents/tool_registry.py            │ CREATE │ Tool registry for hybrid approach       │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/services/agent_registry_service.py │ CREATE │ Service layer for agent management      │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/api/routes/agent_routes.py         │ MODIFY │ Add full CRUD endpoints                 │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/main.py                            │ MODIFY │ Add bootstrap on startup                │
 ├────────────────────────────────────────────────┼────────┼─────────────────────────────────────────┤
 │ backend/app/services/agent_runner.py           │ MODIFY │ Integrate with registry service         │
 └────────────────────────────────────────────────┴────────┴─────────────────────────────────────────┘
 Database Migration Required

 After adding models:
 cd backend
 alembic revision --autogenerate -m "Add agent_configs table"
 alembic upgrade head

 Verification Plan

 1. Unit Tests: Create tests in backend/app/tests/api/routes/test_agent_routes.py
   - Test CRUD operations
   - Test permission enforcement (personal vs system scope)
   - Test bootstrap idempotency
 2. Manual Testing:
 # Start backend
 cd backend && fastapi dev app/main.py

 # Test endpoints via OpenAPI docs
 # http://localhost:8000/docs

 # Verify system agents bootstrapped
 curl http://localhost:8000/api/v1/agents/available
 3. Integration Check:
   - Add agent to room
   - Send message
   - Verify agent responds using registry service

 Migration Strategy

 The implementation includes fallback to the existing agent_registry.py during transition:
 1. New AgentConfig database + service layer
 2. agent_runner checks new registry first, falls back to legacy
 3. System agents bootstrapped to match existing AVAILABLE_AGENTS
 4. Gradual migration of agent definitions to database
 5. Eventually remove legacy registry when fully migrated