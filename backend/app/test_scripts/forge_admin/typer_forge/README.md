# Forge CLI

A Typer-based CLI for managing Forgejo instances using the generated OpenAPI Python SDK.

## Quick Start

```bash

source ~/dog/backend/.venv/bin/activate

cd backend/app/test_scripts/forge-admin/typer-forge

# Test connection
python main.py test

# Show current user
python main.py whoami

# Get help
python main.py --help
python main.py repos --help
```

## Configuration

Edit `forge_client.py` to change:

```python
FORGE_URL = "http://localhost:3000/api/v1"
API_TOKEN = "your-token-here"
```

Generate tokens at: `http://localhost:3000/user/settings/applications`

### Token Scopes

| Scope | Required For |
|-------|--------------|
| `read:user` | `users me`, `whoami` |
| `write:user` | Creating user repos |
| `read:admin` | `admin list-users`, `admin list-orgs` |
| `write:admin` | `users create`, `users delete` |
| `read:repository` | `repos list`, `repos get` |
| `write:repository` | `repos create`, `repos delete` |
| `read:issue` | `issues list`, `issues get` |
| `write:issue` | `issues create`, `issues close` |
| `read:organization` | `orgs list`, `orgs get` |
| `write:organization` | `orgs create`, `orgs delete` |

## Current Commands

### Top-level
- `python main.py test` - Test API connection
- `python main.py whoami` - Show authenticated user
- `python main.py version` - Show CLI version

### Users (`users`)
```bash
python main.py users me                           # Current user info
python main.py users me --json                    # As JSON
python main.py users create USERNAME --email X   # Create user (admin)
python main.py users get USERNAME                 # Get user info
python main.py users delete USERNAME              # Delete user (admin)
```

### Admin (`admin`)
```bash
python main.py admin list-users                   # List all users
python main.py admin list-orgs                    # List all organizations
python main.py admin list-emails                  # List registered emails
python main.py admin cron                         # List cron tasks
```

### Repositories (`repos`)
```bash
python main.py repos create NAME                  # Create repo
python main.py repos create NAME --private        # Create private repo
python main.py repos get OWNER REPO               # Get repo info
python main.py repos list                         # List your repos
python main.py repos list --owner USER            # List user's repos
python main.py repos delete OWNER REPO            # Delete repo
python main.py repos fork OWNER REPO              # Fork a repo
python main.py repos search "query"               # Search repos
```

### Issues (`issues`)
```bash
python main.py issues create OWNER REPO "Title"   # Create issue
python main.py issues create OWNER REPO "T" -b X  # With body
python main.py issues get OWNER REPO NUMBER       # Get issue
python main.py issues list OWNER REPO             # List issues
python main.py issues list OWNER REPO --state closed
python main.py issues close OWNER REPO NUMBER     # Close issue
python main.py issues reopen OWNER REPO NUMBER    # Reopen issue
python main.py issues comment OWNER REPO NUM "X"  # Add comment
python main.py issues comments OWNER REPO NUM     # List comments
```

### Organizations (`orgs`)
```bash
python main.py orgs create NAME                   # Create org
python main.py orgs create NAME -n "Full Name"    # With full name
python main.py orgs get NAME                      # Get org info
python main.py orgs list                          # List all orgs
python main.py orgs delete NAME                   # Delete org
python main.py orgs members NAME                  # List members
python main.py orgs repos NAME                    # List org repos
python main.py orgs teams NAME                    # List teams
```

## Directory Structure

```
typer-forge/
├── main.py              # CLI entry point, registers commands
├── forge_client.py      # Shared API client configuration
├── README.md            # This file
└── commands/
    ├── __init__.py
    ├── _template.py     # Template for new modules
    ├── admin.py         # Admin operations
    ├── users.py         # User management
    ├── repos.py         # Repository management
    ├── issues.py        # Issue tracking
    └── orgs.py          # Organization management
```

## Adding New Commands

### 1. Create a new command module

Copy the template:
```bash
cp commands/_template.py commands/webhooks.py
```

### 2. Import the relevant API

```python
# In commands/webhooks.py
from forge_client import get_repository_api
from openapi_client.models.create_hook_option import CreateHookOption
from openapi_client.rest import ApiException
```

### 3. Implement commands

```python
app = typer.Typer(help="Webhook management commands")

@app.command()
def create(
    owner: Annotated[str, typer.Argument(help="Repo owner")],
    repo: Annotated[str, typer.Argument(help="Repo name")],
    url: Annotated[str, typer.Option("--url", "-u", help="Webhook URL")],
):
    """Create a webhook for a repository."""
    try:
        repo_api = get_repository_api()
        hook = repo_api.repo_create_hook(
            owner=owner,
            repo=repo,
            body=CreateHookOption(
                type="forgejo",
                config={"url": url, "content_type": "json"},
                events=["push"],
                active=True,
            )
        )
        typer.secho(f"✅ Webhook created: {hook.id}", fg=typer.colors.GREEN)
    except ApiException as e:
        handle_api_error(e, "create webhook")
```

### 4. Register in main.py

```python
from commands import webhooks
app.add_typer(webhooks.app, name="webhooks", help="Webhook management")
```

## SDK Reference

The SDK is located at: `~/dog/forge-sdk/python-sdk/`

### Finding available APIs

```bash
ls ~/dog/forge-sdk/python-sdk/openapi_client/api/
# admin_api.py, issue_api.py, organization_api.py, repository_api.py, user_api.py, etc.
```

### Finding available models

```bash
ls ~/dog/forge-sdk/python-sdk/openapi_client/models/
# create_issue_option.py, create_org_option.py, create_repo_option.py, etc.
```

### Checking method signatures

```bash
grep -A 10 "def method_name" ~/dog/forge-sdk/python-sdk/openapi_client/api/some_api.py
```

**Note:** Parameter names vary - most use `body`, but some (like `org_create`) use semantic names like `organization`. Check the signature if you get validation errors.

## Extension Ideas

### Near-term additions

| Module | Commands | APIs needed |
|--------|----------|-------------|
| `pulls` | create, list, merge, review | `RepositoryApi` |
| `webhooks` | create, list, delete, test | `RepositoryApi` |
| `keys` | add, list, delete SSH keys | `UserApi`, `AdminApi` |
| `labels` | create, list, delete | `IssueApi` |
| `milestones` | create, list, close | `IssueApi` |
| `releases` | create, list, upload assets | `RepositoryApi` |
| `actions` | list runs, view logs | `RepositoryApi` |

### Workflow scripts

Create compound commands that chain multiple operations:

```python
@app.command()
def setup_project(name: str, org: str = None):
    """Create repo with standard labels, branch protection, webhooks."""
    # 1. Create repo
    # 2. Add standard labels
    # 3. Create initial issues from template
    # 4. Set up branch protection
    # 5. Add webhooks
```

### Interactive mode

Use `typer.prompt()` for interactive workflows:

```python
@app.command()
def wizard():
    """Interactive project setup wizard."""
    name = typer.prompt("Repository name")
    private = typer.confirm("Make private?", default=False)
    # ...
```

### Import to backend

When ready to use in the main application:

1. Move `forge_client.py` to `backend/app/services/forge_client.py`
2. Load config from environment variables instead of hardcoded values
3. Create a service class that wraps the SDK
4. Add dependency injection for FastAPI routes

## Troubleshooting

### "Missing required argument" / "Unexpected keyword argument"
Check the actual method signature - parameter names vary in the SDK.

### 403 Forbidden
Token missing required scope. Check the scope table above.

### 422 Validation Error
Check the error body for details. Common issues:
- URLs need full protocol (`https://`, not just domain)
- Required fields missing
- Invalid enum values

### Connection refused
Ensure Forgejo is running on the configured URL.
