"""
Demo Configuration CLI Commands
================================

Typer CLI for demo-builder operations with built-in styling presets.
Presets use ONLY supported presentation_json fields verified against color-tests.json.

Commands:
    # Demo Config CRUD
    demos create           - Create a new demo config
    demos list             - List existing demos
    demos get              - Get demo details
    demos delete           - Delete a demo

    # Composition Management
    demos compose          - Set composition from JSON file (PUT)
    demos composition      - View demo composition details
    demos preset           - Apply a named styling preset
    demos presets          - List available presets

    # Session Management
    demos session          - Create a chat session for a demo
    demos sessions         - List your demo sessions
    demos session-get      - Get details of a specific session
    demos session-update   - Update session settings (status, auto-respond)
    demos session-delete   - Delete a demo session
    demos session-resolve  - Get or create session by slug (like visiting /demo/{slug})

    # Quick Creation
    demos quick            - Quick-create a styled demo with optional session
"""

import json
from pathlib import Path
from typing import Annotated, Any

import httpx
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax

import auth_helper

console = Console()
app = typer.Typer(
    name="demos",
    help="Demo configuration and styling commands",
    no_args_is_help=True,
)

# ============================================================================
# STYLING PRESETS - ONLY SUPPORTED FIELDS
# ============================================================================
# These presets use ONLY fields verified in frontend/docs/color-tests.json
# Unsupported fields (bubbleColors, accentColor, headerGradient, etc.) are NOT used

STYLING_PRESETS: dict[str, dict[str, Any]] = {
    "neon-pulse": {
        "description": "Vibrant neon colors with glow effects",
        "composition": {
            "motion": {
                "panel_enter_ms": 280,
                "block_stagger_ms": 80,
                "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            },
            "typography": {
                "size": "sm",
                "line_height": "relaxed",
                "heading_font": "Space Grotesk",
                "body_font": "IBM Plex Sans",
            },
            "backgrounds": {
                "page_gradient": "radial-gradient(1200px 560px at 14% 0%, rgba(0, 255, 136, 0.24), rgba(0, 212, 255, 0.22), rgba(168, 85, 247, 0.18), rgba(26, 26, 46, 0.96))",
                "svg_overlay": "grid-wave-v1",
            },
            "effects": {
                "card_glow": {
                    "enable": True,
                    "css": "0 12px 36px rgba(15, 23, 42, 0.34), 0 0 42px rgba(0, 255, 136, 0.18)",
                }
            },
            "callouts": {
                "header": {"style": "neon-frame", "text": "Neon Pulse", "icon": "zap"},
            },
            "tokens": {
                "--demo-accent-primary": "#00ff88",
                "--demo-accent-secondary": "#00d4ff",
            },
        },
        "chat_panel": {
            "tokens": {"feed_density": "compact"},
            "effects": {
                "message_row_highlight": {
                    "enable": True,
                    "css": "inset 0 0 0 1px rgba(0, 255, 136, 0.35), 0 8px 20px rgba(0, 212, 255, 0.15)",
                }
            },
            "overlays": {
                "panel_header": {
                    "css": "linear-gradient(90deg, rgba(0, 255, 136, 0.30), rgba(0, 212, 255, 0.25))"
                }
            },
            "callouts": {
                "header": {"style": "status-pill", "text": "Live Chat", "icon": "message-square"}
            },
        },
    },
    "warm-studio": {
        "description": "Warm amber and coral tones for a cozy feel",
        "composition": {
            "motion": {
                "panel_enter_ms": 340,
                "block_stagger_ms": 100,
                "easing": "cubic-bezier(0.25, 0.1, 0.25, 1)",
            },
            "typography": {
                "size": "sm",
                "line_height": "relaxed",
                "heading_font": "Space Grotesk",
                "body_font": "IBM Plex Sans",
            },
            "backgrounds": {
                "page_gradient": "radial-gradient(1400px 700px at 20% 10%, rgba(255, 200, 87, 0.28), rgba(255, 138, 101, 0.24), rgba(255, 107, 157, 0.16), rgba(30, 27, 38, 0.95))",
            },
            "effects": {
                "card_glow": {
                    "enable": True,
                    "css": "0 10px 32px rgba(30, 27, 38, 0.36), 0 0 38px rgba(255, 138, 101, 0.14)",
                }
            },
            "callouts": {
                "header": {"style": "runtime-banner", "text": "Warm Studio", "icon": "sun"},
            },
            "tokens": {
                "--demo-accent-primary": "#ffc857",
                "--demo-accent-secondary": "#ff8a65",
            },
        },
        "chat_panel": {
            "tokens": {"feed_density": "comfortable"},
            "effects": {
                "message_row_highlight": {
                    "enable": True,
                    "css": "inset 0 0 0 1px rgba(255, 200, 87, 0.30), 0 6px 18px rgba(255, 138, 101, 0.12)",
                }
            },
            "overlays": {
                "panel_header": {
                    "css": "linear-gradient(90deg, rgba(255, 200, 87, 0.32), rgba(255, 138, 101, 0.26))"
                }
            },
            "callouts": {
                "header": {"style": "glass-pill", "text": "Conversation", "icon": "coffee"}
            },
        },
    },
    "ocean-depths": {
        "description": "Deep blues and teals with subtle wave motion",
        "composition": {
            "motion": {
                "panel_enter_ms": 400,
                "block_stagger_ms": 120,
                "easing": "cubic-bezier(0.33, 1, 0.68, 1)",
            },
            "typography": {
                "size": "sm",
                "line_height": "relaxed",
                "heading_font": "Space Grotesk",
                "body_font": "IBM Plex Sans",
            },
            "backgrounds": {
                "page_gradient": "radial-gradient(1300px 650px at 50% 0%, rgba(0, 150, 199, 0.26), rgba(0, 100, 148, 0.22), rgba(0, 59, 111, 0.20), rgba(10, 15, 30, 0.97))",
                "svg_overlay": "grid-wave-v1",
            },
            "effects": {
                "card_glow": {
                    "enable": True,
                    "css": "0 14px 40px rgba(10, 15, 30, 0.40), 0 0 50px rgba(0, 150, 199, 0.12)",
                }
            },
            "callouts": {
                "header": {"style": "framed-note", "text": "Ocean Depths", "icon": "waves"},
            },
            "tokens": {
                "--demo-accent-primary": "#0096c7",
                "--demo-accent-secondary": "#48cae4",
            },
        },
        "chat_panel": {
            "tokens": {"feed_density": "compact"},
            "effects": {
                "message_row_highlight": {
                    "enable": True,
                    "css": "inset 0 0 0 1px rgba(72, 202, 228, 0.28), 0 8px 22px rgba(0, 100, 148, 0.18)",
                }
            },
            "overlays": {
                "panel_header": {
                    "css": "linear-gradient(90deg, rgba(0, 150, 199, 0.28), rgba(72, 202, 228, 0.22))"
                }
            },
            "callouts": {
                "header": {"style": "status-pill", "text": "Deep Dive", "icon": "anchor"}
            },
        },
    },
    "aurora-borealis": {
        "description": "Northern lights with shifting purples and greens",
        "composition": {
            "motion": {
                "panel_enter_ms": 360,
                "block_stagger_ms": 95,
                "easing": "cubic-bezier(0.22, 1, 0.36, 1)",
            },
            "typography": {
                "size": "sm",
                "line_height": "relaxed",
                "heading_font": "Space Grotesk",
                "body_font": "IBM Plex Sans",
            },
            "backgrounds": {
                "page_gradient": "radial-gradient(1500px 700px at 30% 0%, rgba(127, 255, 0, 0.20), rgba(0, 212, 255, 0.18), rgba(168, 85, 247, 0.22), rgba(255, 107, 157, 0.14), rgba(15, 15, 35, 0.96))",
                "svg_overlay": "grid-wave-v1",
            },
            "effects": {
                "card_glow": {
                    "enable": True,
                    "css": "0 12px 38px rgba(15, 15, 35, 0.38), 0 0 48px rgba(168, 85, 247, 0.14)",
                }
            },
            "callouts": {
                "header": {"style": "neon-frame", "text": "Aurora Borealis", "icon": "sparkles"},
            },
            "tokens": {
                "--demo-accent-primary": "#a855f7",
                "--demo-accent-secondary": "#7fff00",
                "--demo-accent-tertiary": "#00d4ff",
            },
        },
        "chat_panel": {
            "tokens": {"feed_density": "compact"},
            "effects": {
                "message_row_highlight": {
                    "enable": True,
                    "css": "inset 0 0 0 1px rgba(168, 85, 247, 0.32), 0 10px 24px rgba(127, 255, 0, 0.10)",
                }
            },
            "overlays": {
                "panel_header": {
                    "css": "linear-gradient(120deg, rgba(127, 255, 0, 0.24), rgba(168, 85, 247, 0.28), rgba(0, 212, 255, 0.22))"
                }
            },
            "callouts": {
                "header": {"style": "status-pill", "text": "Northern Lights", "icon": "moon-star"}
            },
        },
    },
    "minimal-dark": {
        "description": "Clean dark theme with subtle accents",
        "composition": {
            "motion": {
                "panel_enter_ms": 200,
                "block_stagger_ms": 60,
                "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
            },
            "typography": {
                "size": "sm",
                "line_height": "normal",
            },
            "backgrounds": {
                "page_gradient": "radial-gradient(800px 400px at 50% 0%, rgba(50, 50, 70, 0.40), rgba(20, 20, 30, 0.98))",
            },
            "effects": {
                "card_glow": {
                    "enable": True,
                    "css": "0 8px 24px rgba(0, 0, 0, 0.50)",
                }
            },
            "tokens": {
                "--demo-accent-primary": "#64748b",
            },
        },
        "chat_panel": {
            "tokens": {"feed_density": "comfortable"},
            "overlays": {
                "panel_header": {
                    "css": "linear-gradient(90deg, rgba(100, 116, 139, 0.20), rgba(71, 85, 105, 0.15))"
                }
            },
        },
    },
}


def get_client() -> httpx.Client:
    """Get authenticated HTTP client."""
    token = auth_helper.get_access_token()
    return httpx.Client(
        base_url="http://localhost:8000/api/v1/demos",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )


# ============================================================================
# CRUD COMMANDS
# ============================================================================


@app.command("list")
def list_demos(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed info")] = False,
    limit: Annotated[int, typer.Option(help="Max results")] = 20,
):
    """List existing demo configurations."""
    with get_client() as client:
        response = client.get("/", params={"limit": limit})
        response.raise_for_status()
        data = response.json()

    demos = data.get("data", data) if isinstance(data, dict) else data

    if not demos:
        rprint("[dim]No demos found[/dim]")
        return

    table = Table(title="Demo Configurations", show_lines=verbose)
    table.add_column("ID", style="dim")
    table.add_column("Title", style="cyan")
    table.add_column("Slug", style="green")
    table.add_column("Scope")
    if verbose:
        table.add_column("Layout")
        table.add_column("Panels")

    for demo in demos:
        row = [
            str(demo.get("id", ""))[:8],
            demo.get("title", "Untitled"),
            demo.get("slug", "-"),
            demo.get("scope", "-"),
        ]
        if verbose:
            comp = demo.get("composition_json") or {}
            row.append(comp.get("layout_mode", "-"))
            row.append(str(len(comp.get("panels", []))))
        table.add_row(*row)

    console.print(table)


@app.command("get")
def get_demo(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID or slug")],
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Show raw JSON")] = False,
):
    """Get demo configuration details."""
    with get_client() as client:
        response = client.get(f"/configs/{demo_id}")
        if response.status_code == 404:
            rprint(f"[red]Demo not found: {demo_id}[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        demo = response.json()

    if show_json:
        console.print(Syntax(json.dumps(demo, indent=2), "json", theme="monokai"))
        return

    rprint(Panel(f"[bold]{demo.get('title', 'Untitled')}[/bold]", subtitle=f"ID: {demo.get('id')}"))
    rprint(f"  Slug: [green]{demo.get('slug', '-')}[/green]")
    rprint(f"  Scope: {demo.get('scope', '-')}")

    comp = demo.get("composition_json") or {}
    if comp:
        rprint(f"\n  [bold]Composition:[/bold]")
        rprint(f"    Layout: {comp.get('layout_mode', '-')}")
        rprint(f"    Panels: {len(comp.get('panels', []))}")
        rprint(f"    Blocks: {len(comp.get('blocks', []))}")

        pres = comp.get("presentation_json", {})
        if pres:
            rprint(f"\n  [bold]Presentation:[/bold]")
            if pres.get("backgrounds"):
                rprint(f"    Page gradient: [dim]configured[/dim]")
            if pres.get("effects"):
                rprint(f"    Effects: {list(pres['effects'].keys())}")
            if pres.get("callouts"):
                rprint(f"    Callouts: {list(pres['callouts'].keys())}")


@app.command("create")
def create_demo(
    title: Annotated[str, typer.Argument(help="Demo title")],
    slug: Annotated[str, typer.Option(help="URL slug")] = None,
    scope: Annotated[str, typer.Option(help="personal|shared|system")] = "personal",
    preset: Annotated[str, typer.Option("--preset", "-p", help="Apply a styling preset")] = None,
):
    """Create a new demo configuration."""
    # Validate preset first
    composition_data = None
    if preset:
        if preset not in STYLING_PRESETS:
            rprint(f"[red]Unknown preset: {preset}[/red]")
            rprint(f"Available: {', '.join(STYLING_PRESETS.keys())}")
            raise typer.Exit(1)
        preset_data = STYLING_PRESETS[preset]
        # Build composition with preset styling
        composition_data = {
            "schema_version": 1,
            "layout_mode": "panels",
            "runtime_policy": "auto",
            "presentation_json": preset_data["composition"],
            "panels": [
                {
                    "id": "main-chat",
                    "kind": "chat",
                    "prominence": "primary",
                    "order": 1,
                    "title": "Chat",
                    "presentation_json": preset_data.get("chat_panel", {}),
                    "default_size": 60,
                    "min_size": 30,
                    "viewport_mode": "panel",
                    "options": {"mode": "participant"},
                },
                {
                    "id": "info-panel",
                    "kind": "content",
                    "prominence": "auxiliary",
                    "order": 2,
                    "title": "Info",
                    "default_size": 40,
                    "min_size": 20,
                    "viewport_mode": "panel",
                    "options": {
                        "content_json": {
                            "format": "markdown",
                            "value": f"# {title}\n\nWelcome to this demo.",
                        }
                    },
                },
            ],
            "blocks": [],
        }

    # Create the demo config (without composition)
    demo_payload = {
        "title": title,
        "slug": slug or title.lower().replace(" ", "-"),
        "scope": scope,
    }

    with get_client() as client:
        response = client.post("/", json=demo_payload)
        if response.status_code not in (200, 201):
            rprint(f"[red]Failed to create demo: {response.text}[/red]")
            raise typer.Exit(1)
        demo = response.json()
        demo_id = demo.get("id")

        rprint(f"[green]✓ Created demo:[/green] {demo.get('title')}")
        rprint(f"  ID: {demo_id}")
        rprint(f"  Slug: {demo.get('slug')}")

        # If preset specified, set composition via PUT
        if composition_data:
            comp_response = client.put(
                f"/configs/{demo_id}/composition",
                json=composition_data,
            )
            if comp_response.status_code in (200, 201):
                rprint(f"  Preset: [cyan]{preset}[/cyan] ✓")
            else:
                rprint(f"  [yellow]Warning: Failed to set composition: {comp_response.text}[/yellow]")


@app.command("delete")
def delete_demo(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete a demo configuration."""
    if not force:
        confirm = typer.confirm(f"Delete demo {demo_id}?")
        if not confirm:
            raise typer.Abort()

    with get_client() as client:
        response = client.delete(f"/configs/{demo_id}")
        if response.status_code == 404:
            rprint(f"[red]Demo not found: {demo_id}[/red]")
            raise typer.Exit(1)
        response.raise_for_status()

    rprint(f"[green]✓ Deleted demo: {demo_id}[/green]")


# ============================================================================
# COMPOSITION COMMANDS
# ============================================================================


@app.command("compose")
def set_composition(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID")],
    json_file: Annotated[Path, typer.Argument(help="Path to composition JSON file")],
):
    """Set demo composition from a JSON file.

    Uses PUT to fully replace the composition with the JSON file contents.
    The JSON should contain the full DemoPageCompositionBase structure.
    """
    if not json_file.exists():
        rprint(f"[red]File not found: {json_file}[/red]")
        raise typer.Exit(1)

    composition = json.loads(json_file.read_text())

    with get_client() as client:
        # Use the dedicated composition endpoint with PUT for full replacement
        response = client.put(
            f"/configs/{demo_id}/composition",
            json=composition,
        )
        if response.status_code == 404:
            rprint(f"[red]Demo or composition not found: {demo_id}[/red]")
            raise typer.Exit(1)
        if response.status_code == 403:
            rprint(f"[red]Access denied - you may not own this demo config[/red]")
            raise typer.Exit(1)
        response.raise_for_status()

    rprint(f"[green]✓ Updated composition for demo {demo_id}[/green]")
    rprint(f"  Panels: {len(composition.get('panels', []))}")
    rprint(f"  Blocks: {len(composition.get('blocks', []))}")


@app.command("preset")
def apply_preset(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID")],
    preset_name: Annotated[str, typer.Argument(help="Preset name")],
):
    """Apply a styling preset to an existing demo.

    Fetches the current composition, applies the preset's presentation_json
    and chat panel styling, then PUTs the updated composition back.
    """
    if preset_name not in STYLING_PRESETS:
        rprint(f"[red]Unknown preset: {preset_name}[/red]")
        rprint(f"Available: {', '.join(STYLING_PRESETS.keys())}")
        raise typer.Exit(1)

    preset_data = STYLING_PRESETS[preset_name]

    with get_client() as client:
        # Get current composition (creates one if needed)
        response = client.get(f"/configs/{demo_id}/composition")
        if response.status_code == 404:
            rprint(f"[red]Demo not found: {demo_id}[/red]")
            raise typer.Exit(1)
        if response.status_code == 403:
            rprint(f"[red]Access denied - you may not own this demo config[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        composition = response.json()

        # Apply composition-level presentation
        composition["presentation_json"] = preset_data["composition"]

        # Apply chat panel styling to any existing chat panels
        chat_panel_style = preset_data.get("chat_panel", {})
        for panel in composition.get("panels", []):
            if panel.get("kind") == "chat":
                panel["presentation_json"] = chat_panel_style

        # PUT the updated composition using the dedicated endpoint
        response = client.put(
            f"/configs/{demo_id}/composition",
            json=composition,
        )
        if response.status_code == 403:
            rprint(f"[red]Access denied - cannot modify this demo config[/red]")
            raise typer.Exit(1)
        response.raise_for_status()

    rprint(f"[green]✓ Applied preset [cyan]{preset_name}[/cyan] to demo {demo_id}[/green]")
    rprint(f"  {preset_data['description']}")


@app.command("presets")
def list_presets(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show preset details")] = False,
):
    """List available styling presets."""
    table = Table(title="Styling Presets", show_lines=verbose)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    if verbose:
        table.add_column("Features")

    for name, preset in STYLING_PRESETS.items():
        row = [name, preset["description"]]
        if verbose:
            features = []
            comp = preset["composition"]
            if comp.get("backgrounds", {}).get("page_gradient"):
                features.append("gradient")
            if comp.get("backgrounds", {}).get("svg_overlay"):
                features.append("svg-overlay")
            if comp.get("effects", {}).get("card_glow"):
                features.append("glow")
            if comp.get("callouts"):
                features.append("callouts")
            row.append(", ".join(features) or "-")
        table.add_row(*row)

    console.print(table)
    rprint(f"\n[dim]Use: demos create 'Title' --preset {list(STYLING_PRESETS.keys())[0]}[/dim]")


# ============================================================================
# SESSION COMMANDS
# ============================================================================


@app.command("session")
def create_session(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID")],
    title: Annotated[str, typer.Option(help="Session title")] = None,
):
    """Create a chat session for a demo."""
    with get_client() as client:
        # Get demo first to verify it exists
        response = client.get(f"/configs/{demo_id}")
        if response.status_code == 404:
            rprint(f"[red]Demo not found: {demo_id}[/red]")
            raise typer.Exit(1)
        demo = response.json()

        # Create session
        session_payload = {
            "title": title or f"Session for {demo.get('title', 'Demo')}",
            "demo_config_id": demo_id,
        }
        response = client.post("/sessions", json=session_payload)
        if response.status_code not in (200, 201):
            rprint(f"[red]Failed to create session: {response.text}[/red]")
            raise typer.Exit(1)
        session = response.json()

    rprint(f"[green]✓ Created session:[/green] {session.get('title')}")
    rprint(f"  Room ID: {session.get('id')}")
    rprint(f"  Demo: {demo.get('title')}")


@app.command("sessions")
def list_sessions(
    status_filter: Annotated[str, typer.Option("--status", "-s", help="Filter by status: active|archived|ended")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed info")] = False,
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
    limit: Annotated[int, typer.Option(help="Max results")] = 20,
):
    """List your demo sessions."""
    params: dict[str, Any] = {"limit": limit}
    if status_filter:
        params["status_filter"] = status_filter

    with get_client() as client:
        response = client.get("/sessions", params=params)
        response.raise_for_status()
        data = response.json()

    sessions = data.get("data", [])
    count = data.get("count", len(sessions))

    if show_json:
        console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))
        return

    if not sessions:
        rprint("[dim]No demo sessions found[/dim]")
        return

    table = Table(title=f"Demo Sessions ({count} total)", show_lines=verbose)
    table.add_column("ID", style="dim")
    table.add_column("Demo Config", style="cyan")
    table.add_column("Room ID", style="green")
    table.add_column("Status")
    table.add_column("Auto-respond")
    if verbose:
        table.add_column("Last Accessed")

    for sess in sessions:
        status = sess.get("status", "-")
        status_color = {"active": "green", "archived": "yellow", "ended": "dim"}.get(status, "white")
        row = [
            str(sess.get("id", ""))[:8],
            str(sess.get("demo_config_id", ""))[:8],
            str(sess.get("room_id", ""))[:8],
            f"[{status_color}]{status}[/{status_color}]",
            "✓" if sess.get("auto_respond") else "✗",
        ]
        if verbose:
            row.append(sess.get("last_accessed_at", "-")[:19] if sess.get("last_accessed_at") else "-")
        table.add_row(*row)

    console.print(table)


@app.command("session-get")
def get_session(
    session_id: Annotated[str, typer.Argument(help="Demo session ID")],
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Get details of a specific demo session."""
    with get_client() as client:
        response = client.get(f"/sessions/{session_id}")
        if response.status_code == 404:
            rprint(f"[red]Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        if response.status_code == 403:
            rprint(f"[red]Access denied - you don't own this session[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        sess = response.json()

    if show_json:
        console.print(Syntax(json.dumps(sess, indent=2), "json", theme="monokai"))
        return

    rprint(Panel(f"[bold]Demo Session[/bold]", subtitle=f"ID: {sess.get('id')}"))
    rprint(f"  Demo Config: [cyan]{sess.get('demo_config_id')}[/cyan]")
    rprint(f"  Room ID: [green]{sess.get('room_id')}[/green]")
    rprint(f"  Status: {sess.get('status', '-')}")
    rprint(f"  Auto-respond: {'✓ enabled' if sess.get('auto_respond') else '✗ disabled'}")
    rprint(f"  Created: {sess.get('created_at', '-')[:19] if sess.get('created_at') else '-'}")
    rprint(f"  Last Accessed: {sess.get('last_accessed_at', '-')[:19] if sess.get('last_accessed_at') else '-'}")


@app.command("session-update")
def update_session(
    session_id: Annotated[str, typer.Argument(help="Demo session ID")],
    auto_respond: Annotated[bool, typer.Option("--auto-respond/--no-auto-respond", help="Enable/disable auto-respond")] = None,
    status: Annotated[str, typer.Option("--status", "-s", help="Set status: active|archived|ended")] = None,
):
    """Update a demo session's settings."""
    update_payload: dict[str, Any] = {}
    if auto_respond is not None:
        update_payload["auto_respond"] = auto_respond
    if status is not None:
        if status not in ("active", "archived", "ended"):
            rprint(f"[red]Invalid status: {status}. Must be active|archived|ended[/red]")
            raise typer.Exit(1)
        update_payload["status"] = status

    if not update_payload:
        rprint("[yellow]No updates specified. Use --auto-respond/--no-auto-respond or --status[/yellow]")
        raise typer.Exit(1)

    with get_client() as client:
        response = client.patch(f"/sessions/{session_id}", json=update_payload)
        if response.status_code == 404:
            rprint(f"[red]Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        if response.status_code == 403:
            rprint(f"[red]Access denied - you don't own this session[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        sess = response.json()

    rprint(f"[green]✓ Updated session {session_id[:8]}...[/green]")
    rprint(f"  Status: {sess.get('status', '-')}")
    rprint(f"  Auto-respond: {'✓ enabled' if sess.get('auto_respond') else '✗ disabled'}")


@app.command("session-delete")
def delete_session(
    session_id: Annotated[str, typer.Argument(help="Demo session ID")],
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete a demo session."""
    if not force:
        confirm = typer.confirm(f"Delete session {session_id}?")
        if not confirm:
            raise typer.Abort()

    with get_client() as client:
        response = client.delete(f"/sessions/{session_id}")
        if response.status_code == 404:
            rprint(f"[red]Session not found: {session_id}[/red]")
            raise typer.Exit(1)
        if response.status_code == 403:
            rprint(f"[red]Access denied - you don't own this session[/red]")
            raise typer.Exit(1)
        response.raise_for_status()

    rprint(f"[green]✓ Deleted session: {session_id}[/green]")


@app.command("session-resolve")
def resolve_session(
    demo_slug: Annotated[str, typer.Argument(help="Demo slug (e.g., 'my-demo')")],
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Output as JSON")] = False,
):
    """Get or create a demo session by slug.

    This is the CLI equivalent of visiting /demo/{slug} in the browser.
    If you already have a session for this demo, it returns it.
    Otherwise, it creates a new session with a backing room.
    """
    with get_client() as client:
        response = client.post(f"/{demo_slug}/session")
        if response.status_code == 404:
            rprint(f"[red]Demo not found: {demo_slug}[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        data = response.json()

    if show_json:
        console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))
        return

    demo_config = data.get("demo_config", {})
    demo_session = data.get("demo_session", {})
    created = data.get("created", False)

    action = "Created new" if created else "Resolved existing"
    rprint(f"[green]✓ {action} session for '{demo_slug}'[/green]")
    rprint(f"\n  [bold]Demo Config:[/bold]")
    rprint(f"    ID: [cyan]{demo_config.get('id', '-')}[/cyan]")
    rprint(f"    Title: {demo_config.get('title', '-')}")
    rprint(f"    Scope: {demo_config.get('scope', '-')}")
    rprint(f"\n  [bold]Session:[/bold]")
    rprint(f"    ID: [green]{demo_session.get('id', '-')}[/green]")
    rprint(f"    Room ID: {demo_session.get('room_id', '-')}")
    rprint(f"    Status: {demo_session.get('status', '-')}")
    rprint(f"    Auto-respond: {'✓' if demo_session.get('auto_respond') else '✗'}")

    # Show composition if available
    composition = data.get("composition")
    if composition:
        rprint(f"\n  [bold]Composition:[/bold]")
        rprint(f"    Layout: {composition.get('layout_mode', '-')}")
        rprint(f"    Panels: {len(composition.get('panels', []))}")


@app.command("composition")
def view_composition(
    demo_id: Annotated[str, typer.Argument(help="Demo config ID")],
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Show raw JSON")] = False,
):
    """View demo composition details."""
    with get_client() as client:
        response = client.get(f"/configs/{demo_id}/composition")
        if response.status_code == 404:
            rprint(f"[red]Demo or composition not found: {demo_id}[/red]")
            raise typer.Exit(1)
        response.raise_for_status()
        comp = response.json()

    if show_json:
        console.print(Syntax(json.dumps(comp, indent=2), "json", theme="monokai"))
        return

    rprint(Panel(f"[bold]Composition[/bold]", subtitle=f"Demo: {demo_id[:8]}..."))
    rprint(f"  Layout: [cyan]{comp.get('layout_mode', '-')}[/cyan]")
    rprint(f"  Panels: {len(comp.get('panels', []))}")
    rprint(f"  Blocks: {len(comp.get('blocks', []))}")

    pres = comp.get("presentation_json", {})
    if pres:
        rprint(f"\n  [bold]Styling:[/bold]")
        if pres.get("backgrounds", {}).get("page_gradient"):
            rprint(f"    ✓ Page gradient")
        if pres.get("backgrounds", {}).get("svg_overlay"):
            rprint(f"    ✓ SVG overlay: {pres['backgrounds']['svg_overlay']}")
        if pres.get("effects", {}).get("card_glow"):
            rprint(f"    ✓ Card glow")
        if pres.get("callouts"):
            rprint(f"    ✓ Callouts: {list(pres['callouts'].keys())}")
        if pres.get("motion"):
            rprint(f"    ✓ Motion: {pres['motion'].get('panel_enter_ms', '?')}ms enter")
        if pres.get("typography"):
            rprint(f"    ✓ Typography: {pres['typography'].get('size', '?')} size")


# ============================================================================
# QUICK CREATE - All in one
# ============================================================================


@app.command("quick")
def quick_create(
    title: Annotated[str, typer.Argument(help="Demo title")],
    preset: Annotated[str, typer.Option("--preset", "-p", help="Styling preset")] = "neon-pulse",
    with_session: Annotated[bool, typer.Option("--session", "-s", help="Also create a session")] = False,
):
    """Quick-create a styled demo with optional session."""
    if preset not in STYLING_PRESETS:
        rprint(f"[red]Unknown preset: {preset}[/red]")
        raise typer.Exit(1)

    preset_data = STYLING_PRESETS[preset]
    slug = title.lower().replace(" ", "-")

    # Step 1: Create demo config
    demo_payload = {
        "title": title,
        "slug": slug,
        "scope": "personal",
    }

    # Build composition data
    composition_data = {
        "schema_version": 1,
        "layout_mode": "panels",
        "runtime_policy": "auto",
        "presentation_json": preset_data["composition"],
        "panels": [
            {
                "id": "main-chat",
                "kind": "chat",
                "prominence": "primary",
                "order": 1,
                "title": "Chat",
                "presentation_json": preset_data.get("chat_panel", {}),
                "default_size": 60,
                "min_size": 30,
                "viewport_mode": "panel",
                "options": {"mode": "participant"},
            },
        ],
        "blocks": [],
    }

    with get_client() as client:
        # Create demo
        response = client.post("/", json=demo_payload)
        if response.status_code not in (200, 201):
            rprint(f"[red]Failed: {response.text}[/red]")
            raise typer.Exit(1)
        demo = response.json()
        demo_id = demo.get("id")

        rprint(f"[green]✓ Created:[/green] {demo.get('title')}")
        rprint(f"  ID: {demo_id}")

        # Step 2: Set composition
        comp_response = client.put(
            f"/configs/{demo_id}/composition",
            json=composition_data,
        )
        if comp_response.status_code in (200, 201):
            rprint(f"  Preset: [cyan]{preset}[/cyan] ✓")
        else:
            rprint(f"  [yellow]Warning: Composition not set: {comp_response.text[:100]}[/yellow]")

        # Step 3: Optionally create session
        if with_session:
            session_response = client.post(
                "/sessions",
                json={
                    "demo_config_id": str(demo_id),
                },
            )
            if session_response.status_code in (200, 201):
                session = session_response.json()
                rprint(f"  Session: {session.get('id')}")


if __name__ == "__main__":
    app()
