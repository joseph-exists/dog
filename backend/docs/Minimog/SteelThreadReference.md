# TinyFoot-Minimog Steel Thread: Quick Reference Card

**Print this and keep it visible while developing! 🎯**

---

## 🎯 The Steel Thread Goal

> **"Multiple authors join a shared room attached to a story, invite the StoryAdvisor agent, exchange messages, and all participants see updates in real time while conversations persist across sessions."**

---

## 📊 Current Status Checklist

### Infrastructure (Phase 0)
- [X] Redis running in docker-compose
- [X] Redis client installed (`redis` in pyproject.toml)
- [X] Redis connection singleton created (`app/core/redis.py`)
- [X] pgvector extension verified
- [X] Health checks updated

### Event Sourcing (Phase 1)
- [X] `room_events` table created with event_version field, required for replayability until upcaster services and schema registry
- [X] `rooms` table created
- [X] `room_participants` table created
- [X] `messages` projection created
- [X] Migration applied
- [X] Event emitter service implemented
- [X] Room CRUD operations implemented
- [X] Participant management APIs working
- [X] Room API routes working
- [X] Tests passing (>80% coverage)

### Agent Integration (Phase 2) ✅ COMPLETE
- [X] `story_advisor.py` agent created with PydanticAI
- [X] Agent registry implemented (`agent_registry.py`)
- [X] Agent tools implemented (get_story_outline, get_conversation_summary, get_room_participants)
- [X] AgentRunner service implemented (`agent_runner.py`)
- [X] ContextProvider service implemented (room-aware context with story + messages)
- [X] Agents added as first-class room participants (participant_type='agent')
- [X] Room routes integrated with agent execution (`send_message` triggers agents)
- [X] `participant.joined` events for agents working
- [X] Agent tests passing (19/19 tests - registry, context provider, agent runner, integration)
- [X] Documentation updated (Phase 2 plan, test script + guide)
- [X] End-to-end test script created (`test_agent_integration.py`)

### Frontend UI (Phase 3)
- [X] OpenAPI client regenerated
- [X] Room UI component created
- [X] Room component added to frontend leftnav
- [X] ParticipantList component created
- [X] MessageList/Message components created (with sender attribution)
- [X] MessageInput component created
- [X] useRoom hook implemented
- [X] Room creation and joining flows implemented 
- [X] Room navigation (invite, join, see available rooms, etc)
- [*] Room archive and delete functionality implemented (DEFERRED)
- [*] Mobile responsive : Not in dev framework, external
- [X] UI tests passing : Not in dev framework, external : Valid for current MVP


### Streaming (Phase 4) - 🟢 87.5% Complete (7/8 deliverables)
- [X] WebSocket endpoint created (`app/api/routes/websocket.py`)
- [X] Redis pub/sub fanout working (with advisory locks for sequence generation)
- [X] Agent streaming implemented (token-by-token with cumulative chunk handling)
- [X] useRoomStream hook created (throttled buffering, single connection pattern)
- [X] Frontend shows streaming tokens to all participants
- [X] Reconnection with sequence-based replay working

**Critical Fixes Applied:**
- ✅ Redis connection infrastructure (complete rewrite with ConnectionPool)
- ✅ Docker networking (REDIS_HOST=redis for service name resolution)
- ✅ PydanticAI cumulative chunk handling (extract deltas from full messages)
- ✅ WebSocket hook architecture (single connection per room, no duplicates)
- ✅ Token buffering and throttling (50ms, prevents render spam)

---

## 🏗️ Architecture at a Glance

```
User Message → REST Endpoint (AsyncSessionTransactionDep)
                        ↓
                [TRANSACTION STARTS]
                        ↓
                CRUD: send_user_message()
                        ↓
                emit_event("message.user")
                        ↓
                room_events (append-only log)
                        ↓
                _update_projections()
                        ↓
                rooms, room_participants, room_messages (projections)
                        ↓
                session.flush() — makes changes visible
                        ↓
                [TRANSACTION COMMITS]
                        ↓
                AgentRunner.run_agent() (Phase 2)
                        ↓
                StoryAdvisor Agent (room participant)
                        ↓
                Tools (get_story_outline, etc.)
                        ↓
                emit_event("message.agent")
                        ↓
                Redis pub/sub → WebSocket fanout (Phase 4)
                        ↓
                All connected participants receive updates
```

---

## 📂 File Structure Quick Map

```
backend/
├── app/
│   ├── agents/
│   │   ├── __init__.py ✅ (Phase 2 - registers agents)
│   │   ├── agent_registry.py ✅ (Phase 2 - AGENT_REGISTRY)
│   │   ├── story_advisor.py ✅ (Phase 2 - with tools)
│   │   └── quixote.py ✅ (existing)
│   ├── services/
│   │   ├── event_emitter.py ✅ (Phase 1 complete)
│   │   ├── agent_runner.py ✅ (Phase 2 - run_agents_for_message)
│   │   └── context_provider.py ✅ (Phase 2 - build_room_context)
│   ├── api/routes/
│   │   ├── rooms.py ✅ (Phase 1 + 2 - agent integration at :316-321)
│   │   └── websocket.py (Phase 4)
│   ├── api/
│   │   └── deps.py ✅ (AsyncSessionTransactionDep added)
│   ├── crud.py ✅ (Room operations complete)
│   ├── main.py ✅ (imports app.agents for registration)
│   └── core/
│       └── redis.py ✅ (Phase 0 complete)
frontend/
├── src/
│   ├── components/Rooms/
│   │   ├── addParticipantDialog.tsx 
│   │   ├── addRoom.tsx ✅
│   │   ├── AgentToggle.tsx ✅
│   │   ├── EditRoomDialog.tsx ✅
│   │   ├── Message.tsx ✅
│   │   ├── MessageInput.tsx ✅
│   │   ├── MessageList.tsx ✅
│   │   ├── ParticipantList.tsx ✅
│   │   ├── RemoveParticipantButton.tsx ✅
│   │   ├── RoomCard.tsx ✅
│   │   ├── RoomHeader.tsx ✅
│   │   ├── RoomList.tsx ✅
│   ├── hooks/
│   │   ├── useRoom.ts ✅
│   │   ├── useRoomMessages.ts ✅
│   │   └── useRoomStream.ts  (Phase 4)
│   ├── routes/_layout/
│       └── room.$roomId.tsx ✅
│       └── rooms.tsx ✅
│   └── services/
│       └── roomService.ts ✅

```

---

## 🔑 Key Patterns to Remember

### Event Sourcing Rules
```python
### Event Sourcing Rules
# ✅ CORRECT - Immutable append to room event log
await emit_event(room_id, "message.user", {...})

# ❌ WRONG - Never mutate events
await db.execute("UPDATE room_events SET ...")
await db.execute("DELETE FROM room_events ...")

# ✅ CORRECT - New event to record changes
await emit_event(room_id, "message.deleted", {
    "deleted_message_id": old_id
})
```

### Agent Pattern
```python
# 1. Define room-aware context type
class RoomContext(BaseModel):
    room_id: UUID
    user_id: UUID
    story_data: dict | None
    participants: list[dict]  # Room participants metadata
    room_metadata: dict

# 2. Create agent with context
agent = Agent(
    'openai:gpt-4',
    system_prompt="You are...",
    deps_type=RoomContext
)

# 3. Add tools
@agent.tool
async def my_tool(ctx: RunContext[RoomContext]) -> str:
    return await do_something(ctx.deps.story_data)

```

### Transaction Pattern (Route-Level Management)
```python
# ✅ CORRECT - Route handler owns transaction lifecycle
@router.post("/rooms/{room_id}/messages")
async def send_message(
    session: AsyncSessionTransactionDep,  # Transaction starts here
    room_id: UUID,
    current_user: CurrentUser,
    message_in: RoomMessageSend,
):
    # All operations use the route-level transaction
    message = await send_user_message(
        room_id=room_id,
        user_id=current_user.id,
        content=message_in.content,
        session=session,  # Passes route's transaction to CRUD
    )
    # Transaction commits on successful return
    # Transaction rolls back on any exception
    return message

# ❌ WRONG - Don't manage transactions in CRUD functions
async def send_user_message(session: AsyncSession, ...):
    async with session.begin():  # ❌ NO! Route already started transaction
        await emit_event(session, ...)  # This will cause nested transaction error

# ✅ CORRECT - CRUD functions are transaction-agnostic
async def send_user_message(session: AsyncSession, ...):
    # Uses session provided by route (transaction already active)
    await emit_event(session, ...)
    # emit_event writes to room_events, updates projections, calls session.flush()
    # All changes are visible for subsequent queries in same transaction
```

### Authorization Pattern
```python
# Always check room membership before any room operation
if not await check_room_membership(room_id, user.id, session):
    raise HTTPException(403, "Access denied")

# Validates user is an active participant in room_participants table
```

---

## 🧪 Testing Checklist

### Unit Tests
- [X] Event emitter creates events with correct per-room sequence
- [X] Projection updates work correctly (rooms, room_participants, messages)
- [X] Agent tools return expected formats (StoryAdvisor tools: 3/3 passing)
- [X] Context provider loads story data and room metadata (5/5 tests passing)
- [X] Participant management functions work correctly
- [X] Agent registry validates registration and lookup (6/6 tests passing)

### Integration Tests
- [X] Can create room via API
- [X] Can add participants (users and agents) to room
- [X] Can send message and all participants receive updates
- [X] Agent responses are visible to all room participants
- [X] Events are written atomically with projections
- [X] Multi-user authorization enforced correctly
- [X] Agent integration end-to-end works (`test_agent_integration.py`)
- [X] WebSocket connects and streams to multiple participants

### Manual Tests
- [X] Can create room via REST API (POST /rooms)
- [X] Can add StoryAdvisor agent to room (POST /rooms/{id}/participants)
- [X] Send message triggers agent automatically
- [X] Agent response persisted in messages
- [X] Agent response visible via GET /rooms/{id}/messages
- [X] Agent demonstrates story context awareness (tested)
- [X] Agent demonstrates message history awareness (tested)
- [X] Participant list shows all active users and agents
- [X] Frontend UI integration (Phase 3)
- [ ] Real-time WebSocket updates (Phase 4)

---



---

## 🎬 First Steps (Phase 0)

### Day 1: Add Redis
```bash
# 1. Add to docker-compose.yml
redis:
  image: redis:8.2-alpine
  ports:
    - "6379:6379"
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]

# 2. Add Python client
cd backend
uv add redis

# 3. Create connection
# File: app/core/redis.py
from redis.asyncio import Redis
redis_client = Redis.from_url(settings.REDIS_URL)

# 4. Test
docker compose up -d redis
docker compose exec redis redis-cli ping
# Should return: PONG
```

### Day 2: Verify pgvector
```sql
-- Connect to database
docker compose exec db psql -U postgres -d tinyfoot

-- Check extension
\dx

-- If not installed:
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify
SELECT * FROM pg_extension WHERE extname = 'vector';
```

---

## 📞 Quick Commands

### Backend
```bash
# Generate migration
docker compose exec backend alembic revision --autogenerate -m "Description"

# Apply migration
docker compose exec backend alembic upgrade head

# Run tests
docker compose exec backend pytest

# Check logs
docker compose logs -f backend

# Shell into backend
docker compose exec backend bash
```

### Frontend
```bash
# Regenerate OpenAPI client
npm run generate-client

# Run dev server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```

### Database
```bash
# Connect to PostgreSQL
docker compose exec db psql -U postgres -d tinyfoot

# View room events
SELECT * FROM room_events ORDER BY created_at DESC LIMIT 10;

# View projections
SELECT * FROM rooms ORDER BY last_activity DESC LIMIT 10;
SELECT * FROM room_participants WHERE room_id = '<room_id>';
SELECT * FROM messages WHERE room_id = '<room_id>' ORDER BY created_at DESC LIMIT 10;


# Check table sizes
SELECT 
    tablename, 
    pg_size_pretty(pg_total_relation_size(tablename::text)) 
FROM pg_tables 
WHERE schemaname = 'public';
```

---

## 🔍 Debugging Tips

### Agent Not Responding?
```python
# Add logging to agent runner
import logging
logger = logging.getLogger(__name__)

async def run_agent(...):
    logger.info(f"Running agent for room {room_id}")
    logger.info(f"Room context: {ctx}")
    logger.info(f"Participants: {ctx.participants}")
    result = await agent.run(...)
    logger.info(f"Agent response: {result.data[:100]}...")

```

### Events Not Persisting?
```python
# ✅ Check if route uses AsyncSessionTransactionDep
@router.post("/rooms/{room_id}/messages")
async def send_message(
    session: AsyncSessionTransactionDep,  # Must use this for writes!
    ...
):
    await send_user_message(session=session, ...)
    # Transaction commits here automatically

# ❌ Common mistake - using AsyncSessionDep for write operations
@router.post("/rooms/{room_id}/messages")
async def send_message(
    session: AsyncSessionDep,  # WRONG! No transaction
    ...
):
    await send_user_message(session=session, ...)
    # Changes may not be committed!
```

### Transaction Errors?
```python
# Check for nested transaction attempts in CRUD
async def my_crud_function(session: AsyncSession, ...):
    async with session.begin():  # ❌ Remove this!
        await emit_event(session, ...)
    # Error: "A transaction is already begun on this Session"

# ✅ CRUD should be transaction-agnostic
async def my_crud_function(session: AsyncSession, ...):
    await emit_event(session, ...)  # Uses route's transaction
```

### WebSocket Not Connecting?
```javascript
// Check token format and room membership
const token = localStorage.getItem('token')
const ws = new WebSocket(\`ws://localhost:8000/ws/rooms/\${roomId}?token=\${token}\`)

ws.onerror = (error) => {
    console.error('WebSocket error:', error)
    console.error('Check room membership for user')
}
```

---

## 📖 Quick Links

- **Phase 2 Plan:** `/backend/docs/PLAN_phase2_agent_integration.md`
- **Phase 2 Test:** `/backend/app/test_scripts/test_agent_integration.py`
- **Test Guide:** `/backend/app/test_scripts/AGENT_INTEGRATION_TEST.md`
- **Agent Patterns:** `/backend/AGENT-PATTERNS.md`
- **Current Rules:** `/backend/RULES.md`
- **PydanticAI Docs:** https://ai.pydantic.dev
- **AG-UI Examples:** https://github.com/pydantic/pydantic-ai/tree/main/examples

---

## ✅ Definition of Done (Steel Thread)

The steel thread is complete when:
## ✅ Definition of Done (Steel Thread)

The steel thread is complete when:

1. ✅ Infrastructure is healthy (Redis + pgvector) - **DONE Phase 0**
2. ✅ Can create room via API (optionally with initial agents) - **DONE Phase 1**
3. ✅ Can add multiple users and agents as room participants - **DONE Phase 1+2**
4. ✅ Multiple authors can send messages in same room - **DONE Phase 1**
5. ✅ StoryAdvisor (as room participant) responds with story-aware answers - **DONE Phase 2** ⭐
6. ✅ All room participants see all messages with correct attribution - **DONE Phase 2** ⭐
7. ✅ Conversation and participants persist on page reload - **DONE Phase 1+2** ⭐
8. ✅ Room UI works with participant list multi-user and multi-agent - **DONE Phase 3**
9. ✅ All tests pass (unit + integration + multi-user scenarios) - **DONE (19/19 passing)** ⭐
10. ✅ No regressions in existing features - **VERIFIED**
11. ✅ Authorization enforces room membership correctly - **DONE Phase 1**
12. ✅ Documentation updated - **DONE Phase 2** ⭐
13. ✅ Can demo multi-user end-to-end to stakeholder - **DONE - Phase 3**

**Phase 3 (Frontend UI) Complete! Phase 4 (Streaming) 87.5% Complete!** 🎉

**Phase 4 Status:**
- ✅ Real-time WebSocket streaming working
- ✅ Token-by-token agent responses
- ✅ Multi-worker fanout via Redis pub/sub
- ✅ Reconnection with sequence-based event replay
- ✅ Advisory locks prevent race conditions
- ✅ Redis Event Publisher (event_emitter.py)
- ✅ WebSocket Connection Manager (websocket_manager.py)
- ✅ AG-UI WebSocket Endpoint (api/routes/websocket.py)
- ✅ Agent Streaming Service (agent_runner.py with cumulative chunk handling)
- ✅ Event Replay Service (event_replay.py)
- ✅ Frontend WebSocket Hook (useRoomStream.ts with throttling)
- ✅ Frontend UI Integration (streaming indicators, single connection pattern)

**Ready for Production After:** Load testing completion (50+ concurrent users)

---

## 🎯 Success Mantra

> **"Events are immutable. Projections are transactional. Routes own transactions. Agents are stateless. Context is limited. Tests must pass."**

---

**Keep this card visible and refer to it often!**  

🚀 **Let's build this!** 🚀