"""
 Agent Registry Service

 Bridges database-stored AgentConfig entities and runtime PydanticAI Agent instances.
 Supports user-specific LLM provider configurations for per-user API key associations.
 """

from __future__ import annotations

import logging
import uuid
from typing import Any

from coolname import generate_slug as coolname_generate_slug
from pydantic_ai import Agent
from sqlmodel import Session, select

from app import crud
from app.core.security import decrypt_api_key
from app.models import (
    UserAgentConfig,
    UserAgentConfigCreate,
    UserAgentConfigUpdate,
    UserAccessProvider,
)

logger = logging.getLogger(__name__)


# Provider configuration for user-specific access provider (UserAccessProvider)
class ProviderConfig:
    """Configuration for a user's access provider."""
    def __init__(
        self,
        api_key: str,
        provider_type: str,
        base_url: str | None = None,
    ):
        self.api_key = api_key
        self.base_url = base_url


class AgentRegistryService:
     """Service for managing agent configurations and runtime instances."""

     def __init__(self):
         self._runtime_agents: dict[str, Agent[Any, Any]] = {}
         self._config_cache: dict[str, UserAgentConfig] = {}

     def register_agent(
         self,
         session: Session,
         agent_in: UserAgentConfigCreate,
         owner_id: uuid.UUID | None = None,
     ) -> UserAgentConfig:
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

     def get_agent_config_for_user(
         self,
         session: Session,
         slug: str,
         user_id: uuid.UUID,
     ) -> Agent[Any, Any] | None:
         """Get agent config with  model, api provider type, and access provider configuration.

         Resolution order:
         1. Model: User's model_name from UserAgentConfig
         2: Model provider API type: (openai, anthropic, openai_compatible, etc) - so we know which API structure to use.
         3. Access Provider: User's explicit access provider (from UserAccessProvider) - so we know where to send it
         """
         config = self._get_config(session, slug)
         if not config or not config.is_enabled:
             return None

         # Get user settings - may need refactored
         settings = self._get_user_settings(session, user_id, config.id)

         # Determine effective model name TODO

         # Resolve user's provider configuration based on effective model TODO needs refactor
         provider_config = self._resolve_user_provider(session, user_id, config, settings)

         # Always instantiate fresh for user-specific configs TODO: refactor
         return self._instantiate_agent(e)

     def get_config(self, session: Session, slug: str) -> UserAgentConfig | None:
         return self._get_config(session, slug)

    # TODO : these needs refactored to use UserAgentConfig classes
     def list_agents(
         self,
         session: Session,
         skip: int = 0,
         limit: int = 100,
         enabled_only: bool = True,
         scope: str | None = None,
         owner_id: uuid.UUID | None = None,
     ) -> tuple[list[UserAgentConfig], int]:
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
         agent_in: UserAgentConfigUpdate,
     ) -> UserAgentConfig | None:
         config = crud.get_user_agent_config_by_slug(session=session, slug=slug)
         if not config:
             return None

         updated = crud.update_user_agent_config(
             session=session,
             db_agent=config,
             agent_in=agent_in,
         )
         self._invalidate_cache(slug)
         return updated

     def generate_slug(self, session: Session, max_length: int = 50) -> str:
         """Generate a unique agent slug using coolname."""
         for _ in range(20):
             slug = coolname_generate_slug()
             if len(slug) > max_length:
                 slug = slug[:max_length].rstrip("-") or slug[:max_length]
             if not crud.get_agent_config_by_slug(session=session, slug=slug):
                 return slug
         raise ValueError("Failed to generate a unique slug")

     def _get_config(self, session: Session, slug: str) -> UserAgentConfig | None:
         if slug in self._config_cache:
             return self._config_cache[slug]
         config = crud.get_agent_config_by_slug(session=session, slug=slug)
         if config:
             self._config_cache[slug] = config
         return config

     def _get_user_settings(
         self,
         session: Session,
         user_id: uuid.UUID,
         agent_config_id: uuid.UUID,
     ) -> UserAgentConfig | None:
         """Get user's settings for a specific agent."""


     def _instantiate_agent(
         self,
         config: UserAgentConfig,
         provider_config: ProviderConfig | None = None,
         model_name: str | None = None,
     ) -> Agent[Any, Any]:
         """Create PydanticAI Agent from config with user access provider and other AgentConfig parameters.

         Args:
             user_agent_config: Agent configuration from database
             access_provider_config: Optional user-specific provider settings (API key, base URL)
             model_name: Optional model override (defaults to config.model_name)

         When provider_config is provided, PydanticAI will use the custom API key
         and base URL instead of environment variables.
         """
         effective_model = model_name or config.model_name
         system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

        # TODO : all new UserAgentConfigs (which is how we'll manage all user agents are required to have this)
        # TODO : we don't care about back compat at this point.
         if provider_config:
             # Create agent with user's custom provider settings
             agent = Agent(
                 effective_model, # model is in UserAgentConfig
                 system_prompt=system_prompt,
             )
             # Note: PydanticAI's Agent doesn't directly accept api_key in constructor.
             # TODO: Implement proper provider config injection when PydanticAI supports it
         else:
             # Use system defaults (environment variables)
             agent = Agent(effective_model, system_prompt=system_prompt)
             logger.debug(f"Instantiated agent {config.slug} with model={effective_model}")

         return agent

     def _resolve_user_access_provider(
         self,
         session: Session,
         user_id: uuid.UUID,
         config: UserAgentConfig,
         settings: UserAgentConfig | None,
         effective_model_name: str, # needs to be from UserAgentConfig
     ) -> ProviderConfig | None:
        """Resolve user access provider for an agent.

         User's explicit config in UserAgentConfig for this agent

        Args:
            settings: Pre-fetched user settings (to avoid duplicate query)
            effective_model_name: The model that will be used (may be overridden)
        """
        provider_type_obj = crud.get_access_provider(
        )

        provider: UserAccessProvider | None = None

        return ProviderConfig(
            api_key=decrypt_api_key(provider.api_key_encrypted),
            provider_type=provider_type,
            base_url=provider.base_url,
        )

     def _invalidate_cache(self, slug: str) -> None:
         self._config_cache.pop(slug, None)
         self._runtime_agents.pop(slug, None)


 # Singleton
agent_registry_service = AgentRegistryService()
