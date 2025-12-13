# Minimog Integration Plan: Multi-User Rooms Addendum

**Status:** CRITICAL ARCHITECTURE CLARIFICATION  
**Date:** December 11, 2025  
**Supersedes:** None - Extends MINIMOG-INTEGRATION-PLAN.md

---

## 🎯 Purpose of This Addendum

The original integration plan focused on a **single-user chat session** (user ↔ agent) as the steel thread. However, **Minimog's core value proposition is multi-user rooms where multiple humans and multiple AI agents collaborate together**. This addendum clarifies:

1. The architectural gap between "chat sessions" and "rooms"
2. How to add multi-user room management
3. How agents become room participants alongside users
4. Authorization model for room-based access
5. Required schema and API changes

---

## 🔍 The Gap: Sessions vs Rooms

### What We Have (Current Plan)
```
chat_sessions table:
- session_id (PK)
- user_id (owner)          ← Single user
- story_id (context)
- title

Events flow:
User → sends message → Agent responds → User sees it
```

**Problem:** Only one user can participate. Agent is external to the session.

### What Minimog Needs
```
rooms table:
- room_id (PK)
- title
- created_by
- is_group

room_participants table:
- room_id (PK)
- user_id or agent_id (PK) ← Multiple humans AND agents
- role (owner/member/agent)
- is_active

Events flow:
User A → sends message → ALL participants see it (Users B, C + Agent 1, Agent 2)
Agent 1 → responds → ALL participants see it
User B → replies → ALL see it
```

**Key Difference:** Rooms are **multi-party spaces** where humans and agents are all participants.

---

## 🏗️ Architectural Changes Required

### 1. Replace "chat_sessions" with "rooms"

**FROM (Steel Thread):**
```sql
CREATE TABLE chat_sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID NOT NULL,      -- Single owner
    story_id UUID,
    title VARCHAR(200),
    created_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ
);
```

**TO (Minimog Rooms):**
```sql
CREATE TABLE rooms (
    room_id UUID PRIMARY KEY,
    title VARCHAR(200),
    created_by UUID NOT NULL REFERENCES "user"(id),
    is_group BOOLEAN DEFAULT true,     -- Always true for multi-user
    room_type VARCHAR(50),              -- 'story_discussion', 'general', etc.
    story_id UUID REFERENCES story(id), -- Optional context
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_rooms_created_by ON rooms (created_by);
CREATE INDEX idx_rooms_last_activity ON rooms (last_activity DESC);
CREATE INDEX idx_rooms_story ON rooms (story_id) WHERE story_id IS NOT NULL;
```

### 2. Add room_participants Table (CRITICAL)

This is the **heart of multi-user architecture**:

```sql
CREATE TABLE room_participants (
    room_id UUID NOT NULL REFERENCES rooms(room_id) ON DELETE CASCADE,
    participant_id UUID NOT NULL,        -- user_id OR agent_id
    participant_type VARCHAR(20) NOT NULL, -- 'user' or 'agent'
    role VARCHAR(20) NOT NULL DEFAULT 'member', -- 'owner', 'member', 'agent'
    is_active BOOLEAN DEFAULT true,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    left_at TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',      -- Per-participant settings
    
    PRIMARY KEY (room_id, participant_id, participant_type)
);

CREATE INDEX idx_participants_user_rooms 
    ON room_participants (participant_id, participant_type, is_active) 
    WHERE is_active = true;

CREATE INDEX idx_participants_room 
    ON room_participants (room_id, is_active) 
    WHERE is_active = true;
```

**Why this matters:**
- Users and agents are **both participants** with different types
- Authorization: "Can user X read room Y?" → Check if X is active participant
- Discovery: "What rooms is user X in?" → Query this table
- Multi-agent: "What agents are in this room?" → Query where participant_type='agent'

### 3. Update Event Schema

**FROM (Steel Thread):**
```sql
CREATE TABLE chat_events (
    event_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,  -- Wrong scope
    ...
);
```

**TO (Minimog Rooms):**
```sql
CREATE TABLE room_events (
    event_id BIGSERIAL PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES rooms(room_id),  -- Correct scope
    room_sequence BIGINT NOT NULL,  -- Per-room ordering
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE (room_id, room_sequence)
);

CREATE INDEX idx_room_events_replay ON room_events (room_id, room_sequence);
```

### 4. Update Message Projection

**FROM (Steel Thread):**
```sql
CREATE TABLE chat_messages (
    message_id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    sender_id UUID,          -- Assumes user
    agent_name VARCHAR(50),  -- Separate field
    ...
);
```

**TO (Minimog Rooms):**
```sql
CREATE TABLE messages (
    message_id BIGSERIAL PRIMARY KEY,
    room_id UUID NOT NULL REFERENCES rooms(room_id),
    sender_id UUID,              -- participant_id (user OR agent)
    sender_type VARCHAR(20),     -- 'user' or 'agent'
    agent_name VARCHAR(50),      -- If sender_type='agent'
    content TEXT NOT NULL,
    button_options JSONB,        -- AG-UI interactive elements
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_messages_room_time ON messages (room_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages (sender_id, sender_type);
```

---

## 📊 Room Management Service (New)

Add **Service S2: Room Management** to the architecture:

```python
# app/services/room_manager.py
from uuid import UUID, uuid4
from sqlmodel import Session, select
from app.models import Room, RoomParticipant
from app.services.event_emitter import emit_event

class RoomManager:
    """Manages multi-user rooms and participants"""
    
    async def create_room(
        self,
        title: str,
        created_by: UUID,
        room_type: str = "general",
        story_id: UUID | None = None,
        initial_agents: list[str] | None = None,
        session: Session = None
    ) -> Room:
        """
        Create a new room with the creator as owner.
        Optionally add agents as participants.
        """
        room_id = uuid4()
        
        with session.begin():
            # 1. Emit room.created event
            await emit_event(
                room_id=room_id,
                event_type="room.created",
                payload={
                    "room_id": str(room_id),
                    "title": title,
                    "created_by": str(created_by),
                    "room_type": room_type,
                    "story_id": str(story_id) if story_id else None
                },
                session=session
            )
            
            # 2. Create room (projection)
            room = Room(
                room_id=room_id,
                title=title,
                created_by=created_by,
                room_type=room_type,
                story_id=story_id
            )
            session.add(room)
            
            # 3. Add creator as owner
            await self.add_participant(
                room_id=room_id,
                participant_id=created_by,
                participant_type="user",
                role="owner",
                session=session
            )
            
            # 4. Add initial agents if specified
            if initial_agents:
                for agent_name in initial_agents:
                    await self.add_agent_to_room(
                        room_id=room_id,
                        agent_name=agent_name,
                        session=session
                    )
        
        return room
    
    async def add_participant(
        self,
        room_id: UUID,
        participant_id: UUID,
        participant_type: str,  # 'user' or 'agent'
        role: str = "member",
        invited_by: UUID | None = None,
        session: Session = None
    ) -> RoomParticipant:
        """Add a user or agent to a room"""
        
        with session.begin():
            # 1. Emit participant.joined event
            await emit_event(
                room_id=room_id,
                event_type="participant.joined",
                payload={
                    "room_id": str(room_id),
                    "participant_id": str(participant_id),
                    "participant_type": participant_type,
                    "role": role,
                    "invited_by": str(invited_by) if invited_by else None
                },
                session=session
            )
            
            # 2. Create participant record (projection)
            participant = RoomParticipant(
                room_id=room_id,
                participant_id=participant_id,
                participant_type=participant_type,
                role=role,
                is_active=True
            )
            session.add(participant)
        
        return participant
    
    async def add_agent_to_room(
        self,
        room_id: UUID,
        agent_name: str,
        session: Session = None
    ) -> RoomParticipant:
        """
        Add an AI agent as a participant in the room.
        Agents are identified by their name (e.g., 'story_advisor').
        """
        # Generate stable UUID for agent based on name
        agent_id = uuid5(NAMESPACE_AGENTS, agent_name)
        
        return await self.add_participant(
            room_id=room_id,
            participant_id=agent_id,
            participant_type="agent",
            role="agent",
            session=session
        )
    
    async def get_room_participants(
        self,
        room_id: UUID,
        active_only: bool = True,
        session: Session = None
    ) -> list[RoomParticipant]:
        """Get all participants in a room"""
        query = select(RoomParticipant).where(
            RoomParticipant.room_id == room_id
        )
        
        if active_only:
            query = query.where(RoomParticipant.is_active == True)
        
        return session.exec(query).all()
    
    async def check_room_access(
        self,
        room_id: UUID,
        user_id: UUID,
        session: Session = None
    ) -> bool:
        """Check if user is an active participant in room"""
        result = session.exec(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.participant_id == user_id)
            .where(RoomParticipant.participant_type == "user")
            .where(RoomParticipant.is_active == True)
        ).first()
        
        return result is not None
    
    async def get_user_rooms(
        self,
        user_id: UUID,
        session: Session = None
    ) -> list[Room]:
        """Get all rooms where user is an active participant"""
        # Join rooms with participants
        query = select(Room).join(
            RoomParticipant,
            Room.room_id == RoomParticipant.room_id
        ).where(
            RoomParticipant.participant_id == user_id
        ).where(
            RoomParticipant.participant_type == "user"
        ).where(
            RoomParticipant.is_active == True
        ).order_by(
            Room.last_activity.desc()
        )
        
        return session.exec(query).all()
```

---

## 🔌 Updated API Routes

### Room Management Endpoints

```python
# app/api/routes/rooms.py
from fastapi import APIRouter, Depends
from uuid import UUID
from app.api.deps import CurrentUser, SessionDep
from app.services.room_manager import RoomManager
from app.models import (
    RoomCreate, RoomPublic, RoomsPublic,
    ParticipantCreate, ParticipantPublic
)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("/", response_model=RoomPublic)
async def create_room(
    room: RoomCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> RoomPublic:
    """
    Create a new multi-user room.
    Creator becomes the owner automatically.
    """
    room_manager = RoomManager()
    
    new_room = await room_manager.create_room(
        title=room.title,
        created_by=current_user.id,
        room_type=room.room_type,
        story_id=room.story_id,
        initial_agents=room.initial_agents,  # e.g., ['story_advisor']
        session=session
    )
    
    return RoomPublic.model_validate(new_room)

@router.get("/", response_model=RoomsPublic)
async def list_my_rooms(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> RoomsPublic:
    """
    Get all rooms where current user is a participant.
    """
    room_manager = RoomManager()
    
    rooms = await room_manager.get_user_rooms(
        user_id=current_user.id,
        session=session
    )
    
    # Apply pagination
    paginated = rooms[skip : skip + limit]
    
    return RoomsPublic(
        data=[RoomPublic.model_validate(r) for r in paginated],
        count=len(rooms)
    )

@router.get("/{room_id}", response_model=RoomPublic)
async def get_room(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> RoomPublic:
    """Get room details (if user is participant)"""
    room_manager = RoomManager()
    
    # Authorization check
    if not await room_manager.check_room_access(room_id, current_user.id, session):
        raise HTTPException(status_code=403, detail="Not a room participant")
    
    room = session.get(Room, room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return RoomPublic.model_validate(room)

@router.post("/{room_id}/participants", response_model=ParticipantPublic)
async def invite_participant(
    room_id: UUID,
    participant: ParticipantCreate,
    session: SessionDep,
    current_user: CurrentUser,
) -> ParticipantPublic:
    """
    Invite a user or add an agent to the room.
    Only room owners can add participants.
    """
    room_manager = RoomManager()
    
    # Check if current user is owner
    current_participant = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.participant_id == current_user.id)
        .where(RoomParticipant.participant_type == "user")
    ).first()
    
    if not current_participant or current_participant.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can invite")
    
    # Add participant
    if participant.participant_type == "agent":
        new_participant = await room_manager.add_agent_to_room(
            room_id=room_id,
            agent_name=participant.agent_name,
            session=session
        )
    else:
        new_participant = await room_manager.add_participant(
            room_id=room_id,
            participant_id=participant.user_id,
            participant_type="user",
            role="member",
            invited_by=current_user.id,
            session=session
        )
    
    return ParticipantPublic.model_validate(new_participant)

@router.get("/{room_id}/participants", response_model=list[ParticipantPublic])
async def list_participants(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> list[ParticipantPublic]:
    """List all participants in a room"""
    room_manager = RoomManager()
    
    # Check access
    if not await room_manager.check_room_access(room_id, current_user.id, session):
        raise HTTPException(status_code=403, detail="Not a room participant")
    
    participants = await room_manager.get_room_participants(
        room_id=room_id,
        session=session
    )
    
    return [ParticipantPublic.model_validate(p) for p in participants]

@router.delete("/{room_id}/participants/me")
async def leave_room(
    room_id: UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> dict:
    """Leave a room (set participant to inactive)"""
    room_manager = RoomManager()
    
    with session.begin():
        await emit_event(
            room_id=room_id,
            event_type="participant.left",
            payload={
                "room_id": str(room_id),
                "participant_id": str(current_user.id),
                "participant_type": "user"
            },
            session=session
        )
        
        # Update participant
        session.exec(
            update(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.participant_id == current_user.id)
            .values(is_active=False, left_at=datetime.now())
        )
    
    return {"message": "Left room successfully"}
```

---

## 🔄 Updated Event Flow (Multi-User)

### Single Message Flow Across Multiple Participants

```
1. User A in Room X sends message
   ↓
2. POST /rooms/{room_id}/messages
   ↓
3. Check: Is User A participant in Room X? ✓
   ↓
4. Emit event: room.events
   {
     room_id: X,
     room_sequence: 42,
     event_type: "message.user",
     payload: {
       sender_id: User A,
       content: "How should I end this chapter?"
     }
   }
   ↓
5. Update projection: messages table
   ↓
6. Publish to Redis: channel "room:X"
   ↓
7. WebSocket broadcasts to ALL participants:
   - User A (sees their own message)
   - User B (sees User A's message)
   - User C (sees User A's message)
   - Agent 1 (story_advisor) - triggers agent response
   - Agent 2 (character_expert) - passive observer
   ↓
8. Agent 1 generates response
   ↓
9. Emit event: room.events
   {
     room_id: X,
     room_sequence: 43,
     event_type: "message.agent",
     payload: {
       sender_id: Agent 1 UUID,
       agent_name: "story_advisor",
       content: "Consider these three endings..."
     }
   }
   ↓
10. Broadcast to ALL participants again
    - Everyone sees agent's response
```

**Key Point:** ONE message event → MULTIPLE recipients see it

---

## 🎯 Updated Agent Execution

### Agents as Room Participants

```python
# app/services/agent_runner.py (UPDATED)
from uuid import UUID, uuid5, NAMESPACE_DNS

# Stable namespace for agent UUIDs
NAMESPACE_AGENTS = uuid5(NAMESPACE_DNS, "tinyfoot.agents")

class AgentRunner:
    async def run_agent_in_room(
        self,
        room_id: UUID,
        user_message: str,
        user_id: UUID,
        agent_name: str = "story_advisor",
        session: Session = None
    ) -> str:
        """
        Execute agent as a room participant.
        Agent's response is visible to ALL room participants.
        """
        # Generate stable agent UUID
        agent_id = uuid5(NAMESPACE_AGENTS, agent_name)
        
        # Build context with room awareness
        ctx = await self.build_room_context(
            room_id=room_id,
            agent_name=agent_name,
            session=session
        )
        
        # Run agent
        agent = AGENT_REGISTRY[agent_name]["agent"]
        result = await agent.run(user_message, deps=ctx)
        
        # Emit message as agent participant
        with session.begin():
            await emit_event(
                room_id=room_id,
                event_type="message.agent",
                payload={
                    "sender_id": str(agent_id),  # Agent as sender
                    "agent_name": agent_name,
                    "content": result.data,
                    "model": agent.model_name
                },
                session=session
            )
        
        return result.data
    
    async def build_room_context(
        self,
        room_id: UUID,
        agent_name: str,
        session: Session
    ) -> RoomContext:
        """Build context with room awareness"""
        
        # Get room details
        room = session.get(Room, room_id)
        
        # Get all participants (users + agents)
        participants = session.exec(
            select(RoomParticipant)
            .where(RoomParticipant.room_id == room_id)
            .where(RoomParticipant.is_active == True)
        ).all()
        
        # Get recent messages from ALL participants
        messages = session.exec(
            select(Message)
            .where(Message.room_id == room_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        ).all()
        
        # Get story context if available
        story_data = None
        if room.story_id:
            story = session.get(Story, room.story_id)
            story_data = format_story_outline(story)
        
        return RoomContext(
            room_id=room_id,
            room_title=room.title,
            agent_name=agent_name,
            story_data=story_data,
            participants=[
                {
                    "type": p.participant_type,
                    "id": str(p.participant_id),
                    "role": p.role,
                    "agent_name": p.agent_name if p.participant_type == "agent" else None
                }
                for p in participants
            ],
            message_history=[
                {
                    "role": "user" if m.sender_type == "user" else "assistant",
                    "content": m.content,
                    "sender": m.agent_name if m.sender_type == "agent" else "user"
                }
                for m in reversed(messages)
            ]
        )
```

---

## 🔐 Authorization Model

### Room-Based Access Control

```python
# app/api/deps.py (ADD)
from app.services.room_manager import RoomManager

async def check_room_access(
    room_id: UUID,
    current_user: CurrentUser,
    session: SessionDep
) -> None:
    """
    Dependency to check room access.
    Raises 403 if user is not an active participant.
    """
    room_manager = RoomManager()
    
    if not await room_manager.check_room_access(room_id, current_user.id, session):
        raise HTTPException(
            status_code=403,
            detail="You must be a room participant to access this resource"
        )

# Usage in routes:
@router.get("/rooms/{room_id}/messages")
async def get_messages(
    room_id: UUID,
    _: None = Depends(check_room_access),  # Authorization check
    session: SessionDep,
) -> list[MessagePublic]:
    # User is authorized if we get here
    messages = session.exec(
        select(Message).where(Message.room_id == room_id)
    ).all()
    return messages
```

---

## 📝 Updated Models (Pydantic)

```python
# app/models.py (ADD)

class RoomBase(SQLModel):
    title: str = Field(min_length=1, max_length=200)
    room_type: str = Field(default="general", max_length=50)
    story_id: UUID | None = None

class RoomCreate(RoomBase):
    initial_agents: list[str] | None = None  # e.g., ['story_advisor']

class RoomUpdate(SQLModel):
    title: str | None = None
    story_id: UUID | None = None

class Room(RoomBase, table=True):
    room_id: UUID = Field(default_factory=uuid4, primary_key=True)
    created_by: UUID = Field(foreign_key="user.id", nullable=False)
    is_group: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict, sa_column=Column(JSON))

class RoomPublic(RoomBase):
    room_id: UUID
    created_by: UUID
    created_at: datetime
    last_activity: datetime
    participant_count: int | None = None  # Computed field

class RoomsPublic(SQLModel):
    data: list[RoomPublic]
    count: int

class RoomParticipantBase(SQLModel):
    room_id: UUID
    participant_id: UUID
    participant_type: str  # 'user' or 'agent'
    role: str = Field(default="member")

class ParticipantCreate(SQLModel):
    participant_type: str  # 'user' or 'agent'
    user_id: UUID | None = None  # If type='user'
    agent_name: str | None = None  # If type='agent'

class RoomParticipant(RoomParticipantBase, table=True):
    __tablename__ = "room_participants"
    
    room_id: UUID = Field(foreign_key="rooms.room_id", primary_key=True)
    participant_id: UUID = Field(primary_key=True)
    participant_type: str = Field(primary_key=True)
    role: str
    is_active: bool = Field(default=True)
    joined_at: datetime = Field(default_factory=datetime.now)
    left_at: datetime | None = None
    preferences: dict = Field(default_factory=dict, sa_column=Column(JSON))

class ParticipantPublic(RoomParticipantBase):
    is_active: bool
    joined_at: datetime
    # Enriched with user/agent details
    display_name: str | None = None

class RoomContext(BaseModel):
    """Context for agents running in multi-user rooms"""
    room_id: UUID
    room_title: str
    agent_name: str
    story_data: dict | None
    participants: list[dict]  # All room participants
    message_history: list[dict]  # Messages from all participants
```

---

## 🎬 Updated Phase Plan

### Phase 1: Event Sourcing + Room Management (4-5 days)

**NEW SCOPE:**
- ✅ `rooms` table (not chat_sessions)
- ✅ `room_participants` table (CRITICAL)
- ✅ `room_events` table
- ✅ `messages` projection
- ✅ RoomManager service
- ✅ Room API routes
- ✅ Participant management APIs

**Migration Changes:**
```python
# Previous: chat_sessions
# New: rooms + room_participants



### Phase 2: Multi-User Agent Integration (5-6 days)

**NEW SCOPE:**
- ✅ Agents registered as room participants
- ✅ Agent responses broadcast to all participants
- ✅ Room-aware context building
- ✅ Multiple agents can be in same room

**Key Changes:**
```python
# Before: Agent talks to single user
agent.run(message, deps=ChatContext(user_id=X))

# After: Agent participates in room
agent.run(message, deps=RoomContext(
    room_id=Y,
    participants=[user_A, user_B, agent_1, agent_2],
    message_history=all_room_messages
))
```

### Phase 3: Frontend Multi-User UI (4-5 days)

**NEW SCOPE:**
- ✅ Room list view (all user's rooms)
- ✅ Room creation modal
- ✅ Participant list sidebar
- ✅ Message attribution (show sender name/avatar)
- ✅ Invite users/agents UI

**Component Changes:**
```tsx
// Before: ChatSidebar (single session)
<ChatSidebar sessionId={sessionId} />

// After: RoomChat (multi-participant)
<RoomChat roomId={roomId}>
  <ParticipantList participants={participants} />
  <MessageList>
    {messages.map(msg => (
      <Message 
        sender={msg.sender_type === 'user' ? users[msg.sender_id] : msg.agent_name}
        content={msg.content}
      />
    ))}
  </MessageList>
</RoomChat>
```

---

## 🔄 Event Types Extended

Add these event types to support rooms:

| Event Type | When | Payload |
|------------|------|---------|
| `room.created` | Room created | `{room_id, title, created_by, room_type}` |
| `room.updated` | Room settings changed | `{room_id, changes}` |
| `participant.joined` | User/agent joins | `{room_id, participant_id, participant_type, role}` |
| `participant.left` | User/agent leaves | `{room_id, participant_id, participant_type}` |
| `participant.role_changed` | Role updated | `{room_id, participant_id, old_role, new_role}` |
| `message.user` | User sends message | `{sender_id, content}` |
| `message.agent` | Agent responds | `{sender_id, agent_name, content}` |
| `agent.added` | Agent added to room | `{agent_name, added_by}` |
| `agent.removed` | Agent removed | `{agent_name, removed_by}` |

---

## 🎯 Steel Thread Updated

**NEW Steel Thread:**

> **"Multiple authors can join a shared room, invite the StoryAdvisor agent, and collaborate on story development. All participants see each message in real-time. The agent's responses are contextually aware of the entire conversation."**

**Proves:**
- ✅ Multi-user rooms (not single-user sessions)
- ✅ Agent as room participant
- ✅ Room-level authorization
- ✅ Multi-party event broadcasting
- ✅ Participant management

---

## 📋 Migration Checklist

### From Current Plan to Rooms

- [ ] **Schema Changes**
  - [ ] Rename `chat_sessions` → `rooms`
  - [ ] Add `room_participants` table
  - [ ] Update `chat_events` → `room_events` with `room_id`
  - [ ] Update `chat_messages` → `messages` with sender attribution

- [ ] **Service Changes**
  - [ ] Create `RoomManager` service
  - [ ] Update `AgentRunner` for room context
  - [ ] Update `ContextProvider` for room awareness
  - [ ] Update `EventEmitter` to use room_id

- [ ] **API Changes**
  - [ ] Add room management routes
  - [ ] Add participant management routes
  - [ ] Update message routes to check room access
  - [ ] Update authorization to use room_participants

- [ ] **Frontend Changes**
  - [ ] Create RoomList component
  - [ ] Update ChatSidebar → RoomChat
  - [ ] Add ParticipantList component
  - [ ] Show message sender attribution
  - [ ] Add room creation/invitation UI

- [ ] **Testing Changes**
  - [ ] Test multi-user scenarios
  - [ ] Test agent as participant
  - [ ] Test room authorization
  - [ ] Test participant management
  - [ ] Test multi-agent rooms

---

## 🚨 Critical Notes

### 1. This is NOT Optional
Multi-user rooms are **fundamental to Minimog's value proposition**. Without this, we just have a single-user chatbot, not a collaborative workspace.

### 2. Complexity Increase
Adding rooms increases complexity:
- Authorization becomes room-scoped
- Events broadcast to multiple participants
- Need participant management UI
- Need to handle concurrent users

**BUT:** This complexity is core to the product vision.

### 3. Agent as Participant Pattern
Treating agents as room participants (not external services) is a key architectural insight:
- Agents have stable UUIDs
- Agents appear in participant lists
- Agents can be added/removed like users
- Agent messages flow through same event log

### 4. Backend First
Implement rooms backend completely before frontend. The frontend can initially show rooms as if they're single-user sessions, then add multi-user UI later.

---

## 📖 Updated Documentation Locations

Add sections to existing docs:

**MINIMOG-INTEGRATION-PLAN.md:**
- Update Phase 1 to include room management
- Update data model diagrams to show participants
- Add room authorization patterns

**AGENT-PATTERNS.md:**
- Add "Agents as Room Participants" section
- Update context building for room awareness
- Add multi-agent coordination patterns

**STEEL-THREAD-QUICK-REF.md:**
- Update "Key Patterns" with room authorization
- Add room management commands
- Update testing checklist for multi-user

---

## ✅ Validation Questions

Before proceeding, confirm:

1. **Do we want 1:1 rooms?** Or only multi-user rooms?
   - **Recommendation:** Support both, use `is_group` flag

2. **Can rooms exist without agents?** Or is an agent required?
   - **Recommendation:** Rooms can be human-only initially, agents added later

3. **How many agents per room?** Unlimited or limited?
   - **Recommendation:** Start with 1-3 agents per room

4. **Can users create rooms?** Or only admins?
   - **Recommendation:** Any authenticated user can create rooms

5. **Room discoverability?** Can users browse/join public rooms?
   - **Recommendation:** Phase 2 feature - start with invite-only

---

## 🎯 Summary: What Changed

| Aspect | Original Plan | Updated (Rooms) |
|--------|---------------|-----------------|
| **Core Entity** | chat_sessions (single user) | rooms (multi-user) |
| **Participants** | Implicit (owner only) | Explicit (room_participants table) |
| **Agent Relationship** | External service | Room participant |
| **Authorization** | User owns session | User is room participant |
| **Event Scope** | session_id | room_id |
| **Message Visibility** | User + their agent | All room participants |
| **UI Pattern** | Chat sidebar (1:1) | Room view (N:N) |

---

## 🚀 Next Action

**Decision Required:** Do we adopt the room-based architecture?

**If YES:**
1. Update Phase 1 migration to include rooms + room_participants
2. Create RoomManager service first
3. Update steel thread to prove multi-user capability
