# Proposed Additions to backend/RULES.md
## Agent and Event Sourcing Patterns for TinyFoot

**Status:** DRAFT - To be integrated after Phase 1 completion  
**Date:** December 11, 2025

---

## Agent Development Patterns

### Agent Structure

All agents should follow this structure in the `app/agents/` directory:

```python
# app/agents/example_agent.py
from pydantic_ai import Agent, RunContext
from pydantic import BaseModel
from uuid import UUID

# 1. Define context type with all dependencies
class ExampleContext(BaseModel):
    session_id: UUID
    user_id: UUID
    # Add any other context needed by tools
    story_id: UUID | None = None
    
# 2. Create agent with explicit context type
example_agent = Agent(
    'openai:gpt-4',  # or 'openai:gpt-3.5-turbo' for simpler tasks
    system_prompt="""Your system prompt here.
    Be specific about the agent's role and capabilities.""",
    deps_type=ExampleContext
)

# 3. Define tools that use the context
@example_agent.tool
async def example_tool(ctx: RunContext[ExampleContext], param: str) -> str:
    """Tool description for the LLM to understand when to use this.
    
    Args:
        ctx: Runtime context with session/user info
        param: Parameter description
    
    Returns:
        Result description
    """
    # Access context via ctx.deps
    session_id = ctx.deps.session_id
    
    # Perform tool logic
    result = await do_something(param, session_id)
    
    return result
```

### Agent Tool Best Practices

**DO:**
- Keep tools focused on single responsibilities
- Use async/await for all I/O operations
- Provide clear docstrings (LLM reads these)
- Return JSON-serializable types (str, dict, list)
- Access database via session dependency
- Log tool execution for debugging

**DON'T:**
- Don't make tools do multiple unrelated things
- Don't use blocking operations (time.sleep, requests.get)
- Don't access request-scoped state from tools
- Don't raise exceptions without returning error messages
- Don't return large payloads (>10KB) - summarize instead

### Agent Registration

All production agents must be registered in `app/agents/registry.py`:

```python
# app/agents/registry.py
from app.agents.story_advisor import story_advisor
from app.agents.character_expert import character_expert

AGENT_REGISTRY = {
    "story_advisor": {
        "agent": story_advisor,
        "display_name": "Story Advisor",
        "description": "Helps authors with plot development",
        "context_type": "ChatContext",
        "available_for": ["story_editing"],  # Where agent can be used
    },
    "character_expert": {
        "agent": character_expert,
        "display_name": "Character Expert",
        "description": "Specializes in character development",
        "context_type": "ChatContext",
        "available_for": ["story_editing"],
    },
}
```

### Agent Routes Pattern

Agent routes should follow this pattern in `app/api/routes/agent_routes.py`:

```python
from fastapi import APIRouter, Request
from starlette.responses import Response
from pydantic_ai.ui.ag_ui import AGUIAdapter
from app.agents.registry import AGENT_REGISTRY

router = APIRouter(prefix="/agents", tags=["agents"])

# Endpoint for each registered agent
@router.post('/{agent_name}')
async def run_agent(agent_name: str, request: Request) -> Response:
    """Execute a registered agent via AG-UI protocol"""
    if agent_name not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    
    agent = AGENT_REGISTRY[agent_name]["agent"]
    return await AGUIAdapter.dispatch_request(request, agent=agent)

# Endpoint to list available agents
@router.get('/')
async def list_agents() -> dict:
    """Get list of available agents with their metadata"""
    return {
        "agents": [
            {
                "name": name,
                "display_name": info["display_name"],
                "description": info["description"],
            }
            for name, info in AGENT_REGISTRY.items()
        ]
    }
```

### Testing Agents

Agent tests should be in `app/tests/agents/`:

```python
# app/tests/agents/test_story_advisor.py
import pytest
from app.agents.story_advisor import story_advisor, ChatContext
from uuid import uuid4

@pytest.mark.asyncio
async def test_story_advisor_basic_response():
    """Test agent can respond to basic query"""
    ctx = ChatContext(
        session_id=uuid4(),
        user_id=uuid4(),
        story_id=None
    )
    
    result = await story_advisor.run(
        "How do I create tension?",
        deps=ctx
    )
    
    assert result.data is not None
    assert len(result.data) > 50  # Reasonable response length

@pytest.mark.asyncio
async def test_agent_tool_execution():
    """Test agent can use tools"""
    ctx = ChatContext(
        session_id=uuid4(),
        user_id=uuid4(),
        story_id=uuid4()  # Provide story context
    )
    
    result = await story_advisor.run(
        "Analyze my story's pacing",
        deps=ctx
    )
    
    # Agent should have called the analyze_pacing tool
    assert any(
        call.tool_name == "analyze_pacing" 
        for call in result.all_messages() 
        if hasattr(call, 'tool_name')
    )
```

---

## Event Sourcing Patterns

### Event Structure

All events follow this structure in the `chat_events` table:

```sql
-- Event log is append-only
CREATE TABLE chat_events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    session_sequence BIGINT NOT NULL,  -- Per-session sequence
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (session_id, session_sequence)
);
```

### Event Types

Standard event types for chat system:

| Event Type | When Emitted | Payload Schema |
|------------|--------------|----------------|
| `message.user` | User sends message | `{sender_id, content}` |
| `message.agent` | Agent completes response | `{agent_name, content, model}` |
| `session.created` | New chat session | `{user_id, story_id?, title?}` |
| `agent.handoff` | Agent transfers conversation | `{from_agent, to_agent, reason}` |
| `tool.start` | Tool execution begins | `{tool_name, input}` |
| `tool.end` | Tool execution completes | `{tool_name, output, duration_ms}` |

### Emitting Events

Use the centralized event emitter:

```python
# app/services/event_emitter.py
from uuid import UUID
import json
from sqlmodel import Session
from app.core.db import engine

async def emit_event(
    session_id: UUID,
    event_type: str,
    payload: dict,
    session: Session
) -> int:
    """
    Emit an event to the event log.
    
    Args:
        session_id: Chat session ID
        event_type: Type of event (e.g., 'message.user')
        payload: Event-specific data (JSON-serializable dict)
        session: Database session (for transaction)
    
    Returns:
        session_sequence: The sequence number for this event
    """
    # Generate next sequence number
    result = session.exec(
        text("""
            SELECT COALESCE(MAX(session_sequence), 0) + 1 
            FROM chat_events 
            WHERE session_id = :session_id
        """),
        {"session_id": session_id}
    ).first()
    
    session_sequence = result[0] if result else 1
    
    # Insert event
    session.exec(
        text("""
            INSERT INTO chat_events 
            (session_id, session_sequence, event_type, payload)
            VALUES (:session_id, :sequence, :type, :payload)
        """),
        {
            "session_id": session_id,
            "sequence": session_sequence,
            "type": event_type,
            "payload": json.dumps(payload)
        }
    )
    
    # Update projection in same transaction
    await update_projection(session_id, event_type, payload, session)
    
    return session_sequence
```

### Projection Updates

Projections are materialized views derived from events:

```python
# app/services/event_emitter.py (continued)
async def update_projection(
    session_id: UUID,
    event_type: str,
    payload: dict,
    session: Session
):
    """
    Update projection tables based on event type.
    This runs in the SAME TRANSACTION as the event write.
    """
    if event_type == "message.user":
        # Insert into chat_messages projection
        session.exec(
            text("""
                INSERT INTO chat_messages 
                (session_id, sender_type, sender_id, content, created_at)
                VALUES (:session_id, 'user', :sender_id, :content, NOW())
            """),
            {
                "session_id": session_id,
                "sender_id": payload["sender_id"],
                "content": payload["content"]
            }
        )
        
        # Update session last_activity
        session.exec(
            text("""
                UPDATE chat_sessions 
                SET last_activity = NOW() 
                WHERE session_id = :session_id
            """),
            {"session_id": session_id}
        )
    
    elif event_type == "message.agent":
        # Similar pattern for agent messages
        session.exec(
            text("""
                INSERT INTO chat_messages 
                (session_id, sender_type, agent_name, content, created_at)
                VALUES (:session_id, 'agent', :agent_name, :content, NOW())
            """),
            {
                "session_id": session_id,
                "agent_name": payload["agent_name"],
                "content": payload["content"]
            }
        )
```

### Event Sourcing in Routes

Example of using event sourcing in API routes:

```python
# app/api/routes/chat.py
from app.services.event_emitter import emit_event
from app.services.agent_runner import AgentRunner

@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    message: MessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatMessagePublic:
    """Send a message and get agent response"""
    
    # Start transaction
    with session.begin():
        # 1. Emit user message event
        await emit_event(
            session_id=session_id,
            event_type="message.user",
            payload={
                "sender_id": str(current_user.id),
                "content": message.content
            },
            session=session
        )
        
        # Transaction commits here - events and projections persisted atomically
    
    # 2. Run agent (outside transaction)
    agent_response = await AgentRunner().run_agent(
        session_id=session_id,
        user_message=message.content,
        user_id=current_user.id
    )
    
    # Agent runner will emit message.agent event internally
    
    return ChatMessagePublic(
        sender_type="agent",
        content=agent_response,
        created_at=datetime.now()
    )
```

### Event Immutability Rules

**CRITICAL:** Events are **immutable** once written.

```python
# WRONG - Never do this
session.exec(
    text("UPDATE chat_events SET payload = ... WHERE event_id = ...")
)

# WRONG - Never do this
session.exec(
    text("DELETE FROM chat_events WHERE event_id = ...")
)

# RIGHT - Emit a new event to record the change
await emit_event(
    session_id=session_id,
    event_type="message.deleted",
    payload={
        "deleted_message_id": message_id,
        "deleted_by": user_id,
        "reason": "user_request"
    },
    session=session
)
```

### Event Replay Testing

All projections must be rebuildable from events:

```python
# app/tests/services/test_event_replay.py
@pytest.mark.asyncio
async def test_projection_can_be_rebuilt_from_events():
    """Verify projections can be rebuilt from event log"""
    
    # 1. Create some events via normal flow
    session_id = await create_chat_session(user_id)
    await send_message(session_id, "Hello")
    await send_message(session_id, "World")
    
    # 2. Save current projection state
    messages_before = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    
    # 3. Truncate projection (not events!)
    session.exec(text("TRUNCATE chat_messages"))
    
    # 4. Replay all events
    events = session.exec(
        select(ChatEvent)
        .where(ChatEvent.session_id == session_id)
        .order_by(ChatEvent.session_sequence)
    ).all()
    
    for event in events:
        await update_projection(
            session_id=event.session_id,
            event_type=event.event_type,
            payload=json.loads(event.payload),
            session=session
        )
    
    # 5. Verify projection matches original
    messages_after = session.exec(
        select(ChatMessage).where(ChatMessage.session_id == session_id)
    ).all()
    
    assert len(messages_after) == len(messages_before)
    assert all(
        before.content == after.content
        for before, after in zip(messages_before, messages_after)
    )
```

---

## Context Provider Pattern

### Building Agent Context

Agents need context to provide relevant responses:

```python
# app/services/context_provider.py
from uuid import UUID
from sqlmodel import Session, select
from app.models import Story, StoryNode, ChatMessage, ChatSession

async def build_chat_context(
    session_id: UUID,
    user_id: UUID,
    session: Session
) -> ChatContext:
    """
    Build context for agent execution.
    
    Includes:
    - Recent message history (last 20 messages)
    - Story outline (if session is story-specific)
    - User preferences
    """
    
    # Get session metadata
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise ValueError(f"Session {session_id} not found")
    
    # Get message history
    messages = session.exec(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
    ).all()
    
    message_history = [
        {
            "role": "user" if msg.sender_type == "user" else "assistant",
            "content": msg.content
        }
        for msg in reversed(messages)  # Chronological order
    ]
    
    # Get story context if available
    story_data = None
    if chat_session.story_id:
        story = session.get(Story, chat_session.story_id)
        if story:
            story_data = {
                "title": story.title,
                "description": story.description,
                "node_count": len(story.nodes),
                "outline": format_story_outline(story)
            }
    
    return ChatContext(
        session_id=session_id,
        user_id=user_id,
        story_id=chat_session.story_id,
        story_data=story_data,
        message_history=message_history
    )

def format_story_outline(story: Story) -> str:
    """Format story structure for agent context"""
    outline = f"# {story.title}\n\n{story.description}\n\n## Nodes:\n"
    
    for node in story.nodes[:10]:  # Limit to first 10 nodes
        outline += f"- {node.title}: {node.text[:100]}...\n"
    
    return outline
```

### Context Size Management

**Context Token Limits:**
- GPT-3.5-turbo: 4,096 tokens (~3,000 words)
- GPT-4: 8,192 tokens (~6,000 words)
- GPT-4-32k: 32,768 tokens (~24,000 words)

**Rules:**
- Keep message history to last 20 messages
- Truncate long story outlines
- Summarize instead of including full text
- Monitor token usage via logging

```python
# Estimate tokens (rough approximation)
def estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token"""
    return len(text) // 4

# Check context size before agent run
total_tokens = sum(estimate_tokens(msg["content"]) for msg in message_history)
if total_tokens > 3000:
    # Truncate older messages
    message_history = message_history[-10:]  # Keep only last 10
```

---

## Agent Runner Service

### Service Structure

```python
# app/services/agent_runner.py
from uuid import UUID
from sqlmodel import Session
from app.agents.registry import AGENT_REGISTRY
from app.services.context_provider import build_chat_context
from app.services.event_emitter import emit_event

class AgentRunner:
    """Executes agents with proper context and event emission"""
    
    async def run_agent(
        self,
        session_id: UUID,
        user_message: str,
        user_id: UUID,
        agent_name: str = "story_advisor",
        session: Session = None
    ) -> str:
        """
        Execute agent and return response.
        
        Args:
            session_id: Chat session ID
            user_message: User's message content
            user_id: User ID for authorization
            agent_name: Which agent to run (from registry)
            session: Database session
        
        Returns:
            Agent's response text
        """
        # Get agent from registry
        if agent_name not in AGENT_REGISTRY:
            raise ValueError(f"Unknown agent: {agent_name}")
        
        agent = AGENT_REGISTRY[agent_name]["agent"]
        
        # Build context
        ctx = await build_chat_context(session_id, user_id, session)
        
        # Run agent
        result = await agent.run(user_message, deps=ctx)
        
        # Emit response event
        with session.begin():
            await emit_event(
                session_id=session_id,
                event_type="message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": result.data,
                    "model": agent.model_name
                },
                session=session
            )
        
        return result.data
    
    async def stream_agent_response(
        self,
        session_id: UUID,
        user_message: str,
        user_id: UUID,
        agent_name: str = "story_advisor"
    ) -> AsyncIterator[str]:
        """
        Stream agent response token-by-token (for WebSocket).
        Used in Phase 4 (Streaming).
        """
        # Similar to run_agent but with streaming
        agent = AGENT_REGISTRY[agent_name]["agent"]
        ctx = await build_chat_context(session_id, user_id)
        
        full_response = ""
        async with agent.run_stream(user_message, deps=ctx) as result:
            async for chunk in result.stream_text():
                full_response += chunk
                yield chunk  # Stream to client
        
        # After streaming completes, emit final event
        with session.begin():
            await emit_event(
                session_id=session_id,
                event_type="message.agent",
                payload={
                    "agent_name": agent_name,
                    "content": full_response,
                    "model": agent.model_name
                },
                session=session
            )
```

---

## Migration Workflow

### Creating Event Sourcing Tables

When adding the chat feature:

```bash
# 1. Create migration
docker compose exec backend alembic revision --autogenerate -m "Add chat event sourcing tables"

# 2. Review the generated migration
# Check: backend/app/alembic/versions/XXX_add_chat_event_sourcing_tables.py

# 3. Apply migration
docker compose exec backend alembic upgrade head

# 4. Verify tables created
docker compose exec db psql -U postgres -d tinyfoot -c "\dt chat_*"
```

### Migration Template

```python
# alembic/versions/XXX_add_chat_event_sourcing_tables.py
"""Add chat event sourcing tables

Revision ID: XXX
Revises: YYY
Create Date: 2025-12-11 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'XXX'
down_revision = 'YYY'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Event log (append-only)
    op.create_table('chat_events',
        sa.Column('event_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('session_sequence', sa.BigInteger(), nullable=False),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('event_id'),
        sa.UniqueConstraint('session_id', 'session_sequence')
    )
    op.create_index('idx_chat_events_session_seq', 'chat_events', ['session_id', 'session_sequence'])
    op.create_index('idx_chat_events_type', 'chat_events', ['event_type', 'created_at'])
    
    # Trigger to prevent event mutations
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_chat_event_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'chat_events table is append-only - UPDATE/DELETE forbidden';
        END;
        $$ LANGUAGE plpgsql;
        
        CREATE TRIGGER prevent_chat_event_update
            BEFORE UPDATE OR DELETE ON chat_events
            FOR EACH ROW EXECUTE FUNCTION prevent_chat_event_mutation();
    """)
    
    # Chat sessions
    op.create_table('chat_sessions',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('story_id', sa.UUID(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['story_id'], ['story.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index('idx_chat_sessions_user', 'chat_sessions', ['user_id', 'last_activity'])
    
    # Message projection
    op.create_table('chat_messages',
        sa.Column('message_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('sender_type', sa.String(length=20), nullable=False),
        sa.Column('sender_id', sa.UUID(), nullable=True),
        sa.Column('agent_name', sa.String(length=50), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.session_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('message_id')
    )
    op.create_index('idx_chat_messages_session_time', 'chat_messages', ['session_id', 'created_at'])

def downgrade() -> None:
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.execute('DROP TRIGGER IF EXISTS prevent_chat_event_update ON chat_events')
    op.execute('DROP FUNCTION IF EXISTS prevent_chat_event_mutation')
    op.drop_table('chat_events')
```

---

## Performance Considerations

### Database Indexes

Critical indexes for chat system:

```sql
-- Event log queries
CREATE INDEX idx_chat_events_session_seq ON chat_events (session_id, session_sequence);
CREATE INDEX idx_chat_events_type ON chat_events (event_type, created_at);

-- Session queries
CREATE INDEX idx_chat_sessions_user ON chat_sessions (user_id, last_activity);

-- Message queries
CREATE INDEX idx_chat_messages_session_time ON chat_messages (session_id, created_at DESC);
```

### Query Optimization

**Fast Message Retrieval:**
```python
# Good - uses index
messages = session.exec(
    select(ChatMessage)
    .where(ChatMessage.session_id == session_id)
    .order_by(ChatMessage.created_at.desc())
    .limit(20)
).all()

# Bad - full table scan
messages = session.exec(
    select(ChatMessage)
    .order_by(ChatMessage.created_at.desc())
).all()
```

### Connection Pooling

Configure appropriate pool sizes in `app/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings ...
    
    # Database pool for general queries
    POSTGRES_POOL_SIZE: int = 10
    POSTGRES_MAX_OVERFLOW: int = 20
    
    # Separate pool for agent execution (long-running)
    AGENT_POOL_SIZE: int = 5
    AGENT_MAX_OVERFLOW: int = 10
```

---

## Error Handling

### Agent Execution Errors

```python
# app/services/agent_runner.py
import logging

logger = logging.getLogger(__name__)

async def run_agent(self, ...):
    try:
        result = await agent.run(user_message, deps=ctx)
        return result.data
    
    except TimeoutError:
        logger.error(f"Agent timeout for session {session_id}")
        return "I'm sorry, I'm taking too long to respond. Please try again."
    
    except Exception as e:
        logger.exception(f"Agent error for session {session_id}: {e}")
        
        # Emit error event
        await emit_event(
            session_id=session_id,
            event_type="agent.error",
            payload={
                "agent_name": agent_name,
                "error": str(e),
                "user_message": user_message[:100]
            },
            session=session
        )
        
        return "I encountered an error. Please try rephrasing your question."
```

### Event Emission Errors

```python
# If event emission fails, the entire transaction should rollback
async def send_message(...):
    try:
        with session.begin():
            await emit_event(...)
            # If this fails, transaction rolls back
    except Exception as e:
        logger.exception(f"Event emission failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to save message. Please try again."
        )
```

---

## Security Considerations

### Authorization

Always check session access:

```python
# app/crud.py
async def check_session_access(
    session_id: UUID,
    user_id: UUID,
    session: Session
) -> bool:
    """Check if user has access to session"""
    result = session.exec(
        select(ChatSession)
        .where(ChatSession.session_id == session_id)
        .where(ChatSession.user_id == user_id)
    ).first()
    
    return result is not None

# In routes
if not await check_session_access(session_id, current_user.id, session):
    raise HTTPException(status_code=403, detail="Access denied")
```

### Rate Limiting

Implement rate limiting for agent calls:

```python
# app/api/routes/chat.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/sessions/{session_id}/messages")
@limiter.limit("10/minute")  # 10 messages per minute per IP
async def send_message(...):
    # ...
```

---

## Monitoring and Logging

### Key Metrics to Track

```python
# app/services/agent_runner.py
from prometheus_client import Counter, Histogram

# Metrics
agent_calls_total = Counter(
    'agent_calls_total', 
    'Total agent executions',
    ['agent_name', 'status']
)

agent_duration = Histogram(
    'agent_duration_seconds',
    'Agent execution duration',
    ['agent_name']
)

# In run_agent()
with agent_duration.labels(agent_name=agent_name).time():
    try:
        result = await agent.run(...)
        agent_calls_total.labels(agent_name=agent_name, status='success').inc()
    except Exception:
        agent_calls_total.labels(agent_name=agent_name, status='error').inc()
        raise
```

### Structured Logging

```python
logger.info(
    "Agent execution completed",
    extra={
        "session_id": str(session_id),
        "user_id": str(user_id),
        "agent_name": agent_name,
        "message_length": len(user_message),
        "response_length": len(result.data),
        "duration_ms": duration_ms
    }
)
```

---

## Summary: Key Takeaways

1. **Agents are stateless** - All context comes from ChatContext dependency
2. **Events are immutable** - Never UPDATE or DELETE events
3. **Projections are transactional** - Updated in same transaction as events
4. **Tools should be focused** - One responsibility per tool
5. **Context is limited** - Keep to last 20 messages and story outline
6. **Always check authorization** - Before accessing sessions
7. **Log everything** - Agent calls, errors, durations
8. **Test event replay** - Projections must be rebuildable

---

**Next Steps After Phase 1:**
1. Review these patterns with team
2. Create first agent following these patterns
3. Write comprehensive tests
4. Update this document with learnings

---