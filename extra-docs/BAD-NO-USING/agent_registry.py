"""
Agent Registry: Central registry for room-participating agents.

Provides agent lookup by name and validation. Agents register themselves
at module load time. This enables multiple agents in one room without
tight coupling.

Usage:
    from app.agents.agent_registry import AGENT_REGISTRY, get_agent

    # Register an agent
    AGENT_REGISTRY["StoryAdvisor"] = story_advisor_agent

    # Get an agent
    agent = get_agent("StoryAdvisor")
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pydantic_ai import Agent

# Global registry mapping agent names to Agent instances
AGENT_REGISTRY: dict[str, Agent[Any, Any]] = {}


def register_agent(name: str, agent: Agent[Any, Any]) -> None:
    """
    Register an agent with the given name.

    Args:
        name: Unique agent name (e.g., "StoryAdvisor")
        agent: PydanticAI Agent instance

    Raises:
        ValueError: If agent with name already registered
    """
    if name in AGENT_REGISTRY:
        raise ValueError(f"Agent '{name}' already registered")
    AGENT_REGISTRY[name] = agent


def get_agent(name: str) -> Agent[Any, Any]:
    """
    Get an agent by name.

    Args:
        name: Agent name to look up

    Returns:
        The registered Agent instance

    Raises:
        KeyError: If agent not found
    """
    if name not in AGENT_REGISTRY:
        raise KeyError(f"Agent '{name}' not found in registry")
    return AGENT_REGISTRY[name]


def list_agents() -> list[str]:
    """Return list of registered agent names."""
    return list(AGENT_REGISTRY.keys())


def is_agent_registered(name: str) -> bool:
    """Check if an agent is registered."""
    return name in AGENT_REGISTRY
