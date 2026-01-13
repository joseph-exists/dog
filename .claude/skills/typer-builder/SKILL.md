---
name: typer-builder
description: Build and extend the TinyFoot Typer CLI with new commands and modules. Use when: (1) creating new CLI command modules, (2) adding commands to existing modules, (3) exposing API endpoints as CLI commands, (4) working with backend/app/test_scripts/typer/
---

# Typer Builder

Build and extend the TinyFoot CLI with new Typer commands and modules.

## When NOT to Use

- General Python CLI questions (not TinyFoot-specific)
- Backend API route development (use standard FastAPI patterns)
- Frontend tooling

## Workflow

1. **Read the template**: `backend/app/test_scripts/typer/commands/_template.py`
2. **Copy template** to `commands/<feature>.py`
3. **Implement commands** following template patterns
4. **Register** in `main.py`:
   ```python
   from commands import my_feature
   app.add_typer(my_feature.app, name="myfeature", help="My feature commands")
   ```
5. **Test** with `--verbose` flag
6. **Document** in `COMMANDS.md`

## Environment Setup

```bash
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/typer
```

## Key Files

| File | Purpose |
|------|---------|
| `commands/_template.py` | **Start here** - copy for new modules |
| `main.py` | Register new command modules |
| `COMMANDS.md` | Document commands |
| `auth_helper.py` | Authentication utilities |

## Existing Modules

| Module | CLI Name | Description |
|--------|----------|-------------|
| `stories.py` | stories | Story and state schema management |
| `personas.py` | personas | Archetypes, traits, qualities, personas |
| `rooms.py` | rooms | Chat rooms and participants |
| `users.py` | users | Current user info |
| `trait_conflicts.py` | conflicts | Trait conflict groups |
| `items.py` | items | Basic CRUD example |

## Quick Patterns

### Import Auth Helper
```python
from ..auth_helper import get_authenticated_session
```

### Standard Options
```python
limit: Annotated[int, typer.Option(help="Max items")] = 20
offset: Annotated[int, typer.Option(help="Pagination offset")] = 0
json_output: Annotated[bool, typer.Option("--json")] = False
verbose: Annotated[bool, typer.Option("--verbose", "-v")] = False
force: Annotated[bool, typer.Option("--force", "-f")] = False
```

### Standard CRUD Commands
For a resource, implement: `create`, `list`, `get`, `update`, `delete`

## Style Guidelines

- Emoji status: ✅ success, ❌ error, ⚠️ warning, 🔍 info
- Human-readable by default, `--json` for scripting
- Always include `--verbose` for debugging
- Exit code 0 success, 1 error

## Testing

```bash
# Through main CLI
python main.py <module> <command> [args]
python main.py <module> --help

# Direct module test
python -m backend.app.test_scripts.typer.commands.<module> <command> [args]
```
