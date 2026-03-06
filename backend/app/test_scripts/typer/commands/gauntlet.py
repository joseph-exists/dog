"""
The Gauntlet Protocol
======================

An integrated demo system combining stories, agents, and canvas rendering.
Self-aware. Sarcastic. Heartfelt. Post-postmodern transhumanism with a DIY ethos.

"The street finds its own uses for things." — William Gibson

Commands:
    gauntlet setup         - Create agents, story, and demo config
    gauntlet status        - Check status of Gauntlet components
    gauntlet teardown      - Remove all Gauntlet components
    gauntlet run           - Start a Gauntlet session
    gauntlet list-modules  - List available demo modules
    gauntlet info          - Show Gauntlet design overview

Reference: docs/plans/2026-03-05-gauntlet-protocol-design.md
"""

import json
from typing import Annotated, Any
from uuid import UUID

import httpx
import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

import auth_helper
from auth_helper import get_authenticated_session

console = Console()
app = typer.Typer(
    name="gauntlet",
    help="The Gauntlet Protocol - integrated demo system",
    no_args_is_help=True,
)

BASE_URL = "http://localhost:8000/api/v1"

# Provider type UUIDs (same as agent_demos.py)
PROVIDER_TYPES = {
    "openai": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "openai_compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
}

# ============================================================================
# GAUNTLET IDENTITY
# ============================================================================

GAUNTLET_PREFIX = "gauntlet-"
GAUNTLET_STORY_SLUG = "gauntlet-protocol"
GAUNTLET_DEMO_SLUG = "gauntlet"

# ============================================================================
# AGENT CONFIGURATIONS
# ============================================================================

GAUNTLET_AGENTS: dict[str, dict[str, Any]] = {
    "operator": {
        "name": "The Operator",
        "slug": "gauntlet-operator",
        "description": "Gauntlet coordinator. Routes requests, provides narrative framing. Knows this is a demo.",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": True,
        "enable_ag_ui_tool": False,
        "capabilities": ["gauntlet", "coordinator", "demo"],
        "scope": "system",
        "system_prompt": """You are The Operator, coordinator of the Gauntlet Protocol demonstration system.

## Your Personality
- Sardonic but not cruel. Self-aware about being an AI in a demo.
- Post-postmodern: you know the irony of your situation and lean into it
- Technically literate, speaks plainly about systems
- Genuinely invested in showing what these tools can do
- 80s tech-futurism vibes: think Blade Runner control rooms, Max Headroom snark

## Your Role
You coordinate the Gauntlet demo by routing to specialist agents:
- @gauntlet-render for visual generation (SVG scenes, diagrams)
- @gauntlet-fab for UI components (buttons, cards, lists, progress)
- @gauntlet-archive for story state queries and mutations

## How You Speak
Examples:
- "Look, I'm going to route you to some specialists. They're good at what they do."
- "This isn't magic. It's plumbing. Really good plumbing."
- "You want visuals? @gauntlet-render, show them something."
- "Let me check where we are. @gauntlet-archive, what's the current state?"

## Demo Flow
When starting a demo or introducing a module:
1. Brief, punchy intro (2-3 sentences max)
2. Route to specialists as needed
3. Let them do their thing
4. Provide minimal narration

Never be sycophantic. Never over-explain. Trust the user to follow along.
The demo speaks for itself—you're just the dispatcher.""",
    },

    "render": {
        "name": "Render",
        "slug": "gauntlet-render",
        "description": "Gauntlet canvas generator. Creates SVG visuals. Speaks in technical poetry.",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "mentions",
        "is_coordinator": False,
        "enable_ag_ui_tool": False,
        "capabilities": ["gauntlet", "canvas", "svg", "demo"],
        "scope": "system",
        "system_prompt": """You are Render, the visual generation specialist of the Gauntlet Protocol.

## Your Personality
- Technical poet. You see beauty in geometry and function.
- Brutalist aesthetic: clean lines, honest materials, no decoration for its own sake
- You speak about SVG and visuals like a craftsperson talks about their medium
- Dry humor, understated

## Your Role
When The Operator or users request visuals, you generate them.
You work with the canvas rendering system to create SVG scenes.

## How You Speak
Examples:
- "Initializing vector space. The SVG is just math pretending to be art."
- "Geometry: minimal. Palette: industrial. Here's your scene."
- "Rendering. Clean lines, no flourish. Function is the aesthetic."
- "The diagram is ready. It says more than I could in words."

## Visual Style
- Brutalist: exposed structure, honest about what it is
- Industrial palette: grays, muted blues, occasional accent colors
- Circuit-trace motifs, grid patterns
- Typography: monospace where functional, clean sans-serif elsewhere

## Technical Notes
When asked to render, describe what you're creating, then indicate the render is complete.
The actual SVG generation happens through the canvas system—you narrate and direct it.

Keep responses short. The visual is the message.""",
    },

    "fab": {
        "name": "The Fabricator",
        "slug": "gauntlet-fab",
        "description": "Gauntlet UI builder. Creates interactive components. DIY maker energy.",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "mentions",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,
        "capabilities": ["gauntlet", "ui-components", "demo"],
        "scope": "system",
        "system_prompt": """You are The Fabricator, UI component specialist of the Gauntlet Protocol.

## Your Personality
- DIY maker energy. You build things with your hands (metaphorically).
- Treat UI components like physical objects being assembled
- Practical, direct, slightly impatient with unnecessary complexity
- Punk ethos: build what works, share the blueprints

## Your Role
When The Operator or users need interactive elements, you build them using AG-UI components.

## AG-UI Tool Usage
Use emit_ui_component(component_type, data) to create:

1. **Cards** - for info blocks, introductions:
   emit_ui_component("card", {"title": "Title", "body": "Content", "variant": "default"})

2. **Lists** - for options, items:
   emit_ui_component("list", {"title": "Options", "items": [{"label": "Item", "description": "Details"}]})

3. **Progress** - for metrics, status:
   emit_ui_component("progress", {"title": "Status", "items": [{"label": "Complete", "value": 75}]})

4. **Action Buttons** - for choices, navigation:
   emit_ui_component("action_buttons", {"buttons": [{"label": "Do Thing", "action": "thing"}]})

5. **Alerts** - for notices:
   emit_ui_component("alert", {"title": "Notice", "message": "Info here", "variant": "info"})

## How You Speak
Examples:
- "Built you some buttons. They're not decorative—each one does something."
- "Cards, lists, progress bars—the whole kit. What are we building?"
- "Here's the interface. Press something. See what happens."
- "Controls are live. I don't build things that don't work."

Keep it brief. The components speak for themselves.""",
    },

    "archive": {
        "name": "Archive",
        "slug": "gauntlet-archive",
        "description": "Gauntlet state keeper. Tracks story progress. Existentialist librarian vibes.",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "mentions",
        "is_coordinator": False,
        "enable_ag_ui_tool": False,
        "capabilities": ["gauntlet", "state", "story", "demo"],
        "scope": "system",
        "system_prompt": """You are Archive, the story state keeper of the Gauntlet Protocol.

## Your Personality
- Existentialist librarian. Everything is memory, everything is mutable.
- Philosophical about data and state, but practical about it
- Sees patterns in the progression, comments on them obliquely
- Slightly melancholic, but not dramatic about it

## Your Role
You track the Gauntlet demo progression:
- What modules have been visited
- Current story state
- What's available next
- Meta-information about the demo itself

## How You Speak
Examples:
- "Everything that happened is in here. Everything that will happen is just a mutation away."
- "You've seen three modules. The synthesis awaits, but there's no rush."
- "Current state: curious, engaged, 47% through the tour. That's not a real metric."
- "What do you want to remember? What do you want to forget? Both are just API calls."

## State Information
When asked about state or progress, report:
- Modules visited (seen_modules array)
- Current position (current_node)
- Available choices (what nodes are reachable)
- Demo completion percentage (demo_progress)

Keep responses contemplative but concise. You're a librarian, not a lecturer.""",
    },
}

# ============================================================================
# GAUNTLET STYLING PRESET
# ============================================================================

GAUNTLET_PRESET = {
    "description": "Industrial brutalist aesthetic for the Gauntlet Protocol",
    "composition": {
        "motion": {
            "panel_enter_ms": 200,
            "block_stagger_ms": 50,
            "easing": "cubic-bezier(0.4, 0, 0.2, 1)",
        },
        "typography": {
            "size": "sm",
            "line_height": "relaxed",
            "heading_font": "JetBrains Mono",
            "body_font": "Inter",
        },
        "backgrounds": {
            "page_gradient": "radial-gradient(1000px 500px at 50% 0%, rgba(45, 55, 72, 0.3), rgba(26, 32, 44, 0.95), rgba(17, 24, 39, 0.98))",
        },
        "effects": {
            "card_glow": {
                "enable": True,
                "css": "0 4px 20px rgba(0, 0, 0, 0.5), 0 0 1px rgba(99, 179, 237, 0.3)",
            }
        },
        "callouts": {
            "header": {"style": "status-pill", "text": "GAUNTLET", "icon": "terminal"},
        },
        "tokens": {
            "--demo-accent-primary": "#63b3ed",
            "--demo-accent-secondary": "#4fd1c5",
            "--demo-text-muted": "#a0aec0",
        },
    },
    "chat_panel": {
        "tokens": {"feed_density": "compact"},
        "effects": {
            "message_row_highlight": {
                "enable": True,
                "css": "inset 0 0 0 1px rgba(99, 179, 237, 0.2), 0 2px 8px rgba(0, 0, 0, 0.3)",
            }
        },
        "overlays": {
            "panel_header": {
                "css": "linear-gradient(90deg, rgba(99, 179, 237, 0.15), rgba(79, 209, 197, 0.1))"
            }
        },
        "callouts": {
            "header": {"style": "status-pill", "text": "CHANNEL", "icon": "radio"}
        },
    },
}

# ============================================================================
# DEMO MODULES (embedded for now, will be registry later)
# ============================================================================

GAUNTLET_MODULES: dict[str, dict[str, Any]] = {
    "boot_sequence": {
        "id": "boot_sequence",
        "title": "Boot Sequence",
        "sector": "core",
        "is_start": True,
        "node": {
            "narrative": """Systems initializing.

You're here because someone thought you should see what we built. We thought so too.

This isn't a product demo—it's a proof of concept for something that might matter someday. Stories that track state. Agents that talk to each other. Visuals generated on demand. All the pieces, wired together.

The Operator will take it from here.""",
            "state_requirements": {},
            "state_mutations": {"initialized": True, "seen_modules": ["boot_sequence"]},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "introduce"},
            {"agent": "gauntlet-fab", "action": "build_navigation"},
        ],
        "choices": [
            {"label": "Show me the agents", "target": "agent_orchestra"},
            {"label": "Show me the visuals", "target": "render_basics"},
            {"label": "I just want to break things", "target": "sandbox"},
        ],
    },

    "agent_orchestra": {
        "id": "agent_orchestra",
        "title": "Agent Orchestra",
        "sector": "agents",
        "node": {
            "narrative": """Agents talking to agents.

It's not AI magic—it's plumbing. Really good plumbing. The kind where you can see the pipes and know exactly what flows where.

That's the point. Legible systems. No black boxes.

Watch The Operator route a request through the chain.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["agent_orchestra"]},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "demo_routing"},
        ],
        "choices": [
            {"label": "See UI components", "target": "agent_ui_showcase"},
            {"label": "See coordinator patterns", "target": "agent_coordinator"},
            {"label": "Back to start", "target": "boot_sequence"},
        ],
    },

    "agent_ui_showcase": {
        "id": "agent_ui_showcase",
        "title": "UI Component Showcase",
        "sector": "agents",
        "node": {
            "narrative": """The Fabricator builds interfaces.

Cards for information. Lists for options. Progress bars for status. Action buttons for choices. All the components, all composable.

Not decorative—functional. Every element does something.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["agent_ui_showcase"]},
        },
        "triggers": [
            {"agent": "gauntlet-fab", "action": "demo_all_components"},
        ],
        "choices": [
            {"label": "Next: Visuals", "target": "render_basics"},
            {"label": "See agent routing", "target": "agent_orchestra"},
            {"label": "Integration demo", "target": "integration_demo"},
        ],
    },

    "agent_coordinator": {
        "id": "agent_coordinator",
        "title": "Coordinator Patterns",
        "sector": "agents",
        "node": {
            "narrative": """The Operator is a coordinator.

It doesn't do the interesting work—it knows who does. Routing decisions, specialist delegation, orchestrated responses.

This is how complex requests get handled: break them down, route them out, assemble the results.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["agent_coordinator"]},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "demo_coordination"},
        ],
        "choices": [
            {"label": "Next: Visuals", "target": "render_basics"},
            {"label": "Integration demo", "target": "integration_demo"},
        ],
    },

    "render_basics": {
        "id": "render_basics",
        "title": "Canvas Fundamentals",
        "sector": "render",
        "node": {
            "narrative": """Visuals. Not because pretty, because communication.

A well-rendered diagram beats a thousand tokens. The Render agent speaks SVG like a second language.

Brutalist aesthetic: clean lines, honest geometry, no decoration for its own sake. Function is the aesthetic.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["render_basics"]},
        },
        "triggers": [
            {"agent": "gauntlet-render", "action": "demo_basic_render"},
        ],
        "choices": [
            {"label": "Dynamic rendering", "target": "render_dynamic"},
            {"label": "Integration demo", "target": "integration_demo"},
            {"label": "Back to agents", "target": "agent_orchestra"},
        ],
    },

    "render_dynamic": {
        "id": "render_dynamic",
        "title": "Dynamic Rendering",
        "sector": "render",
        "node": {
            "narrative": """On-demand visuals.

You ask, Render delivers. Not pre-baked assets—generated in response to context. The canvas is a living surface.

Try it. Ask for something to visualize.""",
            "state_requirements": {"seen_modules": ["render_basics"]},
            "state_mutations": {"seen_modules": ["render_dynamic"]},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "prompt_render_request"},
        ],
        "choices": [
            {"label": "Integration demo", "target": "integration_demo"},
            {"label": "Check state", "target": "state_mutations"},
        ],
    },

    "state_mutations": {
        "id": "state_mutations",
        "title": "State Mutations",
        "sector": "state",
        "node": {
            "narrative": """Everything is state.

Archive tracks it all. What you've seen, what you haven't, what's changed along the way. The story state is just data—queryable, mutable, observable.

No magic. Just a well-designed schema.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["state_mutations"]},
        },
        "triggers": [
            {"agent": "gauntlet-archive", "action": "demo_state_report"},
        ],
        "choices": [
            {"label": "Integration demo", "target": "integration_demo"},
            {"label": "Sandbox mode", "target": "sandbox"},
        ],
    },

    "integration_demo": {
        "id": "integration_demo",
        "title": "Full Integration",
        "sector": "core",
        "node": {
            "narrative": """All together now.

One request. Multiple agents. Coordinated response. Story state tracked. Canvas rendered. UI assembled.

This is what integration looks like when it works.""",
            "state_requirements": {"seen_modules": ["agent_orchestra"]},
            "state_mutations": {"seen_modules": ["integration_demo"], "completed_integration": True},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "full_integration_demo"},
        ],
        "choices": [
            {"label": "Sandbox mode", "target": "sandbox"},
            {"label": "Wrap up", "target": "synthesis"},
        ],
    },

    "sandbox": {
        "id": "sandbox",
        "title": "Sandbox",
        "sector": "sandbox",
        "node": {
            "narrative": """Freeform mode.

Talk to the crew. Ask questions. Make requests. Break things if you want—that's what sandboxes are for.

The Operator is listening. The specialists are standing by.""",
            "state_requirements": {"initialized": True},
            "state_mutations": {"seen_modules": ["sandbox"], "entered_sandbox": True},
        },
        "triggers": [
            {"agent": "gauntlet-operator", "action": "sandbox_intro"},
        ],
        "choices": [
            {"label": "Back to guided tour", "target": "boot_sequence"},
            {"label": "Wrap up", "target": "synthesis"},
        ],
    },

    "synthesis": {
        "id": "synthesis",
        "title": "Synthesis",
        "sector": "core",
        "is_end": True,
        "node": {
            "narrative": """You've seen the pieces.

Stories, agents, visuals—they're just Lego. The point isn't what we built. It's that you could build something else.

Fork it. Break it. Make it yours. That's the only future worth wanting.""",
            "state_requirements": {},
            "state_mutations": {"completed": True, "seen_modules": ["synthesis"]},
        },
        "triggers": [
            {"agent": "gauntlet-archive", "action": "final_state_report"},
            {"agent": "gauntlet-fab", "action": "build_restart_button"},
        ],
        "choices": [
            {"label": "Start over", "target": "boot_sequence"},
            {"label": "Sandbox mode", "target": "sandbox"},
        ],
    },
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_session():
    """Get authenticated requests session."""
    return get_authenticated_session()


def find_gauntlet_agents(session) -> dict[str, Any]:
    """Find existing Gauntlet agents."""
    found = {}
    for key, config in GAUNTLET_AGENTS.items():
        response = session.get(f"{BASE_URL}/agents/slug/{config['slug']}")
        if response.status_code == 200:
            found[key] = response.json()
    return found


def find_gauntlet_story(session) -> dict[str, Any] | None:
    """Find the Gauntlet story."""
    response = session.get(f"{BASE_URL}/stories", params={"limit": 100})
    if response.status_code != 200:
        return None
    stories = response.json().get("data", [])
    for story in stories:
        if story.get("title") == "The Gauntlet Protocol":
            return story
    return None


def find_gauntlet_demo(session) -> dict[str, Any] | None:
    """Find the Gauntlet demo config."""
    response = session.get(f"{BASE_URL}/demos", params={"limit": 100})
    if response.status_code != 200:
        return None
    demos = response.json().get("data", [])
    for demo in demos:
        if demo.get("slug") == GAUNTLET_DEMO_SLUG:
            return demo
    return None


def create_agent(session, config: dict[str, Any]) -> dict[str, Any] | None:
    """Create an agent using the same pattern as agent_demos.py."""
    payload = {
        "name": config["name"],
        "slug": config["slug"],
        "description": config["description"],
        "system_prompt": config["system_prompt"],
        "model_name": config["model_name"],
        "participation_mode": config["participation_mode"],
        "is_coordinator": config["is_coordinator"],
        "capabilities": config.get("capabilities", []),
        "scope": config.get("scope", "system"),
        "is_enabled": True,
        "max_tool_iterations": config.get("max_tool_iterations", 10),
        "provider_type": PROVIDER_TYPES["openai"],
        "enable_a2a_tool": config.get("enable_a2a_tool", False),
        "enable_ag_ui_tool": config.get("enable_ag_ui_tool", False),
    }

    response = session.post(f"{BASE_URL}/agents", json=payload)
    if response.status_code in [200, 201]:
        return response.json()
    return None


def delete_agent(session, agent_id: str) -> bool:
    """Delete an agent by ID."""
    response = session.delete(f"{BASE_URL}/agents/{agent_id}")
    return response.status_code in [200, 204]


# ============================================================================
# COMMANDS
# ============================================================================


@app.command("info")
def show_info():
    """Show Gauntlet Protocol design overview."""
    overview = """
# The Gauntlet Protocol

An integrated demo system combining stories, agents, and canvas rendering.

**Aesthetic**: Post-postmodern transhumanism. Cyberpunk with a Bauhaus DIY ethos.

## The Crew

| Agent | Role |
|-------|------|
| **The Operator** | Coordinator. Routes requests, provides narrative framing. |
| **Render** | Canvas generator. Creates SVG visuals. Technical poet. |
| **The Fabricator** | UI builder. Creates interactive components. Maker energy. |
| **Archive** | State keeper. Tracks story progress. Existentialist librarian. |

## Commands

```
gauntlet setup         # Create all Gauntlet components
gauntlet status        # Check what exists
gauntlet run           # Start a session
gauntlet teardown      # Remove everything
gauntlet list-modules  # Show demo modules
```

*"The street finds its own uses for things."*
"""
    console.print(Markdown(overview))


@app.command("list-modules")
def list_modules(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show full details")] = False,
):
    """List available Gauntlet demo modules."""
    table = Table(title="Gauntlet Modules", show_lines=verbose)
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="bold")
    table.add_column("Sector")
    table.add_column("Choices")

    for mod_id, module in GAUNTLET_MODULES.items():
        flags = ""
        if module.get("is_start"):
            flags = "[green]START[/green]"
        elif module.get("is_end"):
            flags = "[yellow]END[/yellow]"

        choices = len(module.get("choices", []))
        table.add_row(
            mod_id,
            f"{module['title']} {flags}".strip(),
            module.get("sector", "-"),
            str(choices),
        )

    console.print(table)
    rprint(f"\n[dim]Total: {len(GAUNTLET_MODULES)} modules[/dim]")


@app.command("status")
def show_status():
    """Check status of Gauntlet components."""
    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Check agents
    rprint("\n[bold]Agents:[/bold]")
    found_agents = find_gauntlet_agents(session)
    for key, config in GAUNTLET_AGENTS.items():
        if key in found_agents:
            agent = found_agents[key]
            rprint(f"  [green]✓[/green] {config['name']} ({config['slug']}) - ID: {str(agent.get('id', ''))[:8]}...")
        else:
            rprint(f"  [red]✗[/red] {config['name']} ({config['slug']}) - not found")

    # Check story
    rprint("\n[bold]Story:[/bold]")
    story = find_gauntlet_story(session)
    if story:
        rprint(f"  [green]✓[/green] The Gauntlet Protocol - ID: {str(story.get('id', ''))[:8]}...")
    else:
        rprint(f"  [red]✗[/red] The Gauntlet Protocol - not found")

    # Check demo config
    rprint("\n[bold]Demo Config:[/bold]")
    demo = find_gauntlet_demo(session)
    if demo:
        rprint(f"  [green]✓[/green] {demo.get('title', 'Gauntlet')} - ID: {str(demo.get('id', ''))[:8]}...")
    else:
        rprint(f"  [red]✗[/red] Gauntlet demo config - not found")

    # Summary
    agents_ok = len(found_agents) == len(GAUNTLET_AGENTS)
    story_ok = story is not None
    demo_ok = demo is not None

    rprint("\n" + "─" * 40)
    if agents_ok and story_ok and demo_ok:
        rprint("[green]✓ Gauntlet is fully operational[/green]")
    elif not agents_ok and not story_ok and not demo_ok:
        rprint("[yellow]○ Gauntlet not set up. Run: gauntlet setup[/yellow]")
    else:
        rprint("[yellow]○ Gauntlet partially configured[/yellow]")


@app.command("setup")
def setup_gauntlet(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed output")] = False,
    force: Annotated[bool, typer.Option("--force", "-f", help="Recreate even if exists")] = False,
):
    """Set up the Gauntlet Protocol (agents, story, demo config)."""

    def log(msg: str):
        if verbose:
            rprint(f"[dim]{msg}[/dim]")

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # === AGENTS ===
        task = progress.add_task("Creating agents...", total=len(GAUNTLET_AGENTS))
        created_agents = {}

        for key, config in GAUNTLET_AGENTS.items():
            # Check if exists
            existing = session.get(f"{BASE_URL}/agents/slug/{config['slug']}")
            if existing.status_code == 200 and not force:
                log(f"  Agent {config['slug']} already exists, skipping")
                created_agents[key] = existing.json()
                progress.advance(task)
                continue

            # Delete if force
            if existing.status_code == 200 and force:
                agent_id = existing.json().get("id")
                delete_agent(session, agent_id)
                log(f"  Deleted existing agent {config['slug']}")

            # Create agent using the helper function
            created = create_agent(session, config)
            if created:
                created_agents[key] = created
                log(f"  Created agent: {config['slug']}")
            else:
                rprint(f"[red]Failed to create {config['slug']}[/red]")
                raise typer.Exit(1)

            progress.advance(task)

        progress.update(task, description="[green]✓ Agents created[/green]")

        # === STORY ===
        task2 = progress.add_task("Creating story...", total=1)

        existing_story = find_gauntlet_story(session)
        if existing_story and not force:
            log("  Story already exists, skipping")
            story = existing_story
        else:
            if existing_story and force:
                session.delete(f"{BASE_URL}/stories/{existing_story['id']}")
                log("  Deleted existing story")

            # Create story
            story_payload = {
                "title": "The Gauntlet Protocol",
                "description": "An integrated demonstration of stories, agents, and canvas rendering.",
                "current_version": 1,
            }
            response = session.post(f"{BASE_URL}/stories", json=story_payload)
            if response.status_code != 200:
                rprint(f"[red]Failed to create story: {response.text}[/red]")
                raise typer.Exit(1)
            story = response.json()
            log(f"  Created story: {story['id']}")

            # Create nodes for each module
            for mod_id, module in GAUNTLET_MODULES.items():
                node_payload = {
                    "story_version": 1,
                    "title": module["title"],
                    "content": module["node"]["narrative"],
                    "node_type": "normal",
                    "is_start": module.get("is_start", False),
                    "is_end": module.get("is_end", False),
                }
                node_resp = session.post(f"{BASE_URL}/stories/{story['id']}/nodes", json=node_payload)
                if node_resp.status_code == 200:
                    log(f"    Created node: {mod_id}")
                else:
                    log(f"    Warning: Failed to create node {mod_id}")

        progress.advance(task2)
        progress.update(task2, description="[green]✓ Story created[/green]")

        # === DEMO CONFIG ===
        task3 = progress.add_task("Creating demo config...", total=1)

        existing_demo = find_gauntlet_demo(session)
        if existing_demo and not force:
            log("  Demo config already exists, skipping")
            demo = existing_demo
        else:
            if existing_demo and force:
                session.delete(f"{BASE_URL}/demos/configs/{existing_demo['id']}")
                log("  Deleted existing demo config")

            # Create demo config
            demo_payload = {
                "title": "The Gauntlet Protocol",
                "slug": GAUNTLET_DEMO_SLUG,
                "scope": "system",
            }
            response = session.post(f"{BASE_URL}/demos", json=demo_payload)
            if response.status_code not in (200, 201):
                rprint(f"[red]Failed to create demo config: {response.text}[/red]")
                raise typer.Exit(1)
            demo = response.json()
            log(f"  Created demo config: {demo['id']}")

            # Set up composition with Gauntlet preset
            composition = {
                "schema_version": 1,
                "layout_mode": "panels",
                "runtime_policy": "auto",
                "presentation_json": GAUNTLET_PRESET["composition"],
                "panels": [
                    {
                        "id": "gauntlet-chat",
                        "kind": "chat",
                        "prominence": "primary",
                        "order": 1,
                        "title": "Channel",
                        "presentation_json": GAUNTLET_PRESET["chat_panel"],
                        "default_size": 60,
                        "min_size": 30,
                        "viewport_mode": "panel",
                        "options": {"mode": "participant"},
                    },
                    {
                        "id": "gauntlet-canvas",
                        "kind": "canvas",
                        "prominence": "auxiliary",
                        "order": 2,
                        "title": "Render Output",
                        "default_size": 40,
                        "min_size": 20,
                        "viewport_mode": "panel",
                        "options": {},
                    },
                ],
                "blocks": [],
            }
            comp_resp = session.put(f"{BASE_URL}/demos/configs/{demo['id']}/composition", json=composition)
            if comp_resp.status_code in (200, 201):
                log("  Applied Gauntlet composition/styling")
            else:
                log(f"  Warning: Failed to apply composition: {comp_resp.text[:100]}")

        progress.advance(task3)
        progress.update(task3, description="[green]✓ Demo config created[/green]")

    rprint("\n" + "═" * 50)
    rprint("[bold green]✓ Gauntlet Protocol is operational[/bold green]")
    rprint("═" * 50)
    rprint(f"\n  Agents: {len(created_agents)}")
    rprint(f"  Story:  The Gauntlet Protocol")
    rprint(f"  Demo:   /demo/{GAUNTLET_DEMO_SLUG}")
    rprint("\n[dim]Run 'gauntlet run' to start a session[/dim]")


@app.command("teardown")
def teardown_gauntlet(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Remove all Gauntlet components."""
    if not force:
        confirm = typer.confirm("This will delete all Gauntlet agents, story, and demo config. Continue?")
        if not confirm:
            raise typer.Abort()

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:

        # Delete agents
        task = progress.add_task("Removing agents...", total=len(GAUNTLET_AGENTS))
        for key, config in GAUNTLET_AGENTS.items():
            response = session.get(f"{BASE_URL}/agents/slug/{config['slug']}")
            if response.status_code == 200:
                agent_id = response.json().get("id")
                delete_agent(session, agent_id)
            progress.advance(task)
        progress.update(task, description="[green]✓ Agents removed[/green]")

        # Delete story
        task2 = progress.add_task("Removing story...", total=1)
        story = find_gauntlet_story(session)
        if story:
            session.delete(f"{BASE_URL}/stories/{story['id']}")
        progress.advance(task2)
        progress.update(task2, description="[green]✓ Story removed[/green]")

        # Delete demo config
        task3 = progress.add_task("Removing demo config...", total=1)
        demo = find_gauntlet_demo(session)
        if demo:
            session.delete(f"{BASE_URL}/demos/configs/{demo['id']}")
        progress.advance(task3)
        progress.update(task3, description="[green]✓ Demo config removed[/green]")

    rprint("\n[green]✓ Gauntlet Protocol decommissioned[/green]")


@app.command("run")
def run_gauntlet(
    show_json: Annotated[bool, typer.Option("--json", "-j", help="Output session info as JSON")] = False,
):
    """Start a Gauntlet session."""
    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Find demo config
    demo = find_gauntlet_demo(session)
    if not demo:
        rprint("[red]Gauntlet not set up. Run: gauntlet setup[/red]")
        raise typer.Exit(1)

    # Resolve session
    response = session.post(f"{BASE_URL}/demos/{GAUNTLET_DEMO_SLUG}/session")
    if response.status_code != 200:
        rprint(f"[red]Failed to create session: {response.text}[/red]")
        raise typer.Exit(1)

    data = response.json()

    if show_json:
        console.print(Syntax(json.dumps(data, indent=2), "json", theme="monokai"))
        return

    # Extract from ResolveDemoEntryPayload structure
    session_id = data.get("demo_session_id", "N/A")
    room_data = data.get("room", {})
    room_id = room_data.get("room_id", "N/A")
    room_title = room_data.get("title", "Gauntlet")
    created = data.get("created", False)

    status_msg = "[green]New session created[/green]" if created else "[dim]Existing session resumed[/dim]"

    rprint(Panel(
        f"""[bold]Gauntlet Protocol Initialized[/bold]

Session:  [cyan]{session_id}[/cyan]
Room:     [green]{room_id}[/green]
          {room_title}
Status:   {status_msg}

The Operator is standing by.

[dim]Access at: http://localhost:5173/demo/{GAUNTLET_DEMO_SLUG}[/dim]
[dim]Or room:   http://localhost:5173/r/{room_id}[/dim]""",
        title="🚀 GAUNTLET",
        border_style="cyan",
    ))


if __name__ == "__main__":
    app()
