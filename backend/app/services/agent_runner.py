"""
Agent Runner Service: Execute agents in room context.

This service:
1. Loads room context via ContextProvider
2. Looks up agent via database AgentConfig
3. Checks participation mode before responding
4. Runs the agent with context
5. Emits room_message.agent event with response
6. Handles errors gracefully
7. Supports Coordinator Pattern for agent orchestration

Participation Modes:
- "always": Agent responds to every message in the room
- "on_mention": Agent responds only when @mentioned (default)
- "manual": Agent only responds when explicitly invoked via API

Coordinator Pattern:
- Agents with is_coordinator=True run FIRST, before participation mode checks
- Coordinators can analyze user intent and @mention specialists
- This enables orchestration where a primary agent routes to others
- Only one coordinator per room is typical, but multiple are allowed

Transaction Management:
- Agent runner receives session from caller
- Does NOT manage its own transaction
- Route handler controls transaction lifecycle
"""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any

from pydantic_ai import Agent, ModelAPIError, RunContext
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.openai import OpenAIProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_api_key
from app.models import (
    AgentConfig,
    LLMProviderType,
    RoomParticipant,
    UserAgentSettings,
    UserLLMProvider,
)
from app.schemas.ag_ui import UIComponent, UIComponentType
from app.services.context_provider import build_room_context
from app.services.event_emitter import (
    emit_agent_internal_message,
    emit_event,
    publish_agent_token,
)

logger = logging.getLogger(__name__)

# =============================================================================
# A2A (Agent-to-Agent) Configuration
# =============================================================================

# Maximum depth of agent-to-agent chains to prevent infinite loops
# Depth 0 = user triggers agent
# Depth 1 = agent triggers another agent
# Depth 2 = that agent triggers yet another agent (max by default)
MAX_A2A_DEPTH = 2


# =============================================================================
# Agent Dependencies (for PydanticAI Tools)
# =============================================================================

@dataclass
class AgentDeps:
    """
    Dependencies passed to agent tools via PydanticAI's RunContext.

    This enables tools to access:
    - Database session for queries
    - Room context for multi-agent coordination
    - Current agent info for self-awareness
    - UI components collector for AG-UI

    Usage in tools:
        async def my_tool(ctx: RunContext[AgentDeps], arg: str) -> str:
            session = ctx.deps.session
            room_id = ctx.deps.room_id
            ...
    """
    session: AsyncSession
    room_id: uuid.UUID
    current_agent_slug: str
    a2a_depth: int = 0
    # AG-UI: Collected UI components (populated by emit_ui_component tool)
    ui_components: list[UIComponent] | None = None

    def __post_init__(self) -> None:
        """Initialize mutable defaults."""
        if self.ui_components is None:
            self.ui_components = []

    def add_ui_component(self, component: UIComponent) -> None:
        """Add a UI component to the collection."""
        if self.ui_components is None:
            self.ui_components = []
        self.ui_components.append(component)


# =============================================================================
# A2A Tool: Request Agent Assistance
# =============================================================================

async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,
    request: str,
) -> str:
    """
    Request another agent's expertise on a specific topic.

    Use this tool when you need specialized help from another agent in the room.
    The target agent will process your request and return their response.

    Args:
        target_agent: The slug or name of the agent to ask (e.g., "DialogueCoach")
        request: Your specific question or request for the agent

    Returns:
        The target agent's response to your request

    Example:
        To ask DialogueCoach for help with dialogue:
        request_agent_assistance("DialogueCoach", "Review this dialogue for naturalness: ...")
    """
    deps = ctx.deps

    # Check A2A depth limit
    if deps.a2a_depth >= MAX_A2A_DEPTH:
        return (
            f"[A2A limit reached] Cannot request assistance from {target_agent} - "
            f"maximum agent chain depth ({MAX_A2A_DEPTH}) exceeded."
        )

    # Prevent self-invocation
    if target_agent.lower() == deps.current_agent_slug.lower():
        return "[Error] Cannot request assistance from yourself."

    # Check if target agent is in the room
    is_in_room, agent_slug, config = await is_agent_in_room(
        deps.session, deps.room_id, target_agent
    )

    if not is_in_room or not agent_slug:
        return (
            f"[Agent not found] '{target_agent}' is not available in this room. "
            f"Check the agent name or ask the user to add them to the room."
        )

    logger.info(
        f"A2A Tool: {deps.current_agent_slug} requesting assistance from {agent_slug} "
        f"(depth {deps.a2a_depth} -> {deps.a2a_depth + 1})"
    )

    # Invoke the target agent (non-streaming for tool response)
    # We use run_agent_for_room (non-streaming) for synchronous tool call
    response = await _run_agent_for_tool_call(
        room_id=deps.room_id,
        agent_slug=agent_slug,
        request=request,
        requesting_agent=deps.current_agent_slug,
        session=deps.session,
        _a2a_depth=deps.a2a_depth + 1,
    )

    if response["success"]:
        return response["content"]
    else:
        return f"[Error from {agent_slug}] {response.get('error', 'Unknown error')}"


async def _run_agent_for_tool_call(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    request: str,
    requesting_agent: str,
    session: AsyncSession,
    _a2a_depth: int,  # Passed for depth tracking, unused to prevent tool recursion
) -> dict[str, Any]:
    """
    Internal function to run an agent for a tool call (non-streaming).

    Unlike run_agent_for_room_streaming, this:
    - Does NOT emit room_message.agent events (response goes back to calling agent)
    - Does NOT publish tokens to Redis
    - Does NOT enable A2A tools on target agent (prevents infinite recursion)
    - Returns response directly to the calling tool

    This enables synchronous A2A communication where Agent A calls Agent B
    and receives the response within the same turn.

    Note: _a2a_depth is passed for tracking but target agents don't get tools
    to prevent tool-call recursion (Agent A → tool → Agent B → tool → Agent A...)
    """
    # Get agent instance
    agent = await get_agent_instance(session, agent_slug)
    if not agent:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Failed to instantiate agent '{agent_slug}'",
        }

    try:
        # Build context for the target agent
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
        )

        # Build prompt with attribution to requesting agent
        prompt = f"@{requesting_agent} is asking for your assistance:\n\n{request}"
        full_prompt = build_agent_prompt(prompt, context, current_agent_slug=agent_slug)

        # Run agent (non-streaming)
        result = await agent.run(full_prompt)

        logger.debug(
            f"A2A Tool: {agent_slug} responded to {requesting_agent} "
            f"({len(result.output)} chars)"
        )

        return {
            "agent_name": agent_slug,
            "content": result.output,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"A2A Tool error: {agent_slug} failed to respond: {e}")
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": str(e),
        }


# =============================================================================
# AG-UI Tool: Emit UI Components
# =============================================================================

def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str:
    """
    Emit a structured UI component to be displayed alongside your response.

    Use this tool to create rich, interactive UI elements that enhance your text response.
    Components will be rendered by the frontend after your message.

    Available component types:
    - "card": Highlighted information card (title, body, variant)
    - "list": Bulleted or numbered list of items
    - "table": Data table with columns and rows
    - "progress": Progress bars for metrics/completion
    - "action_buttons": Clickable action buttons
    - "code": Code blocks with syntax highlighting
    - "quote": Blockquotes for dialogue or excerpts
    - "alert": Info/warning/error notices
    - "collapsible": Expandable content sections
    - "tabs": Tabbed content organization
    - "divider": Visual separator

    Args:
        component_type: The type of UI component to create
        data: Component-specific data (see examples below)
        fallback_text: Text to show if component isn't supported

    Returns:
        Confirmation message

    Examples:
        # Create a character card
        emit_ui_component("card", {
            "title": "Character: Elena",
            "subtitle": "Protagonist",
            "body": "A determined scientist seeking truth...",
            "variant": "highlight",
            "icon": "user"
        })

        # Create a list of suggestions
        emit_ui_component("list", {
            "title": "Suggested Improvements",
            "items": [
                {"label": "Add more conflict", "description": "The scene lacks tension"},
                {"label": "Deepen dialogue", "description": "Characters sound similar"}
            ],
            "ordered": True
        })

        # Create action buttons
        emit_ui_component("action_buttons", {
            "buttons": [
                {"label": "Expand Scene", "action": "expand_scene"},
                {"label": "Generate Dialogue", "action": "generate_dialogue"}
            ],
            "layout": "horizontal"
        })

        # Create a progress display
        emit_ui_component("progress", {
            "title": "Story Completion",
            "items": [
                {"label": "Plot", "value": 75, "color": "blue"},
                {"label": "Characters", "value": 90, "color": "green"},
                {"label": "Dialogue", "value": 45, "color": "yellow"}
            ]
        })

        # Create an alert
        emit_ui_component("alert", {
            "title": "Plot Hole Detected",
            "message": "The timeline inconsistency in chapter 3 needs attention.",
            "variant": "warning"
        })
    """
    component = UIComponent(
        type=component_type,
        data=data,
        fallback_text=fallback_text,
    )

    ctx.deps.add_ui_component(component)

    logger.debug(
        f"AG-UI: Agent {ctx.deps.current_agent_slug} emitted {component_type} component"
    )

    return f"[UI Component Added: {component_type}] Component will be displayed with your response."


# =============================================================================
# Mention Detection
# =============================================================================

def detect_mentions(message: str) -> set[str]:
    """
    Extract @mentions from a message.

    Supports formats:
    - @AgentName (display name with spaces requires quotes or camelCase)
    - @agent-slug (slug format)
    - @"Agent Name" (quoted for names with spaces)

    Returns:
        Set of mentioned names/slugs (lowercase for case-insensitive matching)
    """
    mentions = set()

    # Pattern 1: @"Quoted Name" - names with spaces
    quoted_pattern = r'@"([^"]+)"'
    for match in re.finditer(quoted_pattern, message):
        mentions.add(match.group(1).lower())

    # Pattern 2: @word - simple mentions (alphanumeric, hyphens, underscores)
    # Must not be inside quotes
    simple_pattern = r'@(\w[\w-]*)'
    for match in re.finditer(simple_pattern, message):
        mentions.add(match.group(1).lower())

    return mentions


def is_agent_mentioned(
    message: str,
    agent_slug: str,
    agent_name: str,
) -> bool:
    """
    Check if an agent is mentioned in a message.

    Matches against:
    - Agent slug (e.g., "StoryAdvisor", "story-advisor")
    - Agent display name (e.g., "Story Advisor")

    Case-insensitive matching.
    """
    mentions = detect_mentions(message)

    if not mentions:
        return False

    # Check slug match
    if agent_slug.lower() in mentions:
        return True

    # Check display name match (with and without spaces)
    if agent_name.lower() in mentions:
        return True

    # Check display name without spaces (camelCase mention)
    name_no_spaces = agent_name.replace(" ", "").lower()
    if name_no_spaces in mentions:
        return True

    return False


# =============================================================================
# Agent Resolution and Instantiation
# =============================================================================


async def get_agent_config(session: AsyncSession, slug: str) -> AgentConfig | None:
    """Get agent configuration from database by slug."""
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == slug)
    )
    return result.scalar_one_or_none()


async def resolve_user_credentials(
    session: AsyncSession,
    user_id: uuid.UUID,
    agent_config: AgentConfig,
) -> tuple[str, str | None, LLMProviderType | None, str | None]:
    """
    Resolve user's credentials for an agent.

    Returns:
        Tuple of (effective_model_name, decrypted_api_key, provider_type, base_url)
        - api_key will be None if user has no provider configured (use env vars)
        - base_url will be None for standard providers, set for OpenAI-compatible
    """
    # 1. Check for model override in UserAgentSettings
    settings_result = await session.execute(
        select(UserAgentSettings).where(
            UserAgentSettings.user_id == user_id,
            UserAgentSettings.agent_config_id == agent_config.id,
        )
    )
    settings = settings_result.scalar_one_or_none()

    effective_model_name = agent_config.model_name
    if settings and settings.model_name_override:
        effective_model_name = settings.model_name_override
        logger.debug(
            f"Using model override '{effective_model_name}' for agent {agent_config.slug}"
        )

    # 2. Extract provider type from model name (e.g., "openai:gpt-4o" -> "openai")
    provider_type_str = effective_model_name.split(":")[0] if ":" in effective_model_name else "openai"
    try:
        provider_type = LLMProviderType(provider_type_str)
    except ValueError:
        logger.warning(f"Unknown provider type '{provider_type_str}' in model '{effective_model_name}'")
        return effective_model_name, None, None

    # 3. Find user's provider - first check explicit setting, then default
    provider: UserLLMProvider | None = None

    if settings and settings.provider_id:
        provider_result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.id == settings.provider_id,
                UserLLMProvider.is_enabled,
            )
        )
        provider = provider_result.scalar_one_or_none()
        if provider:
            logger.debug(f"Using explicit provider '{provider.name}' for agent {agent_config.slug}")

    if not provider:
        # Fall back to user's default provider for this type
        default_result = await session.execute(
            select(UserLLMProvider).where(
                UserLLMProvider.user_id == user_id,
                UserLLMProvider.provider_type == provider_type,
                UserLLMProvider.is_default,
                UserLLMProvider.is_enabled,
            )
        )
        provider = default_result.scalar_one_or_none()
        if provider:
            logger.debug(f"Using default provider '{provider.name}' for agent {agent_config.slug}")

    if not provider:
        # No user provider - will use environment variables
        logger.debug(f"No user provider for agent {agent_config.slug}, using env vars")
        return effective_model_name, None, provider_type, None

    # 4. Decrypt API key and get base_url
    api_key = decrypt_api_key(provider.api_key_encrypted)
    base_url = provider.base_url
    logger.debug(f"Resolved credentials: api_key=***{api_key[-4:] if api_key else 'None'}, base_url={base_url}")
    return effective_model_name, api_key, provider_type, base_url


def create_model_with_credentials(
    model_name: str,
    api_key: str | None,
    provider_type: LLMProviderType | None,
    base_url: str | None = None,
) -> Any:
    """
    Create a PydanticAI model with user credentials.

    Args:
        model_name: Full model name (e.g., "openai:gpt-4o-mini")
        api_key: User's decrypted API key (None = use env vars)
        provider_type: Provider type enum
        base_url: Custom base URL for OpenAI-compatible endpoints

    Returns:
        A PydanticAI Model instance, or the model_name string if no credentials
    """
    if not api_key:
        # No user credentials - return model name string (PydanticAI will use env vars)
        return model_name

    # Extract model ID from full name (e.g., "openai:gpt-4o-mini" -> "gpt-4o-mini")
    model_id = model_name.split(":", 1)[1] if ":" in model_name else model_name

    if provider_type == LLMProviderType.OPENAI:
        openai_provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        return OpenAIChatModel(model_id, provider=openai_provider)

    elif provider_type == LLMProviderType.ANTHROPIC:
        anthropic_provider = AnthropicProvider(api_key=api_key, base_url=base_url)
        return AnthropicModel(model_id, provider=anthropic_provider)

    elif provider_type == LLMProviderType.GOOGLE:
        google_provider = GoogleProvider(api_key=api_key)
        return GoogleModel(model_id, provider=google_provider)

    elif provider_type == LLMProviderType.OPENAI_COMPATIBLE:
        # OpenAI-compatible endpoints (Ollama, vLLM, Azure, etc.)
        compat_provider = OpenAIProvider(api_key=api_key, base_url=base_url)
        return OpenAIChatModel(model_id, provider=compat_provider)

    else:
        # Unknown provider type - fall back to model name string
        logger.warning(f"Unknown provider type {provider_type}, using model name directly")
        return model_name


async def get_agent_instance(session: AsyncSession, slug: str) -> Agent[Any, Any] | None:
    """
    Get basic agent instance from database AgentConfig (no tools).

    Instantiates a PydanticAI Agent using the configuration stored in the database.
    Uses the model_name and system_prompt from AgentConfig.

    For agents with A2A tools, use get_agent_instance_with_tools() instead.
    """
    config = await get_agent_config(session, slug)

    if config and config.is_enabled:
        # Instantiate PydanticAI Agent from database config
        system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"
        agent = Agent(config.model_name, system_prompt=system_prompt)
        logger.debug(f"Instantiated database agent: {config.slug} with model {config.model_name}")
        return agent

    return None


async def get_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = True,
    enable_ag_ui_tool: bool = True,
) -> Agent[AgentDeps, str] | None:
    """
    Get agent instance with A2A and AG-UI tools enabled.

    This creates a PydanticAI Agent that can:
    - Use request_agent_assistance to communicate with other agents (A2A)
    - Use emit_ui_component to create rich UI elements (AG-UI)

    When user_id is provided, resolves the user's API credentials and model
    overrides for this agent. Falls back to environment variables if no
    user provider is configured.

    Args:
        session: Async database session
        slug: Agent slug
        user_id: Optional user ID for credential resolution
        enable_a2a_tool: Whether to include the request_agent_assistance tool
        enable_ag_ui_tool: Whether to include the emit_ui_component tool

    Returns:
        Agent instance with deps type AgentDeps, or None if not found
    """
    config = await get_agent_config(session, slug)

    if not config or not config.is_enabled:
        return None

    system_prompt = config.system_prompt or f"You are {config.name}. {config.description}"

    # Resolve model and credentials
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
        # No user - use model name directly (env vars)
        model = config.model_name
        effective_model_name = config.model_name

    # Build list of tools
    tools: list[Any] = []
    if enable_a2a_tool:
        tools.append(request_agent_assistance)
    if enable_ag_ui_tool:
        tools.append(emit_ui_component)

    # Create agent with tools and deps type
    agent: Agent[AgentDeps, str] = Agent(
        model,
        system_prompt=system_prompt,
        tools=tools,
        deps_type=AgentDeps,
    )

    logger.debug(
        f"Instantiated agent {config.slug} with model {effective_model_name} "
        f"and {len(tools)} tool(s)"
    )
    return agent


async def resolve_agent_identifier(
    session: AsyncSession,
    participant_id: str,
) -> tuple[str | None, str | None, AgentConfig | None]:
    """
    Resolve a participant_id to an agent slug, display name, and config.

    participant_id can be either:
    - A UUID string (database agent ID - the standard case)
    - An agent slug (for direct lookups)

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        Tuple of (agent_slug, display_name, config) or (None, None, None) if not found.
        - agent_slug: Used for registry lookups and running the agent
        - display_name: Used for message attribution (agent's name field)
        - config: Full AgentConfig for participation mode checks
    """
    # First, try to parse as UUID (database-registered agent)
    try:
        agent_uuid = uuid.UUID(participant_id)
        agent_config = await session.get(AgentConfig, agent_uuid)

        if agent_config and agent_config.is_enabled:
            logger.debug(f"Resolved UUID {participant_id} to agent slug: {agent_config.slug}")
            return agent_config.slug, agent_config.name, agent_config

        logger.warning(f"Agent UUID {participant_id} not found or disabled in database")
        return None, None, None

    except ValueError:
        # Not a valid UUID, treat as agent slug
        pass

    # Check database registry by slug
    result = await session.execute(
        select(AgentConfig).where(AgentConfig.slug == participant_id)
    )
    agent_config = result.scalar_one_or_none()

    if agent_config and agent_config.is_enabled:
        logger.debug(f"Found database agent by slug: {participant_id}")
        return agent_config.slug, agent_config.name, agent_config

    logger.warning(f"Agent '{participant_id}' not found in database")
    return None, None, None


async def is_agent_available(session: AsyncSession, participant_id: str) -> bool:
    """
    Check if an agent is available in the database.

    Args:
        session: Async database session
        participant_id: The participant_id from RoomParticipant

    Returns:
        True if agent can be run, False otherwise
    """
    slug, _, _ = await resolve_agent_identifier(session, participant_id)
    return slug is not None


# =============================================================================
# Participation Mode Logic
# =============================================================================

def should_agent_respond_to_message(
    config: AgentConfig,
    trigger_message: str,
) -> tuple[bool, str]:
    """
    Determine if an agent should respond based on participation mode.

    Args:
        config: Agent configuration with participation_mode
        trigger_message: The message that triggered the check

    Returns:
        Tuple of (should_respond, reason)
    """
    mode = config.participation_mode or "on_mention"

    if mode == "always":
        return True, "mode=always"

    if mode == "manual":
        # Manual agents never auto-respond; they must be explicitly invoked
        return False, "mode=manual (requires explicit invocation)"

    if mode == "on_mention":
        # Check for @mention
        if is_agent_mentioned(trigger_message, config.slug, config.name):
            return True, "mentioned in message"
        return False, "not mentioned (mode=on_mention)"

    # Unknown mode - default to not responding
    logger.warning(f"Unknown participation mode '{mode}' for agent {config.slug}")
    return False, f"unknown mode '{mode}'"


# =============================================================================
# A2A (Agent-to-Agent) Communication
# =============================================================================

async def is_agent_in_room(
    session: AsyncSession,
    room_id: uuid.UUID,
    agent_identifier: str,
) -> tuple[bool, str | None, AgentConfig | None]:
    """
    Check if an agent is an active participant in a room.

    Args:
        session: Async database session
        room_id: UUID of the room
        agent_identifier: Agent slug or name to check

    Returns:
        Tuple of (is_in_room, agent_slug, agent_config)
    """
    # Get all agent participants in the room
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    agent_participants = result.scalars().all()

    # Check each agent participant
    for participant in agent_participants:
        slug, name, config = await resolve_agent_identifier(session, participant.participant_id)
        if not slug or not config:
            continue

        # Match against slug or name (case-insensitive)
        identifier_lower = agent_identifier.lower()
        if (
            slug.lower() == identifier_lower
            or name.lower() == identifier_lower
            or name.replace(" ", "").lower() == identifier_lower
        ):
            return True, slug, config

    return False, None, None


async def process_agent_response(
    *,
    response: str,
    responding_agent_slug: str,
    room_id: uuid.UUID,
    session: AsyncSession,
    current_depth: int,
    emit_internal_messages: bool = False,
) -> list[dict[str, Any]]:
    """
    Process an agent's response for @mentions and trigger mentioned agents.

    This enables A2A (Agent-to-Agent) communication where agents can
    reference each other with @mentions to request assistance.

    Args:
        response: The agent's response text
        responding_agent_slug: Slug of the agent that just responded
        room_id: UUID of the room
        session: Async database session
        current_depth: Current A2A chain depth (0 = user-triggered)
        emit_internal_messages: If True, emit room_message.agent_internal events
                                for A2A triggers (default False)

    Returns:
        List of response dicts from triggered agents
    """
    # Check depth limit to prevent infinite loops
    if current_depth >= MAX_A2A_DEPTH:
        logger.debug(
            f"A2A depth limit reached ({current_depth}/{MAX_A2A_DEPTH}), "
            f"not processing mentions in {responding_agent_slug}'s response"
        )
        return []

    # Detect @mentions in the response
    mentions = detect_mentions(response)
    if not mentions:
        return []

    logger.info(
        f"Agent {responding_agent_slug} mentioned {len(mentions)} potential agents: {mentions}"
    )

    triggered_responses = []

    for mention in mentions:
        # Skip self-mentions
        if mention.lower() == responding_agent_slug.lower():
            continue

        # Check if mentioned agent is in the room
        is_in_room, agent_slug, config = await is_agent_in_room(session, room_id, mention)

        if not is_in_room or not agent_slug or not config:
            logger.debug(f"Mentioned '{mention}' is not an agent in room {room_id}")
            continue

        # Check if the mentioned agent can respond (not manual mode)
        if config.participation_mode == "manual":
            logger.debug(
                f"Agent {agent_slug} is in manual mode, skipping A2A trigger"
            )
            continue

        logger.info(
            f"A2A: {responding_agent_slug} triggered {agent_slug} "
            f"(depth {current_depth} -> {current_depth + 1})"
        )

        # Optionally emit an internal message to create audit trail
        if emit_internal_messages:
            await emit_agent_internal_message(
                session=session,
                room_id=room_id,
                from_agent=responding_agent_slug,
                to_agent=agent_slug,
                content=f"[A2A Trigger] Requesting assistance from @{agent_slug}",
                visible_to_users=False,
            )

        # Trigger the mentioned agent with the response as context
        # The trigger message includes attribution so the agent knows who mentioned them
        trigger_message = f"@{responding_agent_slug} said: {response}"

        agent_response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=agent_slug,
            trigger_message=trigger_message,
            session=session,
            a2a_depth=current_depth + 1,
        )

        triggered_responses.append(agent_response)

    return triggered_responses


# =============================================================================
# Prompt Building
# =============================================================================

def build_agent_prompt(
    trigger_message: str,
    context: Any,
    current_agent_slug: str | None = None,
) -> str:
    """
    Build the full prompt for an agent including room context and other agents.

    Args:
        trigger_message: The user's message that triggered the agent
        context: RoomContext from context_provider
        current_agent_slug: Slug of the agent receiving this prompt (to exclude from list)

    Returns:
        Full prompt string with context prepended
    """
    conversation_context = ""

    # Add story context if available
    if context.story_data:
        conversation_context += f"\nStory: {context.story_data.get('title', 'Untitled')}\n"
        if context.story_data.get('description'):
            conversation_context += f"Description: {context.story_data.get('description')}\n"

    # Add other agents in the room (agent-aware prompting)
    if context.active_agents:
        other_agents = [
            agent for agent in context.active_agents
            if agent.slug != current_agent_slug
        ]
        if other_agents:
            conversation_context += "\nOther agents in this room:\n"
            for agent in other_agents:
                desc = agent.description or "Assistant"
                line = f"- {agent.name} (@{agent.slug}): {desc}"
                if agent.capabilities:
                    caps = ", ".join(agent.capabilities)
                    line += f" [Capabilities: {caps}]"
                conversation_context += line + "\n"
            conversation_context += (
                "\nYou can reference other agents with @mentions if their expertise is needed.\n"
            )

    # Add recent messages for conversation continuity
    if context.recent_messages:
        recent = context.recent_messages[-5:]
        conversation_context += "\nRecent conversation:\n"
        for msg in recent:
            sender = msg.get("agent_name") or "User"
            conversation_context += f"{sender}: {msg.get('content', '')}\n"

    # Combine context with user message
    if conversation_context:
        return f"{conversation_context}\nUser message: {trigger_message}"
    return trigger_message


# =============================================================================
# Agent Execution
# =============================================================================

async def run_agent_for_room(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Run an agent in a room context and emit its response as an event.

    This is the main entry point for agent execution (non-streaming). It:
    1. Validates the agent exists
    2. Builds room context
    3. Runs the agent
    4. Emits room_message.agent event

    Args:
        room_id: UUID of the room
        agent_name: Name/slug of the agent to run (e.g., "StoryAdvisor")
        trigger_message: The message that triggered the agent
        session: Async database session (transaction managed by caller)

    Returns:
        Dict with agent response details:
        {
            "agent_name": str,
            "content": str,
            "success": bool,
            "error": str | None
        }

    Note:
        This function does NOT manage transactions. The caller (route handler)
        must use AsyncSessionTransactionDep to ensure atomic operations.
    """
    # Validate agent exists
    if not await is_agent_available(session, agent_name):
        logger.warning(f"Attempted to run unregistered agent: {agent_name}")
        return {
            "agent_name": agent_name,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }

    try:
        # Build room context
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
        )

        # Get agent instance
        agent = await get_agent_instance(session, agent_name)
        if not agent:
            return {
                "agent_name": agent_name,
                "content": "",
                "success": False,
                "error": f"Failed to instantiate agent '{agent_name}'",
            }

        # Build prompt with context (pass agent_name to exclude from other agents list)
        full_prompt = build_agent_prompt(trigger_message, context, current_agent_slug=agent_name)

        # Run agent
        result = await agent.run(full_prompt)
        response_content = result.output

        # Emit agent message event
        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload={
                "agent_name": agent_name,
                "content": response_content,
            },
        )

        logger.info(f"Agent {agent_name} responded in room {room_id}")

        return {
            "agent_name": agent_name,
            "content": response_content,
            "success": True,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Agent {agent_name} error in room {room_id}: {e}")

        # Emit error message as agent response
        error_content = (
            "I encountered an error while processing your request. Please try again."
        )

        try:
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": error_content,
                },
            )
        except Exception as emit_error:
            logger.error(f"Failed to emit error message: {emit_error}")

        return {
            "agent_name": agent_name,
            "content": error_content,
            "success": False,
            "error": str(e),
        }


async def should_agent_respond(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    session: AsyncSession,
) -> bool:
    """
    Check if an agent should respond to a message.

    Currently checks if the agent is an active participant in the room.
    For participation mode checks, use should_agent_respond_to_message().

    Args:
        room_id: UUID of the room
        agent_name: Name of the agent
        session: Async database session

    Returns:
        True if agent should respond, False otherwise
    """
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.participant_id == agent_name,
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()

    return participant is not None


async def run_agent_for_room_streaming(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    a2a_depth: int = 0,
) -> dict[str, Any]:
    """
    Run an agent with token-by-token streaming and A2A support.

    Differences from non-streaming version:
    1. Uses agent.run_stream() instead of agent.run()
    2. Publishes tokens to Redis as they arrive
    3. Still emits final room_message.agent event with complete response
    4. Processes @mentions in response to trigger other agents (A2A)

    Token streaming:
    - Tokens published via Redis as ephemeral message.delta events
    - NOT persisted to Postgres (only final message is persisted)
    - Clients receive tokens in real-time for progressive rendering

    A2A (Agent-to-Agent):
    - After response, detects @mentions of other agents
    - Triggers mentioned agents if they're in the room
    - Respects MAX_A2A_DEPTH to prevent infinite loops

    Args:
        room_id: UUID of the room
        agent_name: Name/slug of the agent to run
        trigger_message: The message that triggered the agent
        session: Async database session
        user_id: User ID for resolving API credentials (None = use env vars)
        a2a_depth: Current depth in A2A chain (0 = user-triggered, default)

    Returns:
        Dict with agent response details
    """
    # Check agent availability
    if not await is_agent_available(session, agent_name):
        logger.warning(f"Attempted to run unregistered agent: {agent_name}")
        return {
            "agent_name": agent_name,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_name}' not found",
        }

    try:
        # Build room context
        context = await build_room_context(
            room_id=room_id,
            session=session,
            message_limit=20,
        )

        # Get agent instance with A2A tools and user credentials
        agent = await get_agent_instance_with_tools(
            session, agent_name, user_id=user_id, enable_a2a_tool=True
        )
        if not agent:
            return {
                "agent_name": agent_name,
                "content": "",
                "success": False,
                "error": f"Failed to instantiate agent '{agent_name}'",
            }

        # Create deps for tool context
        deps = AgentDeps(
            session=session,
            room_id=room_id,
            current_agent_slug=agent_name,
            a2a_depth=a2a_depth,
        )

        # Build prompt with context (pass agent_name to exclude from other agents list)
        full_prompt = build_agent_prompt(trigger_message, context, current_agent_slug=agent_name)

        # Debug logging - show what we're sending to the LLM
        logger.debug(
            f"Agent {agent_name} making LLM call:\n"
            f"  Model: {agent.model}\n"
            f"  Prompt length: {len(full_prompt)} chars\n"
            f"  Prompt preview: {full_prompt[:500]}..."
        )

        # Run agent with streaming
        # NOTE: stream_text() yields CUMULATIVE text (full message so far), not deltas
        full_response = ""
        prev_len = 0

        async with agent.run_stream(full_prompt, deps=deps) as result:
            async for chunk in result.stream_text():
                # Extract only the new content since last iteration
                new_content = chunk[prev_len:]
                full_response = chunk  # Update to latest full response
                prev_len = len(chunk)

                # Publish only the new content to Redis
                if new_content:
                    await publish_agent_token(
                        room_id=room_id,
                        agent_name=agent_name,
                        token=new_content,
                    )

        # Collect UI components emitted by agent tools
        ui_components = deps.ui_components or []
        ui_components_data = [c.model_dump() for c in ui_components]

        # Emit final complete message event (with optional UI components)
        payload: dict[str, Any] = {
            "agent_name": agent_name,
            "content": full_response,
        }
        if ui_components_data:
            payload["ui_components"] = ui_components_data

        await emit_event(
            session=session,
            room_id=room_id,
            event_type="room_message.agent",
            payload=payload,
        )

        if ui_components:
            logger.info(
                f"Agent {agent_name} emitted {len(ui_components)} UI component(s)"
            )

        logger.info(f"Agent {agent_name} streamed response in room {room_id}")

        # A2A: Process @mentions in the response to trigger other agents
        a2a_responses = await process_agent_response(
            response=full_response,
            responding_agent_slug=agent_name,
            room_id=room_id,
            session=session,
            current_depth=a2a_depth,
        )

        if a2a_responses:
            logger.info(
                f"A2A: {agent_name} triggered {len(a2a_responses)} agent(s)"
            )

        return {
            "agent_name": agent_name,
            "content": full_response,
            "success": True,
            "error": None,
            "a2a_triggered": [r["agent_name"] for r in a2a_responses if r.get("success")],
            "ui_components": ui_components_data if ui_components_data else None,
        }

    except ModelAPIError as e:
        # PydanticAI model API error - includes details from the provider
        logger.error(
            f"Agent {agent_name} API error in room {room_id}:\n"
            f"  Error: {e}\n"
            f"  Status: {getattr(e, 'status_code', 'N/A')}\n"
            f"  Body: {getattr(e, 'body', 'N/A')}",
            exc_info=True,
        )
        error_content = f"API Error: {e}"

        try:
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": error_content,
                },
            )
        except Exception as emit_error:
            logger.error(f"Failed to emit error message: {emit_error}")

        return {
            "agent_name": agent_name,
            "content": error_content,
            "success": False,
            "error": str(e),
        }

    except Exception as e:
        logger.error(
            f"Agent {agent_name} streaming error in room {room_id}: {e}",
            exc_info=True,  # This logs the full traceback
        )
        error_content = "I encountered an error while processing your request."

        try:
            await emit_event(
                session=session,
                room_id=room_id,
                event_type="room_message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": error_content,
                },
            )
        except Exception as emit_error:
            logger.error(f"Failed to emit error message: {emit_error}")

        return {
            "agent_name": agent_name,
            "content": error_content,
            "success": False,
            "error": str(e),
        }


# =============================================================================
# High-Level Entry Point
# =============================================================================

async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
) -> list[dict[str, Any]]:
    """
    Run agents in a room that should respond to a message based on participation mode.

    This is the high-level function called from route handlers.

    Execution order:
    1. Coordinator agents run FIRST (regardless of participation mode)
       - Coordinators can analyze intent and @mention specialists
       - Only one coordinator typically, but multiple are allowed
    2. Regular agents run based on their participation modes:
       - "always": Agent responds to every message
       - "on_mention": Agent responds only when @mentioned
       - "manual": Agent does not auto-respond (must be explicitly invoked)

    The Coordinator Pattern enables orchestration where a primary agent
    routes to specialists based on message content.

    Args:
        room_id: UUID of the room
        trigger_message: The message that triggered agents
        session: Async database session (transaction managed by caller)
        user_id: User ID for resolving API credentials (None = use env vars)

    Returns:
        List of agent response dicts (one per agent that ran)
    """
    # Find all active agent participants
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    agent_participants = result.scalars().all()

    # Separate coordinators from regular agents
    coordinators: list[tuple[str, str, AgentConfig]] = []
    regular_agents: list[tuple[str, str, AgentConfig, str]] = []  # + participant_id

    for participant in agent_participants:
        participant_id = participant.participant_id

        # Resolve participant_id to agent slug and config
        agent_slug, display_name, config = await resolve_agent_identifier(
            session, participant_id
        )

        if not agent_slug or not config:
            logger.warning(
                f"Agent participant '{participant_id}' in room {room_id} "
                f"could not be resolved to a registered agent"
            )
            continue

        if config.is_coordinator:
            coordinators.append((agent_slug, display_name, config))
        else:
            regular_agents.append((agent_slug, display_name, config, participant_id))

    responses = []

    # Phase 1: Run coordinator agents first (bypass participation mode)
    for agent_slug, display_name, _config in coordinators:
        logger.info(
            f"Running coordinator agent '{display_name}' (slug: {agent_slug}) "
            f"in room {room_id}"
        )

        response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=agent_slug,
            trigger_message=trigger_message,
            session=session,
            user_id=user_id,
        )
        responses.append(response)

    # Phase 2: Run regular agents based on participation mode
    for agent_slug, display_name, config, _ in regular_agents:
        # Check participation mode
        should_respond, reason = should_agent_respond_to_message(config, trigger_message)

        if not should_respond:
            logger.debug(
                f"Agent '{display_name}' skipped in room {room_id}: {reason}"
            )
            continue

        logger.info(
            f"Running agent '{display_name}' (slug: {agent_slug}) "
            f"in room {room_id} ({reason})"
        )

        response = await run_agent_for_room_streaming(
            room_id=room_id,
            agent_name=agent_slug,
            trigger_message=trigger_message,
            session=session,
            user_id=user_id,
        )
        responses.append(response)

    return responses


async def invoke_agent_manually(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]:
    """
    Explicitly invoke an agent regardless of participation mode.

    Use this for:
    - Manual mode agents that need explicit invocation
    - Testing/debugging agents
    - Admin-triggered agent responses

    Args:
        room_id: UUID of the room
        agent_slug: Slug of the agent to invoke
        trigger_message: The message/prompt for the agent
        session: Async database session

    Returns:
        Agent response dict
    """
    # Verify agent exists and is in the room
    slug, display_name, config = await resolve_agent_identifier(session, agent_slug)

    if not slug or not config:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Agent '{agent_slug}' not found",
        }

    # Check if agent is participant in room
    result = await session.execute(
        select(RoomParticipant).where(
            RoomParticipant.room_id == room_id,
            RoomParticipant.participant_type == "agent",
            RoomParticipant.participant_id.in_([agent_slug, str(config.id)]),
            RoomParticipant.active == True,  # noqa: E712
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        return {
            "agent_name": agent_slug,
            "content": "",
            "success": False,
            "error": f"Agent '{display_name}' is not a participant in this room",
        }

    logger.info(
        f"Manually invoking agent '{display_name}' (slug: {slug}) "
        f"in room {room_id}"
    )

    return await run_agent_for_room_streaming(
        room_id=room_id,
        agent_name=slug,
        trigger_message=trigger_message,
        session=session,
    )
