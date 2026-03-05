---
name: agent-registry
description: |
  Agent registry system for database-backed agent configurations with PydanticAI runtime instantiation.
  Use when working with:
  - Agent models, CRUD, or API routes (models.py UserAgentConfig*, crud.py, agent_routes.py)
  - AgentRegistryService or tool_registry.py
  - Creating, configuring, or debugging agents
  - Agent-room participation system

  Triggers: UserAgentConfig, AgentConfig, agent_registry_service, tool_registry, agent_routes, create agent, configure agent
---

# Agent Registry

Database-backed agent configuration system that bridges stored definitions to runtime PydanticAI Agent instances.

## Architecture

```
API Routes (agent_routes.py)         → CRUD endpoints with tiered access
         ↓
AgentRegistryService                 → Caching, validation, instantiation
         ↓
CRUD (crud.py)                       → Repository pattern operations
         ↓
UserAgentConfig Models (models.py)   → 6-tier SQLModel pattern
         ↓
Tool Registry (tool_registry.py)     → Hybrid tool association
         ↓
Agent Orchestration (agent_runner.py) → Runtime execution, A2A, AG-UI
```

**Key Files:**
- `backend/app/models.py` - UserAgentConfigBase through UserAgentConfigsPublic (lines 3685-3920)
- `backend/app/crud.py` - agent config CRUD functions
- `backend/app/services/agent_registry_service.py` - Service singleton with caching
- `backend/app/services/agent_instance.py` - Runtime PydanticAI Agent construction
- `backend/app/agents/tool_registry.py` - Tool definitions and mappings
- `backend/app/api/routes/agent_routes.py` - REST endpoints

## Core Patterns

### 1. Model Hierarchy (6-Tier)

```python
UserAgentConfigBase      # Shared properties (name, slug, model_name, system_prompt, etc.)
UserAgentConfigCreate    # API input - inherits Base
UserAgentConfigUpdate    # Partial updates - all fields optional
UserAgentConfig          # Database table (table=True), adds id, owner_id, timestamps, version
UserAgentConfigPublic    # API response - adds id, timestamps
UserAgentConfigsPublic   # Collection response - data: list + count: int
```

> **Note**: Models are prefixed with `User` to reflect that agents are user-owned resources with tiered access (personal/system scope).

### 2. Tiered Access Control

| Scope | Created By | Visible To | Modifiable By |
|-------|-----------|------------|---------------|
| `system` | Admins only | All users | Admins only |
| `personal` | Any user | Owner + admins | Owner + admins |

### 3. Service Caching

```python
# AgentRegistryService maintains two caches:
_config_cache: dict[str, AgentConfig]      # slug → config from DB
_runtime_agents: dict[str, Agent[Any,Any]] # slug → instantiated PydanticAI Agent

# Cache invalidation on update/delete - next get_agent() re-instantiates
```

### 4. Hybrid Tool Registration

```python
# Core tools: Define in Python, register at module load
register_tool("get_story_outline", ToolDefinition(...))
register_agent_tools("StoryAdvisor", ["get_story_outline", "get_participants"])

# Dynamic tools: Store in AgentConfig.tool_config JSON field
# Processed during _instantiate_agent()
```

## Common Tasks

### Add New Agent Config Field

1. Add to `AgentConfigBase` in models.py
2. Add optional version to `AgentConfigUpdate`
3. Create migration: `alembic revision --autogenerate -m "Add field to agent_configs"`
4. Apply: `alembic upgrade head`

### Create Agent via API

```bash
POST /api/v1/agents
{
  "name": "My Agent",
  "slug": "my-agent",
  "description": "Does something useful",
  "model_name": "openai:gpt-4o-mini",
  "system_prompt": "You are a helpful assistant...",
  "scope": "personal"
}
```

### Extend AgentRegistryService

When adding service methods:
- Accept `session: Session` as first parameter
- Use crud functions for DB operations
- Call `self._invalidate_cache(slug)` after mutations
- Return model types, not dicts

### Register Tools for Agent

```python
# In tool_registry.py or agent module
from app.agents.tool_registry import register_tool, register_agent_tools, ToolDefinition

register_tool("my_tool", ToolDefinition(
    name="my_tool",
    description="Does X",
    implementation=my_tool_fn,
))

register_agent_tools("MyAgent", ["my_tool", "other_tool"])
```

## Integration Points

### With Legacy Agent Registry

```python
# agent_runner.py uses fallback pattern during migration
agent = agent_registry_service.get_agent(session, slug)
if not agent:
    agent = legacy_get_agent(slug)  # Falls back to app.agents.agent_registry
```

### With Room Participants

Agents join rooms via `RoomParticipant` with `participant_type="agent"` and `participant_id=slug`.
The agent_runner queries active agent participants, then uses registry service to get Agent instances.

## References

| Document | Purpose |
|----------|---------|
| [Agent Demo Quick-Start](../../backend/app/services/service-docs/agent-demo-quickstart.md) | **Ready-to-use demo agent configurations** |
| [Agent Orchestration Reference](../../backend/app/services/service-docs/agent-orchestration-reference.md) | **Runtime orchestration patterns & demo capabilities** |
| [Agent User Guide](./references/agent-user-guide.md) | End-user reference for working with agents |
| [Agent Developer Reference](./references/agent-developer-reference.md) | Technical reference for implementation |
| [A2A & AG-UI Roadmap](./references/a2a-ag-ui-roadmap.md) | Agent-to-Agent and UI component system |
| [A2A & AG-UI Reference Card](./references/a2a-ag-ui-reference-card.md) | GTM/Product owner summary |
| [Agent Registry Plan](./references/agent-registry-plan.md) | Original architecture and design |
| [Agent Provider Integration](./references/agent-provider-integration.md) | LLM provider configuration |
