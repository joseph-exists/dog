"""
User Management Commands

Commands for creating and managing Forgejo users via the Admin API.

Note: Path setup is handled by main.py - no sys.path manipulation needed here.
"""

import json
from typing import Annotated

import typer

from openapi_client import CreateUserOption, ApiException


from app.test_scripts.forge_admin.typer_forge.forge_client import (
    get_admin_api,
    get_current_user,
    get_user_api,
)

app = typer.Typer(help="User management commands")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:300]}")
    raise typer.Exit(1)


# =============================================================================
# User Commands
# =============================================================================

@app.command()
def me(
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get current authenticated user info.

    Example:
        python main.py users me
        python main.py users me --json
    """
    try:
        user = get_current_user()

        if json_output:
            typer.echo(json.dumps(user, indent=2, default=str))
        else:
            typer.echo(f"\n👤 Current User:\n")
            typer.echo(f"Username: {user.get('login')}")
            typer.echo(f"Email: {user.get('email')}")
            typer.echo(f"Full Name: {user.get('full_name', 'N/A')}")
            typer.echo(f"ID: {user.get('id')}")
            typer.echo(f"Is Admin: {'Yes' if user.get('is_admin') else 'No'}")

    except ApiException as e:
        handle_api_error(e, "get current user")


@app.command()
def create(
    username: Annotated[str, typer.Argument(help="Username for the new user")],
    email: Annotated[str, typer.Option("--email", "-e", help="Email address")] = None,
    password: Annotated[str, typer.Option("--password", "-p", help="Password")] = "changeme123",
    full_name: Annotated[str, typer.Option("--name", "-n", help="Full name")] = None,
    must_change: Annotated[bool, typer.Option("--must-change", help="Require password change")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """
    Create a new Forgejo user (requires admin token).

    Example:
        python main.py users create newuser --email user@test.local
        python main.py users create testuser -e test@test.local -p secretpass
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Default email if not provided
    if email is None:
        email = f"{username}@localhost.local"

    log(f"Creating user: {username} ({email})")

    user_options = CreateUserOption(
        username=username,
        email=email,
        password=password,
        full_name=full_name or username,
        must_change_password=must_change,
        send_notify=False,
    )

    log(f"Payload: {user_options.to_dict()}")

    try:
        admin = get_admin_api()
        user = admin.admin_create_user(body=user_options)
        user_dict = user.to_dict()

        if json_output:
            typer.echo(json.dumps(user_dict, indent=2, default=str))
        else:
            typer.secho("✅ User created successfully!", fg=typer.colors.GREEN)
            typer.echo(f"\nUsername: {user_dict.get('login')}")
            typer.echo(f"Email: {user_dict.get('email')}")
            typer.echo(f"ID: {user_dict.get('id')}")

    except ApiException as e:
        if e.status == 422:
            typer.secho(f"❌ User already exists or invalid data", fg=typer.colors.RED)
            typer.echo(f"   {e.body[:200] if e.body else ''}")
            raise typer.Exit(1)
        elif e.status == 403:
            typer.secho(f"❌ Permission denied - token needs write:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        else:
            handle_api_error(e, "create user")


@app.command()
def get(
    username: Annotated[str, typer.Argument(help="Username to look up")],
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Get user information by username.

    Example:
        python main.py users get someuser
    """
    try:
        user_api = get_user_api()
        user = user_api.user_get(username=username)
        user_dict = user.to_dict()

        if json_output:
            typer.echo(json.dumps(user_dict, indent=2, default=str))
        else:
            typer.echo(f"\n👤 User: {user_dict.get('login')}\n")
            typer.echo(f"Email: {user_dict.get('email', 'N/A')}")
            typer.echo(f"Full Name: {user_dict.get('full_name', 'N/A')}")
            typer.echo(f"ID: {user_dict.get('id')}")
            typer.echo(f"Is Admin: {'Yes' if user_dict.get('is_admin') else 'No'}")
            typer.echo(f"Created: {user_dict.get('created', 'N/A')}")

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ User '{username}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "get user")


@app.command()
def delete(
    username: Annotated[str, typer.Argument(help="Username to delete")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
    purge: Annotated[bool, typer.Option("--purge", help="Purge user data")] = False,
):
    """
    Delete a user (requires admin token).

    Example:
        python main.py users delete olduser
        python main.py users delete olduser --force --purge
    """
    if not force:
        typer.secho(f"⚠️  This will delete user '{username}'", fg=typer.colors.YELLOW)
        if purge:
            typer.secho("   --purge: All user data will be removed", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        admin = get_admin_api()
        admin.admin_delete_user(username=username, purge=purge)
        typer.secho(f"✅ User '{username}' deleted", fg=typer.colors.GREEN)

    except ApiException as e:
        if e.status == 404:
            typer.secho(f"❌ User '{username}' not found", fg=typer.colors.RED)
            raise typer.Exit(1)
        elif e.status == 403:
            typer.secho(f"❌ Permission denied - token needs write:admin scope", fg=typer.colors.RED)
            raise typer.Exit(1)
        handle_api_error(e, "delete user")


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
