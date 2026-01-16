---
name: forgejo-workflow
description: |
  Manage collaborative work with Josep using Forgejo for issue tracking and documentation.
  Use when: (1) checking assigned issues or tasks, (2) creating/updating issues,
  (3) writing wiki documentation, (4) reporting progress on work, (5) user asks
  "check my issues", "what should I work on", "create an issue", "update the wiki",
  or any Forgejo/issue/ticket-related request. Works with typer-forge CLI.
---

# Forgejo Workflow

Claude collaborates with Josep using Forgejo as the project management backend. All operations use the typer-forge CLI located at `backend/app/test_scripts/forge-admin/typer-forge/`.

## Setup

typer-forge requires the backend venv (for SDK dependencies) plus typer:

```bash
# One-time setup
source /home/josep/dog/backend/.venv/bin/activate
uv pip install typer
```

## Quick Reference

```bash
# Always activate venv first
source /home/josep/dog/backend/.venv/bin/activate
cd /home/josep/dog/backend/app/test_scripts/forge-admin/typer-forge

# Check identity
python main.py whoami

# List assigned issues
python main.py issues list claude claude-workspace --state open

# Get issue details
python main.py issues get claude claude-workspace <NUMBER>

# Comment on issue
python main.py issues comment claude claude-workspace <NUMBER> "message"

# Create wiki page
python main.py wiki create claude claude-workspace "Title" --content "# Content"
```

## Workflow: Check Assigned Issues

When user asks to check issues or what to work on:

1. List open issues in claude/claude-workspace
2. For each issue assigned to claude, get full details
3. Summarize in a table: number, title, priority indicators
4. Ask which to work on, or proceed if one is obvious

## Workflow: Work on Issue

When starting work on an issue:

1. Read the full issue body
2. Comment acknowledging work is starting
3. Break down into subtasks if complex
4. For simple subtasks, delegate to haiku sub-agents (see below)
5. Do the work
6. Comment with completion status and summary
7. Ask user if issue should be closed

## Workflow: Create Issue

When user wants to create an issue:

1. Gather: title, description, assignee (default: claude)
2. Create with `issues create`
3. Report the issue number and URL

## Workflow: Update Wiki

When documenting work or creating proposals:

1. Determine appropriate page title (use kebab-case)
2. Write content in markdown
3. Create or edit wiki page
4. Link from related issues if applicable

## Sub-Agent Delegation

For smaller, well-defined tasks, spawn haiku agents to save context and cost:

```
Task tool with model="haiku" for:
- Writing formatted wiki content from notes
- Formatting issue comments with markdown tables
- Generating boilerplate documentation
- Searching/summarizing related issues
```

Keep opus for: design decisions, complex debugging, architectural proposals.

## Repository Context

- **Owner**: claude
- **Repo**: claude-workspace
- **Wiki**: http://localhost:3000/claude/claude-workspace/wiki
- **Issues**: http://localhost:3000/claude/claude-workspace/issues

## Token Configuration

Current token stored in `forge_client.py`. Switch between:
- Claude token: `4b0f449a6dcf184b0ee94a1fcb0c8b768ca8b779`
- Admin token: `63d42c1df2b231be68209d45739f14732f06eaba`

## Shadow Forgejo Integration

The backend has a ShadowService (`app/services/shadow_service.py`) that automatically versions entities to Forgejo:

- **Agents** and **Stories** are versioned on create/update
- Each entity gets its own repo with JSON snapshots
- Requires user to have a ShadowUser mapping with Forgejo token

Key files:
- `app/models.py`: ShadowUser, ShadowRepo, ShadowVersion models
- `app/services/shadow_service.py`: Versioning service
- `app/api/routes/agent_routes.py`, `stories.py`: Integration hooks

## Command Reference

See [references/typer-forge-commands.md](references/typer-forge-commands.md) for full command list.
