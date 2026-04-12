"""
Agent Management Commands

Commands for working with the agent registry system.
Supports full CRUD operations for agent configurations.

API Endpoints:
    GET    /agents              - List agents (scope filter)
    GET    /agents/available    - List enabled system agents
    GET    /agents/{id}         - Get agent by ID
    POST   /agents              - Create agent
    PUT    /agents/{id}         - Update agent
    DELETE /agents/{id}         - Delete agent

Provider Types (discriminated union):
    openai           - OpenAI provider (Type1)
    openai_compatible - OpenAI-compatible provider (Type3)
"""
import json
from typing import Annotated

import typer

from auth_helper import get_authenticated_session

app = typer.Typer(help="Agent registry management commands")

from cli_config import get_api_v1_url

BASE_URL = get_api_v1_url()

# Provider type UUIDs for the discriminated union
PROVIDER_TYPES = {
    "openai": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "openai_compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
}

# Friendly names for display
PROVIDER_NAMES = {v: k for k, v in PROVIDER_TYPES.items()}


# ============================================================================
# List Commands
# ============================================================================


@app.command("list")
def list_agents(
    scope: Annotated[
        str | None,
        typer.Option("--scope", "-s", help="Filter by scope: system, personal"),
    ] = None,
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 20,
    skip: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    List all agent configurations.

    Users see system agents + their personal agents.
    Admins see all agents.

    Examples:
        python main.py agents list
        python main.py agents list --scope system
        python main.py agents list --scope personal --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"limit": limit, "skip": skip}
    if scope:
        params["scope"] = scope

    log(f"GET /agents with params: {params}")
    response = session.get(f"{BASE_URL}/agents", params=params)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        agents = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🤖 Agent Configurations ({len(agents)} of {total}):\n")

            if not agents:
                typer.secho("  No agents found", fg=typer.colors.YELLOW)
            else:
                for agent in agents:
                    _print_agent_summary(agent, verbose)
    else:
        typer.secho("❌ Failed to list agents", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("list-available")
def list_available(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """
    List agents available for room participation.

    Returns enabled system agents that can be added to rooms.

    Example:
        python main.py agents list-available
        python main.py agents list-available --json
    """

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    response = session.get(f"{BASE_URL}/agents/available")

    if response.status_code == 200:
        data = response.json()
        agents = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🤖 Available Agents for Rooms ({total}):\n")

            if not agents:
                typer.secho("  No agents available", fg=typer.colors.YELLOW)
            else:
                for agent in agents:
                    slug = agent.get("slug", agent.get("id", "unknown"))
                    name = agent.get("name", "Unknown Agent")
                    description = agent.get("description", "")

                    typer.secho(f"  • {name}", fg=typer.colors.CYAN)
                    typer.echo(f"    Slug: {slug}")
                    if description:
                        typer.echo(f"    {description}")
                    typer.echo()
    else:
        typer.secho("❌ Failed to get available agents", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Get Command
# ============================================================================


@app.command("get")
def get_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get agent configuration by ID.

    Example:
        python main.py agents get 550e8400-e29b-41d4-a716-446655440000
        python main.py agents get <agent-id> --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /agents/{agent_id}")
    response = session.get(f"{BASE_URL}/agents/{agent_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        agent = response.json()

        if json_output:
            typer.echo(json.dumps(agent, indent=2))
        else:
            typer.echo(f"\n🤖 Agent Configuration:\n")
            _print_agent_detail(agent)
    elif response.status_code == 404:
        typer.secho(f"❌ Agent not found: {agent_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Access denied", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get agent", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Create Command
# ============================================================================


@app.command("create")
def create_agent(
    name: Annotated[str, typer.Argument(help="Display name for the agent")],
    slug: Annotated[str, typer.Argument(help="Unique identifier/slug")],
    provider_type: Annotated[
        str,
        typer.Option(
            "--provider", "-t",
            help="Provider type: openai (default), openai_compatible"
        ),
    ] = "openai",
    description: Annotated[
        str | None, typer.Option("--desc", "-d", help="Agent description (required for openai)")
    ] = None,
    system_prompt: Annotated[
        str | None, typer.Option("--prompt", "-p", help="System prompt (required)")
    ] = None,
    model_name: Annotated[
        str, typer.Option("--model-name", help="Friendly model name")
    ] = "friendly model name",
    model_id: Annotated[
        str | None, typer.Option("--model-id", help="Model UUID from catalog")
    ] = None,
    scope: Annotated[
        str, typer.Option("--scope", "-s", help="Scope: personal or system")
    ] = "personal",
    participation_mode: Annotated[
        str, typer.Option("--mode", help="Participation mode: always, on_mention, manual")
    ] = "on_mention",
    is_coordinator: Annotated[
        bool, typer.Option("--coordinator/--no-coordinator", help="Process messages first")
    ] = False,
    max_tool_iterations: Annotated[
        int, typer.Option("--max-iterations", help="Max LLM requests per run")
    ] = 10,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Create a new agent configuration.

    Users can create personal agents. Only admins can create system agents.
    The API uses a discriminated union based on provider_type.

    Provider Types:
        openai            - Standard OpenAI provider (requires description and prompt)
        openai_compatible - OpenAI-compatible providers (requires prompt)

    Examples:
        python main.py agents create "My Helper" my-helper --desc "A helpful agent" --prompt "You are helpful"
        python main.py agents create "Story Bot" story-bot --provider openai --desc "Storyteller" --prompt "Tell stories"
        python main.py agents create "Local LLM" local-bot --provider openai_compatible --prompt "You are an assistant"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Validate provider type
    if provider_type not in PROVIDER_TYPES:
        valid_types = ", ".join(PROVIDER_TYPES.keys())
        typer.secho(f"❌ Invalid provider type: {provider_type}", fg=typer.colors.RED, err=True)
        typer.echo(f"Valid types: {valid_types}")
        raise typer.Exit(1)

    provider_type_uuid = PROVIDER_TYPES[provider_type]
    log(f"Provider type: {provider_type} -> {provider_type_uuid}")

    # Validate required fields based on provider type
    if provider_type == "openai":
        if not description:
            typer.secho("❌ --desc is required for openai provider type", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        if not system_prompt:
            typer.secho("❌ --prompt is required for openai provider type", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
    elif provider_type == "openai_compatible":
        if not system_prompt:
            typer.secho("❌ --prompt is required for openai_compatible provider type", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        if system_prompt and len(system_prompt) > 5000:
            typer.secho("❌ --prompt exceeds 5000 char limit for openai_compatible", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Build payload with discriminator field
    payload = {
        "provider_type": provider_type_uuid,
        "name": name,
        "slug": slug,
        "system_prompt": system_prompt,
        "model_name": model_name,
        "scope": scope,
        "participation_mode": participation_mode,
        "is_enabled": True,
        "is_coordinator": is_coordinator,
        "max_tool_iterations": max_tool_iterations,
    }

    # Add optional fields
    if description:
        payload["description"] = description
    if model_id:
        payload["model_id"] = model_id

    log(f"POST /agents with payload:")
    log(json.dumps(payload, indent=2))

    response = session.post(f"{BASE_URL}/agents", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code in [200, 201]:
        agent = response.json()

        if json_output:
            typer.echo(json.dumps(agent, indent=2))
        else:
            typer.secho("✅ Agent created successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_agent_detail(agent)
    elif response.status_code == 400:
        typer.secho("❌ Invalid request", fg=typer.colors.RED, err=True)
        typer.echo(f"Error: {response.json().get('detail', response.text)}")
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Permission denied", fg=typer.colors.RED, err=True)
        typer.echo("Only admins can create system agents")
        raise typer.Exit(1)
    elif response.status_code == 422:
        typer.secho("❌ Validation error", fg=typer.colors.RED, err=True)
        detail = response.json().get("detail", [])
        for err in detail:
            typer.echo(f"  • {err.get('msg', err)}")
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to create agent", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Update Command
# ============================================================================


@app.command("update")
def update_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent UUID to update")],
    name: Annotated[str | None, typer.Option("--name", "-n", help="New display name")] = None,
    description: Annotated[
        str | None, typer.Option("--desc", "-d", help="New description")
    ] = None,
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="New model name")
    ] = None,
    system_prompt: Annotated[
        str | None, typer.Option("--prompt", "-p", help="New system prompt")
    ] = None,
    participation_mode: Annotated[
        str | None, typer.Option("--mode", help="New participation mode")
    ] = None,
    enabled: Annotated[
        bool | None, typer.Option("--enabled/--disabled", help="Enable or disable")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Update an agent configuration.

    Only provide the fields you want to change.

    Examples:
        python main.py agents update <id> --name "New Name"
        python main.py agents update <id> --disabled
        python main.py agents update <id> --model openai:gpt-4o --prompt "New prompt"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Build payload with only provided fields
    payload = {}
    if name is not None:
        payload["name"] = name
    if description is not None:
        payload["description"] = description
    if model is not None:
        payload["model_name"] = model
    if system_prompt is not None:
        payload["system_prompt"] = system_prompt
    if participation_mode is not None:
        payload["participation_mode"] = participation_mode
    if enabled is not None:
        payload["is_enabled"] = enabled

    if not payload:
        typer.secho("⚠️  No updates provided", fg=typer.colors.YELLOW)
        raise typer.Exit(0)

    log(f"PUT /agents/{agent_id} with payload:")
    log(json.dumps(payload, indent=2))

    response = session.put(f"{BASE_URL}/agents/{agent_id}", json=payload)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        agent = response.json()

        if json_output:
            typer.echo(json.dumps(agent, indent=2))
        else:
            typer.secho("✅ Agent updated successfully!", fg=typer.colors.GREEN)
            typer.echo()
            _print_agent_detail(agent)
    elif response.status_code == 404:
        typer.secho(f"❌ Agent not found: {agent_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Access denied", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update agent", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Delete Command
# ============================================================================


@app.command("delete")
def delete_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent UUID to delete")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Delete an agent configuration.

    Example:
        python main.py agents delete <agent-id>
        python main.py agents delete <agent-id> --force
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    if not force:
        typer.secho(f"⚠️  This will delete agent {agent_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"DELETE /agents/{agent_id}")
    response = session.delete(f"{BASE_URL}/agents/{agent_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Agent deleted successfully", fg=typer.colors.GREEN)
    elif response.status_code == 404:
        typer.secho(f"❌ Agent not found: {agent_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 403:
        typer.secho("❌ Access denied", fg=typer.colors.RED, err=True)
        typer.echo("Only admins can delete system agents")
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to delete agent", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Utility Commands
# ============================================================================


@app.command("enable")
def enable_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent UUID")],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Enable an agent (shortcut for update --enabled).

    Example:
        python main.py agents enable <agent-id>
    """
    update_agent(agent_id, enabled=True, verbose=verbose, json_output=False)


@app.command("disable")
def disable_agent(
    agent_id: Annotated[str, typer.Argument(help="Agent UUID")],
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Disable an agent (shortcut for update --disabled).

    Example:
        python main.py agents disable <agent-id>
    """
    update_agent(agent_id, enabled=False, verbose=verbose, json_output=False)


# ============================================================================
# Output Helpers
# ============================================================================


def _print_agent_summary(agent: dict, verbose: bool = False) -> None:
    """Print a brief agent summary for list views."""
    agent_id = agent.get("id", "unknown")
    slug = agent.get("slug", "")
    name = agent.get("name", "Unknown Agent")
    scope = agent.get("scope", "unknown")
    enabled = agent.get("is_enabled", True)

    # Status indicator
    status = "✓" if enabled else "✗"
    status_color = typer.colors.GREEN if enabled else typer.colors.RED

    # Scope badge
    scope_badge = f"[{scope}]"
    scope_color = typer.colors.BLUE if scope == "system" else typer.colors.MAGENTA

    typer.echo(f"  ", nl=False)
    typer.secho(f"{status} ", fg=status_color, nl=False)
    typer.secho(f"{name} ", fg=typer.colors.CYAN, nl=False)
    typer.secho(scope_badge, fg=scope_color)
    typer.echo(f"    ID: {agent_id}")
    typer.echo(f"    Slug: {slug}")

    if verbose:
        # Provider type
        provider_uuid = agent.get("provider_type")
        if provider_uuid:
            provider_name = PROVIDER_NAMES.get(provider_uuid, provider_uuid[:8] + "...")
            typer.echo(f"    Provider: {provider_name}")

        description = agent.get("description", "")
        model = agent.get("model_name", "")
        if description:
            typer.echo(f"    Desc: {description}")
        if model:
            typer.echo(f"    Model: {model}")

        if agent.get("is_coordinator"):
            typer.secho(f"    Coordinator: Yes", fg=typer.colors.YELLOW)

    typer.echo()


def _print_agent_detail(agent: dict) -> None:
    """Print detailed agent information."""
    typer.echo(f"  ID:          {agent.get('id', 'N/A')}")
    typer.echo(f"  Name:        {agent.get('name', 'N/A')}")
    typer.echo(f"  Slug:        {agent.get('slug', 'N/A')}")
    typer.echo(f"  Scope:       {agent.get('scope', 'N/A')}")

    # Provider type (show friendly name if possible)
    provider_uuid = agent.get("provider_type")
    if provider_uuid:
        provider_name = PROVIDER_NAMES.get(provider_uuid, provider_uuid)
        typer.echo(f"  Provider:    {provider_name}")

    enabled = agent.get("is_enabled", True)
    enabled_str = "Yes" if enabled else "No"
    enabled_color = typer.colors.GREEN if enabled else typer.colors.RED
    typer.echo(f"  Enabled:     ", nl=False)
    typer.secho(enabled_str, fg=enabled_color)

    typer.echo(f"  Model:       {agent.get('model_name', 'N/A')}")
    if agent.get("model_id"):
        typer.echo(f"  Model ID:    {agent['model_id']}")
    typer.echo(f"  Mode:        {agent.get('participation_mode', 'N/A')}")

    if agent.get("is_coordinator"):
        typer.secho(f"  Coordinator: Yes", fg=typer.colors.YELLOW)

    if agent.get("max_tool_iterations"):
        typer.echo(f"  Max Iters:   {agent['max_tool_iterations']}")

    if agent.get("description"):
        typer.echo(f"  Description: {agent['description']}")

    if agent.get("system_prompt"):
        prompt = agent["system_prompt"]
        # Truncate long prompts
        if len(prompt) > 100:
            prompt = prompt[:100] + "..."
        typer.echo(f"  Prompt:      {prompt}")

    if agent.get("capabilities"):
        caps = ", ".join(agent["capabilities"])
        typer.echo(f"  Capabilities: {caps}")

    if agent.get("owner_id"):
        typer.echo(f"  Owner:       {agent['owner_id']}")

    typer.echo(f"  Version:     {agent.get('version', 'N/A')}")
    typer.echo(f"  Created:     {agent.get('created_at', 'N/A')}")

    if agent.get("updated_at"):
        typer.echo(f"  Updated:     {agent['updated_at']}")


if __name__ == "__main__":
    app()
