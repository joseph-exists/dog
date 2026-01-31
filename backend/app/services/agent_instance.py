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
    UserAgentConfig,
)

"""
OpenAIProvider example:
model = OpenAIChatModel('gpt-5', provider=OpenAIProvider(api_key='your-api-key'))
agent = Agent(model)

Anthropic example:
model = AnthropicModel(
    'claude-sonnet-4-5', provider=AnthropicProvider(api_key='your-api-key')
)
agent = Agent(model)

OpenAICompatible example:
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://<openai-compatible-api-endpoint>', api_key='your-api-key'
    ),
)
agent = Agent(model)
...


Moonshot: not yet implemented, but k2 is awesome
model = OpenAIChatModel(
    'kimi-k2-0711-preview',
    provider=MoonshotAIProvider(api_key='your-moonshot-api-key'),
)
agent = Agent(model)

Ollama: (not yet implemented, future reference only)
ollama_model = OpenAIChatModel(
    model_name='gpt-oss:20b',
    provider=OllamaProvider(base_url='http://localhost:11434/v1'), 
)
agent = Agent(ollama_model, output_type=CityLocation)

# josep TODO: review httpx.AsyncClient for Anthropic
# josep TODO: review HFProviders

"""


# from app.services.agent_tools import (
#    AgentDeps,
#    emit_ui_component,
#    request_agent_assistance,
# )

logger = logging.getLogger(__name__)

# OPENAI = "openai"
# OPENAI_COMPATIBLE = "openai_compatible"
# ANTHROPIC = "anthropic"
# GOOGLE = "google"


async def get_agent_config(session: AsyncSession, slug: str) -> UserAgentConfig | None:
    """Get user agent configuration from database by slug."""
    return await session.get(UserAgentConfig, slug)

async def get_user_agent_config_by_id(*, session: AsyncSession, agent_id: uuid.UUID) -> UserAgentConfig | None:
    """get user agent config from db by id"""
    return await session.get(UserAgentConfig, agent_id)

"""NEW FOR VALIDATION"""

## notes:
## provider_type in user_agent_configs looks like (openai, openai_compatible, anthropic, google, etc)


async def get_agent_instance(
    session: AsyncSession,
    slug: str,
) -> Agent[Any, Any] | None:
    """
    Get agent instance from database UserAgentConfig (no tools).

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Maps all available UserAgentConfig fields to Agent constructor parameters.

    For agents with A2A tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        # Build system_prompt as before
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

        # Map UserAgentConfig fields to Agent constructor kwargs
        agent_kwargs = {
            "model": getattr(config, "model_name", None),
            "system_prompt": system_prompt,
            "name": getattr(config, "name", None),
            # Output config (assume output_type field like str or Pydantic model str)
            "outputtype": getattr(config, "output_type", "str"),
            # Instructions (assume list of str)
            "instructions": getattr(config, "instructions", None),
            # Model settings (assume ModelSettings JSON/str field)
            "modelsettings": getattr(config, "model_settings", None),
            # Retries
            "retries": getattr(config, "retries", 1),
            "outputretries": getattr(config, "output_retries", None),
            # End strategy (assume enum str like "early")
            "endstrategy": getattr(config, "end_strategy", "early"),
            # Instrumentation
            "instrument": getattr(config, "instrument", None),
            # Validation context (assume callable or dict)
            "validationcontext": getattr(config, "validation_context", None),
            # Deps type (advanced, assume str or type)
            "depstype": getattr(config, "deps_type", None),
            # History processors (assume list)
            "historyprocessors": getattr(config, "history_processors", None),
            # Event stream handler (assume callable field)
            "eventstreamhandler": getattr(config, "event_stream_handler", None),
            # Defer model check
            "defermodelcheck": getattr(config, "defer_model_check", False),
            # NOTE: Skipping tools/toolsets/builtintools/prepare* as docstring excludes tools
            # Add if config has tool-related fields, but set to empty/None here
            "tools": None,
            "toolsets": None,
            "builtintools": None,
            "preparetools": None,
            "prepareoutputtools": None,
        }

        # Filter out None values (Agent handles defaults)
        agent_kwargs = {k: v for k, v in agent_kwargs.items() if v is not None}

        agent = Agent(**agent_kwargs)
        logger.debug(
            f"instantiated new buddy: {config.slug} with settings for {config.model_name}"
        )
        return agent

    return None

async def get_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
) -> Agent[Any, Any] | None:
    """
    Get agent instance from database UserAgentConfig with tools (A2A).

    Instantiates a PydanticAI Agent using the configuration stored in the database,
    including tools/toolsets from UserAgentConfig.
    Maps all available UserAgentConfig fields to Agent constructor parameters.

    For basic agents without tools, use get_agent_instance() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        # Build system_prompt as before
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

        # Map UserAgentConfig fields to Agent constructor kwargs (full set)
        agent_kwargs = {
            "model": getattr(config, "model_name", None),
            "system_prompt": system_prompt,
            "name": getattr(config, "name", None),
            # Output config
            "outputtype": getattr(config, "output_type", "str"),
            # Instructions
            "instructions": getattr(config, "instructions", None),
            # Model settings
            "modelsettings": getattr(config, "model_settings", None),
            # Retries
            "retries": getattr(config, "retries", 1),
            "outputretries": getattr(config, "output_retries", None),
            # End strategy
            "endstrategy": getattr(config, "end_strategy", "early"),
            # Instrumentation
            "instrument": getattr(config, "instrument", None),
            # Validation
            "validationcontext": getattr(config, "validation_context", None),
            # Deps type
            "depstype": getattr(config, "deps_type", None),
            # History processors
            "historyprocessors": getattr(config, "history_processors", None),
            # Event stream handler
            "eventstreamhandler": getattr(config, "event_stream_handler", None),
            # Defer model check
            "defermodelcheck": getattr(config, "defer_model_check", False),
            # Tools/Toolsets (now included for A2A)
            "tools": getattr(config, "tools", None),  # Assume list of Tool/ToolFunc
            "toolsets": getattr(config, "toolsets", None),  # List of AbstractToolset/ToolsetFunc
            "builtintools": getattr(config, "builtin_tools", None),
            "preparetools": getattr(config, "prepare_tools", None),
            "prepareoutputtools": getattr(config, "prepare_output_tools", None),
        }

        # Filter out None values (Agent uses defaults)
        agent_kwargs = {k: v for k, v in agent_kwargs.items() if v is not None}

        agent = Agent(**agent_kwargs)
        logger.debug(
            f"Instantiated database agent with tools: {config.slug} "
            f"with model {config.model_name}"
        )
        return agent

    return None

async def get_abstract_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
) -> AbstractAgent[Any, Any] | None:
    """
    Get AbstractAgent instance from database UserAgentConfig with tools (A2A).

    Instantiates a PydanticAI AbstractAgent using the configuration stored in the database,
    including tools/toolsets from UserAgentConfig.
    Maps all available UserAgentConfig fields to AbstractAgent-compatible parameters.

    AbstractAgent requires subclass implementation (e.g., Agent/WrapperAgent).
    For concrete Agent with tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        # Build system_prompt as before (for docs/instructions fallback)
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

        # Map UserAgentConfig fields to AbstractAgent properties/kwargs
        # Note: AbstractAgent has no direct constructor; set properties post-instantiation
        # Assume instantiation via concrete subclass like Agent (full mapping)
        agent_kwargs = {
            "model": getattr(config, "model_name", None),
            "system_prompt": system_prompt,
            "name": getattr(config, "name", None),
            # Output config
            "outputtype": getattr(config, "output_type", "str"),
            # Instructions
            "instructions": getattr(config, "instructions", None),
            # Model settings
            "modelsettings": getattr(config, "model_settings", None),
            # Retries
            "retries": getattr(config, "retries", 1),
            "outputretries": getattr(config, "output_retries", None),
            # End strategy
            "endstrategy": getattr(config, "end_strategy", "early"),
            # Instrumentation
            "instrument": getattr(config, "instrument", None),
            # Validation
            "validationcontext": getattr(config, "validation_context", None),
            # Deps type
            "depstype": getattr(config, "deps_type", None),
            # History processors
            "historyprocessors": getattr(config, "history_processors", None),
            # Event stream handler
            "eventstreamhandler": getattr(config, "event_stream_handler", None),
            # Defer model check
            "defermodelcheck": getattr(config, "defer_model_check", False),
            # Tools/Toolsets (included for A2A)
            "tools": getattr(config, "tools", None),
            "toolsets": getattr(config, "toolsets", None),
            "builtintools": getattr(config, "builtin_tools", None),
            "preparetools": getattr(config, "prepare_tools", None),
            "prepareoutputtools": getattr(config, "prepare_output_tools", None),
        }

        # Filter out None values
        agent_kwargs = {k: v for k, v in agent_kwargs.items() if v is not None}

        # Instantiate concrete Agent (AbstractAgent lacks __init__; use subclass)
        agent: AbstractAgent[Any, Any] = Agent(**agent_kwargs)
        
        # Optional: Post-instantiation property sets if config has extras
        # agent.model = ... (already handled via kwargs)

        logger.debug(
            f"Instantiated AbstractAgent with tools: {config.slug} "
            f"with model {config.model_name}"
        )
        return agent

    return None

async def get_wrapper_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
) -> WrapperAgent[Any, Any] | None:
    """
    Get WrapperAgent instance from database UserAgentConfig with tools (A2A).

    Instantiates a PydanticAI WrapperAgent wrapping a base Agent,
    using configuration stored in the database including tools/toolsets.
    Maps UserAgentConfig fields to inner Agent constructor, then wraps it.

    WrapperAgent proxies all properties/methods to wrapped agent.
    For standard Agent with tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        # Build system_prompt as before
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

        # Map UserAgentConfig fields to inner Agent kwargs (full set)
        inner_agent_kwargs = {
            "model": getattr(config, "model_name", None),
            "system_prompt": system_prompt,
            "name": getattr(config, "name", None),
            # Output config
            "outputtype": getattr(config, "output_type", "str"),
            # Instructions
            "instructions": getattr(config, "instructions", None),
            # Model settings
            "modelsettings": getattr(config, "model_settings", None),
            # Retries
            "retries": getattr(config, "retries", 1),
            "outputretries": getattr(config, "output_retries", None),
            # End strategy
            "endstrategy": getattr(config, "end_strategy", "early"),
            # Instrumentation
            "instrument": getattr(config, "instrument", None),
            # Validation
            "validationcontext": getattr(config, "validation_context", None),
            # Deps type
            "depstype": getattr(config, "deps_type", None),
            # History processors
            "historyprocessors": getattr(config, "history_processors", None),
            # Event stream handler
            "eventstreamhandler": getattr(config, "event_stream_handler", None),
            # Defer model check
            "defermodelcheck": getattr(config, "defer_model_check", False),
            # Tools/Toolsets (included for A2A)
            "tools": getattr(config, "tools", None),
            "toolsets": getattr(config, "toolsets", None),
            "builtintools": getattr(config, "builtin_tools", None),
            "preparetools": getattr(config, "prepare_tools", None),
            "prepareoutputtools": getattr(config, "prepare_output_tools", None),
        }

        # Filter out None values
        inner_agent_kwargs = {k: v for k, v in inner_agent_kwargs.items() if v is not None}

        # Create inner base Agent
        inner_agent = Agent(**inner_agent_kwargs)

        # Instantiate WrapperAgent wrapping the inner agent
        wrapper_agent = WrapperAgent(inner_agent)

        logger.debug(
            f"Instantiated WrapperAgent with tools: {config.slug} "
            f"wrapping model {config.model_name}"
        )
        return wrapper_agent

    return None



# async def get_agent_instance_with_tools(
#     session: AsyncSession,
#     slug: str,
#     user_id: uuid.UUID | None = None,
#     enable_a2a_tool: bool = False,
#     enable_ag_ui_tool: bool = False,
#     room_id: uuid.UUID | None = None,
# ) -> Agent[AgentDeps, str] | None:
#     """
#     Get agent instance with A2A and AG-UI tools enabled.
#     Looks up the agent config,
#     optionally resolves per-user credentials,
#     constructs the PydanticAI Agent with with AgentDeps as deps_type,
#     and registers:
#         request_agent_assistance tool if enable_a2a_tool is True
#         emit_ui_component tool if enable_ag_ui_tool is True
#     TODO: refactor for more specific tool policies
#     TODO: apply room-specific agent settings when available
#     """
#     config = await get_agent_config(session, slug)

#     if not config or not config.is_enabled:
#         return None

#     system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

#     if user_id:
#         effective_model_name, api_key, provider_type, base_url = await resolve_user_credentials(
#             session, user_id, config
#         )
#         model = create_model_with_credentials(
#             effective_model_name, api_key, provider_type, base_url
#         )
#         logger.debug(
#             f"Resolved credentials for agent {config.slug}: "
#             f"model={effective_model_name}, has_api_key={api_key is not None}, base_url={base_url}"
#         )
#     else:
#         model = config.model_name
#         effective_model_name = config.model_name

#     tools: list[Any] = []
#     if enable_a2a_tool:
#         tools.append(request_agent_assistance)
#     if enable_ag_ui_tool:
#         tools.append(emit_ui_component)

#     agent: Agent[AgentDeps, str] = Agent(
#         model,
#         system_prompt=system_prompt,
#         tools=tools,
#         deps_type=AgentDeps,
#     )

#     # TODO: Apply room-specific agent settings (prompt/tool policy) when available.
#     _ = room_id

#     logger.debug(
#         f"Instantiated agent {config.slug} with model {effective_model_name} "
#         f"and {len(tools)} tool(s)"
#     )
#     return agent
