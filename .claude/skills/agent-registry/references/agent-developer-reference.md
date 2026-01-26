# Agent Developer Reference

> Technical reference for implementing and extending the agent system

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          API Layer                                   │
│  agent_routes.py → CRUD endpoints, user settings                    │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Service Layer                                  │
│  AgentRegistryService → caching, instantiation, validation          │
│  agent_runner.py → execution, streaming, A2A, AG-UI                 │
│  context_provider.py → room context building                        │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        Data Layer                                    │
│  models.py → AgentConfig*, RoomParticipant, UserAgentSettings       │
│  crud.py → database operations                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Model Reference

### AgentConfigBase (Shared Properties)

```python
class AgentConfigBase(SQLModel):
    name: str = Field(max_length=100)           # Display name
    slug: str = Field(max_length=50)            # Unique identifier for @mentions
    description: str | None = Field(max_length=500, default=None)
    model_name: str = Field(default="openai:gpt-4o-mini")  # provider:model
    system_prompt: str | None = None            # Agent behavior instructions
    tool_config: dict | None = Field(sa_column=Column(JSON))
    deps_config: dict | None = Field(sa_column=Column(JSON))
    agent_metadata: dict | None = Field(sa_column=Column(JSON))
    is_enabled: bool = Field(default=True)
    scope: str = Field(default="personal")      # "personal" | "system"
    participation_mode: str = Field(default="on_mention")  # "always" | "on_mention" | "manual"
    is_coordinator: bool = Field(default=False) # Runs first, bypasses participation mode
    capabilities: list[str] = Field(sa_column=Column(JSON), default_factory=list)
```

### AgentConfig (Database Table)

```python
class AgentConfig(AgentConfigBase, table=True):
    __tablename__ = "agent_configs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID | None = Field(foreign_key="user.id")  # null for system agents
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = None
    version: int = Field(default=1)
```

### Model Hierarchy (6-Tier Pattern)

| Model | Purpose |
|-------|---------|
| `AgentConfigBase` | Shared properties |
| `AgentConfigCreate` | API input validation (inherits Base) |
| `AgentConfigUpdate` | Partial updates (all fields optional) |
| `AgentConfig` | Database model (`table=True`) |
| `AgentConfigPublic` | API response (adds id, timestamps) |
| `AgentConfigsPublic` | Collection response (`data` + `count`) |

---

## API Endpoints

### Agent CRUD

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| GET | `/agents/` | `?skip=0&limit=100&scope=` | `AgentConfigsPublic` | List agents (scope filter) |
| GET | `/agents/available` | - | `AgentConfigsPublic` | List enabled agents for rooms |
| GET | `/agents/{agent_id}` | - | `AgentConfigPublic` | Get single agent |
| POST | `/agents/` | `AgentConfigCreate` | `AgentConfigPublic` | Create agent |
| PUT | `/agents/{agent_id}` | `AgentConfigUpdate` | `AgentConfigPublic` | Update agent |
| DELETE | `/agents/{agent_id}` | - | `Message` | Delete agent |

### User Settings

| Method | Path | Request | Response | Description |
|--------|------|---------|----------|-------------|
| GET | `/agents/{agent_id}/my-settings` | - | `UserAgentSettingsPublic \| null` | Get user's config |
| PUT | `/agents/{agent_id}/my-settings` | `UserAgentSettingsUpdate` | `UserAgentSettingsPublic` | Set user's config |
| DELETE | `/agents/{agent_id}/my-settings` | - | `Message` | Clear user's config |

### Access Control

```python
# Users: see system + own personal agents
# Admins: see all agents

# Scope enforcement:
# - Users can only create scope="personal"
# - Admins can create scope="system"
```

---

## Agent Runner

### Key Functions

```python
# Main entry point for room messages
async def run_agents_for_message(
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
) -> list[dict[str, Any]]

# Explicit agent invocation (bypasses participation mode)
async def invoke_agent_manually(
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    session: AsyncSession,
) -> dict[str, Any]

# Streaming agent execution
async def run_agent_for_room_streaming(
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
    a2a_depth: int = 0,
) -> dict[str, Any]
```

### Execution Flow

```
run_agents_for_message()
    │
    ├─► Phase 1: Run Coordinators (is_coordinator=True)
    │   └─► run_agent_for_room_streaming() for each
    │
    └─► Phase 2: Run Regular Agents
        ├─► Check should_agent_respond_to_message()
        │   ├─ mode="always" → respond
        │   ├─ mode="on_mention" → check @mentions → respond if mentioned
        │   └─ mode="manual" → skip
        │
        └─► run_agent_for_room_streaming() for responding agents
```

### Streaming Execution Detail

```python
async def run_agent_for_room_streaming(...):
    # 1. Build context
    context = await build_room_context(room_id, session)

    # 2. Get agent with tools
    agent = await get_agent_instance_with_tools(session, agent_name)

    # 3. Create dependencies
    deps = AgentDeps(
        session=session,
        room_id=room_id,
        current_agent_slug=agent_name,
        a2a_depth=a2a_depth,
    )

    # 4. Build prompt with context
    full_prompt = build_agent_prompt(trigger_message, context, agent_name)

    # 5. Stream response
    async with agent.run_stream(full_prompt, deps=deps) as result:
        async for chunk in result.stream_text():
            new_content = chunk[prev_len:]  # Extract delta
            await publish_agent_token(room_id, agent_name, new_content)

    # 6. Emit final event with UI components
    payload = {
        "agent_name": agent_name,
        "content": full_response,
        "ui_components": [c.model_dump() for c in deps.ui_components],  # if any
    }
    await emit_event(session, room_id, "room_message.agent", payload)

    # 7. Process A2A mentions
    await process_agent_response(response, agent_name, room_id, session, a2a_depth)
```

---

## AgentDeps (Tool Context)

```python
@dataclass
class AgentDeps:
    session: AsyncSession           # Database access
    room_id: uuid.UUID              # Current room
    current_agent_slug: str         # Self-identification
    a2a_depth: int = 0              # Chain depth (max=2)
    ui_components: list[UIComponent] | None = None  # Collected UI

    def add_ui_component(self, component: UIComponent) -> None:
        """Add UI component to collection."""
        self.ui_components.append(component)
```

### Using in Tools

```python
async def my_custom_tool(ctx: RunContext[AgentDeps], arg: str) -> str:
    # Access dependencies
    session = ctx.deps.session
    room_id = ctx.deps.room_id

    # Self-awareness
    me = ctx.deps.current_agent_slug

    # Add UI component
    ctx.deps.add_ui_component(UIComponent(
        type="card",
        data={"title": "Result", "body": "..."}
    ))

    return "Tool result"
```

---

## A2A (Agent-to-Agent) Communication

### Tool: request_agent_assistance

```python
async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,    # Agent slug or name
    request: str,         # Question/request for target
) -> str:                 # Target's response
```

**Behavior:**
- Validates target is in room
- Prevents self-invocation
- Enforces `MAX_A2A_DEPTH = 2`
- Runs target agent non-streaming
- Returns response inline (same turn)

### Automatic @Mention Processing

```python
async def process_agent_response(
    response: str,
    responding_agent_slug: str,
    room_id: uuid.UUID,
    session: AsyncSession,
    current_depth: int,
    emit_internal_messages: bool = False,
) -> list[dict[str, Any]]
```

**Flow:**
1. `detect_mentions(response)` → set of @mentioned names
2. For each mention, check `is_agent_in_room()`
3. Skip if agent is in `manual` mode
4. Trigger `run_agent_for_room_streaming()` with depth+1

### Mention Detection

```python
def detect_mentions(message: str) -> set[str]:
    """
    Supports:
    - @AgentName (camelCase)
    - @agent-slug (kebab-case)
    - @"Agent Name" (quoted)

    Returns lowercase set for case-insensitive matching.
    """
```

---

## AG-UI (Agent-Generated UI)

### Tool: emit_ui_component

```python
def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str
```

### Component Types

| Type | Required Data | Optional Data |
|------|---------------|---------------|
| `card` | `title`, `body` | `subtitle`, `footer`, `variant`, `icon` |
| `list` | `items[]` | `title`, `ordered`, `variant` |
| `table` | `columns[]`, `rows[]` | `title`, `striped`, `compact` |
| `progress` | `items[]` (label, value) | `title`, `show_percentage` |
| `action_buttons` | `buttons[]` | `layout` |
| `code` | `code` | `language`, `title`, `line_numbers` |
| `quote` | `text` | `attribution`, `variant` |
| `alert` | `message` | `title`, `variant`, `dismissible` |
| `collapsible` | `title`, `content` | `default_open`, `icon` |
| `tabs` | `tabs[]` (label, content) | `default_tab` |
| `divider` | - | `label`, `variant` |

### Example Usage

```python
# In agent tool or response
emit_ui_component("card", {
    "title": "Character Profile",
    "subtitle": "Protagonist",
    "body": "Elena is a determined scientist...",
    "variant": "highlight",
})

emit_ui_component("progress", {
    "title": "Story Completion",
    "items": [
        {"label": "Plot", "value": 75, "color": "blue"},
        {"label": "Characters", "value": 90, "color": "green"},
    ]
})
```

### Frontend Rendering

```typescript
// components/AgentUI/AgentUIRenderer.tsx
import { AgentUIRenderer } from "@/components/AgentUI"

{message.ui_components?.map((component, idx) => (
  <AgentUIRenderer
    key={component.id || idx}
    component={component}
    onAction={(action) => handleAction(action)}
  />
))}
```

---

## Context Provider

### RoomContext Structure

```python
@dataclass
class RoomContext:
    room_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict | None           # {title, description, is_published}
    recent_messages: list[dict]       # Last N messages
    participants: list[dict]          # Active room members
    room_metadata: dict               # Room info
    active_agents: list[AgentInfo]    # Agents with capabilities
```

### AgentInfo

```python
@dataclass
class AgentInfo:
    slug: str
    name: str
    description: str
    participation_mode: str
    capabilities: list[str]
```

### Building Context

```python
context = await build_room_context(
    room_id=room_id,
    session=session,
    message_limit=20,  # Default: last 20 messages
)
```

### Prompt Building

```python
full_prompt = build_agent_prompt(
    trigger_message="User's message",
    context=context,
    current_agent_slug="StoryAdvisor",  # Excluded from "other agents" list
)
```

**Output Structure:**
```
Story: [title]
Description: [description]

Other agents in this room:
- DialogueCoach (@DialogueCoach): Specializes in dialogue [Capabilities: dialogue, voice]
- CharacterForge (@CharacterForge): Character development expert

You can reference other agents with @mentions if their expertise is needed.

Recent conversation:
User: Previous message
StoryAdvisor: Previous response

User message: [trigger_message]
```

---

## Room Participation

### RoomParticipant Model

```python
class RoomParticipant(SQLModel, table=True):
    id: uuid.UUID
    room_id: uuid.UUID                    # FK to room
    participant_id: str                   # UUID (user) or slug (agent)
    participant_type: str                 # "user" | "agent"
    role: str                             # "owner" | "member"
    joined_at: datetime
    left_at: datetime | None              # Soft delete timestamp
    active: bool = True
```

### Adding Agents to Rooms

```python
# Via API
POST /rooms/{room_id}/participants
{
    "participant_id": "agent-config-uuid-or-slug",
    "participant_type": "agent",
    "role": "member"
}

# Emits: participant.joined event
```

### Resolving Agent Participants

```python
async def resolve_agent_identifier(
    session: AsyncSession,
    participant_id: str,
) -> tuple[str | None, str | None, AgentConfig | None]:
    """
    Returns: (slug, display_name, config)

    Handles:
    - UUID participant_id → lookup by AgentConfig.id
    - String participant_id → lookup by AgentConfig.slug
    """
```

---

## Event Integration

### Agent Message Event

```python
await emit_event(
    session=session,
    room_id=room_id,
    event_type="room_message.agent",
    payload={
        "agent_name": "StoryAdvisor",
        "content": "Full response text...",
        "ui_components": [
            {"type": "card", "data": {...}, "id": "...", "fallback_text": "..."},
        ],  # Optional
    },
)
```

### Token Streaming

```python
# Ephemeral (not persisted)
await publish_agent_token(
    room_id=room_id,
    agent_name="StoryAdvisor",
    token="partial ",  # Delta only
)
```

### Internal A2A Messages

```python
await emit_agent_internal_message(
    session=session,
    room_id=room_id,
    from_agent="StoryAdvisor",
    to_agent="DialogueCoach",
    content="Please review the dialogue...",
    visible_to_users=False,
)
```

---

## Adding New Agent Tools

### 1. Define the Tool

```python
# In agent_runner.py or separate module

async def my_new_tool(
    ctx: RunContext[AgentDeps],
    param1: str,
    param2: int,
) -> str:
    """
    Tool description for the agent.

    Args:
        param1: What this parameter does
        param2: Another parameter

    Returns:
        Description of return value
    """
    # Access deps
    session = ctx.deps.session
    room_id = ctx.deps.room_id

    # Do work...

    return "Result"
```

### 2. Register the Tool

```python
async def get_agent_instance_with_tools(
    session: AsyncSession,
    slug: str,
    enable_a2a_tool: bool = True,
    enable_ag_ui_tool: bool = True,
    enable_my_new_tool: bool = True,  # Add parameter
) -> Agent[AgentDeps, str] | None:

    tools: list[Any] = []
    if enable_a2a_tool:
        tools.append(request_agent_assistance)
    if enable_ag_ui_tool:
        tools.append(emit_ui_component)
    if enable_my_new_tool:
        tools.append(my_new_tool)  # Add to list

    agent = Agent(
        model_name,
        system_prompt=system_prompt,
        tools=tools,
        deps_type=AgentDeps,
    )
```

---

## Creating System Agents

### Bootstrap Pattern

```python
# In agent_registry_service.py

async def bootstrap_system_agents(session: AsyncSession) -> None:
    """Ensure system agents exist."""

    system_agents = [
        AgentConfigCreate(
            name="StoryAdvisor",
            slug="StoryAdvisor",
            description="Expert in story structure and narrative pacing",
            model_name="openai:gpt-4o-mini",
            system_prompt="You are StoryAdvisor, an expert in...",
            scope="system",
            participation_mode="on_mention",
            capabilities=["story-structure", "pacing", "narrative"],
        ),
        # ... more agents
    ]

    for agent_data in system_agents:
        existing = await get_agent_config(session, agent_data.slug)
        if not existing:
            await create_agent_config(session, agent_data, owner_id=None)
```

---

## Testing Agents

### Unit Test Pattern

```python
import pytest
from app.services.agent_runner import (
    detect_mentions,
    is_agent_mentioned,
    should_agent_respond_to_message,
)

def test_mention_detection():
    mentions = detect_mentions("Hey @StoryAdvisor and @DialogueCoach")
    assert "storyadvisor" in mentions
    assert "dialoguecoach" in mentions

def test_quoted_mentions():
    mentions = detect_mentions('Ask @"Story Advisor" for help')
    assert "story advisor" in mentions

def test_participation_mode_always():
    config = AgentConfig(participation_mode="always", ...)
    should, reason = should_agent_respond_to_message(config, "any message")
    assert should is True
```

### Integration Test Pattern

```python
@pytest.mark.asyncio
async def test_agent_responds_when_mentioned(session, room_with_agent):
    responses = await run_agents_for_message(
        room_id=room_with_agent.id,
        trigger_message="@StoryAdvisor help me",
        session=session,
    )

    assert len(responses) == 1
    assert responses[0]["agent_name"] == "StoryAdvisor"
    assert responses[0]["success"] is True
```

---

## Configuration Constants

```python
# agent_runner.py
MAX_A2A_DEPTH = 2  # Maximum agent chain depth

# Participation modes
PARTICIPATION_ALWAYS = "always"
PARTICIPATION_ON_MENTION = "on_mention"
PARTICIPATION_MANUAL = "manual"

# Default model
DEFAULT_MODEL = "openai:gpt-4o-mini"
```

---

## File Reference

| File | Purpose |
|------|---------|
| `models.py` | AgentConfig*, RoomParticipant, UserAgentSettings |
| `crud.py` | Database operations for agents |
| `api/routes/agent_routes.py` | REST endpoints |
| `services/agent_runner.py` | Execution, A2A, AG-UI, streaming |
| `services/agent_registry_service.py` | Caching, instantiation, bootstrap |
| `services/context_provider.py` | Room context building |
| `services/event_emitter.py` | Event emission, internal messages |
| `schemas/ag_ui.py` | UI component Pydantic models |
| `agents/tool_registry.py` | Tool registration (legacy) |

---

## Migration Checklist

When adding agent features:

1. [ ] Add field to `AgentConfigBase` in `models.py`
2. [ ] Add optional version to `AgentConfigUpdate`
3. [ ] human users create migration (has to happen in different system): `alembic revision --autogenerate -m "Add field"`
4. [ ] human engineers apply migration (happens in different system): `alembic upgrade head`
5. [ ] Update API if needed in `agent_routes.py`
6. [ ] Update `agent_runner.py` for execution changes
7. [ ] Add tests
8. [ ] Update this reference
