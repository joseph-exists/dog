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
- [ ] `room_events` table created
- [ ] `rooms` table created
- [ ] `room_participants` table created
- [ ] `messages` projection created
- [ ] Migration applied
- [ ] Event emitter service implemented
- [ ] Room CRUD operations implemented
- [ ] Participant management APIs working
- [ ] Room API routes working
- [ ] Tests passing (>80% coverage)

### Agent Integration (Phase 2)
- [ ] `story_advisor.py` agent created
- [ ] Agent registry implemented
- [ ] Agent tools implemented (get_story_outline, etc.)
- [ ] AgentRunner service implemented
- [ ] ContextProvider service implemented (room-aware)
- [ ] Agents added as first-class room participants
- [ ] Room routes integrated with agent execution
- [ ] `participant.joined` events for agents working
- [ ] Agent tests passing
- [ ] Documentation updated

### Frontend UI (Phase 3)
- [ ] OpenAPI client regenerated
- [ ] Room UI component created
- [ ] ParticipantList component created
- [ ] MessageList/Message components created (with sender attribution)
- [ ] MessageInput component created
- [ ] useRoom hook implemented
- [ ] Room creation and joining flows implemented
- [ ] Room integrated into StoryEditor
- [ ] Mobile responsive
- [ ] UI tests passing


### Streaming (Phase 4)
- [ ] WebSocket endpoint created
- [ ] Redis pub/sub fanout working
- [ ] Agent streaming implemented
- [ ] useRoomStream hook created
- [ ] Frontend shows streaming tokens to all participants
- [ ] Reconnection with sequence-based replay working
- [ ] Load tested (50+ concurrent users)

---

## 🏗️ Architecture at a Glance


## 🏗️ Architecture at a Glance

```
User Message → REST/WebSocket → emit_event("message.user") 
                                    ↓
                            room_events (immutable log)
                                    ↓
                    Transactional Projection Updates
                                    ↓
                rooms, room_participants, messages (projections)
                                    ↓
                            AgentRunner.run_agent()
                                    ↓
                    StoryAdvisor Agent (as room participant)
                                    ↓
                            Tools (get_story_outline, etc.)
                                    ↓
                            emit_event("message.agent")
                                    ↓
                    Redis pub/sub → All connected participants
                                    ↓
                        Response → WebSocket/REST → All Users
```

---

## 📂 File Structure Quick Map

```
backend/
├── app/
│   ├── agents/
│   │   ├── quixote.py ✅ (existing)
│   │   ├── story_advisor.py 
│   │   └── agent_registry.py 
│   ├── services/
│   │   ├── event_emitter.py 
│   │   ├── room_manager.py 
│   │   ├── agent_runner.py 
│   │   └── context_provider.py  (room-aware)
│   ├── api/routes/
│   │   ├── rooms.py 
│   │   └── websocket.py  (Phase 4)
│   └── core/
│       └── redis.py 
frontend/
├── src/
│   ├── components/Room/ 
│   │   ├── RoomSidebar.tsx (or ChatRoom.tsx)
│   │   ├── ParticipantList.tsx
│   │   ├── MessageList.tsx
│   │   ├── Message.tsx (with sender attribution)
│   │   └── MessageInput.tsx
│   ├── hooks/
│   │   ├── useRoom.ts 
│   │   └── useRoomStream.ts  (Phase 4)
│   └── services/
│       └── roomService.ts 

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

### Transaction Pattern
```python
# Always emit events + update projections in same transaction
with session.begin():
    await emit_event(...)  # Writes to room_events
    # Projections (rooms, room_participants, messages) updated atomically
# Transaction commits - all succeed or all fail
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
- [ ] Event emitter creates events with correct per-room sequence
- [ ] Projection updates work correctly (rooms, room_participants, messages)
- [ ] Agent tools return expected formats
- [ ] Context provider loads story data and room metadata
- [ ] Participant management functions work correctly

### Integration Tests
- [ ] Can create room via API
- [ ] Can add participants (users and agents) to room
- [ ] Can send message and all participants receive updates
- [ ] Agent responses are visible to all room participants
- [ ] Events are written atomically with projections
- [ ] Multi-user authorization enforced correctly
- [ ] WebSocket connects and streams to multiple participants (Phase 4)

### Manual Tests
- [ ] Create/join room from story editor
- [ ] Invite another user and StoryAdvisor agent to room
- [ ] Send message, all participants see it in real-time
- [ ] Agent response visible to all participants
- [ ] Reload page, conversation and participants persist
- [ ] Agent mentions specific story details (room-aware context)
- [ ] Multiple users can collaborate simultaneously
- [ ] Participant list shows all active users and agents

---

## 🚨 Common Pitfalls to Avoid

| Pitfall | Solution |
|---------|----------|
| Updating events directly | Always emit new events instead |
| Forgetting transaction scope | Wrap emit_event + projection in `with session.begin()` |
| Loading too much context | Limit to 20 messages + story outline |
| Blocking operations in tools | Use `async`/`await` or `asyncio.to_thread()` |
| Missing authorization checks | Always call `check_session_access()` first |
| Not handling agent errors | Wrap in try/except, return friendly message |
| Not checking room membership | Always validate via room_participants before operations |
| Missing participant events | Emit participant.joined/left for users AND agents |
| Tight coupling to agent | Use AGENT_REGISTRY for decoupling |

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
# Check transaction scope
with session.begin():  # This is critical!
    await emit_event(...)
# Transaction commits here
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

- **MasterImplementationPlan Integration Plan is source of truth**
- **Agent Patterns:** `/backend/AGENT-PATTERNS.md`
- **Current Rules:** `/backend/RULES.md`
- **PydanticAI Docs:** https://ai.pydantic.dev
- **AG-UI Examples:** https://github.com/pydantic/pydantic-ai/tree/main/examples

---

## ✅ Definition of Done (Steel Thread)

The steel thread is complete when:
## ✅ Definition of Done (Steel Thread)

The steel thread is complete when:

1. ✅ Infrastructure is healthy (Redis + pgvector)
2. ✅ Can create room via API (optionally with initial agents)
3. ✅ Can add multiple users and agents as room participants
4. ✅ Multiple authors can send messages in same room
5. ✅ StoryAdvisor (as room participant) responds with story-aware answers
6. ✅ All room participants see all messages with correct attribution
7. ✅ Conversation and participants persist on page reload
8. ✅ Room UI works in story editor with participant list
9. ✅ All tests pass (unit + integration + multi-user scenarios)
10. ✅ No regressions in existing features
11. ✅ Authorization enforces room membership correctly
12. ✅ Documentation updated
13. ✅ Can demo multi-user end-to-end to stakeholder

---

## 🎯 Success Mantra

> **"Events are immutable. Projections are transactional. Agents are stateless. Context is limited. Tests must pass."**

---

**Keep this card visible and refer to it often!**  

🚀 **Let's build this!** 🚀