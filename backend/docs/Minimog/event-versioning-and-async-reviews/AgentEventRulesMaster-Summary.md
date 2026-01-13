# AgentEventRulesMaster.md 
**Created:** December 12, 2025, 10:34 AM PST 
**Last Update:** January 10, 2026
**Purpose:** document agent and event sourcing patterns 
**Status:** in refinement

---

## TODO: add file locations and ensure correctness
## add to main doc-source
## cross-reference


## Key Concepts

### 1. Architecture: Room Based


**Multi-User Rooms:**
- `room_events` table with `room_id` + `room_sequence`
- `rooms`, `room_participants`, and `messages` projections
- Explicit multi-user participant management
- `RoomContext(room_id, user_id, participants, room_metadata, story_id)`

### 2. Agent Model: Responder → Participant


**Implemented:**
- Agents are first-class room participants in `room_participants` table
- participant_type field: 'user' or 'agent'
- Validation required before agent execution
- Agents visible to all room participants

### 3. Event Types

**implemented:**
- room.created, room.updated (lifecycle)
- participant.joined, participant.left, participant.role_changed (membership)
- message.user, message.agent (content)
- agent.handoff, tool.start, tool.end (observability)

### 4. Authorization: Ownership → Membership


**Master:**
```python
check_room_membership(room_id, user_id)
# Validates user is active participant via room_participants table
```

### 5. Multi-user context provider


**Master:**
```python
build_room_context(room_id, user_id)

```


## Code Examples

### Agent Context Definition


**Master:**
```python
class RoomContext(BaseModel):
    room_id: UUID
    user_id: UUID
    participants: list[dict]  # Multi-user awareness
    room_metadata: dict       # Room context
    story_id: UUID | None = None
```

### Event Emission



### Projection Updates



### Agent Execution

**Current:**
```python
async def run_agent(room_id, user_message, user_id, agent_name):
    # Validate agent is room participant
    agent_participant = session.exec(
        select(RoomParticipant)
        .where(RoomParticipant.room_id == room_id)
        .where(RoomParticipant.participant_id == agent_name)
        .where(RoomParticipant.participant_type == "agent")
        .where(RoomParticipant.active == True)
    ).first()

    if not agent_participant:
        raise ValueError(f"Agent not a participant")

    ctx = await build_room_context(room_id, user_id)
    result = await agent.run(user_message, deps=ctx)
```



## Testing Patterns

###
```python
# Multi-user awareness test
ctx = RoomContext(
    room_id=uuid4(),
    user_id=uuid4(),
    participants=[
        {"participant_id": str(uuid4()), "participant_type": "user", "role": "owner"},
        {"participant_id": str(uuid4()), "participant_type": "user", "role": "member"},
        {"participant_id": "story_advisor", "participant_type": "agent", "role": "member"}
    ],
    room_metadata={"created_at": "2025-12-12T10:00:00Z"},
    story_id=None
)

# Test multi-user scenario
result = await story_advisor.run("Who else is in this room?", deps=ctx)
# Agent should acknowledge multiple participants
```

---

### 1. Multi-User Collaboration Principles 
- default participant equality between users and agents (from the perspective of these modules)
- Authorization model based on room membership
- Event visibility to all participants (potential, dependent on toggles and admin controls)
- Transparency for collaborative development

### 2. Enhanced Error Handling
- Room-scoped logging with participant count
- Error events visible to all room participants (by default)
- Multi-user context in error messages

### 3. Enhanced Monitoring
- Room participant metrics
- Multi-user aware logging
- Structured logging with participant context


**This document should be used as:**
1. ✅ Primary reference for agent development patterns
2. ✅ Source of truth for event sourcing implementation
3. ✅ Guide for room-based architecture
4. ✅ Template for migration creation
5. ✅ Reference for testing patterns


## For Review and doc transformation

### Implementation Checklist
- [ ] Create room_events, rooms, room_participants, messages tables per migration template
- [ ] Implement emit_event() with room_id parameter
- [ ] Implement update_projection() with 3-table logic
- [ ] Create RoomContext class with participants field
- [ ] Implement check_room_membership() authorization
- [ ] Update agent registry with participant_type
- [ ] Implement build_room_context() with participants
- [ ] Create AgentRunner with participant validation
- [ ] Write tests using multi-user scenarios

### For Code Reviews

**Rules for context types, event emission, agent execution and rooms:**
- [ ] All context types use RoomContext
- [ ] All event emissions use room_id parameter
- [ ] Agent execution validates participant membership
- [ ] Projections update all 3 tables (rooms, room_participants, messages)
- [ ] Authorization checks room_membership
- [ ] Event types include participant lifecycle events
