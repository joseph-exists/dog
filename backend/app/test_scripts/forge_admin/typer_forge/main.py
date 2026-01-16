#!/usr/bin/env python3
"""
Forge CLI - Forgejo Administration via OpenAPI Client

A typer-based CLI for managing Forgejo instances using the generated SDK.

Usage:
    source /home/josep/dog/backend/.venv/bin/activate
    cd /home/josep/dog/backend/app/test_scripts/forge-admin/typer-forge
    python main.py [COMMAND] [OPTIONS]

Examples:
    python main.py --help
    python main.py users create "newuser" --email "user@test.local"
    python main.py users me
    python main.py admin list-users
"""

import typer
from openapi_client import ApiException
from app.test_scripts.forge_admin.typer_forge import forge_client
from app.test_scripts.forge_admin.typer_forge.commands import (
    admin,
    issues,
    orgs,
    repos,
    users,
    wiki,
)

# Create main app
app = typer.Typer(
    name="forge",
    help="Forgejo administration CLI using OpenAPI client",
    add_completion=False,
    no_args_is_help=True,
)


# =============================================================================
# Register Command Modules
# =============================================================================



app.add_typer(users.app, name="users", help="User management commands")
app.add_typer(admin.app, name="admin", help="Admin operations")
app.add_typer(repos.app, name="repos", help="Repository management")
app.add_typer(issues.app, name="issues", help="Issue management")
app.add_typer(orgs.app, name="orgs", help="Organization management")
app.add_typer(wiki.app, name="wiki", help="Wiki page management")


# =============================================================================
# Top-level Commands
# =============================================================================

@app.command()
def version():
    """Show CLI version and connection info."""
    typer.echo("Forge CLI v0.1.0")
    typer.echo(f"Target: {forge_client.FORGE_URL}")
    typer.echo(f"Token: {forge_client.API_TOKEN[:8]}...{forge_client.API_TOKEN[-4:]}")


@app.command()
def whoami():
    """Show current authenticated user."""


    try:
        user = forge_client.get_current_user()
        typer.echo(f"👤 {user.get('login')} ({user.get('email')})")
        if user.get('is_admin'):
            typer.secho("   [Admin]", fg=typer.colors.YELLOW)
    except ApiException as e:
        typer.secho(f"❌ Auth failed: {e.status} - {e.reason}", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.command()
def test():
    """Test API connection."""
    typer.echo(f"Testing connection to {forge_client.FORGE_URL}...")

    if forge_client.test_connection():
        user = forge_client.get_current_user()
        typer.secho("✅ Connection successful!", fg=typer.colors.GREEN)
        typer.echo(f"   Authenticated as: {user.get('login')}")
        typer.echo(f"   Admin: {user.get('is_admin')}")
    else:
        typer.secho("❌ Connection failed", fg=typer.colors.RED)
        raise typer.Exit(1)


@app.callback()
def main():
    """
    Forge CLI for Forgejo administration.

    Manage users, repositories, organizations, and more.
    """
    pass


if __name__ == "__main__":
    app()
