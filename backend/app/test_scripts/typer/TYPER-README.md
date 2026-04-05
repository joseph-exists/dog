# TinyFoot CLI (Typer)

A command-line interface for running test scripts and operations in staging environments.

## Quick Start

### Test Authentication

```bash
# Test your auth setup
python auth_helper.py
```

### Run Example Commands

```bash
# Show all available commands
python main.py --help

# Run demo commands
python main.py demo hello "World"
python main.py demo goodbye "Alice" --formal
```

## Setup

### Prerequisites

1. **Backend server running** on `http://localhost:8000`
2. **test.env file** with credentials:
   ```bash
   TEST_USER_EMAIL=test@example.com
   TEST_USER_PASSWORD=yourpassword
   ```
3. **Typer installed** (should be in project dependencies)

### Installation

Typer should already be installed with the project. If not:

```bash
cd backend
uv add typer
```

## Directory Structure

```
typer/
├── README.md              # This file
├── REFERENCE.md           # Comprehensive reference guide
├── main.py               # Main CLI entry point
├── wonka.py              # Example commands
├── auth_helper.py        # Authentication utilities
└── commands/             # Command modules
    ├── __init__.py
    └── _template.py      # Template for new commands
    └── *.py              # 20+ existing command modules
    └── COMMANDS.md       # Commands documentation

```

## Adding New Commands

### Option 1: Quick Start (Copy Template)

```bash
# Copy template to create new command module
cd backend/app/test_scripts/typer/commands
cp _template.py stories.py

# Edit stories.py to add your commands
# Then register in main.py
```

### Option 2: From Scratch

1. **Create command module** in `commands/`:

```python
# commands/stories.py
import typer
from typing_extensions import Annotated
from auth_helper import get_authenticated_session

app = typer.Typer(help="Story management commands")

@app.command()
def create(title: Annotated[str, typer.Argument(help="Story title")]):
    """Create a new story."""
    session = get_authenticated_session()
    response = session.post(
        "http://localhost:8000/api/v1/stories",
        json={"title": title, "current_version": 1}
    )

    if response.status_code == 200:
        typer.secho("✅ Story created!", fg=typer.colors.GREEN)
    else:
        typer.secho("❌ Failed", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
```

2. **Register in main.py**:

```python
# main.py
from .commands import stories

app.add_typer(stories.app, name="stories")
```

3. **Test it**:

```bash
python main.py stories create "My Story"
```

## Common Commands

### Authentication

```bash
# Test authentication
python auth_helper.py
```

### Help

```bash
# Show all commands
python -m backend.app.test_scripts.typer.main --help

# Show help for specific command
python -m backend.app.test_scripts.typer.main demo --help
python -m backend.app.test_scripts.typer.main demo hello --help
```

### Version

```bash
python -m backend.app.test_scripts.typer.main version
```

## Examples

### Basic Command

```bash
python -m backend.app.test_scripts.typer.main demo hello "World"
```

### With Options

```bash
python -m backend.app.test_scripts.typer.main demo goodbye "Alice" --formal
```

### Verbose Mode

```bash
python -m backend.app.test_scripts.typer.main stories create "My Story" --verbose
```

### JSON Output

```bash
python -m backend.app.test_scripts.typer.main stories list --json
```

### Story Authoring (State Machine)

```bash
# Add nodes with explicit version and type
python -m backend.app.test_scripts.typer.main stories add-node STORY_ID \
  --title "Start" --content "..." --start --version 2 --node-type "text"

# Create a new version before editing a published story
python -m backend.app.test_scripts.typer.main stories new-version STORY_ID

# Add guarded choice with state mutations
python -m backend.app.test_scripts.typer.main stories add-choice NODE_A NODE_B \
  --text "Take the risky path" \
  --requires-state '{"has_sword": true}' \
  --sets-state '{"courage": 1}'

# Add access requirements
python -m backend.app.test_scripts.typer.main stories add-requirement STORY_ID \
  --type quality --target-id REQUIREMENT_TARGET_UUID --desc "Requires brave trait"

# Inspect nodes and choices
python -m backend.app.test_scripts.typer.main stories list-nodes STORY_ID --version 2 --json
python -m backend.app.test_scripts.typer.main stories list-choices --story-id STORY_ID --json

# Resolve start node
python -m backend.app.test_scripts.typer.main stories start-node STORY_ID --version 2

# Unpublish if you need to revert a published story to draft
python -m backend.app.test_scripts.typer.main stories unpublish STORY_ID
```

### Story Progress (Playtesting)

```bash
# Start a new playthrough
python -m backend.app.test_scripts.typer.main stories create-progress USER_PERSONA_ID STORY_ID

# Get current node and choices
python -m backend.app.test_scripts.typer.main stories current-node USER_PERSONA_ID STORY_ID

# Make a choice
python -m backend.app.test_scripts.typer.main stories make-choice USER_PERSONA_ID STORY_ID CHOICE_ID

# Jump to ancestor and inspect timeline
python -m backend.app.test_scripts.typer.main stories jump USER_PERSONA_ID STORY_ID --expected-head-version 3 --choice-id CHOICE_ID
python -m backend.app.test_scripts.typer.main stories timeline USER_PERSONA_ID STORY_ID --json
```

### Room Runtime (Shared Run)

```bash
python -m backend.app.test_scripts.typer.main rooms runtime-get ROOM_ID --json
python -m backend.app.test_scripts.typer.main rooms runtime-put ROOM_ID --user-persona-id USER_PERSONA_ID
python -m backend.app.test_scripts.typer.main rooms runtime-advance ROOM_ID --choice-id CHOICE_ID
```

### Embedder Queries

```bash
# Query OpenAPI embeddings
python -m backend.app.test_scripts.typer.main embedder api-query \
  --query "How do I create a story?" --top-k 5

# Query embedded SDK/types/schema code chunks
python -m backend.app.test_scripts.typer.main embedder code-query \
  --query "How is room panel configuration updated?" --kinds sdk_method,schema --top-k 8
```

## Testing Your Commands

### Test Module Directly

```bash
# Run command module directly (useful for development)
python -m backend.app.test_scripts.typer.commands.stories create "Test"
```

### Test Through Main CLI

```bash
# Run through main CLI (how users will use it)
python -m backend.app.test_scripts.typer.main stories create "Test"
```

## Best Practices

1. **Authentication**: Always use `get_authenticated_session()`
2. **Error Handling**: Check HTTP status codes and provide clear error messages
3. **Output**: Use consistent colors (✅ green for success, ❌ red for errors)
4. **Help Text**: Add docstrings and type annotations with help text
5. **Verbose Mode**: Include `--verbose` flag for debugging
6. **JSON Output**: Support `--json` flag for machine-readable output

## Common Patterns

See `REFERENCE.md` for comprehensive examples of:
- Authenticated API calls
- Arguments vs Options
- Output formatting
- Error handling
- Progress indicators
- Confirmation prompts
- File operations
- And much more!

## Troubleshooting

### Import Errors

If you get import errors:
- Ensure you're running from project root
- Check `__init__.py` files exist
- Use relative imports in command modules

### Authentication Failed

If authentication fails:
- Check `test.env` exists with correct credentials
- Verify backend server is running
- Run `python auth_helper.py` to test auth

### Command Not Found

If typer can't find your command:
- Check it's registered in `main.py`
- Verify `@app.command()` decorator is present
- Ensure module is imported correctly

## Resources

- **Detailed Reference**: See `REFERENCE.md` in this directory
- **Template**: Copy `commands/_template.py` to create new commands
- **Typer Docs**: https://typer.tiangolo.com/
- **Existing Scripts**: `../test_*.py` files for functionality to expose

## Development Workflow

1. **Plan**: Decide what functionality to expose
2. **Create**: Copy `_template.py` and modify
3. **Register**: Add to `main.py`
4. **Test**: Run directly and through main CLI
5. **Document**: Add help text and examples
6. **Deploy**: Make available in staging

## Next Steps

1. Review `REFERENCE.md` for detailed patterns and examples
2. Copy `commands/_template.py` to create your first command module
3. Register it in `main.py`
4. Test with `python -m backend.app.test_scripts.typer.main`
5. Add more commands as needed!
