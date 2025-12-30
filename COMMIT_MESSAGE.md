feat(phase-4): Complete WebSocket streaming implementation with critical fixes

## Overview
Implements Phase 4 real-time streaming (7/8 deliverables complete). Fixes critical Redis
connection, WebSocket architecture, and PydanticAI streaming bugs.

## Critical Fixes

### 1. Redis Infrastructure (BLOCKING)
- **Fix**: Complete rewrite of `app/core/redis.py` with connection pooling
- **Problem**: Missing `get_redis()` function, syntax errors, hardcoded localhost
- **Impact**: Redis integration was completely broken, Phase 4 couldn't function
- Files: `redis.py`, `config.py`, `docker-compose.yml`

### 2. Docker Networking (BLOCKING)
- **Fix**: Override REDIS_HOST=redis in docker-compose for backend/prestart
- **Problem**: Containers using localhost instead of Redis service name
- **Impact**: "Connection refused" errors, Redis unreachable from containers

### 3. PydanticAI Cumulative Chunks (DATA CORRUPTION)
- **Fix**: Extract deltas from cumulative `stream_text()` chunks
- **Problem**: `stream_text()` yields full message, not just new tokens
- **Impact**: Final messages corrupted: "HelloHelloHello worldHello world!"
- File: `agent_runner.py` (run_agent_for_room_streaming)

### 4. WebSocket Hook Duplication (UX)
- **Fix**: Single useRoomStream at parent, props to children
- **Problem**: MessageInput + MessageList each created WebSocket connection
- **Impact**: Duplicate streaming messages (2-4x), wasted connections
- Files: `room.$roomId.tsx`, `MessageInput.tsx`, `MessageList.tsx`

### 5. React Render Spam (PERFORMANCE)
- **Fix**: 50ms throttled token buffering
- **Problem**: setState on every token (100+ renders/sec) froze browser
- **Impact**: Laggy UI during streaming, high CPU usage
- File: `useRoomStream.ts`

## Implementation Status

### ✅ Complete (7/8)
1. Redis Event Publisher - Event/token pub/sub with advisory locks
2. WebSocket Connection Manager - Per-worker subscriptions, fanout
3. AG-UI Protocol Handler - JWT auth, handshake, replay
4. Agent Streaming Service - Token-by-token streaming with context
5. Event Replay Service - Sequence-based reconnection
6. Frontend WebSocket Hook - Throttled buffering, single connection
7. Frontend UI Integration - Streaming indicators, REST fallback

### ⚠️ Pending (1/8)
8. Load Testing - Locust tests for 50+ concurrent users

## Files Changed

**Backend:**
- `app/core/redis.py` - Complete rewrite with ConnectionPool
- `app/core/config.py` - Added REDIS_HOST/PORT settings
- `app/services/event_emitter.py` - Added logging, imports, advisory locks
- `app/services/agent_runner.py` - Fixed cumulative chunk handling
- `app/services/websocket_manager.py` - NEW (Phase 4)
- `app/services/event_replay.py` - NEW (Phase 4)
- `app/api/routes/websocket.py` - NEW (Phase 4)

**Frontend:**
- `src/hooks/useRoomStream.ts` - Token buffering, throttling
- `src/routes/_layout/room.$roomId.tsx` - Single WebSocket connection
- `src/components/Rooms/MessageInput.tsx` - Accept WebSocket props
- `src/components/Rooms/MessageList.tsx` - Accept streaming message prop

**Infrastructure:**
- `docker-compose.yml` - REDIS_HOST=redis for Docker networking

**Documentation:**
- `docs/Minimog/Phase4/Phase-4-Plan.md` - Updated status (7/8 complete)
- `docs/Redis-Pattern-Review.md` - NEW (architectural analysis)
- `docs/Minimog/Phase4/Phase-4-Implementation-Summary.md` - NEW (this summary)

## Testing
- ✅ Redis connection from backend container
- ✅ Events published with correct channel names
- ✅ WebSocket connections established
- ✅ Token streaming without duplicates
- ✅ Final messages saved correctly
- ✅ REST API fallback works
- ❌ Load testing (pending)

## Architecture Compliance
- ✅ AP1: Event Sourcing - Redis pub after transaction flush
- ✅ AP2: PydanticAI - stream_text() with cumulative chunk handling
- ✅ AP3: CQRS - Transactional projections maintained
- ✅ AP4: AG-UI Protocol - WebSocket JSON-RPC format
- ✅ AP5: Stateless Multi-Worker - Redis pub/sub fanout
- ✅ AC3.1: Advisory Locks - pg_advisory_xact_lock() for sequences

## Breaking Changes
None - Phase 4 is additive (WebSocket optional, REST API still works)

## Migration Notes
No database migrations required. Restart containers to pick up REDIS_HOST env var.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
