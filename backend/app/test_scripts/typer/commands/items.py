"""
Items Command Module

"""
import json
import typer
from typing import Annotated

from auth_helper import get_authenticated_session

# Create typer app for this command group
app = typer.Typer(help="Items Module")

# Configuration
from cli_config import get_api_v1_url

BASE_URL = get_api_v1_url()

# ============================================================================
# Commands
# ============================================================================

@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the item to create")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Optional description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Enable verbose output")] = False
):
    """
    Create a new item.

    Example:
        python -m backend.app.test_scripts.typer.main template create "My Item" --desc "A test item"
    """

    def log(msg: str):
        """Log verbose messages."""
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Creating item: {name}")

    # Get authenticated session
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Prepare payload
    payload = {
        "name": name,
        "description": description
    }

    log(f"Payload: {json.dumps(payload, indent=2)}")

    # Make API request
    response = session.post(f"{BASE_URL}/items", json=payload)

    log(f"Response status: {response.status_code}")
    log(f"Response body: {response.text[:500]}")

    # Handle response
    if response.status_code in [200, 201]:
        item = response.json()
        typer.secho("✅ Item created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {item.get('id', 'N/A')}")
        typer.echo(f"Name: {item.get('name', 'N/A')}")

        if verbose:
            typer.echo("\nFull response:")
            typer.echo(json.dumps(item, indent=2))
    else:
        typer.secho(f"❌ Failed to create item", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def list(
    limit: Annotated[int, typer.Option(help="Maximum items to list")] = 10,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False
):
    """
    List items with pagination.

    Example:
        python -m backend.app.test_scripts.typer.main template list --limit 5
    """

    # Get authenticated session
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Make API request
    response = session.get(
        f"{BASE_URL}/items",
        params={"limit": limit, "offset": offset}
    )

    # Handle response
    if response.status_code == 200:
        data = response.json()
        items = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            # Machine-readable JSON output
            typer.echo(json.dumps(data, indent=2))
        else:
            # Human-readable output
            typer.echo(f"\n📦 Items ({len(items)} of {total}):\n")

            if not items:
                typer.secho("  No items found", fg=typer.colors.YELLOW)
            else:
                for item in items:
                    typer.echo(f"  • {item.get('name', 'Unnamed')}")
                    typer.echo(f"    ID: {item.get('id', 'N/A')}")
                    if item.get('description'):
                        typer.echo(f"    Desc: {item['description']}")
                    typer.echo()
    else:
        typer.secho(f"❌ Failed to list items", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command()
def delete(
    item_id: Annotated[str, typer.Argument(help="ID of item to delete")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False
):
    """
    Delete an item (with confirmation).

    Example:
        python -m backend.app.test_scripts.typer.main template delete abc123
    """

    # Confirmation prompt (unless --force)
    if not force:
        typer.secho(f"⚠️  This will delete item {item_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    # Get authenticated session
    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    # Make API request
    response = session.delete(f"{BASE_URL}/items/{item_id}")

    # Handle response
    if response.status_code in [200, 204]:
        typer.secho("✅ Item deleted successfully", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed to delete item", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Main (for testing module directly)
# ============================================================================

if __name__ == "__main__":
    # This allows testing the command module directly:
    # python -m backend.app.test_scripts.typer.commands._template create "Test"
    app()
