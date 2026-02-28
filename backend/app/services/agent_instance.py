from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import decrypt_api_key
from app.models import (
    LLMProviderType,
    UserAccessProvider,
    UserAgentConfig,
)
from app.services.agent_tools import (
    AgentDeps,
    emit_ui_component,
    request_agent_assistance,
)
from app.services.logfire_client import ServiceLogfire
from app.services.prompt_runtime_resolver import (
    ResolvedPromptRuntimeConfig,
    resolve_effective_prompt_runtime_config_for_room,
)

logger = logging.getLogger(__name__)
SERVICE_ID = "agent_instance"
logfire = ServiceLogfire(SERVICE_ID)


def _get(cfg: Any, *candidates: str) -> Any:
    """Safely fetch first non-empty candidate from object attrs or mapping keys."""
    for key in candidates:
        if hasattr(cfg, key):
            val = getattr(cfg, key)
            if val not in (None, ""):
                return val
        if isinstance(cfg, Mapping) and key in cfg:
            val = cfg.get(key)
            if val not in (None, ""):
                return val
    return None


def _resolve_provider_api_key(uap: Any) -> str | None:
    """
    Resolve API key from provider row, decrypting Fernet values when needed.

    Accepts either `api_key` or legacy `api_key_encrypted` attributes.
    """
    raw_key = _get(uap, "api_key", "api_key_encrypted")
    if not raw_key:
        return None

    raw_key_str = str(raw_key).strip()
    if not raw_key_str:
        return None

    # Fernet tokens generally start with this prefix; try decrypt first.
    if raw_key_str.startswith("gAAAA"):
        try:
            return decrypt_api_key(raw_key_str)
        except Exception:
            logger.warning(
                "[AGENT_INSTANCE._resolve_provider_api_key] provider_id=%s failed_fallback_decrypt",
                getattr(uap, "id", None),
            )

    # If already plaintext, pass through as-is.
    return raw_key_str


def _masked_key_suffix(api_key: str | None) -> str:
    """Return a non-sensitive key marker for debugging."""
    if not api_key:
        return "none"
    tail_len = 4 if len(api_key) >= 4 else len(api_key)
    return f"***{api_key[-tail_len:]}"


def _normalize_request_limit(value: Any) -> int:
    if isinstance(value, int) and value > 0:
        return value
    return 10


def _log_runtime_resolution(
    *,
    slug: str,
    room_id: uuid.UUID | None,
    config: UserAgentConfig,
    resolved: ResolvedPromptRuntimeConfig,
) -> None:
    payload = resolved.payload
    provenance = resolved.provenance
    logfire.info(
        "agent.runtime_config_resolved",
        agent_slug=slug,
        room_id=str(room_id) if room_id else None,
        prompt_config_id=str(getattr(config, "prompt_config_id", None) or ""),
        prompt_config_version_policy=getattr(config, "prompt_config_version_policy", None),
        prompt_config_version_number=getattr(config, "prompt_config_version_number", None),
        model_name=payload.get("model_name"),
        user_access_provider=str(payload.get("user_access_provider") or ""),
        max_tool_iterations=_normalize_request_limit(payload.get("max_tool_iterations")),
        model_name_source=provenance.get("model_name"),
        system_prompt_source=provenance.get("system_prompt"),
        custom_system_prompt_source=provenance.get("custom_system_prompt"),
        instructions_source=provenance.get("instructions"),
        tool_config_source=provenance.get("tool_config"),
        user_access_provider_source=provenance.get("user_access_provider"),
        max_tool_iterations_source=provenance.get("max_tool_iterations"),
    )


def _attach_runtime_resolution_metadata(
    *,
    agent: Agent[Any, Any],
    resolved: ResolvedPromptRuntimeConfig,
) -> None:
    setattr(agent, "_runtime_prompt_payload", resolved.payload)
    setattr(agent, "_runtime_prompt_provenance", resolved.provenance)
    setattr(
        agent,
        "_runtime_request_limit",
        _normalize_request_limit(resolved.payload.get("max_tool_iterations")),
    )

async def get_user_agent_config_by_slug(
    *, session: AsyncSession, slug: str
) -> UserAgentConfig | None:
    """Get user agent configuration from database by slug."""
    result = await session.exec(
        select(UserAgentConfig).where(UserAgentConfig.slug == slug)
    )
    return result.first()


async def get_user_agent_config_by_id(
    *, session: AsyncSession, agent_id: uuid.UUID
) -> UserAgentConfig | None:
    """get user agent config from db by id"""
    return await session.get(UserAgentConfig, agent_id)


async def get_user_agent_config_provider_type_name_for_model_concat_by_slug(
    *, session: AsyncSession, slug: str
) -> Any | None:
    """get the provider type name for a model based on the slug of the user agent config which is calling that model"""
    stmt = (
        select(LLMProviderType.name)
        .select_from(UserAgentConfig)
        .join(LLMProviderType, UserAgentConfig.provider_type == LLMProviderType.id)
        .where(UserAgentConfig.slug == slug)
    )
    result = await session.exec(stmt)
    return result.first()


async def get_user_agent_config_provider_type_name_for_model_concat_by_user_agent_config_id(
    *, session: AsyncSession, agent_id: uuid.UUID
) -> Any | None:
    """get the provider type name for a model based on the id of the user agent config which is calling that model"""
    stmt = (
        select(LLMProviderType.name)
        .select_from(UserAgentConfig)
        .join(LLMProviderType, UserAgentConfig.provider_type == LLMProviderType.id)
        .where(UserAgentConfig.id == agent_id)
    )
    result = await session.exec(stmt)
    return result.first()


async def get_agent_instance(
    session: AsyncSession,
    slug: str,
    user_id: uuid.UUID | None = None,
    room_id: uuid.UUID | None = None,
) -> Agent[Any, Any] | None:
    """
    Get basic agent instance from database UserAgentConfig (no tools).

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Uses the model_name and system_prompt from UserAgentConfig.

    For agents with A2A tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)
    if not config:
        logger.error("[AGENT_INSTANCE_FAILURE.get_agent_instance] -NO CONFIG")
        return None

    resolved = await resolve_effective_prompt_runtime_config_for_room(
        session=session,
        agent_config=config,
        room_id=room_id,
    )
    effective = resolved.payload
    _log_runtime_resolution(slug=slug, room_id=room_id, config=config, resolved=resolved)

    model_name = _get(effective, "model_name", "model")
    if not model_name:
        logger.error(
            "[AGENT_INSTANCE.get_agent_instance] slug=%s missing model/model_name; cannot instantiate Agent",
            slug,
        )
        return None

    provider_type_name = await get_user_agent_config_provider_type_name_for_model_concat_by_slug(
        session=session, slug=slug
    )
    model_final_form = create_model_subclass_with_credentials(
        model_name=model_name,
        api_key=None,
        provider_type=provider_type_name,
        base_url=None,
    )

    system_prompt = _get(effective, "custom_system_prompt", "system_prompt") or (
        f"You are {getattr(config, 'name', slug)}. {getattr(config, 'description', '')}".strip()
    )

    agent_kwargs: dict[str, Any] = {
        "model": model_final_form,
        "system_prompt": system_prompt,
    }
    agent_kwargs = {k: v for k, v in agent_kwargs.items() if v is not None}
    agent = Agent(**agent_kwargs)
    _attach_runtime_resolution_metadata(agent=agent, resolved=resolved)
    return agent


async def get_agent_config(session: AsyncSession, slug: str) -> UserAgentConfig | None:
    """Fetch enabled agent config by slug or return None if missing/disabled."""
    result = await session.exec(
        select(UserAgentConfig).where(UserAgentConfig.slug == slug)
    )
    config = result.first()
    if not config or getattr(config, "is_enabled", True) is False:
        logger.info(
            "[AGENT_INSTANCE.get_agent_config] slug=%s missing or disabled (config=%s, is_enabled=%s)",
            slug,
            "None" if config is None else "present",
            getattr(config, "is_enabled", "?") if config is not None else "n/a",
        )
        return None
    return config


async def get_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
    room_id: uuid.UUID | None = None,
) -> Agent[Any, Any] | None:
    """
    Build a PydanticAI `Agent` configured from `UserAgentConfig`, wiring optional tools.

    Parameters
    ----------
    session : AsyncSession
        Database session for fetching configuration and (future) credential lookup.
    slug : str
        Agent slug to load.
    user_id : uuid.UUID | None
        Optional user whose credentials may tailor the model (not yet used).
    enable_a2a_tool : bool
        When True, include `request_agent_assistance` tool for agent-to-agent calls.
    enable_ag_ui_tool : bool
        When True, include `emit_ui_component` tool for UI emission.
    room_id : uuid.UUID | None
        Room context, reserved for future room-scoped settings.

    Returns
    -------
    Agent | None
        An instantiated Agent ready for `run_stream` with `deps_type=AgentDeps`, or None
        if the config is missing/disabled.
    """
    config = await get_agent_config(session, slug)
    logger.info(
        "[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s config_present=%s",
        slug,
        config is not None,
    )

    if not config:
        logger.error(
            "[AGENT_INSTANCE_FAILURE.get_agent_instance_with_tools] -NO CONFIG"
        )
        return None

    resolved = await resolve_effective_prompt_runtime_config_for_room(
        session=session,
        agent_config=config,
        room_id=room_id,
    )
    effective = resolved.payload
    _log_runtime_resolution(slug=slug, room_id=room_id, config=config, resolved=resolved)

    model_name = _get(effective, "model_name", "model")
    if not model_name:
        logger.error(
            "[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s missing model/model_name; cannot instantiate Agent",
            slug,
        )
        return None

    # user_agent_configs (UserAgentConfig) has user_access_provider and owner_id.
    # "user_agent_configs_owner_id_fkey" FOREIGN KEY (owner_id) REFERENCES "user"(id)
    # user_access_provider (UserAccessProvider) has "ix_user_access_provider_user_id" btree (user_id)
    # user_access_provider (UserAccessProvider) has base_url, is_enabled, user_id, and api_key.
    # we need to check if: UserAgentConfig has owner_id == user_id of user making the request to use the UAC.
    # we need to check the UserAccessProvider specified in the UserAgentConfig and validate:
    # - owner_id.UserAgentConfig in (user_id or owner_id).user_access_provider
    # - user_access_provider.UserAgentConfig is_enabled;
    # that's how we get to:
    base_url = None
    api_key = None

    # Fetch UserAccessProvider if configured for this agent.
    effective_uap_id = _get(effective, "user_access_provider")
    if effective_uap_id and user_id:
        uap_stmt = (
            select(UserAccessProvider)
            .where(UserAccessProvider.id == effective_uap_id)
            .where(UserAccessProvider.is_enabled)
            .where(UserAccessProvider.user_id == user_id)
        )
        uap_result = await session.exec(uap_stmt)
        uap = uap_result.first()
        if uap:
            base_url = uap.base_url
            api_key = _resolve_provider_api_key(uap)
            logger.debug(
                "[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s using UserAccessProvider id=%s has_api_key=%s",
                slug,
                effective_uap_id,
                bool(api_key),
            )
        else:
            logger.warning(
                "[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s user_access_provider not found or not enabled for user_id=%s",
                slug,
                user_id,
            )

    provider_type_name = (
        await get_user_agent_config_provider_type_name_for_model_concat_by_slug(
            session=session, slug=slug
        )
    )
    logger.debug(
        "[AGENT_INSTANCE.probe_credentials] slug=%s provider_type=%s has_api_key=%s key_suffix=%s base_url=%s",
        slug,
        provider_type_name,
        bool(api_key),
        _masked_key_suffix(api_key),
        base_url,
    )
    model_final_form = create_model_subclass_with_credentials(
        model_name=model_name,
        api_key=api_key,
        provider_type=provider_type_name,
        base_url=base_url,
    )

    system_prompt = _get(effective, "custom_system_prompt", "system_prompt") or (
        f"You are {getattr(config, 'name', slug)}. {getattr(config, 'description', '')}".strip()
    )


    # this might be where we pass instructions, pass skills, etc - agent_personas/archetypes?
    # Future extension: pull model/base_url/provider overrides from user-specific credentials.
    # Keep the hook explicit so new credential sources can slot in without rewriting the caller.

    tools: list[Any] = []
    if enable_a2a_tool:
        tools.append(request_agent_assistance)
    if enable_ag_ui_tool:
        tools.append(emit_ui_component)

    agent_kwargs: dict[str, Any] = {
        "model": model_final_form,
        "system_prompt": system_prompt,
        "deps_type": AgentDeps,
        "tools": tools or None,
        # Optional extras if present on config (each getattr is resilient to missing attrs):
        "toolsets": getattr(config, "toolsets", None),
        "builtintools": getattr(config, "builtin_tools", None),
        "preparetools": getattr(config, "prepare_tools", None),
        "prepareoutputtools": getattr(config, "prepare_output_tools", None),
        # Extension points:
        # - tool_config (JSON): parse and map to concrete callables/toolsets here.
        # - deps_config (JSON): attach additional deps fields or alter AgentDeps subtype.
        # - capabilities/metadata: feed into system_prompt or Agent metadata when supported.
    }
    # Drop None values so Agent uses library defaults and ignores unused columns gracefully.
    agent_kwargs = {k: v for k, v in agent_kwargs.items() if v is not None}

    agent = Agent(**agent_kwargs)
    _attach_runtime_resolution_metadata(agent=agent, resolved=resolved)
    logger.debug(
        "[AGENT_INSTANCE.get_agent_instance_with_tools] instantiated slug=%s model=%s tools=%d a2a=%s ag_ui=%s",
        slug,
        model_name,
        len(tools),
        enable_a2a_tool,
        enable_ag_ui_tool,
    )
    return agent

def create_model_subclass_with_credentials(
    model_name: str,
    api_key: str | None,
    provider_type: str | None,
    base_url: str | None = None,
) -> Any:
    """
    Create a PydanticAI model with user credentials.

    Provider values are expected from the DB as one of:
    openai, anthropic, openai_compatible, custom, empty, google.
    """
    normalized_type = (provider_type or "").strip().lower()

    if normalized_type in {"", "empty", "openai"}:
        if api_key or base_url:
            return OpenAIChatModel(
                model_name,
                provider=OpenAIProvider(
                    api_key=api_key or "not-needed",
                    base_url=base_url,
                ),
            )
        return model_name

    if normalized_type in {"openai_compatible", "custom"}:
        return OpenAIChatModel(
            model_name,
            provider=OpenAIProvider(
                api_key=api_key, # or "not-needed",
                base_url=base_url,
            ),
        )

    if normalized_type == "anthropic":
        if api_key:
            return AnthropicModel(
                model_name,
                provider=AnthropicProvider(api_key=api_key, base_url=base_url),
            )
        return f"anthropic:{model_name}"

    if normalized_type == "google":
        if api_key:
            return GoogleModel(
                model_name,
                provider=GoogleProvider(api_key=api_key),
            )
        return f"google:{model_name}"

    logger.warning(
        "[AGENT_INSTANCE.create_model_subclass_with_credentials] unknown provider_type=%s; using raw model_name",
        provider_type,
    )
    return model_name


# reference function from Pydantic-ai for constructing a custom provider and a custom model profile.

# from pydantic_ai import Agent
# from pydantic_ai.models.openai import OpenAIChatModel
# from pydantic_ai.providers.openai import OpenAIProvider

# model = OpenAIChatModel(
#     'model_name',
#     provider=OpenAIProvider(
#         base_url='https://<openai-compatible-api-endpoint>', api_key='your-api-key'
#     ),
# )
# agent = Agent(model)
