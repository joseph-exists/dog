# CYOA Test Reference Card

Quick reference for fixing CYOA (Choose Your Own Adventure) story system tests.

## 📋 Table of Contents
- [Core Architecture](#core-architecture)
- [API Endpoints](#api-endpoints)
- [Test Patterns](#test-patterns)
- [Common Issues](#common-issues)
- [Debugging](#debugging)

---

## Core Architecture

### Entity Hierarchy
```
User
  └─→ UserPersona (user's instance of a Persona)
       └─→ UserStoryProgress (playthrough of a Story)
            └─→ UserNodeChoice (player's choice history - event sourcing)

Story (content)
  └─→ StoryNode (version 1, 2, etc.)
       └─→ NodeChoice (available choices between nodes)
```

### Key Concepts

**1. Persona System**
- `Persona` = Template/archetype (shared)
- `UserPersona` = User's instance of a Persona
- **Tests must create BOTH**: First Persona, then UserPersona

**2. Event Sourcing Model**
- `UserNodeChoice` records form a **tree** (not linear)
- Each choice has `parent_choice_id` pointing to previous choice
- `head_choice_id` = current position (None = story start)
- `head_version` = optimistic concurrency counter

**3. State Replay**
- `story_state` stored in `UserStoryProgress` (denormalized cache)
- Can be reconstructed by replaying choices from root → head
- Timeline navigation (undo/jump) uses replay

---

## API Endpoints

### Story Progress Management

```python
# 1. Create progress (start story)
POST /api/v1/user-personas/{user_persona_id}/stories/{story_id}
→ Returns: UserStoryProgressPublic (head_choice_id=None, head_version=0)

# 2. Get current node + available choices
GET /api/v1/user-personas/{user_persona_id}/stories/{story_id}/current-node
→ Returns: {
    "node": StoryNodePublic,
    "available_choices": [NodeChoicePublic],  # ← Use this for choice IDs
    "story_state": {...}
}

# 3. Make a choice
POST /api/v1/user-personas/{user_persona_id}/stories/{story_id}/choices/{choice_id}
→ Updates head_choice_id, increments head_version
→ Creates UserNodeChoice with parent_choice_id
```

### Timeline Navigation (Phase 3)

```python
# 4. Undo last choice
POST /api/v1/user-personas/{user_persona_id}/stories/{story_id}/undo
→ Moves head to parent, replays state

# 5. Jump to ancestor
POST /api/v1/user-personas/{user_persona_id}/stories/{story_id}/jump
Body: {
    "choice_id": "uuid-of-ancestor",  # None = jump to start
    "expected_head_version": 5  # Optimistic locking
}
→ Validates target is ancestor (prevents forward jumps)

# 6. Get timeline (breadcrumb trail)
GET /api/v1/user-personas/{user_persona_id}/stories/{story_id}/timeline
→ Returns: {
    "events": [TimelineEvent],  # root → head only (no abandoned branches)
    "head_version": 5
}
```

---

## Test Patterns

### Pattern 1: Making Choices

**OLD (BROKEN)**:
```python
# ❌ WRONG - This accesses the wrong field
choice_id = response.json()["choices"][0]["id"]
```

**NEW (CORRECT)**:
```python
# ✅ CORRECT - Use available_choices from current-node endpoint
response = client.get(
    f"/api/v1/user-personas/{persona_id}/stories/{story_id}/current-node",
    headers=headers,
)
choice_id = response.json()["available_choices"][0]["id"]  # ← Correct field

# Then make the choice
client.post(
    f"/api/v1/user-personas/{persona_id}/stories/{story_id}/choices/{choice_id}",
    headers=headers,
)
```

### Pattern 2: Testing Timeline Navigation

```python
# Make several choices to build a chain
choice_ids = []
for i in range(4):
    resp = client.get(f".../current-node", headers=headers)
    choice_id = resp.json()["available_choices"][0]["id"]

    resp = client.post(f".../choices/{choice_id}", headers=headers)
    # Save the head_choice_id (UUID of UserNodeChoice created)
    choice_ids.append(resp.json()["head_choice_id"])

# Get current head_version for jump
db.refresh(progress)
head_version = progress.head_version

# Jump to second choice
client.post(
    f".../jump",
    headers=headers,
    json={
        "choice_id": choice_ids[1],  # Target ancestor
        "expected_head_version": head_version,
    },
)
```

### Pattern 3: Verifying Tree Structure

```python
# After undo + new choice, verify abandoned branch exists
all_choices = db.exec(
    select(UserNodeChoice).where(
        UserNodeChoice.progress_id == progress.id
    )
).all()

# Find root (parent_choice_id = None)
root = next(c for c in all_choices if c.parent_choice_id is None)

# Verify children
children = [c for c in all_choices if c.parent_choice_id == root.id]
assert len(children) == 2  # Original + new choice after undo
```

---

## Common Issues

### Issue 1: Missing Persona vs UserPersona

**Symptom**: 404 "User persona not found" or persona creation fails

**Cause**: Tests need UserPersona (user's instance), not just Persona

**Fix**:
```python
# Create Persona first
persona = Persona(name="Test", description="Test")
db.add(persona)
db.commit()

# Then create UserPersona linking user to persona
user_persona = UserPersona(
    user_id=user.id,
    persona_id=persona.id,  # ← Links to Persona
)
db.add(user_persona)
db.commit()

# Use user_persona.id in story API calls
```

### Issue 2: Wrong Choice ID Source

**Symptom**: 404 "Choice not found" when making choices

**Cause**: Using wrong response field for choice IDs

**Fix**: Always get choice IDs from `current-node` endpoint's `available_choices` list

### Issue 3: Boolean Query Issues

**Symptom**: "No start node found" errors

**Cause**: Using `is True` instead of `== True` in SQLAlchemy queries

**Fix**:
```python
# ✅ CORRECT for SQLAlchemy
.where(StoryNode.is_start_node == True)  # noqa: E712

# ❌ WRONG (Python identity check doesn't work in SQL)
.where(StoryNode.is_start_node is True)
```

### Issue 4: Stale Progress Object

**Symptom**: Tests fail with old head_version or head_choice_id

**Cause**: Not refreshing DB objects after API calls

**Fix**:
```python
# After making choices via API
db.refresh(progress)  # ← Always refresh before assertions
assert progress.head_version == expected_version
```

---

## Debugging

### Check Progress State
```python
# In test, print current state
db.refresh(progress)
print(f"head_choice_id: {progress.head_choice_id}")
print(f"head_version: {progress.head_version}")
print(f"story_state: {progress.story_state}")
```

### Verify Choice Chain
```python
from app import crud

# Get ancestor chain
chain = crud.get_choice_ancestor_chain(
    session=db,
    choice_id=progress.head_choice_id
)
print(f"Chain length: {len(chain)}")
for i, choice in enumerate(chain):
    print(f"  {i}: {choice.choice_text} (parent={choice.parent_choice_id})")
```

### Test Timeline Endpoint
```python
response = client.get(
    f"/api/v1/user-personas/{persona_id}/stories/{story_id}/timeline",
    headers=headers,
)
timeline = response.json()
print(f"Timeline events: {len(timeline['events'])}")
for event in timeline["events"]:
    current = "← CURRENT" if event["is_current"] else ""
    print(f"  - {event['choice_text']} → {event['node_title']} {current}")
```

---

## Fixture Reference

### `db_story_with_progress`
Returns: `tuple[Story, UserStoryProgress]`

**What it creates**:
- Test User (EMAIL_TEST_USER, matches normal_user_token_headers)
- Test Persona
- UserPersona (links user → persona)
- Story with **5 nodes** (Start → Node2 → Node3 → Node4 → Node5)
- **4 NodeChoices** between consecutive nodes
- UserStoryProgress at story start (head_choice_id=None, head_version=0)

**Story Structure**:
```
Start → Node2 → Node3 → Node4 → Node5 (end)
  ↓       ↓       ↓       ↓
Choice1 Choice2 Choice3 Choice4
```

**Usage**:
```python
def test_something(
    client: TestClient,
    db: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Can make up to 4 choices before reaching end node
    # Now make API calls using persona_id and story.id
```

---

## See Also

- **Implementation Guide**: `backend/docs/CYOA-2-Debug.md`
- **Phase 2 Reference**: `backend/docs/CYOA_PHASE2_QUICKREF.md`
- **Test Example**: `backend/app/test_scripts/test_story_system.py` (15/15 passing)
