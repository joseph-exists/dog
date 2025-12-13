# Minimog Integration Plan for TinyFoot
## Steel Thread: Conversational Story Assistance

**Created:** December 11, 2025  
**Purpose:** Define a clear path to integrate multi-agent chat capabilities into TinyFoot's story creation system

---

## 🎯 Strategic Framing (Why & What)

### Vision
Transform TinyFoot from a story template system into an **interactive story creation platform** where authors collaborate with AI agents to develop compelling narratives.

### Strategic Value
- **Authors:** Get real-time AI assistance while building story templates
- **Players:** Experience richer, more dynamic story instances with AI companions
- **System:** Unlock new gameplay patterns through persistent agent conversations

### Steel Thread Definition
> **"An author can open a chat sidebar while editing their story and ask an AI Story Advisor for suggestions about plot development, with conversation history persisted across sessions."**

This proves:
- ✅ Event sourcing for chat history
- ✅ PydanticAI agent integration with context
- ✅ Real-time frontend updates
- ✅ Multi-session persistence
- ✅ WebSocket streaming (Phase 2)

---

## 🏗️ Architectural Framing (Major Components)

### Current TinyFoot Architecture (Relevant Parts)
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Story Editor    - Persona Manager    - User Auth     │
└────────────────┬────────────────────────────────────────┘
                 │ REST API
┌────────────────▼────────────────────────────────────────┐
│              Backend (FastAPI)                           │
│  - Story CRUD    - User Auth    - agent_routes.py       │
│  - models.py     - crud.py                               │
└────────────────┬────────────────────────────────────────┘
                 │ SQL
┌────────────────▼────────────────────────────────────────┐
│         TimescaleDB (PostgreSQL + pgvector)              │
│  - stories    - users    - personas    - traits         │
└──────────────────────────────────────────────────────────┘
```

### Target Architecture (After Steel Thread)
```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                      │
│  - Story Editor    - Chat Sidebar [NEW]                 │
│  - AG-UI Components [NEW]                                │
└────────────────┬──────────────┬─────────────────────────┘
                 │ REST         │ WebSocket (Phase 2)
┌────────────────▼──────────────▼─────────────────────────┐
│              Backend (FastAPI)                           │
│  - Story CRUD    - Chat Routes [NEW]                     │
│  - Agent Runner [NEW]    - Event Emitter [NEW]           │
└────────────────┬───────────────┬─────────────────────────┘
                 │ SQL           │ Pub/Sub (Phase 2)
┌────────────────▼───────────────▼─────────────────────────┐
│         PostgreSQL            Redis [NEW]                │
│  - chat_events [NEW]          - Stream buffer            │
│  - chat_messages [NEW]                                   │
└──────────────────────────────────────────────────────────┘
```

### New Components to Add

| Component | Purpose | Complexity | Risk |
|-----------|---------|------------|------|
| **chat_events** table | Event sourcing log | Low | Low - standard table |
| **chat_messages** projection | Fast message queries | Low | Low - derived from events |
| **Redis** service | Real-time streaming (Phase 2) | Medium | Low - standard integration |
| **Chat API routes** | CRUD for chat sessions | Low | Low - follows existing patterns |
| **Agent Runner** service | Execute agents with context | Medium | Medium - new pattern |
| **Chat UI components** | Frontend sidebar | Medium | Low - standard React |
| **WebSocket handler** | Streaming (Phase 2) | High | Medium - concurrency concerns |

---

## 🎯 Implementation Framing (Vertical Slices)

Each phase delivers **end-to-end working value** that can be deployed independently.

### Phase 0: Infrastructure (2-3 days)
**Goal:** Add required infrastructure without breaking existing functionality

**Deliverables:**
- ✅ Redis container in docker-compose
- ✅ pgvector extension confirmed/enabled
- ✅ Connection pooling configuration
- ✅ Health checks updated

**Success Criteria:**
- All existing tests pass
- `docker-compose up` succeeds
- Can connect to Redis from backend

**Files Modified:**
- `docker-compose.yml` - Add Redis service
- `.env` - Add Redis connection string
- `backend/app/core/config.py` - Add Redis config
- `backend/requirements.txt` or `pyproject.toml` - Add `redis` package

---

### Phase 1: Event Sourcing Foundation (3-4 days)
**Goal:** Store chat messages as immutable events with projection

**Deliverables:**
- ✅ `room_events` table (event log)
- ✅ `rooms` table (metadata)
- ✅ `room_participants` projection table
- ✅ `messages` projection table
- ✅ RoomManager service
- ✅ Room API routes
- ✅ Participant management APIs
- ✅ Event emission helper functions
- ✅ Basic CRUD operations
- ✅ Alembic migration

**Database Schema:**
```sql
-- Event log (append-only)
-- DO NOT WRITE YET

-- Chat session metadata
-- DO NOT WRITE

-- Message projection (fast queries)
-- DO NOT WRITE
```

**API Endpoints:**
```python
POST   /api/v1/chat/sessions                    # Create session
GET    /api/v1/chat/sessions                    # List user's sessions
GET    /api/v1/chat/sessions/{session_id}       # Get session details
POST   /api/v1/chat/sessions/{session_id}/messages  # Send message (triggers agent)
GET    /api/v1/chat/sessions/{session_id}/messages  # Get message history
DELETE /api/v1/chat/sessions/{session_id}       # Delete session
```

**Success Criteria:**
- Can create chat session
- Can send message and retrieve it
- Events are immutable (UPDATE/DELETE fails)
- Projections update transactionally
- All existing tests still pass

**Files to Create:**
- `backend/app/models.py` - Add ChatEvent, ChatSession, ChatMessage models
- `backend/app/crud.py` - Add chat CRUD operations
- `backend/app/api/routes/chat.py` - Add chat endpoints
- `backend/app/alembic/versions/XXX_add_chat_tables.py` - Migration
- `backend/app/tests/api/routes/test_chat.py` - API tests

---

### Phase 2: Multi-User (including Agent) Integration (4-5 days)
**Goal:** Connect PydanticAI agents to chat context

**Deliverables:**
- ✅ StoryAdvisor agent with tools
- ✅ Agent runner service
- ✅ Context provider (loads story + chat history)
- ✅ Agent response stored as events
- ✅ Updated agent_routes.py pattern
- ✅ Agents registered as room participants
- ✅ Agent responses broadcast to all participants
- ✅ Room-aware context building
- ✅ Multiple agents can be in same room

**Agent Architecture:**
```python
# app/agents/story_advisor.py
from pydantic_ai import Agent, RunContext

class ChatContext:
    session_id: uuid.UUID
    user_id: uuid.UUID
    story_id: uuid.UUID | None
    story_data: dict | None
    message_history: list[dict]

story_advisor = Agent(
    'openai:gpt-4',
    system_prompt="""You are a Story Advisor helping authors create compelling narratives.
    You have access to the author's story outline and can suggest plot developments,
    character arcs, and narrative techniques.""",
    deps_type=ChatContext
)

@story_advisor.tool
async def get_story_outline(ctx: RunContext[ChatContext]) -> str:
    """Fetch the current story structure"""
    if ctx.deps.story_data:
        return format_story_outline(ctx.deps.story_data)
    return "No story context provided"

@story_advisor.tool
async def suggest_plot_twist(ctx: RunContext[ChatContext], genre: str) -> list[str]:
    """Generate plot twist ideas for the given genre"""
    # Use vector search to find similar successful stories
    # Return AI-generated suggestions
    pass
```

**Service Pattern:**
```python
# app/services/agent_runner.py
from typing import AsyncIterator

NOTE: NEEDS REFACTORED FOR AGENT ROOM PARTICIPATION
NOTE: MAY NEED REVISION BASED ON REDIS IMPLEMENTATION

class AgentRunner:
    async def run_agent(
        self, 
        session_id: UUID, 
        user_message: str, 
        user_id: UUID
    ) -> str:
        """Execute agent and return response (blocking version for Phase 2)"""
        
        # 1. Load context
        session = await get_session(session_id)
        story = await get_story(session.story_id) if session.story_id else None
        history = await get_messages(session_id, limit=20)
        
        # 2. Build agent context
        ctx = ChatContext(
            session_id=session_id,
            user_id=user_id,
            story_id=session.story_id,
            story_data=story,
            message_history=history
        )
        
        # 3. Run agent (blocking for now, streaming in Phase 3)
        result = await story_advisor.run(user_message, deps=ctx)
        
        # 4. Store response as event
        await emit_event(session_id, "message.agent", {
            "agent_name": "story_advisor",
            "content": result.data,
            "model": "gpt-4"
        })
        
        return result.data
```

**API Integration:**
```python
# app/api/routes/chat.py
@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    message: MessageCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ChatMessagePublic:
    # 1. Emit user message event
    await emit_event(session_id, "message.user", {
        "sender_id": str(current_user.id),
        "content": message.content
    })
    
    # 2. Run agent (blocking for Phase 2)
    agent_response = await AgentRunner().run_agent(
        session_id, 
        message.content, 
        current_user.id
    )
    
    # 3. Return agent response
    return ChatMessagePublic(
        sender_type="agent",
        agent_name="story_advisor",
        content=agent_response,
        created_at=datetime.now()
    )
```

**Success Criteria: NEEDS REVIEW**
- Agent responds to user messages
- Agent can access story context via tools
- Responses stored in chat_messages table
- Conversation maintains context across messages
- Agent responses are relevant to story content

**Files to Create/Modify:**
- `backend/app/agents/story_advisor.py` - New agent
- `backend/app/services/agent_runner.py` - New service
- `backend/app/services/context_provider.py` - Load story/chat context
- `backend/app/api/routes/chat.py` - Update with agent integration
- `backend/app/tests/agents/test_story_advisor.py` - Agent tests

---

### Phase 3: Frontend Multi-User Multi-Agent Chat UI (3-4 days)
**Goal:** Add chat sidebar to story editor

**Deliverables:**
- ✅ Chat sidebar component
- ✅ Message list with typing indicators
- ✅ Input field with send button
- ✅ Session management (create/switch/delete)
- ✅ OpenAPI client regeneration
- ✅ TypeScript SDK updates
- ✅ Room list view (all user's rooms)
- ✅ Room creation modal
- ✅ Participant list sidebar
- ✅ Message attribution (show sender name/avatar)
- ✅ Invite users/agents UI

**UI Structure:**
```
┌─────────────────────────────────────────────────┐
│  Story Editor                          [Chat >] │  
├─────────────────────────────┬───────────────────┤
│                             │ Story Advisor     │
│  Story Title: [         ]   │                   │
│                             │ ┌───────────────┐ │
│  Nodes:                     │ │ User: How do  │ │
│  □ Opening                  │ │ I create tens │ │
│  □ First Choice             │ │ ion?          │ │
│  □ Resolution               │ │               │ │
│                             │ │ Agent: Here   │ │
│  [+ Add Node]               │ │ are 3 ways... │ │
│                             │ └───────────────┘ │
│                             │                   │
│                             │ [Type message...] │
│                             │ [Send]            │
└─────────────────────────────┴───────────────────┘
```

**Component Hierarchy:**
```
<StoryEditor>
  <ChatSidebar isOpen={chatOpen}>
    <ChatHeader 
      sessionTitle="Story Advisor"
      onClose={() => setChatOpen(false)}
    />
    <MessageList>
      {messages.map(msg => (
        <Message 
          key={msg.id}
          senderType={msg.sender_type}
          content={msg.content}
          timestamp={msg.created_at}
        />
      ))}
      {isAgentTyping && <TypingIndicator />}
    </MessageList>
    <MessageInput 
      onSend={handleSendMessage}
      disabled={isAgentTyping}
    />
  </ChatSidebar>
</StoryEditor>
```

**State Management:**
```typescript
// hooks/useChat.ts
export function useChat(sessionId: string | null) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  
  const sendMessage = async (content: string) => {
    setIsLoading(true)
    try {
      // Add user message optimistically
      const userMsg = { sender_type: 'user', content, created_at: new Date() }
      setMessages(prev => [...prev, userMsg])
      
      // Send to API
      const response = await ChatService.sendMessage(sessionId, { content })
      
      // Add agent response
      setMessages(prev => [...prev, response])
    } finally {
      setIsLoading(false)
    }
  }
  
  return { messages, sendMessage, isLoading }
}
```

**Success Criteria:**
- Chat sidebar opens/closes smoothly
- Can send messages and see responses
- Message history persists on page reload
- Typing indicators work correctly
- Mobile responsive design

**Files to Create/Modify:**
- `frontend/src/components/Chat/ChatSidebar.tsx`
- `frontend/src/components/Chat/MessageList.tsx`
- `frontend/src/components/Chat/MessageInput.tsx`
- `frontend/src/components/Chat/Message.tsx`
- `frontend/src/hooks/useChat.ts`
- `frontend/src/services/chatService.ts`
- `frontend/src/client/` - Regenerate from OpenAPI spec

---

### Phase 4: Real-Time Streaming (5-6 days)
**Goal:** Stream agent responses token-by-token via WebSocket

**Deliverables:**
- ✅ WebSocket endpoint for chat sessions
- ✅ Redis pub/sub integration
- ✅ AG-UI WebSocket protocol support
- ✅ Streaming agent responses
- ✅ Frontend WebSocket client

**WebSocket Flow:**
```
1. Client opens WebSocket: ws://api.domain/ws/chat/{session_id}
2. Server validates JWT, checks session access
3. Client sends: {"type": "message.send", "content": "..."}
4. Server emits user message event
5. Server starts agent execution
6. Agent streams tokens → Redis pub/sub → WebSocket → Client
7. Server emits final message.agent event
8. Client receives: {"type": "message.delta", "content": "token"}
                    {"type": "message.complete", "message_id": 123}
```

**Backend WebSocket Handler:**
```python
# app/api/routes/websocket.py
from fastapi import WebSocket, WebSocketDisconnect
import redis.asyncio as redis

@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(
    websocket: WebSocket,
    session_id: UUID,
    token: str = Query(...),
):
    # Validate JWT
    user = await validate_jwt_token(token)
    
    # Check session access
    if not await can_access_session(user.id, session_id):
        await websocket.close(code=403)
        return
    
    await websocket.accept()
    
    # Subscribe to Redis channel for this session
    redis_client = redis.from_url(settings.REDIS_URL)
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"chat:{session_id}")
    
    async def listen_redis():
        """Forward Redis messages to WebSocket"""
        async for message in pubsub.listen():
            if message["type"] == "message":
                await websocket.send_json(json.loads(message["data"]))
    
    async def listen_client():
        """Handle client messages"""
        try:
            async for data in websocket.iter_json():
                if data["type"] == "message.send":
                    # Emit user message event
                    await emit_event(session_id, "message.user", {
                        "sender_id": str(user.id),
                        "content": data["content"]
                    })
                    
                    # Stream agent response
                    await stream_agent_response(session_id, data["content"], user.id)
        except WebSocketDisconnect:
            await pubsub.unsubscribe(f"chat:{session_id}")
    
    await asyncio.gather(listen_redis(), listen_client())
```

**Agent Streaming:**
```python
# app/services/agent_runner.py
async def stream_agent_response(
    session_id: UUID, 
    user_message: str, 
    user_id: UUID
):
    # Load context
    ctx = await build_chat_context(session_id, user_id)
    
    # Run agent with streaming
    async with story_advisor.run_stream(user_message, deps=ctx) as result:
        full_text = ""
        async for chunk in result.stream_text():
            # Publish token to Redis (ephemeral)
            await redis_client.publish(
                f"chat:{session_id}",
                json.dumps({
                    "type": "message.delta",
                    "content": chunk
                })
            )
            full_text += chunk
        
        # After stream completes, emit final event (persistent)
        await emit_event(session_id, "message.agent", {
            "agent_name": "story_advisor",
            "content": full_text
        })
        
        # Publish completion message
        await redis_client.publish(
            f"chat:{session_id}",
            json.dumps({
                "type": "message.complete",
                "content": full_text
            })
        )
```

**Frontend WebSocket Client:**
```typescript
// hooks/useChatStream.ts
export function useChatStream(sessionId: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentDelta, setCurrentDelta] = useState("")
  const wsRef = useRef<WebSocket | null>(null)
  
  useEffect(() => {
    const token = localStorage.getItem('token')
    const ws = new WebSocket(
      `ws://api.${domain}/ws/chat/${sessionId}?token=${token}`
    )
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      
      if (data.type === "message.delta") {
        // Accumulate streaming tokens
        setCurrentDelta(prev => prev + data.content)
      } else if (data.type === "message.complete") {
        // Finalize message
        setMessages(prev => [...prev, {
          sender_type: 'agent',
          content: data.content,
          created_at: new Date()
        }])
        setCurrentDelta("")
      }
    }
    
    wsRef.current = ws
    return () => ws.close()
  }, [sessionId])
  
  const sendMessage = (content: string) => {
    wsRef.current?.send(JSON.stringify({
      type: "message.send",
      content
    }))
  }
  
  return { messages, currentDelta, sendMessage }
}
```

**Success Criteria:**
- Agent responses stream token-by-token
- Multiple users can chat simultaneously
- WebSocket reconnects automatically
- Missed messages replayed on reconnect
- No message loss during network issues

**Files to Create/Modify:**
- `backend/app/api/routes/websocket.py` - New WebSocket endpoint
- `backend/app/services/agent_runner.py` - Add streaming support
- `backend/app/core/redis.py` - Redis client singleton
- `frontend/src/hooks/useChatStream.ts` - WebSocket hook
- `frontend/src/components/Chat/StreamingMessage.tsx` - Streaming UI

---

### Phase 5: Multi-Agent System (Optional, 6-8 days)
**Goal:** Support multiple specialized agents with handoffs

**Deliverables:**
- ✅ Agent registry pattern
- ✅ Agent handoff tool
- ✅ Context preservation across agents
- ✅ UI shows current agent
- ✅ Step tracking for tool execution

**Agent Registry:**
```python
# app/agents/registry.py
AGENT_REGISTRY = {
    "story_advisor": {
        "agent": story_advisor,
        "display_name": "Story Advisor",
        "description": "Helps with plot and character development",
        "can_transfer_to": ["character_expert", "plot_analyzer"]
    },
    "character_expert": {
        "agent": character_expert,
        "display_name": "Character Expert",
        "description": "Specializes in character arcs and development",
        "can_transfer_to": ["story_advisor"]
    },
    "plot_analyzer": {
        "agent": plot_analyzer,
        "display_name": "Plot Analyzer",
        "description": "Analyzes story structure and pacing",
        "can_transfer_to": ["story_advisor"]
    }
}
```

**Handoff Tool:**
```python
@story_advisor.tool
async def transfer_to_specialist(
    ctx: RunContext[ChatContext], 
    specialist: Literal["character_expert", "plot_analyzer"],
    reason: str
) -> str:
    """Transfer conversation to a specialist agent"""
    
    # Emit handoff event
    await emit_event(ctx.deps.session_id, "agent.handoff", {
        "from_agent": "story_advisor",
        "to_agent": specialist,
        "reason": reason,
        "context_summary": f"User needs help with: {reason}"
    })
    
    # Next message will trigger the specialist agent
    return f"Transferring you to the {specialist.replace('_', ' ').title()}..."
```

**Success Criteria:**
- Agent can transfer to specialist
- Conversation context preserved
- UI indicates agent change
- User can manually switch agents

---

## 📋 Task Framing (Specific Work Items)

### Phase 0 Tasks (Infrastructure)
```
□ Task 0.1: Add Redis to docker-compose.yml
  Files: docker-compose.yml
  Time: 30 min
  
□ Task 0.2: Add Redis Python client
  Files: backend/pyproject.toml
  Time: 15 min
  
□ Task 0.3: Create Redis connection singleton
  Files: backend/app/core/redis.py
  Time: 1 hour
  
□ Task 0.4: Verify pgvector extension
  Files: None (SQL check)
  Time: 30 min
  
□ Task 0.5: Update health checks
  Files: backend/app/api/routes/utils.py
  Time: 1 hour
```

### Phase 1 Tasks (Event Sourcing)
```
□ Task 1.1: Design event schema
  Files: Design doc
  Time: 2 hours
  
□ Task 1.2: Create SQLModel models
  Files: backend/app/models.py
  Time: 3 hours
  
□ Task 1.3: Create Alembic migration
  Files: backend/app/alembic/versions/XXX_add_chat.py
  Time: 2 hours
  
□ Task 1.4: Implement emit_event() helper
  Files: backend/app/services/event_emitter.py
  Time: 2 hours
  
□ Task 1.5: Implement chat CRUD operations
  Files: backend/app/crud.py
  Time: 4 hours
  
□ Task 1.6: Create chat API routes
  Files: backend/app/api/routes/chat.py
  Time: 4 hours
  
□ Task 1.7: Write API tests
  Files: backend/app/tests/api/routes/test_chat.py
  Time: 3 hours
  
□ Task 1.8: Register routes in main.py
  Files: backend/app/api/main.py
  Time: 30 min
  
□ Task 1.9: Integration testing
  Files: Various
  Time: 2 hours
```

### Phase 2 Tasks (Agent Integration)
```
□ Task 2.1: Create StoryAdvisor agent
  Files: backend/app/agents/story_advisor.py
  Time: 3 hours
  
□ Task 2.2: Implement agent tools
  Files: backend/app/agents/story_advisor.py
  Time: 4 hours
  
□ Task 2.3: Create AgentRunner service
  Files: backend/app/services/agent_runner.py
  Time: 4 hours
  
□ Task 2.4: Create ContextProvider service
  Files: backend/app/services/context_provider.py
  Time: 3 hours
  
□ Task 2.5: Integrate agent with chat routes
  Files: backend/app/api/routes/chat.py
  Time: 2 hours
  
□ Task 2.6: Write agent tests
  Files: backend/app/tests/agents/test_story_advisor.py
  Time: 3 hours
  
□ Task 2.7: Update agent_routes.py pattern
  Files: backend/app/api/routes/agent_routes.py
  Time: 2 hours
  
□ Task 2.8: Document agent creation in RULES.md
  Files: backend/RULES.md
  Time: 1 hour
```

### Phase 3 Tasks (Frontend)
```
□ Task 3.1: Generate OpenAPI client
  Command: npm run generate-client
  Time: 30 min
  
□ Task 3.2: Create chat service
  Files: frontend/src/services/chatService.ts
  Time: 2 hours
  
□ Task 3.3: Create useChat hook
  Files: frontend/src/hooks/useChat.ts
  Time: 2 hours
  
□ Task 3.4: Create ChatSidebar component
  Files: frontend/src/components/Chat/ChatSidebar.tsx
  Time: 3 hours
  
□ Task 3.5: Create MessageList component
  Files: frontend/src/components/Chat/MessageList.tsx
  Time: 2 hours
  
□ Task 3.6: Create Message component
  Files: frontend/src/components/Chat/Message.tsx
  Time: 2 hours
  
□ Task 3.7: Create MessageInput component
  Files: frontend/src/components/Chat/MessageInput.tsx
  Time: 2 hours
  
□ Task 3.8: Integrate into StoryEditor
  Files: frontend/src/routes/_layout/stories/$storyId/edit.tsx
  Time: 2 hours
  
□ Task 3.9: Add CSS styling
  Files: frontend/src/components/Chat/chat.css
  Time: 2 hours
  
□ Task 3.10: Mobile responsive testing
  Files: Various
  Time: 2 hours
```

### Phase 4 Tasks (Streaming)
```
□ Task 4.1: Create WebSocket endpoint
  Files: backend/app/api/routes/websocket.py
  Time: 4 hours
  
□ Task 4.2: Implement Redis pub/sub
  Files: backend/app/services/agent_runner.py
  Time: 3 hours
  
□ Task 4.3: Add streaming to AgentRunner
  Files: backend/app/services/agent_runner.py
  Time: 4 hours
  
□ Task 4.4: Create useChatStream hook
  Files: frontend/src/hooks/useChatStream.ts
  Time: 3 hours
  
□ Task 4.5: Create StreamingMessage component
  Files: frontend/src/components/Chat/StreamingMessage.tsx
  Time: 2 hours
  
□ Task 4.6: Update ChatSidebar for streaming
  Files: frontend/src/components/Chat/ChatSidebar.tsx
  Time: 2 hours
  
□ Task 4.7: Implement reconnection logic
  Files: frontend/src/hooks/useChatStream.ts
  Time: 3 hours
  
□ Task 4.8: Add message replay on reconnect
  Files: backend/app/api/routes/websocket.py
  Time: 3 hours
  
□ Task 4.9: Load testing
  Files: Test scripts
  Time: 4 hours
```

---

## 🔍 Decision Framework

### When to Use REST vs WebSocket

**Use REST (Phase 1-2):**
- Creating/listing chat sessions
- Getting message history
- Simple request-response patterns
- Initial implementation (faster to build)

**Use WebSocket (Phase 3+):**
- Real-time message streaming
- Multi-user scenarios
- Live agent typing indicators
- High-frequency updates

### When to Use Event Sourcing

**Always Use Events For:**
- Chat messages (user and agent)
- Agent handoffs
- Tool executions (Phase 5)
- Anything requiring audit trail

**Don't Use Events For:**
- Temporary UI state
- Session metadata updates
- User preferences
- Read-only queries

### Context Strategy

**Load Into Agent Context:**
- Current story outline (if editing story)
- Last 20 messages from session
- User persona preferences
- Relevant story nodes

**Don't Load:**
- Full story with all nodes (too large)
- Other users' chat sessions
- System logs
- Unrelated data

---

## 📊 Success Metrics

### Phase 0
- Infrastructure health: 100% services healthy
- Zero regression in existing tests

### Phase 1
- API response time: <100ms for message CRUD
- Event write throughput: >100/second
- All existing tests pass

### Phase 2
- Agent response time: <3 seconds
- Context relevance: Manual testing shows story awareness
- Tool execution success rate: >95%

### Phase 3
- UI responsiveness: <100ms interactions
- Chat loads: <500ms
- Mobile compatibility: Works on iOS/Android

### Phase 4
- Streaming latency: <100ms per token
- WebSocket uptime: >99.9%
- Concurrent users: 50+ without degradation

---

## 🚧 Risk Mitigation

### High-Risk Areas

| Risk | Mitigation | Owner |
|------|------------|-------|
| WebSocket complexity | Start with REST (Phase 2), add streaming later | Backend team |
| Agent response quality | Extensive prompt engineering + manual testing | Product + AI |
| Context window limits | Implement sliding window (20 messages max) | Backend team |
| Frontend bundle size | Lazy load chat components | Frontend team |
| Database growth | Partition chat_events by month | DevOps |
| Redis unavailability | Graceful fallback to REST polling | Backend team |

### Rollback Strategy

Each phase is independently deployable:
- **Phase 0**: Can disable Redis if issues arise
- **Phase 1**: Can hide chat UI via feature flag
- **Phase 2**: Can disable agent integration
- **Phase 3**: Can revert to server-rendered chat
- **Phase 4**: Can fall back to REST polling

---

## 📖 Documentation Updates

### Files to Update

**After Phase 1:**
- [ ] `backend/RULES.md` - Add event sourcing patterns
- [ ] `README.md` - Document chat feature
- [ ] `backend/app/README.md` - Update service architecture

**After Phase 2:**
- [ ] `backend/RULES.md` - Add agent patterns
- [ ] `backend/app/agents/README.md` - Agent creation guide
- [ ] API documentation - Add chat endpoints

**After Phase 3:**
- [ ] `frontend/README.md` - Document chat components
- [ ] Component Storybook - Add chat stories

**After Phase 4:**
- [ ] WebSocket protocol documentation
- [ ] Deployment guide - Add Redis requirements

---

## 🎓 Learning Resources

### Team Knowledge Gaps

| Topic | Resource | Priority |
|-------|----------|----------|
| Event Sourcing | Martin Fowler's articles | High |
| PydanticAI | Official docs | High |
| WebSocket patterns | Real Python WebSocket guide | Medium |
| Redis pub/sub | Redis University | Medium |
| AG-UI protocol | PydanticAI examples | High |

---

## 🚀 Getting Started

### Immediate Next Steps

1. **Week 1:** Complete Phase 0 (Infrastructure)
   - Add Redis to development environment
   - Verify pgvector works
   - Update health checks

2. **Week 2-3:** Complete Phase 1 (Event Sourcing)
   - Implement event tables
   - Build REST API
   - Write comprehensive tests

3. **Review & Plan:** After Phase 1
   - Demo to stakeholders
   - Gather feedback
   - Plan Phase 2 work

### First PR to Create

**Title:** "Add Redis infrastructure for chat feature"

**Description:**
```
This PR adds Redis to docker-compose and creates the connection singleton
needed for the upcoming chat feature. No behavior changes to existing features.

- Added redis service to docker-compose.yml
- Added redis client to pyproject.toml
- Created app/core/redis.py connection singleton
- Updated health check to include Redis
- Updated .env.example with Redis configuration

Closes #XXX
```

---

## 🎯 Success Definition

**Steel Thread is Complete When:**
1. Author can open chat sidebar while editing story ✅
2. Author can ask "How do I create tension?" ✅
3. StoryAdvisor agent responds with story-aware suggestions ✅
4. Conversation persists across page reloads ✅
5. All existing TinyFoot features still work ✅
6. Zero production incidents from new code ✅

**Ready for Production When:**
- All 4 phases complete
- Load tested with 50 concurrent users
- Security review passed
- Documentation complete
- Rollback plan tested

---

## Appendix A: File Structure After Steel Thread

```
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── quixote.py (existing)
│   │   ├── story_advisor.py (new)
│   │   └── registry.py (new - Phase 5)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── event_emitter.py (new)
│   │   ├── agent_runner.py (new)
│   │   └── context_provider.py (new)
│   ├── api/routes/
│   │   ├── chat.py (new)
│   │   ├── websocket.py (new - Phase 4)
│   │   └── agent_routes.py (modified)
│   ├── core/
│   │   ├── redis.py (new)
│   │   └── config.py (modified)
│   └── alembic/versions/
│       └── XXX_add_chat_tables.py (new)

frontend/
├── src/
│   ├── components/
│   │   └── Chat/ (new)
│   │       ├── ChatSidebar.tsx
│   │       ├── MessageList.tsx
│   │       ├── Message.tsx
│   │       ├── MessageInput.tsx
│   │       ├── StreamingMessage.tsx (Phase 4)
│   │       └── chat.css
│   ├── hooks/
│   │   ├── useChat.ts (new)
│   │   └── useChatStream.ts (new - Phase 4)
│   ├── services/
│   │   └── chatService.ts (new)
│   └── client/ (regenerated after each phase)
```

---

## Appendix B: Example User Journey

**Author's Perspective:**

1. **Login** - Opens TinyFoot dashboard
2. **Select Story** - Clicks "Edit" on "The Lost Kingdom"
3. **Open Chat** - Clicks chat icon in top right
4. **Ask Question** - Types: "How can I make the dragon encounter more dramatic?"
5. **Get Response** - StoryAdvisor analyzes current story outline and suggests:
   - Building tension through sensory details
   - Adding a countdown element
   - Creating internal character conflict
   - Referencing specific nodes in the author's story
6. **Implement** - Author applies suggestions to story nodes
7. **Follow Up** - Asks: "How does this affect the protagonist's arc?"
8. **Context Maintained** - Agent remembers previous conversation and story context
9. **Close Chat** - Returns later, conversation history preserved

**Technical Flow:**

```
User → Frontend → REST API → Event Log → Agent → Tools → Response → Frontend
                     ↓                       ↓                   ↑
                 chat_events            Story Context      WebSocket (Phase 4)
                     ↓                       ↓
                chat_messages           chat_messages
```

---

**END OF INTEGRATION PLAN**

Ready to begin Phase 0? Let's add Redis! 🚀