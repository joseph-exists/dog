"""
Agent Management Commands

Commands for working with agents in the system.
"""
import json
from typing import Annotated

import typer

from auth_helper import get_authenticated_session

app = typer.Typer(help="Agent management commands")

BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Agent Commands
# ============================================================================


@app.command("list-available")
def list_available(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
):
    """
    List available agents for room participation.

    Returns the canonical list of agents that can be added to rooms.
    This is the single source of truth (replaces frontend hardcoded list).

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
            typer.echo(f"\n🤖 Available Agents ({total}):\n")

            if not agents:
                typer.secho("  No agents available", fg=typer.colors.YELLOW)
            else:
                for agent in agents:
                    agent_id = agent.get("id", "unknown")
                    name = agent.get("name", "Unknown Agent")
                    description = agent.get("description", "")

                    typer.secho(f"  • {name}", fg=typer.colors.CYAN)
                    typer.echo(f"    ID: {agent_id}")
                    if description:
                        typer.echo(f"    {description}")
                    typer.echo()
    else:
        typer.secho("❌ Failed to get available agents", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
