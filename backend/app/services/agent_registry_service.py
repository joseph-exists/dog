"""
 Agent Registry Service

not real - and lots of junk to clean out, but it's worth keeping because the tool registry is coming.
if anything calls or imports this file, that's a big big problem, find out why

 Bridges database-stored AgentConfig entities and runtime PydanticAI Agent instances.
 Supports user-specific LLM provider configurations for per-user API key associations.
 """

# from __future__ import annotations

# import logging
# import uuid
# from typing import Any

# from coolname import generate_slug as coolname_generate_slug
# from pydantic_ai import Agent
# from sqlmodel import Session

# from app import crud
# from app.core.security import decrypt_api_key
# from app.models import (
#     UserAgentConfig,
#     UserAgentConfigCreate,
#     UserAgentConfigUpdate,
# )

# logger = logging.getLogger(__name__)


# # Provider configuration for user-specific access provider (UserAccessProvider)
# class ProviderConfig:
#     """Configuration for a user's access provider."""
#     def __init__(
#         self,
#         api_key: str,
#         provider_type: str | None, # this is the API spec provider type. not the access provider type.  a user access provider can support many provider_types in the world.  we support one or lots, and if it's lots, we don't discriminate yet.
#         base_url: str | None = None,
#     ):
#         self.api_key = api_key
#         self.base_url = base_url


# class AgentRegistryService:
#      """Service for managing agent configurations and runtime instances."""

#      def __init__(self) -> None:
#          self._runtime_agents: dict[str, Agent[Any, Any]] = {}
#          self._config_cache: dict[str, UserAgentConfig] = {}

#      def register_agent(
#          self,
#          session: Session,
#          agent_in: UserAgentConfigCreate,
#          owner_id: uuid.UUID | None = None,
#      ) -> UserAgentConfig:
#          """Register a new agent configuration."""
#          existing = crud.get_user_agent_config_by_slug(session=session, slug=agent_in.slug)
#          if existing:
#              raise ValueError(f"Agent with slug '{agent_in.slug}' already exists")

#          config = crud.create_user_agent_config(
#              session=session,
#              agent_in=agent_in,
#              owner_id=owner_id,
#          )

#          self._invalidate_cache(agent_in.slug)
#          logger.info(f"Registered agent: {config.slug}")
#          return config

#      def get_user_agent_config_for_user(
#          self,
#          session: Session,
#          slug: str,
#          user_id: uuid.UUID,
#      ) -> Agent[Any, Any] | None:
#          """Get agent config.

#          """
#          config = self._get_config(session, slug)
#          if not config or not config.is_enabled:
#              return None

#          # Get user agent config settings
#          settings = self._get_user_settings(session, user_id, config.id)
#          # Always instantiate fresh for user-specific configs
#          return self._instantiate_agent(config, provider_config, effective_model_name)

#      def get_config(self, session: Session, slug: str) -> UserAgentConfig | None:
#          return self._get_config(session, slug)

#      def list_agents(
#          self,
#          session: Session,
#          skip: int = 0,
#          limit: int = 100,
#          enabled_only: bool = True,
#          scope: str | None = None,
#          owner_id: uuid.UUID | None = None,
#      ) -> tuple[list[UserAgentConfig], int]:
#          return crud.get_user_agent_configs(  # TODO MAP THIS
#              session=session,
#              skip=skip,
#              limit=limit,
#              enabled_only=enabled_only,
#              scope=scope,
#              owner_id=owner_id,
#          )

#      def update_agent(
#          self,
#          session: Session,
#          slug: str,
#          agent_in: UserAgentConfigUpdate,
#      ) -> UserAgentConfig | None:
#          config = crud.get_user_agent_config_by_slug(session=session, slug=slug)
#          if not config:
#              return None

#          updated = crud.update_user_agent_config(
#              session=session,
#              db_agent=config,
#              agent_in=agent_in,
#          )
#          self._invalidate_cache(slug)
#          return updated

#      def generate_slug(self, session: Session, max_length: int = 50) -> str:
#          """Generate a unique agent slug using coolname."""
#          for _ in range(20):
#              slug = str(coolname_generate_slug())
#              if len(slug) > max_length:
#                  slug = slug[:max_length].rstrip("-") or slug[:max_length]
#              if not crud.get_user_agent_config_by_slug(session=session, slug=slug):
#                  return slug
#          raise ValueError("Failed to generate a unique slug")

#      def _get_config(self, session: Session, slug: str) -> UserAgentConfig | None:
#          if slug in self._config_cache:
#              return self._config_cache[slug]
#          config = crud.get_user_agent_config_by_slug(session=session, slug=slug)
#          if config:
#              self._config_cache[slug] = config
#          return config

#      def _get_user_settings(
#          self,
#          session: Session,
#          user_id: uuid.UUID,
#          agent_config_id: uuid.UUID,
#      ) -> UserAgentConfig | None:
        
#          """Get user's settings for a specific agent.
#          # Placeholder for future user-specific override settings
#          # When UserAgentConfig table exists, query it here:
#          # statement = select(UserAgentConfig).where(
#          #     UserAgentConfig.user_id == user_id,
#          #     UserAgentConfig.agent_config_id == agent_config_id
#          # )
#          # return session.exec(statement).first()
#          return None
# """

#      def _instantiate_agent(
#          self,
#          config: UserAgentConfig,
#          provider_config: ProviderConfig | None = None,
#          model_name: str | None = None,
#      ) -> Agent[Any, Any]:
#          """Create PydanticAI Agent from config with user access provider and other UserAgentConfig parameters.

#          Args:
#              config: Agent configuration from database
#              provider_config: Optional user-specific provider settings (API key, base URL)
#              model_name: Optional model override (defaults to config.model_name)

#          When provider_config is provided, PydanticAI will use the custom API key
#          and base URL instead of environment variables.
#          """
#          effective_model = model_name or config.model_name

#          # Build system prompt from config
#          system_prompt = config.system_prompt
#          if not system_prompt:
#              # Fallback to auto-generated prompt
#              system_prompt = f"You are {config.name}."
#              if config.description:
#                  system_prompt += f" {config.description}"

#          if provider_config:
#              # Create agent with user's custom provider settings
#              # Note: PydanticAI models pick up API keys from environment variables by default.
#              # For custom API keys per user, we need to pass them through model configuration.
#              #
#              # TODO: Implement proper API key injection based on provider_type:
#              # - For OpenAI: Use OpenAI client with custom api_key
#              # - For Anthropic: Use Anthropic client with custom api_key
#              # - For OpenAI-compatible: Use OpenAI client with custom base_url and api_key
#              #
#              # This will require importing the appropriate client classes and
#              # passing them to Agent() constructor via the model parameter.
#              # Example: Agent(OpenAI('gpt-4', api_key=provider_config.api_key))

#              logger.warning(
#                  f"User-specific provider configured for {config.slug}, "
#                  f"but custom API key injection not yet implemented. "
#                  f"Using system defaults."
#              )
#              agent = Agent(effective_model, system_prompt=system_prompt)
#          else:
#              # Use system defaults (environment variables)
#              agent = Agent(effective_model, system_prompt=system_prompt)
#              logger.debug(f"Instantiated agent {config.slug} with model={effective_model}")

#          return agent

#      def _resolve_user_access_provider(
#          self,
#          session: Session,
#          user_id: uuid.UUID,
#          config: UserAgentConfig,
#          settings: UserAgentConfig | None,
#          effective_model_name: str,
#      ) -> ProviderConfig | None:
#         """Resolve user access provider for an agent.

#         Resolution priority:
#         Config requirement (config.user_access_provider)

#         Args:
#             session: Database session
#             user_id: User requesting the agent
#             config: Agent configuration
#             settings: Pre-fetched user settings (to avoid duplicate query)
#             effective_model_name: The model that will be used (may be overridden)

#         Returns:
#             ProviderConfig with decrypted API key if user provider is configured,
#         """
#         # Determine which user_access_provider to use
#         provider_id = None
#         if settings and settings.user_access_provider:
#             provider_id = settings.user_access_provider
#         elif config.user_access_provider:
#             provider_id = config.user_access_provider

#         # If no user access provider configured, we need to reject.

#         if not provider_id:
#             return None

#         # Fetch the user's access provider
#         provider = crud.get_access_provider(
#             session=session,
#             provider_id=provider_id,
#             user_id=user_id, 
#         )

#         if not provider:
#             logger.warning(f"User {user_id} has invalid provider {provider_id} configured")
#             return None

#         # Parse provider type from model name (e.g., "openai:gpt-4" -> "openai")
#         provider_type = self._parse_provider_type(effective_model_name)

#         # Decrypt API key and return config
#         return ProviderConfig(
#             api_key=decrypt_api_key(provider.api_key_encrypted),
#             provider_type=provider_type,
#             base_url=provider.base_url,
#         )

#      def _parse_provider_type(self, model_name: str) -> str:
#         """Parse provider type from model name.

#         Model names are in format: "provider:model" (e.g., "openai:gpt-4")
#         If no colon, assume the whole string is the provider type.

#         Args:
#             model_name: Full model identifier

#         Returns:
#             Provider type string (e.g., "openai", "anthropic", "openai_compatible")
#         """
#         if ":" in model_name:
#             return model_name.split(":", 1)[0]
#         return model_name

#      def _invalidate_cache(self, slug: str) -> None:
#          self._config_cache.pop(slug, None)
#          self._runtime_agents.pop(slug, None)


# Singleton
# agent_registry_service = AgentRegistryService()
