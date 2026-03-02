"""
Affordance Introspection MCP Server
===================================

This MCP server exposes affordance introspection tools, enabling agents
to query what's possible, preview actions, and reason about compositions.

Tools:
- affordance_list: List all affordances in the registry
- affordance_dimensions: List all dimensions and their options
- affordance_available: What can I do given current context?
- affordance_preview: What would happen if I did X?
- affordance_elaborate: What dimensions still need specification?
- affordance_get: Get details of a specific affordance
- affordance_patterns: Get documented composition patterns

Usage:
    fastmcp run affordance_server.py
    # or
    python affordance_server.py

This server uses DIRECT service imports (no HTTP dependency on main backend).
"""

import json
from typing import Any

from fastmcp import FastMCP

# Direct import of the affordance service (no HTTP needed)
from affordance_service import (
    Action,
    Context,
    UserContext,
    DemoConfigContext,
    CompositionContext,
    get_affordance_service,
)

# Create the MCP server
mcp = FastMCP(
    "Affordance Introspection",
    instructions="""
    This server provides tools for introspecting the affordance space.
    Use these tools to understand what operations are possible, preview
    actions before taking them, and reason about compositional constraints.

    Typical workflow:
    1. Use affordance_list to see all available operations
    2. Use affordance_elaborate to understand what parameters an operation needs
    3. Use affordance_preview to validate an action before executing
    4. Use affordance_available to see what's possible given current state
    """,
)

# Get the service singleton (loads registry from demo-builder.yaml)
_service = get_affordance_service()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def build_context(
    user_id: str = "agent",
    is_superuser: bool = False,
    demo_config_id: str | None = None,
    demo_config_slug: str | None = None,
    demo_scope: str | None = None,
    has_composition: bool = False,
    panel_count: int = 0,
    block_count: int = 0,
) -> Context:
    """Build a Context object from simple parameters."""
    user = UserContext(id=user_id, is_superuser=is_superuser)

    demo_config = None
    if demo_config_id:
        demo_config = DemoConfigContext(
            id=demo_config_id,
            slug=demo_config_slug or demo_config_id,
            scope=demo_scope or "personal",
            owner_id=user_id,
            is_active=True,
        )

    composition = None
    if has_composition and demo_config_id:
        composition = CompositionContext(
            id=f"comp-{demo_config_id}",
            demo_config_id=demo_config_id,
            panels=[{"id": f"panel-{i}", "kind": "content"} for i in range(panel_count)],
            blocks=[{"id": f"block-{i}", "type": "content"} for i in range(block_count)],
        )

    return Context(
        user=user,
        demo_config=demo_config,
        composition=composition,
    )


# ============================================================================
# TOOLS
# ============================================================================


@mcp.tool
def affordance_list(category: str | None = None) -> dict[str, Any]:
    """
    List all affordances in the registry.

    Returns a summary of each affordance including name, description,
    category, and required/optional dimensions.

    Args:
        category: Optional filter by category (config, composition, panel, block, session)

    Returns:
        List of affordances grouped by category
    """
    affordances = _service.registry.affordances

    # Filter by category if specified
    if category:
        affordances = [a for a in affordances if a.category == category]

    # Build summary list
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

    # Group by category
    by_category: dict[str, list] = {}
    for item in data:
        cat = item.get("category", "unknown")
        by_category.setdefault(cat, []).append(item)

    return {
        "total": len(data),
        "by_category": by_category,
        "affordances": data,
    }


@mcp.tool
def affordance_dimensions() -> dict[str, Any]:
    """
    List all dimensions defined in the registry.

    Dimensions are the axes along which affordances vary.
    Each dimension has a type (enum, range, reference, etc.) and
    may have options, defaults, and constraints.

    Returns:
        Dictionary of dimension names to their specifications
    """
    return {
        name: dim.model_dump()
        for name, dim in _service.registry.dimensions.items()
    }


@mcp.tool
def affordance_get(name: str) -> dict[str, Any]:
    """
    Get detailed information about a specific affordance.

    Includes dimensions, preconditions, effects, and enables/precludes
    relationships.

    Args:
        name: Name of the affordance (e.g., "add_panel", "create_demo_config")

    Returns:
        Full affordance specification
    """
    for aff in _service.registry.affordances:
        if aff.name == name:
            return aff.model_dump()

    return {"error": f"Affordance not found: {name}"}


@mcp.tool
def affordance_available(
    user_id: str = "agent",
    is_superuser: bool = False,
    demo_config_id: str | None = None,
    has_composition: bool = False,
    panel_count: int = 0,
) -> dict[str, Any]:
    """
    Query what affordances are available given the current context.

    This tells you what actions you CAN take right now based on
    the current state.

    Args:
        user_id: User ID for the context
        is_superuser: Whether user has superuser privileges
        demo_config_id: ID of existing demo config (if any)
        has_composition: Whether a composition exists
        panel_count: Number of panels in composition

    Returns:
        Available affordances grouped by category, plus unavailable
        affordances with reasons
    """
    context = build_context(
        user_id=user_id,
        is_superuser=is_superuser,
        demo_config_id=demo_config_id,
        has_composition=has_composition,
        panel_count=panel_count,
    )

    result = _service.available(context)
    return result.model_dump()


@mcp.tool
def affordance_preview(
    affordance: str,
    parameters: dict[str, Any] | None = None,
    user_id: str = "agent",
    is_superuser: bool = False,
    demo_config_id: str | None = None,
    has_composition: bool = False,
) -> dict[str, Any]:
    """
    Preview what would happen if you took an action.

    This is the key introspection tool - it tells you whether an
    action would succeed, what effects it would have, and what
    affordances would become available or unavailable afterward.

    Args:
        affordance: Name of the affordance to preview
        parameters: Parameters for the action (e.g., {"scope": "personal", "title": "My Demo"})
        user_id: User ID for context
        is_superuser: Whether user is superuser
        demo_config_id: Existing demo config ID
        has_composition: Whether composition exists

    Returns:
        valid: Whether the action would succeed
        violations: Why it would fail (if invalid)
        effects: What would change
        newly_enabled: Affordances that become available
        newly_precluded: Affordances that become unavailable
    """
    context = build_context(
        user_id=user_id,
        is_superuser=is_superuser,
        demo_config_id=demo_config_id,
        has_composition=has_composition,
    )

    action = Action(
        affordance=affordance,
        parameters=parameters or {},
    )

    result = _service.preview(context, action)
    return result.model_dump()


@mcp.tool
def affordance_elaborate(
    affordance: str,
    parameters: dict[str, Any] | None = None,
    user_id: str = "agent",
) -> dict[str, Any]:
    """
    Understand what dimensions still need specification for an affordance.

    This supports progressive elaboration - you can start with just
    the affordance name and learn what parameters are required vs optional,
    what options are available for each, and what defaults exist.

    Args:
        affordance: Name of the affordance to elaborate
        parameters: Already-specified parameters (to see what's remaining)
        user_id: User ID for context

    Returns:
        specified: Parameters already provided
        remaining: Dimensions that still need values
        can_proceed: Whether enough is specified to execute
        preview: If can_proceed, a preview of the action
    """
    context = build_context(user_id=user_id)
    intent = {"affordance": affordance}

    result = _service.elaborate(context, intent, parameters or {})
    return result.model_dump()


@mcp.tool
def affordance_patterns() -> dict[str, Any]:
    """
    Get documented composition patterns.

    Patterns are named sequences of affordances that accomplish
    high-level goals. They show idiomatic ways to compose affordances.

    Returns:
        Dictionary of pattern names to their specifications,
        including steps and expected results
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


@mcp.resource("affordance://registry")
def get_registry() -> str:
    """Full affordance registry as JSON."""
    return json.dumps(_service.registry.model_dump(), indent=2)


@mcp.resource("affordance://dimensions")
def get_dimensions_resource() -> str:
    """All dimensions as JSON."""
    return json.dumps(
        {name: dim.model_dump() for name, dim in _service.registry.dimensions.items()},
        indent=2,
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    mcp.run()
