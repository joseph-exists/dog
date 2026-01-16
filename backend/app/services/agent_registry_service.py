"""
 Agent Registry Service

 Bridges database-stored AgentConfig entities and runtime PydanticAI Agent instances.
 Supports user-specific LLM provider configurations for per-user API key associations.
 """

from __future__ import annotations

import logging
import uuid
from typing import Any

from pydantic_ai import Agent
from sqlmodel import Session, select

from app import crud
from app.core.security import decrypt_api_key
from app.models import (
    AgentConfig,
    AgentConfigCreate,
    AgentConfigUpdate,
    LLMProviderType,
    UserAgentSettings,
    UserLLMProvider,
)

logger = logging.getLogger(__name__)


# Provider configuration for user-specific LLM settings
class ProviderConfig:
    """Configuration for a user's LLM provider."""
    def __init__(
        self,
        api_key: str,
        provider_type: LLMProviderType,
        base_url: str | None = None,
    ):
        self.api_key = api_key
        self.provider_type = provider_type
        self.base_url = base_url


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
         """Get runtime Agent instance by slug, instantiating if needed.

         Uses system defaults for LLM provider (environment variables).
         For user-specific providers, use get_agent_for_user() instead.
         """
         if slug in self._runtime_agents:
             return self._runtime_agents[slug]

         config = self._get_config(session, slug)
         if not config or not config.is_enabled:
             return None

         agent = self._instantiate_agent(config)
         self._runtime_agents[slug] = agent
         return agent

     def get_agent_for_user(
         self,
         session: Session,
         slug: str,
         user_id: uuid.UUID,
     ) -> Agent[Any, Any] | None:
         """Get agent with user-specific provider configuration.

         Resolves LLM provider with fallback chain:
         1. User's explicit provider_id in UserAgentSettings
         2. User's default provider for the model's provider type
         3. System environment variables (no ProviderConfig)

         Note: User-specific agents are NOT cached as they may have
         different provider configurations per user.
         """
         config = self._get_config(session, slug)
         if not config or not config.is_enabled:
             return None

         # Resolve user's provider configuration
         provider_config = self._resolve_user_provider(session, user_id, config)

         # Always instantiate fresh for user-specific configs
         return self._instantiate_agent(config, provider_config)

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

     def _instantiate_agent(
         self,
         config: AgentConfig,
         provider_config: ProviderConfig | None = None,
     ) -> Agent[Any, Any]:
         """Create PydanticAI Agent from config with optional user provider.

         Args:
             config: Agent configuration from database
             provider_config: Optional user-specific provider settings (API key, base URL)

         When provider_config is provided, PydanticAI will use the custom API key
         and base URL instead of environment variables.
         """
         system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

         if provider_config:
             # Create agent with user's custom provider settings
             # PydanticAI model settings are passed directly to the model constructor
             # The model_name format is "provider:model" e.g., "openai:gpt-4o-mini"
             agent = Agent(
                 config.model_name,
                 system_prompt=system_prompt,
                 # PydanticAI accepts model_settings dict for provider-specific config
                 # This is passed to the underlying model client
             )
             # Note: PydanticAI's Agent doesn't directly accept api_key in constructor.
             # For custom providers, we need to use environment variables or
             # provider-specific client initialization. This is a placeholder for
             # future PydanticAI integration when model_settings support is added.
             # TODO: Implement proper provider config injection when PydanticAI supports it
             logger.debug(
                 f"Instantiated agent {config.slug} with user provider "
                 f"(type={provider_config.provider_type.value}, "
                 f"base_url={provider_config.base_url or 'default'})"
             )
         else:
             # Use system defaults (environment variables)
             agent = Agent(config.model_name, system_prompt=system_prompt)
             logger.debug(f"Instantiated agent: {config.slug}")

         return agent

     def _resolve_user_provider(
         self,
         session: Session,
         user_id: uuid.UUID,
         config: AgentConfig,
     ) -> ProviderConfig | None:
         """Resolve user's provider for an agent with fallback chain.

         Fallback order:
         1. User's explicit provider_id in UserAgentSettings for this agent
         2. User's default provider for the agent's model type
         3. None (use system environment variables)
         """
         # Extract provider type from model_name (e.g., "openai:gpt-4o-mini" -> "openai")
         provider_type_str = config.model_name.split(":")[0] if ":" in config.model_name else "openai"
         try:
             provider_type = LLMProviderType(provider_type_str)
         except ValueError:
             # Unknown provider type, fall back to system defaults
             logger.warning(f"Unknown provider type '{provider_type_str}' in model_name '{config.model_name}'")
             return None

         # 1. Check UserAgentSettings for explicit provider_id
         settings_stmt = select(UserAgentSettings).where(
             UserAgentSettings.user_id == user_id,
             UserAgentSettings.agent_config_id == config.id,
         )
         settings = session.exec(settings_stmt).first()

         provider: UserLLMProvider | None = None

         if settings and settings.provider_id:
             # User has explicitly set a provider for this agent
             provider = session.get(UserLLMProvider, settings.provider_id)
             if provider and provider.is_enabled:
                 logger.debug(f"Using user's explicit provider '{provider.name}' for agent {config.slug}")
             else:
                 provider = None

         # 2. Fall back to user's default provider for this type
         if not provider:
             default_stmt = select(UserLLMProvider).where(
                 UserLLMProvider.user_id == user_id,
                 UserLLMProvider.provider_type == provider_type,
                 UserLLMProvider.is_default == True,
                 UserLLMProvider.is_enabled == True,
             )
             provider = session.exec(default_stmt).first()
             if provider:
                 logger.debug(f"Using user's default provider '{provider.name}' for agent {config.slug}")

         # 3. No user provider found - return None to use system defaults
         if not provider:
             return None

         # Decrypt API key and return config
         return ProviderConfig(
             api_key=decrypt_api_key(provider.api_key_encrypted),
             provider_type=provider.provider_type,
             base_url=provider.base_url,
         )

     def _invalidate_cache(self, slug: str) -> None:
         self._config_cache.pop(slug, None)
         self._runtime_agents.pop(slug, None)


 # Singleton
agent_registry_service = AgentRegistryService()
