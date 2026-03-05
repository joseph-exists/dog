#!/usr/bin/env python3
"""
TinyFoot CLI - Staging Environment Operations

A typer-based CLI for running test scripts and operations in staging environments.

Usage:
    python -m backend.app.test_scripts.typer.main [COMMAND] [OPTIONS]

Examples:
    # Show available commands
    python -m backend.app.test_scripts.typer.main --help

    # Run demo commands
    python -m backend.app.test_scripts.typer.main demo hello "World"

    # Test authentication
    python auth_helper.py

For extending this CLI, see REFERENCE.md in this directory.
"""
import typer
import auth_helper
import wonka  # Example command module
from commands import items


app = typer.Typer(
    name="tinyfoot",
    help="TinyFoot staging operations CLI",
    add_completion=False,
    no_args_is_help=True
)

# Register command modules
app.add_typer(wonka.app, name="demo", help="Demo commands (see wonka.py)")


# Command modules
from commands import (
    affordances,
    agent_demos,
    agents,
    demos,
    stories,
    personas,
    rooms,
    users,
    trait_conflicts,
    llm_catalog,
    pages,
    presets,
    panels,
    embedder,
    story_affordances,
)

app.add_typer(items.app, name="items")
app.add_typer(stories.app, name="stories")
app.add_typer(personas.app, name="personas")
app.add_typer(rooms.app, name="rooms")
app.add_typer(users.app, name="users")
app.add_typer(agents.app, name="agents", help="Agent management commands")
app.add_typer(agent_demos.app, name="agent-demos", help="Agent orchestration demo setup")
app.add_typer(trait_conflicts.app, name="conflicts", help="Trait conflict management")
app.add_typer(llm_catalog.app, name="catalog", help="LLM Catalog - browse providers and models")
app.add_typer(pages.app, name="pages", help="Page layout management")
app.add_typer(presets.app, name="presets", help="Panel preset browsing")
app.add_typer(panels.app, name="panels", help="Room panel configuration")
app.add_typer(embedder.app, name="embedder", help="Vector embedding query commands")
app.add_typer(affordances.app, name="affordances", help="Affordance introspection commands")
app.add_typer(demos.app, name="demos", help="Demo configuration and styling commands")
app.add_typer(story_affordances.app, name="story-affordances", help="Story affordance introspection commands")

# TODO: Add more command modules
# from commands import tests
# app.add_typer(tests.app, name="tests")

@app.command()
def version():
    """Show CLI version information."""
    typer.echo("TinyFoot CLI v0.1.0")
    typer.echo("Backend Test Scripts Interface")

@app.callback()
def main():
    """
    TinyFoot CLI for staging operations.

    Run test scripts, manage data, and perform operations in staging environments.
    """
    pass

if __name__ == "__main__":
    app()
