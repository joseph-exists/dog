"""
Story Builder Affordance MCP Server
====================================

This MCP server exposes story-building affordance introspection tools,
enabling agents to understand what operations are possible when authoring
and navigating stories.

Tools:
- story_affordance_list: List all story affordances
- story_affordance_get: Get details of a specific affordance
- story_affordance_available: What can I do given current story context?
- story_affordance_preview: What would happen if I did X?
- story_affordance_elaborate: What parameters does this operation need?
- story_affordance_patterns: Get documented composition patterns

Usage:
    fastmcp run story_server.py
    # or
    python story_server.py
"""

import json
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

# Reuse the affordance service infrastructure
from affordance_service import (
    Action,
    Context,
    UserContext,
    get_affordance_service,
)

# Create the MCP server
mcp = FastMCP(
    "Story Builder",
    instructions="""
    This server provides tools for introspecting story-building affordances.
    Use these tools to understand what operations are possible when creating
    and navigating interactive stories.

    Key concepts:
    - Story: A versioned container with draft/published states
    - Node: A point in the story graph with content
    - Choice: An edge connecting nodes, optionally gated by state
    - State: Variables that track player progress and unlock choices

    Typical workflow:
    1. Use story_affordance_list to see all operations
    2. Use story_affordance_elaborate to understand parameters
    3. Use story_affordance_preview to validate before calling backend API
    4. Use story_affordance_patterns for common sequences
    """,
)

# Load story-specific registry
_story_registry_path = Path(__file__).parent / "story-builder.yaml"
_service = get_affordance_service(registry_path=_story_registry_path)


# ============================================================================
# CONTEXT BUILDERS
# ============================================================================


def build_story_context(
    user_id: str = "agent",
    is_superuser: bool = False,
    story_id: str | None = None,
    story_version: int | None = None,
    is_published: bool = False,
    has_nodes: bool = False,
    node_count: int = 0,
    has_start_node: bool = False,
    has_end_node: bool = False,
    progress_id: str | None = None,
    current_node_id: str | None = None,
) -> Context:
    """Build a Context object from story-specific parameters."""
    user = UserContext(id=user_id, is_superuser=is_superuser)

    # Build extra context for story-specific preconditions
    extra = {
        "story_id": story_id,
        "story_version": story_version,
        "is_published": is_published,
        "has_nodes": has_nodes,
        "node_count": node_count,
        "has_start_node": has_start_node,
        "has_end_node": has_end_node,
        "progress_id": progress_id,
        "current_node_id": current_node_id,
    }

    return Context(user=user, extra=extra)


# ============================================================================
# TOOLS
# ============================================================================


@mcp.tool
def story_affordance_list(category: str | None = None) -> dict[str, Any]:
    """
    List all story-building affordances.

    Returns a summary of each affordance including name, description,
    category, and required/optional dimensions.

    Args:
        category: Optional filter by category (story, node, choice, state, progress)

    Returns:
        List of affordances grouped by category
    """
    affordances = _service.registry.affordances

    if category:
        affordances = [a for a in affordances if a.category == category]

    data = []
    for aff in affordances:
        required_dims = [k for k, v in aff.dimensions.items() if getattr(v, "required", False)]
        optional_dims = [k for k, v in aff.dimensions.items() if not getattr(v, "required", False)]
        data.append({
            "name": aff.name,
            "description": aff.description,
            "category": aff.category,
            "required_dimensions": required_dims,
            "optional_dimensions": optional_dims,
        })

    by_category: dict[str, list] = {}
    for item in data:
        cat = item.get("category", "unknown")
        by_category.setdefault(cat, []).append(item)

    return {
        "domain": "story-builder",
        "total": len(data),
        "by_category": by_category,
        "affordances": data,
    }


@mcp.tool
def story_affordance_get(name: str) -> dict[str, Any]:
    """
    Get detailed information about a specific story affordance.

    Includes dimensions, preconditions, effects, and enables/precludes
    relationships.

    Args:
        name: Name of the affordance (e.g., "add_node", "create_story")

    Returns:
        Full affordance specification
    """
    for aff in _service.registry.affordances:
        if aff.name == name:
            return aff.model_dump()

    return {"error": f"Affordance not found: {name}"}


@mcp.tool
def story_affordance_dimensions() -> dict[str, Any]:
    """
    List all dimensions defined for story affordances.

    Dimensions are the axes along which affordances vary:
    - story_id, story_version, story_title (story-level)
    - node_id, node_title, node_content, is_start_node (node-level)
    - choice_id, choice_text, requires_state, sets_state (choice-level)
    - state_key, state_value_type (state schema)
    - progress_id, current_node_id, story_state (runtime)

    Returns:
        Dictionary of dimension names to their specifications
    """
    return {
        name: dim.model_dump()
        for name, dim in _service.registry.dimensions.items()
    }


@mcp.tool
def story_affordance_available(
    user_id: str = "agent",
    is_superuser: bool = False,
    story_id: str | None = None,
    is_published: bool = False,
    has_nodes: bool = False,
    has_start_node: bool = False,
    has_end_node: bool = False,
    progress_id: str | None = None,
) -> dict[str, Any]:
    """
    Query what story affordances are available given current context.

    This tells you what operations you CAN perform right now.

    Args:
        user_id: User ID for context
        is_superuser: Whether user has superuser privileges
        story_id: ID of existing story (if any)
        is_published: Whether the story is published
        has_nodes: Whether the story has any nodes
        has_start_node: Whether the story has a start node
        has_end_node: Whether the story has an end node
        progress_id: ID of player progress (if playing)

    Returns:
        Available affordances grouped by category
    """
    context = build_story_context(
        user_id=user_id,
        is_superuser=is_superuser,
        story_id=story_id,
        is_published=is_published,
        has_nodes=has_nodes,
        has_start_node=has_start_node,
        has_end_node=has_end_node,
        progress_id=progress_id,
    )

    result = _service.available(context)
    return result.model_dump()


@mcp.tool
def story_affordance_preview(
    affordance: str,
    parameters: dict[str, Any] | None = None,
    user_id: str = "agent",
    is_superuser: bool = False,
    story_id: str | None = None,
    is_published: bool = False,
    has_start_node: bool = False,
    has_end_node: bool = False,
) -> dict[str, Any]:
    """
    Preview what would happen if you took a story action.

    This is the key introspection tool - it tells you whether an
    action would succeed and what effects it would have.

    Args:
        affordance: Name of the affordance to preview
        parameters: Parameters for the action
        user_id: User ID for context
        is_superuser: Whether user is superuser
        story_id: Existing story ID
        is_published: Whether story is published
        has_start_node: Whether story has start node
        has_end_node: Whether story has end node

    Returns:
        valid: Whether the action would succeed
        violations: Why it would fail (if invalid)
        effects: What would change
        newly_enabled: Affordances that become available
    """
    context = build_story_context(
        user_id=user_id,
        is_superuser=is_superuser,
        story_id=story_id,
        is_published=is_published,
        has_start_node=has_start_node,
        has_end_node=has_end_node,
    )

    action = Action(
        affordance=affordance,
        parameters=parameters or {},
    )

    result = _service.preview(context, action)
    return result.model_dump()


@mcp.tool
def story_affordance_elaborate(
    affordance: str,
    parameters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Understand what dimensions still need specification for a story affordance.

    This supports progressive elaboration - learn what parameters are
    required vs optional, what options exist, and what defaults apply.

    Args:
        affordance: Name of the affordance to elaborate
        parameters: Already-specified parameters

    Returns:
        specified: Parameters already provided
        remaining: Dimensions that still need values
        can_proceed: Whether enough is specified to execute
    """
    context = build_story_context()
    intent = {"affordance": affordance}

    result = _service.elaborate(context, intent, parameters or {})
    return result.model_dump()


@mcp.tool
def story_affordance_patterns() -> dict[str, Any]:
    """
    Get documented story composition patterns.

    Patterns are named sequences of affordances that accomplish
    high-level goals like:
    - create_linear_story: Simple sequential narrative
    - create_branching_story: Story with multiple endings
    - add_conditional_choice: Choice gated by state

    Returns:
        Dictionary of pattern names to their specifications
    """
    return {
        "patterns": {
            name: pattern.model_dump()
            for name, pattern in _service.registry.patterns.items()
        },
        "domain": _service.registry.domain,
        "version": _service.registry.version,
    }


# ============================================================================
# RESOURCES
# ============================================================================


@mcp.resource("story://registry")
def get_story_registry() -> str:
    """Full story affordance registry as JSON."""
    return json.dumps(_service.registry.model_dump(), indent=2)


@mcp.resource("story://dimensions")
def get_story_dimensions() -> str:
    """All story dimensions as JSON."""
    return json.dumps(
        {name: dim.model_dump() for name, dim in _service.registry.dimensions.items()},
        indent=2,
    )


@mcp.resource("story://categories")
def get_story_categories() -> str:
    """Story affordance categories and their affordances."""
    by_category: dict[str, list[str]] = {}
    for aff in _service.registry.affordances:
        by_category.setdefault(aff.category, []).append(aff.name)
    return json.dumps(by_category, indent=2)


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    mcp.run()
