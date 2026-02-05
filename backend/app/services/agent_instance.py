from __future__ import annotations

import logging
import uuid
from collections.abc import Mapping
from typing import Any

from pydantic_ai import Agent
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models import (
    UserAgentConfig,
    LLMProviderType,
    LLMProviderTypePublic,
)
from app.services.agent_tools import (
    AgentDeps,
    emit_ui_component,
    request_agent_assistance,
)

logger = logging.getLogger(__name__)


async def get_user_agent_config_by_slug(*, session: AsyncSession, slug: str) -> UserAgentConfig | None:
    """Get user agent configuration from database by slug."""
    result = await session.exec(select(UserAgentConfig).where(UserAgentConfig.slug == slug))
    return result.first()

async def get_user_agent_config_by_id(*, session: AsyncSession, agent_id: uuid.UUID) -> UserAgentConfig | None:
    """get user agent config from db by id"""
    return await session.get(UserAgentConfig, agent_id)

async def get_user_agent_config_provider_type_name_for_model_concat_by_slug(*, session: AsyncSession, slug: str) -> Any | None:
    """get the provider type name for a model based on the slug of the user agent config which is calling that model"""
    stmt = (
        select(LLMProviderType.name)
        .select_from(UserAgentConfig)
        .join(LLMProviderType, UserAgentConfig.provider_type == LLMProviderType.id)
        .where(UserAgentConfig.slug == slug)
    )
    result = await session.exec(stmt)
    return result.first()

async def get_user_agent_config_provider_type_name_for_model_concat_by_user_agent_config_id(*, session: AsyncSession, agent_id: uuid.UUID) -> Any| None:
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
) -> Agent[Any, Any] | None:
    """
    Get basic agent instance from database UserAgentConfig (no tools).

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Uses the model_name and system_prompt from UserAgentConfig.

    For agents with A2A tools, use get_agent_instance_with_tools() instead.
    """
    config: Any = await get_user_agent_config_by_slug(session, slug)
    return config


async def get_agent_config(session: AsyncSession, slug: str) -> UserAgentConfig | None:
    """Fetch enabled agent config by slug or return None if missing/disabled."""
    result = await session.exec(select(UserAgentConfig).where(UserAgentConfig.slug == slug))
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
    enable_a2a_tool: bool = True,
    enable_ag_ui_tool: bool = True,
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
        logger.error("[AGENT_INSTANCE_FAILURE.get_agent_instance_with_tools] -NO CONFIG")
        return None

    # Minimal, safe extraction: ignore unknown/extra columns to avoid AttributeError as
    # the UserAgentConfig schema grows. Use getattr with defaults so missing columns are fine.
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

    model_name = _get(config, "model_name", "model")
    if not model_name:
        logger.error(
            "[AGENT_INSTANCE.get_agent_instance_with_tools] slug=%s missing model/model_name; cannot instantiate Agent",
            config,
            slug,
        )
        return None

    provider_type_name = await get_user_agent_config_provider_type_name_for_model_concat_by_slug(
        session=session, slug=slug
    )
    # Prefix model with provider type when needed (pydantic_ai expects provider:model for non-openai providers).
    if provider_type_name and provider_type_name.lower() != "openai":
        model_final_form = f"{provider_type_name}:{model_name}"
    else:
        model_final_form = model_name

    system_prompt = _get(config, "system_prompt", "custom_system_prompt") or (
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
        # pydantic_ai.Agent expects `model` such as:
        # if provider type =  openai, then model by itself is 'fine'
        # if provider type != openai, then we need to pass provider_type_string:model to pydantic as 'model'
        # ie: model = model_name + ':' + (the resolved provider_type)
        # we need to keep this as slip as possible - we will be refactoring much of this in the near future,
        # this is meant to be a performant stopgap with minimal complexity.
        # note: model_final_form might get us through to the next proof - we'll see.
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
    logger.debug(
        "[AGENT_INSTANCE.get_agent_instance_with_tools] instantiated slug=%s model=%s tools=%d a2a=%s ag_ui=%s",
        slug,
        model_name,
        len(tools),
        enable_a2a_tool,
        enable_ag_ui_tool,
    )
    return agent
