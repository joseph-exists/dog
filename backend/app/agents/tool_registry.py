"""
 Tool Registry - Maps agent slugs to their available tools.

 Hybrid approach:
 - Core tools defined in Python with full type safety
 - Additional tools can be added via JSON config for flexibility
 """

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

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


# =============================================================================
# Built-in A2A Tools
# =============================================================================

# Note: The request_agent_assistance tool is defined in agent_runner.py
# and attached directly to agents via get_agent_instance_with_tools().
# This is because it requires access to AgentDeps which includes session
# and room context that aren't available through the simple registry pattern.
#
# For custom tools that don't need session/room context, use the registry:
#
# from app.agents.tool_registry import register_tool, ToolDefinition
#
# register_tool("my_tool", ToolDefinition(
#     name="my_tool",
#     description="Does something useful",
#     implementation=my_tool_fn,
# ))
