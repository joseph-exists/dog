"""
Preset Management Commands

Commands for browsing available panel presets.
These endpoints are public (no auth required) for read operations.

API Endpoints:
    GET  /presets              - List all presets
    GET  /presets/{preset_id}  - Get preset by ID
"""
import json
from typing import Annotated

import httpx
import typer

app = typer.Typer(help="Panel preset browsing commands")

BASE_URL = "http://localhost:8000/api/v1"


# ============================================================================
# Helper Functions
# ============================================================================


def _get_session() -> httpx.Client:
    """Get HTTP client (no auth needed for preset endpoints)."""
    return httpx.Client(timeout=30.0)


def _print_preset_summary(preset: dict, verbose: bool = False) -> None:
    """Print a brief preset summary for list views."""
    preset_id = preset.get("id", "unknown")
    name = preset.get("name", "Unknown Preset")
    is_system = preset.get("is_system", False)
    panel_count = len(preset.get("panels", []))

    system_badge = " [system]" if is_system else ""
    typer.secho(f"  • {name}{system_badge}", fg=typer.colors.CYAN)
    typer.echo(f"    ID: {preset_id}")
    typer.echo(f"    Panels: {panel_count}")

    if preset.get("description"):
        desc = preset["description"]
        if len(desc) > 80:
            desc = desc[:80] + "..."
        typer.echo(f"    {desc}")

    if verbose and preset.get("panels"):
        for i, panel in enumerate(preset["panels"]):
            panel_type = panel.get("type", panel.get("panel_type", "unknown"))
            typer.echo(f"      [{i}] {panel_type}")

    typer.echo()


def _print_preset_detail(preset: dict) -> None:
    """Print detailed preset information."""
    typer.echo(f"  ID:          {preset.get('id', 'N/A')}")
    typer.echo(f"  Name:        {preset.get('name', 'N/A')}")
    typer.echo(f"  System:      {'Yes' if preset.get('is_system') else 'No'}")

    if preset.get("description"):
        typer.echo(f"  Description: {preset['description']}")

    panels = preset.get("panels", [])
    typer.echo(f"  Panels:      {len(panels)}")

    if panels:
        typer.echo()
        for i, panel in enumerate(panels):
            panel_type = panel.get("type", panel.get("panel_type", "unknown"))
            typer.echo(f"    [{i}] {panel_type}")
            for key, value in panel.items():
                if key not in ("type", "panel_type"):
                    display_val = str(value)
                    if len(display_val) > 60:
                        display_val = display_val[:60] + "..."
                    typer.echo(f"        {key}: {display_val}")


# ============================================================================
# List Command
# ============================================================================


@app.command("list")
def list_presets(
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    List all available panel presets.

    No authentication required.

    Examples:
        python main.py presets list
        python main.py presets list --json
        python main.py presets list -v
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        log("GET /presets")
        response = session.get(f"{BASE_URL}/presets")
        log(f"Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            presets = data.get("presets", [])

            if json_output:
                typer.echo(json.dumps(data, indent=2))
            else:
                typer.echo(f"\n🎨 Available Presets ({len(presets)}):\n")

                if not presets:
                    typer.secho("  No presets found", fg=typer.colors.YELLOW)
                else:
                    for preset in presets:
                        _print_preset_summary(preset, verbose)
        else:
            typer.secho("❌ Failed to list presets", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


# ============================================================================
# Get Command
# ============================================================================


@app.command("get")
def get_preset(
    preset_id: Annotated[str, typer.Argument(help="Preset ID")],
    json_output: Annotated[
        bool, typer.Option("--json", help="Output as JSON")
    ] = False,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="Verbose output")
    ] = False,
):
    """
    Get details of a specific preset.

    No authentication required.

    Examples:
        python main.py presets get my-preset
        python main.py presets get my-preset --json
    """

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    with _get_session() as session:
        log(f"GET /presets/{preset_id}")
        response = session.get(f"{BASE_URL}/presets/{preset_id}")
        log(f"Response status: {response.status_code}")

        if response.status_code == 200:
            preset = response.json()

            if json_output:
                typer.echo(json.dumps(preset, indent=2))
            else:
                typer.echo(f"\n🎨 Preset Details:\n")
                _print_preset_detail(preset)
        elif response.status_code == 404:
            typer.secho(f"❌ Preset not found: {preset_id}", fg=typer.colors.RED, err=True)
            raise typer.Exit(1)
        else:
            typer.secho("❌ Failed to get preset", fg=typer.colors.RED, err=True)
            typer.echo(f"Status: {response.status_code}")
            typer.echo(f"Error: {response.text}")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
