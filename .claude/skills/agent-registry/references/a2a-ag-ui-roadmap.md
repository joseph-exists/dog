# A2A & AG-UI Roadmap

**Status:** ✅ All Phases Complete
**Last Updated:** January 2026

## Overview

This document outlines the path from current agent functionality toward:
- **A2A (Agent-to-Agent):** Agents communicating and coordinating with each other
- **AG-UI:** Agents emitting structured UI components
- **A2UI:** Direct agent-to-frontend streaming

---

## Current State (✅ Complete)

| Feature | Status |
|---------|--------|
| Agent database registry | ✅ |
| Agent participation modes (always/on_mention/manual) | ✅ |
| @Mention detection | ✅ |
| User LLM provider selection | ✅ |
| Room context building | ✅ |
| Agent message attribution | ✅ |
| Token streaming via Redis | ✅ |
| Event sourcing for messages | ✅ |
| Party picker UI | ✅ |
| **Phase 1.1** Agent context enhancement (active_agents in RoomContext) | ✅ |
| **Phase 1.2** Agent capability tags | ✅ |
| **Phase 1.3** Agent-aware prompts | ✅ |
| **Phase 2.1** Agent @mention in responses (A2A triggering) | ✅ |
| **Phase 2.2** Internal agent messages (A2A audit trail) | ✅ |
| **Phase 3** Tool-based agent invocation (request_agent_assistance) | ✅ |
| **Phase 4** AG-UI structured UI components (emit_ui_component) | ✅ |
| **Phase 5** Coordinator Pattern (is_coordinator, priority execution) | ✅ |

---

## Phase 1: Agent Coordination Foundation ✅ COMPLETE

**Goal:** Enable basic agent-to-agent awareness

### 1.1 Agent Context Enhancement

Extend `RoomContext` to include agent-specific information:

```python
@dataclass
class RoomContext:
    # Existing fields...
    active_agents: list[AgentInfo]  # NEW: agents in room with capabilities
```

```python
@dataclass
class AgentInfo:
    slug: str
    name: str
    description: str
    participation_mode: str
    capabilities: list[str]  # e.g., ["story", "dialogue", "characters"]
```

**Files:** `context_provider.py`

### 1.2 Agent Capability Tags

Add `capabilities` field to AgentConfig for discovery:

```python
class AgentConfigBase(SQLModel):
    # Existing fields...
    capabilities: list[str] = Field(default_factory=list)
    # e.g., ["story-structure", "dialogue", "plot-twists"]
```

**Files:** `models.py`, migration

### 1.3 Agent-Aware Prompts

Update `build_agent_prompt()` to include other agents:

```
You are StoryAdvisor. Other agents in this room:
- DialogueCoach (@DialogueCoach): Specializes in dialogue refinement
- CharacterForge (@CharacterForge): Character development expert

You can reference other agents with @mentions if their expertise is needed.
```

**Files:** `agent_runner.py`

---

## Phase 2: Agent-to-Agent Communication

**Goal:** Agents can trigger other agents

### 2.1 Agent @Mention in Responses ✅ COMPLETE

When an agent's response contains `@OtherAgent`, trigger that agent:

```python
async def process_agent_response(response: str, room_id: UUID, session: AsyncSession):
    mentions = detect_mentions(response)
    for mentioned_slug in mentions:
        if await is_agent_in_room(session, room_id, mentioned_slug):
            # Queue secondary agent response
            await run_agent_for_room_streaming(
                room_id=room_id,
                agent_name=mentioned_slug,
                trigger_message=response,  # Previous agent's message
                session=session,
            )
```

**Considerations:**
- Recursion limit (max depth of agent chains)
- Cooldown to prevent infinite loops
- User visibility into agent-to-agent exchanges

**Files:** `agent_runner.py`

### 2.2 Internal Agent Messages ✅ COMPLETE

New event type for agent-internal communication:

```python
await emit_event(
    session=session,
    room_id=room_id,
    event_type="room_message.agent_internal",
    payload={
        "from_agent": "StoryAdvisor",
        "to_agent": "DialogueCoach",
        "content": "Please review the dialogue in scene 3",
        "visible_to_users": False,  # Hidden from UI
    },
)

# Or use the convenience helper:
await emit_agent_internal_message(
    session, room_id,
    from_agent="StoryAdvisor",
    to_agent="DialogueCoach",
    content="Please review the dialogue in scene 3",
)
```

**Implementation Details:**
- Event type: `room_message.agent_internal`
- Creates `RoomMessage` with `sender_type="agent_internal"`
- Optional `emit_internal_messages` flag in `process_agent_response()` enables A2A audit trail
- Frontend can filter internal messages: `messages.filter(m => m.sender_type !== "agent_internal")`

**Files:** `event_emitter.py`, `event_types.md`, `agent_runner.py`

---

## Phase 3: Tool-Based Agent Invocation ✅ COMPLETE

**Goal:** Structured agent-to-agent calls via PydanticAI tools

### 3.1 Agent Invocation Tool ✅

`AgentDeps` dataclass provides context to tools:

```python
@dataclass
class AgentDeps:
    session: AsyncSession
    room_id: uuid.UUID
    current_agent_slug: str
    a2a_depth: int = 0
```

The `request_agent_assistance` tool enables structured A2A calls:

```python
async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,
    request: str,
) -> str:
    """Request another agent's expertise on a specific topic."""
    # Checks depth limit, validates target is in room
    # Invokes target agent non-streaming
    # Returns response directly to calling agent
```

### 3.2 Tool Registration ✅

Agents are instantiated with tools via `get_agent_instance_with_tools()`:

```python
agent = await get_agent_instance_with_tools(session, slug, enable_a2a_tool=True)

# Creates:
agent = Agent(
    model_name,
    system_prompt=system_prompt,
    tools=[request_agent_assistance],
    deps_type=AgentDeps,
)
```

**Implementation Details:**
- `AgentDeps` passed via `deps=` parameter on `run_stream()`
- Tool calls are non-streaming (response returned in-turn)
- Target agents don't get tools (prevents infinite recursion)
- Respects `MAX_A2A_DEPTH` limit

**Files:** `agent_runner.py` (primary), `tool_registry.py` (documentation)

---

## Phase 4: AG-UI (Structured UI Responses) ✅ COMPLETE

**Goal:** Agents can emit structured UI components

### 4.1 UI Component Schema ✅

Backend schemas in `app/schemas/ag_ui.py`:

```python
class UIComponent(BaseModel):
    type: UIComponentType  # card, list, table, progress, etc.
    data: dict[str, Any]
    id: str | None = None
    fallback_text: str | None = None

class AgentUIResponse(BaseModel):
    content: str  # Markdown text
    ui_components: list[UIComponent] = []
```

**11 Component Types Implemented:**
- `card` - Highlighted information cards
- `list` - Bulleted/numbered lists
- `table` - Data tables
- `progress` - Progress bars/metrics
- `action_buttons` - Clickable actions
- `code` - Syntax-highlighted code
- `quote` - Blockquotes/dialogue
- `alert` - Info/warning/error notices
- `collapsible` - Expandable sections
- `tabs` - Tabbed content
- `divider` - Visual separators

### 4.2 Agent Tool ✅

Agents use `emit_ui_component` tool during response generation:

```python
def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str:
    """Emit a structured UI component alongside text response."""
    component = UIComponent(type=component_type, data=data, fallback_text=fallback_text)
    ctx.deps.add_ui_component(component)
    return "[UI Component Added]"
```

### 4.3 Event Payload Extension ✅

`room_message.agent` payload now supports optional `ui_components`:

```python
payload = {
    "agent_name": agent_name,
    "content": response_text,
    "ui_components": [c.model_dump() for c in deps.ui_components],  # Optional
}
```

### 4.4 Frontend Rendering ✅

React component in `frontend/src/components/AgentUI/`:

```typescript
import { AgentUIRenderer } from "@/components/AgentUI"

// In message display:
{message.ui_components?.map((component, idx) => (
  <AgentUIRenderer
    key={component.id || idx}
    component={component}
    onAction={(action) => handleAgentAction(action)}
  />
))}
```

**Files:**
- Backend: `app/schemas/ag_ui.py`, `app/services/agent_runner.py`
- Frontend: `src/components/AgentUI/AgentUIRenderer.tsx`, `types.ts`
- Docs: `event-types.md`

---

## Phase 5: Coordinator Pattern (Advanced A2A) ✅ COMPLETE

**Goal:** Orchestrator agent routes to specialists

### 5.1 Coordinator Agent ✅

A special agent that:
1. Receives all user messages first
2. Analyzes intent
3. Routes to appropriate specialist(s)
4. Synthesizes responses

```python
coordinator_prompt = """
You are the room coordinator. When users send messages:
1. Analyze what expertise is needed
2. @mention the appropriate specialist agent(s)
3. Let them respond, then synthesize if needed

Available specialists:
- @StoryAdvisor: Story structure and pacing
- @DialogueCoach: Dialogue and voice
- @CharacterForge: Character development
"""
```

### 5.2 Coordinator Mode ✅

Add `is_coordinator` flag to AgentConfig:

```python
class AgentConfigBase(SQLModel):
    # Existing fields...
    is_coordinator: bool = Field(default=False)
```

Coordinators process messages first, before participation mode checks.

**Implementation Details:**
- `is_coordinator` boolean field added to `AgentConfig` model
- `run_agents_for_message()` in `agent_runner.py` separates coordinators from regular agents
- Coordinators run in Phase 1 (bypass participation mode)
- Regular agents run in Phase 2 (respect participation mode)
- Coordinators can @mention specialists to trigger them
- A2A depth limits still apply to prevent infinite loops

**Files:**
- Model: `app/models.py` (AgentConfigBase.is_coordinator)
- Runner: `app/services/agent_runner.py` (run_agents_for_message)
- Migration: `alembic/versions/d0ecb69789de_add_is_coordinator_field_to_agent_.py`

---

## Implementation Priority

| Phase | Effort | Impact | Priority |
|-------|--------|--------|----------|
| 1.1 Agent Context Enhancement | Low | Medium | P1 |
| 1.2 Agent Capability Tags | Low | Medium | P1 |
| 1.3 Agent-Aware Prompts | Low | High | P1 |
| 2.1 Agent @Mention in Responses | Medium | High | P2 |
| 3.1 Tool-Based Invocation | Medium | High | P2 |
| 4.1-4.3 AG-UI Components | High | High | P3 |
| 5.1-5.2 Coordinator Pattern | Medium | Medium | P4 |

---

## Future Enhancements

All core A2A and AG-UI phases are complete. Potential future work:

1. **Coordinator UI**
   - Frontend toggle for is_coordinator in agent settings
   - Visual indicator for coordinator agents in room

2. **Advanced Orchestration**
   - Multi-coordinator support with priority ordering
   - Coordinator synthesis of specialist responses
   - Conditional routing based on message content analysis

3. **AG-UI Extensions**
   - Additional component types (charts, forms, media)
   - Interactive component state persistence
   - Component theming and customization

4. **A2A Analytics**
   - Dashboard for agent interaction patterns
   - Token usage tracking across A2A chains
   - Performance monitoring for agent latency

---

## Open Questions

1. **Visibility:** Should users see agent-to-agent exchanges, or only final responses?
2. **Control:** Can users disable certain agents from being auto-invoked?
3. **Rate Limiting:** How to prevent agent loops? (Max depth? Cooldown? Token budget?)
4. **Cost:** Who pays for agent-invoked agents? (User's key? System key?)

---

## References

- [Agent Registry Skill](../SKILL.md)
- [Event Sourcing Skill](../../event-sourcing/SKILL.md)
- [Agent Provider Integration](./agent-provider-integration.md)
- PydanticAI Documentation: https://ai.pydantic.dev/
