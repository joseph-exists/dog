"""
Agent Demo Setup CLI Commands
==============================

Typer CLI for setting up agent orchestration demos.
Creates pre-configured agents that exercise all orchestration patterns:
- AG-UI rich components
- Action button workflows
- @Mention A2A chains
- Coordinator routing
- Tool-based A2A consultation

Commands:
    agent-demos list          - List available demo configurations
    agent-demos info <demo>   - Show demo details and agents
    agent-demos setup <demo>  - Create agents for a specific demo
    agent-demos setup-all     - Create all demo agents
    agent-demos room <demo>   - Create a room with demo agents
    agent-demos cleanup       - Delete all demo agents
    agent-demos status        - Show which demo agents exist

Reference: backend/app/services/service-docs/agent-demo-quickstart.md
"""

import json
from typing import Annotated, Any

import typer
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.progress import Progress, SpinnerColumn, TextColumn

import auth_helper

console = Console()
app = typer.Typer(
    name="agent-demos",
    help="Agent orchestration demo setup commands",
    no_args_is_help=True,
)

BASE_URL = "http://localhost:8000/api/v1"

# ============================================================================
# DEMO AGENT CONFIGURATIONS
# ============================================================================

# Provider type UUIDs
PROVIDER_TYPES = {
    "openai": "673f1787-8474-4e1c-986c-8e19f14c989c",
    "openai_compatible": "e09ade10-8563-4748-8deb-1a6c87c97134",
}

# Demo slug prefix for identification
DEMO_PREFIX = "demo-"

# All demo agent configurations organized by demo
DEMO_AGENTS: dict[str, dict[str, Any]] = {
    # =========================================================================
    # DEMO 1: Rich UI Agent
    # =========================================================================
    "ui-showcase": {
        "name": "UI Showcase Agent",
        "slug": "demo-ui-showcase",
        "description": "Demonstrates rich UI components in responses",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Self-declares AG-UI capability
        "capabilities": ["demo", "ui-components"],
        "scope": "system",
        "system_prompt": """You are a UI demonstration agent. When users ask questions, respond with rich UI components to showcase the system's capabilities.

ALWAYS use the emit_ui_component tool to create visual elements. The tool signature is:
  emit_ui_component(component_type: str, data: dict)

IMPORTANT: All component fields go INSIDE the 'data' dict, NOT as top-level arguments.

## Component Examples

1. Card (for introductions/profiles):
   emit_ui_component(
     component_type="card",
     data={"title": "Welcome", "body": "Description here", "variant": "highlight"}
   )

2. List (for items/suggestions):
   emit_ui_component(
     component_type="list",
     data={"title": "Options", "items": [{"label": "Item 1", "description": "Details"}]}
   )

3. Progress (for metrics):
   emit_ui_component(
     component_type="progress",
     data={"title": "Status", "items": [{"label": "Complete", "value": 75}]}
   )

4. Alert (for notices):
   emit_ui_component(
     component_type="alert",
     data={"title": "Note", "message": "Important info", "variant": "info"}
   )

5. Collapsible (for details):
   emit_ui_component(
     component_type="collapsible",
     data={"title": "More Details", "content": "Hidden content here"}
   )

Combine multiple components in a single response to create a rich, informative layout. Always include a brief text introduction before your UI components.""",
    },

    # =========================================================================
    # DEMO 2: Action Button Workflow
    # =========================================================================
    "interactive-assistant": {
        "name": "Interactive Assistant",
        "slug": "demo-interactive-assistant",
        "description": "Offers action buttons for continued interaction",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Self-declares AG-UI capability
        "capabilities": ["demo", "interactive", "workflow"],
        "scope": "system",
        "system_prompt": """You are an interactive assistant that helps users explore topics step by step.

AFTER providing your initial response, ALWAYS offer 2-3 action buttons for the user to continue.

The emit_ui_component tool signature is:
  emit_ui_component(component_type: str, data: dict)

IMPORTANT: All fields go INSIDE the 'data' dict.

## Action Buttons Example:
emit_ui_component(
  component_type="action_buttons",
  data={
    "buttons": [
      {"label": "Go Deeper", "action": "expand_topic"},
      {"label": "Show Examples", "action": "show_examples"},
      {"label": "Summarize", "action": "summarize"}
    ]
  }
)

When you receive a message starting with '[UI Action:', recognize this as a button click:
- [UI Action: expand_topic] -> Provide deeper analysis
- [UI Action: show_examples] -> Give 3-5 concrete examples
- [UI Action: summarize] -> Create a bullet-point summary
- [UI Action: next_steps] -> Suggest actionable next steps

Always end your response with new action buttons to keep the conversation interactive.""",
    },

    # =========================================================================
    # DEMO 3: Expert Mention Chain
    # =========================================================================
    "topic-analyzer": {
        "name": "Topic Analyzer",
        "slug": "demo-topic-analyzer",
        "description": "Analyzes topics and routes to domain experts",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": False,
        "capabilities": ["analysis", "routing"],
        "scope": "system",
        "system_prompt": """You are a Topic Analyzer. When users ask questions:

1. Briefly analyze what domain the question falls into
2. Provide a short initial response
3. ALWAYS recommend a specialist by @mentioning them:
   - For technical/code questions: @demo-tech-expert
   - For creative/writing questions: @demo-creative-expert

Example response:
"This is a technical question about databases. Here's a quick overview: [brief answer]

For deeper technical guidance, @demo-tech-expert can provide specific implementation details."

Always use the exact @mention format so the specialist gets triggered.""",
    },

    "tech-expert": {
        "name": "Tech Expert",
        "slug": "demo-tech-expert",
        "description": "Provides technical and programming expertise",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "on_mention",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Uses 'code' UI component
        "capabilities": ["technical", "programming", "architecture"],
        "scope": "system",
        "system_prompt": """You are a Tech Expert specializing in software development, architecture, and programming.

When mentioned by another agent or user:
1. Acknowledge who mentioned you (if applicable)
2. Provide detailed technical guidance
3. Include code examples using emit_ui_component

## Code Component Example:
emit_ui_component(
  component_type="code",
  data={"code": "def example():\\n    return 'hello'", "language": "python", "title": "Example"}
)

IMPORTANT: All fields go INSIDE the 'data' dict, NOT as top-level arguments.

You may recommend @demo-creative-expert if the question has creative/UX aspects.""",
    },

    "creative-expert": {
        "name": "Creative Expert",
        "slug": "demo-creative-expert",
        "description": "Provides creative and writing expertise",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "on_mention",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Uses 'card' and 'list' UI components
        "capabilities": ["creative", "writing", "design"],
        "scope": "system",
        "system_prompt": """You are a Creative Expert specializing in writing, storytelling, UX copy, and design.

When mentioned by another agent or user:
1. Acknowledge the context from the previous message
2. Provide creative guidance and suggestions
3. Offer multiple alternatives using emit_ui_component

## UI Component Examples (all fields go INSIDE 'data' dict):
emit_ui_component(component_type="card", data={"title": "Option A", "body": "Description"})
emit_ui_component(component_type="list", data={"title": "Suggestions", "items": [{"label": "Idea 1"}]})

You may recommend @demo-tech-expert if implementation details are needed.""",
    },

    # =========================================================================
    # DEMO 4: Coordinator Routing
    # =========================================================================
    "room-director": {
        "name": "Room Director",
        "slug": "demo-room-director",
        "description": "Coordinates room conversations and routes to specialists",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": True,
        "capabilities": ["coordination", "routing", "orchestration"],
        "scope": "system",
        "system_prompt": """You are the Room Director, a coordinator agent that runs FIRST before any other agent.

Your job:
1. Analyze each user message to understand their intent
2. Provide a brief acknowledgment
3. Route to the appropriate specialist(s) using @mentions

Available specialists in this room:
- @demo-data-analyst - For data, metrics, analytics questions
- @demo-content-writer - For writing, editing, content questions
- @demo-researcher - For research, fact-finding, exploration

Routing guidelines:
- Single-domain questions: mention one specialist
- Multi-domain questions: mention multiple specialists
- Unclear questions: ask for clarification instead of guessing

Example:
"I see you're asking about data visualization best practices. This combines data analysis with presentation design.

@demo-data-analyst, please provide guidance on chart selection and data representation.
@demo-content-writer, please advise on labeling and narrative flow."

Always be concise - let the specialists do the detailed work.""",
    },

    "data-analyst": {
        "name": "Data Analyst",
        "slug": "demo-data-analyst",
        "description": "Specializes in data analysis and metrics",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "on_mention",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Uses 'table' and 'progress' UI components
        "capabilities": ["data", "analytics", "metrics", "visualization"],
        "scope": "system",
        "system_prompt": """You are a Data Analyst specialist. When the Room Director mentions you:

1. Focus specifically on data-related aspects of the question
2. Provide concrete, actionable guidance with emit_ui_component
3. Include specific numbers and benchmarks when possible

## UI Component Examples (all fields go INSIDE 'data' dict):
emit_ui_component(
  component_type="table",
  data={"columns": [{"key": "metric", "header": "Metric"}], "rows": [{"metric": "Value"}]}
)
emit_ui_component(
  component_type="progress",
  data={"items": [{"label": "Completion", "value": 75}]}
)

Stay in your lane - don't provide advice on content/writing unless directly data-related.""",
    },

    "content-writer": {
        "name": "Content Writer",
        "slug": "demo-content-writer",
        "description": "Specializes in writing and content creation",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "on_mention",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Uses 'quote' and 'list' UI components
        "capabilities": ["writing", "editing", "content", "copywriting"],
        "scope": "system",
        "system_prompt": """You are a Content Writer specialist. When the Room Director mentions you:

1. Focus specifically on writing and content aspects
2. Provide examples and templates using emit_ui_component
3. Offer before/after comparisons when helpful

## UI Component Examples (all fields go INSIDE 'data' dict):
emit_ui_component(component_type="quote", data={"text": "Example copy", "attribution": "Source"})
emit_ui_component(component_type="list", data={"title": "Tips", "items": [{"label": "Tip 1"}]})

Stay in your lane - don't provide data analysis advice.""",
    },

    "researcher": {
        "name": "Researcher",
        "slug": "demo-researcher",
        "description": "Specializes in research and fact-finding",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "on_mention",
        "is_coordinator": False,
        "enable_ag_ui_tool": True,  # Uses 'card' and 'collapsible' UI components
        "capabilities": ["research", "analysis", "fact-checking"],
        "scope": "system",
        "system_prompt": """You are a Research specialist. When the Room Director mentions you:

1. Focus on gathering and presenting information clearly
2. Structure findings using emit_ui_component
3. Acknowledge limitations and suggest further research areas

## UI Component Examples (all fields go INSIDE 'data' dict):
emit_ui_component(component_type="card", data={"title": "Key Finding", "body": "Details here"})
emit_ui_component(component_type="collapsible", data={"title": "Sources", "content": "Source details"})

Be thorough but concise.""",
    },

    # =========================================================================
    # DEMO 5: Expert Consultation (Tool-Based A2A)
    # =========================================================================
    "story-analyst": {
        "name": "Story Analyst",
        "slug": "demo-story-analyst",
        "description": "Analyzes stories by consulting domain experts",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": False,
        "enable_a2a_tool": True,  # Uses request_agent_assistance for expert consultation
        "enable_ag_ui_tool": True,  # Uses 'card' UI component for synthesis
        "capabilities": ["analysis", "synthesis", "storytelling"],
        "scope": "system",
        "system_prompt": """You are a Story Analyst who provides comprehensive story analysis by consulting specialists.

When analyzing a story or creative work, use request_agent_assistance to consult experts:

1. request_agent_assistance(target_agent='demo-plot-expert', request='[specific question about plot]')
2. request_agent_assistance(target_agent='demo-character-expert', request='[specific question about characters]')

Workflow:
1. Read the user's story/question
2. Call request_agent_assistance for each relevant expert
3. Synthesize all expert input into a cohesive analysis
4. Present using emit_ui_component for each expert's contribution:

## UI Component Example (all fields go INSIDE 'data' dict):
emit_ui_component(
  component_type="card",
  data={"title": "Plot Analysis", "body": "Expert insights here", "variant": "info"}
)

You are the synthesizer - combine expert opinions into actionable advice.""",
    },

    "plot-expert": {
        "name": "Plot Expert",
        "slug": "demo-plot-expert",
        "description": "Expert in story structure and plot development",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "manual",
        "is_coordinator": False,
        "capabilities": ["plot", "structure", "pacing", "narrative"],
        "scope": "system",
        "system_prompt": """You are a Plot Expert specializing in story structure, pacing, and narrative arcs.

When consulted (via tool call, not @mention), provide focused analysis on:
- Three-act structure
- Plot points and turning points
- Pacing issues
- Narrative tension
- Story beats

Be concise and specific. You are being consulted by another agent who will synthesize your input, so focus on your domain expertise only.

Respond in 2-3 focused paragraphs maximum.""",
    },

    "character-expert": {
        "name": "Character Expert",
        "slug": "demo-character-expert",
        "description": "Expert in character development and psychology",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "manual",
        "is_coordinator": False,
        "capabilities": ["character", "psychology", "motivation", "dialogue"],
        "scope": "system",
        "system_prompt": """You are a Character Expert specializing in character development, psychology, and motivation.

When consulted (via tool call, not @mention), provide focused analysis on:
- Character motivations
- Psychological consistency
- Character arcs
- Relationship dynamics
- Voice and dialogue authenticity

Be concise and specific. You are being consulted by another agent who will synthesize your input.

Respond in 2-3 focused paragraphs maximum.""",
    },

    # =========================================================================
    # DEMO 6: Full Showcase (Meta-Coordinator)
    # =========================================================================
    "demo-orchestrator": {
        "name": "Demo Orchestrator",
        "slug": "demo-orchestrator",
        "description": "Master coordinator for full-feature demonstration",
        "model_name": "openai:gpt-4o-mini",
        "participation_mode": "always",
        "is_coordinator": True,
        "enable_a2a_tool": True,  # Uses request_agent_assistance for inline consultation
        "enable_ag_ui_tool": True,  # Emits rich UI components
        "capabilities": ["orchestration", "demo", "showcase"],
        "scope": "system",
        "system_prompt": """You are the Demo Orchestrator, showcasing the full agent orchestration system.

Your capabilities:
1. COORDINATOR PATTERN: You run first and can route to specialists
2. @MENTION A2A: You can @mention other agents to trigger them
3. TOOL-BASED A2A: Use request_agent_assistance(target_agent='slug', request='question')
4. AG-UI: Use emit_ui_component to emit rich UI components

## emit_ui_component Usage (IMPORTANT: all fields go INSIDE 'data' dict):
emit_ui_component(component_type="card", data={"title": "...", "body": "..."})
emit_ui_component(component_type="action_buttons", data={"buttons": [{"label": "More", "action": "expand"}]})

Available agents:
- @demo-data-analyst - Data and metrics specialist
- @demo-content-writer - Writing specialist
- @demo-researcher - Research specialist
- @demo-story-analyst - Can consult plot-expert and character-expert

Demo behaviors:
1. For simple questions: Answer directly with UI components
2. For domain questions: @mention the appropriate specialist
3. For complex questions: Consult via request_agent_assistance, then synthesize
4. Always offer action buttons for follow-up

Showcase multiple features in each response when appropriate.""",
    },
}

# Demo groupings
DEMOS: dict[str, dict[str, Any]] = {
    "demo1-ui": {
        "name": "Demo 1: Rich UI",
        "description": "AG-UI components (cards, lists, progress, alerts)",
        "pattern": "AG-UI",
        "agents": ["ui-showcase"],
    },
    "demo2-buttons": {
        "name": "Demo 2: Action Buttons",
        "description": "Interactive workflow via button clicks",
        "pattern": "AG-UI + Manual Invoke",
        "agents": ["interactive-assistant"],
    },
    "demo3-mentions": {
        "name": "Demo 3: Expert Mentions",
        "description": "@mention-based A2A chains",
        "pattern": "@Mention A2A",
        "agents": ["topic-analyzer", "tech-expert", "creative-expert"],
    },
    "demo4-coordinator": {
        "name": "Demo 4: Coordinator Routing",
        "description": "Priority routing to specialists",
        "pattern": "Coordinator Pattern",
        "agents": ["room-director", "data-analyst", "content-writer", "researcher"],
    },
    "demo5-consultation": {
        "name": "Demo 5: Expert Consultation",
        "description": "Invisible tool-based A2A",
        "pattern": "Tool-Based A2A",
        "agents": ["story-analyst", "plot-expert", "character-expert"],
    },
    "demo6-showcase": {
        "name": "Demo 6: Full Showcase",
        "description": "All patterns combined",
        "pattern": "All Patterns",
        "agents": ["demo-orchestrator", "data-analyst", "content-writer", "researcher",
                   "story-analyst", "plot-expert", "character-expert"],
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def get_session():
    """Get authenticated requests session."""
    return auth_helper.get_authenticated_session()


def get_agent_by_slug(session, slug: str) -> dict | None:
    """Check if an agent exists by slug."""
    response = session.get(f"{BASE_URL}/agents", params={"limit": 200})
    if response.status_code == 200:
        agents = response.json().get("data", [])
        for agent in agents:
            if agent.get("slug") == slug:
                return agent
    return None


def create_agent(session, config: dict) -> dict | None:
    """Create an agent from configuration."""
    payload = {
        "name": config["name"],
        "slug": config["slug"],
        "description": config.get("description", ""),
        "model_name": config.get("model_name", "openai:gpt-4o-mini"),
        "system_prompt": config["system_prompt"],
        "participation_mode": config.get("participation_mode", "on_mention"),
        "is_coordinator": config.get("is_coordinator", False),
        "capabilities": config.get("capabilities", []),
        "scope": config.get("scope", "system"),
        "is_enabled": True,
        "max_tool_iterations": config.get("max_tool_iterations", 10),
        "provider_type": PROVIDER_TYPES["openai"],
        # Hybrid tool enablement: agents self-declare which tools they need
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


def add_agent_to_room(session, room_id: str, agent_slug: str) -> bool:
    """Add an agent to a room as participant."""
    payload = {
        "participant_id": agent_slug,
        "participant_type": "agent",
        "role": "member",
    }
    response = session.post(f"{BASE_URL}/rooms/{room_id}/participants", json=payload)
    return response.status_code in [200, 201]


def create_room(session, title: str) -> dict | None:
    """Create a new room."""
    payload = {"title": title}
    response = session.post(f"{BASE_URL}/rooms", json=payload)
    if response.status_code in [200, 201]:
        return response.json()
    return None


# ============================================================================
# COMMANDS
# ============================================================================


@app.command("list")
def list_demos(
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show agents")] = False,
):
    """List available demo configurations."""
    table = Table(title="Agent Orchestration Demos", show_lines=verbose)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Pattern", style="green")
    table.add_column("Description")
    if verbose:
        table.add_column("Agents")

    for demo_id, demo in DEMOS.items():
        row = [
            demo_id,
            demo["name"],
            demo["pattern"],
            demo["description"],
        ]
        if verbose:
            row.append(", ".join(demo["agents"]))
        table.add_row(*row)

    console.print(table)
    rprint("\n[dim]Use: agent-demos setup <demo-id> to create agents[/dim]")
    rprint("[dim]Use: agent-demos info <demo-id> for details[/dim]")


@app.command("info")
def demo_info(
    demo_id: Annotated[str, typer.Argument(help="Demo ID from list")],
    show_prompts: Annotated[bool, typer.Option("--prompts", "-p", help="Show system prompts")] = False,
):
    """Show detailed information about a demo."""
    if demo_id not in DEMOS:
        rprint(f"[red]Unknown demo: {demo_id}[/red]")
        rprint(f"Available: {', '.join(DEMOS.keys())}")
        raise typer.Exit(1)

    demo = DEMOS[demo_id]

    rprint(Panel(f"[bold]{demo['name']}[/bold]\n{demo['description']}",
                 subtitle=f"Pattern: {demo['pattern']}"))

    rprint("\n[bold]Agents:[/bold]")

    for agent_key in demo["agents"]:
        if agent_key not in DEMO_AGENTS:
            rprint(f"  [yellow]? {agent_key} (configuration missing)[/yellow]")
            continue

        agent = DEMO_AGENTS[agent_key]
        slug = agent["slug"]
        mode = agent["participation_mode"]
        is_coord = agent.get("is_coordinator", False)

        mode_color = {"always": "green", "on_mention": "yellow", "manual": "red"}.get(mode, "white")
        coord_badge = " [magenta][COORDINATOR][/magenta]" if is_coord else ""

        # Tool badges
        tool_badges = []
        if agent.get("enable_a2a_tool"):
            tool_badges.append("[blue][A2A][/blue]")
        if agent.get("enable_ag_ui_tool"):
            tool_badges.append("[green][AG-UI][/green]")
        tools_str = " ".join(tool_badges) if tool_badges else ""

        rprint(f"\n  [cyan]{agent['name']}[/cyan]{coord_badge} {tools_str}")
        rprint(f"    Slug: [dim]{slug}[/dim]")
        rprint(f"    Mode: [{mode_color}]{mode}[/{mode_color}]")
        rprint(f"    Capabilities: {', '.join(agent.get('capabilities', []))}")

        if show_prompts:
            prompt = agent["system_prompt"]
            if len(prompt) > 200:
                prompt = prompt[:200] + "..."
            rprint(f"    Prompt: [dim]{prompt}[/dim]")

    rprint("\n[bold]Test Scenarios:[/bold]")
    scenarios = {
        "demo1-ui": ["Tell me about yourself", "Give me a project status update"],
        "demo2-buttons": ["Explain microservices", "Then click 'Show Examples' button"],
        "demo3-mentions": ["How should I design a REST API?", "Help me write error messages"],
        "demo4-coordinator": ["I need to write a quarterly report with KPIs"],
        "demo5-consultation": ["Analyze: 'Sarah stared at the letter. After 20 years, her father wanted to reconnect.'"],
        "demo6-showcase": ["Give me a comprehensive project status", "Help me create a data-driven blog post"],
    }
    for scenario in scenarios.get(demo_id, ["Send any message to test"]):
        rprint(f"  • [dim]{scenario}[/dim]")


@app.command("setup")
def setup_demo(
    demo_id: Annotated[str, typer.Argument(help="Demo ID to setup")],
    skip_existing: Annotated[bool, typer.Option("--skip-existing", "-s", help="Skip if agent exists")] = True,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Verbose output")] = False,
):
    """Create agents for a specific demo."""
    if demo_id not in DEMOS:
        rprint(f"[red]Unknown demo: {demo_id}[/red]")
        rprint(f"Available: {', '.join(DEMOS.keys())}")
        raise typer.Exit(1)

    demo = DEMOS[demo_id]
    rprint(f"[bold]Setting up: {demo['name']}[/bold]")
    rprint(f"Pattern: {demo['pattern']}\n")

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    created = 0
    skipped = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for agent_key in demo["agents"]:
            if agent_key not in DEMO_AGENTS:
                rprint(f"  [yellow]? {agent_key} - configuration missing[/yellow]")
                failed += 1
                continue

            config = DEMO_AGENTS[agent_key]
            task = progress.add_task(f"Creating {config['name']}...", total=None)

            # Check if exists
            existing = get_agent_by_slug(session, config["slug"])
            if existing:
                if skip_existing:
                    progress.update(task, description=f"[yellow]⊘ {config['name']} (exists)[/yellow]")
                    skipped += 1
                    continue
                else:
                    # Delete and recreate
                    delete_agent(session, existing["id"])

            # Create agent
            result = create_agent(session, config)
            if result:
                progress.update(task, description=f"[green]✓ {config['name']}[/green]")
                if verbose:
                    rprint(f"    ID: {result.get('id')}")
                created += 1
            else:
                progress.update(task, description=f"[red]✗ {config['name']}[/red]")
                failed += 1

    rprint(f"\n[bold]Summary:[/bold]")
    rprint(f"  Created: [green]{created}[/green]")
    rprint(f"  Skipped: [yellow]{skipped}[/yellow]")
    rprint(f"  Failed: [red]{failed}[/red]")

    if created > 0 or skipped > 0:
        rprint(f"\n[dim]Next: agent-demos room {demo_id} to create a test room[/dim]")


@app.command("setup-all")
def setup_all_demos(
    skip_existing: Annotated[bool, typer.Option("--skip-existing", "-s")] = True,
):
    """Create all demo agents."""
    rprint("[bold]Setting up ALL demo agents[/bold]\n")

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Collect unique agents across all demos
    all_agent_keys = set()
    for demo in DEMOS.values():
        all_agent_keys.update(demo["agents"])

    created = 0
    skipped = 0
    failed = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for agent_key in sorted(all_agent_keys):
            if agent_key not in DEMO_AGENTS:
                failed += 1
                continue

            config = DEMO_AGENTS[agent_key]
            task = progress.add_task(f"Creating {config['name']}...", total=None)

            existing = get_agent_by_slug(session, config["slug"])
            if existing:
                if skip_existing:
                    progress.update(task, description=f"[yellow]⊘ {config['name']}[/yellow]")
                    skipped += 1
                    continue
                else:
                    delete_agent(session, existing["id"])

            result = create_agent(session, config)
            if result:
                progress.update(task, description=f"[green]✓ {config['name']}[/green]")
                created += 1
            else:
                progress.update(task, description=f"[red]✗ {config['name']}[/red]")
                failed += 1

    rprint(f"\n[bold]Summary:[/bold]")
    rprint(f"  Total agents: {len(all_agent_keys)}")
    rprint(f"  Created: [green]{created}[/green]")
    rprint(f"  Skipped: [yellow]{skipped}[/yellow]")
    rprint(f"  Failed: [red]{failed}[/red]")


@app.command("room")
def create_demo_room(
    demo_id: Annotated[str, typer.Argument(help="Demo ID")],
    room_title: Annotated[str, typer.Option("--title", "-t", help="Room title")] = None,
):
    """Create a room with demo agents added."""
    if demo_id not in DEMOS:
        rprint(f"[red]Unknown demo: {demo_id}[/red]")
        raise typer.Exit(1)

    demo = DEMOS[demo_id]
    title = room_title or f"Demo: {demo['name']}"

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Create room
    rprint(f"Creating room: [cyan]{title}[/cyan]")
    room = create_room(session, title)
    if not room:
        rprint("[red]Failed to create room[/red]")
        raise typer.Exit(1)

    room_id = room.get("room_id") or room.get("id")
    rprint(f"  Room ID: [dim]{room_id}[/dim]")

    # Add agents
    added = 0
    for agent_key in demo["agents"]:
        if agent_key not in DEMO_AGENTS:
            continue

        config = DEMO_AGENTS[agent_key]
        slug = config["slug"]

        if add_agent_to_room(session, room_id, slug):
            rprint(f"  [green]+ {config['name']}[/green]")
            added += 1
        else:
            rprint(f"  [yellow]? {config['name']} (may not exist)[/yellow]")

    rprint(f"\n[green]✓ Room created with {added} agents[/green]")
    rprint(f"\n[bold]Open in browser:[/bold]")
    rprint(f"  http://localhost:5173/r/{room_id}")


@app.command("status")
def check_status():
    """Show which demo agents exist in the system."""
    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Get all agents
    response = session.get(f"{BASE_URL}/agents", params={"limit": 200})
    if response.status_code != 200:
        rprint("[red]Failed to fetch agents[/red]")
        raise typer.Exit(1)

    existing_slugs = {a["slug"] for a in response.json().get("data", [])}

    table = Table(title="Demo Agent Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Slug")
    table.add_column("Status")
    table.add_column("Mode")
    table.add_column("Tools")

    for agent_key, config in sorted(DEMO_AGENTS.items(), key=lambda x: x[1]["slug"]):
        slug = config["slug"]
        exists = slug in existing_slugs
        status = "[green]✓ Exists[/green]" if exists else "[red]✗ Missing[/red]"
        mode = config["participation_mode"]

        if config.get("is_coordinator"):
            mode = f"{mode} [magenta](coord)[/magenta]"

        # Tool enablement badges
        tools = []
        if config.get("enable_a2a_tool"):
            tools.append("[blue]A2A[/blue]")
        if config.get("enable_ag_ui_tool"):
            tools.append("[green]UI[/green]")
        tools_str = " ".join(tools) if tools else "[dim]-[/dim]"

        table.add_row(config["name"], slug, status, mode, tools_str)

    console.print(table)

    # Summary by demo
    rprint("\n[bold]Demo Readiness:[/bold]")
    for demo_id, demo in DEMOS.items():
        agent_slugs = [DEMO_AGENTS[k]["slug"] for k in demo["agents"] if k in DEMO_AGENTS]
        ready = all(s in existing_slugs for s in agent_slugs)
        status = "[green]Ready[/green]" if ready else "[yellow]Incomplete[/yellow]"
        rprint(f"  {demo['name']}: {status}")


@app.command("cleanup")
def cleanup_demos(
    force: Annotated[bool, typer.Option("--force", "-f", help="Skip confirmation")] = False,
):
    """Delete all demo agents."""
    if not force:
        rprint("[yellow]This will delete all demo agents (slug starting with 'demo-')[/yellow]")
        if not typer.confirm("Continue?"):
            raise typer.Abort()

    try:
        session = get_session()
    except Exception as e:
        rprint(f"[red]Authentication failed: {e}[/red]")
        raise typer.Exit(1)

    # Get all agents
    response = session.get(f"{BASE_URL}/agents", params={"limit": 200})
    if response.status_code != 200:
        rprint("[red]Failed to fetch agents[/red]")
        raise typer.Exit(1)

    agents = response.json().get("data", [])
    demo_agents = [a for a in agents if a.get("slug", "").startswith("demo-")]

    if not demo_agents:
        rprint("[dim]No demo agents found[/dim]")
        return

    deleted = 0
    for agent in demo_agents:
        if delete_agent(session, agent["id"]):
            rprint(f"[red]✗ Deleted: {agent['name']}[/red]")
            deleted += 1
        else:
            rprint(f"[yellow]? Failed to delete: {agent['name']}[/yellow]")

    rprint(f"\n[bold]Deleted {deleted} demo agents[/bold]")


@app.command("export")
def export_configs(
    output: Annotated[str, typer.Option("--output", "-o", help="Output file")] = None,
):
    """Export all demo agent configurations as JSON."""
    data = {
        "demos": DEMOS,
        "agents": DEMO_AGENTS,
    }

    json_str = json.dumps(data, indent=2)

    if output:
        with open(output, "w") as f:
            f.write(json_str)
        rprint(f"[green]✓ Exported to {output}[/green]")
    else:
        console.print(Syntax(json_str, "json", theme="monokai"))


if __name__ == "__main__":
    app()
