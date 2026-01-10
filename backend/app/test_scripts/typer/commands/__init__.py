"""
TinyFoot CLI Command Modules

This package contains command modules for the TinyFoot CLI.
Each module represents a feature area (stories, personas, rooms, etc.).

To add a new command module:
1. Create a new .py file in this directory (e.g., stories.py)
2. Define an app = typer.Typer() instance
3. Add @app.command() decorated functions
4. Import and register in ../main.py

See REFERENCE.md for detailed examples and patterns.
"""
