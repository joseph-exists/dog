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
from commands import agents, stories, personas, rooms, users, trait_conflicts, llm_catalog

app.add_typer(items.app, name="items")
app.add_typer(stories.app, name="stories")
app.add_typer(personas.app, name="personas")
app.add_typer(rooms.app, name="rooms")
app.add_typer(users.app, name="users")
app.add_typer(agents.app, name="agents", help="Agent management commands")
app.add_typer(trait_conflicts.app, name="conflicts", help="Trait conflict management")
app.add_typer(llm_catalog.app, name="catalog", help="LLM Catalog - browse providers and models")

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
