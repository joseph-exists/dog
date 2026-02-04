"""
Page Layout Management Commands

Commands for managing persisted page layouts for entities.
Supports listing, getting, upserting, updating, and deleting page layouts.

API Endpoints:
    GET    /pages/                                    - List pages (with filters)
    GET    /pages/{entity_type}/{entity_id}           - Get page layout for entity
    POST   /pages/{entity_type}/{entity_id}/layout    - Upsert page layout
    PUT    /pages/{page_id}                           - Update page by ID
    DELETE /pages/{page_id}                           - Delete page by ID
"""
import json
from typing import Annotated

import typer

from auth_helper import get_authenticated_session

app = typer.Typer(help="Page layout management commands")

BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# List Command
# ============================================================================


@app.command("list")
def list_pages(
    entity_type: Annotated[
        str | None,
        typer.Option("--type", "-t", help="Filter by entity type"),
    ] = None,
    entity_id: Annotated[
        str | None,
        typer.Option("--entity-id", "-e", help="Filter by entity ID"),
    ] = None,
    entity_type_prefix: Annotated[
        str | None,
        typer.Option("--type-prefix", help="Filter by entity type prefix"),
    ] = None,
    entity_id_prefix: Annotated[
        str | None,
        typer.Option("--id-prefix", help="Filter by entity ID prefix"),
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
    List persisted page layouts.

    Supports filtering by entity type/ID and prefix matching.

    Examples:
        python main.py pages list
        python main.py pages list --type story
        python main.py pages list --type-prefix room --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"skip": skip, "limit": limit}
    if entity_type:
        params["entity_type"] = entity_type
    if entity_id:
        params["entity_id"] = entity_id
    if entity_type_prefix:
        params["entity_type_prefix"] = entity_type_prefix
    if entity_id_prefix:
        params["entity_id_prefix"] = entity_id_prefix

    log(f"GET /pages/ with params: {params}")
    response = session.get(f"{BASE_URL}/pages/", params=params)
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        pages = data.get("data", [])
        total = data.get("count", 0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n📄 Page Layouts ({len(pages)} of {total}):\n")

            if not pages:
                typer.secho("  No page layouts found", fg=typer.colors.YELLOW)
            else:
                for page in pages:
                    _print_page_summary(page, verbose)
    else:
        typer.secho("❌ Failed to list pages", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Get Command
# ============================================================================


@app.command("get")
def get_page(
    entity_type: Annotated[str, typer.Argument(help="Entity type (e.g. 'story', 'room')")],
    entity_id: Annotated[str, typer.Argument(help="Entity ID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get the page layout for a specific entity.

    Examples:
        python main.py pages get story abc123
        python main.py pages get room def456 --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /pages/{entity_type}/{entity_id}")
    response = session.get(f"{BASE_URL}/pages/{entity_type}/{entity_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        page = response.json()

        if page is None:
            typer.secho("  No page layout found for this entity", fg=typer.colors.YELLOW)
            raise typer.Exit(0)

        if json_output:
            typer.echo(json.dumps(page, indent=2))
        else:
            typer.echo(f"\n📄 Page Layout:\n")
            _print_page_detail(page)
    elif response.status_code == 404:
        typer.secho(f"❌ Page not found for {entity_type}/{entity_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get page layout", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Upsert Command
# ============================================================================


@app.command("upsert")
def upsert_page(
    entity_type: Annotated[str, typer.Argument(help="Entity type (e.g. 'story', 'room')")],
    entity_id: Annotated[str, typer.Argument(help="Entity ID")],
    layout_file: Annotated[
        str, typer.Option("--file", "-f", help="JSON file containing layout_json array")
    ] = None,
    layout_inline: Annotated[
        str, typer.Option("--layout", "-l", help="Inline JSON string for layout_json")
    ] = None,
    layout_version: Annotated[
        int | None, typer.Option("--version", help="Layout version")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Create or overwrite a page layout for an entity.

    Provide layout_json via --file (path to JSON file) or --layout (inline JSON string).

    Examples:
        python main.py pages upsert story abc123 --file layout.json
        python main.py pages upsert room def456 --layout '[{"type":"chat","position":0}]'
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Parse layout JSON
    layout_json = _parse_layout_input(layout_file, layout_inline)
    if layout_json is None:
        typer.secho("❌ Must provide --file or --layout with layout JSON", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {"layout_json": layout_json}
    if layout_version is not None:
        payload["layout_version"] = layout_version

    log(f"POST /pages/{entity_type}/{entity_id}/layout")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(
        f"{BASE_URL}/pages/{entity_type}/{entity_id}/layout",
        json=payload
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        page = response.json()

        if json_output:
            typer.echo(json.dumps(page, indent=2))
        else:
            typer.secho("✅ Page layout saved!", fg=typer.colors.GREEN)
            _print_page_detail(page)
    else:
        typer.secho("❌ Failed to upsert page layout", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Update Command
# ============================================================================


@app.command("update")
def update_page(
    page_id: Annotated[str, typer.Argument(help="Page UUID to update")],
    layout_file: Annotated[
        str, typer.Option("--file", "-f", help="JSON file containing layout_json array")
    ] = None,
    layout_inline: Annotated[
        str, typer.Option("--layout", "-l", help="Inline JSON string for layout_json")
    ] = None,
    layout_version: Annotated[
        int | None, typer.Option("--version", help="Layout version")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Update an existing page layout by page ID.

    Provide layout_json via --file (path to JSON file) or --layout (inline JSON string).

    Examples:
        python main.py pages update abc123 --file updated_layout.json
        python main.py pages update abc123 --layout '[{"type":"chat","position":1}]'
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    # Parse layout JSON
    layout_json = _parse_layout_input(layout_file, layout_inline)
    if layout_json is None:
        typer.secho("❌ Must provide --file or --layout with layout JSON", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    payload = {"layout_json": layout_json}
    if layout_version is not None:
        payload["layout_version"] = layout_version

    log(f"PUT /pages/{page_id}")
    log(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.put(f"{BASE_URL}/pages/{page_id}", json=payload)

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        page = response.json()

        if json_output:
            typer.echo(json.dumps(page, indent=2))
        else:
            typer.secho("✅ Page layout updated!", fg=typer.colors.GREEN)
            _print_page_detail(page)
    elif response.status_code == 404:
        typer.secho(f"❌ Page not found: {page_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update page layout", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Delete Command
# ============================================================================


@app.command("delete")
def delete_page(
    page_id: Annotated[str, typer.Argument(help="Page UUID to delete")],
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Skip confirmation")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Delete a persisted page layout.

    Examples:
        python main.py pages delete abc123
        python main.py pages delete abc123 --force
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    if not force:
        typer.secho(f"⚠️  This will delete page {page_id}", fg=typer.colors.YELLOW)
        if not typer.confirm("Are you sure?"):
            typer.echo("Cancelled.")
            raise typer.Exit(0)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"DELETE /pages/{page_id}")
    response = session.delete(f"{BASE_URL}/pages/{page_id}")
    log(f"Response status: {response.status_code}")

    if response.status_code in [200, 204]:
        typer.secho("✅ Page layout deleted successfully", fg=typer.colors.GREEN)
    elif response.status_code == 404:
        typer.secho(f"❌ Page not found: {page_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to delete page layout", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Output Helpers
# ============================================================================


def _parse_layout_input(file_path: str | None, inline: str | None) -> list | None:
    """Parse layout JSON from file or inline string."""
    if file_path:
        try:
            with open(file_path) as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "layout_json" in data:
                return data["layout_json"]
            return [data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            typer.secho(f"❌ Failed to read layout file: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    if inline:
        try:
            data = json.loads(inline)
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError as e:
            typer.secho(f"❌ Invalid JSON in --layout: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    return None


def _print_page_summary(page: dict, verbose: bool = False) -> None:
    """Print a brief page summary for list views."""
    entity_type = page.get("entity_type", "unknown")
    entity_id = page.get("entity_id", "unknown")
    page_id = page.get("id", "N/A")
    version = page.get("layout_version", "N/A")
    panel_count = len(page.get("layout_json", []))

    typer.echo(f"  • {entity_type}/{entity_id}")
    typer.echo(f"    Page ID: {page_id}")
    typer.echo(f"    Version: {version}")
    typer.echo(f"    Panels: {panel_count}")

    if verbose:
        typer.echo(f"    Owner: {page.get('owner_id', 'N/A')}")
        typer.echo(f"    Created: {page.get('created_at', 'N/A')}")
        typer.echo(f"    Updated: {page.get('updated_at', 'N/A')}")

    typer.echo()


def _print_page_detail(page: dict) -> None:
    """Print detailed page information."""
    typer.echo(f"  ID:          {page.get('id', 'N/A')}")
    typer.echo(f"  Entity Type: {page.get('entity_type', 'N/A')}")
    typer.echo(f"  Entity ID:   {page.get('entity_id', 'N/A')}")
    typer.echo(f"  Version:     {page.get('layout_version', 'N/A')}")
    typer.echo(f"  Owner:       {page.get('owner_id', 'N/A')}")
    typer.echo(f"  Created:     {page.get('created_at', 'N/A')}")
    typer.echo(f"  Updated:     {page.get('updated_at', 'N/A')}")

    layout = page.get("layout_json", [])
    typer.echo(f"  Panels:      {len(layout)}")

    if layout:
        typer.echo()
        for i, panel in enumerate(layout):
            panel_type = panel.get("type", panel.get("panel_type", "unknown"))
            typer.echo(f"    [{i}] {panel_type}")
            for key, value in panel.items():
                if key not in ("type", "panel_type"):
                    display_val = str(value)
                    if len(display_val) > 60:
                        display_val = display_val[:60] + "..."
                    typer.echo(f"        {key}: {display_val}")


if __name__ == "__main__":
    app()
