"""
Template Command Module for Forge CLI

Copy this file to create new command modules.
Example: cp _template.py repos.py

Then:
1. Update the module docstring
2. Import the relevant API and models
3. Add your commands
4. Register in ../main.py
"""

import typer
import json
from typing import Annotated
from pprint import pformat

# Import forge client and SDK components
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from forge_client import get_api_client
from openapi_client.rest import ApiException

# Create typer app for this command group
app = typer.Typer(help="Template commands - replace with your feature area")


# =============================================================================
# Helper Functions
# =============================================================================

def handle_api_error(e: ApiException, context: str = "operation"):
    """Standard error handling for API exceptions."""
    typer.secho(f"❌ Failed to {context}: {e.status} - {e.reason}", fg=typer.colors.RED)
    if e.body:
        typer.echo(f"   {e.body[:200]}")
    raise typer.Exit(1)


# =============================================================================
# Commands
# =============================================================================

@app.command()
def example(
    name: Annotated[str, typer.Argument(help="Name parameter")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    Example command - replace with real functionality.

    Example:
        python main.py template example "test"
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log(f"Running example with name={name}")

    # Example API call pattern:
    # try:
    #     api = SomeApi(get_api_client())
    #     result = api.some_method(name=name)
    #
    #     if json_output:
    #         typer.echo(json.dumps(result.to_dict(), indent=2))
    #     else:
    #         typer.echo(f"Result: {result.name}")
    #
    # except ApiException as e:
    #     handle_api_error(e, "perform example operation")

    typer.echo(f"Example command called with: {name}")


@app.command("list")
def list_items(
    limit: Annotated[int, typer.Option(help="Max items to return")] = 10,
    json_output: Annotated[bool, typer.Option("--json", help="Output as JSON")] = False,
):
    """
    List items with pagination.

    Example:
        python main.py template list --limit 5
    """
    typer.echo(f"Listing up to {limit} items...")
    # Implement listing logic here


# =============================================================================
# Direct execution
# =============================================================================

if __name__ == "__main__":
    app()
