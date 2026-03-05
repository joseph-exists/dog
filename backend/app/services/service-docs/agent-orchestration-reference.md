# Agent Orchestration Reference

> Complete reference for the agent orchestration system, covering all patterns, configurations, and demo capabilities.

## Related Documentation

| Document | Scope | Location |
|----------|-------|----------|
| **Agent Demo Quick-Start** | Ready-to-use demo configurations | `service-docs/agent-demo-quickstart.md` |
| **Agent Registry Skill** | CRUD, models, caching, API endpoints | `.claude/skills/agent-registry/SKILL.md` |
| **Agent Developer Reference** | Implementation details, code patterns | `.claude/skills/agent-registry/references/agent-developer-reference.md` |
| **A2A & AG-UI Roadmap** | Feature phases, completion status | `.claude/skills/agent-registry/references/a2a-ag-ui-roadmap.md` |
| **A2A & AG-UI Reference Card** | GTM/Product owner summary | `.claude/skills/agent-registry/references/a2a-ag-ui-reference-card.md` |
| **Agent Provider Integration** | LLM provider configuration | `.claude/skills/agent-registry/references/agent-provider-integration.md` |
| **Agent User Guide** | End-user documentation | `.claude/skills/agent-registry/references/agent-user-guide.md` |

**This document focuses on runtime orchestration patterns and demo capabilities.** For agent CRUD operations, model definitions, and API endpoints, see the Agent Registry Skill.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Orchestration Patterns](#orchestration-patterns)
3. [Configuration Reference](#configuration-reference)
4. [Tools & Capabilities](#tools--capabilities)
5. [Event System](#event-system)
6. [Context System](#context-system)
7. [Demo Capability Matrix](#demo-capability-matrix)
8. [API Reference](#api-reference)
9. [Implementation Examples](#implementation-examples)

---

## Architecture Overview

### High-Level Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ENTRY POINTS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│  POST /rooms/{id}/messages    │  POST /rooms/{id}/ui-action                 │
│  WebSocket message            │  (invoke_agent_manually)                    │
│  (run_agents_for_message)     │                                             │
└──────────────┬────────────────┴─────────────────┬───────────────────────────┘
               │                                   │
               ▼                                   │
┌──────────────────────────────┐                   │
│   AgentSelectionService      │                   │
│   ├─ resolve_participants()  │                   │
│   ├─ select_agents_for_msg() │◄──────────────────┘
│   └─ should_agent_respond()  │
└──────────────┬───────────────┘
               │ Returns: (coordinators[], regular_agents[])
               ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                         TWO-PHASE EXECUTION                                   │
│  ┌─────────────────────────────┐    ┌──────────────────────────────────────┐ │
│  │ Phase 1: COORDINATORS       │ →  │ Phase 2: REGULAR AGENTS              │ │
│  │ • Run FIRST, always         │    │ • Respect participation_mode         │ │
│  │ • Can @mention specialists  │    │ • always | on_mention | manual       │ │
│  │ • Intent routing/dispatch   │    │ • Sequential execution               │ │
│  └────────────┬────────────────┘    └──────────────────┬───────────────────┘ │
└───────────────┼─────────────────────────────────────────┼────────────────────┘
                │                                         │
                ▼                                         ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                      StreamingAgentRunner.run()                               │
│  1. Build room context    (RoomContextService)                               │
│  2. Instantiate agent     (get_agent_instance_with_tools)                    │
│  3. Execute with tools    (PydanticAI Agent.run_stream)                      │
│  4. Stream tokens         (Redis pub/sub → WebSocket)                        │
│  5. Process @mentions     (A2AOrchestrator)                                  │
│  6. Emit final event      (room_message.agent)                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Service Composition

| Service | File | Responsibility |
|---------|------|----------------|
| **agent_runner.py** | `services/agent_runner.py` | Entry points & high-level orchestration |
| **AgentSelectionService** | `services/agent_selection.py` | Participant resolution, participation mode logic |
| **StreamingAgentRunner** | `services/agent_runner_streaming.py` | Core execution with token streaming |
| **NonStreamingAgentRunner** | `services/agent_runner_non_streaming.py` | Simplified execution (no streaming) |
| **A2AOrchestrator** | `services/a2a_orchestrator.py` | @mention detection & agent-to-agent triggers |
| **agent_instance.py** | `services/agent_instance.py` | PydanticAI Agent construction |
| **agent_tools.py** | `services/agent_tools.py` | Tool definitions (A2A, AG-UI) |
| **AgentEventPublisher** | `services/agent_events.py` | Token & message event emission |
| **RoomContextService** | `services/agent_context.py` | Context building wrapper |
| **context_provider.py** | `services/context_provider.py` | Full context construction |

---

## Orchestration Patterns

### Pattern 1: Coordinator Routing

**Use Case**: Single "router" agent analyzes user intent and delegates to specialist agents.

**How It Works**:
1. Coordinator agent runs FIRST (bypasses participation mode)
2. Coordinator analyzes message and @mentions appropriate specialists
3. A2AOrchestrator detects mentions and triggers specialists sequentially
4. Each specialist responds in the room

**Configuration**:
```python
# Set on UserAgentConfig
is_coordinator: bool = True
participation_mode: str = "always"  # Coordinators typically always active
```

**Flow**:
```
User: "Help me with character dialogue"
           │
           ▼
┌──────────────────────────┐
│  Coordinator Agent       │  ← is_coordinator=True, runs first
│  "I'll get DialogueBot   │
│   to help. @DialogueBot" │
└────────────┬─────────────┘
             │ @mention detected
             ▼
┌──────────────────────────┐
│  DialogueBot (specialist)│  ← participation_mode="on_mention"
│  "Here's how to write... │
└──────────────────────────┘
```

**Best For**:
- Intent classification
- Multi-specialist routing
- User request triage
- Complex task decomposition

---

### Pattern 2: Tool-Based A2A (Synchronous)

**Use Case**: Agent needs to wait for another agent's response before continuing.

**How It Works**:
1. Agent A is executing and needs Agent B's expertise
2. Agent A calls `request_agent_assistance(target_agent, request)`
3. Agent B executes (non-streaming, no events emitted)
4. Agent B's response returns inline to Agent A
5. Agent A incorporates response and continues

**Tool Definition** (`agent_tools.py:60-111`):
```python
async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,  # Agent slug or name
    request: str,       # What you need help with
) -> str:              # Returns Agent B's response text
```

**Configuration**:
```python
# Enable when calling run_agent_for_room_streaming
enable_a2a_tool: bool = True
```

**Depth Limiting**:
```python
DEFAULT_MAX_A2A_DEPTH = 2  # Prevents infinite chains
# Depth 0: User-triggered
# Depth 1: First A2A call
# Depth 2: Second A2A call (max)
```

**Flow**:
```
User: "Analyze this character"
           │
           ▼
┌──────────────────────────────────────────┐
│  Analyst Agent (enable_a2a_tool=True)    │
│  "Let me consult the psychology expert"  │
│  → request_agent_assistance(             │
│      "PsychExpert",                      │
│      "What motivates this character?"    │
│    )                                     │
└────────────────┬─────────────────────────┘
                 │ Synchronous call (no events)
                 ▼
┌──────────────────────────────────────────┐
│  PsychExpert Agent                       │
│  Returns: "This character is driven by..."│
└────────────────┬─────────────────────────┘
                 │ Response flows back
                 ▼
┌──────────────────────────────────────────┐
│  Analyst Agent (continues)               │
│  "Based on the expert analysis..."       │
│  [Final response emitted to room]        │
└──────────────────────────────────────────┘
```

**Best For**:
- Expert consultation workflows
- Synthesis requiring multiple perspectives
- Sequential reasoning chains

---

### Pattern 3: @Mention-Based A2A (Reactive)

**Use Case**: Loose coupling where agents naturally reference each other.

**How It Works**:
1. Agent A completes its response
2. A2AOrchestrator scans response for @mentions
3. Mentioned agents are triggered with Agent A's response as context
4. Mentioned agents respond in the room

**Mention Detection** (`a2a_orchestrator.py:24-35`):
```python
# Supports two formats:
@AgentSlug       # Simple: @DialogueBot
@"Agent Name"    # Quoted: @"Dialogue Expert"
```

**Flow**:
```
User: "Review my story structure"
           │
           ▼
┌──────────────────────────────────────────┐
│  StructureAdvisor Agent                  │
│  "Your plot is solid. For pacing,        │
│   @PacingBot can give specifics."        │
└────────────────┬─────────────────────────┘
                 │ Response complete, @mention detected
                 ▼
┌──────────────────────────────────────────┐
│  PacingBot Agent                         │
│  Receives: "@StructureAdvisor said:..."  │
│  Responds: "For Act 2 pacing..."         │
└──────────────────────────────────────────┘
```

**Best For**:
- Natural agent collaboration
- Optional/suggested expertise
- Agents recommending other agents

---

### Pattern 4: Manual Invocation

**Use Case**: Direct agent invocation via UI action buttons or API.

**How It Works**:
1. User clicks an action button in agent's response
2. `POST /rooms/{id}/ui-action` called
3. `invoke_agent_manually()` runs agent directly
4. Participation mode is bypassed

**Entry Point** (`agent_runner.py:482-597`):
```python
async def invoke_agent_manually(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,    # Often "[UI Action: action_string]"
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
) -> dict[str, Any]:
```

**Best For**:
- Action button responses
- Admin/testing invocations
- "Manual" mode agents
- Workflow step triggers

---

### Pattern 5: Participation-Based Auto-Response

**Use Case**: Agents that respond based on room rules.

**Participation Modes** (`UserAgentConfig.participation_mode`):

| Mode | Behavior | Use Case |
|------|----------|----------|
| `always` | Responds to every message | Primary assistant, moderator |
| `on_mention` | Responds only when @mentioned | Specialist, on-demand expert |
| `manual` | Never auto-responds | Background processor, admin-only |

**Selection Logic** (`agent_selection.py:115-135`):
```python
def should_agent_respond_to_message(
    self,
    *,
    config: UserAgentConfig,
    trigger_message: str,
) -> tuple[bool, str]:
    mode = config.participation_mode or "on_mention"

    if mode == "always":
        return True, "mode=always"

    if mode == "manual":
        return False, "mode=manual (requires explicit invocation)"

    if mode == "on_mention":
        if _is_agent_mentioned(trigger_message, config.slug, config.name):
            return True, "mentioned in message"
        return False, "not mentioned (mode=on_mention)"
```

---

## Configuration Reference

### UserAgentConfig Fields

**Core Identity**:
```python
name: str           # Display name (e.g., "Story Advisor")
slug: str           # Unique identifier (e.g., "story-advisor")
description: str    # What the agent does
```

**Model Configuration**:
```python
model_name: str               # Model identifier (e.g., "gpt-4o-mini")
provider_type: uuid.UUID      # FK to LLMProviderType
user_access_provider: uuid.UUID  # FK to UserAccessProvider (API keys)
```

**Prompt Configuration**:
```python
system_prompt: str            # Base system prompt
custom_system_prompt: str     # User override
instructions: str             # Extended instructions field
prompt_config_id: uuid.UUID   # FK to PromptConfig (versioned prompts)
prompt_config_version_policy: "latest" | "pinned"
prompt_config_version_number: int | None
```

**Behavior Flags**:
```python
is_enabled: bool = True           # Agent can be used
is_coordinator: bool = False      # Runs before regular agents
participation_mode: str = "on_mention"  # "always" | "on_mention" | "manual"
max_tool_iterations: int = 10     # Prevent runaway tool loops
```

**Discovery & Coordination**:
```python
capabilities: list[str] = []      # e.g., ["dialogue", "plot-structure"]
scope: str = "personal"           # "personal" | "system"
```

**Extended Configuration (JSON)**:
```python
tool_config: dict | None          # Tool-specific settings
deps_config: dict | None          # Dependency injection config
agent_metadata: dict | None       # Arbitrary metadata
presentation: dict | None         # UI presentation hints
```

---

## Tools & Capabilities

### Built-in Tools

#### 1. `request_agent_assistance` (A2A Tool)

**Purpose**: Synchronously request help from another agent.

**Signature**:
```python
async def request_agent_assistance(
    ctx: RunContext[AgentDeps],
    target_agent: str,  # Agent slug or display name
    request: str,       # What you need help with
) -> str:              # Target agent's response
```

**Behavior**:
- Checks if target agent is in the room
- Respects depth limit (prevents infinite recursion)
- Runs target agent non-streaming (no room events)
- Returns response directly to calling agent

**Error Responses**:
```python
# Depth limit reached
"[A2A limit reached] Cannot request assistance from {target} - maximum agent chain depth (2) exceeded."

# Self-reference
"[Error] Cannot request assistance from yourself."

# Agent not in room
"[Agent not found] '{target}' is not available in this room."
```

---

#### 2. `emit_ui_component` (AG-UI Tool)

**Purpose**: Emit structured UI components with agent response.

**Signature**:
```python
def emit_ui_component(
    ctx: RunContext[AgentDeps],
    component_type: UIComponentType,
    data: dict[str, Any],
    fallback_text: str | None = None,
) -> str:
```

**Component Types**:

| Type | Fields | Use Case |
|------|--------|----------|
| `card` | title, body, subtitle, footer, variant, icon | Highlighted info |
| `list` | items[], title, ordered, variant | Enumerated items |
| `table` | columns[], rows[], title, striped, compact | Structured data |
| `progress` | items[], title, show_percentage | Completion metrics |
| `action_buttons` | buttons[], layout | User actions |
| `code` | code, language, title, line_numbers | Code snippets |
| `quote` | text, attribution, variant | Highlighted quotes |
| `alert` | message, title, variant, dismissible | Notifications |
| `collapsible` | title, content, default_open | Expandable content |
| `tabs` | tabs[], default_tab | Categorized content |
| `divider` | label, variant | Visual separator |
| `page_layout_preview` | entity_type, entity_id, layout_json | Layout proposals |

**Example - Action Buttons**:
```python
emit_ui_component(
    ctx,
    component_type="action_buttons",
    data={
        "buttons": [
            {"label": "Expand Details", "action": "expand_character"},
            {"label": "Generate More", "action": "regenerate"},
        ],
        "layout": "horizontal"
    },
    fallback_text="Choose an action above."
)
```

**Validation**:
- Data is validated against Pydantic schemas
- Invalid data returns error message to agent for retry
- Validated/normalized data stored with response

---

### AgentDeps (Tool Context)

**Structure** (`agent_tools.py:23-57`):
```python
@dataclass
class AgentDeps:
    session: AsyncSession        # Database access
    room_id: uuid.UUID          # Current room
    current_agent_slug: str     # Self-identification
    a2a_depth: int = 0          # Current A2A chain depth
    ui_components: list[UIComponent] | None = None  # Collected UI
```

**Usage in Tools**:
```python
async def my_custom_tool(ctx: RunContext[AgentDeps], arg: str) -> str:
    deps = ctx.deps
    # Access database
    result = await deps.session.exec(...)
    # Know which room we're in
    room_id = deps.room_id
    # Know our identity
    agent = deps.current_agent_slug
    # Check A2A depth
    if deps.a2a_depth >= 2:
        return "Cannot delegate further"
```

---

## Event System

### Event Flow

```
Agent Response
      │
      ├──► Token Streaming (ephemeral)
      │    └── Redis pub/sub → WebSocket clients
      │        Event: message.delta
      │        NOT persisted to Postgres
      │
      └──► Final Message (persistent)
           └── emit_event() → RoomEvent + RoomMessage
               Event: room_message.agent
               Persisted to Postgres
               Published to Redis
```

### Event Types

| Event Type | Source | Persistent | Description |
|------------|--------|------------|-------------|
| `room_message.user` | User input | Yes | User sends message |
| `room_message.agent` | Agent response | Yes | Agent completes response |
| `message.delta` | Token streaming | No | Individual tokens (ephemeral) |

### Event Emission

**AgentEventPublisher** (`agent_events.py`):
```python
class AgentEventPublisher:
    async def publish_token(
        self,
        *,
        room_id: uuid.UUID,
        agent_name: str,
        token: str,
    ) -> None:
        # Ephemeral - Redis only, no DB

    async def emit_message(
        self,
        *,
        session: AsyncSession,
        room_id: uuid.UUID,
        agent_name: str,
        content: str,
        ui_components: list[dict[str, Any]] | None = None,
    ) -> None:
        # Persistent - emit_event() to DB + Redis
```

---

## Context System

### RoomContext Structure

```python
@dataclass
class RoomContext:
    room_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict[str, Any] | None        # Title, description
    story_runtime: StoryRuntimeContext | None # Live story state
    recent_messages: list[dict[str, Any]]    # Last N messages
    participants: list[dict[str, Any]]       # Users & agents
    room_metadata: dict[str, Any]            # Room title, creator
    active_agents: list[AgentInfo]           # Agent details for A2A
    extra_contexts: list[dict[str, Any]]     # Additional context items
```

### AgentInfo (Agent Discovery)

```python
@dataclass
class AgentInfo:
    slug: str                    # Unique identifier
    name: str                    # Display name
    description: str             # What the agent does
    participation_mode: str      # How it responds
    capabilities: list[str]      # What it's good at
```

**Use Case**: Agents can see other agents in the room and decide whom to @mention or request assistance from.

### StoryRuntimeContext (Story State)

```python
@dataclass
class StoryRuntimeContext:
    current_node_title: str      # Where user is
    current_node_content: str    # Full node text
    current_node_type: str | None
    is_end_node: bool
    node_chain: list[str]        # Path taken (root → current)
    available_choices: list[str] # Next options
    story_state: dict[str, Any]  # Accumulated state
```

---

## Demo Capability Matrix

### Currently Expressible Patterns

| Demo Concept | Pattern | Configuration Required | Status |
|--------------|---------|----------------------|--------|
| **Router + Specialists** | Coordinator Pattern | `is_coordinator=True` on router | ✅ Ready |
| **Expert Consultation** | Tool-Based A2A | `enable_a2a_tool=True` | ✅ Ready |
| **Collaborative Discussion** | @Mention A2A | Multiple agents in room | ✅ Ready |
| **Action Buttons** | AG-UI + Manual Invoke | `enable_ag_ui_tool=True` | ✅ Ready |
| **Progressive Disclosure** | AG-UI Collapsibles | `emit_ui_component(collapsible)` | ✅ Ready |
| **Multi-Tab Analysis** | AG-UI Tabs | `emit_ui_component(tabs)` | ✅ Ready |
| **Streaming Responses** | Default behavior | Token streaming enabled | ✅ Ready |
| **Story-Aware Agents** | Context System | Room linked to Story | ✅ Ready |
| **Capability Discovery** | AgentInfo | `capabilities` field populated | ✅ Ready |
| **Depth-Limited Chains** | A2A Depth Control | `DEFAULT_MAX_A2A_DEPTH` | ✅ Ready |

### Demo Ideas by Complexity

#### Tier 1: Single Agent
- **Basic Chat**: Agent with `participation_mode="always"`
- **Action Buttons**: Agent emits buttons, user clicks, agent responds
- **Rich UI Response**: Agent uses cards, tables, progress bars

#### Tier 2: Multi-Agent (No Orchestration)
- **Parallel Experts**: Multiple `on_mention` agents, user @mentions them
- **Always-On Moderator**: One `always` agent, others `on_mention`

#### Tier 3: Orchestrated Multi-Agent
- **Intent Router**: Coordinator routes to specialists via @mentions
- **Expert Panel**: Agent consults multiple experts via `request_agent_assistance`
- **Debate Format**: Agent A mentions Agent B, B responds and mentions A (depth-limited)

#### Tier 4: Full System Integration
- **Story Advisor Team**: Multiple agents with story context, coordinator routing
- **Interactive Workflow**: Agents emit action buttons that trigger other agents
- **Progressive Analysis**: Agent 1 analyzes, emits buttons, Agent 2 elaborates on click

---

## API Reference

### Entry Points

#### `run_agents_for_message()`
**File**: `agent_runner.py:340-479`

**Purpose**: Main entry point for user messages.

```python
async def run_agents_for_message(
    *,
    room_id: uuid.UUID,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
) -> list[dict[str, Any]]:
```

**Execution Order**:
1. Resolve all agent participants in room
2. Split into coordinators and regular agents
3. Run coordinators first (always)
4. Run regular agents based on participation mode
5. Return list of all responses

---

#### `invoke_agent_manually()`
**File**: `agent_runner.py:482-597`

**Purpose**: Direct agent invocation (bypasses participation mode).

```python
async def invoke_agent_manually(
    *,
    room_id: uuid.UUID,
    agent_slug: str,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
) -> dict[str, Any]:
```

---

#### `run_agent_for_room_streaming()`
**File**: `agent_runner.py:261-333`

**Purpose**: Execute single agent with streaming.

```python
async def run_agent_for_room_streaming(
    *,
    room_id: uuid.UUID,
    agent_name: str,
    trigger_message: str,
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    a2a_depth: int = 0,
    enable_a2a_tool: bool = False,
    enable_ag_ui_tool: bool = False,
) -> dict[str, Any]:
```

---

### Data Types

#### AgentRunRequest
```python
@dataclass(frozen=True)
class AgentRunRequest:
    room_id: uuid.UUID
    agent_slug: str
    trigger_message: str
    user_id: uuid.UUID | None = None
    a2a_depth: int = 0
    enable_a2a_tool: bool = False
    enable_ag_ui_tool: bool = False
```

#### AgentRunResult
```python
@dataclass(frozen=True)
class AgentRunResult:
    agent_name: str
    content: str
    success: bool
    error: str | None = None
    a2a_triggered: list[str] | None = None
    ui_components: list[dict[str, Any]] | None = None
```

---

## Implementation Examples

### Example 1: Coordinator + Specialists

**Setup**:
```python
# Coordinator Agent
UserAgentConfig(
    name="Story Director",
    slug="story-director",
    is_coordinator=True,
    participation_mode="always",
    system_prompt="""
    You are the Story Director. Analyze user requests and delegate to specialists:
    - @DialogueExpert for dialogue issues
    - @PlotAdvisor for plot/structure
    - @CharacterCoach for character development

    Always explain what you're delegating and why.
    """,
    capabilities=["routing", "orchestration"],
)

# Specialist Agents
UserAgentConfig(
    name="Dialogue Expert",
    slug="dialogue-expert",
    is_coordinator=False,
    participation_mode="on_mention",
    system_prompt="You specialize in dialogue...",
    capabilities=["dialogue", "voice", "subtext"],
)
```

**Flow**:
```
User: "My characters sound the same"
      │
      ▼
Story Director (coordinator, runs first):
  "This is a dialogue issue. @DialogueExpert can help
   you develop distinct voices for each character."
      │
      ▼ (A2AOrchestrator detects @mention)
      │
Dialogue Expert (triggered):
  "Let's work on vocal signatures for your characters.
   Consider these techniques..."
```

---

### Example 2: Tool-Based Expert Consultation

**Setup**:
```python
UserAgentConfig(
    name="Story Analyst",
    slug="story-analyst",
    is_coordinator=False,
    participation_mode="always",
    system_prompt="""
    You analyze stories comprehensively. When you need specialized input,
    use request_agent_assistance() to consult:
    - "theme-expert" for thematic analysis
    - "structure-expert" for structural analysis

    Synthesize their insights into your response.
    """,
)

# Call with tools enabled
await run_agent_for_room_streaming(
    room_id=room_id,
    agent_name="story-analyst",
    trigger_message=user_message,
    session=session,
    enable_a2a_tool=True,  # Enable A2A tool
)
```

**Agent Behavior**:
```python
# Inside agent's execution
theme_analysis = await request_agent_assistance(
    ctx,
    target_agent="theme-expert",
    request="What are the major themes in this story outline?",
)

structure_analysis = await request_agent_assistance(
    ctx,
    target_agent="structure-expert",
    request="Analyze the three-act structure of this story.",
)

# Agent synthesizes both analyses in final response
```

---

### Example 3: Interactive UI with Action Buttons

**Setup**:
```python
UserAgentConfig(
    name="Character Designer",
    slug="character-designer",
    participation_mode="always",
    system_prompt="""
    Help users design characters. After providing initial analysis,
    offer action buttons for deeper exploration.

    Use emit_ui_component with action_buttons to offer:
    - "expand_backstory" - Generate detailed backstory
    - "explore_relationships" - Map character relationships
    - "voice_samples" - Create dialogue samples
    """,
)

# Call with UI tools enabled
await run_agent_for_room_streaming(
    room_id=room_id,
    agent_name="character-designer",
    trigger_message=user_message,
    session=session,
    enable_ag_ui_tool=True,  # Enable UI components
)
```

**Agent Response**:
```python
# Agent's tool call
emit_ui_component(
    ctx,
    component_type="card",
    data={
        "title": "Character Analysis: Elena",
        "subtitle": "Protagonist",
        "body": "A determined scientist driven by...",
        "variant": "highlight",
    },
)

emit_ui_component(
    ctx,
    component_type="action_buttons",
    data={
        "buttons": [
            {"label": "Expand Backstory", "action": "expand_backstory"},
            {"label": "Explore Relationships", "action": "explore_relationships"},
            {"label": "Voice Samples", "action": "voice_samples"},
        ],
        "layout": "horizontal",
    },
)
```

**When User Clicks Button**:
```
POST /rooms/{room_id}/ui-action
{
  "action": "expand_backstory",
  "message_id": "uuid-of-message"
}
      │
      ▼
invoke_agent_manually() with trigger:
  "[UI Action: expand_backstory]
   Please expand on Elena's backstory."
```

---

### Example 4: Multi-Expert Panel

**Scenario**: User wants comprehensive story feedback from multiple perspectives.

**Setup**:
```python
# Panel Moderator (Coordinator)
UserAgentConfig(
    name="Panel Moderator",
    slug="panel-moderator",
    is_coordinator=True,
    participation_mode="always",
    system_prompt="""
    You moderate a panel of story experts. When users request feedback:
    1. Introduce the panel
    2. @mention relevant experts based on the question
    3. Summarize after all experts respond

    Experts available:
    - @PlotExpert - Story structure
    - @CharacterExpert - Character development
    - @DialogueExpert - Dialogue quality
    - @PacingExpert - Narrative pacing
    """,
)

# All experts: is_coordinator=False, participation_mode="on_mention"
```

**Flow**:
```
User: "Give me feedback on my opening chapter"
      │
      ▼
Panel Moderator:
  "I'll assemble the panel for comprehensive feedback.

   @PlotExpert, please analyze the story hooks.
   @CharacterExpert, evaluate character introductions.
   @PacingExpert, assess the chapter's rhythm."
      │
      ▼ (Each expert triggered sequentially)
      │
PlotExpert: "The opening hook is..."
CharacterExpert: "Your protagonist introduction..."
PacingExpert: "The pacing in the first section..."
```

---

## Constraints & Limitations

### Current Limitations

1. **Sequential Execution**: Agents run one at a time (no parallel execution)
2. **Synchronous A2A**: `request_agent_assistance` waits for full response
3. **Depth Limit**: A2A chains limited to 2 levels by default
4. **Single Room Scope**: Agents can only see/interact within their room
5. **No State Persistence**: Agents don't remember across sessions (context rebuilt each time)

### Future Extension Points

| Extension | Current State | Location |
|-----------|--------------|----------|
| Parallel agent execution | Not implemented | `run_agents_for_message()` loop |
| Streaming A2A | Non-streaming only | `_run_agent_for_tool_call()` |
| Cross-room agents | Room-scoped only | `AgentDeps.room_id` |
| Agent memory | Context rebuilt per request | `RoomContextService.build()` |
| Custom tool registration | Hardcoded tools | `get_agent_instance_with_tools()` |

---

## Quick Reference

### Enable Features

```python
# Enable A2A tool
enable_a2a_tool=True

# Enable UI components
enable_ag_ui_tool=True

# Make agent a coordinator
UserAgentConfig.is_coordinator = True

# Set participation mode
UserAgentConfig.participation_mode = "always" | "on_mention" | "manual"

# Set capabilities for discovery
UserAgentConfig.capabilities = ["dialogue", "plot", "characters"]
```

### Key Files

```
backend/app/services/
├── agent_runner.py              # Entry points & high-level orchestration
├── agent_runner_streaming.py    # Core streaming execution
├── agent_runner_non_streaming.py
├── agent_runner_types.py        # Request/Result types
├── agent_selection.py           # Participation logic
├── a2a_orchestrator.py          # @mention detection
├── agent_instance.py            # PydanticAI Agent construction (runtime)
├── agent_registry_service.py    # Config caching & instantiation (CRUD layer)
├── agent_tools.py               # A2A & AG-UI tools
├── agent_events.py              # Event publishing
├── agent_context.py             # Context wrapper
├── context_provider.py          # Full context building
└── event_emitter.py             # Core event emission

backend/app/schemas/
└── ag_ui.py                     # UI component schemas

backend/app/models.py
└── UserAgentConfig*             # Agent configuration models (lines 3685-3920)
    ├── UserAgentConfigBase      # Shared properties
    ├── UserAgentConfigCreate    # API input
    ├── UserAgentConfigUpdate    # Partial updates
    ├── UserAgentConfig          # Database table (table=True)
    ├── UserAgentConfigPublic    # API response
    └── UserAgentConfigsPublic   # Collection response

backend/app/api/routes/
├── agent_routes.py              # Agent CRUD endpoints
└── rooms.py                     # Room message & UI action endpoints
```

---

## Integration Notes

### Agent Instantiation Pathways

There are **two pathways** for instantiating agents at runtime:

1. **Direct Instantiation** (`agent_instance.py`):
   - Used by `StreamingAgentRunner` and `NonStreamingAgentRunner`
   - `get_agent_instance_with_tools()` builds PydanticAI Agent directly from `UserAgentConfig`
   - Handles credential resolution via `UserAccessProvider`

2. **Registry Service** (`agent_registry_service.py`):
   - Provides caching layer (`_config_cache`, `_runtime_agents`)
   - Used for CRUD operations and admin workflows
   - Fallback pattern during migration from legacy registry

**Current State**: The orchestration layer primarily uses pathway 1 (`agent_instance.py`). The registry service is available for scenarios requiring caching or batch operations.

### Model Naming

The codebase uses `UserAgentConfig` (not `AgentConfig`) for the agent configuration models. This reflects that agents are user-owned resources with tiered access (personal/system scope).

### LLM Provider Resolution

When instantiating agents, credentials are resolved in this order:
1. User's explicit `user_access_provider` on the agent config
2. User's default provider for that type
3. System environment variables

See [Agent Provider Integration](/.claude/skills/agent-registry/references/agent-provider-integration.md) for details.
