# Typer CLI Reference Guide

Reference guide for extending the TinyFoot CLI using Typer for staging environment operations.

## Overview

This CLI exposes test script functionality through a typer-based command-line interface for use in staging/testing environments. It provides authenticated access to backend operations without needing to write custom scripts.

## Directory Structure

```
backend/app/test_scripts/typer/
├── REFERENCE.md          # This file
├── auth_helper.py        # Authentication utilities
├── wonka.py             # Example commands
└── commands/            # Command modules (create as needed)
    ├── __init__.py
    ├── stories.py       # Story-related commands
    ├── personas.py      # Persona/character commands
    └── rooms.py         # Room management commands
```

## Quick Start

### Basic Command Structure

```python
# commands/my_feature.py
import typer
from typing_extensions import Annotated
from ..auth_helper import get_authenticated_session

app = typer.Typer(help="My feature commands")

@app.command()
def create(
    name: Annotated[str, typer.Argument(help="Name of the item")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Create a new item."""
    if verbose:
        typer.echo(f"Creating item: {name}")

    session = get_authenticated_session()
    response = session.post(
        "http://localhost:8000/api/v1/items",
        json={"name": name, "description": description}
    )

    if response.status_code == 200:
        typer.secho("✅ Item created successfully!", fg=typer.colors.GREEN)
        typer.echo(response.json())
    else:
        typer.secho(f"❌ Failed: {response.text}", fg=typer.colors.RED)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
```

### Registering Commands in Main CLI

```python
# main.py
import typer
from commands import stories, personas, rooms

app = typer.Typer(
    name="tinyfoot",
    help="TinyFoot CLI for staging operations"
)

# Register sub-commands
app.add_typer(stories.app, name="stories")
app.add_typer(personas.app, name="personas")
app.add_typer(rooms.app, name="rooms")

if __name__ == "__main__":
    app()
```

## Common Patterns

### 1. Authenticated API Calls

Always use the auth_helper for authenticated requests:

```python
from auth_helper import get_authenticated_session

session = get_authenticated_session()
response = session.post("http://localhost:8000/api/v1/endpoint", json={...})
```

### 2. Arguments vs Options

**Arguments** - Required positional parameters:
```python
@app.command()
def create(name: str):  # Required argument
    """Create with name"""
    pass
```

**Options** - Optional flags with defaults:
```python
@app.command()
def create(
    name: str,  # Required argument
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False  # Optional flag
):
    """Create with optional verbosity"""
    pass
```

### 3. Type Annotations for Better Help

Use `Annotated` for rich help messages:

```python
from typing_extensions import Annotated

@app.command()
def create(
    title: Annotated[str, typer.Argument(help="Story title")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Story description")] = "",
    version: Annotated[int, typer.Option(help="Version number")] = 1,
):
    """Create a new story."""
    pass
```

### 4. Output Formatting

Use typer's output helpers for consistent formatting:

```python
# Success messages
typer.secho("✅ Operation successful!", fg=typer.colors.GREEN)

# Error messages
typer.secho("❌ Operation failed!", fg=typer.colors.RED, err=True)

# Info messages
typer.secho("ℹ️  Processing...", fg=typer.colors.BLUE)

# Warnings
typer.secho("⚠️  Warning: This is destructive", fg=typer.colors.YELLOW)

# Regular output
typer.echo("Regular message")

# JSON output
import json
typer.echo(json.dumps(data, indent=2))
```

### 5. Error Handling

Handle errors consistently:

```python
@app.command()
def create(name: str):
    """Create an item."""
    try:
        session = get_authenticated_session()
        response = session.post("http://localhost:8000/api/v1/items", json={"name": name})

        if response.status_code in [200, 201]:
            typer.secho("✅ Success!", fg=typer.colors.GREEN)
            typer.echo(json.dumps(response.json(), indent=2))
        else:
            typer.secho(f"❌ HTTP {response.status_code}: {response.text}",
                       fg=typer.colors.RED, err=True)
            raise typer.Exit(1)

    except Exception as e:
        typer.secho(f"❌ Error: {str(e)}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
```

### 6. Verbose Mode

Implement consistent verbose logging:

```python
@app.command()
def create(
    name: str,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Create with optional debug output."""

    def log(msg: str):
        if verbose:
            typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

    log("Starting creation process...")
    log(f"Name: {name}")

    # ... operation ...

    log("Operation completed")
```

## Example Command Modules

### Story Commands

```python
# commands/stories.py
import typer
import json
from typing_extensions import Annotated
from ..auth_helper import get_authenticated_session

app = typer.Typer(help="Story management commands")

BASE_URL = "http://localhost:8000/api/v1"

@app.command()
def create(
    title: Annotated[str, typer.Argument(help="Story title")],
    description: Annotated[str, typer.Option("--desc", "-d", help="Story description")] = "",
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Create a new story."""

    if verbose:
        typer.secho(f"Creating story: {title}", fg=typer.colors.CYAN)

    session = get_authenticated_session()

    payload = {
        "title": title,
        "description": description,
        "current_version": 1
    }

    if verbose:
        typer.echo(f"Payload: {json.dumps(payload, indent=2)}")

    response = session.post(f"{BASE_URL}/stories", json=payload)

    if response.status_code == 200:
        story = response.json()
        typer.secho("✅ Story created successfully!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {story['id']}")
        typer.echo(f"Title: {story['title']}")
        typer.echo(f"Version: {story['current_version']}")
    else:
        typer.secho(f"❌ Failed: {response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

@app.command()
def list(
    limit: Annotated[int, typer.Option(help="Max stories to list")] = 10,
    offset: Annotated[int, typer.Option(help="Pagination offset")] = 0
):
    """List all stories."""

    session = get_authenticated_session()
    response = session.get(
        f"{BASE_URL}/stories",
        params={"limit": limit, "offset": offset}
    )

    if response.status_code == 200:
        stories_data = response.json()
        stories = stories_data.get("data", [])
        total = stories_data.get("count", 0)

        typer.echo(f"\n📚 Stories ({len(stories)} of {total}):\n")

        for story in stories:
            typer.echo(f"  • {story['title']}")
            typer.echo(f"    ID: {story['id']}")
            typer.echo(f"    Published: {'Yes' if story.get('is_published') else 'No'}")
            typer.echo()
    else:
        typer.secho(f"❌ Failed: {response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

@app.command()
def publish(
    story_id: Annotated[str, typer.Argument(help="Story ID to publish")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Publish a story."""

    if verbose:
        typer.secho(f"Publishing story: {story_id}", fg=typer.colors.CYAN)

    session = get_authenticated_session()
    response = session.put(f"{BASE_URL}/stories/{story_id}/publish")

    if response.status_code == 200:
        story = response.json()
        typer.secho("✅ Story published successfully!", fg=typer.colors.GREEN)
        typer.echo(f"Published version: {story.get('published_version')}")
    else:
        typer.secho(f"❌ Failed: {response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

if __name__ == "__main__":
    app()
```

### Test Runner Commands

```python
# commands/tests.py
import typer
import subprocess
from pathlib import Path
from typing_extensions import Annotated

app = typer.Typer(help="Test runner commands")

SCRIPTS_DIR = Path(__file__).parent.parent.parent

@app.command()
def story_system(
    phase: Annotated[int, typer.Option(help="Run specific phase only")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False,
    persona_id: Annotated[str, typer.Option(help="Use existing persona")] = None
):
    """Run story system tests."""

    script = SCRIPTS_DIR / "test_story_system.py"
    cmd = ["python", str(script)]

    if phase:
        cmd.extend(["--phase", str(phase)])
    if verbose:
        cmd.append("--verbose")
    if persona_id:
        cmd.extend(["--persona-id", persona_id])

    typer.secho(f"Running: {' '.join(cmd)}", fg=typer.colors.CYAN)
    result = subprocess.run(cmd)

    raise typer.Exit(result.returncode)

@app.command()
def branching_stories(
    story: Annotated[str, typer.Option(help="Test specific story")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Run branching stories E2E tests."""

    script = SCRIPTS_DIR / "test_branching_stories.py"
    cmd = ["python", str(script)]

    if story:
        cmd.extend(["--story", story])
    if verbose:
        cmd.append("--verbose")

    typer.secho(f"Running: {' '.join(cmd)}", fg=typer.colors.CYAN)
    result = subprocess.run(cmd)

    raise typer.Exit(result.returncode)

if __name__ == "__main__":
    app()
```

## Advanced Patterns

### Progress Indicators

For long-running operations:

```python
import typer

@app.command()
def process():
    """Process items with progress indicator."""
    items = ["item1", "item2", "item3"]

    with typer.progressbar(items, label="Processing") as progress:
        for item in progress:
            # Do work
            import time
            time.sleep(1)

    typer.secho("✅ Done!", fg=typer.colors.GREEN)
```

### Confirmation Prompts

For destructive operations:

```python
@app.command()
def delete(story_id: str):
    """Delete a story (with confirmation)."""

    typer.secho(f"⚠️  This will delete story {story_id}", fg=typer.colors.YELLOW)

    if not typer.confirm("Are you sure?"):
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    # Proceed with deletion
    session = get_authenticated_session()
    response = session.delete(f"{BASE_URL}/stories/{story_id}")

    if response.status_code == 204:
        typer.secho("✅ Story deleted", fg=typer.colors.GREEN)
    else:
        typer.secho(f"❌ Failed: {response.text}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
```

### Interactive Input

For prompting user input:

```python
@app.command()
def create_interactive():
    """Create story interactively."""

    title = typer.prompt("Story title")
    description = typer.prompt("Description (optional)", default="")

    # Create story with inputs...
```

### File Operations

Reading from files:

```python
@app.command()
def import_data(
    file: Annotated[typer.FileText, typer.Argument(help="JSON file to import")]
):
    """Import data from JSON file."""

    import json
    data = json.load(file)

    # Process data...
    typer.echo(f"Imported {len(data)} items")
```

### JSON Output Mode

Support JSON output for scripting:

```python
@app.command()
def list(
    json_output: Annotated[bool, typer.Option("--json")] = False
):
    """List stories with optional JSON output."""

    session = get_authenticated_session()
    response = session.get(f"{BASE_URL}/stories")

    if response.status_code == 200:
        data = response.json()

        if json_output:
            # Machine-readable output
            typer.echo(json.dumps(data, indent=2))
        else:
            # Human-readable output
            stories = data.get("data", [])
            for story in stories:
                typer.echo(f"• {story['title']} ({story['id']})")
    else:
        raise typer.Exit(1)
```

## Testing Commands

Test your commands locally:

```bash
# Run command module directly
python -m backend.app.test_scripts.typer.commands.stories create "My Story"

# Test from main CLI
python -m backend.app.test_scripts.typer.main stories create "My Story"

# With options
python -m backend.app.test_scripts.typer.main stories create "My Story" --desc "A tale" -v
```

## Best Practices

### 1. Command Organization

- **One file per feature area** (stories, personas, rooms)
- **Keep commands focused** - each command does one thing well
- **Use clear, consistent naming** - follow verb-noun pattern

### 2. Help Text

- **Add docstrings** - become command help text
- **Use Annotated types** - provide parameter help
- **Include examples** in module docstrings

### 3. Error Handling

- **Always handle HTTP errors** - check status codes
- **Use Exit codes** - 0 for success, 1 for errors
- **Provide actionable errors** - tell users what went wrong and how to fix it

### 4. Output

- **Use colors consistently**:
  - Green (✅) for success
  - Red (❌) for errors
  - Yellow (⚠️) for warnings
  - Blue (ℹ️) for info
  - Cyan for debug/verbose
- **Support both human and machine output** (--json flag)
- **Show progress** for long operations

### 5. Authentication

- **Always use auth_helper** - don't reimplement auth
- **Handle auth errors gracefully** - catch AuthenticationError
- **Test auth before operations** - fail fast

### 6. Configuration

Use environment variables or config files:

```python
import os

BASE_URL = os.getenv("TINYFOOT_API_URL", "http://localhost:8000")
```

## Integration with Existing Scripts

To expose existing test scripts through CLI:

```python
# commands/populate.py
import typer
import subprocess
from pathlib import Path
from typing_extensions import Annotated

app = typer.Typer(help="Data population commands")

SCRIPTS_DIR = Path(__file__).parent.parent.parent

@app.command()
def jungian_system():
    """Populate Jungian archetype system."""

    script = SCRIPTS_DIR / "populate_jungian_system.py"

    typer.secho("📦 Populating Jungian system...", fg=typer.colors.CYAN)
    result = subprocess.run(["python", str(script)])

    if result.returncode == 0:
        typer.secho("✅ Jungian system populated!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Population failed", fg=typer.colors.RED, err=True)

    raise typer.Exit(result.returncode)
```

## Common Issues

### Import Errors

If you get import errors, ensure:
1. You're in the correct directory
2. `__init__.py` files exist
3. Using relative imports (`from ..auth_helper import ...`)

### Authentication Failures

If authentication fails:
1. Check `test.env` exists and has correct credentials
2. Verify backend is running
3. Test with `python auth_helper.py`

### Command Not Found

If typer doesn't find your command:
1. Check command is registered in main.py
2. Verify function has `@app.command()` decorator
3. Ensure module is imported

## Resources

- **Typer Documentation**: https://typer.tiangolo.com/
- **Existing Scripts**: `backend/app/test_scripts/*.py`
- **Auth Helper**: `backend/app/test_scripts/typer/auth_helper.py`
- **Example Commands**: `backend/app/test_scripts/typer/wonka.py`

## Example Main CLI

```python
# main.py
"""
TinyFoot CLI - Staging Environment Operations

Usage:
    python -m backend.app.test_scripts.typer.main [COMMAND] [OPTIONS]

Examples:
    # Create a story
    python -m backend.app.test_scripts.typer.main stories create "My Story"

    # List personas
    python -m backend.app.test_scripts.typer.main personas list

    # Run tests
    python -m backend.app.test_scripts.typer.main tests story-system --verbose
"""
import typer
from . import wonka  # Example module
# from .commands import stories, personas, rooms, tests

app = typer.Typer(
    name="tinyfoot",
    help="TinyFoot staging operations CLI",
    add_completion=False
)

# Register command modules
app.add_typer(wonka.app, name="demo")
# app.add_typer(stories.app, name="stories")
# app.add_typer(personas.app, name="personas")
# app.add_typer(rooms.app, name="rooms")
# app.add_typer(tests.app, name="tests")

@app.command()
def version():
    """Show CLI version."""
    typer.echo("TinyFoot CLI v0.1.0")

if __name__ == "__main__":
    app()
```

## Next Steps

1. **Create command modules** in `commands/` directory
2. **Register commands** in main.py
3. **Test locally** with `python -m backend.app.test_scripts.typer.main`
4. **Document usage** - add help text and examples
5. **Deploy to staging** - make available in staging environment
