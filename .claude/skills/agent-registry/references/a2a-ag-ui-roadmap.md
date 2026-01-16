# A2A & AG-UI Roadmap

**Status:** Planning
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

---

## Phase 1: Agent Coordination Foundation

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

### 2.1 Agent @Mention in Responses

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

### 2.2 Internal Agent Messages (Optional)

New event type for agent-internal communication:

```python
await emit_event(
    session=session,
    room_id=room_id,
    event_type="room_message.agent_internal",  # NEW
    payload={
        "from_agent": "StoryAdvisor",
        "to_agent": "DialogueCoach",
        "content": "Please review the dialogue in scene 3",
        "visible_to_users": False,  # Hidden from UI
    },
)
```

**Files:** `event_emitter.py`, `event_types.md`

---

## Phase 3: Tool-Based Agent Invocation

**Goal:** Structured agent-to-agent calls via PydanticAI tools

### 3.1 Agent Invocation Tool

Define a tool that agents can use to invoke other agents:

```python
from pydantic_ai import RunContext

async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,
    request: str,
) -> str:
    """Request another agent's expertise on a specific topic."""
    response = await invoke_agent_manually(
        room_id=ctx.deps.room_id,
        agent_slug=target_agent,
        trigger_message=request,
        session=ctx.deps.session,
    )
    return response["content"]
```

### 3.2 Tool Registration

Register the tool with capable agents:

```python
agent = Agent(
    model_name,
    system_prompt=system_prompt,
    tools=[request_agent_assistance],  # A2A tool
)
```

**Files:** `agent_runner.py`, `tool_registry.py`

---

## Phase 4: AG-UI (Structured UI Responses)

**Goal:** Agents can emit structured UI components

### 4.1 UI Component Schema

Define structured response types:

```python
class AgentUIComponent(BaseModel):
    type: Literal["card", "list", "table", "chart", "action_buttons"]
    data: dict[str, Any]

class AgentResponse(BaseModel):
    content: str  # Markdown text
    ui_components: list[AgentUIComponent] = []
```

### 4.2 Event Payload Extension

Extend `room_message.agent` payload:

```python
payload = {
    "agent_name": agent_name,
    "content": response.content,
    "ui_components": [c.model_dump() for c in response.ui_components],
}
```

### 4.3 Frontend Rendering

Create `AgentUIRenderer` component:

```typescript
function AgentUIRenderer({ components }: { components: AgentUIComponent[] }) {
  return components.map((c) => {
    switch (c.type) {
      case "card": return <AgentCard data={c.data} />
      case "list": return <AgentList data={c.data} />
      case "action_buttons": return <AgentActions data={c.data} />
      // ...
    }
  })
}
```

**Files:** Frontend components, `event_emitter.py`

---

## Phase 5: Coordinator Pattern (Advanced A2A)

**Goal:** Orchestrator agent routes to specialists

### 5.1 Coordinator Agent

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

### 5.2 Coordinator Mode

Add `is_coordinator` flag to AgentConfig:

```python
class AgentConfigBase(SQLModel):
    # Existing fields...
    is_coordinator: bool = Field(default=False)
```

Coordinators process messages first, before participation mode checks.

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

## Quick Wins (Recommended Next Steps)

1. **Phase 1.3 - Agent-Aware Prompts**
   - ~30 lines in `agent_runner.py`
   - Immediate improvement in multi-agent coherence
   - No schema changes required

2. **Phase 1.2 - Capability Tags**
   - Add `capabilities` field to AgentConfig
   - Migration + frontend form update
   - Enables future agent discovery

3. **Phase 2.1 - Agent @Mention Chains**
   - Detect @mentions in agent responses
   - Trigger mentioned agents
   - Add recursion guard

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
