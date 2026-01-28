from __future__ import annotations

import logging
import uuid
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from sqlalchemy import func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decrypt_api_key
from app.models import (
    AgentConfig,
    LLMProviderType,
    UserAgentSettings,
    UserLLMProvider,
)
from app.services.agent_tools import AgentDeps, emit_ui_component, request_agent_assistance

logger = logging.getLogger(__name__)

OPENAI = "openai"
OPENAI_COMPATIBLE = "openai_compatible"
ANTHROPIC = "anthropic"
GOOGLE = "google"


async def get_agent_config(session: AsyncSession, slug: str) -> AgentConfig | None:
    """Get agent configuration from database by slug."""
    result = await session.exec(
        select(AgentConfig).where(AgentConfig.slug == slug)
    )
    row = result.one_or_none()
    return row[0] if row and not isinstance(row, AgentConfig) else row


async def resolve_user_credentials(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_config: AgentConfig,
) -> tuple[str, str | None, str | None, str | None]:
    """
    Resolve user's credentials for an agent.

    Returns:
        Tuple of (effective_model_name, decrypted_api_key, provider_type, base_url)
    """
    settings_result = await session.exec(
        select(UserAgentSettings).where(
            UserAgentSettings.user_id == user_id,
            UserAgentSettings.agent_config_id == agent_config.id,
        )
    )
    settings_row = settings_result.one_or_none()
    settings = (
        settings_row[0]
        if settings_row and not isinstance(settings_row, UserAgentSettings)
        else settings_row
    )

    effective_model_name = agent_config.model_name
    if settings and settings.model_name_override:
        effective_model_name = settings.model_name_override
        logger.debug(
            f"Using model override '{effective_model_name}' for agent {agent_config.slug}"
        )

    provider_type_str = (
        effective_model_name.split(":")[0] if ":" in effective_model_name else "openai"
    )
    normalized_type = provider_type_str.lower()
    provider_type_stmt = await session.exec(
        select(LLMProviderType).where(
            func.lower(LLMProviderType.name) == normalized_type
        )
    )
    provider_type = provider_type_stmt.one_or_none()
    if not provider_type:
        logger.warning(
            f"Unknown provider type '{provider_type_str}' in model '{effective_model_name}'"
        )
        return effective_model_name, None, None, None
    provider_type_name = provider_type.name

    provider: UserLLMProvider | None = None

    if settings and settings.provider_id:
        provider_result = await session.exec(
            select(UserLLMProvider).where(
                UserLLMProvider.id == settings.provider_id,
                UserLLMProvider.is_enabled,
            )
        )
        provider_row = provider_result.one_or_none()
        provider = (
            provider_row[0]
            if provider_row and not isinstance(provider_row, UserLLMProvider)
            else provider_row
        )
        if provider:
            logger.debug(
                f"Using explicit provider '{provider.name}' for agent {agent_config.slug}"
            )

    if not provider:
        default_result = await session.exec(
            select(UserLLMProvider).where(
                UserLLMProvider.user_id == user_id,
                UserLLMProvider.provider_type == provider_type_name,
                UserLLMProvider.is_default,
                UserLLMProvider.is_enabled,
            )
        )
        provider_row = default_result.one_or_none()
        provider = (
            provider_row[0]
            if provider_row and not isinstance(provider_row, UserLLMProvider)
            else provider_row
        )
        if provider:
            logger.debug(
                f"Using default provider '{provider.name}' for agent {agent_config.slug}"
            )

    if not provider:
        logger.debug(
            f"No user provider for agent {agent_config.slug}, using env vars"
        )
        return effective_model_name, None, provider_type_name, None

    api_key = decrypt_api_key(provider.api_key_encrypted)
    base_url = provider.base_url
    logger.debug(
        f"Resolved credentials: api_key=***{api_key[-4:] if api_key else 'None'}, base_url={base_url}"
    )
    return effective_model_name, api_key, provider_type_name, base_url


def create_model_with_credentials(
    model_name: str,
    api_key: str | None,
    provider_type: str | None,
    base_url: str | None = None,
) -> Any:
    """
    Create a PydanticAI model with user credentials.

    For openai_compatible providers, always creates an OpenAIProvider even
    without an API key — some servers (Ollama, local vLLM) don't need one,
    and PydanticAI doesn't recognize "openai_compatible" as a provider prefix.
    """
    model_id = model_name.split(":", 1)[1] if ":" in model_name else model_name
    normalized_type = provider_type.lower() if provider_type else ""

    if normalized_type == OPENAI_COMPATIBLE:
        compat_provider = OpenAIProvider(
            api_key=api_key or "not-needed",
            base_url=base_url,
        )
        return OpenAIChatModel(model_id, provider=compat_provider)

    if not api_key:
        return model_name

    if normalized_type == OPENAI:
        openai_provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        return OpenAIChatModel(model_id, provider=openai_provider)

    if normalized_type == ANTHROPIC:
        anthropic_provider = AnthropicProvider(api_key=api_key, base_url=base_url)
        return AnthropicModel(model_id, provider=anthropic_provider)

    if normalized_type == GOOGLE:
        google_provider = GoogleProvider(api_key=api_key)
        return GoogleModel(model_id, provider=google_provider)

    logger.warning(f"Unknown provider type '{provider_type}', using model name directly")
    return model_name


async def get_agent_instance(
    session: AsyncSession,
    slug: str,
) -> Agent[Any, Any] | None:
    """
    Get basic agent instance from database AgentConfig (no tools).

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Uses the model_name and system_prompt from AgentConfig.

    For agents with A2A tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"
        agent = Agent(config.model_name, system_prompt=system_prompt)
        logger.debug(
            f"Instantiated database agent: {config.slug} with model {config.model_name}"
        )
        return agent

    return None


async def get_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
    room_id: uuid.UUID | None = None,
) -> Agent[AgentDeps, str] | None:
    """
    Get agent instance with A2A and AG-UI tools enabled.
    Looks up the agent config,
    optionally resolves per-user credentials,
    constructs the PydanticAI Agent with with AgentDeps as deps_type,
    and registers:
        request_agent_assistance tool if enable_a2a_tool is True
        emit_ui_component tool if enable_ag_ui_tool is True
    TODO: refactor for more specific tool policies
    TODO: apply room-specific agent settings when available
    """
    config = await get_agent_config(session, slug)

    if not config or not config.is_enabled:
        return None

    system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

    if user_id:
        effective_model_name, api_key, provider_type, base_url = await resolve_user_credentials(
            session, user_id, config
        )
        model = create_model_with_credentials(
            effective_model_name, api_key, provider_type, base_url
        )
        logger.debug(
            f"Resolved credentials for agent {config.slug}: "
            f"model={effective_model_name}, has_api_key={api_key is not None}, base_url={base_url}"
        )
    else:
        model = config.model_name
        effective_model_name = config.model_name

    tools: list[Any] = []
    if enable_a2a_tool:
        tools.append(request_agent_assistance)
    if enable_ag_ui_tool:
        tools.append(emit_ui_component)

    agent: Agent[AgentDeps, str] = Agent(
        model,
        system_prompt=system_prompt,
        tools=tools,
        deps_type=AgentDeps,
    )

    # TODO: Apply room-specific agent settings (prompt/tool policy) when available.
    _ = room_id

    logger.debug(
        f"Instantiated agent {config.slug} with model {effective_model_name} "
        f"and {len(tools)} tool(s)"
    )
    return agent
