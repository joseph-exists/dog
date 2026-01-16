# Typer-Forge Command Reference

All commands require venv activation and running from the typer-forge directory:

```bash
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/forge-admin/typer-forge
```

## Top-Level

| Command | Description |
|---------|-------------|
| `python main.py test` | Test API connection |
| `python main.py whoami` | Show current user |
| `python main.py version` | Show CLI version |

## Users

| Command | Description |
|---------|-------------|
| `users me [--json]` | Current user info |
| `users create USERNAME -e EMAIL [-p PASS]` | Create user (admin) |
| `users get USERNAME` | Get user info |
| `users delete USERNAME [-f]` | Delete user (admin) |

## Issues

| Command | Description |
|---------|-------------|
| `issues create OWNER REPO "TITLE" [-b BODY] [-a ASSIGNEE]` | Create issue |
| `issues get OWNER REPO NUMBER` | Get issue details |
| `issues list OWNER REPO [--state open\|closed\|all]` | List issues |
| `issues close OWNER REPO NUMBER` | Close issue |
| `issues reopen OWNER REPO NUMBER` | Reopen issue |
| `issues comment OWNER REPO NUMBER "TEXT"` | Add comment |
| `issues comments OWNER REPO NUMBER` | List comments |

## Wiki

| Command | Description |
|---------|-------------|
| `wiki create OWNER REPO "TITLE" [-c CONTENT] [-f FILE]` | Create page |
| `wiki get OWNER REPO "TITLE" [--raw]` | Get page |
| `wiki list OWNER REPO` | List all pages |
| `wiki edit OWNER REPO "TITLE" [-c CONTENT] [-f FILE]` | Edit page |
| `wiki delete OWNER REPO "TITLE" [-f]` | Delete page |
| `wiki history OWNER REPO "TITLE"` | Show revisions |

## Repos

| Command | Description |
|---------|-------------|
| `repos create NAME [-d DESC] [--private]` | Create repo |
| `repos get OWNER REPO` | Get repo info |
| `repos list [--owner USER]` | List repos |
| `repos delete OWNER REPO [-f]` | Delete repo |
| `repos fork OWNER REPO` | Fork repo |
| `repos search "QUERY"` | Search repos |

## Orgs

| Command | Description |
|---------|-------------|
| `orgs create NAME [-n FULLNAME]` | Create org |
| `orgs get NAME` | Get org info |
| `orgs list` | List all orgs |
| `orgs delete NAME [-f]` | Delete org |
| `orgs members NAME` | List members |
| `orgs repos NAME` | List org repos |
| `orgs teams NAME` | List teams |

## Admin

| Command | Description |
|---------|-------------|
| `admin list-users` | List all users |
| `admin list-orgs` | List all orgs |
| `admin list-emails` | List registered emails |
| `admin cron` | List cron tasks |

## Common Options

- `--json` - Output as JSON
- `-v, --verbose` - Verbose output
- `-f, --force` - Skip confirmation
- `--help` - Show command help
