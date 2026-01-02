# Phase 2 Quick Reference Card - Replay & Projection Logic

**Goal:** Add ability to reconstruct `story_state` from event chain (root → head)

**Estimated Time:** 1 week
**Branch:** `feature/cyoa-phase-2-replay-logic`
**Prerequisites:** Phase 1 complete and merged

---

## Pre-Implementation Checklist

- [ ] Phase 1 merged to main
- [ ] Read CYOA_MIGRATION_PLAN.md Phase 2 section
- [ ] Read CYOA_MIGRATION_ADDENDUM.md CRUD patterns
- [ ] Pull latest main branch
- [ ] Create feature branch from main
- [ ] Ensure local dev environment running

---

## Step 1: [X] Add CRUD Functions (1 hour)

### Location: `backend/app/crud.py`

Add these functions at the end of the file (before any test helpers):

#### 1.1 Add get_choice_ancestor_chain

```python
# ==================== Phase 2: Tree Navigation Functions ====================

def get_choice_ancestor_chain(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get ancestor chain from root to specified choice (inclusive).

    Returns events in order: [root_choice, ..., parent_choice, choice_id]
    Used for replay and timeline display.

    Args:
        session: Database session
        choice_id: Target choice UUID

    Returns:
        List of UserNodeChoice objects from root to target (ordered)

    Raises:
        ValueError: If choice_id doesn't exist in database
    """
    chain = []
    current_id = choice_id

    while current_id is not None:
        choice = session.get(UserNodeChoice, current_id)
        if not choice:
            # If we can't find a choice in the chain, something is corrupt
            raise ValueError(f"Choice {current_id} not found in database (data corruption)")
        chain.append(choice)
        current_id = choice.parent_choice_id

    return list(reversed(chain))  # Root → head order

def replay_state_from_head(
    *, session: Session, progress_id: uuid.UUID, head_choice_id: uuid.UUID | None
) -> dict[str, Any]:
    """
    Reconstruct story_state by replaying all events from root to head.

    This is the SOURCE OF TRUTH for state in event-sourced model.
    The UserStoryProgress.story_state field becomes a denormalized cache.

    Args:
        session: Database session
        progress_id: UserStoryProgress UUID (for validation)
        head_choice_id: Current head position (null = story start)

    Returns:
        Reconstructed state dictionary

    Raises:
        ValueError: If choice doesn't belong to progress_id
    """
    if head_choice_id is None:
        return {}  # At story start

    # Get all events from root to head
    chain = get_choice_ancestor_chain(session=session, choice_id=head_choice_id)

    # Validate all choices belong to this progress
    for choice in chain:
        if choice.progress_id != progress_id:
            raise ValueError(
                f"Choice {choice.id} doesn't belong to progress {progress_id}"
            )

    # Replay events (shallow merge)
    state: dict[str, Any] = {}
    for choice in chain:
        if choice.state_changes:
            state.update(choice.state_changes)

    return state

def get_current_node_from_head(
    *,
    session: Session,
    head_choice_id: uuid.UUID | None,
    story_id: uuid.UUID,
    story_version: int,
) -> uuid.UUID:
    """
    Derive current_node_id from head position.

    If head_choice_id is None, return start node.
    Otherwise, return to_node_id of head choice.

    Args:
        session: Database session
        head_choice_id: Current head position (null = story start)
        story_id: Story UUID (for finding start node)
        story_version: Story version (for finding start node)

    Returns:
        UUID of current story node

    Raises:
        ValueError: If no start node found or head choice missing
    """
    if head_choice_id is None:
        # At story start - find start node
        statement = select(StoryNode).where(
            StoryNode.story_id == story_id,
            StoryNode.story_version == story_version,
            StoryNode.is_start_node == True,  # noqa: E712
        )
        start_node = session.exec(statement).first()
        if not start_node:
            raise ValueError(
                f"No start node for story {story_id} version {story_version}"
            )
        return start_node.id

    # Return destination of head choice
    choice = session.get(UserNodeChoice, head_choice_id)
    if not choice:
        raise ValueError(f"Head choice {head_choice_id} not found")
    return choice.to_node_id

def get_choice_children(
    *, session: Session, choice_id: uuid.UUID
) -> list[UserNodeChoice]:
    """
    Get all direct children of a choice (for debugging/admin tools).

    In normal gameplay, children are hidden (abandoned branches).
    This is used for admin visualization of the full event tree.

    Args:
        session: Database session
        choice_id: Parent choice UUID

    Returns:
        List of child UserNodeChoice objects
    """
    statement = select(UserNodeChoice).where(
        UserNodeChoice.parent_choice_id == choice_id
    )
    return list(session.exec(statement).all())
```

---

## [X] Complete Step 2: Add Validation Endpoint (30 minutes)

### Location: `backend/app/api/routes/user_story_progress.py`

Add this endpoint to validate replay correctness:

```python
@router.get("/{story_id}/validate-state", response_model=dict[str, Any])
def validate_story_state(
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
) -> Any:
    """
    Validate that replayed state matches stored state.

    This is a Phase 2 diagnostic endpoint to verify replay logic correctness.
    In production, replayed state is the source of truth.

    Returns:
        {
            "stored_state": {...},
            "replayed_state": {...},
            "match": true/false,
            "differences": {...}
        }
    """
    # Check if the user persona belongs to the current user
    user_persona = crud.get_user_persona(
        session=session, id=user_persona_id, user_id=current_user.id
    )
    if not user_persona:
        raise HTTPException(status_code=404, detail="User persona not found")

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Story progress not found")

    # Get stored state
    stored_state = progress.story_state or {}

    # Replay state from head
    replayed_state = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id,
    )

    # Compare
    match = stored_state == replayed_state

    # Find differences
    differences = {}
    all_keys = set(stored_state.keys()) | set(replayed_state.keys())
    for key in all_keys:
        stored_val = stored_state.get(key)
        replayed_val = replayed_state.get(key)
        if stored_val != replayed_val:
            differences[key] = {
                "stored": stored_val,
                "replayed": replayed_val,
            }

    return {
        "stored_state": stored_state,
        "replayed_state": replayed_state,
        "match": match,
        "differences": differences,
    }
```

---

## Step 3: Update Choice Endpoint (Transition Phase) (20 minutes)

### Location: `backend/app/api/routes/user_story_progress.py`

**Modify `make_story_choice` to keep both mutable updates AND replay validation:**

```python
@router.post("/{story_id}/choices/{choice_id}", response_model=UserStoryProgressPublic)
def make_story_choice(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    user_persona_id: uuid.UUID,
    story_id: uuid.UUID,
    choice_id: uuid.UUID,
) -> Any:
    """
    Make a choice in the story and progress to the next node.

    PHASE 2: Still updates state mutably, but validates against replay.
    """
    # ... existing validation code ...

    progress = crud.get_user_story_progress(
        session=session, user_persona_id=user_persona_id, story_id=story_id
    )
    # ... existing checks ...

    # Create choice with parent pointer
    user_choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=progress.head_choice_id,
        choice_text=choice.text,
        from_node_id=choice.from_node_id,
        to_node_id=choice.to_node_id,
        state_changes=choice.sets_state,
        rng_data=None
    )
    session.add(user_choice)
    session.flush()  # Get ID

    # Update head pointer
    progress.head_choice_id = user_choice.id
    progress.head_version += 1
    progress.current_node_id = choice.to_node_id

    # PHASE 2: Still update mutably (backward compat)
    if choice.sets_state:
        if progress.story_state:
            progress.story_state.update(choice.sets_state)
        else:
            progress.story_state = choice.sets_state

    # NEW PHASE 2: Validate replay matches mutable update
    replayed_state = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=progress.head_choice_id,
    )

    # Log warning if mismatch (should never happen)
    if replayed_state != progress.story_state:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(
            f"State mismatch for progress {progress.id}: "
            f"stored={progress.story_state}, replayed={replayed_state}"
        )

    # Check end node
    to_node = session.get(StoryNode, choice.to_node_id)
    if to_node and to_node.is_end_node:
        progress.is_completed = True

    session.add(progress)
    session.commit()
    session.refresh(progress)

    return progress
```

---

## Step 4: Write Tests (1.5 hours)

### Location: `backend/app/tests/test_story_replay.py` (NEW FILE)

Create new test file:

```python
"""Tests for Phase 2: Replay logic."""

import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session

from app import crud
from app.models import UserNodeChoice, UserStoryProgress


def test_replay_state_from_single_choice(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay reconstructs state from single choice.

    Given: Progress with one choice that sets state {"has_torch": true}
    When: replay_state_from_head()
    Then: Returns {"has_torch": true}
    """
    story, progress = db_story_with_progress

    # Create a choice with state changes
    choice = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Pick up torch",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_torch": True},
    )
    session.add(choice)
    session.commit()
    session.refresh(choice)

    # Replay state
    replayed = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=choice.id,
    )

    assert replayed == {"has_torch": True}


def test_replay_state_from_chain(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay correctly merges state from chain.

    Given: Chain of 3 choices with state changes
    When: replay_state_from_head(choice_3)
    Then: Returns merged state from all 3 choices
    """
    story, progress = db_story_with_progress

    # Create choice chain
    choice1 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Pick up torch",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_torch": True, "location": "forest"},
    )
    session.add(choice1)
    session.flush()

    choice2 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice1.id,
        choice_text="Enter cave",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"location": "cave", "visited_cave": True},
    )
    session.add(choice2)
    session.flush()

    choice3 = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice2.id,
        choice_text="Find treasure",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"has_treasure": True, "gold": 100},
    )
    session.add(choice3)
    session.commit()

    # Replay state from choice3
    replayed = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=choice3.id,
    )

    # Should merge all state changes (shallow merge, later values override)
    expected = {
        "has_torch": True,
        "location": "cave",  # Overridden by choice2
        "visited_cave": True,
        "has_treasure": True,
        "gold": 100,
    }
    assert replayed == expected


def test_replay_state_at_story_start(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay returns empty state when head is None.

    Given: Progress with head_choice_id = None
    When: replay_state_from_head()
    Then: Returns {}
    """
    story, progress = db_story_with_progress

    replayed = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=None,
    )

    assert replayed == {}


def test_ancestor_chain_order(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that get_choice_ancestor_chain returns correct order.

    Given: Chain A → B → C
    When: get_choice_ancestor_chain(C)
    Then: Returns [A, B, C] in that order
    """
    story, progress = db_story_with_progress

    # Create chain
    choice_a = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=None,
        choice_text="Choice A",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    session.add(choice_a)
    session.flush()

    choice_b = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice_a.id,
        choice_text="Choice B",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    session.add(choice_b)
    session.flush()

    choice_c = UserNodeChoice(
        progress_id=progress.id,
        parent_choice_id=choice_b.id,
        choice_text="Choice C",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes=None,
    )
    session.add(choice_c)
    session.commit()

    # Get ancestor chain
    chain = crud.get_choice_ancestor_chain(session=session, choice_id=choice_c.id)

    assert len(chain) == 3
    assert chain[0].id == choice_a.id
    assert chain[1].id == choice_b.id
    assert chain[2].id == choice_c.id


def test_validate_state_endpoint(
    client: TestClient,
    session: Session,
    normal_user_token_headers: dict[str, str],
    db_story_with_progress: tuple,
) -> None:
    """
    Test that validate-state endpoint correctly compares stored vs replayed.

    Given: Progress with choices made
    When: GET /validate-state
    Then: Returns match=true and both states equal
    """
    story, progress = db_story_with_progress
    persona_id = progress.user_persona_id

    # Make a choice (this updates both mutable state and creates event)
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/current-node",
        headers=normal_user_token_headers,
    )
    choice_id = response.json()["available_choices"][0]["id"]

    client.post(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/choices/{choice_id}",
        headers=normal_user_token_headers,
    )

    # Validate state
    response = client.get(
        f"/api/v1/user-personas/{persona_id}/stories/{story.id}/validate-state",
        headers=normal_user_token_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["match"] is True
    assert data["differences"] == {}
    assert data["stored_state"] == data["replayed_state"]


def test_replay_validates_progress_ownership(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Test that replay raises error if choice doesn't belong to progress.

    Given: Choice from different progress
    When: replay_state_from_head() with wrong progress_id
    Then: Raises ValueError
    """
    story, progress1 = db_story_with_progress

    # Create second progress
    progress2 = UserStoryProgress(
        user_persona_id=progress1.user_persona_id,
        story_id=story.id,
        story_version=1,
    )
    session.add(progress2)
    session.flush()

    # Create choice for progress1
    choice = UserNodeChoice(
        progress_id=progress1.id,
        parent_choice_id=None,
        choice_text="Test",
        from_node_id=uuid.uuid4(),
        to_node_id=uuid.uuid4(),
        state_changes={"test": True},
    )
    session.add(choice)
    session.commit()

    # Try to replay with wrong progress_id
    import pytest

    with pytest.raises(ValueError, match="doesn't belong to progress"):
        crud.replay_state_from_head(
            session=session,
            progress_id=progress2.id,
            head_choice_id=choice.id,
        )
```

### Run Tests

```bash
docker compose exec backend bash
pytest app/tests/test_story_replay.py -v
exit
```

---

## Step 5: Performance Benchmarking (45 minutes)

### Location: `backend/app/tests/test_story_replay_performance.py` (NEW FILE)

```python
"""Performance tests for replay logic."""

import time
import uuid
from sqlmodel import Session

from app import crud
from app.models import UserNodeChoice


def test_replay_performance_100_choices(
    session: Session,
    db_story_with_progress: tuple,
) -> None:
    """
    Benchmark replay performance with 100-choice chain.

    Target: < 50ms for 100 choices
    """
    story, progress = db_story_with_progress

    # Create 100-choice chain
    previous_choice_id = None
    for i in range(100):
        choice = UserNodeChoice(
            progress_id=progress.id,
            parent_choice_id=previous_choice_id,
            choice_text=f"Choice {i}",
            from_node_id=uuid.uuid4(),
            to_node_id=uuid.uuid4(),
            state_changes={"step": i, f"flag_{i}": True},
        )
        session.add(choice)
        session.flush()
        previous_choice_id = choice.id

    session.commit()

    # Benchmark replay
    start = time.time()
    replayed = crud.replay_state_from_head(
        session=session,
        progress_id=progress.id,
        head_choice_id=previous_choice_id,
    )
    elapsed = (time.time() - start) * 1000  # Convert to ms

    # Verify correctness
    assert replayed["step"] == 99
    assert len(replayed) == 101  # step + 100 flags

    # Performance assertion
    assert elapsed < 50, f"Replay took {elapsed}ms, expected < 50ms"

    print(f"✓ Replay of 100 choices: {elapsed:.2f}ms")
```

**Run benchmark:**
```bash
docker compose exec backend bash
pytest app/tests/test_story_replay_performance.py -v -s
exit
```

---

## Step 6: Documentation (30 minutes)

### Location: `backend/app/crud.py`

Add docstring section at top of replay functions:

```python
# ==================== Phase 2: State Replay Functions ====================
#
# These functions implement event sourcing replay logic:
#
# 1. get_choice_ancestor_chain() - Traverses parent pointers from head to root
# 2. replay_state_from_head() - Reconstructs state by merging state_changes
# 3. get_current_node_from_head() - Derives current node from head position
#
# In Phase 2, these functions VALIDATE existing mutable state.
# In Phase 5, these become the SOURCE OF TRUTH for state.
#
# Performance: O(n) where n = chain length. Target < 50ms for 100 choices.
# Optimization: Snapshots added in Phase 5 reduce replay cost.
# ===========================================================================
```

---

## Step 7: Commit Changes (15 minutes)

```bash
# Check status
git status

# Stage changes
git add backend/app/crud.py
git add backend/app/api/routes/user_story_progress.py
git add backend/app/tests/test_story_replay.py
git add backend/app/tests/test_story_replay_performance.py

# Commit
git commit -m "feat: Add replay and projection logic for CYOA event sourcing (Phase 2)

- Add get_choice_ancestor_chain() for tree traversal
- Add replay_state_from_head() for state reconstruction
- Add get_current_node_from_head() for position derivation
- Add validate-state diagnostic endpoint
- Update make_story_choice to validate replay correctness
- Add comprehensive replay tests
- Add performance benchmarks (target: <50ms for 100 choices)

Phase 2 keeps mutable state updates for backward compatibility
while validating against replayed state. Phase 5 will make replay
the single source of truth.

Refs: CYOA_MIGRATION_PLAN.md Phase 2"

# Push branch
git push origin feature/cyoa-phase-2-replay-logic
```

---

## Step 8: Verify Correctness (30 minutes)

### 8.1 Run Full Test Suite

```bash
docker compose exec backend bash
pytest app/tests/ -v
exit
```

### 8.2 Manual Validation

```bash
# Use API docs
open http://localhost:8000/docs

# Test flow:
# 1. Start story: POST /user-personas/{id}/stories/{story_id}
# 2. Make 5 choices (building state)
# 3. Validate: GET /user-personas/{id}/stories/{story_id}/validate-state
#    - Should return match=true
# 4. Check stored vs replayed states are identical
```

### 8.3 Database Inspection

```bash
docker compose exec backend bash
psql -U app -d app

-- Check state in progress record
SELECT
    id,
    story_state,
    head_choice_id
FROM userstoryprogress
WHERE id = '<progress-id>';

-- Check state changes in choices
SELECT
    id,
    parent_choice_id,
    choice_text,
    state_changes,
    choice_time
FROM usernodechoice
WHERE progress_id = '<progress-id>'
ORDER BY choice_time;

-- Manually verify that merging state_changes produces story_state

\q
exit
```

---

## Troubleshooting

### Replay Returns Different State

**Error:** `validate-state` shows `match=false`

**Debug:**
```python
# In make_story_choice, add detailed logging:
import logging
logger = logging.getLogger(__name__)

if replayed_state != progress.story_state:
    logger.error(f"State mismatch details:")
    logger.error(f"  Progress ID: {progress.id}")
    logger.error(f"  Head choice: {progress.head_choice_id}")
    logger.error(f"  Stored: {progress.story_state}")
    logger.error(f"  Replayed: {replayed_state}")

    # Get full chain for debugging
    chain = crud.get_choice_ancestor_chain(
        session=session, choice_id=progress.head_choice_id
    )
    for i, choice in enumerate(chain):
        logger.error(f"  Choice {i}: {choice.state_changes}")
```

**Common Causes:**
- state_changes not being set correctly in Phase 1
- Shallow merge behavior (later keys override earlier)
- JSON serialization issues (check JSONB column)

### Performance Worse Than Expected

**Error:** Replay takes > 50ms for 100 choices

**Solutions:**
- Check database connection latency
- Verify indexes exist on parent_choice_id
- Consider eager loading (joinedload)
- Wait for Phase 5 snapshots

### ValueError: Choice doesn't belong to progress

**Error:** Validation error in replay

**Cause:** Data corruption or wrong progress_id passed

**Fix:**
```bash
# Check data integrity
psql -U app -d app

SELECT
    c.id AS choice_id,
    c.progress_id AS choice_progress,
    p.id AS progress_id
FROM usernodechoice c
LEFT JOIN userstoryprogress p ON c.progress_id = p.id
WHERE p.id IS NULL;

-- Should return no rows (all choices have valid progress)
```

---

## Success Criteria

- [ ] `get_choice_ancestor_chain()` returns correct order
- [ ] `replay_state_from_head()` reconstructs state correctly
- [ ] `get_current_node_from_head()` derives node correctly
- [ ] `validate-state` endpoint works and shows match=true
- [ ] All Phase 1 tests still pass
- [ ] All Phase 2 tests pass
- [ ] Replay performance < 50ms for 100 choices
- [ ] No state mismatches in logs
- [ ] Code committed and pushed

---

## Estimated Time Breakdown

| Task | Time | Running Total |
|------|------|---------------|
| Add CRUD functions | 1h | 1h |
| Add validation endpoint | 30min | 1h 30min |
| Update choice endpoint | 20min | 1h 50min |
| Write tests | 1h 30min | 3h 20min |
| Performance benchmarks | 45min | 4h 5min |
| Documentation | 30min | 4h 35min |
| Commit changes | 15min | 4h 50min |
| Verify correctness | 30min | **5h 20min** |

**Buffer for issues:** +1h 40min
**Total with buffer:** ~7 hours (1 work day)

---

## Next Steps After Phase 2

1. **Create PR** to main branch
2. **Team review** focusing on:
   - Replay logic correctness
   - Performance benchmarks
   - Test coverage
3. **Merge** after approval
4. **Monitor** for state mismatches in logs
5. **Begin Phase 3** (Undo & Rewind APIs)

---

## Quick Commands Reference

```bash
# Run replay tests
pytest app/tests/test_story_replay.py -v

# Run performance tests
pytest app/tests/test_story_replay_performance.py -v -s

# Test specific function
pytest app/tests/test_story_replay.py::test_replay_state_from_chain -v

# Check for state mismatches in logs
docker compose logs backend | grep "State mismatch"
```

---

## Support Resources

- **Main Plan:** `backend/docs/CYOA_MIGRATION_PLAN.md` (Phase 2 section)
- **Patterns:** `backend/docs/CYOA_MIGRATION_ADDENDUM.md` (CRUD patterns)
- **Phase 1 Quickref:** `backend/docs/CYOA_PHASE1_QUICKREF.md`
- **Story System:** `backend/docs/STORY_SYSTEM.md`

**Questions?** Reference documents above or ping backend team.
