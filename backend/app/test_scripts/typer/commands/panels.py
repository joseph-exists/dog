"""
Room Panel Configuration Commands

Commands for managing panel configurations on rooms.
Supports resolved panels, room defaults, and per-user overrides.

API Endpoints:
    GET  /rooms/{room_id}/panels            - Get resolved panels for current user
    GET  /rooms/{room_id}/panels/defaults   - Get room's default panels
    PUT  /rooms/{room_id}/panels/defaults   - Update room's default panels (owner only)
    GET  /rooms/{room_id}/panels/me         - Get my panel config override
    PUT  /rooms/{room_id}/panels/me         - Update my panel config override
"""
import json
from typing import Annotated

import typer

from auth_helper import get_authenticated_session

app = typer.Typer(help="Room panel configuration commands")

BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Get Resolved Panels
# ============================================================================


@app.command("get")
def get_resolved(
    room_id: Annotated[str, typer.Argument(help="Room UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get resolved panel configuration for current user.

    Returns the effective panels based on user override or room/type defaults.

    Examples:
        python main.py panels get abc123
        python main.py panels get abc123 --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /rooms/{room_id}/panels")
    response = session.get(f"{BASE_URL}/rooms/{room_id}/panels")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            panels = data.get("panels", [])
            source = data.get("source", "unknown")

            typer.echo(f"\n🖥️  Resolved Panels (source: {source}):\n")

            if not panels:
                typer.secho("  No panels configured", fg=typer.colors.YELLOW)
            else:
                _print_panels(panels, verbose)
    elif response.status_code == 404:
        typer.secho(f"❌ Room not found: {room_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get resolved panels", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Room Default Panels
# ============================================================================


@app.command("get-defaults")
def get_defaults(
    room_id: Annotated[str, typer.Argument(help="Room UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get room's default panel configuration (set by owner).

    Examples:
        python main.py panels get-defaults abc123
        python main.py panels get-defaults abc123 --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /rooms/{room_id}/panels/defaults")
    response = session.get(f"{BASE_URL}/rooms/{room_id}/panels/defaults")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if data is None:
            typer.secho("  No default panel config set for this room", fg=typer.colors.YELLOW)
            raise typer.Exit(0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.echo(f"\n🖥️  Room Default Panels:\n")
            typer.echo(f"  Config ID: {data.get('id', 'N/A')}")
            typer.echo(f"  Room ID:   {data.get('room_id', 'N/A')}")
            typer.echo(f"  Updated:   {data.get('updated_at', 'N/A')}")

            panels = data.get("panels", [])
            if panels:
                typer.echo()
                _print_panels(panels, verbose)
            else:
                typer.secho("\n  No panels in default config", fg=typer.colors.YELLOW)
    elif response.status_code == 404:
        typer.secho(f"❌ Room not found: {room_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get room defaults", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("set-defaults")
def update_defaults(
    room_id: Annotated[str, typer.Argument(help="Room UUID")],
    panels_file: Annotated[
        str, typer.Option("--file", "-f", help="JSON file containing panels array")
    ] = None,
    panels_inline: Annotated[
        str, typer.Option("--panels", "-p", help="Inline JSON string for panels")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Update room's default panel configuration. Only room owner can modify.

    Provide panels via --file (path to JSON file) or --panels (inline JSON string).

    Examples:
        python main.py panels set-defaults abc123 --file panels.json
        python main.py panels set-defaults abc123 --panels '[{"type":"chat"},{"type":"info"}]'
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    panels_data = _parse_panels_input(panels_file, panels_inline)
    if panels_data is None:
        typer.secho("❌ Must provide --file or --panels with panels JSON array", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"PUT /rooms/{room_id}/panels/defaults")
    log(f"Payload: {json.dumps(panels_data, indent=2)}")

    response = session.put(
        f"{BASE_URL}/rooms/{room_id}/panels/defaults",
        json=panels_data
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Room default panels updated!", fg=typer.colors.GREEN)
            typer.echo(f"  Config ID: {data.get('id', 'N/A')}")
            typer.echo(f"  Room ID:   {data.get('room_id', 'N/A')}")
            typer.echo(f"  Updated:   {data.get('updated_at', 'N/A')}")

            panels = data.get("panels", [])
            if panels:
                typer.echo()
                _print_panels(panels, verbose)
    elif response.status_code == 403:
        typer.secho("❌ Permission denied - only room owner can update defaults", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    elif response.status_code == 404:
        typer.secho(f"❌ Room not found: {room_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update room defaults", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# User Panel Config (My Config)
# ============================================================================


@app.command("my-config")
def get_my_config(
    room_id: Annotated[str, typer.Argument(help="Room UUID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get your panel configuration override for a room.

    Examples:
        python main.py panels my-config abc123
        python main.py panels my-config abc123 --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    log(f"GET /rooms/{room_id}/panels/me")
    response = session.get(f"{BASE_URL}/rooms/{room_id}/panels/me")
    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if data is None:
            typer.secho("  No personal panel config for this room (using defaults)", fg=typer.colors.YELLOW)
            raise typer.Exit(0)

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            use_defaults = data.get("use_room_defaults", True)

            typer.echo(f"\n🖥️  My Panel Config:\n")
            typer.echo(f"  Config ID:         {data.get('id', 'N/A')}")
            typer.echo(f"  User ID:           {data.get('user_id', 'N/A')}")
            typer.echo(f"  Room ID:           {data.get('room_id', 'N/A')}")
            typer.echo(f"  Use Room Defaults: {'Yes' if use_defaults else 'No'}")
            typer.echo(f"  Updated:           {data.get('updated_at', 'N/A')}")

            panels = data.get("panels")
            if panels:
                typer.echo()
                _print_panels(panels, verbose)
            elif not use_defaults:
                typer.secho("\n  No custom panels set", fg=typer.colors.YELLOW)
    elif response.status_code == 404:
        typer.secho(f"❌ Room not found: {room_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to get my panel config", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


@app.command("set-my-config")
def update_my_config(
    room_id: Annotated[str, typer.Argument(help="Room UUID")],
    use_defaults: Annotated[
        bool, typer.Option("--use-defaults/--custom", help="Use room defaults or custom panels")
    ] = True,
    panels_file: Annotated[
        str, typer.Option("--file", "-f", help="JSON file containing panels array")
    ] = None,
    panels_inline: Annotated[
        str, typer.Option("--panels", "-p", help="Inline JSON string for panels")
    ] = None,
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Update your panel configuration for a room.

    Use --use-defaults to follow room defaults, or --custom with --file/--panels
    to set a personal override.

    Examples:
        python main.py panels set-my-config abc123 --use-defaults
        python main.py panels set-my-config abc123 --custom --file my_panels.json
        python main.py panels set-my-config abc123 --custom --panels '[{"type":"chat"}]'
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    panels_data = None
    if not use_defaults:
        panels_data = _parse_panels_input(panels_file, panels_inline)
        if panels_data is None:
            typer.secho("❌ When using --custom, provide --file or --panels", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    try:
        session = get_authenticated_session()
    except Exception as e:
        typer.secho(f"❌ Authentication failed: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    params = {"use_room_defaults": use_defaults}

    log(f"PUT /rooms/{room_id}/panels/me?use_room_defaults={use_defaults}")
    log(f"Body: {json.dumps(panels_data, indent=2) if panels_data else 'null'}")

    response = session.put(
        f"{BASE_URL}/rooms/{room_id}/panels/me",
        params=params,
        json=panels_data
    )

    log(f"Response status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()

        if json_output:
            typer.echo(json.dumps(data, indent=2))
        else:
            typer.secho("✅ Panel config updated!", fg=typer.colors.GREEN)
            using = "room defaults" if data.get("use_room_defaults") else "custom panels"
            typer.echo(f"  Config: {using}")
            typer.echo(f"  Updated: {data.get('updated_at', 'N/A')}")

            panels = data.get("panels")
            if panels:
                typer.echo()
                _print_panels(panels, verbose)
    elif response.status_code == 404:
        typer.secho(f"❌ Room not found: {room_id}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    else:
        typer.secho("❌ Failed to update panel config", fg=typer.colors.RED, err=True)
        typer.echo(f"Status: {response.status_code}")
        typer.echo(f"Error: {response.text}")
        raise typer.Exit(1)


# ============================================================================
# Helpers
# ============================================================================


def _parse_panels_input(file_path: str | None, inline: str | None) -> list | None:
    """Parse panels JSON from file or inline string."""
    if file_path:
        try:
            with open(file_path) as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "panels" in data:
                return data["panels"]
            return [data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            typer.secho(f"❌ Failed to read panels file: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    if inline:
        try:
            data = json.loads(inline)
            if isinstance(data, list):
                return data
            return [data]
        except json.JSONDecodeError as e:
            typer.secho(f"❌ Invalid JSON in --panels: {e}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    return None


def _print_panels(panels: list, verbose: bool = False) -> None:
    """Print panel list in a readable format."""
    for i, panel in enumerate(panels):
        panel_type = panel.get("type", panel.get("panel_type", "unknown"))
        typer.echo(f"  [{i}] {panel_type}")

        if verbose:
            for key, value in panel.items():
                if key not in ("type", "panel_type"):
                    display_val = str(value)
                    if len(display_val) > 60:
                        display_val = display_val[:60] + "..."
                    typer.echo(f"      {key}: {display_val}")


if __name__ == "__main__":
    app()
