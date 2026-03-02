# Affordance Introspection MCP Server

An MCP server that provides affordance introspection tools for the Dog platform's Demo-builder system.

## What It Does

This server enables agents (like Claude) to **introspect the affordance space** before taking actions:

| Tool | Question It Answers |
|------|---------------------|
| `affordance_list` | What affordances exist? |
| `affordance_dimensions` | What dimensions are available? |
| `affordance_available` | What can I do right now? |
| `affordance_preview` | What would happen if I did X? |
| `affordance_elaborate` | What do I need to specify? |
| `affordance_patterns` | What are idiomatic patterns? |

## Why This Matters

Instead of trial-and-error with API calls, an agent can:

1. Query what's possible given current state
2. Preview actions before executing them
3. Progressively elaborate specifications
4. Understand constraint violations

This is the difference between *blind imperative action* and *reasoned compositional planning*.

## Installation

### Prerequisites

- Python 3.12+
- The Dog backend running at `localhost:8000`

### Setup

```bash
cd mcpmvp
uv sync
```

### Running Standalone

```bash
# List available tools
fastmcp list affordance_server.py

# Call a tool
fastmcp call affordance_server.py affordance_list

# Call with parameters
fastmcp call affordance_server.py affordance_elaborate '{"affordance": "add_panel"}'
```

### Installing in Claude Code

```bash
fastmcp install affordance_server.py --name "Affordance Introspection"
```

## Tools Reference

### `affordance_list`
List all affordances, optionally filtered by category.

### `affordance_dimensions`
Get all dimensions with their types, options, and defaults.

### `affordance_get`
Get full details of a specific affordance.

### `affordance_available`
Query what's available given current context.

### `affordance_preview`
Preview an action before taking it.

### `affordance_elaborate`
Understand what dimensions need specification.

### `affordance_patterns`
Get documented composition patterns.
