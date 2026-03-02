"""
Story Affordance Introspection Commands
=======================================

CLI commands for querying the story affordance registry. These commands
enable testing and exploration of the story affordance space.

Commands:
- available: What story operations can I perform right now?
- preview: What would happen if I did X?
- elaborate: What do I need to specify for X?
- list: List all story affordances
- dimensions: List all story dimensions
- get: Get details of a specific affordance
- patterns: List story composition patterns

Note: Uses direct import from mcpmvp (no HTTP backend required).
"""

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

# Add mcpmvp to path for direct service import
MCPMVP_PATH = Path(__file__).parents[5] / "mcpmvp"
sys.path.insert(0, str(MCPMVP_PATH))

from affordance_service import (
    Action,
    Context,
    UserContext,
    get_affordance_service,
)

# Create typer app for this command group
app = typer.Typer(help="Story affordance introspection commands")

# Get the service singleton with story-specific registry
_story_registry_path = MCPMVP_PATH / "story-builder.yaml"
_service = get_affordance_service(registry_path=_story_registry_path)


# ============================================================================
# Helper Functions
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
# Query Commands
# ============================================================================


@app.command()
def available(
    user_id: Annotated[str, typer.Option("--user", "-u", help="User ID")] = "test-user",
    is_superuser: Annotated[bool, typer.Option("--superuser", "-s", help="Is superuser")] = False,
    story_id: Annotated[str | None, typer.Option("--story-id", help="Story ID")] = None,
    is_published: Annotated[bool, typer.Option("--published", help="Story is published")] = False,
    has_nodes: Annotated[bool, typer.Option("--has-nodes", help="Story has nodes")] = False,
    has_start_node: Annotated[bool, typer.Option("--has-start", help="Has start node")] = False,
    has_end_node: Annotated[bool, typer.Option("--has-end", help="Has end node")] = False,
    progress_id: Annotated[str | None, typer.Option("--progress-id", help="Progress ID (playing)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Query available story affordances given current context.

    Example:
        story-affordances available
        story-affordances available --story-id abc123 --has-nodes
        story-affordances available --story-id abc123 --has-start --has-end
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
    data = result.model_dump()

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        affordances = data.get("affordances", [])
        by_category = data.get("by_category", {})

        typer.echo(f"\n📖 Available Story Affordances ({len(affordances)}):\n")

        for category, items in by_category.items():
            typer.secho(f"  {category.upper()}", fg=typer.colors.GREEN, bold=True)
            for item in items:
                typer.echo(f"    • {item['name']}")
                typer.secho(f"      {item['description']}", fg=typer.colors.BRIGHT_BLACK)
                if item.get("required_dimensions"):
                    typer.echo(f"      Required: {', '.join(item['required_dimensions'])}")
            typer.echo()

        unavailable = data.get("unavailable", [])
        if unavailable and verbose:
            typer.secho(f"\n🚫 Unavailable ({len(unavailable)}):", fg=typer.colors.YELLOW)
            for item in unavailable[:5]:
                typer.echo(f"    • {item['affordance']}")
                for violation in item.get("blocked_by", []):
                    typer.secho(f"      - {violation['message']}", fg=typer.colors.BRIGHT_BLACK)


@app.command()
def preview(
    affordance: Annotated[str, typer.Argument(help="Affordance name to preview")],
    params: Annotated[str | None, typer.Option("--params", "-p", help="Parameters as JSON")] = None,
    user_id: Annotated[str, typer.Option("--user", "-u", help="User ID")] = "test-user",
    is_superuser: Annotated[bool, typer.Option("--superuser", "-s", help="Is superuser")] = False,
    story_id: Annotated[str | None, typer.Option("--story-id", help="Story ID")] = None,
    is_published: Annotated[bool, typer.Option("--published", help="Story is published")] = False,
    has_start_node: Annotated[bool, typer.Option("--has-start", help="Has start node")] = False,
    has_end_node: Annotated[bool, typer.Option("--has-end", help="Has end node")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Preview what would happen if a story action were taken.

    Example:
        story-affordances preview create_story \\
            --params '{"story_title": "My Adventure", "story_slug": "my-adventure"}'
        story-affordances preview add_node --story-id abc123 \\
            --params '{"node_title": "Opening Scene", "is_start_node": true}'
    """
    # Parse parameters
    parameters = {}
    if params:
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError as e:
            typer.secho(f"❌ Invalid JSON in --params: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    context = build_story_context(
        user_id=user_id,
        is_superuser=is_superuser,
        story_id=story_id,
        is_published=is_published,
        has_start_node=has_start_node,
        has_end_node=has_end_node,
    )

    action = Action(affordance=affordance, parameters=parameters)
    result = _service.preview(context, action)
    data = result.model_dump()

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        if data.get("valid"):
            typer.secho(f"\n✅ Action is VALID\n", fg=typer.colors.GREEN, bold=True)

            typer.secho("Effects:", fg=typer.colors.BLUE, bold=True)
            for effect in data.get("effects", []):
                typer.echo(f"  • [{effect['change']}] {effect['target']}")
                typer.secho(f"    {effect['description']}", fg=typer.colors.BRIGHT_BLACK)

            newly_enabled = data.get("newly_enabled", [])
            if newly_enabled:
                typer.secho("\nNewly Enabled:", fg=typer.colors.GREEN)
                for item in newly_enabled:
                    typer.echo(f"  + {item['name']}")

            newly_precluded = data.get("newly_precluded", [])
            if newly_precluded:
                typer.secho("\nNewly Precluded:", fg=typer.colors.YELLOW)
                for item in newly_precluded:
                    typer.echo(f"  - {item['name']}")
        else:
            typer.secho(f"\n❌ Action is INVALID\n", fg=typer.colors.RED, bold=True)

            typer.secho("Violations:", fg=typer.colors.RED)
            for violation in data.get("violations", []):
                typer.echo(f"  • {violation['constraint_id']}")
                typer.secho(f"    {violation['message']}", fg=typer.colors.BRIGHT_BLACK)
                typer.echo(f"    Dimension: {violation['dimension']}")


@app.command()
def elaborate(
    affordance: Annotated[str, typer.Argument(help="Affordance name to elaborate")],
    params: Annotated[str | None, typer.Option("--params", "-p", help="Already-specified parameters as JSON")] = None,
    user_id: Annotated[str, typer.Option("--user", "-u", help="User ID")] = "test-user",
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Show what dimensions still need specification for a story affordance.

    Example:
        story-affordances elaborate add_node
        story-affordances elaborate add_choice --params '{"choice_text": "Go left"}'
    """
    # Parse parameters
    parameters = {}
    if params:
        try:
            parameters = json.loads(params)
        except json.JSONDecodeError as e:
            typer.secho(f"❌ Invalid JSON in --params: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    context = build_story_context(user_id=user_id)
    intent = {"affordance": affordance, "parameters": parameters}

    result = _service.elaborate(context, intent)
    data = result.model_dump()

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(f"\n🔍 Elaborating: {data.get('affordance', affordance)}\n")

        specified = data.get("specified", {})
        if specified:
            typer.secho("Already Specified:", fg=typer.colors.GREEN)
            for key, value in specified.items():
                typer.echo(f"  ✓ {key}: {value}")
            typer.echo()

        remaining = data.get("remaining", [])
        if remaining:
            typer.secho("Still Needed:", fg=typer.colors.YELLOW)
            for dim in remaining:
                req_marker = "*" if dim["required"] else ""
                typer.echo(f"  • {dim['dimension']}{req_marker} ({dim['type']})")
                if dim.get("description"):
                    typer.secho(f"    {dim['description']}", fg=typer.colors.BRIGHT_BLACK)
                if dim.get("options"):
                    typer.echo(f"    Options: {', '.join(str(o) for o in dim['options'][:5])}")
                if dim.get("default") is not None:
                    typer.echo(f"    Default: {dim['default']}")
            typer.echo()

        can_proceed = data.get("can_proceed", False)
        if can_proceed:
            typer.secho("✅ Can proceed with current specification", fg=typer.colors.GREEN)
        else:
            typer.secho("⚠️  Required dimensions missing - cannot proceed yet", fg=typer.colors.YELLOW)


@app.command("list")
def list_affordances(
    category: Annotated[str | None, typer.Option("--category", "-c", help="Filter by category (story, node, choice, state, progress)")] = None,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all story affordances in the registry.

    Example:
        story-affordances list
        story-affordances list --category node
        story-affordances list --category progress
    """
    affordances = _service.registry.affordances

    if category:
        affordances = [a for a in affordances if a.category == category]

    data = [
        {
            "name": a.name,
            "description": a.description,
            "category": a.category,
        }
        for a in affordances
    ]

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        # Group by category
        by_category: dict[str, list] = {}
        for item in data:
            cat = item.get("category", "unknown")
            by_category.setdefault(cat, []).append(item)

        typer.echo(f"\n📚 Story Affordances ({len(data)} total):\n")
        for cat, items in sorted(by_category.items()):
            typer.secho(f"  {cat.upper()} ({len(items)})", fg=typer.colors.GREEN, bold=True)
            for item in items:
                typer.echo(f"    • {item['name']}")
                typer.secho(f"      {item['description']}", fg=typer.colors.BRIGHT_BLACK)
            typer.echo()


@app.command()
def dimensions(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List all dimensions defined for story affordances.

    Example:
        story-affordances dimensions
    """
    dims = _service.registry.dimensions
    data = {name: dim.model_dump() for name, dim in dims.items()}

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(f"\n📐 Story Dimensions ({len(data)}):\n")
        for name, dim in data.items():
            typer.secho(f"  {name}", fg=typer.colors.BLUE, bold=True)
            typer.echo(f"    Type: {dim.get('type', 'unknown')}")
            if dim.get("values"):
                typer.echo(f"    Values: {', '.join(str(v) for v in dim['values'][:6])}")
            if dim.get("default"):
                typer.echo(f"    Default: {dim['default']}")
            if dim.get("description"):
                typer.secho(f"    {dim['description']}", fg=typer.colors.BRIGHT_BLACK)
            typer.echo()


@app.command()
def get(
    affordance_name: Annotated[str, typer.Argument(help="Name of affordance to get")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get detailed information about a specific story affordance.

    Example:
        story-affordances get add_node
        story-affordances get navigate_choice
    """
    # Find the affordance
    found = None
    for aff in _service.registry.affordances:
        if aff.name == affordance_name:
            found = aff
            break

    if not found:
        typer.secho(f"❌ Affordance not found: {affordance_name}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    data = found.model_dump()

    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.echo(f"\n📖 {data.get('name', affordance_name)}")
        typer.secho(f"   {data.get('description', '')}", fg=typer.colors.BRIGHT_BLACK)
        typer.echo(f"   Category: {data.get('category', 'unknown')}\n")

        # Dimensions
        dims = data.get("dimensions", {})
        if dims:
            typer.secho("Dimensions:", fg=typer.colors.BLUE, bold=True)
            for name, spec in dims.items():
                req = "required" if spec.get("required") else "optional"
                typer.echo(f"  • {name} ({req})")
                if spec.get("default"):
                    typer.echo(f"    Default: {spec['default']}")
            typer.echo()

        # Preconditions
        preconds = data.get("preconditions", [])
        if preconds:
            typer.secho("Preconditions:", fg=typer.colors.YELLOW, bold=True)
            for p in preconds:
                typer.echo(f"  • {p['id']}: {p['predicate']}")
            typer.echo()

        # Effects
        effects = data.get("effects", [])
        if effects:
            typer.secho("Effects:", fg=typer.colors.GREEN, bold=True)
            for e in effects:
                typer.echo(f"  • [{e['change']}] {e['target']}")
                typer.secho(f"    {e['description']}", fg=typer.colors.BRIGHT_BLACK)
            typer.echo()

        # Enables/Precludes
        enables = data.get("enables", [])
        precludes = data.get("precludes", [])
        if enables:
            typer.secho("Enables:", fg=typer.colors.GREEN)
            typer.echo(f"  {', '.join(enables)}")
        if precludes:
            typer.secho("Precludes:", fg=typer.colors.RED)
            typer.echo(f"  {', '.join(precludes)}")


@app.command()
def patterns(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List story composition patterns.

    Example:
        story-affordances patterns
    """
    patterns_data = {
        name: pattern.model_dump()
        for name, pattern in _service.registry.patterns.items()
    }

    if json_output:
        typer.echo(json.dumps(patterns_data, indent=2))
    else:
        typer.echo(f"\n🎯 Story Composition Patterns ({len(patterns_data)}):\n")
        for name, pattern in patterns_data.items():
            typer.secho(f"  {name}", fg=typer.colors.BLUE, bold=True)
            typer.secho(f"    {pattern.get('description', '')}", fg=typer.colors.BRIGHT_BLACK)
            typer.echo(f"    Steps: {len(pattern.get('sequence', []))}")
            typer.echo(f"    Result: {pattern.get('result', '')}")
            typer.echo()


# ============================================================================
# Scenario Commands - Quick exploration helpers
# ============================================================================


@app.command()
def scenario(
    name: Annotated[str, typer.Argument(help="Scenario name: fresh, authoring, playing")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Show available affordances for common story scenarios.

    Scenarios:
    - fresh: No story exists yet (starting from scratch)
    - authoring: Working on a draft story with nodes
    - playing: Navigating a published story

    Example:
        story-affordances scenario fresh
        story-affordances scenario authoring
        story-affordances scenario playing
    """
    scenarios = {
        "fresh": {
            "description": "Starting from scratch - no story exists",
            "context": build_story_context(),
        },
        "authoring": {
            "description": "Working on a draft story with nodes",
            "context": build_story_context(
                story_id="draft-story",
                has_nodes=True,
                node_count=3,
                has_start_node=True,
            ),
        },
        "playing": {
            "description": "Navigating a published story",
            "context": build_story_context(
                story_id="published-story",
                is_published=True,
                has_nodes=True,
                has_start_node=True,
                has_end_node=True,
                progress_id="player-progress",
                current_node_id="scene-2",
            ),
        },
    }

    if name not in scenarios:
        typer.secho(f"❌ Unknown scenario: {name}", fg=typer.colors.RED, err=True)
        typer.echo(f"Available scenarios: {', '.join(scenarios.keys())}")
        raise typer.Exit(1)

    scenario_info = scenarios[name]
    result = _service.available(scenario_info["context"])
    data = result.model_dump()

    if json_output:
        typer.echo(json.dumps({"scenario": name, **data}, indent=2))
    else:
        typer.echo(f"\n🎬 Scenario: {name}")
        typer.secho(f"   {scenario_info['description']}\n", fg=typer.colors.BRIGHT_BLACK)

        affordances = data.get("affordances", [])
        by_category = data.get("by_category", {})

        typer.echo(f"Available Affordances ({len(affordances)}):\n")

        for category, items in by_category.items():
            typer.secho(f"  {category.upper()}", fg=typer.colors.GREEN, bold=True)
            for item in items:
                typer.echo(f"    • {item['name']}")
            typer.echo()


# ============================================================================
# Main (for testing module directly)
# ============================================================================

if __name__ == "__main__":
    app()
