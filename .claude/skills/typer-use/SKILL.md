---
name: typer-use
description: Use the TinyFoot Typer CLI to explore backend data and functionality instead of reading crud.py/models.py files. Use when: (1) reviewing existing stories, rooms, personas, or other entities, (2) understanding current database state, (3) validating API responses, (4) exploring relationships between entities, (5) discovering what modules and commands are available. Prefer CLI over file reading for data exploration. The CLI is ground truth — always prefer --help output over static docs.
---

# Typer Use

Use the TinyFoot CLI to explore backend functionality and data instead of searching through code files.

## When to Use CLI (Instead of Reading Code)

| Task | Use CLI | Don't Use CLI |
|------|---------|---------------|
| See what stories exist | `stories list` | Reading crud.py |
| Check story structure | `stories get ID --json` | Reading models.py |
| View room participants | `rooms list-participants ID` | Grepping routes |
| Understand entity fields | `--json` output | Reading Pydantic models |
| Validate state schema | `stories validate-state-schema` | Manual inspection |
| Check user's data | `users summary` | Database queries |

## When to Read Code Instead

- Understanding business logic implementation
- Modifying API behavior
- Adding new features
- Debugging specific functions

## Setup

Working directory: `backend/app/test_scripts/typer`

The venv is inherited from the Claude Code shell environment — explicit activation is usually not needed. If commands fail with import errors, activate defensively:

```bash
source /home/josep/dog/backend/.venv/bin/activate
```

**Important:** Shell state does not persist between Bash calls. If you activate the venv and run a command, do it in a single chained call:
```bash
source /home/josep/dog/backend/.venv/bin/activate && python main.py stories list --json
```

Requires `test.env` with `TEST_USER_EMAIL` and `TEST_USER_PASSWORD`.

## Discovery: Always Start Here

**`--help` output is ground truth. It reflects the live code. Static docs can be stale.**

```bash
# What modules are currently available?
python main.py --help

# What commands does a module expose?
python main.py stories --help
python main.py rooms --help

# What are the exact options for a command?
python main.py stories create --help
```

Run `python main.py --help` first in any new session or when uncertain. The module list evolves — don't rely on memory or docs for what exists.

### List Commands (Discovery)

```bash
python main.py stories list --json
python main.py rooms list --json
python main.py personas list-personas --json
python main.py personas list-archetypes --json
python main.py personas list-traits --json
python main.py conflicts list-groups --json
python main.py users my-stories
python main.py users my-rooms
```

### Get Commands (Details)

```bash
python main.py stories get STORY_ID --json
python main.py rooms get ROOM_ID --json
python main.py personas get-persona PERSONA_ID --json
python main.py conflicts get-group GROUP_ID --json
```

### Relationship Exploration

```bash
# Story's rooms
python main.py stories list-rooms STORY_ID --json

# Story's state variables
python main.py stories list-state-vars STORY_ID --json

# Room's participants
python main.py rooms list-participants ROOM_ID --json

# Room's messages
python main.py rooms list-messages ROOM_ID --json

# Conflict group members
python main.py conflicts list-members GROUP_ID --json

# Groups containing a trait
python main.py conflicts by-trait TRAIT_ID --json
```

### Validation Commands

```bash
# Check story state schema
python main.py stories validate-state-schema STORY_ID

# Check conflict group cardinality
python main.py conflicts validate GROUP_ID

# Check if trait conflicts with persona
python main.py conflicts check-persona PERSONA_ID --trait TRAIT_ID
```

### User Context

```bash
# Who am I?
python main.py users whoami

# Full user summary
python main.py users summary --json

# My story progress
python main.py users my-progress USER_PERSONA_ID STORY_ID --json

# My story timeline
python main.py users my-timeline USER_PERSONA_ID STORY_ID --json
```

## Common Exploration Workflows

### Understanding a Story's Structure

```bash
# 1. Get story details
python main.py stories get STORY_ID --json

# 2. Check its state schema
python main.py stories list-state-vars STORY_ID --json

# 3. Validate schema
python main.py stories validate-state-schema STORY_ID

# 4. See associated rooms
python main.py stories list-rooms STORY_ID --json
```

### Understanding the Persona System

```bash
# 1. List archetypes
python main.py personas list-archetypes --json

# 2. List traits
python main.py personas list-traits --json

# 3. List personas
python main.py personas list-personas --json

# 4. Get specific persona details
python main.py personas get-persona PERSONA_ID --json

# 5. Check user-personas
python main.py personas list-user-personas --json
```

### Understanding Room State

```bash
# 1. List rooms
python main.py rooms list --json

# 2. Get room details
python main.py rooms get ROOM_ID --json

# 3. See participants
python main.py rooms list-participants ROOM_ID --json

# 4. See recent messages
python main.py rooms list-messages ROOM_ID --limit 20 --json
```

### Understanding Trait Conflicts

```bash
# 1. List all conflict groups
python main.py conflicts list-groups --json

# 2. Get group details
python main.py conflicts get-group GROUP_ID --json

# 3. See group members
python main.py conflicts list-members GROUP_ID --json

# 4. Check what groups a trait belongs to
python main.py conflicts by-trait TRAIT_ID --json
```

## JSON Output Parsing

Use `--json` flag and pipe to `jq` for specific data:

```bash
# Get story title
python main.py stories get ID --json | jq '.title'

# List all published stories
python main.py stories list --json | jq '.data[] | select(.is_published == true)'

# Count entities
python main.py personas list-personas --json | jq '.count'

# Extract IDs only
python main.py rooms list --json | jq '.data[].room_id'
```

## Affordance Introspection

Several modules expose an affordance layer — a semantic model of what operations are possible and what data they require. Use this before executing, especially when planning a workflow.

```bash
# General affordance system
python main.py affordances --help

# Story-specific affordances
python main.py story-affordances list          # all story operations
python main.py story-affordances dimensions   # all data dimensions/schema
python main.py story-affordances available    # what's possible given current context
python main.py story-affordances scenario     # affordances for common scenarios
python main.py story-affordances preview      # preview an action before taking it
python main.py story-affordances elaborate    # what's still underspecified
```

Use affordance introspection to understand the shape of a domain before running create/update commands.

### MCP vs CLI for Affordances

The `demo-builder` MCP server exposes the same affordance system (`affordance_list`, `affordance_available`, `affordance_preview`, etc.).

- **Use MCP** when planning/reasoning in a conversation — no Bash call needed, output is inline
- **Use CLI** when already in an execution workflow, or when chaining with other commands

Never run both for the same query. Pick based on context.

## Module Reference

The module list evolves. Run `python main.py --help` for the current authoritative list.

Known modules (as of last `--help` run):

| Module | Purpose |
|--------|---------|
| `stories` | CYOA stories, nodes, choices, state, progress |
| `personas` | Archetypes, traits, qualities, personas |
| `rooms` | Chat rooms, participants, messages, runtime |
| `users` | Current user info and data |
| `conflicts` | Trait conflict groups |
| `agents` | Agent registry CRUD |
| `agent-demos` | Agent orchestration demo setup |
| `catalog` | LLM catalog — providers and models |
| `affordances` | General affordance introspection |
| `story-affordances` | Story-specific affordance introspection |
| `gauntlet` | Integrated demo system |
| `demos` | Demo configuration and styling |
| `pages` | Page layout management |
| `presets` | Panel preset browsing |
| `panels` | Room panel configuration |
| `embedder` | Vector embedding queries |
| `svgs` | SVG library commands |

Run `python main.py <module> --help` to discover current commands in any module.
