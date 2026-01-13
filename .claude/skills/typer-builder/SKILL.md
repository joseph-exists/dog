---
name: typer-builder
description: Add functionality to the TinyFoot Typer CLI as commands and modules
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Typer Builder

Build and extend the TinyFoot CLI with new Typer commands and modules.

## Quick Start

To add a new command module:

1. **Create the command module** in `backend/app/test_scripts/typer/commands/`:
```python
# commands/my_feature.py
import typer
import json
from typing import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="My feature commands")
BASE_URL = "http://localhost:8000/api/v1"

@app.command()
def my_command(
    name: Annotated[str, typer.Argument(help="Name argument")],
    verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
):
    """Command description."""
    session = get_authenticated_session()
    # ... implementation
```

2. **Register in main.py**:
```python
from commands import my_feature
app.add_typer(my_feature.app, name="myfeature", help="My feature commands")
```

3. **Document in COMMANDS.md**

## Reference Files

- **README**: `backend/app/test_scripts/typer/TYPER-README.md`
- **Commands Reference**: `backend/app/test_scripts/typer/COMMANDS.md`
- **Template**: `backend/app/test_scripts/typer/commands/_template.py`
- **Example Module**: `backend/app/test_scripts/typer/commands/personas.py`

## Requirements

The dog backend environment must be activated:
```bash
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/typer
```

## Command Patterns

### Standard CRUD Commands

For a resource, implement these commands:
- `create` - Create new resource
- `list` / `list-{resources}` - List with pagination
- `get` / `get-{resource}` - Get by ID
- `update` - Update resource
- `delete` - Delete with confirmation

### Common Options

```python
# Pagination
limit: Annotated[int, typer.Option(help="Max items")] = 20
offset: Annotated[int, typer.Option(help="Pagination offset")] = 0

# Output format
json_output: Annotated[bool, typer.Option("--json")] = False

# Debugging
verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False

# Confirmation skip
force: Annotated[bool, typer.Option("--force", "-f")] = False
```

### Response Handling

```python
if response.status_code in [200, 201]:
    data = response.json()
    if json_output:
        typer.echo(json.dumps(data, indent=2))
    else:
        typer.secho("✅ Success!", fg=typer.colors.GREEN)
        typer.echo(f"ID: {data['id']}")
elif response.status_code == 404:
    typer.secho("❌ Not found", fg=typer.colors.RED, err=True)
    raise typer.Exit(1)
else:
    typer.secho(f"❌ Failed", fg=typer.colors.RED, err=True)
    typer.echo(f"Status: {response.status_code}")
    typer.echo(f"Error: {response.text}")
    raise typer.Exit(1)
```

### Verbose Logging Pattern

```python
def log(msg: str):
    if verbose:
        typer.secho(f"[DEBUG] {msg}", fg=typer.colors.CYAN)

log(f"POST {BASE_URL}/endpoint")
log(f"Payload: {json.dumps(payload, indent=2)}")
```

### Confirmation Prompts

```python
if not force:
    typer.secho(f"⚠️  This will delete {item_id}", fg=typer.colors.YELLOW)
    if not typer.confirm("Are you sure?"):
        typer.echo("Cancelled.")
        raise typer.Exit(0)
```

## Existing Command Modules

| Module | Name | Description |
|--------|------|-------------|
| `stories.py` | stories | Story and state schema management |
| `personas.py` | personas | Archetypes, traits, qualities, personas |
| `rooms.py` | rooms | Chat rooms and participants |
| `users.py` | users | Current user info and data |
| `trait_conflicts.py` | conflicts | Trait conflict groups for logic |
| `items.py` | items | Basic item CRUD example |

## Testing Commands

```bash
# Test module directly
python -m backend.app.test_scripts.typer.commands.my_feature my_command "test"

# Test through main CLI
python main.py myfeature my-command "test"

# Show help
python main.py myfeature --help
python main.py myfeature my-command --help
```

## Workflow

1. **Identify API endpoints** to expose (check `backend/app/api/routes/`)
2. **Copy template** from `commands/_template.py`
3. **Implement commands** following existing patterns
4. **Register** in `main.py`
5. **Document** in `COMMANDS.md`
6. **Test** with `--verbose` flag
7. **Update Documentation** 

## Style Guidelines

- Use emoji for status: ✅ success, ❌ error, ⚠️ warning, 🔍 info
- Human-readable output by default, `--json` for scripting
- Include `--verbose` for debugging
- Add docstrings with examples
- Use descriptive help text for all arguments/options
- Exit code 0 for success, 1 for errors
